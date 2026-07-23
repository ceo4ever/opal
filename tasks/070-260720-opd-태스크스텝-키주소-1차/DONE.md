# DONE: state-tool task-step 키 주소 체계 도입 1차

> 완료일: 2026-07-23 10:10 (KST) | 적용 스킬: opd | 모드: agentic
> 착수: 2026-07-20 | 상태: 완료 (미커밋·미배포)

## 1. 목표 달성 요약

state-tool의 행 주소를 불안정한 순번(`--row N`) 의존에서 **선언된 task-step key**(`plan.pm_gate`) 체계로 전환했다. pilot의 파이프라인 정의를 SKILL.md 마크다운 표에서 `references/pipeline.json`(구조화 SSOT)으로 분리·표준화하고, 그룹 A 표준형 4종(opp/opd/opds/opdw)을 전환했다.

## 2. 구현 결과 (R-1~R-11 + 후속)

| 항목 | 내용 | 상태 |
|------|------|------|
| R-1 | `pipeline-spec.schema.json` 신설 (Draft-07 문서 SSOT) | ✅ |
| R-2 | `--rows-from` `.json`/`.md` 확장자 분기 (.md는 deprecation 경고) | ✅ |
| R-3 | state.schema.json 1.1 — `rows[].key`·`conditional` 선택 필드 | ✅ |
| R-4 | 행 주소 플래그 `--task-step`(key)·`--task-step-id`(숫자), `--row` deprecated 별칭 | ✅ |
| R-5 | `--step` → `--action-step` 개명 (별칭 유지) | ✅ |
| R-6 | `spec-validate` 서브명령 (수작업 검증, jsonschema 미사용) | ✅ |
| R-7 | 그룹 A 4종 `pipeline.json` 생성 + SKILL.md 도메인 섹션 전환 | ✅ |
| R-8 | opdd 드리프트 정정 — skill·stage enum 등록 (init 거부 해소) | ✅ |
| R-9 | `add-row --key` (자동 생성·유일성) | ✅ |
| R-10 | 테스트 보강 (신규 클래스 + 회귀) | ✅ |
| 후속-A | 그룹 A 4종 SKILL.md **본문** 명령 예시 `--row`→`--task-step`, `--step`→`--action-step` 전환 (내부 불일치 해소) | ✅ |
| 후속-B | `cmd_init` schema_version stamp — pipeline.json 경로(key 보유)→`1.1`, `.md`/spec→`1.0` (R-3 "1.1 승격" 충족) | ✅ |

> **slug 명명 확정**: 산출물 스텝=산출물명(`task_md`·`plan_md`·`wireframe_md`), 행위 스텝=동사(`implement`·`run_tests`), 게이트=`pm_gate`·`user_confirm`. `work` 폐기. key 형식 `{stage_slug}.{item_slug}` (stage enum 소문자화, `-`·`/`→`_`).

## 3. 검증 (완료기준 대조)

| 완료기준 | 결과 |
|---------|------|
| ① 전체 테스트 PASS | Ran 241 / **240 PASS + 선재 1 FAIL** (`TestVerify.test_verify_passes_own_test_scenario_md` — 삭제된 034 산출물 참조, 070 무관·git 기준선 확증) |
| ② 그룹 A init + key mark 실증 | opp9/opd15/opds10/opdw9 `spec-validate` ok + 실제 init 행수 일치 + `--task-step` mark 동작 |
| ③ opdd 거부 해소 | `init --skill opdd` + DICT add-row enum 에러 없이 동작 |
| ④ `--row`/`--step` 별칭 회귀 0 | 3주소(`--task-step`/`--task-step-id`/`--row`) 동일 행 해석, 별칭 하위호환 유지 |
| schema_version | 소스 실측 pipeline.json→`1.1`, `.md`→`1.0` |
| 시나리오 | S-1~S-14 전부 PASS (RED-first 강제 트랙, RED 32케이스→GREEN) |
| 컨벤션 | Critical/High 0 (Medium 1 정정 완료, Low/Info는 선재·정책갭) |
| 보안 | changed_files 시크릿 0, 신규 인젝션 표면 없음 |

## 4. 변경 파일 (070 범위)

**수정**: `opal/tools/state-tool/state_tool.py`, `schema/state.schema.json`, `README.md`, `tests/test_state_tool.py`, `opal/skills/opal-pilot-{project,dev,dev-short,dev-wireframe}/SKILL.md`(4), `docs/CONVENTIONS.md`, `.opal/MEMORY.md`(채번)
**신규**: `opal/tools/state-tool/schema/pipeline-spec.schema.json`, `opal/skills/opal-pilot-{project,dev,dev-short,dev-wireframe}/references/pipeline.json`(4)

> ⚠️ **커밋 스코프 주의**: `opal/tools/brain-tool/*`·`tasks/071-*`는 **다른 세션의 071 작업**이므로 070 커밋에서 제외한다.
> `~/.opal/` 무수정 (배포 경계 준수).

## 5. 핵심 의사결정 (AGENTIC-LOG 상세)

- DEC-1: `conditional`=순수 메타데이터(자동 na 없음, 자동화는 2차) / DEC-2: spec 검증=수작업 함수(표준 라이브러리만) / DEC-3: 테스트=unittest.
- 기존 테스트 수정 예외 1건 승인: `TestErrorCodesCompleteness` 카운트 31→39 (신설 8종 반영 — 약화 아닌 계약 갱신).
- fix 루프 2회: RED 저작 결함 2건 / 컨벤션 Medium 1건(addr_label 미사용 → add-row 오류 메시지 플래그명).

## 6. 미해결·후속 (범위 밖)

| 항목 | 조치 |
|------|------|
| **배포본 stale** | `~/.opal`은 어제 설치된 복사본 — 070-코어만 있고 오늘 수정 없음. **라이브 세션(071 등)은 `install` 재배포 전까지 `--row`·`1.0` 유지** |
| install 재배포 | 070 범위 제외 — 사용자 지시 시 실행 (라이브 반영 조건) |
| 커밋 | 사용자 지시 시 (070 파일만, 071 제외) |
| 2차 | dynamic_rows 확장 + 그룹 B(opgc/opsdd/oppd) 전환 |
| 3차 | variants 확장 + 그룹 C(opwt/oppl) + `--row` 안내 문서 24곳(하네스·비그룹A) 일괄 갱신 |
| 선재 FAIL | `TestVerify` 034 참조 — 070 무관, 별도 정리 |
| add-row 자동 key 서술성 | 한글 item→`stage.item_N` 폴백 (기능 정상, 개선 후보) |
| 071 state.json 1.0+key | 라이브 태스크라 불가침 — 무해(validate 통과), install 후 신규 init부터 1.1 |
