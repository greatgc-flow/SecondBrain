# 33. Closed-loop continuous improvement — 상태머신 / 종결 기준

## 목표와 증거
모든 피드백은 SSOT의 **비민감 governance record**로 관리한다. PeerHub feedback/record나 GitHub issue는 관련 ref만 가진 선택 채널이며 canonical 업무 승인 상태가 아니다.

```text
OBSERVED → CAPTURED → TRIAGED → ROOT_CAUSE_ESTABLISHED → APPROVED →
TEST_DESIGNED → RED_REPRODUCED → FIXED → GREEN_VERIFIED →
RELEASED_OR_DEPLOYED → EFFECT_OBSERVED → CLOSED
                    ↘ BLOCKED / REOPENED / WONT_FIX(approved)
```

## 단계별 exit + owner (한 단계당 단일 accountable owner)
| 상태 | 필수 입력 | 완료 증거 / 다음 단계 | 소유자 |
|---|---|---|---|
| OBSERVED | 재현 가능한 증상 또는 구체 사용자 불편 | 최초 수집 시각·출처·영향 범위 | reporter |
| CAPTURED | 피드백 ID, 개인정보 제거한 재현 방법, 분류 | provenance·관련 artifact/ref·중복 관계 | maintainer |
| TRIAGED | 사건 심각도, privacy/legal hold 영향, 재발 여부 | P0~P3, containment/영향 범위, owner, due/revisit | maintainer |
| ROOT_CAUSE_ESTABLISHED | 로그·counterexample·원인 후보 | 5 Whys/가설 실증, 직접/공통근본원인 구분 | maintainer |
| APPROVED | change proposal, 대안/비용/역효과 | 승인자·결정·ADR 필요 여부 | owner |
| TEST_DESIGNED | 변경 대상 invariant + negative/positive fixture | traceability, test plan and expected failure | tester |
| RED_REPRODUCED | 실패 코드+진단환경 | 같은 candidate line에서 테스트 선행 실패 재현 (버그류) | tester |
| FIXED | 최소 변경, 마이그레이션 영향, rollback | code diff, change id, dependency map | developer |
| GREEN_VERIFIED | candidate-bound full gate | regression, cross-cutting/privacy/DR, new red→green | independent reviewer |
| RELEASED_OR_DEPLOYED | release manifest, approvals | artifact digest / deployed baseline / rollback recipe | operator |
| EFFECT_OBSERVED | 사전 정의한 기간/샘플 기준 | 이전 대비 결과, 부작용, evidence refs | operator |
| CLOSED | 재발 여부·사례/표준 반영·증빙 확인 | signed closure or verified completion, due date, lesson | owner |

- 모든 상태 전이는 시간·actor·before/after·관련 증빙 ref로 append-only 기록; 역이행은 새로운 event로 나타낸다.
- 정책/문서 변경은 RED 테스트가 물리적으로 필요 없는 경우 `RED_REPRODUCED=NOT_APPLICABLE_APPROVED` 사유+리뷰 필수. 소프트웨어 결함에는 이를 남용할 수 없음.
- 보안 사고는 triage 직후 incident-record `CONTAINED` (보조 containment 이벤트 별도), 임시 해결 후에도 효과 확인 전 **CLOSED 불가**. 로그를 포함한 포렌식 원본은 별도 Evidence 보존 정책을 준수.
- `WONT_FIX`는 영향·위험 수용권자·재검토 트리거·재검토일 있는 별도 종료 유형이며 CLOSED처럼 "해결"로 집계하지 않음.
- `BLOCKED`도 owner·해소 선행조건·다음 점검일이 필수, 묵시적 만료/삭제 금지.
- 같은 현상 재발 시 새 incident/feedback과 기존 record를 `recurrence_of`로 연결하고 기존 결정을 재검토한다.

## Closed-loop quality gates
L1 불변조건: 모든 변경은 요구사항/위험/사고 중 하나에서 시작하거나 명시적 설계 결정으로 연결됨.
L2 측정조건: `before`, `expected`, `after`, `observation_window`, `population`, `owner`가 존재해야 CLOSED.
L3 검증조건: 테스트 결과와 release/deployment 후보 digest 일치, 실패/미측정이면 HOLD.
L4 지식화: 판례/사건 내용과 다른 **운영상 배운 규칙**은 SOP/ADR/테스트로 승격; 오래된 규칙의 supersession/expiry 관리.
L5 회귀조건: 같은 문제를 검증하는 테스트/체크가 남아야 하며 실증 불가 시 수동 점검 주기/소유자를 명시.

## KPI 분모 제약
`closed_verified_rate = EFFECT_OBSERVED를 충족한 CLOSED / 해당 cohort의 해결 목표 티켓` (WONT_FIX/중복 제외를 이유와 함께 기록).
`recurrence_rate = 동일 root-cause 링크 재발 / 기간 내 해결 티켓` (모집단과 관측 기간 고정).
`escape_rate = 출시 전 검출되지 않은 유효 결함 / 해당 후보의 유효 결함 총수` (미발견 결함이 있어 실제 값은 추정 지표).
지표 악용 방지: closure volume, 테스트 수만을 목표로 삼지 않음; 잔여 위험과 승인된 deferment도 함께 공개.

## PeerHub binding
비민감 `feedback_id`, `change_id`, `record_digest`, `brain://governance/...`만 Extension에 투영. provider dispatch 시 원본 자료·개인정보 자동 포함 금지. PeerHub 충돌·중단 시 Brain 내부 상태는 durable.

**Event/read-model separation:** `governance-event` is authoritative append-only transition record. `feedback-case`/`gate-result` snapshot files are materialized or immutable per candidate; every change is backed by event with actor/time/reason. A valid JSON Schema is insufficient to prove unbroken chain, external authority, or real-world effect.
