---
template: sdlc-v2
---
# TEST-SCENARIO: 워크트리 전용 터미널 런처 orca 경로 배선

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## 목표

허브 세션이 만든 워크트리에 전용 터미널이 실제로 열리고, 그 터미널의 LLM이 첫 턴을 스스로 시작해 해당 태스크를 이어받으며, 회수 시 터미널이 남지 않는다.

## Setup

- 환경: 허브 `/Volumes/Data/AIStudio/workspace/ai-framework`. 테스트 인터프리터는 `~/.opal/.venv/bin/python -m pytest`로 고정한다(시스템 python3.14는 OPAL 테스트 게이트에서 거부된다).
- 공통 데이터: `opal/tools/ownership-tool/tests/fixtures/launcher/` — W-1이 실물 `orca terminal create|read|close --json` stdout을 캡처해 교체할 fixture 3종. 워크트리 경로 성분만 `{WT}` 플레이스홀더로 치환하고 캡처 일시와 `orca --version`을 함께 기록한다.
- 대역 사용과 한계: fixture는 **캡처 시점 버전의 응답 형태**만 고정한다. 버전 드리프트와 "argv 발화가 TUI에 실제 제출됐는가"는 fixture가 대체하지 못하므로 S-10·S-11 live 경로가 유일한 관문이다(H-2·H-3).
- 실행 조건: S-10·S-11은 `orca`가 PATH에 있고 `OPAL_LIVE_ORCA=1`일 때만 실행되는 opt-in이며, 그 외 환경에서는 skip한다. 나머지는 기본 스위트에서 자동 실행한다.
- 부수 효과 규율: live 경로는 자신이 만든 터미널·워크트리만 생성하고 예외 경로를 포함한 teardown에서 반드시 회수한다. 기존 태스크(`task_142`)와 사용자 터미널은 건드리지 않는다.

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-2, H-1, H-2 | W-1이 캡처한 실물 `create` fixture + 변형 3종(`result` 키 부재 / `worktreeId`에 `::` 없음 / `worktreeId` 뒤쪽이 비절대 경로) | `orca.parse_response()` 호출 | 실물 fixture에서 `adapter_handle`이 `term_` 핸들로, `reported_cwd`가 워크트리 절대경로로 **둘 다 채워진다**. 변형 3종은 값을 지어내지 않고 `reported_cwd=None`(또는 `adapter_handle=None`)을 반환해 launcher가 launch 실패로 판정하게 둔다 | unit — `test_adapter_orca.py` | 구현 전 RED |
| S-2 | AC-2, AC-8 | 실물 `create` fixture, 전송 명령 문자열 고정 | `orca.launch()` 보고 dict 검사 + 소스 정적 검사 | `prompt_receipt_source == "launch_argv"`. `prompt_id`가 전송 명령의 sha256 앞 16자와 일치하고 `submitted_at`이 채워져 `launcher_core.build_prompt_receipt()`가 non-None. **구형 토큰 `PROMPT_SOURCE_SESSIONSTART_CLAIM`·`sessionstart_claim_observation` 잔존 0건**(`worktree_launcher` 패키지 전체 grep) | unit + grep 정적 검사 — `test_adapter_orca.py` | 구현 전 RED |
| S-3 | AC-8 | 어댑터 모듈을 파라미터화한 적합성 스위트 | `test_adapter_conformance.py` 실행 | orca 어댑터가 7개 검사 전건 통과 — (1) 3동사 존재·호출 가능 (2) 보고 dict 공통 필수 키·타입 (3) 실패가 예외가 아닌 `exit_code != 0` dict (4) `fallback_attempted`가 항상 False (5) `launch` argv에 worktree/checkout 생성 서브명령 0건 (6) 성공 보고가 `build_launch_receipt()`·`build_prompt_receipt()` 둘 다 non-None (7) `close` 인자 배타성 | unit — `test_adapter_conformance.py` | 구현 전 RED |
| S-4 | AC-4 | `launcher_core.run()`의 복귀 5경로(`adapter_report_invalid`·`launch_receipt_missing`·`reported_cwd_mismatch`·`prompt_receipt_missing`·`ownership_set_rejected`)를 각각 유발하는 fake adapter. 추가로 `close`가 예외를 던지는 변형과 `adapter_handle` 부재 변형 | 각 경로로 `run()` 호출 후 fake adapter 호출 기록·registry 검사 | **handle이 실재하는 복귀 경로 전건**에서 `adapter.close(handle=…)`가 정확히 1회 호출되고, 상태는 `hub_owned` + `attribution_state` 키 부재 + `generation` 증가로 복귀한다. `adapter_report_invalid`는 보고가 dict가 아니어서 `adapter_handle` 원천 자체가 없으므로 close를 시도하지 않고 `handle_missing`으로 기록한다(대상 추측 금지가 우선한다). `ownership_set_rejected` 경로도 같은 정리 경로를 탄다 — 이 시점엔 터미널이 확실히 살아 있다. `close` 예외·미구현(`AttributeError`)이어도 **복귀는 반드시 수행**되며 실패는 `terminal_close` 필드로만 남는다. `adapter_handle`이 없으면 close를 시도하지 않는다(대상 추측 금지) | unit — `test_launcher_core.py` | 구현 전 RED |
| S-5 | AC-1, AC-3, AC-7, C-3 | `run.sh`와 `cli.py`. 인자 조합: `--adapter` 누락 / `--adapter cmux`(미구현) / `--adapter orca` 정상 / `--command` 미지정 | CLI 3서브명령(`launch`·`read`·`close`) 호출 | `--adapter` 누락과 폐쇄 목록 밖 값은 **오류로 거부**하고 자동 폴백·자동 탐지를 하지 않는다. 정상 경로는 단일 라인 JSON을 stdout에 출력하고 성공 exit 0 / 실패 exit 1. `--command` 미지정 시 `resolve_command()`가 설정에서 명령을 결정한다. `run.sh`에서 `not_implemented` 반환 0건이고 venv·import 가드 2종은 유지된다 | unit — `test_cli.py` | 구현 전 RED |
| S-6 | AC-7, C-9 | 임시 `setting.json`·`setting.local.json` 6조합 — 블록 전체 부재 / 전역만 / 로컬이 `default`만 덮어씀 / 로컬이 `agents.codex`만 교체 / JSON 파싱 실패 / `agents`가 문자열(타입 불일치) | `load_launcher_settings()` + `resolve_command()` 호출 | 블록 부재·파싱 실패·타입 불일치 전건에서 **예외 없이** 기본값(`default="claude"`)으로 폴백한다. `default`를 `codex`로 바꾸면 결정되는 명령이 codex argv로 바뀐다. `agents.<name>`은 이름 단위 통째 교체, 그 위 키는 키 단위 덮어쓰기로 머지된다. `setting.default.json`의 `launcher._help`에 `models` 미설정 중단과의 비대칭 근거 문장이 존재한다 | unit — `test_settings.py` + 문자열 검사 | 구현 전 RED |
| S-7 | AC-6, C-6, H-4, H-5 | 임시 허브+워크트리 registry. 변형 4종 — `execution_ownership.adapter` 미기록 / 기록됨 + close 성공 / 기록됨 + close 실패(비-0 종료) / dirty 워크트리 | `worktree-tool remove` 호출 | adapter 미기록이면 close를 호출하지 않고 **응답 키 집합이 기존과 바이트 동일**하다. 기록 시 close가 3중 가드 통과 직후·`git worktree remove` 직전에 호출되고 `terminals_closed`가 응답에 실린다. close 실패는 회수를 차단하지 않고 `warnings`로만 보고된다. dirty 워크트리는 가드에서 거부되어 스윕에 **도달하지 않는다** | unit — `test_worktree_tool.py` | 구현 전 RED |
| S-8 | AC-9 | registry 메타 4종 — `task_ownership_version` 보유 + `execution_ownership` 부재 / 보유 + `completed_unmerged` / 보유 + `closed` / legacy(version 부재) | `worktree-tool status` 호출 | `execution_ownership`이 없어도 `task_ownership_version`만 있으면 `attribution_state`가 방출된다. 파생 불리언 `completed_unmerged`가 `attribution_state == "completed_unmerged"`와 일치한다. legacy 메타의 출력은 **무변경**이다. 새 필드는 `completed_unmerged` 하나뿐이다 | unit — `test_worktree_tool.py` | 구현 전 RED |
| S-9 | AC-5 | 수정된 `task-process.md`·`worktree.md` | 문서 구조 검사 + PM 직접 Read | `task-process.md`에 스텝 5.5가 신설되고 `worktree-launcher/run.sh launch --adapter orca …` 명령 블록과 비차단 실패 규율을 소유한다. 4.5 `ok: true` 목록에는 5.5를 가리키는 1줄만 있고 명령 블록 중복 0건. merge 경계는 `guards.md`를 가리키는 포인터만 있고 규정 원문 복제 0건. `worktree.md`에 실행 세션 기동·터미널 회수 경계 절이 1개 추가되고 절차 원문은 `task-process.md`를 가리킨다 | deterministic grep + manual read | 구현 후 |
| S-10 | AC-2, AC-8, C-7, H-2 | `orca` PATH 존재 + `OPAL_LIVE_ORCA=1`. 실 워크트리 1개 | live 테스트가 터미널 1개를 만들고 `parse_response()`에 실 stdout을 통과시킨 뒤 `close(handle=…)`로 회수 | 실 응답에서 `adapter_handle`·`reported_cwd`가 둘 다 채워진다. teardown이 예외 경로를 포함해 실행되어 **생성한 터미널 0개 잔존**. `OPAL_LIVE_ORCA` 미설정·orca 부재 환경에서는 skip이며 기본 스위트 실행 시간에 영향을 주지 않는다 | live integration — `test_adapter_orca.py` | 구현 후 |
| S-11 | AC-3, AC-5, H-3, H-6 | `orca` PATH 존재 + `OPAL_LIVE_ORCA=1`. 목업 태스크 번호로 만든 실 워크트리 | (1) `launcher_core.run()` 정상 경로 (2) 실패 주입 경로 (3) `--wt` 태스크 1건 실제 생성부터 회수까지 완주 | (1) `worktree_session_owned`까지 전이하고 registry에 `launch_receipt`·`prompt_receipt`가 **객체로** 기록된다. (2) 실패 주입 시 `hub_owned` 복귀 + `orca terminal list --worktree path:<root>` 결과 **터미널 0개**. (3) 워크트리 터미널에서 LLM이 기동해 **첫 턴이 스스로 시작**되고 해당 태스크의 다음 행을 이어받는다(사람 관측). `worktree-tool remove` 후 터미널 0개. 자동 생성 fallback 탭 유무와 무관하게 (2)·(3)의 0개 판정이 성립한다. 관측 증거(명령·스코프·출력)를 태스크 폴더에 기록한다 | live E2E — `test_integration.py` + PM 실측 | 구현 후 (배포 후) |
| S-12 | AC-10, C-6 | 변경 전 기준선(현행 `worktree-launcher/tests` 15건 통과) | `~/.opal/.venv/bin/python -m pytest opal/tools/worktree-launcher/tests opal/tools/worktree-tool/tests opal/tools/state-tool/tests -q` (스위트별 병렬 실행) | 전건 pass. `--wt` 미사용 경로의 `worktree-tool`·`state-tool` 기존 테스트에 실패·skip 증가 0건 | integration(pytest) | 구현 후 |
| S-13 | AC-8 | `close` 인자 조합 4종 — `handle`만 / `worktree_root`+`all`만 / 둘 다 / 둘 다 아님 | `orca.close()` 호출 및 argv 검사 | `handle`만 → `terminal close --terminal <handle>`. `worktree_root`+`all` → `terminal close --worktree path:<root> --all`. 둘 다·둘 다 아님 → 예외가 아니라 `exit_code != 0` 실패 dict. 두 스코프가 서로의 argv를 만들지 않는다 | unit — `test_adapter_orca.py` | 구현 전 RED |
| S-14 | C-1, C-2, C-4, C-5 | 변경 후 `worktree_launcher` 패키지 + `worktree_tool.py` 전체 | 소스 정적 검사(grep·AST) | (C-1) `adapters/`에 신규 모듈 0건이고 `cmux.py` 부재, `generic.py`·`opal_agent_fallback.py` 내용 무변경. (C-2) 어댑터 모듈에 `class`·`ABC`·상속 선언 0건 — 모듈 함수 seam 유지. (C-4) launcher 패키지에서 `worktree add`·`checkout -b`·`orca worktree create` 호출 문자열 0건. (C-5) launcher 패키지에서 registry 메타 파일에 쓰기(`open(...,'w')`·`write_meta_atomic`) 0건이며 상태 전이는 `ownership-set` subprocess 호출로만 발생 | deterministic grep + AST — `test_adapter_conformance.py` | 구현 후 |
| S-15 | C-8, C-10 | 변경 후 하네스 문서 7종과 `worktree_tool.py` | 문서 grep + `cmd_checkpoint` 호출 | (C-8) `task-process.md`·`worktree.md`의 신설·수정 절에 merge를 워크트리에서 수행한다는 문구 0건이고, merge 경계는 `guards.md` 포인터로만 존재한다. (C-10) `worktree-tool checkpoint`를 `main` 브랜치·허브 루트 대상으로 호출하면 종전대로 `requires_user_approval`(`protected_branch_commit`·`hub_commit`)을 반환한다 — 이번 변경이 이 경계를 건드리지 않았음을 회귀로 고정한다 | deterministic grep + unit — `test_worktree_tool.py` | 구현 후 |

## 커버리지 매핑

| 축 | 매핑 |
|---|---|
| AC | AC-1→S-5 / AC-2→S-1·S-2·S-10 / AC-3→S-5·S-11 / AC-4→S-4 / AC-5→S-9·S-11 / AC-6→S-7 / AC-7→S-5·S-6 / AC-8→S-2·S-3·S-10·S-13 / AC-9→S-8 / AC-10→S-12 |
| C | C-1·C-2·C-4·C-5→S-14 / C-3→S-5 / C-6→S-7·S-12 / C-7→S-10 / C-8·C-10→S-15 / C-9→S-6 |
| H | H-1→S-1 / H-2→S-1·S-10 / H-3→S-11 / H-4→S-7 / H-5→S-7 / H-6→S-11 |
| 목표 달성 | S-11 — 첫 턴 자기시작과 회수 후 터미널 0개를 사람 관측으로 확정 |
| 채택·잔존 | S-2 — 신형 `launch_argv` 채택과 구형 `sessionstart_claim_observation` 잔존 0건을 같은 시나리오에서 검증 |
| 경계·부정 | S-1(파싱 실패) · S-4(복귀 4경로·close 실패) · S-5(어댑터 미지정·미구현) · S-6(설정 파손·타입 불일치) · S-7(adapter 미기록·close 실패·dirty) · S-13(인자 배타성) |

## RED-first 적용

RED 대상은 S-1~S-8·S-13이다. 이 9건은 구현 전에 작성해 실패를 관측한 뒤 `test-tool scenario-red`로 증거를 기록하고, `scenario-lock` 통과 후에만 GREEN 구현을 시작한다. S-9·S-10·S-11·S-12는 구현·배포 후 시점이므로 RED 대상이 아니다.
