# ICD-10 Auto Encoder

This repository contains the implementation of an ICD-10 auto-encoder. The project is organized into the following directories:

- `backend/`: Contains backend-related code.
- `frontend/`: Contains frontend-related code.
- `data/`: Contains data files used for training and testing.
- `notebooks/`: Contains Jupyter notebooks for experimentation and analysis.

## Getting Started

To get started, clone this repository and navigate to the respective directories for more details.

how to start app 
docker compose up --build
# backend → http://localhost:8000/healthz
# frontend → http://localhost:8501



1-Week Ship Plan (ICD-10 Auto-Coder)

Goal: free-text chief complaint or note → top-k ICD-10-CM code suggestions with explanations and confidence.

Day 1 — Scope & Dataset

Define MVP: input text → top 5 codes (code, title, confidence, rationale).

Prepare codes table (ICD-10-CM: code, title, description, synonyms).

Create 20–30 seed test cases (short notes) covering common conditions (e.g., chest pain, low back pain, type 2 diabetes, URI, migraine, UTI, hypertension).

Repo scaffolding: backend/, frontend/, data/, notebooks/, README.md, LICENSE.

Day 2 — Ingestion & Indexing

Normalize codes: lowercase, strip punctuation, make search text = title + description + synonyms.

Build an embeddings index (FAISS) over search text (baseline: sentence-transformers MiniLM; stretch: clinical embeddings).

Store rows in PostgreSQL (or SQLite for speed) and keep FAISS index on disk.

Day 3 — Retrieval + Rerank + Explanation

Pipeline:

Embed user text → kNN retrieve 50 candidates from FAISS

Lexical fallback (BM25) for edge cases/negation

Light LLM rerank (pairwise or listwise) → top-5

LLM rationale generation (cite code titles) + simple confidence (normalized rerank scores)

Add negation guardrails (“no chest pain”, “rule out MI”).

Day 4 — Backend API (FastAPI)

Endpoints:

POST /suggest → returns ranked codes + rationales

GET /codes/{code} → details

GET /healthz

Add request logging & timing.

Day 5 — Frontend (Streamlit or React)

Text box → “Suggest Codes”

Table of results with: Code, Title, Confidence, Rationale

Click a row → drawer with full details + copy button.

Day 6 — Eval + Deployment

Offline eval: for each seed note, create a “gold” code list (1–3 codes).
Metrics: Top-1 / Top-3 accuracy, MRR, latency (P50/P95).

Deploy:

Streamlit Cloud / Hugging Face Spaces for the app

Railway/Fly.io/Render for FastAPI if separate

Add example curl + screenshots to README.

Day 7 — Polish for Recruiters

Write a crisp README (problem → approach → results → limits → roadmap).

Add small architecture diagram.

Record a 60-sec Loom demo.

Post to LinkedIn & pin the repo.