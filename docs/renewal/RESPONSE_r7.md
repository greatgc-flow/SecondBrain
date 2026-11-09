# Response to round-7 review (DESIGN.md r8, 2026-11-09)

- Orchestrator correction (post-approval, factual): local dev Python is 3.15.2 and markitdown-gc 0.3.5 declares Requires-Python >=3.10,<3.16, so §9/§12 now say `pyproject` >= 3.11, < 3.16 and CI = Windows + Ubuntu x Python 3.11, 3.13, 3.15 (still six jobs).
- J1 ACCEPT. AT-26's oracle is split: a fault before rename 1 follows startup row 1 (unclaimed `stage.json` deleted, inbox file untouched, rerun claims it with the rerun's options, so `charset == null`); faults after rename 1 keep asserting the persisted `cp949`. No new state or configuration store; protocol unchanged. All other ids ACK (resolved).
