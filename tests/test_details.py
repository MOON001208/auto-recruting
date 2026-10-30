import unittest
import json
from unittest.mock import Mock

import requests

from src.scraper.details import extract_description, fetch_description


class DetailTests(unittest.TestCase):
    def test_jobposting_only_not_company_or_recommended_jobs(self):
        html = '''<nav>SQL Python</nav>
        <script type="application/ld+json">{"@type":"Organization","description":"dbt Airflow"}</script>
        <script type="application/ld+json">{"@graph":[{"@type":"JobPosting","description":"<p>담당업무: SQL 분석</p>"}]}</script>
        <aside>추천 공고 Python LLM</aside>'''
        self.assertEqual(extract_description(html, 'Wanted'), '담당업무: SQL 분석')

    def test_no_whole_page_fallback(self):
        self.assertEqual(extract_description('<nav>SQL</nav><aside>Data Analyst Python</aside>', 'JobKorea'), '')

    def test_wanted_includes_qualifications_but_not_company_intro(self):
        html = '''<div class="JobDescription_JobDescription__paragraph__wrapper_1">회사소개 AI Agent</div>
        <div class="JobDescription_JobDescription__paragraph__1"><h3>주요업무</h3>고객 데이터 분석</div>
        <div class="JobDescription_JobDescription__paragraph__1"><h3>자격요건</h3>SQL Python</div>
        <div class="JobDescription_JobDescription__paragraph__1"><h3>우대사항</h3>dbt Airflow</div>'''
        text = extract_description(html, 'Wanted')
        self.assertIn('SQL Python', text)
        self.assertIn('dbt Airflow', text)
        self.assertNotIn('AI Agent', text)

    def test_linkareer_only_follows_current_activity_detail(self):
        props = {'data': {'activityData': {'activity': {'id': '1'}}}, '__APOLLO_STATE__': {
            'Activity:1': {'detailText': {'__ref': 'ActivityText:1'}},
            'ActivityText:1': {'text': '<p>SQL Python 데이터 분석</p>'},
            'ActivityText:2': {'text': '다른 공고 dbt Airflow'},
        }}
        html = '<script id="__NEXT_DATA__" type="application/json">' + json.dumps({'props': {'pageProps': props}}) + '</script>'
        self.assertEqual(extract_description(html, 'Linkareer'), 'SQL Python 데이터 분석')

    def test_jobkorea_seo_blurb_is_not_jd(self):
        html = '<script type="application/ld+json">' + json.dumps({
            '@type': 'JobPosting', 'description': '주식회사 SQL에서 채용을 진행합니다. 자세한 조건은 공고를 통해 확인할 수 있습니다.'
        }) + '</script>'
        self.assertEqual(extract_description(html, 'JobKorea'), '')

    def test_multiple_structured_jobs_are_not_mixed(self):
        html = '<script type="application/ld+json">{"@type":"JobPosting","description":"SQL"}</script>'
        self.assertEqual(extract_description(html + html, 'Wanted'), '')

    def test_site_specific_content_and_invalid_json(self):
        html = '<script type="application/ld+json">invalid</script><div class="user_content">SQL<br>Python</div>'
        self.assertEqual(extract_description(html, 'Saramin'), 'SQL Python')

    def test_same_site_detail_frame(self):
        page = Mock(text='<iframe id="ifrmJobCont" src="/s_common/jobpost/jobpostcont.asp?job=1"></iframe>', url='https://job.incruit.com/jobdb_info/jobpost.asp?job=1')
        detail = Mock(text='<html><body>고객 데이터 분석 SQL Python</body></html>')
        client = Mock()
        client.get.side_effect = [page, detail]
        self.assertEqual(fetch_description(page.url, 'Incruit', session=client), '고객 데이터 분석 SQL Python')
        self.assertEqual(client.get.call_count, 2)

    def test_external_frame_is_not_followed(self):
        page = Mock(text='<iframe id="ifrmJobCont" src="https://external.test/job"></iframe>', url='https://job.incruit.com/job')
        client = Mock()
        client.get.return_value = page
        self.assertEqual(fetch_description(page.url, 'Incruit', session=client), '')
        self.assertEqual(client.get.call_count, 1)

    def test_jobkorea_nextjs_frame_must_match_current_job(self):
        page = Mock(text=r'<script>src=GI_Read_Comt_Ifrm?Gno=123\u0026isHiringCenter=false</script>', url='https://www.jobkorea.co.kr/Recruit/GI_Read/123')
        detail = Mock(text='<main>데이터 분석 SQL Python</main>')
        client = Mock()
        client.get.side_effect = [page, detail]
        self.assertEqual(fetch_description(page.url, 'JobKorea', session=client), '데이터 분석 SQL Python')
        self.assertIn('Gno=123', client.get.call_args_list[1].args[0])
        page.text = 'GI_Read_Comt_Ifrm?Gno=999'
        client.get.side_effect = [page]
        self.assertEqual(fetch_description(page.url, 'JobKorea', session=client), '')

    def test_saramin_uses_only_requested_public_detail(self):
        page = Mock(text='<html></html>', url='https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=123')
        detail = Mock(text='<article>' + ('데이터 분석 업무 및 SQL Python 자격요건 ' * 5) + '</article>')
        client = Mock()
        client.get.side_effect = [page, detail]
        text = fetch_description(page.url, 'Saramin', session=client)
        self.assertIn('SQL Python', text)
        self.assertEqual(client.get.call_args_list[1].kwargs['params']['rec_idx'], '123')

    def test_timeout_returns_no_jd(self):
        client = Mock()
        client.get.side_effect = requests.Timeout()
        self.assertEqual(fetch_description('https://www.wanted.co.kr/wd/1', 'Wanted', session=client), '')


if __name__ == '__main__':
    unittest.main()
