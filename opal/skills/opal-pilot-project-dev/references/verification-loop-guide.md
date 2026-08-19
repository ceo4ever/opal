# 자동 검증 루핑 가이드 (Verification Loop Guide)

> oppd Phase 3 EXECUTE 스텝의 자동 검증 루핑 전략.
> 오케스트레이터(oppd)가 워커 완료 후 즉시 검증하고, 실패 시 자동으로 재시도 루프를 돌린다.

---

## 1. 개요

### 목적

EXECUTE 스텝마다 즉시 검증하여 오류를 조기 차단한다. 워커가 코드를 작성/수정한 직후 자동 검증을 수행하고, 실패 시 오케스트레이터가 워커에게 수정을 지시하는 루프를 돌린다. 사용자 개입 없이 기계적으로 해결 가능한 오류는 자동 수정하고, 설계적 판단이 필요한 오류는 즉시 에스컬레이션한다.

### 적용 범위

- **대상**: oppd Phase 3 — 태스크별 EXECUTE 액션 실행 시
- **주체**: 오케스트레이터(oppd)가 루프를 관리하고, 워커(opal-task-agent)가 수정을 수행한다
- **전제**: WBS.md 각 태스크의 "완료 기준"에 검증 명령(lint, build, test)이 명시되어 있어야 한다

### 루프 흐름 요약

```
워커 EXECUTE Step 완료
  → lint/format 검증
    → FAIL → 워커에게 수정 지시 → 재검증 (반복)
    → PASS ↓
  → build/type 검증
    → FAIL → 워커에게 수정 지시 → 재검증 (최대 2회)
    → PASS ↓
  → unit/integration test 검증
    → FAIL → 워커에게 수정 지시 → 재검증 (최대 3회)
    → PASS ↓
  → E2E test 검증 (해당 시)
    → FAIL → 1회 재시도 (flaky 대응) → 2회 연속 FAIL → 에스컬레이션
    → PASS ↓
  → QA Gate (기존 QA 에이전트)
    → 설계 수준 실패 → scope별 분기
        → scope: action → 에이전트 자율 재설계 루프(PLAN 재진입, harness §1 상한)
        → scope: wbs   → PM 에스컬레이션 (WBS 2단 기준)
        → scope: trd   → 즉시 사용자 에스컬레이션 (0회)
    → PASS → 다음 Step 또는 완료 보고
```

---

## 2. Layered Verification 모델

검증은 4개 계층으로 구성되며, **하위 계층을 통과해야 상위 계층으로 진행**한다. 하위 계층에서 실패하면 상위 계층을 실행하지 않는다 — 비용과 시간을 절약하고, 원인 파악을 용이하게 한다.

### 계층 정의

| 계층 | 검증 대상 | 실행 명령 (예시) | 소요 시간 | 자동 수정 가능성 |
|------|----------|----------------|----------|----------------|
| L1: lint/format | 코드 스타일, 미사용 변수, import 정리 | `npm run lint:fix`, `npm run format:check` | 수 초 | 매우 높음 |
| L2: build/type | 컴파일 오류, 타입 불일치 | `npm run build`, `npx tsc --noEmit` | 수 초~수십 초 | 높음 |
| L3a: unit/integration | 컴포넌트 단위, 함수, API 통합 테스트 | `npm test -- --run` | 수십 초 | 중간 |
| L3b: E2E | 브라우저 기반 시나리오 테스트 | `npm run test:e2e`, `npx playwright test` | 수 분 | 낮음 (flaky, 느림) |
| L4: QA | 설계 원칙, 아키텍처 패턴, 보안 | QA 에이전트 호출 | 수 분 | scope별 분기 (action→재PLAN / wbs→PM / trd→0회·즉시) |

> **[MUST] watch 모드 금지**: L3a/L3b 테스트는 watch 모드를 금지하고 단발(non-watch) 실행만 허용한다 — 자동 검증 루프가 무한 대기에 빠지지 않도록 한다. (러너별 단발 옵션 예: Vitest `-- --run`, Jest `--ci`/`--watchAll=false`)

### 3축 명명 매핑 (혼동 금지)

OPAL에는 "L번호"를 쓰는 **세 개의 별도 차원(축)**이 존재한다. **동일 "L번호"가 축마다 다른 의미이므로 혼동을 금지**한다. 아래 표가 3축의 유일한 매핑 정의(SSOT)다.

| 축 | 명명 | 정의 |
|----|------|------|
| 검증 계층 (verification-loop, 이 문서) | L1 / L2 / L3a / L3b / L4 | lint / build / unit / E2E / QA — 실행 비용(빠름→느림) 순서 |
| 검증 깊이 (test-scenario-guide) | L1 / L2 / L3 | 기능단위 / 프로세스통합 / 사용자협업 |
| 파이프라인 단계 (캡틴 2단계) | 단위 / 통합 | 단위 = EXECUTE(L1+L2 계층 + L1 깊이) / 통합 = TEST(L3b 계층 + L2·L3 깊이) |

> **[주의] L번호 ≠ 단위·통합**: 이 문서의 L1~L4(검증 계층)는 test-scenario-guide의 L1~L3(검증 깊이)와도, 파이프라인 단계(단위/통합)와도 **별개 축**이다. 워커는 어느 축의 L번호인지 출처(문서)로 식별한다.

**파이프라인 단계 → 기존 L계층 배선** (새 명명 강제 도입 없음 — 기존 L1~L4 명칭 유지):

- **단위 = EXECUTE 묶음**: L1(lint) + L2(build/type) + L3a(unit/integration) — 구현 워커 자가검증.
- **통합 = TEST 묶음**: L3b(E2E) + L4(QA) — opal-test-agent 및 [SUPERVISOR] 수행.

> 위 배선은 기존 §2 L계층 정의를 **재라벨링하지 않고** 파이프라인 단계와 연결하는 주석이다. L3a/L3b 명칭은 그대로 유지한다.

### 실행 순서 원칙

1. **L1 → L2 → L3a → L3b → L4** 순서를 반드시 따른다
2. 현재 계층이 PASS가 아니면 다음 계층으로 넘어가지 않는다
3. 자동 수정 후 **현재 계층부터** 재검증한다 (이전 계층은 재검증하지 않음 — 단, 회귀 방지 가드 예외)
4. L3b(E2E)는 WBS.md에 E2E 검증 명령이 명시된 액션에만 실행한다. 미명시 시 SKIP
5. L4(QA)는 기존 QA Gate 프로세스(opal-harness.md)를 그대로 따른다

### 검증 명령 결정

검증 명령은 WBS.md 태스크의 "완료 기준" 또는 프로젝트의 `package.json` / 설정 파일에서 결정한다:

1. WBS.md 태스크에 검증 명령이 명시되어 있으면 그것을 사용한다
2. 명시되지 않으면 프로젝트 루트의 `package.json` scripts에서 추론한다:
   - lint: `lint`, `lint:check` 스크립트
   - build: `build`, `typecheck`, `tsc` 스크립트
   - test (L3a): `test`, `test:unit`, `test:api`, `test:integration` 스크립트
   - E2E (L3b): `test:e2e`, `e2e`, `playwright` 스크립트
3. 추론 불가 시 해당 계층을 건너뛴다 (SKIP으로 로그 기록)
4. L3b(E2E)는 WBS.md에 E2E 검증 명령이 명시된 액션에만 실행. 미명시 시 SKIP

---

## 3. 실패 유형별 루핑 전략

### 3-0. VERIFY 실패 triage (1차 분류)

VERIFY 실패가 발생하면 오케스트레이터가 아래 3분류 기준으로 실패 성격을 먼저 판별한다.

| 실패 성격 | 신호 | 라우팅 |
|----------|------|--------|
| 구현 수준 | PLAN 계약 안에서 발생·로컬 수정 가능 (로직·타입·경계조건·오타·assertion 값) | EXECUTE 재작업 (fix 루프, 기존 한도 L2:2/L3a:3/L3b:1) |
| 설계 수준 | PLAN 가정/계약 자체를 부정 (인터페이스 불일치·컴포넌트/필드 누락·순환의존·요구사항↔설계 갭) | scope 3계층 라우팅 |
| 회귀(regression) | 이전 통과 테스트가 수정 후 실패 | 즉시 중단 (재PLAN/재fix 안 함) |

**적용 순서**: 실패 발생 시 이 표로 성격을 먼저 판별 → "구현 수준"이면 §3-1~§3-4 계층별 전략(fix 루프)으로 라우팅 → "설계 수준"이면 §3-5 scope 3계층 라우팅 → "회귀"이면 §4 회귀 방지 가드로 즉시 중단.

> 기존 §3-1~§3-4 계층별 실패 전략(lint/build/test/E2E)은 **"구현 수준"** 실패의 처리 경로로 재사용된다.

---

### 3-1. lint/format 실패

**재시도 한도**: 제한 없음 (기계적 수정이므로)

**감지**: 검증 명령 실행 결과를 파싱하여 오류 목록을 추출한다.

**오류 파싱 형식**:
```
파일경로:라인:컬럼 — 규칙명 (오류 메시지)
```

**자동 수정 흐름**:

1. 워커가 EXECUTE Step 완료 → 오케스트레이터가 검증 명령 실행
2. 결과에서 오류 목록 추출
3. 오케스트레이터 → 워커에게 자동 수정 디스패치:

```
[lint 자동 수정 지시]

lint 오류 {N}건을 수정하라:
{오류 목록 — 파일:라인, 규칙명, 메시지를 나열}

수정 후 `{lint 검증 명령}`으로 재검증하라.
```

4. 워커 수정 완료 → 오케스트레이터가 재검증
5. PASS → 다음 계층(L2: build)으로 진행

**예시 — ESLint 오류 자동 수정**:

```
1. 워커가 EXECUTE Step 완료 → 검증 명령 실행: `npm run lint`
2. 결과: FAIL — 3 errors (no-unused-vars: 2, prefer-const: 1)
3. 오케스트레이터 → 워커에게 자동 수정 지시:
   "lint 오류 3건 수정하라:
    - src/auth/service.ts:15 — no-unused-vars (변수 'temp' 미사용)
    - src/auth/service.ts:42 — no-unused-vars (import 'Logger' 미사용)
    - src/api/handler.ts:8 — prefer-const ('config'를 const로 변경)"
4. 워커 수정 완료 → 재검증: `npm run lint` → PASS
5. 다음 계층(build)으로 진행
```

### 3-2. build/type 실패

**재시도 한도**: 최대 2회 — 초과 시 사용자 에스컬레이션

**감지**: 빌드 로그 또는 타입 체커 출력에서 오류를 파싱한다.

**오류 파싱 형식**:
```
파일경로(라인,컬럼): error 코드: 메시지
```

**자동 수정 흐름**:

1. 검증 명령 실행 (`npm run build` 또는 `npx tsc --noEmit`)
2. 오류 컨텍스트 추출: 파일, 라인, 에러 코드, 메시지
3. 오케스트레이터 → 워커에게 수정 디스패치:

```
[build/type 자동 수정 지시 — 시도 {N}/2]

빌드/타입 오류 {M}건을 수정하라:
{오류 목록 — 파일(라인,컬럼): 에러 코드, 메시지를 나열}

참고 파일:
{오류 관련 파일 경로 목록}

수정 후 `{build 검증 명령}`으로 재검증하라.
```

4. 워커 수정 완료 → 오케스트레이터가 재검증
5. PASS → 다음 계층(L3: test)으로 진행
6. 2회 초과 시 → 에스컬레이션 (섹션 5 참조)

**예시 — TypeScript 빌드 오류**:

```
검증 루프: build 시도 1/2 — FAIL

빌드 오류:
  - src/auth/service.ts(23,5): error TS2345: Argument of type 'string' is
    not assignable to parameter of type 'TokenPayload'.
  - src/auth/service.ts(48,12): error TS2339: Property 'expiresIn' does not
    exist on type 'TokenConfig'.

참고 파일:
  - src/auth/types.ts (TokenPayload, TokenConfig 타입 정의)

지시: 위 타입 오류를 수정하라. types.ts의 타입 정의를 확인하고 service.ts를 맞춰라.
      수정 후 `npx tsc --noEmit`으로 재검증하라.
```

### 3-3. L3a: unit/integration test 실패

**재시도 한도**: 최대 3회 — 초과 시 사용자 에스컬레이션

**감지**: 테스트 러너 출력에서 실패 테스트명과 assertion 메시지를 파싱한다.

**컨텍스트 전달 형식**:

테스트 실패는 원인 파악에 더 많은 컨텍스트가 필요하므로, 다음 정보를 모두 워커에게 전달한다:

```
[test 자동 수정 지시 — 시도 {N}/3]

검증 루프: test 시도 {N}/3 — FAIL

실패 테스트:
  - {테스트 파일 경로} > {테스트 스위트명} > {테스트명}
    {에러 타입}: {메시지}
    at {파일}:{라인}:{컬럼}

관련 소스:
  - {실패 원인으로 추정되는 소스 파일} ({관련 함수/클래스명})
  - {관련 타입 정의 파일} ({관련 타입명})

지시: 위 실패 테스트를 분석하고 {소스 파일}의 {함수명} 로직을 수정하라.
      수정 후 `{test 검증 명령} -- --run <대상 파일/glob>` 으로 해당 테스트만 먼저 확인하라.
```

**예시 — Jest 테스트 실패**:

```
검증 루프: test 시도 1/3 — FAIL

실패 테스트:
  - src/__tests__/auth.test.ts > AuthService > should validate token
    AssertionError: Expected 'valid' but received 'expired'
    at src/__tests__/auth.test.ts:45:12

관련 소스:
  - src/auth/service.ts (validateToken 메서드)
  - src/auth/types.ts (TokenStatus 타입)

지시: 위 실패 테스트를 분석하고 src/auth/service.ts의 validateToken 로직을 수정하라.
      수정 후 `npm test -- --run src/**/auth*` 로 해당 테스트만 먼저 확인하라.
```

**관련 소스 결정 방법**:

1. 실패 테스트의 import 문을 분석하여 테스트 대상 모듈을 식별한다
2. 에러 스택 트레이스에서 소스 파일 경로를 추출한다
3. 워커가 현재 Step에서 수정한 파일 목록과 교차 확인한다

### 3-4. L3b: E2E test 실패

**재시도 한도**: 최대 1회 — 2회 연속 실패 시 사용자 에스컬레이션

E2E 테스트는 실제 브라우저를 띄워 시나리오를 실행하므로, unit/integration과 다른 전략이 필요하다.

**L3a와의 차이**:

| 항목 | L3a (unit/integration) | L3b (E2E) |
|------|----------------------|-----------|
| 실행 환경 | Node (브라우저 없음) | 실제 브라우저 (Playwright, Cypress) |
| 소요 시간 | 수십 초 | 수 분 |
| 결정성 | 높음 (결과 재현 가능) | 낮음 (타이밍, 네트워크 이슈로 flaky) |
| 자동 수정 가능성 | 중간 | 낮음 (실패 원인 특정 어려움) |
| 재시도 한도 | 3회 | 1회 |

**적용 조건**: WBS.md 액션의 검증 명령에 E2E 명령이 명시된 경우에만 실행한다. E2E 검증 명령이 없으면 L3b를 SKIP하고 L4로 진행한다.

**도메인별 E2E 도구 예시**:

| 도메인 | 도구 | 검증 명령 예시 |
|--------|------|--------------|
| FE (React/Next.js) | Playwright | `npx playwright test --project=auth` |
| FE (React/Next.js) | Cypress | `npx cypress run --spec "cypress/e2e/auth/**"` |
| 풀스택 | Playwright | `npm run test:e2e` |

**자동 수정 흐름**:

1. L3a 통과 후, E2E 검증 명령을 실행한다
2. FAIL 시 **1회만 재시도** — flaky 테스트 대응
   - 재시도 전 워커에게 수정 지시하지 않음 (동일 코드로 재실행)
3. 2회 연속 FAIL → 에스컬레이션
   - E2E 실패는 FE/BE 어느 쪽 원인인지 특정이 어려우므로 사람 판단이 효율적

**에스컬레이션 형식**:

```
⚠️ [검증 루프 에스컬레이션] E2E test 실패

액션: {액션명}
검증 유형: E2E test
시도: 2/2 — 2회 연속 FAIL (flaky 아님으로 판정)

실패 시나리오:
  - {테스트 파일} > {시나리오명}
    {에러 메시지 또는 스크린샷 경로}

관련 액션:
  - {현재 액션이 의존하는 다른 액션 목록}

E2E 실패는 원인 특정이 어렵습니다. 다음 중 선택해주세요:
1. 실패 로그 분석 후 워커에게 수정 지시
2. 해당 E2E 테스트를 스킵하고 진행
3. 관련 액션을 함께 재검토
```

**병렬 그룹에서의 E2E 전략**:

병렬 그룹의 개별 액션마다 E2E를 실행하면 비효율적이다. 대안:
- **개별 액션**: L3a(unit/integration)까지만 자동 루프 실행
- **병렬 그룹 머지 후**: 통합 시점에 E2E 일괄 실행
- WBS.md에서 E2E 검증 시점을 `개별` 또는 `머지 후`로 지정 가능

### 3-5. 설계 수준 실패

QA 에이전트 또는 VERIFY 루프에서 **설계 수준** 실패(PLAN 가정/계약 자체를 부정하는 이슈)가 감지되면, `failure_context.scope`에 따라 아래 3계층으로 라우팅한다.

**감지**: QA 에이전트의 판정 결과에서 `Critical Fail` 또는 설계/아키텍처 관련 피드백, 혹은 §3-0 triage 판별에서 "설계 수준"으로 분류된 실패.

#### scope별 분기

| scope | 의미 | 처리 | 재시도 한도 |
|-------|------|------|------------|
| `action` | 액션-로컬 설계 결함 (PLAN.md 범위 내 재설계로 해결 가능) | 에이전트 자율 **재설계 루프(PLAN 재진입)** — 상한은 `opal/core/references/opal-harness.md` §1 'PLAN 재진입' 행 참조 (수치 복제 금지) | harness §1 참조 |
| `wbs` | WBS scope·인터페이스 영향 (액션 경계를 벗어나는 설계 결함) | PM 에스컬레이션 (WBS 2단 기준) | PM 자율 처리 |
| `trd` | TRD/PRD 변경 필요 (요구사항·아키텍처 계약 수준) | **즉시 사용자 에스컬레이션 (0회)** | 0회 즉시 |

> [MUST] **"0회 즉시 에스컬레이션"은 `scope: trd`에만 적용**된다. `scope: action`은 harness §1 상한 내 에이전트 자율 재설계가 허용되며, `scope: wbs`는 PM이 WBS 2단 기준으로 처리한다.

**에스컬레이션 형식**: 섹션 5 참조.

---

## 4. 회귀 방지 가드

자동 수정은 새로운 오류를 수정하면서 기존 통과 코드를 깨뜨릴 수 있다. 이를 방지하기 위해 **회귀 방지 가드**를 운영한다.

### 규칙

1. **자동 수정 후 전체 테스트 스위트 재실행**: L3(test) 계층의 자동 수정이 완료되면, 실패 테스트뿐 아니라 전체 테스트 스위트를 재실행한다
2. **회귀 감지 즉시 중단**: 이전에 통과한 테스트가 새로 실패하면 루프를 즉시 중단한다
3. **에스컬레이션**: 회귀가 감지되면 사용자에게 보고한다 (섹션 5 형식)

### 회귀 감지 흐름

```
자동 수정 완료
  → 해당 테스트 재실행 (빠른 확인)
    → FAIL → 수정 재시도 (한도 내)
    → PASS ↓
  → 전체 테스트 스위트 재실행
    → 이전 통과 테스트 실패 발견 → 회귀!
      → 루프 즉시 중단
      → 에스컬레이션 보고
    → 전체 PASS → 다음 계층 또는 완료
```

### 회귀 판별 기준

- **회귀**: 현재 루프 시작 시점에 통과했던 테스트가 자동 수정 후 실패로 전환
- **비회귀**: 현재 Step에서 새로 추가된 테스트의 실패 (이것은 일반 test 실패로 처리)

### 회귀 발생 시 복원

회귀가 감지되면 오케스트레이터는 다음을 수행한다:

1. 루프 즉시 중단
2. 회귀 내역을 STATE.md 검증 루프 로그에 기록
3. 사용자에게 에스컬레이션 보고 (자동 수정 전 코드로의 복원 여부는 사용자가 결정)

---

## 5. 에스컬레이션 프로토콜

자동 수정이 한도를 초과하거나 회귀가 발생하면, 사용자에게 에스컬레이션한다. **사용자 게이트**를 반드시 유지한다 — 루핑은 agentic이지만 최종 확정은 사용자를 거친다.

### 루프 한도 초과 시 보고 형식

```
⚠️ [검증 루프 에스컬레이션] {검증 유형} 한도 초과

태스크: {태스크명}
검증 유형: {build/type | test}
시도: {N}/{최대 재시도} — 모두 FAIL

마지막 오류:
  {마지막 시도의 오류 메시지 요약}

시도 이력:
  - 시도 1: {오류 요약}
  - 시도 2: {오류 요약}
  ...

워커가 자동으로 해결하지 못했습니다. 다음 중 선택해주세요:
1. 직접 수정 후 재검증
2. 해당 오류를 무시하고 진행
3. 태스크 중단
```

### 회귀 발생 시 보고 형식

```
🚨 [회귀 감지] 자동 수정으로 기존 테스트 실패

태스크: {태스크명}
검증 유형: test (시도 {N}/{최대 재시도})

회귀 테스트:
  - {이전 통과 → 현재 실패 테스트 목록}

원인 수정:
  - {자동 수정이 변경한 파일 목록}

루프를 즉시 중단했습니다. 다음 중 선택해주세요:
1. 자동 수정 전 상태로 복원 후 직접 수정
2. 워커에게 회귀 컨텍스트 포함하여 재시도 지시
3. 태스크 중단
```

### QA 에스컬레이션 보고 형식

```
🏗️ [QA 에스컬레이션] 설계/아키텍처 이슈 감지

태스크: {태스크명}

QA 피드백:
  {QA 에이전트가 보고한 이슈 내용}

자동 수정 불가 사유: 설계 수준의 판단이 필요합니다.
다음 중 선택해주세요:
1. 설계 방향 지시 후 워커에게 재실행
2. 해당 이슈를 별도 태스크로 분리
3. 현재 상태로 진행 (이슈 수용)
```

### STATE.md 검증 루프 로그 기록 형식

에스컬레이션 발생 시 STATE.md의 검증 루프 로그 테이블에 기록한다:

```markdown
## 검증 루프 로그
| # | 태스크 | 검증 유형 | 시도 | 결과 | 오류 요약 | 시점 |
|---|--------|----------|------|------|----------|------|
| 1 | T2     | lint     | 1/∞  | Pass | -        | 14:23 |
| 2 | T2     | build    | 1/2  | Fail | TS2345: Property 'x' missing | 14:24 |
| 3 | T2     | build    | 2/2  | Pass | -        | 14:26 |
| 4 | T2     | test     | 1/3  | Fail | 2/15 failed (auth.test) | 14:28 |
| 5 | T2     | test     | 2/3  | Pass | -        | 14:31 |
```

**컬럼 설명**:
- `#`: 순번 (태스크별 누적)
- `태스크`: WBS.md의 태스크 ID
- `검증 유형`: `lint` / `build` / `test` / `QA`
- `시도`: `{현재 시도}/{최대 시도}` — lint는 `N/∞`, build는 `N/2`, test는 `N/3`, QA는 `1/1`
- `결과`: `Pass` / `Fail` / `Skip` / `Regression` / `Escalation`
- `오류 요약`: 1줄 요약. Pass인 경우 `-`
- `시점`: `HH:mm` (KST)

---

## 6. PM 루프 모니터링

> **[MUST] 파이프라인 행 상태(⬜/🔄/✅) 변경은 `~/.opal/tools/state-tool/run.sh`로만 수행한다. `state.json` 직접 편집 금지 — 현황 조회는 `state-tool show <task-path>`로 한다.**
> — `tasks/134-260501-opp-pipeline-state-tool/TASK.md` F-18 / `PLAN.md` §1.5 M-30 / §3 Step 11 / 094 §3.4.2 표준 문구 A
>
> 예: EXECUTE Step 완료 시:
> ```bash
> ~/.opal/tools/state-tool/run.sh mark <task-path> --task-step <key> --done --as-worker --worker-stage EXECUTE --step <N/M>
> ```
> **[R-10]** oppd 비표준 행 구성 — `gate-pass` 사용 불가. `mark` 개별 호출 필수.

오케스트레이터(oppd)는 PM 역할로서 검증 루프의 진행 상황을 모니터링하고, `state-tool` 호출로 STATE.md 행 상태를 갱신하여 추적 가능한 상태를 유지한다.

### STATE.md 검증 루프 로그 갱신 시점

| 이벤트 | 갱신 내용 |
|--------|----------|
| 검증 계층 시작 | 새 행 추가 — 결과: (실행 중) |
| 검증 결과 확인 | 결과 컬럼 갱신 — Pass / Fail |
| 자동 수정 디스패치 | 오류 요약 기록 |
| 루프 재시도 | 새 행 추가 — 시도 N+1 |
| 에스컬레이션 | 결과: `Escalation`, 오류 요약에 사유 기록 |
| 회귀 감지 | 결과: `Regression`, 회귀 테스트명 기록 |

### 루프 진행률 추적 방법

`## 현재 상태` 섹션은 저널화(094 R-1)로 STATE.md에서 제거되었다. 오케스트레이터는 아래 경로로 전체 진행률을 추적한다(H-12 대체 보관처 — `harness/state.md` §세션 복원 · 094 §3.3.2 (4)):

| 구 필드 | 대체 |
|---------|------|
| `- 진행:` (Step N/M) | `state-tool show --format json` → `data.rows[].note`(`Step N/M 완료`가 기록됨) + `data.current_status` |
| `- 상태:` | `state-tool show --format json` → `data.current_status` |
| `- 검증:` (현재 검증 계층·시도 횟수) | STATE.md 저널의 자유 기재 섹션 `## 검증 루프`(PM 수동 기재) — 파생값이 아니라 도구가 담지 못하는 서술 정보이므로 저널 정의에 부합한다 |

`## 검증 루프` 자유 기재 예시 (STATE.md 저널 안에 PM이 직접 기재):

```markdown
## 검증 루프
- 검증: L2 build 시도 1/2
- 상태: 검증 중
```

- `검증` 항목: 현재 검증 계층과 시도 횟수를 표시
- `상태` 항목: `검증 중` / `수정 중` / `에스컬레이션` 중 하나
- 두 항목의 이력(과거 시도)은 §5 "STATE.md 검증 루프 로그" 표(`## 검증 루프 로그`)에 누적 기록한다

### 세션 복원 시 루프 상태 재개

새 세션에서 검증 루프의 중단 지점을 파악할 때는 아래 순서로 상태를 복원한다(`harness/state.md` §세션 복원 · 094 §3.3.2 (4)):

```
1. `~/.opal/tools/state-tool/run.sh show <task-path> --format json` 을 호출해
   현재 단계·행 상태·current_status·next_action을 파악한다 (SSOT: state.json).
2. `tasks/{NNN}-{name}/STATE.md`(저널)를 Read하여 `## 검증 루프`(현재 계층·시도 횟수)와
   `## 검증 루프 로그`(이력) 등 도구가 담지 못하는 서술 맥락을 보완한다.
```

1단계(`show`)가 기계 상태(단계·행 상태·`current_status`)의 유일 근거이며, 2단계(STATE.md Read)는 검증 루프 진행 상태를 포함한 서술 맥락 보완 전용이다 — STATE.md에서 진행률·행 상태를 읽어 판단하지 않는다.

위 2단계 절차로 복원한 뒤, `## 검증 루프`·`## 검증 루프 로그` 자유 기재를 아래 순서로 해석하여 재개 지점을 판단한다:

1. `## 검증 루프`의 `검증` 항목에서 마지막 검증 계층과 시도 횟수를 확인한다
2. `## 검증 루프 로그`의 마지막 행에서 결과를 확인한다:
   - `Fail` → 해당 계층의 다음 시도부터 재개
   - `Escalation` → 사용자에게 에스컬레이션 상태 알림, 결정 요청
   - `Regression` → 회귀 상태 알림, 복원 여부 결정 요청
   - `Pass` → 다음 계층부터 재개
3. 재개 시 이전 세션의 시도 횟수를 누적한다 (세션 간 리셋하지 않음)

---

## 7. 하네스 참조

이 가이드의 재시도 한도와 에스컬레이션 규칙은 `opal-harness.md`의 **"자동 루핑 제약 (Verification Loop Guards)"** 섹션에 정의된 Guards와 일치한다.

### 하네스 Guards 요약 (정합성 확인용)

| 실패 유형 | 최대 재시도 | 초과 시 동작 |
|----------|-----------|------------|
| lint/format | 제한 없음 (즉시 수정) | - |
| build/type | 2회 | 사용자 에스컬레이션 |
| unit/integration test (L3a) | 3회 | 사용자 에스컬레이션 |
| E2E test (L3b) | 1회 | 사용자 에스컬레이션 |
| 설계 수준 — scope별 분기 (action→재PLAN[harness 상한] / wbs→PM / trd→0회) | scope별 상이 | action: harness §1 참조 / wbs: PM 에스컬레이션 / trd: 즉시 사용자 에스컬레이션 |
| PLAN 재진입(재설계 루프) | → `opal-harness.md` §1 참조 | scope별 에스컬레이션 (action 상한 초과→wbs PM / trd→사용자) |

> **정합성 주석**: "0회 즉시 에스컬레이션"은 `scope: trd`에만 적용. `scope: action`은 harness §1 PLAN 재진입 행의 상한 내 에이전트 자율 재설계가 허용된다. §1 루프 흐름 요약 및 §2 L4 계층의 에스컬레이션 서술도 이 scope별 분기 기준을 따른다.

**참조 경로**: `opal/core/references/opal-harness.md` §1 > Guards > 자동 루핑 제약 (Verification Loop Guards)

### 관련 문서

- `opal-harness.md` — 오케스트레이터 공통 인프라 (Guards, Gates, State)
- `opal-pilot-project-dev/SKILL.md` — oppd Phase 3 실행 프로세스
- `opal-pilot-project-dev/references/wbs-guide.md` — 태스크 분할 및 완료 기준 정의

---

## 변경이력

| 날짜 | 버전 | 변경내용 |
|------|------|---------|
| 2026-05-01 | R-2 | state-tool 도입 — §6 PM 루프 모니터링에 `[MUST]` state-tool 호출 블록 추가. oppd 비표준 행 구성 R-10 명시(gate-pass 금지). EXECUTE Step 완료 시 `state mark --as-worker` 호출 표기. "STATE.md 검증 루프 로그" 섹션(§5/§6)은 자유 텍스트 영역으로 보존 — TASK F-18 / PLAN §1.5 M-30 / §3 Step 11 (134) |
| 2026-06-21 16:05 | R-3 | B7 triage 3분류(구현/설계/회귀) 추가 + §3-5 "QA 0회"→"설계 수준" scope별 분기(action 재PLAN[harness 포인터]/wbs PM/trd 0회 유지) + §7 정합성 표 PLAN 재진입 행(harness §1 포인터, 수치 미복제) (031) |
| 2026-06-21 | R-4 | 검증 명령 4종 표준 정합 — §2 L1 `lint`→`lint:fix`, L3a `test:unit`→`npm test -- --run`(watch 금지 단발 실행). watch 모드 금지 규칙 1문장 신규 추가(SSOT 단일 기재). `--testPathPattern` 2건 Vitest식 치환(L3a 템플릿·auth 예시). §검증 명령 결정 추론 키 구조 보존 (033) |
| 2026-06-23 | R-5 | 3축 명명 매핑 표 추가(L계층/검증깊이/파이프라인 단계 별도 축 명시) + 단위=EXECUTE/통합=TEST 배선 (039) |
| 2026-08-16 13:31 | R-6 | STATE.md 저널화 정합 — §6 MUST 블록을 표준 문구 A로 교체 + `--row`→`--task-step`. "루프 진행률 추적 방법"의 `## 현재 상태` 필드 서술을 삭제하고 `show --format json`(진행/상태) + STATE.md 저널 자유 기재 `## 검증 루프`(현재 계층·시도) 보관처로 재정의(H-12). "세션 복원 시 루프 상태 재개"를 `STATE.md Read` 단일 절차에서 `show`(기계 상태) → `STATE.md Read`(서술 맥락 보완) 2단계 표준 절차로 교체(harness/state.md §세션 복원과 동일 문구) (094) |
