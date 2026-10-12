# 49. 실제 운영 현실성·증거 신뢰성·보안 판단 경계

## 법률/포렌식 표현의 경계
- native file을 보존했다는 사실과 해당 파일이 최초 생성 원본이라는 주장은 다르다. 클라우드 재다운로드/스크린샷/메일 재전송 이력, 앱 export로 바뀐 바이트는 취득 당시 그대로 보존한 것이지 원천의 검증된 진본을 뜻하지 않는다.
- 민형사 증거능력·적법 취득·진정성립·전문법칙/증명력 등은 사건별 판단. system-generated `ERL`은 **내부 기술 준비도**이며 법적 효력 등급/포렌식 인증이 아니다.
- Hash는 동일 바이트 판정 수단이지, 파일 작성자·실제 사건 시각·출처의 적법성 확인 수단이 아니다.
- 자기 컴퓨터에서 작성한 journal, manifest, 자체서명만으로 독립된 외부 시점/무변조 입증이 되는 것은 아니다. 외부 timestamp/independent offline copy가 실제로 존재할 때만 그 효력을 설명한다.

## OneDrive·Google Drive 운영 경계
- 파일 동기화 ≠ 트랜잭션 ≠ 불변 저장소 ≠ 별도 보존 백업. 충돌 복사본, symlink, Unicode 정규화/대소문자, Files On-Demand와 Mirror의 실제 bytes 및 version history는 환경 의존. 최소 실증 PC 2대 + 오프라인 상태 + conflict+restore.
- 한쪽 클라우드의 Backup 폴더가 같은 계정/OS/암호화키에 묶이면 독립 failure domain이 아님. 파일 digest 일치만으로 cloud 업로드 완료·계정 접근 가능·복원 완료를 보장하지 않음.
- 단일 Writer는 편의/위험 통제이며 network partition 중 둘의 write를 기술적으로 불가능하게 막는 distributed fencing이 아님. 조기 경보 및 human cutover가 최선. split-brain면 운영 정지·원본 격리·차이를 별도 복구.

## 데이터 민감성 및 정책
- Evidence/derived OCR/knowledge/embedding/AI prompts/console 출력/trace/export/email/thumbnail/temporary files 모두 민감정보 파생경로. target recipient, action, expiry 범위의 egress 승인이 없으면 외부 모델·플러그인으로 원문 이동 차단.
- 파일시스템 root 암호화, 오프사이트 snapshot 암호화·계정 접근 분리, 키 복구 테스트, 로컬 index의 암호화/권한, 로그 최소화·삭제 주기를 **사용자 운영 설정으로 확인**해야 한다. 미확인 키 관리/복구를 `PASS`로 표시하지 않는다.
- 악의적 PDF/Office/archive는 파일 미리보기·OCR·media decoding 시점부터 실행환경 위험. sandbox와 resource/time limit, AV, parser patch, 링크/ADS/hardlink 공격에 대한 negative tests.
- 승인·감사 기능 자체가 손상돼도 무조건 자동 복구/auto delete가 아니라 fail-closed+manual reconciliation. 실사용자 사건 정보로 AI 벤치마크를 제작하는 것은 별도 정보보호 검토 필요.

## 장기 유지보수 / 반(反) 과설계
- Core: 파일 입수, canonical hash+receipt, basic provenance/hold, verify, locally rebuildable catalog, export plan/verify. 다른 핵심 구성요소(Obsidian/PeerHub/cloud API) 없이 독립 동작.
- Extensions: WARC, ExifTool, media OCR/transcription, embeddings/vector/graph, MCP, PeerHub, GUI, TSA, full disaster simulation. 활성화되지 않아도 Core pass 가능한 영역은 필수 runtime dependency로 취급하지 않는다.
- 증거 위험도에 따라 high-quality capture profiles를 유도하되 낮은 위험 개인 노트까지 항상 ERL-4/5를 강제하지 않는다. 중요 사건 증거의 원본무결성은 타협하지 않는다.

## 공식 참조(접속/내용 갱신은 버전 확인)
- RFC8785 JCS https://www.rfc-editor.org/rfc/rfc8785
- RFC8493 BagIt https://www.rfc-editor.org/rfc/rfc8493
- NIST IR 8387 https://www.nist.gov/publications/digital-evidence-preservation-considerations-evidence-handlers
- SWGDE 18-F-002-2.0 (2025) https://www.swgde.org/wp-content/uploads/2025/07/2025-06-30-Best-Practices-for-Digital-Evidence-Collection-18-F-002-2.0.pdf
- NIST SSDF SP 800-218 v1.1 final https://csrc.nist.gov/pubs/sp/800/218/final ; v1.2 https://csrc.nist.gov/pubs/sp/800/218/r1/ipd **initial public draft** (최종 규정 아님)
- MCP specification 2026-07-28 https://blog.modelcontextprotocol.io/posts/2026-07-28/
- PeerHub v0.12.4 (2026-10-09) https://github.com/greatgc-flow/peerhub/releases/tag/v0.12.4
- Engram v3.7.0 (2026-10-03) https://github.com/greatgc-flow/Engram/releases/tag/v3.7.0
