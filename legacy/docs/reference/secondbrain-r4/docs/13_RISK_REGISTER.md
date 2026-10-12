# 13. Initial Risk Register

| ID | Risk | Likelihood | Impact | Design Control |
|---|---|---:|---:|---|
| R-001 | user edits Vault file directly | M | H | digest verify, read-only UX |
| R-002 | sync conflict creates divergent files | M | H | digest identity, preserve both |
| R-003 | two devices ingest same file | H | M | idempotent object resolution |
| R-004 | cloud deletion propagates | M | H | secondary snapshot |
| R-005 | backup exists but is corrupt | M | H | verify-before-success |
| R-006 | SQLite synced and corrupts | M | H | local-only rebuildable index |
| R-007 | AI promotes inference to fact | M | H | provenance tier, approval |
| R-008 | evidence metadata is silently overwritten | M | H | append-only event history |
| R-009 | source timestamp misunderstood | M | H | observed/recorded/valid time separation |
| R-010 | placeholder hashed incompletely | M | H | hydration gate |
| R-011 | tool update changes extraction | M | M | tool version/config digest |
| R-012 | legal hold is bypassed | L | Critical | centralized destructive gate |
| R-013 | ransomware reaches primary | M | Critical | secondary/offline snapshots |
| R-014 | user assumes cloud versioning is backup | H | H | explicit operational docs |
| R-015 | evidence hash is correct but acquisition context missing | M | H | ERL model |
| R-016 | package becomes tightly coupled to PeerHub | M | M | URI/reference-only adapter |
| R-017 | package becomes tied to OneDrive | M | M | filesystem-first root |
| R-018 | schemas drift from code | M | H | schema contract tests planned |

## R2 risk controls
See `docs/15_R1_AUDIT_FINDINGS.md` (F01–F16), `docs/29_RESIDUAL_RISKS.md` (RR-01–12). Add risks: split-brain Writer, data exfiltration via AI, unsafe archive/paths, fake ERL-3, invalid JCS chain, ghost snapshots, unverified cloud upload, legal hold predicate lag, misleading forensic authenticity. 모두 R2 priority P0 guardrails로 trace.
