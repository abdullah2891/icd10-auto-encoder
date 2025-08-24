#!/usr/bin/env bash
set -euo pipefail

: "${AUTOCODER_INDEX_DIR:=/app/data/index}"
: "${AUTOCODER_CODES_CSV:=/app/data/icd10_sample.csv}"

mkdir -p "$AUTOCODER_INDEX_DIR"

# Build TF-IDF artifacts if missing
if [ ! -f "$AUTOCODER_INDEX_DIR/tfidf_vectorizer.pkl" ] || [ ! -f "$AUTOCODER_INDEX_DIR/tfidf_matrix.pkl" ]; then
  echo "[entrypoint] Building TF-IDF index from $AUTOCODER_CODES_CSV -> $AUTOCODER_INDEX_DIR"
  python scripts/build_index.py --csv "$AUTOCODER_CODES_CSV" --out "$AUTOCODER_INDEX_DIR"
fi

# Start API
exec uvicorn backend.app:app --host 0.0.0.0 --port 8000
