# PLAN: 파이프라인 todo 미러 hook 강제 자동화

> 작성일: 2026-07-23 | 입력: TASK.md (ANALYSIS.md 없음 — Short Task, 코드 직접 분석)
> 모드: Multi-Feature (4개 기능) | 실행 모드: 복잡

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

state 파이프라인 현황을 네이티브 todo 패널(TaskCreate/TaskUpdate)에 **결정론적으로 미러**한다. 현행은 `state.md §파이프라인 todo 미러`의 **산문 지시**(PM이 매 이벤트마다 직접 호출)로만 존재해(→ D-1 §파이프라인 todo 미러) PM 누락 시 갱신이 끊긴다. 이를 (1) state-tool이 파생 상태를 담은 `todo_mirror` 페이로드를 출력하고 (2) PostToolUse hook이 state-tool 호출을 트리거로 그 페이로드+지시를 세션에 결정론 주입하는 구조로 전환한다. 헌법 Core Stance "Enforce, don't just advise"를 집행한다 (→ D-5).

### 1.2 정직한 한계 (설계 전제)

네이티브 todo 패널은 **오직 LLM의 TaskCreate/TaskUpdate 도구 호출로만** 기록된다. Python(state-tool)·shell(hook)은 그 도구를 대신 호출할 수 없다(→ D-9 §배경 분석). 따라서 설계 목표는 "완전 무개입 자동"이 아니라 **"hook으로 트리거·페이로드·타이밍을 결정론화 + PM은 주입된 페이로드를 그대로 도구로 전달하는 기계적 1스텝"**이다. 이 PLAN은 이 제약 위에서 설계한다.

### 1.3 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | state-tool `todo_mirror` 페이로드 출력 | R-1 | P0 | 없음 |
| F-002 | PostToolUse hook + 미러 릴레이 헬퍼 스크립트 | R-2 | P0 | F-001 |
| F-003 | `merge_hooks_config` 소유권-마커 멱등 upsert | R-3 | P0 | 없음 |
| F-004 | `state.md` 사양 정합 (prose → hook 강제) | R-4 | P1 | F-001, F-002 |

> **검증 요구사항 (별도 구현 기능 아님)**: R-5(교체 검증 — 구형 prose 잔존0 + 신형 hook 채택 실증)와 R-6(회귀 0 — state-tool 기존 테스트 전량 PASS + install 문법 무손상)는 §5 QA 매트릭스·§3.N.5 테스트 시나리오·리스크 가설 표로 커버한다.

### 1.4 기능 의존 그래프 (ASCII)

```
F-001 (payload) ─┬─ F-002 (hook) ──┐
                 └─────────────────┴─ F-004 (state.md 정합)
F-003 (merge upsert) ── (독립, install 배포 경로)
```

### 1.5 PLAN 설계에 영향을 주는 [MUST] 제약 (인용)

- [MUST] `~/.opal/PRINCIPLES.md` Core Stance: "Enforce, don't just advise: if a rule must always hold, a tool gates it — not prose." (→ D-5) — 이 태스크의 근본 동기.
- [MUST] `docs/CONVENTIONS.md` §구현 규칙 배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `agents/`, `community-skills/`, `scripts/`)에서 수행한다." (→ D-6) — 모든 변경은 소스에서, install 재배포는 별도.
- [MUST] `docs/CONVENTIONS.md` §구현 규칙 플랫폼 분기 격리: "스킬·에이전트 본문에 플랫폼 조건문을 추가하지 않는다 (행위는 플랫폼 독립적으로 기술하고, 도구명은 어댑터에 위임)." (→ D-6) — Claude 전용 hook은 어댑터 계층(claude-hooks.json)에만 격리.
- [MUST] `docs/CONVENTIONS.md` §구현 규칙 @header: "코드 파일을 생성·수정할 때 파일 상단에 @header 블록을 작성한다." (→ D-6) — 신규 `.py` 파일에 @header 필수.
- [MUST] `docs/CONVENTIONS.md` §구현 규칙 State 관리: "파이프라인 STATE.md 행 상태(⬜/🔄/✅) 변경은 `state-tool`로만 수행한다." (→ D-6) — todo는 읽기 전용 거울, SSOT는 state-tool.
- [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 '## 변경이력' 표에 행을 추가한다. 일시는 `YYYY-MM-DD HH:mm`(KST)." (→ D-6) — state.md·README 변경이력 갱신.
- [MUST] `opal/tools/state-tool/schema/state.schema.json` §root: `"additionalProperties": false` (→ D-7:7) — `todo_mirror`는 **stdout ok() 페이로드에만** 담고 state.json에 영속 금지(스키마 위반 회피).

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨. 특히 H-4가 이 태스크의 핵심 가설이다("hook이 실제로 PM의 TaskCreate 호출을 유발하는가").

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-001 `ok()` 출력 계약 | init/advance/mark/block 응답 dict에 `todo_mirror` 키 신설 → 기존 응답을 정확 dict 비교하던 소비자/테스트가 깨짐 | P1 | L1(기존 state-tool 테스트 전량 회귀 PASS) | S-회귀-1 |
| H-2 | F-001 파생 규칙 | `na`(agentic 사용자확인 auto-na)·`failed` 상태를 단계 집계에 잘못 반영 → init 직후 미착수 단계가 `in_progress`로 오판 / 블로커 단계 상태 오판 | P1 | L1(단위 — na 중립·failed→in_progress·전부pending→pending·전부done→completed) | S-F001-2,3,4,5 |
| H-3 | F-001 영속 경계 | `todo_mirror`를 `state.json`에 저장하면 schema `additionalProperties:false` 위반(→ D-7:7) | P1 | L1(save_state_json 결과에 todo_mirror 부재 검증 + schema validate) | S-F001-6 |
| **H-4** | **F-002 hook→도구 유발** | **hook의 `additionalContext` 주입이 실제로 PM의 TaskCreate/TaskUpdate 호출을 유발하는지 — Claude Code PostToolUse 계약 의존, 플랫폼 동작 불확실** | **P0** | **L2(스크립트가 올바른 `hookSpecificOutput.additionalContext` JSON 스키마·페이로드 출력) + L3(실 배포 새 세션에서 state-tool 호출→todo 생성/갱신 실증)** | **S-F002-live-1** |
| H-5 | F-002 stdout 파싱 | Bash `tool_response.stdout`에 stderr 경고(`--rows-from` deprecation 등)·다중 라인 혼입 시 `todo_mirror` JSON 추출 실패 | P1 | L2(경고 라인·다중 라인 포함 stdout에서 마지막 JSON 라인 추출 성공) | S-F002-3 |
| H-6 | F-002 matcher 광역성 | PostToolUse `matcher:"Bash"`가 모든 Bash 호출에 스크립트 실행 → 비state-tool 호출에도 발동(소음·성능·오주입) | P2 | L2(비state-tool 명령 stdin → 무출력·exit0·부작용0) | S-F002-2 |
| H-7 | F-003 merge 마커 | 소유권 마커 키(`_opal_managed`)를 hook 블록에 추가 → Claude Code가 미지 키를 거부/경고하여 settings 로드 실패 | P0 | L2(머지 산출 JSON 유효성) + L3(Claude 세션이 settings 로드 오류 없이 기동·hook 발동) | S-F003-4, S-F002-live-1 |
| H-8 | F-003 멱등·보존 | 기존 외부 hook(orca PostToolUse) 유실(clobber) / N회 재실행 시 OPAL 항목 중복 누적 | P0 | L2(orca 보존 + OPAL upsert + N회 실행 결과 바이트 동일) | S-F003-1,2,3 |
| H-9 | 플랫폼 독립성 | Claude 전용 hook 채택이 `pm-improvement-loop.md §6 hook 미채택(플랫폼 독립)` 원칙·`CONVENTIONS §플랫폼 분기 격리`와 상충 | P1 | 산출물 검사(hook은 claude-hooks.json 어댑터에만 격리 + state.md 능력감지 게이트 보존 + 비Claude는 기존 no-op 폴백) | S-교체-2 |
| H-10 | F-004 교체 완전성 | `state.md`에 prose-only 미러 의존 서술이 잔존(구형 미제거) / SSOT 불변·능력감지 게이트 문구 유실 | P1 | 산출물 검사(prose-only 잔존 grep 0 + SSOT·능력감지 문구 보존) | S-교체-1 |
| H-11 | F-003 테스트 가능성 | 멱등 upsert 로직이 install-mac.sh 인라인 python에 매몰 → 결정론 단위 검증 불가(회귀 사각) | P1 | L1(로직을 호출 가능한 seam으로 분리 후 단위 테스트) | S-F003-1~4 |

**가설 도출 근거(예시 3종)**:
- H-4: hook additionalContext 계약 → PM 도구 호출 유발 여부 불확실 → 운영 영향 P0 → L2(스크립트 출력 스키마) + L3(실세션 실증) 의무. **본 태스크의 근본 검증 대상.**
- H-8: merge 이벤트 통째 교체(현행) → orca clobber/재배포 중복 → 운영 영향 P0 → L2(보존+멱등) 의무.
- H-2: na/failed 상태 파생 오판 → mock 통과 후 실 상태에서 오표시 → 운영 영향 P1 → L1(단위 경계값) 의무.

---

## 2. 기능별 분석

### F-001: state-tool `todo_mirror` 페이로드 출력

#### 2.1.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬(도구) | `opal/tools/state-tool/state_tool.py` | 파이프라인 SSOT CLI — init/advance/mark/block 출력부 | 수정 |
| 스킬(도구) | `opal/tools/state-tool/schema/state.schema.json` | state.json 스키마(additionalProperties:false) | 참조(무변경) |
| 배치(테스트) | `opal/tools/state-tool/tests/test_state_tool.py` | 단위 테스트 스위트 | 수정(테스트 추가) |

#### 2.1.2 현재 구현
- `ok(command, **kwargs)`가 단일 라인 JSON을 stdout으로 출력한다 (`state_tool.py:144-146`). 현재 todo/mirror/stage 집계 코드는 **0줄**(README·소스 grep 확인, → D-9 §배경 분석).
- 4개 서브명령의 최종 출력:
  - `cmd_init` → `ok(command, task_path=..., task_id=..., rows_count=..., created_at=..., import_existing=...)` (`state_tool.py:1058-1063`)
  - `cmd_advance` → `ok(command, row_id=..., stage=..., item=..., status="in_progress", timestamp=...)` (`state_tool.py:1204-1205`)
  - `cmd_mark` → `ok(command, row_id=..., stage=..., item=..., status=..., timestamp=..., owner=...)` (`state_tool.py:1380-1381`)
  - `cmd_block` → `ok(command, row_id=..., stage=..., item=..., status="failed", current_status="blocked", timestamp=...)` (`state_tool.py:1410-1411`)
- 상태 상수: `_COMPLETE_STATUSES = {"done", "additional_work_done", "na"}` (`state_tool.py:449`). 상태 라벨 맵 `STATUS_LABEL_MAP` (`state_tool.py:55-61`).
- 단계 distinct 추출 패턴 선례: `_build_new_state_md`가 `list(dict.fromkeys(r["stage"] for r in rows))`로 단계 순서 보존 목록을 만든다 (`state_tool.py:1069`).
- agentic init 시 `사용자 확인` 행(CLOSE 제외)은 `status="na"`로 자동 마킹된다 (`state_tool.py:600-604`, `806-810`).

#### 2.1.3 영향 범위
- **상위 의존(호출자)**: `ok()` stdout을 소비하는 것은 (a) run.sh 경유 셸 호출자, (b) 신설 hook 스크립트(F-002). 기존 테스트는 응답 dict의 특정 키만 검사(정확 dict 비교 아님 — `state_tool.py` 테스트 패턴 `result["..."]` 접근, `test_state_tool.py:158-174`)하므로 키 추가는 하위호환. → H-1 회귀로 확증.
- **하위 의존**: `build_todo_mirror`는 in-memory `state` dict만 읽고 파일 I/O 없음. `save_state_json`(`state_tool.py:205-210`)은 미접촉 → state.json 영속 경계 보존(H-3).
- **공유 상태**: state.json rows[] 구조. `todo_mirror`는 파생값(비영속).

---

### F-002: PostToolUse hook + 미러 릴레이 헬퍼 스크립트

#### 2.2.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 어댑터(hook) | `opal/core/hooks/claude-hooks.json` | Claude Code hook 정의(현재 SubagentStop/Stop) | 수정 |
| 스킬(도구) | `opal/tools/state-tool/todo_mirror_hook.py` | PostToolUse 릴레이 헬퍼 — stdin 파싱·필터·additionalContext 출력 | 신규 |
| 배치(테스트) | `opal/tools/state-tool/tests/test_todo_mirror_hook.py` | 헬퍼 단위 테스트 | 신규 |
| 환경(배포) | `scripts/install-mac.sh` | tools/ 일괄 배포 루프가 신규 스크립트 자동 배포 | 참조(무변경 — 기존 루프가 흡수) |

#### 2.2.2 현재 구현
- `claude-hooks.json`은 `SubagentStop`/`Stop` 2개 이벤트만 정의(osascript 알림), `PostToolUse` 없음 (→ D-4 전체).
- install은 `merge_hooks_config "$settings" "$hooks_src"`로 `$USER_HOME/.claude/settings.json`에 병합(전역 — OPAL 2-Layer 정합, `install-mac.sh:1233-1238`).
- tools/ 디렉토리는 `install_dir "$opal_dir/tools" "$opal_home/tools"`로 통째 배포(`install-mac.sh:1112-1114`) → `todo_mirror_hook.py`는 별도 install 수정 없이 `~/.opal/tools/state-tool/todo_mirror_hook.py`로 자동 배포됨.
- venv python 경로: `$HOME/.opal/.venv/bin/python` (run.sh 선례 `run.sh:4`).
- **hook 미채택 선례(상충 검토)**: `pm-improvement-loop.md §6`은 hook을 "Claude Code 전용·플랫폼 종속"으로 전면 미채택했다(→ D-10). 본 태스크는 이와 달리 **todo 패널 자체가 Claude 전용 능력**(TaskCreate 노출 세션에서만 존재, `state.md` 능력감지 게이트)이므로, Claude 전용 hook으로 Claude 전용 능력을 강제하는 것은 플랫폼 독립성을 훼손하지 않는다(비Claude는 애초에 이 능력이 없어 기존 no-op 유지). H-9로 확증.

#### 2.2.3 영향 범위
- **상위 의존**: Claude Code hook 런타임(PostToolUse). matcher=`Bash`이므로 모든 Bash 호출에 스크립트가 기동되나, state-tool 명령이 아니면 즉시 무출력 종료(H-6).
- **하위 의존**: F-001의 `todo_mirror` 페이로드(stdout). 스크립트는 이 페이로드를 추출·재포장만 한다.
- **공유 상태**: `~/.claude/settings.json`(F-003 merge 대상). 세션 컨텍스트(additionalContext 주입).

---

### F-003: `merge_hooks_config` 소유권-마커 멱등 upsert

#### 2.3.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 환경(배포) | `scripts/install-mac.sh` | `merge_hooks_config` 배시 함수(179~206) | 수정 |
| 환경(배포) | `scripts/merge-hooks.py` | 멱등 upsert 로직(테스트 가능 seam) | 신규 |
| 배치(테스트) | `scripts/tests/test_merge_hooks.py` | merge 로직 단위 테스트 | 신규 |

#### 2.3.2 현재 구현
- `merge_hooks_config`(`install-mac.sh:179-206`)는 인라인 `python3 -c`로 다음을 수행:
  ```python
  data.setdefault('hooks', {})
  for event, rules in source_hooks.items():
      data['hooks'][event] = rules   # ← 이벤트 통째 교체(clobber)
  ```
  (`install-mac.sh:199-201`) — 배포 타깃 `~/.claude/settings.json`에 이미 존재하는 **orca PostToolUse hook을 통째 덮어써 유실**시킨다(→ D-9 §배경 분석).
- 배포 호출부: `install-mac.sh:1232-1239`.
- 로직이 인라인 python에 매몰되어 결정론 단위 검증 불가(H-11).

#### 2.3.3 영향 범위
- **상위 의존**: install 배포 시 1회 호출. 재실행(재배포) 시 멱등이어야 함.
- **하위 의존**: 사용자의 기존 `~/.claude/settings.json`(orca 등 외부 hook 포함 가능).
- **공유 상태**: `~/.claude/settings.json` — F-002 hook이 여기에 병합됨.

---

### F-004: `state.md` 사양 정합 (prose → hook 강제)

#### 2.4.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드(하네스) | `opal/core/references/harness/state.md` | §파이프라인 todo 미러 사양 SSOT(52~72) | 수정 |

#### 2.4.2 현재 구현
- `state.md §파이프라인 todo 미러`(→ D-1 line 52~72)는 **prose 지시**로만 존재:
  - "적용 시점: state-tool 이벤트 호출 **직후**" (line 55) — PM이 직접 수행하라는 산문.
  - "미러 규칙 — 갱신: `init` 직후 … 이후 `advance`/`mark`/`block` 호출 직후, … state-tool 호출과 1:1로 동반" (line 63-69).
  - 능력감지 게이트(line 59)·SSOT 불변 읽기 전용 거울(line 61)·파생 규칙(line 65-68)·블로커 in_progress 유지(line 70)는 **보존 대상**.
- 파생 규칙 원문(line 65-68): "전부 ✅ → completed / 하나라도 🔄 있거나 일부만 ✅ → in_progress / 전부 ⬜ → open(pending)".

#### 2.4.3 영향 범위
- **상위 의존**: 전 opal-pilot이 이 절을 상속(line 54 "모든 opal-pilot이 상속"). 재서술 금지 원칙 유지.
- 변경이력 표(line 129-137)에 행 추가 필요([MUST] 변경이력 의무).

---

## 3. 기능별 설계

### F-001: state-tool `todo_mirror` 페이로드 출력

#### 3.1.1 파일 변경 계획

**신규 생성** — 없음

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/state-tool/state_tool.py` | 스킬(도구) | `build_todo_mirror(state, action)` 헬퍼 신설 + init/advance/mark/block `ok()`에 `todo_mirror=` 추가 | (→ D-9 R-1), `state_tool.py:1058·1204·1380·1410` |
| 2 | `opal/tools/state-tool/tests/test_state_tool.py` | 배치(테스트) | `TestTodoMirror` 클래스 신설(파생 4규칙 + 영속 경계) | (→ D-9 R-1 AC) |

#### 3.1.2 API·데이터 모델·설계

**헬퍼 함수 시그니처**
```python
def build_todo_mirror(state: dict, action: str) -> dict:
    """R-1: state.json rows[] → 단계 단위 todo 미러 페이로드.
    action: "create"(init) | "update"(advance/mark/block).
    비영속 — ok() stdout 페이로드에만 사용, save_state_json 미접촉(H-3, → D-7:7)."""
```

**파생 규칙 (state.md 사양 + na 중립 정련)** — `na`는 집계에서 **중립**(제외)으로 처리한다. agentic init 시 `사용자 확인` 행이 `na`이므로, na를 완료로 세면 미착수 단계가 오판(in_progress)된다(H-2). 따라서:
```python
_COMPLETE_STATUSES = {"done", "additional_work_done", "na"}  # 기존 상수 재사용(state_tool.py:449)

def build_todo_mirror(state, action):
    stages = list(dict.fromkeys(r["stage"] for r in state.get("rows", [])))  # 순서 보존(state_tool.py:1069 패턴)
    todos = []
    for stage in stages:
        statuses = [r.get("status") for r in state["rows"] if r["stage"] == stage]
        effective = [s for s in statuses if s != "na"]        # na 중립
        if not effective or all(s in ("done", "additional_work_done") for s in effective):
            st = "completed"
        elif all(s == "pending" for s in effective):
            st = "pending"
        else:                                                  # in_progress / failed / 부분완료 혼합
            st = "in_progress"
        todos.append({
            "id":         f"stage:{stage}",       # 세션 내 안정 키 — PM이 content로 native todo 매칭
            "content":    f"{stage} 단계",         # TaskCreate/TaskUpdate content
            "activeForm": f"{stage} 단계 진행 중",  # 진행형 표현(native todo 스키마)
            "status":     st,                      # pending | in_progress | completed (native 직접 릴레이)
        })
    return {"action": action, "todos": todos}
```
- **DEC-1 (파생 상태 열거값)**: `pending`/`in_progress`/`completed` — 네이티브 할일 도구 status와 직접 매핑되어 PM이 그대로 릴레이(state.md `open`을 `pending`으로 통일, F-004에서 문구 정합). (→ D-1 line 65-68)
- **DEC-2 (na 중립)**: `na` 행은 pending/completed 판정에서 제외 — agentic auto-na 오판 방지(H-2). (→ `state_tool.py:600-604`)
- **DEC-3 (블로커)**: `block` 시 대상 행 `failed`는 `_COMPLETE_STATUSES`에 없고 pending도 아니므로 단계가 `in_progress` 유지 — state.md "블로커 시 in_progress 유지" 규칙과 자연 일치(H-2). (→ D-1 line 70)
- **DEC-4 (비영속)**: `todo_mirror`는 4개 `ok()` 호출 인자로만 전달, `state`에 병합·`save_state_json` 금지 → schema `additionalProperties:false` 위반 회피. [MUST] `opal/tools/state-tool/schema/state.schema.json` §root: `"additionalProperties": false` (→ D-7:7)

**ok() 삽입 위치** (기존 인자 뒤에 키만 추가 — 하위호환, H-1)
- `cmd_init`: `ok(command, ..., import_existing=import_mode, todo_mirror=build_todo_mirror(state, "create"))` (`state_tool.py:1058`)
- `cmd_advance`: `ok(command, ..., timestamp=now_str, todo_mirror=build_todo_mirror(state, "update"))` (`state_tool.py:1204`)
- `cmd_mark`: `ok(command, ..., owner=row["owner"], todo_mirror=build_todo_mirror(state, "update"))` (`state_tool.py:1380`)
- `cmd_block`: `ok(command, ..., timestamp=now_str, todo_mirror=build_todo_mirror(state, "update"))` (`state_tool.py:1410`)

**@header 갱신**: `state_tool.py` @header description에 이번 태스크(076) 변경 요약 1줄 추가. [MUST] `docs/CONVENTIONS.md` §@header 규칙 (→ D-6)

#### 3.1.3 환경 변경
해당 없음 (표준 라이브러리만, 신규 의존성 없음 — → D-9 §기술 스택).

#### 3.1.4 배치/마이그레이션
해당 없음.

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 AC(init 페이로드) | 기능 테스트 | `cmd_init` ok() 응답에 `todo_mirror.action=="create"` + 단계별 todo(전부 pending)가 포함된다 |
| TS-002 | R-1 AC(전부 ✅=completed) | 기능 테스트 | 한 단계 전 행 done → 해당 단계 todo status=`completed` |
| TS-003 | R-1 AC(일부·🔄=in_progress) | 기능 테스트 | advance로 한 행 🔄 → 단계 status=`in_progress`; 일부만 done인 단계도 `in_progress` |
| TS-004 | R-1 AC(전부 ⬜=open) | 기능 테스트 | 미착수 단계 todo status=`pending` |
| TS-005 | R-1(na 중립) | 기능 테스트 | agentic init 시 `사용자 확인`(na)+`작업`(pending) 단계 → status=`pending`(na 미반영) |
| TS-006 | R-1(블로커) | 기능 테스트 | `cmd_block` 후 대상 단계 todo status=`in_progress` 유지, `action=="update"` |
| TS-007 | H-3 영속 경계 | 회귀 테스트 | 4개 명령 실행 후 `state.json`에 `todo_mirror` 키 부재 + `save_state_json` 결과가 schema 통과 |

---

### F-002: PostToolUse hook + 미러 릴레이 헬퍼 스크립트

#### 3.2.1 파일 변경 계획

**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 3 | `opal/tools/state-tool/todo_mirror_hook.py` | 스킬(도구) | PostToolUse 릴레이 — stdin 파싱·state-tool 필터·payload 추출·additionalContext 출력 | (→ D-9 R-2) |
| 4 | `opal/tools/state-tool/tests/test_todo_mirror_hook.py` | 배치(테스트) | 헬퍼 단위 테스트 | (→ D-9 R-2 AC) |

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 5 | `opal/core/hooks/claude-hooks.json` | 어댑터(hook) | `PostToolUse` 이벤트 추가(matcher `Bash`, command=venv python + 헬퍼 스크립트) | (→ D-9 R-2), `claude-hooks.json` |

#### 3.2.2 API·데이터 모델·설계

**claude-hooks.json — PostToolUse 추가** (기존 SubagentStop/Stop 보존)
```json
"PostToolUse": [
  {
    "matcher": "Bash",
    "hooks": [
      {
        "type": "command",
        "command": "\"$HOME/.opal/.venv/bin/python\" \"$HOME/.opal/tools/state-tool/todo_mirror_hook.py\""
      }
    ]
  }
]
```
- **DEC-5 (matcher)**: PostToolUse matcher는 도구명(`Bash`)에 매칭된다. 명령 내용 필터(state-tool 여부)는 스크립트가 수행 → 비state-tool 호출은 무출력 종료(H-6, AC "비state-tool 호출에는 발동하지 않는다"를 "발동하되 무부작용"으로 충족). (→ D-4)
- **DEC-6 (실행 경로)**: venv python으로 스크립트 직접 실행 → chmod 불필요(install tools/ 배포 루프가 파일 배포만 하면 됨, `install-mac.sh:1112-1114`). `$HOME` 셸 확장에 의존(hook command는 셸 경유 실행).

**todo_mirror_hook.py — 함수 설계**
```python
# @header {module, layer:"util", domain:"opal-pipeline", description:...}
import json, sys, re

_STATE_TOOL_SIG = "state-tool/run.sh"
_MIRRORED_CMDS = ("init", "advance", "mark", "block")

def extract_command(tool_input: dict) -> str: ...   # tool_input.get("command","")

def is_state_tool_event(command: str) -> bool:
    """command 문자열에 state-tool/run.sh 포함 AND 서브명령이 미러 대상 4종인지."""

def extract_todo_mirror(stdout: str) -> dict | None:
    """stdout의 라인들 중 마지막으로 파싱되는 JSON 객체에서 todo_mirror 추출(H-5 — 경고/다중 라인 견딤). 없으면 None."""

def build_additional_context(command_name: str, payload: dict) -> str:
    """결정론 지시문 + payload JSON 직렬화."""

def main():
    data = json.load(sys.stdin)              # PostToolUse: {tool_name, tool_input, tool_response, ...}
    if data.get("tool_name") != "Bash": return               # 무출력 exit0
    command = extract_command(data.get("tool_input", {}))
    if not is_state_tool_event(command): return              # 비state-tool → 무출력(H-6)
    stdout = _get_stdout(data.get("tool_response"))          # dict/str 양쪽 견딤
    payload = extract_todo_mirror(stdout)
    if not payload: return                                   # 페이로드 없음 → 무출력(H-5)
    ctx = build_additional_context(_subcommand(command), payload)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": ctx
        }
    }, ensure_ascii=False))
```
- **DEC-7 (주입 스키마)**: PostToolUse hook은 stdout에 `{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"..."}}`를 출력하여 세션 컨텍스트에 지시를 주입한다. (핵심 가설 H-4 — L3 실증 필요)
- **DEC-8 (지시문·결정론)**: `additionalContext`는 "[파이프라인 todo 미러] state-tool {cmd} 감지 — 아래 todo_mirror로 네이티브 할일 패널 갱신: action=create→TaskCreate로 단계별 todo 생성, action=update→각 단계 todo를 status로 TaskUpdate. 능력감지: 할일 도구 미노출 세션이면 무시. SSOT는 STATE.md, todo는 읽기 전용 거울." + payload JSON. (→ D-1 §SSOT 불변·능력감지)
- **DEC-9 (fail-safe)**: 파싱 실패·키 부재·비Bash·비state-tool 전 경로에서 **무출력 exit 0** — hook이 정상 툴 흐름을 절대 차단하지 않는다.

#### 3.2.3 환경 변경
해당 없음(표준 라이브러리 json/sys/re만). install tools/ 배포 루프가 신규 파일 자동 배포.

#### 3.2.4 배치/마이그레이션
install 재배포 시 F-003 개선된 `merge_hooks_config`가 PostToolUse를 `~/.claude/settings.json`에 upsert.

#### 3.2.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-010 | R-2 AC(발동) | 기능 테스트 | state-tool `advance` stdin(todo_mirror 포함) → `hookSpecificOutput.additionalContext`에 지시문+payload 출력 |
| TS-011 | R-2 AC(비발동) | 기능 테스트 | 비state-tool Bash 명령 stdin → 무출력·exit0 (H-6) |
| TS-012 | H-5 | 기능 테스트 | stdout에 stderr 경고 라인 혼입 + 마지막 JSON 라인 → payload 추출 성공 |
| TS-013 | DEC-9 fail-safe | 기능 테스트 | todo_mirror 없는 state-tool 출력/깨진 JSON → 무출력·exit0 |
| TS-014 | R-2/R-5 실증 | 통합 테스트(L3) | 배포 후 새 세션에서 state-tool 호출 시 todo 생성/갱신 지시가 세션에 주입됨(수동 실증, S-F002-live-1) |

---

### F-003: `merge_hooks_config` 소유권-마커 멱등 upsert

#### 3.3.1 파일 변경 계획

**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 6 | `scripts/merge-hooks.py` | 환경(배포) | 소유권-마커 멱등 upsert 로직(테스트 seam) | (→ D-9 R-3), H-11 |
| 7 | `scripts/tests/test_merge_hooks.py` | 배치(테스트) | merge 단위 테스트(보존·upsert·멱등) | (→ D-9 R-3 AC) |

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 8 | `scripts/install-mac.sh` | 환경(배포) | `merge_hooks_config` 인라인 python → `merge-hooks.py` 위임 호출 | `install-mac.sh:179-206` |

#### 3.3.2 API·데이터 모델·설계

**merge-hooks.py — 멱등 upsert 알고리즘**
```python
MARKER = "_opal_managed"   # 소유권 마커 키(매처 블록 수준)

def merge_hooks(target_settings: dict, source_hooks: dict) -> dict:
    hooks = target_settings.setdefault("hooks", {})
    for event, rules in source_hooks.items():
        existing = hooks.get(event, [])
        preserved = [r for r in existing if not r.get(MARKER)]   # 외부(orca) 보존
        stamped   = [{**r, MARKER: True} for r in rules]         # OPAL 소유 스탬프
        hooks[event] = preserved + stamped                        # 외부 유지 + OPAL 갱신
    return target_settings

def main():  # argv: target_path, source_hooks_path
    # 파일 로드(target 없거나 공백 → {}) → merge → 원자적 write(indent=2)
```
- **DEC-10 (소유권 마커)**: 각 OPAL 매처 블록에 `_opal_managed:true`를 스탬프. 재실행 시 기존 OPAL 항목(마커 有)은 `preserved`에서 제외 후 새로 append → **N회 실행 결과 동일**(멱등, H-8). 외부 hook(마커 無, 예: orca PostToolUse)은 보존. (→ D-9 R-3 AC)
- **DEC-11 (마커 위치·호환)**: 마커는 매처 블록 dict의 형제 키. Claude Code가 미지 키를 무시한다는 전제(JSON 관대) — H-7로 L2(유효 JSON)+L3(세션 로드/발동) 확증. 위험 시 대안: 마커를 hook command 내 주석 시그니처로 이동(폴백, 문서화).
- **DEC-12 (배시 위임)**: `merge_hooks_config`는 인라인 python 삭제, `/usr/bin/python3 "$SCRIPT_DIR/merge-hooks.py" "$target" "$hooks_json"`로 위임. `SCRIPT_DIR`는 install 상단에서 산출(`install-mac.sh:89 FRAMEWORK_ROOT` 인근 `script_dir` 재사용). 로직을 파일로 분리하여 단위 테스트 가능(H-11).
- **DEC-13 (배포 경계)**: `merge-hooks.py`는 소스(`scripts/`)에만 생성, install이 실행. `~/.opal/` 직접수정 아님. [MUST] `docs/CONVENTIONS.md` §배포 경계 (→ D-6)

#### 3.3.3 환경 변경
해당 없음(표준 라이브러리 json/sys/os). `scripts/tests/` 디렉토리 신설.

#### 3.3.4 배치/마이그레이션
install 재배포가 실 병합을 수행. 기존 사용자 settings.json은 재배포 시 orca 보존하며 OPAL upsert(1회 마이그레이션 효과).

#### 3.3.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-020 | R-3 AC(외부 보존) | 기능 테스트 | 기존 orca PostToolUse가 있는 settings에 merge → orca 항목 보존됨 |
| TS-021 | R-3 AC(upsert) | 기능 테스트 | OPAL PostToolUse/SubagentStop/Stop 항목이 `_opal_managed:true`로 삽입됨 |
| TS-022 | R-3 AC(멱등) | 기능 테스트 | merge 2회 연속 실행 → 결과 JSON 바이트 동일(OPAL 중복 0, orca 중복 0) |
| TS-023 | H-7 | 산출물 검사 | merge 산출 settings.json이 유효 JSON이며 마커 키가 매처 블록에만 존재 |
| TS-024 | R-6 | 회귀 테스트 | `bash -n scripts/install-mac.sh` 문법 검사 통과 |

---

### F-004: `state.md` 사양 정합 (prose → hook 강제)

#### 3.4.1 파일 변경 계획

**신규 생성** — 없음

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 9 | `opal/core/references/harness/state.md` | 가이드(하네스) | §파이프라인 todo 미러를 hook 강제 트리거 방식으로 재서술 + 변경이력 행 추가 | (→ D-1 line 52~72) |

#### 3.4.2 설계
- **적용 시점 재서술**(line 55): "state-tool 이벤트 호출 직후 **PostToolUse hook이 결정론 트리거**하여 todo_mirror 페이로드+지시를 세션에 주입한다. PM(소유자)은 주입된 페이로드를 TaskCreate(create)/TaskUpdate(update)로 **기계적 릴레이**한다(정직한 한계: 최종 도구 호출은 LLM 몫)."
- **미러 규칙 갱신**(line 63-69): "state-tool이 `todo_mirror` 페이로드(단계별 파생 상태)를 출력하고, hook이 이를 지시와 함께 주입" — prose-only "PM이 직접 재계산" 서술 제거(H-10).
- **보존 문구**(무변경): 능력감지 게이트(line 59), SSOT 불변 읽기 전용 거울(line 61), 파생 규칙(line 65-68, `open`→`pending` 용어만 DEC-1과 통일), 블로커 in_progress 유지(line 70), L2 미적용(line 72). [MUST] `docs/CONVENTIONS.md` §State 관리 SSOT 불변 (→ D-6)
- **변경이력 행 추가**(line 129-137): `| v1.5 | 2026-07-23 HH:mm | 파이프라인 todo 미러 hook 강제 정합 — prose 지시 → PostToolUse hook 트리거+state-tool todo_mirror 페이로드 방식으로 재서술(SSOT 불변·능력감지 보존), open→pending 용어 통일 (076) |`. [MUST] `docs/CONVENTIONS.md` §변경이력 의무 (→ D-6)

#### 3.4.3 환경 변경 / 3.4.4 배치
해당 없음.

#### 3.4.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-030 | R-4 AC(hook 강제 서술) | 산출물 검사 | §파이프라인 todo 미러가 hook 트리거+todo_mirror 페이로드 방식으로 서술됨 |
| TS-031 | R-4 AC(보존) | 산출물 검사 | SSOT 불변·능력감지 게이트·읽기 전용 거울 문구 보존 |
| TS-032 | R-5/H-10 | 산출물 검사 | "PM이 직접 재계산/직접 호출"류 prose-only 의존 서술 잔존 0(grep) |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)
| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001 | 1 | opal-task-agent | 순차 | 페이로드 기반 — 후속 의존의 근원 |
| 1 | F-003 | 6 | opal-task-agent | 1과 병렬 | install 경로 독립 |
| 2 | F-001 | 2 | opal-task-agent | 1 후 | payload 단위 테스트 |
| 2 | F-002 | 3 | opal-task-agent | 1 후 | hook 스크립트(payload 소비) |
| 2 | F-003 | 7 | opal-task-agent | 6 후 | merge 단위 테스트 |
| 3 | F-002 | 4, 5 | opal-task-agent | 3 후 | hooks.json + hook 테스트 |
| 3 | F-004 | 8 | opal-task-agent | 1·3 후 | state.md 정합(구현 확정 반영) |
| 4 | 회귀 | 9 | opal-task-agent | 전 구현 후 | state-tool 전량 + bash 문법 |
| 4 | 문서 | 10 | PM 직접 | 9 후 | docs/ 갱신 |

### 4.2 실행 체크리스트
> 총 10개 Step | Phase 4개 | 실행 모드: 복잡

#### Step 1: state-tool `build_todo_mirror` 헬퍼 + 4개 서브명령 출력 추가
- [ ] 완료
- **소속 기능**: F-001
- **영역**: 스킬(도구)
- **agent**: opal-task-agent
- **파일**: `opal/tools/state-tool/state_tool.py`
- **작업 내용**: `build_todo_mirror(state, action)` 신설(§3.1.2 파생 규칙 — na 중립·비영속) + init(`:1058`)/advance(`:1204`)/mark(`:1380`)/block(`:1410`) `ok()`에 `todo_mirror=` 인자 추가. @header description에 076 요약 1줄 추가.
- **완료 기준**: 4개 서브명령 ok() JSON에 `todo_mirror.{action,todos[]}` 포함, `state.json`에는 미영속(H-3). `build_todo_mirror`가 na 중립·전부pending→pending·전부done→completed·부분/failed→in_progress를 정확 산출.
- **테스트**: TS-001~TS-007
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: F-001 단위 테스트(`TestTodoMirror`) 추가
- [ ] 완료
- **소속 기능**: F-001
- **영역**: 배치(테스트)
- **agent**: opal-task-agent
- **파일**: `opal/tools/state-tool/tests/test_state_tool.py`
- **작업 내용**: `TestTodoMirror` 클래스 신설 — 파생 4규칙 + na 중립 + 블로커 유지 + 영속 경계(state.json에 todo_mirror 부재). BaseTestCase 픽스처·`_mock_now`·`make_args` 재사용(`test_state_tool.py:145-251`). exports @header 갱신.
- **완료 기준**: TS-001~TS-007 전부 PASS.
- **테스트**: TS-001~TS-007
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 3: `todo_mirror_hook.py` 릴레이 헬퍼 신규 작성
- [ ] 완료
- **소속 기능**: F-002
- **영역**: 스킬(도구)
- **agent**: opal-task-agent
- **파일**: `opal/tools/state-tool/todo_mirror_hook.py` (신규)
- **작업 내용**: §3.2.2 설계대로 stdin 파싱·Bash/state-tool 필터(4종 서브명령)·stdout에서 todo_mirror 추출(H-5 견딤)·`hookSpecificOutput.additionalContext` 출력·전 경로 fail-safe 무출력 exit0(DEC-9). @header 블록 작성.
- **완료 기준**: 함수 4종 구현 + main() 정상 경로/비발동/파싱실패 분기 완비.
- **테스트**: TS-010~TS-013
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 4: `claude-hooks.json`에 PostToolUse 추가
- [ ] 완료
- **소속 기능**: F-002
- **영역**: 어댑터(hook)
- **agent**: opal-task-agent
- **파일**: `opal/core/hooks/claude-hooks.json`
- **작업 내용**: 기존 SubagentStop/Stop 보존한 채 `PostToolUse`(matcher `Bash`, command=venv python + `~/.opal/tools/state-tool/todo_mirror_hook.py`) 추가.
- **완료 기준**: 유효 JSON, PostToolUse가 헬퍼 스크립트를 호출.
- **테스트**: TS-010(간접), TS-014(L3)
- **실행 방법**: sub-agent
- **의존**: Step 3

#### Step 5: F-002 헬퍼 단위 테스트 신규 작성
- [ ] 완료
- **소속 기능**: F-002
- **영역**: 배치(테스트)
- **agent**: opal-task-agent
- **파일**: `opal/tools/state-tool/tests/test_todo_mirror_hook.py` (신규)
- **작업 내용**: 합성 stdin JSON(state-tool advance+payload / 비state-tool / 경고혼입 stdout / 깨진 JSON)으로 additionalContext 출력·무출력·fail-safe 검증. 표준 라이브러리만.
- **완료 기준**: TS-010~TS-013 전부 PASS.
- **테스트**: TS-010~TS-013
- **실행 방법**: sub-agent
- **의존**: Step 3

#### Step 6: `merge-hooks.py` 멱등 upsert 로직 신규 작성
- [x] 완료
- **소속 기능**: F-003
- **영역**: 환경(배포)
- **agent**: opal-task-agent
- **파일**: `scripts/merge-hooks.py` (신규)
- **작업 내용**: §3.3.2 `merge_hooks(target, source)` — 소유권 마커(`_opal_managed`) 기반 외부 보존 + OPAL upsert + 멱등. main(argv: target, source) 원자적 write. @header 블록 작성.
- **완료 기준**: 함수가 외부 보존·OPAL 스탬프·멱등을 결정론 산출.
- **테스트**: TS-020~TS-022
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 7: F-003 단위 테스트 신규 작성
- [x] 완료
- **소속 기능**: F-003
- **영역**: 배치(테스트)
- **agent**: opal-task-agent
- **파일**: `scripts/tests/test_merge_hooks.py` (신규)
- **작업 내용**: orca PostToolUse 사전 존재 settings + OPAL source로 merge → 보존/upsert/2회 멱등/유효 JSON·마커 위치 검증. 표준 라이브러리만.
- **완료 기준**: TS-020~TS-023 전부 PASS.
- **테스트**: TS-020~TS-023
- **실행 방법**: sub-agent
- **의존**: Step 6

#### Step 8: `install-mac.sh merge_hooks_config` 위임 개선
- [x] 완료
- **소속 기능**: F-003
- **영역**: 환경(배포)
- **agent**: opal-task-agent
- **파일**: `scripts/install-mac.sh`
- **작업 내용**: `merge_hooks_config`(`:179-206`)의 인라인 python(이벤트 통째 교체) 제거 → `/usr/bin/python3 "$SCRIPT_DIR/merge-hooks.py" "$target" "$hooks_json"` 위임(DEC-12). `SCRIPT_DIR` 산출 확인.
- **완료 기준**: `bash -n scripts/install-mac.sh` 통과, merge_hooks_config가 merge-hooks.py 호출.
- **테스트**: TS-024
- **실행 방법**: sub-agent
- **의존**: Step 6

#### Step 9: `state.md` 사양 정합 + 변경이력
- [ ] 완료
- **소속 기능**: F-004
- **영역**: 가이드(하네스)
- **agent**: opal-task-agent
- **파일**: `opal/core/references/harness/state.md`
- **작업 내용**: §3.4.2 — §파이프라인 todo 미러를 hook 강제 트리거+todo_mirror 페이로드 방식으로 재서술(prose-only 의존 제거), SSOT 불변·능력감지·읽기전용 거울 보존, open→pending 용어 통일, 변경이력 v1.5 행 추가.
- **완료 기준**: TS-030~TS-032. prose-only 의존 잔존 0.
- **테스트**: TS-030~TS-032
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 3

#### Step 10: 회귀 검증 (state-tool 전량 + install 문법)
- [ ] 완료
- **소속 기능**: R-6(회귀)
- **영역**: 배치(테스트)
- **agent**: opal-task-agent
- **파일**: `opal/tools/state-tool/tests/`, `scripts/install-mac.sh`
- **작업 내용**: `python3 -m pytest`/`unittest`로 state-tool 기존 테스트 전량 실행 + 신규 테스트 실행. `bash -n scripts/install-mac.sh`. (실행: OPAL venv 또는 표준 python3)
- **완료 기준**: 기존 테스트 회귀 0(H-1), 신규 전량 PASS, bash 문법 통과.
- **테스트**: TS-007, TS-024, 전 TS 스위트
- **실행 방법**: sub-agent
- **의존**: Step 2, 5, 7, 8, 9

#### Step 11: docs/ 갱신 (선택)
- [ ] 완료
- **소속 기능**: 문서
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/ARCHITECTURE.md`, `docs/PROJECT.md`(변경이력)
- **작업 내용**: hook 어댑터 계층에 PostToolUse todo 미러 트리거 + install merge 멱등 upsert 도입을 시스템 구조 문서에 반영(신규 패턴 도입 — CONVENTIONS/ARCHITECTURE 판단 기준). 영향 경미 시 PROJECT.md 변경이력 1행으로 최소화.
- **완료 기준**: 구조 변경이 문서에 반영되거나, 영향 경미 판정 시 스킵 근거 기록.
- **테스트**: 산출물 검사
- **실행 방법**: direct
- **의존**: Step 10

### 4.3 병렬/순차 판별 근거
| 관계 | 근거 |
|------|------|
| Step 1 ∥ Step 6 | 독립 파일(state_tool.py vs merge-hooks.py), 독립 기능 |
| Step 1 → Step 2·3·9 | payload 계약이 테스트·hook·문서의 선행 |
| Step 3 → Step 4·5 | hook 스크립트가 hooks.json 배선·테스트의 선행 |
| Step 6 → Step 7·8 | merge 로직이 테스트·install 위임의 선행 |
| Step 2·5·7·8·9 → Step 10 | 회귀는 전 구현 완료 후 |
| Step 10 → Step 11 | 문서는 구현 확정 후 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA
| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | 4개 서브명령 todo_mirror 결정론 출력 + 파생 4규칙 | TS-001~006 | 파생 규칙 단위 전량 PASS |
| F-001 | state.json 영속 경계(schema 무위반) | TS-007 | state.json에 todo_mirror 부재 + schema 통과 |
| F-002 | state-tool 호출 시 additionalContext 주입 / 비state-tool 무발동 | TS-010, TS-011 | 발동·비발동 분기 정확 |
| F-002 | stdout 파싱 견고성 + fail-safe | TS-012, TS-013 | 경고혼입 추출 성공, 실패 시 무출력 exit0 |
| F-002 | hook→PM 도구 유발 실증(핵심 H-4) | TS-014 | 배포 후 새 세션에서 todo 생성/갱신 지시 주입 확인 |
| F-003 | orca 보존 + OPAL upsert + N회 멱등 | TS-020~022 | 보존·upsert·멱등 전량 PASS |
| F-003 | 유효 JSON·마커 위치 + bash 문법 | TS-023, TS-024 | JSON 유효·`bash -n` 통과 |
| F-004 | hook 강제 재서술 + 보존 문구 | TS-030, TS-031 | 재서술·보존 확인 |
| F-004 | prose-only 의존 잔존 0(R-5 교체) | TS-032 | grep 잔존 0 |

### 5.2 회귀 테스트
- [ ] state-tool 기존 테스트 스위트 전량 PASS(H-1 — 응답 키 추가 하위호환)
- [ ] `save_state_json` 결과 state.schema.json 통과(todo_mirror 미영속, H-3)
- [ ] `bash -n scripts/install-mac.sh` 문법 통과(H-11)
- [ ] SubagentStop/Stop 기존 hook 무손상

### 5.3 코드/문서 품질
- [ ] 신규 `.py` 2종에 @header 블록([MUST] CONVENTIONS §@header)
- [ ] state_tool.py @header description 076 요약 갱신
- [ ] state.md 변경이력 v1.5 행(KST 일시 포함, [MUST] CONVENTIONS §변경이력)
- [ ] 프로젝트 컨벤션(Python snake_case·표준 라이브러리만) 준수

### 5.4 보안
- [ ] hook 스크립트가 stdin 외부 입력을 파싱 시 예외를 무출력 exit0로 격리(임의 명령 실행·주입 없음, DEC-9)
- [ ] 하드코딩 시크릿/토큰 없음
- [ ] settings.json 병합이 사용자 외부 hook을 파괴하지 않음(H-8)

---

## 6. 복잡도 판별
| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 11개 | 복잡 |
| 변경 파일 수 | 9개(수정 5 + 신규 4) | 복잡 |
| 모듈 범위 | 도구(state-tool)·어댑터(hooks)·배포(install)·하네스(state.md) 다중 | 복잡 |
| 작업 유형 | 신규 개발 + 대규모 개선(결정론화) | 복잡 |
| 외부 의존성 | 없음(표준 라이브러리, 신규 패키지 0) | 단순 |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지
- **Batch 1(병렬)**: A1=Step1(state_tool.py) ∥ A2=Step6(merge-hooks.py) — 독립 파일·독립 기능.
- **Batch 2**: A1→Step2·Step3(state_tool 계열, 동일 도구 디렉토리이므로 파일 충돌 방지 위해 A1 계열 순차) ; A2→Step7·Step8(merge 계열).
- **Batch 3**: Step4·Step5(hook 배선·테스트) ; Step9(state.md).
- **Batch 4**: Step10(회귀, 단일 통합) → Step11(문서, PM 직접).
- **그룹핑 원칙**: `state_tool.py`·`tests/`·`todo_mirror_hook.py`는 같은 도구 트리 → 파일 충돌 방지 위해 동일 에이전트(A1) 계열로 순차. `scripts/` 계열은 A2. state.md는 독립.

### C-2. 스킬 요구사항
- 기존 스킬로 충분(op-dev-execute 워커 인라인 지침). 신규 스킬 불요 — 반복 패턴 3 Step 미만(Python 편집·JSON 편집·bash 편집 각 1~2회).

### C-3. 도구 요구사항
- 실행: OPAL `.venv` python 또는 표준 `python3`(테스트), `bash -n`(문법). MCP·신규 패키지·CLI 없음.

### C-4. 테스트 전략
- **기능 테스트**: `python3 -m unittest`(또는 pytest) — `opal/tools/state-tool/tests/test_state_tool.py`(TestTodoMirror), `test_todo_mirror_hook.py`, `scripts/tests/test_merge_hooks.py`.
- **회귀 테스트**: state-tool 기존 전량 재실행(H-1) + `bash -n scripts/install-mac.sh`.
- **통합/실증(L3)**: install 재배포(캡틴 지시 시) 후 새 세션에서 state-tool 호출→settings 로드·hook 발동·todo 지시 주입 확인(TS-014, H-4·H-7). PLAN 범위에서는 설계·자동 단위까지, L3 실증은 EXECUTE/캡틴 승인 후.
- **코드 품질**: @header 존재·표준 라이브러리 준수 검사.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| state-tool | Python 3(표준 라이브러리) | trailofbits/modern-python(참고 — 신규 의존성 없어 uv/ruff 도입 없음) |
| hook | Python 3 + Claude Code PostToolUse | — |
| install | Bash + python3 위임 | — |
| 사양 문서 | Markdown | — |

### 8.2 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|
| (없음) | 표준 라이브러리·기존 코드 분석으로 충분 — 외부 API 문서 불요 |

### 8.3 참조 문서 (설계 결정 근거)
| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | state.md (todo 미러 SSOT) | `opal/core/references/harness/state.md` | §파이프라인 todo 미러 현행 prose 사양·파생 규칙·정합 대상(R-4) |
| D-2 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py` | init/advance/mark/block 출력부·ok()·_COMPLETE_STATUSES·na 마킹 |
| D-3 | 소스 | install merge_hooks_config | `scripts/install-mac.sh` | 이벤트 통째 교체(clobber) 결함·배포 호출부(R-3) |
| D-4 | 소스 | hook 정의 | `opal/core/hooks/claude-hooks.json` | 현행 SubagentStop/Stop·PostToolUse 추가 대상(R-2) |
| D-5 | 설계 | 헌법 | `~/.opal/PRINCIPLES.md` | Core Stance "Enforce, don't just advise" 근거 |
| D-6 | 설계 | CONVENTIONS | `docs/CONVENTIONS.md` | @header·배포 경계·플랫폼 분기 격리·State·변경이력 [MUST] |
| D-7 | 설계 | state.schema.json | `opal/tools/state-tool/schema/state.schema.json` | additionalProperties:false — todo_mirror 영속 금지 근거(H-3) |
| D-8 | 소스 | test_state_tool.py | `opal/tools/state-tool/tests/test_state_tool.py` | BaseTestCase 픽스처·응답 키 접근 패턴(회귀 하위호환 판정) |
| D-9 | 기획 | TASK.md | `tasks/076-260723-opds-todo미러-hook자동화/TASK.md` | 요구사항 R-1~R-6·확정 방향·정직한 한계 |
| D-10 | 설계 | pm-improvement-loop.md | `opal/core/references/harness/pm-improvement-loop.md` | §6 hook 미채택(플랫폼 독립) 선례 — 상충 검토·H-9 |

---

## 9. 리스크 및 대응 (기능-리스크 연결)
| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| 1 | hook additionalContext가 PM 도구 호출을 유발 못함(계약 불확실) | F-002 | P0 | 스크립트 출력 스키마 L2 확정 + 배포 후 L3 실증(TS-014). 실패 시 지시문 강화/폴백 검토 |
| 2 | 소유권 마커 키를 Claude Code가 거부 | F-003 | P0 | L2 유효 JSON + L3 세션 로드 확인. 폴백: command 시그니처 기반 식별(DEC-11) |
| 3 | orca PostToolUse clobber/재배포 중복 | F-003 | P0 | 마커 기반 preserved+upsert, N회 멱등 단위 테스트(TS-020~022) |
| 4 | ok() 계약 확장으로 기존 소비자 파손 | F-001 | P1 | 키 추가만(하위호환), 기존 테스트 전량 회귀(TS-007·Step10) |
| 5 | na/failed 파생 오판 | F-001 | P1 | na 중립·failed→in_progress 단위 경계 테스트(TS-005·006) |
| 6 | 플랫폼 독립성 훼손(hook 채택) | F-002 | P1 | hook을 claude-hooks.json 어댑터에만 격리 + state.md 능력감지 보존 + 비Claude no-op(H-9) |
| 7 | prose-only 미러 의존 잔존(교체 미완) | F-004 | P1 | grep 잔존 0 검증(TS-032, R-5) |
| 8 | Bash 광역 matcher 소음/성능 | F-002 | P2 | 비state-tool 즉시 무출력 종료(TS-011) |
