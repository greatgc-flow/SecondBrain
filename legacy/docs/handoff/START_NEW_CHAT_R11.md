# Copy/paste into a new ChatGPT conversation — SecondBrain R11

Continue the **private** GitHub repository `greatgc-flow/SecondBrain` directly. No ZIP handoffs. Read the following **in order**, starting from the current `main` branch:

1. `docs/handoff/2026-10-10_R10_TO_R11_HANDOFF.md`
2. `docs/handoff/START_NEW_CHAT_R11.md` (this prompt)
3. `README.md`, `docs/README.md`, `docs/roadmap/S1_NEXT.md`, `docs/history/R10_GATE.md`
4. `profiles/secondbrain/R10_CHECKPOINT_QUICKSTART.md`, `brain.py`, `brain_core/`, `schemas/v2/`, and current `tests/`
5. `docs/reference/README.md`, and relevant archived design contracts **only where required**.

**Always check live GitHub `main` SHA, recent commits, CI and open PRs first; do not roll back to the recorded handoff SHA if `main` has advanced.**

Context: R7 Capture, R8 local single Writer/Vault, R9 unanchored RFC 8785 custody chain, and R10 operator-supplied external checkpoint comparison are implemented. As of baseline commit `ef94707`, GitHub CI passed **84 synthetic tests** using `rfc8785==0.1.4`. R11 EvidenceObject **creation** and end-to-end cross-references are **not implemented**. `verify_object` exists but only reads a pre-existing record. `sealed_at` in the existing v2 schema is a potential semantic trap: **never claim trusted sealing or falsify timestamps to make the schema pass**.

**Now execute R11 TDD**, not another broad redesign:
- RED tests for canonical EvidenceObject creation from already-verified Capture/Writer/Custody, unique content-addressed object and independent per-capture Observation/Acquisition references, safe retries, conflicting record refusal, fail-closed partial writes, real byte/record cross-link verification, JSON/symlink/relocation/CLI negative cases.
- Resolve the `sealed_at` semantics with a small explicit schema/status decision, preserving honesty about local vs externally attested states.
- Implement minimal GREEN, refactor to reuse existing helpers, run all tests, push a small GitHub PR, verify candidate-bound CI, merge after green and check fresh `main` CI.
- Update `R11_SCOPE.md`, a short usage guide, `docs/history/R11_GATE.md`, and roadmap/README. Keep requirements↔implementation↔tests↔docs mutually consistent.
- Stay **Very Simple**: SSOT, MECE, minimal tokens/help examples, no unnecessary hardcoding or duplicate functionality; use robust mature modules.
- Preserve evidence originals and privacy. Use **synthetic fixtures only**, do not commit private evidence/secrets/caches/ZIPs, and do not claim real cloud, Windows or paid provider tests were executed unless they were.
- Track error, lesson, root cause and test evidence; do not consider an operational feedback issue closed without observed effect.
- **Do not release** on PyPI/winget or call this a certified evidence system. GitHub is the sole destination for source, tests and current docs.

If an implementation step is blocked by permission/dependency, do as much safely as possible, record the exact blocker and never report an unperformed push/CI/merge as done. Provide a concise status with GitHub PR/commit/CI links, test counts, and actual remaining blockers. Do not deliver a ZIP or request information already in GitHub. Start the work.
