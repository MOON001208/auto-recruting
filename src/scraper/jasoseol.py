import requests
import time
import random

class JasoseolScraper:
    """
    자소설닷컴 스크래퍼
    API 엔드포인트를 활용하여 채용공고 수집
    """
    BASE_URL = "https://jasoseol.com/recruit"
    API_URL = "https://jasoseol.com/api/recruit"
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://jasoseol.com/recruit"
        }

    def search(self, keywords):
        results = []
        for keyword in keywords:
            print(f"Searching Jasoseol for: {keyword}")
            try:
                # 자소설닷컴 API 형식
                params = {
                    "keyword": keyword,
                    "career": "신입",  # 신입 필터
                    "page": 1,
                    "size": 20
                }
                
                response = requests.get(self.API_URL, params=params, headers=self.headers, timeout=10)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        items = data.get('data', data.get('recruits', data.get('list', [])))
                        
                        if isinstance(items, list):
                            for item in items:
                                try:
                                    job_id = item.get('id', item.get('recruitId', ''))
                                    title = item.get('title', item.get('recruitTitle', ''))
                                    company = item.get('company', item.get('companyName', ''))
                                    deadline = item.get('deadline', item.get('endDate', ''))
                                    
                                    if not title:
                                        continue
                                    
                                    link = f"https://jasoseol.com/recruit/{job_id}"
                                    
                                    results.append({
                                        "id": f"jasoseol_{job_id}",
                                        "site": "Jasoseol",
                                        "title": title,
                                        "company": company,
                                        "link": link,
                                        "deadline": deadline,
                                        "hidden_keyword": keyword
                                    })
                                except Exception as e:
                                    continue
                    except:
                        # JSON 파싱 실패시 HTML 파싱 시도
                        self._parse_html(response.text, keyword, results)
                
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                print(f"Error scraping Jasoseol for {keyword}: {e}")
                
        return results
    
    def _parse_html(self, html_text, keyword, results):
        """HTML 파싱 폴백"""
        from bs4 import BeautifulSoup
        try:
            soup = BeautifulSoup(html_text, "html.parser")
            items = soup.select(".recruit-item, .job-item, [class*='recruit']")
            
            for item in items[:20]:
                try:
                    title_tag = item.select_one("a, .title, h3, h4")
                    company_tag = item.select_one(".company, .corp")
                    
                    if title_tag:
                        title = title_tag.text.strip()
                        link = title_tag.get('href', '')
                        if link and not link.startswith('http'):
                            link = f"https://jasoseol.com{link}"
                        
                        company = company_tag.text.strip() if company_tag else ""
                        job_id = hash(f"{title}_{company}")
                        
                        results.append({
                            "id": f"jasoseol_{job_id}",
                            "site": "Jasoseol",
                            "title": title,
                            "company": company,
                            "link": link,
                            "deadline": "",
                            "hidden_keyword": keyword
                        })
                except:
                    continue
        except:
            pass

    def get_details(self, url):
        return ""
