# DONE: 워커 에이전트 프로젝트 컨텍스트 자율 로딩

> 완료일: 2026-03-30

## 변경 요약

3개 워커 에이전트의 실행 프로세스에 "프로젝트 컨텍스트 로드" 단계를 추가하여, 워커가 스킬 유형에 따라 docs/ 문서를 자율적으로 읽도록 개선했다.

## 변경 파일

| 파일 | 변경 내용 |
|------|----------|
| `agents/opal-task-agent/AGENT.md` | Step 3 추가 (6→7단계). 스킬 접두사(op-dev-*/op-task-*)로 로딩 문서 자동 판단 |
| `agents/opal-task-qa-agent/AGENT.md` | Step 3 추가 (5→6단계). qa_skill 유형(op-dev-qa/op-task-qa)으로 판단 |
| `agents/op-dev-test-agent/AGENT.md` | Step 3 추가 (8→9단계). 코드 테스트 에이전트이므로 항상 코드 관련 문서 로드 |

## 배포 동기화

`~/.opal/agents/` 배포본에 3개 파일 모두 복사 완료.
