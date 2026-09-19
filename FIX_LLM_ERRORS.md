# 🔧 Complete Guide to Fix LLM Errors

## ✅ Quick Diagnostics Checklist

Run these commands to diagnose your specific error:

```bash
# 1. Test API connection
python test_groq_connection.py

# 2. Check available models
python check_groq_models.py

# 3. Test question generation
python test_question_generation.py

# 4. Check environment variables
python check_env.py
```

---

## 🚨 Common LLM Errors & Fixes

### **Error 1: Rate Limit Exceeded (429)**

**Symptom:**
```
⚠️ Groq attempt 1/3 failed: 429 Too Many Requests
Rate limited — waiting 15s before retry...
```

**Causes:**
- Too many API requests in short time
- Groq free tier limits: ~30 requests/minute

**Fix 1: Increase Retry Wait Time**
```python
# In question_generator.py, line 32
wait = 30 * attempt  # Change from 15 to 30 seconds
```

**Fix 2: Add Rate Limiting to Your App**
```python
import time
from functools import wraps

def rate_limit(calls=10, period=60):
    """Decorator to limit function calls"""
    times = []
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            times[:] = [t for t in times if now - t < period]
            if len(times) >= calls:
                sleep_time = period - (now - times[0])
                print(f"⏳ Rate limit reached. Waiting {sleep_time:.1f}s")
                time.sleep(sleep_time)
            times.append(now)
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Apply to _call_groq
@rate_limit(calls=20, period=60)
def _call_groq(prompt: str, json_mode: bool = True, retries: int = 3) -> str:
    # ... existing code ...
```

---

### **Error 2: Model Not Found**

**Symptom:**
```
Error: Model 'openai/gpt-oss-120b' not found
```

**Fix: Update to Working Model**

Current available models from Groq (as of your check):
```python
# Recommended models (fastest to slowest):
MODEL = "groq/compound-mini"        # Fastest, good for simple tasks
MODEL = "openai/gpt-oss-20b"        # Medium speed, good quality
MODEL = "openai/gpt-oss-120b"       # Slowest, best quality (CURRENT)
MODEL = "qwen/qwen3.8-27b"          # Alternative
```

**Try switching models in `question_generator.py` line 12:**
```python
MODEL = "groq/compound-mini"  # Try this if 120b is slow or failing
```

---

### **Error 3: JSON Parsing Failures**

**Symptom:**
```
⚠️ LLM Error: JSONDecodeError: Expecting value: line 1 column 1
```

**Cause:** LLM returns non-JSON text or malformed JSON

**Fix: Enhanced JSON Extraction**

Replace the JSON parsing sections with robust extraction:

```python
def _extract_json(raw_text: str) -> dict:
    """Robust JSON extraction from LLM response"""
    import re
    import json
    
    # Method 1: Find JSON block with braces
    start = raw_text.find("{")
    end = raw_text.rfind("}") + 1
    
    if start != -1 and end > start:
        try:
            return json.loads(raw_text[start:end])
        except json.JSONDecodeError:
            pass
    
    # Method 2: Try markdown code block
    json_pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
    match = re.search(json_pattern, raw_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Method 3: Clean and retry
    cleaned = raw_text.strip()
    cleaned = re.sub(r'^[^{]*', '', cleaned)
    cleaned = re.sub(r'[^}]*$', '', cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        raise ValueError(f"Could not parse JSON from response: {raw_text[:200]}")

# Then replace in generate_questions():
data = _extract_json(content)
```

---

### **Error 4: Context Length Exceeded**

**Symptom:**
```
Error: maximum context length exceeded
```

**Fix: Truncate Context**

```python
def generate_questions(context: str, difficulty: str = "medium", ...):
    # Add at the start:
    MAX_CONTEXT = 4000  # characters
    if len(context) > MAX_CONTEXT:
        print(f"⚠️ Truncating context from {len(context)} to {MAX_CONTEXT} chars")
        context = context[:MAX_CONTEXT] + "\n... [truncated]"
    
    prompt = f"""..."""  # rest of the code
```

---

### **Error 5: API Key Invalid/Expired**

**Symptom:**
```
Error: invalid API key
Error: API key unauthorized
```

**Fix Steps:**

1. **Get New API Key:**
   - Go to https://console.groq.com/keys
   - Create new API key
   - Copy it

2. **Update `.env` file:**
```bash
GROQ_API_KEY=gsk_YOUR_NEW_KEY_HERE
```

3. **Restart the app:**
```bash
# Kill any running Python processes
taskkill /F /IM python.exe
python app.py
```

---

### **Error 6: Empty Response**

**Symptom:**
```
⚠️ LLM Error: ValueError: No JSON in response
```

**Fix: Add Fallback & Better Error Messages**

```python
def _call_groq(prompt: str, json_mode: bool = True, retries: int = 3) -> str:
    """Call Groq with automatic retry on rate limit errors."""
    for attempt in range(1, retries + 1):
        try:
            kwargs = {"response_format": {"type": "json_object"}} if json_mode else {}
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=2000,  # Add this to ensure response isn't truncated
                **kwargs
            )
            content = response.choices[0].message.content.strip()
            
            # Validate response
            if not content:
                raise ValueError("Empty response from API")
            
            if json_mode and '{' not in content:
                raise ValueError(f"No JSON in response: {content[:200]}")
            
            return content
            
        except Exception as e:
            err = str(e)
            print(f"⚠️ Groq attempt {attempt}/{retries} failed: {err[:200]}")
            
            # Detailed error logging
            if "429" in err:
                wait = 30 * attempt
                print(f"   Rate limited — waiting {wait}s before retry...")
                time.sleep(wait)
            elif "context_length_exceeded" in err:
                print("   ❌ Context too long! Reduce input size.")
                raise
            elif "invalid_api_key" in err:
                print("   ❌ API key invalid! Check .env file.")
                raise
            elif attempt < retries:
                wait = 5 * attempt
                print(f"   Retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise
    
    raise RuntimeError("All Groq retries exhausted")
```

---

### **Error 7: Connection Timeout**

**Symptom:**
```
Error: Connection timeout
Error: Read timeout
```

**Fix: Add Timeout Configuration**

```python
from groq import Groq
import httpx

# Create client with custom timeout
client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
    timeout=httpx.Timeout(60.0, connect=10.0)  # 60s total, 10s connect
)
```

---

## 🔍 Debugging Tools

### **1. Create LLM Debug Test Script**

Create `test_llm_debug.py`:

```python
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

print("Testing LLM with different scenarios...\n")

# Test 1: Simple query
print("Test 1: Simple text response")
try:
    response = client.chat.completions.create(
        model="groq/compound-mini",
        messages=[{"role": "user", "content": "Say hello"}],
        temperature=0.5
    )
    print(f"✅ Success: {response.choices[0].message.content}")
except Exception as e:
    print(f"❌ Failed: {e}")

print("\n" + "="*60 + "\n")

# Test 2: JSON mode
print("Test 2: JSON mode response")
try:
    response = client.chat.completions.create(
        model="groq/compound-mini",
        messages=[{"role": "user", "content": 'Return JSON: {"status": "ok", "number": 42}'}],
        response_format={"type": "json_object"},
        temperature=0.5
    )
    print(f"✅ Success: {response.choices[0].message.content}")
except Exception as e:
    print(f"❌ Failed: {e}")

print("\n" + "="*60 + "\n")

# Test 3: Long context
print("Test 3: Long context (4000 chars)")
try:
    long_text = "word " * 800  # ~4000 chars
    response = client.chat.completions.create(
        model="groq/compound-mini",
        messages=[{"role": "user", "content": f"Summarize: {long_text}"}],
        temperature=0.5
    )
    print(f"✅ Success: {response.choices[0].message.content[:100]}...")
except Exception as e:
    print(f"❌ Failed: {e}")

print("\nAll tests complete!")
```

Run it:
```bash
python test_llm_debug.py
```

---

### **2. Enable Detailed Logging**

Add to `app.py` at the top:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('llm_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
```

Then add logging in `_call_groq`:
```python
logger.debug(f"Sending to Groq: {prompt[:200]}...")
logger.debug(f"Response: {content[:200]}...")
```

---

## 📊 Performance Optimization

### **Reduce API Calls:**

```python
# Cache frequent queries
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_call_groq(prompt_hash: str, json_mode: bool):
    return _call_groq(prompt_hash, json_mode)
```

### **Use Faster Models for Simple Tasks:**

```python
# Different models for different tasks
FAST_MODEL = "groq/compound-mini"     # For simple tasks
QUALITY_MODEL = "openai/gpt-oss-120b"  # For complex tasks

def _call_groq(prompt: str, json_mode: bool = True, use_fast: bool = False):
    model = FAST_MODEL if use_fast else QUALITY_MODEL
    # ... rest of code
```

---

## 🎯 Most Likely Fixes for Your Issue

Based on the code structure, try these **in order**:

### **Fix 1: Switch to Faster Model (Immediate)**

```bash
# Edit question_generator.py line 12:
MODEL = "groq/compound-mini"  # Change from gpt-oss-120b
```

### **Fix 2: Add Better Error Handling (5 min)**

Replace `_call_groq` function with the enhanced version from Error 6 above.

### **Fix 3: Increase Rate Limit Delays (1 min)**

```python
# Line 32 in question_generator.py:
wait = 30 * attempt  # Change from 15
```

### **Fix 4: Test with Debug Script (2 min)**

```bash
python test_llm_debug.py
```

This will show you the EXACT error message.

---

## 📞 Still Having Issues?

1. **Check the actual error message** in your terminal/logs
2. **Run the debug test:** `python test_llm_debug.py`
3. **Check Groq status:** https://status.groq.com
4. **Try alternate model:** Change `MODEL` variable

**Share the exact error message** and I can provide a specific fix!
