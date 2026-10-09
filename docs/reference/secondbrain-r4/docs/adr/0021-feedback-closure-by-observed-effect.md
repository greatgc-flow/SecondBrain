# ADR-0021 — Effect-verified Feedback Closure
Status: ACCEPTED (design, 2026-10-09). Problem: fixing code and passing tests alone is not verified operational benefit. Decision: require baseline/candidate + post-deploy observation + recurrence check before CLOSED. Otherwise remain AWAITING_EFFECT / corresponding prior state. See docs/33/37.
