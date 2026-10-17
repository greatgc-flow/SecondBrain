"""Search engine and SQLite FTS5 index maintenance for SecondBrain."""

from __future__ import annotations

import email
from email import policy
from html.parser import HTMLParser
import io
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
from typing import Any
import unicodedata

import pypdf

from secondbrain.errors import IntegrityError, UsageIOError
from secondbrain.lock import WriterLock
from secondbrain.root import validate_root

# Extractor and schema versions
EXTRACTOR_VERSION: str = "1.0"
CURRENT_SCHEMA_VERSION: int = 2

# Input and output caps (P1-2, P2)
MAX_TEXT_INPUT_SIZE: int = 32 * 1024 * 1024       # 32 MiB
MAX_PDF_INPUT_SIZE: int = 64 * 1024 * 1024        # 64 MiB
MAX_EML_HTML_INPUT_SIZE: int = 16 * 1024 * 1024   # 16 MiB
MAX_OUTPUT_TEXT_CHARS: int = 2 * 1024 * 1024      # 2 MiB (characters)
MAX_PDF_PAGES: int = 1000
MAX_PDF_STREAM_SIZE: int = 32 * 1024 * 1024       # 32 MiB content stream cap
PDF_TIMEOUT_SECONDS: float = 30.0

TEXT_EXTENSIONS: frozenset[str] = frozenset({".txt", ".md", ".csv", ".json", ".log"})
HTML_EXTENSIONS: frozenset[str] = frozenset({".html", ".htm"})
SUPPORTED_EXTENSIONS: frozenset[str] = (
    TEXT_EXTENSIONS | HTML_EXTENSIONS | frozenset({".pdf", ".eml"})
)


def get_ext_class(filename_or_ext: str) -> str:
    """Return canonical format class for a filename or extension (P1)."""
    ext = Path(filename_or_ext).suffix.lower() if "." in filename_or_ext else filename_or_ext.lower()
    if ext in TEXT_EXTENSIONS:
        return "text"
    if ext in HTML_EXTENSIONS:
        return "html"
    if ext == ".pdf":
        return "pdf"
    if ext == ".eml":
        return "eml"
    return "unsupported"


class HTMLTextExtractor(HTMLParser):
    """Simple HTML parser that strips tags and excludes script/style content."""

    def __init__(self) -> None:
        super().__init__()
        self.text_parts: list[str] = []
        self._ignore: bool = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in ("script", "style", "noscript"):
            self._ignore = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in ("script", "style", "noscript"):
            self._ignore = False

    def handle_data(self, data: str) -> None:
        if not self._ignore:
            cleaned = data.strip()
            if cleaned:
                self.text_parts.append(cleaned)

    def get_text(self) -> str:
        return " ".join(self.text_parts)


def escape_like(s: str) -> str:
    """Escape wildcard characters for SQL LIKE query."""
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def is_link_or_reparse(path: Path) -> bool:
    """Check if path is a symlink, directory junction, or reparse point (P1-1)."""
    try:
        if path.is_symlink():
            return True
        st = os.lstat(path)
        if hasattr(st, "st_file_attributes") and (st.st_file_attributes & 0x0400):
            return True
    except OSError:
        pass
    return False


def is_hardlink(path: Path) -> bool:
    """Check if file has multiple hardlinks (nlink > 1) (P1-1)."""
    try:
        st = os.lstat(path)
        return st.st_nlink > 1
    except OSError:
        return False


def validate_cache_security(cache_dir: Path, db_path: Path | None = None) -> None:
    """Validate that cache/ and index.db are not symlinks, junctions, or hardlinks (P1-1)."""
    if cache_dir.exists():
        if is_link_or_reparse(cache_dir):
            raise UsageIOError(
                f"Refusing write: cache directory '{cache_dir}' is a symlink or reparse point"
            )

    if db_path is not None and db_path.exists():
        if is_link_or_reparse(db_path):
            raise UsageIOError(
                f"Refusing write: index database '{db_path}' is a symlink or reparse point"
            )
        if is_hardlink(db_path):
            raise UsageIOError(
                f"Refusing write: index database '{db_path}' is a hardlink (nlink > 1)"
            )


def decode_text_bytes(data: bytes) -> tuple[str, str | None, str | None]:
    """Decode raw bytes into string using UTF-8/16/CP949 (P2).

    UTF-16 detection heuristics (NUL byte pattern, Hangul byte range, trial decode scoring)
    are evaluated before UTF-8/CP949.
    Returns: (decoded_text, note, error)
    """
    if not data:
        return "", None, None

    # 1. BOM checks
    if data.startswith(b"\xef\xbb\xbf"):
        try:
            return data.decode("utf-8-sig"), None, None
        except UnicodeDecodeError as exc:
            return "", None, f"UTF-8 BOM decode error: {exc}"

    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        try:
            return data.decode("utf-16"), None, None
        except UnicodeDecodeError as exc:
            return "", None, f"UTF-16 BOM decode error: {exc}"

    # 2. BOM-less UTF-16 heuristics and trial decode scoring before UTF-8/CP949 (P2)
    if len(data) >= 2 and len(data) % 2 == 0:
        sample = data[:2048]
        sample_half = len(sample) // 2

        # (a) NUL-byte pattern for ASCII-bearing UTF-16
        odd_nuls = sum(1 for b in sample[1::2] if b == 0)
        even_nuls = sum(1 for b in sample[0::2] if b == 0)

        # (b) Hangul-range heuristics (Hangul syllables U+AC00-D7A3 have high bytes 0xAC..0xD7)
        hangul_hi_le = sum(1 for b in sample[1::2] if 0xAC <= b <= 0xD7)
        hangul_hi_be = sum(1 for b in sample[0::2] if 0xAC <= b <= 0xD7)

        # Helper to trial decode and score
        def _try_score_utf16(enc: str) -> tuple[float, str]:
            try:
                txt = data.decode(enc)
            except (UnicodeDecodeError, ValueError):
                return -1.0, ""
            if "\x00" in txt or any(ord(c) == 0xFFFD for c in txt):
                return -1.0, ""
            if any(0xD800 <= ord(c) <= 0xDFFF for c in txt):
                return -1.0, ""
            total = len(txt)
            if total == 0:
                return -1.0, ""
            hangul = sum(1 for c in txt if 0xAC00 <= ord(c) <= 0xD7A3)
            hangul_jamo = sum(
                1 for c in txt if (0x1100 <= ord(c) <= 0x11FF or 0x3130 <= ord(c) <= 0x318F)
            )
            printable = sum(1 for c in txt if c.isprintable() or c in "\r\n\t ")
            p_ratio = printable / total
            if p_ratio < 0.8:
                return -1.0, ""
            h_ratio = (hangul + hangul_jamo) / total
            score = p_ratio + h_ratio * 3.0
            return score, txt

        le_score, le_txt = _try_score_utf16("utf-16-le")
        be_score, be_txt = _try_score_utf16("utf-16-be")

        # NUL byte dominance
        if odd_nuls >= max(2, sample_half // 3) and even_nuls == 0 and le_score > 0:
            return le_txt, "low_confidence_encoding: bomless_utf16_le", None
        if even_nuls >= max(2, sample_half // 3) and odd_nuls == 0 and be_score > 0:
            return be_txt, "low_confidence_encoding: bomless_utf16_be", None

        # Korean-only / Hangul-range heuristics and trial decode scoring
        # When high bytes fall in 0xAC..0xD7 or trial decode yields Hangul syllables
        if hangul_hi_le > hangul_hi_be and le_score >= 1.5:
            return le_txt, "low_confidence_encoding: bomless_utf16_le", None
        elif hangul_hi_be > hangul_hi_le and be_score >= 1.5:
            # Ensure not space-less CP949: CP949 EUC-KR bytes are all >= 0xA1,
            # whereas UTF-16 BE for Korean text has low bytes < 0xA1
            if any(b < 0xA1 for b in data) or b"\x00" in data:
                return be_txt, "low_confidence_encoding: bomless_utf16_be", None
        elif le_score >= 2.0 and le_score >= be_score:
            return le_txt, "low_confidence_encoding: bomless_utf16_le", None
        elif be_score >= 2.0 and (any(b < 0xA1 for b in data) or b"\x00" in data):
            return be_txt, "low_confidence_encoding: bomless_utf16_be", None

    # 3. Strict UTF-8 (only when no stray NUL bytes in data)
    if b"\x00" not in data:
        try:
            return data.decode("utf-8"), None, None
        except UnicodeDecodeError:
            pass

    # 4. Fallback to CP949
    if b"\x00" not in data:
        try:
            txt = data.decode("cp949")
            return txt, "low_confidence_encoding: cp949", None
        except UnicodeDecodeError:
            pass

    # 5. Last resort BOM-less UTF-16 if even length and contains null bytes
    if len(data) % 2 == 0 and b"\x00" in data:
        try:
            txt = data.decode("utf-16")
            if txt and not any(ord(c) == 0xFFFD for c in txt):
                return txt, "low_confidence_encoding: bomless_utf16", None
        except UnicodeDecodeError:
            pass

    return "", None, "Failed to decode bytes using UTF-8, UTF-16, or CP949"


def _pdf_worker_main(
    pdf_path_str: str,
    max_pages: int,
    output_cap: int,
    max_stream_size: int = MAX_PDF_STREAM_SIZE,
) -> int:
    """Worker process for isolated PDF extraction (P1-2, P2)."""
    try:
        pdf_path = Path(pdf_path_str)
        reader = pypdf.PdfReader(pdf_path)
        if getattr(reader, "is_encrypted", False):
            out = {"status": "failed", "error": "PDF is encrypted / password protected"}
            sys.stdout.write(json.dumps(out))
            return 0

        page_count = len(reader.pages)
        if page_count > max_pages:
            out = {
                "status": "failed",
                "error": f"PDF page count ({page_count}) exceeds limit of {max_pages} pages",
            }
            sys.stdout.write(json.dumps(out))
            return 0

        parts: list[str] = []
        total_chars = 0
        total_stream_bytes = 0

        for i in range(page_count):
            page = reader.pages[i]
            # Enforce stream size cap
            try:
                contents = page.get_contents()
                if contents is not None:
                    data = contents.get_data() if hasattr(contents, "get_data") else None
                    if data:
                        total_stream_bytes += len(data)
                        if len(data) > max_stream_size or total_stream_bytes > max_stream_size:
                            out = {
                                "status": "failed",
                                "error": f"PDF content stream size exceeds limit of {max_stream_size} bytes",
                            }
                            sys.stdout.write(json.dumps(out))
                            return 0
            except Exception:
                pass

            t = page.extract_text()
            if t and t.strip():
                stripped = t.strip()
                parts.append(stripped)
                total_chars += len(stripped)
                if total_chars >= output_cap:
                    break

        combined = "\n".join(parts).strip()
        if combined:
            if len(combined) > output_cap:
                combined = combined[:output_cap]
            out = {"status": "ok", "text": unicodedata.normalize("NFC", combined)}
        else:
            out = {"status": "no_text", "text": ""}
        sys.stdout.write(json.dumps(out))
        return 0
    except Exception as exc:
        out = {"status": "failed", "error": f"PDF extraction failed: {exc}"}
        sys.stdout.write(json.dumps(out))
        return 0


def extract_pdf_subprocess(object_path: Path) -> tuple[str, str, str | None]:
    """Extract text from PDF using isolated worker process with timeout (P1-2, P2)."""
    repo_src = str(Path(__file__).resolve().parent.parent)
    env = os.environ.copy()
    env["PYTHONPATH"] = repo_src + (
        os.pathsep + env["PYTHONPATH"] if "PYTHONPATH" in env else ""
    )

    cmd = [
        sys.executable,
        "-m",
        "secondbrain.search",
        "--extract-pdf-worker",
        str(object_path),
        str(MAX_PDF_PAGES),
        str(MAX_OUTPUT_TEXT_CHARS),
        str(MAX_PDF_STREAM_SIZE),
    ]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=PDF_TIMEOUT_SECONDS,
            env=env,
        )
        if proc.returncode != 0:
            return (
                "",
                "failed",
                f"PDF worker crashed (code {proc.returncode}): {proc.stderr.strip()}",
            )

        out_text = proc.stdout.strip()
        if not out_text:
            return "", "failed", "PDF worker produced empty output"

        data = json.loads(out_text)
        status = data.get("status", "failed")
        if status == "ok":
            return data.get("text", ""), "ok", None
        elif status == "no_text":
            return "", "no_text", None
        else:
            return "", "failed", data.get("error", "PDF extraction failed")
    except subprocess.TimeoutExpired:
        return "", "failed", f"PDF extraction timed out ({PDF_TIMEOUT_SECONDS} s limit)"
    except Exception as exc:
        return "", "failed", f"PDF worker execution failed: {exc}"


def extract_object_text(
    object_path: Path, filename: str
) -> tuple[str, str, str | None, str | None]:
    """Extract text from an object file based on filename extension (P1-2, P2).

    Unsupported formats never have their payloads read. Input size caps and output
    text limits are enforced.

    Returns:
        (extracted_text, status, extraction_note, extraction_error)
        status: 'ok', 'no_text', 'ok_with_warnings', or 'failed'
    """
    ext = Path(filename).suffix.lower()

    # 1. P1-2: Never read unsupported formats' payloads!
    if ext not in SUPPORTED_EXTENSIONS:
        return "", "no_text", None, None

    if not object_path.is_file():
        return "", "failed", None, f"Object file not found: {object_path}"

    try:
        st_size = object_path.stat().st_size
    except OSError as exc:
        return "", "failed", None, f"Cannot stat object file: {exc}"

    # 2. Input size caps (P1-2)
    if ext in TEXT_EXTENSIONS and st_size > MAX_TEXT_INPUT_SIZE:
        return (
            "",
            "failed",
            None,
            f"File size ({st_size} bytes) exceeds limit of {MAX_TEXT_INPUT_SIZE} bytes",
        )
    elif ext == ".pdf" and st_size > MAX_PDF_INPUT_SIZE:
        return (
            "",
            "failed",
            None,
            f"File size ({st_size} bytes) exceeds limit of {MAX_PDF_INPUT_SIZE} bytes",
        )
    elif (
        ext in HTML_EXTENSIONS or ext == ".eml"
    ) and st_size > MAX_EML_HTML_INPUT_SIZE:
        return (
            "",
            "failed",
            None,
            f"File size ({st_size} bytes) exceeds limit of {MAX_EML_HTML_INPUT_SIZE} bytes",
        )

    # 3. PDF format via isolated worker
    if ext == ".pdf":
        text, status, err = extract_pdf_subprocess(object_path)
        return text, status, None, err

    # Read bytes for text/html/eml
    try:
        raw_bytes = object_path.read_bytes()
    except OSError as exc:
        return "", "failed", None, f"Cannot read object file: {exc}"

    # Plain text formats
    if ext in TEXT_EXTENSIONS:
        decoded, note, err = decode_text_bytes(raw_bytes)
        if err:
            return "", "failed", None, err
        norm = unicodedata.normalize("NFC", decoded.strip())
        if norm:
            if len(norm) > MAX_OUTPUT_TEXT_CHARS:
                norm = norm[:MAX_OUTPUT_TEXT_CHARS]
            return norm, "ok", note, None
        return "", "no_text", note, None

    # HTML format
    if ext in HTML_EXTENSIONS:
        decoded, note, err = decode_text_bytes(raw_bytes)
        if err:
            return "", "failed", None, err
        try:
            parser = HTMLTextExtractor()
            parser.feed(decoded)
            stripped = parser.get_text().strip()
            if stripped:
                norm = unicodedata.normalize("NFC", stripped)
                if len(norm) > MAX_OUTPUT_TEXT_CHARS:
                    norm = norm[:MAX_OUTPUT_TEXT_CHARS]
                return norm, "ok", note, None
            return "", "no_text", note, None
        except Exception as exc:
            return "", "failed", None, f"HTML extraction failed: {exc}"

    # EML format (P2: bad charset -> ok_with_warnings or failed)
    if ext == ".eml":
        try:
            msg = email.message_from_bytes(raw_bytes, policy=policy.default)
            parts: list[str] = []
            charset_warnings: list[str] = []
            for h in ("Subject", "From", "To", "Cc", "Date"):
                val = msg.get(h)
                if val:
                    parts.append(f"{h}: {val}")

            for part in msg.walk():
                ctype = part.get_content_type()
                if ctype == "text/plain":
                    try:
                        content = part.get_content()
                        if isinstance(content, str) and content.strip():
                            parts.append(content.strip())
                    except (LookupError, UnicodeDecodeError, ValueError) as exc:
                        charset_warnings.append(f"Bad charset in plain text part: {exc}")
                    except Exception:
                        pass
                elif ctype == "text/html":
                    try:
                        content = part.get_content()
                        if isinstance(content, str):
                            parser = HTMLTextExtractor()
                            parser.feed(content)
                            text_val = parser.get_text()
                            if text_val:
                                parts.append(text_val)
                    except (LookupError, UnicodeDecodeError, ValueError) as exc:
                        charset_warnings.append(f"Bad charset in html part: {exc}")
                    except Exception:
                        pass

            has_replacement_char = any("\ufffd" in p for p in parts)
            combined = "\n".join(parts).strip()
            if combined:
                norm = unicodedata.normalize("NFC", combined)
                if len(norm) > MAX_OUTPUT_TEXT_CHARS:
                    norm = norm[:MAX_OUTPUT_TEXT_CHARS]
                notes: list[str] = []
                if has_replacement_char or "\ufffd" in norm:
                    notes.append("replacement characters present")
                note_str = "; ".join(notes) if notes else None
                err_str = "; ".join(charset_warnings) if charset_warnings else None
                if charset_warnings or has_replacement_char or "\ufffd" in norm:
                    return norm, "ok_with_warnings", note_str, err_str
                return norm, "ok", None, None
            else:
                if charset_warnings:
                    return (
                        "",
                        "failed",
                        None,
                        f"EML extraction failed: {'; '.join(charset_warnings)}",
                    )
                return "", "no_text", None, None
        except Exception as exc:
            return "", "failed", None, f"EML extraction failed: {exc}"

    return "", "no_text", None, None


def make_snippet(
    query: str,
    original_name: str,
    source_path: str,
    extracted_text: str,
    receipt_id: str,
    context_chars: int = 40,
) -> str:
    """Generate snippet with match highlight markers '[' and ']'."""
    q_norm = unicodedata.normalize("NFC", query).strip()
    if not q_norm:
        return original_name

    text_norm = unicodedata.normalize("NFC", extracted_text or "")
    name_norm = unicodedata.normalize("NFC", original_name or "")
    path_norm = unicodedata.normalize("NFC", source_path or "")
    rec_norm = unicodedata.normalize("NFC", receipt_id or "")

    # 1. Match in extracted_text
    idx = text_norm.lower().find(q_norm.lower())
    if idx != -1:
        start = max(0, idx - context_chars)
        end = min(len(text_norm), idx + len(q_norm) + context_chars)
        matched_str = text_norm[idx : idx + len(q_norm)]
        prefix_part = ("..." if start > 0 else "") + text_norm[start:idx].lstrip()
        suffix_part = text_norm[idx + len(q_norm) : end].rstrip() + (
            "..." if end < len(text_norm) else ""
        )
        clean_prefix = " ".join(prefix_part.split())
        clean_suffix = " ".join(suffix_part.split())
        return f"{clean_prefix}[{matched_str}]{clean_suffix}"

    # 2. Match in original_name
    idx = name_norm.lower().find(q_norm.lower())
    if idx != -1:
        matched_str = name_norm[idx : idx + len(q_norm)]
        return name_norm[:idx] + f"[{matched_str}]" + name_norm[idx + len(q_norm) :]

    # 3. Match in source_path
    idx = path_norm.lower().find(q_norm.lower())
    if idx != -1:
        start = max(0, idx - context_chars)
        end = min(len(path_norm), idx + len(q_norm) + context_chars)
        matched_str = path_norm[idx : idx + len(q_norm)]
        prefix_part = ("..." if start > 0 else "") + path_norm[start:idx]
        suffix_part = path_norm[idx + len(q_norm) : end] + (
            "..." if end < len(path_norm) else ""
        )
        return f"{prefix_part}[{matched_str}]{suffix_part} [path match]"

    # 4. Match in receipt_id
    idx = rec_norm.lower().find(q_norm.lower())
    if idx != -1:
        matched_str = rec_norm[idx : idx + len(q_norm)]
        return rec_norm[:idx] + f"[{matched_str}]" + rec_norm[idx + len(q_norm) :] + " [receipt match]"

    # 5. Multi-word query individual terms
    terms = q_norm.split()
    if len(terms) > 1:
        for term in terms:
            if len(term) >= 2:
                idx = text_norm.lower().find(term.lower())
                if idx != -1:
                    start = max(0, idx - context_chars)
                    end = min(len(text_norm), idx + len(term) + context_chars)
                    matched_str = text_norm[idx : idx + len(term)]
                    prefix_part = ("..." if start > 0 else "") + text_norm[start:idx].lstrip()
                    suffix_part = text_norm[idx + len(term) : end].rstrip() + (
                        "..." if end < len(text_norm) else ""
                    )
                    return f"{' '.join(prefix_part.split())}[{matched_str}]{' '.join(suffix_part.split())}"

    return original_name


def probe_sqlite_capabilities() -> dict[str, bool]:
    """Probe SQLite FTS5 and trigram tokenizer capabilities (P1-3)."""
    has_fts5 = False
    has_trigram = False
    try:
        conn = sqlite3.connect(":memory:")
        try:
            conn.execute("CREATE VIRTUAL TABLE _test_fts5 USING fts5(content)")
            has_fts5 = True
            conn.execute(
                "CREATE VIRTUAL TABLE _test_tri USING fts5(content, tokenize='trigram')"
            )
            has_trigram = True
        finally:
            conn.close()
    except (sqlite3.OperationalError, sqlite3.DatabaseError):
        pass
    return {"fts5": has_fts5, "trigram": has_trigram}


def init_database(conn: sqlite3.Connection, has_trigram: bool = True) -> None:
    """Initialize schema in SQLite index database (P1-3, P1-4, P1-5)."""
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(f"PRAGMA user_version = {CURRENT_SCHEMA_VERSION}")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS objects (
            sha256 TEXT NOT NULL,
            ext TEXT NOT NULL,
            ext_class TEXT NOT NULL,
            extractor_version TEXT NOT NULL,
            extracted_text TEXT NOT NULL,
            extraction_status TEXT NOT NULL,
            extraction_note TEXT,
            extraction_error TEXT,
            PRIMARY KEY (sha256, ext_class, extractor_version)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS receipts (
            id TEXT PRIMARY KEY,
            sha256 TEXT NOT NULL,
            ext TEXT NOT NULL,
            ext_class TEXT NOT NULL,
            extractor_version TEXT NOT NULL,
            original_name TEXT NOT NULL,
            source_path TEXT NOT NULL,
            collected_at TEXT NOT NULL,
            tool_version TEXT NOT NULL,
            extracted_text TEXT NOT NULL,
            extraction_status TEXT NOT NULL,
            extraction_note TEXT,
            extraction_error TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS fts_tokens USING fts5(
            receipt_id,
            original_name,
            source_path,
            collected_at,
            text,
            tokenize='unicode61'
        )
        """
    )
    if has_trigram:
        conn.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS fts_trigram USING fts5(
                receipt_id,
                original_name,
                source_path,
                collected_at,
                text,
                tokenize='trigram'
            )
            """
        )


def check_database_healthy(conn: sqlite3.Connection, has_trigram: bool) -> bool:
    """Validate schema_version and FTS table health (P1-5)."""
    try:
        row = conn.execute("PRAGMA user_version").fetchone()
        if not row or row[0] != CURRENT_SCHEMA_VERSION:
            return False
        conn.execute("SELECT rowid FROM fts_tokens LIMIT 1")
        if has_trigram:
            conn.execute("SELECT rowid FROM fts_trigram LIMIT 1")
        return True
    except (sqlite3.OperationalError, sqlite3.DatabaseError):
        return False


def snapshot_and_validate_receipts(
    root: Path,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, str]]]:
    """Snapshot receipt files and validate integrity of receipts and referenced objects (P1-2, P2).

    Returns:
        (receipt_dict, integrity_errors)
    """
    receipts_dir = root / "receipts" / "v1"
    receipts: dict[str, dict[str, Any]] = {}
    integrity_errors: list[dict[str, str]] = []

    if not receipts_dir.is_dir():
        return receipts, integrity_errors

    for p in sorted(receipts_dir.glob("*.json")):
        rec_id = p.stem.lower()
        try:
            content = p.read_text(encoding="utf-8")
            data = json.loads(content)
            if not isinstance(data, dict):
                integrity_errors.append(
                    {"path": str(p), "error": f"Malformed receipt (not a JSON object): {p}"}
                )
                continue
        except Exception as exc:
            integrity_errors.append(
                {"path": str(p), "error": f"Malformed receipt file {p}: {exc}"}
            )
            continue

        sha256 = str(data.get("sha256", "")).lower()
        if not sha256 or len(sha256) != 64:
            integrity_errors.append(
                {"path": str(p), "error": f"Receipt {p} has invalid or missing sha256"}
            )
            continue

        # Check that referenced object file exists
        obj_path = root / "objects" / sha256[:2] / sha256
        if not obj_path.is_file():
            integrity_errors.append(
                {
                    "path": str(obj_path),
                    "error": f"Missing object {obj_path} referenced by receipt {rec_id}",
                }
            )
            continue

        receipts[rec_id] = {
            "path": p,
            "data": data,
            "sha256": sha256,
            "obj_path": obj_path,
        }

    return receipts, integrity_errors


def perform_extractions(
    root: Path,
    receipts: dict[str, dict[str, Any]],
    known_objects: dict[tuple[str, str, str], tuple[str, str, str | None, str | None]],
) -> dict[str, tuple[str, str, str | None, str | None]]:
    """Extract text for all receipts outside of WriterLock (P1-2).

    Cache key is (sha256, ext_class, EXTRACTOR_VERSION) (P1-1, P1-4).
    Recoverable failures (status == 'failed') are retried on each run.
    """
    results: dict[str, tuple[str, str, str | None, str | None]] = {}

    for rec_id, rec in receipts.items():
        data = rec["data"]
        raw_name = str(data.get("original_name") or data.get("name") or "")
        orig_name = unicodedata.normalize("NFC", raw_name)
        ext_class = get_ext_class(orig_name)
        sha256 = rec["sha256"]
        cache_key = (sha256, ext_class, EXTRACTOR_VERSION)

        cached = known_objects.get(cache_key)
        # P1-4: retry recoverable failures on next find (do not reuse cached 'failed')
        if cached is not None and cached[1] != "failed":
            results[rec_id] = cached
        else:
            # Perform extraction WITHOUT holding WriterLock
            text, status, note, err = extract_object_text(rec["obj_path"], orig_name)
            res_tuple = (text, status, note, err)
            results[rec_id] = res_tuple
            known_objects[cache_key] = res_tuple

    return results


def build_index_atomic(
    root: Path,
    receipts: dict[str, dict[str, Any]],
    extracted: dict[str, tuple[str, str, str | None, str | None]],
    has_trigram: bool,
) -> None:
    """Build full index database in temporary file and atomically replace index.db (P1-1, P1-5)."""
    cache_dir = root / "cache"
    validate_cache_security(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    validate_cache_security(cache_dir)

    db_path = cache_dir / "index.db"
    validate_cache_security(cache_dir, db_path)

    # Build into temporary file under cache_dir
    tmp_db_path = cache_dir / f"index.db.tmp.{os.getpid()}.{time.time_ns()}"
    validate_cache_security(cache_dir, tmp_db_path)

    try:
        conn = sqlite3.connect(tmp_db_path)
    except (sqlite3.OperationalError, sqlite3.DatabaseError) as exc:
        raise UsageIOError(f"Cannot initialize temporary index database: {exc}") from exc

    try:
        init_database(conn, has_trigram=has_trigram)

        # Insert objects
        inserted_objects: set[tuple[str, str, str]] = set()
        for rec_id, rec in receipts.items():
            sha256 = rec["sha256"]
            raw_name = str(rec["data"].get("original_name") or rec["data"].get("name") or "")
            orig_name = unicodedata.normalize("NFC", raw_name)
            ext = Path(orig_name).suffix.lower()
            ext_class = get_ext_class(orig_name)
            obj_key = (sha256, ext_class, EXTRACTOR_VERSION)
            if obj_key in inserted_objects:
                continue

            text, status, note, err = extracted[rec_id]
            conn.execute(
                """
                INSERT OR REPLACE INTO objects
                (sha256, ext, ext_class, extractor_version, extracted_text, extraction_status, extraction_note, extraction_error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (sha256, ext, ext_class, EXTRACTOR_VERSION, text, status, note, err),
            )
            inserted_objects.add(obj_key)

        # Insert receipts and FTS rows
        for rec_id, rec in receipts.items():
            data = rec["data"]
            sha256 = rec["sha256"]
            raw_orig_name = str(data.get("original_name") or data.get("name") or "")
            orig_name = unicodedata.normalize("NFC", raw_orig_name)
            ext = Path(orig_name).suffix.lower()
            ext_class = get_ext_class(orig_name)
            source_path = unicodedata.normalize("NFC", str(data.get("source_path") or ""))
            collected_at = str(data.get("collected_at") or "")
            tool_version = str(data.get("tool_version") or "")

            text, status, note, err = extracted[rec_id]

            conn.execute(
                """
                INSERT OR REPLACE INTO receipts
                (id, sha256, ext, ext_class, extractor_version, original_name, source_path, collected_at, tool_version,
                 extracted_text, extraction_status, extraction_note, extraction_error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rec_id,
                    sha256,
                    ext,
                    ext_class,
                    EXTRACTOR_VERSION,
                    orig_name,
                    source_path,
                    collected_at,
                    tool_version,
                    text,
                    status,
                    note,
                    err,
                ),
            )
            conn.execute(
                "INSERT INTO fts_tokens VALUES (?, ?, ?, ?, ?)",
                (rec_id, orig_name, source_path, collected_at, text),
            )
            if has_trigram:
                conn.execute(
                    "INSERT INTO fts_trigram VALUES (?, ?, ?, ?, ?)",
                    (rec_id, orig_name, source_path, collected_at, text),
                )

        conn.commit()
    except (sqlite3.OperationalError, sqlite3.DatabaseError) as exc:
        raise UsageIOError(f"SQLite error during indexing: {exc}") from exc
    finally:
        try:
            conn.close()
        except Exception:
            pass

    # Short commit under WriterLock: atomic replace
    with WriterLock(root):
        validate_cache_security(cache_dir, db_path)
        try:
            os.replace(tmp_db_path, db_path)
        except OSError as exc:
            if tmp_db_path.exists():
                try:
                    tmp_db_path.unlink()
                except OSError:
                    pass
            raise UsageIOError(f"Failed to replace index database: {exc}") from exc


def ensure_index_current(
    root: Path, force_reindex: bool = False, allow_restore_marker: bool = False
) -> tuple[str, list[dict[str, str]]]:
    """Ensure index is current without holding WriterLock during extraction (P1-1, P1-2, P1-5).

    Returns:
        (index_mode, integrity_errors)
    """
    validate_root(root, allow_restore_marker=allow_restore_marker)
    caps = probe_sqlite_capabilities()
    has_trigram = caps["trigram"]
    index_mode = "trigram" if has_trigram else "like"

    cache_dir = root / "cache"
    db_path = cache_dir / "index.db"
    validate_cache_security(cache_dir, db_path if db_path.exists() else None)

    # 1. Snapshot and validate receipts (integrity problems reported with exit 1)
    receipts, integrity_errors = snapshot_and_validate_receipts(root)
    if integrity_errors:
        return index_mode, integrity_errors

    # 2. Check health and staleness
    need_full_rebuild = force_reindex or not db_path.exists()
    known_objects: dict[tuple[str, str, str], tuple[str, str, str | None, str | None]] = {}
    db_receipts: dict[str, dict[str, Any]] = {}
    db_rows: set[tuple[str, str, str, str]] = set()

    if not need_full_rebuild:
        try:
            conn = sqlite3.connect(db_path)
            try:
                if not check_database_healthy(conn, has_trigram):
                    need_full_rebuild = True
                else:
                    for row in conn.execute(
                        """
                        SELECT id, sha256, ext_class, extractor_version,
                               original_name, source_path, collected_at, tool_version,
                               extraction_status, extracted_text
                        FROM receipts
                        """
                    ):
                        rid = row[0]
                        db_rows.add((row[0], row[1], row[2], row[3]))
                        db_receipts[rid] = {
                            "id": row[0],
                            "sha256": row[1],
                            "ext_class": row[2],
                            "extractor_version": row[3],
                            "original_name": row[4],
                            "source_path": row[5],
                            "collected_at": row[6],
                            "tool_version": row[7],
                            "extraction_status": row[8],
                            "extracted_text": row[9],
                        }

                    disk_rows: set[tuple[str, str, str, str]] = set()
                    for rec_id, rec in receipts.items():
                        r_name = str(rec["data"].get("original_name") or rec["data"].get("name") or "")
                        o_name = unicodedata.normalize("NFC", r_name)
                        e_cls = get_ext_class(o_name)
                        disk_rows.add((rec_id, rec["sha256"], e_cls, EXTRACTOR_VERSION))

                    # P1-5 & cx round-2: staleness check compares (receipt_id, sha256, ext_class, extractor_version)
                    if db_rows != disk_rows:
                        db_ids = {r[0] for r in db_rows}
                        disk_ids = {r[0] for r in disk_rows}
                        if (db_ids - disk_ids) or any(r[3] != EXTRACTOR_VERSION for r in db_rows):
                            need_full_rebuild = True

                    # Load cached object extractions
                    for row in conn.execute(
                        """
                        SELECT sha256, ext_class, extractor_version, extracted_text,
                               extraction_status, extraction_note, extraction_error
                        FROM objects
                        """
                    ):
                        key = (row[0], row[1], row[2])
                        known_objects[key] = (row[3], row[4], row[5], row[6])
            finally:
                conn.close()
        except (sqlite3.OperationalError, sqlite3.DatabaseError):
            need_full_rebuild = True

    # 3. Perform extractions outside of WriterLock (P1-2)
    extracted = perform_extractions(root, receipts, known_objects)

    # Check which receipts require updating/upserting (P1)
    upsert_rec_ids: set[str] = set()
    if not need_full_rebuild:
        for rec_id, rec in receipts.items():
            if rec_id not in db_receipts:
                upsert_rec_ids.add(rec_id)
                continue

            prev = db_receipts[rec_id]
            data = rec["data"]
            raw_name = str(data.get("original_name") or data.get("name") or "")
            orig_name = unicodedata.normalize("NFC", raw_name)
            ext_class = get_ext_class(orig_name)
            source_path = unicodedata.normalize("NFC", str(data.get("source_path") or ""))
            collected_at = str(data.get("collected_at") or "")
            sha256 = rec["sha256"]

            # 1. (receipt_id, sha256, ext_class, extractor_version) check
            if (
                sha256 != prev["sha256"]
                or ext_class != prev["ext_class"]
                or EXTRACTOR_VERSION != prev["extractor_version"]
            ):
                upsert_rec_ids.add(rec_id)
                continue

            # 2. Same-ID metadata changes
            if (
                orig_name != prev["original_name"]
                or source_path != prev["source_path"]
                or collected_at != prev["collected_at"]
            ):
                upsert_rec_ids.add(rec_id)
                continue

            # 3. Successful retries of previously failed extractions or status change
            new_text, new_status, new_note, new_err = extracted[rec_id]
            if prev["extraction_status"] == "failed" and new_status != "failed":
                upsert_rec_ids.add(rec_id)
                continue
            if new_status != prev["extraction_status"]:
                upsert_rec_ids.add(rec_id)
                continue

    # 4. Commit into database
    if need_full_rebuild:
        build_index_atomic(root, receipts, extracted, has_trigram)
    elif upsert_rec_ids:
        # Incremental upsert under WriterLock
        with WriterLock(root):
            validate_cache_security(cache_dir, db_path)
            try:
                conn = sqlite3.connect(db_path)
            except (sqlite3.OperationalError, sqlite3.DatabaseError) as exc:
                raise UsageIOError(f"Cannot open index database: {exc}") from exc

            try:
                for rec_id in sorted(upsert_rec_ids):
                    rec = receipts[rec_id]
                    data = rec["data"]
                    sha256 = rec["sha256"]
                    raw_orig_name = str(data.get("original_name") or data.get("name") or "")
                    orig_name = unicodedata.normalize("NFC", raw_orig_name)
                    ext = Path(orig_name).suffix.lower()
                    ext_class = get_ext_class(orig_name)
                    source_path = unicodedata.normalize("NFC", str(data.get("source_path") or ""))
                    collected_at = str(data.get("collected_at") or "")
                    tool_version = str(data.get("tool_version") or "")

                    text, status, note, err = extracted[rec_id]

                    conn.execute(
                        """
                        INSERT OR REPLACE INTO objects
                        (sha256, ext, ext_class, extractor_version, extracted_text, extraction_status, extraction_note, extraction_error)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (sha256, ext, ext_class, EXTRACTOR_VERSION, text, status, note, err),
                    )
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO receipts
                        (id, sha256, ext, ext_class, extractor_version, original_name, source_path, collected_at, tool_version,
                         extracted_text, extraction_status, extraction_note, extraction_error)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            rec_id,
                            sha256,
                            ext,
                            ext_class,
                            EXTRACTOR_VERSION,
                            orig_name,
                            source_path,
                            collected_at,
                            tool_version,
                            text,
                            status,
                            note,
                            err,
                        ),
                    )
                    conn.execute("DELETE FROM fts_tokens WHERE receipt_id = ?", (rec_id,))
                    conn.execute(
                        "INSERT INTO fts_tokens VALUES (?, ?, ?, ?, ?)",
                        (rec_id, orig_name, source_path, collected_at, text),
                    )
                    if has_trigram:
                        conn.execute("DELETE FROM fts_trigram WHERE receipt_id = ?", (rec_id,))
                        conn.execute(
                            "INSERT INTO fts_trigram VALUES (?, ?, ?, ?, ?)",
                            (rec_id, orig_name, source_path, collected_at, text),
                        )
                conn.commit()
            except (sqlite3.OperationalError, sqlite3.DatabaseError) as exc:
                raise UsageIOError(f"SQLite error during incremental indexing: {exc}") from exc
            finally:
                try:
                    conn.close()
                except Exception:
                    pass

    return index_mode, []


def find_items(
    root: Path,
    query: str,
    limit: int | None = None,
    force_reindex: bool = False,
) -> tuple[list[dict[str, Any]], str, list[dict[str, str]]]:
    """Search repository index for matching query string.

    Returns:
        (results, index_mode, integrity_errors)
    """
    index_mode, integrity_errors = ensure_index_current(
        root, force_reindex=force_reindex
    )
    if integrity_errors:
        return [], index_mode, integrity_errors

    q_norm = unicodedata.normalize("NFC", query).strip()
    if not q_norm:
        return [], index_mode, []

    db_path = root / "cache" / "index.db"
    if not db_path.exists():
        return [], index_mode, []

    matched_records: dict[str, dict[str, Any]] = {}
    order_list: list[str] = []

    try:
        conn = sqlite3.connect(db_path)
    except (sqlite3.OperationalError, sqlite3.DatabaseError) as exc:
        raise UsageIOError(f"Cannot open index database: {exc}") from exc

    try:
        conn.row_factory = sqlite3.Row

        # If trigram missing, fall back to LIKE search with notice (P1-3)
        if index_mode == "like" or len(q_norm) < 3:
            pattern = f"%{escape_like(q_norm)}%"
            sql = """
            SELECT id, sha256, original_name, source_path, collected_at, tool_version,
                   extracted_text, extraction_status, extraction_note, extraction_error
            FROM receipts
            WHERE original_name LIKE :pat ESCAPE '\\'
               OR source_path LIKE :pat ESCAPE '\\'
               OR id LIKE :pat ESCAPE '\\'
               OR sha256 LIKE :pat ESCAPE '\\'
               OR collected_at LIKE :pat ESCAPE '\\'
               OR extracted_text LIKE :pat ESCAPE '\\'
            ORDER BY collected_at DESC
            """
            for row in conn.execute(sql, {"pat": pattern}):
                rid = row["id"]
                if rid not in matched_records:
                    matched_records[rid] = dict(row)
                    order_list.append(rid)

        else:
            # Query >= 3 chars with trigram: run FTS5
            fts_phrase = '"' + q_norm.replace('"', '""') + '"'

            # 1. Search trigram for substrings (P1-5: MATCH errors reported not swallowed)
            try:
                sql_tri = (
                    "SELECT receipt_id, rank FROM fts_trigram WHERE fts_trigram MATCH ?"
                    " ORDER BY rank"
                )
                for row in conn.execute(sql_tri, (fts_phrase,)):
                    rid = row["receipt_id"]
                    if rid not in matched_records:
                        matched_records[rid] = None  # type: ignore
                        order_list.append(rid)
            except sqlite3.OperationalError as exc:
                raise UsageIOError(f"FTS trigram search error: {exc}") from exc

            # 2. Search unicode61 word tokens
            try:
                sql_tok = (
                    "SELECT receipt_id, rank FROM fts_tokens WHERE fts_tokens MATCH ?"
                    " ORDER BY rank"
                )
                for row in conn.execute(sql_tok, (fts_phrase,)):
                    rid = row["receipt_id"]
                    if rid not in matched_records:
                        matched_records[rid] = None  # type: ignore
                        order_list.append(rid)
            except sqlite3.OperationalError as exc:
                raise UsageIOError(f"FTS token search error: {exc}") from exc

            # Fetch details for matched IDs
            if order_list:
                placeholders = ",".join("?" for _ in order_list)
                sql_fetch = f"""
                SELECT id, sha256, original_name, source_path, collected_at, tool_version,
                       extracted_text, extraction_status, extraction_note, extraction_error
                FROM receipts
                WHERE id IN ({placeholders})
                """
                for row in conn.execute(sql_fetch, order_list):
                    matched_records[row["id"]] = dict(row)

            # Fallback to LIKE if FTS produced 0 results
            if not matched_records:
                pattern = f"%{escape_like(q_norm)}%"
                sql_like = """
                SELECT id, sha256, original_name, source_path, collected_at, tool_version,
                       extracted_text, extraction_status, extraction_note, extraction_error
                FROM receipts
                WHERE original_name LIKE :pat ESCAPE '\\'
                   OR source_path LIKE :pat ESCAPE '\\'
                   OR id LIKE :pat ESCAPE '\\'
                   OR sha256 LIKE :pat ESCAPE '\\'
                   OR collected_at LIKE :pat ESCAPE '\\'
                   OR extracted_text LIKE :pat ESCAPE '\\'
                ORDER BY collected_at DESC
                """
                for row in conn.execute(sql_like, {"pat": pattern}):
                    rid = row["id"]
                    if rid not in matched_records:
                        matched_records[rid] = dict(row)
                        order_list.append(rid)
    except sqlite3.OperationalError as exc:
        raise UsageIOError(f"Database query error: {exc}") from exc
    finally:
        conn.close()

    results: list[dict[str, Any]] = []
    for rid in order_list:
        rec = matched_records.get(rid)
        if not rec:
            continue
        snippet = make_snippet(
            query=q_norm,
            original_name=rec["original_name"],
            source_path=rec["source_path"],
            extracted_text=rec["extracted_text"],
            receipt_id=rec["id"],
        )
        results.append(
            {
                "id": rec["id"],
                "name": rec["original_name"],
                "original_name": rec["original_name"],
                "snippet": snippet,
                "extraction_status": rec["extraction_status"],
                "extraction_note": rec.get("extraction_note"),
                "extraction_error": rec["extraction_error"],
            }
        )

    if limit is not None and limit > 0:
        results = results[:limit]

    return results, index_mode, []


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--extract-pdf-worker":
        pdf_path_arg = sys.argv[2]
        max_pages_arg = int(sys.argv[3]) if len(sys.argv) > 3 else MAX_PDF_PAGES
        output_cap_arg = (
            int(sys.argv[4]) if len(sys.argv) > 4 else MAX_OUTPUT_TEXT_CHARS
        )
        max_stream_size_arg = (
            int(sys.argv[5]) if len(sys.argv) > 5 else MAX_PDF_STREAM_SIZE
        )
        sys.exit(
            _pdf_worker_main(
                pdf_path_arg, max_pages_arg, output_cap_arg, max_stream_size_arg
            )
        )
