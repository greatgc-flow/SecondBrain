# 28. 리서치 출처/검증 사실/적용 범위 (2026-10-09)

`확인 사실`은 공식 기관/프로젝트 문서에서 지원되는 내용만. `설계 결정`은 사용자 요구에 근거한 아키텍처 선택으로 사실 검증과 구별.

| Ref | 출처 | 확인 내용 | 설계 적용 | 갱신 위험 |
|---|---|---|---|---|
| S01 | SWGDE 18-F-002-2.0 2025-11-20 https://www.swgde.org/documents/published-complete-listing/18-f-002-2-0/ | 데이터/출처/수집 방법/당시 노트/chain-of-custody 기록과 hash | capture/custody | 보존 문서 신구 비교 |
| S02 | NIST IR 8387 https://www.nist.gov/publications/digital-evidence-preservation-considerations-evidence-handlers | 원출처·전달경위·hash와 별도 보관 등 고려 | anchor/offsite verify | 낮음 |
| S03 | SWGDE 17-F-002-2.1 https://www.swgde.org/documents/published-complete-listing/17-f-002-2-1/ | forensic acquisition / working copy 구분 | ERL-5 외부 전문 영역 | 낮음 |
| S04 | RFC 8493 https://www.rfc-editor.org/rfc/rfc8493.html | BagIt data/manifest/tagmanifest | export package | 낮음 |
| S05 | RFC 8785 https://www.rfc-editor.org/rfc/rfc8785.html | deterministic JSON canonicalization | event hashing | 낮음 |
| S06 | RFC 3161 https://www.rfc-editor.org/rfc/rfc3161.html | digest timestamp protocol | optional external anchor | 낮음 |
| S07 | RFC 9562 https://www.rfc-editor.org/rfc/rfc9562.html | UUIDv7 시각 정렬 가능 ID | stable IDs | 낮음 |
| S08 | Library of Congress PREMIS 3 https://www.loc.gov/standards/premis/v3/ | preservation metadata Object/Event/Agent/Rights | conceptual metadata mapping | 낮음 |
| S09 | JSON Schema 2020-12 https://json-schema.org/draft/2020-12/json-schema-validation | format keyword는 기본 assertion이 아닐 수 있음 | FormatChecker+semantic checks | 낮음 |
| S10 | Google Drive help https://support.google.com/drive/answer/13401938?hl=en | Stream vs Mirror; Mirror on local & cloud | local availability | 서비스 변경 가능 |
| S11 | OneDrive help https://support.microsoft.com/en-us/onedrive/save-disk-space-with-onedrive-files-on-demand-for-windows | Always keep on this device | hydration gate | 서비스 변경 가능 |
| S12 | OWASP LLM Top 10 2025 https://owasp.org/www-project-top-10-for-large-language-model-applications/assets/PDF/OWASP-Top-10-for-LLMs-v2025.pdf | retrieved content를 통한 indirect prompt injection | AI boundary | 모델/위협 지속 변화 |
| S13 | Engram v3.7.0 https://github.com/greatgc-flow/Engram/releases/tag/v3.7.0 | 제품 최신 release 기준 2026-10-09 | 런타임 독립 | 높은 갱신 위험 |
| S14 | PeerHub v0.12.4 https://github.com/greatgc-flow/peerhub/releases/tag/v0.12.4 | manifest와 extension, 테스트 게이트 | 연동 기준 | 높은 갱신 위험 |
| S15 | PeerHub README main https://github.com/greatgc-flow/peerhub/blob/main/README.md | Core Peer/Stream/Record/Offset, 기타 extensions | Core/extension 분리 | 높은 갱신 위험 |
| S16 | MCP https://modelcontextprotocol.io/specification/ | protocol tools/resources and security | addon facade | version changes |
| S17 | RO-Crate https://www.researchobject.org/ro-crate/ | research object packaging/provenance 모델 | 향후 export optional | 낮음 |
| S18 | W3C PROV-O https://www.w3.org/TR/prov-o/ | entity/activity/agent provenance | provenance reference | 낮음 |
| S19 | MCP 2026-07-28 https://blog.modelcontextprotocol.io/posts/2026-07-28/ | 현재 최신 published MCP version, stateless protocol core | MCP connector version contract | 높은 갱신 위험 |

## 자료 신뢰성 경계
기술 표준과 법적 증거능력 판단은 분리한다. 법원 제출 목적의 별도 법률 의견에 본 리서치만으로 특정 조항의 적용 가능성을 단정하지 않는다. 본 R2는 Google Drive 계정의 실제 동기화 폴더나 사용자의 저장 공간을 직접 변경하지 않았다.


