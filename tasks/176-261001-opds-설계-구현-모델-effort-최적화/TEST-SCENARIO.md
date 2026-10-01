---
template: sdlc-v2
---
# TEST-SCENARIO: 설계·구현 모델·effort 최적화 — opst 변형 측정과 적용

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: 로컬 macOS, Python 3 `pytest`. S-1~S-6은 가짜 `claude` 실행기(인자·환경을 파일에 기록하고 고정 JSON을 반환하는 스크립트)와 임시 저장소만 쓰며 실제 모델을 호출하지 않는다. S-9~S-11은 install 후 설치본(`~/.opal`, `~/.claude/agents/`)과 실제 `claude` CLI를 쓴다.
- 공통 데이터: 비교 묶음 fixture(변형 2개 × 반복 2의 `run.json`·`metrics`), FW 지문이 같은 묶음과 다른 묶음 각 1개.
- 대역 사용과 한계: S-1~S-5에서 `claude` CLI를 가짜 실행기로 대체한다. 한계: 프로젝트 레벨 에이전트 정의가 실제 서브에이전트에 적용되는지(H-1)와 `--effort` 수용(H-2)은 대역으로 증명되지 않는다. S-9가 실제 CLI로 확인한다.
- 실행 조건: 자동 실행. S-10은 W-6 측정이 끝난 뒤, S-11은 W-7 반영과 install 뒤에 실행한다. W-6의 측정 상한 승인은 캡틴 확인이 필요한 사용자 협업 조건이다.
- 병렬 그룹: 선언 없음(순차)

## Scenarios

| ID | 유형 | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|---|
| S-1 | unit | AC-1 | 변형 문자열 `//opds design=opus/high impl=sonnet/low`, `//opds design=opus`, `//opds`, `//opds design=`, `//opds impl=a/b/c` | 변형 파싱 함수에 각각 입력 | 앞 둘은 Pilot 커맨드 `//opds`와 `design`·`impl`(모델, effort 또는 없음)로 분해된다. 토큰이 없으면 설정이 비어 있다(현행 동작). 빈 값·슬래시 2개 이상은 `variant_setting_invalid` 오류로 거부되고 `PROFILES` 미등록 오류와 구분된다. 토큰을 뗀 Pilot 커맨드가 `PROFILES`에서 조회된다 | `pytest opal/skills/opal-skill-tester/tests/test_task176_variant_settings.py` | 구현 전 RED |
| S-2 | integration | AC-1, C-1 | 임시 시나리오·기반 저장소, 가짜 `claude`(argv·env·cwd 기록, 서브에이전트 모델 사용량 JSON 반환), 설치 정의를 흉내 낸 에이전트 정의 디렉터리, 부모 환경에 `CLAUDE_CODE_SUBAGENT_MODEL` 설정 | `design=opus/high impl=sonnet/low` 변형으로 `run_scenario` 실행 | 가짜 `claude` argv에 `--model opus`와 `--effort high`가 있고 환경에 `CLAUDE_CODE_SUBAGENT_MODEL`이 없다. 모의 저장소 `.claude/agents/`에는 `opal-task-agent`·`opal-be-agent`·`opal-fe-agent` 사본만 있고 각 frontmatter가 `model: sonnet`·`effort: low`이며 본문은 원본과 같다. `opal-evaluator-agent`·`opal-test-agent`·`opal-convention-checker`·`opal-security-checker` 사본은 없다. 토큰이 없는 변형은 `--model`·`--effort`와 `.claude/agents/`가 모두 없다. `run.json`에 `settings.declared`와 `settings.applied`(모델 목록, 덮어쓴 정의의 sha256)가 있다 | 같은 pytest 파일, 가짜 `claude` 실행기 | 구현 전 RED |
| S-3 | unit | AC-2, AC-3, C-2 | FW 지문이 모두 같은 묶음, 지문이 다른 실행이 섞인 묶음 | `write_report`로 각각 보고서 생성 | 지문이 같으면 변형별 `품질 하한` 행이 나온다. 다르면 보고서가 `비교 무효 — FW 버전 상이`를 표시하고 서로 다른 지문을 나열하며 품질 하한 판정과 우열 표시를 내지 않는다. 단일 실행·지문 일치 묶음의 기존 출력 항목은 유지된다 | 같은 pytest 파일, fixture 묶음 | 구현 전 RED |
| S-4 | unit | AC-3, C-2, H-4 | 현행(hidden 1.0, 준수 2/2 합격)과 후보 A(hidden 1.0, 2/2)·후보 B(hidden 0.75 한 번)·후보 C(준수 1/2) fixture, `fix 작업 (1/3)` 행이 있는 `state.json` | `write_report`와 `test_fix_iterations` 수집 | 후보 A는 `하한 충족`, B와 C는 `하한 미충족(결정 대상 아님)`. 비교표에 `wall_min`·`cost_usd`·`test_fix_iterations`가 변형별 평균과 최소~최대로 나온다. `fix 작업 (N/3)` 행 수가 `test_fix_iterations`와 같다 | 같은 pytest 파일 | 구현 전 RED |
| S-5 | unit | H-3 | 변형 2개 × 반복 2의 세션 4개, `--max-parallel 2`, 가짜 `claude`가 시작·종료 시각을 기록 | `run_scenario` 실행 | 동시에 실행된 세션이 2개를 넘지 않고 첫 배치가 서로 다른 변형을 포함한다. `--max-parallel`을 주지 않으면 4개가 동시에 시작한다(기존 동작) | 같은 pytest 파일 | 구현 전 RED |
| S-6 | unit | AC-4, C-5 | `models.claude`의 light·standard·advanced 셀, `launcher.builderModelLevel` 미설정·`{"claude":"advanced"}`·`{"claude":"bogus"}`·`inherit` 셀·에이전트 키와 provider 키 동시 지정·`advanced` 셀 없음 | `resolve_builder_model`과 `resolve_command` 호출 | 미설정과 잘못된 레벨은 `standard` 셀을 주입한다(현행과 같음). `advanced`는 advanced 셀을 `--model`로 주입한다. 에이전트 키가 provider 키를 이긴다. 셀이 `inherit`면 주입하지 않는다. 필요한 셀이 없으면 `builder_model_unresolved` 오류다. `builderEffort`와 함께 쓰면 `--model <값> --effort <값>` 순서로 들어간다. 로컬 `setting.local.json`이 전역을 에이전트 키 단위로 덮는다 | `pytest opal/tools/worktree-launcher/tests/test_settings.py` | 구현 전 RED |
| S-7 | regression | AC-1, AC-4, C-1 | 설정 키·변형 토큰을 쓰지 않는 기존 호출 | launcher `test_cli.py`와 opst `test_skill_tester_todo_crud.py`·`test_skill_tester_oppb.py`·`test_task164_registry_meta.py` 실행 | 모두 통과하고 기존 기대 출력이 바뀌지 않는다 | `pytest opal/tools/worktree-launcher/tests opal/skills/opal-skill-tester/tests` | 구현 후 |
| S-8 | check | C-1, C-5 | 구현 완료 변경 목록 | `git diff --name-only`를 `opal/agents/opal-evaluator-agent/AGENT.md`·`opal/agents/opal-test-agent/AGENT.md`·`opal/agents/opal-convention-checker/AGENT.md`·`opal/agents/opal-security-checker/AGENT.md`와 대조 | 판정 에이전트 4개 정의가 변경 목록에 없다. 구현 에이전트 3개 정의는 W-7 이전에는 변경 목록에 없다 | `git diff --name-only <기준 커밋>` | 구현 후 |
| S-9 | integration | AC-1, H-1, H-2 | install로 배포한 설치본, 격리 임시 저장소에 `.claude/agents/opal-task-agent.md`(`model: haiku`, `effort: low`)를 덮어 둔 상태 | `claude -p --model sonnet --effort low`로 `opal-task-agent`에 한 줄 응답 작업 디스패치를 지시하는 세션을 한 번 실행 [실호출 1회, AC-1] | 세션 JSON `modelUsage`에 서브에이전트 모델 `haiku` 계열 사용량이 있어 프로젝트 정의가 설치 정의보다 우선함이 확인되고, `--effort`가 오류 없이 수용된다. 확인되지 않으면 결과를 `blocked`로 기록하고 W-6을 시작하지 않는다 | 실제 `claude` CLI, 설치본 `~/.opal`(`opal-agent` 래퍼가 있으면 래퍼 경유) | 설치 후 |
| S-10 | check | AC-2, AC-3, C-3, C-4 | W-6 측정 완료 후 opst가 `tasks/`에 남긴 비교 기록의 `record.json`·`REPORT.md`·`report.html`, 캡틴 승인 기록 | 기록을 읽어 항목 확인 | 모든 실행의 `framework` 지문이 하나다. 후보는 3개 이하, 시나리오는 2개 이하, 총 세션이 승인된 상한(16개) 이내다. 승인 기록(`AGENTIC-LOG.md` 또는 `STATE.md` 의사결정 로그)이 첫 실행 시각보다 앞선다. 보고서에 변형별 설정(선언·적용), 숨은 테스트 통과율, 준수 지표, 소요 시간, 비용, TEST 수정 반복, 반복 간 편차, 후보별 품질 하한 판정이 모두 있다 | 기록 파일 읽기와 `jq`·grep | 설치 후 |
| S-11 | e2e | AC-4, C-5 | 캡틴이 결정한 값이 W-7로 반영되고 install이 끝난 상태, 새 worktree 태스크 기동 설정 | 설치된 `~/.claude/agents/opal-{task,be,fe}-agent.md` frontmatter를 읽고, 설치된 launcher로 `resolve_command`를 호출해 기동 명령을 얻고, 새 worktree 태스크를 기동하면 뜨는 세션이 결정한 모델·effort인지 확인 | 세 에이전트 정의의 `model`·`effort`가 결정값과 같다. 기동 명령에 결정한 설계 주체의 `--model`·`--effort`가 들어 있다. 판정 에이전트 정의는 이전과 같다. 캡틴이 값을 정하지 않아 W-7을 수행하지 않으면 이 시나리오는 실행하지 않고 W-7 미수행 사실을 보고한다 | 설치본 파일 읽기, `worktree-launcher` 모듈 호출, 새 worktree 세션 기동 | 설치 후 |
