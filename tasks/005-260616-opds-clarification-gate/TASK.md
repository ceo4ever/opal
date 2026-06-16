# TASK: 명확화 게이트 — TASK 4요소 잠금 기계적 집행 (재스코핑)

> 작성일: 2026-06-16 | 작업 유형: 신규 | 적용 스킬: opds | 모드: semi-agentic
> 입력: 캡틴 요청(005 재스코핑·재개) + 재스코핑 분석
> 출력: TASK.md

## 작업 목표

알투가 TASK 단계에서 목표·범위·제약·완료기준(4요소)을 추정으로 진행하는 패턴을, **prose 권고가 아니라 state-tool 게이트로 기계적으로 차단**한다. TASK.md에 4요소가 잠기지 않으면 다음 단계(PLAN) 진입을 도구가 거부한다.

## 배경

PRINCIPLES.md §1은 "가정 표면화 / 완료기준 선확정"을 always-on 원칙으로 규정하나 **집행 장치가 없다**. 헌법 Core Stance가 *"Enforce, don't just advise — 규칙이 항상 성립해야 하면 prose가 아니라 tool이 gate한다"* 고 못박는데, 명확화만 prose에 머문다. 이 공백을 메운다.

## 배경 분석 (대화에서 도출 — 원안 005 재스코핑)

원안(005, 2026-05-15, opp)은 헌법 신설 전 설계로 다음이 현재 기준 stale/중복:
- 소크라테스식 1문1답 인터뷰(원 R-5) → **AskUserQuestion이 이미 "1질문+옵션+(권고)+이유"를 강제** → 제거
- `reporting-template.md` 참조(원 D-3) → **삭제됨(015)**, AGENT.md 인라인 → 제거
- 6개 단계 SKILL prose 의무화(원 R-4) → advisory·분산. TASK 전환 게이트 1점으로 기계적 대체 → 축소

**진짜 공백 = TASK 4요소 잠금의 기계적 검증.** state-tool은 이미 task 013에서 `verify` 서브커맨드(--red-check)로 동작증거를 집행하는 선례가 있어, 동형으로 `--clarification-check`를 추가한다.

## 확정된 설계 방향 (대화에서 합의 — A안: 기계적 게이트)

| # | 항목 | 결정 |
|---|------|------|
| 1 | 집행 방식 | state-tool `verify --clarification-check` 신설 (prose 아님) |
| 2 | 검증 대상 | TASK.md "## 명확화 결과" 섹션 4요소(목표/범위/제약/완료기준) 잠금 여부 |
| 3 | 발동 지점 | TASK 단계 → 다음 단계 첫 행 advance/mark 시 자동 훅 (close_gate 동형) |
| 4 | 미충족 시 | 비정상 exit + 에러코드 `clarification_gate_unmet`, 다음 단계 진입 거부 |
| 5 | 원칙 출처 | PRINCIPLES §1 참조 (재서술 금지). harness §1 Guards엔 참조 1줄만 |
| 6 | 적용 파이프라인 | TASK 단계를 가진 전 pilot(opp/opd/opds/opdw) 공통 |

## 요구사항

- [ ] **R-1**: state-tool `verify --clarification-check` 모드 신설
  - 어디에: `opal/core/tools/state-tool/` (verify 서브커맨드 확장) + 테스트
  - 왜: 확정 #1 — 기계적 집행
  - AC: `verify <task> --clarification-check` 호출 시 TASK.md "## 명확화 결과" 섹션의 4요소(목표/범위/제약/완료기준) 각 항목이 확정값으로 채워졌으면 `{"ok": true}` exit 0, 하나라도 비었거나 섹션/파일 부재면 `{"ok": false, "error": "clarification_gate_unmet", ...}` 비정상 종료. 단위 테스트(채워짐 PASS / 누락 FAIL / 섹션부재 FAIL)가 통과한다.

- [ ] **R-2**: op-task TASK.md 템플릿에 "## 명확화 결과" 섹션 추가
  - 어디에: `opal/skills/op-task/SKILL.md` STEP 4 템플릿
  - 왜: 확정 #2 — 게이트 검증 대상 산출물 표준화
  - AC: 템플릿에 "## 명확화 결과" 섹션이 "확정된 설계 방향" 직후 추가되고, 4요소(목표/범위/제약/완료기준)별 `확정값 / 미확정(있으면) / 의존 사실` 열을 가진 표가 존재한다. 각 요소는 확정값 또는 명시적 "N/A: <사유>"로 채운다(공란·TBD 금지).

- [ ] **R-3**: TASK→다음 단계 전환 자동 훅
  - 어디에: `opal/core/tools/state-tool/` (advance 또는 mark의 TASK 단계 완료 시점 훅)
  - 왜: 확정 #3·#4 — 진입 차단 자동화
  - AC: TASK 단계의 마지막 필수 행이 done이 된 뒤 다음 단계(PLAN 등) 첫 행 advance/mark를 시도할 때, 도구가 clarification-check를 자동 실행하여 미충족이면 `clarification_gate_unmet` 에러로 거부한다(close_gate 동형, agentic `--auto-pass`도 거부). 충족 시 정상 진행. 단위 테스트로 거부/통과를 검증한다.

- [ ] **R-4**: 원칙 참조 연결 (재서술 금지)
  - 어디에: `opal/core/references/opal-harness.md` §1 Guards
  - 왜: 확정 #5 — 헌법 §1의 tool 집행 지점 명시
  - AC: §1 Guards에 "명확화 게이트(PRINCIPLES §1 집행) — TASK 4요소 미잠금 시 다음 단계 진입 불가, state-tool `--clarification-check`가 집행" 취지 1~2줄과 ERROR_CODES `clarification_gate_unmet` 참조가 추가된다. PRINCIPLES §1 문구를 복제하지 않는다.

- [ ] **R-5**: 변경이력 + 배포
  - 어디에: 수정 대상 파일 변경이력 표 + install 재배포(state-tool/op-task → `~/.opal/`)
  - 왜: 프로젝트 변경이력 의무 + 배포 경계
  - AC: 변경 파일에 (일시 KST + 태스크 005 참조) 행 추가. install로 `~/.opal/tools/state-tool/`·`~/.opal/skills/op-task/` 재배포 후 실호출 검증.

## 제약 조건

- **배포 경계 준수**: `~/.opal/` 직접 편집 금지 — 프로젝트 소스(`opal/core/tools/`, `opal/skills/`, `opal/core/references/`)만 수정 후 install 재배포 (`feedback_deploy_boundary`).
- **하네스 SSOT 준수**: 하네스 변경은 `opal/core/references/opal-harness.md` SSOT에서만, 발췌·복제 금지.
- **원칙 재서술 금지**: PRINCIPLES §1을 복제하지 않고 참조만 (헌법 Governance: lower docs reference, not restate).
- **state-tool 선례 정합**: task 013 `verify --red-check` 구조·ERROR_CODES 패턴을 따른다(신규 패턴 도입 최소화, Simplicity First).
- **기존 동작 회귀 금지**: 기존 state-tool 테스트 전체 통과 유지. 게이트는 "명확화 결과" 섹션이 있는 신규 TASK에만 발동하되, 섹션 부재 기존 태스크 회귀 영향은 PLAN에서 하위호환 정책으로 명시한다.

## 기술 스택

- Python 3 (state-tool, pytest) — `opal/core/tools/state-tool/`
- Markdown / YAML (op-task SKILL.md, opal-harness.md)

## 관련 문서

| # | 유형 | 문서 | 경로 | 참조 이유 |
|---|------|------|------|----------|
| D-1 | 헌법 | PRINCIPLES.md §1 | `opal/core/PRINCIPLES.md` | 집행 대상 원칙(재서술 금지, 참조만) |
| D-2 | 선례 | task 013 산출물 | `tasks/013-260607-opds-state-tool-enforcement/` | `verify --red-check`·ERROR_CODES 구조 선례 |
| D-3 | 소스 | state-tool | `opal/core/tools/state-tool/` | R-1·R-3 대상 |
| D-4 | 소스 | op-task SKILL | `opal/skills/op-task/SKILL.md` | R-2 대상 |
| D-5 | 설계 | opal-harness SSOT | `opal/core/references/opal-harness.md` | R-4 대상(§1 Guards) |
| D-6 | 폐기참조 | 원안 005 TASK | (본 파일 이전 버전) | 재스코핑 전 설계 — 흡수/축소 근거 |

## 명확화 결과

> 본 태스크는 명확화 게이트를 도입하는 태스크이므로, 스스로 4요소를 잠가 dogfooding한다.

| 요소 | 확정값 | 미확정 | 의존 사실 |
|------|--------|--------|----------|
| 목표 | TASK 4요소 잠금을 state-tool 게이트로 기계 집행 (prose 아님) | - | PRINCIPLES §1 "lock acceptance criteria"가 미집행 상태 |
| 범위 | state-tool `--clarification-check` + 자동 훅 + op-task 템플릿 "명확화 결과" 섹션 + harness §1 참조 1줄 (R-1~R-5). 인터뷰 재작성·6 SKILL 의무화·델타 템플릿 제외 | 기존 태스크(섹션 부재) 하위호환 발동 정책 = PLAN에서 확정 | AskUserQuestion이 소크라테스 인터뷰를 이미 대체 |
| 제약 | 배포 경계·하네스 SSOT·원칙 재서술 금지·013 패턴 정합·회귀 금지 | - | task 013 verify 선례 존재 |
| 완료기준 | R-1~R-5 AC 충족 + state-tool 신규 단위테스트 통과 + 기존 회귀 0 + install 재배포 실호출 검증 | - | RED-first 트랙(게이트 로직=self-confirming 위험) |
