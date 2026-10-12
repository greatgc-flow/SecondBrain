# 38. Secure SDLC / 공급망/취약점 개선 루프

## 기준
NIST SSDF SP 800-218(PO·PS·PW·RV), SLSA v1.2 Build track, OWASP LLM Top 10 2025, ISO/IEC 25010:2023는 **참조/맵핑 근거**이지 인증/수준 달성 주장 아님.

## 변경 정책
- Commit/PR: change ID→requirement/incident/risk→test→review→artifact attest→release. 독립된 code review required for Evidence/hold/egress/backup/chain-changing paths.
- Third-party tool/AI provider/version: checksum/signature/license/update/source provenance와 peer role bound; 설치된 CLIs가 보안 승인된 것이 아님.
- Dependencies locked/pinned for release; SBOM 제공 예: SPDX/CycloneDX. 취약점 스캔은 CVE의 오탐/도달성/우회조치를 구분하여 대응과 재검토 일정 기록.
- Secret: env/credential store, 로그/배포/ZIP/Cloud canonical records에 key/token 미포함. 승인 없는 외부 모델 학습/보관 전달 불허.
- Runtime download, archive extraction, OCR, PDF parser, CLI subprocess를 untrusted boundary로 보고 sandbox/timeout/resource limit. Windows junction/hardlink/ADS/case collision test.
- 모델 정답률 변화, parser update, index format migration에도 완전한 regression+corpus drift eval 필요. 기능 외 의미적 후퇴를 release defect로 분류.
- SLSA provenance: input source commit, builder identity, invocation, dependencies, outputs; 자체 로컬 checksum만으로 Build L2/L3 주장하지 않음.
- Zero-trust output: AI-generated command/doc/data는 반드시 schema/allowlist/policy 검증. 코드 실험은 synthetic data only.

## Vulnerability intake
`REPORTED→TRIAGED→FIX_OR_MITIGATION→VERIFIED→DISCLOSED_IF_APPLICABLE→OBSERVED→CLOSED`; security-impact fix는 공통 feedback ledger에 기록하고 재발 시험 추가. 공개 전 private fix, 취약점 exploit 상세를 증거 저장소에 확산시키지 않음.

## Threat ↔ Control ↔ Test
| 공격/고장 | 제어 | 회귀시험 |
|---|---|---|
| malicious archive | path canonicalization + extraction limits | TC-SEC-01/LC-SEC-01 |
| evidence tampering | hash/anchor and independent backup | TC-EVT-02/LC-DRL-01 |
| sensitive AI disclosure | deny egress, scope, recipient | TC-AI-01/LC-SUP-01 |
| retrieval poisoning | trusted source boundary / citation checking | TC-AI-02/LC-EVA-02 |
| compromised build | SBOM+provenance+artifact digest+review | LC-SUP-02/LC-RLS-02 |
| unstable migrations | snapshot, dry-run, reversible cutover | LC-CHG-01/LC-DRL-03 |
