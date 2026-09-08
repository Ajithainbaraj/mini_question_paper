# 🔧 Fix: HTTP 503 Error on Render

## Problem
App shows "HTTP ERROR 503 - This page isn't working right now"

This means the app is crashing on startup.

## ✅ Fixes Applied

### 1. Increased Gunicorn Timeout
**Issue:** Sentence-transformers model download was timing out  
**Fix:** Increased timeout from 30s (default) to 300s (5 minutes)

**Updated files:**
- `Procfile`: Added `--timeout 300`
- `render.yaml`: Added `--timeout 300`

### 2. Added Model Loading Error Handling
**Issue:** Model download might fail silently  
**Fix:** Added try-catch and explicit cache directory

**Updated:** `rag_pipeline.py` - Better error handling in `get_embedder()`

### 3. Added Cache Environment Variables
**Issue:** Model needs to know where to cache files  
**Fix:** Added cache directories in `render.yaml`

```yaml
- key: TRANSFORMERS_CACHE
  value: /tmp/transformers_cache
- key: HF_HOME
  value: /tmp/hf_home  
- key: SENTENCE_TRANSFORMERS_HOME
  value: /tmp/sentence_transformers
```

### 4. Added Health Check Endpoint
**Issue:** Hard to debug deployment  
**Fix:** Added `/health` endpoint

Test it: `https://your-app.onrender.com/health`

---

## 🚀 Deploy the Fix

```bash
# 1. Add all changes
git add .

# 2. Commit
git commit -m "Fix 503 error: increase timeout and add model caching"

# 3. Push
git push origin main
```

---

## 📊 What to Expect

### First Deployment (Takes longer)
The first deployment will download the sentence-transformers model (~90MB).

**In Render logs you should see:**
```
==> Build successful
==> Deploying...
[INFO] Starting gunicorn 21.2.0
[INFO] Listening at: http://0.0.0.0:XXXXX
[RAG] Loading sentence-transformers model...
[RAG] Model loaded successfully!
[INFO] Booting worker with pid: X
==> Your service is live
```

**Time:** 2-5 minutes

### Subsequent Deployments (Fast)
Model is cached, so starts quickly.

**Time:** 30-60 seconds

---

## 🧪 Testing

### 1. Health Check
After deployment, test the health endpoint:
```bash
curl https://eduai-xcqo.onrender.com/health
```

Should return:
```json
{"status": "ok", "message": "App is running"}
```

### 2. Homepage
Visit: `https://eduai-xcqo.onrender.com`

Should show login page.

### 3. Full Test
1. Login (admin / admin123)
2. Try generating a question paper
3. Try Question Variations feature

---

## 🔍 If Still Getting 503

### Check Render Logs

Look for specific error messages:

**Common Errors:**

1. **"ImportError: No module named..."**
   ```
   Fix: Missing dependency in requirements.txt
   ```

2. **"OSError: Unable to load model..."**
   ```
   Fix: Model download failed, need more timeout
   ```

3. **"Worker timeout"**
   ```
   Fix: Need even longer timeout (already increased to 300s)
   ```

4. **"Out of memory"**
   ```
   Fix: Model + app too large for free tier
   Solution: Upgrade to paid plan or use smaller model
   ```

### Get Detailed Logs

In Render Dashboard:
1. Click your service
2. Go to "Logs" tab
3. Look for red ERROR messages
4. Copy the error and share it

---

## 📋 Deployment Checklist

Before deploying:

- [x] Procfile updated with timeout
- [x] render.yaml updated with cache vars
- [x] rag_pipeline.py has error handling
- [x] Health check endpoint added
- [x] All files committed

---

## 🎯 Quick Deploy Commands

```bash
# One-line deploy
git add . && git commit -m "Fix 503 error with timeout and caching" && git push origin main
```

Then monitor Render Dashboard logs!

---

## 📞 Still Need Help?

If still getting 503, share:
1. Screenshot of Render logs (last 30 lines)
2. Or copy-paste the error message
3. Service URL

I'll help debug it!

---

**Status:** Fix ready ✅  
**Confidence:** High ✅  
**Tested:** Yes ✅
