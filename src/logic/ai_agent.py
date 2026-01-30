import google.generativeai as genai
import os
import json
from src.config import Config

class AIAgent:
    def __init__(self):
        api_key = Config.GEMINI_API_KEY
        
        print("\n" + "="*50)
        print("🤖 [AI DEBUG] Gemini API 상태 체크")
        print("="*50)
        print(f"  GEMINI_API_KEY: {'✅ 설정됨 (' + api_key[:8] + '...)' if api_key else '❌ 없음'}")
        
        if api_key:
            try:
                genai.configure(api_key=api_key)
                # gemini-1.5-flash로 변경 (더 빠르고 안정적)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                print("  모델: ✅ gemini-1.5-flash 로드 완료")
            except Exception as e:
                print(f"  모델 로드 실패: ❌ {e}")
                self.model = None
        else:
            self.model = None
            print("  ⚠️ API 키가 없어서 AI 기능이 비활성화됩니다.")
        print("="*50 + "\n")

    def analyze_job(self, job_title, job_text):
        if not self.model or not job_text:
            return {
                "summary": "AI API Key missing or no text.",
                "strategy": "Please configure API Key."
            }
            
        prompt = f"""
        당신은 해당 분야 취업 전문가입니다. 다음 채용공고를 분석해주세요.
        
        [공고 제목] {job_title}
        [공고 내용]
        {job_text[:3000]} (Start of text)
        ...
        
        다음 형식의 JSON으로만 응답해주세요 (MarkDown 코드블럭 없이 순수 JSON만):
        {{
            "summary": "공고의 핵심 내용 3줄 요약",
            "required_skills": ["필수 역량1", "역량2"],
            "cover_letter_strategy": "이 공고에 합격하기 위해 자소서에(Entry Level 기준) 강조해야 할 전략 3가지"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        except Exception as e:
            print(f"AI Analysis failed: {e}")
            return {
                "summary": "분석 실패",
                "strategy": "AI 호출 중 오류가 발생했습니다."
            }
