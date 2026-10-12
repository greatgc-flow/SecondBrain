# 06. Config·Secret·권한·신뢰경계

1. configuration precedence = CLI explicit > environment > per-project config > packaged defaults (제품별 ADR로 재정의 가능). effective config는 secret redaction 후 출력.
2. 미설정 secret은 fail closed; `.env` 실제값/토큰 예제를 배포·로그·fixture에 포함 금지.
3. 권한은 actor/operation/resource/tenant/context로 검증. 모델 지시·문서 내용·로그를 authority로 취급 금지.
4. 외부 자료는 prompt-injection, path traversal, deserialization, XXE/ZIP bomb, SSRF 등 입력 형태별 위협 검토. 허가 없는 네트워크·메일·파일 변경 금지.
5. 데이터 분류(public/internal/confidential/restricted)마다 egress allowlist와 operator approval. AI 전송·embedding·telemetry·log 각각 별도 판단.
6. 개인/민감정보의 보존·삭제·권리 의무는 규제/고객에 맞게 프로젝트 프로파일에서 정의. 무기한 캐시 금지.
7. branch/release CI는 최소권한; 외부 PR/fork에 credential bearing live runner 자동 노출 금지. GitHub Actions는 검증된 full SHA pinning 권고.
8. 사고 발생 시 containment→로그/evidence 유지(최소화)→영향분석→안전 재가동→재발방지. 비밀을 feedback ticket에 복제하지 않는다.
