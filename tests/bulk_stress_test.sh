#!/bin/bash

################################################################################
# PROJECT: Vecinita - RIOS Agent Stress Test
# VERSION: 3.0.0 (POST /api/v1/chat Migration)
# DATE: 2026-02-07
################################################################################

# Configuration - Aligned with the verified 8080/api/v1/chat endpoint
BASE_URL="http://127.0.0.1:8080/api/v1/chat"
LOG_FILE="logs/bulk_test_results.log"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# Ensure log directory exists
mkdir -p logs

echo "=== BULK STRESS TEST: $TIMESTAMP ===" > $LOG_FILE
echo "Endpoint: $BASE_URL" >> $LOG_FILE
echo "----------------------------------------" >> $LOG_FILE

# Query List: "Query|Condition_Tag"
QUERIES=(
  "Hello|English_Baseline"
  "Hola|Spanish_Baseline"
  "Where is the nearest school?|Tool_Trigger_English"
  "¿Cómo reporto una fuga?|Tool_Trigger_Spanish"
  "What is the community policy on noise?|Policy_Inquiry"
  "I need emergency assistance|High_Priority"
  "Necesito ayuda médica|Spanish_Medical"
  "Calculate 15% of 250|Logic_Math"
  "Write a haiku about a neighbor|Creative"
  "Goodbye|Termination"
)

echo "🚀 Starting RIOS Agent Stress Test..."
echo "Targeting: $BASE_URL"

for ENTRY in "${QUERIES[@]}"; do
    # Split the query and the tag
    QUERY=$(echo $ENTRY | cut -d'|' -f1)
    TAG=$(echo $ENTRY | cut -d'|' -f2)

    echo -n "Testing [$TAG]... "

    # Execute the POST request
    # Note: We send 'message' as the key to match the ChatMessage model
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL" \
         -H "Content-Type: application/json" \
         -d "{
               \"message\": \"$QUERY\",
               \"thread_id\": \"test_suite_$(date +%s)\"
             }")

    # Parse Status and Body
    HTTP_STATUS=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')

    # Log results
    {
      echo "TAG: $TAG"
      echo "QUERY: $QUERY"
      echo "STATUS: $HTTP_STATUS"
      echo "RESPONSE: $BODY"
      echo "----------------------------------------"
    } >> $LOG_FILE

    if [ "$HTTP_STATUS" == "200" ]; then
        echo "✅ OK"
    else
        echo "❌ FAIL ($HTTP_STATUS)"
    fi
done

echo "### END OF BULK TEST ###" >> $LOG_FILE
echo "Done! Full details in: $LOG_FILE"
