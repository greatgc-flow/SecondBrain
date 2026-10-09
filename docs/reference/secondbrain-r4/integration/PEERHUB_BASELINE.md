# PeerHub integration R2 — 2026-10-09

Release reference: `v0.12.4`; https://github.com/greatgc-flow/peerhub/releases/tag/v0.12.4
Current README/main: https://github.com/greatgc-flow/peerhub/blob/main/README.md

**PeerHub Core owns Peer, Stream, Record, Offset only.** Bridge/Observation/Diag/Artifact/Work/Search/Routing and optional long work support are Extensions. Do not generate code importing legacy v0 task/consensus/room from Core. The bridge is optional; memory/evidence SSOT in SecondBrain filesystem. Pass restricted evidence only after explicit egress approval and redaction. `peerhub ask` may contact external provider; do not use real user evidence in tests. Integration requires feature detection/version negotiation. `peerhub` is NOT a storage backend.
