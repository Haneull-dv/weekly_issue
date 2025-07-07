import httpx
import uuid
from typing import List, Dict
from app.config.settings import SUMMARIZER_URL, REQUEST_TIMEOUT

class SummaryService:
    def __init__(self):
        self.summary_url = SUMMARIZER_URL
        self.timeout = REQUEST_TIMEOUT
        print(f"🔧 SummaryService 초기화 - URL: {self.summary_url}")
    
    async def summarize_news(self, news_list: List[Dict]) -> List[Dict]:
        """
        요약 모델로 뉴스 요약 생성
        """
        print(f"🤍3-4 요약 서비스 진입 - 총 {len(news_list)}개 뉴스")
        print(f"🔧 Summarizer URL: {self.summary_url}")
        
        summarized_results = []
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for i, news in enumerate(news_list):
                try:
                    print(f"📝 [{i+1}/{len(news_list)}] {news.get('company')} 뉴스 요약 시작")
                    
                    # 설계에 맞는 올바른 payload 형식 사용
                    payload = {
                        "news": {
                            "title": news.get("title", ""),
                            "description": news.get("description", "")  # API가 실제로 요구하는 필드명
                        }
                    }
                    
                    print(f"📤 API 요청 - Title: {payload['news']['title'][:50]}...")
                    print(f"📤 API 요청 - Description: {payload['news']['description'][:50]}...")
                    
                    response = await client.post(
                        self.summary_url,
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    print(f"📥 API 응답 - Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        summary_result = response.json()
                        print(f"📥 API 응답 내용: {summary_result}")
                        
                        summary_text = summary_result.get("summary", "")
                        
                        # 빈 요약일 경우 기본 요약 생성
                        if not summary_text or summary_text.strip() == "":
                            print("⚠️ 빈 요약 반환됨. Fallback 사용.")
                            summary_text = self._generate_fallback_summary(news)
                            summary_type = "fallback_empty_response"
                        else:
                            print(f"✅ AI 요약 성공: {summary_text[:50]}...")
                            summary_type = "ai_generated"
                        
                        result = {
                            "id": str(uuid.uuid4()),
                            "corp": news.get("company"),
                            "summary": summary_text,
                            "original_title": news.get("title"),
                            "confidence": news.get("classification", {}).get("confidence", 0),
                            "matched_keywords": news.get("matched_keywords", []),
                            "news_url": news.get("link", ""),
                            "published_date": self._format_published_date(news.get("pubDate", "")),
                            "category": news.get("category", "일반"),
                            "sentiment": "neutral",
                            "summary_type": summary_type  # 디버깅용
                        }
                        summarized_results.append(result)
                        
                        print(f"✅ {news.get('company')} 뉴스 요약 완료 ({summary_type})")
                    
                    else:
                        print(f"❌ 요약 API 호출 실패: {response.status_code}")
                        print(f"❌ 응답 내용: {response.text}")
                        result = self._create_fallback_result(news)
                        result["summary_type"] = f"fallback_api_error_{response.status_code}"
                        summarized_results.append(result)
                        
                except httpx.RequestError as e:
                    print(f"❌ {news.get('company')} 요약 중 네트워크 오류: {str(e)}")
                    result = self._create_fallback_result(news)
                    result["summary_type"] = "fallback_network_error"
                    summarized_results.append(result)
                except Exception as e:
                    print(f"❌ {news.get('company')} 요약 중 오류: {str(e)}")
                    result = self._create_fallback_result(news)
                    result["summary_type"] = "fallback_unknown_error"
                    summarized_results.append(result)
        
        # 요약 유형별 통계 출력
        summary_stats = {}
        for result in summarized_results:
            summary_type = result.get("summary_type", "unknown")
            summary_stats[summary_type] = summary_stats.get(summary_type, 0) + 1
        
        print(f"✅ 요약 처리 완료: 총 {len(summarized_results)}개")
        print(f"📊 요약 유형별 통계: {summary_stats}")
        
        return summarized_results
    
    def _create_fallback_result(self, news: Dict) -> Dict:
        """
        Fallback 결과 생성 (일관된 구조 보장)
        """
        return {
            "id": str(uuid.uuid4()),
            "corp": news.get("company"),
            "summary": self._generate_fallback_summary(news),
            "original_title": news.get("title"),
            "confidence": news.get("classification", {}).get("confidence", 0),
            "matched_keywords": news.get("matched_keywords", []),
            "news_url": news.get("link", ""),
            "published_date": self._format_published_date(news.get("pubDate", "")),
            "category": news.get("category", "일반"),
            "sentiment": "neutral"
        }
    
    def _generate_fallback_summary(self, news: Dict) -> str:
        """
        AI 요약 실패 시 제목과 설명을 기반으로 간단한 요약 생성
        설계에 맞게 100자 이내로 제한
        """
        title = news.get("title", "")
        description = news.get("description", "")
        company = news.get("company", "")
        
        if title and description:
            # 제목과 설명을 결합하여 100자 이내 요약 생성
            base_summary = f"{company} 관련 뉴스: {title[:30]}"
            if len(base_summary) < 80 and description:
                remaining_chars = 100 - len(base_summary) - 5  # 여유분 5자
                if remaining_chars > 10:
                    base_summary += f" - {description[:remaining_chars]}..."
            return base_summary[:100]  # 최대 100자로 제한
        elif title:
            return f"{company} 관련 뉴스: {title[:70]}"  # 100자 이내로 제한
        else:
            return f"{company} 관련 뉴스가 발표되었습니다."
    
    def _format_published_date(self, pub_date: str) -> str:
        """
        네이버 API의 pubDate 형식을 YYYYMMDD 형식으로 변환
        예: "Mon, 18 Dec 2023 14:30:00 +0900" -> "20231218"
        """
        if not pub_date:
            return ""
        
        try:
            from datetime import datetime
            # 네이버 API의 pubDate 형식 파싱
            # 예: "Mon, 18 Dec 2023 14:30:00 +0900"
            dt = datetime.strptime(pub_date.split('+')[0].strip(), "%a, %d %b %Y %H:%M:%S")
            return dt.strftime("%Y%m%d")
        except Exception as e:
            print(f"⚠️ 날짜 파싱 실패: {pub_date}, 오류: {str(e)}")
            # 파싱 실패 시 현재 날짜 반환
            from datetime import datetime
            return datetime.now().strftime("%Y%m%d")

# 싱글톤 인스턴스
summary_service = SummaryService() 