# QA: PLAN — Antigravity 플랫폼 지원 추가 및 QA 호출 구조 개선

> 검토일: 2026-03-07 | 판정: ⚠️ Needs Revision → ✅ Pass (지적 사항 반영 완료)

## 1. 요약

PLAN은 3개 트랙(A: Antigravity, B: Cursor, C: QA 개선)을 19개 신규 + 8개 수정 + 3개 삭제 파일로 분해하고, 의존성 기반 9단계 구현 순서를 제시한다. 핵심 설계는 before/after 예시를 포함하여 대부분 즉시 구현 가능한 수준이며, RESEARCH의 발견 사항과 리스크가 충실히 반영되어 있다. 그러나 **cursor/skills/ 미러 디렉토리의 동기화 전략이 누락**되어 있어, Cursor 환경에서 QA 호출 개선(C 트랙)과 Antigravity 탐색 경로(A-5)가 반영되지 않는 문제가 발생한다. 테스트 전략도 일부 성공 기준에 대한 커버리지가 부족하다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| P-1 | 즉시 구현 가능성 | ⚠️ Warning | 대부분 구체적이나 M-7(CLAUDE.md), M-8(README.md) 수정이 영역 수준 기술에 그침 |
| P-2 | 의존성 순서 정합 | ✅ Pass | 소스 원본 → Cursor → Antigravity → 템플릿 → 문서 순서 적절 |
| P-3 | RESEARCH 반영 | ✅ Pass | 5개 핵심 발견 + 4개 리스크 모두 PLAN에 반영됨 |
| P-4 | 파일 목록 일치 | ⚠️ Warning | RESEARCH 파일은 모두 포함되나, cursor/skills/ 미러 수정이 RESEARCH와 PLAN 양쪽에서 누락 |
| P-5 | 핵심 설계 구체성 | ✅ Pass | M-1~M-6, N-1~N-14에 before/after 및 변환 규칙 명시. M-7~M-8은 보통 수준 |
| P-6 | 테스트 전략 커버리지 | ⚠️ Warning | TASK 성공 기준 6개 중 3개(#1 부분, #3, #6)에 대한 명시적 테스트 없음 |

## 3. 지적 사항

### 3.1 [Warning] cursor/skills/ 미러 동기화 전략 누락

**현상**: PLAN은 `claude/skills/task-flow/SKILL.md`(M-1)와 `claude/skills/task-flow/references/*.md`(M-2~M-5)를 수정하지만, 실제 존재하는 `cursor/skills/task-flow/SKILL.md` 및 `cursor/skills/task-flow/references/*.md`에 대한 수정은 파일 목록에 포함되어 있지 않다.

**영향**: Cursor 환경에서 task-flow를 사용할 경우:
- QA 호출 강조 블록(C-3)이 반영되지 않음
- 레퍼런스 가이드의 QA 호출 단계(C-1)가 추가되지 않음
- Antigravity 에이전트 탐색 경로(A-5)가 없음

**확인된 파일 목록** (실제 존재하는 cursor/ 미러):
```
cursor/skills/task-flow/SKILL.md
cursor/skills/task-flow/references/research-guide.md
cursor/skills/task-flow/references/plan-guide.md
cursor/skills/task-flow/references/todo-guide.md
cursor/skills/task-flow/references/execute-guide.md
cursor/skills/task-flow/references/execute-plan-guide.md
cursor/skills/api-analyzer/SKILL.md
cursor/skills/doc-writer/SKILL.md
cursor/skills/interview/SKILL.md
cursor/skills/version-mgr/SKILL.md
cursor/skills/wireframe-builder/SKILL.md
```

**권장 조치**: 다음 중 하나를 PLAN에 추가:
- (a) M-1~M-5 수정 사항을 cursor/ 미러에도 동일 적용하는 수정 파일 추가 (M-9~M-13)
- (b) 구현 순서 마지막에 "cursor/skills/를 claude/skills/에서 재복사" 단계를 추가하고, 테스트 T-5에서 검증

### 3.2 [Warning] 테스트 전략 커버리지 부족

TASK 성공 기준과 테스트 항목의 매핑:

| 성공 기준 | 테스트 커버 |
|----------|-----------|
| #1 Antigravity 스킬 정상 인식 | T-1 (YAML), T-2 (경로) — 부분 커버 |
| #2 프로젝트 룰 로딩 | 미커버 (GEMINI.md 템플릿 유효성 검증 없음) |
| #3 알투 Antigravity 동작 | 미커버 (gemini-snippet.md 페르소나 동일성 검증 없음) |
| #4 QA 호출 누락 방지 | T-3 ✓ |
| #5 Cursor 플랫 파일 인식 | T-4 ✓ |
| #6 Claude Code 무영향 | 미커버 (명시적 하위 호환 테스트 없음) |

**권장 조치**: 다음 테스트 추가
- T-7: `templates/GEMINI.md`가 CLAUDE.md 템플릿의 필수 섹션을 모두 포함하는지 확인
- T-8: `templates/r2/gemini-snippet.md`가 `claude-snippet.md`의 알투 페르소나 핵심 요소를 모두 포함하는지 확인
- T-9: `claude/agents/` 디렉토리 구조가 변경되지 않았는지 확인 (task-flow-qa/AGENT.md 내용 수정만, 구조는 그대로)

### 3.3 [Minor] M-7, M-8 설계 구체성 보통

CLAUDE.md(M-7)와 README.md(M-8)의 수정 사항이 "수정 영역" 목록 수준으로만 기술되어 있다. 예를 들어 M-7의 "소스 구조에 antigravity/ 추가"는 어떤 형태의 텍스트를 어디에 넣는지가 명시되지 않았다. 이 두 파일은 프로젝트의 핵심 문서이므로, 구현자에 따라 결과물의 편차가 발생할 수 있다.

**권장 조치**: M-7과 M-8에 대해 최소한 추가/수정할 섹션의 대략적 내용이나 구조 스케치를 포함하면 구현 품질이 일관된다.

### 3.4 [Minor] T-5 범위와 실행 가능성

T-5는 "claude <-> cursor <-> antigravity 스킬 내용이 3-플랫폼 동일한지 diff 비교"라고 정의했으나, cursor/skills/가 PLAN의 수정 대상에 포함되어 있지 않아 diff 비교 시 불일치가 발생할 수밖에 없다. 3.1의 cursor 미러 전략이 확정되어야 T-5도 유의미해진다.

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK A-1 | Antigravity Skills 6개 모두 PLAN 파일 목록에 포함 | ✅ Pass — N-1, N-7~N-11 |
| TASK A-2 | Antigravity 에이전트 적용 방안 | ✅ Pass — N-12~N-14 (Skills 변환, RESEARCH 권장안 A 채택) |
| TASK A-3 | GEMINI.md 템플릿 | ✅ Pass — N-18 |
| TASK A-4 | 알투 Antigravity 설정 | ✅ Pass — N-19 |
| TASK A-5 | 에이전트 탐색 경로 Antigravity 추가 | ✅ Pass — M-1 (claude), N-1 (antigravity) |
| TASK A-6 | 프로젝트 문서 업데이트 | ✅ Pass — M-7, M-8 |
| TASK B-0 | Cursor 플랫 파일 전환 | ✅ Pass — D-1~D-3, N-15~N-17. 탐색 경로도 M-1에 반영 |
| TASK C-1 | 레퍼런스 가이드 QA 호출 추가 | ⚠️ Warning — M-2~M-5는 claude/ 버전만. cursor/ 미러 미반영 |
| TASK C-2 | AGENT.md "자동 호출" 수정 | ✅ Pass — M-6. Cursor 버전도 N-15에서 반영 언급 |
| TASK C-3 | SKILL.md QA 호출 서브섹션 | ⚠️ Warning — M-1은 claude/ 버전만. cursor/ 미러 미반영 |
| TASK 제약: 하위 호환 | 기존 환경 영향 없음 | ✅ Pass — claude/agents/ 구조 유지, 추가/강화만 수행 |
| TASK 제약: 포맷 호환 | Antigravity 실제 설정 체계 부합 | ✅ Pass — RESEARCH 검증 결과와 일치 |
| TASK 제약: 소스 원본 유지 | claude/가 원본 역할 유지 | ✅ Pass — 모든 수정이 claude/ 기준, antigravity는 파생 |
| RESEARCH 발견 1 | Skills 3-플랫폼 공통 포맷 | ✅ Pass — SKILL.md 포맷 유지 |
| RESEARCH 발견 2 | 에이전트→Skills 변환 | ✅ Pass — 섹션 3.5에 변환 규칙 명시 |
| RESEARCH 발견 3 | Cursor 플랫 파일 | ✅ Pass — 섹션 3.2에 명시 |
| RESEARCH 발견 4 | GEMINI.md 단일 파일 패턴 | ✅ Pass — CLAUDE.md 기반 작성, .agent/rules/ 미사용 |
| RESEARCH 발견 5 | QA 호출 구조적 원인 | ✅ Pass — 가이드 + SKILL.md + AGENT.md 3중 보강 |
| RESEARCH 리스크 1~4 | 리스크 대응 방안 | ✅ Pass — PLAN 섹션 6에 모두 반영 |

## 5. 판정

**⚠️ Needs Revision**

PLAN의 전체적인 품질은 우수하며, TASK 요구사항 10개 중 8개를 완전히 커버하고 RESEARCH 발견/리스크를 충실히 반영한다. 구현 순서의 의존성 정합과 핵심 설계의 구체성도 양호하다.

그러나 다음 보완이 필요하다:

1. **[필수] cursor/skills/ 미러 동기화 전략 추가** (3.1항) — C-1, C-3 요구사항이 Cursor 환경에서 미반영되는 문제. 파일 목록에 cursor/skills/task-flow/ 관련 수정을 추가하거나, 재복사 전략을 명시해야 한다.
2. **[권장] 테스트 항목 보강** (3.2항) — GEMINI.md 유효성, R2 페르소나 동일성, Claude Code 하위 호환 테스트 추가.
3. **[선택] M-7, M-8 구체성 보강** (3.3항) — 문서 수정 결과물의 편차를 줄이기 위해 내용 스케치 추가.

필수 보완(1번)만 해결하면 Pass로 전환할 수 있다.
