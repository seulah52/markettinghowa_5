import asyncio
import os
import sys

# Ensure backend folder is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.crawlers.baidu.crawler import BaiduCrawler
from app.core.config import settings

async def test_baidu_crawler():
    print(f"Baidu Index API Key from Settings: {settings.baidu_index_api_key}")
    
    crawler = BaiduCrawler()
    result = await crawler.get_index("小红书")
    
    print("Extraction Results:")
    print(f"Keyword: {result['keyword']}")
    print(f"Index: {result.get('index', 0)}")
    print(f"Age: {result.get('demographics', {}).get('age', {})}")
    print(f"Gender: {result.get('demographics', {}).get('gender', {})}")
    if 'error' in result:
        print(f"Error: {result['error']}")

if __name__ == "__main__":
    asyncio.run(test_baidu_crawler())
