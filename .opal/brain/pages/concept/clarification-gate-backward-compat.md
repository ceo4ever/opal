---
type: concept
title: 명확화 게이트 하위호환 정책 A — graceful skip
tags: [pipeline, enforcement, backward-compat, state-tool]
sources: [task:005]
related: [clarification-gate, state-tool]
created: 2026-06-16
updated: 2026-06-16
status: active
---

## 개요

명확화 게이트가 기존 태스크(TASK.md에 "## 명확화 결과" 섹션 부재)에 미치는 영향을 제로로 만드는 하위호환 정책. 섹션이 없는 TASK.md는 검사를 건너뛰고 `{ok:true, clarification_check:"skipped"}` exit 0을 반환한다.

## 결정 배경 (WHY)

명확화 게이트 신설 시 기존 in-flight 태스크에 소급 적용할지 여부가 미확정 상태였다(`tasks/005-260616-opds-clarification-gate/PLAN.md:421`). 정책 B(강제 FAIL)는 기존 모든 진행 중 태스크의 다음 단계 진입을 일괄 차단해 회귀를 유발한다. 아래 세 가지 선례와의 정합으로 정책 A를 채택했다.

## 결정 내용

**정책 A: graceful skip** — "## 명확화 결과" 섹션이 있는 TASK.md에만 게이트가 발동한다.

- 섹션/파일 부재 → `{ok:true, clarification_check:"skipped", reason:"no '## 명확화 결과' section (backward-compat skip)"}` exit 0
- 섹션 존재 → 4요소 채움 여부 실제 검사 → PASS 또는 `clarification_gate_unmet`

**채택 근거:**
1. **verify 게이트 선례 정합**: state-tool의 모든 verify 게이트(mock/evidence/red)가 대상 산출물 부재 시 graceful skip을 채택한다 (`opal/tools/state-tool/state_tool.py:1480-1486`). 명확화 게이트만 강제하면 일관성이 깨진다.
2. **citation-rules §5 레거시 호환**: "이 규칙 도입 이전 산출물은 소급 변경하지 않는다. 신규 태스크부터 적용한다" (`opal/core/references/harness/citation-rules.md`). 정책 A와 직접 정합.
3. **신규 집행력 손실 없음**: op-task 템플릿(SKILL.md STEP 4)이 신규 TASK.md에 "## 명확화 결과" 섹션을 항상 생성하므로, 신규 태스크는 정책 A에서도 100% 게이트 적용. graceful skip은 구 산출물 전용 안전망.

## 영향 범위

- 기존 태스크: 회귀 영향 0 (섹션 부재 시 skip)
- 신규 태스크: 100% 집행 (op-task 템플릿이 섹션 자동 생성)
- `opal/tools/state-tool/state_tool.py` — `_check_clarification_gate()` None 반환 시 skip 처리, `_run_clarification_hook()` 섹션 부재 → return

## 관련 페이지

- [[clarification-gate]]
- [[state-tool]]
