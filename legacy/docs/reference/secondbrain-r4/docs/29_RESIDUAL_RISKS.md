# 29. 잔여 위험 / 명시적인 비보장 범위

| ID | 잔여 위험 | R2 상태/추가 대응 |
|---|---|---|
| RR-01 | cloud local tree는 WORM이 아님 | **불가피**: 탐지(hash/anchor) + 복구(독립 snapshot); 중요한 법률자료 외부 타임스탬프 권장 |
| RR-02 | 관리자가 event+anchor+backup 모두 조작할 수 있음 | **완화**: independent offline anchor/TSA; 완전 차단 주장 금지 |
| RR-03 | 법적 증거능력은 기술적 저장만으로 보장할 수 없음 | **불가피**: 사건별 법률·진정성립·취득적법성 검토 |
| RR-04 | source original을 확보하지 못한 screenshot/PDF는 원생성 상태 복원 불가 | **완화**: provenance 수준 명시, '원본' 라벨 금지 |
| RR-05 | 2PC 원자성 없는 Cloud sync | **완화**: 지정 Writer+per-device capture-only, manual failover |
| RR-06 | 승인 받은 외부 AI provider의 내부 저장/학습/정책 변화 | **완화**: 기본 egress deny, 최소자료, 서비스약관 별도 판단 |
| RR-07 | 백업 암호화 및 retention 정책은 실제 사용자 운영 환경에 의존 | **OPEN deployment choice**, 계정/키/복원 검증 필요 |
| RR-08 | 대용량 수집/전량 hash 재검증 비용 | **측정 필요**, hash streaming/priority scheduling |
| RR-09 | 스캔/사진의 EXIF·파일시각은 조작 가능 | **완화**: extraction/inference/verification 분리 |
| RR-10 | Obsidian/OS/클라우드 외부 도구가 파일을 수정 | **완화**: 권한/deny plugin/write restrictions + verify |
| RR-11 | 평가셋 점수가 실제 사건의 법적 타당성을 보증하지 않음 | **불가피**, human review gate |
| RR-12 | Extension API 진화 | **완화**: Integration compatibility smoke tests, semver pinning/adapter isolation |

`OPEN deployment choice`는 시스템 설계 블로커가 아니며 운영자가 실제 경로/권한/비용/암호화 수준을 정해야 한다는 뜻. 구현 완료/현장 검증 통과라는 주장은 하지 않는다.

## R3 residual treatment
운영/조직/키 관리/법률 적합성은 `docs/44_R3_AUDIT_FINDINGS_AND_RESIDUALS.md`의 owner/trigger/acceptance/revisit 조건으로 계속 추적. 미검증된 실제 성능·법적 증거능력은 여전히 NOT VERIFIED.
