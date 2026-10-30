import requests
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.config import Config
from src.logic.job_relevance import get_job_category

class Notifier:
    def __init__(self):
        self.slack_url = Config.SLACK_WEBHOOK_URL
        self.discord_url = os.getenv("DISCORD_WEBHOOK_URL")
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.gmail_user = os.getenv("GMAIL_USER")
        self.gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")
        self.gmail_to = os.getenv("GMAIL_TO")
        
        # === 디버깅: 환경변수 체크 ===
        print("\n" + "="*50)
        print("📧 [EMAIL DEBUG] 환경변수 상태 체크")
        print("="*50)
        print(f"  GMAIL_USER: {'✅ 설정됨 (' + self.gmail_user[:5] + '...)' if self.gmail_user else '❌ 없음'}")
        print(f"  GMAIL_APP_PASSWORD: {'✅ 설정됨 (****)' if self.gmail_app_password else '❌ 없음'}")
        print(f"  GMAIL_TO: {'✅ 설정됨 (' + self.gmail_to[:10] + '...)' if self.gmail_to else '❌ 없음'}")
        print(f"  GMAIL_TO_DATA: {'✅' if os.getenv('GMAIL_TO_DATA') else '❌'}")
        print(f"  GMAIL_TO_ACCOUNTING: {'✅' if os.getenv('GMAIL_TO_ACCOUNTING') else '❌'}")
        print(f"  GMAIL_TO_HR: {'✅' if os.getenv('GMAIL_TO_HR') else '❌'}")
        print("="*50 + "\n")
        
    def send_all_alerts(self, new_jobs, today_jobs, upcoming_jobs, page_url):
        """모든 설정된 알림 채널로 발송"""
        new_jobs_count = len(new_jobs) if isinstance(new_jobs, list) else new_jobs
        
        print(f"\n📢 [NOTIFIER] 알림 발송 시작 (신규 {new_jobs_count}건, 오늘마감 {len(today_jobs)}건, 내일마감 {len(upcoming_jobs)}건)")
        
        self.send_slack_alert(new_jobs_count, today_jobs, upcoming_jobs, page_url)
        self.send_discord_alert(new_jobs_count, today_jobs, upcoming_jobs, page_url)
        self.send_telegram_alert(new_jobs_count, today_jobs, upcoming_jobs, page_url)
        
        # 카테고리별 이메일 발송
        if isinstance(new_jobs, list):
            self.send_category_emails(new_jobs, today_jobs, upcoming_jobs, page_url)
        else:
            self.send_gmail_alert(new_jobs_count, today_jobs, upcoming_jobs, page_url, None)
        
    def send_slack_alert(self, new_jobs_count, today_jobs, upcoming_jobs, page_url):
        if not self.slack_url:
            return

        message = f"📢 *오늘의 채용 브리핑* 📢\n\n"
        
        # 1. 내일 마감 (가장 중요)
        if upcoming_jobs:
            message += f"🔥 *내일 마감! 서두르세요 ({len(upcoming_jobs)}건)*\n"
            for job in upcoming_jobs[:5]:
                message += f"• <{job['link']}|{job['title']}> ({job['company']})\n"
            if len(upcoming_jobs) > 5:
                message += f"• 외 {len(upcoming_jobs)-5}건...\n"
            message += "\n"

        # 2. 오늘 마감 (긴급)
        if today_jobs:
            message += f"🚨 *오늘 마감 (놓치지 마세요!)*\n"
            for job in today_jobs[:3]:
                message += f"• <{job['link']}|{job['title']}> ({job['company']})\n"
            message += "\n"
            
        message += f"✨ *신규 발견 공고:* {new_jobs_count}건\n"
        message += f"👉 <{page_url}|전체 공고 보러가기>\n"
        
        try:
            requests.post(self.slack_url, json={"text": message})
            print("✅ Slack 알림 발송 완료")
        except Exception as e:
            print(f"❌ Slack 발송 실패: {e}")

    def send_discord_alert(self, new_jobs_count, today_jobs, upcoming_jobs, page_url):
        if not self.discord_url:
            return

        message = f"📢 **오늘의 채용 브리핑** 📢\n\n"
        
        if upcoming_jobs:
            message += f"🔥 **내일 마감! 서두르세요 ({len(upcoming_jobs)}건)**\n"
            for job in upcoming_jobs[:5]:
                message += f"• [{job['title']}]({job['link']}) ({job['company']})\n"
            message += "\n"

        if today_jobs:
            message += f"🚨 **오늘 마감 ({len(today_jobs)}건)**\n"
            for job in today_jobs[:3]:
                message += f"• [{job['title']}]({job['link']}) ({job['company']})\n"
            message += "\n"
            
        message += f"✨ **신규 발견 공고:** {new_jobs_count}건\n"
        message += f"👉 [전체 공고 보러가기]({page_url})\n"
        
        try:
            requests.post(self.discord_url, json={"content": message})
            print("✅ Discord 알림 발송 완료")
        except Exception as e:
            print(f"❌ Discord 발송 실패: {e}")

    def send_telegram_alert(self, new_jobs_count, today_jobs, upcoming_jobs, page_url):
        if not self.telegram_token or not self.telegram_chat_id:
            return

        message = f"📢 오늘의 채용 브리핑 📢\n\n"
        
        if upcoming_jobs:
            message += f"🔥 내일 마감! ({len(upcoming_jobs)}건)\n"
            for job in upcoming_jobs[:5]:
                message += f"• {job['title']} ({job['company']})\n"
            message += "\n"

        if today_jobs:
            message += f"🚨 오늘 마감 ({len(today_jobs)}건)\n"
            for job in today_jobs[:3]:
                message += f"• {job['title']} ({job['company']})\n"
            message += "\n"
            
        message += f"✨ 신규 발견 공고: {new_jobs_count}건\n"
        message += f"👉 {page_url}\n"
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            requests.post(url, json={
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "HTML"
            })
            print("✅ Telegram 알림 발송 완료")
        except Exception as e:
            print(f"❌ Telegram 발송 실패: {e}")

    def send_category_emails(self, jobs, today_jobs, upcoming_jobs, page_url):
        """카테고리별로 다른 사람에게 이메일 발송"""
        if not self.gmail_user or not self.gmail_app_password:
            return
            
        # 카테고리별로 공고 분류
        category_jobs = {
            "Data": [],
            "Accounting": [],
            "HR": []
        }
        
        for job in jobs:
            category = get_job_category(job)
            if category in category_jobs:
                category_jobs[category].append(job)
        
        # 카테고리별 수신자에게 발송
        for category, cat_jobs in category_jobs.items():
            recipients = Config.GMAIL_RECIPIENTS.get(category)
            if recipients and (cat_jobs or today_jobs or upcoming_jobs):
                # 해당 카테고리 마감 공고 필터
                cat_today = [j for j in today_jobs if self._is_in_category(j, category)]
                cat_upcoming = [j for j in upcoming_jobs if self._is_in_category(j, category)]
                
                category_names = {"Data": "데이터", "Accounting": "회계", "HR": "인사"}
                cat_name = category_names.get(category, category)
                
                self.send_gmail_alert(
                    len(cat_jobs), 
                    cat_today,
                    cat_upcoming,
                    page_url, 
                    recipients,
                    category_name=cat_name,
                    category_jobs=cat_jobs
                )
        
        # 전체 공고 수신자
        all_recipients = Config.GMAIL_RECIPIENTS.get("All")
        if all_recipients:
            self.send_gmail_alert(len(jobs), today_jobs, upcoming_jobs, page_url, all_recipients)

    def _is_in_category(self, job, category):
        return get_job_category(job) == category

    def send_gmail_alert(self, new_jobs_count, today_jobs, upcoming_jobs, page_url, recipients=None, category_name=None, category_jobs=None):
        if not self.gmail_user or not self.gmail_app_password:
            return
        
        # 수신자 결정
        to_emails_raw = recipients or self.gmail_to or self.gmail_user
        to_emails = [email.strip() for email in to_emails_raw.split(',')]
        
        # 카테고리 정보가 있으면 제목에 표시
        subject_prefix = f"[{category_name} 직군]" if category_name else ""
        
        # 카테고리별 URL 파라미터 추가
        category_url_map = {
            "데이터": "data",
            "회계": "accounting",
            "인사": "hr"
        }
        if category_name and category_name in category_url_map:
            page_url = f"{page_url}?category={category_url_map[category_name]}"
        
        # HTML 이메일 본문 생성
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #4F46E5;">📢 오늘의 채용 브리핑 {f"- {category_name} 직군" if category_name else ""}</h2>
        """
        
        # 1. 내일 마감 (Prioritized)
        if upcoming_jobs:
            html += f"""
            <div style="background: #FEF3C7; padding: 15px; border-radius: 8px; margin: 15px 0;">
                <h3 style="color: #D97706; margin: 0;">🔥 내일 마감! 서두르세요 ({len(upcoming_jobs)}건)</h3>
                <ul>
            """
            for job in upcoming_jobs[:5]: # 최대 5개
                html += f'<li><a href="{job["link"]}">{job["title"]}</a> - {job["company"]}</li>'
            if len(upcoming_jobs) > 5:
                html += f'<li>... 외 {len(upcoming_jobs) - 5}건</li>'
            html += "</ul></div>"

        # 2. 오늘 마감 (Urgent)
        if today_jobs:
            html += f"""
            <div style="background: #FEE2E2; padding: 15px; border-radius: 8px; margin: 15px 0;">
                <h3 style="color: #DC2626; margin: 0;">🚨 긴급: 오늘 마감 ({len(today_jobs)}건)</h3>
                <ul>
            """
            for job in today_jobs[:5]:
                html += f'<li><a href="{job["link"]}">{job["title"]}</a> - {job["company"]}</li>'
            html += "</ul></div>"
        
        # 3. 신규 공고
        if category_jobs:
            html += f"""
            <div style="background: #EEF2FF; padding: 15px; border-radius: 8px; margin: 15px 0;">
                <h3 style="color: #4F46E5; margin: 0;">📋 {category_name} 관련 신규 공고 ({len(category_jobs)}건)</h3>
                <ul>
            """
            for job in category_jobs[:10]:
                html += f'<li><a href="{job["link"]}">{job["title"]}</a> - {job["company"]}</li>'
            if len(category_jobs) > 10:
                html += f'<li>... 외 {len(category_jobs) - 10}건</li>'
            html += "</ul></div>"
        elif new_jobs_count > 0:
            html += f"""
            <div style="background: #ECFDF5; padding: 15px; border-radius: 8px; margin: 15px 0;">
                <h3 style="color: #059669; margin: 0;">✨ 신규 발견 공고: {new_jobs_count}건</h3>
            </div>
            """
            
        html += f"""
            <a href="{page_url}" style="display: inline-block; background: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; margin-top: 20px;">
                전체 공고 보러가기 →
            </a>
            <p style="color: #9CA3AF; margin-top: 30px; font-size: 12px;">Job Scout AI가 자동으로 발송한 이메일입니다.</p>
        </body>
        </html>
        """
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[Job Scout] {subject_prefix} 오늘의 채용 브리핑"
            msg['From'] = self.gmail_user
            msg['To'] = ', '.join(to_emails)
            
            msg.attach(MIMEText(html, 'html'))
            
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.gmail_user, self.gmail_app_password)
                server.sendmail(self.gmail_user, to_emails, msg.as_string())
                
            category_info = f" ({category_name})" if category_name else ""
            print(f"✅ Gmail 알림 발송 완료{category_info} ({len(to_emails)}명)")
        except Exception as e:
            print(f"❌ Gmail 발송 실패: {e}")

