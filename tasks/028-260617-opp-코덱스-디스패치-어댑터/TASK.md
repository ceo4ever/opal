# TASK: Codex 워커 디스패치 어댑터 정합 — agents.md Codex 행 + tool-backed 인라인 주입 + config [agents]

> 작성일: 2026-06-17 | 작업 유형: 개선 | 적용 스킬: opp | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

Codex CLI tool-backed 세션에서 OPAL 워커 디스패치가 실제로 동작하도록 어댑터 계층을 정합한다. 현재 `~/.codex/agents/*.toml`은 공식 스펙에 맞게 생성되지만, tool-backed 세션에서는 이름 기반 호출이 불가(공식 버그 #15250)하므로 PM이 런타임에 워커 AGENT.md를 spawn message에 인라인 주입하는 규칙을 어댑터 문서에 명문화한다.

## 배경

OPAL Codex 어댑터(`install_codex_agents`, install-mac.sh v2.6, 2026-05-24)는 `~/.codex/agents/<name>.toml`을 생성하지만, Codex 0.137.0 tool-backed 세션에서 워커가 이름으로 디스패치되지 않는 문제가 보고됨. 원인 규명을 위해 바이너리·feature·config·공식 문서를 교차 검증한 결과, 어댑터 계층에 Codex 분기가 누락되어 있음이 확인됨.

## 배경 분석 (대화에서 도출)

대화에서 다음을 실측·교차 검증함:

1. **공식 스펙 확인**: `~/.codex/agents/*.toml`(필드 `name`·`description`·`developer_instructions`)은 공식 스펙이 맞음. 개별 등록 불요(자동 로드), config.toml `[agents]`는 개별 등록이 아니라 글로벌 한계치(`max_threads`/`max_depth`/`job_max_runtime_seconds`)만 담음 — `[Codex Subagents](https://developers.openai.com/codex/subagents)`.
2. **증상 원인 = 공식 버그 #15250 (OPEN, 2026-03-20 filed)**: 이름 기반 커스텀 에이전트 호출은 Codex app/CLI/TUI(대화형)에서만 동작하고, tool-backed 세션(모델이 도구로 구동)에는 노출되지 않음. tool-backed에서는 `spawn_agent`의 generic `agent_type`(`default`/`explorer`/`no-apps`) + 수동 오버라이드만 제공 — `[Issue #15250](https://github.com/openai/codex/issues/15250)`.
3. **공식 우회법 = 인라인 주입**: 이슈 본문이 "각 TOML을 직접 읽어 `developer_instructions`를 generic 워커에 주입"을 명시. OPAL PM은 모델이 도구로 자율 디스패치하는 구조이므로 #15250 영향권에 정확히 해당.
4. **OPAL 어댑터 현황**: `agents.md §플랫폼 sub-agent 어댑터 변환 규칙`의 메커니즘 표(line 159)는 "2026-04 기준" Claude/Cursor/Gemini/Antigravity 4개뿐 — install v2.6에서 Codex를 추가했으나 이 어댑터 문서에 Codex 행이 미반영(`opal/core/references/agents.md:159-164`).
5. **인라인 주입은 배포 시점이 아니라 디스패치 런타임 PM 행위**: install은 원본 AGENT.md를 `~/.opal/agents/<name>/`에 배포만 함. PM이 디스패치 순간 그 본문을 읽어 spawn message에 붙이는 것이 인라인 주입.

## 확정된 설계 방향 (대화에서 합의)

1. **`~/.codex/agents/*.toml` 생성 유지** — 스펙 정합·TUI/사람 호출·향후 #15250 수정 대비. (초기 "폐기" 제안은 철회됨)
2. **플랫폼 분기는 core/AGENT.md에 넣지 않는다** — OPAL 헌법(플랫폼 독립) + PM 금지사항(분기는 어댑터 계층에서만). Codex 디스패치 규칙은 `agents.md`(Lazy 로드: 워커 디스패치 직전)에 둔다.
3. **3종 산출물**: ① agents.md 어댑터 표에 Codex 행 추가 + tool-backed 인라인 주입 규칙 명문화, ② install — `.toml` 유지 + config.toml `[agents]` 글로벌 설정 신규 작성(mac + windows.ps1 동기), ③ dispatch-process.md에 Codex 실현 경로 연결.

## 명확화 결과

> TASK 4요소를 잠근다.

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | Codex tool-backed 세션에서 OPAL 워커 디스패치가 동작하도록 어댑터 계층(문서+install)을 정합한다. core/AGENT.md는 불변. | - | #15250 OPEN 상태 (수정 시 재검토) |
| 범위 | **포함**: agents.md Codex 행+인라인 주입 규칙 / dispatch-process.md Codex 경로 / install-mac.sh config `[agents]` 작성 / windows.ps1 동기 / opal-model-mapping.md Codex 컬럼 정합 확인 / 관련 변경이력. **제외**: `.toml` 생성 로직 폐기, core/AGENT.md 분기, multi_agent_v2·external_migration 대응(실험 단계), Claude/Cursor/Gemini 동작 변경. | - | - |
| 제약 | ① core/AGENT.md에 플랫폼 분기 추가 금지(헌법) ② `~/.opal/` 직접 편집 금지 — 프로젝트 소스만 수정 후 install 배포 ③ 문서 변경 시 변경이력 행 추가 의무 ④ 인용 규칙(citation-rules) 준수 | - | PRINCIPLES.md Core Stance, .opal/AGENT.md 금지사항 |
| 완료기준 | 아래 요구사항 AC 전부 충족 + agentic PM Gate All Pass | - | - |

## 요구사항

- [ ] **R-1 agents.md Codex 행**: `agents.md §플랫폼 sub-agent 어댑터 변환 규칙` 메커니즘 표에 Codex 행이 추가되고(메커니즘=tool-backed 인라인 주입/TUI 이름호출, 등록 경로=`~/.codex/agents/{name}.toml`, 공식 문서 링크), frontmatter 변환 표에 Codex model 매핑 행이 존재한다.
  - 무엇을: Codex 행 + 변환 규칙 추가 / 어디에: `opal/core/references/agents.md` §어댑터 규칙 / 왜: Codex 행 누락(확정 방향 §3①) / AC: 표에 Codex 행 존재 + #15250 근거 인용 + tool-backed 인라인 주입 규칙 문단 존재
- [ ] **R-2 인라인 주입 규칙 명문화**: agents.md에 "Codex tool-backed 디스패치 시 PM이 `~/.opal/agents/<name>/AGENT.md` 본문을 `spawn_agent` message에 인라인하고 model을 매핑한다"는 PM 런타임 규칙이 #15250 근거와 함께 기재된다.
  - 무엇을: 인라인 주입 PM 규칙 / 어디에: `agents.md` / 왜: tool-backed 이름호출 불가(#15250) / AC: 규칙 문단에 "런타임 PM 행위 / spawn_agent message 주입 / model 매핑 / #15250 인용"이 모두 명시
- [ ] **R-3 dispatch-process.md 연결**: PM 디스패치 절차 문서에 Codex 실현 경로(인라인 주입)로 가는 1줄 포인터가 추가된다.
  - 무엇을: Codex 경로 포인터 / 어디에: `opal/core/references/pm/dispatch-process.md` / 왜: 디스패치 시점 PM 참조(확정 방향 §3③) / AC: dispatch-process.md에 Codex→agents.md 인라인 주입 참조 라인 존재
- [ ] **R-4 install config [agents]**: `install-mac.sh`가 `~/.codex/config.toml`에 `[agents]` 글로벌 설정(max_threads/max_depth/job_max_runtime_seconds)을 멱등적으로 작성하며, 기존 사용자 설정·MCP 블록을 훼손하지 않는다.
  - 무엇을: config `[agents]` 작성 함수 / 어디에: `scripts/install-mac.sh` / 왜: 글로벌 한계치 미설정(확정 방향 §3②) / AC: install 재실행 시 `[agents]` 블록이 1회만 추가되고 재실행 시 중복 추가 없음(멱등)
- [ ] **R-5 windows.ps1 동기**: Windows 설치 스크립트가 R-4와 동일한 config `[agents]` 작성을 수행한다.
  - 무엇을: config `[agents]` 작성 / 어디에: `scripts/install/windows.ps1` / 왜: 플랫폼 동기 의무 / AC: windows.ps1에 mac과 동등한 `[agents]` 작성 로직 존재
- [ ] **R-6 model-mapping 정합 확인**: `opal-model-mapping.md` Codex 컬럼이 install의 `codex_model_map`과 일치하는지 확인하고, 인라인 주입 시 model 매핑이 이 SSOT를 따른다는 점이 명시된다.
  - 무엇을: Codex model 매핑 정합 / 어디에: `opal/core/references/opal-model-mapping.md` / 왜: 인라인 주입 model 오버라이드 근거 / AC: model-mapping Codex 컬럼 ↔ install codex_model_map 일치 확인 기록
- [ ] **R-7 변경이력**: 수정한 모든 참조 문서(agents.md, dispatch-process.md, opal-model-mapping.md)에 변경이력 행이 추가된다.
  - 무엇을: 변경이력 행 / 어디에: 각 수정 문서 변경이력 표 / 왜: 추적성 의무(.opal/AGENT.md) / AC: 수정 문서마다 028 태스크 변경이력 행 존재

## 제약 조건

- core/AGENT.md(`opal/core/AGENT.md`)에 플랫폼 분기를 추가하지 않는다 (헌법 Core Stance).
- `~/.opal/` 배포 파일을 직접 편집하지 않는다. 프로젝트 소스(`opal/`, `scripts/`)만 수정 후 install로 배포·검증한다.
- `.toml` 생성 로직(`install_codex_agents`)은 폐기하지 않는다.
- 문서 수정 시 변경이력 표 행 추가 의무, 인용 규칙(citation-rules.md) 준수.
- Claude/Cursor/Gemini 어댑터 동작을 변경하지 않는다.

## 기술 스택

- Markdown(참조 문서), Bash(install-mac.sh), PowerShell(windows.ps1), TOML(Codex config/agent 파일)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | agents.md (어댑터 SSOT) | `opal/core/references/agents.md` | 플랫폼 어댑터 변환 규칙 — Codex 행 추가 대상 |
| D-2 | 설계 | dispatch-process.md | `opal/core/references/pm/dispatch-process.md` | PM 디스패치 절차 — Codex 경로 연결 대상 |
| D-3 | 설계 | opal-model-mapping.md | `opal/core/references/opal-model-mapping.md` | Codex model 매핑 SSOT 정합 |
| D-4 | 소스 | install-mac.sh | `scripts/install-mac.sh` | `install_codex_agents`(line 670) + config 작성 추가 |
| D-5 | 소스 | windows.ps1 | `scripts/install/windows.ps1` | Codex 동기 지점(line 1538) |
| D-6 | 설계 | PRINCIPLES.md (헌법) | `opal/core/PRINCIPLES.md` 또는 `~/.opal/PRINCIPLES.md` | 플랫폼 독립 Core Stance 근거 |
| D-7 | 외부 | Codex Subagents 공식 | [Codex Subagents](https://developers.openai.com/codex/subagents) | toml 스펙·`[agents]` 글로벌 설정 |
| D-8 | 외부 | Codex Issue #15250 | [Issue #15250](https://github.com/openai/codex/issues/15250) | tool-backed 이름호출 불가 + 인라인 주입 우회법 근거 |
| D-9 | 외부 | Codex Config Reference | [Config Reference](https://developers.openai.com/codex/config-reference) | config.toml `[agents]` 키 검증 |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §2 참조.
