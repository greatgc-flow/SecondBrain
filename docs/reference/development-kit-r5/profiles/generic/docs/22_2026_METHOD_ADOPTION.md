# 22. 2026 방법론 채택/배제 결정

**2026-10-10 조사 기준.** `quality/research_decisions_20261010.csv`가 방법론별 근거·적용·재검토 시점을 가진 결정표다.

## 확정 채택
- **SDD + TDD:** Specify → Plan → Tasks → RED → GREEN → Refactor → Converge; spec는 intent/contract 소유, 구현은 행동의 증거. Spec 문서만 있거나 그럴듯한 agent output만 있는 상태를 완료라 하지 않는다.
- **Harness Engineering:** agent가 배포/저장/모델선택을 소유하지 않게 한다. 완료 판단은 외부 오라클의 책임. 지시 파일은 작게, 공개 계약을 우선한다.
- **Eval-Driven Development:** AI 기능 활성화 프로젝트에 한해 scenario+fixture+grader+환경+반복성·비용·위험·인간보정의 검증 계약을 도입한다.
- **보안 기본:** 권한·예산·연결 경계에서 코드 레벨 통제. 비신뢰 문서/검색/도구 응답은 명령 권한이 없다.

## 조건부·거부
- Spec Kit의 **프로세스**는 채택하지만 특정 CLI 설치는 요구하지 않는다. 기존 R1 계약과 충돌 시 승인된 프로젝트 계약 우선.
- OTel GenAI 분야는 일부가 개발 중이므로 자체 안정적 event schema를 소유하고 telemetry adapter를 버전화한다.
- AgentSkills/AGENTS.md/MCP/PeerHub는 선택 adapter. 범용 Core에 의존성 금지.
- Kubernetes, Neo4j, microservices, 무제한 agent 병렬화, LLM judge 단독 승인을 디폴트로 두지 않는다.

## 운영 및 비용
최소 MVP는 한 개의 수직 슬라이스/한 개의 검증 가능한 oracle. 높은 위험·불확실성이 있을 때만 독립 agent 평가, 다중 trial, SBOM attestation, canary 수준을 높인다. 도입 효과를 먼저 측정하고 범위를 늘린다.
