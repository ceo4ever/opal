# TASK: 파이프라인 todo 미러 hook 강제 자동화

> 작성일: 2026-07-23 | 작업 유형: 개선 | 적용 스킬: opds | 모드: agentic
> 입력: 사용자 요청 (이 세션 진단·설계 대화)
> 출력: TASK.md

## 작업 목표

state 파이프라인 현황을 네이티브 todo 패널(TaskCreate/TaskUpdate)에 **결정론적으로 미러**한다 — 태스크 시작 시 자동 생성, 매 state-tool 이벤트마다 자동 갱신, CLOSE까지 유지. 현행 prose 의존(PM 누락) 결함을 PostToolUse hook 강제 트리거로 해소한다.

## 배경

`state.md §파이프라인 todo 미러`(064 신설)는 "PM이 매 state-tool 이벤트 직후 TaskCreate/TaskUpdate를 직접 호출"하라는 **산문 지시**로만 존재한다. 헌법 Core Stance "Enforce, don't just advise"를 위반하며, state-tool에는 todo 관련 코드가 0줄이다. 결과적으로 PM이 잊으면 미러가 갱신되지 않아 "작동이 잘 안 됨" 상태다(agentic·다중 세션에서 특히 빈발).

## 배경 분석 (대화에서 도출)

- **state-tool 현황**: `state_tool.py`·README에 `todo`/`mirror`/stage 집계 출력 전무 (grep 확인). 미러 구동 코드 없음.
- **sspec 위치**: 미러 규칙은 `opal/core/references/harness/state.md` line 52~72(§파이프라인 todo 미러)에만 존재. 어떤 pilot SKILL도 이를 강제하지 않음.
- **플랫폼 제약(하드 제약)**: 네이티브 todo/Task 패널은 오직 LLM의 `TaskCreate`/`TaskUpdate` 도구 호출로만 기록된다. Python(state-tool)·shell hook은 그 도구를 **대신 호출 불가**. → 완전 무개입(zero-LLM) 자동은 불가능.
- **달성 가능 최대치**: PostToolUse hook으로 트리거·페이로드·타이밍을 결정론화하고, PM의 몫을 "주입된 페이로드를 그대로 도구로 전달"하는 기계적 1스텝으로 축소 = **사실상 자동**.
- **hook 배포 로직 결함**: `install-mac.sh merge_hooks_config`는 `data['hooks'][event] = rules`로 **이벤트 통째 교체**. `~/.claude/settings.json`에 이미 존재하는 orca PostToolUse hook을 clobber함. 배포 타깃은 `$USER_HOME/.claude/settings.json`(line 1236, 전역 — OPAL 2-Layer 정합).
- **능력 감지 게이트**: state.md는 이미 "네이티브 할일 도구 노출 세션에서만 수행, 없는 플랫폼은 스킵"을 능력 감지로 규정(하드코딩 분기 아님).

## 확정된 설계 방향 (대화에서 합의)

1. **state-tool → todo_mirror 페이로드 출력**: init/advance/mark/block JSON 출력에 stage 그룹핑 + 파생 상태(전부✅=completed / 일부·🔄=in_progress / 전부⬜=open) todo 페이로드를 결정론 생성.
2. **PostToolUse hook**: state-tool 호출 직후 발동 → todo_mirror 페이로드 + "이 todo를 생성/갱신하라" 지시를 결정론 주입 → PM이 TaskCreate(init)/TaskUpdate(이벤트) 기계적 릴레이.
3. **merge_hooks_config 개선**: "이벤트 통째 교체" → **소유권-마커 기반 멱등 upsert**(외부 hook 보존 / OPAL 소유 항목만 제거 후 append / N회 재배포 멱등).
4. **state.md 사양 정합**: prose 지시 → tool-강제 트리거 방식으로 갱신(SSOT 불변·읽기전용 거울 원칙 유지).

## 명확화 결과

> TASK 4요소를 잠근다.

| 요소 | 확정값 | 미확정 | 의존 사실 |
|------|--------|--------|----------|
| 목표 | state 파이프라인 현황을 네이티브 todo 패널에 결정론 미러(시작 시 자동생성·이벤트마다 갱신·CLOSE까지 유지). prose 의존을 hook 강제 트리거로 대체 | - | state.md §파이프라인 todo 미러(064) |
| 범위 | 포함: (1) state-tool init/advance/mark/block에 todo_mirror 페이로드 출력 (2) claude-hooks.json에 PostToolUse hook 추가(state-tool 매처, 페이로드+지시 주입) (3) merge_hooks_config 소유권-마커 멱등 upsert 개선(clobber 해소) (4) state.md 사양 정합 (5) 테스트 + install 재배포. 제외: 네이티브 패널 직접 조작(플랫폼상 불가), 비지원 플랫폼(능력감지 스킵), 075 관련 파일 일체 | - | 이 세션 확정 방향 |
| 제약 | `~/.opal/` 직접수정 금지(소스만·install 배포) / 플랫폼 독립성(능력감지, 하드코딩 분기 금지) / SSOT 불변(state-tool=SSOT, todo=읽기전용 거울) / 멱등(재배포 중복·clobber 0) / 최종 도구호출은 LLM 몫(hook은 트리거·데이터까지 — 완전무개입 아님, 정직한 한계) / 커밋·install은 캡틴 지시 시만 / @header·변경이력 준수 | - | 헌법 Core Stance, 배포 경계 |
| 완료기준 | (a) state-tool 이벤트 4종 todo_mirror 결정론 출력 검증 (b) merge_hooks_config orca PostToolUse 보존+OPAL upsert+N회 멱등 검증 (c) 배포 후 새 세션에서 state-tool 호출 시 todo 지시 주입 실증 (d) state-tool 기존 테스트 전량 PASS(회귀 0) (e) 교체: prose-only 미러 잔존 검증 + hook 강제 트리거 채택 실증 | - | 헌법 §4 증거 기반 |

## 요구사항

- [ ] **R-1 state-tool todo_mirror 페이로드 출력**
  - 무엇을: init/advance/mark/block JSON 출력에 `todo_mirror` 필드(stage 그룹 + 파생 상태 + todo id/content/status) 추가
  - 어디에: `opal/tools/state-tool/state_tool.py` (해당 서브명령 출력부)
  - 왜: 확정 방향 §1 — PM이 STATE.md를 수동 그룹핑·집계하지 않도록 결정론 페이로드 제공
  - AC: 4개 서브명령 각각 stage 단위 todo 페이로드를 출력하고, 파생 상태 규칙(전부✅=completed/일부·🔄=in_progress/전부⬜=open)이 단위 테스트로 검증된다

- [ ] **R-2 PostToolUse hook 추가**
  - 무엇을: state-tool run.sh 호출을 매칭하는 PostToolUse hook 정의 — todo_mirror 페이로드 + "생성/갱신 지시"를 세션에 주입
  - 어디에: `opal/core/hooks/claude-hooks.json`
  - 왜: 확정 방향 §2 — 결정론 트리거로 prose 누락 결함 제거
  - AC: state-tool 호출 직후 hook이 발동해 todo 지시가 주입되며, 비state-tool 호출에는 발동하지 않는다

- [ ] **R-3 merge_hooks_config 멱등 upsert 개선**
  - 무엇을: "이벤트 통째 교체" → 소유권-마커 기반 upsert(외부 항목 보존, OPAL 항목만 제거 후 append)
  - 어디에: `scripts/install-mac.sh` merge_hooks_config
  - 왜: 배경 분석 — orca 등 기존 PostToolUse hook clobber 방지 + 재배포 멱등
  - AC: 기존 orca PostToolUse가 보존되고, OPAL 항목이 upsert되며, N회 재실행 시 결과가 동일(중복 0)함이 검증된다

- [ ] **R-4 state.md 사양 정합**
  - 무엇을: §파이프라인 todo 미러를 prose 지시 → tool-강제 트리거 방식으로 갱신(SSOT 불변·읽기전용 거울 원칙 유지), 변경이력 행 추가
  - 어디에: `opal/core/references/harness/state.md`
  - 왜: 확정 방향 §4 — 문서-구현 정합
  - AC: 미러 규칙이 hook 강제 방식으로 서술되고, SSOT 불변·능력감지 게이트 문구가 보존된다

- [ ] **R-5 교체 검증 (구형 제거 + 신형 채택)**
  - 무엇을: prose-only 의존 서술이 신방식으로 대체되었는지 + hook 강제 트리거가 실제 채택·동작하는지 실증
  - 어디에: 태스크 산출물(TEST-SCENARIO 결과)
  - 왜: 교체형 목표 [MUST] — 구형 잔존0 + 신형 채택 검증
  - AC: prose-only 미러 의존이 잔존하지 않고(문서·코드), 배포 후 새 세션에서 hook 트리거로 todo가 생성/갱신되는 시나리오가 검증된다

- [ ] **R-6 회귀 0**
  - 무엇을: state-tool 기존 테스트 전량 PASS + install 문법 무손상
  - 어디에: `opal/tools/state-tool/tests/`, `scripts/install-mac.sh`
  - 왜: 무손상 보장
  - AC: 기존 state-tool 테스트 스위트 전량 PASS, install bash 문법 검사 통과

## 제약 조건

- `~/.opal/` 직접 수정 금지 — 프로젝트 소스만 수정 후 install 재배포.
- 플랫폼 독립성 — 능력 감지 게이트 유지, 하드코딩 플랫폼 분기 추가 금지.
- SSOT 불변 — STATE.md/state-tool이 진행 SSOT, todo는 읽기 전용 거울.
- 멱등 — 재배포 시 hook 중복·clobber 0.
- 정직한 한계 — 최종 TaskCreate/TaskUpdate 호출은 LLM 몫(hook은 트리거·데이터까지). 완전 무개입 아님.
- 커밋·install은 캡틴 명시 지시 시만. @header·변경이력 준수.

## 기술 스택

- Python 3 (state-tool), Bash (install-mac.sh), JSON (claude-hooks.json), Markdown (state.md). 신규 의존성 없음.

## 관련 문서

| # | 유형 | 문서 | 경로 | 참조 이유 |
|---|------|------|------|----------|
| D-1 | 설계 | state.md (todo 미러 SSOT) | `opal/core/references/harness/state.md` | §파이프라인 todo 미러 — 정합 대상(R-4) |
| D-2 | 소스 | state-tool | `opal/tools/state-tool/state_tool.py` | todo_mirror 출력 추가 대상(R-1) |
| D-3 | 소스 | install merge_hooks_config | `scripts/install-mac.sh` | 멱등 upsert 개선 대상(R-3) |
| D-4 | 소스 | hook 정의 | `opal/core/hooks/claude-hooks.json` | PostToolUse 추가 대상(R-2) |
| D-5 | 설계 | 헌법 | `~/.opal/PRINCIPLES.md` | "Enforce, don't just advise" 근거 |
