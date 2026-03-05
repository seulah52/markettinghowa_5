import os
import re
import json
from playwright.sync_api import sync_playwright

def scrape_xhs_anchors():
    if not os.path.exists("huitun_xhs_cookie.json"):
        print("❌ 오류: 'huitun_xhs_cookie.json' 파일이 없습니다. 먼저 1-login.py를 실행하세요.")
        return

    all_influencers = []
    seen_ids = set()

    with sync_playwright() as p:
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            storage_state="huitun_xhs_cookie.json",
            user_agent=user_agent
        )
        page = context.new_page()
        # 자동화 탐지 방지
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        url = "https://xhs.huitun.com/#/anchor/anchor_list?page=add"
        print(f"🚀 페이지 이동 중: {url}")
        
        try:
            page.goto(url, wait_until="networkidle", timeout=120000)
            
            print("🔍 '가구(家居家装)' 카테고리 찾는 중...")
            try:
                cat_btn = page.get_by_text("家居家装").first
                cat_btn.wait_for(state="visible", timeout=15000)
                print("✅ '家居家装' 카테고리 발견! 클릭합니다.")
                cat_btn.click()
            except:
                print("⚠️ 자동 카테고리 선택 실패. 15초 안에 직접 '가구' 카테고리를 선택해주세요!")
                page.wait_for_timeout(15000)
            
            print("⏳ 데이터 로딩 대기 중 (5초)...")
            page.wait_for_timeout(5000)

            print("🚀 수집 시작 (무한 스크롤 방식)...")
            
            scroll_attempts = 0
            max_scroll_attempts = 10 

            while True:
                if len(all_influencers) >= 99:
                    print(f"🎯 목표치(99명)를 달성했습니다. (현재 {len(all_influencers)}명)")
                    break

                id_indicators = page.get_by_text("ID：").all()
                new_found_in_this_round = 0

                for indicator in id_indicators:
                    try:
                        container = indicator.locator("xpath=./ancestor::tr | ./ancestor::div[contains(@class, 'item')] | ./ancestor::div[contains(@class, 'row')] | ./ancestor::div[contains(@class, 'el-table__row')]").first
                        if container.count() == 0:
                            container = indicator.locator("xpath=./../../..")

                        text = container.inner_text().strip()
                        
                        id_match = re.search(r"ID：\s*([a-zA-Z0-9_-]+)", text)
                        if not id_match: continue
                        anchor_id = id_match.group(1)
                        
                        if anchor_id in seen_ids: continue

                        # 데이터 파싱 로직
                        lines = [l.strip() for l in text.split('\n') if l.strip()]
                        img_el = container.locator("img").first
                        avatar_url = img_el.get_attribute("src") or "" if img_el.count() > 0 else ""

                        name = "Unknown"
                        for line in lines:
                            if not re.match(r"^\d+(\.\d+)?$", line) and "ID：" not in line and "灰豚" not in line and "等级" not in line:
                                name = line
                                break

                        # --- 숫자 데이터 정밀 추출 ---
                        # 1. 팔로워 (예: 133.96w)
                        followers_match = re.search(r"(\d+(\.\d+)?w)", text)
                        followers = followers_match.group(1) if followers_match else "0"
                        
                        # 2. 증가율 (예: 0.39%)
                        growth_rate_match = re.search(r"(\d+(\.\d+)?%)", text)
                        growth_rate = growth_rate_match.group(1) if growth_rate_match else "0%"
                        
                        # 3. 나머지 숫자들 (추천지수, 증가량)
                        # 텍스트에서 이미 찾은 팔로워와 증가율을 제외한 나머지 숫자들을 찾음
                        temp_text = text.replace(followers, "").replace(growth_rate, "")
                        # 숫자, 소수점, 콤마가 포함된 덩어리들을 모두 찾음
                        nums = re.findall(r"(\d[\d,.]*)", temp_text)
                        
                        score_val = "0"
                        growth_amount = "0"
                        
                        if len(nums) >= 1:
                            score_val = nums[0]
                        if len(nums) >= 2:
                            growth_amount = nums[1]

                        # --- 유효성 검사 (빈 데이터 및 시스템 메시지 제외) ---
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
                            "description": text.replace('\n', ' ')
                        }
                        
                        all_influencers.append(influencer)
                        seen_ids.add(anchor_id)
                        new_found_in_this_round += 1
                        print(f"   ✅ [{len(all_influencers)}] 수집: {name} (ID: {anchor_id})")
                    except Exception as e:
                        print(f"      ⚠️ 항목 수집 중 오류: {e}")
                        continue

                if new_found_in_this_round > 0:
                    with open("influencers.json", "w", encoding="utf-8") as f:
                        json.dump(all_influencers, f, ensure_ascii=False, indent=4)
                    scroll_attempts = 0 
                else:
                    scroll_attempts += 1

                print(f"⏳ 스크롤 중... (현재 총 {len(all_influencers)}명)")
                page.mouse.wheel(0, 3000) 
                page.wait_for_timeout(2000) 

                if scroll_attempts >= max_scroll_attempts:
                    next_btn = page.locator(".btn-next, .el-icon-arrow-right").last
                    if next_btn.is_visible() and next_btn.is_enabled():
                        print("➡️ '다음' 버튼 발견! 클릭합니다.")
                        next_btn.click()
                        scroll_attempts = 0
                        page.wait_for_timeout(4000)
                    else:
                        print("🏁 더 이상 새로운 데이터가 없습니다. 수집을 종료합니다.")
                        break

            all_influencers.sort(key=lambda x: x['score'], reverse=True)

            with open("influencers.json", "w", encoding="utf-8") as f:
                json.dump(all_influencers, f, ensure_ascii=False, indent=4)
            print(f"\n💾 총 {len(all_influencers)}명의 데이터 저장 완료 (influencers.json)")

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    scrape_xhs_anchors()
