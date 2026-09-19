---
template: sdlc-v2
---
# TASK: OPPB probe 명령의 관측·판정 역할 분리

## Problem

태스크 142(ai-framework에서 OPPB 첫 실사용)가 P2 `environment_seal`에서 구조적으로 막혔다. 프로젝트 결함이 아니라 OPPB 계약의 설계 공백이다.

`op-oppb-project-slice/SKILL.md:195`가 **"`mini_tasks[].verify_command`와 `run_command`에 쓴 argv는 여기에도 같은 내용으로 등재한다"**를 요구한다. 그래서 수용 판정용 명령이 probe 명령 집합에 들어가고, `probe seal`은 그 명령이 exit≠0이면 run 시작을 거부한다(`probe.py` `_observe_command`).

그런데 probe는 판정이 아니라 관측을 위해 설계된 격리 실행기다. 세 가지가 겹쳐 판정용 명령이 구조적으로 통과할 수 없다.

1. `probe.py:405 _observe_command`가 명령마다 `_make_snapshot`으로 새 스냅샷을 만들고 `finally`에서 `shutil.rmtree`한다. bootstrap이 만든 의존성(`node_modules` 등)이 다음 명령에 전달되지 않는다 — 명령 순서를 어떻게 배치해도 그렇다.
2. `probe.py:309 _make_snapshot`이 `git archive HEAD`로 추적 tree만 복사한다. `.gitattributes`의 `export-ignore` 경로는 추적돼 있어도 archive 출력에서 빠진다. 이 저장소는 `/tasks/`·`/docs/`·`/.opal/`·`/.gitignore`를 export-ignore하므로, 동결 fixture를 읽는 테스트가 `FileNotFoundError`로 실패하고(태스크 142 실측 30건, `test_e2e_human_executor.py:52` `_frozen_scenario`) `.gitignore` 기반 판정도 성립하지 않는다.
3. `probe.py:64 COMMAND_TIMEOUT_SECONDS = 180`인데 이 저장소 전체 스위트 실측은 148~222초다.

판정 주체는 원래 Supervisor가 실제 워크트리에서 실행하는 `verify_command`다. probe가 같은 명령의 exit code로 run 시작을 막는 것은 역할 혼동이며, 그 결과 OPPB는 export-ignore를 쓰는 저장소에서 P2를 통과할 수 없다.

원인 특정에 슬라이서 왕복 3회가 들었다. 개별 명령의 exit≠0으로만 드러나 진단 가능한 오류가 아니었다.

## Proposed outcome

OPPB가 이 저장소에서 P2 `environment_seal`을 통과한다. probe는 미추적 쓰기·실행 자원 관측이라는 자기 역할만 수행하고, 수용 판정은 `verify_command`가 계속 단독 소유한다.

슬라이스 스킬을 읽는 사람이 어떤 명령을 probe에 등재해야 하고 어떤 명령은 등재하지 않는지, 그리고 등재하지 않는 명령의 미추적 쓰기를 무엇으로 대신 선언하는지 알 수 있다.

## Affected users and systems

- `opal/skills/op-oppb-project-slice/SKILL.md` — 등재 요구 조항(`:195`)과 그 주변 계약.
- OPPB를 쓰는 모든 프로젝트의 P2 단계. 특히 `.gitattributes` `export-ignore`를 쓰는 저장소.
- 태스크 142가 이 변경의 첫 소비자다 — 변경 후 142의 `.oppb-probe-commands.json`을 갱신하고 P2를 재개한다.
- 범위 제외: `opal/tools/oppb-runtime-tool/` 코드 변경(`probe.py` 스냅샷 방식·timeout), `.gitattributes` 개정, 태스크 142의 spec·슬라이스 형태 변경, OPPB 외 pilot.

## Constraints

- C-1: `opal/tools/oppb-runtime-tool/` 코드를 수정하지 않는다. 이번 변경은 스킬 계약 개정만으로 성립해야 한다.
- C-2: `.gitattributes`를 수정하지 않는다. 릴리스 tarball 의미와 `scripts/tests/test_archive_contents.sh` 회귀를 건드리지 않는다.
- C-3: `~/.opal/` 배포 파일을 직접 수정하지 않는다. 프로젝트 소스를 고치고 install로 배포한다.
- C-4: 판정 주체를 옮기지 않는다 — 수용 판정은 `verify_command`가 계속 소유하며, probe에서 빼는 것이 판정 면제를 뜻하지 않아야 한다.
- C-5: 기존 OPPB 실행 중인 태스크의 `workgraph.json`·`acceptance.json` 스키마를 바꾸지 않는다.
- C-6: 수기 누적 변경이력 절을 만들지 않는다.

## Acceptance criteria

- AC-1: `op-oppb-project-slice/SKILL.md`가 probe 등재 대상을 `kind`로 구분해 규정한다 — 관측용(`bootstrap`·`build`)은 등재하고, 판정용(`test`·`verify` 계열)은 등재하지 않는다는 규칙이 문서에 있다.
- AC-2: 등재하지 않는 명령의 미추적 쓰기를 무엇으로 선언하는지가 문서에 있다. 관측 공백이 그대로 방치되지 않는다.
- AC-3: `verify_command`의 판정 책임이 변하지 않음이 문서에 명시된다 — probe 미등재가 검증 면제가 아니라는 문장이 있다.
- AC-4: 기존 `:195` 등재 요구 문장이 남아 있지 않거나, 남는다면 `kind` 구분과 모순되지 않는 형태로 개정돼 있다.
- AC-5: 변경된 스킬로 태스크 142의 `.oppb-probe-commands.json`에서 `suite-test-tool`과 `verify-T0n` 7건을 제외했을 때, 남은 명령이 probe 스냅샷 조건에서 전건 exit 0이다. 실제 실행 출력으로 확인한다.
- AC-6: 태스크 142의 `probe seal`이 통과해 `.opal/oppb-environment.json`이 봉인된다.
- AC-7: `opal/skills/` 소스 변경이 install로 배포본 `~/.opal/skills/op-oppb-project-slice/SKILL.md`에 반영되고, 배포본에서 AC-1~AC-4 문장이 확인된다.
- AC-8: 기존 회귀 0 — `opal/tools/oppb-runtime-tool` 테스트와 `scripts/tests/test_archive_contents.sh`가 변경 전후로 통과한다.

## Open questions

- probe 미등재 명령의 미추적 쓰기를 `ephemeral_write_hints`로 선언하게 할지, 별도 필드를 두게 할지는 PLAN에서 확정한다. 새 필드 신설은 C-5(스키마 불변)와 충돌할 수 있다.
