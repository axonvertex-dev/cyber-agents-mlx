#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:18110}"

echo "[1/5] Health"
curl -s "$BASE_URL/health" | python3 -m json.tool

echo

echo "[2/5] Policy status"
curl -s "$BASE_URL/policy/status" | python3 -m json.tool

echo

echo "[3/5] Policy search"
curl -s "$BASE_URL/policy/search"   -H "Content-Type: application/json"   -d '{
    "query": "GDPR data minimisation security logs EU AI Act human oversight cybersecurity",
    "top_k": 6,
    "balanced": true
  }' | python3 -m json.tool

echo

echo "[4/5] Fast triage"
curl -s "$BASE_URL/triage/fast"   -H "Content-Type: application/json"   -d @examples/ssh_failed_login.json | python3 -m json.tool

echo

echo "[5/5] Audit status"
curl -s "$BASE_URL/audit/status" | python3 -m json.tool

echo

echo "Smoke test complete."
