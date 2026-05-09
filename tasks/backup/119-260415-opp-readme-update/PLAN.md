# PLAN: README.md 업데이트 — 최근 변경 반영 + 설치/설정 섹션 확장

> 작성일: 2026-04-15
> 입력: TASK.md
> 출력: PLAN.md

## 1. 현황 조사

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `README.md` (636줄) | 갱신 대상 — 프레임워크 공개 소개 문서 | **예** (단일 파일 수정) |
| `docs/PROJECT.md` | 프레임워크 정체성·핵심 철학 SSOT | 아니오 (참조만) |
| `docs/ARCHITECTURE.md` | 아키텍처 개요 상세 | 아니오 (참조만) |
| `docs/CONVENTIONS.md` | 어투·형식 컨벤션 | 아니오 (참조만) |
| `scripts/install-mac.sh` | 설치 스크립트 실제 구현 | 아니오 (R-8 경로 검증 참조) |
| `opal/core/references/agents.md` | 전문 에이전트 6종 레지스트리 | 아니오 (R-3 참조) |
| `opal/core/references/opal-pm.md` | PM 행동 프로세스 (역할 전환) | 아니오 (R-4 참조) |
| `tasks/117-*/DONE.md` | 117 마감 산출물 | 아니오 (R-3 근거 참조) |
| `~/.opal/AGENT.md` | 비서/PM 역할 전환 규칙 상세 | 아니오 (R-4 참조, Read만) |

### 현재 상태

#### README.md 섹션 구조 (636줄)

| # | 섹션 | 줄 범위 | 규모 |
|---|------|--------|------|
| 1 | 제목 + OPAL이란? + 핵심 철학 + 주요 특징 | 1~37 | 37줄 |
| 2 | 목차 | 40~57 | 18줄 |
| 3 | 설치 | 60~77 | 18줄 |
| 4 | 프로젝트 설정 | 80~111 | 32줄 |
| 5 | 핵심 개념 — Pilot과 // 커맨드 | 114~161 | 48줄 |
| 6 | Pilot 비교 & 사용 사례 | 164~339 | 176줄 |
| 7 | Pilot 사용법 | 342~507 | 166줄 |
| 8 | 독립 스킬 사용법 | 509~585 | 77줄 |
| 9 | Agentic Mode | 588~611 | 24줄 |
| 10 | 아키텍처 개요 | 614~636 | 23줄 |

#### 갱신이 필요한 구체적 위치

**R-1 (opds/opd 파이프라인 갱신)**:
- 168~177줄: Pilot 비교 테이블 — `opds` 행의 파이프라인이 `TASK → PLAN → TEST-SCENARIO → EXECUTE → TEST`로 TEST-SCENARIO가 별도 단계로 표기됨. PLAN에 통합됐으므로 `TASK → PLAN(+테스트 시나리오) → EXECUTE → TEST`로 변경 필요
- 170줄: `//opds` 행 — `TASK → PLAN → TEST-SCENARIO → EXECUTE → TEST`
- 171줄: `//opd` 행 — `TASK → ANALYSIS → PLAN → TEST-SCENARIO → EXECUTE → TEST`
- 348줄: opds 파이프라인 — `TASK → PLAN → TEST-SCENARIO → EXECUTE → TEST`
- 350줄: opds 산출물 — `TEST-SCENARIO.md` 별도 나열
- 354~364줄: opds 진행 흐름 — 2단계에서 PLAN+TEST-SCENARIO 분리 표기
- 384줄: opd 파이프라인 — `TASK → ANALYSIS → PLAN → TEST-SCENARIO → EXECUTE → TEST`
- 386줄: opd 산출물 — `TEST-SCENARIO.md` 별도 나열
- 392~405줄: opd 진행 흐름 — 3단계에서 PLAN+TEST-SCENARIO 분리 표기

**R-2 (opsdd VERIFY 추가)**:
- 174줄: opsdd 행 — 파이프라인에 `VERIFY`가 누락 (`TASK → SPEC → REVIEW → DESIGN → EXECUTE-LOOP → DONE`)
- 442줄: opsdd 파이프라인 — `TASK → SPEC → REVIEW → DESIGN → EXECUTE-LOOP → DONE`

**R-3 (전문 에이전트 체계)**:
- 32~36줄: 주요 특징 리스트 — 전문 에이전트 항목 없음
- 614~636줄: 아키텍처 개요 — `agents/` 트리에 전문 에이전트 6종 미표기, `community-skills/` 숫자 31개(실제 37개)
- 신규 섹션 필요: 전문 에이전트 6종의 이름·역할 테이블

**R-4 (비서/PM 역할 전환)**:
- 핵심 개념 섹션(114줄 부근) 또는 별도 소섹션 필요
- 현재 README에 "비서"/"PM" 역할 전환 개념 언급 없음

**R-5 (@header + code-scan)**:
- 아키텍처 개요(614~636줄)에 @header/code-scan 언급 없음

**R-6 (하네스 모듈화)**:
- 아키텍처 개요 트리에 `references/` 안에 `harness/` 모듈화 미표기

**R-7~R-13 (설치/설정 확장)**:
- 설치 섹션(60~77줄): 17줄로 간소. 사전 요구사항, 옵션별 상세, 검증 방법 없음
- 프로젝트 설정 섹션(80~111줄): Claude Code만 다룸. Cursor/Gemini 없음, `//opi` 생성물 상세 없음
- 빠른 시작 섹션 없음
- 트러블슈팅 섹션 없음

#### install-mac.sh 실제 동작 확인 (R-8 경로 정확성)

**[1] OPAL 설치** (`install_opal` 함수, 396~547줄):
- 프레임워크 디렉토리 클린 삭제 후 재배포 (사용자 데이터 `identity.md`, `AGENT.md` 보존)
- 배포 대상:
  - `AGENT.md` → `~/.opal/AGENT.md` (코어 에이전트 정의)
  - 독립 스킬 → `~/.opal/skills/` (skills/ 하위)
  - OPAL 스킬 → `~/.opal/skills/` (opal/skills/ 하위)
  - 에이전트 → `~/.opal/agents/` (opal/agents/ + agents/ 통합)
  - 템플릿 → `~/.opal/templates/`
  - 도구 → `~/.opal/tools/`
  - Python venv → `~/.opal/.venv/` (requirements.txt)
  - 참조 레지스트리 → `~/.opal/references/`
  - 커뮤니티 스킬 → `~/.opal/community-skills/`
  - Claude Code hooks → `~/.claude/settings.json`
- 부트스트래퍼 설치:
  - Claude: `~/.claude/CLAUDE.md` (OPAL 마커 삽입/교체)
  - Cursor: `~/.cursor/rules/000-opal-agent.mdc` (파일 복사)
  - Gemini: `~/.gemini/GEMINI.md` (OPAL 마커 + HARDENING 마커)
- Claude Code `~/.opal` 읽기 권한 → `~/.claude/settings.json`
- Gemini 외부 경로 접근 설정 → `~/.gemini/settings.json`

**[2] MCP 서버 설정** (`install_mcp` 함수, 707~797줄):
- `opal/core/mcps/*.json` 파일을 순회하여 플랫폼별 설정
- Claude: `claude mcp add --scope user` (CLI 등록)
- Gemini: `gemini mcp add -s user` (CLI 등록), CLI 없으면 `~/.gemini/settings.json`에 config_merge
- Cursor: `~/.cursor/mcp.json` (config_merge)
- Antigravity: `~/.gemini/antigravity/mcp_config.json` (config_merge)

**[3] 전체 설치**: [1] + [2] 순차 실행

**[4] Python 패키지**: `~/.opal/.venv/` venv에 requirements.txt 업데이트

#### 전문 에이전트 6종 (agents.md 확인, R-3)

| 에이전트 | 단계 | 영역 | 역할 |
|---------|------|------|------|
| `opal-plan-agent` | PLAN | 공통 | 코드 분석 + 기능 설계 + 에이전트 라우팅 |
| `opal-fe-agent` | EXECUTE | FE | 프론트엔드 구현 전문 |
| `opal-be-agent` | EXECUTE | BE | 백엔드 구현 전문 |
| `opal-db-agent` | PLAN, EXECUTE | DB | DB 모델 설계 + 마이그레이션 구현 |
| `opal-planning-agent` | EXECUTE | 기획 | 서비스 기획 산출물 작성/관리 |
| `opal-test-agent` | TEST | 공통 | 테스트 전문 (BE/FE/E2E 모드) |

#### 비서/PM 역할 전환 (R-4)

- `.opal/AGENT.md` 존재 여부로 자동 전환
- 비서: 프로젝트 밖 (일상 대화, 일반 업무)
- PM: 프로젝트 내 (태스크 관리, 워커 디스패치, Gate 검토)
- PM 내부: 대화 모드(분석/읽기) vs 태스크 모드(`//` 커맨드, 파일 수정)

### 영향 범위

- `README.md` 단일 파일만 수정 (제약 조건)
- 목차 앵커 링크가 신규 섹션에 맞게 갱신되어야 함
- 기존 섹션의 줄 번호가 대폭 이동될 예정 (삽입 분량 약 150~200줄 추정)
- 다른 문서에서 README를 참조하는 부분은 없으므로 외부 영향 없음

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 |
|---|----------|------|
| - | 없음 | - |

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `README.md` | 16개 요구사항(R-1~R-16) 반영: 파이프라인 갱신, 신규 섹션 추가, 설치/설정 확장, 아키텍처 개요 보강, 목차 갱신 |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| - | 없음 | - |

### 최종 README 섹션 구조 (목표)

```
1.  제목 + OPAL이란? + 핵심 철학 + 주요 특징          (기존 유지 + R-3 주요 특징 항목 추가)
2.  목차                                              (R-14 신규 섹션 반영)
3.  설치                                              (R-7~R-9 대폭 확장)
    3a. 사전 요구사항                                  (R-7 신규)
    3b. 설치 실행                                      (기존 유지)
    3c. 설치 옵션별 상세                                (R-8 신규)
    3d. 설치 후 검증                                    (R-9 신규)
4.  프로젝트 설정                                      (R-10~R-11 확장)
    4a. 자동 설정 (//opi)                              (기존 유지)
    4b. //opi 생성물 상세                              (R-11 신규)
    4c. 수동 설정 — Claude Code                        (기존 유지)
    4d. 수동 설정 — Cursor                             (R-10 신규)
    4e. 수동 설정 — Gemini                             (R-10 신규)
5.  빠른 시작                                          (R-12 신규)
6.  핵심 개념 — Pilot과 // 커맨드                      (기존 유지)
    6a. 비서 모드와 PM 모드                            (R-4 신규 소섹션)
7.  Pilot 비교 & 사용 사례                             (R-1, R-2 파이프라인 갱신)
8.  Pilot 사용법                                       (R-1, R-2 파이프라인·산출물·진행 흐름 갱신)
9.  독립 스킬 사용법                                   (기존 유지)
10. Agentic Mode                                       (기존 유지)
11. 전문 에이전트 (Specialist Agent)                   (R-3 신규 섹션)
12. 아키텍처 개요                                      (R-3, R-5, R-6 보강)
13. 트러블슈팅                                         (R-13 신규)
```

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | 주요 특징에 전문 에이전트 항목 추가 | README.md (32~36줄) | 하 |
| 2 | 설치 섹션 확장 (R-7, R-8, R-9) | README.md (60~77줄) | **상** |
| 3 | 프로젝트 설정 섹션 확장 (R-10, R-11) | README.md (80~111줄) | 중 |
| 4 | 빠른 시작 섹션 신규 추가 (R-12) | README.md (설정 직후 삽입) | 하 |
| 5 | 핵심 개념에 비서/PM 역할 전환 소섹션 추가 (R-4) | README.md (161줄 부근) | 중 |
| 6 | Pilot 비교 테이블 파이프라인 갱신 (R-1, R-2) | README.md (168~177줄) | 중 |
| 7 | Pilot 사용법 opds/opd 파이프라인·산출물·진행 흐름 갱신 (R-1) | README.md (344~406줄) | 중 |
| 8 | Pilot 사용법 opsdd 파이프라인 갱신 (R-2) | README.md (438~457줄) | 하 |
| 9 | 전문 에이전트 섹션 신규 추가 (R-3) | README.md (Agentic Mode 뒤) | 중 |
| 10 | 아키텍처 개요 보강 (R-3, R-5, R-6) | README.md (614~636줄) | 중 |
| 11 | 트러블슈팅 섹션 신규 추가 (R-13) | README.md (아키텍처 개요 뒤) | 하 |
| 12 | 목차 갱신 + 앵커 링크 검증 (R-14) | README.md (40~57줄) | 중 |
| 13 | 전체 어투·형식 일관성 확인 (R-15) + 핵심 철학 유지 확인 (R-16) | README.md 전체 | 중 |

### 핵심 설계

#### Step 1: 주요 특징 항목 추가 (R-3)

기존 5개 항목 리스트(32~36줄)에 1개 추가:
```
- **전문 에이전트(Specialist Agent)** — 도메인별 전문 워커가 FE/BE/DB/기획/테스트를 담당
```

#### Step 2: 설치 섹션 확장 (R-7, R-8, R-9)

기존 설치 섹션(60~77줄, 18줄) → 약 80줄로 확장.

**R-7 사전 요구사항** 서브섹션:
- 지원 OS: macOS (install-mac.sh 기준)
- 필수 도구: bash, git, Node.js (v18+, date/skill-registry 툴용), Python 3 (venv/MCP용)
- 지원 AI 플랫폼: Claude Code, Cursor, Gemini (Antigravity)

**R-8 설치 옵션별 상세** 서브섹션:
install-mac.sh 실제 확인 결과 기반. 각 옵션이 배치하는 경로를 정확히 기술:

`[1] OPAL 설치`:
| 배치 대상 | 경로 |
|----------|------|
| 에이전트 코어 | `~/.opal/AGENT.md` |
| 스킬 (독립 + OPAL) | `~/.opal/skills/` |
| 에이전트 (전문 + 범용) | `~/.opal/agents/` |
| 참조 레지스트리 | `~/.opal/references/` |
| CLI 도구 | `~/.opal/tools/` |
| 커뮤니티 스킬 | `~/.opal/community-skills/` |
| 템플릿 | `~/.opal/templates/` |
| Python 가상환경 | `~/.opal/.venv/` |
| 부트스트래퍼 (Claude) | `~/.claude/CLAUDE.md` |
| 부트스트래퍼 (Cursor) | `~/.cursor/rules/000-opal-agent.mdc` |
| 부트스트래퍼 (Gemini) | `~/.gemini/GEMINI.md` |
| Claude hooks/권한 | `~/.claude/settings.json` |
| Gemini 경로 접근 | `~/.gemini/settings.json` |

`[2] MCP 서버 설정`:
| 플랫폼 | 설정 방식 | 설정 파일 |
|--------|----------|----------|
| Claude Code | `claude mcp add --scope user` | CLI 등록 |
| Gemini | `gemini mcp add -s user` | CLI 등록 (폴백: `~/.gemini/settings.json`) |
| Cursor | config_merge | `~/.cursor/mcp.json` |
| Antigravity | config_merge | `~/.gemini/antigravity/mcp_config.json` |

**R-9 설치 후 검증** 서브섹션:
- `ls ~/.opal/` 기대 출력 (AGENT.md, identity.md, skills/, agents/, references/, tools/, templates/, community-skills/)
- AI 도구 재시작 후 부트스트랩 체크리스트 메시지 확인 (`[부트스트랩] ✅ identity ✅ harness ...`)

#### Step 3: 프로젝트 설정 확장 (R-10, R-11)

**R-11 `//opi` 생성물 상세**:
| 파일 | 역할 |
|------|------|
| `.opal/AGENT.md` | PM 프로필 — 프로젝트별 검토 기준, 금지사항, 확정 기준 |
| `docs/PROJECT.md` | 프로젝트 정의 SSOT — 개요, 원칙, 문서 레지스트리 |
| `docs/CONVENTIONS.md` | 코드/문서 컨벤션 — 네이밍, 파일 구조, 커밋 규칙 |

**R-10 Cursor 수동 설정**:
- `~/.cursor/rules/000-opal-agent.mdc`가 전역 자동 적용 (`alwaysApply: true`)
- 프로젝트당 추가 설정 불필요

**R-10 Gemini 수동 설정**:
- 프로젝트 루트 `GEMINI.md`에 OPAL 부트스트래퍼 삽입

#### Step 4: 빠른 시작 (R-12)

프로젝트 설정 직후, 핵심 개념 바로 앞에 배치. 설치 + opi 후 첫 파이프라인 체험 시나리오:
```
//opp README에 프로젝트 설명 추가해줘
```

#### Step 5: 비서/PM 역할 전환 (R-4)

핵심 개념 섹션(기존 "실행 흐름" 뒤)에 소섹션 추가:
- 비서 모드: 프로젝트 밖 (.opal/AGENT.md 없음) — 일상 대화, 일반 업무
- PM 모드: 프로젝트 내 (.opal/AGENT.md 존재) — 태스크 관리, 워커 지휘
- 전환 조건: `.opal/AGENT.md` 존재 여부로 자동 전환

#### Step 6: Pilot 비교 테이블 파이프라인 갱신 (R-1, R-2)

**R-1**:
- `opds` 행: `TASK → PLAN(+테스트 시나리오) → EXECUTE → TEST`
- `opd` 행: `TASK → ANALYSIS → PLAN(+테스트 시나리오) → EXECUTE → TEST`
- 산출물 컬럼에서 `TEST-SCENARIO` 제거, `PLAN`에 통합 명시

**R-2**:
- `opsdd` 행: `TASK → SPEC → VERIFY → REVIEW → DESIGN → EXECUTE-LOOP → DONE`

#### Step 7: opds/opd 사용법 갱신 (R-1)

opds 사용법(344~378줄):
- 파이프라인: `TASK → PLAN(+테스트 시나리오) → EXECUTE → TEST`
- 산출물: `TASK.md`, `PLAN.md`(테스트 시나리오 포함), `DONE.md`
- 진행 흐름: 2단계를 "PLAN.md 작성 (구현 계획 + 테스트 시나리오)"으로 통합

opd 사용법(380~406줄):
- 파이프라인: `TASK → ANALYSIS → PLAN(+테스트 시나리오) → EXECUTE → TEST`
- 산출물: `TASK.md`, `ANALYSIS.md`, `PLAN.md`(테스트 시나리오 포함), `DONE.md`
- 진행 흐름: 3단계를 "PLAN.md 작성 (구현 계획 + 테스트 시나리오)"으로 통합

#### Step 8: opsdd 파이프라인 갱신 (R-2)

opsdd 사용법(438~457줄):
- 파이프라인: `TASK → SPEC → VERIFY → REVIEW → DESIGN → EXECUTE-LOOP → DONE`
- VERIFY 단계 설명 1줄 추가: "SPEC 명세를 교차 검증하여 누락/모순을 점검한다"

#### Step 9: 전문 에이전트 섹션 (R-3)

Agentic Mode 뒤, 아키텍처 개요 앞에 신규 섹션 배치.

**내용**:
- 도입부 2~3문단: 범용 워커 → 전문 에이전트 전환 배경, PM이 단계+영역에 따라 적합한 에이전트를 선택·라우팅
- 6종 에이전트 테이블:

| 에이전트 | 영역 | 단계 | 역할 |
|---------|------|------|------|
| opal-plan-agent | 공통 | PLAN | 코드 분석 + 기능 설계 + 에이전트 라우팅 |
| opal-fe-agent | FE | EXECUTE | React, shadcn/ui, Tailwind 전문 구현 |
| opal-be-agent | BE | EXECUTE | API 설계, OWASP, 레이어 구조 전문 구현 |
| opal-db-agent | DB | PLAN, EXECUTE | DB 모델 설계 + 마이그레이션 |
| opal-planning-agent | 기획 | EXECUTE | 서비스 기획 산출물 (PRD, TRD 등) |
| opal-test-agent | 공통 | TEST | BE/FE/E2E 테스트 모드 |

- 폴백 동작: 전문 에이전트 미매칭 시 범용 `opal-task-agent` 사용

#### Step 10: 아키텍처 개요 보강 (R-3, R-5, R-6)

**R-3**: Global Layer 트리에 `agents/` 내부 전문 에이전트 표기:
```
agents/        서브에이전트 (전문 6종 + 범용 4종)
```

**R-5**: 트리 내부 또는 트리 아래에 1줄 추가:
"코드 파일에 `@header` 주석으로 메타데이터를 기록하고, `code-scan` 도구로 빠르게 탐색한다."

**R-6**: `references/` 라인에 하네스 모듈화 명시:
```
references/    레지스트리 + 모듈화된 하네스 (harness/)
```

커뮤니티 스킬 수 31개 → 37개로 정정.

#### Step 11: 트러블슈팅 (R-13)

아키텍처 개요 뒤 (README 최하단)에 신규 섹션. 2~3개 문제 케이스:

1. **부트스트랩 체크리스트가 뜨지 않음**: AI 도구 재시작 확인, `~/.opal/AGENT.md` 존재 확인, 부트스트래퍼 파일 확인
2. **`//` 커맨드 매칭 실패**: Node.js 설치 확인 (`node --version`), skill-registry 동작 확인
3. **MCP 연결 실패**: 플랫폼별 MCP 설정 파일 경로 확인, `claude mcp list` / Cursor mcp.json 확인

#### Step 12: 목차 갱신 (R-14)

신규 섹션을 반영하여 목차 재작성. 앵커 링크가 각 섹션 제목과 정확히 매칭되는지 확인.

#### Step 13: 전체 일관성 확인 (R-15, R-16)

- R-15: 기존 섹션과 신규 섹션의 어투(존댓말+친근, 한국어 본문+영어 코드), 테이블 스타일, 코드블록 스타일 통일
- R-16: 핵심 철학 5항목(사용자 주권·단계적 실행·문서화 우선·플랫폼 독립·프로젝트 학습) 그대로 유지 확인

---

## 3. 실행 체크리스트

> 총 13개 Step | Phase 5개
>
> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | 1     | 1    | 순차 | 주요 특징 (README.md 상단) |
> | 2     | 2    | 순차 | 설치 섹션 확장 (README.md) |
> | 3     | 3, 4, 5 | 순차 | 프로젝트 설정 → 빠른 시작 → 비서/PM (동일 파일 내 순차 삽입) |
> | 4     | 6, 7, 8, 9, 10, 11 | 순차 | 비교 테이블 → 사용법 → 전문 에이전트 → 아키텍처 → 트러블슈팅 |
> | 5     | 12, 13 | 순차 | 목차 갱신 → 전체 일관성 확인 |

**참고**: 단일 파일(README.md)에 대한 모든 수정이므로, 모든 Step은 순차 실행이다. Phase 구분은 논리적 그룹핑(위→아래 순서 수정)을 나타낸다.

### Step 1: 주요 특징 항목 추가
- [x] 완료
- **파일**: `README.md` (32~36줄)
- **작업 내용**: 기존 주요 특징 5개 리스트에 "전문 에이전트(Specialist Agent)" 항목 1개 추가 — "도메인별 전문 워커가 FE/BE/DB/기획/테스트를 담당"
- **완료 기준**: 주요 특징 리스트에 6개 항목이 존재하고, 전문 에이전트 항목이 포함됨
- **테스트**: Read로 32~40줄 확인
- **의존**: 없음
- **요구사항**: R-3

### Step 2: 설치 섹션 확장
- [x] 완료
- **파일**: `README.md` (60~77줄 영역)
- **작업 내용**:
  - R-7: "사전 요구사항" 서브섹션 추가 (OS, 필수 도구, 지원 플랫폼)
  - R-8: 기존 설치 옵션 테이블 아래에 "[1] OPAL 설치 상세", "[2] MCP 서버 설정 상세" 서브섹션 추가. `install-mac.sh` 실제 구현 기반 경로 명기
  - R-9: "설치 후 검증" 서브섹션 추가 (`ls ~/.opal/` 기대 출력, 부트스트랩 체크리스트 확인)
- **완료 기준**: 설치 섹션에 "사전 요구사항", 옵션별 상세(경로 테이블 포함), "설치 후 검증" 3개 서브섹션이 존재. 경로가 install-mac.sh 실제 구현과 일치
- **테스트**: Read로 설치 섹션 전체 확인 + install-mac.sh와 경로 대조
- **의존**: 없음
- **요구사항**: R-7, R-8, R-9

### Step 3: 프로젝트 설정 확장
- [x] 완료
- **파일**: `README.md` (80~111줄 영역)
- **작업 내용**:
  - R-11: `//opi` 안내 아래에 생성물 3개(`.opal/AGENT.md`, `docs/PROJECT.md`, `docs/CONVENTIONS.md`) 역할 테이블 추가
  - R-10: "수동 설정 — Cursor" 서브섹션 추가 (전역 자동 적용 설명), "수동 설정 — Gemini" 서브섹션 추가 (GEMINI.md 부트스트래퍼)
- **완료 기준**: `//opi` 생성물 테이블 존재, Claude Code/Cursor/Gemini 각각의 설정 방법이 1개 이상 문장으로 명시
- **테스트**: Read로 프로젝트 설정 섹션 확인
- **의존**: Step 2
- **요구사항**: R-10, R-11

### Step 4: 빠른 시작 섹션 추가
- [x] 완료
- **파일**: `README.md` (프로젝트 설정 섹션 뒤, 핵심 개념 앞)
- **작업 내용**: "빠른 시작" 섹션 신규 추가 — 설치+프로젝트 설정 직후 `//opp` 예시 명령어로 파이프라인을 체감하는 1문단 + 코드블록
- **완료 기준**: "빠른 시작" 섹션에 실제 입력 가능한 `//opp ...` 형식 명령어 1개 이상 존재
- **테스트**: Read로 빠른 시작 섹션 확인
- **의존**: Step 3
- **요구사항**: R-12

### Step 5: 비서/PM 역할 전환 소섹션 추가
- [x] 완료
- **파일**: `README.md` (핵심 개념 섹션 내부, "실행 흐름" 뒤)
- **작업 내용**: "비서 모드와 PM 모드" 소섹션(2~3문단) 추가 — 비서/PM 정의, `.opal/AGENT.md` 존재 여부로 자동 전환, PM 모드에서 워커 지휘·Gate 검토 수행
- **완료 기준**: README에 "비서"와 "PM" 용어가 역할 구분으로 등장하고, 전환 조건이 `.opal/AGENT.md` 존재 여부임이 명시
- **테스트**: Read로 핵심 개념 섹션 내 소섹션 확인
- **의존**: Step 4
- **요구사항**: R-4

### Step 6: Pilot 비교 테이블 파이프라인 갱신
- [x] 완료
- **파일**: `README.md` (168~177줄 영역)
- **작업 내용**:
  - R-1: `opds` 행 파이프라인을 `TASK → PLAN(+테스트 시나리오) → EXECUTE → TEST`로 변경, 산출물에서 `TEST-SCENARIO` 제거
  - R-1: `opd` 행 파이프라인을 `TASK → ANALYSIS → PLAN(+테스트 시나리오) → EXECUTE → TEST`로 변경, 산출물에서 `TEST-SCENARIO` 제거
  - R-2: `opsdd` 행 파이프라인을 `TASK → SPEC → VERIFY → REVIEW → DESIGN → EXECUTE-LOOP → DONE`으로 변경 (VERIFY 추가)
- **완료 기준**: 비교 테이블에서 opds/opd에 TEST-SCENARIO 별도 단계 없음, PLAN에 통합 명시. opsdd에 VERIFY 존재
- **테스트**: Read로 비교 테이블 확인
- **의존**: Step 5
- **요구사항**: R-1, R-2

### Step 7: opds/opd 사용법 갱신
- [x] 완료
- **파일**: `README.md` (344~406줄 영역)
- **작업 내용**:
  - opds 사용법: 파이프라인 문자열, 산출물 목록, 진행 흐름 3곳 갱신. TEST-SCENARIO를 PLAN에 통합
  - opd 사용법: 동일 적용
  - QA Gate 관련 문구 제거 (있는 경우)
- **완료 기준**: opds/opd 사용법에서 TEST-SCENARIO 단계가 별도로 나오지 않고, PLAN 단계에 "+테스트 시나리오 포함" 문구 명시
- **테스트**: Read로 opds/opd 사용법 섹션 확인
- **의존**: Step 6
- **요구사항**: R-1

### Step 8: opsdd 파이프라인 갱신
- [x] 완료
- **파일**: `README.md` (438~457줄 영역)
- **작업 내용**: opsdd 사용법의 파이프라인 문자열에 `VERIFY`를 `SPEC`과 `REVIEW` 사이에 삽입
- **완료 기준**: opsdd 파이프라인 문자열에 `VERIFY`가 포함됨
- **테스트**: Read로 opsdd 사용법 확인
- **의존**: Step 7
- **요구사항**: R-2

### Step 9: 전문 에이전트 섹션 추가
- [x] 완료
- **파일**: `README.md` (Agentic Mode 뒤, 아키텍처 개요 앞)
- **작업 내용**: "전문 에이전트 (Specialist Agent)" 신규 섹션 — 도입부 2~3문단 + 6종 에이전트 테이블(이름, 영역, 단계, 역할) + 폴백 동작 설명
- **완료 기준**: (a) 전문 에이전트 섹션 존재. (b) 6종 에이전트의 이름과 역할 1줄 요약이 테이블로 존재. (c) 폴백 동작 언급
- **테스트**: Read로 신규 섹션 확인. agents.md의 6종과 이름/역할이 일치하는지 대조
- **의존**: Step 8
- **요구사항**: R-3

### Step 10: 아키텍처 개요 보강
- [x] 완료
- **파일**: `README.md` (614~636줄 영역, Step 9 삽입으로 줄 번호 이동)
- **작업 내용**:
  - R-3: Global Layer 트리의 `agents/` 라인에 "전문 6종 + 범용 4종" 표기
  - R-5: 트리 아래에 "@header 메타데이터 + code-scan 탐색" 1문장 추가
  - R-6: `references/` 라인에 "모듈화된 하네스 (harness/)" 추가
  - community-skills 숫자 31개 → 37개 정정
- **완료 기준**: 아키텍처 트리에 `agents/` 전문 에이전트 표기, `references/harness/` 또는 "모듈화된 하네스" 존재, `@header`와 `code-scan` 언급, community-skills 37개
- **테스트**: Read로 아키텍처 개요 섹션 확인
- **의존**: Step 9
- **요구사항**: R-3, R-5, R-6

### Step 11: 트러블슈팅 섹션 추가
- [x] 완료
- **파일**: `README.md` (아키텍처 개요 뒤, README 최하단)
- **작업 내용**: "트러블슈팅" 섹션 신규 — 부트스트랩 미동작, // 커맨드 매칭 실패, MCP 연결 실패 3개 케이스 + 각 대응법
- **완료 기준**: 트러블슈팅 섹션에 2개 이상 문제 케이스와 각각의 대응법 존재
- **테스트**: Read로 트러블슈팅 섹션 확인
- **의존**: Step 10
- **요구사항**: R-13

### Step 12: 목차 갱신
- [x] 완료
- **파일**: `README.md` (40~57줄 영역)
- **작업 내용**: 목차를 최종 섹션 구조에 맞게 재작성. 신규 섹션(빠른 시작, 전문 에이전트, 트러블슈팅) 추가. 앵커 링크가 각 섹션 제목과 정확히 매칭되는지 확인
- **완료 기준**: 목차의 모든 항목이 실제 섹션 제목과 매칭되고, 앵커 링크가 유효
- **테스트**: 목차 항목을 실제 섹션 제목과 1:1 대조
- **의존**: Step 11 (모든 섹션 추가/수정 완료 후)
- **요구사항**: R-14

### Step 13: 전체 일관성 및 핵심 철학 확인
- [x] 완료
- **파일**: `README.md` 전체
- **작업 내용**:
  - R-15: 기존 섹션과 신규 섹션의 어투(존댓말+정보 전달 톤), 테이블 스타일(헤더 포함), 코드블록 스타일(```bash, ``` 등) 일관성 확인·수정
  - R-16: 핵심 철학 5항목(사용자 주권·단계적 실행·문서화 우선·플랫폼 독립·프로젝트 학습) 테이블이 변경 없이 유지되는지 확인
- **완료 기준**: R-15 — 신규 섹션이 기존 섹션과 동일한 어투·형식 사용. R-16 — 핵심 철학 5항목 테이블이 원본 그대로 유지
- **테스트**: Read로 핵심 철학 테이블 원문 대조 + 신규 섹션 어투 샘플링 확인
- **의존**: Step 12
- **요구사항**: R-15, R-16

---

## 4. QA 체크리스트

### 기능 테스트
- [x] R-1: opds/opd 파이프라인에서 TEST-SCENARIO가 별도 단계로 나오지 않고 PLAN에 통합 표기
- [x] R-2: opsdd 파이프라인에 VERIFY가 SPEC과 REVIEW 사이에 존재
- [x] R-3: 주요 특징에 전문 에이전트 항목 존재 + 아키텍처 트리에 agents/ 전문 에이전트 표기 + 6종 테이블 섹션 존재
- [x] R-4: "비서"와 "PM" 역할 전환 설명 + `.opal/AGENT.md` 존재 여부 전환 조건 명시
- [x] R-5: @header와 code-scan이 아키텍처 개요에 언급
- [x] R-6: references/harness/ 또는 "모듈화된 하네스" 표현 존재
- [x] R-7: 사전 요구사항(OS, 도구, 플랫폼) 서브섹션 존재
- [x] R-8: 설치 옵션별 배치 경로가 install-mac.sh 실제 구현과 일치
- [x] R-9: 설치 후 검증 명령과 기대 결과 존재
- [x] R-10: Claude Code, Cursor, Gemini 각각의 프로젝트 설정 방법 명시
- [x] R-11: //opi 생성물 3개의 역할 테이블 존재
- [x] R-12: 빠른 시작 섹션에 `//opp ...` 형식 명령어 1개 이상 존재
- [x] R-13: 트러블슈팅 섹션에 2개 이상 문제 케이스와 대응법 존재
- [x] R-14: 목차가 모든 섹션을 반영하고 앵커 링크 유효
- [x] R-15: 신규 섹션이 기존 어투·형식과 일관
- [x] R-16: 핵심 철학 5항목 테이블 변경 없음

### 일관성 테스트
- [x] 파이프라인 표기가 비교 테이블과 각 Pilot 사용법에서 일치
- [x] 에이전트 이름이 agents.md 레지스트리와 정확히 일치
- [x] 설치 경로가 install-mac.sh의 실제 함수 구현과 일치
- [x] 목차 앵커와 실제 섹션 제목이 1:1 대응

### 문서 품질
- [x] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가
- [x] GitHub Flavored Markdown 렌더링에 문제 없는가 (테이블, 코드블록, 앵커)
- [x] 기존 636줄 대비 과도한 분량 증가 없음 (목표: 800~850줄 이내)

---

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| R-8 설치 경로 오기재 | 사용자가 잘못된 경로를 참조하여 혼란 | install-mac.sh의 `install_opal`, `install_mcp` 함수를 직접 Read하여 경로 확인 완료. EXECUTE 시에도 재확인 |
| R-3 전문 에이전트 섹션 과도한 분량 | README 전체 분량 급증으로 가독성 저하 | 테이블 1개 + 도입부 2~3문단으로 제한 (상세는 ARCHITECTURE.md 참조 링크) |
| R-1 파이프라인 표기 불일치 | 비교 테이블, 사용법, 진행 흐름 간 표기가 달라질 수 있음 | Step 6~7에서 3곳(비교 테이블, 파이프라인, 진행 흐름)을 함께 갱신. QA에서 일관성 교차 검증 |
| 목차 앵커 깨짐 | 신규 섹션 추가 후 앵커 링크 미동작 | Step 12에서 목차를 최종 제목과 대조. GitHub Markdown 앵커 규칙(소문자, 하이픈 변환) 준수 |
| R-16 핵심 철학 실수 변경 | 프레임워크 정체성 훼손 | Step 1에서 핵심 철학 테이블 영역은 수정하지 않음. Step 13에서 원문 대조 검증 |
| 섹션 배치 순서 혼란 | 정보 흐름이 부자연스러워 사용자 경험 저하 | 설치 → 프로젝트 설정 → 빠른 시작 → 핵심 개념 순서로 "설치-사용-이해" 자연 흐름 설계 |
| community-skills 숫자 변동 | 현재 37개인데 추후 변동 가능 | ARCHITECTURE.md 기준 37개로 정정. 동적 숫자 대신 "30개+" 같은 근사치 사용도 고려 |
