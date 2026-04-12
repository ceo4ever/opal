# QA: PLAN — 알투 역할 전환 규칙 + 태스크 추가작업 프로세스 정의

> 검토일: 2026-04-05 | 판정: Needs Revision

## 1. 요약

AGENT.md, opal-harness.md, op-task/SKILL.md 3개 파일을 수정하여 역할 전환 규칙(A 그룹), 추가작업 프로세스(B 그룹), TASK.md 작성 프로세스 개선(C 그룹)을 반영하는 계획이다. 실행 순서는 B → A → C이며, B(하네스)가 A(에이전트)에서 참조하는 추가작업 프로세스를 먼저 정의하는 의존성 근거가 명확하다. 핵심 설계에 각 변경 사항의 삽입 위치, 내용 예시, 변경 근거가 구체적으로 기술되어 있어 EXECUTE 워커가 즉시 실행 가능한 수준이다. 단, B4-AC3(각 SKILL.md 개별 수정)을 범위 밖으로 처리했으나 TASK.md AC가 이를 요구하고 있어 EXECUTE 단계에서 미충족으로 판정될 위험이 있다. 또한 B4-AC2의 스킬 목록이 TASK.md와 PLAN.md 간 일치하지 않는다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| GP-1 | 즉시 실행 가능성 | Pass | 파일 변경 계획, 핵심 설계, 실행 체크리스트, QA 체크리스트 모두 완비 |
| GP-2 | 의존성 순서 | Pass | B → A → C 순서 및 근거 명확히 명시됨 |
| GP-3 | TASK 반영 | Warning | B4-AC3 범위 제외 처리 → EXECUTE 단계 미충족 위험 (아래 상세) |
| GP-4 | 파일 목록 완전성 | Pass | 3개 변경 파일이 TASK.md 관련 문서 목록과 정확히 일치 |
| GP-5 | 설계 구체성 | Pass | 각 항목마다 삽입 위치, 마크다운 예시, 필드 정의 포함 |
| GP-6 | 체크리스트 커버리지 | Warning | B4-AC2 스킬 목록 불일치 — TASK는 `opsdd` 포함, PLAN은 `opds`로 기재 (아래 상세) |

## 3. 지적 사항

### [Warning] B4-AC3 범위 이탈 — EXECUTE 단계 미충족 위험

**심각도**: Warning

**근거**:
- TASK.md B4-AC3: "각 SKILL.md에서 하네스 추가작업 섹션을 참조하는 가이드가 명시되어 있다"
- PLAN.md §핵심 설계 Step 1 B4: "각 SKILL.md 개별 수정은 향후 태스크로 분리. 이번 태스크에서는 하네스 중심으로 정의"

**문제**: TASK.md AC가 각 SKILL.md 수정을 명시적으로 요구하는데, PLAN이 이를 범위 밖으로 처리했다. EXECUTE 단계에서 QA가 B4-AC3을 검증하면 Fail 처리될 수 있다.

**권장 조치**: TASK.md B4-AC3을 "하네스에 오버라이드 테이블과 각 SKILL.md 수정 가이드가 명시되어 있다"로 완화하거나, 향후 태스크 분리 사실을 TASK.md 미확정 사항에 명시하면 EXECUTE 단계에서 혼선을 방지할 수 있다. 단, 현 PLAN의 §5 리스크 항목에 이 결정이 이미 인식되어 있으므로 PM이 수용 판단을 내리면 진행 가능.

---

### [Warning] B4-AC2 스킬 목록 불일치 (TASK vs PLAN)

**심각도**: Warning

**근거**:
- TASK.md B4-AC2: "스킬별 검증 차이 테이블(**opp/opds/opsdd**/opwt)이 하네스에 존재한다" — `opsdd` 포함
- PLAN.md §핵심 설계 B4 테이블: `opp / opds / opd / opwt` — `opsdd` 없음, `opd` 있음

**문제**: TASK AC 기준으로는 `opsdd` 스킬이 테이블에 있어야 통과하나, PLAN 설계에는 `opd`로 기재되어 정합성 불일치. EXECUTE 워커가 어느 목록을 따를지 혼선 발생 가능.

**권장 조치**: TASK.md B4-AC2의 스킬 목록을 PLAN과 일치시키거나(opp/opds/opd/opwt), PLAN의 테이블에 `opsdd`를 추가하여 정합성을 맞춘다.

---

### 심각도 분류

- Critical: 없음
- Warning: 2건 (B4-AC3 범위 이탈, B4-AC2 스킬 목록 불일치)
- Info: 없음

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md — A 그룹 (A1~A4) | PLAN §핵심 설계 Step 2에서 A1~A4 전 요구사항 커버 여부 | Pass |
| TASK.md — B 그룹 (B1~B5) | PLAN §핵심 설계 Step 1에서 B1~B5 전 요구사항 커버 여부 | Warning (B4-AC3 범위 제외) |
| TASK.md — C 그룹 (C1~C3) | PLAN §핵심 설계 Step 3에서 C1~C3 전 요구사항 커버 여부 | Pass |
| TASK.md — 미확정 사항 #2 (PM 전환 제안 문구) | PLAN에서 구조/문구 확정 여부 | Pass (핵심 설계 A2에서 구체적 문구 예시 확정) |
| TASK.md — 미확정 사항 #3 (ADD_DONE.md 세부 구조) | PLAN에서 필드 정의 확정 여부 | Pass (핵심 설계 B2에서 6개 필드 정의) |
| TASK.md — 제약 조건 (배포 금지) | PLAN이 소스 파일만 수정 계획인지 | Pass (신규 생성 없음, 3개 소스 파일만 수정) |

## 5. 판정

**Needs Revision**

Critical 항목은 없으나 Warning 2건이 존재한다. B4-AC2 스킬 목록 불일치는 EXECUTE 워커의 구현 혼선을 유발할 수 있고, B4-AC3 범위 이탈은 EXECUTE QA 단계에서 예상치 못한 Fail 판정으로 이어질 수 있다. 두 항목 모두 PM이 간단히 조정(TASK.md AC 수정 또는 PLAN 테이블 보정)하면 해소 가능한 수준이므로, 조치 후 EXECUTE 진행을 권장한다.
