# 36. 측정·관측·경보·운영예산

## 최소 SLI (정의/분모/수집원 분리)
| SLI | 정의 / 분모 | 관측원 | 권고 조치 (목표값은 pilot 이후) |
|---|---|---|---|
| canonical_integrity | PASS verified objects / expected objects; missing도 별도 | deterministic verify | 불일치 1건 = P0, write freeze & triage |
| restore_success | end-to-end restore + lineage + hold PASS / drill runs | receipt + operator | 실패 1건 = release freeze |
| legal_hold_enforcement | prevented forbidden deletes / attempted forbidden deletes | policy test + audit | 금지 파기 1건이면 P0 |
| confidential_egress | unapproved external requests sent (COUNT) | local policy gate | nonzero P0, incident response |
| provenance_coverage | complete capture metadata + limits / observed captures | evidence metadata | incompleteness sample stratified review |
| ingest_latency_p95 | commit latency by volume/profile, excludes provider upload | deterministic receipts | size-based SLO measured first |
| backlog_age_p95 | current ingestion queue waiting age by profile | intake manifest | worker pressure response |
| retrieval_precision | verified citations / claims examined | curated evaluation | regress vs frozen baseline = release block |
| retrieval_abstention | appropriately abstained / no-evidence evaluation cases | curated test set | false confident claims = hard block in high-risk workflows |
| incident_recurrence | recurrence-of same root cause / resolved cohort | feedback ledger | repeated class triggers root-cause re-review |

**데이터 품질의 핵심:** privacy/security/hold의 분모가 0이면 `NOT_APPLICABLE`, 절대로 100% PASS로 표기하지 않는다. 관측값 없음은 UNKNOWN, 오래된 측정은 STALE. Sampling이 전량 완전성을 증명하지 않는다.

## 관측 데이터 흐름
- event/metric/log (local only) → redacted normalized observation → SLI computation → policy decision → alert/ticket → action → verified effect.
- `correlation_id`는 capture→seal→backup→derivation→export를 이어주되 Evidence source body를 로그에 넣지 않는다.
- 로그/trace는 cloud sync로 노출하지 않는다. 장기 운영기록에는 digest, event_ref, metric aggregate만 남긴다.
- 상태/비정상: `HEALTHY`, `DEGRADED`, `UNKNOWN`, `STALE`, `BLOCKED`; UNKNOWN은 HEALTHY가 아니다.
- Watchdog `missing expected scheduled run`, `backup snapshot stale`, `index drift`, `unverified export`를 탐지. 경보 채널 미설정 시 UI/CLI exit code로 확인, 외부 전송은 승인 필요.

## 정책
- P0: 원본 해시 불일치, 금지된 외부 전송, hold 위반, verified backup 망실 → writer freeze, 증거 보존, 우선 진단.
- P1: 반복적인 수집 오류, restore drill 실패, 후보 release attestation mismatch → release freeze + remediation.
- P2/P3: 성능/UX/문서 개선 → 측정 기반 backlog.
- 초기 SLO 숫자를 임의로 확정하지 않는다. 첫 30일 파일 크기·자료형·오류별 pilot 후 target/alert-window 승인.
- error-budget는 인간의 업무 부담과 잔여 위험을 함께 고려. 원본 손상/비인가 유출의 고위험 결과를 허용 가능한 error budget으로 정의하지 않음.

## 회고 cadence
매일/각 ingest: commit receipt 검증; 매주: exception trend/backup evidence, 격주: incident/failure class triage; 매월: full fixity + release change review; 분기: 실제 restore and portability drill; 반기: 표준/의존성/데이터 라이프사이클 재검토. 개인정보·법률자료의 강제 재색인은 별도 권한 심사.
