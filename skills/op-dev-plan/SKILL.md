---
name: op-dev-plan
description: |
  **구현 계획 수립 단계 스킬**. TASK.md와 ANALYSIS.md(선택)를 기반으로 실행 가능한 구현 청사진을 작성한다. ANALYSIS.md 유무에 따라 분석 깊이가 자동 조절된다.
  반드시 이 스킬을 사용해야 하는 상황: 오케스트레이터(opal-pilot-dev, opal-pilot-dev-short)가 PLAN 단계를 디스패치할 때.
  필수 입력: TASK.md. 선택 입력: ANALYSIS.md. 보장 출력: PLAN.md (실행 체크리스트+복잡도 판별 포함), execution-plan.json (FE/BE 시).
---

# 구현 계획 수립 (PLAN)

## 실행 컨텍스트

이 스킬은 워커 에이전트의 컨텍스트에서 실행된다.
오케스트레이터가 워커를 디스패치하면, 워커가 이 스킬을 읽고 프로세스를 따른다.
서브 에이전트 사용이 불가능한 플랫폼에서는 오케스트레이터가 직접 이 스킬을 따른다.

---

## 페르소나

`personas/software-architect.md`를 Read하여 설계 원칙과 행동 규칙을 적용한다.

---

## 입력/출력

| 항목 | 설명 |
|------|------|
| **필수 입력** | TASK.md |
| **선택 입력** | ANALYSIS.md |
| **보장 출력** | PLAN.md |
| **조건부 출력** | execution-plan.json (FE/BE 작업 포함 시) |

---

## 입력 분기

ANALYSIS.md 존재 여부에 따라 프로세스가 분기된다:

| 조건 | "1. 코드 분석" 섹션 | 설계 집중도 |
|------|---------------------|-----------|
| ANALYSIS.md **있음** | ANALYSIS.md 참조하여 간략 작성 | 설계/구현 계획에 집중 |
| ANALYSIS.md **없음** | 직접 수행 (Full ANALYSIS 수준) | 코드 분석 + 설계를 통합 수행 |

---

## 프로세스

### Step 1: 가이드 로딩

`references/plan-guide.md`를 Read한다.

### Step 2: 기술 컨텍스트 로딩

plan-guide.md의 0단계를 따른다. 기술 스택에 따라 아래 스킬/MCP를 활용한다.

#### 활용 스킬 (기술 스택에 따라 선택적 Read)

| 기술 스택 | 스킬 | 탐색 경로 |
|----------|------|----------|
| React | `vercel-labs/react-best-practices` | `~/.opal/community-skills/vercel-labs/` |
| React | `vercel-labs/composition-patterns` | `~/.opal/community-skills/vercel-labs/` |
| Next.js | `vercel-labs/next-best-practices` | `~/.opal/community-skills/vercel-labs/` |
| shadcn/ui | `vercel-labs/shadcn` | `~/.opal/community-skills/vercel-labs/` |
| Python | `trailofbits/modern-python` | `~/.opal/community-skills/trailofbits/` |
| FE 설계 | `anthropics/frontend-design` | `~/.opal/community-skills/anthropics/` |
| FE 화면 | `ui-designer/SKILL.md` | `{프로젝트}/.opal/skills/` → `~/.opal/skills/` |

#### 활용 MCP (필요 시)

| MCP | 용도 |
|-----|------|
| context7 | 최신 라이브러리 API 문서 참조 |
| shadcn MCP | shadcn/ui 컴포넌트 조회 및 사용법 확인 |

### Step 3: 코드 분석 (입력 분기)

**ANALYSIS.md 있음**: ANALYSIS.md의 분석 결과를 참조하여 "1. 코드 분석" 섹션을 간략 작성한다.

**ANALYSIS.md 없음**: 직접 코드 분석을 수행한다 (Full ANALYSIS 수준):
- Glob/Grep/Read로 관련 코드를 실제로 읽는다 (추측 금지)
- 기존 코드 구조, 핵심 로직 흐름 파악
- 관련 함수/클래스 시그니처와 역할
- 외부 라이브러리/API 호출 방식
- 영향 범위 (호출자/피호출자 의존 관계)
- 공유 데이터 구조/상태 영향
- 관련 테스트 파일

### Step 4: 구현 계획 수립

plan-guide.md의 1~5단계를 따라 구현 계획을 수립한다:
1. **구현 범위 확정** — 신규/수정/영향 확인 파일 테이블
2. **구현 순서 결정** — 의존성 기반, FE+BE 시 영역 태그 부여
3. **핵심 설계 명세** — 클래스/함수 시그니처, 데이터 모델, FE 화면 설계
4. **의존성 및 환경 변경** — 추가 패키지, 환경 설정
5. **테스트 전략** — 테스트 종류, 성공 기준

### Step 5: 복잡도 판별

plan-guide.md의 "복잡도 판별" 섹션을 따라 실행 모드를 결정한다.

### Step 6: 실행 아키텍처 설계 (복잡 모드 전용)

복잡 모드로 판정된 경우, plan-guide.md의 "실행 아키텍처 (복잡 모드 전용)" 섹션을 따라 C-1~C-4를 작성한다.
단순 모드이면 이 Step을 스킵한다.

### Step 7: execution-plan.json 생성 (FE/BE 작업 시)

plan-guide.md의 6단계를 따른다.

**생성 조건**:
- FE 또는 BE 작업이 포함되면 생성
- 문서 전용 작업이면 생성하지 않음
- Short Task에서도 FE/BE 작업이면 생성

**저장 경로**: `tasks/{NNN}-{태스크명}/execution-plan.json`

### Step 8: PLAN.md 작성

아래 통일 형식으로 PLAN.md를 작성한다.

### Step 9: 결과 반환

워커는 PLAN.md 경로와 요약을 오케스트레이터에 반환한다.
워커는 QA를 호출하지 않는다. 오케스트레이터가 QA 에이전트를 별도로 호출한다.

---

## PLAN.md 출력 형식

Full Task와 Short Task 모두 동일한 형식을 사용한다.
ANALYSIS.md 유무에 따라 "1. 코드 분석" 섹션의 깊이만 달라진다.

```markdown
# PLAN: {제목}

> 작성일: YYYY-MM-DD
> 입력: TASK.md, ANALYSIS.md (선택)
> 출력: PLAN.md, execution-plan.json (FE/BE 시)

## 1. 코드 분석
### 관련 파일
| 파일 | 역할 | 변경 필요 |
|------|------|----------|
### 현재 구현
{핵심 로직 흐름, 함수/클래스 시그니처, 외부 의존성}
### 영향 범위
{호출자/피호출자 의존 관계, 공유 상태, 관련 테스트}

## 2. 구현 계획
### 파일 변경 계획
#### 신규 생성
| # | 파일 경로 | 역할 |
|---|----------|------|
#### 수정
| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
### 구현 순서
| 순서 | 영역 | 작업 | 파일 | 예상 난이도 |
|------|------|------|------|-----------|
### 핵심 설계
{클래스/함수 시그니처, 데이터 모델, FE 화면 설계}
### 의존성 및 환경 변경
{추가 패키지, 환경 설정}
### 테스트 전략
{테스트 종류, 성공 기준}

## 3. 실행 체크리스트

> 총 {N}개 Step | 실행 모드: {단순 / 복잡}

### Step 1: {작업 제목}
- [ ] 완료
- **파일**: {대상 파일 경로}
- **작업 내용**: {구체적 구현 내용}
- **완료 기준**: {검증 가능한 완료 조건}
- **테스트**: {검증 명령어 또는 방법}
- **실행 방법**: {direct / sub-agent}
- **의존**: {선행 Step 번호 또는 "없음"}

## 4. QA 체크리스트
### 기능 테스트
- [ ] {항목}
### 회귀 테스트
- [ ] {항목}
### 코드 품질
- [ ] {항목}
### 보안
- [ ] {항목}

## 5. 복잡도 판별
| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | {N}개 | {단순/복잡} |
| 변경 파일 수 | {N}개 | {단순/복잡} |
| 모듈 범위 | {단일/다중} | {단순/복잡} |
| 작업 유형 | {유형} | {단순/복잡} |
| 외부 의존성 | {유무} | {단순/복잡} |
| **실행 모드** | **{단순 / 복잡}** | |

## 6. 실행 아키텍처 (복잡 모드 시)
### C-1. 에이전트 토폴로지
{DAG, 그룹핑, 배치 실행 순서}
### C-2. 스킬 요구사항
{기존 스킬 매칭, 갭 판별}
### C-3. 도구 요구사항
{CLI, MCP, 패키지}
### C-4. 테스트 전략
{op-dev-test-agent 실행 계획}

## 7. 기술 컨텍스트
### 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
### 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|

## 8. 리스크 및 대응
| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|

## 참조: execution-plan.json (FE/BE 작업 시)
{tasks/{NNN}-{태스크명}/execution-plan.json 경로}
```

---

## 영역 태그 규칙 (FE + BE 작업 시)

FE + BE 모두 포함하는 작업에서는 각 구현 항목에 영역 태그를 부여한다:

- `[FE]` -- 프론트엔드 전용 (컴포넌트, 페이지, 스타일링)
- `[BE]` -- 백엔드 전용 (모델, 서비스, 라우터, DTO)
- `[공통]` -- FE/BE 공유 (타입 정의, 설정, 공유 DTO)

영역 태그는 EXECUTE에서 FE/BE 병렬 디스패치의 기반이 된다.

---

## execution-plan.json 스키마

```json
{
  "task_id": "NNN-태스크명",
  "common": {
    "items": [
      {
        "id": "C-1",
        "description": "작업 설명",
        "files": ["파일 경로"],
        "depends_on": []
      }
    ]
  },
  "frontend": {
    "screens": [
      {
        "id": "FE-1",
        "name": "화면명",
        "type": "crud | dashboard | form | auth | detail | settings | report | monitor",
        "action": "new | modify",
        "route": "/경로",
        "files": ["파일 경로"],
        "shadcn_components": ["컴포넌트명"],
        "depends_on": ["C-1"],
        "ui_work": {
          "description": "UI 작업 설명",
          "components_to_create": ["컴포넌트명"],
          "components_to_modify": ["컴포넌트명"]
        },
        "api_work": {
          "endpoints": ["GET /api/...", "POST /api/..."],
          "description": "API 연동 설명"
        }
      }
    ]
  },
  "backend": {
    "layers": [
      {
        "id": "BE-1",
        "layer": "model | dto | service | router",
        "description": "작업 설명",
        "files": ["파일 경로"],
        "depends_on": []
      }
    ]
  },
  "execution_order": {
    "strategy": "common-first-then-parallel",
    "sequence": [
      { "phase": 1, "items": ["C-*"], "note": "공통 먼저" },
      { "phase": 2, "parallel": ["frontend", "backend"], "note": "FE/BE 병렬" }
    ]
  }
}
```

**BE layers 순서**: model -> dto -> service -> router (하위 레이어부터)
**FE screens**: 화면별 독립 단위. 각 screen은 ui-designer plan-driven 모드의 입력으로 사용.
**common**: FE/BE 공유 타입, 설정 등. 반드시 먼저 실행.
**frontend/backend가 비어있으면**: 해당 키를 생략하거나 빈 배열로 둔다.

---

## 품질 체크리스트

- [ ] 이 PLAN만 보고 바로 코딩에 들어갈 수 있는가?
- [ ] 구현 순서의 의존성이 올바른가? (하위 레이어 먼저)
- [ ] ANALYSIS(있는 경우)에서 발견한 제약/리스크가 반영되었는가?
- [ ] 테스트 전략이 TASK.md의 요구사항을 모두 커버하는가?
- [ ] 프로젝트 코드 컨벤션을 따르는가?
- [ ] 추천 스킬(기술 컨텍스트)을 Read하고 설계에 반영했는가?
- [ ] 관련 코드를 실제로 읽고 분석했는가? (추측 금지)
- [ ] FE+BE 작업 시 영역 태그를 부여했는가?
- [ ] FE/BE 작업 시 execution-plan.json을 생성했는가?
- [ ] 실행 체크리스트가 TASK.md 요구사항을 모두 커버하는가?
- [ ] QA 항목이 기능/회귀/품질을 포함하는가?
- [ ] 각 Step의 완료 기준이 명확하고 검증 가능한가?
- [ ] 각 Step의 실행 방법(direct/sub-agent)이 지정되었는가?
- [ ] QA 체크리스트에 보안 항목이 포함되어 있는가?
- [ ] 복잡도 판별이 수행되었는가?
- [ ] 복잡 모드일 경우 실행 아키텍처(C-1~C-4)가 포함되어 있는가?
