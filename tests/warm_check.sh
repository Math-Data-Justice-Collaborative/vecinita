#!/bin/bash
# ############################################################################
# FILE: warmup_check.sh
# PATH: tests/warmup_check.sh
# ROLE: Diagnostic tool to verify API and RAG pipeline health.
# INPUT: Localhost API Response -> OUTPUT: Status report
# ############################################################################

URL="http://127.0.0.1:8080/ask"
QUESTION="List 3 elementary schools in Providence"

echo "🚀 Running Morning Diagnostic..."
RESPONSE=$(curl -s -G "$URL" --data-urlencode "question=$QUESTION")

# Check for valid JSON and context type
CONTEXT_TYPE=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(type(data.get('context')))")

if [[ "$CONTEXT_TYPE" == *"'list'"* ]]; then
    echo "✅ RAG Pipeline: Structured Data Flowing"
else
    echo "❌ RAG Pipeline: Data Morph Error (Expected List)"
fi

echo "🏁 Check Complete."

## end-of-file warmup_check.sh
