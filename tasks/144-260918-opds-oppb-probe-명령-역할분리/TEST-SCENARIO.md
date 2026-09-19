---
template: sdlc-v2
---
# TEST-SCENARIO: OPPB probe 명령의 관측·판정 역할 분리

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: 로컬 워크트리 `/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_143` (branch `feat/OP-TASK-143`, base `main`). 셸에서 `grep`·`sed`·`diff`·`git`·`bash`와 `"$HOME/.opal/.venv/bin/python"`을 쓴다.
- 소비 대상 태스크: `/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_142` — AC-5·AC-6의 검증이 이 워크트리에서 일어난다. 142의 run root는 `/Volumes/Data/AIStudio/workspace/ai-framework/.opal-runs/20260918T112303Z-acbbf7af`이며 workgraph revision 1이 이미 load돼 있다.
- 배포본: `~/.opal/skills/op-oppb-project-slice/SKILL.md`. **[MUST] 배포본 확인은 `cd ~` 후 절대경로로만 한다** — 소스 트리 안에서 읽으면 소스를 읽는 거짓 양성이 난다(PLAN H-3).
- 공통 데이터: 없음.
- 대역 사용과 한계: 사용하지 않음. probe seal·install·회귀 스위트를 전부 실제 실행한다.
- 실행 조건: 자동 실행. 단 `probe seal`과 회귀 스위트는 포트·고정 경로 자원을 쓰므로 **동시 실행하지 않는다**(태스크 142에서 동시 실행이 오판을 만든 전례가 있다).
- RED 적용: 없음 — 전 시나리오 `구현 후`. 근거는 PLAN `Approach`의 RED-first 비적용 판정(`harness/red-first.md:15`·`:48`). 산문 계약 변경이라 새 실행 코드가 없다.

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1, AC-4 | W-1 적용 후 `opal/skills/op-oppb-project-slice/SKILL.md` | §3.2 전문을 읽고, 기존 등재 요구 문장(`verify_command`와 `run_command` argv를 같은 내용으로 등재)의 잔존 여부를 확인한다 | 그 문장이 없거나 `kind` 구분과 모순되지 않는 형태로 개정돼 있다. 등재 대상을 가르는 기준이 문서에 명시되고, `kind` 어휘가 `bootstrap`·`build` 2종으로 규정돼 있다 | 결정론 검사(shell `sed`+`grep`) · 로컬 워크트리 | 구현 후 |
| S-2 | AC-2 | W-1 적용 후 §3.2 | 미등재 명령의 미추적 쓰기를 무엇으로 선언하는지 서술을 찾는다 | `lease.ephemeral_writes`·`lease.runtime_resources` 선언과 late discovery 회수 경로가 적혀 있다. 미등재가 관측 공백이 아니라는 인과가 읽힌다 | 결정론 검사(shell `grep -n`) · 로컬 워크트리 | 구현 후 |
| S-3 | AC-3, C-4 | W-1 적용 후 §3.2 | 판정 책임 서술을 찾고, §3.1 `verify_command` 행과의 참조 관계를 확인한다 | "미등재는 검증 면제가 아니다"에 해당하는 문장이 있고 판정 소유자가 `verify_command`로 지목된다. 같은 정의를 두 곳에 복제하지 않고 참조로 연결돼 있다 | 결정론 검사(shell `grep -n`) · 로컬 워크트리 | 구현 후 |
| S-4 | AC-4, H-4 | W-2 적용 후 `docs/proposals/opal-oppb-project-build-pilot.md` | `:544-545`와 `:571` 구간을 읽는다 | 두 문장이 관측 전용 명령만 probe가 실행한다는 서술로 바뀌었고, 판정 명령은 Supervisor가 워크트리에서 `verify_command`로 실행한다는 경계가 있다. 정책 3종 표·late discovery 절차·입력 hash 5종 서술은 그대로다 | 결정론 검사(shell `sed`+`git diff`) · 로컬 워크트리 | 구현 후 |
| S-5 | AC-7, C-3, H-3 | W-3 적용 후 | `cd ~`로 소스 트리를 벗어난 뒤 `~/.opal/skills/op-oppb-project-slice/SKILL.md`를 절대경로로 읽고, 워크트리 소스와 대조한다. 대조는 **양쪽에서 `## 변경이력` 절 이하를 제거한 뒤** 수행한다 | 배포본에 S-1~S-3이 요구한 4개 서술(등재 기준·`kind` 2종·미등재 선언 경로·판정 책임)이 모두 존재하고, `## 변경이력` 절 제외 diff가 0이다. `~/.opal/` 파일을 직접 편집한 흔적이 없다 | 결정론 검사(shell `cd ~`+`sed`+`diff`) · 홈 디렉터리 | 설치 후 |
| S-6 | AC-5 | W-4의 명령 집합 갱신 후, seal 실행 **전** | 142의 `.oppb-probe-commands.json`을 읽어 명령 목록과 각 `kind`를 확인한다 | 판정용 8건(`suite-test-tool`·`verify-T01`~`verify-T07`)이 제거됐고, 판정에 쓰이지 않는 `probe-e2e-clean-dryrun`·`probe-skill-registry-validate`의 `kind`가 `build`다. `config`·`lockfile`·`toolchain`과 남는 명령의 argv·`runtime_resources`는 변경 전과 동일하다 | 결정론 검사(shell `python3 -m json.tool`+`git diff`) · 로컬 워크트리 | 구현 후 |
| S-7 | AC-5, AC-6, H-1, H-2 | S-6 통과 후, 다른 실행이 동시에 돌지 않는 상태 | 142 run root에 `oppb-runtime-tool probe seal`을 실행한다 | `ok: true`. `probe_runs[]` 전건 `exit_code: 0`이고 각 `duration_ms < 180000`이다. `.opal/oppb-environment.json`이 생성되고 `input_hash`와 `ephemeral_write_set`이 존재한다 | integration(실제 도구 실행) · 로컬 워크트리(142) | 구현 후 |
| S-8 | AC-6, C-1, C-5 | S-7 통과 후 | 142의 `.oppb-workgraph-spec.json`·`INTENT.md`와 `opal/tools/oppb-runtime-tool/` 아래 파일의 변경 여부를 확인하고, 142 run root의 `workgraph.json`·`acceptance.json`이 seal 전후로 같은 스키마·필드 집합인지 대조한다 | 소스 세 대상 모두 diff 0이고, run root의 두 문서에 신규 필드·삭제 필드가 없다 — 슬라이스 형태·INTENT·probe 도구 코드·실행 중 태스크 스키마를 건드리지 않고 seal이 통과했다 | 결정론 검사(shell `git diff --stat`+`python3 -m json.tool` 키 집합 대조) · 로컬 워크트리(142) | 구현 후 |
| S-9 | AC-8, C-1, C-2 | 전 Work item 적용 후, 단독 실행 | `"$HOME/.opal/.venv/bin/python" -m unittest discover -s opal/tools/oppb-runtime-tool/tests`와 `bash scripts/tests/test_archive_contents.sh`를 순차 실행한다 | 둘 다 exit 0, 실패 0이다. 코드·`.gitattributes`를 안 고쳤으므로 변경 전과 같은 결과여야 한다 | integration(실제 스위트 실행) · 로컬 워크트리 | 구현 후 |
| S-10 | C-1, C-2, C-6 | 전 Work item 적용 후 | `git status --porcelain`과 `git diff --name-only`로 변경 파일 집합을 확인하고, 스킬 문서의 `변경이력` 표 행 수를 변경 전후로 대조한다 | 변경 파일이 PLAN이 명명한 것(스킬 1·제안서 1·142 probe 명령 1·태스크 캡슐)뿐이다. `opal/tools/oppb-runtime-tool/`·`.gitattributes`는 없다. `변경이력` 표 행 수가 변하지 않았다 | 결정론 검사(shell `git`+`grep -c`) · 로컬 워크트리 | 구현 후 |
| S-11 | H-1 (경계) | S-7에서 timeout 초과가 발생한 경우에만 | 초과한 명령을 등재에서 빼고, 그 자원이 142 spec의 기존 `lease.runtime_resources`에 이미 선언돼 있는지 대조한 뒤 seal을 재실행한다 | 탈락 사유와 대조 결과가 기록되고 seal이 통과한다. **142의 `.oppb-workgraph-spec.json`은 수정하지 않는다.** timeout 상수 변경은 이 태스크에서 하지 않고 후속 후보로만 보고한다 | integration(실제 도구 실행) · 로컬 워크트리(142) | 구현 후 |
| S-12 | AC-1, AC-4 (목표) | 전 Work item 적용 후, 개정 전 대조군은 `git show HEAD:opal/skills/op-oppb-project-slice/SKILL.md` | 개정 전·후 §3.2를 나란히 놓고, "태스크 142를 막았던 등재 요구가 사라졌는가"와 "그 자리에 판정 없는 관측 기준이 들어왔는가"를 확인한다 | **구형 잔존 0**: 판정용 명령을 등재하라는 요구가 남아 있지 않다. **신형 채택**: 등재 기준 2조건이 그 자리를 대신한다. 개정 전 문서에서는 142의 명령 집합이 규칙을 만족할 방법이 없었음이 대조로 드러난다 | 결정론 검사(shell `git show`+`diff`) · 로컬 워크트리 | 구현 후 |
| S-13 | AC-1, AC-4, C-4 (부정) | W-4의 명령 집합 갱신 후, S-7 통과를 확인한 뒤 | 개정된 기준을 **어기는** 명령 1건(R1 위반 — exit code가 수용 판정에 쓰이는 명령, 예: `verify-T01` 원본)을 임시 사본 명령 파일에 되돌려 넣고 142 run root에 `probe seal`을 실행한다. 확인 후 원래 명령 집합으로 되돌린다 | `ok: false`이고 `error`가 `probe_command_failed`다 — 기준 위반이 산문 권고가 아니라 도구 거부로 집행된다. 정상 집합으로 되돌리면 다시 통과한다. **142의 `.oppb-workgraph-spec.json`·`INTENT.md`는 이 시나리오에서도 변경되지 않는다** | integration(실제 도구 실행) · 로컬 워크트리(142) | 구현 후 |
