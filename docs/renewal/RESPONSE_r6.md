# Response to round-6 review (DESIGN.md r7, 2026-11-09)

Legend: ACCEPT (change, r7 section) | ACK (marked resolved; no change). r7 length = r6 (346 lines). argon and ag approved r6.

- cx-1–cx-33, N1–N12, E1–E5, F1, F2, G1, G2 ACK.
- **H1 (blocker) ACCEPT (by collapsing the protocol).** Ingest now has exactly two atomic renames: (1) inbox file -> `.staging/tmp-<n>/src/<received
  filename>` after `stage.json` exists; (2) directory `.staging/tmp-<n>` -> `raws/<id>` at commit. The payload never moves again: items keep
  `src/<received filename>` permanently (`original<ext>` and the `<id>/` staging rename are deleted; collisions are a ledger flag, not a
  rename). Startup recovery is one rule per directory kind, enumerated in a table (§4) and fault-tested row by row (AT-26), including a
  crash right after the payload move with exact byte preservation. Consequences handled: `ext` is metadata only; the planned `src/` path is
  length-checked before the move; the wiki link target is percent-encoded; reserved names are whatever the volume already accepted (a
  failing rename leaves the inbox file in place with `io_error`). §2, §4, §7, AT-01/04/26/35.
- **H2 ACCEPT.** I2 reworded: a successful conversion output is produced at most once per item; completed output is reconciled, never
  regenerated; an attempt that produced no completed text may be retried by `ingest --retry` or a resume. Exact one-call assertions are kept
  only for completed-output recovery paths; AT-13 and AT-26 aligned. §4.
- **H3 ACCEPT.** AT-12 asserts legal pairs only: `failed` with class null, or class `unknown` with state `awaiting-approval`, pinned per
  `EXPECTED.md`. §9.
