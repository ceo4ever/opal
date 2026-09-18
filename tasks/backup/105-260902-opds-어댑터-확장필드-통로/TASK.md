# TASK: 플랫폼 sub-agent 어댑터 확장 필드 통로 신설 + effort 첫 적용

> 작성일: 2026-09-02 | 작업 유형: 개선 | 적용 스킬: opds | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

OPAL 에이전트 frontmatter의 확장 필드를 플랫폼 sub-agent로 전달하는 **변환 테이블 통로**를 어댑터에 신설하고, 그 위에 `effort`를 첫 실적용 필드로 태운다.

## 배경

OPAL은 에이전트 정의(`opal/agents/{name}/AGENT.md`)를 install 시점에 플랫폼별 sub-agent 파일로 변환해 배포한다. 그러나 어댑터가 재조립하는 frontmatter가 `name`·`description`·`model` **3개로 하드코딩**되어 있어, OPAL 측에 어떤 필드를 추가해도 배포 시점에 소실된다.

한편 각 플랫폼은 서브에이전트 단위 추론 강도(effort) 지정 수단을 이미 제공한다. 현재 OPAL은 모델 등급(`light`/`standard`/`advanced`)만 조절할 수 있어, "모델은 유지하고 사고 깊이만 조절"하는 선택지가 없다.

## 배경 분석 (대화에서 도출)

### (1) 현행 어댑터가 버리는 필드

| 위치 | 현행 동작 |
|------|----------|
| `scripts/install-mac.sh:585-588` | `out_lines`에 `name`/`description`/`model` 3줄만 append (Claude·Cursor·Gemini 공통 경로) |
| `scripts/install-mac.sh:800-802` | Codex TOML에 `name`/`description`/`model`만 기록 |
| `scripts/install/windows.ps1:1795` | mac 경로 미러 — `$fmLines += "model: ..."` |
| `opal/core/references/agents.md` §frontmatter 변환 규칙 | 변환 SSOT 표. 마지막 행이 "(기타 OPAL 전용 필드) → (제거)" |

`opal/core/references/agents.md:194`가 **"기타 OPAL 전용 필드 = 제거"**를 규칙으로 명시하고 있어, 통로 부재는 구현 누락이 아니라 현행 설계다.

### (2) 플랫폼별 effort 지원 실측 (2026-09-02)

| 플랫폼 | 통로 모양 | 표기 | 허용값 | 확인 방법 |
|--------|----------|------|--------|----------|
| Claude Code | 독립 필드 | `effort: high` | `low`/`medium`/`high`/`xhigh`/`max` | 공식 문서 필드 표 |
| Codex CLI | 독립 필드(이름 다름) | `model_reasoning_effort = "high"` | `minimal`/`low`/`medium`/`high`/`xhigh` | 공식 config-reference + 로컬 파서 실측 |
| Cursor | **model 값에 내장** | `model: claude-opus-5[effort=high]` | 문서에 값역 미명시 | 공식 문서 + `cursor-agent --help` |
| Gemini CLI | **미지원** | — | — | 공식 subagents.md 필드 표에 부재 |

- Codex 에이전트 파일 수용 여부는 설치본 `codex-cli 0.147.0`으로 대조 실측했다 — `~/.codex/agents/`에 프로브 2개를 넣고 `codex doctor --json` 판정: 미지원 키(`zz_not_a_real_key`)는 `Ignoring malformed agent role definition: ... unknown field` 로 **거부**, `model_reasoning_effort = "low"`는 **경고 없음(수용)**. 프로브는 삭제 후 `0 warn · 0 fail` 복구를 확인했다.
- Cursor는 `model: inherit`(현행 OPAL 정책)에 대괄호를 붙일 수 없어, effort를 주려면 실모델 핀이 선행되어야 한다.
- 값 도메인 공통 구간은 `low`/`medium`/`high`/`xhigh` 4개뿐이다 — Claude에만 `max`, Codex에만 `minimal`이 있다.

### (3) 부수 발견 — Codex 설정이 legacy 키 사용 중

`scripts/install-mac.sh:834`·`scripts/install/windows.ps1:1836`이 `[agents] max_threads = 6`을 기록하는데, Codex 공식 config-reference는 이를 **"Legacy alias for `agents.max_concurrent_threads_per_session`"**로 명시한다.

### (4) 이번 범위에서 확인된 비대상 사항

- 각 에이전트에 실제 effort 값을 배정하는 판단은 통로와 분리한다.
- 대화 중 별도로 검토된 `opal-be-agent`·`opal-task-agent` 모델 강등, `opal-plan-agent` 강등은 본 태스크와 무관하다.

## 확정된 설계 방향 (대화에서 합의)

- `[결정]` 어댑터에 **확장 필드 변환 테이블**을 신설한다 — 필드명·값·배치 방식 3중 변환을 한 자료구조가 소유하고, emit은 그 테이블 순회로 수행한다.
- `[사실]` 단순 pass-through로는 성립하지 않는다 — Cursor는 별도 키가 아니라 model 값에 합성해야 하고(`cursor-agent --help` `--model` 예시 `claude-opus-4-8[context=1m,effort=high,fast=false]`), 값 도메인이 플랫폼마다 다르다.
- `[결정]` effort 실적용 대상은 **Claude Code·Codex 2종**으로 한정한다.
- `[결정]` Gemini는 미지원이므로 **키를 생략**한다 — 미지원 키 주입은 Codex 프로브에서 실제로 거부되는 것이 확인되었다.
- `[결정]` Cursor는 이번 범위에서 **적용하지 않고 테이블에 자리만 예약**한다 — `inherit` 정책을 깨야 하므로 별건이다.
- `[결정]` 플랫폼 분기는 전부 어댑터 계층의 테이블 안에 가둔다 — 프로젝트 금지사항(하드코딩 플랫폼 분기 추가 금지)을 준수한다.
- `[결정]` Codex `max_threads` legacy alias 정리를 본 태스크에 포함한다.
- `[결정]` 에이전트별 effort 값 배정은 **이월**한다 — 통로를 먼저 뚫고 값 판단은 후속 태스크로 분리한다.
- `[결정]` **(태스크 도중 캡틴 승인, 2026-09-02)** R-6 AC(a)의 판정 대상을 "`scripts/` 소스 텍스트"에서 "install이 기록한 `config.toml` 결과 파일"로 이전한다 — PM 실측 결과 `scripts/` 내 잔존 16곳(탐지·치환 정규식/주석/변경이력/성공 메시지/테스트 픽스처)이 전부 legacy 키 탐지·치환 로직 자체가 그 리터럴을 품어야 동작하는 구조적 필연이라, "소스에서 0건"은 원리적으로 충족 불가능한 AC였기 때문이다. 문자열 난독화(`'max_' + 'threads'` 등)로 판정만 속이는 방식은 금지하고, 실제 산출물(설치 결과 파일)이 legacy-free한지를 판정 기준으로 삼는다.

## 명확화 결과

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | 어댑터 frontmatter emit을 하드코딩 3필드에서 확장 가능한 변환 테이블로 전환하고, `effort`를 첫 실적용 필드로 Claude·Codex 2종에 태운다 | - | `scripts/install-mac.sh:585-588` · `scripts/install-mac.sh:800-802` · `scripts/install/windows.ps1:1795` |
| 범위 | **포함**: 변환 테이블 신설(필드명·값·배치 3중 변환) / effort 적용(Claude·Codex) / Gemini 생략 처리 / Cursor 자리 예약(미적용) / `agents.md` 변환 SSOT 표 갱신 / Codex `max_threads`→`max_concurrent_threads_per_session` 정리 / mac·windows 양쪽 동시 반영. **제외**: 에이전트별 effort 값 배정, 모델 등급 강등 건 일체 | - | `opal/core/references/agents.md` §frontmatter 변환 규칙 · `scripts/install-mac.sh:834` · `scripts/install/windows.ps1:1836` |
| 제약 | 플랫폼 분기는 어댑터 계층에만 존재 / `~/.opal/` 직접 편집 금지(프로젝트 소스 수정 후 install 재배포) / 변경이력 행 추가 의무 / mac·windows 어댑터는 문자 단위 미러 유지 / 배포본 에이전트 15개 × 4플랫폼 회귀 0 | - | `.opal/AGENT.md` §금지사항 · `scripts/install/windows.ps1:93` ("install-mac.sh _sub_body_model 미러(문자 단위 동일 정규식)") |
| 완료기준 | R-1~R-6의 AC가 전건 Pass하고, 재배포 후 4플랫폼 배포본에 대해 (a)effort 미선언 에이전트의 산출물이 변경 전과 바이트 동일 (b)effort 선언 시 Claude·Codex에만 올바른 키/값으로 출력 (c)Gemini 산출물에 effort 키 부재 (d)`codex doctor` 0 warn·0 fail 을 실측으로 확인 | - | 배경 분석 (2) 실측 절차 |

## 요구사항

- [ ] **R-1. 확장 필드 변환 테이블 신설 (mac)**
  - 무엇을: `emit_platform_agent_adapter`의 frontmatter emit을 `{OPAL 키 → 플랫폼별 (필드명, 값 변환, 배치 방식)}` 테이블 순회로 전환
  - 어디에: `scripts/install-mac.sh` (Claude·Cursor·Gemini 경로 `:584-589`, Codex 경로 `:795-802`)
  - 왜: 확정 방향 §1 — 필드 추가 시 emit 코드가 아니라 테이블 1행만 늘어나게 한다
  - AC: 테이블에 `effort` 1행이 존재하고, `name`/`description`/`model` 3필드도 동일 테이블 경로로 emit된다. emit 함수 본문에 플랫폼명 조건 분기가 신규로 추가되지 않는다(기존 `platform` 변수의 테이블 조회는 허용)

- [ ] **R-2. 배치 방식 3형태 지원**
  - 무엇을: 변환 테이블이 ①독립 키 ②이름이 다른 독립 키 ③model 값 내 합성 ④미지원 생략 4가지 배치 방식을 표현·실행
  - 어디에: `scripts/install-mac.sh` R-1의 테이블 + emit 로직
  - 왜: 확정 방향 §2 — Cursor는 별도 키가 아니라 model 값 합성이다
  - AC: `effort` 행이 Claude=①, Codex=②, Cursor=③(예약, 미활성), Gemini=④로 선언되어 있고, 각 배치 방식이 최소 1개 단위 테스트로 검증된다

- [ ] **R-3. 값 도메인 변환**
  - 무엇을: OPAL 중립 effort 레벨을 플랫폼 허용값으로 변환하는 매핑 정의. 공통 구간(`low`/`medium`/`high`/`xhigh`)은 항등, 플랫폼에 없는 값은 인접 값으로 축약
  - 어디에: `scripts/install-mac.sh` R-1의 테이블 값 변환 슬롯 + `opal/core/references/agents.md`
  - 왜: 확정 방향 §2 — Claude에만 `max`, Codex에만 `minimal`이 있다
  - AC: `effort: max`가 Claude에 `max`, Codex에 `xhigh`로 출력된다. 정의되지 않은 effort 값은 install이 경고를 출력하고 해당 필드를 생략한다(전체 실패시키지 않는다)

- [ ] **R-4. windows.ps1 미러 반영**
  - 무엇을: R-1~R-3과 동일한 테이블·변환·배치 로직을 PowerShell 어댑터에 반영
  - 어디에: `scripts/install/windows.ps1` (`:1795` 인근 frontmatter emit, Codex TOML 경로 포함)
  - 왜: `scripts/install/windows.ps1:93` — mac 어댑터와 문자 단위 미러 유지가 기존 규약
  - AC: 동일 입력 에이전트에 대해 mac·windows 산출물이 개행 문자를 제외하고 동일하다(에이전트 1개 이상으로 대조 확인)

- [ ] **R-5. 변환 SSOT 표 갱신**
  - 무엇을: `effort` 행을 frontmatter 변환 규칙 표에 추가하고, "기타 OPAL 전용 필드 = 제거" 규칙을 "테이블 미등재 필드 = 제거"로 정정
  - 어디에: `opal/core/references/agents.md` §frontmatter 변환 규칙 (표 `:186-194`)
  - 왜: 확정 방향 §5 — 표가 어댑터의 SSOT이므로 코드와 표가 함께 움직여야 한다
  - AC: 표에 `effort` 행이 존재하고 4플랫폼 셀이 모두 채워져 있다(Gemini는 "(제거 — 미지원)"). 표의 값이 R-1 테이블 구현과 축자 일치한다

- [ ] **R-6. Codex `max_threads` legacy alias 정리 (교체형)**
  - 무엇을: `[agents] max_threads` → `max_concurrent_threads_per_session`으로 교체
  - 어디에: `scripts/install-mac.sh:834` · `scripts/install/windows.ps1:1836`
  - 왜: Codex 공식 config-reference가 `max_threads`를 "Legacy alias"로 명시
  - AC (재정의됨 — 위 `[결정]` 참조): 판정 대상은 **install이 기록한 `config.toml`**이다.
    - (a) **구형 잔존 0** — 3케이스(①파일 없음 ②`[agents]` 없음 ③`[agents]`+legacy 키 보유) 실행 후 결과 파일에 `max_threads` 0건이다.
    - (b) **신형 채택** — 같은 3케이스 결과 파일에 `max_concurrent_threads_per_session` 1건이 존재하고, ③에서 기존 값이 보존되며 `[mcp_servers]` 등 타 블록이 무손상이고, 2회 실행 시 멱등(바이트 무변화)이다.
    - (c) **실환경 확인** — `~/.codex/config.toml`에 정식 키가 존재하고 legacy 키가 0건이며 `codex doctor`가 0 fail이다.
    - **명시적 예외**: 탐지·치환 정규식(`install-mac.sh:983,987` · `windows.ps1:1971,1972`) / 분기 설명 주석(`install-mac.sh:972,981` · `windows.ps1:1956`) / 변경이력(`install-mac.sh:46` · `windows.ps1:99`) / 성공 메시지(`install-mac.sh:991`) / 테스트 픽스처(`test_agent_adapter_fields.sh`)에 등장하는 `max_threads` 리터럴은 판정 대상이 아니다 — legacy 키를 탐지·치환하는 로직은 그 키 이름 리터럴을 코드 안에 품어야만 동작하므로, 소스 텍스트에서 완전히 0건으로 만드는 것은 원리적으로 불가능하다.

## 제약 조건

- [MUST] `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다."
- [MUST] `.opal/AGENT.md` §금지사항: "하드코딩된 플랫폼 분기 추가 금지 — Claude/Cursor/Gemini 분기는 어댑터 계층(install·plugin)에서만 수행한다."
- [MUST] `.opal/AGENT.md` §금지사항: "변경이력 누락 금지 — 스킬·에이전트·참조 문서 수정 시 변경이력 표 행 추가 의무."
- 기존 동작 100% 보존 — `effort`를 선언하지 않은 에이전트의 배포 산출물은 변경 전과 동일해야 한다.
- 미지원 플랫폼에 키를 주입하지 않는다 — Codex는 미지원 키를 실제로 거부한다(배경 분석 (2)).
- Cursor `inherit` 정책은 이번 범위에서 변경하지 않는다.

## 기술 스택

- Bash (`scripts/install-mac.sh`, 내장 Python heredoc)
- PowerShell (`scripts/install/windows.ps1`)
- Markdown frontmatter (YAML) / TOML — 플랫폼 sub-agent 정의 포맷
- 대상 플랫폼 CLI: Claude Code / Codex CLI 0.147.0 / Gemini CLI 0.35.3 / cursor-agent 2026.08.31

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | OPAL 에이전트 어댑터 규칙 | `opal/core/references/agents.md` | frontmatter 변환 SSOT 표 — R-5 대상 |
| D-2 | 소스 | mac install 스크립트 | `scripts/install-mac.sh` | 어댑터 emit 본체 — R-1~R-3, R-6 대상 |
| D-3 | 소스 | windows install 스크립트 | `scripts/install/windows.ps1` | mac 미러 — R-4, R-6 대상 |
| D-4 | 설계 | 모델 매핑 | `opal/core/references/opal-model-mapping.md` | 레벨→실값 2단 구조의 선례 (effort 매핑이 따를 패턴) |
| D-5 | 외부 | Claude Code Sub-agents | [Claude Code Sub-agents](https://code.claude.com/docs/en/sub-agents) | `effort` 필드·허용값 근거 |
| D-6 | 외부 | Codex Config Reference | [Codex Config Reference](https://learn.chatgpt.com/docs/config-file/config-reference) | `model_reasoning_effort`·`max_threads` legacy alias 근거 |
| D-7 | 외부 | Cursor Subagents | [Cursor Subagents](https://cursor.com/docs/agent/subagents) | model 값 대괄호 파라미터 근거 |
| D-8 | 외부 | Gemini CLI Subagents | [Gemini CLI Subagents](https://github.com/google-gemini/gemini-cli/blob/main/docs/core/subagents.md) | effort 미지원 근거 |
