# SecondBrain v0.1 requirements and verification plan

Phase: **DESIGN_REVIEW**. Contract: [design.md](design.md), [decisions.md](decisions.md), [schemas/](schemas/). Nothing here claims implementation or a passing test.

## Reading the matrix

- Planned test names (`test_*`) are PLANNED, not run and **not counted as passed**. Files are chosen at TDD time. Currently only 15 stub tests exist; RED/GREEN has not been executed.
- Implementation reference: `NOT_IMPLEMENTED (stub)` for the current code, or a future module marked PLANNED.
- Evidence: `NOT_YET` (not run) or `NOT_VERIFIED` (needs a real environment). A fake PASS is not allowed.
- Owner = project role responsible for the boundary: `cc` author, `cx` reviewer, `ag` Git/CI facts, `product owner` (explicit future decisions). `cc` is the owner as the current design author; implementation owners are reassigned before TDD starts. All requirements apply to v0.1 unless stated.
- Guide guidance is pinned and used for scoped alignment; no full validator run is claimed.
- The root holds no object counters; index freshness uses receipt metadata fingerprints only.
- Delivery tooling (PeerHub, quotas, model choice) is separate from PRODUCT_RUNTIME, which is offline: no app daemon, provider or network.

## Requirements

| ID | Requirement | Owner | Acceptance / falsification | Planned test or drill | Impl ref | Evidence |
|---|---|---|---|---|---|---|
| SB-001 | Exactly six commands and the agreed options | cc | Falsified by any extra command or flag | test_cli_exposes_only_six_commands | PLANNED secondbrain.cli | NOT_YET |
| SB-002 | `--help` and usage errors have no filesystem effect | cc | Falsified if any file appears | test_help_creates_nothing | PLANNED secondbrain.cli | NOT_YET |
| SB-003 | JSON envelope has exactly status/results/errors; ok ⇒ no errors, error ⇒ ≥1 | cc | Schema validation of ok and error samples | test_json_envelope_schema | PLANNED secondbrain.output | NOT_YET |
| SB-004 | Error and warning codes from cli-output.v1 only; stdout holds only the JSON object | cc | Any extra stdout text or unknown code fails | test_stdout_only_json_object | PLANNED secondbrain.output | NOT_YET |
| SB-005 | Exit precedence 2 > 1 > 0 | cc | Mixed 1+2 failures exit 2 | test_exit_precedence | PLANNED secondbrain.cli | NOT_YET |
| SB-006 | All six result types carry structured `warnings[]`; human text to stderr | cc | Warning present per result under `--json` | test_warnings_structured_per_result | PLANNED secondbrain.output | NOT_YET |
| SB-007 | Config defaults `backup_root: null`; schema-valid; absence invalid | cc | config.v1 accepts null/string, rejects absent/extra | test_config_default_null_valid | PLANNED secondbrain.config | NOT_YET |
| SB-008 | First data command initializes the active root under lock; restore never initializes the global root | cc | Restore leaves default root untouched | test_restore_does_not_init_active_root | PLANNED secondbrain.root | NOT_YET |
| SB-009 | Receipt has six fields, schema-valid, parser rejects duplicate keys/BOM/NaN | cc | receipt.v1 valid/invalid corpus | test_receipt_schema_and_strict_parse | PLANNED secondbrain.receipt | NOT_YET |
| SB-010 | Lowercase id, `-2`,`-3` collision suffixes, no counter; filename = id | cc | Same-second same-hash capture yields `-2` | test_id_format_collision_suffix | PLANNED secondbrain.ids | NOT_YET |
| SB-011 | Identical bytes share one object; each acquisition has its own receipt | cc | Two captures: one object, two receipts | test_acquisition_dedupe | PLANNED secondbrain.capture | NOT_YET |
| SB-012 | Source coherence via one handle, identity/size/mtime and pathname check; ordinary mutation only | cc | Mutated source fails `source_changed`; no TOCTOU claim | test_source_change_detected | PLANNED secondbrain.capture | NOT_YET |
| SB-013 | Reject overlapping paths, actual redirects (symlink, junction, redirecting reparse tags, linked directories), special files and unsafe output names; accept hydrated NTFS cloud-tag regular files for capture and backup; offline bytes exit 2; active root stays unsynced (local NTFS on Windows; on Ubuntu an explicit `--root` on an unsynced local filesystem with required locks and atomic no-replace, else exit 2 `unsupported_platform`) | cc | Redirect/overlap/special cases exit 2 `unsafe_path`; hydrated cloud regular file captured; offline file exits 2 | test_path_safety_matrix, test_source_hydrated_cloud_regular, test_source_redirect_rejected, test_source_offline_unavailable (synthetic) | PLANNED secondbrain.paths | NOT_YET |
| SB-014 | `original_name` preserved raw; working names NFC and safe | cc | Unicode name round-trips in receipt, safe copy name | test_original_name_vs_working_name | PLANNED secondbrain.paths | NOT_YET |
| SB-015 | Sources never modified; synthetic data only; no network; plain files disclosed as unencrypted | cc | Source hash/mtime unchanged; no socket use | test_source_untouched_offline | PLANNED secondbrain.capture | NOT_YET |
| SB-016 | `writer.lock` persistent, nonblocking, OS-released, never unlinked; contention exits 2 | cc | Two processes: second exits 2; lock file survives | test_writer_lock_exclusion | PLANNED secondbrain.locks | NOT_YET |
| SB-017 | Stage, flush, no-replace publish; object before receipt | cc | Injected crash leaves no partial final file | test_publish_stage_noreplace | PLANNED secondbrain.publish | NOT_YET |
| SB-018 | Orphans preserved; verify exits 1; backup rejects | cc | Orphan object reported, not deleted | test_orphan_handling | PLANNED secondbrain.verify | NOT_YET |
| SB-019 | Cleanup only with ownership and identity evidence; no sweeping | cc | Foreign temp file with matching name survives | test_cleanup_requires_identity | PLANNED secondbrain.publish | NOT_YET |
| SB-020 | Folder capture recursive, sorted, partial; any failure forces exit 2; empty folder exits 0 | cc | Mixed folder yields results and errors, exit 2 | test_folder_capture_partial | PLANNED secondbrain.capture | NOT_YET |
| SB-021 | Index fingerprint over receipt paths and byte digests; stale/corrupt rebuild; rebuild failure exits 2 | cc | Corrupt index rebuilt; locked DB exits 2 | test_index_rebuild_fingerprint | PLANNED secondbrain.index | NOT_YET |
| SB-022 | FTS query is literal AND tokens, quotes escaped, no raw operators, deterministic, limit 100 with truncation warning | cc | `OR`/`*`/quote queries behave literally | test_fts_query_escaping_limit | PLANNED secondbrain.search | NOT_YET |
| SB-023 | Korean NFC search and a recorded benchmark of limits | cc | Benchmark table with expected vs actual hits | drill: korean_benchmark | PLANNED secondbrain.search | NOT_VERIFIED |
| SB-024 | Text/PDF extraction bounded; unenforceable limits skip with warning; capture unrestricted | cc | Oversized/hanging PDF yields warning, names searchable | test_extraction_limits | PLANNED secondbrain.extract | NOT_YET |
| SB-025 | `open` verifies object, copies fresh unique path, verifies copy; tampering blocks | cc | Edited object blocks open; earlier copies untouched | test_open_fresh_verified | PLANNED secondbrain.open | NOT_YET |
| SB-026 | `--print-path` output (plain or JSON); launch failure exits 2 | cc | Path only on stdout; failure code 2 | test_print_path_and_launch_failure | PLANNED secondbrain.open | NOT_YET |
| SB-027 | Verify closure and singleton summary with invalid counter | cc | Missing/corrupt/orphan/invalid counted | test_verify_summary_closure | PLANNED secondbrain.verify | NOT_YET |
| SB-028 | Backup locks destination then source; config derived and revalidated under locks | cc | Concurrent config change exits 2 | test_backup_lock_order_config | PLANNED secondbrain.backup | NOT_YET |
| SB-029 | Backup tree and manifest strictly parsed; one config; object set equals receipt references | cc | manifest.v1 plus semantic corpus | test_manifest_strict_semantics | PLANNED secondbrain.manifest | NOT_YET |
| SB-030 | Every written or reused backup copy hash-verified | cc | Corrupt reused file detected | test_backup_hash_reused | PLANNED secondbrain.backup | NOT_YET |
| SB-031 | Manifest published last, then config persisted; save failure keeps backup result and `config_persist_failed` | cc | Injected failure after manifest: exit 2, result retained | test_backup_config_transaction | PLANNED secondbrain.backup | NOT_YET |
| SB-032 | Manifest name equals created_utc UTC portion, canonical suffix ≥ 2, numeric ordering, unexpected entries are integrity errors | cc | `-10` newer than `-2`; stray file exits 1 | test_manifest_names_ordering | PLANNED secondbrain.manifest | NOT_YET |
| SB-033 | Corrupt newest manifest exits 1 without fallback; isolated-mirror recovery documented | cc | Older manifest not used; mirror procedure works | test_latest_corrupt_no_fallback | PLANNED secondbrain.restore | NOT_YET |
| SB-034 | Cloud: hydrated regular files accepted as capture sources and backup inputs, `nlink==0` warns, redirects rejected, unavailable bytes exit 2; real provider behaviour is a manual release gate | cc | Real provider drill (synthetic cases are SB-013) | drill: drive_synced_backup | PLANNED secondbrain.backup | NOT_VERIFIED |
| SB-035 | Restore target must be absent; staged and fully validated | cc | Existing empty directory exits 2 | test_restore_requires_absent | PLANNED secondbrain.restore | NOT_YET |
| SB-036 | Restore maps the sole config entry to staging `config.json` byte-exact | cc | Hash of restored config equals snapshot | test_restore_config_mapping | PLANNED secondbrain.restore | NOT_YET |
| SB-037 | Activation is atomic no-replace; unsupported platform exits 2 | cc | Race creating target during restore: no overwrite | test_activation_noreplace_race | PLANNED secondbrain.restore | NOT_YET |
| SB-038 | Failed restore retains owned staging and never reports success | cc | Injected failure leaves staging, exit 2 | test_restore_failure_retains_staging | PLANNED secondbrain.restore | NOT_YET |
| SB-039 | Post-activation crash leaves destination; rerun refuses and never removes it | cc | Simulated crash then rerun exit 2 | test_restore_postcommit_crash | PLANNED secondbrain.restore | NOT_YET |
| SB-040 | 100 mixed synthetic files: Korean names, spaces, long paths, duplicates, empty, locked | cc | Explicit per-file errors; verify clean | drill: capture_100_mixed | PLANNED acceptance | NOT_VERIFIED |
| SB-041 | Interrupt every publication stage and concurrent capture/backup | cc | Rerun safe; lock exclusion holds | drill: interrupt_and_concurrency | PLANNED acceptance | NOT_VERIFIED |
| SB-042 | Release gates: Windows and Ubuntu, Python 3.11-3.13, offline CI | ag | CI artifact per matrix cell | drill: release_ci_matrix | PLANNED CI | NOT_VERIFIED |
| SB-043 | `__version__` equals build metadata; receipt `tool_version` is semver | cc | Packaging check fails on mismatch | test_version_agreement | PLANNED packaging | NOT_YET |
| SB-044 | No authenticity, admissibility, custody or legal-weight claim anywhere | cx | Text audit of docs and CLI output | drill: claims_audit | n/a | NOT_YET |
| SB-045 | Retire/export is plain-file copy; no automatic deletion anywhere | cc | No delete code path outside own staging | test_no_automatic_deletion | PLANNED review | NOT_YET |

## TDD red plan (after the owner's explicit go)

Order, each step red first and only then green: (1) pure contract: parser, strict JSON, envelope, receipt/config/manifest validation (SB-001..010, 029, 032, 043); (2) publication, locks, capture (SB-011..020); (3) verify and open (SB-018, 025..027); (4) find and index (SB-021..024); (5) backup, then restore (SB-028..039); (6) acceptance and release drills (SB-040..042, 044, 045).
Review the S1-S5 prototype for reuse by mapping each piece to a requirement above; nothing is merged blindly. Test run results are recorded with command, candidate commit, date and result.

## Guide applicability (VerySimpleGuide pin `32c5e1f1258418d0324908f338c646e9602b6716`, Standard 1.7.0)

Controls (15). Owner `cc` unless stated; deferred items name a revisit trigger.

| Control | Status | Reason / revisit |
|---|---|---|
| UPS-CLI | REQUIRED | Six-command CLI, SB-001 |
| UPS-HELP | REQUIRED | `--help` without effects, SB-002 |
| UPS-EXIT | REQUIRED | Exit precedence, SB-005 |
| UPS-CONFIG | REQUIRED | Single `config.json`, SB-007 |
| UPS-LAYOUT | REQUIRED | Root, backup tree, SB-008, SB-029 |
| UPS-SCHEMA | REQUIRED | Four schemas; semantic checks stay in parser |
| UPS-COMP | REQUIRED | Small modules, no framework (0017) |
| UPS-EXT | DEFERRED | No extension points in v0.1; product owner revisits with MCP/import (design "Later") |
| UPS-OBS | REQUIRED | Exit codes, structured warnings and local diagnostics; only optional telemetry collection is out of scope (none) |
| UPS-EVID | REQUIRED | Evidence statuses, hash-bound reviews; cx reviews |
| UPS-SEC | REQUIRED | Path safety, offline, no credentials (SB-013, 015) |
| UPS-MIG | REQUIRED | Receipt/manifest v1 versioning; retire/export SB-045 |
| UPS-TEST | REQUIRED | Sections above; ag owns CI facts |
| UPS-REL | REQUIRED | Gates SB-042, 043; ag owns tags and bundles |
| UPS-DOC | REQUIRED | design, decisions, requirements, guide-style handoff |

Stages (12). State is applicability (REQUIRED / OPTIONAL / N_A / DEFERRED), never a pass; no stage passes because a proposal exists. Owners are current roles; `cc` is the current design author and implementation owners are reassigned before TDD.

| Stage | State | Owner | Reason / revisit |
|---|---|---|---|
| DISCOVER | REQUIRED | product owner | Problem brief rests on the owner-chosen scope and a hypothesis, not empirical user-value proof; acceptance pending |
| ASSESS | REQUIRED | cc | Build vs buy/reuse/do-nothing recorded in 0017 as a claim; owner confirms; acceptance pending |
| INITIATE | REQUIRED | product owner | Roles cc/cx/ag, scope and acceptance authority (unanimous hash-bound assent); acceptance pending |
| SPECIFY | REQUIRED | cc | This file and the schemas; under review |
| DESIGN | REQUIRED | cc | `design.md`/ADRs under DESIGN_REVIEW; not frozen |
| IMPLEMENT | REQUIRED | future implementer (reassigned before TDD) | Waits for the owner's go; acceptance pending |
| VERIFY | REQUIRED | cx | Requirement drills and tests NOT_YET; acceptance pending |
| RELEASE | REQUIRED | ag | SB-042/043 gates NOT_YET; acceptance pending |
| OPERATE_SUPPORT | DEFERRED | product owner | Single-user local tool; revisit at first release |
| IMPROVE | DEFERRED | cc | Revisit when the Korean benchmark or extraction limits cross a recorded threshold (SB-023, 024) |
| EVOLVE | DEFERRED | product owner | Revisit when a v2 receipt/manifest format is needed |
| RETIRE | REQUIRED | product owner | Plan: plain-file export, no automatic deletion (SB-045); executed only at retirement |

Concerns (10). Scope states what is covered; DEFERRED items name a revisit trigger.

| Concern | State | Owner | Scope / revisit |
|---|---|---|---|
| OUTCOME_VALUE | REQUIRED | product owner | Recoverable originals with acquisition context; value is a claim, not measured |
| USERS_ACCESSIBILITY | REQUIRED | cc | Plain-text CLI and JSON; Korean search limits disclosed |
| RISK_SECURITY | REQUIRED | cc | Offline, no credentials, path safety; no TOCTOU or authenticity claim |
| ARCHITECTURE_DEPENDENCIES | REQUIRED | cc | stdlib, SQLite FTS5, `pypdf`; no daemon or framework |
| DATA_PRIVACY | REQUIRED | cc | Plain unencrypted files; cloud backup readable by the provider; synthetic test data; encryption DEFERRED to the product owner (design "Later") |
| QUALITY_ASSURANCE | REQUIRED | cx | This matrix; no counted passes yet |
| RELEASE_SUPPLYCHAIN | REQUIRED | ag | Version agreement and CI gates; real matrix NOT_VERIFIED |
| OPERATIONS_RELIABILITY | REQUIRED | cc | Locks, atomic publish, isolated-mirror recovery |
| ECONOMICS_SUSTAINABILITY | REQUIRED | product owner | Product runtime is offline with no hosted cost; delivery quotas and CI billing remain relevant to the delivery process |
| GOVERNANCE_EVIDENCE | REQUIRED | cx | Unanimous hash-bound assent; ADRs record reversals |

A design artifact can be ready while operational verification stays NOT_VERIFIED; real cloud and OS/Python acceptance are release gates, never pre-marked PASS.
