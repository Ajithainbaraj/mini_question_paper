import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

print("Fetching available Groq models...\n")

try:
    models = client.models.list()
    
    print("Available models:")
    print("-" * 80)
    for model in models.data:
        print(f"ID: {model.id}")
        print(f"   Owned by: {model.owned_by}")
        if hasattr(model, 'active'):
            print(f"   Active: {model.active}")
        print()
        
except Exception as e:
    print(f"Error fetching models: {e}")
