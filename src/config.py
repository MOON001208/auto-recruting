import os

class Config:
    # 직무 검색어와 JD 평가 키워드는 분리한다. AI/SQL 등은 단독 검색하지 않는다.
    KEYWORDS = {
        "Data": [
            "Data Analyst", "Product Data Analyst", "Business Data Analyst",
            "Data Analytics Engineer", "Analytics Engineer", "Marketing Engineer",
            "MarTech", "CRM Data Analyst", "CDP", "Customer Data Analyst",
            "데이터 분석", "프로덕트 데이터 분석", "비즈니스 데이터 분석",
            "애널리틱스 엔지니어", "마케팅 엔지니어", "마테크",
            "CRM 데이터 분석", "고객 데이터 분석", "고객 데이터 플랫폼",
        ],
        "Accounting": ["회계", "재무", "세무", "결산"],
        "HR": ["인사", "HRM", "HRD", "총무", "채용"]
    }

    # 제목이 포괄적일 때는 JD의 관련 업무 + 서로 다른 키워드 2개 이상 필요.
    DATA_MIN_JD_SIGNALS = 2
    # 상세 페이지 장애가 전체 자동화를 지연시키지 않도록 실행당 조회를 제한.
    DATA_DETAIL_LIMIT = 100
    DATA_DETAIL_BUDGET_SECONDS = 300
    # 마감일이 없는 데이터 공고는 검색에서 마지막으로 확인된 뒤 60일까지만 유지.
    DATA_STALE_DAYS = 60
    
    # Secrets (Environment Variables)
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
    
    # 카테고리별 이메일 수신자 설정
    # 각 카테고리별로 다른 사람에게 보낼 수 있음
    GMAIL_RECIPIENTS = {
        "Data": os.getenv("GMAIL_TO_DATA"),           # 데이터 직군 공고 받을 사람
        "Accounting": os.getenv("GMAIL_TO_ACCOUNTING"), # 회계 직군 공고 받을 사람  
        "HR": os.getenv("GMAIL_TO_HR"),               # 인사 직군 공고 받을 사람
        "All": os.getenv("GMAIL_TO")                  # 전체 공고 받을 사람 (기존 호환)
    }
    
    # Paths
    DATA_FILE = "docs/jobs.json"
    STATUS_FILE = "docs/scraper_status.json"
