"""Open command implementation: tamper verification, disposable working copy, viewer launch."""

from __future__ import annotations

import json
import os
import shutil
import sys
import unicodedata
from pathlib import Path
from typing import Any

from secondbrain.capture import compute_sha256
from secondbrain.errors import IntegrityError, UsageIOError
from secondbrain.root import validate_root

WINDOWS_RESERVED = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def sanitize_filename(name: str) -> str:
    """Sanitize original name for Windows reserved names, trailing dots, and invalid characters."""
    norm = unicodedata.normalize("NFC", name)
    chars: list[str] = []
    for ch in norm:
        if ch in '<>:"/\\|?*' or ord(ch) < 32:
            chars.append("_")
        else:
            chars.append(ch)
    cleaned = "".join(chars).strip()
    cleaned = cleaned.rstrip(". ")
    if not cleaned:
        cleaned = "unnamed"

    stem = cleaned.split(".", 1)[0]
    if stem.upper() in WINDOWS_RESERVED:
        cleaned = f"_{cleaned}"

    return cleaned


def launch_viewer(path: Path) -> None:
    """Launch the system default viewer for the given file."""
    try:
        if sys.platform == "win32":
            os.startfile(str(path))
        elif sys.platform == "darwin":
            import subprocess

            subprocess.Popen(["open", str(path)])
        else:
            import subprocess

            subprocess.Popen(["xdg-open", str(path)])
    except Exception as exc:
        raise UsageIOError(f"Failed to launch viewer for {path}: {exc}") from exc


def resolve_receipt(identifier: str, root: Path) -> dict[str, Any]:
    """Resolve an identifier (receipt ID or sha256 prefix >= 8 hex) to a single receipt."""
    query = identifier.strip().lower()
    receipts_dir = root / "receipts" / "v1"

    # Direct filename match if it exists
    if receipts_dir.is_dir():
        exact_file = receipts_dir / f"{query}.json"
        if exact_file.is_file():
            try:
                return json.loads(exact_file.read_text(encoding="utf-8"))
            except Exception as exc:
                raise IntegrityError(f"Failed to read receipt file {exact_file}: {exc}") from exc

    if len(query) < 8:
        raise UsageIOError(f"ID or SHA-256 prefix must be at least 8 characters: '{query}'")

    if not receipts_dir.is_dir():
        raise UsageIOError(f"Receipt not found matching '{identifier}'")

    matches: list[dict[str, Any]] = []
    try:
        for path in sorted(receipts_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                rec_id = str(data.get("id", "")).lower()
                rec_sha = str(data.get("sha256", "")).lower()

                if rec_id == query or rec_id.startswith(query) or rec_sha.startswith(query):
                    matches.append(data)
            except Exception:
                continue
    except OSError as exc:
        raise UsageIOError(f"Cannot read receipts directory: {exc}") from exc

    if not matches:
        raise UsageIOError(f"Receipt not found matching '{identifier}'")

    if len(matches) > 1:
        candidates = [str(m.get("id", "unknown")) for m in matches]
        raise UsageIOError(
            f"Ambiguous prefix '{identifier}': multiple candidates found: {', '.join(candidates)}"
        )

    return matches[0]


def open_item(
    identifier: str,
    root: Path,
    print_path: bool = False,
) -> dict[str, Any]:
    """Verify object hash first, copy to cache/open/<id>/<name>, and launch or print path."""
    validate_root(root)

    # 1. Resolve receipt
    receipt = resolve_receipt(identifier, root)
    receipt_id = receipt["id"].lower()
    sha256 = receipt["sha256"].lower()

    # 2. Verify object hash FIRST (tamper detection)
    object_path = root / "objects" / sha256[:2] / sha256
    if not object_path.is_file():
        raise IntegrityError(
            f"Object file missing for receipt '{receipt['id']}': {object_path}"
        )

    actual_sha = compute_sha256(object_path)
    if actual_sha != sha256:
        raise IntegrityError(
            f"Tamper detected: object {object_path} hash {actual_sha} does not match expected {sha256}"
        )

    # 3. Copy to working copy under <root>/cache/open/<id>/<original_name>
    raw_name = receipt.get("original_name") or receipt.get("original_name_raw") or "unnamed"
    sanitized_name = sanitize_filename(raw_name)

    working_dir = root / "cache" / "open" / receipt_id
    working_dir.mkdir(parents=True, exist_ok=True)
    working_copy = working_dir / sanitized_name

    shutil.copyfile(object_path, working_copy)

    # 4. Launch viewer unless --print-path
    if not print_path:
        launch_viewer(working_copy)

    return {
        "status": "ok",
        "id": receipt["id"],
        "path": str(working_copy),
        "sha256": sha256,
        "opened": not print_path,
    }
