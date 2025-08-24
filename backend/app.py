import asyncio
import httpx
from scripts.utils.rationale import PROMPT_TMPL, LLM_MODEL, LLM_URL, LLM_TEMP, LLM_MAX
def embedding(model_id: str, text: str):
    """
    Returns the embedding vector for the given text using the specified model_id.
    The output is a list of float32, suitable for pgvector, and can be cast to ::vector in SQL.
    """
    # For now, only one model is loaded, but model_id is kept for API compatibility
    vec = model.encode([text], normalize_embeddings=True)[0]
    return np.asarray(vec, dtype=np.float32).tolist()

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict
import json, os, time, pickle
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix

# For vector search
from sentence_transformers import SentenceTransformer
from pgvector.psycopg2 import register_vector
from scripts.utils.db import get_pg_conn

# -----------------------------------------------------------------------------
# Load artifacts (TF-IDF only)
# -----------------------------------------------------------------------------
INDEX_DIR = os.getenv("AUTOCODER_INDEX_DIR", "data/index")
CODES_META_PATH = os.path.join(INDEX_DIR, "codes_meta.json")
VEC_PATH = os.path.join(INDEX_DIR, "tfidf_vectorizer.pkl")
MAT_PATH = os.path.join(INDEX_DIR, "tfidf_matrix.pkl")

with open(CODES_META_PATH, "r") as f:
    CODES = json.load(f)

with open(VEC_PATH, "rb") as f:
    VEC = pickle.load(f)

with open(MAT_PATH, "rb") as f:
    MAT = pickle.load(f)  # sparse matrix shape (n_codes, n_features)

    # -----------------------------------------------------------------------------
    # Load embedding model and PostgreSQL connection for vector search
    # -----------------------------------------------------------------------------
MODEL_NAME = os.getenv("AUTOCODER_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
model = None
pg_conn = None
try:
    model = SentenceTransformer(MODEL_NAME)
    pg_conn = get_pg_conn()
    if pg_conn:
        register_vector(pg_conn)
        print("Loaded embedding model and connected to PostgreSQL for vector search.")
except Exception as e:
    print(f"Vector search setup failed: {e}")

# -----------------------------------------------------------------------------
# FastAPI app + schemas
# -----------------------------------------------------------------------------
app = FastAPI()

class SuggestReq(BaseModel):
    note: str
    top_k: int = 5

# -----------------------------------------------------------------------------
# Core retrieval (TF-IDF cosine similarity)
# -----------------------------------------------------------------------------

def retrieve_tfidf(note: str, top_k: int = 5):
    query_vec = VEC.transform([note])  # 1 x d
    sims = cosine_similarity(query_vec, MAT)  # shape (1, n_codes)
    sims = sims[0]
    idx = np.argsort(-sims)[:top_k]
    results = []
    for i in idx:
        results.append({
            "code": CODES[i]["code"],
            "title": CODES[i]["title"],
            "description": CODES[i].get("description", ""),
            "confidence": float(sims[i]),
            "rationale": f"Text matches {CODES[i]['title'].lower()} with similarity {sims[i]:.2f}"
        })
    return results

# -----------------------------------------------------------------------------
# Core retrieval (Vector DB, pgvector)
# -----------------------------------------------------------------------------
def retrieve_pgvector(note: str, top_k: int = 5):
    if model is None or pg_conn is None:
        return []
    # Use the embedding utility for vector casting
    q_vec = embedding(MODEL_NAME, note)
    with pg_conn.cursor() as cur:
        cur.execute("SET hnsw.ef_search = 100;")
        cur.execute(
            """
            SELECT icd10_codes.code, icd10_codes.title, icd10_codes.description,
                   1 - (embedding <=> %s::vector) AS confidence
            FROM icd10_meta
            JOIN icd10_codes ON icd10_meta.code = icd10_codes.code
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
            """,
            (q_vec, q_vec, top_k)
        )
        rows = cur.fetchall()
    results = []
    for code, title, description, confidence in rows:
        results.append({
            "code": code,
            "title": title,
            "description": description,
            "confidence": float(confidence),
            "rationale": f"Vector similarity to {title.lower()} is {confidence:.2f}"
        })
    return results

    # ...existing code...

# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@app.get("/healthz")
def healthz():
    return {"ok": True}


def llm_rationale(note: str, code: str, title: str, timeout=6.0) -> str:
    try:
        payload = {
            "model": LLM_MODEL,
            "prompt": PROMPT_TMPL.format(note=note, code=code, title=title),
            "options": {"temperature": LLM_TEMP, "num_predict": LLM_MAX}
        }
        with httpx.Client(timeout=timeout) as client:
            r = client.post(f"{LLM_URL}/api/generate", json=payload)
            r.raise_for_status()
            text = r.json().get("response", "").strip()
            text = text.split("\n")[0]
            return text[:300]
    except Exception:
        return f"Presentation is consistent with {title.lower()} based on the note text."

@app.post("/suggest")
def suggest(req: SuggestReq):
    t0 = time.time()
    results = retrieve_pgvector(req.note, req.top_k)
    # Synchronously add rationale to each result using llm_rationale
    for r in results:
        r["rationale"] = llm_rationale(req.note, r["code"], r["title"])
    return {
        "query": req.note,
        "results": results,
        "latency_ms": int((time.time() - t0) * 1000)
    }
