---
type: concept
title: 명확화 게이트 — TASK 4요소 잠금 기계 집행
tags: [pipeline, enforcement, state-tool, clarification]
sources: [task:005]
related: [[state-tool]]
created: 2026-06-16
updated: 2026-06-16
status: active
---

## 개요

OPAL PRINCIPLES §1("Lock acceptance criteria before execution")을 prose 원칙에서 도구 집행으로 전환한 장치. state-tool `verify --clarification-check`가 TASK.md "## 명확화 결과" 섹션의 4요소(목표/범위/제약/완료기준) 잠금 여부를 검사하며, 미충족 시 다음 단계(PLAN 등) 진입을 거부한다.

## 결정 배경 (WHY)

PRINCIPLES §1은 "실행 전 수락 기준을 잠가라"고 명시하나, 실제 집행 장치가 없어 prose 원칙으로만 존재했다. 헌법 Core Stance("Enforce, don't just advise: if a rule must always hold, a tool gates it — not prose")에 따라 코드+테스트로 집행을 구현했다. 원안(opp 스코프, 6 SKILL 분산 의무화)을 현 아키텍처(opds, state-tool 단일 집행점)로 재스코핑한 결과다 (`tasks/005-260616-opds-clarification-gate/DONE.md:20-25`).

## 결정 내용

- **집행 지점**: `state_tool.py` — `_check_clarification_gate()` 헬퍼 + `cmd_verify`의 `--clarification-check` 분기 + `cmd_mark`/`cmd_advance` 자동 훅 (`opal/tools/state-tool/state_tool.py`)
- **자동 훅**: TASK 단계 완료 후 다음 단계 첫 행 진입 시(mark/advance 양쪽) 자동 발동. 별도 수동 호출 불필요.
- **거부 코드**: ERROR_CODES `clarification_gate_unmet` — `{ok:false, error:"clarification_gate_unmet", missing:[...]}` exit 1
- **우회 정책**: `--auto-pass` 우회 불가(agentic 모드도 동일), `--force`만 긴급 탈출구 (close_gate 동형)
- **집행 범위**: TASK 단계를 보유한 파이프라인(opp/opd/opds/opdw 등) 공통 적용

## 영향 범위

- `opal/tools/state-tool/state_tool.py` — 헬퍼 3종 신설, ERROR_CODES 1행, cmd_verify 분기, argparse 플래그, 자동 훅
- `opal/tools/state-tool/tests/test_state_tool.py` — TestClarificationGate 12케이스 (184 passed/0 failed)
- `opal/skills/op-task/SKILL.md` — STEP 4 템플릿에 "## 명확화 결과" 4요소 섹션 추가 (v1.9)
- `opal/core/references/opal-harness.md` — §1 Guards "명확화 게이트" 절 추가 (v5.5)

## 관련 페이지

- [[state-tool]]
- [[clarification-gate-backward-compat]]
- [[opal-principles-constitution]]
