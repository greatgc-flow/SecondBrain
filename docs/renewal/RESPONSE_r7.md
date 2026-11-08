# Response to round-7 review (DESIGN.md r8, 2026-11-09)

- J1 ACCEPT. AT-26's oracle is split: a fault before rename 1 follows startup row 1 (unclaimed `stage.json` deleted, inbox file untouched, rerun claims it with the rerun's options, so `charset == null`); faults after rename 1 keep asserting the persisted `cp949`. No new state or configuration store; protocol unchanged. All other ids ACK (resolved).
