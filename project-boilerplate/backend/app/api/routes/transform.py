"""
transform.py - Persona Transformer API Routes

POST /api/v1/transform        -> rewrite draft for one persona
POST /api/v1/transform/batch  -> rewrite for multiple personas in parallel
POST /api/v1/translate        -> translate draft to target language
"""

import asyncio
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.security import get_current_user
from app.db import sqlite as db
from app.schemas.common import AIResponse, AIMeta
from app.services.llm_service import generate_json, generate

router = APIRouter()

# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class PersonaConfig(BaseModel):
    id: str
    label: str
    description: str
    tone: Optional[str] = None
    custom_instructions: Optional[str] = None


class TransformRequest(BaseModel):
    draft: str = Field(..., min_length=1, description="Original rough draft text")
    persona: PersonaConfig
    target_language: Optional[str] = None  # e.g. "Hindi", "Spanish"

    model_config = {"json_schema_extra": {
        "example": {
            "draft": "API integration is delayed by 3 days. Need more people.",
            "persona": {
                "id": "executive",
                "label": "Executive / C-Level",
                "description": "Concise, strategic, confident, and focused on outcomes."
            }
        }
    }}


class ChangeAnalysis(BaseModel):
    change_percent: float
    meaning_preserved: str   # "High" | "Medium" | "Low"
    tone_shift: str          # e.g. "Casual → Executive"
    key_changes: list[str]


class TransformResult(BaseModel):
    output_id: Optional[str] = None
    persona_id: str
    persona_label: str
    original: str
    rewritten: str
    language: Optional[str] = None
    analysis: ChangeAnalysis


class BatchTransformRequest(BaseModel):
    draft: str = Field(..., min_length=1)
    personas: list[PersonaConfig] = Field(..., min_length=1)
    target_language: Optional[str] = None
    chat_id: Optional[str] = None


class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1)
    target_language: str = Field(..., description="Target language name, e.g. 'Hindi'")


class OutputFeedbackRequest(BaseModel):
    feedback: Optional[str] = Field(default=None, pattern="^(like|dislike)$")


def _persist_results(
    user_id: str,
    chat_id: Optional[str],
    draft: str,
    personas: list[PersonaConfig],
    target_language: Optional[str],
    results: list[dict],
) -> list[dict]:
    persisted = []
    now = datetime.now(timezone.utc).isoformat()
    chat_id = chat_id or str(uuid.uuid4())
    with db.get_conn() as conn:
        existing = conn.execute("SELECT user_id FROM chats WHERE id = ?", (chat_id,)).fetchone()
        if existing and existing["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Chat does not belong to this user")
        conn.execute(
            """
            INSERT INTO chats (id, user_id, title, selected_ids, target_language, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title = excluded.title,
                selected_ids = excluded.selected_ids,
                target_language = excluded.target_language,
                updated_at = excluded.updated_at
            """,
            (
                chat_id,
                user_id,
                " ".join(draft.split())[:60] or "New chat",
                db.dumps([persona.id for persona in personas]),
                target_language,
                now,
                now,
            ),
        )
        for result in results:
            if result.get("error") or not result.get("rewritten"):
                persisted.append(result)
                continue
            output_id = str(uuid.uuid4())
            result["output_id"] = output_id
            conn.execute(
                """
                INSERT INTO outputs (
                    id, user_id, chat_id, persona_id, persona_label, original,
                    rewritten, language, analysis_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    output_id,
                    user_id,
                    chat_id,
                    result["persona_id"],
                    result["persona_label"],
                    result["original"],
                    result["rewritten"],
                    result.get("language"),
                    db.dumps(result.get("analysis")),
                    now,
                ),
            )
            persisted.append(result)
    return persisted


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _levenshtein_distance(s1: str, s2: str) -> int:
    """Compute Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev = list(range(len(s2) + 1))
    for c1 in s1:
        curr = [prev[0] + 1]
        for j, c2 in enumerate(s2):
            curr.append(min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (c1 != c2)))
        prev = curr
    return prev[-1]


def _compute_change_percent(original: str, rewritten: str) -> float:
    """Normalized edit distance as a change percentage."""
    if not original.strip():
        return 0.0
    dist = _levenshtein_distance(original.strip(), rewritten.strip())
    max_len = max(len(original.strip()), len(rewritten.strip()))
    return round(min(100.0, (dist / max_len) * 100), 1)


EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002700-\U000027BF"
    "\U0001F900-\U0001F9FF"
    "\U00002600-\U000026FF"
    "\U0001FA00-\U0001FAFF"
    "\U0001FA70-\U0001FAFF"
    "\U0000200D"
    "\U0000FE0F"
    "]+",
    flags=re.UNICODE,
)


def strip_emojis(text: str) -> str:
    cleaned = EMOJI_RE.sub("", text or "")
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


TRANSFORM_SYSTEM = """You are an expert communication coach and writing assistant.
Your job is to rewrite the user's draft for a specific target audience (persona).

Rules:
- Preserve ALL factual content: names, numbers, dates, deadlines, commitments.
- Do NOT invent new facts or make promises not in the original.
- Match the tone, vocabulary, and style of the specified persona precisely.
- Never use emojis, emoticons, or decorative symbols anywhere in the rewritten text.
- Output ONLY valid JSON matching the exact schema requested.
"""

TRANSFORM_PROMPT_TEMPLATE = """Rewrite the following draft for the "{label}" persona.

Persona description: {description}
{tone_line}
{instructions_line}
{language_line}

Draft:
\"\"\"
{draft}
\"\"\"

Return a JSON object with exactly these keys:
{{
  "rewritten": "<rewritten message as a string>",
  "tone_shift": "<e.g. Casual → Executive>",
  "meaning_preserved": "<High | Medium | Low>",
  "key_changes": ["<change 1>", "<change 2>", "<change 3>"]
}}
"""

TRANSLATE_SYSTEM = """You are a professional translator. Translate the text accurately while:
- Preserving all names, numbers, dates, and factual content.
- Maintaining the original tone and structure.
- Producing natural, fluent output in the target language.
Output ONLY valid JSON.
"""

TRANSLATE_PROMPT_TEMPLATE = """Translate the following text into {target_language}.

Text:
\"\"\"
{text}
\"\"\"

Return a JSON object:
{{
  "translated": "<translated text>"
}}
"""


async def _transform_single(draft: str, persona: PersonaConfig, target_language: Optional[str]) -> TransformResult:
    """Call LLM to rewrite draft for one persona, optionally in a different language."""
    tone_line = f"Preferred tone: {persona.tone}" if persona.tone else ""
    instructions_line = f"Additional instructions: {persona.custom_instructions}" if persona.custom_instructions else ""
    language_line = f"IMPORTANT: Output the rewritten text in {target_language} language." if target_language else ""

    prompt = TRANSFORM_PROMPT_TEMPLATE.format(
        label=persona.label,
        description=persona.description,
        tone_line=tone_line,
        instructions_line=instructions_line,
        language_line=language_line,
        draft=draft,
    )

    data, _meta = await generate_json(
        prompt,
        system=TRANSFORM_SYSTEM,
        temperature=0.5,
    )

    rewritten = strip_emojis(str(data.get("rewritten", "")))
    change_percent = _compute_change_percent(draft, rewritten)

    analysis = ChangeAnalysis(
        change_percent=change_percent,
        meaning_preserved=data.get("meaning_preserved", "High"),
        tone_shift=data.get("tone_shift", f"Original → {persona.label}"),
        key_changes=data.get("key_changes", [])[:5],
    )

    return TransformResult(
        persona_id=persona.id,
        persona_label=persona.label,
        original=draft,
        rewritten=rewritten,
        language=target_language,
        analysis=analysis,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/transform", response_model=AIResponse, tags=["Transform"])
async def transform_draft(req: TransformRequest, user: dict = Depends(get_current_user)):
    """
    Rewrite a draft for a single persona.
    Optionally translate the output to a target language.
    """
    if not req.draft.strip():
        raise HTTPException(400, "Draft cannot be empty")
    try:
        result = await _transform_single(req.draft, req.persona, req.target_language)
        saved_result = _persist_results(
            user["id"],
            None,
            req.draft,
            [req.persona],
            req.target_language,
            [result.model_dump()],
        )[0]
        # Use a lightweight meta since generate_json consumed the real one internally
        meta = AIMeta(provider="groq", model_used="llama-3.3-70b-versatile", latency_ms=0, fallback_used=False)
        return AIResponse(data=saved_result, meta=meta)
    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(503, detail=f"AI service unavailable: {e}")
    except Exception as e:
        raise HTTPException(500, detail=f"Transform failed: {e}")


@router.post("/transform/batch", response_model=AIResponse, tags=["Transform"])
async def transform_batch(req: BatchTransformRequest, user: dict = Depends(get_current_user)):
    """
    Rewrite a draft for multiple personas in parallel.
    Returns a list of results, one per persona.
    """
    if not req.draft.strip():
        raise HTTPException(400, "Draft cannot be empty")
    if not req.personas:
        raise HTTPException(400, "At least one persona must be selected")

    try:
        tasks = [
            _transform_single(req.draft, persona, req.target_language)
            for persona in req.personas
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        output = []
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                # Graceful degradation: return error info for failed persona
                output.append({
                    "persona_id": req.personas[i].id,
                    "persona_label": req.personas[i].label,
                    "error": str(r),
                    "rewritten": None,
                })
            else:
                output.append(r.model_dump())

        output = _persist_results(
            user["id"],
            req.chat_id,
            req.draft,
            req.personas,
            req.target_language,
            output,
        )

        meta = AIMeta(provider="groq", model_used="llama-3.3-70b-versatile", latency_ms=0, fallback_used=False)
        return AIResponse(data=output, meta=meta)
    except RuntimeError as e:
        raise HTTPException(503, detail=f"AI service unavailable: {e}")


@router.post("/translate", response_model=AIResponse, tags=["Transform"])
async def translate_text(req: TranslateRequest, _user: dict = Depends(get_current_user)):
    """
    Translate the given text into the specified target language.
    """
    if not req.text.strip():
        raise HTTPException(400, "Text cannot be empty")

    prompt = TRANSLATE_PROMPT_TEMPLATE.format(
        target_language=req.target_language,
        text=req.text,
    )
    try:
        data, _meta = await generate_json(prompt, system=TRANSLATE_SYSTEM, temperature=0.2)
        translated = strip_emojis(str(data.get("translated", "")))
        meta = AIMeta(provider="groq", model_used="llama-3.3-70b-versatile", latency_ms=0, fallback_used=False)
        return AIResponse(data={"translated": translated, "target_language": req.target_language}, meta=meta)
    except RuntimeError as e:
        raise HTTPException(503, detail=f"AI service unavailable: {e}")
    except Exception as e:
        raise HTTPException(500, detail=f"Translation failed: {e}")


@router.put("/outputs/{output_id}/feedback", tags=["Transform"])
def update_output_feedback(
    output_id: str,
    req: OutputFeedbackRequest,
    user: dict = Depends(get_current_user),
):
    with db.get_conn() as conn:
        result = conn.execute(
            "UPDATE outputs SET feedback = ? WHERE id = ? AND user_id = ?",
            (req.feedback, output_id, user["id"]),
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Output not found")
    return {"output_id": output_id, "feedback": req.feedback}
