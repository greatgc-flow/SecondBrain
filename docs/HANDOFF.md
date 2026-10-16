# HANDOFF

Mutable resume record, 2026-10-16 UTC. Gate, digest and evidence: [status.md](status.md) (canonical). Read this file in any new chat.

## Where things are

| Item | Location |
|---|---|
| Repo | `C:/AI/workspace/SecondBrain` (local branch `docs/v01-design-readiness-20261016`) |
| Guide | `C:/AI/workspace/VerySimpleGuide`, pin `32c5e1f1258418d0324908f338c646e9602b6716`, Standard 1.7.0 |
| External Git backup | `C:/AI/workspace/SecondBrain-archives/20261016/backup-all-20261016.bundle` (hash in [git-inventory.md](git-inventory.md)) |
| PeerHub DB | `C:/AI/workspace/SecondBrain/.peerhub/core.db` (local, never committed) |

## Authority

Rules: [AGENTS.md](../AGENTS.md), [collaboration.md](collaboration.md). Contract: [design.md](design.md), [decisions.md](decisions.md), [requirements.md](requirements.md), [schemas/](schemas/). Git policy and facts: [git-inventory.md](git-inventory.md). CI policy: [ci-policy.md](ci-policy.md).

## State

- The 9-file core candidate (digest in status.md) has explicit AGREE from `cx` (`rec-25155660e03d`), `ag` (`rec-08a5a7abe2bc`) and `cc` (`rec-c69779f0979f`, final acceptance `rec-d75efe76cd41`; digest verified externally by `cx` and `ag`). Gate: DESIGN_FROZEN / PRE_TDD_READY. Earlier candidate `8f8d11fa…` votes are superseded.
- Implementation is **not authorized and not started**; the owner's TDD go does not exist yet. Operational gates (real cloud, OS/Python matrix, drills) are NOT_VERIFIED. No merge now.

## Safe Git policy

Preserve branches, tags and PRs. No force-push, merge or deletion without owner authorization. `ag` owns Git operations. PR46/PR47 stay open; reconcile the `docs/STATUS.md` case collision before any merge. S1-S5 is an unverified reuse prototype, not a baseline.

## PeerHub

Streams: `cx` `secondbrain:council:cx`; `ag` `secondbrain:council:ag`; `cc` `secondbrain:docs:cc:2` (medium, writable workspace `C:/AI/workspace`). The old `cc` stream `secondbrain:council:cc` is `blocked_uncertain` (420 s timeout, termination confirmed, only two workflow files reconciled); it is preserved and never auto-replayed. Each new task is distinct and bounded. Use a separate `--db` for `ask` when needed. No secrets or profile config edits.

## Next actions

1. Publication is complete: initial reviewed delivery commit `e952781883f4d688535a991c2b0721841ce347aa` on `docs/v01-design-readiness-20261016`, DRAFT [PR48](https://github.com/greatgc-flow/SecondBrain/pull/48); evidence in [status.md](status.md). A later metadata follow-up commit changes HEAD, so check the live HEAD and PR state before any work.
2. WAIT for the owner's explicit TDD go. Do nothing in `src/`, `tests/`, `scripts/`, `.github/` or `pyproject.toml` before it. Refresh quota evidence before future work.

## Resume prompt (one line, for a new chat)

`Resume SecondBrain: read C:/AI/workspace/SecondBrain/docs/HANDOFF.md and status.md, check PeerHub state, and hold implementation until the owner gives an explicit TDD go.`
