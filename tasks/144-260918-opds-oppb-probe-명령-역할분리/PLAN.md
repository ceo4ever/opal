---
template: sdlc-v2
---
# PLAN: OPPB probe 명령의 관측·판정 역할 분리

> 입력: [TASK.md](TASK.md) — ANALYSIS 없음(opds Short). 코드 근거는 이 PLAN이 직접 인용한다.

## Approach

probe 계약을 **등재 기준 2조건**으로 다시 쓴다. 코드는 건드리지 않고(C-1), 스킬 문서와 그 상위 SSOT인 제안서의 문장만 실제 소비 방식에 맞춘다.

- 기준 R1(역할): 명령의 exit code가 **수용 판정에 쓰이지 않는** 관측 전용 명령만 등재한다. `mini_tasks[].verify_command`와 전체 스위트 실행은 등재하지 않는다.
- 기준 R2(스냅샷 자족성): `git archive --format=tar HEAD` 산출물만으로 exit 0이고 180초 안에 끝나는 명령만 등재한다. 근거는 `opal/tools/oppb-runtime-tool/probe.py:309 _make_snapshot`(추적 tree만 복사 — `.gitattributes` export-ignore 경로 제외), `probe.py:405 _observe_command`(명령마다 새 스냅샷 + `finally: shutil.rmtree` → bootstrap 산출물 비전달), `probe.py:64 COMMAND_TIMEOUT_SECONDS = 180`.

등재에서 빠진 명령의 미추적 쓰기·실행 자원은 **새 필드 없이** 기존 축으로 선언한다 — 사전 선언은 `mini_tasks[].lease.ephemeral_writes`·`lease.runtime_resources`, 사전에 알 수 없는 잔여는 설계된 late discovery 경로(`probe observe-write`, `probe.py:1084~1140`)가 revision당 1 batch로 회수한다.

`code-scan search probe` 결과 `probe.py`의 @header도 "bootstrap·build·test·검증 명령을 하나씩 단독 실행"으로 제안서 문장을 그대로 복창하고 있고, `code-scan depends opal/tools/oppb-runtime-tool/probe.py`는 depends on·depended by 모두 비어 있다 — 계약이 코드 의존이 아니라 **문서 문장으로만** 전파되므로, 문서를 고치면 전파가 끝난다(코드 @header는 C-1로 손대지 않는다).

범위는 문서 2개(스킬 1 + 제안서 2문장), 배포 1회, 태스크 142 probe 명령 파일 1개, 회귀 2건이다. `opal/tools/oppb-runtime-tool/` 코드·`.gitattributes`·142의 `.oppb-workgraph-spec.json`·슬라이스 형태는 건드리지 않는다.

RED-first는 적용하지 않는다. 변경분이 전부 산문 계약이고 새로 만드는 실행 코드가 없어 실패하는 테스트를 먼저 세울 대상이 없다. 대신 AC-5·AC-6·AC-8은 실행 관측으로 닫는다(관측 항목은 각 Work item의 구체적 변경과 `Release and recovery`에 적는다).

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| D-1. `kind` 어휘를 `bootstrap`·`build` 2종으로 닫는다 | `.oppb-probe-commands.json`의 `kind`는 `bootstrap`(의존성·환경 준비) 또는 `build`(그 외 관측 전용) 둘 중 하나다. `test`·`verify` 계열은 등재 자체를 하지 않으므로 어휘에 없다 | 코드가 실제로 구분하는 값은 `bootstrap` 하나다 — `probe.py:497 classify_path`가 `kind == "bootstrap"`일 때만 `shared_immutable`+`dependency-environment`를 배정하고, `probe.py:560 compute_input_hash`가 bootstrap 부분집합만 따로 hash한다. `probe.py:629 _validate_commands`는 `kind`를 검증하지 않고 기본값 `"build"`를 채우므로 `bootstrap` 외 값은 전부 동치다. 새 `kind` 값 신설은 코드가 소비하지 않는 빈 추상이다([MUST] `~/.opal/PRINCIPLES.md` §2: "Solve only the current requirement. No speculative abstraction or unrequested flexibility.") |
| D-2. 등재 기준을 R1(판정 아님)·R2(스냅샷 자족·180초 내) 2조건 동시 충족으로 규정한다 | 두 조건을 모두 만족할 때만 등재한다. 도구 이름(pytest·unittest·node)이 아니라 **그 명령의 exit code가 수용 판정에 쓰이는지**가 R1의 기준이다. dry-run·validate처럼 판정에 쓰이지 않는 실행은 도구와 무관하게 `build`로 등재한다 | R1은 판정 주체 분리(C-4), R2는 `probe.py:309`·`:405`·`:64`가 이미 강제하는 물리 조건이다. 기준을 문서에 두면 등재 시점에 걸러지고, 어기면 `probe seal`이 `probe_command_failed`로 즉시 거부한다 — 프로세스가 아니라 도구가 집행한다([MUST] `~/.opal/PRINCIPLES.md` §Core Stance: "Enforce, don't just advise: if a rule must always hold, a tool gates it — not prose.") |
| D-3. 미등재 명령의 미추적 쓰기는 새 필드 없이 기존 lease 축으로 선언한다 | 사전에 아는 경로·자원은 `mini_tasks[].lease.ephemeral_writes`·`lease.runtime_resources`에 힌트로 적고, 나머지는 실행 중 late discovery가 회수한다. `.oppb-probe-commands.json`에 새 키를 만들지 않는다 | 새 lease 필드는 스키마 변경을 강제한다 — `opal/tools/oppb-runtime-tool/schema/oppb-state.schema.json` `$defs.lease`가 `additionalProperties: false`에 4축 required이고, `controller.py:370 LEASE_AXES`가 같은 4축이다(C-5 위반). `.oppb-probe-commands.json` 쪽 새 키는 `probe.py:626-648 _validate_commands`가 id·kind·argv·runtime_resources만 정규화해 조용히 버리므로 집행되지 않는 죽은 선언이다. late discovery는 이 공백을 위해 설계된 경로다(`docs/proposals/opal-oppb-project-build-pilot.md` §Late environment discovery) |
| D-4. 판정 책임 불변 선언은 §3.1 `verify_command` 행에 연결한다 | 스킬 §3.2에 "probe 미등재는 검증 면제가 아니다 — 수용 판정은 §3.1 `mini_tasks[].verify_command`가 단독으로 소유한다" 한 문장만 둔다. 판정 책임 서술을 새로 만들지 않는다 | 소유 지점이 이미 있다 — `opal/skills/op-oppb-project-slice/SKILL.md:158`(`verify_command` = "capability 전체를 끝까지 판정하는 독립 검증 명령")과 §4 자기검사의 "모든 미니 태스크에 `verify_command`가 있다". 중복 서술은 두 곳이 갈라질 때 어느 쪽이 계약인지 모호해진다 |
| D-5. 제안서 §P2.2의 대응 문장도 같이 고친다 | `docs/proposals/opal-oppb-project-build-pilot.md:544`("bootstrap·build·test·검증 명령을 …")과 `:571`("각 실행·검증 명령의 실제 미추적 출력 경로")을 관측 전용 명령 기준으로 개정한다. 그 외 §P2.2 본문·정책 3종·late discovery 절차는 그대로 둔다 | 스킬만 고치면 계약이 자기모순이다 — `opal/skills/opal-pilot-project-build/SKILL.md:27`이 "충돌하면 제안서가 이긴다"로 우선순위를 고정해 두어, 개정된 스킬이 제안서에 의해 되돌려진다 |
| D-6. 스킬 `변경이력` 표에 행을 추가하지 않는다 | 기존 표는 그대로 두고 이번 변경 행을 적지 않는다 | C-6과 프로젝트 금지사항(수기 누적 이력 절). 변경 근거는 태스크 캡슐과 git 이력이 소유한다 |
| D-7. 배포는 이 태스크 워크트리 체크아웃에서 실행하고 검증은 소스 트리 밖에서 한다 | `bash <워크트리>/scripts/install-mac.sh` 메뉴 [1]로 배포하고, `cd ~` 후 절대경로 `~/.opal/skills/op-oppb-project-slice/SKILL.md`를 읽어 확인한다 | install은 main이 아니라 **실행한 스크립트의 체크아웃**을 읽는다 — `scripts/install-mac.sh:112` `FRAMEWORK_ROOT="$(dirname "$script_dir")"`, `:1244-1252`가 그 `FRAMEWORK_ROOT/opal/skills/*`를 `~/.opal/skills/`로 복사한다. 따라서 브랜치 내용도 배포되지만, **허브(main 체크아웃)에서 재설치하면 미merge 변경은 사라진다** — CLOSE의 main merge 전에는 허브에서 install을 돌리지 않는다 |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. 슬라이스 스킬 probe 등재 계약 개정 | `opal-task-agent` | `opal/skills/op-oppb-project-slice/SKILL.md` | §3.2에서 `:195` 문장("`verify_command`와 `run_command`에 쓴 argv는 여기에도 같은 내용으로 등재한다")을 삭제하고 D-2의 등재 기준 2조건으로 대체한다. `kind` 어휘를 D-1의 `bootstrap`·`build` 2종으로 규정하고, 예시 JSON의 `verify-T01`/`kind: "test"` 항목을 관측 전용 예시(`{"id": "lint", "kind": "build", ...}` 같은 판정에 쓰이지 않는 명령)로 교체한다. 그 다음 문장("등재되지 않은 명령의 미추적 출력은 …")을 D-3의 선언 경로 서술로 바꾼다 — 사전에 아는 경로·자원은 `lease.ephemeral_writes`·`lease.runtime_resources`에 적고 잔여는 late discovery가 revision당 1 batch로 회수하며, 그래서 미등재가 관측 공백이 아니다. D-4의 판정 책임 한 문장을 §3.2에 넣고 §3.1 `verify_command` 행을 참조로만 건다. `:84`·`:107`의 `ephemeral_write_hints` 서술이 새 기준과 같은 말을 하도록 정합만 맞춘다. `변경이력` 표는 손대지 않는다 | 없음 | P1 | AC-1, AC-2, AC-3, AC-4, C-1, C-5, C-6 |
| W-2. 제안서 §P2.2 문장 정합 | `opal-task-agent` | `docs/proposals/opal-oppb-project-build-pilot.md` | `:544-545`의 "bootstrap·build·test·검증 명령을 격리된 probe snapshot에서 하나씩 단독 실행한다"를 관측 전용 명령(bootstrap·build)만 실행한다로 고치고, 판정 명령은 Supervisor가 실제 워크트리에서 `verify_command`로 실행한다는 경계를 한 문장으로 못 박는다. `:571`의 "각 실행·검증 명령의 실제 미추적 출력 경로"에서 검증 명령을 빼고, 미등재 판정 명령의 미추적 출력은 lease 힌트와 late discovery가 담당한다고 잇는다. 정책 3종 표·late discovery 절차·입력 hash 5종 서술은 변경하지 않는다 | 없음 | P1 | AC-4, C-4 |
| W-3. 배포와 배포본 확인 | `opal-task-agent` | `~/.opal/skills/op-oppb-project-slice/SKILL.md`(배포 산출물) | 워크트리 체크아웃에서 `bash scripts/install-mac.sh` 메뉴 [1]을 실행해 배포한다(D-7). 그 뒤 `cd ~`로 소스 트리 밖에서 배포본을 열어 등재 기준 2조건·`kind` 2종·미등재 선언 경로·판정 책임 문장 4개가 모두 존재하는지 확인하고, 배포본과 소스의 diff가 0인지 대조한다. `~/.opal/` 파일을 직접 편집하지 않는다 | W-1, W-2 | P2 | AC-7, C-3 |
| W-4. 태스크 142 probe 명령 갱신과 seal 재개 | `opal-task-agent` | `.opal-worktrees/task_142/tasks/142-260918-oppb-E2E-여정조각-라이브러리/.oppb-probe-commands.json` | 새 기준으로 명령 집합을 다시 만든다 — R1 위반 8건(`suite-test-tool`, `verify-T01`~`verify-T07`)을 제거하고, 판정에 쓰이지 않는 `probe-e2e-clean-dryrun`·`probe-skill-registry-validate`의 `kind`를 `test`에서 `build`로 고친다. `config`·`lockfile`·`toolchain`과 남는 명령의 argv·`runtime_resources`는 그대로 둔다. 그 다음 142의 run root에 대해 `probe seal`을 실행해 결과 JSON에서 `probe_runs[]` 전건 `exit_code: 0`, 각 `duration_ms < 180000`, `.opal/oppb-environment.json` 생성과 `input_hash`·`ephemeral_write_set` 존재를 확인하고 출력을 증거로 남긴다. 142의 `.oppb-workgraph-spec.json`·슬라이스 형태·`INTENT.md`는 건드리지 않는다. R2로 탈락하는 명령이 나오면 그 명령을 등재에서 빼고, 해당 자원이 142 spec의 기존 `lease.runtime_resources`로 이미 선언돼 있는지 확인한 뒤 결과를 PM에 보고한다(spec은 수정하지 않는다) | W-3 | P3 | AC-5, AC-6, C-1 |
| W-5. 회귀 확인 | `opal-task-agent` | `opal/tools/oppb-runtime-tool/tests/`, `scripts/tests/test_archive_contents.sh` | 워크트리에서 `"$HOME/.opal/.venv/bin/python" -m unittest discover -s opal/tools/oppb-runtime-tool/tests`와 `bash scripts/tests/test_archive_contents.sh`를 실행해 변경 전후 동일 통과(exit 0, 실패 0)를 확인한다. 코드·`.gitattributes` 무변경이므로 결과가 달라지면 그 자체가 범위 이탈 신호다 | W-1, W-2 | P3 | AC-8, C-1, C-2 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. 남은 관측 명령 중 `bootstrap-npm-ci`가 180초 안에 끝나지 않는다 | `probe.py:64 COMMAND_TIMEOUT_SECONDS = 180`. 스냅샷에는 `node_modules`가 없고(`probe.py:309` 추적 tree만 복사) 명령마다 스냅샷이 새로 만들어진다(`probe.py:405`) | timeout이면 `probe_command_failed`로 seal이 다시 거부돼 AC-5·AC-6이 닫히지 않는다. C-1 때문에 이번 태스크에서 상수를 고칠 수 없다 | 기준 R2에 180초를 등재 전제로 못 박아 문서가 먼저 거른다(W-1). 실측은 W-4의 seal 출력 `duration_ms`로 확인한다. 초과하면 해당 명령을 등재에서 빼고 `dashboard/frontend/node_modules`는 late discovery가 회수하도록 둔 뒤, timeout 상수 변경은 별도 태스크 후보로 PM에 보고한다 — 이 PLAN에서 코드를 고치지 않는다 |
| H-2. 남은 관측 명령이 export-ignore 경로를 입력으로 전제한다 | `.gitattributes`가 `/tasks/`·`/docs/`·`/.opal/`·`/.gitignore`를 export-ignore하므로 `git archive HEAD` 산출물에 없다. 142의 `probe-e2e-clean-dryrun`은 `.opal/e2e/` 아래 설정을 읽을 수 있다 | 스냅샷에서 exit≠0 → seal 거부. 태스크 142가 처음 막힌 것과 같은 실패 형태다 | R2가 이 경우도 미등재 사유로 규정한다(W-1). W-4의 seal 실행이 실제로 판별하고, 탈락 명령의 자원이 142 spec의 `lease.runtime_resources`에 이미 있는지 대조한다. spec은 수정하지 않는다(C 유지) |
| H-3. 배포본이 아니라 소스를 읽고 "반영됐다"고 오판한다 | `scripts/install-mac.sh:112`의 `FRAMEWORK_ROOT` 기준 복사. 소스 트리 안에서 확인하면 소스를 읽는 거짓 양성이 난다. 허브(main 체크아웃)에서 재설치하면 미merge 변경은 배포본에서 사라진다 | AC-7이 거짓 통과하고, CLOSE 이후 다른 세션이 옛 계약을 읽어 태스크 142가 다시 막힌다 | W-3이 `cd ~` 후 절대경로로만 배포본을 확인하고 소스와 diff를 대조한다. 허브 install은 main merge 이후에만 안내한다(D-7) |
| H-4. 스킬만 고치면 제안서가 옛 규칙을 되살린다 | `opal/skills/opal-pilot-project-build/SKILL.md:27` — "충돌하면 제안서가 이긴다" | 개정이 무효가 되어 AC-4가 실질적으로 깨진다 | W-2가 제안서 §P2.2의 해당 2문장을 같은 기준으로 맞춘다. 두 문장 밖은 건드리지 않는다([MUST] `~/.opal/PRINCIPLES.md` §3: "Touch only what the plan names.") |

## Release and recovery

- 적용 순서: P1(W-1 스킬 + W-2 제안서, 서로 다른 파일이라 병렬) → P2(W-3 install 배포와 배포본 확인) → P3(W-4 태스크 142 갱신·seal, W-5 회귀). 배포는 워크트리 체크아웃에서만 실행한다. main merge는 CLOSE 소유이며, merge 이후 허브에서 재설치할 때 비로소 다른 세션의 기본 배포본이 갱신된다.
- 검증 범위: 결정론 — W-3의 문장 4종 존재와 소스·배포본 diff 0, W-5의 테스트 exit 0. 실제 연동 — W-4의 `probe seal` 실행 출력(`probe_runs[]` 전건 exit 0, `duration_ms`, `.opal/oppb-environment.json` 봉인). 문서 변경분에 대한 자동 테스트는 신설하지 않는다.
- 실측 경계: 등재 명령 1건당 180초(`probe.py:64`)가 상한이다. seal 1회 전체는 등재 8건 기준 그 합으로 관측하고, 초과 시 H-1 대응으로 넘어간다.
- 실패 시: 문서 2건은 git revert로 되돌리고 `scripts/install-mac.sh`를 다시 실행하면 배포본이 이전 상태로 복구된다(`install_opal`이 `skills`를 통째로 재배치). 142의 `.oppb-probe-commands.json`은 변경 전 사본을 스크래치패드에 남긴 뒤 수정하고, seal 실패 시 그 사본으로 되돌린다 — 142의 run root 상태와 `.oppb-workgraph-spec.json`은 이 태스크가 쓰지 않는다.
