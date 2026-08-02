# PLAN: 워커 중단 복구 프로토콜 + 디스패치 산출량 상한 + 증분 저장 규율 SSOT화

> 작성일: 2026-08-02 | 입력: TASK.md (ANALYSIS.md 없음 — 코드/문서 직접 분석 수행)
> 모드: Multi-Feature | 트랙: 프레임워크 문서·규칙 (코드 변경 0건)

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

078·079에서 실증된 워커 인프라 실패 완화 조합(분할 배치 + 전체 파일 통독 금지 + 증분 저장)이 PM 세션 프롬프트에만 존재해 080에서 재적용 누락 → 동일 실패 5회 재발했다. 이 조합을 하네스 SSOT 3곳(재시도 수치 / 판정 절차 / 산출량·저장 규율)에 **각 규칙 1소유자** 원칙으로 등재하여, 다음 PM이 즉흥 대응 없이 재현할 수 있게 한다.

변경은 Markdown 5파일 + 배포 실행 + 메모리 졸업으로 한정한다. 런타임 동작검증이 성립하지 않으므로 **앵커 존재 grep · 참조 무결성 · 배포본 일치** 3종 정합성 검증으로 대체한다 (→ D-0 §제약 조건).

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | 워커 중단 복구 프로토콜 (수치 + 절차 분리 등재) | REQ-1, REQ-2 | P0 | 없음 |
| F-002 | 디스패치 산출량 상한 (SSOT + 참조 1줄) | REQ-3 | P0 | 없음 |
| F-003 | 증분 저장 + 입력 축소 규율 (전 워커 공통 고정) | REQ-4 | P0 | 없음 |
| F-004 | 변경이력·배포 반영 + 개선 후보 메모리 졸업 | REQ-5, REQ-6 | P1 | F-001, F-002, F-003 |

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 (opal-harness §1 · pm-review-gate 신규 절) ─┐
F-002 (dispatch-process Step 6 · §7.4 참조) ──────┼─ F-004 (변경이력 · install · MEMORY 졸업)
F-003 (dispatch-process 템플릿 · op-dev-execute) ─┘

※ F-002 → F-003 은 파일 공유(dispatch-process.md) 관계로 동일 배치 순차 편집 (→ D-0 §제약 조건)
※ F-002 내부: Step 6(SSOT) → §7.4(참조) 순서 강제 — 참조 대상 선행 존재
```

### 1.4 핵심 제약 (원문 인용 — 재해석 금지)

- [MUST] `~/.opal/PRINCIPLES.md` §Core Stance: "Enforce, don't just advise: if a rule must always hold, a tool gates it — not prose." (`~/.opal/PRINCIPLES.md:15`)
- [MUST] `~/.opal/PRINCIPLES.md` §Governance: "Lower docs reference these principles; they don't restate them." (`~/.opal/PRINCIPLES.md:43`)
- [MUST] `~/.opal/PRINCIPLES.md` §3 Surgical Changes: "Touch only what the plan names. Don't improve adjacent code." (`~/.opal/PRINCIPLES.md:30`)
- [MUST] `.opal/AGENT.md` §금지사항: "**`~/.opal/` 직접 편집 금지** — 항상 프로젝트 소스를 수정한 후 install로 배포한다." (`.opal/AGENT.md:61`)
- [MUST] `.opal/AGENT.md` §금지사항: "**변경이력 누락 금지** — 스킬·에이전트·참조 문서 수정 시 변경이력 표 행 추가 의무." (`.opal/AGENT.md:62`)
- [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 "## 변경이력" 표에 행을 추가한다." (`docs/CONVENTIONS.md:200`)
- [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: "일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함" (`docs/CONVENTIONS.md:201`)
- [MUST] `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `agents/`, `community-skills/`, `scripts/`)에서 수행한다." (`docs/CONVENTIONS.md:206`)
- [MUST] `opal/core/references/opal-harness.md` §1 Guards: "사용자가 명시적으로 '승인', '진행해', '구현해' 등의 실행 허가를 내릴 때까지 코드를 작성하거나 파일을 생성/수정하지 않는다." — 본 PLAN 워커는 PLAN.md만 작성하며 대상 5파일을 수정하지 않았다.

### 1.5 규칙 1소유자 매핑 (Governance 집행 설계)

동일 규칙·수치를 2개 파일에 중복 기재하지 않기 위해, **3개 수치와 1개 절차에 각각 단일 소유 문서**를 지정한다 (→ 1.4 §Governance).

| 규칙 요소 | 유일 소유 문서 | 타 문서 취급 |
|----------|--------------|------------|
| 재개 재시도 상한 = **1회** | `opal-harness.md` §1 자동 루핑 제약 표 | `pm-review-gate.md`·`dispatch-process.md`는 참조만 (수치 미기재) |
| 중단 후 산출물 실측 판정 **3단계 절차** | `harness/pm-review-gate.md` §워커 중단 시 산출물 실측 판정 | `opal-harness.md`·`dispatch-process.md`는 참조만 |
| 산출 파일 상한 = **3개** (관측 기반 잠정치) | `pm/dispatch-process.md` Step 6 | `parallel-execution.md` §7.4·`opal-harness.md` §1은 수치 없이 참조만 |
| 증분 저장 · 입력 축소 **2규율 문언** | `pm/dispatch-process.md` §워커 컨텍스트 주입 템플릿 §핵심 제약 | `op-dev-execute` Step 4는 적용 시점만 기술 + 참조 |

> 검증 가능성: 각 수치 리터럴("1회" / "3개" / 3단계 본문)이 **정확히 1개 파일**에서만 발견되어야 한다 → TS-014.

### 1.6 prose vs tool-gating 판단 (1.4 §Core Stance 대응)

| 규칙 | prose 충분 여부 | 근거 |
|------|---------------|------|
| REQ-1 재시도 상한 1회 | prose 충분 | 기존 자동 루핑 제약 표의 다른 7행 전부가 prose로 운영 중이며 집행 주체가 PM(LLM) 판단이다. 이 행만 도구화하면 표 내부 집행 방식이 이원화된다. |
| REQ-2 실측 판정 3단계 | prose 충분 (단계 1은 이미 도구 기반) | 단계 1이 `git status`/`git diff --stat`라는 도구 관측을 강제하므로 "워커 자기보고 신뢰" 실패 모드가 prose 수준에서 차단된다. 단계 2·3은 PLAN 대조 판단이라 도구화 대상이 아니다. |
| REQ-3 산출 파일 3개 상한 | prose 잠정 → **tool-gating 후속 후보** | 디스패치 직전 대상 파일 수를 세는 것은 기계 판정이 가능하다. 다만 임계값 3이 관측 기반 잠정치(4~9 미검증)라 지금 도구로 잠그면 잘못된 수치를 강제하게 된다. **임계값이 실측으로 확정된 뒤 gating한다** (후속 F-1 재개 카운터 tool-gating과 동일 계열). |
| REQ-4 증분 저장·입력 축소 | prose 충분 (주입 경로가 이미 강제) | 워커 컨텍스트 주입 템플릿에 고정 항목으로 박히면 모든 디스패치 프롬프트에 자동 포함된다 — 템플릿 자체가 집행 장치 역할을 한다. 워커의 실제 저장 시점은 외부에서 관측 불가하므로 도구 게이팅 대상이 아니다. |

> **후속 tool-gating 후보 1건**: REQ-3 산출 파일 수 상한 — 임계값 확정 후 state-tool 또는 디스패치 전 훅에서 파일 수 카운트 게이트. TASK §확정된 설계 방향 F-1(재개 횟수 카운터)과 묶어 단일 후속 태스크로 제안한다.

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-001 / `opal-harness.md` §1 표 행 추가 | 표를 "복제 금지·참조" 관계로 인용하는 하위 문서(`verification-loop-guide`·action-agent·`harness/scenario-gate.md`)가 신규 행의 존재를 모른 채 기존 7행 전제로 동작 | P2 | L1(문서 grep) | S-1 후보 (TS-001·TS-002) |
| H-2 | F-001 / `pm-review-gate.md` 신규 절 삽입 | `opal-pm.md:66`의 요약 포인터가 "검토 11항목"으로 문서 구성을 열거 — 신규 절 미반영 (선행 결함: 실제는 14항목) | P2 | L1(grep) | S-2 후보 (TS-015) |
| H-3 | F-001 / `pm-review-gate.md` 파일 변경 | `opal/tools/code-scan/tests/test-regression.js:930`이 이 파일 본문을 읽어 `validate --changed`·커버리지 문구 존치를 검사 — 절 삽입으로 기존 문구가 밀리거나 유실되면 테스트 실패 | P1 | L3a(`node --test`) | S-3 후보 (TS-012) |
| H-4 | F-002+F-003 / `dispatch-process.md` 2개소 동시 수정 | 동일 파일을 두 요구사항이 편집 — 병렬 편집 시 후행 Write가 선행 편집을 덮어써 한쪽만 반영 | P1 | L1(2앵커 동시 grep) | S-4 후보 (TS-005·TS-007) |
| H-5 | F-001~F-003 전체 / 수치 중복 | Governance 위반 — 동일 수치가 2파일에 기재되면 향후 한쪽만 갱신되어 규칙 불일치 발생 | P1 | L1(리터럴 유일성 grep) | S-5 후보 (TS-014) |
| H-6 | F-004 / install 재배포 | `install-mac.sh:211,219-220`이 배포본에서 `## 변경이력` 이후를 strip — 소스 대 배포본 단순 diff는 항상 불일치로 나옴(오탐) | P2 | L2(strip 기준 정규화 후 대조) | S-6 후보 (TS-010) |
| H-7 | F-004 / REQ-6 memory 졸업 | `promote` 서브명령은 `memory/<file>.md` 실파일 존재를 전제(`memory_tool.py:1164-1168`) — 대상 2건의 파일이 `.opal/memory/`에 부재하여 `memory_file_not_found`로 거부됨 | P1 | L2(도구 실주행) | S-7 후보 (TS-011) |
| H-8 | F-002 / `parallel-execution.md` 변경이력 | 이 파일에는 `## 변경이력` 절 자체가 없음(89줄, §7.6에서 종료) — REQ-5 AC("각 파일 1행 이상")를 충족하려면 절 신설이 선행되어야 함 | P2 | L1(존재 grep) | S-8 후보 (TS-009) |
| H-9 | F-003 / 템플릿 고정 항목 | `## 핵심 제약` 블록은 원래 "문서에서 추출한 [MUST]" 슬롯 — 문서 무관 고정 규율을 섞으면 워커가 근거 문서를 역추적하려다 혼선 | P2 | L1(문언 검토 — 고정 항목 마커 존재 확인) | S-9 후보 (TS-007) |
| H-10 | F-003 / 두 문서 문언 상충 | `dispatch-process.md`(SSOT)와 `op-dev-execute` Step 4의 규율 문언이 다르게 표현되면 워커가 어느 쪽을 따를지 모호 | P1 | L1(참조 관계 grep + 복제 부재 확인) | S-10 후보 (TS-008) |

---

## 2. 기능별 분석

> 영역 축: 프레임워크 문서·규칙 트랙이므로 **가이드 / 스킬 / 문서 / 배치** 축을 사용한다 (op-dev-plan SKILL.md §영역 태그 규칙 — "프레임워크 문서·스킬 태스크에서는 스킬 / 가이드 / 오케스트레이터 / 에이전트 / 문서 / 환경 / 배치 축을 사용한다").

### F-001: 워커 중단 복구 프로토콜

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | `opal/core/references/opal-harness.md` | 오케스트레이터 공통 하네스 — §1 Guards 자동 루핑 제약 표 소유 | 수정 |
| 가이드 | `opal/core/references/harness/pm-review-gate.md` | PM Gate 검토 절차·판정 SSOT | 수정 |
| 문서 | `opal/core/references/opal-pm.md` | `pm-review-gate.md` 요약 포인터 보유(:66) — 본 태스크 **비변경**, 리스크 관측만 | 변경 없음 |
| 배치 | `opal/tools/code-scan/tests/test-regression.js` | `pm-review-gate.md` 본문 존치 검사(:930) — 회귀 검증에 사용 | 변경 없음 |

#### 2.1.2 현재 구현

**`opal-harness.md` §1 자동 루핑 제약 표** (`opal/core/references/opal-harness.md:44-64`) — 3컬럼(`실패 유형` / `최대 재시도` / `초과 시 동작`), 현행 **7행**:

| 현행 행 | 재시도 | 초과 시 |
|--------|-------|--------|
| lint/format | 제한 없음 | - |
| build/type | 2회 | 사용자 에스컬레이션 |
| unit/integration test (L3a) | 3회 | 사용자 에스컬레이션 |
| E2E test (L3b) | 1회 | 사용자 에스컬레이션 |
| QA 설계/아키텍처 | 0회 | 즉시 사용자 에스컬레이션 |
| 워커 폴백 반복 | 1회 | 즉시 에스컬레이션 |
| PLAN 재진입 | 2회 | scope별 에스컬레이션 |
| 시나리오 목표-커버 게이트 | 3회 | 캡틴 에스컬레이션 |

- 표 아래에 **행 보충 note 2건**이 이미 존재한다(`:59` 재설계 루프 정의 / `:61` O1↔O3 보완 관계) — 신규 행의 보충 설명도 같은 위치·같은 인용문 스타일로 붙이는 것이 기존 패턴이다.
- 표의 대상은 전부 **검증·품질 실패**이며, **워커 프로세스 자체의 비정상 종료**(스톨·연결 종료) 행은 없다 → TASK §배경 분석 §3 판정("부재") 실측 확인.
- 가장 가까운 기존 행은 "워커 폴백 반복"이지만, 이는 **워커가 반환에 성공한 뒤 폴백 유형을 보고한 경우**를 다룬다. 반환 자체가 없는 중단은 커버되지 않는다.

**`pm-review-gate.md` 현행 구조** (162줄):

```
> 로드 시점: PM Gate 수행 시 / 워커 완료 수신 직후   (:4)
> 역할: 워커 완료 선언 / 검토 11항목 / ...            (:5)  ← 실제 14항목, 선행 불일치
### 워커 완료 선언            (:11-15)   Observability 선언 1줄
### 검토 절차                 (:17)
  #### 문서 QA 검증           (:19-32)
  #### self-check 질문        (:34-41)
  #### 표준 검토 항목 1~14    (:43-106)
### 자가 진단                 (:108-117)
### PM Gate 통과 후 단일 mark (:119-128)
### 판정                      (:130-135)
### 하네스와의 관계           (:137-139)
### 문서 등록 확인            (:141-145)
## 변경이력                   (:149-162, 최신 v1.8)
```

- `### 워커 완료 선언`은 **정상 반환을 전제**한다 — "워커 결과 수신 직후" Observability 선언만 규정하며, 결과가 오지 않은 경우의 분기가 없다 (`:11-15`).
- `표준 검토 항목`은 산출물이 확정된 뒤의 **품질 검사 14종**이다. 무엇이 산출됐는지를 확정하는 절차는 어디에도 없다.

#### 2.1.3 영향 범위

- **상위 의존**: `opal-harness-interactive.md:23`·`opal-pm.md:66`·`agents.md:21`·`qa-standards.md:7`·`state-template.md:89`·`opal-convention-checker/AGENT.md:47`가 `pm-review-gate.md`를 참조한다. 참조는 모두 **문서 단위 또는 §단위 앵커**(§문서 QA 검증 / §검토 절차 §13)이며, 절 삽입으로 깨지는 줄번호 참조는 없다.
- **유일한 열거형 포인터**: `opal-pm.md:66` "상세(워커 완료 선언, 검토 11항목, Pass/Fail 판정, 문서 등록 확인, 하네스와의 관계)" — 신규 절이 열거에 빠진다(H-2). 단 "11항목"은 이미 현실(14항목)과 불일치하는 **선행 결함**이다.
- **하위 의존**: 없음 — 두 문서 모두 참조 대상일 뿐 다른 문서를 실행 종속시키지 않는다.
- **테스트**: `opal/tools/code-scan/tests/test-regression.js:930-934`가 `pm-review-gate.md` 전문을 읽어 `validate --changed` 문자열과 `커버리지|coverage` 존치를 정규식으로 검사한다 — **줄번호 비의존**이므로 절 삽입은 안전하나, 회귀 실행으로 확인한다(H-3).
- `opal-harness.md` §1 표를 참조하는 문서: `:59` note가 "action-agent·verification-loop-guide는 이 수치를 복제하지 않고 본 표를 참조한다"고 명시 — 신규 행도 같은 규율 아래 놓인다.

---

### F-002: 디스패치 산출량 상한

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | `opal/core/references/pm/dispatch-process.md` | PM 디스패치 전 프로세스 Step 0~7 — Step 6 실행 라우팅(배치 구성) 소유 | 수정 |
| 가이드 | `opal/core/references/harness/parallel-execution.md` | 병렬 처리 원칙 §7 — §7.4 리소스 관리 소유 | 수정 (참조 1줄 + 변경이력 절 신설) |
| 문서 | `opal/core/references/opal-harness.md` | §2 Lazy 로드 조건 테이블(:102) — 앵커 타당성 판정 근거, **비변경** | 변경 없음 |

#### 2.2.2 현재 구현

**앵커 타당성 재검증 (TASK §배경 분석 §4 검증 — 실측 확인 완료)**

| 확인 항목 | 실측 | 결론 |
|----------|------|------|
| `parallel-execution.md` Lazy 로드 조건 | `opal-harness.md:102` — "\| 병렬 처리 \| `harness/parallel-execution.md` \| **병렬 디스패치 시** \| §7 \|" | 단일 디스패치에서는 **로드되지 않음** |
| 동일 조건 재확인 | `opal-harness.md:198,202` — "**[필수 로드]** 병렬 디스패치 시 로드한다. / 적용 시점: 병렬 디스패치 시" | 2개소 일치 — 조건부 로드 확정 |
| 파일 자체 선언 | `parallel-execution.md:4` — "> 로드 시점: 병렬 디스패치 시" | 3개소 일치 |
| 080 실패 디스패치 성격 | TASK §배경 분석 §1 — "Step 2는 10파일 × 67 TS **단일 디스패치**" | 규칙을 이 파일에 두면 실패 케이스에 로드 안 됨 |
| `dispatch-process.md` 로드 조건 | `opal-pm.md:49,57` — PM이 직접 작업하는 경우까지 포함해 Steps 1~3 실행 + "상세 절차(Step 0~7 전체)" 참조. 조건부 로드 조건 없음 | **전 디스패치 공통 진입점** |

> **판정: TASK가 제안한 앵커 교정이 옳다.** `dispatch-process.md` Step 6가 SSOT, `parallel-execution.md` §7.4는 참조 1줄. 더 나은 대안 앵커는 발견되지 않았다 — `opal-harness.md` §7은 stub(6줄)이라 규칙 본문을 담는 자리가 아니고, `observability.md`는 TASK §4 지적대로 행위 주체 선언 문서다.

**`dispatch-process.md` Step 6 현행** (`:145-152`) — 4항목 번호 목록:

```
## Step 6. 실행 라우팅
PLAN.md §4 실행 체크리스트의 agent 필드를 참조하여 에이전트별 배치(Batch)를 구성한다.
1. PLAN.md §4 실행 체크리스트에서 각 Step의 agent 필드를 확인
2. 동일 agent의 독립 Step → 같은 Batch (병렬 가능)
3. 의존 관계가 있는 Step → 순차 배치
4. agent 필드가 없는 Step → opal-task-agent (기존 방식)
```

- 배치 구성 기준이 **agent 동일성과 의존 관계**뿐이다. 배치의 **크기**(산출 파일 수) 기준이 없다 → 10파일 단일 배치가 규칙상 정상으로 통과한다.

**`parallel-execution.md` §7.4 현행** (`:58-64`):

- 고부하 기준 = **입력** 단일 파일 50KB 초과 또는 합산 200KB 초과
- 제한 원칙 = Max 2개 또는 순차
- 판단 주체 = PM 디스패치 전 사전 체크
- → 전부 **입력 리소스·동시 실행 개수** 축이며 **산출량** 축이 없다 (TASK §배경 분석 §3 판정 재확인)
- §7.5 폴백(`:66-74`)은 "리소스 부족으로 인한 오류" 프레임 — 스톨·연결 종료는 리소스 부족과 원인이 다르며, §7.5는 감지 후 **1/2 재분할**을 지시할 뿐 절대 상한이 없다.
- **파일 말미에 `## 변경이력` 절이 존재하지 않는다** (89줄, §7.6 종료가 마지막) → H-8.

#### 2.2.3 영향 범위

- **`dispatch-process.md` 상위 의존**: `opal-pm.md:49,57,115`가 Step 번호 단위로 참조("Steps 1~3", "Step 0~7 전체", "§code-scan 사전 범위 파악"). Step 6 **내부 항목 추가**는 Step 번호를 바꾸지 않으므로 이 참조들은 무영향.
- **brain 페이지 3건**이 `dispatch-process.md`를 버전·절 단위로 인용(`.opal/brain/pages/concept/*.md`) — 모두 과거 태스크(010/015/016) 기록이며 Step 6 무관.
- **`parallel-execution.md` 상위 의존**: `opal-harness.md:102,199`, `opal-harness-interactive.md:81`. §7.4 내부 bullet 추가는 무영향.
- **동명이인 주의**: `opal-pilot-project-dev/references/parallel-execution-guide.md`는 **별개 파일**이다(oppd 전용). 본 태스크 대상 아님 — grep 검증 시 경로 전체를 매칭해 오탐을 막는다.
- **테스트**: `dispatch-process.md`·`parallel-execution.md`를 읽는 자동 테스트는 없음(`RULE_DOCS`에 미포함, `test-regression.js:291-297`).

---

### F-003: 증분 저장 + 입력 축소 규율

#### 2.3.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | `opal/core/references/pm/dispatch-process.md` | §워커 컨텍스트 주입 템플릿 — 전 워커 공통 프롬프트 골격 소유 | 수정 |
| 스킬 | `opal/skills/op-dev-execute/SKILL.md` | EXECUTE 단계 스킬 — Step 4 체크리스트 갱신 규율 | 수정 |

#### 2.3.2 현재 구현

**`dispatch-process.md` §워커 컨텍스트 주입 템플릿** (`:81-103`) — 코드 펜스 안에 4개 하위 블록(`## 참조 문서` / `## 핵심 제약` / `## 종속 문서` / `## 문서/코드 불일치 규칙`). `## 핵심 제약` 현행 3줄(`:92-94`):

```
- [MUST] <문서명> §N: <규칙 원문>  ← 원문 인용 필수 항목
- [MUST] CONVENTIONS.md §N: <컨벤션 강제 규칙 원문>  ← 컨벤션 [MUST]/금지/네이밍 (해당 시)
- {선호사항 또는 가이드라인}: {설명}  ← 요약 허용 항목
```

- 3줄 모두 **플레이스홀더**이며 `←` 주석으로 항목 성격을 라벨링하는 서식이 이미 확립돼 있다 → 고정 항목도 같은 서식으로 얹으면 구조 이질감이 없다(H-9 완화).
- 이 템플릿은 **프로젝트 전체에서 유일본**이다 — `grep -rn "워커 컨텍스트 주입 템플릿" opal/` 결과 `dispatch-process.md` 1건. 사본 동기화 부담 없음.
- 전 워커 공통 주입 지점이라 PLAN·ANALYSIS·EXECUTE 워커 모두에 적용된다 → 080에서 산출물 0건을 낸 **PLAN 워커**도 커버(TASK §배경 분석 §4 지적 해소).

**`op-dev-execute/SKILL.md` Step 4 현행** (`:92-95`) — 4줄:

```
### Step 4. 체크리스트 갱신
각 Step 완료 시 체크박스를 실시간 갱신한다:
PLAN.md 실행 체크리스트의 `- [ ] 완료` → `- [x] 완료`
```

- "각 Step 완료 시 실시간"은 **체크박스 갱신 시점**만 규정한다. **산출물 자체의 저장 시점**(파일 완결 후 이동 vs 말미 일괄) 규율이 없다 → TASK §배경 분석 §3 판정 재확인.
- 인접 Step 3-S(`:57-77`)·3-H(`:78-90`)는 "구현 완료 즉시" 패턴을 이미 쓰고 있어, Step 4에 완결 시점 규율을 붙이는 것이 문서 내 흐름과 일치한다.

**선행 중복 부재 확인**: `grep -rn "통독 금지\|일괄 저장\|증분 저장" opal/` → **0건**. 두 규율은 프레임워크 어디에도 없으며, 신설 문언이 기존 문언과 충돌할 여지가 없다.

#### 2.3.3 영향 범위

- **주입 템플릿 변경은 모든 후속 디스패치 프롬프트에 즉시 반영**된다 — 파급이 가장 넓은 변경이지만, 추가되는 것은 **제약 2줄**이므로 기존 주입 항목을 제거·변경하지 않는다(비파괴).
- `op-dev-execute` Step 4 → Step 5(`:97`)는 "모든 실행 Step 완료 후" QA 자체 검증이며 Step 4 확장과 순서 충돌 없음.
- **가드레일 표**(`:104-113`, 6행 금지 행동)와의 관계: 증분 저장·입력 축소는 **금지가 아니라 수행 규율**이므로 가드레일 표가 아닌 Step 4 본문이 적합하다.
- 테스트: `op-dev-execute/SKILL.md`를 읽는 자동 테스트 없음.

---

### F-004: 변경이력·배포 반영 + 개선 후보 메모리 졸업

#### 2.4.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | 대상 4개 참조 문서 (F-001·F-002·F-003) | 각 파일 `## 변경이력` 표에 081 행 추가 | 수정 (해당 Step에 내재) |
| 스킬 | `opal/skills/op-dev-execute/SKILL.md` | 변경이력 v2.4 행 추가 | 수정 (해당 Step에 내재) |
| 배치 | `scripts/install-mac.sh` | 실행만 — 스크립트 자체는 **비변경** | 실행 |
| 문서 | `.opal/MEMORY.json` | 개선 후보 2건 상태 전이 — `memory-tool`로만 조작 | 수정 (도구 경유) |

#### 2.4.2 현재 구현

**변경이력 절 실측 (5파일)**

| 파일 | `## 변경이력` 존재 | 최신 버전 | 다음 버전 |
|------|-----------------|---------|----------|
| `opal-harness.md` | 있음 (`:274`) | v6.7 (2026-07-28) | **v6.8** |
| `pm-review-gate.md` | 있음 (`:149`) | v1.8 (2026-08-02 14:50) | **v1.9** |
| `dispatch-process.md` | 있음 (`:165`) | v1.5 (2026-06-17) | **v1.6** |
| `op-dev-execute/SKILL.md` | 있음 (`:196`) | v2.3 (2026-06-24) | **v2.4** |
| `parallel-execution.md` | **없음** (89줄, §7.6 종료) | — | **절 신설 + v1.0/v1.1 2행** |

- `dispatch-process.md:169`에 `| v1.0 | - | 초기 작성 — opal-pm.md §3 파생 |` 선례가 있다 — 과거 이력을 모르는 분리 파생 문서는 날짜 `-`로 v1.0 행을 두는 것이 이 저장소의 확립된 패턴이다. `parallel-execution.md`도 동일 패턴(`opal-harness.md` §7 분리)으로 신설한다.

**배포 경로·strip 실측 (`scripts/install-mac.sh`)**

| 소스 | 배포처 | 근거 |
|------|--------|------|
| `opal/core/references/**` | `~/.opal/references/**` | `install-mac.sh:1364` (`ref_src`) |
| `opal/skills/{name}/` | `~/.opal/skills/{name}/` | `install-mac.sh:1041-1052` |

- **변경이력 strip**: `install-mac.sh:211` `awk 'BEGIN{keep=1} /^## 변경이력$/{keep=0} keep==1{print}'` (파일 단위), `:219-220` 동일 로직 디렉토리 일괄. `:1374` 주석 "배포된 모든 .md 파일에서 변경이력 섹션 제거".
- → **배포본 대조는 `## 변경이력` 이전까지만 유효하다**(H-6). 소스에도 동일 awk를 적용한 뒤 `diff`해야 오탐이 없다.

**메모리 현황 실측 (`.opal/MEMORY.json`)**

- 스키마 최상위: `version` / `last_task_number` / `memories` / `history`. `memories` 총 6행, 상태 분포 = `active` + `candidate`.
- `candidate` 2행 (REQ-6 대상):

| 제목 | date | type | file 필드 |
|------|------|------|----------|
| 워커 보고는 실측 대조 없이 신뢰 불가 | 2026-07-29 | improvement | `memory/워커_보고는_실측_대조_없이_신뢰_불가.md` |
| 078 워커 실패 완화책이 079에서 인프라 실패 0건으로 재현됨 | 2026-07-30 | improvement | `memory/078_워커_실패_완화책이_079에서_인프라_실패_0건으로_재현됨.md` |

- **[치명] `.opal/memory/` 실제 내용 = `console-brain-subscription-auth.md`, `follow-up-brain-query-lite.md` 2개뿐** — 위 2건의 `file` 대상 파일이 **존재하지 않는다**.
- `memory_tool.py:1164-1168`: promote는 `mem_file`이 없거나 `exists()`가 거짓이면 `memory_file_not_found`로 즉시 err → **`promote` 경로 사용 불가**(H-7).
- 대안 경로 `update`: `--kind memory`에서 `--status`/`--summary`/`--new-title` 허용(README `:106-110`), 상태 enum에 `promoted` 포함(README `:94`). `dead`/`superseded` 전이는 행 보존(README `:116`).

#### 2.4.3 영향 범위

- **install 재실행 부작용 범위**: `~/.opal/` 전체 재배포 — 본 태스크 무관 파일도 갱신된다. 단 `~/.opal/community-skills/`는 install 불가침(`install-mac.sh:1015`)이라 사용자 데이터 손실 없음.
- **동시 태스크 충돌**: 078·079 시 겪은 `tools.md` 공유 이슈와 달리, 본 태스크 대상 5파일에 대한 동시 편집 태스크는 확인되지 않았다. 단 `pm-review-gate.md`는 **오늘(2026-08-02 14:50) 080이 v1.8을 기록**했으므로 v1.9로 이어붙인다.
- **MEMORY.json 이력 FIFO**: `history`는 FIFO=5(`prune`). 081 히스토리 행 추가 시 최고령 1행이 밀려날 수 있다 — 정상 동작이며 손실 판정 대상 아님.

---

## 3. 기능별 설계

> **공통 규약**: 아래 삽입 문구는 **그대로 복사해 넣는 확정 문언**이다. 워커는 문언을 재작성하지 않는다. `HH:mm`만 실행 시각(`TZ=Asia/Seoul date '+%Y-%m-%d %H:%M'`)으로 치환한다.
> 모든 편집은 **Edit(부분 치환) 전용**이다. 대상 파일에 `Write`(전체 덮어쓰기)를 사용하지 않는다 — 078·079에서 동시 태스크 상호 보존에 유효했던 규율(→ D-6 §8, D-7 §8).

### F-001: 워커 중단 복구 프로토콜

#### 3.1.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| — | 없음 | — | — | — |

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/opal-harness.md` | 가이드 | §1 자동 루핑 제약 표에 행 1개 추가 + 행 보충 note 1개 + 변경이력 v6.8 | `opal/core/references/opal-harness.md:44-64` (→ D-1 §1) |
| 2 | `opal/core/references/harness/pm-review-gate.md` | 가이드 | `### 워커 중단 시 산출물 실측 판정` 절 신설 + 역할 라인 갱신 + 변경이력 v1.9 | `opal/core/references/harness/pm-review-gate.md:5,11-17` (→ D-2) |

#### 3.1.2 설계 — 확정 삽입 문언

##### (A) `opal-harness.md` §1 표 행 추가

- **삽입 위치**: `:57`("시나리오 목표-커버 게이트" 행) **직후**, `:58` 빈 줄 앞. 표 마지막 행으로 추가한다.
- **[MUST] 이 셀에 산출 파일 수치(3)를 기재하지 않는다** — 해당 수치의 유일 소유자는 `dispatch-process.md` Step 6다 (→ §1.5 규칙 1소유자 매핑, D-0 §제약 조건 "R-1의 수치와 절차를 두 파일에 중복 기재하지 않는다").

```markdown
| 워커 프로세스 비정상 종료 (스톨 · 응답 중 연결 종료) | 1회 (동일 컨텍스트 재개) | 새 컨텍스트로 분할 재배치 (분할 기준: `pm/dispatch-process.md` Step 6) |
```

- **행 보충 note 삽입 위치**: `:61`(O1↔O3 보완 관계 note) 직후, `:63`("회귀 방지" bullet) 앞. 기존 note 2건과 동일한 `> **제목**: 본문` 서식을 따른다 (→ `opal-harness.md:59,61`).

```markdown
> **워커 비정상 종료 행 보충**: 동일 컨텍스트 재개가 같은 지점에서 재실패하면 재시도를 즉시 중단한다(관측: 재개 3회가 전부 동일 지점에서 재실패). 중단 후 실제 산출물을 확정하고 잔여만 재배치하는 절차는 `harness/pm-review-gate.md` §워커 중단 시 산출물 실측 판정을 따른다 — 본 표는 재시도 수치만 소유하고 절차·분할 기준을 재서술하지 않는다.
```

- **변경이력 행** (`## 변경이력` 표 말미에 추가):

```markdown
| v6.8 | 2026-08-02 HH:mm | §1 자동 루핑 제약 표에 "워커 프로세스 비정상 종료(스톨·응답 중 연결 종료)" 행 추가 — 재시도 1회(동일 컨텍스트 재개), 초과 시 새 컨텍스트 분할 재배치. 판정 절차는 `harness/pm-review-gate.md`, 분할 기준은 `pm/dispatch-process.md` Step 6가 소유하고 본 표는 수치만 소유(중복 기재 금지) (081) |
```

##### (B) `pm-review-gate.md` 신규 절 신설

- **삽입 위치**: `### 워커 완료 선언` 블록 끝(`:15` 인용문) **직후**, `### 검토 절차`(`:17`) **앞**.
- **배치 근거 (판단 사항 2 결정)**: 3개 후보를 기존 구조와 대조해 판정했다.

| 후보 위치 | 판정 | 근거 |
|----------|------|------|
| 표준 검토 항목 15번 신설 | **부적합** | 1~14번은 산출물이 이미 확정된 뒤의 **품질 검사 항목**이다(`:43-106`). 실측 판정은 "무엇이 산출됐는지"를 정하는 **선행 단계**라 성격이 다르고, 매 게이트마다 도는 체크리스트에 예외 상황 절차를 섞으면 상시 비용이 된다. |
| `### 판정` 절 확장 | **부적합** | `### 판정`(`:130-135`)은 Pass/Fail **결과 처리** 규정이다. 검토 이전 단계의 입력 확정 절차를 여기에 두면 문서 내 시간 순서가 역전된다. |
| **`### 워커 완료 선언` 직후 신규 `###` 절** | **채택** | 정상 반환 경로(`### 워커 완료 선언`)와 비정상 중단 경로를 **형제 절로 병치**해, 워커 결과 수신 직후 분기가 문서 구조로 드러난다. 로드 시점 선언(`:4` "워커 완료 수신 직후")과도 정합한다. 뒤따르는 `### 검토 절차`가 자연스럽게 공통 합류점이 된다. |

```markdown
### 워커 중단 시 산출물 실측 판정

워커가 정상 반환 없이 중단된 경우(600초대 스톨 · 응답 중 연결 종료 등)에도 산출물은 워킹트리에 남아 있을 수 있다. **[MUST] 워커 자기보고의 부재를 산출물의 부재로 간주하지 않는다.** 아래 3단계를 순서대로 수행하여 입력을 확정한 뒤 §검토 절차로 진입한다.

1. **산출물 확정** — `git status --short`와 `git diff --stat`으로 실제 생성·수정된 파일을 확정한다. 판정 근거는 워커 반환 텍스트가 아니라 워킹트리다.
2. **완료/잔여 판정** — 확정된 파일 집합을 `PLAN.md` §4.2 실행 체크리스트와 대조하여 Step 단위로 완료분과 잔여분을 가른다. 부분 산출된 파일은 내용을 열어 해당 Step의 **완료 기준** 충족 여부로 판정하고, 판정 불가면 잔여로 분류한다.
3. **잔여만 재배치** — 잔여 Step만 새 디스패치로 재배치한다. **[MUST] 완료분 파일을 재작업 대상에 포함하거나 덮어쓰지 않는다** — 재디스패치 프롬프트의 대상 파일 목록에서 완료분을 명시적으로 제외하고, 워커에게 `Write`(전체 덮어쓰기) 대신 `Edit`(부분 치환) 사용을 지시한다.

> 동일 컨텍스트 재개 횟수 상한은 `opal-harness.md` §1 자동 루핑 제약 표(워커 프로세스 비정상 종료 행)를, 재배치 시 산출 파일 수 상한은 `pm/dispatch-process.md` Step 6 실행 라우팅을 따른다. 본 절은 판정 절차만 소유하며 두 수치를 재서술하지 않는다.
```

- **역할 라인 갱신** (`:5`) — 신규 절이 문서 역할 요약에서 누락되지 않게 한다. 기존 "검토 11항목"(실제 14항목, 선행 불일치)은 항목 수를 고정하지 않는 표현으로 바꾼다:

```markdown
> 역할: 워커 완료 선언 / 워커 중단 시 산출물 실측 판정 / 검토 절차(문서 QA · 표준 검토 항목) / Pass·Fail 판정 / 문서 등록 확인 / 하네스와의 관계
```

- **변경이력 행**:

```markdown
| v1.9 | 2026-08-02 HH:mm | §워커 중단 시 산출물 실측 판정 절 신설 — ①`git status`로 산출물 확정 → ②PLAN §4.2 체크리스트 대조로 완료/잔여 판정 → ③잔여만 재배치([MUST] 완료분 덮어쓰기 금지) 3단계. 재시도 상한(`opal-harness.md` §1)·산출량 상한(`pm/dispatch-process.md` Step 6)은 참조만. 역할 라인에 신규 절 반영 및 고정 항목수 표기 제거 (081) |
```

#### 3.1.3 환경 변경

해당 없음.

#### 3.1.4 배치/마이그레이션

해당 없음 (배포는 F-004 Step 6에서 일괄).

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | REQ-1 AC | 산출물 검사 | `opal-harness.md` §1 표에 "워커 프로세스 비정상 종료" 행이 존재하고 3컬럼(실패 유형 / `1회 (동일 컨텍스트 재개)` / 새 컨텍스트로 분할 재배치)이 모두 채워져 있다 |
| TS-002 | REQ-1 AC + Governance | 정합성 검사 | 신규 표 셀·보충 note에 산출 파일 수치(`3개`)가 기재되어 있지 않고, `pm/dispatch-process.md` Step 6 참조 문자열이 존재한다 |
| TS-003 | REQ-2 AC | 산출물 검사 | `pm-review-gate.md`에 `### 워커 중단 시 산출물 실측 판정` 절이 있고, 번호 1·2·3 단계가 순서대로 존재하며, "완료분 파일을 재작업 대상에 포함하거나 덮어쓰지 않는다"가 `[MUST]` 접두 표현으로 기재돼 있다 |
| TS-004 | REQ-2 AC + Governance | 정합성 검사 | 신규 절 본문에 재시도 상한 수치(`1회`)와 산출 파일 상한 수치(`3개`)가 재서술되지 않고, 두 SSOT 문서 경로 참조만 존재한다 |
| TS-015 | H-2 관측 | 회귀 검사 | `opal-pm.md:66` 열거형 포인터의 stale 여부를 확인해 결과를 기록한다 (081 비변경 — 후속 판단 입력) |

---

### F-002: 디스패치 산출량 상한

#### 3.2.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| — | 없음 (`parallel-execution.md`의 `## 변경이력` 절은 기존 파일 내 절 신설) | — | — | — |

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/pm/dispatch-process.md` | 가이드 | Step 6에 항목 5(산출량 상한) 추가 + 변경이력 v1.6 | `opal/core/references/pm/dispatch-process.md:145-152` (→ D-4) |
| 2 | `opal/core/references/harness/parallel-execution.md` | 가이드 | §7.4에 참조 bullet 1줄 추가 + `## 변경이력` 절 신설(2행) | `opal/core/references/harness/parallel-execution.md:58-64` (→ D-3 §7.4) |

#### 3.2.2 설계 — 확정 삽입 문언

##### (A) `dispatch-process.md` Step 6 — 항목 5 신설

- **삽입 위치**: `:152`("4. agent 필드가 없는 Step → opal-task-agent (기존 방식)") **직후**, `## Step 7. 컨텍스트 슬라이싱`(`:154`) 앞.

```markdown
5. **산출량 상한** — 단일 디스패치가 생성·수정하는 **산출 파일이 3개를 초과하면** 파일 집합을 비중첩(non-overlapping)으로 분할하여 별도 디스패치로 배치한다. 반대로 **동일 파일을 2개 이상 Step이 변경하면 분할하지 않고 같은 디스패치에 묶어 순차 편집한다**(동시 편집 시 후행 저장이 선행 편집을 덮어쓰는 충돌 방지).
   - 임계값 3은 **관측 기반 잠정치**다 — 산출 2~3파일 배치는 완주하고 10파일 단일 디스패치는 중단된 관측에 근거하며, **4~9 구간은 미검증**이다. 확정치로 취급하지 말고, 새 관측이 쌓이면 이 수치를 갱신한다.
   - 산출 파일 수는 PLAN.md §4.2 각 Step의 `**파일**` 항목을 합집합으로 세되, 같은 경로는 1개로 계수한다.
   - 워커가 중단된 뒤의 산출물 판정·재배치 절차는 `harness/pm-review-gate.md` §워커 중단 시 산출물 실측 판정을, 동일 컨텍스트 재개 횟수 상한은 `opal-harness.md` §1 자동 루핑 제약 표를 따른다(본 항목은 산출량 기준만 소유한다).
```

- **변경이력 행** (REQ-4 문언과 합쳐 1행으로 기재 — 같은 태스크·같은 파일):

```markdown
| v1.6 | 2026-08-02 HH:mm | Step 6에 항목 5 "산출량 상한" 신설 — 산출 파일 3개 초과 시 비중첩 분할, 동일 파일 다중 Step은 같은 디스패치 순차 편집, 임계값은 관측 기반 잠정치(4~9 미검증). §워커 컨텍스트 주입 템플릿 §핵심 제약에 전 워커 공통 고정 2항목(증분 저장 · 입력 축소) 추가 — 문서 선별 결과와 무관하게 항상 주입 (081) |
```

##### (B) `parallel-execution.md` §7.4 — 참조 bullet 1줄

- **삽입 위치**: `:64`("판단 주체" bullet) **직후**, `### 7.5. 런타임 오류 및 폴백`(`:66`) 앞.
- **[MUST] 이 줄에 임계값 숫자를 쓰지 않는다** — 규칙 본문 복제 금지(REQ-3 AC "규칙 본문 복제 없이 Step 6를 가리키는 참조 1줄만"). 수치를 여기 쓰면 §1.5 유일 소유 원칙이 깨지고 TS-014가 실패한다.

```markdown
- **산출량 상한(참조)**: 위 기준은 **입력** 리소스와 동시 실행 개수만 다룬다. 단일 디스패치의 **산출 파일 수 상한**은 병렬 여부와 무관하게 적용되며, 규칙 본문과 임계값은 `pm/dispatch-process.md` Step 6 실행 라우팅에 있다(여기서 재서술하지 않는다).
```

##### (C) `parallel-execution.md` `## 변경이력` 절 신설

- **삽입 위치**: 파일 최말미(`:89` "**interactive/agentic 공통 적용**: ..." 다음). 구분선 `---`을 앞에 둔다.
- **v1.0 행의 날짜 `-` 표기 근거**: 분리 파생 문서의 확립된 선례 — `dispatch-process.md:169` `| v1.0 | - | 초기 작성 — opal-pm.md §3 파생 |`. 과거 이력을 소급 창작하지 않는다.

```markdown

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | - | 초기 작성 — `opal-harness.md` §7 분리 |
| v1.1 | 2026-08-02 HH:mm | §7.4에 "산출량 상한(참조)" bullet 1줄 추가 — 본 문서는 입력 리소스·동시 개수 기준만 소유하고, 산출 파일 수 상한의 규칙 본문·임계값은 `pm/dispatch-process.md` Step 6가 소유함을 명시(재서술 금지). 변경이력 절 신설 (081) |
```

#### 3.2.3 환경 변경

해당 없음.

#### 3.2.4 배치/마이그레이션

해당 없음.

#### 3.2.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-005 | REQ-3 AC | 산출물 검사 | `dispatch-process.md` Step 6에 항목 5가 있고 "산출 파일이 3개를 초과", "관측 기반 잠정치", "4~9 구간은 미검증"이 모두 존재한다 |
| TS-006 | REQ-3 AC | 정합성 검사 | `parallel-execution.md` §7.4에 추가된 줄이 정확히 1줄이고, 임계값 숫자를 포함하지 않으며, `pm/dispatch-process.md` Step 6 참조를 포함한다 |
| TS-016 | REQ-3 AC (앵커 타당성) | 정합성 검사 | `opal-harness.md:102`의 `parallel-execution.md` 로드 조건이 "병렬 디스패치 시"로 유지되고(변경 없음), 산출량 상한 규칙 본문은 조건부 로드 문서가 아닌 `dispatch-process.md`에 위치한다 |

---

### F-003: 증분 저장 + 입력 축소 규율

#### 3.3.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| — | 없음 | — | — | — |

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/pm/dispatch-process.md` | 가이드 | §워커 컨텍스트 주입 템플릿 `## 핵심 제약`에 고정 2줄 + 블록 하단 note 1개 (변경이력은 F-002와 합산 1행) | `opal/core/references/pm/dispatch-process.md:81-103` (→ D-4) |
| 2 | `opal/skills/op-dev-execute/SKILL.md` | 스킬 | Step 4 제목·본문 확장 + 변경이력 v2.4 | `opal/skills/op-dev-execute/SKILL.md:92-95` (→ D-5) |

#### 3.3.2 설계 — 확정 삽입 문언 (판단 사항 3: 두 문서 문언 통일)

**문언 통일 원칙**: SSOT(`dispatch-process.md`)는 **규율 원문**을 소유하고, 참조 측(`op-dev-execute` Step 4)은 **규율 원문을 한 글자도 복제하지 않고** 자기 문서 고유의 적용 시점(체크박스 갱신 타이밍)만 기술한 뒤 SSOT를 가리킨다. 두 문서에 동시 등장하는 유일한 토큰은 **경로 문자열**(`pm/dispatch-process.md`)뿐이다 → 상충 불가능(H-10 차단).

##### (A) `dispatch-process.md` §워커 컨텍스트 주입 템플릿 `## 핵심 제약`

- **삽입 위치**: 코드 펜스 **내부**, `:93`(CONVENTIONS [MUST] 줄) **직후** / `:94`(선호사항 줄) 앞. 기존 `←` 주석 라벨 서식을 그대로 따른다.

```markdown
- [MUST] 증분 저장: 산출물 1개를 완결 저장한 뒤 다음 산출물로 이동한다. 말미 일괄 저장 금지.  ← 전 워커 공통 고정
- [MUST] 입력 축소: 대상 파일 전체 통독 금지. grep으로 위치를 특정한 뒤 해당 구간만 Read하고 부분 편집(Edit)한다.  ← 전 워커 공통 고정
```

- **블록 하단 note 삽입 위치**: `:103`("`docs/CONVENTIONS.md` 부재 시 본 항목은 자연 스킵") **직후**, `## code-scan 사전 범위 파악`(`:105`) 앞.

```markdown
> **전 워커 공통 고정 2항목**(증분 저장 · 입력 축소)은 Step 2 문서 선별 결과와 무관하게 **모든 워커 디스패치에 항상 포함**한다 — 문서에서 추출한 [MUST]와 달리 근거 문서가 없는 운영 규율이다. 워커가 중단되더라도 직전 완결 산출물까지 보존되게 하는 것이 목적이며, 단계 스킬은 이 문언을 복제하지 않고 본 템플릿을 참조한다. 근거: `tasks/078-260728-opd-메모리-json전환/DONE.md` §8(완화 조합 도출 후 전량 성공), `tasks/079-260730-opds-히스토리-정정명령/DONE.md` §8(선제 적용 → 인프라 실패 0건).
```

##### (B) `op-dev-execute/SKILL.md` Step 4 확장

- **치환 대상**: `:92-95` 전체(제목 1줄 + 본문 2줄).

```markdown
### Step 4. 체크리스트 갱신 및 증분 저장

각 Step 완료 시 체크박스를 실시간 갱신한다:
PLAN.md 실행 체크리스트의 `- [ ] 완료` → `- [x] 완료`

갱신 시점은 **산출물 1개를 완결 저장한 직후**다 — 모든 Step을 끝낸 뒤 일괄 갱신하지 않는다. 산출물 저장 시점·입력 축소 규율 자체의 SSOT는 `opal/core/references/pm/dispatch-process.md` §워커 컨텍스트 주입 템플릿 §핵심 제약(전 워커 공통 고정 2항목)이며, 본 스킬은 이를 복제하지 않는다.
```

- **변경이력 행**:

```markdown
| v2.4 | 2026-08-02 HH:mm | Step 4를 "체크리스트 갱신 및 증분 저장"으로 확장 — 갱신 시점을 산출물 완결 직후로 명시(말미 일괄 갱신 금지)하고, 증분 저장·입력 축소 규율의 SSOT를 `pm/dispatch-process.md` §워커 컨텍스트 주입 템플릿 참조로 연결(문언 복제 금지) (081) |
```

#### 3.3.3 환경 변경

해당 없음.

#### 3.3.4 배치/마이그레이션

해당 없음.

#### 3.3.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-007 | REQ-4 AC | 산출물 검사 | `dispatch-process.md` 주입 템플릿 코드 펜스 **내부**에 "증분 저장"·"입력 축소" 2줄이 존재하고 각 줄에 `← 전 워커 공통 고정` 라벨이 있으며, 펜스 하단에 고정 항목 note가 존재한다 |
| TS-008 | REQ-4 AC | 정합성 검사 | `op-dev-execute/SKILL.md` Step 4에 `pm/dispatch-process.md` 참조가 있고, 규율 원문("말미 일괄 저장 금지" / "전체 통독 금지")이 복제돼 있지 않다 |
| TS-017 | REQ-4 AC | 정합성 검사 | 두 문서를 나란히 읽었을 때 상충 지시가 없다 — SSOT는 저장 규율, 스킬은 체크박스 갱신 시점만 규정 |

---

### F-004: 변경이력·배포 반영 + 개선 후보 메모리 졸업

#### 3.4.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| — | 없음 | — | — | — |

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | 대상 5파일 `## 변경이력` | 가이드/스킬 | 081 행 추가 — 문언은 §3.1.2·§3.2.2·§3.3.2에 확정 기재, 각 파일 편집 Step에서 함께 수행 | [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무 (`docs/CONVENTIONS.md:200-201`) |
| 2 | `.opal/MEMORY.json` | 문서 | candidate 2건 상태 전이 + 081 히스토리 1행 — `memory-tool`로만 조작 | `.opal/MEMORY.json` 실측 / `opal/tools/memory-tool/README.md:94,106-116` |

#### 3.4.2 설계 — 배포 및 메모리 졸업 절차

##### (A) install 재배포 및 배포본 대조

```bash
# 1) 재배포 (프로젝트 루트에서)
./scripts/install-mac.sh

# 2) 배포본 대조 — 변경이력 strip 기준을 소스에도 동일 적용 후 diff (H-6 오탐 차단)
for pair in \
  "opal/core/references/opal-harness.md:$HOME/.opal/references/opal-harness.md" \
  "opal/core/references/harness/pm-review-gate.md:$HOME/.opal/references/harness/pm-review-gate.md" \
  "opal/core/references/harness/parallel-execution.md:$HOME/.opal/references/harness/parallel-execution.md" \
  "opal/core/references/pm/dispatch-process.md:$HOME/.opal/references/pm/dispatch-process.md" \
  "opal/skills/op-dev-execute/SKILL.md:$HOME/.opal/skills/op-dev-execute/SKILL.md" ; do
  src="${pair%%:*}"; dst="${pair#*:}"
  diff <(awk 'BEGIN{keep=1} /^## 변경이력$/{keep=0} keep==1{print}' "$src") "$dst" \
    && echo "OK  $src" || echo "DIFF $src"
done
```

- strip 로직은 `scripts/install-mac.sh:211`의 awk와 **동일 표현식**을 사용한다 (→ D-10 `scripts/install-mac.sh:206-220`).
- [MUST] `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다." — 위 절차는 **읽기 대조만** 수행한다.

##### (B) REQ-6 개선 후보 메모리 졸업 (판단 근거 포함)

- **`promote` 사용 불가 확정** — `promote`는 `memory/<file>.md` 실파일 존재를 전제한다(`opal/tools/memory-tool/memory_tool.py:1164-1168`, `if not mem_file.exists(): err("promote", "memory_file_not_found", ...)`). 대상 2건의 `file` 필드가 가리키는 파일이 `.opal/memory/`에 **부재**(실측: `console-brain-subscription-auth.md`, `follow-up-brain-query-lite.md` 2개뿐)하므로 호출 시 `memory_file_not_found`로 거부된다.
- **채택 경로**: `update --kind memory --status promoted` — 상태 enum에 `promoted`가 포함되고(`opal/tools/memory-tool/README.md:94`), `--status`는 `--kind memory`의 허용 필드다(`README.md:108`). 두 후보는 폐기·대체된 것이 아니라 **SSOT로 졸업**했으므로 `superseded`/`dead`보다 라이프사이클 의미가 정확하다.
- **근거 기록**: `promote`가 남기는 `.memory_provenance.log`를 쓸 수 없으므로, 처리 근거를 `history` 1행으로 남긴다 (REQ-6 AC "처리 근거가 메모리 또는 히스토리에 기록된다" 충족).

```bash
# 후보 1 — REQ-2(pm-review-gate 실측 판정 절)로 흡수
~/.opal/tools/memory-tool/run.sh update --file .opal/MEMORY.json --kind memory \
  --title "워커 보고는 실측 대조 없이 신뢰 불가" \
  --status promoted

# 후보 2 — REQ-3·REQ-4(dispatch-process Step 6 / 주입 템플릿)로 흡수
~/.opal/tools/memory-tool/run.sh update --file .opal/MEMORY.json --kind memory \
  --title "078 워커 실패 완화책이 079에서 인프라 실패 0건으로 재현됨" \
  --status promoted

# 처리 근거 기록 (CLOSE 단계 히스토리 행과 겸함)
~/.opal/tools/memory-tool/run.sh append --file .opal/MEMORY.json --kind history \
  --title "081 워커 중단 복구 프로토콜 SSOT화" \
  --stage "완료" \
  --path "tasks/081-260802-opds-워커중단-복구프로토콜/" \
  --result "재시도1회(harness §1)·실측판정3단계(pm-review-gate)·산출3파일상한(dispatch Step6)·증분저장2규율 등재. candidate 2건 promoted"
```

- `--result` 길이는 `--summary`(≤80자) 제약과 별개다(`README.md:109` — history는 `--result` 사용). 실행 시 도구가 거부하면 요약을 축약한다.

#### 3.4.3 환경 변경

해당 없음 — 신규 패키지·설정 없음. `scripts/install-mac.sh`는 **실행만** 하고 수정하지 않는다.

#### 3.4.4 배치/마이그레이션

`./scripts/install-mac.sh` 1회 실행 (재실행 멱등). `~/.opal/community-skills/`는 install 불가침이므로 사용자 데이터 영향 없음 (`scripts/install-mac.sh:1015`).

#### 3.4.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-009 | REQ-5 AC | 산출물 검사 | 대상 5파일 각각의 `## 변경이력` 표에 `(081)`을 포함한 행이 1행 이상 존재하고, 일시가 `YYYY-MM-DD HH:mm` 형식이다. `parallel-execution.md`는 절 자체가 신설되어 2행(v1.0/v1.1)을 갖는다 |
| TS-010 | REQ-5 AC | 통합 검사 | install 후 5파일 전부 변경이력 strip 기준 diff 0줄 (`OK` 5건) |
| TS-011 | REQ-6 AC | 기능 검사 | `MEMORY.json`에 대상 2건이 `status: "promoted"`로 존재하고 `candidate` 0건이며, `history`에 081 행이 존재한다 |
| TS-012 | 회귀 (H-3) | 회귀 테스트 | `node --test opal/tools/code-scan/tests/test-regression.js` 전량 Pass (특히 `077 S-21: pm-review-gate.md ...`) |
| TS-013 | 완료기준 (참조 무결성) | 정합성 검사 | 신규 도입된 상호 참조 5건의 대상 파일·앵커가 실제로 존재한다 (§4.2 Step 8 목록) |
| TS-014 | Governance (H-5) | 정합성 검사 | 수치 리터럴 유일성 — 재시도 `1회` 규정은 `opal-harness.md` 1파일에만, 산출 `3개` 상한은 `dispatch-process.md` 1파일에만, 실측 판정 3단계 본문은 `pm-review-gate.md` 1파일에만 존재한다 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

> **자기적용 (판단 사항 4)**: 모든 배치의 산출 파일이 **3개 이하**다 (REQ-3이 신설하는 상한을 본 태스크가 먼저 준수). `dispatch-process.md`를 건드리는 REQ-3·REQ-4는 **같은 배치의 단일 디스패치에서 순차 편집**한다 (→ D-0 §제약 조건).

| Phase | 기능 | Step | 산출 파일 수 | 실행 | 비고 |
|-------|------|------|------------|------|------|
| 1 | F-001 | 1, 2 | 2 (각 디스패치 1) | **병렬** | 서로 다른 파일, 상호 참조는 텍스트 수준이라 선후 무관 |
| 2 | F-002 + F-003 | 3 | 1 | 순차 | `dispatch-process.md` 단일 파일 2개소 순차 편집 — 분할 금지 |
| 3 | F-002 + F-003 | 4, 5 | 2 (각 디스패치 1) | **병렬** | Step 3 완료 후 — 참조 대상(Step 6·주입 템플릿)이 먼저 존재해야 함 |
| 4 | F-004 | 6, 7, 8 | 0~1 | 순차 | PM 직접 — 배포·메모리·검증 |

### 4.2 실행 체크리스트

> 총 8개 Step | Phase 4개 | 실행 모드: **복잡** (변경 파일 5개 ≥ 4, Step 8개 ≥ 6)
> `agent` 필드: PM이 전문 에이전트 매핑 테이블을 주입하지 않았으므로 op-dev-plan SKILL.md §agent 필드 배정 규칙의 **기본 표**로 배정했다 (PM 오버라이드 가능).

#### Step 1: `opal-harness.md` §1 자동 루핑 제약 표에 워커 비정상 종료 행 추가
- [x] 완료
- **소속 기능**: F-001 (REQ-1, REQ-5)
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/core/references/opal-harness.md` (1개)
- **작업 내용**: §3.1.2 (A)의 확정 문언 3건을 Edit으로 삽입 — ①표 행 1개(`:57` 직후) ②행 보충 note(`:61` 직후) ③변경이력 v6.8 행(`## 변경이력` 표 말미). `HH:mm`은 `TZ=Asia/Seoul date '+%H:%M'` 결과로 치환.
- **완료 기준**: 표에 신규 행 1개가 3컬럼 채워진 상태로 존재 / 셀·note에 `3개` 수치 없음 / `pm/dispatch-process.md` Step 6 참조 존재 / 변경이력 `(081)` 행 1개
- **테스트**: TS-001, TS-002, TS-009
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: `pm-review-gate.md` 워커 중단 산출물 실측 판정 절 신설
- [ ] 완료
- **소속 기능**: F-001 (REQ-2, REQ-5)
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/core/references/harness/pm-review-gate.md` (1개)
- **작업 내용**: §3.1.2 (B)의 확정 문언 3건을 Edit으로 삽입 — ①`### 워커 중단 시 산출물 실측 판정` 절(`### 워커 완료 선언` 블록 직후 / `### 검토 절차` 앞) ②`:5` 역할 라인 치환 ③변경이력 v1.9 행. **[MUST] 기존 표준 검토 항목 1~14의 본문을 수정하지 않는다** (`validate --changed`·커버리지 문구 존치 — 회귀 테스트 대상).
- **완료 기준**: 신규 절에 3단계가 순서대로 존재 / "완료분 ... 덮어쓰지 않는다"가 `[MUST]` 표현 / 절 본문에 `1회`·`3개` 수치 없음 / 역할 라인에 신규 절 포함 / 변경이력 `(081)` 행 1개
- **테스트**: TS-003, TS-004, TS-009, TS-012
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 3: `dispatch-process.md` 2개소 순차 편집 (산출량 상한 + 공통 고정 규율)
- [ ] 완료
- **소속 기능**: F-002 (REQ-3) + F-003 (REQ-4) + REQ-5
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/core/references/pm/dispatch-process.md` (1개)
- **작업 내용**: **한 디스패치 안에서 아래 순서대로** Edit — ①§3.2.2 (A) Step 6 항목 5 추가(`:152` 직후) → ②§3.3.2 (A) 주입 템플릿 `## 핵심 제약` 고정 2줄(코드 펜스 내부, `:93` 직후) → ③펜스 하단 note(`:103` 직후) → ④변경이력 v1.6 행(REQ-3·REQ-4 합산 1행). **[MUST] 이 파일을 다른 Step·다른 워커와 동시 편집하지 않는다.**
- **완료 기준**: 4개 편집이 모두 반영되고 서로 덮어쓰지 않음 / Step 6 항목 번호가 1~5로 연속 / 고정 2줄이 코드 펜스 **내부**에 위치 / 변경이력 `(081)` 행 1개
- **테스트**: TS-005, TS-007, TS-009
- **실행 방법**: sub-agent
- **의존**: 없음 (단 Step 4·5의 선행)

#### Step 4: `parallel-execution.md` §7.4 참조 1줄 + 변경이력 절 신설
- [ ] 완료
- **소속 기능**: F-002 (REQ-3, REQ-5)
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/core/references/harness/parallel-execution.md` (1개)
- **작업 내용**: §3.2.2 (B) 참조 bullet 1줄을 `:64` 직후 삽입, §3.2.2 (C) `## 변경이력` 절을 파일 말미에 신설(구분선 + 2행). **[MUST] §7.4·§7.5의 기존 수치(50KB/200KB/Max 2)를 변경하지 않는다.**
- **완료 기준**: §7.4에 추가된 줄이 정확히 1줄 / 그 줄에 임계값 숫자 없음 / `pm/dispatch-process.md` Step 6 참조 존재 / `## 변경이력` 절에 v1.0·v1.1 2행
- **테스트**: TS-006, TS-009
- **실행 방법**: sub-agent
- **의존**: Step 3 (참조 대상 선행 존재)

#### Step 5: `op-dev-execute/SKILL.md` Step 4 확장
- [ ] 완료
- **소속 기능**: F-003 (REQ-4, REQ-5)
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/op-dev-execute/SKILL.md` (1개)
- **작업 내용**: §3.3.2 (B)의 확정 문언으로 `:92-95`를 치환하고 변경이력 v2.4 행 추가. **[MUST] 규율 원문("말미 일괄 저장 금지" / "전체 파일 통독 금지")을 이 파일에 복제하지 않는다** — 참조만 한다.
- **완료 기준**: Step 4 제목이 "체크리스트 갱신 및 증분 저장" / `pm/dispatch-process.md` 참조 존재 / 규율 원문 복제 없음 / 변경이력 `(081)` 행 1개
- **테스트**: TS-008, TS-017, TS-009
- **실행 방법**: sub-agent
- **의존**: Step 3 (참조 대상 선행 존재)

#### Step 6: install 재배포 + 배포본 대조
- [ ] 완료
- **소속 기능**: F-004 (REQ-5)
- **영역**: 배치
- **agent**: PM 직접
- **파일**: 없음 (`scripts/install-mac.sh` 실행만 — 스크립트 비변경)
- **작업 내용**: §3.4.2 (A)의 2단계 스크립트 실행 — `./scripts/install-mac.sh` 후 5파일 strip 기준 diff.
- **완료 기준**: install 정상 종료 / 대조 결과 5건 전부 `OK` (diff 0줄)
- **테스트**: TS-010
- **실행 방법**: direct
- **의존**: Step 1, 2, 3, 4, 5

#### Step 7: 개선 후보 메모리 2건 졸업 + 히스토리 기록
- [ ] 완료
- **소속 기능**: F-004 (REQ-6)
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `.opal/MEMORY.json` (도구 경유 — 직접 편집 금지)
- **작업 내용**: §3.4.2 (B)의 `memory-tool` 명령 3건 실행 (`update` ×2 + `append --kind history` ×1). 각 호출의 JSON 응답 `ok: true`를 확인한다.
- **완료 기준**: `candidate` 상태 대상 2건이 0건 / 두 행이 `promoted` / `history`에 081 행 존재
- **테스트**: TS-011
- **실행 방법**: direct
- **의존**: Step 6 (SSOT 등재·배포가 졸업의 전제)

#### Step 8: 정합성 검증 3종 + 회귀
- [ ] 완료
- **소속 기능**: F-001, F-002, F-003, F-004 (완료기준 전체)
- **영역**: 배치
- **agent**: PM 직접
- **파일**: 없음 (검증만)
- **작업 내용**: 아래 4종 실행 —
  1. **앵커 존재 grep** — 5파일에 대해 §3의 확정 문언 키 문자열 존재 확인 (TS-001·003·005·006·007·008)
  2. **참조 무결성** — 신규 상호 참조 5건의 대상 실재 확인: (a) `opal-harness.md` → `harness/pm-review-gate.md` §워커 중단 시 산출물 실측 판정 (b) `opal-harness.md` → `pm/dispatch-process.md` Step 6 (c) `pm-review-gate.md` → `opal-harness.md` §1 자동 루핑 제약 표 (d) `pm-review-gate.md`·`parallel-execution.md`·`op-dev-execute` → `pm/dispatch-process.md` 해당 절 (e) `dispatch-process.md` → `harness/pm-review-gate.md` 신규 절
  3. **수치 유일성** — `grep -rn` 으로 재시도 `1회`·산출 `3개`·3단계 본문이 각각 1파일에만 존재함을 확인 (TS-014)
  4. **회귀** — `node --test opal/tools/code-scan/tests/test-regression.js` (TS-012)
- **완료 기준**: 4종 전부 기대값 일치, 회귀 실패 0건
- **테스트**: TS-012, TS-013, TS-014, TS-015, TS-016
- **실행 방법**: direct
- **의존**: Step 7

> **docs/ 갱신 Step 판단**: 불필요. 본 변경은 `opal/` 프레임워크 하네스·PM 참조 문서의 내부 규칙이며, `docs/BACKEND.md`·`docs/FRONTEND.md`·`docs/ARCHITECTURE.md` 대상 구조 변경이 없고, `docs/CONVENTIONS.md`가 규정하는 **프로젝트 코드 컨벤션**(네이밍·파일구조·커밋)에도 해당하지 않는다. 신규 문서 파일 생성이 없으므로 `docs/PROJECT.md` 문서 레지스트리 등록 대상도 아니다 (→ pm-review-gate.md `:73-79` 11번 docs/ 무효화 체크 기준 대조).

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 ∥ Step 2 | 서로 다른 파일. 상호 참조는 텍스트 문자열이라 컴파일 종속이 없어 선후 무관 |
| Step 3 단독 배치 | `dispatch-process.md` 단일 파일에 REQ-3·REQ-4가 동시 개입 — 분할 시 후행 저장이 선행 편집을 덮어쓴다 (→ D-0 §제약 조건, H-4) |
| Step 3 → Step 4 | Step 4가 삽입하는 참조가 Step 3의 Step 6 항목 5를 가리킨다 — 참조 무결성(TS-013) 확보 위해 선행 |
| Step 3 → Step 5 | Step 5가 삽입하는 참조가 Step 3의 주입 템플릿 고정 항목을 가리킨다 — 동일 이유 |
| Step 4 ∥ Step 5 | 서로 다른 파일, 서로 참조하지 않음 |
| Step 5 → Step 6 → Step 7 → Step 8 | 배포는 전 편집 완료 후, 메모리 졸업은 SSOT 등재 확정 후, 검증은 최종 상태에서 1회 |
| 배치별 산출 파일 ≤ 3 | Phase 1=2, Phase 2=1, Phase 3=2, Phase 4=0~1 — REQ-3이 신설하는 상한 자기 준수 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | 자동 루핑 제약 표 신규 행 3컬럼 완비 | TS-001 | 실패 유형·최대 재시도(1회)·초과 시 동작 모두 기재 |
| F-001 | 수치·절차 분리 준수 | TS-002, TS-004 | harness 표에 절차 없음, pm-review-gate에 수치 없음 |
| F-001 | 실측 판정 3단계 + 덮어쓰기 금지 [MUST] | TS-003 | 1·2·3 순서 존재, 금지가 `[MUST]` 표현 |
| F-002 | Step 6 산출량 상한 + 잠정치 단서 | TS-005 | "3개를 초과", "관측 기반 잠정치", "4~9 구간은 미검증" 존재 |
| F-002 | §7.4 참조 1줄 (본문 복제 금지) | TS-006 | 추가 줄 1개, 임계값 숫자 부재, Step 6 참조 존재 |
| F-002 | 앵커 타당성 (조건부 로드 회피) | TS-016 | 규칙 본문이 무조건 로드 문서(`dispatch-process.md`)에 위치 |
| F-003 | 주입 템플릿 고정 2항목 | TS-007 | 코드 펜스 내부 2줄 + `← 전 워커 공통 고정` 라벨 + 하단 note |
| F-003 | 두 문서 문언 무충돌 | TS-008, TS-017 | 스킬 측 규율 원문 복제 0건, 참조만 존재 |
| F-004 | 5파일 변경이력 행 | TS-009 | 각 파일 `(081)` 행 ≥1, 일시 `YYYY-MM-DD HH:mm` |
| F-004 | 배포본 일치 | TS-010 | strip 기준 diff 5건 전부 0줄 |
| F-004 | 메모리 졸업 | TS-011 | 대상 candidate 0건, promoted 2건, history 081 행 |

### 5.2 회귀 테스트

- [ ] `node --test opal/tools/code-scan/tests/test-regression.js` 전량 Pass (특히 `077 S-21: pm-review-gate.md` — H-3)
- [ ] `pm-review-gate.md` 표준 검토 항목 1~14 본문 무변경 (`validate --changed`·`coverage` 문구 존치)
- [ ] `opal-harness.md` §1 기존 8행·§9 code-scan 행 무변경 (`test-regression.js:925-928` 대상)
- [ ] `parallel-execution.md` §7.4 기존 수치(50KB/200KB/Max 2)·§7.5·§7.6 무변경
- [ ] `dispatch-process.md` Step 0~5·Step 7 및 주입 템플릿 기존 4블록 구조 무변경
- [ ] `op-dev-execute/SKILL.md` Step 3-S·3-H·Step 5·가드레일 6행 무변경
- [ ] install 후 `~/.opal/community-skills/` 사용자 데이터 무변경 (`install-mac.sh:1015`)

### 5.3 코드/문서 품질

- [ ] 5파일 전부 `## 변경이력` 행 추가 — [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무 (`docs/CONVENTIONS.md:200`)
- [ ] 일시 `YYYY-MM-DD HH:mm` KST, 버전 semver, 태스크 번호 `(081)` 괄호 포함 (`docs/CONVENTIONS.md:201`)
- [ ] Governance 준수 — 동일 규칙·수치가 2개 파일에 중복 기재되지 않음 (§1.5 매핑 표대로)
- [ ] Surgical 준수 — §3에 명시된 위치 외 편집 0건 (인접 문장 "개선" 금지)
- [ ] 모든 편집이 Edit(부분 치환)으로 수행되고 대상 5파일에 `Write` 사용 0건
- [ ] 신규 문언의 용어가 기존 문서 용어와 일치 (배치/디스패치/산출물/워커)

### 5.4 보안

- [ ] 변경 파일에 토큰·시크릿·개인 식별자 하드코딩 0건 (문서 트랙이나 형식 점검)
- [ ] 절대 경로에 사용자 홈 실경로 노출 없음 — 문서에는 `~/.opal/` 표기 사용
- [ ] `memory-tool` 호출이 `.opal/MEMORY.json`만 대상으로 하고 `~/.opal/` 배포본을 쓰지 않음
- [ ] install 실행이 `~/.opal/community-skills/` 사용자 데이터를 파괴하지 않음

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 8개 | 복잡 |
| 변경 파일 수 | 5개 (+ `.opal/MEMORY.json`) | 복잡 |
| 모듈 범위 | 다중 (하네스 · PM 참조 · 스킬 · 도구 데이터) | 복잡 |
| 작업 유형 | 규칙 신설 (대규모 개선) | 복잡 |
| 외부 의존성 | 없음 (기존 `memory-tool`·`install-mac.sh`만 사용) | 단순 |
| **실행 모드** | **복잡** | 하나라도 복잡이면 복잡 모드 |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

```
Batch 1 (병렬 2 워커, 산출 2파일)
  ├─ W1: opal-task-agent → Step 1  (opal-harness.md)
  └─ W2: opal-task-agent → Step 2  (pm-review-gate.md)
        ↓
Batch 2 (단일 워커, 산출 1파일)
  └─ W3: opal-task-agent → Step 3  (dispatch-process.md, 4개 편집 순차)
        ↓
Batch 3 (병렬 2 워커, 산출 2파일)
  ├─ W4: opal-task-agent → Step 4  (parallel-execution.md)
  └─ W5: opal-task-agent → Step 5  (op-dev-execute/SKILL.md)
        ↓
Batch 4 (PM 직접, 순차)
  └─ Step 6 install·대조 → Step 7 메모리 졸업 → Step 8 검증 4종
```

**그룹핑 근거**
1. **파일 충돌 방지 최우선** — `dispatch-process.md`를 만지는 편집 4건 전부를 W3 단독에 몰았다. 어떤 배치에서도 두 워커가 같은 파일을 열지 않는다.
2. **배치 크기 = REQ-3 상한 이하** — 최대 산출 2파일. 본 태스크가 신설하는 규칙을 스스로 위반하지 않는다.
3. **참조 방향 = 실행 순서** — 참조하는 쪽(Batch 3)이 참조되는 쪽(Batch 2) 뒤에 온다.

**워커 프롬프트 공통 주입 (REQ-4를 선제 자기적용)**
- 증분 저장: 편집 1건을 저장한 뒤 다음 편집으로 이동한다. 말미 일괄 저장 금지.
- 입력 축소: 대상 파일 전체 통독 금지. PLAN §3이 지정한 줄번호 근처만 offset Read하고 grep으로 앵커를 특정한 뒤 Edit한다.
- 문언 고정: PLAN §3의 확정 문언을 그대로 복사한다. 재작성·요약·의역 금지.
- `Write` 금지, `Edit` 전용.

### C-2. 스킬 요구사항

| 필요 역량 | 매칭 | 갭 |
|----------|------|-----|
| 문서 부분 편집 + 변경이력 추가 | `op-dev-execute` (Step 1~5 공통) | 없음 |
| 배포 실행·대조 | PM 직접 + `scripts/install-mac.sh` | 없음 |
| 메모리 조작 | `memory-tool` (`update`/`append`) | 없음 — 단 `promote` 경로는 사용 불가(H-7) |

신규 스킬 불필요 — 동일 패턴이 3개 Step 이상 반복되지만(문서 편집+변경이력) 기존 `op-dev-execute`가 이미 커버한다.

### C-3. 도구 요구사항

| 도구 | 용도 | 상태 |
|------|------|------|
| `scripts/install-mac.sh` | 재배포 | 기존 |
| `~/.opal/tools/memory-tool/run.sh` | candidate 졸업·히스토리 | 기존 |
| `~/.opal/tools/state-tool/run.sh` | STATE.md 갱신 (직접 편집 금지) | 기존 |
| `node --test` | 회귀 (`test-regression.js`) | 기존 |
| `git status` / `diff` / `awk` | 산출물 확정·배포 대조 | 기본 |

신규 설치 없음. code-scan은 **순수 .md 문서 작업이므로 호출 대상 아님** (`dispatch-process.md:107` 코드/문서 판별 기준 — "순수 .md 문서·기획·정책만이면 문서 작업").

### C-4. 테스트 전략

동적 동작검증이 성립하지 않는 트랙이므로 **정적 정합성 검증 + 회귀**로 구성한다 (→ D-0 §제약 조건).

| 계층 | 대상 | 실행 |
|------|------|------|
| L1 (정적) | TS-001~009, TS-013~017 | grep/Read 기반 앵커·문언·유일성 검사 (Step 8 항목 1~3) |
| L2 (통합) | TS-010, TS-011 | install 후 배포본 diff / `memory-tool` 실주행 응답 `ok:true` |
| L3a (회귀) | TS-012 | `node --test opal/tools/code-scan/tests/test-regression.js` |
| L3b (E2E) | — | 해당 없음 (런타임 파이프라인 실행 불요) |

> `op-dev-test-agent` 디스패치는 **불필요**하다 — 테스트 대상이 코드가 아니라 문서 문자열이며, 판정이 grep 결과와 기존 회귀 스위트로 전부 결정된다. TEST 단계는 PM 직접 수행을 권고한다 (PM 최종 판단).

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 문서 | Markdown (하네스·PM 참조 문서, 스킬 SKILL.md) | `op-dev-execute` |
| 배포 | Bash (`scripts/install-mac.sh`) | — |
| 도구 | Python CLI (`memory-tool`), Node `node --test` (회귀) | — |

> React/Next.js/Python/shadcn 등 `op-dev-plan` §Step 2 추천 스킬은 **해당 없음** — 코드 변경 0건, FE 화면 0건이다. `context7`·`shadcn` MCP도 조회 대상이 없어 미사용.

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| — | 미사용. 외부 라이브러리·컴포넌트 의존이 없는 내부 문서 규칙 트랙 |

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-0 | 기획 | 081 TASK.md | `tasks/081-260802-opds-워커중단-복구프로토콜/TASK.md` | REQ-1~6 원문, 배경 분석 §1~§4, 제약 조건 |
| D-1 | 설계 | opal-harness.md | `opal/core/references/opal-harness.md` | §1 자동 루핑 제약 표 현행 8행(:44-64), §2 Lazy 로드 조건(:102), §7 stub(:196-203) |
| D-2 | 설계 | pm-review-gate.md | `opal/core/references/harness/pm-review-gate.md` | 절 구조·삽입 위치 판정(:5,11-17,43-106,130-135), 변경이력 v1.8(:162) |
| D-3 | 설계 | parallel-execution.md | `opal/core/references/harness/parallel-execution.md` | §7.4 입력 KB·동시 개수 기준(:58-64), §7.5 리소스 폴백 프레임(:66-74), 변경이력 절 부재(89줄) |
| D-4 | 설계 | dispatch-process.md | `opal/core/references/pm/dispatch-process.md` | 주입 템플릿(:81-103), Step 6 4항목(:145-152), 코드/문서 판별(:107), v1.0 날짜 `-` 선례(:169) |
| D-5 | 설계 | op-dev-execute SKILL.md | `opal/skills/op-dev-execute/SKILL.md` | Step 4 현행(:92-95), 인접 Step 3-S/3-H 패턴(:57-90), 변경이력 v2.3(:207) |
| D-6 | 설계 | 078 DONE.md | `tasks/078-260728-opd-메모리-json전환/DONE.md` | §8 완화 조합 원문 — 모델 하향+통독 금지+함수 단위 저장+배치 4분할 → 이후 전량 성공 |
| D-7 | 설계 | 079 DONE.md | `tasks/079-260730-opds-히스토리-정정명령/DONE.md` | §8 선제 적용 → 인프라 실패 0건 재현, Write 금지·Edit 전용 규율 |
| D-8 | 소스 | 프로젝트 메모리 | `.opal/MEMORY.json` | candidate 2건 실측(제목·file 필드), 스키마 4키 |
| D-9 | 설계 | 프로젝트 PM 프로필 | `.opal/AGENT.md` | §금지사항 6항(:61-66) — 배포 경계·변경이력 의무 |
| D-10 | 소스 | install-mac.sh | `scripts/install-mac.sh` | 변경이력 strip awk(:206-220), references 배포(:1364), skills 배포(:1041-1052), community-skills 불가침(:1015) |
| D-11 | 소스 | memory_tool.py | `opal/tools/memory-tool/memory_tool.py` | `promote`의 `memory_file_not_found` 전제(:1164-1168) — promote 불가 판정 근거 |
| D-12 | 설계 | memory-tool README | `opal/tools/memory-tool/README.md` | `update --kind memory` 허용 필드(:106-110), 상태 enum(:94,263-266), promote 계약(:120-137) |
| D-13 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | §변경이력(:92-104), §변경이력 작성 의무(:198-202), §배포 경계(:204-210) |
| D-14 | 설계 | PRINCIPLES.md | `~/.opal/PRINCIPLES.md` | §Core Stance(:15), §3 Surgical(:30), §Governance(:43) |
| D-15 | 소스 | test-regression.js | `opal/tools/code-scan/tests/test-regression.js` | `RULE_DOCS.pmReviewGate`(:295), 077 S-21 검사(:930-934) — 회귀 영향 판정 |
| D-16 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | §2 인용 포맷·§4 PLAN 단계 의무 수준 |
| D-17 | 설계 | opal-pm.md | `opal/core/references/opal-pm.md` | :49,57(dispatch-process 무조건 진입), :66(pm-review-gate 열거형 포인터 — H-2) |

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | `dispatch-process.md` 2개소 편집이 분리 디스패치되어 한쪽만 반영 (H-4) | F-002, F-003 | 높음 | Step 3 단일 워커 강제 + 완료 기준에 "4개 편집 모두 반영" 명시 + TS-005·TS-007 동시 검증 |
| R-2 | 수치가 2파일에 중복 기재되어 Governance 위반 (H-5) | F-001~003 | 높음 | §1.5 규칙 1소유자 매핑 표를 워커 프롬프트에 주입 + TS-014 리터럴 유일성 grep |
| R-3 | `promote` 경로 실패로 REQ-6 blocked (H-7) | F-004 | 중간 | `update --status promoted` 대체 경로를 §3.4.2 (B)에 확정 기재 — 실행 전 판정 완료 |
| R-4 | 배포본 단순 diff 오탐으로 검증 실패 오판 (H-6) | F-004 | 중간 | install과 동일한 awk strip을 소스에 적용 후 diff (§3.4.2 (A) 스크립트) |
| R-5 | `pm-review-gate.md` 절 삽입 중 기존 14항목 본문 훼손 → 회귀 실패 (H-3) | F-001 | 중간 | Edit 전용·삽입 전용(치환은 `:5` 역할 라인 1줄만) + TS-012 회귀 실행 |
| R-6 | `parallel-execution.md` 변경이력 절 부재로 REQ-5 AC 미충족 (H-8) | F-002 | 중간 | 절 신설을 Step 4 작업 내용에 포함, v1.0 날짜 `-` 선례(D-4:169) 준수 — **PM 확인 필요(M-3)** |
| R-7 | 주입 템플릿 고정 항목이 문서 유래 [MUST]와 혼동 (H-9) | F-003 | 낮음 | `← 전 워커 공통 고정` 라벨 + 펜스 하단 note에 "근거 문서가 없는 운영 규율" 명시 |
| R-8 | `opal-pm.md:66` 열거형 포인터 stale 지속 (H-2) | F-001 | 낮음 | 본 태스크 비변경(Surgical) — TS-015로 관측 기록만, 후속 F-4로 제안 |
| R-9 | 임계값 3이 잠정치인데 확정치로 굳어져 4~9 구간 오차단 | F-002 | 낮음 | 규칙 본문에 "관측 기반 잠정치 / 4~9 미검증 / 갱신 대상" 3중 단서 명시 |
| R-10 | 용어 일관성 — "산출물"(문서 파일) ↔ "산출 파일"(디스패치 계수 단위) | F-002, F-003 | 낮음 | 계수 대상은 "산출 파일", 저장 단위는 "산출물"로 문서 전반 고정 (citation-rules.md §7.1 검토 — 영역 간 충돌 아님, 단일 문서 내 용어 분화라 `decision_required` 미해당) |

---

## 부록. PM 판단 필요 항목 (decision_required)

| # | 항목 | 워커 권고 | 대안 | 판단 근거 |
|---|------|----------|------|----------|
| M-1 | **앵커 타당성** — TASK 제안 앵커 유지 여부 | **유지 (교정안이 옳음)** | 없음 | `parallel-execution.md` Lazy 조건 "병렬 디스패치 시"를 3개소(`opal-harness.md:102,198,202` + 파일 `:4`)에서 실측 확인. 080 실패는 단일 디스패치 → 이 문서에 두면 로드 안 됨. `dispatch-process.md`는 `opal-pm.md:49,57`상 무조건 진입 |
| M-2 | **REQ-2 배치 위치** | `### 워커 완료 선언` **직후 형제 절** | 표준 검토 항목 15번 / `### 판정` 확장 | 1~14번은 산출물 확정 후 품질 검사이고 실측 판정은 선행 단계. 정상/비정상 경로 병치가 문서 시간 순서와 일치 (§3.1.2 (B) 판정 표) |
| M-3 | **`parallel-execution.md` 변경이력 절 신설** | **신설 (v1.0 `-` + v1.1)** | 신설 생략하고 `opal-harness.md` 변경이력에만 기록 | REQ-5 AC는 "변경된 각 파일"을 요구. 다만 절 신설은 REQ가 명시하지 않은 구조 추가라 Surgical 경계에 걸침 — 선례는 `dispatch-process.md:169` |
| M-4 | **`pm-review-gate.md` 역할 라인(`:5`) 수정** | **수정 (신규 절 반영 + "11항목" 고정 표기 제거)** | 역할 라인 미수정 | 신규 절이 문서 자기소개에서 누락되면 Lazy 로드 판단에 불리. 단 "11항목→표기 제거"는 선행 결함 교정을 겸하므로 Surgical 경계 확인 필요 |
| M-5 | **`opal-pm.md:66` "검토 11항목" 포인터** | **본 태스크 비변경** (TS-015 관측만) | 6번째 파일로 포함해 동시 교정 | 이미 14항목과 불일치하는 **선행 결함**이며 REQ가 명시하지 않은 파일. 후속 F-4(문서 포인터 현행화)로 분리 제안 |
| M-6 | **REQ-6 상태값 선택** | **`--status promoted`** | `superseded` / `dead` | `promote` 서브명령은 `memory_file_not_found`로 거부됨(`memory_tool.py:1164-1168`, 대상 md 파일 부재 실측). 두 후보는 대체가 아니라 SSOT 졸업이므로 `promoted`가 라이프사이클 의미상 정확. 단 README `:264`는 `promoted`의 생산 경로를 `promote` 명령으로 기술하므로 명령↔상태 결합을 엄격히 보려면 `superseded` 선택 가능 |
| M-7 | **후속 tool-gating 분리** | REQ-3 임계값 확정 후 **F-1(재개 카운터)과 묶어 단일 후속 태스크** | 본 태스크에 포함 | 임계값 3이 잠정치(4~9 미검증)라 지금 도구로 잠그면 미검증 수치를 강제 (§1.6) |
| M-8 | **TEST 단계 수행 주체** | **PM 직접** (`op-dev-test-agent` 미디스패치) | test-agent 디스패치 | 판정이 grep 결과 + 기존 회귀 스위트로 전부 결정되는 정적 검증이며, 동적 실행 대상이 없음 (§C-4) |

