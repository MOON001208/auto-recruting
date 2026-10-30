import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, patch
import requests

from src.logic.data_manager import DataManager
from src.logic.deadline import DeadlineChecker
from src.scraper.manager import ScraperManager
from src.scraper.wanted import WantedScraper
from src.scraper.jobkorea import JobKoreaScraper
from src.scraper.incruit import IncruitScraper


class FreshnessTests(unittest.TestCase):
    def test_unconfirmed_old_data_expires_but_recent_or_dated_does_not(self):
        now = datetime(2026, 10, 30, tzinfo=timezone.utc)
        job = {'id': '1', 'category': 'Data', 'deadline': '',
               'scraped_at': (now - timedelta(days=90)).isoformat()}
        self.assertTrue(DeadlineChecker.is_stale_data_job(job, now))
        self.assertFalse(DeadlineChecker.is_stale_data_job(dict(job, last_seen_at=now.isoformat()), now))
        self.assertFalse(DeadlineChecker.is_stale_data_job(dict(job, deadline='2099-11-30'), now))
        self.assertFalse(DeadlineChecker.is_stale_data_job(dict(job, category='HR'), now))

    def test_rediscovered_job_is_refreshed_before_expiry(self):
        old = {'id': '1', 'category': 'Data', 'deadline': '', 'scraped_at': '2020-01-01T00:00:00'}
        DataManager('unused').refresh_seen_jobs([old], [{'id': '1', 'deadline': '2099-11-30'}])
        self.assertEqual(old['deadline'], '2099-11-30')
        self.assertFalse(DeadlineChecker.is_stale_data_job(old))

    def test_unknown_company_does_not_collapse_different_postings(self):
        manager = DataManager('unused')
        old = {'id': '1', 'company': '', 'title': '데이터 분석가 모집'}
        new = {'id': '2', 'company': '', 'title': '데이터 분석가 모집', 'category': 'Data'}
        self.assertEqual(len(manager.filter_new_jobs([new], [old])), 1)


class TimeoutTests(unittest.TestCase):
    def test_job_sites_stop_after_repeated_timeouts(self):
        for cls, module in [(JobKoreaScraper, 'jobkorea'), (IncruitScraper, 'incruit')]:
            with self.subTest(site=module):
                scraper = cls()
                scraper.session.get = Mock(side_effect=requests.Timeout())
                with patch(f'src.scraper.{module}.time.sleep'):
                    self.assertEqual(scraper.search(['a', 'b', 'c', 'd']), [])
                self.assertEqual(scraper.session.get.call_count, 3)
                self.assertEqual(scraper.failures, 3)


class WantedSearchTests(unittest.TestCase):
    def test_uses_search_query_and_actual_jobs_response(self):
        scraper = WantedScraper()
        response = Mock(status_code=200)
        response.json.return_value = {'data': {'jobs': {'data': [
            {'id': 10, 'position': 'Product Data Analyst', 'company_name': 'Test'}]}}}
        scraper.session.get = Mock(return_value=response)
        with patch('src.scraper.wanted.time.sleep'):
            result = scraper.search(['Product Data Analyst'])
        self.assertEqual(result[0]['id'], 'wanted_10')
        self.assertEqual(scraper.session.get.call_args.kwargs['params']['query'], 'Product Data Analyst')
        self.assertEqual(scraper.failures, 0)

    def test_access_denied_is_reported_and_limited(self):
        scraper = WantedScraper()
        scraper.session.get = Mock(return_value=Mock(status_code=403))
        with patch('src.scraper.wanted.time.sleep'):
            self.assertEqual(scraper.search(['a', 'b', 'c', 'd']), [])
        self.assertEqual(scraper.session.get.call_count, 3)
        self.assertEqual(scraper.last_error, 'HTTP 403')

    def test_invalid_search_schema_is_not_treated_as_success(self):
        scraper = WantedScraper()
        response = Mock(status_code=200)
        response.json.return_value = {'data': {'companies': []}}
        scraper.session.get = Mock(return_value=response)
        with patch('src.scraper.wanted.time.sleep'):
            self.assertEqual(scraper.search(['a']), [])
        self.assertEqual(scraper.failures, 1)

    def test_status_distinguishes_failed_source(self):
        scraper = WantedScraper()
        scraper.session.get = Mock(return_value=Mock(status_code=403))
        manager = ScraperManager()
        manager.scrapers = [scraper]
        with patch('src.scraper.wanted.time.sleep'):
            manager.run_all()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'status.json'
            manager.save_status(path)
            status = json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(status['sites']['Wanted']['status'], 'failed')
        self.assertEqual(status['sites']['Wanted']['reason'], 'HTTP 403')


if __name__ == '__main__':
    unittest.main()
