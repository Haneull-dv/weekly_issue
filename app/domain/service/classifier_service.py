import httpx
import asyncio
from typing import List, Dict
from app.config.settings import CLASSIFIER_URL

class ClassifierService:
    def __init__(self):
        self.classifier_url = CLASSIFIER_URL
        print(f"🔧 ClassifierService 초기화 - URL: {self.classifier_url}")
    
    async def classify_news(self, news_list: List[Dict]) -> List[Dict]:
        """
        2차 중요도 분류 모델로 뉴스 제목 분류
        """
        print(f"🤍3-3 분류기 서비스 진입 - 총 {len(news_list)}개 뉴스")
        print(f"🔧 Classifier URL: {self.classifier_url}")
        
        if not news_list:
            return []
        
        classified_news = []
        
        try:
            # 배치로 분류 시도
            titles = [news.get("title", "") for news in news_list]
            print(f"📤 분류기 요청 - {len(titles)}개 제목")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {"text": titles}
                print(f"📤 분류기 페이로드: {len(payload['text'])}개 항목")
                
                response = await client.post(
                    self.classifier_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                print(f"📥 분류기 응답 - Status: {response.status_code}")
            
                if response.status_code == 200:
                    result = response.json()
                    print(f"📥 분류기 응답 내용: {str(result)[:200]}...")
                    
                    batch_results = result.get("result", [])
                    print(f"📊 분류 결과: {len(batch_results)}개")
                    
                    # 결과와 원본 뉴스 매칭
                    for i, news in enumerate(news_list):
                        if i < len(batch_results):
                            prediction = batch_results[i]
                            
                            # 원본 뉴스 정보를 모두 복사
                            classified_item = news.copy()
                            
                            # 분류 결과 추가
                            classified_item["classification"] = {
                                "label": prediction.get("label"),
                                "confidence": prediction.get("confidence")
                            }
                            
                            # 신뢰도가 0.6 이상인 경우 통과 (임시 완화)
                            confidence = prediction.get("confidence", 0)
                            if confidence >= 0.6:
                                classified_news.append(classified_item)
                                print(f"✅ 분류 통과: {news.get('title', '')[:30]}... (신뢰도: {confidence:.3f})")
                            else:
                                print(f"❌ 분류 제외: {news.get('title', '')[:30]}... (신뢰도: {confidence:.3f})")
                    
                    print(f"✅ 분류기 처리 완료: {len(classified_news)}개 뉴스가 중요도 기준 통과")
                    return classified_news
                
                else:
                    print(f"❌ 분류기 API 호출 실패: {response.status_code}")
                    print(f"❌ 응답 내용: {response.text}")
                    # 분류 API 실패 시 원본 뉴스를 그대로 반환 (fallback)
                    print("⚠️ 분류기 실패로 인해 모든 뉴스를 통과시킵니다.")
                    for news in news_list:
                        fallback_item = news.copy()
                        fallback_item["classification"] = {
                            "label": "important",  # 기본값
                            "confidence": 0.7  # 기본 신뢰도
                        }
                        classified_news.append(fallback_item)
                    return classified_news
                
        except httpx.ConnectError as e:
            print(f"❌ 분류기 연결 실패: {str(e)}")
            print("💡 분류기 서비스가 실행되고 있는지 확인해주세요.")
            return self._create_fallback_results(news_list, "connection_error")
            
        except httpx.TimeoutException as e:
            print(f"❌ 분류기 타임아웃: {str(e)}")
            return self._create_fallback_results(news_list, "timeout")
            
        except httpx.RequestError as e:
            print(f"❌ 분류기 호출 중 네트워크 오류: {str(e)}")
            return self._create_fallback_results(news_list, "network_error")
            
        except Exception as e:
            print(f"❌ 분류기 처리 중 오류: {str(e)}")
            return self._create_fallback_results(news_list, "unknown_error")
    
    def _create_fallback_results(self, news_list: List[Dict], error_type: str) -> List[Dict]:
        """
        Fallback 결과 생성
        """
        print(f"⚠️ {error_type}로 인해 모든 뉴스를 통과시킵니다.")
        classified_news = []
        for news in news_list:
            fallback_item = news.copy()
            fallback_item["classification"] = {
                "label": "important",
                "confidence": 0.7
            }
            classified_news.append(fallback_item)
        return classified_news

# 싱글톤 인스턴스
classifier_service = ClassifierService() 