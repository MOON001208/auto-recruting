from datetime import datetime, timedelta, timezone
import re
from src.config import Config

class DeadlineChecker:
    @staticmethod
    def _parse_deadline(deadline_str):
        """
        다양한 마감일 형식을 파싱하여 date 객체로 반환
        지원 형식:
        - 02/14(토) 마감
        - ~ 02/28(토)
        - 2026-02-28
        - 2026.02.28
        - 02.28
        - 내일마감, 오늘마감 등 텍스트
        """
        try:
            today = datetime.now()
            
            # 텍스트 키워드 체크
            # "오늘마감", "내일마감" 텍스트가 그대로 저장되어 있다면
            # 스크래핑 시점에 변환되지 않은 구 데이터임
            # → 이미 지난 것으로 처리 (어제/그저께 날짜 반환)
            if '오늘' in deadline_str or 'today' in deadline_str.lower():
                # 정상 데이터는 "02/02 마감" 형태로 저장됨
                # "오늘마감" 텍스트 그대로면 과거 데이터 → 어제로 처리
                return (today - timedelta(days=1)).date()
            if '내일' in deadline_str or 'tomorrow' in deadline_str.lower():
                # "내일마감" 텍스트 그대로면 과거 데이터 → 오늘로 처리 (이미 지남)
                return today.date()
            
            # 구분자 통일: / 와 - 를 . 으로 변환
            normalized = deadline_str.replace('/', '.').replace('-', '.')
            
            # 숫자와 점만 추출
            clean_date = re.sub(r'[^\d.]', '', normalized)
            
            if not clean_date:
                return None
            
            parsed_date = None
            
            # 형식 판별
            if clean_date.count('.') == 2:
                # YYYY.MM.DD 또는 MM.DD.YY
                parts = clean_date.split('.')
                if len(parts[0]) == 4:  # YYYY.MM.DD
                    parsed_date = datetime.strptime(clean_date, "%Y.%m.%d")
                elif len(parts[0]) == 2:  # MM.DD.YY
                    parsed_date = datetime.strptime(clean_date, "%m.%d.%y")
            elif clean_date.count('.') == 1:
                # MM.DD
                parsed_date = datetime.strptime(clean_date, "%m.%d")
                parsed_date = parsed_date.replace(year=today.year)
            elif len(clean_date) == 8:
                # YYYYMMDD (점 없이 붙어있는 경우)
                parsed_date = datetime.strptime(clean_date, "%Y%m%d")
            elif len(clean_date) == 4:
                # MMDD (점 없이 붙어있는 경우)
                parsed_date = datetime.strptime(clean_date, "%m%d")
                parsed_date = parsed_date.replace(year=today.year)
            
            return parsed_date.date() if parsed_date else None
            
        except:
            return None

    @staticmethod
    def is_deadline_today(deadline_str):
        """마감일이 오늘인지 확인"""
        parsed = DeadlineChecker._parse_deadline(deadline_str)
        if parsed:
            return parsed == datetime.now().date()
        return False
    
    @staticmethod
    def is_deadline_passed(deadline_str):
        """마감일이 지났는지 확인 (오늘 이전인 경우 True)"""
        parsed = DeadlineChecker._parse_deadline(deadline_str)
        if parsed:
            return parsed < datetime.now().date()
        # 날짜가 파싱 안 되면 (상시채용, PENDING 등) 유지
        return False
            
    @staticmethod
    def is_deadline_tomorrow(deadline_str):
        """마감일이 내일인지 확인 (D-1)"""
        parsed = DeadlineChecker._parse_deadline(deadline_str)
        if parsed:
            tomorrow = datetime.now().date() + timedelta(days=1)
            return parsed == tomorrow
        return False

    @staticmethod
    def get_deadline_day_jobs(jobs):
        """오늘 마감인 공고 반환"""
        return [job for job in jobs if DeadlineChecker.is_deadline_today(job.get('deadline', ''))]

    @staticmethod
    def get_upcoming_deadline_jobs(jobs):
        """내일 마감인 공고 반환 (D-1)"""
        return [job for job in jobs if DeadlineChecker.is_deadline_tomorrow(job.get('deadline', ''))]
    
    @staticmethod
    def filter_active_jobs(jobs):
        """기한이 지나지 않은 공고만 필터링"""
        active_jobs = []
        removed_count = 0
        
        for job in jobs:
            deadline = job.get('deadline', '')
            
            # 마감일이 지났는지 확인
            expired = DeadlineChecker.is_deadline_passed(deadline)
            stale = DeadlineChecker.is_stale_data_job(job)
            if expired or stale:
                removed_count += 1
                reason = '마감일 지남' if expired else '장기간 재확인되지 않음'
                print(f"  🗑️  제외 ({reason}): {job['title']} (Deadline: {deadline})")
            else:
                active_jobs.append(job)
        
        if removed_count > 0:
            print(f"✅ Removed {removed_count} expired job(s)")
        
        return active_jobs

    @staticmethod
    def is_stale_data_job(job, now=None):
        """마감일이 없고 장기간 다시 확인되지 않은 데이터 공고를 정리한다."""
        if job.get('category') != 'Data' or DeadlineChecker._parse_deadline(job.get('deadline', '')):
            return False
        last_seen = job.get('last_seen_at') or job.get('scraped_at')
        if not last_seen:
            return False
        try:
            seen = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
            if seen.tzinfo is None:
                seen = seen.replace(tzinfo=timezone.utc)
            current = now or datetime.now(timezone.utc)
            return current - seen > timedelta(days=Config.DATA_STALE_DAYS)
        except (ValueError, TypeError):
            return False
