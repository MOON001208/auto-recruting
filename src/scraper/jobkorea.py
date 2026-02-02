import requests
from bs4 import BeautifulSoup
import time
import random
import re

class JobKoreaScraper:
    """
    잡코리아 스크래퍼 (2025년 최신 구조 대응)
    """
    BASE_URL = "https://www.jobkorea.co.kr/Search/"

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://www.jobkorea.co.kr/"
        }
        self.session = requests.Session()

    def search(self, keywords):
        results = []
        for keyword in keywords:
            print(f"Searching JobKorea for: {keyword}")
            try:
                params = {
                    "stext": keyword,
                    "careerType": "1",  # 신입
                    "tabType": "recruit",
                    "Page_No": "1"
                }

                response = self.session.get(
                    self.BASE_URL,
                    params=params,
                    headers=self.headers,
                    timeout=15
                )

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")

                    # 채용공고 링크 찾기 (제목이 있는 링크만)
                    job_links = soup.find_all('a', href=lambda x: x and '/Recruit/GI_Read/' in x)

                    seen_ids = set()
                    for link in job_links:
                        try:
                            href = link.get('href', '')
                            title = link.get_text(strip=True)

                            # 제목이 너무 짧으면 (회사 로고 등) 스킵
                            if len(title) < 10:
                                continue

                            # ID 추출
                            id_match = re.search(r'GI_Read/(\d+)', href)
                            if not id_match:
                                continue
                            job_id = id_match.group(1)

                            if job_id in seen_ids:
                                continue
                            seen_ids.add(job_id)

                            # 부모 컨테이너 찾기 (2-3레벨 위)
                            container = link.parent
                            for _ in range(3):
                                if container.parent:
                                    container = container.parent

                            container_text = container.get_text(separator='|', strip=True)

                            # 회사명 추출
                            company = self._extract_company(container, container_text)

                            # 마감일 추출
                            deadline = self._extract_deadline(container_text)

                            # 전체 URL
                            full_link = href if href.startswith('http') else f"https://www.jobkorea.co.kr{href}"

                            results.append({
                                "id": f"jk_{job_id}",
                                "site": "JobKorea",
                                "title": title[:100],
                                "company": company or "확인필요",
                                "link": full_link,
                                "deadline": deadline,
                                "hidden_keyword": keyword
                            })

                        except Exception as e:
                            continue

                    print(f"  JobKorea: {len(seen_ids)} jobs collected")

                else:
                    print(f"  JobKorea: HTTP {response.status_code}")

                time.sleep(random.uniform(1.5, 3))

            except Exception as e:
                print(f"Error scraping JobKorea for {keyword}: {e}")

        # 중복 제거
        seen = set()
        unique_results = []
        for job in results:
            if job['id'] not in seen:
                seen.add(job['id'])
                unique_results.append(job)

        return unique_results

    def _extract_company(self, container, container_text):
        """회사명 추출"""
        # 1. 회사 링크에서 찾기
        company_link = container.find('a', href=lambda x: x and '/Corp/' in x)
        if company_link:
            company = company_link.get_text(strip=True)
            if len(company) >= 2:
                return company

        # 2. (주), (유), ㈜ 패턴으로 찾기
        patterns = [
            r'(㈜[가-힣A-Za-z0-9]+)',
            r'(\([주유]\)[가-힣A-Za-z0-9]+)',
            r'([가-힣A-Za-z0-9]+\([주유]\))',
            r'([가-힣]+(?:코리아|그룹|테크|소프트|시스템|넷|랩|전자|생명|제약|바이오|증권|은행|카드|보험|캐피탈))',
        ]

        for pattern in patterns:
            match = re.search(pattern, container_text)
            if match and 3 <= len(match.group(1)) <= 30:
                return match.group(1)

        return ""

    def _extract_deadline(self, text):
        """마감일 추출 - 오늘마감/내일마감은 실제 날짜로 변환"""
        from datetime import datetime, timedelta
        
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        
        # 오늘마감 → 실제 날짜로 변환
        if '오늘마감' in text or '오늘 마감' in text:
            return today.strftime('%m/%d') + ' 마감'
        
        # 내일마감 → 실제 날짜로 변환
        if '내일마감' in text or '내일 마감' in text:
            return tomorrow.strftime('%m/%d') + ' 마감'
        
        # 다양한 마감일 패턴 (우선순위 순)
        patterns = [
            # 02/18(수) 마감
            (r'(\d{2}/\d{2}\([월화수목금토일]\))\s*마감', lambda m: m.group(1) + ' 마감'),
            # 상시채용
            (r'(상시채용)', lambda m: m.group(1)),
            # D-숫자 → 실제 날짜로 변환
            (r'D-(\d+)', lambda m: (today + timedelta(days=int(m.group(1)))).strftime('%m/%d') + ' 마감'),
            # ~02.18(수)
            (r'~\s*(\d{2}\.\d{2}\([월화수목금토일]\))', lambda m: '~' + m.group(1)),
            # ~02/18
            (r'~\s*(\d{2}/\d{2})', lambda m: '~' + m.group(1)),
            # 2025.02.18
            (r'(\d{4}\.\d{2}\.\d{2})', lambda m: m.group(1)),
        ]

        for pattern, formatter in patterns:
            match = re.search(pattern, text)
            if match:
                return formatter(match)

        return ""

    def get_details(self, url):
        return ""
