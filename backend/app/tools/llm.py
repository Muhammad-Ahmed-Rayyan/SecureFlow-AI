# backend/app/tools/llm.py
# OpenAI API client wrapper with JSON mode, retries, and token accounting.
# Strictly scrubs prompts from logs to avoid leaking code or credentials.

from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx
from openai import OpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import settings

logger = logging.getLogger("secureflow.llm")


def _get_client() -> OpenAI:
    """Create OpenAI client using configured key with custom http_client."""
    client = httpx.Client()
    return OpenAI(
        api_key=settings.openai_api_key or "sk-dummy-key-for-local-tests",
        http_client=client,
    )


def _clean_json_text(text: str) -> str:
    """Strip markdown code fences and whitespace from response."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((TimeoutError, ConnectionError)),
    reraise=True,
)
def _call_openai(
    model: str,
    system_prompt: str,
    user_prompt: str,
    timeout: float = 60.0,
) -> tuple[str, dict[str, int]]:
    """Invoke OpenAI ChatCompletion with JSON mode and timeout."""
    client = _get_client()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        timeout=timeout,
    )

    content = response.choices[0].message.content or "{}"
    usage = {
        "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
        "completion_tokens": response.usage.completion_tokens if response.usage else 0,
    }
    return content, usage


def chat_json(
    model: str,
    system: str,
    user: str,
    schema_hint: str | None = None,
    timeout: float = 60.0,
) -> tuple[dict[str, Any], dict[str, int]]:
    """Invoke LLM in JSON mode and return (parsed_dict, token_usage).

    Includes one automatic JSON repair pass if initial parsing fails.
    Never logs prompt content containing sensitive code.
    """
    sys_content = system
    if schema_hint and "json" not in sys_content.lower():
        sys_content = f"{sys_content}\nYou must reply with a valid JSON object matching: {schema_hint}"

    raw_text, usage = _call_openai(model, sys_content, user, timeout=timeout)
    cleaned = _clean_json_text(raw_text)

    try:
        parsed = json.loads(cleaned)
        return parsed, usage
    except json.JSONDecodeError:
        logger.warning("Initial JSON parsing failed. Attempting repair pass.")
        # Repair pass
        repair_sys = "You are a JSON repair tool. Output only the repaired valid JSON object with no surrounding prose."
        repair_raw, repair_usage = _call_openai(
            model=model,
            system_prompt=repair_sys,
            user_prompt=f"Fix this corrupted JSON text into valid JSON:\n{cleaned}",
            timeout=30.0,
        )
        usage["prompt_tokens"] += repair_usage["prompt_tokens"]
        usage["completion_tokens"] += repair_usage["completion_tokens"]

        repaired_clean = _clean_json_text(repair_raw)
        parsed = json.loads(repaired_clean)
        return parsed, usage
