import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from src import main as pipeline
from src.scraper.manager import ScraperManager
from src.scraper.linkareer import LinkareerScraper
from src.notifier import Notifier


def record(job_id, title, keyword):
    return dict(id=job_id, title=title, company='Example', hidden_keyword=keyword,
                site='Wanted', link='https://www.wanted.co.kr/wd/' + job_id,
                deadline='', scraped_at='2026-09-06T09:00:00', is_new=False)


class PipelineTests(unittest.TestCase):
    def test_review_save_and_notification_inputs_use_same_jobs(self):
        old_data = record('old_bad', 'AI 콘텐츠 제작 인턴', 'AI')
        old_hr = record('old_hr', '인사 신입 담당자', '인사')
        new_data = record('new_good', 'Product Data Analyst', 'Product Data Analyst')
        new_noise = record('new_bad', '데이터 분석 부트캠프 교육생 모집', 'Data Analyst')
        manager = ScraperManager()
        manager.run_all = Mock(return_value=[new_data, new_noise])
        manager.scrapers[-1].get_details = Mock(side_effect=lambda url:
            '고객 데이터 분석 SQL Python dbt Airflow' if url.endswith('new_good') else '')
        old_hr['ai_analysis'] = {'summary': 'old analysis'}
        notifier = Mock()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'jobs.json'
            path.write_text(json.dumps([old_data, old_hr]), encoding='utf-8')
            with (patch.object(pipeline.Config, 'DATA_FILE', str(path)),
                  patch.object(pipeline.Config, 'STATUS_FILE', str(Path(directory) / 'status.json')),
                  patch.object(pipeline, 'ScraperManager', return_value=manager),
                  patch.object(pipeline, 'Notifier', return_value=notifier)):
                pipeline.main()
            saved = json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual({job['id'] for job in saved}, {'old_hr', 'new_good'})
        good = next(job for job in saved if job['id'] == 'new_good')
        self.assertEqual(good['category'], 'Data')
        self.assertEqual(good['data_relevance']['score'], 5)
        self.assertTrue(all('ai_analysis' not in job for job in saved))
        sent_jobs = notifier.send_all_alerts.call_args.args[0]
        self.assertEqual([job['id'] for job in sent_jobs], ['new_good'])
        self.assertTrue(Notifier._is_in_category(None, good, 'Data'))
        self.assertFalse(Notifier._is_in_category(None, old_data, 'Data'))

    def test_linkareer_does_not_label_unmatched_feed_and_searches_all_keywords(self):
        scraper = LinkareerScraper()
        response = Mock(status_code=200)
        response.json.return_value = {'data': {'activities': {'nodes': [
            {'id': '1', 'title': 'Data Analyst'}, {'id': '2', 'title': '편의점 점원 모집'}
        ]}}}
        keywords = ['Data Analyst', 'MarTech', 'CDP', 'Customer Data Analyst']
        with (patch('src.scraper.linkareer.requests.post', return_value=response),
              patch('src.scraper.linkareer.time.sleep'),
              patch.object(scraper, '_fallback_search') as search):
            jobs = scraper.search(keywords)
        self.assertEqual([job['id'] for job in jobs], ['linkareer_1'])
        self.assertEqual(search.call_args.args[0], keywords)

    def test_linkareer_fallback_does_not_truncate_keywords(self):
        scraper = LinkareerScraper()
        response = Mock(status_code=200, text='<html></html>')
        keywords = ['Data Analyst', 'MarTech', 'CDP', 'Customer Data Analyst']
        with (patch('src.scraper.linkareer.requests.get', return_value=response) as get,
              patch('src.scraper.linkareer.time.sleep')):
            scraper._fallback_search(keywords, [])
        self.assertEqual([call.kwargs['params']['filterBy_keyword'] for call in get.call_args_list], keywords)

    def test_dry_run_never_sends_notifications(self):
        manager = ScraperManager()
        manager.run_all = Mock(return_value=[])
        notifier = Mock()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'jobs.json'
            path.write_text('[]', encoding='utf-8')
            with (patch.dict('os.environ', {'JOB_SCOUT_DRY_RUN': 'true'}),
                  patch.object(pipeline.Config, 'DATA_FILE', str(path)),
                  patch.object(pipeline.Config, 'STATUS_FILE', str(Path(directory) / 'status.json')),
                  patch.object(pipeline, 'ScraperManager', return_value=manager),
                  patch.object(pipeline, 'Notifier', return_value=notifier)):
                pipeline.main()
        notifier.send_all_alerts.assert_not_called()


if __name__ == '__main__':
    unittest.main()
