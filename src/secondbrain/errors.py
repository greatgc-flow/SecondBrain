"""Exception types for SecondBrain."""

from __future__ import annotations


class SecondBrainError(Exception):
    """Base exception for SecondBrain errors."""


class IntegrityError(SecondBrainError):
    """Raised when an integrity problem occurs (corrupt, missing, or mismatched data). Exit code 1."""


class UsageIOError(SecondBrainError):
    """Raised on usage or IO errors (missing files, locked files, unreadable inputs). Exit code 2."""


class RootRefusedError(UsageIOError):
    """Raised when an active root is refused per ADR 0002. Exit code 2."""


class LockError(UsageIOError):
    """Raised when single-writer lock acquisition fails. Exit code 2."""
