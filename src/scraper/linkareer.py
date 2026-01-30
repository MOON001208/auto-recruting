import requests
import time
import random

class LinkareerScraper:
    """
    링커리어 스크래퍼
    대학생/취준생 대상 인턴, 신입 채용공고 수집
    """
    BASE_URL = "https://linkareer.com/list/recruit"
    API_URL = "https://api.linkareer.com/graphql"
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Referer": "https://linkareer.com/"
        }

    def search(self, keywords):
        results = []
        for keyword in keywords:
            print(f"Searching Linkareer for: {keyword}")
            try:
                # 링커리어 GraphQL API 사용 시도
                query = {
                    "operationName": "ActivityList",
                    "variables": {
                        "filterBy": {
                            "keyword": keyword,
                            "activityTypeCategories": ["RECRUIT"],
                            "careerTypes": ["NEWCOMER", "ANY"]  # 신입, 경력무관
                        },
                        "first": 20,
                        "orderBy": "RECENT"
                    },
                    "query": """
                    query ActivityList($filterBy: ActivityFilterBy, $first: Int, $orderBy: ActivityOrder) {
                        activities(filterBy: $filterBy, first: $first, orderBy: $orderBy) {
                            edges {
                                node {
                                    id
                                    title
                                    organization { name }
                                    deadlineAt
                                }
                            }
                        }
                    }
                    """
                }
                
                response = requests.post(self.API_URL, json=query, headers=self.headers, timeout=10)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        edges = data.get('data', {}).get('activities', {}).get('edges', [])
                        
                        for edge in edges:
                            try:
                                node = edge.get('node', {})
                                job_id = node.get('id', '')
                                title = node.get('title', '')
                                org = node.get('organization', {})
                                company = org.get('name', '') if org else ''
                                deadline = node.get('deadlineAt', '')
                                
                                if not title:
                                    continue
                                
                                link = f"https://linkareer.com/activity/{job_id}"
                                
                                results.append({
                                    "id": f"linkareer_{job_id}",
                                    "site": "Linkareer",
                                    "title": title,
                                    "company": company,
                                    "link": link,
                                    "deadline": deadline[:10] if deadline else "",
                                    "hidden_keyword": keyword
                                })
                            except Exception as e:
                                continue
                    except:
                        # GraphQL 실패시 직접 검색 페이지 파싱 시도
                        self._fallback_search(keyword, results)
                else:
                    self._fallback_search(keyword, results)
                
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                print(f"Error scraping Linkareer for {keyword}: {e}")
                self._fallback_search(keyword, results)
                
        return results
    
    def _fallback_search(self, keyword, results):
        """HTML 파싱 폴백"""
        try:
            search_url = f"https://linkareer.com/list/recruit?keyword={keyword}"
            response = requests.get(search_url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, "html.parser")
                
                # 링커리어 카드 형식
                items = soup.select("[class*='ActivityCard'], [class*='card'], .recruit-item")
                
                for item in items[:20]:
                    try:
                        title_tag = item.select_one("a, h3, .title")
                        company_tag = item.select_one(".company, .organization, [class*='company']")
                        
                        if title_tag:
                            title = title_tag.text.strip()
                            link = title_tag.get('href', '')
                            if link and not link.startswith('http'):
                                link = f"https://linkareer.com{link}"
                            
                            company = company_tag.text.strip() if company_tag else ""
                            job_id = hash(f"{title}_{company}")
                            
                            results.append({
                                "id": f"linkareer_{job_id}",
                                "site": "Linkareer",
                                "title": title,
                                "company": company,
                                "link": link,
                                "deadline": "",
                                "hidden_keyword": keyword
                            })
                    except:
                        continue
        except Exception as e:
            print(f"Linkareer fallback failed: {e}")

    def get_details(self, url):
        return ""
