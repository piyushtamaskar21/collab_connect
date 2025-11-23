import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found in environment variables.")
    exit(1)

genai.configure(api_key=api_key)

def test_model(model_name):
    print(f"Testing model: {model_name}")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Hello, are you working?")
        print(f"Success! Response: {response.text}")
        return True
    except Exception as e:
        print(f"Failed to use {model_name}. Error: {e}")
        return False

print("--- Starting LLM Test ---")
test_model("gemini-3-pro-preview")
test_model("gemini-1.5-pro")
test_model("gemini-2.0-flash-exp")

def test_embedding(model_name):
    print(f"Testing embedding model: {model_name}")
    try:
        result = genai.embed_content(
            model=model_name,
            content="Hello world",
            task_type="retrieval_document",
            title="Test Document"
        )
        print(f"Success! Embedding length: {len(result['embedding'])}")
        return True
    except Exception as e:
        print(f"Failed to use {model_name}. Error: {e}")
        return False

test_embedding("models/text-embedding-004")
