# AGENTS.md — collaboration instructions for AI peers

Applies to every AI peer working in this repository (`cc`, `cx`, `ag`) and to the coordinator that relays between them.
The owner's instructions override this file. The canonical workflow and its debate log live in [docs/collaboration.md](docs/collaboration.md).
The current gate is recorded only in [docs/status.md](docs/status.md), which is canonical; this file does not fix a phase. Work remains ANALYSIS/DESIGN ONLY: product implementation and TDD stay stopped until the owner gives an explicit go. The coordinator cannot bypass the owner's no-implementation phase.

## Peers, roles and effort

| Peer | Role in the current phase | Configured target (effort) | Actual model |
|---|---|---|---|
| `cc` (Claude) | Sole editor of tracked design/readiness documents; mechanical drafting of agreed specs | `claude-sonnet-5-5`, `--effort medium` for mechanical drafting; high only for unresolved design | UNKNOWN |
| `cx` (Codex) | Independent reviewer of exact candidate hashes; may inspect Git and PRs read-only | `gpt-6.1-sol`, effort medium | UNKNOWN |
| `ag` (Antigravity) | Owns all Git operations (branches, commits, tags, bundle, deletions); bounded checks | `gemini-3.8-flash`, medium (effort embedded in the model name; separate effort field null) | UNKNOWN |
| coordinator | Relays, decides process, stays minimal; delegates even small edits | n/a | n/a |

- Configured targets are configuration, not proof. The actual model stays `UNKNOWN` until a peer shows runtime proof (a tool-reported model id). No fake model proof is recorded. The latest policy's preferred profiles are known; they are preferences, not evidence.
- Effort policy (agreed by all three: `cx` rec-50fd3f05f98d, `ag` rec-319b555b0594, `cc` rec-df0b579f12e6): mechanical drafting of already-agreed specs uses medium effort with at most 2 files per bounded call. High effort is for unresolved design only.
- `ag` does not use the Pro-tier model. `ag` runs with bounded calls only.
- Exactly one peer edits a given tracked file at a time (this phase: `cc`). `cx` and `ag` review independently against exact file hashes and are not required to edit the same files.
- The sole editor may transcribe an attributed external review, with its exact record ID and hashes. Transcription is not self-certification; the editor never certifies its own candidate.
- The coordinator does not hand-edit files, including one-line fixes; it asks the responsible peer.

## Quota rule

Before an optional or expensive call, a peer needs fresh evidence of its own quota window (a measurement taken in this session, not remembered).
For a window with remaining quota `R` (percentage points) and `F` = the forecast of **future consumption through the window's reset** (percentage points), not the forecast of a single call:

- Proceed only if `F <= R / 2` **and** `R - F >= 20`, checked for each window.
- Show the signed pace (used share minus elapsed share of the window) next to the evidence. Pace is reported separately and is not part of the rule.
- No fresh evidence, or `F`/evidence is insufficient or `UNKNOWN`: only bounded calls are allowed (small, single-purpose, no fan-out, no long loops). Bounded operation is not compliance with the rule.

## Debate and decisions

- Unlimited debate rounds are allowed for critical decisions, with bounded calls per round and no caps. The stop condition is **unanimity**: all three peers explicitly assent to the exact normative candidate.
- Any reasoned BLOCK holds the candidate. A BLOCK need not be fatal or carry a counterexample; it must give reasons, and it is resolved in a further round.
- Reasons for reversing an earlier position are recorded in the ADR that carries the change (see [docs/decisions.md](docs/decisions.md)).
- Self-certification does not count. Nothing is frozen until all three peers assent to the **same candidate** (the same digest and file list).
- Normative candidate scope is exactly these 9 files: `AGENTS.md`, `docs/collaboration.md`, `docs/design.md`, `docs/decisions.md`, `docs/requirements.md`, and `docs/schemas/{receipt,config,manifest,cli-output}.v1.schema.json`. `docs/status.md`, `docs/HANDOFF.md`, human readmes, CI policy and git-inventory are explanatory or evidence records, are not in the core hash set, and never hash themselves. The final attestation (hashes, assents, freeze) is recorded in `docs/status.md` without changing the core hashes.

## Language

- All repository artifacts, comments and AI-to-AI messages are in English, including those written for the Korean-speaking owner. Messages between peers stay compact.
- The owner is addressed in Korean. Terminal output for the owner is terse.

## Working rules

- Documentation first. Do not change `src/`, `tests/`, `scripts/`, `.github/` or `pyproject.toml` until the design is frozen and the owner authorizes TDD.
- Never claim a test, CI run or drill passed without a recorded artifact (command, candidate commit, date, result). `NOT_YET`, `NOT_VERIFIED` and `UNKNOWN` are valid statuses; a fake `PASS` is not.
- Preserve branches, tags and PRs unless the Git policy in [docs/git-inventory.md](docs/git-inventory.md) permits deletion. No force-push, no merge without owner authorization.
- Use synthetic data only. Never commit real personal files, credentials, or the raw `.peerhub/` state; `.peerhub` remains a local exclude.
- Scope statements are integrity and recorded context only. Do not add authenticity, admissibility, custody or legal-weight claims.
- Do not add a generic registry, daemon, vendor framework or custody feature to v0.1.

## Handoff near a limit

When a peer approaches a context or quota limit it writes [docs/HANDOFF.md](docs/HANDOFF.md) (current state, absolute paths, hashes, next action) and gives the coordinator **one line** that resumes work from that file. The handoff is limited to that file plus the single line.
