"""Configuration and model-selection endpoints for the local agent runtime."""

from fastapi import APIRouter, Body

from src.agent.openapi_examples import AGENT_MODEL_SELECTION_BODY

from .. import main as agent_main

router = APIRouter()


@router.get("/model-selection")
def get_model_selection():
    """Return the active local model selection plus available runtime options."""
    available = agent_main.config()
    return {
        "current": {
            "provider": agent_main.CURRENT_SELECTION.get("provider"),
            "model": agent_main.CURRENT_SELECTION.get("model"),
            "locked": agent_main.CURRENT_SELECTION.get("locked"),
        },
        "available": available,
    }


@router.post("/model-selection")
def set_model_selection(
    selection: agent_main.ModelSelection = Body(openapi_examples=AGENT_MODEL_SELECTION_BODY),
):
    """Persist a validated local model selection when the runtime is unlocked."""
    if agent_main.CURRENT_SELECTION.get("locked"):
        raise agent_main.HTTPException(status_code=403, detail="Model selection is locked")

    normalized_provider = agent_main.llm_client_manager.normalize_provider(selection.provider)
    if normalized_provider != "ollama":
        raise agent_main.HTTPException(
            status_code=400,
            detail="Only the local Ollama provider is supported",
        )

    if selection.model:
        available = agent_main.config()
        available_models = available["models"].get("ollama", [])
        if selection.model not in available_models:
            raise agent_main.HTTPException(
                status_code=400,
                detail=f"Unsupported local model: {selection.model}",
            )

    agent_main._save_model_selection_to_file("ollama", selection.model, selection.lock)
    return {"status": "ok", "current": agent_main.CURRENT_SELECTION}


@router.get("/config")
def config():
    """Expose local-only model discovery and runtime flags for the frontend."""
    payload = agent_main.llm_client_manager.config_payload()
    payload["runtime"] = {
        "fast_mode": agent_main.agent_fast_mode,
        "max_response_sentences": agent_main.agent_max_response_sentences,
        "max_response_chars": agent_main.agent_max_response_chars,
        "reachable": agent_main.llm_client_manager.is_reachable(),
    }
    return payload
