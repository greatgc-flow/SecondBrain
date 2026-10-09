#!/usr/bin/env python3
"""Maintainer-only: preview/update the design ZIP's local file digest manifest.

NOT a signature or trusted supply chain attestation. Inspect the diff before --apply.
"""
import argparse
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'PACKAGE_MANIFEST.sha256'


def calculate():
    rows = []
    for f in sorted(ROOT.rglob('*')):
        if not f.is_file() or f.is_symlink():
            continue
        rel = f.relative_to(ROOT)
        if not rel.parts or rel.parts[0] == '.kit_state' or '__pycache__' in rel.parts or f.suffix == '.pyc' or f == MANIFEST:
            continue
        rows.append(hashlib.sha256(f.read_bytes()).hexdigest() + '\t' + rel.as_posix())
    return '\n'.join(rows) + '\n'


def main():
    p = argparse.ArgumentParser(description='Maintainer only; --apply after reviewed changes')
    p.add_argument('--apply', action='store_true')
    args = p.parse_args()
    candidate = calculate()
    old = MANIFEST.read_text(encoding='utf-8') if MANIFEST.exists() else ''
    if candidate == old:
        print('UNCHANGED: manifest matches tree')
        return 0
    if not args.apply:
        print('DRIFT: manifest differs. Review changes and run --apply when intentional.')
        return 3
    MANIFEST.write_text(candidate, encoding='utf-8', newline='\n')
    print(f'UPDATED {len(candidate.splitlines())} digests. This does not sign/authenticate the archive.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
