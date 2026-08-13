---
name: opal-pilot-write-tech
description: |
  **서비스 기획 산출물 네트워크 오케스트레이터**. 기술 산출물(PRD, TRD, 서비스 정책서, IA 등)을 논리적 네트워크로 관리한다.
  PM이 워커를 병렬 디스패치하여 문서를 분석/작성하고, 교차 논리 검토와 정합성 검증으로 문서 간 일관성을 보장한다.
  반드시 이 스킬: "opal-pilot-write-tech", "opwt", "기획 문서 세트", "기술 산출물 작성", "기획 문서 검토", "기획 문서 최신화".
---

# opal-pilot-write-tech

서비스 기획 산출물 네트워크 오케스트레이터.

## Harness

> 부트스트랩에서 로드되지 않은 경우: `~/.opal/references/opal-harness.md`를 Read한다.
> 병렬 처리 원칙은 하네스 §7을 따른다 — 읽기는 병렬 툴콜, 독립 작업은 병렬 Agent 디스패치.

**[MUST]** 스킬 시작 즉시 모드에 따라 서브 하네스를 Read한다. 이 단계를 건너뛰면 안 된다:
- `--interactive` 플래그 → `~/.opal/references/opal-harness-interactive.md`를 Read한다
- `--agentic` 플래그 → `~/.opal/references/opal-harness-agentic.md`를 Read한다
- 모드 플래그 없음 (기본) 또는 `--semi-agentic` → `~/.opal/references/opal-harness-semi-agentic.md`를 Read한다
- 다중 모드 플래그 동시 사용 시 즉시 사용자에게 보고 + state init도 거부 (`mode_flag_conflict`)

> **[MUST]** 산출물 작성·검증 시 `opal/core/references/harness/citation-rules.md`를 Read하여 규칙(근거 제시 원칙 / 트랙별 매트릭스 / [MUST] 토큰 / 영역 간 용어 일관성 / decision_required 계약)을 준수한다.

## 설계 원칙

- **문서가 인터페이스** — 프로젝트 문서(`docs/`)만 참조, 다른 스킬의 존재를 모른다
- **PM 중심 관리** — 교차 검토/진단/배치 편성/최종 판정/문서 등록
- **병렬 우선** — 독립 문서는 읽기/분석/작성 모두 병렬. 의존관계 있는 문서만 순차

## 커버 범위

**필수 4종**: PRD, TRD, 서비스 정책서(복수), IA(기능 포함 — JSON + Mermaid 사이트맵 이중 출력)
**선택 5종**: 기능도, 기능 시나리오 다이어그램, 화면 흐름도, 운영 정책서, 서비스 매뉴얼
**프로젝트 특화 선택**: 외부 API 명세서 (외부 API 연동 프로젝트 한정 — 메타, 구글광고 등 서드파티 API 스펙 기획 산출물화)
**순서 체인**: PRD → TRD → 서비스 정책서 → IA (역방향도 가능)
**외부 참조**: 와이어프레임, ERD 등 프로젝트 내 기존 문서를 참조하여 작성 품질 향상 (읽기 전용, 선택적)

## 산출물 저장 구조

- `docs/` = 메타 문서 (`PROJECT.md`가 SSOT), 산출물은 별도 폴더
- PM이 `docs/PROJECT.md`로 기존 구조 파악 → 없으면 아래 **default 트리** 제안 → `PROJECT.md`에 기록
- 사용자가 다른 컨벤션을 원하면 자유 입력 (PM은 default를 강제하지 않음)

### Default 폴더 구조 (v4)

산출물 작성이 결정된 항목만 폴더를 생성한다 (작성 안 함 → 폴더 없음). 폴더 prefix는 10 간격으로 향후 산출물 추가 시 사이 삽입을 허용한다.

```
100.기획/
├── 110.PRD/                     ← 필수 (작성 결정 시)
│   └── PRD.md
├── 120.TRD/                     ← 필수 (작성 결정 시)
│   └── TRD.md
├── 130.정책서/                  ← 필수 (도메인별 파일 분리)
│   ├── 계정.md
│   ├── wiki.md
│   └── LLM사용.md
├── 140.IA/                      ← 필수 (JSON + Mermaid 사이트맵)
│   ├── ia.json
│   └── ia-sitemap.md
├── 150.기능도/                  ← 선택 (작성 결정 시)
│   └── 기능도.md
├── 160.화면흐름도/              ← 선택 (작성 결정 시)
│   └── 화면흐름도.md
└── 170.기능시나리오/            ← 선택 (시나리오별 파일 분리)
    ├── 회원가입.md
    └── 결제.md
```

**조건부/선택 산출물** (default 트리 미포함, 작성 결정 시 폴더 prefix 신규 부여):

- 외부 API 명세서 (조건부) — `180.외부API명세/` 권장
- 운영 정책서 (선택) — `190.운영정책/` 또는 `130.정책서/`에 흡수
- 서비스 매뉴얼 (선택) — `190.매뉴얼/` 또는 별도 폴더

**폴더명 컨벤션**:

- 한국어 폴더명 + `XXX.{이름}/` 형식 — 가독성·정렬 우선
- `docs/CONVENTIONS.md`가 kebab-case를 명시한 프로젝트는 사용자 결정으로 컨벤션 충돌을 PM이 인터뷰에서 확인한다


## 3가지 모드와 단계 선택

| 모드 | 단계 |
|------|------|
| 작성 | TASK → PLAN(간략) → EXECUTE → QA |
| 수정 | TASK → ANALYSIS → PLAN → EXECUTE → QA |
| 분석 | TASK → ANALYSIS → PLAN(진단보고) → QA |

---

## TASK 단계

오케스트레이터가 **직접 수행**한다. 하네스 §4 TASK 공통 프로세스 기반 + opwt 전용 확인 항목.

### interview 스킬 호출

TASK 단계에서 사용자 요구사항을 수집하기 위해 **interview 스킬**을 호출한다. 스킬 탐색 경로 (순서대로):

1. `{프로젝트}/.opal/skills/interview/SKILL.md`
2. `~/.opal/skills/interview/SKILL.md`

### Round 1/2/3 라운드 설계

| 라운드 | 질문 수 | 옵션 형식 | multiSelect | 트리거 조건 |
|--------|--------|----------|-------------|------------|
| Round 1 | 3개 | Q1 모드: single / Q2 표준 산출물: multiSelect / Q3 외부 API: single (조건부) | Q2 표준 산출물 항목만 | 항상 |
| Round 2 | 3개 | Q4 부가 산출물: multiSelect (필터링) / Q5 외부 참조: multiSelect (자동 감지 확인) / Q6 산출물 저장 경로: single (default 자동 감지 / 직접 입력) | Q4·Q5 | 항상 |
| Round 3 | PRD 5섹션 (free text) | free text | - | **PRD가 Round 1 답변에서 표준 산출물로 선택된 경우에만** |

### Step 1 — opwt 도메인 옵션 구성 (interview 호출 전)

interview 스킬 호출 전에 다음 신호 탐지를 선행하여 Q3·Q4·Q5 옵션을 동적으로 구성한다.

**(a) 외부 API 신호 탐지** → Q3 조건부 노출

사용자 요청 및 `PROJECT.md`에서 다음 키워드/도메인 검색:
- 키워드: "메타", "구글 광고", "카카오", "결제 게이트웨이", "OAuth", "Open API", "서드파티", "SaaS 연동"
- 도메인: 광고 / 소셜로그인 / 결제 / AI / SMS·이메일 / 지도 / 푸시

키워드 또는 도메인이 탐지되면 Q3(외부 API 연동 여부)를 Round 1에 포함한다.

**(b) 부가 산출물 신호 탐지** → Q4 옵션 필터링

사용자 요청에서 다음 신호 탐지 후 Q4에 해당 옵션만 노출:
- "관리자" 언급 → 운영 정책서 후보
- "사용자에게 안내" → 서비스 매뉴얼 후보
- "화면 많음/UI 복잡" → 화면 흐름도 후보
- "결제·예약·인증 복잡" → 기능 시나리오 다이어그램 후보
- "시스템 모듈 다수" → 기능도 후보

**(c) 외부 참조 자동 스캔** → Q5 옵션 자동 구성

`docs/wireframes/`, `docs/erd/`, `docs/api-spec/` 폴더 스캔하여 존재하는 파일을 Q5 옵션으로 자동 구성한다.

**(d) 산출물 저장 경로 자동 감지** → Q6 옵션 구성

`docs/PROJECT.md`에서 산출물 저장 폴더가 이미 등록되어 있는지 확인하고 Q6 옵션을 구성한다:

1. **PROJECT.md에 등록된 폴더가 있음** → Q6 옵션 1: "기존 등록 경로 사용 ({등록 경로})" + Q6 옵션 2: "다른 경로 직접 입력"
2. **PROJECT.md에 등록 없음 + 프로젝트 루트에 `100.기획/` 폴더가 이미 존재** → Q6 옵션 1: "`100.기획/` (감지됨)" + Q6 옵션 2: "다른 경로 직접 입력"
3. **둘 다 없음** → Q6 옵션 1: "`100.기획/` (default v4)" + Q6 옵션 2: "`docs/planning/` (kebab-case 컨벤션)" + Q6 옵션 3: "직접 입력"

Q6 답변 결과는 Step 4에서 TASK.md "산출물 저장 경로" 섹션에 기록되고, 동시에 PM이 `docs/PROJECT.md`에 등록한다.

### Step 4 — interview 결과 기록

interview 완료 후 결과를 TASK.md에 다음 섹션 양식으로 기록한다:

```markdown
## 산출물 결정

| 분류 | 산출물 | 작성 여부 |
|------|-------|---------|
| 필수 | PRD | ✅ / ⬜ |
| 필수 | TRD | ✅ / ⬜ |
| 필수 | 서비스 정책서 | ✅ / ⬜ |
| 필수 | IA | ✅ / ⬜ |
| 선택 | 기능도 | ✅ / ⬜ |
| 선택 | 기능 시나리오 다이어그램 | ✅ / ⬜ |
| 선택 | 화면 흐름도 | ✅ / ⬜ |
| 선택 | 운영 정책서 | ✅ / ⬜ |
| 선택 | 서비스 매뉴얼 | ✅ / ⬜ |
| 프로젝트 특화 | 외부 API 명세서 | ✅ / ⬜ |

## 외부 참조 산출물

- (탐지된 참조 파일 목록 또는 "없음")

## 산출물 저장 경로

- **선택된 경로**: (Q6 답변 — 예: `100.기획/` 또는 `docs/planning/` 또는 사용자 직접 입력)
- **PROJECT.md 등록 여부**: (PM이 등록 완료 시 ✅ / 미등록 시 ⬜)
- **default 트리 적용 여부**: (default v4 적용 시 ✅, 사용자 정의 시 ⬜)

## PRD 입력 컨텍스트

> PRD가 Round 1 답변에서 표준 산출물로 선택된 경우에만 작성

- **배경 및 목표**: (Round 3 답변)
- **타깃 사용자**: (Round 3 답변)
- **주요 기능 + MVP 범위**: (Round 3 답변)
- **Non-goals**: (Round 3 답변)
```

### 완료 처리

- TASK.md 작성 (interview 결과 — 산출물 결정 표 + 외부 참조 산출물 + PRD 입력 컨텍스트 포함)
- STATE.md 초기화 — state-tool을 호출한다:
  ```
  ~/.opal/tools/state-tool/run.sh init <task-path> --skill opwt --mode <interactive|semi-agentic|agentic> --rows-from opal/skills/opal-pilot-write-tech/references/pipeline.json
  ```
- 행 갱신:
  ```
  ~/.opal/tools/state-tool/run.sh advance <task-path> --row 1   # TASK 작업 행 🔄
  ~/.opal/tools/state-tool/run.sh mark <task-path> --row 1 --done  # TASK 작업 + TASK.md 생성
  ~/.opal/tools/state-tool/run.sh mark <task-path> --row 2 --done --owner user --note '{owner_name} 확인: TASK 완료'
  ```

> **[MUST] 행 갱신**: `mark` 호출 자체가 state 기록이며 별도의 State Gate 행은 존재하지 않는다. state-tool stage-transition guard가 단계 완료 여부를 자동 검증한다.

- 보고 후 다음 단계 승인 (interactive) / 자율 진행 (agentic)

---

## ANALYSIS 단계

> **적용 모드**: 수정, 분석

### 읽기 (병렬 툴콜)

기존 문서 경로를 스캔하여 독립 문서를 **병렬 Read**한다.

### 분석 (병렬 Agent 디스패치)

문서별 워커를 **병렬 디스패치**하여 요약/이슈를 반환받는다.

- 워커 프롬프트: `references/network-guide.md` "Phase 1 워커 프롬프트"
- **[PM 컨텍스트 주입]** 워커 프롬프트 첫 줄에 `[WORKER]` 삽입. 하네스 Guards 핵심 규칙 + 관련 참조 문서 경로를 포함한다.

### 산출물

워커 분석 결과를 취합하여 `ANALYSIS.md`로 저장한다.

```
tasks/{NNN}-opwt-{name}/ANALYSIS.md
- 문서별 요약 및 이슈 목록
- 워커별 반환 결과 취합
```

### STATE 갱신

- 단계 시작 시: state-tool advance 호출
- 단계 완료 시: state-tool mark 호출

### 게이트

ANALYSIS 완료 후 아래 절차를 순서대로 수행한다:

1. **PM Gate (자가 체크)** — ANALYSIS는 PM이 직접 수행하는 단계이므로 외부 QA 에이전트 호출 없이 PM이 자가 점검한다.
   - AGENT.md 검토 기준(§4) 7항목을 체크한다
   - ANALYSIS.md 내용이 모든 워커 결과를 취합하고 있는지 확인한다
   - 문서별 요약 및 이슈 목록이 누락 없이 작성되었는지 확인한다
   - Artifact Gate: `ANALYSIS.md` 파일이 존재하고 내용이 있는지 확인한다
2. PM Gate 통과 후 해당 행을 단일 mark:
   ```
   ~/.opal/tools/state-tool/run.sh mark <task-path> --row <ANALYSIS_PM_Gate_N> --done
   ```
3. 사용자 확인 (interactive) / PM 자율 승인 (agentic):
   ```
   ~/.opal/tools/state-tool/run.sh mark <task-path> --row <ANALYSIS_사용자확인_N> --done --owner user --note '{owner_name} 확인: ANALYSIS 완료'
   ```

---

## PLAN 단계

PM이 **직접 수행**한다.

### 수정/분석 모드 (전체 진단)

1. ANALYSIS.md 결과 기반 종합
2. 외부 참조 산출물 **병렬 Read** (와이어프레임, ERD 등)
3. 교차 논리 검토 — 누락/불일치 진단
4. 문서별 조치 결정 (보강/재작성/신규)
5. `diagnosis.json` 생성 → `depends_on` 기반 배치 편성

### 작성 모드 (간략 진단)

기존 문서 없음 → 신규 작성 대상 문서 목록 확정 → `diagnosis.json` 생성

### 산출물

`PLAN.md` 작성 후 태스크 폴더에 저장한다.

```
tasks/{NNN}-opwt-{name}/PLAN.md
- 교차 논리 검토 결과 및 진단 근거
- 배치 편성 요약 (diagnosis.json 인간 가독 버전)
- QA 체크리스트 (EXECUTE 완료 후 갱신)
```

`diagnosis.json`은 EXECUTE 단계의 기계 처리용 별첨으로 별도 저장한다.

### 공통

- **STATE 갱신**: 단계 시작/완료 시 state-tool advance/mark 호출
- **PM Gate** (PLAN.md + TASK.md 요구사항 체크박스 갱신 포함):
  - PLAN.md 진단 근거·배치 편성·QA 체크리스트 완성도 확인
  - TASK.md 요구사항 전체 커버 여부 확인
  - PM Gate 통과 후 해당 행을 단일 mark:
    ```
    ~/.opal/tools/state-tool/run.sh mark <task-path> --row <PLAN_PM_Gate_N> --done
    ```
- 사용자 확인 (interactive) / PM 자율 승인 (agentic):
  ```
  ~/.opal/tools/state-tool/run.sh mark <task-path> --row <PLAN_사용자확인_N> --done --owner user --note '{owner_name} 확인: PLAN 완료'
  ```
- **게이트**: PLAN.md + 배치 계획 사용자 확인 (interactive) / PM 자율 승인 (agentic)

---

## EXECUTE 단계

> **적용 모드**: 작성, 수정

`diagnosis.json` 파싱 → 배치별 순회:

- **독립 배치**: 워커 **병렬** 디스패치
- **의존 배치**: 선행 배치 완료 후 순차 실행

### 워커 디스패치

- 워커 프롬프트: `references/network-guide.md` "Phase 3 워커 프롬프트"
- **[PM 컨텍스트 주입]** 워커 프롬프트 첫 줄에 `[WORKER]` 삽입. 하네스 Guards 핵심 규칙 + 관련 참조 문서 경로를 포함한다.

### STATE 갱신

- 배치 시작 시: `advance` 호출 → `Batch N 진행 중`
- 배치 완료 시: state-tool mark 호출 → 배치 계획 테이블 갱신

### 게이트 (배치별)

배치 완료
  → **PM Gate** (배치 단위 간이 검토 — 문서 내용 완성도·논리 일관성 확인. 전체 PM Gate는 QA 단계 최종 판정에서 수행):
  ```
  ~/.opal/tools/state-tool/run.sh mark <task-path> --row <EXECUTE_Batch_PM_Gate_N> --done
  ```

  → 사용자 확인 (interactive) / PM 자율 승인 후 다음 배치 (agentic):
  ```
  ~/.opal/tools/state-tool/run.sh mark <task-path> --row <EXECUTE_Batch_사용자확인_N> --done --owner user --note '{owner_name} 확인: Batch N 완료'
  ```
배치 완료 후 `docs/PROJECT.md` 등록 확인

---

## QA 단계

QA 워커 디스패치 (`references/consistency-rules.md` 기반, 유형 간+내 검증).

- **[PM 컨텍스트 주입]** QA 워커 프롬프트 첫 줄에 `[WORKER]` 삽입. 하네스 Guards 핵심 규칙 + 관련 참조 문서 경로를 포함한다.

### STATE 갱신

- 단계 시작/완료 시 state-tool advance/mark 호출

### 산출물

PLAN.md의 QA 체크리스트를 검증 결과로 갱신한다 (하네스 §2 QA 체크리스트 갱신 의무).
모든 항목이 `[x]` 또는 "N/A + 사유"로 채워져야 한다.

### PM 최종 판정

- **PM Gate** — 전체 기획 문서 세트 최종 검증:
  - `references/consistency-rules.md` 기반 유형 간/내 정합성 확인
  - 모든 QA 체크리스트 항목이 `[x]` 또는 "N/A + 사유"로 채워졌는지 확인
  - PM Gate 통과 후 해당 행을 단일 mark:
    ```
    ~/.opal/tools/state-tool/run.sh mark <task-path> --row <QA_PM_Gate_N> --done
    ```
- **Pass**: 사용자에게 완료 보고 후 CLOSE 단계 진입 승인 요청

  보고 형식:
  ```
  📋 [QA] 완료 보고
  📎 산출물: {QA 결과 파일}
  다음 단계(CLOSE)로 넘어갈까요?
  ```

- **Fail**: EXECUTE 부분 재진입 (실패 문서만)

---

## CLOSE 단계

QA 최종 판정 Pass 후 태스크를 마감한다.

1. DONE.md 생성 후 행 mark:
   ```
   ~/.opal/tools/state-tool/run.sh mark <task-path> --row <CLOSE_DONE_행N> --done  # DONE.md 생성
   ```
   > **CLOSE 게이트 제약 (§2.16 G-13)**: CLOSE 단계 최초 진입 행은 `--auto-pass` 적용 불가 (`close_gate_violation`). 반드시 위 명시 호출로 처리한다.
2. **관련 문서 업데이트** (op-brain-ingest 디스패치 직전 실행):
   - `<프로젝트-루트>/docs/PROJECT.md`의 "프로젝트 문서" 레지스트리와 이번 태스크의 `changed_files`(EXECUTE 산출)를 양쪽 종합하여, 태스크 결과로 내용이 달라진 관련 문서(ARCHITECTURE.md·기획서 등)를 식별한다.
   - 갱신 대상이 있으면 PM이 판단하여 직접 수정하거나 적합한 워커를 디스패치해 최신화한다. 갱신 대상이 없으면 자연 스킵(no-op) — CLOSE를 중단시키지 않는다.
   - 목적: brain ingest 이전에 기획·설계 문서를 최신 상태로 만들어 ingest 품질을 보장한다.
3. **op-brain-ingest 디스패치** (DONE.md 생성 직후 실행):
   - `<프로젝트-루트>/.opal/brain/` 존재 여부를 확인한다.
   - **brain이 존재하면**: op-brain-ingest 워커를 디스패치하여 태스크 산출물(DONE.md·PLAN 결정·신규 엔티티)을 brain에 누적한다.
   - **brain이 없으면**: 자연 스킵(no-op). CLOSE가 막히지 않는다.
   - op-brain-ingest 탐색 경로:
     1. `{프로젝트}/.opal/skills/op-brain-ingest/SKILL.md`
     2. `~/.opal/skills/op-brain-ingest/SKILL.md`
   - 디스패치 입력: 태스크 폴더 경로
   - 워커가 `status: skipped` 또는 `status: completed` 또는 `status: completed_with_errors` 반환 — 어떤 경우도 CLOSE를 중단시키지 않는다.
4. **회고(개선 루프) 하드스텝** (op-brain-ingest 직후 실행):
   - 입력: 태스크/세션 궤적 신호 — 워커 재시도·폴백, 소유자 재지시·피드백, PM Gate 반복 이슈, PLAN 재진입, 검증/재설계 루프 로그(STATE.md). ※ 산출물 재독이 아님(그건 PM Gate/QA 담당). 산출 = 프로세스·규칙 개선점.
   - 관찰→분류(로컬 PM 개선 / FW 개선)→기록: 개선 후보별로 `~/.opal/tools/improve-tool/run.sh record --scope <local|fw> --title ... --body ... --situation retrospective --source-task <NNN> --project-root <루트>` 호출.
   - 산출 결정론 기록: 개선 후보 N건은 improve-tool이 결정론적으로 기록(로컬→.opal / FW→fw-inbox).
   - **no-op 안전 [MUST]**: 궤적 신호에서 개선 후보가 **없으면** 기록 없이 "개선후보 0건" 보고 — op-brain-ingest의 skipped와 동일하게 **CLOSE를 중단시키지 않는다**.
   - 개선 루프 프로세스 SSOT: `opal/core/references/harness/pm-improvement-loop.md`.
5. 완료 보고

보고 형식:
```
✅ [CLOSE] 태스크 완료
📎 산출물: tasks/{NNN}-{태스크명}/DONE.md
태스크가 완료되었습니다.
```

> **추가작업**: 태스크 완료 후 추가작업이 필요하면 하네스 §3 "추가작업 프로세스"를 따른다.
> **추가작업 발생 시 (P-6)**: `add-row --after <CLOSE_DONE_행N> --stage CLOSE --item '추가 작업 항목'` → 작업 완료 후 `status --set additional_work_done`

---

## STATE.md 도메인 치환값

하네스 STATE.md 기본 구조에 도메인 고유 섹션 추가:

- `{모드}`: 작성/수정/분석
- `{단계 목록}`: TASK → ANALYSIS → PLAN → EXECUTE → QA → CLOSE (모드에 따라 일부 생략)
- **네트워크 상태**: 산출물 | 유형 | 상태 | 버전 | 경로
- **배치 계획**: Batch | 문서 | 의존 | 상태

> **[SSOT]** SSOT는 `references/pipeline.json`이며, `state-tool init` 호출 시 이를 `--rows-from` 옵션으로 참조한다:
>
> ```
> ~/.opal/tools/state-tool/run.sh init <task-path> --skill opwt --rows-from opal/skills/opal-pilot-write-tech/references/pipeline.json
> ```
>
> opwt는 모드(작성/수정/분석)에 따라 단계 구성이 가변적이다. state-tool은 `references/pipeline.json`을 읽어 초기 행을 생성한다. EXECUTE 단계의 배치 행은 PLAN 완료 후 `add-row`로 동적 삽입한다:
> ```
> ~/.opal/tools/state-tool/run.sh add-row <task-path> --after <EXECUTE_행N> --stage EXECUTE --item 'Batch N: {문서 목록}'
> ```

**진행 현황 행 예시** (아래 표는 사람 열람용 미러 — SSOT는 `references/pipeline.json`. `.md` 파싱은 하위호환 폴백으로만 존치, 편집 금지):

> **[MUST] STATE.md 초기 생성**: `~/.opal/tools/state-tool/run.sh init <task-path> --skill opwt --mode <interactive|semi-agentic|agentic> --rows-from opal/skills/opal-pilot-write-tech/references/pipeline.json` 호출.

```markdown
| # | 단계 | 항목 | 상태 | 시점 |
|---|------|------|------|------|
| 1 | TASK | 작업 | ⬜ | - |
| 2 | TASK | 사용자 확인 | ⬜ | - |
| 3 | PLAN | 작업 | ⬜ | - |
| 4 | PLAN | PM Gate | ⬜ | - |
| 5 | PLAN | 사용자 확인 | ⬜ | - |
| 6 | EXECUTE | 작업 (Batch 동적 삽입) | ⬜ | - |
| 7 | QA | 작업 | ⬜ | - |
| 8 | QA | PM Gate | ⬜ | - |
| 9 | QA | 사용자 확인 | ⬜ | - |
| 10 | CLOSE | DONE.md 생성 | ⬜ | - |
```

> TASK.md 생성은 행 1(TASK 작업)에 흡수. ANALYSIS 모드에서는 ANALYSIS 행이 PLAN 앞에 삽입된다. State Gate 행은 state-tool stage-transition guard로 이전 — 행으로 강제하지 않는다.
> EXECUTE 배치 행은 PLAN 완료 후 `add-row`로 동적 삽입한다. 배치별 PM Gate·사용자 확인 행도 함께 삽입한다.

---

## 문서 표준

opal-doc-standard 적용: `~/.opal/references/opal-doc-standard.md`

## 참조 가이드

- `references/network-guide.md` — 산출물 정의, 연결 맵, diagnosis.json 스키마, 워커 프롬프트, 배치 규칙, IA 형식, **외부 참조 산출물 가이드**
- `references/consistency-rules.md` — 유형 간/내 검증, QA 워커 프롬프트, **외부 참조 검증**

## PM Gate 점검 목록

| Phase | 산출물 | 체크리스트 위치 |
|-------|-------|----------------|
| PLAN | TASK.md, PLAN.md, QA-PLAN.md | TASK.md 요구사항, PLAN.md §3, §4 |
| EXECUTE | QA-EXECUTE.md | - |

---

## Agentic / Semi-Agentic 모드

opal-harness-agentic.md / opal-harness-semi-agentic.md 참조. 본 절은 이 스킬의 차이점만 기술한다.

### 기본 모드 (semi-agentic)

기본 호출(`//opwt {작업}`)은 semi-agentic 모드. PLAN(간략/진단보고)-equivalent까지 사용자 검토, EXECUTE-equivalent 이후 PM 자율, CLOSE 진입은 사용자 승인 필수.

**모드 경계** (이 시점부터 PM 자율):
- PLAN(간략/진단보고) 사용자 확정 행 통과 후 → EXECUTE 작업 행부터 PM 자율
- 분석 모드(진단 보고)는 EXECUTE가 없으므로 semi-agentic이라도 PLAN(진단보고)까지로 종료

### 명시 모드

| 호출 | 모드 |
|------|------|
| `//opwt 작업` | semi-agentic (기본) |
| `//opwt --interactive 작업` | interactive — 모든 단계 사용자 승인 |
| `//opwt --agentic 작업` | agentic — 모든 단계 PM 자율 (CLOSE 진입 제외) |

### 자율 게이트 흐름 (semi-agentic, 작성/수정 모드)

```
TASK → ANALYSIS Gate → PLAN Gate → EXECUTE Gate → QA/CLOSE
사용자   사용자 승인      사용자 승인    PM 자율         사용자 승인 필수
                        (모드 경계)
```

- ANALYSIS/PLAN Gate까지 사용자 승인 필수 (interactive 동작)
- PLAN 사용자 확정 행 통과 후 EXECUTE Gate는 PM 자율 통과
- CLOSE 진입은 사용자 승인 필수 (공통 게이트)
- 각 게이트에서 opal-harness-agentic.md "Gate 루핑 규칙" 적용
- AGENTIC-LOG.md 생성: EXECUTE 등가 첫 행 advance/mark 시점

### CLOSE 진입 게이트 (공통)

semi-agentic / agentic 모두 CLOSE 첫 행 `--auto-pass` 거부 (`agentic_close_gate_requires_user`). 소유자 발화 후 직전 사용자 확인 행 `--owner user` mark 필수.

### AGENTIC-LOG.md 생성 시점

- agentic: TASK 시작 시점
- semi-agentic: EXECUTE-equivalent 첫 행 advance 시점에 PM이 생성

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-03-29 | 초기 작성 |
| v1.1 | 2026-03-28 | Harness 참조 전환으로 슬림화 |
| v1.2 | 2026-03-29 | 컴포넌트 리네이밍 (042) |
| v1.3 | 2026-04-01 | 외부 참조 산출물 지원 — diagnosis.json reference_artifacts[], 워커 프롬프트 확장, 외부 참조 검증 규칙 (062) |
| v1.4 | 2026-04-01 | 외부 API 명세서 프로젝트 특화 선택 타입 추가 — 서드파티 API 기획 산출물화, 내부 API와 구분 (064) |
| v1.5 | 2026-04-01 | IA 산출물 JSON + Mermaid 사이트맵 이중 출력으로 확정 — 변환 스펙, classDef 기준, 분리 규칙 (065) |
| v1.6 | 2026-04-01 | Phase 1/3/4 워커 디스패치에 `[WORKER]` 마커 + PM 컨텍스트 주입 지침 추가 (063) |
| v2.0 | 2026-04-01 | 재설계 — Phase 1-4 → 하네스 표준 단계(TASK/ANALYSIS/PLAN/EXECUTE/QA), TASK 단계 추가, 각 단계 STATE 갱신 명시, 병렬 원칙 적용 (067) |
| v2.1 | 2026-04-01 | 단계별 산출물 문서 추가 — ANALYSIS.md(워커 결과 취합), PLAN.md(진단 근거+배치+QA체크리스트), QA 단계 PLAN.md 갱신 의무 (067) |
| v2.2 | 2026-04-02 | ANALYSIS 게이트 + PLAN QA Gate + EXECUTE 배치별 QA Gate 추가 (072) |
| v2.3 | 2026-04-05 | EXECUTE 후 추가작업 참조 가이드 추가 — 하네스 §3 추가작업 프로세스 (087) |
| v2.4 | 2026-04-06 | PMO 그룹 신설 + 개발 WBS 추가 — 커버 범위 및 TASK 확인 항목 갱신 (089) |
| v2.5 | 2026-04-06 | ANALYSIS PM Gate(자가 체크) 추가 + EXECUTE 배치 게이트 "PM 검토" → "PM Gate" 명확화 (090) |
| v2.6 | 2026-04-07 | TASK/ANALYSIS/PLAN/EXECUTE/QA 각 단계 Gate에 State Gate 참조 추가 (094) |
| v2.7 | 2026-04-07 | State Gate를 PM Gate 전 1개 → 각 Gate 직후로 재배치. EXECUTE 배치 Artifact Gate 제거(opwt 구조상 해당 없음) (097) |
| v2.8 | 2026-04-10 | Artifact Gate 제거 + PM Gate 점검 목록 섹션 추가 + 파이프라인 현황판 이름 변경 (106) |
| v2.9 | 2026-04-11 | PM Gate 점검 목록 — PLAN-equivalent Phase에 TASK.md 요구사항 추가 (108) |
| v3.0 | 2026-04-15 | CLOSE 단계 섹션 신설 + QA 단계에서 DONE.md 생성 분리 + QA Pass 보고 형식 C안 적용 + 단계 목록 CLOSE 추가 (121) |
| v3.1 | 2026-04-24 | citation-rules 트리거 1줄 주입 — SSOT + Trigger 패턴 (130) |
| v3.2 | 2026-05-01 | state-tool 도입 — STATE.md 직접 편집 금지 + `state-tool` 호출 표현 교체 (P-1~P-8 패턴 적용). TASK/ANALYSIS/PLAN/EXECUTE/QA/CLOSE 각 단계 State Gate를 state-tool 명시 호출로 교체. "STATE.md 도메인 치환값" 섹션 리네이밍 + `--rows-from` SSOT 지시. CLOSE 게이트 제약 (§2.16 G-13) + P-6 add-row 가이드 추가 (134) |
| v3.3 | 2026-05-09 11:22 | 3-way 모드 체계 도입 — semi-agentic 기본 채택 + Agentic/Semi-Agentic 모드 절 신규 추가 + Harness 절 3-way 분기 + state init --mode 인수 추가 (140) |
| v3.4 | 2026-05-09 18:30 | 개인 식별자 "캡틴" → "소유자"/"사용자" 치환 — 배포 파일 정체성 누설 정정 (139) |
| v4.0 | 2026-05-24 14:21 | 산출물 체계 v4 — interview 통합(TASK 절 재구성) + PRD 8섹션 표준 + 기능 시나리오 다이어그램 재정의(기존 '순서도' 재정의 — 사용자 수동 재분류) + 화면 흐름도 신설 + Mermaid 시각화 표준 절 신설 + PMO 그룹 및 개발 WBS 제거 (008) |
| v4.1 | 2026-05-24 18:01 | 산출물 저장 경로 누락 보강 — v4 인터뷰 재구성 시 누락된 v3.4 "산출물 저장 경로" 확인 항목을 Round 2 Q6로 복원. Step 1 (d) 저장 경로 자동 감지 추가(PROJECT.md 등록 / 100.기획/ 존재 / 둘 다 없음 3분기). Step 4 TASK.md 양식에 "산출물 저장 경로" 섹션 추가. "산출물 저장 구조" 절에 default v4 7폴더 트리(100.기획/110.PRD~170.기능시나리오) 명시 + 한국어/kebab-case 컨벤션 충돌 안내. (008 추가작업) |
| v4.2 | 2026-06-07 | State Gate 행 제거(guard 이전) + op-task-qa QA Gate 제거 → PM Gate 문서검증 흡수 + gate-pass 4-row 호출 제거 → PM Gate 단일 mark + CLOSE State Gate 행 제거(DONE.md 생성 단일 행) + STATE 행 예시 10행 구조 추가 + TASK 산출물 행 흡수. opds 패턴 정합 (014 Phase 4) |
| v4.3 | 2026-06-11 19:25 | CLOSE 단계에 op-brain-ingest 디스패치 훅 삽입 — DONE.md 생성 직후 brain 존재 시 ingest 워커 디스패치, 부재 시 no-op, CLOSE 비중단. 탐색 경로 2단. STATE 행 수 10 불변 (016) |
| v4.4 | 2026-06-16 | references 비즈니스 용어 우선 주입 — network-guide §7-0 공통 작성 원칙 + consistency-rules §3.1 검증 절 신설, citation-rules §8 참조 (024) |
| v4.5 | 2026-06-24 | CLOSE 단계 op-brain-ingest 디스패치 직전에 "관련 문서 업데이트" 스텝 삽입 — PROJECT.md 레지스트리 + changed_files 종합으로 관련 문서 최신화 후 ingest (없으면 no-op). 후속 항목 번호 재정렬 (042) |
| v4.6 | 2026-07-10 13:12 | note 예시의 소유자 확인 표기를 `{owner_name} 확인:` 형식으로 통일 — identity.md owner_name 재해석 규칙(AGENT.md §정체성 적용)과 정합, 오염 차단 (054) |
| v4.7 | 2026-07-17 | CLOSE 단계에 "회고(개선 루프) 하드스텝" 삽입 — op-brain-ingest 직후·완료보고 직전, 궤적 신호→관찰/분류/기록(improve-tool record --scope local\|fw), 개선후보 0건 시 no-op 비차단(brain-ingest 패턴 답습) (058) |
| v4.8 | 2026-08-13 16:56 | pipeline.json 전환 — references/pipeline.json 신설(10 task-step, SSOT), --rows-from 호출 경로를 SKILL.md에서 pipeline.json으로 교체, 표는 사람 열람용 미러로 명시 (090) |
