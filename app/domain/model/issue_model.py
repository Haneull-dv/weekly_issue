from sqlalchemy import Column, Integer, String, Text, Float, JSON, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class IssueModel(Base):
    """이슈 분석 정보 SQLAlchemy 모델"""
    __tablename__ = "issues"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 이슈 데이터
    corp = Column(String(100), nullable=False, comment="기업명")
    summary = Column(Text, nullable=False, comment="AI 요약 내용")
    original_title = Column(Text, nullable=False, comment="원본 뉴스 제목")
    confidence = Column(Float, nullable=False, comment="AI 분류 신뢰도 (0.0-1.0)")
    matched_keywords = Column(JSON, nullable=True, comment="매칭된 키워드 목록")
    
    # 추가 메타데이터
    news_url = Column(Text, nullable=True, comment="원본 뉴스 URL")
    published_date = Column(String(20), nullable=True, comment="뉴스 발행일 (YYYYMMDD)")
    category = Column(String(50), nullable=True, comment="뉴스 카테고리")
    sentiment = Column(String(20), nullable=True, comment="감정 분석 결과 (positive/negative/neutral)")
    
    # 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성 시간")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="수정 시간")
    
    # 인덱스 설정
    __table_args__ = (
        Index('idx_issue_corp_date', 'corp', 'published_date'),
        Index('idx_issue_confidence', 'confidence'),
        Index('idx_issue_created_at', 'created_at'),
        Index('idx_issue_sentiment', 'sentiment'),
    )
    
    def __repr__(self):
        return f"<IssueModel(id={self.id}, corp='{self.corp}', confidence={self.confidence})>"
    
    def to_dict(self):
        """모델을 딕셔너리로 변환"""
        return {
            "id": self.id,
            "corp": self.corp,
            "summary": self.summary,
            "original_title": self.original_title,
            "confidence": self.confidence,
            "matched_keywords": self.matched_keywords,
            "news_url": self.news_url,
            "published_date": self.published_date,
            "category": self.category,
            "sentiment": self.sentiment,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }