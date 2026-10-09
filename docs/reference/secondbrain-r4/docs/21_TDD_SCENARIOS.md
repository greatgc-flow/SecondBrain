# 21. TDD 입구 — 수락 시나리오 / Negative Tests

이 문서는 **아직 실행 테스트가 아니다**. 테스트 코드를 작성할 때 `traceability/requirements_to_tests.csv`의 모든 P0/MUST를 개별 테스트와 연결한다.

| Scenario ID | Setup | Action | 반드시 관측돼야 할 결과 |
|---|---|---|---|
| TC-SYNC-01 | Writer A, non-writer B | B가 Vault write 시도 | `WRITER_NOT_AUTHORIZED`, no canonical mutation |
| TC-SYNC-02 | 같은 capture_id, payload 동일 | B가 동일 패키지 재접수 | observation/event 중복 없이 reuse |
| TC-SYNC-03 | capture_id 동일, hash 다름 | 재접수 | `IDEMPOTENCY_CONFLICT`, 두 입력 preserve |
| TC-SYNC-04 | 2개 capture_id, byte 동일 | 각각 처리 | object 하나, observations 두 개 |
| TC-SYNC-05 | Device A offline & failover to B | A가 나중에 복귀 | epoch conflict→writes denied |
| TC-TXN-01 | crash at every transaction boundary | recovery | sealed 불완전 표시 금지; 원본 input 생존 |
| TC-TXN-02 | source changed during copy | hash | no seal; quarantine, report source mismatch |
| TC-TXN-03 | target object occupied with wrong bytes | publish | critical failure, never overwrite |
| TC-TXN-04 | valid vault, metadata incomplete | recovery | orphan recover/reconcile with explicit audit |
| TC-EVT-01 | 동일 이벤트 순서 | JCS bytes/hash calculation | stable canonical digest |
| TC-EVT-02 | event history one byte modified | verify chain | chain mismatch & no silent repair |
| TC-EVT-03 | writer attempted fork/duplicate seq | publish | rejected + quarantine |
| TC-SCH-01 | `date-time` invalid, timezone omitted | validate | FormatChecker + semantic check reject |
| TC-SCH-02 | object path `../` or absolute | validate | schema/application reject |
| TC-ERL-01 | only primary hash verified | derive ERL | <= ERL-2 (depending acquisition) |
| TC-ERL-02 | backup incomplete | mark ERL-3 | rejected; status stays unmet |
| TC-HOLD-01 | ACTIVE hold by matter | ingest new linked evidence | hold propagated; delete blocked |
| TC-HOLD-02 | holder released without approved actor | release | rejected / audit |
| TC-BKP-01 | backup payload changed | verify snapshot | FAIL, complete receipt not published |
| TC-BKP-02 | primary conflicted version | restore | plan identifies conflict; no silent overwrite |
| TC-BKP-03 | snapshot 대상 Knowledge 파일이 복사 도중 변경 | source 재해시 | `SNAPSHOT_SOURCE_CHANGED`; no complete receipt / no ERL-3 |
| TC-BKP-04 | primary/secondary가 동일 physical disk | independent-backup 판단 | failure-domain requirement unmet / clear warning |
| TC-SEC-01 | ZIP with `../`, junction or bomb | ingest | quarantine before unsafe extraction |
| TC-SEC-02 | secret in extracted note | log | payload redacted |
| TC-AI-01 | private original, no scoped consent | PeerHub ask | egress blocked; no provider call |
| TC-AI-02 | malicious instruction in PDF | assistant review | treated as data; no policy/tool escalation |
| TC-AI-03 | AI says VERIFIED without evidence | propose promote | refused, human review needed |
| TC-RET-01 | conflicting timestamps / stale claim | retrieve | timestamp and source citations, outdated fact tagged |
| TC-RET-02 | no source matches | answer | uncertainty/abstain; no invented citations |
| TC-EXP-01 | cropped/redacted PDF | export | original lineage+span+redaction+output digest |
| TC-INT-01 | PeerHub not installed | core ingest/retrieve | works normally, integration opt-in |
| TC-INT-02 | PeerHub Core-only present | register addon | no import of legacy task/consensus core paths |
| TC-OPS-01 | Obsidian sync vault accidentally edits original | verify | integrity violation escalated |

## TDD 설계 순서(수정)
T1 Config/path/preflight → T2 Schema v2 semantic validation → T3 Capture-only ingress → T4 Hash/source freeze → T5 Single Writer gate → T6 Content-address object publish/recovery → T7 Observation & idempotency → T8 Canonical journal JCS → T9 Hold propagation → T10 Snapshot+restore → T11 Derivation/Production → T12 Retrieval/attribution → T13 MCP permission/AI egress → T14 PeerHub extension bridge → T15 cloud-like fault simulations → T16 cross-machine restore drill.

## 필수 fault matrix
`disconnected_network`, `offline_conflicted_copy`, `disk_full`, `same_size_modified_bytes`, `mtime_reset`, `symlink_swap`, `ADS_path`, `read_timeout`, `source_deletion_during_copy`, `hash mismatch`, `crash pre/post each commit`, `rewritten journal`, `stale index`, `TSA timeout`, `legal hold active`, `backup partial`, `cloud upload incomplete`, `multi-device split brain`, `malicious prompt injection`, `privacy denied`.

## Exit criteria
모든 MUST/MUST NOT 요구사항은 자동화된 실제 테스트와 연결되어야 하며, 수동 검증이 필수인 cloud provider UI sync 상태/법률 증거 판단은 별도의 manual gate로 분리. 릴리스 PASS는 `docs/30_RELEASE_GATE.md`를 따른다.


## R3 lifecycle negative tests
`quality/lifecycle_scenarios.csv`의 `LC-*` 시나리오를 TDD 이후 자동/수동 게이트에 병합. 실패 후보와 다른 커밋의 테스트 결과, 운영 지표 미측정, 무근거 개선 완료 선언을 승인 불가로 평가한다.
