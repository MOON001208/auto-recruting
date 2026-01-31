import requests
from bs4 import BeautifulSoup
import time
import random
import urllib.parse

class JobKoreaScraper:
    """
    잡코리아 스크래퍼 (2024년 최신 구조 대응)
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
                # URL 인코딩
                encoded_keyword = urllib.parse.quote(keyword)
                
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
                    
                    # 2024년 신규 셀렉터들 시도
                    selectors = [
                        # 새로운 구조
                        ".list-item",
                        ".recruit-info",
                        ".list-post",
                        # 기존 구조
                        ".list-default .list-post",
                        ".dev-list .list-item",
                        # 검색 결과 카드
                        "[class*='job-card']",
                        "[class*='recruit-item']"
                    ]
                    
                    items = []
                    for selector in selectors:
                        items = soup.select(selector)
                        if items:
                            print(f"  JobKorea: Found {len(items)} items with selector '{selector}'")
                            break
                    
                    if not items:
                        # 디버깅: HTML 구조 일부 출력
                        print(f"  JobKorea: No items found. Trying alternative parsing...")
                        # article 또는 li 태그에서 링크 찾기
                        all_links = soup.find_all('a', href=True)
                        job_links = [a for a in all_links if '/Recruit/' in a.get('href', '')]
                        
                        for link in job_links[:20]:
                            try:
                                href = link.get('href', '')
                                if not href.startswith('http'):
                                    href = "https://www.jobkorea.co.kr" + href
                                
                                # 상위 요소에서 정보 추출 시도
                                parent = link.find_parent(['li', 'div', 'article'])
                                
                                title = link.get_text(strip=True)
                                if len(title) < 5:  # 너무 짧으면 스킵
                                    continue
                                    
                                # 회사명 찾기
                                company = ""
                                if parent:
                                    company_tag = parent.find(['span', 'a'], class_=lambda x: x and ('corp' in x.lower() or 'company' in x.lower() or 'name' in x.lower()))
                                    if company_tag:
                                        company = company_tag.get_text(strip=True)
                                
                                # ID 추출
                                job_id = ""
                                if "GI_No=" in href:
                                    job_id = href.split("GI_No=")[1].split("&")[0]
                                else:
                                    job_id = str(hash(href))
                                
                                results.append({
                                    "id": f"jk_{job_id}",
                                    "site": "JobKorea",
                                    "title": title[:100],  # 제목 길이 제한
                                    "company": company or "확인필요",
                                    "link": href,
                                    "deadline": "",
                                    "hidden_keyword": keyword
                                })
                            except:
                                continue
                    else:
                        for item in items:
                            try:
                                # 다양한 셀렉터 시도
                                title_selectors = [".title a", ".tit a", "a.title", ".job-tit a", "h2 a", "h3 a", ".name a"]
                                company_selectors = [".name", ".corp-name", ".company", "a.corp", ".corp a"]
                                date_selectors = [".date", ".deadline", ".period", ".end-date"]
                                
                                title_tag = None
                                for sel in title_selectors:
                                    title_tag = item.select_one(sel)
                                    if title_tag:
                                        break
                                
                                if not title_tag:
                                    # 첫 번째 링크 사용
                                    title_tag = item.select_one("a[href*='/Recruit/']")
                                
                                if not title_tag:
                                    continue
                                
                                company_tag = None
                                for sel in company_selectors:
                                    company_tag = item.select_one(sel)
                                    if company_tag:
                                        break
                                
                                date_tag = None
                                for sel in date_selectors:
                                    date_tag = item.select_one(sel)
                                    if date_tag:
                                        break
                                
                                title = title_tag.get_text(strip=True)
                                link = title_tag.get('href', '')
                                if link and not link.startswith('http'):
                                    link = "https://www.jobkorea.co.kr" + link
                                
                                company = company_tag.get_text(strip=True) if company_tag else ""
                                deadline = date_tag.get_text(strip=True) if date_tag else ""
                                
                                # ID 추출
                                job_id = ""
                                if "GI_No=" in link:
                                    job_id = link.split("GI_No=")[1].split("&")[0]
                                else:
                                    job_id = str(hash(link))
                                
                                results.append({
                                    "id": f"jk_{job_id}",
                                    "site": "JobKorea",
                                    "title": title,
                                    "company": company,
                                    "link": link,
                                    "deadline": deadline,
                                    "hidden_keyword": keyword
                                })
                            except Exception as e:
                                continue
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

    def get_details(self, url):
        return ""
