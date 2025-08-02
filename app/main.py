from fastapi import FastAPI, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from app.db import get_db
from app.utils import (
    get_job, get_or_create_job_test, create_question,
    generate_questions_from_jd, evaluate_answer_llm,
    get_answer_by_result_question, get_answer_by_id
)
from app.models import TestQuestion, JobTest, Job
from app.utils import GenerateQuestionRequest, QuestionCreate, EvaluateAnswerRequest
from typing import List

app = FastAPI(title="JD AI Interview Question API")

api_prefix = "/api/v1/ai"

# 1. Generate questions from single JD
@app.post(f"{api_prefix}/generate-interview-questions")
def generate_interview_questions(payload: GenerateQuestionRequest, db: Session = Depends(get_db)):
    job = get_job(db, payload.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    questions = generate_questions_from_jd(job.description or "")
    return {"job_id": payload.job_id, "questions": questions}

# 2. Bulk generate for multiple jobs (example)
@app.post(f"{api_prefix}/questions/bulk-generate")
def bulk_generate_questions(job_ids: List[int], db: Session = Depends(get_db)):
    results = []
    for job_id in job_ids:
        job = get_job(db, job_id)
        if not job:
            continue
        qs = generate_questions_from_jd(job.description or "")
        results.append({"job_id": job_id, "questions": qs})
    return {"results": results}

# 3. Customize questions (HR submit new ones)
@app.post(f"{api_prefix}/customize-questions")
def customize_questions(payload: QuestionCreate, db: Session = Depends(get_db)):
    test = db.query(JobTest).filter(JobTest.test_id == payload.test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    q = create_question(db, payload.test_id, payload.question_text, payload.explanation)
    return {"question_id": q.question_id, "message": "Question saved"}

# 4. Update existing question
@app.put(f"{api_prefix}/questions/{{question_id}}/customize")
def update_question(question_id: int = Path(...), payload: QuestionCreate = Depends(), db: Session = Depends(get_db)):
    q = db.query(TestQuestion).filter(TestQuestion.question_id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    q.question_text = payload.question_text
    q.explanation = payload.explanation
    db.commit()
    return {"message": "Question updated", "question_id": q.question_id}

# 5. Get question templates (demo hardcoded or rule-based)
@app.get(f"{api_prefix}/question-templates")
def get_question_templates():
    return {
        "templates": [
            "What challenges have you faced in [ROLE]?",
            "How would you approach [TASK] described in the JD?",
            "Give an example of solving a real-world problem relevant to this role."
        ]
    }

# 6. Validate answer using LLM
@app.post(f"{api_prefix}/questions/validate")
def validate_answer(req: EvaluateAnswerRequest, db: Session = Depends(get_db)):
    q = db.query(TestQuestion).filter(TestQuestion.question_id == req.question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    test = db.query(JobTest).filter(JobTest.test_id == q.test_id).first()
    job = db.query(Job).filter(Job.job_id == (test.job_id if test else None)).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    ans = get_answer_by_result_question(db, req.result_id, req.question_id)
    if not ans:
        raise HTTPException(status_code=404, detail="Answer not found")

    result = evaluate_answer_llm(q.question_text, ans.answer_text, job.description or "")
    return {
        "question_id": q.question_id,
        "answer_id": ans.answer_id,
        "score": result["score"],
        "rationale": result["rationale"]
    }
