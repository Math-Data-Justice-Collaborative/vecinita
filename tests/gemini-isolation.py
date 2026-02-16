#tests/gemini_isolation.py
import os
import logging
import google.generativeai as genai

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("gemini-isolation")

def isolate_model():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ ERROR: GOOGLE_API_KEY is not set.")
        return

    print(f"--- 🛰️ Connectivity Test (Key: {api_key[:8]}...) ---")
    genai.configure(api_key=api_key)

    print("\n1. 🔍 DISCOVERING AUTHORIZED MODELS:")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"   ✅ [AUTHORIZED]: {m.name}")
    except Exception as e:
        print(f"   ❌ DISCOVERY FAILED: {e}")
        return

    print("\n2. 🧪 PROBING 2026 STABLE MODELS:")
    # Using specific 2026 identifiers to bypass 404s
    for model_id in ["gemini-3-flash-preview", "gemini-2.5-flash", "gemini-1.5-flash"]:
        print(f"   Testing {model_id}...")
        try:
            model = genai.GenerativeModel(model_id)
            response = model.generate_content("Say 'Engine Online'")
            print(f"   🌟 SUCCESS [{model_id}]: {response.text.strip()}")
            return
        except Exception as e:
            print(f"   🚫 {model_id} failed.")

if __name__ == "__main__":
    isolate_model()
