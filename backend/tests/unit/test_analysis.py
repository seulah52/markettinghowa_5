import pytest
import asyncio
import sys
import os

# 프로젝트 루트(backend) 폴더를 경로에 추가 (app 모듈 인식용)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# OpenAI 기반의 실제 분석 로직이 포함된 파일에서 함수들을 가져옴
# (이 파일은 수집 개수 5개 및 OpenAI API를 사용하도록 기설정됨)
from app.api.v1.endpoints.test_analysis import run_full_analysis

@pytest.mark.asyncio
async def test_run_full_analysis_real_openai():
    """
    OpenAI API와 실제 크롤러(5개 수집)를 사용하여 
    전체 분석 프로세스가 실제 데이터로 정상 작동하는지 테스트합니다.
    """
    # 1. 실제 테스트할 키워드 설정
    test_keyword = "마스크팩"
    
    print(f"\n[Test] '{test_keyword}'로 실제 분석 프로세스를 시작합니다 (OpenAI/5개 수집 모드)...")
    
    # 2. 실제 로직 실행 (Mock 없음, 실제 사이트 접속 및 OpenAI 호출)
    # 수동 엔터 입력이 필요한 상황(쿠키 만료 등)에서는 테스트가 잠시 대기할 수 있습니다.
    try:
        result = await run_full_analysis(test_keyword)
        
        # 3. 결과 구조 검증 (실제 데이터 기반)
        assert result is not None, "분석 결과가 None입니다."
        assert isinstance(result, dict), "결과값이 딕셔너리 형식이 아닙니다."
        
        # 필드 존재 확인
        assert "keyword" in result
        assert "sentiment" in result
        assert "topKeywords" in result
        assert "ageGroups" in result
        assert "competitors" in result
        assert "summary" in result
        
        # 실제 데이터 내용 검증
        assert result["keyword"] == test_keyword
        assert len(result["topKeywords"]) == 5, "topKeywords는 5개여야 합니다."
        assert len(result["ageGroups"]) > 0, "연령대 데이터가 수집되지 않았습니다."
        assert len(result["competitors"]) > 0, "경쟁사 데이터가 분석되지 않았습니다."
        assert len(result["summary"]) > 20, "요약 리포트 내용이 너무 짧습니다."
        
        # 감성 분석 수치 확인 (0~100 사이)
        sent = result["sentiment"]
        assert 0 <= sent["positive"] <= 100
        assert 0 <= sent["neutral"] <= 100
        assert 0 <= sent["negative"] <= 100
        
        print("\n[성공] 실제 데이터를 활용한 OpenAI 기반 통합 분석 테스트를 통과했습니다.")

    except Exception as e:
        pytest.fail(f"실제 분석 테스트 중 오류 발생: {e}")

if __name__ == "__main__":
    # 파일 직접 실행 시에도 테스트 가능하도록 설정
    asyncio.run(test_run_full_analysis_real_openai())
