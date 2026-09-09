#!/usr/bin/env python3
"""Check environment variables and imports before starting app"""
import os
import sys

print("=" * 60)
print("ENVIRONMENT DIAGNOSTIC CHECK")
print("=" * 60)

# Check Python version
print(f"\n✓ Python version: {sys.version}")

# Check critical environment variables
env_vars = {
    "PORT": os.getenv("PORT", "NOT SET"),
    "GROQ_API_KEY": os.getenv("GROQ_API_KEY", "NOT SET")[:20] + "..." if os.getenv("GROQ_API_KEY") else "NOT SET",
    "SECRET_KEY": "SET" if os.getenv("SECRET_KEY") else "NOT SET",
    "TRANSFORMERS_CACHE": os.getenv("TRANSFORMERS_CACHE", "NOT SET"),
}

print("\n📋 Environment Variables:")
for key, value in env_vars.items():
    status = "✓" if value != "NOT SET" else "✗"
    print(f"  {status} {key}: {value}")

# Check critical imports
print("\n📦 Testing Imports:")
try:
    import flask
    print(f"  ✓ Flask: {flask.__version__}")
except Exception as e:
    print(f"  ✗ Flask: {e}")
    sys.exit(1)

try:
    import groq
    print(f"  ✓ Groq: OK")
except Exception as e:
    print(f"  ✗ Groq: {e}")
    sys.exit(1)

try:
    from reportlab.pdfgen import canvas
    print(f"  ✓ ReportLab: OK")
except Exception as e:
    print(f"  ✗ ReportLab: {e}")

try:
    import sentence_transformers
    print(f"  ✓ Sentence Transformers: {sentence_transformers.__version__}")
except Exception as e:
    print(f"  ✗ Sentence Transformers: {e}")

try:
    import faiss
    print(f"  ✓ FAISS: OK")
except Exception as e:
    print(f"  ✗ FAISS: {e}")

# Try importing the app
print("\n🚀 Testing App Import:")
try:
    from app import app
    print(f"  ✓ App imported successfully")
    print(f"  ✓ App name: {app.name}")
    print(f"  ✓ Routes count: {len(list(app.url_map.iter_rules()))}")
except Exception as e:
    print(f"  ✗ App import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ ALL CHECKS PASSED - APP IS READY")
print("=" * 60)
