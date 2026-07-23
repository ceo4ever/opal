# TASK: state-tool task-step 키 주소 체계 도입 1차 — pipeline.json 표준화 + 그룹 A 전환

> 작성일: 2026-07-20 | 작업 유형: 개선 | 적용 스킬: opd | 모드: agentic
> 입력: 사용자 요청 (2026-07-20 대화 — state-tool 행 번호 enum 개선 논의)
> 출력: TASK.md

## 작업 목표

state-tool의 행 주소를 "불안정한 순번(`--row N`)" 의존에서 "SKILL.md 참조 JSON 스펙에 선언된 task-step key(`plan.pm_gate`)" 체계로 개선한다.
1차 범위로 스펙 스키마 신설 + state-tool 코어 확장 + 표준형 pilot 4종(opp/opd/opds/opdw) 전환 + opdd enum 드리프트 정정을 수행한다.

## 배경

- 행 번호의 의미는 코드 어디에도 고정 정의가 없고, init 시점 SKILL.md 마크다운 표 순서로 부여되는 위치값일 뿐이다 (`opal/tools/state-tool/state_tool.py:516` `build_rows_from_skill_md`).
- `add-row`가 row_id를 전체 재정렬하므로 삽입 이후 LLM이 기억하던 번호가 밀리며, 번호를 잘못 세면 **엉뚱한 행을 성공적으로 갱신**한다 — 도구 게이트가 못 잡는 유일한 오갱신 경로.
- SKILL.md 표를 4단 regex로 파싱하는 현행 방식은 깨지기 쉽다 (`skill_md_parse_error` 발생 면적).

## 배경 분석 (대화에서 도출)

- 9개 pilot 전수 검토 결과 3그룹으로 분류됨: 그룹 A 표준형 4종(opp/opd/opds/opdw — 표준 항목만), 그룹 B 고정 비표준 3종(opgc/opsdd/oppd), 그룹 C 동적 2종(opwt/oppl — variants·dynamic_rows 확장 필요).
- 전체 task-step 인벤토리: 고정 118개 + 동적 4패턴(fix/batch/act/t{nn}).
- **드리프트 발견**: `opal-pilot-data-design`은 `--skill opdd`를 지시하나 skill enum(`opal/tools/state-tool/schema/state.schema.json:15`)에 미등록, 단계 DICT/MODEL/DDL/MIGRATION도 stage 16종 enum(`state.schema.json:55`)에 없음 — 현재 init 자체가 거부되는 상태.
- oppd는 유일하게 행 표 자체가 없음(Phase 진행 현황 자유 표) — 전환 시 신규 정의 필요(2차 범위).
- 기존 `--step N/M`은 EXECUTE 내 PLAN 실행 체크리스트의 **액션 Step 진행률** 표기로, 파이프라인 행과 별개 개념 (`state_tool.py:919`).

## 확정된 설계 방향 (대화에서 합의)

1. **스펙 파일 표준**: pilot당 `opal/skills/{pilot}/references/pipeline.json` 1개 (섹션 통합형 — meta/task_steps/pm_gate). SKILL.md에는 데이터 중복 게재 없이 참조와 행동 지시·설계 근거만 유지.
2. **개념·용어**: 행 1개 = **task-step**. 문자 주소 = task-step key(`{stage_slug}.{item_slug}`), 숫자 주소 = task-step id(1-based 유지 — 캡틴 확정).
3. **플래그 네이밍** (캡틴 확정): 신규 `--task-step`(key) / `--task-step-id`(숫자). 기존 `--row`는 deprecated 별칭 유지. 기존 `--step`은 `--action-step`으로 개명(별칭 `--step` 유지).
4. **init 스펙 지정**: 신규 플래그 없이 기존 `--rows-from`이 `.json`을 받도록 확장 (`--spec`은 `--rows-spec`과 혼동 위험으로 철회). `.md`는 레거시 파싱 + deprecation 경고.
5. **slug 명명 규칙** (캡틴 확정 — `work` 폐기): ① 산출물 스텝 = 산출물명(`task_md`·`plan_md`·`wireframe_md`) ② 행위 스텝 = 동사(`implement`·`run_tests`·`review`) ③ 게이트 스텝 = 주체+게이트(`pm_gate`·`user_confirm`). `confirm`도 주체 명시를 위해 `user_confirm`으로 확정.
6. **key 형식**: `^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*(_[0-9]+)?$`, stage_slug는 stage enum 소문자화(`-`·`/`→`_`), 스펙 내 유일성 강제.
7. **단계 분할**: 1차(본 태스크)=코어+그룹 A+opdd enum / 2차=dynamic_rows+그룹 B / 3차=variants+그룹 C+문서 24곳 일괄 갱신.

## 명확화 결과

> TASK 4요소를 잠근다. 각 요소는 확정값 또는 명시적 "N/A: <사유>"로 채운다 (공란·TBD 금지).

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | state-tool 행 주소를 선언된 task-step key 체계로 개선 — pipeline.json 스펙 표준화 + key 주소 플래그 + 그룹 A 4종 전환 + opdd enum 드리프트 정정 | - | `state_tool.py:516`, `state.schema.json:15,55` |
| 범위 | 포함: pipeline-spec.schema.json 신설 / state-tool(--rows-from json·--task-step·--task-step-id·--action-step·spec-validate·add-row --key) / state.schema.json 1.1(key) / opp·opd·opds·opdw pipeline.json+SKILL.md / opdd skill·stage enum 등록. 제외: dynamic_rows·variants 확장, 그룹 B·C 전환, opdd pipeline.json, `--row` 안내 문서 24곳 일괄 갱신, install 실행 | - | 대화 확정 §7 |
| 제약 | `~/.opal/` 직접 수정 금지(프로젝트 소스만) / 하위호환 필수(--row·--step 별칭, .md 파싱, key 없는 레거시 state.json) / 커밋은 사용자 명시 요청 시만 / 본 태스크의 state 관리는 배포본 state-tool 사용(소스 수정 중 자기참조 오염 방지) | - | `.opal/AGENT.md` 금지사항 |
| 완료기준 | ① pytest 전체 PASS(기존 회귀 0 + 신규 케이스) ② 그룹 A 4종 pipeline.json으로 `init` 실증 + `--task-step` mark 동작 실증 ③ opdd `init --skill opdd` 거부 해소 실증 ④ `--row`·`--step` 별칭 동작 회귀 없음 ⑤ 변경 파일 변경이력 표 갱신 | - | 요구사항 AC |

## 요구사항

- [ ] **R-1 pipeline-spec.schema.json 신설**
  - 무엇을: 스펙 JSON Schema(Draft-07) 작성 — `spec_version`·`skill`·`meta{mode_label,stages}`·`task_steps[{id,key,stage,item,conditional?}]`·`pm_gate[{stage,artifacts,checklist}]`
  - 어디에: `opal/tools/state-tool/schema/pipeline-spec.schema.json`
  - 왜: 확정 방향 §1·§6 — 스펙 표준의 결정론 검증 기준
  - AC: 스키마 파일이 존재하고, 그룹 A 4종 pipeline.json이 모두 이 스키마 검증을 통과하며, key 중복·형식 위반 샘플이 거부된다
- [ ] **R-2 state-tool `--rows-from` .json 확장**
  - 무엇을: 확장자 분기 — `.json`이면 스키마 검증 후 task_steps 로딩(key 포함), `.md`면 기존 파싱 + stderr deprecation 경고
  - 어디에: `opal/tools/state-tool/state_tool.py` init 경로
  - 왜: 확정 방향 §4
  - AC: json 스펙으로 init 시 state.json rows에 key가 저장되고, md로 init 시 기존과 동일 결과 + 경고 1줄
- [ ] **R-3 state.json 스키마 1.1 — rows[].key 추가**
  - 무엇을: `key` 선택 필드(정규식 패턴) 추가, `schema_version` "1.1" 승격(1.0 병행 허용)
  - 어디에: `opal/tools/state-tool/schema/state.schema.json`
  - 왜: 확정 방향 §2 — key 영속화
  - AC: key 있는 1.1 state.json과 key 없는 레거시 1.0 state.json 모두 validate 통과
- [ ] **R-4 행 주소 플래그 신설 — `--task-step` / `--task-step-id`**
  - 무엇을: advance/mark/block/add-row(--after 대응 포함)에 key 주소·숫자 주소 플래그 추가, `--row`는 deprecated 별칭(동작 유지·help에 deprecated 표기), key 미매칭 시 `task_step_not_found` 에러(후보 목록 포함)
  - 어디에: `state_tool.py` argparse + 행 해석 공통 함수
  - 왜: 확정 방향 §3 — 번호 불안정성 제거
  - AC: `mark --task-step plan.pm_gate --done`이 해당 행을 갱신하고, 동일 행에 `--task-step-id`·`--row`도 동작하며, 주소 플래그 2개 이상 동시 사용은 `task_step_addr_conflict`로 거부된다
- [ ] **R-5 `--step` → `--action-step` 개명**
  - 무엇을: mark의 진행률 플래그를 `--action-step N/M`으로 개명, `--step` 별칭 유지
  - 어디에: `state_tool.py` p_mark
  - 왜: 확정 방향 §3 — "step" 이중 의미 해소
  - AC: `--action-step 2/6`과 `--step 2/6` 모두 기존 진행률 동작과 동일
- [ ] **R-6 `spec-validate` 서브명령 신설**
  - 무엇을: `spec-validate <pipeline.json 경로>` — 스키마 검증 + key 유일성·형식·stage enum 정합 검사, 단일 라인 JSON 응답
  - 어디에: `state_tool.py` + run.sh 라우팅
  - 왜: 확정 방향 §1 — 스펙 저작 시점 게이트 (수정계 서브명령은 2차)
  - AC: 정상 스펙 ok:true, key 중복/형식 위반/stage 위반 스펙에 각각 구분된 에러 코드 반환
- [ ] **R-7 그룹 A 4종 pipeline.json 생성 + SKILL.md 전환**
  - 무엇을: opp(9)·opd(15)·opds(10)·opdw(9) `references/pipeline.json` 생성(확정 slug 체계, opdw 3~5행 `conditional:true`), 각 SKILL.md "STATE.md 도메인 치환값" 섹션을 JSON 참조 + 지시문·근거만 남기게 수정, init 호출 예시를 json 경로로 교체
  - 어디에: `opal/skills/{opal-pilot-project,opal-pilot-dev,opal-pilot-dev-short,opal-pilot-dev-wireframe}/`
  - 왜: 확정 방향 §1·§5·§7
  - AC: 4종 모두 `spec-validate` 통과 + 실제 `init --rows-from references/pipeline.json` 실증으로 state.json 생성(행 수 9/15/10/9 일치, key 전 행 존재)
- [ ] **R-8 opdd 드리프트 정정 (enum 등록만)**
  - 무엇을: skill enum에 `opdd` 추가(state_tool.py choices + state.schema.json), stage enum에 `DICT`·`MODEL`·`DDL/MIGRATION` 추가(16→19종)
  - 어디에: `state_tool.py`, `state.schema.json`
  - 왜: 배경 분석 — 현재 opdd init 거부 상태
  - AC: `init --skill opdd` + DICT 단계 행 add-row가 enum 에러 없이 동작
- [ ] **R-9 add-row `--key` 지원**
  - 무엇을: 동적 행 삽입 시 `--key` 선택 입력, 미지정 시 `{stage_slug}.{item기반 slug}_{n}` 자동 생성, 파일 내 유일성 보장
  - 어디에: `state_tool.py` add-row
  - 왜: 확정 방향 §2 — 동적 행도 key 주소 가능해야 재정렬 무관성 완성
  - AC: add-row 후 신규 행에 key가 존재하고 기존 행 key는 불변, 중복 key 지정 시 거부
- [ ] **R-10 테스트 보강**
  - 무엇을: 신규 기능(R-1~R-9) pytest 케이스 추가 + 기존 테스트 전체 회귀 확인
  - 어디에: `opal/tools/state-tool/tests/test_state_tool.py`
  - 왜: 완료기준 ①
  - AC: `pytest opal/tools/state-tool/tests/` 전체 PASS, 기존 케이스 수정 없이 통과(별칭 하위호환 증명)

## 제약 조건

- `~/.opal/` 배포 파일 직접 수정 금지 — 프로젝트 소스만 수정, 배포는 install(사용자 요청 시 별도).
- 본 태스크 진행 중 state 관리는 **배포본** `~/.opal/tools/state-tool/run.sh` 사용 (수정 중인 소스로 자기 자신을 관리하지 않는다).
- 하위호환: `--row`·`--step` 별칭, `.md` 파싱 폴백, key 없는 레거시 state.json 모두 동작 유지. 기존 테스트 케이스 수정 금지.
- 커밋은 사용자 명시 요청 시만.
- 수정 파일 변경이력 표 행 추가 의무 (일시 KST + 태스크 070).

## 기술 스택

- Python 3.14 (표준 라이브러리만 — json/argparse/pathlib/re/subprocess), pytest
- JSON Schema Draft-07 (참조용 — 런타임 검증은 표준 라이브러리 자체 구현 관례 확인 후 결정)
- bash 래퍼 (`run.sh`), node date.js (KST)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py` | 수정 대상 본체 (1,936줄) |
| D-2 | 설계 | state.schema.json | `opal/tools/state-tool/schema/state.schema.json` | 1.1 승격 대상 |
| D-3 | 설계 | state-tool README | `opal/tools/state-tool/README.md` | 서브명령·에러 카탈로그 SSOT — 갱신 대상 |
| D-4 | 소스 | 그룹 A SKILL.md 4종 | `opal/skills/opal-pilot-{project,dev,dev-short,dev-wireframe}/SKILL.md` | 도메인 치환값 섹션 전환 대상 |
| D-5 | 설계 | 원 설계 SSOT | `tasks/134-260501-opp-pipeline-state-tool/PLAN.md` | §2.1~§2.20 기존 설계 근거 |
| D-6 | 설계 | opdd SKILL.md | `opal/skills/opal-pilot-data-design/SKILL.md` | 드리프트 근거 (단계 목록·--skill opdd) |
| D-7 | 소스 | 기존 테스트 | `opal/tools/state-tool/tests/test_state_tool.py` | 회귀 기준선 |
