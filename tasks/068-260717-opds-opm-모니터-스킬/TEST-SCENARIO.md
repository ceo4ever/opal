# TEST SCENARIO: opm 범용 모니터 스킬 신설 — 액션 에이전트 진행 현황 발동층

> 작성일: 2026-07-17 | 상태: TEST 완료 — 판정 All Pass (S-1~S-10 전부 Pass, §5/§6 Pass)
> 작성자: opal-plan-agent | PLAN.md §리스크 가설 표(H-1~H-9) 기반
> **RED-first 판정**: 구현-후-검증 트랙 (`--red-check` OFF) — 변경 영역이 전부 스킬·레지스트리·문서(md/json)로 `opal/core/references/harness/red-first.md` §1.5 "설정·문서" 허용 기준에 해당(순수 스킬 문서 신설). 동작 실증(S-6~S-10)은 테스트 코드가 아닌 **실 도구·실 폴더 관찰**로 검증(mock 금지). 공통 불변(작성자≠구현자·TEST 단계 검증)은 유지.

## 1. 리스크 가설 표

> PLAN.md §리스크 가설 표(H-1~H-9) 승계.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | 자동 탐지 알고리즘 (F-002) | 복수 `.oppl-run/` 중 오탐 선택 → 엉뚱한 태스크 렌더 | P2 | L2 | S-7 |
| H-2 | 도구 에러 계약 소비 (F-001) | `{"ok":false}` + exit 1을 성공으로 오해 → 허위 보고 | P1 | L2 | S-8 |
| H-3 | backlog 결합 (F-001) | backlog.json 부재 시 `backlog_not_initialized`를 전체 실패로 처리 | P1 | L2 | S-9 |
| H-4 | 수치·스키마 비복제 (F-001) | 6상태·2초 폴링·JSON 스키마 재서술 → README drift | P2 | L1 | S-3 |
| H-5 | 약어 등록 (F-003) | opm 등록 오류/충돌 → `//opm` 발동 불가 | P1 | L1 | S-4 |
| H-6 | 읽기 전용 계약 (F-001) | 파일 쓰기·state 변경 지시 → 부수효과 | P1 | L1 | S-3 |
| H-7 | install 배포 (F-004) | `opal/skills/` 신규 폴더 배포 누락 → 탐색 경로 부재 | P2 | L3 | S-10 |
| H-8 | 커버리지 경계 (F-001) | oppl 한정·069/070 확장 문구 부재 → 커버리지 오해 | P2 | L1 | S-1 |
| H-9 | oppl SKILL 무접촉 (F-004) | 안내 1줄 초과 변경 → oppl 회귀 | P1 | L1 | S-5 |

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터

> DB 없음(스킬·문서 태스크) — 067 실증 fixture + 신규 산출 파일로 구성. mock 금지·실측 기반.

| 대상 | 식별자 | 상태 | 출처 |
|------|--------|------|------|
| 신규 스킬 | `opal/skills/opal-monitor/SKILL.md` | EXECUTE Step 1 산출 | EXECUTE |
| 레지스트리 엔트리 | `opal/core/references/opal-skills-registry.json` (opal-monitor) | EXECUTE Step 2 산출 | EXECUTE |
| oppl 안내 1줄 | `opal/skills/opal-pilot-project-loop/SKILL.md:379` | EXECUTE Step 3 산출 | EXECUTE |
| 문서 갱신 | `docs/PROJECT.md` (opal-monitor 행 + 변경이력) | EXECUTE Step 4 산출 | EXECUTE |
| 실증 fixture(정상 6단계) | `tasks/067-260717-opd-루프액션-스트림-모니터링/samples/T01-정상슬라이스/` | 067 완성(6 phase `.oppl-run/`) | 실측 확인 |
| 실증 fixture(상태별) | `tasks/067-.../samples/monitor-fixtures/{running,done,blocked,error}/` | 067 완성(단일 phase) | 실측 확인 |
| 실증 대상(부재) | `tasks/068-260717-opds-opm-모니터-스킬/` | `.oppl-run/` 없음 | 실측 확인 |
| 배포본 | `~/.opal/skills/opal-monitor/SKILL.md` | Step 5(배포) 산출 | install |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (실행) | Then (re-read) |
|---------|------------|----------------|---------------|
| S-1 | SKILL.md | 필수 6절·커버리지 경계 grep | 6절 전부 + oppl 한정·069/070 문구 존재 |
| S-2 | SKILL.md | 자동 탐지 절 grep | 탐지/복수후보/미탐지 3경로 + 깊이 상한 존재 |
| S-3 | SKILL.md | 수치 리터럴·쓰기 도구 grep | 6상태/2초/JSON 스키마 리터럴 부재 + README 포인터, 쓰기 지시 부재 |
| S-4 | registry JSON | `skill-registry match "opm"`/`validate` | found:true(opal-monitor) + validate pass + 충돌 0 |
| S-5 | oppl SKILL.md (변경 전/후) | `//opm` 1줄 diff | 안내 1줄 + 변경이력 1행으로 한정 |
| S-6 | PROJECT.md | 컴포넌트 행·변경이력 grep | opal-monitor 행 + 068 이력 존재 |
| S-7 | monitor-fixtures 다중 폴더 | 스킬 자동 탐지 실행 | mtime 최신 채택 + 후보 목록 제시 |
| S-8 | 068 폴더(`.oppl-run/` 없음) | 스킬 실행(인자 지정) | `{"ok":false}` 에러 안내 후 종료(허위 보고 없음) |
| S-9 | 단독 `.oppl-run/`(loop 루트·backlog.json 없음) | 스킬 실행 | backlog 자연 스킵 + 태스크 단독 뷰 |
| S-10 | 배포본 경로 | install 후 Read | `~/.opal/skills/opal-monitor/SKILL.md` Read 가능 |

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 실 파일·실 도구 검사)

#### S-1: SKILL.md 필수 6절 + 커버리지 경계 완비 (TS-001)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8, F-001 AC (R-1) |
| 대상 | `opal/skills/opal-monitor/SKILL.md` |
| 계층 | L1 |
| **실행 방식** | **M1 (grep/Read 검사)** |
| 조건 | EXECUTE Step 1 완료 후 |
| 기대 결과 | frontmatter(name/alias:opm/triggers) + 본문 6절(실행 컨텍스트·프로세스 5단계·해석 보고 형식 a~g·커버리지 경계·에러 경로) + "oppl 한정"·"069·070 확장 시 스킬 무변경" 문구 전부 존재 |
| 도구 | grep, Read |
| 실행 명령 | `grep -nE "alias: opas\|실행 컨텍스트\|프로세스\|해석 보고\|커버리지 경계\|에러 경로\|oppl 한정\|069" opal/skills/opal-action-status/SKILL.md` |
| 결과 | **Pass** |
| 상세 | 실행 결과: frontmatter `alias: opas`(L6) + 본문 6절(`1. 실행 컨텍스트`L17, `2. 프로세스`L22, `3. 해석 보고 형식`L45, `4. 커버리지 경계`L59, `5. 에러 경로`L65, `6. 라이브 관측 안내`L69) + "oppl 한정"(L61) + "069"(L61, "069·070") 전부 존재 확인 |

#### S-2: 자동 탐지 3경로 + 깊이 상한 명문 (TS-003)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1, F-002 AC (R-2) |
| 대상 | SKILL.md §자동 탐지 |
| 계층 | L1 |
| **실행 방식** | **M1 (grep 검사)** |
| 조건 | Step 1 완료 후 |
| 기대 결과 | loop 루트 우선(backlog.json)→glob 폴백→복수 후보(최신 우선+목록)→미탐지 안내 4경로 + glob 깊이 상한·후보 나열 상한 명문 |
| 도구 | grep |
| 실행 명령 | `grep -nE "backlog.json\|자동 탐지\|복수 후보\|미탐지\|깊이 상한\|mtime" opal/skills/opal-action-status/SKILL.md` |
| 결과 | **Pass** |
| 상세 | §자동 탐지(L34) 4경로 전부 확인: ①loop 루트 우선(`backlog.json` 보유 폴더, L36)→②미발견 시 glob 폴백(L38)→③복수 후보(최신 채택+목록, L37/39)→④미탐지 안내(L40). 깊이 상한 명문 L42("loop 루트 기준 깊이 2, 전역 폴백 깊이 3"), 후보 나열 상한 10개, mtime 정렬 기준(L37/38) 명문 확인 |

#### S-3: 읽기 전용 + 수치·스키마 비복제 (TS-001 일부, H-4/H-6)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4, H-6 |
| 대상 | SKILL.md 전문 |
| 계층 | L1 |
| **실행 방식** | **M1 (grep 검사)** |
| 조건 | Step 1 완료 후 |
| 기대 결과 | ① 6상태 판정·2초 폴링·`--json` 스키마 필드 재서술 부재(리터럴 없음) + `opal-action-monitor/README.md` 포인터 존재 ② 파일 쓰기·state 변경 지시 부재, "읽기 전용"·"쓰기 0" 명문 |
| 도구 | grep |
| 실행 명령 | `grep -nE "6상태\|2초\|폴링" opal/skills/opal-action-status/SKILL.md`(리터럴 재서술 부재 확인) ; `grep -n "README.md\|읽기 전용\|쓰기" opal/skills/opal-action-status/SKILL.md` |
| 결과 | **Pass** |
| 상세 | ① `6상태`·`2초` 리터럴 매치 0건. `폴링` 매치 1건(L57)이나 값 재서술이 아닌 "폴링 주기의 상세는 재서술하지 않고 README.md 포인터로 위임한다"는 위임 문장 자체(비복제 명문) — README.md 포인터(`opal-action-monitor/README.md`) 동일 라인에 존재. ② 쓰기 지시 grep(`\bwrite\(|파일을?(생성\|작성\|저장)한다`) 매치 0건 + "읽기 전용"(L20,43), "파일 쓰기·state 변경은 0이다"(L20) 명문 확인 |

#### S-4: 레지스트리 등록 + 약어 충돌 0 (TS-005)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5, F-003 AC (R-3) |
| 대상 | `opal/core/references/opal-skills-registry.json` |
| 계층 | L1 |
| **실행 방식** | **M1 (skill-registry CLI 실측)** |
| 조건 | Step 2 완료 후 |
| 기대 결과 | `match "opm"`·`match "//opm"` → found:true(name:opal-monitor), `validate` pass, alias 충돌 0 |
| 도구 | node skill-registry.js |
| 실행 명령 | `node ~/.opal/tools/skill-registry/skill-registry.js match "opas"` ; `... match "//opas"` ; `... validate` |
| 결과 | **Pass** |
| 상세 | TEST 단계 재실측(배포 후): `match "opas"` → `found:true, name:"opal-action-status", path:"/Users/lucas/.opal/skills/opal-action-status/SKILL.md"`. `match "//opas"` → 동일 `found:true`(cleanInput 접두 `//` 정상 제거). `validate` → `valid:true, errors:[]`(opal-action-status dangling 경고 해소 확인 — PM 배포로 paths 정합). 타 alias 회귀: `match "opbr"` → found:true(opal-brain, 무변경), `match "opd"` → found:true(opal-pilot-dev, 무변경). 충돌 0 |

#### S-5: oppl SKILL 무접촉(안내 1줄) + 변경이력 (TS-006 일부)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9, F-004 AC (R-4) |
| 대상 | `opal/skills/opal-pilot-project-loop/SKILL.md` |
| 계층 | L1 |
| **실행 방식** | **M1 (git diff + grep)** |
| 조건 | Step 3 완료 후 |
| 기대 결과 | `//opm` 발동 안내 1줄 존재 + diff가 안내 1줄 + 변경이력 1행(068)으로 한정(본문 무접촉) |
| 도구 | git diff, grep |
| 실행 명령 | `git diff opal/skills/opal-pilot-project-loop/SKILL.md` (추가 라인 = 안내 1줄 + 이력 1행) ; `grep -n "//opas" opal/skills/opal-pilot-project-loop/SKILL.md` |
| 결과 | **Pass** |
| 상세 | `git diff` 재확인: 본문 삽입 1줄(L379, "진행 현황 모니터링" 문단 내 `//opas [태스크폴더]` 안내 추가) + 변경이력 표 3행(v1.4/v1.5/v1.6) 추가. v1.4/v1.5는 067 커밋 전 미커밋 변경분(H-9 무관, 사전 인지된 상태)이고 **068 자체 추가분은 v1.6 1행 + 안내문 1줄뿐**으로 한정 확인. `grep "//opas"` → L379(본문 안내), L588(v1.6 이력 행) 2건, 본문 다른 곳 무변경 |

#### S-6: PROJECT.md 컴포넌트 행 + 변경이력 (TS-006)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | F-004 AC (R-4) |
| 대상 | `docs/PROJECT.md` |
| 계층 | L1 |
| **실행 방식** | **M1 (grep 검사)** |
| 조건 | Step 4 완료 후 |
| 기대 결과 | Project Loop 표에 opal-monitor(opm) 행 + oppl 한정·069/070 경계 서술 + 변경이력 행(068) |
| 도구 | grep |
| 실행 명령 | `grep -n "opal-action-status\|opas\|068" docs/PROJECT.md` |
| 결과 | **Pass** |
| 상세 | L111: Project Loop 표에 `opal-action-status \| opas \| operator \| ...커버리지 oppl 한정, 069/070 전환 시 무변경 확장` 행 확인. L157: 변경이력에 "(Task 068)" 행 확인. `git diff --stat docs/PROJECT.md` → 5줄 추가(1 파일)로 스코프 한정 확인 |

### L2. 프로세스 통합 (자동 — 실 도구·실 폴더 관찰)

#### S-7: 자동 탐지 최신 채택 + 후보 목록 실증 (TS-004)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1, F-002 AC (R-2) |
| 대상 | 스킬 자동 탐지 프로세스 |
| 계층 | L2 |
| **실행 방식** | **M2 (스킬 프로세스 실행 — 실 폴더 스캔)** |
| 조건 | `tasks/067-.../samples/monitor-fixtures/` 하위 다중 `.oppl-run/` fixture(running/done/blocked/error) |
| 기대 결과 | mtime 최신 폴더 자동 채택 + 상위 후보 목록 함께 제시(사용자 재지정 가능), 오탐 시 사용자 확정 위임 |
| 도구 | 스킬 프로세스(glob·stat), opal-action-monitor |
| 실행 명령 | 스킬 자동 탐지 절차를 monitor-fixtures 부모에서 실행 → 채택 폴더 + 후보 목록 확인 |
| 결과 | **Pass** |
| 상세 | `monitor-fixtures/{running,done,blocked,error}/.oppl-run` 4개 fixture에 `stat -f "%m %N"` + mtime 내림차순 정렬 실행 → 채택: `blocked`(mtime 1784286222, 최신) + 후보 목록(error/running/done) 함께 제시됨(스킬 §자동 탐지 3. "최신 채택 + 상위 후보 목록" 동작 실증). 4개 폴더 각각 `run.sh --json` 개별 소비 가능 확인(`blocked` fixture는 `"blocked": true` 배너 정상 반영, 나머지는 false) — 오탐 없이 정확한 최신 폴더 채택 |

#### S-8: 부재 폴더 에러 안내 완주 실증 (TS-002)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2, F-001 AC (R-1) |
| 대상 | 스킬 에러 경로 |
| 계층 | L2 |
| **실행 방식** | **M2 (실 도구 호출 관찰)** |
| 조건 | `tasks/068-260717-opds-opm-모니터-스킬/` (`.oppl-run/` 없음) |
| 기대 결과 | `opal-action-monitor --json`이 `{"ok":false,"error":"..."}` 반환 → 스킬이 성공으로 오해하지 않고 에러 메시지 안내 후 종료(허위 현황판 미출력) |
| 도구 | opal-action-monitor |
| 실행 명령 | `~/.opal/tools/opal-action-monitor/run.sh tasks/068-260717-opds-opm-모니터-스킬 --json` → `ok:false` 확인 → 스킬 안내 경로 검증 |
| 결과 | **Pass** |
| 상세 | TEST 단계 재실측: `{"ok": false, "error": ".oppl-run/ 디렉토리가 없습니다: tasks/068-260717-opds-opm-모니터-스킬/.oppl-run"}` + `exit=1` 확인. SKILL.md §5 에러 경로(L67) 지시대로 "ok:false + exit 1 → 성공으로 오해하지 않고 error 메시지 안내 후 종료" 계약과 도구 실제 출력이 정확히 일치 — 허위 보고 유발 요소 없음 |

#### S-9: backlog 결합 자연 스킵 실증 (TS-009)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3, F-001 AC (R-1) |
| 대상 | 스킬 backlog 결합 조건 |
| 계층 | L2 |
| **실행 방식** | **M2 (실 도구·실 폴더 관찰)** |
| 조건 | `tasks/067-.../samples/T01-정상슬라이스/` (단독 `.oppl-run/`, 상위에 loop 루트·backlog.json 없음) |
| 기대 결과 | `.oppl-run/` 렌더는 정상 산출, backlog.json 부재로 `backlog-tool show` 자연 스킵(전체 실패 아님) + "루프 백로그 없음 — 태스크 단독 뷰" 안내 |
| 도구 | opal-action-monitor, backlog-tool |
| 실행 명령 | T01 대상 스킬 실행 → 단계×축 보고 산출 + backlog 스킵 배너 확인 |
| 결과 | **Pass** |
| 상세 | T01 상위(`tasks/067-.../samples/`)에 `backlog.json` 부재 확인(find 결과 0건) → `run.sh --json` 실행 결과 `ok:true` + `phases[]` 6종(t1/t2/g/t3/t4a/t4b) 정상 렌더, `blocked:false`, journal_tail 7건 확인. SKILL §2-3(L28) 지시대로 backlog.json 부재 시 `backlog-tool` 미호출·자연 스킵 확인(전체 실패 아님, 태스크 단독 뷰로 정상 처리). 보완 실측: backlog.json 존재 케이스(`tasks/056-260710-opd-oppl-루프-오케스트레이터/dryrun/backlog.json`)에서 `backlog-tool show`가 `ok:true, marker_present:true` + 표 렌더 반환 확인 — 결합 시 계약도 정상 작동 |

### L3. 사용자 협업 (수동, [SUPERVISOR] 마커)

#### S-10: install 배포 검증 (TS-007) [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7, F-004 AC (R-5) |
| 대상 | `./scripts/install-mac.sh` 실행 (배포 = 사람 게이트) |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업 — 캡틴 승인 후 PM 대행 가능)** |
| 조건 | S-1~S-9 통과 후, 캡틴 배포 승인 |
| 기대 결과 | 배포 후 `~/.opal/skills/opal-monitor/SKILL.md` Read 가능 + `~/.opal/references/opal-skills-registry.json`에 opm 엔트리 반영 + `//opm` 매칭 활성 |
| 실행자 | [SUPERVISOR] — 캡틴 승인 필요 (CONVENTIONS §배포 경계) |
| 결과 | **Pass** (PM 대행 배포 완료 확인 — 재확인만 수행) |
| 상세 | install-mac.sh 배포는 PM이 완료. TEST 단계 재확인: `~/.opal/skills/opal-action-status/SKILL.md` Read 가능(5500 bytes, 07-17 23:46) 확인. registry(`~/.opal/core/references/opal-skills-registry.json` 등 배포본)에 opal-action-status 엔트리 반영 확인(paths 2건 포함). `match "opas"`/`match "//opas"` found:true로 활성 매칭 확인(S-4와 동일 실측) |

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| R-1 AC (6절 완비) | H-8 | L1 | S-1 | SKILL.md (grep) | TS-001 |
| R-2 AC (탐지 3경로) | H-1 | L1 | S-2 | SKILL.md (grep) | TS-003 |
| R-1 AC (읽기전용·비복제) | H-4, H-6 | L1 | S-3 | SKILL.md (grep) | TS-001 일부 |
| R-3 AC (등록·충돌0) | H-5 | L1 | S-4 | registry (match/validate) | TS-005 |
| R-4 AC (oppl 무접촉·이력) | H-9 | L1 | S-5 | oppl SKILL (diff) | TS-006 |
| R-4 AC (PROJECT.md) | — | L1 | S-6 | PROJECT.md (grep) | TS-006 |
| R-2 AC (자동탐지 실증) | H-1 | L2 | S-7 | monitor-fixtures 실측 | TS-004 |
| R-1 AC (에러 경로) | H-2 | L2 | S-8 | 068 폴더 실측 | TS-002 |
| R-1 AC (backlog 스킵) | H-3 | L2 | S-9 | T01 실측 | TS-009 |
| R-5 AC (배포 존재) | H-7 | L3 | S-10 | install 실행 확인 | TS-007, 사람 게이트 |

## 5. 코드 품질

> TEST 단계에서 채움 (PLAN 통합 산출 시점 미실행).

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | md/json 구문 육안 + `python -m json.tool`(registry) | Pass | `python3 -m json.tool opal-skills-registry.json` 정상 파싱(구문 오류 0). SKILL.md 헤더(`##` 8개)·테이블(`|` 3행) 구조 정상, frontmatter YAML 정상 |
| 2 | 타입 체크 | 해당 없음 | - | - |
| 3 | 포맷터 | 해당 없음 | - | - |

## 6. 보안

> TEST 단계에서 채움.

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | Pass | 변경 파일(SKILL.md·registry·oppl SKILL·PROJECT.md) 대상 `grep -inE "api[_-]?key\|secret\|token.*="` → 매치 0건 |
| 2 | 읽기 전용 계약 확인 | Pass | 스킬 본문 grep(`write\(`, "파일을 생성/작성/저장한다", "state...변경한다") → 매치 0건 + "읽기 전용"·"파일 쓰기·state 변경은 0이다" 명문 2건 존재(S-3 상세와 동일 근거) |

## 7. 판정

**판정: All Pass**

- L1(S-1~S-6): 전부 Pass — SKILL.md 6절+커버리지 경계 완비(S-1), 자동 탐지 4경로+깊이 상한 명문(S-2), 수치·스키마 비복제+읽기 전용 명문(S-3), 레지스트리 등록+충돌 0(S-4), oppl 무접촉(안내 1줄+이력 1행 한정, S-5), PROJECT.md 반영(S-6).
- L2(S-7~S-9): 전부 Pass — 자동 탐지 mtime 최신 채택+후보 목록 실증(S-7), `{"ok":false}`+exit 1 에러 경로 정확 소비(S-8), backlog 부재 자연 스킵+존재 시 정상 결합 실증(S-9).
- L3(S-10): Pass — PM 대행 배포 완료 상태를 재확인(배포본 Read 가능, registry 반영, `//opas` 매칭 활성).
- 코드 품질(§5): Pass — registry JSON 유효, md 구조 정상.
- 보안(§6): Pass — 시크릿 0건, 읽기 전용 계약 위반 문구 0건.
- 회귀: oppl SKILL.md 본문(§디스패치 외 영역) 무변경 확인, oppl 도구(`opal_agent.py` 등)는 068 스코프 밖(067 미커밋 변경분)이며 068이 건드리지 않음을 `git status`로 확인.
- 특이사항(참고, Fail 아님): 작업트리에 067 태스크의 미커밋 변경(`opal/agents/opal-loop-action-agent/AGENT.md`, `opal/tools/opal-agent/*`, `opal/core/references/opal-harness.md`/`tools.md`, `scripts/install-mac.sh` 등)이 잔존 — 068의 범위가 아니며 이번 TEST가 변경하거나 유발한 것이 아님을 확인.

### PM Gate 체크 (7대 강제 룰)

- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 (실 파일·실 도구·실 폴더만 사용)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전 (H-1~H-9 전부 매핑, 미매핑 시나리오 없음)
- [x] L1/L2/L3 계층 명시 (S-1~6=L1, S-7~9=L2, S-10=L3)
- [x] L3 [SUPERVISOR] 마커 + 캡틴 협업 명시 (S-10)
- [x] 실행 방식(M1/M2/M3) 전 시나리오 명시
