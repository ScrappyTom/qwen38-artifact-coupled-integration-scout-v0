from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from reactive_runtime.canonical import load_json, sha256_file, write_json


def tree_manifest(
    root: Path,
    *,
    exclude_relative_paths: Iterable[str] = (),
) -> dict[str, Any]:
    root = root.resolve()
    excluded = {Path(item).as_posix() for item in exclude_relative_paths}
    rows: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        if path.is_symlink():
            raise ValueError(f"seal root contains symlink: {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative in excluded or ".git" in Path(relative).parts:
            continue
        rows.append(
            {
                "path": relative,
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
        )
    return {
        "file_count": len(rows),
        "files": rows,
        "schema": "ceiba-exact-tree-seal-v1",
        "total_bytes": sum(row["size_bytes"] for row in rows),
    }


def seal_tree(root: Path, manifest_path: Path) -> dict[str, Any]:
    root = root.resolve()
    manifest_path = manifest_path.resolve()
    try:
        relative_manifest = manifest_path.relative_to(root).as_posix()
    except ValueError as exc:
        raise ValueError("seal manifest must be inside sealed root") from exc
    manifest = tree_manifest(root, exclude_relative_paths=(relative_manifest,))
    manifest["manifest_path"] = relative_manifest
    write_json(manifest_path, manifest)
    return manifest


def verify_tree_seal(root: Path, manifest_path: Path) -> tuple[str, ...]:
    root = root.resolve()
    manifest_path = manifest_path.resolve()
    manifest = load_json(manifest_path)
    declared_rows = manifest.get("files")
    if not isinstance(declared_rows, list):
        return ("seal manifest lacks files list",)
    errors: list[str] = []
    try:
        relative_manifest = manifest_path.relative_to(root).as_posix()
    except ValueError:
        return ("seal manifest is outside sealed root",)
    observed = tree_manifest(root, exclude_relative_paths=(relative_manifest,))
    if observed["files"] != declared_rows:
        declared = {row.get("path"): row for row in declared_rows if isinstance(row, dict)}
        current = {row["path"]: row for row in observed["files"]}
        for path in sorted(set(declared) | set(current)):
            if declared.get(path) != current.get(path):
                errors.append(f"sealed file mismatch: {path}")
    if manifest.get("file_count") != observed["file_count"]:
        errors.append("seal file_count mismatch")
    if manifest.get("total_bytes") != observed["total_bytes"]:
        errors.append("seal total_bytes mismatch")
    return tuple(errors)
