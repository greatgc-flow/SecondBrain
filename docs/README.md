# Documentation map

The project restarted on 2026-10-12. Start with the proposed v0.1 contract below.
These documents define intended behaviour; they do not assert that the new CLI is implemented.

| Document | Purpose |
| --- | --- |
| [USAGE.md](USAGE.md) | Install, six commands, exit codes, troubleshooting, and the JSON contract for AI agents. |
| [design.md](design.md) | Product, six-command walkthrough, files/receipts, search limits, recovery, failures and acceptance. |
| [ci-policy.md](ci-policy.md) | Cost-aware private CI: PR smoke, manual full Windows/Linux matrix, limits and verification. |
| [decisions.md](decisions.md) | Eight short ADRs explaining the restart and deliberately small scope. |
| [Repository README](../README.md) | Restart pointer followed by the frozen earlier project description. |

The controlling decision record is the owner's `sb_plan_v21.md` (2026-10-12, very simple first).
Supporting discussion: `sb_law.md`, `sb_design_cx.out`, `sb_design_ag.out`, `sb_vote_cx.out` and `sb_vote_ag.out`.
These inputs are external discussion files, not additional product specifications.
`sb_plan_v2.md` was referenced by the decision record but unavailable when these docs were written; v2.1 controls scope.

Earlier R7–R13 documentation, handoffs, roadmaps and reference kits remain frozen historical material under `legacy-r13-final`.
Their implementation claims and next-step instructions apply to that earlier line, not the restarted v0.1.
No files are moved in M0a. Read the new design and decisions before consulting old test cases.

Later ideas are listed without design in [design.md](design.md#later); they are outside v0.1 acceptance.
