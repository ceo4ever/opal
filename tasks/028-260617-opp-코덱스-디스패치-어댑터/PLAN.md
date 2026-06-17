# PLAN: Codex 워커 디스패치 어댑터 정합 — agents.md Codex 행 + tool-backed 인라인 주입 + config [agents]

> 작성일: 2026-06-17
> 입력: TASK.md
> 출력: PLAN.md
> 작업 성격: 문서·어댑터 정합 작업 (코드 로직 변경 아님). core/AGENT.md 불변.

## 1. 현황 조사

### 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | agents.md (어댑터 SSOT) | `opal/core/references/agents.md` | 플랫폼 어댑터 변환 규칙 — Codex 행/인라인 주입 규칙 추가 대상 (R-1, R-2) |
| D-2 | 설계 | dispatch-process.md | `opal/core/references/pm/dispatch-process.md` | PM 디스패치 절차 — Codex 실현 경로 포인터 추가 대상 (R-3) |
| D-3 | 설계 | opal-model-mapping.md | `opal/core/references/opal-model-mapping.md` | Codex model 매핑 SSOT (v1.4) — install 정합 확인 (R-6) |
| D-4 | 소스 | install-mac.sh | `scripts/install-mac.sh` | `install_codex_agents`(670) + config `[agents]` 작성 함수 신설 (R-4) |
| D-5 | 소스 | windows.ps1 | `scripts/install/windows.ps1` | Codex 동기 지점(`Install-PlatformAgents` 1537) + config 동기 (R-5) |
| D-6 | 설계 | PRINCIPLES.md (헌법) | `opal/core/PRINCIPLES.md` | 플랫폼 독립 Core Stance — core/AGENT.md 분기 금지 근거 |
| D-7 | 외부 | Codex Subagents 공식 | [Codex Subagents](https://developers.openai.com/codex/subagents) | toml 스펙 + config.toml `[agents]` 글로벌 설정 |
| D-8 | 외부 | Codex Issue #15250 | [Issue #15250](https://github.com/openai/codex/issues/15250) | tool-backed 이름호출 불가 + 인라인 주입 우회법 근거 |
| D-9 | 외부 | Codex Config Reference | [Config Reference](https://developers.openai.com/codex/config-reference) | config.toml `[agents]` 키 검증 |
| D-10 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | 산출물 인용 규칙 |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §2~§3.

### 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/core/references/agents.md` | 플랫폼 어댑터 변환 규칙 SSOT | 수정 | `agents.md:157-182` (메커니즘 표 4행 + 변환 표 — Codex 미반영) |
| `opal/core/references/pm/dispatch-process.md` | PM 디스패치 전 절차 | 수정 | `dispatch-process.md:9-27` (Step 0 전문 에이전트 선택), `:163-171` (변경이력) |
| `opal/core/references/opal-model-mapping.md` | model 레벨↔플랫폼 매핑 SSOT | 정합 확인 + (불일치 시) 보강 | `opal-model-mapping.md:19-23` Codex 컬럼, `:82` Codex advanced=`gpt-5.5` |
| `scripts/install-mac.sh` | mac 설치 — 어댑터 배포 | 수정 | `install-mac.sh:670-779` (`install_codex_agents`), `:1045-1055` (호출부) |
| `scripts/install/windows.ps1` | Windows 설치 — 어댑터 배포 | 수정 | `windows.ps1:1506-1610` (`Install-PlatformAgents`) |
| `opal/core/AGENT.md` (참조만) | PM 헌법/로직 | **불변** | 헌법 Core Stance — 분기 금지 |

> 근거: `파일:N-M` 포맷.

### 현재 상태

1. **agents.md 어댑터 표에 Codex 행 누락**: `§플랫폼 sub-agent 어댑터 변환 규칙`의 "플랫폼별 메커니즘 (2026-04 기준)" 표는 Claude / Cursor / Gemini CLI / Antigravity 4행뿐이며 Codex 행이 없다(`agents.md:159-164`). frontmatter 변환 규칙 표도 Claude / Cursor / Gemini CLI 3컬럼뿐 Codex 컬럼이 없다(`agents.md:170-178`). install v2.6에서 Codex를 4번째 플랫폼으로 추가했으나 어댑터 문서에 미반영. 인라인 주입(tool-backed 우회) 규칙도 부재.
   - 해당 §의 함수 참조 문장도 `install_{claude,cursor,gemini}_agents`만 나열(`agents.md:155`) — `install_codex_agents` 누락.

2. **dispatch-process.md에 Codex 실현 경로 없음**: PM 디스패치 절차는 Step 0 전문 에이전트 선택 → Step 1~7로 구성되나, tool-backed 세션에서 Codex 워커 디스패치가 generic spawn + 인라인 주입을 거쳐야 한다는 포인터가 전혀 없다(`dispatch-process.md` 전체).

3. **model-mapping SSOT(v1.4)와 install 코드 불일치 — 핵심 발견**: opal-model-mapping.md §2 Codex 컬럼은 `light=gpt-5.4-mini / standard=gpt-5.4 / advanced=gpt-5.5`이다(`opal-model-mapping.md:21-23`). 그러나 install 측 3개 매핑 dict가 모두 v1.3 잔재(`standard=gpt-5.5 / advanced=gpt-5.3-codex`)로 **stale**:
   - `install-mac.sh:562` `emit_platform_agent_adapter` 내 `mapping['codex']`
   - `install-mac.sh:704-708` `install_codex_agents` 내 `codex_model_map`
   - `windows.ps1:1539` `Install-PlatformAgents`의 `codex` `ModelMap`
   - 즉 model-mapping.md v1.4(2026-06-17)에서 `gpt-5.3-codex` 일몰 대응으로 advanced를 `gpt-5.5`로 통일했으나(`opal-model-mapping.md:82`), install 코드에는 반영되지 않았다. **문서/코드 불일치 → 코드(실질 SSOT)가 stale인 케이스이며, SSOT 문서(v1.4)가 정답**이다. 정합의 방향은 install 코드를 v1.4로 맞추는 것.

4. **install Codex 구조**: `install_codex_agents`(`install-mac.sh:670-779`)는 Python heredoc으로 `~/.opal/agents/<name>/AGENT.md` frontmatter+body를 읽어 `~/.codex/agents/<name>.toml`(name/description/model/developer_instructions)을 생성한다. AUTO-GENERATED 헤더 가드로 사용자 파일 보호. Windows는 `Install-PlatformAgents`(`windows.ps1:1506-1610`)가 codex를 toml Format으로 동일 처리.
   - **config.toml `[agents]` 작성 로직은 양 스크립트 모두 부재** (`grep`으로 `[agents]`/`max_threads`/`config.toml` 0건 확인). Codex MCP는 `codex mcp add` CLI로 등록되므로(`install-mac.sh:1505-1507`, `windows.ps1:1408-1418`) config.toml의 `[mcp_servers]`는 CLI가 관리한다 → 신규 `[agents]` 작성 함수는 이 MCP 블록 및 사용자 설정을 훼손하지 않아야 한다.

5. **install 호출부**: mac은 `install_codex_agents`가 `install_claude/cursor/gemini_agents` 다음에 호출됨(`install-mac.sh:1052-1055`). 신규 config 작성 함수도 이 흐름에 추가한다.

### 영향 범위

- **문서 3종**(agents.md / dispatch-process.md / opal-model-mapping.md): 어댑터 규칙·디스패치 절차·매핑 SSOT 보강. 변경이력 행 추가 의무(R-7).
- **스크립트 2종**(install-mac.sh / windows.ps1): config `[agents]` 작성 함수 신설 + 호출부 연결 + 기존 stale 모델 매핑 정정(3개소). 변경이력(스크립트 헤더) 행 추가.
- **불변**: `opal/core/AGENT.md`(플랫폼 분기 금지), `.toml` 생성 로직(폐기 금지), Claude/Cursor/Gemini 어댑터 동작.
- **런타임 영향**: 인라인 주입은 배포가 아니라 PM 디스패치 런타임 행위 → 문서 규칙(prose)만 추가하면 됨. install은 코드 로직 변경 없이 원본 배포 + config 작성만.

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|
| (없음) | - | 신규 파일 없음 — 기존 문서/스크립트 보강만 | TASK 범위 §3 |

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| M-1 | `opal/core/references/agents.md` | 메커니즘 표에 Codex 행 추가 + frontmatter 변환 표에 Codex 컬럼 추가 + "Codex tool-backed 인라인 주입" 규칙 §신설 + §155 함수 참조에 codex 추가 + 변경이력 행 | R-1, R-2, R-7 (`agents.md:152-195`, `:310`) |
| M-2 | `opal/core/references/pm/dispatch-process.md` | Step 0(또는 디스패치 전 선언) 부근에 "Codex tool-backed 세션 → agents.md 인라인 주입 규칙 참조" 1줄 포인터 + 변경이력 행 | R-3, R-7 (`dispatch-process.md:9-27`, `:163`) |
| M-3 | `opal/core/references/opal-model-mapping.md` | Codex 컬럼(v1.4) ↔ install 매핑 정합 확인 결과 기록 + 인라인 주입 model 매핑이 이 SSOT를 따른다는 1줄 명시 + 변경이력 행 | R-6, R-7 (`opal-model-mapping.md:19-27`, `:82`, `:87-95`) |
| M-4 | `scripts/install-mac.sh` | (a) config `[agents]` 멱등 작성 함수 신설 + 호출부 연결 (b) stale Codex 매핑 2개소(`:562`, `:704-708`)를 v1.4로 정정 + 스크립트 헤더 변경이력 행 | R-4, R-6 (`install-mac.sh:562`, `:670-779`, `:1052-1055`, `:7-27`) |
| M-5 | `scripts/install/windows.ps1` | (a) config `[agents]` 멱등 작성(M-4 동등) + 호출부 연결 (b) stale Codex `ModelMap`(`:1539`) v1.4 정정 + 스크립트 헤더 변경이력 행 | R-5, R-6 (`windows.ps1:1506-1610`, `:1539`, `:50-88`) |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| (없음) | - | `.toml` 생성 로직 폐기 금지(확정 방향). 삭제 대상 없음 |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | model-mapping 정합 확인 + 기록 (SSOT 확정 — 후속 install 정정의 기준) | `opal-model-mapping.md` | 낮음 |
| 2 | agents.md Codex 행 + 인라인 주입 규칙 (어댑터 SSOT 보강) | `agents.md` | 중간 |
| 3 | dispatch-process.md 포인터 (agents.md 규칙을 가리킴 — agents.md 확정 후) | `dispatch-process.md` | 낮음 |
| 4 | install-mac.sh config `[agents]` 작성 + 모델 매핑 정정 | `install-mac.sh` | 중간 |
| 5 | windows.ps1 config `[agents]` 작성 + 모델 매핑 정정 (mac 미러) | `windows.ps1` | 중간 |

> 의존: Step 3은 Step 2(agents.md 규칙 §명칭)에 의존. Step 5는 Step 4(설계 미러). Step 1·2·4는 상호 독립이나 정정 기준(v1.4)은 Step 1이 확정.

### 핵심 설계

> 인라인 인용: `(→ D-N)` 또는 `` `경로:줄번호` `` / `[사이트명](URL)`. 필수 제약은 `[MUST]` 포맷.

#### M-1 agents.md (R-1, R-2)

**(1) 메커니즘 표에 Codex 행 추가** — `§플랫폼별 메커니즘` 표(`agents.md:159-164`)에 1행:

| 플랫폼 | 메커니즘 | 등록 경로 | 공식 문서 |
|--------|---------|----------|----------|
| Codex CLI | tool-backed=인라인 주입 / TUI·대화형=이름호출 | `~/.codex/agents/{name}.toml` (자동 로드, 개별 등록 불요) | [Codex Subagents](https://developers.openai.com/codex/subagents) |

- "(2026-04 기준)" 표 캡션을 "(2026-06 기준)"으로 갱신 검토.
- `.toml` 생성은 스펙 정합·TUI 이름호출에 유효하므로 유지함을 명시 (→ D-7, 확정 방향 §3①).

**(2) frontmatter 변환 표에 Codex 컬럼 추가** — `agents.md:170-178` 표에 Codex 컬럼:

- `model: light` → `gpt-5.4-mini`
- `model: standard` → `gpt-5.4`
- `model: advanced` → `gpt-5.5`
- (값은 M-3에서 확정한 SSOT v1.4 Codex 컬럼과 동일하게 기재 — `opal-model-mapping.md:21-23`)
- `[MUST]` `opal/core/references/opal-model-mapping.md` §2: "Codex `advanced`는 프런티어 `gpt-5.5`로 통일한다" (→ `opal-model-mapping.md:82`) — `gpt-5.3-codex` 2026-06-30 일몰.

**(3) "Codex tool-backed 인라인 주입" 규칙 §신설** (R-2 핵심) — 어댑터 §에 신규 하위 절. 다음을 prose로 명문화:
- Codex tool-backed 세션(모델이 도구로 자율 구동)에서는 커스텀 에이전트 **이름 기반 호출이 노출되지 않는다** ([Issue #15250](https://github.com/openai/codex/issues/15250) — OPEN). generic `spawn_agent`(`default`/`explorer`/`no-apps`)만 사용 가능.
- **PM 런타임 행위**: PM이 Codex 워커를 디스패치할 때 `~/.opal/agents/<name>/AGENT.md` **본문을 직접 읽어 `spawn_agent`의 message에 인라인**하고, OPAL model 레벨을 Codex 모델로 매핑한다(→ D-3).
- 이것은 **배포 시점이 아니라 디스패치 런타임 행위**다 — install은 원본 AGENT.md 배포 + `.toml` 생성 + config `[agents]` 작성만 수행한다 (확정 방향 §, TASK §배경 분석 #5).
- 공식 우회법 근거: 이슈 본문이 "각 TOML의 `developer_instructions`를 generic 워커에 수동 주입"을 명시 (→ D-8).
- [MUST] `opal/core/PRINCIPLES.md` Core Stance: "Platform-independent: keep Claude/Cursor/Gemini branches in adapters, never in logic." → 이 규칙은 어댑터 문서(agents.md)에만 존재하며 `opal/core/AGENT.md`에 Codex 분기를 추가하지 않는다 (→ D-6).

**(4)** `agents.md:155` 함수 참조 문장을 `install_{claude,cursor,gemini,codex}_agents`로 갱신.

**(5)** 변경이력 표(`agents.md:310-319`)에 v1.7 행 추가 (028).

#### M-2 dispatch-process.md (R-3)

- Step 0(전문 에이전트 선택, `dispatch-process.md:9-27`) 또는 "디스패치 전 선언"(`:137-141`) 부근에 **1줄 포인터** 추가:
  - "Codex tool-backed 세션에서 워커 디스패치 시 → `agents.md §Codex tool-backed 인라인 주입` 규칙에 따라 AGENT.md 본문을 spawn message에 인라인 주입한다 (이름호출 불가 — #15250)." (→ D-1 §신설절, D-8)
- 위치는 Step 0 폴백 규칙 직후 또는 §디스패치 전 선언이 자연스럽다 (PLAN.md Step 3에서 워커가 실제 위치 판단).
- 변경이력 표(`dispatch-process.md:163-171`)에 v1.5 행 추가 (028).

#### M-3 opal-model-mapping.md (R-6)

- §2 Codex 컬럼은 이미 v1.4로 `light=gpt-5.4-mini / standard=gpt-5.4 / advanced=gpt-5.5`이며 SSOT다(`opal-model-mapping.md:21-23`). **이 값을 변경하지 않는다.**
- **정합 확인 결과 기록**: install 3개소(`install-mac.sh:562`·`:704-708`, `windows.ps1:1539`)가 v1.3 잔재(`standard=gpt-5.5 / advanced=gpt-5.3-codex`)로 stale했음을 확인했고, install을 SSOT로 맞춘다(정정 방향)는 점을 1줄 기재. (→ `install-mac.sh:704-708`)
- **인라인 주입 model 매핑 명시**: §2 또는 §4 부근에 "Codex tool-backed 인라인 주입 시 PM은 OPAL model 레벨을 이 테이블 Codex 컬럼으로 매핑한다 (→ `agents.md §Codex tool-backed 인라인 주입`)" 1줄 추가.
- 변경이력 표(`opal-model-mapping.md:87-95`)에 v1.5 행 추가 (028). (값 변경 없는 정합·기록 보강 버전)

#### M-4 install-mac.sh (R-4 + R-6 정정)

**(a) config `[agents]` 멱등 작성 함수 신설** — `install_codex_config()` (또는 동등명):
- 대상: `~/.codex/config.toml`. 없으면 생성, 있으면 in-place 편집.
- 작성 블록 (글로벌 한계치 — 개별 에이전트 등록 아님, → D-7, D-9):
  ```toml
  [agents]
  max_threads = <기본값>
  max_depth = <기본값>
  job_max_runtime_seconds = <기본값>
  ```
  - 구체 키/기본값은 [Config Reference](https://developers.openai.com/codex/config-reference)에서 워커가 EXECUTE 시 검증 후 확정 (→ D-9).
- **멱등성 [MUST]**: 재실행 시 `[agents]` 블록이 이미 존재하면 중복 추가하지 않는다(AUTO-GENERATED 가드 마커 또는 `[agents]` 헤더 검출). 기존 `[mcp_servers]`/사용자 설정 블록을 훼손하지 않는다 — Codex MCP는 `codex mcp add` CLI가 config.toml `[mcp_servers]`를 관리하므로(`install-mac.sh:1505-1507`) 그 블록을 보존해야 한다.
- 멱등 편집 패턴: 기존 `install_opal_section`/awk 기반 섹션 제거-재작성 패턴(`install-mac.sh:216-230`) 또는 마커 가드를 참고. 단순 append 금지.
- 호출부: `install_codex_agents` 호출(`install-mac.sh:1055`) 직후에 신규 함수 호출 추가.

**(b) stale Codex 모델 매핑 정정** (R-6):
- `install-mac.sh:562` `mapping['codex']` → `{'light': 'gpt-5.4-mini', 'standard': 'gpt-5.4', 'advanced': 'gpt-5.5'}`
- `install-mac.sh:704-708` `codex_model_map` → 동일 v1.4 값. 기본 폴백 `gpt-5.5`(`:750`)는 advanced와 동일하므로 유지 가능 (워커가 확인).
- [MUST] `opal/core/references/opal-model-mapping.md` §2: "Codex `advanced`는 프런티어 `gpt-5.5`로 통일한다" (→ D-3, `opal-model-mapping.md:82`).

**(c)** 스크립트 헤더 변경이력(`install-mac.sh:7-27`)에 v2.8 행 추가 (028).

#### M-5 windows.ps1 (R-5 + R-6 정정)

- M-4와 **동등**한 config `[agents]` 작성을 PowerShell로 미러. 기존 `Set-ContentNoBom` 헬퍼(`windows.ps1:133`)와 섹션 편집 패턴(`:177`, `:252-308`)을 활용.
- 호출부: `Install-PlatformAgents` 또는 메인 흐름(`Invoke-OpalWindowsInstall`, `:1614~`)에 신규 config 작성 함수 호출 추가.
- stale `ModelMap` 정정: `windows.ps1:1539` `codex` `ModelMap` → `@{ light = 'gpt-5.4-mini'; standard = 'gpt-5.4'; advanced = 'gpt-5.5' }`. toml 기본 폴백(`:1557` `'gpt-5.5'`)은 유지 가능.
- 멱등성·MCP 블록 보존 요건은 M-4와 동일 ([MUST]).
- 스크립트 헤더 변경이력(`windows.ps1:50-88`)에 v1.10 행 추가 (028).

## 3. 실행 체크리스트

> 총 5개 Step | Phase 4개

| Phase | Step | 실행 | 비고 |
|-------|------|------|------|
| 1 | 1 | 단독 | model-mapping SSOT 정합 확인 (정정 기준 확정) |
| 2 | 2 | 단독 | agents.md 어댑터 규칙 (인라인 주입 §명칭 확정) |
| 3 | 3, 4 | 병렬 | 서로 다른 파일 (dispatch-process.md / install-mac.sh) — 둘 다 Phase 1·2 결과에 의존 |
| 4 | 5 | 단독 | windows.ps1 — Step 4 설계 미러 |

### Step 1: opal-model-mapping.md 정합 확인 + 기록 (R-6)
- [x] 완료
- **파일**: `opal/core/references/opal-model-mapping.md`
- **작업 내용**: §2 Codex 컬럼(`light=gpt-5.4-mini / standard=gpt-5.4 / advanced=gpt-5.5`, `:21-23`)을 SSOT로 확정(값 변경 없음). install 3개소(`install-mac.sh:562`·`:704-708`, `windows.ps1:1539`)가 v1.3 stale했음을 확인하고 "install을 SSOT v1.4로 정정한다"는 정합 결과 1줄 + "인라인 주입 model 매핑은 이 Codex 컬럼을 따른다(→ agents.md §Codex tool-backed 인라인 주입)" 1줄을 §2 또는 §4에 기재. 변경이력 표(`:87-95`)에 v1.5 행 추가(028).
- **완료 기준**: §2 Codex 컬럼 = `gpt-5.4-mini / gpt-5.4 / gpt-5.5` 유지 확인 + install 정합 방향 기록 존재 + 인라인 주입 매핑 참조 1줄 존재 + v1.5 변경이력 행 존재.
- **테스트**: `grep -n "gpt-5.4-mini\|gpt-5.4\|gpt-5.5\|인라인" opal/core/references/opal-model-mapping.md` — Codex 컬럼·인라인 참조 확인. 변경이력 v1.5(028) 행 grep.
- **의존**: 없음

### Step 2: agents.md Codex 행 + 인라인 주입 규칙 (R-1, R-2)
- [x] 완료
- **파일**: `opal/core/references/agents.md`
- **작업 내용**: 핵심 설계 M-1 (1)~(5) 적용 — ① 메커니즘 표(`:159-164`)에 Codex 행(tool-backed=인라인 주입/TUI=이름호출, 경로 `~/.codex/agents/{name}.toml`, [Codex Subagents](https://developers.openai.com/codex/subagents)) ② frontmatter 변환 표(`:170-178`)에 Codex 컬럼(light=gpt-5.4-mini/standard=gpt-5.4/advanced=gpt-5.5, Step 1 SSOT와 일치) ③ "Codex tool-backed 인라인 주입" 규칙 §신설(PM 런타임 행위/spawn_agent message 주입/model 매핑/#15250 인용/배포 아닌 런타임 명시/`.toml` 유지 명시) ④ `:155` 함수 참조에 codex 추가 ⑤ 변경이력(`:310`) v1.7 행(028).
- **완료 기준**: 메커니즘 표에 Codex 행 존재 + 변환 표에 Codex 컬럼 존재 + [Issue #15250](https://github.com/openai/codex/issues/15250) 인용된 인라인 주입 규칙 문단에 "런타임 PM 행위 / spawn_agent message 주입 / model 매핑 / #15250 인용 / 배포 시점 아님" 5요소 모두 명시 + `.toml` 유지 명시 + v1.7 변경이력 행.
- **테스트**: `grep -n "Codex\|15250\|spawn_agent\|인라인\|gpt-5" opal/core/references/agents.md` — 5요소 + 표 행 확인. core/AGENT.md 미변경 확인(`git diff --stat opal/core/AGENT.md` 빈 결과).
- **의존**: Step 1 (변환 표 Codex 값 = Step 1 SSOT)

### Step 3: dispatch-process.md Codex 경로 포인터 (R-3)
- [x] 완료
- **파일**: `opal/core/references/pm/dispatch-process.md`
- **작업 내용**: Step 0 폴백 규칙 직후(`:22-27`) 또는 §디스패치 전 선언(`:137-141`)에 "Codex tool-backed 세션 → `agents.md §Codex tool-backed 인라인 주입` 규칙에 따라 AGENT.md 본문을 spawn message에 인라인 주입(이름호출 불가 — #15250)" 1줄 포인터 추가. 변경이력 표(`:163-171`)에 v1.5 행(028).
- **완료 기준**: dispatch-process.md에 Codex→agents.md 인라인 주입 참조 라인 존재 + #15250 언급 + v1.5 변경이력 행.
- **테스트**: `grep -n "Codex\|인라인\|agents.md\|15250" opal/core/references/pm/dispatch-process.md`. 변경이력 v1.5(028) grep.
- **의존**: Step 2 (참조하는 §명칭이 Step 2에서 확정됨)

### Step 4: install-mac.sh config [agents] 작성 + 모델 매핑 정정 (R-4, R-6)
- [x] 완료
- **파일**: `scripts/install-mac.sh`
- **작업 내용**: 핵심 설계 M-4 (a)~(c) — ① config `[agents]` 멱등 작성 함수 신설(`~/.codex/config.toml`에 max_threads/max_depth/job_max_runtime_seconds 글로벌 한계치; 재실행 중복 방지; `[mcp_servers]`/사용자 설정 보존) + 호출부(`:1055` 직후) 연결, 구체 키/기본값은 [Config Reference](https://developers.openai.com/codex/config-reference) 검증 후 확정 ② stale Codex 매핑 정정(`:562`, `:704-708` → light=gpt-5.4-mini/standard=gpt-5.4/advanced=gpt-5.5) ③ 헤더 변경이력(`:7-27`) v2.8 행(028).
- **완료 기준**: install 재실행 시 `[agents]` 블록 1회만 존재(멱등) + 기존 `[mcp_servers]`/사용자 키 보존 + `:562`·`:704-708` Codex 매핑이 v1.4(Step 1 SSOT)와 일치 + v2.8 변경이력 행. `.toml` 생성 로직(`install_codex_agents`) 폐기되지 않음.
- **테스트**: `bash -n scripts/install-mac.sh` 문법 검사. 멱등성 — 임시 config.toml로 함수 2회 실행 후 `grep -c '^\[agents\]'` = 1 + 사전 작성한 `[mcp_servers]` 블록 보존 확인. `grep -n "gpt-5.4\|gpt-5.3-codex" scripts/install-mac.sh`로 stale 잔재(`gpt-5.3-codex`) 0건 확인.
- **의존**: Step 1 (정정 목표값 = SSOT v1.4)

### Step 5: windows.ps1 config [agents] 작성 + 모델 매핑 정정 (R-5, R-6)
- [x] 완료
- **파일**: `scripts/install/windows.ps1`
- **작업 내용**: 핵심 설계 M-5 — Step 4와 동등한 config `[agents]` 멱등 작성을 PowerShell로 미러(`Set-ContentNoBom` 헬퍼 `:133` + 섹션 편집 패턴 활용) + 호출부 연결 + stale `ModelMap`(`:1539` → light=gpt-5.4-mini/standard=gpt-5.4/advanced=gpt-5.5) 정정 + 헤더 변경이력(`:50-88`) v1.10 행(028).
- **완료 기준**: windows.ps1에 mac과 동등한 `[agents]` 작성 로직 존재(멱등·MCP 블록 보존) + `:1539` ModelMap v1.4 일치 + v1.10 변경이력 행.
- **테스트**: PowerShell 파서 검사(`pwsh -NoProfile -Command "[scriptblock]::Create((Get-Content scripts/install/windows.ps1 -Raw))"` 환경 가용 시) 또는 육안 구조 검토. `grep -n "gpt-5.4\|gpt-5.3-codex\|\[agents\]" scripts/install/windows.ps1`로 정정·신규 로직 확인.
- **의존**: Step 1, Step 4 (SSOT 값 + 설계 미러)

## 4. QA 체크리스트

### 기능 테스트
- [x] R-1: agents.md 메커니즘 표에 Codex 행 + frontmatter 변환 표에 Codex 컬럼이 존재하고 #15250 근거가 인용되었는가
- [x] R-2: agents.md 인라인 주입 규칙 문단에 "런타임 PM 행위 / spawn_agent message 주입 / model 매핑 / #15250 인용 / 배포 시점 아님" 5요소가 모두 명시되었는가
- [x] R-3: dispatch-process.md에 Codex→agents.md 인라인 주입 참조 라인이 존재하는가
- [x] R-4: install-mac.sh가 config.toml `[agents]`를 멱등 작성하고 재실행 시 중복 추가가 없으며 `[mcp_servers]`/사용자 설정을 보존하는가 (멱등성 테스트 실행 확인: [agents] 1건, [mcp_servers] 보존)
- [x] R-5: windows.ps1이 R-4와 동등한 `[agents]` 작성을 수행하는가 (Install-CodexConfig 신설, 동일 키/기본값/멱등 전략)
- [x] R-6: opal-model-mapping.md Codex 컬럼 = `gpt-5.4-mini/gpt-5.4/gpt-5.5`이고 install 3개소가 이에 일치하도록 정정되었으며 정합 결과가 기록되었는가
- [x] R-7: agents.md / dispatch-process.md / opal-model-mapping.md + install 스크립트 2종에 028 변경이력 행이 추가되었는가

### 일관성 테스트
- [x] core/AGENT.md(`opal/core/AGENT.md`)에 Codex 분기가 추가되지 않았는가 (헌법 Core Stance — `git diff` 빈 결과)
- [x] `~/.opal/` 배포 파일을 직접 편집하지 않고 `opal/`·`scripts/` 소스만 수정했는가
- [x] `.toml` 생성 로직(`install_codex_agents` / `Install-PlatformAgents` codex)이 폐기되지 않고 유지되는가
- [x] agents.md 변환 표 Codex 값 ↔ opal-model-mapping.md §2 Codex 컬럼 ↔ install 3개소 매핑이 모두 `gpt-5.4-mini/gpt-5.4/gpt-5.5`로 일치하는가 (4지점 동일성)
- [x] mac config 작성 로직과 windows config 작성 로직이 동등한가 (키·기본값·멱등 전략)
- [x] Claude/Cursor/Gemini 어댑터 동작이 변경되지 않았는가

### 문서 품질
- [x] 한국어 본문 + 영어 코드/필드명(name/description/developer_instructions/max_threads 등) 규칙을 따르는가
- [x] kebab-case 파일/폴더 네이밍을 따르는가 (신규 파일 없으므로 N/A)
- [x] 인용 규칙(citation-rules.md) 준수 — #15250·Codex 공식 문서·SSOT 인용이 §2 포맷을 따르는가
- [x] 변경이력 표 형식(버전/날짜/변경내용 + 028 태스크 번호)을 기존 행과 일관되게 따르는가

## 5. 리스크 및 대응

| # | 리스크 | 영향 | 대응 |
|---|--------|------|------|
| R-T1 | **install ↔ SSOT 모델 매핑 불일치 (문서/코드 불일치 발견)** — install 3개소(`install-mac.sh:562`·`:704-708`, `windows.ps1:1539`)가 v1.3 잔재(`standard=gpt-5.5/advanced=gpt-5.3-codex`)로 SSOT v1.4(`standard=gpt-5.4/advanced=gpt-5.5`)와 불일치 | 인라인 주입·`.toml` 생성 시 일몰 예정(2026-06-30) `gpt-5.3-codex` 사용 위험 | 하네스 "코드 SSOT" 규칙의 예외 — 여기서는 **문서(model-mapping v1.4)가 정답**이며 stale한 install 코드를 정정한다(Step 1·4·5). PLAN §1 현황 조사 #3에 명시. agentic이나 결정성 이슈 아니므로 정정 진행(자율) |
| R-T2 | config.toml `[agents]` 작성이 사용자 설정/MCP 블록 훼손 | 기존 Codex 설정·MCP 등록 파괴 | 멱등 마커 가드 + `[mcp_servers]` 등 기존 블록 보존 작성([MUST], M-4/M-5). `codex mcp add` CLI 관리 영역과 분리 |
| R-T3 | config `[agents]` 구체 키/기본값이 [Config Reference](https://developers.openai.com/codex/config-reference) 최신과 다를 수 있음 (베타 문서, 변경 가능성) | 잘못된 키 작성 시 Codex가 무시/오류 | EXECUTE 시 워커가 [Config Reference](https://developers.openai.com/codex/config-reference)·[Codex Subagents](https://developers.openai.com/codex/subagents)를 WebFetch로 재확인 후 키/기본값 확정 (→ D-7, D-9) |
| R-T4 | #15250 향후 수정(tool-backed 이름호출 지원) 시 인라인 주입 규칙이 불필요해짐 | 규칙이 stale될 수 있음 | agents.md 규칙에 "#15250 OPEN 상태 — 수정 시 재검토" 단서 기재. opal-model-mapping.md TASK 의존사실과 동일 (TASK §명확화 목표 행) |
| R-T5 | mac/windows config 작성 로직 비대칭 (PowerShell↔Bash 표현 차이) | 플랫폼 간 동작 불일치 | Step 5를 Step 4 설계 미러로 강제. QA 일관성 테스트에서 키·기본값·멱등 전략 동등성 검증 |
