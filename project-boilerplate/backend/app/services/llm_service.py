"""
llm_service.py - Groq (multi-key rotation) <-> Gemini router with automatic fallback + telemetry.

Quick test (from backend/ after filling .env):
    uv run python -c "import asyncio; from app.services.llm_service import generate; print(asyncio.run(generate('Say hi in 5 words')))"

In routes: catch RuntimeError -> raise HTTPException(503, ...).
"""

import json
import re
import time
from typing import Any, Literal, Optional

from google import genai
from google.genai import types
from groq import AsyncGroq

from app.core.config import get_settings
from app.schemas.common import AIMeta

Provider = Literal["groq", "gemini"]

_groq_clients: dict[str, AsyncGroq] = {}
_gemini_client: Optional[genai.Client] = None
_rr_index = 0  # round-robin pointer over Groq keys


def _groq(key: str) -> AsyncGroq:
    if key not in _groq_clients:
        _groq_clients[key] = AsyncGroq(api_key=key)
    return _groq_clients[key]


def _gemini() -> genai.Client:
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = genai.Client(api_key=get_settings().gemini_api_key)
    return _gemini_client


async def _call_groq(prompt: str, system: Optional[str], model: str,
                     json_mode: bool, temperature: float) -> str:
    """Round-robin over all Groq keys; if one key fails (429 etc.), try the next."""
    global _rr_index
    keys = get_settings().groq_keys
    if not keys:
        raise RuntimeError("No Groq key set (GROQ_API_KEYS / GROQ_API_KEY)")

    if json_mode:
        system = (system or "") + "\nRespond ONLY with valid JSON."
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    kwargs: dict[str, Any] = dict(model=model, messages=messages, temperature=temperature)
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    last_exc: Optional[Exception] = None
    for i in range(len(keys)):
        key = keys[(_rr_index + i) % len(keys)]
        try:
            resp = await _groq(key).chat.completions.create(**kwargs)
            _rr_index = (_rr_index + i + 1) % len(keys)  # next call starts at next key
            return resp.choices[0].message.content or ""
        except Exception as exc:
            last_exc = exc
    _rr_index = (_rr_index + 1) % len(keys)
    raise last_exc  # type: ignore[misc]


async def _call_gemini(prompt: str, system: Optional[str], model: str,
                       json_mode: bool, temperature: float) -> str:
    config = types.GenerateContentConfig(
        system_instruction=system,
        temperature=temperature,
        response_mime_type="application/json" if json_mode else None,
    )
    resp = await _gemini().aio.models.generate_content(
        model=model, contents=prompt, config=config
    )
    return resp.text or ""


async def generate(
    prompt: str,
    *,
    system: Optional[str] = None,
    json_mode: bool = False,
    prefer: Provider = "groq",
    fast: bool = False,
    reasoning: bool = False,
    pro: bool = False,
    temperature: float = 0.3,
) -> tuple[str, AIMeta]:
    """
    Returns (text, AIMeta). Tries `prefer` first, then the other provider.
    fast=True      -> llama-3.1-8b-instant (routing/classification)
    reasoning=True -> openai/gpt-oss-120b on Groq
    pro=True       -> Gemini Pro
    """
    s = get_settings()
    if reasoning:
        groq_model = s.groq_reasoning_model
    elif fast:
        groq_model = s.groq_fast_model
    else:
        groq_model = s.groq_default_model
    models = {
        "groq": groq_model,
        "gemini": s.gemini_pro_model if pro else s.gemini_default_model,
    }
    callers = {"groq": _call_groq, "gemini": _call_gemini}
    order: list[Provider] = ["groq", "gemini"] if prefer == "groq" else ["gemini", "groq"]

    errors: list[str] = []
    for idx, provider in enumerate(order):
        start = time.perf_counter()
        try:
            text = await callers[provider](prompt, system, models[provider], json_mode, temperature)
            meta = AIMeta(
                provider=provider,
                model_used=models[provider],
                latency_ms=int((time.perf_counter() - start) * 1000),
                fallback_used=idx > 0,
            )
            return text, meta
        except Exception as exc:  # rate limit, bad key, timeout -> fall through
            errors.append(f"{provider}: {exc}")
    raise RuntimeError("All LLM providers failed -> " + " | ".join(errors))


def _parse_json(text: str) -> Any:
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\}|\[.*\])", text, flags=re.DOTALL)
        if match:
            return json.loads(match.group(1))
        raise


async def generate_json(prompt: str, **kwargs: Any) -> tuple[Any, AIMeta]:
    """Same as generate() but returns parsed JSON."""
    text, meta = await generate(prompt, json_mode=True, **kwargs)
    return _parse_json(text), meta
