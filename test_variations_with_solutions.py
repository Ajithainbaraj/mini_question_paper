#!/usr/bin/env python3
"""
Quick test script to verify question variations generate with solutions.
Run this to check if the code changes are working before testing in browser.
"""

import os
from dotenv import load_dotenv
load_dotenv()

# Import the function
from question_generator import generate_question_variations

# Test question
test_question = {
    "id": 1,
    "question": "Solve the quadratic equation x² - 5x + 6 = 0",
    "concept": "Quadratic Equations",
    "formula": "ax² + bx + c = 0",
    "chapter": "Algebra",
    "difficulty": "Easy"
}

print("=" * 70)
print("🧪 TESTING: Question Variations with Solutions")
print("=" * 70)
print()

print(f"📝 Original Question: {test_question['question']}")
print(f"📚 Concept: {test_question['concept']}")
print(f"📖 Chapter: {test_question['chapter']}")
print()

print("🔄 Generating variations...")
print()

try:
    # Generate variations
    variations = generate_question_variations(test_question, num_variations=3)  # Test with 3 for speed
    
    print(f"✅ Generated {len(variations)} variations")
    print()
    print("=" * 70)
    
    # Check each variation
    all_have_solutions = True
    for i, v in enumerate(variations, 1):
        print()
        print(f"Variation {i}: {v.get('type', 'Unknown Type')}")
        print("-" * 70)
        print(f"Question: {v.get('question', 'N/A')[:100]}...")
        print(f"Hint: {v.get('hint', 'N/A')[:80]}...")
        print(f"Difficulty: {v.get('difficulty', 'N/A')}")
        
        # Check if solution exists
        solution = v.get('solution', '')
        if solution and len(solution) > 10:
            print(f"✅ Solution: Present ({len(solution)} chars)")
            print(f"   Preview: {solution[:100]}...")
        else:
            print(f"❌ Solution: Missing or too short!")
            all_have_solutions = False
        print()
    
    print("=" * 70)
    print()
    
    # Final result
    if all_have_solutions:
        print("🎉 SUCCESS! All variations have solutions!")
        print()
        print("✅ Code is working correctly")
        print("✅ Ready to test in browser")
        print()
        print("Next steps:")
        print("1. Restart app: restart_app.bat")
        print("2. Open: http://localhost:5000/question-variations")
        print("3. Upload a math question bank")
        print("4. Generate variations and verify solutions appear")
    else:
        print("❌ FAILURE! Some variations are missing solutions")
        print()
        print("Possible causes:")
        print("1. LLM didn't return solutions in JSON")
        print("2. JSON parsing issue")
        print("3. API rate limit")
        print()
        print("Check console output above for errors")
    
    print()
    print("=" * 70)
    
except Exception as e:
    print()
    print("❌ ERROR occurred during generation!")
    print(f"Error: {type(e).__name__}: {e}")
    print()
    print("Possible causes:")
    print("1. GROQ_API_KEY not set in .env")
    print("2. API is down or rate limited")
    print("3. Code has syntax errors")
    print()
    print("Check the error above for details")
    print("=" * 70)
