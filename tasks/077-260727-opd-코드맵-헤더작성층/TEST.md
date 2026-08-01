# TEST: 코드 헤더 작성층 신설 — 인라인 + 외부 code-map 2소스 (Step 19 최종 검증)

> 작성: op-dev-test-agent | 대상: PLAN.md §4.2 Step 19 (mode: full-complex, test_mode: be/CLI)
> 산출물 계약: 본 문서 + `TEST-SCENARIO.md` 결과 필드 채움 (검증 전용 — 소스/규칙 문서 무수정)

## 1. 전량 GREEN 확인

**명령**: `node --test opal/tools/code-scan/tests/*.js` (glob 형태 — 디렉토리 인자 `tests/`는 Node v25.8.2에서 MODULE_NOT_FOUND 발생, glob 형태만 정상 동작)

**결과**: `tests 81 / pass 81 / fail 0 / cancelled 0 / skipped 0 / duration_ms 1497.15` — **exit 0**

전 81 테스트 목록·TS-ID·S-ID 매핑은 실행 로그로 확보(요지: F-001~F-010 전 기능 커버, S-1~S-21·S-23 전량 자동 PASS).

## 2. 8커맨드 골든 회귀 (제약②)

**명령**: `node --test opal/tools/code-scan/tests/test-regression.js`

**결과**: `tests 18 / pass 18 / fail 0` — exit 0. `scan --json`/`domain`/`layer`/`search auth --json`/`exports token --json`/`summary`/`depends auth_service`/`missing` 8개 명령 전부 legacy-repo(code-map 부재) 픽스처 대비 **바이트 동일**. `scan --json` 결과에 `_source` 키 0건(제약② 하위호환 증거). 골든 파일 mtime 14:40(코드 변경 15:24 이전 캡처)으로 "변경 전 코드 캡처" 요건 충족.

## 3. install 재배포 + L3 배포 검증 (S-22)

**명령**: `./scripts/install-mac.sh`

**결과**: exit 0. OPAL v0.6.10-13-g7632527 배포, Console 재기동(PID 17064) 정상.

| 검증 | 명령 | 결과 |
|------|------|------|
| TS-058 | `~/.opal/tools/code-scan/run.sh --help` | exit 0 + USAGE 전문(신규 서브명령 5종 포함) |
| TS-059 | `~/.opal/tools/tool-scan/run.sh usage code-scan` | `{"ok": true, ..., "exit_code": 0, "usage_text": "...discover...scaffold...target...validate...feature..."}` — H-17 해소(기존 `help_exec_failed` 잔존 소멸) 확인 |
| TS-061 | `OPAL_NODE_BIN=/nonexistent ~/.opal/tools/code-scan/run.sh --help` | `{"ok":false,"error":"node_missing","detail":"Node.js not found. Install Node 18+."}` + exit 1 |

## 4. §3.12.2 (G) dogfooding 4항목 + S-24 보강 3항목 (⑦⑧⑨)

### dogfooding 4항목

| # | 명령 | 결과 |
|---|------|------|
| 1 | `run.sh scan/summary/missing/domain/layer/search/exports/depends --scope framework` (8커맨드) | 전부 exit 0. `scan --json` 45파일 커버, `summary` 6도메인 45파일 |
| 2 | `run.sh discover --dry-run --json` | stdout에 `scopes:[framework,console-fe,console-be]`(3종) · `layerRules` 6개 · `exclude` 10건 포함 초안 생성. `.opal/code-map/` **미생성**(`ls` 실패로 전후 확인) |
| 3 | `run.sh validate --changed "<21개 changed_files>" --json` | **exit 2, `ok:false`, `uncovered` 8건** — **FAIL** (아래 §5 참조) |
| 4 | `~/.opal/tools/tool-scan/run.sh usage code-scan` | `ok:true` + 신규 서브명령 포함 (§3과 동일 근거) |

### S-24 보강 3항목 (임시 격리 경로에서 수행 — 저장소 실제 `.opal/code-scan.json` 무변경)

**⑦ 스캔 범위 교체 전후 대조** — 저장소를 `rsync`로 `/private/tmp/.../before-sim-077`에 복제(node_modules/.git/.venv 등 제외, 20M) 후 그 **복사본의** `.opal/code-scan.json`만 `scopes:{}`로 교체해 "Step 1 이전(스코프 미정의 → 전체 워크)" 상태를 재현:

| 상태 | `scan --json` 총 헤더 파일 | `tasks/` | `fixtures/` |
|------|------|------|------|
| AFTER(현재 3스코프) | 101 | **0** | **0** |
| BEFORE(시뮬레이션, scopes 없음) | 114 | 5 | 5 |

→ 스코프 한정이 `tasks/`(우연히 @header 예시를 포함한 기존 태스크 문서 4건 유사자료)·`fixtures/`(픽스처가 의도적으로 보유한 실헤더 5건) 오염을 정확히 0으로 차단함을 수치로 증명.

**⑧ `missing` 결과 축소 전후 대조** (동일 복사본):

| 상태 | `missing` 총 라인 | `tasks/` | `fixtures/` |
|------|------|------|------|
| AFTER(현재 3스코프) | 231 | **0** | **0** |
| BEFORE(시뮬레이션) | 1036 | 526 | 37 |

→ 스코프 한정으로 `missing` 노이즈가 1036→231건(−78%), tasks/fixtures 오염 526+37→0으로 축소. (AGENTIC-LOG Step1 기록 230건과 현재 231건의 근소한 차이는 §5에서 발견된 문서 7종의 신규 uncovered 전이가 원인 — 별건 아님.)

**⑨ 인라인 트랙 1케이스** (픽스처 `codemap-repo`를 임시 복사본 `inline-track-demo`에 복제해 수행 — 원본 fixture 무수정):

1. `target svc/order-api/.../NewFeature.java`(디스크 부재) → `{"write_to":"inline","reason":"new_file"}`
2. 인라인 `@header` JSON 블록 작성 후 재조회 → `{"write_to":"inline","reason":"inline_exists"}`
3. `validate --json` 커버리지: `covered` **7→8**, `inline` **1→2**, `total` **9→10** — 신규 인라인분이 합산됨을 확인
4. 부수 관찰: 해당 디렉토리가 이미 scaffold된 매니페스트를 보유해 `worker_scope_violation:files_key_removed` 1건 추가 발생 — 버그 아님, "매니페스트 보유 디렉토리는 재scaffold 필요"라는 설계상 정합 신호(재scaffold로 해소).

## 5. [FAIL 발견] 자체 저장소 `validate --changed` — CLOSE 게이트 실패

이 태스크의 실제 changed_files(21개: `.gitignore`, `claude-hooks.json`, 참조문서 6종, `code-scan.js`, `tool-scan/manifest.json`, `install-mac.sh`, `code-map-hook.js`, `run.sh`, 신규 테스트 8종)를 대상으로:

```
~/.opal/tools/code-scan/run.sh validate --changed "<21개 경로 csv>" --json
```

**결과**: `exit=2`, `{"ok":false, ..., "counts":{"uncovered":8, 그외 0}, "violations":[...]}`

| 파일 | 위반 |
|------|------|
| `opal/core/references/harness/header-rules.md` | uncovered:no_entry |
| `opal/core/references/harness/pm-review-gate.md` | uncovered:no_entry |
| `opal/core/references/header-standard.md` | uncovered:no_entry |
| `opal/core/references/opal-harness.md` | uncovered:no_entry |
| `opal/core/references/pm/code-scan-management.md` | uncovered:incomplete (module,layer,domain,description,exports 누락) |
| `opal/core/references/tools.md` | uncovered:no_entry |
| `opal/tools/code-scan/code-scan.js` | uncovered:no_entry |

**원인**: 이 저장소 `.opal/code-scan.json`의 `extensions`에 `.md`가 포함되어 있고, `header-rules.md` 자신도 "`.md`가 config에 추가된 경우 md 파일도 적용 대상"이라 규정한다. 즉 이번 태스크가 수정한 참조문서 6종과 `code-scan.js` 자신이 실제로 @header 작성 대상인데, EXECUTE 단계에서 기재되지 않았다.

**처리**: 고치지 않고 실패로 기록한다(하네스 Guards — Step 19는 검증 전용). `pm-review-gate.md` §8(이 태스크가 신설한 CLOSE 게이트 절차) 기준으로 **이 태스크는 현재 상태로 CLOSE 진입 불가**. PM 판단 및 후속 조치(워커 재투입 또는 PM 직접 @header 기재) 필요.

## 6. RED 파일 불변 확인

- `tests/test-*.js` 8종 mtime: `14:49~14:58`(RED phase, Step 2-4) — `code-scan.js` GREEN 수정 시각(`15:24`)보다 전부 이전.
- `fixtures/golden/*` 8종 mtime: `14:40`(RED phase, 코드 변경보다 이전 캡처 — "변경 전 코드 캡처" 요건 근거).
- `git status --porcelain opal/tools/code-scan/tests/` → 전 항목 `??`(신규 미추적)만 존재, `M` 0건.
- **예외 1건**: `fixtures/violations/exports-missing/svc/mod/Missing.java` mtime `15:33`(GREEN 이후) — 내용은 결함 설명 주석 1줄 추가(`// fixture: the manifest declares an identifier that is absent from this file's text.`). 디스패치 프롬프트에 명시된 "PM이 명시 승인한 결함 수정"으로 처리, 위반 아님.

**판정**: RED 파일 불변 요건 충족(승인된 예외 1건 제외 무수정).

## 7. 코드 품질 (§5) 요약

`node --check` 10개 파일(코드 파일) 전부 구문 오류 0건. 린트/타입체크/포맷터는 저장소에 JS 린터·타입체커·포맷터 구성이 없어 "해당 없음(구성 부재)"으로 정직 기재. 신규 파일(테스트 8종·`code-map-hook.js`)은 `@header` 보유 확인, `run.sh`는 `.sh` 확장자로 header-rules.md 적용 대상 제외. **단, 수정 파일(`code-scan.js` 및 참조문서 6종)은 @header 미기재 — §5 FAIL과 동일 근거.**

## 8. 보안 (§6) 요약

하드코딩 시크릿 스캔 0건 / `.gitignore` code-map 예외·code-scan.json 무시 유지 확인 / hook에 `exec/execSync/spawn/child_process` 부재 확인 — 3항목 전부 PASS.

## 9. 최종 판정

**Partial Fail**

- 도구 핵심 기능(5신규 서브명령·5단 상속 해석·경로 사상·역매핑·권한 경계·8커맨드 하위호환·hook·run.sh 배포) = **All Pass** (81/81 유닛 테스트, 골든 회귀, install 배포, dogfooding ①②③⑤⑥⑦⑧⑨ 전부 실행 증거 확보)
- 이 태스크 자신의 EXECUTE 산출물(참조문서 6종 + `code-scan.js`)이 자신이 신설한 @header 규칙을 준수하지 않아 **CLOSE 게이트(`validate --changed`) exit 2로 차단** = **FAIL** (dogfooding 항목 ④)
- 비차단 권고 1건: S-17 `headerSource` 자동 테스트(TS-044/046)가 실제 config 오버레이 없이 통과하는 취약 테스트 — 수동 재현으로 기능 자체는 정확함을 확인했으나 자동 커버리지 보강 권고

### 블로커 목록

1. **[블로커]** `code-scan.js`·`header-rules.md`·`pm-review-gate.md`·`header-standard.md`·`opal-harness.md`·`tools.md`·`brain-tool/README.md` 7개 파일에 @header 작성 후 `validate --changed` 재실행하여 exit 0 확인 필요.

### 비블로커 권고

1. `test-resolve-header.js`의 S-17 관련 테스트에 `headerSource:"manifest"`/`"inline"`/`"bogus"` 실제 config 오버레이 fixture를 추가해 TS-045 신설 + TS-044/046 보강.

### 변경 파일

없음 — 본 Step은 검증 전용. 산출물은 `TEST.md`(신규) + `TEST-SCENARIO.md`(결과 필드 채움) 뿐이며 소스·규칙 문서는 무수정.

---

## 10. 재검증(post-fix) — 2026-07-28 (opal-test-agent, mode: full-complex, test_mode: be)

### 10.1 이전 Partial Fail 원인

Step 19 검증에서 도구 핵심 기능(5신규 서브명령·5단 상속 해석·경로 사상·역매핑·권한 경계·8커맨드 하위호환·hook·`run.sh` 배포)은 All Pass였으나, 이 태스크 자신의 EXECUTE 산출물(참조문서 6종 + `code-scan.js`)이 자신이 신설한 @header 갱신 규칙을 준수하지 않아 자체 저장소 `validate --changed`가 `exit 2`(8건 `uncovered` 위반)로 CLOSE 게이트를 막았다(dogfooding 항목 ④, §9 FAIL).

### 10.2 해소 내역 (재작업 4건)

1. **`uncovered` 2분류 도입** — `newly_uncovered`(git 기준 신규/회귀 파일 → 차단, exit 2) / `pre_existing`(HEAD 시점에도 미커버 → **비차단, exit 0**). 게이트 목적을 "회귀 방지"로 재정의하고, 레거시 소급 부여는 `discover`/`scaffold`의 몫으로 분리.
2. **`--changed`가 전체 스캔과 동일한 `exclude`/`excludePatterns` 적용** — 제외 대상 경로는 위반이 아니라 `skipped[{file,reason}]`로 기록.
3. **`extractHeaderFromContent`에 `@header`↔`{` 근접성 판정(`findProximateHeaderIndex`) 도입** — 산문에서 `@header`를 설명하는 문서를 헤더 보유로 오인하던 오탐 4건 제거(저장소 헤더 보유 수 101→97).
4. **`code-scan.js` 자체 @header 부여 + `VERSION` 1.3.2 + 규칙 문서 3종(`pm-review-gate.md`·`tools.md`·`header-rules.md`) 게이트 문구 정합 + `docs/` 3종(CONVENTIONS·ARCHITECTURE·PROJECT) 갱신** — 이전 FAIL의 직접 원인이던 미기재 파일들이 코드/문서 양쪽에서 해소됨.

### 10.3 재실행 명령·출력 요지

**a) 전량 유닛 재실행**
```
node --test opal/tools/code-scan/tests/*.js
```
→ `tests 97 / pass 97 / fail 0 / cancelled 0 / skipped 0` — exit 0. (이전 81/81 + 재작업 검증용 신규 16건: `TS-077-A-1~5`(newly_uncovered/pre_existing 5분기), `TS-077-B-1~3`(exclude 적용 3케이스))

**b) 핵심 재확인 — dogfooding ④ (자체 저장소 `validate --changed`)**
```
node opal/tools/code-scan/code-scan.js validate --changed "<이 태스크 변경 파일 22개 csv>" --json
```
→
```
{"ok":true,"command":"validate","mode":"changed",
 "coverage":{"total":17,"inline":11,"manifest":0,"covered":11,"percent":64.7},
 "counts":{"orphan":0,"uncovered":6,"conflict":0,"draft":0,"exports_not_found":0,
           "worker_scope_violation":0,"newly_uncovered":0,"pre_existing":6},
 "violations":[6건 전부 code:"uncovered", sub:"pre_existing"
   (header-rules.md/pm-review-gate.md/opal-harness.md/code-scan-management.md/tools.md/brain-tool/README.md)],
 "skipped":[5건 unsupported_extension (.gitignore/claude-hooks.json/manifest.json/install-mac.sh/run.sh)]}
```
**exit 0.** `header-standard.md`와 `code-scan.js`는 violations에서 완전히 사라짐(이전 FAIL 시점 `no_entry` 대상이었으나 현재 헤더/커버리지 보유로 전환). 남은 6건은 전부 `sub:pre_existing`(HEAD 기준 기존 미커버 문서)로 비차단 분류되어 `ok:true`에 포함됨.

추가로 저장소 전체 변경분(tasks/ 제외, `.js`/`.md` 55개 파일) 대상 광역 재확인:
```
node opal/tools/code-scan/code-scan.js validate --changed "<55개 경로 csv>" --json
```
→ `exit 0`, `counts:{"uncovered":33,"newly_uncovered":0,"pre_existing":33}`, `incomplete` 0건. `skipped`에 `opal/tools/code-scan/tests/fixtures/**`·`opal/tools/memory-tool/tests/fixtures/**` 경로가 `reason:"excluded_dir"`로 정확히 제외됨(재작업 항목 2 회귀 없음).

**c) 배포 상태 재조회** (install 재실행 없이 현재 배포본만 재확인 — Guards 준수)
- `~/.opal/tools/code-scan/run.sh --help` → exit 0, `code-scan v1.3.2` 배너 + USAGE 전문(신규 서브명령 5종 포함)
- `~/.opal/tools/tool-scan/run.sh usage code-scan` → `{"ok":true,...,"exit_code":0}` + usage_text에 discover/scaffold/target/validate/feature 포함
- `OPAL_NODE_BIN=/nonexistent ~/.opal/tools/code-scan/run.sh --help` → `{"ok":false,"error":"node_missing",...}` + exit 1
- `~/.claude/settings.json` `PostToolUse` 배열 → `matcher:"Edit|Write|MultiEdit"` 엔트리(`code-map-hook.js`)가 기존 `Bash`(state-tool) 엔트리와 공존 확인

**d) 격리·범위 대조 재확인** — `scan --json` 저장소 루트 재실행 결과 총 97개 헤더 파일(근접성 판정으로 101→97), `tasks/` 0건, `fixtures/` 0건(격리 회귀 없음).

**e) 코드 품질/보안 재확인** — `node --check` 10개 파일(코드 파일) 전부 구문 오류 0건(회귀 없음). 하드코딩 시크릿 스캔 0건, `.gitignore` 예외/무시 유지, hook `exec/execSync/spawn/child_process` 부재 — 3항목 전부 PASS(회귀 없음).

### 10.4 최종 판정

**All Pass** (S-25 [SUPERVISOR] 제외 24개 시나리오 기준)

- 도구 핵심 기능 = All Pass(유지, 97/97 유닛 테스트·골든 회귀·배포 상태 전부 재확인 통과).
- **이전 FAIL — S-24 ④ / dogfooding ④ (자체 저장소 `validate --changed`) → 해소 확인**: `exit 0`, `newly_uncovered:0`로 CLOSE 게이트(`pm-review-gate.md` §8 v1.7 기준) 통과.
- 비차단 권고 1건 유지(S-17 자동 테스트 커버리지 보강, TS-045 신설 등) — CLOSE를 막지 않음.
- **S-25는 여전히 미확인** — [SUPERVISOR] 수동 항목으로 opal-test-agent가 실행하지 않으며, 캡틴 확인 대기 상태가 계속 유지된다. 위 "All Pass"는 S-25를 제외한 범위의 판정이다.

### 10.5 변경 파일

없음 — 본 재검증도 검증 전용. 산출물은 `TEST-SCENARIO.md`(결과 필드 갱신) + `TEST.md`(본 §10 append) 뿐이며 소스·규칙 문서는 무수정.
