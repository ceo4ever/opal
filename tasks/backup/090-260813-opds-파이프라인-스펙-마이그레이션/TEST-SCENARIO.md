# TEST SCENARIO: 미전환 6 pilot 파이프라인 스펙 마이그레이션 — 10/10 완전 전환

> 작성일: 2026-08-13 | 상태: 작성 완료
> 작성자: 알투(PM) + 캡틴 페어 | PLAN.md §리스크 가설 표(H-1~H-18) 기반
> 게이트 이력: iteration 1 pass(2/1/2, 평균 1.67, gap 1) → **iteration 2 pass(2/2/2, 평균 2.00, gap 0)**
> **RED-first 트랙 판정: 미적용 (구현 후 시나리오 검증 트랙)** — 변경 영역이 `설정·문서`(pipeline.json 데이터 + SKILL.md 문서)이고 `state_tool.py` 소스는 무변경이다. 비즈니스 로직·DB 스키마·API 계약·인증/인가·버그 수정 어디에도 해당하지 않는다 (`opal/core/references/harness/red-first.md` §1.5). 공통 불변 3종은 유지한다 — ① 테스트 산출물(검증 스크립트) ② 작성자≠구현자(본 문서는 PM 작성, EXECUTE 워커와 분리) ③ TEST 단계 독립 검증(opal-test-agent).

## 1. 리스크 가설 표

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | F-001 / 그룹 A 4종 | 전후 동등 파괴 — `task_steps[]` 개수·순서·`stage`·`item` 변경 | P0 | L1 + L2 | S-1, S-13 |
| H-2 | F-001 / opsdd `meta.stages` | `EXECUTE-LOOP` 오기입 (STAGE_ENUM 미등록) | P0 | L1 | S-2, S-8 |
| H-3 | F-006 / opsdd 산문 | `EXECUTE-LOOP` 개명 연쇄 (8파일 41곳) | P0 | L1 | S-3 |
| H-4 | F-001 / opsdd pipeline.json | 최장 배열 25행의 `id` 순차·`key` 유일성 위반 | P1 | L1 | S-4 |
| H-5 | F-001 / oppl pipeline.json | baseline 도출 오류 — 파서 before 부재 | P0 | L1 + L2 | S-5, S-14 |
| H-6 | F-001 / oppl pipeline.json | `item` 특수문자 원문 훼손 (백틱·`—`·`✓`·`{NN}`) | P1 | L1 | S-5 |
| H-7 | F-001 / oppd pipeline.json | D-7b 확정 13행 이탈·재설계 | P0 | L1 | S-6 |
| H-8 | F-003 / oppd SKILL.md | 신설 미러 표와 pipeline.json 불일치 | P1 | L1 | S-7 |
| H-9 | F-001 / opdd pipeline.json | `DDL/MIGRATION` slug 처리 실패 | P1 | L1 | S-4 |
| H-10 | F-001 / 6 pilot | `key` 패턴 위반 | P1 | L1 | S-4 |
| H-11 | F-001 / opwt `meta.stages` | 파생 원천 모호 — 라벨 줄의 `ANALYSIS` 오염 | P2 | L1 | S-8 |
| H-12 | F-004 / registry | 표기 형식 미결정 | P2 | L1 | S-9 |
| H-13 | F-003 / 6 SKILL.md | `--rows-from` 잔존 (중복 등장 일부 누락) | P1 | L1 | S-10 |
| H-14 | F-005 / 검증 절차 | 임시 산출물 레포 잔류 | P0 | L2 | S-15 |
| H-15 | F-001~F-003 | 배포 경계 위반 (`~/.opal/` 직접 편집) | P1 | L1 | S-11 |
| H-16 | F-003 / oppl SKILL.md | 범위 밖 개명 유혹 (헤더 2곳) | P2 | L1 | S-12 |
| H-17 | F-001 / oppd 런타임 | `--wbs` 경로 EXECUTE 3행 미완 잔존 | P2 | L2 | S-16 |
| H-18 | F-008 / 코어 레퍼런스·하네스·단계 스킬 | **pilot 밖 구형 지시 잔존** — `tools.md:152`가 이미 전환된 opp를 `.md` 경로로 호출하라 지시한다. 남기면 다음 사람이 복사해 구형 경로를 재도입 | **P0** | L1 | S-10, S-18 |

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터

| 대상 | 식별자 | 상태 | 출처 |
|------|--------|------|------|
| 그룹 A baseline | `$WORK/before/{opdd,opgc,opwt,opsdd}.rows.json` | Step 1에서 `build_rows_from_skill_md` 직접 호출로 생성 | 실행 산출 (레포 밖) |
| oppl 표 baseline | `$WORK/before/oppl.table.json` | `SKILL.md:139-157`을 행 정규식(`state_tool.py:816-820`)으로 추출 | 실행 산출 (레포 밖) |
| oppd 확정 baseline | `$WORK/before/oppd.d7b.json` | `TASK.md` §확정된 설계 방향 D-7b 13행 표를 전사 | 문서 전사 |
| 하드 실패 증거 | `$WORK/before/{oppl,oppd}.initfail.txt` | 전환 전 `init --rows-from SKILL.md` stderr/exit | 실행 산출 (레포 밖) |
| `EXECUTE-LOOP` 횟수 | `$WORK/before/opsdd.execute-loop-count.txt` | `grep -c "EXECUTE-LOOP" opal-pilot-sdd/SKILL.md` = **17** | 실행 산출 (레포 밖) |
| 외부 6파일 해시 | `$WORK/before/external6.sha256` | brain 3종·README·ARCHITECTURE·다이어그램 HTML·`opal-harness-semi-agentic.md`·`op-sdd-plan/SKILL.md` | 실행 산출 (레포 밖) |
| 작업 디렉토리 | `$WORK` = 스크래치패드 하위 `eq-verify/` | 레포 밖, 검증 종료 시 삭제 | 세션 스크래치패드 |
| 기존 태스크 state | `tasks/080~089/state.json` | 무변경 유지 대상 (제약 (d)) | 레포 기존 자산 |

> `$WORK`는 레포 바깥 경로다. 모든 `init` 실행은 `$WORK` 하위 임시 태스크 경로에서만 수행한다.

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (CUD/호출) | Then (re-read) |
|---------|------------|----------------|---------------|
| S-1 | `$WORK/before/{4종}.rows.json` | 신설 pipeline.json으로 `init` 실행 → `after/{4종}.rows.json` | before ↔ after `[(row_id,stage,item)]` 완전 일치 |
| S-2 | opsdd `pipeline.json` | `meta.stages` 읽기 | `["TASK","SPEC","REVIEW","DESIGN","EXECUTE","VERIFY","CLOSE"]`, `EXECUTE-LOOP` 미포함 |
| S-3 | `$WORK/before/opsdd.execute-loop-count.txt`(=17), `external6.sha256` | 전 Step 완료 후 재계수·재해시 | 17회 동일, 6파일 해시 동일, `execute-loop-guide.md` diff 0 |
| S-4 | 10개 pipeline.json | `state-tool spec-validate` ×10 | 10건 `ok:true`·`violations_count:0` |
| S-5 | `$WORK/before/oppl.table.json`(19행) | oppl `pipeline.json` `task_steps` 파싱 | 19개 `(id,stage,item)` 문자 단위 동일 |
| S-6 | `$WORK/before/oppd.d7b.json`(13행) | oppd `pipeline.json` `task_steps` 파싱 | 13개 `(id,key,stage,item)` 완전 일치 |
| S-7 | oppd `SKILL.md` 신설 미러 표 | 표 13행 추출 | `task_steps` 13개와 1:1 동일 |
| S-8 | 10개 pipeline.json | `meta.stages` ↔ `task_steps[].stage` 등장순 중복제거 대조 | 10종 전부 일치 (opwt에 `ANALYSIS` 부재, opsdd에 `EXECUTE-LOOP` 부재) |
| S-9 | `opal-skills-registry.json` | 10종 `pipeline` 값 `" → "` split | 각 `meta.stages`와 순서·원소 완전 일치, oppd `domain` 존재 |
| S-10 | 대상 6종 SKILL.md | `awk`로 `## 변경이력` 이전 구간만 grep | `rows-from.*SKILL.md` 0건 / `rows-from.*pipeline.json` 10파일 |
| S-18 | `tools.md:84,152` · `task-process.md:49` · `op-task/SKILL.md:223` 원문 + `state_tool.py`/`state-tool/README.md` 해시 | F-008 Step 편집 수행 | 3파일 지시 표현 0건 · 변경이력 각 1행 · 도구 자신 2파일 무변경 |
| S-11 | `git status --porcelain` | 전 Step 완료 후 변경 파일 목록 수집 | 전부 `opal/`·`docs/`·`tasks/` 하위, `~/.opal/` 0건 |
| S-12 | oppl `SKILL.md:121`·`:137` 원문 | `git diff` 해당 줄 검사 | 두 줄이 diff에 미등장 |
| S-13 | 10종 신설·기존 pipeline.json | `init` ×10 (2 mode 포함 20회) | 전부 exit 0·`ok:true`·`schema_version:"1.1"`·전 행 `key` 보유 |
| S-14 | `$WORK/before/{oppl,oppd}.initfail.txt` | 전환 후 `.json` 경로로 `init` 재실행 | oppl `rows_count:19` / oppd `rows_count:13`, exit 0 |
| S-15 | 검증 시작 전 `git status --porcelain` 스냅샷 | 전 검증 수행 → `rm -rf $WORK` | 종료 후 `git status --porcelain`이 시작 시점과 동일, `tasks/080~089` 무변경 |
| S-16 | oppd `.json`으로 생성한 임시 state (13행) | id 10~12를 `mark --na` 후 `close.done_md` 진입 시도 | CLOSE 진입 허용 (stage-transition guard 미차단) |
| S-17 | install 재배포 완료된 `~/.opal/` | 캡틴이 새 세션에서 대상 pilot 호출 | 태스크 폴더·STATE.md 정상 생성, deprecation 경고 미출력 |

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 실 데이터 입력)

#### S-1: 그룹 A 4종 전후 동등

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | opdd(15) · opgc(7) · opwt(10) · opsdd(25) pipeline.json |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** — python 대조 스크립트 |
| 조건 | Step 1 before 스냅샷 존재. 각 pilot Step 편집 완료 |
| 기대 결과 | 4종 전부 before ↔ after의 `[(row_id, stage, item)]` 리스트가 **완전 동일**. 특수문자(`{ts}`·`[-{element}]`·`작업 (Batch 동적 삽입)`·`구조 검증 (S-1~S-6)`) 문자 단위 보존 |
| 도구 | python3 (표준 라이브러리) |
| 실행 명령 | (독립 재실행) `~/.opal/tools/state-tool/run.sh init $WORK/test/<alias>-<mode> --skill <alias> --mode <mode> --rows-from opal/skills/<pilot>/references/pipeline.json` ×8(4종×2모드) → `python3`로 `[(row_id,stage,item)]` tuple 비교 |
| 결과 | **Pass** |
| 상세 | opal-test-agent가 opal-task-agent(EXECUTE Step10)의 after 스냅샷을 재사용하지 않고 **자체 CLI 재실행**으로 신규 after를 생성해 대조: `opdd semi-agentic: before_len=15 after_len=15 EQUAL=True` / `opdd agentic: EQUAL=True` / `opgc semi-agentic: before_len=7 after_len=7 EQUAL=True` / `opgc agentic: EQUAL=True` / `opwt semi-agentic: before_len=10 after_len=10 EQUAL=True` / `opwt agentic: EQUAL=True` / `opsdd semi-agentic: before_len=25 after_len=25 EQUAL=True` / `opsdd agentic: EQUAL=True` → **GROUP A OVERALL EQUAL: True**(8/8). 특수문자 원문 보존 확인: `opgc: 'GC-SECURITY-{ts}[-{element}].md 생성'`, `opwt: '작업 (Batch 동적 삽입)'`, `opsdd: '구조 검증 (S-1~S-6)'` 전부 검색 성공. |

#### S-2: opsdd `meta.stages` 오염 차단

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | `opal/skills/opal-pilot-sdd/references/pipeline.json` |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | opsdd Step 완료 |
| 기대 결과 | `meta.stages == ["TASK","SPEC","REVIEW","DESIGN","EXECUTE","VERIFY","CLOSE"]`. 파일 전체에 `EXECUTE-LOOP` 문자열 **0회** |
| 도구 | python3 / grep |
| 실행 명령 | `python3 -c "json.load(...)['meta']['stages']"` + `grep -c "EXECUTE-LOOP" opal/skills/opal-pilot-sdd/references/pipeline.json` |
| 결과 | **Pass** |
| 상세 | `meta.stages = ['TASK','SPEC','REVIEW','DESIGN','EXECUTE','VERIFY','CLOSE']` → `MATCH: True`. `grep -c "EXECUTE-LOOP" .../opal-pilot-sdd/references/pipeline.json` → `0`. |

#### S-3: opsdd `EXECUTE-LOOP` 산문 무변경

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | opsdd SKILL.md 산문 17곳 + `references/execute-loop-guide.md` + 외부 6파일 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** — 계수 + 해시 대조 |
| 조건 | Step 1에서 before 계수(17)·외부 6파일 해시 확보 |
| 기대 결과 | ① opsdd SKILL.md `EXECUTE-LOOP` 등장 **17회로 전후 동일** ② `execute-loop-guide.md` 변경 0건(파일명 포함) ③ 외부 6파일 SHA-256 전후 동일 |
| 도구 | grep -c / sha256sum / git diff |
| 실행 명령 | `grep -c "EXECUTE-LOOP" opal/skills/opal-pilot-sdd/SKILL.md` + `git status --porcelain -- execute-loop-guide.md 외부6파일` |
| 결과 | **Pass** |
| 상세 | after `EXECUTE-LOOP` 등장 = `17`, before(`$WORK/before/opsdd.execute-loop-count.txt`) = `17` → 동일. `git status --porcelain -- opal/skills/opal-pilot-sdd/references/execute-loop-guide.md` 출력 없음(0건). 외부 6파일(`opal-harness-semi-agentic.md`, `op-sdd-plan/SKILL.md`, `README.md`, `docs/ARCHITECTURE.md`, 다이어그램 HTML, brain 3종) 전부 `git status --porcelain` 출력 없음(0건). sha256 재계산 없이 git 추적 diff로 확인(레포이므로 diff-0 = 해시 동일과 동치, before/에 external6.sha256 파일이 실제로는 부재했음을 확인 — 대신 git status로 등가 검증). |

#### S-4: `spec-validate` 10건 전수 통과

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4, H-9, H-10 |
| 대상 | pipeline.json 10개 (기존 4 + 신규 6) |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** — state-tool CLI |
| 조건 | 6 pilot Step 전부 완료 |
| 기대 결과 | 10건 전부 `ok:true`·`violations_count: 0`. 특히 `spec_id_sequence_invalid`·`spec_key_duplicate`·`spec_key_format_invalid`·`spec_stage_invalid`·`spec_key_stage_mismatch` 전부 0건. opdd key가 `ddl_migration.*` 형식 |
| 도구 | `~/.opal/tools/state-tool/run.sh spec-validate` |
| 실행 명령 | `~/.opal/tools/state-tool/run.sh spec-validate opal/skills/<pilot>/references/pipeline.json` ×10 (독립 재실행) |
| 결과 | **Pass** |
| 상세 | 10/10 전부 `exit=0`, `{"ok": true, "command": "spec-validate", "violations": [], "violations_count": 0}` (opp/opd/opds/opdw/opwt/opgc/oppd/opsdd/oppl/opdd). opdd `DDL/MIGRATION` 단계 key 3건(`ddl_migration.ddl_scripts`, `ddl_migration.pm_gate`, `ddl_migration.user_confirm`) 전부 `ddl_migration.*` 패턴 일치 확인(`re.match` True). 전문 로그: `$WORK/test/spec-validate.log`. |

#### S-5: oppl 19행 baseline 일치 + 특수문자 보존

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5, H-6 |
| 대상 | `opal/skills/opal-pilot-project-loop/references/pipeline.json` |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | Step 1에서 `SKILL.md:139-157`을 행 정규식으로 추출한 19행 확보 |
| 기대 결과 | `task_steps` 19개의 `(id, stage, item)`이 추출 baseline과 **문자 단위 동일**. 백틱·전각 대시(`—`)·체크마크(`✓`)·플레이스홀더(`{NN}`)·소수점 ID(`D1.5`) 원문 보존 |
| 도구 | python3 (행 정규식 재사용) |
| 실행 명령 | `python3 -c "before=json.load($WORK/before/oppl.table.json)['rows']; pj=json.load(.../opal-pilot-project-loop/references/pipeline.json)['task_steps']; compare (id,stage,item) tuples"` |
| 결과 | **Pass** |
| 상세 | `before rows: 19  pipeline task_steps: 19` → `EQUAL (id,stage,item): True`. 특수문자 보존 6건 확인: `id=4 'D1 인터뷰 — 명확화 4요소(...)'`(전각 대시), `id=5 'D1.5 여정 매핑 (...'references/journey-flow.md'...)'`(백틱), `id=9 '...backlog-tool init+add-task...'`, `id=13 '...T{NN} 행 동적 삽입)'`(플레이스홀더), `id=16 'L✓ 종료 판정 (...)'`(체크마크) — 문자 단위 원문 그대로 보존. |

#### S-6: oppd D-7b 확정 13행 일치

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | `opal/skills/opal-pilot-project-dev/references/pipeline.json` |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | TASK.md §확정된 설계 방향 D-7b 13행 표 전사본 확보 |
| 기대 결과 | `task_steps` 13개의 `id`·`key`·`stage`·`item`이 D-7b 표와 **완전 일치**. 행 가감·재설계 0건. `meta.stages == ["TASK","PLAN","WBS","EXECUTE","CLOSE"]` |
| 도구 | python3 |
| 실행 명령 | `sed -n '85,97p' TASK.md` (D-7b 13행 전사) ↔ `python3`로 `opal-pilot-project-dev/references/pipeline.json`의 `task_steps` (id,key,stage,item) 비교 |
| 결과 | **Pass** |
| 상세 | `count actual=13 expected=13` → `EQUAL: True` (id 1~13, key `task.task_md`~`close.done_md`, stage TASK/PLAN/WBS/EXECUTE/CLOSE, item 전부 TASK.md D-7b 표와 완전 일치). `meta.stages == ['TASK','PLAN','WBS','EXECUTE','CLOSE']` → `MATCH: True`. 행 가감·재설계 0건. |

#### S-7: oppd 신설 미러 표 ↔ pipeline.json 정합

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 |
| 대상 | oppd `SKILL.md` 신설 미러 표 + `pipeline.json` |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | oppd Step 완료 (pipeline.json + 미러 표 신설) |
| 기대 결과 | SKILL.md 미러 표 13행의 `(#, 단계, 항목)`이 `task_steps` 13개와 1:1 동일 |
| 도구 | python3 |
| 실행 명령 | `grep -n "^|" opal/skills/opal-pilot-project-dev/SKILL.md` → 122~134행 13행 추출 ↔ `pipeline.json task_steps` 비교 |
| 결과 | **Pass** |
| 상세 | SKILL.md:122~134 미러 표 13행(`# / 단계 / 항목`)을 `task_steps` 13개와 1:1 대조 — 예: `mirror=(1,TASK,'작업')`, `(7,WBS,'Phase2 WBS 작성')`, `(13,CLOSE,'DONE.md 생성')` 등 전부 `MATCH=True`. 13/13 완전 일치. |

#### S-8: `meta.stages` 파생 규칙(DEC-4) 10종 준수

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2, H-11 |
| 대상 | pipeline.json 10개 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | 6 pilot Step 완료 |
| 기대 결과 | 10종 전부 `meta.stages == task_steps[].stage`의 등장순 중복 제거값. **opwt `meta.stages`에 `ANALYSIS` 부재**, **opsdd에 `EXECUTE-LOOP` 부재** |
| 도구 | python3 |
| 실행 명령 | `python3`로 10개 `pipeline.json`의 `task_steps[].stage` 등장순 dedup ↔ `meta.stages` 비교 |
| 결과 | **Pass** |
| 상세 | 10/10 전부 `derive_match=True`: `opp:['TASK','PLAN','EXECUTE','CLOSE']`, `opd:[...7개...]`, `opds`, `opdw`, `opwt:['TASK','PLAN','EXECUTE','QA','CLOSE']`(`ANALYSIS_in_meta=False`), `opgc`, `oppd`, `opsdd:[...7개...]`(`EXECUTE-LOOP_in_meta=False`), `oppl`, `opdd`. **OVERALL MATCH: True**. |

#### S-9: registry `pipeline` 10종 정합 + oppd `domain`

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-12 |
| 대상 | `opal/core/references/opal-skills-registry.json` |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | Step 8(registry) 완료 |
| 기대 결과 | 10 pilot 전부 `pipeline` 존재. 각 값을 `" → "`로 split한 리스트가 해당 `meta.stages`와 **순서·원소 완전 일치**. oppd에 `"domain": "dev"` 존재. `skill-registry.js` 소비 필드(`name`/`alias`/`description`/`triggers`/`paths`) 무변경 |
| 도구 | python3 (json) |
| 실행 명령 | `python3`로 `opal-skills-registry.json`의 10 pilot `pipeline` 값 `" → "` split ↔ 각 `meta.stages` 비교, `git diff`로 registry 변경 필드 요약 |
| 결과 | **Pass** |
| 상세 | 10/10 `registry_match=True` (opp/opd/opds/opdw/opwt/opgc/oppd/opsdd/oppl/opdd 전부). `oppd domain='dev'` 존재 확인. `git diff opal-skills-registry.json`의 변경 필드 집계 결과 `pipeline`(17)·`domain`(1, 신규)·`updated_at`/`version`/`changes`/`date`/`task`(changelog)만 변경 — `name`/`alias`/`description`/`triggers`/`paths` 매칭 0건(무변경, `skill-registry.js` 소비 필드 안전). |

#### S-10: `--rows-from` 잔존 0건 / 채택 10건

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-13, H-18 |
| 대상 | 10 pilot SKILL.md |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** — `awk` 구간 분리 + grep |
| 조건 | Step 2~7 완료 |
| 기대 결과 | **잔존(pilot)** — 대상 6종에서 `## 변경이력` **이전 구간**의 `rows-from.*SKILL.md` 매칭 **0건**(D-9). **잔존(레포 전역)** — `opal/`·`docs/`·`README.md` 전역에서 `.md` 파싱을 **지시·예시**하는 지점 **0건**(D-10). 단 `opal/tools/state-tool/state_tool.py`·`opal/tools/state-tool/README.md`의 언급은 도구 자신의 에러 메시지·분기 설명이므로 **집계 제외**. **채택** — `rows-from.*references/pipeline.json` 매칭이 10개 파일에 각 1건 이상 |
| 도구 | awk / grep |
| 실행 명령 | `awk '/^## 변경이력/{exit}{print}' <SKILL.md> \| grep -nE "rows-from.*SKILL\.md"` (6종) + `grep -rlE "rows-from.*references/pipeline\.json" opal/skills/*/SKILL.md` + 정밀 재확인 `grep -rnE -- "--rows-from[[:space:]]+\S*SKILL\.md" opal/ docs/ README.md \| grep -v state-tool` |
| 결과 | **Pass** |
| 상세 | 대상 6종(`data-design·gc·write-tech·sdd·project-loop·project-dev`) `## 변경이력` 이전 구간 `rows-from.*SKILL\.md` 매칭 출력 없음(0건, D-9). `rows-from.*references/pipeline\.json` 매칭 파일: 10 pilot SKILL.md 전부(opp/opd/opds/opdw/opwt/opgc/oppd/opsdd/oppl/opdd) + `op-task/SKILL.md`(11개, op-task는 S-18 영역) — **채택 10/10 확인**. 정밀 재확인(활성 `--rows-from` 인자가 실제 `SKILL.md`인 줄) 결과 **0건** — 전역 스캔에서 잡힌 나머지 매칭은 전부 (a) `--rows-from`의 실제 인자가 `pipeline.json`, (b) changelog 과거형 서술, (c) PM 사전판정 통과 대상(`task-process.md:49`, `op-task/SKILL.md:223` — 반대 의미) 뿐. D-10(레포 전역 잔존 0건)도 동시 충족. |

#### S-11: 배포 경계 준수

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-15 |
| 대상 | 전체 변경 파일 목록 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | Step 2~10 완료 (Step 11 install 이전) |
| 기대 결과 | `git status --porcelain` 변경 파일이 전부 `opal/`·`docs/`·`tasks/` 하위. `~/.opal/` 하위 직접 편집 흔적 0건 |
| 도구 | git / bash |
| 실행 명령 | `git status --porcelain \| awk '{print $2}' \| grep -vE "^(opal/\|docs/\|tasks/\|\.opal/)"` |
| 결과 | **Pass** |
| 상세 | 출력 없음(0건) — 전 변경 파일이 `opal/`·`docs/`·`tasks/`·`.opal/`(레포 내부 로컬, `~/.opal/` 배포본과 무관) 하위. 변경 목록: `.opal/MEMORY.json`(M), `docs/CONVENTIONS.md`(M), `opal/core/references/{tools.md,harness/task-process.md,opal-skills-registry.json}`(M), `opal/skills/{op-task,opal-pilot-data-design,opal-pilot-gc,opal-pilot-project-dev,opal-pilot-project-loop,opal-pilot-sdd,opal-pilot-write-tech}/SKILL.md`(M), 6× `references/pipeline.json`(신규), `tasks/090-.../`(신규). `~/.opal/` 배포 경로 직접 편집 흔적 **0건**(도구 호출인 `run.sh` 실행만 있었고 배포 파일 편집 없음). |

#### S-12: oppl 헤더 무개명 (범위 밖 변경 차단)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-16 |
| 대상 | oppl `SKILL.md:121`(`## STATE.md 초기 생성`), `:137`(`| # | Stage | 항목 |`) |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | oppl Step 완료 |
| 기대 결과 | 두 줄이 `git diff`에 **등장하지 않음**. 즉 `STATE.md 도메인 치환값`·`| # | 단계 |`로의 개명 0건 |
| 도구 | git diff / grep |
| 실행 명령 | `git diff -- opal/skills/opal-pilot-project-loop/SKILL.md \| grep -E "^[-+].*(## STATE\.md 초기 생성\|\| # \| Stage \|)"` + `grep -n` 원문 확인 |
| 결과 | **Pass** |
| 상세 | `git diff` 결과 두 헤더 라인 모두 diff에 미등장(출력 없음, 0건). 현재 파일 원문 확인: `121:## STATE.md 초기 생성`, `137:| # | Stage | 항목 | 상태 | 시점 |` — 라인 번호·텍스트 그대로 보존, `STATE.md 도메인 치환값`·`| # | 단계 |`로의 개명 0건. |

#### S-18: 레포 전역 구형 지시 4곳 정정 + 도구 자신 파일 무변경

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-18 |
| 대상 | `opal/core/references/tools.md`(`:84` 시놉시스, `:152` 실행 예시) · `opal/core/references/harness/task-process.md:49` · `opal/skills/op-task/SKILL.md:223` |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** — grep 전수 + 변경 파일 목록 대조 |
| 조건 | F-008 Step 완료 |
| 기대 결과 | ① 위 3개 파일에서 `.md` 파싱을 **지시·예시하는 표현 0건** ② `tools.md` 실행 예시가 `references/pipeline.json` 경로로 교체됨 ③ 3개 파일 각각 변경이력 1행 추가 ④ **역방향 검증** — `opal/tools/state-tool/state_tool.py`·`opal/tools/state-tool/README.md` 변경 **0건**(도구 자신의 에러 메시지·분기 설명은 정정 대상이 아님) |
| 도구 | grep / git diff |
| 실행 명령 | `grep -rnE "rows-from\|SKILL\.md" opal/core/references/tools.md opal/core/references/harness/task-process.md opal/skills/op-task/SKILL.md` + `git diff <3파일> \| grep changelog행` + `git status --porcelain -- opal/tools/state-tool/{state_tool.py,README.md}` |
| 결과 | **Pass** |
| 상세 | ① 3개 파일 확인: `tools.md:84`(시놉시스 `<path-to-pipeline.json>` 일반화) / `:152`(실행예시 `--rows-from ~/.opal/skills/opal-pilot-project/references/pipeline.json`), `task-process.md:49`(PM 사전판정 통과 — "SKILL.md 행 표는 사람 열람용 미러" 반대 의미), `op-task/SKILL.md:223`(동일 사전판정 통과) — `.md` 파싱을 지시하는 활성 표현 0건. ② `tools.md:152` 실행 예시가 `pipeline.json` 경로로 교체됨 확인. ③ 변경이력 각 1행 추가 확인: `tools.md`(`+\| v2.12 \| 2026-08-13 16:57 \| state-tool 행 원천 지시 정정...`), `task-process.md`(`+\| v1.7 \|...`), `op-task/SKILL.md`(`+\| v2.5 \|...`) — 3/3. ④ 역방향: `git status --porcelain -- opal/tools/state-tool/state_tool.py opal/tools/state-tool/README.md` 출력 없음(0건, 파일을 열지도 수정하지도 않음). |

### L2. 프로세스 통합 (자동, 실 init 실행 → 상태 재확인)

#### S-13: 10 pilot `init` 채택 실증

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | 10 pilot × `state-tool init --rows-from .../pipeline.json` |
| 계층 | L2 |
| **실행 방식** | **M2 (실행 자동화)** — `$WORK` 하위 임시 경로에서 실 CLI 체인 |
| 조건 | Step 2~7 완료. `$WORK` 준비 |
| 기대 결과 | 10종(모드 조합 포함 20회) 전부 exit 0·`ok:true`. `schema_version: "1.1"`, 전 행 `key` 보유. **deprecation 경고 0회**. `rows_count`가 pilot별 기대치와 일치 |
| 도구 | `~/.opal/tools/state-tool/run.sh init` |
| 실행 명령 | `~/.opal/tools/state-tool/run.sh init $WORK/test/<alias>-<mode> --skill <alias> --mode <semi-agentic\|agentic> --rows-from opal/skills/<pilot>/references/pipeline.json` — 10 pilot × 2 mode = 20회 (opal-test-agent 독립 재실행, EXECUTE Step10 산출물 재사용 아님) |
| 결과 | **Pass** |
| 상세 | `$WORK/test/exitcodes.txt` — 20/20 `exit=0`. stderr 20개 파일 전부 크기 0 bytes → `grep -ril deprecat *.stderr.log` = NONE FOUND(0회). stdout 20/20 `ok=True`. `state.json` 20개 전수 확인: `schema_version=1.1`(20/20), `empty_key=0`(20/20). `rows_count`: opd=16, opdd=15, opds=11, opdw=9, opgc=7, opp=9, oppd=13, oppl=19, opsdd=25, opwt=10 — 전부 기대치 일치. |

#### S-14: oppl·oppd 하드 실패 해소

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | oppl · oppd `init` |
| 계층 | L2 |
| **실행 방식** | **M2 (실행 자동화)** |
| 조건 | Step 1에서 전환 전 실패 증거(`skill_md_parse_error: header not found`) 확보 |
| 기대 결과 | 전환 전 두 pilot이 `skill_md_parse_error`로 실패했음이 기록되고, 전환 후 `.json` 경로로 **oppl `rows_count: 19` / oppd `rows_count: 13`** 이 exit 0·`ok:true`로 성공 |
| 도구 | `state-tool init` |
| 실행 명령 | `cat $WORK/before/{oppl,oppd}.init-failure.json` (전환 전 증거) ↔ S-13에서 독립 재실행한 `$WORK/test/oppl-*/state.json`·`oppd-*/state.json` (전환 후 증거) |
| 결과 | **Pass** |
| 상세 | before: oppl → `{"ok": false, "exit_code": 1, "error": "skill_md_parse_error", "message": "--rows-from SKILL.md에서 행 추출 실패: header not found", "path": ".../opal-pilot-project-loop/SKILL.md"}`. oppd → 동일 구조, `path=".../opal-pilot-project-dev/SKILL.md"`. after(S-13 독립 재실행): oppl `rows_count=19`·`exit=0`·`ok=True`, oppd `rows_count=13`·`exit=0`·`ok=True`. **FAIL(header not found) → PASS(19/13) 쌍 실증**. |

#### S-15: 임시 산출물 레포 미잔류

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-14 |
| 대상 | `$WORK` 및 레포 워킹트리 |
| 계층 | L2 |
| **실행 방식** | **M2 (실행 자동화)** |
| 조건 | S-13·S-14 등 실행형 검증 완료 |
| 기대 결과 | `rm -rf $WORK` 후 `git status --porcelain`이 검증 시작 시점 스냅샷과 **동일**. 임시 `state.json`/`STATE.md` 0건. **`tasks/080~089`의 기존 `state.json` 무변경**(제약 (d)) |
| 도구 | git / bash |
| 실행 명령 | `git status --porcelain`(검증 전후 대조) + `git status --porcelain -- tasks/080-* ... tasks/089-*` |
| 결과 | **Pass** (단, PM 지시로 `rm -rf $WORK` 미실행 — 아래 상세 참조) |
| 상세 | **[PM 지시 반영]** `$WORK/before/`는 재현 불가능한 증거이며 검증 완료 후에도 보존 대상(디스패치 프롬프트 "before 12건 — 삭제 금지")이므로 `rm -rf $WORK`를 실행하지 않았다. 대신 AC(레포 잔류 0건)를 직접 검증: 검증 시작~종료 시점 `git status --porcelain` 출력이 동일(수정 11 + 신규 6 pipeline.json + `tasks/090-.../` — EXECUTE Step2~9 정규 산출물뿐, opal-test-agent의 실행형 산출물(`$WORK/test/*`)은 전부 레포 밖 스크래치패드에만 생성됨을 확인). `tasks/080-*`~`tasks/089-*` 대상 `git status --porcelain` 출력 없음(무변경, 제약 (d) 충족). |

#### S-16: oppd `--wbs` 경로 `--na` 처리 후 CLOSE 진입

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-17 |
| 대상 | oppd 13행 state — id 10~12 (EXECUTE) |
| 계층 | L2 |
| **실행 방식** | **M2 (실행 자동화)** |
| 조건 | oppd `.json` init으로 임시 state 생성 (`$WORK` 하위) |
| 기대 결과 | ~~id 1~9를 done 처리 후 id 10~12를 `mark --na`로 처리하면, id 13(`close.done_md`) 진입이 `stage_transition_violation` 없이 허용됨. 표준화 판단 ③이 런타임에서 성립함을 실증~~ → **[재판정, 캡틴 결정 반영]** `mark --na`는 존재하지 않는 플래그였음이 1차 판정에서 실증됨(아래 이력 참조). PM이 `opal/skills/opal-pilot-project-dev/SKILL.md:171`을 실동작 기준으로 정정(`--force --note`) — 도구 구현 변경 없음, `state_tool.py` 무변경 유지(TASK.md 제약 (a)). 재판정 기준: **정정된 문서가 지시하는 절차가 실제로 동작하는가** |
| 도구 | `state-tool mark` |
| 실행 명령 | **[1차 판정 이력]** `init $WORK/test/oppd-s16 --skill oppd --rows-from .../pipeline.json` → `mark --task-step-id {1..9} --done` → `mark --task-step-id 13 --done`(id10~12 미처리) → `mark --task-step-id 13 --done --force`(무-note) → `mark --task-step-id 10 --done --na`(플래그 존재 확인) → `mark --task-step-id 13 --done --force --note "..."`. **[재판정, 정정 문서 그대로 재실행]** `init $WORK/test/oppd-s16-v2 --skill oppd --mode semi-agentic --rows-from opal/skills/opal-pilot-project-dev/references/pipeline.json` → `mark --task-step-id {1..9} --done` → id10~12 미완 상태로 방치 → **`mark $TP --task-step close.done_md --done --force --note "oppd --wbs: Phase 3 미실행"`**(SKILL.md:171 정정 서술 원문 그대로) → `cat $TP/STATE.md` 확인 → `grep -c "mark --na" opal/skills/opal-pilot-project-dev/SKILL.md` |
| 결과 | **Pass** (재판정) — 1차 판정 Fail은 정확했고 문서 정정으로 해소됨 |
| 상세 | **[1차 판정 — Fail, 정확했음]** `--na`는 argparse 미인식 인자(`unrecognized arguments: --na`, exit=2)로 CLI에 미구현 확인. id10~12 미처리 시 id13 시도는 `stage_transition_violation`(exit=1)로 차단, `--force`만으로도 `note_required_for_force`(exit=1) 차단, `--force --note`만 성공 — 원 문서("mark --na로 허용")와 실제 동작이 불일치했음을 정확히 검출했다.<br><br>**[재판정 — 정정 문서 그대로 재실행, Pass]** ① `init` → `exit=0`, `rows_count=13`. ② id1~9 `mark --task-step-id N --done` 9회 전부 `exit=0, ok=True`. ③ id10~12 상태 확인(방치): `10 execute.actions EXECUTE -> status=pending` / `11 execute.pm_gate EXECUTE -> status=pending` / `12 execute.user_confirm EXECUTE -> status=pending` — 의도대로 미완 유지. ④ **정정 문서 원문 명령 그대로 실행**: `mark $TP --task-step close.done_md --done --force --note "oppd --wbs: Phase 3 미실행"` → `{"ok": true, "command": "mark", "row_id": 13, "stage": "CLOSE", "item": "DONE.md 생성", "status": "done", "timestamp": "2026-08-13 17:51", ...}`, **exit=0** — **판정 기준(exit 0·ok:true로 CLOSE 행 done) 충족, Pass**. ⑤ STATE.md 파이프라인 현황판: `\| 13 \| CLOSE \| DONE.md 생성 \| ✅ \| 2026-08-13 17:51 \|`이고 id10~12는 `⬜`로 그대로 남음 — 문서가 설명한 "EXECUTE 3행 미완 잔존 + CLOSE만 강제 진행" 동작과 일치. ⑥ **의사결정 로그 기재 여부(추가 확인 지시 항목)**: `--note`의 문자열("oppd --wbs: Phase 3 미실행")은 **`state.json`의 row 13 `note` 필드에는 기록됨**(`"note": "oppd --wbs: Phase 3 미실행"`) 그러나 **`STATE.md`의 `## 의사결정 로그` 마크다운 표는 헤더만 있고 데이터 행이 추가되지 않음**(실측 원문: `\| # \| 시점 \| 결정 \| 근거 \|` 헤더 아래 빈 표, `cat STATE.md` 전문 확인) — SKILL.md:171의 "STATE.md에 의사결정 로그를 자동 기재한다" 서술은 **state.json 레벨 note 기록으로는 성립하나 STATE.md `## 의사결정 로그` 섹션 자동 기재는 이번 실행에서 관찰되지 않음**(사소한 문서-동작 간극, 재판정 Pass/Fail 판정 기준 자체에는 영향 없음 — 판정 기준은 "exit 0·ok:true로 CLOSE done"이며 이는 충족됨). 이 점은 후속 문서 정밀화 대상으로 별도 기록. ⑦ `grep -c "mark --na" opal/skills/opal-pilot-project-dev/SKILL.md` → **1**(0 아님) — 위치는 `:837`, `## 변경이력`(`:813`) **이후** 구간의 v5.3 changelog 행("`mark --na`는 CLI에 미구현이며 TEST S-16에서 검출") 하나뿐이며 이는 과거 결함을 기술하는 감사 기록(S-10/S-18과 동일 관례, 활성 지시문 아님). **활성 지시 구간(`## 변경이력` 이전)의 `mark --na` 매칭은 0건**(재확인: `awk '/^## 변경이력/{exit}{print}' SKILL.md \| grep -c "mark --na"` → `0`) — "거짓 지시문 제거"는 **활성 지시문 기준으로 실증됨**. |

### L3. 사용자 협업 (수동, [SUPERVISOR] 마커)

#### S-17: 배포 후 실사용 태스크 시작 검증 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1, H-5 (목표달성 시나리오 — `scenario-gate.md` §2 ①축) |
| 대상 | 배포본 `~/.opal/skills/*/references/pipeline.json` + 실제 pilot 호출 |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업)** — 새 세션이 필요해 자동화 불가. M2 대체 불가 |
| 조건 | Step 11(install 재배포) 완료 |
| 기대 결과 | 캡틴이 **새 세션**에서 전환된 pilot 중 최소 2종(권장: `//oppl`, `//oppd` — 기존 하드 실패 pilot)을 호출했을 때 ① 태스크 폴더·`STATE.md`가 정상 생성되고 ② deprecation 경고가 출력되지 않으며 ③ 행 수가 기대치(oppl 19 / oppd 13)와 일치 |
| 실행자 | [SUPERVISOR] — 캡틴 수동 확인 필요 |
| 결과 | **[SUPERVISOR] 대기** |
| 상세 | opal-test-agent는 새 세션 기동 권한이 없어 본 시나리오를 자동 통과 처리하지 않고 실행 보류한다. 참고로 install 재배포(Step 11)는 이미 완료되어 `~/.opal/skills/opal-pilot-project-loop/references/pipeline.json`·`~/.opal/skills/opal-pilot-project-dev/references/pipeline.json`이 레포와 동일 내용으로 배포되어 있음을 파일시스템으로 확인했다(diff 0). 아래 §3 하단 "PM 표준 요청 양식"을 그대로 PM→캡틴 전달용으로 사용할 것을 권고. |

**PM 표준 요청 양식** (TEST 단계에서 발신)

```
캡틴, [시나리오 S-17]은 사용자 협업 검증이 필요합니다.
요청 내용: 새 세션에서 `//oppl` 과 `//oppd` 를 각각 호출하여 태스크를 시작해주십시오.
기대 결과: 태스크 폴더·STATE.md 정상 생성 / deprecation 경고 미출력 / 행 수 oppl 19·oppd 13.
확인 후 결과(PASS/FAIL + 상세)를 알려주세요.
```

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| R-1 (6 파일 생성·행 1:1 일치) | H-1, H-5, H-6, H-7 | L1 | S-1, S-5, S-6 | `$WORK/verify_rows.py:test_group_a_equivalence` [T090/L1-R1] | opdd15·opgc7·opwt10·oppl19·oppd13·opsdd25 |
| R-1 (opsdd `meta.stages`=EXECUTE) | H-2 | L1 | S-2, S-8 | `$WORK/verify_meta.py:test_opsdd_stages` [T090/L1-R1b] | D-7c 집행 |
| R-1 (`key` 패턴·유일성) | H-4, H-9, H-10 | L1 | S-4 | `$WORK/verify_spec.sh:spec_validate_all` [T090/L1-R1c] | `ddl_migration.*` 포함 |
| R-2 (init 인자 전환·잔존 0) | H-13 | L1 | S-10 | `$WORK/verify_residual.sh:grep_before_changelog` [T090/L1-R2] | D-9 구간 분리 |
| R-3 (미러 주석·oppd 표 신설) | H-8 | L1 | S-7 | `$WORK/verify_mirror.py:test_oppd_mirror` [T090/L1-R3] | 6종 주석 + oppd 표 |
| R-4 (registry 10종 + `domain`) | H-12 | L1 | S-9 | `$WORK/verify_registry.py:test_pipeline_derive` [T090/L1-R4] | `" → "` split 대조 |
| R-5 (전후 동등·잔존·채택) | H-1, H-5, H-14 | L1 + L2 | S-1, S-5, S-6, S-10, S-13, S-15 | `$WORK/verify_equivalence.py:test_all` [T090/L2-R5] | 교체형 목표 |
| R-6 (`spec-validate` 10건) | H-4, H-9, H-10 | L1 | S-4 | `$WORK/verify_spec.sh:spec_validate_all` [T090/L1-R6] | violations 0 |
| R-7 (`EXECUTE-LOOP` 무변경) | H-3 | L1 | S-3 | `$WORK/verify_untouched.sh:execute_loop_guard` [T090/L1-R7] | 17회 + 6파일 해시 |
| R-8 (하드 실패 해소) | H-5 | L2 | S-14 | `$WORK/verify_init.sh:test_oppl_oppd_init` [T090/L2-R8] | rows 19 / 13 |
| 목표 (9→10/10 전환, 실사용 가능) | H-1, H-5 | L2 + L3 | S-13, **S-17** | 수동 [T090/L3-GOAL] | **목표달성 시나리오** |
| R-9 (레포 전역 구형 지시 정정) | H-18 | L1 | S-10, S-18 | `$WORK/verify_residual.sh:repo_wide_scan` [T090/L1-R9] | 도구 자신 파일 역방향 무변경 포함 |
| 제약 (e) 배포 경계 | H-15 | L1 | S-11 | `$WORK/verify_boundary.sh` [T090/L1-C-e] | `~/.opal/` 직접편집 0 |
| 범위 제외 (oppl 헤더 개명 금지) | H-16 | L1 | S-12 | `$WORK/verify_untouched.sh:oppl_header` [T090/L1-SCOPE] | 경계/부정 시나리오 |
| 표준화 판단 ③ (`--wbs` `--na`) | H-17 | L2 | S-16 | `$WORK/verify_wbs.sh` [T090/L2-D7b3] | 경계 시나리오 |

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | N/A | Skip | 변경 영역이 데이터(JSON)·문서(SKILL.md)뿐이며 `state_tool.py` 등 소스코드 무변경(§18 역방향 검증으로 확인). 코드 린터 대상 없음. |
| 2 | 타입 체크 | N/A | Skip | 동상 이유. |
| 3 | 포맷터 | N/A | Skip | 동상 이유. |
| 4 | JSON 파싱 유효성 (10 pipeline.json + registry) | `python3 -c "json.load(open(f))"` ×11 | **Pass** | 10개 pilot `pipeline.json`(opp/opd/opds/opdw/opdd/opgc/opwt/opsdd/oppl/oppd) + `opal-skills-registry.json` 전부 `json.load` 성공(`OK <path>` ×11, 예외 0건). |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | **Pass** | 변경 파일 12건 전체를 `grep -inE "(api[_-]?key\|secret\|password\|token)\s*[:=]\s*['\"][A-Za-z0-9]{8,}"`로 스캔 — 매칭 0건. |
| 2 | .gitignore 확인 | **Pass** | `git check-ignore -v "$WORK"` → `fatal: ... is outside repository` — `$WORK`가 레포 추적 범위 밖(스크래치패드)임을 git 자체가 확인, `.gitignore` 대상 여부 판단 불필요. |
| 3 | 경로 이탈 검사 (`$WORK`가 레포 밖인지) | **Pass** | `python3`로 `work.startswith(repo)` 검사 → `False` → `$WORK가 레포 밖: True`. 레포 경로: `/Volumes/Data/AIStudio/workspace/ai-framework`, `$WORK`: `/private/tmp/claude-501/.../scratchpad/eq-verify` — 완전 별개 트리. |

## 7. 판정

**Partial Fail — S-1~S-16, S-18 (18건) Pass, S-17 [SUPERVISOR] 대기(미평가).**

> **[재판정 갱신, 2차]** S-16은 1차 판정 Fail(정확한 검출) → 캡틴 결정에 따른 SKILL.md 문서 정정(`opal/skills/opal-pilot-project-dev/SKILL.md:171`, `mark --na`→`mark --task-step close.done_md --done --force --note "..."`) → **재판정 Pass**로 갱신되었다. 도구(`state_tool.py`) 자체는 무변경(TASK.md 제약 (a) 유지) — 문서를 실동작에 맞춰 정정하는 방식으로 해소됨. 종합 판정을 **Critical Fail이 아닌 Partial Fail**에서 이제 **전건 Pass + S-17 대기**로 격상한다. 판정 사유가 "P2 경계 시나리오라 핵심 목표를 훼손하지 않음"에서 "재판정 결과 자체가 Pass"로 바뀐 것이며, S-17(L3 [SUPERVISOR], 미평가)이 남아있어 "All Pass"로는 선언하지 않고 **Partial Fail**(대기 1건 존재, 자동 통과 처리 금지 원칙)로 유지한다.

### 판정 근거

- **핵심 판정 축 4종 전부 Pass**: ① 전후 동등(D-4) — 그룹 A 4종 8/8(2모드) `[(row_id,stage,item)]` 완전 동일(S-1). ② 하드 실패 해소 — oppl/oppd `skill_md_parse_error(header not found)` → `rows_count 19/13` exit 0 쌍 실증(S-14). ③ 잔존 0/채택 10 — deprecated `.md` 파싱 경로의 활성 호출자 0건, `rows-from.*pipeline.json` 10/10 채택, 레포 전역 정밀 재확인도 0건(S-10, S-18). ④ 무변경 보장 — opsdd `EXECUTE-LOOP` 17=17, `execute-loop-guide.md`·외부 6+2파일·`state_tool.py`·`state-tool/README.md` 전부 `git status --porcelain` 0건(S-3, S-18).
- **S-16 재판정 Pass**: 1차 판정에서 "`mark --na`는 CLI에 미구현, 기본 동작은 CLOSE 진입을 `stage_transition_violation`으로 차단"을 정확히 검출(Fail은 정당했음). 캡틴이 도구 구현이 아닌 **문서 정정**으로 처리하기로 결정(TASK.md 제약 (a) "state_tool.py 소스 무변경" 유지) — SKILL.md:171을 실동작(`--force --note`) 기준으로 재서술. 정정된 문서 명령을 그대로 재실행: `mark $TP --task-step close.done_md --done --force --note "oppd --wbs: Phase 3 미실행"` → `exit=0`, `{"ok": true, ..., "status": "done"}` — **판정 기준(exit 0·ok:true로 CLOSE done) 충족, Pass**. `grep -c "mark --na" SKILL.md`는 원시값 1이나 위치가 `## 변경이력`(:813) 이후 v5.3 changelog 행(:837, 과거 결함 기술용 감사 기록)뿐이고, 활성 지시 구간(`## 변경이력` 이전) 재확인 결과는 **0**(`awk '/^## 변경이력/{exit}{print}' | grep -c "mark --na"` → `0`) — 거짓 지시문 제거가 활성 지시문 기준으로 실증됨. 다만 SKILL.md:171의 "STATE.md에 의사결정 로그를 자동 기재한다" 서술 중 `STATE.md`의 `## 의사결정 로그` **마크다운 표 자체**는 이번 실행에서 데이터 행이 채워지지 않음(`--note` 문자열은 `state.json`의 row 13 `note` 필드에는 기록됨) — 재판정 Pass/Fail 판정 기준(exit0·ok:true) 자체에는 영향 없는 문서 정밀화 여지로 별도 기록.
- **S-17 [SUPERVISOR] 대기**: L3 사용자 협업 시나리오는 opal-test-agent가 실행할 수 없는 새 세션 실사용 검증이므로 자동 통과 처리하지 않고 보류했다. 캡틴이 직접 수행하기로 확정(코디네이터 지시 반영). §3 하단 PM 표준 요청 양식을 그대로 PM→캡틴 전달에 사용 가능.
- **코드 품질(§5)**: JSON 파싱 유효성 11/11 Pass, 린트/타입체크/포맷터는 대상 없음(N/A, 데이터·문서 변경만).
- **보안(§6)**: 하드코딩 시크릿 0건, `$WORK` 레포 밖 확인, 경로 이탈 0건 — 전부 Pass.
- **목업 미잔존**: S-1~S-16, S-18(18건)은 EXECUTE Step10의 after 스냅샷을 그대로 신뢰하지 않고 **opal-test-agent가 독립적으로 CLI를 재실행**(`state-tool init` 20+1회, `spec-validate` 10회, `mark` 다수 — S-16 재판정 포함)하여 자체 증거를 확보했다 — 목업·대체값 0건.

### 갱신된 집계
- **Pass**: 18건 (S-1~S-16, S-18)
- **Fail**: 0건
- **[SUPERVISOR] 대기**: 1건 (S-17)

### 캡틴/PM 후속 조치 권고
1. S-16: (해소됨) SKILL.md:171 문서 정정으로 실동작과 서술 일치. 단, "STATE.md 의사결정 로그 자동 기재" 서술이 이번 실측에서 STATE.md 표 자체엔 반영되지 않았음(state.json row-note 레벨까지만 확인됨) — 필요 시 후속 태스크에서 문서를 "state.json note 필드에 기록됨"으로 한 단계 더 정밀화하거나, `state_tool.py`가 STATE.md 의사결정 로그 표에도 실제로 행을 추가하도록 구현할지 결정.
2. S-17: PM이 §3 요청 양식으로 캡틴에게 새 세션 검증 요청 발신 (캡틴이 직접 수행 확정).

### PM Gate 체크 (7대 강제 룰)

- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 (grep 확인)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전 (미매핑 시나리오 없음 — H-1~H-18 전건, S-1~S-18 전건)
- [x] L1/L2/L3 계층 명시 (모든 시나리오)
- [x] L3 [SUPERVISOR] 마커 존재 + PM 요청 양식 첨부 (S-17)
- [x] 리스크 가설 표(§1) H-N ID와 시나리오 S-N 1:N 매핑 완전
- [x] 모든 시나리오에 실행 방식(M1/M2/M3) 명시
- [x] FE 변경 시 M2 시나리오 포함 — **해당 없음** (FE 화면·컴포넌트·인증/인가·외부 API 연동 변경 0건). 다만 실행형 M2를 4건(S-13·S-14·S-15·S-16) 별도 배치했다
- [x] **목표 커버** — TASK.md R-1~R-9 전체가 §4 매핑 표에 커버되고, 사용자/운영 계층 목표달성 시나리오(S-17)가 §3 L3에 존재
