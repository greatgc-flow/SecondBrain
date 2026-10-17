"""Single-writer lock management."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from secondbrain.errors import LockError
from secondbrain.receipt import is_reparse_point


def _get_path_identity(p: Path) -> tuple[int, int] | None:
    try:
        st = os.stat(str(p))
        dev = getattr(st, "st_dev", 0)
        ino = getattr(st, "st_ino", 0)
        if ino != 0 or dev != 0:
            return (dev, ino)
    except OSError:
        pass
    return None


class WriterLock:
    """Exclusive single-writer lock for the SecondBrain repository."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.lock_path = self.root / "writer.lock"
        self._fp: Any = None

    def acquire(self) -> None:
        """Acquire non-blocking exclusive lock or raise LockError."""
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)

        # Guard lock path before opening:
        # 1. Not a link or reparse point
        if self.lock_path.is_symlink() or os.path.islink(str(self.lock_path)) or is_reparse_point(self.lock_path):
            raise LockError(f"Writer lock path is a symlink or reparse point: {self.lock_path}")

        if self.lock_path.exists():
            try:
                st = os.lstat(str(self.lock_path))
            except OSError as exc:
                raise LockError(f"Cannot stat writer lock path '{self.lock_path}': {exc}") from exc

            # 2. nlink == 1 (reject multiple hardlinks)
            if getattr(st, "st_nlink", 1) > 1:
                raise LockError(
                    f"Writer lock path has multiple hardlinks (nlink={st.st_nlink}): {self.lock_path}"
                )

            # 3. No object alias
            try:
                if os.path.samefile(self.lock_path, self.root):
                    raise LockError(f"Writer lock path is same file as repository root: {self.lock_path}")
            except OSError:
                pass

            objects_dir = self.root / "objects"
            if objects_dir.is_dir():
                empty_sha = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
                empty_obj = objects_dir / empty_sha[:2] / empty_sha
                if os.path.lexists(str(empty_obj)):
                    try:
                        if os.path.samefile(self.lock_path, empty_obj):
                            raise LockError(f"Writer lock path aliases empty object: {self.lock_path}")
                    except OSError:
                        pass

                lock_ident = _get_path_identity(self.lock_path)
                if lock_ident is not None:
                    try:
                        for prefix_entry in os.scandir(objects_dir):
                            if prefix_entry.is_dir() and len(prefix_entry.name) == 2:
                                for obj_entry in os.scandir(prefix_entry.path):
                                    obj_p = Path(obj_entry.path)
                                    obj_ident = _get_path_identity(obj_p)
                                    if obj_ident is not None and obj_ident == lock_ident:
                                        raise LockError(f"Writer lock path aliases object: {self.lock_path}")
                    except OSError:
                        pass

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
