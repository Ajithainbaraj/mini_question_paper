# ✅ Pre-Deployment Checklist

Complete this checklist before deploying to ensure a smooth deployment.

---

## 1. Code Verification

### Files Check
- [x] `app.py` - Updated with Question Variations routes
- [x] `question_generator.py` - Updated with correct model (`openai/gpt-oss-120b`)
- [x] All 4 new templates created in `templates/` folder
- [x] `dashboard_base.html` - Updated with navigation link
- [x] No syntax errors (run `python -m py_compile app.py`)

### Dependencies Check
- [x] `requirements.txt` - All dependencies present
- [x] No missing imports
- [x] `Procfile` - Correct gunicorn configuration
- [x] `runtime.txt` - Python 3.11.9

---

## 2. Git Repository

### Files to Commit
```bash
# Check what needs to be committed
git status
```

Should include:
- [x] Modified: `app.py`
- [x] Modified: `question_generator.py`
- [x] Modified: `templates/dashboard_base.html`
- [x] Modified: `README.md`
- [x] New: `templates/question_variations.html`
- [x] New: `templates/question_variations_concept.html`
- [x] New: `templates/question_variations_detail.html`
- [x] New: `templates/question_variations_filtered.html`
- [x] New: Documentation files (*.md)

### Files NOT to Commit
Verify these are in `.gitignore`:
- [ ] `.env` - Should NOT be committed ✅
- [ ] `__pycache__/` - Should NOT be committed ✅
- [ ] `vector_store/` - Should NOT be committed ✅
- [ ] `uploads/` - Should NOT be committed ✅
- [ ] `papers/` - Should NOT be committed ✅

---

## 3. Environment Variables

Ensure these are set on your deployment platform:

### Required
- [ ] `GROQ_API_KEY` - Your Groq API key (gsk_...)
  - Get from: https://console.groq.com
  - Current value: `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`

### Auto-Generated (if using Render)
- [ ] `SECRET_KEY` - Will be auto-generated ✅

### Optional (OAuth)
- [ ] `GOOGLE_CLIENT_ID` - For Google OAuth
- [ ] `GOOGLE_CLIENT_SECRET` - For Google OAuth
- [ ] `GITHUB_CLIENT_ID` - For GitHub OAuth
- [ ] `GITHUB_CLIENT_SECRET` - For GitHub OAuth

---

## 4. Deployment Platform Check

### For Render.com
- [ ] Account logged in
- [ ] Previous deployment exists
- [ ] Git repository connected
- [ ] Auto-deploy enabled (optional)
- [ ] Environment variables set

### For Heroku
- [ ] Heroku CLI installed
- [ ] Logged in (`heroku login`)
- [ ] App exists (`heroku apps`)
- [ ] Git remote added (`git remote -v`)
- [ ] Environment variables set (`heroku config`)

---

## 5. Quick Tests (Local)

Before deploying, test locally:

```bash
# Start app
python app.py

# Open browser: http://localhost:10000
```

Test these:
- [ ] App starts without errors
- [ ] Can login (admin / admin123)
- [ ] Dashboard loads
- [ ] **Question Variations link appears in sidebar**
- [ ] **Can access /question-variations page**
- [ ] No console errors in browser

---

## 6. Deployment Commands

### Option A: Render (Recommended)

```bash
# 1. Add and commit all files
git add .
git commit -m "Add Question Variations feature and update LLM model"

# 2. Push to GitHub/GitLab
git push origin main

# 3. Render will auto-deploy (if enabled)
# Or manually deploy from Render dashboard
```

### Option B: Heroku

```bash
# 1. Set environment variable (if not set)
heroku config:set GROQ_API_KEY=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

# 2. Commit and push
git add .
git commit -m "Add Question Variations feature and update LLM model"
git push heroku main

# 3. Watch logs
heroku logs --tail
```

### Option C: Use Deploy Script

```bash
# Make script executable
chmod +x DEPLOY_NOW.sh

# Run script
./DEPLOY_NOW.sh
```

---

## 7. Post-Deployment Verification

After deployment completes:

### Check Deployment Status
- [ ] Build completed successfully
- [ ] No build errors in logs
- [ ] Service is running

### Test Application
Visit your deployed URL:

- [ ] Homepage loads
- [ ] Can login
- [ ] Dashboard displays
- [ ] **Question Variations page loads**
- [ ] **Can see "NEW" badge on nav**
- [ ] **Upload form displays**
- [ ] No 404 errors

### Test New Feature
- [ ] Upload a question bank file
- [ ] Analytics dashboard displays
- [ ] Can click on concepts
- [ ] Can generate variations
- [ ] All 10 variation types show
- [ ] PDF download works

---

## 8. Troubleshooting Ready

If issues occur:

- [ ] Have access to deployment logs
- [ ] Know how to rollback (see DEPLOYMENT_GUIDE.md)
- [ ] Can access error messages
- [ ] Have backup of previous working version

---

## 9. Documentation

- [x] README.md updated with new feature
- [x] DEPLOYMENT_GUIDE.md created
- [x] QUICK_START_QUESTION_VARIATIONS.md available
- [x] All feature documentation in place

---

## 10. Final Checks

Before clicking "Deploy":

- [ ] All code committed
- [ ] No uncommitted changes (`git status` clean)
- [ ] `.env` file NOT committed
- [ ] Environment variables set on platform
- [ ] Deployment branch is correct (usually `main`)
- [ ] Ready to monitor deployment

---

## ✅ Ready to Deploy!

If all boxes are checked, you're ready to deploy!

### Quick Deploy Steps:

1. **Commit everything:**
   ```bash
   git add .
   git commit -m "Add Question Variations feature and update LLM model"
   ```

2. **Push to your platform:**
   ```bash
   # For Render (connected to GitHub)
   git push origin main
   
   # OR for Heroku
   git push heroku main
   ```

3. **Monitor deployment:**
   - Watch logs on your platform dashboard
   - Wait 5-15 minutes for first build
   - Check for "Build successful" message

4. **Test your app:**
   - Open your deployed URL
   - Login and test features
   - Verify Question Variations works

---

## 📞 Need Help?

- See: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions
- Check: Platform-specific documentation
- Review: Error logs for specific issues

---

**Deployment Target:** ___________  
**Deployment Date:** ___________  
**Deployed By:** ___________  
**Status:** ___________ 

---

**Good luck! 🚀**
