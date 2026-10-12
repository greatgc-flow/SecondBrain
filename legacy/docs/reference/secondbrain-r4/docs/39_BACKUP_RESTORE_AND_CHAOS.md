# 39. Restore / DR / fault injection / 지속실증

## 필수 실패 모드
입력·동기화(placeholder/mtime false stability/same-size mutation), OS(권한/디스크 부족/crash), 분산(sync conflict/split brain), 데이터(hash chain/anchor/metadata mismatch), 보존(Hold/retention), AI(egress/citation poisoning), 변경(schema migration), 복구(secondary corrupt/partial / copy proof incomplete)를 교차표로 관리.

## Drill 종류
- **D0 deterministic**: 단위/속성, mocked provider, synthetic file fixtures. 매 PR.
- **D1 staging**: 로컬 임시 root에서 crash/fault injection, restore round-trip. 매 candidate.
- **D2 Windows provider**: 전용 테스트 계정·폴더, OneDrive/Google Drive 재접속·충돌·hydration. 후보 관련 변경/분기.
- **D3 physical recovery**: Primary PC 접근 불가, secondary/tertiary에서 새 기기+새 경로로 복원, diff/index/hold/export 검증. 분기.
- **D4 disaster/breach tabletop**: ransomware/corrupt anchor/계정 접근 상실/키 소실, 연락망과 정지 절차. 반기.

테스트 자료는 실제 증거/인증정보 대신 synthetic; 테스트에 실제 cloud provider가 필요하면 별도 human opt-in과 test-only account, 예상 비용/업로드 범위를 사전 설명.

## Restore drill pass 조건
1. Source snapshot ID/manifest/chain head/anchor 검증.
2. 별도 failure domain의 payload hash 전량 또는 위험등급에 맞게 명시한 범위를 확인. 제한 범위 검사라면 전량 PASS로 주장하지 않음.
3. **새 root** 복원, 원래 root 덮어쓰기 금지. Writer epoch 신규 부여, old writer blocked.
4. Source Object/Observation/Acquisition/Custody/Hold/Production 참조 무결성 cross-check PASS.
5. Local index 전체 재생성 뒤 동일 canonical query set retrieval invariant PASS.
6. 금지 외부 전송/파기 경계 재확인, 구조적/시간적 데이터 일치.
7. 수행자·environment·duration·RPO/RTO *측정값*·증거 ref·미확인 부위 기재.

## Chaos bounds
- 실제 사용중 Evidence root에서 destructive chaos test **금지**.
- default `--dry-run`, disposable isolated file tree and test keys, no real PeerHub provider calls.
- Timeout/budget/termination watchdog 필수; cancel/crash에도 source Drop 사본을 삭제하지 않음.
- Fault injection 시 불완전 데이터의 오인 `PASS`, 무리한 자가복구·덮어쓰기, audit trail 영구 손실을 실패로 판정.

## Backups and hold
법률자료 보존기간 무기한을 강제하는 것은 정책 위험. 보존/파기/개인정보 삭제 요청/분쟁 가능성에 대해 별도 human+법률승인, active hold 우선, 파기 이력과 파생본/backup의 처리범위 기록. Cloud sync 내역은 별도 백업 proof 아님.
