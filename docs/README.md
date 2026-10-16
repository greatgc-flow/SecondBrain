# Documentation map

The project restarted on 2026-10-12. These documents define the intended v0.1 behaviour; they do not assert that the new CLI is implemented. The current gate is recorded only in [status.md](status.md).

| Document | Purpose |
|---|---|
| [design.md](design.md) | Target contract: files, receipts, locks, six commands, search, backup/restore, failures, acceptance |
| [decisions.md](decisions.md) | ADRs: decisions and reversals |
| [requirements.md](requirements.md) | Numbered requirements, planned tests, evidence status, guide applicability |
| [schemas/](schemas/) | Receipt, config, manifest and CLI-output JSON Schemas |
| [status.md](status.md) | Current gate and evidence (canonical, mutable) |
| [HANDOFF.md](HANDOFF.md) | Resume record |
| [collaboration.md](collaboration.md) | Workflow, debate log and provenance (rules: [../AGENTS.md](../AGENTS.md)) |
| [ci-policy.md](ci-policy.md) | Cost-aware private CI |
| [git-inventory.md](git-inventory.md) | Git policy and inventory |
| [../README.md](../README.md) | Project orientation |

## Authority

- **Schemas** own serialization: field names, types and structural shape. They are structural only; their `$comment` fields list the semantic checks a parser must add.
- **Prose** ([design.md](design.md), [requirements.md](requirements.md)) owns semantics: behaviour, ordering, failure handling.
- **ADRs** record policy changes and reversals. A decision that changes policy must be synchronized into the design, requirements and schemas in the same candidate.
- [status.md](status.md) and [HANDOFF.md](HANDOFF.md) are evidence records, not specifications.

## Provenance

The earlier external plan `sb_plan_v21.md` is absent from this repository and its hash is UNKNOWN; the in-repo documents and the owner's current direction control. Discussion files (`sb_law.md`, `sb_design_*.out`, `sb_vote_*.out`) are external, non-authoritative inputs.

## History

Earlier R7-R13 documentation and code are frozen under [../legacy/README.md](../legacy/README.md) and the tag `legacy-r13-final`; their claims do not apply to v0.1.
Later ideas are listed without design in [design.md](design.md#later); they are outside v0.1 acceptance.
