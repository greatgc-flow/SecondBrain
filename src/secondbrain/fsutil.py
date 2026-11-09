"""Small filesystem and Markdown primitives; no ledger or command imports."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import unicodedata
from urllib.parse import quote

from .errors import ErrorCode, SbError


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_json_strict(source):
    """Decode a UTF-8 Path, JSON text or bytes, rejecting duplicate object keys."""
    if isinstance(source, Path):
        source = source.read_bytes()
    if isinstance(source, bytes):
        source = source.decode("utf-8")
    def unique(pairs):
        value = {}
        for key, data in pairs:
            require(key not in value, "Duplicate JSON key")
            value[key] = data
        return value
    return json.loads(source, object_pairs_hook=unique)


def resolve_root(path=None):
    return Path(path if path is not None else os.environ.get("SB_ROOT", Path.cwd())).expanduser().resolve()


def write_text(path, text):
    """Write sb-authored UTF-8/LF text; use write_bytes for exact converter/peer bytes."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8", newline="\n")


def write_bytes_atomic(path, data):
    """Preserve exact bytes; flush and fsync the sibling temp before replace."""
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    path.parent.mkdir(parents=True, exist_ok=True)
    with temporary.open("wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def write_json_atomic(path, value):
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=1) + "\n"
    write_bytes_atomic(path, data.encode("utf-8"))


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def is_reparse_point(path):
    try:
        info = Path(path).lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def checked_path(root, target):
    """Require lexical and resolved containment, with no reparse ancestor."""
    root = Path(os.path.abspath(root))
    target = Path(target)
    if not target.is_absolute():
        target = root / target
    if ".." in target.parts:
        raise SbError(ErrorCode.IO_ERROR, 1, "Parent traversal is not allowed")
    try:
        relative = target.relative_to(root)
        target.resolve().relative_to(root.resolve())
    except ValueError as error:
        raise SbError(ErrorCode.IO_ERROR, 1, "Path is outside the root") from error
    current = root
    for part in ("", *relative.parts):
        if part:
            current /= part
        if is_reparse_point(current):
            raise SbError(ErrorCode.IO_ERROR, 1, f"Reparse point refused: {current}")
    return target


def safe_delete(root, target):
    target = checked_path(root, target)
    parts = target.relative_to(Path(os.path.abspath(root))).parts
    allowed = (parts in (("wiki.tmp",), ("wiki.old",))
               or len(parts) == 2 and parts[0] == "work" and re.fullmatch(r"[0-9a-f]{16}", parts[1])
               or len(parts) == 3 and parts[:2] == ("raws", ".staging"))
    if not allowed:
        raise SbError(ErrorCode.IO_ERROR, 1, f"Deletion target refused: {target}")
    if not target.exists():
        return
    if not target.is_dir():
        raise SbError(ErrorCode.IO_ERROR, 1, "Deletion requires a directory")
    # Refuse before any deletion, including links inside an otherwise allowed target.
    for directory, dirs, files in os.walk(target, followlinks=False):
        if any(is_reparse_point(Path(directory) / name) for name in dirs + files):
            raise SbError(ErrorCode.IO_ERROR, 1, "Reparse point inside deletion target")
    def remove_readonly(operation, path, exc_info):
        error = exc_info[1]
        path = checked_path(root, path)
        path.relative_to(target)
        if not isinstance(error, PermissionError) or not (getattr(path.stat(), "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_READONLY):
            raise error
        os.chmod(path, stat.S_IWRITE)
        operation(path)
    try:
        shutil.rmtree(target, onerror=remove_readonly)
    except OSError as error:
        raise SbError(ErrorCode.IO_ERROR, 1, str(error)) from error


def check_path_length(path):
    if len(str(path)) > 240:
        raise SbError(ErrorCode.PATH_TOO_LONG, 1, "Planned source path exceeds 240 characters")


def esc(value):
    result = []
    for char in value:
        if unicodedata.category(char) == "Cc":
            result.append(" ")
        elif char == "<":
            result.append("&lt;")
        elif char == "`":
            result.append("'")
        else:
            result.append(("\\" if char in "\\[]()|*_#!" else "") + char)
    return "".join(result)


def percent_encode(filename):
    return quote(filename, safe="")


