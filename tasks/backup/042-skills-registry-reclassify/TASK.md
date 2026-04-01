# TASK: 컴포넌트 리네이밍 + 레거시 정리

> 작성일: 2026-03-29 | 작업 유형: 개선
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

otp-*/dtp-* 네이밍을 OPAL 체계에 맞게 리네이밍하고, 용어를 공식 정의하며, 레거시 컴포넌트(dev-task-pilot + 레거시 에이전트 6개)를 삭제한다.

## 배경

### 네이밍 문제

- **otp**: 032에서 도입했으나 풀네임 정의 없음
- **dtp**: 원래 dev-task-pilot 약자였으나, 컴포지션 전환 후 의미 소실. wireframe/qa 등 dev 아닌 것도 포함
- **worker**: 에이전트인데 worker로 명명

### 레거시 잔존

032(컴포지션 전환) 완료 후 dev-task-pilot과 레거시 에이전트 6개가 고아 상태.
신규 에이전트(dtp-worker, dtp-qa-worker, dtp-test-worker)가 이미 대체.

### 041 기반

041에서 JSON 레지스트리(SSOT)로 전환 완료. skills.md는 기술 스택 추천만 유지.
리네이밍 시 JSON 레지스트리 갱신이 핵심.

## 요구사항

### A. 리네이밍 — 오케스트레이터 (otp → opal-pilot)

opal-pilot = OPAL Pilot (태스크 파이프라인을 조종하는 오케스트레이터)

| 현재 | 변경 후 | 약어 | 도메인 |
|------|--------|------|--------|
| otp-dev | opal-pilot-dev | opd | dev |
| otp-dev-short | opal-pilot-dev-short | opds | dev |
| otp-wf | opal-pilot-dev-wireframe | opdw | dev |
| otp-write | opal-pilot-write | opw | write |
| otp-write-tech | opal-pilot-write-tech | opwt | write |

- [ ] 스킬 디렉토리 rename (`skills/otp-* → skills/opal-pilot-*`)
- [ ] 각 SKILL.md 내부 name, description, 상호 참조 수정
- [ ] JSON 레지스트리 (`opal-skills-registry.json`) otp 그룹 갱신

### B. 리네이밍 — 단계 스킬 (dtp → op-dev / op-task)

- **op-dev-***: dev 도메인 단계 스킬 (오케스트레이터가 디스패치)
- **op-task-***: 범용 단계 스킬 (여러 도메인에서 공유)

| 현재 | 변경 후 | 성격 |
|------|--------|------|
| dtp-task | op-task | 범용 |
| dtp-qa | op-task-qa | 범용 |
| dtp-analysis | op-dev-analysis | dev |
| dtp-plan | op-dev-plan | dev |
| dtp-todo | op-dev-todo | dev |
| dtp-test-scenario | op-dev-test-scenario | dev |
| dtp-execute | op-dev-execute | dev |
| dtp-wireframe | op-dev-wireframe | dev |

- [ ] 스킬 디렉토리 rename (`skills/dtp-* → skills/op-dev-* 또는 skills/op-task-*`)
- [ ] 각 SKILL.md 내부 name, description, dispatched_by, 상호 참조 수정
- [ ] JSON 레지스트리 dtp 그룹 → op-dev / op-task 그룹으로 재편

### C. 리네이밍 — 에이전트 (worker → agent)

| 현재 | 변경 후 | 역할 |
|------|--------|------|
| dtp-worker | op-dev-agent | 범용 워커 (단계 스킬 실행) |
| dtp-qa-worker | op-task-qa-agent | QA 검증 |
| dtp-test-worker | op-dev-test-agent | 동적 테스트 실행 |
| wtm-worker | wtm-agent | web-to-markdown 워커 |

- [ ] 에이전트 디렉토리 rename (`agents/dtp-*-worker → agents/op-*-agent`)
- [ ] 각 AGENT.md 내부 name, description 수정
- [ ] agents.md 레지스트리 갱신

### D. 레거시 삭제

- [ ] `skills/dev-task-pilot/` 디렉토리 삭제
- [ ] 레거시 에이전트 6개 디렉토리 삭제:
  - `agents/dtp-dev-agent/`
  - `agents/dtp-qa-dev-agent/`
  - `agents/dtp-dev-test-agent/`
  - `agents/dtp-wireframe-ui-agent/`
  - `agents/dtp-qa-wireframe-agent/`
  - `agents/dtp-action-plan-agent/`

### E. 문서 동기화

- [ ] opal-harness.md: 탐색 경로, 용어를 새 네이밍으로 수정
- [ ] CLAUDE.md: 소스 구조 설명, 컴포넌트 의존 관계 수정
- [ ] README.md: dev-task-pilot → opal-pilot 체계로 교체
- [ ] agents.md: 레거시 제거 + 새 에이전트명 반영
- [ ] opal-skills-registry.json / community-skills-registry.json: 그룹 키 + 스킬 데이터 갱신
- [ ] skill-registry.js: 그룹 키 변경에 따른 코드 수정 (있으면)
- [ ] 각 오케스트레이터 SKILL.md 내부의 디스패치 경로, 에이전트 참조 수정
- [ ] AGENT.md (글로벌 `~/.opal/AGENT.md`): `//` 커맨드 예시 갱신
- [ ] install-mac.sh 영향 확인 (clean deploy 방식이므로 별도 수정 불필요 예상)

### F. 용어 정의 문서화

- [ ] opal-harness.md 또는 별도 위치에 공식 용어 정의 추가:
  - **opal-pilot**: OPAL Pilot — 태스크 파이프라인 오케스트레이터
  - **op-dev**: OPAL Pilot Dev Phase — dev 도메인 단계 스킬
  - **op-task**: OPAL Pilot Task Phase — 범용 단계 스킬

## 제약 조건

- 태스크 문서(tasks/022~040)는 이력으로 보존 — 내부 참조는 수정하지 않음
- `//` 커맨드 체계 유지 — 약어만 변경 (otpd→opd 등)
- 041에서 만든 JSON 레지스트리 SSOT 구조 유지

## 기술 스택

- Markdown 문서
- JSON (레지스트리)
- JavaScript (skill-registry.js — 영향 확인)
- Shell script (install-mac.sh — 영향 확인)

## 관련 문서

- `opal/core/references/opal-skills-registry.json` — 스킬 레지스트리 (SSOT)
- `opal/core/references/community-skills-registry.json` — 커뮤니티 레지스트리
- `opal/core/references/skills.md` — 기술 스택 추천 (폴백)
- `opal/core/references/agents.md` — 에이전트 레지스트리
- `opal/core/references/opal-harness.md` — 하네스
- `opal/core/AGENT.md` — 글로벌 에이전트 정의
- `opal/tools/skill-registry/skill-registry.js` — CLI 도구
- `CLAUDE.md` — 소스 구조 설명
- `README.md` — 프로젝트 소개
- `tasks/032-dtp-to-otp-restructure/` — 컴포지션 전환 이력
- `tasks/041-json-registry-tool/` — JSON 레지스트리 전환 이력
