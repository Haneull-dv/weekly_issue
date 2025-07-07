#!/bin/bash

# Issue 서비스 도커 실행 스크립트

echo "🚀 Issue 서비스 도커 컨테이너 시작..."

# 환경 변수 확인
if [ ! -f ".env" ]; then
    echo "⚠️  .env 파일이 없습니다. .env.example을 참고해서 생성해주세요:"
    echo "NAVER_CLIENT_ID=your_naver_client_id_here"
    echo "NAVER_CLIENT_SECRET=your_naver_client_secret_here"
    echo "CLASSIFIER_SERVICE_URL=http://newsclassifier:8087/predict"
    echo "SUMMARY_SERVICE_URL=http://summarizer:8088/summary"
    echo "SERVICE_PORT=8089"
    echo "LOG_LEVEL=INFO"
    exit 1
fi

# 도커 이미지 빌드
echo "🔨 도커 이미지 빌드 중..."
docker build -t issue-service .

if [ $? -eq 0 ]; then
    echo "✅ 이미지 빌드 완료!"
else
    echo "❌ 이미지 빌드 실패!"
    exit 1
fi

# 기존 컨테이너 정리
echo "🧹 기존 컨테이너 정리 중..."
docker stop issue-service 2>/dev/null || true
docker rm issue-service 2>/dev/null || true

# 컨테이너 실행
echo "🚀 컨테이너 실행 중..."
docker run -d \
    --name issue-service \
    --network portfolio_app-network \
    -p 8089:8089 \
    -v $(pwd):/app \
    -v /app/__pycache__ \
    --env-file .env \
    issue-service

if [ $? -eq 0 ]; then
    echo "✅ Issue 서비스가 성공적으로 시작되었습니다!"
    echo "📋 서비스 정보:"
    echo "   - 컨테이너 이름: issue-service"
    echo "   - 포트: 8089"
    echo "   - API 문서: http://localhost:8089/docs"
    echo "   - 뉴스 파이프라인: POST http://localhost:8089/issue/news"
    echo ""
    echo "📊 컨테이너 상태:"
    docker ps --filter name=issue-service --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    echo "📝 실시간 로그 확인:"
    echo "   docker logs -f issue-service"
else
    echo "❌ 컨테이너 실행 실패!"
    exit 1
fi 