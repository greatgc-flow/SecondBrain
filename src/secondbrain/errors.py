"""Shared v1 codes and contract constants; independent of other package modules."""
from enum import StrEnum
import re

CONVERTER_VERSION = "0.3.6"
PEER = re.compile(r"[a-z][a-z0-9-]{0,31}")
LARGE = 20
PLAIN_TEXT_EXTENSIONS = frozenset({".txt", ".csv", ".log", ".json", ".xml"})
MARKUP_EXTENSIONS = frozenset({".md", ".html", ".htm"})
CONTAINER_EXTENSIONS = frozenset({".docx", ".pptx", ".xlsx", ".hwp", ".hwpx"})
RASTER_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".webp"})
TRIAGE_EXTENSIONS = MARKUP_EXTENSIONS | CONTAINER_EXTENSIONS | {".pdf"}
CONVERTIBLE_EXTENSIONS = PLAIN_TEXT_EXTENSIONS | TRIAGE_EXTENSIONS
ALLOWED_EXTENSIONS = CONVERTIBLE_EXTENSIONS | RASTER_EXTENSIONS


class ErrorCode(StrEnum):
    USAGE = "usage"
    UNKNOWN_ID = "unknown_id"
    STATE_NOT_ALLOWED = "state_not_allowed"
    NO_UNITS = "no_units"
    LARGE_REQUIRES_ACK = "large_requires_ack"
    SAME_PEER = "same_peer"
    STALE_OUTPUT = "stale_output"
    MISSING_OUTPUT = "missing_output"
    INVALID_REQUEST = "invalid_request"
    NOT_ELIGIBLE = "not_eligible"
    LLM_INVALID = "llm_invalid"
    ID_COLLISION = "id_collision"
    CORRUPT_META = "corrupt_meta"
    EMPTY_FILE = "empty_file"
    PATH_TOO_LONG = "path_too_long"
    CONVERSION_FAILED = "conversion_failed"
    REPORT_FAILED = "report_failed"
    REPORT_INVALID = "report_invalid"
    NO_CANDIDATE_IDS = "no_candidate_ids"
    TOO_MANY_UNITS = "too_many_units"
    IO_ERROR = "io_error"


class WarningCode(StrEnum):
    ORPHAN = "orphan"
    SKIPPED_REPARSE = "skipped_reparse"
    SKIPPED_HIDDEN = "skipped_hidden"
    STALE_WORK = "stale_work"
    STAGED_COLLISION = "staged_collision"


class SbError(Exception):
    def __init__(self, code, exit, message=None):
        self.code = str(code)
        self.exit = exit
        super().__init__(self.code if message is None else message)
