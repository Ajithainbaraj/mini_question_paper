import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
print(f"API Key found: {bool(api_key)}")
print(f"Key length: {len(api_key) if api_key else 0} chars")
print(f"Key preview: {api_key[:20]}..." if api_key else "No key")

# Test connection
try:
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": "Say 'Connection successful' and nothing else."}],
        temperature=0.5
    )
    print("\n✅ Groq API Test Result:")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"\n❌ Groq API Test FAILED:")
    print(f"Error: {e}")
