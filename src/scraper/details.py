"""공고 본문만 추출한다. 전체 페이지/추천 공고는 JD로 사용하지 않는다."""

import json
import re
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup


DETAIL_SELECTORS = {
    "Saramin": (".user_content", ".jv_cont .user_content", "#job_detail"),
    "JobKorea": (".recruitment-description", "#gib_frame", ".detail-content"),
    "Linkareer": (".activity-description", "[class*='ActivityDetail'] [class*='Description']"),
    "Incruit": ("#jobContent", "#jobDetail", ".jobpost_content"),
    "Wanted": (),  # 담당업무/자격요건/우대사항만 별도로 추출한다.
}
FRAME_SELECTORS = {
    "Saramin": "iframe#iframe_content_0, iframe[src*='/jobs/relay/view-detail']",
    "JobKorea": "iframe#gib_frame, iframe#GI_Read_Contents, iframe[src*='GI_Read_Comt']",
    "Incruit": "iframe#ifrmJobCont",
}


def clean_html(html):
    soup = BeautifulSoup(html or "", "html.parser")
    for tag in soup.select("script, style, nav, header, footer, aside, iframe"):
        tag.decompose()
    return soup.get_text(" ", strip=True)[:20000]


def _job_postings(value):
    if isinstance(value, list):
        for item in value:
            yield from _job_postings(item)
    elif isinstance(value, dict):
        types = value.get("@type", [])
        if isinstance(types, str):
            types = [types]
        if "JobPosting" in types:
            yield value
        # 구조화된 공고만 읽고 추천 공고의 임의 데이터를 본문에 섞지 않는다.
        yield from _job_postings(value.get("@graph", []))


def extract_description(html, site):
    soup = BeautifulSoup(html, "html.parser")
    if site == "Wanted":
        sections = []
        for node in soup.select("[class*='JobDescription_JobDescription__paragraph__']"):
            heading = node.find('h3')
            if heading and heading.get_text(strip=True) in {'주요업무', '자격요건', '우대사항'}:
                sections.append(clean_html(str(node)))
        if sections:
            return '\n'.join(sections)[:20000]
    if site == "Linkareer":
        script = soup.select_one('script#__NEXT_DATA__')
        if script:
            try:
                props = json.loads(script.string)['props']['pageProps']
                activity = props['data']['activityData']['activity']
                state = props.get('__APOLLO_STATE__', {})
                record = state.get('Activity:' + str(activity['id']), activity)
                detail = record.get('detailText', {})
                if isinstance(detail, dict):
                    detail = state.get(detail.get('__ref'), detail)
                    text = clean_html(detail.get('text', ''))
                    if text:
                        return text
            except (ValueError, TypeError, KeyError, AttributeError):
                pass
    postings = []
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            postings.extend(_job_postings(json.loads(script.string or script.get_text())))
        except (ValueError, TypeError):
            continue
    if len(postings) == 1:
        parts = [postings[0].get(field) for field in ('description', 'responsibilities', 'qualifications', 'skills')]
        text = clean_html(' '.join(part for part in parts if isinstance(part, str)))
        # 잡코리아의 SEO 소개문은 실제 담당 업무/자격요건이 아니다.
        if site == 'JobKorea' and '자세한 조건은 공고를 통해 확인' in text:
            text = ''
        if text:
            return text
    for selector in DETAIL_SELECTORS.get(site, ()):
        node = soup.select_one(selector)
        if node and node.name != "iframe":
            text = clean_html(str(node))
            if text:
                return text
    return ""


def fetch_description(url, site, headers=None, session=None):
    client = session or requests
    request_headers = dict(headers or {})
    request_headers["Accept"] = "text/html,application/xhtml+xml"
    try:
        response = client.get(url, headers=request_headers, timeout=10)
        response.raise_for_status()
        text = extract_description(response.text, site)
        if text:
            return text
        # 사람인 상세는 공개 view-detail 페이지에서 동일 공고 ID로 제공된다.
        if site == 'Saramin':
            ids = parse_qs(urlparse(response.url).query).get('rec_idx', [])
            if len(ids) == 1 and ids[0].isdigit():
                detail_url = urljoin(response.url, '/zf_user/jobs/relay/view-detail')
                detail = client.get(detail_url, params={'rec_idx': ids[0], 'rec_seq': '0'},
                                    headers=request_headers, timeout=10)
                detail.raise_for_status()
                text = clean_html(detail.text)
                if len(text) >= 80:
                    return text
        selector = FRAME_SELECTORS.get(site)
        # 잡코리아의 최신 페이지는 상세 iframe 주소를 Next.js 데이터에 담는다.
        if site == 'JobKorea':
            job_id = re.search(r'/Recruit/GI_Read/(\d+)', urlparse(response.url).path, re.I)
            iframe_ids = re.findall(r'GI_Read_Comt_Ifrm\?Gno=(\d+)', response.text, re.I)
            if job_id and job_id.group(1) in iframe_ids:
                frame_url = urljoin(response.url, '/Recruit/GI_Read_Comt_Ifrm?Gno=' + job_id.group(1))
                detail = client.get(frame_url, headers=request_headers, timeout=10)
                detail.raise_for_status()
                return clean_html(detail.text)
        if selector:
            soup = BeautifulSoup(response.text, "html.parser")
            frame = soup.select_one(selector)
            if frame and frame.get("src"):
                frame_url = urljoin(response.url, frame["src"])
                # 공고 본문용이며 같은 사이트의 iframe만 읽는다.
                if urlparse(frame_url).hostname == urlparse(response.url).hostname:
                    detail = client.get(frame_url, headers=request_headers, timeout=10)
                    detail.raise_for_status()
                    return clean_html(detail.text)
    except (requests.RequestException, ValueError, TypeError):
        pass
    return ""
