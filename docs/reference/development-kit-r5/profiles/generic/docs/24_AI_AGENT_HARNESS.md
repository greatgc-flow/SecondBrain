# 24. AI Agent Harness / 중단·재개 계약

AI Agent는 책임이 아니라 **실행 어댑터**다. 정책/권한 승인/테스트 오라클은 사람이 승인한 repo-local 계약과 결정적 검증기가 소유한다.

## 실행 단위
`task_id`, `spec_revision`, `source_commit`, `workspace`, `allowed_tools`, `network_egress`, `budget`, `deadline`, `stop_condition`, `acceptance_oracles`, `artifact_paths`를 시작 전에 묶어 기록한다. 모델명 자체를 코어에 hardcode하지 않는다.

1. Init: 미확인 자료는 READ-ONLY 조사. 테스트/명세 해석. 파괴행위 도구는 기본 거부.
2. Execute: 한 번에 작은 bounded 변경; 명세 바깥 변경 감지 시 중지.
3. Verify: 작성한 agent의 자기평가만 사용하지 말고 테스트/검수 스크립트로 별도 검증.
4. Handoff: 변경 파일·소스 SHA·실행한 실제 검사·실패·미해결 위험·다음 작업을 최소 레코드로 기록.
5. Resume: 이전 기록을 신뢰하지 말고 현재 SHA/계약/테스트를 먼저 다시 읽는다. 충돌 시 reconciliation 요청.

## 자율성 단계
`A0=분석(ReadOnly)`, `A1=격리된 working tree 수정`, `A2=승인된 비파괴 PR 작성`, `A3=인간 승인 후 릴리스/외부 통신`, `A4=상용 자동 운영(별도 프로세스·외부 감사)`. A4는 초기 설계 scope 밖.

고위험: 개인정보 전송, 삭제, 실제 유료 API, 원본 변형, 비밀 접근, 권한 변경, prod 배포 → 기본 deny. 승인해도 action, actor, scope, expiry, idempotency, rollback과 receipt를 남긴다.

트레이스는 secrets/raw prompt/transcript 전체 저장을 기본 금지한다. 필요한 증빙은 사용자 승인된 비식별 digest만. PeerHub는 강제 실행엔진이 아닌 선택 협업 채널이다.
