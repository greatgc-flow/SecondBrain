# 10. G0~G7 품질 게이트

| Gate | 입력 | 성공 증거 | 미충족 시 |
|---|---|---|---|
| G0 | 승인 요구사항·ADR·프로파일 | 수락 오라클/owner/리스크 | 시작 보류 |
| G1 | 신규 실패 테스트 | 특정 소스 후보의 RED 로그 | RED 없는 결함 수정 주장 금지 |
| G2 | 최소 구현 | unit/contract/schema/semantic tests GREEN·정적 검사 | 오류 수정 |
| G3 | 통합 | 환경별 I/F·버전·설치·네트워크/동기화(적용 시) | 차단 |
| G4 | 보안·복구 | 악성입력/비밀유출/rollback/recovery(조건부) | 고위험 차단 |
| G5 | 릴리스 후보 | 소스·설정·deps·테스트·산출물 fingerprint, SBOM, 검토자 | 후보 반려 |
| G6 | 배포/릴리스 | preflight·canary·rollback·운영 승인 | 전환 중지 |
| G7 | 운영 관측·개선 | SLO/사용자효과·재발 추적·closure 증빙 | 개선 오픈 유지 |

Gate status: NOT_RUN/PASS/FAIL/BLOCKED/WAIVED/STALE. WAIVED≠PASS; 합당한 N/A는 해당 프로파일 근거가 필수. 후보 fingerprint가 바뀌면 영향받은 evidence는 STALE. G7은 지속 반복하며 영구 종료 상태가 아니다.

## Candidate fingerprint 정의
`sha256(canonical stable manifest {source_commit, tree_digest, config_digest, deps_lock_digest, test_catalog_digest, schemas_revision, toolchain, target_env})`; product artifact digest는 산출물의 별도 인자로 검증되고 candidate manifest와 연결한다. 빌드 전에 알 수 없는 artifact digest를 빌드 입력 지문에 섞는 순환 참조 금지. 주어진 후보를 검증하지 않고 과거 green을 재사용하지 않는다.

## v2 추가 Gate 인가 규칙
- G0: 승인 spec revision / methods decision / bounded slice.
- G2: spec↔task↔test↔implementation 수렴 및 계약 fitness; unresolved MUST면 FAIL.
- G4: AI 도구 sandbox 및 독립 검토/권한 승인, 민감 egress·high-risk action fail-closed.
- G5: (AI_ENABLED 한정) 모델·prompt·tools·skills·eval corpus·grader revision 바인딩과 stochastic trial/인간 보정; 변경 시 STALE.
- G6: 서비스인 경우 staged deployment + rollback trigger; CLI 등은 적합한 동등 수단.
- G7: 품질·비용·인간가치·운영 부작용과 feedback evidence 종결 확인.
