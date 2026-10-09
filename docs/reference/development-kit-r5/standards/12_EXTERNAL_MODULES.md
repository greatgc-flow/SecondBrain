# 12. 5 Whys 후 안정 외부 모듈 대체/비도입 검토

신규 패키지를 직접 만들기 전에 다음을 **채택 / 선택 / 제외**로 판정했다. 가격·라이선스·지원 플랫폼·성숙도는 실제 개발 시작 시 다시 검증해야 하며, 제품 코드가 없으므로 채택 여부는 아직 *설계 결정*이다.

| 문제 | 기본 선택 | 직접 구현이 불리한 이유 | 경계·한계 |
|---|---|---|---|
| CLI 파서·Help | Python `argparse` **채택** | 신규 parser·명령 inventory 중복 제거 | Node/PowerShell에도 강제하지 않음 |
| 스키마 검사 | `jsonschema` **선택** | Draft 2020-12에 맞는 기존 validator | 암호학적/교차 객체 의미조건은 별도 |
| 테스트 실행 | `unittest` **관리도구**, `pytest` **제품 개발시 선택** | 유력 생태계·편한 파라미터 테스트 | 테스트 수준과 양을 성공으로 착각 금지 |
| Property 기반 반례 | Hypothesis **조건부 선택** | 경계·상태머신 입력 생성 검증 용이 | 입력 generator의 가정 오류 주의 |
| 파일 해시/무결성 | 표준 `hashlib` **채택** | 자체 암호 라이브러리 금지 | WORM/원취득 진정성 보증 X |
| 로컬 검색/메타 | SQLite + FTS5 **조건부** | 초기엔 별도 서버/GraphDB 불필요 | Cloud Sync 폴더에 공유 쓰기 금지 |
| 사진 메타 | ExifTool **조건부** | 풍부한 확장 메타 지원 | 원본 write 금지, 버전·라이선스 확인 |
| 영상/음성 메타·파생 | FFmpeg/ffprobe **조건부** | 포맷 지원·검증 생태계 | 비트단위 원본 변환 금지 |
| 웹 아카이브 | WARC 호환 툴 **조건부** | 국제 표준 컨테이너·재현 가능 수집 | 동적/인증 웹 수집의 법적·기술적 제한 |
| 디지털 이관·증거 | BagIt / RO-Crate **조건부** | 표준 메타/manifest의 상호운용 | checksum은 출처 정당성 증명 아님 |
| AI Agent 연동 | MCP SDK / PeerHub adapter **선택** | 기존 프로토콜·전송 중복 개발 방지 | 도구·모델 권한은 절대 자동 위임 금지 |
| 관측 | OpenTelemetry **선택** | exporter 직접 구현 지양 | GenAI semconv 변경 가능; version pin |
| 서명/공급망 | Sigstore, SLSA, SBOM 도구 **고위험 배포시** | 출처 증명 분리, 재현/검증 표준화 | 설계 ZIP에 인증 등급 주장 금지 |
| OneDrive/Google Drive | 기존 데스크톱 클라이언트 **채택** | Cloud API/OAuth 코드 필요 없음 | Sync≠backup, 양방향 multiwriter X |
| 대규모 GraphDB | 기본 **제외** | 사용자 시나리오가 없음 | 실제 관계형 질의 비용 입증 후 재검토 |
| 자체 AI agent framework | 기본 **제외** | Harness보다 운영 부채 큼 | 1-agent보다 개선 실증될 때만 확대 |

공식 참고: [Python argparse](https://docs.python.org/3/library/argparse.html), [jsonschema](https://python-jsonschema.readthedocs.io/), [Hypothesis](https://hypothesis.readthedocs.io/), [ExifTool](https://exiftool.org/), [FFmpeg](https://ffmpeg.org/), [BagIt RFC 8493](https://www.rfc-editor.org/rfc/rfc8493), [RO-Crate](https://www.researchobject.org/ro-crate/), [MCP](https://modelcontextprotocol.io/), [SLSA](https://slsa.dev/), [Sigstore](https://www.sigstore.dev/).
