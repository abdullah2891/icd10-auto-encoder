from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict
import json, os, time, pickle
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix

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
# Routes
# -----------------------------------------------------------------------------
@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.post("/suggest")
def suggest(req: SuggestReq):
    t0 = time.time()
    results = retrieve_tfidf(req.note, req.top_k)
    return {
        "query": req.note,
        "results": results,
        "latency_ms": int((time.time() - t0) * 1000)
    }
