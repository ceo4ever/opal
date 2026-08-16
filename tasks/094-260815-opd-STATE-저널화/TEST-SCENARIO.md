# TEST SCENARIO: STATE.md 파생 섹션 제거 — 저널로 재정의

> 작성일: 2026-08-16 | 상태: 작성 완료
> 작성자: 알투(PM) + 캡틴 페어 | PLAN.md 가설 표(H-1~H-12) + TEST-SCENARIO 신설 H-13~H-17 기반
> self-confirming 방지: PLAN 워커(opal-plan-agent)와 다른 작성자가 수행함

## 0. RED-first 트랙 판정

> 규칙 SSOT: `opal/core/references/harness/red-first.md` §1.5 하이브리드 자동분기

| 기능 | 변경 영역 | 트랙 판정 | 근거 |
|------|----------|----------|------|
| F-001 저널 전환·의사결정 로그 재배선 | 비즈니스 로직 + 파일 I/O 계약 | **RED-first 강제** | §1.5 "비즈니스 로직" — 의사결정 로그 유실은 self-confirming 위험 최상위(H-1 P0) |
| F-002 마커 게이트·import 제거 | API 계약(CLI stdout·exit code) | **RED-first 강제** | §1.5 "API 계약" |
| F-003 `show` 렌더 원천 단일화 | API 계약 + 정확성 버그 수정 | **RED-first 강제** | §1.5 "버그 수정(회귀 방지)" — 레거시 동결 표 오반환은 현존 결함 |
| F-004 문서 개정 (하네스·pilot·docs) | 설정·문서 | **구현 후 검증** | §1.5 "설정·문서" — 산출물 검사(결정론 grep 스윕)로 검증 |
| F-005 테스트 재작성·실증 | 테스트 자체 | **N/A** | 검증 수단이므로 트랙 대상 아님 |

**종합 판정**: 코드 3기능(F-001·F-002·F-003)에 **RED-first 트랙 적용**. `state-tool verify --red-check` 게이트를 EXECUTE(GREEN) 진입 전에 호출한다.

[MUST] RED 테스트 코드 작성 주체는 `opal-test-agent`(mode: red)이며 EXECUTE 구현 워커(`opal-be-agent`)와 **분리**한다 (`red-first.md` §2).
[MUST] GREEN/fix 루핑 중 RED 테스트 파일 수정 금지 (`red-first.md` §3). 위반 시 블로커.

---

## 1. 리스크 가설 표

> PLAN.md §리스크 가설 표에서 승계. 시나리오 컬럼은 본 문서 §3에서 확정.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | F-001 `sync_state_md` 재배선 | 의사결정 로그 유실 — 마커 게이트 제거 후에도 `append_decision_log`가 조용히 no-op | **P0** | L1 + L2 | S-1, S-2, S-3, S-4, S-21, S-29, S-30, S-32 |
| H-2 | F-001 저널 쓰기 예외 흡수 | 파이프라인 차단 vs 로그 유실의 이중 실패 | **P0** | L2 | S-4, S-5 |
| H-3 | F-001/F-002 `save_state_json` → 저널 순서 | SSOT/미러 순간 불일치 | P1 | L2 | S-4, S-5 |
| H-4 | F-002 마커 제거 + 레거시 STATE.md 공존 | 레거시 파일에서 예외·중복 삽입·정규식 오매칭 | P1 | L2 | S-6, S-8, S-11, S-29 |
| H-5 | F-003 `cmd_show` 렌더 원천 단일화 | `show`가 레거시 동결 표를 최신인 양 반환 | **P0** | L2 | S-10, S-11, S-20, S-24 |
| H-6 | F-003 `show` 응답 계약 | `marker_present` 제거/의미 변경이 소비자 파괴 | P1 | L1 | S-23, S-25 |
| H-7 | F-002 `--import-existing` 제거 | 미발견 호출부가 있으면 파이프라인 즉시 실패 | P1 | L2 | S-9, S-22 |
| H-8 | F-005 테스트 재작성 | 커버리지 공백 / padding 유입 | P1 | L1 + L3 | S-19 |
| H-9 | F-004 문서 개정 (약 29파일) | 구형 잔존 0 미달 + changelog 오삭제 | P1 | L3(결정론 스윕) | S-7, S-12, S-15, S-16, S-17, S-26, S-31 |
| H-10 | F-004 표준 문구 치환 | 표 전제(B) 제거 시 도구 규율(C)까지 소실 | P1 | L3 | S-14 |
| H-11 | F-005 install 재배포 | 미배포 시 실증이 구버전으로 수행되어 거짓 통과 | P1 | L2 | S-18, S-27 |
| H-12 | F-003 검증 루프 상태 | `- 진행:`/`- 검증:` 소멸로 재개 정보 유실 | P1 | L3 | S-13 |
| H-13 | 전체 — 소유자 수용성 | **파일은 남기되 파생을 뺀 결과가 실제로 쓸 만한가** — 자동 검증 불가 영역 | P1 | **L3 [SUPERVISOR]** | S-28 |

| H-14 | R-10 worktree 허브 자산 접근 | 레포 루트 기준 경로 해석이 worktree에서 허브 자산을 못 찾음 — 한쪽 환경만 고치면 반대쪽이 깨진다 | P1 | L2 | S-33 |
| H-15 | R-11 G-1 모드 경계 상수 | **소유자 주권 상실** — semi-agentic(기본 모드) opdd에서 설계 확정 3건이 미노출 통과 | **P0** | L1+L2 | S-34, S-38, S-41 |
| H-16 | R-11 G-2 CLOSE 폴백 | 확인 행 0개 파이프라인(opgc) 데드락 / 반대로 폴백이 너무 느슨하면 무단 CLOSE 허용 | P1 | L2 | S-35, S-39 |
| H-17 | R-11 G-3 파생 신호 | 계산식 변경이 `state.json` 스키마·`build_todo_mirror` 반환 구조를 오염 — 094 제약 ①③ 위반 | P1 | L1+L2 | S-36, S-37, S-40, S-41 |

> H-13은 PLAN에 없던 신규 가설이다. 이번 태스크의 핵심 의사결정(b안 — 파일 존치 + 파생 전면 제거)이 실제 사용에서 옳았는지는 **자동 검증으로 판정할 수 없다**. 태스크 092 교훈(`.opal/MEMORY.json` history — "pytest 전건 GREEN 상태에서 실환경 검증이 결함을 2회 검출")에 근거해 소유자 협업 시나리오를 명시 추가한다.

---

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터

> 이 태스크는 DB가 없다. 테이블 대신 **파일 자산**을 데이터 단위로 삼는다.

| 자산 | 식별자 | 상태 | 출처 |
|------|--------|------|------|
| 신규 태스크 폴더 | `tmp_task_new/` | 빈 폴더 (state.json·STATE.md 없음) | fixture (pytest `tmp_path`) |
| pipeline 스펙 | `opal/skills/opal-pilot-dev/references/pipeline.json` | 기존 파일 무변경 | 실 파일 (repo) |
| 레거시 STATE.md | `tasks/093-260815-opd-사용자확인행-자동승인-일원화/STATE.md` | 마커+표+`## 현재 상태` 보유 (구형) | 실 파일 **사본** — 원본 무변경 [MUST] |
| 레거시 state.json | 위 093 태스크의 `state.json` | rows 보유 | 실 파일 **사본** |
| 손상 저널 | `tmp_task_broken/STATE.md` | `## 의사결정 로그` 표 헤더만 제거 | fixture (테스트가 생성) |
| 읽기전용 저널 | `tmp_task_ro/STATE.md` | 권한 `0444` | fixture (`os.chmod`) |
| 배포본 도구 | `~/.opal/tools/state-tool/state_tool.py` | install 전 = 구버전 / 후 = 신버전 | install-mac.sh 산출 |
| 프로젝트 소스 | `.opal-worktrees/task_094/opal/tools/state-tool/state_tool.py` | 변경 후 | worktree 작업본 |

> [MUST] 레거시 자산은 **반드시 사본으로 조작**한다. 원본 `tasks/093-*/`는 소급 변경 금지 제약(TASK.md 확정 방향 §4) 대상이므로 바이트 무변경을 S-26이 검증한다.

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (CUD/호출) | Then (re-read) |
|---------|------------|----------------|---------------|
| S-1 | 빈 태스크 폴더 | `init --skill opd --mode agentic --rows-from pipeline.json` | STATE.md 본문에 금지 4패턴 0건 |
| S-2 | S-1 산출 저널 | `advance` → `mark` → `block` 연속 | `## 의사결정 로그`·`## 블로커` 2섹션 보존 |
| S-3 | S-1 산출 저널 (로그 1행 기존재) | `mark --auto-pass --note 'x'` | 로그 표 행 +1, 기존 행 전건 보존, `#` 1부터 연속 |
| S-4 | STATE.md **삭제**된 태스크 | `mark --auto-pass --note 'x'` | `ok:true` + STATE.md 자동 생성 + 로그 1행 |
| S-5 | STATE.md 권한 `0444` | `mark --auto-pass --note 'x'` | `ok:true`·exit 0 + stdout `journal_warning.decision` 원문 + state.json 정상 갱신 |
| S-6 | STATE.md (i)삭제 (ii)마커만 제거 (iii)임의 텍스트 3케이스 | `advance`/`mark` | 3케이스 전부 `ok:true`·exit 0 |
| S-7 | 신형 코드 | `len(ERROR_CODES)` 조회 + README 파싱 | `marker_missing`·`import_failed` 부재, `import_existing_removed` 존재, 종수 == README 기재값 |
| S-8 | 마커 없는 STATE.md | `validate` | `violations[]`에 `marker_missing` 0건 |
| S-9 | 빈 태스크 폴더 | `init ... --import-existing` | `{"ok":false,"error":"import_existing_removed"}` 단일 라인 JSON + exit 1 |
| S-10 | S-1 산출 신규 태스크 | `show --format md` | `state.json.rows[]` 파생 표 + 모드/상태/다음액션 3줄 + `marker_present:false` |
| S-11 | 레거시 사본 — **표 내용을 state.json과 의도적 불일치**시킴 | `show --format md` | 반환 표가 **state.json 값**과 일치 + 배너 1줄 + `marker_present:true` |
| S-12 | 개정 후 `opal/`·`docs/` | 결정론 grep 스윕 (§5.2 명세) | 현재시제 본문 금지 패턴 0건 |
| S-13 | 개정 후 하네스·가이드 | 문서 정합 확인 | 검증 루프 진행률 새 보관처 명시 + 세션 복원이 `show` 호출로 기술 |
| S-14 | 개정 후 pilot·가이드 | 표준 문구 존재 확인 | 표 전제 0건 **AND** 도구 규율 문장 파일당 >=1건 |
| S-15 | 개정 후 README + 코드 | 종수 대조 | README 종수 == `len(ERROR_CODES)`, 하네스 2문서에 숫자 부재 |
| S-16 | 개정 후 전역 문서 | SSOT 서술 grep | "STATE.md…유일한 SSOT" 0건 |
| S-17 | 개정 후 전역 문서 | `marker_missing` grep | 현재시제 본문 0건 (changelog 보존) |
| S-18 | S-27 통과한 배포본 | `init`→`advance`→`mark`→`block`→`add-row` | 5명령 전부 `ok:true`, exit 0 |
| S-20 | S-18 실증 태스크 | `show --format md` / `--format json` | 두 포맷 모두 현황 정상 반환 |
| S-21 | 저널 (헤더 라인 보유) | `advance` / `mark` | `> 최종 갱신:` 타임스탬프 갱신됨 |
| S-22 | 빈 태스크 폴더 | `init --rows-from <pipeline.json>` | `rows[].key` 영속화 + `schema_version` 1.1 유지 |
| S-23 | 정상 태스크 | `advance`/`mark`/`block`/`add-row`/`status` 5명령 | 응답 키 삭제 0건, `journal_warning`만 조건부 추가 |
| S-24 | 레거시 사본 / 신규 저널 2케이스 | `show --format full` | 레거시만 배너 부착, 원문 무손상 반환 |
| S-25 | 정상 태스크 | `show --format md`/`json`/`full` | 3포맷 응답 키 집합 기존과 동일 |
| S-19 | 변경 후 테스트 스위트 + `git diff` | `pytest tests/ -v` + 삭제/신규 대응 감사 + 삭제 함수 총수 대조 | fail 0 + 삭제 1:1 대응 + 신규 기능 5종 커버 + **초과 삭제 0건** |
| S-26 | 개정 후 repo | `git diff --stat` | changelog 행·`.opal/brain/pages/**`·`tasks/093-*` 무변경 |
| S-27 | install 실행 후 | `diff` 배포본 vs 소스 | 차이 0 |
| **S-29** | **레거시 093 사본 (마커+표+`## 현재 상태` 보유)** | **`advance` → `mark --auto-pass --note` → `block` 연속 쓰기** | **전건 `ok:true` + 로그 1행 추가 + 레거시 표 바이트 동결 + 중복 삽입 0** |
| **S-30** | **손상 저널 `tmp_task_broken` (`## 의사결정 로그` 헤더 제거)** | **`mark --auto-pass --note` 2회 연속** | **골격 append 복구 + 로그 기재 + 기존 본문 무손실 + 골격 중복 0(멱등)** |
| **S-31** | **개정 후 하네스 3문서 + `init` 실산출 저널** | **저널 구조·`show` 경로 확인 + 템플릿↔코드 산출물 대조** | **3문서에 저널 구조·`show` 명시 + `state-template.md` 템플릿과 실산출 골격 일치** |
| **S-32** | **정상 저널** | **`--note`에 `|`·개행 포함 입력으로 `mark --auto-pass`** | **표 구조 무파괴 + 행 +1 + 원문 보존** |
| **S-33** | **worktree + 허브 2환경** | **`TestVerify` 실행 + `git diff`로 헬퍼 추가 확인** | **양쪽 PASS + 신규 경로 헬퍼 0건** |
| **S-34** | **semi-agentic opdd 태스크** | **`advance model.modeling`** | **`auto_approved` 비고 + `dict.user_confirm` pending 유지 + `user_confirmation_required` 거부** |
| **S-35** | **opgc 태스크 앞 6행 완료** | **`mark close.done_md --done` (±`--owner user`)** | **`--owner user` 있으면 ok / 없으면 `close_gate_violation`** |
| **S-36** | **agentic opd 16행** | **전 행 순회하며 `show --format json`** | **`next_action`이 어느 시점에도 "사용자 확인" 미포함** |
| **S-37** | **agentic 태스크 (작업·게이트 완료 단계)** | **`advance`/`mark` 후 `todo_mirror` 캡처** | **해당 단계 todo가 `completed`로 렌더** |
| **S-38** | **개정 후 pilot 4종 SKILL.md** | **무분기 P-5 패턴 grep** | **잔존 0건 + 모드 분기 문안 존재** |
| **S-39** | **개정 후 하네스 §3 경계 표** | **표 파싱 + 상수·pipeline.json 대조** | **10종 등재 + 모순 0** |
| **S-40** | **R-11 적용 전후 코드** | **`git diff` + 스키마·시그니처 대조** | **신규 상수·분기 0 / `next_action` 스키마 불변 / `build_todo_mirror` 반환 구조 불변** |
| S-28 | **실제 의사결정 2건+·블로커 1건+ 가 기재된 저널** (094 자신 또는 등가) | 캡틴이 저널·`show` 직접 확인 | 수용 판정 (반증 조건 포함) |

---

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 실 데이터 입력)

#### S-1: 신규 저널에 파생 4종 잔존 0

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 (전제) |
| 대상 | `_build_new_state_md` 저널 템플릿 (R-1 AC(a)) |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | 빈 태스크 폴더에서 `init --skill opd --mode agentic --rows-from <pipeline.json>` |
| 기대 결과 | 산출 STATE.md에 `pipeline:start` / `\| # \| 단계 \| 항목 \|` / `## 현재 상태` / `## 다음 액션` 각각 **0건** |
| 도구 | pytest (subprocess CLI 실행 + 실 파일 read) |
| 실행 명령 | `cd opal/tools/state-tool && python3 -m pytest tests/test_state_tool.py -v -k test_s1_new_journal_has_zero_derived_artifacts` |
| 결과 | **Pass** |
| 상세 | `TestNextActionAutoDerive::test_s1_new_journal_has_zero_derived_artifacts` PASSED. 실측: 실 pipeline.json(opd)로 `init --skill opd --mode agentic` 실행 후 산출 STATE.md에 `pipeline:start`/`\| # \| 단계 \| 항목 \|`/`## 현재 상태`/`## 다음 액션` 4패턴 전부 0건. 배포본(`~/.opal/tools/state-tool/run.sh`)으로 별도 실증(스크래치 태스크 `s18_task`) 결과도 동일 — 실산출 STATE.md에 `# STATE:`/`> 최종 갱신:`/SSOT 안내 2줄/`## 의사결정 로그`/`## 블로커` 5줄만 존재, 4금지패턴 0건 재확인. 전체 스위트: `343 passed, 84 subtests passed, 0 failed`. |

#### S-2: 저널 2섹션 보존 (연속 갱신 후)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | 저널 구조 불변성 (R-1 AC(b)) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | S-1 산출 저널에 `advance` → `mark` → `block` 연속 호출 |
| 기대 결과 | `## 의사결정 로그` 표 헤더와 `## 블로커` 섹션이 3회 호출 후에도 전부 보존 |
| 도구 | pytest |
| 실행 명령 | `cd opal/tools/state-tool && python3 -m pytest tests/test_state_tool.py -v -k test_s2_journal_two_sections_survive_consecutive_updates` |
| 결과 | **Pass** |
| 상세 | `TestNextActionAutoDerive::test_s2_journal_two_sections_survive_consecutive_updates` PASSED — S-1 산출 저널에 `advance`→`mark`→`block` 3회 연속 호출 후 `## 의사결정 로그` 표 헤더와 `## 블로커` 섹션 둘 다 보존 확인. 배포본 실증(S-18 시퀀스: init→advance→mark→add-row→block)에서도 최종 STATE.md에 두 섹션 보존 확인(§L2 S-18/S-20 결과 참조). |

#### S-3: 의사결정 로그 누적 무손실

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | `append_decision_log` 행 수 계산 보강 (R-2 AC) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | 로그 1행이 이미 있는 저널에 `mark --auto-pass --note '두번째'` (실재 트리거 — TASK.md R-2 AC 정정 이력 참조) |
| 기대 결과 | 표 행 +1 (총 2행), 기존 1행 원문 보존, `#` 컬럼이 1·2로 연속 |
| 도구 | pytest |
| 실행 명령 | `cd opal/tools/state-tool && python3 -m pytest tests/test_state_tool.py -v -k test_s3_decision_log_accumulates_without_loss` |
| 결과 | **Pass** |
| 상세 | 로그 1행이 이미 있는 저널에 `mark --auto-pass --note '두번째'` 호출 → 표 행 +1(총 2행), 기존 1행 원문 보존, `#` 컬럼 1·2 연속 확인. `append_decision_log` off-by-one 수정 반영됨. |

#### S-7: 에러 카탈로그 코드↔문서 정합

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 |
| 대상 | `ERROR_CODES` + README 카탈로그 (R-3 AC(b), R-9 AC(a)) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | 코드 변경·문서 개정 완료 후 `len(ERROR_CODES)` 실측 및 README 카탈로그 행 수 파싱 |
| 기대 결과 | `marker_missing`·`import_failed` 부재 / `import_existing_removed` 존재 / **실측 종수 == README 기재 종수** (093 머지 후 실측 **44** — 45 − 2 + 1. 어느 경우든 실측값이 기준이며 리터럴을 신뢰하지 않는다) |
| 도구 | pytest |
| 실행 명령 | `cd opal/tools/state-tool && python3 -m pytest tests/test_state_tool.py -v -k test_s7_error_catalog_marker_import_realignment` (+ 직접 실측: `python3 -c "...len(ERROR_CODES)..."`) |
| 결과 | **Pass** |
| 상세 | 실측 `len(ERROR_CODES) == 44`, `marker_missing` 부재, `import_failed` 부재, `import_existing_removed` 존재 — 전부 확인. README.md `## 에러 코드 카탈로그` 헤더 "44종 실측 SSOT" 표기 및 실제 표 행 수(44) 일치(별도 awk 카운트로 재확인, S-15와 공유 증거). |

#### S-8: validate에서 마커 위반 소멸

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | `cmd_validate` 마커 검사 삭제 (R-3 AC(a)) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | 마커 없는 STATE.md를 가진 태스크에서 `validate` 실행 |
| 기대 결과 | `violations[]`에 `marker_missing` 항목 0건 |
| 도구 | pytest |
| 실행 명령 | `cd opal/tools/state-tool && python3 -m pytest tests/test_state_tool.py -v -k test_s8_validate_no_marker_missing_violation` |
| 결과 | **Pass** |
| 상세 | 마커 없는 STATE.md에서 `validate` 실행 → `violations[]`에 `marker_missing` 0건 확인. `cmd_validate` 마커 검사 코드 삭제 반영 확인. |

#### S-10: `show --format md` 신규 태스크 렌더

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | `cmd_show` md 분기 렌더 원천 단일화 (R-5 AC(b)) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | S-1 산출 신규 태스크(마커 없음)에서 `show --format md` |
| 기대 결과 | `state.json.rows[]` 파생 표 반환 + `- 모드:`/`- 상태:`/`- 다음 액션:` 3줄 포함 + `marker_present:false` |
| 도구 | pytest |
| 실행 명령 | `cd opal/tools/state-tool && python3 -m pytest tests/test_state_tool.py -v -k test_s10_show_md_new_journal_renders_from_state_json` |
| 결과 | **Pass** |
| 상세 | `TestShowAsQueryStandard::test_s10_show_md_new_journal_renders_from_state_json` PASSED. 배포본 실증(S-18/S-20 `show --format md` 결과)에서도 `state.json.rows[]` 파생 표 + `- 모드:`/`- 상태:`/`- 다음 액션:` 3줄 + `marker_present:false` 확인(§L2 결과 참조). |

#### S-21: `> 최종 갱신:` 헤더 존치 회귀

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 (부수) |
| 대상 | `update_state_md_header` 존치 (D-3 결정) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | 저널에 `advance`/`mark` 호출 |
| 기대 결과 | `> 최종 갱신:` 라인 타임스탬프가 호출 시각으로 갱신됨 (기존 테스트 4건 유지) |
| 도구 | pytest |
| 실행 명령 | `cd opal/tools/state-tool && python3 -m pytest tests/test_state_tool.py -v -k test_s21_header_timestamp_updates_after_journal_refactor` |
| 결과 | **Pass** |
| 상세 | 저널에 `advance`/`mark` 호출 시 `> 최종 갱신:` 라인 타임스탬프가 호출 시각으로 갱신됨(기존 4건 회귀 유지) 확인. |

#### S-23: 갱신 5명령 응답 키 계약 유지

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | stdout JSON 계약 (제약 ③) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `advance`/`mark`/`block`/`add-row`/`status` 각각 실행 후 응답 키 집합 수집 |
| 기대 결과 | 기존 키 **삭제 0건**, `journal_warning`만 조건부 추가 |
| 도구 | pytest |
| 실행 명령 | `cd opal/tools/state-tool && python3 -m pytest tests/test_state_tool.py -v -k test_s23_five_update_commands_response_keys_preserved` |
| 결과 | **Pass** |
| 상세 | `advance`/`mark`/`block`/`add-row`/`status` 5명령 응답 키 집합 수집 결과 기존 키 삭제 0건, `journal_warning`만 조건부 추가 확인. 배포본 실증(S-18 5명령 연속 실행)에서도 각 응답에 `ok`/`command`/`row_id`/`stage`/`item`/`status`/`timestamp` 등 키 유지 확인. |

#### S-25: `show` 3포맷 응답 키 계약 유지

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | `show --format md/json/full` 응답 계약 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | 3포맷 각각 실행 후 응답 키 집합 수집 |
| 기대 결과 | `ok`·`command`·`format`·`marker_present`·`content`/`data` 키 집합이 기존과 동일(추가만 허용, 삭제 0) |
| 도구 | pytest |
| 실행 명령 | `cd opal/tools/state-tool && python3 -m pytest tests/test_state_tool.py -v -k test_s25_show_three_formats_response_key_contract_preserved` |
| 결과 | **Pass** |
| 상세 | `show --format md/json/full` 3포맷 응답 키 집합(`ok`/`command`/`format`/`marker_present`/`content` 또는 `data`) 기존과 동일 확인(추가만 허용, 삭제 0). 배포본 실증(S-20)의 `show --format md`/`--format json` 실호출 결과도 동일 키 구조. |

#### S-22: `--rows-from` 정상 경로 회귀

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | 074 key 재접합 삭제가 정상 경로를 훼손하지 않음 (R-4 AC) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `init --rows-from <pipeline.json>` 실행 |
| 기대 결과 | `rows[].key` 영속화 포함 기존과 동일 동작, `schema_version` 1.1 유지 |
| 도구 | pytest |
| 실행 명령 | `cd opal/tools/state-tool && python3 -m pytest tests/test_state_tool.py -v -k test_s22_rows_from_json_regression_after_import_existing_removal` |
| 결과 | **Pass** |
| 상세 | `init --rows-from <pipeline.json>` 정상 실행 — `rows[].key` 영속화 포함 기존과 동일 동작, `schema_version` "1.1" 유지 확인. 074 key 재접합 삭제가 정상 경로를 훼손하지 않음. |

---

### L2. 프로세스 통합 (자동, 실 파일 read→CUD→re-read)

#### S-4: STATE.md 삭제 상태에서 의사결정 로그 무손실 [P0]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | `ensure_journal_skeleton` + fail-open 재배선 (R-2 AC) |
| 계층 | L2 |
| **실행 방식** | **M1** (실 파일 I/O + CLI subprocess) |
| 조건 | 정상 태스크에서 STATE.md를 **삭제**한 뒤 `mark --task-step <key> --done --auto-pass --note '삭제상태기재'` |
| 기대 결과 | `ok:true` + STATE.md **자동 생성** + `## 의사결정 로그`에 해당 note 1행 기재 + state.json 정상 갱신 |
| 도구 | pytest (subprocess, mock 금지) |
| 실행 명령 | `cd opal/tools/state-tool && python3 -m pytest tests/test_state_tool.py -v -k test_s4_state_md_deleted_mark_autopass_autocreates_and_logs` |
| 결과 | **Pass** |
| 상세 | `TestJournalResilience::test_s4_state_md_deleted_mark_autopass_autocreates_and_logs` PASSED — STATE.md 삭제 후 `mark --auto-pass --note`에서 `ok:true` + STATE.md 자동 생성 + `## 의사결정 로그`에 note 1행 기재 + state.json 정상 갱신 확인. |

#### S-5: 저널 쓰기 불가 시 이중 실패 방지 [P0]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2, H-3 |
| 대상 | 저널 쓰기 예외 흡수 + `save_state_json` 순서 (R-2 AC) |
| 계층 | L2 |
| **실행 방식** | **M1** (권한 조작으로 실패 주입) |
| 조건 | STATE.md 권한을 `0444`로 변경 후 `mark --auto-pass --note '권한불가기재'` — `cmd_status`는 `decision`을 세팅하지 않으므로(실측) 로그 유실 검증이 불가능하여 트리거 교체 |
| 기대 결과 | ① `ok:true`·exit 0 — **파이프라인이 멈추지 않는다** ② stdout `journal_warning`에 기재 실패한 decision **원문 포함** — 로그가 조용히 증발하지 않는다 ③ `state.json`은 정상 갱신 |
| 도구 | pytest (`os.chmod`, teardown에서 권한 복구) |
| 실행 명령 | `cd opal/tools/state-tool && python3 -m pytest tests/test_state_tool.py -v -k test_s5_state_md_readonly_fail_open_journal_warning`; 추가 실증: 배포본 `run.sh mark`를 STATE.md `chmod 0444` 상태에서 직접 호출 |
| 결과 | **Pass** (단, §6 보안에 부수 결함 발견 — 아래 상세 참조) |
| 상세 | pytest: `ok:true`·exit 0(파이프라인 비차단), `journal_warning`에 note 원문("권한불가기재") 포함, `state.json` 행 status/owner 정상 갱신 — 3조건 전부 확인. **배포본 직접 실증**(스크래치 태스크, STATE.md `chmod 0444` 후 `mark --auto-pass`)에서도 동일하게 `ok:true` + `journal_warning` 확인했으나, 이 과정에서 **PLAN §5.4 보안 체크리스트 위반을 실측**: `journal_warning.reason` 값이 `"PermissionError: [Errno 13] Permission denied: '/private/tmp/.../s5_sec_task/STATE.md'"` 형태로 **태스크 폴더의 절대 경로를 그대로 노출**한다(`sync_state_md` except 블록의 `f"{type(e).__name__}: {e}"`가 경로 절삭 없이 예외 원문을 그대로 반환 — `state_tool.py:447-450`). PLAN §5.4 "예외 메시지에 경로가 포함되면 파일명만 남기고 절삭"이 구현되지 않았다. 시나리오 본연의 3조건(ok:true/journal_warning 존재/state.json 정상)은 Pass이므로 S-5 자체는 Pass 유지하되, 이 결함은 §6 보안에 FAIL로 별도 기록한다(구현 코드 수정 금지 — 보고만). |

#### S-6: 마커 게이트 소멸 3케이스

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | `marker_missing` 하드 차단 제거 (R-3 AC(a)) |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | STATE.md를 (i) 삭제 (ii) 마커 라인만 제거 (iii) 임의 텍스트로 덮어쓰기 — 3케이스 각각에서 `advance`·`mark` 실행 |
| 기대 결과 | 3케이스 × 2명령 = 6회 호출 전부 `ok:true`, exit 0 |
| 도구 | pytest |
| 실행 명령 | `cd opal/tools/state-tool && python3 -m pytest tests/test_state_tool.py -v -k test_s6_marker_gate_removed_three_corruption_cases` |
| 결과 | **Pass** |
| 상세 | STATE.md (i)삭제 (ii)마커 라인만 제거 (iii)임의 텍스트 덮어쓰기 3케이스 × `advance`/`mark` 2명령 = 6회 호출 전부 `ok:true`, exit 0 확인. |

#### S-9: `--import-existing` 명시적 거부

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | `import_existing_removed` 가드 (R-4 AC) |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | `init <path> --skill opd --mode agentic --import-existing` 실행 + `opal/`·`docs/`·`.opal/` 전역에서 해당 플래그 호출 지시 grep |
| 기대 결과 | ① `{"ok":false,"error":"import_existing_removed",...}` **단일 라인 JSON** + exit 1 (exit 2 argparse 에러 아님) ② 프레임워크 내 호출 지시 **0건** |
| 도구 | pytest + grep |
| 실행 명령 | `cd opal/tools/state-tool && python3 -m pytest tests/test_state_tool.py -v -k "test_s9_import_existing_removed_rejected or test_s9_no_framework_call_sites_reference_import_existing"` |
| 결과 | **Pass** |
| 상세 | ① `init ... --import-existing` → `{"ok":false,"error":"import_existing_removed",...}` 단일 라인 JSON + exit 1(argparse 에러 아님) 확인 ② `opal/`·`docs/`·`.opal/` 전역 grep — 프레임워크 내 `--import-existing` 호출 지시 0건 확인. |

#### S-11: 레거시 동결 표 오반환 차단 [P0]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5, H-4 |
| 대상 | `cmd_show` 렌더 원천 단일화 + 배너 (R-5 AC(b), D-4) |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | `tasks/093-*/` **사본**을 준비하고, STATE.md 표 내용과 `state.json.rows[]`를 **의도적으로 불일치**시킨 뒤 `show --format md` |
| 기대 결과 | ① 반환 표가 **state.json 값**과 일치 (STATE.md 동결 표가 아님) ② 배너 1줄 prepend ③ `marker_present:true` ④ 원본 `tasks/093-*/` 파일 **바이트 무변경** |
| 도구 | pytest (실 파일 사본) |
| 실행 명령 | `cd opal/tools/state-tool && python3 -m pytest tests/test_state_tool.py -v -k test_s11_show_md_returns_state_json_values_not_frozen_table` |
| 결과 | **Pass** |
| 상세 | `TestLegacyCoexistence::test_s11_show_md_returns_state_json_values_not_frozen_table` PASSED — `tasks/093-*` 사본에서 STATE.md 표와 state.json을 의도적으로 불일치시킨 뒤 `show --format md` 호출 시 반환 표가 state.json 값과 일치(동결 표 아님) + 배너 1줄 + `marker_present:true` + 원본 `tasks/093-*` 바이트 무변경(사본 조작이라 원본 불가침) 확인. |

#### S-24: `show --format full` 배너 조건부 부착

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | full 분기 배너 로직 (R-5 AC(b)) |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | 레거시 사본 / 신규 저널 2케이스에서 `show --format full` |
| 기대 결과 | 레거시에는 배너 부착, 신규에는 **미부착**, 두 경우 모두 STATE.md 원문을 손상 없이 반환 |
| 도구 | pytest |
| 실행 명령 | `cd opal/tools/state-tool && python3 -m pytest tests/test_state_tool.py -v -k test_s24_show_full_banner_only_on_legacy` |
| 결과 | **Pass** |
| 상세 | 레거시 사본에는 배너 부착, 신규 저널에는 미부착, 두 경우 모두 STATE.md 원문 손상 없이 반환 확인. |

#### S-18: 5개 서브명령 실동작 실증

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-11 |
| 대상 | 신형 구조 전체 (R-8 AC(a)) |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | S-27(배포 검증) 통과 후, 임시 태스크 폴더에서 `init` → `advance` → `mark` → `block` → `add-row` 순차 실행 |
| 기대 결과 | 5개 명령 전부 `ok:true`, exit 0<br>**[간극 고지]** TASK.md §완료기준은 "신규 태스크 1건 **완주**"를 요구하나 본 시나리오는 5명령 실행이다(R-8 AC(a) 자체는 5명령이므로 요구 커버 위반 아님). 완주 검증은 S-28의 Given(094 자신을 신형으로 이어 완주)이 실질 담당하며, 잔여 간극은 **DONE.md에 명시**한다 (`SCENARIO-GATE-1.md` §2.5 부수 관찰) |
| 도구 | Bash (배포본 `~/.opal/tools/state-tool/run.sh` 직접 호출) |
| 실행 명령 | `run.sh init <scratch>/s18_task --skill opd --mode agentic --rows-from <opd pipeline.json>` → `run.sh advance <path> --task-step task.task_md` → `run.sh mark <path> --task-step task.task_md --done --auto-pass --note '...'` → `run.sh add-row <path> --after-task-step task.task_md --stage TASK --item '...'` → `run.sh block <path> --task-step task.s_1 --reason '...'` (block은 신규 삽입 행 대상으로 마지막에 실행 — stage-transition guard 함정 회피) |
| 결과 | **Pass** |
| 상세 | S-27(배포 검증, diff 0) 통과 확인 후 실행. 5개 명령 전부 `{"ok": true, ...}` + exit 0 확인(각 stdout 개별 캡처). 최종 STATE.md는 `## 의사결정 로그` 2행(auto-pass 기재 + add-row 기재) + `## 블로커: 없음`(block reason은 state.json 행 note에만 기록되고 STATE.md `## 블로커` 자유 기재는 PM 수동 — CONVENTIONS.md §태스크 산출물 구조와 일치, 결함 아님)만 존재 확인. [간극 고지] 완주가 아니라 5명령 실행이므로 TASK.md 요구(완주 검증은 S-28 담당)와 별개 — R-8 AC(a) 자체 충족. |

#### S-20: 실증 태스크 조회 정상 반환

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | `show` 조회 표준 경로 (R-8 AC(c)) |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | S-18 실증 태스크에서 `show --format md` 및 `--format json` |
| 기대 결과 | 두 포맷 모두 현황을 정상 반환 (md는 파생 표, json은 state.json raw) |
| 도구 | Bash |
| 실행 명령 | `run.sh show <scratch>/s18_task --format md` / `run.sh show <scratch>/s18_task --format json` |
| 결과 | **Pass** |
| 상세 | `md` 포맷은 `state.json.rows[]` 파생 표(17행, 블로커 반영된 상태·비고 열 포함) + `- 모드:`/`- 상태:`/`- 다음 액션:` 3줄 정상 반환. `json` 포맷은 `data.rows[]`/`data.current_status`("blocked")/`data.next_action` 등 raw state.json 정상 반환. 두 포맷 모두 현황 정상 반환 확인. |

#### S-29: 레거시 저널 **쓰기** 경로 — 표 바이트 동결 [P0·BLOCKING 해소]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 (핵심), H-1 |
| 대상 | 마커+표+`## 현재 상태` 보유 구형 파일에 신형 `sync_state_md`·`ensure_journal_skeleton`·`append_decision_log` 적용 |
| 계층 | L2 |
| **실행 방식** | **M1** (실 파일 사본 + CLI subprocess) |
| 조건 | `tasks/093-260815-opd-사용자확인행-자동승인-일원화/` **사본**(STATE.md + state.json)에 `advance` → `mark --auto-pass --note '레거시쓰기기재'` → `block` 연속 호출 |
| 기대 결과 | ① 3개 호출 전건 `ok:true`, 무예외 ② `## 의사결정 로그`에 해당 note 1행 정상 추가 ③ 레거시 **마커·파이프라인 표·`## 현재 상태` 블록이 바이트 동결**(호출 전후 해당 구간 diff 0) ④ 마커·표 **중복 삽입 0건** ⑤ 원본 `tasks/093-*` 무변경 |
| 도구 | pytest (실 파일 사본, mock 금지) |
| 실행 명령 | `cd opal/tools/state-tool && python3 -m pytest tests/test_state_tool.py -v -k test_s29_legacy_write_path_freezes_pipeline_table_bytes` |
| 결과 | **Pass** |
| 상세 | `TestLegacyCoexistence::test_s29_legacy_write_path_freezes_pipeline_table_bytes` PASSED — `tasks/093-*` 사본에 `advance`→`mark --auto-pass --note`→`block` 연속 호출 시 ① 3개 호출 전건 `ok:true` 무예외 ② `## 의사결정 로그`에 note 1행 정상 추가 ③ 레거시 마커·표·`## 현재 상태` 블록 바이트 동결(diff 0) ④ 중복 삽입 0건 ⑤ 원본 `tasks/093-*` 무변경(사본 조작) — 전부 확인. |

> **신설 근거**: `SCENARIO-GATE-1.md` §2.1 — PLAN H-4가 지정한 레거시 **쓰기** 시나리오가 iteration 1 전사 과정에서 소실되어, H-4의 계약 위험(예외·중복 삽입·정규식 오매칭)이 어떤 시나리오로도 검증되지 않았다. S-6은 신규 fixture, S-11·S-24는 읽기 전용 `show`다.

#### S-30: 손상 저널 골격 복구 append 분기 + 멱등 [BLOCKING 해소]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 (원인 지점) |
| 대상 | `ensure_journal_skeleton` **세 분기 중 두 번째** — 표 헤더 정규식 미매칭 시 파일 끝 append |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | `## 의사결정 로그` 표 헤더만 제거한 손상 저널(`tmp_task_broken/STATE.md`)에서 `mark --auto-pass --note '손상복구기재'`를 **2회 연속** 실행 |
| 기대 결과 | ① `ok:true` ② 골격이 append로 복구되고 로그 1행 기재 — **`append_decision_log`가 조용히 no-op하지 않음** ③ **기존 본문 무손실**(삭제·치환 0건) ④ 2회차 호출 시 골격 **중복 append 0건**(멱등), 로그는 2행 |
| 도구 | pytest |
| 실행 명령 | `cd opal/tools/state-tool && python3 -m pytest tests/test_state_tool.py -v -k test_s30_broken_journal_skeleton_recovers_and_is_idempotent` |
| 결과 | **Pass** |
| 상세 | `TestJournalResilience::test_s30_broken_journal_skeleton_recovers_and_is_idempotent` PASSED — `## 의사결정 로그` 헤더만 제거한 손상 저널에 `mark --auto-pass --note`를 2회 연속 호출 시 ① `ok:true` ② 골격 append 복구 + 로그 1행 기재(no-op 아님) ③ 기존 본문 무손실 ④ 2회차 호출 시 골격 중복 append 0건(멱등), 로그는 2행 — 전부 확인. |

> **신설 근거**: `SCENARIO-GATE-1.md` §2.2 — §2.1에 선언한 `tmp_task_broken` 자산이 iteration 1에서 어떤 시나리오에도 연결되지 않은 고아였다. S-6 (iii)이 유사하나 `ok:true`만 assert하고 **로그 기재 여부를 보지 않아** H-1의 원인 지점(조용한 no-op)을 비껴간다.

#### S-32: `--note` 표 파괴 입력 방어 [경계 보강]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | `append_decision_log` — 사용자 입력이 의사결정 로그 표 구조를 파괴하는 경로 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | `--note` 값에 마크다운 표 구분자(`|`)와 개행이 포함된 입력으로 `mark --auto-pass` 실행 (예: `'A | B\n두번째줄'`) |
| 기대 결과 | ① `ok:true` ② `## 의사결정 로그` 표 구조가 **파괴되지 않음** — 행 수가 정확히 +1이고 컬럼 수가 유지됨 ③ 입력 원문이 복원 가능한 형태로 보존됨(이스케이프 또는 치환, 무단 절삭 금지) ④ 후속 `mark` 호출이 정상 동작 |
| 도구 | pytest |
| 실행 명령 | `cd opal/tools/state-tool && python3 -m pytest tests/test_state_tool.py -v -k test_s32_note_with_pipe_and_newline_does_not_break_table` |
| 결과 | **Pass** |
| 상세 | `--note`에 `\|`·개행 포함 입력(`'A \| B\n두번째줄'`)으로 `mark --auto-pass` 실행 시 ① `ok:true` ② 표 구조 파괴 없이 행 +1·컬럼 수 유지(`_escape_table_cell` 이스케이프 반영) ③ 입력 원문 복원 가능한 형태로 보존(무단 절삭 없음) ④ 후속 `mark` 정상 동작 — 전부 확인. |

> **신설 근거**: `SCENARIO-GATE-2.md` 신규 지적 #3 — 이번 태스크가 **보존하려는 대상**이 바로 의사결정 로그 표인데, 사용자 입력(`--note`)이 그 표 셀에 직삽되는 경로가 31건 중 어느 시나리오로도 검증되지 않았다. 게이트 PASS 이후 발견된 비차단 항목이나, 보호 대상 자체를 깨뜨리는 경로이므로 반영한다.

#### S-34: semi-agentic opdd 주권 회복 [P0 — 헌법 Core Stance]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-15 |
| 대상 | G-1 `MODE_BOUNDARY_STAGES` 3원소 추가 (R-11 AC(b)) |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | opdd `pipeline.json`으로 `--mode semi-agentic` init 후 **경계 3 stage의 확인 행을 각각 노출시키는 3회 전이**를 시도한다 — ① `advance model.modeling`(직전 확인행 = id 5 `dict.user_confirm`/DICT) ② `advance ddl_migration.ddl_scripts`(직전 = id 8 `model.user_confirm`/MODEL) ③ `advance qa.*`(직전 = id 11 `ddl_migration.user_confirm`/DDL/MIGRATION). **[MUST] 3행을 개별 판정한다** — 단일 호출은 DICT 1행만 노출하므로 `MODE_BOUNDARY_STAGES`에 `"DICT"`만 추가한 **부분 구현이 통과**한다(`SCENARIO-GATE-3.md` ① 하향 주사유) |
| 기대 결과 | **3 stage 각각에 대해** ① 응답의 `auto_approved`가 **비어 있음** ② 해당 확인 행(id 5 / 8 / 11)이 `pending`/`owner=PM`으로 **유지** ③ 진입이 `user_confirmation_required`로 **거부** — 3행 중 하나라도 자동 승인되면 FAIL ④ **통과 경로 검증** — 거부된 뒤 소유자가 `mark <해당 key> --done --owner user`로 승인하면 다음 전이가 `ok:true`로 진행된다(차단만 하고 길이 막히지 않음) ⑤ 대조군 — 경계 밖 stage(opdd id 14 `qa.user_confirm`/QA)는 기존대로 자동 승인되어 **과잉 차단이 아님**을 확인 |
| 도구 | pytest (실 pipeline.json + CLI subprocess) |
| 실행 명령 | `cd opal/tools/state-tool && python3 -m pytest tests/test_state_tool.py -v -k test_semi_agentic_opdd_boundary_three_stages_individually_S34` |
| 결과 | **Pass** |
| 상세 | `TestR11ModeBoundary::test_semi_agentic_opdd_boundary_three_stages_individually_S34` PASSED — DICT/MODEL/DDL·MIGRATION 3 stage 각각 개별 전이 시도 시 ① `auto_approved` 비어있음 ② 해당 확인 행 pending/owner=PM 유지 ③ `user_confirmation_required` 거부 ④ `mark --owner user` 승인 후 통과 경로 정상 진행 ⑤ 대조군(QA 확인 행)은 기존대로 자동 승인 — 전부 확인. `MODE_BOUNDARY_STAGES`에 `"DICT","MODEL","DDL/MIGRATION"` 3원소 추가 반영 확인(`state_tool.py:51-58`). |

#### S-35: opgc CLOSE 폴백 — 데드락 해소 + 무단 통과 차단

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-16 |
| 대상 | G-2 `check_close_gate` 폴백 (R-11 AC(c)) |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | opgc(사용자 확인 행 0개) 태스크에서 앞 6행을 전부 완료한 뒤 `mark close.done_md --done`을 **`--owner user` 유/무 2케이스**로 호출 |
| 기대 결과 | ① `--owner user` **있음** → `ok:true`, `--force` 불요 ② `--owner user` **없음** → `close_gate_violation` 거부 — 폴백이 게이트를 무력화하지 않음 ③ 대조군 — 확인 행이 **있는** 파이프라인(opd)은 기존 `prev_user_row` 검증 경로가 그대로 동작 |
| 도구 | pytest |
| 실행 명령 | `cd opal/tools/state-tool && python3 -m pytest tests/test_state_tool.py -v -k test_opgc_close_fallback_owner_axis_and_opd_control_S35` |
| 결과 | **Pass** |
| 상세 | `TestR11CloseGateFallback::test_opgc_close_fallback_owner_axis_and_opd_control_S35` PASSED — opgc(확인 행 0개) 앞 6행 완료 후 ① `--owner user` 있음 → `ok:true`(force 불요) ② 없음 → `close_gate_violation` 거부 ③ 대조군(opd, 확인 행 존재)은 기존 `prev_user_row` 검증 경로 그대로 동작 — 전부 확인. `check_close_gate`의 `owner` 인자·폴백 로직 반영 확인(`state_tool.py:827-873`). |

#### S-36: agentic 전 구간 `next_action` 헛 확인 소멸

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-17 |
| 대상 | G-3-a `_derive_next_action` (R-11 AC(a)) |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | agentic 모드 opd 태스크를 첫 행부터 마지막 행까지 순회하며 매 전이마다 `show --format json`의 `next_action` 수집 |
| 기대 결과 | ① 전 구간 어느 시점에도 `next_action`에 **"사용자 확인" 문자열 미포함** ② CLOSE 진입 직전은 예외 — 소유자 승인이 실제로 필요한 지점이므로 확인을 가리켜야 함 ③ interactive 모드 대조군에서는 **정상적으로 "사용자 확인"을 가리킴**(과잉 억제 아님) |
| 도구 | pytest |
| 실행 명령 | `cd opal/tools/state-tool && python3 -m pytest tests/test_state_tool.py -v -k test_agentic_next_action_suppresses_hollow_confirmation_S36` |
| 결과 | **Pass** |
| 상세 | `TestR11DerivedSignals::test_agentic_next_action_suppresses_hollow_confirmation_S36` PASSED — agentic opd 16행 전 구간 순회 시 ① `next_action`에 "사용자 확인" 미포함(CLOSE 진입 직전 예외) ② interactive 대조군은 정상적으로 "사용자 확인" 지시 — 전부 확인. `_derive_next_action`이 `can_auto_approve_user_confirmation()` 재사용 반영 확인. |

#### S-37: todo 미러 자동 승인 행 중립 처리

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-17 |
| 대상 | G-3-b `build_todo_mirror` (R-11 AC(d)) |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | agentic 태스크에서 특정 단계의 작업·PM Gate 행을 완료하고 사용자 확인 행만 `pending`으로 남긴 뒤 `todo_mirror` 페이로드 캡처 |
| 기대 결과 | ① 해당 단계 todo가 `completed`로 렌더(자동 승인 예정 행은 `na`와 동일하게 중립) ② semi-agentic 모드 경계 **내부** 단계에서는 중립 처리되지 **않음** — 실제 소유자 승인이 필요하므로 `in_progress` 유지 ③ `state.json` 미접촉(스키마 validate 통과) |
| 도구 | pytest |
| 실행 명령 | `cd opal/tools/state-tool && python3 -m pytest tests/test_state_tool.py -v -k test_todo_mirror_neutralizes_pending_auto_approve_row_S37` |
| 결과 | **Pass** |
| 상세 | `TestR11DerivedSignals::test_todo_mirror_neutralizes_pending_auto_approve_row_S37` PASSED — 작업·PM Gate 완료 + 확인 행만 pending인 단계에서 ① todo가 `completed`로 렌더(중립 처리) ② semi-agentic 경계 내부 단계는 중립 처리 안 됨(`in_progress` 유지) ③ `state.json` 미접촉(schema validate 통과) — 전부 확인. `build_todo_mirror`가 `can_auto_approve_user_confirmation()` 재사용 반영 확인. |

#### S-33: worktree·허브 양쪽 환경 경로 해석 (R-10)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-14 |
| 대상 | `find_project_root()` 재사용 (R-10 AC(a)(b)(d)) |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | ① worktree(sparse checkout, `tasks/` 없음)에서 `TestVerify::test_verify_passes_own_test_scenario_md` 실행 ② 허브(전체 체크아웃)에서 동일 로직 실행 ③ `git diff`로 신규 헬퍼 추가 여부 확인 |
| 기대 결과 | ① worktree **PASS** — `find_project_root`이 허브 루트 반환 ② 허브 **PASS** ③ **신규 경로 해석 헬퍼 0건**(`git rev-parse` 등 신설 없음 — 헌법 §2 중복 구현 금지) |
| 도구 | pytest + Bash(`git diff`) |
| 실행 명령 | 워크트리(`.opal-worktrees/task_094`, sparse checkout·`tasks/` 없음): `cd opal/tools/state-tool && python3 -m pytest tests/test_state_tool.py -v -k test_verify_passes_own_test_scenario_md`. 허브(전체 체크아웃): 동일 명령을 `/Volumes/Data/AiStudio/workspace/opal/opal/tools/state-tool`에서 재실행. `git diff main...HEAD -- opal/tools/state-tool/state_tool.py \| grep -E "def find_project_root\|git rev-parse"` |
| 결과 | **Pass** |
| 상세 | ① 워크트리 실행: `1 passed` — `find_project_root`이 sparse checkout 환경에서도 허브 루트를 정상 반환(`tasks/` 디렉토리 부재에도 PASS). ② 허브 실행: `1 passed`(동일 테스트, 전체 체크아웃 환경). ③ `git diff` 결과 신규 경로 해석 헬퍼(`git rev-parse` 신설·`find_project_root` 변형 등) 0건 — 기존 `find_project_root` 그대로 재사용 확인(헌법 §2 중복 구현 금지 준수). |

#### S-27: 배포본↔소스 동일성 (거짓 통과 차단)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-11 |
| 대상 | install 재배포 (R-8 전제) |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | `bash install-mac.sh` 실행 후 `diff ~/.opal/tools/state-tool/state_tool.py <프로젝트 소스>` |
| 기대 결과 | **차이 0**. 차이가 있으면 S-18·S-20·S-28을 실행하지 않는다 (구버전 실증 = 거짓 통과) |
| 도구 | Bash (`diff`) |
| 실행 명령 | `diff ~/.opal/tools/state-tool/state_tool.py /Volumes/Data/AiStudio/workspace/opal/.opal-worktrees/task_094/opal/tools/state-tool/state_tool.py` |
| 결과 | **Pass** |
| 상세 | `diff` exit code 0 — 차이 0건. install-mac.sh가 태스크 094 코드 소스(worktree)로부터 이미 재배포 완료됨을 확인. S-18/S-20/S-28 실증의 전제 충족(구버전 실증에 의한 거짓 통과 아님). |

---

### L3. 산출물 검사 / 사용자 협업

#### S-12: 구형 서술 잔존 0 (결정론 스윕)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 |
| 대상 | 문서 개정 교체형 AC (a) (R-5 AC(a), R-6·R-7) |
| 계층 | L3 |
| **실행 방식** | **M1** (결정론 grep — 사람 판단 불개입) |
| 조건 | PLAN.md §5.2 스윕 명세의 grep 3종을 개정 완료 후 실행 |
| 기대 결과 | ① 현재시제 본문 금지 패턴 **0건** ② 표 헤더 잔존 0건(`render_pipeline_table` 내부 리터럴 1건만 허용) ③ "STATE.md를 Read하여 재개/파악" 계열 0건 |
| 도구 | Bash (grep) |
| 실행 명령 | PLAN.md §5.2 스윕 3종을 `.opal-worktrees/task_094/opal/`·`.opal-worktrees/task_094/docs/`·허브 `.opal/AGENT.md` 대상으로 실행(워크트리에 `tasks/` 없어 스코프 조정, PM 지시 반영) |
| 결과 | **Pass** (2건 사전 승인된 예외 확인, 위반 아님) |
| 상세 | ① 현재시제 금지 패턴(`pipeline:start`/`marker_missing`/`마크다운 표 직접 편집`/`## 다음 액션`/`import-existing`) grep 결과: README.md 4곳·state_tool.py 6곳 매치되나 전부 **"094부터 이 섹션/코드가 없다/제거되었다"는 과거형 설명**(현재 동작 오서술 아님) 또는 `PIPELINE_MARKER_START/END` 상수(레거시 감지 전용 존치, PLAN.md:481,488 "존치(용도 재정의)" 명시적 승인) 또는 @header 변경이력(changelog 동격) — 실질 위반 0건. ② 표 헤더(`\| # \| 단계 \| 항목 \| 상태 \| 시점 \|`) grep: 1건(`state_tool.py:337`, `render_pipeline_table` 내부 — PLAN.md:1073에서 사전 승인된 유일 허용 리터럴) — 기대치 정확히 일치. ③ "STATE.md를 Read하여 재개/파악" 계열: 0건(1건은 변경이력 행이라 제외). |

#### S-14: 도구 규율 보존 역검증

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10 |
| 대상 | 표준 문구 치환 시 (C) 소실 방지 (R-7 AC(b)) |
| 계층 | L3 |
| **실행 방식** | **M1** (결정론 grep) |
| 조건 | 개정 완료 후 도구 규율 문구 grep |
| 기대 결과 | "`state-tool`로만 수행" 계열 규율 문장이 **8건 이상** 존재 — 0이면 실패 (표 전제 제거하다 규율까지 삭제한 것) |
| 도구 | Bash (grep) |
| 실행 명령 | `grep -rln 'state-tool.*로만 수행' .opal-worktrees/task_094/opal/ .opal-worktrees/task_094/docs/ .opal/AGENT.md \| wc -l` |
| 결과 | **Pass** |
| 상세 | 23건 매치(하네스·에이전트 AGENT.md 7종·SKILL.md 8종·CONVENTIONS.md·backup 사본·`.opal/AGENT.md` 등) — 기대 "8건 이상" 충족. 표 전제 제거가 도구 규율까지 함께 삭제하지 않았음을 확인. |

#### S-13: 세션 복원·검증 루프 정보 이관 확인

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-12 |
| 대상 | 검증 루프 진행률 보관처 + 세션 복원 절차 (R-5 AC(a)) |
| 계층 | L3 |
| **실행 방식** | **M1** (산출물 검사) |
| 조건 | 개정 후 `verification-loop-guide.md`·`harness/state.md` 확인 |
| 기대 결과 | ① 세션 복원이 `state-tool show` 호출로 기술됨 ② 검증 루프 진행률의 새 보관처가 문서에 명시됨 |
| 도구 | Bash (grep) + Read |
| 실행 명령 | `grep -n -A3 "세션 복원" opal/core/references/harness/state.md`; `grep -n "state-tool show\|진행률\|검증 루프" opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` |
| 결과 | **Pass** |
| 상세 | ① `harness/state.md` §세션 복원(:101-121)에 "`show` 호출(기계 상태) → STATE.md Read(서술 맥락 보완)" 2단계 표준 절차 명시 확인 ② `verification-loop-guide.md`(:504-517)에 검증 루프 진행률 새 보관처(`- 진행:`→`show --format json` `data.rows[].note`, `- 상태:`→`data.current_status`, `- 검증:`→STATE.md `## 검증 루프` 자유 기재) 명문화 확인. |

#### S-31: 하네스 3문서 신형 채택 + 템플릿↔코드 drift 대조 [BLOCKING 해소]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 |
| 대상 | **R-6 AC(b) 신형 채택** — 문서 개정의 (b)측. 잔존 0(S-12·S-16) 반대편 |
| 계층 | L3 |
| **실행 방식** | **M1** (결정론 grep + 텍스트 대조) |
| 조건 | 개정 완료 후 하네스 3문서(`opal-harness.md` §3 · `harness/state.md` · `harness/state-template.md`) 확인 + `init` 실산출 STATE.md 골격과 `state-template.md` 템플릿 본문 대조 |
| 기대 결과 | ① 3문서 **각각**에 `## 의사결정 로그`·`## 블로커` 저널 구조가 기술됨 ② `state-tool show` 조회 경로가 **3문서 중 최소 1곳(`harness/state.md` §세션 복원 필수)** 에 명시됨 — R-6 AC 문언은 3문서 전량을 요구하지 않으므로 이 해석을 사전 확정한다 ③ **[대조 단위 확정]** `state-template.md`의 **코드펜스 안 템플릿 블록**과 `init` 실산출 STATE.md를 **섹션 헤딩 시퀀스(`^#{1,2} ` 라인의 순서·집합)** 로만 대조하여 일치 — 파일 전체 대조 금지(파이프라인 행 구성 규칙·산출물 행 규칙은 PLAN:640에 따라 존치되므로 전체 대조 시 거짓 FAIL), 헤딩 시퀀스 대조는 무력한 assert가 아니라 저널 골격의 문서↔코드 drift를 정확히 포착한다 |
| 도구 | Bash (grep) + Python (골격 대조) |
| 실행 명령 | `grep -n "의사결정 로그\|블로커" opal-harness.md harness/state.md harness/state-template.md`; Python 스크립트로 `state-template.md` 코드펜스와 S-18 실증 산출 STATE.md의 `^#{1,2} ` 헤딩 시퀀스 비교 |
| 결과 | **Pass** |
| 상세 | ① 3문서(`opal-harness.md:167,171`, `harness/state.md:13,69`, `harness/state-template.md:24,42,59`) 전부 저널 구조(의사결정 로그·블로커) 기술 확인 ② `state-tool show` 조회 경로가 `harness/state.md` §세션 복원에 명시(R-6 AC 해석 사전 확정과 일치) ③ 헤딩 시퀀스 프로그램 대조 결과: 템플릿 `['# STATE: X', '## 의사결정 로그', '## 블로커']` == 실산출(S-18 태스크) `['# STATE: X', '## 의사결정 로그', '## 블로커']` — **MATCH**(drift 0). |

> **신설 근거**: `SCENARIO-GATE-1.md` §2.3 — R-6 AC는 교체형인데 iteration 1은 (a) 잔존 0만 검증하고 (b) 신형 채택이 누락됐다. 특히 `state-template.md`는 PLAN이 "템플릿 전면 교체"로 지정한 문서이자 신규 STATE.md의 문서상 원형인데 **TEST-SCENARIO 전문에 0회 등장**했다(grep 실측). 문서 템플릿과 코드 산출물(`_build_new_state_md`)의 drift 검증도 이 시나리오가 담당한다.

#### S-38: pilot 산문 모드 분기 (R-11 G-4)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-15 |
| 대상 | pilot 4종 SKILL.md 7건 (R-11 AC(e)) |
| 계층 | L3 |
| **실행 방식** | **M1** (결정론 grep) |
| 조건 | 개정 후 `opal/skills/opal-pilot-{dev,dev-short,dev-wireframe,project}/SKILL.md` grep |
| 기대 결과 | ① **구형 잔존 0** — 모드 무분기 `사용자 확인 (P-5)` 명령형 주석 0건 ② **신형 채택** — 자동 승인 구간에서 "PM은 호출하지 않는다"·도구 처리 명시가 각 지점에 존재 |
| 도구 | Bash (grep) |
| 실행 명령 | `grep -rn '사용자 확인 (P-5)\*\*: 사용자 발화 후 PM이' opal/skills/opal-pilot-{dev,dev-short,dev-wireframe,project}/SKILL.md` (구형 잔존 0건 확인) + `grep -rc '모드에 따라 주체가 다르다' opal/skills/opal-pilot-{dev,dev-short,dev-wireframe,project}/SKILL.md` (신형 채택 지점 수 확인, 합계 7) |
| 결과 | **Pass** |
| 상세 | ① 구형 잔존 grep: 0건(4개 SKILL.md 전부) ② 신형 채택 grep 카운트: dev-short 2 + dev-wireframe 1 + dev 3 + project 1 = **합계 7** — 기대치 정확히 일치. |

#### S-39: 하네스 모드 경계 표 정합 (R-11 G-5)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-16 |
| 대상 | `opal-harness-semi-agentic.md` §3 (R-11 AC(f)) |
| 계층 | L3 |
| **실행 방식** | **M1** |
| 조건 | 개정 후 경계 표를 파싱하여 `MODE_BOUNDARY_STAGES` 상수·각 pilot `pipeline.json`과 대조 |
| 기대 결과 | ① pilot **10종 전부 등재** ② opdd 행 경계가 G-1 상수와 **일치** ③ opgc 행이 G-2 폴백 규약과 **일치** ④ 어느 행도 해당 `pipeline.json`과 모순 없음 |
| 도구 | Bash + Python (표 파싱·대조) |
| 실행 명령 | Python 스크립트 — `opal/core/references/opal-harness-semi-agentic.md` §3 표(10행) 파싱 → `opal/tools/state-tool/state_tool.py`의 `MODE_BOUNDARY_STAGES` 정규식 추출과 대조(DICT/MODEL/DDL·MIGRATION 포함 확인) → pilot 10종 각 `references/pipeline.json`의 `item=="사용자 확인"` 행을 stage별 추출해 opdd(DICT/MODEL/DDL·MIGRATION 경계, QA 비경계)·opgc(확인 행 0개)·oppl(REVIEW D7 게이트) 표기와 대조 |
| 결과 | **Pass** |
| 상세 | ① pilot **10종 전부 등재**(opp/opd/opds/opdw/opwt/oppd/opsdd/opdd/oppl/opgc) ② opdd 경계(DICT·MODEL·DDL/MIGRATION, QA 비경계)가 `MODE_BOUNDARY_STAGES = {TASK,ANALYSIS,PLAN,TEST-SCENARIO,SPEC,REVIEW,DESIGN,WBS,WIREFRAME,DICT,MODEL,DDL/MIGRATION}`와 일치 ③ opgc 폴백(확인 행 0개 → CLOSE 첫 행이 소유자 승인 지점, `--owner user` 필수)이 `check_close_gate:852-867` 구현과 일치 ④ 10개 pilot의 `pipeline.json` 실측 결과(각 pilot의 "사용자 확인"류 행 stage) 어느 것도 표와 모순되지 않음(oppd "Phase1/2 사용자 확정"=PLAN/WBS, oppl "D7 사용자 확정 게이트"=REVIEW 등 표기와 정합). |

#### S-40: R-11 불변 제약 역검증 (신규 상수·스키마·시그니처)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-17 |
| 대상 | R-11 [MUST] 제약 — 신규 상수·분기 금지, 스키마·시그니처 불변 |
| 계층 | L3 |
| **실행 방식** | **M1** |
| 조건 | R-11 적용 전후 `git diff` + 스키마·반환 구조 대조 |
| 기대 결과 | ① **신규 판정 상수·판정 함수 0건** — G-1·G-3이 `can_auto_approve_user_confirmation()`만 재사용(헌법 §2) ② `state.json` `next_action` **필드·스키마 불변** ③ `build_todo_mirror` **시그니처·반환 구조 불변**(키 집합 동일) ④ **R-11 diff가 `ERROR_CODES`를 접촉하지 않음** — `git diff`에 `ERROR_CODES` 항목 추가·삭제 0건(종수 리터럴을 assert하지 않는다. S-7·S-15가 실측 기준으로 종수를 판정하므로 여기서 수치를 중복 고정하면 거짓 FAIL 후 가드가 완화될 위험이 있다 — `SCENARIO-GATE-3.md` 확정 결함) |
| 도구 | Bash (`git diff`) + pytest |
| 실행 명령 | `cd opal/tools/state-tool && python3 -m pytest tests/test_state_tool.py -v -k test_r11_invariants_S40` |
| 결과 | **Pass** |
| 상세 | `TestR11Invariants::test_r11_invariants_S40` PASSED — ① 신규 판정 상수·함수 0건(G-1·G-3 모두 `can_auto_approve_user_confirmation()` 재사용) ② `next_action` 필드·스키마 불변 ③ `build_todo_mirror` 시그니처·반환 구조(키 집합) 불변 ④ R-11 diff가 `ERROR_CODES`를 접촉하지 않음(추가·삭제 0건, `ast.parse`/`literal_eval` 키 집합 비교로 검출력 실증됨 — AGENTIC-LOG #36) — 전부 확인. |

#### S-16: SSOT 서술 통일

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 |
| 대상 | 하네스 SSOT 자기모순 해소 (R-9 AC(b)) |
| 계층 | L3 |
| **실행 방식** | **M1** |
| 조건 | 개정 후 전역 grep |
| 기대 결과 | "STATE.md…유일한 SSOT" 계열 서술 **0건**, `state.json` 단일 SSOT 서술로 통일 |
| 도구 | Bash (grep) |
| 실행 명령 | `grep -rn "STATE\.md.*SSOT\|STATE\.md.*유일한 SSOT" opal/ docs/ .opal/AGENT.md \| grep -v tests/ \| grep -v 변경이력` |
| 결과 | **Pass** |
| 상세 | 매치된 모든 라인이 "SSOT는 `state.json`"으로 정확히 귀속(예: `harness/state.md:69` `[SSOT 불변] state.json(state-tool)이 진행 현황의 유일한 SSOT다`) — "STATE.md…유일한 SSOT" 형태의 자기모순 서술 **0건**. R-9 AC(b) SSOT 통일 확인. |

#### S-17: `marker_missing` 서술 소멸

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 |
| 대상 | 트리거 목록 오류 자동 해소 (R-9 AC(c)) |
| 계층 | L3 |
| **실행 방식** | **M1** |
| 조건 | 개정 후 전역 grep |
| 기대 결과 | 현재시제 본문에서 `marker_missing` 서술 **0건** (changelog 행은 보존) |
| 도구 | Bash (grep) |
| 실행 명령 | `grep -rn "marker_missing" opal/ docs/ .opal/AGENT.md \| grep -v tests/ \| grep -v -E ':\s*\|\s*v[0-9]' \| grep -v 변경이력` |
| 결과 | **Pass** |
| 상세 | 매치 2건 — `state_tool.py:6`(@header 변경이력 동격 서술, "marker_missing/import_failed 삭제 후 import_existing_removed 추가"라는 과거 변경 기록) · `README.md:159`("094: STATE.md 마커 존재 여부 검사는 저널화로 제거되었다 — validate는 더 이상 마커 유무를 판정하지 않는다(marker_missing 소멸)") — 둘 다 **제거를 선언하는 과거형 서술**이며 현재시제 본문에서 `marker_missing`이 여전히 유효한 검사 항목인 것처럼 서술하는 곳은 0건. |

#### S-15: README 종수 == 코드 실측

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 |
| 대상 | 에러 카탈로그 정합 (R-9 AC(a)) |
| 계층 | L3 |
| **실행 방식** | **M1** |
| 조건 | 개정 후 README 헤더 종수와 `len(ERROR_CODES)` 대조 + 하네스 2문서 확인 |
| 기대 결과 | README 종수 == 실측값 **AND** 하네스 2문서에는 **종수 숫자 자체가 부재**(README 포인터만) |
| 도구 | Bash + Python |
| 실행 명령 | `python3 -c "len(ERROR_CODES)"` (실측) + `awk` README 표 행 카운트 + `grep -n "44종\|44개" opal-harness.md harness/state.md` |
| 결과 | **Pass** |
| 상세 | 실측 `len(ERROR_CODES) == 44`, README `## 에러 코드 카탈로그` 헤더 "44종 실측 SSOT" 표기 == 실제 표 행 수(awk 카운트 44) 일치, 하네스 2문서(`opal-harness.md`, `harness/state.md`)에는 종수 리터럴 자체가 부재(README 포인터만 존재) 확인. |

#### S-26: 보존 대상 무변경 (오삭제 방지 역검증)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 |
| 대상 | changelog·brain·레거시 태스크 보존 |
| 계층 | L3 |
| **실행 방식** | **M1** |
| 조건 | 개정 완료 후 `git diff --stat` |
| 기대 결과 | ① 변경이력·changelog **표 행 무변경**(신규 1행 추가는 허용) ② `.opal/brain/pages/**` 무변경 ③ `tasks/093-*` 등 레거시 태스크 폴더 **무변경** |
| 도구 | Bash (`git diff`) |
| 실행 명령 | `git diff main...HEAD --stat` + 변경이력 표 diff 개별 확인(`git diff <파일> \| grep -E "^[-+]\|"`) + `git status --short -- tasks/093-*` + `git diff --stat -- .opal/brain/pages` |
| 결과 | **Pass** |
| 상세 | ① 변경이력(`## 변경이력`) 표는 검사한 모든 문서(CONVENTIONS.md, ARCHITECTURE.md, opal-harness.md, harness/state.md, harness/state-template.md, README.md)에서 **`+` 신규 행 추가만** 존재, 기존 행 삭제·수정 0건(에러 카탈로그처럼 "카탈로그 표"는 재실측으로 내용이 바뀌지만 이는 변경이력 표가 아니라 별개 기능 표) ② `.opal/brain/pages` 관련 변경 0건 ③ `tasks/093-260815-opd-사용자확인행-자동승인-일원화/` `git status`/`git diff` 둘 다 공백(완전 무변경) — 전부 확인. |

#### S-19: 회귀 커버리지 감사

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 |
| 대상 | 테스트 재작성 품질 (R-8 AC(b) — 소유자 판정 2026-08-16 성질 기반) |
| 계층 | L3 (L1 실행 + 감사) |
| **실행 방식** | **M1** |
| 조건 | `pytest tests/ -v` 실행 + 삭제/신규 테스트 대응 감사 |
| 기대 결과 | ① **fail 0** ② 삭제된 테스트가 각각 D-1/D-2/R-3 결정에 **1:1 대응**함이 표로 증명됨 ③ 신규 기능 5종(저널 템플릿·의사결정 로그 무손실·`show` 렌더 단일화·import 거부·에러 카탈로그 정합) 각각에 대응 테스트 존재 ④ **[MUST] padding 테스트 0건** ⑤ **[결정론 대조] `git diff` 기준 삭제된 테스트 함수 총 개수 == Step 3 워커가 제출한 삭제 감사표의 열거 건수** — 초과 삭제 0건을 기계로 확인(자기신고 의존 차단). **[판정 기준 명확화 2026-08-16]** 대조 상대는 **Step 3 산출 감사표(실측 15건)**이며, `PLAN.md` §2.5.3의 `-25건`은 **ANALYSIS 단계 예상 회계**이지 감사표가 아니다 — 예상치와의 차이는 초과 삭제가 아니라 **추정 과대**이므로 FAIL 사유가 아니다 ⑥ 최종 `passed` 수를 **참고값으로 기록**(하한 아님) |
| 도구 | pytest + 수동 감사표 |
| 실행 명령 | `cd opal/tools/state-tool && python3 -m pytest tests/ -v` + `git diff main -- tests/test_state_tool.py`(main 대비 함수명 집합 diff, set 연산) |
| 결과 | **Pass** — ①②③④⑤ 전부 충족(PM 판정 2026-08-16 반영 — 대조 상대는 Step 3 산출 감사표) |
| 상세 | ① **fail 0**: `343 passed, 84 subtests passed` 확인(신규 RED 테스트 1건은 §6 보안 후속 조치로 별도 추가된 것이며 이 실행 시점 기준 스냅샷 — 아래 §6 참조). ② **삭제 테스트의 D-1/D-2/R-3 1:1 대응**: main 대비 함수명 집합 diff(그레프 라인 매칭 + set 연산 이중 검증, 결과 동일)로 삭제 함수 **15개** 확정 — `test_import_failed`·`test_scenario_import_existing_success`·`test_scenario_import_existing_failure`·`test_force_import_preserves_all_keys`·`test_import_with_pipeline_json_restores_keys`·`test_import_no_key_source_keyless_with_warning`·`test_preserved_keys_keep_schema_version_1_1`·`test_duplicate_stage_item_ordered_consumption`(이상 8건 → **D-2** `--import-existing` 제거), `test_mark_derives_next_action_preserves_others`·`test_advance_derives_next_action_preserves_others`·`test_m1_first_line_replaced_subordinate_free_text_preserved`(이상 3건 → **D-1** `## 다음 액션` 제거), `test_marker_missing`·`test_show_md_marker_missing_fallback`·`test_show_full_marker_missing_warning_prepend`·`test_scenario_marker_missing_init_then_remove`(이상 4건 → **R-3** `marker_missing` 제거) — **15건 전부 D-1/D-2/R-3 중 하나에 명확히 대응, 미설명 삭제 0건**(초과/임의 삭제 없음). ③ **신규 기능 5종 커버**: 저널 템플릿(S-1/S-2/S-3/S-21 등), 의사결정 로그 무손실(S-4/S-5/S-30/S-32), show 렌더 단일화(S-10/S-11/S-24/S-25/S-29), import 거부(S-9×2/S-22), 에러 카탈로그 정합(S-7/S-8) 각각 대응 테스트 존재 확인(추가된 26개 신규 함수 전부 `test_s\|test_S` 접두 + 시나리오 번호 태깅). ④ **padding 테스트 0건**: 추가 26개 함수 전원이 특정 시나리오(S-1~S-40) 또는 특정 R-11 항목에 매핑되는 구체적 이름·docstring을 가짐 — 숫자 채우기용 무의미 assert 없음. ⑤ **[결정론 대조 — PM 정정 반영]** `git diff` 실측 삭제 함수 총수 **15개** == **Step 3 워커 제출 삭제 감사표(15건)** — `git diff \| grep -cE "^-    def test_"` 재실행 결과도 **15**로 동일, 완전 일치 확인. 초과 삭제 0건. **[기록 보존 — DONE.md 보고용]** 다만 `PLAN.md` §2.5.3(ANALYSIS 단계 예상 회계)은 `-25건`(-12 D-2/-7 D-1/-6 R-3)을 예상했었고, 이는 Step 3 실제 감사표(15건)와 괴리가 있다 — 원인은 `TestImportPreservesKeys`를 9개로 추정했으나 실측 5개, `TestNextActionAutoDerive` "렌더 검증 5건" 추정도 실측 2건 등 **ANALYSIS/PLAN 단계의 사전 추정이 과대**했기 때문이며, Step 3 실측 감사표(15) 자체와는 정확히 일치하므로 초과 삭제·무단 삭감이 아니다. ⑥ **최종 passed 수(참고값)**: 343 passed(변경 전 기준선 308 대비 +35, 하한 아님, 소유자 판정 2026-08-16 반영). |

#### S-28: 저널 구조 소유자 수용 확인 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-13 |
| 대상 | b안(파일 존치 + 파생 전면 제거) 의사결정의 실사용 타당성 |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업)** — 자동화 불가. 수용성은 결정론 판정 대상이 아님 |
| 조건 | **실제 의사결정 2건 이상·블로커 1건 이상이 기재된 저널** — 본 태스크(094) 자신을 신형 도구로 이어 완주한 저널을 우선 대상으로 하고, 불가 시 등가 조건을 갖춘 저널을 준비한다. **[MUST] S-18의 임시 폴더 산출물(도구 생성 형식 행만 존재)로 대체 금지** — 빈 껍데기를 보고 판정하게 된다 |
| 기대 결과 | 캡틴이 아래 3가지를 확인하고 판정: ① 저널 STATE.md를 열었을 때 진행 현황이 없어도 불편하지 않은가 ② `state-tool show`로 현황 조회가 실용적인가 ③ 의사결정 로그·블로커만 남은 구조가 "이 파일을 왜 남겼는가"에 답하는가<br>**[MUST] 반증 조건 — 아래 중 하나라도 관측되면 FAIL**: (i) 진행 현황을 확인하려 `show`가 아니라 **STATE.md를 먼저 열게 되는 습관이 남는다** (ii) 저널을 열었을 때 얻는 정보가 `state.json`을 직접 읽는 것과 차이가 없다 (iii) 의사결정 로그가 도구 생성 형식 행뿐이라 사람이 읽을 가치가 없다 |
| 실행자 | **[SUPERVISOR] — 캡틴 수동 확인 필요** |
| 결과 | _{캡틴 확인 후 기록}_ |
| 상세 | _{캡틴 확인 후 기록}_ |

#### S-41: agentic 승인 계약 소유자 체감 확인 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-15, H-17 |
| 대상 | R-11 전체 — **두 오류 방향이 실제로 해소되었는가**(주권 상실 ↔ 소유자 피로) |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업)** — 두 오류 방향 모두 소유자 체감 속성이라 기계 신호만으로 판정 불가 |
| 조건 | R-11 적용 후 ① `--agentic` 태스크 1건을 진행하고 ② `//opdd`를 **기본 모드(semi-agentic)**로 DICT 단계까지 진행한다 |
| 기대 결과 | 캡틴이 아래를 판정: ① **피로 방향** — agentic 진행 중 PM이 불필요한 확인을 요청하는 횟수가 체감상 줄었는가(기존 opd 1태스크당 4회) ② **주권 방향** — 기본 모드 opdd에서 표준사전 확정 시 **실제로 승인을 요구받았는가** ③ 승인을 요구받은 지점이 "확인할 가치가 있는 지점"이었는가(과잉 차단으로 느껴지지 않았는가)<br>**[MUST] 반증 조건** — (i) agentic인데 여전히 형식적 확인을 받는다 (ii) 기본 모드 opdd에서 설계가 조용히 확정된다 (iii) 차단이 잦아 `--agentic`을 쓰게 된다 → 하나라도 관측되면 FAIL |
| 실행자 | **[SUPERVISOR] — 캡틴 수동 확인 필요** |
| 결과 | _{캡틴 확인 후 기록}_ |
| 상세 | _{캡틴 확인 후 기록}_ |

> **신설 근거**: `SCENARIO-GATE-3.md` ① 하향 부사유 — 완료기준이 R-11까지 넓어졌는데 목표 시나리오는 저널화 계열 3건뿐이고 R-10·R-11에 [SUPERVISOR] 0건이었다. 평가자가 "S-28 확장보다 R-11 전용 신설"을 권고했다.

**PM 표준 요청 양식** (TEST 단계에서 사용):

```
캡틴, [시나리오 S-28]은 사용자 협업 검증이 필요합니다.
요청 내용: 신형 저널 구조로 생성된 실증 태스크의 STATE.md를 직접 열어보시고,
          `~/.opal/tools/state-tool/run.sh show <실증 태스크 경로>`로 현황을 조회해주세요.
기대 결과: ① 저널에 진행 현황이 없어도 불편하지 않음 ② show 조회가 실용적임
          ③ 의사결정 로그·블로커만 남은 구조가 파일 존치 이유에 답함
확인 후 결과(PASS/FAIL + 상세)를 알려주세요.
```

---

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| R-1 AC(a) 구형 잔존 0 | H-1 | L1 | S-1 | `tests/test_state_tool.py::TestInit` | 교체형 (a) |
| R-1 AC(b) 신형 채택 | H-1 | L1 | S-2, S-21 | `tests/test_state_tool.py::TestInit`, `TestAdvance` | 교체형 (b) |
| R-2 AC 로그 보존 | H-1, H-2, H-3 | L1+L2 | S-3, S-4, S-5, **S-30**, **S-32** | `TestJournalResilience` (신설) | **P0** — S-30 append 분기·멱등, S-32 입력 방어 |
| R-3 AC(a) 마커 차단 소멸 | H-4 | L2 | S-6, S-8, **S-29** | `TestJournalResilience`, `TestLegacyCoexistence`, `TestValidate` | 레거시 쓰기 포함 |
| R-3 AC(b) 카탈로그 정합 | H-9 | L1 | S-7 | `TestErrorCodesCompleteness` | - |
| R-4 AC import 거취 | H-7 | L2 | S-9, S-22 | `TestInit`, grep | - |
| R-5 AC(a) 구형 잔존 0 | H-9, H-12 | L3 | S-12, S-13 | 결정론 grep | 교체형 (a) |
| R-5 AC(b) show 조회 | H-5, H-6 | L1+L2 | S-10, S-11, S-24, S-25 | `TestShowAsQueryStandard` (신설) | **P0** / 교체형 (b) |
| R-6 AC(a) 구형 잔존 0 | H-9 | L3 | S-12, S-16 | 결정론 grep | 교체형 (a) |
| R-6 AC(b) 신형 채택 | H-9 | L3 | **S-31** | grep + 템플릿↔코드 대조 | **교체형 (b)** |
| R-7 AC(a) 표 전제 0 | H-9 | L3 | S-12 | 결정론 grep | 교체형 (a) |
| R-7 AC(b) 규율 보존 | H-10 | L3 | S-14 | 결정론 grep (역검증) | 교체형 (b) |
| R-8 AC(a) 5명령 동작 | H-11 | L2 | S-18, S-27 | Bash 실증 | - |
| R-8 AC(b) 회귀 커버리지 | H-8 | L1+L3 | S-19 | pytest + 감사표 | 소유자 판정 반영 |
| R-8 AC(c) show 반환 | H-5 | L2 | S-20 | Bash 실증 | - |
| R-9 AC(a) 종수 일치 | H-9 | L1+L3 | S-7, S-15 | pytest + grep | - |
| R-9 AC(b) SSOT 통일 | H-9 | L3 | S-16 | 결정론 grep | - |
| R-9 AC(c) 트리거 정합 | H-9 | L3 | S-17 | 결정론 grep | - |
| — 보존 역검증 | H-9 | L3 | S-26 | `git diff --stat` | 오삭제 방지 |
| R-10 AC(a)(b)(d) 양환경·헬퍼0 | H-14 | L2 | S-33 | `TestVerify` + `git diff` | 교체형 (b) |
| R-11 AC(a) 헛 확인 소멸 | H-17 | L2 | S-36 | pytest | 대조군 포함 |
| R-11 AC(b) 주권 회복 | H-15 | L2 | S-34 | pytest | **P0** — 헌법 Core Stance |
| R-11 AC(c) CLOSE 폴백 | H-16 | L2 | S-35 | pytest | 데드락 + 무단통과 양방 |
| R-11 AC(d) todo 중립 | H-17 | L2 | S-37 | pytest | 대조군 포함 |
| R-11 AC(e) 산문 분기 | H-15 | L3 | S-38 | 결정론 grep | 교체형 (a)(b) |
| R-11 AC(f) 경계 표 | H-16 | L3 | S-39 | 표 파싱 대조 | - |
| R-11 [MUST] 불변 제약 | H-17 | L3 | S-40 | `git diff` 역검증 | 오염 방지 |
| — 소유자 수용 | H-13 | L3 | S-28 | [SUPERVISOR] | **목표달성 시나리오** |

> **목표달성 시나리오**(scenario-gate §2 ①축): **S-28**이 태스크 목표("파일은 남기되 파생을 뺀 저널이 실제로 쓸 만한가")를 사용자 계층에서 검증한다. 기계 검증(S-1~S-27)이 전건 통과해도 S-28이 FAIL이면 이번 설계 결정 자체를 재검토한다.

---

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | 해당 없음 | 해당 없음 | 프로젝트에 flake8/ruff/pylint 등 린터 설정 부재(확인: `which ruff flake8 pylint` 전부 not found, `pyproject.toml`/`.flake8`/`.pylintrc` 미존재). 대체 확인: `python3 -m py_compile state_tool.py` 성공 + `ast.parse()` 성공 — 문법 오류 없음. |
| 2 | 타입 체크 | 해당 없음 | 해당 없음 | mypy 등 타입체커 미설정(`which mypy` not found), 타입 힌트 자체도 이 코드베이스 컨벤션에 없음(표준 라이브러리 전용 CLI 스크립트). |
| 3 | 포맷터 | 해당 없음 | 해당 없음 | black 등 포맷터 미설정(`which black` not found). |
| 4 | JSON 스키마 유효성 | `python3 -c "json.load(...)"` | Pass | `state.schema.json`·`pipeline-spec.schema.json`·10종 pilot `pipeline.json` 전부 유효 JSON 파싱 확인. `state.schema.json`의 `git diff`는 `description` 문자열 3곳 변경으로만 국한(구조·타입·required 불변) — PLAN §5.3 체크리스트 충족. jsonschema 라이브러리 미설치로 메타스키마(Draft-07) 검증은 미실시(도구 부재, 정직하게 기록). |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | Pass | `grep -nEi "(api[_-]?key\|secret\|password\|token)\s*=\s*['\"][A-Za-z0-9]{8,}"` 대상 변경 파일(state_tool.py, test_state_tool.py, state.schema.json) 전체 0건. |
| 2 | .gitignore 확인 | Pass | 허브 `.gitignore`에 `.env` 등록 확인(:25). 변경 없음. |
| 3 | 경로 이탈 토큰 가드 회귀 (`_is_safe_artifact_token`) | Pass | 구현(`state_tool.py:881-889`) 확인 — 절대경로·`..` 파트 포함 토큰 거부. 회귀 테스트 `test_s16_path_traversal_tokens_rejected_as_missing`·`test_s17_glob_token_matches_when_file_exists`·`test_s17_glob_token_missing_when_no_file` 3건 격리 재실행 결과 `3 passed`. |
| 4 (부수 발견 → PM 결함 확정 → RED 작성 → **GREEN 재검증 완료**) | `journal_warning` 페이로드 경로 노출 (PLAN.md:1094 §5.4 체크리스트) | **Pass** (수정 완료, 직접 재실증으로 확인) | **이력**: ① 배포본 실증(S-5 상세)에서 최초 발견 — `journal_warning.reason`이 절대경로를 절삭 없이 노출(`sync_state_md` except 블록, 당시 `f"{type(e).__name__}: {e}"`) ② PM이 결함 확정, 본 에이전트가 RED 테스트 신설(`tests/test_state_tool.py::TestJournalResilience::test_journal_warning_reason_redacts_absolute_path_and_home_dir`, red-first.md §2 작성자≠구현자, `state_tool.py` 무변경 상태에서 FAIL 재현 확보) ③ 구현 워커가 `_redact_path_like()` 헬퍼(`state_tool.py:425-441`)를 신설해 `sync_state_md` except 절(`:470`)에 적용, 배포본 재배포까지 완료. **[MUST] 재검증 — 남의 보고를 신뢰하지 않고 직접 재실행함**: 배포본(`~/.opal/tools/state-tool/run.sh`)으로 스크래치 태스크에 `chmod 0444` 후 `mark --auto-pass --note '재검증-경로절삭확인'` 직접 재실행, 실제 stdout에서 5조건 확인 — `"journal_warning": {"reason": "PermissionError: [Errno 13] Permission denied: 'STATE.md'", "decision": "agentic auto-pass at row 1, item=작업", "note": "재검증-경로절삭확인"}`. ① **절대경로 부재**: 확인(스크래치 태스크 절대경로 문자열 전무) ② **홈 경로 부재**: 확인 ③ **`STATE.md` 파일명 유지**: 확인(`'STATE.md'`) ④ **`PermissionError` 타입 유지**: 확인 ⑤ **`decision`/`note` 원문 보존(S-5 계약 회귀 없음)**: 확인 — `decision`="agentic auto-pass at row 1, item=작업"(기존 형식 그대로), `note`="재검증-경로절삭확인"(사용자 입력 원문 그대로, 절삭이 이 필드를 침범하지 않음). **배포본↔소스 diff**: `diff ~/.opal/tools/state-tool/state_tool.py <소스>` exit 0(직접 재확인) — S-27 재충족. **RED→GREEN 전환**: `pytest tests/test_state_tool.py -v -k test_journal_warning_reason_redacts_absolute_path_and_home_dir` → `1 passed`(격리 재실행으로 직접 확인, 타인 보고 아님). **전체 스위트**: `pytest tests/ -q` → `344 passed, 84 subtests passed, 0 failures`(직접 재실행 확인, PM 보고치와 일치). 신규 회귀 0건. |

## 7. 판정

**기계 검증 범위 All Pass / [SUPERVISOR] 2건 미판정(소유자 확인 대기) — All Pass를 단독 선언하지 않음.**

**근거**:
1. **자동 실행 대상 39건(S-28·S-41 제외) 전건 Pass.** S-19는 PM 판정(2026-08-16, 대조 상대를 Step 3 산출 감사표로 명확화)에 따라 Pass로 확정 — `git diff` 실측 삭제 함수 15개 == Step 3 감사표 15건, 완전 일치(초과 삭제 0건). §6 보안에서 실측 발견한 `journal_warning` 경로 노출 결함은 구현 워커가 `_redact_path_like()`로 수정 완료했고, **본 에이전트가 배포본에 직접 재실증**(chmod 0444 + mark --auto-pass, 실제 stdout에서 절대경로·홈경로 부재 + STATE.md/PermissionError 보존 + decision/note 원문 보존 5조건 확인) + **RED 테스트 격리 재실행으로 GREEN 전환 직접 확인**(`test_journal_warning_reason_redacts_absolute_path_and_home_dir` → `1 passed`, 타인 보고 신뢰 아님) + **전체 스위트 직접 재실행**(`344 passed, 84 subtests passed, 0 failures`, PM 보고치와 대조 일치)으로 Pass 전환.
2. **S-28·S-41은 "미판정(소유자 확인 대기)"이다 — Pass로 기록하지 않는다.** 두 시나리오는 `[SUPERVISOR]` 마커에 따라 opal-test-agent가 실행하지 않았고, 실제 저널 구조·agentic 승인 계약에 대한 소유자(캡틴)의 체감 판정이 아직 이루어지지 않았다. 기계 검증이 전부 통과했다고 해서 이 2건을 자동으로 Pass 처리하면 "자동 검증으로 판정할 수 없는 실사용 타당성(H-13)"을 별도 시나리오로 분리한 취지 자체가 무너진다. §3 S-28·S-41 결과 칸은 계속 비워 두었으며, 캡틴 확인 후 별도로 채워져야 한다.
3. 따라서 이번 TEST 단계의 최종 산출 판정은 **"기계 검증 범위 All Pass, 단 [SUPERVISOR] 2건(S-28/S-41)은 소유자 확인 대기로 별도 판정 필요"**이며, 이 2건의 실제 판정(PASS/FAIL) 없이는 태스크 전체를 All Pass로 선언할 수 없다.

### PM Gate 체크 (7대 강제 룰)

- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 (§3.5.2 [MUST] mock 금지 승계)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐 — **iteration 2에서 31건 전량 수록으로 정정**(iteration 1은 18건만 수록된 채 체크되어 사실 불일치였음, `SCENARIO-GATE-1.md` §2.7)
- [x] 가설↔시나리오 매핑(§4) 완전 (미매핑 시나리오 없음)
- [x] L1/L2/L3 계층 명시 (모든 시나리오)
- [x] L3 [SUPERVISOR] 마커 존재 + PM 요청 양식 첨부 (S-28)
- [x] 리스크 가설 표(§1) H-N ID와 시나리오 S-N 1:N 매핑 완전 (H-1~H-13 전건, S-1~S-41) — **iteration 2 후 정정**: §1 시나리오 컬럼이 §3·페이로드의 부분집합(10건 누락·S-5 오등재)이던 것을 페이로드 기준으로 전량 동기화 (`SCENARIO-GATE-2.md` 신규 지적 #1)
- [x] 모든 시나리오에 실행 방식(M1/M2/M3) 명시
- [x] FE 변경 시 M2 시나리오 포함 — **해당 없음** (FE 화면·인증/인가·외부 API 연동 0건, CLI+문서 전용)
- [x] 목표 커버 — TASK.md R-1~R-11 전체가 §4 매핑 표에 커버되고, 목표달성 시나리오(S-28)가 §3에 존재
