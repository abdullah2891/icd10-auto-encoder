#!/bin/sh
set -e
ollama serve &

# Wait for Ollama to be ready
until curl -sf http://localhost:11434/api/tags > /dev/null; do
  sleep 1
done

ollama pull llama3.2:1b

# Keep the container running
wait
