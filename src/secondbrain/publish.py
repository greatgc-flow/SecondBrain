"""Atomic publication utilities with Windows retry/backoff and temp cleanup."""

from __future__ import annotations

import os
import time
import uuid
from pathlib import Path
from typing import Callable, TypeVar

T = TypeVar("T")


TOOL_TEMP_PREFIXES: tuple[str, ...] = (".sb-tmp-", ".sb_tmp_")


def is_tool_temp_file(path: Path) -> bool:
    """Check if a path is a tool-owned temporary file."""
    name = path.name
    if name.startswith(TOOL_TEMP_PREFIXES) and name.endswith(".tmp"):
        return True
    if ".sb-tmp" in path.parts and name.endswith(".tmp"):
        return True
    return False


def make_temp_path(dst: Path) -> Path:
    """Generate a tool-owned temp path on the target directory/volume."""
    return dst.parent / f".sb-tmp-{dst.name}-{os.getpid()}-{uuid.uuid4().hex[:8]}.tmp"


def retry_sharing_violation(
    operation: Callable[[], T],
    max_retries: int = 10,
    initial_delay: float = 0.02,
    backoff_factor: float = 2.0,
) -> T:
    """Retry an IO operation only on transient Windows sharing violations."""
    if max_retries < 1:
        raise ValueError("max_retries must be at least 1")
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            return operation()
        except OSError as exc:
            if getattr(exc, "winerror", None) == 32:  # ERROR_SHARING_VIOLATION
                if attempt == max_retries - 1:
                    raise
                time.sleep(delay)
                delay *= backoff_factor
            else:
                raise


def retry_open_read(
    path: Path,
    max_retries: int = 10,
    initial_delay: float = 0.02,
    backoff_factor: float = 2.0,
):
    """Open a file for reading with retry/backoff on transient Windows sharing violations."""
    return retry_sharing_violation(
        lambda: open(path, "rb"), max_retries, initial_delay, backoff_factor
    )


def atomic_replace(
    src: Path,
    dst: Path,
    max_retries: int = 10,
    initial_delay: float = 0.02,
    backoff_factor: float = 2.0,
) -> None:
    """Perform atomic replace with exponential retry/backoff on Windows sharing violations."""
    retry_sharing_violation(
        lambda: os.replace(src, dst), max_retries, initial_delay, backoff_factor
    )


def atomic_publish_bytes(dst: Path, data: bytes) -> Path:
    """Atomically publish byte data to dst via a temp file on the target volume."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = make_temp_path(dst)
    with open(tmp_path, "wb") as fp:
        fp.write(data)
        fp.flush()
        os.fsync(fp.fileno())

    atomic_replace(tmp_path, dst)
    return dst


def atomic_publish_file(src: Path, dst: Path, chunk_size: int = 65536) -> Path:
    """Atomically publish src file contents to dst via a temp file on the target volume."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = make_temp_path(dst)
    with retry_open_read(src) as in_fp, open(tmp_path, "wb") as out_fp:
        while chunk := in_fp.read(chunk_size):
            out_fp.write(chunk)
        out_fp.flush()
        os.fsync(out_fp.fileno())

    atomic_replace(tmp_path, dst)
    return dst


def cleanup_temp_files(root: Path) -> int:
    """Safely remove only tool-owned leftover .tmp files from prior interrupted runs."""
    count = 0
    if not root.exists():
        return count

    for path in root.rglob("*.tmp"):
        if path.is_file() and is_tool_temp_file(path):
            try:
                path.unlink()
                count += 1
            except OSError:
                pass
    return count

