"""Small filesystem and Markdown primitives; no ledger or command imports."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import unicodedata
from urllib.parse import quote

from .errors import ErrorCode, SbError


def resolve_root(path=None):
    return Path(path if path is not None else os.environ.get("SB_ROOT", Path.cwd())).expanduser().resolve()


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8", newline="\n")


def write_json_atomic(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    write_text(temporary, json.dumps(value, ensure_ascii=False, sort_keys=True, indent=1) + "\n")
    os.replace(temporary, path)


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def init_utf8_stdio():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


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
    try:
        shutil.rmtree(target)
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


def fenced_block(text, info="text"):
    fence = "`" * max(3, max((len(run) + 1 for run in re.findall(r"`+", text)), default=0))
    return f"{fence}{info}\n{text}" + ("" if text.endswith("\n") else "\n") + fence
