# TASK: 멀티 플랫폼 에이전트 배포 메커니즘 구축

> 작성일: 2026-04-30 | 작업 유형: 신규 | 적용 스킬: opp | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

OPAL 에이전트(`~/.opal/agents/`)가 Claude Code, Cursor, Gemini, Antigravity 4개 플랫폼에서 sub-agent로 인식되어 디스패치되도록, 각 플랫폼 공식 사이트의 sub-agent 메커니즘을 확인하고 `install-mac.sh`에 플랫폼별 어댑터 자동 배포 로직을 추가한다.

## 배경

OPAL은 13개 에이전트(`opal-be-agent`, `opal-fe-agent`, `opal-task-agent` 등)를 `~/.opal/agents/{name}/AGENT.md`로 정의·배포한다. 그러나 각 AI 환경(Claude Code 등)은 자체 sub-agent 등록 경로를 별도로 가지고 있어, OPAL 에이전트를 `subagent_type`으로 분기 디스패치하는 메커니즘이 작동하지 않는 것으로 의심된다.

## 배경 분석 (대화에서 도출)

### 현재 상태 (2026-04-30 검증)

| 항목 | 결과 | 의미 |
|------|------|------|
| `~/.opal/agents/` 배포 | 13개 에이전트 모두 배포됨 | OPAL 자체 배포는 정상 |
| `~/.claude/agents/` | `.DS_Store`만 존재 (텅 빔) | Claude Code sub-agent 등록 0개 |
| `~/.claude/settings.json` | `permissions.allow`에 `Read(/Users/lucas/.opal/**)` 등 Read 권한만 있음. agents 경로 추가 설정 **없음** | Claude Code가 `~/.opal/agents/`를 sub-agent 경로로 인식하지 않음 |
| `scripts/install-mac.sh` | line 456-486에 OPAL 에이전트 → `~/.opal/agents/` 복사만 존재. `~/.claude/agents/` 배포 로직 **없음** | 어댑터 자동 생성 단계 부재 |
| AGENTIC-LOG (130, 121) | PM이 `op-task-plan 워커 디스패치 / opal-task-agent 적합` 기록은 있으나 실제 Claude Code Agent 도구의 `subagent_type` 처리 결과는 로그 미기록 | 실제 라우팅 검증 불가 |

### 캡틴이 mams 프로젝트에서 보고한 현상

> 1. Agent 도구의 sub-agent type에 opal-be-agent/opal-fe-agent가 직접 등록되어 있지 않아 general-purpose 에이전트로 디스패치됨
> 2. general-purpose는 OPAL 부트스트랩을 자동 인식하지 않으므로, 워커 프롬프트에 "opal-be-agent 역할로 동작 + AGENT.md Read"를 명시 주입해야 자체 로드가 작동

### 가설

Claude Code Agent 도구는 등록되지 않은 `subagent_type`을 받으면 silent하게 `general-purpose`로 폴백한다. 그동안 PM 디스패치 프롬프트가 충분히 자세해서 결과물 자체는 나왔지만, OPAL이 설계한 "에이전트별 페르소나·자체 로드 문서·금지 규칙" 차별화는 한 번도 실제로 발화한 적이 없을 가능성이 크다.

### 4개 플랫폼 sub-agent 메커니즘 (확인 필요)

| 플랫폼 | 공식 sub-agent 경로 (가설) | 검증 필요 |
|--------|--------------------------|----------|
| Claude Code | `~/.claude/agents/{name}.md` | 공식 문서 확인 |
| Cursor | (룰 기반? 별도 메커니즘?) | 공식 문서 확인 |
| Gemini | (extensions? toolsets?) | 공식 문서 확인 |
| Antigravity | (?) | 공식 문서 확인 |

각 플랫폼별로 sub-agent 메커니즘 자체가 존재하는지부터, 존재한다면 frontmatter 스키마와 등록 경로가 무엇인지 PLAN에서 공식 사이트로 확인한다.

## 확정된 설계 방향 (대화에서 합의)

1. `~/.opal/agents/`(OPAL SSOT)는 **변경 없음** — 모든 어댑터는 SSOT에서 변환 생성
2. `scripts/install-mac.sh`에 **플랫폼별 어댑터 자동 생성 함수 추가** — Claude/Cursor/Gemini/Antigravity 각각
3. **frontmatter 변환 규칙** — `model: standard/light/advanced` (OPAL 추상화) → 플랫폼별 모델명 (`opal-model-mapping.md` 활용). `icon` 등 잡 필드는 플랫폼별로 무시 또는 제거
4. **본문 유지** — OPAL `AGENT.md` 본문은 워커 system prompt로 그대로 사용 (`AGENT.md §부트스트랩 [WORKER] 규칙` 활용)
5. **공식 문서 우선** — 각 플랫폼의 sub-agent 메커니즘은 PLAN 단계에서 공식 사이트 확인 후 결정
6. 플랫폼이 sub-agent 메커니즘을 제공하지 않으면 해당 플랫폼은 **본 태스크에서 적용 제외** (이유 문서화)

## 요구사항

- [ ] **R-1** Claude Code sub-agent 어댑터 자동 생성
  - **무엇을**: `~/.opal/agents/*/AGENT.md` 13개를 순회하여 `~/.claude/agents/{name}.md` 어댑터 파일 생성
  - **어디에**: `scripts/install-mac.sh`에 신규 함수(`install_claude_agents()` 등) 추가
  - **왜**: Claude Code Agent 도구가 OPAL 에이전트를 `subagent_type`으로 인식하기 위함 — 본 TASK 배경 분석 §현재 상태 행 2,3
  - **AC**: install-mac.sh 실행 후 `~/.claude/agents/` 디렉토리에 13개의 `.md` 파일이 존재하고, 각 파일의 frontmatter `name` 필드가 OPAL 에이전트 이름과 일치한다

- [ ] **R-2** Cursor sub-agent 어댑터 자동 생성 (메커니즘 존재 시)
  - **무엇을**: Cursor의 sub-agent 메커니즘이 존재하면 동일 패턴으로 어댑터 생성, 없으면 적용 제외 사유 문서화
  - **어디에**: `scripts/install-mac.sh`
  - **왜**: 플랫폼 독립성 원칙 (PROJECT.md §프로젝트 원칙 #3)
  - **AC**: PLAN.md에 Cursor 메커니즘 조사 결과가 기재되고, 메커니즘 존재 시 어댑터 파일이 생성됨 / 부재 시 사유가 install-mac.sh 주석 + DONE.md에 기록됨

- [ ] **R-3** Gemini sub-agent 어댑터 자동 생성 (메커니즘 존재 시)
  - **무엇을**: Gemini의 sub-agent 메커니즘이 존재하면 어댑터 생성, 없으면 적용 제외 사유 문서화
  - **어디에**: `scripts/install-mac.sh`
  - **왜**: 플랫폼 독립성 원칙
  - **AC**: PLAN.md에 Gemini 메커니즘 조사 결과 기재 + 어댑터 생성 또는 사유 문서화

- [ ] **R-4** Antigravity sub-agent 어댑터 자동 생성 (메커니즘 존재 시)
  - **무엇을**: Antigravity의 sub-agent 메커니즘이 존재하면 어댑터 생성, 없으면 적용 제외 사유 문서화
  - **어디에**: `scripts/install-mac.sh`
  - **왜**: 플랫폼 독립성 원칙
  - **AC**: PLAN.md에 Antigravity 메커니즘 조사 결과 기재 + 어댑터 생성 또는 사유 문서화

- [ ] **R-5** frontmatter 변환 규칙 정의
  - **무엇을**: OPAL `AGENT.md` frontmatter → 플랫폼별 sub-agent frontmatter 변환 규칙을 SSOT로 정의 (model 매핑·필드 정리·icon 등 무시 규칙)
  - **어디에**: `opal/runtimes/framework/data/model_mapping.json` 활용 또는 `opal/core/references/agents.md`에 변환 규칙 섹션 추가
  - **왜**: 향후 신규 OPAL 에이전트 추가 시 동일 규칙으로 자동 변환되어야 함
  - **AC**: 변환 규칙 표가 SSOT 문서에 명시되고, install-mac.sh가 해당 규칙을 참조하여 변환을 수행한다

- [ ] **R-6** 검증 절차
  - **무엇을**: 각 플랫폼에서 OPAL 에이전트가 sub-agent로 정상 인식되는지 확인하는 검증 절차 정의 (간단 echo 테스트 또는 dispatch 테스트)
  - **어디에**: PLAN.md §검증 섹션 + DONE.md 검증 결과
  - **왜**: silent 폴백 가설 검증 + 본 태스크 효과 입증
  - **AC**: 최소 1개 플랫폼(Claude Code)에서 OPAL 에이전트로 디스패치 시 `general-purpose` 폴백이 발생하지 않음을 확인하는 절차가 PLAN.md에 명시됨

- [ ] **R-7** 변경이력 갱신
  - **무엇을**: `scripts/install-mac.sh`, 변환 규칙 SSOT 문서, `opal/core/references/agents.md` 등 수정 파일에 변경이력 행 추가
  - **어디에**: 각 파일 변경이력 테이블
  - **왜**: 하네스 컨벤션
  - **AC**: 수정한 모든 파일에 오늘 날짜와 변경 요약 행이 추가되어 있다

## 미확정 사항 (PLAN에서 결정)

- 4개 플랫폼 각각의 공식 sub-agent 메커니즘 존재 여부와 정확한 frontmatter 스키마/등록 경로
- frontmatter 변환 규칙 SSOT의 정확한 위치 (model_mapping.json 확장 vs agents.md 신규 섹션 vs 신규 변환 규칙 파일)
- install-mac.sh에 함수를 직접 추가할지, 별도 helper 스크립트로 분리할지

## 제약 조건

- `~/.opal/` 경로 직접 수정 **금지** — 소스 경로(`opal/agents/`, `scripts/install-mac.sh`)에서만 수정 (확정 기준 §2)
- 배포 행위 **금지** — install-mac.sh 실제 실행은 캡틴 명시 지시 필요 (`.opal/AGENT.md` §금지사항)
- OPAL 에이전트 본문(AGENT.md 본문) 변경 **금지** — frontmatter 변환만 수행
- 커뮤니티 스킬 원본 수정 금지 (해당 시)

## 기술 스택

- Bash (install-mac.sh 확장)
- Markdown frontmatter (YAML)
- 각 플랫폼 공식 문서 (web 조사 대상)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | install-mac.sh | `scripts/install-mac.sh` | 핵심 수정 대상 — 어댑터 생성 함수 추가 |
| D-2 | 소스 | OPAL 에이전트 정의 | `opal/agents/` (13개 에이전트) | 변환 입력 SSOT |
| D-3 | 소스 | 모델 매핑 | `opal/runtimes/framework/data/model_mapping.json` | model 필드 변환 규칙 SSOT |
| D-4 | 설계 | agents.md | `opal/core/references/agents.md` | 에이전트 카탈로그 — 변환 규칙 추가 후보 위치 |
| D-5 | 설계 | PROJECT.md | `docs/PROJECT.md` | 플랫폼 독립성 원칙(#3) 근거 |
| D-6 | 설계 | .opal/AGENT.md | `.opal/AGENT.md` | 배포 금지 규칙 |
| D-7 | 외부 | Claude Code sub-agent 공식 문서 | (PLAN에서 확인) | 등록 경로/frontmatter 스키마 확인 |
| D-8 | 외부 | Cursor sub-agent 공식 문서 | (PLAN에서 확인) | 메커니즘 존재 여부/스키마 확인 |
| D-9 | 외부 | Gemini sub-agent 공식 문서 | (PLAN에서 확인) | 메커니즘 존재 여부/스키마 확인 |
| D-10 | 외부 | Antigravity sub-agent 공식 문서 | (PLAN에서 확인) | 메커니즘 존재 여부/스키마 확인 |
