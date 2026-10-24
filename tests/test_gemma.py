from dotenv import load_dotenv
from google import genai
import os

load_dotenv()

api_key = os.getenv("GEMMA_API_KEY")
model = os.getenv("GEMMA_MODEL", "gemma-2-9b-it")

if not api_key:
    print("ERROR: GEMMA_API_KEY is missing from .env")
    raise SystemExit(1)

print(f"Testing model: {model}")

try:
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=model,
        contents="Reply with exactly: Gemma API is working."
    )

    print("SUCCESS: Gemma API is working.")
    print(response.text)

except Exception as exc:
    print(f"ERROR TYPE: {type(exc).__name__}")
    print(f"ERROR DETAILS: {exc}")

