# Current documentation index (single source of truth)

**Continue in a new chat:** [R10 → R11 verified handoff](handoff/2026-10-10_R10_TO_R11_HANDOFF.md) · [Copyable R11 start prompt](handoff/START_NEW_CHAT_R11.md). Check latest `main` SHA/CI first.

1. **Current implementation:** `profiles/secondbrain/brain.py`, `brain_core/`, `schemas/`, `tests/`.
2. **Current user guide:** `profiles/secondbrain/R13_RECOVERY_SCOPE.md` (recovery quarantine), then `R12_BACKUP_QUICKSTART.md` / `R12_SCOPE.md`, R11 and earlier guides.
3. **Current release facts:** `docs/history/R13_DEV_GATE.md` (local safety + Windows CI) and `R12_GATE.md` (prior snapshot gate). Live run/SHA verification is authoritative. Operational R13 #11 is **still open**.
4. **Next action:** `docs/roadmap/S1_NEXT.md`: independently controlled restore drill, external writer fencing, and real platform/cloud fault tests.
5. **Archived design and generic kit:** `docs/reference/README.md` and `docs/reference/SOURCE_INVENTORY.json` (read-only historical references, not code generation instructions and not an alternate normative spec).

Documentation that asserts a product feature is implemented must cite a source file, a runnable test and a candidate-bound CI result. **Never interpret historical requirements or planned test catalog IDs as implemented tests.**
