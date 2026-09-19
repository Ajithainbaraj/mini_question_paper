import json
import os
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
# Using openai/gpt-oss-120b - most powerful available model on Groq
MODEL = "openai/gpt-oss-120b"


def _call_groq(prompt: str, json_mode: bool = True, retries: int = 3) -> str:
    """Call Groq with automatic retry on rate limit errors."""
    for attempt in range(1, retries + 1):
        try:
            kwargs = {"response_format": {"type": "json_object"}} if json_mode else {}
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                **kwargs
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            err = str(e)
            print(f"⚠️ Groq attempt {attempt}/{retries} failed: {err[:200]}")
            if "429" in err and attempt < retries:
                wait = 15 * attempt
                print(f"   Rate limited — waiting {wait}s before retry...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("All Groq retries exhausted")


# ── UNIVERSITY QUESTION PAPER ────────────────────────────────────────────────
def generate_questions(context: str, difficulty: str = "medium",
                       include_blooms: bool = False, include_answer_key: bool = False) -> dict:
    prompt = f"""You are an intelligent university question paper generator.
Use ONLY the syllabus context below (retrieved via RAG). Do NOT add any external knowledge.

--- SYLLABUS CONTEXT ---
{context}
------------------------

Rules:
1. Question Paper Structure:
   - Part A: exactly 10 MCQs (1 mark each)
   - Part B: exactly 8 short-answer questions (5 marks each)
   - Part C: exactly 2 long-answer questions (10 marks each)

2. Content Guidelines:
   - Questions must be strictly based on the context above.
   - EVERY question must test a COMPLETELY DIFFERENT topic or concept.
   - DO NOT repeat, rephrase, or ask about the same concept twice anywhere in the paper.
   - Each MCQ must have a unique topic — no two MCQs can be about the same subject.
   - Difficulty distribution: Easy 30%, Medium 50%, Hard 20%.
   - Overall difficulty level: {difficulty}

3. STRICT NO-DUPLICATE RULE:
   - Before finalizing, check every question against all others.
   - If any two questions are similar in topic or wording, replace one with a different topic.
   - Questions across Part A, B, and C must all be on different topics.

4. Quality:
   - Clear, academic language. No spelling errors.
   - MCQs: 4 options (A-D), one correct answer.
   - Bloom's taxonomy tag for every question: Remember, Understand, Apply, Analyze, Evaluate, or Create.
   - answer_key for Part B & C: 1-2 sentence hint.

Return STRICT JSON ONLY in this exact format:
{{
  "mcqs": [
    {{
      "question": "string",
      "options": ["string", "string", "string", "string"],
      "answer": "string",
      "blooms": "string"
    }}
  ],
  "part_b": [
    {{
      "question": "string",
      "answer_key": "string",
      "blooms": "string"
    }}
  ],
  "part_c": [
    {{
      "question": "string",
      "answer_key": "string",
      "blooms": "string"
    }}
  ]
}}"""

    try:
        print(f"[DEBUG] Sending to Groq (context: {len(context)} chars)")
        content = _call_groq(prompt, json_mode=True)
        print(f"[DEBUG] Response preview: {content[:300]}")

        start = content.find("{")
        end = content.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError(f"No JSON in response: {content[:200]}")

        data = json.loads(content[start:end])

        if not all(k in data for k in ["mcqs", "part_b", "part_c"]):
            raise ValueError(f"Missing keys. Got: {list(data.keys())}")

        print(f"[DEBUG] Generated: {len(data['mcqs'])} MCQs, {len(data['part_b'])} Part B, {len(data['part_c'])} Part C")
        return _deduplicate(data)

    except Exception as e:
        print(f"⚠️ LLM Error: {type(e).__name__}: {e}")
        return _fallback_questions()


def _normalize(text: str) -> str:
    """Lowercase and strip punctuation for comparison."""
    import re
    return re.sub(r"[^a-z0-9 ]", "", text.lower().strip())


def _deduplicate(data: dict) -> dict:
    """Remove duplicate questions across all sections."""
    seen = set()
    
    def is_duplicate(question: str) -> bool:
        # Compare first 60 chars normalized to catch rephrased duplicates
        key = _normalize(question)[:60]
        if key in seen:
            return True
        seen.add(key)
        return False

    data["mcqs"]   = [q for q in data["mcqs"]   if not is_duplicate(q["question"])]
    data["part_b"] = [q for q in data["part_b"] if not is_duplicate(q["question"])]
    data["part_c"] = [q for q in data["part_c"] if not is_duplicate(q["question"])]

    removed = (10 - len(data["mcqs"])) + (8 - len(data["part_b"])) + (2 - len(data["part_c"]))
    if removed:
        print(f"[DEBUG] Deduplication removed {removed} duplicate question(s)")

    return data


# ── COMPETITIVE EXAM ─────────────────────────────────────────────────────────
def analyze_competitive_exam_topics(subject: str, topics: str) -> dict:
    prompt = f"""You are an expert in competitive exam preparation for NEET/JEE.
Analyze subject "{subject}" with topics: {topics}
Return STRICT JSON ONLY:
{{
    "subject": "{subject}",
    "important_concepts": [
        {{
            "concept": "string",
            "subtopics": ["string"],
            "weightage": "High/Medium/Low",
            "exam_frequency": "Frequently/Occasionally/Rarely",
            "difficulty_level": "Easy/Medium/Hard"
        }}
    ],
    "recommended_study_order": ["string"],
    "common_mistakes": ["string"],
    "key_formulas": ["string"]
}}
Provide 5-8 concepts with 2-4 subtopics each."""

    try:
        response_text = _call_groq(prompt, json_mode=True)
        return json.loads(response_text)
    except Exception as e:
        print(f"⚠️ AI Error: {e}")
        return {
            "subject": subject,
            "important_concepts": [{"concept": "Core Principles", "subtopics": ["Fundamentals"],
                                     "weightage": "High", "exam_frequency": "Frequently", "difficulty_level": "Medium"}],
            "recommended_study_order": ["Start with basics"],
            "common_mistakes": ["Conceptual errors"],
            "key_formulas": ["Basic formulas"]
        }


def generate_competitive_questions(subject: str, topics: str, exam_type: str,
                                   difficulty: str = "medium", num_questions: int = 20) -> str:
    prompt = f"""You are an expert question setter for {exam_type} competitive exams.

Subject: {subject}
Topics: {topics}
Number of Questions: {num_questions}
Difficulty: {difficulty}

Generate high-quality MCQs. Each question must have exactly 4 options (A, B, C, D).
Do NOT include answers or explanations — exam simulation mode.

Output Format:
Q1. <Question>
Options:
A. <Option>
B. <Option>
C. <Option>
D. <Option>

(Continue for all {num_questions} questions)"""

    try:
        return _call_groq(prompt, json_mode=False)
    except Exception as e:
        print(f"⚠️ AI Error: {e}")
        return "\n".join(
            f"Q{i}. Sample question {i} about {subject}?\nOptions:\nA. Option A\nB. Option B\nC. Option C\nD. Option D"
            for i in range(1, num_questions + 1)
        )


# ── FULL MOCK TEST WORKFLOW ───────────────────────────────────────────────────
def generate_full_mock_test(context: str, topic: str, difficulty: str = "medium") -> dict:
    """Step 1: Generate questions only (answers hidden), return as JSON."""
    prompt = f"""You are an intelligent competitive exam question paper setter.
Generate a mock test using ONLY the provided context.

Context:
{context}

Topic: {topic}
Difficulty: {difficulty}

Generate the following:
- Section A: exactly 5 MCQs, each with 4 options (A, B, C, D)
- Section B: exactly 3 short answer questions

Return STRICT JSON ONLY:
{{
  "mcqs": [
    {{
      "id": 1,
      "question": "string",
      "options": {{"A": "string", "B": "string", "C": "string", "D": "string"}},
      "correct": "A"
    }}
  ],
  "short": [
    {{
      "id": 6,
      "question": "string",
      "correct_answer": "string"
    }}
  ]
}}

Rules:
- IDs for mcqs: 1-5, short: 6-8
- correct must be A, B, C, or D for MCQs
- correct_answer for short questions: 1-2 sentence model answer
- Questions must be strictly from the context
- No repetition
"""
    try:
        raw = _call_groq(prompt, json_mode=True)
        start = raw.find("{")
        end = raw.rfind("}") + 1
        return json.loads(raw[start:end])
    except Exception as e:
        print(f"⚠️ Full Mock Test Error: {e}")
        return {"mcqs": [], "short": []}


def evaluate_full_mock_test(test_data: dict, user_answers: dict, context: str) -> dict:
    """Steps 4-10: Evaluate answers, score, analytics, recommendations."""
    mcq_results = []
    short_results = []
    total_marks = 0
    correct_count = 0
    wrong_topics = []
    strong_topics = []

    # ── Evaluate MCQs ──
    for q in test_data.get("mcqs", []):
        qid = str(q["id"])
        user_ans = user_answers.get(qid, "").strip().upper()
        correct  = q["correct"].strip().upper()
        is_correct = user_ans == correct
        marks = 1 if is_correct else 0
        total_marks += marks
        if is_correct:
            correct_count += 1
            strong_topics.append(q["question"][:40])
        else:
            wrong_topics.append(q["question"][:40])

        mcq_results.append({
            "id": q["id"],
            "question": q["question"],
            "options": q["options"],
            "correct": correct,
            "user_answer": user_ans if user_ans else "Not answered",
            "marks": marks,
            "feedback": "Correct!" if is_correct else f"Wrong. Correct answer is {correct}: {q['options'].get(correct, '')}"
        })

    # ── Evaluate Short Answers via LLM ──
    for q in test_data.get("short", []):
        qid = str(q["id"])
        user_ans = user_answers.get(qid, "").strip()
        correct_ans = q.get("correct_answer", "")

        if not user_ans:
            short_results.append({
                "id": q["id"], "question": q["question"],
                "correct_answer": correct_ans, "user_answer": "Not answered",
                "similarity_score": 0, "marks": 0,
                "feedback": "No answer provided."
            })
            wrong_topics.append(q["question"][:40])
            continue

        eval_prompt = f"""You are a strict but fair exam evaluator.
Compare the student answer with the correct answer.

Correct Answer: {correct_ans}
Student Answer: {user_ans}
Context: {context[:500]}

Scoring: >=70% similarity → 1 mark, <70% → 0 mark

Return JSON only:
{{
  "similarity_score": <0-100>,
  "marks": <0 or 1>,
  "feedback": "short feedback string"
}}"""
        try:
            raw = _call_groq(eval_prompt, json_mode=True)
            start = raw.find("{")
            end = raw.rfind("}") + 1
            eval_result = json.loads(raw[start:end])
        except Exception:
            eval_result = {"similarity_score": 0, "marks": 0, "feedback": "Could not evaluate."}

        marks = eval_result.get("marks", 0)
        total_marks += marks
        if marks == 1:
            correct_count += 1
            strong_topics.append(q["question"][:40])
        else:
            wrong_topics.append(q["question"][:40])

        short_results.append({
            "id": q["id"],
            "question": q["question"],
            "correct_answer": correct_ans,
            "user_answer": user_ans,
            "similarity_score": eval_result.get("similarity_score", 0),
            "marks": marks,
            "feedback": eval_result.get("feedback", "")
        })

    total_questions = len(test_data.get("mcqs", [])) + len(test_data.get("short", []))
    accuracy = round((total_marks / total_questions * 100), 1) if total_questions else 0

    # ── Recommendations ──
    rec_prompt = f"""Based on these weak topics from a mock test, suggest 3 revision tips.
Weak topics: {', '.join(wrong_topics) if wrong_topics else 'None'}
Context subject: {context[:300]}
Return JSON only:
{{"revision_topics": ["string"], "practice_suggestions": ["string"]}}"""
    try:
        raw = _call_groq(rec_prompt, json_mode=True)
        start = raw.find("{")
        end = raw.rfind("}") + 1
        recommendations = json.loads(raw[start:end])
    except Exception:
        recommendations = {
            "revision_topics": wrong_topics[:3],
            "practice_suggestions": ["Review the syllabus material", "Practice more questions"]
        }

    return {
        "mcq_results": mcq_results,
        "short_results": short_results,
        "total_marks": total_marks,
        "total_questions": total_questions,
        "correct_count": correct_count,
        "wrong_count": total_questions - correct_count,
        "accuracy": accuracy,
        "weak_topics": wrong_topics,
        "strong_topics": strong_topics,
        "recommendations": recommendations
    }


# ── REVISION NOTES ───────────────────────────────────────────────────────────
def generate_revision_notes(context: str, topic: str) -> str:
    prompt = f"""You are an expert tutor for competitive exams.
Your task is to generate concise revision notes for the given topic using the provided study material.

Instructions:
- Use ONLY the provided context
- Keep the notes short, clear, and exam-focused
- Avoid long paragraphs
- Use bullet points for better readability

Structure:
- Key Concepts
- Important Definitions
- Formulas (if applicable)
- Important Facts
- Keywords

Highlight important points that are frequently asked in exams.

If the topic is not found in the context, respond with:
"The topic is not available in the provided material."

Context:
{context}

Topic:
{topic}

Revision Notes:"""

    try:
        print(f"[DEBUG] Revision notes for topic: {topic}")
        return _call_groq(prompt, json_mode=False)
    except Exception as e:
        print(f"⚠️ Revision Notes Error: {e}")
        return "Sorry, could not generate revision notes at this time. Please try again."


# ── AI TUTOR ─────────────────────────────────────────────────────────────────
def answer_question(context: str, question: str) -> str:
    prompt = f"""You are an expert tutor for competitive exams.
Your task is to explain the given concept clearly using the provided study material.

Instructions:
- Use ONLY the provided context
- Explain in a simple and easy-to-understand way
- Follow a step-by-step structure
- Start with a basic definition
- Then explain key concepts
- Break down complex ideas into smaller steps
- Provide at least one example
- Highlight important exam points

If the concept is not found in the context, respond with:
"The concept is not available in the provided material."

Context:
{context}

Concept:
{question}

Explanation:"""

    try:
        print(f"[DEBUG] Tutor question: {question}")
        return _call_groq(prompt, json_mode=False)
    except Exception as e:
        print(f"⚠️ Tutor Error: {e}")
        return "Sorry, I could not generate an answer at this time. Please try again."


# ── FALLBACK ─────────────────────────────────────────────────────────────────
def _fallback_questions() -> dict:
    return {
        "mcqs": [
            {"question": f"Sample MCQ {i}", "options": ["Option A", "Option B", "Option C", "Option D"],
             "answer": "Option A", "blooms": "Remember"}
            for i in range(1, 11)
        ],
        "part_b": [
            {"question": f"Short answer question {i}.", "answer_key": "Key concept hint.", "blooms": "Understand"}
            for i in range(1, 9)
        ],
        "part_c": [
            {"question": "Long answer question 1.", "answer_key": "Detailed explanation hint.", "blooms": "Evaluate"},
            {"question": "Long answer question 2.", "answer_key": "Detailed explanation hint.", "blooms": "Create"}
        ]
    }


# ── CHAPTER ANALYZER ─────────────────────────────────────────────────────────

def extract_questions_from_paper(paper_text: str) -> list:
    """Extract individual questions from a question paper text using LLM."""
    prompt = f"""You are an expert at parsing question papers.
Extract every question from the text below.
Each question may start with Q1, Q.1, 1., 1), or just a number.
Include all options if present (MCQ format).

Question Paper Text:
{paper_text[:6000]}

Return STRICT JSON ONLY:
{{
  "questions": [
    {{
      "question_no": 1,
      "question": "full question text",
      "options": ["A. option", "B. option", "C. option", "D. option"]
    }}
  ]
}}

Rules:
- If a question has no options, set options to []
- Preserve the exact question text
- Extract ALL questions found, do not skip any
- question_no must be sequential integers starting from 1
"""
    try:
        raw = _call_groq(prompt, json_mode=True)
        start = raw.find("{")
        end = raw.rfind("}") + 1
        data = json.loads(raw[start:end])
        return data.get("questions", [])
    except Exception as e:
        print(f"⚠️ Question extraction error: {e}")
        return []


def classify_questions_to_chapters(questions: list, syllabus_chunks: list) -> list:
    """
    Classify each question to the most relevant chapter using LLM.
    Uses the syllabus chunks as context — no external knowledge.
    """
    # Build a compact syllabus map for the LLM
    syllabus_context = "\n\n".join(syllabus_chunks[:20])  # top 20 chunks

    classified = []
    # Batch questions to reduce API calls (process up to 10 at a time)
    batch_size = 10
    for i in range(0, len(questions), batch_size):
        batch = questions[i:i + batch_size]
        q_list = "\n".join(
            f"Q{q['question_no']}: {q['question'][:200]}"
            for q in batch
        )

        prompt = f"""You are an expert syllabus analyzer.
Given the syllabus content and a list of exam questions, classify each question to the most relevant Unit/Chapter/Topic from the syllabus.

SYLLABUS CONTENT:
{syllabus_context}

QUESTIONS TO CLASSIFY:
{q_list}

Rules:
- Use ONLY topics/chapters found in the syllabus above
- Do NOT invent chapter names
- Pick the single best matching chapter for each question
- If no match found, use "General / Miscellaneous"
- Keep subject names consistent (Physics, Chemistry, Biology, Mathematics, etc.)

Return STRICT JSON ONLY:
{{
  "classifications": [
    {{
      "question_no": 1,
      "subject": "subject name",
      "chapter": "chapter or unit name",
      "confidence": "high/medium/low"
    }}
  ]
}}"""
        try:
            raw = _call_groq(prompt, json_mode=True)
            start = raw.find("{")
            end = raw.rfind("}") + 1
            data = json.loads(raw[start:end])
            classified.extend(data.get("classifications", []))
        except Exception as e:
            print(f"⚠️ Classification batch error: {e}")
            # fallback for this batch
            for q in batch:
                classified.append({
                    "question_no": q["question_no"],
                    "subject": "Unknown",
                    "chapter": "General / Miscellaneous",
                    "confidence": "low"
                })

    # Merge classifications back into questions
    class_map = {c["question_no"]: c for c in classified}
    result = []
    for q in questions:
        cls = class_map.get(q["question_no"], {
            "subject": "Unknown",
            "chapter": "General / Miscellaneous",
            "confidence": "low"
        })
        result.append({
            "question_no": q["question_no"],
            "question": q["question"],
            "options": q.get("options", []),
            "subject": cls.get("subject", "Unknown"),
            "chapter": cls.get("chapter", "General / Miscellaneous"),
            "confidence": cls.get("confidence", "low"),
        })
    return result


def build_chapter_analysis(classified_questions: list) -> dict:
    """Build summary statistics from classified questions."""
    from collections import defaultdict, Counter

    chapter_map      = defaultdict(list)   # chapter → full question dicts
    subject_map      = defaultdict(int)    # subject → count

    for q in classified_questions:
        chapter_map[q["chapter"]].append(q)
        subject_map[q["subject"]] += 1

    # Sort chapters by count descending
    chapters_sorted = sorted(
        [{"chapter": ch, "count": len(qs)}
         for ch, qs in chapter_map.items()],
        key=lambda x: x["count"], reverse=True
    )

    subjects_sorted = sorted(
        [{"subject": sub, "count": cnt}
         for sub, cnt in subject_map.items()],
        key=lambda x: x["count"], reverse=True
    )

    total       = len(classified_questions)
    most_asked  = chapters_sorted[0]["chapter"]  if chapters_sorted else "N/A"
    least_asked = chapters_sorted[-1]["chapter"] if chapters_sorted else "N/A"

    return {
        "total_questions":     total,
        "total_chapters":      len(chapter_map),
        "most_asked_chapter":  most_asked,
        "least_asked_chapter": least_asked,
        "chapters":            chapters_sorted,
        "subjects":            subjects_sorted,
        "chapter_questions":   dict(chapter_map),   # chapter → [q dicts]
        "questions":           classified_questions,
    }


# ── EXAM PATTERN ANALYZER ────────────────────────────────────────────────────

def fetch_exam_pattern(query: str) -> dict:
    """
    Fetch the official exam pattern for any exam based on user query.
    Uses the LLM's training knowledge about official exam structures.
    Returns structured JSON with all pattern details.
    IMPORTANT: Does NOT invent data — only returns what is officially known.
    """
    prompt = f"""You are an expert on Indian and international competitive exam patterns and syllabi.

The user wants to know the official exam pattern for: "{query}"

Your task:
1. Identify the exact exam name, conducting body, and year/edition.
2. Return ONLY officially documented information. Do NOT invent or estimate any figures.
3. If chapter-wise weightage is NOT officially published, set chapter_weightage_available to false and leave chapter_weightage empty.
4. Be accurate about negative marking, total marks, sections, etc.

Return STRICT JSON ONLY in this exact format:
{{
  "exam_name": "Full official name of the exam",
  "conducting_body": "Name of the conducting organization",
  "year": "Year or edition (e.g. 2024, 2025)",
  "level": "National / State / University / School",
  "eligibility": "Brief eligibility criteria",
  "exam_mode": "Online / Offline / Both",
  "duration_minutes": 180,
  "total_marks": 720,
  "total_questions": 180,
  "negative_marking": "-1/3 per wrong answer OR No negative marking",
  "exam_stages": ["Stage 1: Prelims", "Stage 2: Mains"],
  "official_source": "URL or name of official source (e.g. nta.ac.in)",
  "sections": [
    {{
      "name": "Physics",
      "questions": 50,
      "marks": 200,
      "marks_per_question": 4,
      "question_types": ["MCQ", "Assertion-Reason"]
    }}
  ],
  "subject_distribution": [
    {{"subject": "Physics", "questions": 50, "marks": 200, "percentage": 27.8}},
    {{"subject": "Chemistry", "questions": 50, "marks": 200, "percentage": 27.8}},
    {{"subject": "Biology", "questions": 100, "marks": 400, "percentage": 44.4}}
  ],
  "chapter_weightage_available": false,
  "chapter_weightage": [],
  "important_notes": [
    "Any important exam-specific rules or changes",
    "Recent changes to pattern if any"
  ],
  "preparation_tips": [
    "Tip 1",
    "Tip 2",
    "Tip 3"
  ]
}}

If you cannot confidently identify the exam or don't have reliable data, return:
{{
  "exam_name": "Unknown",
  "error": "Could not identify a specific exam from the query. Please be more specific.",
  "conducting_body": "",
  "year": "",
  "level": "",
  "eligibility": "",
  "exam_mode": "",
  "duration_minutes": 0,
  "total_marks": 0,
  "total_questions": 0,
  "negative_marking": "",
  "exam_stages": [],
  "official_source": "",
  "sections": [],
  "subject_distribution": [],
  "chapter_weightage_available": false,
  "chapter_weightage": [],
  "important_notes": [],
  "preparation_tips": []
}}"""

    try:
        raw = _call_groq(prompt, json_mode=True)
        start = raw.find("{")
        end   = raw.rfind("}") + 1
        data  = json.loads(raw[start:end])
        print(f"[DEBUG] Exam pattern fetched for: {query}")
        return data
    except Exception as e:
        print(f"⚠️ Exam pattern error: {e}")
        return {
            "exam_name": "Error",
            "error": f"Failed to fetch exam pattern: {str(e)[:100]}",
            "conducting_body": "", "year": "", "level": "",
            "eligibility": "", "exam_mode": "",
            "duration_minutes": 0, "total_marks": 0, "total_questions": 0,
            "negative_marking": "", "exam_stages": [], "official_source": "",
            "sections": [], "subject_distribution": [],
            "chapter_weightage_available": False, "chapter_weightage": [],
            "important_notes": [], "preparation_tips": []
        }


# ══════════════════════════════════════════════════════════════════════════════
# ── MATHEMATICS QUESTION VARIATION FINDER ─────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def analyze_math_question_bank(question_bank_text: str) -> dict:
    """
    Step 1: Extract and analyze all math questions from the uploaded question bank.
    Identifies: chapter, concept, formula, pattern, difficulty, semantic structure.
    """
    prompt = f"""You are an expert mathematics educator and question pattern analyzer.

Analyze the following mathematics question bank and extract each question with its metadata.

QUESTION BANK:
{question_bank_text[:8000]}

Your task:
1. Extract every question
2. Identify the mathematical chapter (Algebra, Calculus, Trigonometry, Geometry, etc.)
3. Identify the core concept (Quadratic Equations, Derivatives, Trigonometric Identities, etc.)
4. Identify the formula/theorem involved
5. Classify the question pattern type (Direct Formula, Word Problem, Application, Multi-step, Reverse, etc.)
6. Assess difficulty (Easy, Medium, Hard)
7. Extract the semantic structure (what mathematical operation is being tested)

Return STRICT JSON ONLY:
{{
  "total_questions": <number>,
  "questions": [
    {{
      "id": 1,
      "question": "full question text",
      "chapter": "Mathematics chapter name",
      "concept": "specific mathematical concept",
      "formula": "formula or theorem used",
      "pattern_type": "Direct/Word Problem/Application/Multi-step/Reverse/Conceptual",
      "difficulty": "Easy/Medium/Hard",
      "semantic_key": "core mathematical operation (e.g., solve_quadratic, find_derivative)",
      "keywords": ["keyword1", "keyword2"]
    }}
  ]
}}

Rules:
- Extract ALL questions found
- Be precise about the concept (not just chapter)
- semantic_key should identify the core mathematical operation
- Include all relevant formulas
"""
    try:
        raw = _call_groq(prompt, json_mode=True)
        start = raw.find("{")
        end = raw.rfind("}") + 1
        data = json.loads(raw[start:end])
        print(f"[DEBUG] Analyzed {data.get('total_questions', 0)} questions")
        return data
    except Exception as e:
        print(f"⚠️ Question bank analysis error: {e}")
        return {"total_questions": 0, "questions": []}


def find_question_variations(analyzed_questions: list) -> dict:
    """
    Step 2: Group questions by concept and find semantic variations.
    This identifies how the SAME concept appears differently in exams.
    """
    from collections import defaultdict
    
    # Group by concept
    concept_groups = defaultdict(list)
    for q in analyzed_questions:
        concept = q.get("concept", "Unknown")
        concept_groups[concept].append(q)
    
    # Analyze variations for each concept
    variations_map = {}
    
    for concept, questions in concept_groups.items():
        if len(questions) < 2:
            continue  # Need at least 2 questions to find variations
        
        # Use LLM to identify variation patterns
        q_list = "\n\n".join(
            f"Q{i+1}: {q['question']}"
            for i, q in enumerate(questions[:10])  # Limit to 10 per concept
        )
        
        prompt = f"""You are an expert at identifying mathematical question variation patterns.

Concept: {concept}

Questions testing this concept:
{q_list}

Analyze how this SAME concept appears in DIFFERENT ways. Identify variation types:

1. Different Numbers/Values
2. Different Equation Format
3. Formula-based Variation
4. Word Problem vs Direct Question
5. Reverse Question (given answer, find question)
6. Application-based Question
7. Multi-step Question
8. Conceptual Variation
9. Changed Conditions/Data
10. Different Solving Method

Return STRICT JSON ONLY:
{{
  "concept": "{concept}",
  "total_questions": {len(questions)},
  "variation_types": [
    {{
      "type": "Different Numbers",
      "description": "How numbers/values vary",
      "question_ids": [1, 2, 3],
      "example_questions": ["Q text 1", "Q text 2"]
    }}
  ],
  "pattern_summary": "Brief summary of how this concept varies in exams"
}}

Focus on SEMANTIC variations, not just wording differences.
"""
        try:
            raw = _call_groq(prompt, json_mode=True)
            start = raw.find("{")
            end = raw.rfind("}") + 1
            variation_data = json.loads(raw[start:end])
            variations_map[concept] = variation_data
        except Exception as e:
            print(f"⚠️ Variation analysis error for {concept}: {e}")
            continue
    
    return variations_map


def generate_question_variations(original_question: dict, num_variations: int = 10) -> list:
    """
    Step 3: Generate specific variations for a given question.
    Creates all 10 types of variations with hints and solutions.
    """
    question_text = original_question.get("question", "")
    concept = original_question.get("concept", "")
    formula = original_question.get("formula", "")
    chapter = original_question.get("chapter", "")
    
    prompt = f"""You are an expert mathematics question creator.

Original Question:
{question_text}

Chapter: {chapter}
Concept: {concept}
Formula: {formula}

Generate {num_variations} DISTINCT variations of this question that test the SAME concept in DIFFERENT ways:

1. Different Numbers - Change the numerical values
2. Different Equation Format - Rearrange or present differently
3. Formula-based Variation - Emphasize different parts of the formula
4. Word Problem - Create a real-world scenario
5. Reverse Question - Given answer, find the original equation/values
6. Application Question - Practical application of the concept
7. Multi-step Question - Combine with other concepts
8. Conceptual Variation - Test deeper understanding
9. Changed Conditions - Modify constraints or parameters
10. Different Method - Same concept, different solving approach

For EACH variation, provide:
- The question text
- Short hint (1-2 lines)
- Formula/concept used
- Step-by-step solving approach (without final answer)
- Difficulty level

Return STRICT JSON ONLY:
{{
  "original_question": "{question_text[:100]}",
  "concept": "{concept}",
  "variations": [
    {{
      "variation_type": "Different Numbers",
      "question": "full question text",
      "hint": "short hint",
      "formula": "formula used",
      "steps": ["Step 1: ...", "Step 2: ...", "Step 3: ..."],
      "difficulty": "Easy/Medium/Hard",
      "full_solution": "complete solution (hidden by default)"
    }}
  ]
}}

Make each variation MEANINGFULLY different, not just cosmetic changes.
"""
    try:
        raw = _call_groq(prompt, json_mode=True)
        start = raw.find("{")
        end = raw.rfind("}") + 1
        data = json.loads(raw[start:end])
        return data.get("variations", [])
    except Exception as e:
        print(f"⚠️ Variation generation error: {e}")
        return []


def build_variation_analytics(analyzed_questions: list, variations_map: dict) -> dict:
    """
    Step 4: Build comprehensive analytics for the variation dashboard.
    """
    from collections import Counter
    
    total_questions = len(analyzed_questions)
    
    # Count by chapter
    chapters = Counter(q.get("chapter", "Unknown") for q in analyzed_questions)
    
    # Count by concept
    concepts = Counter(q.get("concept", "Unknown") for q in analyzed_questions)
    
    # Count by pattern type
    patterns = Counter(q.get("pattern_type", "Unknown") for q in analyzed_questions)
    
    # Count by difficulty
    difficulties = Counter(q.get("difficulty", "Unknown") for q in analyzed_questions)
    
    # Find most repeated concept
    most_repeated_concept = concepts.most_common(1)[0] if concepts else ("None", 0)
    
    # Find most common pattern
    most_common_pattern = patterns.most_common(1)[0] if patterns else ("None", 0)
    
    # Calculate total possible variations (10 variations per unique concept)
    total_concepts = len(concepts)
    total_variations = total_concepts * 10
    
    # Build variation type frequency
    variation_types = {
        "Different Numbers": 0,
        "Different Equation Format": 0,
        "Formula-based Variation": 0,
        "Word Problem": 0,
        "Reverse Question": 0,
        "Application Question": 0,
        "Multi-step Question": 0,
        "Conceptual Variation": 0,
        "Changed Conditions": 0,
        "Different Method": 0
    }
    
    for concept, var_data in variations_map.items():
        for var in var_data.get("variation_types", []):
            vtype = var.get("type", "")
            if vtype in variation_types:
                variation_types[vtype] += len(var.get("question_ids", []))
    
    return {
        "total_questions": total_questions,
        "total_concepts": len(concepts),
        "total_chapters": len(chapters),
        "most_repeated_concept": most_repeated_concept[0],
        "most_repeated_count": most_repeated_concept[1],
        "most_common_pattern": most_common_pattern[0],
        "most_common_pattern_count": most_common_pattern[1],
        "total_possible_variations": total_variations,
        "chapters": dict(chapters),
        "concepts": dict(concepts),
        "patterns": dict(patterns),
        "difficulties": dict(difficulties),
        "variation_type_frequency": variation_types,
        "concepts_list": sorted(concepts.keys())
    }
