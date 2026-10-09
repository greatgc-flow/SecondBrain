# Engram / PeerHub / Brain / AI의 엄격한 책임 분리

**Engram:** OS/CLI tools 관리, Python/toolchain. 증거 데이터 소유 X.
**PeerHub:** Core=Peer·Stream·Record·Offset; 선택 extension=AI 협업 및 실행. 법률 원본/요건/Gate canonical 소유 X.
**Second Brain:** original immutable-by-policy, metadata provenance, sync writer, release/eval/Legal Hold authoritative.
**AI Agent:** read/context suggestion, limited local changes via ports. 금지: Vault/Legal Hold overwrite, unapproved external model transfer, file deletion, auto evidence readiness promotion.

실제 모델·쿼터·PeerHub 서브커맨드 지원은 도입 시 capability discovery. 로그는 path/token/full transcript 기본 비보존. `brain://` logical identifier and evidence refs only; 툴별 실제 directory/root config는 Core 밖.

**장기 작업 체크포인트:** source HEAD, exact original SHA, schema version, pending tasks, last verified tests, permitted actions, known risks, next owner. 다음 AI는 '이미 완료됨'을 그대로 신뢰하지 않고 verify/reconcile부터 수행.
