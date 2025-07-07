from typing import List, Dict

class KeywordFilterService:
    def __init__(self):
        self.important_keywords = [
            "가상자산", "감사보고서", "강화", "강세", "개최", "거래", "거짓", "게임 매출", "결과", "결의", "결정", "계약", "계약 체결", "공개",
            "공매도", "공시", "기술", "기록", "규탄", "갱신", "기각", "급등",
            "누적", "단행", "달성", "대비", "대표이사", "돌파", "론칭",
            "매입", "매출", "매출액", "매수세", "미공개",
            "메타버스", "발행", "베타", "변동", "부진", "북미", "분기", "법적 대응", "법적",
            "블록체인", "비용", "사업", "사외이사", "사전", "사전 예약", "사전예약", "상장", "상장폐지", "상승 마감",
            "상향", "상향 조정", "선임", "선정", "설립", "소각", "소송", "소집", "수혜",
            "순손실", "신규", "신작",
            "실적", "실적발표", "업데이트", "영업손실", "영업이익", "예약", "예정", "예고", "오픈", "온라인", "온보딩",
            "완료", "위믹스", "유상증자", "유지", "이상", "인건비", "인수", "자기주식",
            "자사주", "자본", "자본 잠식", "적자전환", "전략", "전환", "장중", "잠식",
            "정기주주총회", "정식", "제출", "조정", "종가", "주당", "주식회사", "주요", "주주총회", "주총", "중국",
            "증가", "지급", "지분", "지속", "지속가능경영보고서", "참가",
            "참여", "처분", "체결", "최대", "최초", "추진", "출시", "취득", "테스트",
            "투자", "투자 단행", "파트너십", "파트너십 체결", "판호", "퍼블리싱", "퍼블리싱 계약",
            "한한령", "항소", "항고", "하향", "하락", "합병", "현금배당", "협력", "협약", "협약 체결", "확대", "확장",
            "획득", "흑자전환", "흥행", 
            "ESG", "%", "DLC", "1위", "ai", "cbt", "ip", "mou", "nft"
        ]
    
    def filter_by_keywords(self, news_list: List[Dict]) -> List[Dict]:
        """
        키워드 기반 1차 필터링
        """
        print(f"🤍3-2 키워드 필터 서비스 진입 - 총 {len(news_list)}개 뉴스")
        
        filtered_news = []
        
        for news in news_list:
            title = news.get("title", "").lower()
            
            # 키워드 매칭 확인
            has_keyword = False
            matched_keywords = []
            
            for keyword in self.important_keywords:
                if keyword.lower() in title:
                    has_keyword = True
                    matched_keywords.append(keyword)
            
            if has_keyword:
                news["matched_keywords"] = matched_keywords
                filtered_news.append(news)
        
        print(f"✅ 키워드 필터링 완료: {len(filtered_news)}개 뉴스 통과")
        return filtered_news

# 싱글톤 인스턴스
keyword_filter_service = KeywordFilterService() 