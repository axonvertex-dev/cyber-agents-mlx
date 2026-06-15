#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v ollama >/dev/null 2>&1; then
  echo "ERROR: ollama command not found. Install and start native Ollama/MLX first."
  exit 1
fi

FAST_MODEL="${FAST_MODEL:-gemma4:e2b-mlx}"
DEEP_MODEL="${DEEP_MODEL:-gemma4:e4b-mlx}"
EMBED_MODEL="${EMBED_MODEL:-embeddinggemma:300m-qat-q8_0}"

echo "Pulling project models..."
echo "FAST_MODEL=$FAST_MODEL"
echo "DEEP_MODEL=$DEEP_MODEL"
echo "EMBED_MODEL=$EMBED_MODEL"

ollama pull "$FAST_MODEL"
ollama pull "$DEEP_MODEL"
ollama pull "$EMBED_MODEL"

echo "Models ready."
ollama list
