# 15. Engram · PeerHub · MCP · AI 통합 규칙

- Engram: 선택적 portable execution/tool lifecycle. 버전·경로·툴체인 정보를 metadata로 캡처할 수 있으나 애플리케이션이 Engram 설치를 하드 요구하지 않는다.
- PeerHub: 선택적 조정/메시징 레이어. 2026-10-09 확인 v0.12.4 기준 Core=Peer/Stream/Record/Offset; 관측·작업·artifact 등은 Extension. 범용 패키지의 표준 계약을 PeerHub 실제 Python 내부 API라고 가정 금지. 공개 명령과 지원 확장은 릴리스 기준 feature detection / consumer contract test.
- MCP: 선택적 tool/resource/prompt interface. 입력 검증·actor authorization·egress budget·cancel·idempotency/uncertain 상태가 필요. 모델의 합의나 답변은 제품 규범 승인 근거가 아님.
- 다른 CLI/provider에도 동일: 엔진별 도구/쿼터/세션 재개/중단/steering은 '가능함'이 아니라 실제 검증한 capability로 표기.

통합 장애 시 Core는 비의존 영역 작업을 지속하거나 명시적으로 fail closed. feature detection 미지원이면 조용한 부분 기능 축소 금지. 추천 command names와 namespace는 프로젝트별 기존 CLI 생태계를 존중한다.
