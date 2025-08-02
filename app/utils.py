from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .models import Job, JobTest, TestQuestion, QuestionAnswer
import os
import requests
from langdetect import detect

LLM_API_URL = os.getenv("LLM_API_URL", "https://api.groq.com/openai/v1/chat/completions")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "llama3-8b-8192")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# --------- Pydantic Schemas ---------
class GenerateQuestionRequest(BaseModel):
    job_id: int

class QuestionCreate(BaseModel):
    test_id: int
    question_text: str
    explanation: str = ""

class EvaluateAnswerRequest(BaseModel):
    question_id: int
    result_id: int

# --------- Language Detection ---------
def detect_language(text: str) -> str:
    try:
        lang = detect(text)
        return 'vi' if lang == 'vi' else 'en'
    except:
        return 'en'

# --------- Prompt Builder ---------
def get_prompt(jd: str, lang: str) -> str:
    if lang == 'vi':
        return f"""
            Bạn là chuyên gia tuyển dụng. Dưới đây là mô tả công việc:
            \"\"\"{jd}\"\"\"

            **Nhiệm vụ**:
            1. Xác định mức độ kinh nghiệm yêu cầu cho vị trí này (ít kinh nghiệm, trung bình, hoặc cao cấp) dựa trên nội dung JD.
            2. Dựa vào mức độ đó, tạo **5 câu hỏi phỏng vấn chuyên sâu và phù hợp bằng tiếng Việt**, để đánh giá:
               - Kỹ năng chuyên môn chính.
               - Khả năng giải quyết vấn đề hoặc xử lý tình huống thực tế.
               - Sự phù hợp với vai trò và tổ chức.

            **Định nghĩa mức độ kinh nghiệm**:
            - **Ít kinh nghiệm (Entry-level, dưới 2 năm)**:
              - Ứng viên mới ra trường hoặc có ít kinh nghiệm.
              - Nên hỏi về: kiến thức nền tảng, công cụ cơ bản, quy trình đơn giản, hiểu biết lý thuyết.
            - **Kinh nghiệm trung bình (2–5 năm)**:
              - Đã làm việc thực tế, có khả năng giải quyết vấn đề độc lập.
              - Nên hỏi về: kinh nghiệm triển khai, phân tích tình huống thực tế, cải tiến công việc.
            - **Kinh nghiệm cao (Senior, trên 5 năm)**:
              - Có khả năng ra quyết định, tối ưu hệ thống, hoặc lãnh đạo nhóm.
              - Nên hỏi về: chiến lược, tầm nhìn hệ thống, kinh nghiệm quản lý hoặc mentoring.

            **Yêu cầu**:
            - Mỗi câu hỏi phải rõ ràng, tránh chung chung.
            - Không cần giải thích hay dịch. Chỉ liệt kê 5 câu hỏi một cách ngắn gọn, rõ ràng, phù hợp với JD trên.
            - Trả lời hoàn toàn bằng **tiếng Việt**, trình bày dạng danh sách gạch đầu dòng.
        """
    else:
        return f"""
            You are a professional recruiter. Carefully read the following job description:
            \"\"\"{jd}\"\"\"

            **Your task**:
            1. Determine the required experience level (entry-level, mid-level, or senior-level) based on the JD.
            2. Generate **5 highly relevant interview questions** tailored to that level, aiming to assess:
               - Core technical or functional skills.
               - Real-world problem solving.
               - Fit for the role and organization.

            **Define the experience levels**:
            - **Entry-level (under 2 years)**:
              - Recent graduates or junior professionals.
              - Ask about: basic concepts, common tools, understanding of workflows, theoretical knowledge.
            - **Mid-level (2–5 years)**:
              - Experienced in implementation, troubleshooting, working independently.
              - Ask about: hands-on experience, applied scenarios, improvements they've contributed.
            - **Senior-level (5+ years)**:
              - Decision-makers, system optimizers, team leads.
              - Ask about: strategy, architecture, leadership, mentoring, long-term impact.

            **Guidelines**:
            - Make each question precise and insightful (avoid vague/generic ones).
            - Without explanation or translation. Only list the 5 questions clearly and concisely, based on the job description.
            - Respond in English, in bullet point format.
        """

# --------- AI Services ---------
def generate_questions_from_jd(jd_text: str, model: str = LLM_MODEL_NAME) -> List[str]:
    if not jd_text:
        return []

    lang = detect_language(jd_text)
    prompt = get_prompt(jd_text, lang)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post(LLM_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        lines = content.splitlines()
        questions = [line.strip("-• ") for line in lines if line.strip().startswith(('-', '•')) or line.strip().startswith(tuple("12345"))]
        return questions
    except Exception as e:
        print("❌ Error calling Groq API:", e)
        return []

def evaluate_answer_llm(question: str, answer: str, jd: str) -> dict:
    score = 0.75 if answer and jd and question else 0.0
    rationale = "Câu trả lời phù hợp các yêu cầu chính của JD ở mức khá (demo)."
    return {"score": score, "rationale": rationale}

# --------- CRUD helpers ---------
def get_job(db: Session, job_id: int) -> Optional[Job]:
    return db.query(Job).filter(Job.job_id == job_id).first()

def get_or_create_job_test(db: Session, job_id: int) -> JobTest:
    test = db.query(JobTest).filter(JobTest.job_id == job_id).first()
    if test:
        return test
    test = JobTest(job_id=job_id, test_name="Auto Generated Test")
    db.add(test); db.commit(); db.refresh(test)
    return test

def create_question(db: Session, test_id: int, question_text: str, explanation: str = "") -> TestQuestion:
    q = TestQuestion(test_id=test_id, question_text=question_text, explanation=explanation)
    db.add(q); db.commit(); db.refresh(q)
    return q

def latest_answer_for_question(db: Session, question_id: int) -> Optional[QuestionAnswer]:
    return (db.query(QuestionAnswer)
              .filter(QuestionAnswer.question_id == question_id)
              .order_by(QuestionAnswer.answer_id.desc())
              .first())

def get_answer_by_result_question(db: Session, result_id: int, question_id: int) -> Optional[QuestionAnswer]:
    return db.query(QuestionAnswer).filter(QuestionAnswer.result_id == result_id, QuestionAnswer.question_id == question_id).first()

def get_answer_by_id(db: Session, answer_id: int) -> Optional[QuestionAnswer]:
    return db.query(QuestionAnswer).filter(QuestionAnswer.answer_id == answer_id).first()
