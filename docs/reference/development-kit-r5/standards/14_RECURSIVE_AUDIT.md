# 14. 재귀적 MECE 감사 — 종/횡/5 Whys/반례

- **종방향:** 문제/목표 → 요구 ID → 계약/ADR → 구현(없으면 NOT_IMPLEMENTED) → 시험 ID/반례 → 결과(없으면 NOT_RUN) → 릴리스 후보 → 운영효과 → 피드백 CLOSED 또는 OPEN.
- **횡방향:** CLI↔설정↔OS, 원본↔해시↔메타↔클라우드↔복원, AI↔권한↔토큰↔평가, 사고↔수정↔회귀↔릴리스↔SLO.
- **재귀:** Root/프로필/폴더/파일/JSON 필드/시나리오/테스트마다 Owner, 입력, 출력, 실패, 정본, 의존성, 재현성을 묻는다.
- **MECE 한계:** 범위가 유한한 카탈로그의 중복·누락 검출은 가능하지만 모든 현실적 사용자 상황의 완전한 망라는 수학적으로 증명할 수 없다. 발견한 새 반례를 새로운 테스트에 환류한다.

## 이번 감사에서 직접 발견하고 수정한 것

1. CLI의 **하드코딩 `288` 및 `40`** → 원본 CSV/시나리오에서 산출하고 ID 유일성·테스트 참조·필수 항목을 검증.
2. 문서 `TRIAGED/FIXED/OBSERVING`와 도구의 3상태 불일치 → 상태는 `OPEN/CLOSE_REQUESTED/CLOSED`로 단일화, 단계는 `NOTED` 이력.
3. 오류·lesson·작업 progress 저장 구멍 → `feedback add task`, `feedback note`, `feedback show`, `feedback verify`.
4. 무조건 `CLOSED` 이후 기록 및 수정 → 재발이 생기면 반드시 reopen, 잘못된 전이는 실패.
5. 변경 도중 경합과 JSONL 손상 → O_EXCL 단일 Writer 잠금 + fsync + 순번/prev/hash/transition 확인. 다중 PC 보장 아님.
6. 거대한 목록과 토큰 낭비 → `catalog --id/--find/--limit/--json`, 루트 한 페이지의 Quickstart.
7. 정적 통과와 실증 통과 혼선 → 구조/유닛/통합/실OS·Cloud/유료 AI 5층을 구분하고 미실행 공개.
8. 원본 이력 유실 위험 → 전 버전 ZIP 바이트 그대로 `history/` 유지, 현행 정본 목록 별도.

## 반례에 남는 리스크 (출시 전 해결)

- **외부 앵커 없는 이벤트 해시**는 전체 파일 교체 공격에 취약. 증거 보존용 custody에는 별도 신뢰 앵커 필요.
- **동기화 폴더에서 두 작성자**는 로컬 O_EXCL로 막을 수 없음. 공식 단일 Writer + 클라우드 오프라인 반례 실증 필요.
- **개발 키트의 `verify`는 SHA manifest 무결성만 검사**; 공격자가 패키지와 manifest 전체를 교체하는 공격은 별도 서명/신뢰 경로가 필요.
- **실환경 T3/T4, 제품 구현, 릴리스 테스트**는 미실행. 그 시나리오는 완료 판정 불가.
- **릴리스/휠/winget**은 제품이 아직 없고 repository 지정되지 않았으므로 NO-GO.
