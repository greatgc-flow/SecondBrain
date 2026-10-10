# SecondBrain — R13-L → R13 operational handoff (2026-10-10 KST)

> **CURRENT handoff at creation time, not an alternative spec.** Always re-read live `main`, open PRs, exact GitHub Actions runs, issue #11, roadmap, and actual code/tests before work. Older R10→R11 handoffs are historical and must not reset implementation.

## Verified source of truth / status

- Repository: private `greatgc-flow/SecondBrain`. No ZIP/artifact handoff or uploads of private evidence, real backup contents, personal data, tokens or cloud credentials.
- Baseline `main` **`24338b2cafbbf010f3319f221bb62658afc57bc8`** (docs-only PR [#32](https://github.com/greatgc-flow/SecondBrain/pull/32) merged after R13-L code PR [#31](https://github.com/greatgc-flow/SecondBrain/pull/31)).
- Exact [post-merge main CI #38047645680](https://github.com/greatgc-flow/SecondBrain/actions/runs/38047645680): **6/6 jobs SUCCESS** (Ubuntu and Windows unit regressions, independent GitHub runner synthetic snapshot producers and Ubuntu→Windows / Windows→Ubuntu consumers). R13-L final PR code CI [#38046745935](https://github.com/greatgc-flow/SecondBrain/actions/runs/38046745935): Ubuntu **260 passed, 2 skipped**; Windows **262 passed**; both cross-OS restores PASS. Separately verify current counts when `main` moves.
- Latest R13-L leaf-identity closure in [R13-L gate](../history/R13L_RECOVERY_MARKER_LEAF_GATE.md), [PR #31](https://github.com/greatgc-flow/SecondBrain/pull/31), docs closure [PR #32](https://github.com/greatgc-flow/SecondBrain/pull/32).
- [R13 issue #11](https://github.com/greatgc-flow/SecondBrain/issues/11) is **OPEN**. All **17 real operator acceptance rows remain NOT_RUN/NO-GO**; even 6/6 synthetic CI cannot close them. Product version **`0.0.0`**, formal release **NO-GO**. Neither GitHub runner artifacts nor caller-supplied hash prove independently administered custody.

## Implemented vertical slices, non-overlapping

1. **R7 Capture**: original byte acquisition into Inbox; no destructive move. `brain_core/capture.py`.
2. **R8 local Writer/Vault**: local single-writer admission and content-addressed publication; no distributed fencing. `writer.py`.
3. **R9 local custody**: RFC8785 hash-linked Acquisition/Custody events, local receipt and fail-closed validation; no trusted external clock. `custody.py`.
4. **R10 checkpoint**: export and verify against caller-supplied external witness; no assertion the witness was independently retained. `checkpoint.py`.
5. **R11 EvidenceObject**: local unsealed object metadata with per-capture Observation/Acquisition/Custody cross-links; dedup of identical payloads does not collapse capture provenance. `object.py`.
6. **R12 local snapshot/restore**: complete R7–R11 source closure, byte inventory + RFC8785 manifest + last marker, isolated no-overwrite restore and read-only verification. `backup.py`.
7. **R13-A–L synthetic/CI hardening**:
   - **A** restored-root local recovery-hold + sentinel; mutating commands must refuse. **B** cross-runner/cross-OS synthetic backup transport.
   - **C** optionally pin independently supplied manifest-body SHA-256; independent authentication is not provided. **D** reject hardlink aliases; **E** reject same-byte source leaf identity drift.
   - **F** fail closed on visible Windows REPARSE/OFFLINE/RECALL stat flags; **G** synthetic operator preflight requiring supplied Capture roster, digest, R10 checkpoint (not actual offsite drill).
   - **H** reject unsafe detached-checkpoint witness/ancestor paths and leaf substitutions. **I** fail closed on unreadable/unsafe recovery-marker presence rather than `Path.exists()` false negatives.
   - **J** reject lexical `..` source/snapshot/target path aliases before normalization. **K** reject byte-identical substitution of snapshot `manifest.json` / `.complete` leaves while reading. **L** reject byte-identical substitution of restored-root `recovery-hold.json` / `recovery-sentinel.json` leaves while reading. These checks are **not atomic directory-swap protection**, a distributed lock or real cloud hydration proof.
- Authoritative code: [CLI](../../profiles/secondbrain/brain.py), [brain_core](../../profiles/secondbrain/brain_core), [schemas](../../profiles/secondbrain/schemas), [tests](../../profiles/secondbrain/tests); synthetic helper scripts `ci_cross_runner_drill.py` and `synthetic_offline_drill.py`.
- R13 step-by-step gates: [docs/history](../history/), especially [R13-L](../history/R13L_RECOVERY_MARKER_LEAF_GATE.md); broader narrative in [roadmap](../roadmap/S1_NEXT.md), [docs index](../README.md), root [README](../../README.md). Historical `docs/reference/` is archival, not a second implementation spec.

## Highest-priority next gate (do not mark done without evidence)

Use [R13 independent restore runbook](../runbooks/R13_INDEPENDENT_RESTORE_DRILL.md) and [17-item operator evidence template](../runbooks/R13_OPERATOR_EVIDENCE_RECORD_TEMPLATE.md), tracking the master acceptance criteria in [issue #11](https://github.com/greatgc-flow/SecondBrain/issues/11).

1. Operator establishes *separately governed* synthetic snapshot storage and separately retained expected manifest digest/witness, with no secrets/snapshots in GitHub.
2. Operator actually removes/disconnects original synthetic source, retrieves independently retained snapshot, verifies digest, restores to an entirely new root, re-verifies all R7–R11 links and R10 checkpoint, proves restored root stays `RECOVERED_READ_ONLY` and records observed **RPO/RTO** rather than CI execution seconds.
3. Confirm independently enforceable writer revocation/lease transfer; do not let source and recovered root act simultaneously as writer. Local advisory recovery markers are removable by an operator and insufficient as a distributed fence.
4. Real Windows NTFS and OneDrive/Google Drive **test-account, synthetic-only** matrix: junction/reparse, NTFS permissions, offline placeholders/cloud hydration, hardlink and alias, cross-volume, conflict/collision/delete/reappear, multiple devices and sync lag. Real power-loss/durable fsync and hostile concurrent parent-path swap need observed tests and explicit limitations. Never test by deleting user production evidence.
5. Evidence and independent reviewer must close each `NOT_RUN` row; failure feedback loop: observed fault → issue → narrow failing test (RED) → minimal fix → full Ubuntu/Windows & cross-runner CI (GREEN) → PR/merge → main CI → operator re-observation. **No unsupported claim** of passing external criteria.

**If independent storage/Windows/cloud/operator access is unavailable:** continue only bounded, evidence-led synthetic hardening or improve safe operator instructions; leave 17 gates **NOT_RUN**, issue #11 **OPEN**, release **NO-GO**. Do not manufacture results, perform fake operator sign-off or create endless R13 suffixes purely for activity. Ask for the minimal real-world setup only when an operational run is genuinely ready.

## Working contract for the next ChatGPT conversation

- Access GitHub connector and **check live main SHA / open PRs / latest 6 CI jobs** first. Compare this baseline to current `main`; never overwrite newer work.
- Read this handoff, issue #11, roadmap/runbook/evidence template, and code/tests before deciding the smallest meaningful next task; prioritize closure of operational acceptance, not another design rewrite.
- Keep **Very Simple**, SSOT, recursive MECE (requirements ↔ code ↔ tests ↔ documentation ↔ operator evidence), one engine per concept, standard mature libraries, minimal tokens/examples, no speculative compatibility promises.
- Use TDD when changing code. Commit only safe sources/tests/docs to a feature branch, PR and verified candidate-bound CI, then merge and check exact new `main` CI. Do not claim push, CI, merge or external drill was completed unless direct tool evidence confirms it.
- No personal or legal source evidence, no credentials or actual archive/ZIP/snapshot files in repo. Cloud integrations and external storage are not to be implicitly authorized; synthetic test accounts only.
- No PyPI/winget/official release before all distinct operational, security/privacy and packaging gates pass. `0.0.0` and **NO-GO** remain until actual sign-off.

## Paste into a new chat

> Continue the private GitHub `greatgc-flow/SecondBrain` from its **current `main`**, not a historical snapshot. First read `docs/handoff/2026-10-10_R13L_TO_R13_OPERATIONS.md` completely, then follow its links to issue #11, `docs/roadmap/S1_NEXT.md`, `docs/runbooks/R13_INDEPENDENT_RESTORE_DRILL.md`, the operator evidence template, current source/tests and CI. Verify live latest SHA, open PRs and exact 6-job Actions status before any change. R7–R13-L synthetic development is complete through baseline `24338b2` (6/6 latest main CI success), but all 17 independent operational acceptance checks are NOT_RUN; release 0.0.0 stays NO-GO. Continue with the smallest evidence-backed next gate, real operator drill only when actual independent resources exist; never claim fake custody/real-cloud/RPO/RTO/fencing PASS. Follow TDD RED→GREEN→PR CI→merge→main CI, recursive MECE, Very Simple, private synthetic data only. Save handoff and outputs directly to GitHub; no ZIP. If blocked, document the blocker and what can genuinely be checked, then give verified links and remaining acceptance items.
