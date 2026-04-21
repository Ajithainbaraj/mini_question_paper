import json
import os
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"


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
