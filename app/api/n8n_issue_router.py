from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
from datetime import datetime
import logging

# 공통 DB 모듈 import
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from weekly_db.db.db_builder import get_db_session
from weekly_db.db.weekly_service import WeeklyDataService, WeeklyBatchService
from weekly_db.db.weekly_unified_model import WeeklyDataModel

# Issue 서비스 import
from app.domain.controller.issue_controller import IssueController
from app.config.companies import COMPANY_NAMES, GAME_COMPANIES

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/n8n")

@router.post("/collect-issues")
async def collect_issues_for_n8n(
    week: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    🤖 n8n 자동화: 전체 게임기업 이슈 분석 수집
    
    매주 월요일 오전 7시에 n8n이 자동 호출
    config에 등록된 모든 게임기업의 뉴스를 수집하여 AI 분석 후 weekly_data 테이블에 누적 저장
    
    처리 과정:
    1. 각 기업당 100개 뉴스 수집
    2. 키워드 필터링
    3. AI 분류 (중요도 판별)
    4. AI 요약 생성
    5. DB 저장
    
    Args:
        week: 대상 주차 (YYYY-MM-DD, None이면 현재 주)
    
    Returns:
        {"status": "success", "updated": 8, "skipped": 3, "week": "2025-01-13"}
    """
    
    if not week:
        week = WeeklyDataModel.get_current_week_monday()
    
    logger.info(f"🤖 n8n 이슈 분석 시작 - Week: {week}, Companies: {len(COMPANY_NAMES)}")
    
    # 배치 작업 시작 로그
    batch_service = WeeklyBatchService(db)
    job_id = await batch_service.start_batch_job("issue", week)
    
    try:
        # 1. 기존 Issue Controller로 뉴스 파이프라인 처리 (모든 기업)
        controller = IssueController(db_session=db)
        
        logger.info(f"🔍 뉴스 파이프라인 시작 - {len(COMPANY_NAMES)}개 기업")
        # companies=None이면 자동으로 모든 기업 처리
        pipeline_result = await controller.process_news_pipeline(None)
        
        logger.info(f"📋 이슈 분석 완료 - {len(pipeline_result.results)}건")
        
        # 2. weekly_data 테이블용 데이터 변환
        weekly_items = []
        for issue in pipeline_result.results:
            # 기업명으로 종목코드 찾기 (역매핑)
            stock_code = None
            for code, name in GAME_COMPANIES.items():
                if name == issue.corp:
                    stock_code = code
                    break
            
            weekly_item = {
                "company_name": issue.corp,
                "content": issue.summary,  # AI 요약 내용을 메인 컨텐츠로
                "stock_code": stock_code,
                "metadata": {
                    "original_title": issue.original_title,
                    "confidence": issue.confidence,
                    "matched_keywords": issue.matched_keywords,
                    "news_url": getattr(issue, 'news_url', None),
                    "published_date": getattr(issue, 'published_date', None),
                    "category": getattr(issue, 'category', None),
                    "sentiment": getattr(issue, 'sentiment', None),
                    "source": "naver_news_api"
                }
            }
            weekly_items.append(weekly_item)
        
        # 3. WeeklyDataService로 통합 테이블에 저장
        weekly_service = WeeklyDataService(db)
        result = await weekly_service.bulk_upsert_weekly_data(
            weekly_items=weekly_items,
            category="issue",
            week=week
        )
        
        # 4. 배치 작업 완료 로그
        await batch_service.finish_batch_job(job_id, result)
        
        logger.info(f"✅ n8n 이슈 분석 완료 - {result}")
        
        return {
            "status": result["status"],
            "updated": result["updated"],
            "skipped": result["skipped"],
            "errors": result["errors"],
            "week": result["week"],
            "total_companies": len(COMPANY_NAMES),
            "pipeline_stats": {
                "total_collected": pipeline_result.total_collected,
                "after_keyword_filter": pipeline_result.after_keyword_filter,
                "after_classification": pipeline_result.after_classification,
                "final_summaries": pipeline_result.final_summaries
            },
            "job_id": job_id
        }
        
    except Exception as e:
        logger.error(f"❌ n8n 이슈 분석 실패: {str(e)}")
        
        # 배치 작업 실패 로그
        await batch_service.finish_batch_job(job_id, {}, str(e))
        
        raise HTTPException(
            status_code=500, 
            detail=f"이슈 분석 중 오류 발생: {str(e)}"
        )


@router.get("/issues/status")
async def get_issues_collection_status(
    week: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    📊 이슈 분석 상태 조회
    
    특정 주차의 이슈 데이터 수집 현황을 반환
    """
    if not week:
        week = WeeklyDataModel.get_current_week_monday()
    
    try:
        weekly_service = WeeklyDataService(db)
        
        # 해당 주차 이슈 데이터 조회
        issue_data = await weekly_service.get_weekly_data(
            week=week, 
            category="issue"
        )
        
        # 배치 작업 로그 조회
        batch_service = WeeklyBatchService(db)
        recent_jobs = await batch_service.get_recent_jobs(job_type="issue", limit=5)
        
        # 평균 신뢰도 계산
        confidences = []
        for item in issue_data:
            if item.get("metadata", {}).get("confidence"):
                confidences.append(item["metadata"]["confidence"])
        
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            "week": week,
            "issue_count": len(issue_data),
            "companies_collected": len(set(item["company_name"] for item in issue_data)),
            "total_target_companies": len(COMPANY_NAMES),
            "avg_confidence": round(avg_confidence, 3),
            "high_confidence_count": len([c for c in confidences if c >= 0.8]),
            "recent_jobs": recent_jobs,
            "sample_data": issue_data[:3] if issue_data else []
        }
        
    except Exception as e:
        logger.error(f"❌ 이슈 수집 상태 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"이슈 수집 상태 조회 중 오류 발생: {str(e)}"
        )


@router.get("/issues/weeks")
async def get_available_issue_weeks(
    limit: int = 10,
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """📅 이슈 데이터가 있는 주차 목록 조회"""
    try:
        weekly_service = WeeklyDataService(db)
        weeks = await weekly_service.get_available_weeks(limit=limit)
        
        return {
            "available_weeks": weeks,
            "total_weeks": len(weeks),
            "latest_week": weeks[0] if weeks else None
        }
        
    except Exception as e:
        logger.error(f"❌ 주차 목록 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"주차 목록 조회 중 오류 발생: {str(e)}"
        ) 