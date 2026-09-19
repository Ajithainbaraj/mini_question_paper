#!/usr/bin/env python3
"""Test to debug empty response issue"""

from question_generator import generate_questions
import os

print("="*70)
print("Testing Question Generation with Minimal Context")
print("="*70)

# Test with small context
small_context = """
Computer Networks
1. OSI Model - 7 layers
2. TCP/IP Protocol
3. IP Addressing and Subnetting
4. Routing Algorithms
5. Network Security
"""

print(f"\nTest Context ({len(small_context)} chars):")
print(small_context)
print("\n" + "="*70)
print("Calling generate_questions...")
print("="*70 + "\n")

try:
    result = generate_questions(small_context, difficulty="medium")
    
    print("\n" + "="*70)
    print("✅ SUCCESS!")
    print("="*70)
    print(f"MCQs: {len(result.get('mcqs', []))}")
    print(f"Part B: {len(result.get('part_b', []))}")
    print(f"Part C: {len(result.get('part_c', []))}")
    
    if result.get('mcqs'):
        print(f"\nFirst MCQ: {result['mcqs'][0].get('question', 'N/A')[:80]}...")
        
except Exception as e:
    print("\n" + "="*70)
    print("❌ FAILED!")
    print("="*70)
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
