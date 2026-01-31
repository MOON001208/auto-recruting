import requests
from bs4 import BeautifulSoup
import time
import random
import re

class JasoseolScraper:
    """
    자소설닷컴 스크래퍼 (2024년 최신 구조 대응)
    채용공고 목록 페이지 직접 파싱
    """
    BASE_URL = "https://jasoseol.com"
    RECRUIT_URL = "https://jasoseol.com/recruit"
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://jasoseol.com/"
        }
        self.session = requests.Session()

    def search(self, keywords):
        results = []
        
        # 먼저 메인 채용공고 페이지에서 전체 목록 가져오기
        print(f"Searching Jasoseol: Fetching main recruit page...")
        
        try:
            # 메인 페이지 접근
            response = self.session.get(
                self.RECRUIT_URL, 
                headers=self.headers, 
                timeout=15
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                
                # 다양한 셀렉터 시도
                selectors = [
                    ".recruit-card",
                    ".schedule-item",
                    ".recruit-item",
                    "[class*='schedule']",
                    "[class*='recruit']",
                    ".card",
                    "article",
                    ".item"
                ]
                
                items = []
                for selector in selectors:
                    items = soup.select(selector)
                    if len(items) > 3:  # 최소 3개 이상 찾아야 유효
                        print(f"  Jasoseol: Found {len(items)} items with selector '{selector}'")
                        break
                
                if items:
                    for item in items:
                        try:
                            job_data = self._parse_item(item, keywords)
                            if job_data:
                                results.append(job_data)
                        except:
                            continue
                else:
                    # 폴백: 모든 링크에서 채용공고 찾기
                    print(f"  Jasoseol: Trying link-based parsing...")
                    results.extend(self._parse_links(soup, keywords))
                    
        except Exception as e:
            print(f"Error fetching Jasoseol main page: {e}")
        
        # 키워드별 검색도 시도
        for keyword in keywords[:5]:  # 처음 5개 키워드만
            try:
                search_url = f"{self.RECRUIT_URL}?keyword={keyword}"
                response = self.session.get(search_url, headers=self.headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    
                    # 링크 기반 파싱
                    for a_tag in soup.find_all('a', href=True):
                        href = a_tag.get('href', '')
                        if '/recruit/' in href and href != '/recruit/':
                            job_data = self._extract_from_link(a_tag, keyword)
                            if job_data and job_data['id'] not in [r['id'] for r in results]:
                                results.append(job_data)
                
                time.sleep(random.uniform(0.5, 1))
                
            except Exception as e:
                continue
        
        print(f"  Jasoseol: Total {len(results)} jobs collected")
        return results
    
    def _parse_item(self, item, keywords):
        """개별 아이템 파싱"""
        try:
            # 링크 찾기
            link_tag = item.find('a', href=True)
            if not link_tag:
                return None
            
            href = link_tag.get('href', '')
            if not href or '/recruit/' not in href:
                return None
            
            if not href.startswith('http'):
                href = self.BASE_URL + href
            
            # 제목
            title = ""
            title_candidates = [
                item.find(['h2', 'h3', 'h4']),
                item.find(class_=lambda x: x and ('title' in x.lower() or 'name' in x.lower())),
                link_tag
            ]
            for candidate in title_candidates:
                if candidate:
                    title = candidate.get_text(strip=True)
                    if len(title) > 5:
                        break
            
            if not title or len(title) < 3:
                return None
            
            # 회사명
            company = ""
            company_tag = item.find(class_=lambda x: x and ('company' in x.lower() or 'corp' in x.lower()))
            if company_tag:
                company = company_tag.get_text(strip=True)
            
            # 마감일
            deadline = ""
            date_tag = item.find(class_=lambda x: x and ('date' in x.lower() or 'deadline' in x.lower() or 'period' in x.lower()))
            if date_tag:
                deadline = date_tag.get_text(strip=True)
            
            # ID 추출
            job_id = re.search(r'/recruit/(\d+)', href)
            job_id = job_id.group(1) if job_id else str(hash(href))
            
            # 키워드 매칭
            matched_keyword = ""
            title_lower = title.lower()
            for kw in keywords:
                if kw.lower() in title_lower:
                    matched_keyword = kw
                    break
            
            return {
                "id": f"jasoseol_{job_id}",
                "site": "Jasoseol",
                "title": title[:100],
                "company": company or "자소설닷컴",
                "link": href,
                "deadline": deadline,
                "hidden_keyword": matched_keyword or keywords[0] if keywords else ""
            }
            
        except:
            return None
    
    def _parse_links(self, soup, keywords):
        """링크 기반 파싱 (폴백)"""
        results = []
        seen_ids = set()
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href', '')
            
            # /recruit/숫자 패턴 찾기
            match = re.search(r'/recruit/(\d+)', href)
            if not match:
                continue
            
            job_id = match.group(1)
            if job_id in seen_ids:
                continue
            seen_ids.add(job_id)
            
            # 제목 추출
            title = a_tag.get_text(strip=True)
            if len(title) < 5:
                # 부모 요소에서 찾기
                parent = a_tag.find_parent(['div', 'li', 'article'])
                if parent:
                    title = parent.get_text(strip=True)[:100]
            
            if len(title) < 5:
                continue
            
            full_link = href if href.startswith('http') else self.BASE_URL + href
            
            # 키워드 매칭
            matched_keyword = ""
            title_lower = title.lower()
            for kw in keywords:
                if kw.lower() in title_lower:
                    matched_keyword = kw
                    break
            
            results.append({
                "id": f"jasoseol_{job_id}",
                "site": "Jasoseol",
                "title": title[:100],
                "company": "자소설닷컴",
                "link": full_link,
                "deadline": "",
                "hidden_keyword": matched_keyword or keywords[0] if keywords else ""
            })
        
        return results
    
    def _extract_from_link(self, a_tag, keyword):
        """단일 링크에서 정보 추출"""
        try:
            href = a_tag.get('href', '')
            match = re.search(r'/recruit/(\d+)', href)
            if not match:
                return None
            
            job_id = match.group(1)
            title = a_tag.get_text(strip=True)
            
            if len(title) < 5:
                return None
            
            full_link = href if href.startswith('http') else self.BASE_URL + href
            
            return {
                "id": f"jasoseol_{job_id}",
                "site": "Jasoseol",
                "title": title[:100],
                "company": "자소설닷컴",
                "link": full_link,
                "deadline": "",
                "hidden_keyword": keyword
            }
        except:
            return None

    def get_details(self, url):
        return ""
