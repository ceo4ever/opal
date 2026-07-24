# PLAN: 산출물 소유자 호칭을 identity.md owner_name 기준으로 하네스 통일

> 작성일: 2026-07-10 | 입력: TASK.md (ANALYSIS.md 없음 — 코드 직접 분석)
> 모드: Multi-Feature (F-001 도구 집행 / F-002 문서 규칙)

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

OPAL 산출물의 소유자 호칭이 로컬 `~/.opal/identity.md`의 `owner_name`이 아니라 세션에 로드된 레포 컨텍스트(MEMORY·brain·직전 태스크 산출물)의 지배 호칭에 오염되는 결함을 A(도구 집행)+B(문서 규칙) 공조로 차단한다. A는 `state-tool`이 note 작성 시점에 `{owner_name}` 플레이스홀더를 identity.md 값으로 결정론적 치환하여 도구가 닿는 경로(state.json note)를 봉인한다. B는 하네스 SSOT에 "매 작성 시점 identity.md 재해석 + 레포 컨텍스트 계승 금지" 규칙을 명문화하고 note 예시를 `{owner_name}`으로 통일하여 도구가 안 닿는 자유서술 산출물(DONE.md 등)을 규칙으로 커버한다.

### 1.2 참조 문서 테이블 (설계 근거 SSOT)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py` | note 저장 로직 — A 도구 집행 대상 |
| D-2 | 소스 | test_state_tool.py | `opal/tools/state-tool/tests/test_state_tool.py` | 테스트 하네스 — RED-first 대상 |
| D-3 | 설계 | state-tool README | `opal/tools/state-tool/README.md` | --note/--owner 계약 — 하위호환 문서화 |
| D-4 | 설계 | AGENT.md §정체성 적용 | `opal/core/AGENT.md` (라인 88-96) | 소유자 호칭 규칙 SSOT — B 보강 지점 |
| D-5 | 설계 | harness/state.md | `opal/core/references/harness/state.md` | note/사용자 확인 행 규칙 — B 파생 규칙 |
| D-6 | 설계 | opal-harness-agentic.md | `opal/core/references/opal-harness-agentic.md` (105) | note 예시 `{owner_name} 확인` (이미 준수) |
| D-7 | 설계 | opal-harness-semi-agentic.md | `opal/core/references/opal-harness-semi-agentic.md` (71) | note 예시 (이미 준수) |
| D-8 | 설계 | tools.md | `opal/core/references/tools.md` (175) | note 예시 (이미 준수) |
| D-9 | 소스 | identity-template.md | `opal/core/identity-template.md` | owner_name frontmatter 스키마 확인 |
| D-10 | 설계 | citation-rules.md §5 | `opal/core/references/harness/citation-rules.md` | 레거시 호환 — 과거 산출물 소급 정정 제외 근거 |

### 1.3 [MUST] 제약 인용 (재해석 방지)

- [MUST] `.opal/AGENT.md` 금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스(`opal/`)를 수정한 뒤 install로 재배포한다." → 모든 변경 대상은 `opal/` 소스 경로로 기재.
- [MUST] `opal/core/PRINCIPLES.md` Core Stance: "Platform-independent: keep Claude/Cursor/Gemini branches in adapters, never in logic." → identity 경로는 `OPAL_HOME` 기준 해석, 하드코딩 분기 금지.
- [MUST] `opal/tools/state-tool/tests/test_state_tool.py:26` (TASK T-11): "표준 라이브러리만 import (pytest/hypothesis 금지)" → YAML 파서(PyYAML) 도입 금지, 정규식 파싱 사용.
- [MUST] `opal/core/references/harness/citation-rules.md` §5(레거시 호환 원칙): 과거 산출물(기존 state.json note)은 소급 정정하지 않는다 → 하위호환 회귀 0 설계.

> 프로젝트에 `docs/CONVENTIONS.md` 부재 — CONVENTIONS 인용 자동 스킵 (SKILL.md 품질 체크 마지막 항목 상속). 개발 규칙은 `opal/core/PRINCIPLES.md`·태스크 로컬 상수(T-11)로 대체.

### 1.4 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | (A) state-tool identity 치환 + 하위호환/폴백 | R-1, R-2 | P0 | 없음 |
| F-002 | (B) 하네스 오염 차단 규칙 명문화 + note 예시 통일 | R-3, R-4, R-5 | P0 | 없음 (F-001과 병렬 가능) |

### 1.5 기능 의존 그래프 (ASCII)

```
F-001 (A: 도구 집행) ──┐
                       ├─→ (독립·병렬 가능, 상호 의존 없음)
F-002 (B: 문서 규칙) ──┘
```

F-001과 F-002는 상호 의존이 없다. 단, F-002의 note 예시가 `{owner_name}`으로 통일되어야 F-001의 치환이 실제 산출물에서 효력을 발휘하므로 **공조 관계**이나 구현 순서상 병렬 가능하다.

---

## 리스크 가설 표

> PLAN 단계 작성. TEST-SCENARIO.md §1의 입력이 됨.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | `resolve_owner_placeholder()` 신설 (state_tool.py) | note 저장 계약: 플레이스홀더 포함 note가 실제 owner_name으로 치환 저장되어야 함 (self-confirming 위험 영역) | P0 | L1(단위, RED-first) + L2(실 파일 I/O) | S-1(RED)·S-2(GREEN) |
| H-2 | note-write 경로 6곳 wrap | 하위호환 계약: 플레이스홀더 없는 기존 note는 byte-identical 불변(회귀 0) | P0 | L1(단위 회귀) | S-3 |
| H-3 | identity.md 파일 I/O + frontmatter 파싱 | 폴백 계약: 파일 부재/owner_name 공란/파싱 실패 시 에러 없이 원문(플레이스홀더) 유지 | P1 | L1(단위, 3케이스) | S-4·S-5·S-6 |
| H-4 | `OPAL_HOME` 경로 해석 | 플랫폼 독립 계약: 하드코딩 `~/.opal` 분기 없이 `OPAL_HOME` env 우선 (테스트 주입 가능성 = 검증 가능성) | P1 | L1(단위, env 주입) | S-2·S-4 |
| H-5 | auto-pass note 접두("agentic auto-pass: ")와 치환 상호작용 | 조합 계약: 접두 note의 플레이스홀더도 치환되고 접두는 보존 | P2 | L1(단위) | S-7 |
| H-6 | B: 8개 skill note 예시 문자열 치환 | 문서 계약: `'소유자 확인:'` 하드코딩 0건 + `{owner_name}` 통일 | P1 | L1(grep 정적 검증) | S-8 |
| H-7 | B: SSOT 규칙 명문화 (AGENT.md + state.md) | 문서 계약: 오염 차단 규칙 문장이 지정 위치에 존재 + 중복 없이 상속 | P2 | L1(grep/존재 검증) | S-9 |

---

## 2. 기능별 분석

### F-001: (A) state-tool identity 치환 + 하위호환/폴백

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/state-tool/state_tool.py` | note 저장 로직 (`cmd_advance`/`cmd_mark`/`cmd_add_row`/`cmd_block`/`cmd_status`/`cmd_init`) | 수정 |
| 도구 | `opal/tools/state-tool/tests/test_state_tool.py` | 단위 테스트 하네스 | 수정 (RED-first 추가) |
| 문서 | `opal/tools/state-tool/README.md` | 도구 계약 문서 | 수정 |

#### 2.1.2 현재 구현 (코드 분석 결과)

- note는 사용자 free text가 그대로 저장된다. identity.md를 읽는 로직은 **없다** (`state_tool.py` 전체 grep 결과 `owner_name`/`identity.md` 참조 0건).
- **note-write 경로 6곳** (D-1):
  - `cmd_advance`: `row["note"] = args.note` (`state_tool.py:872-873`)
  - `cmd_mark`: auto-pass 분기 `f"agentic auto-pass: {args.note}"` / owner 분기 / PM 분기 (`state_tool.py:975-988`)
  - `cmd_add_row`: `"note": args.note or None` (`state_tool.py:1160`)
  - `cmd_block`: `row["note"] = f"block: {args.reason}"` (`state_tool.py:1061`) — 입력은 `--reason`
  - `cmd_status`: `reason = args.note` → `append_decision_log` (`state_tool.py:1228`)
  - `cmd_init`: `--force` 시 `append_decision_log(..., args.note)` (`state_tool.py:738`)
- `--owner`는 역할 enum(`PM`/`worker`/`user`/`auto`)이며 사람 이름이 아니다 (`state_tool.py:1821`).
- 도구는 표준 라이브러리만 import한다 (`state_tool.py:15-23`: argparse/fnmatch/json/os/pathlib/re/subprocess/sys/datetime). **PyYAML 없음** → identity frontmatter는 정규식 파싱 필수 (T-11).
- 다른 도구의 `OPAL_HOME` 해석 선례: `opal/tools/doctor/lib/checks.sh:25` `OPAL_HOME="${OPAL_HOME:-$HOME/.opal}"`, `opal/tools/opal-cli/lib/mcp.sh:58` 동일 패턴 → **Python 등가: `os.environ.get("OPAL_HOME") or os.path.expanduser("~/.opal")`** (D-1 grep 근거).
- identity.md frontmatter 스키마: `owner_name:` 단일 스칼라 (`opal/core/identity-template.md:4`, D-9).

#### 2.1.3 영향 범위

- **호출자**: 모든 pilot 스킬이 `run.sh mark ... --note`로 호출. 치환은 note 문자열 내부에서만 발생하므로 호출 계약(인자/응답 스키마) 불변.
- **state.json 스키마**: 변경 없음 (note 필드 값만 치환, 신규 필드 없음).
- **관련 테스트**: `test_state_tool.py` — 기존 케이스는 플레이스홀더 미포함 note를 사용하므로 fast-path로 불변 (회귀 0). `test_state_tool.py:443`의 `note="소유자 확인"`은 플레이스홀더 없음 → 불변.

### F-002: (B) 하네스 오염 차단 규칙 명문화 + note 예시 통일

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서 | `opal/core/AGENT.md` | 소유자 호칭 규칙 SSOT (§정체성 적용) | 수정 |
| 문서 | `opal/core/references/harness/state.md` | note/사용자 확인 행 파생 규칙 | 수정 |
| 스킬 | `opal/skills/opal-pilot-write-tech/SKILL.md` | note 예시 `'소유자 확인:'` ×4 | 수정 |
| 스킬 | `opal/skills/opal-pilot-data-design/SKILL.md` | note 예시 ×5 | 수정 |
| 스킬 | `opal/skills/opal-pilot-sdd/SKILL.md` | note 예시 ×3 | 수정 |
| 스킬 | `opal/skills/opal-pilot-project-dev/SKILL.md` | note 예시 ×2 | 수정 |
| 스킬 | `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | note 예시 ×3 | 수정 |
| 스킬 | `opal/skills/opal-pilot-dev/SKILL.md` | note 예시(산문) ×3 | 수정 |
| 스킬 | `opal/skills/opal-pilot-dev-short/SKILL.md` | note 예시(산문) ×2 | 수정 |
| 스킬 | `opal/skills/opal-pilot-project/SKILL.md` | note 예시(산문) ×1 | 수정 |

#### 2.2.2 현재 구현 (코드 분석 결과)

- **이미 준수(변경 불요)**: `opal-harness-agentic.md:105`, `opal-harness-semi-agentic.md:71`, `tools.md:175` 는 note 예시가 이미 `{owner_name} 확인:` 플레이스홀더 (task 139에서 치환 완료). → **B 대상에서 제외** (변경 없으면 R-5 변경이력 불요).
- **미준수(변경 필요)**: 8개 pilot SKILL.md가 note 예시에 generic `'소유자 확인:'` 하드코딩. "소유자"는 특정 이름은 아니나(오염은 아님) 플레이스홀더가 아니어서 A 치환이 걸리지 않아 개인화되지 않는다 (D-6~D-8 대조).
- **SSOT 공백**: `opal/core/AGENT.md:93` "소유자를 `{owner_name}`으로 부른다"는 **대화 호칭** 지침일 뿐, 영속 산출물 호칭을 identity로 못박고 레포 컨텍스트 계승을 금지하는 규칙이 없다 (TASK 배경 분석 §원인 규명).

#### 2.2.3 영향 범위

- AGENT.md §정체성 적용은 Phase A(모든 세션 즉시 로드)에서 활성 → DONE.md 등 자유서술 산출물 작성 시점에 규칙 in-context 보장.
- harness/state.md는 opal-harness.md §3이 참조하는 상세 문서 → note-write 시점(TASK/EXECUTE/Gate) 로드 경로에 위치.
- skill 예시 변경은 순수 문자열 치환, 로직 무영향.

---

## 3. 기능별 설계

### F-001: (A) state-tool identity 치환 + 하위호환/폴백

#### 3.1.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/state-tool/state_tool.py` | 도구 | `resolve_owner_placeholder(text)` 헬퍼 신설 + note-write 6경로에 적용 | (→ D-1:872-988) |
| 2 | `opal/tools/state-tool/tests/test_state_tool.py` | 도구 | `TestOwnerNamePlaceholder` 클래스 신설 (RED-first) | (→ D-2:126) |
| 3 | `opal/tools/state-tool/README.md` | 문서 | identity 치환 계약 + 폴백 + 변경이력 | (→ D-3) |

#### 3.1.2 함수·데이터 설계

**확정 메커니즘: `{owner_name}` 플레이스홀더 write-time 치환 (근거 있는 확정안)**

새 헬퍼를 파일 I/O 헬퍼 섹션(`state_tool.py:163` 이후) 부근에 신설한다:

```
[MUST] 함수 시그니처: def resolve_owner_placeholder(text: str) -> str
```

동작 명세 (5단계, fail-safe):

1. **fast-path (회귀 0 보장)**: `if not text or "{owner_name}" not in text: return text` — 플레이스홀더 미포함 시 파일 I/O 없이 원문 즉시 반환. → H-2 하위호환 계약 충족.
2. **경로 해석 (플랫폼 독립)**: `opal_home = os.environ.get("OPAL_HOME") or os.path.expanduser("~/.opal")`; `identity_path = pathlib.Path(opal_home) / "identity.md"`. → H-4 (선례: `doctor/lib/checks.sh:25`).
3. **폴백 A (파일 부재)**: `if not identity_path.exists(): return text` — 플레이스홀더 원문 유지. → H-3.
4. **frontmatter 파싱 (정규식, T-11 stdlib-only)**:
   - 파일 읽기 후 선행 `---` ~ `---` frontmatter 블록 추출 (정규식 `^---\s*$ ... ^---\s*$`, `re.M/re.S`). 블록이 없으면 파일 전체를 대상으로 완화 매칭(fail-safe).
   - `re.search(r"^owner_name:\s*(.*)$", block, re.M)` → group(1) `.strip()` 후 좌우 따옴표(`"`/`'`) 제거.
5. **폴백 B (공란/미발견/예외)**: `owner_name`이 없거나 빈 문자열이거나 읽기·파싱 예외 발생 시 `return text` (원문 유지). 정상 값이면 `return text.replace("{owner_name}", owner_name)`. → H-3.

> 예외 처리: 4단계 파일 읽기·정규식 전체를 `try/except Exception: return text`로 감싸 어떤 실패도 원문 유지(fail-safe). 도구가 note 저장 자체를 실패시키지 않는다.

**note-write 6경로 적용** (단일 규칙 = "모든 사용자 free text note는 저장 직전 치환"):

| 경로 | 현행 (D-1) | 변경 |
|------|-----------|------|
| `cmd_advance` | `row["note"] = args.note` (872-873) | `row["note"] = resolve_owner_placeholder(args.note)` |
| `cmd_mark` | 977-988 3분기 | 진입부에서 `note_text = resolve_owner_placeholder(args.note)` 1회 산출 → 3분기가 `note_text` 사용 (auto-pass는 `f"agentic auto-pass: {note_text}"`) |
| `cmd_add_row` | `args.note or None` (1160) | `resolve_owner_placeholder(args.note) or None` |
| `cmd_block` | `f"block: {args.reason}"` (1061) | `f"block: {resolve_owner_placeholder(args.reason)}"` |
| `cmd_status` | `reason = args.note` (1228) | `reason = resolve_owner_placeholder(args.note) or "(none)"` |
| `cmd_init` | `append_decision_log(..., args.note)` (738) | `append_decision_log(..., resolve_owner_placeholder(args.note))` |

> **트레이드오프 (확정 근거)**: 대안 비교 — ① 구조 필드화(state.json에 owner_display 신설): 스키마 변경·하위호환 파손·surface 증가로 기각(TASK "state.json 스키마 영향 최소화 우선"). ② 검증형(하드코딩 이름 note 거부): 이름 열거 불가·개인화 미달·LLM이 여전히 오염 텍스트 작성으로 기각. ③ **플레이스홀더 치환(채택)**: 스키마 무변경 + fast-path 회귀 0 + 결정론적 개인화 + LLM이 이름을 직접 못 씀(오염 원천 차단). R-1 AC와 정합.
> R-1 AC 최소 적용 범위는 `cmd_mark`+`cmd_advance`이나, 단일 규칙 일관성(왜 mark만 치환되고 add-row는 안 되는가 방지)과 fast-path 회귀 0 보장으로 6경로 전체 적용을 권고한다.

#### 3.1.3 환경 변경

해당 없음 (표준 라이브러리만 사용, PyYAML 등 신규 패키지 도입 금지 — T-11).

#### 3.1.4 배치/마이그레이션

해당 없음. 기존 state.json 소급 정정 안 함 (→ D-10 citation-rules §5 레거시 호환).

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-1 | R-1 | L1 단위(RED) | 미구현 상태에서 `--note "{owner_name} 확인: X"` → note가 "{owner_name} 확인: X" 그대로 저장 → 테스트 FAIL(RED 증거) |
| TS-2 | R-1 | L1 단위(GREEN) | OPAL_HOME=temp(owner_name=루카스), `mark --note "{owner_name} 확인: X"` → state.json note == "루카스 확인: X" |
| TS-3 | R-2 | L1 회귀 | 플레이스홀더 없는 note("검토 완료") → 저장값 byte-identical 불변 |
| TS-4 | R-2 | L1 폴백 | OPAL_HOME=temp에 identity.md 부재 → note "{owner_name} 확인" 원문 유지, 에러 없음(exit 0) |
| TS-5 | R-2 | L1 폴백 | identity.md 존재하나 owner_name 공란 → 원문 유지 |
| TS-6 | R-2 | L1 폴백 | frontmatter 없음/파싱 실패 → 원문 유지 |
| TS-7 | R-1 | L1 단위 | `advance --note "{owner_name} 확인"` → 치환 적용 (mark 외 경로 검증) |

### F-002: (B) 하네스 오염 차단 규칙 명문화 + note 예시 통일

#### 3.2.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 4 | `opal/core/AGENT.md` | 문서 | §정체성 적용에 "영속 산출물 호칭 = identity 재해석 + 오염 금지" 규칙 신설 (SSOT) | (→ D-4:88-96) |
| 5 | `opal/core/references/harness/state.md` | 문서 | note 소유자 호칭 규칙(도구 자동 치환 + AGENT.md 참조) 추가 | (→ D-5:31) |
| 6~13 | 8개 pilot SKILL.md | 스킬 | note 예시 `'소유자 확인:'` → `'{owner_name} 확인:'` 치환 | (→ D-6 대조) |

#### 3.2.2 규칙 설계 (SSOT 위치 확정)

**SSOT = `opal/core/AGENT.md` §정체성 적용** (헌법 "lower docs reference, don't restate" 준수):

- 근거: 해당 섹션이 이미 "소유자 호칭"(`{owner_name}`) 의미를 소유하고 Phase A(모든 세션)에서 로드된다 (→ D-4:88-96). 영속 산출물 호칭 규칙을 여기 한 곳에 두면 자유서술 산출물(DONE.md) 작성 시점에 in-context 보장.
- 신설 문장 (기존 "소유자 호칭: 소유자를 `{owner_name}`으로 부른다" 하위에 구분 추가):
  - "**영속 산출물 호칭**: note·DONE.md 등 영속 산출물의 소유자 호칭은 **매 작성 시점** `~/.opal/identity.md`의 `owner_name`에서 재해석한다. 로드된 레포 컨텍스트(MEMORY 브리핑·brain·직전 태스크 산출물)의 지배 호칭을 계승하지 않는다(오염 금지). 도구가 닿는 경로(state.json note)는 state-tool이 `{owner_name}` 플레이스홀더를 자동 치환한다."

**파생 참조 = `harness/state.md`** (재서술 금지, 참조만):

- note-write 규칙 근처(사용자 확인 행 테이블 `state.md:31` 부근)에 1줄 추가: "note에 소유자 호칭이 필요하면 `{owner_name}` 플레이스홀더를 사용한다 — state-tool이 identity.md `owner_name`으로 치환한다. 규칙 상세: `opal/core/AGENT.md` §정체성 적용(오염 금지)."

**note 예시 통일**: 8개 SKILL.md의 `--note '소유자 확인: ...'` / `--note '소유자 확인'` → `--note '{owner_name} 확인: ...'`로 일괄 치환 (산문 예시 포함).

> **B 대상 제외 명시**: `opal-harness-agentic.md`/`opal-harness-semi-agentic.md`/`tools.md`는 이미 `{owner_name}` 사용(task 139) → 변경 없음 → R-5 변경이력 불요. Surgical 원칙(인접 코드 개선 금지) 준수.

#### 3.2.3 환경 변경 / 3.2.4 배치·마이그레이션

해당 없음.

#### 3.2.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-8 | R-4 | 정적 grep | `grep -rn "'소유자 확인:" opal/skills/` 결과 0건 (모두 `{owner_name}`으로 치환) |
| TS-9 | R-3 | 정적 존재 | AGENT.md §정체성 적용에 "identity.md owner_name 재해석 + 오염 금지" 문장 존재; state.md에 참조 1줄 존재 |
| TS-10 | R-5 | git diff | 변경된 각 문서·README에 054 변경이력 행 존재 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | 실행 | 비고 |
|-------|------|------|------|------|
| P1 | F-001 | Step 1(RED)→2(구현)→3(GREEN)→4(README) | 순차 | RED-first 트랙 (self-confirming 위험) |
| P2 | F-002 | Step 5(SSOT)→6(예시 통일)→7(변경이력) | 순차 | P1과 병렬 가능하나 동일 agent로 순차 처리 무방 |

### 4.2 실행 체크리스트

> 총 7개 Step | Phase 2개 | 실행 모드: 복잡 (변경 파일 13개 > 10 — §6 판정)

#### Step 1: RED 테스트 작성 (identity 치환 미구현 상태 실패 증거 확보)
- [x] 완료
- **소속 기능**: F-001
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/state-tool/tests/test_state_tool.py`
- **작업 내용**: `TestOwnerNamePlaceholder(BaseTestCase)` 신설. TS-2(핵심 GREEN 목표)를 RED로 먼저 작성 — `patch.dict(os.environ, {"OPAL_HOME": <temp>})` + temp에 `identity.md`(owner_name=루카스) 생성 후 `_mark(row, note="{owner_name} 확인: X", owner="user")` → `state.json` note == "루카스 확인: X" assert. 구현 전이므로 FAIL(RED 증거).
- **완료 기준**: 테스트 실행 시 해당 케이스가 AssertionError로 실패, 실패 출력(RED 증거) 캡처.
- **테스트**: TS-1
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: `resolve_owner_placeholder()` 구현 + note-write 6경로 적용
- [x] 완료
- **소속 기능**: F-001
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/state-tool/state_tool.py`
- **작업 내용**: §3.1.2 명세대로 `resolve_owner_placeholder(text)` 헬퍼 신설(fast-path + OPAL_HOME 해석 + 정규식 frontmatter 파싱 + 5단계 폴백, try/except 전면 감싸기) 후 `cmd_advance`/`cmd_mark`/`cmd_add_row`/`cmd_block`/`cmd_status`/`cmd_init` note-write 지점에 적용.
- **완료 기준**: Step 1 RED 테스트가 GREEN 전환. 표준 라이브러리만 사용(T-11). 하드코딩 `~/.opal` 분기 없음.
- **테스트**: TS-2, TS-7
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 3: GREEN + 하위호환/폴백 회귀 테스트 완성
- [x] 완료
- **소속 기능**: F-001
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/state-tool/tests/test_state_tool.py`
- **작업 내용**: TS-3(회귀)·TS-4/5/6(폴백 3케이스)·TS-7(advance 경로) 추가. 전체 `python -m unittest` 통과 확인(기존 케이스 회귀 0 포함).
- **완료 기준**: 신규 케이스 전부 PASS + 기존 테스트 스위트 회귀 0.
- **테스트**: TS-3~TS-7
- **실행 방법**: sub-agent
- **의존**: Step 2

#### Step 4: README 치환 계약·폴백 문서화 + 변경이력
- [x] 완료
- **소속 기능**: F-001
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/tools/state-tool/README.md`
- **작업 내용**: `advance`/`mark`/`add-row`/`block`/`status`/`init` note 절에 "`{owner_name}` 플레이스홀더는 identity.md owner_name으로 write-time 치환, 부재/공란 시 원문 유지(fail-safe)" 계약 추가. 변경이력 행(054, KST) 추가.
- **완료 기준**: 치환·폴백 계약이 README에 명시.
- **테스트**: TS-10
- **실행 방법**: sub-agent
- **의존**: Step 2

#### Step 5: (B) 오염 차단 규칙 SSOT 명문화 (AGENT.md + state.md)
- [x] 완료
- **소속 기능**: F-002
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/core/AGENT.md`, `opal/core/references/harness/state.md`
- **작업 내용**: §3.2.2대로 AGENT.md §정체성 적용에 "영속 산출물 호칭 = identity 재해석 + 오염 금지" 규칙 신설(SSOT), state.md에 참조 1줄 추가(재서술 금지). 각 파일 변경이력 행(054) 추가(state.md는 변경이력 표 존재, AGENT.md는 변경이력 관행 확인 후 준용).
- **완료 기준**: 규칙 문장 존재(TS-9), 중복 없이 state.md가 AGENT.md 참조.
- **테스트**: TS-9, TS-10
- **실행 방법**: sub-agent
- **의존**: 없음 (F-001과 병렬 가능)

#### Step 6: (B) 8개 pilot SKILL.md note 예시 `{owner_name}` 통일
- [x] 완료
- **소속 기능**: F-002
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal-pilot-write-tech`, `opal-pilot-data-design`, `opal-pilot-sdd`, `opal-pilot-project-dev`, `opal-pilot-dev-wireframe`, `opal-pilot-dev`, `opal-pilot-dev-short`, `opal-pilot-project` 의 각 SKILL.md
- **작업 내용**: `--note '소유자 확인: ...'` / `--note '소유자 확인'` → `--note '{owner_name} 확인: ...'` 일괄 치환(코드블록+산문 예시). auto-pass 근거 note(`'<근거>'`, `'A{NN} 완료'`, `'그룹 완료'` 등 소유자 호칭 무관 예시)는 대상 아님(surgical).
- **완료 기준**: `grep -rn "소유자 확인:" opal/skills/` 결과 0건(TS-8).
- **테스트**: TS-8
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 7: (B) 변경이력 행 일괄 확인 (변경된 스킬 문서)
- [x] 완료
- **소속 기능**: F-002
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: Step 6에서 변경된 8개 SKILL.md
- **작업 내용**: 각 SKILL.md 변경이력 표(존재 시)에 054 행 추가. 변경이력 표가 없는 SKILL.md는 관행 확인 후 스킵(신설 강제 안 함 — surgical).
- **완료 기준**: 변경된 각 문서에 054 변경이력 행 존재(변경이력 표 보유 문서 한정, TS-10).
- **테스트**: TS-10
- **실행 방법**: sub-agent
- **의존**: Step 6

> docs/ 갱신 Step 없음 — 프로젝트 `docs/`(PROJECT/ARCHITECTURE/CONVENTIONS)는 프레임워크 상위 문서이며 본 변경(도구 내부 로직 + 하네스 참조 문서)은 `docs/` 서술 대상 아님. 하네스 SSOT 자체(opal/core)가 갱신 대상이며 Step 5에 포함됨.

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1→2→3 순차 | RED-first: RED 증거(1) → 구현(2) → GREEN·회귀(3). self-confirming 방지(H-1). |
| Step 4 ← Step 2 | README는 구현 계약 확정 후 문서화. |
| Step 5·6 ∥ Step 1~4 | F-002 문서 변경은 F-001과 무의존 — 병렬 가능. 동일 agent(opal-task-agent) 순차 처리도 무방. |
| Step 7 ← Step 6 | 변경이력은 실제 변경 후 기재. |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | 플레이스홀더 치환 동작 | TS-2, TS-7 | OPAL_HOME identity.md owner_name으로 치환 저장 |
| F-001 | 하위호환 회귀 0 | TS-3 | 플레이스홀더 없는 note byte-identical |
| F-001 | 폴백 fail-safe | TS-4, TS-5, TS-6 | 부재/공란/파싱실패 시 원문 유지 + exit 0 |
| F-001 | RED 증거 확보 | TS-1 | 구현 전 FAIL 출력 캡처 |
| F-002 | note 예시 통일 | TS-8 | `소유자 확인:` grep 0건 |
| F-002 | SSOT 규칙 존재 | TS-9 | AGENT.md 규칙 문장 + state.md 참조 |
| F-002 | 변경이력 | TS-10 | 변경 문서에 054 행 |

### 5.2 회귀 테스트
- [ ] `python -m unittest` 전체 스위트 통과 (기존 케이스 회귀 0)
- [ ] 플레이스홀더 미포함 기존 note 저장 동작 불변 (`test_state_tool.py:443` 포함)

### 5.3 코드/문서 품질
- [ ] 표준 라이브러리만 사용 (T-11, PyYAML 미도입)
- [ ] `OPAL_HOME` 기준 경로 해석, 하드코딩 `~/.opal` 분기 없음 (플랫폼 독립)
- [ ] 변경 대상 전부 `opal/` 소스 (`~/.opal` 직접 편집 없음)
- [ ] 헌법 §2·§3 Simplicity/Surgical — 단일 목적(호칭 오염 차단) 한정, 인접 코드 미개선

### 5.4 보안
- [ ] identity.md 읽기 실패가 note 저장 자체를 실패시키지 않음 (fail-safe, DoS 회피)
- [ ] 치환은 note 문자열 내부에 한정 — 임의 경로 읽기/주입 없음 (경로는 OPAL_HOME 고정 해석)
- [ ] 개인 식별자(owner_name)는 소유자 로컬 파일에서만 취득 — 레포 커밋 산출물에 실명 하드코딩 확산 방지

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 7개 | 단순 |
| 변경 파일 수 | 13개 | **복잡** (>10) |
| 모듈 범위 | 다중 (state-tool + core/AGENT + harness + 8 skills) | **복잡** |
| 작업 유형 | 로직 변경(치환) + 문서 규칙 | 복잡 |
| 외부 의존성 | 없음 (표준 라이브러리) | 단순 |
| **실행 모드** | **복잡** | 변경 파일 13개(>10) + 다중 모듈 |

> **[에스컬레이션 판단 근거 — decision_required]** 변경 파일 13개로 Short Task 휴리스틱(10개)을 초과한다. 다만 (a) 복잡도는 F-001(state_tool.py 1파일)에 집중되고 나머지 12개는 저위험 문자열 치환·규칙 명문화, (b) 전 Step 동일 agent(opal-task-agent)·단일 목적, (c) RED-first로 self-confirming 차단됨 → **Short Task 유지하여 진행 가능**하다고 판단하되, 캡틴이 Full Task 승격을 원하면 P1(F-001)/P2(F-002) 2배치로 분리 실행한다.

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

```
[PM] ─ P1(F-001, RED-first 순차) → opal-task-agent: Step1(RED)→Step2(impl)→Step3(GREEN)→Step4(README)
     └ P2(F-002, 문서, 병렬 가능) → opal-task-agent: Step5(SSOT)→Step6(예시)→Step7(변경이력)
```

배치 실행 순서: P1과 P2는 무의존이나, 단일 워커 타입(opal-task-agent)이므로 PM 판단으로 P1→P2 순차 또는 2워커 병렬 디스패치. TEST-SCENARIO/TEST(L1)는 오케스트레이터 책임.

### C-2. 스킬 요구사항

기존 스킬로 충족 (op-dev-execute EXECUTE Step 실행). 신규 스킬 갭 없음.

### C-3. 도구 요구사항

- `state-tool` 자체 (변경 대상), Python 표준 라이브러리(re/os/pathlib) — 신규 패키지 없음.
- 테스트 실행: `cd opal/tools/state-tool && python -m unittest tests.test_state_tool` (또는 `python -m unittest discover -s tests`). RED 증거는 개별 케이스 지정 실행.

### C-4. 테스트 전략

L1(단위) 중심 — TS-1~TS-7은 `test_state_tool.py` 단위, TS-8~TS-10은 정적 grep/존재/diff 검증. RED-first 트랙 필수(H-1 self-confirming). L2/L3 불요(외부 시스템·동시성 무관).

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 도구 로직 | Python 3 (표준 라이브러리 only, T-11) | — |
| 테스트 | unittest (stdlib) | — |
| 문서 | Markdown/YAML frontmatter | — |

### 8.2 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|
| — | 미사용 (stdlib·로컬 파일만, 외부 라이브러리 API 조회 불요) |

### 8.3 참조 문서 (설계 결정 근거)

§1.2 참조 문서 테이블(D-1~D-10) 참조. 핵심 근거:
- A 주입 지점: `state_tool.py:872-988` (note-write 6경로) — D-1
- OPAL_HOME 선례: `doctor/lib/checks.sh:25` `${OPAL_HOME:-$HOME/.opal}` — D-1 grep
- 테스트 하네스: `test_state_tool.py:126-232` (BaseTestCase/_mark/_advance) — D-2
- owner_name 스키마: `identity-template.md:4` — D-9
- SSOT 위치: `AGENT.md:88-96` §정체성 적용 — D-4

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R1 | 치환 로직이 기존 note 저장 회귀 유발 | F-001 | P0 | fast-path(플레이스홀더 미포함 즉시 반환) + TS-3 회귀 테스트 |
| R2 | identity.md I/O 실패가 note 저장 실패로 전파 | F-001 | P1 | try/except 전면 감싸기 → 원문 유지 fail-safe + TS-4~6 |
| R3 | 자체확인(self-confirming) 테스트로 치환 미검증 | F-001 | P0 | RED-first: Step 1 RED 증거 선확보 → Step 2 GREEN |
| R4 | 하드코딩 `~/.opal` 분기로 플랫폼 종속 | F-001 | P1 | OPAL_HOME env 우선 해석(선례 준수) + 테스트 env 주입 |
| R5 | note 예시 일부 누락으로 grep 잔존 | F-002 | P1 | TS-8 grep 0건 게이트로 완결성 검증 |
| R6 | 변경 파일 13개 — Short Task 초과 | 공통 | P2 | §6 에스컬레이션 판단 근거 제시(decision_required), 저위험 확인 후 진행 |
