from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.service.issue_service import issue_service
from app.domain.service.news_pipeline_service import news_pipeline_service
from app.domain.service.issue_db_service import IssueDbService
from app.domain.schema.issue_schema import IssueResponse
from app.domain.schema.issue_schema import (
    IssueItemCreate,
    IssueListResponse
)
from app.config.companies import COMPANY_NAMES

class IssueController:
    def __init__(self, db_session: AsyncSession = None):
        self.issue_service = issue_service
        self.news_pipeline_service = news_pipeline_service
        self.db_service = IssueDbService(db_session) if db_session else None
        print("🤍1 이슈 컨트롤러 초기화 완료 (DB 서비스 포함)")
    
    def get_important_news(self) -> List[Dict]:
        """
        중요한 뉴스를 가져오는 컨트롤러 메서드 (단순 조회용 - DB 저장 불필요)
        """
        print(f"🤍2 컨트롤러 진입")
        return self.issue_service.get_important_news()
    
    async def process_news_pipeline(self, companies: List[str]) -> IssueResponse:
        """
        뉴스 파이프라인 처리 및 DB 저장
        """
        print(f"🤍2 뉴스 파이프라인 컨트롤러 진입")
        
        # companies가 None이거나 빈 리스트면 모든 기업 처리
        if not companies:
            companies = COMPANY_NAMES
            print(f"🤍2-1 모든 기업 자동 선택: {len(companies)}개 기업")
        
        print(f"🤍2-2 처리 대상 기업: {companies}")
        
        # 1. 기존 서비스로 뉴스 파이프라인 처리
        pipeline_response = await self.issue_service.process_news_pipeline_with_response(companies)
        print(f"🤍3 파이프라인 처리 완료 - {len(pipeline_response.results)}건")
        
        # 2. DB 저장 (DB 세션이 있는 경우에만)
        if self.db_service and pipeline_response.results:
            try:
                # 이슈 데이터를 DB 저장용 스키마로 변환
                issue_creates = []
                for result in pipeline_response.results:
                    # dict 타입이 아니면 dict로 변환
                    if not isinstance(result, dict):
                        if hasattr(result, 'model_dump'):
                            result = result.model_dump()
                        elif hasattr(result, '__dict__'):
                            result = dict(result.__dict__)
                    if isinstance(result, dict) and result.get('summary'):  # 요약이 있는 것만 저장
                        # id가 int면 str로 변환
                        if 'id' in result and isinstance(result['id'], int):
                            result['id'] = str(result['id'])
                        issue_create = IssueItemCreate(
                            corp=result.get('corp', ''),
                            summary=result.get('summary', ''),
                            original_title=result.get('original_title', ''),
                            confidence=result.get('confidence', 0.0),
                            matched_keywords=result.get('matched_keywords', []),
                            news_url=result.get('news_url', ''),  # 뉴스 URL 추가
                            published_date=result.get('published_date', ''),  # 발행일 추가
                            category=result.get('category', '일반'),  # 카테고리 추가
                            sentiment=result.get('sentiment', 'neutral')  # 감정 분석 추가
                        )
                        issue_creates.append(issue_create)
                
                if issue_creates:
                    # 대량 저장
                    saved_issues = await self.db_service.bulk_create(issue_creates)
                    print(f"🗄️4 DB 저장 완료 - {len(saved_issues)}건")
                else:
                    print("🗄️4 저장할 이슈 데이터가 없음")
                
            except Exception as e:
                print(f"❌ DB 저장 실패: {str(e)}")
                # DB 저장 실패해도 원본 응답은 반환
        
        return pipeline_response
    
    async def get_recent_issues_from_db(
        self, 
        days: int = 7
    ) -> IssueListResponse:
        """DB에서 최근 이슈 정보 조회 (DB 전용)"""
        print(f"🤍2 DB 조회 컨트롤러 진입 - 최근 {days}일")
        
        if not self.db_service:
            raise ValueError("DB 서비스가 초기화되지 않았습니다")
        
        return await self.db_service.get_all()
    
    async def search_issues(
        self,
        corp: str = None,
        keyword: str = None,
        min_confidence: float = None,
        page: int = 1,
        page_size: int = 20
    ) -> IssueListResponse:
        """DB에서 이슈 검색 (DB 전용)"""
        print(f"🤍2 DB 검색 컨트롤러 진입 - 기업: {corp}, 키워드: {keyword}")
        
        if not self.db_service:
            raise ValueError("DB 서비스가 초기화되지 않았습니다")
        
        return await self.db_service.search_issues(
            corp=corp,
            keyword=keyword,
            min_confidence=min_confidence,
            page=page,
            page_size=page_size
        )
    
    async def get_high_confidence_issues(
        self, 
        min_confidence: float = 0.8
    ) -> List:
        """고신뢰도 이슈 조회 (DB 전용)"""
        print(f"🤍2 고신뢰도 이슈 컨트롤러 진입 - 임계값: {min_confidence}")
        
        if not self.db_service:
            raise ValueError("DB 서비스가 초기화되지 않았습니다")
        
        return await self.db_service.get_by_confidence_threshold(min_confidence)

# 싱글톤 인스턴스 제거 - DI 기반으로 변경
