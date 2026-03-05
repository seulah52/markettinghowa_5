import sys
import os

# 프로젝트 루트(backend) 폴더를 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import httpx
import structlog
import asyncio
from app.core.config import settings

logger = structlog.get_logger()

# 분석 결과를 저장할 전역 변수
DEEPSEEK_COMPETITOR_RESULT = {}

class DeepSeekCompetitorAnalysis:
    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        
    async def analyze(self, keyword: str) -> dict:
        global DEEPSEEK_COMPETITOR_RESULT
        if not self.api_key:
            return {"error": "API Key가 설정되지 않았습니다."}
            
        print(f"[DeepSeek] '{keyword}' 경쟁사 분석을 시작합니다...")
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                # 1. 경쟁사 10개 리스트업 및 선정 근거 도출
                print("[DeepSeek] 경쟁사 리스트업 중...")
                listup_prompt = f"""
                Identify 10 major competitors in the product category or industry related to the Chinese keyword '{keyword}'.
                
                Guidelines:
                - Include major Chinese local companies.
                - Include foreign companies that have successfully expanded into and performed well in the Chinese market.
                - STRICTLY EXCLUDE ANY SOUTH KOREAN COMPANIES FROM THE LIST.
                - Provide a clear and logical justification for why each company is considered a key competitor in the Chinese market.
                
                Return the result in a structured format in Korean.
                """
                payload_listup = {
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": "You are a professional business analyst."},
                        {"role": "user", "content": listup_prompt}
                    ],
                    "stream": False
                }
                res_listup = await client.post("https://api.deepseek.com/chat/completions", json=payload_listup, headers=headers, timeout=180.0)
                res_listup.raise_for_status()
                competitors_info = res_listup.json()['choices'][0]['message']['content'].strip()
                print(f"[DeepSeek] '{keyword}' 경쟁사 10개 리스트업 완료.")
                
                # 2. 리스트업된 경쟁사들에 대한 5FORCE 분석
                print("[DeepSeek] 경쟁사 5FORCE 분석 진행 중...")
                five_force_prompt = f"""
                Based on the following list of competitors for the keyword '{keyword}':
                
                {competitors_info}
                
                Perform a 5FORCE analysis (Threat of New Entrants, Bargaining Power of Buyers, Bargaining Power of Suppliers, Threat of Substitute Products, Intensity of Competitive Rivalry) for each competitor.
                For each of the 5 factors, provide a specific analysis based on recent data and INCLUDE a relevant source URL (e.g., news article, official report, or market research link) that supports the analysis.
                Format the output clearly for each competitor. Keep the analysis in Korean.
                """
                payload_5force = {
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": "You are a professional business analyst."},
                        {"role": "user", "content": five_force_prompt}
                    ],
                    "stream": False
                }
                res_5force = await client.post("https://api.deepseek.com/chat/completions", json=payload_5force, headers=headers, timeout=180.0)
                
                if res_5force.status_code != 200:
                    print(f"\n[DeepSeek 5FORCE 오류] 상태 코드: {res_5force.status_code}")
                    raise Exception(f"DeepSeek 5FORCE API 호출 실패: {res_5force.text}")

                five_force_analysis = res_5force.json()['choices'][0]['message']['content'].strip()
                
                DEEPSEEK_COMPETITOR_RESULT = {
                    "original_keyword": keyword,
                    "competitors_list": competitors_info,
                    "five_force_analysis": five_force_analysis
                }
                
                print("[DeepSeek] 분석 완료.")
                return DEEPSEEK_COMPETITOR_RESULT
                
        except Exception as e:
            logger.error(f"DeepSeek 분석 실패: {e}")
            print(f"[DeepSeek] 치명적 오류 발생: {e}")
            raise e # 더미 데이터를 반환하지 않고 에러를 던집니다.
