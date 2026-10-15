#!/usr/bin/env python3
"""Single-command SecondBrain local/CI check. Does not modify source data."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git_snapshot() -> tuple[str, str]:
    try:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT,
            text=True, capture_output=True, check=False,
        )
        dirty = subprocess.run(
            ["git", "status", "--porcelain"], cwd=ROOT,
            text=True, capture_output=True, check=False,
        )
    except OSError:
        return "NOT_VERIFIED", "NOT_VERIFIED"
    if head.returncode or dirty.returncode:
        return "NOT_VERIFIED", "NOT_VERIFIED"
    return head.stdout.strip(), ("DIRTY" if dirty.stdout.strip() else "CLEAN")


def main() -> int:
    head, tree = git_snapshot()
    print(f"SecondBrain VERIFY | HEAD={head} | working_tree={tree}", flush=True)
    label = "pytest tests (current v0.1 code, not frozen legacy)"
    print(f"START {label}", flush=True)
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests", "-q"],
            cwd=ROOT, check=False,
        )
        status = "PASS" if result.returncode == 0 else "FAIL"
    except OSError as exc:
        print(f"EXECUTION ERROR: {exc}", file=sys.stderr)
        status = "FAIL"
    print(f"{status}: {label}", flush=True)
    print("NOT_VERIFIED: Windows/other Python matrix unless run on those runners.")
    print(f"OVERALL={status} | HEAD={head} | working_tree={tree}", flush=True)
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
