#!/usr/bin/env bash
set -euo pipefail

mkdir -p policy_docs/raw

UA='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.3.1 Safari/605.1.15'

download_checked() {
  local url="$1"
  local out="$2"
  local tmp="${out}.download.tmp"

  if [ -s "$out" ]; then
    echo "SKIP: existing non-empty file: $out"
    echo "bytes: $(wc -c < "$out")"
    return 0
  fi

  echo "Downloading:"
  echo "  $url"
  echo "To:"
  echo "  $out"

  if curl --http1.1 -fL --retry 3 --retry-delay 2 --connect-timeout 30     -A "$UA"     "$url"     -o "$tmp"; then

    if [ -s "$tmp" ]; then
      mv "$tmp" "$out"
      echo "OK: $(wc -c < "$out") bytes"
      return 0
    fi
  fi

  echo "FAILED or empty: $out"
  echo "Temporary file, if present, was left for inspection: $tmp"
  return 1
}

echo "[1/3] GDPR PDF"
download_checked   'https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX%3A32016R0679'   'policy_docs/raw/gdpr-regulation-2016-679.pdf' || true

echo
echo "[2/3] EU AI Act PDF"
download_checked   'https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=OJ%3AL_202401689'   'policy_docs/raw/eu-ai-act-regulation-2024-1689.pdf' || true

echo
echo "[3/3] Result:"
ls -lh policy_docs/raw

echo
echo "Next: add the GPAI guidance PDF manually if it is not already present:"
echo "policy_docs/raw/eu-ai-act-gpai-guidelines-2025-draft-communication.pdf"
