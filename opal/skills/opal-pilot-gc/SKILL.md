---
name: opal-pilot-gc
description: |
  **경량 Pilot — 코드 컨벤션·보안 진단 오케스트레이터**. 커밋 전 보안·컨벤션 진단을 4단계 파이프라인으로 수행한다. 진단 전담(수정 없음) — 수정이 필요하면 CLOSE 단계에서 `//opds` 체인 안내.
  반드시 이 스킬을 사용해야 하는 상황: "opal-pilot-gc", "opgc", "gc", "//opgc", "//gc", "garbage collection", "보안 체크", "컨벤션 체크".
  약어: opgc | 별칭: gc
---

# opal-pilot-gc (경량 Pilot — GC 진단 오케스트레이터)

## Harness

모드: GC (SCAN → CHECK → REPORT → CLOSE)

> 부트스트랩에서 로드되지 않은 경우: `~/.opal/references/opal-harness.md`를 Read한다.

**[MUST]** 스킬 시작 즉시 모드에 따라 서브 하네스를 Read한다:
- `--agentic` 플래그 있음 → `~/.opal/references/opal-harness-agentic.md`를 Read한다
- `--agentic` 없음 (기본) → `~/.opal/references/opal-harness-interactive.md`를 Read한다

> **[MUST]** 산출물 작성·검증 시 `opal/core/references/harness/citation-rules.md`를 Read하여 규칙(근거 제시 원칙 / 트랙별 매트릭스 / [MUST] 토큰 / 영역 간 용어 일관성 / decision_required 계약)을 준수한다.

> **[MUST] 진단 전담**: 본 스킬은 코드 파일을 수정하지 않는다(APPLY 단계 제거됨). 수정이 필요한 이슈는 CLOSE 단계에서 `//opds` 체인으로 이관한다. Guards §1 "소스 파일 수정 금지" 원칙과 부합한다.

---

## Arguments 파싱

```
//opgc                                    # 전체 진단 (기본: staged, 보안+컨벤션 둘 다)
//opgc --security                         # 보안만 (컨벤션 체커 디스패치 생략)
//opgc --convention                       # 컨벤션만 (보안 체커 디스패치 생략)
//opgc --security --convention            # 둘 다 (둘 다 생략과 동일 — 명시적 전체)
//opgc --scope all                        # 전체 범위 + 보안+컨벤션 둘 다
//opgc --scope all --convention           # 전체 범위 + 컨벤션만
//opgc --agentic --convention             # Agentic 모드 + 컨벤션만
//opgc --scope all --convention --agentic # 전체 범위 + 컨벤션 + Agentic 모드
```

| Arguments | 기본값 | 설명 |
|---------|------|------|
| `--security` | - | 보안 진단 토글 (미지정 또는 `--convention`과 둘 다 지정 = 둘 다 실행) |
| `--convention` | - | 컨벤션 진단 토글 (동일 규칙) |
| `--scope staged` | ✅ 기본 | git staged 파일 대상 |
| `--scope all` | - | 프로젝트 전체 파일 대상 |
| `--agentic` | - | Agentic Mode 활성화 (CLOSE 진입 게이트만 유지) |

**토글 조합 규칙**:
- 둘 다 생략 → 둘 다 실행 (기본)
- `--security`만 → 보안만
- `--convention`만 → 컨벤션만
- `--security --convention` → 둘 다 (명시적 전체)
- 축이 다른 플래그는 자유 조합 가능 (`--scope`, `--agentic`, `--security`/`--convention`)

> **마이그레이션**: v1.0의 `--only security` / `--only convention` / `--apply`는 v1.1부터 제거되었다.
> - `--only security` → `--security`
> - `--only convention` → `--convention`
> - `--apply` → 제거 (APPLY 단계 자체가 사라짐 — 수정은 `//opds` 체인으로 이관)

---

## 태스크 폴더 자동 생성 규칙

```
tasks/{NNN}-{YYMMDD}-opgc-{short-summary}/
  ├── STATE.md                        # 파이프라인 상태 + 실행 요약 테이블 (허브)
  ├── GC-SECURITY-{타임스탬프}.md     # 보안 보고서 (요소별 N개 가능, 체크리스트 내장, 자기완결)
  ├── GC-CONVENTION-{타임스탬프}.md   # 컨벤션 보고서 (요소별 N개 가능, 체크리스트 내장, 자기완결)
  └── DONE.md                         # CLOSE 단계 완료 문서
```

`short-summary` 자동 생성 규칙:
- 기본: `staged` 또는 `all`
- `--security`만: `{scope}-sec-only`
- `--convention`만: `{scope}-conv-only`
- 둘 다 또는 둘 다 생략: `{scope}` (접미사 없음)
- 예: `tasks/NNN-260417-opgc-staged/`, `tasks/NNN-260417-opgc-all-conv-only/`

`NNN`: `memory-tool task-number --bump` 응답의 `last_task_number`. SCAN 단계에서 호출한다 (절차: `harness/task-process.md` §태스크 번호 채번 규칙).

---

## STEP 1: SCAN

**목적**: 대상 파일 선별, 기술 스택 감지, 기준 문서 로드, 프로젝트 구성 기반 분할, STATE.md 생성

### 1.1 범위 파싱 및 파일 선별

```bash
# --scope staged (기본)
git diff --name-only --staged

# --scope all
git ls-files
```

### 1.2 기술 스택 감지

다음 파일 존재 여부 확인:
- `package.json` → Node.js/React/Vue/Next/Express
- `requirements.txt` / `pyproject.toml` → Python/Django/Flask/FastAPI
- `go.mod` → Go
- `pom.xml` / `build.gradle` → Java/Spring Boot
- `Cargo.toml` → Rust

### 1.3 기준 문서 로드 확인

- `docs/SECURITY.md` 존재 여부 확인 (존재 → opal-security-checker에 경로 전달, 부재 → 플래그 설정)
- `docs/CONVENTIONS.md` 존재 여부 확인 (존재 → opal-convention-checker에 경로 전달, 부재 → 플래그 설정)

### 1.4 STATE.md 생성

태스크 폴더 생성 + STATE.md 초기화:

```
~/.opal/tools/state-tool/run.sh init <task-path> --skill opgc --rows-from opal/skills/opal-pilot-gc/SKILL.md
```

### 1.5 PROJECT.md 프로젝트 구성 기반 분할

`docs/PROJECT.md`의 "## 프로젝트 구성" 섹션을 파싱하여 CHECK 단계 디스패치 매트릭스를 구성한다. 상세 규약: `opal/core/references/pm/context-injection.md` "PROJECT.md 프로젝트 구성 기반 라우팅".

**파싱 의사코드**:

```
project_config = Read(docs/PROJECT.md)
if "## 프로젝트 구성" 섹션 존재:
    elements = 테이블 파싱 → [(요소명, 경로, 기술_스택, 전문_에이전트), ...]

    # target_files를 요소별 경로 prefix로 분할
    element_targets = {}
    for element in elements:
        element_targets[element.요소명] = [
            f for f in target_files
            if any(f.startswith(p) for p in element.경로.split(", "))
        ]

    # 체커 디스패치 매트릭스 = {요소} × {security, convention 중 활성 토글}
    dispatch_matrix = elements × active_checker_types
else:
    # Fallback (하위호환) — 프로젝트 구성 섹션 부재
    # 기존 1+1 단일 디스패치 유지
    dispatch_matrix = [(프로젝트_전체, active_checker_types)]
```

**요소별 target_files 분할 결과 예시** (풀스택 프로젝트):

| 요소 | 경로 | 분할된 파일 | 전문 에이전트 참조 |
|------|------|------------|-------------------|
| frontend | `web/` | `web/Button.tsx`, `web/Home.tsx` | opal-fe-agent |
| backend | `api/` | `api/user.py`, `api/auth.py` | opal-be-agent |
| batch | `batch/` | `batch/daily_report.py` | opal-be-agent (Backend 상속) |

> **[MUST] 하위호환**: "프로젝트 구성" 섹션이 없는 기존 프로젝트에서는 fallback(프로젝트 전체 × 체커)으로 진행하여 1+1 단일 디스패치와 동일하게 동작한다.

**산출물**: state-tool로 STATE.md 갱신 (분할 결과는 내부 참조, STATE.md에는 디스패치 매트릭스 요약만 기록)

**게이트**: 없음 (자동 진행)

---

## STEP 2: CHECK

**목적**: opal-security-checker + opal-convention-checker를 요소 × 체커 매트릭스로 병렬 디스패치

### 2.1 디스패치 매트릭스 선정

활성 체커 유형:
- `--security --convention` 또는 둘 다 생략 → `[security, convention]`
- `--security`만 → `[security]`
- `--convention`만 → `[convention]`

최종 디스패치 목록:

```
if 프로젝트_구성_섹션 존재:
    for element in elements:
        for checker in active_checker_types:
            dispatches.append((element, checker))
else:
    for checker in active_checker_types:
        dispatches.append((프로젝트_전체, checker))
```

### 2.2 요소 × 체커 병렬 매트릭스 예시

```
Case A — 단일 스택 프로젝트 (OPAL 자체):
  elements = [(Framework, opal/ · skills/ · agents/, opal-task-agent)]
  active_checker_types = [security, convention]
  → [Framework × security, Framework × convention] = 2회 병렬 디스패치

Case B — 모노레포 풀스택:
  elements = [frontend, backend]
  active_checker_types = [security, convention]
  → [frontend × security, frontend × convention,
     backend × security, backend × convention] = 4회 병렬 디스패치

Case C — FE + BE + Batch (3요소):
  elements = [frontend, backend, batch]
  active_checker_types = [security, convention]
  → 3 × 2 = 6회 병렬 디스패치

Case D — Fallback (프로젝트 구성 섹션 부재):
  dispatches = [(프로젝트_전체, security), (프로젝트_전체, convention)]
  → 2회 병렬 디스패치 (기존 1+1 동작, 하위호환)
```

### 2.3 병렬 디스패치 프롬프트 템플릿

각 `(element, checker)` 조합당 1개 에이전트를 병렬 호출한다:

```
[WORKER]

당신은 opal-{security|convention}-checker 에이전트입니다.
~/.opal/agents/opal-{security|convention}-checker/AGENT.md를 Read하고 프로세스를 따르세요.

## 핵심 제약 (Guards)
- [MUST] ~/.opal/ 경로 파일 직접 수정 금지
- [MUST] 커밋 금지 (git commit 호출 금지)
- [MUST] 커뮤니티 스킬 원본 수정 금지 — Read 래핑만
- [MUST] docs/SECURITY.md (또는 docs/CONVENTIONS.md) 자동 갱신 금지
- [MUST] 진단 전담 — 소스 파일 수정 금지(Edit/Write 도구 미할당)

## 입력 파라미터
- task_folder: {task_folder}
- target_files: {element_targets[element.요소명] 또는 전체 target_files}
- timestamp: {ts}
- checklist_path: ~/.opal/skills/opal-pilot-gc/references/base-{security|convention}-checklist.md
- template_path: ~/.opal/skills/opal-pilot-gc/references/report-{security|convention}-template.md
- project_root: {project_root}
- scope: {element.요소명 또는 "all"}      # 허브+링크 모델에서 상세 문서 선택
- docs/SECURITY.md 존재: {true|false}      # 보안 에이전트만
- docs/CONVENTIONS.md 존재: {true|false}   # 컨벤션 에이전트만

## 참조 문서 경로
- docs/CONVENTIONS.md (컨벤션 에이전트 허브)
- docs/SECURITY.md (보안 에이전트 허브)
- docs/ARCHITECTURE.md (시스템 구조 참조)
- opal/core/references/conventions-hub-model.md (허브+링크 체이닝 규약)

## 전문 에이전트 참조
- {element.전문_에이전트} (선정 근거 — 보고서 §3 출력 시 참조)
```

> **보고서 파일명 충돌 방지**: 요소가 여러 개인 경우 timestamp 뒤에 `-{요소명}` 접미사를 추가한다. 예: `GC-SECURITY-{ts}-frontend.md`, `GC-CONVENTION-{ts}-backend.md`. 요소가 1개(또는 fallback)인 경우 기존 포맷 유지.

### 2.4 완료 확인 게이트

모든 디스패치 결과의 `status: completed` 확인.

**산출물**: 각 (요소 × 체커) 보고서 임시 결과 (STATE 로그)

**게이트**: 워커 완료 확인

---

## STEP 3: REPORT

**목적**: 에이전트 결과 수합, 빈도/심각도 트리거 감지, STATE.md 요약 테이블 갱신

### 3.1 결과 수합

각 에이전트가 생성한 보고서 파일 확인:
- `{task_folder}/GC-SECURITY-{ts}[-{요소명}].md` (요소별 N개)
- `{task_folder}/GC-CONVENTION-{ts}[-{요소명}].md` (요소별 N개)

### 3.2 빈도 분석 상수

```
FREQ_THRESHOLD = 3  # 파일 수 기준 (향후 --freq-threshold로 오버라이드 가능성은 있으나 이번 구현 범위 아님)
```

### 3.3 트리거 감지 (독립 판정)

```
// 빈도 트리거 (N=3, 파일 수 기준)
동일 fingerprint가 FREQ_THRESHOLD개 이상 파일 → "[빈도 트리거]" 제안 생성

// 심각도 트리거 (Critical 또는 High — 빈도 트리거와 완전 독립 판정)
Critical 또는 High 이슈 1건 이상 → "[심각도 트리거]" 제안 생성
// 두 트리거는 별개 §4 항목으로 분리 표기한다

// 새 카테고리 트리거
기존 CONVENTIONS.md/SECURITY.md에 없는 카테고리 → "[새 카테고리 트리거]" 제안 생성
```

### 3.4 STATE.md 실행 요약 테이블 갱신

요소별 보고서가 여러 개인 경우, 요소별 행 + 합계 행으로 확장한다:

```markdown
## 이번 실행 요약

| 요소 | 에이전트 | 총 이슈 | Critical | High | Medium | Low | Info | 확인 필요 | 문서 제안 | 보고서 |
|------|----------|--------|----------|------|--------|-----|------|----------|----------|--------|
| frontend | security | 3 | 0 | 1 | 1 | 1 | 0 | 1 | 0건 | [→](./GC-SECURITY-{ts}-frontend.md) |
| frontend | convention | 8 | 0 | 0 | 2 | 4 | 2 | 1 | 1건 | [→](./GC-CONVENTION-{ts}-frontend.md) |
| backend | security | 5 | 1 | 2 | 1 | 1 | 0 | 2 | 2건 | [→](./GC-SECURITY-{ts}-backend.md) |
| backend | convention | 12 | 0 | 0 | 3 | 7 | 2 | 1 | 0건 | [→](./GC-CONVENTION-{ts}-backend.md) |
| **합계** | - | 28 | 1 | 3 | 7 | 13 | 4 | 5 | 3건 | - |
```

단일 요소(Fallback)인 경우 기존 2행 + 합계 포맷 유지.

**산출물**: `GC-SECURITY-{ts}[-{element}].md` × N, `GC-CONVENTION-{ts}[-{element}].md` × N, state-tool로 STATE.md 갱신

**게이트**: 사용자 확인 (기본) — Agentic 모드에서 자율 통과

보고 형식:
```
📋 [REPORT] 완료 — opal-pilot-gc

📎 보안 보고서: GC-SECURITY-{ts}[-{element}].md × {N} (Critical {N} / High {N} / 총 {N}건)
📎 컨벤션 보고서: GC-CONVENTION-{ts}[-{element}].md × {N} (총 {N}건)
📎 문서 업데이트 제안: {N}건

CLOSE로 진행할까요? 수정이 필요하면 CLOSE 단계에서 //opds 체인 안내를 드립니다.
```

---

## STEP 4: CLOSE

**목적**: 실행 요약 집계, DONE.md 생성, 필요 시 opds 수동 체인 안내

> **[MUST] CLOSE 진입 게이트**: REPORT 단계 사용자 확인 없이는 CLOSE 진입 금지.
> (하네스 §1 Guards, TASK.md §제약조건 원문 준수)

### 4.1 DONE.md 생성

`{task_folder}/DONE.md` 생성 — `done-template.md` 참조:
```
~/.opal/skills/opal-pilot-gc/references/done-template.md
```

### 4.2 CLOSE 행 갱신

DONE.md 생성 완료 후 state-tool로 행 갱신:

```
~/.opal/tools/state-tool/run.sh mark <task-path> --row 7 --done  # DONE.md 생성 (CLOSE 완료)
```

> **[MUST] 행 갱신**: mark하는 것 자체가 state 기록이며 별도의 State Gate 행은 존재하지 않는다. state-tool stage-transition guard가 이전 단계 필수 행 완료 여부를 자동 검증한다.
> **CLOSE 진입 게이트 (§2.16 G-13)**: CLOSE 단계 첫 행(#7)은 `--auto-pass` 적용 불가 (`close_gate_violation`). 반드시 위 명시 호출로 처리한다.

**관련 문서 업데이트** (op-brain-ingest 디스패치 직전 실행):

- `<프로젝트-루트>/docs/PROJECT.md`의 "프로젝트 문서" 레지스트리와 이번 GC 태스크의 `changed_files`를 양쪽 종합하여, 결과로 내용이 달라진 관련 문서(ARCHITECTURE.md·기획서 등)를 식별한다.
- 갱신 대상이 있으면 PM이 직접 수정하거나 적합한 워커를 디스패치해 최신화한다. 없으면 자연 스킵(no-op) — CLOSE를 중단시키지 않는다.
- 목적: brain ingest 이전에 기획·설계 문서를 최신 상태로 만들어 ingest 품질을 보장한다.

**op-brain-ingest 디스패치** (DONE.md 생성 + state-tool mark 완료 직후):

- `<프로젝트-루트>/.opal/brain/` 존재 여부를 확인한다.
- **brain이 존재하면**: op-brain-ingest 워커를 디스패치하여 GC 산출물(DONE.md·보고서 핵심 결정)을 brain에 누적한다.
- **brain이 없으면**: 자연 스킵(no-op). CLOSE가 막히지 않는다.
- op-brain-ingest 탐색 경로:
  1. `{프로젝트}/.opal/skills/op-brain-ingest/SKILL.md`
  2. `~/.opal/skills/op-brain-ingest/SKILL.md`
- 디스패치 입력: GC 태스크 폴더 경로
- 워커 status(skipped / completed / completed_with_errors) 무관 — CLOSE를 중단시키지 않는다.

**회고(개선 루프) 하드스텝** (op-brain-ingest 직후 실행):

- 입력: 태스크/세션 궤적 신호 — 워커 재시도·폴백, 소유자 재지시·피드백, PM Gate 반복 이슈, PLAN 재진입, 검증/재설계 루프 로그(STATE.md). ※ 산출물 재독이 아님(그건 PM Gate/QA 담당). 산출 = 프로세스·규칙 개선점.
- 관찰→분류(로컬 PM 개선 / FW 개선)→기록: 개선 후보별로 `~/.opal/tools/improve-tool/run.sh record --scope <local|fw> --title ... --body ... --situation retrospective --source-task <NNN> --project-root <루트>` 호출.
- 산출 결정론 기록: 개선 후보 N건은 improve-tool이 결정론적으로 기록(로컬→.opal / FW→fw-inbox).
- **no-op 안전 [MUST]**: 궤적 신호에서 개선 후보가 **없으면** 기록 없이 "개선후보 0건" 보고 — op-brain-ingest의 skipped와 동일하게 **CLOSE를 중단시키지 않는다**.
- 개선 루프 프로세스 SSOT: `opal/core/references/harness/pm-improvement-loop.md`.

### 4.3 수정이 필요한 경우 — opds 체인

opgc는 **진단 전담**이다. 보고서에서 `auto_fixable=true` 이슈나 `[?] review` 항목이 있다면, opds(opal-pilot-dev-short)로 체인하여 수정을 반영한다:

```
//opds "tasks/{NNN}-{YYMMDD}-opgc-{summary}/ GC 결과 반영"
```

**opds용 TASK.md 골격 예시**:

```markdown
# TASK: GC 결과 반영

## 배경
opgc 실행 결과 {N}건 이슈 감지
- GC-SECURITY-{ts}[-{element}].md (Critical {N} / High {N} / 총 {N}건)
- GC-CONVENTION-{ts}[-{element}].md (총 {N}건)

## 참조 문서
- tasks/{NNN}-{YYMMDD}-opgc-{summary}/GC-SECURITY-{ts}[-{element}].md
- tasks/{NNN}-{YYMMDD}-opgc-{summary}/GC-CONVENTION-{ts}[-{element}].md
- tasks/{NNN}-{YYMMDD}-opgc-{summary}/STATE.md (실행 요약 테이블)

## 요구사항
- auto_fixable=true 이슈 {M}건 수정 반영
- 각 이슈의 fix_hint를 근거로 수정하고, 보고서 체크박스를 `[x] done`으로 갱신

## 제약
- [?] review 항목은 본 태스크 제외 (소유자 판단 필요)
- 기존 테스트 회귀 금지
- 커밋은 소유자 지시 시만 (하네스 Guards §1)
- docs/CONVENTIONS.md, docs/SECURITY.md 자동 갱신 금지
```

**산출물**: `DONE.md`

보고 형식:
```
✅ [CLOSE] opal-pilot-gc 실행 완료
📎 산출물: tasks/{NNN}-{ts}-opgc-{summary}/DONE.md

{auto_fixable 이슈가 있는 경우}
수정이 필요한 이슈가 {M}건 있습니다. opds 체인으로 반영하시겠습니까?
  //opds "tasks/{NNN}-{ts}-opgc-{summary}/ GC 결과 반영"

태스크가 완료되었습니다.
```

---

## STATE.md 도메인 치환값

| 필드 | 값 |
|------|------|
| 모드 | GC |
| 단계 목록 | SCAN / CHECK / REPORT / CLOSE |

> **[SSOT]** `state-tool init` 호출 시 이 섹션의 행 테이블을 `--rows-from` 옵션으로 참조한다:
>
> ```
> ~/.opal/tools/state-tool/run.sh init <task-path> --skill opgc --rows-from opal/skills/opal-pilot-gc/SKILL.md
> ```
>
> state-tool이 이 파일의 "파이프라인 현황판 행 구조" 테이블을 읽어 state.json을 초기화한다. 행 데이터를 직접 편집하지 않는다.

**파이프라인 현황판 행 구조** (STATE.md 초기 생성 시):

```markdown
| # | 단계 | 항목 | 상태 | 시점 |
|---|------|------|------|------|
| 1 | SCAN | 대상 파일 선별 + 스택 감지 + 프로젝트 구성 파싱 | ⬜ | - |
| 2 | CHECK | 에이전트 (요소×체커) 병렬 디스패치 | ⬜ | - |
| 3 | CHECK | 에이전트 완료 확인 | ⬜ | - |
| 4 | REPORT | GC-SECURITY-{ts}[-{element}].md 생성 | ⬜ | - |
| 5 | REPORT | GC-CONVENTION-{ts}[-{element}].md 생성 | ⬜ | - |
| 6 | REPORT | 실행 요약 테이블 갱신 | ⬜ | - |
| 7 | CLOSE | DONE.md 생성 | ⬜ | - |
```

**실행 요약 테이블 템플릿** (REPORT 단계에서 STATE.md에 추가):

```markdown
## 이번 실행 요약

| 요소 | 에이전트 | 총 이슈 | Critical | High | Medium | Low | Info | 확인 필요 | 문서 제안 | 보고서 |
|------|----------|--------|----------|------|--------|-----|------|----------|----------|--------|
| {요소} | security | {N} | {N} | {N} | {N} | {N} | {N} | {N} | {N}건 | [→](./GC-SECURITY-{ts}[-{element}].md) |
| {요소} | convention | {N} | {N} | {N} | {N} | {N} | {N} | {N} | {N}건 | [→](./GC-CONVENTION-{ts}[-{element}].md) |
| **합계** | - | {N} | {N} | {N} | {N} | {N} | {N} | {N} | {N}건 | - |
```

---

## Agentic Mode (--agentic 플래그)

`~/.opal/references/opal-harness-agentic.md`를 Read한다.

Agentic 모드 특수 규칙:
- **CLOSE 진입 게이트만 유지** — REPORT 사용자 확인 게이트는 자율 통과
- `AGENTIC-LOG.md`를 태스크 폴더에 생성하여 자율 결정 내역을 기록
- 보고서 내 `[?] review` 항목은 **건너뛰지 않고** 주석에 "agentic: 사용자 확인 필요" 표기
- 자율 통과 시 state-tool `--auto-pass` 호출 (P-8):
  ```
  ~/.opal/tools/state-tool/run.sh mark <task-path> --row N --done --auto-pass --note '<근거>'
  ```
- **CLOSE 단계 첫 행(#7)은 `--auto-pass` 금지** (`close_gate_violation` — §2.16 G-13); 반드시 명시 호출
- init 시 `--mode agentic` 플래그 추가:
  ```
  ~/.opal/tools/state-tool/run.sh init <task-path> --skill opgc --mode agentic --rows-from opal/skills/opal-pilot-gc/SKILL.md
  ```
- CLOSE 진입 전 소유자 확인 메시지 표시:
  ```
  [Agentic CLOSE 게이트] 자율 실행 완료. CLOSE 진입 승인? (y/n)
  ```

---

## Fingerprint 알고리즘 (설계 참조)

에이전트 내부 집계용 — 보고서 미노출:

```
fingerprint_input = "{category_id}|{normalized_tokens}"
fingerprint = sha1(fingerprint_input).hex()[:16]

정규화 순서:
1. 코드 스니펫 ±3줄 추출
2. 주석 제거
3. 문자열 리터럴 → STR
4. 숫자 리터럴 → NUM
5. 식별자 → ID (언어별 정규식 — base-security-checklist.md 참조)
6. 연속 공백 → 단일 스페이스
7. 파일 경로·라인 번호 제외
```

---

## 관련 references

| 파일 | 역할 |
|------|------|
| `references/report-security-template.md` | 보안 보고서 템플릿 |
| `references/report-convention-template.md` | 컨벤션 보고서 템플릿 |
| `references/base-security-checklist.md` | OWASP+CWE+SANS+도메인 체크리스트 |
| `references/base-convention-checklist.md` | 컨벤션 카테고리 체크리스트 |
| `references/done-template.md` | DONE.md 템플릿 |
| `references/sample-report-security.md` | 보안 샘플 보고서 (참조용) |
| `references/sample-report-convention.md` | 컨벤션 샘플 보고서 (참조용) |
| `opal/core/references/conventions-hub-model.md` | 허브+링크 체이닝 규약 (체커 scope 매칭) |
| `opal/core/references/pm/context-injection.md` | PROJECT.md 프로젝트 구성 기반 라우팅 규약 |

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-04-17 | 초기 작성 — 5단계 파이프라인, arguments 파싱, STATE.md 치환값, 에이전트 병렬 디스패치, Agentic Mode, CLOSE 진입 게이트, 트리거 독립 판정, stash 롤백, fingerprint (122) |
| v1.1 | 2026-04-17 | APPLY 제거(진단 전담화) — 4단계 파이프라인(SCAN/CHECK/REPORT/CLOSE), CLI 토글 전환(`--security`/`--convention`, `--apply`/`--only X` 제거), PROJECT.md 프로젝트 구성 기반 동적 분할 병렬 디스패치, 체커에 `scope` 입력 + 허브+링크 체이닝, opds 수동 체인 가이드 (125) |
| v1.2 | 2026-04-24 | citation-rules 트리거 1줄 주입 — SSOT + Trigger 패턴 (130) |
| v1.3 | 2026-05-01 | state-tool 도입 — SCAN 1.4 init 호출 명시 + CLOSE State Gate를 state-tool mark 명시 호출로 교체 + `--rows-from` SSOT 지시 + agentic `--auto-pass` + CLOSE 진입 게이트 거부 정책 추가 (134) |
| v1.4 | 2026-05-09 18:30 | 개인 식별자 "캡틴" → "소유자" 치환 — 배포 파일 정체성 누설 정정 (139) |
| v1.5 | 2026-06-07 | STATE 행 8→7 재구성 — State Gate 행 제거(guard로 이전), §4.2 단일 mark 패턴으로 정합화 (014 Phase 4) |
| v1.6 | 2026-06-11 19:26 | §4.2 CLOSE에 op-brain-ingest 훅 삽입 — brain 존재 시 GC 산출물 누적, 부재 시 no-op, CLOSE 비중단 (016) |
| v1.7 | 2026-06-24 | §4.2 CLOSE op-brain-ingest 디스패치 직전에 "관련 문서 업데이트" 단락 삽입 — PROJECT.md 레지스트리 + changed_files 종합으로 관련 문서 최신화 후 ingest (없으면 no-op) (042) |
| v1.8 | 2026-07-17 | §4.2 CLOSE op-brain-ingest 직후에 "회고(개선 루프) 하드스텝" 삽입 — 궤적 신호→관찰/분류/기록(improve-tool record --scope local\|fw), 개선후보 0건 시 no-op 비차단(brain-ingest 패턴 답습) (058) |
| v1.9 | 2026-07-28 | `NNN` 채번 서술을 `.opal/MEMORY.md` 헤더 직접 참조에서 `memory-tool task-number --bump` 포인터 참조로 전환 (절차 SSOT: `harness/task-process.md`) (078) |
