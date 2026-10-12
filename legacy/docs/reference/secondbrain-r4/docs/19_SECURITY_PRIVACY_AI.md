# 19. Security / Privacy / AI Boundary / Prompt Injection

## 기본 Zero-Trust 정책
1. 입력 파일은 모두 **untrusted data**, 웹페이지/PDF/이메일 안의 AI 지시문은 명령이 아니다.
2. 파일 경로는 `Path.resolve()`와 실제 루트 경계 검증을 거쳐 traversal/junction/symlink/UNC/ADS 및 디바이스 특수파일을 제한. string prefix 비교만 하지 않는다. 아카이브는 member별 안전 경로·확장률·파일수·총 해제 크기 제한을 강제.
3. ingestion은 직접 실행/매크로 허용하지 않고, 확장자는 식별 단서일 뿐. MIME sniff / 악성 문서 경고 / parser isolation.
4. Vault의 **해시 식별 가능성**은 confidentiality가 아님. 파일명·메타데이터·검색 인덱스·로그도 비밀정보가 될 수 있다.
5. 민감도 `public/internal/private/restricted`, `legal_hold`, 별도 `egress_policy`를 독립 속성으로 관리.

## 외부 AI 전송 정책
- 기본 `deny_external_for_private_and_restricted=true`. 로컬 모델은 보안정책 내에서 별도 allow. PeerHub/Engram CLI 설치 여부가 개인정보 전송 동의와 같지 않다.
- 명시적 human approval 시에도 **목적·범위·제공자·모델·만료시각·자료 해시·가공본/원문 구분**의 disclosure receipt가 필요. 승인 없는 디렉터리 전체/자동 추출 업로드 금지.
- AI 입력: 꼭 필요한 최소 발췌/가명화, access-control filtering, prompt-injection sentinel, content boundary delimiters.
- AI 출력: `asserted/extracted/inferred/verified` 분리. 출처인용 없는 사실·확신 점수는 정답으로 승격 금지. 신뢰할 만한 human review와 별도 검증 절차 기록.
- 에이전트가 write/deletion/production을 제안할 수 있어도 policy gateway에서 검증 후 human confirm. 읽기 도구가 위험한 side-effect를 수행하지 않음.

## 계정/암호화/키
- OneDrive/Google Drive의 동기화 위치는 사용자가 선택한다. Provider의 접근 통제·공유 링크·실수 공유는 Core 밖 운영 위험으로 별도 체크.
- `restricted` 자료를 외부 클라우드에 올릴지, 클라이언트 암호화가 필요한지 **운영자 선택**. R2 기본은 자동 외부 공유 금지, 파일을 암호화하는 기능은 Out of Scope; 없는 암호화를 있는 것처럼 광고 금지.
- secret/key는 OS credential store/외부 secret manager 참조만 canonical config에 저장.
- 식별 가능한 민감 원본이 포함된 로그/검색 질의/LLM transcript는 기본 저장하지 않거나 최소화·필요 시 암호화.
- 삭제/retention은 법률보존과 충돌 가능: active Hold 우선, 파기 승인은 2단계 검토.

## Threat cases
- 악성 PDF의 `ignore previous instructions`가 LLM에게 전달: *문서 데이터*로만 렌더; policy 변경 불가.
- 파일이 `../../Windows/...`를 대상으로 하는 ZIP: quarantine; unpack 금지.
- 동기화 conflicted copy가 존재: original overwrite 금지, 보존·비교 후 triage.
- AI가 다른 evidence URI를 추측: 요청 actor scope 검사와 evidence visibility policy 검증.
- 다른 장치에서 `manifest.json`을 교체: hash-chain/secondary anchor discrepancy 표시, 정상이라고 단정하지 않음.

### 참고
OWASP LLM Top 10 2025 LLM01, https://owasp.org/www-project-top-10-for-large-language-model-applications/assets/PDF/OWASP-Top-10-for-LLMs-v2025.pdf
