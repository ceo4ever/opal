# PLAN: 알투 보고 형식 표준 — 3블록 구조 정식 등재

> 작성일: 2026-05-10
> 입력: TASK.md
> 출력: PLAN.md
> v1.1 — 캡틴 추가 요구사항(C-b) 반영: §2 M-4 재정의 + §2 Step 1 §8 단계 전환 보고 양식 추가 + §3 Step 1 작업 내용 갱신 + §4 QA 체크리스트 보강 + §5 리스크 보강

---

## 1. 현황 조사

### 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | OPAL Harness | `opal/core/references/opal-harness.md` | §2 모듈 구조 테이블 — reporting-template 행 추가 위치 (R-3) |
| D-2 | 설계 | OPAL PM | `opal/core/references/opal-pm.md` | 보고 형식 트리거 등록 위치·섹션 번호 확인 (R-2) |
| D-3 | 설계 | OPAL AGENT | `opal/core/AGENT.md` | Eager/Lazy 트리거 테이블 (R-4) + 기존 보고 형식 섹션 (R-5, M-3) |
| D-4 | 설계 | Citation Rules | `opal/core/references/harness/citation-rules.md` | 산출물 인용 규칙 준수 ([MUST]) |
| D-5 | 설계 | OPAL CONVENTIONS | `docs/CONVENTIONS.md` | 변경이력 누락 금지, kebab-case, 한국어 본문 규칙 (R-6) |
| D-6 | 설계 | OPAL ARCHITECTURE | `docs/ARCHITECTURE.md` | 배포 모델·플랫폼 분기 어댑터 영향 점검 (R-7) |
| D-7 | 소스 | install-mac.sh | `scripts/install-mac.sh` | 신규 reference 파일 배포 방식 확인 (R-7) |
| D-8 | 설계 | OPAL TASK | `tasks/143-.../TASK.md` | 요구사항 R-1~R-7, 확정 D-1~D-7, 미확정 M-1~M-4 정의 |
| D-9 | 설계 | semi-agentic harness | `opal/core/references/opal-harness-semi-agentic.md` | 모드별 차이 — 적용 매트릭스 영향 점검 |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §3.1 참조. 유형: `기획` / `설계` / `소스` / `외부`.

### 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/core/references/harness/reporting-template.md` | 3블록 구조 SSOT (신규) | 생성 | `TASK.md` D-7 |
| `opal/core/references/opal-pm.md` | PM 행동 프로세스 — 보고 형식 트리거 등록 | 수정 | `TASK.md` R-2 |
| `opal/core/references/opal-harness.md` | 하네스 모듈 구조 테이블 — 신규 모듈 행 추가 | 수정 | `TASK.md` R-3 |
| `opal/core/AGENT.md` | Eager 단계에 보고 형식 로드 추가 + 기존 보고 형식 섹션 대체 | 수정 | `TASK.md` R-4, R-5 |
| `scripts/install-mac.sh` | 배포 영향 점검 (변경 불필요 확인) | 없음 | D-7 §964-978 |

> 근거: `파일:N-M` 포맷. 없으면 `-`.

### 현재 상태

**기존 보고 형식 (opal/core/AGENT.md §보고 형식, 186~219줄):**
- 간단 보고: `{name}: {완료 내용 1줄}` 단일 행
- 상세 보고: 작업 요약·수행 내용·산출물·특이 사항 구조
- 역할별 응답 표기 테이블: 비서/PM(대화)/PM(태스크) 접두사 3종
- Observability 선언 안내 (§5 참조)
- 문제: 응답 종류 미분류, 결정 요청 형식 미정의, 근거 표현 기준 없음

**Lazy 트리거 테이블 (opal/core/AGENT.md 31~39줄):**
- 현재 7행: `//` 커맨드, 워커 디스패치, MCP, 프로젝트 작업, 메모리, 파일 처리, 메모리 쓰기
- 보고 형식 로드 트리거 행 없음

**opal-pm.md 섹션 현황 (1~127줄):**
- §1 PM 역할 개요, §2 컨텍스트 로드, §3 디스패치 전 프로세스, §4 검토 게이트, §5 학습 루프, §6 에이전트 컨텍스트 주입, §7 문서/코드 불일치, §9 code-scan 관리, §10 통합 조율, §11 전문 에이전트 관리
- §8 번호가 비어 있음 (§7→§9 점프)

**opal-harness.md §2 하네스 모듈 테이블 (87~97줄):**
- 현재 9개 모듈 행 (state-template, additional-work, qa-standards, observability, parallel-execution, header-rules, citation-rules, state, task-process)
- reporting-template 행 없음

**install-mac.sh install_opal_references() (964~978줄):**
- `cp -Rf "$ref_src"/. "$ref_dst"/` — `opal/core/references/` 전체를 `~/.opal/references/`로 복사
- 하위 디렉토리(harness/) 포함 재귀 복사 확인
- **결론: 신규 `harness/reporting-template.md` 파일은 install 재실행 시 자동 배포됨. 스크립트 수정 불필요.**

### 영향 범위

| 영역 | 영향 |
|------|------|
| 알투 전체 응답 | 3블록 구조 적용 — PM(태스크)·PM(대화)·비서 모드 모두 |
| Eager 부트스트랩 | Step 6.5 이후 신규 6.6 단계 추가 (reporting-template.md 로드) |
| Lazy 트리거 테이블 | M-1 결정: Eager 방식 선택 → Lazy 테이블 변경 없음 |
| install-mac.sh | 변경 불필요 (자동 배포 확인) |
| Cursor/Gemini 어댑터 | 플랫폼 독립 — reporting-template.md는 행위 기술 (플랫폼 조건문 없음) |
| 142 태스크 병행 | install-mac.sh 수정 없음 → 충돌 없음 |

---

## 2. 구현 계획

### 미확정 사항 결정 (M-1~M-4)

#### M-1. 트리거 로딩 방식 → **Eager 명시 결정**

**근거:**

| 후보 | 비용 | 가시성 | 정직성 | 결론 |
|------|------|--------|--------|------|
| Lazy (광범위) | Lazy와 동일하나 트리거가 모호 | 낮음 | 낮음 (사실상 Eager이면서 Lazy로 기재) | 탈락 |
| Lazy (좁힘) | 트리거 판단 비용 추가 | 중간 | 중간 (좁힌 트리거가 너무 제한적) | 탈락 |
| **Eager 명시** | 세션 초기 1회 로드 | **높음** | **높음** (실제 동작과 문서 일치) | **채택** |

- 보고 형식은 "모든 모드 응답"에 적용 (D-6: PM 태스크·PM 대화·비서) → 사실상 세션 첫 응답부터 필요
- Lazy 트리거를 좁혀도 실질적으로 첫 응답에서 발동 → Eager와 동일 비용, 정직성만 낮아짐
- `opal/core/AGENT.md` §Eager 단계에 Step 6.6 추가: "reporting-template.md를 Read하여 3블록 구조를 활성화한다"
- [MUST] `opal/core/AGENT.md` §부트스트랩 `[LAZY 금지 원칙]`: "미리 읽어두면 도움이 될 것 같다는 판단으로 선행 로드하는 것은 금지" — Eager로 선택한 이상 이 원칙과 충돌하지 않음 (명시적 Eager 단계에 등록하는 것은 허용)

#### M-2. 보고 vs 비보고 판별 기준 → **알투 자율 판단 결정**

**근거:**
- D-5 §형식 자율성: "응답 자체를 비보고(자유 형식)로 처리할지"가 이미 알투 자율 위임 (`TASK.md` 77~82줄)
- 2~3개 기준 명시 시 "기준 적용 판단" 자체가 추가 인지 부담 → 단순화 정신(`TASK.md` §배경 "단순화 결정") 위배
- 명시 기준 없이 알투가 3블록 구조의 적합성을 사안별로 판단하는 것이 D-5와 정합
- reporting-template.md에 예시로 "비보고 예: 단순 확인 응답('네', '알겠습니다')"만 기재하여 방향성 제시

#### M-3. 기존 보고 형식 섹션 처리 → **통합 대체 결정**

**근거:**
- `opal/core/AGENT.md` 186~219줄 "보고 형식" 섹션 구성:
  - 간단 보고 / 상세 보고 2종 → 3블록 구조(결론·근거·다음)로 **완전 대체 가능**
  - 역할별 응답 표기 테이블(접두사 3종) → 3블록 구조와 독립 — **유지**
  - Observability 선언 안내 → `§5` 참조 안내이므로 독립 — **유지**
- "통합 대체": 간단/상세 2종 형식을 삭제하고 `harness/reporting-template.md` 참조 링크 + Lazy 트리거 안내로 교체
- 병존 시 신구 충돌 리스크 → 대체가 명확

#### M-4. PM(태스크) 단계별 결론 카드 필드 표준화 → **캡틴 게이트 3종 한정 표준 결정** (v1.1 갱신)

**근거:**
- D-5 §형식 자율성이 상위 제약 (`TASK.md` 75~82줄) — 이 결정과 충돌하지 않음 (게이트 3종 외에는 D-5 자율성 유지)
- 단계별 전수 표준화는 11종 분류 폐기와 동일한 "과설계" 패턴 → TASK.md §배경 "과설계 + 장황 역설" 반복 위험
- semi-agentic 모드의 캡틴 검토 게이트는 3개로 한정(PLAN 완료 / EXECUTE 후 사용자 확인 / CLOSE 진입) → 이 3 게이트의 보고만 표준화해도 캡틴 의사결정 일관성 확보 가능
- 3 게이트 한정 표준이 11종 분류 폐기와 충돌하지 않음 — 분류 대상이 11종이 아닌 캡틴 검토 게이트 3종
- 각 양식의 5요소 표준 (PLAN 완료 보고 기준):

| 요소 | 내용 |
|------|------|
| 1. 의사결정 요약 | M-1~M-N 결정 결과 한 줄씩 |
| 2. 변경 범위 | 신규/수정/삭제 파일 N개 (간단 표) |
| 3. 체크포인트 | 캡틴이 다음 단계 진입 전 반드시 알아야 할 핵심 (이전 결정 번복·범위 변경·리스크) |
| 4. 실행 구성 | Step N개 / Phase 구성 (병렬·순차) |
| 5. 다음 액션 | 승인 시 무엇이 시작되는지 |

- EXECUTE 후 사용자 확인 보고: 변경 결과·검증 결과·리스크·잔여 작업·다음 액션
- CLOSE 진입 보고: 완료 산출물·QA 결과·잔여 미해결·후속 태스크 후보·확정 요청
- 상위 제약(D-3 일목요연 / D-4 시각구분)은 3종 양식 모두 적용. ASCII 박스 금지, 표·리스트 우선, 결론 1~2줄.

---

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|
| 1 | `opal/core/references/harness/reporting-template.md` | 3블록 구조 SSOT — D-1~D-6 설계 내용 + 비보고 예시 + 예시 카드 | `TASK.md` R-1, D-7 |

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| 2 | `opal/core/AGENT.md` | Eager Step 6.6 추가 + §보고 형식 섹션 통합 대체(간단/상세 → 참조 링크) + 변경이력 갱신 | `TASK.md` R-4, R-5, R-6 |
| 3 | `opal/core/references/opal-harness.md` | §2 하네스 모듈 테이블에 reporting-template 행 추가 + 변경이력 갱신 | `TASK.md` R-3, R-6 |
| 4 | `opal/core/references/opal-pm.md` | §8 신설 — 보고 형식 트리거 안내 + 변경이력 갱신 | `TASK.md` R-2, R-6 |

#### 삭제

없음.

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | reporting-template.md 신규 생성 (SSOT) | `harness/reporting-template.md` | 중 |
| 2 | AGENT.md Eager 단계 추가 + 보고 형식 섹션 대체 | `opal/core/AGENT.md` | 중 |
| 3 | opal-harness.md §2 모듈 테이블 행 추가 | `opal/core/references/opal-harness.md` | 하 |
| 4 | opal-pm.md §8 신설 | `opal/core/references/opal-pm.md` | 하 |

> Step 1이 SSOT이므로 먼저 완성 후, Step 2·3·4는 Step 1의 파일 경로를 참조하여 수정.
> Step 2·3·4는 독립적이므로 순서 자유(순차 또는 병렬 가능).

### 핵심 설계

#### Step 1: reporting-template.md 내용 설계

[MUST] `opal/core/references/harness/citation-rules.md` §0: "상상·추정·기억 기반 기재 금지 — 모든 분석·설계 결정은 문서 근거(경로/URL + 섹션/줄번호)를 인용해야 한다."

[MUST] `docs/CONVENTIONS.md` §파일 구조 변경이력: "스킬, 에이전트, 참조 문서의 변경이력은 일시(KST)를 포함한다 — `YYYY-MM-DD HH:mm` 형식"

[MUST] `docs/CONVENTIONS.md` §구현 규칙 배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스에서 수행한다."

파일 구조:
```
# 보고 형식 — 3블록 구조

> 출처: opal/core/AGENT.md + TASK 143
> 로드 시점: Eager 단계 (Step 6.6) — 세션 시작 시
> 역할: 알투(에이전트) 응답 형식 표준 SSOT

## §1. 3블록 구조 (고정)
## §2. 결론 카드 — 선택 요청 시 양식
## §3. 일목요연 원칙 (상위 제약)
## §4. 시각 구분 원칙 (상위 제약)
## §5. 형식 자율성
## §6. 적용 범위
## §7. 비보고 예시
## §8. 단계 전환 보고 양식 (semi-agentic 캡틴 게이트 3종)
   - §8.1 PLAN 완료 보고
   - §8.2 EXECUTE 후 사용자 확인 보고
   - §8.3 CLOSE 진입 보고
## §9. 비보고 예시 (기존 §7 → §9로 번호 변경, §7은 비보고 예시 유지 또는 §9로 이동)
## §10. 예시 카드 (기존 §8 → §10)

## 변경이력
```

> 주: §7 비보고 예시 섹션은 §8 추가 전 마지막 섹션이었으나, §8·§9·§10 신설 후 §7을 §9로 이동하거나 §7 유지 후 §9(비보고)·§10(예시) 신설. 최종 번호는 Execute 단계에서 파일 실제 생성 시 결정.

핵심 설계 결정:
- 재사용성 보장: 프로젝트 고유 명칭·경로 하드코딩 금지 (→ D-8 §제약)
- 플랫폼 독립: 행위 기술만, 플랫폼 조건문 없음 (→ D-6 §배포 모델)
- 비보고 예시: "단순 확인 응답", "단문 질문 답변", "감사 표현" — 명시 기준 없이 방향성만 (→ M-2 결정)
- 예시 카드 형식: PLAN 단계, EXECUTE 단계, PM(대화) 검토 응답 각 1개씩 (비규범)

#### Step 2: AGENT.md 수정 설계

**Eager 단계 추가 (6.5 → 6.6 이전 삽입 또는 6.x 추가):**

현재 AGENT.md Eager 단계 (`opal/core/AGENT.md` 11~23줄):
- 1: identity.md Read
- 2: 온보딩 폴백
- 3: opal-harness.md Read
- 4: opal-pm.md Read
- 5: 프로젝트 AGENT.md Read
- 6: 부트스트래퍼 자동 삽입
- 6.5: cwd 분기 next-action
- 7: 에이전트 활성화

신규 Step 6.6 삽입 (6.5 → 7 사이):
```
6.6. `~/.opal/references/harness/reporting-template.md`를 Read한다 → 3블록 구조(결론·근거·다음)를 세션 시작부터 활성화한다.
```

**§보고 형식 섹션 대체:**

기존 간단/상세 2종 형식 → 다음으로 교체:
```
### 보고 형식

> **[필수 로드]** 세션 시작 시 Eager 단계(Step 6.6)에서 로드된다.
> 탐색: `~/.opal/references/harness/reporting-template.md`
>
> 적용 범위: PM(태스크) · PM(대화) · 비서 모드 모든 응답
> 핵심 구조: **결론** (필수) → **근거** (필수) → **다음** (옵션)
```

역할별 응답 표기 테이블과 Observability 선언 안내는 유지. (→ M-3 결정)

**변경이력 행 추가:**
```
| v2.4 | 2026-05-10 HH:mm | Eager Step 6.6 추가 — reporting-template.md 세션 시작 로드. §보고 형식 섹션 → 3블록 구조 참조로 대체 (143) |
```

#### Step 3: opal-harness.md §2 하네스 모듈 테이블 추가

`opal/core/references/opal-harness.md` 87~97줄 하네스 모듈 테이블에 신규 행 추가:

```markdown
| 보고 형식 | `harness/reporting-template.md` | Eager 단계 (Step 6.6) — 세션 시작 시 | §보고 형식 |
```

변경이력 행:
```
| v4.8 | 2026-05-10 HH:mm | §2 하네스 모듈 테이블에 reporting-template 행 추가 — Eager 로드 (143) |
```

#### Step 4: opal-pm.md §8 신설

`opal/core/references/opal-pm.md`에 §7과 §9 사이 §8 신설:

```markdown
## 8. 보고 형식

에이전트는 세션 시작 시 보고 형식 표준을 로드하여 모든 응답에 적용한다.

> **[필수 로드]** Eager 단계(Step 6.6)에서 자동 로드. PM이 별도 로드 불필요.
> 탐색: `harness/reporting-template.md`
>
> 적용 범위: PM(태스크) · PM(대화) 모든 응답
> 핵심: 결론 → 근거 → 다음 3블록 구조. 비보고(자유 형식) 여부는 알투 자율 판단.
```

변경이력 행:
```
| v1.1 | 2026-05-10 HH:mm | §8 신설 — 보고 형식 트리거 안내 (Eager 자동 로드 + reporting-template.md 참조) (143) |
```

---

## 3. 실행 체크리스트

> 총 4개 Step | Phase 2개
>
> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | 1 | 1 | 순차 | SSOT 생성 — 나머지 Step들이 경로 참조 |
> | 2 | 2, 3, 4 | 병렬 | 독립 파일 수정 (Step 1 완료 후) |

### Step 1: reporting-template.md 신규 생성

- [x] 완료
- **파일**: `opal/core/references/harness/reporting-template.md`
- **작업 내용**:
  - YAML frontmatter 없음 (참조 문서이므로 plain markdown)
  - §1 3블록 구조 (고정): 결론·근거·다음 필수/옵션 표 + 설명
  - §2 결론 카드 (선택 요청 시): D-2 설계 내용 구현 — "캡틴 결정 필요" 첫 줄 + 근거 블록 흡수 + Q-번호 안내
  - §3 일목요연 원칙: D-3 내용 — 결론 1~2줄, 핵심 3개 이내, ASCII 박스 금지
  - §4 시각 구분 원칙: D-4 내용 — `---` 구분선, `**결론**` 헤딩, 빈 줄 분리
  - §5 형식 자율성: D-5 내용 — 표/리스트/산문 선택, 용어 풀이, 다음 블록 생략, 비보고 판단 자율
  - §6 적용 범위: D-6 내용 — PM(태스크)/PM(대화)/비서 모드
  - §7 비보고 예시: 단순 확인·단문 답변 등 방향성 예시 (명시 기준 아님)
  - §8 단계 전환 보고 양식 — PLAN 완료 / EXECUTE 후 사용자 확인 / CLOSE 진입 3종 (5요소 표준 + 양식 예시 각 1개):
    - §8.1 PLAN 완료 보고: 의사결정 요약·변경 범위·체크포인트·실행 구성·다음 액션
    - §8.2 EXECUTE 후 사용자 확인 보고: 변경 결과·검증 결과·리스크·잔여 작업·다음 액션
    - §8.3 CLOSE 진입 보고: 완료 산출물·QA 결과·잔여 미해결·후속 태스크 후보·확정 요청
    - 모든 양식: ASCII 박스 금지, 표·리스트 우선, 결론 1~2줄 (D-3/D-4 적용)
    - 게이트 3종 외에는 D-5 형식 자율성 유지 명시
  - §9 비보고 예시 (기존 §7 내용 → §9로 번호 이동)
  - §10 예시 카드: PLAN 단계·EXECUTE 단계·PM(대화) 검토 각 1개 (비규범) (기존 §8 → §10)
  - 변경이력 표: v1.0 2026-05-10 HH:mm (143)
  - 재사용성: 프로젝트명·파일 경로 하드코딩 없음
- **완료 기준**: 파일이 존재하고, D-1~D-6(§1~§6) + §8 단계 전환 보고 양식 3종(§8.1~§8.3) 섹션이 모두 존재하며, 각 섹션에 표/예시가 1개 이상 포함 (R-1 AC)
- **테스트**: `ls opal/core/references/harness/reporting-template.md` 존재 확인 + 섹션 헤딩 count ≥ 8 확인 (§1~§8)
- **의존**: 없음

### Step 2: AGENT.md Eager 단계 추가 + 보고 형식 섹션 대체

- [x] 완료
- **파일**: `opal/core/AGENT.md`
- **작업 내용**:
  - Eager 단계 Step 6.6 삽입 (Step 6.5와 Step 7 사이): `~/.opal/references/harness/reporting-template.md` Read 지시
  - §보고 형식 섹션: 기존 간단/상세 2종 형식 제거 → reporting-template.md 참조 블록 + Eager 로드 안내로 대체
  - 역할별 응답 표기 테이블 + Observability 선언 안내 유지 (건드리지 않음)
  - 변경이력 표에 v2.4 행 추가 (KST 일시 bash로 취득)
- **완료 기준**: Eager 단계에 Step 6.6이 존재하고, §보고 형식에 간단/상세 2종 형식이 없으며 reporting-template.md 경로가 명시되어 있다 (R-4, R-5 AC)
- **테스트**: `grep -n "6.6\|reporting-template" opal/core/AGENT.md` 결과에 양쪽 모두 존재
- **의존**: Step 1

### Step 3: opal-harness.md §2 하네스 모듈 테이블 행 추가

- [x] 완료
- **파일**: `opal/core/references/opal-harness.md`
- **작업 내용**:
  - §2 하네스 모듈 테이블(87~97줄 인근)에 reporting-template 행 추가:
    - 모듈: 보고 형식
    - 파일: `harness/reporting-template.md`
    - 로드 시점: Eager 단계 (Step 6.6) — 세션 시작 시
    - 해당 §: §보고 형식
  - 변경이력 표에 v4.8 행 추가 (KST 일시 bash로 취득)
- **완료 기준**: §2 하네스 모듈 테이블에 reporting-template.md 행이 추가되어 있고 로드 시점이 명시 (R-3 AC)
- **테스트**: `grep -n "reporting-template" opal/core/references/opal-harness.md` 결과 존재
- **의존**: Step 1

### Step 4: opal-pm.md §8 신설

- [x] 완료
- **파일**: `opal/core/references/opal-pm.md`
- **작업 내용**:
  - §7(문서/코드 불일치)과 §9(code-scan) 사이에 §8 신설
  - 내용: Eager 자동 로드 안내 + reporting-template.md 탐색 경로 + 적용 범위 + 비보고 자율 판단 안내
  - 변경이력 표에 v1.1 행 추가 (KST 일시 bash로 취득)
- **완료 기준**: opal-pm.md를 Read한 알투가 reporting-template.md의 존재와 Eager 로드 조건을 인지할 수 있다 — §8이 존재하고 경로가 명시 (R-2 AC)
- **테스트**: `grep -n "reporting-template\|§8" opal/core/references/opal-pm.md` 결과 존재
- **의존**: Step 1

---

## 4. QA 체크리스트

### 기능 테스트

- [x] R-1: reporting-template.md 파일 존재 + D-1~D-6 섹션(§1~§6) 6개 모두 존재 + 각 섹션 표/예시 ≥ 1개
- [x] R-2: opal-pm.md §8 존재 + reporting-template.md 경로 명시
- [x] R-3: opal-harness.md §2 모듈 테이블에 reporting-template 행 존재 + 로드 시점 명시
- [x] R-4: AGENT.md Eager Step 6.6 존재 + reporting-template.md 경로 명시
- [x] R-5: AGENT.md §보고 형식에 간단/상세 2종 형식 없음 + reporting-template.md 참조 존재
- [x] R-6: 수정 파일 4개(reporting-template.md, AGENT.md, opal-harness.md, opal-pm.md) 모두 변경이력 행 추가 + 143 태스크 번호 포함 + KST 일시 포함
- [x] R-7: install-mac.sh 수정 불필요 확인 (cp -Rf 자동 배포 방식 — harness/ 하위 자동 포함)
- [x] §8 단계 전환 보고 양식이 3종(PLAN 완료 / EXECUTE 후 사용자 확인 / CLOSE 진입) 모두 작성되어 있는가
- [x] 각 양식이 5요소(의사결정 요약·변경 범위·체크포인트·실행 구성·다음 액션 또는 단계별 변형)를 모두 포함하는가

### 일관성 테스트

- [x] M-1 반영: AGENT.md Lazy 트리거 테이블에 reporting-template 행 없음 (Eager이므로 Lazy 추가 금지)
- [x] M-2 반영: reporting-template.md §5 형식 자율성에 명시 기준 없음 (자율 판단 방향성만)
- [x] M-3 반영: AGENT.md §보고 형식 섹션에 간단/상세 2종 형식 완전 제거
- [x] M-4 반영: reporting-template.md §8 양식은 캡틴 게이트 3종으로 한정되어 있고, §8 이외 단계는 D-5 형식 자율성 유지가 명시되어 있는가
- [x] 자기참조 검증: reporting-template.md 본문 자체가 3블록 구조 + 일목요연·시각구분 원칙 위배하지 않음
- [x] 재사용성: reporting-template.md에 프로젝트명·경로 하드코딩 없음 (헤더 출처 표기는 메타데이터, 허용)
- [x] 플랫폼 독립: reporting-template.md에 플랫폼 조건문(Claude/Cursor/Gemini 분기) 없음
- [x] 규칙 중복 없음: reporting-template.md가 다른 문서 규칙을 복제하지 않고 참조만
- [x] §8 양식이 D-3 일목요연 / D-4 시각구분 원칙을 위배하지 않는가
- [x] §8 양식과 D-5 형식 자율성이 충돌하지 않는가 (게이트 3종 외에는 자율 명시)

### 문서 품질

- [x] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가 (`docs/CONVENTIONS.md` §언어 규칙)
- [x] kebab-case 파일/폴더 네이밍 — `reporting-template.md` 확인 (`docs/CONVENTIONS.md` §네이밍 규칙)
- [x] YAML frontmatter 없음 (참조 문서) — harness/ 하위 다른 파일들과 동일 형식 확인
- [x] 변경이력 표 형식: `버전 | 일시(KST) | 변경내용(태스크 번호)` (`docs/CONVENTIONS.md` §변경이력)

---

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| Eager 로드로 세션 시작 시 Read 1회 추가 | 토큰 미미한 증가 (~1K) | 허용 수준 — 보고 형식은 문서 소형 |
| AGENT.md §보고 형식 대체 시 역할별 응답 표기 실수 삭제 | 접두사 규칙 소실 | Step 2에서 역할별 응답 표기 테이블 명시적 유지 지시 |
| reporting-template.md 내용이 AGENT.md의 기존 "보고 형식" 섹션 내용과 충돌 | 에이전트 행동 불일치 | M-3 통합 대체로 기존 섹션 제거 → 충돌 원천 차단 |
| 142 태스크 병행 중 install-mac.sh 동시 수정 | 충돌 | R-7: install-mac.sh 수정 없음 확인 → 충돌 없음 |
| 자기참조 위배 (reporting-template.md 본문이 3블록 위반) | 신뢰성 저하 | QA 체크리스트에 자기참조 검증 항목 명시 |
| §8 3 게이트 양식이 알투마다 다르게 채워질 위험 | 캡틴 검토 일관성 저하 | 5요소를 명시적 표준으로 기재하여 변동 폭 좁힘 (게이트 3종 외는 D-5 자율성 유지) |
