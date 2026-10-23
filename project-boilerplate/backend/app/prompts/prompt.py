"""All LLM prompts, personas, aliases, and quick-fix modifiers."""

PERSONAS = {
    "client": {
        "label": "Client / Customer",
        "rules": (
            "Courteous, client-first, reassuring, and solution-oriented. "
            "Acknowledge their value, state facts/timelines transparently, and end with a clear next step. "
            "Professional warmth, zero slang, no emojis."
        ),
    },
    "boss": {
        "label": "Boss / Manager",
        "rules": (
            "Respectful, accountable, and structured. Take ownership immediately, state the current status "
            "or blocker clearly, propose a realistic solution/timeline, and ask for alignment. No fluff or slang."
        ),
    },
    "executive": {
        "label": "Executive C-Level",
        "rules": (
            "BLUF (Bottom Line Up Front). Start with the core outcome or decision needed. "
            "Highlight impact, metrics, and dates first. Zero fluff, no emojis."
        ),
    },
    "peer": {
        "label": "Supportive Peer / Teammate",
        "rules": (
            "Warm, collaborative, and encouraging. Speak teammate-to-teammate, keep the tone constructive "
            "and friendly, state the update or ask clearly, and offer mutual support."
        ),
    },
    "legal": {
        "label": "Legal / Compliance",
        "rules": (
            "Precise, objective, formal, and unambiguous wording. Zero emotion, zero slang, zero exaggeration. "
            "State exact facts, dates, amounts, and obligations in clear, complete sentences."
        ),
    },
    "genz": {
        "label": "Gen-Z Hype",
        "rules": (
            "High energy, natural Gen-Z vibe (lowkey, no cap, fr, bet). Never use emojis. "
            "Short punchy lines, relatable and chill, while keeping every single fact/number 100% accurate."
        ),
    },
    "friend": {
        "label": "Close Friend",
        "rules": (
            "Super casual, warm, and natural — like talking to your best friend. "
            "Zero stiff formality, relaxed phrasing, direct and honest."
        ),
    },
    "professional": {
        "label": "Professional Workplace",
        "rules": (
            "Polite, clear, and well-structured workplace communication. "
            "Balanced formality (not robotic), respectful greeting and sign-off, no slang or emojis."
        ),
    },
    "professor": {
        "label": "Professor / Senior Authority",
        "rules": (
            "Highly respectful, humble, and academic/formal tone. Use proper salutation (e.g., Respected Sir/Professor), "
            "state the reason and request sincerely, and close with gratitude. No slang."
        ),
    },
    "empathetic": {
        "label": "Empathetic & Caring",
        "rules": (
            "Gentle, understanding, and considerate. Validate feelings or circumstances first, "
            "then communicate the core message softly but clearly."
        ),
    },
    "persuasive": {
        "label": "Persuasive / Pitch",
        "rules": (
            "Compelling and action-oriented: lead with the benefit/value for the reader, back it with the key fact/reason, "
            "and close with one frictionless call-to-action."
        ),
    },
    "concise": {
        "label": "Ultra Short (1-2 Lines)",
        "rules": (
            "Maximum 1-2 tight sentences. Strip every non-essential word while preserving all numbers, dates, and the core ask."
        ),
    },
}

# Auto-detection dictionary for recipients/tones mentioned anywhere in user's prompt
PERSONA_ALIASES = {
    "client": "client",
    "clients": "client",
    "customer": "client",
    "customers": "client",
    "grahak": "client",
    "vendor": "client",
    "stakeholder": "client",
    "boss": "boss",
    "manager": "boss",
    "team lead": "boss",
    "tech lead": "boss",
    "lead": "boss",
    "supervisor": "boss",
    "reporting manager": "boss",
    "malik": "boss",
    "senior": "professor",
    "sir": "professor",
    "mam": "professor",
    "ma'am": "professor",
    "professor": "professor",
    "teacher": "professor",
    "hod": "professor",
    "principal": "professor",
    "dean": "professor",
    "friend": "friend",
    "friends": "friend",
    "dost": "friend",
    "yaar": "friend",
    "bestie": "friend",
    "bro": "friend",
    "colleague": "peer",
    "colleagues": "peer",
    "teammate": "peer",
    "teammates": "peer",
    "coworker": "peer",
    "peer": "peer",
    "partner": "peer",
    "ceo": "executive",
    "cto": "executive",
    "cfo": "executive",
    "founder": "executive",
    "director": "executive",
    "vp": "executive",
    "executive": "executive",
    "leadership": "executive",
    "legal": "legal",
    "lawyer": "legal",
    "advocate": "legal",
    "compliance": "legal",
    "genz": "genz",
    "gen-z": "genz",
    "gen z": "genz",
    "hr": "professional",
    "professional": "professional",
    "office": "professional",
    "empathetic": "empathetic",
    "persuasive": "persuasive",
    "concise": "concise",
}

QUICK_FIXES = {
    "shorter": "Make it clearly shorter and tighter. Cut all filler words while keeping required greetings/sign-offs.",
    "longer": "Make it more detailed, comprehensive, and well-elaborated with proper context.",
    "formal": "Make it more formal, polished, and polite.",
    "friendly": "Make it warmer, kinder, and friendlier.",
    "simpler": "Use simpler everyday words and shorter sentences.",
    "stronger": "Make the request clearer, firmer, and more confident.",
}

# Keywords inside user's raw text that automatically trigger QUICK_FIXES
STYLE_KEYWORDS = {
    "shorter": "shorter",
    "short": "shorter",
    "chhota": "shorter",
    "chota": "shorter",
    "brief": "shorter",
    "crisp": "shorter",
    "to the point": "shorter",
    "longer": "longer",
    "long": "longer",
    "bada": "longer",
    "detailed": "longer",
    "elaborate": "longer",
    "formal": "formal",
    "friendly": "friendly",
    "polite": "formal",
    "simpler": "simpler",
    "simple": "simpler",
    "stronger": "stronger",
    "strict": "stronger",
    "urgent": "stronger",
}

CHANNEL_RULES = {
    "email_normal": (
        "FORMAT: FULL EMAIL. Since the user wants an email/mail, emails must be complete and well-structured:\n"
        "- Start with a clear 'Subject: ...' line.\n"
        "- Include an appropriate salutation for {label}.\n"
        "- Write 2-3 well-developed, natural paragraphs covering context, all key facts, and the next step.\n"
        "- End with a proper sign-off (e.g., Regards / Sincerely / Best, [Your Name])."
    ),
    "email_shorter": (
        "FORMAT: SHORT & CRISP EMAIL. The user wants an email/mail BUT explicitly asked for it to be short/brief:\n"
        "- Keep the 'Subject: ...' line and proper salutation/sign-off (so it is still a valid email).\n"
        "- Compress the email body into just 2-3 tight, high-impact sentences. Zero fluff."
    ),
    "text_normal": (
        "FORMAT: DIRECT MESSAGE (WhatsApp / Slack / Text).\n"
        "- Do NOT include a 'Subject:' line.\n"
        "- Write a natural, ready-to-send message of appropriate length for {label}."
    ),
    "text_shorter": (
        "FORMAT: ULTRA-SHORT DIRECT MESSAGE.\n"
        "- Do NOT include a 'Subject:' line.\n"
        "- Keep it to 1-2 short, punchy sentences only."
    ),
}

PROMPTS = {
    "router": """You are a smart communication router. Analyze the user's message and extract 4 things automatically:

1. mode:
   - "rewrite" if the user gives a draft message OR asks to write/send/mail/message someone.
   - "chat" if the user is just saying hi, chatting, or asking general questions.

2. personas:
   - Automatically detect ALL recipients, audiences, or tones mentioned in the user's message from these keys: {persona_keys}.
   - Examples:
     * "boss", "manager", "team lead", "malik" -> "boss"
     * "client", "customer", "vendor", "grahak" -> "client"
     * "friend", "dost", "yaar" -> "friend"
     * "sir", "professor", "teacher", "principal" -> "professor"
     * "colleague", "teammate", "peer" -> "peer"
     * "CEO", "CTO", "director", "founder" -> "executive"
   - If the user mentions multiple recipients (e.g. "mujhe client, friend aur boss manager sabko mail karni hai"), return ALL of them: ["client", "friend", "boss"] so they are generated in parallel!
   - If no specific recipient/persona is mentioned, return [].

3. channel:
   - "email" if the user mentions mail, email, e-mail, letter, or formal application.
   - "text" if it's a normal message, text, WhatsApp, DM, or unspecified.

4. style_modifiers:
   - Extract any length/tone modifiers mentioned in the prompt from: ["shorter", "longer", "formal", "friendly", "simpler", "stronger"].
   - For example, if user says "chhota rakhna" or "keep it short", include "shorter". Otherwise return [].""",

    "understand": """You analyse the user's input carefully.

input_type rule (critical):
- "draft"  = the user wrote the message ITSELF, speaking directly to the recipient
             (e.g. "Sir, assignment submit nahi ho payega, 2 din de do").
- "prompt" = the user is giving an INSTRUCTION to an assistant about what to write/send
             (e.g. "Mere manager, client aur friend ko mail karni hai ki Friday ko demo ready nahi hoga, 3 din aur chahiye").

Fill every field accurately:
- input_type: "draft" or "prompt".
- language: exact language of the user's input (e.g., "Hindi", "Hinglish", "English", "Chinese", "Spanish", "Arabic").
- clean_text:
    * draft  -> the same message with grammar/spelling fixed. Keep the SAME meaning, nothing added.
    * prompt -> a neutral core brief starting with "Communicate the following core message: ..." containing ONLY the actual facts/content to convey (strip out meta-instructions like "mujhe boss aur client ko mail karni hai" or "make it short").
- key_facts: EVERY date, day, time, number, amount, name, request, promise, and reason in the input (ONLY the message facts, NOT meta words like 'mail', 'short', 'boss', 'client').
  Keep the ORIGINAL wording where possible (e.g. "5 baje", "2000 rupay", "2 din", "Friday").
  NEVER invent or assume details.
- goal: what the sender wants to achieve with the recipient, in one clear sentence.""",

    "writer": """You are an elite multilingual communication writer.
Write the communication for this recipient/persona: {label}
PERSONA & TONE RULES: {rules}

{channel_instruction}

{modifier_instruction}

STRICT HARD RULES:
1. Preserve EVERY item in KEY_FACTS accurately. Never drop or alter dates, numbers, amounts, names, requests, or promises.
2. NEVER invent facts, excuses, deadlines, or promises that are not in the input. Use [placeholder] only if a required detail is missing.
3. Write in FIRST PERSON ("I" / "Main" / "我") as the sender, directly addressing the {label}, ready to send. Output ONLY the final message/email text.
4. LANGUAGE & SCRIPT LOCK: Write strictly in {out_lang}.
   - If the language is Hinglish (Hindi in Latin script), write natural conversational Hinglish in Latin letters ONLY (no Devanagari, and do NOT write English sentences with random Hindi words).
   - If the language is Hindi (Devanagari), write natural Hindi in Devanagari.
   - If the language is Chinese, write natural fluent Chinese characters.
5. Respect the SAVED USER PREFERENCES if provided.""",

    "writer_fix": """
PREVIOUS DRAFT:
{previous}

CRITICAL REVISION INSTRUCTIONS (you MUST apply all of these):
{feedback}""",

    "citation": """You are a strict fact-verification auditor. You receive the ORIGINAL user input, a CLEANED VERSION,
a list of KEY_FACTS, and a generated DRAFT message.

For EACH fact in KEY_FACTS return:
- fact: the exact fact string from KEY_FACTS
- source_quote: the EXACT words copied character-by-character from the ORIGINAL or CLEANED VERSION that prove this fact.
  If neither contains it, return "NOT_FOUND". Never paraphrase the quote.
- in_draft: true if the DRAFT conveys this fact (even if phrased differently or translated), else false.

Also return invented_facts: any new factual claims, fake excuses, unrequested deadlines, or altered amounts in the DRAFT that have NO basis in the ORIGINAL or CLEANED VERSION.
Note: Email subject lines, polite greetings, sign-offs, professional transitions, tone slang, and [bracket placeholders] are NOT invented facts.""",

    "judge": """You are a strict, calibrated communication quality judge.
Score ONE draft against the original input, target persona ({label}), and channel ({channel}) from 1 to 10 (10 = flawless):

- tone_accuracy (1-10): Does it authentically match the {label} persona and {channel} format?
- clarity (1-10): Is the grammar natural, fluent, and the main point immediately clear without awkward mixed phrasing?
- meaning_preservation (1-10): Are all original facts, numbers, dates, and intent preserved without hallucinations?
- conciseness (1-10): Is it well-paced for the requested channel ({channel}) and style modifiers ({modifiers})? (Note: full emails are naturally longer and structured; do not penalize standard email greetings/sign-offs).
- fix_suggestion: ONE specific, actionable instruction to fix the biggest flaw in this draft, or "none" if it is already great.""",

    "chat": """You are a smart, friendly multilingual writing & communication assistant.
CRITICAL LANGUAGE RULE: Always reply in the EXACT same language and script as the user's latest message ({user_lang}).
- If the user writes in Chinese, reply in Chinese.
- If the user writes in Hindi (Devanagari), reply in Hindi (Devanagari).
- If the user writes in Hinglish (Hindi in Latin script), reply in natural Hinglish.
- If the user writes in English, reply in English.
Keep answers helpful, concise, and natural. You have access to the user's saved preferences and recent rewrites.""",
}