import requests
from bs4 import BeautifulSoup
import time
import random
import urllib.parse
import re

class IncruitScraper:
    """
    인크루트 스크래퍼
    신입 채용공고 수집
    """
    BASE_URL = "https://job.incruit.com"
    SEARCH_URL = "https://job.incruit.com/jobdb_list/searchjob.asp"

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://job.incruit.com/"
        }
        self.session = requests.Session()

    def search(self, keywords):
        results = []

        for keyword in keywords:
            print(f"Searching Incruit for: {keyword}")
            try:
                # 인크루트 검색 파라미터
                params = {
                    "col": "job_all",
                    "kw": keyword,
                    "oession1": "4",  # 신입
                    "sortfield": "reg"  # 최신순
                }

                response = self.session.get(
                    self.SEARCH_URL,
                    params=params,
                    headers=self.headers,
                    timeout=15
                )

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")

                    # 채용공고 목록 찾기
                    # 인크루트 구조: jobpost.asp?job= 패턴의 링크
                    job_links = soup.find_all('a', href=re.compile(r'jobpost\.asp\?job='))

                    seen_ids = set()
                    for link in job_links:
                        try:
                            href = link.get('href', '')

                            # job ID 추출
                            match = re.search(r'job=(\d+)', href)
                            if not match:
                                continue

                            job_id = match.group(1)
                            if job_id in seen_ids:
                                continue
                            seen_ids.add(job_id)

                            # 제목 추출
                            title = link.get_text(strip=True)
                            if len(title) < 5:
                                # 부모 요소에서 제목 찾기
                                parent = link.find_parent(['li', 'div', 'tr'])
                                if parent:
                                    title_tag = parent.find(['strong', 'h3', 'h4', 'span'])
                                    if title_tag:
                                        title = title_tag.get_text(strip=True)

                            if len(title) < 5:
                                continue

                            # 회사명 찾기
                            company = ""
                            parent = link.find_parent(['li', 'div', 'tr'])
                            if parent:
                                company_link = parent.find('a', href=re.compile(r'/company/\d+'))
                                if company_link:
                                    company = company_link.get_text(strip=True)

                            # 마감일 찾기
                            deadline = ""
                            if parent:
                                date_patterns = [
                                    r'~\s*(\d{2}\.\d{2}\.\d{2})',
                                    r'(\d{4}-\d{2}-\d{2})',
                                    r'(\d{2}/\d{2}/\d{2})'
                                ]
                                parent_text = parent.get_text()
                                for pattern in date_patterns:
                                    match = re.search(pattern, parent_text)
                                    if match:
                                        deadline = match.group(1)
                                        break

                            # 전체 URL 생성
                            full_link = href if href.startswith('http') else f"{self.BASE_URL}/jobdb_info/{href}"

                            results.append({
                                "id": f"incruit_{job_id}",
                                "site": "Incruit",
                                "title": title[:100],
                                "company": company or "확인필요",
                                "link": full_link,
                                "deadline": deadline,
                                "hidden_keyword": keyword
                            })

                        except Exception as e:
                            continue

                    if not job_links:
                        # 대체 셀렉터 시도
                        self._fallback_parse(soup, keyword, results)

                else:
                    print(f"  Incruit: HTTP {response.status_code}")

                time.sleep(random.uniform(1, 2))

            except Exception as e:
                print(f"Error scraping Incruit for {keyword}: {e}")

        # 중복 제거
        seen = set()
        unique_results = []
        for job in results:
            if job['id'] not in seen:
                seen.add(job['id'])
                unique_results.append(job)

        return unique_results

    def _fallback_parse(self, soup, keyword, results):
        """대체 파싱 방법"""
        try:
            # 클래스 기반 셀렉터 시도
            selectors = [
                ".list-item",
                ".job-item",
                "[class*='recruit']",
                "article",
                ".card"
            ]

            items = []
            for selector in selectors:
                items = soup.select(selector)
                if items:
                    break

            for item in items[:20]:
                try:
                    link_tag = item.find('a', href=True)
                    if not link_tag:
                        continue

                    href = link_tag.get('href', '')
                    title = link_tag.get_text(strip=True)

                    if len(title) < 5:
                        continue

                    job_id = hash(f"{title}_{href}")

                    results.append({
                        "id": f"incruit_{job_id}",
                        "site": "Incruit",
                        "title": title[:100],
                        "company": "",
                        "link": href if href.startswith('http') else f"{self.BASE_URL}{href}",
                        "deadline": "",
                        "hidden_keyword": keyword
                    })
                except:
                    continue

        except Exception as e:
            print(f"  Incruit fallback failed: {e}")

    def get_details(self, url):
        return ""
