#!/bin/bash
# ############################################################################
# FILE: master_test.sh
# PATH: tests/master_test.sh
# ROLE: Master Orchestrator for Vecinita Quality Suite.
# ############################################################################

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' 

echo -e "===================================================="
echo -e "🚀 STARTING VECINITA MASTER TEST SUITE"
echo -e "====================================================\n"

# API Contract
echo -n "Test 1: API Contract... "
./tests/test_api_contract.sh > /dev/null 2>&1
if [ $? -eq 0 ]; then echo -e "${GREEN}PASS${NC}"; else echo -e "${RED}FAIL${NC}"; fi

# RAG Fidelity
echo -n "Test 2: RAG Fidelity...  "
./tests/test_rag_fidelity.sh > /dev/null 2>&1
if [ $? -eq 0 ]; then echo -e "${GREEN}PASS${NC}"; else echo -e "${RED}FAIL${NC}"; fi

# System Audit
echo -e "Test 3: Rule Compliance Audit:"
python3 tests/audit_rules.py
if [ $? -eq 0 ]; then echo -e "${GREEN}PASS${NC}"; else echo -e "${RED}FAIL${NC}"; fi

# Connectivity
echo -n "Test 4: Connectivity...  "
./tests/warm_check.sh > /dev/null 2>&1
if [ $? -eq 0 ]; then echo -e "${GREEN}PASS${NC}"; else echo -e "${RED}FAIL${NC}"; fi

echo -e "\n===================================================="
echo -e "🏁 TESTING COMPLETE"

## end-of-file master_test.sh
