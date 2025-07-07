import asyncio
from typing import List, Dict
from fuzzywuzzy import fuzz
from .naver_news_service import naver_news_service
from .keyword_filter_service import keyword_filter_service
from .classifier_service import classifier_service
from .summary_service import summary_service

class NewsPipelineService:
    def __init__(self):
        self.naver_service = naver_news_service
        self.keyword_filter = keyword_filter_service
        self.classifier = classifier_service
        self.summary = summary_service
    
    def remove_similar_titles(self, news_list: List[Dict]) -> List[Dict]:
        """
        유사한 제목을 가진 뉴스들을 제거하여 중복 기사를 줄입니다.
        fuzzywuzzy token_set_ratio를 사용하여 한국어 어순/조사 변화에 강한 비교를 수행합니다.
        
        Args:
            news_list: 뉴스 객체 리스트
            
        Returns:
            유사한 제목을 제거한 뉴스 리스트
        """
        if not news_list:
            return news_list
        
        original_count = len(news_list)
        filtered_news = []
        similarity_threshold = 85
        
        for current_news in news_list:
            current_title = current_news.get("title", "").strip()
            if not current_title:
                continue
            
            # 이미 추가된 뉴스들과 유사도 비교
            is_similar = False
            for existing_news in filtered_news:
                existing_title = existing_news.get("title", "").strip()
                
                # fuzzywuzzy token_set_ratio를 사용한 유사도 계산
                similarity_score = fuzz.token_set_ratio(current_title, existing_title)
                
                if similarity_score >= similarity_threshold:
                    is_similar = True
                    break
            
            # 유사하지 않으면 추가
            if not is_similar:
                filtered_news.append(current_news)
        
        print(f"🧹 유사 제목 제거 결과: {len(filtered_news)}/{original_count}개")
        return filtered_news
    
    async def process_news_pipeline(self, companies: List[str]) -> Dict:
        """
        전체 뉴스 파이프라인 처리
        1. 네이버 뉴스 수집
        2. 키워드 1차 필터링
        3. AI 모델 2차 분류
        4. 요약 생성
        """
        print(f"🤍3 뉴스 파이프라인 서비스 진입 - 기업 수: {len(companies)}")
        
        try:
            # 1단계: 모든 기업의 뉴스 수집
            print("📰 1단계: 뉴스 수집 시작")
            all_news = []
            
            # 동시에 모든 기업 뉴스 수집
            tasks = [self.naver_service.fetch_news_for_company(company) for company in companies]
            news_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in news_results:
                if isinstance(result, list):
                    all_news.extend(result)
                else:
                    print(f"뉴스 수집 중 오류: {result}")
            
            print(f"✅ 1단계 완료: 총 {len(all_news)}개 뉴스 수집")
            
            if not all_news:
                return {
                    "status": "success",
                    "message": "수집된 뉴스가 없습니다.",
                    "total_collected": 0,
                    "after_keyword_filter": 0,
                    "after_classification": 0,
                    "final_summaries": 0,
                    "results": []
                }
            
            # 2단계: 키워드 기반 1차 필터링
            print("🔍 2단계: 키워드 필터링 시작")
            keyword_filtered_news = self.keyword_filter.filter_by_keywords(all_news)
            
            if not keyword_filtered_news:
                return {
                    "status": "success",
                    "message": "키워드 필터링을 통과한 뉴스가 없습니다.",
                    "total_collected": len(all_news),
                    "after_keyword_filter": 0,
                    "after_deduplication": 0,
                    "after_classification": 0,
                    "final_summaries": 0,
                    "results": []
                }
            
            # 2.5단계: 유사한 제목 제거
            print("🧹 2.5단계: 유사 제목 제거 시작")
            deduped_news = self.remove_similar_titles(keyword_filtered_news)
            
            if not deduped_news:
                return {
                    "status": "success",
                    "message": "유사 제목 제거 후 남은 뉴스가 없습니다.",
                    "total_collected": len(all_news),
                    "after_keyword_filter": len(keyword_filtered_news),
                    "after_deduplication": 0,
                    "after_classification": 0,
                    "final_summaries": 0,
                    "results": []
                }
            
            # 3단계: AI 모델 2차 분류
            print("🤖 3단계: AI 분류 시작")
            classified_news = await self.classifier.classify_news(deduped_news)
            
            if not classified_news:
                return {
                    "status": "success",
                    "message": "AI 분류를 통과한 뉴스가 없습니다.",
                    "total_collected": len(all_news),
                    "after_keyword_filter": len(keyword_filtered_news),
                    "after_deduplication": len(deduped_news),
                    "after_classification": 0,
                    "final_summaries": 0,
                    "results": []
                }
            
            # 4단계: 요약 생성
            print("📝 4단계: 요약 생성 시작")
            final_results = await self.summary.summarize_news(classified_news)
            
            # 결과 정리
            pipeline_result = {
                "status": "success",
                "message": "뉴스 파이프라인 처리 완료",
                "total_collected": len(all_news),
                "after_keyword_filter": len(keyword_filtered_news),
                "after_deduplication": len(deduped_news),
                "after_classification": len(classified_news),
                "final_summaries": len(final_results),
                "companies_processed": companies,
                "results": final_results
            }
            
            print(f"🎉 파이프라인 완료: 최종 {len(final_results)}개 요약 생성")
            return pipeline_result
            
        except Exception as e:
            print(f"❌ 파이프라인 처리 중 오류: {str(e)}")
            return {
                "status": "error",
                "message": f"파이프라인 처리 중 오류 발생: {str(e)}",
                "total_collected": 0,
                "after_keyword_filter": 0,
                "after_deduplication": 0,
                "after_classification": 0,
                "final_summaries": 0,
                "results": []
            }

# 싱글톤 인스턴스
news_pipeline_service = NewsPipelineService() 