# ############################################################################
# FILE: audit_rules.py
# PATH: tests/audit_rules.py
# ROLE: High-Fidelity Linguistic Auditor. Dictionary-Aware Content Extraction.
# ############################################################################

import requests
import sys

API_URL = "http://127.0.0.1:8080/ask"
TEST_QUERY = "What are the requirements for the SNAP program in Rhode Island?"

def extract_text(raw_data):
    """
    DATA MORPH: Deep Extraction.
    Handles String, List[str], and List[Dict] formats to find the AI's answer.
    """
    if isinstance(raw_data, str):
        return raw_data
    if isinstance(raw_data, list):
        # Extract content if it's a list of dicts (e.g., [{'content': '...'}])
        extracted = []
        for item in raw_data:
            if isinstance(item, dict):
                # Look for common keys where the text might hide
                text_val = item.get("content") or item.get("text") or str(item)
                extracted.append(text_val)
            else:
                extracted.append(str(item))
        return "\n\n".join(extracted)
    return str(raw_data)

def run_audit():
    try:
        response = requests.get(API_URL, params={"question": TEST_QUERY}, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # --- THE FIX: DEEP EXTRACTION ---
        answer = extract_text(data.get("answer", ""))
        
        # 1. BREVITY CHECK (Max 2 Paragraphs)
        paragraphs = [p for p in answer.split('\n\n') if p.strip()]
        p_count = len(paragraphs)
        p_pass = p_count <= 2
        
        # 2. ENGAGEMENT CHECK (Final Question)
        has_question = answer.strip().endswith('?')
        
        # 3. CITATION CHECK (Source URL presence)
        has_citation = "Source:" in answer or "http" in answer

        # --- RESULTS DISPLAY ---
        print(f"\n🔍 Auditing Query: '{TEST_QUERY}'")
        print("-" * 50)
        print(f"{'RULE CRITERIA' : <30} | {'STATUS' : <10}")
        print("-" * 50)
        print(f"{'Brevity (Max 2 Paras)' : <30} | {'✅ PASS' if p_pass else '❌ FAIL'} ({p_count})")
        print(f"{'Follow-up Question (?)' : <30} | {'✅ PASS' if has_question else '❌ FAIL'}")
        print(f"{'Source Citation' : <30} | {'✅ PASS' if has_citation else '❌ FAIL'}")
        print("-" * 50)
        
        if not (p_pass and has_question and has_citation):
            print(f"\n📝 RAW RESPONSE FOR DEBUGGING:\n{answer}\n")
            sys.exit(1)
            
        print("🎉 ALL RULES FOLLOWED.")
        sys.exit(0)

    except Exception as e:
        print(f"\n❌ AUDIT CRASHED: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_audit()

## end-of-file audit_rules.py
