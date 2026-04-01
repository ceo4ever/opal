# DONE: QA 에이전트 통합 — opal-task-qa-agent

> 완료일: 2026-03-29

## 요약

op-dev-qa-agent + op-task-qa-agent를 **opal-task-qa-agent** 하나로 통합. 디스패치 시 `qa_skill` 파라미터로 QA 스킬을 동적 선택.

## 변경 파일

### 신규 생성
| 파일 | 역할 |
|------|------|
| `agents/opal-task-qa-agent/AGENT.md` | 통합 QA 에이전트 — qa_skill로 스킬 동적 실행 |

### 수정
| 파일 | 변경 내용 |
|------|----------|
| `skills/op-dev-qa/SKILL.md` | 실행 주체 → opal-task-qa-agent |
| `skills/op-task-qa/SKILL.md` | 실행 주체 → opal-task-qa-agent |
| `opal/core/references/opal-harness.md` | QA Gate 에이전트 단일화 + qa_skill 컬럼 |
| `opal/core/references/agents.md` | 2개 항목 → opal-task-qa-agent 1개 |
| `CLAUDE.md` | 에이전트 트리/설명 |
| `README.md` | 에이전트 테이블/구조 트리 |
| `docs/ARCHITECTURE.md` | 다이어그램/테이블/구조 트리 |
| `docs/CONVENTIONS.md` | 네이밍 예시 |

### 삭제
| 파일 | 사유 |
|------|------|
| `agents/op-dev-qa-agent/AGENT.md` | opal-task-qa-agent로 통합 |
| `agents/op-task-qa-agent/AGENT.md` | opal-task-qa-agent로 통합 |

## 핵심 설계 결정

1. qa_skill 파라미터로 QA 스킬 동적 선택 → 에이전트 1개로 dev/범용 QA 모두 커버
2. 오케스트레이터 변경 불필요 — 스킬명 참조이므로 에이전트 통합에 무관
3. 에이전트 총 수: 5개 → 4개 (opal-task-agent, opal-task-qa-agent, op-dev-test-agent, wtm-agent)
