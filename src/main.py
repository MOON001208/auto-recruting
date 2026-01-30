import sys
import os

# Ensure we can import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.scraper.manager import ScraperManager
from src.logic.data_manager import DataManager
from src.logic.deadline import DeadlineChecker
from src.logic.ai_agent import AIAgent
from src.notifier import Notifier
from src.config import Config

def main():
    print("Starting Job Scout Pipeline...")
    
    # 1. Setup
    data_manager = DataManager(Config.DATA_FILE)
    scraper_manager = ScraperManager()
    ai_agent = AIAgent()
    notifier = Notifier()
    
    # 2. Load Old Data
    existing_jobs = data_manager.load_existing_jobs()
    print(f"Loaded {len(existing_jobs)} existing jobs.")
    
    # 3. Scrape
    scraped_jobs = scraper_manager.run_all()
    print(f"Scraped {len(scraped_jobs)} jobs.")
    
    # 4. Filter New
    new_jobs = data_manager.filter_new_jobs(scraped_jobs, existing_jobs)
    print(f"Found {len(new_jobs)} new jobs.")
    
    # 5. AI Analysis (Only for new jobs to save cost/time)
    for i, job in enumerate(new_jobs):
        print(f"Analyzing {i+1}/{len(new_jobs)}: {job['title']}")
        # Get Full Text (Scrapers need to implement get_details properly)
        # For MVP, we might skip full text if scraper.get_details is empty
        # or just pass title + company for a "Initial Strategy"
        
        # NOTE: Ideally we call scraper.get_details(job['link']) here
        # But for speed in this demo, we might just analyze based on Title
        job['ai_analysis'] = ai_agent.analyze_job(job['title'], job['title']) 
        
    # 6. Merge & Save
    all_jobs = data_manager.merge_jobs(existing_jobs, new_jobs)
    # Check deadlines on ALL jobs (even old ones)
    deadline_jobs = DeadlineChecker.get_deadline_day_jobs(all_jobs)
    
    # Sort: Deadline today first, then Newest scraped
    all_jobs.sort(key=lambda x: (x.get('deadline') != 'Today', x.get('scraped_at')), reverse=True)
    
    data_manager.save_jobs(all_jobs)
    print("Data saved.")
    
    # 7. Notify
    # GitHub Pages URL
    repo_name = os.getenv("GITHUB_REPOSITORY", "username/repo")
    page_url = f"https://{repo_name.split('/')[0]}.github.io/{repo_name.split('/')[1]}"
    
    # [TEST MODE] Force send email even if no new jobs
    if len(new_jobs) == 0 and len(all_jobs) > 0:
        print("📢 [TEST MODE] No new jobs, but sending email with top 5 recent jobs for testing.")
        # 최근 5개를 강제로 new_jobs로 취급
        test_jobs = all_jobs[:5]
        notifier.send_all_alerts(test_jobs, deadline_jobs, page_url)
    elif len(new_jobs) > 0 or len(deadline_jobs) > 0:
        notifier.send_all_alerts(new_jobs, deadline_jobs, page_url)
    else:
        print("No new jobs and no deadlines. Skipping notification.")
    
if __name__ == "__main__":
    main()
