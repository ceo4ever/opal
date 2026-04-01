# TASK: op-task-qa → op-dev-qa 리네이밍 + 범용 op-task-qa 신규

> 작성일: 2026-03-29 | 작업 유형: 개선
> 입력: 사용자 요청 + 메모리(project_qa_skill_rename.md)
> 출력: TASK.md

## 작업 목표

현재 코드 개발 특화된 op-task-qa를 op-dev-qa로 리네이밍하고, 도메인 무관한 범용 op-task-qa를 신규 생성하여 QA 체계를 dev/범용으로 분리한다.

## 배경

- 045 태스크에서 opal-project-pilot(opp) 도입 시, PLAN 후 QA Gate에 범용 QA가 필요함을 확인
- 현재 op-task-qa는 qa-dev-guide.md(ANALYSIS/PLAN), qa-wireframe-guide.md(WIREFRAME/EXECUTE-UI)로 **코드 개발 도메인에 특화**됨
- opal-project-pilot이 사용하는 범용 태스크(스킬 작성, 설정 변경, 워크플로우 등)에는 부적합
- 네이밍 체계상 `op-dev-*`은 dev 도메인, `op-task-*`은 범용이므로 현재 이름이 역할과 불일치

## 요구사항

### R1. op-task-qa → op-dev-qa 리네이밍

- [ ] R1.1 `skills/op-task-qa/` → `skills/op-dev-qa/`로 디렉토리 리네이밍
- [ ] R1.2 SKILL.md frontmatter name을 `op-dev-qa`로 변경
- [ ] R1.3 SKILL.md 내부 자기 참조 경로 변경
- [ ] R1.4 references/(qa-dev-guide.md, qa-wireframe-guide.md), personas/qa-engineer.md 유지 (내용 변경 불필요)

### R2. op-task-qa-agent → op-dev-qa-agent 리네이밍

- [ ] R2.1 `agents/op-task-qa-agent/` → `agents/op-dev-qa-agent/`로 디렉토리 리네이밍
- [ ] R2.2 AGENT.md frontmatter name을 `op-dev-qa-agent`로 변경
- [ ] R2.3 AGENT.md 내부 스킬 탐색 경로를 op-dev-qa로 변경

### R3. 범용 op-task-qa 신규 생성

- [ ] R3.1 `skills/op-task-qa/SKILL.md` 신규 생성 — 도메인 무관 QA 검증
- [ ] R3.2 `references/qa-general-guide.md` 작성 — 범용 산출물 검증 체크리스트
- [ ] R3.3 `personas/qa-engineer.md` — 기존과 동일 페르소나 재사용 또는 범용화
- [ ] R3.4 검증 대상: TASK.md, PLAN.md 등 범용 산출물 (코드 관련 항목 제외)

### R4. 범용 op-task-qa-agent 신규 생성

- [ ] R4.1 `agents/op-task-qa-agent/AGENT.md` 신규 생성
- [ ] R4.2 op-task-qa 스킬을 실행하는 범용 QA 에이전트

### R5. 참조 업데이트 (기존 오케스트레이터/하네스)

- [ ] R5.1 `opal-harness.md` — QA Gate 탐색 경로를 분기 로직으로 변경 (dev 오케스트레이터 → op-dev-qa, 범용 오케스트레이터 → op-task-qa)
- [ ] R5.2 `opal-pilot-dev-short/SKILL.md` — op-dev-qa로 변경
- [ ] R5.3 `opal-pilot-dev/SKILL.md` — op-dev-qa로 변경
- [ ] R5.4 `opal-pilot-dev-wireframe/SKILL.md` — op-dev-qa로 변경
- [ ] R5.5 `opal-pilot-write/SKILL.md` — QA 호출부 확인 및 적절한 QA 스킬로 변경
- [ ] R5.6 `opal-pilot-write-tech/SKILL.md` — QA 호출부 확인 및 적절한 QA 스킬로 변경
- [ ] R5.7 `opal-project-pilot/SKILL.md` — op-task-qa(범용) 유지 확인

### R6. 레지스트리 및 문서 업데이트

- [ ] R6.1 `opal-skills-registry.json` — op-dev-qa 추가, op-task-qa를 범용으로 변경
- [ ] R6.2 `agents.md` — op-dev-qa-agent 추가, op-task-qa-agent를 범용으로 변경
- [ ] R6.3 `skills.md` — 스킬 목록 반영
- [ ] R6.4 `CLAUDE.md` — 소스 구조 트리 업데이트
- [ ] R6.5 `README.md` — 컴포넌트 테이블 업데이트
- [ ] R6.6 `docs/ARCHITECTURE.md` — 아키텍처 문서 업데이트
- [ ] R6.7 `docs/CONVENTIONS.md` — 네이밍 예시 업데이트

### R7. install-mac.sh 배포 동기화

- [ ] R7.1 install-mac.sh에서 op-dev-qa 스킬/에이전트 배포 경로 추가
- [ ] R7.2 기존 op-task-qa 배포 경로가 범용 버전을 배포하도록 확인

## 제약 조건

- 기존 dev 오케스트레이터(opd/opds/opdw)의 QA 기능이 저하되면 안 됨
- 하네스의 QA Gate 메커니즘은 유지하되, dev/범용 분기만 추가
- 커뮤니티 스킬 원본 수정 금지
- 레거시 태스크 파일(tasks/042 등)은 히스토리이므로 수정하지 않음

## 기술 스택

- Markdown (SKILL.md, AGENT.md, 가이드 문서)
- JSON (opal-skills-registry.json)
- Shell (install-mac.sh)

## 관련 문서

- `skills/op-task-qa/SKILL.md` — 현재 QA 스킬 (리네이밍 대상)
- `agents/op-task-qa-agent/AGENT.md` — 현재 QA 에이전트 (리네이밍 대상)
- `opal/core/references/opal-harness.md` — QA Gate 정의
- `opal/core/references/opal-skills-registry.json` — 스킬 레지스트리
- `opal/core/references/agents.md` — 에이전트 레지스트리
- `.opal/memory/project_qa_skill_rename.md` — 태스크 메모리
