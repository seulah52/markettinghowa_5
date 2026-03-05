from playwright.async_api import async_playwright, BrowserContext
import asyncio

class BrowserPool:
    def __init__(self, size: int = 3):
        self.size = size
        self._pool: list[BrowserContext] = []
        self._lock = asyncio.Lock()

    async def init(self):
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        for _ in range(self.size):
            ctx = await browser.new_context(locale="zh-CN")
            self._pool.append(ctx)

    async def acquire(self) -> BrowserContext:
        async with self._lock:
            return self._pool.pop()

    async def release(self, ctx: BrowserContext):
        async with self._lock:
            self._pool.append(ctx)

browser_pool = BrowserPool()
