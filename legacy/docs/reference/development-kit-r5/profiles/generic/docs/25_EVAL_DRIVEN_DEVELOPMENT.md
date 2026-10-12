# 25. Eval-Driven Development + Independent Grading

조건 `AI_ENABLED=true`에서 적용한다. 기존 unit/contract/TDD를 대체하지 않는다.

## Golden task 설계
각 eval case는 `scenario_id`, data sensitivity, setup snapshot hash, input/query pointer, allowed tools, objective terminal state, expected prohibitions, grader/version, owner, severity, repeated-trials policy. **문자열 정답만으로 성공이라 단정하지 않는다.**

- Code grader: 상태/파일/권한/외부 부작용/해시 검증. 가능하면 최상위 판정.
- Model grader: 요약의 적절성·언어 품질 등 주관적 판정; rubric·grader revision 기록. 단독 보안 승인 불가.
- Human grader: 불일치/법률·고위험·설계 의도를 표본 재검토. judge drift 보정.
- Multi trial: 시행 수 n, 성공수 k, 모델·도구·프롬프트·환경·seed(사용 가능 시), latency/cost 분포 기록; 작은 n에 확정적 품질을 주장하지 않는다.

**벤치마크 오염 방지:** golden answer/test fixture를 구현 모델에게 무제한 공개하지 않는다. 그러나 모델에 의존하는 비공개 답변으로 보안 침해를 탐지한다고 주장하지 않는다. 평가 데이터는 repo 버전, 비밀/실데이터는 별도 vault.

**업그레이드 게이트:** 모델/prompt/skills/tool/schema/permissions 변경 때 영향을 받는 eval 결과는 STALE. 후보별 품질 하한, latency/cost 상한, adverse-event maximum, human calibration 결과를 독립 검사한다.

**관측→학습:** 운영 실패 → 익명화된 failure case → RED 재현 → 수정 → benchmark + regression 재실행 → 운영 효과. 원문 개인정보를 데이터셋으로 자동 승격 금지.
