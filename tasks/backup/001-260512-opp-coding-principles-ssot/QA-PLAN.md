# QA-PLAN: 카르파시 행동 원칙 흡수

> 검토일: 2026-05-12 | 판정: **Needs Revision**

## 1. 요약

PLAN.md는 카르파시 4원칙을 OPAL 단계별로 매핑하는 SSOT 신설, 워커 에이전트 3종 수정, 스킬 2종 보강을 포함한 8개 Step으로 분해했다. TASK.md 5개 요구사항(F-1~F-5)을 모두 커버하며, 실행 순서·의존성·완료 기준을 명확히 제시했다. 다만 §4 섹션 번호가 중복되는 형식 오류와 3개 에이전트의 스킬 트리거 문구 일관성 이슈가 발견되었다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|:----:|------|
| GP-1 | 즉시 실행 가능성 | Pass | 8개 Step이 구체적 파일·작업 내용·완료 기준을 포함하여 워커가 직접 실행 가능 |
| GP-2 | 의존성 순서 | Pass | Phase 구조와 Step 간 의존성(Step 1 → 2,3 → 4,5,6 → 7,8)이 명확하고 병렬 실행 구간 표시됨 |
| GP-3 | TASK 반영 | Pass | F-1(SSOT 신설) ~ F-5(AC↔verify 매핑) 5개 요구사항이 8개 Step으로 매핑됨. Step 1(F-1) / Step 2,3(F-1,F-3) / Step 4,5,6(F-2) / Step 7,8(F-4,F-5) |
| GP-4 | 파일 목록 완전성 | Pass | 신규 1개 + 수정 7개 = 총 8개 파일이 모두 명시됨 |
| GP-5 | 설계 구체성 | Pass | 의사결정 M-1~M-4에서 위치·구조·방식·조건부 선택 근거를 상세히 제시 |
| GP-6 | 체크리스트 커버리지 | Pass | 모든 F-ID가 Step으로 분해되고, 각 Step에 완료 기준(AC 참조)과 테스트 방법 포함 |
| B-1 | 형식 정합 | Fail | **§4 섹션 번호 중복**: PLAN.md:313(`## 4. 실행 체크리스트`) + PLAN.md:476(`## 4. QA 체크리스트`) 두 개의 §4 존재. QA 체크리스트는 §5로 정정 필요. 후속 §5 리스크 → §6으로 연쇄 변경 |
| B-2 | 에이전트 일관성 | Warning | **스킬 트리거 문구 불일치**: Step 4(FE: `op-dev-execute` 또는 `op-dev-wireframe`) vs Step 5(BE: `op-dev-execute` 명시, wireframe 미언급) vs Step 6(Task: `op-dev-execute` 또는 `op-task-execute`). Task 에이전트만 `op-task-execute` 포함은 정당하지만, FE/BE의 wireframe 격차 검토 필요. |
| B-3 | 변경이력 형식 | Pass | 모든 Step의 변경이력 표 행에 일시(KST: 2026-05-12 10:56) + 버전 + 태스크 번호(001) 포함. YAML 포맷 `YYYY-MM-DD HH:mm` 준수 |
| B-4 | 카르파시 인용 준비 | Pass | §2.5(op-task SKILL.md 보강)에서 카르파시 §4 원문 영문 인용 + 한국어 설명 병기 명시됨 |
| B-5 | 배포 경계 준수 | Pass | PLAN은 산출물(.md) 작성만 명시. `~/.opal/` 직접 편집 금지 원칙 준수. install 재실행은 EXECUTE 후 안내 예정(Step 5 근거) |

## 3. 지적 사항

### [Issue-1] §4 섹션 번호 중복 ⚠️ **Critical**

**위치**: PLAN.md:313, PLAN.md:476  
**내용**:
- 라인 313: `## 4. 실행 체크리스트` (8개 Step 상세 정의)
- 라인 476: `## 4. QA 체크리스트` (기능/일관성/문서 품질 체크 항목)

**영향**: 마크다운 목차 자동 생성 시 중복, 문서 정합성 위반  
**근거**: `docs/CONVENTIONS.md` 파일 구조 규칙 및 표준 마크다운 섹션 네이밍 원칙  
**정정 권고**: 
- 라인 476의 `## 4. QA 체크리스트` → `## 5. QA 체크리스트`로 변경
- 라인 503의 `## 5. 리스크 및 대응` → `## 6. 리스크 및 대응`으로 변경
- 라인 514의 `## 변경이력` 유지 (최종 섹션)

### [Issue-2] 에이전트 스킬 트리거 일관성 ⚠️ **Warning**

**위치**: Step 4, Step 5, Step 6의 조건부 의무 문구  
**발견**:

| 에이전트 | 스킬 트리거 |
|---------|-----------|
| **FE (Step 4)** | `op-dev-execute` **또는** `op-dev-wireframe` |
| **BE (Step 5)** | `op-dev-execute` (wireframe 미언급) |
| **Task (Step 6)** | `op-dev-execute` **또는** `op-task-execute` |

**문제**: FE는 wireframe을 포함하지만 BE는 미포함. Task는 `op-task-execute` 추가(정당함, 범용 에이전트).  
**근거**: PLAN.md Step 5에서 "Step 4와 동일한 패턴"이라고 했으나 실제 Step 5 본문에서는 `op-dev-execute`만 명시됨  
**정정 권고**: Step 5의 조건부 의무 문구를 다음과 같이 명확화:
```
- EXECUTE 단계 진입 시(스킬이 `op-dev-execute` 또는 `op-dev-wireframe` 계열일 때): 
  `opal/core/references/harness/coding-principles.md`를 Read하고 §4 EXECUTE 원칙을 준수한다.
```

또는 의도적으로 BE는 wireframe 미지원인 경우, Step 5 문구를 BE 도메인 정합성에 맞게 조정 필요.

### [Issue-3] opal-harness.md §10 신설 시 번호 검증 결과

**위치**: PLAN.md M-2 근거 및 Step 2  
**확인**: `opal/core/references/opal-harness.md` 현재 구조를 조사한 결과, §9(OPAL Tools)가 마지막 섹션이며 §10은 공백 번호. 충돌 없음. ✅  
**영향**: 리스크 §5 "리스크 및 대응" 테이블의 세 번째 행("opal-harness.md §번호 충돌") 위험 항목은 PLAN 수립 시점에 조사 완료된 상태이므로 실질적 리스크 없음.

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|---------|------|
| TASK.md F-1 AC | Step 1 "완료 기준"에서 TASK.md F-1 AC (a)~(e) 전항 명시 | Pass |
| TASK.md F-2 AC | Step 4,5,6에서 "(F-2 AC a), (F-2 AC b)" 명확히 참조 | Pass |
| TASK.md F-3 AC | Step 3에서 "(F-3 AC a), (F-3 AC b)" 참조 | Pass |
| TASK.md F-4 AC | Step 7에서 "(F-4 AC a), (F-4 AC b), (F-4 AC c)" 참조 | Pass |
| TASK.md F-5 AC | Step 8에서 "(F-5 AC a), (F-5 AC b), (F-5 AC c)" 참조 | Pass |
| TASK.md 배경 분석 | PLAN §2.1에서 "카르파시↔OPAL 단계 매트릭스" 참조 | Pass |
| TASK.md 의사결정 D-1~D-6 | PLAN §2.1~§2.6에서 D-참고 기호로 근거 명시 | Pass |
| CONVENTIONS.md 변경이력 | 일시 `YYYY-MM-DD HH:mm` (KST) 형식 준수 확인 | Pass |

## 5. 판정

**Needs Revision**

**판정 근거**: 
PLAN.md는 TASK.md 5개 요구사항을 8개 Step으로 완전 분해하고, 실행 순서·의존성·완료 기준을 구체적으로 제시했다. 의사결정 기록(M-1~M-4)도 명확하다. 그러나 **Critical 이슈 1개(§4 번호 중복)와 Warning 1개(에이전트 스킬 트리거 일관성)**가 존재한다. 특히 §4 중복은 목차 생성·문서 구조 정합성을 위협하므로 EXECUTE 진입 전 정정 권장.

---

## 부록: 단계별 추적성 검증 매트릭스

| TASK 요구사항 | PLAN Step | 완료 기준 명시 | 의존성 | 상태 |
|-------------|----------|-----------|--------|------|
| F-1 coding-principles.md 신설 | Step 1 | AC (a)~(e) ✅ | 독립 | Pass |
| F-1 하네스 정합 | Step 2 | 테이블 + §10 ✅ | Step 1 | Pass |
| F-3 "그냥 해" 표 | Step 3 | AC (a)~(b) ✅ | Step 1 | Pass |
| F-2 워커 자가 로드 (FE) | Step 4 | AC (a)~(b) ✅ | Step 1 | Pass |
| F-2 워커 자가 로드 (BE) | Step 5 | AC (a)~(b) ✅ | Step 1 | Pass (일관성 검토 필요) |
| F-2 워커 자가 로드 (Task) | Step 6 | AC (a)~(b) ✅ | Step 1 | Pass |
| F-4 AC 작성 가이드 보강 | Step 7 | AC (a)~(c) ✅ | 독립 | Pass |
| F-5 AC↔verify 매핑 | Step 8 | AC (a)~(c) ✅ | 독립 | Pass |

