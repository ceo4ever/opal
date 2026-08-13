# DONE: 파이프라인 todo 미러 hook 강제 자동화

> 완료일: 2026-07-23 | 적용 스킬: opds (agentic) | 태스크: 076
> 상태: 완료 (S-9 L3 실증은 새 세션 후속 확인 — 캡틴)

## 1. 결과 요약

state 파이프라인 현황을 네이티브 todo 패널(TaskCreate/TaskUpdate)에 **결정론적으로 미러**하는 구조를 구현했다. 현행 `state.md` 산문 지시(PM이 매 이벤트마다 직접 호출 — 누락 빈발) 결함을 헌법 Core Stance "Enforce, don't just advise"에 따라 **hook 강제 트리거 + state-tool 페이로드 출력**으로 대체했다.

**동작 흐름**: state-tool init/advance/mark/block → `todo_mirror` 페이로드 출력 → PostToolUse hook이 감지·`additionalContext`로 지시+페이로드 주입 → PM이 TaskCreate(create)/TaskUpdate(update)로 기계적 릴레이. 태스크 시작 시 생성 → 단계마다 갱신 → CLOSE까지 유지.

**정직한 한계**: 네이티브 패널은 오직 LLM 도구 호출로만 기록되므로 hook·Python이 대신 호출 불가. 따라서 "완전 무개입 자동"이 아니라 **트리거·페이로드·타이밍의 결정론화 + PM 기계적 릴레이**다.

## 2. 변경 파일 (9종)

**신규**
- `opal/tools/state-tool/todo_mirror_hook.py` — PostToolUse 릴레이 헬퍼(stdin 파싱·state-tool 필터·additionalContext 출력·전 경로 fail-safe)
- `opal/tools/state-tool/tests/test_todo_mirror_hook.py` — 12건
- `scripts/merge-hooks.py` — 소유권-마커(`_opal_managed`) 기반 멱등 upsert
- `scripts/tests/test_merge_hooks.py` — 5건

**수정**
- `opal/tools/state-tool/state_tool.py` — `build_todo_mirror(state, action)` 헬퍼 + init/advance/mark/block ok()에 `todo_mirror=` (stdout 전용, state.json 미영속)
- `opal/tools/state-tool/tests/test_state_tool.py` — `TestTodoMirror` 7건
- `opal/core/hooks/claude-hooks.json` — PostToolUse(matcher Bash) 추가, 기존 SubagentStop/Stop 보존
- `scripts/install-mac.sh` — `merge_hooks_config` 인라인 python(이벤트 통째 교체=clobber) → `merge-hooks.py` 위임
- `opal/core/references/harness/state.md` — §파이프라인 todo 미러 hook 강제 재서술 + 변경이력 v1.5

## 3. 검증 결과

| 항목 | 결과 |
|------|------|
| 신규 단위 테스트 | 24건 전량 PASS (TestTodoMirror 7 + Hook 12 + merge-hooks 5) |
| 목표-커버 게이트 (dogfooding) | 수렴 PASS — coverage exit0 + evaluator 평균 2.0 |
| 076 회귀 | **0** (state-tool 261/264, 3건 사전결함은 073/075/034 기원) |
| 배포 검증 (실 `~/.claude/settings.json`) | ⭐ orca PostToolUse **보존** + OPAL upsert 공존 (clobber 해소 실증) |
| 배포본 state-tool | todo_mirror 5단계 출력 확인 |
| 배포본 hook | state-tool 이벤트에 additionalContext 주입 확인 |
| H-3 (영속 경계) | state.json에 todo_mirror 미영속 + schema 통과 |
| H-10 (교체) | prose-only 의존 잔존 0, SSOT 불변·능력감지 보존 |

## 4. 후속 항목

- **[핵심] S-9 (L3, H-4) 실증**: 새 Claude Code 세션에서 아무 태스크나 `//opds`로 시작 → 하단 todo 패널 단계 todo 생성·갱신·CLOSE까지 유지 + orca hook 유지 확인 (캡틴). hook의 additionalContext가 실제 PM의 TaskCreate 호출을 유발하는지 = 이 태스크 근본 성패 판정.
- **[별건] 073/075 기존 회귀**: `test_state_tool.py:_GROUP_A_SPECS` 기대값 stale (opd 15→16, opds 10→11 미갱신) → 3건 사전 실패. 076 범위 외이므로 미수정. 별도 후속(2줄 수정) 권고.
- **커밋**: 캡틴 지시 대기.

## 5. 근거

- 헌법 Core Stance "Enforce, don't just advise" (`~/.opal/PRINCIPLES.md`)
- state.md §파이프라인 todo 미러 (064 신설 prose → 076 hook 강제 정합)
- PLAN.md / TEST-SCENARIO.md / SCENARIO-GATE-1.md / AGENTIC-LOG.md
