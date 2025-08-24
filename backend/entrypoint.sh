#!/usr/bin/env bash
set -euo pipefail

: "${AUTOCODER_INDEX_DIR:=/app/data/index}"
: "${AUTOCODER_CODES_CSV:=/app/data/icd10_sample.csv}"

mkdir -p "$AUTOCODER_INDEX_DIR"


# Build TF-IDF artifacts if missing
if [ ! -f "$AUTOCODER_INDEX_DIR/tfidf_vectorizer.pkl" ] || [ ! -f "$AUTOCODER_INDEX_DIR/tfidf_matrix.pkl" ]; then
  echo "[entrypoint] Building TF-IDF index from $AUTOCODER_CODES_CSV -> $AUTOCODER_INDEX_DIR"

  PG_ARGS=""
  [ -n "$PG_HOST" ] && PG_ARGS="$PG_ARGS --pg-host $PG_HOST"
  [ -n "$PG_PORT" ] && PG_ARGS="$PG_ARGS --pg-port $PG_PORT"
  [ -n "$PG_USER" ] && PG_ARGS="$PG_ARGS --pg-user $PG_USER"
  [ -n "$PG_PASSWORD" ] && PG_ARGS="$PG_ARGS --pg-password $PG_PASSWORD"
  [ -n "$PG_DBNAME" ] && PG_ARGS="$PG_ARGS --pg-dbname $PG_DBNAME"

  python scripts/build_index.py --csv "$AUTOCODER_CODES_CSV" --out "$AUTOCODER_INDEX_DIR" $PG_ARGS
fi


# Enable hot reload in development mode
if [ "${HOT_RELOAD:-false}" = "true" ]; then
  echo "[entrypoint] Starting API with hot reload enabled."
  exec uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload --reload-dir backend
else
  echo "[entrypoint] Starting API without hot reload."
  exec uvicorn backend.app:app --host 0.0.0.0 --port 8000
fi
