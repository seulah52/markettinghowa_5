import os
import sys
import re
import json
import time
import base64
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor
import asyncio

# Windows CP949 환경에서 이모지/한글 print 시 UnicodeEncodeError 방지
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1, closefd=False)
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1, closefd=False)

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.append(ROOT_DIR)

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import AsyncOpenAI
from playwright.sync_api import sync_playwright
from app.core.config import settings

router = APIRouter()
_executor = ThreadPoolExecutor(max_workers=4)

WANGHONG_DIR = os.path.dirname(os.path.abspath(__file__))
WANGHONG_DATA_DIR = os.path.join(WANGHONG_DIR, "wanghong")
DATA_PATH = os.path.join(ROOT_DIR, "storage", "data", "influencers.json")
COOKIE_PATH = os.path.join(WANGHONG_DATA_DIR, "huitun_xhs_cookie.json")

deepseek_client = AsyncOpenAI(api_key=settings.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


# ── 한국어 레이블 매핑 ──
KEY_LABEL_KO = {
    "avatar": "프로필 이미지",
    "name": "이름",
    "id": "ID",
    "followers": "팔로워 수",
    "growth_amount": "팔로워 증가량",
    "growth_rate": "팔로워 증가율",
    "score": "점수",
    "description": "소개",
    "ID": "ID",
    "笔记数": "게시물 수",
    "赞藏总数": "좋아요·저장 합계",
    "关注数": "팔로잉 수",
    "新增笔记": "새 게시물",
    "平均点赞": "평균 좋아요 수",
    "粉丝数": "팔로워 수",
}


# ── 2단계 번역 (중국어 → 영어 → 한국어) ──
async def translate_zh_to_ko(text: str) -> str:
    if not text or not text.strip():
        return text
    try:
        r1 = await deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a professional translator. Translate the given Chinese text into English. Output only the translated text, nothing else."},
                {"role": "user", "content": text},
            ],
            max_tokens=500,
        )
        english = r1.choices[0].message.content.strip()
        r2 = await deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a professional translator. Translate the given English text into Korean. Output only the translated text, nothing else."},
                {"role": "user", "content": english},
            ],
            max_tokens=500,
        )
        return r2.choices[0].message.content.strip()
    except Exception as e:
        print(f"[translate_zh_to_ko] error: {e}")
        return text


# ── DeepSeek 왕홍 추천 ──
async def _recommend_by_deepseek(keyword: str, influencers: list, recommend_count: int) -> list:
    # description 필드 제외 — DeepSeek가 description 텍스트를 id로 혼동하는 것을 방지
    # NOTE: reason은 여기서 생성하지 않는다.
    #       현재 보유 데이터(이름·팔로워·점수)만으로는 근거 있는 분석이 불가능하기 때문.
    #       reason은 detail-json 호출 시 실제 크롤링 수치를 근거로 별도 생성한다.
    sample = [
        {
            "id": str(i.get("id", "")),
            "name": i.get("name", ""),
            "followers": i.get("followers", "0"),
            "score": i.get("score", 0),
        }
        for i in influencers[:100]
    ]
    prompt = f"""You are an expert in Chinese influencer (Wanghong) marketing.

[User Keyword]
{keyword}

[Wanghong Candidate List (JSON)]
Each entry has: "id" (a unique numeric/alphanumeric account identifier), "name" (display name), "followers", "score".
{json.dumps(sample, ensure_ascii=False)}

[Mission]
Select the {recommend_count} most relevant Wanghong influencers for the given keyword.
Base your selection ONLY on name relevance and score. Do NOT fabricate any content analysis.

[CRITICAL RULES]
- The "id" in your output MUST be the exact value of the "id" field from the list above (e.g. "975157141", "chabaotangbao23").
- DO NOT use "name" as the id. "id" and "name" are different fields.
- Output JSON only — no "reason" field:
{{ "recommendations": [{{"id":"<exact id from list>"}},...] }}
"""
    try:
        resp = await deepseek_client.chat.completions.create(
            model="deepseek-chat",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a strict JSON generator. Output ONLY valid JSON. The id field must be the exact id value from the input list, never the name."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
        )
        raw = resp.choices[0].message.content or "{}"
        data = json.loads(raw)
        recs = data.get("recommendations", [])
        print(f"[DEBUG] DeepSeek recs: {recs}")
        out = []
        for r in recs:
            if isinstance(r, dict) and r.get("id"):
                out.append({"id": str(r["id"]).strip()})
        return out[:max(1, recommend_count)]
    except Exception as e:
        print(f"[_recommend_by_deepseek] error: {e}")
        return []


class RecommendRequest(BaseModel):
    product_desc: str
    recommend_count: int = 10
    use_previous: bool = False   # True 시 product_desc 대신 이전 데이터의 keyword 사용


class OneClickRequest(BaseModel):
    keyword: str
    recommend_count: int = 10
    use_previous: bool = False   # True 시 keyword 대신 이전 데이터의 keyword 사용


def format_w_to_man(text):
    if not text:
        return "0"
    return text.replace('w', '만').replace('W', '만')


def encode_image(image_path):
    if not os.path.exists(image_path):
        return ""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')


async def extract_with_vision(main_img_path, price_img_path):
    try:
        main_base64 = encode_image(main_img_path)
        price_base64 = encode_image(price_img_path)
        if not main_base64:
            return None
        prompt = """
        Analyze these screenshots.
        Extract data into a JSON object.
        CRITICAL: All explanations or labels must be in Korean.
        Keys: new_followers, new_notes, hot_rate, avg_like, avg_save, avg_share, video_price, image_price, cpe, cpm.
        Replace 'w' with '만' in any numeric values.
        """
        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{main_base64}"}},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{price_base64}"}} if price_base64 else {"type": "text", "text": "Price image not available"},
            ]}],
            max_tokens=800,
        )
        content = response.choices[0].message.content.strip()
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        return json.loads(json_match.group()) if json_match else None
    except Exception:
        return None


def _cookie_exists() -> bool:
    return os.path.exists(COOKIE_PATH)


def _raise_cookie_required():
    raise HTTPException(
        status_code=401,
        detail={"code": "COOKIE_EXPIRED", "message": "로그인 세션이 없거나 만료되었습니다."},
    )


def _assert_session_alive_sync(page) -> None:
    try:
        body = page.evaluate("() => document.body && document.body.innerText ? document.body.innerText : ''") or ""
        if "登录/注册" in body:
            raise HTTPException(status_code=401, detail={"code": "COOKIE_EXPIRED", "message": "로그인 세션이 만료되었습니다."})
    except HTTPException:
        raise
    except Exception:
        return


def _check_session_and_login_if_needed(context_kwargs: dict) -> bool:
    """
    독립적인 sync_playwright 인스턴스로 세션만 확인한다.
    로그인이 필요하면 False를 반환하고, 호출부에서 401을 raise한다.
    실제 로그인(GUI 창 띄우기)은 /login 엔드포인트가 전담한다.
    """
    if not _cookie_exists():
        print("[huitun] 쿠키 파일 없음 — 로그인 필요")
        return False

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(**context_kwargs)
        page = context.new_page()
        try:
            page.goto("https://xhs.huitun.com/", wait_until="domcontentloaded", timeout=20000)
            time.sleep(2)
            body = page.evaluate("() => document.body ? document.body.innerText : ''") or ""
            if "登录/注册" in body or "ID：" not in body:
                print("[huitun] 세션 만료 — 재로그인 필요")
                return False
            else:
                print("[huitun] 세션 유효 — 크롤링 진행")
                return True
        except Exception as e:
            print(f"[huitun] 세션 확인 중 오류: {e}")
            return False
        finally:
            browser.close()


def _run_login_with_chromium() -> bool:
    """
    Playwright Chromium headless=False 창을 띄워 위챗 QR 로그인을 수행하고
    쿠키를 저장한다. /login 엔드포인트의 백그라운드 스레드에서 실행된다.
    """
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-features=IsolateOrigins,site-per-process",
            ],
        )
        ctx_login = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=user_agent,
            ignore_https_errors=True,
        )
        page = ctx_login.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        try:
            print("[login] Chromium 창 열기 → https://xhs.huitun.com/#/login")
            page.goto("https://xhs.huitun.com/#/login", wait_until="domcontentloaded", timeout=30000)
            print("★ 위챗(WeChat) QR코드로 로그인을 완료해주세요! (최대 3분)")

            deadline = time.time() + 180
            logged_in = False
            while time.time() < deadline:
                time.sleep(2)
                try:
                    cur_body = page.evaluate("() => document.body ? document.body.innerText : ''") or ""
                except Exception:
                    break
                if "ID：" in cur_body and "登录/注册" not in cur_body:
                    print("✅ 로그인 성공! 쿠키 저장 중...")
                    page.goto("https://xhs.huitun.com/", wait_until="domcontentloaded", timeout=15000)
                    time.sleep(2)
                    os.makedirs(WANGHONG_DATA_DIR, exist_ok=True)
                    ctx_login.storage_state(path=COOKIE_PATH)
                    print(f"✅ 쿠키 저장 완료: {COOKIE_PATH}")
                    logged_in = True
                    break

            if not logged_in:
                print("❌ 로그인 시간 초과 (3분).")
            return logged_in
        except Exception as e:
            print(f"❌ 로그인 중 오류: {e}")
            return False
        finally:
            browser.close()


def _crawl_wanghong_list_sync() -> List[dict]:
    all_influencers: List[dict] = []
    seen_ids = set()

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    context_kwargs: dict = {"user_agent": user_agent}
    if _cookie_exists():
        context_kwargs["storage_state"] = COOKIE_PATH

    # 로그인 확인 — 세션 만료 시 401 반환 (로그인은 /login 엔드포인트 전담)
    ok = _check_session_and_login_if_needed(context_kwargs)
    if not ok:
        raise HTTPException(
            status_code=401,
            detail={"code": "COOKIE_EXPIRED", "message": "로그인이 필요합니다. /login 엔드포인트를 먼저 호출해주세요."},
        )

    # 로그인 후 새 쿠키 반영
    if _cookie_exists():
        context_kwargs["storage_state"] = COOKIE_PATH

    # 크롤링 (독립 playwright 인스턴스)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(**context_kwargs)
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        try:
            page.goto("https://xhs.huitun.com/#/anchor/anchor_list?page=add", wait_until="networkidle", timeout=120000)
            _assert_session_alive_sync(page)

            try:
                cat_btn = page.get_by_text("家居家装").first
                cat_btn.wait_for(state="visible", timeout=15000)
                cat_btn.click()
            except Exception:
                pass

            page.wait_for_timeout(5000)

            scroll_attempts = 0
            max_scroll_attempts = 10

            while True:
                if len(all_influencers) >= 99:
                    break

                id_indicators = page.get_by_text("ID：").all()
                new_found_in_this_round = 0

                for indicator in id_indicators:
                    try:
                        container = indicator.locator(
                            "xpath=./ancestor::tr | ./ancestor::div[contains(@class, 'item')] | ./ancestor::div[contains(@class, 'row')] | ./ancestor::div[contains(@class, 'el-table__row')]"
                        ).first
                        if container.count() == 0:
                            container = indicator.locator("xpath=./../../..")

                        text = container.inner_text().strip()
                        if not text:
                            continue

                        id_match = re.search(r"ID：\s*([a-zA-Z0-9_-]+)", text)
                        if not id_match:
                            continue
                        anchor_id = id_match.group(1)
                        if anchor_id in seen_ids:
                            continue

                        lines = [l.strip() for l in text.split("\n") if l.strip()]
                        img_el = container.locator("img").first
                        avatar_url = ""
                        try:
                            if img_el.count() > 0:
                                avatar_url = img_el.get_attribute("src") or ""
                        except Exception:
                            avatar_url = ""

                        name = "Unknown"
                        for line in lines:
                            if (not re.match(r"^\d+(\.\d+)?$", line)
                                    and "ID：" not in line
                                    and "灰豚" not in line
                                    and "等级" not in line):
                                name = line
                                break

                        followers_match = re.search(r"(\d+(\.\d+)?w)", text)
                        followers = followers_match.group(1) if followers_match else "0"

                        growth_rate_match = re.search(r"(\d+(\.\d+)?%)", text)
                        growth_rate = growth_rate_match.group(1) if growth_rate_match else "0%"

                        temp_text = text.replace(followers, "").replace(growth_rate, "")
                        nums = re.findall(r"(\d[\d,.]*)", temp_text)
                        score_val = nums[0] if len(nums) >= 1 else "0"
                        growth_amount = nums[1] if len(nums) >= 2 else "0"

                        if "即将到期" in name or followers == "0" or anchor_id == "1001242613":
                            continue

                        influencer = {
                            "avatar": avatar_url,
                            "name": name,
                            "id": anchor_id,
                            "followers": followers,
                            "growth_amount": growth_amount,
                            "growth_rate": growth_rate,
                            "score": float(score_val.replace(',', '')) if score_val.replace('.', '').replace(',', '').isdigit() else 0,
                        }

                        all_influencers.append(influencer)
                        seen_ids.add(anchor_id)
                        new_found_in_this_round += 1
                        print(f"   ✅ [{len(all_influencers)}] 수집: {name} (ID: {anchor_id})")
                    except Exception as e:
                        print(f"      ⚠️ 항목 수집 중 오류: {e}")
                        continue

                if new_found_in_this_round > 0:
                    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
                    with open(DATA_PATH, "w", encoding="utf-8") as f:
                        json.dump(all_influencers, f, ensure_ascii=False, indent=4)
                    scroll_attempts = 0
                else:
                    scroll_attempts += 1

                page.mouse.wheel(0, 3000)
                page.wait_for_timeout(2000)

                if scroll_attempts >= max_scroll_attempts:
                    next_btn = page.locator(".btn-next, .el-icon-arrow-right").last
                    if next_btn.is_visible() and next_btn.is_enabled():
                        next_btn.click()
                        scroll_attempts = 0
                        page.wait_for_timeout(4000)
                    else:
                        break

            all_influencers.sort(key=lambda x: x['score'], reverse=True)
            os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
            with open(DATA_PATH, "w", encoding="utf-8") as f:
                json.dump(all_influencers, f, ensure_ascii=False, indent=4)

            return all_influencers
        finally:
            browser.close()


def _get_detail_sync(anchor_id: str, name: str = "") -> dict:
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            storage_state=COOKIE_PATH,
            user_agent=user_agent,
        )
        page = context.new_page()
        try:
            result: dict = {"ID": anchor_id}

            # ── 1단계: 리스트 페이지에서 name 검색 후 클릭 ──
            # URL 직접 접근 시 暂无数据가 뜨므로, 반드시 리스트→클릭 경로로 진입
            page.goto(
                "https://xhs.huitun.com/#/anchor/anchor_list?page=add",
                wait_until="domcontentloaded",
                timeout=60000,
            )
            page.wait_for_timeout(3000)

            _assert_session_alive_sync(page)

            # 家居家装 카테고리 선택
            try:
                cat_btn = page.get_by_text("家居家装").first
                cat_btn.wait_for(state="visible", timeout=10000)
                cat_btn.click()
                page.wait_for_timeout(2000)
            except Exception:
                pass

            # name으로 해당 왕홍 탐색 — 스크롤마다 div.styles_one_line__21T4I inner text 정확 매칭 후 즉시 클릭
            found = False
            anchor_name = name or anchor_id
            for scroll_idx in range(25):
                candidates = page.locator("div.styles_one_line__21T4I").all()
                for el in candidates:
                    try:
                        el_text = el.inner_text(timeout=1000).strip()
                        if el_text == anchor_name:
                            el.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            el.click(force=True)
                            found = True
                            print(f"[detail] '{anchor_name}' 매칭 클릭 성공 (스크롤 {scroll_idx}회)")
                            break
                    except Exception:
                        continue
                if found:
                    break
                page.mouse.wheel(0, 1500)
                page.wait_for_timeout(1000)

            # 새 탭이 열렸으면 전환
            page.wait_for_timeout(2000)
            if len(context.pages) > 1:
                page = context.pages[-1]
                page.bring_to_front()

            # 클릭 실패 시 URL 직접 접근 (fallback)
            if not found or "anchor_detail" not in page.url:
                page.goto(
                    f"https://xhs.huitun.com/#/anchor/anchor_detail?id={anchor_id}",
                    wait_until="domcontentloaded",
                    timeout=60000,
                )

            # ── 2단계: 데이터 로딩 대기 (暂无数据 감지 시 최대 2회 새로고침) ──
            refresh_count = 0
            data_verified = False
            while refresh_count <= 2:
                page.wait_for_timeout(3000)
                body_text = page.evaluate("() => document.body ? document.body.innerText : ''") or ""

                if "暂无数据" in body_text:
                    if refresh_count < 2:
                        refresh_count += 1
                        print(f"[detail] 暂无数据 감지 ({refresh_count}/2회) — 새로고침")
                        page.reload(wait_until="domcontentloaded")
                        continue
                    else:
                        print("[detail] 2회 새로고침 후에도 暂无数据 — 현재 상태로 진행")
                        break

                import re as _re
                if _re.search(r"(粉丝|笔记|赞藏|关注|点赞)\D*[1-9]", body_text):
                    data_verified = True
                    page.wait_for_timeout(2000)  # 애니메이션 안정화
                    break

                refresh_count += 1
                page.reload(wait_until="domcontentloaded")

            if not data_verified:
                print("[detail] 데이터 미확인 — 현재 상태로 수집 진행")

            # ── 3단계: 개요 섹션 1 — styles_left_info__ys-bA ──
            try:
                left_items = page.locator("div.styles_left_info__ys-bA .styles_item__IrJab").all()
                for item in left_items:
                    try:
                        label = item.locator("p.styles_label__SZucZ").inner_text(timeout=3000).strip()
                        value = item.locator("p.styles_value__2FWRI").inner_text(timeout=3000).strip()
                        if label:
                            result[label] = value
                    except Exception:
                        continue
            except Exception as e:
                print(f"[detail] left_info error: {e}")

            # ── 4단계: 개요 섹션 2 — 지표 (新增粉丝 ~ 平均分享) ──
            try:
                stat_labels = page.locator("p.styles_label__SZucZ").all()
                stat_values = page.locator("p.styles_value__2FWRI").all()
                for label_el, value_el in zip(stat_labels, stat_values):
                    try:
                        label = label_el.inner_text(timeout=3000).strip()
                        value = value_el.inner_text(timeout=3000).strip()
                        if label and label not in result:
                            result[label] = value
                    except Exception:
                        continue
            except Exception as e:
                print(f"[detail] stat_labels error: {e}")

            # ── 5단계: 견적 섹션 — 报价 버튼 클릭 → 팝업 수집 ──
            try:
                baojia_btn = page.locator("div.styles_button__YXvD0", has_text="报价").first
                baojia_btn.wait_for(state="visible", timeout=10000)
                baojia_btn.click()
                page.wait_for_timeout(2000)

                sections = page.locator("span.styles_box_title__1I-P4").all()
                for section_el in sections:
                    try:
                        section_title = section_el.inner_text(timeout=3000).strip()
                        container = section_el.locator("xpath=./ancestor::div[contains(@class,'styles_box__')]").first
                        items = container.locator("div.styles_base_item__V4EhH").all()
                        for item in items:
                            try:
                                item_label = item.locator("p").first.inner_text(timeout=3000).strip()
                                item_value = item.locator("p").nth(1).inner_text(timeout=3000).strip()
                                key = f"{section_title}报价_{item_label}"
                                result[key] = item_value
                            except Exception:
                                continue
                    except Exception:
                        continue

                page.keyboard.press("Escape")
                page.wait_for_timeout(500)

            except Exception as e:
                print(f"[detail] baojia error: {e}")

            return result

        finally:
            browser.close()


def _get_detail_vision_sync(anchor_id: str, name: str) -> tuple:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1440, 'height': 900}, storage_state=COOKIE_PATH)
        page = context.new_page()
        try:
            page.goto(f"https://xhs.huitun.com/#/anchor/anchor_detail?id={anchor_id}", wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            main_shot = f"debug_main_{anchor_id}.png"
            page.screenshot(path=main_shot)

            page.evaluate("""() => {
                const targets = Array.from(document.querySelectorAll('.ant-tabs-tab, .el-tabs__item, span, div'));
                const found = targets.find(t => t.innerText && t.innerText.trim() === '报价');
                if (found) found.click();
            }""")
            page.wait_for_timeout(2000)

            price_shot = f"debug_price_{anchor_id}.png"
            page.screenshot(path=price_shot)
            return main_shot, price_shot
        finally:
            browser.close()


# ── async 래퍼 ──

async def _crawl_wanghong_list_impl() -> List[dict]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _crawl_wanghong_list_sync)


async def _get_detail_impl(anchor_id: str, name: str = "") -> dict:
    if not _cookie_exists():
        _raise_cookie_required()
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _get_detail_sync, anchor_id, name)


async def _get_detail_vision_impl(anchor_id: str, name: str) -> tuple:
    if not _cookie_exists():
        _raise_cookie_required()
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _get_detail_vision_sync, anchor_id, name)


# ── 이전 데이터 헬퍼 ──

def _load_previous_keyword() -> dict:
    """storage/data/final_report.json 에서 keyword·category를 추출해 반환."""
    final_path = os.path.join(ROOT_DIR, "storage", "data", "final_report.json")
    if not os.path.exists(final_path):
        return {"keyword": "", "category": "", "raw": {}}
    with open(final_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    keyword = ""
    for key in ("keyword", "keywords", "search_keyword", "query",
                "product", "product_name", "한국어_키워드", "kr_keyword"):
        val = data.get(key)
        if val:
            keyword = val[0] if isinstance(val, list) else str(val)
            break

    category = ""
    for key in ("category", "industry", "industry_category", "산업군",
                "sector", "main_category", "classification"):
        val = data.get(key)
        if val:
            category = val[0] if isinstance(val, list) else str(val)
            break

    return {"keyword": keyword, "category": category, "raw": data}


# ── 라우터 엔드포인트 ──

@router.get("/crawl")
async def crawl_wanghong_list():
    influencers = await _crawl_wanghong_list_impl()
    return {"success": True, "count": len(influencers)}


@router.get("/previous-data")
async def get_previous_data():
    """이전 리서치 데이터(final_report.json)에서 keyword·category를 반환한다."""
    try:
        result = _load_previous_keyword()
        if not result["keyword"] and not result["category"]:
            raise HTTPException(status_code=404, detail="이전 데이터가 없습니다. 먼저 리서치를 실행해주세요.")
        return {"status": "ok", **result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend")
async def recommend_wanghong(req: RecommendRequest):
    if not os.path.exists(DATA_PATH):
        raise HTTPException(status_code=404, detail="왕홍 데이터가 없습니다. 먼저 수집을 실행해주세요.")

    # 이전 데이터 불러오기 모드: product_desc를 이전 keyword로 대체
    if req.use_previous:
        prev = _load_previous_keyword()
        if not prev["keyword"]:
            raise HTTPException(status_code=404, detail="이전 데이터가 없습니다. 먼저 리서치를 실행해주세요.")
        product_desc = prev["keyword"]
    else:
        product_desc = req.product_desc

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        influencers = json.load(f)

    prompt = f"""
    당신은 가구/인테리어 마케팅 전문가입니다.
    [상품]: {product_desc}
    [왕홍 리스트]: {json.dumps(influencers[:100], ensure_ascii=False)}

    미션: 위 리스트 중 상품과 가장 잘 어울리는 왕홍 {req.recommend_count}명을 선별하세요.
    조건:
    1. 추천 사유(reason)는 반드시 한국어로 작성할 것.
    2. 결과는 JSON 리스트 형식만 출력할 것: [{{ "id": "...", "name": "...", "reason": "..." }}]
    """

    try:
        response = await deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Marketing expert. JSON output only."},
                {"role": "user", "content": prompt},
            ],
        )
        content = response.choices[0].message.content.strip()
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        recs = json.loads(json_match.group()) if json_match else json.loads(content)

        inf_map = {str(i.get('id')): i for i in influencers}
        results = []
        for r in recs:
            item = inf_map.get(str(r.get('id')))
            if item:
                c = item.copy()
                c['reason'] = r.get('reason', '추천 사유 없음')
                c['followers'] = format_w_to_man(str(c.get('followers', '0')))
                results.append(c)
        return {"recommendation": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 추천 실패: {str(e)}")


@router.post("/one-click")
async def one_click(req: OneClickRequest):
    # 이전 데이터 불러오기 모드: keyword를 이전 데이터로 대체
    if req.use_previous:
        prev = _load_previous_keyword()
        if not prev["keyword"]:
            raise HTTPException(status_code=404, detail="이전 데이터가 없습니다. 먼저 리서치를 실행해주세요.")
        keyword = prev["keyword"]
    else:
        keyword = req.keyword

    influencers = await _crawl_wanghong_list_impl()
    recs = await _recommend_by_deepseek(keyword, influencers, req.recommend_count)

    inf_map = {str(i.get("id")): i for i in influencers}
    name_map = {str(i.get("name", "")).strip(): i for i in influencers}
    out = []
    for r in recs:
        rec_id = str(r.get("id", "")).strip()
        # 1차: 숫자 id로 매칭
        item = inf_map.get(rec_id)
        # 2차: DeepSeek가 name을 id로 잘못 반환했을 때 name으로 fallback
        if not item:
            item = name_map.get(rec_id)
        if item:
            c = item.copy()
            c["followers"] = format_w_to_man(str(c.get("followers", "0")))
            if c.get("description"):
                c["description"] = await translate_zh_to_ko(c["description"])
            out.append(c)

    return {"status": "ok", "keyword": keyword, "recommendation": out[:req.recommend_count]}


@router.post("/login")
async def start_login():
    """
    Playwright Chromium 창을 직접 띄워 위챗 QR 로그인을 시작한다.
    로그인은 백그라운드 스레드에서 진행되며, 성공하면 쿠키가 자동 저장된다.
    """
    try:
        loop = asyncio.get_event_loop()
        loop.run_in_executor(_executor, _run_login_with_chromium)
        return {"status": "started", "message": "Chromium 창이 열렸습니다. 위챗 QR코드로 로그인해주세요."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"로그인 프로세스 시작 실패: {str(e)}")


@router.get("/detail-json")
async def get_wanghong_detail_json(
    anchor_id: Optional[str] = Query(None),
    id: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
):
    target_id = anchor_id or id
    if not target_id:
        raise HTTPException(status_code=422, detail="anchor_id 또는 id 파라미터가 필요합니다.")

    # 1) influencers.json 기본 정보
    base_info: dict = {}
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            influencers = json.load(f)
        base_info = {str(i.get("id")): i for i in influencers}.get(str(target_id), {})

    # 2) 크롤링 상세 정보
    crawled: dict = {}
    try:
        crawled = await _get_detail_impl(target_id, name or "")
    except HTTPException:
        raise
    except Exception as e:
        print(f"[detail-json] 크롤링 실패 (무시하고 계속): {e}")

    # 3) 표시 필드 순서
    DISPLAY_FIELDS = ["avatar", "name", "id", "followers", "growth_amount", "growth_rate", "score"]
    result: dict = {}

    for field in DISPLAY_FIELDS:
        label_ko = KEY_LABEL_KO.get(field, field)
        raw_value = base_info.get(field, "")

        if field == "name":
            result[label_ko] = raw_value
        elif field == "avatar":
            result[label_ko] = raw_value
        elif field == "followers":
            result[label_ko] = format_w_to_man(str(raw_value)) if raw_value else "0"
        elif field == "description":
            result[label_ko] = await translate_zh_to_ko(str(raw_value)) if raw_value else ""
        else:
            result[label_ko] = str(raw_value) if raw_value != "" else "0"

    # 4) 크롤링 추가 항목 병합
    for raw_key, raw_val in crawled.items():
        if raw_key == "ID":
            continue
        # 견적(报价) 키는 원본 중국어 key 유지 — 프론트가 k.includes('报价')로 필터링
        if "报价" in raw_key:
            result[raw_key] = str(raw_val) if raw_val else ""
        else:
            label_ko = KEY_LABEL_KO.get(raw_key, raw_key)
            result[label_ko] = format_w_to_man(str(raw_val)) if raw_val else "0"

    # 5) 수치 기반 사실 분석 생성
    #    수집된 실제 수치(게시물 수, 좋아요·저장 합계, 팔로워 증가율 등)만 사용.
    #    추측·가정 표현은 일절 사용하지 않는다.
    analysis = _build_fact_based_analysis(base_info, crawled)
    if analysis:
        result["__analysis__"] = analysis

    return {"status": "ok", "detail": result}


def _build_fact_based_analysis(base_info: dict, crawled: dict) -> str:
    """
    크롤링으로 수집된 실제 수치만 사용해 분석 텍스트를 조립한다.
    수집되지 않은 항목은 언급하지 않는다.
    """
    lines: list[str] = []

    # ── 팔로워 / 증가율 (influencers.json) ──
    followers_raw = base_info.get("followers", "")
    growth_rate = base_info.get("growth_rate", "")
    growth_amount = base_info.get("growth_amount", "")
    score = base_info.get("score", "")

    if followers_raw and followers_raw != "0":
        followers_ko = format_w_to_man(str(followers_raw))
        line = f"팔로워 수 {followers_ko}명"
        if growth_rate and growth_rate != "0%":
            line += f"이며, 최근 팔로워 증가율은 {growth_rate}입니다."
            if growth_amount and growth_amount not in ("0", followers_raw):
                line += f" (증가량 {format_w_to_man(str(growth_amount))}명)"
        else:
            line += "입니다."
        lines.append(line)

    if score and str(score) not in ("0", "0.0"):
        lines.append(f"灰豚 플랫폼 종합 점수는 {score}점입니다.")

    # ── 크롤링 수치 지표 (huitun 상세 페이지) ──
    # 한국어 라벨 우선, 없으면 중국어 원문 key 탐색
    def _get(ko_label: str, *zh_keys: str) -> str:
        v = crawled.get(ko_label, "")
        if not v or v == "0":
            for k in zh_keys:
                v = crawled.get(k, "")
                if v and v != "0":
                    break
        return str(v).strip() if v else ""

    note_count    = _get("게시물 수",       "笔记数",   "新增笔记")
    like_save     = _get("좋아요·저장 합계", "赞藏总数")
    avg_like      = _get("평균 좋아요 수",   "平均点赞", "平均点赞数")
    new_followers = _get("",                 "新增粉丝")
    hot_rate      = _get("",                 "热门率",   "热门笔记率")

    if note_count:
        lines.append(f"총 게시물 수는 {format_w_to_man(note_count)}건입니다.")
    if like_save:
        lines.append(f"게시물 전체의 좋아요·저장 합계는 {format_w_to_man(like_save)}입니다.")
    if avg_like:
        lines.append(f"게시물 1건당 평균 좋아요 수는 {format_w_to_man(avg_like)}입니다.")
    if new_followers:
        lines.append(f"최근 신규 팔로워는 {format_w_to_man(new_followers)}명입니다.")
    if hot_rate:
        lines.append(f"게시물 열람 기준 인기 콘텐츠 비율은 {hot_rate}입니다.")

    # ── 견적 요약 (수집된 경우) ──
    baojia_items = {k: v for k, v in crawled.items() if "报价" in k and v and v != "0"}
    if baojia_items:
        price_parts = []
        for k, v in list(baojia_items.items())[:3]:
            label = k.replace("报价_", "").replace("_", " ")
            price_parts.append(f"{label} {v}")
        lines.append("수집된 견적: " + " / ".join(price_parts))

    if not lines:
        return ""

    header = "※ 아래 분석은 灰豚数据 플랫폼에서 실시간 수집된 수치만을 근거로 합니다.\n"
    return header + "\n".join(f"• {l}" for l in lines)


@router.get("/detail")
async def get_wanghong_detail(anchor_id: str, name: str):
    async def generate():
        yield f"data: 🚀 '{name}' 정밀 분석 시작...\n\n"
        try:
            yield "data: 🖥️ 브라우저 캡처 중...\n\n"
            main_shot, price_shot = await _get_detail_vision_impl(anchor_id, name)

            yield "data: 🧠 AI Vision 분석 중...\n\n"
            ai_data = await extract_with_vision(main_shot, price_shot)

            for s in [main_shot, price_shot]:
                if os.path.exists(s):
                    os.remove(s)

            if ai_data:
                for key in ai_data:
                    if isinstance(ai_data[key], str):
                        ai_data[key] = format_w_to_man(ai_data[key])
                yield f"data: FINISHED:{json.dumps(ai_data)}\n\n"
            else:
                yield "data: ERROR: 분석 실패\n\n"
        except Exception as e:
            yield f"data: ERROR: {str(e)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


if __name__ == "__main__":
    async def test_run():
        print(">>> 왕홍 리스트 수집 시작")
        await crawl_wanghong_list()
    asyncio.run(test_run())
