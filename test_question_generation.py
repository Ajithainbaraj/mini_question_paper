from question_generator import generate_questions

# Test with a simple context
test_context = """
Computer Science Syllabus:
1. Data Structures: Arrays, Linked Lists, Stacks, Queues, Trees, Graphs
2. Algorithms: Sorting (Bubble, Quick, Merge), Searching (Linear, Binary)
3. Object-Oriented Programming: Classes, Objects, Inheritance, Polymorphism
4. Database Management: SQL, Normalization, Transactions, ACID Properties
"""

print("Testing question generation with sample context...")
print(f"Context length: {len(test_context)} chars")
print("\nGenerating questions...\n")

try:
    result = generate_questions(test_context, difficulty="medium", 
                               include_blooms=True, include_answer_key=True)
    
    print("✅ Question generation succeeded!")
    print(f"\nGenerated {len(result['mcqs'])} MCQs")
    print(f"Generated {len(result['part_b'])} Part B questions")
    print(f"Generated {len(result['part_c'])} Part C questions")
    
    # Show first MCQ to verify it's not fallback
    if result['mcqs']:
        first_mcq = result['mcqs'][0]
        print(f"\nFirst MCQ:")
        print(f"Q: {first_mcq['question']}")
        print(f"Options: {first_mcq['options']}")
        
except Exception as e:
    print(f"❌ Question generation FAILED:")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
