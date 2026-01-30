# Job Scout AI 🚀

매일 아침 자동으로 채용공고를 수집하고, AI가 자소서 전략까지 짜주는 서버리스 자동화 시스템입니다.

## 📁 파일 구조 및 설명

```
📦 채용공고자동화
├── 📂 .github/workflows/
│   └── daily_job.yml      # GitHub Actions 자동화 설정 (매일 09:00 KST 실행)
├── 📂 docs/
│   ├── index.html         # 웹 대시보드 (친구에게 공유할 페이지)
│   └── jobs.json          # 수집된 공고 데이터 (자동 생성됨)
├── 📂 src/
│   ├── config.py          # 설정 파일 (검색 키워드, API 키 등)
│   ├── main.py            # 메인 실행 파일 (전체 흐름 관리)
│   ├── notifier.py        # 알림 발송 (Slack/이메일)
│   ├── 📂 scraper/
│   │   ├── saramin.py     # 사람인 크롤러
│   │   ├── jobkorea.py    # 잡코리아 크롤러
│   │   └── manager.py     # 크롤러 통합 관리
│   └── 📂 logic/
│       ├── ai_agent.py    # Gemini AI 연동 (요약 및 전략 생성)
│       ├── data_manager.py # 데이터 저장/중복 제거
│       └── deadline.py    # 마감일 체크
└── requirements.txt       # Python 라이브러리 목록
```

## 🚀 배포 방법 (GitHub)

### 1. GitHub 저장소 생성
1. [GitHub](https://github.com/new)에서 새 저장소 생성 (Public 선택)
2. 아무 옵션도 체크하지 말고 빈 저장소로 생성

### 2. 코드 업로드
```bash
git remote add origin https://github.com/[아이디]/[저장소명].git
git branch -M main
git push -u origin main
```

### 3. GitHub Secrets 설정 (필수!)
`Settings > Secrets and variables > Actions`에서 추가:
| Name | Value |
|------|-------|
| `GEMINI_API_KEY` | Google AI Studio에서 발급받은 키 |
| `SLACK_WEBHOOK_URL` | Slack 웹훅 URL (선택) |

### 4. GitHub Pages 설정
`Settings > Pages`에서:
- Source: `Deploy from a branch`
- Branch: `main` / `/docs` 선택 후 Save

### 5. 수동 실행 테스트
`Actions` 탭 > `Daily Job Scout` > `Run workflow` 클릭

## 🎯 타겟 직무
현재 설정된 검색 키워드:
- **데이터**: 데이터 분석, Data Analyst, 데이터 엔지니어, AI, 머신러닝
- **회계**: 회계, 재무, 세무, 결산
- **인사**: 인사, HRM, HRD, 총무, 채용

키워드 수정은 `src/config.py` 파일에서 가능합니다.

## 📱 알림 설정

### Slack 알림 받기
1. Slack 워크스페이스에서 [Incoming Webhook](https://api.slack.com/messaging/webhooks) 생성
2. 생성된 URL을 GitHub Secrets의 `SLACK_WEBHOOK_URL`에 등록

## 🔑 Gemini API 키 발급 방법
1. [Google AI Studio](https://aistudio.google.com/app/apikey) 접속
2. `Create API Key` 클릭
3. 생성된 키를 GitHub Secrets에 등록

---
Made with ❤️ for job seekers
