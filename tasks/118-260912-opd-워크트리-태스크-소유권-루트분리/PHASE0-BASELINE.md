# PHASE0-BASELINE — W-1 Console BE 축 실측 완결

> 담당: opal-be-agent (W-1, 실행 그룹 P1) · 완료 기준: AC-1, AC-2, C-3 · 시나리오: S-1, S-2
> 이 문서는 다섯 root 소비자 중 **Console BE 축만 새로 실측**한다. state-tool·code-scan·event-loader·brain-tool의 착지값은 `ANALYSIS.md` Q1 행에서 인용하고 재실행하지 않는다(원 지시 준수).

## 0. fixture 구성 (S-1, S-2 공통)

C-3(disposable fixture) + H-5(운영 설정 무변경) 제약 아래 아래 3단 구성으로 shadow cone을 만들었다.

```bash
HUB=/Volumes/Data/AIStudio/workspace/ai-framework
FIXTURE_PARENT=/Volumes/Data/AIStudio/workspace/op118-phase0-fixture   # 이 태스크 전용, 측정 후 전량 삭제
SRC=$FIXTURE_PARENT/_src/hub-clone                                     # disposable local clone (git clone --local)
SHADOW=$FIXTURE_PARENT/shadow-cone                                     # 실측 대상 shadow cone worktree

git clone --local "$HUB" "$SRC"
cd "$SRC" && git worktree add "$SHADOW" -b task118-phase0-shadow3
cd "$SHADOW"
git sparse-checkout init --cone
git sparse-checkout set cursor-rules dashboard docs opal scripts skills tasks .opal
```

- `repos`(운영 `.opal/worktree.json`의 6개: cursor-rules·dashboard·docs·opal·scripts·skills)에 `tasks`·`.opal`을 추가한 cone — PLAN W-1·TASK Proposed outcome 원문과 일치.
- 운영 `.opal/worktree.json`·`console.config.json`·`dashboard/backend/config.py`는 이 과정에서 **한 번도 쓰기 대상이 아니었다**(전부 읽기 전용 소비, 아래 §4 실증).

### H-5 배치 위치에 대한 이탈과 근거 (반드시 기록)

PLAN 원문은 "`$HOME/workspace/` 하위"를 지시하지만, 이 머신의 운영 `~/.opal/console.config.json`을 **읽기만** 해서 실측한 결과 실제 `scan_roots`는 아래와 같이 `$HOME/workspace`를 포함하지 않는다(파일 미변경, 조회만):

```bash
$ cat ~/.opal/console.config.json
{
  "scan_roots": [
    "/Volumes/Data/AIStudio/workspace",
    "/Volumes/Data/ProjectStudio/workspace",
    "/Volumes/Data/StoreLinkStudio"
  ],
  "scan_depth": 2, ...
}
```

`dashboard/backend/config.py:24`의 `DEFAULT_SCAN_ROOTS = [str(Path.home()/"workspace")]`는 `~/.opal/console.config.json`이 **존재하지 않을 때만** 적용되는 폴백이며(`config.py:77-79` `load_config()`), 이 머신은 이미 운영 파일이 있어 폴백이 발동하지 않는다. `$HOME/workspace`에 fixture를 두면(최초 시도, 아래 §5 이탈 기록 참조) 운영 `scan_roots` 화이트리스트 밖이라 `_find_project_path`(`dashboard/backend/routers/tasks.py:86-96`, `scan_projects(cfg.scan_roots, ...)` 결과와 경로 일치 여부만 확인)가 즉시 거부해 애초에 재현이 안 된다.

C-3의 "명시적 shadow cone"과 H-5의 "실측 가능해야 한다"는 요건을 함께 만족하려면 fixture는 **실제 활성 `scan_roots`의 하나**(`/Volumes/Data/AIStudio/workspace`, 즉 허브의 부모 디렉터리) 밑에 있어야 한다 — 이는 H-5가 우려한 "실제 프로젝트가 사는 곳"과 정확히 일치하는 지점이며, PLAN이 이미 예견한 위험이다. 완화책: ① 태스크 전용 고유 이름(`op118-phase0-fixture`) ② disposable clone 본체(`_src/hub-clone`)는 `scan_depth=2`를 넘는 깊이(`_src` 아래)에 둬 스캐너가 절대 도달하지 않게 함(§4 `scan_projects` 결과로 실증) ③ 측정 직후 전량 삭제(§4).

**dot-prefix 미적용 사유**: `dashboard/backend/scanner.py:216-218` `_walk_dir`는 `entry.name.startswith(".") and entry.name != ".opal"`인 하위 디렉터리는 재귀 진입 자체를 건너뛴다. 최상위를 `.`으로 시작하는 이름으로 두면 `scan_projects`가 `shadow-cone`까지 내려가지 못해 S-2 재현이 원천 불가능해진다. 그래서 이 축만 비-hidden 이름을 쓰고, 대신 위 3중 완화책으로 대체했다.

## (a) 5개 마커 실체화 여부

```bash
$ cd $SHADOW && for p in .git .opal/AGENT.md .opal/MEMORY.json .opal/brain tasks; do
    [ -e "$p" ] && echo "EXISTS: $p" || echo "MISSING: $p"
  done
EXISTS: .git
EXISTS: .opal/AGENT.md
EXISTS: .opal/MEMORY.json
EXISTS: .opal/brain
EXISTS: tasks
```

5개 전부 실체화됨 — AC-1 전반부 충족.

## (b) 다섯 root 소비자 착지 경로

| 소비자 | 착지 경로 (이 fixture) | 출처 |
|---|---|---|
| code-scan `findProjectRoot()` | 워크트리 자신(cone 1차 패스로 이미 자기완결) | **인용** — ANALYSIS.md Q1 code-scan 행, `code-scan.js:338-346`(hubRootFromPath)/`:348-386`(findProjectRoot) |
| event-loader `_hub_root()`/`_roots()` | 무조건 허브로 수렴(세그먼트 우선 분기 — cone 확장으로 개선 안 됨) | **인용** — ANALYSIS.md Q1 event-loader 행, `event_loader.py:84-98`/`:107-119` |
| brain-tool `hub_root()`/`_hub_cwd()` | event-loader와 동형, 무조건 허브 수렴 | **인용** — ANALYSIS.md Q1 brain-tool 행, `brain_tool.py:232-250`/`:253-255` |
| state-tool `find_project_root()` | 워크트리 자신의 `.opal/MEMORY.json` 사본(핵심 위험 — Phase 0/1 분리 근거) | **인용** — ANALYSIS.md Q1 state-tool 행, `state_tool.py:704-711` |
| **Console `paths.hub_root()`** | **워크트리 자신**(무조건 수렴 로직이나, 경로에 `.opal-worktrees` 리터럴 세그먼트가 없어 항등 반환) | **신규 실측(본 문서)** — 아래 실행 로그 |

```bash
$ cd $SHADOW && python3 -c "
from dashboard.backend.paths import hub_root
print(hub_root('$SHADOW'))"
/Volumes/Data/AIStudio/workspace/op118-phase0-fixture/shadow-cone
```

`paths.py:18-29`는 `code-scan.js:338-346`의 `hubRootFromPath`와 동형(순수 문자열 함수, `.opal-worktrees` 리터럴 세그먼트 존재 여부만 검사)이므로 code-scan과 동일한 결론이 재확인된다 — 다만 이 값은 **Console 프로덕션 경로에서 호출자가 0건**(ANALYSIS Q1 Console 행, `doctor.py:85-90` 미호출 주석)이라 착지값 자체는 AC-2 결론에 영향을 주지 않는다. AC-2의 실제 원인은 아래 (c)다.

## (c) Console BE 스위트 pass/fail/skip — 새 기준선

### 실행 명령과 스코프

```bash
$ cd $SHADOW && python3 -m pytest dashboard/backend/tests/ -q
383 passed, 1 warning in 18.54s
```

스코프: `dashboard/backend/tests/` 전체(9개 파일: test_adapters, test_brain, test_brain_spike, test_cache, test_config, test_deploy_smoke, test_doctor_adapter, test_main, test_parsers, test_paths, test_routers, test_scanner, test_stats). cwd = shadow cone worktree 루트(`$SHADOW`).

### 대조군(허브 cwd, 동일 커밋)

```bash
$ cd /Volumes/Data/AIStudio/workspace/ai-framework && python3 -m pytest dashboard/backend/tests/ -q
383 passed, 1 warning in 16.43s
```

**shadow cone과 허브가 바이트 수준까지 동일한 383 passed / 0 failed / 0 skipped** — 잔여 실패 0건.

### 기준선 대비 상대 증분 (절대 수치 직접 비교 금지 원칙 준수)

| 시점 | 실패 건수 | 근거 |
|---|---|---|
| 태스크 107 최종 회귀 (허브 cwd 실행, 워크트리 cone 미확장) | Console BE 33건 | `.opal/brain/pages/concept/worktree-tasks-fixture-structural-limit.md:26` "console BE(저장소 루트 실행) 33건" |
| 이번 태스크 ANALYSIS 세션 (scan_roots 미충족 fixture) | Console BE 36건 | ANALYSIS.md Q1 AC-2 재기준선 행 |
| **본 W-1 (scan_roots 충족 shadow cone)** | **0건** | 위 실행 로그 |

두 선행 기준선(33건, 36건) 대비 **실패 0건으로 전량 회복** — 상대 증분은 "개선"으로 판정.

### 단일 테스트 격리 재현 — 원인이 cone·hub-root가 아님을 입증

잔여 실패가 없으므로(c)의 "잔여 실패가 있으면" 조건은 해당 없음. 대신 원인 격리를 **재현 가능한 최소 사례**로 고정해 근거를 남긴다 — `scan_roots` 멤버십 여부만 바꾸고 cone·hub-root 로직은 전혀 건드리지 않은 채 pass/fail이 뒤집히는 것을 실측했다.

```bash
# ① scan_roots 밖 shadow cone(최초 시도, $HOME/workspace 하위 — 운영 scan_roots 미포함) → 실패
$ cd $HOME/workspace/.op118-phase0-fixture/shadow-cone && \
  python3 -m pytest dashboard/backend/tests/test_routers.py::test_t103_ts043_archive_column_existing_behavior_unchanged -q
FAILED ... KeyError: '089-260811-opi-opal'   # by_id[_T103_TASK_089] 조회 실패 — project가 scan_projects 결과에 없음

# ② scan_roots 안 shadow cone(본 fixture, /Volumes/Data/AIStudio/workspace 하위) → 통과
$ cd $SHADOW && \
  python3 -m pytest dashboard/backend/tests/test_routers.py::test_t103_ts043_archive_column_existing_behavior_unchanged -q
1 passed
```

두 실행은 cone 구성(`repos+tasks+.opal`)·hub-root 로직·코드 버전이 완전히 동일하고 **fixture 배치 위치(=scan_roots 멤버십)만** 다르다. `_T103_ROOT = hub_root(str(Path(__file__).resolve().parents[3]))`(`test_routers.py:1014`)가 두 경우 모두 fixture 자신의 경로로 항등 해석되지만(§b, `.opal-worktrees` 리터럴 세그먼트 부재), `_find_project_path`(`routers/tasks.py:86-96`)가 `scan_projects(cfg.scan_roots, ...)` 결과와 경로 일치를 요구하므로 ①에서만 프로젝트를 찾지 못해 실패한다. 즉 **원인은 cone·hub-root가 아니라 `dashboard/backend/config.py:24`의 `DEFAULT_SCAN_ROOTS` 폴백이 이 머신의 운영 `console.config.json`에 가려 적용되지 않는다는 사실과, 그 운영 `scan_roots`에 fixture가 있었는지 여부**임이 실행 증거로 확인됐다.

## 측정 종료 후 정리 (H-5 완료 조건)

```bash
$ cd $SRC && git worktree remove --force "$SHADOW"
$ rm -rf /Volumes/Data/AIStudio/workspace/op118-phase0-fixture
$ ls /Volumes/Data/AIStudio/workspace | grep -i op118
NO_RESIDUE_FOUND
$ cd /Volumes/Data/AIStudio/workspace/ai-framework && git worktree list
/Volumes/Data/AIStudio/workspace/ai-framework                           5227f65 [main]
/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_115  0806bd0 [feat/OP-TASK-115]
/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_116  8824419 [feat/OP-TASK-116]
/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_118  e8b6c4f [feat/OP-TASK-118]
$ git diff --stat -- dashboard/backend/config.py .opal/worktree.json
(출력 없음 — 무변경)
```

`$HOME/workspace` 하위에 만들었던 최초 시도분(§0 이탈 기록의 대조군 ①)도 측정 직후 삭제했고, 재확인 결과 `$HOME/workspace` 디렉터리 자체가 생성 전 상태(부재)로 복귀했다.

**중간 사고 기록(투명성)**: 최초 `git worktree add` 실행 시 disposable clone 경로로 `cd` 하는 명령이 (별도 파일시스템 간 하드링크 실패로 clone이 만들어지지 않은 상태에서) 조용히 실패하며 cwd가 허브 루트에 남았고, 그 결과 `git worktree add`가 **허브 자신**에 브랜치 `task118-phase0-shadow2`와 linked worktree를 일시 생성했다. 파일 내용 변경은 없었으나(추가된 것은 `.git` 메타데이터의 브랜치 참조와 worktree 등록뿐), 즉시 `git worktree remove --force` + `git branch -D`로 원복했고 위 최종 `git worktree list`가 이를 실증한다. 이후 clone을 스크래치패드 우회 없이 허브와 같은 볼륨(`/Volumes/Data`) 안, scan_depth 밖 위치(`_src/hub-clone`)에 두어 재발을 막았다.

## 요약 판정

- AC-1(materialization + 착지 경로): 실체화 5/5 확인(신규 실측) + 착지 경로 5/5 기록(Console만 신규 실측, 나머지 4개는 ANALYSIS.md Q1 인용).
- AC-2(재기준선): state-tool 축은 ANALYSIS가 이미 닫음(인용, 420 passed/3 skipped). Console BE 축은 본 문서가 닫음 — **383 passed, 0 failed, 0 skipped**(107 기준 33건 실패·ANALYSIS 세션 36건 실패 대비 전량 회복), 원인 격리 근거 포함.
- C-3: 운영 `console.config.json`·`dashboard/backend/config.py`·`.opal/worktree.json` 무변경(diff 0) + disposable fixture 전량 삭제 확인.
