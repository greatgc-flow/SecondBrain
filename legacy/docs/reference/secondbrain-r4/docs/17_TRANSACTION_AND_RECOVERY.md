# 17. 원본 봉인·출판 Transaction / Crash Recovery

## 불변조건
1. input file을 복사하기 전의 출처/발견 맥락이 기록돼야 하며, `first_observed_at`은 시스템 최초 접수시각이지 원본 생성시각이 아니다.
2. `sealed`는 *source copy hashed → local staging copy verified → vault bytes published → vault bytes independently re-read/verified → canonical record committed*를 완료한 상태.
3. 실패/전원중단/디스크 부족에서도 수집 input의 유일 사본은 삭제하지 않는다.
4. 어떤 부분 파일이나 미검증 marker도 `sealed` 상태로 노출 금지. SHA-256 충돌은 사실상 매우 드물지만 **기존 path bytes/hash/size 불일치** 시 절대 덮어쓰지 않는다.
5. legacy/WIP payload를 완전한 원본이라고 표시하지 않는다.

## 동일 호스트 내 Commit protocol
```
CAPTURE_RECEIVED → SOURCE_SNAPSHOT → STAGING_COPY → STAGING_VERIFIED
       → VAULT_PUBLISHED → VAULT_VERIFIED → RECORD_PUBLISHED
       → OBSERVATION_PUBLISHED → ACQUISITION_PUBLISHED
       → CUSTODY_PUBLISHED → COMMIT_RECEIPT → INDEXABLE
```
- Source open 전에 file type/permission/placeholder 검증. File identity(stat/method)가 복사 전후 바뀌면 `SOURCE_CHANGED`.
- Source는 해시를 포함한 스트리밍 복사 1회 + 대상 재독립 재해시. 대용량 경우 비용은 선택 사항이 아니라 증거 수집 강도를 위한 Tradeoff로 문서화.
- `Vault` publication은 temp file과 대상이 같은 physical filesystem일 때만 atomic rename을 가정. Cloud global atomicity나 multi-file transaction이라고 해석하지 않는다.
- 폴더 단위 수집은 snapshot manifest 목록 기준. 수집 중 변경된 파일은 부분 성공/실패 개별 표현.
- 각 record는 write temp → flush → fsync 가능 범위 → rename. 복수 파일 publish는 개별 순차적이며 최종 `commit-receipt.json`가 logical transaction 성립 기준.
- Reader는 committed receipts만 공개. 미완성 partial records는 recovery 대상이고 검색 index에 넣지 않는다.

## Recoverable states
| Crash point | Retry behavior | Original safety |
|---|---|---|
| pre-source-copy | 다시 재수집 | Drop 보존 |
| after staging copy | staging 검증 후 continue 또는 제거/재생성 | Drop 보존 |
| vault published, record 없음 | orphan 검사→동일 hash 면 record 이어쓰기 | Vault 유지 |
| record published, custody 없음 | receipts 확인 후 결손 이벤트 복구, 모호하면 HOLD | Vault 유지 |
| before commit receipt | 오직 verification 기반 재개; 임의 성공처리 금지 | Vault 유지 |
| after receipt, before index | index rebuild | Vault 유지 |
| secondary backup 실패 | `ERL-2` 유지, backup retry; ERL-3 자동표시 금지 | Primary 보존 |

## Collision & retry semantics
- `capture_id`: 동일 요청 재시도 안정 키. 동일 key/상이한 내용은 `IDEMPOTENCY_CONFLICT`.
- `object_id`: `obj-sha256-<digest>`처럼 digest derived identity. 파일 bytes 정체성.
- `evidence_id`: 개별 사건/주장 맥락의 논리적 단위. 한 object가 여러 evidence_id를 가질 수 있음.
- `observation_id`: 새로운 취득 사실당 발급. 동일 시도 복구 시 기존 ID 재사용.
- SHA-512는 이중 검증 보조 digest; SHA-256 contents address의 alternate digest가 아님.

## Canonical event hash
`event_hash=lowerhex(SHA256(UTF8(JCS(event_without_event_hash))))`; JCS=RFC8785, null 포함/제외는 스키마에서 선택하여 이벤트 생성 시 **고정**, `previous_event_hash` 첫 항은 `null`. 스트림별 단일 순서, event stream ID와 증가 counter 필수. 이벤트 발행 후 body 덮어쓰기 금지.
- 시간은 원본에 적힌 시각 / host 관측시각 / 입력 시각 / 가용한 서버검증시각을 분리. clock skew는 `time_quality` 필드로.
- Hash-chain만으로 부정한 관리자에 의한 전체 기록 교체를 막지 못함. 정기 chain-head external/secondary anchor + offline snapshot + 서명은 상위 강화수단.

## Error model
일관된 machine code: `SOURCE_CHANGED`, `NOT_HYDRATED`, `UNSAFE_PATH`, `UNSUPPORTED_ARCHIVE`, `QUARANTINED`, `INTEGRITY_MISMATCH`, `IDEMPOTENCY_CONFLICT`, `WRITER_NOT_AUTHORIZED`, `INCOMPLETE_COMMIT`, `BACKUP_NOT_VERIFIED`, `LEGAL_HOLD_ACTIVE`, `POLICY_DENIED`, `SENSITIVE_EGRESS_DENIED`, `UNKNOWN`.

## Backup boundary note
Snapshot의 순간 일관성은 ingest commit receipts만으로 보장되지 않는다. Knowledge/Context 수정 중 백업은 `docs/20_BACKUP_RETENTION.md`의 quiesce/source-rehash gate를 거쳐야 하며, 실패하면 backup 완료 표시 금지.
