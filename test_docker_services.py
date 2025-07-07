#!/usr/bin/env python3
"""
Docker 서비스 연결 테스트 스크립트
실제 포트와 서비스 상태를 확인
"""

import asyncio
import httpx
import socket
import sys
import os

async def test_port_connectivity():
    """
    포트 연결 테스트
    """
    print("🔍 포트 연결 테스트")
    
    test_hosts = [
        ("localhost", 8087, "newsclassifier"),
        ("localhost", 8088, "summarizer"),
        ("127.0.0.1", 8087, "newsclassifier"),
        ("127.0.0.1", 8088, "summarizer"),
    ]
    
    for host, port, service in test_hosts:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                print(f"✅ {service}: {host}:{port} - 포트 열림")
            else:
                print(f"❌ {service}: {host}:{port} - 포트 닫힘")
                
        except Exception as e:
            print(f"❌ {service}: {host}:{port} - 테스트 실패: {str(e)}")

async def test_service_endpoints():
    """
    서비스 엔드포인트 테스트
    """
    print("\n🔍 서비스 엔드포인트 테스트")
    
    test_endpoints = [
        # Classifier 테스트
        {
            "name": "newsclassifier",
            "urls": [
                "http://localhost:8087/",
                "http://localhost:8087/health", 
                "http://localhost:8087/docs",
                "http://localhost:8087/predict"
            ]
        },
        # Summarizer 테스트
        {
            "name": "summarizer", 
            "urls": [
                "http://localhost:8088/",
                "http://localhost:8088/health",
                "http://localhost:8088/docs", 
                "http://localhost:8088/summarize"
            ]
        }
    ]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for service in test_endpoints:
            print(f"\n📊 {service['name']} 서비스 테스트:")
            
            for url in service['urls']:
                try:
                    print(f"  🔍 테스트: {url}")
                    
                    if url.endswith('/predict') or url.endswith('/summarize'):
                        # API 엔드포인트는 POST 요청
                        if 'predict' in url:
                            payload = {"text": ["테스트 제목"]}
                        else:
                            payload = {
                                "news": {
                                    "title": "테스트 제목",
                                    "description": "테스트 내용"
                                }
                            }
                        
                        response = await client.post(url, json=payload)
                    else:
                        # 기타 엔드포인트는 GET 요청
                        response = await client.get(url)
                    
                    print(f"    ✅ 응답: {response.status_code}")
                    
                    if response.status_code == 200:
                        content = response.text[:100].replace('\n', ' ')
                        print(f"    📄 내용: {content}...")
                    elif response.status_code == 422:
                        print(f"    ⚠️ 요청 형식 오류 (서비스는 정상)")
                        
                except httpx.ConnectError as e:
                    print(f"    ❌ 연결 실패: {str(e)}")
                except httpx.TimeoutException as e:
                    print(f"    ❌ 타임아웃: {str(e)}")
                except Exception as e:
                    print(f"    ❌ 오류: {str(e)}")

async def test_actual_ai_requests():
    """
    실제 AI 서비스 요청 테스트
    """
    print("\n🤖 실제 AI 서비스 요청 테스트")
    
    # Classifier 테스트
    print("\n📊 Classifier 테스트:")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "text": [
                    "크래프톤, 배틀그라운드 신규 업데이트 발표",
                    "넥슨, AI 기술과 게임 결합 방안 공개"
                ]
            }
            
            response = await client.post(
                "http://localhost:8087/predict",
                json=payload
            )
            
            print(f"  📥 응답 상태: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"  📄 분류 결과: {result}")
            else:
                print(f"  ❌ 오류: {response.text}")
                
    except Exception as e:
        print(f"  ❌ Classifier 테스트 실패: {str(e)}")
    
    # Summarizer 테스트  
    print("\n📝 Summarizer 테스트:")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "news": {
                    "title": "크래프톤, 배틀그라운드 신규 맵 추가 업데이트 발표",
                    "description": "크래프톤이 인기 게임 배틀그라운드에 새로운 맵을 추가하는 대규모 업데이트를 발표했습니다. 이번 업데이트에는 새로운 게임 모드와 함께 다양한 기능 개선사항이 포함되어 있습니다."
                }
            }
            
            response = await client.post(
                "http://localhost:8088/summarize", 
                json=payload
            )
            
            print(f"  📥 응답 상태: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"  📄 요약 결과: {result}")
                
                summary = result.get("summary", "")
                if summary:
                    print(f"  📏 요약 길이: {len(summary)}자")
                    if len(summary) <= 100:
                        print(f"  ✅ 길이 요구사항 충족")
                    else:
                        print(f"  ⚠️ 너무 길음 ({len(summary)}자)")
            else:
                print(f"  ❌ 오류: {response.text}")
                
    except Exception as e:
        print(f"  ❌ Summarizer 테스트 실패: {str(e)}")

async def main():
    """메인 테스트"""
    print("=" * 60)
    print("🐳 DOCKER 서비스 연결 테스트")
    print("=" * 60)
    
    await test_port_connectivity()
    await test_service_endpoints()
    await test_actual_ai_requests()
    
    print("\n" + "=" * 60)
    print("🎉 Docker 서비스 테스트 완료!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main()) 