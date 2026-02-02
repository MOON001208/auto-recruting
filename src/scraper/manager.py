from src.config import Config
from src.scraper.saramin import SaraminScraper
from src.scraper.jobkorea import JobKoreaScraper
from src.scraper.linkareer import LinkareerScraper
from src.scraper.incruit import IncruitScraper
from src.scraper.wanted import WantedScraper

class ScraperManager:
    def __init__(self):
        self.scrapers = [
            SaraminScraper(),      # 사람인
            JobKoreaScraper(),     # 잡코리아
            LinkareerScraper(),    # 링커리어
            IncruitScraper(),      # 인크루트
            WantedScraper()        # 원티드
        ]

    def run_all(self):
        all_jobs = []

        # 모든 카테고리의 키워드 수집
        targets = []
        for category, keywords in Config.KEYWORDS.items():
            targets.extend(keywords)

        # 중복 키워드 제거
        targets = list(set(targets))

        print(f"🔍 Starting scrape for {len(targets)} keywords across {len(self.scrapers)} sites...")
        print(f"📍 Sites: 사람인, 잡코리아, 링커리어, 원티드")
        
        for scraper in self.scrapers:
            scraper_name = scraper.__class__.__name__
            try:
                print(f"\n▶ Running {scraper_name}...")
                jobs = scraper.search(targets)
                print(f"  ✅ {scraper_name}: {len(jobs)}개 공고 수집")
                all_jobs.extend(jobs)
            except Exception as e:
                print(f"  ❌ {scraper_name} failed: {e}")
        
        print(f"\n📊 Total collected: {len(all_jobs)} jobs")
        return all_jobs
