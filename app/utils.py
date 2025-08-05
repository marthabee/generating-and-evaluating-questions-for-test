from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
import re
from .models import Job, JobTest, TestQuestion, QuestionAnswer, TestResult, Application
import os
import requests
from langdetect import detect
import json
from datetime import datetime

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
            2. Dựa vào mức độ đó, tạo 5 câu hỏi phỏng vấn chuyên sâu và phù hợp **bằng TIẾNG VIỆT**, để đánh giá:
               - Kỹ năng chuyên môn chính - **3 câu**.
               - Khả năng giải quyết vấn đề hoặc xử lý tình huống thực tế - **1 câu**.
               - Sự phù hợp với vai trò và tổ chức - **1 câu**.

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
            - Trả lời hoàn toàn bằng **tiếng Việt**, trả về 1 danh sách câu hỏi không cần dịch hay giải thích gì thêm.
        """
    else:
        return f"""
            You are a professional recruiter. Carefully read the following job description:
            \"\"\"{jd}\"\"\"

            **Your task**:
            1. Determine the required experience level (entry-level, mid-level, or senior-level) based on the JD.
            2. Generate **5 highly relevant interview questions** tailored to that level, aiming to assess:
               - Core technical or functional skills - **3 questions**.
               - Real-world problem solving - **1 question**.
               - Fit for the role and organization - **1 question**.

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
            - Without explanation or translation or formatting. Only plain list the 5 questions clearly and concisely, based on the job description.
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
        lines = [line.strip("-• ").strip() for line in content.splitlines() if line.strip()]

        questions = []
        for i, line in enumerate(lines):
            if not line.endswith("?"):
                continue
            question_text = re.sub(r"^\d+\.\s*", "", line).strip()

            if i < 3:
                q_type = "core"
            elif i == 3:
                q_type = "problem_solving"
            else:
                q_type = "fit"

            questions.append({
                "question_text": question_text,
                "question_type": q_type
            })

        return questions

    except Exception as e:
        print("❌ Error calling Groq API:", e)
        return []
    
# --------- Evaluation Functions ---------

def get_review_prompt(question: str, answer: str, lang: str = LLM_MODEL_NAME) -> str:
    if lang == "vi":
        return f"""
## 🧑 Vai trò (Role)
Bạn là chuyên gia nhân sự cấp cao, nhiều kinh nghiệm phỏng vấn ứng viên.

## 📄 Bối cảnh (Context)
- Câu hỏi phỏng vấn: {question}
- Câu trả lời của ứng viên: {answer}

## 📝 Hướng dẫn (Instructions)
1. Đánh giá câu trả lời dựa trên mức độ phù hợp với câu hỏi, tính chính xác, độ rõ ràng.
2. Viết **nhận xét ngắn gọn** (1–3 câu) giúp ứng viên hiểu điểm mạnh & điểm yếu.
3. Chấm điểm câu trả lời trên **thang điểm 100** (0 là hoàn toàn sai, 100 là rất tốt). nếu câu trả lời trống, trả về 0. nếu câu trả lời đúng với câu hỏi, trả về chính xác 100.
4. Đưa ra 1–2 gợi ý cải thiện, nếu cần.

## 📦 Định dạng (Format)
Trả về JSON đúng cấu trúc sau, không giải thích thêm, không thêm thông tin khác ngoài JSON:

{{
  "score": <số nguyên từ 0 đến 100>,
  "comment": "<nhận xét>",
  "suggestion": "<gợi ý cải thiện nếu có>"
}}

Trả lời **hoàn toàn bằng tiếng Việt**.
"""
    else:
        return f"""
## 🧑 Role
You are a senior HR professional with extensive experience interviewing candidates.

## 📄 Context
- Interview question: {question}
- Candidate's answer: {answer}

## 📝 Instructions
1. Evaluate the answer based on its relevance, accuracy, and clarity.
2. Write a **brief comment** (1–3 sentences) summarizing strengths and weaknesses.
3. Give a score from 0 to 100 (0 = completely wrong/no answer, 100 = excellent). if the answer is empty, return 0. if the answer is correct, return exactly 100.
4. Provide 1–2 suggestions for improvement, if applicable.

## 📦 Format
Return a JSON object matching the exact structure below. Do not include explanations or extra text:

{{
  "score": <integer 0-100>,
  "comment": "<brief feedback>",
  "suggestion": "<improvement advice if any>"
}}

Respond entirely in English.
"""

def generate_evaluation(question: str, answer: str, model: str = LLM_MODEL_NAME) -> dict:
    try:
        lang = detect(answer or question)
    except:
        lang = "vi"

    prompt = get_review_prompt(question, answer, lang)

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful interview assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3
        }
    )

    if response.status_code != 200:
        print("❌ Error calling API:", response.text)
        return {}

    content = response.json()["choices"][0]["message"]["content"]

    try:
        return json.loads(content)
    except Exception as e:
        print("❌ Error parsing JSON:", e)
        print("🔎 Content returned:", content)
        return {}

def evaluate_single_answer(question_id: int, answer_id: int, db) -> dict:
    from app.models import TestQuestion, QuestionAnswer

    question = db.query(TestQuestion).filter(TestQuestion.question_id == question_id).first()
    answer = db.query(QuestionAnswer).filter(QuestionAnswer.answer_id == answer_id).first()

    if not question:
        return {"error": "Không tìm thấy câu hỏi"}
    if not answer:
        return {"error": "Không tìm thấy câu trả lời"}

    if not answer.answer_text:
        return {"error": "Câu trả lời trống"}

    eval_result = generate_evaluation(question.question_text, answer.answer_text)

    # Tính điểm
    score = eval_result.get("score", 0)
    points = float(question.points or 1.0)
    earned = round(score / 100 * points, 2)

    # Cập nhật vào DB
    answer.points_earned = earned
    answer.is_correct = score >= 70
    answer.submitted_at = datetime.utcnow()
    db.add(answer)
    db.commit()

    return {
        "answer_id": answer_id,
        "question": question.question_text,
        "answer": answer.answer_text,
        "score": score,
        "earned_points": earned,
        "comment": eval_result.get("comment", ""),
        "suggestion": eval_result.get("suggestion", "")
    }


def evaluate_test_result(result_id: int, db) -> dict:
    result = db.query(TestResult).filter(TestResult.result_id == result_id).first()
    if not result:
        return {"error": "Không tìm thấy bài làm."}

    answers = db.query(QuestionAnswer).filter(QuestionAnswer.result_id == result_id).all()
    if not answers:
        return {"error": "Bài làm không có câu trả lời nào."}

    scores = []
    feedback_list = []

    for ans in answers:
        question = db.query(TestQuestion).filter(TestQuestion.question_id == ans.question_id).first()
        if not question or not ans.answer_text:
            continue

        eval_result = generate_evaluation(question.question_text, ans.answer_text)

        # Chấm điểm
        score = eval_result.get("score", 0)
        points = float(question.points or 1.0)
        earned = round(score / 100 * points, 2)

        ans.points_earned = earned
        ans.is_correct = score >= 70
        ans.submitted_at = datetime.utcnow()
        db.add(ans)

        scores.append(score)  # <-- Chấm theo thang điểm 100, lưu để tính trung bình
        feedback_list.append(f"Q{question.order_index}: {eval_result.get('comment', '')}")

    db.commit()

    # Tổng & trung bình
    total_score = round(sum(scores), 2)
    average_score = round(total_score / len(scores), 2)

    # Đánh giá đạt hay không: trung bình >= 60
    passing_score = 60
    passed = average_score >= passing_score

    # Cập nhật test_results
    result.total_score = total_score
    result.percentage = average_score
    result.passed = passed
    result.graded_at = datetime.utcnow()
    result.feedback = "\n".join(feedback_list)
    db.add(result)
    db.commit()

    return {
        "result_id": result_id,
        "total_score": total_score,
        "average_score": average_score,
        "passed": passed,
        "feedback": feedback_list
    }



def get_answer_details(result_id: int, db: Session):
    result = db.query(TestResult).filter(TestResult.result_id == result_id).first()
    if not result:
        return {"error": "Không tìm thấy bài làm."}

    answers = (
        db.query(QuestionAnswer)
        .filter(QuestionAnswer.result_id == result_id)
        .order_by(QuestionAnswer.answer_id)
        .all()
    )

    if not answers:
        return {"error": "Không có câu trả lời nào."}

    details = []
    for answer in answers:
        question = db.query(TestQuestion).filter(TestQuestion.question_id == answer.question_id).first()
        details.append({
            "question_id": question.question_id,
            "question_text": question.question_text,
            "answer_id": answer.answer_id,
            "answer_text": answer.answer_text,
            "score": answer.points_earned,
            "is_correct": answer.is_correct,
            "submitted_at": answer.submitted_at,
            "comment": getattr(answer, "comment", ""),        
            "suggestion": getattr(answer, "suggestion", "")   
        })

    return {
        "result_id": result_id,
        "test_id": result.test_id,
        "questions_and_answers": details
    }


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

