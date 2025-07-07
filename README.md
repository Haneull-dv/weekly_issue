# ML 모델 API 서버

FastAPI를 이용한 머신러닝 모델 서빙 API 서버입니다.

## 프로젝트 구조

```
📁 app/
├── 📁 controller/         ← API 라우터 정의
│   └── predict_controller.py
├── 📁 service/            ← 비즈니스 로직
│   └── predict_service.py
├── main.py               ← FastAPI 앱 실행
├── model.pkl             ← 저장된 ML 모델
📄 Dockerfile              ← 도커 이미지 정의
📄 requirements.txt        ← 의존 패키지 리스트
📄 .dockerignore           ← 도커 빌드시 제외할 파일 목록
```

## 🚀 설치 및 실행

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정
`issue/.env` 파일을 생성하고 다음 내용을 설정하세요:

```env
# 네이버 뉴스 API 설정
NAVER_CLIENT_ID=your_naver_client_id_here
NAVER_CLIENT_SECRET=your_naver_client_secret_here

# AI 모델 서비스 URL 설정 (도커 컨테이너 간 통신)
CLASSIFIER_SERVICE_URL=http://newsclassifier:8087/predict
SUMMARY_SERVICE_URL=http://summarizer:8088/summary

# 서비스 설정
SERVICE_PORT=8089
LOG_LEVEL=INFO

# Docker 환경 변수
PYTHONPATH=/app
PYTHONDONTWRITEBYTECODE=1
PYTHONUNBUFFERED=1
```

### 3. 서비스 실행

#### Docker Compose 사용 (권장)
```bash
# 전체 스택 실행
make up

# Issue 서비스만 실행
make up-issue

# 빌드 후 실행
make build-issue && make up-issue

# 로그 확인
make logs-issue

# 재시작
make restart-issue
```

#### 개별 실행
```bash
# Windows
docker-run.bat

# Linux/Mac
./docker-run.sh

# 또는 직접 실행
cd app
python -m uvicorn main:app --host 0.0.0.0 --port 8089 --reload
```

## 📊 API 엔드포인트

### 뉴스 파이프라인 처리
```http
POST /issue/news
Content-Type: application/json

{
    "companies": ["크래프톤", "엔씨소프트", "넷마블"]
}
```

**또는 기본 기업 리스트 사용:**
```http
POST /issue/news
```

### 응답 예시
```json
{
    "status": "success",
    "message": "뉴스 파이프라인 처리 완료",
    "total_collected": 500,
    "after_keyword_filter": 150,
    "after_classification": 45,
    "final_summaries": 12,
    "companies_processed": ["크래프톤", "엔씨소프트", "넷마블"],
    "results": [
        {
            "corp": "크래프톤",
            "summary": "배틀그라운드 신규 맵 출시로 월간 활성사용자 증가 예상",
            "original_title": "크래프톤, 배틀그라운드 신규 맵 '탄고' 출시",
            "confidence": 0.8945,
            "matched_keywords": ["출시", "신규"]
        }
    ]
}
```

## 🔧 서비스 아키텍처

### MSA 구조
- **Router**: API 엔드포인트 관리
- **Controller**: 요청 처리 및 서비스 호출
- **Services**: 
  - `NaverNewsService`: 네이버 뉴스 API 호출
  - `KeywordFilterService`: 1차 키워드 필터링
  - `ClassifierService`: 2차 AI 분류 모델 호출
  - `SummaryService`: 요약 모델 호출
  - `NewsPipelineService`: 전체 파이프라인 오케스트레이션

### 처리 플로우
1. **뉴스 수집**: 네이버 뉴스 API로 기업별 최대 100개 뉴스 수집
2. **1차 필터링**: 키워드 기반 중요도 필터링
3. **2차 분류**: AI 모델로 중요도 분류 (라벨 1만 통과)
4. **요약 생성**: 통과한 뉴스의 제목+본문을 요약

## 🎯 필수 사전 조건

1. **네이버 뉴스 API 키** 발급 및 설정
2. **분류 모델 서비스** 실행 (포트 8087)
3. **요약 모델 서비스** 실행 (포트 8088)

## 📝 기본 기업 리스트
- 크래프톤, 엔씨소프트, 넷마블, 펄어비스, 카카오게임즈, 위메이드, 네오위즈, NHN, 컴투스

## API 사용법

### 예측 API

- **엔드포인트**: `/api/predict`
- **메서드**: POST
- **입력 형식**:
```json
{
  "features": [0.1, 0.2, 0.3, 0.4]
}
```
- **출력 형식**:
```json
{
  "prediction": "class_label",
  "probability": {
    "class_1": 0.1,
    "class_2": 0.9
  }
}
```

## 주의사항

- 실제 모델 파일(model.pkl)은 직접 추가해야 합니다. 