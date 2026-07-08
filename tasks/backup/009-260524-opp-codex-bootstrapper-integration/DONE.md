# DONE: Codex CLI OPAL 프레임워크 통합

> 완료일: 2026-05-24 22:40 | 적용 스킬: opp | 모드: semi-agentic
> 태스크 폴더: `tasks/009-260524-opp-codex-bootstrapper-integration/`

---

## 1. 태스크 요약

OpenAI Codex CLI를 OPAL의 4번째 통합 플랫폼(Claude Code · Cursor · Antigravity Gemini에 이어)으로 편입했다. 부트스트래퍼·sub-agent 어댑터·MCP 등록·모델 매핑 4축에 걸쳐 코드 변경 + SSOT 문서 정합성을 동시 처리했고, install-mac.sh 한 곳에 codex 분기를 격리하여 linux.sh는 위임으로 자동 상속하는 구조로 설계했다.

| 영역 | 결정/변경 | 출처 |
|------|----------|------|
| 글로벌 진입점 | `~/.codex/AGENTS.md` + OPAL 마커 (idempotent) | developers.openai.com/codex/guides/agents-md |
| 프로젝트 자동 삽입 | 스킵 (Claude/Cursor 패턴) — 글로벌이 항상 먼저 로드 | 동일 출처 §Load Sequence |
| Sub-agent | 지원 — `~/.codex/agents/<name>.toml` (필수: name/description/developer_instructions) | developers.openai.com/codex/subagents |
| MCP 등록 | `codex mcp add` CLI (scope 플래그 없음) | `codex mcp --help` + config-reference |
| 모델 매핑 | light=gpt-5-mini / standard=gpt-5-codex / advanced=gpt-5.1-codex-max | config-reference §model + 캡틴 환경 |
| 권한/하드닝 | 불필요 (`install_codex_permissions()` 신설 안 함) | config-reference §sandbox_mode |

## 2. 산출물 목록

### 2.1 본 태스크 산출물

| 파일 | 역할 |
|------|------|
| `tasks/009-260524-opp-codex-bootstrapper-integration/TASK.md` | 요구사항 R-1~R-8 + 미확정 M-1~M-6 + 관련 문서 D-1~D-12 |
| `tasks/009-260524-opp-codex-bootstrapper-integration/PLAN.md` (v1.1) | M-1~M-6 결정 + 8 Step / 3 Phase 실행 체크리스트 + QA 보강 반영 |
| `tasks/009-260524-opp-codex-bootstrapper-integration/QA-PLAN.md` | CONDITIONAL_PASS — 30/33, Major-1 + Minor-2 PM 직접 반영 |
| `tasks/009-260524-opp-codex-bootstrapper-integration/QA-EXECUTE.md` | CONDITIONAL_PASS — 24/25, Minor 1건 PM 분석 오류로 판정 |
| `tasks/009-260524-opp-codex-bootstrapper-integration/AGENTIC-LOG.md` | semi-agentic 모드 EXECUTE 이후 PM 자율 판단 + 2건 EXECUTE 정정 기록 |
| `tasks/009-260524-opp-codex-bootstrapper-integration/STATE.md` | 파이프라인 현황판 (state-tool 관리, 20행) |
| `tasks/009-260524-opp-codex-bootstrapper-integration/DONE.md` | 본 완료 보고서 |

### 2.2 변경된 프레임워크 산출물 (배포 대상)

| 파일 | 핵심 변경 |
|------|---------|
| `opal/bootstrapper/codex-bootstrap.md` (신규) | Claude/Gemini 패턴 동일 OPAL 마커 본문 2줄 + 변경이력 v1.0 |
| `opal/core/AGENT.md` | "Codex — 자동 삽입 스킵" 단락 추가 + 프로젝트 컨텍스트 갱신 + 변경이력 v2.8 |
| `opal/core/references/opal-model-mapping.md` | §2 Codex 컬럼 추가(3행) + 플랫폼 감지 + 갱신 가이드 + 변경이력 v1.2 |
| `opal/core/mcps/context7.json` / `playwright.json` / `sequential-thinking.json` / `shadcn.json` | `platforms` 배열에 `"codex"` 추가 (사전 식별 4종 = 편집 4종) |
| `docs/PROJECT.md` (L17) | 플랫폼 독립성 문장에 "Codex" 추가 |
| `scripts/install-mac.sh` (v2.6 → v2.6.2) | `install_codex_agents()` 신설 + `emit_platform_agent_adapter` codex 매핑 + `install_opal`/`install_mcp` codex 분기 + show_menu/print_summary 갱신 + 2건 EXECUTE 정정 |
| `scripts/install/windows.ps1` (v1.8.0) | Register-Bootstrapper / Install-OpalMcp / Install-PlatformAgents codex 분기 + TOML 직렬화 |
| `scripts/install/linux.sh` (v1.1) | 변경이력 1행만 추가 (코드 본문 무변경, install-mac.sh 위임 자동 상속) |

### 2.3 캡틴 PC 배포 확인 (install-mac.sh 실행 결과)

| 산출물 | 경로 | 상태 |
|--------|------|------|
| Codex 부트스트래퍼 | `~/.codex/AGENTS.md` | ✅ OPAL 마커 정상 삽입 |
| Codex sub-agent 어댑터 | `~/.codex/agents/*.toml` | ✅ 13개 정상 생성 |
| Codex MCP | `codex mcp add` 등록 | ✅ install_mcp 흐름 동작 |

## 3. 결과 검증

### 3.1 R-1 ~ R-8 AC 충족 결과

| 요구사항 | AC 충족 | 검증 위치 |
|---------|--------|---------|
| R-1 codex-bootstrap.md 신규 | ✅ 3/3 | `opal/bootstrapper/codex-bootstrap.md` + 코드블록 본문 + 변경이력 v1.0 |
| R-2 install-mac.sh Codex 통합 | ✅ 4/4 (a/b/c/d) | install_codex_agents + MODEL_MAP codex + install_mcp codex 케이스 + 변경이력 v2.6/v2.6.1/v2.6.2 |
| R-3 linux.sh Codex 분기 (위임 상속) | ✅ 2/2 | linux.sh 코드 본문 무변경 + 변경이력 v1.1 + exec 위임 |
| R-4 windows.ps1 Codex 분기 | ✅ 4/4 | Register-Bootstrapper + Install-OpalMcp + Install-PlatformAgents codex + 변경이력 v1.8.0 |
| R-5 opal-model-mapping.md codex 컬럼 | ✅ 3/3 | §2 Codex 컬럼(gpt-5-mini/gpt-5-codex/gpt-5.1-codex-max) + §공식 모델 목록 + 변경이력 v1.2 |
| R-6 AGENT.md Codex 스킵 단락 + v2.8 | ✅ 3/3 | "Codex — 자동 삽입 스킵" 단락 + 프로젝트 컨텍스트 + 변경이력 v2.8 |
| R-7 docs/PROJECT.md 플랫폼 목록 | ✅ 1/1 | L17 "Claude Code, Cursor, Gemini, Codex 등" |
| R-8 변경이력 누락 금지 | ✅ 6/6 | 6개 파일 모두 변경이력 행 추가 |

**총 AC 결과**: 26/26 충족.

### 3.2 QA 결과

| QA | Verdict | Blocker | Major | Minor |
|----|---------|---------|-------|-------|
| QA-PLAN | CONDITIONAL_PASS | 0 | 1 → PM 즉시 보강 | 2 → PM 즉시 보강 |
| QA-EXECUTE | CONDITIONAL_PASS | 0 | 0 | 1 → PM 분석 오류 판정 (PowerShell `-replace`는 정상 동작) |

### 3.3 PM 의사결정 (AGENTIC-LOG)

| # | 결정 | 근거 |
|---|------|------|
| D-1 | QA-EXECUTE Minor M-1 (windows.ps1 escape) 무효 판정 | PowerShell 단일 따옴표 `'\\'` = 2자 literal. 정규식 패턴 `\\` → 단일 `\` 매칭, .NET 치환 문자열 `\\` → literal 2자. `\` → `\\` 의도대로 동작 |
| D-2 | EXECUTE 정정 #1: install-mac.sh L752 docstring raw string 변경 (v2.6.1) | 캡틴 install 실행 시 SyntaxWarning 13회 — Python 3.12+ invalid escape `\ `. 함수 로직 무변경, 미래 호환성 확보 |
| D-3 | EXECUTE 정정 #2: install-mac.sh print_summary Codex 부트스트래퍼 행 추가 (v2.6.2) | 캡틴 install 결과 표 일관성 결손 — 부트스트래퍼 행이 Claude/Cursor/Gemini 패턴과 불일치. PLAN §3.3 U-1 (7) 설계 누락 root cause |

## 4. 리스크 및 잔여 미해결

### 4.1 PLAN §6 리스크 5건 — 대응 결과

| # | 리스크 | 대응 결과 |
|---|--------|----------|
| R-T1 | Codex 모델 ID 변경 빈도 | opal-model-mapping.md §5에 "분기마다 점검" 명시 |
| R-T2 | TOML escape (multiline + 따옴표·백슬래시) | toml_escape 함수 적용 + 샘플 검증 통과 |
| R-T3 | find_cli_bin nvm 폴백 | `~/.nvm/versions/node/*/bin/codex` 와일드카드 폴백 포함 — 캡틴 PC 검출 확인 |
| R-T4 | mcps/*.json 키 매핑 | install_mcp_cli이 command/args만 CLI 인자로 전달 — 영향 없음 |
| R-T5 | 경로 표기 (opal/AGENT.md vs opal/core/AGENT.md) | PLAN §1.2에서 보정 + EXECUTE Step 5 동일 경로 인용 |

### 4.2 잔여 미해결 (별도 후속 태스크 후보)

| # | 항목 | 사유 |
|---|------|------|
| F-1 | **Windows VM 실 환경 dry-run** | 캡틴 macOS 환경 → Codex 통합의 Windows 동작은 정적 분석으로만 확인. 별도 Windows 검증 세션 권장 |
| F-2 | **print_summary 일관성 정리** (전체 플랫폼) | sub-agent 어댑터 행이 Claude/Cursor/Gemini/Codex 모두 누락 — 기존 결함. 일괄 보강 별도 태스크 |
| F-3 | **Codex plugin 등록 가능성** | 본 PLAN §7 명시 — sub-agent + MCP + 부트스트래퍼 외 plugin 마켓플레이스 등록은 범위 외 |
| F-4 | **Codex sub-agent 실제 invocation 검증** | "use the opal-pilot-project agent" 자연어 spawn 1회 실측 — 캡틴이 Codex 세션 사용 시 확인 |
| F-5 | **TASK.md R-1 AC 표현 정정** | QA-EXECUTE Info M-2 — 차후 태스크 정정 권고 (R-1 AC가 마커 블록을 SSOT에 요구한 표현은 부정확) |

## 5. 파이프라인 진행 현황

| # | 단계 | 항목 | 상태 |
|---|------|------|------|
| 1~3 | TASK | 작업 / TASK.md / 사용자 확인 | ✅ |
| 4~11 | PLAN | 작업 / PLAN.md / QA Gate / QA-PLAN / State / PM / State / 사용자 확인 | ✅ |
| 12~18 | EXECUTE | 작업 / QA Gate / QA-EXECUTE / State / PM(auto-pass) / State / 사용자 확인 | ✅ |
| 19~20 | CLOSE | DONE.md / State Gate | ✅ (본 행에서 마감) |

## 6. 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-05-24 22:40 | DONE.md 최초 작성 — 태스크 009 완료 (009) |
