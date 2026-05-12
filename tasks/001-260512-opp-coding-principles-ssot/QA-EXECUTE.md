# QA-EXECUTE: 카르파시 행동 원칙 흡수

> 검토일: 2026-05-12 | 판정: Pass

## 1. 요약

EXECUTE 단계에서 8개 파일(신규 1 + 수정 7)에 대해 TASK.md F-1~F-5 AC를 검증했다. 모든 필수 요구사항이 충족되었으며, 코딩 원칙 SSOT(`coding-principles.md`)가 정상 신설되었고 워커·PM 자가 로드 규칙, 하네스 통합, AC 작성 가이드 보강, TEST-SCENARIO 매핑 규칙이 모두 적용되었다. 변경이력 표 일시는 KST 포맷(2026-05-12 11:16)으로 통일되었고 모든 파일에 태스크 번호 (001)이 포함되었다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| F-1a | coding-principles.md 파일 존재 | Pass | 경로: `opal/core/references/harness/coding-principles.md` |
| F-1b | 6개 섹션 헤딩 존재 | Pass | §1 TASK, §2 PLAN, §3 TEST-SCENARIO, §4 EXECUTE, §5 QA Gate, §6 적용 매트릭스 |
| F-1c | §3 희박 케이스 5행 매트릭스 | Pass | 높음/높음, 높음/낮음, 낮음/높음, 낮음/낮음, 불가능/— 5행 완성 |
| F-1d | Frontmatter 적용 주체·로드 시점 명시 | Pass | "코드 변경하는 모든 주체" + "워커 EXECUTE 진입 / PM 그냥 해 진입" 2줄 명시 |
| F-1e | 변경이력 표 v1.0 행 | Pass | "2026-05-12 11:16" + "(001)" 포함 |
| F-1 추가 | §6 적용 매트릭스 전재 확인 | Pass | TASK.md §"배경 분석"의 카르파시↔OPAL 표와 동일 (카르파시 4원칙 × 5단계) |
| F-2a | 워커 3개 에이전트 coding-principles.md 참조 | Pass | FE (라인 27), BE (라인 26), Task (라인 62) 각 1줄 이상 포함 |
| F-2b | 3개 에이전트 변경이력 표 추가 | Pass | FE/BE v1.1, Task v1.1 각각 "2026-05-12 11:16" + "(001)" 행 추가 |
| F-2 추가 | M-3 도메인별 트리거 차이 준수 | Pass | FE: `op-dev-execute` ∨ `op-dev-wireframe`, BE: `op-dev-execute`, Task: `op-dev-execute` ∨ `op-task-execute` |
| F-3a | "그냥 해" 표 Coding Principles 행 | Pass | opal/core/AGENT.md 라인 147에 "Coding Principles (코드 파일 변경 시)" 행 등재 (유지 카테고리) |
| F-3b | AGENT.md 변경이력 표 추가 | Pass | v2.5, "2026-05-12 11:16", "(001)" 행 추가 |
| F-4a | op-task SKILL.md 카르파시 §4 인용문 | Pass | "Strong criteria let you loop independently. Weak criteria require constant clarification." 원문 인용 + 한국어 설명 병기 |
| F-4b | Bad/Good 표 2행 이상 | Pass | 기존 1행 + 신규 1행 = 2행 완성 (SSOT 예시 행) |
| F-4c | op-task SKILL.md 변경이력 표 | Pass | v1.6, "2026-05-12 11:16", "(001)" 행 추가 |
| F-5a | TEST-SCENARIO 체크리스트 매핑 의무 | Pass | op-dev-test-scenario SKILL.md 라인 136에 "AC ↔ verify check 매핑 표" 체크리스트 항목 추가 |
| F-5b | 매핑 표 형식 예시 제공 | Pass | TEST-SCENARIO.md 통일 형식(라인 111-115)에 AC ID / 대응 시나리오 / 비고 3열 예시 포함 |
| F-5c | op-dev-test-scenario SKILL.md 변경이력 | Pass | v1.3, "2026-05-12 11:16", "(001)" 행 추가 |
| F-6a | opal-harness.md §2 테이블 coding-principles 행 | Pass | 라인 99에 "Coding Principles" 행 추가, §10 참조 |
| F-6b | opal-harness.md §10 stub 신설 | Pass | 라인 240-247에 "## 10. Coding Principles" 섹션 신설, 적용 주체/시점/PM Gate 검증 명시 |
| F-6c | opal-harness.md 변경이력 표 | Pass | v4.9, "2026-05-12 11:16", "(001)" 행 추가 |
| G-1 | 변경이력 표 일시 형식 | Pass | 모든 파일 "2026-05-12 11:16" KST 포맷 통일 |
| G-2 | 변경이력 표 태스크 번호 | Pass | 모든 7개 수정 파일 + 신규 coding-principles.md에 "(001)" 포함 |
| H-1 | 에이전트 파일 경로 일관성 | Pass | FE/BE/Task 모두 `opal/core/references/harness/coding-principles.md` 경로 일치 |
| H-2 | 로드 시점 일관성 | Pass | coding-principles.md frontmatter "워커 EXECUTE 진입 / PM 그냥 해 진입" ↔ opal-harness.md §10 "EXECUTE 단계 진입 시 / PM 그냥 해 진입" ↔ AGENT.md "그냥 해" 표 "코드 파일 변경 시" 일관 |
| I-1 | 회귀 방지 — 8개 파일 외 수정 | Pass | git status: 8개 파일만 변경, .opal/ 배포 파일 직접 편집 없음 |
| J-1 | 한국어 본문 + 영어 필드명 | Pass | CONVENTIONS.md §언어 규칙 준수 |
| J-2 | kebab-case 파일명 | Pass | `coding-principles.md` ✅ |
| J-3 | YAML frontmatter 유효성 | Pass | coding-principles.md 헤더 `---` 쌍 정상 |

## 3. 지적 사항

지적 사항 없음. 모든 AC가 명시적으로 충족되었으며 추가 경고나 정정 사항이 없다.

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md F-1 AC (a)~(e) | 신규 파일 + 헤딩 + 매트릭스 + frontmatter + 변경이력 | Pass |
| TASK.md F-2 AC (a)~(b) + M-3 | 워커 3종 자가 로드 + 도메인별 스킬 차이 | Pass |
| TASK.md F-3 AC (a)~(b) | "그냥 해" 표 Coding Principles 행 추가 | Pass |
| TASK.md F-4 AC (a)~(c) | 카르파시 §4 인용 + Bad/Good 표 + 변경이력 | Pass |
| TASK.md F-5 AC (a)~(c) | TEST-SCENARIO 매핑 의무 + 형식 예시 + 변경이력 | Pass |
| PLAN.md §4 실행 체크리스트 | Step 1~8 모두 완료 | Pass |
| PLAN.md §5 QA 체크리스트 | 기능 테스트 + 일관성 테스트 + 문서 품질 + 리스크 대응 | Pass |

## 5. 판정

**Pass**

EXECUTE 단계에서 PLAN.md의 8 Step(Step 1 SSOT 신설 ~ Step 8 매핑 룰)이 모두 정상 완료되었다.

- ✅ F-1: 카르파시 4원칙 SSOT(`coding-principles.md`) 신설 완료 — 6섹션 + 희박 케이스 매트릭스 + frontmatter + 변경이력
- ✅ F-2: 워커 3종 자가 로드 규칙 추가 완료 — 도메인별 스킬 트리거 차이(FE: wireframe 포함, BE: 미포함, Task: op-task-execute 추가) 정확 반영
- ✅ F-3: PM "그냥 해" 적용 범위 표 갱신 완료 — Coding Principles 행 등재
- ✅ F-4: op-task AC 작성 가이드 보강 완료 — 카르파시 §4 원문 인용 + Bad/Good 예시 2행
- ✅ F-5: TEST-SCENARIO 매핑 규칙 추가 완료 — 체크리스트 항목 + 형식 예시
- ✅ F-6: 하네스 통합 완료 — opal-harness.md §2 테이블 + §10 stub
- ✅ G: 변경이력 표 — 모든 파일 KST 일시 + 태스크 번호 (001) 통일
- ✅ H: 일관성 — 파일 경로/로드 시점/로드 조건 전역 일치
- ✅ I: 회귀 방지 — 8개 파일만 변경, 배포 경계 준수
- ✅ J: 품질 — 한국어/영어 규칙, kebab-case, YAML 유효성

코딩 원칙 SSOT는 카르파시 4원칙(Think / Simplicity / Surgical / Goal-Driven)을 OPAL 4단계(TASK / PLAN / TEST-SCENARIO / EXECUTE) + QA Gate에 명확히 매핑했으며, 워커와 PM 모두가 자동으로 로드할 수 있도록 설계되었다. PLAN 단계에서 예상한 8개 파일 수정·신설 모두 정상 완료되었고, 모든 변경사항이 일관성 있게 적용되었다.

## 6. 체크리스트 갱신 결과

PLAN.md §4 실행 체크리스트의 Step 1~8이 모두 완료되었으므로 다음과 같이 갱신해야 한다:

```markdown
### Step 1: coding-principles.md SSOT 신설 (F-1)
- [x] 완료

### Step 2: opal-harness.md §2 테이블 + §10 stub 추가 (F-1 하네스 정합, M-2)
- [x] 완료

### Step 3: opal/core/AGENT.md "그냥 해" 표 갱신 (F-3)
- [x] 완료

### Step 4: opal-fe-agent/AGENT.md 자가 로드 룰 추가 (F-2)
- [x] 완료

### Step 5: opal-be-agent/AGENT.md 자가 로드 룰 추가 (F-2)
- [x] 완료

### Step 6: opal-task-agent/AGENT.md 자가 로드 룰 추가 (F-2, M-4)
- [x] 완료

### Step 7: op-task SKILL.md AC 작성 가이드 보강 (F-4)
- [x] 완료

### Step 8: op-dev-test-scenario SKILL.md 매핑 룰 추가 (F-5, M-1)
- [x] 완료
```

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-05-12 11:25 | 초기 작성 — F-1~F-6 AC 전항 검증, 일관성·품질·회귀 확인, 판정 Pass (001) |
