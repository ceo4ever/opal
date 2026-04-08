# DONE: opds/opd TEST-SCENARIO 흐름 재설계

> 완료일: 2026-04-08

## 완료 요약

opds(opal-pilot-dev-short)와 opd(opal-pilot-dev)의 TEST-SCENARIO 흐름을 재설계했다.

## 변경된 파일

- `opal/skills/opal-pilot-dev-short/SKILL.md` → v2.5
- `opal/skills/opal-pilot-dev/SKILL.md` → v2.4

## 주요 변경 내용

### 1. TEST-SCENARIO를 Gates 앞으로 이동

**변경 전**: PLAN → Gates → TEST-SCENARIO → 사용자 승인
**변경 후**: PLAN → TEST-SCENARIO → State Gate → QA Gate(PLAN+TEST-SCENARIO 동시) → ... → 사용자 승인

### 2. TEST 단계 공식화

**변경 전**: EXECUTE 완료 후 서브스텝으로 묻힘
**변경 후**: 독립 단계 (opds: STEP 4, opd: STEP 5), STATE.md에 명시적 행

### 3. TEST 루핑 구현

FAIL 시: op-dev-test-agent → op-dev-execute(fix 모드) → 재TEST (최대 3회)
3회 초과 시 사용자 에스컬레이션

### 4. STATE.md 템플릿 갱신

| 스킬 | 단계 목록 | 행 수 |
|------|----------|------|
| opds | TASK / PLAN / TEST-SCENARIO / EXECUTE / TEST | 21행 |
| opd | TASK / ANALYSIS / PLAN / TEST-SCENARIO / EXECUTE / TEST | 29행 |
