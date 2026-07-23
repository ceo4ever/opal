# PLAN: state-tool STATE.md "다음 액션" 자동 파생 (미갱신 결함 해소)

> 작성일: 2026-07-23 | 입력: TASK.md, ANALYSIS.md
> 모드: Multi-Feature
> 실행 컨텍스트: 단일 영역(Python CLI 도구) — EXECUTE는 `opal-task-agent` 단일 배치로 순차 처리 (오케스트레이터 지시)

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

STATE.md `## 다음 액션`이 `init` 이후 어떤 명령으로도 갱신되지 않아 태스크 내내 첫 단계 값(예: "PLAN 단계 진입")에 고정되는 결함을 해소한다. `advance`/`mark`(행 상태 전이) 시 state-tool이 파이프라인 프론티어(첫 미완료 행)에서 "다음 액션"을 **자동 파생**하여 갱신하도록 하고, `state.json`에 `next_action` 필드를 신설해 렌더 SSOT로 삼는다. 이는 단순 버그 픽스가 아니라 `state-template.md:34`가 "다음 액션은 PM 수동 갱신 (state-tool 범위 밖)"으로 명문화한 **설계 자체의 반전**이므로, 설계 문서 갱신과 회귀 테스트(`TestFreeTextPreservation`) 반전을 함께 포함한다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | state.json `next_action` 필드 + init 영속화 + 스키마 등록 | R-1 | P0 | 없음 |
| F-002 | 자동 파생 엔진(`_derive_next_action`) + 렌더 치환(`update_next_action_section`) + advance/mark 통합 | R-2, R-3 | P0 | F-001 |
| F-003 | advance/mark `--next-action` per-transition 오버라이드 | R-4 | P1 | F-002 |
| F-004 | 테스트 — `TestFreeTextPreservation` 반전(mark/advance) + `TestNextActionAutoDerive` 신규 (RED-first) | R-5 | P0 | F-001, F-002, F-003 |
| F-005 | 문서·설계문서 SSOT 개정·배포 — README/state-template.md/@header/변경이력 + install | R-6 | P0 | F-001~F-004 |

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 ─ F-002 ─ F-003 ─┬─ F-004 ─ F-005
                       │            ↑
                       └────────────┘
(F-004는 F-001·F-002·F-003 전부에 의존, F-005는 전 기능 완료 후 배포)
```

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-004 `TestFreeTextPreservation` (`test_state_tool.py:1516-1528`) | "다음 액션 불변" assert가 R-2 구현 시 필연 RED — **의도된 설계 반전이지 회귀 아님** | P0 | L1(단위) — 반전된 테스트가 "블로커 보존 + 다음 액션 파생 + 하위 자유기재 보존"을 검증 | S-후보-A(mark/advance 반전 검증) |
| H-2 | F-002 `_derive_next_action` 프론티어 정의 | "다음 대기 행" 오판 — 완료행/실패행/전체완료 경계에서 잘못된 문자열 파생 | P1 | L1(단위) — 순차 advance/mark, 전체 완료, 다중 in_progress 경계 | S-후보-B(경계 파생) |
| H-3 | F-002 `update_next_action_section` 정규식 치환 범위 | 섹션 전체를 덮어써 PM 자유 기재(`- 세부 액션 N`)가 소실되거나, 첫 줄 치환이 다른 섹션을 오염 | P1 | L1(단위) — 자유기재 보존 + 첫 줄만 치환 검증 | S-후보-A |
| H-4 | F-001 `state.schema.json` `required` 오추가 | `next_action`을 `required`에 넣으면 구버전 state.json이 (향후 실 validate 시) 즉시 위반 → 하위호환 파괴 | P1(향후) | L1(단위) — 구버전 state.json 무손상 + `properties` optional 확인 | S-후보-C(하위호환) |
| H-5 | F-002 `sync_state_md` 시그니처 확장 | `next_action` 파라미터 추가가 기존 호출부(block/add-row/status)의 "다음 액션 미접촉" 계약을 깨뜨림 | P1 | L1(단위) — block/add-row 후 다음 액션 불변(=None 전달 시 보존) | S-후보-A |
| H-6 | F-005 배포본-소스 드리프트 | install 미실행/부분 실행으로 `~/.opal/tools/state-tool/`와 소스 불일치 | P1 | L3(배포 검증) — 배포본 diff 0 | S-후보-D(배포) |

**가설 도출 관점**: H-1은 "테스트가 옛 설계를 락인 → 반전 필수"(반전을 회귀로 오인 금지), H-2/H-3은 "파생 로직·치환 범위 정확성", H-4/H-5는 "하위호환·계약 비파괴", H-6은 "배포 경계"에서 도출.

---

## 2. 기능별 분석

### F-001: state.json `next_action` 필드 + init 영속화 + 스키마 등록

#### 2.1.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/state-tool/state_tool.py` | `cmd_init` state 딕셔너리 구성(`903-912`) + 렌더(`927`,`979-1008`) | 수정 |
| 스키마 | `opal/tools/state-tool/schema/state.schema.json` | 최상위 `properties`에 `next_action` 등록 | 수정 |

#### 2.1.2 현재 구현
- `next_action`은 `cmd_init` 실행 중 로컬 변수로만 존재: `next_action = args.next_action or "PLAN 단계 진입"` (`state_tool.py:927`) → `_build_new_state_md(...)`가 STATE.md `## 다음 액션` 본문에 1회 렌더(`979-1008`, 특히 `1006-1007`). **state.json 딕셔너리(`903-912`)에는 키가 없다** → 휘발성.
- `state.schema.json`은 최상위 `required`(`:6`)에 8개 필드만, `additionalProperties: false`(`:7`) — 즉 `next_action`을 state.json에 넣으면 이 스키마로 strict validate 시 "미선언 속성"으로 걸린다(런타임은 미검증이나 `properties` 등록이 정합상 필요). (`state.schema.json:5-8`)

#### 2.1.3 영향 범위
- `cmd_show(format=json)`(`state_tool.py:1021-1025`)은 `state` 딕셔너리를 그대로 반환 → `next_action` 추가 시 `show --format json`에도 자동 노출(추가 코드 불요).
- `cmd_validate`(`state_tool.py:1328-1334`)는 하드코딩 `required_fields` 리스트로 검증, `state.schema.json` 파일 비의존 → `next_action` 추가가 validate 동작에 무영향. `required_fields`에 넣지 않는다.
- 기존 구버전 state.json(필드 없음)은 `load_state_json` 후 `state.get("next_action")` 접근이 안전(None) — 마이그레이션 불요.

---

### F-002: 자동 파생 엔진 + 렌더 치환 + advance/mark 통합

#### 2.2.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/state-tool/state_tool.py` | `_derive_next_action`(신규)·`update_next_action_section`(신규)·`sync_state_md`(`346-371`)·`cmd_advance`(`1071-1114`)·`cmd_mark`(`1131-1286`) | 수정 |

#### 2.2.2 현재 구현
- 상태 전이 명령(`advance`/`mark`/`block`)은 각자 로직 후 `sync_state_md()`(`346-371`) 한 곳으로 STATE.md 갱신을 위임. 이 함수는 ① 마커 표(`render_pipeline_table`→`replace_pipeline_section`) ② `> 최종 갱신:` 헤더(`update_state_md_header`) ③ `## 현재 상태`(`update_current_status_section`) ④ (옵션)의사결정 로그(`append_decision_log`)만 갱신 — **`## 다음 액션` 미접촉**(결함의 정확한 지점).
- `## 다음 액션` 섹션은 STATE.md 최하단(`1006-1007`): `## 다음 액션\n{next_action}\n`. 하위에 후속 `## ` 헤더가 없다.
- 정규식 1줄 치환 선례: `update_current_status_section()`(`301-315`)이 `re.sub(r"^(- 진행: ).*$", ..., count=1, MULTILINE)`로 특정 라인만 교체 — 자유 텍스트 보존형 치환의 기존 관례.
- 완료 판정 상수 `_COMPLETE_STATUSES = {"done", "additional_work_done", "na"}`(`435`) 이미 존재 — 여집합(완료 아님)이 "미완료 행".
- 행 구조(`state.schema.json:44-113`, 렌더 `render_pipeline_table:263-279`): 각 행은 `stage`/`item`/`status`/`status_label`/`row_id` 보유. `status` enum = pending/in_progress/done/failed/na.

#### 2.2.3 영향 범위
- `sync_state_md` 호출자: `cmd_advance`(`1112`), `cmd_mark`(`1281-1283`), `cmd_block`(`1313`), `cmd_add_row`, `cmd_status` 등. **advance/mark만** `next_action`을 계산해 전달, 나머지는 None(=미접촉) → block/add-row의 "다음 액션 보존" 계약 유지.
- `TestFreeTextPreservation`(`test_state_tool.py:1484-1554`)이 mark/advance 후 `## 다음 액션` 섹션 불변을 assert → 반전 대상(F-004).

---

### F-003: advance/mark `--next-action` per-transition 오버라이드

#### 2.3.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/state-tool/state_tool.py` | `build_parser()` `p_adv`(`2105-2114`)·`p_mark`(`2117-2139`) argparse + `cmd_advance`/`cmd_mark` 우선순위 처리 | 수정 |

#### 2.3.2 현재 구현
- `--next-action`은 현재 `p_init`에만 존재(`state_tool.py:2086`). `p_adv`/`p_mark`엔 없음.
- 테스트 헬퍼 `make_args`(`test_state_tool.py:97-141`)는 `next_action` 기본값 None을 이미 포함 → advance/mark가 `getattr(args, "next_action", None)` 접근 시 기존 테스트 AttributeError 없음.

#### 2.3.3 영향 범위
- opal-pilot-* SKILL의 `init --next-action` 호출은 init 한정이라 무영향(R-4 유지). advance/mark `--next-action`은 순수 신규 추가(하위호환 breaking 아님).

---

### F-004: 테스트 — `TestFreeTextPreservation` 반전 + `TestNextActionAutoDerive` 신규

#### 2.4.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 테스트 | `opal/tools/state-tool/tests/test_state_tool.py` | `TestFreeTextPreservation`(`1484-1554`) 반전 + `TestNextActionAutoDerive`(신규) | 수정 |

#### 2.4.2 현재 구현
- `TestFreeTextPreservation`(`1484-1554`)의 4개 보존 테스트 + `test_pipeline_marker_region_only_changed`(`1544-1553`). setUp(`1490-1497`)이 `## 다음 액션` 본문을 `초기 다음 액션\n- 세부 액션 1\n- 세부 액션 2`로 확장하고, `_assert_free_text_preserved`(`1509-1514`)가 블로커·다음 액션 섹션 **전체 문자 동일**을 단언.
- 베이스라인: 로컬 241 테스트 중 **240 pass / 1 fail**. fail 1건은 무관 결함 `TestVerify.test_verify_passes_own_test_scenario_md`(`test_state_tool.py:2177`, 이동된 `tasks/backup/034-.../` 경로 참조).

#### 2.4.3 영향 범위
- 반전 범위는 **mark/advance 2개 테스트로 국한**된다(§3 F-004 설계 참조): block/add-row는 파생을 트리거하지 않으므로 해당 보존 테스트는 GREEN 유지. 모든 테스트의 블로커 섹션 assert도 불변.

---

### F-005: 문서·설계문서 SSOT 개정·배포

#### 2.5.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서 | `opal/core/references/harness/state-template.md` | "다음 액션=PM 수동" 원 설계 문언(`33-42`,`81-82`) 반전 | 수정 |
| 문서 | `opal/tools/state-tool/README.md` | init/advance/mark 섹션(`40-52`,`66-102`)·의존성·변경이력 표(`132-`) 갱신 | 수정 |
| 문서 | `opal/core/references/harness/task-process.md`, `opal/skills/op-task/SKILL.md` | `--next-action` 계약 재인용 지점 보강(경미) | 수정(경미) |
| 도구 | `opal/tools/state-tool/state_tool.py` | @header `description`에 태스크 072 요약 추가 | 수정 |
| 배포 | `scripts/install-mac.sh` (재실행만) | `opal/tools/` → `~/.opal/tools/` 동기화 | 실행 |

#### 2.5.2 현재 구현
- `state-template.md:34`: "이후 갱신 명령은 `## 의사결정 로그`에만 자동 추가 (§2.17), `## 블로커`와 `## 다음 액션`은 PM이 수동 갱신 (state-tool 범위 밖)." — 본 태스크가 반전하는 SSOT 문언.
- `install-mac.sh:1111`이 `opal/tools/` 일괄 동기화. 변경이력 섹션은 install이 배포본에서 자동 strip(`docs/CONVENTIONS.md` §변경이력 작성 의무).

#### 2.5.3 영향 범위
- `header-rules.md:91`, `parallel-execution.md:74`(다음 액션을 자유 텍스트로 전제)는 첫 줄만 치환하는 설계(M-1) 덕에 "폴백 사유 1줄 기록" 관행과 충돌하지 않음 → 문구 변경 불요, 교차 확인만.

---

## 3. 기능별 설계

### F-001: state.json `next_action` 필드 + init 영속화 + 스키마 등록

#### 3.1.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/state-tool/state_tool.py` | 도구 | `cmd_init` state 딕셔너리(`903-912`)에 `"next_action": next_action` 추가 (계산은 `927` 그대로 재사용) | `state_tool.py:903-927` |
| 2 | `opal/tools/state-tool/schema/state.schema.json` | 스키마 | 최상위 `properties`에 `next_action` optional 등록 (`required` 미포함) | `state.schema.json:88-101`(note optional 관례) |

#### 3.1.2 API·데이터 모델·화면 설계

**데이터 모델 — state.json `next_action` 필드**
- 타입: `string | null` (렌더 SSOT). `note` 필드와 동일한 optional 관례를 따른다.
- init 기록값: `state["next_action"] = args.next_action or "PLAN 단계 진입"` — 기존 `927` 계산식을 그대로 딕셔너리에 반영 (→ D-2:927). init 기본값·오버라이드 동작 무변경(R-4 하위호환).
- [MUST] `docs/CONVENTIONS.md` §언어 규칙: "코드/변수/필드명 English" — 필드명은 `next_action`(snake_case) 사용.

**스키마 — `state.schema.json` properties 추가** (`note` 필드 `88-101` 패턴 재사용):
```json
"next_action": {
  "oneOf": [ {"type": "string"}, {"type": "null"} ],
  "description": "STATE.md '## 다음 액션' 렌더 SSOT — advance/mark 시 다음 대기 행에서 자동 파생, init/전이 --next-action 오버라이드 가능 (072). optional (하위호환)"
}
```
- [MUST] `required` 배열(`state.schema.json:6`)에 **추가하지 않는다** — 구버전 state.json 무손상 (H-4). (→ ANALYSIS §3.3, §5)
- `additionalProperties: false`(`:7`)이므로 `properties` 등록은 필수(등록 없으면 향후 strict validate 시 위반).

#### 3.1.3 환경 변경
해당 없음 (표준 라이브러리만, `state_tool.py:16-24`).

#### 3.1.4 배치/마이그레이션
해당 없음 — 필드 부재 시 `state.get("next_action")`가 None 반환하는 fail-safe로 마이그레이션 불요 (TASK §제약 하위호환).

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 AC | 기능 테스트 | init 후 state.json에 `next_action` 키 존재, 값 = `--next-action` 또는 "PLAN 단계 진입" |
| TS-002 | R-1 AC | 회귀 테스트 | 기존 `init --next-action "테스트 다음 액션"` 후 STATE.md 렌더 불변(`test_state_tool.py:280-287` 그린 유지) |
| TS-003 | R-1 / 하위호환 | 회귀 테스트 | `next_action` 없는 구버전 state.json 로드 → advance/mark 무손상(KeyError 없음) |

---

### F-002: 자동 파생 엔진 + 렌더 치환 + advance/mark 통합

#### 3.2.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/state-tool/state_tool.py` | 도구 | `_derive_next_action(state)` 신규 + `update_next_action_section(md, next_action)` 신규 + `sync_state_md`에 `next_action=None` 파라미터 추가 + `cmd_advance`/`cmd_mark`에서 계산·전달 | `state_tool.py:301-315`,`346-371`,`435`,`1112`,`1281-1283` |

#### 3.2.2 API·데이터 모델·화면 설계

**[M-1 확정] 치환 범위 = (b) 첫 줄만 정규식 치환 (하위 자유 기재 보존)**
- 결정: `update_current_status_section()`(`301-315`)을 모델로 한 **정규식 1줄 치환**을 채택한다. `## 다음 액션` 헤더 직후 첫 줄(파생값)만 교체하고, 그 아래 PM 자유 기재 라인(`- 세부 액션 N` 등)은 보존한다. (→ ANALYSIS §4-6, §5; 기존 관례 `test_state_tool.py:1496`)
- 근거: (a) 섹션 전체 덮어쓰기는 매 전이마다 PM 부기 텍스트를 소실시켜 `header-rules.md:91`·`parallel-execution.md:74`의 "폴백 사유 1줄 기록" 관행과 충돌. (b) 1줄 치환은 `update_current_status_section` 기존 관례와 정합.

**신규 함수 — `update_next_action_section`**:
```python
def update_next_action_section(md_content, next_action):
    """G-16: '## 다음 액션' 섹션의 첫 줄(파생값)만 치환. 하위 자유 기재 라인 보존.
    섹션 부재 시 미변경(fail-safe, 레거시 STATE.md 호환)."""
    if next_action is None:
        return md_content
    pattern = re.compile(r"(^## 다음 액션\n)([^\n]*)", re.MULTILINE)
    m = pattern.search(md_content)
    if not m:
        return md_content
    return md_content[:m.start()] + m.group(1) + next_action + md_content[m.end():]
```
- `[^\n]*`는 헤더 다음 첫 줄의 내용만 매칭(개행 미포함) → 둘째 줄부터 보존. 섹션 부재 시 no-op(레거시 호환). (→ 선례 `state_tool.py:301-315`)

**[M-1 확정] 파생 문자열 포맷 + 신규 함수 `_derive_next_action`**:
- 정의: **파이프라인 프론티어 = rows[]를 순서대로 스캔한 첫 미완료 행**(`status ∉ _COMPLETE_STATUSES`). 이 행에서 문자열을 파생한다. `_COMPLETE_STATUSES`(`435`) 재사용 → 070 task-step key 체계 무접촉(row 순서 스캔만, `row_index` 기반). (→ ANALYSIS §4-4)
- 포맷(행 상태별):
  - `pending` → `f"{stage} {item} 진입"` (예: "ANALYSIS 작업 진입")
  - `in_progress` → `f"{stage} {item} 진행 중"` (예: "PLAN 작업 진행 중")
  - `failed` → `f"{stage} {item} 블로커 해소"` (방어적 — 정상 advance/mark 흐름에서는 stage guard가 앞 실패행 통과를 차단하므로 도달 드묾)
  - 미완료 행 없음(전체 완료) → `"태스크 완료"` **[M-2 확정]**
```python
def _derive_next_action(state):
    """G-16: 파이프라인 프론티어(첫 미완료 행)에서 '다음 액션' 문자열 파생.
    전체 완료 시 '태스크 완료'(M-2). 070 정합: row 순서 스캔 + _COMPLETE_STATUSES 재사용."""
    for row in state.get("rows", []):
        st = row.get("status")
        if st in _COMPLETE_STATUSES:
            continue
        stage, item = row.get("stage", ""), row.get("item", "")
        if st == "in_progress":
            return f"{stage} {item} 진행 중"
        if st == "failed":
            return f"{stage} {item} 블로커 해소"
        return f"{stage} {item} 진입"   # pending
    return "태스크 완료"
```
- [M-2 경계 처리 지점] "전체 완료" 판정은 `_derive_next_action`의 루프 미스 시 `return "태스크 완료"` 한 곳. CLOSE 마지막 행 mark done 직후 이 경로로 진입(모든 행 `_COMPLETE_STATUSES`).

**`sync_state_md` 시그니처 확장** (`346-371`):
```python
def sync_state_md(task_path, state, now_str, command,
                  progress=None, status_text=None,
                  decision=None, reason=None, next_action=None):  # next_action 신규
    ...
    replaced = update_current_status_section(replaced, progress=progress, status_text=status_text)
    replaced = update_next_action_section(replaced, next_action)  # None이면 no-op → 기존 호출부 무영향
    if decision is not None:
        replaced = append_decision_log(...)
```
- [MUST] block/add-row/status 호출부는 `next_action` 인자를 넘기지 않음(기본 None) → "다음 액션 미접촉" 계약 유지 (H-5). TASK §범위 "제외: 블로커 섹션 동작 변경"과 정합.

**`cmd_advance` 통합** (`1101-1112` 부근):
```python
# 상태 변경(row["status"]="in_progress") 및 save_state_json 후
state["next_action"] = getattr(args, "next_action", None) or _derive_next_action(state)
save_state_json(task_path, state)  # next_action 영속화
progress = f"{row['stage']} 단계"
sync_state_md(task_path, state, now_str, command, progress=progress,
              next_action=state["next_action"])
```

**`cmd_mark` 통합** (`1252`·`1281-1283` 부근): 상태 확정(done/in_progress) 후 동일 패턴으로 `state["next_action"]` 계산·`save_state_json`·`sync_state_md(..., next_action=state["next_action"])`.
- 파생은 **상태 변경이 state에 반영된 뒤** 호출 → 프론티어가 방금 전이한 행 이후로 자연 이동(mark done 시 다음 행, advance in_progress 시 그 행 자신 "진행 중").
- [R-3] 렌더는 `update_next_action_section`이 STATE.md `## 다음 액션` 첫 줄을 `state["next_action"]`으로 치환 → state.json 미러 정합.

#### 3.2.3 환경 변경
해당 없음.

#### 3.2.4 배치/마이그레이션
해당 없음.

#### 3.2.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-004 | R-2 AC | 기능 테스트 | 여러 행 순차 advance/mark → 각 시점 STATE.md·state.json `next_action`이 프론티어 행을 정확히 반영 |
| TS-005 | R-2 / M-2 | 기능 테스트 | CLOSE 마지막 행 mark done → `next_action == "태스크 완료"` |
| TS-006 | R-3 AC | 기능 테스트 | advance/mark 후 STATE.md `## 다음 액션` 첫 줄 == state.json `next_action` |
| TS-007 | R-2 / M-1 | 기능 테스트 | `## 다음 액션` 하위 자유 기재 라인(`- 세부 액션 1/2`) 전이 후 보존 |
| TS-008 | R-2 / H-5 | 회귀 테스트 | block/add-row 후 `## 다음 액션` 섹션 전체 불변 |
| TS-009 | R-2 / in_progress | 기능 테스트 | advance(row→in_progress) 후 파생값 == "{stage} {item} 진행 중" |

---

### F-003: advance/mark `--next-action` per-transition 오버라이드

#### 3.3.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/state-tool/state_tool.py` | 도구 | `p_adv`(`2105-2114`)·`p_mark`(`2117-2139`)에 `--next-action` 선택 인자 추가 (init `2086` 동형) | `state_tool.py:2086` |

#### 3.3.2 API·데이터 모델·화면 설계

**[M-3 확정] 오버라이드 지속성 = per-transition (비지속) + 다음 전이 시 자동 파생 복귀**
- 결정: advance/mark `--next-action <text>`는 **해당 전이 1회에만** 적용된다. 다음 전이가 `--next-action` 없이 실행되면 자동 파생으로 복귀한다. (→ ANALYSIS §M-3)
- 근거·상호작용 규칙:
  1. 우선순위: `state["next_action"] = args.next_action or _derive_next_action(state)` — 오버라이드가 파생보다 우선(R-4 AC).
  2. state.json `next_action`은 "마지막 write 값"을 담는 렌더 미러일 뿐 **지속 정책 필드가 아니다**. 매 advance/mark가 오버라이드 또는 파생으로 새로 write → 다음 전이에서 오버라이드 미지정 시 파생값이 덮어씀.
  3. 지속 오버라이드는 결함(영구 stale)을 재도입하므로 채택하지 않는다 — "enforce, don't advise"(`~/.opal/PRINCIPLES.md`, → D-5).
- argparse: `p_adv.add_argument("--next-action")`, `p_mark.add_argument("--next-action")` (init `2086` 동형, dest 기본 `next_action`).

#### 3.3.3 환경 변경
해당 없음.

#### 3.3.4 배치/마이그레이션
해당 없음.

#### 3.3.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-010 | R-4 AC | 기능 테스트 | advance/mark `--next-action "커스텀"` → `next_action == "커스텀"`(파생보다 우선) |
| TS-011 | R-4 / M-3 | 기능 테스트 | 오버라이드 전이 → 이후 `--next-action` 없는 전이 → 자동 파생값으로 복귀(비지속) |

---

### F-004: 테스트 — `TestFreeTextPreservation` 반전 + `TestNextActionAutoDerive` 신규

#### 3.4.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/state-tool/tests/test_state_tool.py` | 테스트 | `TestFreeTextPreservation` mark/advance 2개 테스트 반전 + 신규 `TestNextActionAutoDerive` 클래스 추가 | `test_state_tool.py:1484-1554` |

#### 3.4.2 API·데이터 모델·화면 설계

**[MUST][R-2 반전 계획] `TestFreeTextPreservation` 재정의 — "블로커 완전 보존 / 다음 액션 파생 갱신"** (→ ANALYSIS §1.4, §4-5)
- 클래스 docstring(`1485-1488`) 갱신: "블로커는 전 명령 보존. 다음 액션은 mark/advance 시 파생 갱신(첫 줄), block/add-row 시 보존. 하위 자유 기재 라인은 전 명령 보존."
- 반전 대상(2개, **회귀 아님 — 의도된 설계 반전**):
  - `test_mark_preserves_free_text`(`1516-1521`) → **`test_mark_derives_next_action_preserves_others`**: (a) 블로커 섹션 불변 assert 유지, (b) `## 다음 액션` 첫 줄 == `_derive_next_action` 기대값 assert, (c) 하위 자유 기재 라인(`- 세부 액션 1/2`) 잔존 assert.
  - `test_advance_preserves_free_text`(`1523-1528`) → **`test_advance_derives_next_action_preserves_others`**: 동형.
- 유지 대상(GREEN, 변경 없음): `test_block_preserves_free_text`(`1530-1535`), `test_add_row_preserves_free_text`(`1537-1542`), `test_pipeline_marker_region_only_changed`(`1544-1553`, 블로커만 assert). ← block/add-row는 파생 미트리거(§3 F-002 H-5 설계) → 전체 보존 성립.
- 근거 인용 갱신: 각 반전 테스트 docstring의 `(PLAN §3 Step 2)` → 본 태스크 `(PLAN 072 F-002/F-004)`로 정정.

**[RED-first] 신규 `TestNextActionAutoDerive` 클래스** (배치: `TestFreeTextPreservation` 인접, `# E.` 섹션 하위 또는 신규 `# E-2.` 라벨 — `test_state_tool.py:1480` 관례):
- RED-first 트랙 적격(동작 변경). EXECUTE Step 1에서 **파생 전 코드로 이 클래스를 실행해 RED 확인**(advance/mark `--next-action` 부재로 argparse 에러 또는 파생 미수행으로 assert 실패) 후 구현 진입. TEST-SCENARIO(STEP 3.5, PM)에서 RED 증거를 구체화.
- 커버 테스트(TS-001~011 대응): init next_action 영속(TS-001), 순차 전이 프론티어 파생(TS-004), 전체 완료 "태스크 완료"(TS-005), 렌더-json 정합(TS-006), 자유기재 보존(TS-007), in_progress 파생(TS-009), 오버라이드 우선(TS-010), 오버라이드 비지속 복귀(TS-011), 구버전 state.json 하위호환(TS-003).

#### 3.4.3 환경 변경
해당 없음 (unittest 표준 라이브러리, `test_state_tool.py:35`).

#### 3.4.4 배치/마이그레이션
해당 없음.

#### 3.4.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-012 | R-5 / RED-first | 회귀 테스트 | `TestNextActionAutoDerive`가 파생 전 코드에서 RED, 구현 후 GREEN |
| TS-013 | R-5 반전 | 회귀 테스트 | `TestFreeTextPreservation` 반전 2개 GREEN + 유지 3개 GREEN |
| TS-014 | R-5 베이스라인 | 회귀 테스트 | 무관 실패 1건(`test_verify_passes_own_test_scenario_md`) 제외 **240 pass 유지** + 반전분 반영 |

---

### F-005: 문서·설계문서 SSOT 개정·배포

#### 3.5.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/harness/state-template.md` | 문서 | `34`(자유텍스트 3섹션 설명)·`40`(표 "다음 액션" 행)·`82`(템플릿 주석) 반전 — "다음 액션은 advance/mark 자동 파생, 오버라이드만 수동" | `state-template.md:33-42,81-82` |
| 2 | `opal/tools/state-tool/README.md` | 문서 | init/advance/mark 섹션에 `next_action` 필드·자동 파생·`--next-action` 오버라이드(M-3) 반영 + 변경이력 표에 072 행 | `README.md:40-102,132-` |
| 3 | `opal/core/references/harness/task-process.md`, `opal/skills/op-task/SKILL.md` | 문서 | `--next-action` 계약에 "advance/mark에서도 자동 갱신" 1줄 보강(경미) | `task-process.md:42`, `op-task/SKILL.md:219` |
| 4 | `opal/tools/state-tool/state_tool.py` | 도구 | @header `description`에 072 요약 1문 추가 | `state_tool.py:2-13` |

#### 3.5.2 API·데이터 모델·화면 설계

**[MUST] 설계 SSOT 반전 — `state-template.md`** (→ ANALYSIS §4-1, §3.1):
- `state-template.md:34` 원문 "…`## 블로커`와 `## 다음 액션`은 PM이 수동 갱신 (state-tool 범위 밖)." → "…`## 블로커`는 PM이 수동 갱신(state-tool 범위 밖). `## 다음 액션`은 advance/mark 시 파이프라인 프론티어에서 자동 파생·갱신되며(첫 줄), 하위 자유 기재는 보존된다. init/전이 `--next-action`으로 오버라이드 가능(072)."
- `:40` 표 행 "다음 액션 | `--next-action` 인자 값 또는 기본값" → "자동 파생값(첫 줄, advance/mark 갱신) / `--next-action` 오버라이드".
- `:82` 템플릿 주석 동기화.

**[MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무**: "일시는 `YYYY-MM-DD HH:mm`(KST), 버전 semver, 변경내용은 태스크 번호 괄호 포함" — README·state-template.md·citation 등 변경 문서에 `(072)` 행 추가. 배포 시 install이 변경이력 strip.
- README 변경이력 추가 행(예): `| v1.6 | 2026-07-23 HH:mm | (072) | STATE.md "다음 액션" 자동 파생 — state.json next_action 필드 신설·advance/mark 프론티어 파생·update_next_action_section(첫 줄 치환)·--next-action 오버라이드(비지속) |`

**[MUST] `docs/CONVENTIONS.md` §@header 규칙**: state_tool.py @header `description`(`:6`)에 072 요약 1문 append(기존 서술형 관례 유지).

**[MUST] `docs/CONVENTIONS.md` §배포 경계**: `~/.opal/` 직접 편집 금지, `opal/` 소스 수정 후 `./scripts/install-mac.sh` 재실행으로 `~/.opal/tools/state-tool/` 재배포. 별도 배포 스크립트 수정 불요(`install-mac.sh:1111` 기존 동기화 흡수, → ANALYSIS §3.3).

#### 3.5.3 환경 변경
해당 없음.

#### 3.5.4 배치/마이그레이션
`./scripts/install-mac.sh` 재실행(배포). 배포본 diff 0 확인.

#### 3.5.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-015 | R-6 / 추적성 | 산출물 검사 | README·state-template.md·@header에 072 반영 + 변경이력 행 추가 |
| TS-016 | R-6 / 설계반전 | 산출물 검사 | `state-template.md`에 "다음 액션 수동" 문언 잔존 0건 |
| TS-017 | R-6 배포 | 산출물 검사 | install 후 `~/.opal/tools/state-tool/state_tool.py`가 소스와 일치(변경이력 strip 제외) |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)
| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-004(RED) | 1 | opal-task-agent | 순차 | RED-first: 신규 테스트 선작성·RED 확인 |
| 2 | F-001 | 2 | opal-task-agent | 순차 | 스키마+init 영속화 |
| 3 | F-002 | 3 | opal-task-agent | 순차 | 파생 엔진+렌더+advance/mark |
| 4 | F-003 | 4 | opal-task-agent | 순차 | --next-action 오버라이드 |
| 5 | F-004(반전+GREEN) | 5 | opal-task-agent | 순차 | 테스트 반전 + 전체 회귀 GREEN |
| 6 | F-005 | 6, 7 | opal-task-agent | 순차 | 문서·설계문서 + install 배포 |

### 4.2 실행 체크리스트
> 총 7개 Step | Phase 6개 | 실행 모드: 복잡 (변경 파일 5개 ≥4) — 단, 단일 모듈·단일 에이전트 순차

#### Step 1: RED-first — 신규 `TestNextActionAutoDerive` 작성 및 RED 확인
- [ ] 완료
- **소속 기능**: F-004
- **영역**: 테스트
- **agent**: opal-task-agent
- **파일**: `opal/tools/state-tool/tests/test_state_tool.py`
- **작업 내용**: `TestFreeTextPreservation` 인접에 `TestNextActionAutoDerive` 클래스 신규 작성 (TS-001·003·004·005·006·007·009·010·011 커버). 파생 전 코드로 실행하여 RED(실패 출력) 확보.
- **완료 기준**: 신규 클래스가 파생 전 코드에서 실패(RED)함을 실행 로그로 확인. 기존 240 pass는 불변.
- **테스트**: TS-012
- **실행 방법**: direct
- **의존**: 없음

#### Step 2: F-001 — state.json `next_action` 필드 + init 영속화 + 스키마 등록
- [x] 완료
- **소속 기능**: F-001
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/state-tool/state_tool.py`, `opal/tools/state-tool/schema/state.schema.json`
- **작업 내용**: `cmd_init` state 딕셔너리(`903-912`)에 `"next_action"` 추가. schema `properties`에 `next_action`(oneOf string/null) 등록, `required` 미추가.
- **완료 기준**: init 후 state.json에 `next_action` 키 존재. TS-001~003 GREEN. schema `required` 불변.
- **테스트**: TS-001, TS-002, TS-003
- **실행 방법**: direct
- **의존**: Step 1

#### Step 3: F-002 — 자동 파생 엔진 + 렌더 치환 + advance/mark 통합
- [x] 완료
- **소속 기능**: F-002
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/state-tool/state_tool.py`
- **작업 내용**: `_derive_next_action(state)`·`update_next_action_section(md, next_action)` 신규. `sync_state_md`에 `next_action=None` 파라미터 추가. `cmd_advance`/`cmd_mark`에서 상태 반영 후 `state["next_action"]` 계산·저장·전달. block/add-row/status 호출부는 미전달(None).
- **완료 기준**: TS-004~009 GREEN. block/add-row 다음 액션 불변(TS-008). 070 key 체계 무접촉.
- **테스트**: TS-004~009
- **실행 방법**: direct
- **의존**: Step 2

#### Step 4: F-003 — advance/mark `--next-action` per-transition 오버라이드
- [x] 완료
- **소속 기능**: F-003
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/state-tool/state_tool.py`
- **작업 내용**: `p_adv`·`p_mark`에 `--next-action` 추가. `cmd_advance`/`cmd_mark`에서 `args.next_action or _derive_next_action(state)` 우선순위. 오버라이드는 비지속(M-3).
- **완료 기준**: TS-010·011 GREEN. 오버라이드 우선 + 다음 전이 파생 복귀.
- **테스트**: TS-010, TS-011
- **실행 방법**: direct
- **의존**: Step 3

#### Step 5: F-004 — `TestFreeTextPreservation` 반전 + 전체 회귀 GREEN
- [x] 완료
- **소속 기능**: F-004
- **영역**: 테스트
- **agent**: opal-task-agent
- **파일**: `opal/tools/state-tool/tests/test_state_tool.py`
- **작업 내용**: `test_mark_preserves_free_text`·`test_advance_preserves_free_text`를 "블로커 보존 + 다음 액션 파생 + 자유기재 보존"으로 반전(테스트명·docstring·근거 인용 갱신). block/add-row/marker 테스트는 유지. 전체 스위트 실행.
- **완료 기준**: TS-012~014 GREEN. 무관 1건 제외 240 pass + 신규/반전분 GREEN. RED-first 클래스가 GREEN 전환.
- **테스트**: TS-012, TS-013, TS-014
- **실행 방법**: direct
- **의존**: Step 4

#### Step 6: F-005 — 문서·설계 SSOT 반전 + @header + 변경이력
- [x] 완료
- **소속 기능**: F-005
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/core/references/harness/state-template.md`, `opal/tools/state-tool/README.md`, `opal/core/references/harness/task-process.md`, `opal/skills/op-task/SKILL.md`, `opal/tools/state-tool/state_tool.py`(@header)
- **작업 내용**: state-template.md `34`/`40`/`82` 반전. README init/advance/mark + 변경이력 072 행. task-process/op-task 경미 보강. state_tool.py @header에 072 요약. 변경이력 일시 = KST `node ~/.opal/tools/date/date.js datetime`.
- **완료 기준**: TS-015·016 GREEN. "다음 액션 수동" 잔존 0건. CONVENTIONS §변경이력/@header 준수.
- **테스트**: TS-015, TS-016
- **실행 방법**: direct
- **의존**: Step 5

#### Step 7: F-005 — install 배포 + 배포본 정합 검증
- [x] 완료
- **소속 기능**: F-005
- **영역**: 배포
- **agent**: opal-task-agent
- **파일**: `scripts/install-mac.sh`(재실행), `~/.opal/tools/state-tool/`(배포 대상, 직접 편집 금지)
- **작업 내용**: `./scripts/install-mac.sh` 재실행. 배포본 `~/.opal/tools/state-tool/state_tool.py`·`schema/state.schema.json`이 소스와 일치(변경이력 strip 제외) 확인.
- **완료 기준**: TS-017 GREEN. 배포본-소스 diff 0(변경이력 제외).
- **테스트**: TS-017
- **실행 방법**: direct
- **의존**: Step 6

> **docs/ 갱신 판단**: 본 변경은 `opal/tools/` 내부 CLI 도구 + `opal/core/references/harness/` 설계문서 범위다. 프로젝트 `docs/`(PROJECT.md/ARCHITECTURE.md/CONVENTIONS.md 등)는 프레임워크 개요·규약이며 이 변경으로 내용이 달라지지 않는다(state 관리 규약 `docs/CONVENTIONS.md:183-188`은 서브명령 목록 수준이라 무영향) → **docs/ 갱신 Step 불요**. 설계 SSOT 반전은 harness 문서(state-template.md)로 Step 6에 흡수.

### 4.3 병렬/순차 판별 근거
| 관계 | 근거 |
|------|------|
| Step 1 → 2 → 3 → 4 → 5 | 전부 `state_tool.py`/`test_state_tool.py` 동일 파일 순차 수정 — 파일 충돌 방지 위해 단일 에이전트 순차 |
| Step 3 ← Step 2 | 파생 엔진이 F-001의 `next_action` 필드에 의존 |
| Step 5 ← Step 4 | 반전 테스트는 오버라이드까지 구현된 최종 동작 검증 |
| Step 6 → 7 | 문서 확정 후 배포(소스→배포본 동기화) |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA
| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | init이 state.json에 `next_action` 기록 + schema optional 등록 | TS-001, TS-002, TS-003 | 키 존재·기존 렌더 불변·구버전 무손상·`required` 불변 |
| F-002 | advance/mark 프론티어 자동 파생 + 첫 줄 치환 렌더 + 자유기재 보존 | TS-004~009 | 순차 전이 정확 반영·전체완료 "태스크 완료"·state-md 정합·자유기재 잔존·block/add-row 불변 |
| F-003 | `--next-action` 오버라이드 우선 + 비지속 복귀 | TS-010, TS-011 | 오버라이드 값 우선·다음 전이 파생 복귀 |
| F-004 | RED-first + `TestFreeTextPreservation` 반전 + 베이스라인 | TS-012, TS-013, TS-014 | RED→GREEN·반전 2 + 유지 3 GREEN·240 pass 유지 |
| F-005 | 문서·설계 SSOT 반전 + @header/변경이력 + 배포 정합 | TS-015, TS-016, TS-017 | 072 반영·"수동" 잔존 0·배포본 diff 0 |

### 5.2 회귀 테스트
- [x] 무관 실패 1건(`test_verify_passes_own_test_scenario_md`) **제외** 240 pass 유지 (ANALYSIS §1.4 베이스라인)
- [x] `TestFreeTextPreservation` 반전은 **회귀 아님 — 의도된 설계 반전**임을 TEST-SCENARIO에 근거로 기록
- [x] block/add-row/status의 `## 다음 액션` 미접촉 계약 불변
- [x] 070 task-step key 체계(`resolve_row_index`·`--task-step`) 무접촉
- [x] 기존 `init --next-action` 동작·기본값("PLAN 단계 진입") 불변

### 5.3 코드/문서 품질
- [x] `docs/CONVENTIONS.md` §@header 규칙: state_tool.py @header 갱신
- [x] `docs/CONVENTIONS.md` §변경이력 작성 의무: README 등 `(072)` 행 + KST 일시 + semver
- [x] `docs/CONVENTIONS.md` §언어 규칙: 코드/필드명 English(`next_action` snake_case)
- [x] 표준 라이브러리만 사용(신규 import 없음, `state_tool.py:16-24`)
- [x] 설계 SSOT `state-template.md`에 낡은 "다음 액션 수동" 문언 잔존 0건

### 5.4 보안
- [x] 하드코딩 시크릿/토큰 없음 (내부 CLI, 표준 라이브러리)
- [x] `.opal/` 배포 파일 직접 편집 없음 — 소스만 수정 후 install (`docs/CONVENTIONS.md` §배포 경계)
- [x] 사용자 입력(`--next-action` 문자열)은 STATE.md 텍스트로만 삽입 — 정규식 치환 시 개행 미포함(`[^\n]*`)으로 섹션 경계 오염 방지

---

## 6. 복잡도 판별
| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 7개 | 복잡 |
| 변경 파일 수 | 5개 (state_tool.py, state.schema.json, test_state_tool.py, README.md, state-template.md; task-process/op-task 경미) | 복잡 |
| 모듈 범위 | 단일 (state-tool) | 단순 |
| 작업 유형 | 결함 수정 + 설계 반전 | 단순~복잡 경계 |
| 외부 의존성 | 없음 (표준 라이브러리) | 단순 |
| **실행 모드** | **복잡** (Step·파일 수 기준) — 단, 단일 모듈·단일 에이전트 순차로 토폴로지 단순 | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지
- 단일 에이전트 순차 파이프라인: `opal-task-agent`가 Step 1→7을 순차 실행(오케스트레이터 지시: 단일 영역·단일 배치). 파일 충돌 방지 원칙상 `state_tool.py`/`test_state_tool.py` 동일 파일 반복 수정은 반드시 동일 에이전트에 배치 → 병렬 분리 없음.
- Batch 1(순차): Step 1(RED) → Step 2~4(구현) → Step 5(반전·회귀) → Step 6~7(문서·배포).

### C-2. 스킬 요구사항
- 기존 스킬로 충분 — state-tool은 프로젝트 내부 도구. 신규 스킬 갭 없음. (ANALYSIS §6.2)

### C-3. 도구 요구사항
- Python 3(`~/.opal/.venv/bin/python`), `unittest`(표준), `node ~/.opal/tools/date/date.js datetime`(KST 변경이력), `./scripts/install-mac.sh`(배포). 신규 패키지·MCP 없음.

### C-4. 테스트 전략
- RED-first: Step 1에서 `TestNextActionAutoDerive` RED 증거 확보 → Step 3~4 구현 후 GREEN.
- 기능 테스트: `~/.opal/.venv/bin/python -m unittest` (또는 프로젝트 표준 러너)로 `test_state_tool.py` 전체 실행.
- 회귀: 무관 1건 제외 240 pass 유지 + 반전 2건 + 신규 클래스 GREEN.
- 코드 품질: @header/변경이력 검사(산출물 검사). 배포 정합: 소스-배포본 diff.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 언어 | Python 3 (표준 라이브러리만: json/argparse/re/pathlib) | (프로젝트 내부 도구) |
| 테스트 | unittest (표준 라이브러리) | - |
| 스키마 | JSON Schema Draft-07 (참조용, 런타임 미검증) | - |
| 배포 | bash `scripts/install-mac.sh` | - |

> `trailofbits/modern-python` 스킬은 uv/ruff/async 등 신규 툴체인 도입 시 유효하나, 본 태스크는 표준 라이브러리만 사용하는 기존 CLI 수정이라 적용 대상 아님(ANALYSIS §6.2·§2).

### 8.2 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|
| (없음) | 표준 라이브러리 기반 내부 도구 — 외부 API 문서 조회 불요 |

### 8.3 참조 문서 (설계 결정 근거)
| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py` | init/advance/mark/sync_state_md/_COMPLETE_STATUSES·파생/렌더 대상 (R-1~R-4) |
| D-2 | 소스 | state.schema.json | `opal/tools/state-tool/schema/state.schema.json` | next_action 필드 추가·required 비추가 (R-1) |
| D-3 | 소스 | test_state_tool.py | `opal/tools/state-tool/tests/test_state_tool.py` | TestFreeTextPreservation 반전·신규 클래스·베이스라인 (R-5) |
| D-4 | 소스 | state-tool README | `opal/tools/state-tool/README.md` | 문서 정합·변경이력 (R-6) |
| D-5 | 설계 | state-template.md | `opal/core/references/harness/state-template.md` | "다음 액션 수동" 원 설계 SSOT — 반전 대상 |
| D-6 | 설계 | OPAL 헌법 | `~/.opal/PRINCIPLES.md` | enforce-don't-advise 근거 (M-3 비지속 오버라이드) |
| D-7 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | @header/변경이력/배포경계/네이밍 규칙 |
| D-8 | 소스 | install-mac.sh | `scripts/install-mac.sh:1111` | opal/tools → ~/.opal/tools 배포 경계 (R-6) |

---

## 9. 리스크 및 대응 (기능-리스크 연결)
| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| 1 | `TestFreeTextPreservation` RED를 회귀로 오인 | F-004 | P0 | H-1·§5.2에 "의도된 설계 반전" 명시, TEST-SCENARIO에 RED 근거 기록, 반전 범위 mark/advance 2건으로 국한 |
| 2 | 파생 프론티어 경계 오판(전체완료/실패행/다중 in_progress) | F-002 | P1 | `_derive_next_action` 상태별 분기 + `_COMPLETE_STATUSES` 재사용, TS-005·009 경계 테스트 |
| 3 | 섹션 전체 덮어쓰기로 PM 자유기재 소실 | F-002 | P1 | M-1 결정 = 첫 줄만 치환(`[^\n]*`), TS-007 보존 검증 |
| 4 | schema `required` 오추가로 하위호환 파괴 | F-001 | P1(향후) | `required` 미추가(properties만), TS-003 구버전 무손상 |
| 5 | sync_state_md 시그니처 확장이 block/add-row 계약 파괴 | F-002 | P1 | `next_action=None` 기본값 + block/add-row 미전달, TS-008 |
| 6 | 오버라이드 지속 오해로 stale 재도입 | F-003 | P1 | M-3 = per-transition 비지속 명문화, TS-011 복귀 검증 |
| 7 | 배포본-소스 드리프트 | F-005 | P1 | install 재실행 + 배포본 diff 0(TS-017), 변경이력 strip 인지 |
| 8 | 070 task-step key 체계 훼손 | F-002 | P1 | row 순서 스캔·row_index 기반, key/resolve_row_index 무접촉 (ANALYSIS §4-4) |
