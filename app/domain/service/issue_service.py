from typing import List, Dict
from .news_pipeline_service import news_pipeline_service
from app.domain.schema.issue_schema import IssueResponse

class IssueService:
    def __init__(self):
        self.news_pipeline_service = news_pipeline_service
    
    def get_important_news(self) -> List[Dict]:
        """
        중요한 뉴스를 반환하는 서비스 로직
        """
        print(f"🤍3 서비스 진입")
        return [
            {
                "id": 1,
                "title": "게임 산업 주요 이슈 발생",
                "content": "게임 산업에서 중요한 변화가 있었습니다.",
                "importance": "high",
                "date": "2024-01-15"
            },
            {
                "id": 2,
                "title": "투자 관련 주요 발표",
                "content": "주요 투자 관련 발표가 있었습니다.",
                "importance": "medium",
                "date": "2024-01-14"
            }
        ]
    
    async def process_news_pipeline_with_response(self, companies: List[str]) -> IssueResponse:
        """뉴스 파이프라인 처리 및 응답 변환 (controller에서 이동한 로직)"""
        print(f"🤍3 뉴스 파이프라인 서비스 로직 진입")
        
        try:
            result = await self.news_pipeline_service.process_news_pipeline(companies)
            
            # 결과를 IssueResponse 형태로 변환
            results = result.get("results", [])
            
            return IssueResponse(
                status="success",
                message=result.get("message", "뉴스 파이프라인 처리 완료"),
                total_collected=result.get("total_collected", 0),
                after_keyword_filter=result.get("after_keyword_filter", 0),
                after_deduplication=result.get("after_deduplication", 0),
                after_classification=result.get("after_classification", 0),
                final_summaries=result.get("final_summaries", 0),
                companies_processed=len(result.get("companies_processed", [])),
                results=results
            )
        except Exception as e:
            print(f"❌ 뉴스 파이프라인 처리 중 오류: {str(e)}")
            return IssueResponse(
                status="error",
                message=f"뉴스 파이프라인 처리 실패: {str(e)}",
                total_collected=0,
                after_keyword_filter=0,
                after_deduplication=0,
                after_classification=0,
                final_summaries=0,
                companies_processed=0,
                results=[]
            )

# 싱글톤 인스턴스
issue_service = IssueService() 