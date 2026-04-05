# QA-EXECUTE

> 검토일: 2026-04-01 | 검토자: QA 에이전트

## 판정: Pass

## 검토 결과

| 파일 | 항목 | 결과 | 비고 |
|------|------|------|------|
| `opal/core/AGENT.md` | Eager 단계에 identity.md + opal-harness.md만 있는가 | ✅ Pass | Eager 단계 1~5 중 1: identity.md, 3: opal-harness.md만 Read. 2: 온보딩(조건부), 4: 부트스트래퍼 삽입(파일 확인), 5: 활성화 — Read 파일은 두 개만 해당 |
| `opal/core/AGENT.md` | `[WORKER]` 규칙 존재 여부 | ✅ Pass | 부트스트랩 섹션 상단에 `[WORKER 규칙]` 블록 명시 |
| `opal/core/AGENT.md` | Lazy 트리거 테이블 존재 여부 | ✅ Pass | 5행 트리거 테이블 존재. TASK.md 요구사항의 5개 항목 모두 포함 |
| `opal/core/AGENT.md` | 완료 보고 형식에 ⏳ 포함 여부 | ✅ Pass | `⏳ registry ⏳ references ⏳ model-mapping ⏳ PM` 포함 |
| `opal/core/AGENT.md` | PM 컨텍스트 섹션 내용 보존 여부 | ✅ Pass | "PM 컨텍스트 로드", "참조 문서 전달 의무", "PM 검토 게이트", "PM 학습 루프" 등 기존 내용 유지 + Lazy 트리거 주석 추가 |
| `opal/core/AGENT.md` | 프로젝트 메모리 브리핑 섹션 보존 여부 | ✅ Pass | 섹션 상단에 Lazy 트리거 주석 추가됨. 기존 절차·형식·규칙 내용 보존 |
| `opal/core/AGENT.md` | 모델 매핑 섹션 보존 여부 | ✅ Pass | "모델 매핑 자동 적용" 섹션 상단에 `> **Lazy 트리거**: 워커 디스패치 직전` 추가. 기존 절차 보존 |
| `opal/core/AGENT.md` | 변경이력 추가 여부 | ✅ Pass | v1.1 행 추가 (063 태스크 내용 기재) |
| `opal/skills/opal-pilot-project/SKILL.md` | `[WORKER]` 마커 지침 추가 여부 | ✅ Pass | STEP 2 (PLAN), STEP 3 (EXECUTE) 모두에 `[PM 컨텍스트 주입]` 블록 추가 |
| `opal/skills/opal-pilot-project/SKILL.md` | PM 컨텍스트 주입 규칙 존재 여부 | ✅ Pass | 두 디스패치 블록 모두에 하네스 Guards, 참조 문서, 기술 스택 연동 지시 3항목 명시 |
| `opal/skills/opal-pilot-project/SKILL.md` | 기존 내용 손상 여부 | ✅ Pass | STEP 1~3 구조, STATE.md 도메인, Agentic Mode, 변경이력 보존 |
| `opal/skills/opal-pilot-dev/SKILL.md` | `[WORKER]` 마커 지침 추가 여부 | ✅ Pass | STEP 2 (ANALYSIS), 3-1 (PLAN), 3-2 (TEST-SCENARIO), STEP 4 (EXECUTE) — 4개 디스패치 프롬프트 코드 블록 첫 줄에 `[WORKER]` 직접 삽입 |
| `opal/skills/opal-pilot-dev/SKILL.md` | PM 컨텍스트 주입 규칙 존재 여부 | ✅ Pass | 각 코드 블록에 `**하네스 Guards**`, `**참조 문서**` 파라미터 포함 |
| `opal/skills/opal-pilot-dev/SKILL.md` | 기존 내용 손상 여부 | ✅ Pass | 4단계 파이프라인, 에스컬레이션, Agentic Mode 보존 |
| `opal/skills/opal-pilot-dev-short/SKILL.md` | `[WORKER]` 마커 지침 추가 여부 | ✅ Pass | PLAN 디스패치, TEST-SCENARIO 디스패치(연속), EXECUTE — 3개 위치에 `[PM 컨텍스트 주입]` 블록 추가 |
| `opal/skills/opal-pilot-dev-short/SKILL.md` | PM 컨텍스트 주입 규칙 존재 여부 | ✅ Pass | PLAN 블록은 3항목 상세 기재. TEST-SCENARIO·EXECUTE는 축약형으로 동일 내용 명시 |
| `opal/skills/opal-pilot-dev-short/SKILL.md` | 기존 내용 손상 여부 | ✅ Pass | 에스컬레이션 규칙, STATE.md, Agentic Mode 보존 |
| `opal/skills/opal-pilot-write-tech/SKILL.md` | `[WORKER]` 마커 지침 추가 여부 | ✅ Pass | Phase 1 (병렬 분석), Phase 3 (병렬 작성), Phase 4 (정합성 검증) — 3개 위치에 `[PM 컨텍스트 주입]` 블록 추가 |
| `opal/skills/opal-pilot-write-tech/SKILL.md` | PM 컨텍스트 주입 규칙 존재 여부 | ✅ Pass | 3개 Phase 모두에 Guards + 참조 문서 경로 포함 지침 명시 |
| `opal/skills/opal-pilot-write-tech/SKILL.md` | 기존 내용 손상 여부 | ✅ Pass | 설계 원칙, 커버 범위, 3가지 모드, 게이트 체크포인트, 참조 가이드 보존 |
| `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | `[WORKER]` 마커 지침 추가 여부 | ✅ Pass | STEP 2 (WIREFRAME), STEP 3 (EXECUTE) 에 `[PM 컨텍스트 주입]` 블록 추가 |
| `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | PM 컨텍스트 주입 규칙 존재 여부 | ✅ Pass | WIREFRAME은 3항목 상세, EXECUTE는 축약형으로 명시 |
| `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | 기존 내용 손상 여부 | ✅ Pass | 입력물 분기표, STEP 1~3 구조, STATE.md 보존 |
| `opal/skills/opal-pilot-project-dev/SKILL.md` | `[WORKER]` 마커 지침 추가 여부 | ✅ Pass | Phase 3-1 순차 실행 루프의 디스패치 파라미터에 `[WORKER]` 첫 줄 명시. Phase 3-1b 병렬 실행에도 `[WORKER]` 삽입 명시 |
| `opal/skills/opal-pilot-project-dev/SKILL.md` | PM 컨텍스트 주입 규칙 존재 여부 | ✅ Pass | `harness_guards`, `reference_docs` 파라미터가 순차·병렬 양쪽 디스패치에 포함됨 |
| `opal/skills/opal-pilot-project-dev/SKILL.md` | 기존 내용 손상 여부 | ✅ Pass | Phase 1~3, 에이전트 결과 처리, STATE.md 관리, Agentic Mode 보존 |

## 발견 사항

### 경미한 관찰 사항 (기능상 문제 없음)

1. **opd vs opds/opp 스타일 불일치**: `opal-pilot-dev`(opd)는 디스패치 프롬프트 코드 블록 내에 `[WORKER]`를 직접 삽입하는 방식을 사용하고, `opal-pilot-dev-short`(opds)·`opal-pilot-project`(opp)·`opal-pilot-dev-wireframe`(opdw)은 코드 블록 외부에 `[PM 컨텍스트 주입]` 설명 블록을 추가하는 방식을 사용한다. PLAN에서는 opd 방식(코드 블록 직접 포함)이 더 명확하다고 설계 의도를 확인 가능하나, 두 방식이 혼재한다. 기능상 문제는 없다.

2. **opwt의 references 파일 미변경**: PLAN.md 6절 리스크에서 언급한 대로 `references/network-guide.md`, `references/consistency-rules.md`의 워커 프롬프트 템플릿에는 `[WORKER]` 마커가 삽입되지 않았다. SKILL.md에 지침이 추가되어 있어 PM이 직접 삽입해야 함을 알 수 있다. 리스크 대응이 문서에 명시되어 있으므로 허용 범위 내.

3. **AGENT.md Eager 단계 번호 표기**: Eager 단계 항목 4가 "부트스트래퍼 자동 삽입 확인"으로 기재되어 있고 본문에는 "부트스트랩 7단계"를 참조하도록 되어 있다. 기존 번호(7단계)가 Eager 4단계로 재배치됨을 명시하고 있으나, 본문 "프로젝트 부트스트래퍼 자동 관리" 섹션은 "부트스트랩 7단계에서"라는 기존 표현을 유지하고 있어 번호 불일치가 있다. 섹션 내용 참조에 오해 여지 있음.

## 권고사항

1. **경미 — 부트스트래퍼 섹션 번호 업데이트**: `opal/core/AGENT.md`의 "프로젝트 부트스트래퍼 자동 관리" 섹션 첫 줄 "부트스트랩 7단계에서,"를 "Eager 단계 4에서,"로 수정하면 번호 불일치를 해소할 수 있다. 기능에 영향은 없으나 가독성 개선 효과가 있다.

2. **선택 — 디스패치 스타일 통일 고려**: 추후 개선 작업 시 opds/opp/opdw의 디스패치 블록도 opd처럼 코드 블록 내 `[WORKER]` 직접 삽입 방식으로 통일하면 일관성이 향상된다. 현재 혼재 방식도 운영상 문제가 없으므로 즉시 조치는 불필요하다.
