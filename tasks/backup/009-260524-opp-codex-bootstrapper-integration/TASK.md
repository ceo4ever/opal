# TASK: Codex CLI OPAL 프레임워크 통합

> 작성일: 2026-05-24 | 작업 유형: 신규 | 적용 스킬: opp | 모드: semi-agentic
> 입력: 사용자 요청 "codex 에서도 opal framework가 활성화 되게 구현해줘"
> 출력: TASK.md

## 작업 목표

OpenAI Codex CLI 환경에서도 OPAL 프레임워크가 활성화되도록 부트스트래퍼·sub-agent 어댑터·MCP 등록·모델 매핑을 추가하여, 기존 Claude Code / Cursor / Antigravity(Gemini) 3개 플랫폼과 동등한 4번째 통합 플랫폼으로 Codex를 편입한다.

## 배경

OPAL은 "플랫폼 독립성"을 핵심 원칙으로 하여 Claude Code, Cursor, Antigravity(Gemini) 3개 플랫폼에 부트스트래퍼 + sub-agent 어댑터 + MCP 등록 + 모델 매핑 패턴으로 통합되어 있다. 사용자(캡틴) PC에 OpenAI Codex CLI(`~/.codex/`)가 이미 설치되어 있으나, 현재 OPAL은 Codex 통합을 제공하지 않아 Codex 세션에서 OPAL 에이전트(알투)가 자동 활성화되지 않는다. 이를 해소하여 캡틴이 어느 CLI에서든 OPAL을 사용할 수 있도록 한다.

## 배경 분석 (대화에서 도출)

### 현재 OPAL 플랫폼 통합 매트릭스

| 축 | Claude Code | Cursor | Antigravity(Gemini) | Codex (대상) |
|----|------------|--------|---------------------|--------------|
| 부트스트래퍼 진입점 | `~/.claude/CLAUDE.md` (마커 삽입) | `~/.cursor/rules/000-opal-agent.mdc` | `~/.gemini/GEMINI.md` (마커 삽입) | **PLAN 조사** |
| 부트스트래퍼 소스 | `opal/bootstrapper/claude-bootstrap.md` | `opal/bootstrapper/cursor-bootstrap.mdc` | `opal/bootstrapper/gemini-bootstrap.md` (+`gemini-hardening.md`) | **신규 필요** |
| Sub-agent 어댑터 디렉토리 | `~/.claude/agents/` | `~/.cursor/agents/` | ❌ 미지원 (출처 명시) | **PLAN 조사** |
| MCP 등록 방식 | `claude mcp add` CLI | `~/.cursor/settings.json` | gemini config | **PLAN 조사** |
| 권한/하드닝 | `install_claude_permissions()` | - | `install_gemini_hardening()` | **PLAN 결정** |
| 모델 매핑 | haiku/sonnet/opus | inherit | gemini-2.5-flash-lite/flash/pro | **PLAN 확정** |
| 프로젝트 자동 삽입 | 스킵 (글로벌 install이 처리) | 스킵 (`alwaysApply: true`) | 수행 (Gemini 글로벌 진입점 한정) | **PLAN 결정** |

### 캡틴 PC ~/.codex/ 현황

- `~/.codex/config.toml`: model = "gpt-5.1-codex-max", model_reasoning_effort = "medium" 설정 존재
- `~/.codex/skills/`, `~/.codex/plugins/`: 디렉토리 존재하나 사용자 콘텐츠 없음
- `~/.codex/` 최상단에 `*.md` 파일(AGENTS.md / instructions.md 등) 부재
- 기존 진입점(`~/.claude/CLAUDE.md` 등)과 같은 자동 로드 파일 위치가 공식 문서 조사로 확정 필요

### 영향 받는 파일 (예상 범위)

| # | 파일 | 변경 유형 | 비고 |
|---|------|----------|------|
| F-1 | `opal/bootstrapper/codex-bootstrap.md` | 신규 | Claude/Gemini 패턴 준용 |
| F-2 | `scripts/install-mac.sh` | 수정 | `install_codex_bootstrap()` / `install_codex_agents()` / `install_codex_config()` / `install_codex_permissions()`(필요 시) 함수 신설 + main install 흐름 호출 + MCP 메뉴 codex 분기 + `emit_platform_agent_adapter()` codex 분기 |
| F-3 | `scripts/install/linux.sh` | 수정 | Codex Linux 지원 여부 반영 |
| F-4 | `scripts/install/windows.ps1` | 수정 | Codex Windows 지원 여부 반영 |
| F-5 | `opal/core/references/opal-model-mapping.md` | 수정 | codex 컬럼 추가 (light/standard/advanced → gpt-5.x 모델 ID) |
| F-6 | `opal/AGENT.md` | 수정 | "프로젝트 부트스트래퍼 자동 관리" 절(L250~289)에 Codex 정책 추가 |
| F-7 | `docs/PROJECT.md` | 수정 | 지원 플랫폼 목록에 Codex 추가 |
| F-8 | (옵션) `~/.codex/AGENTS.md` 또는 동등 파일 | install 산출물 | install-mac.sh가 마커 영역에 삽입 |

## 확정된 설계 방향 (대화에서 합의)

1. **통합 범위 4종 모두 수행** — 부트스트래퍼(필수) + Sub-agent 어댑터 + MCP 등록 + 모델 매핑. 단, Sub-agent / MCP는 Codex 플랫폼이 해당 기능을 지원하는 경우에 한정 (PLAN 조사 후 미지원 시 명시적 스킵 메시지로 처리).
2. **OS 지원 3종 모두** — macOS / Linux / Windows 동시 진행. 각 OS에서 Codex CLI 미설치 시 graceful skip 처리 (기존 Claude/Cursor/Gemini와 동일한 `find_cli_bin` 패턴 준용).
3. **기존 어댑터 계층 패턴 준수** — `emit_platform_agent_adapter()` 분기 확장으로 처리. 새 분기를 install 함수 내부에 격리하고, 프로젝트 SSOT(`opal-harness.md`, `opal-pm.md`)는 플랫폼 분기를 포함하지 않는다.
4. **PLAN 단계에서 조사 후 결정 (디스패치 시 워커에게 조사 의무 명시)** — Codex CLI 진입점·sub-agent 지원·MCP 지원·프로젝트 자동 삽입 정책은 PLAN 워커가 Codex CLI 공식 문서를 조사하여 확정한다.

## 요구사항

- [ ] **R-1 codex-bootstrap.md 신규 작성**
  - 무엇을: `opal/bootstrapper/codex-bootstrap.md` 파일 생성 (Claude/Gemini bootstrap과 동일한 OPAL 마커 영역 + 변경이력 표 포함)
  - 어디에: `opal/bootstrapper/codex-bootstrap.md`
  - 왜: 기존 부트스트래퍼 SSOT 패턴 일관성 유지 (`claude-bootstrap.md`, `gemini-bootstrap.md` 참조)
  - AC: 파일이 존재하고, `## OPAL AI Agent — 필수 부트스트랩` 마커 블록(`# === OPAL START ===` / `# === OPAL END ===`)을 포함하며, "변경이력" 표에 v1.0 / 2026-05-24 / 태스크 009 행이 있다

- [ ] **R-2 install-mac.sh — Codex 통합 함수 신설**
  - 무엇을: `install_codex_bootstrap()`, `install_codex_agents()` 함수를 신설하고 main install 흐름의 OPAL Bootstrapper 메뉴([1])에서 호출. MCP 메뉴([2])에서 `codex` 케이스 추가. `emit_platform_agent_adapter()`에 `codex` 분기 추가
  - 어디에: `scripts/install-mac.sh`
  - 왜: macOS 진입점에서 Codex 자동 설치 제공
  - AC: (a) OPAL Bootstrapper 메뉴 실행 시 codex 분기가 호출되고, codex CLI 미설치 시 graceful skip 메시지 출력. (b) MCP 메뉴 [2] 실행 시 codex가 등록 대상 플랫폼 목록에 포함. (c) `emit_platform_agent_adapter` MODEL_MAP 딕셔너리에 `'codex': {...}` 행이 추가되어 있다. (d) 변경이력 헤더 주석에 v_.x / 2026-05-24 / 태스크 009 행 추가

- [ ] **R-3 scripts/install/linux.sh — Codex 분기 추가**
  - 무엇을: Linux 설치 흐름에 codex 통합 호출 추가 (install-mac.sh의 codex 함수를 호출 가능한 형태로 위임하거나 동등한 Bash 로직 추가)
  - 어디에: `scripts/install/linux.sh`
  - 왜: 캡틴이 확정한 OS 3종 동시 지원 (확정된 설계 방향 §2)
  - AC: linux.sh 실행 시 codex CLI가 PATH에 있으면 부트스트래퍼/어댑터/MCP 설치를 수행하고, 없으면 명시적 스킵 메시지 출력. 변경이력 주석에 태스크 009 행 추가

- [ ] **R-4 scripts/install/windows.ps1 — Codex 분기 추가**
  - 무엇을: Windows 설치 흐름에 codex 통합 호출 추가 (PowerShell 함수로 신설)
  - 어디에: `scripts/install/windows.ps1`
  - 왜: 캡틴이 확정한 OS 3종 동시 지원 (확정된 설계 방향 §2)
  - AC: windows.ps1 실행 시 codex CLI가 PATH에 있으면 부트스트래퍼/어댑터/MCP 설치를 수행하고, 없으면 명시적 스킵 메시지 출력. 변경이력 주석에 태스크 009 행 추가

- [ ] **R-5 opal-model-mapping.md — codex 컬럼 추가**
  - 무엇을: `opal/core/references/opal-model-mapping.md`의 플랫폼 매핑 테이블에 codex 열 추가 (light/standard/advanced 3레벨)
  - 어디에: `opal/core/references/opal-model-mapping.md`
  - 왜: 워커 디스패치 시 codex 환경에서 정확한 모델 ID 선택 (확정된 설계 방향 §1 모델 매핑 항목)
  - AC: codex 매핑 행이 추가되어 있고, 각 레벨에 gpt-5 계열 모델 ID(또는 `inherit`)가 명시되어 있다. 변경이력 표에 태스크 009 행 추가

- [ ] **R-6 opal/AGENT.md — 프로젝트 부트스트래퍼 자동 관리 절 갱신**
  - 무엇을: "프로젝트 부트스트래퍼 자동 관리" 절(L250~289)에 Codex 정책 단락 추가 — PLAN에서 결정된 자동 삽입/스킵 정책 명시
  - 어디에: `opal/AGENT.md` "프로젝트 부트스트래퍼 자동 관리" 섹션
  - 왜: 프로젝트 단위 마커 삽입 정책 SSOT 갱신
  - AC: "Codex —" 절이 추가되어 있고, 자동 삽입 수행/스킵 정책이 명시되며, 마커 블록 예시(Claude 절의 마커 동일 포맷)가 포함된다. 변경이력 표에 태스크 009 행 추가

- [ ] **R-7 docs/PROJECT.md — 지원 플랫폼 목록 갱신**
  - 무엇을: 플랫폼 또는 어댑터 관련 문장/표에 Codex 추가
  - 어디에: `docs/PROJECT.md`
  - 왜: PM/워커가 통합 대상 플랫폼을 4종으로 인식
  - AC: PROJECT.md에서 플랫폼 독립성/지원 플랫폼을 다루는 문장 또는 표에 "Codex" 단어가 등장한다. 변경이력 표가 있는 경우 태스크 009 행 추가

- [ ] **R-8 변경이력 누락 금지**
  - 무엇을: 위 R-1~R-7에서 변경된 모든 스킬/에이전트/참조 문서의 변경이력 표에 행 추가
  - 어디에: 수정된 모든 문서의 변경이력 섹션
  - 왜: 프로젝트 금지사항 "변경이력 누락 금지" (`.opal/AGENT.md` 금지사항 §2)
  - AC: 수정된 문서마다 변경이력 표 또는 헤더 주석에 `2026-05-24 (KST) / 태스크 009 / 변경 요약` 행이 추가되어 있다

## 미확정 사항 (PLAN에서 결정)

| # | 항목 | 조사 대상 | 결정 방식 |
|---|------|----------|----------|
| M-1 | Codex CLI 글로벌 instructions 진입점 | OpenAI Codex CLI 공식 문서, `codex --help`, `~/.codex/` 표준 구조 | PLAN 워커가 공식 출처를 인용하여 확정 (`~/.codex/AGENTS.md` / `instructions.md` / `config.toml` 항목 / 그 외) |
| M-2 | 프로젝트 단위 부트스트래퍼 자동 삽입 정책 | Codex가 글로벌 vs 프로젝트 AGENTS.md를 어떻게 우선 적용하는지 | M-1 결과에 따라 결정. 글로벌 진입점이 충분하면 스킵, 프로젝트 우선이면 자동 삽입 |
| M-3 | Codex sub-agent 지원 여부 | Codex CLI 공식 문서, plugins / agents 디렉토리 명세 | 지원 → `install_codex_agents()`가 어댑터 생성 / 미지원 → 명시적 스킵 메시지로 처리 (Antigravity 패턴 준용, 출처 URL 명시) |
| M-4 | Codex MCP 등록 방식 | Codex MCP 지원 여부, `codex mcp` 류 명령 또는 config.toml 설정 항목 | 지원 시 install-mac.sh MCP 메뉴에 codex 케이스 추가 / 미지원 시 메뉴에서 codex 옵션 비활성화 + 사유 명시 |
| M-5 | Codex 모델 매핑 정확한 ID | 캡틴 PC `~/.codex/config.toml` 현재 값(gpt-5.1-codex-max) + 공식 문서의 light/standard/advanced 대응 모델 | PLAN 워커가 조사하여 light/standard/advanced 3레벨 모델 ID 확정. 불확실 시 `inherit` 폴백 |
| M-6 | Codex 권한/하드닝 필요성 | Codex가 외부 디렉토리(`~/.opal/`) 접근에 별도 권한을 요구하는지 | 요구 시 `install_codex_permissions()` 신설, 불필요 시 생략 |

## 제약 조건

- **배포 경계 준수**: `~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스(`opal/`, `scripts/`)를 수정한 뒤 install로 재배포한다 (`.opal/AGENT.md` 금지사항 §1)
- **변경이력 누락 금지**: 스킬·에이전트·참조 문서 수정 시 변경이력 표 행 추가 의무 (`.opal/AGENT.md` 금지사항 §2)
- **하드코딩된 플랫폼 분기 추가 금지**: Claude/Cursor/Gemini/Codex 분기는 어댑터 계층(install·plugin)에서만 수행 (`.opal/AGENT.md` 금지사항 §3)
- **하네스 우회 금지**: Guards/Gates를 PM 임의 판단으로 건너뛰지 않는다 (`.opal/AGENT.md` 금지사항 §4)
- **사용자 승인 없는 코드 생성·수정 금지** — 산출물 문서(.md) 작성·분석은 허용, 코드/설정 변경은 명시 승인 필요 (현재 `//opp` 호출로 태스크 진입 승인 완료, 단 EXECUTE 직전 PLAN 승인 필요)
- **기존 통합 패턴 일관성**: Claude/Cursor/Gemini 통합 함수 시그니처·로그 형식·에러 처리 패턴을 codex에도 동일 적용
- **출처 명시 의무**: M-1~M-6 조사 결과는 공식 문서 URL을 인용하여 PLAN.md에 기록 (`citation-rules.md` §2 준수)

## 기술 스택

- **Bash** — `scripts/install-mac.sh`, `scripts/install/linux.sh` (기존 함수 패턴: `install_claude_bootstrap`, `emit_platform_agent_adapter`)
- **PowerShell** — `scripts/install/windows.ps1`
- **Python (embedded)** — `install-mac.sh` 내 `emit_platform_agent_adapter()` heredoc Python 블록 (MODEL_MAP 딕셔너리 확장)
- **Markdown / YAML frontmatter** — `opal/bootstrapper/codex-bootstrap.md`, `opal-model-mapping.md`, `AGENT.md`

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | OPAL Bootstrapper SSOT (Claude) | `opal/bootstrapper/claude-bootstrap.md` | codex-bootstrap.md 작성 시 동일 패턴 적용 |
| D-2 | 소스 | OPAL Bootstrapper SSOT (Gemini) | `opal/bootstrapper/gemini-bootstrap.md` | 강제 부트스트랩 패턴 참조 (v1.1) |
| D-3 | 소스 | install 메인 스크립트 | `scripts/install-mac.sh` | `install_claude_bootstrap`, `install_gemini_config`, `emit_platform_agent_adapter` 등 함수 패턴 참조 |
| D-4 | 소스 | install Linux 진입점 | `scripts/install/linux.sh` | Linux 분기 추가 위치 확인 |
| D-5 | 소스 | install Windows 진입점 | `scripts/install/windows.ps1` | Windows 분기 추가 위치 확인 |
| D-6 | 설계 | 모델 매핑 SSOT | `opal/core/references/opal-model-mapping.md` | codex 컬럼 추가 대상 |
| D-7 | 설계 | OPAL AGENT.md | `opal/AGENT.md` (L250~289) | "프로젝트 부트스트래퍼 자동 관리" 절 Codex 정책 추가 위치 |
| D-8 | 기획 | 프로젝트 정의 | `docs/PROJECT.md` | 지원 플랫폼 목록 갱신 대상 |
| D-9 | 외부 | OpenAI Codex CLI 공식 문서 | [Codex CLI](https://developers.openai.com/codex/cli) (또는 GitHub 리포지토리) | M-1~M-6 조사 출처 — PLAN 워커가 정확한 URL 확정 |
| D-10 | 환경 | 캡틴 PC Codex 설정 | `~/.codex/config.toml` | 현재 사용 모델(gpt-5.1-codex-max) 확인 — M-5 모델 매핑 기초 자료 |
| D-11 | 설계 | 인용 규칙 SSOT | `opal/core/references/harness/citation-rules.md` | PLAN/EXECUTE 산출물 작성·검증 시 준수 |
| D-12 | 설계 | OPAL 하네스 SSOT | `opal/core/references/opal-harness.md` | Guards / Gates / 디스패치 의무 준수 |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §2 참조.
