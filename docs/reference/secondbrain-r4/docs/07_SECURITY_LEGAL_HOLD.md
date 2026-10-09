# 07. Security / Legal Hold / Threat Model

## 1. 보호 대상

- Evidence original bytes
- hash manifests
- custody journal
- acquisition records
- provenance
- Legal Hold records
- production lineage
- backup snapshots

---

## 2. 주요 위협

| Threat | 영향 | 기본 대응 |
|---|---|---|
| 실수로 원본 편집 | 원본성 쟁점 | Vault 분리 + digest verify |
| cloud conflict | divergent copies | content identity + conflict 보존 |
| ransomware | 원본/동기화본 오염 | Secondary snapshot + offline option |
| silent corruption | bytes 변경 | periodic full fixity |
| index corruption | 검색 오류 | index rebuild |
| AI hallucination | 잘못된 사실 승격 | provenance tier + human/policy gate |
| metadata overwrite | 과거 상태 소실 | event history |
| legal hold bypass | 증거 파기 위험 | centralized hold check |
| multi-device double ingest | duplicate/corruption | idempotent object resolution |
| clock skew | 사건 시각 오해 | source time / observed time / recorded time 분리 |
| cloud placeholder | 불완전 hash | hydration gate |
| secret leakage | 개인정보/토큰 노출 | secret exclusion/redaction policy |
| sync deletion propagation | backup 동시 삭제 | Secondary snapshot, not live mirror |

---

## 3. Legal Hold

구조:

```text
10_Evidence/LegalHold/<hold_id>/
├─ hold.json
├─ scope.json
└─ events.jsonl
```

상태:
```text
DRAFT
ACTIVE
RELEASED
```

ACTIVE이면:
- canonical object delete 금지
- observation/custody delete 금지
- production delete는 정책에 따라 제한
- derived cache는 삭제 가능하되 원본 lineage 영향 없어야 함

release는 event로 남긴다.

---

## 4. Hash-chain journal

각 custody event:

```text
event_hash = SHA256(canonical_json(event_without_event_hash))
```

그리고:
```text
previous_event_hash
```
를 포함한다.

canonicalization 규칙은 TDD 전에 별도 결정이 필요하므로 ADR에서 JSON Canonicalization Scheme(RFC 8785) 채택 여부를 OPEN 항목으로 둔다.

---

## 5. Timestamp

ERL-4에서 RFC 3161 형태의 trusted timestamp를 선택 지원한다.

원칙:
- 파일 전체를 TSA에 보내지 않음
- cryptographic digest를 timestamp
- request/response token 자체도 canonical file로 보존
- TSA failure가 ingest 전체를 실패시키지 않음
- ERL-3 완료 후 ERL-4 승격 작업으로 분리

---

## 6. Filesystem immutability

R1은 일반 OneDrive/Google Drive 폴더를 사용하므로 진정한 WORM을 주장하지 않는다.

정확한 목표:
> 변경을 절대 불가능하게 만드는 것이 아니라, 무단/실수 변경을 높은 신뢰도로 탐지하고 정상 사본으로 복구할 수 있게 한다.

추가 강화:
- read-only attribute
- ACL
- 별도 backup
- 외부 TSA
- offline media

는 MAY/SHOULD 영역이다.

---

## 7. Sensitive data

metadata에는:
- password
- auth token
- provider refresh token
- private key
를 넣지 않는다.

개인정보/사건자료는 cloud sharing 정책과 별개로 운영자가 접근권한을 관리해야 한다.

## R2 security override
All untrusted sources guarded by parser isolation, path controls, prompt injection defense, default-deny sensitive AI egress. Hold predicate expands to subsequently linked matter evidence; hash-chain external anchor needed to detect whole-history replacement. 세부 `docs/19_SECURITY_PRIVACY_AI.md`, `docs/20_BACKUP_RETENTION.md`.
