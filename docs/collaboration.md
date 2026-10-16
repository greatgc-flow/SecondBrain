# Collaboration workflow, debate log and provenance

Canonical for how the three AI peers and the coordinator work on this repository. Short rules for agents are in [AGENTS.md](../AGENTS.md).
The current gate is recorded only in [status.md](status.md) (canonical). Work is ANALYSIS/DESIGN ONLY until the owner gives an explicit go. Nothing here is frozen until all three peers assent to the same candidate digest and file list (the 9-file core scope in [AGENTS.md](../AGENTS.md)).

## Workflow

1. **Frame.** The coordinator states the question and the authority (owner instruction or accepted ADR).
2. **Propose.** Each peer returns a vote (AGREE / AGREE-with-change / BLOCK) with reasons. Any reasoned BLOCK holds the candidate; it need not be fatal or carry a counterexample.
3. **Delta rounds.** Rounds repeat on the remaining differences only, until unanimity. There is no round cap; each call is bounded.
4. **Author.** One peer (this phase: `cc`) writes the agreed text. No other peer edits those files meanwhile.
5. **Review.** A non-editor (`cx`, then `ag` for Git facts) reviews the candidate. Review records the exact file hashes it saw.
6. **Freeze or revise.** Freeze only on independent assent to the same hashes. Any later edit reopens review.
7. **Implement (later).** Test-first implementation starts only after the unanimous freeze and an explicit go from the owner alone; the coordinator cannot authorize it independently.

Gates, in order: `DESIGN_REVIEW` -> `DESIGN_FROZEN` -> `TDD_M1` -> `M1_ACCEPTED`. Which gate is current is recorded only in [status.md](status.md).

## Roles and effort (agreed Rounds 1-4 and the resource adjustment)

| Peer | Responsibility | Effort |
|---|---|---|
| `cc` | Sole editor of tracked documents on the doc branch; no Git writes. Mechanical drafting of agreed specs: `claude-sonnet-5-5`, medium, at most 2 files per bounded call; high only for unresolved design | medium (high on escalation) |
| `cx` | Independent review of exact hashes; read-only inspection of Git/PR state; configured `gpt-6.1-sol` | medium |
| `ag` | All Git operations; archive tags, bundle, dry-run list, deletions; bounded checks; configured `gemini-3.8-flash` (effort embedded in model name, separate effort field null) | medium, bounded |
| coordinator | Process and relaying; minimal; delegates even small edits | n/a |

Configured profiles: `cc` `claude-sonnet-5-5` with `--effort medium` for mechanical drafting; `cx` `gpt-6.1-sol` medium; `ag` `gemini-3.8-flash` medium; no `ag3P`. Configured targets are not proof; actual models are UNKNOWN and no model proof is recorded. Quota rule (`F` = forecast of future consumption through reset; `F <= R/2` and `R - F >= 20` per window; signed pace separate; insufficient/UNKNOWN forecast allows bounded calls only, which is not compliance), model-evidence rule and language rule: [AGENTS.md](../AGENTS.md). The earlier invented pace ordering is removed. Effort adjustment agreed by all three: `cx` rec-50fd3f05f98d, `ag` rec-319b555b0594, `cc` rec-df0b579f12e6.

Process rules: unanimity needs explicit assent from all three on the exact normative candidate; any reasoned BLOCK holds (not fatal-only). Reviews are independent against exact hashes; the sole editor may transcribe attributed external reviews with exact IDs and hashes, without self-certification. `DESIGN_REVIEW` stays stopped before product TDD until the owner's go; the coordinator cannot bypass it. Artifacts are English; the owner is addressed in Korean. Rounds are unlimited with bounded calls and no caps. Handoff is limited to `docs/HANDOFF.md` plus one line. `.peerhub` remains a local exclude.

## Decisions reached in the debate

Short form; the binding text is in [design.md](design.md) and the ADRs in [decisions.md](decisions.md).

| # | Decision | Where recorded |
|---|---|---|
| C1 | Unlimited rounds with bounded calls (earlier 2- and 3-round caps withdrawn) | AGENTS.md |
| C2 | Writer lock is a persistent OS-released nonblocking lock; never unlinked; no PID or age based stale breaking | ADR 0010 |
| C3 | Lowercase IDs `cap-<yyyymmdd>t<hhmmss>z-<8hex>` with `-2`, `-3` collision suffixes | ADR 0011 |
| C4 | Immutable objects, receipts, config snapshots and manifests: stage complete bytes, then no-replace publish. Raw `O_EXCL` into the final name is withdrawn because a crash leaves a visible partial file | ADR 0010 |
| C5 | Restore targets must be **absent** (the earlier "empty directory" allowance is withdrawn); activation is a same-volume no-replace rename | ADR 0009 |
| C6 | No `--manifest` flag. Recovery from a damaged newest manifest uses a documented isolated mirror; the original backup is untouched | ADR 0012 |
| C7 | Old temp files are never swept (by name, location or lock). A command removes only handles it created itself; failed stages are retained and reported | ADR 0010 |
| C8 | Directory redirects (symlink, junction) are rejected; hydrated cloud regular files are accepted; `nlink == 0` on backup files warns; unavailable bytes fail with exit 2 | ADR 0013 |
| C9 | JSON envelope, stable codes, exit precedence 2 > 1 > 0, literal-token search, receipt-byte index fingerprint, bounded PDF extraction | ADR 0014 |
| C10 | Git: archive tags are kept (immutable, one namespace, pushed, verified); reviewer dry-run gate and a fresh PR head/base check precede any deletion | [git-inventory.md](git-inventory.md) |
| C11 | S2-S5 and PR46/PR47 are a reference prototype, not an approved baseline | [status.md](status.md) |

### Positions the author reversed (with reason)

| Earlier position (`cc`) | Now | Reason |
|---|---|---|
| Stale-lock handling by PID | OS-released lock, no breaking | PID reuse and clock/age guesses can break a live writer |
| `open` overwrites an existing working copy | Fresh `cache/open/<id>/<n>/` per call, never deleted | Overwrite destroys user edits |
| Restore into an empty directory | Restore to an absent path | Windows cannot rename onto an existing directory; remove-then-rename races; a half-restored root would look valid |
| Name-based sweeping of old temp files | No sweeping | A lock proves no cooperating writer, not ownership of a user-created file |
| Raw `O_EXCL` into the final name | Stage, then no-replace publish | Crash exposes a partial file at a final name |
| Optional `restore --manifest NAME` | Dropped | Isolated mirror recovery needs no flag change; keeps the frozen flag set |
| Archive tags redundant | Tags kept | Owner safety preference; cheap and immutable |

## Provenance and exact record IDs

Stream provenance (no replay; no invented positions):

- Old `cc` stream `secondbrain:council:cc` is `blocked_uncertain`, preserved for audit. The slow high-effort authoring call `rec-aae4f52985c5` timed out at 420 s; termination was confirmed and the filesystem was reconciled for only `AGENTS.md` and `docs/collaboration.md`. A new stream followed without a full replay.
- Current author stream: `secondbrain:docs:cc:2` (a distinct process vote, not a replay). Actual models of all sources are UNKNOWN.
- Workflow review observed: `ag` rec-af77bd6a162f BLOCK, fixed in the workflow text.
- `cx` AGREED design: `rec-c615550dc787`, stream `secondbrain:council:cx`. `ag` AGREED: `rec-18fbb24a1282`, stream `secondbrain:council:ag`. `cc` Round 4: `rec-bd070772e0af`, old stream.
- Workflow adjustment IDs: `cx` rec-50fd3f05f98d, `ag` rec-319b555b0594, `cc` rec-df0b579f12e6.
- Guide pin: `32c5e1f1258418d0324908f338c646e9602b6716`, Standard 1.7.0.

Records visible to `cc` when this pack was written (old `cc` stream as relayed; record numbers are in-stream positions):

| Position | Record ID | Author | Kind | Content |
|---|---|---|---|---|
| 7 | `rec-24f30b02d004` | `cc` | `context.boundary` | Binding change; catch-up of positions 1-5 (21151 of 24000 bytes) |
| 8 | `rec-a95c730d0c70` | `cc` | `response` | Round 3 votes and design decisions D1-D12, Git policy, document plan |
| 9 | `rec-9648ec5513f9` | `secondbrain-coordinator` | `prompt` | Round 4 delta request (no authoring) |
| 10 | `rec-bd070772e0af` | `cc` | `response` | Round 4 explicit AGREE on the delta choices |

The Round 4 authoring authorization arrived as a coordinator prompt after position 10; its record ID was not visible to `cc` and is not invented here.
Positions 1-6 were summarized out of `cc`'s context and are not cited. The `cx` and `ag` AGREE/BLOCK statements are known to `cc` only as relayed by the coordinator; their own record IDs are **UNKNOWN to this author** and should be added by the peers.

### Provenance gap

The owner's decision record `sb_plan_v21.md`, which earlier text calls the controlling scope document, is **absent** from this repository and from the files `cc` could read; its hash is **UNKNOWN**. No hash is invented. The accepted in-repo baseline is `docs/design.md` and `docs/decisions.md` at `main` `5a9fcf44f94a614649a3633e3c0df75f07f69b8f`, combined with the owner's current broad authorization to improve earlier decisions (recorded in the Round 4 prompt). `sb_plan_v2.md` was already unavailable earlier.

### Version mismatch observed

Three version strings appear: `0.0.1` (`pyproject.toml` and `src/secondbrain/__init__.py`), `0.1.0` (sample receipt in the old design), `0.0.0` (historical root README, "NO-GO"). The design fixes one source of truth: `secondbrain.__version__` ([design.md](design.md#versioning)). `0.1.0` in examples is illustrative only.

## Review records

### Hash scope (no circularity)

The **normative candidate hash set** is exactly 9 files: `AGENTS.md`, `docs/collaboration.md`, `docs/design.md`, `docs/decisions.md`, `docs/requirements.md` and `docs/schemas/{receipt,config,manifest,cli-output}.v1.schema.json`. `docs/status.md`, `docs/HANDOFF.md`, human readmes, CI policy and git-inventory are explanatory or evidence records: they attest the core hashes and are never part of their own hash set. The final attestation lives in `status.md`. Nothing is frozen until all three peers explicitly assent to the same digest and file list. The final core hash is PENDING until the independent reviews.

### Records

Reviews are independent against exact hashes. The sole editor may transcribe original peer reviews with their record IDs; that is not self-approval. Rows below are **HISTORICAL** transcriptions of superseded candidates, not the current gate; no current votes are recorded here. The canonical final attestation is in [status.md](status.md).

| Reviewer | Candidate hashes reviewed | Verdict (historical) | Record ID |
|---|---|---|---|
| `cx` | `design.md` `7EBD3E48…E8E2`, `decisions.md` `98F8C108…7534` (superseded candidate) | BLOCK with 7 amendments, applied in a later candidate | `rec-f6b3f24f1762` |
| `ag` | workflow candidate (hashes not relayed to this author) | BLOCK on workflow; correction applied | `rec-af77bd6a162f` |
