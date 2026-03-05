import os
import re
import json
import time
from playwright.sync_api import sync_playwright

def extract_anchor_data(page, anchor_id):
    """상세 페이지에서 숫자 데이터를 추출하는 전용 함수"""
    
    # 1. 명시적 대기: 주요 데이터 레이블이나 컨테이너가 나타날 때까지 대기
    # '笔记数' 텍스트나 핵심 데이터 클래스가 보일 때까지 기다림
    try:
        # 데이터가 포함된 주요 컨테이너나 특정 클래스를 대기
        page.wait_for_selector(".detail-item-value, .info-value, text=笔记数", timeout=15000)
        # Vue/React 렌더링 안정화를 위해 짧게 대기
        page.wait_for_timeout(1500)
    except Exception as e:
        print(f"⚠️ 데이터 로딩 지연 또는 요소를 찾을 수 없습니다 (ID: {anchor_id})")

    # 페이지 전체 텍스트 가져오기
    page_text = page.evaluate("() => document.body.innerText")

    # 숫자 추출 정규식 함수 (라벨 뒤의 숫자+단위 추출)
    def get_val(label):
        # 라벨 뒤에 나오는 숫자(w, +, . 포함) 추출
        pattern = rf"{label}\D*([\d\.w,w+]+)(?!%)"
        match = re.search(pattern, page_text)
        return match.group(1).strip() if match else "0"

    # 기본 추출 시도
    detail_data = {
        "ID": anchor_id,
        "笔记数": get_val("笔记数"),
        "赞藏总数": get_val("赞藏总数"),
        "关注数": get_val("关注数"),
        "新增笔记": get_val("新增笔记"),
        "平均点赞": get_val("平均点赞"),
        "粉丝数": get_val("粉丝数")
    }

    # 2. 셀렉터 최적화 백업 로직: 정규식 실패 시 특정 클래스 기반으로 재시도
    if detail_data["笔记数"] == "0" or detail_data["粉丝数"] == "0":
        try:
            # 숫자가 들어있는 공통 클래스들 탐색
            vals = page.locator(".detail-item-value, .info-value, .data-num, b").all_inner_texts()
            # 텍스트가 비어있지 않은 것들만 필터링
            vals = [v.strip() for v in vals if v.strip()]
            
            if len(vals) >= 5:
                # 데이터 매칭 (사이트 구조에 따라 순서가 다를 수 있음)
                # 우선순위가 낮은 경우에만 백업 데이터 활용
                if detail_data["笔记数"] == "0": detail_data["笔记数"] = vals[0]
                if detail_data["粉丝数"] == "0": detail_data["粉丝数"] = vals[-1]
        except:
            pass

    return detail_data

def get_anchor_detail(anchor_id):
    if not os.path.exists("huitun_xhs_cookie.json"):
        print("❌ 오류: 'huitun_xhs_cookie.json' 파일이 없습니다. 먼저 1-login.py를 실행하세요.")
        return

    print(f"🚀 ID: {anchor_id} 상세 데이터 수집 시작...")

    with sync_playwright() as p:
        # --- 페이지 진입 경로 코드 (보존) ---
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            storage_state="huitun_xhs_cookie.json",
            user_agent=user_agent
        )
        page = context.new_page()

        # 직접 상세 페이지 URL로 접속
        url = f"https://xhs.huitun.com/#/anchor/anchor_detail?id={anchor_id}"
        page.goto(url, wait_until="networkidle")
        # ----------------------------------

        # 데이터 추출 함수 호출
        detail_data = extract_anchor_data(page, anchor_id)

        browser.close()
        return detail_data

if __name__ == "__main__":
    test_ids = ["103644785", "120841490", "1272"]
    
    results = []
    for aid in test_ids:
        data = get_anchor_detail(aid)
        if data:
            print("-" * 30)
            for key, val in data.items():
                print(f"📊 {key}: {val}")
            print("-" * 30)
            results.append(data)
            time.sleep(2)

    with open("anchor_details_result.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    # f-string 문법 오류 수정
    print("\n✅ 수집 완료: anchor_details_result.json 에 저장되었습니다.")
