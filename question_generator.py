import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load env variables from .env if present
load_dotenv()

# ✅ Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

def analyze_competitive_exam_topics(subject, topics):
    """
    Analyze subject and topics to identify important concepts for competitive exams like NEET/JEE
    """
    prompt = f"""
    You are an expert in competitive exam preparation for NEET/JEE and similar entrance exams.
    
    Analyze the subject "{subject}" with topics: {topics}
    
    List the important concepts and subtopics commonly asked in competitive exams like NEET/JEE.
    
    Return STRICT JSON ONLY (no explanation, no markdown):
    {{
        "subject": "{subject}",
        "important_concepts": [
            {{
                "concept": "string",
                "subtopics": ["string", "string"],
                "weightage": "High/Medium/Low",
                "exam_frequency": "Frequently/Occasionally/Rarely",
                "difficulty_level": "Easy/Medium/Hard"
            }}
        ],
        "recommended_study_order": ["string", "string"],
        "common_mistakes": ["string", "string"],
        "key_formulas": ["string", "string"]
    }}
    
    Rules:
    - Provide 5-8 important concepts
    - Each concept should have 2-4 relevant subtopics
    - Be specific about what's commonly tested in competitive exams
    - Include practical study recommendations
    """
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(temperature=0.3)
        )
        
        result = response.text.strip()
        
        # Try to parse as JSON, if fails return fallback
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            # Fallback response
            return {
                "subject": subject,
                "important_concepts": [
                    {
                        "concept": "Core Principles",
                        "subtopics": ["Fundamental theories", "Basic applications"],
                        "weightage": "High",
                        "exam_frequency": "Frequently",
                        "difficulty_level": "Medium"
                    }
                ],
                "recommended_study_order": ["Start with basics", "Practice problems"],
                "common_mistakes": ["Conceptual errors", "Calculation mistakes"],
                "key_formulas": ["Basic formulas", "Advanced equations"]
            }
            
    except Exception as e:
        print(f"⚠️ AI Error / Fallback used: {e}")
        # Fallback response
        return {
            "subject": subject,
            "important_concepts": [
                {
                    "concept": "Core Principles",
                    "subtopics": ["Fundamental theories", "Basic applications"],
                    "weightage": "High",
                    "exam_frequency": "Frequently",
                    "difficulty_level": "Medium"
                }
            ],
            "recommended_study_order": ["Start with basics", "Practice problems"],
            "common_mistakes": ["Conceptual errors", "Calculation mistakes"],
            "key_formulas": ["Basic formulas", "Advanced equations"]
        }

def generate_competitive_questions(subject, topics, exam_type, difficulty="medium", num_questions=20):
    """
    Generate competitive exam questions based on subject and topics analysis
    """
    prompt = f"""You are an expert question setter for competitive exams like NEET and JEE.

Subject: {subject}
Topics: {topics}
Number of Questions: {num_questions}
Difficulty Level: {difficulty}

Task:
Analyze the topics and generate high-quality multiple-choice questions suitable for a real competitive exam.

Instructions:

Each question must have exactly 4 options (A, B, C, D)
Only one correct answer (but DO NOT reveal it)
Include conceptual, application-based, and numerical questions
Follow real {exam_type} exam patterns
Avoid repetition
Ensure clarity and correctness

IMPORTANT:

Do NOT include answers
Do NOT include explanations
This is for exam simulation mode

Output Format:

Q1. <Question>

Options:
A. <Option>
B. <Option>
C. <Option>
D. <Option>

Q2. <Question>

Options:
A. <Option>
B. <Option>
C. <Option>
D. <Option>

(Continue for all questions)

Format neatly like a real exam paper.
"""
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(temperature=0.3)
        )
        
        result = response.text.strip()
        return result
            
    except Exception as e:
        print(f"⚠️ AI Error / Fallback used: {e}")
        # Fallback response
        fallback_questions = []
        for i in range(1, num_questions + 1):
            fallback_questions.append(f"""Q{i}. What is the fundamental principle of {subject} (Question {i})?

Options:
A. Option A
B. Option B
C. Option C
D. Option D
""")
        return "\n".join(fallback_questions)

def generate_questions(syllabus_text, difficulty="medium", include_blooms=False, include_answer_key=False):
    prompt = f"""
You are a university question paper setter.

Generate STRICT JSON ONLY (no explanation, no markdown).

Format:
{{
  "mcqs": [
    {{
      "question": "string",
      "options": ["A", "B", "C", "D"],
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
}}

Rules:
- Exactly 10 MCQs
- Exactly 8 part_b questions
- Exactly 2 part_c questions
- Every single question must test a COMPLETELY DIFFERENT topic or subtopic from the syllabus.
- Ensure all MCQs are strictly about different topics/subtopics and are NEVER similar in wording or meaning.
- DO NOT repeat, rephrase, or ask about the same concept twice in different forms across any section.
- "blooms" should be one of [Remember, Understand, Apply, Analyze, Evaluate, Create]
- "answer_key" for part_b and part_c should be a brief hint/core concept (1-2 sentences).

Syllabus:
{syllabus_text}

Difficulty: {difficulty}
"""

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.6,
                response_mime_type="application/json"
            )
        )

        content = response.text.strip()

        # ✅ Handle accidental text before JSON
        start = content.find("{")
        end = content.rfind("}") + 1
        content = content[start:end]

        data = json.loads(content)

        # ✅ Validate structure
        if not all(k in data for k in ["mcqs", "part_b", "part_c"]):
            raise ValueError("Invalid JSON structure")

        return data

    except Exception as e:
        print("⚠️ AI Error / Fallback used:", e)

        # ✅ SAFE FALLBACK WITH UNIQUE MODULAR QUESTIONS
        fallback_data = {
            "mcqs": [
                {
                    "question": "What is the primary function of a game engine?",
                    "options": ["To compile code", "To provide a software framework for building games", "To design 3D models", "To act as an operating system"],
                    "answer": "To provide a software framework for building games",
                    "blooms": "Remember"
                },
                {
                    "question": "Which of the following is responsible for rendering 2D or 3D graphics?",
                    "options": ["Physics Engine", "Rendering Engine", "Audio Engine", "Input System"],
                    "answer": "Rendering Engine",
                    "blooms": "Remember"
                },
                {
                    "question": "In game development, what does 'UI' stand for?",
                    "options": ["User Interaction", "User Interface", "Unified Integration", "Universal Input"],
                    "answer": "User Interface",
                    "blooms": "Remember"
                },
                {
                    "question": "What defines the rules and behavior of objects in a game world?",
                    "options": ["Texture Mapping", "AI Scripts", "Physics Engine", "Shader Graph"],
                    "answer": "Physics Engine",
                    "blooms": "Understand"
                },
                {
                    "question": "Which component manages background music and sound effects?",
                    "options": ["Audio Engine", "Network Stack", "Renderer", "Memory Manager"],
                    "answer": "Audio Engine",
                    "blooms": "Understand"
                },
                {
                    "question": "What is 'Raycasting' mostly used for in game engines?",
                    "options": ["Processing Audio", "Collision Detection and Line of Sight", "Texturing", "Memory Allocation"],
                    "answer": "Collision Detection and Line of Sight",
                    "blooms": "Apply"
                },
                {
                    "question": "Which scripting language is predominantly used in the Unity Game Engine?",
                    "options": ["C++", "Python", "C#", "Java"],
                    "answer": "C#",
                    "blooms": "Remember"
                },
                {
                    "question": "What is a 'Prefab' in game engine terminology?",
                    "options": ["A pre-recorded video", "A reusable game object template", "A pre-compiled shader", "A networking protocol"],
                    "answer": "A reusable game object template",
                    "blooms": "Understand"
                },
                {
                    "question": "Which technique limits the number of rendered polygons based on camera view?",
                    "options": ["Frustum Culling", "Raytracing", "V-Sync", "Anti-aliasing"],
                    "answer": "Frustum Culling",
                    "blooms": "Apply"
                },
                {
                    "question": "What manages multiplayer connectivity in modern engines?",
                    "options": ["Rendering Pipeline", "Networking API / Middleware", "Asset Importer", "Physics Subsystem"],
                    "answer": "Networking API / Middleware",
                    "blooms": "Remember"
                }
            ],
            "part_b": [
                {
                    "question": "Explain the architecture of a modern game engine.",
                    "answer_key": "Discuss Core Systems: Rendering, Physics, Audio, Input.",
                    "blooms": "Understand"
                },
                {
                    "question": "Discuss the importance and basic mechanics of a physics engine.",
                    "answer_key": "Explain Rigidbodies, Colliders, and forces.",
                    "blooms": "Understand"
                },
                {
                    "question": "Describe the difference between 2D and 3D rendering pipelines.",
                    "answer_key": "Compare Sprites/Orthographic vs Polygons/Perspective.",
                    "blooms": "Analyze"
                },
                {
                    "question": "Analyze the role of scripting and narrative logic in game design.",
                    "answer_key": "Detail how logic connects states and narrative progression.",
                    "blooms": "Analyze"
                },
                {
                    "question": "What are the common algorithms used for collision detection?",
                    "answer_key": "Discuss AABB, SAT (Separating Axis Theorem).",
                    "blooms": "Understand"
                },
                {
                    "question": "Explain how memory management works in large scale AAA games.",
                    "answer_key": "Cover Object Pooling, Streaming, and Garbage Collection.",
                    "blooms": "Apply"
                },
                {
                    "question": "Discuss the usage of AI protocols like NavMeshes and Pathfinding.",
                    "answer_key": "Explain A* Algorithm and Node graphs for NPC traversal.",
                    "blooms": "Create"
                },
                {
                    "question": "Describe the audio engine's components (listeners, sources, and mixers).",
                    "answer_key": "Identify 3D spatialization, listeners, and emitters.",
                    "blooms": "Remember"
                }
            ],
            "part_c": [
                {
                    "question": "Design a comprehensive system architecture for a massively multiplayer online game (MMO) including server-client interaction.",
                    "answer_key": "Focus on Network topology, latency mitigation, state synchronization, and database sharding.",
                    "blooms": "Create"
                },
                {
                    "question": "Critically analyze how hardware advancements (like Raytracing algorithms) have shaped the evolution of game engine rendering.",
                    "answer_key": "Evaluate Real-time lighting vs Baked lighting, computational cost, and visual fidelity.",
                    "blooms": "Evaluate"
                }
            ]
        }

        return fallback_data
