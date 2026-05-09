# QA: PLAN — opds/opd TEST-SCENARIO 흐름 재설계

> 검토일: 2026-04-08 | 판정: **Pass**

---

## 1. 요약

PLAN.md는 TASK.md가 정의한 두 가지 구조적 문제(TEST-SCENARIO Gate 미통과, TEST 비공식 단계)를 해결하기 위한 변경 설계를 담고 있다. opds와 opd 두 스킬 모두 TEST-SCENARIO 디스패치 순서를 QA Gate 앞으로 이동하고, EXECUTE 후 TEST를 독립 공식 단계로 신설하는 구조를 구체적으로 명시하고 있다. TEST 루핑은 하네스 §1 L3a 기준과 정합하며 의사코드와 흐름도로 구체화되었다. STATE.md 새 템플릿도 행 단위로 명시되어 즉시 실행 가능한 수준이다.

---

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| GP-1 | **즉시 실행 가능성** — PLAN만으로 EXECUTE 워커가 작업을 수행할 수 있는가 | Pass | 변경 섹션 테이블, 템플릿 전문, 의사코드, 프롬프트 예시까지 명시. 실행 충분. |
| GP-2 | **의존성 순서** — 변경 대상 파일 간 순서 의존성이 없는가 | Pass | opds SKILL.md와 opd SKILL.md는 독립 파일. 순서 제약 없음. |
| GP-3 | **TASK 반영** — TASK.md 요구사항이 모두 PLAN에 반영되었는가 | Pass | 요구사항 5개 항목 전부 커버. 상세 하단 §3 교차 참조 참조. |
| GP-4 | **파일 목록 완전성** — 변경 대상 파일이 빠짐없이 명시되었는가 | Pass | `opal/skills/opal-pilot-dev-short/SKILL.md`, `opal/skills/opal-pilot-dev/SKILL.md` 명시. TASK.md 변경 대상과 일치. |
| GP-5 | **설계 구체성** — 변경 전/후 비교, 섹션 단위 지침이 구체적인가 | Pass | §1에서 변경 전/후 흐름을 나란히 제시. §3 실행 체크리스트가 섹션 단위로 분해. |
| GP-6 | **체크리스트 커버리지** — 실행 체크리스트가 TASK.md 완료 기준을 모두 포함하는가 | Pass | TASK.md 완료 기준 5개 항목이 실행 체크리스트와 대응됨. |
| GP-7 | **루핑 가드 정합성** — TEST 루핑 설계가 하네스 §1 L3a(3회)와 일치하는가 | Pass | PLAN §2 의사코드: `MAX_ATTEMPTS = 3`, 초과 시 에스컬레이션. 하네스 §1 L3a와 정확히 정합. |
| GP-8 | **회귀 방지 반영** — 하네스 §1 회귀 방지 규칙이 fix 모드에 반영되었는가 | Pass | PLAN §4-1에서 "fix 후 이전 PASS 항목 재실행 → 회귀 발생 시 루프 즉시 중단 + 에스컬레이션" 명시. |
| GP-9 | **STATE.md 템플릿 완전성** — 새 행 목록이 변경 설계와 일치하는가 | Pass | opds 새 템플릿(21행) 전문 제시. TEST 루핑 행 동적 추가 방식도 명시. opd는 "opds와 동일 구조 적용"으로 충분히 안내. |
| GP-10 | **opd STATE.md 구체성** — opd 신규 STATE.md 행 목록이 직접 제시되었는가 | Warning | opds는 전체 행 템플릿을 직접 제시하나, opd는 "opds와 동일 구조" 참조로만 기술. 실행 워커가 opd용 템플릿을 별도 도출해야 하는 모호성 존재. |
| GP-11 | **fix 모드 미구현 리스크** — op-dev-execute fix 모드 존재 여부 확인 여부 | Warning | §4-2와 §5에서 "확인 필요", "미구현 시 프롬프트 컨텍스트로 대응" 표기. 실행 전 확인 필요 항목이 PLAN에 열린 채로 남아있음. 블로커 수준 아님. |
| GP-12 | **agentic 모드 영향** — agentic 모드 자율 게이트 흐름도 동일 변경이 필요한가 | Warning | SKILL.md 변경 후 agentic 모드 섹션의 자율 게이트 흐름(`TASK → PLAN+TEST-SCENARIO → EXECUTE`)도 갱신 대상이나 PLAN에 미명시. 실행 워커가 해당 흐름 텍스트를 함께 수정해야 함을 인지하지 못할 수 있음. |

---

## 3. 지적 사항

### Warning-1: opd STATE.md 진행 현황 행 직접 제시 부재 (GP-10)

- **심각도**: Warning
- **내용**: opds는 21행 전체 템플릿을 직접 제시하는 반면, opd는 "opds와 동일 구조 적용"으로만 기술. opd는 ANALYSIS 단계가 추가되어 행 번호 오프셋이 달라지므로 실행 워커가 이를 직접 도출해야 한다.
- **권고**: PLAN에 opd용 진행 현황 행 전체 템플릿을 직접 추가하거나, 실행 체크리스트 항목에 "opd 행 템플릿 직접 도출" 지시를 명시하는 것이 안전함. 현 수준도 실행 가능하나, 오류 여지가 있다.
- **판단**: 진행 가능. 실행 워커 지시 시 명확히 안내 필요.

### Warning-2: fix 모드 미구현 여부 PLAN 내 미확정 (GP-11)

- **심각도**: Warning
- **내용**: PLAN §4-2에서 "op-dev-execute SKILL.md에 이미 구현되어 있는지 EXECUTE 단계에서 확인 필요"라고 기술되어 있어, PLAN 시점에 확인되지 않은 전제 조건이 존재함.
- **권고**: 실행 워커 디스패치 전 op-dev-execute SKILL.md를 미리 확인하고 fix 모드 존재 여부를 PLAN에 기록하는 것이 바람직함. 단, PLAN §5 리스크에 대응 방안이 명시되어 있어 블로커는 아님.
- **판단**: 진행 가능. 실행 시작 시 op-dev-execute SKILL.md 선확인 권장.

### Warning-3: agentic 모드 흐름 갱신 누락 (GP-12)

- **심각도**: Warning
- **내용**: opds와 opd SKILL.md의 `## Agentic Mode` 섹션 내 자율 게이트 흐름 텍스트(`TASK → PLAN+TEST-SCENARIO → EXECUTE`)도 새 단계 구조(`TASK → PLAN → TEST-SCENARIO → EXECUTE → TEST`)에 맞게 갱신이 필요하나, PLAN의 실행 체크리스트(§3)에 해당 섹션이 변경 대상으로 포함되지 않음.
- **권고**: PLAN §3 실행 체크리스트의 opds/opd 변경 섹션 테이블에 `## Agentic Mode — 자율 게이트 흐름` 항목을 추가. 변경 내용: `PLAN+TEST-SCENARIO → EXECUTE` → `PLAN → TEST-SCENARIO → EXECUTE → TEST`.
- **판단**: 진행 가능. 단, 실행 워커가 이 항목을 놓치지 않도록 디스패치 시 명시 필요.

---

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md 요구사항 1 | TEST-SCENARIO를 Gates 앞으로 이동 → PLAN §1-1 변경 후 흐름에 반영 | Pass |
| TASK.md 요구사항 2 | TEST를 공식 단계로 신설, STATE.md에 명시적 행 → PLAN §1-1 TEST 단계 신설 + 진행 현황 템플릿 갱신 | Pass |
| TASK.md 요구사항 3 | TEST 루핑 구현 (최대 3회, 에스컬레이션) → PLAN §2 의사코드·흐름도에 완전 반영 | Pass |
| TASK.md 요구사항 4 | opds + opd 동시 수정 → PLAN §1-1 (opds), §1-2 (opd) 각각 기술 | Pass |
| TASK.md 요구사항 5 | STATE.md 템플릿 갱신 → PLAN §1-1에 opds 21행 전체 제시. opd는 간접 기술 (Warning) | Pass (Warning) |
| TASK.md 완료 기준 1 | opds SKILL.md: TEST-SCENARIO Gates 앞, TEST 단계 + 루핑 → 실행 체크리스트 변경 섹션 테이블로 커버 | Pass |
| TASK.md 완료 기준 2 | opd SKILL.md: 동일 구조 반영 → 실행 체크리스트 커버 | Pass |
| TASK.md 완료 기준 3 | 두 스킬 STATE.md 템플릿에 TEST-SCENARIO, TEST 행 추가 → opds 직접, opd 간접 커버 | Pass (Warning) |
| TASK.md 완료 기준 4 | 루핑 가드: 최대 3회, 초과 시 에스컬레이션 → PLAN §2 의사코드 MAX_ATTEMPTS=3, §4-1 하네스 정합성 명시 | Pass |
| TASK.md 완료 기준 5 | 변경이력 업데이트 → PLAN §3 실행 체크리스트 각 스킬 변경 섹션에 v2.5/v2.4 항목 추가 명시 | Pass |
| 하네스 §1 L3a | unit/integration test 최대 3회, 초과 시 에스컬레이션 → PLAN §2 MAX_ATTEMPTS=3 정합 | Pass |
| 하네스 §1 회귀 방지 | fix 후 이전 PASS 항목 재실행 → PLAN §4-1에 명시 | Pass |

---

## 5. 판정

**Pass**

TASK.md의 모든 요구사항과 완료 기준이 PLAN에 반영되었고, TEST 루핑 설계는 하네스 §1 L3a와 정확히 정합한다. Warning 3건은 블로커 수준이 아니며 실행 시 주의로 처리 가능하다. EXECUTE 단계 진행을 승인한다.

> Warning 요약: opd STATE.md 행 템플릿 직접 미제시(GP-10), fix 모드 확인 미완(GP-11), agentic 모드 흐름 갱신 항목 누락(GP-12). 실행 워커 디스패치 시 이 3건을 명시적으로 안내 권장.
