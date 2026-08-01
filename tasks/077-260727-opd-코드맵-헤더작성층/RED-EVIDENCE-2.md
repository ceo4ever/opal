# RED-EVIDENCE-2 — 태스크 077 재작업 (결함 A/B, 캡틴 승인 조치)

> 작성: opal-test-agent (mode: red) | 재작업 — Step 19 검증에서 발견된 결함 2건에 대한 테스트 보강
> 작성자≠구현자 원칙(`~/.opal/references/harness/red-first.md` §2) 준수 — 본 파일 작성자는 GREEN(구현)을 수행하지 않는다.
> 기존 `RED-EVIDENCE.md`(Phase 1 최초 RED)는 수정하지 않았다. 본 파일은 재작업 전용 증거다.
> Scope: `opal/tools/code-scan/tests/test-validate.js`, `opal/tools/code-scan/tests/test-resolve-header.js`만 수정. `code-scan.js`·규칙 문서·`run.sh`·hook은 무수정.

---

## 1. 실행 명령

```bash
# 개별 파일
node --test opal/tools/code-scan/tests/test-validate.js
node --test opal/tools/code-scan/tests/test-resolve-header.js

# glob 형태(완료 기준 명시 형식)
node --test opal/tools/code-scan/tests/*.js
```

- cwd: 저장소 루트(`/Volumes/Data/AIStudio/workspace/ai-framework`)
- Node 버전: v25.8.2
- 실행 방식: `node:test` + `node:assert/strict` + `spawnSync` CLI 블랙박스. 계약 A 테스트는 **실 임시 디렉토리에서 `git init`한 실 git 트리**를 구성해 검증한다(대역 객체·몽키패치 0건, PRINCIPLES §4 준수). 저장소(ai-framework) 자체의 git 상태는 건드리지 않았다(`git status`로 재확인 완료 — 아래 §5).

---

## 2. 전체 결과 요약

### 2.1 glob 전체 실행 (`node --test opal/tools/code-scan/tests/*.js`)

```
# tests 87
# pass 82
# fail 5
# skipped 0
```

**exit code = 1** (신규 계약 A 테스트 5건이 실패 — RED 확인)

### 2.2 파일별 집계

| 파일 | 총 | PASS | FAIL | exit code | 비고 |
|------|----|------|------|-----------|------|
| test-discover.js | 5 | 5 | 0 | 0 | 무수정 — 회귀 0 |
| test-feature.js | 5 | 5 | 0 | 0 | 무수정 — 회귀 0 |
| test-hook.js | 7 | 7 | 0 | 0 | 무수정 — 회귀 0 |
| test-regression.js | 18 | 18 | 0 | 0 | 무수정 — 회귀 0 |
| test-scaffold.js | 6 | 6 | 0 | 0 | 무수정 — 회귀 0 |
| test-target.js | 6 | 6 | 0 | 0 | 무수정 — 회귀 0 |
| **test-resolve-header.js** | 18 | 18 | 0 | 0 | **계약 B 강화**(TS-044 강화·TS-045 신설·TS-046 강화) — 전부 PASS (§3.2 참조) |
| **test-validate.js** | 22 | 17 | 5 | 1 | 기존 17건 계속 PASS(회귀 0) + **계약 A 신규 5건 전부 FAIL(RED)** |
| **합계** | **87** | **82** | **5** | **1(전체 스위트)** | |

기존 케이스 회귀 0건 확인: 재작업 이전 베이스라인(RED-EVIDENCE.md §2 기준, GREEN 완료 후 상태)의 81건(test-validate.js 17 + test-resolve-header.js 17 + 나머지 47)이 전부 그대로 PASS 유지되며, 여기에 test-validate.js 신규 5건(FAIL, 의도된 RED) + test-resolve-header.js 신규 1건(TS-045, PASS)이 순증했다: 81 + 5 + 1 = 87. 계산 일치.

---

## 3. 결함별 상세 증거

### 3.1 결함 A — `uncovered` 2분류 (newly_uncovered/pre_existing) — 진성 RED 확인

`test-validate.js`에 TS-077-A-1~5 5건을 신설했다. 각 테스트는 `os.tmpdir()` 하위 임시 디렉토리에 `git init`으로 격리된 실 git 트리를 구성하고(`fs.mkdtempSync` + `git init -q` + local `user.email`/`user.name`/`commit.gpgsign=false` 설정 — 전역 git 설정 무변경), 종료 시 `process.on('exit')` 훅에서 정리한다.

실행 결과(`node --test --test-reporter=tap opal/tools/code-scan/tests/test-validate.js`):

```
# tests 22
# pass 17
# fail 5
```

5건 전부 FAIL — 실제 assertion 출력:

1. **TS-077-A-1 (신규 untracked 헤더 없는 파일)**
   ```
   AssertionError: [RED expect] untracked 신규 헤더 없는 파일은 sub:'newly_uncovered'여야 함
   + actual:   'no_entry'
   - expected: 'newly_uncovered'
   ```
2. **TS-077-A-2 (HEAD엔 헤더 있었으나 현재 제거 — 회귀)**
   ```
   AssertionError: [RED expect] HEAD 대비 헤더 회귀는 sub:'newly_uncovered'여야 함
   got {"code":"uncovered","sub":"no_entry","file":"svc/mod/HadHeader.java","detail":""}
   ```
3. **TS-077-A-3 (HEAD에도 헤더 없던 기존 파일 → 비차단 exit 0 기대)**
   ```
   AssertionError: [RED expect] HEAD에도 헤더가 없던 기존 파일은 회귀가 아니므로 비차단 exit 0이어야 함
   (현행은 무조건 exit 2) — 2 !== 0
   ```
4. **TS-077-A-4 (혼재 — newly_uncovered 1건 + pre_existing 1건)**
   ```
   AssertionError: [RED expect] NewOne.java sub:'newly_uncovered'
   got {"code":"uncovered","sub":"no_entry","file":"svc/mod/NewOne.java","detail":""}
   ```
5. **TS-077-A-5 (비git 트리 → 전량 pre_existing + exit 0 + stderr 경고)**
   ```
   AssertionError: [RED expect] git 미사용 환경은 전량 pre_existing으로 비차단 exit 0이어야 함
   (현행은 무조건 exit 2) — 2 !== 0
   ```

**진단 근거**: 현행 `code-scan.js`의 `cmdValidate`(코드 라인 1361~1405 부근)는 git 상태를 전혀 조회하지 않고, `uncovered` 위반의 `sub`를 항상 `'no_entry'`(엔트리 자체 부재) 또는 `'incomplete'`(필수 필드 미충족)로만 부여하며, 위반이 하나라도 있으면 무조건 `exit 2`로 종료한다(`process.exit(ok ? 0 : 2)`, 라인 1512). `newly_uncovered`/`pre_existing` 분류, `counts.newly_uncovered`/`counts.pre_existing` 키, git 미사용 환경 stderr 경고 모두 미구현 상태 — 계약 A는 **진성 RED**다.

### 3.2 결함 B — `headerSource` 실검증 — 강화 완료, 실행 결과는 이미 GREEN(구현 기존 정상, 테스트 커버리지 공백만 해소)

`test-resolve-header.js`의 기존 TS-044(inline)·TS-046(bogus) 테스트는 실제로 `.opal/code-scan.json`에 `headerSource` 값을 기재하지 않고 auto 모드 결과만 확인하는 공허한 검증이었다(TEST-SCENARIO.md §S-17 상세에 이미 명시된 발견). 이를 제거하고, `codemap-repo` 픽스처를 `fs.mkdtempSync` 임시 복사본에 복제한 뒤 `.opal/code-scan.json`에 `headerSource` 값을 **실제로** 기재해 검증하도록 강화했다:

- **TS-044 (강화)**: `headerSource:"inline"` → 결과가 정확히 `AdminHome.tsx` 1건(실제 인라인 `@header` 보유 파일)만 반환되고, file/package/rule/domain tier로만 커버되는 5개 파일(`OrderService.java`/`ShipRepo.java`/`AdminGuard.tsx`/`OrderMisc.java`/`legacy_util.py`)이 결과에서 전부 제외됨을 검증.
- **TS-045 (신설)**: `headerSource:"manifest"` → `AdminHome.tsx`(인라인 보유)가 인라인을 무시하고 매니페스트 필드(`description`/`exports:["ManifestOnlyExport"]`)로 대체되며 `_source !== 'inline'`임을 검증. `OrderService.java`(file tier)는 manifest 모드에서도 정상 커버됨을 대조 확인.
- **TS-046 (강화)**: `headerSource:"bogus"` → `exitCode 0` + `stdout` JSON 파싱 성공(무오염) + `stderr`에 `"invalid headerSource"` + `"bogus"` 언급 경고 존재 + **auto 모드 결과와 stdout이 바이트 동일**(`.trim()` 비교)함을 검증.

실행 결과(`node --test --test-reporter=tap opal/tools/code-scan/tests/test-resolve-header.js`):

```
# tests 18
# pass 18
# fail 0
```

**정직한 보고**: 위 3건(TS-044/045/046)은 실행 시 **모두 PASS**했다 — RED가 아니다. 사전에 각 픽스처 복사본으로 `node code-scan.js scan --json`을 직접 실행해 수동 검증한 결과(§4), `headerSource: inline/manifest/bogus` 3값 모두 계약대로 정확히 동작함을 확인했다 — 즉 **`headerSource` 스위치 기능 구현 자체는 이미 정확하다**. 결함 B는 "기능 결함"이 아니라 "테스트 커버리지 공백"이었다는 TEST-SCENARIO.md §S-17의 기존 판정과 정확히 일치한다. 작업 지시(§완료 기준)의 "계약 B 강화 케이스가 실패해야 한다"는 일반 진술과 실제 실행 결과가 다르다는 점을 숨기지 않고 명시한다 — PRINCIPLES §4 "Don't fake it"에 따라 실행 증거를 인위적으로 실패시키지 않았다. 대신 강화된 3건은 회귀 방지용 GREEN 테스트로 그대로 남기며(실 config 오버레이로 실제 분기 동작을 검증하므로 이전의 공허한 버전보다 계약 준수를 훨씬 엄격히 강제한다), 향후 `headerSource` 구현이 퇴행하면 즉시 잡아낸다.

---

## 4. 결함 B 사전 수동 재현 (테스트 작성 전 확인용, 참고 자료)

테스트 작성 전 실제 동작을 먼저 수동으로 확인했다(임시 복사본 `mktemp -d` 사용, 검증 후 삭제):

```
$ headerSource="inline" → scan --json 결과 키: ["web/admin/pages/AdminHome.tsx"] (1건)
$ headerSource="manifest" → 키 9건, AdminHome.tsx.description="매니페스트 전용 설명 — 인라인이 존재하므로 병합되면 안 됨 (S-6 혼재 검증)", exports=["ManifestOnlyExport"], _source="file"
$ headerSource="bogus" → stderr: 'Warning: invalid headerSource "bogus", falling back to "auto"' / stdout 키 9건(auto와 동일)
```

이 수동 재현 결과를 그대로 자동 테스트 assertion으로 옮겼다(§3.2).

---

## 5. 저장소 git 상태 무변경 확인

```bash
$ git status --porcelain | grep -v '^?? tasks/077' | grep -v 'tests/test-validate.js\|tests/test-resolve-header.js\|RED-EVIDENCE-2.md'
```
→ (출력 없음, 본 태스크가 의도한 파일 외 변경 없음 확인)

임시 git 트리는 전부 `os.tmpdir()` 하위(`opal-t077-gituncov-*`)에서 생성·정리되며, 저장소(ai-framework) 자체에 대해 `git add`/`commit`/`checkout`을 실행하지 않았다.

---

## 6. 변경 파일

- `opal/tools/code-scan/tests/test-validate.js` — TS-077-A-1~5 신설(계약 A, RED 확인)
- `opal/tools/code-scan/tests/test-resolve-header.js` — TS-044 강화·TS-045 신설·TS-046 강화(계약 B, 실행 결과 GREEN)

구현 파일(`code-scan.js`)·규칙 문서·`run.sh`·hook은 일체 수정하지 않았다.
