# OPAL Harness -- 오케스트레이터 공통 인프라

> opal-pilot-* 오케스트레이터가 공유하는 프로세스 규칙.
> 각 opal-pilot SKILL.md 상단에서 이 문서를 Read하고, 도메인 고유 부분만 직접 정의한다.

---

## 1. Guards (제약)

### 구현 금지 원칙 (최우선 규칙)

**사용자가 명시적으로 "승인", "진행해", "구현해" 등의 실행 허가를 내릴 때까지 코드를 작성하거나 파일을 생성/수정하지 않는다.**

- 허용: 산출물 문서(.md) 작성, PM Gate 문서검증, 코드베이스 읽기/분석, 웹 검색
- 금지 (승인 전): 소스 코드 파일 생성/수정, 패키지 설치, DB 스키마 변경, 설정 파일 수정

### Git 사전 점검

태스크 시작 전 `git status`를 확인한다:
- **클린 상태**: 진행
- **커밋되지 않은 변경**: 사용자에게 커밋/스태시를 제안한 후 진행

### 디스패치 의무 원칙

**오케스트레이터 SKILL.md에 "워커 디스패치"로 정의된 단계(ANALYSIS, PLAN, EXECUTE 등)는 반드시 서브에이전트를 디스패치한다.** PM이 임의 판단으로 직접 실행하여 대체하지 않는다.

- 허용: TASK 단계(하네스에서 "직접 수행"으로 정의), 각 SKILL.md에서 "직접 수행"으로 명시된 경우
- 금지: "워커 디스패치"로 정의된 단계를 PM이 직접 실행

### CLOSE 진입 게이트

사용자의 확인된 지시(`승인`, `확인`, `확인완료` 등 명시적 표현)가 없으면 CLOSE 단계 진입 불가.
이 규칙은 agentic 모드에서도 유지된다(다른 Gate는 PM 자율 통과 허용이나 CLOSE 진입은 예외).

### 커밋 규칙

**커밋은 사용자가 명시적으로 요청할 때만 수행한다.** EXECUTE 완료, DONE.md 생성, 테스트 통과 후에도 자동으로 커밋하지 않는다. 완료 보고만 하고 사용자 지시를 기다린다.

### 자동 루핑 제약 (Verification Loop Guards)

자동 검증 루핑은 무한 루프를 방지하기 위해 다음 제약을 준수한다:

| 실패 유형 | 최대 재시도 | 초과 시 동작 |
|----------|-----------|------------|
| lint/format | 제한 없음 (즉시 수정) | - |
| build/type | 2회 | 사용자 에스컬레이션 |
| unit/integration test (L3a) | 3회 | 사용자 에스컬레이션 |
| E2E test (L3b) | 1회 | 사용자 에스컬레이션 |
| QA 설계/아키텍처 | 0회 | 즉시 사용자 에스컬레이션 |
| 워커 폴백 반복 (동일 작업 내 동일 폴백 유형 재발) | 1회 | 즉시 에스컬레이션 |

> **O1(§7.6)과 O3(이 행) 보완 관계**: O3은 단일 워커 수준(한 워커가 같은 폴백을 2번째 시도하면 중단), O1은 배치 집계 수준(배치 내 과반수 워커가 동일 폴백 패턴이면 다음 배치 중단). 두 규칙은 독립적으로 발동하며, 어느 쪽이든 먼저 트리거되면 즉시 적용한다.

- **회귀 방지**: 자동 수정 후 이전 통과 테스트를 재실행한다. 회귀 발생 시 루프 즉시 중단 + 에스컬레이션
- **사용자 게이트 유지**: 루핑은 agentic이지만 최종 확정은 반드시 사용자를 거친다

---

## 2. 모듈 구조

하네스는 **공통(이 문서) + 모드별 서브 하네스** 구조로 구성된다.
오케스트레이터는 이 문서를 Read하면, 모드에 따라 해당 서브 하네스를 추가로 Read한다.

### 서브 하네스 모듈

| 모듈 | 역할 | 로드 조건 | 탐색 경로 |
|------|------|----------|----------|
| `opal-harness-semi-agentic.md` | semi-agentic 모드 (기본 — PLAN까지 interactive 흐름, EXECUTE 이후 agentic 흐름, CLOSE 게이트 공통) | 모드 플래그 없음 (기본) 또는 `--semi-agentic` | `~/.opal/references/opal-harness-semi-agentic.md` |
| `opal-harness-interactive.md` | interactive 모드 (Gates — 단계/QA/PM/체크리스트 게이트) | `--interactive` 플래그 **있음** | `~/.opal/references/opal-harness-interactive.md` |
| `opal-harness-agentic.md` | agentic 모드 (PM 대행, 자율 검토, Gate 루핑, AGENTIC-LOG) | `--agentic` 플래그 **있음** | `~/.opal/references/opal-harness-agentic.md` |

### 로딩 규칙

1. 오케스트레이터는 **공통 하네스**(`opal-harness.md`)를 Read한다 (부트스트랩 또는 Harness 섹션)
2. 공통 하네스 Read 후, 모드에 따라 **서브 하네스 1개를 추가 Read**한다:
   - 모드 플래그 없음 (기본) 또는 `--semi-agentic` → `opal-harness-semi-agentic.md`
   - `--interactive` → `opal-harness-interactive.md`
   - `--agentic` → `opal-harness-agentic.md`
   - 다중 모드 플래그 동시 사용 → `mode_flag_conflict` 에러 (state init도 동일 거부)
   - **단, 해당 서브 하네스가 현재 세션 컨텍스트에 이미 로딩되어 있으면 Read를 스킵한다.**
3. 새 모드 추가 시: 이 테이블에 행을 추가하고, 서브 하네스 파일을 생성한다

### 하네스 모듈

Lazy 로드 모듈. 각 §의 stub이 로드 시점과 파일 경로를 지시한다.

| 모듈 | 파일 | 로드 시점 | 해당 § |
|------|------|----------|--------|
| State 템플릿 | `harness/state-template.md` | TASK 단계에서 STATE.md 초기 생성 시 | §3 |
| 추가작업 | `harness/additional-work.md` | 태스크 완료 후 추가 수정 필요 시 | §3 |
| QA 표준 | `harness/qa-standards.md` | PM Gate 문서검증 시 | §2 |
| Observability | `harness/observability.md` | 워커 디스패치 직전 (매 디스패치마다) | §5 |
| 병렬 처리 | `harness/parallel-execution.md` | 병렬 디스패치 시 | §7 |
| @header 규칙 | `harness/header-rules.md` | EXECUTE 단계에서 코드 파일 생성/수정 시 | §8 |
| 인용 규칙 | `harness/citation-rules.md` | TASK/ANALYSIS/PLAN 산출물 작성 시 | §2 |
| State 관리 | `harness/state.md` | TASK 단계 시작 / Gate 직후 State Gate | §3 |
| TASK 공통 프로세스 | `harness/task-process.md` | TASK 단계 진입 시 | §4 |
| Coding Principles | `harness/coding-principles.md` | EXECUTE 단계 진입 시 (코드 변경 워커) / PM "그냥 해" 진입 시 | §10 |
| RED-first 규칙 | `harness/red-first.md` | TEST-SCENARIO 작성·EXECUTE 진입 시 | §1.5 |

> 탐색 경로: `{프로젝트}/.opal/references/harness/{file}` → `~/.opal/references/harness/{file}`

### QA 산출물 표준 및 검증

> **[필수 로드]** PM Gate 문서검증 시 로드한다.
> 탐색: `harness/qa-standards.md`
>
> 적용 주체: PM
> 적용 시점: PM Gate 문서검증 시
> PM Gate 검증: QA 산출물 파일명이 표준을 따르는가, 체크리스트 갱신 규칙이 적용되었는가

### Citation Rules 적용 의무

> **[MUST]** 모든 pilot(오케스트레이터) / PLAN·TASK·ANALYSIS 스킬 / QA 스킬은 각자 다루는 산출물의 작성·검증 시 `opal/core/references/harness/citation-rules.md`를 필수 Read하고 그 규칙을 준수한다.
>
> 적용 범위: 근거 제시 원칙(§0) / 트랙별 근거 매트릭스(§1.5) / [MUST] 토큰 대상(§2.5) / 영역 간 용어 일관성 + decision_required 계약(§7)
> 적용 모드: interactive · agentic 양쪽 모두

---

## 3. State (상태 관리)

> **[필수 로드]** TASK 단계 시작 / EXECUTE Step 진행 / Gate 직후 State Gate 수행 시 로드한다.
> 탐색: `harness/state.md`
>
> 적용 주체: PM(오케스트레이터), 워커(EXECUTE Step 갱신)
> 적용 시점: TASK/EXECUTE/Gate 단계 전반
> PM Gate 검증: STATE.md 갱신 여부, 파이프라인 현황판 행 상태 정합성

> **[MUST]** 파이프라인 현황판 행 상태 변경은 `state-tool`로만 수행한다. LLM이 STATE.md 마크다운 표를 직접 편집하는 것은 금지된다.
>
> - TASK 단계 시작: `~/.opal/tools/state-tool/run.sh init <task-path> --skill <약어> --mode <모드>`
> - 단계 시작(⬜→🔄): `~/.opal/tools/state-tool/run.sh advance <task-path> --row <N>`
> - 단계 완료(→✅): `~/.opal/tools/state-tool/run.sh mark <task-path> --row <N> --done`
> - 워커 완료(EXECUTE Step): `~/.opal/tools/state-tool/run.sh mark <task-path> --row <N> --done --as-worker --worker-stage <stage>`
> - PM Gate 통과 후 단일 mark: `~/.opal/tools/state-tool/run.sh mark <task-path> --row <N> --done`
> - [deprecated] gate-pass — 레거시 전용. 신규는 위 단일 mark 사용 (Phase4 완료, State Gate/QA Gate 행 제거)
> - 추가작업 행 삽입: `~/.opal/tools/state-tool/run.sh add-row <task-path> --after <N> --stage <단계> --item <항목>`
>
> 위반 시 도구가 거부하며 에러 코드를 반환한다. 주요 에러:
> `marker_missing`(STATE.md 마커 누락) / `worker_scope_violation`(워커 권한 초과) / `state_not_initialized`(state.json 미존재)
> — 전체 에러 카탈로그 23종: `tasks/134-260501-opp-pipeline-state-tool/PLAN.md` §2.18
>
> 근거: `tasks/134-260501-opp-pipeline-state-tool/TASK.md` F-13 / `PLAN.md` §1.5 M-8 / §3 Step 3

---

## 4. TASK 공통 프로세스

> **[필수 로드]** TASK 단계 진입 시 로드한다.
> 탐색: `harness/task-process.md`
>
> 적용 주체: PM(오케스트레이터)
> 적용 시점: TASK 단계 진입 / 태스크 채번 / 저장 경로 판단 시
> PM Gate 검증: TASK.md 헤더 필드 준수, STATE.md 생성 완료, 저장 경로 규칙 준수

---

## 5. Observability (관측)

> **[필수 로드]** 워커 디스패치 직전 로드한다 (매 디스패치마다).
> 탐색: `harness/observability.md`
>
> 적용 주체: PM(오케스트레이터)
> 적용 시점: 워커 디스패치 직전 (매 디스패치마다)
> PM Gate 검증: 행위 주체 표시 수행 여부, 타임스탬프 bash 취득 여부

---

## 6. Model Mapping (모델 매핑)

오케스트레이터가 워커를 디스패치할 때, model 필드는 플랫폼 중립적인 레벨명을 사용한다.
레벨별 플랫폼 매핑: `~/.opal/references/opal-model-mapping.md` 참조.

| 레벨 | 용도 |
|------|------|
| `light` | 단순 작업 (분류, 포맷 변환, 검색 기반 분석) |
| `standard` | 범용 작업 (코드 작성, 문서 작성, 일반 분석) |
| `advanced` | 복잡 추론 (아키텍처 설계, 깊은 분석) |

---

## 7. 병렬 처리 원칙

> **[필수 로드]** 병렬 디스패치 시 로드한다.
> 탐색: `harness/parallel-execution.md`
>
> 적용 주체: PM(오케스트레이터)
> 적용 시점: 병렬 디스패치 시
> PM Gate 검증: 병렬/순차 판별이 올바른가, 리소스 제한이 준수되었는가

---

## 8. EXECUTE @header 규칙

> **[필수 로드]** EXECUTE 단계에서 코드 파일 생성/수정 시 로드한다.
> 탐색: `harness/header-rules.md`
>
> 적용 주체: PM → 워커 프롬프트에 주입
> 적용 시점: EXECUTE 단계에서 코드 파일 변경 시
> PM Gate 검증: changed_files 중 대상 확장자에 @header가 올바르게 작성되었는가

---

## 9. OPAL Tools (도구)

> **Lazy 트리거**: 파일 처리(xlsx, pdf, 이미지 등) 또는 데이터 변환 작업 요청 시

### 도구 우선 원칙

파일 처리나 데이터 변환이 필요할 때, **에이전트가 직접 코드를 작성하기 전에 OPAL 도구를 먼저 확인한다.**

1. `~/.opal/references/tools.md`를 Read하여 사용 가능한 도구 목록을 확인한다
2. 적합한 도구가 있으면 해당 도구를 Bash로 호출한다
3. 도구가 없을 때만 직접 코드를 작성하거나 에이전트를 디스패치한다

### 도구 호출 방식

OPAL 도구는 모두 `~/.opal/tools/{tool-name}/run.sh` 래퍼를 통해 호출한다.
출력은 JSON이며, `"ok": false`이면 `"error"` 필드를 확인하여 에스컬레이션한다.

```bash
# 올바른 예 — 래퍼 스크립트 호출
~/.opal/tools/xlsx-tool/run.sh info file.xlsx

# 출력 확인
{ "ok": true, "command": "info", "sheets": [...] }
```

### 현재 등록된 도구

| 도구 | 용도 | 트리거 조건 |
|------|------|------------|
| `xlsx-tool` | xlsx 읽기/쓰기/검색 | xlsx 파일 처리 요청 |
| `state-tool` | 파이프라인 현황판 JSON SSOT 관리 (9개 서브 명령: `init`/`show`/`advance`/`mark`/`block`/`validate`/`add-row`/`status`/`gate-pass`) | TASK 단계 시작 / Gate 직후 / 추가작업 진입 |
| `brain-tool` | 프로젝트 브레인 지식 위키 결정론적 집행 — 8 서브명령 `init`/`add-page`/`index`/`log`/`search`/`sync-header`/`lint`/`validate` | `//opbr` 또는 brain 참조 시 |

> 전체 사용법: `~/.opal/references/tools.md`

---

## 10. Coding Principles

> **[필수 로드]** EXECUTE 단계에서 코드 파일 변경 시, 또는 PM "그냥 해" 직접 수행 시 로드한다.
> 탐색: `harness/coding-principles.md`
>
> 적용 주체: 코드 변경하는 모든 워커 + PM("그냥 해")
> 적용 시점: EXECUTE 단계 진입 직후 / PM 직접 수행 시
> PM Gate 검증: 산출물에 사변적 추가·인접 코드 개선·불가능 시나리오 방어 코드가 없는가

---

## 변경이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | - | 최초 작성 |
| v2.0 | 2026-03-31 | 모듈화 — §2 Gates → opal-harness-interactive.md, §7 Agentic → opal-harness-agentic.md 분리. §2 모듈 구조 + QA 체크리스트 검증 추가 (058) |
| v2.1 | 2026-04-01 | §7 병렬 처리 원칙 추가 — 읽기(툴콜)/실행(Agent) 병렬 필수 원칙 (067) |
| v2.2 | 2026-04-02 | §7.4-§7.5 리소스 관리 및 런타임 폴백 원칙 추가 — 대용량 작업 안정성 확보 (068) |
| v2.3 | 2026-04-02 | §0 폴백 용어 정의, §1 워커 폴백 반복 제약 + O1/O3 보완 관계, §7.6 배치 실패 패턴 감지 추가 (071) |
| v2.4 | 2026-04-03 | §8 OPAL Tools 추가 — 도구 우선 원칙 + tools.md Lazy 트리거 (076) |
| v2.5 | 2026-04-04 | §4 TASK 공통 프로세스에 스킬/공통 영역 구분 마커 추가 + STATE.md 생성 `[필수]` 강조 (083) |
| v2.6 | 2026-04-05 | §2 QA 체크리스트 검증 — 2단계 갱신 구조(QA 에이전트 1차 갱신 + PM 2차 확인) + PM 직접 갱신 금지 원칙 (085) |
| v2.7 | 2026-04-05 | §3 추가작업 프로세스 추가 — 상태값 `추가작업중`/`추가작업완료` + 전이 흐름, ADD_DONE.md 템플릿, 감지 조건 3가지, 진입 절차 5단계, 스킬별 검증 테이블(opp/opds/opd/opwt/opsdd), DONE.md 보존 원칙 (087) |
| v2.8 | 2026-04-06 | §2 QA 산출물 표준 파일명 서브섹션 추가 — Artifact Gate 기준 파일명 공통화 (090) |
| v2.9 | 2026-04-07 | §4 저장 경로 규칙 추가 — base_path 조건부 처리 (기존 오케스트레이터 영향 없음) (093) |
| v3.0 | 2026-04-07 | §3 STATE.md 이벤트 테이블 전면 재설계 — Gate별 진행 현황 테이블 행 갱신으로 통합. `완료 산출물` 섹션 → `진행 현황` 행 기반 테이블로 교체. Artifact Gate 이벤트 추가. 수행 순서 강제 원칙 추가. 레거시 Gate 상태값 deprecated (097) |
| v3.0 | 2026-04-07 | §3 STATE.md 이벤트 테이블에 "강제" 명시 + 갱신 모델(워커 1차 + PM 확인) 추가. §3 State Gate 섹션 신설 — 자가 점검 프롬프트 + 차단 원칙 + 표준 Gate 순서 문구 (094) |
| v3.1 | 2026-04-07 | §3 상태값 확장(`대기 중` → Gate 3단계) + 이벤트 테이블 Gate 행 추가 + State Gate 이전 단계 차단 규칙. §5 행위 주체 표시 신설(PM직접/워커디스패치/워커완료). 레거시 호환 노트 추가 (096) |
| v3.2 | 2026-04-09 | §2 단계별 주요 산출물 표준 파일명 추가. §3 이벤트 테이블 산출물 생성 행 추가. 진행 현황 행 구성 규칙에 산출물 행 규칙 추가 (101) |
| v3.3 | 2026-04-09 | §4 저장 경로 날짜 포함 형식으로 변경(`{NNN}-{YYMMDD}-{스킬약어}-{태스크명}`) + 태스크 번호 채번 규칙 추가(`last_task_number` 기반). §5 타임스탬프 취득 규칙(필수) 추가 — bash 생략 금지 (102) |
| v3.4 | 2026-04-10 | §3 진행 현황 행 구성 규칙에 opsdd (opal-pilot-sdd) 43행 진행 현황 예시 추가 (R-5, 105) |
| v3.5 | 2026-04-10 | Artifact Gate 제거 + 파이프라인 현황판 이름 변경 (R-4) + PM Gate 관련 참조 정리 (106) |
| v3.6 | 2026-04-12 | §8 EXECUTE @header 규칙 추가 — 파일 생성/수정 시 워커 작성 의무 + 적용 대상 확장자 + md 파일 HTML comment 포맷 지원 + code-scan 활용 가이드 (B안) 추가. 기존 §8 OPAL Tools → §9로 번호 변경 (109) |
| v3.7 | 2026-04-12 | §3 State 리팩토링 — opsdd 파이프라인 현황판 예시 제거(opsdd SKILL.md에 존재), 병렬 실행 State 제거(oppd SKILL.md/guide에 존재), State Gate 자가 점검 프롬프트 deprecated 상태값 갱신 (110) |
| v4.0 | 2026-04-12 | 하네스 모듈화 — §2 QA 표준, §3 템플릿/추가작업, §5 Observability, §7 병렬 처리, §8 @header 규칙을 `harness/` 개별 모듈로 분리. §2에 모듈 매핑 테이블 추가. 각 § stub에 [필수 로드] + 적용 주체/시점/PM Gate 검증 명시 (111) |
| v4.1 | 2026-04-15 | §4 태스크 번호 채번 규칙 — `last_task_number` 갱신 시점을 "TASK.md 완료 후" → "채번 직후(폴더 생성 전)"으로 변경. 동시 실행 인스턴스 간 번호 중복 방지 (120) |
| v4.2 | 2026-04-15 | §1 Guards에 CLOSE 진입 게이트 Guard 신설 + §3 이벤트 테이블 CLOSE 귀속 + 상태 전이 흐름 CLOSE 명시 + 레거시 호환 원칙 추가 (121) |
| v4.3 | 2026-04-17 | §2 하네스 모듈 테이블에 citation-rules 추가 — 산출물 인용 규칙 신설 (123) |
| v4.4 | 2026-04-21 | 다운사이징 — §0 용어 정의 삭제, §3 State 본문 → harness/state.md 분리, §3 레거시 호환 노트 3건 삭제, §4 TASK 공통 프로세스 본문 → harness/task-process.md 분리, §2 모듈 테이블에 state.md·task-process.md 행 추가 (128) |
| v4.5 | 2026-04-24 | §2 Citation Rules 적용 의무 블록 추가 — 모든 pilot/스킬/가이드/QA 대상 인용 규칙 필수 적용 선언 (130) |
| v4.6 | 2026-05-01 | §3 state-tool [MUST] 호출 의무 블록 추가 — 파이프라인 현황판 행 상태 변경은 state-tool로만, 위반 시 에러 코드 목록 + PLAN §2.18 링크. §9 도구 테이블에 state-tool 행 추가 (트리거: TASK 단계 시작 / Gate 직후 / 추가작업 진입) (134) |
| v4.7 | 2026-05-09 11:22 | §2 모듈 구조 표에 semi-agentic 행 추가 + 로딩 규칙 3-way 갱신 (140) |
| v4.8 | 2026-05-10 19:36 | §2 하네스 모듈 테이블에 reporting-template 행 추가 — Eager 로드 (143) |
| v4.9 | 2026-05-12 11:16 | §2 하네스 모듈 테이블에 coding-principles 행 추가 + §10 Coding Principles stub 신설 (001) |
| v5.0 | 2026-06-07 | §1 Guards 허용 항목 "QA 에이전트 호출" → "PM Gate 문서검증" 치환. §2 하네스 모듈 테이블 QA 표준 로드 시점 "QA Gate 수행 시" → "PM Gate 문서검증 시" 치환. §2 QA 산출물 표준 stub 3곳 동일 정합화 — 별도 QA Gate/QA 에이전트 제거 (014 Phase 3 보완) |
| v5.1 | 2026-06-07 | §3 state-tool [MUST] 블록 — "Gate 직후 일괄 처리 gate-pass" 줄을 "PM Gate 통과 후 단일 mark"로 교체 + [deprecated] gate-pass 레거시 안내 추가. Phase4 완료 반영 (014 Phase 4) |
| v5.2 | 2026-06-08 | §2 하네스 모듈 테이블 reporting-template 행 제거 — 보고 형식 AGENT.md 인라인화 (015) |
| v5.3 | 2026-06-09 18:42 | §2 하네스 모듈 테이블에 RED-first 규칙 행 추가 — red-first.md 등록, 로드 시점: TEST-SCENARIO 작성·EXECUTE 진입 시 (016) |
| v5.4 | 2026-06-10 01:04 | §9 등록 도구 표에 brain-tool 행 추가 — 프로젝트 브레인 지식 위키 도구 8 서브명령 (015-brain, 별도 PC 015와 중복 채번) |
