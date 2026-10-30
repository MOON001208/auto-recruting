import random
import time

import requests

from src.scraper.details import fetch_description
from src.scraper.health import SearchHealth


class WantedScraper(SearchHealth):
    # v4/jobs는 keyword를 무시하므로 실제 통합검색 API를 사용한다.
    SEARCH_URL = 'https://www.wanted.co.kr/api/v3/search'

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8',
            'Referer': 'https://www.wanted.co.kr/',
            'wanted-user-country': 'KR', 'wanted-user-language': 'ko',
        }
        self.session = requests.Session()
        self.reset_health()

    def search(self, keywords):
        self.reset_health()
        results, seen = [], set()
        for keyword in keywords:
            try:
                response = self.session.get(
                    self.SEARCH_URL, params={'query': keyword, 'tab': 'position', 'country': 'kr'},
                    headers=self.headers, timeout=10)
                if response.status_code != 200:
                    self.search_failed(f'HTTP {response.status_code}')
                    print(f'Wanted search: HTTP {response.status_code}')
                else:
                    data = response.json().get('data', {})
                    jobs = data.get('jobs', data.get('positions'))
                    if isinstance(jobs, dict):
                        jobs = jobs.get('data')
                    if not isinstance(jobs, list):
                        raise ValueError('검색 응답에서 공고 목록을 찾을 수 없음')
                    self.search_succeeded()
                    for item in jobs:
                        job_id = item.get('id')
                        title = item.get('position') or item.get('title')
                        if not job_id or not title or job_id in seen:
                            continue
                        seen.add(job_id)
                        company = item.get('company_name') or (item.get('company') or {}).get('name', '')
                        results.append({'id': f'wanted_{job_id}', 'site': 'Wanted', 'title': title,
                                        'company': company, 'link': f'https://www.wanted.co.kr/wd/{job_id}',
                                        'deadline': (item.get('due_time') or '')[:10], 'hidden_keyword': keyword})
            except (requests.RequestException, ValueError, TypeError, AttributeError) as exc:
                self.search_failed(type(exc).__name__)
                print(f'Wanted search failed: {type(exc).__name__}')
            if self.should_stop():
                print('Wanted: 연속 실패로 나머지 검색을 중단합니다.')
                break
            time.sleep(random.uniform(0.5, 1))
        return results

    def get_details(self, url):
        return fetch_description(url, 'Wanted', self.headers, self.session)
