import asyncio
import sys

# 윈도우에서 Playwright/Subprocess 지원을 위한 루프 정책 강제 설정
if sys.platform == 'win32':
    try:
        if not isinstance(asyncio.get_event_loop_policy(), asyncio.WindowsProactorEventLoopPolicy):
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
