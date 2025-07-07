import os
import requests
import json
from typing import List, Dict
from pathlib import Path
from dotenv import load_dotenv

# __file__ 기준으로 .env 파일 절대경로 설정 (weekly_issue/.env)
current_file = Path(__file__).resolve()
# Docker 환경: /app/weekly_issue/app/domain/service/naver_news_service.py
# 로컬 환경: /path/to/portfolio/weekly_issue/app/domain/service/naver_news_service.py
project_root = current_file.parents[3]  # weekly_issue 루트 디렉토리
env_path = project_root / ".env"

print(f"🔍 [DEBUG] 환경변수 파일 경로:")
print(f"   - Current file: {current_file}")
print(f"   - Project root: {project_root}")
print(f"   - .env path: {env_path}")
print(f"   - .env exists: {env_path.exists()}")

# 명시적 경로로 .env 로딩
load_dotenv(dotenv_path=env_path)

class NaverNewsService:
    def __init__(self):
        try:
            # os.environ으로 환경변수 직접 접근 (KeyError 시 즉시 실패)
            self.client_id = os.environ["NAVER_CLIENT_ID"]
            self.client_secret = os.environ["NAVER_CLIENT_SECRET"]
            self.base_url = "https://openapi.naver.com/v1/search/news.json"
            
            # 디버깅: 환경 변수 로딩 상태 확인
            print(f"✅ [DEBUG] 환경 변수 로딩 성공:")
            print(f"   - NAVER_CLIENT_ID: {self.client_id[:4]}***")
            print(f"   - NAVER_CLIENT_SECRET: {self.client_secret[:4]}***")
            print(f"   - Base URL: {self.base_url}")
            
        except KeyError as e:
            error_msg = f"필수 환경변수가 설정되지 않았습니다: {e}"
            print(f"❌ {error_msg}")
            print(f"   - .env 파일 경로: {env_path}")
            print(f"   - .env 파일 존재 여부: {env_path.exists()}")
            if env_path.exists():
                print(f"   - .env 파일 내용 확인 필요 (NAVER_CLIENT_ID, NAVER_CLIENT_SECRET)")
            raise ValueError(error_msg)
    
    async def fetch_news_for_company(self, company: str, display: int = 100) -> List[Dict]:
        """
        특정 기업의 뉴스를 네이버 API로 가져오기
        """
        print(f"🤍3-1 네이버 뉴스 서비스 진입 - 기업: {company}")
        
        # __init__에서 이미 환경변수 검증이 완료되었으므로 추가 체크 불필요
        
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        params = {
            "query": company,
            "display": display,
            "start": 1,
            "sort": "date"
        }
        
        # 디버깅: API 호출 정보 로그
        print(f"🔍 [DEBUG] API 호출 정보:")
        print(f"   - URL: {self.base_url}")
        print(f"   - Headers: X-Naver-Client-Id={self.client_id[:4]}***, X-Naver-Client-Secret={self.client_secret[:4]}***")
        print(f"   - Params: {params}")
        
        try:
            print(f"📡 API 호출 시작...")
            response = requests.get(self.base_url, headers=headers, params=params, timeout=10)
            
            # 디버깅: 응답 상태 상세 로그
            print(f"🔍 [DEBUG] API 응답:")
            print(f"   - Status Code: {response.status_code}")
            print(f"   - Response Headers: {dict(response.headers)}")
            print(f"   - Response Text (first 200 chars): {response.text[:200]}...")
            
            if response.status_code == 401:
                print(f"❌ 401 Unauthorized 에러 발생!")
                print(f"   - 사용된 Client ID: {self.client_id[:4]}***")
                print(f"   - 사용된 Client Secret: {self.client_secret[:4]}***")
                print(f"   - 응답 내용: {response.text}")
                raise Exception(f"네이버 API 인증 실패 (401): API 키가 유효하지 않거나 권한이 없습니다.")
            
            response.raise_for_status()
            
            data = response.json()
            news_items = data.get("items", [])
            
            # 필요한 필드만 추출
            processed_news = []
            for item in news_items:
                processed_news.append({
                    "company": company,
                    "title": self._clean_html_tags(item.get("title", "")),
                    "description": self._clean_html_tags(item.get("description", "")),
                    "link": item.get("link", ""),
                    "pubDate": item.get("pubDate", "")
                })
            
            print(f"✅ {company}: {len(processed_news)}개 뉴스 수집 완료")
            return processed_news
            
        except requests.exceptions.RequestException as e:
            print(f"❌ {company} 뉴스 수집 실패: {str(e)}")
            return []
        except Exception as e:
            print(f"❌ {company} 뉴스 처리 중 오류: {str(e)}")
            return []
    
    def _clean_html_tags(self, text: str) -> str:
        """
        HTML 태그 제거
        """
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)

# 싱글톤 인스턴스
naver_news_service = NaverNewsService() 