#!/bin/bash
#/mnt/data_prod/vecinita/spanish_test.sh
# Configuration
API_URL="http://127.0.0.1:8080/ask"
LOG_FILE="diagnostic_results.log"

echo "=== Vecinita Diagnostic Test Suite ===" > $LOG_FILE
echo "Started at: $(date)" >> $LOG_FILE
echo "---------------------------------------" >> $LOG_FILE

tests=(
  "1. Baseline: English|Hello"
  "2. Encoding: Spanish ASCII|Hola como estas"
  "3. Encoding: Spanish UTF8|¿Cómo estás?"
  "4. Logic: Spanish Math|Cuanto es dos mas dos"
  "5. Logic: Spanish Math UTF8|¿Cuánto es dos más dos?"
  "6. Tool: English Search|school"
  "7. Tool: Spanish Search ASCII|escuela"
  "8. Tool: Spanish Search UTF8|¿Dónde hay una escuela?"
  "9. Tool: Mixed Lang|Where is the nearest escuela"
  "10. Stress: Long Spanish UTF8|Necesito ayuda para encontrar una clínica de salud cerca de Providence"
)

for test in "${tests[@]}"; do
  DESC=$(echo $test | cut -d'|' -f1)
  QUERY=$(echo $test | cut -d'|' -f2)
  
  echo "Testing: $DESC..."
  echo "TEST: $DESC" >> $LOG_FILE
  echo "QUERY: $QUERY" >> $LOG_FILE
  
  ENCODED_QUERY=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$QUERY'))")
  
  # Capture response and status code
  RESPONSE_BODY=$(curl -s "$API_URL?question=$ENCODED_QUERY")
  STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL?question=$ENCODED_QUERY")
  
  echo "HTTP_STATUS: $STATUS_CODE" >> $LOG_FILE
  echo "RESPONSE: $RESPONSE_BODY" >> $LOG_FILE
  
  # If it's a 500 error, grab the specific traceback from journalctl
  if [ "$STATUS_CODE" -eq 500 ]; then
    echo "DETECTED 500: Extracting system logs..." >> $LOG_FILE
    sudo journalctl -u vecinita.service -n 15 --no-pager >> $LOG_FILE
  fi
  
  echo "---------------------------------------" >> $LOG_FILE
  sleep 2
done

echo "Tests Complete. Results saved to $LOG_FILE"
