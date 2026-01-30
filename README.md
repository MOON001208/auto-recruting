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

> ⚠️ **중요**: `Settings > Secrets and variables > Actions`로 이동하면 **Secrets**와 **Variables** 두 개의 탭이 있습니다.
> 
> **반드시 `Secrets` 탭을 선택**하고 `New repository secret` 버튼을 눌러 등록하세요!
> - ✅ **Secrets**: API 키처럼 민감한 정보 저장 (암호화됨, 로그에 안 보임)
> - ❌ **Variables**: 일반적인 설정값 저장 (누구나 볼 수 있음) ← 여기에 API 키 넣으면 안됨!

**등록 방법:**
1. `Settings` → `Secrets and variables` → `Actions` 클릭
2. **Secrets** 탭 선택
3. `New repository secret` 버튼 클릭
4. 아래 정보 입력 후 `Add secret` 클릭

| Name | Value | 필수 여부 |
|------|-------|----------|
| `GEMINI_API_KEY` | Google AI Studio에서 발급받은 키 | ✅ 필수 |
| `SLACK_WEBHOOK_URL` | Slack 웹훅 URL | 선택 (알림 원하면 등록) |

### 4. GitHub Pages 설정
`Settings > Pages`에서:
- Source: `Deploy from a branch`
- Branch: `main` / `/docs` 선택 후 Save

### 5. GitHub Actions 사용법 (처음 쓰는 분들을 위한 상세 가이드)

GitHub Actions는 코드를 자동으로 실행해주는 GitHub의 무료 기능입니다.
우리 프로젝트에서는 **매일 아침 9시에 자동으로 채용공고를 수집**하도록 설정되어 있습니다.

#### 🔍 Actions 탭 찾아가기
1. GitHub에서 내 저장소 페이지로 이동
2. 상단 메뉴에서 **`Actions`** 탭 클릭 (Code, Issues, Pull requests 옆에 있음)
3. 처음 들어가면 "I understand my workflows, go ahead and enable them" 버튼이 보일 수 있음 → **클릭해서 활성화**

#### ▶️ 수동으로 실행해보기 (테스트)
1. `Actions` 탭 클릭
2. 왼쪽 사이드바에서 **`Daily Job Scout`** 클릭
3. 오른쪽에 **`Run workflow`** 버튼 클릭
4. 드롭다운이 열리면 다시 **`Run workflow`** (초록색 버튼) 클릭
5. 페이지를 새로고침하면 실행 중인 워크플로우가 보임

#### ✅ 실행 결과 확인하기
- **🟢 초록색 체크**: 성공! 채용공고 수집 완료
- **🔴 빨간색 X**: 실패. 클릭해서 로그 확인 필요
- **🟡 노란색 원**: 실행 중...

#### 🔧 실패했을 때 확인할 것들
1. **Secrets 설정 확인**: `GEMINI_API_KEY`가 제대로 등록되었는지
2. **로그 확인 방법**:
   - 실패한 워크플로우 클릭
   - `scout` job 클릭
   - 빨간색 X 표시된 단계 클릭하면 에러 메시지 확인 가능

#### ⏰ 자동 실행 스케줄
- 설정된 시간: **매일 00:00 UTC = 한국시간 오전 9시**
- 자동으로 돌아가므로 한번 설정하면 신경 쓸 필요 없음!
- 실행 기록은 `Actions` 탭에서 언제든 확인 가능

#### 💡 알아두면 좋은 것
- GitHub Actions는 **월 2,000분 무료** (Public 저장소는 무제한)
- 한 번 실행에 약 1-3분 소요 → 하루 1번이면 월 90분 정도만 사용
- 걱정 없이 무료로 사용 가능!

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
