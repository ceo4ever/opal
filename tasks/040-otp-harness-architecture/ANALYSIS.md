# ANALYSIS: OPAL Harness Architecture

> 작성일: 2026-03-29
> 입력: TASK.md
> 출력: ANALYSIS.md

## 1. 현재 otp 생태계 분석

### 1.1 otp 오케스트레이터 전수 조사

5개 otp + 2개 creator를 실제 Read하여 비교 분석한 결과.

#### Pipeline 비교


| otp            | 단계 수    | Pipeline                                       |
| -------------- | ------- | ---------------------------------------------- |
| otp-dev        | 4       | TASK → ANALYSIS → PLAN+TEST-SCENARIO → EXECUTE |
| otp-dev-short  | 3       | TASK → PLAN+TEST-SCENARIO → EXECUTE            |
| otp-wf         | 3       | TASK → WIREFRAME → EXECUTE                     |
| otp-write      | 3       | TASK → PLAN → WRITE                            |
| otp-write-tech | 4 Phase | 병렬 분석 → PM 진단 → 병렬 작성 → 정합성 검증                 |


#### Harness 구성 요소별 공통도


| Harness 구성 요소                | 공통도 | 현재 상태                                       |
| ---------------------------- | --- | ------------------------------------------- |
| **TASK** (Context Gathering) | 95% | dtp-task 직접 수행, 동일 포맷. 도메인별 추가 필드만 다름       |
| **Gates** (체크포인트)            | 90% | "확인/피드백/중단" 3단계 응답 패턴 거의 동일                 |
| **Guards** (제약)              | 90% | 구현 금지 원칙, 커밋 규칙 — 각 otp에 복붙                 |
| **State** (STATE.md)         | 85% | 구조 동일, 모드명/산출물 목록만 다름                       |
| **Observability** (보고/메모리)   | 90% | 보고 형식, 메모리 동기화 거의 동일                        |
| **ANALYSIS** (조사)            | 80% | 방법만 다름 (코드=Glob/Grep, 문서=WebSearch, WF=이미지) |
| **PLAN** (설계)                | 70% | "조사→설계→목차" 흐름 유사, 산출물 구조가 다름                |
| **EXECUTE** (산출)             | 20% | 여기서 완전히 갈라짐 — 코드/문서/UI/기획 세트                |
| **VERIFY** (검증)              | 60% | dtp-qa/dtp-test 공용이지만, 검증 기준이 도메인별로 다름      |


### 1.2 복제 패턴 정량 분석

각 otp SKILL.md에서 **도메인 비종속 코드(하네스)**와 **도메인 종속 코드(프로파일)**의 비율.


| otp            | 총 줄 수 | 하네스 (복제)                                          | 프로파일 (고유)                              | 복제율 |
| -------------- | ----- | ------------------------------------------------- | -------------------------------------- | --- |
| otp-dev        | 275   | ~180 (Gates, Guards, State, Observability, 탐색 경로) | ~95 (워커 디스패치, 모델 지정, FE/BE 병렬)         | 65% |
| otp-dev-short  | 235   | ~160                                              | ~75 (에스컬레이션, 통합 PLAN)                  | 68% |
| otp-wf         | ~200  | ~130                                              | ~70 (WIREFRAME 단계, 프로토/프로덕션 모드)        | 65% |
| otp-write      | 162   | ~110                                              | ~52 (소스 조사 분기, 섹션별 작성, 출력 형식)          | 68% |
| otp-write-tech | 132   | ~70                                               | ~62 (4 Phase, diagnosis.json, 네트워크 상태) | 53% |


**평균 복제율: ~64%** — 각 otp의 약 2/3가 동일한 하네스 코드.

### 1.3 039에서 발견된 Harness 원형 패턴

otp-write-tech는 다른 otp와 독립적으로 설계되었지만, 결과적으로 **동일한 Harness 패턴**을 재발명했다:


| 039 패턴              | Harness 대응         | 비고                                 |
| ------------------- | ------------------ | ---------------------------------- |
| 4 Phase Pipeline    | Pipeline Layer     | ANALYSIS → PLAN → EXECUTE → VERIFY |
| PM 직접 수행 (교차 검토/진단) | Pipeline 내 PM Gate | 판단이 필요한 단계는 직접, 작업은 워커             |
| 워커 병렬 디스패치          | Execute Strategy   | 독립=병렬, 의존=배치 순차                    |
| diagnosis.json      | Pipeline State     | 단계 간 구조화된 데이터 전달                   |
| references/ 분리      | Domain Profile     | 도메인 전문 지식을 외부 참조로 분리               |
| 3가지 모드 (작성/수정/분석)   | Mode Selection     | Full/Short의 확장                     |
| 게이트 체크포인트           | Gate Layer         | Phase/배치 완료 시 사용자 확인               |
| STATE.md 네트워크 확장    | State Layer        | 도메인별 확장 가능한 State 구조               |


### 1.4 현재 dtp 레이어 분석

otp가 호출하는 dtp(단계 스킬)와 에이전트:


| dtp 스킬            | 호출하는 otp                   | 역할        | Harness 레이어           |
| ----------------- | -------------------------- | --------- | --------------------- |
| dtp-task          | dev, short, wf, write      | 요구사항 구조화  | Context Gathering     |
| dtp-analysis      | dev                        | 코드베이스 분석  | Analysis (dev 전용)     |
| dtp-plan          | dev, short                 | 구현 계획     | Planning (dev 전용)     |
| dtp-test-scenario | dev, short                 | 테스트 시나리오  | Planning (dev 전용)     |
| dtp-execute       | dev, short, wf             | 코드 작성     | Execution (dev/wf 전용) |
| dtp-qa            | dev, short, wf, write-tech | 산출물 검증    | Verification (공용)     |
| dtp-test          | dev, short                 | 코드 테스트    | Verification (dev 전용) |
| dtp-wireframe     | wf                         | 와이어프레임 생성 | Execution (wf 전용)     |
| dtp-doc-write     | (없음, write가 직접)            | 문서 작성     | Execution (write 전용)  |


## 2. Harness Architecture 구조 분석

### 2.1 추출 가능한 Harness 공통 레이어

현재 otp들에서 **추출하여 공통화할 수 있는 것**:

```
Harness Layer (공통 인프라)
├── Pipeline Engine
│   ├── Mode Selection — Full(4단계) / Short(3단계) / Custom
│   ├── Stage Sequencing — 단계별 순차 실행 + 조건 스킵
│   └── Stage Transition — 단계 간 데이터 전달 (산출물 경로, 요약)
│
├── Gate Engine
│   ├── User Gate — 승인/피드백/중단 3단계 응답 처리
│   ├── QA Gate — dtp-qa 워커 호출 + 결과 판정
│   └── PM Gate — .opal/AGENT.md 기반 PM 검토 (있으면)
│
├── Guard Engine
│   ├── Pre-approval Guard — 승인 전 산출물만 허용, 소스코드 금지
│   ├── Commit Guard — 사용자 명시 요청 시에만 커밋
│   └── Scope Guard — PLAN 밖 파일 변경 금지
│
├── State Engine
│   ├── STATE.md — 현재 단계, 산출물 상태, 의사결정 로그
│   ├── Session Restore — STATE.md Read로 재개 지점 파악
│   └── Memory Sync — .opal/MEMORY.md 작업 히스토리 갱신
│
└── Observability
    ├── Report Format — 간단 보고 / 상세 보고
    ├── Gate Logging — 각 Gate 통과 기록
    └── Error Handling — 블로커 감지 → 중단 → 사용자 보고
```

### 2.2 Domain Profile 구조 분석

각 otp에서 **도메인 고유**한 부분만 추출:


| Domain         | ANALYSIS 방식             | PLAN 산출물                         | EXECUTE 방식                         | VERIFY 방식                       | 고유 도구                            |
| -------------- | ----------------------- | -------------------------------- | ---------------------------------- | ------------------------------- | -------------------------------- |
| **dev**        | Glob/Grep/Read 코드 분석    | PLAN.md (실행 체크리스트, 복잡도, 실행 아키텍처) | dtp-execute 워커 (sonnet) + FE/BE 병렬 | dtp-test + dtp-qa               | execution-plan.json              |
| **write**      | WebSearch + 코드 분석 + 인터뷰 | PLAN.md (목차 + 섹션별 개요)            | 직접 섹션별 작성                          | dtp-qa (선택)                     | opal-doc-standard                |
| **wf**         | 이미지 분석 + 기존 UI 분석       | wireframe.md                     | wireframe-builder + ui-designer    | dtp-qa (WIREFRAME + EXECUTE-UI) | shadcn MCP                       |
| **write-tech** | 워커 병렬 문서 분석             | diagnosis.json (교차 진단)           | 워커 병렬 문서 작성 (배치)                   | QA 워커 정합성 검증                    | network-guide, consistency-rules |
| **skill**      | 기존 스킬 구조 분석             | SKILL.md 초안 설계                   | skill-creator 위임 + OPAL 후처리        | 완료 체크리스트                        | skill-creator                    |


### 2.3 Domain Profile 스키마 초안

```yaml
# domain-profile.yaml (개념적 스키마)
domain: dev | write | wf | write-tech | skill | ...
display_name: "코드 개발"
triggers: ["코드", "개발", "구현", "기능 추가"]

modes:
  full: [TASK, ANALYSIS, PLAN, EXECUTE, VERIFY]
  short: [TASK, PLAN, EXECUTE]
  # write-tech는 custom mode도 가능

analysis:
  method: code | web | document | interview | parallel-workers
  worker_model: haiku | sonnet | opus
  artifacts: [ANALYSIS.md]

plan:
  method: implementation-plan | document-outline | diagnosis
  artifacts: [PLAN.md | diagnosis.json]
  worker_model: opus

execute:
  method: worker-dispatch | direct | parallel-batch
  worker: dtp-execute | dtp-wireframe | direct
  worker_model: sonnet
  parallel: false | fe-be | batch-based

verify:
  method: test+qa | qa-only | consistency-check
  workers: [dtp-test, dtp-qa]

tools:
  skills: [references/..., community-skills/...]
  mcps: [context7, shadcn, ...]
  standards: [opal-doc-standard]
```

## 3. 설계 옵션 비교

### Option A: 단일 범용 otp (모놀리식)

```
otp (300~400줄)
  ├── Harness 공통 코드 (inline)
  ├── Domain Profile 감지 로직 (inline)
  └── 도메인별 분기 (if/switch 스타일)
```


| 장점      | 단점                             |
| ------- | ------------------------------ |
| 하나의 진입점 | 스킬이 비대 (400줄+, LLM 후반부 무시 리스크) |
| 중복 제거   | 새 도메인 추가 시 본체 수정 필요            |
|         | 도메인 전문성 표현이 어려움                |


### Option B: 하네스 참조 문서 + 도메인별 otp (현재+공통화)

```
references/opal-harness.md (참조 문서 — Gates, Guards, State, Observability 규칙)
  ↑ Read
otp-dev, otp-write, otp-wf, otp-write-tech (각각 독립, 하네스 규칙 참조)
```


| 장점                  | 단점                           |
| ------------------- | ---------------------------- |
| 기존 구조 유지, 마이그레이션 최소 | 복제는 줄지만 각 otp가 하네스를 "해석"해야 함 |
| 도메인별 최적화 유지         | 하네스 변경 시 모든 otp 영향           |
| 각 스킬 200줄 이내 유지     | 새 도메인마다 otp 추가는 여전           |


### Option C: 디스패처 otp + 도메인 프로파일 (하이브리드)

```
otp/SKILL.md (디스패처 — TASK 직접 수행 + 도메인 감지 + 해당 otp-{domain} 호출)
  ├── otp-dev/SKILL.md (dev 프로파일, 하네스 참조)
  ├── otp-write/SKILL.md (write 프로파일, 하네스 참조)
  └── ...
references/opal-harness.md (공통 규칙)
```


| 장점                              | 단점                         |
| ------------------------------- | -------------------------- |
| `//otp`로 범용 진입 가능               | 디스패처 + 도메인 otp 2단 구조 (복잡도) |
| 기존 `//otpd`, `//otpw` 직접 호출도 유지 | 도메인 감지 오류 가능               |
| 새 도메인 = 프로파일 추가만                |                            |


### Option D: 하네스 엔진 참조 + 도메인 프로파일 참조 (완전 분리)

```
references/opal-harness.md (Harness 엔진 — Pipeline, Gates, Guards, State, Observability)
references/profiles/dev.md (dev 프로파일 — ANALYSIS/PLAN/EXECUTE/VERIFY 방식)
references/profiles/write.md
references/profiles/wf.md
references/profiles/write-tech.md

otp/SKILL.md (범용 오케스트레이터 — harness.md Read + 도메인 감지 + profile Read + 실행)
```


| 장점                           | 단점                              |
| ---------------------------- | ------------------------------- |
| 완전한 분리 — 하네스 변경이 otp 하나에만 영향 | otp가 2개 문서를 Read (컨텍스트 소모)      |
| 새 도메인 = profiles/ 추가만        | Profile 문서의 표현력 한계 (LLM이 잘 따를지) |
| otp 하나로 모든 도메인 커버            | 도메인별 세밀한 최적화 어려움                |


## 4. 핵심 발견 사항

1. **평균 64% 복제** — 현재 otp의 2/3가 하네스 코드. 공통화의 실효성이 높다.
2. **039가 Harness를 재발명** — otp-write-tech는 독립 설계했지만, diagnosis.json(Pipeline State), PM/워커 분리(Gate 패턴), references/ 분리(Domain Profile)를 자연스럽게 만들어냈다. 이것이 Harness가 필요하다는 강한 신호.
3. **EXECUTE에서 완전히 갈라짐** — 공통화 가능한 건 TASK(95%), Gates(90%), Guards(90%), State(85%). EXECUTE는 20% — 여기가 Domain Profile의 핵심.
4. **VERIFY는 중간** — dtp-qa는 공용이지만 검증 기준(코드 vs 문서 vs 정합성)이 다르다. Harness가 "검증 프레임"만 제공하고, 검증 기준은 Profile이 정의하는 구조가 적합.
5. **LLM 스킬 크기 제약** — 하나의 SKILL.md가 300줄을 넘으면 후반부 지시를 무시하는 경향. Option A(모놀리식)는 비현실적. Option B 또는 D가 유력.
6. **마이그레이션 비용** — Option B는 최소(참조 문서 추가만), Option D는 전면 재설계. Option C는 중간.

## 5. 제약/리스크


| 항목            | 설명                                             | 심각도   |
| ------------- | ---------------------------------------------- | ----- |
| LLM 컨텍스트 소모   | 하네스 + 프로파일 + 도메인 references를 모두 Read하면 컨텍스트 과다 | 높음    |
| 도메인 감지 정확도    | 사용자 요청에서 도메인을 잘못 판별하면 엉뚱한 프로파일 적용              | 중간    |
| 기존 otp 마이그레이션 | 5개 otp를 새 구조로 전환하는 비용                          | 중간~높음 |
| Harness 문서 크기 | 공통 규칙을 한 문서에 넣으면 200줄+ — 분할 필요 가능              | 중간    |
| 기존 사용자 습관     | `//otpd`, `//otpw` 등 기존 약어에 익숙 — 하위 호환 필수      | 낮음    |


## 6. 기술 컨텍스트

### 참조한 외부 자료


| 자료                                                                                                               | 핵심 인사이트                                                   |
| ---------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| [OpenAI Harness Engineering](https://openai.com/index/harness-engineering/)                                      | 에이전트가 아니라 하네스가 어렵다. Context + Constraints + Feedback + GC |
| [Martin Fowler Harness Engineering](https://martinfowler.com/articles/exploring-gen-ai/harness-engineering.html) | 결정론적 + LLM 기반 접근 혼합                                       |
| [Phil Schmid Agent Harness 2026](https://www.philschmid.de/agent-harness-2026)                                   | 하네스의 6대 구성 요소                                             |
| [Inngest: Harness Not Framework](https://www.inngest.com/blog/your-agent-needs-a-harness-not-a-framework)        | 프레임워크 vs 하네스의 차이                                          |
| [The Harness Problem](https://blog.can.ac/2026/02/12/the-harness-problem/)                                       | 모델이 아닌 하네스를 바꿨을 때 15개 LLM 모두 성능 향상                        |


### 기술 스택


| 영역     | 기술                               |
| ------ | -------------------------------- |
| 문서 포맷  | Markdown (SKILL.md, references/) |
| 프레임워크  | OPAL v1.0+                       |
| 하네스 참조 | opal-doc-standard.md (기존 성공 사례)  |


---

## 7. 아키텍처 결정: Option B 채택

캡틴과 검토 후 **Option B (하네스 참조 문서 + 도메인별 otp 유지)**로 결정.

### 결정 근거

1. **검증된 패턴**: opal-doc-standard.md가 이미 동일 방식(참조 문서 + 여러 스킬이 Read)으로 성공 작동 중
2. **최소 마이그레이션**: 참조 문서 1개 추가 + 기존 otp에서 복붙 코드를 "참조"로 교체
3. **LLM 현실성**: 참조 1개만 Read하면 됨 (Option D는 2개 Read — 컨텍스트 과다 리스크)
4. **단계적 확장**: 나중에 필요하면 B → C(디스패처 추가)로 자연스럽게 확장 가능

### opal-harness.md 구성 내용

현재 5개 otp에서 **65% 복붙**되고 있는 공통 코드를 추출한 참조 문서:

```
references/opal-harness.md (~150줄)

## 1. Pipeline 프로세스
  - Full 모드: TASK → ANALYSIS → PLAN → EXECUTE → VERIFY
  - Short 모드: TASK → PLAN → EXECUTE → VERIFY
  - 단계 전환 규칙 (이전 산출물 → 다음 단계 입력)

## 2. Gates (체크포인트)
  - 단계 완료 시 사용자 보고 + 승인 대기
  - 응답 패턴: "확인/다음/승인" → 진행, 피드백 → 수정, "중단/보류" → 대기
  - QA Gate: dtp-qa 호출 패턴
  - PM Gate: .opal/AGENT.md 존재 시 PM 검토

## 3. Guards (제약)
  - 구현 금지 원칙 (승인 전 코드 작성 금지)
  - 커밋 규칙 (사용자 명시 요청 시에만)
  - Git 사전 점검

## 4. State (상태 관리)
  - STATE.md 템플릿 (현재 상태, 산출물, 의사결정 로그, 블로커)
  - 세션 복원 (STATE.md Read로 재개)
  - 프로젝트 메모리 동기화 (.opal/MEMORY.md 히스토리 갱신)

## 5. Observability (관측)
  - 보고 형식 (간단 보고 / 상세 보고)
  - 스킬 탐색 경로 규칙

## 6. TASK 공통 프로세스
  - dtp-task 직접 수행 패턴
  - STATE.md 초기 생성
```

### references/ 배치

```
~/.opal/references/
  ├── opal-doc-standard.md  ← 문서를 "어떤 형식으로" 쓸지
  ├── opal-harness.md       ← 작업을 "어떤 프로세스로" 할지 (NEW)
  ├── skills.md             ← 스킬 레지스트리
  ├── agents.md             ← 에이전트 레지스트리
  ├── mcps.md               ← MCP 레지스트리
  └── skill-guide.md        ← 스킬 퀵 가이드
```

### Option B 적용 예시: otp-dev 슬림화

**Before (275줄)**:

```markdown
# otp-dev/SKILL.md

## 구현 금지 원칙 (최우선 규칙)           ← 하네스 (복붙)
사용자가 명시적으로 승인할 때까지...

## Git 사전 점검                        ← 하네스 (복붙)
태스크 시작 전 git status...

## STEP 1: TASK                        ← 하네스 (복붙)
dtp-task/SKILL.md를 Read...
STATE.md를 생성...

## STEP 2: ANALYSIS                    ← 도메인 고유
워커 디스패치 (haiku)...
dtp-qa 워커 호출 → PM 검토 게이트...

## STEP 3: PLAN + TEST-SCENARIO        ← 도메인 고유
워커 디스패치 (opus)...

## STEP 4: EXECUTE                     ← 도메인 고유
워커 디스패치 (sonnet)...
execution-plan.json 기반 FE/BE 병렬...

### 커밋 규칙                            ← 하네스 (복붙)
커밋은 사용자가 명시적으로 요청할 때만...

## STATE.md 관리                        ← 하네스 (복붙, 템플릿 전체)
## 프로젝트 메모리 동기화                  ← 하네스 (복붙)
## 스킬 탐색 경로                        ← 하네스 (복붙)
## 게이트 체크포인트                      ← 하네스 (복붙, 응답 패턴 테이블)
```

**After (~100줄)**:

```markdown
# otp-dev/SKILL.md

## Harness
opal-harness.md 참조: `~/.opal/references/opal-harness.md`
- 모드: Full (TASK → ANALYSIS → PLAN → EXECUTE → VERIFY)

## STEP 1: TASK
opal-harness.md "TASK 공통 프로세스" 참조.

## STEP 2: ANALYSIS (도메인 고유)
워커 디스패치 (haiku): dtp-analysis 스킬
QA Gate + PM Gate

## STEP 3: PLAN + TEST-SCENARIO (도메인 고유)
워커 디스패치 (opus): dtp-plan 스킬
TEST-SCENARIO 스킵 조건: 문서 전용 작업 시
QA Gate + PM Gate

## STEP 4: EXECUTE (도메인 고유)
워커 디스패치 (sonnet): dtp-execute 스킬
execution-plan.json 기반 FE/BE 병렬
EXECUTE 완료 후: dtp-test → DONE.md → 보고

## 변경이력
```

### Option B 적용 예시: otp-write 슬림화

**Before (162줄)** → **After (~55줄)**:

```markdown
# otp-write/SKILL.md

## Harness
opal-harness.md 참조: `~/.opal/references/opal-harness.md`
- 모드: Short (TASK → PLAN → EXECUTE)

## STEP 1: TASK
opal-harness.md "TASK 공통 프로세스" 참조.
추가 확인: 문서 유형, 대상 독자, 범위, 출력 형식

## STEP 2: PLAN (도메인 고유)
소스 조사 (유형별 분기):
| 문서 유형 | 소스 조사 방식 |
| 기술 산출물 | Glob/Grep/Read 코드 분석 |
| 보고서 | 코드 분석 + WebSearch |
| 가이드 | 코드 분석 + 기존 문서 참조 |
| 기획/제안 | WebSearch + interview |
opal-doc-standard 참조하여 목차/구조 설계
QA Gate (선택)

## STEP 3: WRITE (도메인 고유)
섹션별 순차 작성
출력 형식: .md 기본, .docx/.pdf는 커뮤니티 스킬 연동
DONE.md 생성

## 변경이력
```

### 슬림화 효과 예측

| otp | Before | After (예상) | 감소율 |
|-----|--------|-------------|--------|
| otp-dev | 275줄 | ~100줄 | -64% |
| otp-dev-short | 235줄 | ~85줄 | -64% |
| otp-wf | ~200줄 | ~75줄 | -63% |
| otp-write | 162줄 | ~55줄 | -66% |
| otp-write-tech | 132줄 | ~65줄 | -51% |
| **opal-harness.md** | (신규) | ~150줄 | — |
| **합계** | 1,004줄 | ~530줄 | **-47%** |

### 단계적 확장 로드맵

```
Phase 1 (040 태스크): Option B 구현
  → opal-harness.md 생성
  → 기존 5개 otp 슬림화 (복붙 → 참조)
  → 검증: 기존 기능 그대로 동작 확인

Phase 2 (향후 필요 시): B → C 확장
  → //otp 디스패처 추가 (얇은 진입점, 도메인 감지)
  → 기존 //otpd, //otpw 직접 호출도 유지

Phase 3 (훨씬 나중): C → D 진화 (필요 시에만)
  → Domain Profile을 별도 파일로 분리
  → otp 하나로 완전 통합
```
