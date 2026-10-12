# 31. R1 요구사항 변경 정책 — R2 authoritative amendments

원 R1 요구사항 ID는 삭제하지 않고 역사로 남긴다. 다음 변경이 기존 원문보다 우선한다.

| R1 requirement | 현 문제 | R2 강제 해석 |
|---|---|---|
| REQ-ING-003~004 | 다중 PC 겹침을 idempotent/atomic이라고 과도 주장 | 각 PC capture-only; **단일 Writer**가 canonical publish; 로컬 atomic != cloud-global atomic |
| REQ-ING-005 | 봉인 후 Drop 처리 우회 가능 | verified receipt + 보존 정책 충족 전 source 파일 삭제 금지 |
| REQ-EVD-015 | event serialization OPEN | JCS RFC8785 + per-stream seq + independent anchors |
| REQ-EVD-017 | Evidence 삭제만 거부 | matter predicate와 linked derivatives/production/backup 영향까지 hold propagation |
| REQ-OPS-005 | backup 검증 의미 불명확 | source vs secondary byte verify PASS, cloud upload 별도 unverified/synced |
| REQ-SHD-004 | 외부 TSA 붙이면 자동으로 확실한 날짜라고 오해 가능 | TSA 인증서/응답 검증, 사용 시점 및 token 보관, 파일 생성시점 입증과 분리 |
| REQ-KNW-003 | VERIFIED를 모델이 자유롭게 선언 가능 | independent human/tool verification evidence required |
| REQ-AI-005 | 승인 경계 추상적 | explicit actor/expiry/scope/recipient egress approval and deny by default |
| config.default_erl = ERL-3 | 독립 snapshot 없는데 과대등급 | `target_erl=ERL-3` and `initial_erl=ERL-0`; actual ERL derived |
| OD-007 | 모든 장치 ingest 허용 | **CLOSED:** designated Writer only; other PC capture-only |
| OD-001 | UUID algorithm OPEN | **CLOSED:** UUIDv7 (RFC9562); collision re-roll and uniqueness check |
| OD-002 | JCS OPEN | **CLOSED:** RFC8785 JCS |
| OD-003 | Object path OPEN | **CLOSED:** `/sha256/aa/bb/<digest>/payload` |
| OD-004 | snapshot choice OPEN | **CLOSED:** directory snapshot for backup, BagIt v1 for export |
| OD-005 | Encryption OPEN | Deployment policy decision; no product encryption capability R2 |
| OD-006 | vault scope OPEN | Obsidian default Knowledge/Context UX, Evidence read-only browse |

모든 R1 `MAY`는 core 구현 초기 필수가 아니다. `SHOULD` 미구현은 documented deferment 필요. `MUST`/`MUST NOT`은 보안/무결성 조건이므로 release gate 강제.
