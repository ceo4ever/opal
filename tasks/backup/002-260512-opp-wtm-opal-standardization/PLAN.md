# PLAN: wtm-agent OPAL 표준화 + cmux 통합 + 사용자 surface 재사용

> 작성일: 2026-05-12
> 입력: `tasks/002-260512-opp-wtm-opal-standardization/TASK.md`
> 출력: `tasks/002-260512-opp-wtm-opal-standardization/PLAN.md`
> 모드: semi-agentic

---

## 1. 현황 조사

### 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | opal-harness.md | `opal/core/references/opal-harness.md` | §1 Guards(구현 금지), §9 OPAL Tools(`~/.opal/tools/{tool}/run.sh` 래퍼 표준 + JSON 출력) |
| D-2 | 설계 | agents.md | `opal/core/references/agents.md` | L216-221 wtm-agent 레지스트리(현행 Crawl4AI 명시) + L137-150 전문 에이전트 매핑 + L226-237 에이전트 추가 가이드 |
| D-3 | 설계 | web-to-markdown SKILL.md | `skills/web-to-markdown/SKILL.md` | v1.8 현행 호출 인터페이스(L22-30) + 실행 흐름(L82-104) + Phase 1/2(L106-181) + 변경이력(L528-538) |
| D-4 | 소스 | wtm-agent AGENT.md (현행) | `agents/wtm-agent/AGENT.md` | 삭제 대상 — frontmatter L4-9 + Phase 2 Crawl4AI 안내(L40-47) 부정합 원본 |
| D-5 | 설계 | opal-pm.md | `opal/core/references/opal-pm.md` | §11 프로젝트 전문 에이전트 관리(인용 의무 포맷·검토 게이트) |
| D-6 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | §2 인용 포맷 4종 + §2.4 [MUST] 토큰 + §3.1 참조 테이블 스키마 |
| D-7 | 외부 | cmux Browser Automation | [cmux docs](https://cmux.com/ko/docs/browser-automation) | `cmux browser open/get/eval/wait/tab close/goto` 명령 사양 |
| D-8 | 외부 | cmux GitHub | [manaflow-ai/cmux](https://github.com/manaflow-ai/cmux) | 설치 안내 링크(공식 사이트와 함께 미설치 안내 메시지에 포함) |
| D-9 | 소스 | install-mac.sh | `scripts/install-mac.sh` | L723-918 `install_opal()` — `install_dir` 패턴(L186-200) + tools/ 배포(L813-816) + 실행 권한 부여(L819-830) + 변경이력 헤더(L7-18) |
| D-10 | 소스 | opal-task-agent AGENT.md | `opal/agents/opal-task-agent/AGENT.md` | 표준 워커 7단계 프로세스(L12-26) + JSON 결과 5필드(L29-38) + 행동 규칙(L56-63) |
| D-11 | 소스 | opal-be-agent AGENT.md | `opal/agents/opal-be-agent/AGENT.md` | 도메인 전문 워커 구조(자체 로드 문서 + 자체 탐색 + 금지 규칙) — 본 태스크 opal-wtm-agent 패턴 모델 |
| D-12 | 소스 | playwright-tool run.sh | `opal/tools/playwright-tool/run.sh` | OPAL Tools 래퍼 표준(venv 가드 + 의존성 확인 + JSON 에러 출력 + `exec` 위임) |
| D-13 | 설계 | .opal/AGENT.md | `.opal/AGENT.md` | §PM 검토 기준(컴포넌트 표준화) + §금지사항(`~/.opal/` 직접 편집 금지 + 변경이력 누락 금지) |
| D-14 | 설계 | docs/PROJECT.md | `docs/PROJECT.md` | L50 네이밍 규칙 예시 갱신 대상 |
| D-15 | 설계 | docs/CONVENTIONS.md | `docs/CONVENTIONS.md` | L21 범용 에이전트 폴더 예시(현재 `wtm-agent`) 갱신 대상 |
| D-16 | 설계 | docs/ARCHITECTURE.md | `docs/ARCHITECTURE.md` | L49(다이어그램 워커 목록) + L141(에이전트 표) + L275(트리뷰) 갱신 대상 |
| D-17 | 소스 | opal-agent-creator SKILL.md | `opal/skills/opal-agent-creator/SKILL.md` | L66 — kebab-case 예시 `wtm-agent` 인용 갱신 대상(잔존 참조 zero 화) |

> 인용 형식: D-6 §3.1 참조. 유형: `기획` / `설계` / `소스` / `외부`.

### 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `agents/wtm-agent/AGENT.md` | 현행 워커 (삭제 대상) | 삭제 | `agents/wtm-agent/AGENT.md:1-86` |
| `opal/agents/opal-wtm-agent/AGENT.md` | 표준 OPAL 워커 (신규) | 신규 | (신규) |
| `opal/tools/cmux-tool/run.sh` | cmux 래퍼 (신규) | 신규 | (신규) |
| `opal/tools/cmux-tool/README.md` | cmux-tool 사용 가이드 (선택) | 신규 | (신규, 도구별 README 관행에 따름) |
| `skills/web-to-markdown/SKILL.md` | 호출 인터페이스 + Phase 폴백 체인 + 워커 경로 | 수정 | `skills/web-to-markdown/SKILL.md:17-30, 82-104, 144-181, 386-475, 492-523, 528-538` |
| `opal/core/references/agents.md` | wtm-agent 등록 정보 갱신 | 수정 | `opal/core/references/agents.md:214-221` |
| `scripts/install-mac.sh` | cmux-tool 배포 + 실행권한 + 변경이력 | 수정 | `scripts/install-mac.sh:7-18, 813-845` |
| `docs/PROJECT.md` | 네이밍 예시 갱신 | 수정 | `docs/PROJECT.md:50` |
| `docs/CONVENTIONS.md` | 범용 에이전트 폴더 예시 갱신 | 수정 | `docs/CONVENTIONS.md:21` |
| `docs/ARCHITECTURE.md` | 워커 다이어그램·표·트리뷰 갱신 | 수정 | `docs/ARCHITECTURE.md:49, 141, 274-275` |
| `opal/skills/opal-agent-creator/SKILL.md` | 네이밍 예시 갱신 | 수정 | `opal/skills/opal-agent-creator/SKILL.md:66` |
| `agents/wtm-agent/` | 디렉토리 자체 | 삭제 | `agents/wtm-agent/AGENT.md` 단일 파일 |

### 현재 상태

1. **wtm-agent 위치/네이밍 불일치**: `agents/wtm-agent/`는 루트 직속 + `opal-` 접두사 미사용으로 OPAL 표준(`opal/agents/opal-*-agent/`)에서 이탈. CONVENTIONS.md L21·PROJECT.md L50이 이를 명시적 예시로 인정하여 표준 일관성을 깨고 있다.
2. **Crawl4AI 부정합 3건 잔존**:
   - `agents/wtm-agent/AGENT.md:5` frontmatter description → "Phase 2(Crawl4AI)"
   - `agents/wtm-agent/AGENT.md:40-47` 본문 Phase 2 섹션 → Crawl4AI Python 호출 전체 절차
   - `opal/core/references/agents.md:218` → "Phase 1(WebFetch) → Phase 2(Crawl4AI) 폴백"
   - 현실: SKILL.md v1.7부터 Phase 2 = playwright-tool CLI (D-3 §변경이력 v1.7 행)
3. **OPAL 표준 워커 7단계 미준수**: 현 `agents/wtm-agent/AGENT.md`는 자체 정의 Phase 1/2 구조 + 자유 형식 반환을 사용한다. 표준 모델(D-10 §실행 프로세스)은 "스킬 SKILL.md Read → 페르소나 Read → 프로세스 따름 → JSON 5필드 반환".
4. **cmux 통합 부재**: 캡틴이 cmux 0.64.3 터미널 환경에서 자주 작업하지만 web-to-markdown은 cmux 우선 폴백이 없어 사용자 surface 재사용/인증 세션 활용 불가.
5. **OPAL Tools 표준 적용 공백**: cmux 호출 시 직접 `cmux browser open ...`를 명령하는 형태이며 D-1 §9 표준(`~/.opal/tools/{tool}/run.sh` 래퍼 + JSON 출력)을 만족하는 어댑터가 없다.
6. **변경이력 갱신 추적성 의무**: D-13 §업무 수행 지침 — "스킬·에이전트·참조 문서 수정 시 변경이력 표에 행을 추가한다 (일시 KST + 태스크 번호 포함)".

### 영향 범위

- **신규 도구 1개**: `opal/tools/cmux-tool/` → install-mac.sh tools/ 어댑터 자동 흡수 + 실행권한 단건 추가
- **신규 에이전트 1개**: `opal/agents/opal-wtm-agent/` → install-mac.sh `install_opal()` L780-789 `opal/agents/*` 루프 자동 흡수
- **삭제 1개**: `agents/wtm-agent/` 디렉토리 — install-mac.sh L791-803 `agents/*` 루프에서 자동 제외
- **SSOT 갱신 3건**: SKILL.md(v1.8 → v1.9) + agents.md(L214-221) + AGENT.md(신규 v1.0)
- **레지스트리·문서 동기 5건**: PROJECT.md L50 / CONVENTIONS.md L21 / ARCHITECTURE.md L49·L141·L275 / opal-agent-creator SKILL.md L66
- **외부 의존성 영향**: cmux 0.64.3+(선택 의존성) — install-mac.sh는 설치 강제하지 않고 안내만, 미설치 시 Phase 2 자동 건너뜀
- **하위 호환**: `//wtm {url}`, `//wtm --browser {url}`, `--clean/--wireframe` 등 기존 호출 인터페이스 모두 유지 (R-6 신규 모드는 추가 옵션)

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|
| N-1 | `opal/tools/cmux-tool/run.sh` | cmux browser 래퍼 (URL 모드 A + 사용자 surface 모드 B/C 통합, `--wait` 옵션, JSON 출력, B/C cleanup 가드) | D-1 §9 "OPAL 도구는 모두 `~/.opal/tools/{tool-name}/run.sh` 래퍼를 통해 호출한다" / TASK §확정 방향 §5·§6·§7·§8 |
| N-2 | `opal/tools/cmux-tool/README.md` | 도구 사용법 + 의존성(cmux 0.64.3+) + 입출력 스키마 + 안전 가드 | 도구별 사용자 문서 관행 — playwright-tool 등 기존 도구와 동일 수준의 자가설명 보장 |
| N-3 | `opal/agents/opal-wtm-agent/AGENT.md` | OPAL 표준 워커 — 7단계 프로세스, JSON 5필드 반환, 안전 규칙, 변경이력 v1.0 | D-10 §실행 프로세스 L12-26 + §결과 반환 형식 L29-38 / TASK R-1 |

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| M-1 | `skills/web-to-markdown/SKILL.md` | (a) 호출 인터페이스에 `//wtm --surface <handle>`, `//wtm --surface <handle> {url}`, `--wait <ms>` 추가 (b) 실행 흐름을 Phase 1→2(cmux 조건부)→3(playwright-tool CLI) 3단계로 재구성 (c) 신규 §Phase 2 cmux 사양 섹션(명령 시퀀스 + 환경 감지 + 미설치 안내) (d) 기존 §Phase 2 playwright-tool CLI → §Phase 3로 재번호 + 진입 조건 갱신 (e) §의존성 표에 cmux(선택) 행 추가 (f) §복수 URL 처리 — 워커 이름 `opal-wtm-agent` + 경로 갱신 (g) §변경이력 v1.9 행 추가 | D-3 L17-30/82-104/144-181/386-475/492-523/528-538 + TASK R-5·R-6·R-7·R-8 |
| M-2 | `opal/core/references/agents.md` | §wtm-agent → §opal-wtm-agent 갱신: 역할 문구를 Phase 1→2(cmux)→3(playwright-tool CLI)로 재정의 + 입력에 `url|--surface`, `mode`, `--wait` 명시 + 출력 JSON 5필드 형식 명시 + 호출 시점/모델/에이전트 경로 추가 | D-2 L214-221 + D-2 L226-237 §에이전트 추가 가이드 |
| M-3 | `scripts/install-mac.sh` | (a) 변경이력 헤더에 v2.2 행 추가 (b) `install_opal()` 내 tools/ 처리 직후(L816-822 인접) `cmux-tool/run.sh` chmod +x 블록 추가 (c) cmux 의존성 안내 메시지 출력 분기(설치 감지 — 정보성, 강제 아님) | D-9 L7-18 변경이력 패턴 + L813-830 chmod 블록 패턴 + TASK R-11 |
| M-4 | `docs/PROJECT.md` | L50: `agents/` 행 예시에서 `wtm-agent` 제거 후 비고에 "범용 에이전트는 본 프로젝트에 현재 없음(`opal-wtm-agent`는 OPAL 전용)" 명시. 또는 `wtm-agent` 토큰을 삭제하고 다른 범용 예시가 없으면 행 자체를 비고 보강 | D-14 L50 + TASK R-2 |
| M-5 | `docs/CONVENTIONS.md` | L21: "범용 에이전트 폴더: `agents/{agent-name}/` — `wtm-agent` (OPAL 무관)" 행을 `agents/` 디렉토리 비어있음 표기 또는 향후용 명시로 갱신. OPAL 표준 위치는 그대로 유지 | D-15 L21 + TASK R-2 |
| M-6 | `docs/ARCHITECTURE.md` | L49 다이어그램의 `wtm-agent: 웹→마크다운 변환` → `opal-wtm-agent: 웹→마크다운 변환` / L141 표의 `wtm-agent` → `opal-wtm-agent` / L274-275 트리뷰의 `agents/wtm-agent/` 행 제거 + 트리뷰 상단 `opal/agents/` 섹션에 `opal-wtm-agent/` 추가 | D-16 L49·L141·L274-275 + TASK R-2 |
| M-7 | `opal/skills/opal-agent-creator/SKILL.md` | L66 예시 `wtm-agent` → `opal-wtm-agent` 치환 | D-17 L66 + TASK R-2 |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| X-1 | `agents/wtm-agent/AGENT.md` | OPAL 표준 위치(`opal/agents/opal-wtm-agent/`)로 이전. SSOT 중복 제거 (TASK R-2 + 확정 방향 §1) |
| X-2 | `agents/wtm-agent/` (빈 디렉토리) | AGENT.md 삭제 후 잔여 빈 폴더 제거 |

### 구현 순서

> 의존 원칙: 하위 레이어(도구) → 상위 레이어(에이전트) → 통합 레이어(스킬/레지스트리/문서) → 정리(삭제) → 추적(변경이력).

| 순서 | Phase | 작업 | 파일 | 예상 난이도 |
|------|-------|------|------|-----------|
| 1 | Phase 1 | cmux-tool run.sh 신규 (래퍼 + 3모드 + `--wait` + cleanup 가드) | N-1 | 중 |
| 2 | Phase 1 | cmux-tool README.md 신규 | N-2 | 하 |
| 3 | Phase 2 | opal-wtm-agent AGENT.md 신규 (7단계 + JSON 5필드 + 안전 규칙) | N-3 | 중 |
| 4 | Phase 3 | web-to-markdown SKILL.md 갱신 (호출 인터페이스 + Phase 체인 + 워커 경로) | M-1 | 중 |
| 5 | Phase 3 | agents.md 갱신 (§opal-wtm-agent) | M-2 | 하 |
| 6 | Phase 3 | install-mac.sh 갱신 (cmux-tool chmod + 변경이력) | M-3 | 하 |
| 7 | Phase 3 | docs/PROJECT.md L50 갱신 | M-4 | 하 |
| 8 | Phase 3 | docs/CONVENTIONS.md L21 갱신 | M-5 | 하 |
| 9 | Phase 3 | docs/ARCHITECTURE.md L49·L141·L275 갱신 | M-6 | 하 |
| 10 | Phase 3 | opal-agent-creator SKILL.md L66 갱신 | M-7 | 하 |
| 11 | Phase 4 | `agents/wtm-agent/` 삭제 (잔존 참조 0건 grep 검증 후) | X-1, X-2 | 하 |
| 12 | Phase 5 | 변경이력 행 일괄 검증 (SKILL.md v1.9 / AGENT.md v1.0 / agents.md / install-mac.sh / agent-creator 등) | M-1, M-2, M-3, M-7, N-3 | 하 |

### 핵심 설계

> 인용 포맷: D-6 §2 — `[MUST]` 토큰은 재해석 여지 있는 제약에 적용 / `(→ D-N §N)` 단축 / 풀 경로 + 줄번호 혼용.

#### N-1. `opal/tools/cmux-tool/run.sh` (신규)

**역할**: cmux browser 호출을 캡슐화한 bash 래퍼. URL 모드(A) + 사용자 surface 모드(B/C) 통합. JSON 출력. B/C 모드 cleanup 가드.

**입력 인터페이스**:

```
run.sh <url> [--mode <full|clean|wireframe>] [--wait <ms>]
run.sh --surface <handle> [<url>] [--mode <full|clean|wireframe>] [--wait <ms>]
```

- 인자 1개 = `<url>` → 신규 모드 (A)
- `--surface <handle>` 단독 → 현재 페이지 모드 (B)
- `--surface <handle> <url>` → surface 재사용 + navigate 모드 (C)
- `--mode` 기본 `full` / `--wait` 기본 2000ms / `--wait 0`은 wait 생략

**환경 감지 룰**:

```bash
if [[ -z "${CMUX_SURFACE_ID:-}" ]]; then
  echo '{"ok":false,"error":"not_in_cmux","fallback":"phase3"}' >&2; exit 2
fi
if ! command -v cmux >/dev/null 2>&1; then
  cat >&2 <<'EOF'
{"ok":false,"error":"cmux_not_installed","install_url":"https://cmux.com/","github":"https://github.com/manaflow-ai/cmux","fallback":"phase3"}
EOF
  exit 3
fi
```

→ [MUST] `opal/core/references/opal-harness.md` §1 Guards: "사용자가 명시적으로 '승인', '진행해', '구현해' 등의 실행 허가를 내릴 때까지 코드를 작성하거나 파일을 생성/수정하지 않는다." (본 PLAN 단계에서 코드 작성 안 함, EXECUTE 단계 진입 후 작성)

→ [MUST] `opal/core/references/opal-harness.md` §9: "OPAL 도구는 모두 `~/.opal/tools/{tool-name}/run.sh` 래퍼를 통해 호출한다. 출력은 JSON이며, `\"ok\": false`이면 `\"error\"` 필드를 확인하여 에스컬레이션한다."

**명령 시퀀스 (실측 검증, TASK §대화 결과)**:

| 모드 | 시퀀스 |
|------|--------|
| A (신규) | 1) `OPEN_OUT=$(cmux browser open "$URL" --workspace "$CMUX_WORKSPACE_ID" --focus false)` 2) `SURFACE=$(echo "$OPEN_OUT" \| grep -oE 'surface:[0-9]+' \| head -1)` 3) `cmux browser "$SURFACE" wait --load-state complete --timeout-ms 15000` 4) `sleep "$WAIT_S"` (WAIT_MS/1000, --wait 0 시 생략) 5) `TITLE=$(cmux browser "$SURFACE" get title)` 6) `FINAL_URL=$(cmux browser "$SURFACE" get url)` 7) `HTML=$(cmux browser "$SURFACE" eval --script "document.documentElement.outerHTML")` 8) `cmux browser "$SURFACE" tab close` ← **A 모드에서만 실행** |
| B (현재 페이지) | A의 1·2단계 생략, `SURFACE=$1` (검증: `^surface:[0-9]+$` 또는 UUID 패턴), 3-7단계 실행, **8단계 절대 생략** |
| C (surface + navigate) | `SURFACE=$1` 검증, `cmux browser "$SURFACE" goto "$URL"` 호출, 3-7단계 실행, **8단계 절대 생략** |

→ 명령 사양 출처: [cmux Browser Automation 공식 문서](https://cmux.com/ko/docs/browser-automation) (D-7)

**JSON 출력 스키마**:

```json
{
  "ok": true,
  "method": "cmux",
  "mode": "A|B|C",
  "surface": "surface:N",
  "user_owned": false,
  "title": "...",
  "final_url": "https://...",
  "content": "<html>...</html>",
  "bytes": 315209,
  "wait_ms": 2000
}
```

- 실패 시: `{"ok": false, "error": "<code>", "detail": "...", "fallback": "phase3"}`
- `user_owned: true` (B/C 모드)일 때 호출자가 산출물 보고에 "사용자 세션 기반 추출 — 민감 정보 포함 가능" 안내를 부착하도록 시그널 제공 (→ TASK R-13)

**[안전 가드 3계층 책임 분리]** (TASK §R-13 AC 충족 구조):

| 계층 | 책임 위치 | 산출물 | 책임 내용 |
|------|----------|--------|----------|
| 1차 시그널 생성 | `opal/tools/cmux-tool/run.sh` (N-1) | JSON 출력 | B 모드(`--surface` 단독) / C 모드(`--surface` + URL) 진입 시 `user_owned: true` 필드를 출력 JSON에 포함. A 모드는 `user_owned: false`. |
| 2차 가공 보고 | `opal/agents/opal-wtm-agent/AGENT.md` (N-3) | 결과 JSON 반환 | `user_owned: true` 수신 시 `summary` 필드에 "사용자 세션 기반 추출 — 민감 정보 포함 가능, 외부 공유 시 검토 필요" 안내 문구를 자동 부착. 저장 경로(`artifact_path`)도 함께 명시. 사용자 surface 핸들 미명시 시 B/C 모드 진입 거부(`status: blocked` + blocker 메시지). |
| 3차 사용자 노출 | `skills/web-to-markdown/SKILL.md` §결과 보고 형식 (M-1) | 사용자 stdout 출력 | B/C 모드 실행 결과를 사용자에게 보고할 때 경고 텍스트(2차 계층에서 부착된 `summary`)를 그대로 노출 의무. 결과 출력 형식 섹션에 "B/C 모드 안내" 명시. |

→ [MUST] `tasks/002-260512-opp-wtm-opal-standardization/TASK.md` §R-13 AC: "B/C 모드 실행 결과 보고에 저장 경로 명시 / '사용자 세션 기반 추출 — 민감 정보 포함 가능, 외부 공유 시 검토 필요' 안내 포함 / 사용자 surface 핸들이 명시되지 않은 경우 B/C 모드 진입 거부"

> 본 3계층 분리는 단일 파일에 책임 집중 시 SKILL.md 또는 AGENT.md 한 곳만 수정해도 누락 발생하는 위험을 방지한다. 각 계층은 §3 Step 1(cmux-tool)·Step 3(opal-wtm-agent)·Step 4(SKILL.md) 완료 기준에 개별 검증 항목으로 반영된다.

**[MUST] 안전 가드 (스크립트 정적 검증으로 보장)**:

→ [MUST] `tasks/002-260512-opp-wtm-opal-standardization/TASK.md` §제약 조건: "사용자 surface cleanup 절대 금지: B/C 모드에서 `tab close` 호출 안 함 — 스크립트 정적 검증으로 보장"

구현 패턴:

```bash
# A 모드에서만 cleanup 분기 진입
case "$MODE" in
  A) cmux browser "$SURFACE" tab close ;;
  B|C) ;;  # cleanup 금지
esac
```

검증: `grep -cE '"tab close"|tab close' run.sh` 결과가 정확히 1개 (A 분기에만 존재).

**의존성 가드**: D-12 `playwright-tool/run.sh` 패턴 차용 — 의존성 미충족 시 JSON 에러로 stderr 출력 후 `exit N` (호출자가 폴백 분기 가능).

#### N-2. `opal/tools/cmux-tool/README.md` (신규)

**구성**:

1. 개요 (1줄) — "cmux browser 자동화 래퍼: URL 추출 + 사용자 surface 재사용"
2. 요구사항 — cmux 0.64.3+, `$CMUX_SURFACE_ID` 환경
3. 사용법 — 3모드 명령 예시 + 옵션 표
4. 출력 스키마 — JSON 필드 표
5. 에러 코드 — `not_in_cmux`, `cmux_not_installed`, `invalid_surface`, `goto_failed`, `eval_failed`
6. 안전 가드 — B/C 모드 cleanup 절대 금지 (→ TASK §확정 방향 §8)

→ 도구별 README는 `playwright-tool`, `xlsx-tool`, `state-tool` 등 기존 도구에서 통용되는 자가설명 관행을 따른다 (선택 산출물).

#### N-3. `opal/agents/opal-wtm-agent/AGENT.md` (신규)

**frontmatter**:

```yaml
---
name: opal-wtm-agent
description: |
  web-to-markdown 스킬의 워커 에이전트.
  단일 URL 또는 사용자 cmux surface를 받아 Phase 1(WebFetch) → Phase 2(cmux, 조건부) → Phase 3(playwright-tool CLI) 폴백 전략으로 웹 페이지를 마크다운으로 변환한다. 복수 URL 병렬 처리 시 오케스트레이터가 URL별로 디스패치한다.
model: light
color: green
icon: "🌐"
---
```

→ [MUST] `tasks/002-260512-opp-wtm-opal-standardization/TASK.md` §R-1 AC: "frontmatter `name: opal-wtm-agent` + `model: light` / 실행 프로세스가 opal-task-agent와 동일 7단계 구조 / 결과 반환 JSON 5필드(`artifact_path`, `summary`, `status`, `blockers`, `changed_files`) 명시"

**실행 프로세스 7단계** (D-10 §실행 프로세스 패턴 차용 + 도메인 특화):

1. 오케스트레이터 프롬프트에서 입력 확인 (`url` 또는 `--surface <handle>`, `save_path`, `mode`, `--wait`).
2. 스킬 SKILL.md(`skills/web-to-markdown/SKILL.md`)를 Read.
3. 프로젝트 컨텍스트 로드 (태스크 폴더에서 PROJECT.md 추론, 없으면 스킵).
4. 모드 결정: `--surface` 명시 → B 또는 C / URL만 → A.
5. Phase 폴백 실행: 1(WebFetch) → 2(cmux 조건부) → 3(playwright-tool CLI).
6. 산출물 생성 + 저장 (slug 규칙은 SKILL.md §저장 경로 적용).
7. 결과 JSON 반환 (5필드 + `method`, `mode`, `user_owned`).

**결과 반환 형식** (SSOT — 본 스키마가 단일 진실 원천):

```json
{
  "artifact_path": "{save_path}/{slug}.md",
  "summary": "Phase 2(cmux, mode=C) 추출 — 315KB, 사용자 세션 기반",
  "status": "completed",
  "blockers": [],
  "changed_files": ["{save_path}/{slug}.md"],
  "method": "cmux|webfetch|playwright-cli",
  "mode": "A|B|C|null",
  "user_owned": false
}
```

**필드 구성 (총 8필드 — SSOT)**:

| 구분 | 필드 | 출처 | 비고 |
|------|------|------|------|
| 표준 5필드 | `artifact_path`, `summary`, `status`, `blockers`, `changed_files` | D-10 opal-task-agent §결과 반환 형식 L29-38 | OPAL 워커 표준, TASK §R-1 AC와 일치 |
| 도메인 특화 3필드 | `method` | wtm-agent 도메인 확장 | Phase 폴백 시 실제 사용된 백엔드 시그널 (`cmux`/`webfetch`/`playwright-cli`) |
| 도메인 특화 3필드 | `mode` | wtm-agent 도메인 확장 | 사용자 surface 모드 (`A`/`B`/`C`/`null`) — `null`은 surface 모드 아닐 때 |
| 도메인 특화 3필드 | `user_owned` | wtm-agent 도메인 확장 | B/C 모드 안전 가드 시그널 — `true`이면 호출자가 민감 정보 경고 부착 (→ TASK §R-13) |

> **[SSOT 일관성]** 본 8필드 스키마는 다음 3 산출물 모두에서 동일하게 참조한다:
> - 본 PLAN.md §2 N-3 핵심 설계 (현 위치, SSOT)
> - `opal/agents/opal-wtm-agent/AGENT.md` §결과 반환 형식 (구현 산출물)
> - `opal/core/references/agents.md` §opal-wtm-agent §출력 (레지스트리, M-2)
> - `skills/web-to-markdown/SKILL.md` §결과 보고 형식 (스킬 호출 인터페이스, M-1)
>
> EXECUTE 단계에서 8필드 외 추가/삭제 시 본 SSOT 행을 먼저 갱신 후 4 산출물 동시 정합 갱신해야 한다.

→ D-10 §결과 반환 형식 L29-38 표준 5필드 + 도메인 확장 3필드 (`method`/`mode`/`user_owned`).
→ TASK §R-1 AC ("결과 반환 JSON 5필드") + TASK §R-10 AC ("출력 JSON 형식 명시") 동시 충족.

**[MUST] 안전 규칙**:

→ [MUST] `tasks/002-260512-opp-wtm-opal-standardization/TASK.md` §R-13 AC: "B/C 모드 실행 결과 보고에 저장 경로 명시 / '사용자 세션 기반 추출 — 민감 정보 포함 가능, 외부 공유 시 검토 필요' 안내 포함 / 사용자 surface 핸들이 명시되지 않은 경우 B/C 모드 진입 거부"

규칙 본문:

- B/C 모드 결과 보고에 "사용자 세션 기반 추출 — 민감 정보 포함 가능, 외부 공유 시 검토 필요" 경고문 + 저장 경로(`artifact_path`)를 명시. **구현 방식**: cmux-tool 출력의 `user_owned: true` 수신 시 본 에이전트가 반환 JSON의 `summary` 필드에 경고 텍스트를 자동 부착(2차 계층, §2 N-1 [안전 가드 3계층] 참조).
- 사용자 surface 핸들 미명시 시 B/C 모드 진입 거부 — 오케스트레이터 입력 검증에서 `mode=B|C`이지만 `--surface` 인자 없으면 `status: blocked` + blocker 메시지 즉시 반환.
- 사용자 surface에 대해서는 어떤 경우에도 `cmux browser <surface> tab close` 호출 안 함 — cmux-tool run.sh가 1차 차단, 본 에이전트는 2차 검증.
- SKILL.md §결과 보고 형식이 본 에이전트의 `summary` 텍스트를 사용자에게 그대로 노출 (3차 계층).

**행동 규칙** (D-10 §행동 규칙 패턴):

- 스킬 SKILL.md 프로세스를 정확히 따른다.
- QA/Test 에이전트를 호출하지 않는다 — 오케스트레이터 책임.
- 블로커 발생 시 즉시 `status: blocked` 반환.
- STATE.md 갱신 의무는 없음 (web-to-markdown은 파이프라인 단계가 아닌 도구성 워커).

**변경이력 표** (v1.0 행, W-3 포맷 통일 — `YYYY-MM-DD HH:mm KST` + 태스크 토큰 `(002)`):

```markdown
| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-05-12 HH:mm KST | 초기 작성 — agents/wtm-agent/ 표준화 이전 + cmux Phase 2 + 사용자 surface 3모드 + JSON 5필드 (002) |
```

> EXECUTE 단계에서 `HH:mm`은 실제 작성 시각으로 치환 (예: `18:30 KST`). 본 태스크 모든 변경이력 행은 동일 포맷 (§3 Step 12 일괄 검증).

#### M-1. `skills/web-to-markdown/SKILL.md` 갱신

**(a) §호출 인터페이스 — L22-30 갱신**:

```markdown
//wtm {url}                                # 단일 URL, full 모드, Phase 1→2(cmux 조건부)→3
//wtm {url1} {url2} {url3}                 # 복수 URL, 병렬
//wtm --browser {url}                      # Phase 1 생략, cmux→playwright 폴백
//wtm --surface <handle>                   # 현재 페이지(B 모드) — navigate 안 함, cleanup 금지
//wtm --surface <handle> {url}             # surface 재사용 + navigate(C 모드)
//wtm --wait <ms> {url}                    # wait ms 지정 (기본 2000, 0=생략)
//wtm --clean {url}                        # 본문만
//wtm --wireframe {url}                    # 와이어프레임
```

→ TASK §R-8 AC + §확정 방향 §9

**(b) §실행 흐름 — L82-104 재구성**:

```
URL/--surface 입력
  │
  ├─ [browser 모드 또는 --surface 명시] → Phase 1 생략, Phase 2(cmux)로 이동
  │
  ├─ Phase 1: WebFetch (단일 URL만)
  │     ├─ 성공 → MD 정제 → 저장
  │     └─ 실패 → Phase 2
  │
  ├─ Phase 2: cmux (조건부) — $CMUX_SURFACE_ID + cmux 설치 모두 충족 시만
  │     ├─ run.sh 호출 (모드 A/B/C)
  │     ├─ {"ok": true} → content 정제 → 저장
  │     └─ {"ok": false, "fallback": "phase3"} → Phase 3
  │
  └─ Phase 3: playwright-tool CLI
        ├─ run.sh {url} --mode {mode} 호출
        ├─ {"ok": true} → content 정제 → 저장
        └─ run.sh 미설치 → 설치 안내 후 중단
```

→ TASK §R-5 AC: "흐름도에 3단계 명시 / 각 Phase별 성공/실패 판정 기준 명시 / `--browser` 모드 분기도 cmux/playwright 우선순위 일치"

**(c) §Phase 2: cmux (신규 섹션)**:

- 환경 감지 룰: `[[ -n "$CMUX_SURFACE_ID" ]] && command -v cmux >/dev/null 2>&1`
- 호출: `bash ~/.opal/tools/cmux-tool/run.sh <url> [--surface <handle>] [--mode <m>] [--wait <ms>]`
- JSON 출력 파싱 + 정제 규칙은 §콘텐츠 추출 및 MD 정제 섹션 재사용
- 미설치 안내: cmux 공식 사이트 + GitHub 링크 (→ D-7, D-8)
- 환경 미충족 또는 `cmux_not_installed` → Phase 3로 폴백 (→ TASK §R-4 AC)

**(d) §Phase 3: playwright-tool CLI** (현 §Phase 2 → §Phase 3 재번호):

- 진입 조건 갱신: "Phase 1 실패 후 cmux 환경 미충족 또는 cmux Phase 실패 시"
- 나머지 본문 유지

**(e) §의존성 표 — L492-511 갱신**:

| 도구 | 필요 시점 | 미설치 시 동작 |
|------|----------|--------------|
| cmux 0.64.3+ (선택) | $CMUX_SURFACE_ID 환경에서 Phase 2 진입 | 안내 출력 후 Phase 3로 폴백 |
| playwright-tool CLI | Phase 3 진입 | 안내 후 중단 |

→ TASK §R-8 AC

**(f) §복수 URL 처리 §워커 에이전트 — L391-395 갱신**:

- 에이전트 이름: `opal-wtm-agent`
- 탐색 경로: `1) {프로젝트}/.opal/agents/opal-wtm-agent/AGENT.md` / `2) ~/.opal/agents/opal-wtm-agent/AGENT.md`
- §추출 방식 표기 (L348, L218, L74) — `WebFetch | cmux | playwright-tool CLI` 3종 명시

**(g-prev) §결과 보고 형식 — 신규 또는 갱신**:

- B/C 모드(사용자 surface) 실행 결과를 사용자에게 보고할 때, opal-wtm-agent 반환 JSON의 `summary` 필드(2차 계층에서 자동 부착된 "사용자 세션 기반 추출 — 민감 정보 포함 가능, 외부 공유 시 검토 필요" 안내 포함)를 그대로 stdout/응답에 노출한다 (3차 계층).
- 보고 형식 예시:
  ```
  ✅ web-to-markdown 완료 (Phase 2 cmux, mode=C)
  📁 저장: {artifact_path}
  ⚠️  사용자 세션 기반 추출 — 민감 정보 포함 가능, 외부 공유 시 검토 필요
  ```
- A 모드(신규 surface 또는 일반 URL)에서는 경고문 노출 안 함 (`user_owned: false`).

→ [MUST] `tasks/002-260512-opp-wtm-opal-standardization/TASK.md` §R-13 AC + §2 N-1 [안전 가드 3계층] 3차 계층 책임.

**(g) §변경이력 v1.9 행 추가** (W-3 포맷 통일 — `YYYY-MM-DD HH:mm KST` + 태스크 토큰 `(002)`):

```markdown
| v1.9 | 2026-05-12 HH:mm KST | 워커 에이전트 OPAL 표준화 (wtm-agent → opal-wtm-agent) + Phase 2 cmux 신설 (Phase 2 playwright → Phase 3 재번호) + `--surface <handle>` 3모드(A/B/C) + `--wait <ms>` 옵션 + Crawl4AI 잔존 참조 제거 (002) |
```

→ [MUST] `.opal/AGENT.md` §업무 수행 지침: "스킬·에이전트·참조 문서 수정 시 변경이력 표에 행을 추가한다 (일시 KST + 태스크 번호 포함)" (→ D-13)

#### M-2. `opal/core/references/agents.md` §wtm-agent 갱신

**현행 (D-2 L214-221)**:

```markdown
## web-to-markdown 에이전트

### wtm-agent

- **역할**: web-to-markdown 에이전트 — 단일 URL을 받아 Phase 1(WebFetch) → Phase 2(Crawl4AI) 폴백 전략으로 웹 페이지를 마크다운으로 변환
- **호출 시점**: web-to-markdown 스킬에서 URL별로 오케스트레이터가 디스패치
- **입력**: url, save_path, mode (full/clean)
- **출력**: 마크다운 파일 (save_path에 저장)
```

**개정**:

```markdown
## web-to-markdown 에이전트

### opal-wtm-agent

- **역할**: web-to-markdown 스킬 워커 — Phase 1(WebFetch) → Phase 2(cmux, 조건부) → Phase 3(playwright-tool CLI) 폴백으로 단일 URL 또는 사용자 cmux surface(B/C 모드)를 마크다운으로 변환
- **호출 시점**: web-to-markdown 스킬에서 URL/surface별로 오케스트레이터가 디스패치
- **단계**: 도구성 워커 (파이프라인 단계 외)
- **영역**: 공통
- **model**: light
- **입력**: `url | --surface <handle> [url]`, `save_path`, `mode (full|clean|wireframe)`, `--wait <ms>` (기본 2000)
- **출력**: 마크다운 파일(`{save_path}/{slug}.md`) + JSON 결과 (총 8필드, 본 PLAN §2 N-3 SSOT 스키마와 동일):
  ```json
  {
    "artifact_path": "...",
    "summary": "...",
    "status": "completed",
    "blockers": [],
    "changed_files": ["..."],
    "method": "cmux|webfetch|playwright-cli",
    "mode": "A|B|C|null",
    "user_owned": false
  }
  ```
- **에이전트 경로**: `opal/agents/opal-wtm-agent/`
```

→ TASK §R-10 AC
→ JSON 출력 형식은 본 PLAN §2 N-3 §결과 반환 형식 SSOT를 단일 참조원으로 사용 (8필드 = 표준 5 + 도메인 3). 본 M-2 항목은 SSOT의 사본이며, 갱신 시 SSOT 우선 변경 후 동기화.

#### M-3. `scripts/install-mac.sh` 갱신

**(a) 변경이력 헤더 v2.2 행 추가** (D-9 L7-18 패턴 + W-3 포맷 통일 — `YYYY-MM-DD HH:mm KST` + `(002)`):

```
#   v2.2 2026-05-12 HH:mm KST: cmux-tool 등록 + opal-wtm-agent 자동 어댑터 — install_opal()의 tools/ 처리 직후 cmux-tool/run.sh chmod +x 추가 (002)
```

> install-mac.sh는 변경이력이 마크다운 표가 아닌 헤더 주석 형식이므로 동일한 시각 포맷(`YYYY-MM-DD HH:mm KST`)을 헤더 주석에 그대로 적용한다.

**(b) tools/ 처리 후 chmod +x 블록 추가** (D-9 L819-830 패턴 차용):

```bash
# ── cmux-tool 실행 권한 ──
local cmux_run="$opal_home/tools/cmux-tool/run.sh"
if [[ -f "$cmux_run" ]]; then
    chmod +x "$cmux_run"
    success "cmux-tool run.sh 실행 권한 설정"
    # cmux 의존성 안내 (정보성 — 설치 강제 없음)
    if ! command -v cmux &>/dev/null; then
        info "cmux 미감지 — Phase 2(cmux) 사용 시 https://cmux.com/ 또는 https://github.com/manaflow-ai/cmux 에서 설치 필요"
    fi
fi
```

→ TASK §R-11 AC: "install-mac.sh가 `opal/tools/cmux-tool/` → `~/.opal/tools/cmux-tool/` 복사 / 실행 권한 부여(`chmod +x`) / 정상 설치 시 cmux 의존성 안내 메시지 출력 / 재실행 시 멱등(idempotent)"

> 디렉토리 자체 복사는 D-9 L815 `install_dir "$opal_dir/tools" "$opal_home/tools" "OPAL 도구"`가 `opal/tools/` 하위 전체를 자동 흡수하므로 별도 코드 추가 불필요 (멱등성 자동 확보).
> 마찬가지로 N-3 `opal/agents/opal-wtm-agent/`도 D-9 L780-789 `opal/agents/*` 루프가 자동 흡수.

**(c) 멱등성 검증**: 위 chmod 블록은 `if [[ -f ... ]]`로 가드되어 재실행 안전.

#### M-4. `docs/PROJECT.md` L50 갱신

**현행** (D-14 L50): `agents/` 행 예시에 `wtm-agent` 표기.

**개정 옵션**:
- 옵션 (i): 행 예시에서 `wtm-agent` 제거 + 비고에 "현재 비어있음 (모든 워커 에이전트는 `opal/agents/`로 통합)" 명시
- 옵션 (ii): `agents/` 행 전체를 보존하되 예시에 다른 향후 범용 에이전트 후보 placeholder 표기

→ EXECUTE 단계에서 옵션 (i)를 적용한다 (TASK §R-2 — 잔존 참조 0건 목표 + 현실적으로 `agents/` 디렉토리가 빈 상태 됨).

#### M-5. `docs/CONVENTIONS.md` L21 갱신

**현행** (D-15 L21): `- 범용 에이전트 폴더: \`agents/{agent-name}/\` — \`wtm-agent\` (OPAL 무관)`

**개정**: `- 범용 에이전트 폴더: \`agents/{agent-name}/\` — 현재 비어있음 (OPAL 표준 워커는 \`opal/agents/opal-*-agent/\` 사용)`

→ TASK §R-2 AC + D-15

#### M-6. `docs/ARCHITECTURE.md` 갱신

| 줄 | 현행 | 개정 |
|----|------|------|
| L49 | `│  │  └─ wtm-agent: 웹→마크다운 변환                    │   │` | `│  │  └─ opal-wtm-agent: 웹→마크다운 변환                │   │` |
| L141 | `\| wtm-agent \| light \| web-to-markdown 병렬 처리 \|` | `\| opal-wtm-agent \| light \| web-to-markdown 워커 (Phase 1 WebFetch → Phase 2 cmux → Phase 3 playwright-tool CLI) \|` |
| L274-275 | `├── agents/                              범용 에이전트 (OPAL 무관)` / `│   └── wtm-agent/                       웹→마크다운 에이전트` | `├── agents/                              범용 에이전트 슬롯 (현재 비어있음)` (다음 행 삭제) + L264 인근 `opal/agents/` 트리뷰 섹션에 `│   └── opal-wtm-agent/                  웹→마크다운 워커` 추가 |

→ TASK §R-2 AC + D-16

#### M-7. `opal/skills/opal-agent-creator/SKILL.md` L66 갱신

**현행** (D-17 L66): `1. **name** -- kebab-case, \`{워크플로우}-{역할}\` 패턴 권장 (예: \`op-task-qa\`, \`wtm-agent\`)`

**개정**: `1. **name** -- kebab-case, \`{워크플로우}-{역할}\` 패턴 권장 (예: \`op-task-qa\`, \`opal-wtm-agent\`)`

→ TASK §R-2 AC + D-17

---

## 3. 실행 체크리스트

> 총 12개 Step | Phase 5개

| Phase | Step | 실행 | 비고 |
|-------|------|------|------|
| 1     | 1, 2 | 병렬 | cmux-tool 도구 신규 (독립 파일) |
| 2     | 3 | 순차 | opal-wtm-agent — Phase 1의 cmux-tool 호출 인터페이스 안정화 의존 |
| 3     | 4, 5, 6, 7, 8, 9, 10 | 병렬 | SSOT/레지스트리/install/docs/agent-creator — 서로 다른 파일, Phase 2 완료 후 일제히 진행 |
| 4     | 11 | 순차 | `agents/wtm-agent/` 삭제 — Phase 3의 잔존 참조 갱신 완료 후 안전하게 제거 |
| 5     | 12 | 순차 | 변경이력 일괄 검증 — 모든 수정 완료 후 마지막 검수 |

### Step 1: cmux-tool run.sh 신규 작성

- [x] 완료
- **파일**: `opal/tools/cmux-tool/run.sh`
- **작업 내용**: 
  - shebang `#!/bin/bash` + `set -euo pipefail`
  - 인자 파싱: `<url>`, `--surface <handle>`, `--mode <m>`, `--wait <ms>`
  - 환경 감지: `$CMUX_SURFACE_ID` + `command -v cmux` 2단 가드 (미충족 시 `{"ok":false,"error":"...","fallback":"phase3"}`)
  - 모드 결정: A (URL만) / B (--surface 단독) / C (--surface + URL)
  - A 모드: `cmux browser open` → surface 파싱 → wait → sleep → title/url/eval → tab close
  - B 모드: 입력 surface 패턴 검증 → wait → sleep → title/url/eval (cleanup 없음)
  - C 모드: 입력 surface 검증 → goto → wait → sleep → title/url/eval (cleanup 없음)
  - JSON 출력 (stdout) + 에러 JSON (stderr) + 종료 코드 (0/2/3/4...)
  - `chmod +x` 부여
- **완료 기준**: 
  - 파일 존재 + 실행 권한
  - 모든 분기 정적 검증 통과 (`grep -cE 'tab close' run.sh` = 1, A 분기 내부에만)
  - `--help` 또는 인자 없음 호출 시 사용법 JSON 반환
  - **`user_owned` 필드 1차 시그널 검증** (§2 N-1 [안전 가드 3계층] 1차 계층): A 모드 출력 JSON에 `"user_owned": false`, B/C 모드 출력 JSON에 `"user_owned": true` 포함
- **테스트**: 
  - `bash run.sh` → `{"ok":false,"error":"usage",...}` 출력 확인
  - cmux 환경 외부에서 `bash run.sh https://example.com` → `{"ok":false,"error":"not_in_cmux"}` + 종료 2
  - (cmux 환경 내) `bash run.sh https://naver.com` → `{"ok":true,"method":"cmux","mode":"A","user_owned":false,...}` + 종료 0
  - (cmux 환경 내) `bash run.sh --surface surface:3` → mode B, `user_owned:true`, cleanup 미호출 확인
  - (cmux 환경 내) `bash run.sh --surface surface:3 https://google.com` → mode C, `user_owned:true`, goto 호출 + cleanup 미호출 확인
  - `bash run.sh --wait 0 https://example.com` → sleep 단계 생략 확인
  - 정적 검증: `grep -cE '"user_owned"' run.sh` ≥ 2 (A 분기 false + B/C 분기 true)
- **의존**: 없음

### Step 2: cmux-tool README.md 신규 작성

- [x] 완료
- **파일**: `opal/tools/cmux-tool/README.md`
- **작업 내용**: 개요 / 요구사항 / 사용법 / 출력 스키마 / 에러 코드 / 안전 가드 6개 섹션
- **완료 기준**: 6개 섹션 모두 존재 + 3모드 예시 + JSON 필드 표 포함
- **테스트**: 사용자가 README만 보고 cmux-tool 호출 가능 (자가설명)
- **의존**: 없음

### Step 3: opal-wtm-agent AGENT.md 신규 작성

- [x] 완료
- **파일**: `opal/agents/opal-wtm-agent/AGENT.md`
- **작업 내용**:
  - frontmatter: `name: opal-wtm-agent`, `model: light`, `color: green`, `icon: 🌐`, description (Phase 1→2(cmux)→3 명시)
  - §실행 프로세스 7단계 (D-10 패턴)
  - §결과 반환 형식 (JSON 5필드 + `method`/`mode`/`user_owned`)
  - §안전 규칙 [MUST] (사용자 surface cleanup 금지 + 민감 정보 안내 + 미명시 거부)
  - §행동 규칙 (스킬 정확히 따름 / QA 호출 금지 / 블로커 즉시 반환)
  - §변경이력 v1.0 행 (2026-05-12 KST + 002)
- **완료 기준**: 
  - 파일 존재
  - frontmatter 5필드 명시
  - 7단계 프로세스 모두 기재
  - JSON 5+3 필드 명시 (§2 N-3 SSOT 8필드와 일치)
  - [MUST] 토큰 1건 이상 (안전 규칙)
  - **2차 가공 보고 검증** (§2 N-1 [안전 가드 3계층] 2차 계층): 안전 규칙 섹션에 "`user_owned: true` 수신 시 `summary`에 '사용자 세션 기반 추출 — 민감 정보 포함 가능, 외부 공유 시 검토 필요' 자동 부착" 명시
  - **B/C 모드 진입 거부 검증**: `--surface` 인자 없이 mode=B|C 진입 시 `status: blocked` 반환 규칙 명시
  - 변경이력 v1.0 행 존재 (W-3 포맷 통일 기준 충족 — 아래 D-6 보완 참조)
- **테스트**: 
  - `head -10 AGENT.md`로 frontmatter 확인
  - `grep -c "MUST" AGENT.md` ≥ 1
  - `grep -c "v1.0" AGENT.md` = 1
  - `grep -c "민감 정보 포함 가능" AGENT.md` ≥ 1
  - `grep -c "user_owned" AGENT.md` ≥ 1
- **의존**: Step 1 (cmux-tool 인터페이스 안정화)

### Step 4: web-to-markdown SKILL.md 갱신

- [x] 완료
- **파일**: `skills/web-to-markdown/SKILL.md`
- **작업 내용**: 핵심 설계 M-1 (a)~(g-prev)~(g) 8개 변경 일괄 적용
- **완료 기준**: 
  - §호출 인터페이스에 `--surface`, `--wait` 3개 예시 추가
  - §실행 흐름이 Phase 1→2(cmux)→3 3단계 다이어그램
  - §Phase 2 cmux 사양 섹션 신규 (환경 감지 + 호출 + 미설치 안내)
  - §Phase 3 playwright-tool CLI (현 §Phase 2 → §Phase 3 재번호)
  - §의존성 표에 cmux(선택) 행 추가
  - §복수 URL §워커 에이전트의 이름/탐색 경로가 `opal-wtm-agent`
  - 본문 내 `Crawl4AI` 검색 시 변경이력 행을 제외한 잔존 0건 (`grep -c Crawl4AI` ≤ 변경이력 행 수)
  - **3차 사용자 노출 검증** (§2 N-1 [안전 가드 3계층] 3차 계층 + M-1 (g-prev)): §결과 보고 형식 섹션에 "B/C 모드 결과 출력 시 `summary` 경고문 그대로 노출 + 저장 경로(`artifact_path`) 명시" 의무 명시
  - §변경이력 v1.9 행 추가 (W-3 포맷 통일 기준 — `2026-05-12 HH:MM KST` + 태스크 002, 아래 D-6 보완 참조)
- **테스트**: 
  - `grep -c "opal-wtm-agent" skills/web-to-markdown/SKILL.md` ≥ 3
  - `grep -c "wtm-agent" skills/web-to-markdown/SKILL.md` = (변경이력 행만)
  - `grep -c "Phase 3" skills/web-to-markdown/SKILL.md` ≥ 2
  - `grep -c "v1.9" skills/web-to-markdown/SKILL.md` ≥ 1
  - `grep -c "민감 정보 포함 가능" skills/web-to-markdown/SKILL.md` ≥ 1 (3차 계층 — 결과 보고 형식 섹션)
- **의존**: Step 1, Step 3 (호출 인터페이스 + 워커 이름 안정화)

### Step 5: opal/core/references/agents.md §opal-wtm-agent 갱신

- [x] 완료
- **파일**: `opal/core/references/agents.md`
- **작업 내용**: §wtm-agent 섹션 헤더 → §opal-wtm-agent로 변경 + 본문 7항목(역할/호출 시점/단계/영역/model/입력/출력/에이전트 경로) 재작성. `Crawl4AI` 토큰 제거.
- **완료 기준**: 
  - L216 헤더가 `### opal-wtm-agent`
  - 본문 7항목 모두 존재
  - **출력 JSON 필드 표기가 본 PLAN §2 N-3 §결과 반환 형식 SSOT 8필드와 일치** (표준 5필드 `artifact_path`/`summary`/`status`/`blockers`/`changed_files` + 도메인 3필드 `method`/`mode`/`user_owned`)
  - 파일 내 `Crawl4AI` 검색 결과 0건 (변경이력 행은 본 문서에 없으므로 완전 0건)
  - 파일 내 `wtm-agent` 검색 결과 = `opal-wtm-agent` 일치 행만
- **테스트**: 
  - `grep -c "opal-wtm-agent" opal/core/references/agents.md` ≥ 2
  - `grep "Crawl4AI" opal/core/references/agents.md` → 매치 없음
  - JSON 8필드 모두 매치: `for f in artifact_path summary status blockers changed_files method mode user_owned; do grep -c "$f" opal/core/references/agents.md; done` → 모두 ≥ 1
- **의존**: Step 3 (AGENT.md 신규 — 등록 정보 SSOT 일관성)

→ **SSOT 일관성 보장**: 본 Step의 출력 JSON은 PLAN §2 N-3 SSOT 스키마의 사본이며, Step 3(AGENT.md)·Step 4(SKILL.md §결과 보고 형식)와 동일 8필드를 유지한다.

### Step 6: scripts/install-mac.sh 갱신

- [x] 완료
- **파일**: `scripts/install-mac.sh`
- **작업 내용**: 핵심 설계 M-3 (a)~(c) — 변경이력 v2.2 행 + cmux-tool chmod 블록 + 정보성 안내
- **완료 기준**: 
  - L7-18 변경이력에 v2.2 행 (2026-05-12 KST + 002)
  - tools/ 처리 직후(현 L823 인근) cmux-tool chmod 블록 존재
  - `bash -n scripts/install-mac.sh` 문법 통과
  - 멱등성: 두 번 연속 실행해도 동일 결과 (chmod는 멱등, 변경이력은 코드 외부)
- **테스트**: 
  - `grep -c "cmux-tool" scripts/install-mac.sh` ≥ 2 (chmod + info)
  - `grep "v2.2" scripts/install-mac.sh` 매치 1건
  - `bash -n scripts/install-mac.sh` exit 0
- **의존**: Step 1 (cmux-tool/run.sh 존재 — install 대상 파일 보장)

### Step 7: docs/PROJECT.md L50 갱신

- [x] 완료
- **파일**: `docs/PROJECT.md`
- **작업 내용**: L50 예시에서 `wtm-agent` 토큰 제거 + 비고에 "현재 비어있음 (모든 워커 에이전트는 `opal/agents/`로 통합)" 명시
- **완료 기준**: L50 행에 `wtm-agent` 토큰 없음
- **테스트**: `grep -n "wtm-agent" docs/PROJECT.md` 매치 없음
- **의존**: 없음 (다른 파일과 독립)

### Step 8: docs/CONVENTIONS.md L21 갱신

- [x] 완료
- **파일**: `docs/CONVENTIONS.md`
- **작업 내용**: L21 `wtm-agent (OPAL 무관)` → `현재 비어있음 (OPAL 표준 워커는 opal/agents/opal-*-agent/ 사용)`
- **완료 기준**: L21 행에 `wtm-agent` 토큰 없음
- **테스트**: `grep -n "wtm-agent" docs/CONVENTIONS.md` 매치 없음
- **의존**: 없음

### Step 9: docs/ARCHITECTURE.md 3곳 갱신

- [x] 완료
- **파일**: `docs/ARCHITECTURE.md`
- **작업 내용**: 
  - L49 다이어그램: `wtm-agent` → `opal-wtm-agent`
  - L141 표: `wtm-agent` 행 → `opal-wtm-agent` 행 (역할 문구 갱신)
  - L274-275 트리뷰: `agents/` 하위 `wtm-agent/` 행 제거 + 상단 `opal/agents/` 섹션에 `opal-wtm-agent/` 추가
- **완료 기준**: 
  - `grep -c "wtm-agent" docs/ARCHITECTURE.md` = `opal-wtm-agent` 일치 행만 (3건)
  - 잔존 `wtm-agent` (접두사 없음) = 0건
- **테스트**: 
  - `grep -nE "(^|[^-])wtm-agent" docs/ARCHITECTURE.md` 매치 없음 (단어 경계 검증)
  - `grep -c "opal-wtm-agent" docs/ARCHITECTURE.md` ≥ 3
- **의존**: 없음 (docs/backup/은 보존 — 백업이므로 변경 대상 외)

### Step 10: opal/skills/opal-agent-creator/SKILL.md L66 갱신

- [x] 완료
- **파일**: `opal/skills/opal-agent-creator/SKILL.md`
- **작업 내용**: L66 예시 `wtm-agent` → `opal-wtm-agent`
- **완료 기준**: `grep -n "wtm-agent" opal/skills/opal-agent-creator/SKILL.md`에서 `opal-wtm-agent`만 매치
- **테스트**: `grep -cE "(^|[^-])wtm-agent" opal/skills/opal-agent-creator/SKILL.md` = 0
- **의존**: 없음

### Step 11: agents/wtm-agent/ 삭제

- [x] 완료
- **파일**: `agents/wtm-agent/AGENT.md`, `agents/wtm-agent/`
- **작업 내용**: 
  - 사전 검증 (1) — wtm-agent 경로 잔존 참조 0건:
    ```bash
    grep -rln "agents/wtm-agent" --include="*.md" \
      --exclude-dir=tasks --exclude-dir=docs/backup .
    # 기대 결과: 0건
    ```
  - 사전 검증 (2) — Crawl4AI 잔존 참조 0건 (TASK §R-9 AC 충족):
    ```bash
    grep -rln "Crawl4AI" --include="*.md" \
      --exclude-dir=tasks --exclude-dir=docs/backup .
    # 기대 결과: web-to-markdown 관련 잔존 0건
    # 예외 허용: SKILL.md 변경이력 v1.1/v1.2/v1.4 행만 (Phase 2 백엔드 교체 이력 보존)
    ```
  - 사전 검증 (3) — `opal/agents/opal-wtm-agent/AGENT.md` 본문에 `Crawl4AI` 토큰 0건 (신규 워커는 playwright-tool CLI 기반)
  - `rm agents/wtm-agent/AGENT.md`
  - `rmdir agents/wtm-agent` (빈 디렉토리)
- **완료 기준**: 
  - `agents/wtm-agent/` 존재하지 않음
  - 전체 코드베이스 `grep -rln "agents/wtm-agent" --include="*.md" --exclude-dir=tasks --exclude-dir=docs/backup` 결과 0건
  - 전체 코드베이스 잔존 `(^|[^-])wtm-agent` (단어 경계, opal- 접두사 제외) 결과 0건 (변경이력/backup 예외)
  - **전체 코드베이스 `Crawl4AI` 잔존 0건** (web-to-markdown 관련, 변경이력 v1.1/v1.2/v1.4 행만 예외) — TASK §R-9 AC와 동일 기준
- **테스트**: 
  - `ls agents/wtm-agent/ 2>/dev/null` 출력 없음
  - `find agents -type d -name "wtm-agent"` 결과 없음
  - `grep -rln "Crawl4AI" --include="*.md" --exclude-dir=tasks --exclude-dir=docs/backup .` 결과: SKILL.md 변경이력 행 외 0건
- **의존**: Step 3, 4, 5, 6, 7, 8, 9, 10 (모든 잔존 참조 갱신 후 안전 삭제)

→ [MUST] `tasks/002-260512-opp-wtm-opal-standardization/TASK.md` §R-9 AC: "전체 코드베이스에서 `grep -rln \"Crawl4AI\"` 검색 시 web-to-markdown 관련 잔존 0건(변경이력 행 예외 허용)" — 본 Step 사전 검증으로 사전 차단, Step 12 일괄 검증으로 사후 재확인 (§4 QA C-2와 동일 명령).

### Step 12: 변경이력 일괄 검증

- [x] 완료
- **파일**: 변경이력이 추가된 모든 파일 (M-1, M-3, N-3)
- **작업 내용**: 
  - `skills/web-to-markdown/SKILL.md` 변경이력 표에 v1.9 행 (2026-05-12 HH:mm KST + 002) 존재 확인
  - `opal/agents/opal-wtm-agent/AGENT.md` 변경이력 표에 v1.0 행 (2026-05-12 HH:mm KST + 002) 존재 확인
  - `scripts/install-mac.sh` 변경이력 헤더에 v2.2 행 (2026-05-12 HH:mm KST + 002) 존재 확인
  - `opal/core/references/agents.md` §변경이력 표(L296 인근)는 본 태스크가 §wtm-agent 섹션 내용만 갱신하고 §변경이력 표 자체 갱신은 선택 — 추적성 강화를 위해 v1.4 행 추가 권장 (포맷 동일)
  - `opal/skills/opal-agent-creator/SKILL.md`에 변경이력 표 존재 여부 확인 — 있으면 행 추가, 없으면 스킵
  - `docs/PROJECT.md` / `docs/CONVENTIONS.md` / `docs/ARCHITECTURE.md` 변경이력 표 존재 여부 확인 — 프로젝트 문서이므로 표 존재 시 행 추가
  - **W-3 포맷 통일 검증**: 모든 행이 `YYYY-MM-DD HH:mm KST` + `(002)` 단일 표준 포맷 사용. 예외 허용: install-mac.sh는 헤더 주석 형식(표 아님)이나 동일 시각 포맷 적용. PLAN.md 자체 변경이력은 본 태스크 표준 외 (사후 갱신 가능).
- **완료 기준**: 
  - 변경된 모든 파일에 "2026-05-12" + "002" 토큰을 포함한 행이 1건 이상 존재
  - 변경된 모든 파일의 변경이력 행이 `2026-05-12 HH:mm KST` 시각 포맷 사용 (HH:mm은 실제 작성 시각)
  - 파일 간 포맷 혼용 0건 (모두 `YYYY-MM-DD HH:mm KST` 통일)
- **테스트**: 
  - `grep -l "2026-05-12.*002" skills/web-to-markdown/SKILL.md opal/agents/opal-wtm-agent/AGENT.md scripts/install-mac.sh` → 3건 모두 매치
  - W-3 포맷 통일 검증: `grep -E "2026-05-12 [0-9]{2}:[0-9]{2} KST.*\(002\)" skills/web-to-markdown/SKILL.md opal/agents/opal-wtm-agent/AGENT.md scripts/install-mac.sh` → 3건 모두 매치
  - 잔존 구 포맷(`2026-05-12 ?? KST` 또는 시각 없는 `2026-05-12 |`) 0건: `grep -nE "\| 2026-05-12 \|" skills/web-to-markdown/SKILL.md opal/agents/opal-wtm-agent/AGENT.md` → 매치 없음
- **의존**: Step 1-11 모두 완료

→ [MUST] `.opal/AGENT.md` §업무 수행 지침: "문서 변경이력: 스킬·에이전트·참조 문서 수정 시 변경이력 표에 행을 추가한다 (일시 KST + 태스크 번호 포함)" — 본 태스크는 일시 형식을 `YYYY-MM-DD HH:mm KST`로 통일하여 파일 간 혼용을 차단(W-3 해소).

---

## 4. QA 체크리스트

### 기능 테스트

- [ ] **F-1**: `bash ~/.opal/tools/cmux-tool/run.sh https://example.com` (cmux 환경) → `{"ok":true,"method":"cmux","mode":"A"}` + 종료 0 + `tab close` 1회 호출 (TASK §R-3 AC)
- [ ] **F-2**: `bash ~/.opal/tools/cmux-tool/run.sh --surface surface:3` → mode B, `goto`/`open` 미호출, `tab close` 미호출 (TASK §R-6 AC)
- [ ] **F-3**: `bash ~/.opal/tools/cmux-tool/run.sh --surface surface:3 https://google.com` → mode C, `goto` 호출, `tab close` 미호출 (TASK §R-6 AC)
- [ ] **F-4**: `bash ~/.opal/tools/cmux-tool/run.sh --wait 0 https://example.com` → `sleep` 단계 생략 (TASK §R-7 AC)
- [ ] **F-5**: `bash ~/.opal/tools/cmux-tool/run.sh --wait 5000 https://example.com` → 5초 대기 후 추출 (TASK §R-7 AC)
- [x] **F-6**: cmux 환경 외부에서 호출 → `{"ok":false,"error":"not_in_cmux","fallback":"phase3"}` + 종료 2 (TASK §R-4 AC)
- [ ] **F-7**: `$CMUX_SURFACE_ID` 있고 cmux 미설치 → `{"ok":false,"error":"cmux_not_installed","install_url":"https://cmux.com/","github":"https://github.com/manaflow-ai/cmux"}` + 종료 3 (TASK §R-4 AC)
- [ ] **F-8**: web-to-markdown 스킬을 `//wtm --surface surface:3` 호출 시 opal-wtm-agent가 Phase 2 cmux 모드 B로 진입 + 결과 보고에 "민감 정보 포함 가능" 안내 + 저장 경로 명시 (TASK §R-13 AC)
- [ ] **F-9**: 사용자 surface 핸들 없이 B/C 모드 진입 시도 → 거부 (TASK §R-13 AC)
- [ ] **F-10**: `//wtm {url}` 기본 호출 (모드 명시 없음) — 하위 호환 유지: Phase 1 WebFetch 시도 → 실패 시 cmux 환경 충족 시 Phase 2, 아니면 Phase 3 (TASK §제약 조건)

### 일관성 테스트

- [x] **C-1**: `grep -rln "wtm-agent" --include="*.md" --exclude-dir=tasks --exclude-dir=docs/backup .` 결과에 `opal-` 접두사 없는 잔존 0건 (변경이력 행 예외) (TASK §R-2 AC)
- [x] **C-2**: `grep -rln "Crawl4AI" --include="*.md" --exclude-dir=tasks --exclude-dir=docs/backup .` 결과 0건 (web-to-markdown 관련, 변경이력 v1.1/v1.2/v1.4 행 예외 허용) (TASK §R-9 AC)
- [x] **C-3**: `agents/wtm-agent/` 디렉토리 미존재 + `opal/agents/opal-wtm-agent/AGENT.md` 존재 (TASK §R-1, R-2 AC)
- [x] **C-4**: SKILL.md §복수 URL 워커 경로가 `opal-wtm-agent`로 통일 + agents.md §opal-wtm-agent 섹션과 입출력 명세 일치 (TASK §R-8, R-10 AC)
- [x] **C-5**: install-mac.sh 재실행 시 멱등 — `~/.opal/tools/cmux-tool/run.sh`가 한 번만 chmod되고, 두 번째 실행도 에러 없이 통과 (TASK §R-11 AC)
- [x] **C-6**: docs/PROJECT.md L50 / docs/CONVENTIONS.md L21 / docs/ARCHITECTURE.md L49·L141·L275 / opal-agent-creator SKILL.md L66 모두 `wtm-agent` 토큰을 `opal-wtm-agent` 또는 빈 슬롯으로 갱신 (TASK §R-2 AC)
- [x] **C-7**: 변경이력 — 변경된 5개 핵심 파일(SKILL.md / AGENT.md / install-mac.sh / agents.md / agent-creator) 모두 "2026-05-12" + "002" 토큰 1건 이상 존재 (TASK §R-12 AC)

### 문서 품질

- [x] **Q-1**: 한국어 본문 + 영어 코드/필드명 규칙 준수 (D-15 §언어 규칙)
- [x] **Q-2**: kebab-case 파일/폴더 네이밍 — `opal-wtm-agent`, `cmux-tool` 모두 만족 (D-15 §네이밍 규칙)
- [x] **Q-3**: YAML frontmatter 유효성 — opal-wtm-agent AGENT.md를 `python3 -c "import yaml; yaml.safe_load(open('opal/agents/opal-wtm-agent/AGENT.md').read().split('---')[1])"` 통과
- [ ] **Q-4**: 인용 규칙 (D-6) 준수 — PLAN.md §1 참조 테이블 17행 + §2 핵심 설계 인라인 인용 + [MUST] 토큰 3건 이상
- [x] **Q-5**: 변경이력 행 포맷 통일 — 모든 파일이 `\| v{N.M} \| 2026-05-12 HH:mm KST \| 변경내용 (002) \|` 단일 표준 포맷 (W-3 해소, §3 Step 12 검증과 일치). install-mac.sh는 헤더 주석 형식이나 동일 시각 포맷(`2026-05-12 HH:mm KST`) 적용.

---

## 5. 리스크 및 대응

| # | 리스크 | 영향 | 대응 방안 |
|---|--------|------|----------|
| R-1 | **cmux 외부 의존성 변경** — cmux 0.65+에서 명령 인터페이스 변경 시 cmux-tool 명령 시퀀스 깨짐 | Phase 2 동작 실패 → Phase 3 자동 폴백되나 cmux 가치 상실 | (a) cmux-tool 내부에서 `cmux --version` 출력으로 호환성 체크 (0.64.3+ 가드) (b) README.md에 검증 버전 명시 (c) 신 버전 도입 시 별도 태스크로 재검증 |
| R-2 | **사용자 surface 데이터 민감도** — B/C 모드에서 인증 세션 페이지(광고 관리, 결제 등) 추출 시 토큰/PII가 산출물에 노출 | 민감 정보 외부 유출 가능 | (a) cmux-tool 출력에 `user_owned: true` 시그널 (b) opal-wtm-agent가 결과 보고에 [MUST] 경고문 부착 + 저장 경로 명시 (TASK §R-13) (c) docs/SECURITY.md에 향후 항목 추가 검토 (별도 태스크) |
| R-3 | **멀티 workspace 핸들 충돌** — 다른 workspace의 `surface:3`을 사용자가 실수로 명시 시 cross-workspace 동작 | 의도와 다른 surface 추출 | (a) cmux-tool에서 `cmux browser <surface> get url`을 추출 전 1회 호출하여 surface 유효성 확인 (b) 출력 JSON에 surface 핸들 + 최종 URL 모두 명시하여 호출자가 검증 가능 |
| R-4 | **하위 호환 회귀** — `//wtm {url}` 기본 호출이 갑자기 cmux를 거쳐 동작이 달라짐 (속도/안정성 차이) | 기존 사용자 경험 변화 | (a) Phase 2(cmux)는 **조건부** — `$CMUX_SURFACE_ID` 미존재 시 즉시 Phase 3로 폴백 (b) cmux 환경에서도 Phase 1(WebFetch) 우선이 유지되어 일반 페이지는 동일 동작 (c) F-10 회귀 테스트로 검증 |
| R-5 | **Phase 폴백 무한루프 또는 잘못된 분기** — Phase 2 실패가 `fallback: phase3`로 표시되지 않으면 Phase 3 진입 불가 | 추출 실패 + 사용자 차단 | (a) cmux-tool 모든 실패 경로에 `fallback: phase3` 명시적 시그널 (b) SKILL.md 실행 흐름 다이어그램에 Phase 2 실패 → Phase 3 화살표 명시 (c) F-6, F-7 테스트로 분기 검증 |
| R-6 | **install-mac.sh 멱등성 위반** — chmod 블록 두 번째 실행 시 오류 | 재설치 실패 | (a) chmod 블록을 `if [[ -f ... ]]` 가드 (b) C-5 테스트로 재실행 검증 |
| R-7 | **`docs/backup/` 잔존 참조** — grep 결과에 backup 폴더의 옛 문서가 포함되어 C-1, C-2 false negative | QA 통과 시점 혼동 | (a) grep 명령에 `--exclude-dir=docs/backup` + `--exclude-dir=tasks` 일관 적용 (b) C-1, C-2 테스트 명령에 이를 명시 |
| R-8 | **terminology mismatch** — 워커 이름 `opal-wtm-agent` ↔ 약어 `wtm` ↔ 도구 이름 `cmux-tool` ↔ 스킬 이름 `web-to-markdown` 간 용어 혼선 | 호출자가 잘못된 컴포넌트 지정 | (a) SKILL.md §호출 인터페이스에 풀네임/약어 매핑 표 명시 (b) agents.md §opal-wtm-agent에 "스킬: web-to-markdown / 약어: wtm" 명시 (D-6 §7.1 영역간 일관성 검토 결과 — 결정성 이슈는 아니므로 에스컬레이션 불필요, 문서 명시로 해소) |

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-05-12 | 초기 작성 — 12 Step / 5 Phase 실행 체크리스트 + 7개 수정 + 3개 신규 + 2개 삭제 + 안전 가드 [MUST] 4건 + 리스크 8건 (002) |
| v1.1 | 2026-05-12 HH:mm KST | QA Needs Revision 정정 — C-1(§3 Step 11에 Crawl4AI grep 사전 검증 + Step 12 사후 일괄 검증 추가) + W-1(§2 N-3에 JSON 8필드 SSOT 스키마 통일 + §3 Step 5 완료 기준 정정) + W-2(§2 N-1에 안전 가드 3계층 책임 분리 표 + §3 Step 1/3/4 완료 기준에 계층별 검증 항목 추가) + W-3(변경이력 포맷을 `YYYY-MM-DD HH:mm KST + (002)` 단일 표준으로 통일, §2 N-3/M-1/M-3 정정 + §3 Step 12 KST 포맷 검증 추가) (002) |
