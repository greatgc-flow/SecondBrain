# 35. TDD → Production 단계별 품질 Gate (G0~G7)

## Gate rule
Gate 결과는 지정 소스/설정/스키마/의존성/운영체제/배포 타깃의 fingerprint에 결속된다. candidate SHA가 달라졌다면 영향받는 Gate를 STALE로 표시하고 재실행한다. 테스트 결과 `PASS`는 pipeline green만으로 대체할 수 없다.

| Gate | 단계 | 필수 산출물 / 성공 조건 | 차단 조건 |
|---|---|---|---|
| G0 | Pre-TDD | requirements/ADR/traceability, 환경·권한·금지 동작 명시 | 모호한 P0, 검증 대상 없는 MUST |
| G1 | RED | 실패부터 작성한 TDD test, 기존 실패와 신규 실패의 명확한 구별 | failing test 없이 버그 해결 주장 |
| G2 | GREEN | 단위/계약/스키마/속성/경계/negative 테스트, static/type | 필수 CI 미실행·실패·waive |
| G3 | Integration | Windows 파일 특성/Sync simulator/MCP/PeerHub smoke, cross-version | 권한 우회·실제 provider 필수 경계 오해 |
| G4 | Security & DR | 악성입력/유출방지, 백업 복원, 원본 변조 탐지, Legal Hold, supply chain scan | 보안/복구 P0 미해결, restore 미검증 |
| G5 | Release Candidate | immutable candidate fingerprint, artifact hashes, SBOM, provenance, signer/reviewer | artifact≠검증 후보, unsigned waiver, stale gate |
| G6 | Canary/Deploy | 분리된 테스트자료로 shadow/canary, preflight, rollback, operator 승인 | prod 원본 손실 가능성, rollback 불가 |
| G7 | Observe & Learn | telemetry windows, incident→root cause→action→retest→효과 검증 | 개선효과 미관측/재발 및 오염 은폐 |

G0는 본 패키지의 설계 단계에서 static-only. G1~G7은 미래 실행 항목으로 **NOT RUN**. G7은 전체 제품 릴리스 후 지속 게이트라서 '영구적으로 완료'라는 의미는 아님.

## Release evidence rule
- 후보 ID에는 source commit, code tree digest, package sha256, config hash, requirements revision, schema revision, Python/OS/Engram/PeerHub baseline, test plan revision, test suite & dependency lock digest 포함.
- `gate-result`마다 status, evidence_uri, evidence_digest, producer, executed_at, environment, rationale; expected baseline과 정확 일치.
- CI나 AI가 approval signer 역할을 자동 겸임하지 않음. 위험 변경/파괴적 migration은 별도 human independent approval.
- break-glass는 실제 시스템 운영 응급조치만 허용; 사후 사건/승인/원복/회귀 검증 의무. 출시용 hard gate 우회는 허용하지 않음.
- 실험용 dev build는 production release와 명확히 구별하고 위험한 Evidence root 사용 금지.

## Deployment rollout
`preflight → backup verified → read-only mirror on sample root → canary with synthetic evidence → approval → production cutover → post-deploy verify → observation window`. 비상: `freeze writes → isolate → diagnose → restore to new root → reverify → human cutover`. 백업/restore에서 이전 root 덮어쓰기 금지.

## Upgrade controls
R2 schema/v2 canonical 승격이나 Python/PeerHub/Engram/MCP version 업그레이드는 별도 change candidate. 모든 의존 경로와 golden test result를 후보에 바인딩하고, protocol 변경 시 consumer contract probe 필수.

`governance-event` journal integrity/anchor and candidate fingerprint semantic validation are G2/G5 requirements; parser-only schema PASS cannot satisfy them.
