# PLAN: 오케스트레이터 정비

> 작성일: 2026-03-30
> 입력: TASK.md, 영향 범위 조사 결과
> 출력: PLAN.md

## 1. 조사 결과 요약

### 변경 대상 (active 파일만, 과거 tasks/ 히스토리 제외)

| 구분 | 소스 (opal/) | 배포 (~/.opal/) | 프로젝트 docs/ |
|------|-------------|----------------|---------------|
| opw 삭제 | 스킬 폴더 + 레지스트리 + 참조 | 스킬 폴더 + 레지스트리 + 참조 | ARCHITECTURE, CONVENTIONS |
| opp 리네이밍 | 스킬 폴더 + 레지스트리 + 참조 | 스킬 폴더 + 레지스트리 + 참조 | ARCHITECTURE, CONVENTIONS |
| opdp 리네이밍+연동 | 스킬 폴더 + 레지스트리 + 참조 | 스킬 폴더 + 레지스트리 + 참조 | ARCHITECTURE, CONVENTIONS |

### 리네이밍 매핑

| Before | After | 약어 |
|--------|-------|------|
| opal-pilot-write (opw) | 삭제 | — |
| opal-project-pilot (opp) | opal-pilot-project (opp) | 유지 |
| opal-project-dev-pilot (opdp) | opal-pilot-project-dev (oppd) | 변경 |

## 2. 구현 계획

### Step 1: opw 삭제

**소스 삭제**:
- `rm -rf opal/skills/opal-pilot-write/`

**배포본 삭제**:
- `rm -rf ~/.opal/skills/opal-pilot-write/`

**레지스트리 정리** (`opal/core/references/opal-skills-registry.json`):
- opw 항목 제거

**참조 정리 (opw 언급 제거/수정)**:
- `opal/skills/opal-pilot-dev/SKILL.md` — "문서 작성(opal-pilot-write)" → "문서 작성(opal-pilot-write-tech)" 또는 제거
- `opal/skills/opal-pilot-dev-short/SKILL.md` — 동일
- `opal/skills/opal-project-init/SKILL.md` — opdp 내 opw 참조
- `opal/core/references/opal-harness.md` — 용어표 `opw / opwt` 행 → `opwt`만 유지

### Step 2: opp 리네이밍 (opal-project-pilot → opal-pilot-project)

**폴더 이동**:
- `mv opal/skills/opal-project-pilot/ opal/skills/opal-pilot-project/`
- `mv ~/.opal/skills/opal-project-pilot/ ~/.opal/skills/opal-pilot-project/` (또는 재배포)

**SKILL.md 수정**:
- name: opal-pilot-project
- description: 프로젝트 범용 오케스트레이터 (문서, 간단한 코드 수정 포함)
- triggers 업데이트

**레지스트리 수정**: name, paths, triggers 변경

**참조 파일 수정**:
- `opal/core/references/agents.md` — opal-project-pilot → opal-pilot-project
- `opal/core/references/opal-harness.md` — 용어표
- `opal/skills/op-task-plan/SKILL.md` — 탐색 경로
- `opal/skills/op-task-execute/SKILL.md` — 탐색 경로
- `opal/skills/op-task-qa/SKILL.md` — 참조

### Step 3: opdp 리네이밍 + opwt 연동 (opal-project-dev-pilot → opal-pilot-project-dev)

**폴더 이동**:
- `mv opal/skills/opal-project-dev-pilot/ opal/skills/opal-pilot-project-dev/`
- `mv ~/.opal/skills/opal-project-dev-pilot/ ~/.opal/skills/opal-pilot-project-dev/`

**SKILL.md 구조 변경**:
- name: opal-pilot-project-dev
- 약어: oppd
- Phase 1~2(PRD/TRD 직접 작성) → opwt 호출로 전환
  - Phase 1-2를 하나의 Phase로 통합: "opwt로 기획 산출물(PRD, TRD) 작성"
  - opwt의 "작성" 모드를 호출하여 PRD/TRD 생성
  - PM 검수는 opwt의 Phase 4(정합성 검증)로 대체
  - 사용자 확정 게이트는 유지
- Phase 3(ROADMAP)은 현행 유지 (PM 직접 작성)
- Phase 4(태스크 실행)에서 opd/opds 사용 명시 강화
- 자체 prd-guide.md, trd-guide.md → opwt에 위임되므로 참조만 유지

**레지스트리 수정**: name, alias(opdp→oppd), paths, triggers 변경

**참조 파일 수정**:
- `opal/skills/opal-project-init/SKILL.md` — opdp → oppd 참조
- `opal/core/references/opal-harness.md` — 용어표

### Step 4: 프로젝트 문서 + 전체 참조 정리

- `docs/ARCHITECTURE.md` — 오케스트레이터 목록/이름 갱신
- `docs/CONVENTIONS.md` — 스킬명 갱신
- `opal/core/references/opal-harness.md` — 용어표 최종 정리
- 배포본 동기화 최종 확인

### Step 5: 별도 태스크 등록

- agentic 자율 루핑 장치(QA/TEST 루핑 → 자율 개선/보정) 메모리 등록

## 3. 실행 체크리스트

- [x] 1-1. opw 소스 폴더 삭제
- [x] 1-2. opw 배포본 폴더 삭제
- [x] 1-3. 레지스트리 JSON에서 opw 제거
- [x] 1-4. opd, opds SKILL.md에서 opw 참조 수정
- [x] 1-5. 하네스 용어표에서 opw 정리
- [x] 2-1. opp 소스 폴더 이동
- [x] 2-2. opp SKILL.md name/description/triggers 수정
- [x] 2-3. 레지스트리 JSON에서 opp 항목 갱신
- [x] 2-4. op-task-plan, op-task-execute, op-task-qa에서 참조 수정
- [x] 2-5. agents.md에서 참조 수정
- [x] 2-6. opp 배포본 동기화
- [x] 3-1. opdp 소스 폴더 이동
- [x] 3-2. opdp SKILL.md 리네이밍 + opwt 연동 구조 반영
- [x] 3-3. 레지스트리 JSON에서 opdp 항목 갱신 (alias: oppd)
- [x] 3-4. opal-project-init에서 opdp→oppd 참조 수정
- [x] 3-5. opdp 배포본 동기화
- [x] 4-1. docs/ARCHITECTURE.md 갱신
- [x] 4-2. docs/CONVENTIONS.md 갱신
- [x] 4-3. 하네스 용어표 최종 정리
- [x] 4-4. 배포본 전체 동기화 최종 확인
- [x] 5-1. agentic 루핑 장치 메모리/태스크 등록

## 4. QA 체크리스트

- [x] 레지스트리 JSON에 opw 항목 없음
- [x] `opal-project-pilot`, `opal-project-dev-pilot` 문자열이 소스 어디에도 없음 (tasks/ 히스토리 제외)
- [x] `opw`가 독립 참조로 남아있지 않음 (opwt 제외)
- [x] 모든 소스 폴더와 배포본 폴더명 일치
- [x] opal-pilot-project-dev SKILL.md에서 opwt 호출 구조가 명확
- [x] 레지스트리의 paths가 실제 폴더 경로와 일치
