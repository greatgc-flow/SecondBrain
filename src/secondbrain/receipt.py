"""Strict receipt validation and parsing shared across SecondBrain."""

from __future__ import annotations

import json
import os
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

from secondbrain.errors import IntegrityError, UsageIOError

HEX64_PATTERN = re.compile(r"^[0-9a-f]{64}$")
# IDs are stateless: cap-<YYYYMMDDtHHMMSSz>-<first 8 hex of sha256> with optional collision suffix -<int>
RECEIPT_ID_PATTERN = re.compile(r"^cap-(\d{8}t\d{6}z)-([0-9a-f]{8})(-\d+)?$")
REQUIRED_RECEIPT_FIELDS = (
    "id",
    "sha256",
    "original_name",
    "source_path",
    "collected_at",
    "tool_version",
)
ALLOWED_RECEIPT_FIELDS = {
    "id",
    "sha256",
    "original_name",
    "original_name_raw",
    "source_path",
    "collected_at",
    "tool_version",
}


def is_reparse_point(path: Path) -> bool:
    """Check if path is a symlink or Windows reparse point (junction)."""
    try:
        if path.is_symlink() or os.path.islink(str(path)):
            return True
        st = os.lstat(str(path))
        file_attrs = getattr(st, "st_file_attributes", 0)
        # FILE_ATTRIBUTE_REPARSE_POINT = 0x400
        if file_attrs & 0x400:
            return True
    except (OSError, ValueError):
        pass
    return False


def validate_receipt_id(receipt_id: str, expected_sha256: str | None = None) -> None:
    """Strictly validate receipt ID syntax, lowercase enforcement, valid timestamp, and hash prefix."""
    if not isinstance(receipt_id, str):
        raise ValueError(f"Receipt ID must be a string, got {type(receipt_id).__name__}")
    if not receipt_id:
        raise ValueError("Receipt ID cannot be empty")
    if receipt_id != receipt_id.lower():
        raise ValueError(f"Receipt ID must be strictly lowercase: '{receipt_id}'")

    match = RECEIPT_ID_PATTERN.match(receipt_id)
    if not match:
        raise ValueError(
            f"Invalid receipt ID format: '{receipt_id}'. Expected cap-<YYYYMMDDtHHMMSSz>-<prefix8>[-suffix]"
        )

    ts_str, prefix_hex, _ = match.groups()
    try:
        # Validate that the timestamp is a valid UTC date and time
        datetime.strptime(ts_str, "%Y%m%dt%H%M%Sz")
    except ValueError as exc:
        raise ValueError(f"Invalid timestamp in receipt ID '{receipt_id}': {exc}") from exc

    if expected_sha256 is not None:
        expected_prefix = expected_sha256[:8].lower()
        if prefix_hex != expected_prefix:
            raise ValueError(
                f"Receipt ID hash prefix '{prefix_hex}' does not match sha256 prefix '{expected_prefix}'"
            )


def validate_receipt_data(data: Any, expected_id: str | None = None) -> dict[str, Any]:
    """Strictly validate parsed receipt dictionary against schema constraints."""
    if not isinstance(data, dict):
        raise ValueError(f"Receipt root must be a JSON object, got {type(data).__name__}")

    for field in REQUIRED_RECEIPT_FIELDS:
        if field not in data:
            raise ValueError(f"Missing required field in receipt: '{field}'")
        if not isinstance(data[field], str):
            raise ValueError(f"Field '{field}' must be a string, got {type(data[field]).__name__}")

    extra_fields = set(data.keys()) - ALLOWED_RECEIPT_FIELDS
    if extra_fields:
        raise ValueError(f"Receipt contains unexpected extra fields: {sorted(extra_fields)}")

    rec_id = data["id"]
    sha256 = data["sha256"]

    if sha256 != sha256.lower() or not HEX64_PATTERN.match(sha256):
        raise ValueError(f"Invalid sha256 in receipt: '{sha256}'. Must be 64 lowercase hex characters.")

    validate_receipt_id(rec_id, expected_sha256=sha256)

    if expected_id is not None:
        if rec_id != expected_id.lower():
            raise ValueError(
                f"Receipt filename/ID mismatch: file indicates '{expected_id}' but content id is '{rec_id}'"
            )

    # Validate collected_at is a valid ISO 8601 timestamp with timezone
    collected_at = data["collected_at"]
    try:
        dt = datetime.fromisoformat(collected_at)
        if dt.tzinfo is None:
            raise ValueError("collected_at must contain timezone offset")
    except Exception as exc:
        raise ValueError(f"Invalid collected_at timestamp '{collected_at}': {exc}") from exc

    orig_name = data["original_name"]
    if not orig_name:
        raise ValueError("original_name cannot be empty")
    if unicodedata.normalize("NFC", orig_name) != orig_name:
        raise ValueError("original_name must be normalized to Unicode NFC")

    if not data["source_path"]:
        raise ValueError("source_path cannot be empty")

    if not data["tool_version"]:
        raise ValueError("tool_version cannot be empty")

    return data


def load_and_validate_receipt(path: Path) -> dict[str, Any]:
    """Load and strictly validate a receipt file from disk."""
    if is_reparse_point(path):
        raise IntegrityError(f"Receipt file is a symlink or reparse point: {path}")

    if not path.is_file():
        raise UsageIOError(f"Receipt file does not exist or is not a regular file: {path}")

    filename = path.name
    if not filename.endswith(".json"):
        raise IntegrityError(f"Receipt filename must end with .json: {filename}")

    expected_id = filename[:-5]
    if expected_id != expected_id.lower():
        raise IntegrityError(f"Receipt filename must be strictly lowercase: {filename}")

    try:
        raw_text = path.read_text(encoding="utf-8")
    except (PermissionError, OSError) as exc:
        raise UsageIOError(f"Cannot read receipt file {path}: {exc}") from exc

    if not raw_text.strip():
        raise IntegrityError(f"Receipt file is empty: {path}")

    try:
        data = json.loads(raw_text)
    except Exception as exc:
        raise IntegrityError(f"Malformed JSON in receipt file {path}: {exc}") from exc

    try:
        return validate_receipt_data(data, expected_id=expected_id)
    except ValueError as exc:
        raise IntegrityError(f"Invalid receipt schema in {path}: {exc}") from exc
