# TF-IDF only (no faiss)
FROM python:3.11-slim

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
RUN pip install --no-cache-dir -r requirements.txt

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
