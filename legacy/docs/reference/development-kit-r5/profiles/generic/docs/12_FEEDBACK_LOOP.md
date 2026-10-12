# 12. 종결되는 지속개선 피드백 루프

`OBSERVED → CAPTURED → TRIAGED → ROOT_CAUSE_ESTABLISHED → APPROVED → TEST_DESIGNED → RED_REPRODUCED → FIXED → GREEN_VERIFIED → RELEASED → EFFECT_OBSERVED → CLOSED`

각 이동: actor, timestamp, before/after, evidence ref, owner, review due. BLOCKED/WONT_FIX/REOPENED는 별도 사건이며 해결 완료에 합산 금지. 문서/정책만 바꾸는 변경은 위험승인 아래 RED 생략 이유를 명시 가능하나 소프트웨어 버그에는 남용 금지.

**CLOSED 필수 조건**: (1) 결함/기회의 바탕 가설 (2) regression/검증 결과 (3) 실제 반영 릴리스 (4) before/expected/after와 표본·기간·지표 (5) 부작용 관측 (6) 표준/테스트/지침 갱신 (7) 재발 시 재개 트리거.

사고: first containment, 5 Whys/원인 가설 반증, impact analysis, 장단기 수정, 예상 부작용, 자동 테스트/수동 probe, release, 효과 관측. 매주 blocked/stale, 월간 재발/성능, 분기별 위험/외부 표준/의존성 재검토를 권고(팀 상황에 따라 조정).

KPI에는 분모·모집단·기간·단위·지표 owner가 있어야 한다. DORA throughput vs instability를 균형 있게 보며 단일 점수로 개발자를 평가하지 않는다.
