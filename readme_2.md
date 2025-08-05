# 🧠 Hướng dẫn tích hợp FE & BE cho hệ thống AI Matching

---

## 🧠 Mục tiêu hệ thống

🔹 Ứng dụng AI nhằm:

- Phân tích mức độ phù hợp giữa **CV ứng viên** và **Job Description (JD)**.
- Gợi ý việc làm phù hợp.
- Sinh đánh giá AI tự động cho đơn ứng tuyển.

---

## 📌 Hướng dẫn Frontend (FE)

### 1. API So khớp CV & JD

- **POST** `/api/v1/ai/calculate-match`
- **Body**:

```json
{
  "cv_id": 123,
  "job_id": 456
}
```

- **Response**:

```json
{
  "match_id": 1,
  "job_id": 456,
  "candidate_id": 78,
  "cv_id": 123,
  "overall_similarity": 0.82,
  "mo_ta_ban_than_similarity": 0.76,
  "ky_nang_similarity": 0.85,
  "kinh_nghiem_similarity": 0.80,
  "hoc_van_similarity": 0.65
}
```

---

### 2. API Điểm so khớp chi tiết theo phần

- **GET** `/api/v1/ai/similarity`
- **Params**:
  - `cv_id`, `job_id`
  - `section_type`: `full_text`, `ky_nang`, `kinh_nghiem_lam_viec`, `hoc_van`, `du_an`, `weighted`
- **Response**:

```json
{
  "cv_id": 123,
  "job_id": 456,
  "section_type": "ky_nang",
  "similarity_score": 0.85
}
```

---

### 3. API Gợi ý việc làm

- **GET** `/api/v1/ai/job-recommendations/{candidate_id}`
- **Params**: `top_k`
- **Response**:

```json
{
  "candidate_id": 78,
  "cv_id": 123,
  "top_k": 5,
  "recommendations": [
    {
      "job_id": 456,
      "title": "Data Scientist",
      "group": "ABC Corp",
      "overall_similarity": 0.87
    }
  ]
}
```

---

### 4. API Phân tích AI đơn ứng tuyển

- **GET** `/api/v1/ai/match-analysis/{application_id}`
- **Response**:

```json
{
  "application_id": 999,
  "cv_id": 123,
  "job_id": 456,
  "language_detected": "vi",
  "overall": 0.81,
  "skills": 0.84,
  "experience": 0.78,
  "education": 0.60,
  "reasoning": "## Điểm phù hợp..."
}
```

---

## 📘 API tạo câu hỏi & đánh giá ứng viên từ JD

### 1. Tạo câu hỏi phỏng vấn từ JD

- **POST** `/api/v1/ai/generate-interview-questions`
- **Body**:

```json
{
  "job_id": 123
}
```

- **Response**:

```json
{
  "job_id": 123,
  "questions": [
    "Bạn đã từng giải quyết tình huống nào tương tự như yêu cầu trong JD chưa?",
    "..."
  ]
}
```

### 2. Tạo câu hỏi hàng loạt

- **POST** `/api/v1/ai/questions/bulk-generate`
- **Body**:

```json
[123, 456, 789]
```

- **Response**:

```json
{
  "results": [
    { "job_id": 123, "questions": [...] }
  ]
}
```

### 3. Tuỳ chỉnh / cập nhật câu hỏi

- **POST** `/api/v1/ai/customize-questions`

```json
{
  "test_id": 1,
  "question_text": "Mô tả cách bạn xử lý một dự án lớn.",
  "explanation": "Đánh giá tư duy quản lý."
}
```

- **PUT** `/api/v1/ai/questions/{question_id}/customize`

### 4. Đánh giá câu trả lời bằng LLM

- **POST** `/api/v1/ai/questions/validate`

```json
{
  "question_id": 10,
  "result_id": 200
}
```

- **Response**:

```json
{
  "question_id": 10,
  "answer_id": 305,
  "score": 0.75,
  "rationale": "Câu trả lời phù hợp các yêu cầu chính của JD ở mức khá (demo)."
}
```

---

## 🧠 Lưu ý kỹ thuật

- Hệ thống sử dụng:
  - **SQLAlchemy** ORM
  - **Groq API** (LLM: llama3-8b-8192)
  - Phát hiện ngôn ngữ bằng `langdetect`
- Các bảng/schema:
  - `jobs`, `job_tests`, `test_questions`, `question_answers`, `test_results`

---

## 📝 Ghi chú DB

| Mục           | Bảng                                       | Mô tả                |
| ------------- | ------------------------------------------ | -------------------- |
| CV            | cv\_content, cv\_embeddings                | Nội dung + embedding |
| JD            | jobs, job\_embeddings                      | JD và embedding      |
| Skills        | job\_skills, candidate\_skills             | Gộp từ parse và DB   |
| Match         | vector\_matches                            | So khớp cosine       |
| Phân tích AI  | applications.ai\_analysis                  | Markdown lý do AI    |
| Đánh giá test | job\_tests, test\_questions, test\_results | Đề bài & kết quả     |

---

## ✅ FE & BE Checklist

### Frontend:

-

### Backend:

-

