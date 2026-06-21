# TASK: OPAL 검증 명령 표준 명문화 + dashboard/frontend vitest 셋업

> 작성일: 2026-06-21 | 작업 유형: 개선 | 적용 스킬: opd | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

OPAL의 자동 검증 체계에서 사용하는 검증 명령을 캡틴이 제시한 4종 표준(빌드 `npm run build` / 테스트 `npm test -- --run`(watch 모드 금지) / 린트 `npm run lint:fix` / 타입체크 `npx tsc --noEmit`)으로 명문화하고, 표준이 실제로 동작하도록 `dashboard/frontend`에 vitest를 셋업한다.

## 배경

캡틴이 "테스트 시 위 4종 방식을 적용하고 있는가"를 질의했고, PM이 코드베이스를 대조한 결과 **부분 적용 + 명문화 갭**을 확인했다. 검증 명령 SSOT(`verification-loop-guide.md`)와 cascade 가이드들이 캡틴 표준과 어긋나며, 특히 "watch 모드 금지" 규칙은 어디에도 없고, 정작 `dashboard/frontend`에는 테스트 러너 자체가 없다.

## 배경 분석 (대화에서 도출)

PM이 대화 중 직접 대조한 현황:

| 캡틴 표준 | OPAL 실태 | 판정 | 근거 |
|----------|----------|------|------|
| 빌드 `npm run build` | `npm run build` (L2 계층) | ✅ 일치 | `verification-loop-guide.md:55` / `dashboard/frontend/package.json:8` (`tsc -b && vite build`) |
| 타입체크 `tsc --noEmit` | `npx tsc --noEmit` (L2 계층) | ✅ 일치 | `verification-loop-guide.md:55,157` |
| 테스트 `npm test -- --run` | Jest식 `npm test -- --testPathPattern=…` | ❌ 불일치 | `verification-loop-guide.md:238`, `wbs-guide.md:165~170,280~284`, `roadmap-guide.md:98~102` |
| 린트 `npm run lint:fix` | `npm run lint` (`:fix` 없음) | ❌ 불일치 | `verification-loop-guide.md:54,74` |

추가 확인 사실:
- `-- --run`(Vitest non-watch)·`lint:fix`·"watch 모드 금지" 문구는 **전 코드베이스 grep 0건**이다.
- `dashboard/frontend/package.json`에 `test` 스크립트 없음 · devDeps에 vitest 미설치 · `.test/.spec` 파일·`vitest.config` 0건. 따라서 검증 명령 추론 규칙(`verification-loop-guide.md:73~78`)에 의해 FE 테스트 계층은 현재 **SKIP**되고, build-only + cmux 시각검증으로 운영돼 왔다(`.opal/MEMORY.md` 작업 히스토리 021·023).
- 실무상 테스트는 `opal-test-agent`가 "Bash 단발 실행"으로 돌려(`test-scenario-guide.md:71`) 사실상 비-watch이나, 플래그/규칙으로 강제되지 않는다.

## 확정된 설계 방향 (대화에서 합의)

AskUserQuestion 3건으로 캡틴이 확정한 방향:

1. **명문화 범위 = SSOT + 산재 예시 전부 통일**: `verification-loop-guide.md`(SSOT) + Jest식 예시가 복제된 cascade 가이드(`wbs-guide`·`roadmap-guide`·`parallel-execution-guide`·`test-scenario-guide` + 관련 SKILL/persona)를 모두 Vitest식(`-- --run`, watch 금지)·`lint:fix`로 통일한다.
2. **vitest 셋업 = 표준 문서 + 실제 셋업 함께**: `dashboard/frontend`에 vitest를 도입해 `npm test -- --run`이 실제 동작하게 한다. FE 테스트 정책을 build-only → unit 포함으로 전환한다.
3. **모드 = agentic**, **파이프라인 = `//opd`(Full Task)**.
4. **Git 처리 = 커밋 없이 진행**: 완료된 task 032의 미커밋 변경 위에 본 작업을 누적한다(캡틴이 트레이드오프 인지 후 선택).

## 명확화 결과

> TASK 4요소를 잠근다. 각 요소는 확정값 또는 명시적 "N/A: <사유>"로 채운다 (공란·TBD 금지).

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | 검증 명령 4종 표준을 SSOT+cascade에 명문화(watch 금지 규칙 신규 포함) + `dashboard/frontend` vitest 셋업으로 표준 실동작 확보 | - | `verification-loop-guide.md`가 검증 명령 SSOT |
| 범위 | **포함**: 트랙A(SSOT + cascade 가이드/SKILL/persona Vitest식 통일) + 트랙B(dashboard/frontend vitest 셋업·동작검증). **제외**: dashboard/backend(pytest — 이미 단발 실행이라 watch 이슈 없음), 기존 task 032 변경 정리(별건), CI 훅 연결(후속) | - | FE는 Vite 생태계라 vitest가 자연 정합 |
| 제약 | ①플랫폼 독립성(특정 러너 강제 금지 — watch 금지는 *원칙*, `-- --run`은 Vitest *예시*, 명령은 package.json 추론 구조 유지) ②SSOT 단일 기재(핵심 규칙은 SSOT에만, cascade는 예시 정합) ③generic 검증명령 금지 원칙 유지(`wbs-guide`) ④배포 경계(소스 `opal/`·`dashboard/` 수정 후 install 재배포 / `~/.opal/` 직접 수정 금지) ⑤문서 변경이력 행 추가 의무 ⑥task 032 미커밋 위 누적 | - | `PRINCIPLES.md` Core Stance / `.opal/AGENT.md` 금지사항 |
| 완료기준 | **트랙A**: Jest식 `--testPathPattern` 잔존 0건(grep) + `verification-loop-guide.md`에 watch 금지 규칙 명문 존재 + 4종 명령이 L1/L2/L3a 계층에 반영 + 수정 문서에 변경이력 행. **트랙B**: `dashboard/frontend`에서 `npm test -- --run` 실제 exit 0 + 샘플 테스트 PASS + `npm run lint:fix`·`npx tsc --noEmit`·`npm run build` 정상 + 기존 build 회귀 0 | - | 동작검증은 TEST 단계에서 실측 |

## 요구사항

### 트랙 A — 검증 명령 표준 명문화 (문서 정합)

- [ ] **R-A1 (SSOT 명문화)**: `verification-loop-guide.md` §2 계층 정의 표의 검증 명령 예시를 4종 표준으로 갱신한다 — L1=`npm run lint:fix`, L2=`npm run build`/`npx tsc --noEmit`, L3a=`npm test -- --run`. **무엇을**: 계층별 실행 명령 예시 치환 + "테스트는 watch 모드 금지(단발 실행)" 규칙 문장 신규 추가 + §검증 명령 결정의 스크립트 추론 키 정합. **어디에**: `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` §2·§검증 명령 결정. **왜**: 확정 방향 §1(SSOT). **AC**: 표에 4종이 반영되고, "watch 모드 금지" 규칙 문장이 1개 이상 존재하며, `--testPathPattern` 표현이 이 파일에서 0건이다.
- [ ] **R-A2 (cascade 통일)**: Jest식 `--testPathPattern` 예시가 복제된 cascade 문서들을 Vitest식으로 치환한다. **무엇을**: `--testPathPattern=X` → Vitest식(`-- --run <파일/패턴>` 또는 `-- --run -t "<name>"`)으로 치환, `npm run lint` 예시는 표준화 맥락에 맞춰 정합. **어디에**: `wbs-guide.md`·`roadmap-guide.md`·`parallel-execution-guide.md`·`test-scenario-guide.md` + `opal-pilot-project-dev/SKILL.md`·`op-dev-qa/references/qa-wireframe-guide.md`·`opal-pilot-sdd/SKILL.md`·`opal-pilot-sdd/references/execute-loop-guide.md`·`opal/agents/opal-test-agent/personas/test-engineer.md`(grep으로 최종 대상 확정). **왜**: 확정 방향 §1(산재 예시 전부 통일). **AC**: 위 파일 집합에서 `--testPathPattern` 잔존 0건(grep), generic 명령 금지 원칙 문장은 보존된다.
- [ ] **R-A3 (정합·이력)**: 수정한 가이드/참조 문서에 변경이력 행을 추가하고, CONVENTIONS.md 검증·커밋 규칙과의 정합을 확인한다. **무엇을**: 변경이력 표 행 추가(태스크 033, KST 일시), 필요 시 `docs/CONVENTIONS.md`에 검증 명령 표준 한 줄 등록. **어디에**: 각 수정 문서 변경이력 표 + `docs/CONVENTIONS.md`. **왜**: `.opal/AGENT.md` 금지사항(변경이력 누락 금지). **AC**: 변경한 모든 문서에 033 행이 존재한다.

### 트랙 B — dashboard/frontend vitest 셋업 (코드/설정 + 동작검증)

- [ ] **R-B1 (vitest 셋업)**: `dashboard/frontend`에 vitest와 검증 스크립트를 도입한다. **무엇을**: `package.json` scripts에 `test`(vitest run 기반), `lint:fix`(`eslint . --fix`), `typecheck`(`tsc --noEmit`) 추가 + devDependencies에 vitest(및 필요한 환경 패키지) 추가 + `vitest.config.ts` 생성 + 샘플 테스트 1개 이상 작성. **어디에**: `dashboard/frontend/package.json`·`vitest.config.ts`·`src/**/*.test.ts(x)`. **왜**: 확정 방향 §2. **AC**: `package.json`에 `test`·`lint:fix`·`typecheck` 스크립트가 존재하고, `vitest.config.ts`와 샘플 테스트 파일이 존재한다.
- [ ] **R-B2 (동작검증)**: 4종 명령이 실제로 동작함을 실측한다. **무엇을**: `npm test -- --run`·`npm run lint:fix`·`npm run typecheck`(=`tsc --noEmit`)·`npm run build` 실행. **어디에**: `dashboard/frontend/`. **왜**: 완료기준(동작검증). **AC**: `npm test -- --run`이 watch 없이 종료(exit 0)하며 샘플 테스트 PASS, 나머지 3종 명령도 정상 종료, 기존 `npm run build` 회귀 0.

## 제약 조건

- **플랫폼 독립성**: 검증 명령은 프로젝트 `package.json` 스크립트 기반 추론 구조를 유지한다. "watch 모드 금지(단발 실행)"는 **원칙**으로 명문화하고, `-- --run`은 Vitest **예시**로 둔다. 특정 테스트 러너를 하드 강제하지 않는다 (`PRINCIPLES.md` Core Stance — Platform-independent).
- **SSOT 단일 기재**: 핵심 규칙(watch 금지)은 SSOT(`verification-loop-guide.md`)에만 둔다. cascade 가이드의 액션 예시는 SSOT를 따르는 *예시 정합*이며 규칙을 재서술하지 않는다 (`.opal/AGENT.md` 금지사항 — 하네스 변경 시 SSOT 수정).
- **generic 검증명령 금지 보존**: `wbs-guide.md`의 "액션별 구체 수용 시나리오 필수, generic 명령 금지" 원칙을 훼손하지 않는다. `npm test -- --run` 단독을 generic 명령으로 강제하지 않는다.
- **배포 경계**: 소스(`opal/`, `dashboard/`)를 수정한 뒤 install로 재배포해야 동작이 발효된다. `~/.opal/` 배포본을 직접 수정하지 않는다 (`.opal/AGENT.md` 금지사항).
- **문서 변경이력**: 스킬·참조 문서 수정 시 변경이력 표에 행을 추가한다 (KST 일시 + 태스크 033).
- **Git 베이스**: 완료된 task 032의 미커밋 변경 위에 누적한다 (캡틴 결정).

## 기술 스택

- **Framework 문서**(트랙 A): Markdown — `opal/skills/opal-pilot-project-dev/references/`, `opal/skills/op-dev-*`, `opal/agents/opal-test-agent/`
- **Console FE**(트랙 B): React 19, TypeScript ~6.0, Vite 8, Tailwind 4, shadcn/ui, ESLint 10 → **vitest** 도입 (Vite 생태계 정합) — `dashboard/frontend/`

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | verification-loop-guide.md | `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` | 검증 명령 SSOT — 계층 정의·명령 결정 (트랙A 핵심) |
| D-2 | 설계 | wbs-guide.md | `opal/skills/opal-pilot-project-dev/references/wbs-guide.md` | 수용 시나리오 검증 명령(Jest식 다수)·generic 금지 원칙 |
| D-3 | 설계 | roadmap-guide.md | `opal/skills/opal-pilot-project-dev/references/roadmap-guide.md` | 액션 검증 명령 예시 |
| D-4 | 설계 | parallel-execution-guide.md | `opal/skills/opal-pilot-project-dev/references/parallel-execution-guide.md` | 병렬 액션 검증 명령 예시 |
| D-5 | 설계 | test-scenario-guide.md | `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | 테스트 도구(M1) 단발 실행·vitest 언급 |
| D-6 | 소스 | package.json (FE) | `dashboard/frontend/package.json` | vitest 셋업 대상 (트랙B) |
| D-7 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 검증·커밋 규칙 정합 |
| D-8 | 설계 | test-engineer.md | `opal/agents/opal-test-agent/personas/test-engineer.md` | tsc --noEmit 등 검증 명령 페르소나 |
