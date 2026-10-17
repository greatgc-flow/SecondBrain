"""Atomic publication utilities with Windows retry/backoff, no-clobber primitives, and temp cleanup."""

from __future__ import annotations

import hashlib
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Callable, TypeVar

from secondbrain.errors import IntegrityError

T = TypeVar("T")

TOOL_TEMP_PREFIXES: tuple[str, ...] = (".sb-tmp-", ".sb_tmp_")


def compute_file_sha256(path: Path) -> str:
    """Compute lowercase SHA-256 hex digest of a file."""
    hasher = hashlib.sha256()
    with open(path, "rb") as fp:
        while chunk := fp.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest().lower()


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


def publish_no_clobber(src_temp: Path, dst: Path, expected_sha: str) -> None:
    """Publish src_temp to dst using a no-clobber primitive.

    On collision: compare hashes. Identical = fine; different = error exit 1 naming the file.
    """
    dst.parent.mkdir(parents=True, exist_ok=True)

    if sys.platform == "win32":
        try:
            # os.rename fails with FileExistsError (winerror 183) on Windows if dst exists
            retry_sharing_violation(lambda: os.rename(str(src_temp), str(dst)))
            return
        except FileExistsError:
            pass
    else:
        try:
            os.link(str(src_temp), str(dst))
            try:
                src_temp.unlink()
            except OSError:
                pass
            return
        except FileExistsError:
            pass

    # Collision detected! Remove the staging temp file
    if src_temp.exists():
        try:
            src_temp.unlink()
        except OSError:
            pass

    # Compare hashes of existing destination file
    dst_sha = compute_file_sha256(dst)
    if dst_sha != expected_sha:
        raise IntegrityError(
            f"Collision on existing file with differing content: {dst} expected {expected_sha} got {dst_sha}"
        )


def stage_and_verify_copy(
    src: Path,
    dst: Path,
    expected_sha: str,
    expected_size: int | None = None,
) -> int:
    """Copy src to dst via tool-owned temp file in dst.parent, close, re-read and hash, then publish no-clobber.

    Sharing-violation retries reset the staging file and hasher state.
    """
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = make_temp_path(dst)

    def _attempt_copy_and_verify() -> int:
        # Reset staging file if it exists from previous retry
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass

        # 1. Stream write to tmp_path
        with retry_open_read(src) as in_fp, open(tmp_path, "wb") as out_fp:
            while chunk := in_fp.read(65536):
                out_fp.write(chunk)
            out_fp.flush()
            os.fsync(out_fp.fileno())

        # 2. Closed! Re-read from disk and compute sha256 and size
        hasher = hashlib.sha256()
        total_size = 0
        with open(tmp_path, "rb") as verify_fp:
            while chunk := verify_fp.read(65536):
                hasher.update(chunk)
                total_size += len(chunk)

        computed_sha = hasher.hexdigest().lower()
        if computed_sha != expected_sha:
            try:
                tmp_path.unlink()
            except OSError:
                pass
            raise IntegrityError(
                f"Corrupted bytes during staging of {src} -> {dst}: expected {expected_sha} got {computed_sha}"
            )
        if expected_size is not None and total_size != expected_size:
            try:
                tmp_path.unlink()
            except OSError:
                pass
            raise IntegrityError(
                f"Size mismatch during staging of {src} -> {dst}: expected {expected_size} got {total_size}"
            )

        return total_size

    try:
        size = retry_sharing_violation(_attempt_copy_and_verify)
        # 3. Publish no-clobber
        publish_no_clobber(tmp_path, dst, expected_sha)
        return size
    except Exception:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        raise


def stage_and_verify_bytes(
    data: bytes,
    dst: Path,
    expected_sha: str | None = None,
) -> tuple[int, str]:
    """Write bytes to dst via tool-owned temp file, close, re-read and hash, then publish no-clobber.

    Sharing-violation retries reset the staging file and hasher state.
    """
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = make_temp_path(dst)

    def _attempt_write_and_verify() -> tuple[int, str]:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass

        with open(tmp_path, "wb") as out_fp:
            out_fp.write(data)
            out_fp.flush()
            os.fsync(out_fp.fileno())

        hasher = hashlib.sha256()
        total_size = 0
        with open(tmp_path, "rb") as verify_fp:
            while chunk := verify_fp.read(65536):
                hasher.update(chunk)
                total_size += len(chunk)

        computed_sha = hasher.hexdigest().lower()
        if expected_sha is not None and computed_sha != expected_sha:
            try:
                tmp_path.unlink()
            except OSError:
                pass
            raise IntegrityError(
                f"Corrupted bytes during staging of {dst}: expected {expected_sha} got {computed_sha}"
            )
        return total_size, computed_sha

    try:
        size, computed_sha = retry_sharing_violation(_attempt_write_and_verify)
        exp_sha = expected_sha if expected_sha is not None else computed_sha
        publish_no_clobber(tmp_path, dst, exp_sha)
        return size, computed_sha
    except Exception:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        raise


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
