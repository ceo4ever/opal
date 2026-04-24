# TASK: Citation Rules 하네스 보편화 — 근거 제시 원칙 강화

> 작성일: 2026-04-24 | 작업 유형: 개선(아키텍처) | 적용 스킬: opp | 모드: agentic
> 입력: 캡틴 피드백 3건 + 대화에서 도출된 방향 전환
> 출력: 단일 태스크로 C-1~C-7 모두 완료 (SSOT + Trigger 패턴)

## 1. 작업 목표

citation-rules.md를 **"상상·추정 금지, 근거 제시 의무"의 하네스 SSOT**로 승격하고, OPAL의 모든 pilot(오케스트레이터) · PLAN/TASK/ANALYSIS 스킬 · QA 스킬이 이를 필수 적용하도록 구조를 정비한다.

설계 패턴은 **SSOT + Trigger**:
- **SSOT** — citation-rules.md 안에 모든 규칙(원칙·기준·방식·트랙 매트릭스·[MUST] 토큰·영역 간 검토·`decision_required` 계약)을 단일 진실 원천으로 정리
- **Trigger** — 관련 문서는 "citation-rules.md를 반드시 Read하고 준수하라"는 한 줄 트리거만 주입. 규칙 내용을 복제하지 않는다.

근거 유형은 트랙별 — 비개발 = 관련 문서 + 웹사이트, 개발 = 기획 산출물 + 설계 산출물 + 소스 코드.

## 2. 원칙 (캡틴 지시 핵심)

> **"citation-rules.md는 분석·설계 시에 의견이 어디에 근거를 두었는지 반드시 제시하게끔 해서 상상이나 추정을 못하게 하는 의도다. 이것은 반드시 pilot에 반영되어야 하는 중요한 하네스다. 비개발이면 관련 문서나 웹사이트 등을 적용해야 하고, 개발은 기획 산출물·설계 산출물·소스 코드까지 적용했으면 한다."** (2026-04-24 대화)

> **"citation-rules.md 문서에 인용 기준, 방식 등 SSOT를 모두 정리를 하고, 관련 문서에서는 이 문서를 반드시 트리거해서 지키게끔 하면 되는 것 아닌가?"** (2026-04-24 대화 — SSOT + Trigger 패턴 지시)

### 원칙 요약

| 원칙 | 내용 |
|------|------|
| **근거 제시 의무** | 모든 분석·설계 결정은 문서 근거(경로/URL + 섹션/줄번호)를 인용해야 한다. 상상·추정·기억 기반 기재 금지. |
| **트랙별 근거 유형** | 비개발 = 관련 문서 + 웹사이트. 개발 = 기획 산출물 + 설계 산출물 + 소스 코드. |
| **SSOT + Trigger** | 규칙 본체는 citation-rules.md에만. 관련 문서는 트리거 1줄로 참조. |
| **pilot 필수 적용** | 모든 pilot이 citation-rules를 필수 적용한다. 공통 하네스와 각 pilot SKILL.md에서 트리거 선언. |

## 3. 대화에서 도출된 의사결정 (타임라인)

| # | 시점 | 의사결정 | 근거 |
|---|------|--------|------|
| D-1 | 08:10 | 캡틴이 최근 프로젝트 피드백 3건을 공유 | (1) PLAN 필드명 snake_case/camelCase 가정 오류 (2) FE/BE 용어 불일치 (`userType` vs `subType`) (3) FE↔BE 통합 검증 사람 병목 |
| D-2 | 08:15 | 피드백 1·2 통합, 3은 분리 | 인용 의무 강화(1)가 용어 노출(2)을 자연스럽게 커버. E2E 자동화(3)는 별개 로드맵 |
| D-3 | 08:18 | 인용 의무 강화만으론 "능동 검출"이 부족함 확인 | 워커가 불일치를 자발적으로 §리스크에 기재하는 규칙 필요 |
| D-4 | 08:20 | `decision_required` 플래그 계약 도입 | 용어 통일은 도메인 결정 사안 — agentic이어도 사용자 에스컬레이션 필수 |
| D-5 | 08:25 | §리스크 섹션에 용어 불일치 기재 | "다름의 발견"은 리스크 성격 |
| D-6 | 08:40 | 범위 확장 필요성 제기 — 기획/설계 산출물 + ERD/IA 토큰 포함 | 캡틴 질문: "정책서·IA·ERD 근거 제시도 반영되나?" |
| D-7 | 08:43 | opwt 범위 외 / PLAN 계열(op-dev-plan, op-task-plan, op-sdd-plan) 동시 강화 | 역할 분리 존중 + 불균형 방지 |
| D-8 | 08:50 | **방향 전환**: consistency-rules 통합안 → citation-rules 하네스 보편화 | 캡틴 원칙 선언: 상상·추정 금지는 모든 pilot 필수 적용 하네스여야 함 |
| D-9 | 08:55 | 전체 로드맵 C-1~C-10 정립 (초기 안) | 규모 12~15 파일 |
| D-10 | 09:00 | β안 선택 — 2단계 분할 (130=C-1~C-4, 131=C-5~C-10) + 맥락 보존 장치 3종 | agentic Gate 루핑 리스크 관리 |
| D-11 | 09:10 | TASK.md를 전체 로드맵 + 대화 맥락 마스터 문서로 구성 | 캡틴 제안 — 후속 태스크가 맥락을 온전히 상속 |
| D-12 | 09:30 | **SSOT + Trigger 패턴 채택** — 캡틴 통찰로 설계 단순화 | citation-rules.md에 모두 정리, 관련 문서는 트리거 1줄만. C-5~C-9가 "트리거 1줄 주입"으로 단순화되어 β분할 이유 약화 |
| D-13 | 09:40 | **α안 전환** — 단일 태스크로 C-1~C-7 완료 | 파일 수(14~18개)는 많지만 각 파일 작업 단순(1줄 추가). 원샷 일관성 확보. Gate 루핑 리스크 오히려 감소 |
| D-14 | 09:42 | project 메모리 등재 없음 | 캡틴 결정 — 후속 태스크가 없고 본 TASK.md + citation-rules.md가 맥락 담체로 충분 |

## 4. 현황 분석 (Gap)

현 citation-rules.md는 이미 하네스 §2에서 로드되는 공통 규칙이다. 그러나 캡틴 지시 기준과 비교할 때 다음 Gap이 있다:

| 항목 | 현재 | Gap | 해결 대상 |
|------|------|-----|---------|
| 최상위 원칙 선언 | "인용 포맷"이 서두(§2) | ❌ "상상·추정 금지" 원칙이 명시적으로 없음 | C-1 |
| 개발/비개발 트랙 구분 | 없음 | ❌ 트랙별 근거 매트릭스 필요 | C-2 |
| 개발 트랙 [MUST] 토큰 | 포맷만 제시, 대상 미구체화 | ❌ 필드/시그니처/타입/ERD 컬럼/IA 화면 ID/정책 조항 등 구체 목록 부재 | C-3 |
| 영역 간 용어 불일치 검출 | 없음 | ❌ FE↔BE, 정책↔코드, ERD↔코드 검출 규칙 부재 | C-4 |
| decision_required 플래그 계약 | 없음 | ❌ 결정성 이슈 에스컬레이션 계약 부재 | C-4 |
| pilot 적용 의무 선언 | 일부 스킬(§1 테이블)만 명시 | ❌ 공통 하네스에 "모든 pilot 필수" 강제 선언 부족 | C-5 |
| 관련 문서 Trigger 참조 | 개별 스킬에 산발 | ❌ 통일된 "citation-rules §N 준수" 트리거 부재 | C-6 |
| 변경이력 | 단일 파일만 | ❌ 본 태스크로 변경되는 모든 파일 동기화 | C-7 |

## 5. 전체 로드맵 (C-1 ~ C-7 단일 태스크 마스터)

| # | 제목 | 내용 | 대상 |
|---|------|------|------|
| **C-1** | 근거 제시 원칙 [MUST] 선언 | citation-rules.md 서두에 "상상·추정·기억 기반 기재 금지" 원칙 선언 + 목적 재정의 | `opal/core/references/harness/citation-rules.md` |
| **C-2** | 개발/비개발 트랙 매트릭스 | 트랙별 필수 근거 유형 매트릭스 신설 (비개발 = 문서/웹 / 개발 = 기획+설계+소스) | `citation-rules.md` |
| **C-3** | 개발 트랙 [MUST] 토큰 구체화 | 필드명·함수 시그니처·타입명·ERD 컬럼명·IA 화면 ID/라우트·정책 조항 번호 + Good/Bad 예시 | `citation-rules.md` |
| **C-4** | 영역 간 용어 일관성 검토 + `decision_required` 계약 | 동일 개념 불일치 검출 규칙 + `decision_required` 플래그 스키마 정의 + 에스컬레이션 원칙 | `citation-rules.md` |
| **C-5** | 공통 하네스 pilot 적용 의무 선언 | opal-harness.md §2에 "모든 pilot/스킬/가이드/QA는 citation-rules 필수 적용" 선언 추가 | `opal/core/references/opal-harness.md` |
| **C-6** | 관련 문서에 Trigger 주입 | 각 pilot/PLAN 스킬/TASK·ANALYSIS 스킬/QA 스킬에 "citation-rules §N 준수" 트리거 1줄 추가 | 14~18 파일 (PLAN 워커가 정확 목록 확정) |
| **C-7** | 전 수정 파일 변경이력 갱신 | citation-rules.md + opal-harness.md + 14~18개 트리거 주입 파일 | 전 수정 파일 |

## 6. 단일 태스크 구조 (α안 + SSOT/Trigger)

### 병렬 디스패치 전략 (EXECUTE 단계)
파일군을 4개 그룹으로 나누어 **병렬 워커 디스패치**:

| 그룹 | 파일군 | 예상 파일 수 | 워커 |
|------|-------|-----------|------|
| G1 | citation-rules.md 본체 (C-1~C-4) | 1 | 독립 워커 (먼저 완료 필요) |
| G2 | opal-harness.md (C-5) | 1 | G1 완료 후 |
| G3a | pilot SKILL.md (C-6) | 8개 | 병렬 (G1 완료 후) |
| G3b | PLAN/TASK/ANALYSIS 스킬 (C-6) | 5~6개 | 병렬 (G1 완료 후) |
| G3c | QA 스킬 (C-6) | 2~3개 | 병렬 (G1 완료 후) |
| G4 | 변경이력 일괄 갱신 (C-7) | 전 수정 파일 | G1~G3 완료 후 |

하네스 §7 병렬 처리 원칙 + 파일 충돌 방지(동일 파일 단일 워커) 준수.

### 맥락 담체 설계
- citation-rules.md 본체에 **원칙 선언 + 트랙 매트릭스 + [MUST] 토큰 + 영역 간 검토 + decision_required 계약**을 구체 예시와 함께 모두 기재
- 본 TASK.md가 대화 맥락·의사결정 타임라인·Gap 분석을 담은 역사적 기록 역할
- 이 2개 파일만으로 규칙의 "무엇을·왜·어떻게" 완결

## 7. 요구사항 (R-1 ~ R-8)

### R-1 ~ R-5: citation-rules.md 본체 SSOT 완성 (C-1 ~ C-4)

대상 파일: `opal/core/references/harness/citation-rules.md`

- [x] **R-1** (C-1) 근거 제시 원칙 [MUST] 선언 신설
  - **무엇을**: 현 §1 앞 또는 §1.1에 "근거 제시 원칙" 섹션 신설. "상상·추정·기억 기반 기재 금지 — 모든 분석·설계 결정은 문서 근거(경로/URL + 섹션/줄번호)를 인용해야 한다"를 `[MUST]` 포맷으로 선언.
  - **AC**: citation-rules.md 최상단(또는 §1 직후)에 `[MUST]` 포맷 근거 제시 원칙 선언이 존재하고, 본 태스크 §2의 캡틴 원칙 요약과 일치한다.

- [x] **R-2** (C-2) 개발/비개발 트랙별 근거 매트릭스 추가
  - **무엇을**: 신설 §로 트랙별 필수 근거 매트릭스 추가. 행=트랙(비개발/개발), 열=근거 유형(문서/웹/기획 산출물/설계 산출물/소스 코드). 각 셀에 필수/선택/불필요 표기.
  - **AC**: 매트릭스 테이블이 존재하고, 개발 트랙(기획+설계+소스 "필수") / 비개발 트랙(문서+웹 "필수")이 명확히 구분되어 있다.

- [x] **R-3** (C-3) 개발 트랙 [MUST] 토큰 대상 구체화
  - **무엇을**: 개발 트랙에서 `[MUST]` 인용이 반드시 필요한 구체 토큰 유형 6종 나열 — (1) 필드명 (2) 함수 시그니처 (3) 타입명 (4) ERD 컬럼명 (5) IA 화면 ID/라우트 (6) 정책 조항 번호. 각 유형별 Good/Bad 예시 1쌍씩.
  - **AC**: 6종 토큰 유형이 모두 나열되고, 각 유형별 Good/Bad 예시 쌍이 최소 1개 존재. §2 기존 인용 포맷과 일관.

- [x] **R-4** (C-4) 영역 간 용어 일관성 검토 규칙 + `decision_required` 계약 스키마
  - **무엇을**: 신설 §로 "영역 간 용어 일관성 검토" 규칙 추가. 동일 개념이 서로 다른 영역(FE/BE, 정책/코드, ERD/코드 등)에서 다른 토큰으로 나타나면 워커가 능동 검출하여 산출물 §리스크 섹션에 기재할 의무. 검출 시 워커 반환 페이로드에 `decision_required: [{type: "terminology_mismatch", summary, tokens: [...], areas: [...]}]` 배열 포함. 하위 섹션에 (a) 검출 대상 영역 쌍 예시 (b) 산출물 §리스크 기재 포맷 예시 (c) `decision_required` JSON 스키마 (d) "결정성 이슈는 agentic 모드에서도 사용자 에스컬레이션 필수" 원칙 명시.
  - **AC**: 규칙이 존재하고, 검출 시 기재 포맷 + JSON 스키마 + 에스컬레이션 의무 원칙이 모두 명시. 예시 1개 이상.

- [x] **R-5** (C-7 일부) citation-rules.md 변경이력 갱신
  - **무엇을**: 변경이력 테이블에 2026-04-24, 태스크 130, v2.0 행 추가. 변경 요약: R-1~R-4 합성.
  - **AC**: 변경이력 최하단에 태스크 130 참조 행 존재.

### R-6 ~ R-8: 공통 하네스 선언 + Trigger 주입 + 변경이력 동기화 (C-5 ~ C-7)

- [x] **R-6** (C-5) opal-harness.md §2에 pilot 적용 의무 선언 추가
  - **무엇을**: opal-harness.md §2 "QA 산출물 표준 및 검증" 위/아래 또는 §2 내 별도 소섹션으로 **"Citation Rules 적용 의무"** 블록 추가. 내용: "모든 pilot(오케스트레이터) / PLAN·TASK·ANALYSIS 스킬 / QA 스킬은 각자 다루는 산출물의 작성·검증 시 `opal/core/references/harness/citation-rules.md`를 필수 Read하고 그 규칙을 준수한다. 이 의무는 interactive·agentic 모드 모두에 적용된다."
  - **대상**: `opal/core/references/opal-harness.md`
  - **AC**: opal-harness.md §2에 해당 블록이 존재하고, citation-rules.md 경로가 정확히 기재되며, interactive/agentic 양쪽에 적용됨을 명시한다.

- [x] **R-7** (C-6) 관련 문서에 Trigger 1줄 주입
  - **무엇을**: 아래 대상 파일 각각의 적절 위치(Harness/프로세스/검증 기준 섹션 등)에 다음 형태의 트리거 1줄 추가:
    ```
    > **[MUST]** 산출물 작성·검증 시 `opal/core/references/harness/citation-rules.md`를 Read하여 규칙(근거 제시 원칙 / 트랙별 매트릭스 / [MUST] 토큰 / 영역 간 용어 일관성 / decision_required 계약)을 준수한다.
    ```
  - **주입 위치 원칙**:
    - pilot SKILL.md: `## Harness` 섹션 하위 또는 각 단계 진입부
    - PLAN/TASK/ANALYSIS 스킬: `## 프로세스` Step 1 앞 또는 `실행 컨텍스트` 하위
    - QA 스킬: `## 검증 기준` 또는 `프로세스 Step 3 품질 검증` 하위
  - **대상 파일 (잠정 목록, PLAN 워커가 Glob으로 최종 확정)**:

    | 카테고리 | 파일 |
    |---------|------|
    | pilot | `opal/skills/opal-pilot-project/SKILL.md` |
    | pilot | `opal/skills/opal-pilot-project-dev/SKILL.md` |
    | pilot | `opal/skills/opal-pilot-dev/SKILL.md` |
    | pilot | `opal/skills/opal-pilot-dev-short/SKILL.md` |
    | pilot | `opal/skills/opal-pilot-dev-wireframe/SKILL.md` |
    | pilot | `opal/skills/opal-pilot-sdd/SKILL.md` |
    | pilot | `opal/skills/opal-pilot-write-tech/SKILL.md` |
    | pilot | `opal/skills/opal-pilot-gc/SKILL.md` |
    | PLAN 스킬 | `opal/skills/op-dev-plan/SKILL.md` |
    | PLAN 가이드 | `opal/skills/op-dev-plan/references/plan-guide.md` |
    | PLAN 스킬 | `opal/skills/op-task-plan/SKILL.md` |
    | PLAN 스킬 | `opal/skills/op-sdd-plan/SKILL.md` |
    | PLAN 스킬 | `opal/skills/op-sdd-action-plan/SKILL.md` |
    | TASK 스킬 | `opal/skills/op-task/SKILL.md` (존재 확인 필요) |
    | ANALYSIS 스킬 | `opal/skills/op-dev-analysis/SKILL.md` (존재 확인 필요) |
    | QA 스킬 | `opal/skills/op-dev-qa/SKILL.md` |
    | QA 가이드 | `opal/skills/op-dev-qa/references/qa-dev-guide.md` |
    | QA 스킬 | `opal/skills/op-task-qa/SKILL.md` (존재 확인 필요) |

  - **AC**: 실제 존재하는 각 대상 파일에 트리거 1줄이 정확한 경로와 함께 주입되어 있다. 누락 파일 0건.

- [x] **R-8** (C-7) 전 수정 파일 변경이력 갱신
  - **무엇을**: citation-rules.md + opal-harness.md + R-7로 수정한 모든 파일의 변경이력 테이블에 태스크 130 참조 행 추가.
  - **AC**: 모든 수정 파일의 변경이력에 2026-04-24, 태스크 130 행이 존재.

## 8. 제약 조건

- **[MUST]** `~/.opal/` 경로 직접 수정 금지. 모든 편집은 `opal/` 소스 경로에서만 수행. (확정 기준 §2)
- **[MUST]** 기존 citation-rules.md의 §2~§6 (포맷/적용/단계별 의무 수준 매트릭스/예외 규칙/사람·AI 탐색 가이드)은 **구조 보존**. 삽입·확장만 수행, 기존 섹션 삭제 금지 (하위호환).
- **[MUST]** R-7 트리거는 "규칙 내용 복제 금지, 참조만" 원칙 준수. 트리거 블록 안에 규칙의 구체 내용을 반복 기재하지 않는다.
- **[MUST]** R-7 대상 파일 중 존재하지 않는 파일은 스킵하고 QA Gate 보고에 기록. 해당 파일 존재 여부는 PLAN 단계에서 Glob으로 확정한다.
- `decision_required` 플래그는 citation-rules.md에 **스키마 + 에스컬레이션 원칙**까지만 정의. 각 pilot의 상세 Gate 처리 로직은 본 태스크 범위에서는 트리거 참조로 충분 (각 pilot이 citation-rules를 Read하면 자동으로 규칙을 알게 됨).
- 변경이 opal-harness.md §2 Lazy 로드 모듈 기재와 충돌 없어야 한다.

## 9. 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | 본 태스크 SSOT 본체 |
| D-2 | 설계 | opal-harness.md | `opal/core/references/opal-harness.md` | §2 Citation Rules 선언 + pilot 적용 의무 추가 대상 |
| D-3 | 소스 | opwt consistency-rules.md | `opal/skills/opal-pilot-write-tech/references/consistency-rules.md` | §3 용어 일관성 참조 (구조 설계 힌트) |
| D-4 | 소스 | op-dev-plan plan-guide | `opal/skills/op-dev-plan/references/plan-guide.md` | 현재 인용 규칙 적용 형태 확인 |
| D-5 | 소스 | op-task-plan SKILL.md | `opal/skills/op-task-plan/SKILL.md` | citation-rules 적용 대상 스킬 |
| D-6 | 소스 | op-sdd-plan SKILL.md | `opal/skills/op-sdd-plan/SKILL.md` | 트리거 주입 대상 확인 |
| D-7 | 설계 | opal-harness-agentic.md §6 | `~/.opal/references/opal-harness-agentic.md` | decision_required 에스컬레이션 정합성 확인 |
| D-8 | 기획 | 캡틴 피드백 3건 + 원칙 선언 | 대화 로그 2026-04-24 | 요구사항 원출처 |

## 10. 성공 기준

- [ ] citation-rules.md에 근거 제시 원칙이 `[MUST]` 포맷으로 서두에 선언 (R-1)
- [ ] 개발/비개발 트랙별 근거 매트릭스 존재 (R-2)
- [ ] 개발 트랙 `[MUST]` 토큰 6종 Good/Bad 예시 포함 (R-3)
- [ ] 영역 간 용어 일관성 검토 규칙 + `decision_required` 계약 스키마 + 에스컬레이션 원칙 모두 기재 (R-4)
- [ ] citation-rules.md 변경이력 갱신 (R-5)
- [ ] opal-harness.md §2에 Citation Rules 적용 의무 블록 존재 (R-6)
- [ ] R-7 대상 파일(PLAN 단계에서 확정)에 트리거 1줄 정확히 주입, 누락 0건 (R-7)
- [ ] 전 수정 파일 변경이력에 태스크 130 참조 행 존재 (R-8)
- [ ] citation-rules.md 기존 섹션 구조 보존 — 하위호환 유지
- [ ] 트리거 블록에 규칙 내용이 복제되어 있지 않음 — SSOT 원칙 준수
