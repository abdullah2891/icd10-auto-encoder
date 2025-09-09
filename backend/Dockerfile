# TF-IDF only (no faiss)
FROM public.ecr.aws/docker/library/python:3.11-slim

# System deps for numpy/scipy/scikit-learn wheels
RUN apt-get update \
     && apt-get install -y --no-install-recommends \
         build-essential \
         gcc \
         g++ \
         curl \
         libopenblas-dev \
         libpq-dev \
     && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (leverages layer cache)
COPY requirements.txt ./


ENV PIP_NO_CACHE_DIR=1 \
    PIP_DEFAULT_TIMEOUT=180 \
    PIP_INDEX_URL=https://pypi.org/simple


# Try wheels only; if (rare) wheels are missing, temporarily install build tools then remove
RUN python -m pip install -U pip setuptools wheel \
 && pip install --only-binary=:all: -r /tmp/requirements.txt \
 || (apt-get update && apt-get install -y --no-install-recommends build-essential rustc cargo \
     && pip install -r /tmp/requirements.txt && \
     apt-get purge -y build-essential rustc cargo && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*)

 
# Copy source
COPY backend ./backend
COPY scripts ./scripts
COPY data ./data

# Add entrypoint that ensures TF-IDF artifacts exist
COPY backend/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Env defaults (override at runtime if needed)
ENV AUTOCODER_INDEX_DIR=/app/data/index \
    AUTOCODER_CODES_CSV=/app/data/icd10_sample.csv \
    PYTHONUNBUFFERED=1

EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
