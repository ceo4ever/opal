# DONE: PM 직접 수행 모델 — actor 축 신설과 L2 대체

## 결과

파이프라인을 "누가 수행하는가"로 나누는 **actor 축**을 신설하고, 규모(파일 수·변경량)를 근거로 직접 수행을 제한하던 `L2 경량 트랙`을 걷어냈다.

**새로 생긴 것**

- `--pm` actor 옵션 — 모드 축(`--interactive`/`--semi-agentic`/`--agentic`)·워크스페이스 축(`--wt`)과 직교하며 `mode_flag_conflict` 개수 판정에 포함되지 않는다. 규칙 원문은 신규 owner 문서 `harness/actor.md`가 단독 소유하고, `pilot.start` required doc 5번째 항목으로 등재되어 모든 Pilot이 첫 작업 전에 강제 로드한다.
- `//oppm`(`opal-self-pm`) — 종료 조건을 가진 대화형 PM 작업 루프. 쓰기 전 6항목 계약 승인, 완료 전 8영역(기획·설계·프로젝트 문서·CONVENTIONS·SECURITY·brain·memory·code-scan) 전수 판정, 사용자 최종 확인 전 완료 선언 금지를 [MUST]로 규정한다.
- `self-pm-tool` — 8필드 경량 실행 기록 CLI(`init`/`update`/`show`). `state.json`·`test-scenario.json`·`backlog.json` 3-SSOT를 읽지도 쓰지도 않아 소유권 경계를 침범하지 않는다.

**유지된 것 (회귀 방어)**

- `--pm` 미지정 기본 경로(`//opd`·`//opds`)는 동작·산출물·상태 스키마가 무변경이다. `state.json`에 `actor` 키가 **생성되지 않고**, `pipeline.json`·`pipeline-short.json`은 diff 0바이트다.
- `actor=pm`에서도 독립 검증 3지점은 서브에이전트 증거 없이 통과할 수 없다 — 목표-커버 게이트, TEST 단계, CLOSE 진입 게이트. 생성자≠평가자 분리가 actor 값과 무관하게 유지된다.
- 권한 경계(외부 설치·프로젝트 밖 쓰기·비가역 변경·commit/push/배포·사용자 Gate)는 직접 수행 승인과 별개로 유지된다.

**적용한 경계**

- 지원 Pilot은 `opal-pilot-dev`(`opd`/`opds`) **하나**로 닫았다. 목록 밖 Pilot에 `--pm`을 주면 `actor.md`의 폐쇄 목록이 통보를 강제하고, `state-tool init --actor pm --skill <목록 밖>`이 `actor_unsupported_for_skill`로 exit 1 거부한다(산문 + 도구 2중).
- 제안서 §12의 4단계(타 Pilot 확산)와 6단계(전 Pilot 회귀)는 범위에서 제외했다 — 제안서 자신이 "한 Pilot 수직 검증 후 확산"을 권고한다.
- 제안서 §8(GC 검사 본체 분리)은 태스크 120에서 `op-gc-security`·`op-gc-convention`·`op-gc-report` 실명으로 완료되어 있어, 이번에는 직접 수행 경로에서의 **호출 연동**만 규정했다.

## 변경 파일

**신규**

- `opal/core/references/harness/actor.md`
- `opal/skills/opal-self-pm/SKILL.md`
- `opal/skills/opal-self-pm/references/question-loop.md`
- `opal/skills/opal-self-pm/references/knowledge-sync.md`
- `opal/tools/self-pm-tool/self_pm_tool.py`
- `opal/tools/self-pm-tool/run.sh`
- `opal/tools/self-pm-tool/README.md`
- `opal/tools/self-pm-tool/tests/test_self_pm_tool.py`
- `opal/tools/state-tool/tests/fixtures/s1_baseline_rows.json`

**수정**

- `opal/core/references/events.json` — `pilot.start` required_docs에 `actor` 추가
- `opal/core/references/harness/modes.md` — 라우팅 계약 조항 8(actor 직교)
- `opal/core/references/harness/guards.md` — 디스패치 의무 actor-aware 재서술 + §독립 검증 경계 신설
- `opal/core/references/harness/capability.md` — §PM 직접 수행 시 capability 선택
- `opal/core/references/harness/state.md` · `harness/header-rules.md` · `harness/pm-improvement-loop.md` — L2 참조를 `opal-self-pm`으로 이전
- `opal/core/references/harness/skill-commands.md` — 커맨드 문법에 `[--pm]` 노출 + 예시 2행
- `opal/core/references/opal-pm.md` — §12 L2 블록을 §PM 직접 수행 진입점으로 교체
- `opal/core/references/opal-harness.md` — 실행 소유 문서 표에 `harness/actor.md` 1행
- `opal/core/references/pm/dispatch-process.md` — Steps 1~3의 `actor=pm` preflight 재사용 명시
- `opal/core/references/opal-skills-registry.json` — v3.18.0, `groups.opal`에 `opal-self-pm`(alias `oppm`)
- `opal/skills/opal-pilot-dev/SKILL.md` — `--pm` 수직 접합(actor 축 절·STATE 초기화·STEP 2/3-1/4 분기·독립 검증 3지점 actor 무관 명시)
- `opal/tools/state-tool/state_tool.py` · `tests/test_state_tool.py` · `README.md` — `--actor {pm}` 조건부 영속화 + `actor_unsupported_for_skill`
- `scripts/install-mac.sh` — `self-pm-tool/run.sh` chmod 블록
- `README.md` · `docs/PROJECT.md` · `docs/ARCHITECTURE.md` · `docs/CONVENTIONS.md` · `docs/architecture-diagram/opal_framework_architecture.html` — 진입점·컴포넌트·약어·개수 동기화

**이관**

- `docs/proposals/opal-pm-direct-execution.md` → `docs/proposals/archives/` (상태 `제안` → `적용완료`, 잔여 인용 0건 확인 후)

## 검증

- `pytest opal/tools/state-tool/tests/` → **428 passed, 3 skipped, 111 subtests passed**
- `pytest opal/tools/self-pm-tool/tests/` → **6 passed**
- `test-tool scenario-status` → **22/22 PASS**, failed 0, blocked 0, `red_confirmed 7/7`, locked
- `code-scan validate --changed <csv>` → **exit 0**, `newly_uncovered: 0`, `header_history: 0` (`pre_existing: 16`은 기존 결손·비차단)
- `state-tool validate` → violations 0
- 컨벤션 자동 진단(`opal-convention-checker`, scope=all, 대상 9건) → **PASS**, Critical/High/Medium/Low 전부 0 — `GC-CONVENTION-2026-09-12T20-35-03.md`
- AC-4 회귀 — `--actor` 미지정 `state.json`에 `actor` 키 부재 + 11행 유지
- AC-14 — `--actor pm --skill opwt` **exit 1** `actor_unsupported_for_skill`, `state.json` 미생성 / 대조군 `--skill opds`는 exit 0 + `actor: "pm"`
- AC-1 — `--pm --agentic --wt` 3축 동시 투입 시 `mode_flag_conflict` 미발생
- AC-12 — `command grep -e "L2 경량" -e "direct-workflow" -e "direct-adaptive"` 결과가 변경이력 표 행 3파일 외 **0건**
- AC-13 배포 실측(install 1차 19:58 exit 0 시점) — `~/.opal/references/harness/actor.md` 존재 · `pilot.start` required **5종**(guards·modes·worktree·capability·actor) · `~/.opal/skills/opal-self-pm/SKILL.md` 존재 · `self-pm-tool/run.sh` 실행 가능 · 배포본 `skill-commands.md`에 `--pm` 3건
- 보안 — 변경분 시크릿 패턴 0건, `.gitignore:32`에 `.env` 등재

## 회고적 학습 후보

.opal/brain/pages/concept/actor-axis-orthogonal-to-mode.md
.opal/brain/pages/concept/count-notation-scattered-across-docs.md
.opal/brain/pages/concept/verification-only-workitem-needs-remediation-owner.md
.opal/brain/pages/concept/fork-agent-inherits-pm-role.md
.opal/brain/pages/entity/opal-self-pm.md
.opal/brain/pages/entity/self-pm-tool.md

## 참고

- **배포본 미동기 상태로 마감했다.** CLOSE 시점 `~/.opal/`에는 이 태스크의 신규 자산(`actor.md`·`opal-self-pm`·`self-pm-tool`)이 없다. 같은 머신의 다른 세션이 허브(main)에서 `install-mac.sh`를 실행해 배포본을 main 상태로 되돌렸기 때문이며, 워크트리 소스는 무결하다. **merge 후 `./scripts/install-mac.sh` 1회 실행으로 복구된다.** 소유자 지시로 배포는 손대지 않고 마감했다.
- `~/.opal/`은 세션 간 공유 자원이므로 동시 실행 중에는 install이 경합한다 — 마지막에 끝난 쪽이 이긴다.
- `pre_existing` 16건(기존 harness 문서 `@header` 결손)은 이 게이트의 책임 범위가 아니어서 손대지 않았다. 소급 부여는 `discover`/`scaffold`의 몫이다.
- `plan.scenario_gate` 행은 `pipeline-short.json`에 `gate` 필드가 없어 도구 차단 없이 mark된다 — 이번 태스크 이전부터의 설계이며 pipeline 파일은 diff 0바이트로 비변경이다. 문서 수준 보장은 `opal-pilot-dev/SKILL.md`가 담당한다.
- `--wt`는 `skill-commands.md` 커맨드 문법에 여전히 없다 — 이번 태스크가 만든 결함이 아니어서 범위 밖으로 두었다.
