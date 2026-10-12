# START HERE — R5 / 한 화면 시작 (2026-10-10)

**상태:** 범용 개발/Second Brain 제품 모두 **Pre-TDD / 제품 구현 0 / 제품 테스트 미실행 / 정식 배포 불가**. 실행 가능한 것은 `kit.py`(설계 패키지 관리 도구)와 그 11개 로컬 테스트뿐이다.

## 최소 명령

```sh
python kit.py help
python kit.py catalog --summary
python kit.py catalog --id GD-001 --json
python kit.py catalog --find "원본" --profile secondbrain --limit 5
python kit.py verify
python -m unittest discover -s tests -v
```

**실제 작업/에러/교훈을 남기는 흐름** — 피드백은 `.kit_state/feedback.jsonl`에 추가 기록한다(단일 로컬 Writer; 동기화 폴더 다중 Writer 금지).

```sh
python kit.py feedback add --kind task --title "TDD slice-1" --note "착수 및 기대 출력"
python kit.py feedback note FB-UUID --kind progress --note "RED 재현" --ref TEST-001
python kit.py feedback note FB-UUID --kind error --note "실패 로그" --ref run-001
python kit.py feedback note FB-UUID --kind lesson --note "원인: 경계조건 누락"
python kit.py feedback show FB-UUID
python kit.py feedback verify
python kit.py feedback propose-close FB-UUID --release RC-001 --regression TEST-001 --observation "실환경 7일 관측" --lesson "회귀 케이스 추가" --evidence "sha256:..."
python kit.py feedback approve-close FB-UUID --reviewer independent --evidence "검토기록 URL/해시"
```

`FB-UUID`는 `add` 결과의 실제 ID로 교체한다. 리뷰어 문자열은 **본인 인증이 아닌 자체 진술**이다. 종결 근거의 참/거짓을 프로그램이 자동 판단하지 않는다. 실제 효과가 입증되지 않았다면 **OPEN**으로 둔다.

## 어디를 읽어야 하나? (독자별 1~3개 파일)

- **사용자:** 이 문서 → `README.md` → `standards/10_DECISIONS_FOR_OWNER.md`.
- **AI 개발자:** 이 문서 → `standards/00_CANONICAL_MAP.md` → 작업 프로필의 `00_START_HERE.md`.
- **QA/릴리스 담당:** `standards/05_TEST_MATRIX.md` → `standards/13_LIVE_TEST_PROCEDURE.md` → `standards/06_RELEASE_AND_HISTORY.md`.
- **감사 담당:** `standards/14_RECURSIVE_AUDIT.md` → `quality/AUDIT_REPORT.json` → `catalog/FEATURE_INVENTORY.csv`.

**제품별 첫 TDD**: 범용 `profiles/generic/docs/16_TDD_KICKOFF.md`; Second Brain `profiles/secondbrain/docs/50_FINAL_VERDICT_AND_TDD_ORDER.md`. 제품 CLI 예시는 *명세*이지 구현된 명령이 아니다.

**이동성:** 패키지 루트명·상위 폴더 경로는 바꿔도 된다. 로컬 `kit.py`는 자신의 위치 기준 상대 경로를 읽는다. 외부 Node/Windows/AI CLI의 한글·공백·장경로 호환은 **경고 + T3 실측**으로 확인하며 자동 경로 변조를 하지 않는다.
