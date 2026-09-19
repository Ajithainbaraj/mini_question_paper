#!/usr/bin/env python3
"""Test the JSON repair functionality"""

from question_generator import _repair_incomplete_json
import json

print("Testing JSON repair functionality...\n")

# Test 1: Incomplete array (truncated mid-list)
print("Test 1: Incomplete array")
test1 = '''{"total_questions": 3,"questions": [{"id": 1,"question": "Test 1"},{"id": 2,"question": "Test 2'''
try:
    result = _repair_incomplete_json(test1)
    if result:
        print(f"✅ REPAIRED: {result}")
    else:
        print("❌ Could not repair")
except Exception as e:
    print(f"❌ Error: {e}")

print()

# Test 2: Incomplete object (truncated mid-field)
print("Test 2: Incomplete object with truncated formula")
test2 = '''{"total_questions": 2,"questions": [{"id": 1,"question": "Solve x^2 = 4","chapter": "Algebra","formula": "If ax^2+bx+c=0 and factors as (x-p)(x-q)=0 then'''
try:
    result = _repair_incomplete_json(test2)
    if result:
        print(f"✅ REPAIRED: {result}")
        print(f"   Questions extracted: {result.get('total_questions')}")
    else:
        print("❌ Could not repair")
except Exception as e:
    print(f"❌ Error: {e}")

print()

# Test 3: Complete JSON (should not break it)
print("Test 3: Complete JSON (should pass through)")
test3 = '''{"total_questions": 1,"questions": [{"id": 1,"question": "Test"}]}'''
try:
    result = _repair_incomplete_json(test3)
    if result:
        print(f"✅ PASS: {result}")
    else:
        # Complete JSON returns None from repair function
        parsed = json.loads(test3)
        print(f"✅ PASS (already complete): {parsed}")
except Exception as e:
    print(f"❌ Error: {e}")

print()

# Test 4: The actual error case from your log
print("Test 4: Real error case from log")
test4 = '''{"total_questions": 20,"questions": [{"id": 1,"question": "Solve the quadratic equation x^2 - 5x + 6 = 0.","chapter": "Quadratic Equations","concept": "Solving quadratic equations by factoring","formula": "If ax^2+bx+c=0 and factors as (x-p)(x-q)=0 then'''
try:
    result = _repair_incomplete_json(test4)
    if result:
        print(f"✅ REPAIRED!")
        print(f"   Total questions: {result.get('total_questions')}")
        print(f"   Questions array length: {len(result.get('questions', []))}")
        if result.get('questions'):
            print(f"   First question: {result['questions'][0].get('question', 'N/A')[:50]}...")
    else:
        print("❌ Could not repair")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*60)
print("Testing complete!")
