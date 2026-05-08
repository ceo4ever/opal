# PLAN: PM Gate 컨벤션 자동 진단 — opal-convention-checker 영역별 병렬 디스패치

> 작성일: 2026-05-08
> 입력: TASK.md
> 출력: PLAN.md

## 1. 현황 조사

### 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | pm-review-gate.md | `opal/core/references/harness/pm-review-gate.md` | PM Gate 검토 절차 SSOT — §13 신설 대상 (TASK.md D-1) |
| D-2 | 설계 | opal-convention-checker AGENT.md | `opal/agents/opal-convention-checker/AGENT.md` | §입력 명세 + Phase 5 보고서 파일명 규약 갱신 대상 (TASK.md D-2) |
| D-3 | 설계 | context-injection.md | `opal/core/references/pm/context-injection.md` | "## 프로젝트 구성" prefix 매칭 라우팅 의사코드 — §13 영역 분할에서 재사용 (TASK.md D-3) |
| D-4 | 설계 | conventions-hub-model.md | `opal/core/references/conventions-hub-model.md` | 허브+링크 모델 + 단일 문서 프로젝트 분기 근거 (TASK.md D-4) |
| D-5 | 설계 | dispatch-process.md | `opal/core/references/pm/dispatch-process.md` | 인용 의무 규칙 — 본 태스크는 참고만, 변경 대상 아님 (TASK.md D-5) |
| D-6 | 설계 | opal-plan-agent AGENT.md | `opal/agents/opal-plan-agent/AGENT.md` | PLAN 에이전트 자체 로드 명세 — 사전 주입 갭 근거 (TASK.md D-6) |
| D-7 | 설계 | opp SKILL.md | `opal/skills/opal-pilot-project/SKILL.md` | EXECUTE PM Gate 호출 시점 + PM Gate 점검 목록 갱신 검토 대상 (TASK.md D-7) |
| D-8 | 설계 | docs/PROJECT.md | `docs/PROJECT.md` | OPAL 자체 "## 프로젝트 구성" 단일 요소 — 영역 분할 폴백 검증 (TASK.md D-8) |
| D-9 | 설계 | docs/CONVENTIONS.md | `docs/CONVENTIONS.md` | OPAL 컨벤션 SSOT — 단일 문서 모델 동작 검증 (TASK.md D-9) |
| D-10 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | PLAN.md 작성 인용 규칙 — `[MUST]` 포맷·참조 테이블 스키마 |
| D-11 | 설계 | opd SKILL.md | `opal/skills/opal-pilot-dev/SKILL.md` | PM Gate 점검 목록 보유 — R-8 갱신 검토 대상 |
| D-12 | 설계 | opds SKILL.md | `opal/skills/opal-pilot-dev-short/SKILL.md` | PM Gate 점검 목록 보유 — R-8 갱신 검토 대상 |
| D-13 | 설계 | opdw SKILL.md | `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | PM Gate 점검 목록 보유 — R-8 갱신 검토 대상 (코드 변경 가능성 있음) |
| D-14 | 설계 | oppd SKILL.md | `opal/skills/opal-pilot-project-dev/SKILL.md` | 메타 오케스트레이터 — PM Gate 점검 목록 부재 확인 → R-8 적용 불가 |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §3.1 참조. 유형: `설계`로 일관 (모두 OPAL 프레임워크 내부 설계 문서).

### 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/core/references/harness/pm-review-gate.md` | PM Gate 검토 절차 SSOT | 수정 (§검토 절차 §13 신설) | `pm-review-gate.md:18-46` (현재 1~12 항목 정의) |
| `opal/agents/opal-convention-checker/AGENT.md` | 컨벤션 체커 에이전트 정의 | 수정 (§입력 명세 + Phase 5 파일명 규약) | `opal-convention-checker/AGENT.md:21-33` (입력 명세 7개 파라미터), `:132-156` (Phase 5 보고서) |
| `opal/skills/opal-pilot-project/SKILL.md` | opp 오케스트레이터 | 수정 (§PM Gate 점검 목록에 EXECUTE Phase 산출물 추가) | `opal-pilot-project/SKILL.md:168-174` (현재 PM Gate 점검 목록 표) |
| `opal/skills/opal-pilot-dev/SKILL.md` | opd 오케스트레이터 | 수정 (§PM Gate 점검 목록 EXECUTE 행 신설/보강) | `opal-pilot-dev/SKILL.md:265-272` (현재 PM Gate 점검 목록 표 — EXECUTE 행 부재) |
| `opal/skills/opal-pilot-dev-short/SKILL.md` | opds 오케스트레이터 | 수정 (§PM Gate 점검 목록 EXECUTE 행 신설/보강) | `opal-pilot-dev-short/SKILL.md:262-267` (현재 PM Gate 점검 목록 표 — EXECUTE 행 부재) |
| `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | opdw 오케스트레이터 | 수정 (§PM Gate 점검 목록 EXECUTE 행 산출물 컬럼 추가) | `opal-pilot-dev-wireframe/SKILL.md:215-220` (현재 EXECUTE 행 산출물 = QA-EXECUTE.md만) |
| `opal/skills/opal-pilot-project-dev/SKILL.md` | oppd 메타 오케스트레이터 | 변경 없음 (Phase 1~3 구조는 PM Gate 점검 목록 섹션 부재 — `grep -n "PM Gate 점검 목록"` 결과 없음) | `opal-pilot-project-dev/SKILL.md` 헤더 목록 691줄까지 해당 섹션 없음 |
| `opal/core/references/pm/context-injection.md` | 영역 라우팅 의사코드 SSOT | 변경 없음 (참조만) | `context-injection.md:60-86` (라우팅 절차 + 의사코드 + 폴백) |
| `opal/core/references/conventions-hub-model.md` | 허브+링크 모델 규약 | 변경 없음 (참조만) | `conventions-hub-model.md:38-94` (체이닝 흐름 + 예시 B 단일 문서 프로젝트) |
| `docs/PROJECT.md` | 프로젝트 구성 SSOT (단일 요소) | 변경 없음 (검증용) | `docs/PROJECT.md:74-80` (단일 요소 Framework × opal-task-agent) |

### 현재 상태

#### 1) PM Gate 검토 절차 (D-1)

`pm-review-gate.md:18-46`는 12개 항목으로 구성된다. 11번 "docs/ 무효화 체크"와 12번 "STATE.md 정합성 자동 검증(state validate)"까지 정의되어 있으며 13번 항목은 부재. 항목 8번(`@header` 검증), 12번(state validate)이 자동 검증 항목의 선례로 존재 — 13번 신설 시 동일한 "트리거 조건 / 호출 명령 / 결과 처리 / 근거" 4단 포맷으로 일관 작성 가능.

판정 섹션(`pm-review-gate.md:71-76`)은 Pass / Fail / Fail(영역 침범) / `.opal/AGENT.md` 미존재 시 4종으로 정의되어 있다. R-7 하위 호환은 4번째 항목과 동일한 결로 §13에 명시 가능.

#### 2) opal-convention-checker (D-2)

`opal-convention-checker/AGENT.md:21-33`의 입력 명세는 7개 파라미터(`task_folder` / `target_files` / `timestamp` / `checklist_path` / `template_path` / `project_root` / `scope`). PM Gate 호출 시 PM이 어떤 값을 어떻게 매핑하는지(특히 `target_files = changed_files`, `scope = 영역명 또는 "all"`) 명시가 부재.

`opal-convention-checker/AGENT.md:132-156` Phase 5는 단일 보고서 `GC-CONVENTION-{timestamp}.md`만 정의. 영역별 다중 보고서 시나리오에서 파일명 충돌을 방지하는 규약이 없다. `Phase 5:134`의 보고서 경로 한 줄과 `Phase 6:160-167`의 결과 반환 JSON `artifact_path`/`changed_files` 두 곳을 함께 갱신해야 하는 의존성이 존재한다.

#### 3) 영역 라우팅 (D-3)

`context-injection.md:60-86`는 "## 프로젝트 구성" 섹션 파싱 → 가장 긴 prefix 매칭 → 매칭 실패 시 `opal-task-agent` 폴백을 정의. 의사코드 형식(파이썬)으로 명세되어 있어 §13에서 그대로 인용 가능. opgc SCAN 동적 분할이 이미 동일 규약을 재사용하고 있어(D-3 §opgc SCAN 동적 분할 연계) PM Gate에서도 동일 재사용 합리적.

#### 4) 허브+링크 모델 + 단일 문서 분기 (D-4)

`conventions-hub-model.md:38-94`는 체이닝 흐름 4단계 + 예시 B "단일 문서 프로젝트(OPAL 자체 포함)"를 명시. `scope` 미지정 또는 `all` → 허브 전체 적용으로 OPAL 자체에서도 동작 보장. 따라서 본 태스크의 동작 검증은 OPAL 자체에서 가능하지만 영역 분할 효과는 풀스택 프로젝트에서만 검증 가능하다는 영역 한계 명시 필요.

#### 5) 오케스트레이터 PM Gate 점검 목록 (D-7, D-11~D-14)

| 스킬 | 현재 EXECUTE 행 산출물 | EXECUTE Phase 존재 여부 | 비고 |
|-----|---------------------|----------------------|------|
| opp (D-7) | `EXECUTE: QA-EXECUTE.md` | O | EXECUTE 컬럼에 컨벤션 보고서 추가 가능 |
| opd (D-11) | EXECUTE 행 부재 | O (STEP 4 EXECUTE) | EXECUTE 행 신설 후 컨벤션 보고서 포함 — `opal-pilot-dev/SKILL.md:265-272` |
| opds (D-12) | EXECUTE 행 부재 | O (STEP 4 EXECUTE) | EXECUTE 행 신설 후 컨벤션 보고서 포함 — `opal-pilot-dev-short/SKILL.md:262-267` |
| opdw (D-13) | `EXECUTE: QA-EXECUTE.md` | O | 컨벤션 보고서 추가. WIREFRAME은 코드 변경 아니므로 영향 없음 |
| oppd (D-14) | 섹션 부재 | △ (Phase 3 액션 실행이 EXECUTE 대응) | PM Gate 점검 목록 섹션 자체가 없으므로 본 태스크 R-8 대상 외 |

#### 6) 도구·범위 제약

본 태스크는 **사후 검증 자동화(제안 B)** 한정. D-5 dispatch-process.md / D-6 opal-plan-agent.md의 "사전 주입 강화(제안 A)"는 별도 후속 태스크. PLAN.md에서도 D-5/D-6은 변경하지 않는다 — TASK.md §제약 조건 마지막 항목 부합.

### 영향 범위

본 변경은 OPAL 프레임워크 메타 정의(하네스/에이전트/오케스트레이터 스킬) 다중 파일에 걸친 SSOT 갱신이다. 전파 영향:

1. **PM Gate 동작 변화 (모든 PM Gate 보유 오케스트레이터)**
   - opp, opd, opds, opdw 4종 오케스트레이터의 EXECUTE PM Gate가 컨벤션 자동 진단을 추가 수행
   - oppd는 Phase 3 액션 실행이 내부적으로 opp/opds 등을 위임 호출하므로 간접 적용 (oppd 자체 수정 없음)
   - opal-pilot-gc(opgc)는 본 태스크 적용 대상 외 — opgc는 컨벤션 체커를 CHECK 단계 본 작업으로 호출하며 PM Gate 검토 단계 자체가 다른 의도

2. **워커 디스패치 호출량 증가**
   - 단일 문서 프로젝트(OPAL 자체 포함): EXECUTE 1회당 최대 +1 호출
   - 풀스택 프로젝트: 영역 수에 따라 EXECUTE 1회당 +N 호출 (병렬 디스패치)
   - 스킵 조건(R-6) 적용 시 호출 0건

3. **태스크 폴더 산출물 추가**
   - `tasks/{NNN}-.../GC-CONVENTION-{area}-{ts}.md` (영역별) 또는 `GC-CONVENTION-{ts}.md` (단일)
   - QA Gate / State Gate 라이프사이클은 변경 없음 — 보고서는 PM Gate 자체 검토 산출물로 분류

4. **하위 호환 보장**
   - `.opal/AGENT.md` 미존재 → PM Gate 자체 스킵 (D-1:76 기존 동작 유지)
   - `docs/CONVENTIONS.md` 부재 → 체커가 `check_enabled=false`로 처리 (D-2:62-66 기존 동작) → PM Gate Pass + 초안 유도 보고
   - `docs/PROJECT.md` "## 프로젝트 구성" 섹션 부재 또는 매칭 실패 → 허브 전체 적용 폴백 (D-3:69 + D-4 예시 B)

5. **별도 후속 태스크 분리 명시**
   - 사전 주입 강화(D-5 dispatch-process.md 인용 카탈로그 확장 / D-6 opal-plan-agent.md PLAN.md 자체 [MUST] 박기) 는 본 태스크 외 — PLAN.md 명시적 비변경 처리

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|

> 본 태스크는 모든 변경이 기존 SSOT 파일의 섹션 추가/보강이며 신규 파일은 없다.

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| 1 | `opal/core/references/harness/pm-review-gate.md` | §검토 절차에 "13. 컨벤션 자동 진단" 항목 신설 (트리거 조건 / 호출 절차 / 영역 분할 / 판정 기준 / 스킵 조건 / 하위 호환 6개 소절) + 변경이력 v1.2 추가 | R-1, R-2, R-5, R-6, R-7 (→ D-1 §검토 절차) |
| 2 | `opal/agents/opal-convention-checker/AGENT.md` | §입력 명세 하단에 "PM Gate 호출 시나리오" 파라미터 매핑 표 추가 + Phase 5 보고서 파일명 규약을 단일/영역별 2종으로 분기 + Phase 6 결과 반환 JSON `artifact_path` 영역별 갱신 + 변경이력 v1.2 추가 | R-3, R-4 (→ D-2 §입력 명세, §Phase 5, §Phase 6) |
| 3 | `opal/skills/opal-pilot-project/SKILL.md` | §PM Gate 점검 목록 표 EXECUTE 행 산출물 컬럼에 `GC-CONVENTION-*.md` 추가 + 변경이력 v2.8 추가 | R-8 (→ D-7 §PM Gate 점검 목록) |
| 4 | `opal/skills/opal-pilot-dev/SKILL.md` | §PM Gate 점검 목록 표 **TEST 행** 산출물 컬럼에 `GC-CONVENTION-*.md` 추가 + **STEP 5 TEST PM Gate 검증 체크리스트에 6번째 항목 '컨벤션 자동 진단 PASS' 신설** + 변경이력 v3.5 추가 | R-8 (→ D-11 §PM Gate 점검 목록, `opal-pilot-dev/SKILL.md:152-165` TEST PM Gate 검증 체크리스트) |
| 5 | `opal/skills/opal-pilot-dev-short/SKILL.md` | §PM Gate 점검 목록 표 **TEST 행** 산출물 컬럼에 `GC-CONVENTION-*.md` 추가 + **STEP 4 TEST PM Gate 검증 체크리스트에 6번째 항목 '컨벤션 자동 진단 PASS' 신설** + 변경이력 v2.x 추가 | R-8 (→ D-12 §PM Gate 점검 목록, `opal-pilot-dev-short/SKILL.md:118-131` TEST PM Gate 검증 체크리스트) |
| 6 | `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | §PM Gate 점검 목록 표 EXECUTE 행 산출물 컬럼에 `GC-CONVENTION-*.md` 추가 + 변경이력 v2.x 추가 | R-8 (→ D-13 §PM Gate 점검 목록) |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|

> 삭제 파일 없음.

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | pm-review-gate.md §13 신설 (SSOT 정의) | `opal/core/references/harness/pm-review-gate.md` | 中 (의사코드 + 4종 트리거 정의) |
| 2 | opal-convention-checker §입력 명세 + Phase 5 파일명 규약 | `opal/agents/opal-convention-checker/AGENT.md` | 中 (3개 위치 동기 갱신) |
| 3 | opp SKILL.md PM Gate 점검 목록 갱신 | `opal/skills/opal-pilot-project/SKILL.md` | 低 (1행 수정) |
| 4 | opd SKILL.md **TEST PM Gate 점검 목록 + 검증 체크리스트 갱신** (1행 수정 + 1항목 추가) | `opal/skills/opal-pilot-dev/SKILL.md` | 低 (TEST 행 산출물 컬럼 갱신 + STEP 5 검증 체크리스트 6번째 항목 신설) |
| 5 | opds SKILL.md **TEST PM Gate 점검 목록 + 검증 체크리스트 갱신** (1행 수정 + 1항목 추가) | `opal/skills/opal-pilot-dev-short/SKILL.md` | 低 (TEST 행 산출물 컬럼 갱신 + STEP 4 검증 체크리스트 6번째 항목 신설) |
| 6 | opdw SKILL.md PM Gate 점검 목록 갱신 | `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | 低 (1행 수정) |

**Phase 그룹핑**:

| Phase | Step | 실행 | 비고 |
|-------|------|------|------|
| 1 | 1 | 순차 | SSOT 정의 — 후속 단계가 인용할 §13 본문이 먼저 확정되어야 함 |
| 2 | 2 | 순차 | Step 1의 §13 호출 절차/파라미터 매핑이 Phase 5/6 갱신에 인용됨 |
| 3 | 3, 4, 5, 6 | 병렬 | 4개 오케스트레이터 SKILL.md 독립 파일 — Step 1·2 완료 후 동시 갱신 가능 |

> **의존성 근거**: Step 2의 "PM Gate 호출 시나리오" 표는 Step 1의 §13 호출 절차에서 정의된 파라미터 명세를 그대로 인용해야 일관됨 (D-1·D-2 SSOT 일관성). Step 3~6의 "PM Gate 점검 목록" 표는 Step 2의 보고서 파일명 규약(`GC-CONVENTION-{area}-{ts}.md` / `GC-CONVENTION-{ts}.md`)을 인용 — Phase 2 완료 후 일괄 병렬 가능.

### 핵심 설계

#### Step 1: pm-review-gate.md §검토 절차 §13 신설

**[MUST]** `opal/core/references/harness/citation-rules.md` §2.4: "재해석 여지가 있는 금지사항·강제 규칙은 `[MUST]` 접두사 + 원문 인용으로 기재한다." — §13 본문에서 R-1~R-7 강제 규칙은 모두 `[MUST]` 포맷으로 박는다.

**[MUST]** `opal/core/references/harness/state.md` §15: "파이프라인 행 상태 변경은 state-tool로만 수행한다. LLM이 STATE.md 마크다운 표를 직접 편집하는 것은 금지된다." — §13 신설 자체는 STATE.md 변경이 아니므로 영향 없음.

§검토 절차 항목 12번(`pm-review-gate.md:43-46`) 다음에 13번 신설. 기존 12번의 4단 포맷("실행 / 결과 / 근거")을 따른다.

**§13 본문 구성**:

```markdown
13. 컨벤션 자동 진단
   - **트리거 조건**: 단계 = EXECUTE이고 워커 반환 `changed_files` 중 docs/, .opal/, *.md, tasks/ 외 파일이 ≥1건 (R-6 스킵 조건의 역)
   - **영역 분할 절차**: `docs/PROJECT.md` "## 프로젝트 구성" 섹션 prefix 매칭으로 영역별 분할 — 의사코드는 `opal/core/references/pm/context-injection.md` §PROJECT.md 프로젝트 구성 기반 라우팅을 그대로 적용 (→ D-3). 매칭 실패 시 단일 호출(`scope=all`)로 폴백 (→ D-4 예시 B)
   - **호출**: 영역별로 opal-convention-checker 워커 디스패치 — 파라미터 매핑은 `opal/agents/opal-convention-checker/AGENT.md` §입력 명세 §PM Gate 호출 시나리오 표 참조 (→ D-2)
   - **호출 입력 명세**: `target_files = changed_files ∩ 영역 prefix`, `scope = 영역명` (단일 호출 시 `scope=all`), `task_folder = 현재 태스크 폴더`, `timestamp` = 영역별 분리 (병렬 호출별 고유 ts)
   - **판정 기준**:
     | 발견 이슈 심각도 | 결과 |
     |---------------|------|
     | Critical 또는 High ≥1건 | **Fail** → 워커 재지시 1회 → 미해결 시 캡틴 에스컬레이션 |
     | Medium 이하만 | **Pass** + 캡틴에 보고서 경로 요약 보고 |
   - **스킵 조건** (3종):
     1. `changed_files` = 0건
     2. `changed_files`가 docs/, .opal/, *.md, tasks/ 등 컨벤션 적용 외 파일만 포함
     3. `docs/CONVENTIONS.md` 부재 → 체커가 `check_enabled=false`로 자체 처리(`GC-CONVENTION-*.md` §5 "문서 작성 유도"만 작성) + PM Gate Pass
   - **하위 호환**: `.opal/AGENT.md` 미존재 시 PM Gate 자체 스킵(§판정 4번째 항목)이므로 본 §13도 동시 스킵 (→ D-1 §판정)
   - **근거**: TASK.md R-1~R-7 / `tasks/136-260508-opp-pm-gate-convention-auto-check/PLAN.md` §2 핵심 설계
```

설계 결정:
- **자동화 자기 검증 항목 8번/12번 포맷 일치**: 트리거 조건 / 호출 / 판정 / 근거 4단 — `pm-review-gate.md:26-30`(8번) `:43-46`(12번) 구조 답습
- **호출 명령은 워커 디스패치 형식 명시**: 단일 라인 CLI가 아니라 `opal-convention-checker` 서브에이전트 디스패치 형식 — D-2가 서브에이전트 정의이므로
- **영역 분할은 D-3 SSOT 인용**: 의사코드를 §13에 중복 작성하지 않고 D-3 섹션 링크로 단일화 (`context-injection.md:60-86` 그대로 재사용)
- **TS 분리**: 병렬 호출 시 동일 ts 사용 시 파일명 충돌 위험. 영역별 ts 분리 명시
- **변경이력**: v1.2 (2026-05-08) 추가

#### Step 2: opal-convention-checker §입력 명세 + Phase 5 + Phase 6 갱신

**[MUST]** `opal/core/references/harness/citation-rules.md` §0: "상상·추정·기억 기반 기재 금지 — 모든 분석·설계 결정은 문서 근거(경로/URL + 섹션/줄번호)를 인용해야 한다." — §입력 명세 PM Gate 시나리오 표는 D-1 §13의 호출 명령을 그대로 역참조하는 형식으로 작성한다.

**(a) §입력 명세 — PM Gate 호출 시나리오 표 추가** (`opal-convention-checker/AGENT.md:33` 7번째 파라미터 `scope` 행 다음):

```markdown
### PM Gate 호출 시나리오 (참고)

opp/opd/opds/opdw EXECUTE PM Gate에서 호출될 때의 파라미터 매핑:

| 파라미터 | 값 (PM Gate 호출 시) |
|---------|------------------|
| task_folder | 현재 태스크 폴더 (예: `tasks/136-.../`) |
| target_files | EXECUTE 워커가 반환한 `changed_files`를 영역 prefix 매칭으로 분할한 부분집합 (단일 호출 시 전체) |
| timestamp | 호출별 고유 ts. 영역별 병렬 디스패치 시 각 호출별로 분리하여 보고서 파일명 충돌 방지 |
| checklist_path | `~/.opal/skills/opal-pilot-gc/references/base-convention-checklist.md` (opgc 호출과 동일) |
| template_path | `~/.opal/skills/opal-pilot-gc/references/report-convention-template.md` (opgc 호출과 동일) |
| project_root | 프로젝트 루트 절대 경로 |
| scope | 영역명(`frontend`/`backend`/`batch`/`mobile` 등 — `docs/PROJECT.md` "## 프로젝트 구성" 요소명) 또는 `all`(단일 문서 프로젝트 / 매칭 실패 폴백) |

> 트리거 조건·판정 기준·스킵 조건은 `opal/core/references/harness/pm-review-gate.md` §검토 절차 §13 참조.
```

**(b) Phase 5 보고서 파일명 규약 분기** (`opal-convention-checker/AGENT.md:134` 한 줄을 다음으로 교체):

```markdown
`{task_folder}/GC-CONVENTION-{file_suffix}.md` 생성 (보고서 템플릿 기반):

- `file_suffix` 규약:
  - `scope == "all"` 또는 단일 호출 → `{timestamp}` (예: `GC-CONVENTION-2026-05-08T14-32-18.md`)
  - `scope` = 특정 영역 → `{scope}-{timestamp}` (예: `GC-CONVENTION-frontend-2026-05-08T14-32-18.md`)
- 영역별 병렬 디스패치 시 호출별 `timestamp`가 분리되므로 파일명 충돌 없음.
```

**(c) Phase 6 결과 반환 JSON `artifact_path` 갱신** (`opal-convention-checker/AGENT.md:160-167`):

```json
{
  "artifact_path": "{task_folder}/GC-CONVENTION-{file_suffix}.md",
  ...
}
```

`changed_files` 항목도 `["GC-CONVENTION-{file_suffix}.md"]`로 동기 갱신.

설계 결정:
- **§입력 명세 핵심 표 보존**: 7개 파라미터 본 표는 그대로 두고 시나리오 표를 부속 섹션으로 추가 — opgc 호출 호환성 유지
- **`file_suffix` 도입**: Phase 5와 Phase 6의 파일명 표현을 단일 변수로 통일하여 두 위치 동기 갱신 누락 방지
- **변경이력**: v1.2 (2026-05-08) 추가

#### Step 3~6: 4개 오케스트레이터 SKILL.md PM Gate 점검 목록 갱신

각 SKILL.md의 §PM Gate 점검 목록 표 EXECUTE 행 산출물 컬럼에 `GC-CONVENTION-*.md` 추가. 글로브 패턴(`*`)은 단일/영역별 두 형식을 모두 포함한다.

**Step 3 — opp** (`opal-pilot-project/SKILL.md:170-174`):

```diff
| Phase | 산출물 | 체크리스트 위치 |
|-------|-------|----------------|
| PLAN | TASK.md, PLAN.md, QA-PLAN.md | TASK.md 요구사항, PLAN.md §3, §4 |
- | EXECUTE | QA-EXECUTE.md | PLAN.md §3 |
+ | EXECUTE | QA-EXECUTE.md, GC-CONVENTION-*.md | PLAN.md §3 |
```

**Step 4 — opd** (`opal-pilot-dev/SKILL.md:265-272` PM Gate 점검 목록 표 + `:152-165` STEP 5 TEST PM Gate 검증 체크리스트): opd는 EXECUTE PM Gate가 의도적으로 부재(STEP 4 EXECUTE 후 STEP 5 TEST PM Gate가 종합 검증 위치) — TEST PM Gate에 컨벤션 자동 진단을 합류시킨다:

(a) PM Gate 점검 목록 표 TEST 행 산출물 컬럼 갱신:
```diff
| Phase | 산출물 | 체크리스트 위치 |
|-------|-------|----------------|
| ANALYSIS | ANALYSIS.md | - |
| PLAN | TASK.md, PLAN.md, TEST-SCENARIO.md | ... |
- | TEST | TEST-SCENARIO.md | TEST-SCENARIO.md 시나리오 결과/코드품질/보안/회귀 |
+ | TEST | TEST-SCENARIO.md, GC-CONVENTION-*.md | TEST-SCENARIO.md 시나리오 결과/코드품질/보안/회귀, 컨벤션 자동 진단 PASS |
```

(b) STEP 5 TEST PM Gate 검증 체크리스트(`opal-pilot-dev/SKILL.md:152-165`)에 6번째 항목 신설:
```diff
PM Gate 검증 체크리스트:
- [ ] TEST-SCENARIO.md 시나리오 결과 PASS
- [ ] 코드 품질 검토 PASS
- [ ] 보안 검토 PASS
- [ ] 회귀 영향 검토 PASS
- [ ] 설계 피드백 검토 PASS
+ - [ ] 컨벤션 자동 진단 PASS
```

**Step 5 — opds** (`opal-pilot-dev-short/SKILL.md:262-267` PM Gate 점검 목록 표 + `:118-131` STEP 4 TEST PM Gate 검증 체크리스트): 동일 패턴 — PM Gate 점검 목록 표 TEST 행 산출물 컬럼에 `GC-CONVENTION-*.md` 추가 + STEP 4 TEST PM Gate 검증 체크리스트에 6번째 항목 `[ ] 컨벤션 자동 진단 PASS` 신설.

**Step 6 — opdw** (`opal-pilot-dev-wireframe/SKILL.md:217-220`): EXECUTE 행 산출물 컬럼 갱신:

```diff
- | EXECUTE | QA-EXECUTE.md | - |
+ | EXECUTE | QA-EXECUTE.md, GC-CONVENTION-*.md | - |
```

설계 결정:
- **oppd 비변경 사유 명시**: oppd는 PM Gate 점검 목록 섹션 자체가 부재(`opal-pilot-project-dev/SKILL.md` 헤더 691줄 검색 결과 없음). Phase 3 액션 실행이 내부적으로 opp/opds 등을 위임하여 본 변경의 §PM Gate 점검 목록은 위임 대상 스킬에서 자동 적용됨 → R-8 적용 불가, AC 후반("추가하지 않는 명확한 사유가 PLAN.md에 기재") 충족
- **opgc 비변경 사유 명시**: opgc는 컨벤션 체커를 CHECK 단계 본 작업으로 호출하며, 본 태스크의 "PM Gate 자동 진단" 의도와 다른 별개 라이프사이클이므로 적용 대상 외
- **글로브 패턴(`*`) 사용 근거**: 단일 호출(`GC-CONVENTION-{ts}.md`) / 영역별(`GC-CONVENTION-{area}-{ts}.md`) 두 형식을 모두 표기하기 위함 — Step 2에서 정의한 file_suffix 규약과 일관

---

## 3. 실행 체크리스트

> 총 6개 Step | Phase 3개

| Phase | Step | 실행 | 비고 |
|-------|------|------|------|
| 1 | 1 | 순차 | SSOT(§13 본문) 정의 — 후속 단계 인용 의존 |
| 2 | 2 | 순차 | §13의 파라미터 명세를 §입력 명세 + Phase 5에 동기 |
| 3 | 3, 4, 5, 6 | 병렬 | 4개 오케스트레이터 SKILL.md 독립 파일 일괄 갱신 |

### Step 1: pm-review-gate.md §검토 절차 §13 "컨벤션 자동 진단" 신설

- [x] 완료
- **파일**: `opal/core/references/harness/pm-review-gate.md`
- **agent**: opal-task-agent
- **작업 내용**: §검토 절차 12번 다음에 13번 항목 신설. 트리거 조건 / 영역 분할 절차 / 호출 / 호출 입력 명세 / 판정 기준 / 스킵 조건 3종 / 하위 호환 / 근거 7개 소절 작성. 영역 분할은 D-3 §PROJECT.md 프로젝트 구성 기반 라우팅을 인용. 판정 기준은 Critical/High = Fail / Medium 이하 = Pass 표 형식. 스킵 조건은 changed_files=0 / 컨벤션 적용 외 / CONVENTIONS.md 부재 3종. 하위 호환은 `.opal/AGENT.md` 미존재 시 PM Gate 자체 스킵 인용. 변경이력 v1.2 (2026-05-08) 추가.
- **완료 기준**:
  - §검토 절차에 13번 항목이 존재한다 (제목: "컨벤션 자동 진단")
  - 7개 소절(트리거/영역 분할/호출/입력 명세/판정/스킵/하위 호환)이 모두 명시되어 있다
  - 판정 기준 표에 Critical/High = Fail / Medium 이하 = Pass 행이 있다
  - 스킵 조건 3종이 번호 매겨 명시되어 있다
  - D-3(`context-injection.md` §PROJECT.md 프로젝트 구성 기반 라우팅) 인용 링크가 존재한다
  - 변경이력 표 마지막 행이 v1.2 (2026-05-08)이다
- **테스트**: `grep -n "13. 컨벤션 자동 진단" opal/core/references/harness/pm-review-gate.md` 1건 / `grep -c "스킵 조건" pm-review-gate.md` ≥1 / `grep -c "Critical" pm-review-gate.md` ≥1
- **의존**: 없음

### Step 2: opal-convention-checker AGENT.md §입력 명세 + Phase 5 + Phase 6 갱신

- [x] 완료
- **파일**: `opal/agents/opal-convention-checker/AGENT.md`
- **agent**: opal-task-agent
- **작업 내용**:
  - §입력 명세 7개 파라미터 표 하단에 "PM Gate 호출 시나리오 (참고)" 부속 섹션 추가 — 7행 매핑 표 + §13 역참조 한 줄
  - Phase 5 첫 줄 `{task_folder}/GC-CONVENTION-{timestamp}.md` 한 줄을 `file_suffix` 변수 도입 형태로 교체 + 단일/영역별 분기 명시
  - Phase 6 결과 반환 JSON `artifact_path`/`changed_files` 두 곳을 `file_suffix` 표현으로 동기 갱신
  - 변경이력 v1.2 (2026-05-08) 추가
- **완료 기준**:
  - §입력 명세에 "PM Gate 호출 시나리오" 부제목이 존재한다
  - 매핑 표에 7개 파라미터(task_folder/target_files/timestamp/checklist_path/template_path/project_root/scope) 행이 모두 있다
  - Phase 5에 `file_suffix` 변수가 도입되고 단일(`{timestamp}`) / 영역별(`{scope}-{timestamp}`) 2종 규약이 명시된다
  - Phase 6 JSON `artifact_path`가 `{file_suffix}` 형태로 갱신된다
  - 변경이력 v1.2 (2026-05-08) 행이 추가된다
- **테스트**:
  - `grep -n "PM Gate 호출 시나리오" opal/agents/opal-convention-checker/AGENT.md` 1건
  - `grep -n "file_suffix" opal/agents/opal-convention-checker/AGENT.md` ≥3건 (Phase 5 정의 1건 + Phase 5 사용 1건 + Phase 6 1건)
  - `grep -c "GC-CONVENTION-{scope}" AGENT.md` ≥1건
- **의존**: Step 1 (§13의 파라미터 명세 인용 일관성 보장)

### Step 3: opp SKILL.md PM Gate 점검 목록 갱신

- [x] 완료
- **파일**: `opal/skills/opal-pilot-project/SKILL.md`
- **agent**: opal-task-agent
- **작업 내용**: §PM Gate 점검 목록 표 EXECUTE 행 산출물 컬럼에 `, GC-CONVENTION-*.md` 추가. 변경이력 v2.8 (2026-05-08) 추가.
- **완료 기준**: §PM Gate 점검 목록 EXECUTE 행 산출물 컬럼이 `QA-EXECUTE.md, GC-CONVENTION-*.md`로 변경됨. 변경이력 v2.8 추가.
- **테스트**: `grep -n "GC-CONVENTION" opal/skills/opal-pilot-project/SKILL.md` 1건
- **의존**: Step 2 (`GC-CONVENTION-*.md` 파일명 규약은 Step 2에서 확정)

### Step 4: opd SKILL.md TEST PM Gate 점검 목록 + 검증 체크리스트 갱신

- [x] 완료
- **파일**: `opal/skills/opal-pilot-dev/SKILL.md`
- **agent**: opal-task-agent
- **작업 내용**:
  - (a) §PM Gate 점검 목록 표(`opal-pilot-dev/SKILL.md:265-272`) **TEST 행 산출물 컬럼**에 `, GC-CONVENTION-*.md` 추가 + 체크리스트 위치 컬럼에 `, 컨벤션 자동 진단 PASS` 추가
  - (b) STEP 5 TEST PM Gate 검증 체크리스트(`opal-pilot-dev/SKILL.md:152-165`)에 **6번째 항목 `[ ] 컨벤션 자동 진단 PASS`** 신설 (기존 5개 항목: TEST-SCENARIO/코드 품질/보안/회귀/설계 피드백 다음 행)
  - 변경이력 v3.5 (2026-05-08) 추가
- **완료 기준**:
  - §PM Gate 점검 목록 TEST 행 산출물 컬럼에 `GC-CONVENTION-*.md`가 포함됨
  - STEP 5 TEST PM Gate 검증 체크리스트에 "컨벤션 자동 진단 PASS" 항목이 6번째로 추가됨
  - 변경이력 v3.5 추가
- **테스트**:
  - `grep -n "GC-CONVENTION" opal/skills/opal-pilot-dev/SKILL.md` ≥1건
  - `grep -n "컨벤션 자동 진단 PASS" opal/skills/opal-pilot-dev/SKILL.md` 1건
  - `grep -c "| TEST |" opal/skills/opal-pilot-dev/SKILL.md` ≥1 (PM Gate 점검 목록 표 내)
- **의존**: Step 2

### Step 5: opds SKILL.md TEST PM Gate 점검 목록 + 검증 체크리스트 갱신

- [x] 완료
- **파일**: `opal/skills/opal-pilot-dev-short/SKILL.md`
- **agent**: opal-task-agent
- **작업 내용**:
  - (a) §PM Gate 점검 목록 표(`opal-pilot-dev-short/SKILL.md:262-267`) **TEST 행 산출물 컬럼**에 `, GC-CONVENTION-*.md` 추가 + 체크리스트 위치 컬럼에 `, 컨벤션 자동 진단 PASS` 추가
  - (b) STEP 4 TEST PM Gate 검증 체크리스트(`opal-pilot-dev-short/SKILL.md:118-131`)에 **6번째 항목 `[ ] 컨벤션 자동 진단 PASS`** 신설
  - 변경이력 v2.x (2026-05-08) 추가 (현재 최신 버전 확인 후 +1)
- **완료 기준**:
  - §PM Gate 점검 목록 TEST 행 산출물 컬럼에 `GC-CONVENTION-*.md`가 포함됨
  - STEP 4 TEST PM Gate 검증 체크리스트에 "컨벤션 자동 진단 PASS" 항목이 6번째로 추가됨
  - 변경이력 행 추가
- **테스트**:
  - `grep -n "GC-CONVENTION" opal/skills/opal-pilot-dev-short/SKILL.md` ≥1건
  - `grep -n "컨벤션 자동 진단 PASS" opal/skills/opal-pilot-dev-short/SKILL.md` 1건
- **의존**: Step 2

### Step 6: opdw SKILL.md PM Gate 점검 목록 갱신

- [x] 완료
- **파일**: `opal/skills/opal-pilot-dev-wireframe/SKILL.md`
- **agent**: opal-task-agent
- **작업 내용**: §PM Gate 점검 목록 표 EXECUTE 행 산출물 컬럼(`opal-pilot-dev-wireframe/SKILL.md:220`)에 `, GC-CONVENTION-*.md` 추가. 변경이력 v2.x (2026-05-08) 추가 (현재 최신 버전 확인 후 +1).
- **완료 기준**: §PM Gate 점검 목록 EXECUTE 행 산출물 컬럼이 `QA-EXECUTE.md, GC-CONVENTION-*.md`로 변경됨. 변경이력 행 추가.
- **테스트**: `grep -n "GC-CONVENTION" opal/skills/opal-pilot-dev-wireframe/SKILL.md` 1건
- **의존**: Step 2

---

## 4. QA 체크리스트

### 기능 테스트 (R-1 ~ R-8 커버)

- [x] R-1: `opal/core/references/harness/pm-review-gate.md` §검토 절차에 "13. 컨벤션 자동 진단" 항목이 존재하고, 트리거 조건 / 호출 절차 / 판정 기준 / 스킵 조건 4개 이상의 소절이 모두 명시되어 있다
- [x] R-2: D-1 §13 본문에 D-3(`context-injection.md` §라우팅)의 의사코드 인용 링크가 존재하거나 의사코드가 그대로 명시되어 있고, 매칭 실패 시 "허브 전체 적용 폴백"이 정의되어 있다
- [x] R-3: `opal/agents/opal-convention-checker/AGENT.md` §입력 명세에 "PM Gate 호출 시나리오" 파라미터 매핑 표가 존재하고, 영역별 병렬 디스패치 시 timestamp 분리 규약이 명시되어 있다
- [x] R-4: D-2 §Phase 5에 영역별(`GC-CONVENTION-{area}-{ts}.md`) / 단일(`GC-CONVENTION-{ts}.md`) 두 형식의 보고서 파일명 규약이 모두 정의되어 있다
- [x] R-5: D-1 §13에 Critical/High = Fail / Medium 이하 = Pass 판정 표가 존재하고, Fail 시 "워커 재지시 1회 → 캡틴 에스컬레이션" 흐름이 D-1 §판정과 정합적으로 연결된다
- [x] R-6: D-1 §13에 스킵 조건 3종(changed_files=0 / 컨벤션 적용 외 / CONVENTIONS.md 부재)이 명시되어 있고, 각각의 처리 방식이 구분되어 있다
- [x] R-7: D-1 §13에 `.opal/AGENT.md` 미존재 시 PM Gate 자체 스킵으로 컨벤션 자동 진단도 동시 스킵된다는 문장이 존재한다
- [x] R-8: **opp/opdw**는 §PM Gate 점검 목록 표 **EXECUTE Phase** 산출물 컬럼에 `GC-CONVENTION-*.md`가 추가되어 있고, **opd/opds**는 §PM Gate 점검 목록 표 **TEST Phase** 산출물 컬럼에 `GC-CONVENTION-*.md`가 추가되어 있으며 + **TEST PM Gate 검증 체크리스트(opd STEP 5 / opds STEP 4)에 6번째 항목 '컨벤션 자동 진단 PASS'가 신설**되어 있다. oppd는 PM Gate 점검 목록 섹션 부재로 비변경 사유가 본 PLAN.md §1·§2에 기재되어 있다

### 일관성 테스트

- [x] §13의 파라미터 명세(Step 1)와 opal-convention-checker §입력 명세 PM Gate 시나리오 표(Step 2)의 7개 파라미터가 일치한다 (이름·필수·설명)
- [x] D-2 Phase 5의 `file_suffix` 변수와 Phase 6의 JSON `artifact_path`가 동일 변수로 표현되어 있다 (동기 갱신 누락 없음)
- [x] 4개 오케스트레이터 SKILL.md의 §PM Gate 점검 목록에 추가된 표현(`GC-CONVENTION-*.md`)이 글로브 패턴으로 통일되어 있다 (단일/영역별 형식 모두 매칭)
- [x] 변경된 모든 파일의 변경이력 표가 형식(`| 버전 | 날짜 | 변경내용 |`)을 일관되게 따른다
- [x] D-5(dispatch-process.md) / D-6(opal-plan-agent AGENT.md)는 본 태스크에서 비변경 (사전 주입 강화는 후속 태스크) — `git diff` 결과 두 파일 변경 없음 확인

### 문서 품질

- [x] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가 (예: `target_files`, `scope`, `changed_files` 영문)
- [x] kebab-case 파일/폴더 네이밍을 따르는가 (예: `pm-review-gate.md`, `GC-CONVENTION-*.md`)
- [x] 모든 변경 파일의 YAML frontmatter가 유지되어 있는가 (해당 시 — opal-convention-checker AGENT.md)
- [x] §1 참조 문서 테이블이 작성되어 있는가 (D-1 ~ D-14, 유형/경로(URL)/참조 이유 포함)
- [x] §2 핵심 설계에 인라인 인용이 기재되어 있는가 (`(→ D-N)`, `` `경로:줄번호` `` 등)
- [x] 재해석 여지가 있는 제약은 [MUST] 포맷으로 기재되어 있는가 (citation-rules.md §2.4)
- [x] STATE.md가 직접 편집되지 않았는가 (워커는 PLAN 단계 STATE.md 갱신 권한 없음 — PM이 state-tool로 갱신)
- [x] `~/.opal/` 배포 파일이 직접 편집되지 않았는가 (TASK 디스패치 §[MUST] 핵심 제약 #1 — 진본은 `opal/...` 한정)

---

## 5. 리스크 및 대응

| # | 리스크 | 영향 | 대응 |
|---|--------|------|------|
| R-T1 | OPAL 자체는 단일 문서 프로젝트 — 영역 분할 효과를 OPAL 내부에서 실증할 수 없음 | 풀스택 프로젝트에서만 영역별 병렬 디스패치 검증 가능. OPAL 자체에서는 단일 호출 폴백(`scope=all`)만 동작 검증 가능 | D-4 예시 B "단일 문서 프로젝트(OPAL 자체 포함)" 흐름이 `conventions-hub-model.md:87-94`에 이미 정의 → 본 태스크 OPAL 자체 검증은 단일 호출 폴백 + 스킵 조건 3종에 한정. 풀스택 영역 분할 동작은 별도 적용 프로젝트 검증으로 위임 |
| R-T2 | Step 2의 Phase 5/6 동기 갱신 누락 시 보고서 파일명과 결과 반환 JSON이 불일치 | 워커 결과 수신 측(PM)이 보고서 경로를 잘못 인식하여 후속 처리 실패 | `file_suffix` 단일 변수 도입(§2 핵심 설계 Step 2 (b)·(c))으로 두 위치 동기 강제. QA 일관성 테스트 2번째 항목으로 검증 |
| R-T3 | EXECUTE PM Gate가 영역별 N회 워커 디스패치 — 풀스택 프로젝트에서 호출 비용 증가 | 토큰/시간 비용 증가. 캡틴 비용 인지 필요 | TASK.md §제약 §비용 제어와 정합 — 매 EXECUTE Step이 아닌 EXECUTE PM Gate 1회로 집약. R-6 스킵 조건 3종으로 불필요 호출 차단. PLAN.md §13 호출 절차에 "병렬 디스패치"로 시간 비용은 영역 수와 무관하게 ≈1회 |
| R-T4 | opd/opds의 §PM Gate 점검 목록 EXECUTE 행이 부재한 것은 EXECUTE 단계가 PM Gate 직접 검증 없이 TEST PM Gate에서 종합 검증되도록 의도된 설계 (`opal-pilot-dev/SKILL.md:152-165` STEP 5 TEST PM Gate 검증 체크리스트 5항목: TEST-SCENARIO/코드 품질/보안/회귀/설계 피드백 / 동일 구조 `opal-pilot-dev-short/SKILL.md:118-131`) | EXECUTE 행 신설 시 의도된 검증 단계 분리가 깨짐 | **(b) 옵션 채택 결정 (캡틴 명시 결정)** — opp/opdw는 자체 EXECUTE PM Gate에서 §13(컨벤션 자동 진단) 발동(기존 PLAN 유지), opd/opds는 EXECUTE PM Gate가 의도적으로 부재이므로 **TEST PM Gate에서 §13 발동**으로 합류시킨다. 결정 근거: ①opd/opds STEP 4(opd) / STEP 3(opds) EXECUTE 후 PM Gate 부재가 명시적 설계(`opal-pilot-dev/SKILL.md:152-165` TEST PM Gate가 종합 검증 위치) ②변경이력 v2.9 "TEST QA Gate 제거, PM Gate에 검증 체크리스트 추가"가 동일 합류 패턴 선례 ③R-8 처리 분기: opp/opdw는 EXECUTE 행 산출물 컬럼에 `GC-CONVENTION-*.md` 추가, opd/opds는 TEST 행 산출물 컬럼에 `GC-CONVENTION-*.md` 추가 + STEP 5(opd) / STEP 4(opds) TEST PM Gate 검증 체크리스트에 **6번째 항목 '컨벤션 자동 진단 PASS' 신설**. |
| R-T5 | `tasks/{NNN}-.../GC-CONVENTION-*.md` 파일이 changed_files에 포함되어 PM Gate 11번 "docs/ 무효화 체크"와 충돌 가능 | PM Gate 11번이 `tasks/`를 docs/ 변경으로 잘못 분류할 위험 | TASK.md §제약 R-6 스킵 조건 2번 "docs/, .opal/, *.md, tasks/ 등 컨벤션 적용 외" — `tasks/` 경로는 컨벤션 적용 외로 분류. PM Gate 11번도 `docs/` 한정이며 `tasks/` 무관. R-T5는 실질적 충돌 아님 (재확인 결과). |
| R-T6 | oppd Phase 3 액션 실행이 opp/opds 등을 위임 호출 시 컨벤션 자동 진단이 위임 대상 스킬에서 자동 적용되는지 검증 부재 | oppd 사용 시 컨벤션 자동 진단 누락 가능성 | oppd `Phase 3-1 실행 루프`(`opal-pilot-project-dev/SKILL.md:353-394`)는 opal-task-action-agent를 위임하지만, 위임 대상 액션이 opp/opds를 호출하는 경우 해당 오케스트레이터의 EXECUTE PM Gate가 그대로 적용됨 — Step 3~6 갱신으로 자동 적용. 별도 oppd 수정 불필요 (PLAN.md §1.5 R-8 oppd 비변경 사유 인용). |

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-05-08 16:41 | 초기 작성 |
| v1.1 | 2026-05-08 18:35 | (b) 옵션 채택 — opd/opds Step 4·5를 EXECUTE 행 신설 → TEST 행 갱신 + 검증 체크리스트 6번째 항목 추가로 정정 (R-T4 결정 결과 반영) |
