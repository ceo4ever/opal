# DONE: 명확화 게이트 — TASK 4요소 잠금 기계적 집행

> 완료일: 2026-06-16 18:11 | 스킬: opds (semi-agentic) | 태스크: 005 (재스코핑·재개)

## 1. 목표 달성

PRINCIPLES §1("Lock acceptance criteria before execution")이 prose 원칙으로만 존재하던 집행 공백을, state-tool 게이트로 **기계적으로 집행**한다. TASK.md "## 명확화 결과"에 4요소(목표/범위/제약/완료기준)가 잠기지 않으면 다음 단계(PLAN 등) 진입을 도구가 거부한다.

## 2. 변경 파일 (수정 4)

| 파일 | 변경 |
|------|------|
| `opal/tools/state-tool/state_tool.py` | `verify --clarification-check` 분기 + 헬퍼 3종(`_find_task_md`/`_parse_clarification_table`/`_check_clarification_gate`) + `_run_clarification_hook`(cmd_advance/cmd_mark TASK→다음단계 자동 훅) + ERROR_CODES `clarification_gate_unmet` |
| `opal/tools/state-tool/tests/test_state_tool.py` | `TestClarificationGate` 12 케이스 + ERROR_CODES 단언(30→31) |
| `opal/skills/op-task/SKILL.md` | STEP 4 템플릿에 "## 명확화 결과" 4요소 섹션 + 작성 체크리스트 1행 + 변경이력 v1.9 |
| `opal/core/references/opal-harness.md` | §1 Guards "명확화 게이트 (PRINCIPLES §1 집행)" 절 + 변경이력 v5.5 |

## 3. 핵심 설계 결정 (원안 005 재스코핑)

- **opp → opds 재라우팅** — state-tool 코드 변경은 동작검증 필요(self-confirming 위험), TEST 단계 보유 pilot 필요 (task 013 선례).
- **TASK 한 점 게이트 (캡틴 옵션1)** — 모호함 원점인 TASK 4요소를 기계 집행, 이후 단계는 PRINCIPLES §1 + AskUserQuestion에 위임. 원안의 6 SKILL 분산 의무화 대체.
- **하위호환 정책 A: graceful skip (캡틴 결정)** — "명확화 결과" 섹션 있는 TASK에만 발동, 부재 시 skip. 기존 태스크 회귀 0, 신규는 op-task 템플릿이 섹션 항상 생성하므로 100% 집행.
- **원안 흡수분 제거** — 소크라테스 인터뷰(AskUserQuestion이 대체), reporting-template 참조(삭제됨).
- **원칙 재서술 금지** — PRINCIPLES §1 문구 복제 없이 참조만(헌법 Governance).
- `--auto-pass` 우회 불가(close_gate 동형), `--force`만 긴급 탈출구.

## 4. 검증 결과

- RED-first: 신규 10 RED → 구현 후 **184 passed / 0 failed**(회귀 0), 테스트 불변.
- 배포본(install [1] 재배포) 실호출 3종 — ① 4요소 충족 `{ok:true,pass}` ② 완료기준 공란 `clarification_gate_unmet, missing:["완료기준"]` exit 1 ③ 기존 태스크(023) `skipped`(정책 A). 전부 설계대로.
- 4요소 라벨 코드(`_CLARIFICATION_ELEMENTS`)↔템플릿 일치, PRINCIPLES §1 재서술 0.
- dogfooding: 본 태스크 TASK.md가 "명확화 결과" 4요소를 직접 잠가 작성.

## 5. 적용 효과

- 신규 태스크: TASK 4요소 미잠금 시 PLAN 진입이 도구로 차단됨 (TASK 단계를 가진 opp/opd/opds/opdw 공통).
- 기존 태스크: 영향 없음(graceful skip).

## 6. 후속 후보

- ANALYSIS/PLAN 단계 델타 게이트 확장(원안 R-7) — 현재 보류(옵션1). 필요 시 별도 태스크.
- 커밋: 캡틴 지시 시 수행.
