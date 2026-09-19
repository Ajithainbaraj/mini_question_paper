#!/usr/bin/env python3
"""Verify that the correct (new) code is loaded"""

import sys
import importlib

# Clear any cached imports
if 'question_generator' in sys.modules:
    del sys.modules['question_generator']

# Import fresh
from question_generator import generate_questions
import inspect

print("="*70)
print("CODE VERIFICATION")
print("="*70)

# Get the source code of generate_questions
source = inspect.getsource(generate_questions)

# Check for key indicators of the NEW code
checks = {
    "Simplified prompt": "Generate a university exam paper from this syllabus context" in source,
    "Context size limit": "MAX_CONTEXT_SIZE = 3500" in source,
    "Total prompt logging": "total prompt:" in source,
    "NOT old verbose prompt": "You are an intelligent university question paper generator" not in source,
}

print("\nChecking if NEW code is loaded:\n")
all_good = True
for check_name, result in checks.items():
    status = "✅" if result else "❌"
    print(f"{status} {check_name}: {result}")
    if not result:
        all_good = False

print("\n" + "="*70)
if all_good:
    print("✅ CORRECT CODE IS LOADED!")
    print("="*70)
    print("\nYou can now run: python app.py")
    print("The app will use the NEW simplified prompts.")
else:
    print("❌ OLD CODE IS STILL LOADED!")
    print("="*70)
    print("\nTO FIX:")
    print("1. Close any running Python/Flask processes")
    print("2. Delete __pycache__ folder")
    print("3. Run: python -B app.py")
    print("\nOr simply run: restart_app.bat")

print()
