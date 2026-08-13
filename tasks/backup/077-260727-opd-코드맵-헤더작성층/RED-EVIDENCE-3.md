# RED-EVIDENCE-3 — 태스크 077 재작업 (결함 B, PM 실측 지시)

> 작성: opal-test-agent (mode: red) | 재작업 — F-6 AC 미충족 1건(`validate --changed`가 `exclude`/`excludePatterns` 미적용)에 대한 RED 테스트 보강.
> 작성자≠구현자 원칙(`~/.opal/references/harness/red-first.md` §2) 준수 — 본 파일 작성자는 GREEN(구현)을 수행하지 않는다.
> 기존 `RED-EVIDENCE.md`(Phase 1 최초 RED), `RED-EVIDENCE-2.md`(결함 A/B 재작업 1차 — 본 문서의 "결함 B"와 이름은 같지만 서로 다른 결함이다: RED-EVIDENCE-2의 결함 B는 `test-resolve-header.js` 관련이며 이미 GREEN 완료됨. 본 문서는 PM이 신규 실측한 별개 결함이다)는 수정하지 않았다. 본 파일은 이번 재작업 전용 증거다.
> Scope: `opal/tools/code-scan/tests/test-validate.js`만 수정(픽스처 디렉토리 신규 추가 없음 — 모두 `os.tmpdir()` 임시 git 트리로 자기완결 구성). `code-scan.js`·규칙 문서 무수정.

---

## 1. 결함 요약 (PM 실측)

`validate --changed <경로목록>`이 명시 경로를 판정할 때 `.opal/code-scan.json`의 `exclude`(디렉토리명 매칭)와 `excludePatterns`(와일드카드)를 전혀 적용하지 않는다.

- 근거 코드: `code-scan.js:1421-1438` (`cmdValidate`의 `--changed` 파싱 블록). `fs.existsSync(abs)` / `.isFile()` / `config.extensions.includes(...)` 3가지만 검사하고 `config.exclude`·`excludePatterns`는 전혀 조회하지 않는다.
- 대조: 전체 스캔(`scan`) 경로는 `walkDir`(`code-scan.js:251-270`, `config.exclude.includes(e.name)`로 각 디렉토리 세그먼트 필터)과 `isExcluded`(`code-scan.js:234-241`, `excludePatterns` 와일드카드 매칭)를 정상 적용한다. → **`--changed` 경로와 전체 스캔 경로의 판정 기준이 불일치**.
- 결과: 저장소 `.opal/code-scan.json`의 `exclude`에 `fixtures`가 있음에도, `--changed`에 `fixtures/` 하위 파일을 넘기면 `uncovered:newly_uncovered`로 오판정되어 exit 2로 차단된다.

## 2. 실행 명령

```bash
node --test opal/tools/code-scan/tests/test-validate.js
node --test "opal/tools/code-scan/tests/*.js"
```

- cwd: 저장소 루트(`/Volumes/Data/AIStudio/workspace/ai-framework`)
- Node 버전: v25.8.2
- 실행 방식: `node:test` + `node:assert/strict` + `spawnSync` CLI 블랙박스. 각 신규 테스트는 `os.tmpdir()` 하위 임시 디렉토리에 실 `git init` 트리를 구성한다(대역 객체·몽키패치 0건, `opal/core/PRINCIPLES.md` §4 "Don't fake it" 준수). 저장소(ai-framework) 자체의 git 상태는 건드리지 않았다(§5 확인).

## 3. 신규 테스트 3건 (TS-077-B-1~3)

| TC | 목적 | 기대 판정 |
|----|------|----------|
| TS-077-B-1 | `--changed`로 `exclude` 디렉토리명(`fixtures`) 하위 경로 전달 | `skipped[]`에 `{file, reason:'excluded_dir'}` 기록, `counts.uncovered`/`newly_uncovered` 무영향, exit 0 |
| TS-077-B-2 | `--changed`로 `excludePatterns`(`*.generated.java`) 매치 경로 전달 | `skipped[]`에 `{file, reason:'excluded_pattern'}` 기록, `counts.uncovered` 무영향, exit 0 |
| TS-077-B-3 (대조군) | `--changed`로 exclude에 걸리지 않는 헤더 없는 신규 파일 전달 | 기존 동작 불변 — `uncovered:newly_uncovered` + exit 2 (**PASS 기대**, 결함 A 계약 회귀 확인용) |

### 3.1 실행 결과 — `test-validate.js` 단독

```
# tests 90
# pass 88
# fail 2
```

exit code = **1**

**RED 확인 — TS-077-B-1 실패 (실제 assertion 출력)**:
```
✖ TS-077-B-1 (결함 B): exclude 디렉토리명(fixtures) 하위 --changed 파일 → skipped[excluded_dir] + counts 무영향 + exit 0
AssertionError [ERR_ASSERTION]: [RED expect] exclude 디렉토리(fixtures) 하위 경로는 판정에서 제외되어 exit 0이어야 함(현행은 uncovered로 오판정되어 exit 2), got 2
2 !== 0
  actual: 2
  expected: 0
  operator: 'strictEqual'
```

**RED 확인 — TS-077-B-2 실패 (실제 assertion 출력)**:
```
✖ TS-077-B-2 (결함 B): excludePatterns 매치 --changed 파일 → skipped[excluded_pattern] + counts 무영향 + exit 0
AssertionError [ERR_ASSERTION]: [RED expect] excludePatterns(*.generated.java) 매치 경로는 판정에서 제외되어 exit 0이어야 함(현행은 uncovered로 오판정되어 exit 2), got 2
2 !== 0
  actual: 2
  expected: 0
  operator: 'strictEqual'
```

두 케이스 모두 현행 구현이 exclude 필터를 적용하지 않아 `exit 2`를 반환함이 실측으로 확인되었다 — PM이 보고한 결함이 테스트 코드로 재현되었다(진성 RED).

**대조군 PASS 확인 — TS-077-B-3**:
```
ok - TS-077-B-3 (대조군 — 회귀 없음 확인, PASS 기대): exclude에 걸리지 않는 --changed 신규 헤더 없는 파일 → 기존대로 newly_uncovered + exit 2
```
exclude에 걸리지 않는 파일은 여전히 `newly_uncovered` + exit 2로 판정됨 — 결함 A(uncovered 2분류) 계약이 훼손되지 않았음을 확인.

## 4. 전체 스위트 결과 (glob, `opal/tools/code-scan/tests/*.js`)

```
ℹ tests 90
ℹ suites 0
ℹ pass 88
ℹ fail 2
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 2976.079375
```

**exit code = 1**

실패 2건은 정확히 §3의 TS-077-B-1, TS-077-B-2 (다른 파일에서의 실패 0건). 회귀 검증:

| 구분 | 건수 | 상태 |
|------|------|------|
| 재작업 이전 기존 테스트 87건(test-discover/test-feature/test-hook/test-regression/test-scaffold/test-target/test-resolve-header 전체 + test-validate.js의 기존 22건) | 87 | **전부 PASS 유지 — 회귀 0건** |
| 신규 TS-077-B-1 | 1 | FAIL (의도된 RED) |
| 신규 TS-077-B-2 | 1 | FAIL (의도된 RED) |
| 신규 TS-077-B-3(대조군) | 1 | PASS |
| **합계** | **90** | 87 + 3 = 90 (pass 88 = 87 + 1(B-3), fail 2 = B-1 + B-2) — 계산 일치 |

## 5. 격리 검증 (PM-6 / PRINCIPLES §4)

- 신규 테스트 3건은 각각 `fs.mkdtempSync(os.tmpdir())`로 독립 임시 디렉토리를 만들고 그 안에서 `git init -q` + local `user.email`/`user.name`/`commit.gpgsign=false`를 설정한다(전역 git 설정 무변경). `.opal/code-scan.json`도 임시 트리 내부에 직접 기록한다(저장소 실제 설정 무변경).
- 기존 helper(`initGitRepo`, `writeJavaFile`, `cleanupDirs`)를 재사용하고, exclude 조합 전용 helper `writeGitClassConfigWithExclude(dir, exclude, excludePatterns)` 1개만 신규 추가했다. 임시 디렉토리는 `process.on('exit')` 훅에서 정리된다.
- 저장소(ai-framework) git 상태 재확인:
  ```
  git status --porcelain -- opal/tools/code-scan/tests/
  ?? opal/tools/code-scan/tests/
  ```
  (이 디렉토리는 태스크 077 진행 중 아직 커밋되지 않은 신규 트리 전체이며, 본 작업으로 인한 별도 변경이 아니다 — `test-validate.js` 1개 파일만 수정했다.)
- `code-scan.js`, `.opal/code-scan.json`(저장소 루트본), 규칙 문서(`header-rules.md` 등)는 수정하지 않았다 — 스코프 제한 준수.

## 6. 다음 단계

GREEN(구현) 워커가 `code-scan.js`의 `cmdValidate` `--changed` 파싱 블록(`code-scan.js:1421-1438`)에 `config.exclude`(디렉토리 세그먼트 매칭) + `excludePatterns`(`isExcluded` 재사용) 필터를 추가하고, 제외된 경로를 `skipped[]`에 `{file, reason: 'excluded_dir'|'excluded_pattern'}` 형태로 기록하도록 구현해야 한다. 기존 `skipped` 항목(존재하지 않는 경로/미지원 확장자/스코프 밖)의 표기 방식도 함께 정비가 필요하면 이번 3건의 계약(§3 표)을 기준으로 확장한다.
