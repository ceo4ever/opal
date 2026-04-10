# PLAN: opsdd STATE Gate 완성 + VERIFY Phase 추가

> 작성일: 2026-04-10 | 태스크: 105-opp-opsdd-state-gate-verify

---

## 1. 배경 분석

### 1-1. 현재 파일 상태

#### `opal/skills/opal-pilot-sdd/SKILL.md` (v2.4)

- **문제**: STATE.md 도메인 치환값 섹션이 "완료 산출물" 독자 테이블 구조로 남아 있다.
  - 산출물 목록 테이블 (`| 산출물 | 상태 |`) 방식 → 하네스 §3 공통 진행 현황 행 구조와 불일치
  - State Gate가 진행 현황 행을 기반으로 동작하는데, opsdd는 독자 구조를 쓰므로 State Gate가 실제로 동작 불가
  - v2.3 changelog에 "하네스 §3 진행 현황 테이블 적용"이라고 명시했지만, 실제 STATE.md 구조 예시는 여전히 구 방식
- **문제**: 파이프라인이 5단계(TASK→SPEC→REVIEW→DESIGN→EXECUTE-LOOP→DONE)에서 VERIFY Phase 없음
  - 배경에 언급된 E2E 미수행, TEST-SCENARIOS.md 실시간 갱신 안 함 문제의 원인
  - PM 직접 E2E 검증을 강제하는 명시적 단계가 없음
- **문제**: EXECUTE Phase에 L1(tsc --noEmit)/L2(pnpm build) ACT별 검증 루프 명시 없음
- **문제**: ACT 목록 테이블에 코드/L1 lint/L2 build 컬럼 없음

#### `opal/skills/opal-pilot-sdd/references/execute-loop-guide.md`

- **문제**: §9.2 ACT 목록 테이블이 `| ACT | 이름 | 그룹 | 상태 | 완료일 |` 구조
  - L1/L2 컬럼 없어 PM이 빌드 검증 결과를 추적할 수 없음
- **문제**: §9의 제목은 "STATE.md ACT 상태 관리"이지만 L1/L2 검증 루프 설명 없음

#### `opal/skills/opal-pilot-sdd/references/spec-plan-guide.md`

- **문제**: SPEC-PLAN.md의 ACT 블록 구조 설명에 상태 필드 금지 원칙이 없음
  - ACT 블록에 상태 필드를 두면 STATE.md의 ACT 목록 SSOT 원칙과 충돌

#### `opal/core/references/opal-harness.md` (v3.3)

- **문제**: §3 진행 현황 행 구성 규칙에 "오케스트레이터 SKILL.md 도메인 치환값에 스킬별 예시가 명시됨"이라고 했지만, opsdd 진행 현황 행 예시가 하네스 §3에 없음
  - 하네스 §3에 opp/opd 예시가 없듯 opsdd도 없으나, TASK.md에 요구사항으로 명시됨 (R-5)

### 1-2. 변경 필요 지점 요약

| 파일 | 변경 필요 지점 | 우선순위 |
|------|-------------|---------|
| `opal/skills/opal-pilot-sdd/SKILL.md` | STATE.md 도메인 치환값 교체 (완료 산출물 → 진행 현황 행 구조) | 높음 |
| `opal/skills/opal-pilot-sdd/SKILL.md` | VERIFY Phase 신설 (Phase 5), DONE → Phase 6 | 높음 |
| `opal/skills/opal-pilot-sdd/SKILL.md` | YAML frontmatter description 업데이트 (6단계 반영) | 높음 |
| `opal/skills/opal-pilot-sdd/SKILL.md` | Phase 4 EXECUTE-LOOP — L1/L2 검증 루프 명시 | 높음 |
| `opal/skills/opal-pilot-sdd/references/execute-loop-guide.md` | §9.2 ACT 목록 테이블에 코드/L1 lint/L2 build 컬럼 추가 | 높음 |
| `opal/skills/opal-pilot-sdd/references/spec-plan-guide.md` | ACT 블록 상태 필드 금지 원칙 추가 | 높음 |
| `opal/core/references/opal-harness.md` | §3 opsdd 진행 현황 행 예시 추가 | 중간 |

---

## 2. 구현 전략

### 2-1. 적용 순서

의존관계를 고려하여 다음 순서로 적용한다:

```
Step 1: execute-loop-guide.md 수정 (R-3 — ACT 목록 테이블 컬럼 추가)
  ↓ ACT 목록 SSOT 구조 확정 후
Step 2: spec-plan-guide.md 수정 (R-4 — ACT 상태 필드 금지 원칙)
  ↓ ACT 관련 문서 정비 완료 후
Step 3: SKILL.md 수정 (R-1 STATE.md 도메인 치환값 교체)
  ↓ 진행 현황 행 구조 확정 후
Step 4: SKILL.md 수정 (R-2 VERIFY Phase 신설 + R-3 Phase 4 L1/L2 명시)
  ↓ SKILL.md 전체 반영 완료 후
Step 5: opal-harness.md 수정 (R-5 opsdd 진행 현황 행 예시 추가)
```

**이유**:
- execute-loop-guide.md의 ACT 목록 테이블 구조가 확정되어야, SKILL.md STATE.md 도메인 치환값의 ACT 목록 SSOT 컬럼을 정확히 기술할 수 있다
- spec-plan-guide.md의 ACT 상태 필드 금지는 독립적이지만 execute-loop-guide.md에서 ACT 목록이 SSOT임을 명확히 한 후 작성하는 것이 논리적
- SKILL.md 변경이 가장 복잡하므로 전제 문서를 먼저 완성
- harness.md 변경은 중간 우선순위이므로 마지막

### 2-2. 각 요구사항별 접근 방법

#### R-1: STATE.md 도메인 치환값 교체

현재 "완료 산출물" 섹션 구조:
```
## 완료 산출물
| 산출물 | 상태 |
```

교체 후 "진행 현황" 테이블 구조 (24행):
- **TASK** (3행): 작업 / TASK.md 생성 / 사용자 확인
- **SPEC** (5행): 작업 / SPEC.md 생성 / State Gate / PM Gate / 사용자 확인
  - SPEC은 워커 디스패치 → State Gate → PM Gate → 사용자 Gate (QA Gate 없음)
- **REVIEW** (4행): 작업 / TEST-SCENARIOS.md 생성 / State Gate / 사용자 확인
  - REVIEW는 PM 직접 수행 → Gate 최소화
- **DESIGN** (5행): 작업 / SPEC-PLAN.md 생성 / State Gate / PM Gate / 사용자 확인
  - DESIGN은 워커 디스패치 → State Gate → PM Gate → 사용자 Gate (QA Gate 없음)
- **EXECUTE** (2행): 요약 1행 + 사용자 확인
  - EXECUTE-LOOP는 ACT별 내부 관리 → 진행 현황 테이블에는 요약 행만
- **VERIFY** (3행): 작업 / State Gate / 사용자 확인
  - VERIFY는 PM 직접 E2E 수행 → 사용자 Gate
- **DONE** (2행): DONE.md 생성 / 사용자 확인

**ACT 목록 테이블 SSOT** 섹션 추가:
```
| ACT | 이름 | 그룹 | 의존 | 코드 | L1 lint | L2 build | 상태 | 시작 | 완료 |
```

**TS 현황 요약** 섹션 추가:
```
Green: N / Red: N / Fail: N / Skip: N
```

**SPEC 변경 이력** 섹션 추가

#### R-2: VERIFY Phase 신설

파이프라인 변경:
- 현재: TASK → SPEC → REVIEW → DESIGN → EXECUTE-LOOP → DONE (5→6단계 이미 6단계)
- 변경: TASK → SPEC → REVIEW → DESIGN → EXECUTE-LOOP → VERIFY → DONE (Phase 0~6)

YAML frontmatter:
- description에서 "5단계 파이프라인" → "6단계 파이프라인" 변경
- version: 2.4.0 → 2.5.0

Phase 번호 이동:
- 기존 Phase 5: DONE → Phase 6: DONE
- 신규 Phase 5: VERIFY

VERIFY Phase 내용:
- PM 직접 Playwright E2E 수행 (워커 디스패치 없음)
- TEST-SCENARIOS.md 실시간 갱신 의무
- State Gate → 사용자 Gate 순서

#### R-3: EXECUTE Phase L1/L2 검증 루프

SKILL.md Phase 4에 추가:
- PM이 각 ACT 완료 후 L1(tsc --noEmit) + L2(pnpm build) 직접 검증 의무 명시
- 재시도 규칙: L1 무제한, L2 2회 초과 → 캡틴 에스컬레이션

execute-loop-guide.md §9.2 ACT 목록 테이블:
- 현재: `| ACT | 이름 | 그룹 | 상태 | 완료일 |`
- 변경: `| ACT | 이름 | 그룹 | 의존 | 코드 | L1 lint | L2 build | 상태 | 시작 | 완료 |`

#### R-4: SPEC-PLAN.md ACT 상태 필드 금지

spec-plan-guide.md에 추가:
- §8 ACT 분해 섹션(또는 관련 위치)에 "ACT 블록에 상태 필드 금지" 원칙 명시
- 이유: STATE.md ACT 목록 테이블이 상태 SSOT — 중복 관리 금지

#### R-5: harness.md §3 opsdd 진행 현황 행 예시

opal-harness.md §3 "진행 현황 행 구성 규칙" 하단 또는 별도 서브섹션에:
- opsdd 스킬의 진행 현황 행 예시 24행 추가
- SPEC/REVIEW/DESIGN/EXECUTE/VERIFY/DONE 단계별 행 구조 예시

### 2.3 교체될 STATE.md 템플릿 (실행 기준)

> R-1 적용 후 opsdd SKILL.md의 `{{STATE.md 도메인 치환값}}` 섹션에 들어갈 완성 템플릿.
> 실행 워커는 이 템플릿을 기준으로 SKILL.md를 수정한다.

```markdown
# STATE: {기능명} SDD 개발

> 최종 갱신: YYYY-MM-DD HH:mm

## 현재 상태
- 모드: SDD Task
- Phase: {현재 Phase}
- 상태: {진행 중 / 완료 / 블로커 / 추가작업중 / 추가작업완료}

## 진행 현황

> 상태값: ⬜ 대기 / 🔄 진행 중 / ✅ 완료 / ❌ 실패 / - 해당 없음
> **수행 원칙**: 위에서 아래로 순서대로 처리한다. 현재 행이 ✅가 아니면 다음 행으로 진행 불가.

| # | Phase | 항목 | 상태 | 시점 |
|---|-------|------|------|------|
| 1 | TASK | TASK.md 작성 | ⬜ | |
| 2 | TASK | STATE.md 생성 | ⬜ | |
| 3 | TASK | 사용자 확인 | ⬜ | |
| 4 | SPEC | 워커 디스패치 | ⬜ | |
| 5 | SPEC | SPEC.md 생성 | ⬜ | |
| 6 | SPEC | State Gate | ⬜ | |
| 7 | SPEC | Artifact Gate | ⬜ | |
| 8 | SPEC | State Gate | ⬜ | |
| 9 | SPEC | PM Gate | ⬜ | |
| 10 | SPEC | State Gate | ⬜ | |
| 11 | SPEC | 사용자 확인 | ⬜ | |
| 12 | REVIEW | 구조 검증 (S-1~S-6) | ⬜ | |
| 13 | REVIEW | TEST-SCENARIOS.md 작성 | ⬜ | |
| 14 | REVIEW | FR↔TS 커버리지 확인 | ⬜ | |
| 15 | REVIEW | State Gate | ⬜ | |
| 16 | REVIEW | Artifact Gate | ⬜ | |
| 17 | REVIEW | State Gate | ⬜ | |
| 18 | REVIEW | PM Gate | ⬜ | |
| 19 | REVIEW | State Gate | ⬜ | |
| 20 | REVIEW | 사용자 확인 | ⬜ | |
| 21 | DESIGN | 워커 디스패치 | ⬜ | |
| 22 | DESIGN | SPEC-PLAN.md 생성 | ⬜ | |
| 23 | DESIGN | State Gate | ⬜ | |
| 24 | DESIGN | Artifact Gate | ⬜ | |
| 25 | DESIGN | State Gate | ⬜ | |
| 26 | DESIGN | PM Gate | ⬜ | |
| 27 | DESIGN | State Gate | ⬜ | |
| 28 | DESIGN | 사용자 확인 | ⬜ | |
| 29 | EXECUTE | ACT 실행 (상세: ACT 목록 참조) | ⬜ | |
| 30 | EXECUTE | State Gate | ⬜ | |
| 31 | EXECUTE | PM Gate | ⬜ | |
| 32 | EXECUTE | State Gate | ⬜ | |
| 33 | EXECUTE | 사용자 확인 | ⬜ | |
| 34 | VERIFY | E2E 테스트 수행 | ⬜ | |
| 35 | VERIFY | TS 전체 Green 확인 | ⬜ | |
| 36 | VERIFY | State Gate | ⬜ | |
| 37 | VERIFY | PM Gate | ⬜ | |
| 38 | VERIFY | State Gate | ⬜ | |
| 39 | VERIFY | 사용자 확인 | ⬜ | |
| 40 | DONE | State Gate | ⬜ | |
| 41 | DONE | DONE.md 생성 | ⬜ | |
| 42 | DONE | State Gate | ⬜ | |
| 43 | DONE | 사용자 확인 | ⬜ | |

## ACT 목록 (SSOT — EXECUTE Phase 상세)

> DESIGN 완료 후 SPEC-PLAN.md의 ACT를 기반으로 동적 삽입.
> ACT 완료 시 즉시 갱신. SPEC-PLAN.md에는 ACT 상태를 두지 않는다.

| ACT | 이름 | 그룹 | 의존 | 코드 | L1 lint | L2 build | 상태 | 시작 | 완료 |
|-----|------|------|------|------|---------|----------|------|------|------|

> 상태값: ⬜ 대기 / 🔄 진행 중 / ✅ 완료 / ❌ 실패
> L1/L2: ACT 완료 후 PM이 검증 실행. ❌→✅ = 1차 실패 → 수정 → 재통과

## TS 현황 (VERIFY Phase 요약)

> TEST-SCENARIOS.md 추적 매트릭스의 요약. 테스트 수행 시 즉시 갱신.

| 상태 | 건수 |
|------|------|
| Green | 0 |
| Red | 0 |
| Fail | 0 |
| Skip | 0 |

## SPEC 변경 이력

> REVIEW 이후 SPEC.md가 변경된 경우 기록. 변경 추적이 안 되면 TS와 정합성이 깨진다.

| # | 시점 | 변경 내용 | 사유 |
|---|------|----------|------|

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|

## 블로커
없음

## 다음 액션
{다음으로 수행할 작업}
```

---

## 3. 실행 체크리스트

### Step 1: execute-loop-guide.md 수정 (R-3 부분)

- [ ] `opal/skills/opal-pilot-sdd/references/execute-loop-guide.md` 읽기
- [ ] §9.2 ACT 목록 테이블 구조 변경
  - [ ] 현재 컬럼 `| ACT | 이름 | 그룹 | 상태 | 완료일 |` 확인
  - [ ] 새 컬럼 `| ACT | 이름 | 그룹 | 의존 | 코드 | L1 lint | L2 build | 상태 | 시작 | 완료 |`로 교체
  - [ ] 예시 데이터 행도 새 컬럼에 맞게 업데이트
- [ ] §9-3 갱신 시점 테이블에 L1/L2 관련 갱신 이벤트 추가
- [ ] §1 (또는 별도 서브섹션)에 L1/L2 검증 루프 규칙 추가
  - [ ] L1(tsc --noEmit): 무제한 재시도
  - [ ] L2(pnpm build): 2회 초과 → 캡틴 에스컬레이션
- [ ] 변경이력 항목 추가

### Step 2: spec-plan-guide.md 수정 (R-4)

- [ ] `opal/skills/opal-pilot-sdd/references/spec-plan-guide.md` 읽기
- [ ] ACT 블록 구조 설명 위치 확인 (§8 또는 관련 섹션)
- [ ] ACT 상태 필드 금지 원칙 추가
  - [ ] "ACT 블록에 상태 필드를 두지 않는다" 원칙 명시
  - [ ] 이유: STATE.md ACT 목록 테이블이 상태 SSOT
  - [ ] 위반 시 STATE.md와 중복 관리로 불일치 발생 경고
- [ ] 변경이력 항목 추가

### Step 3: SKILL.md 수정 — STATE.md 도메인 치환값 교체 (R-1)

- [ ] `opal/skills/opal-pilot-sdd/SKILL.md` 읽기
- [ ] "STATE.md 도메인 치환값" 섹션 전체 교체
  - [ ] 필드 테이블에 VERIFY Phase 반영 (`단계 목록` 업데이트)
  - [ ] "완료 산출물" 구조 제거
  - [ ] 하네스 공통 진행 현황 행 구조로 교체 (24행 예시)
    - [ ] TASK 3행 포함
    - [ ] SPEC 5행 포함
    - [ ] REVIEW 4행 포함
    - [ ] DESIGN 5행 포함
    - [ ] EXECUTE 2행(요약+사용자확인) 포함
    - [ ] VERIFY 3행 포함
    - [ ] DONE 2행 포함
  - [ ] ACT 목록 SSOT 테이블 명시 (`| ACT | 이름 | 그룹 | 의존 | 코드 | L1 lint | L2 build | 상태 | 시작 | 완료 |`)
  - [ ] TS 현황 요약 섹션 추가 (Green/Red/Fail/Skip 건수)
  - [ ] SPEC 변경 이력 섹션 추가
- [ ] STATE.md 구조 예시 코드블록 업데이트

### Step 4: SKILL.md 수정 — VERIFY Phase + Phase 4 L1/L2 (R-2, R-3)

- [ ] YAML frontmatter 업데이트
  - [ ] description: "5단계 파이프라인" → "6단계 파이프라인"
  - [ ] version: 2.4.0 → 2.5.0
- [ ] 5단계 파이프라인 요약 다이어그램 업데이트
  - [ ] EXECUTE-LOOP → VERIFY → DONE 구조 반영
  - [ ] VERIFY Phase 라인 추가
- [ ] Phase 5 DONE → Phase 6 DONE으로 번호 이동
- [ ] Phase 5 VERIFY 섹션 신설
  - [ ] 워커 디스패치 없음 (PM 직접) 명시
  - [ ] PM 직접 Playwright E2E 수행 절차
  - [ ] TEST-SCENARIOS.md 실시간 갱신 의무
  - [ ] TS 현황 요약 갱신
  - [ ] Gate: State Gate → 사용자 Gate
- [ ] Phase 4 EXECUTE-LOOP 섹션 수정
  - [ ] "ACT 실행 순서" 또는 "상태 갱신" 서브섹션에 L1/L2 검증 명시
  - [ ] PM이 각 ACT 완료 후 L1/L2 직접 검증 의무
  - [ ] L1 무제한 / L2 2회 초과 → 캡틴 에스컬레이션 규칙
- [ ] 변경이력 항목 추가 (v2.5)

### Step 5: opal-harness.md 수정 — opsdd 진행 현황 행 예시 (R-5)

- [ ] `opal/core/references/opal-harness.md` §3 "진행 현황 행 구성 규칙" 위치 확인
- [ ] 기존 "오케스트레이터 SKILL.md 도메인 치환값에 해당 스킬의 진행 현황 행 예시가 명시됨" 문구 아래에 opsdd 예시 서브섹션 추가
  - [ ] opsdd 6단계 진행 현황 행 24행 예시 테이블 추가
  - [ ] 각 단계별 설명 주석 추가
- [ ] 변경이력 항목 추가

---

## 4. QA 체크리스트

### 4-1. STATE Gate 완성 검증

- [ ] SKILL.md STATE.md 도메인 치환값의 진행 현황 행 구조가 하네스 §3 "진행 현황 행 구성 규칙"과 일치한다
- [ ] TASK 단계가 3행(작업/산출물/사용자확인)으로 구성된다 (Gate 없음)
- [ ] SPEC/DESIGN 단계가 State Gate + PM Gate를 포함한다 (QA Gate 없음, **순서: State Gate → PM Gate**)
- [ ] SPEC/DESIGN 단계 진행 현황 행의 Gate 순서가 "State Gate → PM Gate"이다 (PM Gate가 State Gate보다 나중)
- [ ] REVIEW 단계가 PM 직접 수행으로 Gate 최소화되어 있다
- [ ] EXECUTE 단계가 요약 행으로만 구성된다 (상세는 ACT 목록 테이블에서 관리)
- [ ] VERIFY 단계가 3행(작업/State Gate/사용자확인)으로 구성된다
- [ ] DONE 단계가 2행(DONE.md 생성/사용자확인)으로 구성된다
- [ ] 총 행 수가 24행임을 확인한다

### 4-2. ACT 목록 SSOT 검증

- [ ] execute-loop-guide.md §9.2 ACT 목록 테이블이 `| ACT | 이름 | 그룹 | 의존 | 코드 | L1 lint | L2 build | 상태 | 시작 | 완료 |` 구조다
- [ ] SKILL.md STATE.md 도메인 치환값의 ACT 목록 SSOT 컬럼이 execute-loop-guide.md와 일치한다
- [ ] spec-plan-guide.md에 ACT 상태 필드 금지 원칙이 명시되어 있다

### 4-3. VERIFY Phase 검증

- [ ] SKILL.md 파이프라인 다이어그램에 VERIFY Phase가 포함되어 있다
- [ ] YAML frontmatter description이 6단계 파이프라인을 설명한다
- [ ] Phase 5: VERIFY 섹션이 존재한다
- [ ] Phase 6: DONE 섹션으로 번호가 이동되었다
- [ ] VERIFY Phase에 E2E 수행 + TEST-SCENARIOS.md 갱신 의무가 명시되어 있다
- [ ] VERIFY Phase Gate 순서가 "State Gate → 사용자 Gate"이다

### 4-4. L1/L2 검증 루프 검증

- [ ] execute-loop-guide.md에 L1/L2 검증 루프 규칙이 명시되어 있다
- [ ] SKILL.md Phase 4에 PM이 각 ACT 완료 후 L1/L2 직접 검증 의무가 명시되어 있다
- [ ] L1 무제한 재시도, L2 2회 초과 → 에스컬레이션 규칙이 반영되어 있다
- [ ] ACT 목록 테이블에 L1 lint / L2 build 컬럼이 추가되어 있다

### 4-5. 일관성 검증

- [ ] SKILL.md의 파이프라인 요약, STATE.md 도메인 치환값, 각 Phase 섹션이 모두 6단계를 일관되게 반영한다
- [ ] SKILL.md agentic 모드 자율 게이트 흐름에도 VERIFY Phase가 반영되어 있다
- [ ] harness.md §3의 opsdd 예시가 SKILL.md의 도메인 치환값과 일치한다
- [ ] 소스 경로(`opal/skills/`, `opal/core/`)만 수정되고 `~/.opal/` 직접 수정이 없다

### 4-6. 변경이력 검증

- [ ] SKILL.md 변경이력에 v2.5 항목이 추가되어 있다
- [ ] execute-loop-guide.md 변경이력에 항목이 추가되어 있다
- [ ] spec-plan-guide.md 변경이력이 있으면 항목이 추가되어 있다
- [ ] opal-harness.md 변경이력에 항목이 추가되어 있다

---

## 5. 주의 사항 및 리스크

### 5-1. 106 태스크와의 충돌 주의

- 106 태스크(Artifact Gate 제거)도 opsdd SKILL.md를 수정할 예정
- 105에서 먼저 수정 완료 후 106에서 105 변경 내용을 기반으로 조율
- 특히 SKILL.md Gate 순서 관련 섹션에서 충돌 가능성 있음

### 5-2. EXECUTE 단계 진행 현황 행 설계

- EXECUTE-LOOP는 ACT가 동적으로 생성되므로 진행 현황 테이블에 고정 행으로 넣기 어려움
- 설계 결정: 진행 현황 테이블에는 EXECUTE 요약 1행 + 사용자확인 1행만 두고, 상세 ACT 추적은 별도 "ACT 목록 테이블 SSOT"로 분리
- 하네스 §3의 "산출물이 없는 단계는 산출물 행 생략" 원칙과 일치

### 5-3. SPEC/DESIGN의 QA Gate 없는 State Gate 구조

- SKILL.md v2.3 기준으로 이미 "QA Gate 없는 Phase는 State Gate 단독 구조"로 설계됨
- 진행 현황 행 구성 시 QA Gate 행 없이 작업 → 산출물 생성 → PM Gate → State Gate → 사용자 확인 순서 적용
- interactive 하네스의 Gate 순서 "QA Gate → Artifact Gate → State Gate → PM Gate"와 차이가 있음을 명확히 설명 필요

### 5-4. REVIEW 단계 Gate 구조

- REVIEW는 PM 직접 수행 (워커 디스패치 없음)
- 진행 현황 행: 작업 / TEST-SCENARIOS.md 생성 / State Gate / 사용자 확인
- QA Gate 없음 (PM이 직접 검증 = PM Gate 통합), Artifact Gate 없음 (산출물은 TEST-SCENARIOS.md)

### 5-5. spec-plan-guide.md에 §8 ACT 분해 섹션 존재 여부

- 현재 spec-plan-guide.md는 7섹션 표준 구조(§1~§7)로 설계됨
- ACT 분해는 SPEC-PLAN.md 산출물에 포함되지만 spec-plan-guide.md 자체에는 별도 섹션 없을 수 있음
- 실제 파일 확인 후 적합한 위치에 금지 원칙 추가 필요 (execute-loop-guide.md 참조 문구 + 금지 원칙)
