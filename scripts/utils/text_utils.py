# utils/text_utils.py
# Utility functions for text normalization and search text building

ALIASES = {
    # Add your custom token aliases here, e.g.:
    'htn': 'hypertension',
}

def normalize_text(s: str) -> str:
    import re
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r"[^\w\s]", " ", s)  # drop punctuation
    s = re.sub(r"\s+", " ", s).strip()
    tokens = []
    for tok in s.split():
        tok = ALIASES.get(tok, tok)
        tokens.append(tok)
    return " ".join(tokens)

def build_search_text(row):
    parts = [
        normalize_text(row.get("title", "")),
        normalize_text(row.get("description", "")),
        normalize_text(row.get("synonyms", "").replace(";", " "))
    ]
    return " \n ".join([p for p in parts if p])
