# Quality evidence registry
`STATIC_AUDIT_RESULTS.json` is historical R2 result, **not** R3 proof. R3-specific results will be written to `R3_STATIC_AUDIT_RESULTS.json` and `R3_CROSS_TRACE.json`. `lifecycle_scenarios.csv` are **planned** tests; not executed. Never treat scenario count or fixture structural validity as passing G1~G7. When TDD starts, collect code+run output+candidate hashes and append live release gate evidence separately.

Current R3 static result is generated at package build; do not confuse it with validated runtime gates. The `quality/STATIC_AUDIT_RESULTS.json` is retained historical R2 evidence only.
