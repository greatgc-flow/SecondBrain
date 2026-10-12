# 45. 최신 자료 대조 / Reference-driven improvement

**Verified as of 2026-10-09:** 공식 출처에서 원칙을 확인했고, 실제 제품 구현 여부를 검증한 것은 아니다.

| ID | 자료와 원본 URL | 적용 개념 | 재점검 trigger |
|---|---|---|---|
| S20 | NIST SSDF SP 800-218 https://csrc.nist.gov/pubs/sp/800/218/final | PO/PS/PW/RV, 취약점 root cause/재발방지 | 취약점·제품 보안 정책 변경 |
| S21 | Google SRE Workbook https://sre.google/workbook/table-of-contents/ | incident response/postmortem/SLO/canary | 운영 SLO 재설계 |
| S22 | DORA delivery performance https://dora.dev/guides/dora-metrics/ | change lead time, deployment frequency, recovery time, change fail/rework | 팀/제품 규모 변화 |
| S23 | SLSA v1.2 https://slsa.dev/spec/v1.2/ | build provenance, source/build track, 증빙 신뢰 수준 | release pipeline 교체 |
| S24 | ISO/IEC 25010:2023 https://www.iso.org/standard/78176.html | 9 characteristics product quality map | quality model 개정 |
| S25 | OWASP LLM Top 10 2025 https://genai.owasp.org/llm-top-10/ | injection, disclosure, poisoning, embedding leakage | AI model/provider/retrieval 변경 |
| S26 | NDSA Preservation v2.1 https://www.ndsa.org/activities/levels-of-digital-preservation/ | storage/integrity 보존성숙도·지속성 | evidence preservation review |
| S27 | RFC 8785 https://www.rfc-editor.org/rfc/rfc8785 | event JCS canonical bytes; code에서 정밀 구현 검증 | serialization 변경 |
| S28 | PeerHub v0.12.4 https://github.com/greatgc-flow/peerhub/releases/tag/v0.12.4 | Core vs Extensions, catalog candidate gates | new peerhub release |
| S29 | Engram v3.7.0 https://github.com/greatgc-flow/Engram/releases/tag/v3.7.0 | runtime contract, version hash verification | new engram release |

**사실/결정 구분:** 위 문서는 참고표준/현행 제품의 설계 근거이며 Second Brain이 그 표준에 인증되었거나 그 수준을 달성했다는 진술이 아니다. 대부분의 운영 검증은 구현 및 사용자의 독립 저장매체/계정/키 정책 확정 후 수행해야 한다.
