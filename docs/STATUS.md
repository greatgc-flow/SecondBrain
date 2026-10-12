# SecondBrain status (checkpoint)

**Checkpoint 2026-10-12 (M0 done).** The project restarted very simply. The old R7-R13 line is frozen (tag `legacy-r13-final`, moved to `legacy/`, reference only). Scope, decisions and acceptance are in [design.md](design.md) and [decisions.md](decisions.md).

## Done
- M0: design v0.1 (six commands, plain files, one backup root), ADRs, frozen legacy, `src/` skeleton with CLI stubs, smoke tests, CI (Windows + Ubuntu).

## Next (M1, implementer ag, reviewer cx, verifier cc; each step small and verified)
1. S1 `capture`: SHA-256 object store, receipts, duplicate handling, atomic publish, interruption recovery.
2. S2 `verify` and `open`: re-hash, report missing/corrupt/orphan, exit codes, tamper detection.
3. S3 `find`: derived SQLite FTS5 index, `.txt`/`.md`/text-PDF extraction, Korean search limits documented.
4. S4 `backup` and `restore`: append-only mirror to one backup root (may be a Drive/OneDrive synced folder), manifest last, restore into an empty directory and verify.
5. S5 acceptance: 100 mixed files (Korean names, spaces, long paths, duplicates, empty and locked files), interruption at every step.

## Owner decisions on record
Name `sb`, data root `D:\SecondBrain`; backup = one user-managed folder, no engine, no encryption in v0.1; AI access later and only for items the owner marks AI-visible; legal specifics (timestamp authority, exhibit format) are decided with a lawyer before any evidence tier is built.

## Later (not designed)
Read-only MCP access, web capture, e-mail/messenger import, other-device inbox, OCR/transcription, evidence tier, optional encryption.
