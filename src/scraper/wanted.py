import requests
import time
import random

class WantedScraper:
    """
    원티드 스크래퍼
    내부 API를 활용한 채용공고 수집
    """
    # 원티드 내부 API 엔드포인트
    API_URL = "https://www.wanted.co.kr/api/v4/jobs"

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.wanted.co.kr/",
            "wanted-user-country": "KR",
            "wanted-user-language": "ko"
        }
        self.session = requests.Session()

    def search(self, keywords):
        results = []

        for keyword in keywords:
            print(f"Searching Wanted for: {keyword}")
            try:
                # 원티드 API 파라미터
                params = {
                    "country": "kr",
                    "job_sort": "job.latest_order",
                    "years": "0",  # 신입 (0년차)
                    "locations": "all",
                    "limit": 20,
                    "offset": 0,
                    "keyword": keyword
                }

                response = self.session.get(
                    self.API_URL,
                    params=params,
                    headers=self.headers,
                    timeout=15
                )

                if response.status_code == 200:
                    try:
                        data = response.json()
                        jobs = data.get('data', [])

                        for job in jobs:
                            try:
                                job_id = job.get('id', '')
                                title = job.get('position', '')
                                company = job.get('company', {}).get('name', '')

                                if not title:
                                    continue

                                link = f"https://www.wanted.co.kr/wd/{job_id}"

                                # 마감일 처리
                                due_time = job.get('due_time', '')
                                deadline = ""
                                if due_time:
                                    deadline = due_time[:10] if len(due_time) >= 10 else due_time

                                results.append({
                                    "id": f"wanted_{job_id}",
                                    "site": "Wanted",
                                    "title": title,
                                    "company": company,
                                    "link": link,
                                    "deadline": deadline,
                                    "hidden_keyword": keyword
                                })
                            except Exception as e:
                                continue

                    except Exception as e:
                        print(f"  Wanted: JSON parsing failed, trying alternative...")
                        self._fallback_search(keyword, results)
                else:
                    print(f"  Wanted: HTTP {response.status_code}, trying alternative...")
                    self._fallback_search(keyword, results)

                time.sleep(random.uniform(1, 2))

            except Exception as e:
                print(f"Error scraping Wanted for {keyword}: {e}")
                self._fallback_search(keyword, results)

        # 중복 제거
        seen = set()
        unique_results = []
        for job in results:
            if job['id'] not in seen:
                seen.add(job['id'])
                unique_results.append(job)

        return unique_results

    def _fallback_search(self, keyword, results):
        """대체 API 엔드포인트 시도"""
        try:
            # v3 API 시도
            alt_url = "https://www.wanted.co.kr/api/v3/search"
            params = {
                "query": keyword,
                "tab": "position",
                "country": "kr"
            }

            response = self.session.get(alt_url, params=params, headers=self.headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                positions = data.get('data', {}).get('positions', [])

                for pos in positions[:20]:
                    try:
                        job_id = pos.get('id', '')
                        title = pos.get('title', '') or pos.get('position', '')
                        company = pos.get('company_name', '') or pos.get('company', {}).get('name', '')

                        if not title or not job_id:
                            continue

                        results.append({
                            "id": f"wanted_{job_id}",
                            "site": "Wanted",
                            "title": title,
                            "company": company,
                            "link": f"https://www.wanted.co.kr/wd/{job_id}",
                            "deadline": "",
                            "hidden_keyword": keyword
                        })
                    except:
                        continue
        except Exception as e:
            print(f"  Wanted fallback also failed: {e}")

    def get_details(self, url):
        return ""
