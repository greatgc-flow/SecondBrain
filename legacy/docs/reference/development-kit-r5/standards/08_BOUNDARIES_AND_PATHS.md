# 08. OS, Cloud, 권한, 데이터 경계

모든 상대경로는 `Path(__file__).resolve()`에서 찾는다. `SECOND_BRAIN_ROOT`는 사용자가 설정하고 경로를 바꿔도 ID/참조는 그대로 유지한다. OS 별 임시/캐시는 root 밖에 저장하고 상태 저장소는 주기적으로 보관한다. 경로 문자열을 파일 내용 식별자로 사용하지 않는다.

- OneDrive / Google Drive 폴더는 파일 보관·동기화 계층. 로컬에 실제 bytes가 없으면 원본 hash 검증에서 FAIL/WARN으로 차단한다.
- 동일 vault에는 단일 Writer. 다중 PC는 capture-only, canonical commit은 승인된 한 컴퓨터. 드라이브 버전 기록 ≠ 독립 백업.
- 증거 파일 원본 byte와 JSONL event는 불변 정책. WORM이라는 광고 금지. 외부 anchor/독립 snapshot이 없으면 완전한 변조 불가 입증 불가.
- 소스 메타(EXIF, ACL, 원출처 시간)는 파일 복제 전에 취득 가능한 범위를 기록. 취득 이전 사실은 시스템이 보증 못함.
- 모델, MCP, PeerHub, telemetry adapter에 민감자료 기본 전송 금지, 외부처리는 명시 승인 시에만.
- 파일/폴더 이름 Unicode·공백·Windows 예약문자·MAX_PATH, Node.js process quoting, PowerShell 버전별 옵션은 별도 compatibility matrix로 검사. 지원 안 되는 조합은 명확한 Warning + 수동 우회. silent rename이나 바이트 수정 금지.

모든 path 관련 제약은 `catalog/COMPATIBILITY_NOTES.md`에 버전과 재검토일을 함께 기록한다.
