from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from ..repository.issue_repository import IssueRepository
from ..model.issue_model import IssueModel
from ..schema.issue_schema import (
    IssueItemCreate, 
    IssueItem, 
    IssueListResponse,
    PipelineStats
)


class IssueDbService:
    """이슈 분석 정보 DB 접근 전용 서비스"""
    
    def __init__(self, db_session: AsyncSession):
        self.repository = IssueRepository(db_session)
    
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> IssueListResponse:
        """모든 이슈 정보 조회 (페이징)"""
        print("🗄️ [DB] 모든 이슈 정보 조회")
        
        issues = await self.repository.get_all(skip=skip, limit=limit)
        total_count = await self.repository.count_total()
        stats = await self.repository.get_statistics()
        
        issue_items = [
            IssueItem.model_validate(issue) 
            for issue in issues
        ]
        
        pipeline_stats = PipelineStats(
            total_collected=stats.get("total_count", 0),
            after_keyword_filter=stats.get("total_count", 0),  # DB에 저장된 것은 모두 필터링 통과
            after_classification=stats.get("total_count", 0),
            final_summaries=stats.get("total_count", 0),
            companies_processed=len(stats.get("top_companies", {}))
        )
        
        return IssueListResponse(
            status="success",
            message="이슈 목록 조회 완료",
            data=issue_items,
            total_count=total_count,
            page=skip // limit + 1,
            page_size=limit,
            stats=pipeline_stats
        )
    
    async def get_by_id(self, issue_id: int) -> Optional[IssueItem]:
        """ID로 이슈 정보 조회"""
        print(f"🗄️ [DB] 이슈 정보 조회 - ID: {issue_id}")
        
        issue = await self.repository.get_by_id(issue_id)
        if not issue:
            return None
        
        return IssueItem.model_validate(issue)
    
    async def get_by_corp(self, corp: str) -> List[IssueItem]:
        """기업명으로 이슈 정보 조회"""
        print(f"🗄️ [DB] 이슈 정보 조회 - 기업: {corp}")
        
        issues = await self.repository.get_by_corp(corp)
        return [
            IssueItem.model_validate(issue) 
            for issue in issues
        ]
    
    async def get_by_confidence_threshold(
        self, 
        min_confidence: float = 0.7
    ) -> List[IssueItem]:
        """신뢰도 임계값 이상의 이슈 조회"""
        print(f"🗄️ [DB] 고신뢰도 이슈 조회 - 임계값: {min_confidence}")
        
        issues = await self.repository.get_by_confidence_threshold(min_confidence)
        return [
            IssueItem.model_validate(issue) 
            for issue in issues
        ]
    
    async def get_by_sentiment(self, sentiment: str) -> List[IssueItem]:
        """감정 분석 결과로 이슈 조회"""
        print(f"🗄️ [DB] 이슈 조회 - 감정: {sentiment}")
        
        issues = await self.repository.get_by_sentiment(sentiment)
        return [
            IssueItem.model_validate(issue) 
            for issue in issues
        ]
    
    async def get_by_date_range(
        self, 
        start_date: str, 
        end_date: str
    ) -> List[IssueItem]:
        """날짜 범위로 이슈 정보 조회"""
        print(f"🗄️ [DB] 이슈 조회 - 기간: {start_date} ~ {end_date}")
        
        issues = await self.repository.get_by_date_range(start_date, end_date)
        return [
            IssueItem.model_validate(issue) 
            for issue in issues
        ]
    
    async def get_recent_issues(self, days: int = 7) -> List[IssueItem]:
        """최근 N일간의 이슈 정보 조회"""
        print(f"🗄️ [DB] 최근 {days}일 이슈 조회")
        
        issues = await self.repository.get_recent_issues(days)
        return [
            IssueItem.model_validate(issue) 
            for issue in issues
        ]
    
    async def search_by_keyword(self, keyword: str) -> List[IssueItem]:
        """키워드로 이슈 검색"""
        print(f"🗄️ [DB] 키워드 검색 - 키워드: {keyword}")
        
        issues = await self.repository.search_by_keyword(keyword)
        return [
            IssueItem.model_validate(issue) 
            for issue in issues
        ]
    
    async def get_top_issues_by_confidence(self, limit: int = 10) -> List[IssueItem]:
        """신뢰도 상위 이슈 조회"""
        print(f"🗄️ [DB] 신뢰도 상위 {limit}개 이슈 조회")
        
        issues = await self.repository.get_by_confidence_threshold(0.0)  # 모든 이슈
        # 신뢰도순 정렬 후 상위 N개
        sorted_issues = sorted(issues, key=lambda x: x.confidence, reverse=True)[:limit]
        
        return [
            IssueItem.model_validate(issue) 
            for issue in sorted_issues
        ]
    
    async def get_summary_statistics(self) -> Dict[str, Any]:
        """이슈 데이터 요약 통계"""
        print("🗄️ [DB] 이슈 요약 통계 조회")
        
        return await self.repository.get_statistics()
    
    async def count_total(self) -> int:
        """전체 이슈 개수 조회"""
        print("🗄️ [DB] 전체 이슈 개수 조회")
        return await self.repository.count_total()
    
    async def create(self, issue_data: IssueItemCreate) -> IssueItem:
        """새로운 이슈 정보 생성"""
        print(f"🗄️ [DB] 이슈 정보 생성 - 기업: {issue_data.corp}")
        
        issue = await self.repository.create(issue_data)
        return IssueItem.model_validate(issue)
    
    async def bulk_create(
        self, 
        issues_data: List[IssueItemCreate]
    ) -> List[IssueItem]:
        """이슈 정보 대량 생성"""
        print(f"🗄️ [DB] 이슈 정보 대량 생성 - {len(issues_data)}건")
        
        issues = await self.repository.bulk_create(issues_data)
        return [
            IssueItem.model_validate(issue) 
            for issue in issues
        ]
    
    async def update(
        self, 
        issue_id: int, 
        issue_data: dict
    ) -> Optional[IssueItem]:
        """이슈 정보 수정"""
        print(f"🗄️ [DB] 이슈 정보 수정 - ID: {issue_id}")
        
        from ..schema.issue_schema import IssueItemUpdate
        update_schema = IssueItemUpdate(**issue_data)
        
        issue = await self.repository.update(issue_id, update_schema)
        if not issue:
            return None
        
        return IssueItem.model_validate(issue)
    
    async def delete(self, issue_id: int) -> bool:
        """이슈 정보 삭제"""
        print(f"🗄️ [DB] 이슈 정보 삭제 - ID: {issue_id}")
        return await self.repository.delete(issue_id)
    
    async def search_issues(
        self,
        corp: Optional[str] = None,
        keyword: Optional[str] = None,
        sentiment: Optional[str] = None,
        min_confidence: Optional[float] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> IssueListResponse:
        """복합 조건으로 이슈 검색"""
        print(f"🗄️ [DB] 이슈 검색 - 기업={corp}, 키워드={keyword}, 감정={sentiment}")
        
        skip = (page - 1) * page_size
        
        # 조건별 검색
        if corp:
            issues = await self.repository.get_by_corp(corp)
        elif keyword:
            issues = await self.repository.search_by_keyword(keyword)
        elif sentiment:
            issues = await self.repository.get_by_sentiment(sentiment)
        elif min_confidence:
            issues = await self.repository.get_by_confidence_threshold(min_confidence)
        elif start_date and end_date:
            issues = await self.repository.get_by_date_range(start_date, end_date)
        else:
            issues = await self.repository.get_all(skip=skip, limit=page_size)
        
        # 추가 필터링 적용
        if min_confidence and not sentiment and not corp and not keyword:
            issues = [issue for issue in issues if issue.confidence >= min_confidence]
        
        # 페이징 적용
        if corp or keyword or sentiment or min_confidence or (start_date and end_date):
            total_count = len(issues)
            issues = issues[skip:skip + page_size]
        else:
            total_count = await self.repository.count_total()
        
        issue_items = [
            IssueItem.model_validate(issue) 
            for issue in issues
        ]
        
        # 통계 정보
        stats_data = await self.repository.get_statistics()
        pipeline_stats = PipelineStats(
            total_collected=stats_data.get("total_count", 0),
            after_keyword_filter=stats_data.get("total_count", 0),
            after_classification=stats_data.get("total_count", 0),
            final_summaries=stats_data.get("total_count", 0),
            companies_processed=len(stats_data.get("top_companies", {}))
        )
        
        return IssueListResponse(
            status="success",
            message="이슈 검색 완료",
            data=issue_items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            stats=pipeline_stats
        )
