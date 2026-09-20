---
template: sdlc-v2
---
# PLAN: 부트스트랩 행동 필요 브리핑

> 입력: [TASK.md](TASK.md), [ANALYSIS.md](ANALYSIS.md) (별도 ANALYSIS 없음; opds 경량 트랙)

## Approach

`session.project`가 기존 이벤트 로딩을 완료한 뒤, 프로젝트의 읽기 전용 상태 요약과
`MEMORY.json`의 검토 후보를 각각 bounded CLI로 조회하도록 계약을 확장한다. 두 결과는
부트스트래퍼가 조건부로 첫 응답에 렌더링하며, 아무 결과가 없으면 현재의 짧은 응답을
그대로 유지한다. 변경 대상은 프로젝트 code-scan 결과(`.opal/code-scan.json`)의 Framework
영역에 한정한다. 기존 `state-tool`/`memory-tool` 명령과 JSON 키는 유지하고 새 필드·조회
경로만 additive로 도입한다. 부트스트랩 본문은 Codex·Claude·Cursor·Gemini에 동일한
행동·출력 계약으로 반영한다.

## Reference documents

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|---|---|---|---|
| D-1 | 설계 | 프로젝트 정의·문서 레지스트리 | `docs/PROJECT.md` | Framework 구성과 문서 갱신 범위 |
| D-2 | 설계 | Guards | `/Users/iskang/.opal/references/harness/guards.md` | 상태 SSOT·변경/검증 경계 |
| D-3 | 설계 | Worktree | `/Users/iskang/.opal/references/harness/worktree.md` | 허브 태스크 문서와 코드 작업본 경계 |
| D-4 | 설계 | PM 디스패치 전 프로세스 | `/Users/iskang/.opal/references/pm/dispatch-process.md` | 워커 산출물·검증·반환 계약 |
| D-5 | 설계 | 컨텍스트 주입 | `/Users/iskang/.opal/references/pm/context-injection.md` | 단계별 입력과 변경 문서 선별 |
| D-6 | 설계 | 인용 규칙 | `/Users/iskang/.opal/references/harness/citation-rules.md` | PLAN 근거·[MUST] 인용 형식 |
| D-7 | 소스 | memory-tool boot brief 구현 | `opal/tools/memory-tool/memory_tool.py` | 현행 1KB·키·축약 순서 |
| D-8 | 소스 | state-tool 상태 조회 구현 | `opal/tools/state-tool/state_tool.py` | 현행 상태/행/다음 액션 SSOT |
| D-9 | 소스 | boot brief 회귀 테스트 | `opal/tools/memory-tool/tests/test_boot_brief.py` | 1,024바이트·3건·history 0 검증 |
| D-10 | 소스 | 플랫폼 parity 감사 | `scripts/tests/task113_bootstrap_audit.py` | 4개 설치 산출물과 이벤트 계약 검증 |
| D-11 | 설계 | PM 메모리 브리핑 계약 | `opal/core/references/opal-pm.md` §15, §17 | 변경 후 세션/PM 경계 갱신 |
| D-12 | 설계 | memory-tool 공개 계약 | `opal/tools/memory-tool/README.md` §boot brief | 사용자 대면 출력 규칙 갱신 |
| D-13 | 설계 | 도구 레퍼런스 | `opal/core/references/tools.md` §memory-tool | 설치 경로와 CLI 계약 갱신 |
| D-14 | 설계 | 코드맵 스캔 결과 | `.opal/code-scan.json` | 변경 대상 경로와 소비자 확인 |

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| 상태와 메모리를 각 SSOT 도구로 분리 조회 | 상태는 `state-tool`이 태스크 디렉터리의 `state.json`을 읽고, 검토 메모리는 `memory-tool`이 `.opal/MEMORY.json`을 읽는다. 어느 도구도 상대 저장소를 갱신하지 않는다. | [MUST] 파이프라인 상태는 state-tool로만 갱신한다(TASK C-5); state-tool의 state.json 단일 조회 원칙(`opal/tools/state-tool/state_tool.py:1434-1469`) (→ D-2, D-8) |
| 프로젝트 상태 조회는 새 읽기 전용 bounded 경로로 추가 | `state-tool`에 프로젝트 루트에서 `in_progress` 또는 `blocked`인 최신 태스크를 최대 1건으로 반환하는 boot 요약 계약을 추가한다. 결과에는 태스크 제목, 현재 단계, `next_action`을 포함하며 없으면 빈 목록/요약을 반환한다. 기존 `show`의 md/json/full 출력과 state schema는 변경하지 않는다. | state.json의 `current_status` enum과 rows가 SSOT다(`opal/tools/state-tool/schema/state.schema.json`); 기존 show 형식 보존은 TASK C-4 (→ D-8) |
| 검토 우선순위는 결정론적으로 고정 | `memory-tool --boot-brief`에 기존 `index_rows`/`history_rows`를 유지하면서 `review_rows`를 additive로 반환한다. `review_rows`는 최대 2건이며 `candidate` 상태를 먼저, 그 다음 active `feedback`·`issues`·`improvement`를 type 우선순위로 선택하고 동일 우선순위는 최신 `date`, 원래 순서로 안정 정렬한다. `promoted/superseded/dead`, 일반 `project/architecture/preferences/task`는 제외한다. | memory schema의 type/status enum(`opal/tools/memory-tool/schema/memory.schema.json`), 기존 boot 축약과 history 제외(`opal/tools/memory-tool/memory_tool.py:1321-1369`) (→ D-7) |
| 단일 전체 상한을 유지 | 두 CLI 결과를 합친 세션 브리핑은 UTF-8 1,024바이트 이내이며, 작업 1건·검토 메모리 2건·제목/단계/다음 행동/요약만 포함한다. 상세 본문·history `result`·긴 작업 결과는 포함하지 않는다. 초과 시 결정론적으로 오래된/낮은 우선순위 항목부터 제거한다. | TASK C-2/AC-4 및 현행 memory-tool hard cap (→ D-7) |
| 조건부 session.project 표시 | `session.project`에서만 두 조회 결과가 하나라도 있을 때 `이어보기`/`우선 검토` 블록을 첫 응답에 추가한다. 둘 다 비면 기존 부트스트랩 응답을 byte-identical하게 유지한다. `[ASSISTANT]`, `[WORKER]`, `session.disabled` 동작에는 브리핑을 추가하지 않는다. | 부트 이벤트 분기와 project brief 억제 규칙(`opal/bootstrapper/claude-bootstrap.md:16-34`) 및 TASK C-4 (→ D-7) |
| 4개 플랫폼은 같은 본문 계약을 사용 | Claude·Codex·Cursor·Gemini 소스 부트스트래퍼가 동일한 조회 순서, 조건, 필드·상한을 기술하고 parity 감사가 이를 비교한다. 설치 스크립트는 소스 파일을 계속 배포 원천으로 사용한다. | PROJECT의 플랫폼 독립성·bootstrapper 구조와 TASK AC-5 (→ D-1, D-10) |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. 메모리 검토 후보 계약 | opal-be-agent (memory-tool 소유) | `opal/tools/memory-tool/memory_tool.py`, `opal/tools/memory-tool/tests/test_boot_brief.py`, `opal/tools/memory-tool/README.md`, `opal/core/references/tools.md` | 기존 boot brief의 최상위 키와 1KB·history 0 동작을 유지하고, candidate→feedback→issues→improvement 우선의 최대 2건 `review_rows`를 추가한다. 빈/긴/동률 입력, 기존 active 행, 비대상 상태를 독립 테스트하고 공개 CLI 문서를 갱신한다. | 없음 | P1 | AC-2, AC-3, AC-4, AC-6, C-1, C-2, C-3, C-4 | `python -m unittest opal/tools/memory-tool/tests/test_boot_brief.py`; `python opal/tools/memory-tool/memory_tool.py show --help` |
| W-2. 미완료 작업 요약 계약 | opal-be-agent (state-tool 소유) | `opal/tools/state-tool/state_tool.py`, `opal/tools/state-tool/tests/test_state_tool.py` | 프로젝트 루트 하위 태스크의 state.json을 읽는 read-only boot 요약 경로를 추가한다. `in_progress`/`blocked`만 대상으로 최신 updated_at을 선택하고 단계·제목·next_action을 bounded 결과로 반환한다. done/추가작업/손상·누락 파일을 안전하게 제외하고 기존 show/validate/schema를 보존한다. | 없음 | P1 | AC-1, AC-3, AC-4, AC-6, C-1, C-4, C-5 | `python -m unittest opal/tools/state-tool/tests/test_state_tool.py`; `python opal/tools/state-tool/state_tool.py --help` |
| W-3. session.project 4플랫폼 통합 및 parity | opal-task-agent (bootstrapper 소유) | `opal/bootstrapper/claude-bootstrap.md`, `opal/bootstrapper/codex-bootstrap.md`, `opal/bootstrapper/cursor-bootstrap.mdc`, `opal/bootstrapper/gemini-bootstrap.md`, `scripts/tests/task113_bootstrap_audit.py` | 기존 session 분기 뒤 상태 요약→memory boot brief 순서로 실행하고, 성공한 bounded 결과만 조건부 첫 응답에 렌더링한다. no-op/실패/disabled/assistant/worker 경계를 명시하고 최대 1+2건·1,024바이트를 강제한다. 4개 플랫폼 본문 동일성, 명령 순서, marker 분기, 부재/미완료/우선 메모리 사례를 감사·독립 테스트로 확장한다. | W-1, W-2 | P2 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, C-2, C-3, C-4 | `python scripts/tests/task113_bootstrap_audit.py`; `python -m unittest opal/tools/opal-agent/tests/test_opal_agent_events.py` |
| W-4. 세션/PM 공개 계약 정합성 | opal-task-agent (문서 소유) | `opal/core/references/opal-pm.md` §15·§17 | 기존 “소유자 요청 시에만 메모리 브리핑” 문구를 session.project의 조건부 행동 필요 브리핑 계약으로 갱신하고, PM 재생성·문서 로딩 금지·1KB 상한·기존 키 보존을 명시한다. | W-1, W-2, W-3 | P3 | AC-1, AC-2, AC-3, AC-4, C-2, C-3, C-4 | `rg -n "session\.project|1KB|1024|review_rows|state-tool" opal/core/references/opal-pm.md` |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. 태스크 폴더 탐색이 워크트리 경계를 넘을 수 있음 | `--wt` 실행에서 허브의 tasks/.opal은 고정하고 소스 검증은 작업본에 남겨야 한다. | 다른 프로젝트의 미완료 상태가 브리핑에 섞이거나 작업본 검증 의미가 뒤집힐 수 있다. | W-2는 [MUST] worktree 허브 해석 규칙을 적용해 입력 프로젝트 루트만 탐색하고, W-3은 실제 작업본 소스와 허브 고정 데이터 경계를 테스트한다(`worktree.md` §허브 루트 해석 규칙) (→ D-3). |
| H-2. 기존 boot brief 소비자가 추가 키를 거부할 수 있음 | 기존 `show` 응답 키와 active 행 의미가 바뀌면 improve-tool·회귀 테스트가 깨진다. | 설치 후 세션 또는 메모리 자동화가 중단된다. | W-1은 기존 키를 삭제/개명하지 않고 `review_rows`만 additive로 추가하며, 기존 test_boot_brief와 memory-tool 회귀를 함께 실행한다(`memory_tool.py:1372-1467`) (→ D-7, D-9). |
| H-3. 플랫폼별 snippet drift | 한 플랫폼만 조회 순서·상한·조건이 다르면 AC-5가 실패한다. | 사용자별 부트 경험과 안전 경계가 달라진다. | W-3에서 4개 소스 본문을 parity 비교하고 설치 감사 명령을 통과시킨 뒤에만 W-4로 문서를 정합화한다(`scripts/tests/task113_bootstrap_audit.py:390-430`) (→ D-10). |

## Release and recovery

- 적용 순서: P1(W-1, W-2) 병렬 구현·단위검증 → P2(W-3) 4플랫폼 통합/감사 → P3(W-4) 공개 문서 정합성 → 허브에서 전체 회귀 검증. 설치 산출물은 기존 install 스크립트가 소스 bootstrapper를 읽는 경로로 재생성한다.
- 검증 범위: memory/state 결정론 단위 테스트, bootstrap parity·이벤트 경계 독립 테스트, 기존 memory/state/opal-agent 회귀 테스트를 구분해 실행한다. 브리핑은 read-only이며 상태·메모리 저장 포맷을 변경하지 않는다.
- 실측 경계: 성공 JSON과 합성 첫 응답 모두 UTF-8 1,024바이트 이하를 측정한다. 초과·파싱 실패·파일 부재는 해당 블록을 생략하고 기존 짧은 응답으로 종료한다.
- 실패 시: 설치·배포 전에는 W-3 변경을 되돌리고 기존 부트스트래퍼 소스와 회귀 테스트를 재실행한다. 배포 후 parity/상한 회귀가 발견되면 bootstrapper 소스의 신규 조회·렌더 블록만 제거해 기존 session.project 응답으로 즉시 복구하고, state/memory CLI의 additive 필드는 유지 또는 다음 수정에서 비활성화한다. 커밋은 사용자 명시 없이는 수행하지 않는다([MUST] `guards.md` §커밋 규칙).
