import requests
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.config import Config

class Notifier:
    def __init__(self):
        self.slack_url = Config.SLACK_WEBHOOK_URL
        self.discord_url = os.getenv("DISCORD_WEBHOOK_URL")
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.gmail_user = os.getenv("GMAIL_USER")
        self.gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")
        self.gmail_to = os.getenv("GMAIL_TO")  # 받을 이메일 주소
        
    def send_all_alerts(self, new_jobs_count, deadline_jobs, page_url):
        """모든 설정된 알림 채널로 발송"""
        self.send_slack_alert(new_jobs_count, deadline_jobs, page_url)
        self.send_discord_alert(new_jobs_count, deadline_jobs, page_url)
        self.send_telegram_alert(new_jobs_count, deadline_jobs, page_url)
        self.send_gmail_alert(new_jobs_count, deadline_jobs, page_url)
        
    def send_slack_alert(self, new_jobs_count, deadline_jobs, page_url):
        if not self.slack_url:
            return

        message = f"📢 *오늘의 채용 브리핑* 📢\n\n"
        
        if deadline_jobs:
            message += f"🚨 *오늘 마감 공고 ({len(deadline_jobs)}건)*\n"
            for job in deadline_jobs[:3]:
                message += f"• <{job['link']}|{job['title']}> ({job['company']})\n"
            if len(deadline_jobs) > 3:
                message += f"• 외 {len(deadline_jobs)-3}건...\n"
            message += "\n"
            
        message += f"✨ *신규 발견 공고:* {new_jobs_count}건\n"
        message += f"👉 <{page_url}|전체 공고 및 AI 자소서 전략 보러가기>\n"
        
        try:
            requests.post(self.slack_url, json={"text": message})
            print("✅ Slack 알림 발송 완료")
        except Exception as e:
            print(f"❌ Slack 발송 실패: {e}")

    def send_discord_alert(self, new_jobs_count, deadline_jobs, page_url):
        if not self.discord_url:
            return

        message = f"📢 **오늘의 채용 브리핑** 📢\n\n"
        
        if deadline_jobs:
            message += f"🚨 **오늘 마감 공고 ({len(deadline_jobs)}건)**\n"
            for job in deadline_jobs[:3]:
                message += f"• [{job['title']}]({job['link']}) ({job['company']})\n"
            if len(deadline_jobs) > 3:
                message += f"• 외 {len(deadline_jobs)-3}건...\n"
            message += "\n"
            
        message += f"✨ **신규 발견 공고:** {new_jobs_count}건\n"
        message += f"👉 [전체 공고 보러가기]({page_url})\n"
        
        try:
            requests.post(self.discord_url, json={"content": message})
            print("✅ Discord 알림 발송 완료")
        except Exception as e:
            print(f"❌ Discord 발송 실패: {e}")

    def send_telegram_alert(self, new_jobs_count, deadline_jobs, page_url):
        if not self.telegram_token or not self.telegram_chat_id:
            return

        message = f"📢 오늘의 채용 브리핑 📢\n\n"
        
        if deadline_jobs:
            message += f"🚨 오늘 마감 공고 ({len(deadline_jobs)}건)\n"
            for job in deadline_jobs[:3]:
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

    def send_gmail_alert(self, new_jobs_count, deadline_jobs, page_url):
        if not self.gmail_user or not self.gmail_app_password:
            return
            
        to_email = self.gmail_to or self.gmail_user  # 받을 주소 없으면 본인에게
        
        # HTML 이메일 본문 생성
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #4F46E5;">📢 오늘의 채용 브리핑</h2>
        """
        
        if deadline_jobs:
            html += f"""
            <div style="background: #FEE2E2; padding: 15px; border-radius: 8px; margin: 15px 0;">
                <h3 style="color: #DC2626; margin: 0;">🚨 오늘 마감 공고 ({len(deadline_jobs)}건)</h3>
                <ul>
            """
            for job in deadline_jobs[:5]:
                html += f'<li><a href="{job["link"]}">{job["title"]}</a> - {job["company"]}</li>'
            html += "</ul></div>"
            
        html += f"""
            <div style="background: #ECFDF5; padding: 15px; border-radius: 8px; margin: 15px 0;">
                <h3 style="color: #059669; margin: 0;">✨ 신규 발견 공고: {new_jobs_count}건</h3>
            </div>
            
            <a href="{page_url}" style="display: inline-block; background: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; margin-top: 20px;">
                전체 공고 및 AI 자소서 전략 보러가기 →
            </a>
            
            <p style="color: #9CA3AF; margin-top: 30px; font-size: 12px;">
                Job Scout AI가 자동으로 발송한 이메일입니다.
            </p>
        </body>
        </html>
        """
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[Job Scout] 오늘의 채용 브리핑 - 신규 {new_jobs_count}건"
            msg['From'] = self.gmail_user
            msg['To'] = to_email
            
            msg.attach(MIMEText(html, 'html'))
            
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.gmail_user, self.gmail_app_password)
                server.sendmail(self.gmail_user, to_email, msg.as_string())
                
            print("✅ Gmail 알림 발송 완료")
        except Exception as e:
            print(f"❌ Gmail 발송 실패: {e}")
