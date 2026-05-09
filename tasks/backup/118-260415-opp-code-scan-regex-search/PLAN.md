# PLAN: code-scan search/exports 커맨드 정규식 기반 전환

> 작성일: 2026-04-15
> 입력: TASK.md
> 출력: PLAN.md

---

## 1. 현황 조사

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `opal/tools/code-scan/code-scan.js` | OPAL @header 메타 스캐너 본체 (단일 파일 CLI) | ✅ 수정 |
| `~/.opal/tools/code-scan/code-scan.js` | 배포본 (사용자 홈 설치본) | ❌ (TASK 제약 — 직접 수정 금지, 별도 배포 단계에서 복사) |
| `opal/tools/code-scan/code-scan.json` 등 프로젝트 설정 | 스캐너 scope/exclude 설정 | ❌ (변경 없음) |

### 현재 상태

- **버전**: `VERSION = '1.1.0'` (line 26)
- **USAGE 문자열** (line 36~74): `search <keyword>  Search within header content`, `exports <keyword>  Search within exports field only` — 두 커맨드 모두 단순 키워드 검색 표현만 있음. 정규식 언급 없음.
- **`cmdSearch`** (line 447~462): `keyword.toLowerCase()` → `JSON.stringify(r.header).toLowerCase().includes(kw)` — 헤더 JSON 전체를 lowercase 문자열로 만들어 substring 포함 여부 검사.
- **`cmdExports`** (line 464~482): `keyword.toLowerCase()` → `r.header.exports.some(e => e.toLowerCase().includes(kw))` — exports 배열의 각 항목을 lowercase 비교하여 substring 포함 여부 검사.
- **나머지 커맨드**(`cmdScan`, `cmdDomain`, `cmdLayer`, `cmdSummary`, `cmdDepends`, `cmdMissing`): 정확 일치(`===`) 또는 substring 비교가 내부 로직용이며 사용자 키워드 입력 대상이 아니므로 정규식 전환 대상 아님.
- **변경이력 주석** (line 611~613): 파일 하단에 `// 변경이력` 헤더 + `// v1.0.0 ...`, `// v1.1.0 ...` 2줄 존재. 다음 줄에 v1.2.0 행을 추가하면 됨.
- **에러 처리 스타일 기존 관례**: `process.exit(1)`와 `console.error(...)` 조합 사용 (line 230, 449, 466, 514 등). stderr 출력은 `console.error` 또는 `process.stderr.write` 두 스타일이 혼재하나, 기존 `cmdSearch`/`cmdExports`는 `console.error`를 사용. 일관성 유지.

### 영향 범위

- **사용자 사용 패턴 호환성**: 기존 리터럴 키워드(예: `search "auth"`)는 정규식으로 해석되어도 그대로 매칭된다. 단, 사용자가 `search "."` 같은 특수문자를 리터럴로 검색하던 경우 동작이 달라질 가능성이 있음 — TASK §제약 "기존 리터럴 키워드는 정규식으로도 동일하게 동작해야 함 (하위 호환)" 에 부합하는 범위이며, 일반 키워드(영문/한글/숫자)는 모두 안전.
- **다른 커맨드에는 영향 없음** — `cmdSearch`, `cmdExports` 두 함수의 내부 로직만 수정.
- **배포본(`~/.opal/tools/code-scan/code-scan.js`)**: TASK 제약에 의해 본 태스크에서는 수정 금지. 별도 배포 단계에서 수작업 또는 배포 스크립트로 동기화.
- **버전 상승**: `--version` 출력 형식이 `code-scan v1.1.0` → `code-scan v1.2.0` 으로 변경. `--help`에 regex 표현 반영.

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 |
|---|----------|------|
| - | (없음) | - |

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `opal/tools/code-scan/code-scan.js` | ① `VERSION` 상수 `1.1.0` → `1.2.0` <br> ② `USAGE` 문자열의 `search`/`exports` 설명을 정규식 지원으로 갱신 <br> ③ `cmdSearch`: `includes(kw)` → `RegExp(keyword, 'i').test(...)` + try/catch SyntaxError 처리 <br> ④ `cmdExports`: `e.toLowerCase().includes(kw)` → `RegExp(keyword, 'i').test(e)` + try/catch SyntaxError 처리 <br> ⑤ 파일 하단 변경이력 주석에 v1.2.0 행 추가 |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| - | (없음) | - |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | `VERSION` 상수 갱신 | `code-scan.js` | 낮음 |
| 2 | `USAGE` 문자열 `search`/`exports` 설명 갱신 | `code-scan.js` | 낮음 |
| 3 | `cmdSearch` 정규식 전환 + 에러 처리 | `code-scan.js` | 중간 |
| 4 | `cmdExports` 정규식 전환 + 에러 처리 | `code-scan.js` | 중간 |
| 5 | 변경이력 주석 v1.2.0 행 추가 | `code-scan.js` | 낮음 |
| 6 | 수동 검증 (기능 AC + 회귀) | - | 중간 |

> 순서 1~5는 동일 파일의 독립적 변경이나, 구현 편의상 위→아래 순으로 진행한다. 순서 6은 전 단계 완료 후 일괄 검증.

### 핵심 설계

#### 설계 결정 1: 정규식 컴파일 위치

- **결정**: `keyword`에서 `RegExp` 객체를 한 번만 컴파일하여 filter 루프 외부에 보관. 루프 내부에서는 `.test()`만 호출.
- **근거**: 성능 (파일 수 N개에 대해 N번 재컴파일 회피) + 명확한 try/catch 범위 분리.

#### 설계 결정 2: 에러 메시지 포맷

- **결정**: `console.error(\`Invalid regex: ${keyword} — ${err.message}\`)` 후 `process.exit(1)`.
- **근거**: TASK R3 AC에 명시된 포맷 `"Invalid regex: [invalid — <에러 메시지>"` 를 그대로 따른다. `err.message`는 V8의 `Invalid regular expression: /.../: Unterminated character class` 같은 상세 메시지를 노출하여 디버깅 편의 제공.

#### 설계 결정 3: 플래그

- **결정**: `new RegExp(keyword, 'i')` — 대소문자 무시(`i`) 플래그만 적용.
- **근거**: 기존 구현의 `toLowerCase()` 하위 호환. multiline/dotall 등은 불필요 (exports 항목은 단일 식별자 문자열, header JSON은 직렬화된 한 줄 문자열).

#### 설계 결정 4: `cmdSearch`의 검색 대상

- **결정**: 기존처럼 `JSON.stringify(r.header)` 결과를 대상으로 `regex.test(...)` 호출. lowercase 변환은 제거(플래그 `i`로 대체).
- **근거**: 기존 계약 유지 — "헤더 전체 텍스트"가 검색 범위. AC "`search \"auth.*service\"` 실행 시 `auth`와 `service`를 모두 포함하는 파일이 반환"은 직렬화된 JSON 문자열에 대한 정규식 매칭으로 자연스럽게 만족됨.

#### 설계 결정 5: `cmdExports`의 매칭 방식

- **결정**: `r.header.exports.some(e => regex.test(e))` — 배열 내 하나라도 매칭되면 true. 기존 `includes` → `test` 1:1 치환.
- **근거**: 배열 구조와 "하나라도 매칭" 의미를 그대로 유지하면서 substring → regex 로만 전환. `^`/`$` 앵커 지원도 이 구조에서 자연스럽게 동작 (각 항목 전체 문자열이 test 대상).

#### 코드 스케치

```js
// cmdSearch (수정안)
function cmdSearch(projectRoot, config, opts) {
  const keyword = opts.commandArg;
  if (!keyword) { console.error('Usage: code-scan search <pattern>'); process.exit(1); }

  let regex;
  try { regex = new RegExp(keyword, 'i'); }
  catch (err) {
    console.error(`Invalid regex: ${keyword} — ${err.message}`);
    process.exit(1);
  }

  const all = scanHeaders(projectRoot, config, { ...opts, domain: null, layer: null });
  const matches = all.filter(r => regex.test(JSON.stringify(r.header)));

  const filtered = matches.filter(r => {
    if (opts.domain && r.header.domain !== opts.domain) return false;
    if (opts.layer && r.header.layer !== opts.layer) return false;
    return true;
  });
  output(filtered, opts);
}

// cmdExports (수정안)
function cmdExports(projectRoot, config, opts) {
  const keyword = opts.commandArg;
  if (!keyword) { console.error('Usage: code-scan exports <pattern>'); process.exit(1); }

  let regex;
  try { regex = new RegExp(keyword, 'i'); }
  catch (err) {
    console.error(`Invalid regex: ${keyword} — ${err.message}`);
    process.exit(1);
  }

  const all = scanHeaders(projectRoot, config, { ...opts, domain: null, layer: null });
  const matches = all.filter(r => {
    if (!r.header.exports || !Array.isArray(r.header.exports)) return false;
    return r.header.exports.some(e => regex.test(e));
  });

  const filtered = matches.filter(r => {
    if (opts.domain && r.header.domain !== opts.domain) return false;
    if (opts.layer && r.header.layer !== opts.layer) return false;
    return true;
  });
  output(filtered, opts);
}
```

#### USAGE 문자열 수정 스케치

```
  search <pattern>      Search within header content (regex, case-insensitive)
  exports <pattern>     Search within exports field only (regex, case-insensitive)
```

> 커맨드 argument 이름도 `<keyword>` → `<pattern>`으로 함께 갱신하여 정규식 의미를 드러낸다.

#### 변경이력 주석 추가 스케치

```
// v1.2.0 — 2026-04-15 — search/exports 커맨드 정규식 기반 전환 (default regex, case-insensitive) (118)
```

---

## 3. 실행 체크리스트

> 총 6개 Step. 전부 동일 파일(`opal/tools/code-scan/code-scan.js`) 수정이므로 Step 1~5는 하나의 세션에서 순차 진행한다. Step 6은 검증.

### Step 1: `VERSION` 상수 갱신
- [ ] 완료
- **파일**: `opal/tools/code-scan/code-scan.js`
- **작업 내용**: line 26 `const VERSION = '1.1.0';` 를 `const VERSION = '1.2.0';` 로 변경
- **완료 기준**: 파일 내 `VERSION = '1.2.0'` 문자열이 존재하고, `1.1.0`은 변경이력 주석 외의 위치에 남아있지 않다
- **테스트**: `node opal/tools/code-scan/code-scan.js --version` → `code-scan v1.2.0` 출력
- **의존**: 없음

### Step 2: `USAGE` 문자열의 search/exports 설명 갱신
- [ ] 완료
- **파일**: `opal/tools/code-scan/code-scan.js`
- **작업 내용**: `USAGE` 상수(line 36~74) 내 2줄 수정
  - `search <keyword>      Search within header content` → `search <pattern>      Search within header content (regex, case-insensitive)`
  - `exports <keyword>     Search within exports field only` → `exports <pattern>     Search within exports field only (regex, case-insensitive)`
- **완료 기준**: `USAGE` 문자열에 `regex` 표현이 search/exports 설명에 각각 포함된다
- **테스트**: `node opal/tools/code-scan/code-scan.js --help | grep -E "search|exports"` → 두 줄 모두 `regex` 포함 확인
- **의존**: 없음 (Step 1과 독립적이나 동일 파일이므로 순차 처리)

### Step 3: `cmdSearch` 정규식 전환 + 에러 처리
- [ ] 완료
- **파일**: `opal/tools/code-scan/code-scan.js`
- **작업 내용**: `cmdSearch` 함수(line 447~462) 본문을 "핵심 설계 §코드 스케치"의 수정안으로 교체
  - `const kw = keyword.toLowerCase();` 제거
  - try/catch로 `new RegExp(keyword, 'i')` 감싸기 (SyntaxError 시 `console.error` + `process.exit(1)`)
  - filter 내 `JSON.stringify(r.header).toLowerCase().includes(kw)` → `regex.test(JSON.stringify(r.header))`
  - Usage 에러 메시지의 `<keyword>` → `<pattern>`
- **완료 기준**: 
  - `new RegExp(keyword, 'i')` 호출이 try/catch 블록 내에 존재
  - `regex.test(...)` 호출로 매칭 수행
  - domain/layer 재필터링 로직은 기존 그대로 유지
- **테스트**: 
  - `node opal/tools/code-scan/code-scan.js search "opal"` → 정상 결과 반환 (리터럴 회귀)
  - `node opal/tools/code-scan/code-scan.js search "[invalid"` → stderr에 `Invalid regex: [invalid — ...` 출력 + exit code 1 (`echo $?`로 확인)
- **의존**: 없음

### Step 4: `cmdExports` 정규식 전환 + 에러 처리
- [ ] 완료
- **파일**: `opal/tools/code-scan/code-scan.js`
- **작업 내용**: `cmdExports` 함수(line 464~482) 본문을 "핵심 설계 §코드 스케치"의 수정안으로 교체
  - `const kw = keyword.toLowerCase();` 제거
  - try/catch로 `new RegExp(keyword, 'i')` 감싸기 (SyntaxError 시 `console.error` + `process.exit(1)`)
  - `r.header.exports.some(e => e.toLowerCase().includes(kw))` → `r.header.exports.some(e => regex.test(e))`
  - 배열 체크(`!r.header.exports || !Array.isArray(...)`)는 기존 그대로 유지
  - Usage 에러 메시지의 `<keyword>` → `<pattern>`
- **완료 기준**: 
  - `regex.test(e)` 매칭 수행
  - exports 배열 유효성 체크 유지
  - domain/layer 재필터링 유지
- **테스트**: 
  - `node opal/tools/code-scan/code-scan.js exports "opal"` → 정상 결과 반환 (리터럴 회귀)
  - `node opal/tools/code-scan/code-scan.js exports "[invalid"` → stderr에 `Invalid regex: [invalid — ...` 출력 + exit code 1
- **의존**: 없음

### Step 5: 변경이력 주석 갱신
- [ ] 완료
- **파일**: `opal/tools/code-scan/code-scan.js`
- **작업 내용**: 파일 하단 변경이력 주석(line 611~613)에 v1.2.0 행 추가
  ```
  // v1.2.0 — 2026-04-15 — search/exports 커맨드 정규식 기반 전환 (default regex, case-insensitive) (118)
  ```
- **완료 기준**: 파일 최하단에 v1.2.0 행이 존재
- **테스트**: `tail -5 opal/tools/code-scan/code-scan.js` 로 v1.2.0 행 육안 확인
- **의존**: Step 1 (버전 상수와 변경이력 행의 버전 문자열이 일치해야 함)

### Step 6: 통합 검증 (수동 실행)
- [ ] 완료
- **파일**: - (실행만)
- **작업 내용**: 아래 커맨드를 실행하고 결과를 STATE.md 또는 DONE.md에 기록
  1. `node opal/tools/code-scan/code-scan.js --version` → `code-scan v1.2.0`
  2. `node opal/tools/code-scan/code-scan.js --help` → search/exports 두 줄에 `regex` 포함
  3. `node opal/tools/code-scan/code-scan.js search "opal"` → 기존 동작과 동일하게 `opal` 포함 파일 반환 (리터럴 하위 호환)
  4. `node opal/tools/code-scan/code-scan.js search "auth.*service"` 또는 프로젝트 실데이터 기반의 유사 패턴 → 두 토큰을 모두 포함하는 파일 반환 (정규식 동작 증빙)
  5. `node opal/tools/code-scan/code-scan.js exports "^cmd"` 또는 유사한 앵커 패턴 → 해당 접두어로 시작하는 exports 항목 보유 파일 반환
  6. `node opal/tools/code-scan/code-scan.js search "[invalid" ; echo "exit=$?"` → stderr에 에러 메시지, exit=1
  7. `node opal/tools/code-scan/code-scan.js exports "[invalid" ; echo "exit=$?"` → stderr에 에러 메시지, exit=1
- **완료 기준**: 위 7개 커맨드가 모두 기대대로 동작
- **테스트**: 위 커맨드 자체가 테스트. 프로젝트에 `.opal/code-scan.json`이 없는 경우 실제 데이터 검증이 제한될 수 있으니, `opal/` 소스 트리를 대상으로 수행
- **의존**: Step 1~5

---

## 4. QA 체크리스트

### 기능 테스트

#### R1 — search 커맨드 정규식 전환
- [ ] `search "auth.*service"` 실행 시 `auth`와 `service`를 모두 포함하는 파일만 반환된다 (`auth` 단독 또는 `service` 단독만 포함하는 파일은 제외)
- [ ] `search "opal"` 실행 시 기존 v1.1.0과 동일한 결과 집합이 반환된다 (리터럴 하위 호환)
- [ ] `search "OPAL"` (대문자) 실행 시 `opal` 포함 파일이 반환된다 (case-insensitive 동작)
- [ ] `--domain`/`--layer` 필터와 조합 시 정상 동작 (정규식 매칭 후 filter 재적용)

#### R2 — exports 커맨드 정규식 전환
- [ ] `exports "^get[A-Z]"` 실행 시 `get` + 대문자로 시작하는 exports를 가진 파일만 반환된다
- [ ] `exports "parse"` 실행 시 `parse`를 포함하는 exports(`parseArgs`, `parseHeader` 등)를 가진 파일이 반환된다 (리터럴 하위 호환)
- [ ] exports 필드가 없거나 배열이 아닌 파일은 결과에서 제외된다 (기존 동작 유지)
- [ ] `--domain`/`--layer` 필터와 조합 시 정상 동작

#### R3 — 잘못된 정규식 에러 처리
- [ ] `search "[invalid"` 실행 시 stderr에 `Invalid regex: [invalid — <V8 에러 메시지>` 형태로 출력된다
- [ ] 위 실행의 exit code가 1이다
- [ ] `exports "[invalid"` 실행 시 동일하게 처리된다
- [ ] `search "("` (닫히지 않은 괄호) 등 다른 종류의 잘못된 정규식도 동일한 방식으로 처리된다

#### R4 — 버전 및 USAGE 갱신
- [ ] `--version` 출력이 `code-scan v1.2.0` 이다
- [ ] `--help` 출력의 `search` 줄에 `regex` 표현이 포함된다
- [ ] `--help` 출력의 `exports` 줄에 `regex` 표현이 포함된다
- [ ] 파일 하단 변경이력 주석에 `v1.2.0 — 2026-04-15 — ...` 행이 추가되어 있다

### 일관성 테스트

- [ ] 다른 커맨드(`scan`, `domain`, `layer`, `summary`, `depends`, `missing`)의 동작은 변경되지 않았다 (회귀 테스트)
- [ ] 에러 메시지 스타일(`console.error` + `process.exit(1)`)이 파일 내 다른 에러 처리와 일관된다
- [ ] Usage 인자 표기 `<pattern>`과 `<keyword>`가 파일 전체에서 혼용되지 않는다 (search/exports만 `<pattern>`, 나머지는 기존 유지)
- [ ] 배포본(`~/.opal/tools/code-scan/code-scan.js`)은 본 태스크에서 수정하지 않았다 (제약 준수)

### 문서 품질

- [ ] 변경이력 주석 포맷이 기존 항목(`v1.0.0`, `v1.1.0`)과 동일하다 (날짜, 설명, 태스크 번호 참조)
- [ ] USAGE의 search/exports 설명이 사용자에게 정규식 지원을 명확히 전달한다
- [ ] `node` 내장 모듈 외 외부 패키지가 추가되지 않았다 (`package.json` 변화 없음 / `require` 구문 변화 없음)

---

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| 기존 리터럴 키워드 중 정규식 특수문자(`.`, `*`, `?`, `[`, `(`, `+` 등)를 포함한 경우 동작 차이 발생 | 사용자가 `search "node.js"` 등 점(.)을 리터럴로 검색하던 경우 결과가 의도와 다를 수 있음 (매칭 범위가 넓어질 뿐 결과는 상위집합이라 대개 문제 없음) | TASK 제약 범위(영문/한글/숫자 키워드) 내 하위 호환 확보. 변경이력 주석에 "default regex" 명시하여 사용자 인지 유도. 필요 시 후속 태스크에서 `--literal` 플래그 추가 가능 (현재는 과잉 설계로 배제) |
| V8 `RegExp` 에러 메시지가 OS/버전에 따라 미세하게 달라질 가능성 | QA에서 문자열 완전 일치 검증 시 실패 위험 | AC를 "메시지 내에 `Invalid regex: <pattern> —` 접두사 포함" 수준으로 완화해서 검증 (완전 일치 강요 금지) |
| 배포본(`~/.opal/`)과 소스본의 버전 불일치 | 사용자가 여전히 v1.1.0 동작을 경험 | 본 태스크 범위 밖. DONE 시 "배포본 동기화 필요" 후속 조치를 PM에게 명시 보고 |
| `.opal/code-scan.json`이 없는 환경에서 QA 실행 시 결과 0건으로 거짓 통과 가능 | 정규식 동작 검증 불가 | QA Step 6에서 `opal/` 소스 트리를 대상으로 실행하며, 결과 파일 수가 0이 아님을 확인하는 일차 검증을 선행 |

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-04-15 | 초기 작성 |
