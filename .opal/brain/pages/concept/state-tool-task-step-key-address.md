---
type: concept
title: state-tool task-step 키 주소 체계
tags:
- state-tool
- pipeline
- key-address
- task-070
sources:
- task:070
related:
- state-tool
- pipeline-json-spec
created: '2026-07-23'
updated: '2026-07-23'
status: active
---
## 개념 요약

state-tool의 행 주소 방식을 불안정한 순번(`--row N`)에서 pilot이 선언한 task-step key(`{stage_slug}.{item_slug}`, 예: `plan.pm_gate`)로 전환한다. 1차 범위로 그룹 A 표준형 4종(opp/opd/opds/opdw)에 적용했다.

## 배경·문제 (WHY)

- 행 번호는 코드 어디에도 고정 정의가 없고, init 시점 SKILL.md 표 순서로 부여되는 위치값일 뿐이었다(근거: task:070 TASK.md 배경).
- `add-row`가 row_id를 전체 재정렬하므로 삽입 이후 LLM이 기억하던 번호가 밀리며, 번호를 잘못 세면 엉뚱한 행이 성공적으로 갱신되는 오류를 도구 게이트가 잡지 못했다(근거: task:070 TASK.md 배경).
- SKILL.md 표를 4단 regex로 파싱하는 기존 방식이 깨지기 쉬워 `skill_md_parse_error` 발생 면적이 넓었다(근거: task:070 TASK.md 배경).
- 대안: jsonschema 패키지로 런타임 검증하는 안은 표준 라이브러리만 허용하는 기술 스택 제약으로 기각하고, 수작업 검증 함수(DEC-2)를 채택했다(근거: task:070 PLAN.md DEC-2).

## 결정 내용 (HOW)

- pilot 파이프라인 정의를 SKILL.md 마크다운 표에서 `references/pipeline.json`(구조화 SSOT)으로 분리했다. 스펙 형식은 `pipeline-spec.schema.json`(Draft-07, 문서 SSOT)으로 표준화하고 `spec-validate` 서브명령이 수작업 검증 함수로 집행한다.
- key 형식: `^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*(_[0-9]+)?$` — `{stage_slug}.{item_slug}`. stage_slug는 stage enum을 소문자화하고 `-`·`/`를 `_`로 치환하며, 스펙 내 유일성을 강제한다.
- slug 명명 규칙(확정): 산출물 스텝 = 산출물명(`task_md`·`plan_md`·`wireframe_md`), 행위 스텝 = 동사(`implement`·`run_tests`·`review`), 게이트 스텝 = 주체+게이트(`pm_gate`·`user_confirm`). 범용 slug `work`는 폐기했다.
- 주소 플래그: 신규 `--task-step`(key 주소)·`--task-step-id`(숫자 1-based 주소)를 추가하고, 기존 `--row`는 deprecated 별칭으로 남겨 동일 행 산출을 보장한다. 진행률 플래그는 `--step`→`--action-step`으로 개명(별칭 `--step` 유지) — "step"이 파이프라인 행과 액션 진행률 두 의미로 쓰이던 혼동을 해소했다.
- state.json 스키마 1.1: `rows[].key`(선택)·`rows[].conditional`(선택) 필드를 추가했다. `conditional`은 순수 메타데이터로 저장만 하며 자동 na 마킹은 수행하지 않는다(DEC-1 — 자동화는 2차 dynamic_rows 범위로 유보. Simplicity First).
- 1차 범위: 그룹 A 표준형 4종(opp 9행·opd 15행·opds 10행·opdw 9행) 전환 + opdd skill·stage enum 드리프트 정정(DICT/MODEL/DDL·MIGRATION 등록, `init --skill opdd` 거부 상태 해소).

## 영향·관계

- `opal/tools/state-tool/state_tool.py` — `KEY_PATTERN`(`:40`)·`stage_to_slug`(`:43`)·`validate_pipeline_spec`(`:685`)·`build_rows_from_pipeline_json`(`:747`)·`cmd_spec_validate`(`:1381`) 신설, `--row`/`--step` 하위호환 별칭 유지
- `opal/tools/state-tool/schema/state.schema.json` — `schema_version` 1.1(1.0과 병행 허용)
- [[pipeline-json-spec]] — 이 결정으로 신설된 pipeline.json 스펙·pipeline-spec.schema.json 상세
- [[state-tool]] — 이 결정을 구현하는 도구
- 후속: 2차 dynamic_rows 확장 + 그룹 B(opgc/opsdd/oppd) 전환, 3차 variants 확장 + 그룹 C(opwt/oppl) + `--row` 안내 문서 일괄 갱신

## 근거 출처

- task:070 — state-tool task-step 키 주소 체계 도입 1차 (TASK.md 배경·확정된 설계 방향, PLAN.md DEC-1~DEC-3)
