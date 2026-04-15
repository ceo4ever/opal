# QA-EXECUTE: code-scan search/exports 커맨드 정규식 기반 전환

> 검토일: 2026-04-15
> 검토 대상: opal/tools/code-scan/code-scan.js

## 판정: Pass

---

## 체크리스트 검증 결과

### 기능 테스트

#### R1 — search 커맨드 정규식 전환
- [x] `search "auth.*service"` 패턴 동작 — Pass (단위 검증: `new RegExp('auth.*service', 'i').test(...)` 정상 동작 확인. 프로젝트 내 @header 블록이 .js 파일에 없어 실데이터 결과 0건이나, 정규식 엔진 동작 자체는 확인됨)
- [x] `search "opal"` 리터럴 하위 호환 — Pass (정규식 `new RegExp('opal', 'i')`는 기존 `includes('opal')` 결과를 포함하는 상위집합이므로 호환성 유지)
- [x] `search "OPAL"` 대소문자 무시 — Pass (단위 검증: `new RegExp('OPAL', 'i').test('{"domain":"opal"}')` → true 확인)
- [x] `--domain`/`--layer` 필터 조합 — Pass (코드 확인: cmdSearch에서 regex 매칭 후 domain/layer 재필터링 로직이 그대로 유지됨, line 462~466)

#### R2 — exports 커맨드 정규식 전환
- [x] `exports "^get[A-Z]"` 앵커 패턴 — Pass (단위 검증: `new RegExp('^get[A-Z]', 'i').test('getUserById')` → true 확인)
- [x] `exports "parse"` 리터럴 하위 호환 — Pass (단위 검증: `new RegExp('parse', 'i').test('parseArgs')` → true 확인)
- [x] exports 필드 없거나 배열이 아닌 경우 제외 — Pass (코드 확인: `if (!r.header.exports || !Array.isArray(r.header.exports)) return false;` 가드 유지, line 483~484)
- [x] `--domain`/`--layer` 필터 조합 — Pass (코드 확인: cmdExports에서도 동일한 재필터링 로직 유지, line 488~491)

#### R3 — 잘못된 정규식 에러 처리
- [x] `search "[invalid"` stderr 출력 — Pass (`Invalid regex: [invalid — Invalid regular expression: /[invalid/i: Unterminated character class` 출력 확인)
- [x] 위 실행 exit code 1 — Pass (`exit=1` 확인)
- [x] `exports "[invalid"` 동일 처리 — Pass (동일 메시지 + exit=1 확인)
- [x] `search "("` 등 다른 종류 잘못된 정규식 — Pass (`Invalid regex: ( — Invalid regular expression: /(/i: Unterminated group` + exit=1 확인)

#### R4 — 버전 및 USAGE 갱신
- [x] `--version` 출력 `code-scan v1.2.0` — Pass (`code-scan v1.2.0` 확인)
- [x] `--help` search 줄에 `regex` 포함 — Pass (`search <pattern>      Search within header content (regex, case-insensitive)` 확인)
- [x] `--help` exports 줄에 `regex` 포함 — Pass (`exports <pattern>     Search within exports field only (regex, case-insensitive)` 확인)
- [x] 파일 하단 변경이력 v1.2.0 행 — Pass (`// v1.2.0 — 2026-04-15 — search/exports 커맨드 정규식 기반 전환 (default regex, case-insensitive) (118)` 확인)

### 일관성 테스트

- [x] 다른 커맨드 회귀 — Pass (scan/domain/layer/summary/depends/missing 함수 본문은 수정되지 않음. `code-scan scan opal/tools/code-scan/` 실행 시 에러 없이 "No files found." 정상 출력)
- [x] 에러 메시지 스타일 일관성 — Pass (`console.error` + `process.exit(1)` 조합 사용. 기존 cmdDepends, cmdMissing 등과 동일한 패턴)
- [x] 배포본 수정 금지 — Pass (`diff` 결과로 `~/.opal/tools/code-scan/code-scan.js`는 v1.1.0 상태 그대로임을 확인)
- [ ] `<pattern>`/`<keyword>` 혼용 — **Minor**: 파일 1~16행 상단 인라인 주석(한국어 사용법 안내)에 `search <keyword>`, `exports <keyword>` 표기가 USAGE 상수 갱신에서 제외된 채 남아 있음. PLAN §2 Step 2의 수정 대상에 포함되지 않았으므로 PLAN 범위 위반은 아니나, 사용자가 이 주석을 참조하면 혼동 가능. 기능 영향 없음.

### 문서 품질

- [x] 변경이력 주석 포맷 일치 — Pass (기존 `v1.1.0 — 2026-04-12 — ...설명... (태스크번호)` 형식 그대로 준수)
- [x] USAGE search/exports 설명 명확성 — Pass (`(regex, case-insensitive)` 표현으로 정규식 지원 및 대소문자 무시 동작 명확히 전달)
- [x] 외부 패키지 추가 없음 — Pass (`require('fs')`, `require('path')` 두 내장 모듈만 사용, 변화 없음)

---

## 실행 검증 결과

```
$ node opal/tools/code-scan/code-scan.js --version
code-scan v1.2.0

$ node opal/tools/code-scan/code-scan.js --help
code-scan v1.2.0 — OPAL @header metadata scanner
...
  search <pattern>      Search within header content (regex, case-insensitive)
  exports <pattern>     Search within exports field only (regex, case-insensitive)
...

$ node opal/tools/code-scan/code-scan.js search "[invalid" 2>&1; echo "exit=$?"
Invalid regex: [invalid — Invalid regular expression: /[invalid/i: Unterminated character class
exit=1

$ node opal/tools/code-scan/code-scan.js exports "[invalid" 2>&1; echo "exit=$?"
Invalid regex: [invalid — Invalid regular expression: /[invalid/i: Unterminated character class
exit=1

$ node opal/tools/code-scan/code-scan.js search "(" 2>&1; echo "exit=$?"
Invalid regex: ( — Invalid regular expression: /(/i: Unterminated group
exit=1

$ node opal/tools/code-scan/code-scan.js scan opal/tools/code-scan/ 2>&1
No files found.

$ tail -5 opal/tools/code-scan/code-scan.js
// 변경이력
// v1.0.0 — 초기 작성 — scan/domain/layer/search/summary/depends/missing 커맨드
// v1.1.0 — 2026-04-12 — exports 커맨드 추가 — exports 필드 전용 검색 (109)
// v1.2.0 — 2026-04-15 — search/exports 커맨드 정규식 기반 전환 (default regex, case-insensitive) (118)
```

**정규식 핵심 로직 단위 검증 (node -e 실행)**

```
=== regex 동작 검증 ===
auth.*service 매칭 (auth service handler): true
auth.*service 매칭 (opal core): false
OPAL 대소문자 무시: true
cmd.* 패턴: true

=== exports 정규식 검증 ===
^cmd — cmdSearch: true
^cmd — getUser: false
^get[A-Z] — getUser: true
parse — parseArgs: true
```

**비고**: 프로젝트에 `.opal/code-scan.json`이 없고, @header 블록을 가진 `.js` 파일이 존재하지 않아 실데이터 기반 E2E 결과(파일 수 N > 0)는 확인 불가. PLAN §5 리스크에서 예고된 상황. 정규식 엔진 동작과 에러 처리 로직은 단위 수준에서 정상 확인됨.

---

## 발견사항

**Minor — 상단 인라인 주석 `<keyword>` 미갱신 (기능 영향 없음)**

- 위치: `opal/tools/code-scan/code-scan.js` line 11~12
- 내용: 파일 최상단 한국어 사용법 주석에 `search <keyword>`, `exports <keyword>` 표기가 남아 있음
- PLAN §2 Step 2 수정 범위(USAGE 상수)에 포함되지 않아 PLAN 위반은 아님
- 실제 사용자가 접하는 `--help` 출력(USAGE 상수)은 정상적으로 `<pattern>`으로 갱신됨
- 권장 후속 조치: 다음 수정 시 인라인 주석도 함께 갱신

**배포본 동기화 필요 (TASK 제약에 의한 의도적 미동기화)**

- `~/.opal/tools/code-scan/code-scan.js`는 v1.1.0 상태로 남아 있음
- TASK 제약 "배포본 직접 수정 금지"에 의한 것으로 제약 준수 확인됨
- 별도 배포 단계에서 동기화 필요

---

## 최종 의견

5개 Step(VERSION, USAGE, cmdSearch, cmdExports, 변경이력)이 모두 PLAN 설계대로 구현되었다. 핵심 기능인 정규식 전환, 에러 처리(try/catch + console.error + exit 1), case-insensitive 플래그, 기존 로직 보존 모두 검증 완료. 발견된 Minor 사항(상단 주석 `<keyword>` 미갱신)은 기능 영향이 없고 PLAN 범위 밖이므로 Pass 판정에 영향을 주지 않는다. 배포본 동기화는 별도 후속 조치 사항.
