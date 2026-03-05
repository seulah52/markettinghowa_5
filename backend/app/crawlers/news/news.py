import httpx
import re
import xml.etree.ElementTree as ET
from openai import AsyncOpenAI
from app.core.config import settings

# 전역 변수 설정
NewsData = {}

class NewsCrawler:
    def __init__(self):
        self.kotra_api_key = settings.kotra_news_api_key
        self.breaking_api_key = settings.breaking_news_api_key
        self.openai_api_key = settings.OPENAI_API_KEY
        self.client = AsyncOpenAI(api_key=self.openai_api_key) if self.openai_api_key else None

    async def _get_broad_category(self, keyword: str) -> str:
        """OpenAI를 사용하여 검색어를 최대한 넓은 범위의 핵심 산업군으로 변환합니다."""
        if not self.client:
            return keyword
        try:
            prompt = f"제품명 '{keyword}'가 속한 가장 큰 단위의 핵심 산업군 명칭을 단어 하나로 답변해줘. (예: 매트리스 -> 가구, 립스틱 -> 화장품)"
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=20,
                temperature=0
            )
            return re.sub(r'[^\w\s]', '', response.choices[0].message.content.strip())
        except:
            return keyword

    def _clean_title(self, title: str) -> str:
        """뉴스 제목에서 매체사 이름 및 특수문자를 제거하여 중복 체크용 순수 제목을 만듭니다."""
        # 1. 하이픈(-) 또는 대괄호([]) 뒤의 매체명 제거
        cleaned = re.sub(r'[\-\[\]].*$', '', title)
        # 2. 공백 및 특수문자 제거 후 핵심 15자 추출
        cleaned = re.sub(r'[^\w]', '', cleaned)
        return cleaned[:15]

    async def _summarize_news(self, title: str, content_snippet: str) -> str:
        """OpenAI를 사용하여 뉴스 내용을 요약합니다."""
        if not self.client:
            return "요약 불가"
        try:
            prompt = f"""
            뉴스 제목: {title}
            내용 정보: {content_snippet}
            
            위 뉴스를 바탕으로 해당 품목의 '중국 시장 동향' 또는 '수출입 현황'을 3문장 내외로 요약해줘.
            반드시 한국어로 답변해줘.
            """
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except:
            return "요약 실패"

    async def get_china_news(self, keyword: str) -> dict:
        """중복을 엄격히 배제하고 다양한 출처의 뉴스를 수집합니다."""
        global NewsData
        broad_category = await self._get_broad_category(keyword)
        print(f"\n>>> [5단계] '{keyword}' 분석을 위해 '{broad_category}' 산업군 뉴스를 수집합니다 (중복 필터링 적용).")
        
        news_list = []
        seen_titles = set()

        # 1. KOTRA 수집
        if self.kotra_api_key:
            url_kotra = "http://apis.data.go.kr/B551505/foreignMarketNews/getForeignMarketNewsList"
            params_kotra = {
                'serviceKey': self.kotra_api_key, 
                'searchKeyword': f"중국 {broad_category}", 
                'pageNo': '1', 'numOfRows': '10', 'type': 'json'
            }
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(url_kotra, params=params_kotra, timeout=10.0)
                    if resp.status_code == 200:
                        items = resp.json().get('response', {}).get('body', {}).get('items', {}).get('item', [])
                        if isinstance(items, dict): items = [items]
                        for item in items:
                            raw_title = item.get('newsTitl', '')
                            clean_t = self._clean_title(raw_title)
                            if clean_t not in seen_titles:
                                summary = await self._summarize_news(raw_title, item.get('newsAbst', ''))
                                news_list.append({"title": raw_title, "summary": summary, "source": "KOTRA"})
                                seen_titles.add(clean_t)
                                if len(news_list) >= 2: break
            except: pass

        # 2. Google News RSS 수집 (중복 체크 강화)
        if len(news_list) < 3:
            try:
                search_query = f"중국 {broad_category} 시장 전망"
                rss_url = f"https://news.google.com/rss/search?q={search_query}&hl=ko&gl=KR&ceid=KR:ko"
                async with httpx.AsyncClient() as client:
                    resp = await client.get(rss_url, timeout=10.0)
                    root = ET.fromstring(resp.content)
                    for item in root.findall('.//item'):
                        raw_title = item.findtext('title')
                        clean_t = self._clean_title(raw_title)
                        if clean_t not in seen_titles:
                            summary = await self._summarize_news(raw_title, "중국 시장 동향 리포트")
                            news_list.append({"title": raw_title, "summary": summary, "source": "시장 뉴스 리포트"})
                            seen_titles.add(clean_t)
                            if len(news_list) >= 3: break
            except: pass

        # 3. 최종 보정
        if not news_list:
            news_list = [{"title": f"중국 {broad_category} 시장 데이터 조회 불가", "summary": "현재 실시간 데이터를 확보하지 못했습니다.", "source": "시스템 안내"}]

        # 4. 터미널 출력 및 데이터 저장
        print("\n" + "=" * 60)
        print(f" [최근 {broad_category} 산업군 중국 시장 뉴스 - 총 {len(news_list[:3])}건]")
        print("-" * 60)
        for i, news in enumerate(news_list[:3], 1):
            print(f"({i}) 제목: {news['title']}")
            print(f"    출처: {news['source']}")
            print(f"    AI 요약: {news['summary']}")
            print("-" * 60)

        NewsData = {"news": news_list[:3]}
        return NewsData
