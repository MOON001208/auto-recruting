import json
import os
from datetime import datetime

class DataManager:
    def __init__(self, file_path):
        self.file_path = file_path
        
    def load_existing_jobs(self):
        if not os.path.exists(self.file_path):
            return []
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
            
    def save_jobs(self, jobs):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)
            
    def filter_new_jobs(self, scraped_jobs, existing_jobs):
        seen_ids = set(job['id'] for job in existing_jobs)
        new_jobs = []
        
        # 중복 검사를 위한 기존 공고들의 정규화된 데이터 미리 생성 (속도 최적화)
        existing_signatures = []
        for job in existing_jobs:
            existing_signatures.append({
                'company': self._normalize_text(job['company']),
                'title': self._normalize_text(job['title']),
                'original': job
            })
            
        print(f"Comparing {len(scraped_jobs)} scraped jobs against {len(existing_jobs)} existing jobs...")
        
        for job in scraped_jobs:
            if job['id'] in seen_ids:
                continue
                
            # ID는 다르지만 내용이 같은 "교차 중복" 확인 (다른 사이트 동일 공고)
            is_duplicate = False
            current_company = self._normalize_text(job['company'])
            current_title = self._normalize_text(job['title'])
            
            for existing in existing_signatures:
                # 1. 회사명이 다르면 바로 패스 (가장 강력한 필터)
                if current_company != existing['company']:
                    continue
                
                # 2. 회사명이 같으면 제목 유사도 검사
                # 제목이 서로 포함관계이거나, 70% 이상 유사하면 중복으로 간주
                if current_title in existing['title'] or existing['title'] in current_title:
                   is_duplicate = True
                   # print(f"Duplicate found (Substring): {job['title']} == {existing['original']['title']}")
                   break
                   
                # difflib는 느릴 수 있으므로 텍스트가 짧을 때만 정밀 비교
                if self._check_similarity(current_title, existing['title']):
                    is_duplicate = True
                    # print(f"Duplicate found (Similarity): {job['title']} == {existing['original']['title']}")
                    break
            
            if not is_duplicate:
                job['scraped_at'] = datetime.now().isoformat()
                job['is_new'] = True
                
                # 방금 추가된 것도 중복 비교군에 추가 (이번 실행 내에서의 중복 방지)
                existing_signatures.append({
                    'company': current_company,
                    'title': current_title,
                    'original': job
                })
                seen_ids.add(job['id']) # ID도 등록
                new_jobs.append(job)
                
        return new_jobs

    def _normalize_text(self, text):
        """특수문자, 공백, (주) 등을 제거하여 비교하기 쉽게 만듦"""
        import re
        if not text: return ""
        # 소문자 변환
        text = text.lower()
        # (주), 주식회사 등 흔한 법인명 제거
        text = re.sub(r'\(주\)|주식회사|\(유\)|inc\.|co\.|ltd\.', '', text)
        # 괄호 안의 내용 제거 (예: [판교], (채용시마감) 등 지역/상태 정보 제거)
        text = re.sub(r'\[.*?\]|\(.*?\)', '', text)
        # 특수문자 및 공백 제거 (숫자와 한글/영어만 남김)
        text = re.sub(r'[^a-zA-Z0-9가-힣]', '', text)
        return text

    def _check_similarity(self, s1, s2):
        from difflib import SequenceMatcher
        # 너무 짧은 제목은 비교하지 않음
        if len(s1) < 5 or len(s2) < 5:
            return False
        return SequenceMatcher(None, s1, s2).ratio() > 0.7  # 70% 이상 유사하면 중복

    def merge_jobs(self, existing_jobs, new_jobs):
        # Create a map for easy updates
        job_map = {job['id']: job for job in existing_jobs}
        
        # Mark old jobs as not new
        for job in job_map.values():
            job['is_new'] = False
            
        # Add or update new jobs
        for job in new_jobs:
            job_map[job['id']] = job
            
        return list(job_map.values())
