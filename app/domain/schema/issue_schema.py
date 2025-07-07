from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# === 기본 이슈 아이템 ===
class IssueItemBase(BaseModel):
    """이슈 아이템 기본 스키마"""
    corp: str = Field(..., description="기업명", example="크래프톤")
    summary: str = Field(..., description="AI 요약 내용", example="크래프톤이 새로운 게임 출시를 발표했습니다.")
    original_title: str = Field(..., description="원본 뉴스 제목", example="크래프톤, 신작 MMORPG '검은사막 모바일' 출시 발표")
    confidence: float = Field(..., ge=0.0, le=1.0, description="AI 분류 신뢰도", example=0.95)
    matched_keywords: Optional[List[str]] = Field(None, description="매칭된 키워드 목록", example=["게임", "출시", "MMORPG"])

class IssueItemCreate(IssueItemBase):
    """이슈 아이템 생성 스키마"""
    news_url: Optional[str] = Field(None, description="원본 뉴스 URL")
    published_date: Optional[str] = Field(None, description="뉴스 발행일 (YYYYMMDD)")
    category: Optional[str] = Field("일반", description="뉴스 카테고리")
    sentiment: Optional[str] = Field("neutral", description="감정 분석 결과")

class IssueItemUpdate(BaseModel):
    """이슈 아이템 수정 스키마"""
    corp: Optional[str] = None
    summary: Optional[str] = None
    original_title: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    matched_keywords: Optional[List[str]] = None
    news_url: Optional[str] = None
    published_date: Optional[str] = None
    category: Optional[str] = None
    sentiment: Optional[str] = None

class IssueItem(IssueItemBase):
    """이슈 아이템 응답 스키마"""
    id: str = Field(..., description="이슈 ID")
    news_url: Optional[str] = Field(None, description="원본 뉴스 URL")
    published_date: Optional[str] = Field(None, description="뉴스 발행일")
    category: Optional[str] = Field("일반", description="뉴스 카테고리")
    sentiment: Optional[str] = Field("neutral", description="감정 분석 결과")
    created_at: Optional[datetime] = Field(None, description="생성 시간")
    updated_at: Optional[datetime] = Field(None, description="수정 시간")
    
    class Config:
        from_attributes = True

# === AI 파이프라인 통계 ===
class PipelineStats(BaseModel):
    """AI 파이프라인 통계 스키마"""
    total_collected: int = Field(..., description="총 수집된 뉴스 수", example=150)
    after_keyword_filter: int = Field(..., description="키워드 필터링 후 뉴스 수", example=75)
    after_deduplication: int = Field(..., description="중복 제거 후 뉴스 수", example=60)
    after_classification: int = Field(..., description="AI 분류 후 뉴스 수", example=45)
    final_summaries: int = Field(..., description="최종 요약 생성 수", example=30)
    companies_processed: int = Field(..., description="처리된 기업 수", example=10)

# === API 응답 스키마 ===
class IssueResponse(BaseModel):
    """이슈 분석 API 응답 스키마"""
    status: str = Field(..., description="응답 상태", example="success")
    message: str = Field(..., description="응답 메시지", example="주간 이슈 분석 완료")
    total_collected: int = Field(..., description="총 수집된 뉴스 수")
    after_keyword_filter: int = Field(..., description="키워드 필터링 후 뉴스 수")
    after_deduplication: int = Field(..., description="중복 제거 후 뉴스 수")
    after_classification: int = Field(..., description="AI 분류 후 뉴스 수")
    final_summaries: int = Field(..., description="최종 요약 생성 수")
    companies_processed: int = Field(..., description="처리된 기업 수")
    results: List[Dict[str, Any]] = Field(..., description="분석 결과 목록")

class IssueListResponse(BaseModel):
    """이슈 목록 조회 응답 스키마"""
    status: str = Field("success", description="응답 상태")
    message: str = Field("이슈 목록 조회 완료", description="응답 메시지")
    data: List[IssueItem] = Field(..., description="이슈 데이터 목록")
    total_count: int = Field(..., description="총 개수")
    page: int = Field(1, description="현재 페이지")
    page_size: int = Field(20, description="페이지 크기")
    stats: Optional[PipelineStats] = Field(None, description="파이프라인 통계")

# === 요청 스키마 ===
class IssueAnalysisRequest(BaseModel):
    """이슈 분석 요청 스키마"""
    start_date: Optional[str] = Field(None, description="시작 날짜 (YYYYMMDD)", example="20241213")
    end_date: Optional[str] = Field(None, description="종료 날짜 (YYYYMMDD)", example="20241220")
    companies: Optional[List[str]] = Field(None, description="대상 기업 목록", example=["크래프톤", "넷마블", "엔씨소프트"])
    keywords: Optional[List[str]] = Field(None, description="추가 키워드", example=["게임", "출시", "업데이트"])
    confidence_threshold: float = Field(0.7, ge=0.0, le=1.0, description="신뢰도 임계값")

class IssueSearchRequest(BaseModel):
    """이슈 검색 요청 스키마"""
    corp: Optional[str] = Field(None, description="기업명")
    keyword: Optional[str] = Field(None, description="검색 키워드")
    sentiment: Optional[str] = Field(None, description="감정 분석 결과")
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="최소 신뢰도")
    start_date: Optional[str] = Field(None, description="시작 날짜")
    end_date: Optional[str] = Field(None, description="종료 날짜")
    page: int = Field(1, ge=1, description="페이지 번호")
    page_size: int = Field(20, ge=1, le=100, description="페이지 크기")

# === 배치 처리 스키마 ===
class BatchJobRequest(BaseModel):
    """배치 작업 요청 스키마"""
    job_type: str = Field(..., description="작업 타입", example="daily_analysis")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="작업 파라미터")
    schedule_time: Optional[str] = Field(None, description="예약 실행 시간 (HH:MM)")

class BatchJobResponse(BaseModel):
    """배치 작업 응답 스키마"""
    job_id: str = Field(..., description="작업 ID")
    status: str = Field(..., description="작업 상태")
    message: str = Field(..., description="응답 메시지")
    started_at: Optional[datetime] = Field(None, description="시작 시간")
    estimated_duration: Optional[int] = Field(None, description="예상 소요 시간 (분)")

# === 에러 응답 ===
class ErrorResponse(BaseModel):
    """에러 응답 스키마"""
    status: str = Field("error", description="응답 상태")
    message: str = Field(..., description="에러 메시지")
    error_code: Optional[str] = Field(None, description="에러 코드")
    details: Optional[dict] = Field(None, description="에러 세부사항")
