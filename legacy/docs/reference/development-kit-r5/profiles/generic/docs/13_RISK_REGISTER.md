# 13. 위험 분류·남은 문제

| Risk | 적용 조건 | 완화 및 오라클 | Owner |
|---|---|---|---|
| R-01 Core 과대화 | ALL | 선택 통합 고립/의존성 역전 계약 | architect |
| R-02 계약 불명 | ALL | 소비자 contract negative/compat tests | maintainer |
| R-03 자료 유실 | STATEFUL | crash/restore 단절점 시험 | operator |
| R-04 동시 수정 충돌 | CLOUD_SYNC | 단일 writer/epoch 또는 검증된 consensus, 침묵 합병 금지 | owner |
| R-05 인증/인가 | NETWORKED | cross-user/tenant IDOR negative | security |
| R-06 AI 비밀 유출 | AI_ENABLED | egress/embedding/log/trace 전 경계 deny | security |
| R-07 공급망 | ALL | lock/SBOM/scan/allowlist/candidate digest | release |
| R-08 회귀 허점 | ALL | mutation/property/negative/real tests | test |
| R-09 stale PASS | ALL | candidate-bound gate invalidation | release |
| R-10 개선 착시 | ALL | effect observed before closure | product |
| R-11 fake vs live 혼동 | AI_ENABLED | mock/live provenance 분리 | reviewer |
| R-12 도메인 법규 누락 | REGULATED 프로젝트만 | 전문 자문/별도 compliance profile | owner |

잔여 위험은 위험 수용권자, next review, 트리거가 있는 기록으로 보류. '완벽' 판정 불가: 실환경·실사례·유지보수성은 운영 중 측정해야 한다.
