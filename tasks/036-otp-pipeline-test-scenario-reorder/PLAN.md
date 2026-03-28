# PLAN: otp 파이프라인 TEST-SCENARIO 단계 재배치 + EXECUTE 후 커밋 규칙 명시

> 작성일: 2026-03-28
> 입력: TASK.md
> 출력: PLAN.md

## 1. 코드 분석

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `skills/otp-dev-short/SKILL.md` | Short Task 오케스트레이터 (4단계 파이프라인) | ✅ |
| `skills/otp-dev/SKILL.md` | Full Task 오케스트레이터 (7단계 파이프라인) | ✅ |

### 현재 구현

#### otp-dev-short (Short Task)

현재 4단계 파이프라인:
```
STEP 1: TASK → STEP 2: PLAN → STEP 3: TEST-SCENARIO → STEP 4: EXECUTE
```

- **STEP 2 (PLAN)**: dtp-plan 워커 디스패치 → dtp-qa 워커 → PM 검토 게이트 → 사용자 보고
- **STEP 3 (TEST-SCENARIO)**: 독립 STEP으로 dtp-test-scenario 워커 디스패치 → 사용자 보고. "승인 = EXECUTE 시작 허가"
- **STEP 4 (EXECUTE)**: dtp-execute 워커 디스패치 → dtp-test → DONE.md → 완료 보고
- 파이프라인 다이어그램 (L30-35): `dtp-task → dtp-plan → [QA] → 검토 → dtp-test-scenario → 검토/승인 → dtp-execute → [Test] → 완료`
- STATE.md 템플릿 (L168): 단계 목록 `TASK / PLAN / TEST-SCENARIO / EXECUTE`

#### otp-dev (Full Task)

현재 6단계 파이프라인 (STEP 1~6):
```
STEP 1: TASK → STEP 2: ANALYSIS → STEP 3: PLAN → STEP 4: TODO → STEP 5: TEST-SCENARIO → STEP 6: EXECUTE
```

- **STEP 4 (TODO)**: dtp-todo 워커 디스패치 → 사용자 보고 (QA 없음). 승인 대기
- **STEP 5 (TEST-SCENARIO)**: 독립 STEP으로 dtp-test-scenario 워커 디스패치 → 사용자 보고. "승인 = EXECUTE 시작 허가"
- **STEP 6 (EXECUTE)**: dtp-execute 워커 디스패치 → dtp-test → DONE.md → 완료 보고
- 파이프라인 다이어그램 (L30-36): `dtp-task → dtp-analysis → [QA] → 검토 → dtp-plan → [QA] → 검토 → dtp-todo → 검토 → dtp-test-scenario → 검토/승인 → dtp-execute → [Test] → 완료`
- STATE.md 템플릿 (L202): 단계 목록 `TASK / ANALYSIS / PLAN / TODO / TEST-SCENARIO / EXECUTE`

#### 공통 문제점

1. TEST-SCENARIO가 독립 STEP이므로 컨텍스트 길어지면 스킵되기 쉬움
2. EXECUTE 완료 후 "커밋하지 않는다"는 규칙이 명시되어 있지 않아 무단 커밋 발생

### 영향 범위

- **변경 대상만**: 두 SKILL.md 파일의 내부 구조 변경 (STEP 번호, 파이프라인 다이어그램, STATE.md 템플릿)
- **에이전트 파일**: 변경 없음 — 워커는 디스패치 프롬프트만 받으므로 스킬 내 STEP 순서 변경에 영향받지 않음
- **dtp-test-scenario/SKILL.md**: 변경 없음 — 호출 위치만 이동
- **하위 호환**: 게이트 체크포인트 원칙(각 단계 완료 시 사용자 보고 + 승인 대기)은 유지

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

없음.

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `skills/otp-dev-short/SKILL.md` | STEP 재구성: TEST-SCENARIO를 STEP 2에 통합, STEP 번호 조정, 파이프라인 다이어그램 업데이트, STATE.md 템플릿 수정, EXECUTE 후 커밋 금지 문구 추가 |
| 2 | `skills/otp-dev/SKILL.md` | STEP 재구성: TEST-SCENARIO를 STEP 4에 통합, STEP 번호 조정, 파이프라인 다이어그램 업데이트, STATE.md 템플릿 수정, EXECUTE 후 커밋 금지 문구 추가 |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | otp-dev-short STEP 재구성 + 커밋 규칙 추가 | `skills/otp-dev-short/SKILL.md` | 보통 |
| 2 | otp-dev STEP 재구성 + 커밋 규칙 추가 | `skills/otp-dev/SKILL.md` | 보통 |

### 핵심 설계

#### 변경 1: otp-dev-short — TEST-SCENARIO를 STEP 2에 통합

**Before** (4 STEP):
```
STEP 1: TASK (직접 수행)
STEP 2: PLAN (워커) → QA → PM 검토 → 사용자 보고
STEP 3: TEST-SCENARIO (워커) → 사용자 보고 (승인 = EXECUTE 허가)
STEP 4: EXECUTE (워커) → Test → DONE.md → 완료 보고
```

**After** (3 STEP):
```
STEP 1: TASK (직접 수행)
STEP 2: PLAN + TEST-SCENARIO (연속 워커 디스패치)
  → dtp-plan 워커 → QA → PM 검토
  → dtp-test-scenario 워커 (연속 디스패치)
  → 사용자 보고 (PLAN + TEST-SCENARIO 합산, 승인 = EXECUTE 허가)
STEP 3: EXECUTE (워커) → Test → DONE.md → 완료 보고
```

구체적 변경:
- **frontmatter description**: "4단계" → "3단계"로 변경
- **파이프라인 다이어그램**: 변경된 흐름 반영
- **STEP 2 섹션**: 기존 PLAN 완료 후 QA/PM 검토 이후, TEST-SCENARIO 워커를 연속 디스패치하는 흐름 추가. TEST-SCENARIO 완료 후 "사용자에게 PLAN + TEST-SCENARIO를 함께 보고. 승인 = EXECUTE 시작 허가" 문구
- **STEP 3 삭제**: 기존 독립 TEST-SCENARIO STEP 제거
- **STEP 4 → STEP 3**: 기존 EXECUTE를 STEP 3으로 번호 변경
- **EXECUTE 완료 후 커밋 규칙**: "커밋은 사용자가 명시적으로 요청할 때만 수행한다. 오케스트레이터가 자체적으로 커밋하지 않는다." 문구 추가
- **STATE.md 템플릿**: 단계 목록 `TASK / PLAN+TEST-SCENARIO / EXECUTE`로 변경

#### 변경 2: otp-dev — TEST-SCENARIO를 STEP 4에 통합

**Before** (6 STEP):
```
STEP 1: TASK (직접 수행)
STEP 2: ANALYSIS (워커) → QA → PM 검토 → 사용자 보고
STEP 3: PLAN (워커) → QA → PM 검토 → 사용자 보고
STEP 4: TODO (워커) → 사용자 보고
STEP 5: TEST-SCENARIO (워커) → 사용자 보고 (승인 = EXECUTE 허가)
STEP 6: EXECUTE (워커) → Test → DONE.md → 완료 보고
```

**After** (5 STEP):
```
STEP 1: TASK (직접 수행)
STEP 2: ANALYSIS (워커) → QA → PM 검토 → 사용자 보고
STEP 3: PLAN (워커) → QA → PM 검토 → 사용자 보고
STEP 4: TODO + TEST-SCENARIO (연속 워커 디스패치)
  → dtp-todo 워커 → 사용자 보고 (TODO 결과)
  → dtp-test-scenario 워커 (연속 디스패치)
  → 사용자 보고 (TODO + TEST-SCENARIO 합산, 승인 = EXECUTE 허가)
STEP 5: EXECUTE (워커) → Test → DONE.md → 완료 보고
```

구체적 변경:
- **frontmatter description**: "7단계" → "5단계" (실질 STEP 수)로 변경. 또는 기존 "7단계"가 아닌 표현이면 STEP 수에 맞게 조정
- **파이프라인 다이어그램**: 변경된 흐름 반영
- **STEP 4 섹션**: 기존 TODO 워커 완료 후, TEST-SCENARIO 워커를 연속 디스패치하는 흐름 추가. TEST-SCENARIO 완료 후 "사용자에게 TODO + TEST-SCENARIO를 함께 보고. 승인 = EXECUTE 시작 허가" 문구
- **STEP 5 삭제**: 기존 독립 TEST-SCENARIO STEP 제거
- **STEP 6 → STEP 5**: 기존 EXECUTE를 STEP 5로 번호 변경
- **EXECUTE 완료 후 커밋 규칙**: "커밋은 사용자가 명시적으로 요청할 때만 수행한다. 오케스트레이터가 자체적으로 커밋하지 않는다." 문구 추가
- **STATE.md 템플릿**: 단계 목록 `TASK / ANALYSIS / PLAN / TODO+TEST-SCENARIO / EXECUTE`로 변경

#### 변경 3: 두 스킬 공통 — EXECUTE 후 커밋 금지 규칙

EXECUTE 완료 후 섹션("### EXECUTE 완료 후")에 다음을 추가:

```markdown
### 커밋 규칙

**커밋은 사용자가 명시적으로 요청할 때만 수행한다.** EXECUTE 완료, DONE.md 생성, 테스트 통과 후에도 자동으로 커밋하지 않는다. 완료 보고만 하고 사용자 지시를 기다린다.
```

### 의존성 및 환경 변경

없음. 마크다운 문서 수정만 해당.

### 테스트 전략

| 검증 항목 | 기준 |
|----------|------|
| 파이프라인 다이어그램 정합성 | 다이어그램이 STEP 내용과 일치하는가 |
| STEP 번호 연속성 | 빠진 번호나 중복 번호 없는가 |
| 디스패치 프롬프트 유지 | TEST-SCENARIO 디스패치 프롬프트의 내용(스킬 경로, 이전 산출물 등)이 보존되는가 |
| STATE.md 템플릿 정합성 | 단계 목록이 변경된 STEP 구조와 일치하는가 |
| 커밋 규칙 명시 | 두 스킬 모두 EXECUTE 후 커밋 금지 문구가 존재하는가 |
| 게이트 체크포인트 유지 | 각 단계 완료 시 사용자 보고 + 승인 대기 원칙이 유지되는가 |
| 기존 콘텐츠 보존 | 에스컬레이션 규칙, 구현 금지 원칙, Git 사전 점검 등 비변경 섹션이 손상되지 않았는가 |

## 3. 실행 체크리스트

- [ ] Step 1: otp-dev-short frontmatter 수정 -- `skills/otp-dev-short/SKILL.md` -- description의 "4단계" → "3단계"
- [ ] Step 2: otp-dev-short 파이프라인 다이어그램 업데이트 -- `skills/otp-dev-short/SKILL.md` -- 변경된 흐름 반영
- [ ] Step 3: otp-dev-short STEP 2 재작성 -- `skills/otp-dev-short/SKILL.md` -- PLAN 완료 후 TEST-SCENARIO 연속 디스패치 추가, 승인 = EXECUTE 허가 문구
- [ ] Step 4: otp-dev-short STEP 3 (기존 TEST-SCENARIO) 삭제 -- `skills/otp-dev-short/SKILL.md` -- 독립 TEST-SCENARIO STEP 제거
- [ ] Step 5: otp-dev-short STEP 4 → STEP 3 번호 변경 -- `skills/otp-dev-short/SKILL.md` -- EXECUTE를 STEP 3으로 + 커밋 규칙 추가
- [ ] Step 6: otp-dev-short STATE.md 템플릿 수정 -- `skills/otp-dev-short/SKILL.md` -- 단계 목록 갱신
- [ ] Step 7: otp-dev 파이프라인 다이어그램 업데이트 -- `skills/otp-dev/SKILL.md` -- 변경된 흐름 반영
- [ ] Step 8: otp-dev STEP 4 재작성 -- `skills/otp-dev/SKILL.md` -- TODO 완료 후 TEST-SCENARIO 연속 디스패치 추가, 승인 = EXECUTE 허가 문구
- [ ] Step 9: otp-dev STEP 5 (기존 TEST-SCENARIO) 삭제 -- `skills/otp-dev/SKILL.md` -- 독립 TEST-SCENARIO STEP 제거
- [ ] Step 10: otp-dev STEP 6 → STEP 5 번호 변경 -- `skills/otp-dev/SKILL.md` -- EXECUTE를 STEP 5로 + 커밋 규칙 추가
- [ ] Step 11: otp-dev STATE.md 템플릿 수정 -- `skills/otp-dev/SKILL.md` -- 단계 목록 갱신
- [ ] Step 12: otp-dev frontmatter 확인 -- `skills/otp-dev/SKILL.md` -- description 표현이 STEP 수와 맞는지 확인/수정

## 4. QA 체크리스트

### 기능 테스트

- [ ] otp-dev-short: STEP 2에 PLAN + TEST-SCENARIO가 연속 디스패치로 통합되어 있는가
- [ ] otp-dev: STEP 4에 TODO + TEST-SCENARIO가 연속 디스패치로 통합되어 있는가
- [ ] 두 스킬 모두: EXECUTE 후 "커밋은 사용자가 명시적으로 요청할 때만 수행한다" 문구가 존재하는가
- [ ] 파이프라인 다이어그램이 실제 STEP 구조와 일치하는가
- [ ] STATE.md 템플릿의 단계 목록이 변경된 흐름과 일치하는가

### 회귀 테스트

- [ ] 에스컬레이션 규칙(otp-dev-short)이 유지되는가
- [ ] 구현 금지 원칙이 유지되는가
- [ ] Git 사전 점검이 유지되는가
- [ ] 게이트 체크포인트 원칙이 유지되는가
- [ ] 프로젝트 메모리 동기화가 유지되는가
- [ ] 스킬 탐색 경로가 유지되는가
- [ ] TEST-SCENARIO 디스패치 프롬프트 내용(스킬 경로, 이전 산출물, 모델 등)이 보존되는가
- [ ] execution-plan.json 기반 FE/BE 병렬 로직(otp-dev)이 유지되는가

### 코드 품질

- [ ] 마크다운 헤딩 레벨이 일관되는가 (## STEP, ### 하위)
- [ ] 변경이력에 v1.1 항목이 추가되었는가
- [ ] STEP 번호에 빠짐이나 중복이 없는가

## 5. 기술 컨텍스트

### 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 문서 | 마크다운 (SKILL.md) | 없음 |

### 사용 MCP

없음 — 마크다운 문서 수정 작업.

## 6. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| TEST-SCENARIO 디스패치 프롬프트가 통합 STEP에서 누락 | 테스트 시나리오 미생성 | 기존 디스패치 프롬프트를 그대로 복사하여 통합 STEP 내에 배치 |
| STEP 번호 변경 시 에스컬레이션/세션복원 참조 불일치 | 세션 복원 실패 가능 | STATE.md 템플릿의 단계 목록을 동기화하여 정합성 확보 |
| 연속 디스패치 시 PLAN QA 실패하면 TEST-SCENARIO도 지연 | 설계 산출물 피드백 루프 지연 | QA 통과 후 TEST-SCENARIO 디스패치하므로 품질 게이트는 유지됨 |
