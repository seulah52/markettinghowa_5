import httpx
import pandas as pd
from datetime import datetime
from app.core.config import settings

# 전역 변수 설정 (기존 호환성 유지용)
UnComtrade = {}

class UnComtradeCrawler:
    def __init__(self):
        self.api_key = settings.uncomtrade_api_key

    async def get_trade_stats(self, hs_code: str) -> dict:
        """UN Comtrade API를 사용하여 한국 대중국 무역액 데이터를 수집합니다."""
        global UnComtrade # global 선언을 함수 최상단으로 이동

        if not hs_code or hs_code == "000000":
            res = {"success": False, "stats": {}, "message": "유효하지 않은 HS Code입니다."}
            UnComtrade = res
            return res

        years = ",".join([str(datetime.now().year - i) for i in range(1, 6)])
        url = "https://comtradeapi.un.org/data/v1/get/C/A/HS"
        params = {
            'reporterCode': '410', 
            'partnerCode': '156',
            'period': years, 
            'cmdCode': hs_code,
            'flowCode': 'M,X', 
            'subscription-key': self.api_key
        }
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params, timeout=20.0)
                if resp.status_code != 200:
                    raise Exception(f"API 요청 실패 (Status: {resp.status_code})")
                
                raw_stats = resp.json().get('data', [])
                if raw_stats:
                    df = pd.DataFrame(raw_stats)
                    pivot = df.pivot_table(index='period', columns='flowCode', values='primaryValue', aggfunc='sum').fillna(0)
                    
                    if 'M' not in pivot.columns: pivot['M'] = 0
                    if 'X' not in pivot.columns: pivot['X'] = 0
                    
                    pivot['Import'] = pivot['M'] / 1000
                    pivot['Export'] = pivot['X'] / 1000
                    pivot['Balance'] = pivot['Export'] - pivot['Import']
                    
                    stats_dict = pivot.sort_index(ascending=False).to_dict(orient='index')
                    
                    UnComtrade = {"success": True, "stats": stats_dict}
                    return UnComtrade
                else:
                    raise ValueError("UN Comtrade에 해당 품목 데이터가 존재하지 않습니다.")
        except Exception as e:
            err_res = {"success": False, "stats": {}, "message": f"무역 통계 수집 실패: {str(e)}"}
            UnComtrade = err_res
            return err_res
