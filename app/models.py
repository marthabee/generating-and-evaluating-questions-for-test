from sqlalchemy import ARRAY, Column, BigInteger, Date, Integer, String, Text, ForeignKey, Boolean, DECIMAL, TIMESTAMP, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"
    job_id = Column(BigInteger, primary_key=True)
    recruiter_id = Column(BigInteger, ForeignKey("users.user_id"))
    company_id = Column(BigInteger, ForeignKey("companies.company_id", ondelete="CASCADE"))
    title = Column(String(200))
    description = Column(Text)
    requirements = Column(Text)
    responsibilities = Column(Text)
    experience_level = Column(String(20))
    employment_type = Column(String(20))
    salary_min = Column(DECIMAL(12,2))
    salary_max = Column(DECIMAL(12,2))
    city_id = Column(Integer)
    work_arrangement = Column(String(20))
    min_experience_years = Column(Integer)
    max_experience_years = Column(Integer)
    category = Column(String(100))
    education_requirements = Column(Text)
    language_requirements = Column(ARRAY(String))
    application_deadline = Column(Date)
    

class JobTest(Base):
    __tablename__ = "job_tests"
    test_id = Column(BigInteger, primary_key=True)
    job_id = Column(BigInteger, ForeignKey("jobs.job_id", ondelete="CASCADE"))
    test_name = Column(String(200))
    test_type = Column(String(30))
    difficulty_level = Column(String(20))
    duration_minutes = Column(Integer)
    passing_score = Column(DECIMAL(5,2))
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow)

class TestQuestion(Base):
    __tablename__ = "test_questions"
    question_id = Column(BigInteger, primary_key=True)
    test_id = Column(BigInteger, ForeignKey("job_tests.test_id", ondelete="CASCADE"))
    question_text = Column(Text)
    question_type = Column(String(30))
    points = Column(DECIMAL(5,2))
    time_limit_seconds = Column(Integer)
    order_index = Column(Integer)
    explanation = Column(Text)
    required = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

class QuestionAnswer(Base):
    __tablename__ = "question_answers"
    answer_id = Column(BigInteger, primary_key=True)
    result_id = Column(BigInteger, ForeignKey("test_results.result_id", ondelete="CASCADE"))
    question_id = Column(BigInteger, ForeignKey("test_questions.question_id"))
    answer_text = Column(Text)
    is_correct = Column(Boolean)
    points_earned = Column(DECIMAL(5,2))
    time_taken_seconds = Column(Integer)
    submitted_at = Column(TIMESTAMP, default=datetime.utcnow)

class TestResult(Base):
    __tablename__ = "test_results"
    result_id = Column(BigInteger, primary_key=True)
    application_id = Column(BigInteger, ForeignKey("applications.application_id", ondelete="CASCADE"))
    test_id = Column(BigInteger, ForeignKey("job_tests.test_id"))
    start_time = Column(TIMESTAMP)
    submit_time = Column(TIMESTAMP)
    total_score = Column(DECIMAL(5,2))
    percentage = Column(DECIMAL(5,2))
    status = Column(String(20))
    passed = Column(Boolean)
    time_taken_seconds = Column(Integer)
    graded_by = Column(BigInteger, ForeignKey("users.user_id"))
    graded_at = Column(TIMESTAMP)
    feedback = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
