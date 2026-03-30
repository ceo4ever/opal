# DONE: 오케스트레이터 정비

> 완료일: 2026-03-30 | 스킬: //opp

## 수행 내용

### 1. opw 삭제
- 소스(`opal/skills/opal-pilot-write/`) + 배포본(`~/.opal/skills/opal-pilot-write/`) 삭제
- 레지스트리, 하네스 용어표, 다른 스킬 참조 정리

### 2. opp 리네이밍 + 정체성 정비
- opal-project-pilot → **opal-pilot-project** (약어 opp 유지)
- description: "프로젝트 범용 오케스트레이터 (문서 작성, 간단한 코드 수정 포함)"

### 3. opdp 리네이밍 + opwt 연동
- opal-project-dev-pilot → **opal-pilot-project-dev** (약어 oppd)
- Phase 1~2(PRD/TRD 직접 작성) → opwt "작성" 모드 호출로 전환
- 4 Phase → 3 Phase 슬림화 (PLAN → ROADMAP → EXECUTE)

### 4. 전체 참조 정리
- docs/ARCHITECTURE.md, docs/CONVENTIONS.md 갱신
- 하네스 용어표 최종 정리
- 배포본 전체 동기화 완료

### 5. 별도 태스크 등록
- agentic 자율 루핑 장치 설계 → `.opal/memory/task_agentic_loop.md`

### 6. 하네스 공통 규칙 추가
- **Guards: 디스패치 의무 원칙** — 오케스트레이터 SKILL.md에 "워커 디스패치"로 정의된 단계는 반드시 서브에이전트를 디스패치. PM이 직접 실행으로 대체 금지
- **Gates: 체크리스트 검증 게이트** — 1차 워커가 체크박스 갱신, 2차 PM이 PLAN.md Read하여 갱신 확인. 완전 갱신 후에만 DONE.md 진행
- PLAN.md 체크리스트 소급 갱신 완료

## 변경 파일

**소스 (삭제)**:
- `opal/skills/opal-pilot-write/` (전체 삭제)

**소스 (리네이밍)**:
- `opal/skills/opal-project-pilot/` → `opal/skills/opal-pilot-project/`
- `opal/skills/opal-project-dev-pilot/` → `opal/skills/opal-pilot-project-dev/`

**소스 (수정)**:
- `opal/core/references/opal-skills-registry.json`
- `opal/core/references/opal-harness.md`
- `opal/core/references/agents.md`
- `opal/skills/opal-pilot-dev/SKILL.md`
- `opal/skills/opal-pilot-dev-short/SKILL.md`
- `opal/skills/opal-pilot-project/SKILL.md`
- `opal/skills/opal-pilot-project-dev/SKILL.md` (전면 재작성)
- `opal/skills/opal-pilot-project-dev/references/prd-guide.md`
- `opal/skills/opal-pilot-project-dev/references/trd-guide.md`
- `opal/skills/opal-pilot-project-dev/references/roadmap-guide.md`
- `opal/skills/opal-project-init/SKILL.md`
- `opal/skills/op-task-plan/SKILL.md`
- `opal/skills/op-task-execute/SKILL.md`
- `opal/skills/op-task-qa/SKILL.md`
- `opal/skills/op-task-qa/references/qa-general-guide.md`
- `docs/ARCHITECTURE.md`
- `docs/CONVENTIONS.md`

## 정비 후 오케스트레이터 체계

| 약어 | 이름 | 파이프라인 |
|------|------|-----------|
| opd | opal-pilot-dev | TASK→ANALYSIS→PLAN+TS→EXECUTE |
| opds | opal-pilot-dev-short | TASK→PLAN+TS→EXECUTE |
| opdw | opal-pilot-dev-wireframe | TASK→WIREFRAME→EXECUTE |
| opwt | opal-pilot-write-tech | Phase 1~4 (네트워크) |
| opp | opal-pilot-project | TASK→PLAN→EXECUTE |
| oppd | opal-pilot-project-dev | opwt→ROADMAP→opd/opds |
