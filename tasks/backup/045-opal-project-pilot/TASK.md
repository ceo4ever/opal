# TASK: opal-project-pilot 오케스트레이터 + 범용 단계 스킬 신규 개발

> 작성일: 2026-03-29 | 작업 유형: 신규
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

코드 개발이 아닌 범용 태스크를 수행하는 오케스트레이터(opal-project-pilot)와 범용 단계 스킬(op-plan, op-execute)을 신규 개발하고, 기존 워커 에이전트를 범용 이름으로 리네이밍한다.

## 배경

현재 OPAL 오케스트레이터는 코드 개발(opd/opds/opdw)과 문서 작성(opw/opwt)에 특화되어 있다. OPAL 프로젝트 자체처럼 "코드도 아니고 순수 문서도 아닌" 작업(스킬/에이전트 .md 작성, 셸 스크립트 수정, 구조 변경 등)을 수행할 범용 오케스트레이터가 없다.

또한 기존 워커 에이전트(op-dev-agent)는 실제로 범용 스킬 실행기임에도 이름이 dev에 한정되어 있어 혼동을 준다.

## 요구사항

### 오케스트레이터: opal-project-pilot (opp)

- [ ] TASK → PLAN → EXECUTE 3단계 파이프라인
- [ ] 워커 디스패치 방식 (PM 직접 수행 아님)
- [ ] 하네스(opal-harness.md) 준수 (Guards, Gates, State)
- [ ] TASK 단계는 기존 op-task 스킬 재활용
- [ ] PLAN 단계에서 op-plan 스킬을 워커에게 디스패치
- [ ] EXECUTE 단계에서 op-execute 스킬을 워커에게 디스패치
- [ ] STATE.md 도메인 치환값 정의

### 범용 단계 스킬: op-plan

- [ ] TASK.md를 분석하여 범용 실행 계획(PLAN.md)을 작성
- [ ] 필요 시 웹검색, 파일검색, 스킬검색, 코드검색, 프로젝트 문서 등 모든 수단을 동원하여 분석/설계
- [ ] 도메인 무관 — 문서, 코드, 설정, 구조 변경 등 어떤 작업이든 계획 가능
- [ ] FE/BE 특화 로직 없음 (execution-plan.json, 영역 태그, 복잡도 판별 등 불필요)
- [ ] 실행 체크리스트 포함 (op-execute가 따를 수 있는 구체적 수준)
- [ ] 페르소나 정의 (범용 분석/설계)

### 범용 단계 스킬: op-execute

- [ ] PLAN.md를 읽고 분석하여 파일 작성/수정/이동 등 실행
- [ ] 도메인 무관 — 마크다운, 셸 스크립트, 설정 파일, 간단한 코드 수정 등 만능 실행
- [ ] FE/BE 특화 로직 없음 (ui-designer 연동, 보안 가드레일 등 불필요)
- [ ] PLAN.md의 실행 체크리스트를 순서대로 수행
- [ ] 페르소나 정의 (범용 실행)

### 에이전트 리네이밍: op-dev-agent → opal-task-agent

- [ ] 에이전트 파일 리네이밍 (폴더명 + AGENT.md 내용)
- [ ] model 오버라이드 테이블에 op-plan, op-execute 추가
- [ ] 기존 op-dev-* 스킬 model 매핑 유지 (하위 호환)
- [ ] 기존 오케스트레이터(opd/opds/opdw)의 에이전트 참조 업데이트
- [ ] agents.md 레지스트리 업데이트
- [ ] install-mac.sh 배포 경로 업데이트

## 제약 조건

- 기존 opal-pilot-dev/dev-short/dev-wireframe 파이프라인의 동작에 영향을 주지 않아야 한다
- 하네스(opal-harness.md)를 수정하지 않는다 (공통 인프라는 그대로)
- 네이밍 패턴: 오케스트레이터는 `opal-project-pilot`, 단계 스킬은 `op-{기능}`, 에이전트는 `opal-{역할}`
- opal-doc-standard v2.0 문서 규칙 준수

## 기술 스택

- 마크다운 문서 (SKILL.md, AGENT.md)
- 셸 스크립트 (install-mac.sh)
- JSON (skill-registry)

## 관련 문서

- `~/.opal/references/opal-harness.md` — 하네스 공통 인프라
- `~/.opal/references/skills.md` — 스킬 레지스트리
- `~/.opal/references/agents.md` — 에이전트 레지스트리
- `skills/opal-pilot-dev-short/SKILL.md` — 참조 오케스트레이터 (구조 참고)
- `skills/op-dev-plan/SKILL.md` — 참조 단계 스킬 (구조 참고)
- `skills/op-dev-execute/SKILL.md` — 참조 단계 스킬 (구조 참고)
- `agents/op-dev-agent/AGENT.md` — 리네이밍 대상
- `docs/CONVENTIONS.md` — 코드 및 문서 컨벤션
