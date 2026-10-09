# ADR-0020 — Candidate-bound Gate Evidence
Status: ACCEPTED (design, 2026-10-09). Problem: CI PASS from different code/config/dependency can be misapplied. Decision: freeze candidate fingerprint and gate receipts, STALE upon relevant changes; release requires human signoff and recovery. See docs/35/40.
