"""검색어는 발견 경로일 뿐이며, 데이터 직군은 제목과 실제 JD로 판별한다."""

import re
import unicodedata

from src.config import Config


LEGACY_DATA_KEYWORDS = {
    "데이터 분석", "Data Analyst", "데이터 엔지니어", "Data Scientist",
    "머신러닝", "AI", "AI AGENT",
}


def normalize(text):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text or "").casefold()).strip()


def contains(text, phrase):
    # AI가 retail에, SQL이 NoSQL에 매칭되지 않도록 영문 단어 경계를 확인한다.
    pattern = re.escape(normalize(phrase)).replace(r"\ ", r"[\s\-/]*")
    left_boundary = r"(?<![a-z0-9가-힣])" if re.match(r"[가-힣]", phrase) else r"(?<![a-z0-9])"
    right_boundary = r"(?![a-z0-9가-힣])" if phrase == "마테크" else r"(?![a-z0-9])"
    return bool(re.search(left_boundary + pattern + right_boundary, normalize(text)))


ROLE_ALIASES = {
    "Data Analyst": ("Data Analyst", "데이터 분석", "데이터 애널리스트", "데이터 애널리틱스"),
    "Product Data Analyst": ("Product Data Analyst", "Product Analyst", "프로덕트 데이터 분석", "프로덕트 분석"),
    "Business Data Analyst": ("Business Data Analyst", "비즈니스 데이터 분석", "비즈니스 분석가"),
    "Data Analytics Engineer": ("Data Analytics Engineer", "데이터 애널리틱스 엔지니어"),
    "Analytics Engineer": ("Analytics Engineer", "애널리틱스 엔지니어", "분석 엔지니어"),
    "Marketing Engineer": ("Marketing Engineer", "마케팅 엔지니어"),
    "MarTech": ("MarTech", "Marketing Technology", "마테크", "마케팅 테크놀로지"),
    "CRM Data Analyst": ("CRM Data Analyst", "CRM Analyst", "CRM 데이터 분석", "CRM 분석"),
    "CDP": ("CDP", "Customer Data Platform", "고객 데이터 플랫폼"),
    "Customer Data Analyst": ("Customer Data Analyst", "Customer Analyst", "고객 데이터 분석", "고객 분석"),
}

# 동의어/반복 표현은 하나로 센다. 회사명, 검색어, AI 요약은 평가에 사용하지 않는다.
JD_SIGNALS = {
    "SQL": ("SQL", "MySQL", "PostgreSQL", "T-SQL", "BigQuery"),
    "Python": ("Python", "파이썬"),
    "Data Modeling": ("Data Modeling", "Data Modelling", "데이터 모델링", "데이터 모델 설계"),
    "Pipeline": ("Pipeline", "Pipelines", "파이프라인", "ETL", "ELT"),
    "dbt": ("dbt",),
    "Airflow": ("Airflow", "에어플로우"),
    "GA4 / Event Tracking": ("GA4", "Google Analytics 4", "Event Tracking", "이벤트 트래킹", "이벤트 추적", "이벤트 설계"),
    "Experiment": ("Experiment", "Experiments", "Experimentation", "A/B Test", "A/B Testing", "AB Test", "실험 설계", "실험 분석", "실험"),
    "Funnel": ("Funnel", "Funnels", "퍼널"),
    "Customer Data": ("Customer Data", "고객 데이터", "고객 행동 데이터"),
    "Automation": ("Automation", "Automate", "Automated", "자동화"),
    "LLM / AI Agent": ("LLM", "LLMs", "Large Language Model", "AI Agent", "AI Agents", "AI 에이전트", "대규모 언어 모델"),
}

DATA_DUTIES = (
    "데이터 분석", "데이터 모델링", "고객 데이터", "고객 행동 분석",
    "마케팅 자동화", "지표 설계", "퍼널 분석",
    "data analysis", "data analytics", "analytics engineering",
    "customer data", "marketing automation", "funnel analysis",
)

# 키워드가 들어간 교육 광고/라벨링/다른 직군을 데이터 공고로 올리지 않는다.
EXCLUDED_TITLES = (
    r"(?:교육생|수강생|연수생|훈련생)\s*(?:모집|채용)",
    r"부트\s*캠프|boot\s*camp|취업\s*연계\s*과정|국비\s*(?:무료|지원|교육)",
    r"데이터\s*(?:라벨링|라벨러|입력)|data\s*(?:labeling|labelling|entry)|어노테이터",
    r"(?:ui\s*[/·&-]?\s*ux|ux\s*[/·&-]?\s*ui)\s*디자이너|ui/ux\s*designer",
    r"상담원|텔레마케터|customer\s*(?:support|service)\s*(?:agent|representative)",
)


def matched_roles(text):
    return [role for role, aliases in ROLE_ALIASES.items() if any(contains(text, alias) for alias in aliases)]


def search_category(job):
    """이전 저장 데이터도 재평가할 수 있도록 옛 검색어를 인식한다."""
    keyword = normalize(job.get("hidden_keyword"))
    for category, keywords in Config.KEYWORDS.items():
        if keyword in {normalize(kw) for kw in keywords}:
            return category
    if keyword in {normalize(kw) for kw in LEGACY_DATA_KEYWORDS}:
        return "Data"
    return "Other"


def is_data_candidate(job):
    return job.get("category") == "Data" or search_category(job) == "Data" or bool(matched_roles(job.get("title", "")))


def evaluate_data_job(job):
    title = job.get("title", "")
    description = job.get("description", "").strip()
    title_roles = matched_roles(title)
    jd_roles = matched_roles(description)
    signals = [name for name, aliases in JD_SIGNALS.items() if any(contains(description, alias) for alias in aliases)]
    excluded = any(re.search(pattern, normalize(title)) for pattern in EXCLUDED_TITLES)
    # 회사 소개에 AI/고객 데이터가 있더라도 영업 포지션은 데이터 직군이 아니다.
    if not title_roles and re.search(r'세일즈|(?:b2b\s*)?영업|\bsales\b', normalize(title)):
        excluded = True
    # CDP는 환경 공시 등에도 쓰인다. 플랫폼/고객 데이터 업무가 확인되어야 한다.
    cdp_context = any(
        contains(title + " " + description, phrase)
        for phrase in ("Customer Data", "고객 데이터", "마케팅", "marketing", "CRM", "데이터 플랫폼")
    )
    has_data_duties = (bool(set(jd_roles) - {'CDP'}) or ('CDP' in jd_roles and cdp_context)
                       or any(contains(description, duty) for duty in DATA_DUTIES))
    ambiguous_cdp = title_roles == ["CDP"] and not cdp_context
    title_matches = bool(title_roles) and not ambiguous_cdp
    jd_matches = has_data_duties and len(signals) >= Config.DATA_MIN_JD_SIGNALS
    accepted = not excluded and (title_matches or jd_matches)
    return {
        "matched": accepted,
        "score": len(signals),
        "matched_keywords": signals,
        "matched_roles": list(dict.fromkeys(title_roles + jd_roles)),
        "jd_status": "available" if description else "unavailable",
        "reason": (
            "제외 대상 공고" if excluded else
            "관련 직무/JD 확인" if accepted and description else
            "직무명 일치 · JD 확인 필요" if accepted else
            "관련 직무/JD 근거 부족"
        ),
    }


def get_job_category(job):
    if job.get("category") in Config.KEYWORDS:
        return job["category"]
    if is_data_candidate(job):
        return "Data" if evaluate_data_job(job)["matched"] else "Other"
    return search_category(job)
