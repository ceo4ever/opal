# PLAN: opi 스킬에 tasks/ 태스크 기록 추가

> 작성일: 2026-03-30
> 입력: TASK.md
> 출력: PLAN.md

## 1. 현황 조사

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `~/.opal/skills/opal-project-init/SKILL.md` | opi 스킬 정의 (Phase 1~4 프로세스) | **수정** |
| `~/.opal/references/opal-harness.md` | 오케스트레이터 공통 인프라 (STATE.md, TASK 프로세스 등) | 참조만 |
| `/Volumes/Data/AIStudio/workspace/ai-framework/docs/CONVENTIONS.md` | 태스크 산출물 구조, 네이밍 규칙 | 참조만 |
| `~/.opal/skills/opal-project-init/references/docs-guide.md` | docs 문서 구조 가이드 | 참조만 |
| `~/.opal/skills/opal-project-init/references/agent-guide.md` | AGENT.md 구조 가이드 | 참조만 |

### 현재 상태

**opi SKILL.md (v2.0.0)** 의 현재 프로세스:

1. **Phase 1**: 프로젝트 이해 (레이아웃 탐색 → 기술 스택 분석 → 카테고리 판별 → 사용자 인터뷰)
2. **Phase 2**: 공통 문서 작성 + 검토 (`docs/PROJECT.md`, `.opal/AGENT.md`, `.opal/MEMORY.md`, 사용자 요청 문서)
3. **Phase 3**: 개발 문서 (개발 프로젝트만: `ARCHITECTURE.md`, `CONVENTIONS.md`, `BACKEND.md`, `FRONTEND.md`)
4. **Phase 4**: 플랫폼 파일 + 완료 (부트스트래퍼 생성 → MEMORY.md 히스토리 기록 → 완료 보고)

**현재 기록 방식**:
- Phase 4-2에서 `.opal/MEMORY.md` 작업 히스토리에 1줄만 기록
- `tasks/` 폴더에는 아무 산출물도 남기지 않음

**다른 오케스트레이터의 tasks/ 기록 패턴** (CONVENTIONS.md 기준):
```
tasks/{NNN}-{설명}/
├── TASK.md               요구사항 정의
├── ANALYSIS.md           코드베이스 분석 (Full Task)
├── PLAN.md               구현 계획
├── TEST-SCENARIO.md      테스트 시나리오
├── STATE.md              상태 관리
└── DONE.md               완료 보고
```

**opi에 필요한 최소 기록** (TASK.md 요구사항):
```
tasks/{NNN}-opi-{프로젝트명}/
├── TASK.md      ← Phase 1 분석 결과 구조화
└── DONE.md      ← 생성/변경 문서 목록 + 핵심 결정
```

### 영향 범위

| 영향 대상 | 영향 내용 |
|----------|----------|
| opi SKILL.md | Phase 4에 tasks/ 기록 프로세스 추가 |
| 기존 Phase 1~4 흐름 | 변경 없음 (Phase 4 내부에 단계 추가) |
| MEMORY.md 히스토리 | 기존 그대로 유지 (병행) |
| CONVENTIONS.md | 변경 불필요 (이미 태스크 산출물 구조 정의됨) |

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
| 1 | `~/.opal/skills/opal-project-init/SKILL.md` | Phase 4에 tasks/ 태스크 기록 프로세스 추가 (TASK.md + DONE.md 생성) |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| - | 없음 | - |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | opi SKILL.md에 tasks/ 기록 프로세스 추가 | `~/.opal/skills/opal-project-init/SKILL.md` | 중 |

### 핵심 설계

#### SKILL.md 변경 명세

**변경 위치**: Phase 4 섹션 내부, 기존 4-2(메모리 갱신)와 4-3(완료 보고) 사이에 새 단계 삽입.

**Phase 4 구조 변경**:
- 4-1. 플랫폼 파일 생성 (기존 유지)
- 4-2. 프로젝트 메모리 갱신 (기존 유지)
- **4-3. tasks/ 태스크 기록** ← 신규 추가
- 4-4. 완료 보고 + 원래 요청으로 복귀 (기존 4-3 → 번호만 변경)

**4-3. tasks/ 태스크 기록 — 설계 내용**:

1. **태스크 번호 결정**:
   - `tasks/` 폴더를 스캔하여 가장 높은 NNN + 1
   - 폴더명: `tasks/{NNN}-opi-{프로젝트명}/` (kebab-case)

2. **TASK.md 생성** — Phase 1 분석 결과를 구조화:
   ```markdown
   # TASK: opi {초기화|최신화} — {프로젝트명}

   > 작성일: YYYY-MM-DD HH:mm | 작업 유형: 프로젝트 {초기화|최신화}
   > 스킬: opal-project-init (opi)

   ## 프로젝트 정보
   - 프로젝트명: {이름}
   - 카테고리: {개발|일반} 프로젝트 — {서브 카테고리}
   - 단계: {현재 단계}

   ## 기술 스택
   {Phase 1에서 분석된 기술 스택 요약 — 개발 프로젝트만}

   ## 인터뷰 요약
   {Q1~Q7+ 답변 핵심 요약}

   ## 분석 결과
   {레이아웃 탐색 결과, 프로젝트 구조 요약}
   ```

3. **DONE.md 생성** — 완료 시 생성:
   ```markdown
   # DONE: opi {초기화|최신화} — {프로젝트명}

   > 완료일: YYYY-MM-DD HH:mm

   ## 작업 요약
   {초기화/최신화 수행 내용 1~2줄}

   ## 생성/변경 문서
   | 파일 | 작업 | 설명 |
   |------|------|------|
   | docs/PROJECT.md | 생성 | 프로젝트 정의서 |
   | .opal/AGENT.md | 생성 | PM 프로필 |
   | ... | ... | ... |

   ## 핵심 결정 사항
   | 결정 | 근거 |
   |------|------|
   | {예: PM 관점 — 품질+확장성} | {사용자 Q5 답변 기반} |
   | ... | ... |
   ```

4. **최신화 모드 대응**:
   - 최신화 모드에서도 동일하게 tasks/ 기록 생성
   - TASK.md에는 "최신화" 관점의 분석 결과 (변경 감지 항목, 문서 상태)
   - DONE.md에는 업데이트된 문서 목록 + 변경 사항

5. **MEMORY.md 히스토리와의 병행**:
   - 기존 4-2 MEMORY.md 기록은 그대로 유지
   - MEMORY.md 히스토리의 `경로` 컬럼에 tasks/ 경로 추가: `docs/, .opal/, tasks/{NNN}-opi-{name}/`

6. **완료 보고(4-4) 변경**:
   - 기존 완료 보고 형식에 tasks/ 기록 경로 추가

**설계 결정 근거**:

| 결정 | 근거 |
|------|------|
| Phase 4 내부에 삽입 (새 Phase 아님) | Phase 1~4 흐름을 깨지 않는 최소 변경 |
| TASK.md에 Phase 1 결과 구조화 | Phase 1 완료 시점에 필요한 정보가 모두 수집됨 |
| DONE.md는 Phase 4 마지막에 생성 | 모든 문서 생성이 완료된 후에야 목록 확정 가능 |
| STATE.md 미포함 | TASK.md 제약 조건 — opi는 장기 세션 복원 불필요 |
| MEMORY.md 히스토리 유지 | TASK.md 요구사항 — tasks/ 기록과 병행 |
| 4-2와 4-3 사이 배치 | MEMORY.md 갱신 후, 완료 보고 전에 기록 생성이 자연스러움 |
| TASK.md는 Phase 1 직후가 아닌 Phase 4에서 생성 | opi는 인터랙티브(사용자 인터뷰)이므로 Phase 1~3 사이에 중단점을 넣으면 흐름이 깨짐. Phase 4에서 한꺼번에 TASK.md + DONE.md 생성이 적절 |

---

## 3. 실행 체크리스트

> 총 1개 Step (단일 파일 수정)

### Step 1: opi SKILL.md에 tasks/ 태스크 기록 프로세스 추가
- [x] 완료
- **파일**: `~/.opal/skills/opal-project-init/SKILL.md`
- **작업 내용**:
  1. Phase 4 섹션에서 기존 `4-3. 완료 보고`를 `4-4`로 번호 변경
  2. 새 `4-3. tasks/ 태스크 기록` 섹션 추가:
     - 태스크 번호 결정 로직 (tasks/ 스캔 → 최대 NNN + 1)
     - 폴더 생성: `tasks/{NNN}-opi-{프로젝트명}/`
     - TASK.md 생성 명세 (프로젝트 정보, 기술 스택, 인터뷰 요약, 분석 결과)
     - DONE.md 생성 명세 (작업 요약, 생성/변경 문서 목록, 핵심 결정 사항)
  3. 기존 4-2 MEMORY.md 히스토리의 경로 컬럼에 `tasks/` 경로 병기
  4. 4-4 완료 보고 형식에 tasks/ 경로 추가
  5. 최신화 모드 Phase 4에도 동일 tasks/ 기록 프로세스 추가
  6. version 업데이트: `2.0.0` → `2.1.0` (기능 추가)
- **완료 기준**:
  - Phase 4에 `4-3. tasks/ 태스크 기록` 섹션이 존재
  - TASK.md / DONE.md 템플릿이 명세되어 있음
  - 기존 Phase 1~3 프로세스가 변경되지 않음
  - 기존 MEMORY.md 히스토리 기록(4-2)이 유지됨
  - 초기화/최신화 모드 모두 tasks/ 기록을 생성함
  - 기존 4-3(완료 보고)이 4-4로 올바르게 번호 변경됨
- **테스트**: SKILL.md를 통독하여 Phase 1~4 흐름이 일관적인지 확인. 초기화/최신화 모드 모두 tasks/ 기록 경로가 포함되는지 확인.
- **의존**: 없음

---

## 4. QA 체크리스트

### 기능 테스트
- [x] Phase 4에 `4-3. tasks/ 태스크 기록` 섹션이 존재하는가
- [x] TASK.md 템플릿에 프로젝트 정보, 기술 스택, 인터뷰 요약, 분석 결과가 포함되는가
- [x] DONE.md 템플릿에 작업 요약, 생성/변경 문서 목록, 핵심 결정 사항이 포함되는가
- [x] 태스크 번호 결정 로직(tasks/ 스캔 → 최대 NNN + 1)이 명시되어 있는가
- [x] 폴더명이 `tasks/{NNN}-opi-{프로젝트명}/` (kebab-case) 형식인가
- [x] 최신화 모드에서도 tasks/ 기록 생성이 정의되어 있는가
- [x] MEMORY.md 히스토리 기록(4-2)이 기존대로 유지되는가

### 일관성 테스트
- [x] Phase 1~3 프로세스가 변경되지 않았는가
- [x] Phase 4 번호 체계(4-1 ~ 4-4)가 일관적인가
- [x] 초기화 모드와 최신화 모드의 tasks/ 기록 형식이 일관적인가
- [x] 기존 DONE.md 형식(`tasks/054-*` 등)과 호환되는 구조인가
- [x] CONVENTIONS.md의 태스크 산출물 구조와 호환되는가 (TASK.md + DONE.md만 사용)

### 문서 품질
- [x] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가
- [x] kebab-case 파일/폴더 네이밍을 따르는가
- [x] YAML frontmatter version이 올바르게 업데이트되었는가

---

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| Phase 4 번호 변경으로 기존 참조 깨짐 | SKILL.md 내부에서 "Phase 4-3"을 참조하는 곳이 있을 수 있음 | SKILL.md 전체에서 4-3 참조를 검색하여 4-4로 갱신 |
| tasks/ 폴더가 없는 프로젝트 | opi 초기화 대상 프로젝트에 tasks/ 폴더가 없을 수 있음 | TASK.md/DONE.md 생성 시 `tasks/` 디렉토리 자동 생성 명시 |
| 최신화 반복 시 tasks/ 기록 누적 | 같은 프로젝트를 여러 번 최신화하면 기록이 쌓임 | 의도된 동작 — 최신화 이력 추적이 목적. 별도 정리 불필요 |
