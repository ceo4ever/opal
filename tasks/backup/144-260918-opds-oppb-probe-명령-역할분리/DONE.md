# DONE: OPPB probe 명령의 관측·판정 역할 분리

## 결과

OPPB가 `.gitattributes` `export-ignore`를 쓰는 저장소에서 P2 `environment_seal`을 통과할 수 없던 구조적 차단을 걷어냈다. 태스크 142가 실제로 이 차단에 걸려 멈춰 있었고, 이 태스크의 변경으로 재개 가능해졌다.

**무엇이 문제였나.** `op-oppb-project-slice/SKILL.md`가 `verify_command`·`run_command` argv를 probe 명령 집합에 **같은 내용으로 등재하라**고 요구했다. 그래서 수용 판정용 명령이 probe에 들어갔고, `probe seal`은 그 명령이 exit≠0이면 run 시작을 거부했다. 그런데 probe는 판정기가 아니라 관측기다 — 명령마다 `git archive HEAD` 스냅샷을 새로 만들고 실행 직후 버리며(`probe.py:405` `_observe_command`), 그 스냅샷에는 export-ignore된 `tasks/`·`docs/`·`.opal/`·`.gitignore`가 없다. 동결 fixture를 읽는 테스트 30건이 `FileNotFoundError`로 죽고, bootstrap이 만든 의존성도 다음 명령에 전달되지 않는다. 등재는 필수인데 통과는 불가능한 상태였다.

**무엇을 바꿨나.** 등재 기준을 kind 라벨이 아니라 두 조건으로 규정했다 — R1(그 명령의 exit code가 수용 판정에 쓰이지 않는다)과 R2(`git archive HEAD` 산출물만으로 exit 0이고 180초 안에 끝난다). 둘을 동시에 만족하는 관측 전용 명령만 등재한다. `kind`는 `bootstrap`(의존성·환경 준비)과 `build`(그 외 관측 전용) 2종으로 닫았다.

**판정 주체는 옮기지 않았다.** "probe 미등재는 검증 면제가 아니다 — 수용 판정은 §3.1 `verify_command`가 단독 소유"를 §3.2에 넣고 정의 원본(§3.1)은 참조로만 걸었다. 미등재 명령의 미추적 쓰기는 `lease.ephemeral_writes`·`lease.runtime_resources` 선언과 late discovery(`probe observe-write`)가 담당한다 — 관측 공백으로 두지 않았다.

**제안서도 함께 맞췄다.** `opal-pilot-project-build/SKILL.md:26`이 "설계 SSOT는 제안서"라고 선언하므로 스킬만 고치면 개정이 무효가 된다. `opal-oppb-project-build-pilot.md` §P2.2의 2문장만 같은 기준으로 정합시켰다.

**아무것도 새로 만들지 않았다.** 새 `kind` 값을 만들지 않은 이유는 코드가 실제 구분하는 값이 `bootstrap` 하나뿐이고(`probe.py:497` `classify_path`) 나머지는 `build`와 동치라, 새 값이 코드가 소비하지 않는 빈 추상이 되기 때문이다. 새 lease 필드를 만들지 않은 이유는 `schema/oppb-state.schema.json` `$defs.lease`가 `additionalProperties: false`이고 `controller.py:370 LEASE_AXES`가 같은 4축이라 스키마 위반이 되기 때문이다.

유지된 것: `opal/tools/oppb-runtime-tool/` 코드 무변경(`COMMAND_TIMEOUT_SECONDS` 포함), `.gitattributes` 무변경, 142의 `.oppb-workgraph-spec.json`·`INTENT.md`·슬라이스 형태 무변경, 스킬 `변경이력` 표 행 수 불변.

## 변경 파일

- `opal/skills/op-oppb-project-slice/SKILL.md`
- `docs/proposals/opal-oppb-project-build-pilot.md`
- `.opal-worktrees/task_142/tasks/142-260918-oppb-E2E-여정조각-라이브러리/.oppb-probe-commands.json` (소비 태스크 갱신, git 미추적)
- `.opal-worktrees/task_142/.opal/oppb-environment.json` (seal 산출물, `.gitignore`로 무시)
- `~/.opal/skills/op-oppb-project-slice/SKILL.md` (install 산출물 — 직접 편집 없음)

## 검증

- S-1~S-13 실행 — `scenario-status` 실측 `passed: 12, failed: 0, blocked: 1`. blocked 1건은 S-11로 조건 미성립이다(전제인 timeout 초과가 0건).
- **S-7(목표)** — 142 run root 봉인 검증. `probe_runs` 8건 전건 `exit_code: 0`, 최장 `bootstrap-npm-ci` 7752ms(상한 180000ms의 4.3%). `input_hash` 5종(bootstrap·commands·config·lockfile·toolchain), `ephemeral_write_set` 44건, `scope_hash` 존재.
- **S-13(부정)** — R1 위반 명령 1건을 임시 사본에 넣자 `probe seal`이 `{"ok": false, "error": "probe_command_failed", "message": "verify-T01 exit=5 … NO TESTS RAN"}`로 거부. 실행 전후 파일 6건 sha256 전건 동일 — run root 무변경.
- **S-5(배포)** — `cd ~` 후 절대경로로 배포본 확인, 4개 서술 전건 존재. `## 변경이력` 절 제외 diff 0. 배포본 mtime이 install 산출임을 확인.
- **S-12(채택·잔존)** — 구형 등재 요구 문장 잔존 0, 신형 R1·R2 채택. 개정 전 규칙에서 142가 만족 불가였음을 대조 입증.
- `state-tool verify --plan-contract-check` / `--code-scan-citation-check` / `validate` — 전건 pass, violations 0.
- `code-scan validate --changed` — `newly_uncovered: 0`.
- 회귀: `oppb-runtime-tool` unittest `Ran 13 tests / OK` exit 0. `test_archive_contents.sh` exit 1(PASS 11 / FAIL 1) — 유일 실패 TC-E는 선재 실패이며 아래 §참고에 기록한다.
- op-scenario-gate iteration 1 `verdict: pass` (goal 2 / adoption 2 / boundary 1, gaps 0). 통과 후 evaluator 지시 2건(S-5 기대결과 정정·S-13 신설)을 반영했고 커버리지 재검사 exit 0.

## 회고적 학습 후보

.opal/brain/pages/concept/observation-tool-must-not-gate-acceptance.md
.opal/brain/pages/concept/execution-evidence-is-bound-to-execution-condition.md

## 참고

- **이 태스크는 143에서 144로 재번호됐다.** 채번 직후 다른 세션이 같은 번호로 `tasks/143-260918-opds-스킬-문서-사이드바`를 만들어 main에 먼저 머지했다(`e6911aa`). 나중에 완료된 이쪽이 양보했다. 문서 본문과 커밋 `a275431`의 "143" 표기는 실행 당시 사실이며 재작성하지 않았다 — 식별자는 폴더명 `144-260918-opds-oppb-probe-명령-역할분리`가 소유한다. `state.json`의 `task_id`도 init 시점 기록이라 `143-...`로 남아 있다(도구가 이후 호출에서는 폴더명을 쓴다). 채번이 원자적이지 않았던 원인은 별도 태스크가 소유한다.

- **TC-E 선재 실패(143과 무관).** `scripts/tests/test_archive_contents.sh:139-149`가 `opal/core/hooks/claude-hooks.json`에 `transition_action`·`continue`·`next_action`·`stop_hook_active` 4종을 요구하는데, 작업 트리·HEAD·`feat/OP-TASK-138` 브랜치 모두 0건이다. Stop 가드가 `ownership_tool/stop_hook.py`로 이동하면서 문자열이 JSON에서 빠졌는데 테스트가 옛 훅 형태를 그대로 단언한다. 그 파일의 마지막 커밋은 `9553d3a`(태스크 138)다. 143은 그 파일을 건드리지 않았다(`git status` 0행). **AC-8의 '동일'은 충족, '통과'는 이 1건이 미충족이며 별도 태스크 후보다.**
- **142 `.oppb-probe-commands.json`이 git 미추적이다.** `.gitignore`가 `.opal/*`를 무시해 바이트 기준선이 없고, "변경 전과 동일" 절을 사후 입증할 수 없다. 이번에는 간접 대조(142 `PROJECT-DESIGN.md:45`의 동일 id·자원 기록)로 갈음했다. OPPB가 이 파일을 추적하거나 EXECUTE가 변경 전 사본을 남기는 절차가 필요하다 — 후속 후보.
- **제안서 상태 행이 어휘 밖이다.** `opal-oppb-project-build-pilot.md:3`이 `> 상태: 초안`인데 `harness/proposal-lifecycle.md` §상태 어휘는 `제안`·`검토`·`적용완료`·`폐기` 4종만 허용한다. PLAN이 명명하지 않은 변경이라 손대지 않았다.
- **제안서 아카이브 이관은 하지 않는다.** 잔여 인용 3건(`opal/tools/oppb-runtime-tool/README.md:14`, `opal/agents/opal-evaluator-agent/AGENT.md:237`, `opal/skills/opal-pilot-project-build/SKILL.md:26`)이 있고, 이 제안서는 OPPB 설계 SSOT로 현역이다.
- **머지 후 허브 재설치가 필요하다.** 현재 배포본은 워크트리 143에서 설치한 것이다. `install-mac.sh:112`가 실행한 체크아웃을 읽으므로, 다른 세션이 허브(main)에서 재설치하면 미머지 상태의 이 개정이 사라진다. main merge 이후 허브에서 한 번 더 install해야 안정된다.
- **태스크 142 재개 가능.** P2 `environment_seal`이 blocked였고 이 태스크의 변경으로 봉인이 완료됐다. 142는 `p2.user_gate`(사용자 게이트 ②)부터 이어가면 된다.
