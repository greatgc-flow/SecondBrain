# Documentation map

SecondBrain v1 starts from the approved renewal documents:

| Document | Purpose |
| --- | --- |
| [Design r8](renewal/DESIGN.md) | Data contract, workflow, invariants, and acceptance tests. |
| [Implementation plan](renewal/IMPL_PLAN.md) | Ordered slices, file boundaries, and review gates. |
| [Brief](renewal/BRIEF.md) | Owner requirements. |
| [Rubric](renewal/RUBRIC.md) | Requirement and invariant scores, maintained by the orchestrator. |

CI runs the full Ubuntu/Windows × Python 3.11/3.13/3.15 matrix on pushes to
`main` and `renew/**`, on pull requests, and on manual dispatch. The old
private-allowance policy (`ci-policy.md`) has been deleted.

Slice 0 provides the package and test bootstrap. Characterization and
implementation follow in later slices. See the [repository README](../README.md)
for development commands and the history note.
