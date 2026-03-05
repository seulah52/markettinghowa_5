import pandas as pd

class StrategyService:
    def generate_strategy(self, trade_stats: dict) -> dict:
        """수집된 무역 통계(stats)를 바탕으로 성장률(CAGR) 계산 및 진입 전략을 생성합니다."""
        if not trade_stats:
            return {"cagr": 0.0, "comment": "데이터 부족으로 전략 수립 불가", "action_plans": []}

        try:
            # 딕셔너리를 DataFrame으로 변환하여 계산
            df = pd.DataFrame.from_dict(trade_stats, orient='index').sort_index()
            exp = df['Export']
            
            if len(exp) >= 2 and exp.iloc[0] > 0:
                cagr = ((exp.iloc[-1] / exp.iloc[0]) ** (1/max(1, len(exp)-1)) - 1) * 100
            else:
                cagr = 0.0

            if cagr > 10:
                comment = f"수출 성장률이 {cagr:.1f}%로 매우 가파릅니다. 현재 중국 시장 내 수요가 폭발적으로 증가하고 있어 '공격적인 시장 확장 및 선점 전략'이 요구됩니다."
                action_plans = [
                    "공격적 마케팅: 도우인/샤오홍슈 라이브 커머스 비중 확대",
                    "유통망 확장: 중국 내륙 2선 도시 거점 물류 확보"
                ]
                force_scores = [4, 2, 3, 5, 2]
            else:
                comment = f"수출 성장률이 {cagr:.1f}%로 정체 또는 하락세입니다. 단순 가격 경쟁보다는 '리스크 관리 및 프리미엄 브랜드 차별화 전략'을 통한 틈새 시장 공략이 필요합니다."
                action_plans = [
                    "제품 고도화: 현지 맞춤형 기능 추가 및 디자인 리뉴얼",
                    "인증 강화: 중국 GB 표준 및 CCC 인증 선제적 갱신"
                ]
                force_scores = [5, 4, 2, 4, 3]

            return {
                "cagr": round(cagr, 2),
                "comment": comment,
                "action_plans": action_plans,
                "force_scores": force_scores
            }
        except:
            return {"cagr": 0.0, "comment": "분석 중 오류 발생", "action_plans": []}
