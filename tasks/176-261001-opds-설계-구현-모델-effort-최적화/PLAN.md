---
template: sdlc-v2
---
# PLAN: 설계·구현 모델·effort 최적화 — opst 변형 측정과 적용

> 입력: [TASK.md](TASK.md)

## Approach

세 단계로 나눈다. (1) opst가 변형마다 설계 주체와 구현 에이전트의 model·effort를 따로 지정·기록·비교하게 만들고, (2) 현행과 후보 3개를 같은 배포 버전에서 측정해 하나의 비교 보고서로 캡틴에게 올리고, (3) 캡틴이 결정한 값을 에이전트 정의와 worktree 세션 기동 설정에 반영한다.

opst는 격리 저장소에서 `claude -p`로 Pilot 세션을 직접 띄운다. 이 세션이 worktree 세션 PM(설계 주체)을 대신하므로 설계 설정은 `claude -p`의 `--model`·`--effort`로 주고, 구현 에이전트 설정은 모의 저장소의 프로젝트 레벨 에이전트 정의(`.claude/agents/`)로 덮어쓴다. 판정 에이전트 정의는 건드리지 않아 C-1이 구조적으로 지켜진다. 실제 worktree 태스크의 설계 주체 모델은 launcher가 `models.<provider>.standard`로 고정해 두고 있어(effort는 `builderEffort`로 이미 설정 가능), 모델 레벨을 고르는 설정 키를 추가한다.

code-scan 결과(`code-scan scan --json`, 변경 대상 코드 파일):

| 파일 | domain | layer | depends | exports |
|---|---|---|---|---|
| `opal/skills/opal-skill-tester/scripts/skill_tester.py` | opal-skill-tester | util | 없음 | `main`, `load_scenarios`, `validate_scenario`, `run_scenario`, `collect_run`, `judge_run`, `write_report`, `record_results`, `collect_history` |
| `opal/skills/opal-skill-tester/scripts/report_html.py` | opal-skill-tester | util | 없음 | `render_report`, `axes_for` |
| `opal/tools/worktree-launcher/worktree_launcher/settings.py` | opal-workspace | util | `opal/core/setting.default.json`(launcher 블록 기본값 SSOT) | `load_launcher_settings`, `resolve_builder_model`, `resolve_builder_effort`, `BUILDER_MODEL_LEVEL`, `BUILDER_EFFORT_KEY` 외 |

`settings.py`는 `load_launcher_settings`가 레이어 병합 시 알려진 키만 받는다(`_apply_layer`가 `builderEffort`만 처리). 새 키는 이 병합 함수와 초기 `resolved`에 함께 추가해야 전역·로컬 설정에서 읽힌다. exports 변경은 `resolve_builder_model`의 반환 계약(`(model, error)`)을 유지하는 범위에서만 한다.

## Findings

### 직접 변경
- opst 실행기 `opal/skills/opal-skill-tester/scripts/skill_tester.py`: 변형 문자열의 `design=`·`impl=` 토큰 파싱, `claude -p` 플래그 주입, 구현 에이전트 덮어쓰기 파일 생성, 적용 설정 기록, 병렬 상한, TEST 수정 반복 수집, FW 버전 일치 검사, 비교 보고.
- opst 대시보드 `opal/skills/opal-skill-tester/scripts/report_html.py`: 변형 설정·편차·품질 하한 판정·비교 무효 표시.
- launcher `opal/tools/worktree-launcher/worktree_launcher/settings.py`: builder 모델 레벨 설정 키(`launcher.builderModelLevel`) 해석.
- 구현 에이전트 정의 `opal/agents/opal-task-agent/AGENT.md`, `opal/agents/opal-be-agent/AGENT.md`, `opal/agents/opal-fe-agent/AGENT.md`: 캡틴 결정값의 model·effort(W-7).
- 새 단위 테스트 `opal/skills/opal-skill-tester/tests/test_task176_variant_settings.py`.

### 회귀 확인
- `opal/tools/worktree-launcher/tests/test_cli.py`: 기존 builder 모델·effort 주입 동작이 설정 키 미지정 시 그대로여야 한다.
- `opal/agents/opal-evaluator-agent/AGENT.md`: 판정 에이전트 effort 선언(172 확정값)이 바뀌지 않아야 한다.
- `opal/skills/opal-skill-tester/tests/test_skill_tester_todo_crud.py`: 기존 단일 변형 실행·판정 경로.
- `scripts/install-mac.sh`: 에이전트 effort 어댑터가 구현 에이전트 3종의 `effort:`를 Claude `effort` 키로 내보내는지(코드 변경 없음, 배포 산출물만 확인).

### 문서 갱신
- `opal/skills/opal-skill-tester/SKILL.md`, `opal/skills/opal-skill-tester/references/metrics.md`, `opal/skills/opal-skill-tester/README.md`: 변형 설정 문법, 신규 지표, 비교 무효·품질 하한 규칙.
- `opal/tools/worktree-launcher/README.md`, `opal/core/references/harness/worktree.md`: `builderModelLevel` 키와 설계 주체 설정 계약.
- `opal/core/setting.default.json`: 캡틴이 결정한 설계 주체 레벨·effort의 기본 시드(W-7).

### 미확인 가정
H-1, H-2, H-3 참조.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| 변형 설정 문법 | `--variant "//opds design=opus/high impl=sonnet/low"`. `design=`·`impl=` 토큰은 `<model>[/<effort>]`이며 둘 다 선택이다. 토큰은 Pilot 커맨드 판정(`PROFILES`)과 발화 `{variant}` 치환 전에 떼어 낸다. 변형 식별·slug·이력은 토큰을 포함한 전체 문자열을 쓴다 | 기존 `--variant` 반복·`record`·이력 탭 구조를 그대로 재사용한다. 새 인자 체계를 만들지 않는다 |
| 설계 주체 적용 | `design=`은 `claude -p`에 `--model <model>`, effort가 있으면 `--effort <effort>`로 전달한다. 미지정이면 플래그를 넣지 않아 현행 그대로다 | opst 세션이 worktree 세션 PM과 같은 역할이다. 실제 worktree 기동은 launcher가 같은 CLI 플래그를 쓴다(`opal/tools/worktree-launcher/README.md` §builder effort 기동 시점 주입) |
| 구현 에이전트 적용 | `impl=`은 모의 저장소 `.claude/agents/`에 `opal-task-agent`·`opal-be-agent`·`opal-fe-agent` 정의 사본을 만들어 frontmatter `model`·`effort`만 바꾼다. 원본은 설치된 정의다. 판정 에이전트는 사본을 만들지 않는다. 실행기는 `CLAUDE_CODE_SUBAGENT_MODEL` 환경변수를 세션에 넘기지 않는다 | 서브에이전트 모델 전역 환경변수는 판정 에이전트까지 바꿔 C-1을 깬다. 프로젝트 레벨 정의는 변형별 격리 저장소 안에서만 유효하다 |
| 적용 설정 기록 | 실행마다 `run.json`에 `settings.declared`(변형이 지정한 값)와 `settings.applied`(세션 JSON `modelUsage`의 모델 목록, 덮어쓴 에이전트 정의의 sha256)를 남긴다 | AC-1의 "실제 적용된 설정 기록". 선언만 기록하면 적용 실패를 놓친다 |
| FW 버전 일치 | 실행마다 기존 `framework` 지문(설치 VERSION + state-tool·Pilot SKILL sha)을 기록하고, 한 비교 묶음의 지문이 하나가 아니면 보고서가 `비교 무효 — FW 버전 상이`를 표시하고 품질 판정을 내지 않는다 | AC-2. 지문은 이미 수집되므로 비교 규칙만 더한다 |
| TEST 수정 반복 | `test_fix_iterations` = `state.json` 행 중 `item`이 `fix 작업`으로 시작하는 수 | 쇼트 Pilot이 TEST 실패 시 `fix 작업 (N/3)` 행을 동적 추가한다(`opal/skills/opal-pilot-dev-short/SKILL.md` §FAIL 시) |
| 반복 간 편차 | 변형 비교표의 수치 지표마다 평균과 함께 최소~최대를 표시한다 | N이 작아 평균만으로 결론을 내리지 못한다(`references/metrics.md` 머리말) |
| 품질 하한 판정 | 후보는 현행 대비 `hidden_pass_rate` 평균이 낮지 않고 준수 합격 수 비율이 낮지 않을 때만 `하한 충족`이다. 미충족 후보는 결정 대상에서 제외 표시한다 | C-2 |
| 병렬 상한 | `run --max-parallel N`(기본 전체 병렬, 기존 동작 유지)으로 동시 세션 수를 제한한다. 한 배치 안의 세션 순서는 변형을 교차 배치해 시간대 편향을 줄인다 | 16 세션을 한꺼번에 띄우면 계정 호출 한도·머신 부하가 측정에 섞인다 |
| builder 모델 레벨 키 | `launcher.builderModelLevel.<에이전트\|provider>`가 `light\|standard\|advanced`면 해당 레벨의 `models.<provider>.<레벨>` 셀을 builder 모델로 주입한다. 미설정은 `standard`로 현행과 같다. 해석 규칙(에이전트 키가 provider 키를 이김, 셀 부재 시 `builder_model_unresolved`)은 기존 모델 주입 계약을 따른다 | 플랫폼별 모델 값 변환을 `models` 매핑과 launcher 설정 계층에만 둔다(C-5). effort는 기존 `builderEffort`를 그대로 쓴다 |
| 측정 상한(C-3) | 후보 3개 + 현행, 시나리오 2개(`function-stockctl-multiloc`, `function-todo-crud`), 반복 2회 → 세션 16개. 동시 8개, 총 비용 상한 $240(시나리오 estimate 상한 × 세션 수), 총 시간 상한 3시간. 상한 초과 예상 시 중단하고 보고한다. 이 값은 측정 실행 전에 캡틴 승인을 받는다 | 시나리오 estimate는 1회 약 $10~15·20~35분이다(`opal/skills/opal-skill-tester/SKILL.md` §실행 비용) |
| 후보 설정(안) | 현행(설계 sonnet 기본, 구현 sonnet 미선언) 대비 C1 설계 `opus/high`·구현 `sonnet/low`, C2 설계 `opus/high`·구현 `sonnet/medium`, C3 설계 `opus/medium`·구현 `haiku/medium`. 최종 후보는 측정 승인 시 캡틴이 확정한다 | 170 측정에서 `xhigh`가 약 6배 느렸으므로 `high` 이하로 한정한다 |
| 적용 시점 | 측정 결과를 보고한 뒤 캡틴이 값을 정하면 W-7이 반영한다. 캡틴이 정하지 않으면 W-7은 수행하지 않고 현행을 유지한다 | C-5 |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. opst 변형 설정 테스트(RED) | opal-task-agent | `opal/skills/opal-skill-tester/tests/test_task176_variant_settings.py` | 변형 토큰 파싱(`design=`·`impl=`, 생략·잘못된 값), `claude -p` 인자 조립, 구현 에이전트 사본 frontmatter 치환과 판정 에이전트 사본 부재, `settings.applied` 기록, FW 지문 불일치 시 비교 무효, 품질 하한 판정, `test_fix_iterations` 집계, `--max-parallel` 배치를 가짜 `claude` 실행기와 임시 저장소로 검증하는 실패 테스트를 먼저 작성한다 | 없음 | P1 | AC-1, AC-2, AC-3, C-1, C-2 |
| W-2. launcher builder 모델 레벨 | opal-task-agent | `opal/tools/worktree-launcher/worktree_launcher/settings.py`, `opal/tools/worktree-launcher/tests/test_settings.py` | `launcher.builderModelLevel` 상수를 추가하고 `load_launcher_settings`의 초기값과 `_apply_layer`(에이전트 키 단위 덮어쓰기, `builderEffort`와 같은 방식)에 반영하며 `resolve_builder_model`이 레벨을 쓰게 한다. 미설정·잘못된 레벨은 `standard`. 에이전트 키가 provider 키를 이긴다. 테스트를 같은 변경에서 추가한다 | 없음 | P1 | AC-4, C-5 |
| W-3. opst 실행기 변형 설정 적용·기록 | opal-task-agent | `opal/skills/opal-skill-tester/scripts/skill_tester.py` | 변형 토큰 파싱, `PROFILES` 판정 전 토큰 제거, `claude -p` 플래그 주입, `.claude/agents/` 구현 에이전트 사본 생성, 세션 환경에서 `CLAUDE_CODE_SUBAGENT_MODEL` 제거, `run.json` `settings.declared/applied` 기록, `test_fix_iterations` 수집, `--max-parallel` 배치 실행, 변형별 FW 지문 비교와 무효 표시, 변형 비교 요약의 최소~최대·품질 하한 판정을 REPORT.md에 추가 | W-1 | P2 | AC-1, AC-2, AC-3, C-1, C-2 |
| W-4. opst 대시보드 비교 표시 | opal-task-agent | `opal/skills/opal-skill-tester/scripts/report_html.py` | 비교 탭에 변형 설정(선언·적용), 지표별 평균·최소~최대, 품질 하한 판정, `비교 무효` 배너를 표시한다. 단일 실행·이력 탭 표시는 그대로 둔다 | W-1 | P2 | AC-2, AC-3 |
| W-5. 문서 갱신 | opal-task-agent | `opal/skills/opal-skill-tester/SKILL.md`, `opal/skills/opal-skill-tester/references/metrics.md`, `opal/skills/opal-skill-tester/README.md`, `opal/tools/worktree-launcher/README.md`, `opal/core/references/harness/worktree.md` | opst 변형 설정 문법·신규 지표(`test_fix_iterations`, 적용 설정)·비교 무효/품질 하한 규칙·`--max-parallel`을 적고, launcher `builderModelLevel` 키와 설계 주체 설정 계약을 적는다. 현재 사실만 쓰고 이력 절을 만들지 않는다 | W-2, W-3, W-4 | P3 | AC-1, AC-2, AC-3, AC-4 |
| W-6. 측정 실행과 비교 보고 | PM(`opal-skill-tester` 실행, 모델 실호출은 `opal-agent`) | `tasks/176-261001-opds-설계-구현-모델-effort-최적화/run/` | 소스를 install해 배포하고(이후 측정이 끝날 때까지 재설치 금지), 소형 프로브로 H-1·H-2를 확인한다. 캡틴에게 후보 확정과 상한을 승인받은 뒤 시나리오별로 현행+후보 3×반복 2를 실행하고 비교 보고서를 캡틴에게 제시한다 | W-5 | P4 | AC-2, AC-3, C-3, C-4 |
| W-7. 결정값 반영 | PM | `opal/agents/opal-task-agent/AGENT.md`, `opal/agents/opal-be-agent/AGENT.md`, `opal/agents/opal-fe-agent/AGENT.md`, `opal/core/setting.default.json` | 캡틴이 정한 구현 model·effort를 3개 에이전트 frontmatter에 선언하고, 설계 주체 레벨·effort를 `launcher.builderModelLevel`·`launcher.builderEffort` 시드로 반영한다. 캡틴 결정이 없으면 수행하지 않는다 | W-6 | P5 | AC-4, C-5 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. 모의 저장소의 `.claude/agents/<name>.md`가 사용자 레벨 설치 정의보다 우선하고 `claude -p`의 서브에이전트 디스패치가 그것을 쓴다 | `impl=` 적용 | 구현 설정이 실제로 안 바뀐 채 측정되어 비교가 무의미해진다 | W-6 첫 단계의 소형 프로브가 `modelUsage`와 서브에이전트 기록으로 적용 여부를 확인하고, 미적용이면 측정을 중단하고 캡틴에게 보고한다. 단위 테스트는 사본 생성까지만 검증한다 |
| H-2. `claude -p`가 `--effort`를 받고 서브에이전트 frontmatter `effort`가 호출 세션 설정을 덮는다 | `design=`·`impl=` effort 적용 | effort 차이가 실제로 반영되지 않는다 | 같은 프로브에서 effort 지정 세션을 실행해 확인한다. 거부되면 effort 없는 모델 변형만 측정하도록 범위를 줄이고 보고한다 |
| H-3. 16 세션을 동시에 돌리면 호출 한도·머신 부하가 시간 지표에 섞인다 | 시간·비용 비교 | 후보 간 차이를 부하 차이로 오판한다 | `--max-parallel 8`과 변형 교차 배치, 시간 지표는 편차와 함께 보고한다 |
| H-4. 반복 2회로는 우연과 차이를 구분하기 어렵다 | 품질 하한·시간 비교 | 잘못된 설정을 확정할 수 있다 | 보고서가 최소~최대와 합격 수를 함께 보이고, 결정은 캡틴이 한다. 결과가 모호하면 후보를 좁혀 재측정을 제안한다 |

## Release and recovery

- 적용 순서: P1(테스트·launcher) → P2(opst 실행기·대시보드) → P3(문서) → 단위 테스트 통과 후 install → P4 측정(이 기간 재설치 금지) → 캡틴 결정 → P5 반영 → install → 새 worktree 태스크 기동 명령 확인.
- 검증 범위: 결정론은 opst 신규 테스트·launcher `test_settings.py`·기존 `test_cli.py`·`test_skill_tester_todo_crud.py` 회귀. 실제 연동은 W-6 프로브와 측정 세션, AC-4는 install 후 생성된 `~/.claude/agents/*.md`의 model·effort와 `worktree-launcher`가 만든 기동 명령을 확인한다.
- 실측 경계: 세션 시작~종료 `wall_min`, `phase_min`의 설계/구현/테스트 구간, 비용은 세션 JSON `cost_usd`, 재작업은 `test_fix_iterations`·`gate_iterations`. 대기 시간은 배치 대기를 제외하고 세션 내부 경과만 센다.
- 실패 시: P5 반영 전에는 에이전트 정의·설정 시드가 바뀌지 않으므로 복구할 것이 없다. P5 후 문제가 생기면 3개 에이전트 frontmatter와 시드 변경을 되돌리고 install로 재배포한다. 측정 중 FW가 바뀐 흔적이 있으면 해당 비교 묶음을 무효로 보고 재측정한다.
