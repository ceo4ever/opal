# TASK: QA 에이전트 통합 — op-dev-qa-agent + op-task-qa-agent → opal-task-qa-agent

> 작성일: 2026-03-29 | 작업 유형: 개선
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

거의 동일한 구조의 op-dev-qa-agent와 op-task-qa-agent를 **opal-task-qa-agent** 하나로 통합하고, 오케스트레이터가 디스패치 시 `qa_skill` 파라미터로 사용할 QA 스킬을 지정하도록 변경한다.

## 배경

- 046 태스크에서 op-task-qa → op-dev-qa 리네이밍 + 범용 op-task-qa 신규 생성 완료
- op-dev-qa-agent와 op-task-qa-agent의 실질적 차이: 스킬 탐색 경로 1줄 + readonly 예외 1줄뿐
- 에이전트는 "스킬을 읽고 실행하는 워커"이므로, 어떤 QA 스킬을 사용할지를 디스패치 시 전달하면 1개로 충분
- 네이밍: `opal-task-qa-agent` — opal 프레임워크 레벨의 범용 QA 워커

## 요구사항

### R1. opal-task-qa-agent 신규 생성

- [ ] R1.1 `agents/opal-task-qa-agent/AGENT.md` 생성
- [ ] R1.2 디스패치 시 `qa_skill` 입력을 받아 해당 스킬을 탐색·실행하는 구조
- [ ] R1.3 model: light
- [ ] R1.4 readonly: true (기본), EXECUTE-UI 시 readonly: false (op-dev-qa의 기존 예외 유지)

### R2. 기존 QA 에이전트 삭제

- [ ] R2.1 `agents/op-dev-qa-agent/` 디렉토리 삭제
- [ ] R2.2 `agents/op-task-qa-agent/` 디렉토리 삭제

### R3. QA 스킬 실행 주체 변경

- [ ] R3.1 `skills/op-dev-qa/SKILL.md` — 실행 주체를 opal-task-qa-agent로 변경
- [ ] R3.2 `skills/op-task-qa/SKILL.md` — 실행 주체를 opal-task-qa-agent로 변경

### R4. 하네스 QA Gate 업데이트

- [ ] R4.1 `opal-harness.md` — QA 에이전트 컬럼을 단일 opal-task-qa-agent로 통합

### R5. 레지스트리 및 문서 업데이트

- [ ] R5.1 `agents.md` — op-dev-qa-agent + op-task-qa-agent → opal-task-qa-agent 통합
- [ ] R5.2 `CLAUDE.md` — 에이전트 트리 및 설명
- [ ] R5.3 `README.md` — 에이전트 테이블 및 구조 트리
- [ ] R5.4 `docs/ARCHITECTURE.md` — 에이전트 다이어그램/테이블 및 구조 트리
- [ ] R5.5 `docs/CONVENTIONS.md` — 필요 시 네이밍 예시

## 제약 조건

- QA 스킬(op-dev-qa, op-task-qa)은 변경하지 않음 (실행 주체 참조만 변경)
- 오케스트레이터 SKILL.md에서 QA 디스패치 시 qa_skill 파라미터를 포함해야 함
- install-mac.sh는 glob 기반이므로 소스 변경만으로 자동 반영

## 기술 스택

- Markdown (AGENT.md, SKILL.md, 문서)

## 관련 문서

- `agents/op-dev-qa-agent/AGENT.md` — 삭제 대상
- `agents/op-task-qa-agent/AGENT.md` — 삭제 대상
- `opal/core/references/opal-harness.md` — QA Gate 정의
- `opal/core/references/agents.md` — 에이전트 레지스트리
- `tasks/046-qa-skill-rename/` — 선행 태스크
