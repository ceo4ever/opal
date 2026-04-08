# DONE: 에이전트 아이콘 Observability + 메모리 브리핑 간소화

> 완료: 2026-04-09 11:10

## 완료 요약

Observability 선언에 에이전트별 아이콘 체계를 도입하고, 메모리 브리핑 절차를 간소화했다.

하네스 §5 행위 주체 표시를 `⚙️ 워커` 중심에서 `{icon} 에이전트` 중심으로 확장하여 QA·테스트·액션 등 비워커 에이전트 디스패치도 선언 대상에 포함되도록 했다. 각 에이전트 AGENT.md frontmatter에 `icon` 필드를 추가하여 아이콘 룩업이 가능해졌다. 메모리 브리핑에서 하위 파일을 선택적으로 Read하던 4단계를 삭제하여 MEMORY.md 인덱스만 읽도록 간소화했다.

## 변경 파일

| 파일 | 변경 내용 |
|------|----------|
| `opal/core/references/opal-harness.md` | §5 행위 주체 표시 — 아이콘 룩업 규칙 추가 + `{icon} 디스패치/완료` 형식으로 확장. 모든 Agent 디스패치 대상 명시 |
| `docs/CONVENTIONS.md` | YAML frontmatter 스키마에 `icon` 필드 추가 (에이전트 전용, 선택, 디폴트 ✨) |
| `agents/opal-task-agent/AGENT.md` | frontmatter에 `icon: "✨"` 추가 |
| `agents/opal-task-qa-agent/AGENT.md` | frontmatter에 `icon: "🔍"` 추가 |
| `agents/opal-task-action-agent/AGENT.md` | frontmatter에 `icon: "⚡"` 추가 |
| `agents/op-dev-test-agent/AGENT.md` | frontmatter에 `icon: "🧪"` 추가 |
| `agents/wtm-agent/AGENT.md` | frontmatter에 `icon: "🌐"` 추가 |
| `opal/core/AGENT.md` | 메모리 브리핑 절차 4단계 삭제 — 하위 파일 Read 제거, 5단계 → 4단계로 번호 조정 |

## 핵심 설계 결정

| # | 결정 | 근거 |
|---|------|------|
| 1 | 디폴트 아이콘 `✨` 채택 | `📋`(PM)과 시각적 구분 명확 + 범용성 |
| 2 | PM 직접 행위 표시(`📋 알투[PM] 직접:`) 현행 유지 | 아이콘 체계는 Agent 도구 디스패치에만 적용 |
| 3 | 메모리 브리핑 하위 파일 Read 삭제 | MEMORY.md 인덱스만으로 브리핑에 충분, 토큰 절약 |
