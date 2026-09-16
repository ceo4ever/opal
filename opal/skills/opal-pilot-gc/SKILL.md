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

**[MUST — pilot.start 이벤트 게이트]** 파일럿의 첫 작업 전에 아래 순서를 수행한다.

1. `~/.opal/tools/event-loader/run.sh load --event pilot.start > <pilot-receipt-path>`를 호출한다.
2. load 응답의 `documents[].content` 전문을 모두 현재 컨텍스트에 적용하고, `modes` 문서가 현재 플래그에 대해 라우팅한 서브 하네스 전문 하나만 Read한다.
3. `~/.opal/tools/state-tool/run.sh event-verify --event pilot.start --receipt <pilot-receipt-path>`가 성공한 뒤에만 진행한다.

**[MUST — 단계 이벤트 게이트]** 각 실제 단계의 첫 작업이나 `state-tool advance` 직전에 아래 매핑의 이벤트를 load하고, 응답 문서 전문을 적용한 뒤 같은 event id로 `state-tool event-verify`를 통과해야 한다.

| 실제 단계 | 이벤트 |
|---|---|
| SCAN | stage.analysis |
| CHECK | stage.test |
| REPORT | stage.plan |
| CLOSE | stage.close |

호출 형식은 `~/.opal/tools/event-loader/run.sh load --event <stage.*> > <stage-receipt-path>` 다음
`~/.opal/tools/state-tool/run.sh event-verify --event <stage.*> --receipt <stage-receipt-path>`이다.
문서 집합은 `events.json`만 SSOT로 사용하며 SKILL에 파일 목록을 복제하지 않는다. load 실패,
필수 문서 누락, stale receipt, wrong-event receipt는 해당 파일럿·단계 진입을 즉시 중단하는
blocker다. 부트 캐시를 근거로 공통 문서를 직접 재Read하는 우회는 금지한다.

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
  ├── STATE.md                        # 저널(의사결정 로그·블로커) + 실행 요약(자유 기재) (허브)
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

범위 해석은 아래 5경로 중 하나로만 확정한다.

| 범위 | 해석 | 대상 파일 확정 방법 |
|------|------|--------------------|
| `staged` (기본) | git staged 변경 | `git diff --name-only --staged` |
| `all` | 프로젝트 전체 추적 파일 | `git ls-files` |
| `untracked` | 추적되지 않은 신규 파일 | `git ls-files --others --exclude-standard` |
| `commit` / `commit:<ref>` | 특정 커밋의 변경 파일 (`<ref>` 생략 시 `HEAD`) | `git diff --name-only <ref>^ <ref>` |
| explicit | 호출자가 명시한 파일 목록 | git 조회 없이 전달받은 목록을 그대로 사용 |

- 호출자가 명시 목록(explicit)을 전달한 경우 git 조회를 수행하지 않는다. 명시 목록이 `--scope`보다 우선한다.
- `commit:<ref>`에서 `<ref>^`가 없는 최초 커밋이면 `git show --name-only --pretty=format: <ref>`로 대체한다.
- 어느 경로든 조회 결과에서 실재하지 않는 경로(삭제된 파일)만 제외하고 나머지를 `target_files`로 확정한다.

> **[MUST] 대상 고정**: SCAN이 확정한 파일 목록을 **그대로** CHECK 디스패치의 `target_files`로 전달한다. 하위 스킬(`op-gc-security`·`op-gc-convention`)은 git 상태나 자체 판단으로 대상을 재선별·확장·축소하지 않는다. §1.5 요소별 분할은 확정 목록의 분배일 뿐이며, 분할 결과의 합집합은 확정 목록과 같아야 한다. 분배되지 않고 남는 파일이 있으면 fallback 요소로 함께 전달한다.

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

> STATE.md 초기 생성은 §Agentic Mode(--agentic 플래그) 참조.

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

### 1.6 baseline 탐색

직전 opgc 실행 결과를 이번 실행의 delta 비교 기준으로 확정한다.

```
후보 = glob("tasks/*-opgc-*/gc-report.json")
후보 중 태스크 폴더 접두 NNN이 현재 태스크의 NNN보다 작은 것만 남긴다
남은 후보 중 NNN 최대값 1건 → baseline = 해당 gc-report.json 경로
후보가 없으면 → baseline = none
```

- 확정한 `baseline` 값은 CHECK 디스패치(§2.3)와 REPORT 위임(§3.2)에 같은 값으로 전달한다.
- `baseline: none`이면 이번 실행의 finding을 전건 신규로 표기한다.
- 비교 키와 delta 분류 규칙은 `opal/core/references/harness/gc-finding-schema.md` §7이 소유한다. 본 스킬은 규칙을 복제하지 않는다.

**산출물**: PM이 STATE.md 저널(자유 기재 영역)에 디스패치 매트릭스 요약 직접 기록 (분할 결과는 내부 참조용, `state.json` 비접촉 — state.json 파생이 아닌 opgc 고유 서술 정보)

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

> **[PM 컨텍스트 주입]** 디스패치 프롬프트 첫 줄에 `[WORKER]` 삽입. 주입 항목·핵심 제약(전 워커 공통 고정 포함)은 `opal/core/references/pm/dispatch-process.md` §워커 컨텍스트 주입 템플릿을 따른다 — 본 스킬은 항목을 열거하지 않는다.

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
- skill_path: ~/.opal/skills/op-gc-{security|convention}/SKILL.md
- project_root: {project_root}
- target_files: {element_targets[element.요소명] 또는 전체 target_files}   # SCAN 확정 목록 그대로 — 재선별 금지
- output_dir: {task_folder}
- timestamp: {ts}
- scope: {element.요소명 또는 "all"}      # 허브+링크 모델에서 상세 문서 선택
- element: {element.요소명 또는 미지정}    # 산출물 파일명 접미사 (요소 1개·fallback이면 생략)
- baseline: {§1.6에서 확정한 gc-report.json 경로 또는 none}
- project_documents: {docs/PROJECT.md 레지스트리에서 선별한 기준·설계 문서 경로 목록}
- docs/SECURITY.md 존재: {true|false}      # 보안 에이전트만
- docs/CONVENTIONS.md 존재: {true|false}   # 컨벤션 에이전트만

## 참조 문서 경로
- opal/core/references/harness/gc-finding-schema.md (finding 필드·envelope·fingerprint·판정 SSOT)
- docs/CONVENTIONS.md (컨벤션 에이전트 허브)
- docs/SECURITY.md (보안 에이전트 허브)
- docs/ARCHITECTURE.md (시스템 구조 참조)
- opal/core/references/conventions-hub-model.md (허브+링크 체이닝 규약)

## 전문 에이전트 참조
- {element.전문_에이전트} (선정 근거 — 보고서 §3 출력 시 참조)
```

> **보고서 파일명 충돌 방지**: 요소가 여러 개인 경우 timestamp 뒤에 `-{요소명}` 접미사를 추가한다. 예: `GC-SECURITY-{ts}-frontend.md`, `GC-CONVENTION-{ts}-backend.md`. 요소가 1개(또는 fallback)인 경우 기존 포맷 유지. 같은 규칙이 finding JSON(`gc-findings-{security|convention}-{ts}[-{요소명}].json`)에도 동일하게 적용된다.

### 2.4 완료 확인 게이트

모든 디스패치 결과의 `status: completed` 확인.

**산출물**: 각 (요소 × 체커)의 `GC-{SECURITY|CONVENTION}-{ts}[-{요소명}].md`와 `gc-findings-{security|convention}-{ts}[-{요소명}].json` (REPORT 입력)

**게이트**: 워커 완료 확인

---

## STEP 3: REPORT

**목적**: check 산출물 수합, `op-gc-report` 위임으로 통합 판정·baseline delta·문서 업데이트 트리거 산출, STATE.md 요약 테이블 갱신

### 3.1 결과 수합 입력 구성

각 (요소 × 체커) 디스패치 반환에서 아래 산출물 경로를 모은다. 누락된 산출물이 있으면 해당 조합을 통과로 간주하지 않고 결측으로 표기한다.

- 보고서: `{task_folder}/GC-SECURITY-{ts}[-{요소명}].md`, `{task_folder}/GC-CONVENTION-{ts}[-{요소명}].md` (요소별 N개)
- finding JSON: `{task_folder}/gc-findings-security-{ts}[-{요소명}].json`, `{task_folder}/gc-findings-convention-{ts}[-{요소명}].json` (요소별 N개)

### 3.2 op-gc-report 위임

중복 병합·baseline delta·차단 계산·최종 판정·문서 업데이트 트리거는 `op-gc-report`가 소유한다. 본 스킬은 판정 조건·임계값·fingerprint 산출을 보유하지 않는다.

- 스킬 탐색 경로:
  1. `{프로젝트}/.opal/skills/op-gc-report/SKILL.md`
  2. `~/.opal/skills/op-gc-report/SKILL.md`
- 디스패치 입력:
  - `project_root`: {project_root}
  - `output_dir`: {task_folder}
  - `timestamp`: {ts}
  - `findings_inputs`: §3.1에서 모은 finding JSON 경로 전건
  - `baseline`: §1.6에서 확정한 `gc-report.json` 경로 또는 `none`
- 산출 수합: `{task_folder}/GC-REPORT-{ts}.md`, `{task_folder}/gc-report.json`
- 반환의 `verdict`·`delta`·`blocking`·`missing_capabilities`를 STATE 요약과 사용자 보고의 근거로 쓴다.

> **[MUST]** finding JSON을 하나도 읽지 못했거나 `op-gc-report`가 `status: blocked`로 반환하면 PM이 판정을 임의로 생성하지 않고 REPORT를 중단한다.

### 3.3 STATE.md 실행 요약 테이블 갱신

> 아래 표는 `state.json` 파생이 아닌 opgc 고유 자유 기재이며, PM이 STATE.md 저널에 직접 기록한다(094 R-6).

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

**산출물**: `GC-SECURITY-{ts}[-{element}].md` × N, `GC-CONVENTION-{ts}[-{element}].md` × N, `GC-REPORT-{ts}.md`, `gc-report.json`, PM이 STATE.md 저널(자유 기재)에 실행 요약과 `op-gc-report` 판정(`verdict`·delta 건수) 직접 기록

**게이트**: 사용자 확인 (기본, 대화형 — pipeline.json 행 아님) — Agentic 모드에서 자율 통과. 이 확인의 결과는 별도 행으로 기록되지 않고 CLOSE 첫 행(`close.done_md`) `--owner user` mark로 집행된다(R-11 G-2, §4.2 참조).

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

> **[MUST] CLOSE 진입 게이트 (R-11 G-2 — 확인 행 0개 파이프라인 폴백)**: opgc `references/pipeline.json`에는 "사용자 확인" 행이 없다. 이 경우 `check_close_gate`는 **CLOSE 첫 행(`close.done_md`) 자체를 유일한 소유자 승인 지점**으로 취급한다 — 소유자에게 REPORT 결과를 보고하고 승인 발화를 받은 뒤 `--owner user`로 mark해야 하며, 생략 시 `close_gate_violation`으로 거부된다(`--force` 불요 — `--force`는 정책 우회이므로 사용하지 않는다).
> (`pilot.start`가 전달한 `guards`, `opal/tools/state-tool/state_tool.py` `check_close_gate` G-2 폴백 / `opal/core/references/opal-harness-semi-agentic.md` §3 opgc 행 / TASK.md §제약조건 원문 준수)

### 4.1 DONE.md 생성

`{task_folder}/DONE.md` 생성 — `done-template.md` 참조:
```
~/.opal/skills/opal-pilot-gc/references/done-template.md
```

### 4.2 CLOSE 행 갱신

소유자 승인 발화 수신 + DONE.md 생성 완료 후 state-tool로 행 갱신:

```
~/.opal/tools/state-tool/run.sh mark <task-path> --task-step close.done_md --done --owner user --note '{owner_name} 확인: GC 결과 확인 후 CLOSE 진행'
```

> **[MUST] 행 갱신**: mark하는 것 자체가 state 기록이며 별도의 State Gate 행은 존재하지 않는다. state-tool stage-transition guard가 이전 단계 필수 행 완료 여부를 자동 검증한다.
> **CLOSE 진입 게이트 (R-11 G-2 / §2.16 G-13)**: opgc는 확인 행이 0개이므로 CLOSE 첫 행(`close.done_md`)이 유일한 소유자 승인 지점이다. `--owner user` 누락 시 `close_gate_violation`으로 거부된다(`--force` 불요). `--auto-pass`는 agentic/semi-agentic 모드에서 별도로 `agentic_close_gate_requires_user`로 거부된다.

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

> **[MUST] 파이프라인 행 상태(⬜/🔄/✅) 변경은 `~/.opal/tools/state-tool/run.sh`로만 수행한다. `state.json` 직접 편집 금지 — 현황 조회는 `state-tool show <task-path>`로 한다.**
>
> **[SSOT]** SSOT는 `references/pipeline.json`이며, `state-tool init` 호출 시 이를 `--rows-from` 옵션으로 참조한다.
>
> STATE.md 초기 생성은 §Agentic Mode(--agentic 플래그) 참조.
>
> state-tool이 `references/pipeline.json`을 읽어 state.json을 초기화한다. 아래 표는 사람 열람용 미러이며 행 데이터를 직접 편집하지 않는다.

**파이프라인 행 구조**(`state.json` `rows[]`) (아래 표는 사람 열람용 미러 — SSOT는 `references/pipeline.json`. `.md` 파싱은 하위호환 폴백으로만 존치, 편집 금지):

> **행 구성 SSOT**: `references/pipeline.json` `task_steps[]`. 현재 행 목록은
> `~/.opal/tools/state-tool/run.sh show <task-path>` 또는 pipeline.json을 직접 조회한다.

**실행 요약 테이블 템플릿** (REPORT 단계에서 PM이 STATE.md 저널에 직접 기록 — `state.json` 비접촉, 자유 기재):

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
- **CLOSE 진입 게이트만 유지** — REPORT 사용자 확인 게이트(대화형, pipeline.json 행 아님)는 자율 통과
- `AGENTIC-LOG.md`를 태스크 폴더에 생성하여 자율 결정 내역을 기록
- 보고서 내 `[?] review` 항목은 **건너뛰지 않고** 주석에 "agentic: 사용자 확인 필요" 표기
- 자율 통과 시 state-tool mark 호출 (P-8):
  ```
  ~/.opal/tools/state-tool/run.sh mark <task-path> --task-step <task-step-key> --done
  ```
- **opgc는 "사용자 확인" 행 자체가 없다(R-11 G-2)** — 다른 pilot의 "사용자 확인 행은 PM이 명시 호출하지 않는다"(자동 승인) 규칙은 opgc에 적용 대상이 없다. 대신 **CLOSE 첫 행(`close.done_md`)이 유일한 소유자 승인 지점**이며, agentic 모드라도 이 행은 `--owner user`를 명시하여 mark해야 한다(자동 승인 대상 아님, `check_close_gate` G-2 폴백).
- **CLOSE 단계 첫 행(`close.done_md`)은 `--auto-pass` 금지** (`close_gate_violation` / agentic·semi-agentic은 `agentic_close_gate_requires_user` — §2.16 G-13); 반드시 `--owner user` 포함 명시 호출
- init 시 `--mode agentic` 플래그 추가:
  ```
  ~/.opal/tools/state-tool/run.sh init <task-path> --skill opgc --mode agentic --rows-from opal/skills/opal-pilot-gc/references/pipeline.json
  ```
- CLOSE 진입 전 소유자 확인 메시지 표시:
  ```
  [Agentic CLOSE 게이트] 자율 실행 완료. CLOSE 진입 승인? (y/n)
  ```

### 단계 보고 전이 계약

각 단계 행 mark/advance 직후 `state-tool` stdout의 `transition_action` / `report_type` / `next_action`을 소비한다. `report_type=progress_report`는 비차단 보고이며 `transition_action=continue`이면 같은 응답에서 다음 단계로 이어간다. `report_type=decision_request`는 `transition_action=await_user|blocked`일 때만 사용하고, CLOSE 진입 승인 예외는 유지한다.

---

## 관련 references

| 파일 | 역할 |
|------|------|
| `references/pipeline.json` | 파이프라인 행 구성 SSOT (편집 금지) |
| `references/done-template.md` | DONE.md 템플릿 |
| `~/.opal/skills/op-gc-security/SKILL.md` | 보안 검사 단계 스킬 — 검사 기준·보고서 형식 소유 (CHECK 디스패치 대상) |
| `~/.opal/skills/op-gc-convention/SKILL.md` | 컨벤션 검사 단계 스킬 — 검사 기준·보고서 형식 소유 (CHECK 디스패치 대상) |
| `~/.opal/skills/op-gc-report/SKILL.md` | 결과 정규화·판정·baseline delta·문서 업데이트 트리거 (REPORT 위임 대상) |
| `opal/core/references/harness/gc-finding-schema.md` | finding 필드·envelope·fingerprint·source_tier·판정표·delta SSOT |
| `opal/core/references/conventions-hub-model.md` | 허브+링크 체이닝 규약 (체커 scope 매칭) |
| `opal/core/references/pm/context-injection.md` | PROJECT.md 프로젝트 구성 기반 라우팅 규약 |

---
