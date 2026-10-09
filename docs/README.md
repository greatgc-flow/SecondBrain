# Current documentation index (single source of truth)

**Continue in a new chat:** inspect private GitHub latest `main` SHA, open PRs and Actions first, then follow [R13-D developer gate](history/R13D_HARDLINK_GATE.md), [current roadmap](roadmap/S1_NEXT.md), and [R13 operational issue #11](https://github.com/greatgc-flow/SecondBrain/issues/11). Historical R10→R11 handoff prompts are not today's implementation SSOT.

1. **Current implementation:** `profiles/secondbrain/brain.py`, `brain_core/`, `schemas/`, `tests/`.
2. **Current user guide:** `profiles/secondbrain/R13C_DETACHED_DIGEST_QUICKSTART.md` (optional manifest pin), `R13_RECOVERY_SCOPE.md` (recovery quarantine), then `R12_BACKUP_QUICKSTART.md` / `R12_SCOPE.md`, R11 and earlier guides.
3. **Current release facts:** `docs/history/R13D_HARDLINK_GATE.md` (static hardlink refusal and limits), `R13C_DETACHED_DIGEST_GATE.md` (operator-supplied manifest digest, not authenticated independently), `R13B_CROSS_RUNNER_GATE.md` (synthetic cross-OS transfer) and `R13_DEV_GATE.md` (local quarantine), then `R12_GATE.md`. Live run/SHA verification is authoritative. Operational R13 #11 is **still open**.
4. **Next action:** `docs/roadmap/S1_NEXT.md`: independently controlled restore drill, external writer fencing, and real platform/cloud fault tests.
5. **Archived design and generic kit:** `docs/reference/README.md` and `docs/reference/SOURCE_INVENTORY.json` (read-only historical references, not code generation instructions and not an alternate normative spec).

Documentation that asserts a product feature is implemented must cite a source file, a runnable test and a candidate-bound CI result. **Never interpret historical requirements or planned test catalog IDs as implemented tests.**
