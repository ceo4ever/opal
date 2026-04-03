# TASK: opal-pilot-sdd (opsdd) 스킬 설계 방안 제안

> 작성일: 2026-04-03 | 작업 유형: 신규 | 적용 스킬: opp | 모드: interactive
> 입력: sdd.txt, sdd1.txt, 대화 컨텍스트
> 출력: opsdd 스킬 설계 방안 문서 (PLAN.md)

## 작업 목표

SDD(Spec-Driven Development) 방법론을 분석하여, OPAL 프레임워크에 통합할 `opal-pilot-sdd` (약어: `opsdd`) 스킬의 설계 방안을 제안한다.

## 배경

SDD는 코드 작성 전에 spec.md(기능 명세)를 먼저 확정하고, 그것을 기반으로 구현과 검증을 진행하는 방법론이다. AI 코딩 환경에서 환각을 줄이고 요구사항 추적성을 높이는 데 특히 유효하다. (AI 환각률 38% → 8.2% 사례 존재)

기존 OPAL 개발 스킬들(opd/opds)은 TASK → PLAN → EXECUTE 구조로, 명세 단계가 별도로 존재하지 않는다. opsdd는 SPEC을 TASK보다 상위에 두어 "무엇을 만들지"를 코드 작성 전에 완전히 확정하는 새 개발 방법 스킬이다.

## 요구사항

- [ ] sdd.txt, sdd1.txt의 SDD 핵심 개념 및 흐름 분석
- [ ] 기존 OPAL 스킬(oppd, opds, opp)과의 포지셔닝 비교 분석
- [ ] opsdd 파이프라인 설계 제안 (단계 구성 + 산출물)
- [ ] 각 단계의 신규 스킬 필요 여부 판단 (신규 vs 기존 재활용)
- [ ] TDD 통합 여부 및 방식 결정 제안
- [ ] opal-skill-creator (osc) 활용 계획 제안

## 제약 조건

- OPAL 전용 스킬 (`~/.opal/skills/opal-pilot-sdd/` 경로)
- SPEC이 TASK보다 상위 개념 — 파이프라인 설계에 반드시 반영
- OPAL 하네스(Guards, Gates, State) 규칙 준수
- 기존 스킬(op-task, op-dev-execute, op-dev-qa 등) 최대한 재활용
- SKILL.md 500줄 이하 유지

## 기술 스택

- OPAL 프레임워크 (마크다운 기반 스킬 시스템)
- 참조 방법론: SDD + TDD 하이브리드 (sdd1.txt)

## 관련 문서

- `temp/sdd.txt` — SDD 방법론 기본 개념, spec.md 구조, 검증 스크립트
- `temp/sdd1.txt` — SDD+TDD 하이브리드 8단계 워크플로우, 실제 사례
- `~/.opal/references/opal-harness.md` — 하네스 공통 규칙
- `~/.opal/skills/opal-pilot-project-dev/SKILL.md` — oppd 참조 (포지셔닝 비교)
- `~/.opal/skills/opal-skill-creator/SKILL.md` — osc (스킬 생성 후 단계)

---

## SDD 방법론 분석 (sdd.txt + sdd1.txt 정리)

> PLAN 단계에서 이 섹션을 기준으로 스킬을 설계한다.

### 1. SDD란

**Spec-Driven Development** — 명세 중심 개발 방법론.
코드보다 명세를 먼저 작성하고, 명세를 SSOT(Single Source of Truth)로 삼아 구현과 검증을 진행한다.

- **목적**: "무엇을 왜 만드는지"가 코드에 묻히는 문제 방지, 일관성·추적성 확보
- **AI 코딩 효과**: 환각률 38% → 8.2% 감소, 코드 리뷰 시간 60% 감소 (카카오페이 사례)
- **TDD와의 차이**: TDD는 테스트 먼저, SDD는 명세 먼저. 둘은 상호보완적

### 2. 핵심 흐름

```
SDD:  spec.md 작성 → 명세 검증 → plan.md → tasks.md → 구현
TDD:  테스트 스켈레톤 → 구현(Green) → 리팩토링(Refactor)

하이브리드:
  SPEC(SDD) → VALIDATE → PLAN → TEST-SKELETON(TDD Red) → EXECUTE(Green) → REFACTOR → QA
```

### 3. spec.md 구조

SDD의 핵심 산출물. 구현 세부가 아닌 **의도와 동작**을 기술한다.

| 섹션 | 내용 |
|------|------|
| Background | 왜 이 기능이 필요한지 |
| Goals / Non-goals | 범위 확정 |
| User Stories | `As a ... I want ... so that ...` |
| Functional Requirements | 반드시 동작해야 하는 기능 목록 |
| Acceptance Criteria | `GIVEN / WHEN / THEN` 형태 (← TDD 테스트와 1:1 매핑) |
| Edge Cases | 예외 상황, 실패 케이스 |
| Non-functional Requirements | 성능, 보안, 접근성 |
| Constraints | 기술적·정책적 제한 |
| Open Questions | 미결정 사항 |

### 4. spec.md 검증 스크립트

spec이 완성되지 않으면 구현으로 넘어가지 않는다.

```python
# 검사 항목 (validate-spec.py)
- 필수 섹션 존재 여부 (Background, Goals, Acceptance Criteria 등)
- "NEEDS CLARIFICATION" 마커 잔존 여부
- Acceptance Criteria의 GIVEN/WHEN/THEN 형식 최소 1개 이상
- 최소 bullet-point 요구사항 수 (5개 이상)
```

검증 실패 시 → 섹션 보강 → 재검증. 통과 후에만 PLAN 진행.

### 5. SDD+TDD 하이브리드 8단계 (sdd1.txt)

```
Phase 1: 명세 정의 (SDD)
  ① spec.md 작성 (사용자 스토리 + GIVEN/WHEN/THEN)
  ② validate-spec.py 실행 → PASS 확인
  ③ plan.md + tasks.md 생성

Phase 2: 테스트 주도 구현 (TDD)
  ④ 테스트 스켈레톤 생성 (Red) — spec.md AC → pytest 자동 생성
  ⑤ 최소 구현 (Green) — 테스트 통과 코드
  ⑥ 리팩토링 (Refactor) — ruff + pytest

Phase 3: Quality Gate
  ⑦ 전체 검증 (make ci: spec + lint + test)
  ⑧ PR → Merge
```

**핵심 연결고리**: `spec.md의 Acceptance Criteria ↔ pytest 테스트 함수 1:1 매핑`

### 6. 실제 프로젝트 파일 구조

```
specs/001-{feature}/
├── spec.md           # SDD: 무엇을
├── plan.md           # 기술 계획
├── tasks.md          # T001~T005 작업 분해
├── tests/test_*.py   # TDD: 잘됨을 검증
└── src/{feature}/    # 최종 구현
```

### 7. OPAL 스킬 설계에의 시사점

| SDD 개념 | opsdd 스킬 설계 반영 방향 |
|----------|--------------------------|
| SPEC이 TASK 상위 | 파이프라인 첫 단계를 SPEC으로 확정 |
| spec 검증 게이트 | SPEC → VALIDATE 단계 또는 SPEC 단계 내 검증 포함 |
| AC → 테스트 1:1 매핑 | EXECUTE 단계에 테스트 스켈레톤 생성 포함 |
| Quality Gate | 기존 op-dev-qa 재활용 가능 |
| plan.md + tasks.md | PLAN 단계 산출물로 통합 |
| Open Questions | SPEC 완료 조건에 "미결 없음" 포함 |
