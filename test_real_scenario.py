"""Test the actual RAG pipeline + question generation workflow"""
import os
from rag_pipeline import process_syllabus, get_context_for_query
from question_generator import generate_questions

print("=" * 80)
print("TESTING REAL WORKFLOW: Upload → RAG → Question Generation")
print("=" * 80)

# Use existing sample file
sample_file = "uploads/sample.txt"

if not os.path.exists(sample_file):
    print(f"❌ Sample file not found: {sample_file}")
    print("Available files in uploads/:")
    if os.path.exists("uploads"):
        for f in os.listdir("uploads"):
            print(f"  - {f}")
else:
    print(f"\n✅ Found sample file: {sample_file}")
    
    # Step 1: Process syllabus
    print("\n📚 Step 1: Processing syllabus...")
    store_dir = "vector_store/test_scenario"
    try:
        process_syllabus(sample_file, store_dir)
        print(f"   ✅ Vector store created: {store_dir}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        exit(1)
    
    # Step 2: Retrieve context
    print("\n🔍 Step 2: Retrieving context...")
    query = "computer science"
    try:
        context = get_context_for_query(query, store_dir, top_k=5)
        print(f"   ✅ Context retrieved: {len(context)} chars")
        print(f"   Preview: {context[:200]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        exit(1)
    
    # Step 3: Generate questions
    print("\n📝 Step 3: Generating questions...")
    try:
        questions = generate_questions(context, difficulty="medium")
        
        print(f"\n✅ RESULT:")
        print(f"   MCQs: {len(questions['mcqs'])}")
        print(f"   Part B: {len(questions['part_b'])}")
        print(f"   Part C: {len(questions['part_c'])}")
        
        # Check if it's fallback
        first_mcq = questions['mcqs'][0]
        if "Sample MCQ" in first_mcq['question']:
            print(f"\n❌ WARNING: Got FALLBACK questions instead of real ones!")
            print(f"   First question: {first_mcq['question']}")
        else:
            print(f"\n✅ SUCCESS: Got real LLM-generated questions!")
            print(f"   First question: {first_mcq['question'][:100]}...")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
