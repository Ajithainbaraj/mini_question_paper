import os
import io
import uuid

from flask import Flask, request, render_template, send_file, session, redirect, url_for
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from rag_pipeline import process_syllabus, get_context_for_query
from question_generator import (
    generate_questions,
    analyze_competitive_exam_topics,
    generate_competitive_questions,
    answer_question,
    generate_revision_notes,
    generate_full_mock_test,
    evaluate_full_mock_test,
)

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["PAPERS_FOLDER"] = "papers"
app.config["VECTOR_STORE"] = "vector_store"

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["PAPERS_FOLDER"], exist_ok=True)

# ── Simple credentials (change as needed) ────────────────────────────────────
USERS = {
    "admin": "admin123",
    "student": "student123",
}

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ── HELPERS ──────────────────────────────────────────────────────────────────
def format_university_paper(college, subject, semester, exam_type, questions,
                             include_blooms=False, include_answer_key=False):
    mcqs   = questions.get("mcqs", [])
    part_b = questions.get("part_b", [])
    part_c = questions.get("part_c", [])

    paper = f"""{college.upper()}
------------------------------------------------------------
B.E / B.Tech – {subject}
Semester: {semester}
Examination: {exam_type}
Time: 3 Hours                         Max Marks: 70
------------------------------------------------------------

PART A – MCQs (10 × 1 = 10 Marks)
------------------------------------------------------------
"""
    answer_key_lines = ["PART A – Answer Key", "-" * 60] if include_answer_key else []

    for i, mcq in enumerate(mcqs[:10], 1):
        bloom = f" [{mcq.get('blooms', '')}]" if include_blooms else ""
        paper += f"{i}. {mcq['question']}{bloom}\n"
        for j, opt in enumerate(mcq["options"]):
            paper += f"   {chr(65+j)}. {opt.lstrip('ABCDabcd.: ').strip()}\n"
        paper += "\n"
        if include_answer_key:
            answer_key_lines.append(f"{i}. {mcq.get('answer', 'N/A')}")

    paper += """
PART B – Answer ANY FIVE questions (8 × 5 = 40 Marks)
------------------------------------------------------------
"""
    if include_answer_key:
        answer_key_lines += ["", "PART B & C – Answer Hints", "-" * 60]

    for i, q in enumerate(part_b[:8], 1):
        bloom = f" [{q.get('blooms', '')}]" if include_blooms else ""
        paper += f"{i}. {q.get('question', q) if isinstance(q, dict) else q}{bloom}\n"
        if include_answer_key and isinstance(q, dict):
            answer_key_lines.append(f"B{i}. {q.get('answer_key', 'N/A')}")

    paper += """
PART C – Answer ALL questions (2 × 10 = 20 Marks)
------------------------------------------------------------
"""
    for i, q in enumerate(part_c[:2], 1):
        bloom = f" [{q.get('blooms', '')}]" if include_blooms else ""
        paper += f"{i}. {q.get('question', q) if isinstance(q, dict) else q}{bloom}\n"
        if include_answer_key and isinstance(q, dict):
            answer_key_lines.append(f"C{i}. {q.get('answer_key', 'N/A')}")

    if include_answer_key and answer_key_lines:
        paper += "\n\n" + "=" * 60 + "\nANSWER KEY\n" + "=" * 60 + "\n"
        paper += "\n".join(answer_key_lines) + "\n" + "=" * 60 + "\n"

    paper += """
------------------------------------------------------------
End of Question Paper
------------------------------------------------------------
Instructions:
• Answer all questions clearly
• Draw diagrams wherever necessary
"""
    return paper


# ── ROUTES ───────────────────────────────────────────────────────────────────

# LOGIN / LOGOUT
@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("home"))
    error = None
    registered = request.args.get("registered")
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if USERS.get(username) == password:
            session["logged_in"] = True
            session["username"] = username
            return redirect(url_for("home"))
        error = "Invalid username or password. Please try again."
    return render_template("login.html", error=error, registered=registered)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("logged_in"):
        return redirect(url_for("home"))
    error = None
    success = None
    if request.method == "POST":
        fullname = request.form.get("fullname", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")

        if not fullname or not username or not password:
            error = "All fields are required."
        elif username in USERS:
            error = "Username already exists. Please choose another."
        elif password != confirm:
            error = "Passwords do not match."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        else:
            USERS[username] = password
            return redirect(url_for("login") + "?registered=1")

    return render_template("register.html", error=error, success=success)

# 1b. DEDICATED PAPERS PAGE
@app.route("/papers", methods=["GET", "POST"])
@login_required
def papers():
    if request.method == "POST":
        uploaded_file      = request.files.get("syllabus_file")
        college            = request.form.get("college")
        subject            = request.form.get("subject")
        semester           = request.form.get("semester")
        exam_type          = request.form.get("exam_type")
        difficulty         = request.form.get("difficulty", "medium")
        query              = request.form.get("query", subject)
        include_blooms     = request.form.get("include_blooms") == "yes"
        include_answer_key = request.form.get("include_answer_key") == "yes"

        if not uploaded_file or uploaded_file.filename == "":
            return render_template("papers.html", error="Please upload a syllabus file.")

        file_path = os.path.join(app.config["UPLOAD_FOLDER"], uploaded_file.filename)
        uploaded_file.save(file_path)

        try:
            store_dir = os.path.join(app.config["VECTOR_STORE"], str(uuid.uuid4()))
            process_syllabus(file_path, store_dir)
            context = get_context_for_query(query or subject, store_dir, top_k=8)
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

        questions = generate_questions(context, difficulty, include_blooms, include_answer_key)
        result    = format_university_paper(college, subject, semester, exam_type,
                                            questions, include_blooms, include_answer_key)

        paper_id   = str(uuid.uuid4())
        paper_path = os.path.join(app.config["PAPERS_FOLDER"], f"{paper_id}.txt")
        with open(paper_path, "w", encoding="utf-8") as f:
            f.write(result)

        session["paper_id"] = paper_id
        return redirect(url_for("result_page"))

    return render_template("papers.html")


# 1. HOME
@app.route("/", methods=["GET", "POST"])
@login_required
def home():
    if request.method == "POST":
        uploaded_file  = request.files.get("syllabus_file")
        college        = request.form.get("college")
        subject        = request.form.get("subject")
        semester       = request.form.get("semester")
        exam_type      = request.form.get("exam_type")
        difficulty     = request.form.get("difficulty", "medium")
        query          = request.form.get("query", subject)   # topic query for RAG
        include_blooms = request.form.get("include_blooms") == "yes"
        include_answer_key = request.form.get("include_answer_key") == "yes"

        if not uploaded_file or uploaded_file.filename == "":
            return render_template("index.html", error="Please upload a syllabus file.")

        # ── Save upload ──
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], uploaded_file.filename)
        uploaded_file.save(file_path)

        try:
            # ── RAG: process syllabus → vector store ──
            store_dir = os.path.join(app.config["VECTOR_STORE"], str(uuid.uuid4()))
            process_syllabus(file_path, store_dir)

            # ── RAG: retrieve context for query ──
            context = get_context_for_query(query or subject, store_dir, top_k=8)
            print(f"[DEBUG] RAG context retrieved: {len(context)} chars")
            print(f"[DEBUG] Context preview: {context[:300]}")

        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

        # ── Generate questions from retrieved context ──
        questions = generate_questions(context, difficulty, include_blooms, include_answer_key)
        result    = format_university_paper(college, subject, semester, exam_type,
                                            questions, include_blooms, include_answer_key)

        # ── Persist paper with UUID ──
        paper_id   = str(uuid.uuid4())
        paper_path = os.path.join(app.config["PAPERS_FOLDER"], f"{paper_id}.txt")
        with open(paper_path, "w", encoding="utf-8") as f:
            f.write(result)

        session["paper_id"] = paper_id
        return redirect(url_for("result_page"))

    return render_template("index.html")


# 2. RESULT
@app.route("/result")
@login_required
def result_page():
    paper_id = session.get("paper_id")
    if not paper_id:
        return redirect(url_for("home"))

    paper_path = os.path.join(app.config["PAPERS_FOLDER"], f"{paper_id}.txt")
    if not os.path.exists(paper_path):
        return "Session expired or paper not found."

    with open(paper_path, "r", encoding="utf-8") as f:
        paper = f.read()

    return render_template("result.html", result=paper)


# 3. PDF DOWNLOAD
@app.route("/download_pdf")
@login_required
def download_pdf():
    paper_id = session.get("paper_id")
    if not paper_id:
        return "No paper in session.", 400

    paper_path = os.path.join(app.config["PAPERS_FOLDER"], f"{paper_id}.txt")
    if not os.path.exists(paper_path):
        return "Paper not found.", 404

    with open(paper_path, "r", encoding="utf-8") as f:
        content = f.read()

    buffer = io.BytesIO()
    pdf    = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    margin, y, line_height = 50, height - 50, 14

    pdf.setFont("Times-Roman", 11)
    for line in content.split("\n"):
        if y < 60:
            pdf.showPage()
            pdf.setFont("Times-Roman", 11)
            y = height - 50
        pdf.drawString(margin, y, line)
        y -= line_height

    pdf.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True,
                     download_name="Question_Paper.pdf",
                     mimetype="application/pdf")


# 4. COMPETITIVE EXAM
@app.route("/competitive", methods=["GET", "POST"])
@login_required
def competitive_exam():
    if request.method == "POST":
        subject       = request.form.get("subject")
        topics        = request.form.get("topics")
        exam_type     = request.form.get("exam_type")
        difficulty    = request.form.get("difficulty", "medium")
        num_questions = int(request.form.get("num_questions", 20))

        if not subject or not topics:
            return render_template("competitive.html",
                                   error="Please provide both subject and topics.")

        questions_text = generate_competitive_questions(
            subject, topics, exam_type, difficulty, num_questions
        )
        session["competitive_questions"] = questions_text
        return render_template("competitive_result.html",
                               questions_text=questions_text,
                               subject=subject, exam_type=exam_type,
                               difficulty=difficulty, total_questions=num_questions)

    return render_template("competitive.html")


@app.route("/competitive_download")
def competitive_download():
    questions_text = session.get("competitive_questions")
    if not questions_text:
        return "No questions available.", 400

    buffer = io.BytesIO()
    buffer.write(f"COMPETITIVE EXAM QUESTIONS\n{'='*40}\n\n{questions_text}".encode("utf-8"))
    buffer.seek(0)
    return send_file(buffer, as_attachment=True,
                     download_name="Competitive_Questions.txt",
                     mimetype="text/plain")


# 5. AI TUTOR
@app.route("/tutor", methods=["GET", "POST"])
@login_required
def tutor():
    answer = None
    question = None

    if request.method == "POST":
        uploaded_file = request.files.get("syllabus_file")
        question = request.form.get("question", "").strip()

        if not uploaded_file or uploaded_file.filename == "":
            return render_template("tutor.html", error="Please upload a file.")
        if not question:
            return render_template("tutor.html", error="Please enter a question.")

        file_path = os.path.join(app.config["UPLOAD_FOLDER"], uploaded_file.filename)
        uploaded_file.save(file_path)

        try:
            store_dir = os.path.join(app.config["VECTOR_STORE"], "tutor_" + str(uuid.uuid4()))
            process_syllabus(file_path, store_dir)
            context = get_context_for_query(question, store_dir, top_k=5)
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

        answer = answer_question(context, question)

    return render_template("tutor.html", answer=answer, question=question)


# 6. REVISION NOTES
@app.route("/revision", methods=["GET", "POST"])
@login_required
def revision():
    notes = None
    topic = None

    if request.method == "POST":
        uploaded_file = request.files.get("syllabus_file")
        topic = request.form.get("topic", "").strip()

        if not uploaded_file or uploaded_file.filename == "":
            return render_template("revision.html", error="Please upload a file.")
        if not topic:
            return render_template("revision.html", error="Please enter a topic.")

        file_path = os.path.join(app.config["UPLOAD_FOLDER"], uploaded_file.filename)
        uploaded_file.save(file_path)

        try:
            store_dir = os.path.join(app.config["VECTOR_STORE"], "revision_" + str(uuid.uuid4()))
            process_syllabus(file_path, store_dir)
            context = get_context_for_query(topic, store_dir, top_k=5)
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

        notes = generate_revision_notes(context, topic)

    return render_template("revision.html", notes=notes, topic=topic)



@app.route("/fulltest", methods=["GET", "POST"])
@login_required
def fulltest():
    if request.method == "POST":
        uploaded_file = request.files.get("syllabus_file")
        topic      = request.form.get("topic", "").strip()
        difficulty = request.form.get("difficulty", "medium")

        if not uploaded_file or uploaded_file.filename == "":
            return render_template("fulltest.html", error="Please upload a file.")
        if not topic:
            return render_template("fulltest.html", error="Please enter a topic.")

        file_path = os.path.join(app.config["UPLOAD_FOLDER"], uploaded_file.filename)
        uploaded_file.save(file_path)

        try:
            store_dir = os.path.join(app.config["VECTOR_STORE"], "full_" + str(uuid.uuid4()))
            process_syllabus(file_path, store_dir)
            context = get_context_for_query(topic, store_dir, top_k=6)
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

        test_data = generate_full_mock_test(context, topic, difficulty)
        session["full_test_data"] = test_data
        session["full_test_context"] = context[:3000]
        session["full_test_topic"] = topic
        session["full_test_difficulty"] = difficulty

        return render_template("fulltest_questions.html",
                               test_data=test_data, topic=topic, difficulty=difficulty)

    return render_template("fulltest.html")


@app.route("/fulltest/submit", methods=["POST"])
def fulltest_submit():
    test_data  = session.get("full_test_data", {})
    context    = session.get("full_test_context", "")
    topic      = session.get("full_test_topic", "")
    difficulty = session.get("full_test_difficulty", "medium")

    if not test_data:
        return redirect(url_for("fulltest"))

    # Collect all answers from form
    user_answers = {}
    for q in test_data.get("mcqs", []):
        user_answers[str(q["id"])] = request.form.get(f"ans_{q['id']}", "")
    for q in test_data.get("short", []):
        user_answers[str(q["id"])] = request.form.get(f"ans_{q['id']}", "")

    results = evaluate_full_mock_test(test_data, user_answers, context)
    show_answers = request.form.get("show_answers") == "yes"

    return render_template("fulltest_result.html",
                           results=results, topic=topic,
                           difficulty=difficulty, show_answers=show_answers,
                           test_data=test_data)


# ── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
