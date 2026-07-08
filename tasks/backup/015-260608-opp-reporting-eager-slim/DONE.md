# DONE: 보고 형식 Eager 슬림화 + 헌법 문체 재작성

> 완료일: 2026-06-08 17:05 KST | 적용 스킬: opp | 모드: agentic | 태스크: 015

## 완료 산출물

| 구분 | 파일 | 핵심 변경 |
|------|------|----------|
| 수정 | `opal/core/AGENT.md` | §보고 형식 → 헌법 문체 인라인(골격·원칙·작동하는가, ~33줄) / Eager Step 6.6 제거 / 부트스트랩 완료 보고 `✅ reporting` 칼럼 제거 |
| 수정 | `opal/core/references/opal-harness-semi-agentic.md` | §10 단계 전환 보고 양식 3종 신설 (reporting-template §8 이전, 🎯 결론·근거 통합 골격) |
| 수정 | `opal/core/references/opal-harness.md` | §2 모듈 테이블 reporting-template 행 제거 |
| 수정 | `opal/core/references/opal-pm.md` | §8 탐색 경로 → AGENT.md §보고 형식 인라인 재지정 |
| 삭제 | `opal/core/references/harness/reporting-template.md` | 318줄/9KB — §1~7 인라인 / §8 이전 / §9 폐기로 전량 귀속 |

## 재설계된 보고 형식 (핵심 성과)

1. **결론·근거 통합** — 기존 2블록(🎯 결론 / 🔍 근거)을 `🎯 결론·근거` 1블록으로 통합, 항상 들여쓰기 불릿
2. **의사결정 = AskUserQuestion 도구** — 텍스트 `❓` 블록 폐지, 선택형 의사결정은 도구로 강제 (헌법 "Enforce with a tool, not prose" 구현)
3. **진행 = 승인 대기** — `▶️ ~ 승인(확인)해주시면 계속 진행하겠습니다`, 자동 진행 금지
4. **적용 범위** — 골격·도구는 PM(태스크)·PM(대화)·비서 전 모드, 승인 대기는 다음 액션이 있는 응답에만

## QA 결과

| 영역 | 결과 |
|------|------|
| R1 AGENT.md 인라인 (통합 골격/AskUserQuestion/승인대기/이모티/자율성) | ✅ Pass |
| R2 §8 → semi-agentic §10 이전 (양식 3종, 통합 골격 정합) | ✅ Pass |
| R3 reporting-template.md 삭제 | ✅ Pass |
| R4 참조 재지정 (AGENT.md/opal-harness.md/opal-pm.md 3곳 + interactive.md 무참조 확인) | ✅ Pass |
| R5 install 정합 (references/ 통째 clean+copy → 스크립트 무변경) | ✅ Pass |
| R6 변경이력 4문서 015 행 추가 | ✅ Pass |
| 일관성 (🔍 근거 단독 0건 / Eager 흐름 6.5→7 보존 / 칼럼 일관성) | ✅ Pass |

## 성과 지표

- **Eager 절감**: reporting-template.md 318줄/9KB 제거 → AGENT.md 인라인 ~33줄. **순감 약 285줄**
- 신규 파일 0개, 동작검증(코드 로직) 불변

## 범위 보정 (PLAN 조사 기반)

- TASK 가정 "참조 4곳 + install 수정" → 실측 "수정 3곳 + 삭제 1 + interactive.md·install 무변경" (grep 0건 근거)
- M-4-a "✅ reporting 칼럼 유지" → 캡틴 지적으로 "제거" 번복 (인라인 흡수로 독립 로드 단계 소멸)

## 잔여 미해결

- 없음

## 후속 태스크 후보

- **install 재실행** — 배포본(`~/.opal/`) 동기화 (현재 배포본은 구 reporting-template.md 잔존, install이 references/ 통째 clean+copy로 자동 purge)

## 추적

- AGENTIC-LOG.md — 게이트 판단·ERROR/FIX·의사결정 전 이력
