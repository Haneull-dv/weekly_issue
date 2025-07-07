#!/usr/bin/env python3
"""
환경 변수 디버깅 스크립트
"""
import os
from dotenv import load_dotenv

load_dotenv()

client_id = os.getenv('NAVER_CLIENT_ID')
client_secret = os.getenv('NAVER_CLIENT_SECRET')

print("🔍 환경 변수 상세 분석:")
print(f"Client ID:")
print(f"  - 값: [{client_id}]")
print(f"  - 길이: {len(client_id) if client_id else 0}")
print(f"  - 앞/뒤 공백: '{client_id.strip()}' == '{client_id}': {client_id.strip() == client_id if client_id else False}")
print()
print(f"Client Secret:")
print(f"  - 값: [{client_secret}]")
print(f"  - 길이: {len(client_secret) if client_secret else 0}")
print(f"  - 앞/뒤 공백: '{client_secret.strip()}' == '{client_secret}': {client_secret.strip() == client_secret if client_secret else False}")
print(f"  - 뒤에 공백 있음: {client_secret.endswith(' ') if client_secret else False}")
print(f"  - 16진수 표현: {client_secret.encode('unicode_escape') if client_secret else None}")

# 공백 제거 후 다시 테스트
if client_id and client_secret:
    import requests
    
    clean_id = client_id.strip()
    clean_secret = client_secret.strip()
    
    print(f"\n🧹 공백 제거 후 테스트:")
    print(f"  - 정리된 ID: [{clean_id}]")
    print(f"  - 정리된 Secret: [{clean_secret}]")
    
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": clean_id,
        "X-Naver-Client-Secret": clean_secret
    }
    params = {
        "query": "테스트",
        "display": 1,
        "start": 1,
        "sort": "date"
    }
    
    try:
        print("\n🚀 공백 제거 후 API 호출...")
        response = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 공백 제거 후 성공!")
        else:
            print(f"❌ 여전히 실패: {response.text}")
            
    except Exception as e:
        print(f"❌ 오류: {e}") 