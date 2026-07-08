# PLAN: OPAL 검증 명령 표준 명문화 + dashboard/frontend vitest 셋업

> 작성일: 2026-06-21 | 입력: TASK.md, ANALYSIS.md
> 모드: Multi-Feature (기능 2개 — 트랙 A 문서 정합 / 트랙 B FE 코드·설정)

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

OPAL 자동 검증 체계의 검증 명령을 캡틴 4종 표준(L1=`npm run lint:fix` / L2=`npm run build`·`npx tsc --noEmit` / L3a=`npm test -- --run`)으로 명문화하고, "테스트는 watch 모드 금지(단발 실행)" 규칙을 SSOT에 신규 등록한다. 동시에 표준이 실제로 동작하도록 `dashboard/frontend`에 vitest를 셋업하여 build-only 정책을 unit 포함으로 전환한다. 트랙 A(문서)와 트랙 B(FE 코드)는 의존성이 없어 병렬 Phase로 실행 가능하다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | 검증 명령 4종 표준 문서 정합 (트랙 A) | R-A1, R-A2, R-A3 | P0 | 없음 |
| F-002 | dashboard/frontend vitest 셋업 + 동작검증 (트랙 B) | R-B1, R-B2 | P0 | 없음 (F-001과 독립·병렬) |

> TASK 요구사항 매핑: R-A1·R-A2·R-A3 → F-001 / R-B1·R-B2 → F-002. 모든 R 커버.

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 (트랙 A: 문서)  ─┐
                      ├─ (독립 — 병렬 그룹)
F-002 (트랙 B: FE)    ─┘
```

두 기능은 입력·산출물·파일 집합이 완전히 분리된다. F-001은 `opal/skills/**` 마크다운만, F-002는 `dashboard/frontend/**` 코드/설정만 변경한다. 교차 의존 없음 → 병렬 실행 가능.

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 된다. 트랙별 RED-first 적용 여부를 명시한다.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-001 / verification-loop-guide.md §검증 명령 결정 (L68-80) | 추론 키(`test`/`test:unit` 등)를 잘못 바꾸면 oppd 검증 루프가 L3a 명령을 추론 못 해 SKIP/오추론 | P0 | L1(산출물 grep: 추론 키 보존) | S-A 후보 |
| H-2 | F-001 / "watch 금지" 규칙 누락 (SSOT) | CI/자동 검증에서 watch 모드가 무한 대기로 잠김 (규칙이 SSOT에 없으면 재발) | P1 | L1(문장 존재 grep) | S-B 후보 |
| H-3 | F-001 / `--testPathPattern` 16건 치환 (verification-loop 2 + wbs 14) | Jest식 문법이 1건이라도 잔존하면 표준 불일치·EXECUTE 워커가 Jest 명령 복제 | P1 | L1(잔존 0건 grep) | S-C 후보 |
| H-4 | F-001 / wbs-guide.md generic 금지 원칙(L46/L175/L264) | 치환 시 단순 `npm test -- --run`으로 평탄화하면 "액션별 구체 명령 필수"(L46) 원칙 훼손 | P1 | L1(generic 금지 문장 보존 + 치환 명령에 대상 경로/`-t` 유지) | S-D 후보 |
| H-5 | F-001 / SSOT 단일 기재 vs cascade 복제 | watch 금지 "규칙"을 cascade(wbs/roadmap)에 재서술하면 SSOT 이원화 (`.opal/AGENT.md` 위반) | P2 | L1(규칙 문장은 SSOT 1곳, cascade는 예시만) | S-E 후보 |
| H-6 | F-002 / vitest ↔ Vite 8 peer | vitest ^4.1.9 peer(`vite ^6\|\|^7\|\|^8`)가 Vite 8.0.12 불만족 시 설치/실행 실패 | P0 | L3a(실측 — `npm test -- --run` exit 0) | S-F 후보 |
| H-7 | F-002 / `npm run build` 회귀 | vitest.config.ts·devDeps 추가가 기존 `tsc -b && vite build` 동작을 변경 | P0 | L2(실측 — `npm run build` 회귀 0) | S-G 후보 |
| H-8 | F-002 / `typecheck` 스크립트 정의 | 프로젝트가 project references(`tsc -b`)를 쓰므로 단순 `tsc --noEmit`가 표준 단독 typecheck로 오작동 가능 | P1 | L2(실측 — `npm run typecheck` exit 0) | S-H 후보 |
| H-9 | F-002 / 샘플 테스트 RED→GREEN | setupFiles 경로·happy-dom 환경·jest-dom 매처 미정합 시 샘플 PASS 실패 | P1 | L3a(샘플 RED→GREEN 실측) | S-I 후보 |
| H-10 | F-001·F-002 공통 / 배포 경계 | `~/.opal/` 배포본 직접 수정 시 소스-배포 불일치, install 미발효 | P1 | L1(소스만 변경 확인 — `~/.opal/` diff 0) | S-J 후보 |
| H-11 | F-001·F-002 공통 / 변경이력 누락 | 수정 문서에 033 변경이력 행 누락 시 컨벤션 위반 | P2 | L1(변경 문서별 033 행 grep) | S-K 후보 |

**RED-first 트랙별 적용 (최종 결정은 TEST-SCENARIO 단계)**:
- **트랙 A (F-001) = 문서 정합** → 동작 검증 불요. **RED-first 비적용 트랙**. 검증은 산출물 grep(L1) 정합 검사로 충분.
- **트랙 B (F-002) = vitest 셋업** → 샘플 테스트에 RED→GREEN 적용 가능 (예: `cn()` 기대 동작 테스트를 먼저 실패시키는 형태로 작성 후 환경 정합으로 GREEN 전환). **RED-first 적용 가능 트랙**. PLAN은 적용 여부만 명시하고, 구체 시나리오 구성은 TEST-SCENARIO 단계가 결정한다.

---

## 2. 기능별 분석

### F-001: 검증 명령 4종 표준 문서 정합 (트랙 A)

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드(SSOT) | `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` | 검증 명령 계층 정의(§2)·명령 결정 규칙(§검증 명령 결정) — **SSOT** | 수정 |
| 가이드(cascade) | `opal/skills/opal-pilot-project-dev/references/wbs-guide.md` | 수용 시나리오 검증 명령 예시(Jest식 14건) + generic 금지 원칙 | 수정 |
| 가이드(cascade) | `opal/skills/opal-pilot-project-dev/references/roadmap-guide.md` | 액션 검증 명령 예시(generic `&&` 6건) | 수정(조건부 — §2.1.3 grep 재확정) |
| 가이드(cascade) | `opal/skills/opal-pilot-project-dev/references/parallel-execution-guide.md` | 병렬 액션 검증 명령 예시(generic `&&` 변형 다수) | 수정(조건부 — 동일) |
| 스킬 | `opal/skills/opal-pilot-project-dev/SKILL.md` | WBS 예시 표의 generic `npm run lint && npm test` 2건 | 수정(조건부 — 동일) |
| 문서 | `docs/CONVENTIONS.md` | 검증 명령 표준 등록 검토(구현 규칙 절) | 수정 검토(R-A3) |
| 가이드(참조) | `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | 테스트 도구 단발 실행·vitest 언급 | **변경 불요** (이미 "Bash 단발 실행" 정합, `--testPathPattern` 0건 — §2.1.3) |

#### 2.1.2 현재 구현 (ANALYSIS.md + grep 재확정 기반)

- **verification-loop-guide.md §2 계층 정의 표 (L52-58)**: 현행 L1=`npm run lint`·`npm run format:check`, L2=`npm run build`·`npx tsc --noEmit`, L3a=`npm run test:unit`·`npm run test:api`, L3b=`npm run test:e2e`. → L2/타입체크는 이미 표준 일치. L1(`:fix` 없음)·L3a(Jest/스크립트식)가 표준과 어긋남. "watch 금지" 문구 부재.
- **verification-loop-guide.md §검증 명령 결정 (L68-80)**: package.json scripts 추론 키 정의 — lint(`lint`,`lint:check`)/build(`build`,`typecheck`,`tsc`)/test(`test`,`test:unit`,`test:api`,`test:integration`)/E2E. 이 추론 구조는 [MUST] 보존(H-1).
- **verification-loop-guide.md `--testPathPattern` 2건**: L220(generic 템플릿 `{test 검증 명령} -- --testPathPattern={패턴}`), L238(Jest 예시 `npm test -- --testPathPattern=auth`). L223의 "예시 — Jest 테스트 실패" 헤딩과 L226의 "검증 루프: test 시도 1/3" 문맥과 연결.
- **wbs-guide.md `--testPathPattern` 14건**: L164·165·166·167·168·169·170(액션 수용 시나리오 표 7건), L280·281·282·283·284(유형별 검증 명령 표 5건), L298·299(FE 3계층 표 2건). + generic 금지 원칙 L46/L175/L264.

#### 2.1.3 영향 범위

- **상위 의존(소비자)**: oppd 오케스트레이터가 verification-loop-guide §검증 명령 결정을 참조해 L3a 명령을 추론한다(H-1). wbs-guide·roadmap-guide는 WBS.md 작성 시 수용 시나리오 예시로 복제된다.
- **EXECUTE 직전 grep 재확정 (결정론적 — 특정 라인 하드코딩 금지)**: 본 PLAN 작성 시점 grep 실측은 아래와 같다. EXECUTE 워커는 **착수 직전 동일 grep을 재실행**하여 file:line·건수를 재확정한 뒤 치환한다.
  - `grep -rn -- "--testPathPattern" opal/ skills/ agents/ dashboard/ docs/` → **16건** (verification-loop-guide 2 + wbs-guide 14). 그 외 후보 파일(test-scenario-guide, qa-wireframe, opal-pilot-sdd, test-engineer) **0건** — 변경 불요로 확정.
  - `grep -rn -- "npm run lint && npm test" ...` → **8건** (SKILL.md L334·335, roadmap-guide L98·99·100, wbs-guide L46·175·264). 단 wbs-guide 3건은 **generic 금지 원칙 설명문(부정 예시)** 이므로 **치환 금지·보존**(H-4) — SKILL.md 2건·roadmap-guide 3건만 표준 정합 대상.
  - `grep -rn -- "npm run lint && npm run build && npm test" ...` → roadmap-guide L101, parallel-execution-guide L39·40·41·288·331·522·524 등 변형 — 표준 정합 대상(generic `&&` 변형).
- **하위 의존**: 없음 (가이드는 소비만 됨).
- **관련 테스트**: 문서 정합이므로 산출물 grep 검증(L1)이 테스트.

### F-002: dashboard/frontend vitest 셋업 + 동작검증 (트랙 B)

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 환경 | `dashboard/frontend/package.json` | scripts(test/lint:fix/typecheck) + devDependencies(vitest 외) | 수정 |
| 환경 | `dashboard/frontend/vitest.config.ts` | vitest 설정 (environment/globals/setupFiles/plugin) | 신규 |
| 환경 | `dashboard/frontend/src/test/setup.ts` | jest-dom 매처 등록 setupFile | 신규 |
| FE | `dashboard/frontend/src/lib/utils.test.ts` (또는 `src/**/__tests__/`) | 샘플 테스트(`cn()` 검증) | 신규 |
| 환경 | `dashboard/frontend/tsconfig.app.json` | vitest globals 타입 인식 (필요 시 `types`/`include` 조정) | 수정(조건부) |

#### 2.2.2 현재 구현 (실측 기반)

- **package.json scripts (L6-11)**: `dev`/`build`(`tsc -b && vite build`)/`lint`(`eslint .`)/`preview`만 존재. `test`·`lint:fix`·`typecheck` 부재.
- **devDependencies (L52-66)**: `@vitejs/plugin-react ^6.0.1`·`vite ^8.0.12`·`typescript ~6.0.2`·`eslint ^10.3.0` 존재. vitest·@testing-library·happy-dom 부재 → L3a 추론 SKIP 상태.
- **tsconfig 구조**: project references(`tsconfig.json` → app/node). `tsconfig.app.json`은 `noEmit: true`·`allowImportingTsExtensions: true`·`verbatimModuleSyntax: true`·`types: ["vite/client"]`·`paths: {"@/*": ["./src/*"]}`. → 빌드는 `tsc -b`. 표준 단독 typecheck는 project references와 정합하는 `tsc -b --noEmit` 권고(H-8).
- **샘플 테스트 후보**: `src/lib/utils.ts`의 `cn()` — 순수 함수(DOM 불요), RED→GREEN 시드로 최적. RTL/jest-dom 매처 검증용으로 간단 컴포넌트 렌더 1건 추가 가능.
- **vite.config.ts·eslint.config.js 존재** → vitest는 vite.config와 별도 `vitest.config.ts`로 격리 가능(빌드 회귀 차단 — H-7).

#### 2.2.3 영향 범위

- **상위 의존(소비자)**: oppd가 dashboard/frontend 액션 검증 시 L3a `npm test -- --run` 명령을 추론·실행하게 됨(현재 SKIP → 동작). FE 테스트 정책이 build-only → unit 포함으로 전환.
- **하위 의존**: vitest는 `@vitejs/plugin-react`·`vite`·`happy-dom`·`@testing-library/*`에 의존.
- **공유 상태**: `npm run build`(`tsc -b && vite build`)는 vitest.config.ts 격리로 무영향(H-7).
- **관련 테스트**: 신규 샘플 테스트 + 동작검증 4종(`test`/`lint:fix`/`typecheck`/`build`)은 TEST 단계(opal-test-agent, mode=fe)가 실측.

---

## 3. 기능별 설계

> 인용 형식: `(→ D-N §N)` 또는 `` `경로:줄번호` `` 또는 `[사이트명](URL)`. citation-rules.md §2.

### F-001: 검증 명령 4종 표준 문서 정합 (트랙 A)

#### 3.1.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| - | (없음 — 문서 정합은 기존 파일 수정만) | - | - | - |

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` | 가이드(SSOT) | §2 계층 표를 4종 표준으로(L1=`lint:fix`, L2=`build`/`tsc --noEmit`, L3a=`npm test -- --run`) + "watch 금지(단발 실행)" 규칙 신규 1문장 + §검증 명령 결정 추론 키 정합 + `--testPathPattern` 2건(L220 generic 템플릿·L238 예시) Vitest식 치환 | `verification-loop-guide.md:52-58,68-80,220,238` (→ D-1) |
| 2 | `opal/skills/opal-pilot-project-dev/references/wbs-guide.md` | 가이드(cascade) | `--testPathPattern` **14건**(L164-170 7건 / L280-284 5건 / L298-299 2건)을 Vitest식 액션별 구체 명령으로 치환. generic 금지 원칙 문장(L46/L175/L264)은 **보존** | `wbs-guide.md:164-170,280-284,298-299` (→ D-2) |
| 3 | `opal/skills/opal-pilot-project-dev/references/roadmap-guide.md` | 가이드(cascade) | generic `npm run lint && npm test`(L98-100)·`+build`(L101) 변형을 `lint:fix` 정합 + 표준 맥락 정렬 | `roadmap-guide.md:98-101` (EXECUTE 직전 grep 재확정) |
| 4 | `opal/skills/opal-pilot-project-dev/references/parallel-execution-guide.md` | 가이드(cascade) | generic `npm run lint && npm run build && npm test` 변형(L39-41,288,331,522,524 등)을 `lint:fix` 정합 | `parallel-execution-guide.md` (EXECUTE 직전 grep 재확정) |
| 5 | `opal/skills/opal-pilot-project-dev/SKILL.md` | 스킬 | WBS 예시 표 generic `npm run lint && npm test`(L334·335)를 `lint:fix` 정합 | `SKILL.md:334-335` (EXECUTE 직전 grep 재확정) |
| 6 | `docs/CONVENTIONS.md` | 문서 | 검증 명령 4종 표준 한 줄 등록 검토(구현 규칙 절) | TASK R-A3 |
| 7 | 위 1~6 각 문서 변경이력 표 | 가이드/스킬/문서 | 033 변경이력 행 추가 (KST 일시) | `docs/CONVENTIONS.md §변경이력 작성 의무` |

> wbs-guide 14건 = 16(전체) − 2(verification-loop-guide). EXECUTE 직전 grep으로 file:line·건수 재확정 후 치환(특정 라인 하드코딩 금지).

#### 3.1.2 API·데이터 모델·화면 설계 (= 치환 규칙 명세)

문서 태스크이므로 "치환 규칙"이 설계의 본체다. 아래 규칙을 결정론적으로 적용한다.

**[규칙 R1] 4종 표준 계층 매핑** (verification-loop-guide §2 계층 표):

| 계층 | 표준 명령 (예시) | 원칙 |
|------|----------------|------|
| L1 lint/format | `npm run lint:fix` | 자동 수정 가능 (기존 `npm run lint`는 체크만) |
| L2 build/type | `npm run build` / `npx tsc --noEmit` | 변경 없음 (이미 표준) |
| L3a unit/integration | `npm test -- --run` | watch 금지 단발 실행 |
| L3b E2E | `npm run test:e2e` / `npx playwright test` | 변경 없음 |

- [MUST] `opal/core/PRINCIPLES.md` Core Stance: "Platform-independent: keep Claude/Cursor/Gemini branches in adapters, never in logic." (`opal/core/PRINCIPLES.md:16`) → **"watch 모드 금지(단발 실행)"는 러너 독립 원칙으로 기술**하고, `-- --run`은 **Vitest 예시**로만 둔다. 특정 러너(vitest)를 하드 강제하지 않는다. (→ D-3)
- [MUST] `verification-loop-guide.md` §검증 명령 결정 (L73-78): 검증 명령은 package.json scripts에서 **추론**한다. → 추론 키 구조(`lint`/`build`/`test`·`test:unit` 등)를 보존하고, watch 금지 원칙만 추가한다. (→ D-1 §검증 명령 결정)

**[규칙 R2] "watch 금지" 규칙 신규 문장** (SSOT 단일 기재 — verification-loop-guide만):
- §2 계층 정의 또는 §검증 명령 결정에 1문장 신규 추가. 예시 문안: "L3a/L3b 테스트는 **watch 모드를 금지**하고 단발(non-watch) 실행만 허용한다 — 자동 검증 루프가 무한 대기에 빠지지 않도록 한다. (러너별 단발 옵션 예: Vitest `-- --run`, Jest `--ci`/`--watchAll=false`)". cascade 가이드는 이 규칙을 **재서술하지 않고** 예시 명령만 정합(H-5).

**[규칙 R3] `--testPathPattern` → Vitest식 치환 (generic 금지 보존 — H-4)**:
- [MUST] `wbs-guide.md` L46: "generic 명령 금지 — 액션별 구체 명령 필수" 원칙 보존. → 단순 `npm test -- --run`(전체 실행 = generic)으로 평탄화 **금지**.
- 치환 매핑 (대상 구체성 유지):
  - `npm test -- --testPathPattern=<경로/패턴>` → `npm test -- --run <파일/경로 glob>` (경로 기반 대상 지정)
  - 시나리오 이름 기반이 적합하면 → `npm test -- --run -t "<test name>"`
  - 예: `--testPathPattern=auth` → `--run src/**/auth*` 또는 `--run -t "auth"`; `--testPathPattern=api/crud` → `--run src/**/api/crud*` 등. EXECUTE 워커가 각 액션 문맥(BE/FE/통합)에 맞는 대상으로 구체화.
- generic 금지 원칙 설명문(L46/L175/L264)의 부정 예시 `npm run lint && npm test`는 **원칙 설명이므로 보존**(치환하면 원칙 문장이 깨짐).

**[규칙 R4] generic `&&` 변형 정합** (roadmap-guide·parallel-execution-guide·SKILL.md):
- `npm run lint && npm test` / `npm run lint && npm run build && npm test` 형태의 **표준 정합 대상**(generic 금지 원칙 설명문 제외)은 `npm run lint` → `npm run lint:fix`로 정합. (해당 표들은 roadmap/parallel 예시 맥락이므로 `&&` 묶음 자체는 예시로 허용되나, lint 명령은 표준화 — R-A2 "generic `&&` 변형도 정합".)

**[규칙 R5] CONVENTIONS.md 등록 (R-A3)**: `docs/CONVENTIONS.md` 구현 규칙 절(또는 검증 관련 신규 항목)에 "검증 명령 4종 표준(L1=`lint:fix`/L2=`build`·`tsc --noEmit`/L3a=`npm test -- --run` watch 금지) — SSOT: `verification-loop-guide.md`" 한 줄 등록. 규칙 본체는 복제하지 않고 SSOT 포인터로 기재(H-5).

#### 3.1.3 환경 변경

해당 없음 (문서만 수정).

#### 3.1.4 배치/마이그레이션

해당 없음.

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-A2 AC | 산출물 검사 | `grep -rn -- "--testPathPattern" opal/ skills/ agents/ dashboard/ docs/` → **0건** (16건 전부 치환) |
| TS-002 | R-A1 AC | 산출물 검사 | verification-loop-guide.md에 "watch" 금지 규칙 문장 ≥1개 존재 + L1 계층에 `lint:fix` 반영 |
| TS-003 | R-A1 AC | 산출물 검사 | verification-loop-guide.md §검증 명령 결정의 package.json 추론 키 구조 보존(`lint`/`build`/`test` 키 잔존) |
| TS-004 | R-A2 AC | 산출물 검사 | wbs-guide.md generic 금지 원칙 문장(L46/L175/L264 부정 예시) 보존 + 치환된 명령에 대상 경로/`-t` 구체성 존재 (단순 `npm test -- --run` 단독 0건) |
| TS-005 | R-A3 AC | 산출물 검사 | 수정한 모든 문서(verification-loop·wbs·roadmap·parallel·SKILL·CONVENTIONS)에 033 변경이력 행 존재 |
| TS-006 | R-A2 AC | 산출물 검사 | `npm run lint`(`:fix` 없는 generic 정합 대상) → `lint:fix` 정합 (원칙 설명문 제외 잔존 0건) |

### F-002: dashboard/frontend vitest 셋업 + 동작검증 (트랙 B)

#### 3.2.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `dashboard/frontend/vitest.config.ts` | 환경 | vitest 설정 (environment=happy-dom, globals=true, setupFiles, plugin=@vitejs/plugin-react) | TASK R-B1 / [Vitest Config](https://vitest.dev/config/) |
| 2 | `dashboard/frontend/src/test/setup.ts` | 환경 | `@testing-library/jest-dom` 매처 등록 | TASK R-B1 |
| 3 | `dashboard/frontend/src/lib/utils.test.ts` | FE | 샘플 테스트 — `cn()` 검증(순수 함수) + (선택) RTL 컴포넌트 렌더 1건 | `dashboard/frontend/src/lib/utils.ts:13` (`cn` export) |

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `dashboard/frontend/package.json` | 환경 | scripts에 `test`/`lint:fix`/`typecheck` 추가 + devDependencies에 vitest 외 4종 추가 | `dashboard/frontend/package.json:6-11,52-66` (→ D-4) |
| 2 | `dashboard/frontend/tsconfig.app.json` | 환경 | (조건부) vitest globals 타입 인식 위해 `types`에 항목 추가 또는 vitest.config의 typecheck 위임 | `dashboard/frontend/tsconfig.app.json:7` (`types: ["vite/client"]`) |

#### 3.2.2 API·데이터 모델·화면 설계 (= 설정/스크립트 명세)

**package.json scripts (확정 — TASK R-B1)**:
```jsonc
"scripts": {
  "dev": "vite",
  "build": "tsc -b && vite build",          // 변경 없음 (회귀 차단 — H-7)
  "lint": "eslint .",                          // 기존 유지
  "lint:fix": "eslint . --fix",                // 신규 (L1 표준)
  "typecheck": "tsc -b --noEmit",              // 신규 (L2 표준 — project references 정합, H-8)
  "test": "vitest run",                        // 신규 (L3a 표준; `npm test -- --run` 호출 시 vitest에 --run 전달, run 모드 중복 무해)
  "preview": "vite preview"
}
```
- [MUST] `docs/CONVENTIONS.md §언어 규칙`: 파일/폴더 이름은 English kebab-case (`docs/CONVENTIONS.md:12`). → 신규 파일 `vitest.config.ts`·`setup.ts`·`utils.test.ts` kebab/표준 네이밍 준수.
- `test` = `vitest run`이 기본 단발 실행. `npm test -- --run`은 `vitest run --run`으로 전달되어 watch 금지 보장(H-2 표준의 FE 실현).

**devDependencies 추가 (PM 확정 버전 — 재조사 금지)**:
```jsonc
"vitest": "^4.1.9",                       // peer: vite ^6||^7||^8 → Vite 8.0.12 만족 (H-6)
"@testing-library/react": "^16.3.2",      // React 19 지원
"@testing-library/jest-dom": "최신",       // DOM 매처
"happy-dom": "^20.10.6"                    // 경량 DOM 환경
// @vitejs/plugin-react ^6.0.1 — 기존 유지(추가 안 함)
```
- 버전은 ANALYSIS §2.1·PM 정정 확정값. EXECUTE는 이 버전을 그대로 사용한다(재조사·변경 금지).

**vitest.config.ts (확정 구조)**:
```ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'happy-dom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
  },
  resolve: { alias: { '@': '/src' } },   // tsconfig paths(@/*) 정합 — tsconfig.app.json:25 참조
})
```
- `globals: true` → describe/it/expect 전역 사용 (ANALYSIS §2.1). `environment: 'happy-dom'` → jest-dom 매처와 정합.
- 근거: [Vitest Config](https://vitest.dev/config/), [Vitest Test Context](https://vitest.dev/guide/environment.html).

**src/test/setup.ts**:
```ts
import '@testing-library/jest-dom'
```

**샘플 테스트 (RED-first 적용 가능 — 최종 시나리오는 TEST-SCENARIO 결정)**:
```ts
// src/lib/utils.test.ts
import { describe, it, expect } from 'vitest'
import { cn } from '@/lib/utils'
describe('cn', () => {
  it('merges class names', () => {
    expect(cn('a', 'b')).toBe('a b')
  })
  it('dedupes conflicting tailwind classes', () => {
    expect(cn('p-2', 'p-4')).toBe('p-4')   // tailwind-merge 동작
  })
})
```
- `cn`은 `src/lib/utils.ts:13` 순수 함수 — DOM 불요, RED→GREEN 시드로 적합(H-9).

#### 3.2.3 환경 변경

- 추가 패키지 4종(vitest/@testing-library/react/@testing-library/jest-dom/happy-dom). `npm install` 필요.
- `tsconfig.app.json` `types`에 (필요 시) vitest globals 타입 추가 — globals 타입 미인식으로 typecheck 실패 시에만 조정(H-8). 우선 vitest.config `test.globals`만으로 시도하고, tsc 오류 발생 시 `types: ["vite/client", "vitest/globals"]` 추가.

#### 3.2.4 배치/마이그레이션

해당 없음.

#### 3.2.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-101 | R-B1 AC | 산출물 검사 | package.json에 `test`·`lint:fix`·`typecheck` 스크립트 존재 + devDeps 4종 추가 + `vitest.config.ts`·`setup.ts`·샘플 테스트 파일 존재 |
| TS-102 | R-B2 AC | 기능 테스트 | `npm test -- --run` 실행 → watch 없이 종료(exit 0), 샘플 테스트 PASS |
| TS-103 | R-B2 AC | 기능 테스트 | `npm run lint:fix` 정상 종료(exit 0) |
| TS-104 | R-B2 AC | 기능 테스트 | `npm run typecheck`(`tsc -b --noEmit`) 정상 종료(exit 0) |
| TS-105 | R-B2 AC | 회귀 테스트 | `npm run build`(`tsc -b && vite build`) 정상 종료 + 기존 빌드 회귀 0 (H-7) |
| TS-106 | R-B1/H-9 | 기능 테스트 | jest-dom 매처가 setupFiles 경유 등록되어 RTL 컴포넌트 테스트(추가 시) PASS |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| **그룹 P (병렬)** | F-001 | 1, 2, 3 | opal-task-agent | 트랙 내 순차, 트랙 간 병렬 | 트랙 A 문서 — `opal/skills/**`·`docs/**`만 변경 |
| **그룹 P (병렬)** | F-002 | 4, 5, 6 | opal-fe-agent | 트랙 내 순차(4→5→6), 트랙 간 병렬 | 트랙 B FE — `dashboard/frontend/**`만 변경 |
| 직렬 후행 | F-001·F-002 | 7 | PM 직접 | 순차 (Step 1-6 후) | docs/ 갱신 (CONVENTIONS·PROJECT 정책 정합) |

> **병렬 판단**: F-001(문서)과 F-002(FE 코드)는 파일 집합이 완전 분리되어 충돌 없음 → **병렬 그룹 P 구성**. 단 트랙 A 내부(verification SSOT → cascade 정합)는 SSOT 우선 권고, 트랙 B 내부(셋업 → 샘플 → 동작)는 순차.

### 4.2 실행 체크리스트

> 총 7개 Step | Phase 3개(병렬 그룹 P 2트랙 + 후행 1) | 실행 모드: **복잡** (변경 파일 ≥10, 다중 영역, 새 패키지 도입)

#### Step 1: verification-loop-guide.md (SSOT) 4종 표준 + watch 금지 명문화
- [x] 완료
- **소속 기능**: F-001 (R-A1)
- **영역**: 공통 (가이드 SSOT)
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md`
- **작업 내용**: §2 계층 표 L1 → `npm run lint:fix`, L3a → `npm test -- --run`(규칙 R1). "watch 모드 금지(단발 실행)" 규칙 1문장 신규 추가(규칙 R2 — SSOT 단일 기재). §검증 명령 결정 추론 키 구조 보존(H-1). `--testPathPattern` 2건(L220 generic 템플릿·L238 예시) Vitest식 치환(규칙 R3). 변경이력 033 행 추가.
- **완료 기준**: TS-002·TS-003 + 이 파일 내 `--testPathPattern` 0건 + "watch" 금지 문장 ≥1 + 추론 키(`lint`/`build`/`test`) 보존 + 033 변경이력 행
- **테스트**: TS-002, TS-003 (산출물 grep)
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: wbs-guide.md `--testPathPattern` 14건 Vitest식 치환 (generic 금지 보존)
- [x] 완료
- **소속 기능**: F-001 (R-A2)
- **영역**: 공통 (가이드 cascade)
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-project-dev/references/wbs-guide.md`
- **작업 내용**: 착수 직전 `grep -rn -- "--testPathPattern" wbs-guide.md`로 file:line 재확정 후, 14건(L164-170/L280-284/L298-299)을 규칙 R3로 치환(`--run <대상>` 또는 `--run -t "<name>"` — 액션별 구체성 유지). [MUST] generic 금지 원칙 문장(L46/L175/L264 부정 예시 `npm run lint && npm test`)은 **보존**(H-4). 변경이력 033 행 추가.
- **완료 기준**: TS-001(이 파일 0건)·TS-004 + 단순 `npm test -- --run` 단독(대상 없는 generic) 0건 + 033 변경이력 행
- **테스트**: TS-001, TS-004 (산출물 grep)
- **실행 방법**: sub-agent
- **의존**: Step 1 (SSOT 규칙 R2/R3 확정 후 cascade 정합 권고 — 충돌 아님, SSOT 우선 일관성)

#### Step 3: roadmap·parallel·SKILL generic `&&` 변형 lint:fix 정합
- [x] 완료
- **소속 기능**: F-001 (R-A2)
- **영역**: 공통 (가이드/스킬 cascade)
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-project-dev/references/roadmap-guide.md`, `.../parallel-execution-guide.md`, `opal/skills/opal-pilot-project-dev/SKILL.md`
- **작업 내용**: 착수 직전 `grep -rn -- "npm run lint && " <대상들>`로 재확정 후, 표준 정합 대상(원칙 설명문 제외)의 `npm run lint` → `npm run lint:fix` 정합(규칙 R4). watch 금지 "규칙"은 재서술하지 않음(H-5 — SSOT 단일). 각 수정 문서 변경이력 033 행 추가.
- **완료 기준**: TS-006 + 표준 정합 대상에서 `npm run lint`(non-fix) 잔존 0건(원칙 설명문 제외) + 수정 각 문서 033 변경이력 행
- **테스트**: TS-006 (산출물 grep)
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 4: dashboard/frontend package.json scripts + devDeps 추가
- [x] 완료
- **소속 기능**: F-002 (R-B1)
- **영역**: FE (환경)
- **agent**: opal-fe-agent
- **파일**: `dashboard/frontend/package.json`
- **작업 내용**: scripts에 `lint:fix`(`eslint . --fix`)·`typecheck`(`tsc -b --noEmit`)·`test`(`vitest run`) 추가(§3.2.2). `build` 변경 금지(H-7). devDependencies에 PM 확정 버전 4종 추가(vitest ^4.1.9 / @testing-library/react ^16.3.2 / @testing-library/jest-dom 최신 / happy-dom ^20.10.6). `npm install` 수행.
- **완료 기준**: package.json에 3 스크립트 + 4 devDeps 존재, `npm install` 성공, `node_modules`에 vitest 설치
- **테스트**: TS-101 (산출물 검사)
- **실행 방법**: sub-agent
- **의존**: 없음 (트랙 B 시작 — F-001과 병렬)

#### Step 5: vitest.config.ts + setup.ts + 샘플 테스트 작성
- [x] 완료
- **소속 기능**: F-002 (R-B1)
- **영역**: FE (환경 + FE)
- **agent**: opal-fe-agent
- **파일**: `dashboard/frontend/vitest.config.ts`, `dashboard/frontend/src/test/setup.ts`, `dashboard/frontend/src/lib/utils.test.ts`
- **작업 내용**: vitest.config.ts(happy-dom/globals/setupFiles/react plugin/alias `@`→/src) 생성(§3.2.2). setup.ts(jest-dom import). 샘플 테스트(`cn()` 검증) 작성 — RED-first 적용 가능 트랙(TEST-SCENARIO 단계가 RED→GREEN 구성 최종 결정). 필요 시 tsconfig.app.json types 조정(H-8 조건부).
- **완료 기준**: 3개 파일 존재 + vitest.config 구조가 §3.2.2 정합
- **테스트**: TS-101 (산출물 검사)
- **실행 방법**: sub-agent
- **의존**: Step 4

#### Step 6: 동작검증 (TEST 단계 위임) — test/lint:fix/typecheck/build 4종 실측
- [ ] 완료
- **소속 기능**: F-002 (R-B2)
- **영역**: FE (동작검증)
- **agent**: opal-test-agent (mode=fe) — TEST 단계에서 오케스트레이터가 디스패치
- **파일**: `dashboard/frontend/` (실행만)
- **작업 내용**: `npm test -- --run`(watch 없이 exit 0, 샘플 PASS) / `npm run lint:fix` / `npm run typecheck` / `npm run build`(회귀 0) 실측. RED-first 시 샘플 RED→GREEN 전환 확인.
- **완료 기준**: TS-102~TS-105 모두 exit 0 + 기존 build 회귀 0 (H-6·H-7·H-8·H-9 해소)
- **테스트**: TS-102, TS-103, TS-104, TS-105, TS-106
- **실행 방법**: sub-agent (opal-test-agent)
- **의존**: Step 5

#### Step 7: docs/ 갱신 — CONVENTIONS.md 검증 명령 표준 등록
- [ ] 완료
- **소속 기능**: F-001·F-002 (R-A3, 새 패턴/규칙 도입)
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/CONVENTIONS.md` (필요 시 `docs/PROJECT.md` 검증 정책 정합 검토)
- **작업 내용**: 구현 규칙 절에 검증 명령 4종 표준(SSOT=verification-loop-guide.md 포인터) 한 줄 등록(규칙 R5, H-5 — 규칙 본체 복제 금지). dashboard/frontend FE 테스트 정책 build-only→unit 전환 사실이 ARCHITECTURE.md/PROJECT.md 기재와 상충하는지 점검(상충 시 정합). 변경이력 033 행 추가.
- **완료 기준**: TS-005 + CONVENTIONS.md에 검증 명령 표준 등록 + 033 변경이력 행
- **테스트**: TS-005 (산출물 검사)
- **실행 방법**: direct (PM)
- **의존**: Step 1, Step 4 (SSOT 명령·FE 스크립트 확정 후)

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| F-001(Step 1-3) ∥ F-002(Step 4-6) | 파일 집합 완전 분리 (`opal/skills/**` vs `dashboard/frontend/**`) — 충돌 없음, 트랙 간 병렬 |
| Step 1 → Step 2 → Step 3 | 트랙 A 내부 SSOT 우선 일관성 (verification SSOT 규칙 확정 후 cascade 예시 정합) — 충돌 아니나 권고 순서 |
| Step 4 → Step 5 → Step 6 | 트랙 B 내부 의존: 패키지 설치 → 설정/테스트 작성 → 동작검증 (선후 필수) |
| Step 6 (TEST) | opal-test-agent가 TEST 단계에서 디스패치 — EXECUTE 완료 후 |
| Step 7 ⟵ Step 1·4 | docs/ 갱신은 SSOT 명령·FE 스크립트 확정 후 — 후행 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | `--testPathPattern` 전 코드베이스 잔존 0건 | TS-001 | `grep -rn -- "--testPathPattern" opal/ skills/ agents/ dashboard/ docs/` → 0건 |
| F-001 | watch 금지 규칙 SSOT 명문화 + 추론 키 보존 | TS-002, TS-003 | verification-loop-guide에 watch 금지 문장 ≥1 + `lint:fix` 반영 + 추론 키 잔존 |
| F-001 | generic 금지 원칙 보존 + 치환 구체성 | TS-004 | 원칙 설명문 보존 + 대상 없는 단순 `npm test -- --run` 0건 |
| F-001 | lint:fix 정합 + 변경이력 | TS-005, TS-006 | 정합 대상 lint→lint:fix + 수정 전 문서 033 행 |
| F-002 | vitest 셋업 산출물 존재 | TS-101 | 3 스크립트 + 4 devDeps + config/setup/샘플 파일 |
| F-002 | 4종 명령 동작 + 회귀 0 | TS-102~TS-105 | `test --run`/`lint:fix`/`typecheck`/`build` 전부 exit 0, 빌드 회귀 0 |
| F-002 | jest-dom 매처 정합 | TS-106 | setupFiles 경유 매처 등록, 컴포넌트 테스트 PASS |

### 5.2 회귀 테스트
- [x] `npm run build`(`tsc -b && vite build`) 기존 동작 회귀 0 (H-7, TS-105) — exit 0 확인 (2026-06-21 19:26)
- [ ] verification-loop-guide §검증 명령 결정 package.json 추론 키 구조 보존 → oppd 검증 루프 정상 (H-1, TS-003)
- [ ] cascade 가이드 generic 금지 원칙 문장 보존 → WBS 작성 규칙 비파괴 (H-4, TS-004)

### 5.3 코드/문서 품질
- [ ] 수정한 모든 가이드/스킬/문서에 033 변경이력 행 추가 (`docs/CONVENTIONS.md §변경이력 작성 의무`, TS-005)
- [ ] watch 금지 "규칙"은 SSOT 1곳만 — cascade는 예시만 정합 (H-5, SSOT 단일 기재)
- [x] 신규 FE 파일 네이밍 kebab/표준 준수 (`docs/CONVENTIONS.md:12`) — vitest.config.ts / setup.ts / utils.test.ts 준수 확인
- [ ] [MUST] 러너 하드강제 금지 — watch 금지=원칙, `-- --run`=Vitest 예시 (`opal/core/PRINCIPLES.md:16`)

### 5.4 보안
- [x] devDependencies 추가 패키지(vitest/@testing-library/happy-dom)의 PM 확정 버전 고정 — 임의 latest 미사용 (vitest ^4.1.9 / @testing-library/react ^16.3.2 / @testing-library/jest-dom ^6.6.3 / happy-dom ^20.10.6)
- [x] 샘플 테스트/설정 파일에 하드코딩된 토큰·시크릿 없음
- [x] `.opal/` 배포본 직접 수정 없음 — 소스(`opal/`, `dashboard/`)만 변경, install 재배포로 발효 (H-10, `.opal/AGENT.md` 배포 경계)
- [x] vitest.config·setup·테스트 파일이 빌드 산출물(dist)에 포함되지 않음 (vitest.config 격리 — build exit 0, dist에 test 파일 미포함 확인)

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 7개 | 복잡 |
| 변경 파일 수 | ~11개 (문서 6 + FE 신규 3 + FE 수정 2) | 복잡 |
| 모듈 범위 | 다중 (Framework 문서 + Console FE + docs) | 복잡 |
| 작업 유형 | 표준 명문화(개선) + 새 패키지 도입(vitest 셋업) | 복잡 |
| 외부 의존성 | 있음 (vitest/@testing-library/happy-dom 신규 4종) | 복잡 |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

```
Batch 1 (병렬):
  ├─ [트랙 A] opal-task-agent  → Step 1 → Step 2 → Step 3   (opal/skills/** 마크다운)
  └─ [트랙 B] opal-fe-agent    → Step 4 → Step 5            (dashboard/frontend/**)
Batch 2 (Batch 1 후):
  └─ opal-test-agent (mode=fe) → Step 6                     (FE 동작검증 4종)
Batch 3 (Batch 1·2 후):
  └─ PM 직접                    → Step 7                     (docs/CONVENTIONS.md)
```

- **그룹핑 원칙**: 파일 충돌 방지 — 트랙 A는 `opal/skills/**`, 트랙 B는 `dashboard/frontend/**`로 완전 분리. 동일 트랙 내 파일은 같은 에이전트가 순차 처리.
- **병렬 극대화**: 트랙 A·B는 독립 디렉토리이므로 Batch 1에서 병렬 디스패치.

### C-2. 스킬 요구사항

- 트랙 A·B EXECUTE: `op-dev-execute` (체크포인트 기반 코드/문서 실행) — 기존 스킬 매칭, 갭 없음.
- 트랙 B 샘플 테스트: `op-dev-test-scenario`(선택, 샘플 시나리오 구성) — RED-first 구성 시 TEST-SCENARIO 단계 사용.
- 신규 스킬 불요 (동일 패턴 3 Step 미만의 신규 행위 없음).

### C-3. 도구 요구사항

- **패키지**: vitest ^4.1.9 / @testing-library/react ^16.3.2 / @testing-library/jest-dom 최신 / happy-dom ^20.10.6 (PM 확정 — npm install).
- **MCP**: context7(vitest config API 확인, 필요 시) — ANALYSIS §6.3.
- **CLI**: grep(결정론적 잔존 검사), npm(설치·동작검증), `./scripts/install-mac.sh`(EXECUTE 후 재배포 — 배포 경계 H-10).

### C-4. 테스트 전략

- **opal-test-agent (mode=fe)**: Step 6에서 동작검증 4종 실측 (TS-102~TS-106).
  - 기능 테스트: `npm test -- --run` (watch 없이 exit 0, 샘플 PASS)
  - 코드 품질: `npm run lint:fix`, `npm run typecheck`
  - 회귀 테스트: `npm run build` (기존 동작 회귀 0)
- **문서(트랙 A) 검증**: 동작 테스트 없음 — 산출물 grep(L1) 정합 검사 (TS-001~TS-006). PM Gate에서 직접 수행.
- **RED-first**: 트랙 A 비적용, 트랙 B 샘플에 적용 가능(최종 TEST-SCENARIO 결정).

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| Framework 문서 (트랙 A) | Markdown (가이드/스킬) | op-dev-execute |
| Console FE (트랙 B) | React 19, TypeScript ~6.0, Vite 8, vitest ^4.1.9, @testing-library, happy-dom | op-dev-execute, op-dev-test-scenario |

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| context7 | vitest config API(environment/globals/setupFiles) 확인용 — ANALYSIS §2.1에서 PM이 버전·peer 실측 완료, 추가 조회 선택 |

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | verification-loop-guide.md (SSOT) | `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` | 검증 명령 SSOT — §2 계층·§검증 명령 결정·`--testPathPattern` 2건 (규칙 R1·R2·R3) |
| D-2 | 설계 | wbs-guide.md | `opal/skills/opal-pilot-project-dev/references/wbs-guide.md` | `--testPathPattern` 14건·generic 금지 원칙 L46 (규칙 R3·R4, H-4) |
| D-3 | 설계 | PRINCIPLES.md | `opal/core/PRINCIPLES.md:16` | [MUST] Platform-independent — 러너 하드강제 금지 (규칙 R1) |
| D-4 | 소스 | package.json (FE) | `dashboard/frontend/package.json:6-11,52-66` | vitest 셋업 대상·현행 scripts/devDeps |
| D-5 | 소스 | utils.ts (cn) | `dashboard/frontend/src/lib/utils.ts:13` | 샘플 테스트 시드(순수 함수) |
| D-6 | 소스 | tsconfig.app.json | `dashboard/frontend/tsconfig.app.json` | project references·noEmit·paths — typecheck 설계(H-8) |
| D-7 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 변경이력 의무·배포 경계·네이밍·검증 명령 등록(R-A3) |
| D-8 | 외부 | Vitest Config | [Vitest Config](https://vitest.dev/config/) | vitest.config 구조(environment/globals/setupFiles/plugin) |
| D-9 | 외부 | npm vitest | [npm vitest](https://www.npmjs.com/package/vitest) | 버전·peer(PM 실측 확정 ^4.1.9, Vite 8 만족) |
| D-10 | 설계 | test-scenario-guide.md | `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md:71,83` | 테스트 도구 단발 실행·vitest 정합(변경 불요 확인) |

> 인용 형식: `opal/core/references/harness/citation-rules.md §3.1`. 유형: 기획/설계/소스/외부.

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| H-1 | 추론 키 변경 → oppd L3a 오추론/SKIP | F-001 | P0 | §검증 명령 결정 추론 키 구조 보존, TS-003 grep 검증 |
| H-2 | watch 금지 미명문화 → CI 무한 대기 재발 | F-001 | P1 | SSOT 1문장 규칙 R2 + FE `test`=`vitest run` 기본 단발(TS-002·TS-102) |
| H-3 | `--testPathPattern` 잔존 → 표준 불일치 | F-001 | P1 | 16건 전수 치환 + EXECUTE 직전 grep 재확정 + TS-001(0건) |
| H-4 | generic 평탄화 → "구체 명령 필수" 원칙 훼손 | F-001 | P1 | 규칙 R3(대상/`-t` 유지) + 원칙 설명문 보존 + TS-004 |
| H-5 | watch 규칙 cascade 복제 → SSOT 이원화 | F-001 | P2 | 규칙은 SSOT 1곳, cascade 예시만 + 5.3 체크 |
| H-6 | vitest ↔ Vite 8 peer 불만족 | F-002 | P0 | PM 실측 확정(peer 만족) + TS-102 동작검증 |
| H-7 | build 회귀 | F-002 | P0 | `build` 스크립트 변경 금지 + vitest.config 격리 + TS-105 |
| H-8 | typecheck가 project references와 부정합 | F-002 | P1 | `tsc -b --noEmit` 채택 + 필요 시 types 조정 + TS-104 |
| H-9 | 샘플 RED→GREEN 환경 부정합 | F-002 | P1 | happy-dom/setupFiles/jest-dom 정합 + 순수함수 시드 + TS-102·TS-106 |
| H-10 | 배포 경계 위반(`~/.opal/` 직접 수정) | 공통 | P1 | 소스만 변경, install 재배포 + 5.4 체크 |
| H-11 | 변경이력 누락 | 공통 | P2 | 수정 문서별 033 행 + TS-005 |

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-06-21 17:00 | 초기 작성 — 2트랙(F-001 문서 정합 / F-002 FE vitest) Multi-Feature PLAN. PM 실측 정정 반영(`--testPathPattern` 16건=verification 2+wbs 14, generic `&&` 변형 별도). 치환 규칙 R1~R5(러너 독립 원칙·watch 금지 SSOT 단일·generic 금지 보존). RED-first 트랙별(A 비적용/B 적용가능). 리스크 가설 H-1~H-11. EXECUTE 직전 grep 재확정 명시(라인 하드코딩 금지) (033) |
