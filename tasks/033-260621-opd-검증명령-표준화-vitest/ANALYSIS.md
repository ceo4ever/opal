# ANALYSIS: OPAL 검증 명령 표준 명문화 + dashboard/frontend vitest 셋업

> 작성일: 2026-06-21
> 입력: TASK.md
> 출력: ANALYSIS.md

---

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | verification-loop-guide.md (SSOT) | `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` | 검증 명령 SSOT — 계층 정의(L1-L4)·명령 결정 규칙·watch 모드 금지 신규 규칙 추가 대상 |
| D-2 | 설계 | wbs-guide.md | `opal/skills/opal-pilot-project-dev/references/wbs-guide.md` | 수용 시나리오 검증 명령(Jest식 다수)·generic 금지 원칙(L46)·액션별 수용 시나리오 표(L164-170, 280-299) |
| D-3 | 설계 | PRINCIPLES.md | `opal/core/PRINCIPLES.md` | 플랫폼 독립성 원칙(Core Stance: "Platform-independent: keep Claude/Cursor/Gemini branches in adapters, never in logic") |
| D-4 | 소스 | package.json (FE) | `dashboard/frontend/package.json` | vitest 셋업 대상·현행 스크립트 현황(build, lint만 존재) |
| D-5 | 설계 | test-scenario-guide.md | `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | 테스트 도구(M1) 단발 실행·vitest 언급 |
| D-6 | 설계 | roadmap-guide.md | `opal/skills/opal-pilot-project-dev/references/roadmap-guide.md` | 액션 검증 명령 예시(Jest식 존재 여부 확인) |
| D-7 | 설계 | parallel-execution-guide.md | `opal/skills/opal-pilot-project-dev/references/parallel-execution-guide.md` | 병렬 액션 검증 명령 예시(Jest식 존재 여부 확인) |
| D-8 | 외부 | Vitest 공식 문서 | [Vitest](https://vitest.dev/) | vitest 설정·환경 변수·플러그인 문서 |
| D-9 | 외부 | npm 레지스트리 | [npm vitest](https://www.npmjs.com/package/vitest) | vitest 최신 버전 확인 |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §2 참조.

---

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` | **SSOT** — 검증 명령 계층 정의·명령 결정 규칙 | **필수** — 4종 표준 + watch 금지 규칙 명문화 | D-1 §2 (L52-80), §검증 명령 결정 (L68-80) |
| `opal/skills/opal-pilot-project-dev/references/wbs-guide.md` | cascade 가이드 — 수용 시나리오 검증 명령(Jest식) | **필수** — `--testPathPattern` → Vitest식 통일 | L164-170, 280-299 |
| `opal/skills/opal-pilot-project-dev/references/roadmap-guide.md` | cascade 가이드 — 액션 검증 명령 예시 | 조건부 — Jest식 존재 시 통일 | grep으로 확정 필요 |
| `opal/skills/opal-pilot-project-dev/references/parallel-execution-guide.md` | cascade 가이드 — 병렬 액션 검증 명령 | 조건부 — Jest식 존재 시 통일 | grep으로 확정 필요 |
| `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | cascade 참조 — 테스트 도구 단발 실행 | 조건부 — vitest 관련 내용 정합 | grep 확인 필요 |
| `opal/agents/opal-test-agent/personas/test-engineer.md` | 페르소나 — 검증 명령 참조 | 조건부 — `--testPathPattern` 존재 시 통일 | grep 확인 필요 |
| `opal/skills/opal-pilot-project-dev/SKILL.md` | opal-pilot-project-dev 스킬 정의 | 조건부 — 검증 명령 참조 | grep 확인 필요 |
| `opal/skills/op-dev-qa/references/qa-wireframe-guide.md` | QA 와이어프레임 가이드 | 조건부 — 검증 명령 참조 | grep 확인 필요 |
| `opal/skills/opal-pilot-sdd/SKILL.md` | 스킬 정의 | 조건부 — 검증 명령 참조 | grep 확인 필요 |
| `opal/skills/opal-pilot-sdd/references/execute-loop-guide.md` | execute 루프 가이드 | 조건부 — 검증 명령 참조 | grep 확인 필요 |
| `dashboard/frontend/package.json` | FE 프로젝트 설정 | **필수** — test/lint:fix/typecheck 스크립트 추가 | D-4 (현황: L6-10, test·typecheck 스크립트 미존재) |
| `dashboard/frontend/vitest.config.ts` | Vitest 설정 파일 | **신규 생성** — environment/globals/setupFiles/plugin | - |
| `dashboard/frontend/src/**/*.test.ts(x)` | 샘플 테스트 파일 | **신규 생성** — 최소 1개 이상 샘플 | - |

### 1.2 아키텍처 패턴

**현행 검증 명령 사용 패턴 (4종)**:

1. **L1: Lint/Format** — `npm run lint` (ESLint, 스타일)
   - 현황: `dashboard/frontend`에는 `npm run lint` (L9) 존재
   - 표준: `npm run lint:fix` (자동 수정 가능해야 함)
   - 기존 `npm run lint`는 체크만 수행 (fix 불가)

2. **L2: Build/Type** — `npm run build` + `npx tsc --noEmit` 병행
   - `npm run build`: Vite 빌드 + TypeScript 바이너리 빌드 (`tsc -b`)
   - `npx tsc --noEmit`: 타입 체크 단독

3. **L3a: Unit/Integration Test** — Jest식 `npm test -- --testPathPattern={패턴}` (문제)
   - **현행**: WBS에 `--testPathPattern` 명령 산재 (L164-170, 280-299 in wbs-guide, L220·238 in verification-loop-guide)
   - **문제**: Jest 문법이며, `dashboard/frontend`는 테스트 러너 자체 부재 (vitest 설치 필요)
   - **표준**: Vitest `npm test -- --run` (단발 비watch) 또는 `npm test -- --run -t "{name}"`
   - **watch 모드 금지**: CI/자동 검증에서는 단발 실행만 허용

4. **L3b: E2E Test** — Playwright/Cypress (특정 액션만)
   - 현황: WBS에 E2E 명령 명시되면 실행 (L65-66 in verification-loop-guide)

**패턴 정합 이슈**:
- verification-loop-guide.md는 SSOT이나, "watch 모드 금지" 규칙이 명문화되지 않음
- wbs-guide.md의 "generic 명령 금지"(L46) 원칙 ↔ vitest 표준화 정합 필요
- `--testPathPattern` 예시가 8개 액션 + 4개 유형(L164-170, 280-299)에 산재

### 1.3 의존성 맵

**documentation 레이어** (마크다운):
```
verification-loop-guide.md (SSOT, L68-80 검증 명령 결정 규칙)
  ← wbs-guide.md (수용 시나리오 표, L164-170 등)
  ← roadmap-guide.md (예시)
  ← parallel-execution-guide.md (예시)
  ← test-scenario-guide.md (테스트 도구 M1 참조)
```

**code 레이어**:
```
dashboard/frontend/package.json (scripts)
  ← dashboard/frontend/tsconfig.json (TypeScript 설정)
  ← dashboard/frontend/vite.config.ts (Vite 설정)
  ← dashboard/frontend/eslint.config.js (ESLint 설정)
```

**현황**: dashboard/frontend에 vitest 설정 없음 (build·dev·lint·preview만 존재).

### 1.4 테스트 현황

**dashboard/frontend**:
- ✅ **Build**: `npm run build` (tsc -b && vite build) 동작 확인
- ✅ **Lint**: `npm run lint` (ESLint) 동작 확인
- ❌ **Test**: test 스크립트 미존재 / vitest 미설치 / 테스트 파일 0건 / vitest.config.ts 미존재
- ❌ **Type Check**: typecheck 스크립트 미존재 (build에 포함되나 단독 검증 불가)

**검증 루핑 측면** (D-1 L68-78):
- `npm test` / `npm run test:unit` 스크립트 없으므로, 현재 dashboard/frontend은 검증 명령 추론(D-1 L73-78)에서 **SKIP** 상태

---

## 2. 외부 조사 결과

### 2.1 라이브러리/API 조사

**Vitest 버전 및 호환성** (PM이 `npm view`로 실측):
- `vitest`: **^4.1.9** (latest)
  - peer 의존성: `vite: ^6.0.0 || ^7.0.0 || ^8.0.0` → dashboard/frontend의 Vite 8.0.12 지원 ✅
  - 공식: Vite 8과의 호환성 검증됨 (https://vitest.dev/)

**패키지 버전 확정** (PM 실측값, 재조사 금지):
- `vitest`: ^4.1.9
- `@testing-library/react`: ^16.3.2 (React 19 지원)
- `@testing-library/jest-dom`: 최신
- `happy-dom`: ^20.10.6 (jsdom 29.1.1 대안)
- `@vitejs/plugin-react`: ^6.0.1 (기존 유지, dashboard/frontend는 현재 6.0.1)

**Vitest 환경 선택**:
- jest-dom 플러그인을 사용하므로, happy-dom 선택 (jsdom보다 가볍고 충분)
- globals: true로 describe/it 직접 사용 가능

### 2.2 버전 호환성

| 패키지 | 현재 버전 | 추가 버전 | 호환성 |
|--------|----------|---------|--------|
| Vite | ^8.0.12 | - | vitest 4.1.9 peer 만족 |
| @vitejs/plugin-react | ^6.0.1 | - | vitest와 호환 ✅ |
| React | ^19.2.6 | - | @testing-library/react 16.3.2 지원 ✅ |
| TypeScript | ~6.0.2 | - | vitest 4.1.9와 호환 ✅ |

**회귀 위험**: 기존 build 동작(`tsc -b && vite build`)과 vitest.config 격리되므로 회귀 0 예상.

---

## 3. 영향 범위

### 3.1 직접 영향

**문서 수정 (트랙A)**:
1. `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md`
   - 수정 대상: §2 계층 정의 표(L52-58), §검증 명령 결정(L68-80)
   - 내용: 4종 표준 명령 명시 + "watch 모드 금지(단발 실행)" 규칙 문장 신규 추가

2. `opal/skills/opal-pilot-project-dev/references/wbs-guide.md`
   - 수정 대상: 액션 수용 시나리오 표(L164-170), 유형 검증 명령 표(L280-299)
   - 내용: `npm test -- --testPathPattern={패턴}` → Vitest식(`npm test -- --run` 또는 `npm test -- --run -t "{name}"`) 치환
   - 발생 건수: 17건 (L164-170의 8개 행 + L280-299의 4개 행 + 추가)

3. Cascade 가이드 (조건부):
   - `roadmap-guide.md`: grep으로 Jest식 존재 여부 확정 후 수정
   - `parallel-execution-guide.md`: 동일
   - `opal-pilot-project-dev/SKILL.md`: 동일
   - `op-dev-qa/references/qa-wireframe-guide.md`: 동일
   - `opal-pilot-sdd/SKILL.md`: 동일
   - `opal-pilot-sdd/references/execute-loop-guide.md`: 동일
   - `opal/agents/opal-test-agent/personas/test-engineer.md`: 동일

**코드 수정 (트랙B)**:
1. `dashboard/frontend/package.json`
   - 수정 대상: scripts(L6-11), devDependencies(L52-67)
   - 추가: `test`(vitest run), `lint:fix`(eslint --fix), `typecheck`(tsc --noEmit) 스크립트
   - 추가: vitest, @testing-library/react, @testing-library/jest-dom, happy-dom devDeps

2. `dashboard/frontend/vitest.config.ts` (신규 생성)
   - `environment: 'happy-dom'`, `globals: true`, `setupFiles`, `@vitejs/plugin-react` 플러그인

3. `dashboard/frontend/src/**/*.test.ts(x)` (신규 샘플 테스트)
   - 최소 1개 이상 샘플 테스트 작성 (e.g., `src/__tests__/sample.test.ts`)

### 3.2 간접 영향

**의존 관계**:
1. verification-loop-guide.md 수정 → oppd 오케스트레이터가 참조하는 검증 명령이 변경되므로, oppd 실행 흐름에서 L3a 검증 명령 변화
2. wbs-guide.md 수정 → oppd 태스크 WBS.md 작성 시 예시로 사용되는 검증 명령 표준화
3. dashboard/frontend vitest 셋업 → dashboard/frontend 액션(opd/opds)을 실행할 때 `npm test -- --run` 검증 명령 실제 동작

**소비자/호출자**:
- oppd 오케스트레이터: 검증 루핑(verification-loop-guide.md §2 L68-80) 참조
- opal-task-agent / opal-test-agent: 검증 명령 실행
- WBS.md 작성자: cascade 가이드 예시 참조

### 3.3 영향 범위 요약

- [x] 문서 구조/표준 변경 (guide + wbs-guide)
- [x] 코드/설정 변경 (package.json + vitest.config.ts + 샘플 테스트)
- [ ] DB 스키마 변경
- [ ] API 인터페이스 변경 (검증 명령 문법만 변경, 반환 인터페이스 동일)
- [x] 설정/환경변수 변경 (vitest 환경 변수, npm scripts)
- [ ] 빌드/배포 파이프라인 변경 (소스 수정 후 `~/.opal/` 재배포만, 직접 수정 금지)

---

## 4. 핵심 발견 사항

1. **"watch 모드 금지" 규칙 미명문화** — verification-loop-guide.md(SSOT)에서 테스트 단발 실행 원칙이 명시되지 않았음. L52-80 계층 정의 표에는 L3a 예시(L56)만 있고, "watch 금지" 조항이 없음. 문서에 추가해야 함.

2. **Jest식 `--testPathPattern` 산재(17건)** — wbs-guide.md L164-170(8개 행), L280-299(4개 행) + verification-loop-guide.md L220, L238에서 Jest 문법 명령 반복. Vitest 표준으로 통일 필요.

3. **dashboard/frontend 테스트 러너 부재** — package.json에 test 스크립트·vitest·테스트 파일·vitest.config 모두 미존재. 표준 명문화와 동시에 실제 동작 환경(FE) 셋업 필수.

4. **generic 명령 금지 원칙과의 정합** — wbs-guide.md L46 "generic 명령 금지, 액션별 구체 명령 필수" 원칙 유지. Vitest로 통일하되, 단순 `npm test -- --run`이 아닌 `npm test -- --run -t "{패턴}"` 형태로 액션별 구체성 보장.

5. **플랫폼 독립성 원칙 보존** — PRINCIPLES.md의 "Platform-independent" 원칙에 따라, "watch 모드 금지"는 **원칙** (모든 CI/검증에 필수), `-- --run`은 Vitest **예시** (다른 러너는 동등 옵션 사용). 문서에 명시.

---

## 5. 제약/리스크

| 항목 | 설명 | 심각도 | 근거 |
|------|------|--------|------|
| **H-1: vitest↔Vite8 호환성** | vitest ^4.1.9의 peer 의존성(`vite: ^6.0.0 \|\| ^7.0.0 \|\| ^8.0.0`)이 dashboard/frontend의 Vite 8.0.12를 포함하는지 확인 필요 | 중 | D-8 (Vitest 공식 호환성 매트릭스), D-4 (dashboard/frontend Vite 버전) |
| **H-2: watch 모드 무한대기(CI 문제)** | SSOT(`verification-loop-guide.md`)에 "테스트는 watch 금지(단발 실행)" 규칙이 명문화되지 않으면, CI 자동 검증 시 watch 모드 설정이 실수로 탁 들어갈 수 있음 | 높음 | D-1 L68-80 (검증 명령 결정 규칙에 watch 금지 없음) |
| **H-3: generic 금지 원칙↔표준화 정합** | wbs-guide.md L46의 "generic 명령 금지" 원칙을 위배하지 않으면서 Vitest 표준화를 진행해야 함 | 중 | D-2 L46 (generic 금지 원칙), TASK.md §제약 ②(SSOT 단일 기재) |
| **H-4: SSOT 단일기재 vs cascade 복제** | verification-loop-guide.md(SSOT)에 규칙을 기재하면, wbs-guide.md·roadmap-guide.md 등 cascade 가이드에서는 예시만 정합하고 규칙을 재서술하지 않아야 함 | 중 | TASK.md §제약 ②(SSOT 단일 기재), `.opal/AGENT.md` 금지사항 (하네스 변경 시 SSOT만 수정) |
| **H-5: 기존 build 회귀** | vitest.config.ts 추가가 기존 `npm run build`(tsc -b && vite build) 동작을 변경할 수 없음. vitest는 test 스크립트에만 영향 | 낮음 | D-4 L8 (현행 build 명령), vitest 설정 격리 원칙 |
| **H-6: 배포 경계 위반** | 소스(`opal/`, `dashboard/`) 수정 후 `install`로 재배포해야만 발효됨. `~/.opal/` 배포본을 직접 수정하면 안 됨 | 높음 | `.opal/AGENT.md` 금지사항 (배포 경계), TASK.md §제약 ④ |
| **H-7: 문서 변경이력 누락** | 수정한 모든 문서(verification-loop-guide, wbs-guide 등)에 변경이력 행을 추가해야 함 (KST + 033) | 중 | `.opal/AGENT.md` 금지사항 (변경이력 누락 금지), TASK.md §제약 ⑤ |
| **H-8: cascade 파일 누락** | grep으로 확인하지 않은 파일(roadmap-guide, parallel-execution-guide 등)에 `--testPathPattern`이 있을 수 있음. 모든 파일 scan 필수 | 중 | TASK.md §트랙 A (grep으로 최종 대상 확정) |
| **H-9: Node.js 버전 호환성** | happy-dom 20.10.6이 현재 Node.js 버전과 호환하는지 확인 필요 (dashboard/frontend의 .nvmrc 또는 engines 확인) | 낮음 | D-9 (npm 레지스트리) |
| **H-10: 샘플 테스트의 실제 동작** | vitest.config.ts 작성 후 `npm test -- --run`을 실제 실행했을 때 PASS하는지 검증 필요 (setupFiles 경로, happy-dom 환경, jest-dom 플러그인) | 중 | TASK.md §완료기준 (R-B2 동작검증) |

---

## 6. 기술 컨텍스트

### 6.1 기술 스택

| 카테고리 | 기술 | 버전 | 설명 |
|----------|------|------|------|
| **test runner** | Vitest | ^4.1.9 | Vite 네이티브 테스트 러너, Jest API 호환 |
| **test env** | happy-dom | ^20.10.6 | 경량 DOM 구현, jsdom 대안 |
| **test utils** | @testing-library/react | ^16.3.2 | React 19 지원, 컴포넌트 테스트 |
| **test matchers** | @testing-library/jest-dom | latest | DOM 매처 확장 (toBeInTheDocument 등) |
| **build** | Vite | ^8.0.12 | FE 빌드 도구 (vitest와 피어) |
| **FE framework** | React | ^19.2.6 | UI 프레임워크 |
| **type checker** | TypeScript | ~6.0.2 | 정적 타입 체크 |
| **linter** | ESLint | ^10.3.0 | 스타일 검증 |

### 6.2 추천 스킬

| 스킬 | 용도 |
|------|------|
| `//opds` (Short Task) | 트랙B — dashboard/frontend vitest 셋업(10파일 미만, 단일 모듈) |
| `op-dev-test-scenario` | 트랙B — 샘플 테스트 시나리오 작성(선택) |

### 6.3 추천 MCP

| MCP | 용도 |
|-----|------|
| context7 | vitest 공식 문서·설정 API 조사 |
| WebSearch | 호환성 이슈·최신 변경사항 확인(필요 시) |

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-06-21 | 초기 작성 — 검증 명령 산재 현황 분석(17건 --testPathPattern) + dashboard/frontend vitest 셋업 필요성 + 제약/리스크 10종(H-1~H-10) + 핵심 발견(watch 금지 미명문, generic 정합, SSOT 단일기재 원칙) (033) |
