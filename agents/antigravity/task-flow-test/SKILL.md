---
name: task-flow-test
description: |
  **task-flow 테스트 실행 스킬**. EXECUTE 단계 완료 후 모든 모드에서 호출되어, TEST-SCENARIO.md를 입력으로 받아 도구 결정 + 실행 + 결과 기록 + 판정을 수행합니다.
  task-flow-qa가 문서를 리뷰하는 스킬이라면, task-flow-test는 코드를 실행하여 검증하는 스킬입니다.
---

# task-flow-test 스킬

> 이 스킬은 테스트 실행을 위해 코드를 실행할 수 있습니다.

## 목적

EXECUTE 단계 완료 후, TEST-SCENARIO.md를 입력으로 받아 **실제 실행하여 검증**하는 스킬:
1. TEST-SCENARIO.md의 시나리오(S-1~S-N)에 대해 **도구를 결정**하고 **실행**
2. 기존 테스트 스위트를 돌려 **회귀 검증**
3. 린트, 타입 체크, 포맷터로 **코드 품질 검사**
4. 하드코딩 시크릿 등 **보안 검사**
5. 결과를 **TEST-SCENARIO.md에 인라인으로 기록** + 판정

### task-flow-qa와의 역할 분담

| 구분 | task-flow-qa | task-flow-test |
|------|-------------|---------------|
| 대상 | 마크다운 산출물 (RESEARCH, PLAN) | 소스 코드 + 실행 환경 |
| 방법 | 체크리스트 기반 정적 리뷰 | 테스트 실행 기반 동적 검증 |
| 시점 | RESEARCH, PLAN 완료 후 | EXECUTE 완료 후 |
| 산출물 | QA-RESEARCH.md, QA-PLAN.md | TEST-SCENARIO.md (인라인 갱신) |
| 코드 실행 | 불가 (읽기 전용) | **가능** (테스트 실행 필요) |

---

## 호출 시점

```
[EXECUTE 단계 완료] → task-flow-test 호출 → TEST-SCENARIO.md 결과 채움 + 판정
                   → 오케스트레이터: 테스트 결과 포함 완료 보고
                   → DONE.md 생성 → 사용자 보고
```

**모든 모드**(Full 단순, Full 복잡, Short Task)에서 호출된다.

---

## 입력

| 입력 | 설명 |
|------|------|
| `task_path` | 태스크 폴더 경로 (예: `tasks/001-user-auth-implementation/`) |
| `mode` | 태스크 모드 (`full-simple` / `full-complex` / `short`) |
| `scenario_path` | TEST-SCENARIO.md 경로 (task-flow-agent가 사전 작성한 시나리오) |
| `changed_files` | 변경된 파일 목록 (EXECUTE 단계에서 수집) |

---

## 실행 프로세스

### Step 1: TEST-SCENARIO.md 읽기 + 테스트 환경 확인

1. `scenario_path`의 TEST-SCENARIO.md를 읽어 시나리오 목록(S-1~S-N)을 파악
2. 테스트 도구 설치 여부 확인 (프로젝트 설정 파일 기반)
3. 테스트 실행 가능 상태인지 검증 (의존성 설치, 빌드 성공 등)
4. 환경 문제 발견 시 -> TEST-SCENARIO.md 해당 항목에 환경 이슈로 기록

### Step 2: 시나리오 실행 (S-1~S-N)

TEST-SCENARIO.md의 각 시나리오에 대해:
1. **도구 결정**: 시나리오의 대상/조건을 분석하여 적합한 테스트 도구 선택
2. **실행 명령 구성**: 도구에 맞는 실행 명령 작성
3. **실행**: 명령 실행
4. **결과 기록**: Pass / Fail / Skip + 상세 정보
5. TEST-SCENARIO.md의 해당 시나리오에 도구/실행 명령/결과/상세를 채움

### Step 3: 회귀 테스트

기존 테스트 스위트 실행:
1. 프로젝트의 기존 테스트 전체 실행
2. 실패 항목 식별
3. 원인 분류: 이번 변경으로 인한 실패 / 기존 실패
4. TEST-SCENARIO.md 회귀 테스트 섹션에 결과 기록

### Step 4: 코드 품질 검사

변경 파일 대상으로:
1. 린트 실행 (eslint, flake8 등)
2. 타입 체크 (tsc, mypy 등)
3. 포맷터 확인 (prettier, black 등)
4. TEST-SCENARIO.md 코드 품질 섹션에 결과 기록

### Step 5: 보안 검사

1. 하드코딩 시크릿 스캔 -- 변경 파일에서 `password`, `secret`, `token`, `api_key` 패턴 검색
2. .gitignore 확인 -- `.env`, 인증 파일이 포함되어 있는지
3. 민감 파일 노출 여부 -- 변경 파일 중 시크릿 파일이 없는지
4. TEST-SCENARIO.md 보안 섹션에 결과 기록

### Step 6: 판정 + TEST-SCENARIO.md 갱신

1. 모든 테스트 결과를 종합하여 판정 결정
2. TEST-SCENARIO.md의 판정 섹션에 결과 기록
3. TEST-SCENARIO.md의 상태를 "실행 완료"로 갱신
4. 오케스트레이터에 결과 반환

---

## 문서만 변경한 태스크

`changed_files`가 모두 `.md` 파일이면:
- Step 4(코드 품질) + Step 5(보안 검사)만 실행
- Step 2(시나리오 실행) + Step 3(회귀 테스트) 스킵
- TEST-SCENARIO.md 시나리오 결과에 "문서 전용 변경 -- 코드 테스트 스킵" 명시
- 판정에 "문서 전용 변경" 사유 기록

---

## 출력

### 산출물

기존 TEST-SCENARIO.md를 **인라인 갱신**한다 (별도 파일을 생성하지 않음).

```
tasks/{NNN}-{태스크명}/TEST-SCENARIO.md  (갱신)
```

### 갱신 내용

task-flow-agent가 비워둔 필드를 채운다:
- 각 시나리오(S-1~S-N)의 도구/실행 명령/결과/상세
- 코드 품질 섹션의 도구/결과/상세
- 보안 섹션의 결과/상세
- 회귀 테스트 섹션의 테스트 스위트/결과/상세
- 판정 섹션의 최종 판정 + 근거
- 상태를 "작성 완료" -> "실행 완료"로 갱신

---

## 판정 기준

| 판정 | 조건 |
|------|------|
| **All Pass** | 모든 시나리오 Pass, 회귀 Pass, 품질/보안 이슈 없음 |
| **Partial Fail** | 일부 시나리오 Fail 또는 경미한 품질 이슈 (수정 후 재실행 권장) |
| **Critical Fail** | 핵심 시나리오 Fail 또는 보안 이슈 (반드시 수정 필요) |

---

## 반환 형식

```
- artifact_path: TEST-SCENARIO.md 경로
- summary: 테스트 결과 요약 (시나리오 N/M Pass, 회귀 Pass/Fail, 품질 Pass/Fail, 판정)
- status: success / blocked
- verdict: All Pass / Partial Fail / Critical Fail
```

---

## 호출 예시

EXECUTE 완료 후:

```
1. EXECUTE 단계 완료 (모든 Step 완료)
2. task-flow-test 호출:
   - task_path: tasks/003-payment-integration/
   - mode: short
   - scenario_path: tasks/003-payment-integration/TEST-SCENARIO.md
   - changed_files: [src/payment.ts, src/api/routes.ts, ...]
3. Test 스킬이 Step 1~6 순서로 실행
4. TEST-SCENARIO.md에 결과 채움 + 판정
5. 오케스트레이터에 반환:

[TEST 결과]
- 시나리오: 5/5 Pass
- 회귀 테스트: 24/24 Pass
- 코드 품질: 린트 Pass, 타입 체크 Pass
- 보안: 시크릿 스캔 Pass
- 판정: All Pass
```
