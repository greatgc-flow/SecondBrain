"""Open command implementation: tamper verification, disposable working copy, viewer launch.

Security Architecture & Pathname Race Documentation:
-----------------------------------------------------
1. Verification & Copy:
   - The source object is opened with sharing-violation retries.
   - We verify the source hash and stream chunks directly from the verified open handle
     into an exclusively created destination working file (O_CREAT | O_EXCL), hashing
     the transferred bytes during the copy.
   - The destination is flushed and fsynced.
   - The finished destination copy on disk is independently re-hashed before launch.

2. Reparse Point & Boundary Defense:
   - All cache directories and ancestor paths under <root>/cache/open/<id> are inspected
     to reject symlinks and Windows reparse points (junctions).
   - Resolved canonical containment is strictly enforced.
   - Working copy leaf paths that are symlinks or junctions are rejected with IntegrityError.
   - The finished working copy is made read-only (os.chmod / FILE_ATTRIBUTE_READONLY) prior to launch as a convenience marker, not a security boundary.

3. Executable File Association Defense:
   - Refuses to launch dangerous executable or script associations (.exe, .bat, .cmd, .ps1,
     .lnk, etc.) unless --force-launch is explicitly provided.
   - --print-path always succeeds for safe headless inspection without launching.

4. Remaining Pathname Races:
   While the source handle is held during verification and copy, and the destination copy
   hash is verified before launch, there is an inherent race on multitasking operating systems
   between closing the destination write handle / verifying the copy and the external viewer
   launching (via os.startfile or xdg-open/open subprocess). A malicious concurrent process
   with write access to the user's filesystem could attempt to replace the file or directory
   at that exact instant. We minimize this surface by scoping working copies exclusively
   under <root>/cache/open/<receipt_id>/ and making the destination file read-only.
"""

from __future__ import annotations

import hashlib
import os
import stat
import sys
import unicodedata
from pathlib import Path
from typing import Any

import uuid

from secondbrain.errors import IntegrityError, UsageIOError
from secondbrain.publish import (
    retry_open_read,
    retry_sharing_violation,
)
from secondbrain.receipt import (
    HEX64_PATTERN,
    RECEIPT_ID_PATTERN,
    is_reparse_point,
    load_and_validate_receipt,
    validate_receipt_id,
)
from secondbrain.root import validate_root

WINDOWS_RESERVED = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}

EXECUTABLE_EXTENSIONS = {
    "exe",
    "com",
    "bat",
    "cmd",
    "ps1",
    "psm1",
    "vbs",
    "vbe",
    "js",
    "jse",
    "wsf",
    "wsh",
    "msi",
    "msp",
    "scr",
    "lnk",
    "url",
    "hta",
    "cpl",
    "jar",
    "reg",
    "inf",
    "application",
    "gadget",
}
EXECUTABLE_EXTENSIONS.update(f".{x}" for x in list(EXECUTABLE_EXTENSIONS))

ALLOWED_VIEWER_EXTENSIONS = {
    "txt",
    "md",
    "pdf",
    "png",
    "jpg",
    "jpeg",
    "gif",
    "webp",
    "bmp",
    "tif",
    "tiff",
    "svg",
    "csv",
    "json",
    "log",
    "html",
    "htm",
    "eml",
    "docx",
    "xlsx",
    "pptx",
    "mp3",
    "mp4",
    "m4a",
    "wav",
    "mov",
    "mkv",
    "webm",
}
ALLOWED_VIEWER_EXTENSIONS.update(f".{x}" for x in list(ALLOWED_VIEWER_EXTENSIONS))

# Hook between destination copy and finished hash check for testing
_test_hook_after_copy: Any = None


def get_final_extension(name: str) -> str:
    """Extract normalised final extension after stripping trailing dots/spaces.

    Uses name.rsplit('.', 1)[-1] semantics where names like '.exe' count.
    """
    cleaned = name.rstrip(". ").lower()
    if "." in cleaned:
        return cleaned.rsplit(".", 1)[-1]
    return ""


def set_read_only(path: Path) -> None:
    """Set path read-only (os.chmod / FILE_ATTRIBUTE_READONLY). Convenience marker, not a security boundary."""
    try:
        os.chmod(path, stat.S_IREAD)
    except OSError:
        pass
    if sys.platform == "win32":
        try:
            import ctypes

            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
            if attrs != -1 and not (attrs & 0x1):
                ctypes.windll.kernel32.SetFileAttributesW(str(path), attrs | 0x1)
        except Exception:
            pass


def set_writable(path: Path) -> None:
    """Set path writable to allow modification or deletion."""
    try:
        os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
    except OSError:
        pass
    if sys.platform == "win32":
        try:
            import ctypes

            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
            if attrs != -1 and (attrs & 0x1):
                ctypes.windll.kernel32.SetFileAttributesW(str(path), attrs & ~0x1)
        except Exception:
            pass



def to_extended_path(path: Path) -> str:
    """Format an absolute path for Windows extended path length support if needed."""
    s = str(path.resolve())
    if sys.platform == "win32" and not s.startswith("\\\\?\\") and len(s) >= 240:
        if s.startswith("\\\\"):
            return "\\\\?\\UNC\\" + s[2:]
        return "\\\\?\\" + s
    return s


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

    # Truncate length if extreme
    if len(cleaned) > 200:
        base, dot, ext = cleaned.rpartition(".")
        if dot:
            cleaned = base[: 200 - len(ext) - 1] + "." + ext
        else:
            cleaned = cleaned[:200]

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
            return load_and_validate_receipt(exact_file)

    if len(query) < 8:
        raise UsageIOError(f"ID or SHA-256 prefix must be at least 8 characters: '{query}'")

    if not receipts_dir.is_dir():
        raise UsageIOError(f"Receipt not found matching '{identifier}'")

    matches: list[dict[str, Any]] = []
    try:
        with os.scandir(receipts_dir) as it:
            for entry in it:
                if not entry.name.endswith(".json") or entry.is_dir(follow_symlinks=False):
                    continue
                path = Path(entry.path)
                try:
                    data = load_and_validate_receipt(path)
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


def check_and_prepare_cache_dir(root: Path, receipt_id: str) -> Path:
    """Ensure cache/open directories have no symlinks or reparse points and enforce containment."""
    cache_dir = root / "cache"
    open_dir = cache_dir / "open"

    for d in (root, cache_dir, open_dir):
        if d.exists() and is_reparse_point(d):
            raise IntegrityError(f"Cache ancestor directory is a symlink or reparse point: {d}")

    open_dir.mkdir(parents=True, exist_ok=True)

    # Check resolved containment of open_dir
    resolved_root = Path(os.path.normcase(str(root.resolve())))
    resolved_open = Path(os.path.normcase(str(open_dir.resolve())))
    if resolved_root != resolved_open and resolved_root not in resolved_open.parents:
        raise IntegrityError(f"Open cache directory escapes repository root: {open_dir}")

    working_dir = open_dir / receipt_id
    if working_dir.exists() and is_reparse_point(working_dir):
        raise IntegrityError(f"Working directory is a symlink or reparse point: {working_dir}")

    working_dir.mkdir(parents=True, exist_ok=True)

    resolved_working = Path(os.path.normcase(str(working_dir.resolve())))
    if resolved_open != resolved_working and resolved_open not in resolved_working.parents:
        raise IntegrityError(f"Working directory escapes open cache: {working_dir}")

    return working_dir


def open_item(
    identifier: str,
    root: Path,
    print_path: bool = False,
    force_launch: bool = False,
) -> dict[str, Any]:
    """Verify object hash first, copy to cache/open/<id>/<name>, and launch or print path."""
    validate_root(root)

    # 1. Resolve and strictly validate receipt
    receipt = resolve_receipt(identifier, root)
    receipt_id = receipt["id"].lower()
    sha256 = receipt["sha256"].lower()

    # Enforce syntax on resolved receipt ID
    validate_receipt_id(receipt_id, expected_sha256=sha256)

    # 2. Open source object handle with sharing-violation retries and verify hash FIRST
    object_path = root / "objects" / sha256[:2] / sha256
    if not object_path.is_file():
        raise IntegrityError(f"Object file missing for receipt '{receipt['id']}': {object_path}")
    if is_reparse_point(object_path):
        raise IntegrityError(f"Object file is a symlink or reparse point: {object_path}")

    src_fp = retry_sharing_violation(lambda: retry_open_read(object_path))
    with src_fp:
        # First verify the source bytes from this open handle
        src_hasher = hashlib.sha256()
        src_fp.seek(0)
        while chunk := src_fp.read(65536):
            src_hasher.update(chunk)
        if src_hasher.hexdigest().lower() != sha256:
            raise IntegrityError(
                f"Tamper detected: object {object_path} hash does not match expected {sha256}"
            )

        # 3. Only after source verification succeeds, prepare working directory
        working_dir = check_and_prepare_cache_dir(root, receipt_id)
        raw_name = receipt.get("original_name") or receipt.get("original_name_raw") or "unnamed"
        sanitized_name = sanitize_filename(raw_name)
        working_copy = working_dir / sanitized_name

        # Check that destination leaf is not a reparse point
        if working_copy.exists() and is_reparse_point(working_copy):
            raise IntegrityError(f"Working copy path is a symlink or reparse point: {working_copy}")

        # Check launch policy (executable associations & viewer allow-list)
        if not print_path and not force_launch:
            names_to_check = [sanitized_name, raw_name]
            if ":" in raw_name:
                names_to_check.extend(raw_name.split(":"))
            for n in names_to_check:
                ext = get_final_extension(n)
                if ext in EXECUTABLE_EXTENSIONS:
                    raise UsageIOError(
                        f"Refusing to launch executable file association '{sanitized_name}' (.{ext}) without --force-launch. "
                        f"Use --print-path to inspect safely or --force-launch to override."
                    )
            final_ext = get_final_extension(sanitized_name)
            if final_ext not in ALLOWED_VIEWER_EXTENSIONS:
                raise UsageIOError(
                    f"Refusing to launch unapproved file association '{sanitized_name}' without --force-launch. "
                    f"Use --print-path to inspect safely or --force-launch to override."
                )

        # Rewind source handle to copy bytes
        src_fp.seek(0)

        # Unique staging name in working_dir: write to staging first, atomic replace only after verified
        staging_copy = working_dir / f".sb-stage-{os.getpid()}-{uuid.uuid4().hex}.tmp"
        if staging_copy.exists():
            try:
                staging_copy.unlink()
            except OSError:
                pass

        # Create staging copy exclusively
        open_flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0)
        try:
            dst_fd = os.open(to_extended_path(staging_copy), open_flags)
        except OSError as exc:
            raise UsageIOError(f"Failed to exclusively create staging copy {staging_copy}: {exc}") from exc

        copy_hasher = hashlib.sha256()
        try:
            with open(dst_fd, "wb", closefd=True) as dst_fp:
                while chunk := src_fp.read(65536):
                    copy_hasher.update(chunk)
                    dst_fp.write(chunk)
                dst_fp.flush()
                os.fsync(dst_fp.fileno())
        except Exception:
            try:
                staging_copy.unlink()
            except OSError:
                pass
            raise

    # Test hook between copy and hash check
    if _test_hook_after_copy is not None:
        _test_hook_after_copy(staging_copy)

    # 4. Verify bytes streamed into copy
    if copy_hasher.hexdigest().lower() != sha256:
        try:
            staging_copy.unlink()
        except OSError:
            pass
        raise IntegrityError(
            f"Tamper detected during copy: streamed bytes hash does not match expected {sha256}"
        )

    # 5. Verify finished destination copy on disk before atomic replace and launch
    finished_hasher = hashlib.sha256()
    try:
        with retry_sharing_violation(lambda: retry_open_read(staging_copy)) as check_fp:
            while chunk := check_fp.read(65536):
                finished_hasher.update(chunk)
    except Exception:
        try:
            staging_copy.unlink()
        except OSError:
            pass
        raise

    if finished_hasher.hexdigest().lower() != sha256:
        try:
            staging_copy.unlink()
        except OSError:
            pass
        raise IntegrityError(
            f"Tamper detected: finished working copy on disk does not match expected {sha256}"
        )

    # Protect staging copy identity
    if is_reparse_point(staging_copy):
        try:
            staging_copy.unlink()
        except OSError:
            pass
        raise IntegrityError(f"Staging copy became a reparse point during verification: {staging_copy}")

    # Set staged copy read-only (convenience marker, not a security boundary)
    set_read_only(staging_copy)

    # 6. Now that the new copy exists and is completely verified, atomically replace old copy
    if working_copy.exists():
        if is_reparse_point(working_copy):
            try:
                set_writable(staging_copy)
                staging_copy.unlink()
            except OSError:
                pass
            raise IntegrityError(f"Cannot overwrite reparse point working copy: {working_copy}")
        set_writable(working_copy)

    try:
        os.replace(staging_copy, working_copy)
    except OSError as exc:
        try:
            set_writable(staging_copy)
            staging_copy.unlink()
        except OSError:
            pass
        raise UsageIOError(f"Failed to atomically replace working copy {working_copy}: {exc}") from exc

    # Ensure destination working copy is read-only before launch
    set_read_only(working_copy)

    # Protect destination identity through launch
    if is_reparse_point(working_copy):
        try:
            set_writable(working_copy)
            working_copy.unlink()
        except OSError:
            pass
        raise IntegrityError(f"Working copy became a reparse point during verification: {working_copy}")

    # 7. Launch viewer unless --print-path
    if not print_path:
        launch_viewer(working_copy)

    return {
        "status": "ok",
        "id": receipt["id"],
        "path": str(working_copy),
        "sha256": sha256,
        "opened": not print_path,
    }
