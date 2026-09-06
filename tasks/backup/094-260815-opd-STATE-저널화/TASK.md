# TASK: STATE.md 파생 섹션 제거 — 저널로 재정의

> 작성일: 2026-08-15 | 작업 유형: 개선 | 적용 스킬: opd | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

STATE.md에서 `state.json`으로부터 파생되는 섹션(파이프라인 현황판 표·마커·현재 상태·다음 액션 자동 파생)을 전부 제거하여, STATE.md를 **도구가 담지 못하는 서술 정보만 보유하는 저널**로 재정의한다. 기계 상태의 SSOT는 `state.json` 단일로 확정한다.

## 배경

`state-tool` 도입(태스크 134) 이후 파이프라인 현황판의 SSOT는 `state.json`으로 이미 이전되었고, STATE.md의 표는 도구가 렌더한 미러로 강등되었다. 그러나 미러 파일이 SSOT 갱신을 차단하는 역방향 의존(`marker_missing`)이 남아 있고, 렌더·파싱 전용 코드가 `state_tool.py`에 계속 유지되고 있다. 이중 표현의 유지 비용이 미러의 효용을 초과한 상태다.

## 배경 분석 (대화에서 도출)

TASK 진입 전 대화에서 현행 구조를 실측했다.

### (1) STATE.md는 이미 미러로 강등되어 있다

- `state-tool/README.md:13`: "**SSOT**: `state.json` (마크다운 표는 도구가 자동 렌더한 미러)"
- LLM이 STATE.md를 실제로 Read하는 소비 지점은 **1건**뿐이다 — `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md:520` (세션 복원)
- `harness/state.md:57`: "소유자는 STATE.md 파일을 열지 않고도 하단 패널에서 진행 상황을 한눈에 본다" — 사람 소비 경로도 todo 미러로 이동 완료

### (2) 섹션별 성격 — 파생 3 / 원본 2

| 섹션 | 출처 | 성격 |
|------|------|------|
| 제목 · `## 현재 상태` | `state.json` `mode`/`rows`/`current_status` | 파생 |
| `## 파이프라인 현황판` (마커 포함) | `state.json` `rows[]` | 파생 |
| `## 다음 액션` 첫 줄 | `state.json` `next_action` | 파생 |
| `## 의사결정 로그` | STATE.md 고유 | **원본** |
| `## 블로커` | STATE.md 고유 (PM 수동 갱신) | **원본** |

- `state.json` 필드는 `task_id`/`skill`/`mode`/`schema_version`/`created_at`/`updated_at`/`current_status`/`rows`/`next_action`/`worktree` 10개다 (`opal/tools/state-tool/schema/state.schema.json`)
- 의사결정 로그·블로커에 대응하는 필드는 **존재하지 않는다** → 이 두 섹션은 STATE.md가 유일 저장소이며 제거 대상이 아니다

### (3) 제거 시 사라지는 부담

- `state_tool.py`(2,611줄)의 렌더·마커·파싱 전용 함수 **8개**: `load_state_md:219` / `save_state_md:227` / `render_pipeline_table:270` / `replace_pipeline_section:288` / `update_state_md_header:300` / `sync_state_md:365` / `parse_existing_state_md:1064` / `_build_new_state_md:1317`
- `marker_missing` 에러(`README.md:284`) — HTML 주석 마커 손실 시 `init`/`advance`/`mark`/`block`/`add-row` 전부 차단되는 **미러가 SSOT를 인질로 잡는 구조**
- `--import-existing` — 기존 STATE.md 표 흡수 전용 하위호환 경로

### (4) 개정 영향 범위

- 소스(`tasks/`·`backup/`·`docs/backup/` 제외) STATE.md 참조 **약 385건 / 84 파일** — 하네스·pilot 10종·에이전트 10종·brain 페이지·`docs/CONVENTIONS.md`·`docs/ARCHITECTURE.md`
  - **정정 이력**: TASK 작성 시점의 PM 추정치 754건은 오측이었다. macOS BSD grep이 출력 경로에 `./` 접두사를 붙이지 않아 `grep -v "^./tasks/"`·`grep -v "^./backup/"` 필터가 무효화되어 `backup/`(252건)과 태스크 아카이브(약 208건)가 전부 포함된 수치였다. ANALYSIS 단계 실측(385~387건)이 정확하며, 이 수치를 개정 모집단으로 확정한다 (→ D-11 `ANALYSIS.md` §3.2)
- 태스크 092에서 `--row` 45건이 `--task-step`으로 전환 완료되어 표 좌표 의존은 이미 상당 부분 해소된 상태다

### (5) 확인된 리스크 — 비Claude 플랫폼 가시성

- todo 미러는 `TaskCreate`/`TaskUpdate` **능력 감지 게이트**(`harness/state.md:64`)가 걸려 있어 Cursor·Gemini·Codex에서는 no-op이다
- 표가 사라지면 해당 플랫폼에서 진행 현황을 파일로 확인할 수단이 없어진다 → 대체 조회 경로의 명문화가 필요하다

## 확정된 설계 방향 (대화에서 합의)

1. **STATE.md 파일 자체는 삭제하지 않는다.** 의사결정 로그·블로커는 `state.json`에 대응 필드가 없어 삭제 시 유실되므로, 파일을 남기고 파생만 걷어낸다.
2. **경계는 "표"가 아니라 "파생 전체"로 긋는다.** 표만 제거하면 `sync_state_md`·`update_state_md_header`가 살아남아 부분 렌더 상태가 유지되고 코드 정리 효과가 반감된다.
3. **결과 정의**: STATE.md = 의사결정 로그 + 블로커 + 자유 기재 = **저널**. 기계 상태 조회는 `state-tool show`로 일원화한다.
4. **하위호환**: 기존 태스크(001~093)의 STATE.md는 소급 변경하지 않는다 (`harness/citation-rules.md` §5 레거시 호환 원칙 준용). 신규 태스크부터 신형 구조를 적용한다.

## 명확화 결과

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | STATE.md에서 `state.json` 파생 섹션(현황판 표·마커·현재 상태·다음 액션 파생)을 제거하고, 의사결정 로그·블로커만 남긴 저널로 재정의한다 | - | 배경 분석 (2) |
| 범위 | **포함** — `state_tool.py` 렌더·마커·파싱 경로 / `state.schema.json` / `state-tool/README.md` / 하네스 §3 · `harness/state.md` · `harness/state-template.md` / pilot 10종 `SKILL.md`+`pipeline.json` / 전문 에이전트 문서의 STATE.md 서술 / `docs/CONVENTIONS.md`·`docs/ARCHITECTURE.md` 해당 절 / 현황 조회 표준 경로 명문화 / **선재 결함 3건 동반 정정(R-9 — 에러 카탈로그 종수·SSOT 자기모순·marker_missing 트리거 목록, 소유자 승인 2026-08-16)** / **worktree 허브 자산 접근 규약(R-10 — 092 경로 계약의 코드 미인지, 소유자 승인 2026-08-16)** / **agentic 승인 계약 정합(R-11 — 모드 경계 상수·CLOSE 폴백·파생 신호 계산식·pilot 산문·하네스 경계 표, 소유자 승인 2026-08-16)**<br>**제외** — `state.json` `rows[]` 스키마 변경 / `--task-step` 주소 체계 / ~~todo 미러 파생 로직~~ **(R-11 편입으로 철회, 소유자 승인 2026-08-16 — 계산식만 변경하며 시그니처·반환 구조·영속 경계는 불변)** / 기존 태스크 STATE.md 소급 개정 / 파일명 변경(STATE.md 유지) / **G-6 교차 회귀 매트릭스·opdd·opwt 계약 서술 신규 집필(095 이월)** | `## 다음 액션` 섹션을 완전 제거할지, 자동 파생만 끊고 자유 기재 섹션으로 남길지 (PLAN에서 결정) | 배경 분석 (2)(4) |
| 제약 | ① `state.json`은 기존 스키마·`rows[]` 구조를 유지한다(교체 아님, 파생 제거만) ② 의사결정 로그·블로커는 **어떤 경우에도 유실 금지** ③ `state-tool` 서브명령의 stdout 응답 계약은 기존과 호환 유지 ④ 배포 경계 준수 — `~/.opal/` 직접 수정 금지, 프로젝트 소스 수정 후 install 재배포 ⑤ 플랫폼 분기 하드코딩 금지(능력 감지만 허용) | `--import-existing` 서브옵션을 제거할지 no-op으로 남길지 (PLAN에서 결정) | `.opal/AGENT.md` §금지사항 |
| 완료기준 | 아래 요구사항 **R-1~R-11** 전체의 AC를 충족하고, 신규 태스크 1건을 신형 구조로 완주하여 파이프라인이 정상 동작함을 실증한다<br>**정정 이력(2026-08-16)**: 최초 문안이 `R-1~R-8`이라 범위 편입된 R-9·R-10이 완료기준에서 누락돼 있었다(→ D-15 §6-2 지적). R-11 편입과 함께 일괄 정정한다 | - | 요구사항 절 |

## 요구사항

- [ ] **R-1. STATE.md 파생 섹션 제거**
  - 무엇을: `## 파이프라인 현황판` 표 + `<!-- pipeline:start -->`/`<!-- pipeline:end -->` 마커 + `## 현재 상태` 4줄 + `## 다음 액션` 자동 파생을 STATE.md 생성·갱신 산출물에서 제거
  - 어디에: `opal/tools/state-tool/state_tool.py` (`_build_new_state_md`·`sync_state_md`·`render_pipeline_table`·`replace_pipeline_section`·`update_state_md_header`)
  - 왜: 확정 방향 §2 — 파생을 전부 걷어내야 렌더 동기화 코드가 소멸한다
  - AC: (a) **구형 잔존 0** — 신규 `state init` 산출 STATE.md에 `pipeline:start` 마커·현황판 표 헤더(`| # | 단계 | 항목 |`)·`## 현재 상태`가 0건 (b) **신형 채택** — 신규 STATE.md가 `## 의사결정 로그`·`## 블로커`를 포함하고, `advance`/`mark`/`block` 호출 후에도 두 섹션이 보존됨을 실행 증거로 확인

- [ ] **R-2. 의사결정 로그·블로커 보존 검증**
  - 무엇을: 파생 제거 후에도 의사결정 로그 자동 추가(`--force` 시 기재)와 블로커 수동 기재가 정상 동작함을 보장
  - 어디에: `state_tool.py` 의사결정 로그 기재 경로 + `harness/state-template.md`
  - 왜: 제약 ② — 두 섹션은 `state.json`에 대응 필드가 없어 유실 시 복구 불가
  - AC: 의사결정 로그 기재 트리거(**`mark --auto-pass --note` / `mark --as-worker --force --note` / `gate_artifact_force` 우회** 3종) 각각에서 STATE.md `## 의사결정 로그` 표에 행이 1건 추가되고, 기존 행이 전건 보존된다
  - **AC 정정 이력 (2026-08-16, EXECUTE Step 0 RED에서 검출)**: 최초 문안은 트리거를 `mark --force --note`로 기재했으나 **코드 실측 결과 존재하지 않는 경로**였다. `cmd_mark`가 `decision`을 세팅하는 트리거는 위 3종뿐이며(`state_tool.py:1615-1634`), 일반 `--force`(비워커·비게이트)와 `cmd_status`/`cmd_block`/`cmd_add_row`는 `decision=None`으로 호출한다(grep 실측 0건). 트리거를 신설하는 것은 PLAN §3.1.2 "전량 존치" 결정과 헌법 §3(Surgical Changes)에 반하므로, **AC를 실재 트리거로 교정**한다 — 검증 대상(재배선 후 로그 무손실)은 동일하다

- [ ] **R-3. `marker_missing` 에러 제거**
  - 무엇을: 마커 부재로 `init`/`advance`/`mark`/`block`/`add-row`를 차단하던 게이트와 에러 코드를 제거
  - 어디에: `state_tool.py` 마커 검사 경로 + `state-tool/README.md` 에러 카탈로그
  - 왜: 배경 분석 (3) — 미러가 SSOT를 인질로 잡는 역방향 의존 해소
  - AC: (a) STATE.md를 삭제하거나 임의 편집한 상태에서 `advance`/`mark`가 정상 성공한다 (b) README 에러 카탈로그에서 `marker_missing` 행이 제거되고 총 종수가 정합하게 갱신된다

- [ ] **R-4. `--import-existing` 경로 정리**
  - 무엇을: 기존 STATE.md 표 파싱(`parse_existing_state_md`) 의존 옵션의 거취를 확정하고 반영
  - 어디에: `state_tool.py` + `state-tool/README.md` §1 init
  - 왜: 표가 사라지면 파싱 대상 자체가 없어져 옵션이 무의미해진다
  - AC: 제거 시 — 옵션 지정 호출이 명확한 에러/경고를 반환하고 README에서 삭제됨. 유지(no-op) 시 — README에 no-op 사유가 명시되고 호출이 실패하지 않음. 둘 중 확정된 쪽이 코드·문서에 일관 반영

- [ ] **R-5. 현황 조회 표준 경로 명문화**
  - 무엇을: 파이프라인 현황 조회의 표준 경로를 `state-tool show`로 지정하고, 세션 복원 절차를 STATE.md Read → `show` 호출로 교체
  - 어디에: `opal/core/references/harness/state.md` §세션 복원 + `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md:520`
  - 왜: 배경 분석 (5) — 비Claude 플랫폼에서 표 소멸 시 대체 조회 수단이 필요하다
  - AC: (a) 구형 잔존 0 — "STATE.md를 Read하여 재개" 서술이 0건 (b) 신형 채택 — 세션 복원 절차가 `show` 호출로 기술되고, 실제 호출이 현황을 반환함을 실행 증거로 확인

- [ ] **R-6. 하네스 SSOT 개정**
  - 무엇을: STATE.md의 역할 정의를 "파이프라인 현황판"에서 "저널"로 개정하고, 파생 섹션 관련 서술을 제거
  - 어디에: `opal/core/references/opal-harness.md` §3 / `harness/state.md` / `harness/state-template.md`
  - 왜: 확정 방향 §3 — 규칙 SSOT가 신형 구조를 정의해야 pilot·에이전트가 상속한다
  - AC: 3개 문서에서 (a) 현황판 표 템플릿·마커 명세·`## 현재 상태` 템플릿이 0건 (b) 저널 구조(의사결정 로그·블로커)와 `show` 조회 경로가 명시됨

- [ ] **R-7. pilot·에이전트 문서 정합화**
  - 무엇을: pilot 10종 `SKILL.md`와 전문 에이전트 문서에서 STATE.md 현황판 관련 서술을 신형 구조로 교체
  - 어디에: `opal/skills/opal-pilot-*/SKILL.md` (+`references/pipeline.json` 영향 시) / `opal/agents/*/AGENT.md`
  - 왜: 배경 분석 (4) — SSOT만 고치고 소비처를 두면 문서·동작 불일치가 남는다
  - AC: (a) 구형 잔존 0 — "STATE.md 마크다운 표 직접 편집 금지"류 서술 중 표 존재를 전제한 문구가 0건 (b) 신형 채택 — `state-tool` 호출 규율(도구로만 상태 변경)은 유지되며 표 전제만 제거됨

- [ ] **R-9. 선재 결함 3건 동반 정정** (ANALYSIS 검출 → 소유자 승인으로 범위 편입, 2026-08-16)
  - 무엇을: ① 에러 카탈로그 3중 불일치(코드 44종 / `README.md:279` 39종 / `opal-harness.md:181`·`harness/state.md:21` 23종)를 실측 기준으로 통일 ② 하네스 SSOT 자기모순(`harness/state.md:66` "STATE.md/state-tool이 유일한 SSOT" ↔ `state-tool/README.md:13` "SSOT: state.json") 해소 ③ `README.md:284` `marker_missing` 트리거 목록 오류(`init` 오기재 · `status`/`gate-pass` 누락) 정정
  - 어디에: `opal/tools/state-tool/README.md` / `opal/core/references/opal-harness.md` / `opal/core/references/harness/state.md`
  - 왜: 세 결함 모두 R-3·R-6이 이미 여는 파일에 있고, `marker_missing` 제거로 에러 종수가 어차피 재산정된다. SSOT 자기모순은 이번 태스크의 전제("state.json이 SSOT")와 정면 배치되므로 방치 시 개정 결과가 문서상 모순된다 (→ D-11 `ANALYSIS.md` §1.3.5 문서/코드 불일치, §5 R-C/R-D/R-E)
  - AC: (a) 에러 종수가 코드 실측값 기준으로 3개 문서에서 **동일 수치**로 일치 (b) "STATE.md가 SSOT"류 서술 잔존 0건, `state.json` 단일 SSOT 서술로 통일 (c) `marker_missing` 관련 서술이 제거되거나(R-3 결과) 잔존 시 실제 트리거 명령과 일치

- [ ] **R-10. worktree 허브 자산 접근 규약** (EXECUTE Step 0에서 검출 → 소유자 승인으로 범위 편입, 2026-08-16)
  - 무엇을: ① `tests/test_state_tool.py:3163`의 `repo_root = _TOOL_DIR.parents[2]`를 **기존 `find_project_root()` 패턴**(`.opal/MEMORY.json` 보유 조상 탐색, `state_tool.py:565`)으로 교체하여 worktree에서도 허브 `tasks/`를 찾게 한다 ② `opal/core/references/opal-harness.md` §2.5에 규약 1줄 추가 — "코드에서 허브 고정 자산(`tasks/`·`.opal/`)에 접근할 때는 레포 루트 상대 경로가 아니라 허브 탐색 헬퍼를 사용한다"
  - 어디에: `opal/tools/state-tool/tests/test_state_tool.py` / `opal/core/references/opal-harness.md` §2.5
  - 왜: 092가 "`tasks/`는 분기하지 않고 허브에 고정"이라는 경로 계약을 신설했으나(`opal-harness.md` §2.5), **코드가 그 계약을 모른 채 "레포 루트 = 작업 루트"를 가정**한다. worktree에서 이 등식이 깨져 `TestVerify::test_verify_passes_own_test_scenario_md`가 구조적으로 실패하며, 이것이 R-8 AC(b)의 "잔존 테스트 전건 통과(fail 0)"를 막는다. 예외를 달면 회귀 판정이 흐려져 진짜 회귀를 "그 환경 실패겠지"로 넘길 여지가 생긴다
  - **[MUST] 신규 헬퍼를 만들지 않는다** — `find_project_root()`(088 도입)가 이미 올바른 패턴이며 worktree에서 허브를 정확히 반환함을 실측 확인했다. 새 폴백(`git rev-parse --git-common-dir` 등) 신설은 중복 구현이며 헌법 §2(단일 용도 추상화 금지) 위반이다
  - AC: (a) worktree에서 `pytest tests/ -q` 실행 시 `TestVerify::test_verify_passes_own_test_scenario_md`가 **통과**한다 (b) 허브(전체 체크아웃)에서도 동일하게 통과한다 — 양쪽 환경 모두에서 동작 (c) `opal-harness.md` §2.5에 허브 자산 접근 규약이 명시되어 재발이 문서로 차단된다 (d) 신규 경로 해석 헬퍼가 추가되지 않았음(`git diff`로 확인)

- [ ] **R-11. agentic 승인 계약 정합 — 모드 경계·CLOSE 폴백·파생 신호·pilot 산문** (별도 세션 진단 → 소유자 승인으로 범위 편입, 2026-08-16)
  - 무엇을: 093이 집행 층에 일원화한 "사용자 확인 행 자동 승인 계약"을 ① 모드 경계 상수(G-1) ② CLOSE 게이트 폴백(G-2) ③ 파생 신호 2종(G-3) ④ pilot 산문 7건(G-4) ⑤ 하네스 모드 경계 표(G-5)에 정합시킨다. 변경 명세 5건의 상세는 **D-15 `R-11-요청서.md` §2**가 SSOT다
  - 어디에: `opal/tools/state-tool/state_tool.py`(G-1·G-2·G-3) / `opal/skills/opal-pilot-{dev,dev-short,dev-wireframe,project}/SKILL.md`(G-4, 7건) / `opal/core/references/opal-harness-semi-agentic.md` §3(G-5)
  - 왜: 093이 승인 주체를 PM→도구로 옮겼으나 표시 층·산문 층이 여전히 PM을 주체로 서술한다. **094 R-5가 `show`를 기계 상태의 유일 근거로 승격하므로, 값을 바로잡지 않으면 094가 만든 규약이 잘못된 값을 가리킨다** (→ D-15 §0)
  - **PM 실측 검증 (2026-08-16)**: ① `MODE_BOUNDARY_STAGES`에 `DICT`·`MODEL`·`DDL/MIGRATION` 부재 확인, opdd `pipeline.json`에 해당 3 stage의 `user_confirm` 행 실재 확인 → **semi-agentic(기본 모드)에서 설계 확정 3건이 소유자 미노출 통과**, 헌법 Core Stance("user sovereignty") 직접 위반 ② opgc `pipeline.json` 7행 전수 확인 — `user_confirm` 행 **0개**인데 `close.done_md` 존재 → `--force` 없이 종료 불가 확인
  - **[MUST] 신규 상수·신규 분기 금지** — G-1·G-3은 093이 만든 단일 판정 함수 `can_auto_approve_user_confirmation()`을 재사용한다(헌법 §2). `state.json` `next_action` **필드·스키마 불변**(제약 ①), `build_todo_mirror` **시그니처·반환 구조 불변**, stdout 페이로드만 변경(제약 ③)
  - AC: (a) agentic 모드로 pilot 10종 각 `pipeline.json`을 전 행 순회할 때 `show --format json`의 `next_action`이 "사용자 확인"을 가리키지 않는다 — **단 CLOSE 진입 직전은 예외**(소유자 승인이 실제로 필요한 유일 지점이며, 코드 실측상 축1이 무조건 거부한다. 요청서 원문의 "어느 시점에도"는 이 예외를 누락한 부정확한 문언이므로 정정. `SCENARIO-GATE-3.md` ⑥ 비차단 지적) (b) semi-agentic에서 opdd의 `dict`/`model`/`ddl_migration` 사용자 확인 행이 자동 승인되지 **않고** `user_confirmation_required`로 거부된다 (c) pilot 10종 전부가 `--force` 없이 CLOSE 첫 행 진입에 도달 가능하다(opgc 포함) (d) `build_todo_mirror`가 자동 승인 예정 사용자 확인 행을 중립 처리하여 작업·게이트가 완료된 단계가 `completed`로 렌더된다 (e) **구형 잔존 0** — pilot SKILL.md에서 모드 무분기 `사용자 확인 (P-5)` 명령형 주석 0건 / **신형 채택** — 자동 승인 구간에서 도구가 처리함이 명시됨 (f) 하네스 모드 경계 표에 pilot 10종이 전부 등재되고 각 경계가 `MODE_BOUNDARY_STAGES`·해당 `pipeline.json`과 모순되지 않는다
  - **095 이월 (이번 범위 아님)**: G-6 pilot 10종 × 3모드 교차 회귀 매트릭스 게이트 / opdd·opwt의 093 계약 서술 신규 집필(두 pilot은 언급 0건이라 문장 교체가 아닌 신규 작성) (→ D-15 §4)

- [ ] **R-8. 신형 구조 실동작 실증**
  - 무엇을: 신규 태스크 1건을 신형 구조로 `init` → `advance` → `mark` → `block` → `add-row`까지 실행하여 파이프라인 정상 동작을 확인
  - 어디에: `opal/tools/state-tool/tests/` + 실행 증거
  - 왜: 헌법 §4 — 완료는 문서가 아니라 검증된 동작이다
  - AC: (a) 5개 서브명령이 전부 `ok: true` 반환 (b) **회귀 커버리지 유지** — 잔존 테스트 전건 통과(fail 0) AND 삭제된 테스트가 각각 PLAN 결정(D-1/D-2/R-3)에 1:1 대응함이 증명됨 AND 신규 기능 5종(저널 템플릿·의사결정 로그 무손실·`show` 렌더 단일화·import 거부·에러 카탈로그 정합) 각각에 대응하는 신규 테스트 존재 (c) `show --format md`/`json`이 현황을 정상 반환
  - **AC(b) 개정 이력 (소유자 판정 2026-08-16)**: 최초 문안은 "기존 pass 수 이상(308)"이었으나, D-1·D-2·R-3으로 테스트 25건이 **정당하게 삭제**되는 상황에서 숫자 하한이 **padding 테스트를 유도**하는 역효과가 확인되어 성질 기반으로 전환했다. 헌법 §4("완료는 검증된 동작") 취지상 숫자 채우기용 테스트는 검증이 아니다. **[MUST] passed 수를 채우기 위한 테스트 작성 금지** — 최종 passed 수와 삭감 내역은 DONE.md에 보고한다. 변경 전 기준선(308 passed + 32 subtests)은 참고값으로만 유지한다

## 제약 조건

- `state.json` 스키마와 `rows[]` 구조는 변경하지 않는다 — 이번 작업은 파생 제거이며 SSOT 교체가 아니다
- 의사결정 로그·블로커 데이터는 어떤 경로에서도 유실되어서는 안 된다
- `state-tool` 서브명령의 stdout 응답 계약(`ok`/`command`/`todo_mirror`/`gate_checklist` 등)은 기존 소비자와 호환을 유지한다
- 배포 경계 준수 — `~/.opal/` 직접 편집 금지, 프로젝트 소스 수정 후 install로 재배포한다
- 플랫폼 분기 하드코딩 금지 — 비Claude 대응은 능력 감지 또는 공통 경로(`show`)로 해결한다
- 기존 태스크(001~093)의 STATE.md는 소급 변경하지 않는다
- 커밋은 소유자가 명시 요청할 때만 수행한다

## 기술 스택

- Python 3 — `opal/tools/state-tool/state_tool.py` (2,611줄), pytest 기반 `tests/`
- Node.js — `opal/tools/date/date.js`, `skill-registry`
- Bash — `run.sh` 래퍼
- Markdown — 하네스·스킬·에이전트 문서 (프레임워크 산출물 본체)
- JSON Schema — `schema/state.schema.json`, `schema/pipeline-spec.schema.json`

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | opal-harness.md | `opal/core/references/opal-harness.md` | §3 State 정의 — 개정 대상 SSOT |
| D-2 | 설계 | state.md | `opal/core/references/harness/state.md` | STATE.md 이벤트 표·todo 미러·세션 복원 — 개정 대상 |
| D-3 | 설계 | state-template.md | `opal/core/references/harness/state-template.md` | STATE.md 템플릿·마커 명세 — 개정 대상 |
| D-4 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py` | 렌더·마커·파싱 함수 8개 — 제거 대상 |
| D-5 | 설계 | state-tool README | `opal/tools/state-tool/README.md` | 서브명령 명세·에러 카탈로그 39종 |
| D-6 | 설계 | state.schema.json | `opal/tools/state-tool/schema/state.schema.json` | state.json 필드 10개 — 파생/원본 판별 근거 |
| D-7 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 프로젝트 컨벤션 — STATE.md 관련 규약 |
| D-8 | 설계 | ARCHITECTURE.md | `docs/ARCHITECTURE.md` | 아키텍처 문서 — STATE.md 위치 서술 |
| D-9 | 설계 | verification-loop-guide.md | `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` | 세션 복원 절차(:520) — 유일한 STATE.md Read 소비 지점 |
| D-15 | 설계 | R-11 편입 요청서 | `tasks/094-260815-opd-STATE-저널화/R-11-요청서.md` | R-11 변경 명세 5건(G-1~G-5)·실측 재현·095 이월 항목 SSOT |
| D-10 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | §5 레거시 호환 원칙 — 하위호환 정책 근거 |
