# TASK: install 어댑터 본문 model 레벨명 치환 — 액션 에이전트 sub-dispatch 모델 버그 수정

> 작성일: 2026-06-21 | 작업 유형: 수정(버그) | 적용 스킬: opds | 모드: agentic
> 입력: 사용자 요청 (진단 + 설계 대화 선행) + AskUserQuestion 방향 확정(옵션 A)
> 출력: TASK.md

## 작업 목표

install 어댑터(`emit_platform_agent_adapter`)가 에이전트 **본문(body)의 인라인 `model: <레벨>` 토큰**도 플랫폼 실모델명으로 치환하도록 확장하여, sub-orchestrating 에이전트(opal-task-action-agent · opal-sdd-action-agent)가 sub-worker 디스패치 시 유효한 모델명을 Agent 도구에 전달하게 만든다.

## 배경

oppd Phase 3 액션 에이전트(opal-task-action-agent)가 sub-worker(opal-task-agent 등)를 디스패치할 때 본문 지시에 적힌 레벨명(`model: advanced/standard/light`)을 Agent 도구 `model` 파라미터에 그대로 전달한다. Agent 도구의 `model` enum은 실모델명(`sonnet/opus/haiku/fable`)만 허용하므로 레벨명은 검증 위반으로 실패한다. 액션 에이전트는 `[WORKER]` 마커로 디스패치되어 부트스트랩(모델 매핑 로드)을 건너뛰므로 런타임에 레벨→모델명 변환 테이블도 갖지 못한다. 결과적으로 Phase 3 sub-dispatch가 깨지거나 모델 티어링이 비결정적으로 무시된다.

## 배경 분석 (대화에서 도출)

코드·문서 대조로 확정한 4단계 실패 사슬 (대상은 프로젝트 소스 `opal/...` · `scripts/...`):

| # | 사실 | 근거 |
|---|------|------|
| 1 | Agent 도구 `model` 파라미터는 실모델명 enum만 허용 — 레벨명 전달 시 검증 실패 | Agent 도구 스키마 `model.enum = [sonnet, opus, haiku, fable]` (이 세션 도구 정의) |
| 2 | install 어댑터는 **frontmatter `model:`만** 변환(claude: advanced→opus·standard→sonnet·light→haiku), 본문은 verbatim 복사 | `scripts/install-mac.sh:556-565` (frontmatter 변환) + `scripts/install-mac.sh:601` (`f.write(body)`) |
| 3 | 액션 에이전트 본문이 sub-worker 디스패치를 레벨명으로 지시 | `opal/agents/opal-task-action-agent/AGENT.md:37,46,50,67,87,95` · `opal/agents/opal-sdd-action-agent/AGENT.md:40,44` |
| 4 | oppd가 액션 에이전트를 `[WORKER]` 마커로 디스패치 → 부트스트랩 전체 스킵 → `opal-model-mapping.md` 미로드, oppd도 모델 매핑 미주입 | `opal/skills/opal-pilot-project-dev/SKILL.md:364,445` + `opal/core/AGENT.md:9` ([WORKER] 규칙) |

**근본 성격**: frontmatter는 어댑터가 변환하는데 본문은 안 함 = **어댑터 변환 경계의 비대칭**. 또한 모델 티어링이 prose 주석으로만 존재하고 강제되지 않음 = 헌법 §"Enforce, don't just advise" 위반.

**영향 범위**: 본문에 레벨명 sub-dispatch 지시를 가진 에이전트 2개 — opal-task-action-agent, opal-sdd-action-agent. 나머지 11개 에이전트는 sub-dispatch가 없어 본문 model 토큰 없음(grep 확인).

## 확정된 설계 방향 (대화에서 합의)

캡틴이 AskUserQuestion으로 직접 선택한 결정:

**방향 = 옵션 A — install 어댑터가 본문도 변환** (다른 검토안: B oppd PM 실모델명 주입 / C 본문 오버라이드 제거)
- 근거: 이미 model 변환을 담당하는 단일 어댑터 지점을 확장하므로 헌법(플랫폼 독립=어댑터에 격리)과 가장 정합. 소스는 플랫폼 중립 유지(레벨명 그대로), 배포본만 플랫폼별 실모델명. `[WORKER]`/부트스트랩 충돌 없음. phase별 티어링 의도 보존.
- frontmatter 변환에 쓰이는 동일 `mapping[platform]` dict를 본문 치환에 재사용.

**031 태스크와의 관계** = 별도 032로 분리 진행 (캡틴 확정). 031(oppd 런타임 프로세스/루프 재설계)과 레이어 분리 — 032는 배포 변환 메커니즘(install·windows 한정). 어댑터 치환은 본문 레벨명이 몇 줄이든 무관하게 동작하므로 031의 본문 재작성과 forward-compatible.

## 요구사항

### F-001 install-mac.sh 본문 model 레벨 치환

- [ ] **무엇을**: `emit_platform_agent_adapter`에서 body 직렬화(`f.write(body)`) 직전, 본문 인라인 `model: <레벨>` 토큰을 `mapping[platform]`의 실모델명으로 정규식 치환한다. frontmatter 변환에 쓰는 동일 mapping dict를 재사용한다.
- **어디에**: `scripts/install-mac.sh` `emit_platform_agent_adapter` 내장 Python — `f.write(body)` 직전 (현 `scripts/install-mac.sh:601`)
- **왜**: 배경 분석 #2 — frontmatter만 변환되고 본문은 verbatim 복사되어 레벨명이 Agent 도구에 그대로 전달됨 (→ 확정 방향 옵션 A)
- **AC**: install 재배포 후 `~/.claude/agents/opal-task-action-agent.md` 본문에 `model: opus`·`model: sonnet`·`model: haiku`가 나타나고, `model: advanced`·`model: standard`·`model: light`는 0건이다. opal-sdd-action-agent.md도 동일.

### F-002 cursor inherit 엣지 처리

- [ ] **무엇을**: cursor 플랫폼은 mapping이 모든 레벨을 `inherit`로 반환한다. 본문에 `model: inherit`가 그대로 남아 Agent 도구 model 파라미터로 오인되면 또 enum 위반이 된다. cursor의 경우 본문 model 오버라이드 토큰이 "오버라이드 생략(target 에이전트 frontmatter 상속)"으로 해석되는 형태가 되도록 치환 규칙을 정의한다. (정확한 치환 형태 — 주석 제거 vs 무해 표기 — 는 PLAN에서 잠금)
- **어디에**: `scripts/install-mac.sh` (cursor 분기 처리) + 필요 시 본문 해석 지침
- **왜**: 배경 분석 #2의 매핑(`scripts/install-mac.sh:561` cursor 전 레벨 `inherit`) — claude만 고치면 cursor에서 동일 버그 재현
- **AC**: cursor 어댑터 출력 본문에 Agent 도구 model 파라미터로 전달될 수 있는 형태의 `model: inherit` 또는 `model: <레벨>` 토큰이 남지 않는다 (PLAN에서 확정한 검증 가능 형태로 판정).

### F-003 windows.ps1 미러

- [ ] **무엇을**: install-mac.sh와 동일한 본문 치환 로직 + 플랫폼 매핑 dict를 windows.ps1의 에이전트 어댑터 함수에 미러한다.
- **어디에**: `scripts/windows.ps1` 에이전트 어댑터 함수
- **왜**: PM 검토기준 "부트스트래퍼·MCP 등 배포 영향 항목이 install 스크립트에 반영" + 028 교훈(양 플랫폼 어댑터 일관성)
- **AC**: windows.ps1에 본문 model 레벨 치환 로직이 존재하고, 매핑 값이 install-mac.sh와 동기(claude/gemini/codex/cursor 4개 컬럼)한다.

### F-004 회귀 방지 — 정규식 앵커 + 비대상 에이전트 본문 불변

- [ ] **무엇을**: 치환 정규식을 `\b(light|standard|advanced)\b` 단어 경계로 한정하고, `model:` 접두 토큰에 결합된 경우만 치환한다. sub-dispatch가 없는 11개 에이전트 본문과 13개 전체의 frontmatter 변환 동작은 불변이어야 한다.
- **어디에**: `scripts/install-mac.sh` (및 미러 `scripts/windows.ps1`)의 치환 정규식 패턴
- **왜**: 본문 다른 위치의 일반 단어("advanced" 등) 오염 차단 + 기존 frontmatter 변환 회귀 방지
- **AC**: install 재배포 후 sub-dispatch 없는 11개 에이전트의 배포본 본문 diff가 없고, 13개 에이전트 frontmatter `model:` 값이 기존과 동일하며, 본문이 변경되는 에이전트는 opal-task-action-agent·opal-sdd-action-agent 2개뿐이다.

### F-005 agents.md 문서 동기 (문서-코드 불일치 방지)

- [ ] **무엇을**: `agents.md` §"본문(System Prompt) 처리"가 "본문은 변경 없이 복사된다"고 명시하는데, F-001 후엔 본문 인라인 `model: <레벨>` 디스패치 토큰이 frontmatter처럼 변환된다. 이 진술을 정정하고(본문 복사 + 인라인 model 레벨 토큰만 예외 변환), §frontmatter 변환 규칙 인근에 본문 변환을 함께 기재한다. 변경이력 행 추가.
- **어디에**: `opal/core/references/agents.md` §"본문(System Prompt) 처리"(186-187줄) + §"플랫폼 sub-agent 어댑터 변환 규칙" 인근
- **왜**: 헌법 §"코드가 실질적 문서(source of truth)" — 어댑터 동작이 바뀌면 그 동작을 서술하는 SSOT 문서가 거짓이 됨. PM 검토기준 "추적 가능성·문서 일관성"
- **AC**: agents.md §본문 처리에 "본문은 복사되되 인라인 `model: <레벨>` 디스패치 토큰은 플랫폼 실모델명으로 변환된다"는 취지가 기재되고, "본문은 **변경 없이** 그대로 복사된다"는 무조건 진술이 남아있지 않으며, 변경이력 표에 행이 추가된다.

## 제약 조건

- **배포 경계 준수**: 프로젝트 소스(`scripts/...`)만 수정한다. `~/.opal/`·`~/.claude/agents/` 배포본은 install 재배포로만 갱신한다 (직접 편집 금지).
- **소스 플랫폼 중립 유지**: 에이전트 AGENT.md 본문의 레벨명(advanced/standard/light)은 소스에서 그대로 유지한다. 변환은 어댑터(배포 시점)에서만 수행 — 플랫폼 분기를 로직(에이전트)에 넣지 않는다.
- **하네스 우회 금지**: RED-first 트랙 — 자가 검증 위험 영역이므로 수정 전 RED 증거(배포본 본문에 레벨명 잔존) 확보 후 GREEN 검증.
- **031 미간섭**: 진행 중 태스크 031의 파일(`tasks/031-.../`)·산출물을 건드리지 않는다.
- **커밋 금지**: 사용자 명시 요청 전 커밋하지 않는다.

## 기술 스택

- Bash + 내장 Python3 (`scripts/install-mac.sh`), PowerShell (`scripts/windows.ps1`)
- 정규식 치환 (Python `re` / PowerShell `-replace`)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | install-mac.sh | `scripts/install-mac.sh` | 어댑터 frontmatter 변환·body 직렬화 현 동작 (461-602) |
| D-2 | 소스 | windows.ps1 | `scripts/windows.ps1` | 어댑터 미러 대상 함수 |
| D-3 | 소스 | opal-task-action-agent | `opal/agents/opal-task-action-agent/AGENT.md` | 본문 레벨명 sub-dispatch 지시 (37,46,50,67,87,95) |
| D-4 | 소스 | opal-sdd-action-agent | `opal/agents/opal-sdd-action-agent/AGENT.md` | 동일 패턴 자매 에이전트 (40,44) |
| D-5 | 설계 | opal-model-mapping.md | `opal/core/references/opal-model-mapping.md` | 레벨↔플랫폼 모델 매핑 SSOT (§2 매핑 테이블) |
| D-6 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 구현 규칙(배포 경계·플랫폼 분기·변경이력) |
| D-7 | 설계 | opal-pilot-project-dev | `opal/skills/opal-pilot-project-dev/SKILL.md` | [WORKER] 디스패치·모델 매핑 미주입 확인 (364,445) |
| D-8 | 설계 | agents.md | `opal/core/references/agents.md` | §본문 처리 "변경 없이 복사" 진술 + frontmatter 변환 규칙 표 (F-005 정정 대상, 184-187) |
