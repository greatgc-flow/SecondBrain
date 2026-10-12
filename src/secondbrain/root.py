"""Root management, validation, and layout bootstrapping."""

from __future__ import annotations

import ctypes
import json
import os
import sys
from pathlib import Path
from typing import Any

from secondbrain.errors import IntegrityError, RootRefusedError

DEFAULT_ROOT: str = r"D:\SecondBrain"
CLOUD_SYNC_NAMES: tuple[str, ...] = (
    "onedrive",
    "google drive",
    "googledrive",
    "dropbox",
    "icloud",
    "iclouddrive",
    "nextcloud",
    "box",
    "box sync",
    "owncloud",
)


def resolve_root(cli_root: str | None = None) -> Path:
    """Resolve the active root path following precedence: --root > SB_ROOT > default D:\\SecondBrain."""
    if cli_root:
        return Path(cli_root)
    env_root = os.environ.get("SB_ROOT")
    if env_root:
        return Path(env_root)
    return Path(DEFAULT_ROOT)


def is_cloud_synced_path(path: Path) -> tuple[bool, str]:
    """Check if the given path appears to reside in a known cloud sync location.

    Uses path-component / ancestor matching (not substring matching) and known sync folder names.
    Ordinary junctions are not classified as cloud sync. Detection is best effort.
    """
    resolved = path.resolve()
    parts = [p.lower() for p in resolved.parts]

    # Check path components against known sync names (exact component or sync prefix)
    for part in parts:
        for name in CLOUD_SYNC_NAMES:
            if part == name or part.startswith((name + " ", name + " -", name + " (")):
                return True, f"path component '{part}' matches sync location '{name}'"

    # Check environment variables commonly pointing to sync directories (ancestor matching)
    env_vars = ("OneDrive", "OneDriveConsumer", "OneDriveCommercial", "GoogleDriveFS")
    for var in env_vars:
        val = os.environ.get(var)
        if val:
            val_path = Path(val).resolve()
            if val_path in resolved.parents or val_path == resolved:
                return True, f"located under {var} ({val})"

    # On Windows, check file attributes for specific cloud storage flags (do NOT classify ordinary junctions)
    if sys.platform == "win32" and path.exists():
        try:
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
            # FILE_ATTRIBUTE_PINNED (0x80000)
            # FILE_ATTRIBUTE_UNPINNED (0x100000)
            # FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS (0x400000)
            # FILE_ATTRIBUTE_RECALL_ON_OPEN (0x40000)
            if attrs != -1 and (attrs & 0x5C0000):
                return True, "cloud storage attributes detected"
        except Exception:
            pass

    return False, ""


def check_uncertain_sync(path: Path) -> str | None:
    """Check if an accepted root might potentially be cloud synced (uncertain)."""
    resolved = path.resolve()
    for part in resolved.parts:
        part_lower = part.lower()
        for kw in ("sync", "cloud"):
            if kw in part_lower and part_lower not in CLOUD_SYNC_NAMES:
                return f"path component '{part}' contains keyword '{kw}'"
    return None


def get_filesystem_type(path: Path) -> str | None:
    """Return filesystem type on Windows (e.g. 'NTFS') or None on other platforms."""
    if sys.platform != "win32":
        return None

    try:
        drive = os.path.splitdrive(os.path.abspath(path))[0]
        if not drive:
            return None
        volume_root = drive + "\\"
        fs_name_buf = ctypes.create_unicode_buffer(261)
        res = ctypes.windll.kernel32.GetVolumeInformationW(
            ctypes.c_wchar_p(volume_root),
            None,
            0,
            None,
            None,
            None,
            fs_name_buf,
            260,
        )
        if res:
            return fs_name_buf.value
    except Exception:
        pass
    return None


def is_remote_drive(path: Path) -> bool:
    """Check if drive is a remote/network drive on Windows."""
    if sys.platform != "win32":
        return False

    try:
        drive = os.path.splitdrive(os.path.abspath(path))[0]
        if not drive:
            return False
        volume_root = drive + "\\"
        drive_type = ctypes.windll.kernel32.GetDriveTypeW(ctypes.c_wchar_p(volume_root))
        # DRIVE_REMOTE = 4
        return drive_type == 4
    except Exception:
        return False


def validate_root(root: Path) -> None:
    """Validate active root per ADR 0002. Refuses cloud-synced or non-NTFS roots on Windows.

    Detection is best-effort (warn, don't fight). Warns also on accepted roots when uncertain.
    """
    is_synced, sync_reason = is_cloud_synced_path(root)
    if is_synced:
        raise RootRefusedError(
            f"Warning (ADR 0002): Refusing root '{root}'. "
            f"Active Windows root must live on local NTFS outside sync folders ({sync_reason}). "
            "Detection is best-effort (warn, don't fight)."
        )

    if sys.platform == "win32":
        if is_remote_drive(root):
            raise RootRefusedError(
                f"Warning (ADR 0002): Refusing root '{root}'. "
                "Active Windows root must live on local NTFS outside network drives. "
                "Detection is best-effort (warn, don't fight)."
            )

        fs_type = get_filesystem_type(root)
        if fs_type and fs_type.upper() != "NTFS":
            raise RootRefusedError(
                f"Warning (ADR 0002): Refusing root '{root}'. "
                f"Active Windows root must live on local NTFS (detected filesystem: '{fs_type}'). "
                "Detection is best-effort (warn, don't fight)."
            )

    uncertain_reason = check_uncertain_sync(root)
    if uncertain_reason:
        import warnings

        warnings.warn(
            f"ADR 0002 note: Detection is best-effort. Root '{root}' accepted, but {uncertain_reason}.",
            UserWarning,
            stacklevel=2,
        )


def load_config(root: Path) -> dict[str, Any]:
    """Load and validate config.json on read. Truncated/corrupt config raises IntegrityError with recovery hint."""
    config_path = root / "config.json"
    if not config_path.is_file():
        return {}
    try:
        content = config_path.read_text(encoding="utf-8")
        if not content.strip():
            raise ValueError("config file is empty or truncated")
        data = json.loads(content)
        if not isinstance(data, dict):
            raise ValueError("config root must be a JSON object")
        return data
    except Exception as exc:
        raise IntegrityError(
            f"Corrupt or truncated config at '{config_path}': {exc}. "
            "Recovery hint: restore config.json from backup or delete it to allow re-initialization."
        ) from exc


def bootstrap_root(root: Path) -> None:
    """Create directory layout and config.json atomically if not present, validate on read, and clean temp files."""
    from secondbrain.publish import atomic_publish_bytes, cleanup_temp_files

    root.mkdir(parents=True, exist_ok=True)
    (root / "objects").mkdir(parents=True, exist_ok=True)
    (root / "receipts" / "v1").mkdir(parents=True, exist_ok=True)

    config_path = root / "config.json"
    if not config_path.is_file():
        default_config = {"backup_root": None}
        content = (json.dumps(default_config, indent=2) + "\n").encode("utf-8")
        atomic_publish_bytes(config_path, content)
    else:
        load_config(root)

    cleanup_temp_files(root)

