"""One-shot: inspect llm-models manifest and mark g9v3:3b available if weights exist."""

from __future__ import annotations

import json
from pathlib import Path

import modal

app = modal.App("vecinita-spike-fix-manifest")
vol = modal.Volume.from_name("llm-models")


@app.function(volumes={"/models": vol}, timeout=120)
def fix_g9v3_manifest() -> str:
    """Reload volume, print manifest/repos, mark g9v3:3b available when present."""
    vol.reload()
    mp = Path("/models/manifest.json")
    repos = Path("/models/repos")
    lines: list[str] = [f"manifest_exists={mp.exists()}"]
    if mp.exists():
        lines.append(mp.read_text(encoding="utf-8")[:4000])
    if repos.exists():
        lines.append("repos=" + ",".join(sorted(p.name for p in repos.iterdir())))
    g9 = repos / "g9v3_3b"
    n_files = len(list(g9.rglob("*"))) if g9.exists() else 0
    lines.append(f"g9v3_path_exists={g9.exists()} n_files={n_files}")
    if not g9.exists() or n_files == 0:
        return "\n".join([*lines, "NO_WEIGHTS"])
    data: dict[str, object] = {"models": []}
    if mp.exists():
        loaded = json.loads(mp.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            data = loaded
    models_raw = data.get("models")
    models: list[dict[str, object]] = (
        [m for m in models_raw if isinstance(m, dict)] if isinstance(models_raw, list) else []
    )
    found = False
    for entry in models:
        if entry.get("model_id") == "g9v3:3b":
            entry["available"] = True
            found = True
    if not found:
        models.append({"model_id": "g9v3:3b", "available": True})
    mp.write_text(json.dumps({"models": models}), encoding="utf-8")
    vol.commit()
    lines.append("MARKED_AVAILABLE")
    lines.append(mp.read_text(encoding="utf-8"))
    return "\n".join(lines)


@app.local_entrypoint()
def main() -> None:
    """Run fix remotely and print result."""
    print(fix_g9v3_manifest.remote())
