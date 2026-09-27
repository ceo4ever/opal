---
template: sdlc-v2
---
# PLAN: 검증 도구 실행 정확성 복구

> 입력: [TASK.md](TASK.md), [REQUEST.md](REQUEST.md) §A1 및 공통 계약

## Approach

`test-tool unit`이 실제 검사 명령과 설치 확인 명령을 구분해 실행하고, 실제로 실행한 검사의 명령·실행 디렉터리·설정 출처·검사 범위·결과를 한 응답에 남기게 한다. 새 실행기를 만들지 않고 기존 `unit` 경로(`opal/tools/test-tool/test_tool.py:162-187` → `opal/tools/test-tool/lib/runner.py:133-200`)와 설정 해석(`opal/tools/test-tool/lib/resolver.py:194-284`)을 보완한다.

변경 전 확인 사실(E1·E2):

- **설치 확인 명령이 검사로 실행된다.** 실행기는 도구 항목의 `check` 값을 검사 명령으로 실행한다(`opal/tools/test-tool/lib/runner.py:172-176`). 전역 템플릿의 unit 도구는 모두 `--version`류다(`opal/templates/test-tools.yaml:52`, `:58`, `:64`, `:77`, `:89`, `:105`). 스키마는 `check`를 "설치 여부를 확인하는 명령"으로 정의한다(`opal/core/references/test-tools-schema.yaml:61-64`). 전역 템플릿으로 해석되는 프로젝트의 `unit`은 버전 확인만 하고 통과한다.
- **빈 실행이 통과다.** 계층이 없거나 `check`가 비면 건너뛰고(`opal/tools/test-tool/lib/runner.py:163-174`), 실패가 없으면 `ok: not overall_failed`로 `true`다(`:191-196`). 실행한 계층이 0개여도 exit 0이다.
- **stop-on-fail 이후 계층이 응답에서 사라진다.** `break` 뒤 계층은 `layers`에 없다(`opal/tools/test-tool/lib/runner.py:186-189`). 미실행 여부를 응답만으로 구분할 수 없다.
- **변경 파일 인자가 버려진다.** `--changed-files`는 선언만 있고(`opal/tools/test-tool/test_tool.py:437`) `cmd_unit`은 실행기에 넘기지 않는다(`opal/tools/test-tool/test_tool.py:176-181`).
- **Python 추론 lint 명령이 무효다.** 추론은 `ruff .`을 낸다(`opal/tools/test-tool/lib/resolver.py:142`). 설치된 ruff 0.15.17에서 `ruff .`은 `error: unrecognized subcommand '.'`, exit 2다(실행: `$TMPDIR`에서 `ruff .`, 2026-09-27 07:37 KST). 올바른 명령은 `ruff check .`이다.
- **출처 경로가 응답에 없다.** resolve 응답은 `source`만 있고 파일 경로는 없다(`opal/tools/test-tool/lib/resolver.py:219-226`, `:250-257`, `:269-276`).
- **기준선 회귀.** `opal/tools/test-tool/tests/test_test_tool.py`는 변경 전 17 passed(실행: 작업본 루트에서 `~/.opal/.venv/bin/python -m pytest opal/tools/test-tool/tests/test_test_tool.py -q`). 기존 TestUnit 픽스처는 실제 검사 명령을 `check`에 넣은 구형 설정이다(`opal/tools/test-tool/tests/test_test_tool.py:295-307`, `:327-339`). test-tool 전체 회귀는 변경 전 23 failed·529 passed·3 skipped다(실행: 작업본 루트에서 `~/.opal/.venv/bin/python -m pytest opal/tools/test-tool/tests -q -p no:cacheprovider -rf`, 2회 동일). 실패는 모두 E2E SUT 기동 계열(`opal/tools/test-tool/tests/test_e2e_sut_http_surfaces.py` 16, `opal/tools/test-tool/tests/test_e2e_surface_fidelity.py` 5, `opal/tools/test-tool/tests/test_e2e_skeleton.py` 1, `opal/tools/test-tool/tests/test_red_s27_no_retry_on_product_failure.py` 1)이다. `test_e2e_skeleton.py`는 작업본 `dashboard/frontend`에서 `npm run dev` 기동이 실패한다(의존성 미설치). AC-7은 이 목록을 기준선으로 비교한다.
- **기존 사용자 설정.** `/Volumes/Data/AIStudio/workspace` 아래 4단계 깊이까지 작업본을 제외하고 `.opal/test-tools.yaml` 파일은 0건이다(실행: `find /Volumes/Data/AIStudio/workspace -maxdepth 4 -path '*/.opal/test-tools.yaml' -not -path '*/.opal-worktrees/*'`). 이관 대상은 전역 템플릿과, 사용자가 앞으로 가져올 수 있는 구형 설정 형태다.

범위 밖: `check` 서브명령의 설치 판정 방식(`opal/tools/test-tool/lib/runner.py:50-52`의 PATH 조회), GC 판정 문서 정합(A2), GC 완화(B), 증거 게이트(C), 증분 재검사(D), 과거 호출 조사. 이 항목은 TASK §Affected users and systems가 분리했다.

## Findings

### 직접 변경

소비자 판정 기준: `unit`·`resolve`·`check`·`integration` 서브명령이나 `test-tools.yaml` 도구 필드를 실행에 쓰는 코드·스킬·에이전트·문서를 소비자로 본다. `scenario-*`·`e2e *`만 쓰는 소비자는 이 변경의 입력·출력을 읽지 않는다. 조사 명령: 작업본에서 `grep -rnIE "test-tool|test-tools" opal skills scripts docs README.md`로 참조를 뽑고, `scenario-*`·`e2e` 하위 명령만 쓰는 행을 제외했다.

- `opal/tools/test-tool/lib/runner.py` — 소비자(코드). `run_unit_layers`가 `check`를 검사 명령으로 실행한다(`:172-176`). 새 실행 계약의 본체로 바꾼다.
- `opal/tools/test-tool/lib/resolver.py` — 소비자(코드, `resolve`·`unit`·`check`·`integration` 공통 입력). 추론 명령(`:79-89`, `:142-144`, `:167`)과 출처 경로 부재(`:219-276`)를 고친다.
- `opal/tools/test-tool/test_tool.py` — 소비자(코드, CLI). `cmd_unit`(`:162-187`)이 변경 파일을 넘기고 새 결과 상태를 exit·오류 코드로 대응시킨다. `ERROR_CODES`(`:51-89`)에 새 코드를 더한다.
- `opal/tools/test-tool/tests/test_test_tool.py` — 소비자(회귀 테스트). 구형 픽스처(`:295-307`, `:327-339`)를 새 설정 형식으로 옮기고 새 계약 테스트를 더한다.
- 실제 도구 고정 사례 폴더(test-tool 테스트 fixtures 아래 unit-real, W-3 변경 대상) — 신규. 실제 도구로 정상·위반을 관측할 고정 사례 프로젝트.
- `opal/templates/test-tools.yaml` — 소비자(전역 설정). unit 도구 전부가 `--version`류 `check`만 가진다(`:49-111`). 실제 검사 명령을 `run`으로 선언한다.
- `opal/core/references/test-tools-schema.yaml` — 소비자(스키마 문서). `tiers.item_fields`(`:158-192`)에 `run`·`run_files`·`file_globs`를 정의하고 `check`는 설치 확인 전용임을 명시한다.

### 회귀 확인

영향 없음 판정 소비자와 근거:

- `opal/tools/test-tool/lib/e2e_adapter.py` — `integration`은 `tiers.integration.e2e` 후보만 읽고(`:275`) api_db는 `skip`으로 둔다(`:110`). 도구 `check`·`run`을 실행하지 않으므로 계약 변경의 영향이 없다. `integration` 회귀 테스트 통과만 확인한다.
- `opal/tools/test-tool/lib/scenario.py` — `scenario-*`는 tiers를 읽지 않는다(작업본에서 `grep -n "tiers\|test-tools\|run_unit\|resolve_test" opal/tools/test-tool/lib/scenario.py` 결과 0건).
- `scripts/install-mac.sh` — `templates/`를 통째로 배포하고(`:1357`), 셸 설정에 `OPAL_TEST_TOOLS_GLOBAL`을 등록한다(`:1136-1153`). 배포 경로와 환경변수 이름이 그대로라 수정하지 않는다. AC-8에서 실제 배포본으로 확인한다.
- `opal/skills/op-dev-execute/SKILL.md` — test-tool 명령을 구조적 workflow로 규정할 뿐(`:23`) 서브명령·필드를 직접 쓰지 않는다. 실행 절차는 가이드가 소유한다.
- `opal/skills/op-scenario-gate/SKILL.md` — 현재 `resolve` 호출이 없다. 변경 이력 행(`:219`)만 과거 호출 제거를 기록한다.
- `opal/skills/op-dev-qa/personas/qa-engineer.md` — 레지스트리를 참고해 도구를 고른다는 행동 지침(`:15`)만 있고 명령·필드 의존이 없다.
- `opal/core/references/tools.md` — 도구 레지스트리 설명(`:42`)은 "test-tools.yaml을 읽어 실행·판정"으로 변경 후에도 참이다.
- `opal/skills/opal-pilot-sdd/SKILL.md`, `opal/skills/opal-pilot-project-loop/SKILL.md`, `opal/agents/opal-evaluator-agent/AGENT.md`, `opal/agents/opal-loop-action-agent/AGENT.md`, `opal/agents/opal-task-action-agent/AGENT.md`, `opal/skills/opal-e2e/SKILL.md`, `opal/skills/op-dev-test-scenario/SKILL.md` — E2E 계약(`opal/skills/opal-pilot-sdd/SKILL.md:289`), `scenario-*`(`opal/agents/opal-loop-action-agent/AGENT.md:413`), 기계검증 소관 언급(`opal/agents/opal-evaluator-agent/AGENT.md:75`)만 쓴다. 입력·출력 의존이 없다.
- `opal/tools/tool-scan/tests/test_tool_scan.py` — 도구 이름 목록만 단언한다(`:329`, `:933`).
- `.opal/brain/pages/concept/test-two-tier-system.md` — 파생 지식 스냅샷이다. "resolve/unit/integration 서브명령이 2단계를 집행"(`:31`)은 변경 후에도 참이며 CLOSE brain ingest가 갱신 여부를 판단한다.
- `tasks/` 아래 과거 태스크 기록(예: `tasks/150-260922-opds-워크트리-태스크-소유권-이관-계약/DONE.md`)과 opst 실행 산출물은 이력이다. 소비자가 아니며 수정하지 않는다(C-7).
- 수정 없이 통과해야 하는 기존 회귀: `opal/tools/test-tool/tests/test_scenario.py`, `opal/tools/test-tool/tests/test_e2e_contract.py`, 그 밖의 `opal/tools/test-tool/tests/` E2E·RED 테스트 전체.

### 문서 갱신

- `opal/tools/test-tool/README.md` — `unit` 절(`:84-109`)을 새 결과 계약의 단일 원문으로 다시 쓴다. 계층·전체 상태값과 의미, 사유 코드, exit·오류 코드, 범위 필드, 구형 설정 이관 절차를 여기서만 정의한다(C-4). `resolve` 출력 예시(`:41-53`)에 `source_path`를 더한다.
- `opal/skills/op-dev-execute/references/execute-guide.md` — 소비자(스킬 참조, `unit --scope be`·`--scope fe` 호출 `:64-66`). 변경 파일 전달, `status: pass`만 통과로 소비, `incomplete`·`fail`의 처리 규칙을 적는다.
- `opal/agents/opal-test-agent/AGENT.md` — 소비자(에이전트, `resolve` 기반 러너 탐지 `:104`, `:107`). 실행 명령은 `run`, `check`는 설치 확인임을 명시한다.

### 미확인 가정

- H-1, H-2, H-3 참조.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| D-1. 도구 항목 필드 의미 | `check` = 설치 확인 명령(exit 0이면 설치됨), `install` = 설치 명령, `run` = 실제 검사 명령(프로젝트 전체 범위). 선택 필드 `run_files` = `{files}` 자리표시자를 가진 파일 단위 검사 명령, `file_globs` = `run_files`에 넘길 파일의 glob 목록(생략 시 전체). | TASK C-2가 check/install/run 의미를 고정했다. 스키마 원래 의미(`opal/core/references/test-tools-schema.yaml:61-64`)와 일치한다. |
| D-2. 계층 실행 순서 | 계층마다 첫 번째 도구만 쓴다(현행 `opal/tools/test-tool/lib/runner.py:167-168` 유지). ① `run`이 없으면 아무 명령도 실행하지 않고 `not_configured`(사유 `run_missing`). ② `check`가 있으면 먼저 실행해 실패 시 `tool_unavailable`(사유 `install_check_failed`)이고 `run`은 실행하지 않는다. ③ `run`(또는 D-3의 `run_files`)을 실행해 exit 0이면 `pass`, 아니면 `fail`. | run 누락 시 check를 대체 실행하지 않는다(C-2). 구형 설정의 `check`에 든 실제 검사 명령을 설치 확인으로 오인해 실행하는 일도 ①이 막는다. |
| D-3. 검사 범위 | `--changed-files`가 비어 있지 않으면 요청 파일로 기록한다. 도구에 `run_files`가 있으면 프로젝트 안에 실재하고 `file_globs`에 맞는 파일만 넘긴다. 0개면 명령을 실행하지 않고 `not_applicable`(사유 `no_matching_files`)이다. `run_files`가 없으면 `run`을 프로젝트 전체로 실행하고 범위 사유를 `file_scope_unsupported`로 남긴다. 인자가 없거나 비면 프로젝트 전체. 계층 응답 `scope` = `{kind, requested, checked, excluded: [{path, reason}], reason}` — `kind`는 `files` 또는 `project`, 제외 사유는 `missing`·`outside_project`·`pattern_mismatch`. | 요청 파일과 실제 범위를 구분하고, 파일 단위를 지원하지 않는 도구에 인자를 붙이지 않는다(C-5). |
| D-4. 결과 상태(폐쇄 목록) | 계층 `status` ∈ {`pass`, `fail`, `tool_unavailable`, `not_configured`, `not_applicable`, `not_run`}. `fail` 뒤 계층은 실행하지 않고 `not_run`(사유 `stopped_after_failure`)으로 응답에 남긴다. 전체 `status` ∈ {`pass`, `fail`, `incomplete`}: 필수 계층에 `fail`이 있으면 `fail`. 아니고 필수 계층에 `tool_unavailable`·`not_configured`가 있거나 `pass` 계층이 0개면 `incomplete`(사유 `required_layer_unverified`·`no_check_executed`·`no_layers_declared`). 그 외 `pass`. `ok`는 `status == "pass"`일 때만 `true`. | 설치 확인 실패·미설정·미실행·검사 실패·통과를 구분하고 빈 실행을 통과로 소비하지 않는다(AC-2, AC-7). |
| D-5. 필수 여부 | 도구 `required: false`인 계층의 `tool_unavailable`·`not_configured`는 전체를 `incomplete`로 만들지 않고 계층 상태로만 남는다. `required` 키가 없으면 필수로 본다. | 템플릿 a11y(`opal/templates/test-tools.yaml:67-72`, `required: false`)는 독립 실행 명령이 없다. 선택 도구의 부재가 필수 검사 통과를 가리지 않게 한다. |
| D-6. exit·오류 코드 | `pass` → exit 0. `fail` → exit 5, `error: layer_failed`(현행 유지). `incomplete` → exit 21, `error: unit_incomplete`(신규, `ERROR_CODES` 등록). 설정 해석 실패는 현행 exit 1 유지. | test-tool이 이미 쓰는 exit 0~20과 겹치지 않는 첫 값이다(`opal/tools/test-tool/README.md:377`, `opal/tools/test-tool/lib/e2e_contract.py:42`). 호출자가 실패와 미완료를 exit만으로도 구분한다. |
| D-7. 증거 필드 | 응답 최상위: `status`, `reason`(비통과 시), `scope`(fe·be), `cwd`(절대 경로), `config: {source, path}`, `requested_files`, `layers`, `stopped_at`. 계층: `name`, `tool`, `required`, `status`, `reason`, `check: {cmd, exit, status}`(실행 시), `cmd`(실제 실행한 run 명령, 미실행이면 `null`), `exit`, `stdout`, `scope`. resolve 응답에 `source_path`를 더한다(infer는 근거 파일 경로). | 명령·실행 디렉터리·설정 출처·범위·결과를 공개 CLI 출력으로 관측한다(AC-3). 별도 증거 저장소를 만들지 않고, 호출자는 이 JSON을 기존 `test-scenario.json` 증거(`scenario-mark`)에 담는다(C-6, REQUEST A1-5). |
| D-8. 계약 원문 위치 | 상태값·사유 코드·의미·exit 대응은 `opal/tools/test-tool/README.md` `unit` 절 한 곳이 원문이다. 코드에는 같은 값의 선언 목록을 두고 방출 시 대조한다. GC 판정 대응표는 만들지 않는다. | C-4. 도구별 코드 의미는 각 도구 README가 소유한다(`opal/core/references/harness/tool-output-contract.md` §오류 코드). |
| D-9. 구형 설정 이관 | 도구가 `check`를 `run`으로 자동 복사하지 않는다. `run` 없는 구형 설정은 D-2 ①에 따라 `not_configured` + `incomplete`/exit 21이고, 계층 응답에 이관 안내(`hint`)를 담는다. 이관은 사용자가 설정에 `run`을 추가하고 `check`를 설치 확인 명령으로 바꾸는 명시 편집이며, 절차와 전후 예시를 README에 둔다. | C-2 "사용자 기존 check를 임의로 run으로 복사하지 않는다". 현재 기존 사용자 설정은 0건이다(Approach 기존 사용자 설정). |
| D-10. 전역 템플릿·추론 명령 | 템플릿 unit: eslint `run: npx eslint .`·`run_files: npx eslint {files}`, tsc `run: npx tsc --noEmit`, vitest `run: npx vitest run`, ruff `run: ruff check .`·`run_files: ruff check {files}`·`file_globs: ["*.py"]`, mypy `run: mypy .`, pyright `run: pyright`, pytest `run: pytest`. eslint `file_globs`는 js·jsx·ts·tsx·mjs·cjs. integration api_db pytest에 `run: pytest`. `check`는 버전 확인 명령으로 유지한다. 추론(`opal/tools/test-tool/lib/resolver.py`)도 같은 명령·필드를 낸다. package.json 추론의 `required`는 현행(eslint·tsc만 명시)을 유지한다. | AC-4·AC-6. `ruff .`은 무효다(Approach 실측). 단발 실행이며 watch 플래그를 쓰지 않는다(`opal/tools/test-tool/lib/runner.py:17`). |
| D-11. 배포 | 소스 검증 통과 후 작업본에서 정식 설치(`scripts/install-mac.sh`, 메뉴 1)를 실행한다. 설치는 공유 전역(`~/.opal/`) 쓰기이므로 실행 직전 사용자 승인을 받는다. 설치 뒤 배포된 실행기·스키마·전역 템플릿과, 새 로그인 셸의 `OPAL_TEST_TOOLS_GLOBAL` 해석을 검증한다. 복구는 허브 main에서 같은 설치를 다시 실행한다. | 공통 배포 완료 조건(REQUEST)과 AC-8. 전역 쓰기는 별도 승인 경계다(`opal/core/references/harness/guards.md` §독립 검증 경계). |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. 전역 템플릿·스키마 이관 | opal-task-agent | `opal/templates/test-tools.yaml`, `opal/core/references/test-tools-schema.yaml` | 템플릿 unit·integration api_db 도구에 D-10 `run`·`run_files`·`file_globs`를 추가하고 `check`는 버전 확인으로 둔다. 헤더 주석·Python 예시 블록(`:151-183`)도 같은 형식으로 고친다. 스키마 `tiers.item_fields`에 `run`·`run_files`·`file_globs`를 D-1 의미로 정의하고 `check` 설명을 "설치 확인 전용 — unit 검사로 실행하지 않음"으로 고친다. `global.item_fields.check`는 설치 확인 의미 그대로 둔다. | 없음 | P1 | AC-4, AC-8, C-1, C-2 |
| W-2. 소비자 문서 이관 | opal-task-agent | `opal/skills/op-dev-execute/references/execute-guide.md`, `opal/agents/opal-test-agent/AGENT.md` | execute-guide §4 자가 점검: `unit --scope be`(또는 `fe`) `--changed-files <변경 파일>`로 호출하고 `status: pass`만 통과로 소비한다. `incomplete`는 통과 처리하지 않고 사유(설정 미완료·설치 확인 실패·미실행)와 함께 블로커로 보고, `fail`은 수정 루프 대상이라고 적는다. 계약 원문은 test-tool README를 가리키고 상태값을 복제하지 않는다. opal-test-agent red mode 절차 2에 "실행 명령은 도구 항목의 `run`, `check`는 설치 확인"을 한 문장으로 더한다. | 없음 | P1 | AC-1, AC-4, C-4 |
| W-3. unit 실행 계약 구현 | opal-task-agent | `opal/tools/test-tool/lib/runner.py`, `opal/tools/test-tool/lib/resolver.py`, `opal/tools/test-tool/test_tool.py`, `opal/tools/test-tool/tests/test_test_tool.py`, `opal/tools/test-tool/tests/fixtures/unit-real/`, `opal/tools/test-tool/README.md` | runner: D-2~D-5·D-7에 따라 `run_unit_layers(tiers_data, scope, project_root, env, changed_files)`를 다시 쓰고 상태·사유 선언 목록을 모듈 상수로 둔다. resolver: D-10 추론 명령과 D-7 `source_path`를 넣는다. CLI: `cmd_unit`이 `--changed-files`를 넘기고 `cwd`를 절대 경로로 기록하며 D-6 exit·오류 코드로 대응시킨다. `ERROR_CODES`에 `unit_incomplete`를 더한다. 테스트: 구형 TestUnit 픽스처(`run` 없이 `check`에 실제 명령)를 `run` 형식으로 옮겨 기존 stop-on-fail·계층 순서·단발 실행 단언을 유지한다. 새 계약의 공개 CLI 테스트는 TEST-SCENARIO `구현 전 RED` 행대로 `opal-test-agent`가 별도 파일에 먼저 작성하며, 이 W는 그 파일을 수정하지 않고 통과시킨다(RED 계약 약화 금지). `fixtures/unit-real/`: 추론 경로용 Python 사례(pyproject.toml만, 정상 / lint 위반 / 타입 위반 / 테스트 실패)와 TS 사례(package.json·eslint 설정·tsconfig, 정상 / lint 위반 / 타입 위반 / 테스트 실패). README `unit` 절을 D-8 원문으로 다시 쓰고 구형 설정 이관 절차(D-9)를 더한다. | W-1 | P2 | AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, C-2, C-3, C-4, C-5, C-6, C-7 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. 실제 도구 가용성 — Python 추론 경로의 mypy가 설치돼 있지 않다(작업본에서 `command -v mypy` 결과 없음). TS 도구는 작업본 `dashboard/frontend`에 의존성이 설치되지 않았다(registry `pending_setup`에 `npm ci` 대기). | AC-6 실제 도구 정상·위반 관측 | mypy·eslint·tsc·vitest 실측을 못 하면 AC-6을 충족할 수 없다 | TEST에서 mypy는 태스크 임시 디렉터리의 격리 venv(`uv venv` + `uv pip install mypy`)로, TS 도구는 작업본 `dashboard/frontend`의 `npm ci` 뒤 그 `node_modules`로 공급하고 버전을 기록한다. 공급에 실패하면 통과로 보고하지 않고 BLOCKED로 올린다. |
| H-2. check 사전 실행 비용과 의미 — 계층마다 `check`를 먼저 실행하면 `npx … --version`이 호출당 수백 ms~수 초를 더한다. `check`가 느리거나 네트워크를 타면 설치 확인 실패로 오분류될 수 있다. | D-2 ② 설치 확인 실패 구분 | 자가 점검 시간 증가, 오프라인 npx 설치 확인 실패 | 실측 사례에서 check 소요를 계층 응답으로 관측한다. npx 도구는 로컬 설치가 있으면 네트워크 없이 끝나는지 TS 실측에서 확인한다. 설치 확인 실패는 검사 실패와 다른 상태로만 남아 수정 루프를 오도하지 않는다. |
| H-3. 공유 전역 배포 — 작업본에서 정식 설치를 하면 병합 전 코드가 같은 기계의 다른 세션에 배포된다. | AC-8 배포본 검증, 다른 세션의 `unit` 동작 | 다른 작업이 구형 설정으로 `unit`을 부르면 `incomplete`로 바뀐다 | D-11대로 설치 직전 사용자 승인을 받는다. 전역 템플릿이 같은 설치로 `run`을 갖게 되므로 전역 경로 사용자는 실제 검사로 넘어간다. 문제 시 허브 main에서 재설치해 복구한다. |

## Release and recovery

- 적용 순서: `opal-test-agent` red mode가 RED 테스트 작성·실패 기록·`scenario-lock`(W-1 템플릿 단언 포함이라 구현 전 수행) → P1(W-1, W-2 병렬 — 변경 파일 겹침 없음) → P2(W-3 GREEN) → TEST(소스 회귀·실측) → 사용자 승인 후 정식 설치 → 배포본 검증.
- 검증 범위: 결정론 — 공개 CLI 회귀(`opal/tools/test-tool/tests/test_test_tool.py`)와 test-tool 전체 회귀. 실제 연동 — `fixtures/unit-real/` 사례에 실제 ruff·mypy·pytest·eslint·tsc·vitest를 실행해 정상 `pass`·위반 `fail`을 관측하고 도구 버전과 출력을 태스크 `evidence/`에 보존한다. 배포 — 설치 뒤 `~/.opal/tools/test-tool/run.sh`로 `resolve`(전역 출처 경로)·`unit`(실측 사례)을 실행하고, `~/.opal/templates/test-tools.yaml`·`~/.opal/references/test-tools-schema.yaml`의 `run` 필드, 새 로그인 셸(`zsh -lic`)의 `OPAL_TEST_TOOLS_GLOBAL` 값을 확인한다.
- 실패 시: 설치 전에는 작업본 브랜치에서 보정 커밋으로 복구한다. 설치 후 문제가 생기면 허브 main 체크아웃에서 `scripts/install-mac.sh` 메뉴 1을 다시 실행해 이전 배포본으로 되돌린다.
