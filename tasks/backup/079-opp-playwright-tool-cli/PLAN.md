# PLAN: playwright-tool CLI 구현 + wtm 스킬 연동

> 작성일: 2026-04-03 | 태스크: 079-opp-playwright-tool-cli

---

## 1. 멀티브라우저 vs 멀티탭 비교 분석

### 비교표

| 항목 | 멀티브라우저 (CLI 방식) | 멀티탭 (MCP 방식) |
|------|----------------------|-----------------|
| **속도** | 프로세스 시작 오버헤드 있음 (~1~2초). 각 요청이 독립 실행되므로 진정한 병렬 처리 가능. | MCP 서버는 이미 기동된 상태이므로 탭 열기가 빠름. 그러나 탭 간 순차 전환으로 실질 속도 저하. |
| **리소스 (메모리/CPU)** | 브라우저 인스턴스당 ~100~200MB RAM. N개 동시 실행 시 N배 소비. headless 모드로 최소화 가능. | 단일 브라우저 프로세스 공유. 메모리는 효율적이나, 단일 이벤트 루프 병목. |
| **격리 수준** | 완전 격리 (프로세스 분리). 쿠키, 세션, 캐시 완전 독립. 한 인스턴스 크래시가 다른 인스턴스에 무영향. | 같은 브라우저 컨텍스트 공유 가능. 탭 간 상태 누수 위험. 탭 전환 경쟁(race condition) 발생. |
| **구현 복잡도** | 단순. `playwright.chromium.launch()` + headless. JSON stdout 출력. run.sh 래퍼 패턴(xlsx-tool 동일). | MCP 프로토콜 위에서 탭 관리 로직 추가 구현 필요. `browser_tabs` 도구로 탭 ID 추적. 복잡도 높음. |
| **OPAL 아키텍처 적합성** | OPAL 도구 우선 원칙(opal-harness §8)에 부합. Bash CLI로 호출하므로 에이전트 병렬 디스패치와 자연스럽게 연동. | MCP는 단일 서버 프로세스 = PM 직접 순차 수집 패턴만 지원. 에이전트 병렬 디스패치와 충돌. |
| **실용성** | 각 wtm 서브에이전트가 `run.sh {URL}` 호출 → 독립 브라우저 → 진정한 병렬 수집. OPAL venv에 playwright 이미 설치됨으로 즉시 사용 가능. | MCP 서버가 실행 중이어야 하고, 동일 브라우저 내 탭 전환 경쟁으로 인해 병렬화가 불완전. |

### 결론: **멀티브라우저(CLI) 방식 채택**

근거:
1. **격리 완전성**: 에이전트 N개가 동시에 `run.sh`를 Bash 호출하면 각자 독립 브라우저 인스턴스 → 탭 충돌 원천 차단.
2. **OPAL 아키텍처 일치**: OPAL 도구 우선 원칙 + Bash CLI 패턴(xlsx-tool)과 동일 구조.
3. **이미 설치된 playwright 활용**: `~/.opal/.venv`에 playwright가 설치되어 있어 추가 설치 불필요.
4. **MCP 종속성 제거**: browser 모드가 MCP 서버 기동 여부에 의존하지 않아 신뢰성 향상.
5. **멀티탭 단점 명확**: MCP는 단일 이벤트 루프로 탭 간 순차 처리만 가능해 병렬화 이점 없음.

---

## 2. playwright-tool CLI 설계

### 2.1 디렉토리 구조

```
opal/tools/playwright-tool/
├── main.py      # Python CLI 구현
└── run.sh       # Bash 래퍼 (xlsx-tool 패턴)
```

### 2.2 `run.sh` 설계

xlsx-tool 패턴 기반. 주요 차이점: playwright venv 설치 체크 추가.

```bash
#!/bin/bash
# playwright-tool 래퍼 — OPAL .venv python 호출
VENV_PYTHON="$HOME/.opal/.venv/bin/python"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 1. venv 존재 확인
if [[ ! -x "$VENV_PYTHON" ]]; then
  echo '{"ok":false,"error":"OPAL .venv not found. Run install-mac.sh first."}' >&2
  exit 1
fi

# 2. playwright 패키지 설치 확인 (import 가능 여부)
if ! "$VENV_PYTHON" -c "import playwright" 2>/dev/null; then
  echo '{"ok":false,"error":"playwright not installed in .venv. Run: ~/.opal/.venv/bin/pip install playwright"}' >&2
  exit 1
fi

exec "$VENV_PYTHON" "$SCRIPT_DIR/main.py" "$@"
```

**xlsx-tool 대비 차이점**: playwright 패키지 import 가능 여부 추가 체크 (playwright는 pip 설치 외에 `playwright install` 브라우저 다운로드도 필요하므로, 브라우저 바이너리는 main.py 내부에서 오류 메시지로 안내).

### 2.3 `main.py` 인터페이스 설계

**인자 (argparse)**:

| 인자 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| `url` | positional | 필수 | - | 수집할 URL |
| `--mode` | `{full,clean}` | 선택 | `full` | 콘텐츠 추출 모드 |
| `--output` | 파일 경로 | 선택 | - | 지정 시 파일 저장, 미지정 시 stdout JSON |
| `--timeout` | int (초) | 선택 | `30` | 페이지 로딩 타임아웃 |

**출력 형식 (stdout, JSON)**:

성공 시:
```json
{"ok": true, "url": "https://...", "mode": "full", "path": "/path/to/output.md", "content": "# 페이지 타이틀\n..."}
```
- `path`: `--output` 미지정 시 `null`, 지정 시 저장된 파일 경로
- `content`: 항상 stdout으로 출력 (파일 저장 여부와 무관)

실패 시:
```json
{"ok": false, "url": "https://...", "error": "오류 메시지"}
```

**에러 처리**:
- `TimeoutError`: 타임아웃 초과 → `{"ok":false,"error":"timeout: page load exceeded 30s"}`
- `playwright._impl._errors.Error`: 브라우저 미설치 → `{"ok":false,"error":"browser not installed. Run: ~/.opal/.venv/bin/playwright install chromium"}`
- 기타 예외: `str(e)` 그대로 error 필드에 출력

**내부 동작 (playwright sync API)**:
1. `sync_playwright()` 컨텍스트 진입
2. `chromium.launch(headless=True)` — 항상 headless
3. `page.goto(url, timeout=timeout*1000, wait_until="networkidle")`
4. `page.content()` → HTML 취득
5. 모드에 따라 본문 추출 (BeautifulSoup 또는 정규식):
   - **full**: `<script>`, `<style>` 태그 제거 후 전체 텍스트 → Markdown 변환
   - **clean**: 추가로 `<nav>`, `<header>`, `<footer>`, `<aside>` 제거 후 본문 추출
6. MD 정제 → stdout JSON 출력 또는 파일 저장

### 2.4 playwright sync vs async API 선택

**sync API 채택**.

근거:
- CLI 도구이므로 단일 URL 처리 = 이벤트 루프 불필요
- `sync_playwright()` 컨텍스트 매니저가 더 간결하고 에러 처리가 명확
- xlsx-tool.py도 동기 방식 (openpyxl)으로 일관성 유지
- async API는 `asyncio.run()` 래핑이 필요하여 불필요한 복잡도 추가

---

## 3. wtm SKILL.md 변경 계획

### 3.1 변경 범위 개요

| 섹션 | 변경 유형 | 내용 |
|------|----------|------|
| 추출 모드 표 (`--browser` 행) | 수정 | "Playwright MCP 즉시 사용" → "playwright-tool CLI 즉시 호출" |
| 실행 흐름 다이어그램 | 수정 | Phase 2: "Playwright MCP" → "playwright-tool CLI" |
| Phase 2 섹션 전체 | 수정 | MCP 호출 → CLI 호출로 교체, MCP 등록 안내 제거 |
| 복수 URL 처리 기준표 | 수정 | browser 모드 조건을 "PM 직접 순차 수집" 대상에서 제외 |
| 의존성 섹션 | 수정 | MCP 의존성 → CLI 도구 의존성으로 교체 |
| 변경이력 | 추가 | v1.7 항목 추가 |

### 3.2 Phase 2 변경 상세 (MCP 호출 → CLI 호출)

**현재 (v1.6)**:
```
Phase 2: Playwright MCP
  1. browser_navigate(url)
  2. browser_snapshot() → Accessibility Tree
  3. Claude가 Markdown 정제
  4. 스냅샷 보관 (/tmp/playwright-mcp/ → task 폴더)
```

**변경 후 (v1.7)**:
```
Phase 2: playwright-tool CLI
  1. run.sh 경로 확인: ~/.opal/tools/playwright-tool/run.sh
  2. Bash 호출: bash {run.sh} {url} --mode {full|clean}
  3. JSON 출력 파싱: {"ok": true, "content": "..."}
  4. content를 MD 정제 규칙에 따라 최종 정제
  5. {slug}.md 저장
  실패 시: {"ok": false, "error": "..."} → 오류 안내 후 중단
```

**browser 모드 진입 시 사전 확인 변경**:
- 현재: `playwright` MCP 도구(`browser_navigate`) 가용 여부를 ToolSearch로 확인
- 변경: `~/.opal/tools/playwright-tool/run.sh` 파일 존재 여부를 Bash로 확인
  ```bash
  # 확인 명령
  ls ~/.opal/tools/playwright-tool/run.sh 2>/dev/null || echo "NOT_FOUND"
  ```
  미설치 시 안내 메시지:
  ```
  playwright-tool CLI가 설치되어 있지 않습니다.
  설치 방법: install-mac.sh 실행 후 옵션 1 (OPAL 설치) 선택
  ```

### 3.3 복수 URL + browser 모드 처리 방식 변경

**현재 (v1.6) 처리 방식 선택 기준표**:
```
| URL 수 6개 이상 또는 browser 모드 포함 | PM 직접 순차 수집 |
```

**변경 후 (v1.7)**:
```
| URL 수 6개 이상 (browser 모드 제외) | PM 직접 순차 수집 |
| browser 모드 + 복수 URL             | 에이전트 병렬 디스패치 허용 |
```

이유: CLI 방식은 각 에이전트가 독립 브라우저 인스턴스를 생성하므로 탭 충돌 없이 진정한 병렬 처리 가능. MCP 방식(탭 공유)과 달리 경쟁 조건 없음.

**디스패치 프롬프트 변경**:
- 현재: `Phase 1(WebFetch) 시도 후 실패하면 Phase 2(브라우저)로 폴백`
- browser 모드 디스패치: `browser 모드: playwright-tool CLI를 직접 호출하여 콘텐츠를 추출해줘. WebFetch 단계를 생략하고 즉시 CLI를 실행한다.`

### 3.4 Phase 1 실패 → Phase 2 폴백 변경

**현재**: "Phase 2(Playwright MCP)로 폴백" → MCP `browser_navigate` 호출

**변경 후**: "Phase 2(playwright-tool CLI)로 폴백" → Bash run.sh 호출

폴백 흐름:
```
Phase 1(WebFetch) 실패
  └─ Phase 2: bash ~/.opal/tools/playwright-tool/run.sh {url} --mode {full|clean}
       ├─ {"ok": true} → content 정제 → MD 저장 → 성공
       └─ {"ok": false} → 오류 사유 보고 후 중단
```

### 3.5 의존성 섹션 변경

**현재**: `playwright` MCP 서버 등록 필수 / settings.json 설정 안내

**변경 후**: `playwright-tool` CLI 설치 확인

```markdown
### 필수 도구

| 도구 | 필요 시점 | 미설치 시 동작 |
|------|----------|--------------|
| `playwright-tool` CLI | browser 모드 진입 시, 또는 Phase 1 실패 후 Phase 2 진입 시 | 설치 안내 메시지 출력 후 즉시 중단 |

설치 확인:
  ls ~/.opal/tools/playwright-tool/run.sh

미설치 시 설치 방법:
  scripts/install-mac.sh → 옵션 1 (OPAL 설치)
```

---

## 4. install-mac.sh 변경 계획

### 4.1 참조 패턴 (xlsx-tool)

현재 install-mac.sh의 `install_opal()` 함수에서 `opal/tools/` 전체를 `~/.opal/tools/`로 복사:

```bash
# ── 도구 (opal/tools/ → ~/.opal/tools/) ──
if [[ -d "$opal_dir/tools" ]]; then
    install_dir "$opal_dir/tools" "$opal_home/tools" "OPAL 도구"
    ...
fi
```

`install_dir` 함수는 `cp -Rf "$src"/. "$dst"/` 방식으로 전체 디렉토리를 복사한다.

### 4.2 playwright-tool 배포 방식

`opal/tools/playwright-tool/` 디렉토리를 `opal/tools/` 하위에 생성하면, 기존 `install_dir "$opal_dir/tools" "$opal_home/tools"` 호출이 **자동으로 playwright-tool 포함 배포**한다.

즉, **install-mac.sh 코드 수정 없이** `opal/tools/playwright-tool/` 디렉토리를 생성하는 것만으로 배포 경로가 추가된다.

다만, `run.sh`에 실행 권한이 필요하므로 배포 후 권한 부여가 필요하다. 현재 xlsx-tool의 run.sh도 동일한 상황이므로, install-mac.sh에 명시적 `chmod +x` 추가를 권장한다.

### 4.3 install-mac.sh 변경 위치

`install_opal()` 함수 내 도구 설치 블록 (`# ── 도구 (opal/tools/ → ~/.opal/tools/) ──`) 아래에 다음을 추가:

```bash
# ── playwright-tool 실행 권한 ──
local playwright_run="$opal_home/tools/playwright-tool/run.sh"
if [[ -f "$playwright_run" ]]; then
    chmod +x "$playwright_run"
    success "playwright-tool run.sh 실행 권한 설정"
fi
```

> 참고: xlsx-tool run.sh에도 동일 chmod 패턴 적용을 권장 (현재 미적용 상태이나 이번 태스크 범위 외).

---

## 5. 실행 체크리스트 (EXECUTE 워커용)

### Step 1: playwright-tool 디렉토리 생성 및 run.sh 작성

- [ ] `opal/tools/playwright-tool/` 디렉토리 생성
- [ ] `opal/tools/playwright-tool/run.sh` 작성
  - xlsx-tool run.sh 패턴 기반
  - VENV_PYTHON 경로: `$HOME/.opal/.venv/bin/python`
  - playwright import 가능 여부 체크 추가
  - `exec "$VENV_PYTHON" "$SCRIPT_DIR/main.py" "$@"`
- [ ] run.sh 실행 권한 설정 (`chmod +x`)

### Step 2: playwright-tool main.py 작성

- [ ] `opal/tools/playwright-tool/main.py` 작성
  - argparse: `url` (positional), `--mode {full,clean}`, `--output`, `--timeout`
  - playwright sync API 사용 (`from playwright.sync_api import sync_playwright`)
  - headless=True, timeout=30초 기본값
  - full 모드: script/style 제거 + 전체 HTML → Markdown 변환
  - clean 모드: 추가로 nav/header/footer/aside 제거
  - 성공: `{"ok": true, "url": ..., "mode": ..., "path": ..., "content": ...}` stdout 출력
  - 실패: `{"ok": false, "url": ..., "error": ...}` stdout 출력 후 `sys.exit(1)`
  - `--output` 지정 시 content를 파일로 저장, path 필드에 경로 기록
  - `--output` 미지정 시 path는 `null`

### Step 3: install-mac.sh 수정

- [ ] `install_opal()` 함수 내 도구 설치 블록 이후에 playwright-tool chmod 블록 추가
  - 위치: `install_dir "$opal_dir/tools" ...` 호출 다음
  - 내용: `playwright-tool/run.sh` 존재 시 `chmod +x`

### Step 4: wtm SKILL.md 수정

- [ ] 파일: `skills/web-to-markdown/SKILL.md`
- [ ] **추출 모드 표** `--browser` 행 설명 변경
  - "Playwright MCP 즉시 사용" → "playwright-tool CLI 즉시 호출"
- [ ] **browser 모드 설명 단락** 수정
  - "Phase 2(Playwright MCP)로 즉시 진입" → "Phase 2(playwright-tool CLI)로 즉시 진입"
- [ ] **실행 흐름 다이어그램** 수정
  - Phase 2 레이블: "Playwright MCP" → "playwright-tool CLI"
  - Phase 2 내부: `browser_navigate(url) → browser_snapshot()` → `bash run.sh {url} --mode {mode}`
  - "MCP 미등록 → 설치 안내 후 중단" → "run.sh 미설치 → 설치 안내 후 중단"
- [ ] **Phase 2 섹션** 전체 교체
  - 제목: "Phase 2: Playwright MCP" → "Phase 2: playwright-tool CLI"
  - 설치 확인: MCP 등록 체크 → run.sh 파일 존재 체크
  - 실행: MCP 도구 호출 → Bash CLI 호출
  - 미설치 안내: MCP 설정 JSON → install-mac.sh 안내
  - 스냅샷 보관 단계 제거 (CLI는 직접 content 반환, /tmp 복사 불필요)
- [ ] **복수 URL 처리 기준표** 수정
  - `"URL 수 6개 이상 또는 browser 모드 포함 → PM 직접 순차 수집"` 행을
  - `"URL 수 6개 이상 (browser 모드 제외) → PM 직접 순차 수집"` + `"browser 모드 + 복수 URL → 에이전트 병렬 디스패치 허용"` 두 행으로 분리
- [ ] **PM 직접 순차 수집 패턴** 섹션 내 browser 모드 관련 언급 제거 또는 수정
  - "동일 호스트이거나 browser 모드 적용 대상" 조건에서 browser 모드 제거
- [ ] **Phase 1 실패 → Phase 2 폴백** 흐름 문구 수정
  - "Phase 2(Playwright MCP)로 폴백" → "Phase 2(playwright-tool CLI)로 폴백"
  - 실행 흐름 다이어그램 내 폴백 분기 레이블 일치 확인
- [ ] **의존성 섹션** 교체
  - 필수 MCP 표 → 필수 도구 표 (playwright-tool CLI)
  - MCP 등록 방법(settings.json) → run.sh 설치 확인 + install-mac.sh 안내
  - **사전 확인 규칙** 수정: ToolSearch → Bash `ls` 명령으로 run.sh 존재 확인
- [ ] **산출물 형식** 내 `추출 방식` 필드 값 업데이트
  - "WebFetch | Playwright MCP" → "WebFetch | playwright-tool CLI"
- [ ] **결과 보고 표** 수정
  - "Playwright MCP" → "playwright-tool CLI"
- [ ] **변경이력** v1.7 추가
  - `| v1.7 | 2026-04-03 | Phase 2를 Playwright MCP → playwright-tool CLI로 교체, browser 모드 병렬 디스패치 허용, MCP 의존성 제거 (079) |`

### Step 5: 동작 검증

- [ ] run.sh 직접 실행 테스트: `bash opal/tools/playwright-tool/run.sh https://example.com`
  - 예상 출력: `{"ok": true, "url": "https://example.com", ...}`
  - JSON 파싱 가능 여부 확인: `bash opal/tools/playwright-tool/run.sh https://example.com | python3 -m json.tool`
- [ ] mode 옵션 테스트: `--mode clean`
- [ ] output 옵션 테스트: `--output /tmp/test-playwright.md` → 파일 생성 확인 + path 필드 일치 확인
- [ ] timeout 체크: `--timeout 1 https://example.com` → TimeoutError 발생 시 `{"ok": false, "error": "timeout: ..."}` 확인
- [ ] 오류 케이스 확인: 잘못된 URL(예: `https://invalid.invalid`) → `{"ok": false, "error": "..."}`
- [ ] wtm SKILL.md 변경 내용 리뷰 (browser 모드 플로우 일관성, Phase 1 실패 → Phase 2 폴백 문구 확인)

---

## QA 체크리스트

- [ ] 멀티브라우저 vs 멀티탭 비교가 충분한 근거와 함께 작성되었는가
- [ ] main.py 인터페이스가 명확하게 설계되었는가
- [ ] wtm SKILL.md 변경 사항이 구체적으로 명시되었는가
- [ ] install-mac.sh 변경 방법이 xlsx-tool 패턴과 일치하는가
- [ ] 실행 체크리스트가 순서대로 검증 가능한 단위로 작성되었는가
