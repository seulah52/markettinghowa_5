import asyncio
from app.crawlers.xiaohongshu.crawler import XiaohongshuCrawler
from app.crawlers.taobao.crawler import TaobaoCrawler
from app.crawlers.baidu.crawler import BaiduCrawler
from app.ai.gemini.client import GeminiClient

async def run_analysis(keyword: str) -> dict:
    xhs     = XiaohongshuCrawler()
    taobao  = TaobaoCrawler()
    baidu   = BaiduCrawler()
    gemini  = GeminiClient()

    xhs_data, taobao_data, baidu_data = await asyncio.gather(
        xhs.crawl_analysis_data(keyword),
        taobao.crawl_analysis_data(keyword),
        baidu.get_index(keyword),
    )

    prompt = f"""
    Analyze the following Chinese market data for keyword: {keyword}
    Xiaohongshu data: {xhs_data}
    Taobao data: {taobao_data}
    Baidu index: {baidu_data}
    Provide a comprehensive market analysis in Korean.
    """
    summary = await gemini.generate(prompt)

    return {
        "keyword": keyword,
        "summary": summary,
        "raw": {"xhs": xhs_data, "taobao": taobao_data, "baidu": baidu_data},
    }
