# TASK: Artifact Gate 설계 및 적용

> 작성일: 2026-04-06 | 작업 유형: 개선 | 적용 스킬: opp | 모드: interactive
> 입력: 메모리 #8 (feedback_artifact_gate.md) + 사전 대화
> 출력: 하네스 및 오케스트레이터 SKILL.md 변경

## 작업 목표

QA Gate 완료의 증거(산출물 파일)가 없으면 다음 단계 진입을 구조적으로 차단하는 **Artifact Gate** 메커니즘을 하네스와 각 오케스트레이터에 적용한다.

## 배경

알투(PM)가 하네스 프로세스(QA Gate → PM Gate 등)를 규칙으로 정의해도 실제로 빠뜨리는 일이 반복되고 있다. 근본 원인은 LLM 특성상 컨텍스트에서 규칙이 밀려나 의도 없이 스킵하는 구조적 문제다. "규칙 준수를 의지가 아닌 구조로 강제"하기 위해 산출물 파일 존재 여부를 게이트 진입 조건으로 명문화한다.

## 확정된 설계 방향 (대화에서 합의)

1. **Artifact Gate 위치**: QA Gate 완료 후 PM Gate 진입 전
2. **강제 조건**: QA 산출물 파일(예: `QA-PLAN.md`, `QA-EXECUTE.md`)이 존재하지 않으면 PM Gate 및 DONE.md 생성 단계 진입 불가
3. **적용 범위**:
   - `opal-harness-interactive.md` — Artifact Gate 규칙 추가 (§2 QA Gate 또는 §3 PM Gate)
   - `opal-harness-agentic.md` — 동일 규칙 추가
   - 각 오케스트레이터 SKILL.md — 단계별 필수 산출물 명세 추가 (공통화 또는 인라인)
4. **자가 점검 프롬프트**: 게이트 진입 시 산출물 존재 여부를 출력하여 오케스트레이터가 스스로 확인

## 요구사항

- [ ] **Artifact Gate 규칙 추가 — opal-harness-interactive.md**
  - 무엇을: QA Gate 완료 시 산출물 파일 존재 여부를 확인하는 Artifact Gate 규칙을 추가한다
  - 어디에: `opal/core/references/opal-harness-interactive.md` → §2 QA Gate 또는 §3 PM Gate 사이
  - 왜: 확정 방향 §1, §2
  - AC: PM Gate 진입 조건에 "QA 산출물 파일이 존재해야 한다"는 규칙이 명시되고, 파일 부재 시 동작(QA 재소환 또는 진입 차단)이 기술되어 있다

- [ ] **Artifact Gate 규칙 추가 — opal-harness-agentic.md**
  - 무엇을: interactive와 동일한 Artifact Gate 규칙을 agentic 모드에도 추가한다
  - 어디에: `opal/core/references/opal-harness-agentic.md` → QA Gate / PM Gate 관련 섹션
  - 왜: 확정 방향 §1, §2
  - AC: agentic 모드에서도 QA 산출물 파일 부재 시 자율 게이트 통과가 차단됨이 명시되어 있다

- [ ] **필수 산출물 명세 추가 — 오케스트레이터 SKILL.md (공통 또는 인라인)**
  - 무엇을: 각 단계(PLAN, EXECUTE)별 QA Gate 완료를 증명하는 필수 산출물 파일명을 명세한다
  - 어디에: `opal/core/references/opal-harness.md` 공통 섹션 또는 각 오케스트레이터 SKILL.md (opp, opds, opd, opwt, opsdd)
  - 왜: 확정 방향 §3
  - AC: 각 오케스트레이터(또는 하네스 공통)에서 "PLAN QA 산출물: QA-PLAN.md", "EXECUTE QA 산출물: QA-EXECUTE.md" 형식으로 필수 파일이 명시되어 있다

- [ ] **자가 점검 프롬프트 추가**
  - 무엇을: 게이트 진입 시 "필수 산출물 파일이 존재하는가?" 자가 점검 항목을 추가한다
  - 어디에: 하네스 Artifact Gate 규칙 내
  - 왜: 확정 방향 §4
  - AC: 게이트 진입 절차에 산출물 파일 존재 여부를 확인하는 단계가 포함되어 있고, 파일 존재 시 / 부재 시 동작이 각각 명시되어 있다

- [ ] **opwt ANALYSIS 단계 PM Gate 추가**
  - 무엇을: ANALYSIS 완료 후 사용자 확인 전에 PM Gate를 추가한다
  - 어디에: `opal/skills/opal-pilot-write-tech/SKILL.md` → ANALYSIS 단계 게이트 절차
  - 왜: 현재 "사용자 확인"만 있고 PM 검토 기준 체크가 빠져 있음. 다른 스킬의 ANALYSIS 단계(opd 등)와 일관성 확보
  - AC: opwt ANALYSIS 게이트 절차에 "QA Gate → PM Gate → 사용자 확인" 순서가 명시되어 있다

- [ ] **opwt EXECUTE 배치 "PM 검토" → PM Gate 명확화**
  - 무엇을: EXECUTE 배치 완료 후 "PM 검토"를 "PM Gate"로 명확화하고 하네스 §3 참조를 추가한다
  - 어디에: `opal/skills/opal-pilot-write-tech/SKILL.md` → EXECUTE 단계 배치 완료 게이트 절차
  - 왜: "PM 검토"라는 표기가 하네스 §3 PM Gate 절차(체크리스트 갱신 확인 등)와 동일하게 동작하는지 불명확
  - AC: EXECUTE 배치 게이트 절차가 "QA Gate → **PM Gate** (체크리스트 갱신 상태 확인 — 하네스 §3 참조)" 형식으로 명시되어 있다

## 제약 조건

- `~/.opal/` 경로 직접 수정 금지 — 소스는 `opal/core/references/` 및 `opal/skills/` 에서 수정한다 (확정 기준 #2)
- 커뮤니티 스킬 원본 수정 금지
- 하네스 변경은 모든 오케스트레이터에 영향하므로 파급 범위를 PLAN에서 사전 분석한다

## 기술 스택

- Markdown (문서 프레임워크)

## 관련 문서

- `.opal/memory/feedback_artifact_gate.md` — 문제 정의 및 해결 방향
- `opal/core/references/opal-harness.md` — 공통 하네스
- `opal/core/references/opal-harness-interactive.md` — interactive 서브 하네스
- `opal/core/references/opal-harness-agentic.md` — agentic 서브 하네스
- `opal/skills/opal-pilot-project/SKILL.md` — opp 오케스트레이터
- `opal/skills/opal-pilot-dev-short/SKILL.md` — opds 오케스트레이터
- `docs/CONVENTIONS.md` — 코드 및 문서 컨벤션
