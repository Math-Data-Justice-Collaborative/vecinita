# ############################################################################
# FILE: main.py
# ROLE: High-Fidelity Gemini Orchestrator. 
#       Validated Syntax for Gemini 3 Flash & Pydantic v2.
# ############################################################################

import os
import logging
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from src.agent.tools.db_search import db_search

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vecinita.main")

app = FastAPI(title="Vecinita Engine")

# --- THE CONTRACT (Pydantic v2) ---
class VecinitaResponse(BaseModel):
    answer_text: str = Field(description="Strictly ONE block of text. Max 4 sentences.")
    citation: str = Field(description="Format: 'Source: [URL/ID]'.")
    engagement_question: str = Field(description="A brief follow-up question.")

# --- THE LLM INITIALIZATION ---
# We use 'gemini-3-flash-preview' for frontier reasoning.
# Temperature 0.1 ensures maximum consistency for the auditor.
llm = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.1
)

# Bind the schema. This ensures the decoder only predicts tokens that fit our JSON.
structured_llm = llm.with_structured_output(VecinitaResponse)

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/ask")
async def ask_question(question: str) -> Dict[str, Any]:
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    try:
        # 1. RAG Retrieval
        context_data = db_search(question)
        context_text = "\n\n".join([f"Source: {c['source']}\n{c['content']}" for c in context_data])

        # 2. Message Construction (Bilingual Strategy Ready)
        messages = [
            SystemMessage(content="You are a Rhode Island community resource agent. Be factual and warm."),
            HumanMessage(content=f"CONTEXT DATA:\n{context_text}\n\nUSER QUESTION: {question}")
        ]

        # 3. Structured Inference
        output = structured_llm.invoke(messages)

        # 4. SURGICAL ASSEMBLY (Fixes Test 3 Paragraph Count)
        # We attach citation to answer for Para 1, then the question for Para 2.
        final_answer = (
            f"{output.answer_text.strip()}\n"
            f"{output.citation.strip()}\n\n"
            f"{output.engagement_question.strip()}"
        )

        return {
            "answer": final_answer,
            "context": context_data
        }

    except Exception as e:
        logger.error(f"Inference Error: {e}", exc_info=True)
        # We return the actual error string to debug the 'Connection Reset'
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

## end-of-file main.py
