#!/bin/bash
# ############################################################################
# FILE: test_api_contract.sh
# PATH: tests/test_api_contract.sh
# ROLE: Verifies the "Contract" between Backend and Frontend.
# INPUT: Localhost API -> OUTPUT: Pass/Fail (JSON Validation)
# ############################################################################

URL="http://127.0.0.1:8080/ask"
echo "🔍 Checking API Contract..."

RESPONSE=$(curl -s -G "$URL" --data-urlencode "question=Hello")

# Check if 'context' is a List
IS_LIST=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(isinstance(data.get('context'), list))")

if [ "$IS_LIST" == "True" ]; then
    echo "✅ SUCCESS: Context is a List."
else
    echo "❌ FAIL: Context is not a List. Morphing error detected."
    exit 1
fi

## end-of-file test_api_contract.sh
