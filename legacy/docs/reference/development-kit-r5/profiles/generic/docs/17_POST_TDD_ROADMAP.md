# 17. TDD 이후 마일스톤·실행 순서

| 단계 | 목표 | 종료 증거 |
|---|---|---|
| M0 | 첫 수직 Slice RED/GREEN | 실제 테스트 log + 소스 SHA |
| M1 | Core 불변식/오류·권한·설정 | unit/property/negative 통과 |
| M2 | ports/adapters/선택 데이터·I/F | contract+integration+version test |
| M3 | 보안·복구·통합 교차 검증 | 격리된 chaos/security/recovery |
| M4 | 빌드/공급망/릴리스 후보 | source→artifact digest+필수 gates |
| M5 | 안전 출시/canary/rollback | 설치/전환/비상 복귀 증빙 |
| M6 | SLO/사용자 피드백 관측 | 결과 지표와 사고 대응 가동 |
| M7 | 재발방지/closed-loop | 실제 개선 before-after+다음 regression |

각 milestone마다 변경 승인·역추적·후보 버전과 실제 실행 기록이 있어야 한다. 제품 종류별로 해당 없는 단계는 N/A 근거. 고위험 결함에 대해서는 '일정'보다 안전성이 우선.

## v2 추가 단계 (마일스톤 번호 불변)
M0=최초 수직 slice + spec convergence; M1=architecture fitness/contract; M2=provider-independent harness; M3=agent safety/eval (AI_ENABLED); M4=candidate-bound eval results·artifact lineage; M5=staged delivery/rollback; M6=quality+cost+human effect; M7=incident→new RED→re-release→observed effect closure. 각 단계 신규 수행 증거 없으면 원래 기준의 NOT_RUN을 유지한다.
