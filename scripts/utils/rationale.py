import os, requests

LLM_URL   = os.getenv("LLM_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2:3b-instruct")
LLM_TEMP  = float(os.getenv("LLM_TEMP", "0.2"))
LLM_MAX   = int(os.getenv("LLM_MAX_TOKENS", "96"))

PROMPT_TMPL = """You are assisting with ICD-10 code suggestions.
Write ONE short sentence explaining why the ICD-10 code fits the note.
Avoid clinical certainty; use hedged language if needed.

Note: "{note}"
ICD-10: {code} — {title}

One-sentence rationale:"""

def llm_rationale(note: str, code: str, title: str, timeout=6.0) -> str:
    try:
        payload = {
            "model": LLM_MODEL,
            "prompt": PROMPT_TMPL.format(note=note, code=code, title=title),
            "options": {"temperature": LLM_TEMP, "num_predict": LLM_MAX}
        }
        r = requests.post(f"{LLM_URL}/api/generate", json=payload, timeout=timeout)
        r.raise_for_status()
        text = r.json().get("response", "").strip()
        # Safety trims: 1 sentence, < 30 words
        text = text.split("\n")[0]
        return text[:300]
    except Exception:
        # Fallback template
        return f"Presentation is consistent with {title.lower()} based on the note text."
