# RED-EVIDENCE-5 — 태스크 077 추가작업 (결함 D, PM 실측 진단: scaffold↔validate 필터 비대칭)

> 작성: opal-test-agent (mode: red) | 추가작업 — `validate` 구조 패스가 `scaffold` 열거 필터(`config.exclude`/`index.exclude`/`excludePatterns`)를 전혀 적용하지 않아, scaffold가 정당히 제외한 파일이 `worker_scope_violation/files_key_removed`로 오탐되는 결함(결함 D)에 대한 RED 테스트 신설.
> 작성자≠구현자 원칙(`~/.opal/references/harness/red-first.md` §2) 준수 — 본 파일 작성자는 GREEN(구현)을 수행하지 않는다.
> **명명 주의**: 이 저장소의 기존 `RED-EVIDENCE-4.md`가 이미 "결함 C"(`extractHeader` 근접 제약 결함, `TS-077-C-1~4`)를 선점했다. 본 결함은 그와 무관한 별개 결함이므로 ID 충돌을 피하기 위해 **"결함 D" / `TS-077-D-1~3`**으로 명명했다.
> 기존 `RED-EVIDENCE.md`/`RED-EVIDENCE-2.md`/`RED-EVIDENCE-3.md`/`RED-EVIDENCE-4.md`는 전혀 수정하지 않았다. 본 파일은 결함 D 전용 신규 증거다.
> **Scope**: `opal/tools/code-scan/tests/test-validate.js` 수정(신규 테스트 3건 추가) + `opal/tools/code-scan/tests/fixtures/violations/worker-scope-exclude-symmetry/` 신규 자기완결 픽스처 추가. **`code-scan.js`·규칙 문서는 전혀 수정하지 않았다** (구현은 op-dev-execute 담당).

---

## 1. 결함 요약 (PM 실측 진단)

`scaffold`의 디렉토리 열거 `collectDirsWithCodeFiles`(`code-scan.js:1223-1239`)와 `validate` 구조 패스의 디렉토리 열거 `listCodeFilesInDir`(`code-scan.js:1430-1438`) 사이에 **필터 비대칭**이 존재한다.

| 경로 | 필터 | 근거 |
|------|------|------|
| scaffold 열거 `collectDirsWithCodeFiles` | 디렉토리 `config.exclude` **+ `index.exclude`** 합집합 + 파일 `excludePatterns` **적용** | `code-scan.js:1223-1239` |
| validate 구조 패스 `listCodeFilesInDir` | **확장자만** 확인, 필터 0건 | `code-scan.js:1430-1438` |
| 검출기 | 디스크에 있고 매니페스트 키에 없으면 `worker_scope_violation/files_key_removed` | `code-scan.js:1580-1584` |

⇒ scaffold가 정당하게 제외한 파일(`excludePatterns` 매치 / `config.exclude` 디렉토리명 / `index.exclude` 디렉토리명)이 validate에서 "워커가 키를 삭제했다"로 오탐된다. `PLAN.md` §3.7.2(F-007 표, `files` 키 집합 행)는 애초에 "`m.dir` 디렉토리를 `config.extensions`·`config.exclude ∪ index.exclude`·`excludePatterns` 적용해 열거"하도록 계약되어 있었으나 실제 구현(`listCodeFilesInDir`)은 이 계약을 이행하지 않는다.

## 2. 실행 명령

```bash
node --test opal/tools/code-scan/tests/test-validate.js
node --test "opal/tools/code-scan/tests/*.js"
```

- cwd: 저장소 루트(`/Volumes/Data/AIStudio/workspace/ai-framework`)
- Node 버전: `process.execPath`(node) — 기존 스위트와 동일 환경
- 실행 방식: `node:test` + `node:assert/strict` + `spawnSync` CLI 블랙박스(신규 3건 전부) — 대역 객체·몽키패치 0건, 실 파일시스템 + 실 CLI만 사용(`opal/core/PRINCIPLES.md` §4 "Don't fake it" 준수).
- 신규 픽스처는 `opal/tools/code-scan/tests/fixtures/violations/worker-scope-exclude-symmetry/`에 자기완결 트리로 추가했다(자체 `.opal/code-scan.json` + `.opal/code-map/` 보유). Case B(대조군) 테스트만 `os.tmpdir()` 하위 임시 디렉토리에 픽스처를 복사한 뒤 파일 1개를 추가해 실행하며, `process.on('exit')`에서 자동 정리한다(기존 `cleanupDirs` 배열 재사용). 저장소 git 상태·기존 픽스처는 무변경.

## 3. 픽스처 설계 — `violations/worker-scope-exclude-symmetry/`

요구계약 1(`excludePatterns`)/2(`config.exclude` 디렉토리명)/3(`index.exclude` 디렉토리명)을 **서로 격리**해 각각 단독으로 검증하도록 설계했다(한 요인만 바뀌어도 실패 지점이 명확해지도록).

```
.opal/code-scan.json   : exclude=["node_modules",".git","thirdparty"], excludePatterns=["*.generated.java"]
.opal/code-map/index.json : exclude=["vendor"]  (config.exclude에는 "vendor"가 없음 — union 여부를 정확히 가른다)
.opal/code-map/svc/mod.json       : dir="svc/mod",       files={ "Normal.java": {...} }
.opal/code-map/svc/vendor.json    : dir="svc/vendor",    files={}   (index.exclude 전용 격리, req3)
.opal/code-map/svc/thirdparty.json: dir="svc/thirdparty",files={}   (config.exclude 전용 격리, req2)

svc/mod/Normal.java             — 매니페스트 키 존재(정상, 대조 대상)
svc/mod/Excluded.generated.java — excludePatterns 매치, 키 없음(req1 격리)
svc/vendor/Nested.java          — index.exclude 디렉토리("vendor") 하위, 키 없음(req3 격리). 무관한 uncovered
                                   잡음 배제를 위해 인라인 @header로 자기완결.
svc/thirdparty/Old.java         — config.exclude 디렉토리("thirdparty") 하위, 키 없음(req2 격리). 동일하게
                                   인라인 @header로 자기완결.
```

`Nested.java`/`Old.java`에 인라인 헤더를 부여한 이유: `walkDir`(전체 스캔 경로, `code-scan.js:258-277`)은 `config.exclude`만 조회하고 `index.exclude`는 조회하지 않는 별도의(범위 밖) 비대칭이 있어, 인라인 헤더 없이는 `uncovered:no_entry`가 부수적으로 발생해 본 결함(`files_key_removed`)과 무관한 잡음이 섞인다. 본 태스크의 **디스패치 스코프는 `files_key_removed` 비대칭(구조 패스)에 한정**되므로, `uncovered` 경로의 별도 비대칭은 손대지 않고 픽스처 설계로 격리했다(관측된 사실은 §5에 기록).

## 4. 신규 테스트 3건 (`TS-077-D-1~3`)

| TC | Case | 목적 | 기대 판정 | 결과 |
|----|------|------|----------|------|
| `TS-077-D-1` | Case A(대칭 불변식) | 픽스처 전체에서 구조 위반(`orphan`/`files_key_added`/`files_key_removed`) 0건 | 0건 | **FAIL (RED)** |
| `TS-077-D-2` | Case C(요구계약 3 전용) | `svc/vendor/Nested.java`(index.exclude 전용)는 `files_key_removed`로 오탐되지 않음 | 미검출 | **FAIL (RED)** |
| `TS-077-D-3` | Case B(대조군) | 제외 대상 아닌 신규 파일(`Rogue.java`)은 여전히 `files_key_removed`로 정상 검출(게이트 무력화 방지) | 검출됨 | **PASS** (기대대로) |

### 4.1 `TS-077-D-1` 실패 (실제 assertion 출력)

```
AssertionError [ERR_ASSERTION]: [RED expect] excludePatterns/config.exclude/index.exclude로 정당히 제외된
3개 파일 모두 files_key_removed 오탐 없이 통과해야 함(현행 listCodeFilesInDir는 필터 0건 적용이라 3건 전부 오탐),
got [
  {"code":"worker_scope_violation","sub":"files_key_removed","manifest":".opal/code-map/svc/mod.json","key":"Excluded.generated.java","detail":""},
  {"code":"worker_scope_violation","sub":"files_key_removed","manifest":".opal/code-map/svc/thirdparty.json","key":"Old.java","detail":""},
  {"code":"worker_scope_violation","sub":"files_key_removed","manifest":".opal/code-map/svc/vendor.json","key":"Nested.java","detail":""}
]
3 !== 0
```

→ req1(excludePatterns)·req2(config.exclude)·req3(index.exclude) 3종 전부가 **동시에** 오탐됨을 단일 실행으로 실측 확인.

### 4.2 `TS-077-D-2` 실패 (실제 assertion 출력, req3 전용 격리)

```
AssertionError [ERR_ASSERTION]: [RED expect] "vendor"는 index.exclude 전용(config.exclude에는 없음)이므로
scaffold ∪ 규약상 제외 대상 — files_key_removed가 발생하면 안 됨(현행은 index.exclude를 전혀 조회하지
않아 오탐), got {"code":"worker_scope_violation","sub":"files_key_removed","manifest":".opal/code-map/svc/vendor.json","key":"Nested.java","detail":""}
```

→ `config.exclude ∪ index.exclude` 합집합 중 **`index.exclude`만으로 제외되는 케이스**를 단독으로 재현해, 구현이 향후 `config.exclude`만 참조하고 `index.exclude`를 빠뜨리는 회귀를 잡을 수 있도록 격리했다.

### 4.3 `TS-077-D-3` 통과 (대조군, 게이트 무력화 방지 확인)

임시 디렉토리에 픽스처를 복사한 뒤 `svc/mod/Rogue.java`(어떤 exclude 규칙에도 매치되지 않는 순수 신규 파일)를 추가하고 실행한 결과, `files_key_removed`가 `Rogue.java`에 대해 정상 검출됨을 확인했다(직접 실행 증거는 §5). 이는 detector 자체가 무력화된 것이 아니라 **exclude 필터 미적용만이 문제**임을 증명하는 대조군이며, 향후 구현이 "모든 `files_key_removed`를 억제"하는 식의 과잉수정(게이트 무력화)을 하지 않았는지 검증하는 역할을 한다.

## 5. 직접 실행 증거 (구현 전 수동 재현 — 테스트 코드와 별개로 확인)

```bash
$ cd opal/tools/code-scan/tests/fixtures/violations/worker-scope-exclude-symmetry
$ node ../../../../code-scan.js validate --json
{"ok":false,"command":"validate","mode":"full","coverage":{"total":2,"inline":1,"manifest":1,"covered":2,"percent":100},
 "counts":{"orphan":0,"uncovered":0,"conflict":0,"draft":0,"exports_not_found":0,"worker_scope_violation":3,"newly_uncovered":0,"pre_existing":0},
 "violations":[
   {"code":"worker_scope_violation","sub":"files_key_removed","manifest":".opal/code-map/svc/mod.json","key":"Excluded.generated.java","detail":""},
   {"code":"worker_scope_violation","sub":"files_key_removed","manifest":".opal/code-map/svc/thirdparty.json","key":"Old.java","detail":""},
   {"code":"worker_scope_violation","sub":"files_key_removed","manifest":".opal/code-map/svc/vendor.json","key":"Nested.java","detail":""}
 ],"skipped":[]}
$ echo "EXIT: $?"
EXIT: 2
```

`counts.uncovered: 0`, `coverage.total: 2`(=`Normal.java`(manifest) + `Nested.java`(inline)) — `Old.java`(config.exclude, 전체 스캔 경로도 이미 정상 제외)와 `Excluded.generated.java`(excludePatterns, 전체 스캔 경로도 이미 정상 제외)는 `uncovered` 잡음 없이 완전히 배제됨을 확인. 오직 구조 패스(`files_key_removed`)만 3건 오탐. 픽스처 설계가 의도대로 결함을 격리했음을 실측으로 검증했다.

대조군(임시 복사본 + `Rogue.java` 추가) 실행:

```bash
$ node code-scan.js validate --json   # (tmp copy, svc/mod/Rogue.java 추가)
{"ok":false, ...,
 "counts":{"orphan":0,"uncovered":1,"conflict":0,"draft":0,"exports_not_found":0,"worker_scope_violation":4,"newly_uncovered":0,"pre_existing":0},
 "violations":[
   {"code":"uncovered","sub":"no_entry","file":"svc/mod/Rogue.java","detail":""},
   {"code":"worker_scope_violation","sub":"files_key_removed","manifest":".opal/code-map/svc/mod.json","key":"Excluded.generated.java","detail":""},
   {"code":"worker_scope_violation","sub":"files_key_removed","manifest":".opal/code-map/svc/mod.json","key":"Rogue.java","detail":""},
   {"code":"worker_scope_violation","sub":"files_key_removed","manifest":".opal/code-map/svc/thirdparty.json","key":"Old.java","detail":""},
   {"code":"worker_scope_violation","sub":"files_key_removed","manifest":".opal/code-map/svc/vendor.json","key":"Nested.java","detail":""}
 ],"skipped":[]}
EXIT: 2
```

`Rogue.java`가 `files_key_removed`로 정상 검출됨(대조군 성립).

## 6. 회귀 확인 — 기존 97건 전부 PASS

```bash
$ node --test opal/tools/code-scan/tests/*.js
ℹ tests 100
ℹ pass 98
ℹ fail 2
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
```

exit code = **1**

- 전체 100건 = 기존 97건 + 신규 3건(`TS-077-D-1~3`).
- 실패 2건은 **정확히** 신규 RED 케이스(`TS-077-D-1`, `TS-077-D-2`)이며, 기존 97건은 **전부 PASS**(회귀 0건). `TS-077-D-3`(대조군)도 기대대로 PASS.
- 실패 테스트 목록(`node --test` 출력 그대로):
  ```
  ✖ failing tests:
  test at opal/tools/code-scan/tests/test-validate.js:572:1
  ✖ TS-077-D-1 (결함 D 신규, Case A — 대칭 불변식): ...
  test at opal/tools/code-scan/tests/test-validate.js:589:1
  ✖ TS-077-D-2 (결함 D 신규, Case C — 요구계약 3 전용): ...
  ```

## 7. 변경 파일

- 수정: `opal/tools/code-scan/tests/test-validate.js` (changelog v1.2 라인 + `TS-077-D-1~3` 3건 추가, 기존 코드 무변경)
- 신규: `opal/tools/code-scan/tests/fixtures/violations/worker-scope-exclude-symmetry/`
  - `.opal/code-scan.json`
  - `.opal/code-map/index.json`
  - `.opal/code-map/svc/mod.json`, `.opal/code-map/svc/vendor.json`, `.opal/code-map/svc/thirdparty.json`
  - `svc/mod/Normal.java`, `svc/mod/Excluded.generated.java`, `svc/vendor/Nested.java`, `svc/thirdparty/Old.java`
- **`code-scan.js`·규칙 문서·기존 `RED-EVIDENCE*.md`는 전혀 수정하지 않았다.**

## 8. GREEN 진입 가이드 (구현자 참고용 — 본 파일 작성자가 구현하지 않음)

`listCodeFilesInDir(dirAbs, config)`가 `config.exclude ∪ index.exclude ∪ excludePatterns`를 알지 못하는 근본 원인은 함수 시그니처에 `index`가 전달되지 않고, `dirAbs`의 파일 열거 시 `isExcluded()`/`hasExcludedSegment()`(둘 다 기존 `code-scan.js`에 이미 존재하는 재사용 가능 헬퍼)를 호출하지 않기 때문이다. `PLAN.md` §3.7.2 표가 애초에 이 계약("`config.extensions`·`config.exclude ∪ index.exclude`·`excludePatterns` 적용해 열거")을 명시했으므로, GREEN 구현은 이 계약대로 `listCodeFilesInDir` 호출부(`cmdValidate` 내 구조 패스, `code-scan.js:1570` 부근)에 `index`를 전달하고 동일한 필터를 적용하면 된다. 이 파일은 그 판단을 확정하지 않는다 — 실제 결정은 op-dev-execute가 내린다.
