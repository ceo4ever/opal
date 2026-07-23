---
type: entity
title: pipeline.json (pilot 파이프라인 정의 SSOT)
module: pipeline_spec
layer: schema
domain: opal-pipeline
exports: [pipeline-spec.schema.json]
source_ref: opal/tools/state-tool/schema/pipeline-spec.schema.json
header_synced: 2026-07-23
tags:
- state-tool
- pipeline
- schema
- task-070
sources:
- task:070
related:
- state-tool
- state-tool-task-step-key-address
created: '2026-07-23'
updated: '2026-07-23'
status: active
---

## 개요

pilot(opp/opd/opds/opdw 등)의 task-step 파이프라인 정의를 SKILL.md 마크다운 표 대신 담는 구조화 JSON 파일이다. 각 pilot 디렉토리의 `references/pipeline.json`에 위치하며, state-tool init이 이 파일을 읽어 STATE.md 행을 생성한다.

## 책임 (WHAT)

- 스펙 필드: `spec_version`(const "1.0")·`skill`(enum)·`meta.mode_label`·`meta.stages`·`task_steps[]`(id/key/stage/item/conditional?)·`pm_gate[]`(stage/artifacts/checklist) (`opal/tools/state-tool/schema/pipeline-spec.schema.json`)
- `spec-validate <pipeline.json>` 서브명령이 필수 필드·skill enum·stage enum·key 형식(KEY_PATTERN)·key 유일성·id 순차성·key-stage 정합을 검사한다 (`opal/tools/state-tool/state_tool.py:685` `validate_pipeline_spec`, `:1381` `cmd_spec_validate`)
- `init --rows-from references/pipeline.json`이 이 스펙을 읽어 state.json `rows[]`에 key를 영속화한다 (`opal/tools/state-tool/state_tool.py:747` `build_rows_from_pipeline_json`)

## 설계 배경 (WHY)

- pilot마다 SKILL.md 마크다운 표를 4단 regex로 파싱하던 기존 방식이 깨지기 쉬웠고, 데이터(파이프라인 정의)와 문서(지시문·설계 근거)가 SKILL.md 한 파일에 섞여 있었다 (근거: task:070 TASK.md 배경).
- `pipeline-spec.schema.json`은 Draft-07로 작성됐지만 런타임 검증은 jsonschema 패키지 없이 수작업 함수(`validate_pipeline_spec`)로 수행한다 — 스키마 파일은 문서 SSOT 역할만 한다 (근거: task:070 PLAN.md DEC-2, 표준 라이브러리만 허용하는 기술 스택 제약).
- `.md` 파싱 경로는 폐기하지 않고 deprecated 경고와 함께 유지한다 — 하위호환 제약 때문이다 (근거: task:070 TASK.md 제약).

## 관계 (HOW)

- [[state-tool]]이 이 스펙을 로드·검증·집행하는 도구다.
- [[state-tool-task-step-key-address]] — 이 파일 도입의 상위 아키텍처 결정.

## 소스 커버리지

| 식별자 | 경로:줄번호 | 설명 |
|--------|-----------|------|
| `pipeline-spec.schema.json` | `opal/tools/state-tool/schema/pipeline-spec.schema.json` | 스펙 문서 SSOT (Draft-07) |
| `KEY_PATTERN` | `opal/tools/state-tool/state_tool.py:40` | task-step key 정규식 |
| `stage_to_slug` | `opal/tools/state-tool/state_tool.py:43` | stage enum → slug 변환 |
| `validate_pipeline_spec` | `opal/tools/state-tool/state_tool.py:685` | 수작업 스펙 검증 함수 |
| `build_rows_from_pipeline_json` | `opal/tools/state-tool/state_tool.py:747` | .json 스펙 → rows[] 변환 |
| `cmd_spec_validate` | `opal/tools/state-tool/state_tool.py:1381` | spec-validate 서브명령 |
| opp pipeline.json | `opal/skills/opal-pilot-project/references/pipeline.json` | 9행 |
| opd pipeline.json | `opal/skills/opal-pilot-dev/references/pipeline.json` | 15행 |
| opds pipeline.json | `opal/skills/opal-pilot-dev-short/references/pipeline.json` | 10행 |
| opdw pipeline.json | `opal/skills/opal-pilot-dev-wireframe/references/pipeline.json` | 9행 (3~5행 conditional) |
