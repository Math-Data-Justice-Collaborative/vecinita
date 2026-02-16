# ############################################################################
# FILE: main.py
# ROLE: High-Fidelity Gemini Orchestrator. 
#       Unified Resilience Ladder & Robust Assembly.
# ############################################################################

import os
import logging
from typing import Dict, Any, List
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from src.agent.tools.db_search import db_search

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vecinita.main")

app = FastAPI(title="Vecinita Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- THE CONTRACT (Pydantic v2) ---
class VecinitaResponse(BaseModel):
    answer_text: str = Field(description="Strictly ONE block of text. Max 4 sentences.")
    citation: str = Field(description="Format: 'Source: [URL/ID]'.")
    engagement_question: str = Field(description="A brief follow-up question.")

# --- THE RESILIENCE LADDER ---
# We start with gemini-pro as it is the most universally stable across API versions.

MODELS_TO_TRY = [
    "gemini-3-flash-preview",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-flash-latest"
]

def get_resilient_llm():
    """Attempts to initialize the best available model with zero retry delay."""
    for model_name in MODELS_TO_TRY:
        try:
            logger.info(f"🔄 Attempting to lock in model: {model_name}")
            llm_candidate = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=os.getenv("GOOGLE_API_KEY"),
                temperature=0.1,
                max_retries=0,  # Fast fail to move to the next ladder rung
                convert_system_message_to_human=True
            )
            # Connectivity probe
            llm_candidate.invoke([HumanMessage(content="ping")])
            logger.info(f"✅ Success! Model verified: {model_name}")
            return llm_candidate
        except Exception as e:
            logger.warning(f"⚠️ Model {model_name} unavailable: {e}")
    return None

# Initializing the engine
llm = get_resilient_llm()
structured_llm = llm.with_structured_output(VecinitaResponse) if llm else None

@app.get("/")
async def serve_gui():
    return FileResponse("index.html")

@app.get("/health")
async def health():
    if structured_llm:
        return {"status": "healthy", "model": llm.model}
    return {"status": "degraded", "error": "No LLM available"}

@app.get("/ask")
async def ask_question(question: str) -> Dict[str, Any]:
    if not structured_llm:
        raise HTTPException(status_code=503, detail="AI Engine is offline.")
    
    try:
        # 1. RAG Retrieval
        context_data = db_search(question)
        context_text = "\n\n".join([f"Source: {c['source']}\n{c['content']}" for c in context_data])

        # 2. Message Construction
        messages = [
            SystemMessage(content="You are a warm community resource agent. Answer in the user's language."),
            HumanMessage(content=f"CONTEXT DATA:\n{context_text}\n\nUSER QUESTION: {question}")
        ]

        # 3. Structured Inference
        output = structured_llm.invoke(messages)

        # 4. ROBUST ASSEMBLY
        try:
            answer_part = output.answer_text.strip() if (output and output.answer_text) else "No pude generar respuesta."
            citation_part = output.citation.strip() if (output and output.citation) else "Fuente: Local."
            engagement_part = output.engagement_question.strip() if (output and output.engagement_question) else "¿Algo más?"
            final_answer = f"{answer_part}\n{citation_part}\n\n{engagement_part}"
        except Exception:
            final_answer = "Error en el ensamblaje de la respuesta."

        return {"answer": final_answer, "context": context_data}

    except Exception as e:
        logger.error(f"Inference Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

# ############################################################################
# END OF FILE: main.py
# ############################################################################
