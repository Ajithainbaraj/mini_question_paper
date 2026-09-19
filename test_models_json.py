import os
from dotenv import load_dotenv
from groq import Groq
import json

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

test_models = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.8-27b",
    "groq/compound"
]

prompt = """Return a simple JSON with this structure:
{
  "test": "success",
  "number": 42
}"""

print("Testing JSON mode for different models...\n")

for model_name in test_models:
    print(f"Testing: {model_name}")
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        # Try to parse
        data = json.loads(content)
        print(f"   ✅ SUCCESS - Got valid JSON: {data}")
    except Exception as e:
        error_str = str(e)
        if "json_validate_failed" in error_str:
            print(f"   ❌ JSON validation failed")
        else:
            print(f"   ❌ Error: {error_str[:100]}")
    print()
