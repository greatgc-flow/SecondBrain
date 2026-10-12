# 22. Recursive MECE Coverage Map

MECE는 **서로 직교한 축을 택해서 점검**한다. 일부 현실의 요건(예: security)은 여러 축과 교차하므로 억지로 하나의 카테고리로 밀어 넣지 않는다. 교차 규칙은 별도 matrix로 식별한다.

## 1차 기능 범위
| 축 | 소유권 | 입력→출력 | 실패 시 |
|---|---|---|---|
| Capture | Intake | external bytes→receipt | incomplete/quarantine |
| Preservation | Evidence | receipt→sealed vault | fail-closed |
| Context | Knowledge | evidence→note/links | unverified draft |
| Retrieval | Search | query→evidence pack | abstain |
| Coordination | PeerHub extension | task proposal→review record | isolated/error |
| Production | Evidence export | selected items→verified package | block export |
| Operations | Backup/governance | files→snapshots/audits | alert / reconcile |

## 2차 정보 신뢰/시간 축
| Dimension | 가능 값/규칙 | 비고 |
|---|---|---|
| Origin | physical/native/export/screenshot/derived/unknown | 사실에 충실 |
| Epistemic | observed/extracted/asserted/inferred/verified | claim마다 지정 |
| Time | source claimed / observed / acquired / recorded / verified / valid interval | timestamp conflation 금지 |
| Privacy | public/internal/private/restricted | actor scope gate |
| Retention | hold active / controlled / eligible / destroyed | 삭제 여건 분리 |
| Integrity | unknown/verified/mismatched/unavailable | byte hash + provenance |
| Replication | local/primary-sync/secondary-verified/offline | cloud upload 상태 별도 |
| Authority | device capture-only / designated writer / human approval | 멀티기기 제약 |

## 3차 예외 축
- 입력: zero-byte, huge files, corrupt file, nested archive, unicode, filename collision, timestamp conflict, unknown encoding.
- 경로: traversal, hardlink, junction, symlink, case-fold clash, NTFS ADS, UNC, sync placeholder, quota.
- 연산: interrupted, concurrent, repeated, stale, partial, idempotency conflict, retry-after-crash.
- 출력: page reference mismatch, OCR uncertainty, redaction hidden text, missing original, citation hallucination.
- 장기 보존: primary deletion, sync conflict, backup contamination, retention/hold conflict, offline restore, migration.

## 4차 Quality attributes
**Correctness, Traceability, Safety, Security/Privacy, Reliability/Recoverability, Usability, Portability, Performance, Maintainability, Observability, Evolvability.** 각 기능은 최소 1개 예외/1개 품질 속성에 대응하는 테스트를 가진다.

## MECE 교차 결론
- 원본 파일은 Evidence/Object만 소유; Knowledge/Context/Memory는 참조. 파생데이터는 사용자 승인 없이 '원본 사실'을 변경하지 않는다.
- Hold·Privacy·Retention은 모든 계층의 cross-cutting policy이며 특정 폴더에 보관한다고 효과가 자동 발생하지 않는다.
- cloud provider와 PeerHub는 **실행 환경/교환 어댑터**, canonical 사실/권한의 주인이 아니다.
- 본 문서는 exhaustiveness의 근거로 cross-coverage를 보이지만 zero-defect 증명이 아니다.

## R3 lifecycle coverage
범위/기능 위주의 R2 매트릭스에 더해 시간축·직교 품질축·인수인계 축을 `docs/43_RECURSIVE_MECE_LIFECYCLE_AUDIT.md`에서 검증. **한 행이 여러 품질속성과 교차하는 것은 MECE 위반이 아니다**. 소유자가 정확히 하나인지와 예외가 빠짐없는지 검사한다.
