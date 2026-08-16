---
type: concept
title: state-tool import-existing key 재접합
tags:
- state-tool
- import
- key-address
- task-074
sources:
- task:074
- task:094
related:
- state-tool
- state-tool-task-step-key-address
- pipeline-json-spec
- state-md-journal-redefinition
created: '2026-07-23'
updated: '2026-08-16'
status: stale
---
## 이후 갱신 (task:094 — 기능 자체 제거)

**이 결정이 다루는 기능(`--import-existing`)은 task:094에서 완전히 제거됐다.** STATE.md가 파생 표 없는 저널로 재정의되면서(D-1, R-1) `parse_existing_state_md`의 파싱 원천(렌더 표)이 소멸했고, 이 페이지가 기록한 key 재접합 로직(`_key_source_index`·`_reattach_import_keys`)도 함께 삭제됐다. `cmd_init`은 이제 `--import-existing` 지정 시 항상 `import_existing_removed`로 거부한다(exit 1). argparse 인자는 `help=argparse.SUPPRESS`로만 존치한다(삭제 시 비-JSON exit 2가 stdout 계약을 깨기 때문 — task:094 D-2 근거 ③). 신규 태스크는 전량 `init --rows-from pipeline.json` 경로다.

아래 원 결정 기록은 **역사적 참고**로만 남긴다 — "렌더용 표는 원본 데이터의 lossy projection"이라는 교훈 자체는 여전히 유효하다(상세: [[state-md-journal-redefinition]]).

## 개념 요약 (역사적 기록 — task:074 원 결정)

`state-tool init --import-existing`의 기존 task-step key 복구 원천을 STATE.md 렌더 표에서 권위 원천(state.json/pipeline.json)으로 전환하는 설계다. 렌더 표는 key 컬럼이 없는 lossy projection이므로, keyless import 행에 원천의 key를 (stage,item) 순서 소비로 재접합해야 한다.

## 배경·문제 (WHY)

- `cmd_init`의 import 분기가 rows를 STATE.md 마크다운 표에서 파싱(`parse_existing_state_md`)한다 — 표 컬럼은 `| # | 단계 | 항목 | 상태 | 시점 |`뿐으로 070이 도입한 key가 렌더되지 않는다(근거: task:074 PLAN §2.2, `opal/tools/state-tool/state_tool.py:271`, `:819-851`).
- 결과 keyless rows를 `--force`가 기존 state.json(key 보유)에 덮어써 schema_version이 "1.1"→"1.0"으로 강등되고 `--task-step`/`--task-step-id` 주소가 전면 불능이 되었다(근거: task:074 TASK.md 배경 분석).
- key는 `{stage_slug}.{item_slug}` 형식으로 stage에 결속되므로 (stage,item)이 자연 조인축이다. row_id는 파싱 시 순번 재부여(및 add-row 시 재번호)되어 위치 변동적이라 신뢰할 수 없다(근거: task:074 PLAN DEC-1).
- **교훈**: 렌더용 마크다운 표는 항상 원본 데이터의 lossy projection일 수 있다 — 복구·재구성 로직의 원천을 표에 두면 표에 없는 필드가 조용히 유실된다. 권위 원천(구조화 데이터)에서 재접합하는 경로를 별도로 확보해야 한다.

## 결정 내용 (HOW)

- 매칭축은 (stage,item) 순서 소비(ordered consumption)로 채택 — 원천 rows에서 (stage,item)→[key,...] 순서 큐를 구성하고, keyless import 행을 순서대로 순회하며 동일 (stage,item) 큐에서 앞에서부터 pop해 부여한다(DEC-1). 매칭 안 되는 행은 keyless로 남기는 best-effort 복구이며 오류로 중단하지 않는다.
- 우선순위: (1) 기존 state.json soft-load(덮어쓰기 이전, DEC-4) → (2) 재접합 후에도 keyless가 남고 `--rows-from *.json`이 동반된 경우만 pipeline.json 폴백(DEC-2) → (3) 원천 전무 시 keyless 유지 + stderr 경고 1줄, stdout 불변(DEC-5, 하위호환).
- schema_version 승격 로직(`any(key)` 계산, `state_tool.py:932`) 자체는 무변경 — 재접합을 그 계산 이전에 배치해 key 보존 시 자동으로 "1.1"이 stamp되도록 했다(DEC-3).
- 신규 헬퍼 `_key_source_index`(원천 rows → (stage,item) 순서 큐)·`_reattach_import_keys`(keyless 행에 순서 소비로 key 재접합, 이미 key 있는 행은 skip해 체이닝 안전)를 `cmd_init` import 분기(`state_tool.py:908` 직후)에 삽입했다.

## 영향·관계

- `opal/tools/state-tool/state_tool.py` — `cmd_init` import 분기에 재접합 블록 삽입, 신규 헬퍼 2종 추가. line 932(schema 승격)·line 957(`save_state_json`) 자체는 무변경.
- state.json `rows[].key` — 070이 도입한 `--task-step` 주소 SSOT. 이번 결정으로 `--import-existing --force` 경로에서도 보존이 보장된다.
- [[state-tool-task-step-key-address]] — 이번 결정이 보완하는 070의 key 주소 체계 원설계.
- [[pipeline-json-spec]] — DEC-2 폴백 원천.
- [[state-tool]] — 이 결정을 구현하는 도구.

## 근거 출처

- task:074 — state-tool `--import-existing` task-step key 유실 결함 수정 (TASK.md 배경 분석, PLAN.md DEC-1~DEC-5)
