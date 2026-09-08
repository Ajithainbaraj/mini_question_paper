import os
import io
import uuid
import json
import hashlib

from flask import Flask, request, render_template, send_file, session, redirect, url_for
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from authlib.integrations.flask_client import OAuth

from rag_pipeline import process_syllabus, get_context_for_query
from question_generator import (
    generate_questions,
    analyze_competitive_exam_topics,
    generate_competitive_questions,
    answer_question,
    generate_revision_notes,
    generate_full_mock_test,
    evaluate_full_mock_test,
    extract_questions_from_paper,
    classify_questions_to_chapters,
    build_chapter_analysis,
    fetch_exam_pattern,
    analyze_math_question_bank,
    find_question_variations,
    generate_question_variations,
    build_variation_analytics,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["PAPERS_FOLDER"] = "papers"
app.config["VECTOR_STORE"] = "vector_store"

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["PAPERS_FOLDER"], exist_ok=True)

# ── OAuth setup ───────────────────────────────────────────────────────────────
oauth = OAuth(app)

oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

oauth.register(
    name="github",
    client_id=os.environ.get("GITHUB_CLIENT_ID"),
    client_secret=os.environ.get("GITHUB_CLIENT_SECRET"),
    access_token_url="https://github.com/login/oauth/access_token",
    authorize_url="https://github.com/login/oauth/authorize",
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "user:email"},
)

# ── Persistent user store (JSON file) ────────────────────────────────────────
USERS_FILE = "users.json"

def _load_users() -> dict:
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    # Seed default accounts on first run
    defaults = {
        "admin":   _hash_pw("admin123"),
        "student": _hash_pw("student123"),
    }
    _save_users(defaults)
    return defaults

def _save_users(users: dict):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def _hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def _check_pw(password: str, hashed: str) -> bool:
    return _hash_pw(password) == hashed

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
        users = _load_users()
        if username in users and _check_pw(password, users[username]):
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

        users = _load_users()
        if not fullname or not username or not password:
            error = "All fields are required."
        elif username in users:
            error = "Username already exists. Please choose another."
        elif password != confirm:
            error = "Passwords do not match."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        else:
            users[username] = _hash_pw(password)
            _save_users(users)
            return redirect(url_for("login") + "?registered=1")

    return render_template("register.html", error=error, success=success)


# ── Google OAuth ──────────────────────────────────────────────────────────────
@app.route("/login/google")
def login_google():
    redirect_uri = url_for("auth_google", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@app.route("/auth/google")
def auth_google():
    try:
        token = oauth.google.authorize_access_token()
        userinfo = token.get("userinfo") or oauth.google.userinfo()
        email = userinfo.get("email", "")
        name  = userinfo.get("name", email.split("@")[0])
        username = f"google_{email.replace('@','_').replace('.','_')}"

        users = _load_users()
        if username not in users:
            users[username] = _hash_pw(uuid.uuid4().hex)  # random pw, OAuth only
            _save_users(users)

        session["logged_in"] = True
        session["username"] = name or username
        return redirect(url_for("home"))
    except Exception as e:
        return render_template("login.html", error=f"Google login failed: {str(e)[:100]}")


# ── GitHub OAuth ──────────────────────────────────────────────────────────────
@app.route("/login/github")
def login_github():
    redirect_uri = url_for("auth_github", _external=True)
    return oauth.github.authorize_redirect(redirect_uri)

@app.route("/auth/github")
def auth_github():
    try:
        token = oauth.github.authorize_access_token()
        resp = oauth.github.get("user", token=token)
        profile = resp.json()
        username = f"github_{profile.get('login', uuid.uuid4().hex)}"
        display  = profile.get("name") or profile.get("login") or username

        users = _load_users()
        if username not in users:
            users[username] = _hash_pw(uuid.uuid4().hex)
            _save_users(users)

        session["logged_in"] = True
        session["username"] = display
        return redirect(url_for("home"))
    except Exception as e:
        return render_template("login.html", error=f"GitHub login failed: {str(e)[:100]}")

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


# ── CHAPTER ANALYZER ─────────────────────────────────────────────────────────
@app.route("/chapter-analyzer", methods=["GET", "POST"])
@login_required
def chapter_analyzer():
    analysis = None
    error = None

    if request.method == "POST":
        # Clear any previous analysis from session before starting new one
        session.pop("chapter_analysis", None)
        session.pop("chapter_analysis_id", None)
        
        syllabus_file  = request.files.get("syllabus_file")
        paper_file     = request.files.get("paper_file")

        if not syllabus_file or syllabus_file.filename == "":
            error = "Please upload a syllabus file."
        elif not paper_file or paper_file.filename == "":
            error = "Please upload a question paper file."
        else:
            # Generate unique analysis ID
            analysis_id = str(uuid.uuid4())
            
            syl_path   = os.path.join(app.config["UPLOAD_FOLDER"], f"syl_{analysis_id}_{syllabus_file.filename}")
            paper_path = os.path.join(app.config["UPLOAD_FOLDER"], f"paper_{analysis_id}_{paper_file.filename}")
            syllabus_file.save(syl_path)
            paper_file.save(paper_path)

            try:
                # 1. Build vector store from syllabus with unique ID
                store_dir = os.path.join(app.config["VECTOR_STORE"], f"analyzer_{analysis_id}")
                process_syllabus(syl_path, store_dir)

                # 2. Load syllabus chunks for chapter classification
                from rag_pipeline import load_vector_store as _lv
                _, syllabus_chunks = _lv(store_dir)

                # 3. Extract text from question paper
                from rag_pipeline import load_document, clean_text
                paper_text = load_document(paper_path)

                # 4. Extract individual questions using LLM
                questions = extract_questions_from_paper(paper_text)
                if not questions:
                    error = "Could not extract questions from the paper. Please ensure it is a readable PDF/text file."
                else:
                    # 5. Classify questions to chapters using syllabus
                    classified = classify_questions_to_chapters(questions, syllabus_chunks)

                    # 6. Build analytics
                    analysis = build_chapter_analysis(classified)
                    
                    # Store with unique ID in session
                    session["chapter_analysis"] = analysis
                    session["chapter_analysis_id"] = analysis_id

            except Exception as e:
                error = f"Analysis failed: {str(e)[:200]}"
            finally:
                # Clean up temporary files
                for p in [syl_path, paper_path]:
                    if os.path.exists(p):
                        os.remove(p)
                
                # Clean up vector store directory if analysis failed
                if error and store_dir and os.path.exists(store_dir):
                    import shutil
                    shutil.rmtree(store_dir, ignore_errors=True)

    else:
        # GET request - check if we should show previous analysis or clean form
        # Only restore analysis if explicitly requested via query param
        if request.args.get("show") == "current":
            analysis = session.get("chapter_analysis")
        else:
            # Clean state for new analysis
            pass

    return render_template("chapter_analyzer.html", analysis=analysis, error=error)


@app.route("/chapter-analyzer/new", methods=["GET"])
@login_required
def chapter_analyzer_new():
    """Clear session and start a new analysis."""
    session.pop("chapter_analysis", None)
    session.pop("chapter_analysis_id", None)
    return redirect(url_for("chapter_analyzer"))


@app.route("/chapter-analyzer/current", methods=["GET"])
@login_required
def chapter_analyzer_current():
    """View current analysis results."""
    return redirect(url_for("chapter_analyzer", show="current"))


@app.route("/chapter-analyzer/download-report")
@login_required
def chapter_analyzer_report():
    """Generate and download a PDF analysis report."""
    analysis = session.get("chapter_analysis")
    if not analysis:
        return "No analysis in session.", 400

    buffer = io.BytesIO()
    pdf    = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 50
    margin = 50
    lh = 16

    def write_line(text, bold=False, indent=0, size=11):
        nonlocal y
        if y < 70:
            pdf.showPage()
            pdf.setFont("Times-Bold" if bold else "Times-Roman", size)
            y = height - 50
        pdf.setFont("Times-Bold" if bold else "Times-Roman", size)
        pdf.drawString(margin + indent, y, text[:110])
        y -= lh

    write_line("CHAPTER-WISE QUESTION PAPER ANALYSIS REPORT", bold=True, size=14)
    write_line("=" * 70)
    y -= 6

    write_line("SUMMARY", bold=True, size=12)
    write_line(f"  Total Questions   : {analysis['total_questions']}")
    write_line(f"  Total Chapters    : {analysis['total_chapters']}")
    write_line(f"  Most Asked Chapter: {analysis['most_asked_chapter']}")
    write_line(f"  Least Asked Chapter: {analysis['least_asked_chapter']}")
    y -= 10

    write_line("CHAPTER-WISE DISTRIBUTION", bold=True, size=12)
    write_line("-" * 60)
    for ch in analysis["chapters"]:
        pct = round(ch["count"] / analysis["total_questions"] * 100, 1) if analysis["total_questions"] else 0
        write_line(f"  {ch['chapter'][:50]:<50} {ch['count']} Q  ({pct}%)")
    y -= 10

    write_line("SUBJECT DISTRIBUTION", bold=True, size=12)
    write_line("-" * 60)
    for sub in analysis["subjects"]:
        pct = round(sub["count"] / analysis["total_questions"] * 100, 1) if analysis["total_questions"] else 0
        write_line(f"  {sub['subject']:<40} {sub['count']} Q  ({pct}%)")
    y -= 10

    write_line("COMPLETE QUESTION MAPPING", bold=True, size=12)
    write_line("-" * 60)
    for q in analysis["questions"]:
        write_line(f"  Q{q['question_no']}  [{q['subject']} › {q['chapter']}]", bold=True)
        # wrap question text
        words = q["question"].split()
        line = "     "
        for w in words:
            if len(line) + len(w) + 1 > 100:
                write_line(line)
                line = "     " + w + " "
            else:
                line += w + " "
        if line.strip():
            write_line(line)
        y -= 4

    pdf.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True,
                     download_name="Chapter_Analysis_Report.pdf",
                     mimetype="application/pdf")


# ── EXAM PATTERN ─────────────────────────────────────────────────────────────
@app.route("/exam-pattern", methods=["GET", "POST"])
@login_required
def exam_pattern():
    pattern = None
    error   = None
    query   = ""

    if request.method == "POST":
        query = request.form.get("query", "").strip()
        if not query:
            error = "Please enter an exam name or query."
        else:
            try:
                pattern = fetch_exam_pattern(query)
                if pattern.get("error"):
                    error   = pattern["error"]
                    pattern = None
                else:
                    session["exam_pattern"] = pattern
                    session["exam_query"]   = query
            except Exception as e:
                error = f"Could not fetch exam pattern: {str(e)[:150]}"

    # Restore from session on GET if available
    if request.method == "GET":
        pattern = session.get("exam_pattern")
        query   = session.get("exam_query", "")

    return render_template("exam_pattern.html", pattern=pattern, error=error, query=query)


@app.route("/exam-pattern/clear")
@login_required
def exam_pattern_clear():
    session.pop("exam_pattern", None)
    session.pop("exam_query", None)
    return redirect(url_for("exam_pattern"))


@app.route("/exam-pattern/download")
@login_required
def exam_pattern_download():
    """Download exam pattern blueprint as PDF."""
    pattern = session.get("exam_pattern")
    if not pattern:
        return "No pattern in session.", 400

    buffer = io.BytesIO()
    pdf    = canvas.Canvas(buffer, pagesize=letter)
    w, h   = letter
    y      = h - 50
    margin = 50
    lh     = 15

    def ln(text, bold=False, size=11, indent=0):
        nonlocal y
        if y < 70:
            pdf.showPage()
            y = h - 50
        pdf.setFont("Times-Bold" if bold else "Times-Roman", size)
        pdf.drawString(margin + indent, y, str(text)[:100])
        y -= lh

    ln("EXAM PATTERN BLUEPRINT — EduAI", bold=True, size=14)
    ln("=" * 65)
    y -= 4

    ln(f"Exam  : {pattern.get('exam_name','')}", bold=True, size=12)
    ln(f"Body  : {pattern.get('conducting_body','')}")
    ln(f"Year  : {pattern.get('year','')}  |  Level: {pattern.get('level','')}")
    ln(f"Mode  : {pattern.get('exam_mode','')}  |  Duration: {pattern.get('duration_minutes','')} minutes")
    ln(f"Marks : {pattern.get('total_marks','')}  |  Questions: {pattern.get('total_questions','')}")
    ln(f"Negative Marking: {pattern.get('negative_marking','')}")
    y -= 6

    if pattern.get("exam_stages"):
        ln("EXAM STAGES", bold=True)
        for s in pattern["exam_stages"]:
            ln(f"  • {s}", indent=8)
        y -= 4

    ln("SECTION-WISE BREAKDOWN", bold=True)
    ln("-" * 60)
    for sec in pattern.get("sections", []):
        ln(f"  {sec.get('name',''):<30} {sec.get('questions','')} Q   {sec.get('marks','')} Marks", indent=8)
    y -= 6

    if pattern.get("important_notes"):
        ln("IMPORTANT NOTES", bold=True)
        for note in pattern["important_notes"]:
            ln(f"  • {note}", indent=8)
        y -= 4

    if pattern.get("preparation_tips"):
        ln("PREPARATION TIPS", bold=True)
        for tip in pattern["preparation_tips"]:
            ln(f"  → {tip}", indent=8)
        y -= 4

    ln(f"Source: {pattern.get('official_source','')}")

    pdf.save()
    buffer.seek(0)
    safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in pattern.get("exam_name", "Exam"))
    return send_file(buffer, as_attachment=True,
                     download_name=f"{safe_name}_Blueprint.pdf",
                     mimetype="application/pdf")


# ══════════════════════════════════════════════════════════════════════════════
# ── MATH QUESTION VARIATION FINDER ────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/question-variations", methods=["GET", "POST"])
@login_required
def question_variations():
    """Main page for Math Question Variation Finder."""
    analytics = None
    error = None
    
    if request.method == "POST":
        # Clear previous session data
        session.pop("variation_analytics", None)
        session.pop("variation_questions", None)
        session.pop("variations_map", None)
        
        question_bank_file = request.files.get("question_bank_file")
        
        if not question_bank_file or question_bank_file.filename == "":
            error = "Please upload a mathematics question bank file."
        else:
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], f"qbank_{uuid.uuid4()}_{question_bank_file.filename}")
            question_bank_file.save(file_path)
            
            try:
                # Load and read the question bank
                from rag_pipeline import load_document
                question_bank_text = load_document(file_path)
                
                # Step 1: Analyze all questions
                analyzed_data = analyze_math_question_bank(question_bank_text)
                questions = analyzed_data.get("questions", [])
                
                if not questions:
                    error = "Could not extract questions from the file. Please ensure it contains mathematics questions."
                else:
                    # Step 2: Find variations
                    variations_map = find_question_variations(questions)
                    
                    # Step 3: Build analytics
                    analytics = build_variation_analytics(questions, variations_map)
                    
                    # Store in session
                    session["variation_analytics"] = analytics
                    session["variation_questions"] = questions
                    session["variations_map"] = variations_map
                    
            except Exception as e:
                error = f"Analysis failed: {str(e)[:200]}"
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)
    else:
        # GET request - restore from session if available
        if request.args.get("show") == "current":
            analytics = session.get("variation_analytics")
    
    return render_template("question_variations.html", analytics=analytics, error=error)


@app.route("/question-variations/concept/<concept_name>")
@login_required
def question_variations_concept(concept_name):
    """View all questions and variations for a specific concept."""
    questions = session.get("variation_questions", [])
    variations_map = session.get("variations_map", {})
    
    # Filter questions by concept
    concept_questions = [q for q in questions if q.get("concept") == concept_name]
    concept_variations = variations_map.get(concept_name, {})
    
    return render_template("question_variations_concept.html",
                          concept=concept_name,
                          questions=concept_questions,
                          variations=concept_variations)


@app.route("/question-variations/generate/<int:question_id>")
@login_required
def question_variations_generate(question_id):
    """Generate all 10 variations for a specific question."""
    questions = session.get("variation_questions", [])
    
    # Find the question
    original_question = next((q for q in questions if q.get("id") == question_id), None)
    
    if not original_question:
        return "Question not found.", 404
    
    # Generate variations
    variations = generate_question_variations(original_question, num_variations=10)
    
    return render_template("question_variations_detail.html",
                          original=original_question,
                          variations=variations)


@app.route("/question-variations/filter")
@login_required
def question_variations_filter():
    """Filter questions by chapter, concept, difficulty, or pattern."""
    questions = session.get("variation_questions", [])
    analytics = session.get("variation_analytics", {})
    
    # Get filter params
    chapter = request.args.get("chapter")
    concept = request.args.get("concept")
    difficulty = request.args.get("difficulty")
    pattern = request.args.get("pattern")
    
    # Apply filters
    filtered = questions
    if chapter:
        filtered = [q for q in filtered if q.get("chapter") == chapter]
    if concept:
        filtered = [q for q in filtered if q.get("concept") == concept]
    if difficulty:
        filtered = [q for q in filtered if q.get("difficulty") == difficulty]
    if pattern:
        filtered = [q for q in filtered if q.get("pattern_type") == pattern]
    
    return render_template("question_variations_filtered.html",
                          questions=filtered,
                          analytics=analytics,
                          filters={
                              "chapter": chapter,
                              "concept": concept,
                              "difficulty": difficulty,
                              "pattern": pattern
                          })


@app.route("/question-variations/download-report")
@login_required
def question_variations_download():
    """Download variation analysis report as PDF."""
    analytics = session.get("variation_analytics")
    if not analytics:
        return "No analysis in session.", 400
    
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    w, h = letter
    y = h - 50
    margin = 50
    lh = 15
    
    def ln(text, bold=False, size=11, indent=0):
        nonlocal y
        if y < 70:
            pdf.showPage()
            y = h - 50
        pdf.setFont("Times-Bold" if bold else "Times-Roman", size)
        pdf.drawString(margin + indent, y, str(text)[:100])
        y -= lh
    
    ln("MATHEMATICS QUESTION VARIATION ANALYSIS REPORT", bold=True, size=14)
    ln("=" * 70)
    y -= 6
    
    ln("SUMMARY", bold=True, size=12)
    ln(f"  Total Questions Analyzed   : {analytics['total_questions']}")
    ln(f"  Total Concepts Found       : {analytics['total_concepts']}")
    ln(f"  Total Chapters             : {analytics['total_chapters']}")
    ln(f"  Most Repeated Concept      : {analytics['most_repeated_concept']} ({analytics['most_repeated_count']} Q)")
    ln(f"  Most Common Pattern        : {analytics['most_common_pattern']} ({analytics['most_common_pattern_count']} Q)")
    ln(f"  Total Possible Variations  : {analytics['total_possible_variations']}")
    y -= 10
    
    ln("CHAPTER DISTRIBUTION", bold=True, size=12)
    ln("-" * 60)
    for ch, count in sorted(analytics['chapters'].items(), key=lambda x: x[1], reverse=True):
        pct = round(count / analytics['total_questions'] * 100, 1) if analytics['total_questions'] else 0
        ln(f"  {ch[:45]:<45} {count} Q  ({pct}%)")
    y -= 10
    
    ln("CONCEPT DISTRIBUTION (Top 15)", bold=True, size=12)
    ln("-" * 60)
    sorted_concepts = sorted(analytics['concepts'].items(), key=lambda x: x[1], reverse=True)[:15]
    for concept, count in sorted_concepts:
        pct = round(count / analytics['total_questions'] * 100, 1) if analytics['total_questions'] else 0
        ln(f"  {concept[:45]:<45} {count} Q  ({pct}%)")
    y -= 10
    
    ln("QUESTION PATTERN DISTRIBUTION", bold=True, size=12)
    ln("-" * 60)
    for pattern, count in sorted(analytics['patterns'].items(), key=lambda x: x[1], reverse=True):
        pct = round(count / analytics['total_questions'] * 100, 1) if analytics['total_questions'] else 0
        ln(f"  {pattern[:45]:<45} {count} Q  ({pct}%)")
    y -= 10
    
    ln("DIFFICULTY DISTRIBUTION", bold=True, size=12)
    ln("-" * 60)
    for diff, count in analytics['difficulties'].items():
        pct = round(count / analytics['total_questions'] * 100, 1) if analytics['total_questions'] else 0
        ln(f"  {diff:<45} {count} Q  ({pct}%)")
    y -= 10
    
    ln("VARIATION TYPE FREQUENCY", bold=True, size=12)
    ln("-" * 60)
    for vtype, count in sorted(analytics['variation_type_frequency'].items(), key=lambda x: x[1], reverse=True):
        ln(f"  {vtype[:45]:<45} {count} instances")
    
    pdf.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True,
                    download_name="Question_Variation_Analysis.pdf",
                    mimetype="application/pdf")


@app.route("/question-variations/new")
@login_required
def question_variations_new():
    """Clear session and start new analysis."""
    session.pop("variation_analytics", None)
    session.pop("variation_questions", None)
    session.pop("variations_map", None)
    return redirect(url_for("question_variations"))


# ── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
