from app.crawlers.browser_pool import browser_pool

class DouyinCrawler:
    async def search_wanghong(self, keyword: str) -> list[dict]:
        ctx = await browser_pool.acquire()
        try:
            page = await ctx.new_page()
            await page.goto(f"https://www.douyin.com/search/{keyword}?type=user")
            await page.wait_for_timeout(2000)
            return []
        finally:
            await page.close()
            await browser_pool.release(ctx)
