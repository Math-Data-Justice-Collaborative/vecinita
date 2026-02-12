#!/bin/bash
# ############################################################################
# FILE: tests/test_rag_fidelity.sh
# ROLE: Ensures Gemini handles massive RAG context without 413 errors.
# ############################################################################

URL="http://127.0.0.1:8080/ask"
QUESTION="List 3 elementary schools in Providence" # Triggers high-token search

echo "🚀 Stress Testing Gemini Bridge with Large Payload..."
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" -G "$URL" --data-urlencode "question=$QUESTION")

if [ "$STATUS_CODE" -eq 200 ]; then
    echo "✅ SUCCESS: Gemini handled the high-token request (200 OK)."
else
    echo "❌ FAIL: Received HTTP $STATUS_CODE. Check logs for 413 or Reset."
    exit 1
fi

## end-of-file test_rag_fidelity.sh
