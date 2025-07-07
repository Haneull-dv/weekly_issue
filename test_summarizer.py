#!/usr/bin/env python3
"""
Summarizer 서비스 전용 테스트 스크립트
AI 요약 서비스가 정상 동작하는지 확인
"""

import asyncio
import httpx
import sys
import os

# 프로젝트 루트 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config.settings import SUMMARIZER_URL

async def test_summarizer_direct():
    """
    Summarizer 서비스 직접 테스트
    """
    print("🧪 Summarizer 서비스 직접 테스트 시작")
    print(f"🔧 Target URL: {SUMMARIZER_URL}")
    
    # 테스트용 샘플 데이터
    test_payload = {
        "news": {
            "title": "크래프톤, 배틀그라운드 신규 맵 추가 업데이트 발표",
            "news_content": "크래프톤이 인기 게임 배틀그라운드에 새로운 맵을 추가하는 대규모 업데이트를 발표했습니다. 이번 업데이트에는 새로운 게임 모드와 함께 다양한 기능 개선사항이 포함되어 있습니다."
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("📤 API 요청 전송 중...")
            print(f"📤 Payload: {test_payload}")
            
            response = await client.post(
                SUMMARIZER_URL,
                json=test_payload,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"📥 응답 상태: {response.status_code}")
            print(f"📥 응답 헤더: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 요약 성공!")
                print(f"📄 응답 전체: {result}")
                
                summary = result.get("summary", "")
                if summary:
                    print(f"📝 생성된 요약: {summary}")
                    print(f"📏 요약 길이: {len(summary)}자")
                    
                    # 설계 요구사항 검증
                    if len(summary) <= 100:
                        print("✅ 요약 길이 요구사항 충족 (100자 이내)")
                    else:
                        print(f"⚠️ 요약이 너무 길음 ({len(summary)}자 > 100자)")
                    
                    if "크래프톤" in summary:
                        print("✅ 기업명 포함 확인")
                    else:
                        print("⚠️ 기업명이 요약에 포함되지 않음")
                else:
                    print("❌ 요약이 비어있음")
                    
            elif response.status_code == 404:
                print("❌ 엔드포인트를 찾을 수 없음 (404)")
                print("💡 Summarizer 서비스가 실행되지 않았거나 URL이 잘못되었을 수 있습니다.")
                
            elif response.status_code == 422:
                print("❌ 요청 형식 오류 (422)")
                print(f"❌ 오류 내용: {response.text}")
                print("💡 Payload 형식을 확인해주세요.")
                
            else:
                print(f"❌ 예상치 못한 응답: {response.status_code}")
                print(f"❌ 응답 내용: {response.text}")
                
    except httpx.ConnectError as e:
        print(f"❌ 연결 실패: {str(e)}")
        print("💡 Summarizer 서비스가 실행되고 있는지 확인해주세요.")
        
    except httpx.TimeoutException as e:
        print(f"❌ 타임아웃: {str(e)}")
        print("💡 Summarizer 서비스 응답이 너무 오래 걸립니다.")
        
    except Exception as e:
        print(f"❌ 기타 오류: {str(e)}")

async def test_health_endpoints():
    """
    다양한 헬스체크 엔드포인트 테스트
    """
    print("\n🔍 헬스체크 엔드포인트 테스트")
    
    health_urls = [
        SUMMARIZER_URL.replace('/summarize', '/health'),
        SUMMARIZER_URL.replace('/summarize', '/'),
        SUMMARIZER_URL.replace('/summarize', '/docs'),
        f"http://summarizer:8088/health",  # Docker 내부 네트워크
        f"http://localhost:8088/health",   # 로컬 테스트
    ]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for url in health_urls:
            try:
                print(f"🔍 테스트 중: {url}")
                response = await client.get(url)
                print(f"   ✅ 응답: {response.status_code}")
                if response.status_code == 200:
                    print(f"   📄 내용: {response.text[:100]}...")
                    
            except Exception as e:
                print(f"   ❌ 실패: {str(e)}")

async def test_integration():
    """
    전체 파이프라인에서 Summarizer 동작 테스트
    """
    print("\n🔗 파이프라인 통합 테스트")
    
    from app.domain.service.summary_service import summary_service
    
    # 분류 완료된 가짜 뉴스 데이터
    test_news = [{
        "company": "크래프톤",
        "title": "크래프톤, 배틀그라운드 신규 맵 추가 업데이트 발표", 
        "description": "크래프톤이 인기 게임 배틀그라운드에 새로운 맵을 추가하는 대규모 업데이트를 발표했습니다.",
        "link": "https://example.com/news/1",
        "pubDate": "Mon, 25 Dec 2023 14:30:00 +0900",
        "classification": {
            "label": "important",
            "confidence": 0.9
        },
        "matched_keywords": ["게임", "업데이트"]
    }]
    
    try:
        results = await summary_service.summarize_news(test_news)
        
        if results:
            result = results[0]
            print(f"📊 통합 테스트 결과:")
            print(f"   - 요약: {result.get('summary', 'N/A')}")
            print(f"   - 요약 유형: {result.get('summary_type', 'N/A')}")
            print(f"   - 뉴스 URL: {result.get('news_url', 'N/A')}")
            print(f"   - 발행일: {result.get('published_date', 'N/A')}")
            
            summary_type = result.get('summary_type', '')
            if summary_type == 'ai_generated':
                print("✅ AI 요약 성공!")
            else:
                print(f"⚠️ Fallback 사용됨: {summary_type}")
        else:
            print("❌ 결과 없음")
            
    except Exception as e:
        print(f"❌ 통합 테스트 실패: {str(e)}")

async def main():
    """메인 테스트 실행"""
    print("=" * 60)
    print("🧪 SUMMARIZER 서비스 종합 테스트")
    print("=" * 60)
    
    await test_summarizer_direct()
    await test_health_endpoints() 
    await test_integration()
    
    print("\n" + "=" * 60)
    print("🎉 테스트 완료!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main()) 