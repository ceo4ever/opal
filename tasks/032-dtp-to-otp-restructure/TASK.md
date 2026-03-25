# TASK: dev-task-pilot → opal-task-pilot 리스트럭처링

> 작성일: 2026-03-25 | 작업 유형: 리팩토링 (대규모 구조 변경)

## 작업 목표

dev-task-pilot(dtp) 단일 스킬을 opal-task-pilot(otp) 체계로 전면 재구조화한다. 3개 모드를 독립 스킬로 분리하고, 페르소나 시스템과 기술 컨텍스트 가이드를 도입한다.

## 배경

1. **모드 자동 감지 제거**: 현재 단일 SKILL.md에서 Full/Short/Wireframe을 자동 판별하는데, 사용자가 명시적으로 스킬을 호출하는 방식으로 변경
2. **TASK.md 서브에이전트 위임**: 현재 오케스트레이터(알투)가 직접 TASK.md를 작성하는데, 서브에이전트가 TASK부터 전체 파이프라인을 담당하도록 변경
3. **페르소나 시스템 도입**: 단계별로 다른 사고방식(Product Engineer, Code Analyst, Architect, FE/BE Engineer)을 워커에 주입
4. **기술 컨텍스트 분리**: analysis-guide.md에 흩어져 있던 기술 스택 로딩 로직을 독립 가이드로 통합

## 요구사항

### R1. 스킬 분리
- [ ] `skills/otp-dev/SKILL.md` — Full Task 전용 (`/otp-dev`)
- [ ] `skills/otp-dev-short/SKILL.md` — Short Task 전용 (`/otp-dev-short`)
- [ ] `skills/otp-dev-wf/SKILL.md` — Wireframe UI 전용 (`/otp-dev-wf`)
- [ ] 각 스킬은 모드 판별 로직 없이 해당 파이프라인만 정의

### R2. 공통 리소스 (otp-common)
- [ ] `skills/otp-common/references/` — 공유 가이드 (기존 references/ 이관 + 신규)
  - [ ] `task-guide.md` — 신규: TASK.md 작성 공통 규칙
  - [ ] `tech-context-guide.md` — 신규: 기술 스택 로딩, 스킬/MCP 매핑 공통 프로세스
  - [ ] `analysis-guide.md` — 기존 이관 (기술 컨텍스트 부분 분리 후)
  - [ ] `plan-guide.md` — 기존 이관
  - [ ] `execute-guide.md` — 기존 이관
  - [ ] `test-scenario-guide.md` — 기존 이관
  - [ ] `checkpoint-guide.md` — 기존 이관
  - [ ] `state-guide.md` — 기존 이관
- [ ] `skills/otp-common/personas/` — 페르소나 5개
  - [ ] `product-engineer.md`
  - [ ] `code-analyst.md`
  - [ ] `software-architect.md`
  - [ ] `frontend-engineer.md`
  - [ ] `backend-engineer.md`

### R3. 스킬별 전용 리소스
- [ ] `skills/otp-dev/references/todo-guide.md` — Full Task 전용
- [ ] `skills/otp-dev/references/execute-plan-guide.md` — Full Task 복잡 모드 전용
- [ ] `skills/otp-dev-wf/references/wireframe-task-guide.md` — Wireframe 전용
- [ ] `skills/otp-dev-wf/references/wireframe-qa-guide.md` — Wireframe QA 전용

### R4. 에이전트 리네이밍
- [ ] `dtp-dev-agent` → `otp-dev-agent`
- [ ] `dtp-wireframe-ui-agent` → `otp-wf-agent`
- [ ] `dtp-qa-dev-agent` → `otp-qa-dev-agent`
- [ ] `dtp-qa-wireframe-agent` → `otp-qa-wf-agent`
- [ ] `dtp-action-plan-agent` → `otp-action-plan-agent`
- [ ] `dtp-dev-test-agent` → `otp-test-agent`
- [ ] 각 에이전트 AGENT.md 내용에서 dtp 참조를 otp로 변경
- [ ] 페르소나 디스패치 연동 반영

### R5. 오케스트레이션 변경
- [ ] TASK.md를 서브에이전트가 작성하도록 변경 (단계별 디스패치)
- [ ] 오케스트레이터 역할: 워커 디스패처 + QA 디스패처 + 게이트 관리자
- [ ] 각 SKILL.md의 디스패치 프롬프트에 페르소나 + 기술 컨텍스트 + 가이드 조합 명시

### R6. 페르소나 시스템
- [ ] 단계별 페르소나 매핑: TASK→Product Engineer, ANALYSIS→Code Analyst, PLAN/TODO→Architect, EXECUTE→FE/BE Engineer
- [ ] 신규/수정 모드 자동 판별 (기존 코드 유무로 결정, 호출 시 지정 불필요)
- [ ] 페르소나는 principles 기반 (있으면 따르고, 없으면 만든다 패턴)

### R7. 레지스트리 업데이트
- [ ] `~/.opal/references/skills.md` — otp 스킬 3개 등록, dtp 트리거 유지 (당분간 공존)
- [ ] `~/.opal/references/agents.md` — otp 에이전트 6개 등록

## 제약 조건

- 기존 `skills/dev-task-pilot/`은 삭제하지 않음 (안정화 후 판단)
- 기존 에이전트 `agents/dtp-*`도 당분간 유지
- otp-doc 스킬은 이번 태스크 범위 밖 (별도 태스크로 진행)
- `install-mac.sh` 배포 스크립트 업데이트는 이번 범위에 포함

## 기술 스택

- 산출물: Markdown (.md)
- 영향 범위: skills/, agents/, opal/core/references/, install-mac.sh

## 실행 단계 스케줄

| 단계 | 내용 | 주요 산출물 | 의존 |
|------|------|------------|------|
| **1. ANALYSIS** | 기존 dtp 전체 파일 분석, 이관 대상 식별, 변경 영향 맵 | ANALYSIS.md | TASK |
| **2. PLAN** | 폴더 구조 확정, 파일별 작성/이관/수정 계획, 디스패치 구조 설계 | PLAN.md | ANALYSIS |
| **3. TODO** | 실행 체크리스트 (파일 단위), 의존 순서, 복잡도 판별 | TODO.md | PLAN |
| **4. TEST-SCENARIO** | 검증 시나리오 (구조 정합성, 참조 경로, 레지스트리 일관성) | TEST-SCENARIO.md | TODO |
| **5. EXECUTE** | 실제 파일 생성/이관/수정 | 스킬 3개 + 공통 + 에이전트 6개 + 레지스트리 | TODO |
| **6. QA + TEST** | 산출물 품질 검증 + 테스트 시나리오 실행 | QA 리포트 + DONE.md | EXECUTE |

### 단계별 상세

**1단계 ANALYSIS** — 기존 구조 정밀 분석
- 기존 dtp SKILL.md, modes/3개, references/10개 전수 조사
- 기존 에이전트 6개 내용 분석
- 이관 vs 신규 작성 vs 수정 분류
- 파일 간 참조 관계(상호 의존) 맵핑

**2단계 PLAN** — 신규 구조 설계
- otp-common / otp-dev / otp-dev-short / otp-dev-wf 폴더 구조 확정
- 페르소나 5개 상세 내용 설계
- task-guide.md, tech-context-guide.md 신규 가이드 설계
- 기존 가이드 이관 시 변경 사항 (기술 컨텍스트 분리, dtp→otp 참조 변경)
- 디스패치 프롬프트 구조 설계 (페르소나 + 기술 컨텍스트 + 가이드 조합)
- 에이전트 리네이밍 + 내용 변경 계획

**3단계 TODO** — 실행 순서 결정
- 의존 순서: otp-common(공통) → otp-dev → otp-dev-short → otp-dev-wf → 에이전트 → 레지스트리
- 파일 단위 체크리스트
- 복잡도 판별 → Part C 필요 여부

**4단계 TEST-SCENARIO** — 검증 계획
- S-1: 폴더 구조 정합성 (모든 참조 경로가 실제 파일 존재)
- S-2: 가이드 간 상호 참조 일관성
- S-3: 에이전트 AGENT.md 내 otp 참조 정확성
- S-4: 레지스트리(skills.md, agents.md) 등록 정합성
- S-5: install-mac.sh 배포 경로 정합성

**5단계 EXECUTE** — 구현
- 공통 리소스 → 스킬 3개 → 에이전트 6개 → 레지스트리 → install-mac.sh 순서

**6단계 QA + TEST** — 검증 및 완료
- 테스트 시나리오 실행
- 최종 QA 리뷰
- DONE.md 생성

## 관련 문서

- 기존 스킬: `skills/dev-task-pilot/SKILL.md`
- 기존 에이전트: `agents/dtp-*/AGENT.md` (6개)
- 레지스트리: `~/.opal/references/skills.md`, `~/.opal/references/agents.md`
- 프로젝트 메모리: `.opal/memory/project_otp_doc_plan.md` (otp-doc 후속 계획)
