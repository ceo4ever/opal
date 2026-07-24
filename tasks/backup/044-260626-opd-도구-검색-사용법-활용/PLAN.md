# PLAN: 도구·MCP·스킬 통합 검색·사용법·활용 체계 (tool-scan)

> 작성일: 2026-06-26 | 입력: TASK.md, ANALYSIS.md
> 모드: Multi-Feature
> 입력 분기: ANALYSIS.md **있음** → F-NNN별 분석은 ANALYSIS 참조하여 간략, 설계/구현 계획에 집중

---

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

PM이 작업 중 필요한 capability(OPAL/외부 CLI 도구·MCP·스킬)를 ①상황 기반 **검색** → ②권위 출처(live)에서 **정확한 사용법 확인** → ③**정확히 사용**하도록 하는 결정론적 discovery/usage 도구 `tool-scan`(신규)과 thin `manifest.json`(SSOT)을 구축한다. 동시에 기존 인지 맵(`AGENT.md`)·도구 레지스트리(`tools.md`·`harness §9`)의 분산·drift·오라우팅을 정비하고, 신규 도구를 install 배포 경로에 등록한다. 사용법 텍스트는 매니페스트에 **저장하지 않고**(포인터만) `usage`가 live `--help`를 셸 실행해 반환한다. 도구 자체 로직이라 self-confirming 위험이 있어 **RED-first(작성자≠구현자)**를 강제 적용한다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | tool-scan 도구 골격 (run.sh + tool_scan.py + ERROR_CODES + JSON 응답 헬퍼) | R-1 | P0 | 없음 |
| F-002 | thin manifest.json (SSOT) — 6종 OPAL 도구 + tool-scan 자기 엔트리, usage_source 포인터 | R-3 | P0 | 없음 |
| F-003 | `usage <tool> [subcmd]` — live `--help` 셸 실행 추출 (OPAL 래퍼=exit0 판정 / 외부 CLI=stdout+stderr 원문) | R-2 | P0 | F-001, F-002 |
| F-004 | `list` / `which <상황>` / `resolve <상황>` / `check <tool>` 서브명령 + federation(mcps.md·skills-registry.json 읽기) + 라우팅 알고리즘 | R-1, R-4, R-5 | P0 | F-001, F-002 |
| F-005 | 인지 맵 정비 — AGENT.md cmux-tool 행 추가 + localhost 오라우팅 수정 + 도구 사용 규율(사용법 선확인·에러 진단후 폴백) | R-6, R-7 | P0 | 없음 (병렬) |
| F-006 | 레지스트리 drift 정합 — tools.md(brain-tool·tool-scan 섹션 추가) + harness §9(code-scan·cmux-tool·tool-scan 행 추가) | R-8 | P1 | F-002 (도구명 확정 후) |
| F-007 | install 배포 등록 — install-mac.sh에 tool-scan chmod 블록 + (선택) test-tool chmod 누락 보정 | R-9 | P1 | F-001 |

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 (골격) ──┬─ F-003 (usage live --help)
F-002 (manifest)┤
               ├─ F-004 (list/which/resolve/check + federation)
               └─ F-006 (drift 정합)   ┐
F-001 ───────────── F-007 (install)    ├─ 문서/환경 트랙 (코드와 병렬)
F-005 (인지맵 정비) ───────────────────┘  ← 완전 독립, 병렬

RED-first 게이트: TEST(작성자) → F-001/F-003/F-004 구현(구현자) 순서 강제
```

---

## 리스크 가설 표

> PLAN 단계 작성. TEST-SCENARIO.md §1의 입력. ANALYSIS §5 리스크 5종 + 신규 가설.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-005 federation 읽기(skills-registry.json) | `groups` 구조·`name`/`alias`/`triggers`/`paths` 필드를 skill-registry.js가 파싱 중 → 구조/필드명 변경 시 install·harness 파괴 | P0 | L1(원본 무변경 단언) + 회귀(skill-registry.js list 정상) | S-불파괴 |
| H-2 | F-001/F-003/F-004 (tool-scan 자체 로직) | self-confirming — 구현자가 테스트도 쓰면 "통과하도록" 맞춤 → 오라우팅·오판정 미검출 | P0 | RED-first 작성자≠구현자 분리 (L1 단위) | S-RED |
| H-3 | F-004 MCP discovery | `mcp-schema` live 경로 부재 → `usage_source: mcp-schema`로 파라미터 스키마 반환 시도 시 빈 결과/오류 | P1 | L1(MCP는 mcps.md 파싱 도구명/설명만 + ToolSearch 포인터 반환 단언) | S-mcp-pointer |
| H-4 | F-003 `usage`(OPAL 래퍼) | cmux-tool `--help` = `ok:false` + **exit 0** → 파서가 `ok` 기준 판정 시 성공을 실패로 오판 | P0 | L1(exit code 기준 판정 단언, ok:false+exit0 케이스 stub) | S-exit0-trap |
| H-5 | F-006 tools.md brain-tool 섹션 신설 | harness §9엔 brain 1행 있으나 tools.md 섹션 부재 → 신설 분량·정합 누락 | P1 | L1(두 표 도구 집합 동일성 검사) | S-drift-parity |
| H-6 | F-007 install chmod | test-tool chmod 블록이 install-mac.sh에 누락(state/brain/cmux는 있음) → run.sh 실행 권한 미설정 가능성 | P2 | L1(install 스크립트 tool-scan·test-tool chmod 라인 존재 grep) | S-install-line |
| H-7 | F-003 `usage`(외부 CLI) | 외부 CLI `--help`가 stderr로만 출력하는 경우(stdout 비어있음) → stdout만 캡처 시 빈 usage | P1 | L1(stub CLI가 stderr로 help 출력 → 병합 캡처 단언) | S-stderr-merge |
| H-8 | F-003 `usage` 정적 캐시 금지 계약 | 정적 파일 복제 시 도구 `--help` 변경이 미반영(R-2 위반) | P1 | L1(stub `--help` 출력 변경 → usage 반환 변화 단언) | S-live-no-cache |
| H-9 | F-002 manifest usage 텍스트 미저장 계약 | 누군가 편의로 usage 본문을 manifest에 inline 저장 → drift 표면 부활(R-3 위반) | P1 | L1(manifest grep 시 `--help` 본문 부재, `usage_source` 포인터만 존재) | S-no-usage-text |
| H-10 | F-004 `resolve` 결정론 | 동일 상황 키워드 입력에 비결정적/순서불안정 후보 반환 → PM 라우팅 신뢰성 저하 | P1 | L1(동일 입력 → 동일 정렬 후보 반복 단언) | S-deterministic |

**가설 도출 근거 인용**: H-1(`opal/tools/skill-registry/skill-registry.js:64-87`, ANALYSIS §1.3) / H-2(TASK §제약 RED-first, ANALYSIS §5) / H-3·H-4(ANALYSIS §2.1·§5) / H-5(ANALYSIS 부록 C) / H-6(ANALYSIS §5 test-tool chmod) / H-7·H-8(R-2 AC).

---

## 2. 기능별 분석

### F-001: tool-scan 도구 골격

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 환경 | `opal/tools/state-tool/run.sh` | Bash 래퍼 12줄 패턴 (detail 없는 venv 에러) | 참조 |
| 환경 | `opal/tools/test-tool/run.sh` | Bash 래퍼 12줄 패턴 (detail 있는 venv 에러) | 참조 |
| 도구 | `opal/tools/test-tool/test_tool.py` | @header + ERROR_CODES dict + `_respond`/`_error` + argparse subparsers | 참조 (구조 답습) |
| 도구 | `opal/tools/tool-scan/run.sh` | 신규 Bash 래퍼 | 신규 |
| 도구 | `opal/tools/tool-scan/tool_scan.py` | 신규 Python 진입점 | 신규 |

#### 2.1.2 현재 구현

ANALYSIS §1.2 참조. state-tool/test-tool 양 도구가 동일한 12줄 Bash 래퍼(`VENV_PYTHON` 고정 경로 → `exec python {tool}_tool.py "$@"`)를 사용. Python 진입점은 상단 `@header {...}` docstring → `ERROR_CODES: Dict[str,str]` SSOT → `_respond(data, exit_code)`/`_error(error_key, detail, command)` 헬퍼 → argparse subparsers 라우터(`test_tool.py:1-253`). 표준 라이브러리만 사용(json/argparse/pathlib/sys).

#### 2.1.3 영향 범위

- 피호출자: 없음(신규). 호출자: PM 프롬프트(셸 실행)·install-mac.sh(배포 chmod).
- 공유 상태: `~/.opal/.venv` 공유 — 외부 패키지 미설치(표준 라이브러리만, state-tool T-11 원칙).

---

### F-002: thin manifest.json (SSOT)

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/tool-scan/manifest.json` | thin SSOT — 도구 엔트리 + ERROR_CODES 참조 | 신규 |
| 소스 | `opal/core/references/tools.md` | 실제 OPAL 도구 6종 사용법 권위 출처(`--help` 포인터 대상) | 참조 |
| 소스 | `opal/tools/cmux-tool/run.sh:54-85` | `_show_help()` JSON 구조 (usage live 대상) | 참조 |

#### 2.2.2 현재 구현

매니페스트는 신규. 기존엔 도구 인벤토리가 tools.md(산문)·harness §9(표)·AGENT.md(인지맵) 3곳에 손-관리되어 drift. 실제 OPAL 도구 집합 = {xlsx, state, code-scan, cmux, test, brain}(ANALYSIS 부록 C). 매니페스트는 이 6종 + tool-scan 자기 자신을 엔트리로 등록.

#### 2.2.3 영향 범위

- 피호출자: F-003 `usage`(usage_source 포인터 소비), F-004 `list`/`which`/`resolve`/`check`(엔트리 메타 소비).
- **[MUST] usage 텍스트 저장 금지** — `usage_source` 포인터만(R-3, TASK §제약 매니페스트 규율). drift 표면 ≈ 도구 추가/제거 시에만.

---

### F-003: usage live --help 추출

#### 2.3.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/tool-scan/tool_scan.py` (cmd_usage) | usage 서브명령 핸들러 | 신규 |
| 소스 | `opal/tools/cmux-tool/run.sh:54-85,99` | `--help` exit 0 + `ok:false` JSON (exit0 함정) | 참조 |

#### 2.3.2 현재 구현

ANALYSIS §2.1 확인: cmux-tool `--help`는 `python json.dumps()` 구조화 JSON을 stdout 출력하고 `exit 0`(`run.sh:99`)이나 본문은 `"ok": false, "error": "usage"`. state-tool/test-tool은 argparse `--help`(표준 usage 텍스트, exit 0). 외부 CLI(예: cmux 바이너리)는 `--help` 출력 형식 비표준 + stderr 사용 가능성.

#### 2.3.3 영향 범위

- 피호출자: F-004 `resolve`가 `usage`를 1콜 결합 시 내부 호출.
- **[MUST] exit code(==0)로 성공 판정** — `ok` 필드 기준 판정 금지(H-4, ANALYSIS §2.1·§5). **[MUST] 정적 캐시 금지**(R-2, live).

---

### F-004: list/which/resolve/check + federation + 라우팅

#### 2.4.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/tool-scan/tool_scan.py` (cmd_list/which/resolve/check) | 서브명령 핸들러 | 신규 |
| 도구 | `opal/tools/tool-scan/lib/federation.py` (선택 분리) | mcps.md·skills-registry.json 읽기 파서 | 신규 |
| 소스 | `opal/core/references/mcps.md` | MCP federation 입력 (`## {server}` → 제공 도구) | 읽기 |
| 소스 | `opal/core/references/opal-skills-registry.json` | skill federation 입력 (`groups`→`triggers`/`stage`/`dispatched_by`) | 읽기 (불파괴) |
| 소스 | `opal/tools/skill-registry/skill-registry.js:64-87` | 불파괴 제약 실제 범위(파싱 필드) | 참조 |

#### 2.4.2 현재 구현

ANALYSIS §2.2·§2.3 확인:
- **mcps.md**: `## {server-name}` 섹션 + `제공 도구:` 목록(`- \`tool\`: 설명`). 4 MCP = shadcn/sequential-thinking/context7/playwright. `mcp-schema` live 경로 부재 → 도구명/설명만 파싱 가능(H-3).
- **skills-registry.json**: `groups` 딕트. pilot 그룹(`dispatched_by` 없음 + alias=`//`진입), op 스테이지 그룹(`stage`+`dispatched_by` 보유). `op-data-model`: triggers `["^op-data-model$"]`, stage `MODEL`, dispatched_by `["opal-pilot-data-design"]`(`opal-skills-registry.json:365-379`).
- **불파괴 범위(H-1)**: `$schema`/`groups`/엔트리 `name`/`alias`/`description`/`triggers`/`paths`가 skill-registry.js에서 직접 참조(`skill-registry.js:64-87`). 읽기만 허용.

#### 2.4.3 영향 범위

- 피호출자: PM 프롬프트(상황→capability 조회).
- **[MUST] skills-registry.json 원본 무변경**(R-5, H-1). **[MUST] 결정론적 정렬**(H-10).

---

### F-005: 인지 맵 정비 (AGENT.md)

#### 2.5.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 에이전트 | `opal/core/AGENT.md:244-257` | 도구 인지 맵 표 + 사용 규율 | 수정 |
| 소스 | `scripts/install-mac.sh:978` | `strip_deploy_md`로 `~/.opal/AGENT.md` 배포 | 참조 (간접 영향) |

#### 2.5.2 현재 구현

ANALYSIS 부록 B 확인: `AGENT.md:254` 현재 `| SPA·동적 렌더·localhost 페이지 접근 | playwright MCP | 읽기(선제) | references/mcps.md |` — **cmux-tool 부재(오라우팅)**. 인지 맵 표는 `:246-256`, "도구·MCP 적극 활용 규칙" 산문은 `:236-242`(계열별 경계: 읽기=선제 / 변경=승인). 에러계약 진단·폴백 규율 문단 부재.

#### 2.5.3 영향 범위

- 간접: `~/.opal/AGENT.md`(install 재배포 시 반영 — 캡틴). 본 작업은 `opal/core/AGENT.md` 소스만 수정(배포 경계).
- 행 추가/수정은 다른 F의 코드와 무충돌 → 완전 병렬.

---

### F-006: 레지스트리 drift 정합

#### 2.6.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 소스 | `opal/core/references/tools.md` | CLI 도구 레지스트리(섹션 산문) | 수정 |
| 소스 | `opal/core/references/opal-harness.md:238-247` | §9 "현재 등록된 도구" 표 | 수정 |

#### 2.6.2 현재 구현

ANALYSIS 부록 C drift 매트릭스:
- tools.md 섹션 = {xlsx:8, state:69, code-scan:202, cmux:292, test:416} — **brain-tool 부재**.
- harness §9 표(`:242-245`) = {xlsx, state, brain, test} — **code-scan·cmux-tool 부재**.
- drift = 정확히 3도구 × 위치 = harness에 code-scan·cmux 2행 추가, tools.md에 brain 섹션 신설. 신규 tool-scan은 양쪽 추가.

#### 2.6.3 영향 범위

- 간접: `~/.opal/references/`(install `install_opal_references()` cp -Rf 배포 — 캡틴).
- tool-scan 정합은 F-002 도구명 확정 후. brain/code-scan/cmux 정합은 즉시 가능(병렬).

---

### F-007: install 배포 등록

#### 2.7.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 환경 | `scripts/install-mac.sh:1084` (cmux lib chmod 직후) | tool-scan chmod 블록 삽입 위치 | 수정 |
| 환경 | `scripts/install-mac.sh:1056-1084` | test-tool chmod 누락 구간(H-6) | 수정(선택) |

#### 2.7.2 현재 구현

ANALYSIS §4-5·부록 A: `install_dir()`(`:1046`)이 `opal/tools/` 전체를 `~/.opal/tools/`로 복사 → 신규 도구 파일은 자동 배포. 도구별 chmod 블록(playwright/state/brain/cmux)은 명시(`:1049-1085`). test-tool chmod는 누락(H-6). Python venv는 `install_opal_venv()`(`:1108`) 공통 처리.

#### 2.7.3 영향 범위

- **[MUST] install 재배포는 캡틴이 수행**(TASK §제약 배포 경계). 본 작업은 소스 라인 추가만.

---

## 3. 기능별 설계

### F-001: tool-scan 도구 골격

#### 3.1.1 파일 변경 계획

**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/tools/tool-scan/run.sh` | 환경 | Bash 래퍼 (venv python 호출) | (→ ANALYSIS §1.2) |
| 2 | `opal/tools/tool-scan/tool_scan.py` | 도구 | argparse 5서브명령 라우터 + ERROR_CODES + 응답 헬퍼 | `test_tool.py:1-253` |

#### 3.1.2 API·데이터 모델·설계

**run.sh** — test-tool 래퍼 답습(`test-tool/run.sh:1-13`). venv 에러 JSON은 §3.8 통일 결정(detail 포함, test-tool 방식)을 따른다:
```bash
#!/bin/bash
# tool-scan 래퍼 — OPAL .venv python 호출
# @header: shell script — 적용 대상 아님 (header-rules.md §적용 대상 확장자 참조)
VENV_PYTHON="$HOME/.opal/.venv/bin/python"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ ! -x "$VENV_PYTHON" ]]; then
  echo '{"ok":false,"error":"venv_missing","detail":"OPAL .venv not found. Run install-mac.sh first."}' >&2
  exit 1
fi
exec "$VENV_PYTHON" "$SCRIPT_DIR/tool_scan.py" "$@"
```
`[MUST] 'docs/CONVENTIONS.md' §파일/폴더`: Python 파일 snake_case → `tool_scan.py` (→ ANALYSIS §1.2).

**tool_scan.py 골격** — `test_tool.py` 구조 답습:
- 상단 `@header { "module":"tool_scan", "layer":"util", "domain":"opal-tools", "description":"...", "exports":["main","ERROR_CODES"], "depends":[...] }` (`[MUST] 'docs/CONVENTIONS.md' §@header 규칙`).
- `_respond(data: Dict, exit_code: int = 0) -> None` — `print(json.dumps(data, ensure_ascii=False))` 후 `sys.exit` (`test_tool.py:60-63`).
- `_error(error_key: str, detail: Optional[str], command: str) -> None` — `{"ok":False,"command":...,"error":...,"detail":...}` + exit 1 (`test_tool.py:66-76`).
- `_build_parser()` subparsers 5종: list / which / usage / resolve / check.
- `main()` dispatch dict 라우팅.
- 성공: `{"ok":true,"command":"<subcmd>", ...}` / 실패: `{"ok":false,"command":"<subcmd>","error":"<key>","detail":"..."}`.

**ERROR_CODES 카탈로그 (dict SSOT)** — `test_tool.py:46-54` 패턴, 임의 변형 금지:
```python
ERROR_CODES: Dict[str, str] = {
    "venv_missing":        "OPAL .venv not found — Run install-mac.sh first",
    "manifest_missing":    "manifest.json 없음 — tool-scan 설치 손상",
    "manifest_parse_failed":"manifest.json 파싱 실패 — JSON 문법 오류",
    "tool_not_found":      "매니페스트에 해당 도구 엔트리 없음",
    "usage_unavailable":   "usage_source 해석 실패 — --help 실행/파일 Read 불가",
    "help_exec_failed":    "self --help 셸 실행 실패 (run.sh 부재·실행권한 없음)",
    "no_match":            "which/resolve — 상황 키워드 매칭 후보 없음",
    "registry_read_failed":"federation 입력(mcps.md/skills-registry.json) 읽기 실패",
}
```

#### 3.1.3 환경 변경
표준 라이브러리만 사용(json/argparse/pathlib/sys/subprocess/re). 추가 패키지 없음 (→ ANALYSIS §6.1, state-tool T-11).

#### 3.1.4 배치/마이그레이션
해당 없음.

#### 3.1.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 | 기능 | `run.sh list` 등 4+서브명령이 `{"ok":true,"command":...}` JSON 반환, exit 0 |
| TS-002 | R-1 | 기능 | venv 부재 stub 시 `{"ok":false,"error":"venv_missing","detail":...}` + exit 1 (§3.8 통일) |
| TS-003 | R-1 | 산출물 | 잘못된 서브명령/인자 시 `{"ok":false,...,"error":"..."}` 구조 + 비0 exit |

---

### F-002: thin manifest.json (SSOT)

#### 3.2.1 파일 변경 계획

**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/tools/tool-scan/manifest.json` | 도구 | thin SSOT — 7 엔트리(6 OPAL + tool-scan) | (→ TASK §확정 1) |

#### 3.2.2 데이터 모델 설계 — manifest.json 스키마

**최상위 구조**:
```json
{
  "$schema": "tool-scan-manifest-v1",
  "version": "1.0.0",
  "updated_at": "2026-06-26",
  "tools": [ { /* 엔트리 */ } ]
}
```

**엔트리 스키마** (TASK §확정 1: `kind`/`purpose`/`when`/`exec`/`usage_source`/`fallback`):
| 필드 | 타입 | 의미 | 비고 |
|------|------|------|------|
| `name` | string | capability 식별자 | `tool-scan`, `cmux-tool` 등 |
| `kind` | enum | `tool` \| `mcp` \| `pilot-skill` \| `op-skill` | TASK §확정 5 — invoke 형태 결정 |
| `purpose` | string | 1줄 용도 (list 출력용, 쌈) | TASK §확정 4 (2단 토큰) |
| `when` | string[] | 상황 키워드 배열 (which/resolve 매칭) | §3.4 라우팅 입력 |
| `exec` | string | 호출 형태 — tool=run.sh 상대경로 / mcp=`ToolSearch:<keyword>` 포인터 | kind별 의미 분기 |
| `usage_source` | object | 사용법 출처 포인터 (**텍스트 미저장**) | §3.3 우선순위 |
| `fallback` | object\|null | 에러 시 폴백 계약 (cmux=폴백금지/cmux_not_installed=허용) | (→ D-8 README:146-163) |

**`usage_source` 객체** (TASK §확정 2 우선순위 ⓪→②→①→③):
```json
"usage_source": {
  "type": "self-help",          // self-help | context7 | url | inline | doc
  "exec": "run.sh --help",      // self-help: 셸 명령 (live)
  "ref": null,                  // context7: library-id / url: URL / doc: 경로
  "text": null,                 // inline 전용 (단순 도구만)
  "freshness": null             // doc 전용 — "as of YYYY-MM-DD" 표기
}
```
> **[MUST] usage 텍스트 미저장**(R-3, TASK §제약): `self-help`/`context7`/`url`/`doc` 유형은 `text:null` 필수. `inline`만 예외(단순 capability 한정).

**초기 엔트리 7종** (`usage_source.type` 지정):

| name | kind | usage_source.type | exec / ref | fallback |
|------|------|-------------------|------------|----------|
| `tool-scan` | tool | self-help | `run.sh list` (또는 `--help`) | null |
| `xlsx-tool` | tool | self-help | `run.sh --help` | null |
| `state-tool` | tool | self-help | `run.sh --help` (argparse) | null |
| `code-scan` | tool | self-help | `run.sh --help` | null |
| `cmux-tool` | tool | self-help | `run.sh --help` (exit0+ok:false — H-4) | `{"on":"cmux_not_installed","allow_fallback":true},{"on":"usage","allow_fallback":false}` (→ D-8 README:146-163) |
| `test-tool` | tool | self-help | `run.sh --help` (argparse) | null |
| `brain-tool` | tool | self-help | `run.sh --help` | null |

> MCP/스킬은 매니페스트에 **저장하지 않고** federation(읽기)으로 동적 조회한다 — TASK §확정 5(기존 mcps.md·skills-registry.json 불파괴). 매니페스트는 OPAL atomic 도구만 SSOT로 보유. (`resolve`가 federation 결과를 매니페스트 도구와 통합 — §3.4.)

#### 3.2.3 환경 변경 / 3.2.4 배치
해당 없음.

#### 3.2.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-010 | R-3 | 산출물 | manifest grep 시 도구별 `--help` 본문 텍스트 부재, `usage_source.text` = null(inline 외) (H-9) |
| TS-011 | R-3 | 산출물 | 6 OPAL 도구 + tool-scan 자기 엔트리 존재, 각 `usage_source.type` 지정 |
| TS-012 | R-3 | 기능 | `list`가 매니페스트 7 엔트리 `purpose` 1줄씩만 반환(전체 usage 미주입 — TASK §확정 4) |

---

### F-003: usage live --help 추출

#### 3.3.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/tool-scan/tool_scan.py` | 도구 | `cmd_usage` 핸들러 + `_resolve_usage(entry, subcmd)` 추가 | (→ ANALYSIS §2.1) |

#### 3.3.2 API 설계 — `usage <tool> [subcmd]`

**입력**: `usage <tool> [subcmd]` — tool=매니페스트 name, subcmd(선택)=세부 명령.

**동작 (usage_source.type 분기, 우선순위 ⓪→②→①→③)**:
1. `self-help`: **OPAL 래퍼** → `subprocess.run(["bash", <run.sh 절대경로>, "--help"], capture_output=True, text=True)`. **[MUST] exit code(returncode==0)로 성공 판정**(H-4, ANALYSIS §2.1 — cmux는 `ok:false+exit0` 함정). stdout이 JSON이면 파싱하여 `usage_json` 필드로, 아니면 `usage_text` 원문.
2. `self-help`: **외부 CLI** → `subprocess.run([...], capture_output=True)`. **[MUST] stdout+stderr 병합 원문 반환**(H-7 — 일부 CLI는 stderr로 help 출력).
3. `context7`/`url`: 셸 실행 없이 `{"type":"context7","ref":"<library-id>"}` 또는 `{"type":"url","ref":"<URL>"}` **포인터 반환**(LLM이 후속 MCP/WebFetch 호출).
4. `inline`: 매니페스트 `text` 그대로 반환.
5. `doc`: `ref` 경로 Read 결과 + `freshness` 표기 반환(최후수단).

**출력 스키마**:
```json
{
  "ok": true, "command": "usage", "tool": "cmux-tool",
  "kind": "tool", "source_type": "self-help",
  "live": true,                       // self-help/외부CLI = true (정적 캐시 아님)
  "exit_code": 0,                     // self-help 시 실제 returncode
  "usage_json": { ... },              // stdout이 JSON일 때
  "usage_text": "...",                // stdout이 텍스트일 때 (둘 중 하나)
  "fallback": { ... }                 // 매니페스트 fallback 계약 동봉
}
```
실패: `{"ok":false,"command":"usage","error":"help_exec_failed"|"usage_unavailable","detail":...}`.

> **[MUST] 정적 캐시 금지**(R-2): self-help는 매 호출 셸 실행 → 도구 `--help` 변경 자동 반영. `live:true`로 명시.

#### 3.3.3 환경 / 3.3.4 배치
해당 없음.

#### 3.3.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-020 | R-2 | 기능 | OPAL 래퍼 stub(`--help` exit0 + `{"ok":false}`) → `usage` 성공 판정(exit_code 기준), `live:true` (H-4) |
| TS-021 | R-2 | 기능 | stub `--help` 출력 변경 → `usage` 반환 변화(정적 캐시 아님 증명) (H-8) |
| TS-022 | R-2 | 기능 | 외부 CLI stub이 stderr로만 help 출력 → 병합 캡처되어 usage_text 비어있지 않음 (H-7) |
| TS-023 | R-1 | 기능 | 미등록 tool → `{"ok":false,"error":"tool_not_found"}` |

---

### F-004: list/which/resolve/check + federation + 라우팅

#### 3.4.1 파일 변경 계획

**수정/신규**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/tool-scan/tool_scan.py` | 도구 | cmd_list/which/resolve/check 핸들러 | (→ ANALYSIS §2.2·§2.3) |
| 2 | `opal/tools/tool-scan/lib/federation.py` | 도구 | mcps.md(정규식)·skills-registry.json(json) 읽기 파서 (선택 분리) | `skill-registry.js:64-87` |

#### 3.4.2 API 설계 — 4서브명령

**(a) `list`** — 입력 없음. 동작: 매니페스트 7 엔트리 + federation MCP/skill capability를 `kind`별 그룹핑, 각 1줄 `purpose`만. 출력:
```json
{"ok":true,"command":"list","capabilities":[
  {"name":"cmux-tool","kind":"tool","purpose":"브라우저 자동화·웹 크롤링·E2E"},
  {"name":"context7","kind":"mcp","purpose":"라이브러리 최신 공식 문서"},
  {"name":"op-data-model","kind":"op-skill","purpose":"데이터 모델링 3단계 ERD"}
]}
```
> **[MUST] 전체 usage 미주입**(TASK §확정 4 2단 토큰) — list는 purpose만.

**(b) `which <상황>`** — 입력: 상황 키워드 문자열. 동작: §3.4.3 라우팅으로 후보 capability 1+ 반환(usage 미포함, 가벼움). 출력:
```json
{"ok":true,"command":"which","situation":"browser check localhost",
 "matches":[{"name":"cmux-tool","kind":"tool","score":3,"matched_on":["browser","localhost"]}]}
```

**(c) `resolve <상황>`** — 입력: 상황 키워드. 동작: which 후보 중 top → **kind별 invoke 형태 + usage 결합**(TASK §확정 3 단일 호출 결합). kind별 반환:
| kind | invoke 형태 | 추가 필드 |
|------|------------|----------|
| `tool` | `{"invoke":"shell","exec":"~/.opal/tools/<name>/run.sh ..."}` | `usage`(self-help live), `fallback`, `error_contract` |
| `mcp` | `{"invoke":"ToolSearch","exec":"ToolSearch query \"select:<tool>\""}` | mcps.md 설명 포인터(스키마는 런타임 ToolSearch — H-3) |
| `pilot-skill` | `{"invoke":"alias","exec":"//<alias>"}` | pipeline 진입(파이프라인) |
| `op-skill` | `{"invoke":"dispatch","skill_path":"~/.opal/skills/<name>/SKILL.md","dispatched_by":[...]}` | 워커 디스패치(SKILL.md 주입) |

출력 예(R-4 AC):
```json
{"ok":true,"command":"resolve","situation":"데이터 모델",
 "resolved":{"name":"op-data-model","kind":"op-skill",
   "invoke":"dispatch","skill_path":"~/.opal/skills/op-data-model/SKILL.md",
   "stage":"MODEL","dispatched_by":["opal-pilot-data-design"]}}
```
> **[MUST] mcp는 ToolSearch 포인터만**(H-3, ANALYSIS §2.2): live mcp-schema 부재 → 파라미터 스키마는 런타임 ToolSearch가 반환. resolve는 discovery 포인터까지만.

**(d) `check <tool>`** — 입력: tool name. 동작: 도구 설치/실행 가능 여부 검사(run.sh 존재·실행권한·외부 CLI는 `command -v`). 출력:
```json
{"ok":true,"command":"check","tool":"cmux-tool","installed":false,
 "detail":"cmux 미설치","fallback_allowed":true}
```

#### 3.4.3 라우팅 알고리즘 (which/resolve 공통 — **결정론**)

ANALYSIS §2.2·§2.3 근거. 3소스 통합 매칭:

1. **입력 정규화**: 상황 문자열 → lowercase → 공백 토큰화 → 토큰 집합 `T`.
2. **소스별 매칭**:
   - **매니페스트 tool**: 각 엔트리 `when[]` 배열의 키워드가 `T`에 포함되면 매칭. `score += 매칭 키워드 수`.
   - **skills-registry.json skill**: 각 엔트리 `triggers[]` 정규식을 상황 문자열에 `re.search` (ReDoS 방어 — 입력 256자 제한, `skill-registry.js:97-99` 정책 답습). 매칭 시 `score += 2`(정규식은 강한 신호). `kind` = `dispatched_by` 유무로 분기(있음→`op-skill`, 없음→`pilot-skill`).
   - **mcps.md MCP**: `## {server}` 섹션 설명 + 제공 도구명을 토큰화 → `T`와 교집합 크기만큼 `score`.
3. **정렬(결정론)**: `(-score, kind 우선순위[tool<mcp<op-skill<pilot-skill], name 알파벳)` 안정 정렬. **[MUST] 동일 입력 → 동일 출력**(H-10).
4. `which`: 정렬 후보 전체(score>0). `resolve`: top-1(동점 시 정렬 규칙으로 결정).
5. 후보 없음: `{"ok":false,"error":"no_match"}`.

**federation 읽기 위치 해석**(skill-registry.js getReferencesDir 답습, `skill-registry.js:60-71`): ① cwd `opal/core/references/` → ② `~/.opal/references/` → ③ 폴백. **[MUST] 읽기만 — 원본 무변경**(R-5, H-1).

#### 3.4.4 배치
해당 없음.

#### 3.4.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-030 | R-4 | 기능 | `resolve "browser check localhost"` → cmux-tool(kind=tool, invoke=shell, fallback 동봉) |
| TS-031 | R-4 | 기능 | `resolve "library docs"` → context7(kind=mcp, invoke=ToolSearch 포인터) (H-3) |
| TS-032 | R-4 | 기능 | `resolve "데이터 모델"` → op-data-model(kind=op-skill, dispatched_by 포함) |
| TS-033 | R-5 | 산출물 | resolve 실행 전후 skills-registry.json byte 동일(원본 무변경) (H-1) |
| TS-034 | R-4 | 기능 | 동일 입력 2회 → 동일 정렬 후보(결정론) (H-10) |
| TS-035 | R-1 | 기능 | `which` 매칭 없음 → `{"ok":false,"error":"no_match"}` |

---

### F-005: 인지 맵 정비 (AGENT.md)

#### 3.5.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/AGENT.md:254` | 에이전트 | localhost 행 라우팅 수정 + cmux-tool 행 추가 | (→ ANALYSIS 부록 B) |
| 2 | `opal/core/AGENT.md:236-242` 인근 | 에이전트 | 도구 사용 규율 문단 추가(사용법 선확인·에러 진단후 폴백) | (→ R-7) |

#### 3.5.2 설계 — 인지 맵 + 규율

**R-6 인지 맵 수정**(ANALYSIS 부록 B):
- `:254` 수정: `| SPA·동적 렌더·localhost 페이지 접근 | cmux-tool 우선 / playwright MCP 폴백 | 읽기(선제) | references/tools.md |`
- 신규 행 추가: `| 브라우저 자동화·웹 크롤링·E2E (cmux 환경) | cmux-tool | 읽기(선제) | references/tools.md |`
- (선택) `tool-scan` 행 추가: `| 상황 기반 도구·MCP·스킬 검색·사용법 확인 | tool-scan resolve/usage | 읽기(선제) | references/tools.md |`

**R-7 사용 규율 문단**(인지 맵 표 직후 산문 추가):
- **변경/실행 계열 첫 호출 前 사용법 확인**: 도구의 `--help`/`tool-scan usage <tool>`로 정확한 서브명령·인자 확인 후 호출(추측 금지).
- **에러 시 종류 기반 진단 후 폴백**(맹목 폴백 금지): 에러계약 소비 — `error:"usage"`/escalation = 호출자 수정(폴백 금지), `cmux_not_installed` = 폴백 허용 (→ D-8 README:146-163).
> `[MUST] 'docs/CONVENTIONS.md' §배포 경계`: `opal/core/AGENT.md` 소스만 수정 — `~/.opal/AGENT.md` 직접 편집 금지(install 재배포는 캡틴).

#### 3.5.3 환경 / 3.5.4 배치
해당 없음 (배포는 install — 캡틴).

#### 3.5.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-040 | R-6 | 산출물 | AGENT.md 인지 맵에 cmux-tool 행 존재, localhost 행이 cmux-tool 1순위 명시 |
| TS-041 | R-7 | 산출물 | "변경/실행 계열 사용법 선확인" + "에러 종류 기반 진단후 폴백(usage=수정/cmux_not_installed=폴백)" 문단 존재 |

---

### F-006: 레지스트리 drift 정합

#### 3.6.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/tools.md` | 소스 | brain-tool 섹션 신설 + tool-scan 섹션 추가 + 변경이력 행 | (→ ANALYSIS 부록 C) |
| 2 | `opal/core/references/opal-harness.md:242-245` | 소스 | §9 표에 code-scan·cmux-tool·tool-scan 행 추가 | (→ ANALYSIS 부록 C) |

#### 3.6.2 설계 — drift 정합

**tools.md**(`:464` 변경이력 직전):
- brain-tool 섹션 신설(harness §9 기존 설명 답습 — 8서브명령 init/add-page/index/log/search/sync-header/lint/validate). cmux-tool/test-tool 섹션 포맷 답습(트리거/커맨드/출력 형식).
- tool-scan 섹션 신설(5서브명령 list/which/usage/resolve/check + 출력 형식).
- 변경이력 행 `| v1.8 | 2026-06-26 | brain-tool·tool-scan 섹션 신규 추가 + drift 정합 (044) |`.

**harness §9 표**(`:242-245`) — 행 추가:
- `| code-scan | 코드 구조·exports·의존 탐색 | 코드 위치/구조 파악 시 |`
- `| cmux-tool | 브라우저 자동화·웹 크롤링·E2E (12+1 서브명령) | 브라우저/localhost 접근 시 |`
- `| tool-scan | 도구·MCP·스킬 상황 검색·live 사용법 확인 (5서브명령) | 도구 선택/사용법 확인 시 |`

> **[MUST] 두 표 도구 집합 동일**(R-8 AC): 정합 후 {xlsx, state, code-scan, cmux, test, brain, tool-scan} 일치 (H-5).

#### 3.6.3 환경 / 3.6.4 배치
해당 없음 (배포는 install — 캡틴).

#### 3.6.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-050 | R-8 | 산출물 | tools.md 섹션 집합 == harness §9 표 도구 집합 (둘 다 7도구) (H-5) |
| TS-051 | R-8 | 산출물 | tools.md에 brain-tool 섹션, harness §9에 code-scan·cmux 행 존재 |

---

### F-007: install 배포 등록

#### 3.7.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `scripts/install-mac.sh:1084` 직후 | 환경 | tool-scan chmod 블록 추가 | (→ ANALYSIS 부록 A) |
| 2 | `scripts/install-mac.sh:1061` 직후(선택) | 환경 | test-tool chmod 누락 보정 | (→ H-6) |

#### 3.7.2 설계 — install 등록

ANALYSIS 부록 A 그대로(`:1084` cmux lib chmod 직후):
```bash
# ── tool-scan 실행 권한 (044) ──
local tool_scan_run="$opal_home/tools/tool-scan/run.sh"
if [[ -f "$tool_scan_run" ]]; then
    chmod +x "$tool_scan_run"
    success "tool-scan run.sh 실행 권한 설정"
fi
```
(선택, H-6) test-tool chmod 블록도 동일 패턴으로 보정. Python venv는 `install_opal_venv()` 공통 처리 → 별도 의존성 라인 불필요.
> **[MUST] install 재배포는 캡틴**(TASK §제약 배포 경계): 소스 라인만 추가.

#### 3.7.3 환경 / 3.7.4 배치
해당 없음.

#### 3.7.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-060 | R-9 | 산출물 | install-mac.sh에 `tool-scan/run.sh` chmod 라인 존재 (H-6) |

---

### 3.8 venv 에러 JSON 통일 결정 (ANALYSIS §4-1)

state-tool(`{"ok":false,"error":"OPAL .venv not found..."}` — detail 없음) vs test-tool(`{"ok":false,"error":"venv_missing","detail":"..."}` — detail 있음) 차이.

**결정: test-tool 방식(detail 포함 + error_key=`venv_missing`)으로 통일.**
- 근거: tool-scan ERROR_CODES 카탈로그가 `error_key` 기반(`test_tool.py:46`) → state-tool의 자유 문장 error는 ERROR_CODES 규약 위반. test-tool 방식이 `error`=키 / `detail`=설명 분리로 일관(`test_tool.py:66-76`).
- 적용: §3.1.2 run.sh + `_error` 헬퍼 모두 `venv_missing` 키 + detail. (state-tool 자체는 본 작업 범위 밖 — 변경 안 함.)

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 0 (RED) | F-001/F-003/F-004 | 1 | opal-test-agent | 단독 (게이트) | **RED-first: 테스트 선작성, 구현자와 분리** (H-2) |
| 1 | F-002 | 2 | opal-be-agent | Phase 0 후 | manifest 데이터 (구현 트랙 진입) |
| 1 | F-005 | 6 | PM 직접 | 병렬 (독립) | AGENT.md — 코드와 무충돌 |
| 1 | F-006(brain/code-scan/cmux) | 7a | PM 직접 | 병렬 (독립) | tool-scan 외 drift 즉시 가능 |
| 2 | F-001 | 3 | opal-be-agent | Step 1·2 후 | 골격 GREEN |
| 2 | F-003 | 4 | opal-be-agent | Step 3 후 (동일 파일) | usage GREEN |
| 2 | F-004 | 5 | opal-be-agent | Step 4 후 (동일 파일) | federation/routing GREEN |
| 3 | F-006(tool-scan) | 7b | PM 직접 | Step 2 후(도구명 확정) | tool-scan 섹션/행 추가 |
| 3 | F-007 | 8 | opal-task-agent | Step 3 후 | install chmod 라인 |
| 4 | 문서 | 9 | PM 직접 | 코드 변경 후 | docs/ 갱신 판단 |

### 4.2 실행 체크리스트

> 총 9개 Step | Phase 5개(0~4) | 실행 모드: **복잡**
> **RED-first 분리**(H-2, TASK §제약): Step 1(테스트 작성=opal-test-agent) ≠ Step 3/4/5(구현=opal-be-agent). 작성자와 구현자를 **다른 agent**로 강제.

#### Step 1: tool-scan RED 테스트 작성 (작성자 = 구현자 아님)
- [ ] 완료
- **소속 기능**: F-001, F-003, F-004
- **영역**: 도구
- **agent**: opal-test-agent
- **파일**: `opal/tools/tool-scan/tests/test_tool_scan.py` (신규), `opal/tools/tool-scan/tests/fixtures/` (stub manifest·stub run.sh)
- **작업 내용**: TS-001~003, TS-010~012, TS-020~023, TS-030~035 를 unittest로 작성. test-tool RED 패턴 답습(`test_test_tool.py:1-32`) — `subprocess.run(["bash", run.sh] + args)` 공개 인터페이스만 단언, MagicMock 금지. `tmpdir`에 stub manifest.json + stub `--help` 쉘 스크립트(exit0+ok:false 케이스 / stderr-only 케이스) 주입으로 파일시스템 격리. **구현 없이 RED(전부 실패) 확인**.
- **완료 기준**: 모든 테스트가 import/실행되며 구현 부재로 **FAIL**(RED). exit0+ok:false stub·stderr-only stub·skills-registry 무변경 단언 포함.
- **테스트**: 자기 자신 (테스트 코드)
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: manifest.json 작성
- [ ] 완료
- **소속 기능**: F-002
- **영역**: 도구
- **agent**: opal-be-agent
- **파일**: `opal/tools/tool-scan/manifest.json` (신규)
- **작업 내용**: §3.2.2 스키마로 7 엔트리(xlsx/state/code-scan/cmux/test/brain/tool-scan) 작성. 각 `usage_source.type=self-help`, cmux는 fallback 계약 동봉. **usage 텍스트 미저장**(text:null).
- **완료 기준**: TS-010~011 GREEN. manifest grep 시 `--help` 본문 부재.
- **테스트**: TS-010, TS-011
- **실행 방법**: sub-agent
- **의존**: Step 1 (RED 존재)

#### Step 3: tool-scan 골격 구현 (run.sh + tool_scan.py)
- [ ] 완료
- **소속 기능**: F-001
- **영역**: 도구
- **agent**: opal-be-agent
- **파일**: `opal/tools/tool-scan/run.sh`, `opal/tools/tool-scan/tool_scan.py` (신규)
- **작업 내용**: §3.1.2 — run.sh(test-tool 답습, venv_missing+detail §3.8), tool_scan.py(@header, ERROR_CODES dict, `_respond`/`_error`, argparse 5 subparsers, main dispatch). list/check 핸들러 구현.
- **완료 기준**: TS-001~003, TS-012 GREEN. `run.sh list` JSON 반환.
- **테스트**: TS-001, TS-002, TS-003, TS-012
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 2

#### Step 4: usage live --help 구현
- [ ] 완료
- **소속 기능**: F-003
- **영역**: 도구
- **agent**: opal-be-agent
- **파일**: `opal/tools/tool-scan/tool_scan.py` (cmd_usage + _resolve_usage)
- **작업 내용**: §3.3.2 — self-help(OPAL=exit0 판정 / 외부=stdout+stderr 병합), context7/url=포인터, inline, doc 분기. live:true. 정적 캐시 금지.
- **완료 기준**: TS-020~023 GREEN. exit0+ok:false stub 성공 판정, 출력 변경 자동 반영.
- **테스트**: TS-020, TS-021, TS-022, TS-023
- **실행 방법**: sub-agent
- **의존**: Step 3 (동일 파일 순차)

#### Step 5: which/resolve/federation/routing 구현
- [ ] 완료
- **소속 기능**: F-004
- **영역**: 도구
- **agent**: opal-be-agent
- **파일**: `opal/tools/tool-scan/tool_scan.py` (cmd_which/cmd_resolve), `opal/tools/tool-scan/lib/federation.py` (신규)
- **작업 내용**: §3.4 — federation.py(mcps.md 정규식 파서 + skills-registry.json json 파서, getReferencesDir 답습, ReDoS 방어). §3.4.3 결정론 라우팅(when[]+triggers 정규식+mcps 설명, 안정 정렬). resolve kind별 invoke(tool=shell / mcp=ToolSearch 포인터 / pilot-skill=//alias / op-skill=dispatch+dispatched_by).
- **완료 기준**: TS-030~035 GREEN. skills-registry.json 원본 무변경, 결정론 출력.
- **테스트**: TS-030, TS-031, TS-032, TS-033, TS-034, TS-035
- **실행 방법**: sub-agent
- **의존**: Step 4 (동일 파일 순차)

#### Step 6: AGENT.md 인지 맵 정비
- [ ] 완료
- **소속 기능**: F-005
- **영역**: 에이전트
- **agent**: PM 직접
- **파일**: `opal/core/AGENT.md`
- **작업 내용**: §3.5.2 — localhost 행 수정(cmux-tool 1순위/playwright 폴백) + cmux-tool 행 추가 + (선택)tool-scan 행 + R-7 사용 규율 문단(사용법 선확인·에러 종류 진단후 폴백). 배포 경계 준수(소스만).
- **완료 기준**: TS-040~041 GREEN.
- **테스트**: TS-040, TS-041
- **실행 방법**: direct
- **의존**: 없음 (병렬)

#### Step 7: 레지스트리 drift 정합 (tools.md + harness §9)
- [ ] 완료
- **소속 기능**: F-006
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `opal/core/references/tools.md`, `opal/core/references/opal-harness.md`
- **작업 내용**: §3.6.2 — tools.md brain-tool 섹션 신설 + 변경이력 행(7a, 즉시) / tool-scan 섹션 추가(7b, Step 2 후) / harness §9에 code-scan·cmux·tool-scan 행 추가. 두 표 도구 집합 동일화.
- **완료 기준**: TS-050~051 GREEN. 두 표 == 7도구.
- **테스트**: TS-050, TS-051
- **실행 방법**: direct
- **의존**: brain/code-scan/cmux 부분 없음(병렬) / tool-scan 부분 Step 2

#### Step 8: install-mac.sh tool-scan 등록
- [ ] 완료
- **소속 기능**: F-007
- **영역**: 환경
- **agent**: opal-task-agent
- **파일**: `scripts/install-mac.sh`
- **작업 내용**: §3.7.2 — `:1084` 직후 tool-scan chmod 블록 + (선택)test-tool chmod 보정. install 실행은 캡틴.
- **완료 기준**: TS-060 GREEN.
- **테스트**: TS-060
- **실행 방법**: sub-agent
- **의존**: Step 3 (run.sh 존재)

#### Step 9: docs/ 갱신 판단
- [ ] 완료
- **소속 기능**: 문서
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/ARCHITECTURE.md`(도구 배포 모델 — 신규 도구 추가 시), `docs/CONVENTIONS.md`(신규 패턴 도입 시)
- **작업 내용**: tool-scan 신규 도구 = 새 capability discovery 패턴 도입 → ARCHITECTURE.md "도구 인벤토리"/2-Layer 모델에 tool-scan 반영 여부 판단. CONVENTIONS에 영향 없으면 스킵.
- **완료 기준**: 갱신 필요 판단 시 반영, 불요 시 스킵 사유 기록.
- **테스트**: 산출물 검사
- **실행 방법**: direct
- **의존**: Step 3, Step 7 완료 후

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 → Step 3/4/5 | **RED-first 게이트**: 테스트 선작성(작성자) 후 구현(구현자) — 작성자≠구현자 (H-2) |
| Step 3 → Step 4 → Step 5 | 동일 파일(`tool_scan.py`) 순차 수정 — 파일 충돌 방지 |
| Step 2 ∥ Step 6 ∥ Step 7(brain/code-scan/cmux) | 독립 파일(manifest / AGENT.md / 레지스트리) — 무충돌 |
| Step 6 ∥ Step 1~5 전체 | AGENT.md는 tool-scan 코드와 완전 독립 (병렬 극대화) |
| Step 7(tool-scan) → Step 2 후 | 도구명·서브명령 확정 후 섹션 작성 |
| Step 8 → Step 3 | run.sh 존재 후 chmod 라인 의미 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | R-1: 4+서브명령 JSON 반환 | TS-001~003 | 5서브명령(list/which/usage/resolve/check) `{"ok":true,...}` JSON + exit 0 |
| F-002 | R-3: usage 텍스트 미저장 | TS-010~012 | manifest grep `--help` 본문 부재, usage_source 포인터만, 7 엔트리 |
| F-003 | R-2: live --help, exit0 판정 | TS-020~023 | exit code 기준 성공 판정, 출력 변경 자동 반영, stderr 병합 |
| F-004 | R-4·R-5: routing + federation 불파괴 | TS-030~035 | resolve 3예시(cmux/context7/op-data-model), skills-registry 무변경, 결정론 |
| F-005 | R-6·R-7: 인지맵 + 규율 | TS-040~041 | cmux-tool 행 존재·localhost 1순위, 사용법 선확인·진단후 폴백 문단 |
| F-006 | R-8: drift 정합 | TS-050~051 | 두 표 7도구 동일, brain 섹션·code-scan/cmux 행 존재 |
| F-007 | R-9: install 등록 | TS-060 | install-mac.sh tool-scan chmod 라인 존재 |

### 5.2 회귀 테스트
- [ ] 기존 state-tool/test-tool/cmux-tool 테스트 스위트 전부 GREEN (회귀 0)
- [ ] `skill-registry.js` list/find 정상 동작 (skills-registry.json 불파괴 검증 — H-1)
- [ ] mcps.md·skills-registry.json·tools.md 기존 소비자(install·harness) 무영향

### 5.3 코드/문서 품질
- [ ] `[MUST] 'docs/CONVENTIONS.md' §@header`: tool_scan.py·federation.py 상단 @header 블록
- [ ] `[MUST] 'docs/CONVENTIONS.md' §파일/폴더`: snake_case (tool_scan.py)
- [ ] 변경 문서(AGENT.md/tools.md/harness.md)에 변경이력 행 추가
- [ ] 표준 라이브러리만 사용 (외부 패키지 0 — state-tool T-11)
- [ ] ERROR_CODES 카탈로그 SSOT 일관 (test-tool 패턴)

### 5.4 보안
- [ ] subprocess 호출 시 shell=False (인자 리스트) — 셸 인젝션 방지
- [ ] federation 입력 파일 경로 화이트리스트(getReferencesDir 결과만) — 임의 경로 Read 금지
- [ ] ReDoS 방어: triggers 정규식 입력 길이 제한(256자, skill-registry.js 정책 답습)
- [ ] 하드코딩 시크릿/토큰 없음, .env 미참조

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 9개 | 복잡 |
| 변경 파일 수 | 신규 4(run.sh/tool_scan.py/manifest.json/federation.py+tests) + 수정 4(AGENT.md/tools.md/harness.md/install) = 8+ | 복잡 |
| 모듈 범위 | 다중(신규 도구 + 인지맵 + 레지스트리 + install) | 복잡 |
| 작업 유형 | 신규 도구 개발 + 정비 | 복잡 |
| 외부 의존성 | 신규 도구·federation 읽기 | 복잡 |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

```
Batch 0 (RED 게이트):  [opal-test-agent] Step 1
        │ (게이트 통과 = RED 확인)
        ▼
Batch 1 (병렬):  [opal-be-agent] Step 2(manifest)
                 [PM 직접]       Step 6(AGENT.md)  ∥  Step 7a(brain/code-scan/cmux)
        ▼
Batch 2 (구현 순차, 동일 파일):  [opal-be-agent] Step 3 → Step 4 → Step 5
        ▼
Batch 3 (병렬):  [PM 직접] Step 7b(tool-scan 섹션)  ∥  [opal-task-agent] Step 8(install)
        ▼
Batch 4:  [PM 직접] Step 9(docs/ 판단) + 회귀 테스트(opal-test-agent)
```

**그룹핑 원칙**: tool_scan.py 수정 Step(3/4/5)은 동일 파일 → 같은 에이전트(opal-be-agent) 순차. 테스트 작성(Step 1)은 self-confirming 방지 위해 **반드시 별도 agent(opal-test-agent)**.

### C-2. 스킬 요구사항
- 기존 스킬: op-dev-execute(구현), op-dev-test(테스트 작성·실행).
- 갭: 없음 — 기존 도구 패턴(state/test-tool) 답습으로 충분, 신규 스킬 불필요.

### C-3. 도구 요구사항
- CLI: 신규 tool-scan(본 작업 산출물). 기존 cmux-tool(usage 검증 대상).
- MCP: sequential-thinking(manifest 스키마·routing 구조화 — 설계 보조).
- 패키지: 없음(표준 라이브러리).

### C-4. 테스트 전략
- 기능 테스트: `python -m unittest opal/tools/tool-scan/tests/test_tool_scan.py` (Step 1 작성, Batch 2 후 GREEN).
- 회귀: state-tool/test-tool/cmux-tool/skill-registry.js 기존 스위트.
- 코드 품질: @header 검사, snake_case, ERROR_CODES 일관.
- 보안: subprocess shell=False, 경로 화이트리스트, ReDoS 방어.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 도구 런타임 | Python 3.x (`~/.opal/.venv`) + Bash 래퍼 | op-dev-execute |
| 데이터 | JSON manifest + mcps.md(md)·skills-registry.json(json) federation | - |
| 테스트 | unittest (표준 라이브러리, pytest 금지 — state-tool T-11) | op-dev-test |
| 배포 | scripts/install-mac.sh | - |

### 8.2 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|
| sequential-thinking | manifest JSON 스키마·resolve 라우팅 알고리즘 구조화 보조 (설계 단계, 미실행) |

### 8.3 참조 문서 (설계 결정 근거)
| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 기획 | TASK.md | `tasks/044-.../TASK.md` | 확정 설계 6항·R-1~R-9·제약 |
| D-2 | 기획 | ANALYSIS.md | `tasks/044-.../ANALYSIS.md` | 7대상 전수조사·부록(install/인지맵/drift/usage_source) |
| D-3 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | @header·snake_case·배포경계·RED-first |
| D-4 | 설계 | ARCHITECTURE.md | `docs/ARCHITECTURE.md` | 도구 배포 모델·2-Layer |
| D-5 | 소스 | test_tool.py | `opal/tools/test-tool/test_tool.py:1-253` | @header·ERROR_CODES·_respond/_error·argparse 패턴 |
| D-6 | 소스 | cmux run.sh | `opal/tools/cmux-tool/run.sh:54-99` | --help JSON 구조·exit0+ok:false 함정 |
| D-7 | 소스 | cmux README | `opal/tools/cmux-tool/README.md:146-163` | 에러계약·fallback (usage=수정/cmux_not_installed=폴백) |
| D-8 | 소스 | skill-registry.js | `opal/tools/skill-registry/skill-registry.js:60-99` | federation 불파괴 범위·getReferencesDir·ReDoS 방어 |
| D-9 | 소스 | skills-registry.json | `opal/core/references/opal-skills-registry.json:365-379` | op-data-model 엔트리(resolve 예시) |
| D-10 | 소스 | mcps.md | `opal/core/references/mcps.md:14-64` | MCP federation 입력 구조 |
| D-11 | 소스 | AGENT.md | `opal/core/AGENT.md:244-257` | 인지맵 정비 대상(R-6/R-7) |
| D-12 | 소스 | tools.md | `opal/core/references/tools.md:464-475` | drift 정합·변경이력 |
| D-13 | 소스 | opal-harness.md | `opal/core/references/opal-harness.md:238-247` | §9 도구 표 drift |
| D-14 | 소스 | install-mac.sh | `scripts/install-mac.sh:1044-1108` | 도구 chmod 등록 패턴 |

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | skills-registry.json 스키마 파괴 → install·harness 깨짐 | F-004 | 높음 | 읽기만(federation), 원본 무변경 단언 TS-033 (H-1) |
| R-2 | self-confirming(구현자가 테스트 맞춤) | F-001/3/4 | 높음 | RED-first 작성자(opal-test-agent)≠구현자(opal-be-agent) Step 분리 (H-2) |
| R-3 | mcp-schema live 부재 → resolve mcp 오동작 | F-004 | 중간 | mcps.md 파싱(도구명/설명만)+ToolSearch 포인터, 스키마 미반환 (H-3) |
| R-4 | cmux --help exit0+ok:false 오판정 | F-003 | 높음 | exit code 기준 판정 강제, stub 검증 TS-020 (H-4) |
| R-5 | manifest usage 텍스트 저장으로 drift 부활 | F-002 | 중간 | text:null 강제, grep 단언 TS-010 (H-9) |
| R-6 | usage 정적 캐시화(R-2 위반) | F-003 | 중간 | 매 호출 live 셸 실행, 출력 변경 반영 TS-021 (H-8) |
| R-7 | drift 정합 누락(brain 섹션 신설 부담) | F-006 | 낮음 | 두 표 집합 동일성 단언 TS-050 (H-5) |
| R-8 | install chmod 누락(test-tool 선례) | F-007 | 낮음 | chmod 라인 grep 단언 TS-060, test-tool 보정 (H-6) |
| R-9 | resolve 비결정성 → 라우팅 신뢰성 저하 | F-004 | 중간 | 안정 정렬(-score,kind,name), 반복 동일성 TS-034 (H-10) |
| R-10 | 외부 CLI --help stderr-only → 빈 usage | F-003 | 중간 | stdout+stderr 병합 캡처 TS-022 (H-7) |

---

## 설계 피드백 / 미해결

1. **외부 CLI 엔트리 부재(설계 결정)**: 초기 manifest 7 엔트리는 모두 OPAL 도구(self-help=run.sh). 순수 외부 CLI(예: cmux 바이너리 자체) 엔트리는 1차 범위에서 제외 — cmux-tool 래퍼가 채널링하므로 raw cmux 직접 노출 불필요(TASK §확정 6 래퍼 채널링). usage의 외부 CLI stdout+stderr 병합 로직은 향후 확장 대비 구현하되 테스트는 stub으로 검증(TS-022).
2. **MCP/skill을 manifest에 미저장(설계 결정)**: TASK §확정 5(federation 불파괴) 준수 → mcp/skill은 list/resolve 시 동적 federation. manifest는 OPAL atomic 도구만 SSOT. → list/resolve가 manifest+federation 통합 결과를 반환(§3.4.2).
3. **tool-scan 자기 usage_source(미세 결정)**: `run.sh list`로 자기 list 출력을 usage로 노출하거나 `--help` argparse 사용. 구현 시 argparse `--help`(표준)를 1순위 권고 — 별도 list 호출 불필요.
4. **R-7 강제 한계 정직(TASK §확정 6)**: "사용법 선확인 100% 하드게이트 불가"는 메커니즘상 한계 → AGENT.md 규율(protocol) + 래퍼 채널링 + tool-scan 쉬운 기본 경로로 대체. PLAN은 이를 새 기능으로 추가하지 않고 §3.5.2 규율 문단 + resolve 편의성으로만 반영(Simplicity First).
5. **docs/ 갱신 범위 미확정**: Step 9에서 PM이 ARCHITECTURE.md 도구 인벤토리 반영 여부 판단(신규 도구이므로 갱신 가능성 높음).
