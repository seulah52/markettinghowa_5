import os
import sys
import asyncio

# Windows에서 Playwright subprocess 지원을 위해 ProactorEventLoop 정책 설정
# 주의: 루프를 직접 생성/설정하면 uvicorn의 루프 관리와 충돌하므로 정책만 설정
if sys.platform == 'win32':
    policy = getattr(asyncio, "WindowsProactorEventLoopPolicy", None)
    if policy:
        asyncio.set_event_loop_policy(policy())

import httpx
import json
import pandas as pd
import numpy as np
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from dotenv import load_dotenv
from openai import AsyncOpenAI
import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import re
from typing import Any, Dict, List, Optional

# 프로젝트 루트(backend) 폴더를 경로에 추가
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.append(ROOT_DIR)

from app.core.config import settings

# .env 환경 변수 로드
load_dotenv()

logger = structlog.get_logger()
router = APIRouter()

# 데이터 저장 경로 설정 (backend/storage/data)
DATA_STORAGE_DIR = os.path.join(ROOT_DIR, "storage", "data")
if not os.path.exists(DATA_STORAGE_DIR):
    os.makedirs(DATA_STORAGE_DIR)

# 전역 변수 설정
KEYWORD = ""
GLOBAL_FINAL_REPORT = {}

# DeepSeek API 설정
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
deepseek_client = AsyncOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
) if DEEPSEEK_API_KEY else None
DEEPSEEK_MODEL = "deepseek-chat"

class AnalysisRequest(BaseModel):
    keyword: str

@router.post("/start")
async def api_start_analysis(req: AnalysisRequest):
    """프론트엔드에서 호출하는 통합 분석 엔드포인트"""
    try:
        result = await run_full_analysis(req.keyword)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error("analysis_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Wanghong matching (used by /wanghong one-click)
# =============================================================================

WANGHONG_MATCH_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "recommendations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["id", "reason"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["recommendations"],
    "additionalProperties": False,
}


async def recommend_wanghong_by_keyword(
    keyword_kr: str,
    influencers: List[Dict[str, Any]],
    recommend_count: int = 10,
    *,
    client: Optional[AsyncOpenAI] = None,
) -> List[Dict[str, str]]:
    """
    왕홍 리스트(크롤링 결과)와 입력 키워드를 받아,
    연관성 높은 왕홍을 선별해 id + reason(한국어)만 반환한다.
    """
    if not keyword_kr.strip():
        return []
    if not influencers:
        return []

    # DeepSeek 클라이언트 우선 사용
    c = deepseek_client or AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    model = DEEPSEEK_MODEL if deepseek_client else settings.OPENAI_API_MODEL
    # 토큰/비용 방어: 100명까지만 전달
    sample = influencers[:100]

    prompt = f"""You are an expert in Chinese influencer (Wanghong) marketing.

[User Keyword (Korean)]
{keyword_kr}

[Wanghong Candidate List (JSON)]
{json.dumps(sample, ensure_ascii=False)}

[Mission]
Select the {recommend_count} most relevant Wanghong influencers for the given keyword.

[Rules]
- Write the "reason" field in Korean, specifically in 2-4 sentences.
- No exaggeration or speculation. Base your reasoning strictly on the data provided (description, metrics).
- Output JSON only. Follow this schema exactly:
{{ "recommendations": [{{"id":"...","reason":"..."}},...] }}
"""

    resp = await c.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You are a strict JSON generator. Output ONLY valid JSON."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.4,
    )

    raw = resp.choices[0].message.content or "{}"
    try:
        data = json.loads(raw)
    except Exception:
        # 혹시라도 주변 텍스트가 섞였을 때 최소 복구
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        data = json.loads(m.group(0)) if m else {"recommendations": []}

    recs = data.get("recommendations", [])
    out: List[Dict[str, str]] = []
    for r in recs:
        if not isinstance(r, dict):
            continue
        _id = str(r.get("id", "")).strip()
        reason = str(r.get("reason", "")).strip()
        if _id and reason:
            out.append({"id": _id, "reason": reason})

    return out[: max(1, int(recommend_count or 10))]

def save_data_to_file(filename, data):
    """수집된 데이터를 개별 파일(JSON)로 저장"""
    file_path = os.path.join(DATA_STORAGE_DIR, filename)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_data_from_file(filename):
    """저장된 파일에서 데이터 로드"""
    file_path = os.path.join(DATA_STORAGE_DIR, filename)
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

# =============================================================================
# 번역 함수 (2단계 번역 - 모든 중간 단계는 OpenAI/DeepSeek, 최종 한국어는 OpenAI)
# =============================================================================

async def translate_kr_en_cn(text):
    """
    2단계 번역: 한국어 -> 영어 -> 중국어
    모든 단계에서 OpenAI를 사용합니다.
    """
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    # 단계 1: 한국어 -> 영어
    res_en = await client.chat.completions.create(
        model=settings.OPENAI_API_MODEL,
        messages=[
            {"role": "system", "content": "You are a translator. Translate Korean to English. Return ONLY the English term, no explanation."},
            {"role": "user", "content": text}
        ],
        temperature=0.3,
    )
    en_text = res_en.choices[0].message.content.strip()
    
    # 단계 2: 영어 -> 중국어
    res_cn = await client.chat.completions.create(
        model=settings.OPENAI_API_MODEL,
        messages=[
            {"role": "system", "content": "You are a translator. Translate English to Simplified Chinese. Return ONLY the Chinese term, no explanation."},
            {"role": "user", "content": en_text}
        ],
        temperature=0.3,
    )
    cn_text = res_cn.choices[0].message.content.strip()
    
    return cn_text

async def translate_cn_en_kr(text_cn):
    """
    2단계 번역: 중국어 -> 영어 -> 한국어
    단계 1,2: DeepSeek 사용 (중국어 → 영어)
    단계 2,3: OpenAI 사용 (영어 → 한국어)
    """
    # 단계 1: 중국어 -> 영어 (DeepSeek 우선, 없으면 OpenAI)
    if deepseek_client:
        res_en = await deepseek_client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": "You are a translator. Translate Chinese to English. Return ONLY the English term, no explanation."},
                {"role": "user", "content": text_cn}
            ],
            temperature=0.3,
        )
    else:
        res_en = await AsyncOpenAI(api_key=settings.OPENAI_API_KEY).chat.completions.create(
            model=settings.OPENAI_API_MODEL,
            messages=[
                {"role": "system", "content": "You are a translator. Translate Chinese to English. Return ONLY the English term, no explanation."},
                {"role": "user", "content": text_cn}
            ],
            temperature=0.3,
        )
    en_text = res_en.choices[0].message.content.strip()
    
    # 단계 2: 영어 -> 한국어 (OpenAI만 사용 - 한국어 정제)
    res_kr = await AsyncOpenAI(api_key=settings.OPENAI_API_KEY).chat.completions.create(
        model=settings.OPENAI_API_MODEL,
        messages=[
            {"role": "system", "content": "You are a translator. Translate English to Korean. Return ONLY the Korean term, no explanation."},
            {"role": "user", "content": en_text}
        ],
        temperature=0.3,
    )
    kr_text = res_kr.choices[0].message.content.strip()
    
    return kr_text

async def get_baidu_keyword(text_cn):
    """
    중국어 검색어를 바이두 지수 검색에 적합한 대표 키워드로 변환
    OpenAI가 처리합니다.
    """
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    prompt = f"Convert the following Chinese product name '{text_cn}' into the most representative and general Chinese keyword that would have measurable search volume on Baidu Index. (e.g. '高品质丝绸手提包' -> '手提包'). Reply with ONLY the Chinese keyword, no explanation."
    res = await client.chat.completions.create(
        model=settings.OPENAI_API_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return res.choices[0].message.content.strip()

async def get_industry_category(text):
    """
    입력된 검색어를 큰 틀의 산업군(한국어/중국어)으로 변환
    한국어 정제는 OpenAI가, 중국어 번역은 2단계 번역(한영중)으로 수행합니다.
    """
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    prompt = f"What broad industry category does the product '{text}' belong to? Reply with ONLY one Korean word for the industry name. (e.g. lipstick -> 화장품, Galaxy phone -> 스마트폰)"
    res = await client.chat.completions.create(
        model=settings.OPENAI_API_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    industry_kr = res.choices[0].message.content.strip()
    
    # 산업군 한국어 -> 영어 -> 중국어 (2단계 번역)
    industry_cn = await translate_kr_en_cn(industry_kr)
    return {"kr": industry_kr, "cn": industry_cn}

async def extract_competitors(keyword_cn, industry_cn, taobao_data, xhs_data):
    """
    수집된 데이터와 시장 정보를 기반으로 경쟁사 5개씩 추출
    OpenAI가 처리하며, description/main_product/origin은 2단계 번역(중→영→한)으로 한국어화합니다.
    """
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    # 데이터 요약 (LLM 전달용)
    taobao_titles = [p.get('title', '') for p in taobao_data[:10]]
    xhs_titles = [p.get('title', '') for p in xhs_data[:10]]
    
    prompt = f"""You are a China market analyst. Based on the following data and market knowledge, create a competitor list.

[Data]
- Search keyword (Chinese): {keyword_cn}
- Industry category (Chinese): {industry_cn}
- Taobao search results (sample): {taobao_titles}
- Xiaohongshu search results (sample): {xhs_titles}

[Requirements]
1. List 5 major competing brands/companies in the Chinese market for the product '{keyword_cn}'.
2. List 5 major competing brands/companies in the Chinese market for the entire '{industry_cn}' industry.
3. For each brand, include:
   - name: Brand name (keep original brand name, do not translate)
   - main_product: Main product in Korean
   - origin: 중국 로컬 기업 or 외국계 기업 (국적 명시)
   - description: One-line characteristic in Korean

Reply with JSON only:
{{
  "keyword_competitors": [
    {{ "name": "brand", "main_product": "제품명(한국어)", "origin": "origin", "description": "한국어 설명" }}, ... (5 items)
  ],
  "industry_competitors": [
    {{ "name": "brand", "main_product": "제품명(한국어)", "origin": "origin", "description": "한국어 설명" }}, ... (5 items)
  ]
}}
"""
    
    res = await client.chat.completions.create(
        model=settings.OPENAI_API_MODEL,
        messages=[
            {"role": "system", "content": "You are a professional market analyst. All text fields except 'name' must be written in Korean. Output ONLY valid JSON."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.4,
    )
    competitors = json.loads(res.choices[0].message.content)

    # 2단계 번역: 혹시 남아있는 중국어 필드를 한국어로 후처리
    for group_key in ['keyword_competitors', 'industry_competitors']:
        for c in competitors.get(group_key, []):
            for field in ['main_product', 'origin', 'description']:
                val = c.get(field, '')
                # 중국어 문자(CJK)가 포함된 경우에만 번역
                if val and re.search(r'[\u4e00-\u9fff]', val):
                    try:
                        c[field] = await translate_cn_en_kr(val)
                    except Exception as e:
                        print(f"   [번역 경고] {field} 번역 실패: {e}")

    # 터미널 출력
    print("\n" + "="*50)
    print(f">>> [경쟁사 분석 결과]")
    print(f"소분류 키워드({keyword_cn}) 관련 경쟁사:")
    for c in competitors.get('keyword_competitors', []):
        print(f" - {c['name']} | {c['main_product']} | {c['origin']} | {c['description']}")
    
    print(f"\n산업군({industry_cn}) 관련 경쟁사:")
    for c in competitors.get('industry_competitors', []):
        print(f" - {c['name']} | {c['main_product']} | {c['origin']} | {c['description']}")
    print("="*50 + "\n")

    return competitors

async def run_full_analysis(user_in):
    global KEYWORD
    # 모듈 임포트
    from app.crawlers.taobao.crawler import TaobaoCrawler
    from app.crawlers.xiaohongshu.crawler import XiaohongshuCrawler
    from app.crawlers.baidu.crawler import BaiduCrawler
    import app.crawlers.customs.hscode as hscode_mod
    import app.crawlers.uncomtrade.uncom as uncom_mod
    import app.crawlers.news.news as news_mod

    print(f"[통합 분석] '{user_in}'에 대한 고도화된 순차 조사를 시작합니다... (2단계 번역 최적화 버전)")
    
    # 0. 번역 및 키워드 최적화 (2단계 번역)
    KEYWORD = await translate_kr_en_cn(user_in)
    BAIDU_KEYWORD = await get_baidu_keyword(KEYWORD)
    industry_info = await get_industry_category(user_in)
    print(f"   [준비] 번역 및 키워드 최적화 완료: {user_in} -> {KEYWORD} (바이두용: {BAIDU_KEYWORD})")
    
    # 객체 초기화
    xhs = XiaohongshuCrawler()
    baidu = BaiduCrawler()
    taobao = TaobaoCrawler()
    customs = hscode_mod.CustomsCrawler()
    uncomtrade = uncom_mod.UnComtradeCrawler()
    news = news_mod.NewsCrawler()

    # 1단계: 샤오홍슈 수집
    print("\n>>> [1단계] 샤오홍슈 수집 (소비 트렌드 분석용)...")
    try:
        xhs_data = await xhs.crawl_analysis_data(KEYWORD, target_count=30)
        if not xhs_data:
            print("   [정보] 수집된 새로운 데이터가 없습니다. 기존 데이터를 유지합니다.")
            xhs_data = load_data_from_file("xhs_result.json") or []
        else:
            save_data_to_file("xhs_result.json", xhs_data)
            
            # [추가] 해시태그 별도 파싱 및 저장 로직
            all_tags = []
            for item in xhs_data:
                desc = item.get("description", "")
                # #으로 시작하는 태그 추출 (공백이나 줄바꿈 기준)
                tags = re.findall(r'#([^\s#]+)', desc)
                all_tags.extend(tags)
            
            # 중복 제거 및 저장
            unique_tags = list(set(all_tags))
            save_data_to_file("xhs_tag.json", {"tags": unique_tags, "count": len(unique_tags)})
            print(f"   [완료] 샤오홍슈 해시태그 {len(unique_tags)}개 추출 및 xhs_tag.json 저장 완료.")

    except Exception as e:
        print(f"   [경고] 샤오홍슈 수집 중 오류 발생: {e}. 기존 저장된 데이터를 사용합니다.")
        xhs_data = load_data_from_file("xhs_result.json") or []
    
    # 2단계: 바이두 인덱스
    print("\n>>> [2단계] 바이두 인덱스 수집 (소비자 관심도 분석용)...")
    baidu_data = await baidu.get_index(BAIDU_KEYWORD)
    save_data_to_file("baidu_result.json", baidu_data)
    
    # 3단계: 타오바오 수집
    print("\n>>> [3단계] 타오바오 수집 (시장 가격 및 소비자 만족도 분석용)...")
    try:
        taobao_data = await taobao.crawl_analysis_data(KEYWORD, target_count=20)
        if taobao_data:
            save_data_to_file("taobao_result.json", taobao_data)
        else:
            print("   [정보] 수집된 새로운 데이터가 없습니다. 기존 데이터를 유지합니다.")
            taobao_data = load_data_from_file("taobao_result.json") or []
    except Exception as e:
        print(f"   [경고] 타오바오 수집 중 오류 발생: {e}. 기존 저장된 데이터를 사용합니다.")
        taobao_data = load_data_from_file("taobao_result.json") or []
    
    # 4단계: HS Code 및 무역 데이터
    print("\n>>> [4단계] HS Code 지능형 매핑 및 무역 데이터 수집...")
    
    hs_res = await customs.get_hs_code(user_in)
    trade_res = await uncomtrade.get_trade_stats(hs_res.get('hs_code', '000000'))
    
    save_data_to_file("hs_code_result.json", hs_res)
    save_data_to_file("trade_stats_result.json", trade_res)
    save_data_to_file("industry_trade_stats_result.json", {"success": False, "message": "Product-level analysis only"})

    print(f"   - [{user_in}] HS Code: {hs_res.get('hs_code')} ({hs_res.get('mapping_method', 'Failed')})")
    if trade_res.get('success'):
        recent_year = sorted(trade_res['stats'].keys(), reverse=True)[0]
        recent_val = trade_res['stats'][recent_year]
        print(f"   - [{user_in}] 최근 대중국 수출액({recent_year}): ${recent_val.get('Export', 0):,.0f}K")
    
    # 5단계: 뉴스 및 경쟁사 분석
    print("\n>>> [5단계] 뉴스 수집 및 경쟁사 리스트업...")
    await news.get_china_news(user_in)
    save_data_to_file("news_result.json", news_mod.NewsData)
    
    competitors = await extract_competitors(KEYWORD, industry_info['cn'], taobao_data, xhs_data)
    save_data_to_file("competitor_result.json", competitors)
    
    # 6단계: OpenAI 기반 최종 리포트 합성
    print("\n>>> [6단계] OpenAI AI 데이터 통합 심층 분석 및 최종 리포트 생성 중...")
    
    xhs_final = load_data_from_file("xhs_result.json") or []
    baidu_final = load_data_from_file("baidu_result.json") or {}
    taobao_final = load_data_from_file("taobao_result.json") or []
    hs_final = load_data_from_file("hs_code_result.json") or {}
    trade_final = load_data_from_file("trade_stats_result.json") or {}
    news_final = load_data_from_file("news_result.json") or {}
    comp_final = load_data_from_file("competitor_result.json") or {}

    # OpenAI 분석용 데이터 요약
    summary_data = {
        "target": {
            "kr": user_in, "cn": KEYWORD, 
            "industry": industry_info['kr'],
            "hs_code": hs_final.get('hs_code'), 
            "hs_definition": hs_final.get('description')
        },
        "trade_stats": trade_final.get('stats'),
        "competitors": comp_final,
        "xiaohongshu": [{"title": p['title'], "desc": p.get('description', ''), "comments": [c['content'] for c in p['comments'][:15]]} for p in xhs_final[:30]],
        "taobao": [{"title": p['title'], "price": p['price'], "reviews": p['reviews']} for p in taobao_final],
        "baidu": baidu_final,
        "news": news_final
    }

    final_prompt = f"""
You are a senior analyst specializing in the Chinese market. Using all the real data provided below (Baidu Index, Taobao reviews, Xiaohongshu trends, trade statistics, news, competitor analysis), write a comprehensive 'China Market Entry Strategy Report'. All output must be in Korean.

Data: {summary_data}

[Requirements]
1. xhs_trend_summary: Analyze Xiaohongshu posts and comments to summarize current consumer trends and needs in China.
2. xhs_keywords: Extract 5 core product-related keywords most frequently mentioned in Xiaohongshu data.
   - Exclude meaningless social comments like "info sharing", "price inquiry", "nice post".
   - Exclude keywords identical or too similar to '{user_in}' or '{KEYWORD}'.
   - Select only words containing product insights: features, advantages, consumer complaints.
   - Output format: ["Chinese keyword (Korean meaning)", ...] (list format)
3. export_trend_summary: Based on trade_stats data, analyze the export trend over the past 4 years in 3 sentences.
4. taobao_market_summary: Based on Taobao product data, analyze product categories, market conditions, and average price range.
5. review_reactions: Classify Taobao reviews into positive/neutral/negative, and summarize exactly 3 key reactions for each.
6. baidu_info: Summarize consumer interest levels based on Baidu search volume index and demographic data.
7. five_force_analysis: Analyze the 5 Forces (new entrants, buyers, suppliers, substitutes, rivalry) for this industry in detail.
8. competitor_analysis: Based on collected competitor data, describe the competitive landscape in the Chinese market.
9. summary: Connect all the above indicators organically and write a detailed 'China Market Entry Strategy' in at least 10-15 sentences.
   - Include professional insights analyzing correlations between data points, not just summaries.
   - Provide concrete action plans highlighting strengths a Korean company can leverage and weaknesses to address.

Reply strictly in the following JSON format, with all values in Korean:
{{
  "xhs_trend_summary": "content",
  "xhs_keywords": ["keyword1 (meaning)", "keyword2 (meaning)", "keyword3 (meaning)", "keyword4 (meaning)", "keyword5 (meaning)"],
  "export_trend_summary": "export trend analysis summary",
  "taobao_market_summary": "content",
  "review_reactions": {{ "positive": ["line1", "line2", "line3"], "neutral": ["line1", "line2", "line3"], "negative": ["line1", "line2", "line3"] }},
  "baidu_info": {{ "summary": "content", "index": {baidu_final.get('index')}, "period": "{baidu_final.get('period')}", "age_dist": {baidu_final.get('demographics', {}).get('age')}, "gender_dist": {baidu_final.get('demographics', {}).get('gender')} }},
  "competitor_analysis": "content",
  "five_force_analysis": {{ "new_entrants": "detailed analysis", "buyers": "detailed analysis", "suppliers": "detailed analysis", "substitutes": "detailed analysis", "rivalry": "detailed analysis" }},
  "summary": "detailed entry strategy (long form)"
}}
"""

    try:
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        res = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a professional market analyst. Output ONLY JSON."},
                {"role": "user", "content": final_prompt}
            ],
            response_format={"type": "json_object"}
        )
        report_json = json.loads(res.choices[0].message.content)
    except Exception as e:
        print(f"\n[OpenAI API 에러] 최종 리포트 합성 실패: {e}")
        raise e

    # 최종 리포트 구성
    final_report = {
        "keyword": user_in,
        "industry": industry_info['kr'],
        "hs_code": hs_final.get('hs_code'),
        "competitors": comp_final,
        "xhs_trend_summary": report_json.get("xhs_trend_summary"),
        "xhs_keywords": report_json.get("xhs_keywords", []),
        "export_trend_summary": report_json.get("export_trend_summary"),
        "taobao_market_summary": report_json.get("taobao_market_summary"),
        "review_reactions": report_json.get("review_reactions"),
        "baidu_info": report_json.get("baidu_info"),
        "competitor_analysis": report_json.get("competitor_analysis"),
        "five_force_analysis": report_json.get("five_force_analysis"),
        "summary": report_json.get("summary"),
        "trade_stats": trade_final.get('stats'),
        "news": news_final
    }

    # 마케팅 모듈 학습을 위해 파일로 저장 및 전역 변수 업데이트
    save_data_to_file("final_report.json", final_report)
    global GLOBAL_FINAL_REPORT
    GLOBAL_FINAL_REPORT = final_report

    print("\n[완료] 산업군 및 경쟁사 정보가 포함된 통합 리포트 생성이 완료되었습니다.")
    return final_report

def main():
    user_in = input("분석할 품목명(한국어)을 입력하세요: ").strip()
    result = asyncio.run(run_full_analysis(user_in))
    print("\n--- 분석 결과 (JSON) ---")
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
