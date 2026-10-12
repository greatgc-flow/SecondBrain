# 03. CLI 도움말 및 최소 토큰 계약

도구의 **실제 명령**은 `python kit.py help [catalog|verify|feedback]`가 정본이다. 본 문서는 익숙한 진입 예시만 제공하며 서브옵션을 중복 정의하지 않는다.

```sh
python kit.py catalog --summary                         # 한 줄 상태
python kit.py catalog --id GD-001 --json                # 한 요구의 구조화 계약
python kit.py catalog --find "원본" --limit 5            # 최소 맥락만 조회
python kit.py verify --json                              # 정적 무결성/추적, 외부 네트워크 0
python kit.py feedback add --kind task --title "TDD1" --note "시작"
python kit.py feedback note FB-UUID --kind progress --note "RED" --ref TEST-001
python kit.py feedback show FB-UUID                      # 현재 작업 인수인계
python kit.py feedback verify                            # 로컬 이력 위변조 정적 확인
```

`catalog --json`은 AI용. 일반 CLI 실행 결과와 경고는 분리한다. `--help`는 하위 명령마다 재귀적으로 사용 가능. 미지원 기능/문자 경로/장경로는 명확한 WARN 또는 실패로 표시하고 임의의 복구/경로 변환을 강제하지 않는다.

**주의:** `brain ingest`, `brain verify`, `brain export` 등은 **제품 사양**에 등장하지만 이 패키지에서 실행되지 않는다. PeerHub `--resume`도 외부 설치버전 기능이므로 발견/호환 검사 후에만 opt-in 사용한다.
