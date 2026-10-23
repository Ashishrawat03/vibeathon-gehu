"""Persona Transformer — Modular FastAPI + LangGraph Backend (Single File).

New Capabilities:
1. Zero-Parameter Auto-Detection (`router`):
   - Automatically detects ALL recipients/personas from the message text ("boss", "client", "friend", etc.)
     without needing the `personas` parameter.
   - Automatically detects `channel` ("email" vs "text"): Mails get full Subject + Salutation + Body + Sign-off.
   - Automatically detects `style_modifiers` ("shorter", "longer", "formal", etc.) from either the message text
     OR optional request parameters (`quick` / `style`), compressing email body while keeping email structure!
2. Language-Aware Model Routing Node (`language_router`): Dynamically switches LLM models
   based on user language (Chinese -> Qwen, Hindi/Hinglish -> GPT-OSS-120B, Arabic -> Allam, etc.).
3. Parallel Multi-Persona Generation (`Send("writer", ...)`), Citation, Judge, Auto-Retry & `InMemorySaver`.
"""

from __future__ import annotations

import difflib
import json
import os
import re
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from operator import add
from typing import Annotated, Dict, List, Literal, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, Send, interrupt
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from prompts import (
    CHANNEL_RULES,
    PERSONA_ALIASES,
    PERSONAS,
    PROMPTS,
    QUICK_FIXES,
    STYLE_KEYWORDS,
)

load_dotenv()

# ===========================================================================
# 1. CONFIGURATION & LANGUAGE-BASED MODEL REGISTRY
# ===========================================================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

MODEL_QUALITY = os.getenv("GROQ_MODEL_QUALITY", "openai/gpt-oss-120b")
MODEL_FAST = os.getenv("GROQ_MODEL_FAST", "qwen/qwen3.8-27b")

LANGUAGE_MODELS = {
    "chinese": os.getenv("GROQ_MODEL_CHINESE", "qwen/qwen3.8-27b"),
    "japanese": os.getenv("GROQ_MODEL_JAPANESE", "qwen/qwen3.8-27b"),
    "korean": os.getenv("GROQ_MODEL_KOREAN", "qwen/qwen3.8-27b"),
    "hindi": os.getenv("GROQ_MODEL_HINDI", "openai/gpt-oss-120b"),
    "hinglish": os.getenv("GROQ_MODEL_HINGLISH", "openai/gpt-oss-120b"),
    "arabic": os.getenv("GROQ_MODEL_ARABIC", "allam-2-7b"),
    "english": os.getenv("GROQ_MODEL_ENGLISH", "openai/gpt-oss-120b"),
    "default": MODEL_QUALITY,
}

DEFAULT_PERSONA = "professional"
PASS_SCORE = float(os.getenv("PASS_SCORE", "7.5"))
MAX_RETRY = int(os.getenv("MAX_RETRY", "2"))
MAX_REWRITE = int(os.getenv("MAX_REWRITE", "3"))
MEMORY_FILE = os.getenv("MEMORY_FILE", "persona_memory.json")
DEFAULT_USER = "demo"

ROLE_MODEL = {
    "router": 2,
    "chat": 2,
    "understand": 1,
    "writer": 1,
    "citation": 1,
    "judge": 1,
}
ROLE_TEMP = {
    "router": 0.0,
    "chat": 0.6,
    "understand": 0.0,
    "writer": 0.7,
    "citation": 0.0,
    "judge": 0.0,
}

_calls_lock = threading.Lock()
_db_lock = threading.Lock()
CALLS = {"writer": 0, "citation_llm": 0, "judge_llm": 0, "citation_node": 0}

if GROQ_API_KEY:
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY


def set_api_key(key: str) -> None:
    """Helper for Colab / notebooks to set the Groq API key at runtime."""
    global GROQ_API_KEY
    GROQ_API_KEY = key.strip()
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY


def make_llm(model: str, temperature: float = 0.7) -> ChatGroq:
    key = GROQ_API_KEY or os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        raise RuntimeError("GROQ_API_KEY missing. Set it in environment, .env, or via set_api_key().")
    return ChatGroq(model=model, temperature=temperature, api_key=key)


def get_llm(role: str, lang_model: Optional[str] = None) -> ChatGroq:
    if lang_model and role in ("writer", "chat", "understand"):
        model = lang_model
    else:
        model = MODEL_QUALITY if ROLE_MODEL.get(role, 1) == 1 else MODEL_FAST
    return make_llm(model, ROLE_TEMP.get(role, 0.3))


# ===========================================================================
# 2. PERMANENT JSON STORAGE (persona_memory.json)
# ===========================================================================
def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def _read_db() -> dict:
    if not os.path.exists(MEMORY_FILE):
        return {"users": {}}
    try:
        with open(MEMORY_FILE, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        os.replace(MEMORY_FILE, MEMORY_FILE + ".bad")
        return {"users": {}}


def _write_db(db: dict) -> None:
    tmp = MEMORY_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)
    os.replace(tmp, MEMORY_FILE)


def _user(db: dict, user_id: str) -> dict:
    return db["users"].setdefault(user_id, {"prefs": [], "chat": [], "runs": []})


def _find_run(u: dict, run_id: str) -> dict:
    for r in u["runs"]:
        if r["run_id"] == run_id:
            return r
    raise KeyError(f"run_id '{run_id}' nahi mila")


def add_pref(user_id: str, text: str) -> None:
    with _db_lock:
        db = _read_db()
        prefs = _user(db, user_id)["prefs"]
        if text not in prefs:
            prefs.append(text)
            _write_db(db)


def list_prefs(user_id: str) -> list:
    with _db_lock:
        return list(_user(_read_db(), user_id)["prefs"])


def delete_pref(user_id: str, index: int) -> Optional[str]:
    with _db_lock:
        db = _read_db()
        prefs = _user(db, user_id)["prefs"]
        if 0 <= index < len(prefs):
            removed = prefs.pop(index)
            _write_db(db)
            return removed
        return None


def prefs_as_text(user_id: str) -> str:
    prefs = list_prefs(user_id)
    return "\n".join(f"- {p}" for p in prefs) if prefs else "No saved preferences."


def add_chat(user_id: str, role: str, content: str) -> None:
    with _db_lock:
        db = _read_db()
        _user(db, user_id)["chat"].append({"role": role, "content": content, "time": _now()})
        _write_db(db)


def get_chat(user_id: str, last_n: int = 10) -> list:
    with _db_lock:
        chat = _user(_read_db(), user_id)["chat"][-last_n:]
        return [{"role": m["role"], "content": m["content"]} for m in chat]


def save_run(user_id: str, user_input: str, mode: str, personas: list) -> str:
    with _db_lock:
        db = _read_db()
        u = _user(db, user_id)
        run_id = f"run_{len(u['runs']) + 1}"
        u["runs"].append({
            "run_id": run_id,
            "time": _now(),
            "input": user_input,
            "mode": mode,
            "personas": personas,
            "versions": {},
            "feedback": [],
        })
        _write_db(db)
        return run_id


def add_version(user_id, run_id, persona, message, scores=None, citation=None, source="auto") -> int:
    with _db_lock:
        db = _read_db()
        run = _find_run(_user(db, user_id), run_id)
        versions = run["versions"].setdefault(persona, [])
        v = len(versions) + 1
        versions.append({
            "version": v,
            "message": message,
            "scores": scores,
            "citation": citation,
            "source": source,
            "time": _now(),
        })
        _write_db(db)
        return v


def get_versions(user_id: str, run_id: str, persona: str) -> list:
    with _db_lock:
        run = _find_run(_user(_read_db(), user_id), run_id)
        return list(run["versions"].get(persona, []))


def add_feedback(user_id: str, run_id: str, persona: str, liked: bool, comment: str = "") -> None:
    with _db_lock:
        db = _read_db()
        run = _find_run(_user(db, user_id), run_id)
        run["feedback"].append({
            "persona": persona,
            "liked": liked,
            "comment": comment,
            "time": _now(),
        })
        _write_db(db)


def recent_runs_text(user_id: str, n: int = 3) -> str:
    with _db_lock:
        runs = _user(_read_db(), user_id)["runs"][-n:]
    lines = []
    for r in runs:
        lines.append(f"Original: {r['input'][:150]}")
        for persona, vs in r["versions"].items():
            if vs:
                lines.append(f"  [{persona}] v{vs[-1]['version']}: {vs[-1]['message'][:200]}")
    return "\n".join(lines) if lines else "No rewrites yet."


def get_user_memory(user_id: str) -> dict:
    with _db_lock:
        return _user(_read_db(), user_id)


def delete_user(user_id: str) -> None:
    with _db_lock:
        db = _read_db()
        db["users"].pop(user_id, None)
        _write_db(db)


# ===========================================================================
# 3. SCHEMAS & GRAPH STATE
# ===========================================================================
class RouteDecision(BaseModel):
    mode: Literal["chat", "rewrite"] = Field(
        description="'rewrite' if the user gives a draft or asks to write/rewrite/send a mail or message, else 'chat'"
    )
    personas: List[str] = Field(
        default_factory=list,
        description="All persona keys explicitly mentioned as recipients or styles in the message.",
    )
    channel: Literal["email", "text"] = Field(
        default="text",
        description="'email' if user mentions mail/email/letter/application, else 'text'",
    )
    style_modifiers: List[str] = Field(
        default_factory=list,
        description="Any modifiers mentioned by user from: shorter, longer, formal, friendly, simpler, stronger",
    )


class Analysis(BaseModel):
    input_type: Literal["draft", "prompt"]
    language: str
    clean_text: str
    key_facts: List[str]
    goal: str


class FactCheck(BaseModel):
    fact: str
    source_quote: str
    in_draft: bool


class CitationResult(BaseModel):
    facts: List[FactCheck]
    invented_facts: List[str]


class DraftScore(BaseModel):
    tone_accuracy: int
    clarity: int
    meaning_preservation: int
    conciseness: int
    fix_suggestion: str


def merge_dicts(old, new):
    return {**(old or {}), **(new or {})}


class GraphState(TypedDict, total=False):
    user_id: str
    user_message: str
    selected_personas: List[str]
    out_lang: str
    channel: str
    style_modifiers: List[str]
    detected_language: str
    detected_script: str
    lang_model: str
    memory_text: str
    run_id: str
    mode: str
    personas: List[str]
    analysis: dict
    drafts: Annotated[List[dict], add]
    checks: Annotated[List[dict], add]
    scores: Annotated[List[dict], add]
    retries: Annotated[Dict[str, int], merge_dicts]
    rewrites: Annotated[Dict[str, int], merge_dicts]
    to_write: List[str]
    fixes: Dict[str, str]
    reply: str
    final: dict
    feedback_decision: dict


def make_input(
    user_message: str,
    selected_personas=None,
    user_id: Optional[str] = None,
    out_lang: str = "same as input",
    quick=None,
    channel: Optional[str] = None,
):
    mods = [quick] if isinstance(quick, str) else list(quick or [])
    return {
        "user_id": user_id or DEFAULT_USER,
        "user_message": user_message,
        "selected_personas": selected_personas or [],
        "out_lang": out_lang,
        "channel": channel or "",
        "style_modifiers": [m.lower().strip() for m in mods if m],
        "drafts": [],
        "checks": [],
        "scores": [],
        "retries": {},
        "rewrites": {},
        "to_write": [],
        "fixes": {},
    }


def latest_drafts(state):
    latest = {}
    for d in state.get("drafts", []):
        latest[d["persona"]] = d
    return latest


def find_item(items, persona, version):
    for x in reversed(items or []):
        if x["persona"] == persona and x["version"] == version:
            return x
    return None


def next_version(state, persona):
    return sum(1 for d in state.get("drafts", []) if d["persona"] == persona) + 1


# ===========================================================================
# 4. AUTO-DETECTION HELPERS (PERSONAS, CHANNEL, MODIFIERS, LANGUAGE)
# ===========================================================================
HINGLISH_MARKERS = {
    "bhai", "yaar", "mera", "meri", "mere", "tum", "apna", "kya", "nahi", "nhi",
    "kar", "karo", "karni", "karna", "hai", "hain", "tha", "thi", "the", "ko",
    "se", "me", "mein", "aur", "bhi", "abhi", "tak", "kal", "aaj", "din",
    "tarikh", "rupay", "rupaye", "paise", "batao", "likho", "dedo", "de", "do",
    "tabiyat", "kharab", "jaldi", "wapas", "bola", "mujhe", "sabko", "unko",
    "bhejna", "bhej", "chhota", "bada",
}


def detect_script_and_lang(text: str) -> tuple[str, str, str]:
    """Detects (script, language_key, model_id) from raw user text."""
    text = text or ""
    if re.search(r"[\u4e00-\u9fff]", text):
        return "Chinese (Hanzi)", "chinese", LANGUAGE_MODELS["chinese"]
    if re.search(r"[\u3040-\u30ff]", text):
        return "Japanese", "japanese", LANGUAGE_MODELS["japanese"]
    if re.search(r"[\uac00-\ud7af]", text):
        return "Korean (Hangul)", "korean", LANGUAGE_MODELS["korean"]
    if re.search(r"[\u0600-\u06ff]", text):
        return "Arabic", "arabic", LANGUAGE_MODELS["arabic"]
    if re.search(r"[\u0900-\u097f]", text):
        return "Devanagari", "hindi", LANGUAGE_MODELS["hindi"]

    low = text.lower()
    if "chinese" in low or "mandarin" in low:
        return "Chinese (Hanzi)", "chinese", LANGUAGE_MODELS["chinese"]

    tokens = set(re.findall(r"[a-zA-Z]+", low))
    if len(tokens & HINGLISH_MARKERS) >= 2:
        return "Latin", "hinglish", LANGUAGE_MODELS["hinglish"]

    return "Latin", "english", LANGUAGE_MODELS["english"]


def resolve_out_lang(out_lang: str, analysis: dict, user_message: str, detected_script: str, detected_lang: str) -> str:
    lang_label = (analysis or {}).get("language") or detected_lang
    if (out_lang or "").strip().lower() == "same as input":
        if detected_script == "Chinese (Hanzi)":
            return "fluent natural Chinese (matching input), written strictly in Chinese characters"
        if detected_script == "Devanagari":
            return "natural Hindi written strictly in Devanagari script"
        if detected_lang == "hinglish" or "hinglish" in lang_label.lower() or (
            detected_script == "Latin" and "hindi" in lang_label.lower()
        ):
            return (
                "natural conversational Hinglish (Hindi words written ONLY in Latin/Roman alphabet). "
                "Do NOT use Devanagari script, and do NOT write full English sentences with isolated Hindi words."
            )
        return f"the exact same language ({lang_label}) and script ({detected_script}) as the user's input"
    return out_lang


def extract_personas_from_text(text: str) -> List[str]:
    """Deterministic multi-audience extractor from raw user text (handles typos like 'clinet', 'manger')."""
    low = (text or "").lower()
    # Common typo normalization for hackathon demos
    typo_map = {
        "clinet": "client",
        "cleint": "client",
        "manger": "manager",
        "managar": "manager",
        "frined": "friend",
        "freind": "friend",
        "proffesor": "professor",
        "professer": "professor",
    }
    for bad, good in typo_map.items():
        low = re.sub(rf"\b{bad}\b", good, low)

    found = []
    # Match in order of appearance in text so user's order is preserved
    matches = []
    for alias, key in PERSONA_ALIASES.items():
        for m in re.finditer(rf"\b{re.escape(alias)}\b", low):
            matches.append((m.start(), key))
    matches.sort(key=lambda x: x[0])
    for _, key in matches:
        if key in PERSONAS and key not in found:
            found.append(key)
    return found


def detect_channel_from_text(text: str) -> str:
    """Detects whether the user wants an email/mail or a direct text message."""
    low = (text or "").lower()
    if re.search(r"\b(mail|mails|email|emails|e-mail|letter|application| ईमेल | मेल )\b", low) or "邮件" in low:
        return "email"
    return "text"


def extract_modifiers_from_text(text: str) -> List[str]:
    """Extracts style/length modifiers like 'shorter', 'formal', 'longer' directly from user text."""
    low = (text or "").lower()
    mods = []
    for kw, mod in STYLE_KEYWORDS.items():
        if re.search(rf"\b{re.escape(kw)}\b", low):
            if mod in QUICK_FIXES and mod not in mods:
                mods.append(mod)
    return mods


def clean_persona_list(items) -> List[str]:
    out = []
    for p in items or []:
        p = str(p).strip().lower()
        p = PERSONA_ALIASES.get(p, p)
        if p in PERSONAS and p not in out:
            out.append(p)
    return out


def clean_modifier_list(items) -> List[str]:
    out = []
    for m in items or []:
        m = str(m).strip().lower()
        m = STYLE_KEYWORDS.get(m, m)
        if m in QUICK_FIXES and m not in out:
            out.append(m)
    return out


def normalize_text(s):
    if not isinstance(s, str):
        return s
    for bad, good in {
        "\u2011": "-", "\u2010": "-", "\u2013": "-", "\u2014": "-",
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
    }.items():
        s = s.replace(bad, good)
    return s


def ask_structured(role, schema, system, human, tries=3, lang_model: Optional[str] = None):
    llm = get_llm(role, lang_model=lang_model).with_structured_output(schema)
    last_error = None
    for i in range(tries):
        try:
            result = llm.invoke([("system", system), ("human", human)])
            if result is None:
                raise ValueError("LLM returned empty structured output")
            return result
        except Exception as e:
            last_error = e
            time.sleep(1.5 * (i + 1))
    raise last_error


def ask_text(role, system, human, tries=3, lang_model: Optional[str] = None):
    llm = get_llm(role, lang_model=lang_model)
    last_error = None
    for i in range(tries):
        try:
            res = llm.invoke([("system", system), ("human", human)])
            text = (res.content or "").strip()
            text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
            if not text:
                raise ValueError("LLM returned empty text")
            return text
        except Exception as e:
            last_error = e
            time.sleep(1.5 * (i + 1))
    raise last_error


# ===========================================================================
# 5. LANGGRAPH NODES
# ===========================================================================
def router(state: GraphState):
    """Auto-detects mode, all recipients/personas, channel (email vs text), and style modifiers."""
    user_id = state.get("user_id", DEFAULT_USER)
    memory = prefs_as_text(user_id)
    msg = state.get("user_message", "")

    # 1. Deterministic extraction from text + explicit parameters
    explicit_personas = clean_persona_list(state.get("selected_personas"))
    text_personas = extract_personas_from_text(msg)
    explicit_mods = clean_modifier_list(state.get("style_modifiers"))
    text_mods = extract_modifiers_from_text(msg)
    det_channel = state.get("channel") or detect_channel_from_text(msg)

    # 2. Ask Router LLM for mode + any implicit personas/modifiers/channel
    persona_help = ", ".join(f"{k} ({v['label']})" for k, v in PERSONAS.items())
    system = PROMPTS["router"].format(persona_keys=persona_help)
    decision = ask_structured("router", RouteDecision, system, f"USER MESSAGE: {msg}")

    if decision.mode == "chat" and not explicit_personas and not text_personas:
        return {
            "mode": "chat",
            "personas": [],
            "channel": "text",
            "style_modifiers": [],
            "memory_text": memory,
        }

    # Merge personas: if user passed explicit_personas in UI/API, prioritize those; otherwise merge text + LLM
    if explicit_personas:
        final_personas = explicit_personas
    else:
        final_personas = clean_persona_list(text_personas + list(decision.personas or []))
        if not final_personas:
            final_personas = [DEFAULT_PERSONA]

    # Channel: email if either regex or LLM detected email
    final_channel = "email" if (det_channel == "email" or decision.channel == "email") else "text"

    # Style modifiers: merge parameter modifiers + text modifiers + LLM modifiers
    final_mods = clean_modifier_list(explicit_mods + text_mods + list(decision.style_modifiers or []))

    return {
        "mode": "rewrite",
        "personas": final_personas,
        "channel": final_channel,
        "style_modifiers": final_mods,
        "memory_text": memory,
    }


def language_router(state: GraphState):
    """Dedicated LangGraph node that detects user language/script and selects the optimal LLM model."""
    script, lang_key, model_id = detect_script_and_lang(state.get("user_message", ""))
    return {
        "detected_script": script,
        "detected_language": lang_key,
        "lang_model": model_id,
    }


def route_after_language(state: GraphState):
    return "chat_node" if state.get("mode") == "chat" else "understand"


def understand(state: GraphState):
    result = ask_structured(
        "understand",
        Analysis,
        PROMPTS["understand"],
        f"USER INPUT:\n{state['user_message']}",
        lang_model=state.get("lang_model"),
    )
    a = result.model_dump()
    a["clean_text"] = normalize_text(a["clean_text"])
    a["goal"] = normalize_text(a["goal"])
    a["key_facts"] = [normalize_text(f) for f in a["key_facts"]]
    if state.get("detected_language") == "hinglish":
        a["language"] = "Hinglish"
    elif state.get("detected_language") == "chinese":
        a["language"] = "Chinese"
    run_id = save_run(state["user_id"], state["user_message"], "rewrite", state["personas"])
    return {"analysis": a, "run_id": run_id}


def fan_out(state: GraphState):
    """Creates parallel Send('writer', ...) tasks — 1 per detected persona."""
    targets = state.get("to_write") or state["personas"]
    fixes = state.get("fixes", {}) or {}
    rewrites = state.get("rewrites", {}) or {}
    latest = latest_drafts(state)
    sends = []
    for p in targets:
        n = rewrites.get(p, 0)
        sends.append(Send("writer", {
            "persona": p,
            "version": next_version(state, p),
            "analysis": state["analysis"],
            "user_message": state["user_message"],
            "out_lang": state.get("out_lang", "same as input"),
            "channel": state.get("channel", "text"),
            "style_modifiers": state.get("style_modifiers", []),
            "detected_script": state.get("detected_script", "Latin"),
            "detected_language": state.get("detected_language", "english"),
            "lang_model": state.get("lang_model", MODEL_QUALITY),
            "memory_text": state.get("memory_text", ""),
            "fix": fixes.get(p, ""),
            "previous": latest[p]["message"] if p in latest else "",
            "source": f"user_rewrite_{n}" if n > 0 else "auto",
        }))
    return sends


def writer(payload: dict):
    p = payload["persona"]
    a = payload["analysis"]
    cfg = PERSONAS[p]
    channel = payload.get("channel", "text")
    mods = payload.get("style_modifiers") or []
    is_short = "shorter" in mods or p == "concise"

    # Choose channel formatting rule (Email vs Text, Normal vs Shorter)
    if channel == "email":
        chan_key = "email_shorter" if is_short else "email_normal"
    else:
        chan_key = "text_shorter" if is_short else "text_normal"
    channel_instruction = CHANNEL_RULES[chan_key].format(label=cfg["label"])

    # Build modifier instructions if any (shorter, formal, friendly, etc.)
    if mods:
        mod_lines = "\n".join(f"- {QUICK_FIXES[m]}" for m in mods if m in QUICK_FIXES)
        modifier_instruction = f"ACTIVE STYLE MODIFIERS:\n{mod_lines}"
    else:
        modifier_instruction = "ACTIVE STYLE MODIFIERS: Standard length and depth for this channel."

    out_lang = resolve_out_lang(
        payload.get("out_lang", "same as input"),
        a,
        payload["user_message"],
        payload.get("detected_script", "Latin"),
        payload.get("detected_language", "english"),
    )
    system = PROMPTS["writer"].format(
        label=cfg["label"],
        rules=cfg["rules"],
        channel_instruction=channel_instruction,
        modifier_instruction=modifier_instruction,
        out_lang=out_lang,
    )
    human = (
        f"TARGET RECIPIENT / PERSONA: {cfg['label']}\n"
        f"CHANNEL: {channel.upper()}\n"
        f"ORIGINAL USER INPUT: {payload['user_message']}\n"
        f"CLEANED VERSION / BRIEF: {a['clean_text']}\n"
        f"KEY_FACTS: {a['key_facts']}\n"
        f"GOAL: {a['goal']}\n"
        f"SAVED USER PREFERENCES:\n{payload['memory_text']}"
    )
    if a["input_type"] == "prompt":
        human += (
            f"\n\nNOTE: The user input is an INSTRUCTION. Write the actual ready-to-send {channel} "
            f"specifically addressed to the {cfg['label']}."
        )
    if payload.get("fix"):
        human += PROMPTS["writer_fix"].format(previous=payload.get("previous", ""), feedback=payload["fix"])

    text = ask_text("writer", system, human, lang_model=payload.get("lang_model"))
    text = normalize_text(text).strip().strip('"').strip()
    with _calls_lock:
        CALLS["writer"] += 1
    return {
        "drafts": [{
            "persona": p,
            "version": payload["version"],
            "message": text,
            "source": payload["source"],
            "channel": channel,
            "style_modifiers": mods,
            "model_used": payload.get("lang_model", MODEL_QUALITY),
        }]
    }


# ===========================================================================
# 6. CITATION & FACT-CHECK NODE
# ===========================================================================
def norm_for_match(s):
    s = normalize_text(s or "").lower()
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def digits_in(text):
    return set(re.findall(r"\d+", re.sub(r"(?<=\d),(?=\d)", "", text or "")))


def quote_found(quote, sources):
    if not quote or quote.strip().upper() == "NOT_FOUND":
        return False
    q = norm_for_match(quote)
    return bool(q) and any(q in norm_for_match(src) for src in sources)


def verify_citation(original, analysis, draft_text, cit):
    sources = [original, analysis["clean_text"]]
    draft_digits = digits_in(draft_text)
    facts = []
    for f in cit["facts"]:
        in_draft = bool(f["in_draft"])
        fd = digits_in(f["fact"])
        if fd and not fd <= draft_digits:
            in_draft = False
        facts.append({**f, "quote_ok": quote_found(f["source_quote"], sources), "in_draft": in_draft})
    known = digits_in(original) | digits_in(analysis["clean_text"])
    total = len(facts)
    in_count = sum(1 for f in facts if f["in_draft"])
    return {
        "facts": facts,
        "missing_facts": [f["fact"] for f in facts if not f["in_draft"]],
        "unverified_facts": [f["fact"] for f in facts if not f["quote_ok"]],
        "invented_facts": list(cit["invented_facts"]),
        "digits_missing": sorted(digits_in(original) - draft_digits),
        "digits_invented": sorted(draft_digits - known),
        "coverage": round(in_count / total, 2) if total else 1.0,
    }


def change_report(original, new):
    a, b = original.split(), new.split()
    sm = difflib.SequenceMatcher(None, a, b)
    return round((1 - sm.ratio()) * 100), len(a), len(b)


def check_one(original, analysis, draft):
    human = (
        f"ORIGINAL (user's exact words):\n{original}\n\n"
        f"CLEANED VERSION:\n{analysis['clean_text']}\n\n"
        f"KEY_FACTS: {analysis['key_facts']}\n\n"
        f"DRAFT:\n{draft['message']}"
    )
    res = ask_structured("citation", CitationResult, PROMPTS["citation"], human)
    with _calls_lock:
        CALLS["citation_llm"] += 1
    out = verify_citation(original, analysis, draft["message"], res.model_dump())
    if analysis["input_type"] == "draft":
        pct, w1, w2 = change_report(original, draft["message"])
        out.update({"changed_pct": pct, "words_before": w1, "words_after": w2})
    else:
        out.update({"changed_pct": None, "words_before": None, "words_after": None})
    return out


def citation(state: GraphState):
    with _calls_lock:
        CALLS["citation_node"] += 1
    done = {(c["persona"], c["version"]) for c in state.get("checks", [])}
    pending = [d for d in state["drafts"] if (d["persona"], d["version"]) not in done]
    if not pending:
        return {}
    original, a = state["user_message"], state["analysis"]
    with ThreadPoolExecutor(max_workers=min(6, len(pending))) as pool:
        results = list(pool.map(lambda d: check_one(original, a, d), pending))
    return {"checks": [{"persona": d["persona"], "version": d["version"], **r} for d, r in zip(pending, results)]}


# ===========================================================================
# 7. JUDGE, SELECTIVE AUTO-RETRY, OUTPUT & FEEDBACK NODES
# ===========================================================================
def reliable_missing(chk):
    return [f["fact"] for f in chk.get("facts", []) if f.get("quote_ok") and not f["in_draft"]]


def compute_overall(s, chk):
    base = (
        0.40 * s["meaning_preservation"]
        + 0.25 * s["tone_accuracy"]
        + 0.20 * s["clarity"]
        + 0.15 * s["conciseness"]
    )
    penalty = (
        1.0 * len(chk.get("invented_facts") or [])
        + 1.5 * len(chk.get("digits_missing") or [])
        + 1.0 * len(chk.get("digits_invented") or [])
        + 1.0 * len(reliable_missing(chk))
    )
    return round(max(base - min(penalty, 4.0), 0), 2)


def citation_summary(chk):
    if not chk:
        return {}
    return {
        "coverage": chk.get("coverage"),
        "missing_facts": reliable_missing(chk),
        "invented_facts": chk.get("invented_facts", []),
        "digits_missing": chk.get("digits_missing", []),
        "digits_invented": chk.get("digits_invented", []),
        "changed_pct": chk.get("changed_pct"),
    }


def judge_one(original, analysis, persona, draft, chk, channel="text", modifiers=None):
    chk = chk or {"facts": [], "invented_facts": [], "digits_missing": [], "digits_invented": []}
    miss = reliable_missing(chk)
    cfg = PERSONAS[persona]
    system = PROMPTS["judge"].format(
        label=cfg["label"],
        channel=channel,
        modifiers=modifiers or ["normal"],
    )
    human = (
        f"ORIGINAL INPUT: {original}\n"
        f"CLEANED VERSION / BRIEF: {analysis['clean_text']}\n"
        f"REQUESTED AUDIENCE: {cfg['label']} - {cfg['rules']}\n"
        f"CHANNEL: {channel} | STYLE MODIFIERS: {modifiers or ['normal']}\n\n"
        f"FACT-CHECK RESULT:\n- missing facts: {miss}\n- invented facts: {chk.get('invented_facts')}\n"
        f"- numbers from the original missing in draft: {chk.get('digits_missing')}\n"
        f"- new numbers in draft: {chk.get('digits_invented')}\n\n"
        f"DRAFT TO SCORE:\n{draft['message']}"
    )
    res = ask_structured("judge", DraftScore, system, human)
    with _calls_lock:
        CALLS["judge_llm"] += 1
    s = res.model_dump()
    for k in ("tone_accuracy", "clarity", "meaning_preservation", "conciseness"):
        s[k] = max(1, min(10, int(s[k])))
    s["overall"] = compute_overall(s, chk)
    s["meaning_safe"] = not chk.get("digits_missing") and not chk.get("digits_invented") and not miss
    s["passed"] = bool(s["overall"] >= PASS_SCORE and s["meaning_safe"])
    return s


def judge(state: GraphState):
    done = {(s["persona"], s["version"]) for s in state.get("scores", [])}
    pending = [d for d in state["drafts"] if (d["persona"], d["version"]) not in done]
    if not pending:
        return {}
    original, a = state["user_message"], state["analysis"]
    channel = state.get("channel", "text")
    mods = state.get("style_modifiers", [])
    with ThreadPoolExecutor(max_workers=min(6, len(pending))) as pool:
        results = list(pool.map(
            lambda d: judge_one(
                original, a, d["persona"], d,
                find_item(state.get("checks", []), d["persona"], d["version"]),
                channel=channel, modifiers=mods,
            ),
            pending,
        ))
    return {"scores": [{"persona": d["persona"], "version": d["version"], **r} for d, r in zip(pending, results)]}


def failing_personas(state):
    active = state.get("to_write") or state.get("personas", [])
    latest = latest_drafts(state)
    out = []
    for p in active:
        d = latest.get(p)
        if not d:
            continue
        s = find_item(state.get("scores", []), p, d["version"])
        if s and not s["passed"] and state.get("retries", {}).get(p, 0) < MAX_RETRY:
            out.append(p)
    return out


def route_after_judge(state: GraphState):
    return "retry" if failing_personas(state) else "done"


def prepare_retry(state: GraphState):
    latest = latest_drafts(state)
    targets, fixes = failing_personas(state), {}
    for p in targets:
        d = latest[p]
        s = find_item(state["scores"], p, d["version"])
        c = find_item(state["checks"], p, d["version"])
        parts = []
        if s and (s.get("fix_suggestion") or "").strip().lower() not in ("", "none"):
            parts.append(s["fix_suggestion"])
        if c:
            if reliable_missing(c):
                parts.append(f"Include these missing facts: {reliable_missing(c)}")
            if c.get("invented_facts"):
                parts.append(f"Remove these things the sender never said: {c['invented_facts']}")
            if c.get("digits_missing"):
                parts.append(f"Keep these numbers/digits intact: {c['digits_missing']}")
            if c.get("digits_invented"):
                parts.append(f"Remove these invented numbers: {c['digits_invented']}")
        parts.append("Ensure smooth, natural phrasing in a single consistent language and script.")
        fixes[p] = "\n".join(f"- {x}" for x in parts)
    return {
        "to_write": targets,
        "fixes": fixes,
        "retries": {p: state.get("retries", {}).get(p, 0) + 1 for p in targets},
    }


def output(state: GraphState):
    user_id, run_id = state["user_id"], state["run_id"]
    by_persona: dict = {}
    for d in state["drafts"]:
        by_persona.setdefault(d["persona"], []).append(d)

    results = {}
    for p in state["personas"]:
        versions = sorted(by_persona.get(p, []), key=lambda d: d["version"])
        already_saved = len(get_versions(user_id, run_id, p))
        rows = []
        for d in versions:
            s = find_item(state.get("scores", []), p, d["version"]) or {}
            c = find_item(state.get("checks", []), p, d["version"]) or {}
            if d["version"] > already_saved:
                add_version(user_id, run_id, p, d["message"], scores=s, citation=citation_summary(c), source=d["source"])
            rows.append((d, s, c))

        n = (state.get("rewrites") or {}).get(p, 0)
        pool = [r for r in rows if r[0].get("source") == f"user_rewrite_{n}"] if n > 0 else rows
        d, s, c = max(pool or rows, key=lambda t: (bool(t[1].get("passed")), t[1].get("overall", 0), t[0]["version"]))
        results[p] = {
            "persona_label": PERSONAS[p]["label"],
            "channel": d.get("channel", state.get("channel", "text")),
            "style_modifiers": d.get("style_modifiers", state.get("style_modifiers", [])),
            "message": d["message"],
            "version": d["version"],
            "attempts": len(versions),
            "rewrites": n,
            "model_used": d.get("model_used", state.get("lang_model", MODEL_QUALITY)),
            "scores": s,
            "citation": citation_summary(c),
            "all_versions": [
                {
                    "version": x[0]["version"],
                    "source": x[0].get("source", "auto"),
                    "overall": x[1].get("overall"),
                    "passed": x[1].get("passed"),
                }
                for x in rows
            ],
        }
    return {
        "final": {
            "run_id": run_id,
            "original": state["user_message"],
            "channel": state.get("channel", "text"),
            "style_modifiers": state.get("style_modifiers", []),
            "detected_language": state.get("detected_language"),
            "detected_script": state.get("detected_script"),
            "lang_model": state.get("lang_model"),
            "analysis": state["analysis"],
            "results": results,
        }
    }


def _feedback_payload(state: GraphState) -> dict:
    return {
        "run_id": state.get("run_id"),
        "results": (state.get("final") or {}).get("results", {}),
        "rewrites": state.get("rewrites", {}),
        "max_rewrite": MAX_REWRITE,
        "quick_fixes": list(QUICK_FIXES),
        "hint": "liked=true to save, liked=false to rewrite one persona, done=true to finish.",
    }


def feedback_node(state: GraphState):
    decision = interrupt(_feedback_payload(state))
    if not isinstance(decision, dict):
        decision = {"done": True, "comment": str(decision)}
    return {"feedback_decision": decision, "to_write": []}


def route_after_feedback(state: GraphState):
    d = state.get("feedback_decision") or {}
    if d.get("done") and not d.get("persona"):
        return "end"
    if d.get("liked"):
        return "save_json"
    if d.get("persona") and d.get("liked") is False:
        return "user_rewrite"
    return "end"


def save_json(state: GraphState):
    d = state.get("feedback_decision") or {}
    persona = d.get("persona")
    user_id, run_id = state["user_id"], state["run_id"]
    results = (state.get("final") or {}).get("results", {})
    if persona and persona in results:
        ver = results[persona]["version"]
        add_feedback(user_id, run_id, persona, True, d.get("comment") or f"liked v{ver}")
        if d.get("remember", True):
            with _db_lock:
                run = _find_run(_user(_read_db(), user_id), run_id)
            asked = [
                x["comment"] for x in run["feedback"]
                if x["persona"] == persona and not x["liked"] and x["comment"]
            ]
            if asked:
                add_pref(user_id, f"For {PERSONAS[persona]['label']} messages: {asked[-1]}")
    return {}


def route_after_save(state: GraphState):
    d = state.get("feedback_decision") or {}
    return "end" if d.get("done") else "feedback"


def prepare_user_rewrite(state: GraphState):
    d = state.get("feedback_decision") or {}
    persona = d.get("persona")
    n = (state.get("rewrites") or {}).get(persona, 0)
    if not persona or n >= MAX_REWRITE:
        return {"to_write": []}

    quick_list = d.get("quick") or []
    if isinstance(quick_list, str):
        quick_list = [quick_list]
    quick_list = clean_modifier_list(quick_list)
    parts = [QUICK_FIXES[q] for q in quick_list if q in QUICK_FIXES]
    if d.get("comment"):
        parts.append(d["comment"])
    request = " ".join(parts) if parts else "Write a clearly different and better version."
    add_feedback(state["user_id"], state["run_id"], persona, False, request)
    fix = (
        f"- The user rejected the previous draft. Their instruction: {request}\n"
        "- Keep every key fact exactly (dates, numbers, names).\n"
        "- Do not add anything the sender never said.\n"
        "- Write a visibly different version that follows the instruction."
    )
    updated_mods = clean_modifier_list(list(state.get("style_modifiers") or []) + quick_list)
    return {
        "to_write": [persona],
        "fixes": {persona: fix},
        "style_modifiers": updated_mods,
        "rewrites": {persona: n + 1},
        "retries": {persona: 0},
    }


def chat_node(state: GraphState):
    user_id = state.get("user_id", DEFAULT_USER)
    user_lang = f"{state.get('detected_language', 'english')} ({state.get('detected_script', 'Latin')})"
    system = (
        PROMPTS["chat"].format(user_lang=user_lang)
        + f"\n\nUSER PREFERENCES:\n{prefs_as_text(user_id)}"
        + f"\n\nRECENT REWRITES:\n{recent_runs_text(user_id)}"
    )
    messages = [("system", system)]
    messages += [(m["role"], m["content"]) for m in get_chat(user_id, 10)]
    messages.append(("user", state["user_message"]))

    reply = ""
    llm = get_llm("chat", lang_model=state.get("lang_model"))
    for i in range(3):
        try:
            raw = (llm.invoke(messages).content or "").strip()
            reply = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
            if reply:
                break
        except Exception:
            time.sleep(1.5 * (i + 1))
    if not reply:
        reply = "Sorry, abhi jawab nahi de paya. Dobara try karo."
    add_chat(user_id, "user", state["user_message"])
    add_chat(user_id, "assistant", reply)
    return {"reply": reply}


# ===========================================================================
# 8. GRAPH BUILDERS (InMemorySaver + Notebook Helpers)
# ===========================================================================
def build_graph(checkpointer=None, with_interrupt: bool = True):
    g = StateGraph(GraphState)
    g.add_node("router", router)
    g.add_node("language_router", language_router)
    g.add_node("understand", understand)
    g.add_node("chat_node", chat_node)
    g.add_node("writer", writer)
    g.add_node("citation", citation)
    g.add_node("judge", judge)
    g.add_node("prepare_retry", prepare_retry)
    g.add_node("output", output)

    g.add_edge(START, "router")
    g.add_edge("router", "language_router")
    g.add_conditional_edges(
        "language_router",
        route_after_language,
        {"chat_node": "chat_node", "understand": "understand"},
    )
    g.add_conditional_edges("understand", fan_out, ["writer"])
    g.add_edge("writer", "citation")
    g.add_edge("citation", "judge")
    g.add_conditional_edges("judge", route_after_judge, {"retry": "prepare_retry", "done": "output"})
    g.add_conditional_edges("prepare_retry", fan_out, ["writer"])
    g.add_edge("chat_node", END)

    if with_interrupt:
        g.add_node("feedback", feedback_node)
        g.add_node("save_json", save_json)
        g.add_node("prepare_user_rewrite", prepare_user_rewrite)
        g.add_edge("output", "feedback")
        g.add_conditional_edges(
            "feedback",
            route_after_feedback,
            {"save_json": "save_json", "user_rewrite": "prepare_user_rewrite", "end": END},
        )
        g.add_conditional_edges("save_json", route_after_save, {"feedback": "feedback", "end": END})
        g.add_conditional_edges("prepare_user_rewrite", fan_out, ["writer"])
    else:
        g.add_edge("output", END)

    return g.compile(checkpointer=checkpointer)


def build_rewrite_app():
    g = StateGraph(GraphState)
    g.add_node("writer", writer)
    g.add_node("citation", citation)
    g.add_node("judge", judge)
    g.add_node("prepare_retry", prepare_retry)
    g.add_node("output", output)

    g.add_conditional_edges(START, fan_out, ["writer"])
    g.add_edge("writer", "citation")
    g.add_edge("citation", "judge")
    g.add_conditional_edges("judge", route_after_judge, {"retry": "prepare_retry", "done": "output"})
    g.add_conditional_edges("prepare_retry", fan_out, ["writer"])
    g.add_edge("output", END)
    return g.compile()


checkpointer = InMemorySaver()
graph = build_graph(checkpointer=checkpointer, with_interrupt=True)

notebook_checkpointer = InMemorySaver()
app_graph = build_graph(checkpointer=notebook_checkpointer, with_interrupt=False)
rewrite_app = build_rewrite_app()


# ===========================================================================
# 9. NOTEBOOK DISPLAY & ZERO-PARAM INTERACTIVE HELPERS
# ===========================================================================
def show(out: dict) -> None:
    if out.get("mode") == "chat":
        print(f"🌐 Language: {out.get('detected_language')} | Model: {out.get('lang_model')}")
        print("🤖", out["reply"])
        return
    f = out["final"]
    a = f["analysis"]
    print(
        f"🧠 {a['input_type']} | Channel: {f.get('channel', 'text').upper()} | "
        f"Modifiers: {f.get('style_modifiers') or ['normal']} | "
        f"Lang: {a['language']} ({f.get('detected_script')}) | Model: {f.get('lang_model')}"
    )
    print(f"🎯 Auto-Detected Personas: {out.get('personas')} | Goal: {a['goal']}")
    for p, r in f["results"].items():
        s, c = r["scores"], r["citation"]
        print("=" * 70)
        print(
            f"📌 [{PERSONAS[p]['label']}] (key: '{p}') | {r.get('channel', 'text').upper()} | "
            f"v{r['version']} chuna, {r['attempts']} attempt | "
            f"{'✅ pass' if s['passed'] else '⚠️ pass nahi hua'}"
        )
        print("-" * 70)
        print(r["message"])
        print("-" * 70)
        print(
            f"📊 overall {s['overall']} | tone {s['tone_accuracy']} | clarity {s['clarity']} | "
            f"meaning {s['meaning_preservation']} | concise {s['conciseness']}"
        )
        print(
            f"🔎 missing {c['missing_facts']} | invented {c['invented_facts']} | "
            f"digits missing {c['digits_missing']} | digits invented {c['digits_invented']}"
        )
        if c["changed_pct"] is not None:
            print(f"✏️ change: {c['changed_pct']}%")
        print("🔁 sab versions:", r["all_versions"])


def show_one(out: dict, persona: str) -> None:
    r = out["final"]["results"][persona]
    s, c = r["scores"], r["citation"]
    rewrites_count = out.get("rewrites", {}).get(persona, 0)
    print("=" * 70)
    print(
        f"📌 [{PERSONAS[persona]['label']}] | v{r['version']} | rewrites: {rewrites_count}/{MAX_REWRITE} | "
        f"{'✅ pass' if s['passed'] else '⚠️ pass nahi hua'}"
    )
    print("-" * 70)
    print(r["message"])
    print("-" * 70)
    print(
        f"📊 overall {s['overall']} | tone {s['tone_accuracy']} | clarity {s['clarity']} | "
        f"meaning {s['meaning_preservation']} | concise {s['conciseness']}"
    )
    print(
        f"🔎 missing {c['missing_facts']} | invented {c['invented_facts']} | "
        f"digits missing {c['digits_missing']} | digits invented {c['digits_invented']}"
    )
    if c["changed_pct"] is not None:
        print(f"✏️ change: {c['changed_pct']}%")


def show_versions(out: dict, persona: str) -> None:
    for v in get_versions(out["user_id"], out["run_id"], persona):
        sc = v["scores"]["overall"] if v.get("scores") else "-"
        print(f"--- v{v['version']} | {v['source']} | score {sc}\n{v['message']}\n")


def run(
    message: str,
    personas=None,
    quick=None,
    channel: Optional[str] = None,
    user_id: str = DEFAULT_USER,
    out_lang: str = "same as input",
    thread_id: Optional[str] = None,
) -> dict:
    """
    Zero-parameter friendly runner!
    - Just call: run("mujhe boss, client aur friend ko mail karni hai ki demo 3 din late hoga")
    - Or pass quick="shorter" (or write "shorter" in the message itself).
    """
    t0 = time.time()
    tid = thread_id or str(uuid.uuid4())
    inp = make_input(
        user_message=message,
        selected_personas=personas or [],
        user_id=user_id,
        out_lang=out_lang,
        quick=quick,
        channel=channel,
    )
    out = app_graph.invoke(inp, {"configurable": {"thread_id": tid}})
    out["thread_id"] = tid
    print(f"⏱️ {time.time() - t0:.1f}s")
    show(out)
    return out


def feedback(out: dict, persona: str, liked: bool, comment: str = "", quick=None, remember: bool = True) -> dict:
    if out.get("mode") != "rewrite":
        print("Ye chat tha, isme feedback nahi hota.")
        return out
    persona = PERSONA_ALIASES.get(persona.lower().strip(), persona.lower().strip())
    results = out["final"]["results"]
    if persona not in results:
        print(f"'{persona}' is run me nahi tha. Available: {list(results)}")
        return out

    user_id, run_id = out["user_id"], out["run_id"]
    if liked:
        ver = results[persona]["version"]
        add_feedback(user_id, run_id, persona, True, comment or f"liked v{ver}")
        print(f"👍 {PERSONAS[persona]['label']} v{ver} pasand aaya, save ho gaya.")
        if remember:
            with _db_lock:
                run_rec = _find_run(_user(_read_db(), user_id), run_id)
            asked = [
                x["comment"] for x in run_rec["feedback"]
                if x["persona"] == persona and not x["liked"] and x["comment"]
            ]
            if asked:
                add_pref(user_id, f"For {PERSONAS[persona]['label']} messages: {asked[-1]}")
                print("🧠 Style preference yaad rakh li.")
        return out

    n = out.get("rewrites", {}).get(persona, 0)
    if n >= MAX_REWRITE:
        print(f"⛔ {persona} ke liye max {MAX_REWRITE} rewrite ho chuke. show_versions() se purane dekho.")
        return out

    quick_list = [quick] if isinstance(quick, str) else (quick or [])
    quick_list = clean_modifier_list(quick_list)
    parts = [QUICK_FIXES[q] for q in quick_list if q in QUICK_FIXES] + ([comment] if comment else [])
    request = " ".join(parts) if parts else "Write a clearly different and better version."

    add_feedback(user_id, run_id, persona, False, request)
    fix = (
        f"- The user rejected the previous draft. Their instruction: {request}\n"
        "- Keep every key fact exactly (dates, numbers, names).\n"
        "- Do not add anything the sender never said.\n"
        "- Write a visibly different version that follows the instruction."
    )

    state = dict(out)
    state["to_write"] = [persona]
    state["fixes"] = {persona: fix}
    state["style_modifiers"] = clean_modifier_list(list(out.get("style_modifiers") or []) + quick_list)
    state["rewrites"] = {**out.get("rewrites", {}), persona: n + 1}
    state["retries"] = {**out.get("retries", {}), persona: 0}

    print(f"🔄 {PERSONAS[persona]['label']} ka rewrite ({n + 1}/{MAX_REWRITE}): {request}")
    t0 = time.time()
    new_out = rewrite_app.invoke(state)
    print(f"⏱️ {time.time() - t0:.1f}s")
    show_one(new_out, persona)
    return new_out


# ===========================================================================
# 10. FASTAPI ENDPOINTS
# ===========================================================================
def _config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def _interrupt_values(thread_id: str) -> list:
    snap = graph.get_state(_config(thread_id))
    values = []
    for task in snap.tasks:
        for item in getattr(task, "interrupts", ()) or ():
            values.append(getattr(item, "value", item))
    return values


def _pack(thread_id: str, result: dict) -> dict:
    interrupts = _interrupt_values(thread_id)
    snap = graph.get_state(_config(thread_id))
    values = snap.values or result or {}
    status = "needs_feedback" if interrupts else "done"
    return {
        "status": status,
        "thread_id": thread_id,
        "mode": values.get("mode"),
        "channel": values.get("channel", "text"),
        "style_modifiers": values.get("style_modifiers", []),
        "detected_language": values.get("detected_language"),
        "detected_script": values.get("detected_script"),
        "lang_model": values.get("lang_model"),
        "personas": values.get("personas", []),
        "run_id": values.get("run_id"),
        "reply": values.get("reply"),
        "final": values.get("final"),
        "rewrites": values.get("rewrites", {}),
        "retries": values.get("retries", {}),
        "interrupt": interrupts[0] if interrupts else None,
        "next": list(snap.next or []),
    }


class RunRequest(BaseModel):
    message: str
    personas: List[str] = []
    quick: Optional[List[str] | str] = None
    channel: Optional[str] = None
    user_id: str = DEFAULT_USER
    out_lang: str = "same as input"
    thread_id: Optional[str] = None


class FeedbackRequest(BaseModel):
    thread_id: str
    persona: Optional[str] = None
    liked: Optional[bool] = None
    comment: str = ""
    quick: Optional[List[str] | str] = None
    remember: bool = True
    done: bool = False


class PrefRequest(BaseModel):
    user_id: str = DEFAULT_USER
    text: str


app = FastAPI(title="Persona Transformer API", version="2.1")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "ok": True,
        "has_key": bool(GROQ_API_KEY),
        "models": {
            "quality": MODEL_QUALITY,
            "fast": MODEL_FAST,
            "language_models": LANGUAGE_MODELS,
        },
    }


@app.get("/personas")
def list_personas():
    return {
        "personas": {k: v["label"] for k, v in PERSONAS.items()},
        "aliases": PERSONA_ALIASES,
        "quick_fixes": list(QUICK_FIXES),
        "pass_score": PASS_SCORE,
        "max_retry": MAX_RETRY,
        "max_rewrite": MAX_REWRITE,
    }


@app.get("/graph")
def graph_mermaid():
    return {"mermaid": graph.get_graph().draw_mermaid()}


@app.post("/run")
def run_message(req: RunRequest):
    if not (GROQ_API_KEY or os.getenv("GROQ_API_KEY")):
        raise HTTPException(500, "GROQ_API_KEY missing")
    cleaned = clean_persona_list(req.personas)
    if req.personas and not cleaned:
        raise HTTPException(400, f"Unknown personas: {req.personas}. Use GET /personas")
    thread_id = req.thread_id or str(uuid.uuid4())
    payload = make_input(
        user_message=req.message,
        selected_personas=cleaned,
        user_id=req.user_id,
        out_lang=req.out_lang,
        quick=req.quick,
        channel=req.channel,
    )
    try:
        result = graph.invoke(payload, _config(thread_id))
    except Exception as e:
        raise HTTPException(500, str(e)) from e
    return _pack(thread_id, result)


@app.post("/feedback")
def submit_feedback(req: FeedbackRequest):
    snap = graph.get_state(_config(req.thread_id))
    if not snap.next:
        raise HTTPException(400, "Is thread pe koi pending feedback nahi hai (graph already END).")
    persona = PERSONA_ALIASES.get(req.persona.lower().strip(), req.persona.lower().strip()) if req.persona else None
    if persona and persona not in PERSONAS:
        raise HTTPException(400, f"Unknown persona '{req.persona}'")
    if req.liked is False and persona:
        n = (snap.values.get("rewrites") or {}).get(persona, 0)
        if n >= MAX_REWRITE:
            raise HTTPException(400, f"Max {MAX_REWRITE} user rewrites for {persona}")

    resume = {
        "persona": persona,
        "liked": req.liked,
        "comment": req.comment,
        "quick": req.quick,
        "remember": req.remember,
        "done": req.done,
    }
    try:
        result = graph.invoke(Command(resume=resume), _config(req.thread_id))
    except Exception as e:
        raise HTTPException(500, str(e)) from e
    return _pack(req.thread_id, result)


@app.get("/state/{thread_id}")
def get_thread_state(thread_id: str):
    return _pack(thread_id, {})


@app.get("/memory/{user_id}")
def memory(user_id: str):
    return get_user_memory(user_id)


@app.get("/memory/{user_id}/runs/{run_id}/{persona}")
def versions(user_id: str, run_id: str, persona: str):
    try:
        return {"versions": get_versions(user_id, run_id, persona)}
    except KeyError as e:
        raise HTTPException(404, str(e)) from e


@app.post("/prefs")
def add_preference(req: PrefRequest):
    add_pref(req.user_id, req.text)
    return {"prefs": list_prefs(req.user_id)}


@app.delete("/prefs/{user_id}/{index}")
def remove_preference(user_id: str, index: int):
    removed = delete_pref(user_id, index)
    return {"removed": removed, "prefs": list_prefs(user_id)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=True)