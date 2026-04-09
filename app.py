from flask import Flask, request, render_template, send_file, session, redirect, url_for
from question_generator import generate_questions, analyze_competitive_exam_topics, generate_competitive_questions
import os, io, uuid

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required to use Flask sessions securely
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PAPERS_FOLDER'] = 'papers'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PAPERS_FOLDER'], exist_ok=True)

# ---------------- TEXT EXTRACTION ----------------
def extract_text(file_path):
    ext = file_path.split('.')[-1].lower()
    text = ""

    if ext == "txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

    elif ext == "pdf":
        import PyPDF2
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                if page.extract_text():
                    text += page.extract_text() + "\n"

    elif ext == "docx":
        import docx
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"

    return text


# ---------------- UNIVERSITY FORMAT ----------------
def format_university_paper(college, subject, semester, exam_type, questions, include_blooms=False, include_answer_key=False):

    mcqs = questions.get("mcqs", [])
    part_b = questions.get("part_b", [])
    part_c = questions.get("part_c", [])

    paper = f"""
{college.upper()}
------------------------------------------------------------
B.E / B.Tech – {subject}
Semester: {semester}
Examination: {exam_type}
Time: 3 Hours                         Max Marks: 100
------------------------------------------------------------

PART A – MCQs (10 × 1 = 10 Marks)
------------------------------------------------------------
"""

    # ✅ PART A – MCQs
    answer_key_lines = []
    if include_answer_key:
        answer_key_lines.append("PART A – MCQs")
        answer_key_lines.append("-" * 60)
        
    for i, mcq in enumerate(mcqs[:10], start=1):
        bloom_tag = f" [{mcq.get('blooms', 'Remember')}]" if include_blooms else ""
        paper += f"{i}. {mcq['question']}{bloom_tag}\n"
        for j, opt in enumerate(mcq["options"]):
            clean_opt = opt.lstrip("ABCDabcd.: ").strip()
            paper += f"   {chr(65+j)}. {clean_opt}\n"
            
        if include_answer_key:
            answer_key_lines.append(f"{i}. {mcq.get('answer', 'N/A')}")


    paper += """
PART B – Answer ANY THREE questions (3 × 10 = 30 Marks)
------------------------------------------------------------
"""

    if include_answer_key:
        answer_key_lines.append("\nPART B & C – Answer Hints")
        answer_key_lines.append("-" * 60)

    for i, q in enumerate(part_b[:8], start=1):
        # Handle string (old fallback) or dict (new format)
        if isinstance(q, dict):
            bloom_tag = f" [{q.get('blooms', 'Understand')}]" if include_blooms else ""
            paper += f"{i}. {q.get('question', '')}{bloom_tag}\n"
            if include_answer_key:
                answer_key_lines.append(f"Part B Q{i}: {q.get('answer_key', 'N/A')}")
        else:
            paper += f"{i}. {q}\n"

    paper += """
PART C – Answer ANY ONE question (1 × 30 = 30 Marks)
------------------------------------------------------------
"""
    
    for i, q in enumerate(part_c[:2], start=1):
        if isinstance(q, dict):
            bloom_tag = f" [{q.get('blooms', 'Evaluate')}]" if include_blooms else ""
            paper += f"{i}. {q.get('question', '')}{bloom_tag}\n"
            if include_answer_key:
                answer_key_lines.append(f"Part C Q{i}: {q.get('answer_key', 'N/A')}")
        else:
            paper += f"{i}. {q}\n"

    if include_answer_key and answer_key_lines:
        paper += "\n\n"
        paper += "=" * 60 + "\n"
        paper += "ANSWER KEY & HINTS\n"
        paper += "=" * 60 + "\n"
        paper += "\n".join(answer_key_lines) + "\n"
        paper += "=" * 60 + "\n"

    paper += """
------------------------------------------------------------
End of Question Paper
------------------------------------------------------------
Instructions:
• Answer all questions clearly
• Draw diagrams wherever necessary
"""

    return paper

@app.route("/result")
def result_page():
    # 🐛 BUG FIX: Access only THIS user's specific paper via UUID
    paper_id = session.get('paper_id')
    
    if not paper_id:
        return redirect(url_for("home"))
        
    paper_path = os.path.join(app.config['PAPERS_FOLDER'], f"{paper_id}.txt")
    
    if not os.path.exists(paper_path):
        return "No question paper found or user session expired."

    with open(paper_path, "r", encoding="utf-8") as f:
        paper = f.read()

    return render_template("result.html", result=paper)


# ---------------- HOME ROUTE ----------------
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        uploaded_file = request.files.get("syllabus_file")
        college = request.form.get("college")
        subject = request.form.get("subject")
        semester = request.form.get("semester")
        exam_type = request.form.get("exam_type")
        difficulty = request.form.get("difficulty", "medium")
        include_blooms = request.form.get("include_blooms") == "yes"
        include_answer_key = request.form.get("include_answer_key") == "yes"

        if not uploaded_file or uploaded_file.filename == "":
            return render_template("index.html", error="Please upload syllabus file")

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
        uploaded_file.save(file_path)

        syllabus_text = ""
        try:
            # Token limiter: Avoid sending massive 200-page textbooks to OpenAI
            syllabus_text = extract_text(file_path)[:15000] 
        finally:
            # 🐛 BUG FIX: The Storage Leak (Delete file immediately after extraction)
            if os.path.exists(file_path):
                os.remove(file_path)

        questions = generate_questions(syllabus_text, difficulty, include_blooms, include_answer_key)

        result = format_university_paper(
            college, subject, semester, exam_type, questions, include_blooms, include_answer_key
        )

        # 🐛 BUG FIX: The Race Condition (Save explicitly with UUID)
        paper_id = str(uuid.uuid4())
        paper_path = os.path.join(app.config['PAPERS_FOLDER'], f"{paper_id}.txt")
        
        with open(paper_path, "w", encoding="utf-8") as f:
            f.write(result)
            
        session['paper_id'] = paper_id

        # IMPORTANT: always return after POST
        return redirect(url_for("result_page"))

    #IMPORTANT: return something for GET
    return render_template("index.html")


# ---------------- PDF DOWNLOAD ----------------
@app.route("/download_pdf")
def download_pdf():
    paper_id = session.get('paper_id')
    
    if not paper_id:
        return "No paper generated yet for this session", 400
        
    paper_path = os.path.join(app.config['PAPERS_FOLDER'], f"{paper_id}.txt")

    if not os.path.exists(paper_path):
        return "Paper file not found", 404

    with open(paper_path, "r", encoding="utf-8") as f:
        content = f.read()

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    text = pdf.beginText(40, 750)
    text.setFont("Times-Roman", 11)

    for line in content.split("\n"):
        text.textLine(line)

    pdf.drawText(text)
    pdf.showPage()
    pdf.save()

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="University_Question_Paper.pdf",
        mimetype="application/pdf"
    )


# ---------------- COMPETITIVE EXAM ROUTES ----------------
@app.route("/competitive", methods=["GET", "POST"])
def competitive_exam():
    if request.method == "POST":
        subject = request.form.get("subject")
        topics = request.form.get("topics")
        exam_type = request.form.get("exam_type")
        difficulty = request.form.get("difficulty", "medium")
        num_questions = int(request.form.get("num_questions", 20))
        
        if not subject or not topics:
            return render_template("competitive.html", error="Please provide both subject and topics")
        
        # Handle optional file upload
        uploaded_file = request.files.get("syllabus_file")
        additional_context = ""
        
        if uploaded_file and uploaded_file.filename != "":
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
            uploaded_file.save(file_path)
            
            try:
                additional_context = extract_text(file_path)[:5000]  # Limit additional context
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)
        
        # Generate only questions
        questions_text = generate_competitive_questions(subject, topics, exam_type, difficulty, num_questions)
        
        # Store questions in session for download
        session['competitive_questions'] = questions_text
        
        return render_template("competitive_result.html", questions_text=questions_text, subject=subject, exam_type=exam_type, difficulty=difficulty, total_questions=num_questions)
    
    return render_template("competitive.html")

@app.route("/competitive_download")
def competitive_download():
    questions_text = session.get('competitive_questions')
    
    if not questions_text:
        return "No questions available for download", 400
    
    # Create a formatted text report with only questions
    report = f"""COMPETITIVE EXAM QUESTIONS
==========================
Generated: {os.popen('date').read().strip()}

{questions_text}
"""
    
    # Create text file for download
    buffer = io.BytesIO()
    buffer.write(report.encode('utf-8'))
    buffer.seek(0)
    
    filename = "Competitive_Exam_Questions.txt"
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="text/plain"
    )

# ---------------- MAIN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
