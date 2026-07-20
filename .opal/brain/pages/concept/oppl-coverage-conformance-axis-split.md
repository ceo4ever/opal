---
type: concept
title: 커버리지·conformance 판정의 축별 분리 — backlog-tool/test-tool 외부 집계
tags:
- oppl
- coverage
- conformance
- ssot
- tool-gated
sources:
- task:069
related:
- oppl-surface-inventory-contract
- oppl-evidence-fidelity-principle
- oppl-3-ssot-tool-gated-separation
created: '2026-07-19'
updated: '2026-07-19'
status: active
---
## 개념 요약

계약 표면(surface) 대비 "누가 커버하는가"(R-3, 태스크 축)와 "실제로 검증됐는가"(R-4, 결과 축)를 [[oppl-3-ssot-tool-gated-separation]]의 축 분리 정신을 유지한 채 서로 다른 SSOT 소유 도구에 배치한다. 종료 판정(L✓)은 PM(오케스트레이터)이 각 도구의 개별 거부 결과를 불리언 AND로 조합한다.

## 결정 배경 (WHY)

실전 사고에서 done-check가 태스크 축(all_done)만 판정해 "계약 전 표면이 어느 태스크에서 검증되는가"를 아무도 보지 못했고, 크로스스택 동형성 테스트가 표본(3개 표면)만 검사하고 "크로스스택 OK"라는 잘못된 확신을 만들었다. 이를 봉쇄하려면 표면 축 판정이 필요하지만, 3-SSOT 축 분리 원칙("각 도구는 자기 SSOT만 소유")을 깨지 않아야 한다.

## 결정 내용 (HOW)

- **R-3 커버리지 게이트 → backlog-tool `coverage-check`**: backlog.json(자기 SSOT) + surfaces.json(CONTRACT 도메인, 읽기 전용)만 읽는다. `surface_uncovered`/`integration_task_missing` 거부. test-scenario.json은 미접촉 — 축 분리 유지.
- **R-4 conformance 전수 판정 → test-tool `scenario-conformance`**: surfaces.json(분모, 읽기 전용) + 자기 test-scenario.json(result존)만 읽는다. backlog.json은 미접촉. `all_surfaces_green`/`surface_unverified` 거부.
- **L✓ 종료 판정 = PM 불리언 AND**: PM이 `done-check.all_done`(태스크 축) ∧ `scenario-conformance.all_surfaces_green`(표면 축) ∧ 회귀 0을 조합한다. 각 조건은 개별 도구 거부로 tool-gated이며, PM의 불리언 AND는 기존 "done-check + 회귀 0" 판정과 동일한 정당한 오케스트레이터 제어흐름(loop-control.md §5)이다. 어느 도구도 타 도구의 SSOT를 직접 파싱하지 않는다.
- **backlog-tool covers 필드**: `add-task`/`update-task --covers '["surface-id",...]'` — 태스크가 커버하는 표면 id 배열. 미지정 시 `[]`(하위 호환). BACKLOG.md 미러에 "커버 표면" 컬럼으로 렌더된다.

## 영향 범위

- `opal/tools/backlog-tool/backlog_tool.py` — `--covers` 필드, `coverage-check` 서브명령, 에러 4종(covers_invalid_json·surface_uncovered·integration_task_missing·surfaces_file_not_found)
- `opal/tools/backlog-tool/schema/backlog.schema.json` — covers optional 필드, schema_version 1.0→1.1(신규 init만 적용, 기존 파일 무파손)
- `opal/skills/opal-pilot-project-loop/SKILL.md` D7 coverage-check 게이트, L✓ 3중 불리언 AND(done-check ∧ conformance ∧ 회귀 0) + 여정 스모크

## 관련 페이지

- [[oppl-surface-inventory-contract]]
- [[oppl-evidence-fidelity-principle]]
- [[oppl-3-ssot-tool-gated-separation]]
