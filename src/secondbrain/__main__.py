"""Executable entrypoint for `python -m secondbrain`."""

from __future__ import annotations

import sys
from secondbrain.cli import main

if __name__ == "__main__":
    sys.exit(main())
