# PLAN: Codex CLI OPAL 프레임워크 통합

> 작성일: 2026-05-24 | 모드: semi-agentic | 다음 단계: EXECUTE
> 입력: `tasks/009-260524-opp-codex-bootstrapper-integration/TASK.md`
> 출력: 본 PLAN.md (PLAN 워커는 코드/설정 미변경, 단일 문서 산출)

---

## 1. 현황 조사

### 1.1 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | claude-bootstrap.md | `opal/bootstrapper/claude-bootstrap.md` | codex-bootstrap.md 신규 작성 시 마커 블록/변경이력 패턴 |
| D-2 | 소스 | gemini-bootstrap.md | `opal/bootstrapper/gemini-bootstrap.md` | "강제 부트스트랩" 패턴(v1.1) 준용 — Codex도 동일 강제 절차 |
| D-3 | 소스 | gemini-hardening.md | `opal/bootstrapper/gemini-hardening.md` | HARDENING 마커 패턴 — Codex 도입 여부 판단 기준 |
| D-4 | 소스 | install-mac.sh | `scripts/install-mac.sh` | `install_opal_section`/`install_claude_permissions`/`install_*_agents`/`emit_platform_agent_adapter`/`install_mcp` 패턴 |
| D-5 | 소스 | install/linux.sh | `scripts/install/linux.sh:24-38` | install-mac.sh로 `exec bash` 단순 위임 — codex 분기가 install-mac.sh 측에 추가되면 Linux는 자동 상속 |
| D-6 | 소스 | install/windows.ps1 | `scripts/install/windows.ps1` | `Register-Bootstrapper`/`Install-OpalMcp`/`Install-PlatformAgents` 패턴 — Codex 분기 추가 위치 |
| D-7 | 설계 | opal-model-mapping.md | `opal/core/references/opal-model-mapping.md` | §2 플랫폼별 매핑 테이블에 Codex 컬럼 추가 |
| D-8 | 설계 | opal/core/AGENT.md | `opal/core/AGENT.md:250-289` | "프로젝트 부트스트래퍼 자동 관리" 절에 Codex 정책 추가 (TASK.md D-7의 실제 경로 보정) |
| D-9 | 기획 | docs/PROJECT.md | `docs/PROJECT.md:17` | §프로젝트 원칙 #3 "플랫폼 독립성" 플랫폼 목록에 Codex 추가 |
| D-10 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | §0 근거 제시 / §2.4 [MUST] 포맷 준수 |
| D-11 | 설계 | coding-principles.md | `opal/core/references/harness/coding-principles.md` | §2 단순성 우선 / §4 외과적 변경 준수 |
| D-12 | 환경 | 캡틴 `~/.codex/config.toml` | `/Users/lucas/.codex/config.toml:1` | 현재 모델 `model = "gpt-5.1-codex-max"`, `model_reasoning_effort = "medium"` |
| D-13 | 외부 | Codex AGENTS.md 가이드 | [Custom instructions with AGENTS.md — Codex](https://developers.openai.com/codex/guides/agents-md) | 글로벌 진입점·로드 순서·project_doc_max_bytes 등 |
| D-14 | 외부 | Codex Config Reference | [Configuration Reference — Codex](https://developers.openai.com/codex/config-reference) | `model` / `mcp_servers.<id>` / `sandbox_mode` / `project_doc_fallback_filenames` 키 |
| D-15 | 외부 | Codex Subagents | [Subagents — Codex](https://developers.openai.com/codex/subagents) | `~/.codex/agents/*.toml` 스키마(name/description/developer_instructions) |
| D-16 | 외부 | Codex CLI 페이지 | [CLI — Codex](https://developers.openai.com/codex/cli) | 모델 스위처 `/model` + `gpt-5.5`/`gpt-5.3-Codex` 등 사용자 노출 모델 |
| D-17 | 환경 | `codex --help` (캡틴 머신) | `which codex` → `/Users/lucas/.nvm/.../bin/codex` | `mcp`/`plugin`/`mcp-server`/`sandbox` 서브커맨드 + `-s sandbox` 플래그 |

### 1.2 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/bootstrapper/claude-bootstrap.md` | Claude 부트스트래퍼 SSOT | 무변경(참조만) | `opal/bootstrapper/claude-bootstrap.md:14-21` |
| `opal/bootstrapper/gemini-bootstrap.md` | Gemini 부트스트래퍼 SSOT | 무변경(참조만) | `opal/bootstrapper/gemini-bootstrap.md:14-21` |
| `opal/bootstrapper/codex-bootstrap.md` | Codex 부트스트래퍼 SSOT | **신규** | — |
| `scripts/install-mac.sh` | macOS 진입점 (Linux 위임 호스트) | **수정** | `scripts/install-mac.sh:235-308`(install_opal_section), `:368-405`(claude permissions), `:450-591`(emit_platform_agent_adapter), `:593-657`(install_*_agents), `:890-924`(install_opal main 흐름), `:1100-1231`(install_mcp), `:113-124`(show_menu), `:1287-1293`(print_summary) |
| `scripts/install/linux.sh` | Linux 진입점 | **무변경**(자동 상속) | `scripts/install/linux.sh:38` exec 위임 |
| `scripts/install/windows.ps1` | Windows 진입점 | **수정** | `scripts/install/windows.ps1:767-823`(Register-Bootstrapper), `:1044-1190`(Install-OpalMcp), `:1258-1328`(Install-PlatformAgents) |
| `opal/core/references/opal-model-mapping.md` | 모델 매핑 SSOT | **수정** | `opal/core/references/opal-model-mapping.md:17-25` 매핑 테이블 |
| `opal/core/AGENT.md` | AGENT v2.7 (부트스트래퍼 자동 관리 절) | **수정** | `opal/core/AGENT.md:250-289` |
| `docs/PROJECT.md` | 프로젝트 정의(SSOT) | **수정** | `docs/PROJECT.md:17` 플랫폼 독립성 문장 |
| `opal/core/mcps/*.json` | 공용 MCP 정의 (`name`/`config`/`platforms`) | **수정(선택)** | TASK.md R-2 (b) 충족을 위해 `platforms` 배열에 `"codex"` 추가 |
| `~/.codex/AGENTS.md` | Codex 글로벌 진입점 (install 산출물) | install이 생성/갱신 | (D-13 §Load Sequence) |
| `~/.codex/agents/*.toml` | Codex 사용자 sub-agent (install 산출물) | install이 생성 | (D-15 §File Location) |
| `~/.codex/config.toml` | Codex 사용자 config (install 산출물) | install이 `mcp_servers.<id>` 머지 | (D-14 §MCP Servers) |

### 1.3 현재 상태

- OPAL은 Claude Code / Cursor / Antigravity(Gemini) 3개 플랫폼에 통합되어 있으며 (`docs/PROJECT.md:17` "Claude Code, Cursor, Gemini"), `install-mac.sh:890-918`에서 부트스트래퍼·hardening·permissions·sub-agent 어댑터·MCP 머지를 일괄 수행한다.
- 캡틴 머신에 OpenAI Codex CLI가 설치되어 있고(`which codex → /Users/lucas/.nvm/versions/node/v22.14.0/bin/codex`), 현재 `~/.codex/config.toml`은 `model = "gpt-5.1-codex-max"` / `model_reasoning_effort = "medium"`만 설정되어 있다 (D-12).
- `~/.codex/` 최상단에 `AGENTS.md` 부재. `~/.codex/agents/` 디렉토리 부재. `~/.codex/skills/`·`~/.codex/plugins/` 디렉토리는 존재하지만 OPAL과 무관(Codex 자체 plugin 마켓플레이스).
- `scripts/install/linux.sh:38`은 `install-mac.sh`로 단순 위임이므로, Codex 분기는 `install-mac.sh`에 한 번만 추가하면 Linux는 자동 상속한다. (Linux 별도 수정 불필요 — R-3 결론 갱신)

### 1.4 영향 범위

- **추가**: Codex 신규 통합 — 부트스트래퍼 + sub-agent 어댑터 + MCP 등록 + 모델 매핑.
- **수정**: 4개 SSOT 문서(모델 매핑·AGENT.md 자동 관리 절·PROJECT.md·`opal/core/mcps/*.json` `platforms` 배열) + 2개 install 진입점(mac, windows).
- **무영향**: Claude/Cursor/Gemini 기존 통합은 어댑터 계층 추가만 일어나므로 회귀 없음(분기 격리).
- **배포**: `~/.codex/AGENTS.md`(글로벌), `~/.codex/agents/*.toml`(어댑터), `~/.codex/config.toml`의 `[mcp_servers.<id>]` 항목.

---

## 2. 의사결정 (M-1~M-6 결정)

> **[MUST]** `opal/core/references/harness/citation-rules.md` §0: "상상·추정·기억 기반 기재 금지 — 모든 분석·설계 결정은 문서 근거(경로/URL + 섹션/줄번호)를 인용해야 한다."

### M-1. Codex CLI 글로벌 instructions 진입점

**결정값**: `~/.codex/AGENTS.md` (선택적으로 `~/.codex/AGENTS.override.md` 우선) — 표준 Markdown, 별도 마커 포맷 불필요.

**근거**: [Custom instructions with AGENTS.md — Codex](https://developers.openai.com/codex/guides/agents-md) §Load Sequence — "In your Codex home directory (defaults to `~/.codex`, unless you set `CODEX_HOME`), Codex reads `AGENTS.override.md` if it exists. Otherwise, Codex reads `AGENTS.md`. ... The combined content is injected into the context window before any of your prompts." 동일 문서 §2: "No special marker blocks or section formatting is required — standard Markdown works fine. The discovery mechanism is purely filename-based."

**적용**:
- 신규 SSOT `opal/bootstrapper/codex-bootstrap.md`를 만들고 `install-mac.sh`의 `install_opal_section()`을 그대로 재사용하여 `~/.codex/AGENTS.md`에 마커 블록(`# === OPAL START ===` ~ `# === OPAL END ===`)을 삽입한다. Codex는 마커를 요구하지 않지만, OPAL의 다른 글로벌 진입점(Claude/Gemini)과 동일한 idempotent 갱신·전환 패턴을 그대로 적용하기 위해 마커를 사용한다 (→ D-4 `scripts/install-mac.sh:235-308`).
- `~/.codex/AGENTS.override.md`는 사용자 우선 파일이므로 OPAL이 점유하지 않는다 — 사용자가 OPAL 부트스트래퍼를 일시 비활성화할 출구로 남긴다 (D-13 §Load Sequence).

### M-2. 프로젝트 단위 부트스트래퍼 자동 삽입 정책

**결정값**: **스킵 (글로벌만)**. Claude/Cursor와 동일한 정책으로 분류.

**근거**: [Codex AGENTS.md](https://developers.openai.com/codex/guides/agents-md) §Load Sequence — "Codex reads AGENTS.md files before doing any work. ... When you start a Codex session, it automatically walks the filesystem from your Git repository root to your current working directory, reading every AGENTS.md it finds." → 글로벌(`~/.codex/AGENTS.md`)이 항상 먼저 주입되므로 `~/.opal/` 미설치 환경이 아닌 한 OPAL 부트스트랩은 글로벌만으로 충분하다. `opal/core/AGENT.md:259-261`의 Claude/Cursor 스킵 논리가 그대로 적용된다.

**적용**:
- `opal/core/AGENT.md` "프로젝트 부트스트래퍼 자동 관리" 절(`opal/core/AGENT.md:250-289`)에 `### Codex — 자동 삽입 스킵` 단락을 추가하여 Claude/Cursor와 동일한 사유를 명시한다.
- 프로젝트 단위 `AGENTS.md` 자동 삽입은 수행하지 않는다 — Codex는 Git 루트부터 자동으로 프로젝트 `AGENTS.md`를 읽지만 OPAL이 임의로 사용자 프로젝트 파일을 변조하는 부작용을 피한다.

### M-3. Codex sub-agent 지원 여부 + 등록 경로/스키마

**결정값**: **지원** — `~/.codex/agents/<name>.toml` (개인) / `.codex/agents/<name>.toml` (프로젝트). 필수 필드 `name`, `description`, `developer_instructions`. 선택 필드 `model`, `model_reasoning_effort`, `sandbox_mode`, `mcp_servers`, `nickname_candidates`, `skills.config`.

**근거**: [Subagents — Codex](https://developers.openai.com/codex/subagents) — "Custom subagents are defined as standalone TOML files in two locations: **Personal agents:** `~/.codex/agents/`; **Project-scoped agents:** `.codex/agents/`. Each file defines a single custom agent and is loaded as a configuration layer for spawned sessions." 필수 필드 3종 + 선택 필드 6종 명시.

**적용**:
- `install-mac.sh`에 `install_codex_agents()` 함수 신설. `~/.opal/agents/*/AGENT.md`의 YAML frontmatter(`name`/`description`/`model`) + 본문을 읽어 TOML 포맷으로 변환 — `description` ↔ frontmatter `description`, `developer_instructions` ↔ `body`(AGENT.md 본문), `model` ↔ M-5 매핑.
- 변환은 기존 `emit_platform_agent_adapter()`의 평탄화·AUTO-GENERATED 헤더·user-managed 파일 가드 규칙을 그대로 따른다 (`scripts/install-mac.sh:450-591`). 단, 출력 포맷은 Markdown YAML이 아닌 **TOML** — Python heredoc에서 `tomli_w`(venv 의존)를 쓰지 않고 stdlib 문자열 빌딩으로 직렬화(영문 키 + 따옴표 escape).
- `emit_platform_agent_adapter()`의 `mapping` 딕셔너리에 `codex` 행을 추가하되, **출력 경로 분기에서 TOML 모드를 사용**한다 — 즉 platform="codex"일 때만 분기. 단순성 우선(coding-principles §2)을 위해, codex용 작성은 `emit_platform_agent_adapter`를 호출하지 않고 `install_codex_agents()` 내부에서 별도 짧은 Python heredoc으로 직렬화한다(YAML→TOML 포맷 차이로 인한 분기 비용 회피).

### M-4. Codex MCP 등록 방식

**결정값**: `codex mcp add <name> -- <command> [args...]` CLI 사용 (Claude/Gemini와 동일 패턴). 환경변수는 `--env KEY=VALUE` 반복 플래그.

**근거**: `codex mcp --help` 출력(D-17) — `Commands: list / get / add / remove / login / logout`. `codex mcp add --help` — `Usage: codex mcp add [OPTIONS] <NAME> (--url <URL> | -- <COMMAND>...)`, `--env <KEY=VALUE>` "Environment variables to set when launching the server. Only valid with stdio servers". [Codex Config Reference](https://developers.openai.com/codex/config-reference) — `mcp_servers.<id>.command` / `.args` / `.url` / `.enabled` / `.enabled_tools`.

**적용**:
- `install-mac.sh:install_mcp()` (`scripts/install-mac.sh:1100-1231`)의 platform switch에 `codex)` 케이스 추가. `find_cli_bin codex` 검출 → `install_mcp_cli "$bin" "" "$name" "$command" "${args_array[@]}"` 호출. **scope 플래그 없음** (Codex는 user/project 스코프 분기 없이 `~/.codex/config.toml`로 머지).
- `install_mcp_cli()`는 `"$cli_bin" mcp get "$name"` 멱등 체크가 Codex에도 동작한다 (D-17 codex mcp 서브커맨드 `get` 존재).
- `print_summary`의 안내문에 `Codex MCP                    codex mcp add (CLI 등록)` 행 추가.
- `opal/core/mcps/*.json` 각 파일의 `platforms` 배열에 `"codex"` 추가 (대상 MCP는 stdio 명령 화이트리스트 npx/npm/node/python3/python을 사용하므로 Codex와 호환).
- **windows.ps1**: `Install-OpalMcp` switch에 `'codex'` 케이스 추가 — `Get-Command codex` 검출 → `& $codexCli.Source mcp remove $name 2>&1 | Out-Null` → `& $codexCli.Source mcp add $name -- $cfgWin.command $cfgWin.args` (Convert-McpConfigForWindows 결과 사용, npx→npx.cmd 그대로 적용).

### M-5. Codex 모델 매핑 (light / standard / advanced)

**결정값**:

| 레벨 | Codex 모델 ID |
|------|--------------|
| `light` | `gpt-5-mini` |
| `standard` | `gpt-5-codex` |
| `advanced` | `gpt-5.1-codex-max` |

**근거**:
- [Codex Config Reference](https://developers.openai.com/codex/config-reference) §model — "Model to use (e.g., `gpt-5.5`)." 유효 모델 ID로 `gpt-5.5`, `gpt-5.1-codex-max`, `gpt-5-codex`, `gpt-5`, `gpt-5-mini`, `gpt-5-nano` 명시.
- 캡틴 환경 `/Users/lucas/.codex/config.toml:1` — `model = "gpt-5.1-codex-max"` (D-12) — 캡틴 일상 사용 모델이 `advanced` 슬롯과 일치.
- `gpt-5-codex`는 코딩 특화 standard 모델로, OPAL standard 슬롯의 "범용 작업: 코드 작성, 문서 작성, 일반 분석" (`opal/core/references/opal-model-mapping.md:14`) 정의와 일치.
- `gpt-5-mini`는 light 슬롯의 "단순 작업: 분류, 포맷 변환, 검색 기반 분석" 정의와 일치 (가장 가벼운 일반 모델). `gpt-5-nano`는 추론 성능이 더 낮아 OPAL light(분석 포함) 요구를 보수적으로 충족하지 못해 후순위.

**적용**:
- `opal/core/references/opal-model-mapping.md` §2 표에 `Codex` 컬럼 추가(상기 3행).
- `install-mac.sh:emit_platform_agent_adapter()` (`scripts/install-mac.sh:548-553`) `mapping` dict에 codex 행 추가: `'codex': {'light': 'gpt-5-mini', 'standard': 'gpt-5-codex', 'advanced': 'gpt-5.1-codex-max'}`. (Codex sub-agent TOML의 `model` 필드 채움 — D-15 §Optional Fields)
- `windows.ps1:Install-PlatformAgents` `$platforms` hashtable에 동일 codex 항목 추가 (`scripts/install/windows.ps1:1273-1286`).
- 모델 ID 변경 가능성: D-16에서 Codex 사용자 UI가 `gpt-5.5`·`gpt-5.3-Codex` 등 새 ID로 이동 중이므로, 모델 매핑 SSOT 문서의 §5 갱신 가이드라인에 "Codex는 모델 변경 빈도가 높음 — 분기마다 점검" 주석을 1줄 추가한다.

### M-6. Codex 권한/하드닝 필요성

**결정값**: **권한 별도 설정 불필요**(`~/.opal/` 외부 디렉토리 접근에 추가 설정 없음). HARDENING 미도입.

**근거**:
- [Codex Config Reference](https://developers.openai.com/codex/config-reference) §sandbox_mode — `read-only | workspace-write | danger-full-access`. `sandbox_workspace_write.writable_roots` — "Additional writable roots when `sandbox_mode = "workspace-write"`". → **read 전용 접근에는 별도 화이트리스트가 필요하지 않다**. OPAL은 사용자 세션에서 `~/.opal/` 하위를 Read 도구로 읽는 용도 위주이므로 `read-only`/`workspace-write` 기본값으로 동작한다.
- Claude는 `install_claude_permissions()`로 `settings.json`의 `permissions.allow`에 `Read(~/.opal/**)`를 등록(`scripts/install-mac.sh:368-405`)했지만, 이는 Claude Code의 명시적 권한 모델(`Read(...)` 패턴) 특성에 따른 것이며 Codex는 동일 권한 모델을 사용하지 않는다. → 별도 함수 신설 안 함.
- Gemini의 `install_gemini_config()`는 `context.includeDirectories`에 `~/.opal/`을 추가(`scripts/install-mac.sh:409-440`)했지만, Codex의 `project_doc_*` 키는 "fallback filename"과 "max bytes"만 다루고(D-14) "추가 inclusion 경로" 개념이 없다 → 동등 항목 부재.
- Gemini HARDENING(`opal/bootstrapper/gemini-hardening.md`)은 Gemini 모델의 "Eager 로드 누락" 행동 특성을 보정하기 위한 것이며, Codex의 행동 특성에서 동일한 결함이 관측·보고되지 않았다 → 도입하지 않는다. (관측되면 별도 태스크로 추가)

**적용**:
- `install_codex_permissions()` 함수 신설하지 않음.
- HARDENING 마커 미도입.
- 다만 `~/.codex/config.toml`에 `mcp_servers.<id>`를 머지할 때 기존 `model`/`personality`/`projects.*` 등 다른 키를 보존해야 한다 — Python TOML 머지로 처리(아래 §3 Step 5).

### 결정 사항 요약

| # | 항목 | 결정 |
|---|------|------|
| M-1 | 글로벌 진입점 | `~/.codex/AGENTS.md` + OPAL 마커 블록(다른 플랫폼과 동일 idempotent 패턴) |
| M-2 | 프로젝트 자동 삽입 | **스킵** (Claude/Cursor와 동일 — 글로벌이 항상 먼저 주입됨) |
| M-3 | Sub-agent 지원 | **지원** — `~/.codex/agents/<name>.toml` (필수: name/description/developer_instructions) |
| M-4 | MCP 등록 | `codex mcp add` CLI + `~/.codex/config.toml [mcp_servers.<id>]` |
| M-5 | 모델 매핑 | light=`gpt-5-mini` / standard=`gpt-5-codex` / advanced=`gpt-5.1-codex-max` |
| M-6 | 권한/하드닝 | **불필요** (`install_codex_permissions()` 신설 안 함, HARDENING 미도입) |

---

## 3. 구현 계획

### 3.1 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|
| N-1 | `opal/bootstrapper/codex-bootstrap.md` | Codex 부트스트래퍼 SSOT (claude-bootstrap.md와 동일 구조) | M-1, R-1 |

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| U-1 | `scripts/install-mac.sh` | (1) 헤더 변경이력 v2.6 행 추가 / (2) `install_codex_agents()` 신설 / (3) `emit_platform_agent_adapter()` `mapping` dict에 codex 행 추가(M-5) — codex platform일 때는 별도 처리 위해 codex 호출 경로 분리 / (4) `install_opal()` 본문에 `install_opal_section "$opal_dir/bootstrapper/codex-bootstrap.md" "$USER_HOME/.codex/AGENTS.md" "Codex"` + `install_codex_agents` 추가 / (5) `install_mcp()` switch에 `codex)` 케이스 추가 / (6) `show_menu` 안내 문구 갱신 / (7) `print_summary`에 Codex 행 추가 | R-2, M-1, M-3, M-4, M-5 |
| U-2 | `scripts/install/linux.sh` | **무변경** (`scripts/install/linux.sh:38` 단순 위임이므로 install-mac.sh 변경분 자동 상속). 단, 헤더 변경이력 주석에 v1.1 행 1줄만 추가 — "task 009: install-mac.sh의 Codex 분기를 그대로 상속(별도 코드 변경 없음)" 명시로 추적성 확보 | R-3(축소 적용), §1.2 D-5 |
| U-3 | `scripts/install/windows.ps1` | (1) 헤더 변경이력 행 추가 / (2) `Register-Bootstrapper`에 `~/.codex/AGENTS.md` 처리 추가 (Install-OpalSection 재사용) / (3) `Install-OpalMcp` switch에 `'codex'` 케이스 추가 / (4) `Install-PlatformAgents`에 codex(`~/.codex/agents/<name>.toml`, TOML 직렬화, M-5 모델 매핑) 추가 | R-4, M-1, M-3, M-4, M-5 |
| U-4 | `opal/core/references/opal-model-mapping.md` | (1) §2 매핑 테이블에 `Codex` 컬럼 추가 (light=gpt-5-mini / standard=gpt-5-codex / advanced=gpt-5.1-codex-max) / (2) §공식 모델 목록 표에 Codex 행 추가(URL: developers.openai.com/codex/config-reference) / (3) §4 플랫폼 감지에 `~/.codex/AGENTS.md → Codex` 분기 추가 / (4) §5 갱신 가이드라인에 "Codex는 모델 ID 변경 빈도가 높음 — 분기마다 점검" 1줄 추가 / (5) 변경이력 v1.2 행 추가 | R-5, M-5 |
| U-5 | `opal/core/AGENT.md` | "프로젝트 부트스트래퍼 자동 관리" 절(L250-289)에 `### Codex — 자동 삽입 스킵` 단락 추가(Claude 절과 동일 사유: 글로벌이 항상 먼저 주입). §250 도입부 문장 "Antigravity(Gemini) 환경에 한해" → "Antigravity(Gemini) 환경에 한해" 유지(Codex는 글로벌 진입점이 자동 로드되므로 자동 삽입 제외 그룹). §프로젝트 컨텍스트(L294)의 "CLAUDE.md / .cursor/rules/ / GEMINI.md" 줄에 "AGENTS.md(Codex)" 추가. 변경이력 v2.8 행 추가 | R-6, M-2 |
| U-6 | `docs/PROJECT.md` | §프로젝트 원칙 #3(L17) "Claude Code, Cursor, Gemini 등" → "Claude Code, Cursor, Gemini, Codex 등"로 갱신. 변경이력 표가 부재한 파일이므로 별도 변경이력 추가 없이 본문만 갱신(TASK.md R-7 AC "변경이력 표가 있는 경우" 조건절 만족) | R-7 |
| U-7 | `opal/core/mcps/*.json` (모든 *.json) | 각 파일의 `platforms` 배열에 `"codex"` 항목 추가 (대상은 install_type="config_merge" + command이 npx/npm/node/python3/python인 항목 한정) | R-2 (b) AC, M-4 |

#### 삭제

없음.

### 3.2 구현 순서

> Phase 그룹핑: 동일 파일 수정은 같은 Phase 금지, 의존성은 SSOT → 어댑터(스크립트) → 진입점 정책 → 메타 문서 순.

| 순서 | Phase | 작업 | 파일 | 예상 난이도 |
|------|-------|------|------|-----------|
| 1 | 1 | Codex 부트스트래퍼 SSOT 신규 작성 (N-1) | `opal/bootstrapper/codex-bootstrap.md` | 낮음 |
| 2 | 1 | 모델 매핑 SSOT에 Codex 컬럼 추가 (U-4) | `opal/core/references/opal-model-mapping.md` | 낮음 |
| 3 | 1 | mcps/*.json platforms 배열에 codex 추가 (U-7) | `opal/core/mcps/*.json` | 낮음 |
| 4 | 1 | PROJECT.md 플랫폼 독립성 문장 갱신 (U-6) | `docs/PROJECT.md` | 낮음 |
| 5 | 1 | AGENT.md 자동 관리 절에 Codex 스킵 절 추가 (U-5) | `opal/core/AGENT.md` | 낮음 |
| 6 | 2 | install-mac.sh: install_codex_agents + emit_platform_agent_adapter codex 분기 + install_opal/install_mcp/show_menu/print_summary 갱신 + 헤더 변경이력 (U-1) | `scripts/install-mac.sh` | 중간 |
| 7 | 3 | windows.ps1: Register-Bootstrapper / Install-OpalMcp / Install-PlatformAgents codex 분기 + 헤더 변경이력 (U-3) | `scripts/install/windows.ps1` | 중간 |
| 8 | 3 | linux.sh: 헤더 변경이력 행만 1줄 추가(코드 변경 없음) (U-2) | `scripts/install/linux.sh` | 낮음 |

> Phase 1: SSOT 5개 파일은 서로 독립이므로 병렬 실행 가능. Phase 2/3: install-mac.sh가 SSOT 4개를 읽어 사용하므로 Phase 1 이후. windows.ps1과 linux.sh는 install-mac.sh와 독립 파일(병렬 가능)이지만 동작 대칭 검증을 위해 install-mac.sh 직후 그룹으로 묶는다.

### 3.3 핵심 설계

#### N-1: `opal/bootstrapper/codex-bootstrap.md`

`opal/bootstrapper/claude-bootstrap.md`의 구조를 그대로 따른다 (→ D-1) — `````markdown` 코드블록 안에 OPAL 마커 안에 들어갈 본문 1벌.

본문은 claude/gemini bootstrap과 동일한 2줄(`~/.opal/AGENT.md` Read + `~/.opal/identity.md` Read) 부트스트랩 명령 + 코드블록 외 변경이력 표 1행 (v1.0 / 2026-05-24 / "최초 작성 — Codex CLI 통합 (태스크 009)").

마커 블록 본문(`# === OPAL START ===` ~ `# === OPAL END ===`)은 `install-mac.sh:install_opal_section()`이 추출하여 `~/.codex/AGENTS.md`에 삽입한다 (→ D-4 `scripts/install-mac.sh:225-308`).

[MUST] `opal/bootstrapper/claude-bootstrap.md:14-21`: ```` ```markdown / ## OPAL AI Agent — 필수 부트스트랩 / **[MUST]** ... / 1. `~/.opal/AGENT.md` ... / 2. `~/.opal/identity.md` ... / ``` ```` — 본문은 위 두 줄을 그대로 사용한다 (워커 행동 일관성).

#### U-1: `scripts/install-mac.sh`

(1) 헤더 주석(파일 상단)에 1행 추가:

```
#   v2.6 2026-05-24: Codex CLI 통합 — install_codex_agents 신설 + install_opal/install_mcp/show_menu/print_summary codex 분기 + emit_platform_agent_adapter codex 모델 매핑 (009)
```

(2) `install_codex_agents()` 신설 (위치: `install_gemini_agents()` 직후, L658 근처). 시그니처는 install_*_agents 패턴 동일.

`~/.opal/agents/*/AGENT.md`를 Read하여 다음 TOML로 변환:

```toml
name = "<agent name>"
description = "<flattened description>"
model = "<M-5 mapped id>"
developer_instructions = """
<AGENT.md body — frontmatter 제외 본문, 평탄화 없음 그대로>
"""
```

(→ D-15 §Required Schema Fields). 출력은 `~/.codex/agents/<name>.toml`. Python heredoc에서 stdlib 문자열 빌딩으로 직렬화 (TOML triple-quoted basic string + `\`/`"` escape — `tomli_w` 의존 회피로 단순성 유지 (coding-principles §2)).

[MUST] [Subagents — Codex](https://developers.openai.com/codex/subagents): "Every custom agent file must include three mandatory fields: `name`, `description`, `developer_instructions`."

기존 emit_platform_agent_adapter의 user-managed 파일 가드(`AUTO-GENERATED by install-mac.sh` 헤더 미존재 시 스킵 — `scripts/install-mac.sh:555-561`)를 동일하게 적용한다. TOML에서는 헤더 주석을 `# AUTO-GENERATED by install-mac.sh from ~/.opal/agents/<name>/AGENT.md. DO NOT EDIT.`로 첫 줄에 삽입한다 (TOML 주석은 `#`).

(3) `emit_platform_agent_adapter()` (`scripts/install-mac.sh:548-553`)의 `mapping` dict에 codex 행 추가:

```python
'codex': {'light': 'gpt-5-mini', 'standard': 'gpt-5-codex', 'advanced': 'gpt-5.1-codex-max'},
```

단, codex는 출력 포맷이 TOML이므로 emit_platform_agent_adapter 자체는 사용하지 않고 mapping만 동기 목적 보존 — install_codex_agents가 내부 mini-script에서 동일 매핑을 사용한다. (또는 mapping dict 자체를 호출 측에서 공유하도록 environment variable로 전달 — 단순성 우선하여 install_codex_agents에 매핑 dict를 인라인으로 복제하지 않고 [MUST] M-5 매핑 표를 1곳(emit_platform_agent_adapter)에 두고 install_codex_agents가 동일 표를 코드 주석으로 cross-reference한다.)

(4) `install_opal()` 본문 (L890-924) 부트스트래퍼 블록에 다음 2줄 추가:

```bash
install_opal_section "$opal_dir/bootstrapper/codex-bootstrap.md" \
    "$USER_HOME/.codex/AGENTS.md" "Codex"
```

그리고 `install_*_agents` 블록(L916-918) 끝에:

```bash
install_codex_agents
```

(5) `install_mcp()` (L1180~) switch에 `codex)` 케이스 추가 (claude 케이스 패턴 복제):

```bash
codex)
    local bin
    if bin=$(find_cli_bin codex "$USER_HOME/.nvm/versions/node/*/bin/codex" "/opt/homebrew/bin/codex" "/usr/local/bin/codex"); then
        if install_mcp_cli "$bin" "" "$name" "$command" "${args_array[@]}"; then
            installed_platforms+=("codex")
        fi
    else
        warn "codex CLI 없음 — 수동 등록: codex mcp add $name -- $command ${args_array[*]}"
    fi
    ;;
```

scope 플래그가 빈 문자열(`""`)인 점만 claude(`"--scope user"`)와 다르다 (M-4).

(6) `show_menu()` (L113-124) 메뉴 [2] 안내 문구 갱신: `"MCP 서버 설정 → claude, cursor, gemini, antigravity"` → `"MCP 서버 설정 → claude, cursor, gemini, antigravity, codex"`.

(7) `print_summary()` (L1287) 안내 행 추가: `echo "    Codex MCP                    codex mcp add (CLI 등록)"`.

#### U-2: `scripts/install/linux.sh`

코드 변경 없음. 헤더 주석 §변경이력에 1행 추가 (`scripts/install/linux.sh:19` 다음):

```
#   v1.1 2026-05-24: Codex CLI 통합은 install-mac.sh 위임 경로로 자동 상속 (별도 코드 변경 없음) (009)
```

코딩 원칙 §4 외과적 변경: `linux.sh`는 `exec bash ${INSTALLER}` 단순 위임이므로 추가 작업이 없음 — 추적성만 추가.

#### U-3: `scripts/install/windows.ps1`

(1) 헤더 변경이력 (L82 근처 끝)에 1행 추가:

```
v1.6.0 2026-05-24  Codex CLI 통합 — Register-Bootstrapper 에 ~/.codex/AGENTS.md 추가 + Install-OpalMcp 에 'codex' 케이스 + Install-PlatformAgents 에 codex(TOML 직렬화) 추가 (009)
```

(2) `Register-Bootstrapper` (L767-823) 끝에 Codex 블록 추가:

```powershell
# ── Codex ──
$codexSnippet = [IO.Path]::Combine($bsDir, 'codex-bootstrap.md')
$codexTarget  = [IO.Path]::Combine($userHome, '.codex', 'AGENTS.md')
if (Test-Path $codexSnippet) {
    Install-OpalSection -SnippetPath $codexSnippet -Target $codexTarget -Label 'Codex'
}
```

(3) `Install-OpalMcp` (L1116) switch에 `'codex'` 케이스 추가:

```powershell
'codex' {
    $codexCli = Get-Command codex -ErrorAction SilentlyContinue
    if ($codexCli) {
        $prevErrPref = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        try {
            & $codexCli.Source mcp remove $name 2>&1 | Out-Null
            $cfgWin = Convert-McpConfigForWindows -Config $config
            $args = @('mcp', 'add', $name, '--', $cfgWin.command) + @($cfgWin.args)
            & $codexCli.Source @args 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) { $installed += 'codex' }
        } finally {
            $ErrorActionPreference = $prevErrPref
        }
    } else {
        Write-OpalWarn "codex CLI 없음 — ${name} 수동 등록 필요"
    }
}
```

scope 플래그 없음(M-4).

(4) `Install-PlatformAgents` (L1273-1286) `$platforms` 해시테이블에 codex 추가:

```powershell
'codex' = @{
    Dst = Join-Path $userHome '.codex\agents'
    ModelMap = @{ light = 'gpt-5-mini'; standard = 'gpt-5-codex'; advanced = 'gpt-5.1-codex-max' }
    Format = 'toml'
}
```

`foreach ($pname in $platforms.Keys)` 루프 내부에 `$Format` 분기 — `'toml'`이면 TOML 직렬화 경로(필수 필드 name/description/developer_instructions + 선택 model), 아니면 기존 Markdown YAML 경로. TOML 직렬화는 PowerShell 문자열 빌딩으로 처리(triple-quoted basic string `"""..."""`, `\` 및 `"` escape).

#### U-4: `opal/core/references/opal-model-mapping.md`

(1) §2 매핑 테이블 (`opal/core/references/opal-model-mapping.md:19-23`) 컬럼 추가:

```markdown
| 레벨 | Claude | Gemini | OpenAI | Codex |
|------|--------|--------|--------|-------|
| `light` | haiku | gemini-2.5-flash-lite | gpt-4.1-mini | gpt-5-mini |
| `standard` | sonnet | gemini-2.5-flash | gpt-4.1 | gpt-5-codex |
| `advanced` | opus | gemini-2.5-pro | o3 | gpt-5.1-codex-max |
```

(2) §공식 모델 목록 표에 Codex 행 추가: `| Codex | https://developers.openai.com/codex/config-reference |`.

(3) §4 플랫폼 감지 단계 #1 항목에 `AGENTS.md` (`~/.codex/AGENTS.md`) → Codex 행 추가.

(4) §5 갱신 가이드라인 끝에 1줄: "Codex는 모델 ID 변경 빈도가 높다 — 분기마다 [Codex Config Reference](https://developers.openai.com/codex/config-reference) 점검."

(5) 변경이력 행 추가: `| v1.2 | 2026-05-24 | Codex 컬럼 추가 + 플랫폼 감지/갱신 가이드 보강 (009) |`.

#### U-5: `opal/core/AGENT.md`

(1) §250 도입부 문장 유지 — Codex는 자동 삽입 스킵 그룹이므로 본문 구조 변경 없음.

(2) "Cursor — 자동 삽입 스킵" 절(L276-278) 직후에 `### Codex — 자동 삽입 스킵` 단락 추가:

```markdown
### Codex — 자동 삽입 스킵

install-mac.sh가 `~/.codex/AGENTS.md`(글로벌)에 OPAL 마커를 자동 삽입하며, Codex CLI는 세션 시작 시 글로벌 → 프로젝트 순으로 AGENTS.md를 항상 자동 로드한다 ([Codex AGENTS.md 가이드](https://developers.openai.com/codex/guides/agents-md)). 따라서 프로젝트 단위 `AGENTS.md` 자동 삽입은 **수행하지 않는다**.

이유: Claude/Cursor 절과 동일 — `~/.opal/` 미설치 환경에서는 마커가 있어도 무용이고, 설치 환경에서는 글로벌 마커가 함께 셋업된다.
```

(3) §프로젝트 컨텍스트(L294) 줄 갱신:

```
- `CLAUDE.md` / `.cursor/rules/` / `GEMINI.md` / `AGENTS.md`(Codex) — OPAL 부트스트래퍼
```

(4) §변경이력에 v2.8 행 추가: `| v2.8 | 2026-05-24 | "프로젝트 부트스트래퍼 자동 관리" 절에 Codex 스킵 정책 추가 — Codex 글로벌 진입점이 자동 로드되므로 Claude/Cursor와 동일하게 프로젝트 마커 미삽입 (009) |`.

#### U-6: `docs/PROJECT.md`

§프로젝트 원칙 #3 (`docs/PROJECT.md:17`):

> 변경 전: `3. **플랫폼 독립성** — Claude Code, Cursor, Gemini 등 어디서든 동작해야 한다`
> 변경 후: `3. **플랫폼 독립성** — Claude Code, Cursor, Gemini, Codex 등 어디서든 동작해야 한다`

PROJECT.md에 변경이력 표가 부재하므로 별도 변경이력 행 추가는 수행하지 않는다 (TASK.md R-7 AC "변경이력 표가 있는 경우" 조건 부합).

#### U-7: `opal/core/mcps/*.json`

각 파일의 `platforms` 배열에 `"codex"` 추가. 단, 조건:
- `install_type` == `"config_merge"`
- `config.command` 의 basename이 화이트리스트(`npx|npm|node|python3|python`)에 포함 (`scripts/install-mac.sh:1087-1089`)

조건 미달 항목은 무변경.

---

## 4. 실행 체크리스트

> 총 8개 Step | Phase 3개
>
> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | 1     | 1, 2, 3, 4, 5 | 병렬 | 독립 SSOT/문서 파일 5종 |
> | 2     | 6 | 순차 | install-mac.sh — Phase 1의 codex-bootstrap.md를 참조 |
> | 3     | 7, 8 | 병렬 | windows.ps1 / linux.sh — install-mac.sh와 독립 |

### Step 1: Codex 부트스트래퍼 SSOT 신규 작성

- [x] 완료
- **파일**: `opal/bootstrapper/codex-bootstrap.md` (신규)
- **작업 내용**: `opal/bootstrapper/claude-bootstrap.md` 구조를 그대로 따라 작성. `````markdown` 코드블록 안에 OPAL 마커 본문(2줄 부트스트랩 명령 — `~/.opal/AGENT.md` Read + `~/.opal/identity.md` Read) + 코드블록 외 변경이력 표 1행 (v1.0 / 2026-05-24 / "최초 작성 — Codex CLI 통합 (태스크 009)").
- **완료 기준**: (a) 파일이 존재 (b) `# === OPAL START ===` / `# === OPAL END ===` 마커 사이 본문이 claude-bootstrap.md와 동일한 2줄 명령 포함 (c) 변경이력 표에 v1.0/2026-05-24/태스크 009 행 존재.
- **테스트**: `extract_bootstrap_content opal/bootstrapper/codex-bootstrap.md` 명령(또는 sed 동일 패턴)이 빈 출력이 아닌 정상 추출. `grep -c "OPAL AI Agent — 필수 부트스트랩" opal/bootstrapper/codex-bootstrap.md` ≥ 1.
- **의존**: 없음.

### Step 2: 모델 매핑 SSOT에 Codex 컬럼 추가

- [x] 완료
- **파일**: `opal/core/references/opal-model-mapping.md`
- **작업 내용**: §2 매핑 테이블에 Codex 컬럼 추가(light=gpt-5-mini / standard=gpt-5-codex / advanced=gpt-5.1-codex-max), §공식 모델 목록에 Codex 행, §4 플랫폼 감지 분기에 AGENTS.md → Codex, §5 갱신 가이드라인에 Codex 변경 빈도 주석, §변경이력에 v1.2 행.
- **완료 기준**: `grep -c '| Codex |' opal/core/references/opal-model-mapping.md` ≥ 1 (공식 모델 목록 + 매핑 테이블 헤더). 매핑 테이블에 4개 컬럼(Claude/Gemini/OpenAI/Codex). 변경이력 표 v1.2 행 존재.
- **테스트**: 매핑 테이블 파싱: `grep -E '^\| (light|standard|advanced) \|' | awk -F'|' '{print NF}'` 결과가 모두 6 (앞뒤 빈칸 포함, 4개 데이터 컬럼).
- **의존**: 없음.

### Step 3: opal/core/mcps/*.json platforms 배열에 codex 추가

- [x] 완료
- **파일**: `opal/core/mcps/*.json` (해당하는 모든 파일)
- **작업 내용**: 각 파일의 `platforms` 배열에 `"codex"` 추가. 조건: `install_type == "config_merge"` AND `config.command` basename ∈ {npx, npm, node, python3, python}. 조건 미달 항목은 무변경.
- **대상 사전 식별 명령 (편집 전 실행 필수 — QA-PLAN Minor-2 반영)**:
  ```bash
  python3 -c "import json,glob,os; W={'npx','npm','node','python3','python'}; print('\n'.join(f for f in sorted(glob.glob('opal/core/mcps/*.json')) if (d:=json.load(open(f))).get('install_type')=='config_merge' and os.path.basename((d.get('config') or {}).get('command') or '') in W))"
  ```
  실행 결과(대상 파일 목록)를 편집 전 확인하고, 동일 집합에만 `"codex"`를 추가한다.
- **완료 기준**: (a) 대상 *.json 파일들에서 `platforms` 배열 길이가 1씩 증가하고 `"codex"`가 포함된다. (b) JSON 유효성 유지. (c) 사전 식별 명령 결과 집합 = 실제 편집 파일 집합.
- **테스트**: `python3 -c "import json,glob; [print(f, json.load(open(f))['platforms']) for f in glob.glob('opal/core/mcps/*.json')]"` 출력에 codex 포함 여부 확인.
- **의존**: 없음.

### Step 4: docs/PROJECT.md 플랫폼 독립성 문장 갱신

- [x] 완료
- **파일**: `docs/PROJECT.md`
- **작업 내용**: §프로젝트 원칙 #3 (L17) 문장에서 "Claude Code, Cursor, Gemini 등" → "Claude Code, Cursor, Gemini, Codex 등"로 변경. 변경이력 표가 없는 파일이므로 별도 행 추가 없음.
- **완료 기준**: `grep -c 'Codex' docs/PROJECT.md` ≥ 1, 문장 위치는 L17.
- **테스트**: `grep -n 'Claude Code, Cursor, Gemini, Codex 등' docs/PROJECT.md`가 정확히 1줄 매칭.
- **의존**: 없음.

### Step 5: opal/core/AGENT.md 자동 관리 절에 Codex 스킵 단락 추가

- [x] 완료
- **파일**: `opal/core/AGENT.md`
- **작업 내용**: Cursor 절(L276-278) 직후에 `### Codex — 자동 삽입 스킵` 단락 추가, §프로젝트 컨텍스트(L294)에 `AGENTS.md`(Codex) 추가, §변경이력에 v2.8 행 추가.
- **완료 기준**: `grep -c '### Codex — 자동 삽입 스킵' opal/core/AGENT.md` == 1, 변경이력 v2.8 행 존재, 프로젝트 컨텍스트 L294 줄에 `AGENTS.md(Codex)` 등장.
- **테스트**: `grep -n 'Codex' opal/core/AGENT.md` 출력이 (a) Step 1 문구·(b) Codex 절 헤더·(c) 프로젝트 컨텍스트·(d) 변경이력 v2.8 — 4건 이상.
- **의존**: 없음.

### Step 6: install-mac.sh — Codex 통합 함수 + 흐름 연결

- [x] 완료
- **파일**: `scripts/install-mac.sh`
- **작업 내용**:
  1. 헤더 변경이력에 v2.6 행 추가(§3.3 U-1 (1)).
  2. `install_codex_agents()` 함수 신설 — `~/.opal/agents/*/AGENT.md` → `~/.codex/agents/<name>.toml` 변환 (TOML 필수 3필드 + model 매핑 + AUTO-GENERATED 헤더 + user-managed 가드). `install_gemini_agents()` 직후(L658 근처)에 위치.
  3. `emit_platform_agent_adapter()` 의 `mapping` dict(L548-552)에 `'codex'` 행 추가 — Codex 모델 매핑 SSOT 보존(install_codex_agents가 cross-reference).
  4. `install_opal()`(L890-924) 부트스트래퍼 블록에 `install_opal_section ... codex-bootstrap.md ... ~/.codex/AGENTS.md "Codex"` 추가 + 어댑터 블록에 `install_codex_agents` 추가.
  5. `install_mcp()`(L1180~) switch에 `codex)` 케이스 추가 — `find_cli_bin codex` 검출 → `install_mcp_cli "$bin" "" "$name" ...`(scope 플래그 빈 문자열).
  6. `show_menu()`(L118) 메뉴 [2] 안내 문구 갱신.
  7. `print_summary()`(L1287)에 `Codex MCP                    codex mcp add (CLI 등록)` 행 추가.
- **완료 기준**: (a) `bash -n scripts/install-mac.sh` 문법 통과. (b) `grep -c 'install_codex_agents' scripts/install-mac.sh` ≥ 3(정의 1 + 호출 1 + 헤더 변경이력 1). (c) `grep -c 'codex)' scripts/install-mac.sh` ≥ 1 (install_mcp switch). (d) `grep -c "'codex':" scripts/install-mac.sh` ≥ 1 (emit_platform_agent_adapter mapping).
- **테스트**: shellcheck 통과(가능 시). `bash scripts/install-mac.sh` 비대화형 모드(`OPAL_AUTO_INSTALL=1`)로 dry-run 시 Codex CLI 미설치 환경에서 `warn "codex CLI 없음 ..."`이 graceful 출력되고 다른 플랫폼 흐름이 영향받지 않음.
- **의존**: Step 1 (codex-bootstrap.md 존재).

### Step 7: windows.ps1 — Codex 통합 함수 + 흐름 연결

- [x] 완료
- **파일**: `scripts/install/windows.ps1`
- **작업 내용**:
  1. 헤더 변경이력에 v1.6.0 행 추가(§3.3 U-3 (1)).
  2. `Register-Bootstrapper`(L767-823)에 Codex 블록(Install-OpalSection 재사용) 추가.
  3. `Install-OpalMcp`(L1116) switch에 `'codex'` 케이스 추가 — `Get-Command codex` 검출 → `& $codexCli.Source mcp add $name -- ...`(scope 없음).
  4. `Install-PlatformAgents`(L1273-1286) `$platforms` hashtable에 codex 추가(Dst=`~/.codex/agents`, ModelMap=M-5, Format='toml'). 루프 내부에 `Format` 분기 — toml이면 TOML 직렬화, 그 외는 기존 Markdown YAML.
- **완료 기준**: (a) PSScriptAnalyzer 0 Error(가능 시). (b) `Select-String -Path scripts/install/windows.ps1 -Pattern "\.codex\\AGENTS\.md"` ≥ 1. (c) `'codex'` 케이스가 `Install-OpalMcp` switch에 존재. (d) `Install-PlatformAgents`에 `codex` 키 존재.
- **테스트**: Windows VM에서 dry-run 또는 PowerShell 5.1 환경에서 함수 import 후 `Register-Bootstrapper` 호출이 codex 스니펫 없을 때(파일 자체가 신규이므로 Step 1 완료 후) graceful 처리.
- **의존**: Step 1.

### Step 8: linux.sh — 변경이력 1행만 추가 (install-mac.sh 위임으로 codex 자동 상속)

- [x] 완료
- **파일**: `scripts/install/linux.sh`
- **작업 내용**: 헤더 §변경이력 블록(L18-19)에 `v1.1 2026-05-24: Codex CLI 통합은 install-mac.sh 위임 경로로 자동 상속 (별도 코드 변경 없음) (009)` 1줄 추가. 코드 본문 무변경.
- **R-3 AC 충족 근거 (QA-PLAN Major-1 반영)**: `scripts/install/linux.sh:38`은 `exec bash "${INSTALLER}" "$@"`로 install-mac.sh에 모든 인자를 위임한다. Step 6에서 install-mac.sh에 추가되는 codex 분기(`install_opal_section ... codex-bootstrap.md`, `install_codex_agents`, `install_mcp()` 의 `codex)` 케이스)가 linux.sh 실행 경로에서 동일하게 실행된다. 따라서 TASK.md R-3 AC("linux.sh 실행 시 codex CLI가 PATH에 있으면 부트스트래퍼/어댑터/MCP 설치를 수행하고, 없으면 명시적 스킵 메시지 출력")는 linux.sh 자체 코드 변경 없이 위임 경로로 충족된다.
- **완료 기준**:
  - (a) `grep -c 'v1.1 2026-05-24' scripts/install/linux.sh` == 1
  - (b) `bash -n scripts/install/linux.sh` 통과
  - (c) **위임 검증**: `bash scripts/install/linux.sh` 실행 시 install-mac.sh로 exec 위임되어 codex 분기에 도달하는 호출 그래프 확인 (수동 trace 또는 `OPAL_AUTO_INSTALL=1 bash scripts/install/linux.sh`로 dry-run하여 codex 관련 로그 출력 확인). codex CLI 미설치 환경에서는 `warn "codex CLI 없음 ..."` 그라데이션 스킵 메시지가 출력된다.
- **테스트**: `diff -u`로 본문(L21 이하) 무변경 확인. shellcheck 통과. 위 (c) 위임 검증 수동 trace.
- **의존**: Step 6 (install-mac.sh에 codex 분기가 추가되어야 위임 상속이 의미를 가짐 — 의존 명시).

---

## 5. QA 체크리스트

### 5.1 기능 테스트

- [x] **R-1 codex-bootstrap.md**: 파일 존재 + `# === OPAL START ===`/`# === OPAL END ===` 마커 사이에 2줄 부트스트랩 명령 + 변경이력 v1.0 / 2026-05-24 / 태스크 009.
- [x] **R-2 install-mac.sh (a)**: OPAL Bootstrapper 메뉴 실행 시 codex 분기 호출, codex CLI 미설치 환경에서 graceful skip 메시지(`warn "codex CLI 없음 ..."`).
- [x] **R-2 install-mac.sh (b)**: MCP 메뉴 [2] 실행 시 `opal/core/mcps/*.json`의 `platforms`에 `"codex"`가 있는 항목이 codex CLI(설치된 경우)에 등록됨.
- [x] **R-2 install-mac.sh (c)**: `emit_platform_agent_adapter` MODEL_MAP에 `'codex': {...}` 행 존재.
- [x] **R-2 install-mac.sh (d)**: 헤더 §변경이력에 v2.6 / 2026-05-24 / 태스크 009 행.
- [x] **R-3 linux.sh**: 별도 코드 변경 없이 install-mac.sh 위임으로 Codex 분기 자동 상속. 헤더 변경이력에 v1.1 행 추가.
- [x] **R-4 windows.ps1**: Register-Bootstrapper / Install-OpalMcp / Install-PlatformAgents에 codex 분기 존재. codex CLI 미설치 시 graceful warn.
- [x] **R-5 opal-model-mapping.md**: §2 매핑 테이블에 Codex 컬럼 + 3행. §변경이력 v1.2 행.
- [x] **R-6 AGENT.md**: "Codex — 자동 삽입 스킵" 단락 존재 + 사유 명시 + 마커 예시는 Claude 절 마커 블록과 동일 포맷 재사용 가능(추가 코드 블록 생략하고 Claude 절 인용). §변경이력 v2.8 행.
- [x] **R-7 PROJECT.md**: 플랫폼 독립성 문장에 "Codex" 등장.
- [x] **R-8 변경이력 누락 금지**: codex-bootstrap.md/opal-model-mapping.md/opal/core/AGENT.md/install-mac.sh/linux.sh/windows.ps1 모두 변경이력 1행 추가.

### 5.2 일관성 테스트

- [x] **모델 매핑 동기화**: `opal-model-mapping.md` §2 표의 Codex 매핑(gpt-5-mini / gpt-5-codex / gpt-5.1-codex-max)과 `install-mac.sh:emit_platform_agent_adapter()` mapping dict의 codex 행, `install/windows.ps1:Install-PlatformAgents` `$platforms['codex'].ModelMap`가 **3곳 모두 동일**.
- [x] **마커 블록 동일**: codex-bootstrap.md / claude-bootstrap.md / gemini-bootstrap.md의 코드블록 내부 본문(2줄 부트스트랩 명령)이 **문자 동일**.
- [x] **자동 삽입 정책 동기화**: `opal/core/AGENT.md` "프로젝트 부트스트래퍼 자동 관리" 절의 Codex 단락 사유(글로벌 자동 로드)와 PLAN.md §M-2 결정 근거가 일치.
- [x] **함수 시그니처 일관성**: `install_codex_agents()`가 `install_claude_agents()`/`install_cursor_agents()`/`install_gemini_agents()`와 동일한 시그니처(인자 없음, `~/.opal/agents` 디렉토리 부재 시 warn + return).
- [x] **MCP 스코프 처리 일관성**: `install_mcp_cli`의 scope_flag 빈 문자열 처리가 다른 CLI 호출 분기와 충돌하지 않음 — 기존 `"$cli_bin" mcp add $scope_flag "$name"` 라인에서 `$scope_flag`가 빈 문자열일 때 추가 인자가 들어가지 않는지 검증(IFS 분리로 안전).

### 5.3 문서 품질

- [x] 한국어 본문 + 영어 코드/필드명 규칙 준수.
- [x] kebab-case 파일/폴더 네이밍 준수 (codex-bootstrap.md, install_codex_agents 함수명도 일관).
- [x] YAML frontmatter 또는 변경이력 표 포맷이 SSOT(claude-bootstrap.md 등) 패턴과 동일.
- [x] §3.3 핵심 설계의 인라인 인용 — 모든 외부 결정(M-1~M-6)에 공식 URL 또는 백틱 경로:줄번호가 부착되어 있음 (`citation-rules.md` §3.2 인라인 인용 의무).
- [x] [MUST] 인용 — Codex sub-agent 필수 필드(name/description/developer_instructions)가 [MUST] 포맷으로 인용됨 (`citation-rules.md` §2.4).

---

## 6. 리스크 및 대응

| # | 리스크 | 영향 | 대응 |
|---|--------|------|------|
| R-T1 | Codex 모델 ID 변경 — D-16에서 사용자 UI에 `gpt-5.5`·`gpt-5.3-Codex` 등 새 ID 노출. 매핑(M-5)의 light/standard/advanced 모델이 deprecate될 가능성. | OPAL Codex sub-agent의 model 필드가 옛 ID로 굳어 에이전트 실패. | `opal-model-mapping.md` §5에 "Codex 분기마다 점검" 명시. EXECUTE 시 매핑 동기화 검증 항목(§5.2)이 SSOT 한 곳만 갱신해도 install이 그 값을 전파하도록 보장. |
| R-T2 | TOML 직렬화 — Codex sub-agent의 `developer_instructions`가 multiline + 따옴표·백슬래시 포함 시 TOML basic string escape 처리 부재로 파싱 실패 가능. | `~/.codex/agents/<name>.toml`이 Codex 로딩 시 에러. | install_codex_agents의 Python heredoc에서 triple-quoted basic string + `\` 및 `"` escape 적용. 테스트: `python3 -c "import tomllib; tomllib.load(open('~/.codex/agents/foo.toml','rb'))"`로 파싱 검증. |
| R-T3 | `find_cli_bin codex` 폴백 경로 — Codex CLI가 nvm 경로(`~/.nvm/versions/node/*/bin/codex`)에 설치된 사용자 환경이 많음 (캡틴 머신도 동일). PATH 미주입 시 검출 실패. | MCP 등록·로그에서 codex 분기가 항상 graceful skip. | `find_cli_bin codex "$USER_HOME/.nvm/versions/node/*/bin/codex" "/opt/homebrew/bin/codex" "/usr/local/bin/codex"` — nvm 와일드카드 폴백을 fallback_paths에 명시. shell `case`의 glob 확장 검증 필요. |
| R-T4 | Codex의 mcp_servers 키와 OPAL `opal/core/mcps/*.json`의 `config` 키 매핑 — Codex는 `command`/`args`/`url`/`enabled`/`enabled_tools`/`env`만 인식(D-14). OPAL JSON에 다른 키가 있으면 `codex mcp add`가 무시하거나 거부할 가능성. | 일부 MCP가 Codex에서 동작 실패. | install_mcp_cli는 이미 `command`와 `args[]`만 CLI 인자로 전달하므로 영향 없음(다른 키는 config_merge 폴백 경로에서만 사용). 검증: MCP 등록 후 `codex mcp list`로 확인. |
| R-T5 | 용어 일관성(`citation-rules.md` §7) — TASK.md D-7이 "`opal/AGENT.md` (L250~289)"로 표기하나 실제 파일은 `opal/core/AGENT.md` (1.2 D-8 보정). PROJECT.md / AGENT.md / PLAN.md 사이에 경로 표기 혼선 가능. | EXECUTE 워커가 잘못된 파일을 수정할 위험. | PLAN.md §1.2 표에 정확 경로(`opal/core/AGENT.md`)와 줄번호(`:250-289`) 명시. EXECUTE Step 5에서 동일 경로를 인용. |

---

## 7. 남은 미확정 사항

본 PLAN 단계에서 M-1~M-6 모두 결정 완료. EXECUTE 단계에서 추가 결정 필요 사항 없음.

단, 다음 두 항목은 EXECUTE 후 검증 단계(QA)에서 실측 필요:

- **Codex Plugin 등록 가능성** — `codex plugin` 마켓플레이스 시스템(D-17)이 OPAL을 third-party plugin으로 등록할 수 있는지. 현재 본 PLAN은 sub-agent + MCP + 부트스트래퍼 3축만 다루고 plugin 등록은 범위 외(별도 태스크 후보).
- **Codex sub-agent 실제 invocation 검증** — `codex` 세션에서 "use the opal-pilot-project agent" 자연어로 spawn 되는지 캡틴 머신 1회 실측 필요(D-15 §Invocation — "users invoke subagents through natural language requests"). EXECUTE 단계가 아닌 별도 검증 세션.

---

## 8. 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-05-24 | 초기 작성 — M-1~M-6 결정 + 8 Step 실행 체크리스트 (009) |
| v1.1 | 2026-05-24 | QA-PLAN 보강 반영 — Step 8 R-3 AC 충족 근거 + 위임 검증 완료 기준 추가 (Major-1), Step 3 mcps/*.json 사전 식별 명령 추가 (Minor-2) (009) |
