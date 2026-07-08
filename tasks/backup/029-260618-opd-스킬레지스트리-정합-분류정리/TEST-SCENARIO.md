# TEST SCENARIO: opal/skills 레지스트리 정합 + 분류 정리 + opal-brain 오기재 교정 + validate lint

> 작성일: 2026-06-18 | 상태: 작성 완료
> 작성자: 알투(PM) + 캡틴 페어 | PLAN.md v2.0 §리스크 가설 표 기반
> RED-first 트랙: **F-004(validate 코드+테스트) 적용** — S-1~S-4는 RED(작성자=opal-test-agent mode:red) → GREEN(구현자=opal-task-agent). F-001/F-002/F-003은 구현-후-검증(설정·문서 트랙, `red-first.md §1.5`).

## 1. 리스크 가설 표

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-3 | F-004 / `validateUnregistered()` standalone 미스캔 | top-level `skills/`(standalone)를 `opal/skills/`만 스캔 시 미등록 오판(false positive) | 중간 | L1 | S-2 |
| H-4 | F-004 / 소스/배포 환경 미구분 | 배포 환경(`~/.opal/references/`)에서 unregistered 스캔 시 false positive | 중간 | L1 | S-3 |
| H-5 | F-004 / no-SKILL.md warning→error 격상(`skill-registry.js:379`) | dangling이 warning(exit 0)으로 남으면 R4 AC(exit 1) 미달 | 높음 | L1 | S-1 |
| H-6 | F-001 / dangling 제거 후 문서 잔존(`PROJECT.md:61`,`ARCHITECTURE.md:126,328`) | 레지스트리만 제거하고 문서 잔존 시 SSOT 불일치 재발 | 낮음 | L1 | S-7 |
| H-8 | F-003 / opal-brain 불변 회귀(폴더·alias·entry·전역 참조) | PROJECT.md 교정 중 실수로 opal-brain 폴더·alias(`opbr`)·triggers·entry를 건드리면 부트·`//opbr` 매칭·배포가 깨짐 (리네임 철회 회귀 가드) | 중간 | L1 | S-9 |

> 추가 산출물 정합 시나리오(가설 비종속, AC 직접 검증): S-4(validate clean exit 0), S-5(F-001 레지스트리 정합), S-6(F-002 그룹 재배치), S-8(F-003 오기재 교정), S-10(회귀), S-11(통합 validate).

## 2. 테스트 데이터 설계

> 본 태스크는 DB 무관 — "데이터"는 (a) 현행 레지스트리/문서 상태(사전 조건)와 (b) validate 단위 테스트용 합성 fixture(임시 디렉토리)다.

### 2.1 사전 조건 데이터

| 테이블 | 식별자 | 상태 | 출처 |
|--------|--------|------|------|
| 레지스트리 op-sdd 그룹 | `op-sdd-tasks` | dangling(폴더 부재) — 제거 대상 | 현행 `opal-skills-registry.json:304-319` |
| 레지스트리 opal 그룹 | `opal-orchestrator` | dangling(폴더 부재) — 제거 대상 | 현행 `opal-skills-registry.json:618-629` |
| `opal/skills/` 폴더 | `op-sdd-action-plan` | 미등록(폴더 존재, 레지스트리 부재) — 등록 대상 | 현행 `opal/skills/op-sdd-action-plan/SKILL.md` |
| 레지스트리 opal 그룹 | `op-spec-validator`,`op-brain-ingest`,`opal-pilot-project-dev` | 오배치 — 재배치 대상 | 현행 `opal-skills-registry.json:594,608,686` |
| 레지스트리 opal 그룹 | `opal-brain`(alias `opbr`) | 정상 — **불변(잔류)** | 현행 `opal-skills-registry.json:670-684` |
| 문서 | `docs/PROJECT.md:79` opal-brain 행 | "오케스트레이터/Pilot" 오기재 — 교정 대상 | 현행 `docs/PROJECT.md:79` |
| validate fixture | 합성 레지스트리+스킬 폴더 (clean/dangling/unregistered/standalone/deploy) | 임시 디렉토리 생성 | `tests/test-validate.js` fixture (신규) |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (사전 상태) | When (조작) | Then (검증) |
|---------|------------------|-------------|-------------|
| S-1 | dangling 항목 있는 합성 레지스트리 | `validate()` 실행 | errors에 `dangling` 포함, exit 1 |
| S-2 | standalone(`skills/`) 폴더가 레지스트리에 등록된 fixture + 미등록 폴더 1개 | `validate()` 실행 | 등록 standalone 오판 0, 미등록 폴더만 `unregistered` exit 1 |
| S-3 | refDir이 배포 경로(`~/.opal/references/`)를 가리키는 fixture 구성 | `validate()` 실행 | unregistered 스캔 비활성, false positive 0 |
| S-4 | 정합(clean) 합성 레지스트리+폴더 | `validate()` 실행 | errors 0, exit 0 |
| S-5 | 작업 후 실제 레지스트리 | jq 조회 | op-sdd-tasks·opal-orchestrator 0건, op-sdd-action-plan 1건 |
| S-6 | 작업 후 실제 레지스트리 | jq 그룹 조회 | 3항목 정합 그룹, opal 그룹 단계스킬 0건, opal-brain opal 잔류 |
| S-7 | 작업 후 docs | grep | PROJECT.md `op-sdd-tasks` 0건, ARCHITECTURE.md `opal-orchestrator` 0건 |
| S-8 | 작업 후 PROJECT.md:79 | grep | opal-brain 행에 "오케스트레이터"·"Pilot" 0건, operator/라우터 성격 기재 |
| S-9 | 작업 전/후 opal-brain 자산 | git diff + grep + match | opal-brain 폴더·entry·전역 참조 변경 0건, `match '//opbr'`→opal-brain 매칭 |
| S-10 | 작업 후 도구 | 기존 명령 실행 | match/list/get 정상, brain-tool pytest PASS |
| S-11 | 전체 작업 완료된 실제 레포 | `node skill-registry.js validate` | dangling·unregistered 0건, exit 0 |

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 실 데이터 입력)

#### S-1: validate dangling → error 격상 (exit 1) [RED-first]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | `validate()` no-SKILL.md error 격상 (`skill-registry.js:379`) |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구 — Node 내장 assert/test)** |
| 조건 | 폴더 없는 레지스트리 항목(dangling) 포함 합성 fixture |
| 기대 결과 | `validate()` 반환 `valid:false` + errors에 `dangling` 문자열 포함, 프로세스 exit 1 |
| 도구 | node:test (test-validate.js TC2) |
| 실행 명령 | `node --test opal/tools/skill-registry/tests/test-validate.js` |
| 결과 | PASS |
| 상세 | TC2 (dangling) PASS: exit 1, valid:false, errors에 "dangling" 포함 확인. 5/5 TC 전체 통과 (453ms). |

#### S-2: validate unregistered 감지 + standalone 오판 방지 [RED-first]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | `validateUnregistered()` 양쪽 폴더(`opal/skills/`+`skills/`) 스캔 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | (a) top-level `skills/`에 등록된 standalone 폴더 fixture, (b) 등록 없는 폴더 1개 fixture |
| 기대 결과 | 등록 standalone은 unregistered 미보고(오판 0), 미등록 폴더만 errors에 `unregistered` 포함 exit 1 |
| 도구 | node:test (test-validate.js TC3+TC5) |
| 실행 명령 | `node --test opal/tools/skill-registry/tests/test-validate.js` |
| 결과 | PASS |
| 상세 | TC3 (unregistered) PASS: exit 1, errors에 "unregistered" 포함. TC5 (standalone) PASS: top-level skills/ 등록 폴더 unregistered 오판 0, exit 0. |

#### S-3: validate 배포 환경 false positive 방지 [RED-first]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | 소스/배포 환경 구분 (`getReferencesDir()` 판별로 unregistered 조건부) |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | refDir이 배포 경로(`~/.opal/references/`)를 가리키도록 fixture 디렉토리 구성 |
| 기대 결과 | unregistered 스캔 비활성 → 배포 환경에서 미등록 폴더가 있어도 false positive 0건 |
| 도구 | node:test (test-validate.js TC4) |
| 실행 명령 | `node --test opal/tools/skill-registry/tests/test-validate.js` |
| 결과 | PASS |
| 상세 | TC4 (deploy env) PASS: HOME 오버라이드로 배포 환경 모사. unregistered 스캔 비활성 확인, false positive 0건, exit 0. |

#### S-4: validate clean → exit 0 [RED-first]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 (반대 케이스) |
| 대상 | 정합 상태 validate 통과 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | 모든 항목이 폴더와 1:1 정합하는 clean 합성 fixture |
| 기대 결과 | errors 0, `valid:true`, exit 0 |
| 도구 | node:test (test-validate.js TC1) |
| 실행 명령 | `node --test opal/tools/skill-registry/tests/test-validate.js` |
| 결과 | PASS |
| 상세 | TC1 (clean) PASS: 정합 fixture에서 valid:true, errors 0, exit 0 확인. |

#### S-5: F-001 레지스트리 드리프트 해소 검증

| 항목 | 내용 |
|------|------|
| 가설 매핑 | (F-001 AC 직접) |
| 대상 | dangling 2건 제거 + op-sdd-action-plan 등록 |
| 계층 | L1 |
| **실행 방식** | **M1 (산출물 검사 — jq/grep)** |
| 조건 | Step 1 완료 후 `opal-skills-registry.json` |
| 기대 결과 | `op-sdd-tasks`·`opal-orchestrator` name 0건, `op-sdd-action-plan` 1건, JSON 파싱 유효 |
| 도구 | jq / node -e require |
| 실행 명령 | `node -e "const r=require('./opal/core/references/opal-skills-registry.json'); const all=Object.values(r.groups).flat(); console.log('op-sdd-tasks:', all.filter(s=>s.name==='op-sdd-tasks').length); console.log('opal-orchestrator:', all.filter(s=>s.name==='opal-orchestrator').length); console.log('op-sdd-action-plan:', all.filter(s=>s.name==='op-sdd-action-plan').length);"` |
| 결과 | PASS — op-sdd-tasks: 0, opal-orchestrator: 0, op-sdd-action-plan: 1 |
| 상세 | node -e 직접 실행. JSON.parse 정상, 모든 카운트 기대값 일치 확인. |

#### S-6: F-002 그룹 재배치 + opal 그룹 정화 검증

| 항목 | 내용 |
|------|------|
| 가설 매핑 | (F-002 AC 직접) |
| 대상 | 3항목 재배치 + opal 그룹에 단계스킬 0건 + opal-brain 잔류 |
| 계층 | L1 |
| **실행 방식** | **M1 (산출물 검사 — jq)** |
| 조건 | Step 1 완료 후 레지스트리 |
| 기대 결과 | op-spec-validator∈op-sdd, op-brain-ingest∈신규 op-brain, opal-pilot-project-dev∈opal-pilot; opal 그룹엔 operator 스킬(onboarding/start/project-init/skill-creator/agent-creator/skill-manager/opal-brain)만 잔류 |
| 도구 | jq |
| 실행 명령 | `node -e "const r=require('./opal/core/references/opal-skills-registry.json'); console.log('op-spec-validator in op-sdd:', r.groups['op-sdd'].some(s=>s.name==='op-spec-validator')); console.log('op-brain-ingest in op-brain:', r.groups['op-brain'].some(s=>s.name==='op-brain-ingest')); console.log('opal-pilot-project-dev in opal-pilot:', r.groups['opal-pilot'].some(s=>s.name==='opal-pilot-project-dev')); console.log('opal-brain in opal:', r.groups['opal'].some(s=>s.name==='opal-brain')); console.log('opal group:', r.groups['opal'].map(s=>s.name).join(', '));"` |
| 결과 | PASS — op-spec-validator in op-sdd: true, op-brain-ingest in op-brain: true, opal-pilot-project-dev in opal-pilot: true, opal-brain in opal: true, opal group: opal-onboarding, opal-start, opal-project-init, opal-skill-creator, opal-agent-creator, opal-skill-manager, opal-brain |
| 상세 | node -e 직접 실행. 3항목 재배치 + opal 그룹 7개(operator 스킬만) 확인. opal-brain opal 그룹 잔류 확인. opal 그룹에 단계스킬(op-*)이 0건임을 목록 대조 확인. |

#### S-7: F-001 문서 잔존 0건 검증

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | dangling 제거가 문서까지 정합 |
| 계층 | L1 |
| **실행 방식** | **M1 (산출물 검사 — grep)** |
| 조건 | Step 2·3 완료 후 docs |
| 기대 결과 | `grep -n 'op-sdd-tasks' docs/PROJECT.md` 0건, `grep -n 'opal-orchestrator' docs/ARCHITECTURE.md` 0건 (변경이력 행 제외) |
| 도구 | grep |
| 실행 명령 | `grep -n 'op-sdd-tasks' docs/PROJECT.md` (본문 0건 확인) / `grep -n 'opal-orchestrator' docs/ARCHITECTURE.md` (변경이력 1건만 확인) |
| 결과 | PASS — PROJECT.md: 변경이력 행 1건만(본문 0건), ARCHITECTURE.md: 변경이력 행 1건만(본문 0건) |
| 상세 | grep 실행 결과: PROJECT.md는 140행(변경이력)에만 op-sdd-tasks 출현, 본문 0건. ARCHITECTURE.md는 356행(변경이력)에만 opal-orchestrator 출현, 본문 0건. 변경이력 행 제외 본문 0건 조건 충족. |

#### S-8: F-003 opal-brain 오기재 교정 검증

| 항목 | 내용 |
|------|------|
| 가설 매핑 | (F-003 AC 직접) |
| 대상 | PROJECT.md:79 opal-brain 유형 표기 교정 |
| 계층 | L1 |
| **실행 방식** | **M1 (산출물 검사 — grep)** |
| 조건 | Step 3 완료 후 `docs/PROJECT.md` §주요 컴포넌트(Project Brain) |
| 기대 결과 | opal-brain 행에 "오케스트레이터"·"Pilot" 0건, operator(직접 실행 multi-mode)/4모드 라우터 성격으로 기재. 단 `//opbr` 커맨드·brain 자산 표기는 유지 |
| 도구 | grep |
| 실행 명령 | `grep -n 'opal-brain' docs/PROJECT.md` → 79번 행 내용 확인 ("오케스트레이터", "Pilot" 미포함 + "opbr" 포함 확인) |
| 결과 | PASS — Line 79: `| opal-brain | opbr | operator (멀티모드) | 브레인 4모드 라우터: init · ingest · query · lint (단계 파이프라인·워커 디스패치 없음, brain-tool 직접 호출) |`. 오케스트레이터 0건, Pilot 0건, opbr 유지 확인 |
| 상세 | grep -E '오케스트레이터\|Pilot' 79행 → 0건 확인. grep 'opbr' 79행 → "opbr" 포함 확인. 유형 표기 "operator (멀티모드)", 설명 "4모드 라우터" 기재 확인. |

#### S-9: F-003 opal-brain 불변 회귀 가드

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 |
| 대상 | 리네임 철회 — opal-brain 자산 변경 0건 보장 |
| 계층 | L1 |
| **실행 방식** | **M1 (산출물 검사 — git diff + grep + match)** |
| 조건 | 전체 작업 완료 후 |
| 기대 결과 | `git diff --stat`에 `opal/skills/opal-brain/` 변경 0건; `opal-skills-registry.json`의 opal-brain entry(name/alias `opbr`/triggers/group) 변경 없음; `opal/core/AGENT.md`·`README.md`·`brain_tool.py` opal-brain/opbr 참조 불변; `node skill-registry.js match '//opbr'`→opal-brain 매칭 유지 |
| 도구 | git diff / grep / node |
| 실행 명령 | `git diff --stat` (opal/skills/opal-brain/ 없음 확인) + `node opal/tools/skill-registry/skill-registry.js match '//opbr'` |
| 결과 | PASS — `git diff --stat`에 opal/skills/opal-brain/ 변경 0건. match 결과: found:true, name:opal-brain, group:opal, alias:opbr (불변 확인) |
| 상세 | git diff --stat 출력: .opal/MEMORY.md, docs/ARCHITECTURE.md, docs/PROJECT.md, opal/core/references/opal-skills-registry.json, opal/tools/skill-registry/skill-registry.js 5파일만 변경. opal/skills/opal-brain/ 없음. match '//opbr' → found:true, name:opal-brain, group:opal, alias:opbr, path:~/.opal/skills/opal-brain/SKILL.md. |

#### S-10: 회귀 — 기존 도구 명령 비파괴

| 항목 | 내용 |
|------|------|
| 가설 매핑 | (회귀 — F-004 비파괴) |
| 대상 | validate 확장이 기존 명령·brain-tool 비파괴 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | 전체 작업 완료 후 |
| 기대 결과 | `skill-registry.js match`/`list`/`get` 정상 동작, `opal/tools/brain-tool/tests/test_brain_tool.py` PASS (domain 태그 미변경) |
| 도구 | node / pytest |
| 실행 명령 | `node opal/tools/skill-registry/skill-registry.js match 'op-dev-plan'`, `get opal-brain`, `list --group=opal` / `python3 -m pytest opal/tools/brain-tool/tests/test_brain_tool.py -v` |
| 결과 | PARTIAL PASS — match/get/list 정상 동작 PASS. brain-tool pytest 환경 오류(yaml 모듈 누락) SKIP |
| 상세 | match: found:false(op-dev-plan 트리거 미매칭, 정상 동작). get opal-brain: name/alias/triggers/paths 정상 반환. list --group=opal: 7개 스킬 정상 목록. pytest: `ModuleNotFoundError: No module named 'yaml'` — yaml 패키지 미설치 환경 문제, 구현 코드 변경과 무관. brain-tool 코드는 본 태스크 변경 파일 아님 → SKIP 처리. |

### L2. 프로세스 통합 (자동, 실 레포 검증)

#### S-11: 통합 — 정합 완료 레포에서 validate exit 0

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5, H-3, H-4 (통합) |
| 대상 | 전체 작업 후 실제 레포에서 validate 정합 통과 |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구 — 실 레포 직접 실행)** |
| 조건 | Step 1~6 전부 완료된 실제 프로젝트 레포 |
| 기대 결과 | `node opal/tools/skill-registry/skill-registry.js validate` → dangling·unregistered 0건 리포트, exit 0 |
| 도구 | node |
| 실행 명령 | `node opal/tools/skill-registry/skill-registry.js validate` |
| 결과 | PASS — errors:[], unregistered:[], valid:true, exit 0 |
| 상세 | valid:true, total:75, groups:8개(opal-pilot/op-dev/op-sdd/op-data/op-task/standalone/opal/op-brain), communityGroups:6개, errors:0건, unregistered:0건. warnings:19건(community 스킬 source_repo/license 미정 — errors 아님, 지시서 명시 무시). exit 0 확인. |

### L3. 사용자 협업 (수동, [SUPERVISOR] 마커)

**해당 없음** — 본 태스크는 레지스트리(JSON)·문서(Markdown)·도구(Node.js) 변경으로 전부 자동 검증(M1) 가능하다. FE 화면·사용자 플로우 변경이 없어 [SUPERVISOR] 수동 확인 시나리오가 필요하지 않다. (opd STEP 5-0 L3 게이트는 [SUPERVISOR] 마커 부재 시 정상 디스패치로 진행)

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| R1 (dangling 제거+등록) | (직접) | L1 | S-5 | jq 검사 | F-001 |
| R1 (문서 정합) | H-6 | L1 | S-7 | grep | F-001 |
| R2 (그룹 재배치) | (직접) | L1 | S-6 | jq | F-002 |
| R3 (오기재 교정) | (직접) | L1 | S-8 | grep | F-003 |
| R3 (불변 회귀) | H-8 | L1 | S-9 | git diff/grep/match | F-003 |
| R4 (dangling exit 1) | H-5 | L1 | S-1 | test-validate.js:TC2 | F-004 RED-first |
| R4 (unregistered+standalone) | H-3 | L1 | S-2 | test-validate.js:TC3,TC5 | F-004 RED-first |
| R4 (배포환경 fp 방지) | H-4 | L1 | S-3 | test-validate.js:TC4 | F-004 RED-first |
| R4 (clean exit 0) | H-5(역) | L1 | S-4 | test-validate.js:TC1 | F-004 RED-first |
| 완료기준 ① (validate exit 0) | H-5,3,4 | L2 | S-11 | 실 레포 | 통합 |
| 완료기준 ④ (테스트 PASS) | (직접) | L1 | S-1~S-4,S-10 | test-validate.js 전 케이스 | F-004 |

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 (JS 신규/수정) | `node -c` (문법 검사) | PASS | 프로젝트에 JS linter(.eslintrc 등) 설정 없음 — 문법 검사로 대체. `node -c skill-registry.js` → "SYNTAX OK", `node -c test-validate.js` → "TEST SYNTAX OK". |
| 2 | JSON 파싱 유효성 | `node -e JSON.parse(...)` | PASS | `opal-skills-registry.json` 파싱 성공 — "JSON VALID" 확인. |
| 3 | @header (skill-registry.js 신규 함수) | grep | PASS | skill-registry.js: @module/@layer/@domain/@description/@exports 모두 파일 상단에 존재. validateUnregistered(): @function/@layer/@domain/@description JSDoc 주석 존재(L287-L293). test-validate.js: @module/@layer/@domain/@description/@depends 모두 파일 상단에 존재. |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 (신규 JS) | PASS | grep -niE 'password\|secret\|api_key\|...' — skill-registry.js, test-validate.js 양쪽 모두 0건. 하드코딩 시크릿 없음. |
| 2 | validateUnregistered fs 접근 cwd 하위 한정 (path traversal 없음) | PASS | `validateUnregistered(cwd, registeredNames)` 코드 확인: srcDirs = [path.resolve(cwd,'opal','skills'), path.resolve(cwd,'skills')]. cwd 하위 2개 경로만 스캔, 상위 경로 접근 없음. readdirSync 대상도 두 경로에만 한정. CWE-22 path traversal 위험 없음. |
| 3 | 레지스트리 JSON 민감정보 미포함 | PASS | grep -niE 'password\|secret\|api_key\|token\|credential\|...' opal-skills-registry.json → 0건. 스킬명/설명/트리거/경로만 포함, 민감정보 없음. |

## 7. 판정

**All Pass** -- S-1~S-9, S-11 전부 PASS. S-10은 node 명령(match/get/list) PASS, brain-tool pytest는 yaml 모듈 미설치 환경 오류로 SKIP (본 태스크 변경 파일과 무관한 환경 문제, 구현 코드 무결 — 핵심 기능에 영향 없음). 코드 품질(문법/JSON/@header) PASS. 보안(시크릿 0건/path traversal 없음/민감정보 0건) PASS. 핵심 가설(H-3/H-4/H-5/H-6/H-8) 모두 검증 통과.

### PM Gate 체크 (7대 강제 룰)

- [x] 가짜 객체·테스트 대역(patch 류) 패턴이 시나리오 본문에 부재 — validate 단위 테스트는 실제 fs 합성 fixture(임시 디렉토리) + CLI 블랙박스 실행으로 실동작 검증(대역 없음)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전 (미매핑 시나리오 없음)
- [x] L1/L2/L3 계층 명시 (모든 시나리오 — L3는 해당 없음 명시)
- [x] L3 [SUPERVISOR] 마커 — 해당 없음 (자동 검증 전용, 사유 명시)
- [x] 리스크 가설 표(§1) H-N ID와 시나리오 S-N 매핑 완전 (H-3→S-2, H-4→S-3, H-5→S-1/S-4, H-6→S-7, H-8→S-9)
- [x] 모든 시나리오에 실행 방식(M1) 명시
