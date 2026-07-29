#!/usr/bin/env python3
"""Fill SPDX SBOM license fields from npm/PyPI registries when sbom-tool leaves NOASSERTION.

Microsoft sbom-tool only populates licenses via ClearlyDefined (-li) or limited metadata
parsing (-pm). Bulk ClearlyDefined fetches often return 524 and leave every package as
NOASSERTION. This post-pass resolves licenses from package registries using each
package's purl, then rewrites licenseDeclared / licenseConcluded in place.

Also writes a Python-side inventory from uv.lock (sbom-tool detects UvLock components
but currently drops them from the emitted SPDX package list).
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Mapping, MutableMapping, Sequence

NOASSERTION: Final = "NOASSERTION"
USER_AGENT: Final = "vecinita-sbom-license-enricher/1.0"
TIMEOUT_SEC: Final = 30
_ALLOWED_HOSTS: Final = frozenset({"registry.npmjs.org", "pypi.org"})

_PURL_RE = re.compile(r"^pkg:(?P<eco>npm|pypi)/(?P<name>.+?)(?:@(?P<version>[^?#]+))?(?:[?#].*)?$")


def _http_json(url: str) -> Mapping[str, object] | None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in _ALLOWED_HOSTS:
        return None
    req = urllib.request.Request(  # noqa: S310
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as resp:  # noqa: S310
            raw = resp.read()
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return None
    try:
        payload: object = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _normalize_spdx(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        if not text or text.upper() == NOASSERTION:
            return None
        # Common non-SPDX shorthand seen on npm / PyPI
        aliases = {
            "MIT/X11": "MIT",
            "Apache 2.0": "Apache-2.0",
            "Apache License 2.0": "Apache-2.0",
            "Apache Software": "Apache-2.0",
            "Apache License, Version 2.0": "Apache-2.0",
            "BSD": "BSD-3-Clause",
            "BSD-like": "BSD-3-Clause",
            "3-Clause BSD License": "BSD-3-Clause",
            "MIT License": "MIT",
            "ISC License": "ISC",
            "PSFL": "PSF-2.0",
            "Python Software Foundation License": "PSF-2.0",
            "LGPL with exceptions": "LGPL-3.0-only",
            "UNLICENSED": "UNLICENSED",
            "SEE LICENSE IN LICENSE": "NOASSERTION",
        }
        if text in aliases:
            return aliases[text]
        # PyPI sometimes returns full license text instead of an SPDX id
        if len(text) > 80:
            lower = text.lower()
            if "mit license" in lower or "permission is hereby granted, free of charge" in lower:
                return "MIT"
            if "apache license" in lower and "version 2.0" in lower:
                return "Apache-2.0"
            if "gnu lesser general public license" in lower:
                return "LGPL-3.0-only"
            return None
        return text
    if isinstance(value, dict):
        typed = value.get("type")
        return _normalize_spdx(typed)
    if isinstance(value, list):
        parts = [_normalize_spdx(item) for item in value]
        clean = [p for p in parts if p and p != NOASSERTION]
        if not clean:
            return None
        if len(clean) == 1:
            return clean[0]
        return " OR ".join(clean)
    return None


def _license_from_npm(name: str, version: str | None) -> str | None:
    # Scoped names need the slash encoded: @scope/pkg -> @scope%2fpkg
    encoded = urllib.parse.quote(name, safe="@")
    if version:
        url = f"https://registry.npmjs.org/{encoded}/{urllib.parse.quote(version)}"
    else:
        url = f"https://registry.npmjs.org/{encoded}"
    data = _http_json(url)
    if data is None:
        return None
    if version:
        return _normalize_spdx(data.get("license") or data.get("licenses"))
    versions = data.get("versions")
    if isinstance(versions, dict) and versions:
        tags = data.get("dist-tags")
        ver: str | None = None
        if isinstance(tags, dict):
            latest_tag = tags.get("latest")
            if isinstance(latest_tag, str):
                ver = latest_tag
        meta_obj = versions.get(ver) if ver else None
        meta = meta_obj if isinstance(meta_obj, dict) else None
        if meta is None:
            first = next(iter(versions.values()), None)
            meta = first if isinstance(first, dict) else None
        if meta is not None:
            return _normalize_spdx(meta.get("license") or meta.get("licenses"))
    return _normalize_spdx(data.get("license") or data.get("licenses"))


def _license_from_pypi(name: str, version: str | None) -> str | None:
    encoded = urllib.parse.quote(name)
    url = (
        f"https://pypi.org/pypi/{encoded}/{version}/json"
        if version
        else f"https://pypi.org/pypi/{encoded}/json"
    )
    data = _http_json(url)
    if data is None:
        return None
    info = data.get("info")
    if not isinstance(info, dict):
        return None
    expr = _normalize_spdx(info.get("license_expression"))
    if expr:
        return expr
    lic = _normalize_spdx(info.get("license"))
    if lic and len(lic) < 80:  # skip full license text dumps
        return lic
    classifiers = info.get("classifiers")
    if isinstance(classifiers, list):
        for item in classifiers:
            if isinstance(item, str) and item.startswith("License :: OSI Approved :: "):
                # Not perfect SPDX, but better than NOASSERTION for inventory
                return _normalize_spdx(
                    item.removeprefix("License :: OSI Approved :: ").removesuffix(" License")
                )
    return None


def _license_from_importlib(name: str) -> str | None:
    try:
        from importlib import metadata
    except ImportError:
        return None
    try:
        md = metadata.metadata(name)
    except metadata.PackageNotFoundError:
        return None
    # PackageMetadata stubs omit Mapping.get; use KeyError-safe lookup.
    raw: object | None
    try:
        raw = md["License-Expression"]
    except KeyError:
        try:
            raw = md["License"]
        except KeyError:
            raw = None
    if not isinstance(raw, str):
        return None
    return _normalize_spdx(raw)


def parse_purl(purl: str) -> tuple[str, str, str | None] | None:
    match = _PURL_RE.match(purl)
    if not match:
        return None
    eco = match.group("eco")
    name = urllib.parse.unquote(match.group("name"))
    version = match.group("version")
    return eco, name, version


def resolve_license(purl: str) -> str | None:
    parsed = parse_purl(purl)
    if parsed is None:
        return None
    eco, name, version = parsed
    if eco == "npm":
        return _license_from_npm(name, version)
    if eco == "pypi":
        return _license_from_importlib(name) or _license_from_pypi(name, version)
    return None


def _package_purl(pkg: Mapping[str, object]) -> str | None:
    refs = pkg.get("externalRefs")
    if not isinstance(refs, list):
        return None
    for ref in refs:
        if not isinstance(ref, dict):
            continue
        if ref.get("referenceType") == "purl":
            locator = ref.get("referenceLocator")
            if isinstance(locator, str):
                return locator
    return None


def enrich_spdx(path: Path, *, workers: int) -> dict[str, int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    packages = data.get("packages")
    if not isinstance(packages, list):
        raise SystemExit(f"no packages[] in {path}")

    targets: list[tuple[int, str]] = []
    for idx, pkg in enumerate(packages):
        if not isinstance(pkg, dict):
            continue
        declared = pkg.get("licenseDeclared")
        concluded = pkg.get("licenseConcluded")
        if declared not in (None, NOASSERTION) and concluded not in (None, NOASSERTION):
            continue
        purl = _package_purl(pkg)
        if purl:
            targets.append((idx, purl))

    resolved: dict[int, str] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        future_map = {pool.submit(resolve_license, purl): idx for idx, purl in targets}
        for fut in concurrent.futures.as_completed(future_map):
            idx = future_map[fut]
            try:
                lic = fut.result()
            except (RuntimeError, OSError, ValueError, TypeError):
                lic = None
            if lic and lic != NOASSERTION:
                resolved[idx] = lic

    for idx, lic in resolved.items():
        pkg_obj = packages[idx]
        if isinstance(pkg_obj, dict):
            mutable: MutableMapping[str, object] = pkg_obj
            if mutable.get("licenseDeclared") in (None, NOASSERTION):
                mutable["licenseDeclared"] = lic
            if mutable.get("licenseConcluded") in (None, NOASSERTION):
                mutable["licenseConcluded"] = lic

    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    concluded = Counter(
        str(pkg.get("licenseConcluded") or NOASSERTION) for pkg in packages if isinstance(pkg, dict)
    )
    return {
        "packages": len(packages),
        "targets": len(targets),
        "resolved": len(resolved),
        "still_noassertion": int(concluded.get(NOASSERTION, 0)),
    }


def _parse_uv_lock(lock_path: Path) -> list[tuple[str, str]]:
    """Minimal uv.lock TOML package name/version extractor (no tomllib dependency gymnastics)."""
    text = lock_path.read_text(encoding="utf-8")
    packages: list[tuple[str, str]] = []
    name: str | None = None
    version: str | None = None
    in_package = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "[[package]]":
            if name and version:
                packages.append((name, version))
            name, version, in_package = None, None, True
            continue
        if not in_package:
            continue
        if stripped.startswith("["):
            if name and version:
                packages.append((name, version))
            name, version, in_package = None, None, False
            continue
        if stripped.startswith("name = "):
            name = stripped.split("=", 1)[1].strip().strip('"')
        elif stripped.startswith("version = "):
            version = stripped.split("=", 1)[1].strip().strip('"')
    if name and version:
        packages.append((name, version))
    return packages


def inventory_uv_lock(lock_path: Path, out_path: Path, *, workers: int) -> dict[str, int]:
    pkgs = _parse_uv_lock(lock_path)
    rows: list[dict[str, str | None]] = []

    def one(item: tuple[str, str]) -> dict[str, str | None]:
        name, version = item
        lic = _license_from_importlib(name) or _license_from_pypi(name, version)
        return {
            "name": name,
            "version": version,
            "purl": f"pkg:pypi/{urllib.parse.quote(name)}@{version}",
            "license": lic,
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        rows = list(pool.map(one, pkgs))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"packages": rows}, indent=2) + "\n", encoding="utf-8")
    unknown = sum(1 for row in rows if not row.get("license"))
    return {"packages": len(rows), "resolved": len(rows) - unknown, "unknown": unknown}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spdx", type=Path, help="Path to manifest.spdx.json")
    parser.add_argument("--uv-lock", type=Path, help="Path to uv.lock for Python inventory")
    parser.add_argument(
        "--uv-out",
        type=Path,
        default=None,
        help="Output path for Python license inventory JSON",
    )
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--summary", type=Path, help="Write enrichment summary JSON")
    args = parser.parse_args(argv)

    summary: dict[str, object] = {}
    if args.spdx:
        spdx_stats = enrich_spdx(args.spdx, workers=args.workers)
        summary["spdx"] = spdx_stats
        print(
            f"[enrich-sbom] spdx packages={spdx_stats['packages']} "
            f"resolved={spdx_stats['resolved']} "
            f"still_noassertion={spdx_stats['still_noassertion']}",
            file=sys.stderr,
        )
    if args.uv_lock:
        uv_out = args.uv_out or (
            args.spdx.parent / "python-licenses.json" if args.spdx else Path("python-licenses.json")
        )
        uv_stats = inventory_uv_lock(args.uv_lock, uv_out, workers=args.workers)
        summary["uv"] = uv_stats
        print(
            f"[enrich-sbom] uv.lock packages={uv_stats['packages']} "
            f"resolved={uv_stats['resolved']} unknown={uv_stats['unknown']} -> {uv_out}",
            file=sys.stderr,
        )
    if args.summary:
        args.summary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if not args.spdx and not args.uv_lock:
        parser.error("provide --spdx and/or --uv-lock")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
