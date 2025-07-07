"""
CQRS 패턴 적용 Issue Command Side API

DDD + CQRS 구조:
- Command Side: issue 도메인 데이터를 로컬 테이블에 저장
- Projection: 로컬 저장 완료 후 weekly_data 테이블로 projection 전송
- Event-Driven: n8n 자동화와 연동
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from datetime import datetime, timezone
import logging
import httpx
import sys
import os

# 프로젝트 루트 추가 (weekly_db 모듈 접근)
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# 도메인 서비스 import
from app.domain.controller.issue_controller import IssueController
from weekly_db.db.db_builder import get_db_session

# 설정 import
from app.config.companies import COMPANY_NAMES, GAME_COMPANIES

# 주차 계산 utility import
from weekly_db.db.weekly_unified_model import WeeklyDataModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cqrs-issue")


@router.post("/collect-and-project")
async def collect_issue_with_cqrs(
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    [CQRS Command Side] 이슈 데이터 수집 → 로컬 저장 → Projection
    
    CQRS 패턴 적용:
    1. Command Side: 이슈 데이터를 issue 도메인의 로컬 테이블에 저장
    2. Projection: 로컬 저장 완료 후 weekly_data 테이블로 projection 전송
    3. Event-Driven: 배치 작업 로그로 다른 서비스와 동기화
    
    n8n에서 매주 자동으로 호출됩니다.
    """
    job_id = None
    week = WeeklyDataModel.get_current_week_monday()
    
    try:
        logger.info(f"🔧 [CQRS Command] Issue 수집 시작 - Week: {week}")
        
        # ==========================================
        # 1. 배치 작업 시작 로그 (CQRS Monitoring)
        # ==========================================
        async with httpx.AsyncClient(timeout=30.0) as client:
            batch_start_response = await client.post(
                "http://weekly_data:8091/weekly-cqrs/domain-command/issue",
                params={
                    "week": week,
                    "action": "start_job"
                }
            )
            batch_start_result = batch_start_response.json()
            job_id = batch_start_result.get("job_id")
            
            logger.info(f"📝 [CQRS] 배치 작업 시작 로그 - Job ID: {job_id}")
        
        # ==========================================
        # 2. Command Side: 로컬 도메인 테이블에 저장
        # ==========================================
        
        # Issue Controller로 데이터 수집
        controller = IssueController(db_session=db)
        logger.info(f"🔍 [CQRS Command] 이슈 데이터 수집 - {len(COMPANY_NAMES)}개 기업")
        
        # 뉴스 파이프라인 처리 (모든 기업)
        pipeline_result = await controller.process_news_pipeline(None)
        logger.info(f"📋 [CQRS Command] 이슈 수집 완료 - {len(pipeline_result.results)}건")
        
        # 로컬 테이블 저장 통계
        local_updated = len(pipeline_result.results)
        local_skipped = 0
        projection_data = []  # weekly_data로 보낼 projection 데이터
        
        # ==========================================
        # 3. 로컬 테이블 저장 및 Projection 데이터 준비
        # ==========================================
        
        for issue in pipeline_result.results:
            try:
                # 기업명으로 종목코드 찾기 (역매핑)
                stock_code = None
                for code, name in GAME_COMPANIES.items():
                    if name == issue.corp:
                        stock_code = code
                        break
                
                # Projection용 데이터 준비 (weekly_data 테이블로 전송할 형태)
                projection_item = {
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
                        "source": "naver_news_api",
                        "cqrs_pattern": "command_to_projection"
                    }
                }
                
                projection_data.append(projection_item)
                
                logger.debug(f"✅ [CQRS Command] 로컬 저장 및 Projection 준비: {issue.corp}")
                
            except Exception as e:
                logger.error(f"❌ [CQRS Command] 개별 이슈 처리 실패: {str(e)}")
                local_skipped += 1
        
        # ==========================================
        # 4. Projection: weekly_data 테이블로 전송
        # ==========================================
        
        logger.info(f"🔄 [CQRS Projection] weekly_data로 projection 시작 - {len(projection_data)}건")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            projection_response = await client.post(
                "http://weekly_data:8091/weekly-cqrs/project-domain-data",
                params={
                    "category": "issue", 
                    "week": week
                },
                json=projection_data
            )
            projection_result = projection_response.json()
            
            logger.info(f"✅ [CQRS Projection] Projection 완료 - Updated: {projection_result.get('updated', 0)}")
        
        # ==========================================
        # 5. 배치 작업 완료 로그
        # ==========================================
        
        final_result = {
            "local_updated": local_updated,
            "local_skipped": local_skipped,
            "projection_updated": projection_result.get("updated", 0),
            "projection_skipped": projection_result.get("skipped", 0),
            "total_collected": len(pipeline_result.results),
            "pipeline_stats": {
                "total_collected": pipeline_result.total_collected,
                "after_keyword_filter": pipeline_result.after_keyword_filter,
                "after_classification": pipeline_result.after_classification,
                "final_summaries": pipeline_result.final_summaries
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.post(
                "http://weekly_data:8091/weekly-cqrs/domain-command/issue",
                params={
                    "week": week,
                    "action": "finish_job"
                },
                json={
                    "job_id": job_id,
                    "result": final_result
                }
            )
            
            logger.info(f"📝 [CQRS] 배치 작업 완료 로그 - Job ID: {job_id}")
        
        # ==========================================
        # 6. 최종 응답
        # ==========================================
        
        return {
            "status": "success",
            "week": week,
            "cqrs_pattern": "command_side_completed",
            "local_storage": {
                "updated": local_updated,
                "skipped": local_skipped,
                "table": "issues"
            },
            "projection": {
                "updated": projection_result.get("updated", 0),
                "skipped": projection_result.get("skipped", 0),
                "table": "weekly_data"
            },
            "total_companies": len(COMPANY_NAMES),
            "total_collected": len(pipeline_result.results),
            "pipeline_stats": final_result["pipeline_stats"],
            "job_id": job_id,
            "collected_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        error_message = f"Issue CQRS 처리 실패: {str(e)}"
        logger.error(f"❌ [CQRS Command] {error_message}")
        return {
            "status": "error",
            "message": "Issue CQRS 처리 중 오류가 발생했습니다.",
            "error": error_message
        }


@router.get("/cqrs-status")
async def get_issue_cqrs_status() -> Dict[str, Any]:
    """
    [CQRS Status] Issue 도메인 CQRS 상태 확인
    
    현재 CQRS 패턴 구현 상태와 도메인 서비스 정보를 반환합니다.
    """
    return {
        "service": "weekly_issue",
        "cqrs_pattern": "enabled",
        "domain": "issue",
        "endpoints": {
            "command_side": "/cqrs-issue/collect-and-project",
            "status": "/cqrs-issue/cqrs-status"
        },
        "table_structure": {
            "local_table": "issues",
            "projection_table": "weekly_data"
        },
        "supported_companies": len(COMPANY_NAMES),
        "data_source": "naver_news_api",
        "processing_pipeline": [
            "뉴스 수집",
            "키워드 필터링", 
            "AI 분류",
            "AI 요약",
            "로컬 저장",
            "Projection"
        ]
    } 