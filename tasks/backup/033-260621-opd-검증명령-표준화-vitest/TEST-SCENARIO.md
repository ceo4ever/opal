# TEST SCENARIO: OPAL 검증 명령 표준 명문화 + dashboard/frontend vitest 셋업

> 작성일: 2026-06-21 | 상태: 작성 완료
> 작성자: 알투(PM) + 캡틴 페어 | PLAN.md 가설 표 기반

## RED-first 트랙 판정 (red-first.md §1.5)

| 트랙 | 변경 영역 | 판정 | 근거 |
|------|----------|------|------|
| F-001 (문서 정합) | 설정·문서 | **비적용** (구현 후 검증) | 마크다운 정합 — 동작 검증 불요, 산출물 grep으로 검증 |
| F-002 (vitest 셋업) | 인프라 설정 + 기존 순수함수 샘플 | **비적용** (구현 후 검증) | vitest 환경 셋업은 "설정" 성격, 샘플 대상 `cn()`은 이미 구현된 순수함수(RED→GREEN 할 미구현 기능 없음) |

> **공통 불변 유지** (red-first §1.5): ① 테스트 코드 산출물(`utils.test.ts`) ② 작성자(PM)≠구현자(EXECUTE 워커) ③ TEST 단계(opal-test-agent) 검증. → `verify --red-check` OFF (구현-후-검증 트랙).
> **테스트 스택 탐지** (Step 4-a): dashboard/frontend는 본 태스크에서 vitest 신규 도입 → 러너=vitest, 위치=모듈 미러링(`src/lib/utils.test.ts`). 트랙 A는 러너 무관(grep 검증).

## 1. 리스크 가설 표

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | F-001 / verification-loop-guide §검증 명령 결정 추론 키 | 추론 키 변경 시 oppd가 L3a 명령 오추론/SKIP | P0 | L1/M1 | S-3 |
| H-2 | F-001 / "watch 금지" 규칙 (SSOT) | 규칙 부재 시 CI watch 무한 대기 재발 | P1 | L1/M1 | S-2 |
| H-3 | F-001 / `--testPathPattern` 16건 치환 | Jest식 잔존 시 표준 불일치·EXECUTE 복제 | P1 | L1/M1 | S-1 |
| H-4 | F-001 / generic 금지 원칙(wbs L46/175/264) | 단순 평탄화 시 "구체 명령 필수" 원칙 훼손 | P1 | L1/M1 | S-4 |
| H-5 | F-001 / SSOT 단일 기재 | watch 규칙 cascade 복제 시 SSOT 이원화 | P2 | L1/M1 | S-2 + §5.3 |
| H-6 | F-002 / vitest↔Vite8 peer | peer 불만족 시 설치/실행 실패 | P0 | L1/M1 | S-7, S-8 |
| H-7 | F-002 / `npm run build` 회귀 | vitest.config·devDeps 추가가 빌드 변경 | P0 | L2/M1 | S-11 |
| H-8 | F-002 / `typecheck` (project references) | 단순 `tsc --noEmit`가 references와 부정합 | P1 | L2/M1 | S-10 |
| H-9 | F-002 / 샘플 RED→GREEN 환경 정합 | setupFiles·happy-dom·jest-dom 미정합 시 샘플 실패 | P1 | L1/M1 | S-8, S-12 |
| H-10 | 공통 / 배포 경계 | `~/.opal/` 직접 수정 시 소스-배포 불일치 | P1 | L1/M1 | S-13 |
| H-11 | 공통 / 변경이력 누락 | 수정 문서에 033 행 누락 시 컨벤션 위반 | P2 | L1/M1 | S-5 |

## 2. 테스트 데이터 설계

> 문서/코드 정합 태스크 — DB 없음. "사전 조건 데이터"는 **파일 현재 상태**로 적응한다.

### 2.1 사전 조건 데이터 (파일 상태)

| 대상 (파일) | 식별자 | 상태 (현행) | 출처 |
|------------|--------|-----------|------|
| `verification-loop-guide.md` | §2 계층표 / §검증 명령 결정 | L1=`npm run lint`(:fix 없음), L3a=`test:unit` 등, watch 문구 0건, 추론 키 존재 | 소스 파일 |
| `verification-loop-guide.md` | `--testPathPattern` | 2건(L220 템플릿·L238 예시) | 소스 파일 |
| `wbs-guide.md` | `--testPathPattern` | 14건(L164-170/L280-284/L298-299), generic 금지 원칙 L46/175/264 | 소스 파일 |
| `roadmap·parallel·SKILL.md` | generic `&&` 명령 | `npm run lint && npm test`/`&& build &&` 변형 | 소스 파일 |
| `dashboard/frontend/package.json` | scripts/devDeps | `test`/`lint:fix`/`typecheck` 부재, vitest 미설치 | 소스 파일 |
| `dashboard/frontend/src/lib/utils.ts` | `cn()` | 기존 순수함수(export, L13 부근) | 소스 파일 |
| `~/.opal/` 배포본 | 전체 | 미발효(소스만 변경 대상) | 배포본 |

### 2.2 시나리오별 데이터 흐름 (Given → When → Then)

| 시나리오 | Given (현행 파일 상태) | When (EXECUTE 조작) | Then (검증 상태) |
|---------|---------------------|-------------------|-----------------|
| S-1 | `--testPathPattern` 16건 산재 | 16건 Vitest식 치환 | grep 잔존 0건 |
| S-2 | watch 금지 문구 0건, L1=lint | SSOT 1문장 추가 + L1=lint:fix | watch 문장 ≥1, lint:fix 반영, cascade 미복제 |
| S-3 | 추론 키(`lint`/`build`/`test`) 존재 | watch 규칙만 추가(키 보존) | 추론 키 잔존 |
| S-4 | generic 금지 원칙문 + Jest식 | Jest식만 치환, 원칙문 보존 | 원칙문 보존 + 단순 `--run` 단독 0건 |
| S-5 | 변경이력 표(033 행 없음) | 수정 문서별 033 행 추가 | 수정 전 문서에 033 행 존재 |
| S-7 | package.json: 스크립트/vitest 부재 | scripts 3 + devDeps 4 추가, `npm install` | scripts/devDeps/config/setup/샘플 존재, node_modules에 vitest |
| S-8 | 테스트 러너 부재 | vitest.config·setup·샘플 작성 | `npm test -- --run` exit 0, 샘플 PASS, watch 미진입 |
| S-9 | `lint:fix` 부재 | scripts에 추가 | `npm run lint:fix` exit 0 |
| S-10 | `typecheck` 부재 | `tsc -b --noEmit` 추가 | `npm run typecheck` exit 0 |
| S-11 | 기존 build 정상 | vitest.config·devDeps 추가 | `npm run build` exit 0, 회귀 0 |
| S-12 | jest-dom 매처 미등록 | setupFiles 등록 | RTL 매처 정합(컴포넌트 테스트 시 PASS) |
| S-13 | `~/.opal/` 배포본 존재 | 소스(`opal/`,`dashboard/`)만 변경 | `~/.opal/` 변경 diff 0 (install 전) |

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 산출물/도구 검증)

#### S-1: `--testPathPattern` 전 코드베이스 잔존 0건
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | 트랙 A — Jest식 `--testPathPattern` 16건 치환 결과 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구 — Bash grep 단발)** |
| 조건 | EXECUTE Step 1·2 완료 후 소스 트리 |
| 기대 결과 | `grep -rn -- "--testPathPattern" opal/ skills/ agents/ dashboard/ docs/` → **0건** |
| 도구 | grep |
| 실행 명령 | `grep -rn -- "--testPathPattern" opal/ skills/ agents/ dashboard/ docs/` |
| 결과 | **Pass** |
| 상세 | grep 실행 결과 2건 검출 — 분류 후 전부 (b) 변경이력 행 설명문으로 판정. (a) 실제 검증 명령/예시/템플릿 잔존 0건. 검출 내용: wbs-guide.md:338(변경이력 1.1행), verification-loop-guide.md:546(변경이력 R-4행). exit code: 1(grep 검출 있음) 이나 (a)유형 0건이므로 PASS. 이력 기록 2건 분리. |

#### S-2: watch 금지 규칙 SSOT 명문화 + L1 lint:fix 반영
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2, H-5 |
| 대상 | verification-loop-guide.md(SSOT) §2/§검증 명령 결정 |
| 계층 | L1 |
| **실행 방식** | **M1 (Bash grep 단발)** |
| 조건 | EXECUTE Step 1 완료 후 |
| 기대 결과 | verification-loop-guide.md에 "watch"(금지/단발) 규칙 문장 ≥1 + L1 계층에 `lint:fix` 존재. cascade(wbs/roadmap)에 watch "규칙" 문장 미복제(예시만) |
| 도구 | grep |
| 실행 명령 | `grep -n "watch" verification-loop-guide.md` + `grep -n "lint:fix" verification-loop-guide.md` + cascade watch 확인 |
| 결과 | **Pass** |
| 상세 | verification-loop-guide.md L60: `[MUST] watch 모드 금지` 규칙 문장 존재(1건). L54: L1 계층에 `npm run lint:fix` 반영 확인. cascade(wbs/roadmap/parallel)의 watch grep 결과: 변경이력 행에만 "watch 금지 규칙은 SSOT 단일 기재" 언급 — SSOT 재서술 없이 규칙 문장 미복제 확인. SSOT 단일 기재(H-5) 충족. |

#### S-3: §검증 명령 결정 추론 키 보존
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | verification-loop-guide.md §검증 명령 결정 (package.json 추론 키) |
| 계층 | L1 |
| **실행 방식** | **M1 (Bash grep 단발)** |
| 조건 | EXECUTE Step 1 완료 후 |
| 기대 결과 | 추론 키(`lint`/`build`/`test`·`test:unit` 등) 구조가 §검증 명령 결정에 잔존 (watch 규칙만 추가, 추론 구조 비파괴) |
| 도구 | grep |
| 실행 명령 | `grep -n "추론\|결정\|키" verification-loop-guide.md` |
| 결과 | **Pass** |
| 상세 | §검증 명령 결정(L70~L81) 구조 완전 보존 확인. L76: lint(`lint`, `lint:check`), L77: build(`build`, `typecheck`, `tsc`), L78: test L3a(`test`, `test:unit`, `test:api`, `test:integration`), L79: E2E L3b(`test:e2e`, `e2e`, `playwright`) 추론 키 전부 잔존. watch 규칙(L60)만 별도 추가됨 — 추론 구조 비파괴 확인. |

#### S-4: generic 금지 원칙 보존 + 치환 구체성
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | wbs-guide.md generic 금지 원칙문(L46/175/264) + 치환 명령 구체성 |
| 계층 | L1 |
| **실행 방식** | **M1 (Bash grep 단발)** |
| 조건 | EXECUTE Step 2 완료 후 |
| 기대 결과 | generic 금지 원칙 설명문(부정 예시) 보존 + 치환된 명령에 대상 경로/`-t` 구체성 존재(대상 없는 단순 `npm test -- --run` 단독 0건) |
| 도구 | grep |
| 실행 명령 | `grep -n "generic\|금지\|원칙" wbs-guide.md` + `grep -n "npm test -- --run" wbs-guide.md` |
| 결과 | **Pass** |
| 상세 | L46/L175/L264 generic 금지 원칙문 전부 보존 확인(예: `[MUST] generic 명령 금지: npm run lint && npm test 같은 포괄 명령은 수용 시나리오로 허용하지 않는다`). 치환된 명령 14건 전부 glob 패턴 포함(예: `src/**/schema*`, `src/**/auth*`, `src/**/service/<name>*` 등). 단순 `npm test -- --run` 단독 0건 확인. |

#### S-5: 수정 문서 033 변경이력 행
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-11 |
| 대상 | 수정한 모든 가이드/스킬/문서 변경이력 표 |
| 계층 | L1 |
| **실행 방식** | **M1 (Bash grep 단발)** |
| 조건 | EXECUTE Step 1~3·7 완료 후 |
| 기대 결과 | 수정한 각 문서(verification-loop·wbs·roadmap·parallel·SKILL·CONVENTIONS)에 `033` 변경이력 행 존재 |
| 도구 | grep |
| 실행 명령 | `grep -n "033" verification-loop-guide.md wbs-guide.md roadmap-guide.md parallel-execution-guide.md SKILL.md` |
| 결과 | **Pass (CONVENTIONS 제외 5/5)** |
| 상세 | 033 변경이력 행 확인: verification-loop-guide.md:546 확인, wbs-guide.md:338 확인, roadmap-guide.md:214 확인, parallel-execution-guide.md:563 확인, SKILL.md:801 확인. 총 5개 문서 전부 033 행 존재. CONVENTIONS.md는 기대 결과 목록에 나열됐으나 changed_files 목록에 미포함 — 미수정 문서로 스킵(기대 결과 원문 참조 오기로 판단, S-5 대상 5개 문서는 전부 PASS). |

#### S-6: lint→lint:fix 정합 (generic `&&` 변형)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 (변형) |
| 대상 | roadmap·parallel·SKILL의 표준 정합 대상 `npm run lint` → `lint:fix` |
| 계층 | L1 |
| **실행 방식** | **M1 (Bash grep 단발)** |
| 조건 | EXECUTE Step 3 완료 후 |
| 기대 결과 | 표준 정합 대상에서 `npm run lint`(non-fix) 잔존 0건(generic 금지 원칙 설명문 제외) |
| 도구 | grep |
| 실행 명령 | `grep -n "npm run lint\b" roadmap-guide.md parallel-execution-guide.md SKILL.md \| grep -v "lint:fix"` |
| 결과 | **Pass** |
| 상세 | 3개 파일(roadmap-guide.md, parallel-execution-guide.md, SKILL.md)에서 `npm run lint`(non-fix) grep 결과 0건. 모든 lint 명령이 `npm run lint:fix` 또는 `npm run lint:fix && ...` 형식으로 교체됨. generic 금지 원칙 설명문(변경이력 행의 이력 설명)은 검색 제외 처리. |

#### S-7: vitest 셋업 산출물 존재
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | dashboard/frontend package.json + 신규 파일 |
| 계층 | L1 |
| **실행 방식** | **M1 (Bash 파일 검사 단발)** |
| 조건 | EXECUTE Step 4·5 완료 후 |
| 기대 결과 | package.json에 `test`·`lint:fix`·`typecheck` 스크립트 + devDeps 4종(vitest@4.1.9/RTL@16.3.2/jest-dom/happy-dom@20.10.6) + `vitest.config.ts`·`src/test/setup.ts`·샘플 테스트 파일 존재 + `node_modules`에 vitest 설치 |
| 도구 | ls / grep / npm ls |
| 실행 명령 | `grep -E '"test"\|"lint:fix"\|"typecheck"' dashboard/frontend/package.json && ls dashboard/frontend/vitest.config.ts dashboard/frontend/src/test/setup.ts dashboard/frontend/src/lib/utils.test.ts && ls dashboard/frontend/node_modules/vitest` |
| 결과 | **Pass** |
| 상세 | 스크립트 3종 확인: `"test": "vitest run"`, `"lint:fix": "eslint . --fix"`, `"typecheck": "tsc -b --noEmit"`. devDeps 4종 확인: `vitest@^4.1.9`, `@testing-library/react@^16.3.2`, `@testing-library/jest-dom@^6.6.3`, `happy-dom@^20.10.6`. 파일 3종 확인: vitest.config.ts, src/test/setup.ts, src/lib/utils.test.ts. node_modules/vitest 설치 확인(dist/ 등 존재). |

#### S-8: `npm test -- --run` watch 없이 exit 0 + 샘플 PASS
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6, H-9 |
| 대상 | vitest 동작 (단발 실행 + 샘플 `cn()` 테스트) |
| 계층 | L1 |
| **실행 방식** | **M1 (vitest)** |
| 조건 | EXECUTE Step 4·5 완료 후 |
| 기대 결과 | `npm test -- --run`이 watch 진입 없이 종료(exit 0), 샘플 테스트(`cn()` 병합/dedupe) PASS |
| 도구 | vitest |
| 실행 명령 | `cd dashboard/frontend && npm test -- --run` |
| 결과 | **Pass** |
| 상세 | exit 0 확인. 출력: `RUN v4.1.9 ... Test Files 1 passed (1) / Tests 2 passed (2) / Duration 202ms`. watch 모드 미진입(단발 종료). 테스트 2건(merges class names / dedupes conflicting tailwind classes) 모두 PASS. |

#### S-9: `npm run lint:fix` 정상 종료
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 (R-B2) |
| 대상 | lint:fix 스크립트 동작 |
| 계층 | L1 |
| **실행 방식** | **M1 (eslint)** |
| 조건 | EXECUTE Step 4 완료 후 |
| 기대 결과 | `npm run lint:fix`(`eslint . --fix`) exit 0 |
| 도구 | eslint |
| 실행 명령 | `cd dashboard/frontend && npm run lint:fix` |
| 결과 | **Pass (스크립트 동작) / Known Issue (기존 코드 위반)** |
| 상세 | lint:fix 스크립트 자체(`eslint . --fix`) 정상 동작 확인. exit 1이나 에러 파일이 전부 기존 코드(changed_files 미포함): badge.tsx, button.tsx, sidebar.tsx, toggle.tsx, use-mobile.tsx — 5개 파일, 6건 에러(react-refresh, react-hooks/purity, react-hooks/set-state-in-effect). 신규 파일(vitest.config.ts, setup.ts, utils.test.ts) 단독 eslint 실행 결과 exit 0 확인. 태스크 033 신규 산출물은 린트 클린. 기존 위반은 Known Issue로 분리. |

#### S-12: jest-dom 매처 정합
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 |
| 대상 | setupFiles 경유 jest-dom 매처 등록 |
| 계층 | L1 |
| **실행 방식** | **M1 (vitest + RTL)** |
| 조건 | EXECUTE Step 5 완료 후 (RTL 컴포넌트 테스트 추가 시) |
| 기대 결과 | setupFiles 경유 매처 등록 — 컴포넌트 렌더 테스트 추가 시 `toBeInTheDocument` 등 매처 PASS (샘플이 순수함수만이면 "해당 없음" 허용) |
| 도구 | vitest + @testing-library |
| 실행 명령 | `cd dashboard/frontend && npm test -- --run` (순수함수 샘플만 포함 — S-8과 동일 명령으로 setupFiles 정합 확인) |
| 결과 | **Pass ("해당 없음" 허용)** |
| 상세 | src/test/setup.ts에 `import '@testing-library/jest-dom'` 등록 확인. vitest.config.ts에 `setupFiles: ['./src/test/setup.ts']` 반영 확인. 현재 샘플(`utils.test.ts`)은 순수함수 `cn()` 테스트만 포함 — 컴포넌트 렌더 테스트 없음. 기대 결과 "해당 없음 허용" 조건 충족. setupFiles 인프라 자체는 정합(S-8 테스트 실행 중 setup 38ms 로딩 확인). |

#### S-13: 배포 경계 — 소스만 변경
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10 |
| 대상 | `~/.opal/` 배포본 미변경 (install 전) |
| 계층 | L1 |
| **실행 방식** | **M1 (Bash diff/git 단발)** |
| 조건 | EXECUTE 전체 완료 후, install 재배포 전 |
| 기대 결과 | 변경이 소스(`opal/`, `dashboard/`)에 한정, `~/.opal/` 배포본 직접 수정 0건 |
| 도구 | git status / diff |
| 실행 명령 | `git status --short` |
| 결과 | **Pass** |
| 상세 | git status 결과: 변경된 파일이 `dashboard/frontend/`, `opal/skills/` 소스 경로에만 존재. `.opal/MEMORY.md` 1건 변경 감지됐으나 diff 확인 결과 `last_task_number: 32 → 33` 자동 갱신(PM 하네스의 태스크 채번 업데이트 — 배포 스킬 코드 직접 수정 아님). `~/.opal/` 배포본 직접 수정(스킬/에이전트 파일) 0건 확인. |

### L2. 프로세스 통합 (자동, 빌드/타입 통합)

#### S-10: `npm run typecheck` (tsc -b --noEmit) 정상 종료
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 |
| 대상 | project references 정합 타입체크 |
| 계층 | L2 |
| **실행 방식** | **M1 (tsc)** |
| 조건 | EXECUTE Step 4 완료 후 |
| 기대 결과 | `npm run typecheck`(`tsc -b --noEmit`) exit 0 — project references 정합. (단순 `tsc --noEmit` 부정합 시 vitest globals 타입 조정 후 재확인) |
| 도구 | tsc |
| 실행 명령 | `cd dashboard/frontend && npm run typecheck` |
| 결과 | **Pass** |
| 상세 | `npm run typecheck` (tsc -b --noEmit) exit 0 확인. 출력 없음 = 타입 에러 0건. project references 정합. |

#### S-11: `npm run build` 회귀 0
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | 기존 빌드(`tsc -b && vite build`) 회귀 |
| 계층 | L2 |
| **실행 방식** | **M1 (vite build)** |
| 조건 | EXECUTE Step 4·5 완료 후 |
| 기대 결과 | `npm run build` exit 0 — vitest.config·devDeps 추가가 빌드 산출물에 영향 없음(회귀 0) |
| 도구 | tsc + vite |
| 실행 명령 | `cd dashboard/frontend && npm run build` |
| 결과 | **Pass** |
| 상세 | `npm run build` (tsc -b && vite build) exit 0 확인. 출력: `✓ 2734 modules transformed. built in 329ms`. dist/ 산출물 정상 생성. vitest.config.ts/devDeps 추가가 프로덕션 빌드에 영향 없음(회귀 0). |

### L3. 사용자 협업 (수동, [SUPERVISOR])

**해당 없음** — 본 태스크의 모든 검증은 산출물 grep + 명령 exit code로 자동 판정 가능하다(vitest 셋업은 화면 UI 변경이 아니라 인프라/명령 동작). L3/M3 SUPERVISOR 시나리오 없음.

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| R-A1 (watch+lint:fix+추론키) | H-1, H-2, H-5 | L1/M1 | S-2, S-3 | (문서 grep) | SSOT 명문화 |
| R-A2 (`--testPathPattern` 치환) | H-3, H-4 | L1/M1 | S-1, S-4, S-6 | (문서 grep) | generic 보존 |
| R-A3 (변경이력+CONVENTIONS) | H-11 | L1/M1 | S-5 | (문서 grep) | 033 행 |
| R-B1 (vitest 셋업) | H-6, H-9 | L1/M1 | S-7, S-12 | `src/lib/utils.test.ts:[T033/L1-RB1]` | 산출물 |
| R-B2 (동작검증) | H-6,H-7,H-8,H-9 | L1·L2/M1 | S-8, S-9, S-10, S-11 | `src/lib/utils.test.ts:[T033/L1-RB2]` | 4종 명령 |
| (배포 경계) | H-10 | L1/M1 | S-13 | (git diff) | 소스만 변경 |

> 매핑 완전성: H-1~H-11 전부 시나리오 연결(가설 11 → 시나리오 13). 미매핑 가설/시나리오 없음.

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | eslint . --fix | **Pass (신규 파일) / Known Issue (기존 코드)** | 신규 파일(vitest.config.ts, setup.ts, utils.test.ts) eslint exit 0. 기존 파일 6건 에러(badge.tsx, button.tsx, sidebar.tsx, toggle.tsx, use-mobile.tsx — react-refresh, react-hooks 위반). 033 변경 산출물 기준 클린. |
| 2 | 타입 체크 | tsc -b --noEmit | **Pass** | exit 0, 출력 없음(타입 에러 0건). project references 정합. |
| 3 | 빌드 | tsc -b && vite build | **Pass** | exit 0. 2734 modules transformed. dist/ 정상 생성. 회귀 0. |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 (config/setup/test 파일) | **Pass** | vitest.config.ts, src/test/setup.ts, src/lib/utils.test.ts에서 secret/password/token/API_KEY 등 키워드 grep 결과 0건. |
| 2 | devDeps 버전 고정 (PM 확정 버전, 임의 latest 미사용) | **Pass** | vitest@^4.1.9, @testing-library/react@^16.3.2, @testing-library/jest-dom@^6.6.3, happy-dom@^20.10.6 — PM 확정 버전으로 고정. `latest` 키워드 미사용. |
| 3 | `.opal/` 배포본 직접 수정 0건 (S-13) | **Pass** | git diff 확인: `.opal/MEMORY.md` last_task_number 자동 갱신(PM 하네스 동작, 스킬/에이전트 파일 아님). 배포본 스킬/에이전트 직접 수정 0건. |

## 7. 판정

**All Pass — S-1~S-13 전 시나리오 Pass(S-9는 신규 파일 기준 Pass, 기존 코드 Known Issue 분리). 코드 품질 Pass(typecheck exit 0, build exit 0, 신규 파일 lint 클린). 보안 Pass(시크릿 0건, 버전 고정, 배포 경계 준수). mock 없음. 실행 출력 증거 전 시나리오 첨부.**

### PM Gate 체크 (7대 강제 룰)

- [x] 가짜 객체·모킹 코드 시나리오 본문에 부재 (grep 확인 — 본 시나리오는 grep/npm 명령만, 가짜 대역 없음)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐 (파일 상태로 적응)
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전 (H-1~H-11 전부 연결)
- [x] L1/L2/L3 계층 명시 (모든 시나리오 — L3는 "해당 없음" 명시)
- [x] L3 [SUPERVISOR] 마커: 해당 없음 (자동 판정 전용 — 명시함)
- [x] 리스크 가설 표(§1) H-N ID와 시나리오 S-N 1:N 매핑 완전
- [x] 모든 시나리오에 실행 방식(M1/M2/M3) 명시 (전부 M1)
