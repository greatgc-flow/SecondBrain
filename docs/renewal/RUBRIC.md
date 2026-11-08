# SecondBrain v1 rubric

Skeleton for DESIGN.md §11 and invariants I1–I8. The orchestrator maintains
scores after slice review. All scores start at 0; release requires all at 100.

| Id | Requirement / invariant | Score |
| --- | --- | --- |
| B1 | inbox -> raws -> wiki | 0 |
| B2 | Discard v0.1; tag history only | 0 |
| B3 | Deterministic wiki pages, index, and links | 0 |
| B4 | Explicit LLM tier via peers | 0 |
| B5 | Classify and list counts before approved OCR | 0 |
| B6 | Explicit approval for sensitive or large inputs | 0 |
| B7 | markitdown-gc 0.3.5 conversion and triage | 0 |
| B8 | MECE classification, including unsupported and unknown | 0 |
| B9 | Never retranscribe; record provenance | 0 |
| B10 | VerySimpleGuide, Windows, English | 0 |
| G1 | OCR prompt, batching, pilot, concurrency, approval cap | 0 |
| G2 | Independent second-peer verification; exact digits | 0 |
| G3 | OCR ledger, no cache, scratch cleanup | 0 |
| G4 | Offline CI; peerhub as operator workflow | 0 |
| X1 | Crash safety and corruption handling | 0 |
| X2 | Untrusted content handling | 0 |
| X3 | Complete CLI, JSON, and exit contract | 0 |
| I1 | Source never written or moved after rename 1 | 0 |
| I2 | Completed conversion output produced at most once | 0 |
| I3 | Pure transcript view | 0 |
| I4 | Approved OCR keys and new digests only | 0 |
| I5 | Verifying peer differs from recording peer | 0 |
| I6 | Unverified OCR excluded from view and wiki | 0 |
| I7 | Wiki derived only from raws | 0 |
| I8 | Restricted deletion targets | 0 |
