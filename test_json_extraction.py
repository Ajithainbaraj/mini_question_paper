#!/usr/bin/env python3
"""Test the robust JSON extraction"""

from question_generator import _extract_json_robust
import json

print("Testing robust JSON extraction...\n")

# Test 1: Clean JSON
print("Test 1: Clean JSON")
test1 = '{"mcqs": [], "part_b": [], "part_c": []}'
try:
    result = _extract_json_robust(test1)
    print(f"✅ PASS: {result}")
except Exception as e:
    print(f"❌ FAIL: {e}")

print()

# Test 2: JSON with text before
print("Test 2: JSON with text before")
test2 = 'Here is the JSON:\n{"mcqs": [], "part_b": [], "part_c": []}'
try:
    result = _extract_json_robust(test2)
    print(f"✅ PASS: {result}")
except Exception as e:
    print(f"❌ FAIL: {e}")

print()

# Test 3: JSON with text after
print("Test 3: JSON with text after")
test3 = '{"mcqs": [], "part_b": [], "part_c": []}\nHope this helps!'
try:
    result = _extract_json_robust(test3)
    print(f"✅ PASS: {result}")
except Exception as e:
    print(f"❌ FAIL: {e}")

print()

# Test 4: JSON in code block
print("Test 4: JSON in code block")
test4 = '```json\n{"mcqs": [], "part_b": [], "part_c": []}\n```'
try:
    result = _extract_json_robust(test4)
    print(f"✅ PASS: {result}")
except Exception as e:
    print(f"❌ FAIL: {e}")

print()

# Test 5: Complex nested JSON
print("Test 5: Complex nested JSON")
test5 = '''{"mcqs": [{"question": "test", "options": ["A", "B"], "answer": "A", "blooms": "Remember"}], "part_b": [], "part_c": []}'''
try:
    result = _extract_json_robust(test5)
    print(f"✅ PASS: {len(result['mcqs'])} MCQs found")
except Exception as e:
    print(f"❌ FAIL: {e}")

print()

# Test 6: Invalid - no JSON
print("Test 6: Invalid - no JSON (should fail)")
test6 = "This is just plain text with no JSON"
try:
    result = _extract_json_robust(test6)
    print(f"❌ Should have failed but got: {result}")
except Exception as e:
    print(f"✅ PASS: Correctly detected invalid JSON")

print("\n" + "="*60)
print("All tests completed!")
