from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(asset_ids: set[str] | None = None) -> dict[str, Any]:
    manifest = json.loads((ROOT / "RUNTIME_ASSET_MANIFEST.json").read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    declared_ids = {str(row["asset_id"]) for row in manifest["assets"]}
    if asset_ids is not None:
        failures.extend(f"undeclared_asset:{value}" for value in sorted(asset_ids - declared_ids))
    for declared in manifest["assets"]:
        if asset_ids is not None and declared["asset_id"] not in asset_ids:
            continue
        path = Path(declared["path"])
        exists = path.is_file()
        observed = sha256_file(path) if exists else None
        passed = exists and observed == declared["sha256"]
        if declared.get("required") is True and not passed:
            failures.append(str(declared["asset_id"]))
        rows.append(
            {
                "asset_id": declared["asset_id"],
                "path": str(path),
                "exists": exists,
                "expected_sha256": declared["sha256"],
                "observed_sha256": observed,
                "passed": passed,
            }
        )
    server_row = next(row for row in manifest["assets"] if row["asset_id"] == "llama_server_cuda")
    server_path = Path(server_row["path"])
    bundle_rows = []
    if server_path.parent.is_dir():
        for path in sorted(server_path.parent.iterdir(), key=lambda item: item.name.casefold()):
            if path.is_file() and path.suffix.casefold() in {".dll", ".exe"}:
                bundle_rows.append(
                    {
                        "name": path.name,
                        "bytes": path.stat().st_size,
                        "sha256": sha256_file(path),
                    }
                )
    if not bundle_rows:
        failures.append("runtime_bundle_empty")
    return {
        "schema_version": "ceiba-runtime-asset-verification-v0",
        "selected_asset_ids": None if asset_ids is None else sorted(asset_ids),
        "assets": rows,
        "runtime_bundle": bundle_rows,
        "passed": not failures,
        "failures": failures,
    }


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2, sort_keys=True))
