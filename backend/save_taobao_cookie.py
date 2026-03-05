import asyncio
import os
from playwright.async_api import async_playwright

async def save_taobao_cookie():
    cookie_path = os.path.join("storage", "cookies", "taobao_cookie.json")
    os.makedirs(os.path.dirname(cookie_path), exist_ok=True)

    async with async_playwright() as p:
        print("\n[알림] 타오바오 로그인을 위해 브라우저를 실행합니다...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print("단계: 타오바오 메인 페이지로 이동합니다.")
        await page.goto("https://www.taobao.com")
        
        print("\n============================================================")
        print("1. 열린 브라우저 창에서 타오바오 로그인을 직접 완료하세요.")
        print("2. 로그인이 완료되면 이 터미널로 돌아와서 [Enter] 키를 누르세요.")
        print("============================================================\n")
        
        await asyncio.to_thread(input, "로그인 완료 후 Enter를 누르세요...")

        await context.storage_state(path=cookie_path)
        print(f"\n[성공] 타오바오 쿠키가 저장되었습니다: {cookie_path}")
        
        await browser.close()

if __name__ == "__main__":
    try:
        asyncio.run(save_taobao_cookie())
    except Exception as e:
        print(f"\n[오류] 실행 중 문제가 발생했습니다: {e}")
