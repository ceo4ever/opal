# DONE: code-scan search/exports 커맨드 정규식 기반 전환

> 완료일: 2026-04-15 | 스킬: opp | 모드: agentic

## 완료 요약

`code-scan.js`의 `search`와 `exports` 커맨드를 정규식(regex) 기반 매칭으로 전환했다. 별도 플래그 없이 기본 동작이 정규식이 된다.

## 변경 파일

| 파일 | 변경 내용 |
|------|----------|
| `opal/tools/code-scan/code-scan.js` | VERSION `1.1.0` → `1.2.0`, cmdSearch/cmdExports 정규식 전환, USAGE 갱신, 변경이력 추가 |

## 구현 내용

- **R1** `cmdSearch` — `JSON.stringify(r.header).toLowerCase().includes(kw)` → `regex.test(JSON.stringify(r.header))` (case-insensitive `i` 플래그)
- **R2** `cmdExports` — `e.toLowerCase().includes(kw)` → `regex.test(e)` (배열 구조 유지)
- **R3** 잘못된 정규식 입력 시 `Invalid regex: <pattern> — <메시지>` stderr 출력 + exit code 1
- **R4** VERSION `1.2.0`, USAGE `<keyword>` → `<pattern>` + `(regex, case-insensitive)`, 변경이력 v1.2.0 행 추가

## 사용 예

```bash
# 정규식 패턴 검색 (신규)
code-scan search "auth.*service"
code-scan exports "^get[A-Z]"
code-scan search "user|account" --domain auth

# 기존 리터럴 검색 (하위 호환)
code-scan search "opal"
code-scan exports "parse"

# 잘못된 정규식 → 에러
code-scan search "[invalid"
# Invalid regex: [invalid — Invalid regular expression: ...
```

## 후속 조치

- **배포본 동기화 필요**: `~/.opal/tools/code-scan/code-scan.js` (v1.1.0) → 캡틴이 `install-mac.sh`로 별도 배포

## QA 결과

- QA-PLAN.md: Pass
- QA-EXECUTE.md: Pass (Minor 1건 — 상단 인라인 주석 `<keyword>` 미갱신, 기능 무관)
