# TASK: opsdd 스킬 구현 — 092 설계 기반

> 작성일: 2026-04-07 | 작업 유형: 개선 | 적용 스킬: opp | 모드: interactive
> 입력: 092 PLAN.md §8 구현 체크리스트 + 오늘 대화 합의사항
> 출력: 수정된 스킬 파일들

## 작업 목표

092에서 확정된 opsdd 스킬 개선 설계를 실제로 구현한다.
7단계 → 5단계 파이프라인, tasks/ 단일 루트 통합, EXECUTE-LOOP 재작성, op-sdd-tasks 삭제.

## 배경

092 태스크에서 opsdd의 세 가지 구조 문제(폴더 혼재, EXECUTE-LOOP 미작동, Verify 과다)를 분석하고 설계 방향을 확정했다. 이번 태스크에서 해당 설계를 실제 스킬 파일에 반영한다.

## 확정된 설계 방향 (대화에서 합의)

1. **tasks/ 단일 루트**: 모든 산출물을 `tasks/{NNN}-{feature}/` 안에 통합
2. **base_path 조건부 처리**: 하네스 §4에서 base_path가 지정된 경우 사용, 없으면 기본값 유지 (기존 오케스트레이터 영향 없음)
3. **5단계 파이프라인**: TASK → SPEC → REVIEW(PM 직접) → DESIGN → EXECUTE → DONE
4. **EXECUTE-LOOP**: opds/opd 대신 op-dev-plan + op-dev-execute 직접 디스패치, ACT 구조
5. **op-sdd-verify**: 파일 수정 없음 — PM이 현재 파일을 그대로 읽어 체크리스트로 활용. opsdd SKILL.md에서 디스패치 지시만 제거
6. **op-sdd-tasks**: op-sdd-plan에 통합 후 삭제
7. **ACT 에이전트**: 구현 + 테스트 통합 수행 (op-dev-qa 별도 디스패치 제거), PM이 재시도 루프 관리

## 요구사항

### Step 1: 폴더 구조 통합 + base_path 조건부

- [ ] **opal-harness.md §4 수정** — base_path 조건부 규칙 추가
  - 무엇을: `base_path` 파라미터가 지정된 경우 해당 경로 사용, 없으면 `tasks/{NNN}-{스킬약어}-{태스크명}/` 기본값
  - 어디에: `opal/core/references/opal-harness.md` §4 TASK 공통 프로세스 저장 경로 항목
  - AC: 기존 오케스트레이터(opp, opds 등)는 동작 변경 없음. opsdd만 base_path 지정 시 경로 오버라이드 가능

- [ ] **opal-pilot-sdd/SKILL.md Phase 0 수정** — base_path 지정
  - 무엇을: Phase 0(TASK)에서 `base_path=tasks/{NNN}-{feature}/` 지정하도록 명시
  - AC: opsdd 실행 시 `tasks/{NNN}-{feature}/` 단일 경로에 모든 산출물 생성

### Step 2: EXECUTE-LOOP 재작성

- [ ] **opal-pilot-sdd/SKILL.md Phase 4 수정**
  - 무엇을: opds/opd 위임 제거 → ACT 에이전트(구현+테스트 통합) 직접 디스패치, actions/ACT-{NNN}-{name}/ 구조 반영, ACT 재시도 루프(PM 관리, op-dev-execute만 재디스패치), ACT 내부 STATE.md 제거 반영
  - AC: Phase 4가 5단계 파이프라인(PLAN.md §4)과 일치함. op-dev-qa 별도 디스패치 없음

- [ ] **execute-loop-guide.md 재작성**
  - 무엇을: ACT 루프 구조(ACT 에이전트 통합 실행 + PM 재시도 관리), 재시도 패턴, 디스패치 프롬프트 템플릿 — 하네스 §1 자동 루핑 제약과 최대 재시도 횟수 명시 연결
  - AC: ACT별 실행 흐름과 재시도 조건이 명확히 기술됨

### Step 3: REVIEW Phase + Verify 간소화

- [ ] **opal-pilot-sdd/SKILL.md Phase 1~3 재작성**
  - 무엇을: SPEC-VERIFY/TASKS-VERIFY Phase 제거, Phase 2를 REVIEW(PM 직접: 구조검증 → TEST-SCENARIOS.md 작성 → 커버리지 확인)로 전환
  - AC: 5단계 파이프라인과 단계 수/Gate 수 일치

- [ ] **op-sdd-verify/SKILL.md — 수정 없음**
  - 무엇을: 파일 자체는 변경하지 않음. PM이 현재 파일을 그대로 읽어 구조검증 체크리스트로 활용
  - AC: opal-pilot-sdd/SKILL.md에서 op-sdd-verify 워커 디스패치 지시가 제거됨

- [ ] **verify-guide.md 재작성**
  - 무엇을: REVIEW Phase PM 직접 검증 가이드 (구조검증 S-1~S-6, TS 작성 기준, 커버리지 확인)
  - AC: 워커 디스패치 내용 없음, PM 액션 기준으로 기술

### Step 4: 단계 스킬 수정

- [ ] **op-sdd-plan/SKILL.md 수정** — op-sdd-tasks 통합
  - 무엇을: SPEC-PLAN.md에 아키텍처 + ACT 분해 + 병렬/순서 의존관계까지 포함하도록 확장, 출력 경로 수정
  - AC: 단일 스킬로 SPEC-PLAN.md(아키텍처 + ACT 목록 + 병렬/순서 의존관계) 생성 가능

- [ ] **op-sdd-tasks/SKILL.md 삭제**
  - AC: 파일 삭제 완료, opal-pilot-sdd/SKILL.md에서 참조 없음

- [ ] **op-sdd-spec/SKILL.md 출력 경로 수정**
  - 무엇을: specs/ → tasks/ 기준으로 경로 수정
  - AC: 출력 경로가 `tasks/{NNN}-{feature}/SPEC.md`로 명시됨

### Step 5: 검증

- [ ] 수정된 opal-pilot-sdd/SKILL.md 전체 흐름 검토 (5단계 일관성)
- [ ] 기존 opp/opds 동작에 영향 없음 확인 (base_path 미지정 케이스)

## 제약 조건

- `~/.opal/` 직접 수정 금지 — 소스 경로(`opal/core/`, `opal/skills/`)만 수정
- op-sdd-tasks 삭제 전 op-sdd-plan 통합 완료 확인
- 하네스 변경은 기존 오케스트레이터(opp, opds, opd, opwt)에 영향 없어야 함

## 기술 스택

- Markdown

## 관련 문서

- `tasks/092-opp-opsdd-refactor/PLAN.md` — 설계 분석 + 수정 파일 목록 + 구현 체크리스트
- `opal/skills/opal-pilot-sdd/SKILL.md`
- `opal/skills/opal-pilot-sdd/references/execute-loop-guide.md`
- `opal/skills/opal-pilot-sdd/references/verify-guide.md`
- `opal/skills/op-sdd-verify/SKILL.md`
- `opal/skills/op-sdd-plan/SKILL.md`
- `opal/skills/op-sdd-tasks/SKILL.md`
- `opal/skills/op-sdd-spec/SKILL.md`
- `opal/core/references/opal-harness.md`
