# 🎓 RAG based Question paper generator

A full-stack web application that uses **Retrieval-Augmented Generation (RAG)** to generate university question papers, revision notes, AI tutoring, competitive exam prep, and full mock tests — all strictly based on uploaded syllabus content.

---

## ✨ Features

| Tool | Description |
|---|---|
| 📄 **Question Papers** | Generate full university exam papers (Part A/B/C) from uploaded syllabus |
| 🏆 **Competitive Exams** | NEET/JEE style MCQ sets for entrance exam preparation |
| 🤖 **AI Tutor** | Step-by-step concept explanations based on your notes |
| 📝 **Revision Notes** | Concise bullet-point exam-focused notes for any topic |
| 🧪 **Full Mock Test** | Attempt a test, get AI-scored results, analytics & recommendations |

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| LLM | Groq API — `llama-3.3-70b-versatile` |
| Embeddings | `sentence-transformers` — `all-MiniLM-L6-v2` |
| Vector DB | FAISS (local, CPU) |
| Document Parsing | PyPDF2, python-docx |
| PDF Export | ReportLab |
| Frontend | Jinja2, HTML, CSS, Vanilla JS |
| Auth | Flask sessions |

---

## 🔄 RAG Pipeline

```
Upload Syllabus (PDF / DOCX / TXT)
        ↓
1. Load & Clean — extract raw text
        ↓
2. Chunk — split into 500-word chunks (50-word overlap)
        ↓
3. Embed — sentence-transformers → 384-dim vectors
        ↓
4. Store — FAISS IndexFlatIP (cosine similarity, saved locally)
        ↓
Enter Topic / Query
        ↓
5. Retrieve — embed query → top-5 similar chunks
        ↓
6. Augment — join chunks into context string
        ↓
7. Generate — Groq LLM generates output from context only
        ↓
Structured output (JSON → formatted paper / notes / answer)
```

> ⚠️ The LLM is strictly instructed to use **only** the retrieved context — no hallucination from external knowledge.

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

### 2. Create a virtual environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file in the root directory:

```
GROQ_API_KEY=your_groq_api_key_here
```

Get a free Groq API key at [https://console.groq.com](https://console.groq.com)

### 5. Run the app

```bash
python app.py
```

Open [http://localhost:10000](http://localhost:10000)

---

## 🔑 Default Login Credentials

| Username | Password |
|---|---|
| `admin` | `admin123` |
| `student` | `student123` |

You can also register a new account from the login page.

---

## 📁 Project Structure

```
├── app.py                        # Flask routes and app config
├── question_generator.py         # LLM prompt functions (Groq)
├── rag_pipeline.py               # RAG: load, chunk, embed, store, retrieve
├── requirements.txt
├── .env                          # API keys (not committed)
├── .gitignore
├── static/
│   └── style.css
├── templates/
│   ├── login.html
│   ├── register.html
│   ├── dashboard_base.html       # Shared sidebar layout
│   ├── fullpage_base.html        # Full-page layout (no sidebar)
│   ├── index.html                # Dashboard home
│   ├── papers.html               # Question paper generator
│   ├── competitive.html
│   ├── competitive_result.html
│   ├── tutor.html
│   ├── revision.html
│   ├── fulltest.html
│   ├── fulltest_questions.html
│   ├── fulltest_result.html
│   └── result.html
├── uploads/                      # Temp file storage (auto-deleted)
├── papers/                       # Generated papers (UUID-named)
└── vector_store/                 # FAISS indexes (per session)
```

---

## 📦 Requirements

```
Flask
gunicorn
reportlab
PyPDF2
python-docx
groq
python-dotenv
sentence-transformers
faiss-cpu
numpy
tf-keras
```

---

## 🛡️ Security Notes

- Uploaded files are **deleted immediately** after text extraction
- Each paper is stored with a **UUID** to prevent session conflicts
- `.env` is excluded from version control via `.gitignore`
- Passwords are stored in-memory (for demo — use a database for production)

---

## 📄 License

This project is open source. Feel free to use and modify as needed.
