# TODO: wireframe-builder 개선 및 ui-designer 스킬 신규 개발

> 작성일: 2026-03-13 | 참조: TASK.md, RESEARCH.md, PLAN.md

## Part A: 실행 체크리스트

> 총 5개 Step | 실행 모드: 복잡

### Step 1: wireframe-builder SKILL.md 재작성

- **파일**: `skills/wireframe-builder/SKILL.md`
- **작업 내용**:
  - 현재 HTML 와이어프레임 생성 스킬을 UI 분석·설계 도구로 전면 재작성
  - YAML frontmatter 변경: description을 "UI 분석·설계 스킬"로 업데이트, 트리거 키워드 변경
  - 4단계 프로세스 정의: 입력 분석 → 화면 도출 → 화면별 상세 설계 → 산출물 생성
  - wireframe.md 산출물 스키마 인라인 포함 (6개 섹션: 서비스 개요, 전체 구조, 화면 목록, 화면별 상세, 공통 컴포넌트, shadcn 설치 목록)
  - 기존 자산 보존: 화면 도출 규칙 테이블, 화면 유형별 ASCII 레이아웃 패턴, 서브 에이전트 위임 패턴
  - 제거: HTML/CSS/JS 코드 생성 로직, showPage 함수, 그레이스케일 원칙, 단일 HTML 출력 규칙
  - 마이그레이션 안내 포함: "HTML 생성은 ui-designer 스킬로 이관됨"
- **완료 기준**: YAML frontmatter 유효, 4단계 프로세스 정의 완료, wireframe.md 스키마 인라인 포함, HTML 생성 로직 완전 제거
- **테스트**: SKILL.md 구조 검증 (frontmatter, 프로세스, 스키마 존재 여부)
- **실행 방법**: direct
- **의존**: 없음
- **상태**: ✅ 완료

### Step 2: ui-designer SKILL.md 신규 작성

- **파일**: `skills/ui-designer/SKILL.md`
- **작업 내용**:
  - ui-designer 스킬 신규 생성 (wireframe.md → React+shadcn UI 구현)
  - YAML frontmatter: name, description, 트리거 키워드 정의
  - 5단계 프로세스 정의: 입력 파싱 → 프로젝트 초기화 → 공통 컴포넌트 생성 → 화면별 구현 → 빌드 및 산출물 생성
  - 2개 출력 모드 정의: 프로토타입(web-artifacts-builder 연계) / 프로덕션(Next.js App Router)
  - wireframe.md 입력 스키마 참조 (Step 1에서 정의한 스키마와 동일)
  - shadcn Critical Rules 인라인 요약 + 참조 경로 명시
  - web-artifacts-builder 연계 방식 (init-artifact.sh, bundle-artifact.sh 호출)
  - 서브 에이전트 위임 규칙 (5화면 이상 시)
- **완료 기준**: YAML frontmatter 유효, 5단계 프로세스 정의, 2개 출력 모드 정의, shadcn 규칙 참조+인라인 존재, web-artifacts-builder 연계 명시
- **테스트**: SKILL.md 구조 검증, wireframe.md 스키마가 Step 1과 일관성 확인
- **실행 방법**: direct
- **의존**: Step 1 (wireframe.md 스키마 확정 필요)

- **상태**: ✅ 완료

### Step 3: 스킬 레지스트리 업데이트

- **파일**: `opal/core/references/skills.md`
- **작업 내용**:
  - 프레임워크 스킬 테이블에서 wireframe-builder 행의 트리거/설명 변경
  - ui-designer 행 신규 추가
- **완료 기준**: wireframe-builder 설명이 "UI 분석·설계 → wireframe.md 생성"으로 변경, ui-designer 행이 추가됨, 트리거 키워드 충돌 없음
- **테스트**: 테이블 형식 검증, 중복 트리거 키워드 없음 확인
- **실행 방법**: direct
- **의존**: Step 1, Step 2 (트리거 키워드 확정 후)
- **상태**: ✅ 완료

### Step 4: CLAUDE.md 소스 구조 업데이트

- **파일**: `CLAUDE.md`
- **작업 내용**:
  - 소스 구조 트리에 `ui-designer/` 행 추가, `wireframe-builder/` 설명 변경
  - 컴포넌트 유형 테이블: Skills 개수 6개 → 7개
- **완료 기준**: 소스 구조에 ui-designer 포함, 스킬 개수 7개 반영, 알파벳 순서 정렬
- **테스트**: CLAUDE.md 내 ui-designer 검색, 스킬 개수 확인
- **실행 방법**: direct
- **의존**: Step 2 (ui-designer 확정 후)
- **상태**: ⬜ 대기

### Step 5: install-mac.sh 스킬 개수 수정

- **파일**: `scripts/install-mac.sh`
- **작업 내용**:
  - 3곳의 `"스킬 (6개)"` → `"스킬 (7개)"` 변경 (install_claude, install_cursor, install_antigravity 함수 내)
- **완료 기준**: 3곳 모두 "7개"로 변경, bash 문법 오류 없음
- **테스트**: `grep "스킬" scripts/install-mac.sh`로 변경 확인, `bash -n scripts/install-mac.sh`로 문법 검사
- **실행 방법**: direct
- **의존**: 없음
- **상태**: ✅ 완료

---

## Part B: QA 체크리스트

### B-1. 기능 테스트

- [ ] wireframe-builder SKILL.md가 4단계 프로세스를 정의하고 있는가
- [ ] wireframe-builder에 wireframe.md 스키마(6개 섹션)가 인라인 포함되어 있는가
- [ ] wireframe-builder에서 HTML 생성 로직이 완전히 제거되었는가
- [ ] ui-designer SKILL.md가 5단계 프로세스를 정의하고 있는가
- [ ] ui-designer에 프로토타입/프로덕션 2개 출력 모드가 정의되어 있는가
- [ ] ui-designer에 shadcn Critical Rules 참조 경로 + 인라인 요약이 있는가
- [ ] ui-designer에 web-artifacts-builder 연계 방식(스크립트 호출)이 명시되어 있는가
- [ ] wireframe.md 스키마가 양쪽 스킬에서 일관성 있는가 (출력 스키마 = 입력 스키마)
- [ ] skills.md에 wireframe-builder 설명이 변경되고 ui-designer가 추가되었는가
- [ ] CLAUDE.md 소스 구조에 ui-designer가 포함되고 스킬 개수가 7개인가
- [ ] install-mac.sh에서 3곳의 스킬 개수가 "7개"로 변경되었는가

### B-2. 회귀 테스트

- [ ] wireframe-builder의 기존 자산(화면 도출 규칙, ASCII 레이아웃 패턴)이 보존되었는가
- [ ] wireframe-builder의 서브 에이전트 위임 패턴이 유지되는가
- [ ] skills.md의 기존 스킬 항목(task-flow, api-analyzer 등)이 변경되지 않았는가
- [ ] CLAUDE.md의 다른 섹션(Architecture, Workflow 등)이 변경되지 않았는가
- [ ] install-mac.sh의 다른 로직(복사 경로, 함수 구조)이 변경되지 않았는가

### B-3. 코드 품질

- [ ] SKILL.md가 YAML frontmatter(name, description) 형식을 준수하는가
- [ ] 문서 본문이 한국어, 코드/변수명이 영어 컨벤션을 따르는가
- [ ] 파일/폴더명이 kebab-case를 따르는가 (ui-designer)
- [ ] version-mgr 참조가 적절히 포함되어 있는가

### B-4. 보안

- [ ] 민감 정보(토큰, 시크릿)가 포함되지 않았는가
- [ ] install-mac.sh에 보안 관련 변경이 없는가

---

## 복잡도 판별

| 기준 | 값 | 판정 |
|------|-----|------|
| Step 수 | 5개 | 단순 (≤5) |
| 변경 파일 수 | 5개 | **복잡** (≥4) |
| 모듈 범위 | skills + opal/references + CLAUDE.md + scripts | **복잡** (다중) |
| 작업 유형 | 신규 개발 + 기능 개선 | **복잡** |
| 외부 의존성 | 없음 | 단순 |

**판정: 복잡 모드** (3개 기준 해당)

> 단, 모든 변경 대상이 마크다운 문서(.md)와 쉘 스크립트 메시지 수정이므로, 서브 에이전트 병렬 실행보다는 메인 에이전트 순차 실행이 효율적입니다. Part C에서 실행 아키텍처를 결정합니다.

---

## Part C: 실행 아키텍처

> 에이전트 5개 | 병렬 그룹 1개 | 예상 배치 3개

### C-1. 에이전트 토폴로지

#### 의존성 분석 (DAG)

```
Step 1 (wireframe-builder) ──┐
                              ├──→ Step 3 (skills.md) ──→ Step 4 (CLAUDE.md)
Step 2 (ui-designer)     ──┘
Step 5 (install-mac.sh)  ← 독립
```

- Step 1, Step 2: wireframe.md 스키마가 PLAN.md/RESEARCH.md에 확정되어 있으므로 병렬 실행 가능
- Step 3, Step 4: Step 1+2의 YAML frontmatter(트리거 키워드) 확정 후 실행
- Step 5: 다른 Step과 의존성 없음

#### 그룹핑 근거

| 기준 | 분석 | 결론 |
|------|------|------|
| 동일 파일 수정 | 5개 Step이 각각 다른 파일 수정 | 파일 충돌 없음 |
| 동일 모듈/레이어 | Step 1+2: skills/ 디렉토리 (핵심 스킬 작성) | 각각 다른 파일이므로 병렬 분리 |
| 독립적 모듈 | Step 3+4+5: 레지스트리/문서 메타데이터 업데이트 | 별도 에이전트 가능 |
| 작업 복잡도 | Step 1+2: 높음 (전체 재작성/신규) / Step 3+4+5: 낮음 (행 수정) | 핵심 작업과 메타데이터 분리 |

Step 1과 Step 2는 각각 다른 파일을 수정하며, wireframe.md 스키마가 PLAN.md/RESEARCH.md에 이미 확정되어 있으므로 병렬 실행이 가능하다. 따라서 **2(병렬)+1+1+1 구조**(wireframe-builder 에이전트 ∥ ui-designer 에이전트 → 메타데이터 에이전트 → QA 에이전트 → 테스트 에이전트)로 분할한다.

#### Agent-1A: wireframe-builder 재작성
- **담당 Step**: Step 1
- **실행 방법**: sub-agent
- **필요 컨텍스트**:
  - PLAN.md 3.1절 (wireframe-builder 설계)
  - RESEARCH.md 3절 (wireframe.md 스키마 설계)
  - `skills/wireframe-builder/SKILL.md` — 현재 파일 전체 (보존할 자산 식별)
- **필요 스킬**: 없음 (직접 구현)
- **필요 도구**: 없음

#### Agent-1B: ui-designer 신규 작성
- **담당 Step**: Step 2
- **실행 방법**: sub-agent
- **필요 컨텍스트**:
  - PLAN.md 3.2절 (ui-designer 설계)
  - RESEARCH.md 2절 (shadcn Critical Rules) + 3절 (wireframe.md 스키마 설계)
  - `/Users/iskang/.opal/community-skills/vercel-labs/shadcn/SKILL.md` — shadcn Critical Rules 참조
  - `/Users/iskang/.opal/community-skills/anthropics/web-artifacts-builder/SKILL.md` — 번들링 파이프라인 참조
- **필요 스킬**: 없음 (직접 구현)
- **필요 도구**: 없음

#### Agent-2: 레지스트리 및 문서 업데이트
- **담당 Step**: Step 3, Step 4, Step 5
- **실행 방법**: sub-agent
- **필요 컨텍스트**:
  - Agent-1A 산출물: `skills/wireframe-builder/SKILL.md`의 YAML frontmatter (트리거 키워드)
  - Agent-1B 산출물: `skills/ui-designer/SKILL.md`의 YAML frontmatter (트리거 키워드)
  - `opal/core/references/skills.md` — 현재 레지스트리
  - `CLAUDE.md` — 현재 소스 구조 섹션
  - `scripts/install-mac.sh` — 스킬 개수 표기 위치
- **필요 스킬**: 없음 (직접 구현)
- **필요 도구**: bash (install-mac.sh 문법 검사: `bash -n`)

#### Agent-3: QA 검증
- **담당 Step**: Part B QA 체크리스트 검증
- **실행 방법**: task-flow-qa 에이전트 호출 (QA-EXECUTE.md 생성)
- **필요 컨텍스트**:
  - TODO.md Part A + Part B 전체
  - TASK.md (요구사항/성공 기준 대조)
  - Agent-1A, Agent-1B, Agent-2의 모든 산출물 (변경된 5개 파일)
- **필요 스킬**: 없음
- **필요 도구**: 없음

#### Agent-4: 테스트 검증
- **담당 Step**: C-4 테스트 전략 실행
- **실행 방법**: task-flow-test 에이전트 호출 (TEST-REPORT.md 생성)
- **필요 컨텍스트**:
  - TODO.md Part B + Part C-4 전체
  - Agent-3의 QA-EXECUTE.md (QA 지적 사항 반영 확인)
  - Agent-1A, Agent-1B, Agent-2의 모든 산출물 (변경된 5개 파일)
- **필요 스킬**: 없음
- **필요 도구**: bash (grep, bash -n)

#### 실행 순서

```
[Agent-1A: wireframe-builder] ──┐
                                 ├→ [Agent-2: 레지스트리/문서] → [Agent-3: QA] → [Agent-4: Test]
[Agent-1B: ui-designer]     ──┘
```

**배치 구성:**
- Batch 1: Agent-1A + Agent-1B (병렬 실행)
- Batch 2: Agent-2 (Step 3, Step 4, Step 5, 순차)
- Batch 3: Agent-3 (QA 검증) → Agent-4 (테스트 검증) 순차

### C-2. 스킬 요구사항

| 스킬 | 상태 | 용도 | 비고 |
|------|------|------|------|
| doc-writer | 참조 불필요 | - | 스킬 문서는 SKILL.md 자체 형식을 따름 |
| version-mgr | 참조만 | wireframe.md 산출물 버전 관리 안내 | Step 1, 2에서 참조 경로 명시 |
| interview | 참조만 | wireframe-builder 입력 부족 시 호출 안내 | Step 1에서 참조 경로 명시 |

신규 스킬 생성 필요 없음. 모든 작업이 기존 SKILL.md 작성 패턴(YAML frontmatter + 단계별 프로세스 + 산출물 템플릿)을 따르며, 이 패턴은 이미 프레임워크에 확립되어 있다.

### C-3. 도구 요구사항

| 도구 | 유형 | 상태 | 용도 |
|------|------|------|------|
| bash | CLI | 설치됨 | install-mac.sh 문법 검사 (`bash -n`) |
| grep | CLI | 설치됨 | 변경 확인 (스킬 개수, 키워드 검색) |
| Node.js 22 | CLI | 설치됨 | 직접 사용 안 함 (ui-designer 런타임 의존성 확인용) |
| pnpm | CLI | 설치됨 | 직접 사용 안 함 (ui-designer 런타임 의존성 확인용) |

추가 도구 설치 불필요. 이번 태스크는 마크다운 문서와 쉘 스크립트 메시지만 수정하므로 빌드 도구, MCP 서버, 외부 패키지가 필요하지 않다.

### C-4. 테스트 전략

- **QA 에이전트**: task-flow-qa → Agent-3에서 QA-EXECUTE.md 생성
- **테스트 에이전트**: task-flow-test → Agent-4에서 TEST-REPORT.md 생성
- **실행 시점**: Agent-2 완료 후, QA → Test 순차 실행

| 구분 | 도구 | 대상 | 실행 방법 |
|------|------|------|----------|
| B-1 기능 | grep + 수동 검증 | 변경된 5개 파일 | 각 파일에서 키워드/섹션 존재 여부 검색 |
| B-2 회귀 | grep + diff | wireframe-builder 기존 자산, skills.md/CLAUDE.md/install-mac.sh 비변경 영역 | 기존 자산 키워드 검색 + 비변경 영역 무결성 확인 |
| B-3 품질 | grep | SKILL.md YAML frontmatter, 네이밍 컨벤션 | frontmatter 파싱, kebab-case 확인 |
| B-4 보안 | grep | 전체 변경 파일 | 시크릿 패턴 스캔 (token, secret, password, api_key) |

#### 기능 테스트 상세 (B-1)

| 항목 | 검증 명령 |
|------|----------|
| wireframe-builder 4단계 프로세스 | `grep -c "Phase [1-4]" skills/wireframe-builder/SKILL.md` (결과: 4) |
| wireframe.md 스키마 6개 섹션 | `grep -c "^### [1-6]\." skills/wireframe-builder/SKILL.md` (결과: 6) |
| HTML 생성 로직 제거 | `grep -ci "showPage\|<html\|<script\|그레이스케일" skills/wireframe-builder/SKILL.md` (결과: 0) |
| ui-designer 5단계 프로세스 | `grep -c "Phase [1-5]" skills/ui-designer/SKILL.md` (결과: 5) |
| 2개 출력 모드 | `grep -c "프로토타입\|프로덕션" skills/ui-designer/SKILL.md` (결과: 2 이상) |
| shadcn 규칙 참조 | `grep -c "Critical Rules\|shadcn" skills/ui-designer/SKILL.md` (결과: 2 이상) |
| web-artifacts-builder 연계 | `grep -c "init-artifact\|bundle-artifact" skills/ui-designer/SKILL.md` (결과: 2 이상) |
| wireframe.md 스키마 일관성 | 양쪽 SKILL.md에서 섹션 6개 헤딩이 동일한지 수동 비교 |
| skills.md 업데이트 | `grep "ui-designer" opal/core/references/skills.md` (결과: 1줄 이상) |
| CLAUDE.md 업데이트 | `grep "ui-designer" CLAUDE.md` + `grep "7개" CLAUDE.md` |
| install-mac.sh 업데이트 | `grep -c "7개" scripts/install-mac.sh` (결과: 3) |

#### 회귀 테스트 상세 (B-2)

| 항목 | 검증 명령 |
|------|----------|
| 화면 도출 규칙 보존 | `grep -c "화면 도출" skills/wireframe-builder/SKILL.md` (결과: 1 이상) |
| ASCII 레이아웃 보존 | `grep -c "┌\|┘\|│" skills/wireframe-builder/SKILL.md` (결과: 1 이상) |
| 서브 에이전트 위임 보존 | `grep -c "서브.*에이전트\|sub.*agent" skills/wireframe-builder/SKILL.md` (결과: 1 이상) |
| install-mac.sh 문법 | `bash -n scripts/install-mac.sh` (종료 코드: 0) |

---

## 승인 요청

> 위 TODO(Part A + B + C)가 사용자의 승인을 받으면 EXECUTE 단계를 시작합니다.
> 복잡 모드: Part C 토폴로지에 따라 5개 에이전트를 3개 배치로 실행합니다.
> Batch 1: Agent-1A ∥ Agent-1B (병렬) → Batch 2: Agent-2 → Batch 3: Agent-3(QA) → Agent-4(Test)
