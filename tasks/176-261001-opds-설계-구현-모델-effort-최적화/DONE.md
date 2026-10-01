# DONE: 설계·구현 모델·effort 최적화 — opst 변형 측정과 적용

## 결과

opst가 설계 주체와 구현 에이전트의 model·effort를 변형마다 따로 지정해 같은 조건에서 비교하게 만들고, 현행과 후보 3개를 시나리오 2개로 측정했다. 측정 결과 어느 후보도 두 시나리오에서 일관된 속도·비용 이득을 보이지 않아 캡틴이 **현행(설계·구현 모두 sonnet 5.5, effort 미선언)을 유지**하기로 결정했다. 따라서 에이전트 정의와 설정 시드는 바뀌지 않았다. 시나리오 11건은 모두 PASS다.

**달라진 것**

- **변형 설정 지정(AC-1).** `--variant "//opds design=opus/high impl=sonnet/low"`처럼 변형 끝에 `design=<model>[/<effort>]`·`impl=<model>[/<effort>]`를 붙인다. `design`은 세션의 `claude -p --model/--effort`, `impl`은 격리 저장소 `.claude/agents/`의 구현 에이전트 3종(`opal-task-agent`·`opal-be-agent`·`opal-fe-agent`) 사본 frontmatter로 적용한다. 판정 에이전트 사본은 만들지 않고 세션에 `CLAUDE_CODE_SUBAGENT_MODEL`을 넘기지 않는다. 지정값과 적용 결과(세션 `modelUsage` 모델, 덮어쓴 정의 sha256)가 `run.json`의 `settings`에 남는다.
- **FW 버전 일치(AC-2).** 비교 묶음의 `framework` 지문이 하나가 아니면 보고서가 `비교 무효 — FW 버전 상이`를 표시하고 품질 하한 판정을 내지 않는다.
- **비교 보고(AC-3).** 변형 비교표가 지표마다 `평균 (최소~최대)`를 보이고, 신규 지표 `test_fix_iterations`(TEST 수정 반복)와 후보별 품질 하한 판정(`하한 충족`/`하한 미충족(결정 대상 아님)`)을 싣는다. `--max-parallel N`으로 동시 세션 수를 제한할 수 있다.
- **설계 주체 모델 레벨(AC-4 준비).** `launcher.builderModelLevel.<에이전트|provider>`(`light|standard|advanced`)로 worktree 세션의 모델 레벨을 고를 수 있다. 미설정은 `standard`로 이전과 같다. 이 설정은 아직 사용하지 않는다.

**유지한 것:** 판정 에이전트 4종(evaluator·test·convention-checker·security-checker)과 구현 에이전트 3종의 정의, 설계 게이트·TEST 판정 기준, 기존 시나리오와 숨은 인수 테스트, 단일 변형 실행 동작.

## 측정 결과

세션 16개(현행 + 후보 3 × 시나리오 2 × 반복 2), 비용 $198.5, 약 2.8시간으로 승인 상한($240·3시간) 안이다. 후보는 C1(설계 opus/high, 구현 sonnet/low), C2(설계 opus/high, 구현 sonnet/medium), C3(설계 opus/medium, 구현 haiku/medium)다. 각 칸은 평균이다.

| 시나리오 | 지표 | 현행 | C1 | C2 | C3 |
|---|---|---|---|---|---|
| stockctl | 시간(분) | 22.6 (18.4~26.7) | 20.1 (19.7~20.5) | 22.7 (21.8~23.5) | 32.4 (27.7~37.1) |
| stockctl | 비용($) | 10.7 | 11.2 | 11.9 | 12.0 |
| stockctl | 숨은 테스트 | 100% | 100% | 100% | 100% |
| todo-crud | 시간(분) | 24.5 (23.3~25.6) | 30.3 (30.0~30.6) | 34.6 (26.4~42.8) | 33.4 (29.2~37.6) |
| todo-crud | 비용($) | 11.5 | 14.5 | 14.7 | 13.0 |
| todo-crud | 숨은 테스트 | 100% | 100% | 100% | 100% |

TEST 수정 반복은 전 실행 0, 설계 게이트 반복은 전 실행 1이다. 후보 3개 모두 품질 하한(숨은 테스트 통과율)을 충족했지만 속도·비용 이득은 확인되지 않았다. stockctl에서 C1이 약 11% 빨랐으나 현행의 편차 안이다. C3(haiku)는 두 시나리오 모두 느렸다. 기록은 `skill-tests/` 아래 두 폴더(`record.json`·`REPORT.md`·`report.html`)에 있다.

## 변경 파일

- `opal/skills/opal-skill-tester/scripts/skill_tester.py`
- `opal/skills/opal-skill-tester/scripts/report_html.py`
- `opal/skills/opal-skill-tester/tests/test_task176_variant_settings.py`
- `opal/skills/opal-skill-tester/SKILL.md`
- `opal/skills/opal-skill-tester/README.md`
- `opal/skills/opal-skill-tester/references/metrics.md`
- `opal/tools/worktree-launcher/worktree_launcher/settings.py`
- `opal/tools/worktree-launcher/tests/test_settings.py`
- `opal/tools/worktree-launcher/README.md`
- `opal/core/references/harness/worktree.md`
- 태스크 산출물: `tasks/176-261001-opds-설계-구현-모델-effort-최적화/` 아래 PLAN.md·TEST-SCENARIO.md·AGENTIC-LOG.md·run/·skill-tests/·GC-CONVENTION 보고서

## 검증

- 시나리오 11건 PASS(실패·BLOCKED 0). RED 6건(S-1~S-6)은 구현 전에 실제 실패를 확인하고 잠갔다.
- 회귀 `pytest opal/tools/worktree-launcher/tests opal/skills/opal-skill-tester/tests`: 226 passed, 4 skipped.
- 설계 게이트 1회차 pass(설계 4축 PASS, 시나리오 3축 2/2/2).
- 컨벤션 진단: High 1건(신규 테스트 파일 @header `exports` 공란)을 고쳐 `convention-precheck` findings 0건으로 통과.
- 실호출 프로브: 모의 저장소의 덮어쓴 구현 에이전트 정의(`haiku`)가 설치본보다 우선해 서브에이전트가 `claude-haiku-4-5`로 실행됨을 확인했다. 디스패치에서 `model: opus`를 지정하면 정의의 `haiku`보다 우선해 서브에이전트가 opus로 실행됨도 확인했다.

## 미충족·한계

- **AC-4 "새 worktree 태스크에서 실제로 그 설정으로 실행"은 값 변경이 없어 검증 대상이 아니다.** S-11은 소스 launcher로 대체 검증했다: `builderModelLevel` 미설정이면 `--model sonnet`, `advanced`면 `--model opus`, `builderEffort`와 함께면 `--model opus --effort high` 순서로 명령이 만들어진다. 새 worktree 세션을 실제로 띄워 확인하지는 않았다.
- **install 하지 않았다.** 배포된 `~/.opal`의 launcher에는 `builderModelLevel`이 없다. merge 후 install 때 반영된다.
- **측정 중 배포 FW가 바뀌었다(C-4).** stockctl 8개는 `main+19da06`, todo-crud 8개는 `v0.7.3-72-gbb257506+9c962d`다. 이 세션은 측정 중 install을 하지 않았고 외부 재설치로 추정한다. 각 시나리오 묶음 안에서는 지문이 일치해 시나리오별 비교는 유효하지만, 두 시나리오를 합친 결론은 내지 않았다.
- **todo-crud는 현행도 합격하지 못한다.** 기준 2건을 포함해 8건 모두 `checkpoint_commits`(도구 체크포인트 커밋 0건)에서 불충족이다. 설정과 무관한 기존 문제로 보이며 원인은 미규명이다. 그래서 이 시나리오의 품질 하한 판정은 "equally failing 기준 대비"라 정보량이 낮다. 후보 쪽에는 추가 불충족이 있었다(C2 1건 미완료, C3 1건 state_valid·run-log 적체).
- **첫 todo-crud 측정 8건은 무효 처리했다.** 사용량 한도(`api_error`, 토큰·비용 0)로 모델 호출 전에 중단되어 기록을 삭제하고 한도 리셋 후 재실행했다.
- **표본이 작다.** 반복 2회로는 우연과 실제 차이를 구분하기 어렵다.
- **effort 적용은 직접 관찰하지 못했다.** `--effort` 수용은 확인했지만, 구현 에이전트 frontmatter `effort`가 서브에이전트에 실제 반영되는지는 `modelUsage`로 볼 수 없다.
- **과정 실수.** `test.pm_gate`를 컨벤션 진단 완료 전에 먼저 mark했다(AGENTIC-LOG #13). 이후 진단·수정·재검사로 통과를 확인했다.

## 개선 후보 (후속)

모델·effort를 조정하는 지점은 현재 7곳(레벨↔모델 매핑, 에이전트 frontmatter, 설계 주체 기동 설정, 파일럿 SKILL.md 디스패치 지시, `agents.md`, opst 변형 토큰, `opal-agent` CLI)이다. 계속 튜닝하려면 다음이 필요하다.

- **A. effort 매핑 층.** 모델은 `setting.json`의 `models`에서 한 줄로 바꾸지만 effort는 에이전트 frontmatter 16개와 `builderEffort`에 흩어져 있다. 에이전트→effort 매핑 블록을 설정에 두고 재배포 없이 조정하게 한다(install 어댑터까지 영향).
- **B. 우선순위 문서화.** 디스패치 `model` 지정이 에이전트 frontmatter보다 우선함을 실측으로 확인했다. 같은 에이전트를 SKILL.md·`agents.md`·frontmatter가 각각 다르게 말할 수 있으므로 SSOT 하나를 정하고 우선순위를 문서화한다. effort 우선순위는 미확인이다.
- **C. 측정 환경.** 측정 시작 시 FW 지문을 고정하고 실행 중 바뀌면 중단하게 한다. todo-crud가 현행에서도 `checkpoint_commits`로 실패하는 원인을 규명한다. 이전 태스크(172)의 `test-cycle.md` 실호출 절이 `opal-agent` 경유를 요구하는 것과 opst 실행기가 raw `claude -p`를 쓰는 점도 정리한다.
- `launcher._help`와 `setting.default.json`에 `builderEffort`·`builderModelLevel`이 문서화되어 있지 않다. 사용법은 launcher README에만 있다.
