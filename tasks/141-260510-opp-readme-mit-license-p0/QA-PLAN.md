# QA: PLAN — README 오픈소스 공개 P0 정비 — MIT LICENSE + 표시·실측 정정

> 검토일: 2026-05-10 | 판정: Pass

## 1. 요약

태스크 141은 OPAL 오픈소스 공개에 필요한 P0 정비 7건(MIT LICENSE 신규, README 배지/섹션 추가, 6건 표시 정정, ARCHITECTURE.md 에이전트 카운트 동기화)을 다루는 순수 문서 변경 태스크다. PLAN.md는 TASK.md R-1~R-8 요구사항을 모두 커버하는 10개 Step으로 분해하였으며, 각 Step에 완료 기준과 검증 명령이 명세되어 있다. 의존성 순서가 올바르게 설정되어 있고, 영역 간 용어 일관성 리스크(R-T1)를 선제적으로 식별하여 M-9(ARCHITECTURE.md §에이전트 GC 체커 2행 추가)으로 자체 해결 방안을 제시하였다. 컨벤션 [MUST] 4종 인용이 §1 컨벤션 인용 섹션에 명시되어 있으며, 에이전트 배정은 PROJECT.md 단일 영역(Framework)과 정합하는 `opal-task-agent` 단일 배정으로 이루어졌다.

---

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| GP-1 | 즉시 실행 가능성 | Pass | §2 핵심 설계에 각 변경의 Before/After가 명시되어 있어 PLAN만으로 바로 실행 진입 가능 |
| GP-2 | 의존성 순서 | Pass | Phase 1~5 의존 흐름 명시. LICENSE → 배지/License 섹션, ARCHITECTURE.md §에이전트 → README L728 순서 정확. README 다중 편집 시 동일 파일 순차 권장 주석 포함 |
| GP-3 | TASK 반영 | Pass | R-1~R-8 전체가 Step 1~10에 1:1 AC 매핑으로 커버됨 (Step 4가 R-6, Step 5가 R-2, Step 6이 R-4, Step 7이 R-5, Step 8이 R-7, Step 9가 R-8, Step 10이 R-3) |
| GP-4 | 파일 목록 완전성 | Pass | LICENSE(신규), README.md(수정), docs/ARCHITECTURE.md(수정) 3건 모두 포함. 삭제 파일 없음. TASK.md §관련 문서 D-1~D-6과 일치 |
| GP-5 | 설계 구체성 | Pass | N-1(LICENSE 본문 22줄 전문 포함), M-1~M-9 각각 기존/변경 후 텍스트 명시, 배지 SVG URL 구체 기재, 모델 컬럼 실측 지시(R-T5 대응) |
| GP-6 | 체크리스트 커버리지 | Pass | §3 실행 체크리스트 Step 1~10이 TASK.md R-1~R-8 모두를 커버. §4 QA 체크리스트 R-1~R-8 직접 검증 + 일관성/문서품질 항목 추가 |
| C-1 | 컨벤션 [MUST] 4종 인용 | Pass | §언어 규칙 / §Guards / §변경이력 / §커밋 규칙 4종 모두 §1 컨벤션 인용 섹션에 [MUST] 형식으로 명시됨 |
| C-2 | 에이전트 배정 정합성 | Pass | 전체 10개 Step이 `opal-task-agent` 단일 배정. PROJECT.md §프로젝트 구성 Framework 단일 영역 + 전문 에이전트 폴백 규칙과 정합 |
| C-3 | M-9 범위 판단 | Pass with Note | TASK.md §확정된 설계 방향 §6의 "ARCHITECTURE.md(L186) 표기 갱신" 범위를 합리적 확장. R-T1(영역 간 분류 불일치) 리스크 대응으로 §에이전트 표 갱신은 R-6 AC "분류는 ARCHITECTURE.md §컴포넌트 유형과 동일 표현" 충족을 위해 필수. 단, TASK.md §확정된 설계 방향 §6이 "L186 표기"만 명시하고 §에이전트 표 갱신을 직접 언급하지 않으므로 경계선에 위치함 (아래 §3 참조) |
| C-4 | 변경이력 면제 판단 | Pass | docs 카테고리(README/ARCHITECTURE/LICENSE) 면제가 TASK.md §제약 조건 + L186 v0.3.15 선례 양쪽으로 근거 확보. §1 컨벤션 인용 [MUST] 섹션에도 명시됨 |
| C-5 | 영역 간 용어 일관성 (citation-rules §7) | Pass | R-T1(README L728 분류 ↔ ARCHITECTURE.md §에이전트 분류 불일치)을 능동 검출, M-9 Step 2로 자체 해결 방안 포함. §7.4 decision_required 보고도 "추가 사용자 결정 없음"으로 명기 |
| C-6 | 완료 기준 검증 가능성 | Pass | 전체 10 Step이 `grep`, `find`, `wc -l`, `ls`, `head` 등 쉘 명령으로 검증 가능한 형태. 시각 검증은 "선택" 표기로 적절히 구분됨 |
| C-7 | citation-rules §0 근거 제시 원칙 | Pass | D-1~D-11 참조 테이블 완전, 핵심 설계 각 섹션에 인라인 인용 포함, [MUST] 4종 포맷 준수 |
| C-8 | R-8 AC 해석 정합 | Warning | TASK.md R-8 AC: "단순 삭제"도 허용 옵션으로 기재됨. PLAN M-6/Step 9는 "단순 삭제 + 검증 명령 안내 1줄 대체"로 R-8 AC의 두 번째 선택지를 채택함. 이는 정합하나, Step 9 완료 기준이 "대체 명령 1줄"을 필수로 두어 "단순 삭제"만의 경우를 불허하고 있음 — TASK.md §확정된 설계 방향 §7 "단순 삭제. 별도 안내 문구 불필요"와 미묘하게 긴장 관계. 실행 시 대체 명령 1줄 추가가 더 사용자 친화적이므로 기능상 문제는 없으나, EXECUTE 워커가 TASK.md §7과 PLAN M-6 중 PLAN을 따르면 됨을 확인 필요 |

---

## 3. 지적 사항

### Warning: C-8 — R-8 완료 기준과 TASK.md §확정된 설계 방향 §7 사이의 미묘한 긴장

**심각도**: Warning (진행 가능, 확인 권장)

**상세**:

- **TASK.md §확정된 설계 방향 §7**: "MCP 트러블슈팅 라인 삭제: 단순 삭제. 자동 등록은 [3/4] doctor 진단 + `claude mcp list` / `claude mcp get`으로 검증 가능하므로 **별도 안내 문구 불필요**."
- **TASK.md R-8 AC**: "해당 라인이 제거되고, 그 자리에 사용자가 검증할 수 있는 명령(`claude mcp list` / `opal-cli doctor`) 안내가 들어가거나 **단순 삭제**"
- **PLAN M-6/Step 9**: "단순 삭제 + 검증 명령 안내 1줄로 대체" 채택. Step 9 완료 기준에 `grep -n "claude mcp list\|opal-cli doctor" README.md → 1건 이상`을 필수 테스트로 포함.

**영향**: §확정된 설계 방향 §7은 "별도 안내 문구 불필요"를 명시하지만, R-8 AC는 안내 추가를 허용하며 PLAN은 안내 추가를 사실상 필수화했다. 사용자 경험 측면에서 검증 명령 안내가 더 우수하므로 기능상 문제 없음. 다만 EXECUTE 워커가 Step 9 테스트를 필수로 수행 시 안내 1줄을 반드시 포함해야 한다는 점을 인지해야 한다.

**권장**: 진행 가능. EXECUTE 단계에서 PLAN Step 9(검증 명령 1줄 대체)를 기준으로 실행할 것.

---

### Note: C-3 — M-9(ARCHITECTURE.md §에이전트 GC 체커 2행 추가)의 TASK.md 범위 경계

**심각도**: Info (진행에 영향 없음)

**상세**:

- TASK.md §확정된 설계 방향 §6은 "ARCHITECTURE.md(L186) 표기 '10개'도 동시에 13개 기준으로 정합 갱신"만 명시하며, §에이전트 분류 표 갱신을 직접 언급하지 않는다.
- PLAN M-9는 R-6 AC "분류는 ARCHITECTURE.md §컴포넌트 유형과 동일 표현"을 충족하기 위해, §에이전트 표가 11개로 outdated인 상태에서 README L728의 13개 분류와 정합되도록 §에이전트 표도 갱신하는 것으로 범위를 확장했다. 이는 R-T1 리스크(citation-rules §7 영역 간 용어 일관성 위반) 대응이기도 하다.
- 판단: M-9는 TASK.md R-6 AC를 충족하기 위한 합리적 범위 확장으로 인정. "부수 영향 최소화" 제약(TASK.md §제약 조건)과 긴장하나, R-6 AC 달성에 필수 불가결한 변경이다.

**결론**: 범위 초과로 보지 않음. TASK.md R-6 AC 정합을 위해 설계 방향 §6의 자연스러운 확장으로 판정.

---

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md R-1~R-8 | PLAN §3 Step 1~10 AC 매핑으로 1:1 커버 여부 | Pass — R-1→Step1, R-2→Step5, R-3→Step10, R-4→Step6, R-5→Step7, R-6→Step2+3+4, R-7→Step8, R-8→Step9 |
| TASK.md §확정된 설계 방향 §1 (범위 P0만) | PLAN이 P1/P2 항목을 포함하지 않는가 | Pass — 배지 P2 후속 분리, community-skills 142 분리 명시 |
| TASK.md §제약 조건 (변경이력 면제) | PLAN §1 컨벤션 인용 및 §1 영향 범위에서 면제 근거 명시 여부 | Pass — L186 v0.3.15 선례 + TASK.md §제약 조건 이중 근거 |
| TASK.md §제약 조건 (커밋 사용자 승인 후) | PLAN이 커밋 자동화를 포함하지 않는가 | Pass — [MUST] §커밋 규칙 인용으로 EXECUTE 후 자동 커밋 금지 명시 |
| PROJECT.md §프로젝트 구성 | 에이전트 배정이 Framework 단일 영역 + opal-task-agent 폴백 정합인가 | Pass — 전체 Step opal-task-agent 단일 배정 |
| PROJECT.md §프로젝트 문서 | PLAN §1 참조 문서 테이블(D-1~D-11)이 PROJECT.md 등재 문서를 포함하는가 | Pass — README.md(D-1), ARCHITECTURE.md(D-2), CONVENTIONS.md(D-7), PROJECT.md(D-8) 포함 |
| citation-rules §0 (근거 제시 원칙) | 설계 결정에 근거 없는 추정 기재 여부 | Pass — M-9 모델 컬럼 "EXECUTE에서 실측" 명시, PLAN 단계 추측 금지 준수 |
| citation-rules §7 (영역 간 용어 일관성) | README L728 분류 ↔ ARCHITECTURE.md §에이전트 분류 불일치 감지 및 대응 여부 | Pass — R-T1으로 능동 검출, M-9 Step 2로 자체 해결 |
| TASK.md §관련 문서 D-3 | PLAN D-3이 install.sh를 추가로 포함 (TASK.md는 install.ps1/windows.ps1) | Pass (확장) — TASK.md D-3은 ps1만, PLAN D-3은 install.sh도 포함. 실측 검증 범위 확장으로 정합성 향상 |

---

## 5. 판정

**Pass**

TASK.md R-1~R-8 요구사항이 PLAN §3 Step 1~10에 1:1 AC 매핑으로 완전히 커버되며, 컨벤션 [MUST] 4종 인용·에이전트 단일 배정·의존성 순서·설계 구체성 모두 기준을 충족한다. Warning 1건(C-8)은 EXECUTE 실행 방향을 명확히 하는 권고 수준으로 PLAN 진행을 막지 않는다. M-9(GC 체커 2행 추가)의 범위 확장은 R-6 AC 충족을 위한 합리적 확장으로 인정된다.
