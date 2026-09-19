# 🔄 How to Restart Your App with Fixed Code

## The Problem

You're seeing old error messages like:
```
⚠️ Prompt too large (6231 chars), truncating to 6000
[DEBUG] Response received: 0 chars
```

This means your Flask app is still running the **OLD code** from memory/cache.

---

## ✅ Solution: Restart the App

### Method 1: Use the Restart Script (Easiest)

Double-click this file in Windows Explorer:
```
restart_app.bat
```

This will:
1. ✅ Stop all Python processes
2. ✅ Clear Python cache
3. ✅ Start app with fresh code

---

### Method 2: Manual Restart

#### Step 1: Stop the App
In your terminal where the app is running, press:
```
Ctrl + C
```

Or kill all Python processes:
```bash
taskkill /F /IM python.exe /T
```

#### Step 2: Clear Cache
```bash
rmdir /s /q __pycache__
```

#### Step 3: Start Fresh
```bash
python -B app.py
```

The `-B` flag prevents Python from creating cache files.

---

### Method 3: Verify Then Restart

#### First, verify the correct code is ready:
```bash
python verify_code_loaded.py
```

You should see:
```
✅ CORRECT CODE IS LOADED!
```

#### Then restart:
```bash
# Stop old app (Ctrl+C or taskkill)
taskkill /F /IM python.exe /T

# Start fresh
python -B app.py
```

---

## How to Know It Worked

### ❌ OLD Code (Wrong):
```
[DEBUG] Sending to Groq (context: 4287 chars)
⚠️ Prompt too large (6231 chars), truncating to 6000
[DEBUG] Response received: 0 chars
```

### ✅ NEW Code (Correct):
```
[DEBUG] Sending to Groq (context: 3500 chars, total prompt: 3900 chars)
[DEBUG] Response received: 5851 chars
[DEBUG] Response preview: {"mcqs": [{"question": ...
```

**Key differences:**
1. ✅ Shows "total prompt: XXXX chars" (NEW feature)
2. ✅ Context is limited to 3500 chars (NEW feature)
3. ✅ Total prompt is ~3900 chars (not 6231)
4. ✅ Response is NOT empty (has 5000+ chars)

---

## Quick Commands Reference

```bash
# 1. Verify code is correct
python verify_code_loaded.py

# 2. Stop old app
taskkill /F /IM python.exe /T

# 3. Clear cache
rmdir /s /q __pycache__

# 4. Start fresh
python -B app.py
```

Or just:
```bash
restart_app.bat
```

---

## Test After Restart

1. Open: http://localhost:5000/papers
2. Upload a syllabus file
3. Generate questions
4. Check console output - should see NEW format
5. Should get 10 MCQs, 8 Part B, 2 Part C ✅

---

## Still Seeing Old Messages?

### Check 1: Is the app actually restarted?
```bash
tasklist | findstr python
```
Should show only ONE python.exe process.

### Check 2: Are you editing the right file?
```bash
python verify_code_loaded.py
```
Should say "✅ CORRECT CODE IS LOADED!"

### Check 3: Is there a different app running?
Check the port - maybe another instance on different port?

---

## Important Notes

1. **Always restart** after code changes
2. **Use `-B` flag** to prevent caching issues
3. **Clear __pycache__** if you see old behavior
4. **Watch console output** to confirm new code is running

---

## Summary

**The fix is already in the code!** You just need to restart the Flask app to load it.

### Fastest Way:
```bash
Double-click: restart_app.bat
```

Then visit: http://localhost:5000/papers

**Problem solved!** 🎉
