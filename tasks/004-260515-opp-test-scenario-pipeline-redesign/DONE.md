# DONE: 테스트 시나리오 양식·작성 흐름·파이프라인 재설계

> 완료일: 2026-05-19 | 적용 스킬: opp | 모드: semi-agentic
> 시작: 2026-05-15 13:25 | 완료: 2026-05-19 17:09
> 산출물: TASK.md / PLAN.md / QA-PLAN.md / QA-EXECUTE.md / AGENTIC-LOG.md / DONE.md (이 파일)

---

## 1. 작업 요약

OPAL 프레임워크의 **테스트 시나리오 양식·작성 시점·작성자·EXECUTE 흐름·파이프라인 구조**를 일괄 재설계. mams 회귀 12건 패턴(단위 테스트 PASS 후 운영 회귀)이 사전 시나리오로 흡수되도록 SSOT를 보강.

### 핵심 변화 (Before → After)

| 항목 | Before | After |
|------|--------|-------|
| 시나리오 도출 | AC 매핑 강제 (당연한 시나리오 양산) | **리스크 가설 매핑** (가설 N건 → 시나리오 N건 이상) |
| 검증 차원 | 1차원 — "기능·에지·통합" 자유 분류 | **2차원 매트릭스** — 검증 깊이 L1/L2/L3 × 실행 방식 M1/M2/M3 |
| mock 처리 | "도구" 필드에 자유 기재 가능 | **mock 0 강제** (grep 감지 시 PM Gate FAIL) |
| 데이터 설계 | 양식에 없음 | "사전 조건 데이터 표" + "Given/When/Then" 필드 의무 |
| 작성자 | PLAN 워커가 PLAN.md + TEST-SCENARIO.md 통합 작성 (self-confirming) | **알투(PM) + 캡틴 페어** — PLAN 워커와 분리 |
| 작성 시점 | PLAN 단계 내부 | **STEP 3.5 TEST-SCENARIO 신설** (PLAN → TEST-SCENARIO → EXECUTE 직렬) |
| EXECUTE 흐름 | PLAN.md만 input | **scenario_source 추가** + L1/L2 시나리오 PASS = 완료 기준 (TDD red-green) |
| 모드 경계 | PLAN 사용자 확인 행 후 PM 자율 | **TEST-SCENARIO 사용자 확인 행** 후 PM 자율 |
| L3 [SUPERVISOR] | 권고 수준 | **즉시 PM 반환 의무** + PM 표준 요청 양식 |

### self-confirming 4분리 구도 달성

```
PLAN(opal-plan-agent) ≠ TEST-SCENARIO(알투+캡틴 페어) ≠ EXECUTE(워커) ≠ TEST(opal-test-agent + 캡틴)
```

---

## 2. 산출물 산정

### TASK.md 요구사항 충족

| F-ID | 변경 대상 | 결과 |
|------|---------|------|
| F-001 | `op-dev-test-scenario/SKILL.md` 양식 7섹션 재편 | ✅ Pass |
| F-002 | `test-scenario-guide.md` 재작성 — 5단계 프로세스 + 계층 결정 규칙 + mock 금지 + (추가작업) Step 3-b M1/M2/M3 | ✅ Pass |
| F-003 | `opal-pilot-dev/SKILL.md` 4→5단계 재편 + STATE 28행 + 모드 경계 이동 | ✅ Pass |
| F-004 | `op-dev-execute/SKILL.md` scenario_source input + 자가 점검 절차 | ✅ Pass |
| F-005 | `opal-pilot-dev/SKILL.md` EXECUTE 디스패치 3 필드 추가 | ✅ Pass |
| F-006 | `op-dev-plan/SKILL.md` 리스크 가설 표 SSOT + `opal-plan-agent/AGENT.md` 행동 규칙 | ✅ Pass |
| F-007 | `opal-pilot-dev/SKILL.md` PM Gate TEST-SCENARIO 행 — 6→7항목(추가작업으로 확장) | ✅ Pass |
| F-008 | `opal-harness-semi-agentic.md` §3 opd 행 + §8 차이 표 (opd 전용) | ✅ Pass |
| F-009 | `opal-pilot-dev/SKILL.md` L3 협업 게이트 + `opal-test-agent/AGENT.md` [SUPERVISOR] 처리 | ✅ Pass |
| F-010 | 8개 파일 변경이력 행 추가 — 단일 KST 일시 (EXECUTE 2026-05-15 16:40 / 추가작업 2026-05-19 17:05) | ✅ Pass |

### 변경 파일 (8개 — 본 EXECUTE 8개 중 4개에 추가작업 보강 누적)

| 파일 | EXECUTE 변경 | 추가작업 변경 |
|------|------------|-------------|
| `opal/skills/op-dev-test-scenario/SKILL.md` | F-001 양식 7섹션 재편 | "실행 방식" 필드 4건 + PM Gate 8번째 |
| `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | F-002 5단계 프로세스 + 계층 결정 규칙 + mock 금지 | **Step 3-b 신설 (M1/M2/M3 + L×M 매트릭스)** |
| `opal/skills/opal-pilot-dev/SKILL.md` | F-003·F-005·F-007·F-009 5단계 재편 | PM Gate 7항목 + STEP 3.5 절차 보강 |
| `opal/skills/op-dev-execute/SKILL.md` | F-004 scenario_source + 자가 점검 | (변경 없음) |
| `opal/skills/op-dev-plan/SKILL.md` | F-006 리스크 가설 표 SSOT | (변경 없음) |
| `opal/agents/opal-plan-agent/AGENT.md` | F-006 행동 규칙 1줄 | (변경 없음) |
| `opal/agents/opal-test-agent/AGENT.md` | F-009 [SUPERVISOR] 처리 | **M2 도구 환경 확인·환경 미비 시 PM 반환·mock 우회 금지** |
| `opal/core/references/opal-harness-semi-agentic.md` | F-008 §3 opd + §8 (opd 전용) | (변경 없음) |

---

## 3. 검증 결과

| Gate | 결과 | 상세 |
|------|------|------|
| PLAN QA Gate | Conditional Pass (10/11) → EXECUTE 자연 해소 | STATE 28행·F-008 opd 전용·STEP 3.5 작성자 명시 |
| PLAN PM Gate | Pass | 권고 3건 EXECUTE에서 반영 |
| EXECUTE QA Gate | Pass (32/32) | §A 기능 21 + §B 일관성 5 + §C 문서 품질 6 |
| EXECUTE PM Gate | Pass | spot-check 7/7 (STEP 3.5·mock·변경이력·opd 전용·scenario_source·가설 표·SUPERVISOR) |
| 추가작업 spot-check | Pass (5/5) | Step 3-b 신설·실행 방식 필드·PM Gate 7항목·M2 분기·변경이력 4파일 |
| EXECUTE 사용자 확인 | ✅ owner=user | 캡틴 "확인" 2026-05-19 17:10 |

---

## 4. 잔존 이슈 및 후속 태스크 후보

### 잔존 이슈

| 항목 | 상태 |
|------|------|
| 잔존 리스크 | **없음** |
| 미검증 항목 | **없음** |
| 블로커 | **없음** |

### 후속 태스크 후보

1. **`opal-pilot-dev-short`(opds) 동일 보강** — mams 회귀 12건의 다수가 opds 영역에서 발생. opds도 동일 self-confirming 구조이나 본 태스크 범위 외(TASK 제약). PLAN.md 리스크 가설 표 / TEST-SCENARIO 단계 / scenario_source input / 모드 경계 이동을 opds에도 적용.

2. **`opal-pilot-project`(opp) 검토** — opp는 현재 TEST-SCENARIO 자체가 없으나, 코드 변경을 동반하는 opp 태스크(예: 본 004)에서는 양식 일부 적용이 유용할 수 있음. 적용 범위/조건 검토.

3. **`docs/CONVENTIONS.md` 갱신 검토** — "테스트 시나리오 작성 시 mock 금지 + read→CUD→re-read + L/M 2차원 매트릭스" 룰을 CONVENTIONS에 추가하여 컨벤션 체커가 인지하도록.

4. **mams 적용 시 추가 빈틈 학습 루프** — 본 양식으로 첫 mams 태스크를 진행한 후 발견되는 빈틈을 메모리에 기록하여 다음 SSOT 보강 태스크로 흡수.

### 배포 (본 태스크 범위 외)

캡틴이 별도로 `scripts/install-mac.sh` 실행하여 `~/.opal/` 배포본 동기화 필요. 본 태스크는 프로젝트 소스(`opal/`) 변경만 완료.

---

## 5. 메모리·학습 정착

본 태스크의 핵심 결정은 OPAL 프레임워크 SSOT에 직접 반영되었으므로 별도 프로젝트 메모리는 불필요. 다만 다음 1건은 작업 패턴 메모리로 등재 권고:

- **feedback**: "테스트 시나리오는 PLAN 직후 알투+캡틴 페어가 작성 — self-confirming 방지. mock 0 + 실 데이터 + read→CUD→re-read + 2차원 매트릭스(L×M) 강제."

→ `.opal/MEMORY.md` 갱신은 본 DONE.md 직후 PM이 수행.

---

## 6. 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-05-19 17:10 | 초기 작성 — 004 태스크 완료 보고 (EXECUTE 12 Step + 추가작업 M1/M2/M3 보강) |
