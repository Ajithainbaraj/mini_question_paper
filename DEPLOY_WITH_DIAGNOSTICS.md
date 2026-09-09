# 🔍 Deploy with Diagnostics

## What This Does

I've added a diagnostic check (`check_env.py`) that will run BEFORE your app starts. This will show us exactly what's failing.

## 🚀 Deploy Now

```bash
git add .
git commit -m "Add diagnostic check for deployment troubleshooting"
git push origin main
```

## 📊 What to Look For in Render Logs

After pushing, go to Render Dashboard → Your Service → Logs

You should see:

```
============================================================
ENVIRONMENT DIAGNOSTIC CHECK
============================================================

✓ Python version: 3.11.9

📋 Environment Variables:
  ✓ PORT: 10000
  ✓ GROQ_API_KEY: gsk_OtTRvDMpu0Hb6...
  ✓ SECRET_KEY: SET
  ✓ TRANSFORMERS_CACHE: /tmp/transformers_cache

📦 Testing Imports:
  ✓ Flask: 3.0.3
  ✓ Groq: OK
  ✓ ReportLab: OK
  ✓ Sentence Transformers: 2.7.0
  ✓ FAISS: OK

🚀 Testing App Import:
  ✓ App imported successfully
  ✓ App name: app
  ✓ Routes count: XX

============================================================
✅ ALL CHECKS PASSED - APP IS READY
============================================================

[INFO] Starting gunicorn...
```

## 🔍 If You See ✗ (X marks)

The diagnostic will show EXACTLY which part is failing:

### If GROQ_API_KEY shows ✗:
1. Go to Render Dashboard
2. Your Service → Environment
3. Add `GROQ_API_KEY` = `your_actual_groq_api_key`
4. Click "Save Changes"

### If Sentence Transformers shows ✗:
The timeout isn't long enough. Need to increase it more or use a different approach.

### If App import shows ✗:
There's a code error. The traceback will show exactly what's wrong.

## 📸 Share the Logs

After deployment:
1. Copy the ENTIRE diagnostic output from Render logs
2. Share it with me
3. I'll tell you exactly what to fix

## 🎯 Expected Outcome

If all checks pass (all ✓), the app will start successfully and the 503 error will be gone!

---

**Deploy the fix now with those git commands above!** 🚀
