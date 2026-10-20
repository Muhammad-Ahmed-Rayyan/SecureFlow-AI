# scripts/smoke_llm.py — quick OpenAI connectivity test (SF-006).
# Run: python scripts/smoke_llm.py
# Requires OPENAI_API_KEY and OPENAI_MODEL_FAST to be set in backend/.env

import json
import sys
import os

# Allow running from backend/ directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import settings
from openai import OpenAI

def main():
    if not settings.openai_api_key:
        print("ERROR: OPENAI_API_KEY is not set in .env")
        sys.exit(1)

    model = settings.openai_model_fast
    print(f"Smoke-testing model: {model}")

    client = OpenAI(api_key=settings.openai_api_key)

    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": "You are a JSON-only assistant. Always respond with valid JSON.",
            },
            {
                "role": "user",
                "content": (
                    'Reply with {"status": "ok", "message": "SecureFlow AI LLM smoke test passed"}'
                ),
            },
        ],
        max_tokens=64,
    )

    raw = response.choices[0].message.content
    parsed = json.loads(raw)
    usage = response.usage

    print("Parsed response:", json.dumps(parsed, indent=2))
    print(f"Token usage — prompt: {usage.prompt_tokens}, completion: {usage.completion_tokens}")
    print("Smoke test PASSED")


if __name__ == "__main__":
    main()
