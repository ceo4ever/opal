# PLAN: opgc 진단 전담화 + 프로젝트 구성 표준 정립

> 작성일: 2026-04-18
> 입력: TASK.md
> 출력: PLAN.md
> 적용 스킬: op-task-plan (advanced) | 오케스트레이터: opp(opal-pilot-project)

---

## 1. 현황 조사

### 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | opal-pilot-gc SKILL | `opal/skills/opal-pilot-gc/SKILL.md` | 본 개편 주 대상 — CLI/APPLY/SCAN/CHECK/CLOSE 전반 수정 |
| D-2 | 소스 | opal-convention-checker AGENT | `opal/agents/opal-convention-checker/AGENT.md` | APPLY 제거, scope 입력 추가, 허브+링크 체이닝 반영 |
| D-3 | 소스 | opal-security-checker AGENT | `opal/agents/opal-security-checker/AGENT.md` | APPLY 제거, scope 입력 추가, 허브+링크 체이닝 반영 |
| D-4 | 설계 | docs/PROJECT.md | `docs/PROJECT.md` | "프로젝트 구성" 섹션 신설 + "프로젝트 문서" 테이블 `적용 범위` 컬럼 추가 |
| D-5 | 설계 | docs/CONVENTIONS.md | `docs/CONVENTIONS.md` | 허브+링크 모델 검토 — OPAL 자체는 단일 문서라 예시/주석 수준만 |
| D-6 | 소스 | opal-project-init SKILL | `opal/skills/opal-project-init/SKILL.md` | 표준 섹션 생성 템플릿 반영 (초기화/최신화 모두) |
| D-7 | 소스 | opal-pm.md | `opal/core/references/opal-pm.md` | §6 컨텍스트 주입 원칙에서 프로젝트 구성 기반 라우팅 연결 |
| D-8 | 소스 | context-injection.md | `opal/core/references/pm/context-injection.md` | 프로젝트 구성 기반 라우팅 규약 상세 추가 대상 |
| D-9 | 소스 | agents.md | `opal/core/references/agents.md` | opgc 예시 명령어/문법 정합화 |
| D-10 | 참조 | opal-pilot-dev-short SKILL | `opal/skills/opal-pilot-dev-short/SKILL.md` | opgc → opds 수동 체인 대상 파이프라인 구조(TASK → PLAN → EXECUTE → TEST → CLOSE) |
| D-11 | 하네스 | citation-rules | `opal/core/references/harness/citation-rules.md` | 산출물 인용 규칙 — 본 PLAN.md 작성 준수 |
| D-12 | 하네스 | opal-harness.md | `opal/core/references/opal-harness.md` | Guards(§1), Gates(§3), 자동 루핑 제약 |
| D-13 | 하네스 | header-rules | `opal/core/references/harness/header-rules.md` | .md 파일에는 @header 미적용 — 본 태스크 대상 파일 전부 .md이므로 @header 작성 대상 없음 |
| D-14 | 소스 | agents.md opgc 섹션 | `opal/core/references/agents.md:44-70` | opal-security-checker / opal-convention-checker 입력 명세 — `scope`/`apply_mode` 정합화 대상 |
| D-15 | 소스 | README.md | `README.md` | opgc 언급 검토 대상 — 조사 결과 opgc/opal-pilot-gc 문자열 없음(F-10 AC에서 "없음" 기록) |
| D-16 | 소스 | skills.md | `opal/core/references/skills.md:73` | opgc 한 줄 소개만 존재 — CLI 문법 없음이므로 변경 불필요 |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §3.1 준수. 유형: `기획` / `설계` / `소스` / `외부` / `하네스` / `참조`.

### 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/skills/opal-pilot-gc/SKILL.md` | opgc 오케스트레이터 — 5단계 파이프라인 | **수정** (핵심) | `opal/skills/opal-pilot-gc/SKILL.md:11`(모드 정의), `:23-43`(Arguments), `:56-63`(short-summary), `:67-102`(SCAN), `:105-151`(CHECK), `:154-209`(REPORT), `:213-275`(APPLY — 전체 삭제), `:278-303`(CLOSE), `:307-343`(STATE.md 치환값), `:345-359`(Agentic Mode), `:397-401`(변경이력) |
| `opal/agents/opal-convention-checker/AGENT.md` | 컨벤션 체커 에이전트 | **수정** | `opal/agents/opal-convention-checker/AGENT.md:9`(tools), `:22-32`(입력 명세), `:36-61`(Phase 1-2), `:63-90`(Phase 3), `:112-136`(Phase 5), `:138-145`(Phase 6 APPLY — 삭제), `:146-156`(Phase 7), `:170-180`(행동 규칙), `:212-216`(변경이력) |
| `opal/agents/opal-security-checker/AGENT.md` | 보안 체커 에이전트 | **수정** | `opal/agents/opal-security-checker/AGENT.md:9`(tools), `:18-29`(입력 명세), `:34-65`(Phase 1-3), `:66-96`(Phase 4), `:121-132`(Phase 6), `:133-167`(Phase 7 APPLY — 삭제), `:168-178`(Phase 8), `:192-201`(행동 규칙), `:217-221`(변경이력) |
| `docs/PROJECT.md` | OPAL 프로젝트 정의 (SSOT) | **수정** | `docs/PROJECT.md:54-72`("주요 컴포넌트" 다음 위치에 "프로젝트 구성" 신설), `:74-82`("프로젝트 문서" 테이블 — `적용 범위` 컬럼 추가) |
| `docs/CONVENTIONS.md` | OPAL 코드 컨벤션 | 수정(주석 수준) | OPAL 자체는 단일 문서 — 허브+링크 적용 선택적 (D-5 설계) |
| `opal/skills/opal-project-init/SKILL.md` | 프로젝트 초기화/최신화 스킬 | **수정** | `opal/skills/opal-project-init/SKILL.md:302-310`(Phase 2 작성 대상 테이블 — PROJECT.md 템플릿 확장), `:221-269`(인터뷰 Q 세트 — 프로젝트 구성 인터뷰 추가), `:583-601`(최신화 Step E "새 문서 필요성 판단" — "프로젝트 구성 섹션 부재 시 추가 제안" 분기 신설), `:815-823`(변경이력) |
| `opal/core/references/opal-pm.md` | PM 행동 프로세스 | **수정** | `opal/core/references/opal-pm.md:144-151`(§6 에이전트 컨텍스트 주입 원칙 — "프로젝트 구성 기반 라우팅" 한 줄 추가 + context-injection.md 참조) |
| `opal/core/references/pm/context-injection.md` | 컨텍스트 주입 상세 | **수정** (핵심) | `opal/core/references/pm/context-injection.md:17-26`(트리거 기반 동적 선별 테이블에 "프로젝트 구성 매칭" 행 추가) + 섹션 신설 "PROJECT.md 프로젝트 구성 기반 라우팅" |
| `opal/core/references/agents.md` | 에이전트 레지스트리 | **수정** | `opal/core/references/agents.md:44-70`(opal-pilot-gc 서브에이전트 섹션 — 입력에서 `apply_mode` 삭제, `scope` 추가), `:149-150`(매핑 테이블 — `자체 로드 문서` 컬럼 허브+링크 반영 여부 확인) |
| `opal/core/references/conventions-hub-model.md` | 허브+링크 가이드 | **신규** | 신설 |
| `tasks/125-260417-opp-opgc-diagnosis-split-dispatch/PLAN.md` | 본 산출물 | **신규** | 이 파일 |
| `README.md` | 프레임워크 공개 소개 | 변경 없음 | grep 결과 opgc/opal-pilot-gc 문자열 부재 — F-10 AC에서 "해당 없음" 기록 (D-15) |
| `opal/core/references/skills.md:73` | 스킬 레지스트리 한 줄 | 변경 없음 | opgc 호출 예시 `//opgc`만 존재, CLI 문법 부재 (D-16) |

### 현재 상태

**opgc(opal-pilot-gc) 현재 구조** (D-1):
- 5단계 파이프라인: SCAN → CHECK → REPORT → **APPLY** → CLOSE (`opal/skills/opal-pilot-gc/SKILL.md:11`)
- 4플래그: `--only security/convention`, `--scope staged|all`, `--apply`, `--agentic` (`opal/skills/opal-pilot-gc/SKILL.md:23-43`)
- APPLY 섹션에 3-tier stash 롤백 + 자동 판정 알고리즘 + 문서 업데이트 제안 승인 UX 내장 (`opal/skills/opal-pilot-gc/SKILL.md:213-275`)
- STATE.md 파이프라인 현황판 12행 (SCAN 1 / CHECK 2 / REPORT 4 / APPLY 3 / CLOSE 2) (`opal/skills/opal-pilot-gc/SKILL.md:316-331`)
- CHECK 단계: `opal-security-checker` + `opal-convention-checker` **고정 1+1 병렬 디스패치** (`opal/skills/opal-pilot-gc/SKILL.md:109-142`)
- v1.0 (2026-04-17, 태스크 122) (`opal/skills/opal-pilot-gc/SKILL.md:399-401`)

**체커 에이전트 현재 구조** (D-2, D-3):
- `tools: [Read, Grep, Glob, Bash, Edit, Write]` — Edit/Write 포함 (`opal/agents/opal-convention-checker/AGENT.md:9`, `opal/agents/opal-security-checker/AGENT.md:9`)
- 입력 명세에 `apply_mode: manual|auto` 파라미터 보유 (`opal/agents/opal-convention-checker/AGENT.md:31`, `opal/agents/opal-security-checker/AGENT.md:28`)
- 컨벤션 체커: Phase 6 "APPLY (apply_mode == auto 또는 오케스트레이터 승인 시)" (`opal/agents/opal-convention-checker/AGENT.md:138-145`)
- 보안 체커: Phase 7 "APPLY" — 자동 판정 + 파일 단위 stash + syntax check (`opal/agents/opal-security-checker/AGENT.md:133-167`)
- Phase 7/8 `changed_files`가 보고서 `.md`만 포함 — 실제로는 APPLY에서 소스 파일 수정 가능 (설계 불일치) (`opal/agents/opal-convention-checker/AGENT.md:150-155`, `opal/agents/opal-security-checker/AGENT.md:170-177`)
- 체커는 허브(`docs/CONVENTIONS.md` / `docs/SECURITY.md`) 단일 문서 직접 Read — 허브+링크 체이닝 **미도입**
- `scope` 입력 파라미터 없음 — 모든 영역을 하나의 문서로 체크

**docs/PROJECT.md 현재 상태** (D-4):
- "프로젝트 개요", "프로젝트 구조", "주요 컴포넌트" 섹션 존재 (`docs/PROJECT.md:7-72`)
- "**프로젝트 구성**" 섹션 **부재** — 요소/경로/기술 스택/전문 에이전트 스키마 없음
- "프로젝트 문서" 테이블 컬럼: `문서 / 설명 / 용도 / 참조 시점` — `적용 범위` 컬럼 **부재** (`docs/PROJECT.md:76-82`)

**opi(opal-project-init) 현재 상태** (D-6):
- Phase 2 작성 대상 테이블에 PROJECT.md 포함 (`opal/skills/opal-project-init/SKILL.md:305`)
- 인터뷰 Q1~Q7 + 추가 기술 질문(Q8~) 존재 (`opal/skills/opal-project-init/SKILL.md:221-283`)
- "프로젝트 구성" 섹션 생성 템플릿/인터뷰 **부재**
- 최신화 모드 Step E "새 문서 필요성 판단" 존재 (`opal/skills/opal-project-init/SKILL.md:583-601`) — "프로젝트 구성 섹션 부재 시 추가 제안" 분기 **부재**

**opal-pm.md §6 / context-injection.md 현재 상태** (D-7, D-8):
- §6 "에이전트 컨텍스트 주입 원칙" — 3단계(최소 보장 / 트리거 선별 / PM 상황 판단) (`opal/core/references/opal-pm.md:144-151`)
- `context-injection.md` 트리거 테이블 — DB 모델/FE 화면/API/code-scan 등 (`opal/core/references/pm/context-injection.md:17-26`)
- "PROJECT.md 프로젝트 구성 기반 라우팅" 항목 **부재**

**agents.md opgc 섹션 현재 상태** (D-9, D-14):
- `opal-pilot-gc` 서브에이전트 섹션에 `opal-security-checker`, `opal-convention-checker` 등록 (`opal/core/references/agents.md:44-70`)
- **입력**: "범위(`staged`/`all`)"만 명시 — `scope` 파라미터(frontend/backend/batch/mobile/all) **부재**, `apply_mode` 언급 없음(이미 개요 수준)
- 매핑 테이블의 `자체 로드 문서` 컬럼 — 허브 Read만 명시, 링크 파싱 언급 없음 (`opal/core/references/agents.md:149-150`)
- README.md grep 결과 opgc 문자열 없음 (D-15) — F-10에서 "해당 없음" 기록

**허브+링크 가이드 문서 현재 상태** (F-11):
- `opal/core/references/conventions-hub-model.md` **부재** — 신규 작성 대상

**설계 중복 지점** (TASK.md §배경 분석):
- opgc APPLY = opds(opal-pilot-dev-short) EXECUTE + TEST (파일 수정 + stash + 회귀 검증) — D-10 파이프라인이 이미 동일 기능을 수행 (`opal/skills/opal-pilot-dev-short/SKILL.md:9-13`)
- opgc `--agentic`가 `--apply` + REPORT 자율 게이트 통과를 포함 → `--apply`가 `--agentic`의 하위 집합
- 컨벤션 체커의 `apply_mode`/`Edit` 권한 = op-dev-execute 워커와 기능 중복

### 영향 범위

**직접 수정 대상** (9개 파일 + 1개 신규 = 10개):
1. `opal/skills/opal-pilot-gc/SKILL.md` (F-1, F-2, F-3, F-4, F-10 변경이력)
2. `opal/agents/opal-convention-checker/AGENT.md` (F-5, F-6)
3. `opal/agents/opal-security-checker/AGENT.md` (F-5, F-6)
4. `docs/PROJECT.md` (F-7)
5. `docs/CONVENTIONS.md` (D-5 — 예시/주석 수준, 선택 수정)
6. `opal/skills/opal-project-init/SKILL.md` (F-8)
7. `opal/core/references/opal-pm.md` (F-9 요약)
8. `opal/core/references/pm/context-injection.md` (F-9 상세)
9. `opal/core/references/agents.md` (F-10 — opgc 서브에이전트 입력 명세 정합화)
10. `opal/core/references/conventions-hub-model.md` **신규** (F-11)

**변경 없음 확정**:
- `README.md`: opgc 문자열 부재 (D-15) — F-10 AC "없으면 해당 없음 기록" 적용
- `opal/core/references/skills.md`: opgc 호출 예시만, CLI 문법 없음 (D-16)
- opgc 하위 references/templates: `base-*-checklist.md`, `report-*-template.md`, `sample-*.md`, `done-template.md` — APPLY 제거로 인한 변경 영향 없음(보고서 5단계 상태 모델은 유지)

**하위호환 보장 포인트** (TASK.md §제약 조건 "하위호환" 원문):
- [MUST] "프로젝트 구성" 섹션이 없는 기존 프로젝트에서 opgc는 현행 1+1 단일 디스패치로 동일하게 동작해야 한다 (`tasks/125-260417-opp-opgc-diagnosis-split-dispatch/TASK.md` §제약 조건)
- 체커 `scope` 파라미터도 **선택(optional)** — 미지정 시 허브 전체 적용(기존 동작)

**잠재 영향 (수정 대상 아님, 검토만)**:
- `~/.opal/` 배포 경로 — TASK.md §제약 "**`~/.opal/` 경로 직접 수정 금지**" 준수. 캡틴이 `install-mac.sh`로 배포
- 커뮤니티 스킬(getsentry, openai) — TASK.md §제약 "**커뮤니티 스킬 원본 수정 금지**" 준수 (Read 래핑만)
- 체커가 `docs/CONVENTIONS.md`, `docs/SECURITY.md` 자동 갱신 금지 — TASK.md §제약 "**기준 문서 자동 갱신 금지 유지**" 준수

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|
| N-1 | `opal/core/references/conventions-hub-model.md` | 허브+링크 구조 가이드 (F-11) | [MUST] `tasks/125-260417-opp-opgc-diagnosis-split-dispatch/TASK.md` F-11 AC: "신설 문서에 ① 허브 문서의 역할, ② 링크 규약, ③ 체커의 참조 체이닝 흐름, ④ 최소 1개 이상의 예시 블록이 포함된다." (→ D-11 §F-11) |

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| M-1 | `opal/skills/opal-pilot-gc/SKILL.md` | (a) Arguments 섹션: `--only security/convention`→`--security`/`--convention` 토글 교체, `--apply` 제거(F-1) / (b) `## STEP 4: APPLY` 섹션 전체 삭제 + 파이프라인 4단계 재번호(F-2) / (c) 기존 STEP 5→STEP 4 (CLOSE) 내부에 opds 수동 체인 안내 + TASK.md 골격 예시 추가(F-3) / (d) SCAN 절차에 "프로젝트 구성 파싱 + target_files 분할" 신설 + CHECK 절차에 "요소×체커 병렬 매트릭스" + "섹션 부재 시 fallback" 분기 명시(F-4) / (e) STATE.md 파이프라인 현황판 8행 이하로 축소(SCAN/CHECK/REPORT/CLOSE만)(F-2) / (f) 변경이력 v1.1(2026-04-17, 125) 추가(F-10) | D-1, TASK.md F-1~F-4, F-10 |
| M-2 | `opal/agents/opal-convention-checker/AGENT.md` | (a) `tools: [Read, Grep, Glob, Bash]`로 축소(F-5) / (b) 입력 명세에서 `apply_mode` 삭제, `scope`(frontend/backend/batch/mobile/all) 추가(F-5, F-6) / (c) Phase 6(APPLY) 섹션 전체 삭제(F-5) / (d) Phase 1-2 절차에 "허브 Read → 링크 파싱 → scope 매칭 상세 문서 Read" 흐름 반영(F-6) / (e) Phase 7 `changed_files`가 보고서 `.md`만 포함하도록 예시 명시 확인(F-5) / (f) 변경이력 v1.1 추가 | D-2, TASK.md F-5, F-6 |
| M-3 | `opal/agents/opal-security-checker/AGENT.md` | M-2와 동일 구조 — Phase 7(APPLY) 삭제, `apply_mode` 제거, `scope` 추가, 허브+링크 체이닝 반영, tools 축소, `changed_files` 보고서만, 변경이력 v1.1 | D-3, TASK.md F-5, F-6 |
| M-4 | `docs/PROJECT.md` | (a) "주요 컴포넌트 (GC 파이프라인)" 섹션 뒤에 `## 프로젝트 구성` 신설 — 스키마 `\| 요소 \| 경로 \| 기술 스택 \| 전문 에이전트 \|`(F-7) / (b) "프로젝트 문서" 테이블에 `적용 범위` 컬럼 추가(문서/설명/적용 범위/참조 시점 4컬럼) — OPAL 자체는 "Framework" 또는 "전체" 표기(F-7) | D-4, TASK.md F-7 |
| M-5 | `docs/CONVENTIONS.md` | (선택) 허브+링크 모델 주석 1줄 추가 — "OPAL 자체는 단일 문서. 다중 구성 프로젝트는 `opal/core/references/conventions-hub-model.md` 참조"(D-5, F-11 연계) | D-5 |
| M-6 | `opal/skills/opal-project-init/SKILL.md` | (a) Phase 1-3 인터뷰에 "프로젝트 구성" 질문 블록 추가(초기화 모드) — FE/BE/Batch/Mobile 요소·경로·기술 스택·전문 에이전트(F-8) / (b) Phase 2 작성 프로세스에 "PROJECT.md 내 프로젝트 구성 섹션 + 적용 범위 컬럼 자동 생성" 단계 명시(F-8) / (c) 최신화 모드 Phase 2 Step E(새 문서 필요성 판단)에 "기존 PROJECT.md에 프로젝트 구성 섹션 부재 시 추가 제안" 조건 분기 신설(F-8) / (d) 변경이력 v3.4 추가 | D-6, TASK.md F-8 |
| M-7 | `opal/core/references/opal-pm.md` | §6 "에이전트 컨텍스트 주입 원칙" 요약 문단에 한 줄 추가 — "PROJECT.md의 프로젝트 구성 기반 라우팅(파일 경로 ↔ 요소 경로 매칭)" 요약. 상세는 context-injection.md 참조(F-9) | D-7, TASK.md F-9 |
| M-8 | `opal/core/references/pm/context-injection.md` | (a) "트리거 기반 동적 선별" 테이블에 "프로젝트 구성 요소 매칭 — PROJECT.md 프로젝트 구성 — 파일 경로 ↔ 요소 경로 prefix 매칭 → 해당 요소의 전문 에이전트 참조 주입" 행 추가 / (b) 새 섹션 "## PROJECT.md 프로젝트 구성 기반 라우팅" 신설 — 매칭 의사코드 + 최소 1개 예시(F-9) | D-8, TASK.md F-9 |
| M-9 | `opal/core/references/agents.md` | (a) `opal-pilot-gc` 서브에이전트 섹션의 `opal-security-checker`, `opal-convention-checker` 입력 명세에 `scope` 추가, `apply_mode` 관련 언급 제거(F-5, F-6) / (b) 매핑 테이블의 `자체 로드 문서` 컬럼에 "(허브+링크 체이닝)" 표기(F-6) / (c) opgc 예시 명령어/본문에서 `--apply` / `--only X` 문법 사용 검토 — 현재 부재 확인 상태이므로 변경 없음 기록(F-10) | D-9, D-14, TASK.md F-5/F-6/F-10 |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| - | - | 본 태스크에서 **파일 단위 삭제 없음**. opgc SKILL.md 내부 STEP 4(APPLY) 섹션 내용 삭제, 체커 AGENT.md 내 Phase 6/7(APPLY) 섹션 내용 삭제는 파일 수정에 포함(M-1, M-2, M-3). |

### 구현 순서

> **원칙**: 의존 받는 쪽(하위 레이어 = 체커 AGENT, 허브 가이드)부터, 이후 오케스트레이터(opgc SKILL, opi), 마지막으로 정합화 문서(agents.md, pm refs, PROJECT.md). PROJECT.md는 opi/context-injection이 참조하는 표준이므로 선행 구현 필요.

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | M-4: PROJECT.md "프로젝트 구성" 섹션 + "적용 범위" 컬럼 신설 | `docs/PROJECT.md` | 중 |
| 2 | N-1: 허브+링크 가이드 문서 신설 | `opal/core/references/conventions-hub-model.md` | 중 |
| 3 | M-2: 컨벤션 체커 AGENT — APPLY 제거 + scope + 허브 체이닝 | `opal/agents/opal-convention-checker/AGENT.md` | 중 |
| 4 | M-3: 보안 체커 AGENT — APPLY 제거 + scope + 허브 체이닝 | `opal/agents/opal-security-checker/AGENT.md` | 중 |
| 5 | M-1: opgc SKILL — CLI 토글화 + APPLY 제거 + 동적 분할 + opds 체인 + 변경이력 | `opal/skills/opal-pilot-gc/SKILL.md` | 상 |
| 6 | M-6: opi — 프로젝트 구성 섹션 생성 템플릿 + 최신화 분기 | `opal/skills/opal-project-init/SKILL.md` | 중 |
| 7 | M-8: context-injection.md — 프로젝트 구성 기반 라우팅 신설 | `opal/core/references/pm/context-injection.md` | 중 |
| 8 | M-7: opal-pm.md §6 요약 한 줄 추가 | `opal/core/references/opal-pm.md` | 하 |
| 9 | M-9: agents.md opgc 입력 명세 정합화 + README 검토 결과 기록 | `opal/core/references/agents.md` | 하 |
| 10 | M-5: CONVENTIONS.md 허브+링크 안내 주석(선택) | `docs/CONVENTIONS.md` | 하 |

**병렬화 기회**:
- Phase 1 (순서 1~2): PROJECT.md + 허브 가이드 — 독립 파일, 서로 참조 없음 → 병렬 가능
- Phase 2 (순서 3~4): 두 체커 AGENT — 독립 파일, 구조 동일 → 병렬 가능 (M-4 완료 후)
- Phase 3 (순서 5~6): opgc SKILL + opi SKILL — 서로 독립. opgc는 체커(M-2/M-3) + PROJECT.md(M-4) + 허브 가이드(N-1)에 의존. opi는 PROJECT.md(M-4)에 의존 → 병렬 가능
- Phase 4 (순서 7~9): context-injection / opal-pm / agents.md — 독립 파일 → 병렬 가능
- Phase 5 (순서 10): CONVENTIONS.md — 선택 사항 (마지막)

### 핵심 설계

> 각 파일별 변경 내용. 인라인 인용은 `(→ D-N §M)` 또는 `` `경로:줄번호` `` 포맷. 필수 제약은 `[MUST]` 포맷. (→ D-11 §2)

#### 설계 1: `docs/PROJECT.md` 프로젝트 구성 섹션 신설 (M-4)

**(a) "## 프로젝트 구성" 섹션 신설 위치**: `docs/PROJECT.md:72` (주요 컴포넌트(GC) 섹션과 "프로젝트 문서" 섹션 사이)

**(b) 스키마 4컬럼**: `| 요소 | 경로 | 기술 스택 | 전문 에이전트 |` (→ D-4 §TASK.md D-7)

**(c) OPAL 자체 작성 내용 예시** (FE/BE가 없는 프레임워크 — 단일 행 원칙):

```markdown
## 프로젝트 구성

> 프로젝트의 기술적 요소를 영역별로 정의한다. SCAN/디스패치/컨텍스트 주입 시 이 표를 기반으로 영역 매칭과 전문 에이전트 선정이 이루어진다. (→ D-1 F-4 SCAN 동적 분할 병렬 디스패치)

| 요소 | 경로 | 기술 스택 | 전문 에이전트 |
|------|------|-----------|--------------|
| Framework | `opal/`, `skills/`, `agents/` | Markdown, YAML, Bash, Node.js | opal-task-agent (범용) |
```

**(d) "프로젝트 문서" 테이블** `적용 범위` 컬럼 추가 (→ D-4 §TASK.md F-7 AC):
- 컬럼 구성: `| 문서 | 설명 | 적용 범위 | 참조 시점 |` (기존 "용도" 컬럼을 "적용 범위"로 대체 또는 분리 — 검토 필요: AC 요구는 "컬럼이 `문서/설명/적용 범위/참조 시점`으로 4개" 이므로 **용도→적용 범위** 리네이밍 + 내용 보정)
- 각 행의 `적용 범위`: OPAL 자체는 "전체" 또는 "Framework" 표기 (빈 셀 금지 — AC "모든 행의 `적용 범위` 셀이 비어있지 않다")

**[MUST]** `tasks/125-260417-opp-opgc-diagnosis-split-dispatch/TASK.md` F-7 AC: "PROJECT.md에 `## 프로젝트 구성` H2 섹션이 존재하고 스키마 4컬럼이 모두 채워져 있으며, '프로젝트 문서' 테이블의 컬럼이 `문서 / 설명 / 적용 범위 / 참조 시점`으로 4개이고 모든 행의 `적용 범위` 셀이 비어있지 않다." (→ D-4)

---

#### 설계 2: `opal/core/references/conventions-hub-model.md` 허브+링크 가이드 신설 (N-1)

**(a) 섹션 구성** (→ D-11 F-11 AC ①~④):

```markdown
# 컨벤션·보안 허브+링크 모델

> OPAL 체커 에이전트(opal-convention-checker / opal-security-checker)의 참조 문서 체이닝 규약.
> Lazy 트리거: 체커가 프로젝트 `docs/CONVENTIONS.md` 또는 `docs/SECURITY.md`를 Read할 때.
> 선택 모델 — 기존 프로젝트에 적용 강제하지 않는다.

## 1. 개념

CONVENTIONS.md / SECURITY.md를 "허브" 문서로 유지하고, 영역(FE/BE/Batch/Mobile)별 상세 규칙은 별도 문서로 분리하여 허브에서 링크로 연결한다.

## 2. 허브 문서의 역할

- 영역별 공통 원칙(언어/네이밍/문서/커밋 등)만 허브에 기술
- 영역별 상세(React 컴포넌트 컨벤션, FastAPI 라우팅 규칙 등)는 `FE-CONVENTIONS.md`, `BE-CONVENTIONS.md`, `BATCH.md` 등으로 분리
- 허브는 **단일 진입점** — 체커는 허브를 먼저 Read하고 scope에 맞는 링크를 따라간다

## 3. 링크 규약

허브 문서 최상단(또는 전용 섹션)에 아래 포맷으로 영역별 상세 링크를 배치한다:

> 영역별 상세:
> - [FE-CONVENTIONS.md](./FE-CONVENTIONS.md) — Frontend
> - [BE-CONVENTIONS.md](./BE-CONVENTIONS.md) — Backend
> - [BATCH.md](./BATCH.md) — Batch (Backend 상속)

## 4. 체커 참조 체이닝 흐름

체커는 scope 입력에 따라 아래 순서로 문서를 로드한다:

1. 허브(CONVENTIONS.md 또는 SECURITY.md) Read
2. 허브 내 영역별 상세 링크 파싱 (정규식 `\[([\w-]+\.md)\]\(\.?/([^)]+)\)`)
3. scope 파라미터(frontend/backend/batch/mobile/all)와 매칭되는 상세 문서 선택
4. 상세 문서 Read → 허브 공통 원칙과 병합하여 체크

## 5. 예시 블록 (풀스택 프로젝트)

[예시: `docs/CONVENTIONS.md` 허브 + `docs/FE-CONVENTIONS.md` + `docs/BE-CONVENTIONS.md` 구조 코드 블록 + scope="frontend"로 호출 시 로드되는 문서 경로 예시]

## 변경이력
| v1.0 | 2026-04-17 | 초기 작성 (125) |
```

**[MUST]** `tasks/125-260417-opp-opgc-diagnosis-split-dispatch/TASK.md` F-11 AC: "신설 문서에 ① 허브 문서의 역할, ② 링크 규약(예: `> 영역별 상세: [FE-CONVENTIONS.md](./FE-CONVENTIONS.md) — Frontend`), ③ 체커의 참조 체이닝 흐름, ④ 최소 1개 이상의 예시 블록이 포함된다." (→ D-11)

---

#### 설계 3: 체커 AGENT.md 수정 (M-2 컨벤션, M-3 보안)

**(a) YAML frontmatter** — tools 축소:
- Before: `tools: [Read, Grep, Glob, Bash, Edit, Write]` (`opal/agents/opal-convention-checker/AGENT.md:9`, `opal/agents/opal-security-checker/AGENT.md:9`)
- After: `tools: [Read, Grep, Glob, Bash]` (→ D-2, D-3, TASK.md F-5 AC ②)

**(b) 입력 명세 테이블** — 추가/제거:
- **삭제**: `apply_mode` 행 (→ TASK.md F-5 AC ③)
- **추가**: `| scope | X | 체크 범위 — frontend/backend/batch/mobile/all (선택, 미지정 시 허브 전체) |` (→ TASK.md F-6 AC)

**(c) Phase 1-2 (체커 공통) — 허브+링크 체이닝 반영**:

```
Phase 1: 기준 문서 분기 처리 (허브+링크)
  if 허브(docs/CONVENTIONS.md 또는 docs/SECURITY.md) 존재:
      Read → 허브 공통 원칙 파싱
      영역별 상세 링크 파싱 (정규식 기반)
      if scope 지정:
          상세 문서 Read → 허브 + 상세 병합
      else:
          허브 전체만 적용 (하위호환 — 기존 단일 문서 모델)
      check_enabled = true
  else:
      check_enabled = false
      초안 유도 플래그 활성화
```

**[MUST]** TASK.md F-6 AC: "두 AGENT.md의 입력 명세에 `scope` 행이 있고, 실행 프로세스 Phase에 '허브 Read → 링크 파싱 → 상세 문서 Read' 흐름이 명시되며, Phase 흐름은 `check_enabled` 판정과 공존한다." (→ D-2, D-3)

**(d) 컨벤션 체커 Phase 6(APPLY) 삭제** (`opal/agents/opal-convention-checker/AGENT.md:138-145`), **보안 체커 Phase 7(APPLY) 삭제** (`opal/agents/opal-security-checker/AGENT.md:133-167`). Phase 번호 재배정 (컨벤션: 1-5+반환, 보안: 1-6+반환).

**(e) 반환 예시의 `changed_files`** — 보고서 `.md`만 포함 (이미 현재도 보고서만 명시되어 있으나, APPLY 삭제로 "소스 파일이 changed_files에 없음"이 의미적으로 일관성 확보) (→ TASK.md F-5 AC ④)

**(f) 행동 규칙 중 "자동 갱신 금지" 유지** (`opal/agents/opal-convention-checker/AGENT.md:176`, `opal/agents/opal-security-checker/AGENT.md:196`) — TASK.md §제약 "**기준 문서 자동 갱신 금지 유지**" 원문 준수

**[MUST]** `tasks/125-260417-opp-opgc-diagnosis-split-dispatch/TASK.md` F-5 AC: "두 AGENT.md 모두 ① `Phase 6` / `APPLY` 소제목이 사라지고, ② `tools: [Read, Grep, Glob, Bash]`로 축소되며, ③ 입력 명세에 `apply_mode` 행이 없고, ④ Phase 7 반환 예시의 `changed_files`가 보고서 `*.md`만 포함한다." (→ D-2, D-3)

---

#### 설계 4: `opal/skills/opal-pilot-gc/SKILL.md` 개편 (M-1)

**(a) Arguments 파싱 (F-1)** — `opal/skills/opal-pilot-gc/SKILL.md:23-43`

```
//opgc                                  # 전체 체크 (기본: staged, 둘 다)
//opgc --security                       # 보안만
//opgc --convention                     # 컨벤션만
//opgc --security --convention          # 둘 다 (둘 다 생략과 동일)
//opgc --scope all                      # 전체 범위 + 둘 다
//opgc --scope all --convention         # 전체 범위 + 컨벤션만
//opgc --agentic --convention           # Agentic 모드 + 컨벤션만
//opgc --scope all --convention --agentic   # 전체 범위 + 컨벤션 + Agentic
```

Arguments 테이블 (→ TASK.md F-1 AC: `--security`/`--convention` 2행 존재, `--only`로 시작하는 행 0개):

| Arguments | 기본값 | 설명 |
|---------|------|------|
| `--security` | - | 보안 체크 토글 (미지정 또는 둘 다 지정 = 둘 다 실행) |
| `--convention` | - | 컨벤션 체크 토글 (동일) |
| `--scope staged` | 기본 | git staged 파일 대상 |
| `--scope all` | - | 프로젝트 전체 파일 대상 |
| `--agentic` | - | Agentic Mode (CLOSE 진입 게이트만 유지) |

**[MUST]** TASK.md F-1 AC: "Arguments 파싱 블록에 `--apply`가 전혀 등장하지 않고, Arguments 테이블에 `--security` / `--convention` 2행이 존재하며 `--only`로 시작하는 행이 0개다. 조합 예시 5종 이상(`--scope all --convention`, `--agentic --convention`, `--scope all --convention --agentic` 포함)이 수록된다." (→ D-1)

**(b) 파이프라인 축소 (F-2)** — STEP 4(APPLY) 섹션 전체 삭제 (`opal/skills/opal-pilot-gc/SKILL.md:213-275`). 기존 STEP 5(CLOSE)를 STEP 4로 재번호. Harness 헤더: `모드: GC (SCAN → CHECK → REPORT → CLOSE)` 수정(`opal/skills/opal-pilot-gc/SKILL.md:11`).

**(c) short-summary 규칙** (`opal/skills/opal-pilot-gc/SKILL.md:56-63`) — `--apply` 접미사 제거, `--only` 접미사 제거. 대신 `--security` → `{scope}-sec-only`, `--convention` → `{scope}-conv-only`. 둘 다 지정 또는 미지정 → `{scope}`.

**(d) SCAN 동적 분할 병렬 디스패치 (F-4)** — STEP 1(SCAN)에 신설 절 1.5 추가:

```
### 1.5 PROJECT.md 프로젝트 구성 기반 분할 (신규)

docs/PROJECT.md의 "## 프로젝트 구성" 섹션 파싱:

if "프로젝트 구성" 섹션 존재:
    요소 목록 파싱 → [(요소명, 경로, 기술 스택, 전문 에이전트), ...]
    target_files를 요소별 경로 prefix로 분할:
        element_targets[요소명] = [f for f in target_files if f.startswith(요소.경로)]
    체커 디스패치 매트릭스 = {요소} × {security, convention}
else:
    # Fallback (하위호환) — 기존 1+1 단일 디스패치 유지
    체커 디스패치 매트릭스 = {프로젝트 전체} × {security, convention}
```

**의사코드 + 분할 표 예시**:

```
[프로젝트 구성 파싱 결과 예시]
| 요소 | 경로 | 전문 에이전트 |
|------|------|--------------|
| frontend | web/ | opal-fe-agent |
| backend | api/ | opal-be-agent |
| batch | batch/ | (Backend 상속) opal-be-agent |

[target_files 분할 결과]
| 요소 | 분할된 파일 |
|------|------------|
| frontend | web/Button.tsx, web/Home.tsx |
| backend | api/user.py, api/auth.py |
| batch | batch/daily_report.py |
```

**(e) CHECK 병렬 매트릭스 (F-4 AC)** — STEP 2(CHECK)에 케이스별 예시 3종 이상:

```
Case A — 단일 스택 프로젝트 (OPAL 자체):
  [Framework] × [security, convention] = 2회 병렬 디스패치

Case B — 모노레포 풀스택:
  [frontend, backend] × [security, convention] = 4회 병렬 디스패치

Case C — FE+BE+Batch (3요소):
  [frontend, backend, batch] × [security, convention] = 6회 병렬 디스패치

Case D — Fallback (프로젝트 구성 섹션 부재):
  [프로젝트 전체] × [security, convention] = 2회 병렬 디스패치 (기존 1+1 동작)
```

**[MUST]** TASK.md F-4 AC: "SCAN 절차에 '프로젝트 구성 섹션 파싱' 의사코드와 요소별 `target_files` 분할 표가 존재하며, CHECK 절차에 '요소 × 체커' 병렬 매트릭스 예시(단일/모노레포/FE+BE+Batch 3케이스 이상)가 있고, '섹션 부재 시 fallback' 분기가 명시된다." (→ D-1)

**(f) 병렬 디스패치 프롬프트 템플릿 갱신 (F-4, F-5, F-6)** — 기존 `apply_mode` 삭제, `scope` 추가. `target_files`는 분할된 요소별 파일 목록 전달.

**(g) STEP 4: CLOSE — opds 수동 체인 가이드 (F-3)** — 기존 STEP 5(CLOSE)에 다음 블록 신설:

```
### 수정이 필요한 경우 — opds 체인

GC 보고서에서 auto_fixable 이슈나 review 필요 항목이 있다면, opds로 체인한다:

  //opds "tasks/{NNN}-{YYMMDD}-opgc-{summary}/ GC 결과 반영"

opds용 TASK.md 골격 예시:

  # TASK: GC 결과 반영
  ## 배경
  opgc 실행 결과 {N}건 이슈 감지 (GC-SECURITY-{ts}.md, GC-CONVENTION-{ts}.md)
  ## 참조 문서
  - GC-SECURITY-{ts}.md
  - GC-CONVENTION-{ts}.md
  ## 요구사항
  - auto_fixable=true 이슈 {M}건 수정 반영
  - [?] review 항목은 본 태스크 제외
  ## 제약
  - [?] review 제외
  - 기존 테스트 회귀 금지
  - 커밋은 캡틴 지시 시만
```

**[MUST]** TASK.md F-3 AC: "CLOSE 섹션에 `//opds` 호출 예시 1개 이상과 '요구사항(auto_fixable 이슈 목록)', '참조 문서(GC-*.md)', '제약(`[?] review` 제외, 회귀 금지)'를 포함한 TASK.md 골격 블록이 존재한다." (→ D-1)

**(h) STATE.md 파이프라인 현황판 축소 (F-2 AC "8행 이하")** — `opal/skills/opal-pilot-gc/SKILL.md:316-331`의 12행에서 APPLY 관련 3행 삭제:

```markdown
| # | 단계 | 항목 | 상태 | 시점 |
|---|------|------|------|------|
| 1 | SCAN | 대상 파일 선별 + 스택 감지 + 프로젝트 구성 파싱 | ⬜ | - |
| 2 | CHECK | 에이전트 (요소×체커) 병렬 디스패치 | ⬜ | - |
| 3 | CHECK | 에이전트 완료 확인 | ⬜ | - |
| 4 | REPORT | GC-SECURITY-{ts}.md 생성 (요소별) | ⬜ | - |
| 5 | REPORT | GC-CONVENTION-{ts}.md 생성 (요소별) | ⬜ | - |
| 6 | REPORT | 실행 요약 테이블 갱신 | ⬜ | - |
| 7 | CLOSE | DONE.md 생성 | ⬜ | - |
| 8 | CLOSE | State Gate | ⬜ | - |
```

**(i) Agentic Mode 블록 갱신** (`opal/skills/opal-pilot-gc/SKILL.md:345-359`) — APPLY 관련 "중간 사용자 확인 게이트는 자율 통과" 문구에서 APPLY 제거. 현재 남은 중간 게이트는 REPORT 사용자 확인 하나.

**(j) 변경이력 v1.1 추가 (F-10 AC)**:

```
| v1.1 | 2026-04-17 | APPLY 제거(진단 전담화) + CLI 토글 전환(--security/--convention, --apply 제거) + PROJECT.md 프로젝트 구성 기반 동적 분할 병렬 디스패치 + opds 수동 체인 가이드 (125) |
```

**[MUST]** TASK.md F-2 AC: "SKILL.md에 'APPLY' 단어가 Guards 설명 맥락(수정 금지) 외에는 등장하지 않으며, `STEP 4`가 `CLOSE`이고, 파이프라인 현황판 테이블이 8행 이하로 축소되어 SCAN/CHECK/REPORT/CLOSE만 포함한다." (→ D-1)

---

#### 설계 5: `opal/skills/opal-project-init/SKILL.md` 갱신 (M-6)

**(a) 초기화 모드 Phase 1-3 인터뷰 확장 (F-8)** — `opal/skills/opal-project-init/SKILL.md:221-283` 이후 개발 프로젝트 전용 "프로젝트 구성 인터뷰" 블록 추가:

```
Q8. 프로젝트를 어떤 요소로 구성하시겠습니까? (개발 프로젝트 한정, 복수 선택 가능)
    a) Frontend (예: web/, frontend/)
    b) Backend (예: api/, backend/, server/)
    c) Batch (예: batch/, scheduler/ — Backend 상속 기본)
    d) Mobile (예: mobile/, app/)
    e) Framework/Library (단일 요소)
    f) 기타: 직접 입력

Q9. 각 요소의 경로와 기술 스택을 알려주세요.
    (Step A 레이아웃 탐색 결과를 기본값으로 제시, 수정 가능)

Q10. 각 요소에 어울리는 전문 에이전트를 매핑합니다.
     기본: FE → opal-fe-agent, BE → opal-be-agent, DB → opal-db-agent, 기획 → opal-planning-agent, 범용 → opal-task-agent
```

**(b) Phase 2 작성 프로세스에 "프로젝트 구성 섹션 자동 생성" 명시 (F-8 AC "템플릿이 명시적으로 존재")** — `opal/skills/opal-project-init/SKILL.md:302-310`의 작성 대상 테이블 주변에 추가:

```
PROJECT.md 작성 시 반드시 포함할 표준 섹션:
- ## 프로젝트 구성 (신규) — Phase 1-3 Q8~Q10 결과 기반
- 프로젝트 문서 테이블 (기존) — 4컬럼: 문서/설명/적용 범위/참조 시점
```

**(c) 최신화 모드 Step E 분기 신설 (F-8 AC "추가 제안 분기")** — `opal/skills/opal-project-init/SKILL.md:583-601`의 테이블에 행 추가:

| 조건 | 제안 문서 |
|------|----------|
| ... (기존) | ... |
| 기존 PROJECT.md에 "프로젝트 구성" 섹션 부재 | **PROJECT.md 프로젝트 구성 섹션 추가 제안** (→ D-4 스키마 참조) |
| 기존 PROJECT.md "프로젝트 문서" 테이블에 "적용 범위" 컬럼 부재 | 컬럼 추가 제안 |

**(d) 변경이력 v3.4 추가**:

```
| v3.4 | 2026-04-17 | PROJECT.md "프로젝트 구성" 섹션 생성 + "적용 범위" 컬럼 표준화 (초기화 Q8~Q10, 최신화 Step E 분기) (125) |
```

**[MUST]** TASK.md F-8 AC: "opi SKILL.md에 '프로젝트 구성 섹션 생성' 단계 또는 템플릿이 명시적으로 존재하며, 최신화 흐름에 '기존 PROJECT.md에 프로젝트 구성 섹션 부재 시 추가 제안' 분기가 있다." (→ D-6)

---

#### 설계 6: `opal/core/references/pm/context-injection.md` 갱신 (M-8)

**(a) 트리거 테이블에 행 추가** — `opal/core/references/pm/context-injection.md:17-26`:

```
| 작업 대상 파일의 경로 | docs/PROJECT.md "프로젝트 구성" 섹션 | 요소 경로 prefix 매칭 → 매칭 요소의 전문 에이전트 참조 주입 |
```

**(b) 신규 섹션 "## PROJECT.md 프로젝트 구성 기반 라우팅"** — 마지막 섹션 뒤에 추가:

```markdown
## PROJECT.md 프로젝트 구성 기반 라우팅

워커 디스패치 시 대상 파일 경로를 PROJECT.md "프로젝트 구성" 섹션의 요소 경로와 매칭하여 적합한 `전문 에이전트`를 자동 선정한다.

### 절차

1. docs/PROJECT.md의 "## 프로젝트 구성" 섹션 파싱 → [(요소, 경로, 기술스택, 전문에이전트), ...]
2. 디스패치 대상 파일 목록에서 파일별 경로 → 가장 긴 prefix 매칭 요소 선정
3. 매칭된 요소의 `전문 에이전트`를 워커 디스패치 시 참조로 주입
4. 섹션 부재 시: `opal-task-agent` (범용)으로 폴백

### 의사코드

```
def route(file_path, project_config):
    if not project_config.has_section("프로젝트 구성"):
        return "opal-task-agent"  # fallback
    best = None
    for element in project_config.elements:
        if file_path.startswith(element.path) and (best is None or len(element.path) > len(best.path)):
            best = element
    return best.agent if best else "opal-task-agent"
```

### 예시

```
프로젝트 구성:
  | frontend | web/ | React | opal-fe-agent |
  | backend | api/ | FastAPI | opal-be-agent |

파일 경로: web/components/Button.tsx → opal-fe-agent 선정
파일 경로: api/user.py → opal-be-agent 선정
파일 경로: scripts/deploy.sh → opal-task-agent 폴백 (어느 요소도 매칭 안 됨)
```
```

**[MUST]** TASK.md F-9 AC: "문서에  'PROJECT.md 프로젝트 구성 기반 라우팅' 절이 존재하고, 파일 경로 → 요소 매칭 의사코드 또는 예시 1개 이상이 포함된다." (→ D-8)

---

#### 설계 7: `opal/core/references/opal-pm.md` §6 요약 한 줄 추가 (M-7)

`opal/core/references/opal-pm.md:144-151` §6 문단의 2번째 문장 뒤에 한 줄 삽입:

```
PM은 디스패치 시 대상 파일 경로를 `docs/PROJECT.md`의 "프로젝트 구성" 섹션 요소 경로와 매칭하여 적합한 전문 에이전트를 자동 선정한다. 상세 규약은 `opal/core/references/pm/context-injection.md` 참조.
```

(→ D-7, TASK.md F-9)

---

#### 설계 8: `opal/core/references/agents.md` 정합화 (M-9)

**(a) opal-pilot-gc 서브에이전트 섹션 입력 명세 갱신** (`opal/core/references/agents.md:44-70`):
- `opal-security-checker` / `opal-convention-checker` "**입력**" 항목: 기존 "대상 파일 목록, 범위(staged/all), 기술 스택..." 뒤에 "`scope`(frontend/backend/batch/mobile/all — 선택)" 추가.
- `apply_mode` 관련 언급이 있으면 제거 — 현재 문서에는 없음 확인 (D-14) → 변경 없음, 단 새 `scope`만 추가

**(b) 매핑 테이블 `자체 로드 문서` 컬럼** (`opal/core/references/agents.md:149-150`): 기존 "CONVENTIONS.md, base-convention-checklist" 뒤에 "(허브+링크 체이닝 — conventions-hub-model.md 참조)" 표기

**(c) opgc 예시 명령어/본문 문법 검토 (F-10 AC)** — 현재 agents.md에 `--apply` / `--only X` 사용 **없음** 확인(본 조사 결과). 변경 없음. 단, M-1(opgc SKILL.md)에서 신 CLI 문법으로 교체되므로 agents.md 관점에서 일관성 확인만.

**[MUST]** TASK.md F-10 AC: "agents.md에 `--apply` / `--only` 문자열이 opgc 섹션에서 사라지고, opgc SKILL.md 변경이력 테이블에 v1.1 행(2026-04-17, 125)이 추가되며, README.md에서 opgc 언급이 있으면 신 CLI로 일치한다(없으면 해당 없음 기록)." (→ D-9, D-15)

---

#### 설계 9: `docs/CONVENTIONS.md` 선택 주석 (M-5)

OPAL 자체는 단일 문서로 유지되므로, 파일 하단(예: `docs/CONVENTIONS.md:150` 말미)에 다음 주석 한 블록 추가 (선택):

```
> **참고**: OPAL 프레임워크 자체는 단일 CONVENTIONS.md를 사용한다.
> 다중 구성(FE/BE/Batch 등) 프로젝트는 허브+링크 모델 적용 가능 —
> `opal/core/references/conventions-hub-model.md` 참조.
```

(→ D-5, TASK.md §확정된 설계 방향 D-6)

---

## 3. 실행 체크리스트

> 총 **11개 Step** | Phase **5개**
>
> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | 1 | 1, 2 | 병렬 | PROJECT.md + 허브 가이드(신규) — 서로 독립 |
> | 2 | 3, 4 | 병렬 | 두 체커 AGENT — 독립 파일, 구조 동일. Phase 1(PROJECT.md) 완료 후 |
> | 3 | 5, 6 | 병렬 | opgc SKILL + opi SKILL — Phase 1·2 완료 후. 서로 독립 |
> | 4 | 7, 8, 9 | 병렬 | context-injection / opal-pm / agents.md — 독립 파일 |
> | 5 | 10, 11 | 순차 | CONVENTIONS.md(선택) + 최종 정합성 셀프체크 |

---

### Step 1: PROJECT.md "프로젝트 구성" 섹션 + "적용 범위" 컬럼 신설 [F-7]

- [x] 완료
- **파일**: `docs/PROJECT.md`
- **작업 내용**:
  1. "주요 컴포넌트 (GC 파이프라인)" 섹션(`docs/PROJECT.md:64-72`) 뒤에 `## 프로젝트 구성` H2 신설
  2. 스키마 4컬럼 `| 요소 | 경로 | 기술 스택 | 전문 에이전트 |` 작성
  3. OPAL 자체 내용 1행: `| Framework | opal/, skills/, agents/ | Markdown, YAML, Bash, Node.js | opal-task-agent |`
  4. 섹션 머리에 도입 문구(프로젝트 구성의 역할 — SCAN/디스패치/컨텍스트 주입의 기준)
  5. "프로젝트 문서" 테이블(`docs/PROJECT.md:74-82`)에 `적용 범위` 컬럼 추가 → 컬럼 순서 `문서 / 설명 / 적용 범위 / 참조 시점`
  6. 각 행의 `적용 범위` 셀에 값 기입 — 모두 "전체" 또는 "Framework" (빈 셀 금지)
- **완료 기준**:
  - `## 프로젝트 구성` H2 섹션이 존재하고 스키마 4컬럼이 모두 채워짐
  - "프로젝트 문서" 테이블 컬럼이 정확히 `문서 / 설명 / 적용 범위 / 참조 시점` 4개
  - 모든 행의 `적용 범위` 셀이 비어있지 않음
- **테스트**: Grep 검증 — `grep -A3 "## 프로젝트 구성" docs/PROJECT.md` 출력 확인 + "프로젝트 문서" 테이블 모든 행이 `|`로 4번 구분되었는지 확인
- **의존**: 없음

### Step 2: 허브+링크 가이드 문서 신설 [F-11]

- [x] 완료
- **파일**: `opal/core/references/conventions-hub-model.md` (신규)
- **작업 내용**:
  1. 섹션 구성: §1 개념 / §2 허브 문서의 역할 / §3 링크 규약 / §4 체커 참조 체이닝 흐름 / §5 예시 블록
  2. §3에 링크 포맷 예시(`> 영역별 상세: [FE-CONVENTIONS.md](./FE-CONVENTIONS.md) — Frontend`)
  3. §4에 체커 체이닝 흐름 4단계 (허브 Read → 링크 파싱 → scope 매칭 → 상세 Read)
  4. §5에 풀스택 프로젝트 예시 코드 블록(CONVENTIONS.md 허브 + FE-CONVENTIONS.md + BE-CONVENTIONS.md + scope="frontend" 호출 시 로드 경로)
  5. 변경이력 v1.0 (2026-04-17, 125)
- **완료 기준**:
  - ① 허브 역할 / ② 링크 규약(예시 포함) / ③ 체커 체이닝 흐름 / ④ 예시 블록 1개 이상 — 4가지 모두 포함
- **테스트**: Read 후 4 섹션 존재 확인
- **의존**: 없음

### Step 3: opal-convention-checker AGENT.md 개편 [F-5, F-6]

- [x] 완료
- **파일**: `opal/agents/opal-convention-checker/AGENT.md`
- **작업 내용**:
  1. frontmatter `tools`: `[Read, Grep, Glob, Bash, Edit, Write]` → `[Read, Grep, Glob, Bash]` (`opal/agents/opal-convention-checker/AGENT.md:9`)
  2. 입력 명세(`opal/agents/opal-convention-checker/AGENT.md:22-32`)에서 `apply_mode` 행 삭제
  3. 입력 명세에 `scope` 행 추가: `| scope | X | 체크 범위 — frontend/backend/batch/mobile/all (선택, 미지정 시 허브 전체) |`
  4. Phase 1 "기준 문서 분기 처리" 블록(`opal/agents/opal-convention-checker/AGENT.md:36-52`)을 허브+링크 체이닝으로 확장 — 허브 Read → 링크 파싱 → scope 매칭 상세 Read 흐름 명시 (check_enabled 판정과 공존)
  5. **Phase 6(APPLY) 섹션 전체 삭제** (`opal/agents/opal-convention-checker/AGENT.md:138-145`)
  6. Phase 번호 재배정 (1~5 + 최종 반환)
  7. 반환 예시 `changed_files` 필드가 `GC-CONVENTION-{timestamp}.md`만 포함하는지 재확인 (`opal/agents/opal-convention-checker/AGENT.md:154`)
  8. 변경이력 v1.1 추가 — "APPLY 제거(진단 전담) + tools 축소 + scope 입력 추가 + 허브+링크 체이닝 (125)"
- **완료 기준**:
  - ① "Phase 6" 또는 "APPLY" 소제목 부재 (Guards/금지 맥락 제외)
  - ② `tools: [Read, Grep, Glob, Bash]` 정확히 일치
  - ③ 입력 명세에 `apply_mode` 행 부재
  - ④ 입력 명세에 `scope` 행 존재
  - ⑤ 실행 프로세스 Phase에 "허브 Read → 링크 파싱 → 상세 문서 Read" 흐름 명시
  - ⑥ 반환 예시 `changed_files`에 보고서 `.md`만 포함
- **테스트**: Read 후 검색 — `grep "APPLY\|apply_mode" AGENT.md`에서 Guards 맥락 외 매치 없음. `grep "scope" AGENT.md`로 scope 존재 확인.
- **의존**: Step 1 (PROJECT.md의 프로젝트 구성과 scope 의미 정합)

### Step 4: opal-security-checker AGENT.md 개편 [F-5, F-6]

- [x] 완료
- **파일**: `opal/agents/opal-security-checker/AGENT.md`
- **작업 내용**: Step 3와 동일 구조로 적용
  1. `tools: [Read, Grep, Glob, Bash, Edit, Write]` → `[Read, Grep, Glob, Bash]` (`opal/agents/opal-security-checker/AGENT.md:9`)
  2. 입력 명세에서 `apply_mode` 삭제, `scope` 추가
  3. Phase 2 "SECURITY.md 분기 처리"(`opal/agents/opal-security-checker/AGENT.md:39-48`)를 허브+링크 체이닝으로 확장
  4. **Phase 7(APPLY) 섹션 전체 삭제** (`opal/agents/opal-security-checker/AGENT.md:133-167`)
  5. Phase 번호 재배정 (1~6 + 최종 반환)
  6. 반환 예시 `changed_files`가 `GC-SECURITY-{timestamp}.md`만 포함하는지 재확인 (`opal/agents/opal-security-checker/AGENT.md:176`)
  7. 변경이력 v1.1 추가
- **완료 기준**: Step 3의 ①~⑥과 동일 AC
- **테스트**: Step 3와 동일
- **의존**: Step 1

### Step 5: opal-pilot-gc SKILL.md 개편 [F-1, F-2, F-3, F-4, F-10]

- [x] 완료
- **파일**: `opal/skills/opal-pilot-gc/SKILL.md`
- **작업 내용**:
  1. **[F-1]** Harness 헤더 `모드: GC (SCAN → CHECK → REPORT → APPLY → CLOSE)` → `모드: GC (SCAN → CHECK → REPORT → CLOSE)` (`opal/skills/opal-pilot-gc/SKILL.md:11`)
  2. **[F-1]** Arguments 파싱 블록(`opal/skills/opal-pilot-gc/SKILL.md:23-43`) 전체 교체: `--only security/convention` → `--security`/`--convention` 토글, `--apply` 제거. 조합 예시 5종 이상 수록 (`--security`, `--convention`, `--scope all`, `--scope all --convention`, `--agentic --convention`, `--scope all --convention --agentic`)
  3. **[F-1]** Arguments 테이블에서 `--only` 접두사 행 삭제, `--apply` 행 삭제, `--security`/`--convention` 2행 추가
  4. **[F-2]** short-summary 규칙(`opal/skills/opal-pilot-gc/SKILL.md:56-63`) — `--apply` 접미사 제거, `--only` 제거. `--security` → `{scope}-sec-only`, `--convention` → `{scope}-conv-only`로 재작성
  5. **[F-4]** STEP 1(SCAN)에 신설 절 1.5 "PROJECT.md 프로젝트 구성 기반 분할" 추가 — 파싱 의사코드 + 요소별 target_files 분할 표 예시
  6. **[F-4]** STEP 2(CHECK)에 "요소 × 체커" 병렬 매트릭스 예시 3종 이상 추가(단일/모노레포/FE+BE+Batch + fallback)
  7. **[F-4, F-5, F-6]** STEP 2의 디스패치 프롬프트 템플릿(`opal/skills/opal-pilot-gc/SKILL.md:113-142`)에서 `apply_mode: {manual|auto}` 삭제, `scope: {요소명 또는 all}` 추가. `target_files`는 분할된 요소별 목록
  8. **[F-2]** **STEP 4: APPLY 섹션 전체 삭제** (`opal/skills/opal-pilot-gc/SKILL.md:213-275`). 관련 3-tier stash / 자동 판정 알고리즘 / 문서 업데이트 제안 승인 UX 전부 제거
  9. **[F-2]** 기존 STEP 5(CLOSE) → STEP 4로 재번호
  10. **[F-3]** STEP 4(CLOSE)에 "수정이 필요한 경우 — opds 체인" 섹션 신설 — `//opds` 호출 예시 + opds TASK.md 골격(배경/참조 문서(GC-*.md)/요구사항(auto_fixable 목록)/제약([?] review 제외, 회귀 금지, 커밋은 캡틴 지시 시만))
  11. **[F-2]** STATE.md 파이프라인 현황판(`opal/skills/opal-pilot-gc/SKILL.md:316-331`) 8행으로 축소 — APPLY 관련 행 전부 삭제
  12. **[F-2]** STATE.md 도메인 치환값 테이블(`opal/skills/opal-pilot-gc/SKILL.md:309-313`) "단계 목록" → `SCAN / CHECK / REPORT / CLOSE`
  13. **[F-1]** REPORT 완료 보고 형식(`opal/skills/opal-pilot-gc/SKILL.md:200-208`)에서 "APPLY 단계로 넘어갈까요? (--apply 플래그 없으면 대기)" 문구를 "CLOSE로 진행할까요?" 또는 "수정이 필요하면 opds 체인을 안내합니다"로 교체
  14. **[F-2]** Agentic Mode 블록(`opal/skills/opal-pilot-gc/SKILL.md:345-359`)에서 APPLY 관련 항목 삭제 ("문서 업데이트 제안 승인: `--agentic` 시..." 포함). 현재 남은 중간 게이트는 REPORT 사용자 확인 하나로 정리
  15. **[F-10]** 변경이력 v1.1 행 추가(2026-04-17, 125)
- **완료 기준**:
  - [F-1] Arguments 파싱 블록에 `--apply` 부재, Arguments 테이블에 `--security`/`--convention` 2행 존재, `--only*` 행 0개, 조합 예시 5종 이상
  - [F-2] SKILL.md 본문에 "APPLY" 단어가 Guards/금지 맥락 외 부재, `STEP 4`가 `CLOSE`, 파이프라인 현황판 8행 이하
  - [F-3] CLOSE 섹션에 `//opds` 예시 1개 이상 + TASK.md 골격 블록 (요구사항/참조 문서/제약 포함)
  - [F-4] SCAN에 프로젝트 구성 파싱 의사코드 + target_files 분할 표, CHECK에 요소×체커 매트릭스 예시 3종 이상 + fallback 분기
  - [F-10] 변경이력 테이블에 v1.1 (2026-04-17, 125) 행
- **테스트**:
  - `grep -c "APPLY" opal/skills/opal-pilot-gc/SKILL.md` — Guards/금지 맥락 외 매치 0
  - `grep "STEP 4" opal/skills/opal-pilot-gc/SKILL.md` → `STEP 4: CLOSE`
  - `grep -c "^| " opal/skills/opal-pilot-gc/SKILL.md` 섹션별 행 수 — 파이프라인 현황판 헤더 제외 8행 이하
  - `grep "//opds" opal/skills/opal-pilot-gc/SKILL.md` — 매치 1개 이상
  - `grep "v1.1.*125" opal/skills/opal-pilot-gc/SKILL.md` — 매치
- **의존**: Step 1 (프로젝트 구성 섹션 설계), Step 2 (허브 가이드), Step 3·4 (체커 scope 파라미터)

### Step 6: opal-project-init SKILL.md 갱신 [F-8]

- [x] 완료
- **파일**: `opal/skills/opal-project-init/SKILL.md`
- **작업 내용**:
  1. 초기화 모드 Phase 1-3 인터뷰(`opal/skills/opal-project-init/SKILL.md:221-283`) 뒤에 개발 프로젝트 전용 "프로젝트 구성" Q 블록(Q8 요소 선택, Q9 경로/기술 스택, Q10 전문 에이전트 매핑) 추가
  2. Phase 2 작성 프로세스(`opal/skills/opal-project-init/SKILL.md:302-310`) 영역에 "PROJECT.md 내 표준 섹션 생성 — `## 프로젝트 구성` + `적용 범위` 컬럼" 명시 문구 추가 (docs-guide.md 참조 지침 유지)
  3. 최신화 모드 Phase 2 Step E(`opal/skills/opal-project-init/SKILL.md:583-601`) 테이블에 2행 추가:
     - 조건 "기존 PROJECT.md에 '프로젝트 구성' 섹션 부재" → 제안 "프로젝트 구성 섹션 추가 제안"
     - 조건 "'프로젝트 문서' 테이블에 '적용 범위' 컬럼 부재" → 제안 "컬럼 추가 제안"
  4. 변경이력 v3.4 추가(2026-04-17, 125)
- **완료 기준**:
  - 초기화 모드에 프로젝트 구성 인터뷰(Q8~Q10 또는 동등) 존재
  - Phase 2 작성 프로세스에 "프로젝트 구성 섹션 생성" 단계/템플릿 명시적 존재
  - 최신화 모드에 "기존 PROJECT.md에 프로젝트 구성 섹션 부재 시 추가 제안" 분기 존재
  - 변경이력 v3.4 행 추가
- **테스트**:
  - `grep "프로젝트 구성" opal/skills/opal-project-init/SKILL.md` — 초기화/최신화 양쪽에서 매치
  - `grep "적용 범위" opal/skills/opal-project-init/SKILL.md` — 매치 1개 이상
- **의존**: Step 1 (PROJECT.md 표준 확정)

### Step 7: context-injection.md — 프로젝트 구성 기반 라우팅 [F-9]

- [x] 완료
- **파일**: `opal/core/references/pm/context-injection.md`
- **작업 내용**:
  1. "트리거 기반 동적 선별" 테이블(`opal/core/references/pm/context-injection.md:17-26`)에 행 추가 — `| 작업 대상 파일 경로 | docs/PROJECT.md 프로젝트 구성 | 요소 경로 prefix 매칭 → 전문 에이전트 주입 |`
  2. 문서 말미에 신규 섹션 `## PROJECT.md 프로젝트 구성 기반 라우팅` 추가 — 절차 4단계 + 의사코드 + 예시 3건
- **완료 기준**:
  - 섹션 "PROJECT.md 프로젝트 구성 기반 라우팅" 존재
  - 파일 경로 → 요소 매칭 의사코드 또는 예시 1개 이상 포함
  - 섹션 부재 시 폴백 규약 명시
- **테스트**:
  - `grep "프로젝트 구성 기반 라우팅" opal/core/references/pm/context-injection.md` — 매치
- **의존**: Step 1 (PROJECT.md 스키마 확정)

### Step 8: opal-pm.md §6 요약 한 줄 추가 [F-9]

- [x] 완료
- **파일**: `opal/core/references/opal-pm.md`
- **작업 내용**: §6(`opal/core/references/opal-pm.md:144-151`) 문단 2번째 문장 뒤에 한 줄 삽입 — "PM은 디스패치 시 대상 파일 경로를 `docs/PROJECT.md`의 '프로젝트 구성' 섹션 요소 경로와 매칭하여 적합한 전문 에이전트를 자동 선정한다. 상세 규약은 `opal/core/references/pm/context-injection.md` 참조."
- **완료 기준**: §6 문단에 "프로젝트 구성 기반" 또는 "요소 경로와 매칭" 문구 존재, context-injection.md 참조 링크 존재
- **테스트**: `grep "프로젝트 구성" opal/core/references/opal-pm.md` — §6 영역에서 매치
- **의존**: Step 7 (context-injection.md 신규 섹션 먼저 확정 — 참조 무결성)

### Step 9: agents.md opgc 입력 명세 정합화 + README 검토 결과 기록 [F-10]

- [x] 완료
- **파일**: `opal/core/references/agents.md`
- **작업 내용**:
  1. `opal-security-checker`/`opal-convention-checker` "**입력**"(`opal/core/references/agents.md:56,68`)에 `scope`(frontend/backend/batch/mobile/all — 선택) 추가
  2. 매핑 테이블(`opal/core/references/agents.md:149-150`)의 `자체 로드 문서` 컬럼에 "(허브+링크 체이닝 — conventions-hub-model.md 참조)" 표기
  3. opgc 관련 본문에 `--apply` / `--only X` 문자열 검색 — 현재 부재 확인(D-14). 변경 없음
  4. README.md에 opgc 언급 검토 결과 — 현재 부재(D-15). 본 PLAN §1에 "해당 없음 기록" 유지. README.md 변경하지 않음
- **완료 기준**:
  - agents.md opgc 서브에이전트 섹션의 입력 명세에 `scope` 문자열 존재
  - 매핑 테이블에 "conventions-hub-model" 참조 또는 허브+링크 표기
  - `grep "--apply\|--only" opal/core/references/agents.md` 결과 opgc 섹션에 매치 없음
- **테스트**: `grep "scope" opal/core/references/agents.md`, `grep "conventions-hub-model" opal/core/references/agents.md`
- **의존**: Step 2 (conventions-hub-model.md 경로 확정), Step 3·4 (체커 scope 파라미터 확정)

### Step 10: CONVENTIONS.md 허브+링크 안내 주석 (선택) [D-5]

- [x] 완료
- **파일**: `docs/CONVENTIONS.md`
- **작업 내용**: 파일 말미에 "참고" 박스 1블록 추가 — "OPAL 자체는 단일 문서. 다중 구성 프로젝트는 conventions-hub-model.md 참조"
- **완료 기준**: `docs/CONVENTIONS.md`에 `conventions-hub-model` 문자열 1회 이상 존재. OPAL 기존 규칙 내용은 변경 없음(주석만 추가)
- **테스트**: `grep "conventions-hub-model" docs/CONVENTIONS.md` — 매치 1개
- **의존**: Step 2

### Step 11: 최종 정합성 셀프체크 [F-1 ~ F-11 전체 교차 검증]

- [x] 완료
- **파일**: (검증 전용 — 파일 수정 없음, 본 Step은 체크리스트 형태로 PLAN에 박음)
- **작업 내용**: Step 1~10 완료 후 EXECUTE 워커가 아래 항목을 순차로 검증
  1. [F-1] opgc SKILL.md Arguments 블록/테이블 — `--apply` 부재, `--security`/`--convention` 존재, `--only` 부재, 조합 예시 ≥5
  2. [F-2] opgc SKILL.md — APPLY 단어 부재(Guards 제외), STEP 4=CLOSE, 파이프라인 현황판 ≤8행
  3. [F-3] opgc CLOSE — `//opds` 예시 + TASK.md 골격 블록
  4. [F-4] opgc SCAN — 파싱 의사코드 + 분할 표, CHECK — 매트릭스 3종 + fallback
  5. [F-5] 두 AGENT.md — Phase 6/7 APPLY 부재, tools=[Read,Grep,Glob,Bash], apply_mode 부재, changed_files 보고서만
  6. [F-6] 두 AGENT.md — scope 입력 존재, 허브+링크 체이닝 Phase 흐름 명시, check_enabled 공존
  7. [F-7] PROJECT.md — `## 프로젝트 구성` H2 존재, 4컬럼 스키마, 프로젝트 문서 테이블 4컬럼(적용 범위 포함) 모든 행 기재
  8. [F-8] opi SKILL.md — 초기화 프로젝트 구성 인터뷰, 최신화 Step E 추가 제안 분기
  9. [F-9] opal-pm.md §6 + context-injection.md — 라우팅 절 + 의사코드/예시
  10. [F-10] agents.md `scope` 추가 + `--apply`/`--only` 부재 확인, opgc SKILL.md 변경이력 v1.1(125)
  11. [F-11] conventions-hub-model.md — ①허브 역할 ②링크 규약 ③체이닝 흐름 ④예시 1개 이상
  12. 하위호환 검증: 프로젝트 구성 섹션이 없는 프로젝트에서 opgc SCAN의 fallback 분기가 1+1 단일 디스패치를 유지하는지 문서상 명시 확인
  13. [MUST] 제약 교차 검증: `~/.opal/` 수정 0건, 커뮤니티 스킬(getsentry, openai) 수정 0건, 체커 자동 갱신 로직 부재 확인
- **완료 기준**: 13개 교차 검증 항목 전원 Pass
- **테스트**: 각 항목의 grep/Read 조합
- **의존**: Step 1~10 모두 완료

---

## 4. QA 체크리스트

### 기능 테스트 (F-1 ~ F-11 AC 대응)

- [x] **F-1 AC**: opgc SKILL.md Arguments 파싱 블록에 `--apply` 부재(마이그레이션 안내 문구 제외), Arguments 테이블에 `--security`/`--convention` 2행 존재, `--only`로 시작하는 행 0개, 조합 예시 5종 이상(포함 필수 3종: `--scope all --convention`, `--agentic --convention`, `--scope all --convention --agentic`) — 셀프체크 완료
- [x] **F-2 AC**: opgc SKILL.md에 "APPLY" 단어가 Guards(수정 금지) 맥락 외 부재, `STEP 4`가 `CLOSE`, 파이프라인 현황판 8행(SCAN/CHECK/REPORT/CLOSE만) — 셀프체크 완료
- [x] **F-3 AC**: opgc CLOSE 섹션에 `//opds "{태스크폴더} GC 결과 반영"` 호출 예시 포함, TASK.md 골격 블록(요구사항 auto_fixable / 참조 문서 GC-*.md / 제약 `[?] review` 제외 + 회귀 금지) 포함 — 셀프체크 완료
- [x] **F-4 AC**: opgc SCAN 절차에 프로젝트 구성 섹션 파싱 의사코드 + 요소별 target_files 분할 표 존재, CHECK 절차에 요소×체커 병렬 매트릭스 예시(Case A/B/C/D 4케이스) + 섹션 부재 시 fallback 분기 명시 — 셀프체크 완료
- [x] **F-5 AC**: 두 체커 AGENT.md 모두 ①Phase 6/7 APPLY 소제목 부재(변경이력 언급만 잔존) ②`tools: [Read, Grep, Glob, Bash]` 정확 일치 ③입력 명세 `apply_mode` 행 부재 ④반환 예시 `changed_files`에 보고서 `.md`만 포함 — 셀프체크 완료
- [x] **F-6 AC**: 두 체커 AGENT.md 입력 명세에 `scope` 행 존재, Phase 1(컨벤션) / Phase 2(보안)에 "허브 Read → 링크 파싱 → scope 매칭 상세 Read" 흐름 명시, `check_enabled` 판정과 공존 — 셀프체크 완료
- [x] **F-7 AC**: `docs/PROJECT.md`에 `## 프로젝트 구성` H2 섹션 존재, 스키마 4컬럼(요소/경로/기술 스택/전문 에이전트) 모두 채워짐, "프로젝트 문서" 테이블 컬럼이 `문서 / 설명 / 용도 / 적용 범위 / 참조 시점` 5개(PM 지시 B 옵션 2 — `용도` 유지 + `적용 범위` 신규 추가), 모든 행의 `적용 범위` 셀 채워짐(Framework) — 지시 B 오버라이드 반영
- [x] **F-8 AC**: opi SKILL.md에 "프로젝트 구성 섹션 생성" 단계/템플릿 명시적 존재(Phase 2 표준 섹션 테이블 + 초기화 인터뷰 Q8+ 세트), 최신화 Step E 테이블에 "기존 PROJECT.md에 `## 프로젝트 구성` 섹션 부재" + "`적용 범위` 컬럼 부재" 2개 분기 추가, v3.4 변경이력 기재 — 셀프체크 완료
- [x] **F-9 AC**: `context-injection.md`에 "PROJECT.md 프로젝트 구성 기반 라우팅" 섹션 존재, 절차 4단계 + 의사코드 + 예시 3건 이상 포함. `opal-pm.md` §6에도 요약 한 줄 + context-injection.md 참조 — 셀프체크 완료
- [x] **F-10 AC**: `agents.md`의 opgc 서브에이전트 섹션 입력 명세에 `scope` 추가, `--apply`/`--only` 문자열 opgc 섹션 부재, opgc SKILL.md 변경이력 v1.1(2026-04-17, 125) 추가, README.md에 opgc 언급 없음 → "해당 없음 기록" 유지 — 셀프체크 완료
- [x] **F-11 AC**: `conventions-hub-model.md` 신설 문서에 ①허브 문서의 역할(§2) ②링크 규약(§3 — `> 영역별 상세: [FE-CONVENTIONS.md](./FE-CONVENTIONS.md) — Frontend` 예시 포함) ③체커의 참조 체이닝 흐름(§4 — 4단계 절차) ④예시 블록 2종(풀스택/단일 문서, §5) 모두 포함 — 셀프체크 완료

### 일관성 테스트

- [x] opgc SKILL.md 본문과 STATE.md 도메인 치환값 "단계 목록"이 `SCAN / CHECK / REPORT / CLOSE`로 정확히 일치 — 셀프체크 완료
- [x] opgc SKILL.md 병렬 디스패치 프롬프트 템플릿의 입력 파라미터와 두 체커 AGENT.md 입력 명세가 정합 (`scope` 양쪽 존재, `apply_mode` 양쪽 부재) — 셀프체크 완료
- [x] `agents.md` 매핑 테이블의 체커 자체 로드 문서 기술과 AGENT.md Phase 1/2 실제 로드 문서가 일치 (허브+링크 체이닝 표현 동기 — conventions-hub-model.md 참조 명시) — 셀프체크 완료
- [x] `context-injection.md` 프로젝트 구성 기반 라우팅 규약과 `docs/PROJECT.md` "프로젝트 구성" 섹션 스키마(요소/경로/기술 스택/전문 에이전트)가 정합 — 셀프체크 완료
- [x] `opi SKILL.md` 인터뷰 질문의 요소 종류(Frontend/Backend/Batch/Mobile/Framework/기타)와 PROJECT.md 스키마 적용 범위 값(전체/Frontend/Backend/Batch/Mobile/Framework)이 정합 — 셀프체크 완료
- [x] 하위호환 — "프로젝트 구성 섹션 부재 프로젝트"에서 opgc fallback이 1+1 단일 디스패치 유지 문구가 opgc SKILL.md STEP 1.5 + STEP 2.2 Case D에 명시됨 — 셀프체크 완료
- [x] TASK.md §제약 원문([MUST]) 전체가 PLAN.md §1 참조 문서 + §2 핵심 설계에 인용 반영 — PLAN 작성 시 이미 반영(§1·§2 인용 준수)

### 문서 품질

- [x] 한국어 본문 + 영어 코드/필드명 규칙을 따름 (`docs/CONVENTIONS.md` §언어 규칙) — 셀프체크 완료
- [x] kebab-case 파일/폴더 네이밍을 따름 (신규 `conventions-hub-model.md` kebab-case) — 셀프체크 완료
- [x] YAML frontmatter가 올바름 — 체커 AGENT의 `tools` 배열 축소 후 YAML 파싱 유효(`[Read, Grep, Glob, Bash]`) — 셀프체크 완료
- [x] @header 규칙 비대상 — 본 태스크 수정/신규 파일 전부 `.md`. 프로젝트 `.opal/code-scan.json` 부재(확인 완료)로 Step 3-H 비대상. `opal/core/references/harness/header-rules.md` §적용 대상 확장자에도 .md 미포함 — 본 태스크 @header 작성 대상 없음 (→ D-13, 지시 E)
- [x] 변경이력 일시 형식 `YYYY-MM-DD` + 버전 semver — opgc v1.1(2026-04-17, 125), 컨벤션 체커 v1.1, 보안 체커 v1.1, opi v3.4, conventions-hub-model v1.0 모두 적용 — 셀프체크 완료
- [x] 각 산출 문서의 변경이력 행에 태스크 번호 `(125)` 병기 — 셀프체크 완료

---

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| PROJECT.md "프로젝트 문서" 테이블의 기존 `용도` 컬럼과 신규 `적용 범위` 컬럼이 의미상 중복 | PROJECT.md 컬럼 구조 혼란 — AC("컬럼이 4개") 준수 우선 | **PM 확인 필요**: (옵션1) `용도` 삭제 + `적용 범위`로 대체, (옵션2) `용도`→`적용 범위`로 리네이밍 + 내용 재해석. 본 PLAN은 옵션2(리네이밍) 기본 — AC "`문서 / 설명 / 적용 범위 / 참조 시점` 4개" 정확 일치. 옵션1 필요 시 EXECUTE에서 캡틴에게 확인 |
| 기존 opgc 태스크 폴더(`tasks/124-*-opgc-pm-optimization/`)의 보고서가 APPLY 기록을 포함 중 | 레거시 산출물이 신 구조와 불일치 | 레거시 소급 변경 불필요 (citation-rules.md §5 "레거시 호환" 원칙 준용). 신규 실행부터 신 구조 적용 |
| 체커 AGENT에서 `tools`에서 Edit/Write를 제거하면 기존 초안 생성 유도(`opi` 재사용) 흐름 중 에이전트가 직접 파일 작성하는 케이스 발생 여부 | CONVENTIONS.md 초안 자동 생성 불가 가능성 | 초안 생성은 **opi 스킬 재사용** 원칙이므로(현행 행동 규칙), 체커가 직접 파일을 쓰는 로직은 없음 확인. Edit/Write 제거해도 기능 영향 없음. 혹 초안 생성 Phase에서 Edit/Write가 필요하면 EXECUTE에서 재검토 — **PM 확인 필요** |
| `scope`는 optional이지만, 프로젝트 구성이 있는 프로젝트에서도 미지정 호출이 발생할 수 있음 | 요소 매트릭스 확장이 작동하지 않을 수 있음 | scope 미지정 시 opgc SKILL.md가 "섹션 존재 시 요소 전체 × 체커" 매트릭스로 자동 확장하도록 지정. scope 지정 시에만 해당 요소로 좁힘. EXECUTE 시 SCAN 절차에 이 규약을 명시 |
| 허브+링크 모델이 OPAL 자체 CONVENTIONS.md에는 적용되지 않음(단일 문서) | OPAL 자체로 F-11 예시 생성 어려움 | conventions-hub-model.md §5 예시는 풀스택 프로젝트(FE/BE 분리) 가상 예시로 기술. OPAL 자체는 §참고에 "단일 문서 프로젝트" 명시 |
| opi 변경으로 기존 `tasks/0NN-opi-*` 흐름이 영향 받을 가능성 | opi 정규 실행 시 추가 인터뷰 질문 등장 | Q8~Q10은 개발 프로젝트 한정 + 선택 확장. 일반 프로젝트/문서 프로젝트는 기존 7Q 흐름 유지 — 하위호환 확보 |
| `--apply`/`--only` 플래그를 학습한 세션의 사용자/에이전트가 기존 문법 호출 시 | 신 CLI 파서에서 실패 | opgc SKILL.md Arguments 파싱 블록 하단에 "이전 버전 플래그(`--only X`, `--apply`)는 v1.1부터 제거 — 마이그레이션: ..." 안내 문구 추가 (EXECUTE에서 반영) |
| 본 태스크는 단일 태스크 완료 원칙이나(TASK.md §제약 "단일 태스크 완료"), Step이 11개로 많음 | EXECUTE 분량 증가 | Phase 그룹핑(§3 위 표)으로 병렬 디스패치 기회 최대화. Step 11(셀프체크)를 PLAN에 명시하여 EXECUTE 워커가 AC 누락을 방지 |
| 체커 AGENT의 Phase 번호 재배정(6→삭제, 7→6 등) 시 내부 참조 ("PLAN §2.8 기준" 등)가 깨질 수 있음 (`opal/agents/opal-convention-checker/AGENT.md:140`, `opal/agents/opal-security-checker/AGENT.md:135`) | 문서 내 상호참조 무효화 | EXECUTE 시 Phase 내 `(PLAN §N)` 상호참조 문자열 grep → 재참조 또는 제거 |

---

## 변경 요약 (Executive Summary)

- **신규 생성**: 1개 — `opal/core/references/conventions-hub-model.md`
- **수정**: 8개 (선택 1 포함) — opgc SKILL, 컨벤션 체커 AGENT, 보안 체커 AGENT, PROJECT.md, opi SKILL, opal-pm.md, context-injection.md, agents.md, (선택) CONVENTIONS.md
- **삭제**: 0개 (파일 단위)
- **커밋**: 수행하지 않음 (하네스 Guards §1 + TASK.md §제약 준수)
- **@header 대상**: 없음 (모든 산출물 `.md`)
- **요구사항 커버리지**: F-1 ~ F-11 (11개) — 각 Step에 F-ID 태그 부여, QA 체크리스트에서 AC 전원 매핑
- **하위호환**: 프로젝트 구성 섹션 부재 프로젝트에서 opgc 1+1 단일 디스패치 fallback 유지 (TASK.md §제약 원문 준수)
