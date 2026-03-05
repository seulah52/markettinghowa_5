import os
import sys
import asyncio
import random
import structlog
from playwright.async_api import async_playwright

logger = structlog.get_logger()

XHS_CRAWL_RESULT = []


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
    results = []

    async with async_playwright() as p:
        print(f"\n[Xiaohongshu] '{keyword}' 수집을 시작합니다. (목표: {target_count}개)")

        context_kwargs = {
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        }
        if os.path.exists(cookie_path):
            context_kwargs["storage_state"] = cookie_path

        # 1단계: Headless=True로 로그인 상태 체크
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(**context_kwargs)
        page = await context.new_page()

        need_manual_login = False
        try:
            await page.goto(
                "https://www.xiaohongshu.com",
                wait_until="domcontentloaded",
                timeout=20000,
            )
            await asyncio.sleep(random.uniform(0.8, 3.0))

            login_modal = await page.query_selector(
                '.login-container, .login-modal, [class*="login"]'
            )
            is_blocked = await page.query_selector("text='Sorry, this page isn't available'")
            search_bar = await page.query_selector("input#search-input")

            if login_modal or is_blocked or not search_bar:
                print("[Xiaohongshu] 로그인 만료 또는 차단 감지 -> 가시 모드로 전환합니다.")
                need_manual_login = True
        except Exception:
            need_manual_login = True

        # 2단계: 로그인 필요 시 headless=False로 재시작
        if need_manual_login:
            await browser.close()
            print("\n" + "!" * 70)
            print("[Xiaohongshu] 로그인이 필요합니다. 브라우저 창이 열리면 로그인을 완료해 주세요.")
            print("!" * 70)

            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(**context_kwargs)
            page = await context.new_page()
            await page.goto("https://www.xiaohongshu.com")

            # 별도 프로세스이므로 input() 호출 가능 (uvicorn 루프 블로킹 없음)
            input(">>> 로그인이 완료되어 메인 화면이 보이면 엔터를 누르세요: ")

            await context.storage_state(path=cookie_path)
            print(f"[Xiaohongshu] 새로운 쿠키 저장 완료: {cookie_path}")
            await page.reload(wait_until="domcontentloaded")
        else:
            print("[Xiaohongshu] 로그인 상태가 유효합니다. Headless 모드를 유지합니다.")

        # 3단계: 본격적인 수집 시작
        try:
            print(f"[Xiaohongshu] 검색어 '{keyword}' 입력 중...")
            search_input = page.locator("input#search-input.search-input")
            await search_input.wait_for(state="visible", timeout=10000)
            await search_input.fill(keyword)
            await page.keyboard.press("Enter")

            await page.wait_for_selector("section.note-item", timeout=20000)
            await asyncio.sleep(random.uniform(0.8, 3.0))

            post_links = []
            print(f"[Xiaohongshu] 게시물 링크 수집 중 (목표: {target_count}개)...")
            max_retry = 40
            while len(post_links) < target_count and max_retry > 0:
                elements = await page.locator("section.note-item a.cover").all()
                for el in elements:
                    href = await el.get_attribute("href")
                    if href and href not in post_links:
                        post_links.append(href)
                    if len(post_links) >= target_count:
                        break
                if len(post_links) >= target_count:
                    break
                await page.mouse.wheel(0, 2500)
                await asyncio.sleep(random.uniform(0.8, 3.0))
                max_retry -= 1

            print(f"[Xiaohongshu] 총 {len(post_links)}개 링크 확보. 상세 수집 시작...")

            for i, link in enumerate(post_links):
                try:
                    post_url = f"https://www.xiaohongshu.com{link}"
                    await page.goto(post_url, wait_until="domcontentloaded", timeout=30000)
                    await asyncio.sleep(random.uniform(0.8, 3.0))

                    title = "제목 없음"
                    try:
                        title_elem = await page.query_selector("#detail-title")
                        if title_elem:
                            title = await title_elem.inner_text()
                    except Exception:
                        pass

                    desc = ""
                    try:
                        desc_elem = await page.query_selector("#detail-desc")
                        if desc_elem:
                            desc = await desc_elem.inner_text()
                    except Exception:
                        pass

                    await page.keyboard.press("PageDown")
                    await asyncio.sleep(random.uniform(0.8, 3.0))

                    comments = []
                    comment_items = await page.locator(".comment-item").all()
                    for c_item in comment_items[:30]:
                        try:
                            author = await c_item.locator(".author").first.inner_text(
                                timeout=1000
                            )
                            content = await c_item.locator(".content").first.inner_text(
                                timeout=1000
                            )
                            comments.append({
                                "author": author.strip(),
                                "content": content.strip().replace("\n", " "),
                            })
                        except Exception:
                            continue

                    results.append({
                        "index": i + 1,
                        "url": post_url,
                        "title": title.strip(),
                        "description": desc.strip().replace("\n", " "),
                        "comments": comments,
                    })

                    if (i + 1) % 5 == 0:
                        print(f"       [{i+1}/{target_count}] 완료... (현재 {len(results)}개)")

                except Exception as e:
                    print(f"   [경고] {i+1}번째 게시물 분석 실패 (건너뜀): {e}")
                    continue

            print(f"\n[Xiaohongshu] 모든 수집 완료 (총 {len(results)}개)")
            return results

        except Exception as e:
            print(f"[Xiaohongshu] 수집 중 에러: {e}")
            return results
        finally:
            await browser.close()


class XiaohongshuCrawler:
    def __init__(self):
        current_file_path = os.path.abspath(__file__)
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(current_file_path)))
        )
        self.cookie_path = os.path.join(
            project_root, "storage", "cookies", "xhs_cookie.json"
        )

    async def crawl_analysis_data(
        self, keyword: str, target_count: int = 30
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

        global XHS_CRAWL_RESULT
        XHS_CRAWL_RESULT = result
        return XHS_CRAWL_RESULT
