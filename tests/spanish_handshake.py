#!/usr/bin/env python3
"""
RIOS Institute - Stability Test Suite
Name: Spanish Handshake Isolation
Description: Tests the Pydantic 'extra=allow' logic to prevent crashes when 
             the LLM hallucinates language fields in tool calls.
"""

import os
import datetime
from pydantic import BaseModel, Field, ValidationError

# --- LOGGING SETUP ---
LOG_FILE = "logs/handshake_results.log"
os.makedirs("logs", exist_ok=True)

def log_result(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(message)

# --- THE COMPONENT: THE SCHEMA ---
class StaticResponseInput(BaseModel):
    query: str = Field(description="The search query")

    # THE STABILITY FIX
    class Config:
        extra = "allow"  # This allows the tool to ignore 'language' or other extra fields

# --- THE INTERACTION: VALIDATION ---
def test_handshake(test_name, payload):
    log_result(f"--- Running Test: {test_name} ---")
    log_result(f"Input Payload: {payload}")
    try:
        # Simulate the Handshake
        validated = StaticResponseInput(**payload)
        log_result("✅ SUCCESS: Handshake accepted.")
        log_result(f"Effective Data: {validated.dict()}")
    except ValidationError as e:
        log_result("❌ CRASH: Handshake rejected extra fields.")
        log_result(f"Error Details: {e}")
    log_result("-" * 40)

if __name__ == "__main__":
    # Clear log for fresh run
    with open(LOG_FILE, "w") as f:
        f.write(f"=== SPANISH HANDSHAKE TEST: {datetime.datetime.now()} ===\n")

    # SCENARIO 1: Perfect English Call
    test_handshake("Standard English", {"query": "school"})

    # SCENARIO 2: Spanish Hallucinated Call (The Crash Source)
    test_handshake("Spanish Hallucination", {"query": "escuela", "language": "es"})

    log_result("### END-OF-FILE: Spanish Handshake Test Complete ###")
