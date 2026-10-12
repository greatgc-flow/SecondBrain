# 02. 단일 Golden Path — 예시가 포함된 전체 생명주기

```text
관찰/요청 → 이슈와 기대 효과 → 스펙과 수락기준 → 1개 수직 작업
  → RED → GREEN → REFACTOR → 정적·통합·보안·실측 시험
  → 동일 후보 빌드/검증 → 사용자 릴리스 → 운영 실측
  → 피드백/사고 → 5Whys + 작은 개선 → 새 실패시험 → 루프 재시작
```

**예: 일반 CLI**
1. 사용자가 잘못된 옵션을 주면 이해 가능한 오류를 요구한다(GD-... 관련 항목 선택).
2. `cmd --unknown`은 종료 코드 2이며 도움말과 대안 1개를 출력한다는 계약을 적는다.
3. RED 실행 후 코드를 수정, GREEN, 에러 메시지에 비밀경로가 노출되지 않는 반례 추가.
4. 배포 후보 SHA 기준 테스트 실행, 실제 사용자의 문제 재현이 사라졌는지 측정한 후 CLOSED.

**예: Second Brain**
1. 동기화 중인 PDF가 Inbox에 들어옴 → 아직 안정화 안됨.
2. 안정화 확인→원본 byte 해시→Vault 봉인→검증 receipt; 예외면 fail-closed.
3. RED: copy 도중 전원 중단, object_id/hash 불일치, LegalHold 우회, 외부 LLM egress.
4. 실제 복원과 제3자 기기로 해시가 일치하기 전 `evidence-ready`로 발표하지 않음.

**AI 작업 단축 규칙:** 모델에 수백 문서를 일괄 주지 말고 `00_START_HERE` + 1개 대상 요건 + 관련 계약 + 실패 오라클 + 현재 HEAD를 준다. `status`와 `done`은 서로 다른 상태다.

**선택 단계:** 단순 로컬 CLI에 Kubernetes, SLSA attestation 전체, 3-agent 합의는 N/A 가능. 민감자료, 법률 보존, 결제, 외부 실행, 배포가 있는 경우 필수 게이트는 생략하지 않는다.
