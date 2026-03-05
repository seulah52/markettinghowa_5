import asyncio
import os
from playwright.async_api import async_playwright

async def save_xhs_cookie():
    # 저장 경로 설정
    cookie_dir = os.path.join(os.getcwd(), "storage", "cookies")
    if not os.path.exists(cookie_dir):
        os.makedirs(cookie_dir)
    cookie_path = os.path.join(cookie_dir, "xhs_cookie.json")

    async with async_playwright() as p:
        # 브라우저 실행 (사용자가 직접 조작할 수 있도록 headless=False)
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print("\n" + "="*60)
        print("1. 브라우저 창에서 샤오홍슈에 로그인해 주세요 (QR코드 등)")
        print("2. 로그인이 완전히 완료되면 이 터미널로 돌아오세요.")
        print("3. '엔터(Enter)' 키를 누르면 쿠키가 자동으로 저장됩니다.")
        print("="*60)

        # 샤오홍슈 메인 페이지 이동
        await page.goto("https://www.xiaohongshu.com")

        # 사용자 입력 대기 (동기식 input 사용을 위해 별도 처리)
        await asyncio.get_event_loop().run_in_executor(None, input, "로그인 완료 후 엔터를 눌러주세요...")

        # 현재 상태 저장
        await context.storage_state(path=cookie_path)
        print(f"\n[성공] 쿠키가 저장되었습니다: {cookie_path}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(save_xhs_cookie())
