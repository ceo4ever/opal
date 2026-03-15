# TASK: task-flow STATE.md 체크포인트 시스템 추가

> 작성일: 2026-03-15 | 작업 유형: 기능 개선

## 작업 목표
task-flow 스킬에 태스크별 STATE.md 체크포인트 시스템을 추가하여, LLM 토큰 리밋으로 컨텍스트가 유실되어도 정확한 위치에서 작업을 재개할 수 있도록 한다.

## 배경
task-flow로 작업 중 LLM 토큰 리밋에 도달하면 대화 컨텍스트가 압축/유실된다. 현재 "이어하기" 기능은 산출물 파일 존재 여부로 마지막 완료 단계를 추론하지만, 다음 정보가 유실된다:
- 진행 중인 단계의 중간 상태 (EXECUTE Step 3/7 완료 등)
- 대화 중 내린 의사결정 (산출물 반영 전)
- 워커 에이전트 ID (resume 불가)
- 사용자 피드백/수정 지시 (반영 전)
- 활성 태스크 식별 (다중 태스크 시)

## 요구사항
- [ ] 각 태스크 폴더에 STATE.md 파일을 두고 실시간 상태를 추적
- [ ] 단계 시작/완료, Step 진행, 의사결정, 블로커 발생 시 STATE.md 자동 갱신
- [ ] 새 세션 시작 시 STATE.md를 읽어 자동 복원 프로토콜 제공
- [ ] task-flow SKILL.md에 STATE.md 갱신/복원 규칙 통합
- [ ] 워커 에이전트(task-flow-agent)에 STATE.md 갱신 규칙 전달
- [ ] 기존 "이어하기" 기능을 STATE.md 기반으로 고도화
- [ ] DONE.md 생성 시 STATE.md를 "완료" 상태로 갱신

## 제약 조건
- 기존 task-flow 워크플로우의 호환성 유지 (STATE.md는 추가 기능)
- STATE.md 갱신 오버헤드 최소화 (Edit 한 번 수준)
- 크로스 플랫폼 호환 (Claude Code, Cursor, Gemini CLI, Antigravity)
- 산출물 저장 구조에 STATE.md 추가 반영

## 관련 문서
- skills/task-flow/SKILL.md — 메인 스킬 정의
- skills/task-flow/references/execute-guide.md — 실행 가이드
- agents/claude/task-flow-agent/AGENT.md — 워커 에이전트
- CLAUDE.md — 프로젝트 컨벤션
