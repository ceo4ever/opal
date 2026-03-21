# TASK: opal-project-init PM 에이전트 프로필 생성 파이프라인 추가

> 작성일: 2026-03-21 | 작업 유형: 기능 개선

## 작업 목표

opal-project-init 스킬에서 `.opal/AGENT.md`(PM 프로필)과 `.opal/MEMORY.md`(메모리 인덱스)를 자동 생성하여, 알투가 프로젝트 진입 시 PM 역할을 수행할 수 있도록 한다.

## 배경

### 현재 문제

1. **역할 연결 끊김**: `~/.opal/AGENT.md`에 "프로젝트에 `.opal/AGENT.md`가 있으면 오케스트레이터 모드"라고 정의되어 있지만, `opal-project-init`이 이 파일을 생성하지 않아 오케스트레이션이 활성화될 일이 없음
2. **템플릿 위치 부적절**: `opal/templates/project-agent.md`와 `memory-index.md`가 opal-project-init과 분리되어 있어, 스킬 실행 시 자동 적용되지 않음
3. **PM 프로필 부재**: 기존 `project-agent.md` 템플릿은 코드 컨벤션/브랜치 전략 같은 기술적 규칙만 있고, PM 역할에 필요한 섹션(페르소나, 도메인 지식, 의사결정 원칙 등)이 없음

### 알투의 역할 정의 (캡틴과 합의)

- **알투 = 항상 캡틴의 개인 비서**
- **프로젝트 업무 시 → 해당 프로젝트의 PM으로 전환** (별도 PM 에이전트를 만들지 않음)
  - 페르소나: 이 프로젝트에서 어떤 관점으로 사고할지
  - 프로젝트 목적: 왜 이 프로젝트가 존재하는지
  - 도메인 지식: 해당 분야의 핵심 개념/용어
  - 의사결정 원칙: 트레이드오프 시 어떤 쪽을 선택할지
  - 현재 Phase: 지금 어디까지 왔고 다음은 뭔지
  - 금지사항: 이 프로젝트에서 절대 하면 안 되는 것
- **3-Tier(PM 에이전트 도입) 대신 2-Tier 유지**: 서브에이전트가 상주 불가하므로 PM 레이어를 추가해도 오버헤드만 증가. `.opal/AGENT.md`를 고도화하여 알투 자신이 PM 모자를 쓰는 방식이 효과적

### PM 모자를 쓰기 위해 필요한 것

1. **프로젝트 PM 프로필** (`.opal/AGENT.md`): 알투가 읽으면 PM 역할 활성화
2. **프로젝트 메모리** (`.opal/MEMORY.md`): 세션 간 맥락 유지 (아키텍처 결정, 도메인 지식, 작업 이력, 선호, 반복 이슈)
3. **자동 생성 파이프라인**: opal-project-init에서 신규/기존 프로젝트 모두 자동 생성

## 요구사항

- [ ] `opal/templates/`의 `project-agent.md`, `memory-index.md`를 `skills/opal-project-init/templates/common/opal/`로 이동
- [ ] `project-agent.md` 템플릿을 PM 역할 관점으로 개선 (페르소나, 프로젝트 목적, 도메인 지식, 의사결정 원칙, 현재 Phase, 금지사항)
- [ ] `memory-index.md` 템플릿을 카테고리 구조화 (architecture_decisions, domain_knowledge, work_history, preferences, issues)
- [ ] `opal-project-init/SKILL.md`의 Step 7에 `.opal/` 생성 로직 추가 (apply.js 연동)
- [ ] `apply.js`에 `[5/5] .opal/` 생성 섹션 추가
- [ ] 신규/기존 프로젝트 모드 모두 지원 (existing 모드에서 기존 `.opal/AGENT.md` 보존)
- [ ] 기존 `opal/templates/project-agent.md`, `memory-index.md` 삭제

## 제약 조건

- 기존 `apply.js`의 `[1/4]~[4/4]` 동작을 변경하지 않음 (회귀 방지)
- existing 모드에서 사용자가 커스터마이징한 `.opal/AGENT.md`를 덮어쓰지 않음
- 플레이스홀더는 기존 매핑표(`{{PROJECT_NAME}}` 등)를 재활용

## 관련 문서

- `skills/opal-project-init/SKILL.md` — 메인 스킬 정의
- `skills/opal-project-init/scripts/apply.js` — 템플릿 적용 스크립트
- `opal/templates/project-agent.md` — 기존 템플릿 (이동 대상)
- `opal/templates/memory-index.md` — 기존 템플릿 (이동 대상)
- `~/.opal/AGENT.md` — 알투 에이전트 정의 (`.opal/AGENT.md` 존재 시 오케스트레이터 모드)
- `~/.opal/skills/opal-orchestrator/SKILL.md` — 오케스트레이터 스킬
