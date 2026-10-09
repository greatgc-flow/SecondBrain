# 25. Engram / PeerHub / MCP / Obsidian 최신 경계

## Engram (확인일 2026-10-09)
- GitHub 최신 Release `v3.7.0` (2026-10-03). Repo main의 업데이트 주기와 released tag를 구별.
- Runtime/CLI 설치·업데이트·진단은 Engram 소유. Second Brain 데이터는 Engram 실행 트리에 포함하지 않음. `SECOND_BRAIN_ROOT`, `SECOND_BRAIN_LOCAL_STATE` 환경변수는 선택적 연동 계약.
- 관리 도구 가용 여부는 런타임 검증을 거쳐야 하며 Engram에 도구 등록을 전제로 설치 성공을 주장하지 않는다.
- Engram 저장소 수정/새 기능 구현은 본 R2 작업 범위 밖.

## PeerHub (확인일 2026-10-09)
- 최신 GitHub Release `v0.12.4` (2026-10-09). 현행 README는 **Core=Peer, Stream, Record, Offset**이며 Bridge, Observation, Diag, Artifact, Work, Search, Routing 등의 기능은 **extensions**다.
- 이전 v0.10.1 설계의 `task/consensus/lesson/artifact/room/session`을 **Core API라고 가정하지 않음**. 최신 공개 CLI와 Extension host/manifest를 재확인하고 브리지 구현.
- Extension manifest fields: `id`, `version`, `entrypoint` required; optional `dependencies`, `description`. 실제 구현 전에 0.12.4 wheel의 schema 검증.
- Second Brain native Core는 PeerHub 없이 독립 동작, PeerHub addon이 `brain://` refs만 전달. 원본 binary, secret, 민감 원문은 dispatch 기본 금지.
- `peerhub ask`는 실제 provider를 호출할 수 있음. 기술 검증에서도 quota/비용/기밀 전송 사전동의.
- `PEERHUB_DB`는 별도 local database로서 Second Brain canonical 원본이 아님. 동기화 폴더에 공유 SQLite를 두지 않음.

## MCP
- 표준 사양을 고정된 가상의 API 이름으로 구현하지 않는다. **MCP protocol version은 client/server 협상 또는 호환성 매트릭스**로 관리.
- Read resources / search tools / propose tools 분리. 원본 byte 읽기·외부 AI 전달·수정은 independent policy gate.
- 처음에는 stdio/local only. 공개 네트워크 server/원격 인증은 후속 별도 threat review.
- URI `brain://`는 SecondBrain application-defined locator이지 MCP가 본래 보장하는 URI scheme이 아니다.

## Obsidian
- Markdown은 사람 편집 가능한 Knowledge/Context의 UI. Evidence vault binary와 custody records는 Obsidian 자동 formatter/플러그인이 직접 수정해서는 안 됨.
- Obsidian 플러그인은 선택적. 파일 시스템 / `brain CLI`만으로 canonical file을 읽고 재구축 가능.

### 원문 링크
- https://github.com/greatgc-flow/Engram/releases/tag/v3.7.0
- https://github.com/greatgc-flow/peerhub/releases/tag/v0.12.4
- https://github.com/greatgc-flow/peerhub/blob/main/README.md
- https://modelcontextprotocol.io/specification/

## MCP current version alignment (2026-10-09)
공식 현행 MCP 사양은 **2026-07-28**이다(https://blog.modelcontextprotocol.io/posts/2026-07-28/). 기존 버전 대비 protocol-level handshake/session이 제거된 stateless core이며 HTTP 요청에는 버전·client capability metadata가 포함된다. R2는 초기에 **로컬 stdio**만 계획한다. MCP `2026-07-28`을 사용하는 경우에도 **adapter가 구현한 구체 SDK/transport의 상호운용 시험 전에는 'MCP 호환'을 주장하지 않는다**. 2025-11-25 클라이언트와 무조건 wire-compatible하다는 가정 금지.
