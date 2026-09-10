# OPAL Framework Evaluation Loop 설계 제안서

> 상태: 제안
> 작성: 알투(PM)
> 작성일: 2026-09-10
> 목적: 스킬·에이전트·하네스 변경의 효과와 회귀를 반복 검증하고, 기여하지 않는 중복 구성요소를 안전하게 제거할 수 있는 자체 고도화 체계 제안
> 범위: 방향과 핵심 계약을 정하는 제안서. 구현 계획(PLAN)과 코드 변경은 포함하지 않는다.

---

## 1. 제안 요약

OPAL에는 태스크 단위 테스트, 목표-커버 게이트, 독립 Evaluator, 회귀 중단, 개선 후보 기록 체계가 이미 있다. 그러나 이 자산들은 주로 “이번 태스크가 요구사항을 충족했는가”를 판정한다. 다음 질문을 반복 가능하게 답하는 프레임워크 평가 계층은 아직 없다.

- 스킬을 고친 뒤 실제 수행 품질이 좋아졌는가?
- 하네스 단계를 추가한 효과가 비용과 복잡도를 정당화하는가?
- 같은 변경이 Claude·Codex·Gemini에서 모두 유효한가?
- 구성요소 하나를 제거해도 품질이 유지되는가?
- 평가 결과가 모델의 우연한 출력이나 실행 환경 차이가 아니라 실제 개선인가?

이 제안은 가칭 **OPAL Framework Evaluation Loop**를 신설한다. 내부 명칭은 **OPAL Forge**를 사용한다.

```text
실제 실패·개선 후보
  → 고정 평가 과제 등록
  → 기준 버전과 후보 버전 격리 실행
  → 결과·궤적·비용 채점
  → 비교·제거·변이 실험
  → 사용자 승격 결정
  → 프레임워크 반영
  → 새 실패를 영구 회귀 과제로 편입
```

핵심은 새 테스트 러너를 다시 만드는 것이 아니다. 기존 `opal-agent`, `test-tool`, `opal-evaluator-agent`, `worktree-tool`, `improve-tool`을 재사용하고, 그 위에 **평가 과제군·반복 실행·버전 비교·기여도 판정**을 추가한다.

---

## 2. 문제 정의

### 2.1 OPAL이 검증하기 어려운 이유

OPAL의 산출물은 일반 라이브러리와 다르다. 스킬·에이전트·하네스는 Markdown과 YAML로 작성되지만 실제 동작은 모델, 플랫폼, 도구 가용성, 프로젝트 상태, 대화 이력에 따라 달라진다.

따라서 다음과 같은 특성이 있다.

| 특성 | 일반 코드 테스트만으로 부족한 이유 |
|---|---|
| 비결정성 | 같은 입력도 실행할 때마다 결과와 도구 경로가 달라질 수 있음 |
| 장기 실행 | 여러 단계와 워커를 거치므로 최종 산출물만 보면 실패 지점을 알기 어려움 |
| 환경 의존 | 모델·플랫폼·CPU·RAM·timeout·도구 상태가 결과에 영향을 줌 |
| 주관적 품질 | 문서 가독성·설계 적합성·과도한 구현 등은 단순 문자열 비교로 판정 불가 |
| 구성요소 상호작용 | 스킬 하나의 효과가 에이전트·하네스·모델 조합에 따라 달라짐 |
| 자기검증 위험 | 변경을 만든 주체가 같은 기준으로 평가하면 결함을 놓칠 수 있음 |

“시뮬레이션을 돌렸다”는 사실만으로는 검증이 아니다. 과제의 최종 상태를 판정하는 verifier와 변경 전후를 비교할 기준선이 없으면 시뮬레이션은 재현 가능한 증거가 되지 못한다.

### 2.2 현행 자산

| 자산 | 현재 역할 | 근거 |
|---|---|---|
| `test-tool` | lint·typecheck·unit·integration 단발 실행과 테스트 시나리오 상태 관리 | `opal/tools/test-tool/README.md:7-14` |
| `scenario-gate` | 목표·요구·기능·리스크 커버와 독립 평가자 판정 결합 | `opal/core/references/harness/scenario-gate.md:16-27`, `:67-99` |
| `opal-evaluator-agent` | 생성자와 분리된 읽기 전용 루브릭 판정 | `opal/agents/opal-evaluator-agent/AGENT.md:16-18`, `:59-69` |
| `opal-improve` | 태스크 궤적과 사용자 피드백에서 개선 후보 발견·분류·기록 | `opal/skills/opal-improve/SKILL.md:34-43`, `:84-102` |
| `improve-tool` | 개선 후보를 로컬 메모리 또는 FW 인박스에 결정론적으로 기록 | `opal/tools/improve-tool/improve_tool.py` `@header` |
| `worktree-tool` | 후보 변경을 기본 작업본과 분리하는 작업 공간 제공 | `docs/PROJECT.md` §주요 컴포넌트, `opal-harness.md` §워크스페이스 축 |
| Project Loop | 명세 Evaluator와 동작 test-agent를 분리한 2원 검증 | `opal/skills/opal-pilot-project-loop/references/verification.md` §검증 2원화 |

### 2.3 현행의 빈칸

| 필요한 질문 | 현행 판정 가능 여부 | 빈칸 |
|---|:---:|---|
| 개별 태스크의 테스트가 통과했는가 | 가능 | — |
| 목표를 검증하는 시나리오가 존재하는가 | 가능 | — |
| 개선 전보다 개선 후가 나은가 | 불가 | 기준/후보 paired run 부재 |
| 반복 실행 결과가 안정적인가 | 불가 | trial·분산·신뢰구간 부재 |
| 어느 구성요소가 실제 성능에 기여하는가 | 불가 | ablation 실행·비교 부재 |
| 제거 후 다른 기능이 회귀하지 않는가 | 부분 가능 | 프레임워크 전역 holdout suite 부재 |
| 플랫폼 간 효과가 이전되는가 | 불가 | 동일 과제 cross-platform matrix 부재 |
| 왜 성공하거나 실패했는가 | 부분 가능 | 공통 trace 계약과 trace grader 부재 |
| 개선 후보가 실증을 거쳐 배포됐는가 | 불가 | `fw-inbox`와 평가·승격 상태 연결 부재 |

### 2.4 핵심 판단

OPAL에 필요한 것은 기존 테스트를 대체하는 또 하나의 테스트 스킬이 아니다. 기존 테스트와 평가자를 사용해 **프레임워크 버전 간 차이를 측정하는 실험 하네스**다.

---

## 3. 외부 사례 조사 결과

### 3.1 Agent Eval의 공통 구조

Anthropic은 에이전트 평가를 task·trial·grader·transcript·outcome·evaluation harness로 나눈다. 같은 과제를 여러 번 실행하고, 최종 답변보다 실제 환경의 최종 상태를 우선 확인하며, 코드 기반·모델 기반·사람 평가를 겹쳐 사용하는 접근이다. 초기 과제군은 실제 실패에서 뽑은 20~50개로도 시작할 수 있다고 제안한다.

출처: [Anthropic — Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)

### 3.2 스킬의 효과는 paired evaluation으로 측정

SkillsBench는 같은 과제를 스킬이 없는 조건과 curated skill이 있는 조건으로 짝지어 실행한다. 현재 공개 결과에서는 curated skill이 평균 성공률을 높였지만 효과는 조합별로 달랐고, 최대 3개 모듈로 집중된 스킬이 더 크고 포괄적인 번들보다 좋은 결과를 냈다. 스킬의 존재가 항상 이익이라는 가정 대신, 같은 환경에서 **있음/없음의 차이**를 측정해야 한다는 근거다.

출처: [SkillsBench 논문](https://arxiv.org/abs/2602.12670), [SkillsBench 1.1](https://www.skillsbench.ai/blogs/skillsbench-1-1)

### 3.3 스킬 개선에는 기준선·분산·블라인드 비교가 필요

Anthropic의 공식 Skill Creator는 스킬이 있는 실행과 기준선 실행을 함께 만들고, 성공률·시간·토큰의 평균과 표준편차 및 delta를 집계한다. 고급 비교에서는 두 결과의 출처를 숨긴 블라인드 A/B 판정을 사용하며, trigger description 최적화는 학습용과 holdout을 분리해 과적합을 줄인다.

출처: [Anthropic Skills — Skill Creator](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md)

### 3.4 에이전트 평가는 격리 환경과 결과 verifier가 중심

Inspect AI는 dataset·agent·tool·scorer를 조합하고 Docker 등의 sandbox에서 에이전트를 실행하며, Codex CLI·Claude Code·Gemini CLI 같은 외부 에이전트 연결과 trace 분석을 지원한다. Harbor도 task·instruction·environment·tests·solution 구조로 컨테이너 과제를 정의하고 여러 코딩 에이전트를 동일 환경에서 실행한다.

출처: [Inspect AI](https://inspect.aisi.org.uk/), [Inspect Sandboxing](https://inspect.aisi.org.uk/sandboxing.html), [Harbor](https://github.com/harbor-framework/harbor), [Harbor Task Structure](https://www.harborframework.com/docs/tasks)

### 3.5 하네스 단순화는 한 번에 하나씩 제거하며 검증

Anthropic의 장기 실행 하네스 실험은 복잡한 하네스에서 어떤 요소가 실제로 필요한지 알기 위해 구성요소를 한 번에 하나씩 제거하고 최종 결과의 변화를 비교했다. 모델이 발전하면 과거에 필요했던 scaffolding이 불필요해질 수 있으므로 구성요소의 기여도를 주기적으로 다시 측정해야 한다.

출처: [Anthropic — Harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps)

### 3.6 실행 환경은 실험 변수다

Anthropic은 agentic coding eval에서 CPU·RAM 등 인프라 차이만으로 성공률이 최대 6%p 변한 사례를 보고했다. 모델·과제·프롬프트가 같아도 자원 상한과 오류율이 다르면 같은 실험이 아니다. 작은 점수 차이는 실행 환경과 반복 편차를 고정하지 않으면 개선 근거가 될 수 없다.

출처: [Anthropic — Quantifying infrastructure noise in agentic coding evals](https://www.anthropic.com/engineering/infrastructure-noise)

### 3.7 자기 개선은 후보 아카이브와 경험적 검증으로 통제

Darwin Gödel Machine은 하나의 최신 에이전트를 계속 덮어쓰지 않고 여러 후보 버전을 아카이브에 보존한 뒤 코딩 벤치마크로 경험적 성능을 검증한다. OPAL에는 자율 자기수정보다, 후보를 격리하고 검증된 변경만 사용자 승인으로 승격시키는 구조가 적합하다.

출처: [Darwin Gödel Machine](https://arxiv.org/abs/2505.22954)

### 3.8 특정 서비스 종속은 피한다

OpenAI의 trace grading은 에이전트의 전체 도구 호출과 의사결정 흐름을 구조화해 회귀와 개선 원인을 찾는 방법으로 참고할 가치가 있다. 다만 OpenAI Hosted Evals는 2026년 10월 31일 읽기 전용 전환과 11월 30일 종료가 예정돼 있으므로 OPAL의 핵심 실행 계층으로 채택하지 않는다.

출처: [OpenAI Trace grading](https://developers.openai.com/api/docs/guides/trace-grading), [OpenAI Evals 종료 일정](https://developers.openai.com/api/docs/guides/evals)

---

## 4. 설계 원칙

### 4.1 결과 상태가 최종 근거

에이전트의 “완료했다”는 답변이 아니라 verifier가 확인한 파일, 테스트, API, 데이터베이스, 브라우저 상태를 결과로 사용한다.

### 4.2 비교 없는 점수는 개선 근거가 아님

후보 버전은 같은 과제·모델·플랫폼·자원 조건의 기준 버전과 짝지어 실행한다. 절대 점수보다 기준 대비 delta를 우선 본다.

### 4.3 결과와 궤적을 분리해 채점

- **Outcome**: 최종 상태가 목표를 충족했는가
- **Trace**: 어떤 스킬과 도구를 읽고 어떤 경로로 결과에 도달했는가

결과가 맞아도 금지된 우회, 불필요한 반복, 과도한 도구 호출이 있으면 별도 품질 문제로 기록한다. 반대로 권장 경로와 달라도 결과가 정확하고 정책 위반이 없다면 무조건 실패로 처리하지 않는다.

### 4.4 결정론 판정을 우선

파일·스키마·테스트·상태·보안·승인 위반은 코드 기반 verifier가 판정한다. 가독성·설계 품질·과잉 구현·응답 적합성처럼 결정론 판정이 어려운 항목만 독립 LLM judge와 사용자 검토로 넘긴다.

### 4.5 평가자와 생성자를 분리

후보를 만든 에이전트가 자기 결과의 최종 pass를 선언하지 않는다. 결정론 verifier, 독립 Evaluator, 사용자 승격 게이트를 분리한다.

### 4.6 평가 과제와 verifier도 검증 대상

약한 assertion은 거짓 초록불을 만든다. 의도적으로 결함을 넣은 변이본을 verifier가 잡는지 확인하고, 잡지 못한 변이는 평가 과제의 결함으로 처리한다.

### 4.7 후보 버전을 덮어쓰지 않음

기준 버전과 후보 버전을 worktree 또는 container로 격리한다. 후보는 실험 결과와 함께 보존하고, 사용자 승인 전 프레임워크 소스나 배포본으로 승격하지 않는다.

### 4.8 외부 하네스는 어댑터로 격리

평가 과제와 결과 스키마는 OPAL이 소유한다. Inspect·Harbor·BenchFlow 같은 외부 실행기는 교체 가능한 adapter로만 연결한다.

---

## 5. 제안 컴포넌트

### 5.1 `opal-framework-eval` 스킬

가칭 별칭은 `opev`다. 최종 별칭은 구현 계획에서 스킬 레지스트리 충돌 검사를 거쳐 확정한다.

역할은 평가 목적을 과제군과 실험 조건으로 변환하고, 실행 결과를 해석해 사용자에게 승격·반려·추가 검증안을 제시하는 것이다.

```text
DEFINE → MATERIALIZE → RUN → GRADE → COMPARE → DECIDE
```

| 단계 | 역할 | 산출 |
|---|---|---|
| DEFINE | 변경 가설·영향 범위·성공 기준·비목표 확정 | experiment spec |
| MATERIALIZE | 과제·fixture·verifier·실행 환경 준비 | eval suite |
| RUN | 기준/후보/제거 조건 반복 실행 | trial traces·outcomes |
| GRADE | 결정론·루브릭·사람 판정 | grader results |
| COMPARE | delta·분산·회귀·비용 분석 | comparison report |
| DECIDE | 승격·반려·추가 실험 제안 | 사용자 decision gate |

이 스킬은 결과를 직접 조작하지 않는다. `eval-tool` 출력과 독립 Evaluator 결과가 없으면 개선을 확정하지 않는다.

### 5.2 `eval-tool`

평가 과제, trial, 점수, 비교 결과의 결정론적 집행기다. 모델을 직접 판단하지 않고 확정된 실험 조건을 실행하고 결과를 집계한다.

| 제안 명령 | 역할 |
|---|---|
| `suite-check` | 과제 구조·verifier·oracle·resource policy 검사 |
| `run` | 기준/후보 조건을 격리 환경에서 반복 실행 |
| `score` | 기존 run에 결정론 scorer 적용 또는 재채점 |
| `compare` | paired delta·평균·편차·회귀·비용 집계 |
| `ablate` | 지정 구성요소 하나를 비활성화한 조건 생성·실행 |
| `mutate` | 규칙·과제·fixture 변이본 실행과 verifier 탐지율 계산 |
| `gate` | hard gate와 비교 기준으로 `promotable/reject/review` 반환 |
| `report` | Markdown·JSON 비교 보고 생성 |

`gate`는 프레임워크 파일을 수정하거나 배포하지 않는다. 승격 실행은 사용자 승인 이후 별도 태스크가 담당한다.

### 5.3 독립 비교 판정

기존 `opal-evaluator-agent`에 가칭 `experiment-rubric` phase를 추가하는 안을 우선 검토한다. 기존 에이전트가 이미 verdict-only·readonly·생성자 분리 원칙을 갖고 있으므로 새 범용 judge agent를 만들기 전에 재사용 가능성을 검증한다.

블라인드 비교에서는 다음 정보를 평가자에게 숨긴다.

- 어느 결과가 기준 버전인지
- 어느 결과가 후보 버전인지
- 변경 가설이 어떤 결과를 기대하는지

평가자는 A/B 결과의 품질과 근거만 판정하고, PM이 숨겨진 조건을 해제해 정량 결과와 합성한다.

### 5.4 기존 컴포넌트 재사용

| 기존 자산 | 평가 루프에서의 역할 |
|---|---|
| `opal-agent` | 플랫폼별 에이전트 실행 adapter |
| `test-tool` | trial 내부 lint·unit·integration·scenario 판정 |
| `opal-evaluator-agent` | 주관 품질·블라인드 A/B 판정 |
| `worktree-tool` | 기준/후보 소스 격리 |
| `code-scan` | 영향 범위·구성요소 의존·중복 후보 수집 |
| `improve-tool` | 평가 결과에서 확인된 개선 후보 기록 |
| `state-tool` | 평가 구현 태스크 자체의 상태 관리 |
| OPAL Console | 후속 단계의 평가 결과 조회·비교 화면 |

---

## 6. 평가 자산 구조

### 6.1 소스와 실행 결과 분리

```text
opal/evals/
├── suites/
│   ├── skill-routing/
│   ├── harness-guards/
│   ├── planning-quality/
│   ├── worker-handoff/
│   └── end-to-end/
├── cases/
│   └── {case-id}/
│       ├── task.md
│       ├── case.yaml
│       ├── environment/
│       ├── fixtures/
│       ├── verifier/
│       └── oracle/
└── schema/
    ├── eval-case.schema.json
    ├── eval-run.schema.json
    └── eval-result.schema.json

.opal/eval-runs/
└── {run-id}/
    ├── run.json
    ├── trials/
    │   └── {case-id}/{condition}/{trial-id}/
    │       ├── trace.jsonl
    │       ├── outcome.json
    │       ├── score.json
    │       └── artifacts/
    ├── comparison.json
    └── REPORT.md
```

- `opal/evals/`는 install로 배포되는 프레임워크 평가 자산이다.
- `.opal/eval-runs/`는 실행 결과이므로 프로젝트 런타임 데이터다.
- 평가 과제와 실행 결과를 섞지 않는다.
- 원본 trace는 append-only로 보존하고 집계 결과는 재생성 가능하게 한다.

### 6.2 평가 과제 계약

각 case는 최소한 다음을 선언한다.

```yaml
id: harness-close-approval
goal: CLOSE 진입 전에 사용자 승인을 요구한다
category: harness-guard
input: task.md
environment: environment/
verifiers:
  - type: deterministic
    path: verifier/check.py
rubrics:
  - policy-compliance
resources:
  cpu: 2
  memory_mb: 4096
  timeout_seconds: 600
trials:
  default: 3
tags:
  - close
  - approval
```

실제 스키마와 필드명은 구현 계획에서 확정한다. 이 예시는 필요한 정보 경계를 보여주기 위한 것이다.

### 6.3 실행 조건 계약

같은 paired experiment 안에서는 다음 조건을 고정한다.

- 과제와 fixture 해시
- 모델 ID와 추론 설정
- 플랫폼과 agent harness 버전
- 사용 가능한 도구 목록
- CPU·RAM·timeout·동시성
- 네트워크 정책과 외부 서비스 상태
- 기준/후보 프레임워크 commit
- trial 수와 실행 시각

조건이 다르면 paired 결과로 합치지 않고 별도 cohort로 분리한다.

---

## 7. 실험 유형

### 7.1 기준선 비교 (`paired`)

같은 과제를 다음 조건으로 실행한다.

| 조건 | 목적 |
|---|---|
| `baseline` | 현재 배포 또는 기준 commit의 성능 |
| `candidate` | 변경 후보의 성능 |
| `minimal` | 해당 스킬·에이전트·하네스가 없는 최소 기준선 |

새 스킬은 `minimal`을 무스킬 조건으로 사용한다. 기존 스킬 개선은 현재 배포 버전을 `baseline`으로 사용한다.

### 7.2 구성요소 제거 실험 (`ablation`)

스킬 절, agent rule, harness 단계, 도구 호출 하나를 비활성화하고 동일 과제를 반복 실행한다.

| 결과 | 해석 |
|---|---|
| 품질 하락 | load-bearing 구성요소. 유지 대상 |
| 품질 동일·비용 감소 | 제거 또는 병합 후보 |
| 특정 도메인에서만 하락 | 공통 하네스에서 도메인 스킬로 이동 후보 |
| 품질 상승 | 과도한 지침·충돌·불필요한 단계 후보 |
| 편차 확대 | 평균 효과와 별개로 안정성에 기여하는 구성요소 |

한 실험에서 구성요소를 여러 개 동시에 제거하지 않는다. 여러 요소를 함께 제거하면 어떤 변화가 결과를 만들었는지 판정할 수 없다.

### 7.3 규칙 변이 실험 (`mutation`)

OPAL 문서와 실행 계약에 의도적인 결함을 넣고 기존 verifier가 이를 탐지하는지 확인한다.

초기 mutation catalog는 다음과 같다.

- `[MUST]` 조항 제거
- Gate 순서 변경
- 사용자 승인 행 제거
- 생성자와 평가자를 같은 주체로 지정
- 잘못된 도구 경로·서브명령 삽입
- 동일 규칙을 다른 SSOT에 중복 기재
- 상충하는 trigger 추가
- fallback 조건 반전
- output contract 필수 필드 제거
- mock을 실제 통합 증거로 위장

mutation survival은 평가 체계의 실패다. 살아남은 변이가 있으면 후보 프레임워크보다 verifier를 먼저 보강한다.

### 7.4 과거 태스크 재생 (`replay`)

실제 OPAL 태스크의 실패를 축소·익명화해 고정 과제로 편입한다.

- 사용자 재지시가 발생한 사례
- PM 검토는 통과했으나 checker가 잡은 사례
- 문서와 코드의 불일치를 놓친 사례
- 목표 시나리오 자체가 누락된 사례
- 워커가 불필요한 도구·문서를 반복 호출한 사례
- 배포본과 프로젝트 소스 경계를 위반한 사례
- 플랫폼별 동작 차이로 실패한 사례

실패를 고친 뒤 replay case를 제거하지 않는다. 다음 변경이 같은 문제를 재발시키는지 보는 영구 회귀 자산으로 유지한다.

### 7.5 플랫폼 이전 실험 (`cross-platform`)

같은 case를 Claude·Codex·Gemini 등 여러 플랫폼에서 실행한다.

목적은 플랫폼별 절대 순위를 만드는 것이 아니라 다음을 확인하는 것이다.

- 변경 효과의 방향이 플랫폼을 바꿔도 같은가
- 특정 플랫폼 adapter에만 의존한 규칙인가
- 스킬 본문에 플랫폼 분기가 새어 들어갔는가
- 모델이 좋아지면서 과거 scaffolding이 불필요해졌는가

플랫폼별 모델 능력 차이와 프레임워크 효과를 섞지 않는다. 같은 플랫폼 안에서 `candidate - baseline`을 계산한 뒤 delta의 방향을 비교한다.

---

## 8. 초기 평가 과제군

처음부터 대규모 벤치마크를 만들지 않는다. 실제 OPAL 실패와 핵심 계약에서 20개 안팎으로 시작한다.

| 영역 | 초기 수 | 대표 검증 |
|---|---:|---|
| 스킬 trigger·라우팅 | 4 | should-trigger·should-not-trigger·경쟁 스킬 판정 |
| 하네스 Guards·Gate | 4 | 승인·순서·상태·worker 경계 |
| PLAN·TEST-SCENARIO 품질 | 4 | 목표·요구·기능·리스크 커버 |
| 워커 디스패치·핸드오프 | 3 | 컨텍스트 누락·반환 계약·생성자/평가자 분리 |
| 도구 선택·fallback | 3 | 올바른 도구·에러 종류별 fallback·부재 처리 |
| 전체 미니 프로젝트 | 2 | 결과 상태·회귀·비용·전체 궤적 |

### 8.1 초기 fixture archetype

| fixture | 목적 |
|---|---|
| 문서 전용 프로젝트 | 정책·문서·citation·SSOT 검증 |
| Python CLI 프로젝트 | 단위 테스트·도구 계약·실행 증거 |
| React + FastAPI 미니 프로젝트 | FE/BE/E2E·전문 agent handoff |
| multi-repo 프로젝트 | worktree·허브 루트·프로젝트 경계 |
| brain/code-scan 부재 프로젝트 | 자산 부재 fallback |
| 의도적 문서·코드 불일치 프로젝트 | SSOT 판정과 갱신 후보 식별 |

### 8.2 데이터 분리

- **개발 세트**: 개선안을 만들고 디버깅할 때 사용
- **회귀 세트**: 모든 후보에 반복 적용
- **holdout 세트**: 승격 직전에만 사용해 과적합 확인

실패 사례가 새로 들어오면 먼저 holdout에 넣지 않는다. 재현·verifier 검증을 거친 뒤 회귀 세트로 승격한다.

---

## 9. 채점 체계

### 9.1 단일 종합점수를 사용하지 않음

품질·정책·비용을 하나의 숫자로 합치면 중요한 회귀가 평균에 가려진다. 다음 순서로 판정한다.

#### 1단계 — 필수 회귀 게이트

- 기존 합격 case의 신규 실패 0건
- 보안·승인·소유권·배포 경계 위반 0건
- 결정론 verifier 오류 0건
- 필수 mutation 탐지 실패 0건

하나라도 위반하면 품질 평균이 높아도 승격 불가다.

#### 2단계 — 효과

- task resolution rate
- 목표·요구·기능·리스크 커버
- blind A/B win rate
- failure category별 개선·악화
- 플랫폼별 paired delta

#### 3단계 — 효율

- 입력·출력 token
- wall-clock time
- 모델 호출과 도구 호출 수
- 재시도·PLAN 재진입·fallback 수
- 읽은 문서와 context byte
- 비용 추정치

#### 4단계 — 안정성

- trial 간 표준편차
- 결과 뒤집힘 비율
- 인프라 오류율
- 플랫폼·모델 변경 시 delta 방향 유지

### 9.2 trial 정책

- 초기 smoke: case당 조건별 1회
- 정식 paired run: case당 조건별 3회
- 승격선 근처 또는 결과 뒤집힘 발생: 5회 이상 재실행
- 인프라 오류 trial: 능력 실패와 분리하고 원인을 기록

20 case를 baseline/candidate 2조건으로 3회 실행하면 총 120 trial이다. 모든 변경마다 전체 실행하지 않고 영향 범위에 따라 smoke → 관련 suite → 전체 holdout 순서로 확대한다.

### 9.3 승격 판정

`eval-tool gate`의 결과는 세 가지다.

| 결과 | 조건 | 다음 행동 |
|---|---|---|
| `promotable` | hard gate 전건 통과 + 효과 개선 또는 동등 품질/효율 개선 + holdout 통과 | 사용자 승격 승인 요청 |
| `reject` | hard regression 또는 명확한 품질 악화 | 후보 반려·원인 기록 |
| `review` | 작은 delta·높은 편차·평가지표 충돌 | trial 확대 또는 사람 블라인드 검토 |

작은 점수 차이를 자동으로 개선이라 판정하지 않는다. 실행 환경과 신뢰구간을 함께 보고, 차이가 불확실하면 `review`로 남긴다.

---

## 10. 중복 제거 방법

### 10.1 1단계 — 구조적 후보 탐지

`code-scan` 확장 또는 별도 분석 모듈이 다음 후보를 수집한다.

- 동일·유사 문장과 규칙
- 여러 문서에 복제된 SSOT
- 같은 trigger를 두고 경쟁하는 스킬
- 동일한 입력·출력·도구를 가진 agent
- 같은 Gate를 중복 집행하는 harness 단계
- 서로 다른 이름이지만 같은 기능을 가진 도구
- 항상 함께 로드되지만 실제 참조되지 않는 reference

정적 유사도는 삭제 판정이 아니라 실험 후보 생성에만 사용한다.

### 10.2 2단계 — 소유권 판정

유사한 규칙이 여러 문서에 있으면 먼저 다음을 구분한다.

- 하나가 SSOT이고 나머지가 포인터여야 하는가
- 적용 시점이 달라 의도적으로 중복된 것인가
- 플랫폼 adapter와 공통 규칙의 역할이 다른가
- 설명과 집행 규칙이 서로 다른 계층에 있는가

SSOT 중복이면 기능 제거 실험 전에 문서 소유권 문제로 분류한다.

### 10.3 3단계 — 단일 구성요소 ablation

후보 하나만 비활성화하고 관련 suite와 holdout을 실행한다.

### 10.4 4단계 — 블라인드 결과 비교

정량 결과가 동등하면 독립 Evaluator 또는 사용자가 출처가 가려진 A/B 산출물을 비교한다.

### 10.5 5단계 — 삭제 게이트

다음 조건을 모두 충족할 때만 제거를 제안한다.

- hard regression 0건
- holdout 품질 저하 없음
- 적용 범위 누락 없음
- token·시간·복잡도 중 하나 이상 개선
- SSOT와 참조 링크 정합
- cross-platform 효과가 특정 adapter의 우연이 아님

삭제 후 전체 회귀 suite를 다시 실행한다. 제거 실험 결과 자체도 이후 프레임워크 판단 근거로 보존한다.

---

## 11. 개선 루프 연결

### 11.1 개선 후보 lifecycle 확장

현재 `opal-improve`와 `improve-tool`은 후보를 발견하고 기록한다. 여기에 평가 상태를 연결한다.

```text
candidate
  → experiment-ready
  → benchmarked
  → accepted | rejected | inconclusive
  → deployed
```

| 상태 | 의미 |
|---|---|
| `candidate` | 관찰이나 피드백으로 발견됨 |
| `experiment-ready` | 가설·과제·성공 기준이 준비됨 |
| `benchmarked` | 기준/후보 비교가 실행됨 |
| `accepted` | 평가 통과 + 사용자 채택 |
| `rejected` | 회귀 또는 효과 없음 |
| `inconclusive` | 편차·평가 충돌로 판단 유보 |
| `deployed` | 프로젝트 소스 반영과 install 검증 완료 |

기존 memory와 fw-inbox가 이 상태를 직접 소유할지, 별도 `eval-candidate.json`이 참조할지는 구현 계획에서 SSOT 경계를 확정한다. 같은 상태를 두 곳에 복제하지 않는다.

### 11.2 태스크 CLOSE 환류

태스크 CLOSE 회고는 개선 후보를 기록하는 것에서 끝나지 않고 다음 중 하나를 연결한다.

- 기존 eval case로 재현 가능 → 해당 case reference 연결
- 새 실패 유형 → case 초안 후보 생성
- 반복되는 비용·도구 낭비 → ablation 후보 생성
- 평가 체계가 놓친 결함 → mutation catalog 추가

모든 태스크가 새 평가 case를 만들 필요는 없다. 재발 가능하고 프레임워크 공통성이 있는 실패만 승격한다.

### 11.3 후보 아카이브

후보는 worktree 또는 container image와 다음 메타데이터로 보존한다.

- 기준 commit과 후보 commit
- 변경 가설
- 변경 파일
- 실행 suite와 case 해시
- 플랫폼·모델·자원 조건
- 비교 결과
- 채택·반려 이유
- 사용자 결정

최신 후보가 실패해도 이전의 유망한 후보와 실험 결과를 잃지 않는다.

---

## 12. 외부 도구 채택 전략

### 12.1 추천: OPAL 스키마 + Inspect 실행 adapter

Inspect AI를 첫 sandbox 실행 adapter로 검토한다.

이유:

- 로컬·오픈소스 실행 가능
- dataset·agent·tool·scorer가 분리됨
- Docker를 포함한 sandbox 지원
- Codex CLI·Claude Code·Gemini CLI 같은 외부 agent 연결 가능
- trace와 결과 로그 분석 기능 보유
- 특정 모델 공급자에 종속되지 않음

OPAL이 case·run·result 스키마를 소유하고 Inspect는 실행만 담당한다. Inspect API가 바뀌어도 OPAL 평가 자산이 함께 바뀌지 않도록 adapter 경계를 둔다.

### 12.2 Harbor 호환은 2차

Harbor는 터미널 기반 coding task와 대규모 container 실행에 강하다. OPAL의 end-to-end 미니 프로젝트가 늘어나거나 외부 benchmark와 상호운용해야 할 때 export/import adapter를 검토한다.

### 12.3 SkillsBench·BenchFlow는 방법론과 외부 교차검증

스킬 있음/없음 paired design과 deterministic verifier 구조는 직접 채택한다. 이후 OPAL 스킬 일부를 SkillsBench 형식으로 export해 외부 harness에서도 효과를 교차검증할 수 있다.

### 12.4 Promptfoo는 micro-eval에 한정

trigger 문구, 응답 형식, 짧은 rubric 비교에는 Promptfoo 같은 경량 matrix runner를 사용할 수 있다. 파일과 환경을 수정하는 장기 agent task의 주 실행기로는 사용하지 않는다.

출처: [Promptfoo Assertions](https://www.promptfoo.dev/docs/configuration/expected-outputs/), [Promptfoo CI/CD](https://www.promptfoo.dev/docs/integrations/ci-cd/)

### 12.5 OpenAI Hosted Evals는 핵심 의존성에서 제외

trace grading과 grader 설계는 참고하되 종료 예정인 hosted Evals 서비스에 평가 SSOT를 두지 않는다.

---

## 13. 단계별 도입안

### 단계 0 — 측정 가능성 PoC

목표: 새 프레임워크 전체를 만들기 전에 paired evaluation이 OPAL 개선에 실제 신호를 주는지 확인한다.

범위:

- 과거 실패 기반 case 10개
- 스킬 1개 선택
- 현재 버전·후보 버전·무스킬 3조건
- 동일 모델·플랫폼
- 조건별 3 trial
- 기존 `opal-agent`·`test-tool`·Evaluator 재사용
- 결과·token·시간·도구 호출·trace 수동 집계

완료 기준:

- 조건별 차이가 재현됨
- verifier가 최종 상태를 독립 판정함
- 동일 case 반복 편차가 측정됨
- 최소 1개의 유효 개선 또는 제거 후보 도출

PoC에서 차이가 측정되지 않으면 도구를 구현하기 전에 과제와 verifier 설계를 수정한다.

### 단계 1 — 평가 SSOT와 결정론 도구

- eval case/run/result 스키마 확정
- `eval-tool suite-check/run/compare/report` 구현
- worktree 기반 기준/후보 격리
- run metadata와 trace 표준화
- hard regression gate

### 단계 2 — sandbox·ablation·mutation

- Inspect adapter
- 고정 resource policy
- ablation runner
- mutation catalog와 mutation score
- blind A/B Evaluator phase
- holdout suite

### 단계 3 — 플랫폼·운영 통합

- Claude·Codex·Gemini cross-platform matrix
- `improve-tool` 후보 lifecycle 연결
- 평가 결과를 OPAL Console에서 조회
- 외부 Harbor·SkillsBench 호환 검토
- 주기 실행과 비용 예산 정책

---

## 14. 위험과 통제

| 위험 | 영향 | 통제 |
|---|---|---|
| 평가 과제 과적합 | benchmark는 오르지만 실제 프로젝트 성능 저하 | 개발/회귀/holdout 분리, 신규 실제 실패 지속 편입 |
| 약한 verifier | 거짓 초록불 | mutation test, oracle sanity check, 독립 grader |
| LLM judge 편향 | 후보 설명에 끌린 판정 | blind A/B, deterministic 우선, 사람 calibration |
| 인프라 노이즈 | 작은 delta를 개선으로 오판 | 자원 고정, 반복 trial, infra error 분리 |
| 평가 비용 증가 | 모든 변경에서 전체 suite 실행 불가 | smoke → 관련 suite → holdout 단계 실행 |
| 프레임워크 자기변경 | 실패 후보가 기준선을 훼손 | worktree/container 격리, 자동 승격 금지 |
| 외부 도구 종속 | adapter 변경이 평가 자산을 지배 | OPAL schema SSOT, adapter 격리 |
| 중복 제거 오판 | 다른 문맥의 필수 규칙 삭제 | 정적 탐지는 후보만, ablation+holdout+cross-platform 게이트 |
| benchmark gaming | agent가 verifier를 읽고 우회 | verifier/oracle 비노출, sandbox 권한 분리, outcome 검사 |

---

## 15. 권고안

### 15.1 방향

**OPAL 전용 평가 계층을 만들되, 처음부터 전체 시스템을 구현하지 않는다.**

1. 과거 실패 10건으로 스킬 1개의 paired evaluation PoC 수행
2. PoC에서 실제 개선·악화·편차가 구분되는지 확인
3. 신호가 확인되면 `eval-tool`과 평가 SSOT 구현
4. 그 다음 ablation·mutation·cross-platform으로 확장

### 15.2 외부 도구 선택

- 평가 자산 SSOT: OPAL 자체 소유
- 첫 실행 adapter: Inspect AI 우선 검토
- 터미널·외부 benchmark 확장: Harbor 2차 검토
- 스킬 효과 측정 방법: SkillsBench paired design 채택
- trigger·짧은 출력 검사: Promptfoo 선택 사용
- Hosted Evals 서비스: 핵심 의존성 제외

### 15.3 가장 먼저 검증할 가설

> “현재 OPAL 스킬 하나를 기준 버전·후보 버전·무스킬 조건으로 같은 과제 10개에 반복 적용하면, 품질·비용·안정성 차이를 재현 가능하게 측정할 수 있다.”

이 가설이 통과해야 후속 컴포넌트 구현이 정당화된다. 통과하지 않으면 평가 도구보다 과제·verifier·trace 계약을 먼저 개선한다.

---

## 16. 결정 필요 항목

| # | 결정 | 추천 |
|---|---|---|
| D-1 | 내부 명칭 | `OPAL Forge` |
| D-2 | 스킬명 | `opal-framework-eval` |
| D-3 | 별칭 | `opev` 후보, 레지스트리 충돌 확인 후 확정 |
| D-4 | 첫 대상 스킬 | 반복 실행이 쉽고 verifier가 명확한 스킬 1개를 실측 후 선정 |
| D-5 | 첫 실행 환경 | 현재 `opal-agent` 기반 로컬 worktree |
| D-6 | 첫 외부 adapter | Inspect AI |
| D-7 | 초기 과제 수 | PoC 10개, 정식 초기 suite 약 20개 |
| D-8 | trial 수 | smoke 1회, 정식 3회, 경계 결과 5회 이상 |
| D-9 | 승격 권한 | 사용자 승인 유지, 자동 배포 금지 |

---

## 17. AS-IS 축 매트릭스와 갭

| 쟁점 | 정책 | 화면 | 데이터 | 코드 |
|---|---|---|---|---|
| 개별 태스크 검증 | scenario-gate·하네스 | - | state·test-scenario | `test-tool` 근거 확보 |
| 변경 전후 효과 비교 | 명시 기준 없음 | - | 실험 SSOT 없음 | 전용 benchmark runner 미보유 |
| 중복 제거 검증 | 단순성 원칙만 존재 | - | ablation 결과 없음 | 기능 단위 제거 실험 미보유 |
| 자체 고도화 | 개선 후보 기록 규칙 존재 | - | fw-inbox 존재 | 후보 검증·승격 연결 미보유 |

갭 목록:

1. **개선 후보는 기록되지만 효과가 증명되지 않음 / 근거 부족 / paired evaluation 추가**
2. **프레임워크 버전 간 비교 단위가 없음 / 근거 부족 / eval run SSOT 추가**
3. **중복 제거 원칙은 있으나 삭제 안전성을 검증할 실험이 없음 / 근거 부족 / ablation gate 추가**
4. **플랫폼별 adapter는 있으나 동일 과제 비교가 없음 / 근거 부족 / cross-platform matrix 추가**
5. **공통 trace 계약이 별도 제안 상태 / 부분 근거 / `opal-task-run-log.md`와 중복 없이 접합 설계 필요**

---

## 18. 관련 내부 문서

- `docs/proposals/opal-task-run-log.md` — 태스크 전체 여정 trace의 공통 원천 후보
- `opal/core/references/harness/scenario-gate.md` — 목표-커버 평가와 생성자/평가자 분리
- `opal/skills/opal-improve/SKILL.md` — 개선 후보 수집·분류·기록
- `opal/core/references/harness/pm-improvement-loop.md` — CLOSE 회고와 FW 개선 환류
- `opal/agents/opal-evaluator-agent/AGENT.md` — 독립 루브릭 판정 주체
- `opal/tools/test-tool/README.md` — 기존 동작 검증 실행기
- `opal/skills/opal-pilot-project-loop/references/verification.md` — 결정론·루브릭·사람 3-tier와 검증 2원화

---

## 19. 외부 참고 자료

2026-09-10 확인 기준이다.

1. [Anthropic — Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
2. [SkillsBench: Benchmarking How Well Agent Skills Work Across Diverse Tasks](https://arxiv.org/abs/2602.12670)
3. [SkillsBench 1.1](https://www.skillsbench.ai/blogs/skillsbench-1-1)
4. [Anthropic Skills — Skill Creator](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md)
5. [Inspect AI](https://inspect.aisi.org.uk/)
6. [Inspect AI — Sandboxing](https://inspect.aisi.org.uk/sandboxing.html)
7. [Harbor Framework](https://github.com/harbor-framework/harbor)
8. [Harbor — Task Structure](https://www.harborframework.com/docs/tasks)
9. [Anthropic — Harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps)
10. [Anthropic — Quantifying infrastructure noise in agentic coding evals](https://www.anthropic.com/engineering/infrastructure-noise)
11. [Darwin Gödel Machine](https://arxiv.org/abs/2505.22954)
12. [OpenAI — Trace grading](https://developers.openai.com/api/docs/guides/trace-grading)
13. [OpenAI — Working with evals](https://developers.openai.com/api/docs/guides/evals)
14. [Promptfoo — Assertions and metrics](https://www.promptfoo.dev/docs/configuration/expected-outputs/)
15. [Promptfoo — CI/CD integration](https://www.promptfoo.dev/docs/integrations/ci-cd/)

