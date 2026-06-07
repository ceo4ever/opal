# Wireframe UI QA 가이드 (WIREFRAME / EXECUTE-UI 검증 기준)

> **실행 컨텍스트**: 이 가이드는 **PM Gate 검증 시 PM(오케스트레이터)이 참조하는 검증 기준 라이브러리**다. WIREFRAME 단계의 문서 QA(정적 문서 리뷰)는 별도 QA Gate 단계나 QA 에이전트 디스패치 없이 PM Gate가 직접 흡수한다. EXECUTE-UI 단계의 **빌드/린트 실행은 동작 검증(독립·불변 영역)** 이며, PM은 그 실행 결과와 wireframe↔코드 대조를 본 기준으로 확인한다 — "글자 존재"로 대체 불가.

---

## 목적

Wireframe UI 파이프라인의 품질을 **두 시점**에서 검증한다:

1. **WIREFRAME 단계 QA**: wireframe.md 품질 검증 → QA-WIREFRAME.md 생성
2. **EXECUTE-UI 단계 QA**: 빌드/린트 실행 + wireframe↔코드 대조 → QA-EXECUTE-UI.md 생성

---

## 적용 시점 (PM Gate 검증)

```
Wireframe UI 파이프라인:
  [wireframe.md 완료] → PM Gate 문서검증 (stage: WIREFRAME, 본 기준 적용) → 사용자 검토
  [UI 코드 구현 완료] → 동작 검증(빌드/린트 실행, 독립·불변) + PM Gate 검토 (stage: EXECUTE-UI, 본 기준으로 결과 확인) → 사용자 검토
```

---

## WIREFRAME 단계 QA 기준

wireframe-builder가 생성한 wireframe.md의 품질을 검증한다.

| # | 검증 항목 | 확인 내용 |
|---|----------|----------|
| W-1 | 섹션 완전성 | 서비스 개요, 전체 구조, 화면 목록, 화면별 상세, 공통 컴포넌트, shadcn 설치 목록 -- 6개 섹션이 모두 존재하는가 |
| W-2 | 화면 목록 완전성 | TASK.md에서 요청한 화면이 모두 wireframe.md에 포함되었는가 |
| W-3 | 상세 설계 충분성 | 각 화면의 ASCII 레이아웃, 구성 요소, 인터랙션이 명세되었는가 |
| W-4 | shadcn 컴포넌트 매핑 | 각 화면 요소가 shadcn 컴포넌트로 매핑되었는가 |
| W-5 | 구현 가능성 | ui-designer 스킬로 바로 구현 가능한 수준인가 (모호한 지시 없음) |

### WIREFRAME QA 프로세스

1. wireframe.md 읽기
2. TASK.md 읽기 (요구사항 교차 참조용)
3. W-1~W-5 검증 수행
4. QA-WIREFRAME.md 생성

### WIREFRAME QA 리포트 형식

```markdown
# QA: WIREFRAME — {태스크 제목}

> 검토일: YYYY-MM-DD | 판정: {Pass / Needs Revision}

## 1. 요약
{wireframe.md의 핵심 내용 3~5줄}

## 2. 검증 결과
| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| W-1 | 섹션 완전성 | Pass / Warning / Fail | {구체적 근거} |
| W-2 | 화면 목록 완전성 | Pass / Warning / Fail | {구체적 근거} |
| W-3 | 상세 설계 충분성 | Pass / Warning / Fail | {구체적 근거} |
| W-4 | shadcn 컴포넌트 매핑 | Pass / Warning / Fail | {구체적 근거} |
| W-5 | 구현 가능성 | Pass / Warning / Fail | {구체적 근거} |

## 3. 지적 사항
{Warning 또는 Fail 항목에 대한 상세 설명, 없으면 "지적 사항 없음"}

## 4. 교차 참조 검증
| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md | 요청한 화면이 모두 포함되었는가 | Pass / Warning |

## 5. 판정
**{Pass / Needs Revision}**
{판정 근거 1~2줄}
```

---

## EXECUTE-UI 단계 QA 기준

UI 구현 결과를 검증한다. **빌드/린트 실행**과 **wireframe↔코드 대조**를 수행한다.

| # | 검증 항목 | 확인 내용 |
|---|----------|----------|
| E-1 | 빌드 성공 | 빌드 명령(`npm run build` 등) 실행 결과 오류 없음 |
| E-2 | 린트 통과 | ESLint/타입 체크(`npm run lint`, `tsc --noEmit`) 오류 없음 |
| E-3 | 화면 커버리지 | wireframe.md의 화면 목록(마스터 테이블)이 모두 구현되었는가 |
| E-4 | 레이아웃 대조 | wireframe.md의 ASCII 레이아웃과 구현 화면 구조가 일치하는가 |
| E-5 | 컴포넌트 대조 | wireframe.md의 구성요소/shadcn 컴포넌트가 코드에 사용되었는가 |
| E-6 | 인터랙션 구현 | wireframe.md의 인터랙션 명세가 이벤트 핸들러로 구현되었는가 |

### EXECUTE-UI QA 프로세스

1. **빌드 실행** (E-1): 프로젝트의 빌드 명령을 실행하여 성공 여부 확인
2. **린트 실행** (E-2): ESLint + 타입 체크 실행
3. **wireframe.md 로드**: wireframe.md를 읽어 화면 목록, 구성요소, 인터랙션 명세를 추출
4. **대조 체크리스트 생성** (E-3~E-6): wireframe.md의 각 항목과 코드를 1:1 대조

### 대조 체크리스트 형식

```markdown
## 대조 체크리스트

### 화면 커버리지 (E-3)
| wireframe.md 화면 | 구현 파일 | 상태 |
|-------------------|----------|------|
| [A] 대시보드 | pages/dashboard.tsx | 구현됨 |
| [B] 사용자 목록 | pages/users.tsx | 구현됨 |
| [C] 설정 | — | 미구현 |

### 컴포넌트 대조 (E-5)
| wireframe.md 구성요소 | shadcn 컴포넌트 | 코드 경로 | 상태 |
|---------------------|----------------|----------|------|
| KPI 카드 4개 | Card | components/kpi-card.tsx | 구현됨 |
| 데이터 테이블 | DataTable | components/data-table.tsx | 구현됨 |

### 인터랙션 대조 (E-6)
| wireframe.md 인터랙션 | 구현 상태 | 비고 |
|---------------------|----------|------|
| 필터 드롭다운 변경 → 테이블 갱신 | 구현됨 | onChange 핸들러 |
| 행 클릭 → 상세 모달 | 부분 구현 | 모달은 있으나 데이터 바인딩 누락 |
```

### EXECUTE-UI QA 리포트 형식

```markdown
# QA: EXECUTE UI — {태스크 제목}

> 검토일: YYYY-MM-DD | 판정: {Pass / Needs Revision}

## 1. 요약
{UI 구현 결과 3~5줄 요약}

## 2. 빌드/린트 결과
| # | 검증 항목 | 결과 | 상세 |
|---|----------|------|------|
| E-1 | 빌드 성공 | Pass / Fail | {빌드 명령 + 결과} |
| E-2 | 린트 통과 | Pass / Warning / Fail | {경고/에러 수} |

## 3. 대조 체크리스트
{위 형식의 대조 체크리스트}

## 4. 검증 요약
| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| E-3 | 화면 커버리지 | {N/M} | {미구현 화면 목록} |
| E-4 | 레이아웃 대조 | Pass / Warning | {불일치 항목} |
| E-5 | 컴포넌트 대조 | {N/M} | {누락 컴포넌트} |
| E-6 | 인터랙션 구현 | {N/M} | {미구현 인터랙션} |

## 5. 지적 사항
{Warning 또는 Fail 항목에 대한 상세 설명}

### 심각도 분류
- Critical: 빌드 실패, 핵심 화면 미구현
- Warning: 린트 경고, 일부 인터랙션 미구현
- Info: 스타일 미세 차이 등

## 6. 판정
**{Pass / Needs Revision}**
{판정 근거 1~2줄}
```

---

## 판정 기준

### WIREFRAME 단계

| 판정 | 조건 |
|------|------|
| **Pass** | W-1~W-5 모두 통과, 또는 Info만 존재 |
| **Needs Revision** | Critical 1개 이상, 또는 Warning 3개 이상 |

### EXECUTE-UI 단계

| 판정 | 조건 |
|------|------|
| **Pass** | E-1, E-2 Pass + E-3~E-6 80% 이상 구현 |
| **Needs Revision** | E-1 또는 E-2 Fail, 또는 E-3~E-6 80% 미만 |

EXECUTE-UI 단계에서는 빌드(E-1) 또는 린트(E-2) 실패 시 자동으로 Critical 처리한다.

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.1 | 2026-06-07 | QA→PM Gate 통합 정합화 — 실행 컨텍스트를 "QA 전용 워커 에이전트" → "PM Gate 검증 시 PM이 참조하는 검증 기준 라이브러리"로 재정의(WIREFRAME 문서 QA는 PM Gate 흡수). "호출 시점(→ QA 호출 → QA-X.md)" → "적용 시점(PM Gate 검증)". EXECUTE-UI 빌드/린트 실행은 동작 검증(독립·불변)으로 명시 — 동작 검증 영역 불변. 검증 기준 콘텐츠 보존 (014 Phase 4-2) |
