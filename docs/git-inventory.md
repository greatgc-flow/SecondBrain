# Git policy and inventory

Policy first, then verified facts. All Git operations are delegated to `ag` (original record `rec-ef51dbb58ce9`, stream `secondbrain:council:ag`). Evidence status: [status.md](status.md).

## Policy

- Keep every unique or uncertain branch and every open-PR base/head reference. Never delete a branch because it is old.
- Before any deletion: a full-SHA immutable archive tag, a verified bundle, a reviewer dry run, a fresh check of PR heads/bases, and an atomic delete with an expected-old-SHA lease.
- No force-push to `main`. No merge without owner authorization.
- Branch cleanup is conservative: only provable ancestors of `main` are candidates.
- Raw inventory reports are local and never committed; external copies exist.

## Verified facts (2026-10-16)

| Fact | Value |
|---|---|
| Initial heads | 43 |
| Remote heads before the doc branch push | 42 |
| `main` | `5a9fcf44f94a614649a3633e3c0df75f07f69b8f` |
| Kept PR heads | 2: PR46 `docs/checkpoint-m0` tip `0f2f8c84c4036a8bd54fa969f36f09671625ae60`; PR47 `feat/m1-s1-capture` tip `b94e86cb0219909c5b77b3347f6d7cf17c3f9768` |
| Other kept heads | 39 non-ancestor unique/squash tips, including the S2-S5 prototype |
| Removed (exactly one) | `dev/r13l-snapshot-consistency-20261010`, tip `8df9056bcba0929131f544629cf29e9bc27b5832` |
| Archive tag | `archive/20261016/dev/r13l-snapshot-consistency-20261010`, tag object `c1671dc8eaa59904f39baf0070f3e52e85d83b32`, remote peeled target verified before an atomic expected-old-SHA delete |
| Bundle | `C:/AI/workspace/SecondBrain-archives/20261016/backup-all-20261016.bundle`, SHA-256 `301c8898827ca1a0bba90e3119a5fc1a61335b3326c6dfa41924099657160c7f`, verified, 47 refs |
| Raw reports | `.peerhub/git-inventory-20261016.json`, `.peerhub/git-cleanup-20261016.json` (local; external copies; never committed) |

Only one branch was actually removed, not all 43.

## Working branch

`docs/v01-design-readiness-20261016` is a separate preparation branch. A draft PR is pending; no PR URL is recorded here.

## Restoring from the bundle

Do not reset the working tree. Clone the bundle into a temporary directory for inspection, verify the target tip SHA there, and copy back only what is needed after review.
