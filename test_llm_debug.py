#!/usr/bin/env python3
"""
LLM Debug Test Script
Run this to diagnose exact LLM errors
"""

import os
from groq import Groq
from dotenv import load_dotenv
import json

load_dotenv()

print("="*70)
print("🔍 LLM ERROR DIAGNOSIS TOOL")
print("="*70)
print()

# Setup
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    print("❌ GROQ_API_KEY not found in .env file!")
    print("   Fix: Add GROQ_API_KEY=your_key_here to .env")
    exit(1)

print(f"✅ API Key found: {api_key[:10]}...{api_key[-4:]}")
print()

client = Groq(api_key=api_key)

# Available models to test
models_to_test = [
    ("groq/compound-mini", "Fast model - recommended"),
    ("openai/gpt-oss-20b", "Medium model"),
    ("openai/gpt-oss-120b", "Current model - slowest"),
]

print("Testing models...")
print("-"*70)

working_models = []
failed_models = []

for model, description in models_to_test:
    print(f"\n📝 Testing: {model}")
    print(f"   Description: {description}")
    
    # Test 1: Simple response
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say 'hello'"}],
            temperature=0.5,
            max_tokens=50
        )
        result = response.choices[0].message.content
        print(f"   ✅ Simple response: {result[:50]}")
        
        # Test 2: JSON mode
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": 'Return JSON only: {"status": "ok"}'}],
                response_format={"type": "json_object"},
                temperature=0.5,
                max_tokens=100
            )
            json_result = response.choices[0].message.content
            parsed = json.loads(json_result)
            print(f"   ✅ JSON mode: {json_result[:50]}")
            working_models.append((model, description))
        except Exception as e:
            print(f"   ⚠️  JSON mode failed: {str(e)[:60]}")
            failed_models.append((model, f"JSON mode error: {str(e)[:50]}"))
            
    except Exception as e:
        print(f"   ❌ FAILED: {str(e)[:80]}")
        failed_models.append((model, str(e)[:80]))

print("\n" + "="*70)
print("📊 TEST RESULTS")
print("="*70)

if working_models:
    print(f"\n✅ {len(working_models)} WORKING MODEL(S):")
    for model, desc in working_models:
        print(f"   • {model}")
        print(f"     {desc}")
else:
    print("\n❌ NO WORKING MODELS FOUND!")

if failed_models:
    print(f"\n⚠️  {len(failed_models)} FAILED MODEL(S):")
    for model, error in failed_models:
        print(f"   • {model}")
        print(f"     Error: {error}")

print("\n" + "="*70)
print("💡 RECOMMENDATIONS")
print("="*70)

if working_models:
    best_model = working_models[0][0]
    print(f"\n✅ Use this model in question_generator.py:")
    print(f"\n   MODEL = \"{best_model}\"")
    print(f"\n   Edit line 12 in question_generator.py")
else:
    print("\n❌ All models failed! Possible issues:")
    print("   1. API key invalid/expired")
    print("   2. Network/firewall blocking Groq")
    print("   3. Groq service down (check status.groq.com)")
    print("   4. Rate limit exceeded (wait 5 minutes)")

print("\n" + "="*70)
print("🔧 NEXT STEPS")
print("="*70)
print("""
If models are working:
  1. Update MODEL in question_generator.py
  2. Restart your app: python app.py
  
If models are failing:
  1. Check error messages above
  2. Verify API key at console.groq.com
  3. Check network connection
  4. Try again in 5 minutes (rate limit)
  5. See FIX_LLM_ERRORS.md for detailed solutions
""")
