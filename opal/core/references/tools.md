# OPAL Tools

> OPAL 에이전트가 파일 처리, 데이터 변환 등 특정 작업 시 호출하는 CLI 도구 레지스트리.
> 새 도구 추가 시 이 파일에 등록하고 install-mac.sh의 `install_opal_venv()`를 통해 배포한다.

---

## xlsx-tool

**용도**: xlsx 파일 읽기, 쓰기, 검색, 메타데이터 조회  
**실행 경로**: `~/.opal/tools/xlsx-tool/run.sh`  
**소스 경로**: `opal/tools/xlsx-tool/`  
**의존성**: `~/.opal/.venv` (openpyxl, pandas)

### 커맨드

```bash
# 시트 목록, 행/열 수, 헤더 메타데이터 조회
~/.opal/tools/xlsx-tool/run.sh info <file>

# 데이터 읽기 (JSON 출력)
~/.opal/tools/xlsx-tool/run.sh read <file> [--sheet <name|index>] [--range <A1:Z100>] [--header-row <n>]

# 키워드 검색
~/.opal/tools/xlsx-tool/run.sh search <file> --keyword <text> [--sheet <name>] [--range <A1:Z100>]

# 데이터 쓰기 (신규 또는 수정)
~/.opal/tools/xlsx-tool/run.sh write <file> --data '<json>' [--sheet <name>] [--mode new|update] [--format]
~/.opal/tools/xlsx-tool/run.sh write <file> --data-file <path.json> [--sheet <name>] [--mode new|update] [--format]
```

### 출력 형식

모든 커맨드는 JSON으로 출력한다.

```json
// 성공
{ "ok": true, "command": "read", "data": [...] }

// 실패
{ "ok": false, "command": "read", "error": "Sheet 'foo' not found" }
```

### 사용 예시

```bash
# 파일 구조 파악
~/.opal/tools/xlsx-tool/run.sh info project.xlsx

# 특정 시트 읽기
~/.opal/tools/xlsx-tool/run.sh read data.xlsx --sheet "2026"

# 키워드로 셀 찾기
~/.opal/tools/xlsx-tool/run.sh search wbs.xlsx --keyword "백엔드"

# JSON 데이터로 새 파일 생성 (서식 포함)
~/.opal/tools/xlsx-tool/run.sh write output.xlsx \
  --data '[{"이름":"홍길동","부서":"개발"}]' \
  --format

# 기존 파일의 특정 시트 업데이트
~/.opal/tools/xlsx-tool/run.sh write report.xlsx \
  --mode update --sheet "요약" \
  --data '[{"항목":"완료","수":"12"}]'
```

---

## state-tool

**용도**: STATE.md 파이프라인 현황판 JSON SSOT 관리 — 9개 서브 명령으로 행 상태 갱신, 검증, 추가작업 삽입  
**실행 경로**: `~/.opal/tools/state-tool/run.sh`  
**소스 경로**: `opal/tools/state-tool/`  
**의존성**: `~/.opal/.venv/bin/python` (표준 라이브러리만 — `json`, `argparse`, `pathlib`, `subprocess`, `re`, `sys`, `datetime`, `os`)

### 커맨드

```bash
# state.json + STATE.md 신규 생성 (TASK 단계 시작 시)
~/.opal/tools/state-tool/run.sh init <task-path> \
  --skill <opp|opd|opds|opdw|opwt|opgc|oppd|opsdd> \
  --mode <interactive|agentic> \
  [--task-title <text>] [--next-action <text>] \
  [--rows-spec <inline-json>] [--rows-from <path-to-skill.md>] \
  [--force] [--note <text>] [--import-existing]

# 파이프라인 현황판 출력 (md/json/full)
~/.opal/tools/state-tool/run.sh show <task-path> [--format md|json|full]

# ⬜→🔄 전환 한정 (단계 시작 시)
~/.opal/tools/state-tool/run.sh advance <task-path> --row <N> [--note <text>]

# ⬜/🔄→✅ 전환 (단계 완료, Gate, 워커 Step 완료)
~/.opal/tools/state-tool/run.sh mark <task-path> \
  --row <N> --done \
  [--note <text>] \
  [--as-worker --worker-stage <stage>] \
  [--step <N/M>] \
  [--owner <PM|worker|user|auto>] \
  [--auto-pass] [--force]

# any→❌ + current_status=blocked
~/.opal/tools/state-tool/run.sh block <task-path> --row <N> --reason <text>

# 정합성 검증 (PM Gate 전 필수)
~/.opal/tools/state-tool/run.sh validate <task-path>

# 추가작업 행 삽입 (행 N 직후)
~/.opal/tools/state-tool/run.sh add-row <task-path> \
  --after <N> --stage <단계> --item <항목명> [--note <text>]

# current_status 명시 전환
~/.opal/tools/state-tool/run.sh status <task-path> \
  --set <in_progress|done|blocked|additional_work|additional_work_done> \
  [--note <text>]

# [deprecated] gate-pass — 레거시 전용. 신규 태스크는 PM Gate 통과 후 단일 mark 사용
# (State Gate/QA Gate 행이 제거되어 4행 패턴 성립 안 함 — Phase4 완료)
~/.opal/tools/state-tool/run.sh gate-pass <task-path> --start <N> [--note <text>]
```

### 출력 형식

모든 커맨드는 단일 라인 JSON으로 출력한다.

```json
// 성공
{"ok": true, "command": "mark", "row_id": 5, "stage": "PLAN", "item": "작업", "timestamp": "2026-05-01 18:00"}

// validate 성공
{"ok": true, "command": "validate", "violations": [], "violations_count": 0}

// 실패
{"ok": false, "command": "mark", "error": "worker_scope_violation", "message": "..."}

// 실패 (violations 포함)
{"ok": false, "command": "validate", "violations": [{"code": "marker_missing", "row_id": null, "detail": "..."}], "violations_count": 1}
```

### 사용 예시

```bash
# TASK 단계 시작 — state.json + STATE.md 생성 (opp 표준 20행 외부 주입)
~/.opal/tools/state-tool/run.sh init tasks/134-.../ \
  --skill opp --mode interactive \
  --task-title "파이프라인 state-tool 도입" \
  --rows-spec '[{"stage":"TASK","item":"작업"},{"stage":"TASK","item":"사용자 확인"},...]'

# SKILL.md에서 행 구성 자동 파싱
~/.opal/tools/state-tool/run.sh init tasks/134-.../ \
  --skill opp --mode interactive \
  --rows-from ~/.opal/skills/opal-pilot-project/SKILL.md

# 단계 시작 (⬜→🔄)
~/.opal/tools/state-tool/run.sh advance tasks/134-.../ --row 4

# 단계 완료 (→✅)
~/.opal/tools/state-tool/run.sh mark tasks/134-.../ --row 4 --done

# 워커 EXECUTE Step 완료 (→✅, 권한 게이트 적용)
~/.opal/tools/state-tool/run.sh mark tasks/134-.../ \
  --row 12 --done --as-worker --worker-stage EXECUTE --step 3/8

# [deprecated] gate-pass — 레거시 전용 (PLAN Gate 행이 6번부터 시작하는 예시, 신규 사용 금지)
~/.opal/tools/state-tool/run.sh gate-pass tasks/134-.../ --start 6

# PM Gate 전 정합성 검증
~/.opal/tools/state-tool/run.sh validate tasks/134-.../

# 현황판 출력 (기본 마크다운)
~/.opal/tools/state-tool/run.sh show tasks/134-.../

# 사용자 확인 행 처리
~/.opal/tools/state-tool/run.sh mark tasks/134-.../ \
  --row 11 --done --owner user --note "{owner_name} 확인: PLAN 단계 검토 완료"

# 추가작업 행 삽입
~/.opal/tools/state-tool/run.sh add-row tasks/134-.../ \
  --after 19 --stage CLOSE --item "추가 검증" --note "추가작업 진입"

# 추가작업 완료 상태 전환
~/.opal/tools/state-tool/run.sh status tasks/134-.../ \
  --set additional_work_done --note "추가작업 완료"

# 기존 STATE.md 흡수 (회귀 마이그레이션)
~/.opal/tools/state-tool/run.sh init tasks/134-.../ \
  --skill opp --mode interactive --import-existing
```

### 종료 코드

| 코드 | 의미 |
|------|------|
| `0` | 성공 |
| `1` | 위반 / 스코프 오류 / 검증 실패 (`worker_scope_violation`, `marker_missing`, `state_not_initialized` 등) |
| `2` | 내부 오류 (`date_tool_failed`, `rows_acts_not_implemented` 등) |

> 근거: `tasks/134-260501-opp-pipeline-state-tool/TASK.md` T-3 / `PLAN.md` §2.18 에러 코드 카탈로그 23종 SSOT

---

## code-scan

**용도**: 코드 파일의 `@header` 메타블록 스캔 — 도메인/레이어/의존 관계 조회  
**실행 경로**: `node ~/.opal/tools/code-scan/code-scan.js <command>`  
**소스 경로**: `opal/tools/code-scan/`  
**의존성**: Node.js (외부 패키지 없음)

### 커맨드

```bash
# 전체 스캔 (scope 미지정 시 프로젝트 전체)
node ~/.opal/tools/code-scan/code-scan.js scan [path] [--scope <name>]

# 도메인별 조회 (인자 없으면 목록)
node ~/.opal/tools/code-scan/code-scan.js domain [name]

# 레이어별 조회 (인자 없으면 목록)
node ~/.opal/tools/code-scan/code-scan.js layer [name]

# 헤더 내 패턴 검색 (정규식 지원, 대소문자 무시)
node ~/.opal/tools/code-scan/code-scan.js search <pattern>
# 예: search "auth.*service", search "^user", search "login|logout"

# 도메인/레이어 요약
node ~/.opal/tools/code-scan/code-scan.js summary

# 의존 관계 추적
node ~/.opal/tools/code-scan/code-scan.js depends <module>

# @header 없는 파일 목록
node ~/.opal/tools/code-scan/code-scan.js missing
```

### 주요 옵션

| 옵션 | 설명 |
|------|------|
| `--scope <name>` | 스코프 필터 (`.opal/code-scan.json`의 `scopes` 키) |
| `--domain <name>` | 도메인 필터 |
| `--layer <name>` | 레이어 필터 |
| `--exclude <patterns>` | 제외 패턴 (쉼표 구분, 와일드카드 지원) |
| `--brief` | 한 줄 요약 출력 (기본값) |
| `--full` | 전체 헤더 JSON 출력 |
| `--json` | 파이프용 raw JSON 출력 |

### 프로젝트 설정

프로젝트 루트의 `.opal/code-scan.json`으로 스코프와 필터를 정의한다.

```json
{
  "scopes": { "be": "workspace/backend/", "fe": "workspace/frontend/src/" },
  "extensions": [".py", ".js", ".ts", ".vue"],
  "exclude": ["node_modules", "__pycache__"],
  "excludePatterns": ["__init__.py", "test_*", "*.spec.ts"]
}
```

### PM 관리 방안

`{프로젝트}/.opal/code-scan.json`은 PM이 생성하고 관리한다.

- **생성 시점**: code-scan 도구를 처음 사용하려 할 때 파일이 없으면 PM이 생성
- **갱신 트리거**: 신규 도메인/폴더 추가, 대규모 리팩토링, 신규 언어 도입
- **PM Gate 확인**: EXECUTE 완료 후 PM Gate에서 신규 scope/domain 반영 여부 확인

상세 관리 절차: `~/.opal/references/opal-pm.md` §9 참조

### 사용 예시

```bash
# BE 스코프 도메인 요약
node ~/.opal/tools/code-scan/code-scan.js summary --scope be

# auth 모듈 의존 관계 추적
node ~/.opal/tools/code-scan/code-scan.js depends auth

# @header 누락 파일 확인
node ~/.opal/tools/code-scan/code-scan.js missing --scope fe

# exports 필드 전용 검색 (정규식 지원, 대소문자 무시)
node ~/.opal/tools/code-scan/code-scan.js exports "issueToken"
# 예: exports "^get[A-Z]", exports "Token$", exports "create|update"

# @header 검증 (PM Gate용)
node ~/.opal/tools/code-scan/code-scan.js scan src/auth/auth.service.ts --json
```

---

## cmux-tool

**용도**: cmux browser 자동화 래퍼 — 12+1종 서브명령으로 웹 자동화·추출·상호작용을 단일 도구로 처리  
**실행 경로**: `bash ~/.opal/tools/cmux-tool/run.sh`  
**소스 경로**: `opal/tools/cmux-tool/`  
**의존성**: `cmux` 0.64.3 이상 (macOS 전용, 선택 설치) + Python 3.x (JSON 직렬화, 내장)  
**환경 변수**: `$CMUX_SURFACE_ID` (cmux 터미널 내 자동 설정)

### 트리거 조건

알투가 아래 사용자 문장을 수신하면 cmux-tool을 우선 선택한다.  
cmux 미설치 시 wtm-agent 경유 호출은 silent fallback → playwright-tool. 단독 호출 시 에러 JSON 반환.

| 사용 시점 | 대표 사용자 문장 | 우선 명령 (cmux-tool) | 폴백 |
|----------|----------------|----------------------|------|
| **웹 크롤링** (HTML 본문 추출) | "URL 읽어줘", "사이트 내용 정리", "이 페이지 마크다운" | `bash run.sh extract <url>` | playwright-tool |
| **정보 수집** (구조화된 데이터 조회) | "스냅샷 떠줘", "현재 페이지 구조 보여줘" | `bash run.sh snapshot --surface <h>` | (정보 조회만 — 폴백 없음) |
| **웹 테스트** (단일 상호작용) | "로그인 버튼 눌러", "이메일 칸에 입력해" | `bash run.sh click <sel>` / `bash run.sh fill <sel> --text <v>` | playwright-tool |
| **E2E 자동화** (다단계 시나리오) | "회원가입 폼 테스트", "결제 흐름 자동화" | `examples/e2e-form-fill.sh` 또는 fill + click + wait + snapshot 조합 | playwright-tool |
| **로컬 SPA·동적 페이지** | "localhost:3000 분석", "Next.js 화면 확인" | `bash run.sh extract <url>` (localhost URL 자동 감지) | playwright-tool |

### 커맨드 (12+1종)

```bash
# 레거시 호환: 첫 인자가 URL이면 extract 자동 라우팅
bash ~/.opal/tools/cmux-tool/run.sh https://example.com

# 서브명령 직접 지정
bash ~/.opal/tools/cmux-tool/run.sh extract https://example.com [--mode full|clean] [--wait <ms>]
bash ~/.opal/tools/cmux-tool/run.sh extract --surface <h> [<url>]  # B/C 모드
bash ~/.opal/tools/cmux-tool/run.sh snapshot [--surface <h>] [--compact]
bash ~/.opal/tools/cmux-tool/run.sh eval --script "<js>" [--surface <h>]
bash ~/.opal/tools/cmux-tool/run.sh wait --load-state complete [--surface <h>] [--timeout-ms N]
bash ~/.opal/tools/cmux-tool/run.sh wait --selector "<sel>" [--surface <h>]
bash ~/.opal/tools/cmux-tool/run.sh navigate <url> [--surface <h>]
bash ~/.opal/tools/cmux-tool/run.sh click <selector> [--surface <h>]
bash ~/.opal/tools/cmux-tool/run.sh fill <selector> --text <value> [--surface <h>]
bash ~/.opal/tools/cmux-tool/run.sh open <url>
bash ~/.opal/tools/cmux-tool/run.sh open-split <url>
bash ~/.opal/tools/cmux-tool/run.sh reload [--surface <h>]
bash ~/.opal/tools/cmux-tool/run.sh press <key> [--surface <h>]
bash ~/.opal/tools/cmux-tool/run.sh get <selector> [--attr <name>] [--surface <h>]

# 사용법 보기
bash ~/.opal/tools/cmux-tool/run.sh --help
```

### 출력 형식

공통 5필드 + 명령별 특화 필드로 JSON 출력.

```json
// extract 성공 (기존 8필드 + command 필드 — R-2 호환)
{
  "ok": true, "command": "extract", "method": "cmux", "mode": "A",
  "surface": "surface:3", "user_owned": false,
  "title": "Example", "final_url": "https://example.com",
  "content": "<html>...", "bytes": 315209, "wait_ms": 2000
}

// snapshot 성공
{"ok":true,"command":"snapshot","surface":"surface:3","user_owned":true,"snapshot_text":"...","length":4096}

// 실패 (공통 5필드)
{"ok":false,"command":"click","surface":"surface:3","user_owned":true,"error":"eval_failed","detail":"..."}

// 폴백 트리거 실패 (fallback 필드 포함)
{"ok":false,"command":"extract","error":"cmux_not_installed","fallback":"phase2","install_url":"https://cmux.com/"}
```

### 에러 코드 (SSOT: run.sh / lib/dispatch.sh)

| 코드 | 종료값 | wtm-agent 처리 |
|------|--------|---------------|
| `not_in_cmux` | 2 | 자동 폴백 (phase2) |
| `cmux_not_installed` | 3 | 자동 폴백 (phase2) |
| `surface_parse_failed` | 5 | 자동 폴백 (phase2) |
| `open_failed` | 5 | 자동 폴백 (phase2) |
| `usage` | 1 | 폴백 금지 — 호출자 수정 |
| `invalid_surface` | 4 | 폴백 금지 — 핸들 수정 |
| `goto_failed` | 6 | 폴백 금지 — URL 오류 |
| `wait_failed` | 7 | 폴백 금지 — 네트워크/셀렉터 |
| `eval_failed` | 8 | 폴백 금지 — 명령 오류 |

> 에러 코드 신규 추가 순서: (1) run.sh / lib/dispatch.sh → (2) README.md → (3) tools.md → (4) AGENT.md

### 사용 예시

```bash
# URL 추출 (extract A 모드)
bash ~/.opal/tools/cmux-tool/run.sh https://docs.example.com

# 사용자 surface 현재 페이지 스냅샷 (B 모드)
bash ~/.opal/tools/cmux-tool/run.sh snapshot --surface surface:3

# 폼 자동화 (click + fill + wait)
bash ~/.opal/tools/cmux-tool/run.sh fill "#email" --text "user@example.com" --surface surface:3
bash ~/.opal/tools/cmux-tool/run.sh click "[type=submit]" --surface surface:3
bash ~/.opal/tools/cmux-tool/run.sh wait --load-state complete --surface surface:3

# E2E 레시피 실행
bash ~/.opal/tools/cmux-tool/examples/e2e-form-fill.sh https://example.com/login \
  --email user@example.com --password secret

# 분기 자동 결정
bash ~/.opal/tools/cmux-tool/examples/e2e-branch-auto.sh https://localhost:3000
```

### 종료 코드

| 코드 | 의미 |
|------|------|
| `0` | 성공 |
| `1` | 사용법 오류 / 알 수 없는 서브명령 |
| `2` | 환경 오류 (CMUX_SURFACE_ID 미설정) |
| `3` | cmux 미설치 |
| `4` | surface 핸들 형식 오류 |
| `5` | browser open / surface 파싱 실패 |
| `6` | URL 이동 실패 |
| `7` | 로드 타임아웃 |
| `8` | 명령 실행 실패 |

---

## test-tool

**용도**: 테스트 단계별 도구 결정론적 집행 — 4서브명령(`resolve`/`check`/`unit`/`integration`)으로 `test-tools.yaml`을 읽어 단계(단위=EXECUTE / 통합=TEST)별 도구를 실행·판정하고 JSON 증거를 반환  
**실행 경로**: `bash ~/.opal/tools/test-tool/run.sh`  
**소스 경로**: `opal/tools/test-tool/`  
**의존성**: `~/.opal/.venv/bin/python` + PyYAML + cmux-tool (E2E 어댑터)

### 트리거 조건

테스트 단계 진입 시 호출한다 — 단위(EXECUTE 자가검증) 또는 통합(TEST). test-tool은 1회 실행·판정만 수행하며, 재시도 루프 한도는 보유하지 않는다(SSOT: `opal-harness.md §1`).

| 서브명령 | 용도 | 단계 |
|---------|------|------|
| `resolve` | `test-tools.yaml` resolution_order(project→global→추론) 해석 → tier×scope 도구셋 JSON 반환 | 단위/통합 공통 |
| `check` | required/optional 게이트 — required 미설치 차단, optional 미설치 skip | 단위/통합 공통 |
| `unit` | lint→build/type→unit 계층 stop-on-fail 단발 실행 | 단위 (EXECUTE) |
| `integration` | cmux-tool 호출→에러코드 소비→playwright 폴백 결정 + 실DB API 통합 | 통합 (TEST) |

### 커맨드

```bash
# test-tools.yaml 해석 → tier×scope 도구셋 JSON
bash ~/.opal/tools/test-tool/run.sh resolve [--stack py|ts] [--project-root PATH]

# required/optional 설치 게이트
bash ~/.opal/tools/test-tool/run.sh check [--category C] [--tier unit|integration] [--project-root PATH]

# 단위 계층 stop-on-fail 단발 실행 (lint→build→unit)
bash ~/.opal/tools/test-tool/run.sh unit [--scope fe|be] [--changed-files ...] [--project-root PATH]

# 통합 — cmux 1순위→playwright 폴백 (E2E) + 실DB API
bash ~/.opal/tools/test-tool/run.sh integration [--scope fe|be] [--url URL] [--project-root PATH]
```

### 출력 형식

모든 서브명령은 JSON으로 출력한다.

```json
// resolve 성공
{ "ok": true, "command": "resolve", "tiers": { "unit": {...}, "integration": {...} }, "source": "...", "stack": "ts" }

// 실패
{ "ok": false, "command": "unit", "error": "layer_failed", "stopped_at": "lint" }
```

---

## brain-tool

**용도**: 프로젝트 브레인 지식 위키 결정론적 집행 — 8 서브명령으로 index·log·링크 무결성을 집행하고 `@header` 단방향 시드를 관리  
**실행 경로**: `bash ~/.opal/tools/brain-tool/run.sh`  
**소스 경로**: `opal/tools/brain-tool/`  
**의존성**: `~/.opal/.venv/bin/python` (표준 라이브러리 우선)

### 트리거 조건

`//opbr` 호출 또는 brain 참조(과거 결정·설계 맥락 조회) 시. `.opal/brain/` 부재 프로젝트에서는 no-op.

### 커맨드 (8 서브명령)

```bash
bash ~/.opal/tools/brain-tool/run.sh init <project-root>        # brain 디렉토리·index 초기화
bash ~/.opal/tools/brain-tool/run.sh add-page <args>            # 신규 페이지(entity/concept/flow 등) 추가 — --related로 관련 페이지 슬러그 CSV 지정 가능
bash ~/.opal/tools/brain-tool/run.sh index                      # index.md 재생성(링크 그래프 갱신)
bash ~/.opal/tools/brain-tool/run.sh log <args>                 # 변경 로그 기록
bash ~/.opal/tools/brain-tool/run.sh search <키워드>            # 후보 목록(page·title·score·snippet) 반환
bash ~/.opal/tools/brain-tool/run.sh sync-header <args>         # code-scan @header → entity 단방향 시드
bash ~/.opal/tools/brain-tool/run.sh lint                       # 링크 무결성·구조 린트
bash ~/.opal/tools/brain-tool/run.sh validate                   # frontmatter·평탄성 검증 — 링크필드(related) 값이 '[[', ']]', '.md'를 포함하면 거부

# 서브명령별 상세 플래그
bash ~/.opal/tools/brain-tool/run.sh <subcommand> --help
```

### 출력 형식

모든 커맨드는 JSON으로 출력한다 (`{"ok": true/false, ...}`). 상세 사용법은 `run.sh <subcommand> --help`(live)로 확인한다.

---

## tool-scan

**용도**: capability(OPAL/외부 CLI 도구·MCP·스킬) 상황 검색 + 권위 출처(live) 사용법 확인 — PM이 "필요 시점에 도구를 꺼내 정확한 사용법으로 사용"하도록 결정론적으로 집행  
**실행 경로**: `bash ~/.opal/tools/tool-scan/run.sh`  
**소스 경로**: `opal/tools/tool-scan/`  
**의존성**: `~/.opal/.venv/bin/python` (표준 라이브러리만 — json/argparse/pathlib/subprocess/re)

### 설계 원칙

- **사용법 텍스트를 저장하지 않는다** — `manifest.json`엔 `usage_source` 포인터만. `usage`는 매 호출 **live `--help`를 셸 실행**해 반환(drift 0).
- **federation(읽기)** — MCP는 `mcps.md`, 스킬은 `opal-skills-registry.json`을 읽기 전용으로 조회(원본 불파괴). OPAL atomic 도구만 매니페스트 SSOT.
- **2단 토큰** — `list`(전체 1줄 용도, 쌈) / `usage`(확정 1개의 live 사용법). 전체 사용법 일괄 주입 안 함.

### 커맨드 (5 서브명령)

```bash
bash ~/.opal/tools/tool-scan/run.sh list                       # 전체 capability 1줄 용도 (kind별)
bash ~/.opal/tools/tool-scan/run.sh which <상황>               # 상황→capability 후보 (가벼움)
bash ~/.opal/tools/tool-scan/run.sh resolve <상황>             # top capability + kind별 invoke + live usage + fallback
bash ~/.opal/tools/tool-scan/run.sh usage <도구> [서브명령]     # 권위 출처 live 사용법 (OPAL=exit0 판정 / 외부=stdout+stderr)
bash ~/.opal/tools/tool-scan/run.sh check <도구>               # 설치/실행 가능 여부
```

### 출력 형식

모든 서브명령은 JSON으로 출력한다.

```json
// resolve — kind별 invoke 형태
{"ok":true,"command":"resolve","situation":"browser check localhost",
 "resolved":{"name":"cmux-tool","kind":"tool","invoke":"shell","exec":"~/.opal/tools/cmux-tool/run.sh ...",
   "usage":{...},"fallback":{...}}}

// resolve — op-skill (워커 디스패치 형태)
{"ok":true,"command":"resolve","resolved":{"name":"op-data-model","kind":"op-skill",
   "invoke":"dispatch","skill_path":"~/.opal/skills/op-data-model/SKILL.md","dispatched_by":["opal-pilot-data-design"]}}

// 실패
{"ok":false,"command":"resolve","error":"no_match","detail":"..."}
```

> kind별 invoke: `tool`=셸 실행 / `mcp`=ToolSearch 포인터(파라미터 스키마는 런타임 ToolSearch) / `pilot-skill`=`//alias` 진입 / `op-skill`=워커 디스패치(SKILL.md 주입).

---

## memory-tool

**용도**: 프로젝트 메모리 인덱스·히스토리 결정론적 집행 — 9서브명령 init/append/update/promote/prune/migrate/show/review/delete. 메모리→docs/brain 졸업 워크플로우·히스토리 FIFO5·요약 길이캡·라이프사이클·마커 직접편집 금지·매 변경 후 자가검토(review)·dead/superseded 정리(delete 무손실 가드)  
**실행 경로**: `~/.opal/tools/memory-tool/run.sh`  
**소스 경로**: `opal/tools/memory-tool/`  
**의존성**: `~/.opal/.venv/bin/python` (표준 라이브러리만 — json/argparse/pathlib/re/sys/datetime/os)

### 트리거 조건

메모리 등록·정리·이관 시 — append(신규 지식), update(상태 전이), promote(졸업), review(health 점검).

### 커맨드 (9 서브명령)

```bash
# MEMORY.md 신포맷 마커·헤더·빈 표 삽입 (create-if-absent)
~/.opal/tools/memory-tool/run.sh init --file <MEMORY.md 경로> [--force]

# 메모리 행 추가 (kind=memory: 지식 인덱스 / kind=history: 작업 히스토리 FIFO5)
~/.opal/tools/memory-tool/run.sh append --file <path> --kind {memory,history} --title <제목> \
  [--type {project,architecture,feedback,preferences,issues,task}] \
  [--status {active,promoted,superseded,dead}] \
  [--summary <요약 ≤80자>] \
  [--stage <단계>] [--path <경로>]  # history 전용

# 메모리 상태/요약/제목 수정 (라이프사이클 전이: active→superseded/dead 등)
~/.opal/tools/memory-tool/run.sh update --file <path> --title <제목> \
  [--status <새 상태>] [--summary <새 요약 ≤80자>] [--new-title <새 제목>]  # --new-title: migrate crude 제목 보정

# 메모리 → 영구 거처 졸업 (이전 확인 후 행+파일 삭제 + provenance 기록)
~/.opal/tools/memory-tool/run.sh promote --file <path> --title <제목> \
  [--to {docs,brain}] [--ref <영구 거처 위치 예: AGENT.md#금지사항>]

# 히스토리 FIFO=5 결정론 정리 (이미 ≤5이면 no-op)
~/.opal/tools/memory-tool/run.sh prune --file <path>

# 구포맷 → 신포맷 변환 (제목 자동 추출 + [REVIEW] 플래그, 행수 보존)
~/.opal/tools/memory-tool/run.sh migrate --file <path>

# 인덱스/히스토리 현황 출력 (read-only)
~/.opal/tools/memory-tool/run.sh show --file <path>

# 자가검토 단독 health 명령 — violations[] + 라이프사이클 후보 반환
~/.opal/tools/memory-tool/run.sh review --file <path>

# dead/superseded 메모리 정리(인덱스 행 제거) — 무손실 가드(active/promoted 거부)
~/.opal/tools/memory-tool/run.sh delete --file <path> --title <제목> [--with-file]  # --with-file: memory/<file>.md도 삭제
```

### 출력 형식

모든 서브명령은 단일라인 JSON으로 출력한다.

```json
// 성공 (변경 명령은 review 블록 자동 첨부)
{"ok": true, "command": "append", "kind": "memory", "title": "...", "active_count": 3,
 "review": {"promote_candidates": [], "cleanup_candidates": [], "violations": [], "history_status": {...}}}

// 실패
{"ok": false, "command": "append", "error": "summary_too_long", "message": "요약 85자 > 80자 제한"}
```

### 주요 에러 코드 (SSOT: memory_tool.py ERROR_CODES)

| 코드 | 의미 |
|------|------|
| `marker_missing` | MEMORY.md에 마커 누락 — init 먼저 실행 |
| `summary_too_long` | 요약 >80자 제한 위반 |
| `promote_ref_missing` | promote 시 --ref(영구 거처 위치) 미지정 — 무손실 가드 |
| `row_not_found` | --title 에 해당하는 인덱스 행 없음 |
| `memory_file_not_found` | 메모리 파일(memory/*.md) 없음 |
| `already_initialized` | 마커 이미 존재 — --force로 재삽입 가능 |
| `import_failed` | 구포맷 파싱 실패 (migrate 시) |
| `delete_requires_dead_or_superseded` | active/promoted 행 delete 시도 — dead/superseded만 제거 가능(무손실 가드) |

### 사용 예시

```bash
# 새 MEMORY.md 초기화
~/.opal/tools/memory-tool/run.sh init --file .opal/MEMORY.md

# 피드백 지식 등록
~/.opal/tools/memory-tool/run.sh append --file .opal/MEMORY.md \
  --kind memory --title "배포 경계 직접편집 금지" \
  --type feedback --summary "~/.opal/ 배포 파일 직접편집 금지, 소스만 수정"

# 작업 히스토리 등록 (6번째부터 자동 FIFO 정리)
~/.opal/tools/memory-tool/run.sh append --file .opal/MEMORY.md \
  --kind history --title "045 메모리 관리 개선" \
  --stage "완료" --path "tasks/045-260626-opd-메모리-관리-개선/" \
  --summary "memory-tool 신설 + SSOT 개정"

# 메모리 → docs 졸업 (이전 완료 확인 후)
~/.opal/tools/memory-tool/run.sh promote --file .opal/MEMORY.md \
  --title "배포 경계 직접편집 금지" \
  --to docs --ref "AGENT.md#금지사항"

# health 점검
~/.opal/tools/memory-tool/run.sh review --file .opal/MEMORY.md
```

---

## git-sync-tool

**용도**: 워크스페이스 아래 여러 독립 git 저장소를 순회하며 안전 일괄 최신화 — 결정론적 집행. clean + fast-forward 가능한 저장소만 `git pull --ff-only`로 자동 최신화하고, 문제 저장소(dirty/diverged/detached/no-upstream/fetch-failed)는 건드리지 않고 skip 사유와 함께 보고한다. 자율 조치(stash/rebase/force/commit/push) 일절 없음 — 헌법 user sovereignty.  
**실행 경로**: `~/.opal/tools/git-sync-tool/run.sh`  
**소스 경로**: `opal/tools/git-sync-tool/`  
**의존성**: `~/.opal/.venv/bin/python` (표준 라이브러리만 — json/argparse/pathlib/sys/subprocess) + 로컬 **git 2.22+** (`git rev-list --left-right --count` 사용)  
**호출자**: `opal-workspace-sync` 스킬(alias `opws`) — 대상 결정·5섹션 보고서·승인 게이트는 스킬이 담당, 도구는 순회·판정·pull만 집행.

### 트리거 조건

워크스페이스(여러 저장소 컨테이너)의 여러 git을 한 번에 최신화할 때. opal-workspace-sync 스킬 STEP 2에서 호출.

### 커맨드 (단일 서브명령)

```bash
# 지정 경로 순회 + 안전 최신화 → JSON 결과
~/.opal/tools/git-sync-tool/run.sh sync <workspace_path>
```

- `<path>/.git` 존재 → 그 1개를 단일 저장소로 처리. 아니면 `<path>` 직속 자식 1단계만 순회(재귀 안 함).
- 저장소별 판정 순서: detached → no-upstream → dirty → fetch → diverged/ff (detached HEAD에서 `@{u}` 조회가 fatal이라 no-upstream보다 선행).

### 출력 형식 (JSON)

```json
{"ok": true, "command": "sync", "workspace": "<절대경로>",
 "repositories": [{"name","branch","upstream","status","reason","ahead","behind","prev_head","new_head","pulled_commits"}],
 "summary": {"total","updated","skipped","failed"}, "error": null}
```

- `status`: `updated` | `skipped` | `failed` | `already-current`
- `reason`: `dirty` | `diverged` | `detached` | `no-upstream` | `fetch-failed` (정상이면 `null`)
- `already-current`는 `total`에 포함되나 updated/skipped/failed 카운트에는 미포함.
- `ok: false` + `error`(예: `PATH_NOT_FOUND`, `NOT_A_DIRECTORY`)는 치명 오류 시. exit 0(ok)/1(에러).

---

## 변경이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-04-03 | xlsx-tool 등록 (076) |
| v1.1 | 2026-04-11 | code-scan 등록 |
| v1.2 | 2026-04-12 | code-scan 섹션에 PM 관리 방안 서브섹션 추가 + exports 커맨드 사용 예시 추가 (109) |
| v1.3 | 2026-05-01 | state-tool 섹션 신규 추가 — 파이프라인 현황판 JSON SSOT 관리 CLI 9개 서브 명령 등록 (134) |
| v1.4 | 2026-05-09 18:30 | 개인 식별자 누설 정정 — note 예시 "캡틴 확인" → "{owner_name} 확인" placeholder 치환 (139) |
| v1.5 | 2026-05-22 10:00 KST | cmux-tool 섹션 신규 추가 — 12+1종 서브명령 + 트리거 조건 5행 매트릭스 + 에러 코드 9종 + fallback 4종 (007) |
| v1.6 | 2026-06-07 | state-tool gate-pass deprecated 표기 — 사용법 블록·예시 2곳에 [deprecated] 레거시 전용 안내 추가. 신규는 PM Gate 통과 후 단일 mark 사용. Phase4 완료 반영 (014 Phase 4) |
| v1.7 | 2026-06-23 | test-tool 섹션 신규 추가 — 테스트 단계별 도구 결정론적 집행 4서브명령(resolve/check/unit/integration) + 트리거 조건 + 커맨드 + 출력 형식. cmux-tool 포맷 답습. 루프 한도 수치 비복제(harness §1 포인터) (039) |
| v1.8 | 2026-06-26 | brain-tool 섹션 신설(8 서브명령) + tool-scan 섹션 신설(5 서브명령 — capability 검색·live 사용법) + harness §9 drift 정합(code-scan·cmux-tool·tool-scan 행 추가). tools.md ↔ harness §9 도구 집합 7종 동일화 (044) |
| v1.9 | 2026-06-26 | memory-tool 섹션 신설(9 서브명령 init/append/update/promote/prune/migrate/show/review/delete) — 프로젝트 메모리 인덱스·히스토리 결정론적 집행, 메모리→docs/brain 졸업 워크플로우·히스토리 FIFO5·요약 길이캡·마커 직접편집 금지·매 변경 후 자가검토·delete(dead/superseded 무손실 정리)·update --new-title(제목 보정). harness §9 drift 정합 (045) |
| v2.0 | 2026-07-02 | git-sync-tool 섹션 신설(단일 서브명령 sync) — 워크스페이스 git 저장소 일괄 동기화, 직속 자식 순회 + ff-only pull + 5종 skip 판정 + JSON 출력. opal-workspace-sync 스킬이 호출. harness §9 drift 정합 (052) |
| v2.1 | 2026-07-10 13:11 | brain-tool validate 설명에 링크필드(related) 값 검사('[[', ']]', '.md' 거부) 반영 + add-page에 `--related` 플래그 설명 추가 (053) |
