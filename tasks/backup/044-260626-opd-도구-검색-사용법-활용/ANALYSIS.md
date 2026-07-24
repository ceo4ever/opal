# ANALYSIS: 도구·MCP·스킬 통합 검색·사용법·활용 체계

> 작성일: 2026-06-26
> 입력: TASK.md
> 출력: ANALYSIS.md

---

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | 프로젝트 정의 SSOT | `docs/PROJECT.md` | 프로젝트 구성·문서 레지스트리 |
| D-2 | 설계 | 코드·문서 컨벤션 | `docs/CONVENTIONS.md` | 네이밍·@header·배포경계·플랫폼분기 규칙 |
| D-3 | 설계 | 아키텍처 | `docs/ARCHITECTURE.md` | 도구 배포 모델·2-Layer |
| D-4 | 소스 | 도구 레지스트리 | `opal/core/references/tools.md` | 정합 대상 + 도구 패턴 기준 |
| D-5 | 소스 | MCP 레지스트리 | `opal/core/references/mcps.md` | federation 입력 |
| D-6 | 소스 | 스킬 레지스트리 | `opal/core/references/opal-skills-registry.json` | federation 입력(불파괴) |
| D-7 | 소스 | 글로벌 에이전트 정의(인지맵 원천) | `opal/core/AGENT.md` | 인지맵 정비 대상(R-6/R-7) |
| D-8 | 소스 | cmux 래퍼 | `opal/tools/cmux-tool/` (run.sh·README·docs/CMUX-REFERENCE.md) | 에러계약·라우팅 기준, 사건 당사자 |
| D-9 | 소스 | 도구 패턴 참조 | `opal/tools/state-tool/`·`opal/tools/test-tool/` | run.sh+python+JSON 패턴 답습 |
| D-10 | 소스 | 공통 하네스 §9 | `opal/core/references/opal-harness.md` | 도구 표 drift 정합(R-8) |
| D-11 | 소스 | 설치 스크립트 | `scripts/install-mac.sh` | 신규 도구 배포 등록(R-9) |

---

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/tools/state-tool/run.sh` | Bash 래퍼 — venv python 호출 진입점 | 참조(패턴 답습) | `opal/tools/state-tool/run.sh:1-13` |
| `opal/tools/state-tool/state_tool.py` | Python 진입점 — argparse + JSON 출력 | 참조(패턴 답습) | `opal/tools/state-tool/state_tool.py:1-12` |
| `opal/tools/test-tool/run.sh` | Bash 래퍼 — venv python 호출 진입점 | 참조(패턴 답습) | `opal/tools/test-tool/run.sh:1-13` |
| `opal/tools/test-tool/test_tool.py` | Python 진입점 — 4서브명령 argparse 라우터 | 참조(패턴 답습) | `opal/tools/test-tool/test_tool.py:1-77` |
| `opal/tools/cmux-tool/run.sh` | Bash 디스패처 — 12+1종 서브명령 + --help JSON 출력 | 참조(R-2 --help 검증) | `opal/tools/cmux-tool/run.sh:54-85` |
| `opal/tools/cmux-tool/lib/dispatch.sh` | 에러코드 실제 구현부 (9종 SSOT) | 참조(에러계약) | `opal/tools/cmux-tool/lib/dispatch.sh:43-60` |
| `opal/tools/cmux-tool/README.md` | 에러코드표 9종 + 폴백 계약 | 참조(에러계약 문서 SSOT) | `opal/tools/cmux-tool/README.md:146-163` |
| `opal/core/AGENT.md` | 도구 인지 맵 — 정비 대상 | **변경 필요** (R-6/R-7) | `opal/core/AGENT.md:244-257` |
| `opal/core/references/opal-skills-registry.json` | 스킬 메타 — federation 읽기 입력 | 읽기만 (불파괴) | `opal/core/references/opal-skills-registry.json:1-5` |
| `opal/core/references/mcps.md` | MCP 레지스트리 — federation 읽기 입력 | 읽기만 | `opal/core/references/mcps.md:1-120` |
| `opal/core/references/tools.md` | CLI 도구 레지스트리 — drift 정합 대상 | **변경 필요** (R-8) | `opal/core/references/tools.md:1-476` |
| `opal/core/references/opal-harness.md` | §9 도구 표 — drift 정합 대상 | **변경 필요** (R-8) | `opal/core/references/opal-harness.md:238-247` |
| `scripts/install-mac.sh` | 도구 배포 등록 — 신규 도구 추가 대상 | **변경 필요** (R-9) | `scripts/install-mac.sh:1044-1108` |
| `opal/tools/state-tool/tests/test_state_tool.py` | 기존 도구 테스트 — RED-first 패턴 참조 | 참조(테스트 골격) | `opal/tools/state-tool/tests/test_state_tool.py:1-60` |
| `opal/tools/test-tool/tests/test_test_tool.py` | RED-first 테스트 패턴 SSOT | 참조(신규 도구 테스트 골격) | `opal/tools/test-tool/tests/test_test_tool.py:1-32` |

---

### 1.2 아키텍처 패턴

#### 기존 도구 최소 골격 (state-tool/test-tool 공통 패턴)

**run.sh 패턴** (`opal/tools/state-tool/run.sh:1-13`, `opal/tools/test-tool/run.sh:1-13`):

두 도구 모두 동일한 12줄 Bash 래퍼 구조:
- `VENV_PYTHON="$HOME/.opal/.venv/bin/python"` 고정 경로
- `SCRIPT_DIR` 계산 후 `exec "$VENV_PYTHON" "$SCRIPT_DIR/{tool}_tool.py" "$@"`
- venv 미설치 시 `{"ok":false,"error":"venv_missing","detail":"..."}` JSON + exit 1
- `@header: shell script — 적용 대상 아님 (header-rules.md §적용 대상 확장자 참조)` 주석 명시

**Python 진입점 패턴** (`opal/tools/test-tool/test_tool.py:1-77`):
- 파일 상단 `@header { ... }` docstring 블록 (MUST)
- `ERROR_CODES: Dict[str, str]` SSOT 카탈로그 (임의 변형 금지)
- `_respond(data, exit_code)` — `json.dumps(data, ensure_ascii=False)` 후 sys.exit
- `_error(error_key, detail, command)` — `{"ok": false, "command": ..., "error": ..., "detail": ...}` + sys.exit(1)
- argparse subparsers로 서브명령 라우팅

**서브명령 디스패치 방식**:
- test-tool 4종: resolve / check / unit / integration (`test_tool.py:83-182`)
- state-tool 9종: init / show / advance / mark / block / validate / add-row / status / gate-pass (`state_tool.py:7-12`)
- 성공 응답: `{"ok": true, "command": "<subcommand>", ...}`
- 실패 응답: `{"ok": false, "command": "...", "error": "<error_key>", "detail": "..."}`

**tool-scan 적용 최소 골격 요약**:

| 항목 | 규칙 |
|------|------|
| 진입점 | `opal/tools/tool-scan/run.sh` → `~/.opal/.venv/bin/python tool_scan.py "$@"` |
| Python 파일 | `tool_scan.py` (snake_case — `docs/CONVENTIONS.md §파일/폴더`) |
| JSON 공통 | `{"ok": true/false, "command": "...", "error": "..." (실패 시)}` |
| ERROR_CODES | 카탈로그 dict SSOT — `state-tool:68` / `test-tool:46` 패턴 답습 |
| 서브명령 | list / which / usage / resolve / check (5종) |
| @header | Python 파일 상단 필수 (`docs/CONVENTIONS.md §@header 규칙`) |
| 의존 | `~/.opal/.venv/bin/python` + 표준 라이브러리 우선 (state-tool T-11 원칙) |

---

### 1.3 의존성 맵

#### tool-scan이 federation으로 읽을 입력 소스

```
tool-scan (신규)
  ├── opal/tools/tool-scan/manifest.json        (신규 thin SSOT)
  ├── ~/.opal/references/mcps.md                (읽기 — D-5)
  │     ## {server-name} 섹션 → 제공 도구 목록 파싱
  └── ~/.opal/references/opal-skills-registry.json  (읽기 — D-6)
        groups 구조 순회 → name/alias/triggers/stage/dispatched_by 추출
```

#### opal-skills-registry.json 소비 주체 (불파괴 제약 실제 범위)

1. **`opal/tools/skill-registry/skill-registry.js:64-87`** — Node.js CLI. `getReferencesDir()`로 파일 위치 확인 → `loadJsonFile()`로 파싱. `groups` 딕트 전체 순회하며 `name`/`alias`/`triggers`/`paths`/`description` 필드 참조.
2. **`scripts/install-mac.sh:1263-1276` `install_opal_references()`** — `cp -Rf "$ref_src"/. "$ref_dst"/` 통째 복사. JSON 파일은 strip 없이 그대로 배포.
3. **하네스 런타임** — AGENT.md/harness.md가 skill-registry.js CLI를 통해 간접 소비. JSON 직접 파싱은 에이전트 프롬프트(문서 Read)로만.

**불파괴 제약 실제 범위**: `$schema`, `groups` 최상위 키, 각 엔트리 `name`/`alias`/`description`/`triggers`/`paths`가 skill-registry.js 로직에서 직접 참조됨. `dispatched_by`/`stage`/`pipeline`은 문서 프롬프트 전용. 새 엔트리 추가(읽기 전용)는 불파괴이나 `groups` 구조 변경·기존 필드명 변경은 파괴적.

---

### 1.4 테스트 현황

| 도구 | 테스트 위치 | 프레임워크 | 방식 |
|------|-----------|----------|------|
| state-tool | `opal/tools/state-tool/tests/test_state_tool.py` | unittest (표준 라이브러리) | 모듈 직접 import (`import state_tool as ST`) |
| test-tool | `opal/tools/test-tool/tests/test_test_tool.py` | unittest (표준 라이브러리) | subprocess로 run.sh 호출 — exit code + stdout JSON 단언 |

**test-tool RED-first 핵심 패턴** (`test_test_tool.py:1-32`):
- `subprocess.run(["bash", str(_RUN_SH)] + args)` — 공개 인터페이스만 단언
- `OPAL_CMUX_TOOL_CMD` 환경변수로 실제 stub 쉘 스크립트 주입 (MagicMock/patch 금지)
- state-tool mock 가드 false positive 교훈 반영 (`tasks/033/034`)

**tool-scan RED-first 권고**: test-tool 방식 답습. `tmpdir`에 stub `manifest.json` 생성 주입으로 파일시스템 격리.

---

## 2. 외부 조사 결과

### 2.1 cmux-tool --help 구조 검증 (R-2 실현성)

**실제 확인** (`opal/tools/cmux-tool/run.sh:54-85`): `_show_help()` 함수가 Python `json.dumps()`로 구조화된 JSON 반환:

```json
{
  "ok": false, "error": "usage",
  "usage": "run.sh <url|subcommand> [args...]",
  "subcommands": { "extract": "...", "snapshot": "...", ... },
  "common_output_fields": { "ok": "bool", "command": "string", ... }
}
```

exit code: `exit 0` (`run.sh:99`). 즉 `ok: false`이지만 exit 0.

**R-2 실현성 판정**: **가능**. `subprocess.run(["bash", "run.sh", "--help"])` → exit code 0 확인 + stdout JSON 파싱. 파서는 exit code로 성공 판정(ok 필드 아님).

### 2.2 mcps.md federation 실현성

mcps.md Markdown 구조: `## {server-name}` → `제공 도구:` 목록 (`- \`tool-name\`: 설명`). Python 표준 라이브러리 정규식으로 파싱 가능. 4개 MCP 등록: shadcn / sequential-thinking / context7 / playwright.

`mcp-schema` live 접근(JSON Schema 형식) 경로는 현재 없음 — `opal/core/mcps/*.json`은 MCP 서버 설정(command/args)이며 도구 파라미터 스키마 아님.

### 2.3 opal-skills-registry.json federation 실현성

op 스테이지 스킬 그룹 구조 (실제 확인):

| 그룹 | 엔트리 수 | dispatched_by 있는 그룹 | 특이사항 |
|------|---------|----------------------|--------|
| opal-pilot | 8개 | 없음 (파이프라인 진입) | alias + domain + pipeline 필드 |
| op-dev | 7개 | 있음 | stage 필드 필수 |
| op-sdd | 5개 | 있음 | - |
| op-data | 3개 | 있음 | - |
| op-task | 4개 | 있음 | - |
| standalone | 7개 | 없음 | alias 있는 것도 있음 |
| opal | 4개+ | 없음 | auto_trigger 필드 있음 |

**R-4 예시 검증**: `op-data-model` — triggers: `["^op-data-model$"]` + stage: "MODEL" + dispatched_by: ["opal-pilot-data-design"]. `//erm` alias = erd-modeler의 standalone 그룹 legacy 엔트리 (`"[deprecated] → op-data-model"`).

---

## 3. 영향 범위

### 3.1 직접 영향

| 대상 | 변경 유형 | 상세 |
|------|----------|------|
| `opal/tools/tool-scan/` (신규) | 신규 생성 | run.sh + tool_scan.py + tests/ + manifest.json |
| `opal/core/AGENT.md` | 수정 | 인지 맵 cmux-tool 행 추가 + localhost 행 수정 (R-6), 사용 규율 추가 (R-7) |
| `opal/core/references/tools.md` | 수정 | brain-tool 섹션 신설, tool-scan 섹션 추가 (R-8) |
| `opal/core/references/opal-harness.md` | 수정 | §9 code-scan/cmux-tool/tool-scan 행 추가 (R-8) |
| `scripts/install-mac.sh` | 수정 | tool-scan chmod 블록 추가 (R-9) |

### 3.2 간접 영향

- `~/.opal/AGENT.md` — `install-mac.sh:978` `strip_deploy_md`로 배포 → install 재배포 시 반영
- `~/.opal/references/tools.md` / `opal-harness.md` — `install_opal_references()` cp -Rf로 배포 → install 재배포 시 반영
- `opal-skills-registry.json` — 불파괴 (읽기만), 변경 없음

### 3.3 영향 범위 요약

- [ ] DB 스키마 변경 — 해당 없음
- [ ] API 인터페이스 변경 — 해당 없음
- [x] 설정/환경변수 변경 — install-mac.sh tool-scan chmod 라인 추가 (소스만)
- [ ] 빌드/배포 파이프라인 변경 — 해당 없음

---

## 4. 핵심 발견 사항

1. **run.sh 래퍼가 완전 표준화됨**: state-tool/test-tool 양 도구가 동일한 12줄 Bash 래퍼를 사용. tool-scan/run.sh는 복사-적응으로 충분. 차이점: state-tool은 `{"ok":false,"error":"OPAL .venv not found..."}` (detail 없음), test-tool은 `"error":"venv_missing","detail":"..."` (detail 포함). PLAN에서 통일 방식 결정 필요.

2. **cmux-tool --help가 이미 JSON 구조화됨**: `run.sh:54-85` `_show_help()`가 exit 0 + `json.dumps()` 출력. R-2(live --help 추출)는 subprocess 호출로 즉시 구현 가능. `ok: false + exit 0` 패턴 주의 — exit code 기준으로 성공 판정해야 함.

3. **인지 맵 오라우팅이 코드로 확인됨**: `opal/core/AGENT.md:254` — "SPA·동적 렌더·localhost 페이지 접근 | `playwright` MCP" (cmux-tool 부재). `install-mac.sh:978` strip_deploy_md 경로로 배포됨. R-6 수정 범위: 해당 1행 수정 + cmux-tool 신규 1행 추가.

4. **drift가 정확히 3도구 × 2문서 = 6곳**: harness §9에 없는 것: code-scan / cmux-tool. tools.md에 없는 것: brain-tool. 신규 tool-scan은 양쪽 추가. 정합 작업은 기계적으로 수행 가능.

5. **install-mac.sh tool 추가 패턴 확립됨**: `줄 1044-1084` — `install_dir()`로 `opal/tools/` 전체 복사 후 도구별 chmod 블록. 신규 도구는 `줄 1084` 이후에 4줄짜리 if 블록만 추가하면 됨. Python 도구는 venv 설치(공통, `install_opal_venv()`)로 자동 처리.

---

## 5. 제약/리스크

| 항목 | 설명 | 심각도 | 근거 |
|------|------|--------|------|
| skills-registry.json 스키마 불파괴 | resolve federation 구현 시 읽기만 허용. groups 구조·기존 필드명 변경 불가. skill-registry.js가 name/alias/triggers/paths 파싱 | 높음 | `opal/tools/skill-registry/skill-registry.js:64-87` |
| mcp-schema live 접근 경로 부재 | `usage_source: mcp-schema` 구현 시 파라미터 JSON Schema 없음. mcps.md Markdown 파싱(도구명/설명만)으로 대체 필요 | 중간 | `opal/core/references/mcps.md` — 제공 도구 필드만 있고 JSON Schema 없음 |
| self --help 파싱 ok:false 함정 | cmux-tool --help: exit 0이지만 `ok: false, error: "usage"` 반환. 파서가 ok 기준으로 성공 판정 시 오판 | 낮음 | `opal/tools/cmux-tool/run.sh:54-85, 99` |
| RED-first 작성자≠구현자 규율 | tool-scan은 self-confirming 위험 → RED-first 적용 의무. 테스트 작성(PLAN 워커)과 구현(EXECUTE 워커)을 분리해야 함 | 높음 | `tasks/044-.../TASK.md §제약 조건`, `docs/CONVENTIONS.md §RED-first` |
| brain-tool tools.md 섹션 신설 부담 | harness §9에는 brain-tool 1행 있으나 tools.md에 섹션 없음. brain-tool 전체 사용법 섹션 신설 필요 (상당 분량) | 낮음 | `opal/core/references/tools.md:464-476` (변경이력 v1.3 이후 미추가) |
| test-tool 배포 chmod 미등록 가능성 | state/brain/cmux는 chmod 블록 명시. test-tool은 `install-mac.sh:1056-1084` 구간에 없음 → run.sh 실행 권한 미설정 가능성 (현행 동작 영향 없을 시 무시, 있으면 R-9와 함께 수정) | 낮음 | `scripts/install-mac.sh:1056-1084` |

---

## 6. 기술 컨텍스트

### 6.1 기술 스택

| 카테고리 | 기술 | 버전/비고 |
|----------|------|----------|
| 도구 런타임 | Python | `~/.opal/.venv` 공유 venv |
| 래퍼 | Bash | macOS/Linux 공통 |
| 데이터 포맷 | JSON (표준 라이브러리 json) | 외부 패키지 불필요 |
| 테스트 프레임워크 | unittest (표준 라이브러리) | pytest 금지 (state-tool T-11) |
| 배포 | `scripts/install-mac.sh` | install_dir() + chmod +x 패턴 |
| federation 입력 | Markdown (mcps.md) + JSON (opal-skills-registry.json) | 읽기만 |

### 6.2 추천 스킬

| 스킬 | 용도 |
|------|------|
| op-dev-plan | 신규 tool-scan 구현 계획 (서브명령 설계·manifest 스키마·federation 구현) |
| op-dev-execute | Python/Bash 코드 구현 |

### 6.3 추천 MCP

| MCP | 용도 |
|-----|------|
| sequential-thinking | manifest JSON 스키마 설계 / resolve 알고리즘 구조화 |

---

## 부록: PLAN 직접 사용 사실 정리

### A. install-mac.sh tool-scan 등록 위치 (R-9)

삽입 위치: `scripts/install-mac.sh:1084` (cmux-tool lib/ chmod 블록 직후):

```bash
# ── tool-scan 실행 권한 (044) ──
local tool_scan_run="$opal_home/tools/tool-scan/run.sh"
if [[ -f "$tool_scan_run" ]]; then
    chmod +x "$tool_scan_run"
    success "tool-scan run.sh 실행 권한 설정"
fi
```

`opal/tools/` → `~/.opal/tools/` 전체 복사는 `줄 1046`의 `install_dir`이 이미 처리. chmod 블록만 추가하면 됨.

### B. 인지 맵 정비 대상 정확한 위치 (R-6)

`opal/core/AGENT.md:254` (배포 원천 `install-mac.sh:978`):

현재: `| SPA·동적 렌더·localhost 페이지 접근 | playwright MCP | 읽기(선제) | references/mcps.md |`

수정 후: `| SPA·동적 렌더·localhost 페이지 접근 | cmux-tool 우선 / playwright MCP 폴백 | 읽기(선제) | references/tools.md |`

추가 행(cmux-tool): `| 브라우저 자동화·웹 크롤링·E2E (cmux 환경) | cmux-tool | 읽기(선제) | references/tools.md |`

### C. drift 정합 매트릭스 (R-8)

| 도구 | tools.md | harness §9 | 정합 액션 |
|------|----------|-----------|---------|
| xlsx-tool | 있음 | 있음 | 없음 |
| state-tool | 있음 | 있음 | 없음 |
| code-scan | 있음 | **없음** | harness §9 표에 1행 추가 |
| cmux-tool | 있음 | **없음** | harness §9 표에 1행 추가 |
| brain-tool | **없음** | 있음 | tools.md에 섹션 신설 |
| test-tool | 있음 | 있음 | 없음 |
| tool-scan (신규) | 없음 | 없음 | 양쪽 추가 |

### D. usage_source 4종 기술적 실현성 판정

| usage_source 유형 | 실현 방법 | 판정 |
|-----------------|---------|------|
| `self --help` (OPAL 래퍼) | subprocess → exit 0 + JSON stdout 파싱 | **가능** (cmux-tool 검증 완료) |
| `self --help` (외부 CLI) | subprocess → stdout 원문 반환 (stderr 병합 필요) | **가능** |
| `mcp-schema` | mcps.md Markdown 파싱 → 도구명/설명만 | **부분 가능** (JSON Schema 없음) |
| `context7/url` (슬라이스) | manifest에 URL 포인터 반환 → LLM이 MCP 호출 | **가능** (포인터 방식) |
| `inline/doc:<path>` | manifest inline 텍스트 또는 파일 Read | **가능** |

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-06-26 | 초기 작성 — 7개 분석 대상 전수 조사 + PLAN 직접 사용 가능 수준 산출물 (044) |
