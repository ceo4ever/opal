# TEST SCENARIO: 파이프라인 스펙 중복정리 — SKILL.md 감량 + PM Gate SSOT 승격

> 작성일: 2026-08-14 | 상태: 작성 완료
> 작성자: 알투(PM) + 캡틴 페어 | PLAN.md 가설 표 기반
> 트랙: **RED-first** — 변경 영역에 비즈니스 로직(`state_tool.py` 게이트 검증)이 포함되므로 `harness/red-first.md` §1.5 "RED-first 강제"에 해당. RED 테스트 작성은 PLAN Step 7(opal-test-agent, mode: red)이 담당하며 구현 워커(Step 8)와 분리한다.
> 테스트 스택: `test-tool resolve` 결과 BE unit = **pytest**(실측 `pytest 9.1.0` / `Python 3.14.3`). 기존 baseline **284 passed, 22 subtests passed**(2026-08-14 실측).

---

## 1. 리스크 가설 표

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | `cmd_mark` 게이트 가드 삽입 위치 | 검증 실패가 `save_state_json()` 이후면 state.json은 갱신되고 STATE.md는 미갱신 — 부분 상태 변경 | P0 | L1, L2 | S-10, S-11 |
| H-2 | `build_rows_from_pipeline_json()` gate 복사 | `state.schema.json` `additionalProperties:false` 위반 + 기존 태스크 state.json(gate 없음) 하위호환 | P1 | L1, L2 | S-13, S-31 |
| H-3 | `gate` 미보유 행의 mark 경로 | 기존 284 tests 회귀 — 조기 return 없으면 전 파이프라인 mark 영향 | P0 | L1, L2 | S-13, S-30 |
| H-4 | glob 토큰 매칭 | `*` 미포함 토큰 오분류 / 절대경로·`..` 토큰의 태스크 폴더 밖 매칭 | P1 | L1 | S-16, S-17 |
| H-5 | `--force` 게이트 우회 | 우회 시 의사결정 로그 미기재 → 감사 추적 상실 | P2 | L1, L2 | S-15 |
| H-6 | checklist stdout 페이로드 형태 | `todo_mirror_hook._extract_payload`가 `dict`만 통과(`todo_mirror_hook.py:78`) — list면 조용히 무시되어 주입 무발동 | P1 | L1, L2 | S-12, S-18 |
| H-7 | 미러 표 삭제 후 산문 잔존 참조 | 좌표계 소실 — `행 N`·`--row`가 해석 불능 문서로 잔존 | P1 | L1, L3 | S-20, S-22, S-34, **S-35** |
| H-13 | **삭제만 하고 채택 안 함** (게이트 iter1 지적) | 구형(`--row`·`행 N`)을 지우기만 해도 잔존 검증이 통과 — 신형(`--task-step`)이 실제로 들어섰는지는 아무도 안 봄. 070이 실패한 지점 | P0 | L1 | **S-35** |
| H-8 | opwt 동적 행 key 규약 신설 | `KEY_PATTERN` 위반 시 `add-row` 실패 | P1 | L2 | S-23 |
| H-9 | init 명령 중복 제거 | 정본으로 남길 명령이 `--mode` 누락본이면 모드 기본값 오적용 | P1 | L2 | S-26 |
| H-10 | install 재배포 | `install-mac.sh`가 SKILL.md 변경이력을 strip → 소스-배포본 diff 0 불성립 | P2 | L2 | S-32 |
| H-11 | state.json rows[] 신규 필드 → dashboard | `PipelineRow` 명시 생성이라 무영향 예상이나 미검증 시 회귀 사각 | P2 | L2 | S-31 |
| H-12 | opd 게이트가 `test_scenario.scenario_gate` 행에 배치 | 게이트 행이 `*.pm_gate` 네이밍이 아닌 유일 사례 — key 접미로 식별하면 누락 | P2 | L1 | S-5 |

> 가설 13건 → 시나리오 35건 (정량 충족). H-13과 S-35는 목표-커버 게이트 iteration 1의 지적(⑤ 채택/잔존 1/2)을 반영해 추가했다.

---

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터

DB가 없는 도구·문서 태스크이므로 "테이블" 자리에 **검증 대상 자산**을 둔다.

| 테이블(자산) | 식별자 | 상태 | 출처 |
|--------------|--------|------|------|
| baseline 스냅샷 | `$SCRATCH/baseline/{skill}-{mode}.json` × 20 | 편집 전 캡처 완료 | Step 1 생성 (fixture) |
| pipeline.json | `opal/skills/opal-pilot-{10종}/references/pipeline.json` | 편집 전: `pm_gate` 4종 보유·6종 키 부재 | 레포 실파일 |
| pilot SKILL.md | `opal/skills/opal-pilot-{10종}/SKILL.md` | 편집 전: 미러 표 134행·`--row` 45건·산문 `행 N` 36건(비-변경이력) | 레포 실파일 |
| state-tool 테스트 | `opal/tools/state-tool/tests/test_state_tool.py` | 284 passed, 22 subtests (2026-08-14 실측) | 레포 실파일 |
| hook 테스트 | `opal/tools/state-tool/tests/test_todo_mirror_hook.py` | 기존 15건 통과 | 레포 실파일 |
| 게이트 검증용 태스크 폴더(충족) | `$SCRATCH/gate-ok/` — `TASK.md`·`PLAN.md` 실파일 존재 | 산출물 충족 상태 | 테스트 fixture (seed) |
| 게이트 검증용 태스크 폴더(부재) | `$SCRATCH/gate-missing/` — `PLAN.md` 없음 | 산출물 부재 상태 | 테스트 fixture (seed) |
| glob 검증용 폴더 | `$SCRATCH/gate-glob/actions/ACT-1/DONE.md` | 실파일 1건 존재 | 테스트 fixture (seed) |
| 구 state.json | `tasks/090-260813-opds-.../state.json` | `gate` 필드 없음 (하위호환 대조군) | 레포 실파일 (읽기 전용 복사본으로 사용) |
| 배포본 | `~/.opal/skills/opal-pilot-*/references/pipeline.json` | install 재배포 후 | Step 16 산출 |

> `$SCRATCH` = 세션 스크래치패드. 레포를 오염시키지 않는다. 구 state.json은 **복사본**으로만 쓰고 원본을 수정하지 않는다(TASK.md 제약 (d) 소급 변경 금지).

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (실행) | Then (re-read) |
|---------|------------|------------|---------------|
| S-1 | 편집 0건 상태의 pipeline.json 10종 | 10 pilot × 2 mode `init --rows-from` → `rows[]` 추출 저장 | `baseline/` 20 JSON, 각 배열 길이 = 해당 `task_steps` 길이 |
| S-2 | `state-template.md:94`·`qa-standards.md:46` 원문 | Step 2 편집 | 두 파일 `행 예시가 명시` 0건, `references/pipeline.json` ≥1건 |
| S-3 | opdd:241·opsdd:386,399 원문 | Step 12 편집 | 레포 전역 `표를 파싱`·`SSOT 표를 기준` 0건 |
| S-4 | opdd:242 줄번호 인용 | Step 12 편집 | pilot SKILL.md 내 `SKILL.md:[0-9]` 0건 |
| S-5 | pipeline.json 10종 | Step 4~6 gate 이관 | opgc 제외 9종 게이트 행 27건 전부 `gate` 보유, `checklist` 길이 ≥1 |
| S-6 | `pm_gate` 보유 4파일 | Step 4~5 이관 | 10종 최상위 `pm_gate` 키 0건 |
| S-7 | SKILL.md 현행 표(상세본) | Step 4~6 이관 | opd ⑥에 `PM 요청 양식`, opdw에 `참조` 문구, `changed_files`·`GC-CONVENTION-*.md` 원문이 checklist에 보존 |
| S-8 | `baseline/` 20 JSON | F-003 완료 시점 재측정 | 20/20 diff 0 (gate 추가가 rows[] 불변) |
| S-9 | 정상 pipeline.json 10종 + 고의 결손 3종 | `spec-validate` 실행 | 정상 10/10 `ok:true`, 결손 3종이 각 전용 에러코드로 검출 |
| S-10 | `gate-missing/` (PLAN.md 부재) | 게이트 행 `mark --done` | `ok:false`, `gate_artifact_missing`, `missing[]`에 `PLAN.md` |
| S-11 | S-10 직후 state.json·STATE.md | (추가 조작 없음) 파일 재독 | 내용·mtime 무변화 — 부분 상태 변경 없음 |
| S-12 | `gate-ok/` (산출물 충족) | 게이트 행 `mark --done` | `ok:true` + `gate_checklist`가 **dict**로 반환 |
| S-13 | `gate` 미보유 행 | `mark --done` | 응답 키 집합·값이 변경 전과 동일 |
| S-14 | opdw `execute.pm_gate` (artifacts 전치로 `[]`) | 산출물 없이 `mark --done` | `ok:true` — 영구 차단 부재 |
| S-15 | `gate-missing/` | `mark --done --force --note '...'` | `ok:true` + STATE.md 의사결정 로그에 `gate_artifact_force` + missing 목록 |
| S-16 | artifacts 토큰 `/etc/passwd`·`../outside.md` | 게이트 검증 실행 | 태스크 폴더 밖 매칭 0건, missing 처리 |
| S-17 | `gate-glob/actions/ACT-1/DONE.md` 존재 / 부재 폴더 | `actions/ACT-*/DONE.md` 토큰 검증 | 존재 시 통과, 부재 시 missing |
| S-18 | S-12의 stdout JSON | `todo_mirror_hook.py`에 stdin 주입 실행 | `additionalContext`에 checklist 포함 |
| S-19 | 076·088 페이로드 동시 출력 stdout | hook 실행 + 기존 hook 테스트 | 병존 출력, 기존 15건 전건 통과 |
| S-20 | SKILL.md 10종 (`--row` 45건) | Step 10~13 편집 | `## 변경이력` 이전 구간 `--row ` 0건 |
| S-21 | **SKILL.md에서 `--task-step\s+(\S+)` 정규식으로 추출한 key 전량** (워커 제출 목록 금지) | 대표 4종(opdd·opsdd·oppl·**opwt**) `--task-step` 실호출 | 전 key가 `task_steps[].key`에 실재, exit 0 |
| S-35 | pilot별 `--task-step` 현행 건수 (실측 기준선: opdd 0 / opwt 0 / opsdd 0 / oppl 0 / opgc 0 / oppd 1) | Step 10~13 편집 | 6종 전부 `--task-step` ≥1건으로 증가. 0건 잔류 = 삭제만 하고 채택 안 함 |
| S-22 | SKILL.md 10종 (비-변경이력 `행 N` 36건) | Step 10~13 편집 | `## 변경이력` 이전 구간 `행 [0-9]+` 0건, 변경이력 13건 불변 |
| S-23 | opwt 동적 key 제안 6건 | `add-row --key` 실호출 | 전량 exit 0 생성 |
| S-24 | 미러 표 134행 | Step 10~13 삭제 | 10종에서 `\| # \| 단계 \| 항목 \|` 표 0건 |
| S-25 | 도메인 치환값 절 (표/불릿/혼합 3형식) | Step 10~13 정리 | 모드·단계 목록 중복 0건, 잔존은 고유 정보만 |
| S-26 | init 중복 게재 (opgc 3·opwt 3 등) | Step 10~13 정리 | pilot당 완전 명령 최대 1회, 그 1건이 `--mode` 포함, 10종 init exit 0 |
| S-27 | `## PM Gate 점검 목록` 표 | Step 10~13 포인터화 | 게이트 산출물·체크리스트 나열 표 0건, 판정 절차 산문 존치 |
| S-28 | 감량 완료된 pilot 3종 | 게이트 행 mark | pipeline.json 유래 checklist가 stdout 출력 |
| S-29 | `baseline/` 20 JSON | 전 편집 완료 후 재측정 | `diff -r` 출력 없음 (20/20) |
| S-30 | 기존 284 passed | `pytest tests/ -q` | 284 + 신규 전건 passed |
| S-31 | 구 state.json 복사본 + dashboard 어댑터 | `mark`(088 히스토리)·`show --format json` | 히스토리 연결·todo_mirror 불변, 어댑터 파싱 정상 |
| S-32 | 소스 pipeline.json 10건 | install 재배포 후 배포본 대조 + 배포 경로 실행 | `diff` 0, 배포 경로 init + 게이트 차단 재현 |
| S-33 | 배포 완료 상태 | 캡틴이 새 세션에서 실제 pilot 호출 | 게이트 mark 시 checklist 세션 노출, 산출물 부재 시 차단 체감 |
| S-34 | 감량된 SKILL.md | 캡틴이 미러 표 없이 통독 | 파이프라인 구조·게이트 기준을 문서만으로 파악 가능 |

---

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 실 데이터 입력)

#### S-1: 전후 동등 baseline 캡처

| 항목 | 내용 |
|------|------|
| 가설 매핑 | (전제 — S-8·S-29의 기준선) |
| 대상 | 10 pilot × 2 mode `init --rows-from` 결과 `rows[]` |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구 — bash + jq/python)** |
| 조건 | 레포에 편집 0건인 시점. 캡처는 **최초 1회만 유효**하며 편집 후 재현 불가 |
| 기대 결과 | `baseline/` 아래 JSON 20개 생성, 각 배열 길이가 해당 pipeline.json `task_steps` 길이와 동일 |
| 도구 | bash + python3 |
| 실행 명령 | PLAN §3.1.2 절차 재확인: `baseline/` 20개 파일 존재 확인 + `python3` 스크립트로 각 파일 배열 길이 vs 현재 `pipeline.json task_steps` 길이 비교(10 pilot × 2 mode) |
| 결과 | Pass |
| 상세 | `tasks/091.../baseline/` 20개 파일 실재 확인(ls). 전량 길이 일치: opd16·opds11·opdw9·opp9·opwt10·opgc7·oppd13·opsdd25·oppl19·opdd15(interactive·agentic 공통) — PLAN §3 Step1 완료 기준과 정확히 일치. EXECUTE Step1이 편집 0건 시점(레포 git 변경 0)에 캡처했음을 AGENTIC-LOG #19로 교차 확인. |

#### S-2: 하네스 상위 규칙 2건 정정

| 항목 | 내용 |
|------|------|
| 가설 매핑 | (R-2 AC) |
| 대상 | `harness/state-template.md:94`, `harness/qa-standards.md:46` |
| 계층 | L1 |
| **실행 방식** | **M1 (grep 산출물 검사)** |
| 조건 | Step 2 편집 완료 |
| 기대 결과 | 두 파일에서 `행 예시가 명시` 0건이고, 각각 `references/pipeline.json` 문자열 ≥1건 |
| 도구 | grep |
| 실행 명령 | `grep -n "행 예시가 명시" opal/core/references/harness/state-template.md opal/core/references/harness/qa-standards.md`; `grep -c "references/pipeline.json" <동일 2파일>` |
| 결과 | Pass |
| 상세 | "행 예시가 명시" grep 0건(exit 1, 무출력). "references/pipeline.json" 각 파일 2건씩 확인(≥1 충족). |

#### S-3: 자기모순 문장 제거 (레포 전역)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | (R-1 AC) |
| 대상 | `opdd/SKILL.md:241`, `opsdd/SKILL.md:386`·`:399` + 레포 전역 |
| 계층 | L1 |
| **실행 방식** | **M1 (grep 산출물 검사)** |
| 조건 | Step 12 편집 완료 |
| 기대 결과 | 레포 전역 `표를 파싱`·`SSOT 표를 기준` grep 0건. 각 지점이 `references/pipeline.json`을 원천으로 서술 |
| 도구 | grep |
| 실행 명령 | `grep -rn "표를 파싱\|SSOT 표를 기준" --include="*.md" .` (레포 전역) + `grep -n "아래 표를 파싱\|위 SSOT 표를 기준으로" opal/skills/opal-pilot-data-design/SKILL.md opal/skills/opal-pilot-sdd/SKILL.md` (실 정정 대상 개별 확인) |
| 결과 | Pass (단서 있음 — 상세 참조) |
| 상세 | R-1 AC의 실제 정정 대상 문구("아래 표를 파싱"/"위 SSOT 표를 기준으로", opdd:241·opsdd:386/399)는 두 파일에서 grep 0건으로 완전 제거 확인. "레포 전역" 리터럴 검색은 12건 매치되나 전건이 무관: (a) `state-tool/README.md:58` — `--import-existing`(기존 STATE.md 마크다운 표 파싱) 기능 설명, 이번 수정 대상과 무관한 기존 정상 문장 (b) `opal-pilot-sdd/SKILL.md:512` — 변경이력 행(불변 대상, 이번 태스크가 신규 추가한 이력 서술 안에 있는 인용문) (c) `tasks/090.../`, `tasks/backup/070.../`, `.opal/brain/...`, 본 태스크 `PLAN.md`/`TASK.md`/`ANALYSIS.md` 등 — 과거 기록·계획 문서로 라이브 지시문이 아님. 실질 검증 대상(2 파일 3 지점) 기준으로는 Pass. |

#### S-4: 줄번호 인용 오류 제거

| 항목 | 내용 |
|------|------|
| 가설 매핑 | (R-3 AC) |
| 대상 | `opdd/SKILL.md:242`의 `opal-pilot-dev/SKILL.md:266-289` |
| 계층 | L1 |
| **실행 방식** | **M1 (grep 산출물 검사)** |
| 조건 | Step 12 편집 완료 |
| 기대 결과 | pilot SKILL.md 내 타 SKILL.md 줄번호 인용(`SKILL\.md:[0-9]`) 0건, 또는 잔존분이 실제 줄 범위와 일치 |
| 도구 | grep |
| 실행 명령 | `grep -rn "SKILL\.md:[0-9]" opal/skills/opal-pilot-*/SKILL.md` |
| 결과 | Pass |
| 상세 | 0건(exit 1, 무출력). opdd:242의 `opal-pilot-dev/SKILL.md:266-289` 줄번호 인용이 완전 삭제됨(교체 아닌 삭제 — PLAN 설계 결정과 일치). |

#### S-5: 게이트 정의 이관 완전성 (H-12 포함)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-12 |
| 대상 | pipeline.json 9종(opgc 제외) `task_steps[].gate` |
| 계층 | L1 |
| **실행 방식** | **M1 (python3 JSON 파싱)** |
| 조건 | Step 4~6 완료 |
| 기대 결과 | 게이트 행 27건 전부 `gate` 보유, `gate.checklist` 길이 ≥1. **게이트 식별이 key 접미(`*.pm_gate`)가 아니라 `row.get("gate")` 유무로 이뤄져 opd `test_scenario.scenario_gate`가 누락되지 않음** |
| 도구 | python3 |
| 실행 명령 | python3로 9종(opgc 제외) `pipeline.json` 로드 → `"gate" in ts` 필터(키 접미가 아닌 필드 존재로 식별) → 행 수·`gate.checklist` 길이 집계 |
| 결과 | Pass |
| 상세 | gate 보유 행 합계 27건 정확 일치(opd4+opds2+opdw2+opp2+opwt2+oppd3+opsdd5+oppl3+opdd4=27), 전건 `checklist` 길이≥1(위반 0). H-12 엣지케이스 확인 — opd `test_scenario.scenario_gate`(`.pm_gate` 접미 아님)도 `gate` 필드 존재로 정확히 검출됨(checklist 길이 7, artifacts=["TEST-SCENARIO.md"]). opgc는 gate 행 0건으로 제외 대상 정합 확인. |

#### S-6: 최상위 `pm_gate` 잔존 0 (구형 잔존 검증)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | (R-9 AC(b) — 교체형 목표 잔존 기준) |
| 대상 | pipeline.json 10종 |
| 계층 | L1 |
| **실행 방식** | **M1 (python3 JSON 파싱)** |
| 조건 | Step 4~5 완료 |
| 기대 결과 | 10종 최상위 `pm_gate` 키 0건 (실제 제거 대상 4파일: opd·opds·opdw·opp) |
| 도구 | python3 |
| 실행 명령 | python3로 10개 `pipeline.json` 로드 후 `"pm_gate" in spec`(최상위) 확인 |
| 결과 | Pass |
| 상세 | 10/10 전부 `False`(최상위 `pm_gate` 키 없음). |

#### S-7: 이관 시 정보 손실 0

| 항목 | 내용 |
|------|------|
| 가설 매핑 | (R-9 AC(c)) |
| 대상 | opd `TEST-SCENARIO` ⑥항, opdw 2행, 전치된 비-경로 토큰 |
| 계층 | L1 |
| **실행 방식** | **M1 (python3 JSON 파싱)** |
| 조건 | Step 4~6 완료 |
| 기대 결과 | opd ⑥에 `PM 요청 양식` 존재, opdw에 `op-dev-qa` 참조 문구 존재, `changed_files`·`GC-CONVENTION-*.md` 원문이 checklist에 전치 보존 |
| 도구 | python3 |
| 실행 명령 | python3로 opd/opdw `pipeline.json` 문자열 검색("PM 요청 양식"/"op-dev-qa") + 10개 `pipeline.json` 전체에서 "changed_files"·"GC-CONVENTION" 문자열 존재 파일 목록화 |
| 결과 | Pass |
| 상세 | opd에 "PM 요청 양식" True, opdw에 "op-dev-qa" True. "changed_files"는 opdw 1개 파일에서 확인. "GC-CONVENTION"은 opds·opdw·opd·opgc·opp 5개 파일에서 확인 — 정보 손실 0. |

#### S-9: `spec-validate` gate 검증

| 항목 | 내용 |
|------|------|
| 가설 매핑 | (R-10 AC) |
| 대상 | `validate_pipeline_spec()` |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest + CLI 실호출)** |
| 조건 | Step 8 구현 완료. 고의 결손 스펙 3종 준비(키 누락 / 타입 오류 / `checklist:[]`) |
| 기대 결과 | 정상 10/10 `ok:true`·violations 0. 결손 3종이 각각 `spec_gate_missing_field`·`spec_gate_field_type_invalid`·`spec_gate_checklist_empty`로 검출 |
| 도구 | pytest |
| 실행 명령 | (1) `for f in opal/skills/opal-pilot-*/references/pipeline.json; do bash opal/tools/state-tool/run.sh spec-validate "$f"; done` (2) 스크래치 fixture 3종(gate.artifacts 삭제/gate.artifacts 타입오류/gate.checklist:[]) 생성 후 동일 명령 실행. 겸하여 `pytest tests/test_state_tool.py -k test_gate` 관련 5건도 실행 |
| 결과 | Pass |
| 상세 | 정상 10/10 전부 `{"ok": true, "violations": [], "violations_count": 0}`. 결손 fixture: gate.artifacts 키 삭제 → `spec_gate_missing_field`("gate missing field: artifacts"), gate.artifacts="NOT_A_LIST" → `spec_gate_field_type_invalid`, gate.checklist=[] → `spec_gate_checklist_empty`. 3종 전용 에러코드 정확 매치(exit 1 각각). |

#### S-10: 산출물 부재 시 게이트 차단

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | `cmd_mark` 게이트 가드 |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | `gate-missing/` — `PLAN.md` 부재 상태의 태스크 폴더 |
| 기대 결과 | `ok:false`, `error`(code) `gate_artifact_missing`, `missing[]`에 `PLAN.md` 포함 |
| 도구 | pytest |
| 실행 명령 | `cd opal/tools/state-tool && python3 -m pytest tests/test_state_tool.py -k TestTaskStepGate -v` (`test_s10_missing_artifact_blocks_mark`) + 배포경로 실측(S-32에서 opd analysis.pm_gate로 별도 재현) |
| 결과 | Pass |
| 상세 | `test_s10_missing_artifact_blocks_mark` PASSED — opd `plan.pm_gate`(artifacts=TASK.md,PLAN.md) 미충족 시 `ok:false`+`error:gate_artifact_missing`+`missing`에 둘 다 포함 확인(mock 없음, 실 tempdir·실 pipeline.json fixture). S-32 배포경로 실측에서도 동형 응답(`{"ok": false, "error": "gate_artifact_missing", "missing": ["ANALYSIS.md"]}`) 재현. |

#### S-12: checklist dict 페이로드 반환

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | `cmd_mark` ok() stdout |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | `gate-ok/` — artifacts 충족 상태 |
| 기대 결과 | `ok:true` + `gate_checklist` 필드가 **dict**로 직렬화 (list면 `_extract_payload`가 조용히 무시 — `todo_mirror_hook.py:78`) |
| 도구 | pytest |
| 실행 명령 | `pytest tests/test_state_tool.py -k TestTaskStepGate` (`test_s12_gate_checklist_dict_payload_on_pass`) + S-28/S-32 실 CLI 재확인 |
| 결과 | Pass |
| 상세 | `test_s12_gate_checklist_dict_payload_on_pass` PASSED. 실 CLI 교차확인(S-28): `mark plan.pm_gate --done` stdout에 `"gate_checklist": {"key":"plan.pm_gate", ..., "checklist":[...]}` — `type()`이 dict(JSON object)이며 list가 아님을 실측 확인. |

#### S-13: `gate` 미보유 행 무영향 (회귀)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2, H-3 |
| 대상 | `gate` 없는 행의 mark 경로 |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | `gate` 필드가 없는 행 + 기존 태스크 state.json 복사본 |
| 기대 결과 | mark 응답의 키 집합·값이 변경 전과 동일. 구 state.json(gate 없음)도 정상 통과 |
| 도구 | pytest |
| 실행 명령 | `pytest tests/test_state_tool.py -k TestTaskStepGate` (`test_s13_new_style_row_without_gate_response_unaffected`, `test_s13_legacy_keyless_state_json_mark_still_passes`) + S-31 구 090 state.json 복사본 실측 |
| 결과 | Pass |
| 상세 | 2건 PASSED. 신형(gate 없는 행)·구형(schema_version 1.0, key 없음) 양쪽 모두 mark 응답 불변. S-31에서 구 090 state.json 복사본(gate 필드 전무) `mark close.done_md`도 `gate_checklist` 키가 응답에 부재함을 실측 확인(H-3 회귀 없음). |

#### S-14: 빈 artifacts는 차단하지 않음 (영구 차단 부재)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | (캡틴 확정 실패 모드 배제) |
| 대상 | opdw `execute.pm_gate` — 전치 후 `artifacts: []` |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | 산출물이 하나도 없는 상태 |
| 기대 결과 | `ok:true` — 빈 배열에서 검증 함수가 즉시 return하여 **차단 자체가 발생하지 않음** |
| 도구 | pytest |
| 실행 명령 | `pytest tests/test_state_tool.py -k TestTaskStepGate` (`test_s14_empty_artifacts_never_blocks`) |
| 결과 | Pass |
| 상세 | PASSED. opdw `execute.pm_gate`(artifacts:[]) — 산출물 무관 `ok:true`, `check_gate_artifacts()`가 `tokens`가 빈 배열이면 즉시 `None` 반환(소스 `state_tool.py:744-746` 확인)하여 영구 차단 부재 성립. |

#### S-15: `--force` 우회 시 의사결정 로그 강제

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | `--force --note` 경로 |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | `gate-missing/` + `--force --note '<사유>'` |
| 기대 결과 | `ok:true`로 통과하되 STATE.md 의사결정 로그에 `gate_artifact_force`와 missing 목록이 기재됨. `--note` 미제공 시 `note_required_for_force` 거부 |
| 도구 | pytest |
| 실행 명령 | `pytest tests/test_state_tool.py -k TestTaskStepGate` (`test_s15_force_note_bypass_records_decision_log`, `test_s15_force_without_note_rejected`) + S-32 배포경로 실측 |
| 결과 | Pass |
| 상세 | 2건 PASSED. `--force --note '<사유>'` → `ok:true`+STATE.md 의사결정 로그에 `gate_artifact_force`+missing 목록 기재. `--force`만(note 없음) → `note_required_for_force` 거부. |

#### S-16: 경로 이탈 토큰 거부 (보안·경계)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | artifacts 토큰 경로 해석 |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | artifacts에 `/etc/passwd`·`../outside.md` 주입 |
| 기대 결과 | 태스크 폴더 밖 매칭 0건. 절대경로·상위 경로 토큰은 missing 처리되며 예외로 크래시하지 않음 |
| 도구 | pytest |
| 실행 명령 | `pytest tests/test_state_tool.py -k TestTaskStepGate` (`test_s16_path_traversal_tokens_rejected_as_missing`) + 소스 `_is_safe_artifact_token()`(`state_tool.py:728-736`) 직접 확인 |
| 결과 | Pass |
| 상세 | PASSED. `/etc/passwd`·`../outside.md` 토큰이 missing 처리, 크래시 없음. 소스 확인: `pathlib.PurePosixPath(t).is_absolute()` 또는 `".." in pp.parts`이면 `False`(불안전) 반환 — 절대경로·상위경로 이탈 방어 로직 실재. §6-3 보안 항목과 동일 근거. |

#### S-17: glob 토큰 매칭

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | `actions/ACT-*/DONE.md` (opsdd 실사용처) |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | `gate-glob/actions/ACT-1/DONE.md` 존재 폴더 / 동일 구조 부재 폴더 |
| 기대 결과 | 존재 시 통과, 부재 시 missing. `*` 미포함 토큰은 glob로 오분류되지 않음 |
| 도구 | pytest |
| 실행 명령 | `pytest tests/test_state_tool.py -k TestTaskStepGate` (`test_s17_glob_token_matches_when_file_exists`, `test_s17_glob_token_missing_when_no_file`, `test_s17_non_glob_token_not_misclassified_as_glob`) |
| 결과 | Pass |
| 상세 | 3건 PASSED. `actions/ACT-*/DONE.md`(opsdd 실사용처) 글롭 — 파일 존재 시 통과, 부재 시 missing. `*` 미포함 정적 경로 토큰은 glob 경로로 오분류되지 않음. |

#### S-20: `--row` 잔존 0 (구형 잔존 검증)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | pilot SKILL.md 10종 |
| 계층 | L1 |
| **실행 방식** | **M1 (grep 산출물 검사)** |
| 조건 | Step 10~13 완료. 기준선 45건(비-변경이력) |
| 기대 결과 | `## 변경이력` 헤딩 **이전** 구간의 `--row ` 출현 0건. 변경이력 구간 1건은 **불변** |
| 도구 | grep + awk |
| 실행 명령 | `awk '/^## 변경이력/{exit} {print}' <SKILL.md> \| grep -oE -- "--row " \| wc -l` (10 pilot 개별) + 변경이력 구간 동일 카운트, `git show HEAD:<file>` 대비 원본 대조 |
| 결과 | Pass |
| 상세 | **occurrence 단위**(라인 아닌 매치 수) 카운트로 재확인 — 10/10 pilot 변경이력 이전 구간 `--row ` 0건. 변경이력 구간: 원본(HEAD, 이번 태스크 착수 전) 1건(opsdd v3.6.0, "070 pipeline.json 전환은 범위 밖")이 git diff에 전혀 나타나지 않아 완전 불변 확인. 이번 태스크가 추가한 신규 변경이력 6건(opdd/opwt/opsdd/oppl/oppd/opgc — 전환내용을 서술하는 신규 행, "`--row N`(14건)→`--task-step <key>`" 등)에 `--row` 텍스트가 포함되어 전체 카운트는 7이 되나, 이는 **CONVENTIONS.md 변경이력 작성 의무에 따른 신규 행 추가**이지 잔존 실행-예시가 아니므로 위반 아님. |

#### S-22: 산문 `행 N` 잔존 0

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | pilot SKILL.md 10종 |
| 계층 | L1 |
| **실행 방식** | **M1 (grep 산출물 검사)** |
| 조건 | Step 10~13 완료. 기준선 **비-변경이력 36건** |
| 기대 결과 | `## 변경이력` 헤딩 **이전** 구간의 `행 [0-9]+` 출현 0건. 변경이력 구간 13건은 손대지 않음 |
| 도구 | grep + awk |
| 실행 명령 | `awk '/^## 변경이력/{exit} {print}' <SKILL.md> \| grep -oE "행 [0-9]+" \| wc -l` (10 pilot 개별, occurrence 단위) + `git show HEAD:<file>`로 원본 13건 대조 |
| 결과 | Pass |
| 상세 | **주의(자체 발견 후 정정)**: 최초 `grep -c`(라인 카운트)로는 opds=6·opp=4 등으로 나와 PLAN.md 기준선(opds9·opp8 등, 합 36)과 불일치했으나, 원인은 일부 줄에 `행 N`이 4회까지 중복 출현(예: 구 opds:275줄)하는 데 있었다. `grep -oE | wc -l`(occurrence 단위)로 재측정하여 10/10 pilot 변경이력 이전 구간 0건 확인, PLAN 기준선과 정합. 변경이력 구간: 원본(HEAD) occurrence 합계 13건 — 현재도 정확히 13건 그대로(각 pilot별 원본↔현재 동수 확인, 수정 없음) + 이번 태스크 신규 이력 1건(opwt v4.9, "산문 `행 1` 1건을") = 14건. 신규 1건은 전환 서술이라 위반 아님. |

#### S-35: 신형 주소 채택 전후 델타 (삭제-만-함 검출)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-13, H-7 |
| 대상 | `--row` 보유 6 pilot의 `--task-step` 출현 건수 |
| 계층 | L1 |
| **실행 방식** | **M1 (grep 전후 대조)** |
| 조건 | Step 10~13 완료. **기준선 실측 확정**(2026-08-14, 변경이력 제외): opdd 0 / opwt 0 / opsdd 0 / oppl 0 / opgc 0 / oppd 1 |
| 기대 결과 | **① 존재 조건**: 6종 전부 `--task-step` ≥1건으로 증가(0건 잔류 = FAIL). **② 수량 대응 조건**: pilot별 `--task-step` 증가분이 해당 pilot의 `--row` 감소분과 **일치**한다(opdd +14 / opwt +11 / opsdd +9 / oppd +5 / oppl +4 / opgc +2, 합계 **+45**). 명령 예시를 삭제하기로 한 지점이 있으면 그 건수를 실행 명령에 사유와 함께 명시하고 차감한다. 참고 대조군: 070 전환 완료 4종은 현재 opd 12 / opds 10 / opdw 9 / opp 8건 |
| 도구 | grep + awk |
| 실행 명령 | `awk '/^## 변경이력/{exit}{print}' <SKILL.md> \| grep -oE -- '--task-step[[:space:]]+[^ )\`]+' \| wc -l` (6 pilot, 현재/원본(`git show HEAD:`) 각각) + 매치 라인 목록(`grep -noE`)으로 개별 항목 분류 |
| 결과 | Pass |
| 상세 | **원본(HEAD) 기준선 실측**: opdd·opwt·opsdd·oppl·opgc `--task-step`=0, oppd=1(사전 존재, `close.done_md`) — dispatch가 제시한 기준선과 정확히 일치. **현재(raw occurrence) 총계**: opdd15·opwt12·opsdd10·oppl5·opgc2·oppd7. 이는 기대치(14/11/9/4/2/+5=6)보다 각 pilot당 최대 1건씩 많아 raw 합계 50 ≠ 45. 매치 라인을 전수 검사한 결과, opdd·opwt·opsdd·oppl·oppd 5개 파일에 **동일 문구의 "게이트 정의 SSOT" 안내 산문**(`> **게이트 정의 SSOT**: ... \`state-tool mark --task-step <게이트 key>\` 호출 시 ...`, placeholder `<게이트 key>` 사용) 1건씩이 F-003/R-9(c)·R-12(a) 작업(S-7·S-27 대상)으로 별도 추가되어 있음 — 이는 `--row`→`--task-step` 치환(R-4/H-13/S-35 대상)이 **아니며** SKILL.md 자체 변경이력에도 별도 항목("PM Gate 절차 블록쿼트에 게이트 정의 SSOT 포인터 1줄 추가")으로 구분 기재되어 있다. oppd는 추가로 사전 존재 `close.done_md` 1건(HEAD에도 있던 것)이 섞여 있음. 이 두 종류(SSOT 안내 산문 5건 + oppd 사전존재 1건)를 근거를 밝혀 차감하면: opdd15-1=14, opwt12-1=11, opsdd10-1=9, oppl5-1=4, opgc2-0=2, oppd7-1(포인터)-1(사전존재)=5 → **합계 14+11+9+4+2+5=45**, `--row` 감소분(각 14/11/9/4/2/5, 원본 HEAD 실측과 일치)과 **정확히 1:1 일치**. ① 존재조건(6종 전부≥1) ② 수량대응조건(합 45) 모두 충족. |

> **이 시나리오가 있는 이유**: S-20(`--row` 0건)은 명령 예시를 **통째로 삭제해도 통과**한다. 070이 정확히 이 구멍으로 "목표 미검증 완료"를 냈다(→ `scenario-gate.md` §1). 잔존 검증과 채택 검증을 분리해 짝을 맞춘다.
> **② 수량 대응 조건을 둔 이유**(게이트 iter2 G-4): 존재 조건(≥1건)만으로는 "opdd에서 14건을 지우고 1건만 넣는" 통과가 가능하다. 45건 전량이 신형으로 **치환**됐음을 수량으로 앵커한다.

#### S-24: 미러 표 삭제

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | pilot SKILL.md 10종, 134행 |
| 계층 | L1 |
| **실행 방식** | **M1 (grep 산출물 검사)** |
| 조건 | Step 10~13 완료 |
| 기대 결과 | 10종에서 `\| # \| 단계 \| 항목 \|` 형식 표 0건, 원천 포인터 1줄로 교체됨 |
| 도구 | grep |
| 실행 명령 | `grep -rn '\| # \| 단계 \| 항목 \|' opal/skills/opal-pilot-*/SKILL.md` |
| 결과 | Pass |
| 상세 | 0건(exit 1, 무출력) — 10종 전부 미러 표 삭제 확인. |

#### S-25: 도메인 치환값 중복 제거

| 항목 | 내용 |
|------|------|
| 가설 매핑 | (R-7 AC) |
| 대상 | `## STATE.md 도메인 치환값` 절 (표/불릿/혼합 3형식) |
| 계층 | L1 |
| **실행 방식** | **M1 (grep 산출물 검사)** |
| 조건 | Step 10~13 완료 |
| 기대 결과 | 10종에서 모드·단계 목록 중복 기재 0건. 잔존 항목은 pipeline.json에 없는 고유 정보(산출물 목록 등)만 포함 |
| 도구 | grep |
| 실행 명령 | `grep -n "도메인 치환값" opal/skills/opal-pilot-*/SKILL.md` (섹션 존재 파일 식별) + `awk '/^## STATE.md 도메인 치환값/{f=1;next}/^## /{f=0}f' <file> \| grep -nE '\{모드\}\|\{단계 목록\}\|필드.*값\|interactive.*agentic.*semi'` (섹션별 중복 패턴 검사) |
| 결과 | Pass |
| 상세 | "STATE.md 도메인 치환값" 섹션이 8개 pilot(opdd·opd·opds·opdw·opgc·opp·opwt·opsdd)에 존재(oppl·oppd는 해당 섹션 없음 — 구조상 불필요). 8개 전부 모드·단계 목록 중복 테이블 0건 — 잔존 매치는 전부 init 명령 예시의 `--mode <interactive\|semi-agentic\|agentic>` 문법 표기(중복 아님, CLI 사용법 문서화). 유일 예외: opsdd에 `\| 필드 \| 값 \|` 표가 남아있으나 내용은 "산출물 목록"·"태스크 경로"뿐(pipeline.json에 없는 고유 정보) — 시나리오가 명시적으로 허용한 잔존 범위. |

#### S-27: PM Gate 표 포인터화

| 항목 | 내용 |
|------|------|
| 가설 매핑 | (R-12 AC(a)) |
| 대상 | `## PM Gate 점검 목록` 절 |
| 계층 | L1 |
| **실행 방식** | **M1 (grep 산출물 검사)** |
| 조건 | Step 10~13 완료 |
| 기대 결과 | 게이트 산출물·체크리스트를 나열한 표 0건. 판정 절차 산문은 존치(C-6) |
| 도구 | grep |
| 실행 명령 | `grep -n "^## PM Gate 점검 목록" opal/skills/opal-pilot-*/SKILL.md` + `awk '/^## PM Gate 점검 목록/{f=1;next}/^## /{f=0}f' <file> \| grep -c '^\|.*\|.*\|'`(섹션 내 테이블행 카운트, 10 pilot) |
| 결과 | Pass |
| 상세 | 헤딩 자체는 7개 pilot(opd·opds·opdw·opp·opsdd·opwt·opdd)에 존치하나 내용 전부 "게이트 정의 SSOT" 포인터 산문(`references/pipeline.json task_steps[].gate` 참조 + 판정 절차는 STEP N "PM Gate" 절 따름)으로 교체 — 섹션 내 테이블행 0/7. 나머지 3종(opgc·oppl·oppd)은 동일 취지 포인터 산문을 다른 위치에 배치, 산출물·체크리스트 나열 표는 전 10종에서 0건. 판정 절차 산문(각 STEP 섹션의 "PM Gate" 서술)은 그대로 존치 확인. |

---

### L2. 프로세스 통합 (자동, 실 파일시스템 read→변경→re-read)

#### S-8: 중간 검증 — F-003 완료 시점 동등

| 항목 | 내용 |
|------|------|
| 가설 매핑 | (H-2 조기 검출) |
| 대상 | pipeline.json 편집이 `rows[]`를 건드리지 않았는지 |
| 계층 | L2 |
| **실행 방식** | **M1 (bash + python3 실호출)** |
| 조건 | Step 4~6 완료, `state_tool.py` 미변경 시점 |
| 기대 결과 | baseline 재측정 → 20/20 diff 0. 이 시점 diff 발생 = pipeline.json 편집이 행 구성을 훼손했다는 뜻 |
| 도구 | bash + python3 |
| 실행 명령 | (재현 불가 — 상세 참조) |
| 결과 | Blocked — 독립 재검증 불가 |
| 상세 | "F-003 완료·`state_tool.py` 미변경" 시점은 EXECUTE 진행 중의 특정 순간이며, 이번 태스크의 모든 변경(pipeline.json 10건 + state_tool.py 등)이 **단일 미커밋 워킹트리 diff**로 존재해 중간 커밋 체크포인트가 없다(`git log` 확인 — 태스크 시작 이후 신규 커밋 0건). TEST 단계는 EXECUTE 전체 완료 후 진입하므로 그 중간 시점을 되돌려 독립 재현할 방법이 없다(선택적 git stash는 "프로젝트 소스 수정 금지" 가드에 저촉될 위험이 있어 시도하지 않음). 다만 EXECUTE 시점에 PM이 실측한 기록이 있다: AGENTIC-LOG.md #21 "TS-008 중간 동등 20/20 diff 0"(2026-08-14 08:50, F-003 완료 직후). 이 기록은 TEST 단계의 독립 검증이 아니라 EXECUTE PM의 자체 확인이므로 정직하게 Blocked로 기록한다. 최종 시점 동등성은 S-29(20/20 diff 0, 이번 TEST 단계에서 독립 재현 완료)로 대체 커버된다. |

#### S-11: 차단 시 부분 상태 변경 부재

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | `cmd_mark` 실패 경로의 파일 쓰기 |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + 실 파일시스템)** |
| 조건 | S-10 실행 직후 |
| 기대 결과 | `state.json` 내용·mtime 무변화, `STATE.md` 무변화 — 검증이 `save_state_json()` **이전**에 수행됨 |
| 도구 | pytest |
| 실행 명령 | `pytest tests/test_state_tool.py -k TestTaskStepGate` (`test_s11_no_partial_state_change_on_block`) + 소스 확인(`cmd_mark`가 `save_state_json()` 호출 전 구간에서 게이트 가드 호출 여부) |
| 결과 | Pass |
| 상세 | PASSED. 소스상 가드 호출 지점(`state_tool.py:1527` 부근)이 `save_state_json()` 실호출(`:1596` 부근)보다 선행 — AGENTIC-LOG #23의 EXECUTE 실측("가드 `:1527` < `save_state_json()` `:1596`")과 본 코드 구조가 일치, 부분 상태 변경 부재가 구조적으로 보장됨. |

#### S-18: hook 세션 주입 실동작

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | `todo_mirror_hook.py` checklist 릴레이 |
| 계층 | L2 |
| **실행 방식** | **M1 (subprocess 실호출)** |
| 조건 | Step 9 완료. S-12의 실제 stdout을 stdin으로 주입 |
| 기대 결과 | hook exit 0 + `additionalContext`에 checklist 내용 포함 |
| 도구 | pytest + subprocess |
| 실행 명령 | `cd opal/tools/state-tool && python3 -m pytest tests/test_todo_mirror_hook.py -v` (`TestGateChecklistRelay::test_s18_gate_checklist_alone_injects_additional_context`) |
| 결과 | Pass |
| 상세 | PASSED. 테스트가 `subprocess.run([sys.executable, todo_mirror_hook.py], input=stdin_json)`로 스크립트를 실제 프로세스로 실행(mock 없음) — S-12의 `gate_checklist` stdout 형태를 stdin에 주입해 hook exit 0 + `additionalContext`에 checklist 릴레이 확인. |

#### S-19: 기존 페이로드 병존 (회귀)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | 076 `todo_mirror` · 088 `history_link` · 신규 checklist |
| 계층 | L2 |
| **실행 방식** | **M1 (subprocess 실호출)** |
| 조건 | Step 9 완료 |
| 기대 결과 | 세 페이로드가 병존 출력되고 기존 hook 테스트 15건 전건 통과 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest tests/test_todo_mirror_hook.py -v`(전체) |
| 결과 | Pass |
| 상세 | **17 passed**(기존 15건 + 신규 S-18/S-19 2건, 0 failed). `test_s19_three_payloads_coexist` PASSED — 076 `todo_mirror`·088 `history_link`·091 `gate_checklist` 3종 stdin 동시 주입 시 병존 릴레이 확인. 기존 15건(TS-010~013, TestHistoryLinkRelay 3건 등) 전건 회귀 없음. |

#### S-21: `--task-step` 신형 주소 채택 검증

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 (신형 채택 기준) |
| 대상 | 교체된 key 45건 |
| 계층 | L2 |
| **실행 방식** | **M1 (CLI 실호출)** |
| 조건 | Step 10~13 완료. **검증 입력은 SKILL.md에서 `--task-step\s+(\S+)` 정규식으로 직접 추출한다 — 워커가 제출한 key 목록을 입력으로 쓰지 않는다(self-confirming 차단)** |
| 기대 결과 | 추출된 key가 전부 해당 pipeline.json `task_steps[].key`에 실재. 대표 **4종**(opdd·opsdd·oppl·**opwt**)에서 `--task-step` 실호출 exit 0. opwt는 `--row` 2위이자 H-8 동적 key 규약 대상이므로 표본에서 제외하지 않는다 |
| 도구 | bash + state-tool |
| 실행 명령 | python3 정규식(`--task-step\s+(\S+)`)으로 10 pilot SKILL.md 변경이력 이전 구간 전량 추출 → placeholder(`<>`,`{}`,`\|` 포함) 제외한 concrete key를 `pipeline.json task_steps[].key` 집합과 대조 + 4개 pilot에서 `init`→`advance --task-step`→`mark --task-step --done` 실호출 |
| 결과 | Pass |
| 상세 | 추출: concrete 63건 / placeholder 31건. 최초 대조에서 opwt 2건("analysis.pm_gate","analysis.user_confirm")이 정적 `task_steps[].key`에 없어 불일치로 보였으나, opwt SKILL.md 자체가 이 두 key를 "수정/분석 모드 동적 `add-row --key`" 규약(S-23 대상)으로 명시 문서화(`add-row --key analysis.pm_gate` 등, SKILL.md:435-436) — 정적 존재검사 대상이 아닌 정상 설계(H-8과 정합). 이를 제외하면 불일치 0건. CLI 실호출: opdd·opsdd·oppl·opwt 4종 전부 `init`→`advance --task-step task.task_md`→`mark --task-step task.task_md --done` exit 0 확인. |

#### S-23: opwt 동적 key 규약 성립

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 |
| 대상 | `add-row --key` 신규 규약 (`analysis.*` 3, `execute.batch_*_1` 3) |
| 계층 | L2 |
| **실행 방식** | **M1 (CLI 실호출)** |
| 조건 | Step 13 완료 |
| 기대 결과 | 제안 key 6건 전량이 `KEY_PATTERN`을 만족하고 `add-row --key` exit 0으로 생성됨 |
| 도구 | state-tool |
| 실행 명령 | opwt SKILL.md §동적 key 규약(SKILL.md:434-443)에 문서화된 6건을 그대로 `add-row --after-task-step ... --stage ... --key ... --item ...`로 순차 실행(`{N}`→1 치환) |
| 결과 | Pass |
| 상세 | 6건 전부 exit 0: `analysis.analysis_md`(row_id3)→`analysis.pm_gate`(4)→`analysis.user_confirm`(5)→`execute.batch_1`(10)→`execute.batch_pm_gate_1`(11)→`execute.batch_user_confirm_1`(12). `KEY_PATTERN` 위반 거부 0건. |

#### S-26: init 정본 1개 + 실호출

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 |
| 대상 | pilot SKILL.md의 init 명령 |
| 계층 | L2 |
| **실행 방식** | **M1 (CLI 실호출)** |
| 조건 | Step 10~13 완료 |
| 기대 결과 | pilot당 완전 명령 최대 1회, 그 1건이 `--mode` 포함. 10종 init 실호출 exit 0 |
| 도구 | grep + state-tool |
| 실행 명령 | `awk '/^## 변경이력/{exit}{print}' <SKILL.md> \| grep -c "run.sh init.*--skill.*--mode"` (10 pilot) + 10종 `run.sh init --skill ... --mode semi-agentic --rows-from ...` 실호출 |
| 결과 | Pass |
| 상세 | 10/10 pilot 전부 완전 init 명령(--skill+--mode) 정확히 1건. oppl은 `run.sh init` 문자열이 2회 매치되나 두번째는 **다른 도구**(`backlog-tool/run.sh init`)로 중복 아님(확인). 10종 실 CLI 호출 전부 exit 0. |

#### S-28: 게이트 checklist 실출력 (신형 채택 검증)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | (R-12 AC(b) — 교체형 목표 채택 기준) |
| 대상 | 감량 완료된 pilot에서 게이트 행 mark |
| 계층 | L2 |
| **실행 방식** | **M1 (CLI 실호출)** |
| 조건 | Step 8~13 완료. 대표 3 pilot |
| 기대 결과 | SKILL.md 표가 사라진 자리에서 pipeline.json 유래 checklist가 stdout으로 실제 출력됨 — 정보 손실 0 |
| 도구 | state-tool |
| 실행 명령 | opd(`plan.pm_gate`)·opdw(`wireframe.pm_gate`)·opsdd(`spec.pm_gate`) 3종에서 `init`→선행 행 순차 `mark`→실 아티팩트 파일 생성(touch)→게이트 행 `mark --task-step <key> --done` |
| 결과 | Pass |
| 상세 | 3종 전부 `ok:true`+stdout `gate_checklist` dict 실측: opd `plan.pm_gate`→`{"artifacts":["TASK.md","PLAN.md"],"checklist":["TASK.md 요구사항","PLAN.md §4.2","PLAN.md §5","PLAN.md §리스크 가설 표"]}`, opdw `wireframe.pm_gate`→3항목 checklist(TASK.md 요구사항/wireframe.md 화면 목록/op-dev-qa 검증기준), opsdd `spec.pm_gate`→1항목 checklist. SKILL.md에서 표가 삭제된 지점의 정보가 CLI stdout으로 실제 출력됨을 확인. |

#### S-29: 전후 동등 최종 (20/20)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | (R-13 AC(a) — 최우선 제약) |
| 대상 | 10 pilot × 2 mode `rows[]` |
| 계층 | L2 |
| **실행 방식** | **M1 (bash + diff)** |
| 조건 | 전 편집 완료 후 |
| 기대 결과 | baseline vs after `diff -r` 출력 없음 (20/20) |
| 도구 | bash + diff |
| 실행 명령 | PLAN §3.6.2 절차 그대로 재현: `AFTER=$(mktemp -d)/after`; F-001과 동일 루프(10 pilot×2 mode `init --rows-from` → 7필드 투영 저장)를 `$AFTER`에 실행 → `diff -r tasks/091.../baseline "$AFTER"` |
| 결과 | Pass |
| 상세 | `after/` 20개 파일 생성 확인. `diff -r baseline after` **무출력, exit 0** — 20/20 완전 동일. 태스크 최우선 제약("행 구성 불변")이 전 편집 완료 후에도 성립함을 독립 재현으로 확정. `baseline/`은 건드리지 않음(읽기 전용 대조만 수행). |

#### S-30: 전체 회귀 (pytest)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | `opal/tools/state-tool/tests/` |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | 전 구현 완료. 기준선 **284 passed, 22 subtests** |
| 기대 결과 | `cd opal/tools/state-tool && python3 -m pytest tests/ -q` → 284 + 신규 전건 passed, 실패 0 |
| 도구 | pytest 9.1.0 |
| 실행 명령 | `cd opal/tools/state-tool && python3 -m pytest tests/ -q` |
| 결과 | Pass |
| 상세 | **304 passed, 32 subtests passed, 실패 0**(8.72s). 기준선(284 passed, 22 subtests) 대비 +20 tests·+10 subtests — 이번 태스크가 추가한 RED-first 시나리오 테스트(S-9~S-23 등)·hook 테스트(S-18/S-19) 전건 반영, 회귀 0건. |

#### S-31: 인접 기능 회귀 (088·076·dashboard)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2, H-11 |
| 대상 | 088 메모리 히스토리 연결, 076 todo_mirror, `show --format json` |
| 계층 | L2 |
| **실행 방식** | **M1 (CLI 실호출)** |
| 조건 | 전 구현 완료. 구 state.json 복사본 사용 |
| 기대 결과 | CLOSE mark 시 히스토리 자동 생성 불변, todo_mirror 페이로드 불변, `show --format json`이 dashboard `PipelineRow` 파싱과 호환 |
| 도구 | state-tool + python3 |
| 실행 명령 | `tasks/090-260813-opds-.../state.json`(gate 필드 없음)을 스크래치에 **복사**(원본 미접촉) → `close.done_md` 행을 `in_progress`로 리셋 후 `mark --task-step close.done_md --done` 실행 + `show --format json` 실행 |
| 결과 | Pass |
| 상세 | `mark`: `ok:true`, `history_link` 필드 존재(스크래치 경로가 실 프로젝트 루트 밖이라 `status:"skipped"`로 fail-safe 동작 — 088의 "예외/실패 전부 흡수, mark는 항상 ok:true" 설계와 정확히 일치, 크래시 없음), `todo_mirror` 필드 정상 존재, **`gate_checklist` 필드는 부재**(gate 없는 구 행이므로 H-3 회귀 없음 확인). `show --format json`: `data.rows[0]`가 `{row_id,stage,item,key,status,status_label,timestamp,owner,note}` 형태로 정상 반환 — dashboard `PipelineRow` 어댑터와 호환(추가 필수 필드 없음, gate 없는 구 데이터도 파싱 정상). 원본 090 태스크 파일은 무변경(복사본만 사용). |

#### S-32: 배포 정합 + 배포본 실동작

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10 |
| 대상 | `~/.opal/` 배포본 |
| 계층 | L2 |
| **실행 방식** | **M1 (install + CLI 실호출)** |
| 조건 | Step 16. install 재배포 후 |
| 기대 결과 | 배포본 pipeline.json 10건 소스와 `diff` 0. SKILL.md는 install이 변경이력을 strip하므로 strip 구간 제외 비교. 배포 경로 state-tool로 대표 3 pilot init + 게이트 차단 재현 |
| 도구 | install-mac.sh + diff + state-tool |
| 실행 명령 | `bash scripts/install-mac.sh`(재배포, 독립 재실행) → 10건 `diff opal/skills/<d>/references/pipeline.json ~/.opal/skills/<d>/references/pipeline.json` → `~/.opal/tools/state-tool/run.sh init/mark`로 opd(차단+통과)·opdw·opsdd(init) 재현 |
| 결과 | Pass |
| 상세 | install 재실행 exit 0("OPAL 설치 완료 v0.6.14-3-ged59eff"). 재배포 후 10/10 pipeline.json diff 0(무출력). 배포 경로(`~/.opal/tools/state-tool/run.sh`) 실호출: opd `init` exit 0 → 산출물(ANALYSIS.md) 부재 상태 `mark analysis.pm_gate --done` → `{"ok":false,"error":"gate_artifact_missing","missing":["ANALYSIS.md"]}`(차단 재현) → 산출물 생성 후 재실행 → `{"ok":true,"gate_checklist":{...}}`(통과+checklist 재현). opdw·opsdd도 배포 경로 `init` exit 0 확인(대표 3 pilot). |

---

### L3. 사용자 협업 (수동, [SUPERVISOR])

#### S-33: 실사용 게이트 체감 — 목표달성 검증 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | (TASK.md 목표 문장 — 목표달성 시나리오) |
| 대상 | 배포본으로 실제 태스크를 시작했을 때의 게이트 동작 |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업)**. 자동화 불가 — 새 세션의 실제 파이프라인 진행과 세션 주입 관측이 필요 |
| 조건 | Step 16 배포 완료. 캡틴이 **새 세션**에서 임의 pilot(예: `//opds`)로 태스크를 시작 |
| 기대 결과 | ① 산출물이 없는 상태에서 게이트 행 mark가 차단되고 `missing[]`이 표시된다 ② 산출물 충족 후 mark하면 checklist가 세션에 노출된다 ③ SKILL.md에 표가 없어도 PM이 게이트 기준을 알 수 있다 |
| 실행자 | [SUPERVISOR] — 캡틴 수동 확인 필요 |
| 결과 | 대기 — [SUPERVISOR] 캡틴 확인 필요 |
| 상세 | opal-test-agent는 L3 [SUPERVISOR] 시나리오를 실행하지 않고 PM에 위임한다(하네스 규칙). 자동화 검증 불가 — 새 세션·실제 사용자 협업 필요. |

**PM 요청 양식 (S-33)**

```
[SUPERVISOR 요청] S-33 실사용 게이트 체감
1. 새 세션을 여신 뒤 아무 프로젝트에서 `//opds <간단한 작업>`으로 태스크를 시작해주십시오.
2. PLAN 단계 PM Gate 행을 mark할 때 다음 두 가지를 확인해주십시오.
   (a) PLAN.md가 아직 없는 상태에서 mark → 차단되고 missing 목록이 뜨는가
   (b) PLAN.md 생성 후 mark → 체크리스트가 화면에 뜨는가
3. 결과를 알려주시면 TEST-SCENARIO.md에 기록하겠습니다. 판정이 어려우면 출력 원문을 그대로 주셔도 됩니다.
```

#### S-34: 감량된 SKILL.md 가독성 — 채택 검증 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 (좌표계 소실 여부의 사람 판정) |
| 대상 | 미러 표가 삭제된 pilot SKILL.md |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업)**. grep으로는 "해석 가능성"을 판정할 수 없다 |
| 조건 | Step 10~13 완료 |
| 기대 결과 | 캡틴이 미러 표 없이 SKILL.md를 통독했을 때 파이프라인 단계 구성과 게이트 기준을 문서만으로 파악할 수 있다. 어느 지점에서 pipeline.json을 열어야 하는지가 명확하다. **통독 대상 5종**(opds·opp·opdd·opd·opsdd)으로 산문 `행 N` 36건 중 **32건**을 관측 범위에 넣는다 |
| 실행자 | [SUPERVISOR] — 캡틴 수동 확인 필요 |
| 결과 | 대기 — [SUPERVISOR] 캡틴 확인 필요 |
| 상세 | opal-test-agent는 L3 [SUPERVISOR] 시나리오를 실행하지 않고 PM에 위임한다(하네스 규칙). grep으로 "해석 가능성"을 판정할 수 없어 사람의 통독 판단 필요. |

**PM 요청 양식 (S-34)**

```
[SUPERVISOR 요청] S-34 감량된 SKILL.md 가독성
1. 아래 5개를 통독해주십시오. (괄호 안은 산문 `행 N` 실측 건수 — 변경이력 제외 기준)
   - `opal/skills/opal-pilot-dev-short/SKILL.md` (opds — **최다 9건**)
   - `opal/skills/opal-pilot-project/SKILL.md` (opp — 8건)
   - `opal/skills/opal-pilot-data-design/SKILL.md` (opdd — 7건, `--row` 최다 14건)
   - `opal/skills/opal-pilot-dev/SKILL.md` (opd — 6건, 표준 구조 기준점)
   - `opal/skills/opal-pilot-sdd/SKILL.md` (opsdd — 2건, 25행 비표준 구조)
   → 5종으로 36건 중 **32건**이 관측 범위에 들어옵니다(게이트 iter1 G-3 + iter2 G-5 반영).
2. 다음을 판정해주십시오.
   (a) 미러 표 없이 파이프라인 단계 구성을 파악할 수 있는가
   (b) PM Gate 기준을 어디서 확인해야 하는지 문서가 알려주는가
   (c) 산문에 해석 불가능한 참조가 남아 있는가
3. (c)에 해당하는 지점이 있으면 위치를 알려주십시오 — 재작업하겠습니다.
```

---

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| R-1 AC | — | L1 | S-3 | (grep 검사) | 오문장 제거 |
| R-2 AC | — | L1 | S-2 | (grep 검사) | 상위 규칙 해제 |
| R-3 AC | — | L1 | S-4 | (grep 검사) | 줄번호 인용 |
| R-4 AC(a) 구형 잔존0 | H-7 | L1 | S-20 | (grep 검사) | `--row` 45→0 |
| R-4 AC(b) 신형 채택 | H-7, **H-13** | L1, L2 | **S-35**, S-21 | `tests/test_state_tool.py:[T091/L2-R4b]` | `--task-step` 전후 델타 + 실호출 |
| R-5 AC(재정의) | H-7 | L1, L3 | S-22, S-34 | (grep 검사 + 수동) | 비-변경이력 36→0 |
| R-6 AC(a) | H-7 | L1 | S-24 | (grep 검사) | 미러 표 0건 |
| R-6 AC(b) | H-2 | L2 | S-29 | (diff 검사) | rows[] 전후 동일 |
| R-7 AC | — | L1 | S-25 | (grep 검사) | 치환값 중복 |
| R-8 AC | H-9 | L2 | S-26 | `tests/test_state_tool.py:[T091/L2-R8]` | init 정본 1개 |
| R-9 AC(a) | H-12 | L1 | S-5 | `tests/test_state_tool.py:[T091/L1-R9a]` | gate 보유 27건 |
| R-9 AC(b) | — | L1 | S-6 | `tests/test_state_tool.py:[T091/L1-R9b]` | pm_gate 0건 |
| R-9 AC(c) | — | L1 | S-7 | `tests/test_state_tool.py:[T091/L1-R9c]` | 정보 손실 0 |
| R-10 AC | — | L1 | S-9 | `tests/test_state_tool.py:[T091/L1-R10]` | spec-validate |
| R-11 AC(a) | H-1 | L1, L2 | S-10, S-11 | `tests/test_state_tool.py:[T091/L1-R11a]` | 차단 + 부분변경 부재 |
| R-11 AC(b) | H-6 | L1 | S-12 | `tests/test_state_tool.py:[T091/L1-R11b]` | checklist dict |
| R-11 AC(c) | H-2, H-3 | L1 | S-13 | `tests/test_state_tool.py:[T091/L1-R11c]` | gate 미보유 무영향 |
| R-11 AC(d) | — | L1 | S-14 | `tests/test_state_tool.py:[T091/L1-R11d]` | 영구 차단 부재 |
| R-12 AC(a) | — | L1 | S-27 | (grep 검사) | PM Gate 표 0건 |
| R-12 AC(b) | — | L2 | S-28 | `tests/test_state_tool.py:[T091/L2-R12b]` | checklist 실출력 |
| R-13 AC(a) | H-2 | L1, L2 | S-1, S-8, S-29 | (diff 검사) | 전후 동등 20/20 |
| R-13 AC(b) | H-3 | L2 | S-30 | `tests/` 전건 | 284+신규 |
| R-13 AC(c) | H-2, H-11 | L2 | S-31 | `tests/test_state_tool.py:[T091/L2-R13c]` | 088·076·dashboard |
| R-14 AC | H-10 | L2 | S-32 | (install + 실호출) | 배포 정합 |
| 미결-4 (force 정책) | H-5 | L1 | S-15 | `tests/test_state_tool.py:[T091/L1-D4]` | force + 로그 |
| 미결-5 (세션 주입) | H-6 | L2 | S-18, S-19 | `tests/test_todo_mirror_hook.py:[T091/L2-D5]` | hook 릴레이 |
| 경계/보안 | H-4 | L1 | S-16, S-17 | `tests/test_state_tool.py:[T091/L1-H4]` | traversal·glob |
| **TASK 목표 문장** | — | L3 | **S-33** | (수동) | **목표달성 시나리오** |

> 매핑 완전성: R-1~R-14 전건 커버, **H-1~H-13** 전건 시나리오 연결, 미매핑 시나리오 0건.
> 테스트 파일은 **모듈 미러링** — 태스크 폴더가 아니라 `opal/tools/state-tool/tests/` 기존 2파일에 케이스를 추가한다(새 파일 분리 금지). 케이스명 프리픽스 `[T091/L{계층}-{AC}]`.

---

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | ruff | Pass(회귀 없음) | `ruff check` 변경 4개 .py 파일에서 15건 검출(F401 미사용 import 2·F841 미사용 변수 6·F541 불필요 f-string 1·E401/E402 각 2). `git show HEAD:<file>`로 만든 원본본과 정밀 대조(규칙+파일+변수명 단위) 결과 **동일 15건**(줄번호만 삽입된 코드량만큼 이동) — 이번 태스크가 신규로 유발한 위반 0건, 전건 기존부채. |
| 2 | 타입 체크 | mypy | Skip — 미설치 | `which mypy` → not found. 설치된 도구 없어 정직하게 스킵(있는 척 하지 않음). |
| 3 | 포맷터 | ruff format | Pass(회귀 없음) | `ruff format --check` 4개 파일 전부 "would reformat" — 단, 동일 명령을 `git show HEAD:` 원본에도 실행한 결과 **동일하게 4개 파일 전부 재포맷 대상**(기존 코드가 ruff 표준 포맷을 따르지 않음, 이번 태스크 이전부터의 상태). 신규 회귀 0건. |
| 4 | JSON 유효성 | python3 json.load | Pass | pipeline.json 10건 + `schema/pipeline-spec.schema.json` + `schema/state.schema.json` 총 12개 파일 전부 `json.load()` 성공(파싱 에러 0). |

---

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | Pass | `git diff --name-only`(태스크 폴더·MEMORY.json 제외) 대상 `grep -InE "(api[_-]?key\|secret\|password\|token\|aws_access\|private_key)\s*[:=]\s*['\"][A-Za-z0-9+/_-]{8,}"` — 매치 0건. |
| 2 | .gitignore 확인 | Pass | 표준 패턴(`.opal/*`, `__pycache__/`, `.pytest_cache/` 등) 확인. 스크래치 fixture는 레포 밖(`/private/tmp/.../scratchpad`)에만 생성해 레포 오염 0 — `git status --short`로 예상 외 신규/변경 파일 없음 확인(본 태스크 diff 목록 + `tasks/091.../` untracked 외 없음). |
| 3 | 경로 이탈(path traversal) 방어 — S-16 | Pass | `_is_safe_artifact_token()`(`state_tool.py:728-736`) 실코드 확인: `pathlib.PurePosixPath(t).is_absolute()` 또는 `".." in pp.parts`이면 `False`(불안전) 판정 후 `check_gate_artifacts()`가 missing 처리(예외 미발생). pytest `test_s16_path_traversal_tokens_rejected_as_missing` PASSED로 교차 확인(S-16과 동일 근거). |

---

## 7. 판정

**Partial Fail -- 근거: 실행 가능 33건(L1 21 + L2 12) 중 32건 Pass(전건 실제 명령 출력 증거로 확보) + 1건(S-8) Blocked. S-8은 "F-003 완료·state_tool.py 미변경" 중간 시점 재검증으로, 이번 태스크의 전 변경이 단일 미커밋 워킹트리 diff라 중간 체크포인트가 없어 TEST 단계(EXECUTE 완료 후)에서 구조적으로 재현 불가능하다 — 기능 결함이 발견된 것이 아니라 검증 시점 접근 불가이며, 동일 취지의 최종 시점 동등성은 S-29(`diff -r baseline after` 20/20, 무출력)로 독립 재현·확정했다. L3 2건(S-33·S-34, `[SUPERVISOR]`)은 하네스 규칙에 따라 실행하지 않고 캡틴 수동 확인 대기로 남겨두었으며 **미검증을 Pass로 세지 않았다**. 태스크 최우선 제약·핵심 검증 항목은 전부 실증 Pass: S-29(20/20 diff 0) · S-30(pytest 304 passed/32 subtests, 0 failed) · S-35(신형 채택 수량 대응 — raw 불일치 5건을 근거와 함께 규명 후 45건 정확 일치 확정, "삭제-만-함" 070 재발 없음) · S-10~S-17(게이트 8종 pytest+실 CLI) · S-32(배포본 diff 0 + 배포경로 게이트 실동작). 코드품질(린트/포맷 위반 15건은 전량 태스크 이전 기존부채로 확인, 신규 회귀 0) · 보안(시크릿 0건, 경로이탈 방어 실증, .gitignore 정상) 모두 Pass. 실제로 발견된 기능적 결함은 0건이므로 "Partial Fail"은 버그가 아니라 **검증 완결성 기준의 보수적 판정**임을 명시한다.**

### PM Gate 체크 (7대 강제 룰)

- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 (grep 확인)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전 (미매핑 시나리오 없음)
- [x] L1/L2/L3 계층 명시 (모든 시나리오)
- [x] L3 [SUPERVISOR] 마커 존재 + PM 요청 양식 첨부 (S-33, S-34)
- [x] 리스크 가설 표(§1) H-N ID와 시나리오 S-N 1:N 매핑 완전
- [x] 모든 시나리오에 실행 방식(M1/M2/M3) 명시
- [x] **FE 변경 시 M2 시나리오 포함** — 해당 없음. 변경 영역에 FE 화면/컴포넌트·인증/인가·외부 API 연동이 **없음**(대상은 Python CLI 도구 + Markdown/JSON 문서). `test-scenario-guide.md` §Step 3-b M2 의무 트리거 비대상
- [x] **목표 커버** — R-1~R-14 전건이 §4에 커버되고, 목표달성 시나리오 **S-33**(L3/M3)이 사용자 계층에서 태스크 목표를 검증
