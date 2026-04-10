"""System and informational endpoints for the agent service."""

from fastapi import APIRouter

from .. import main as agent_main

router = APIRouter()


@router.get("/")
async def get_root():
    """Return basic API metadata and common endpoint links."""
    return {
        "service": "Vecinita Backend API",
        "status": "running",
        "version": "2.0",
        "endpoints": {
            "health": "/health",
            "ask": "/ask?question=<your_question>",
            "docs": "/docs",
            "config": "/config",
        },
        "message": "Use the React frontend at http://localhost:3000 or call /ask endpoint directly",
    }


@router.get("/health")
async def health():
    """Return a lightweight health check for local and container probes."""
    return {"status": "ok"}


@router.get("/privacy")
def privacy():
    """Return the privacy policy markdown payload for frontend rendering."""
    policy_path = agent_main.Path(__file__).parent.parent.parent / "docs" / "PRIVACY_POLICY.md"
    if not policy_path.exists():
        policy_path = agent_main.Path(__file__).parents[4] / "docs" / "PRIVACY_POLICY.md"
    if policy_path.exists():
        return agent_main.JSONResponse({"markdown": policy_path.read_text(encoding="utf-8")})

    fallback_markdown = (
        "# Privacy Policy\n\n"
        "Privacy policy content is temporarily unavailable in this deployment.\n\n"
        "For the latest policy text, contact the Vecinita team."
    )
    return agent_main.JSONResponse({"markdown": fallback_markdown})
