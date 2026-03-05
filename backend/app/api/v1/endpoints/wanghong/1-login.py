from playwright.sync_api import sync_playwright
import time

def save_huitun_xhs_cookie():
    with sync_playwright() as p:
        # 실제 브라우저처럼 보이도록 User-Agent 설정
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent=user_agent
        )
        page = context.new_page()

        # 자동화 탐지 방지 스크립트
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        page.goto("https://xhs.huitun.com/#/login")
        
        print("★ 위챗(WeChat) QR코드로 로그인을 완료해주세요!")
        
        # 로그인 성공 후 나타나는 대시보드 요소를 기다림 (최대 2분)
        try:
            # 왼쪽 메뉴나 대시보드 아이콘 등 로그인 후에만 보이는 요소 대기
            page.wait_for_selector(".side-menu, .user-info, .dashboard", timeout=120000)
            print("✅ 로그인 성공 감지! 세션을 저장합니다...")
            time.sleep(3) # 안정적인 저장을 위해 잠시 대기
            
            context.storage_state(path="huitun_xhs_cookie.json")
            print("✅ 쿠키 저장 완료: huitun_xhs_cookie.json")
        except Exception as e:
            print(f"❌ 로그인 감지 실패 또는 시간 초과: {e}")
            # 실패하더라도 수동 저장 시도
            context.storage_state(path="huitun_xhs_cookie.json")
            
        browser.close()

if __name__ == "__main__":
    save_huitun_xhs_cookie()