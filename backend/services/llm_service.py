"""IBM Granite LLM service with retry logic and IAM token management."""
from __future__ import annotations
import asyncio
import json
import logging
import time
from typing import Any

import httpx

from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_iam_token: str | None = None
_iam_token_expiry: float = 0.0


async def _get_iam_token() -> str:
    """Fetch (or return cached) IAM bearer token."""
    global _iam_token, _iam_token_expiry
    if _iam_token and time.time() < _iam_token_expiry - 60:
        return _iam_token

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            settings.ibm_iam_url,
            data={
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                "apikey": settings.ibm_api_key,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        data = resp.json()
        _iam_token = data["access_token"]
        _iam_token_expiry = time.time() + data.get("expires_in", 3600)
        return _iam_token


SYSTEM_PROMPT = """You are a professional travel planning assistant.
Your job is to create detailed, accurate day-by-day travel itineraries based ONLY on:
1. The retrieved destination context provided below.
2. General reasoning about travel logistics, timing, and budgets.

Rules:
- NEVER invent attractions, restaurants, or hotels not mentioned in the context.
- ALWAYS output a valid JSON object with the EXACT structure shown below — no extra text.
- ALL estimated costs MUST be in Indian Rupees (INR, symbol ₹) per person.
- Keep activity descriptions concise (1-2 sentences). Use only plain ASCII characters — NO special characters, accented letters, or unicode escapes.
- Flag any outdoor activity as weather_risk: "high" if rain/storm is likely on that day.
- Do NOT include markdown fences, commentary, or any text outside the JSON block.

Output ONLY this JSON (fill every field, use 0 for free activities):
{
  "title": "<Descriptive trip title>",
  "days": [
    {
      "day": 1,
      "date": "YYYY-MM-DD",
      "morning":   {"activity": "", "location": "", "description": "", "estimated_cost": 0, "weather_risk": "low", "tips": ""},
      "afternoon": {"activity": "", "location": "", "description": "", "estimated_cost": 0, "weather_risk": "low", "tips": ""},
      "evening":   {"activity": "", "location": "", "description": "", "estimated_cost": 0, "weather_risk": "low", "tips": ""}
    }
  ],
  "total_estimated_cost": 0,
  "summary": "<2-3 sentence trip summary in plain English>"
}
"""


def _sanitise_text(text: str) -> str:
    """Remove mojibake / latin-1 misreadings from LLM output.
    Granite sometimes returns UTF-8 bytes decoded as latin-1 (e.g. cafAc, chÃ¢).
    We detect that pattern and re-encode to recover the original UTF-8 string.
    """
    try:
        # If the string contains typical mojibake signatures, re-encode as latin-1
        # then decode as utf-8 to recover the original text.
        fixed = text.encode("latin-1").decode("utf-8")
        return fixed
    except (UnicodeEncodeError, UnicodeDecodeError):
        # Either it's clean UTF-8 already or unrecoverable — return as-is.
        return text


def _build_prompt(system: str, user_content: str) -> str:
    return f"<|system|>\n{system}\n<|user|>\n{user_content}\n<|assistant|>\n"


async def call_granite(
    user_content: str,
    max_new_tokens: int = 3000,
) -> dict[str, Any]:
    """Call IBM Granite and return parsed JSON itinerary."""
    prompt = _build_prompt(SYSTEM_PROMPT, user_content)

    payload = {
        "model_id": settings.ibm_model_id,
        "project_id": settings.ibm_project_id,
        "input": prompt,
        "parameters": {
            "decoding_method": "greedy",
            "max_new_tokens": max_new_tokens,
            "stop_sequences": ["<|user|>", "<|endoftext|>"],
            "repetition_penalty": 1.05,
        },
    }

    last_exc: Exception | None = None
    for attempt in range(1, settings.llm_max_retries + 1):
        try:
            token = await _get_iam_token()
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    settings.ibm_url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                )
                if resp.status_code == 429:
                    wait = settings.llm_retry_delay * (2 ** (attempt - 1))
                    logger.warning("Rate limited. Waiting %.1fs before retry %d", wait, attempt)
                    await asyncio.sleep(wait)
                    continue
                resp.raise_for_status()
                result = resp.json()
                raw: str = result["results"][0]["generated_text"]
                generated_text = _sanitise_text(raw).strip()

                # Extract JSON block from response
                json_start = generated_text.find("{")
                json_end = generated_text.rfind("}") + 1
                if json_start == -1:
                    raise ValueError("LLM did not return JSON")
                return json.loads(generated_text[json_start:json_end])

        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
            last_exc = exc
            logger.error("LLM call attempt %d failed: %s", attempt, exc)
            if attempt < settings.llm_max_retries:
                await asyncio.sleep(settings.llm_retry_delay * attempt)

    raise RuntimeError(f"LLM call failed after {settings.llm_max_retries} retries: {last_exc}")
