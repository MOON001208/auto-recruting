import requests
import time
import random

class LinkareerScraper:
    """
    링커리어 스크래퍼 (2025년 최신 API 구조 대응)
    대학생/취준생 대상 인턴, 신입 채용공고 수집
    """
    BASE_URL = "https://linkareer.com/list/recruit"
    API_URL = "https://api.linkareer.com/graphql"

    # 채용 타입 ID (링커리어 내부 분류)
    RECRUIT_TYPE_ID = "5"

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": "https://linkareer.com",
            "Referer": "https://linkareer.com/list/recruit"
        }

    def search(self, keywords):
        results = []

        print(f"Searching Linkareer for all keywords...")
        try:
            # 링커리어 GraphQL API - 채용 타입만 필터링
            query = {
                "query": """
                query GetRecruitActivities($filterBy: ActivityFilter) {
                    activities(filterBy: $filterBy) {
                        nodes {
                            id
                            title
                            organizationName
                            deadlineStatus
                        }
                    }
                }
                """,
                "variables": {
                    "filterBy": {
                        "activityTypeID": self.RECRUIT_TYPE_ID
                    }
                }
            }

            response = requests.post(self.API_URL, json=query, headers=self.headers, timeout=15)

            if response.status_code == 200:
                data = response.json()
                nodes = data.get('data', {}).get('activities', {}).get('nodes', [])

                print(f"  Linkareer: Retrieved {len(nodes)} recruit postings")

                for node in nodes:
                    try:
                        job_id = node.get('id', '')
                        title = node.get('title', '')
                        company = node.get('organizationName', '')
                        deadline = node.get('deadlineStatus', '')

                        if not title:
                            continue

                        # 키워드 매칭
                        matched_keyword = ""
                        title_lower = title.lower()
                        for kw in keywords:
                            if kw.lower() in title_lower:
                                matched_keyword = kw
                                break

                        link = f"https://linkareer.com/activity/{job_id}"

                        results.append({
                            "id": f"linkareer_{job_id}",
                            "site": "Linkareer",
                            "title": title,
                            "company": company,
                            "link": link,
                            "deadline": deadline if deadline else "",
                            "hidden_keyword": matched_keyword or keywords[0] if keywords else ""
                        })
                    except Exception as e:
                        continue
            else:
                print(f"  Linkareer: HTTP {response.status_code}, trying fallback...")
                self._fallback_search(keywords, results)

            time.sleep(random.uniform(1, 2))

        except Exception as e:
            print(f"Error scraping Linkareer: {e}")
            self._fallback_search(keywords, results)

        # 중복 제거
        seen = set()
        unique_results = []
        for job in results:
            if job['id'] not in seen:
                seen.add(job['id'])
                unique_results.append(job)

        return unique_results

    def _fallback_search(self, keywords, results):
        """HTML 파싱 폴백"""
        try:
            from bs4 import BeautifulSoup

            for keyword in keywords[:3]:  # 처음 3개 키워드만
                search_url = f"https://linkareer.com/list/recruit?filterBy_keyword={keyword}"
                response = requests.get(search_url, headers=self.headers, timeout=10)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")

                    # __NEXT_DATA__에서 데이터 추출 시도
                    script = soup.find("script", id="__NEXT_DATA__")
                    if script:
                        import json
                        try:
                            data = json.loads(script.string)
                            # Next.js 데이터 구조 탐색
                            props = data.get('props', {}).get('pageProps', {})
                            activities = props.get('activities', [])

                            for act in activities:
                                job_id = act.get('id', str(hash(act.get('title', ''))))
                                title = act.get('title', '')
                                company = act.get('organizationName', '')

                                if title:
                                    results.append({
                                        "id": f"linkareer_{job_id}",
                                        "site": "Linkareer",
                                        "title": title,
                                        "company": company,
                                        "link": f"https://linkareer.com/activity/{job_id}",
                                        "deadline": "",
                                        "hidden_keyword": keyword
                                    })
                        except:
                            pass

                    # 링크 기반 폴백
                    links = soup.find_all('a', href=True)
                    activity_links = [l for l in links if '/activity/' in l.get('href', '')]

                    for link in activity_links[:10]:
                        try:
                            href = link.get('href', '')
                            title = link.get_text(strip=True)

                            if len(title) < 5:
                                continue

                            # ID 추출
                            import re
                            match = re.search(r'/activity/(\d+)', href)
                            job_id = match.group(1) if match else str(hash(title))

                            full_link = href if href.startswith('http') else f"https://linkareer.com{href}"

                            results.append({
                                "id": f"linkareer_{job_id}",
                                "site": "Linkareer",
                                "title": title[:100],
                                "company": "",
                                "link": full_link,
                                "deadline": "",
                                "hidden_keyword": keyword
                            })
                        except:
                            continue

                time.sleep(random.uniform(0.5, 1))

        except Exception as e:
            print(f"Linkareer fallback failed: {e}")

    def get_details(self, url):
        return ""
