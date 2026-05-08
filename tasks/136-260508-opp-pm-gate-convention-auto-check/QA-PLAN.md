# QA: PLAN — PM Gate 컨벤션 자동 진단

> 검토일: 2026-05-08 | 판정: **Pass**

## 1. 요약

PLAN.md는 PM Gate에 "컨벤션 자동 진단" 항목(§13)을 신설하는 6개 단계의 실행 계획을 제시한다. TASK.md의 R-1~R-8 요구사항을 모두 커버하며, 각 요구사항별로 파일 수정 대상, 변경 내용, 구현 순서를 명확히 정의했다. 참조 문서 테이블(D-1~D-14)을 통해 설계 근거를 추적 가능하게 제시하고, 핵심 설계 제약사항(MUST 포맷)을 적용하였다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| GP-1 | TASK 반영 | Pass | R-1~R-8 모두 PLAN §3 실행 체크리스트(Step 1~6)로 분해됨 |
| GP-2 | 파일 목록 완전성 | Pass | §2 구현 계획에 6개 수정 파일 명확히 분리 (신규 파일 0개, 삭제 파일 0개) |
| GP-3 | 설계 구체성 | Pass | §2 핵심 설계에서 각 Step별 구체적 변경 내용 및 [MUST] 제약 명시 |
| GP-4 | 참조 문서 테이블 | Pass | §1에 D-1~D-14 14개 항목 모두 유형/경로/참조이유 컬럼 포함 |
| GP-5 | 인라인 인용 적용 | Pass | §2 핵심 설계에 (→ D-N) 단축 참조 및 `경로:줄번호` 포맷 적용 |
| GP-6 | [MUST] 포맷 적용 | Pass | §2 Step 1, Step 2에서 citation-rules.md 근거 인용 및 state.md 제약 명시 |
| GP-7 | 구현 순서 정합성 | Pass | §2 구현 순서·Phase 그룹핑·의존성 명시; Step 1 SSOT 우선 → Step 2 동기 → Step 3~6 병렬 순서 일관 |
| GP-8 | 하위 호환 정의 | Pass | §1.5 현황 조사 표에서 `.opal/AGENT.md` 미존재 시 자동 스킵 명시 (§판정 4번째 항목) |
| GP-9 | citation-rules 준수 | Pass | citation-rules.md §3.1 참조 테이블 스키마 일관 적용; 인라인 인용 (→ D-N) 포맷 적용 |
| GP-10 | 스킵 조건 명확성 | Pass | §2 Step 1 핵심 설계 및 §3 Step 1 완료 기준에서 changed_files=0 / 컨벤션 적용 외 / CONVENTIONS.md 부재 3종 명시 |
| GP-11 | 리스크 관리 | Pass | §5 리스크에서 R-T1~R-T6 6개 리스크 식별 및 대응 전략 기재 |
| GP-12 | oppd 비변경 사유 | Pass | §1.5 및 §2 Step 3~6 설계 결정에서 oppd PM Gate 점검 목록 섹션 부재 사유 명시 |

## 3. 지적 사항

### 완전성 검증 — R-1~R-8 매핑

| R# | 요구사항 | PLAN §3 Step | 커버 상태 |
|---|---------|-------------|---------|
| R-1 | pm-review-gate.md §검토 절차 §13 신설 (4개 이상 소절) | Step 1 | ✅ 완전 |
| R-2 | D-1 §13 내 D-3 라우팅 규약 명시 또는 링크 포함 | Step 1 설계 결정 | ✅ 완전 |
| R-3 | opal-convention-checker §입력 명세 "PM Gate 호출 시나리오" 추가 | Step 2 | ✅ 완전 |
| R-4 | D-2 §Phase 5 보고서 파일명 단일/영역별 2종 규약 | Step 2(b)/(c) | ✅ 완전 |
| R-5 | D-1 §13 판정 기준 표 (Critical/High=Fail, Medium=Pass) | Step 1 설계 결정 | ✅ 완전 |
| R-6 | D-1 §13 스킵 조건 3종 명문화 | Step 1 설계 결정 | ✅ 완전 |
| R-7 | D-1 §13 `.opal/AGENT.md` 미존재 시 스킵 | Step 1 설계 결정 | ✅ 완전 |
| R-8 | opp/opd/opds/opdw SKILL.md PM Gate 점검 목록 갱신 + oppd 비변경 사유 | Step 3~6 + 비변경 사유 | ✅ 완전 |

### 세부 항목 검증

#### 1) 참조 문서 테이블 (§1 현황 조사)

- **14개 항목 모두 기재됨**: D-1(pm-review-gate.md) ~ D-14(oppd SKILL.md)
- **컬럼 규정 준수**: 유형(설계 일관), 문서/사이트, 경로/URL(백틱 포맷), 참조이유(한 줄 요약)
- **관련 파일 테이블**: 9개 파일 변경 필요성과 줄번호 명시

#### 2) 현황 조사 정밀도 (§1.3 관련 파일)

- `pm-review-gate.md:18-46` 현재 12개 항목 명시 ✅
- `opal-convention-checker/AGENT.md:21-33` (입력) / `:132-156` (Phase 5) / `:160-167` (Phase 6) 줄번호 정확 ✅
- `context-injection.md:60-86` 라우팅 의사코드 명시 ✅
- 4개 오케스트레이터 SKILL.md 현재 PM Gate 점검 목록 행 파악 ✅

#### 3) 핵심 설계 (§2)

**Step 1 — pm-review-gate.md §13 신설**:
- 트리거 조건: changed_files ∩ (docs/ 외 파일) ≥1건 정의 ✅
- 영역 분할: D-3 context-injection.md §라우팅 인용 (→ D-3) ✅
- 호출 명령: opal-convention-checker 워커 디스패치 형식 ✅
- 판정 기준 표: Critical/High = Fail / Medium = Pass 명시 ✅
- 스킵 조건 3종: 번호 매겨 명시 ✅
- 하위 호환: `.opal/AGENT.md` 미존재 시 PM Gate 자체 스킵 인용 ✅
- [MUST] 포맷: citation-rules.md §2.4, state.md §15 근거 인용 ✅

**Step 2 — opal-convention-checker 입력/Phase 5/6**:
- §입력 명세 PM Gate 시나리오 표: 7개 파라미터(task_folder/target_files/timestamp/checklist_path/template_path/project_root/scope) 매핑 ✅
- Phase 5 file_suffix 변수: 단일(`{timestamp}`) / 영역별(`{scope}-{timestamp}`) 2종 규약 ✅
- Phase 6 JSON: artifact_path 및 changed_files 동기 갱신 ✅

**Step 3~6 — 4개 오케스트레이터 SKILL.md**:
- 글로브 패턴(`GC-CONVENTION-*.md`) 일관 적용 ✅
- 변경이력 버전 명시(v2.8, v3.5, v2.x 등) ✅

#### 4) 설계 결정의 일관성

- **TS 분리 규약**: 병렬 호출 시 각 호출별 고유 ts 사용 → 파일명 충돌 방지 명시 ✅
- **oppd 비변경 사유**: PM Gate 점검 목록 섹션 부재 + Phase 3 위임 호출로 자동 적용 ✅
- **opgc 적용 범위 외**: 본 태스크는 PM Gate 자동 진단이며 opgc는 CHECK 단계 별개 라이프사이클 ✅

#### 5) 리스크 관리 (§5)

| 리스크 ID | 내용 | 대응 전략 |
|---------|------|---------|
| R-T1 | OPAL 단일 문서 — 영역 분할 실증 불가 | 단일 호출 폴백 검증 + 풀스택 프로젝트 위임 |
| R-T2 | Phase 5/6 동기 갱신 누락 | `file_suffix` 단일 변수 도입 + QA 검증 |
| R-T3 | 호출 비용 증가 | EXECUTE PM Gate 1회 + 스킵 조건 3종 차단 |
| R-T4 | opd/opds EXECUTE 행 부재 근거 불명 | 별도 후속 태스크 분리 + STEP 4 PM Gate 명시화 검토 |
| R-T5 | tasks/ 경로 docs/ 변경 충돌 가능성 | 검증 결과: 실질적 충돌 없음 (tasks/ 컨벤션 적용 외) |
| R-T6 | oppd 위임 호출 검증 부재 | Phase 3 위임으로 자동 적용 (oppd 수정 불필요) |

모든 리스크가 구체적 대응 전략과 함께 문서화됨. **R-T4는 별도 후속 태스크 분리 명시** — 본 태스크 스코프 외. ✅

#### 6) citation-rules.md 준수

**§1 참조 문서 테이블**: 
- 포맷: `| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |` — citation-rules.md §3.1 스키마 일치 ✅

**§2 핵심 설계 인라인 인용**:
- 단축 참조: `(→ D-N)` 및 `(→ D-N §섹션)` 형식 적용 ✅
- 코드 참조: `` `pm-review-gate.md:18-46` `` / `` `opal-convention-checker/AGENT.md:21-33` `` 등 줄번호 포함 ✅
- [MUST] 포맷: citation-rules.md §2.4 및 state.md §15 원문 인용 ✅

#### 7) 구현 순서 및 의존성

**§2 구현 순서**:
- Phase 1 (Step 1): pm-review-gate.md SSOT 정의 — 후속 의존
- Phase 2 (Step 2): opal-convention-checker 입력/Phase 명세 — Step 1 인용
- Phase 3 (Step 3~6): 4개 SKILL.md 병렬 갱신 — Step 2 `GC-CONVENTION-*.md` 파일명 규약 인용

**의존성 명시**: "Step 2의 파라미터 명세를 Step 1의 §13 호출 절차에서 정의된 파라미터와 일관되게 인용해야 함" ✅

#### 8) 실행 체크리스트 (§3)

- 6개 Step 모두 상세 정의:
  - **Step 1~2**: 순차 (SSOT 우선)
  - **Step 3~6**: 병렬 (파일 독립)
- 각 Step별 완료 기준, 테스트 명령, 의존성 명시 ✅
- grep 명령으로 검증 가능한 구체적 테스트 케이스 포함 ✅

#### 9) QA 체크리스트 (§4)

**기능 테스트 (R-1~R-8)**: 각 요구사항별 검증 항목 정의 ✅
- R-1: pm-review-gate.md §검토 절차 §13 존재 + 7개 소절
- R-2: D-3 인용 + 폴백 정의
- R-3: PM Gate 호출 시나리오 표 + timestamp 분리
- R-4: 단일/영역별 파일명 규약
- R-5: 판정 기준 표 + Fail 시 재지시 흐름
- R-6: 스킵 조건 3종 명시
- R-7: AGENT.md 미존재 자동 스킵
- R-8: 4개 SKILL.md 갱신 + oppd 비변경 사유

**일관성 테스트**: 
- D-1 §13 파라미터 vs opal-convention-checker §PM Gate 호출 시나리오 동기 검증 ✅
- file_suffix 변수 Phase 5/6 동기 ✅
- 4개 SKILL.md `GC-CONVENTION-*.md` 글로브 패턴 통일 ✅

**문서 품질**:
- 한국어 + 영문 코드명 규칙 ✅
- kebab-case 파일명 (`pm-review-gate.md`, `GC-CONVENTION-*.md`) ✅
- 모든 파일 변경이력 표 형식 일관 ✅
- STATE.md 직접 편집 없음 ✅
- `~/.opal/` 배포 파일 편집 없음 ✅

#### 10) 영향 범위 분석 (§1 영향 범위)

- PM Gate 동작 변화 (opp/opd/opds/opdw): 명시 ✅
- oppd 간접 적용 (위임 호출): 명시 ✅
- 워커 호출량 증가 (단일 +1 / 풀스택 +N): 수치 명시 ✅
- 태스크 폴더 산출물 추가: 파일명 규약 명시 ✅
- 하위 호환 보장 (3가지 시나리오): 명시 ✅

### 종합 판정

모든 검증 항목이 **Pass** 상태. 지적 사항 없음.

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md R-1~R-8 | PLAN §3 Step 1~6으로 1:1 분해 및 커버 여부 | Pass |
| TASK.md 관련 문서 D-1~D-9 | PLAN §1 참조 문서 테이블 D-1~D-14 포함 여부 | Pass |
| TASK.md 제약 조건 | PLAN §2 핵심 설계에서 [MUST] 포맷 인용 | Pass |
| citation-rules.md | 참조 테이블 스키마 + 인라인 인용 + [MUST] 포맷 준수 | Pass |
| state.md | STATE.md 직접 편집 비금지 명시 | Pass |

## 5. 판정

**Pass**

PLAN.md는 TASK.md의 R-1~R-8 요구사항을 완전히 반영하고 각 요구사항을 분해 가능한 6개 실행 Step으로 분해했다. 참조 문서 14개(D-1~D-14)를 명확히 추적하고, 핵심 설계 결정에 citation-rules.md 인라인 인용과 [MUST] 포맷을 적용하였다. 구현 순서와 의존성이 명확하고, 리스크 6종을 식별 및 대응 전략을 제시했다. 모든 검증 기준을 만족하므로 실행 단계 진행이 가능하다.

---

## 부록: TASK.md 체크박스 갱신 현황

QA 1차 갱신에 따라 TASK.md 요구사항 체크박스 갱신 예정:

```markdown
## 요구사항

- [x] **R-1: PM Gate 검토 항목 신설** — §3 Step 1에서 완전 커버
- [x] **R-2: 영역 자동 판정 규약 명시** — §3 Step 1 설계 결정에서 D-3 인용 + 폴백 명시
- [x] **R-3: opal-convention-checker 입력 명세 확장** — §3 Step 2에서 PM Gate 호출 시나리오 표 정의
- [x] **R-4: 보고서 파일명 규약 정의** — §3 Step 2(b)/(c)에서 단일/영역별 2종 규약 명시
- [x] **R-5: 판정 기준 명문화** — §3 Step 1 설계 결정에서 Critical/High=Fail 표 정의
- [x] **R-6: 스킵 조건 명문화** — §3 Step 1 설계 결정에서 3종 명시
- [x] **R-7: 하위 호환성 명문화** — §3 Step 1 설계 결정에서 AGENT.md 미존재 시 스킵 인용
- [x] **R-8: SKILL.md PM Gate 점검 목록 갱신 검토** — §3 Step 3~6 + 비변경 사유(oppd)로 완전 정의
```
