import os
import sys
import asyncio
import random
import urllib.parse
import structlog
from playwright.async_api import async_playwright

logger = structlog.get_logger()

TAOBAO_CRAWL_RESULT = []


def _run_in_new_process(keyword: str, target_count: int, cookie_path: str) -> list:
    """
    별도 프로세스 진입점.
    Windows에서 uvicorn(SelectorEventLoop)과 충돌 없이
    ProactorEventLoop + Playwright를 안전하게 실행한다.
    """
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    return asyncio.run(_crawl(keyword, target_count, cookie_path))


async def _crawl(keyword: str, target_count: int, cookie_path: str) -> list:
    """실제 크롤링 로직. 별도 프로세스 안에서만 호출된다."""
    product_list = []

    async with async_playwright() as p:
        print(f"\n[Taobao] '{keyword}' 크롤링을 시작합니다. (목표: {target_count}개)")

        browser = await p.chromium.launch(headless=False)
        context_kwargs = {
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        }
        if os.path.exists(cookie_path):
            print(f"[Taobao] 쿠키 로드 완료: {cookie_path}")
            context_kwargs["storage_state"] = cookie_path

        context = await browser.new_context(**context_kwargs)
        page = await context.new_page()

        encoded_input = urllib.parse.quote(keyword)
        search_url_base = f"https://s.taobao.com/search?q={encoded_input}"

        print("[Taobao] 검색 결과 페이지 접속 중...")
        await page.goto(search_url_base, wait_until="domcontentloaded")
        await asyncio.sleep(random.uniform(3.0, 5.0))

        # [단계 1: '销量'(판매량순) 정렬 클릭]
        try:
            sales_tab_selector = "li.next-tabs-tab.customTabItem--cSF7eEGH"
            await page.wait_for_selector(sales_tab_selector, timeout=10000)
            tabs = await page.query_selector_all(sales_tab_selector)
            for tab in tabs:
                text = await tab.inner_text()
                if "销量" in text:
                    await tab.click()
                    print("[Taobao] '销量' 정렬 적용 완료")
                    await asyncio.sleep(random.uniform(3.0, 5.0))
                    break
        except Exception as e:
            print(f"[Taobao] '销量' 정렬 버튼을 찾는 데 실패했습니다: {e}")

        # [단계 2: 리스트 페이지에서 상품명 및 가격 수집]
        print("[Taobao] 리스트 페이지에서 상품 정보 수집 중...")
        items = await page.query_selector_all(
            'div[class*="search-content-col"] a[id^="item_id_"]'
        )

        for item in items:
            if len(product_list) >= target_count:
                break
            try:
                p_int_elem = await item.query_selector(".priceInt--yqqZMJ5a")
                p_float_elem = await item.query_selector(".priceFloat--XpixvyQ1")
                p_int = (await p_int_elem.inner_text()).strip() if p_int_elem else "0"
                p_float = (await p_float_elem.inner_text()).strip() if p_float_elem else ""
                price = f"{p_int}{p_float}"

                title_elem = await item.query_selector('div[class*="title--"]')
                title = (await title_elem.inner_text()).strip() if title_elem else "N/A"

                product_list.append({
                    "title": title,
                    "price": price,
                    "element": item,
                    "reviews": [],
                })
            except Exception as e:
                print(f"   상품 기본 정보 수집 실패: {e}")
                continue

        print(
            f"[Taobao] 총 {len(product_list)}개 기본 정보 수집 완료. "
            "상위 10개 리뷰 수집 시작..."
        )

        # [단계 3: 상위 10개 제품 리뷰 수집]
        for i, product in enumerate(product_list[:10]):
            try:
                print(f"   [{i+1}/10] '{product['title'][:20]}...' 상세 분석 중...")

                async with context.expect_page() as new_page_info:
                    await product["element"].click()
                detail_page = await new_page_info.value
                await detail_page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(random.uniform(4.0, 6.0))

                sales_elem = await detail_page.query_selector("div.itemInfo--TSMo4Asj")
                product["sales"] = (
                    (await sales_elem.inner_text()).strip() if sales_elem else "0"
                )

                review_btn = await detail_page.query_selector(
                    'div.ShowButton--fMu7HZNs:has-text("查看全部评价")'
                )
                all_reviews = []

                if review_btn:
                    await review_btn.click()
                    await asyncio.sleep(random.uniform(3.0, 5.0))

                    try:
                        impr_items = await detail_page.query_selector_all(
                            "div.content--nuxTngci.detailContentClassName--L4MaK8TB "
                            "span.imprItem--fTAkDWa5"
                        )
                        for impr in impr_items:
                            impr_text = await impr.inner_text()
                            if any(kw in impr_text for kw in ["追평", "追追", "追"]):
                                await impr.click()
                                print("      '追平' 필터 적용 완료")
                                await asyncio.sleep(random.uniform(2.0, 3.5))
                                break
                    except Exception:
                        pass

                    last_count = 0
                    while True:
                        rev_elements = await detail_page.query_selector_all(
                            ".content--uonoOhaz"
                        )
                        current_count = len(rev_elements)
                        if current_count <= last_count:
                            break
                        skip_texts = [
                            "该用户未填写评价内容",
                            "該用戶未及時主動評價，系統默認評價",
                            "该用户觉得商品非常好，给出好评",
                        ]
                        for rev in rev_elements[last_count:]:
                            t = (await rev.inner_text()).strip()
                            if t and t not in skip_texts and t not in all_reviews:
                                all_reviews.append(t)
                        last_count = current_count
                        await detail_page.mouse.wheel(0, 2000)
                        await asyncio.sleep(1.0)
                        if len(all_reviews) >= 100:
                            break

                product["reviews"] = all_reviews
                print(f"      수집 완료: 리뷰 {len(all_reviews)}개")
                await detail_page.close()
                await asyncio.sleep(random.uniform(1.5, 3.0))

            except Exception as e:
                print(f"   상품 상세 처리 실패: {e}")
                continue

        await browser.close()

        for prod in product_list:
            prod.pop("element", None)

        return product_list


class TaobaoCrawler:
    def __init__(self):
        current_file_path = os.path.abspath(__file__)
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(current_file_path)))
        )
        self.cookie_path = os.path.join(
            project_root, "storage", "cookies", "taobao_cookie.json"
        )

    async def crawl_analysis_data(
        self, keyword: str, target_count: int = 20
    ) -> list[dict]:
        """
        uvicorn(SelectorEventLoop) 안에서 호출되어도 안전하도록
        ProcessPoolExecutor로 별도 프로세스에서 Playwright를 실행한다.
        """
        import concurrent.futures

        loop = asyncio.get_event_loop()
        with concurrent.futures.ProcessPoolExecutor(max_workers=1) as executor:
            result = await loop.run_in_executor(
                executor,
                _run_in_new_process,
                keyword,
                target_count,
                self.cookie_path,
            )

        global TAOBAO_CRAWL_RESULT
        TAOBAO_CRAWL_RESULT = result
        return TAOBAO_CRAWL_RESULT
