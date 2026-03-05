import httpx
import re
import xml.etree.ElementTree as ET
from openai import AsyncOpenAI
from app.core.config import settings

# 전역 변수 설정 (기존 호환성 유지용)
HsCode = {}

class CustomsCrawler:
    def __init__(self):
        self.hs_code_api_key = settings.hs_code_api_key
        self.openai_api_key = settings.OPENAI_API_KEY
        self.client = AsyncOpenAI(api_key=self.openai_api_key) if self.openai_api_key else None

    async def _search_definition(self, keyword: str) -> str:
        """Google 검색을 통해 제품의 정의 및 특징을 내부적으로 학습합니다."""
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            search_url = f"https://www.google.com/search?q={keyword}+definition+product+features"
            async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
                resp = await client.get(search_url, timeout=10.0)
                text = resp.text
                snippets = re.findall(r'<(?:div|span) [^>]*class="[^"]*(?:vvsy70|BNeawe|s3eb4c|VwiC3b)[^"]*"[^>]*>(.*?)</(?:div|span)>', text)
                return " ".join(snippets[:5]) if snippets else "검색된 정의 없음"
        except:
            return "정보 검색 실패"

    async def _generalize_keyword(self, keyword: str) -> str:
        """OpenAI를 사용하여 검색어를 HS Code 검색이 용이한 일반적인 제품군으로 변환합니다."""
        if not self.client: return keyword
        try:
            prompt = f"품목명 '{keyword}'을(를) HS Code 검색이 용이한 더 넓은 범위의 '일반적인 제품군' 명칭(한국어)으로 변환하세요. (예: '나이키 에어맥스' -> '신발', '고급 실크 핸드백' -> '핸드백') 명칭만 한 단어로 답변하세요."
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[HS Code] 키워드 일반화 실패: {e}")
            return keyword

    async def get_hs_code(self, keyword: str, is_retry: bool = False) -> dict:
        """학습된 정의를 바탕으로 OpenAI가 적합한 HS Code를 추출합니다. 실패 시 제품군으로 변환하여 재시도합니다."""
        global HsCode
        
        # 1. 내부 검색을 통한 학습 시도
        context = await self._search_definition(keyword)
        
        # 2. OpenAI를 이용한 지능형 매핑
        if self.client:
            try:
                prompt = f"""
                당신은 국제 무역 및 관세 전문가입니다. 
                다음 제품에 대해 가장 적절한 '국제 표준 HS Code (6자리)'를 선정하고 그 정의를 설명하세요.
                
                제품명: {keyword}
                참고 정보: {context}
                
                [응답 규칙]
                1. HS Code는 반드시 6자리 숫자여야 합니다. (예: 8517.13 또는 851713)
                2. 설명은 해당 HS Code가 정의하는 국제적인 제품 범주를 객관적으로 서술하세요.
                
                [응답 형식]
                HS Code: [6자리 숫자]
                설명: [품목 정의]
                """
                response = await self.client.chat.completions.create(
                    model=settings.OPENAI_API_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0
                )
                res_text = response.choices[0].message.content.strip()
                
                code_match = re.search(r"(?:HS\s*Code|코드)[:\s\*]*([\d\.]+)", res_text, re.IGNORECASE)
                desc_match = re.search(r"(?:설명|정의)[:\s\*]*(.*)", res_text, re.DOTALL | re.IGNORECASE)
                
                if code_match and desc_match:
                    clean_code = "".join(re.findall(r"\d", code_match.group(1)))[:6]
                    if len(clean_code) == 6:
                        res_data = {
                            "hs_code": clean_code,
                            "item_name": keyword,
                            "description": desc_match.group(1).strip(),
                            "mapping_method": f"OpenAI ({settings.OPENAI_API_MODEL})" if not is_retry else f"OpenAI Retry ({keyword})"
                        }
                        HsCode = res_data
                        return res_data
            except Exception as e:
                print(f"[HS Code] OpenAI 매핑 중 오류: {e}")

        # 3. 관세청 API (OpenAI 실패 시)
        if self.hs_code_api_key:
            url = "https://unipass.customs.go.kr/openapi/services/index/portal/proxy/hs/getItemClassificationList"
            params = {'crkyCn': self.hs_code_api_key, 'itemNm': keyword}
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(url, params=params, timeout=10)
                    if resp.status_code == 200 and resp.content:
                        root = ET.fromstring(resp.content)
                        item = root.find('.//itemClassificationList')
                        if item is not None:
                            res_data = {
                                "hs_code": item.findtext('hsCd')[:6],
                                "item_name": item.findtext('itemNm'),
                                "description": f"관세청 DB 기반 '{keyword}' 분류 코드",
                                "mapping_method": "Customs API" if not is_retry else f"Customs API Retry ({keyword})"
                            }
                            HsCode = res_data
                            return res_data
            except Exception as e:
                print(f"[HS Code] 관세청 API 호출 중 오류: {e}")

        # 4. 실패 시 제품군 변환 후 재시도
        if not is_retry:
            general_keyword = await self._generalize_keyword(keyword)
            if general_keyword != keyword:
                print(f"[HS Code] '{keyword}' 매핑 실패 -> 제품군 '{general_keyword}'(으)로 재시도합니다.")
                return await self.get_hs_code(general_keyword, is_retry=True)

        # 최종 실패
        error_res = {"error": "HS Code 매핑 실패", "hs_code": "000000", "mapping_method": "Failed"}
        HsCode = error_res
        return error_res
