# TASK: opds/opd TEST-SCENARIO 흐름 재설계

> 적용 스킬: opal-pilot-project (opp)
> 태스크 폴더: tasks/100-opp-dev-skill-test-redesign/

## 배경

현재 opds(opal-pilot-dev-short)와 opd(opal-pilot-dev)의 TEST-SCENARIO 흐름에 두 가지 구조적 문제가 있다.

**문제 1 — QA Gate가 PLAN만 검토 (TEST-SCENARIO 없음)**

현재 흐름:
```
PLAN 작성 → QA/PM Gates → TEST-SCENARIO 작성 → 사용자 승인
```
Gates 시점에 TEST-SCENARIO가 없어, QA Gate는 PLAN만 검토하고 통과함.
TEST-SCENARIO는 QA/PM Gate를 통과하지 않음.

**문제 2 — EXECUTE 후 TEST가 공식 단계 아님**

현재 흐름:
```
EXECUTE → (완료 후) op-dev-test-agent 호출 → PM Gate → DONE
```
TEST가 "완료 후 처리" 서브스텝에 묻혀 있고, STATE.md에도 별도 행이 없음.
또한 테스트 실패 시 재시도(루핑) 메커니즘이 없음.

## 요구사항

- [x] **TEST-SCENARIO를 Gates 앞으로 이동**: PLAN 작성 후 → TEST-SCENARIO 작성 → QA/PM Gates (PLAN + TEST-SCENARIO 함께 검토) → 사용자 승인
- [x] **TEST를 공식 단계로 신설**: EXECUTE 완료 후 TEST 단계를 STATE.md에 명시적 행으로 추가
- [x] **TEST 루핑 구현**: TEST FAIL → op-dev-execute fix → 재TEST 루핑 (하네스 루핑 가드: 최대 3회, 초과 시 에스컬레이션)
- [x] **opds + opd 동시 수정**: 두 스킬 모두 동일 구조로 반영
- [x] **STATE.md 템플릿 갱신**: 두 스킬의 STATE.md 진행 현황 행 업데이트

## 변경 대상 파일

- `opal/skills/opal-pilot-dev-short/SKILL.md` (opds)
- `opal/skills/opal-pilot-dev/SKILL.md` (opd)

## 확정 설계

### 새 PLAN 단계 흐름 (opds 기준)

```
PLAN 디스패치
  ↓
TEST-SCENARIO 디스패치 (PLAN 기반 — 연속)
  ↓
QA Gate → State Gate → Artifact Gate → State Gate → PM Gate → State Gate
  (PLAN + TEST-SCENARIO 둘 다 검토)
  ↓
사용자 승인 → EXECUTE
```

### 새 TEST 단계 흐름

```
EXECUTE 완료
  ↓
TEST 단계 진입
  op-dev-test-agent → TEST-SCENARIO 실행 + 결과 기록 + PASS/FAIL 판정
    ↓ PASS
  QA Gate → State Gate → PM Gate → State Gate → DONE
    ↓ FAIL
  op-dev-execute (fix 모드) — 오류 수정
    ↓
  op-dev-test-agent → 재검증
    ↓ (루핑, 최대 3회)
  초과 시 사용자 에스컬레이션
```

### STATE.md 단계 목록 변경

| 스킬 | 기존 | 변경 |
|------|------|------|
| opds | TASK / PLAN+TEST-SCENARIO / EXECUTE | TASK / PLAN / TEST-SCENARIO / EXECUTE / TEST |
| opd | TASK / ANALYSIS / PLAN+TEST-SCENARIO / EXECUTE | TASK / ANALYSIS / PLAN / TEST-SCENARIO / EXECUTE / TEST |

## 완료 기준

- [ ] opds SKILL.md: TEST-SCENARIO가 Gates 앞, TEST 단계 + 루핑 로직 명시
- [ ] opd SKILL.md: 동일 구조 반영
- [ ] 두 스킬의 STATE.md 진행 현황 템플릿에 TEST-SCENARIO, TEST 행 추가
- [ ] 루핑 가드: 최대 3회, 초과 시 에스컬레이션 명시
- [ ] 변경이력 업데이트
