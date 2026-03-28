---
name: dtp-execute
description: |
  **코드 실행 단계 스킬**. 오케스트레이터가 지정한 체크리스트를 따라 실제 코드를 작성하고 검증한다. FE/BE 작업 시 해당 페르소나를 적용한다.
  반드시 이 스킬을 사용해야 하는 상황: 오케스트레이터(dtp-dev, dtp-dev-short, dtp-dev-wf)가 EXECUTE 단계를 디스패치할 때.
  필수 입력: checklist_source (경로 + 섹션, 오케스트레이터 지정). 선택 입력: execution-plan.json. 보장 출력: 코드 변경 + changed_files.
---

# dtp-execute — 코드 실행

## 실행 컨텍스트

- **호출자**: 오케스트레이터(dtp-dev, dtp-dev-short, dtp-dev-wf)가 EXECUTE 단계를 디스패치
- **실행 주체**: 워커 에이전트 (dtp-dev-agent 또는 dtp-wireframe-ui-agent)
- **입력**: `checklist_source` (오케스트레이터가 경로+섹션 지정)
  - Full Task: `TODO.md` Part A (또는 `execution-plan.json`)
  - Short Task: `PLAN.md` 섹션 3 실행 체크리스트
  - Wireframe UI: wireframe.md 기반 실행 항목
- **출력**: 코드 변경 + `changed_files` 목록

## 페르소나

작업 유형에 따라 페르소나를 선택한다:

- **FE 작업**:
  ```
  Read ~/.opal/skills/dtp-execute/personas/frontend-engineer.md
  ```
- **BE 작업**:
  ```
  Read ~/.opal/skills/dtp-execute/personas/backend-engineer.md
  ```

페르소나 파일이 없으면 다음 역할을 따른다:
- FE: 시니어 프론트엔드 엔지니어 (React, shadcn/ui, 접근성 중시)
- BE: 시니어 백엔드 엔지니어 (API 설계, 데이터 모델링, 보안 중시)

## 프로세스

### Step 1. 실행 가이드 로딩

```
Read ~/.opal/skills/dtp-execute/references/execute-guide.md
```

가이드의 금지 행동, 보안 가드레일, 실행 모드별 동작을 숙지한다.

### Step 2. 체크리스트 확인

오케스트레이터가 지정한 `checklist_source`에서 실행 항목을 파악한다.

**입력 우선순위**:
1. `execution-plan.json` (있으면) -- FE/BE 구조화된 실행 순서
2. `TODO.md` Part A (Full Task, JSON 없을 때) -- Step별 체크리스트
3. `PLAN.md` 섹션 3 (Short Task, JSON 없을 때) -- 실행 체크리스트

### Step 3. 코드 작성 및 검증

실행 모드(단순/복잡/Short)에 따라 execute-guide.md의 절차를 따른다.

### Step 4. 체크리스트 갱신

각 Step 완료 시 체크박스를 실시간 갱신한다:
- Full Task: `TODO.md` Part A의 `- [ ]` → `- [x]`
- Short Task: `PLAN.md` 섹션 3의 `- [ ]` → `- [x]`

### Step 5. QA 체크리스트 검증

모든 실행 Step 완료 후, dtp-test 호출 전에 워커가 QA 체크리스트를 자체 검증한다:
- Full Task → `TODO.md` Part B
- Short Task → `PLAN.md` 섹션 4

## 가드레일

### 절대 금지

| # | 금지 행동 | 이유 |
|---|----------|------|
| 1 | PLAN/TODO/execution-plan.json에 없는 파일 생성/수정 | 계획 밖 변경은 추적 불가 |
| 2 | 설계(클래스 구조, 함수 시그니처, DB 스키마)를 임의로 변경 | PLAN에서 QA를 통과한 설계를 무효화 |
| 3 | 다른 영역 침범 (FE 워커가 BE 파일 수정, 또는 그 반대) | 병렬 실행 시 충돌 발생 |
| 4 | PLAN에 명시되지 않은 패키지 설치 | 의존성 변경은 사전 승인 필요 |
| 5 | 환경변수/시크릿을 소스 코드에 하드코딩 | 보안 위반 |

### 보안 가드레일

| # | 패턴 | 감지 방법 | 조치 |
|---|------|----------|------|
| 1 | 하드코딩 시크릿 | `password=`, `secret=`, `api_key=` 리터럴 값 | 환경변수로 교체 제안 |
| 2 | SQL Injection 취약점 | f-string/문자열 연결로 SQL 구성 | 파라미터 바인딩으로 교체 제안 |
| 3 | 민감 파일 커밋 위험 | `.env`, `credentials.*` 파일 생성 시 `.gitignore` 미포함 | `.gitignore` 추가 제안 |
| 4 | 무제한 입력 | 사용자 입력을 검증 없이 DB/파일시스템에 전달 | 입력 검증 추가 제안 |

## 실행 모드

### 단순 모드 (Simple)

워커가 Step 순서대로 직접 실행한다.

```
Step 1 → Step 2 → ... → Step N → QA 체크리스트 → 결과 반환
```

### 복잡 모드 (Complex)

워커 내부에서 Part C 토폴로지에 따라 서브 에이전트를 배치하여 병렬 실행한다.

```
Batch 1: [Agent-1, Agent-2 병렬] → Batch 2: [Agent-3] → ... → QA 체크리스트 → 결과 반환
```

### Short Task 모드

PLAN.md 섹션 3 기반으로 순차 실행한다.

```
Step 1 → Step 2 → ... → Step N → QA 체크리스트 → 결과 반환
```

## FE 역할 분담: ui-designer vs dtp-execute

FE 태스크에서 **UI 구현**과 **비UI 작업**의 담당을 명확히 구분한다.

### ui-designer 담당 (UI 구현)

화면에 보이는 것을 만드는 작업. shadcn/ui + React 컴포넌트 전문.

| 작업 | 예시 |
|------|------|
| 페이지 레이아웃 | 전체 화면 구조, 헤더/사이드바/콘텐츠 배치 |
| UI 컴포넌트 구현 | 버튼, 폼, 테이블, 카드, 다이얼로그 등 |
| shadcn 컴포넌트 조합 | shadcn MCP 조회 → 설치 → 조합 |
| 스타일링 | Tailwind CSS, 반응형 레이아웃 |
| 인터랙션 UI | 탭, 아코디언, 드롭다운, 모달 등 |
| 폼 UI | 입력 필드, 유효성 표시, 에러 메시지 표시 |

**호출 방법**: execution-plan.json의 FE screen 항목을 ui-designer plan-driven 모드로 전달.

### dtp-execute 담당 (비UI FE 작업)

화면 뒤에서 동작하는 것을 만드는 작업.

| 작업 | 예시 |
|------|------|
| API 연동 | fetch/axios, API 클라이언트, 에러 처리 |
| 상태 관리 | zustand, context, React Query 설정 |
| 라우팅 설정 | Next.js app router, 페이지 구조 |
| 타입 정의 | TypeScript 인터페이스, OpenAPI 타입 생성 |
| 유틸리티 | 헬퍼 함수, 포맷터, 밸리데이터 |
| 환경 설정 | .env, 빌드 설정, 패키지 설치 |
| 인증/인가 로직 | 토큰 관리, 가드, 미들웨어 |

### 실행 순서 (FE 태스크)

```
dtp-execute:
  1. 비UI 작업 먼저 (라우팅, 타입, API 클라이언트, 상태 관리)
  2. ui-designer 호출 (화면 UI 구현)
  3. UI + 비UI 통합 (API 연결, 이벤트 핸들러 바인딩)
```

## 활용 스킬/MCP (FE)

| 스킬/MCP | 담당 | 용도 |
|----------|------|------|
| **ui-designer** (plan-driven) | UI 구현 | 화면 레이아웃 + shadcn 컴포넌트 구현 |
| shadcn MCP | UI 구현 | 컴포넌트 검색·조회·설치 (ui-designer가 사용) |
| vercel-labs/shadcn | UI 구현 | shadcn Critical Rules, 폼/레이아웃 패턴 |
| vercel-labs/react-best-practices | 비UI | React 패턴 (상태 관리, 훅 등) |
| vercel-labs/next-best-practices | 비UI | Next.js 패턴 (라우팅, RSC 등) |
| vercel-labs/composition-patterns | 공통 | 컴포넌트 조합 패턴 |
| anthropics/frontend-design | 공통 | FE 아키텍처/UX 설계 참조 |
| context7 | 비UI | 라이브러리 문서 조회 |

## 활용 MCP (BE)

| MCP | 용도 | 사용 시점 |
|-----|------|----------|
| context7 | 라이브러리 문서 조회 (Python, Flutter, Kotlin, Go 등) | 외부 라이브러리 API 확인 시 |

## execution-plan.json 기반 실행

execution-plan.json이 존재하면:
1. `execution_order.sequence`에 따라 phase별 실행
2. phase 1 (common) 완료 후 phase 2 (FE/BE 병렬) 시작
3. 각 항목의 `depends_on`을 확인하여 선행 작업 완료 여부 검증
4. **FE 항목 실행 순서**:
   a. 비UI 작업 먼저 (dtp-execute): 라우팅, 타입 정의, API 클라이언트, 상태 관리
   b. UI 구현 (ui-designer): screen 항목을 ui-designer plan-driven 모드로 전달
   c. 통합 (dtp-execute): API 연결, 이벤트 핸들러 바인딩, 최종 조립
5. BE layer 항목: model → dto → service → router 순서로 순차 실행

## 블로커 처리

블로커가 발생하면:

1. **즉시 중단** -- 추측으로 해결하지 않는다
2. **사용자 보고**:
   - Step 번호와 제목
   - 구체적 에러/상황
   - 가능한 원인
   - 해결 방안 제안
3. **사용자 지시 대기** -- 지시에 따라 재개 또는 건너뛰기

## 결과 반환

워커는 dtp-test를 직접 호출하지 않는다. 실행이 완료되면 결과를 오케스트레이터에 반환한다.

**반환 형식**:
```json
{
  "artifact_path": "tasks/{NNN}-{태스크명}/",
  "summary": "{실행 요약}",
  "status": "complete | blocked",
  "blockers": [],
  "changed_files": ["파일1", "파일2"]
}
```

## EXECUTE 품질 체크리스트

- [ ] 모든 Step 체크박스가 [x] 또는 사용자 승인으로 건너뛰어졌는가
- [ ] 각 Step의 테스트 기준이 통과되었는가
- [ ] 블로커 발생 시 사용자에게 보고되었는가
- [ ] 변경 파일 목록이 PLAN.md의 파일 목록과 일치하는가
- [ ] 코드가 프로젝트 컨벤션을 따르는가
- [ ] QA 체크리스트 체크박스가 갱신되었는가
- [ ] PLAN/execution-plan.json에 없는 파일을 생성/수정하지 않았는가
- [ ] 하드코딩 시크릿이 없는가
- [ ] FE/BE 영역 간 침범이 없는가 (병렬 실행 시)
