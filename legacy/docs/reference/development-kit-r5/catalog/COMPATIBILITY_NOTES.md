# 최신 확인한 실행환경·제품 경계 (2026-10-10)

| 도구 | 관찰된 기준 | 프로젝트에 적용할 정책 |
|---|---|---|
| Engram | GitHub 최신 release `v3.7.0` (2026-10-03) | 단순 휴대용 runtime/tool life-cycle. `engram help` CLI/복구/유니코드 루트를 현장 점검. Engram에 Brain 데이터 SSOT 넣지 않음. |
| PeerHub | GitHub 최신 release `v0.12.6` (2026-10-09), main은 후속 문서 commit 존재 | Core=Peer/Stream/Record/Offset. Native resume는 `ask --resume` 명시 opt-in, 실패 시 근거 있는 fresh fallback; 요청/세션 상태를 맹신하지 않음. |
| Spec Kit | 도구 종속 금지 | `spec→plan→tasks→test→convergence` 방법만 채택. |
| Python | CLI kit: Python 3.11+ 지원 목표 | `argparse/pathlib/csv/json/unittest` 표준라이브러리. 제품의 Python 버전/OS는 별도 계약. |
| Node.js | 범용 제한사항 | Windows 특수문자/경로/프로세스 quoting은 배포 전 실제 T3로 확인. 위험한 string-concatenation workaround 금지. |
| OneDrive/Drive | 사용자 보유 Cloud | Provider API 미사용, 로컬 full hydration을 전제로 파일시스템 root 선택, 독립 backup 별도. |
| OTel GenAI | Semconv 개발 상태 일부 유지 | exporter adapter 선택; 내부 canonical event 구조는 versioned. |

**확인 방식:** Engram/PeerHub GitHub Releases API 및 commits 조회, 두 프로젝트 README. 본 문서는 해당 CLI를 실제 설치·실행하여 호환을 입증하지 않는다. 최신 버전 변경 시 자동 적용하지 않고 capability discovery.

- Engram: https://github.com/greatgc-flow/Engram/releases/tag/v3.7.0
- PeerHub: https://github.com/greatgc-flow/peerhub/releases/tag/v0.12.6
- PeerHub: https://github.com/greatgc-flow/peerhub/blob/main/README.md
- OpenAI Harness Engineering: https://openai.com/index/harness-engineering/
- DORA 2025: https://dora.dev/research/2025/dora-report/
- NIST SSDF IPD (초안): https://csrc.nist.gov/pubs/sp/800/218/r1/ipd
- SLSA: https://slsa.dev/spec/v1.2/
- OpenTelemetry Semconv: https://opentelemetry.io/docs/specs/semconv/
