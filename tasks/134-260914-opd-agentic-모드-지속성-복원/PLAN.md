---
template: sdlc-v2
---
# PLAN: agentic 모드 지속성 복원

> 입력: [TASK.md](TASK.md), [ANALYSIS.md](ANALYSIS.md)

## Approach

`state.json.mode`를 새 저장소로 대체하지 않고, state-tool의 단일 effective-mode resolver가 신규 시작·기존 작업 재개·명시 override·자동 승인·검증·부트 요약에 동일한 우선순위와 fail-closed 정책을 제공하게 한다. Pilot은 서브 하네스를 읽기 전에 이 구조화 결과를 소비하고, 중첩 Pilot과 트랙 전환에는 판정된 모드를 명시 전달한다. 구현은 RED 계약을 먼저 고정한 뒤 state-tool과 event-loader를 변경하고, 마지막에 owner 하네스·Pilot·프로젝트 문서와 source→install 경계를 맞춘다. code-scan `search 'state|event|harness|pilot|mode' --full` 결과에서 `state_tool`(domain `opal-pipeline`, layer `util`)과 `event_loader`(domain `opal-tools`, layer `util`) 및 각 테스트가 현재 코드 변경의 직접 표면으로 확인됐으며, 아래 E2 코드 근거와 함께 사용한다. (`opal/tools/state-tool/state_tool.py:1-18`, `opal/tools/event-loader/event_loader.py:525-622`; → D-9 §9(e))

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|---|---|---|---|
| D-1 | 기획 | TASK | `tasks/134-260914-opd-agentic-모드-지속성-복원/TASK.md` | AC-1~AC-8와 C-1~C-6 |
| D-2 | 설계 | ANALYSIS | `tasks/134-260914-opd-agentic-모드-지속성-복원/ANALYSIS.md` | 현재 결함·변경 경계·handoff |
| D-3 | 설계 | Modes | `opal/core/references/harness/modes.md` | 현재 모드 플래그 라우팅 owner |
| D-4 | 설계 | State | `opal/core/references/harness/state.md` | 세션 복원과 state.json SSOT owner |
| D-5 | 설계 | 프로젝트 정의 | `docs/PROJECT.md` | 표준화·재사용·플랫폼 독립·하네스 원칙과 문서 레지스트리 |
| D-6 | 설계 | 아키텍처 | `docs/ARCHITECTURE.md` | session JIT, 하네스 owner, source→install 모델 |
| D-7 | 설계 | 컨벤션 | `docs/CONVENTIONS.md` | Guards, State, 도구, 배포, 플랫폼 분기 규칙 |
| D-8 | 설계 | 프로젝트 에이전트 계약 | `.opal/AGENT.md` | 하네스 owner 수정·state-tool·배포 경계 |
| D-9 | 설계 | 인용 규칙 | `opal/core/references/harness/citation-rules.md` | PLAN 인용과 E5 동반 근거 계약 |
| D-10 | 설계 | 자동 승인 2축 지식 | `.opal/brain/pages/concept/auto-approve-user-confirmation-axis-separation.md` | CLOSE 축과 mode 축 분리 포인터(E5) |
| D-11 | 소스 | state-tool | `opal/tools/state-tool/state_tool.py` | mode 판정·상태 I/O·CLI·boot-summary 구현 |
| D-12 | 소스 | event-loader | `opal/tools/event-loader/event_loader.py` | bounded project-brief 구현 |

[MUST] `.opal/AGENT.md` §프로젝트별 추가 지침: "`~/.opal/` 배포 파일을 직접 수정하지 않는다. 항상 프로젝트 소스(`opal/`, `skills/`, `agents/`, `community-skills/`, `scripts/`)를 수정한 뒤 install로 재배포한다." (`.opal/AGENT.md:39-46`)

[MUST] `docs/CONVENTIONS.md` §State 관리: "파이프라인 행 상태(⬜/🔄/✅) 변경은 `~/.opal/tools/state-tool/run.sh`로만 수행한다. `state.json` 직접 편집 금지" (`docs/CONVENTIONS.md:235-243`)

[MUST] `docs/CONVENTIONS.md` §플랫폼 분기 격리: "스킬·에이전트 본문에 플랫폼 조건문을 추가하지 않는다" (`docs/CONVENTIONS.md:261-264`)

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| D-1. effective mode resolver를 state-tool에 단일화 | 공개 명령은 `state-tool resolve-mode <task-path> [--mode interactive\|semi-agentic\|agentic] [--new-task]`로 한다. 정확히 한 함수가 `명시 --mode > 유효한 기존 state.json.mode > 신규 task의 semi-agentic 기본값`을 판정하고 JSON에 `effective_mode`, `source`(`explicit`/`state`/`default`/`fail_closed`), `persisted`, `previous_mode`, `warnings`를 반환한다. state 부재는 `--new-task`일 때만 신규로 인정하고 기존 task의 state 부재를 신규로 추정하지 않는다. Pilot은 `pilot.start` receipt 검증 뒤, 모드별 서브 하네스 load 전에 이 명령을 호출한다. | 현행 modes owner는 무플래그를 무조건 semi-agentic으로 정하고, 세션 복원은 뒤늦게 state를 조회해 두 판정이 갈라진다. (`opal/core/references/harness/modes.md:20-32`, `opal/core/references/harness/state.md:101-113`, `opal/skills/opal-pilot-dev/SKILL.md:10-16`; → D-2 Findings 2)
| D-2. 명시 override는 resolver의 전용 mutation 경로로만 수행 | 기존 parse 가능한 state에서 `--mode`가 주어지면 resolver가 명시값을 effective mode로 확정하고, 값이 달라질 때 `state.json`의 `mode`만 같은 디렉터리의 임시 파일→flush/fsync→`os.replace`로 원자 갱신한다. `rows`, `created_at`, 진행 상태와 나머지 필드는 의미적으로 그대로 보존하며 `--force init`은 사용하지 않는다. 실제 변경은 STATE.md 의사결정 로그에 `old→new`, source=`explicit`, 사용자 플래그 근거를 남기고 stdout에도 동일 감사 필드를 반환한다. 같은 값 재지정은 멱등(`persisted:false`)이며 로그를 중복 추가하지 않는다. 저널 실패는 기존 fail-open `journal_warning`으로 표면화한다. | `init`은 기존 state를 거부하고 `--force init`은 rows를 재구성한다. 기존 저널 API는 결정·근거와 실패 경고를 제공한다. (`opal/tools/state-tool/state_tool.py:495-572`, `opal/tools/state-tool/state_tool.py:1377-1429`; → D-2 Findings 4~5)
| D-3. legacy/invalid 상태를 interactive로 fail-closed | 기존 state의 mode가 누락·비문자·enum 밖이면 무플래그 resolver는 파일을 고치지 않고 `effective_mode=interactive`, `source=fail_closed`, 경고를 반환한다. `advance`/`mark`의 자동 승인 판정도 같은 정규화 함수를 사용해 `invalid_mode_requires_user`로 거부하며, `validate`는 invalid mode 위반을 보고한다. 명시 `--mode`만 D-2 경로로 복구할 수 있다. JSON 자체가 깨졌거나 top-level object가 아니면 보존 가능한 state가 아니므로 명시 플래그가 있어도 `state_json_malformed`로 차단하고 무변경한다. 신규 task만 semi-agentic 기본값을 쓴다. | 현재 schema는 3-way enum을 요구하지만 unknown 문자열은 자동 승인 함수의 허용 종단으로 흘러간다. (`opal/tools/state-tool/schema/state.schema.json:6-15`, `opal/tools/state-tool/schema/state.schema.json:38-45`, `opal/tools/state-tool/state_tool.py:65-89`, `opal/tools/state-tool/state_tool.py:945-951`; → D-2 Findings 7). 이는 기존 mode 축을 안전하게 입력할 뿐 CLOSE 축을 바꾸지 않는다. (→ D-10 §결정 내용 + E2 `opal/tools/state-tool/state_tool.py:970-1018`)
| D-4. 신규·재개·검토 왕복의 순서를 고정 | 신규 task는 `resolve-mode --new-task [--mode ...]` 결과로 하네스를 선택하고 같은 mode로 `init`한다. 기존 task의 무플래그 재개와 사용자 검토 응답 후 재진입은 `resolve-mode <task-path>`의 저장 mode를 상속한다. 기존 task에 명시 플래그가 있으면 resolver의 원자 override·감사 기록을 완료한 뒤 그 결과의 하네스를 읽고 state 전이를 수행한다. task 식별 실패·복수 후보는 추정하지 않고 기존 선택 게이트로 남긴다. | 정상 state의 mode는 저장·자동 승인에 이미 사용되지만 Pilot 시작에 합성 resolver가 없다. (`opal/tools/state-tool/state_tool.py:913-963`, `opal/tools/state-tool/state_tool.py:1419-1428`; → D-2 Findings 1~4)
| D-5. project brief는 mode를 노출하되 판정 SSOT가 아니다 | `boot-summary.items[0]`에 정규화된 `mode`와 `mode_source`를 additive로 싣고, project-brief `이어보기` 한 줄에도 mode를 표시한다. invalid legacy는 `interactive`와 `fail_closed`를 함께 노출한다. 1,024 UTF-8 byte 상한, 최신 미완료 1건, 부분 조회 실패 시 해당 블록만 생략하는 계약은 유지한다. Pilot은 브리프 산문을 파싱하지 않고 D-1 JSON 명령을 다시 호출한다. | 현재 두 층은 title/stage/next_action만 전달한다. (`opal/tools/state-tool/state_tool.py:2384-2445`, `opal/tools/event-loader/event_loader.py:525-622`; → D-2 Findings 3). session.project는 최대 1KB 브리핑만 인지한다. (`docs/ARCHITECTURE.md:54-70`)
| D-6. nested/track 경계에는 판정값을 명시 전달 | `oppd→opwt` 호출과 사용자가 수락한 `opd→opds`, `opds→opd` 전환은 부모/현재 task의 effective mode를 대응하는 명시 플래그로 전달한다. 이 전달은 mode 상속만 담당하고 새 사용자 override로 재해석하지 않는다. 기존 산출물/profile 인계 및 트랙 선택 절차는 유지하며 `--force init`으로 pipeline을 재작성하지 않는다. | 현재 oppd의 opwt 호출 템플릿에는 부모 mode가 없고 track 문서는 산출물 인계만 정한다. (`opal/skills/opal-pilot-project-dev/SKILL.md:183-200`, `opal/skills/opal-pilot-dev/references/track-routing.md:46-58`, `opal/skills/opal-pilot-dev/references/track-escalation.md:43-55`; → D-2 Findings 6~7)
| D-7. mode와 사용자 주권 게이트를 직교 유지 | resolver는 mode 축의 입력만 결정한다. CLOSE 진입 사용자 확인, 권한·안전·비가역 행동, PRD/TRD 소유권, 트랙 전환 수락은 agentic이어도 자동 승인하지 않는다. interactive 전 구간과 semi-agentic pre-execute 경계 및 worker/force 예외도 기존 결과를 유지한다. | CLOSE는 mode보다 먼저 거부되고 track 변경은 사용자 응답 없이 수행할 수 없다. (`opal/tools/state-tool/state_tool.py:83-89`, `opal/tools/state-tool/state_tool.py:970-1018`, `opal/skills/opal-pilot-dev/references/track-routing.md:12-18`, `opal/skills/opal-pilot-project-dev/SKILL.md:469-481`; → D-10 §결정 내용). [MUST] `docs/CONVENTIONS.md` §Guards: "CLOSE 단계 진입 직전에는 사용자의 명시적 확인 ... 이 반드시 있어야 한다" (`docs/CONVENTIONS.md:207-213`)
| D-8. 기존 project-brief 실패는 RED 단계에서 별도 분류 | 구현 전에 현행 `test_project_brief_renders_ready_to_emit_markdown`의 `이어보기` 누락을 독립 재현하고, state-tool subprocess/fixture/환경 경계를 분리해 원인을 기록한다. 기존 기대 문자열은 삭제·완화하지 않으며 원인에 해당하는 최소 수정 뒤 mode 기대를 additive로 확장한다. | 단일 테스트 실행은 현재 `이어보기` 없이 FAIL한다(E1, 범위: 해당 unittest 1건, 명령: `cd opal/tools/event-loader/tests && python3 -m unittest test_event_loader_extended.EventLoaderExtendedContractTest.test_project_brief_renders_ready_to_emit_markdown`). (`opal/tools/event-loader/tests/test_event_loader_extended.py:209-257`; → D-2 Findings 9)
| D-9. source→install 및 플랫폼 공통 계약 | 수정은 저장소 소스에만 하고 install은 산출물을 배포본과 지원 플랫폼에 전파하는 검증 단계로 사용한다. 모드 로직에 플랫폼 조건문을 추가하지 않는다. | 소스→`~/.opal/` 배포와 지원 플랫폼 어댑터 경계가 정의돼 있다. (`docs/ARCHITECTURE.md:221-260`, `docs/CONVENTIONS.md:253-264`; → D-5 §프로젝트 원칙)

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. RED 회귀 계약 및 baseline 원인 분류 | `opal-be-agent` (RED 테스트 작성 전담; W-2/W-3 구현자와 다른 워커 인스턴스) | `opal/tools/state-tool/tests/test_mode_resolution.py`, `opal/tools/event-loader/tests/test_event_loader_extended.py`, `scripts/tests/task134_mode_persistence_contract.py` | 먼저 기존 project-brief 1건의 `이어보기` 누락을 단독 재현해 state-tool subprocess·fixture·환경 중 원인을 분리하고 기존 기대값을 보존한다. 이어 공개 CLI 블랙박스 RED로 신규 기본 semi, 유효 저장 mode 무플래그 재개/새 프로세스, 명시 우선·원자 갱신·rows/created_at 보존·멱등·감사, 누락/비문자/unknown fail-closed, malformed JSON 무변경, agentic 검토 왕복, interactive/semi/CLOSE 경계를 고정한다. event 테스트에는 mode payload/렌더/1KB/부분 실패를, 정적 계약 테스트에는 `oppd→opwt`, 기존 task 재호출, 양방향 track 전환의 effective mode 전달과 사용자 게이트 보존을 추가한다. code-scan 결과의 `state_tool`/`event_loader` 테스트 모듈 경계를 따른다. (`opal/tools/state-tool/tests/test_state_tool.py:8052-8299`, `opal/tools/event-loader/tests/test_event_loader_extended.py:209-325`) | 없음 | P1 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, C-2, C-3, C-4 |
| W-2. state-tool effective mode SSOT 구현 | `opal-be-agent` (구현 전담; W-1 작성자와 다른 워커 인스턴스) | `opal/tools/state-tool/state_tool.py`, `opal/tools/state-tool/schema/state.schema.json` | D-1~D-4의 공통 mode 정규화/resolver와 `resolve-mode` CLI를 추가하고 명시 override를 temp+fsync+`os.replace`로 원자 저장한다. 모든 비-mode state 값을 보존하고 기존 결정 로그·warning 경로로 감사를 남긴다. advance/mark/validate/boot-summary를 같은 resolver에 연결해 unknown fail-open을 제거하고 malformed 오류를 구조화하며 mode/mode_source를 bounded boot payload에 추가한다. 현행 host-interpreter baseline 원인이 state-tool 소스 인코딩 선언 부재로 확정되면 UTF-8 선언을 최소 추가해 기존 브리프 기대를 복구한다. W-1 테스트 파일은 수정하지 않는다. (`opal/tools/state-tool/state_tool.py:65-89`, `opal/tools/state-tool/state_tool.py:359-372`, `opal/tools/state-tool/state_tool.py:913-963`, `opal/tools/state-tool/state_tool.py:2384-2445`, `opal/tools/state-tool/state_tool.py:3989-4049`) | W-1 | P2 | AC-1, AC-2, AC-4, AC-5, AC-6, AC-7, C-1, C-2, C-3, C-4, C-6 |
| W-3. event-loader mode 브리프 구현 | `opal-be-agent` (구현 전담; W-1 작성자와 다른 워커 인스턴스) | `opal/tools/event-loader/event_loader.py` | boot-summary의 `mode`/`mode_source`를 정규화해 `이어보기`에 표시하고, invalid legacy의 fail-closed 상태를 구분한다. 기존 최신 1건·부분 실패 생략·UTF-8 1,024-byte truncation을 유지하며 브리프는 표시 전용임을 코드 계약에 남긴다. W-1 테스트 파일은 수정하지 않는다. code-scan 결과의 `event_loader` util 경계 안에서만 변경한다. (`opal/tools/event-loader/event_loader.py:520-622`) | W-1 | P2 | AC-2, AC-5, AC-6, C-1, C-4, C-6 |
| W-4. owner 하네스·Pilot·공개 문서 및 install 검증 정합화 | PM 직접 | `opal/core/references/harness/modes.md`, `opal/core/references/harness/state.md`, `opal/skills/opal-pilot-dev/SKILL.md`, `opal/skills/opal-pilot-dev/references/track-routing.md`, `opal/skills/opal-pilot-dev/references/track-escalation.md`, `opal/skills/opal-pilot-project-dev/SKILL.md`, `opal/tools/state-tool/README.md`, `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md` | modes owner에 resolver 우선순위·호출 순서·invalid/malformed 계약을 한 번만 정의하고 state owner에는 구조화 복원 소비를 연결한다. Dev Pilot에는 신규/기존/검토 왕복/명시 override를, track 문서와 project-dev에는 effective mode 명시 상속을 추가하되 트랙·PRD/TRD·CLOSE 사용자 게이트를 보존한다. README와 프로젝트 문서는 실제 CLI·brief·원자 override·source/install 계약만 갱신하고 `events.json` 문서 집합은 새 owner가 없으므로 변경하지 않는다. 정적 계약 테스트, 관련 Python 회귀, `./scripts/install-mac.sh` 또는 격리된 install 검증으로 source가 배포 대상에 반영 가능한지 확인하며 `~/.opal/`을 직접 편집하지 않는다. (`.opal/AGENT.md:39-46`, `docs/ARCHITECTURE.md:208-260`, `docs/CONVENTIONS.md:253-264`) | W-2, W-3 | P3 | AC-2, AC-3, AC-5, AC-6, AC-7, AC-8, C-1, C-2, C-3, C-4, C-5, C-6 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. 기존 state의 mode 결손을 정상 legacy와 손상으로 완전히 구분할 버전 표지가 없다 | 무플래그 재개에서 안전성과 레거시 진행성의 균형 | 잘못 agentic으로 승격되면 사용자 확인이 생략될 수 있고, 전면 차단하면 레거시 작업 재개가 어려워진다 | D-3처럼 둘 다 interactive fail-closed로 실행하되 warning+validate 위반을 남기고, 명시 override만 영속 복구한다. W-1이 누락·비문자·unknown·malformed를 각각 고정한다. (`opal/tools/state-tool/schema/state.schema.json:6-15`, `opal/tools/state-tool/state_tool.py:359-365`)
| H-2. mode 원자 저장과 STATE.md 감사 로그는 단일 파일 트랜잭션이 아니다 | override 성공 후 저널 쓰기만 실패할 수 있음 | 사후 감사 문맥 일부가 저널에서 빠질 수 있음 | state.json은 먼저 원자 확정하고 stdout에 old/new/source/persisted를 항상 반환하며, 기존 `journal_warning`을 보존해 실패를 조용히 숨기지 않는다. (`opal/tools/state-tool/state_tool.py:545-572`)
| H-3. 브리프 문자열 확대가 1KB truncation 또는 기존 exact-string 회귀를 깨뜨릴 수 있다 | session.project 첫 응답 byte 상한과 `이어보기` 표시 | 부트 응답 누락 또는 플랫폼 부트 계약 실패 | W-1에서 baseline 실패를 먼저 분리하고 기대 삭제를 금지하며, mode를 additive로 넣은 exact/boundary/partial-query 테스트를 고정한다. (`opal/tools/event-loader/event_loader.py:558-585`, `opal/tools/event-loader/tests/test_event_loader_extended.py:209-325`)
| H-4. track profile state 이관 문제를 mode 변경으로 함께 풀려 하면 범위가 확대된다 | opd/opds pipeline rows와 skill 값 보존 | 진행 행 손상 또는 강제 init 재구성 | 이번 변경은 effective mode 명시 상속만 소유하고 profile 산출물/상태 이관의 기존 계약을 유지하며 `--force init`을 금지한다. 별도 상태 이관 결함이 검출되면 mode와 분리해 보고한다. (`opal/skills/opal-pilot-dev/references/track-routing.md:46-58`, `opal/skills/opal-pilot-dev/references/track-escalation.md:43-55`)

## Release and recovery

- 적용 순서: P1에서 RED 및 baseline 원인 분류를 확정한 뒤 P2의 W-2/W-3를 파일 비충돌로 구현하고, 두 구현이 GREEN일 때만 P3의 owner 문서·Pilot·README·프로젝트 문서와 install 검증을 수행한다. 이후 `opal-test-agent`가 변경 파일 기준 전체 관련 회귀를 독립 실행한다.
- 검증 범위: 결정론 검증은 `resolve-mode` 공개 CLI의 우선순위·무변경 실패·원자 override·감사 payload, 자동 승인 모드×단계 회귀표, boot-summary/project-brief exact/bounded/partial-query를 포함한다. 통합 검증은 기존 task 무플래그 재호출, 프로세스 재시작, 사용자 검토 왕복, `oppd→opwt`, `opd↔opds`, CLOSE/권한/트랙 게이트 정적 계약을 포함한다. install 검증은 저장소 소스가 배포 대상에 반영 가능한지만 확인하고 배포본을 수기 수정하지 않는다. (`docs/ARCHITECTURE.md:221-260`)
- 실측 경계: baseline E1은 W-1 시작 시 단일 실패 테스트로 재확인하고 원인 분류를 기록한다. GREEN은 W-1 신규/변경 테스트, 기존 state-tool/event-loader 전체 테스트, 정적 Pilot 계약 테스트, install 회귀가 모두 통과할 때 종료한다. 실제 4개 플랫폼의 대화 세션 재개는 이 환경의 자동 검증 범위 밖이므로 플랫폼 독립 소스·무분기 정적 계약과 install 결과를 대리 증거로 사용한다. (→ D-2 Critical assumptions)
- 실패 시: install 전 실패는 W-1 테스트 계약을 보존한 채 W-2/W-3/W-4의 소스 변경만 역순으로 되돌린다. install 후 실패는 저장소의 직전 정상 소스를 install로 재배포해 복구하며 `~/.opal/`을 직접 수정하지 않는다. mode override 중 프로세스 실패는 `os.replace` 전이면 기존 state, 후이면 새 mode 중 하나만 존재해야 하며 temp 잔여는 대상 검증 후 제거한다. 이미 완료된 rows나 `created_at`은 어떤 복구 경로에서도 재구성하지 않는다.
