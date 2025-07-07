#!/usr/bin/env python3
"""
네이버 뉴스 API 직접 테스트 스크립트
"""
import os
import requests
from dotenv import load_dotenv

def test_naver_api():
    print("🧪 네이버 뉴스 API 직접 테스트 시작")
    print("=" * 50)
    
    # 환경 변수 로드
    load_dotenv()
    
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")
    
    print(f"🔍 환경 변수 확인:")
    print(f"   - NAVER_CLIENT_ID: {client_id[:4] if client_id else 'None'}***")
    print(f"   - NAVER_CLIENT_SECRET: {client_secret[:4] if client_secret else 'None'}***")
    print(f"   - 실제 길이 - ID: {len(client_id) if client_id else 0}, Secret: {len(client_secret) if client_secret else 0}")
    
    if not client_id or not client_secret:
        print("❌ 환경 변수가 설정되지 않았습니다!")
        return
    
    # API 호출 준비
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }
    params = {
        "query": "테스트",
        "display": 1,
        "start": 1,
        "sort": "date"
    }
    
    print(f"\n📡 API 호출 정보:")
    print(f"   - URL: {url}")
    print(f"   - Query: {params['query']}")
    print(f"   - 헤더에 사용될 값들:")
    print(f"     X-Naver-Client-Id: {client_id[:4]}***")
    print(f"     X-Naver-Client-Secret: {client_secret[:4]}***")
    
    try:
        print(f"\n🚀 API 호출 실행...")
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        print(f"📋 응답 결과:")
        print(f"   - Status Code: {response.status_code}")
        print(f"   - Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ API 호출 성공!")
            data = response.json()
            print(f"   - 검색 결과 개수: {len(data.get('items', []))}")
            if data.get('items'):
                first_item = data['items'][0]
                print(f"   - 첫 번째 뉴스 제목: {first_item.get('title', 'N/A')}")
        
        elif response.status_code == 401:
            print("❌ 401 Unauthorized - 인증 실패!")
            print(f"   - 응답 내용: {response.text}")
            
            # 추가 디버깅 정보
            print(f"\n🔍 추가 디버깅 정보:")
            print(f"   - Client ID 길이: {len(client_id)}")
            print(f"   - Client Secret 길이: {len(client_secret)}")
            print(f"   - Client ID 타입: {type(client_id)}")
            print(f"   - Client Secret 타입: {type(client_secret)}")
            print(f"   - Client ID에 공백 포함: {' ' in client_id}")
            print(f"   - Client Secret에 공백 포함: {' ' in client_secret}")
            
        else:
            print(f"❌ API 호출 실패: {response.status_code}")
            print(f"   - 응답 내용: {response.text}")
            
    except Exception as e:
        print(f"❌ 예외 발생: {str(e)}")

if __name__ == "__main__":
    test_naver_api() 