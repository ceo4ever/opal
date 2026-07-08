# TASK: opx (opal-pilot-flex) — 인터뷰 기반 적응형 메타 pilot 신설

> 작성일: 2026-06-15 | 작업 유형: 신규 | 적용 스킬: opd | 모드: semi-agentic
> 입력: 캡틴 요청 + 2라운드 인터뷰 합의
> 출력: TASK.md

## 작업 목표

작업 입력의 충분성을 평가해 (부족하면 인터뷰로 보완) **목적·이유·성공기준·범위 4요소를 확정**한 뒤, 기존 `op-*` 단계 스킬·에이전트를 **동적으로 조합**해 그 작업에 최적화된 파이프라인을 설계·승인·실행하는 범용 적응형 메타 pilot `opx`(opal-pilot-flex)를 신설한다.

## 배경

기존 OPAL pilot(opd/opds/opp/opwt/opdd/opsdd)은 모두 `op-*` 단계 스킬의 **고정 조합**이다 — 작업 성격과 무관하게 정해진 파이프라인이 실행된다. 캡틴 요청의 핵심은 "파이프라인 자체를 인터뷰로 동적 설계하는 pilot"으로, 기존 고정 파이프라인과 차별되는 새로운 컴포넌트 계층이다.

## 배경 분석 (대화에서 도출)

### 자산 인벤토리 (그라운딩 완료)

- **빌딩 블록 (op-\* 단계 스킬)**: `op-task`, `op-task-plan`, `op-task-execute`, `op-task-qa`, `op-dev-analysis`, `op-dev-plan`, `op-dev-execute`, `op-dev-qa`, `op-dev-test-scenario`, `op-dev-todo`, `op-dev-wireframe`, `op-data-dictionary`, `op-data-model`, `op-data-ddl`, `op-sdd-*`, `op-spec-validator`, `op-brain-ingest`
- **에이전트**: be/fe/db/plan/planning/task/task-qa/task-action/test/sdd-action/convention/security/wtm
- **동적 STATE 인에이블러**: `state-tool init --rows-spec`가 임의 단계 행 구성을 받음 — "설계된 파이프라인 → 동적 STATE 행 생성 → 실행"이 기술적으로 성립 (`opal/skills/opal-pilot-dev/SKILL.md:266-269`)

### 기존 자산과의 관계

- 멈춰있는 `tasks/005-260515-opp-clarification-gate-ssot/`(명확화 게이트 SSOT)는 "TASK 인터뷰로 4요소 명확화 + 추정 진행 차단"을 일부 다루나, opx의 핵심인 "적응형 단계 설계 + 실행"은 없음 → **보완재**. 005 연계는 **보류**(캡틴 결정).
- `skills/interview/SKILL.md`(요구사항 수집 인터뷰)는 INTAKE 단계의 갭 보완 인터뷰에서 재사용.

### 인터뷰 합의 (2라운드)

| 결정 | 내용 |
|------|------|
| 구현 경로 | `opd` 풀 파이프라인 정식 태스크 (skill-creator는 일반 스킬용 — pilot 배선 미커버) |
| 실행 모델 | 기존 `op-*` 단계 스킬·에이전트 동적 조합 (신규 실행 스킬 만들지 않음, 필요 시 블록 수정 허용) |
| 작업 범위 | 범용 (코드+문서+혼합) |
| 이름/커맨드 | `opx` / `opal-pilot-flex` |
| 설계 산출물 | 별도 `PIPELINE.md` 설계서 (선택 단계·순서·근거·검증전략) → 캡틴 승인 |
| 조합 단위 | 계층 — op-* 단계 스킬 기본 + 필요 시 에이전트 직접 지정 |
| op-* 수정 범위 | 적극 수정/리팩터 (동적 조합 친화) |
| 005 연계 | 보류 |

## 확정된 설계 방향 (대화에서 합의)

opx 파이프라인 (잠정 — 정식 설계는 PLAN에서 확정):

| 단계 | 동작 | 산출물 |
|------|------|--------|
| INTAKE | 입력(호출 컨텍스트+선행 대화) 충분성 평가 → 4요소 도출 가능하면 즉시 확정 / 갭 존재 시 **갭에 한해서만** 인터뷰 보완 (전체 재질문 금지) | TASK.md |
| DESIGN | 작업 성격 분석 → 적합한 op-* 단계 스킬·에이전트 선택·순서화 + 검증전략 | PIPELINE.md |
| (승인 게이트) | 캡틴이 설계된 파이프라인 검토·승인 | — |
| MATERIALIZE | 승인된 PIPELINE.md → `state-tool init --rows-spec`로 동적 STATE 행 생성 | STATE.md |
| EXECUTE | 설계 단계를 순차/병렬 디스패치 (단계스킬 기본 + 필요 시 에이전트 직접) | 단계별 산출물 |
| CLOSE | DONE.md + brain ingest 훅 | DONE.md |

> INTAKE 충분성 판정 = "4요소 도출 가능성 룰브릭". 임계·표현은 PLAN에서 확정.

## 요구사항

- [ ] **R1 신규 pilot 스킬 생성** — `opal/skills/opal-pilot-flex/SKILL.md` 신설. AC: 파일이 존재하고, frontmatter `name: opal-pilot-flex` + OPAL description 패턴("반드시 이 스킬을 사용해야 하는 상황: ... opx ...") 포함, Harness 3-way 모드 분기 + INTAKE/DESIGN/MATERIALIZE/EXECUTE/CLOSE 단계 헤딩이 모두 존재, 500줄 이하.
- [ ] **R2 INTAKE 조건부 인터뷰** — 입력 충분성 평가 분기. AC: SKILL.md에 "4요소(목적·이유·성공기준·범위) 도출 가능 → 즉시 확정 / 갭 존재 → 갭 한정 인터뷰" 판정 룰브릭이 표/절차로 명시되고, interview 스킬 탐색 경로(프로젝트→글로벌)가 기재됨.
- [ ] **R3 DESIGN 동적 조합 + PIPELINE.md** — op-* 단계 스킬·에이전트를 작업 성격에 매핑해 선택·순서화. AC: SKILL.md에 빌딩 블록 카탈로그(op-* + 에이전트)와 선택 기준이 존재하고, PIPELINE.md 산출 형식(선택 단계·순서·근거·검증전략 필드)이 정의됨.
- [ ] **R4 MATERIALIZE 동적 STATE** — 승인된 PIPELINE.md를 `state-tool init --rows-spec`로 STATE 행에 반영하는 절차가 SKILL.md에 명시됨. AC: `--rows-spec` 호출 예시가 PIPELINE→행 매핑과 함께 기재됨.
- [ ] **R5 EXECUTE 계층 디스패치** — 단계스킬 기본 + 에이전트 직접 지정 폴백. AC: 디스패치 절차(단계 순회·병렬/순차 판별·`[WORKER]` 주입·Guards)가 기재됨.
- [ ] **R6 CLOSE 훅** — DONE.md 생성 + brain ingest 훅(brain 부재 시 no-op) + CLOSE 진입 게이트(사용자 승인 필수) 준수.
- [ ] **R7 op-* 리팩터 (동적 조합 친화)** — 동적 조합에 필요한 최소∼적극 수정. AC: opx가 호출하는 op-* 스킬이 "오케스트레이터가 단계를 동적으로 끼워넣어도 동작"하도록 입력 계약(이전 산출물·산출물 경로·다음 단계명 비고정)이 정리됨. 수정 대상·범위는 PLAN에서 확정.
- [ ] **R8 레지스트리 등록** — `opal/core/references/opal-skills-registry.json` + `~/.opal/references/skills.md`(소스: `opal/.../skills.md`) + skill-commands 예시에 opx/opal-pilot-flex 등록. AC: 레지스트리에서 `opx`/`opal-pilot-flex` 매칭 가능.
- [ ] **R9 배포 영향 반영** — install-mac.sh / windows.ps1 등 배포 스크립트에 신규 스킬·수정 op-* 동기화 필요 여부 검토 및 반영. AC: 신규 스킬이 배포 대상에 포함됨(또는 디렉토리 일괄 배포로 자동 포함됨이 확인됨).
- [ ] **R10 변경이력** — 신규 SKILL.md 변경이력 표 + 수정한 기존 문서(op-*, 레지스트리 등)에 행 추가 (일시 KST + 태스크 022).

## 제약 조건

- **배포 경계**: `~/.opal/` 직접 편집 금지. 프로젝트 소스(`opal/`, `skills/`, `scripts/`)만 수정 후 install로 배포 (`.opal/AGENT.md` §금지사항).
- **하드코딩 플랫폼 분기 금지**: Claude/Cursor/Gemini 분기는 어댑터 계층(install)에서만.
- **하네스 우회 금지**: opx 자체도 Guards/Gates/State 준수 — 특히 CLOSE 진입 게이트(사용자 승인 필수)와 STATE 직접 편집 금지(state-tool만).
- **단순성 우선**: 신규 실행 스킬을 만들지 않고 검증된 op-* 블록 재사용 (헌법 §2).
- **커밋 금지**: 캡틴 지시 — 다른 알투와 병행 작업 중이므로 본 태스크에서 커밋·스태시 수행 안 함.
- **재사용성**: opx는 특정 프로젝트 비의존 — 모든 OPAL 프로젝트에서 동작.

## 기술 스택

- OPAL 프레임워크 (Markdown 스킬 정의 + Python state-tool/brain-tool + bash install 스크립트). 별도 런타임 의존 없음.

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | opal-pilot-dev SKILL | `opal/skills/opal-pilot-dev/SKILL.md` | opd 파이프라인 구조 + STATE rows-spec 인에이블러 |
| D-2 | 설계 | opal-pilot-dev-short SKILL | `opal/skills/opal-pilot-dev-short/SKILL.md` | 경량 pilot 구조 참조 |
| D-3 | 설계 | op-task SKILL | `opal/skills/op-task/SKILL.md` | INTAKE 단계 기반 (조건부 인터뷰 연동) |
| D-4 | 설계 | interview SKILL | `skills/interview/SKILL.md` | 갭 보완 인터뷰 재사용 |
| D-5 | 설계 | opal-skill-creator SKILL | `opal/skills/opal-skill-creator/SKILL.md` | (4) 검토 대상 — 일반 스킬용 한계 확인 |
| D-6 | 설계 | opal-harness (공통/semi-agentic) | `opal/core/references/opal-harness.md`, `~/.opal/references/opal-harness-semi-agentic.md` | Guards/Gates/모드 경계 |
| D-7 | 설계 | 명확화 게이트 TASK (보류) | `tasks/005-260515-opp-clarification-gate-ssot/TASK.md` | INTAKE 델타 검증 발상 참조 |
| D-8 | 설계 | 스킬 레지스트리 | `opal/core/references/opal-skills-registry.json` | R8 등록 대상 |
