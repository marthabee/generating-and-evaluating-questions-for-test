# Hệ thống sinh và đánh giá câu hỏi phỏng vấn từ JD

Backend này cung cấp các API dùng AI để:
- Sinh câu hỏi phỏng vấn từ bản mô tả công việc (JD)
- Tùy chỉnh và lưu câu hỏi cho từng bài test
- Đánh giá câu trả lời của ứng viên bằng API Groq (LLaMA)

## 🚀 Công nghệ sử dụng
- **FastAPI** (Python 3.10+)
- **PostgreSQL** (chạy bằng Docker)
- **SQLAlchemy ORM**
- **LLaMA-3 thông qua Groq API**

---

## 🔧 Hướng dẫn cài đặt

### 1. Tạo môi trường ảo
```bash
cd thu_muc_du_an
python -m venv venv
source venv/bin/activate  # hoặc .\venv\Scripts\activate trên Windows
```

### 2. Cài thư viện cần thiết
```bash
pip install -r requirements.txt
```

### 3. Tạo file cấu hình `.env`
```env
DATABASE_URL=postgresql://admin:your_secure_password@localhost:5432/ai_match_db
LLM_API_URL=https://api.groq.com/openai/v1/chat/completions
LLM_MODEL_NAME=llama3-8b-8192
GROQ_API_KEY=your_groq_api_key
```

### 4. Chạy PostgreSQL bằng Docker
```bash
docker run -d \
  --name postgres \
  -e POSTGRES_DB=ai_match_db \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=your_secure_password \
  -p 5432:5432 \
  postgres:15
```

(Có thể thêm `pgvector` nếu cần embedding)
```bash
docker exec -it postgres bash
apt update && apt install -y postgresql-15-pgvector
psql -U admin -d ai_match_db -c "CREATE EXTENSION vector;"
```

### 5. Khởi tạo bảng dữ liệu
```bash
python
>>> from app.db import Base, engine
>>> Base.metadata.create_all(bind=engine)
```

### 6. Khởi chạy server
```bash
uvicorn app.main:app --reload
```
Truy cập tại: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📘 Danh sách API chính

### Sinh câu hỏi
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/api/v1/ai/generate-interview-questions` | Sinh câu hỏi từ 1 JD |
| POST | `/api/v1/ai/questions/bulk-generate` | Sinh câu hỏi từ nhiều JD |

### Tùy chỉnh câu hỏi
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/api/v1/ai/customize-questions` | Tạo câu hỏi tùy chỉnh |
| PUT  | `/api/v1/ai/questions/{questionId}/customize` | Cập nhật nội dung câu hỏi |

### Mẫu câu hỏi & đánh giá
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET  | `/api/v1/ai/question-templates` | Lấy danh sách câu hỏi mẫu |
| POST | `/api/v1/ai/questions/validate` | Đánh giá câu trả lời của ứng viên |
