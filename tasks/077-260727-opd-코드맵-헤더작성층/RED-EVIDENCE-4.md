# RED-EVIDENCE-4 — 태스크 077 재작업 (결함 C, PM 실측 진단)

> 작성: opal-test-agent (mode: red) | 재작업 — extractHeader "@header 언급 이후 첫 { " 근접 제약 부재(결함 C)에 대한 RED 테스트 보강.
> 작성자≠구현자 원칙(`~/.opal/references/harness/red-first.md` §2) 준수 — 본 파일 작성자는 GREEN(구현)을 수행하지 않는다.
> 기존 `RED-EVIDENCE.md`(Phase 1 최초 RED), `RED-EVIDENCE-2.md`(결함 A/B 1차 재작업 — 이미 GREEN 완료), `RED-EVIDENCE-3.md`(결함 B: `validate --changed`의 exclude 미적용 — 본 세션 실행 시점 기준 이미 GREEN 완료 확인, 아래 §4 참조)는 수정하지 않았다. 본 파일은 결함 C 전용 신규 증거다.
> Scope: `opal/tools/code-scan/tests/test-resolve-header.js` 수정(신규 테스트 7건 추가) + `opal/tools/code-scan/tests/fixtures/header-proximity/` 신규 자기완결 픽스처 트리 추가. **`code-scan.js`·규칙 문서(`header-standard.md` 등)는 전혀 수정하지 않았다.**

---

## 1. 결함 요약 (PM 실측 진단)

`extractHeader`(`code-scan.js:369-373`, 실질 로직은 `extractHeaderFromContent` `code-scan.js:330-367`)가 "`@header` 문자열 등장 이후 **처음 나타나는 `{`**"를 무조건 헤더 블록 시작으로 간주한다(`code-scan.js:337`: `content.indexOf('{', idx + 7)` — 근접 제약 없음).

- 근거 코드: `code-scan.js:333-338`.
- 결과: 본문에서 `@header`를 **산문으로 설명**하고 그 뒤 임의 위치에 **무관한 JSON 블록**(설정 예시 등)이 오는 문서 파일이, 그 무관 블록을 자신의 헤더로 오인당한다. 실측: `node opal/tools/code-scan/code-scan.js scan opal/core/references/pm/code-scan-management.md --json` → 문서 내 `.opal/code-scan.json` 설정 예시 JSON(`scopes`/`extensions`/`exclude`)이 파일 헤더로 반환됨(실제로는 `@header` 블록 없음).
- 대조: git HEAD 비교 경로(`classifyUncovered`, `code-scan.js:435-445`)는 이미 `hasNearbyHeaderBlock`(`code-scan.js:423-428`)로 근접 검사(토큰 뒤 5자 이내 `{`)를 거쳐 같은 오탐을 막고 있다. **이 근접 검사가 라이브 스캔 경로(`extractHeader`/`extractHeaderFromContent`, 즉 `scan`/`missing`/`resolveHeader` 등 전체 조회 경로)에는 적용되어 있지 않다** — 이것이 결함 C다.
- 파급: 이 오탐 때문에 `validate`가 해당 파일을 `uncovered`(필수 5필드 결손으로 `sub: incomplete`)로 오판정해 CLOSE 게이트를 차단할 수 있다.

## 2. 실행 명령

```bash
node --test opal/tools/code-scan/tests/test-resolve-header.js
node --test "opal/tools/code-scan/tests/*.js"
node --test opal/tools/code-scan/tests/test-regression.js   # 골든 회귀 영향 확인용 별도 실행
```

- cwd: 저장소 루트(`/Volumes/Data/AIStudio/workspace/ai-framework`)
- Node 버전: **v25.8.2**
- 실행 방식: `node:test` + `node:assert/strict` + `spawnSync` CLI 블랙박스(신규 CLI 테스트 2건) + `require()` 직접 호출(신규 unit 테스트 5건, `code-scan.js`의 기존 `module.exports.extractHeader` 재사용 — 대역 객체·몽키패치 0건, `opal/core/PRINCIPLES.md` §4 "Don't fake it" 준수).
- 신규 픽스처는 `opal/tools/code-scan/tests/fixtures/header-proximity/`에 자기완결 트리로 추가했다(자체 `.opal/code-scan.json` 보유, 저장소 루트 설정·기존 픽스처 트리 무변경).

## 3. 신규 테스트 7건 (TS-077-C-1~4)

| TC | 목적 | 기대 판정 | 결과 |
|----|------|----------|------|
| TS-077-C-1 (unit) | `extractHeader(prose-mention.md)` — 산문 `@header` 언급 + 뒤따르는 무관 JSON 블록 | `null` 반환 | **FAIL (RED)** |
| TS-077-C-1 (CLI) | `scan --json`/`missing` — 위 파일 | `scan` 결과 미등장 + `missing` 목록에 등장 | **FAIL (RED)** |
| TS-077-C-2 (대조군) | `extractHeader(normal-header.js)` — 표준 JSDoc 헤더 | 인식(module/exports 필드 일치) | PASS |
| TS-077-C-3 (대조군) | `extractHeader(header-then-unrelated-brace.js)` — 정상 헤더 + 뒤쪽 무관 `{` | 인식 + 무관 필드 미병합 | PASS |
| TS-077-C-4 (대조군, Python) | `extractHeader(python-docstring.py)` | 인식(module 일치) | PASS |
| TS-077-C-4 (대조군, `//` 주석) | `extractHeader(slash-comment.js)` | 인식(module 일치) | PASS |
| TS-077-C-4 (대조군, Vue HTML 주석) | `extractHeader(html-comment.vue)` | 인식(module 일치) | PASS |

### 3.1 실행 결과 — `test-resolve-header.js` 단독

```
ℹ tests 25
ℹ pass 23
ℹ fail 2
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
```

exit code = **1**

**RED 확인 — TS-077-C-1 (unit) 실패 (실제 assertion 출력)**:
```
✖ TS-077-C-1 (결함 C): extractHeader — 산문 @header 언급 + 뒤따르는 무관 JSON 블록은 null 반환해야 함 (2.630292ms)
AssertionError [ERR_ASSERTION]: [RED expect] 산문 @header 언급 뒤 무관 JSON 블록은 헤더로 인정되면 안 됨(근접 제약 필요), got {"scopes":{"be":"workspace/backend/"},"extensions":[".py",".js"],"exclude":["node_modules","fixtures"]}
  actual: { scopes: { be: 'workspace/backend/' }, extensions: [ '.py', '.js' ], exclude: [ 'node_modules', 'fixtures' ] }
  expected: null
  operator: 'strictEqual'
```

**RED 확인 — TS-077-C-1 (CLI) 실패 (실제 assertion 출력)**:
```
✖ TS-077-C-1 (결함 C): scan --json — 산문 언급 파일이 결과에 미등장 + missing에 등장 (72.695041ms)
AssertionError [ERR_ASSERTION]: [RED expect] prose-mention.md는 scan --json 결과에 등장하면 안 됨, got {"scopes":{"be":"workspace/backend/"},"extensions":[".py",".js"],"exclude":["node_modules","fixtures"]}
  actual: { scopes: { be: 'workspace/backend/' }, extensions: [ '.py', '.js' ], exclude: [ 'node_modules', 'fixtures' ] }
  expected: undefined
  operator: 'strictEqual'
```

두 케이스 모두 현행 구현이 근접 제약 없이 산문 뒤 무관 JSON 블록을 헤더로 오인함이 실측으로 확인되었다 — PM이 보고한 결함이 테스트 코드로 재현되었다(진성 RED).

**보강 확인 (CLI 수동 재현, 테스트 코드 외부에서 직접 실행)**:
```bash
$ cd opal/tools/code-scan/tests/fixtures/header-proximity && node ../../../code-scan.js missing
All files have @header blocks.
```
→ 6개 파일(그중 1개는 실제로는 헤더 없음) 전체가 "헤더 보유"로 오판정됨을 CLI 레벨에서도 직접 확인.

**대조군 PASS 확인 (TS-077-C-2~4, 5건 전부)**:
```
✔ TS-077-C-2 (대조군 — 회귀 0): 정상 JSDoc 헤더는 계속 인식되어야 함
✔ TS-077-C-3 (대조군 — 회귀 0): 정상 헤더 뒤에 무관한 { 블록이 와도 계속 인식되어야 함
✔ TS-077-C-4 (대조군 — 회귀 0): Python docstring 포맷 헤더는 계속 인식되어야 함
✔ TS-077-C-4 (대조군 — 회귀 0): "//" 라인 주석 포맷 헤더는 계속 인식되어야 함
✔ TS-077-C-4 (대조군 — 회귀 0): Vue HTML 주석 포맷 헤더는 계속 인식되어야 함
```
표준 헤더(JSDoc/Python docstring/`//` 주석/Vue HTML 주석)와 "정상 헤더 + 뒤쪽 무관 `{`" 케이스는 현재도 정상 인식되며, 결함 C 수정 후에도 이 5건은 계속 PASS로 유지되어야 한다(GREEN 워커의 회귀 가드 기준선).

## 4. 전체 스위트 결과 (glob, `opal/tools/code-scan/tests/*.js`)

```
ℹ tests 97
ℹ pass 95
ℹ fail 2
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
```

**exit code = 1**

실패 2건은 정확히 §3의 TS-077-C-1 (unit) / TS-077-C-1 (CLI) 뿐이다(다른 파일에서의 실패 0건).

| 구분 | 건수 | 상태 |
|------|------|------|
| 기존 90건 (RED-EVIDENCE-3 시점 기준 전체 스위트) | 90 | **전부 PASS 유지 — 회귀 0건**. 특히 `TS-077-B-1`/`TS-077-B-2`(RED-EVIDENCE-3의 결함 B RED 테스트)가 본 세션 실행 시점에는 이미 **PASS**로 확인됨 — 즉 결함 B는 본 작업 착수 전에 이미 GREEN 완료된 상태였다(§5 근거 참조, 실측: `git diff --stat opal/tools/code-scan/code-scan.js`가 1119 insertions로 이미 반영되어 있음). 본 재작업은 이 사실을 변경하지 않았다. |
| 신규 TS-077-C-1 (unit) | 1 | FAIL (의도된 RED) |
| 신규 TS-077-C-1 (CLI) | 1 | FAIL (의도된 RED) |
| 신규 TS-077-C-2~4 (대조군 5건) | 5 | 전부 PASS |
| **합계** | **97** | 90 + 7 = 97 (pass 95 = 90 + 5, fail 2 = C-1 unit + C-1 CLI) — 계산 일치 |

## 5. 골든 회귀(`test-regression.js`) 영향 확인 — 필수 확인 항목

지시에 따라 골든 회귀에 미치는 영향을 **실행으로 확인**했다:

```bash
$ node --test opal/tools/code-scan/tests/test-regression.js
ℹ tests 18
ℹ pass 18
ℹ fail 0
```
**exit code = 0**

**결론: 골든 회귀는 이번 재작업(테스트/픽스처 추가만, 구현 무수정)으로는 전혀 영향받지 않는다 — 18건 전부 PASS, 신규 실패 0건.**

이유: 이번 세션은 `code-scan.js` 구현을 전혀 수정하지 않았고(§0 확인), 신규 픽스처 `tests/fixtures/header-proximity/`는 `test-regression.js`가 참조하는 `legacy-repo`/`golden` 픽스처와 무관한 별도 자기완결 트리이므로 골든 8커맨드 출력·S-19 이중 격리 판정에 개입하지 않는다.

**단, 향후 GREEN(결함 C 실제 수정) 이후에는 재확인이 필요하다** — PM 프롬프트가 경고한 대로, `extractHeader`에 근접 제약이 추가되면 저장소 전체 `scan` 결과에서 (이 결함으로 인한) 오탐 헤더 보유 문서들이 빠지게 되어 `missing` 카운트가 늘어날 수 있다. 다만 `test-regression.js`의 골든 8파일은 `legacy-repo` 픽스처(코드 파일만 구성, 산문+무관 JSON 오탐 패턴 없음) 기준이므로, 현재 확인한 바로는 골든 자체에는 영향이 없다. GREEN 구현 완료 후 `node --test opal/tools/code-scan/tests/test-regression.js`를 다시 실행해 바이트 동일성이 유지되는지는 GREEN 워커가 재확인해야 한다(본 RED 단계에서는 구현 변경이 없으므로 골든 불변 확인만으로 충분함).

## 6. 격리 검증 (PM-6 / PRINCIPLES §4)

- 신규 픽스처 트리(`tests/fixtures/header-proximity/`)는 기존 픽스처 트리(`codemap-repo`/`legacy-repo`/`violations`/`tiebreak`/`schema`/`golden`)와 완전히 분리된 신규 디렉토리이며, 자체 `.opal/code-scan.json`(scope: `root: "./"`, extensions에 `.md` 추가)을 보유한다. 저장소 루트 `.opal/code-scan.json`과 기존 픽스처는 전혀 건드리지 않았다.
- 신규 unit 테스트 5건은 `code-scan.js`가 이미 노출하는 `module.exports.extractHeader`를 `require()`로 직접 호출한다(기존 `TS-008` 테스트가 이미 사용하는 동일 패턴 — `delete require.cache[CODE_SCAN_JS]; const mod = require(CODE_SCAN_JS);`). 신규 CLI 테스트 2건은 기존 `run(cwd, args)` 헬퍼(실 `spawnSync` 서브프로세스)를 그대로 재사용했다 — 신규 헬퍼 함수 추가 없음.
- 저장소(ai-framework) git 상태 확인:
  ```
  $ git status --porcelain -- opal/tools/code-scan/
   M opal/tools/code-scan/code-scan.js        ← 본 세션 이전(결함 B GREEN)에 이미 발생한 변경, 본 작업으로 인한 변경 아님
  ?? opal/tools/code-scan/code-map-hook.js    ← 태스크 077 기존 미커밋 산출물
  ?? opal/tools/code-scan/run.sh              ← 태스크 077 기존 미커밋 산출물
  ?? opal/tools/code-scan/tests/              ← 태스크 077 기존 미커밋 산출물 트리 전체(본 작업의 신규 파일 포함)

  $ git diff --stat -- opal/tools/code-scan/code-scan.js
   opal/tools/code-scan/code-scan.js | 1135 ++++++++++++++++++++++++++++++++++++-
   1 file changed, 1119 insertions(+), 16 deletions(-)
  ```
  → `code-scan.js`의 변경은 이번 세션에서 발생한 것이 아니라(직접 편집 이력 없음), 이전 GREEN 작업(결함 A/B)이 이미 누적해 놓은 미커밋 diff다. 본 작업(mode: red)은 이 파일을 열람만 했고 **한 글자도 수정하지 않았다**.
  ```
  $ git status --porcelain -- opal/tools/code-scan/tests/fixtures/header-proximity/
  ?? opal/tools/code-scan/tests/fixtures/header-proximity/
  ```
  → 신규 픽스처 트리는 온전히 신규 추가분이며, 기존 픽스처 파일을 수정한 이력은 0건이다.
- `code-scan.js`, 저장소 루트 `.opal/code-scan.json`, 규칙 문서(`header-standard.md`/`header-rules.md` 등)는 수정하지 않았다 — 스코프 제한 준수. 외부 저장소 참조 없음. 커밋 없음.

## 7. 다음 단계

GREEN(구현) 워커가 `code-scan.js`의 `extractHeaderFromContent`(`code-scan.js:330-367`, 특히 337행 `const braceStart = content.indexOf('{', idx + 7);`)에 근접 검사를 추가해야 한다 — 기존 `hasNearbyHeaderBlock`(`code-scan.js:423-428`)과 동등한 계약(`@header` 토큰 직후 공백만 허용하고 `{`가 와야 함)을 라이브 스캔 경로에도 적용하되, 코드 중복을 피하려면 `hasNearbyHeaderBlock`을 `extractHeaderFromContent` 내부에서 먼저 호출해 근접하지 않으면 조기에 `null`을 반환하는 방식을 권고한다(정확한 구현 방식은 GREEN 워커 재량이나, 본 RED가 고정한 계약 — §3 표 7건 — 을 반드시 만족해야 함). 수정 후 다음을 재확인해야 한다:
1. `node --test opal/tools/code-scan/tests/test-resolve-header.js` — TS-077-C-1 (unit/CLI) 2건이 PASS로 전환되고, 기존 25건(신규 5건 대조군 포함, 재작업 이전 18건) 전부 PASS 유지.
2. `node --test "opal/tools/code-scan/tests/*.js"` — 97건 전부 PASS, exit 0.
3. `node --test opal/tools/code-scan/tests/test-regression.js` — 골든 8커맨드 재확인. §5에서 예고한 대로 저장소 전체 `scan`/`missing` 결과의 오탐 헤더 문서 제거로 인한 실사용 영향(문서 파일들의 `missing` 편입)이 있을 수 있으나, `legacy-repo`/`golden` 픽스처 자체(코드 파일만 구성)에는 이 패턴이 없으므로 골든 바이트 동일성은 유지될 것으로 예상된다 — GREEN 워커가 실행으로 최종 확인.
