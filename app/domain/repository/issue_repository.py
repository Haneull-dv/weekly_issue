from typing import List, Optional
from sqlalchemy import select, and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..model.issue_model import IssueModel
from ..schema.issue_schema import IssueItemCreate, IssueItemUpdate


class IssueRepository:
    """이슈 분석 정보 Repository 클래스"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def create(self, issue_data: IssueItemCreate) -> IssueModel:
        """새로운 이슈 정보 생성"""
        issue = IssueModel(
            corp=issue_data.corp,
            summary=issue_data.summary,
            original_title=issue_data.original_title,
            confidence=issue_data.confidence,
            matched_keywords=issue_data.matched_keywords,
            news_url=issue_data.news_url,
            published_date=issue_data.published_date,
            category=issue_data.category,
            sentiment=issue_data.sentiment
        )
        
        self.db.add(issue)
        await self.db.commit()
        await self.db.refresh(issue)
        return issue
    
    async def get_by_id(self, issue_id: int) -> Optional[IssueModel]:
        """ID로 이슈 정보 조회"""
        query = select(IssueModel).where(IssueModel.id == issue_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[IssueModel]:
        """모든 이슈 정보 조회 (페이징)"""
        query = (
            select(IssueModel)
            .order_by(desc(IssueModel.confidence), desc(IssueModel.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_by_corp(self, corp: str) -> List[IssueModel]:
        """기업명으로 이슈 정보 조회"""
        query = (
            select(IssueModel)
            .where(IssueModel.corp == corp)
            .order_by(desc(IssueModel.confidence), desc(IssueModel.created_at))
        )
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_by_confidence_threshold(
        self, 
        min_confidence: float = 0.7
    ) -> List[IssueModel]:
        """신뢰도 임계값 이상의 이슈 조회"""
        query = (
            select(IssueModel)
            .where(IssueModel.confidence >= min_confidence)
            .order_by(desc(IssueModel.confidence), desc(IssueModel.created_at))
        )
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_by_sentiment(self, sentiment: str) -> List[IssueModel]:
        """감정 분석 결과로 이슈 조회"""
        query = (
            select(IssueModel)
            .where(IssueModel.sentiment == sentiment)
            .order_by(desc(IssueModel.confidence), desc(IssueModel.created_at))
        )
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_by_date_range(
        self, 
        start_date: str, 
        end_date: str
    ) -> List[IssueModel]:
        """날짜 범위로 이슈 정보 조회"""
        query = (
            select(IssueModel)
            .where(
                and_(
                    IssueModel.published_date >= start_date,
                    IssueModel.published_date <= end_date
                )
            )
            .order_by(desc(IssueModel.confidence))
        )
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def search_by_keyword(self, keyword: str) -> List[IssueModel]:
        """키워드로 이슈 검색 (제목 또는 요약에서)"""
        query = (
            select(IssueModel)
            .where(
                IssueModel.original_title.contains(keyword) |
                IssueModel.summary.contains(keyword)
            )
            .order_by(desc(IssueModel.confidence))
        )
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_recent_issues(self, days: int = 7) -> List[IssueModel]:
        """최근 N일간의 이슈 정보 조회"""
        from datetime import datetime, timedelta
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        query = (
            select(IssueModel)
            .where(IssueModel.created_at >= start_date)
            .order_by(desc(IssueModel.confidence), desc(IssueModel.created_at))
        )
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_statistics(self) -> dict:
        """이슈 통계 정보 조회"""
        # 전체 개수
        total_query = select(func.count(IssueModel.id))
        total_result = await self.db.execute(total_query)
        total_count = total_result.scalar()
        
        # 감정별 개수
        sentiment_query = (
            select(IssueModel.sentiment, func.count(IssueModel.id))
            .group_by(IssueModel.sentiment)
        )
        sentiment_result = await self.db.execute(sentiment_query)
        sentiment_stats = {row[0]: row[1] for row in sentiment_result.all()}
        
        # 평균 신뢰도
        avg_confidence_query = select(func.avg(IssueModel.confidence))
        avg_confidence_result = await self.db.execute(avg_confidence_query)
        avg_confidence = avg_confidence_result.scalar() or 0.0
        
        # 기업별 개수
        corp_query = (
            select(IssueModel.corp, func.count(IssueModel.id))
            .group_by(IssueModel.corp)
            .order_by(desc(func.count(IssueModel.id)))
            .limit(10)
        )
        corp_result = await self.db.execute(corp_query)
        corp_stats = {row[0]: row[1] for row in corp_result.all()}
        
        return {
            "total_count": total_count,
            "sentiment_distribution": sentiment_stats,
            "average_confidence": round(avg_confidence, 3),
            "top_companies": corp_stats
        }
    
    async def count_total(self) -> int:
        """전체 이슈 개수 조회"""
        query = select(func.count(IssueModel.id))
        result = await self.db.execute(query)
        return result.scalar()
    
    async def update(
        self, 
        issue_id: int, 
        issue_data: IssueItemUpdate
    ) -> Optional[IssueModel]:
        """이슈 정보 수정"""
        issue = await self.get_by_id(issue_id)
        if not issue:
            return None
        
        update_data = issue_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(issue, field, value)
        
        await self.db.commit()
        await self.db.refresh(issue)
        return issue
    
    async def delete(self, issue_id: int) -> bool:
        """이슈 정보 삭제"""
        issue = await self.get_by_id(issue_id)
        if not issue:
            return False
        
        await self.db.delete(issue)
        await self.db.commit()
        return True
    
    async def bulk_create(self, issues_data: List[IssueItemCreate]) -> List[IssueModel]:
        """이슈 정보 대량 생성"""
        issues = []
        for data in issues_data:
            issue = IssueModel(
                corp=data.corp,
                summary=data.summary,
                original_title=data.original_title,
                confidence=data.confidence,
                matched_keywords=data.matched_keywords,
                news_url=data.news_url,
                published_date=data.published_date,
                category=data.category,
                sentiment=data.sentiment
            )
            issues.append(issue)
        
        self.db.add_all(issues)
        await self.db.commit()
        
        # 새로 생성된 ID로 다시 조회
        for issue in issues:
            await self.db.refresh(issue)
        
        return issues
