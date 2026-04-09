import PyPDF2
import docx

# ---------------- TEXT EXTRACTION ----------------
def extract_text(file_path):
    ext = file_path.split('.')[-1].lower()
    text = ""

    if ext == "txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

    elif ext == "pdf":
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                if page.extract_text():
                    text += page.extract_text() + "\n"

    elif ext == "docx":
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
             text += para.text + "\n"

    return text


# ---------------- UNIVERSITY FORMAT ----------------
def format_university_paper(college, subject, semester, exam_type, questions):
    # Depending on dynamic pattern, the questions dict structure might change
    # But for now, we'll gracefully handle missing keys.
    mcqs = questions.get("mcqs", [])
    part_b = questions.get("part_b", [])
    part_c = questions.get("part_c", [])
    summary = questions.get("summary", "")

    paper = f"""
{college.upper()}
------------------------------------------------------------
B.E / B.Tech – {subject}
Semester: {semester}
Examination: {exam_type}
Time: 3 Hours                         Max Marks: 100
------------------------------------------------------------
"""
    if summary:
        paper += f"""
[AI PAPER ANALYTICS SUMMARY]
{summary}
------------------------------------------------------------
"""

    if mcqs:
        paper += """
PART A – (MCQs)
------------------------------------------------------------
"""
        for i, mcq in enumerate(mcqs, start=1):
            paper += f"{i}. {mcq['question']}\n"
            for j, opt in enumerate(mcq["options"]):
                clean_opt = opt.lstrip("ABCDabcd.: ").strip()
                paper += f"   {chr(65+j)}. {clean_opt}\n"
            paper += "\n"

    if part_b:
        paper += """
PART B – Descriptive Questions
------------------------------------------------------------
"""
        for i, q in enumerate(part_b, start=1):
            paper += f"{i}. {q}\n"
        paper += "\n"

    if part_c:
        paper += """
PART C – Advanced / Application Questions
------------------------------------------------------------
"""
        for i, q in enumerate(part_c, start=1):
            paper += f"{i}. {q}\n"
        paper += "\n"


    paper += """
------------------------------------------------------------
End of Question Paper
------------------------------------------------------------
Instructions:
• Answer all questions clearly
• Draw diagrams wherever necessary
"""

    return paper
