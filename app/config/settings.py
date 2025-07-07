"""
Issue 서비스 설정
"""
import os

# 뉴스 수집 설정
DEFAULT_NEWS_COUNT = 100  # 기업당 수집할 뉴스 개수
NEWS_SEARCH_DAYS = 7  # 뉴스 검색 기간 (일)

# AI 분석 설정
CONFIDENCE_THRESHOLD = 0.7  # AI 분류 신뢰도 임계값
MIN_SUMMARY_LENGTH = 50  # 최소 요약 길이

# 환경 감지 (Docker vs Local)
IS_DOCKER = os.environ.get('RUNNING_IN_DOCKER', 'false').lower() == 'true'

# API 연동 설정 (환경별 분기)
if IS_DOCKER:
    # Docker 환경 (컨테이너 간 통신)
    CLASSIFIER_URL = "http://newsclassifier:8087/predict"
    SUMMARIZER_URL = "http://summarizer:8088/summarize"
else:
    # 로컬 개발 환경 (localhost 사용)
    CLASSIFIER_URL = "http://localhost:8087/predict"
    SUMMARIZER_URL = "http://localhost:8088/summarize"

print(f"🔧 환경 설정 - Docker: {IS_DOCKER}")
print(f"🔧 Classifier URL: {CLASSIFIER_URL}")
print(f"🔧 Summarizer URL: {SUMMARIZER_URL}")

# 요청 설정
REQUEST_TIMEOUT = 15  # 초
MAX_RETRY_COUNT = 3  # 최대 재시도 횟수 