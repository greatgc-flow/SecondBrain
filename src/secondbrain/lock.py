"""Single-writer lock management."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from secondbrain.errors import LockError


class WriterLock:
    """Exclusive single-writer lock for the SecondBrain repository."""

    def __init__(self, root: Path) -> None:
        self.lock_path = root / "writer.lock"
        self._fp: Any = None

    def acquire(self) -> None:
        """Acquire non-blocking exclusive lock or raise LockError."""
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._fp = open(self.lock_path, "a+b")
            self._fp.seek(0, 2)
            if self._fp.tell() == 0:
                self._fp.write(b"L")
                self._fp.flush()
            self._fp.seek(0)

            if sys.platform == "win32":
                import msvcrt

                msvcrt.locking(self._fp.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(self._fp.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (OSError, IOError) as exc:
            if self._fp is not None:
                try:
                    self._fp.close()
                except Exception:
                    pass
                self._fp = None
            raise LockError(f"Another process holds the writer lock on {self.lock_path}") from exc

    def release(self) -> None:
        """Release the lock and close the file."""
        if self._fp is not None:
            try:
                self._fp.seek(0)
                if sys.platform == "win32":
                    import msvcrt

                    msvcrt.locking(self._fp.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(self._fp.fileno(), fcntl.LOCK_UN)
            except Exception:
                pass
            finally:
                try:
                    self._fp.close()
                except Exception:
                    pass
                self._fp = None

    def __enter__(self) -> WriterLock:
        self.acquire()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.release()
