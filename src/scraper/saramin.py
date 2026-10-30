import requests
from bs4 import BeautifulSoup
import time
import random
import re
from datetime import datetime, timedelta
from src.scraper.details import fetch_description
from src.scraper.health import SearchHealth

class SaraminScraper(SearchHealth):
    BASE_URL = "https://www.saramin.co.kr/zf_user/search/recruit"
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.reset_health()

    def search(self, keywords):
        self.reset_health()
        results = []
        for keyword in keywords:
            print(f"Searching Saramin for: {keyword}")
            try:
                # Basic parameters for Saramin search
                params = {
                    "searchType": "search",
                    "searchword": keyword,
                    "recruitPage": 1,
                    "recruitSort": "relation",
                    "recruitPageCount": 20,  # Get top 20 relevant
                    "exp_cd": 1,  # 신입 필터 (1=신입, 2=경력, 3=신입/경력)
                    "exp_none": 1  # 경력무관도 포함
                }
                
                response = requests.get(self.BASE_URL, params=params, headers=self.headers, timeout=15)
                if response.status_code == 200:
                    self.search_succeeded()
                    soup = BeautifulSoup(response.text, "html.parser")
                    items = soup.select(".item_recruit")
                    
                    for item in items:
                        try:
                            title_tag = item.select_one(".job_tit a")
                            company_tag = item.select_one(".corp_name a")
                            date_tag = item.select_one(".job_date .date")
                            
                            if not title_tag: continue
                            
                            job_id = title_tag['href'].split("rec_idx=")[1].split("&")[0]
                            title = title_tag.text.strip()
                            company = company_tag.text.strip()
                            link = "https://www.saramin.co.kr" + title_tag['href']
                            deadline = self._convert_deadline(date_tag.text.strip())
                            
                            results.append({
                                "id": f"saramin_{job_id}",
                                "site": "Saramin",
                                "title": title,
                                "company": company,
                                "link": link,
                                "deadline": deadline,
                                "hidden_keyword": keyword
                            })
                        except Exception as e:
                            print(f"Error parsing item: {e}")
                            continue
                else:
                    self.search_failed(f'HTTP {response.status_code}')
                
                # Be nice to the server
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                self.search_failed(type(e).__name__)
                print(f"Error scraping Saramin for {keyword}: {e}")
            if self.should_stop():
                print('Saramin: 연속 실패로 나머지 검색을 중단합니다.')
                break
                
        return results

    def _convert_deadline(self, text):
        """마감일을 절대 날짜로 변환"""
        today = datetime.now()
        tomorrow = today + timedelta(days=1)

        # 오늘마감 → 실제 날짜로 변환
        if '오늘' in text:
            return today.strftime('%m/%d') + ' 마감'

        # 내일마감 → 실제 날짜로 변환
        if '내일' in text:
            return tomorrow.strftime('%m/%d') + ' 마감'

        # D-숫자 패턴
        d_match = re.search(r'D-(\d+)', text)
        if d_match:
            days = int(d_match.group(1))
            target = today + timedelta(days=days)
            return target.strftime('%m/%d') + ' 마감'

        return text

    def get_details(self, url):
        return fetch_description(url, 'Saramin', self.headers)
