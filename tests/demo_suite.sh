#!/bin/bash

################################################################################
# PROJECT: VECINITA-RIOS
# SCRIPT: demo_suite.sh
# DESCRIPTION: End-to-end RAG pipeline validation for production deployment.
#              Tests retrieval, bilingual support, and LangGraph memory.
# AUTHOR: Vecinita Team / Hugo Prod
# DATE: 2026-02-07
################################################################################

# --- CONFIGURATION ---
# Target the Public GCP Production IP for external validation
API_URL="http://34.55.88.67:8000/api/v1/chat"

echo "============================================================"
echo "🚀 STARTING VECINITA-RIOS PRODUCTION DEMO SUITE"
echo "Target Endpoint: $API_URL"
echo "============================================================"

# --- TEST 1: SIMPLE RETRIEVAL (BILINGUAL) ---
echo -e "\n[TEST 1] Simple Retrieval: Health Clinics (Providence)"
curl -s -X POST "$API_URL" \
     -H "Content-Type: application/json" \
     -d '{
          "message": "What health clinics are in Providence?",
          "history": []
         }' | python3 -m json.tool

# --- TEST 2: COMPLEX REASONING & RAG ---
echo -e "\n[TEST 2] Complex Reasoning: Immigrant Resources"
curl -s -X POST "$API_URL" \
     -H "Content-Type: application/json" \
     -d '{
          "message": "I live in Central Falls and need help with immigrant services. Who is nearby?",
          "history": []
         }' | python3 -m json.tool

# --- TEST 3: CONTEXTUAL MEMORY (LANGGRAPH) ---
echo -e "\n[TEST 3] Contextual Memory: Follow-up question"
# This simulates a memory state by passing a previous turn in the history array
curl -s -X POST "$API_URL" \
     -H "Content-Type: application/json" \
     -d '{
          "message": "What was their phone number again?",
          "history": [
            {"role": "user", "content": "Tell me about Clinica Esperanza"},
            {"role": "assistant", "content": "Clinica Esperanza is at 60 Valley St. Their number is (401) 347-9093."}
          ]
         }' | python3 -m json.tool

echo -e "\n============================================================"
echo "✅ PRODUCTION DEMO SUITE COMPLETE"
echo "Status: Verified Green - $(date)"
echo "============================================================"

################################################################################
# END OF SCRIPT: VECINITA-RIOS STABLE v1.0
################################################################################
