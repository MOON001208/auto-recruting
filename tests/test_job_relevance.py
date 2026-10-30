import unittest
from unittest.mock import Mock, patch

from src.config import Config
from src.logic.job_relevance import contains, evaluate_data_job, get_job_category
from src.scraper.manager import ScraperManager


def job(title, description='', keyword='Data Analyst', **extra):
    return dict(id='wanted_1', site='Wanted', title=title, description=description,
                hidden_keyword=keyword, company='Sample', link='https://www.wanted.co.kr/wd/1',
                deadline='', **extra)


class RelevanceTests(unittest.TestCase):
    def test_all_requested_roles(self):
        for title in Config.KEYWORDS['Data']:
            with self.subTest(title=title):
                self.assertTrue(evaluate_data_job(job(title, '고객 데이터 분석에 SQL과 Python을 사용합니다.'))['matched'])

    def test_generic_title_can_be_accepted_from_jd(self):
        result = evaluate_data_job(job('2026년 신입 공개채용', '프로덕트 데이터 분석, SQL, Python, Funnel, A/B Testing'))
        self.assertTrue(result['matched'])
        self.assertEqual(result['score'], 4)

    def test_keyword_and_company_do_not_count_as_evidence(self):
        record = job('생산관리 사무직 채용', 'Excel로 생산 일정 관리')
        record['company'] = 'Data Analyst SQL Python dbt'
        record['ai_analysis'] = {'summary': '데이터 분석 SQL Python'}
        self.assertFalse(evaluate_data_job(record)['matched'])
        self.assertEqual(evaluate_data_job(record)['score'], 0)

    def test_company_name_substring_is_not_martech(self):
        record = job('[신입] 경영지원부 사무보조 모집 - 타코마테크놀러지')
        self.assertFalse(evaluate_data_job(record)['matched'])
        self.assertFalse(contains('마테크놀러지', '마테크'))
        self.assertTrue(contains('마테크 개발자', '마테크'))

    def test_related_title_without_jd_is_marked_unverified(self):
        result = evaluate_data_job(job('Product Data Analyst'))
        self.assertTrue(result['matched'])
        self.assertEqual(result['jd_status'], 'unavailable')
        self.assertEqual(result['score'], 0)

    def test_generic_title_requires_multiple_jd_signals(self):
        self.assertFalse(evaluate_data_job(job('신입 공채', '고객 데이터 담당'))['matched'])
        self.assertTrue(evaluate_data_job(job('신입 공채', '고객 데이터 분석 및 SQL 쿼리 작성'))['matched'])

    def test_tools_without_related_duties_do_not_make_data_role(self):
        self.assertFalse(evaluate_data_job(job('백엔드 개발자', 'Python SQL Pipeline Automation'))['matched'])
        self.assertFalse(evaluate_data_job(job('AI Research Scientist', 'Python LLM AI Agent'))['matched'])
        self.assertFalse(evaluate_data_job(job('B2B 세일즈 매니저', '고객 데이터 기반 영업, LLM 기반 제품 판매'))['matched'])
        self.assertTrue(evaluate_data_job(job('영업 데이터 분석가', 'SQL로 고객 데이터를 분석합니다'))['matched'])

    def test_ambiguous_cdp(self):
        self.assertFalse(evaluate_data_job(job('CDP 기후변화 공시 담당', '환경경영 보고서 작성'))['matched'])
        self.assertFalse(evaluate_data_job(job('CDP 담당자'))['matched'])
        self.assertFalse(evaluate_data_job(job('CDP 공시 담당', 'CDP 환경 공시 보고서 SQL Python Automation'))['matched'])
        self.assertTrue(evaluate_data_job(job('CDP 개발자', '고객 데이터 플랫폼을 개발합니다. SQL Python'))['matched'])

    def test_noise_titles_even_with_good_looking_keywords(self):
        titles = ['데이터 분석 부트캠프 교육생 모집', 'Data Analyst 수강생 모집',
                  '데이터 라벨링 신입채용', '데이터 분석력을 겸비한 UI/UX디자이너 채용',
                  '고객 데이터 관리 상담원 채용']
        for title in titles:
            with self.subTest(title=title):
                self.assertFalse(evaluate_data_job(job(title, '고객 데이터 분석 SQL Python dbt'))['matched'])

    def test_signals_count_families_once_and_ignore_title(self):
        result = evaluate_data_job(job('Data Analyst Airflow', 'SQL sql MySQL PostgreSQL Python 파이썬 GA4 Event Tracking LLM AI Agent'))
        self.assertEqual(result['matched_keywords'], ['SQL', 'Python', 'GA4 / Event Tracking', 'LLM / AI Agent'])
        self.assertEqual(result['score'], 4)

    def test_word_boundaries_and_spelling(self):
        self.assertFalse(contains('retail', 'AI'))
        self.assertFalse(contains('NoSQL', 'SQL'))
        self.assertFalse(contains('CDP123', 'CDP'))
        self.assertTrue(contains('데이터분석 담당', '데이터 분석'))
        self.assertTrue(contains('PRODUCT-DATA ANALYST', 'Product Data Analyst'))
        self.assertTrue(contains('ＳＱＬ', 'SQL'))

    def test_more_jd_matches_rank_higher(self):
        low = evaluate_data_job(job('Data Analyst', 'SQL'))
        high = evaluate_data_job(job('Data Analyst', 'SQL Python dbt Airflow'))
        self.assertGreater(high['score'], low['score'])

    def test_legacy_unrelated_data_is_not_classified_by_keyword(self):
        self.assertEqual(get_job_category(job('AI 콘텐츠 제작 인턴', keyword='AI')), 'Other')
        self.assertEqual(get_job_category(job('회계 담당자', keyword='회계')), 'Accounting')
        self.assertEqual(get_job_category(job('인사 담당자', keyword='인사')), 'HR')


class ReviewTests(unittest.TestCase):
    def test_filters_existing_and_new_jobs_and_reuses_jd(self):
        manager = ScraperManager()
        scraper = manager.scrapers[-1]
        scraper.get_details = Mock(return_value='Product Data Analyst SQL Python dbt')
        source = job('신입 공채')
        first = manager.review_jobs([source, source])
        second = manager.review_jobs([source])
        self.assertEqual(first[0]['category'], 'Data')
        self.assertEqual(second[0]['data_relevance']['score'], 3)
        self.assertEqual(len(first), 1)
        self.assertNotIn('category', source)
        scraper.get_details.assert_called_once()

    def test_keeps_other_categories_without_detail_requests(self):
        manager = ScraperManager()
        manager._get_details = Mock(side_effect=AssertionError('Unexpected JD request'))
        result = manager.review_jobs([job('회계 신입', keyword='회계'), dict(job('인사 신입', keyword='인사'), id='wanted_2')])
        self.assertEqual([j['category'] for j in result], ['Accounting', 'HR'])

    def test_old_broad_search_is_rechecked(self):
        manager = ScraperManager()
        jobs = [job('AI 번역 평가자', keyword='AI'), dict(job('데이터분석 담당자'), id='wanted_2')]
        result = manager.review_jobs(jobs, fetch_details=False)
        self.assertEqual([j['title'] for j in result], ['데이터분석 담당자'])

    def test_detail_budget_does_not_promote_generic_title(self):
        manager = ScraperManager()
        with patch.object(Config, 'DATA_DETAIL_LIMIT', 0):
            result = manager.review_jobs([job('신입 공채')])
        self.assertEqual(result, [])

    def test_detail_failure_keeps_only_clear_role(self):
        manager = ScraperManager()
        manager.scrapers[-1].get_details = Mock(side_effect=RuntimeError('offline'))
        result = manager.review_jobs([job('Data Analyst')])
        self.assertEqual(result[0]['data_relevance']['jd_status'], 'unavailable')

    def test_detail_requests_are_shared_across_sites(self):
        manager = ScraperManager()
        manager.scrapers[0].get_details = Mock(return_value='SQL Python')
        manager.scrapers[-1].get_details = Mock(return_value='SQL dbt')
        records = [dict(job('Data Analyst'), id=f'saramin_{i}', site='Saramin') for i in range(3)]
        records.append(job('Data Analyst'))
        with patch.object(Config, 'DATA_DETAIL_LIMIT', 2):
            reviewed = manager.review_jobs(records)
        self.assertEqual(reviewed[-1]['data_relevance']['score'], 2)
        manager.scrapers[0].get_details.assert_called_once()
        manager.scrapers[-1].get_details.assert_called_once()


if __name__ == '__main__':
    unittest.main()
