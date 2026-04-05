# TASK: opal-pilot-sdd (opsdd) 오케스트레이터 스킬 설계

> 작성일: 2026-04-03 | 갱신일: 2026-04-05 | 작업 유형: 신규 | 적용 스킬: opp | 모드: interactive
> 입력: SDD 방법론 리서치 + 설계 토론 (080 폴더 참고자료)
> 출력: opsdd 스킬 설계 문서 (PLAN.md)

## 작업 목표

SDD(Spec-Driven Development) 방법론을 OPAL 프레임워크에 통합하는 `opal-pilot-sdd` (약어: `opsdd`) 오케스트레이터 스킬을 설계한다. 기존 opal-pilot 스킬(opd/opds/opp)을 EXECUTE-LOOP에서 재활용하여 "명세 중심 divide and conquer + 자율 완성" 패턴을 구현한다.

## 배경

### 현재 문제

1. **기존 opd/opds는 단일 PLAN → 단일 EXECUTE 구조**: 태스크 크기에 관계없이 하나의 PLAN.md → 하나의 EXECUTE로 처리. 큰 태스크는 품질이 떨어지고, 작은 태스크는 과도한 오버헤드
2. **명세 단계 부재**: TASK.md에 요구사항을 나열하지만, Acceptance Criteria(수용 기준) 기반 정형 명세가 없어 "완성"의 기준이 모호
3. **Divide and Conquer 메커니즘 부재**: 큰 태스크를 자동으로 쪼개고, 각각 검증하며 루핑하는 구조가 없음

### SDD 방법론의 가치

- **명세가 SSOT** — "무엇을 만들지"가 코드에 묻히지 않음
- **검증 선행** — 구현 전에 명세와 태스크를 검증하여 환각/스코프 드리프트 방지
- **양방향 추적성** — AC ↔ 테스트 ↔ 태스크 ↔ 코드 전 과정 추적
- **AI 코딩 환각 감소** — 환각률 38% → 8.2% (카카오페이 사례)

### SDD vs OPAL의 개념 충돌과 해소

| 세계 | 최상위 개념 | 설명 |
|------|-----------|------|
| SDD | SPEC | 명세가 SSOT, 태스크는 명세에서 파생 |
| OPAL | TASK | 하네스 진입점, 모든 오케스트레이터의 출발 |

**해소 방안 (C안 채택)**: TASK는 진입점(행정적 역할), SPEC이 실질적 SSOT. 두 세계를 분리하되 연결한다:
- `specs/` — SDD 세계. SPEC이 최상위, tasks.md가 spec에서 파생
- `tasks/` — OPAL 세계. 기존 opal-pilot이 각 태스크를 실행
- **브릿지**: opsdd 오케스트레이터가 specs/tasks.md에서 각 태스크를 기존 opal-pilot(opd/opds/opp)으로 디스패치

### SDD 리서치 요약

주요 SDD 구현체(Kiro, spec-kit, cc-sdd)와 TDD 하이브리드(ATDD) 분석 완료.

| 구현체 | 구조 | 핵심 차별점 |
|--------|------|-----------|
| Amazon Kiro | requirements → design → tasks | 3단계 워크플로우, EARS 표기법 |
| GitHub spec-kit | spec → plan → tasks/ + constitution.md | 불변 원칙 별도 관리 |
| cc-sdd (gotalab) | specs/{feature}/ + steering/ | 멀티 에이전트 지원 |

SDD 성숙도 레벨: L1(Spec-First) → L2(Spec-Anchored) → L3(Spec-as-Source). OPAL은 **L2** 지향 (코드 우선 원칙 + opi 최신화로 동기화).

주요 함정 대응:

| 함정 | 대응 |
|------|------|
| Spec Theater (거대 스펙) | 기능 단위 스코프 제한, 훑어보게 되면 분할 |
| Spec/Code Drift | 코드 우선 원칙 유지 + opi 최신화 연계 |
| Over-specification | opsdd는 기능 개발 전용, 단순 작업은 opds |
| Waterfall 회귀 | 구현 중 발견 사항 spec.md 반영 허용 |

> 상세 리서치: `tasks/080-opp-opsdd-design-proposal/opsdd-리서치_v1_260405.md`
> 초안 제안서: `tasks/080-opp-opsdd-design-proposal/opsdd-제안서_v1_260405.md`

## 요구사항

### 파이프라인 설계

- [ ] R1. opsdd 6단계 파이프라인 설계: SPEC → SPEC-VERIFY → TASKS → TASKS-VERIFY → EXECUTE-LOOP → DONE
- [ ] R2. 각 단계의 수행 주체 명확화 (PM 직접 / 워커 디스패치), 워커 디스패치 시 에이전트 구분 (어떤 에이전트가 어떤 단계를 수행하는지)
- [ ] R3. 각 단계의 게이트 설계 — QA Gate + PM Gate 포함
- [ ] R4. EXECUTE-LOOP에서 기존 opal-pilot(opd/opds/opp) 호출 방식 설계

### 폴더 구조

- [ ] R5. specs/ 폴더 구조 설계 — 순번 포함 (`specs/{NNN}-{feature-name}/`)
- [ ] R6. specs/ (SDD 세계)와 tasks/ (OPAL 세계) 간 연결 구조 설계
- [ ] R7. tasks.md의 상태 관리 구조 설계 (추적 매트릭스, 의존관계, 태스크별 상태)

### 검증 (SDD + TDD)

- [ ] R8. SPEC-VERIFY: 3계층 검증(구조/의미/도메인) + AC 기반 테스트 시나리오 도출 (TDD Red)
- [ ] R9. TASKS-VERIFY: AC 커버리지 매핑, 의존관계 유효성, 자기완결성 검증
- [ ] R10. EXECUTE-LOOP 내 TEST: 검증 루프(L1~L3) 재활용 설계

### Agentic 모드

- [ ] R11. EXECUTE-LOOP의 `--agentic` 모드 설계 — PM 자율 게이트, 병렬 실행, 자동 루핑

### 스킬/에이전트 구성

- [ ] R12. 신규 단계 스킬 목록 확정 (op-sdd-spec, op-sdd-verify, op-sdd-tasks)
- [ ] R13. 각 단계 스킬의 에이전트 매핑 (어떤 에이전트가 수행하는지)
- [ ] R14. 기존 스킬 재활용 범위 확정 (op-dev-plan, op-dev-execute, op-dev-qa 등)

### 문서 체계

- [ ] R15. spec.md 표준 구조 정의 (Background, Goals, Non-goals, User Stories, FR, AC, Edge Cases, NFR, Constraints, Open Questions)
- [ ] R16. 문서 계층 관계 정의: TASK.md(진입) → spec.md(SSOT) → test-scenarios.md, tasks.md → T{N}/PLAN.md
- [ ] R17. verify.md 누적 저널 구조 설계

### 기존 스킬과의 포지셔닝

- [ ] R18. opd/opds/oppd와의 역할 분담 정리
- [ ] R19. oppd Phase 3 액션 스킬로서의 opsdd 연계 방안

## 확정된 설계 방향 (대화에서 합의)

### 1. C안 채택: TASK = 진입점, SPEC = SSOT

```
TASK.md (진입, 행정적) → spec.md (실질적 SSOT) → 이후 모든 것이 spec 기준
```

### 2. 두 세계 분리 구조

```
specs/{NNN}-{feature}/          ← SDD 세계 (SPEC이 왕)
├── spec.md                     # SSOT
├── tasks.md                    # 상태 관리 + 태스크 목록
├── verify.md                   # 검증 저널
├── tests/
│   └── test-scenarios.md       # AC → 테스트 시나리오 (TDD Red)
└── DONE.md

tasks/                          ← OPAL 세계 (기존 opal-pilot 실행)
├── {NNN}-opds-T1-{name}/      # T1 실행 (기존 opds)
├── {NNN}-opds-T2-{name}/      # T2 실행
└── {NNN}-opd-T3-{name}/       # T3 실행 (복잡하면 opd)
```

### 3. EXECUTE-LOOP에서 기존 opal-pilot 재활용

```
opsdd 오케스트레이터:
  for each T in tasks.md (의존 순서):
    → 기존 opal-pilot (opds/opd/opp) 디스패치
    → tasks/{NNN}-{스킬}-T{N}-{name}/ 에서 실행
    → 완료 후 tasks.md 상태 갱신
```

### 4. 파이프라인 흐름

```
Phase 1: SPEC ──────── spec.md 작성 (워커 디스패치)
Phase 2: SPEC-VERIFY ─ 3계층 검증 + 테스트 시나리오 도출 (워커 디스패치)
Phase 3: TASKS ─────── 태스크 분해 (워커 디스패치)
Phase 4: TASKS-VERIFY ─ 커버리지/의존관계 검증 (워커 디스패치)
Phase 5: EXECUTE-LOOP ─ 기존 opal-pilot로 각 태스크 실행 (PM 관리)
Phase 6: DONE ────────── 최종 검증 + 완료
```

### 5. 컴포넌트 구성 (잠정)

| 컴포넌트 | 유형 | 신규/기존 |
|----------|------|----------|
| opal-pilot-sdd (opsdd) | 오케스트레이터 | 신규 |
| op-sdd-spec | 단계 스킬 | 신규 |
| op-sdd-verify | 단계 스킬 | 신규 |
| op-sdd-tasks | 단계 스킬 | 신규 |
| opds/opd/opp | 오케스트레이터 (EXECUTE-LOOP) | 기존 재활용 |
| 하네스 | 공통 규칙 | 변경 없음 |

### 6. 미확정 사항 (PLAN에서 결정)

| # | 항목 | 선택지 |
|---|------|--------|
| 1 | spec.md 갱신 정책 | 구현 중 즉시 반영 vs 구현 후 일괄 반영 |
| 2 | 경량 모드 | 항상 전체 6단계 vs --light 옵션 |
| 3 | 검증 에이전트 | 별도 에이전트 vs QA 에이전트 확장 |
| 4 | 테스트 코드 위치 | specs/tests/ vs 프로젝트 tests/ |
| 5 | oppd 연계 | Phase 3 액션 스킬 등록 시점 |

## 제약 조건

- OPAL 전용 스킬 (`~/.opal/skills/opal-pilot-sdd/` 경로)
- SDD 세계에서 SPEC이 SSOT — 파이프라인 설계에 반영
- OPAL 하네스(Guards, Gates, State) 규칙 준수 — 하네스 변경 없음
- 기존 opal-pilot(opd/opds/opp)을 EXECUTE-LOOP에서 그대로 재활용
- SKILL.md 500줄 이하 유지
- 범용 (언어/프레임워크 무관)
- 플랫폼 독립 (Claude Code, Cursor, Gemini)

## 기술 스택

- OPAL 프레임워크 (마크다운 기반 스킬 시스템)
- 참조 방법론: SDD + TDD 하이브리드 (ATDD)

## 관련 문서

### 080 폴더 참고자료

- `tasks/080-opp-opsdd-design-proposal/sdd.txt` — SDD 방법론 기본 개념
- `tasks/080-opp-opsdd-design-proposal/sdd1.txt` — SDD+TDD 하이브리드 8단계
- `tasks/080-opp-opsdd-design-proposal/opsdd-제안서_v1_260405.md` — 초안 제안서
- `tasks/080-opp-opsdd-design-proposal/opsdd-리서치_v1_260405.md` — SDD 리서치 정리

### OPAL 프레임워크 문서

- `~/.opal/references/opal-harness.md` — 하네스 공통 규칙
- `~/.opal/references/opal-harness-interactive.md` — interactive 모드 게이트
- `~/.opal/references/opal-harness-agentic.md` — agentic 모드
- `~/.opal/skills/opal-pilot-project-dev/SKILL.md` — oppd (포지셔닝 비교)
- `~/.opal/skills/opal-pilot-dev/SKILL.md` — opd (EXECUTE-LOOP 재활용)
- `~/.opal/skills/opal-pilot-dev-short/SKILL.md` — opds (EXECUTE-LOOP 재활용)
