# DONE: op-task-qa → op-dev-qa 리네이밍 + 범용 op-task-qa 신규

> 완료일: 2026-03-29

## 요약

기존 코드 개발 특화 op-task-qa를 op-dev-qa로 리네이밍하고, 도메인 무관한 범용 op-task-qa를 신규 생성하여 QA 체계를 dev/범용으로 분리 완료.

## 변경 파일

### 신규 생성
| 파일 | 역할 |
|------|------|
| `skills/op-dev-qa/SKILL.md` | Dev QA 스킬 (기존 op-task-qa 리네이밍) |
| `skills/op-dev-qa/references/qa-dev-guide.md` | Dev QA 가이드 (기존 유지) |
| `skills/op-dev-qa/references/qa-wireframe-guide.md` | Wireframe QA 가이드 (기존 유지) |
| `skills/op-dev-qa/personas/qa-engineer.md` | QA 페르소나 (기존 유지) |
| `agents/op-dev-qa-agent/AGENT.md` | Dev QA 에이전트 (기존 op-task-qa-agent 리네이밍) |
| `skills/op-task-qa/SKILL.md` | 범용 QA 스킬 (신규) |
| `skills/op-task-qa/references/qa-general-guide.md` | 범용 QA 가이드 (신규) |
| `skills/op-task-qa/personas/qa-engineer.md` | 범용 QA 페르소나 (신규) |
| `agents/op-task-qa-agent/AGENT.md` | 범용 QA 에이전트 (신규) |

### 수정
| 파일 | 변경 내용 |
|------|----------|
| `opal/core/references/opal-harness.md` | QA Gate dev/범용 분기 테이블 |
| `opal/core/references/opal-skills-registry.json` | op-dev-qa 추가, op-task-qa 범용화 |
| `opal/core/references/agents.md` | op-dev-qa-agent 추가, op-task-qa-agent 범용화 |
| `skills/opal-pilot-dev-wireframe/SKILL.md` | op-dev-qa 참조 |
| `skills/opal-pilot-dev/SKILL.md` | op-dev-qa 명시 |
| `skills/opal-pilot-dev-short/SKILL.md` | op-dev-qa 명시 |
| `skills/opal-pilot-write/SKILL.md` | op-task-qa(범용) 확인 |
| `skills/opal-project-pilot/SKILL.md` | op-task-qa 명시 |
| `CLAUDE.md` | 구조 트리 + 컴포넌트 설명 |
| `README.md` | 스킬/에이전트 테이블 + 구조 트리 |
| `docs/ARCHITECTURE.md` | 아키텍처 다이어그램 + 테이블 |
| `docs/CONVENTIONS.md` | 네이밍 예시 |

## 핵심 설계 결정

1. **방안 B**: 하네스는 분기 테이블만 정의, 각 오케스트레이터가 QA 스킬명을 직접 명시
2. **install-mac.sh 무변경**: glob 기반 배포로 소스 리네이밍만으로 자동 반영
3. **opal-pilot-write-tech 무변경**: 자체 QA(consistency-rules.md) 사용
