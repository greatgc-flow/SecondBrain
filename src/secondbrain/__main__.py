"""Executable entrypoint for `python -m secondbrain`."""
import sys

from secondbrain.cli import main

if __name__ == "__main__":
    sys.exit(main())
