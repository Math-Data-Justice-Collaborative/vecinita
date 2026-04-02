"""Cross-platform env var sync contract tests.

These tests parse static source files only — no running services,
no secrets required.  They enforce that:
  - render.yaml/render.staging.yaml declare the same canonical keys
  - Modal proxy config uses ALLOWED_ORIGINS (not CORS_ORIGINS)
  - GH workflows reference the expected Modal credentials
  - No deprecated alias keys remain in render.yaml
  - No localhost values appear in critical endpoint entries
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

# ---------------------------------------------------------------------------
# Paths (relative to repo root — three parents up from backend/tests/contracts/)
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = REPO_ROOT / "backend"
RENDER_YAML = REPO_ROOT / "render.yaml"
RENDER_STAGING_YAML = REPO_ROOT / "render.staging.yaml"
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
MODAL_PROXY_CONFIG = REPO_ROOT / "services" / "modal-proxy" / "app" / "config.py"
SCRAPER_CONFIG = (
    REPO_ROOT / "services" / "scraper" / "src" / "vecinita_scraper" / "core" / "config.py"
)
DATA_MGMT_CONFIG = (
    REPO_ROOT
    / "services"
    / "data-management-api"
    / "packages"
    / "shared-config"
    / "shared_config"
    / "__init__.py"
)
RENDER_ENV_CONTRACT = BACKEND_ROOT / "src" / "utils" / "render_env_contract.py"

pytestmark = pytest.mark.contract


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_render_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def _render_env_keys(data: dict) -> dict[str, set[str]]:
    """Return {service_name: set_of_env_keys} from a render.yaml dict."""
    result: dict[str, set[str]] = {}
    for svc in data.get("services", []):
        name = svc.get("name", "")
        keys: set[str] = set()
        for env_entry in svc.get("envVars", []):
            if "key" in env_entry:
                keys.add(env_entry["key"])
        result[name] = keys
    return result


def _required_keys_from_source() -> set[str]:
    """Import REQUIRED_KEYS from render_env_contract without using importlib."""
    src = RENDER_ENV_CONTRACT.read_text()
    match = re.search(r"REQUIRED_KEYS\s*:\s*set\[str\]\s*=\s*\{([^}]+)\}", src, re.DOTALL)
    assert match, "Could not parse REQUIRED_KEYS from render_env_contract.py"
    raw = match.group(1)
    return {m.group(1) for m in re.finditer(r'"([^"]+)"', raw)}


# ---------------------------------------------------------------------------
# 1. render.yaml declares every key in render_env_contract.REQUIRED_KEYS
# ---------------------------------------------------------------------------


def test_render_yaml_declares_all_contract_required_keys():
    """Every key in REQUIRED_KEYS must appear in at least one render.yaml service."""
    data = _load_render_yaml(RENDER_YAML)
    all_keys: set[str] = set()
    for keys in _render_env_keys(data).values():
        all_keys |= keys

    required = _required_keys_from_source()
    # DATABASE_URL, AGENT_SERVICE_URL are bound via fromDatabase/fromService — not in env list
    infra_bound = {"DATABASE_URL", "AGENT_SERVICE_URL"}
    missing = required - all_keys - infra_bound
    assert not missing, f"render.yaml does not declare these REQUIRED_KEYS: {sorted(missing)}"


# ---------------------------------------------------------------------------
# 2. render.staging.yaml key-set matches render.yaml
# ---------------------------------------------------------------------------


def test_render_staging_mirrors_prod_env_keys():
    """Staging and prod env key sets must match (no silent drift)."""
    prod_data = _load_render_yaml(RENDER_YAML)
    staging_data = _load_render_yaml(RENDER_STAGING_YAML)

    prod_keys = _render_env_keys(prod_data)
    staging_keys = _render_env_keys(staging_data)

    # Normalise names: strip -staging suffix for comparison
    normalised_staging = {k.replace("-staging", ""): v for k, v in staging_keys.items()}
    normalised_prod = dict(prod_keys)

    for svc_name, prod_svc_keys in normalised_prod.items():
        staging_svc_keys = normalised_staging.get(svc_name, set())
        extra_in_prod = prod_svc_keys - staging_svc_keys
        extra_in_staging = staging_svc_keys - prod_svc_keys
        assert (
            not extra_in_prod
        ), f"Service '{svc_name}': prod has keys not in staging: {sorted(extra_in_prod)}"
        assert (
            not extra_in_staging
        ), f"Service '{svc_name}': staging has extra keys not in prod: {sorted(extra_in_staging)}"


# ---------------------------------------------------------------------------
# 3. modal-proxy uses ALLOWED_ORIGINS (not CORS_ORIGINS)
# ---------------------------------------------------------------------------


def test_modal_proxy_uses_allowed_origins_not_cors_origins():
    """modal-proxy must use ALLOWED_ORIGINS env var, not CORS_ORIGINS."""
    if not MODAL_PROXY_CONFIG.exists():
        pytest.skip("modal-proxy submodule not checked out")
    src = MODAL_PROXY_CONFIG.read_text()
    assert (
        "allowed_origins" in src
    ), "services/modal-proxy/app/config.py must declare an 'allowed_origins' alias"
    # Ensure old CORS_ORIGINS alias is gone
    assert (
        'alias="cors_origins"' not in src
    ), "services/modal-proxy/app/config.py still uses deprecated alias='cors_origins'"


# ---------------------------------------------------------------------------
# 4. GH workflows reference MODAL_TOKEN_ID and MODAL_TOKEN_SECRET
# ---------------------------------------------------------------------------


def test_gh_workflows_reference_modal_credentials():
    """At least one workflow must reference MODAL_TOKEN_ID and MODAL_TOKEN_SECRET."""
    if not WORKFLOWS_DIR.exists():
        pytest.skip(".github/workflows not found")
    all_workflow_text = "\n".join(p.read_text() for p in WORKFLOWS_DIR.glob("*.yml"))
    secrets = set(re.findall(r"secrets\.([A-Z0-9_]+)", all_workflow_text))
    assert "MODAL_TOKEN_ID" in secrets, "No workflow references secrets.MODAL_TOKEN_ID"
    assert "MODAL_TOKEN_SECRET" in secrets, "No workflow references secrets.MODAL_TOKEN_SECRET"


# ---------------------------------------------------------------------------
# 5. No localhost in render.yaml critical endpoint values
# ---------------------------------------------------------------------------


def test_no_localhost_in_render_yaml_endpoint_values():
    """render.yaml must not set localhost for any *_URL / *_API_URL / *_ENDPOINT key."""
    src = RENDER_YAML.read_text()
    url_key_section = re.findall(
        r"key:\s*((?:VECINITA_[A-Z_]+_URL|[A-Z_]+_ENDPOINT|[A-Z_]+_API_URL))\n\s+value:\s*(\S+)",
        src,
    )
    bad = [(k, v) for k, v in url_key_section if "localhost" in v.lower()]
    assert not bad, f"render.yaml sets localhost for endpoint keys: {bad}"


# ---------------------------------------------------------------------------
# 6. Deprecated alias keys are absent from render.yaml
# ---------------------------------------------------------------------------

DEPRECATED_KEYS = {
    "MODAL_OLLAMA_ENDPOINT",
    "MODAL_EMBEDDING_ENDPOINT",
    "OLLAMA_BASE_URL",
    "EMBEDDING_SERVICE_URL",
    "MODAL_PROXY_AUTH_TOKEN",
    "X_PROXY_TOKEN",
}


def test_no_deprecated_alias_keys_in_render_yaml():
    """Deprecated alias env keys must not appear in render.yaml after Phase 0."""
    data = _load_render_yaml(RENDER_YAML)
    all_keys: set[str] = set()
    for keys in _render_env_keys(data).values():
        all_keys |= keys

    still_present = DEPRECATED_KEYS & all_keys
    assert (
        not still_present
    ), f"render.yaml still contains deprecated alias keys: {sorted(still_present)}"


def test_no_deprecated_alias_keys_in_render_staging_yaml():
    """Deprecated alias env keys must not appear in render.staging.yaml after Phase 0."""
    data = _load_render_yaml(RENDER_STAGING_YAML)
    all_keys: set[str] = set()
    for keys in _render_env_keys(data).values():
        all_keys |= keys

    still_present = DEPRECATED_KEYS & all_keys
    assert (
        not still_present
    ), f"render.staging.yaml still contains deprecated alias keys: {sorted(still_present)}"


# ---------------------------------------------------------------------------
# 7. Scraper uses canonical SUPABASE_URL / SUPABASE_KEY
# ---------------------------------------------------------------------------


def test_scraper_config_uses_canonical_supabase_keys():
    """Scraper config.py must read SUPABASE_URL (not SUPABASE_PROJECT_URL) primarily."""
    if not SCRAPER_CONFIG.exists():
        pytest.skip("scraper submodule not checked out")
    src = SCRAPER_CONFIG.read_text()
    assert (
        'os.getenv("SUPABASE_URL")' in src
    ), "scraper config must read SUPABASE_URL as the primary Supabase URL key"
    assert (
        'os.getenv("SUPABASE_KEY")' in src
    ), "scraper config must read SUPABASE_KEY as the primary Supabase key"


# ---------------------------------------------------------------------------
# 8. data-management-api uses canonical VECINITA_* and ALLOWED_ORIGINS
# ---------------------------------------------------------------------------


def test_data_management_api_uses_canonical_env_keys():
    """data-management-api shared-config must use canonical VECINITA_* and ALLOWED_ORIGINS."""
    if not DATA_MGMT_CONFIG.exists():
        pytest.skip("data-management-api submodule not checked out")
    src = DATA_MGMT_CONFIG.read_text()
    assert "VECINITA_SCRAPER_API_URL" in src
    assert "VECINITA_MODEL_API_URL" in src
    assert "VECINITA_EMBEDDING_API_URL" in src
    assert "ALLOWED_ORIGINS" in src
    # Old names must be gone
    assert '"SCRAPER_SERVICE_URL"' not in src
    assert '"MODEL_SERVICE_URL"' not in src
    assert '"CORS_ORIGINS"' not in src


# ---------------------------------------------------------------------------
# 9. render-deploy.yml gates deploy on CI tests (Phase C validation)
# ---------------------------------------------------------------------------


def test_render_deploy_workflow_gates_deploy_on_ci():
    """render-deploy.yml must have a deploy job that needs validate or test jobs."""
    deploy_workflow = WORKFLOWS_DIR / "render-deploy.yml"
    if not deploy_workflow.exists():
        pytest.skip("render-deploy.yml not found")
    src = deploy_workflow.read_text()
    data = yaml.safe_load(src)
    jobs = data.get("jobs", {})
    # Accept either 'deploy' (new canonical) or 'deploy-production' (legacy name)
    deploy_job_name = "deploy" if "deploy" in jobs else "deploy-production"
    assert (
        deploy_job_name in jobs
    ), "render-deploy.yml must have a 'deploy' or 'deploy-production' job"
    deploy_needs = jobs[deploy_job_name].get("needs", [])
    if isinstance(deploy_needs, str):
        deploy_needs = [deploy_needs]
    ci_jobs = {"validate", "test", "quality", "lint", "backend-quality", "frontend-quality"}
    assert ci_jobs & set(
        deploy_needs
    ), f"deploy/deploy-production job must need at least one CI job from {ci_jobs}; needs={deploy_needs}"
