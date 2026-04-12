# PLAN: Harness Gate 상태 관리 개선

## 1. 변경 목표

| 목표 | 해결 문제 |
|------|----------|
| `완료 산출물` → `진행 현황` 통합 테이블 | Gate별 상태가 테이블에 기록되지 않아 추적 불가 |
| State Gate를 각 Gate 직후에 내재화 | State Gate 1개로는 중간 Gate 묶어서 처리해도 통과됨 |
| Gate Fail 공통 처리 섹션 신설 | Fail 처리가 3개 문서에 산발적으로 정의됨 |

---

## 2. 설계 결정

### 진행 현황 테이블

컬럼 방식 대신 **행 기반 수행 순서 테이블**로 설계. 모든 Gate(State Gate 포함)가 행으로 노출되어 숨김/함축 없이 순서대로 처리하는 하네스 도구로 동작.

```markdown
## 진행 현황

| # | 단계 | 항목 | 상태 | 시점 |
|---|------|------|------|------|
| 1 | TASK | 작업 | ✅ | HH:mm |
| 2 | TASK | 사용자 확인 | ✅ | HH:mm |
| 3 | PLAN | 작업 | ⬜ | - |
| 4 | PLAN | QA Gate | ⬜ | - |
| 5 | PLAN | State Gate | ⬜ | - |
| 6 | PLAN | Artifact Gate | ⬜ | - |
| 7 | PLAN | State Gate | ⬜ | - |
| 8 | PLAN | PM Gate | ⬜ | - |
| 9 | PLAN | State Gate | ⬜ | - |
| 10 | PLAN | 사용자 확인 | ⬜ | - |
| 11 | EXECUTE | 작업 | ⬜ | - |
| ... | | | | |
```

**상태값**: `⬜` 대기 / `🔄` 진행 중 / `✅` 완료 / `❌` 실패 / `-` 해당 없음

**수행 규칙 (하네스에 명시)**:
- 현재 행이 ✅가 아니면 다음 행으로 진행 불가
- PM/워커는 이 테이블을 위에서 아래로 순서대로 처리한다
- State Gate 행 = 직전 Gate 항목의 진행 현황 테이블 갱신 확인 및 기록
- Gate 없는 단계(TASK 등)는 해당 Gate 행 전체 생략

**갱신 책임**: 작업 행은 워커(1차)+PM(확인). Gate/State Gate 행은 PM이 각 Gate 완료 즉시 갱신.

**기존 `완료 산출물` 테이블 제거**: 이 테이블이 대체. 기존 `상태:` 필드는 전체 흐름 요약으로 유지.

### State Gate 내재화 (핵심 변경)

현재 State Gate가 PM Gate 진입 전 1개뿐이라 "어차피 최종 상태가 같으니까" 판단이 개입할 여지가 있음.

**변경 전:**
```
QA Gate → Artifact Gate → State Gate(1개) → PM Gate
```

**변경 후:**
```
QA Gate → [State Gate: QA ✅ 확인] → Artifact Gate → [State Gate: Artifact ✅ 확인] → PM Gate → [State Gate: PM ✅ 확인]
```

각 Gate 섹션(§2, §2.5, §3) 끝에 State Gate를 내재화. 기존 §3 "State Gate 확인" 서브섹션은 각 Gate 내부로 통합되어 제거.

**오케스트레이터 SKILL.md 수정**: 현재 `→ State Gate` 가 PM Gate 전 1개로 표기되어 있음. 하네스에서 내재화되더라도, PM이 SKILL.md를 읽을 때 흐름이 명확히 보여야 하므로 각 Gate 직후로 재배치.

### Gate Fail 공통 처리

`opal-harness-interactive.md §5`로 신설. 각 Gate에서 "Fail 시 §5 참조" 1줄로 연결.

PM 즉시 처리 / 재소환·재지시 / 사용자 에스컬레이션 3단계 구조. 앞 Gate가 ❌인 상태에서 후속 Gate 차단 원칙 포함.

---

## 3. 실행 체크리스트

### opal-harness.md

- [x] §3 이벤트 테이블에 `Artifact Gate 통과` 행 추가
- [x] §3 STATE.md 공통 템플릿 — `완료 산출물` → `진행 현황` 통합 테이블로 교체 (상태값 범례 + 도메인별 예시 주석 포함)

### opal-harness-interactive.md

- [x] §2 QA Gate — 완료 후 State Gate 내재화 (QA 컬럼 ✅ 미갱신 시 PM 즉시 갱신 → 재확인) + Fail 시 §5 참조
- [x] §2.5 Artifact Gate — 완료 후 State Gate 내재화 (Artifact 컬럼 ✅ 미갱신 시 PM 즉시 갱신 → 재확인) + Fail 시 §5 참조
- [x] §3 PM Gate — 완료 후 State Gate 내재화 (PM 컬럼 ✅ 미갱신 시 PM 즉시 갱신 → 재확인) + Fail 시 §5 참조
- [x] §3 기존 "State Gate 확인" 서브섹션 제거 (각 Gate 내부 통합으로 중복)
- [x] §5 Gate Fail 공통 처리 섹션 신설

### 오케스트레이터 SKILL.md (6개)

`→ State Gate` 위치를 PM Gate 전(현재) → 각 Gate 직후로 재배치.
대상: opds / opd / opp / opdw / opsdd / opwt

- [x] opal-pilot-dev-short/SKILL.md
- [x] opal-pilot-dev/SKILL.md
- [x] opal-pilot-project/SKILL.md
- [x] opal-pilot-dev-wireframe/SKILL.md
- [x] opal-pilot-sdd/SKILL.md
- [x] opal-pilot-write-tech/SKILL.md

---

## 4. QA 체크리스트

- [x] 진행 현황 테이블이 행 기반으로 모든 Gate(State Gate 포함)를 노출하는가
- [x] State Gate가 QA / Artifact / PM 각 Gate 직후에 명시되어 있는가
- [x] Gate Fail §5에서 QA / Artifact / PM / State 4개 유형이 모두 커버되는가
- [x] 앞 Gate ❌ 상태에서 후속 차단 원칙이 명확한가
- [x] 6개 SKILL.md에서 State Gate 위치가 올바르게 재배치되었는가
- [x] 기존 `완료 산출물` 잔여 참조가 양쪽 하네스 파일에 남아있지 않은가
- [x] 변경이력이 모든 수정 파일에 추가되었는가
