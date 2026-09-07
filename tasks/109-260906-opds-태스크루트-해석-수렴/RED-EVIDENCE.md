# RED-EVIDENCE.md — 태스크 109 Step 3

## §1 측정 좌표

- 측정 시각: 2026-09-07 15:44 KST (state-tool 측정까지 포함해 15:44~15:46 KST 구간)
- 브랜치: main (워크트리 `task_109`)
- 대상 커밋: `3fec20cf42be8a1f7b076e10cc78317f270ad591` (2026-09-06 23:25:08 +0900)
- 허브 경로: `/Volumes/Data/AIStudio/workspace/ai-framework`
- 워크트리 경로: `/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_109`
- 인터프리터: `~/.opal/.venv/bin/python` 3.14.3 (console BE / brain-tool), `python3` 3.14.3 (state-tool), `node` v25.8.2 (code-scan)

## §2 회귀 기준선 (PM 실측 인용 — 재도출 안 함)

| 스위트 | 허브 (청정) | 워크트리 (Step 착수 전) |
|---|---|---|
| state-tool | 1 failed / 396 passed / 6 skipped | 1 failed / 396 passed / 6 skipped |
| console BE | 9 failed / 348 passed / 1 skipped (수집 358) | 33 failed / 322 passed / 3 skipped (수집 358) |
| code-scan | 369 pass / 0 fail | 361 pass / 8 fail |
| brain-tool | 142 passed / 0 failed | 정상 실행됨 |

- 워크트리 code-scan 8건 = 전건 `.opal/` 부재 원인의 선재 실패(Step 1·2가 깬 것이 아님):
  - 직접 5건 — `test-regression.js` TS-044(S-14)×2 · 077 TS-052(S-19) · 077 TS-057 / `test-shard-policy.js` TS-154
  - 메타 3건 — `test-regression.js` TS-062(S-16) · `test-shard.js` S-19 · `test-shard-policy.js` TS-080 (「전량 GREEN」 파생)
- state-tool skip 6건 귀속: 3건은 `<자기 루트>/tasks/098-…` 조립(허브에서도 skip) → Step 7b에서 해소 / 3건은 `/Volumes/Data/AiStudio/workspace/opal/tasks/093-…`(표기가 다른 옛 저장소) 죽은 경로 → 범위 외.

## §3 신규 테스트 RED 증거

### (1) console BE — `test_paths.py` (Step 1 신설)

명령 (워크트리):
```
cd /Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_109
~/.opal/.venv/bin/python -m pytest dashboard/backend/tests/test_paths.py -q
```

원문 출력:
```
==================================== ERRORS ====================================
____________ ERROR collecting dashboard/backend/tests/test_paths.py ____________
ImportError while importing test module '/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_109/dashboard/backend/tests/test_paths.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/homebrew/Cellar/python@3.14/3.14.3_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
dashboard/backend/tests/test_paths.py:18: in <module>
    from dashboard.backend import paths
E   ImportError: cannot import name 'paths' from 'dashboard.backend' (/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_109/dashboard/backend/__init__.py)
=========================== short test summary info ============================
ERROR dashboard/backend/tests/test_paths.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.08s
```
- exit code: 2

**올바른 이유 판정: RED — 정상.** 기대한 `ImportError: cannot import name 'paths' from 'dashboard.backend'`가 그대로 재현됐다. `dashboard/backend/paths.py` 모듈 부재가 원인이며, 문법 오류·픽스처 오류가 아니다.

### (2) brain-tool — `hub_root` 동치 (Step 1) + TS-014 정합 (Step 1b)

명령 (워크트리):
```
cd /Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_109/opal/tools/brain-tool
~/.opal/.venv/bin/python -m pytest tests/ -q -rs
```

원문 출력 (요약 라인 포함 전체 재현):
```
________ TestHubRootGoldenCases.test_all_golden_cases_match (case='C-1') ________
...
E   AttributeError: module 'brain_tool' has no attribute 'hub_root'
tests/test_brain_tool.py:2515: AttributeError
(C-1~C-7 각각 동일 AttributeError 반복)

_ TestHubRootGoldenCases.test_identity_cases_are_byte_identical_to_input (case='C-3') _
...
E   AttributeError: module 'brain_tool' has no attribute 'hub_root'
tests/test_brain_tool.py:2528: AttributeError
(C-3, C-6, C-7 각각 동일 AttributeError 반복)

10 failed, 146 passed in 0.98s
```
- exit code: 1
- `-rs` 출력에 skip 항목 없음 (skip 0건 확인 — 위 요약 라인 `10 failed, 146 passed`에 skipped 표기 자체가 없음)

**올바른 이유 판정: RED — 정상, 기대치와 정확히 일치.** 10 failed / 146 passed / 0 skipped, 10건 전부 `AttributeError: module 'brain_tool' has no attribute 'hub_root'`. 문법 오류·import 경로 오류가 아니라 미구현 속성 부재가 원인.

### (3) code-scan — `test-hub-root.js` (Step 2 신설)

명령 (워크트리):
```
cd /Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_109/opal/tools/code-scan
node --test tests/test-hub-root.js
```

원문 출력:
```
✖ [T109/L1-F1] TS-011: hubRootFromPath가 골든 표 C-1~C-7 전건에서 §2.5(4) 기대값을 반환한다 (5.243583ms)
✖ [T109/L2-F2] TS-022: 워크트리 cwd에서 validate 실행 시 허브 .opal/code-scan.json을 발견해 header_source_unset이 나지 않는다 (78.71125ms)
✖ [T109/L2-F2b] TS-022 음성: 설정을 워크트리 쪽에만 두면(허브에는 없음) header_source_unset이 그대로 난다 (75.791584ms)
ℹ tests 3
ℹ suites 0
ℹ pass 0
ℹ fail 3
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 257.716042

✖ failing tests:

test at tests/test-hub-root.js:64:1
✖ [T109/L1-F1] TS-011: hubRootFromPath가 골든 표 C-1~C-7 전건에서 §2.5(4) 기대값을 반환한다 (5.243583ms)
  AssertionError [ERR_ASSERTION]: [RED expect] code-scan.js는 아직 hubRootFromPath를 export하지 않는다 — GREEN 구현 전 단계
  + actual - expected
  + 'undefined'
  - 'function'
  (tests/test-hub-root.js:67:10)

test at tests/test-hub-root.js:87:1
✖ [T109/L2-F2] TS-022: 워크트리 cwd에서 validate 실행 시 허브 .opal/code-scan.json을 발견해 header_source_unset이 나지 않는다 (78.71125ms)
  AssertionError [ERR_ASSERTION]: [RED expect] 현재는 findProjectRoot()가 워크트리 자신을 프로젝트 루트로 오인해 허브의 .opal/code-scan.json을 발견하지 못하고 header_source_unset이 난다. json={"ok":false,"error":"header_source_unset", ...}
  actual: 'header_source_unset', expected: 'header_source_unset' (operator: notStrictEqual — 즉 실제로 header_source_unset이 남을 확인하는 RED 단언)
  (tests/test-hub-root.js:109:10)

test at tests/test-hub-root.js:119:1
✖ [T109/L2-F2b] TS-022 음성: 설정을 워크트리 쪽에만 두면(허브에는 없음) header_source_unset이 그대로 난다 (75.791584ms)
  AssertionError [ERR_ASSERTION]: 허브 기준 해석이 맞다면 워크트리 쪽 설정은 무시되고 header_source_unset이 나야 한다. json=null stderr=
  + actual - expected
  + null
  - 'header_source_unset'
  (tests/test-hub-root.js:139:10)
```
- exit code: 1

**올바른 이유 판정: RED — 정상, 3건 전부 기대한 이유로 실패.**
- TS-011: `hubRootFromPath`가 미export (`actual 'undefined' expected 'function'`) — 기대 그대로.
- TS-022: `findProjectRoot()`가 워크트리 자신의 `.git`에서 멈추고 허브까지 올라가지 않아 `header_source_unset`이 여전히 남 — 기대 그대로.
- TS-022 음성: 설정을 워크트리 쪽에만 두면 현재 코드가 워크트리 자신의 설정을 찾아 `json=null`(성공)로 끝남 — 같은 세그먼트 무시 버그의 반대 방향, 기대 그대로.

## §4 이미 해소된 항목 — state-tool

명령 (워크트리):
```
cd /Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_109/opal/tools/state-tool
python3 -m pytest tests/ -q -rs
```

원문 출력 (요약):
```
SKIPPED [1] tests/test_state_tool.py:7358: 레거시 실 자산 없음(메인 저장소 경로): /Volumes/Data/AiStudio/workspace/opal/tasks/093-260815-opd-사용자확인행-자동승인-일원화
SKIPPED [1] tests/test_state_tool.py:7280: 레거시 실 자산 없음(메인 저장소 경로): /Volumes/Data/AiStudio/workspace/opal/tasks/093-260815-opd-사용자확인행-자동승인-일원화
SKIPPED [1] tests/test_state_tool.py:7470: 레거시 실 자산 없음: /Volumes/Data/AiStudio/workspace/opal/tasks/093-260815-opd-사용자확인행-자동승인-일원화
400 passed, 3 skipped, 98 subtests passed in 76.02s (0:01:16)
```
- exit code: 0

**판정: 기대치(400 passed / 0 failed / 3 skipped, 093- 레거시만)와 정확히 일치.** 기준선 1 failed / 6 skipped에서 이미 해소된 상태임을 실행으로 확인. 이 Step은 이 사실을 기록만 한다 (Step 7·7b가 해소한 것).

## §5 GREEN 진입 판정

**Yes.**

근거:
1. console BE `test_paths.py`, brain-tool `hub_root` 관련 10건, code-scan `test-hub-root.js` 3건 — 총 신규 RED 14건 전부 **올바른 이유**(미구현 대상의 부재)로 실패함을 실행 출력으로 확인했다. 문법 오류·픽스처 오류·환경 오류로 인한 오탐 RED는 없었다.
2. state-tool은 이미 400 passed / 0 failed / 3 skipped(범위 외 레거시만)로 해소되어 있어 이 Step의 회귀 부담이 없다.
3. code-scan 기존 회귀 8건(워크트리 선재 실패)은 이번 신규 RED 14건과 원인이 겹치지 않으며 GREEN 단계에서 함께 해소될 항목으로 별도 추적된다(§2 인용).
4. 이로써 Step 4(GREEN)는 위 14건을 구현 대상으로 명확히 특정해 진행할 수 있는 근거를 갖췄다.
