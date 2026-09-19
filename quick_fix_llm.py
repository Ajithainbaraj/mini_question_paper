#!/usr/bin/env python3
"""
Quick Fix Script for Common LLM Errors
Automatically applies recommended fixes
"""

import os
import sys

print("="*70)
print("🔧 QUICK FIX: LLM Error Auto-Repair")
print("="*70)
print()

# Check if question_generator.py exists
if not os.path.exists("question_generator.py"):
    print("❌ question_generator.py not found!")
    sys.exit(1)

print("Reading question_generator.py...")
with open("question_generator.py", "r", encoding="utf-8") as f:
    content = f.read()

original_content = content
changes_made = []

# Fix 1: Switch to faster, more reliable model
print("\n🔄 Fix 1: Switching to faster model...")
if 'MODEL = "openai/gpt-oss-120b"' in content:
    content = content.replace(
        'MODEL = "openai/gpt-oss-120b"',
        'MODEL = "groq/compound-mini"  # Auto-fixed: faster & more reliable'
    )
    changes_made.append("✅ Switched model from gpt-oss-120b to compound-mini (faster)")
else:
    print("   ℹ️  Model already changed or different format")

# Fix 2: Increase retry wait time for rate limits
print("\n🔄 Fix 2: Increasing rate limit wait time...")
if "wait = 15 * attempt" in content:
    content = content.replace(
        "wait = 15 * attempt",
        "wait = 30 * attempt  # Auto-fixed: increased from 15s"
    )
    changes_made.append("✅ Increased rate limit wait from 15s to 30s per retry")
else:
    print("   ℹ️  Wait time already modified")

# Fix 3: Add max_tokens to prevent truncation
print("\n🔄 Fix 3: Adding max_tokens parameter...")
if "temperature=0.5," in content and "max_tokens=" not in content:
    content = content.replace(
        "temperature=0.5,",
        "temperature=0.5,\n                max_tokens=2000,  # Auto-fixed: prevent truncation"
    )
    changes_made.append("✅ Added max_tokens=2000 to prevent response truncation")
else:
    print("   ℹ️  max_tokens already present or different format")

# Fix 4: Add retry count increase
print("\n🔄 Fix 4: Increasing retry attempts...")
if "retries: int = 3" in content:
    content = content.replace(
        "retries: int = 3",
        "retries: int = 5  # Auto-fixed: increased from 3"
    )
    changes_made.append("✅ Increased retry attempts from 3 to 5")
else:
    print("   ℹ️  Retry count already modified")

# Show summary
print("\n" + "="*70)
print("📊 CHANGES SUMMARY")
print("="*70)

if changes_made:
    print(f"\n✅ Applied {len(changes_made)} fix(es):\n")
    for change in changes_made:
        print(f"   {change}")
    
    # Create backup
    backup_path = "question_generator.py.backup"
    print(f"\n💾 Creating backup: {backup_path}")
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(original_content)
    
    # Write fixed file
    print("📝 Writing fixed version...")
    with open("question_generator.py", "w", encoding="utf-8") as f:
        f.write(content)
    
    print("\n" + "="*70)
    print("✅ FIXES APPLIED SUCCESSFULLY!")
    print("="*70)
    print("""
Next steps:
  1. Test the fixes: python test_llm_debug.py
  2. Run your app: python app.py
  3. If issues persist, check FIX_LLM_ERRORS.md
  
To revert changes:
  mv question_generator.py.backup question_generator.py
""")
    
else:
    print("\nℹ️  No changes needed - file already has fixes applied")
    print("   or uses different code structure.")
    print("\n   Try running: python test_llm_debug.py")
    print("   to diagnose the specific error.")
