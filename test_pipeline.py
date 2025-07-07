#!/usr/bin/env python3
"""
뉴스 파이프라인 테스트 스크립트
새로운 필드들(news_url, published_date, category, sentiment)이 올바르게 처리되는지 확인
"""

import asyncio
import sys
import os

# 프로젝트 루트 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.domain.service.news_pipeline_service import news_pipeline_service

async def test_news_pipeline():
    """
    뉴스 파이프라인 테스트
    """
    print("🧪 뉴스 파이프라인 테스트 시작")
    
    # 작은 규모로 테스트 (크래프톤만)
    test_companies = ["크래프톤"]
    
    try:
        result = await news_pipeline_service.process_news_pipeline(test_companies)
        
        print(f"\n📊 파이프라인 결과:")
        print(f"- Status: {result.get('status')}")
        print(f"- Message: {result.get('message')}")
        print(f"- 총 수집: {result.get('total_collected', 0)}개")
        print(f"- 키워드 필터 후: {result.get('after_keyword_filter', 0)}개")
        print(f"- 중복 제거 후: {result.get('after_deduplication', 0)}개")
        print(f"- AI 분류 후: {result.get('after_classification', 0)}개")
        print(f"- 최종 요약: {result.get('final_summaries', 0)}개")
        
        results = result.get('results', [])
        if results:
            print(f"\n📰 첫 번째 결과 샘플:")
            first_result = results[0]
            print(f"- ID: {first_result.get('id', 'N/A')}")
            print(f"- 기업: {first_result.get('corp', 'N/A')}")
            print(f"- 제목: {first_result.get('original_title', 'N/A')[:50]}...")
            print(f"- 요약: {first_result.get('summary', 'N/A')[:100]}...")
            print(f"- 뉴스 URL: {first_result.get('news_url', 'N/A')}")
            print(f"- 발행일: {first_result.get('published_date', 'N/A')}")
            print(f"- 카테고리: {first_result.get('category', 'N/A')}")
            print(f"- 감정: {first_result.get('sentiment', 'N/A')}")
            print(f"- 신뢰도: {first_result.get('confidence', 'N/A')}")
            print(f"- 매칭 키워드: {first_result.get('matched_keywords', [])}")
        
        print(f"\n✅ 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_news_pipeline()) 