from datetime import datetime, timedelta
import re

class DeadlineChecker:
    @staticmethod
    def is_deadline_today(deadline_str):
        # Handle various formats: "2024.01.30", "01/30", "~ 01/30(화)"
        try:
            today = datetime.now()
            
            # Clean string
            clean_date = re.sub(r'[^\d.]', '', deadline_str) # Keep digits and dots
            
            # Cases
            # 1. YYYY.MM.DD
            # 2. MM.DD (Assume current year)
            
            parsed_date = None
            
            if clean_date.count('.') == 2:
                parsed_date = datetime.strptime(clean_date, "%Y.%m.%d")
            elif clean_date.count('.') == 1:
                parsed_date = datetime.strptime(clean_date, "%m.%d")
                parsed_date = parsed_date.replace(year=today.year)
                # Edge case: Jan deadline scraped in Dec logic omitted for simplicity
                
            if parsed_date:
                return parsed_date.date() == today.date()
                
            return False
        except:
            return False
    
    @staticmethod
    def is_deadline_passed(deadline_str):
        """마감일이 지났는지 확인 (오늘 이전인 경우 True)"""
        try:
            today = datetime.now()
            
            # Clean string
            clean_date = re.sub(r'[^\d.]', '', deadline_str)
            
            # 날짜가 추출되지 않으면 (상시채용, PENDING 등) 유지
            if not clean_date:
                return False
            
            parsed_date = None
            
            if clean_date.count('.') == 2:
                parsed_date = datetime.strptime(clean_date, "%Y.%m.%d")
            elif clean_date.count('.') == 1:
                parsed_date = datetime.strptime(clean_date, "%m.%d")
                parsed_date = parsed_date.replace(year=today.year)
                
            if parsed_date:
                # 오늘보다 이전이면 True (마감 지남)
                return parsed_date.date() < today.date()
                
            return False
        except:
            return False
            
    @staticmethod
    def get_deadline_day_jobs(jobs):
        return [job for job in jobs if DeadlineChecker.is_deadline_today(job.get('deadline', ''))]
    
    @staticmethod
    def filter_active_jobs(jobs):
        """기한이 지나지 않은 공고만 필터링"""
        active_jobs = []
        removed_count = 0
        
        for job in jobs:
            deadline = job.get('deadline', '')
            
            # 마감일이 지났는지 확인
            if DeadlineChecker.is_deadline_passed(deadline):
                removed_count += 1
                print(f"  🗑️  Removing expired job: {job['title']} (Deadline: {deadline})")
            else:
                active_jobs.append(job)
        
        if removed_count > 0:
            print(f"✅ Removed {removed_count} expired job(s)")
        
        return active_jobs
