# TASK: code-scan search/exports 커맨드 정규식 기반 전환

> 작성일: 2026-04-15 | 작업 유형: 개선 | 적용 스킬: opp | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

`code-scan.js`의 `search`와 `exports` 커맨드를 단순 substring 매칭에서 정규식(regex) 기반 매칭으로 전환한다. 별도 플래그 없이 기본 동작이 정규식이 된다.

## 배경

현재 `search`와 `exports` 커맨드는 `JSON.stringify(r.header).toLowerCase().includes(kw)` 방식의 단순 substring 매칭을 사용한다. 이로 인해 `auth.*service`, `^get[A-Z]` 같은 패턴 검색이 불가능하다.

## 배경 분석 (대화에서 도출)

- `search` 커맨드 (line 447~462): `JSON.stringify(r.header).toLowerCase().includes(kw)` — 헤더 전체 텍스트 대상
- `exports` 커맨드 (line 464~482): `r.header.exports.some(e => e.toLowerCase().includes(kw))` — exports 배열 대상
- 나머지 커맨드(`domain`, `layer`, `depends`, `missing`, `scan`, `summary`)는 정확한 값 일치 방식으로 동작 — 정규식 불필요
- 현재 버전: v1.1.0

## 확정된 설계 방향 (대화에서 합의)

1. `search`와 `exports` 두 커맨드만 변경 대상
2. 정규식을 기본(default)으로 적용 — `--regex` 플래그 추가 없음
3. `--literal` 역방향 옵션도 추가 안 함 (정규식이 리터럴을 포함하므로)
4. 잘못된 정규식 입력 시 명확한 에러 메시지 출력 필요
5. 버전 v1.2.0으로 올림

## 요구사항

- [ ] **R1** — `search` 커맨드 정규식 전환
  - 무엇을: `cmdSearch`에서 `includes(kw)` 를 `new RegExp(keyword, 'i')` 기반 매칭으로 교체
  - 어디에: `opal/tools/code-scan/code-scan.js` → `cmdSearch` 함수
  - 왜: 패턴 검색 지원 (확정 방향 §1~3)
  - AC: `search "auth.*service"` 실행 시 `auth`와 `service`를 모두 포함하는 파일이 반환된다. `search "auth"` 실행 시 기존과 동일하게 동작한다 (리터럴 검색 호환).

- [ ] **R2** — `exports` 커맨드 정규식 전환
  - 무엇을: `cmdExports`에서 `includes(kw)` 를 정규식 매칭으로 교체
  - 어디에: `opal/tools/code-scan/code-scan.js` → `cmdExports` 함수
  - 왜: exports 필드 패턴 검색 지원 (확정 방향 §1~3)
  - AC: `exports "^get[A-Z]"` 실행 시 `get`으로 시작하고 다음 문자가 대문자인 exports 항목이 있는 파일이 반환된다.

- [ ] **R3** — 잘못된 정규식 에러 처리
  - 무엇을: `try/catch`로 `new RegExp()` 감싸고, SyntaxError 시 명확한 메시지 출력 후 종료
  - 어디에: `cmdSearch`, `cmdExports` 각각
  - 왜: 확정 방향 §4
  - AC: `search "[invalid"` 실행 시 `"Invalid regex: [invalid — <에러 메시지>"` 형태의 오류가 stderr에 출력되고 exit code 1로 종료된다.

- [ ] **R4** — USAGE 문자열 및 변경이력 갱신
  - 무엇을: USAGE의 `search`/`exports` 설명에 정규식 지원 명시. 버전 v1.2.0으로 업데이트. 변경이력 행 추가
  - 어디에: `opal/tools/code-scan/code-scan.js` → `VERSION` 상수, `USAGE` 문자열, 파일 하단 변경이력 주석
  - 왜: 문서 일관성
  - AC: `--help` 출력에서 `search`와 `exports` 설명에 "regex" 또는 "정규식" 표현이 포함된다. `--version` 출력이 `code-scan v1.2.0`이다.

## 제약 조건

- 소스 파일 경로: `opal/tools/code-scan/code-scan.js` (배포본 `~/.opal/` 직접 수정 금지)
- 다른 커맨드(`domain`, `layer`, `depends`, `missing`, `scan`, `summary`)는 변경하지 않는다
- Node.js 내장 모듈만 사용 (외부 패키지 추가 없음)
- 기존 `search "auth"` 같은 리터럴 키워드는 정규식으로도 동일하게 동작해야 함 (하위 호환)

## 기술 스택

- Node.js (내장 모듈: `fs`, `path`)
- 정규식: `new RegExp(pattern, 'i')` (대소문자 무시)

## 관련 문서

- 소스: `opal/tools/code-scan/code-scan.js`
