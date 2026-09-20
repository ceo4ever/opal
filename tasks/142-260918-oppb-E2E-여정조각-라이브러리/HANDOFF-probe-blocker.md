# HANDOFF: oppb Environment Probe 구조적 차단 해소

> 작성: 2026-09-19 | 출처: 태스크 142 P2 9행 블로커 | 수신: 신규 태스크를 맡을 PM
> 이 문서는 **인계 브리핑**이다. 실행 계약(TASK.md)은 수신 PM이 채번 후 작성한다.

## 1. 한 문단 요약

`oppb`(opal-pilot-project-build) 파이프라인의 P2 Environment Probe가 이 저장소에서 구조적으로 통과할 수 없다. 원인은 태스크 142 고유의 문제가 아니라 `probe.py`의 설계 전제와 저장소의 `.gitattributes` `export-ignore` 정책이 충돌하는 것이며, **`export-ignore`를 쓰고 테스트가 저장소 자산을 읽는 모든 프로젝트에서 동일하게 재현된다.** OPAL 자신이 그런 저장소이므로 현재 oppb로 OPAL을 빌드하는 경로가 전부 닫혀 있다.

## 2. 근본 원인

`opal/tools/oppb-runtime-tool/probe.py:309 _make_snapshot()`이 명령마다 `git archive --format=tar HEAD`로 격리 스냅샷을 만들고, `_observe_command()`(`probe.py:406-420`)의 `finally: shutil.rmtree(...)`가 실행 직후 폐기한다.

격리 의도 자체는 정당하다 — worktree의 미추적·ignored 상태를 섞지 않고, 스냅샷을 `git init` → `add -A` → `commit`으로 독립 저장소화한 뒤(`probe.py:332-336`) `git status --porcelain --untracked-files=all --ignored=matching`으로 "이 명령이 무엇을 만들어내는가"를 git 판정으로 읽으려는 것이다.

문제는 **`git archive`가 `.gitattributes`의 `export-ignore`를 존중한다**는 점이다. 이 저장소는 `/tasks/`·`/docs/`·`/.opal/`·`/.gitignore`·`/.gitattributes`를 export-ignore 한다(install tarball 정제 목적, 2026-05-09 도입). 즉 probe가 관측하는 "프로젝트"는 이 저장소가 아니라 **배포본**이다.

## 3. 파생 증상 4건 (모두 같은 뿌리)

| # | 증상 | 근거 |
|---|------|------|
| S-1 | 동결 fixture를 읽는 테스트가 `FileNotFoundError` | `opal/tools/test-tool/tests/test_e2e_sut_http_surfaces.py:75`가 `_SOURCE_ROOT.glob("tasks/127-*")`로 `surfaces.json`·`test-scenario.json`을 읽는다. 스냅샷에 `tasks/`가 없어 `_TASK_DIRS`가 빈 리스트가 되고 분모와 assertion id 원천이 동시에 소멸한다. 이 스위트는 id를 리터럴로 적지 않고 동결 spec에서 읽도록 **의도 설계**돼 있어(파일 주석 §A.5) 폴백이 없다 |
| S-2 | bootstrap 산출물이 다음 명령에 전달되지 않음 | 스냅샷이 명령 1개당 1개이고 `finally`에서 즉시 삭제된다. `bootstrap`이 만든 venv·의존성·캐시가 `build`·`test` 스냅샷에 존재하지 않는다. 명령 간 격리가 설계 목적이므로 버그가 아니라 전제 충돌이다 |
| S-3 | 신규 자산의 lease 경로를 관측 불가 | 태스크 142가 만들 자산이 `docs/e2e/`·`.opal/e2e/`·`.e2e/`인데 앞의 둘이 export-ignore 대상이다. 정책(`shared_immutable`·`attempt_namespaced`·`exclusive`) 배정 대상 자체가 스냅샷에 없다 |
| S-4 | `.gitignore` 관련 완료조건 판정 불가 | `/.gitignore`가 export-ignore라 스냅샷에 없다. ignore 규칙이 없는 저장소에서 `--ignored=matching`을 돌리면 **모든 것이 미추적으로 보인다**. "`.e2e/`가 `.gitignore` 1줄로 전량 무시되는가"를 검증할 기반이 소멸한다 |
| S-5 | timeout 여유 없음 | `probe.py:64 COMMAND_TIMEOUT_SECONDS = 180`. 대상 스위트 실측 148~222s로 상한에 걸쳐 있어 통과해도 불안정하다 |

## 4. 우회가 막힌 이유

`opal/skills/op-oppb-project-slice/SKILL.md:195`:

> `mini_tasks[].verify_command`와 `mini_tasks[].run_command`에 쓴 argv는 여기에도 같은 내용으로 등재한다. 등재되지 않은 명령의 미추적 출력은 봉인되지 않아 late discovery 또는 `scope_violation` 경로로 들어간다.

probe에서 verify 명령을 빼면 P3에서 그 명령의 출력이 미봉인 쓰기가 되어 `scope_violation`으로 승격되고 attempt·rework 예산을 차감한다. **넣어도 막히고 빼도 막힌다.**

## 5. 권고 해결 방향

`_make_snapshot`을 `git archive` 스냅샷에서 **워크트리 직접 관측**으로 전환한다.

- 근거: probe의 목적은 "실행 환경에서 명령이 실제로 도는지" 관측인데, 실제 실행 환경은 배포 산출물이 아니라 워크트리다. `git archive` 스냅샷은 그 목적을 배반한다.
- `git status --ignored=matching`은 워크트리에서도 동일하게 동작하므로 기술적 장벽은 없다.
- 함께: `COMMAND_TIMEOUT_SECONDS` 상향(명령별 override 허용 검토).

### 검토했으나 권고하지 않는 안

| 안 | 배제 근거 |
|---|---|
| `.gitattributes`의 `export-ignore` 범위 축소 | 배포 경계를 흐린다. 이 축은 이미 사고 이력이 있다 — `.gitattributes` 주석이 기록한 2026-08-08 릴리스 tarball 파손(`dashboard/frontend/src/pages/tasks/TasksPage.tsx` 누락) |
| 슬라이스 스킬의 probe 필수 등재 완화 | 관측 없이 P3 무인 실행에 진입하게 되어 oppb의 안전장치를 무르게 한다 |

## 6. 미해결 설계 쟁점 (수신 PM이 확정할 것)

- **Q-1**: 워크트리 관측으로 바꿀 때 "명령 전후 비교"의 baseline을 무엇으로 잡는가. 현재는 스냅샷 `git init` 직후 commit이 baseline이다. 워크트리에는 이미 미추적 파일이 있을 수 있어 **명령 실행 전 status를 baseline으로 찍고 delta를 취하는** 방식이 필요해 보이나 미확정이다.
- **Q-2**: S-2(bootstrap 산출물 전달)를 워크트리 관측으로 바꾸면 자동 해소되는가, 아니면 명령 간 순차 의존을 별도로 선언해야 하는가.
- **Q-3**: timeout을 전역 상향할 것인가, `commands[].timeout_seconds` 필드를 신설할 것인가.

## 7. 제약 (OPAL PM 금지사항 — 위반 불가)

- `~/.opal/` 배포 파일 **직접 수정 금지**. 프로젝트 소스(`opal/tools/oppb-runtime-tool/`, `opal/skills/`)를 고치고 install로 재배포한다.
- 사용자 승인 없는 코드 수정 금지. 산출물 문서(.md) 작성·분석은 허용.
- 파이프라인 행 상태 변경은 `~/.opal/tools/state-tool/run.sh`로만. `state.json` 직접 편집 금지.
- 하드코딩된 플랫폼 분기 추가 금지. `probe.py`는 표준 라이브러리 + git CLI만 쓰며 플랫폼 분기를 두지 않는 것이 현재 계약이다(`README.md:5`).
- `oppb`의 exit 계약·`scope_violation` 승격 규칙을 이 태스크가 재정의하지 않는다.

## 8. 완료조건 초안 (수신 PM이 TASK.md로 확정)

- D-1 이 저장소에서 `oppb` P2 Environment Probe가 봉인까지 도달한다 — `.opal/oppb-environment.json`이 생성되고 `export-ignore` 대상 경로(`docs/`·`.opal/`·`tasks/`·`.gitignore`)의 변경이 관측 결과에 포함된다.
- D-2 S-1 재현 케이스가 통과한다 — `tasks/127-*` fixture를 읽는 테스트가 probe 실행 안에서 `FileNotFoundError` 없이 돈다.
- D-3 S-4가 해소된다 — `.gitignore` 규칙이 적용된 상태로 `--ignored=matching` 판정이 이루어진다.
- D-4 S-5가 해소된다 — 148~222s 실측 스위트가 timeout 없이 완주한다.
- D-5 회귀 0 — `opal/tools/oppb-runtime-tool/tests/` 전건 통과. 특히 `test_probe.py`(현재 8건).
- D-6 `_make_snapshot` 동작 변경에 대한 **신규 테스트가 추가된다**. 현재 `test_probe.py`에 스냅샷 생성 경로·export-ignore 상호작용을 직접 검증하는 케이스가 0건이다 — 이번 결함이 테스트로 잡히지 않은 이유다.
- D-7 install 배포 영향 확인 — `scripts/` install 경로로 `probe.py` 변경분이 `~/.opal/`에 반영된다.

## 9. 검증 명령

```bash
# 인터프리터 게이트가 있다 — 시스템 python3로 돌리면 conftest.py가 중단시킨다
~/.opal/.venv/bin/python -m pytest opal/tools/oppb-runtime-tool/tests/ -q
~/.opal/.venv/bin/python -m pytest opal/tools/test-tool/tests/ -q
bash scripts/tests/test_archive_contents.sh   # export-ignore 회귀 방지
```

## 10. 태스크 142와의 관계

- 태스크 142(`E2E 여정·조각 라이브러리 구축`, worktree `feat/OP-TASK-142`)는 P2 9행에서 이 블로커로 정지해 있다. P0·P1과 P2의 1~8행(PROJECT-DESIGN·workgraph/acceptance 기계검증·design-review pass)은 완료 상태다.
- 이 인계 태스크가 D-1을 달성하면 142는 9행 재실행으로 재개한다. **142의 산출물·INTENT는 건드리지 않는다.**
- 142의 INTENT 제외 범위가 프레임워크 개정을 배제하므로, 이 작업은 142 캡슐 안에서 수행하지 않는다(귀속 분리).

## 11. 참조

| 대상 | 경로 |
|---|---|
| probe 구현 | `opal/tools/oppb-runtime-tool/probe.py` (`_make_snapshot:309`, `_observe_command:406`, `COMMAND_TIMEOUT_SECONDS:64`) |
| probe 계약 | `opal/tools/oppb-runtime-tool/README.md` |
| 등재 강제 조항 | `opal/skills/op-oppb-project-slice/SKILL.md:195` |
| export-ignore 정책·사고 이력 | `.gitattributes` (파일 상단 주석) |
| S-1 재현 지점 | `opal/tools/test-tool/tests/test_e2e_sut_http_surfaces.py:75` |
| 인터프리터 게이트 | `conftest.py` (저장소 루트) |
| 142 블로커 원문 | `tasks/142-260918-oppb-E2E-여정조각-라이브러리/state.json` 9행 note |
