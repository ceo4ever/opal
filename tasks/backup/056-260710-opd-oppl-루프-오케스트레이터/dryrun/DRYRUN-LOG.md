# DRYRUN-LOG: oppl 드라이런 E2E (hello-cli)

> PLAN §4.2 Step 13 드라이런 실행 로그. oppl Loop 1 D2~D5를 최소 규모("hello-cli")로 재현하며,
> 배포본 도구(`~/.opal/tools/backlog-tool/`, `~/.opal/tools/date/date.js`)만 사용한다(mock 금지).
> Phase A(설계 루프 산출물 구성) 기록. Phase B(Evaluator 판정)·Phase C(구현+테스트) evidence는 이후 이어서 추가된다 — H-9(검증 순서) 확인용 시계열 기준점.

---

## Phase A — 설계 루프 산출물 구성

### 1. 드라이런 폴더 생성

- 시점: 2026-07-10 17:00 (KST)
- 명령: `mkdir -p dryrun && node ~/.opal/tools/date/date.js datetime`
- 결과: `dryrun/` 디렉토리 생성, 타임스탬프 확인 `2026-07-10 17:00`

### 2. PRD.md / TRD.md / CONTRACT.md 작성 (D2~D4 재현)

- 시점: 2026-07-10 17:00~17:01 (KST)
- 대상: 미니 프로젝트 "hello-cli" — `dryrun/src/hello.sh`가 `hello <name>` 입력 시 `Hello, <name>!` 출력 (src/ 구현은 Phase C에서 수행, 이 시점엔 미생성)
- 생성 파일:
  - `dryrun/PRD.md` (목표·배경·범위·수용 기준·비범위, 15줄 이내)
  - `dryrun/TRD.md` (기술 선택·구현 방식·수용 기준, 15줄 이내)
  - `dryrun/CONTRACT.md` — `references/contract.md` §2 구조(스키마·시그니처·경계 + 기계검증절 + 루브릭절) 준수
    - 기계검증절 검증 명령: `bash dryrun/src/hello.sh World` → stdout `Hello, World!` · exit 0
    - 루브릭절: 계약 완전성 / 계약 일관성 / 설계 정합 3항목 (Likert 1–5, 통과선 ≥4)

### 3. 백로그 생성 (D5 재현 — 배포본 backlog-tool)

- 시점: 2026-07-10 17:01 (KST)
- 명령 1:
  ```
  cd dryrun && bash ~/.opal/tools/backlog-tool/run.sh init . \
    --project-title "hello-cli" --mode agentic \
    --goal "hello.sh 수용기준 전건 GREEN"
  ```
  - 출력: `{"ok": true, "command": "init", "task_path": ".../dryrun", "created_at": "2026-07-10 17:01"}`
- 명령 2:
  ```
  bash ~/.opal/tools/backlog-tool/run.sh add-task . \
    --id T01 --title "hello.sh 구현" --slice "인사 출력 수직 슬라이스" \
    --acceptance '["bash src/hello.sh World가 '\''Hello, World!'\'' 출력+exit 0"]' \
    --area 공통 --priority P0
  ```
  - 출력: `{"ok": true, "command": "add-task", "task_id": "T01", "tasks_count": 1}`
- 명령 3 (렌더 확인):
  ```
  bash ~/.opal/tools/backlog-tool/run.sh show . --format md
  ```
  - 출력:
    ```
    ## 백로그

    > 상태값: pending / in_progress / done / blocked

    | ID | 제목 | 영역 | 우선순위 | 상태 | 의존 |
    |----|------|------|--------|------|------|
    | T01 | hello.sh 구현 | 공통 | P0 | pending | - |
    ```
- 생성 파일: `dryrun/backlog.json` (SSOT), `dryrun/BACKLOG.md` (렌더 미러)

### 4. Phase A 완료 시점

- 시점: 2026-07-10 17:01 (KST)
- 산출물 전체: `dryrun/PRD.md`, `dryrun/TRD.md`, `dryrun/CONTRACT.md`, `dryrun/backlog.json`, `dryrun/BACKLOG.md`, `dryrun/DRYRUN-LOG.md`(본 파일)
- `dryrun/src/hello.sh` 및 `dryrun/TEST-SCENARIO.md`는 미생성 상태 (Phase C 대상)
- 다음 단계: Phase B(Evaluator design-review 판정) 대기

---

## Phase B — Evaluator 설계 검토 (D6/G 게이트 재현, 구현 전)

### 1. QA-SPEC.md evidence

- QA-SPEC.md 파일 mtime: **2026-07-10 17:04:08** (내부 기록 "실행 일시 2026-07-10 17:03")
- 판정 대상: PRD.md, TRD.md, CONTRACT.md, backlog.json(T01 수용기준) — 루브릭절만 (기계검증절은 판정 대상 제외)
- **verdict: pass** — 전 차원 Likert ≥4 (최저 4점: 계약 일관성), drift: no
- Evaluator 발견 사항: backlog.json T01 수용기준이 `bash src/hello.sh World`(dryrun/ 접두어 누락)로 PRD/TRD/CONTRACT 3자와 미세 불일치 — 개선 제안 수준(통과선 미달 아님)

### 2. PM 반영 사항 (backlog.json 손편집 금지 원칙 유지)

- **결정 1**: backlog.json T01 수용기준 텍스트는 그대로 두고(백로그 JSON 손편집 금지), **수용기준 실행 cwd를 `dryrun/`으로 통일 해석**한다 — 즉 `bash src/hello.sh World`는 `dryrun/`이 cwd일 때의 표현이고, CONTRACT.md §4 기계검증절(`bash dryrun/src/hello.sh World`)은 프로젝트 루트 기준 표현이다. 두 표현이 동일 대상을 가리키는지 Phase C §7 GREEN 단계에서 **양쪽 실행으로 동치 확인**한다.
- **결정 2**: test-tool에 `red_confirmed` 갱신 전용 tool-gated 서브명령이 없음(설계 갭) — PM이 후속 개선 과제로 기록. 우회 절차로 **RED를 실관찰 후 `scenario-init --scenarios`에 `red_confirmed:true`를 시드**한다. RED 관찰 시각 < scenario-init 시각 순서를 evidence로 남긴다(§3 참조).

---

## Phase C — 실행 루프 완주 (Loop 2 재현)

### 1. L0 태스크 선택

- 시점: 2026-07-10 17:05 (KST)
- `backlog-tool select-next dryrun` → `{"next_task_id": "T01", ...}`
- `backlog-tool mark dryrun --id T01 --status in_progress` → `{"ok": true, "status": "in_progress"}`

### 2. RED 실관찰 (PM 결정 2 우회 절차)

- 시점: **2026-07-10 17:05 (KST)**
- 명령: `cd dryrun && bash src/hello.sh World`
- 출력: `bash: src/hello.sh: No such file or directory` / **exit 127**
- 판정: RED 확인(파일 부재로 인한 실패) — 구현 전 상태의 실패를 실제로 관찰함

### 3. RED-first 시드 (test-tool scenario-init)

- 시점: **2026-07-10 17:06:01 (KST)** (`test-scenario.json.created_at`)
- 명령: `test-tool scenario-init --task-path dryrun --scenarios '[{"id":"S1","acceptance_ref":"T01-AC1","type":"contract","expected":"Hello, World! + exit 0","red_confirmed":true}]'`
- 출력: `{"ok": true, "command": "scenario-init", "task_id": "dryrun", "scenarios_count": 1}`
- **순서 evidence**: RED 관찰(17:05) < scenario-init(17:06:01) — RED를 먼저 실관찰한 후 red_confirmed를 시드했음을 시각으로 증명

### 4. 음성 확인 — lock 전 scenario-mark 거부

- 시점: 2026-07-10 17:06 (KST)
- 명령: `test-tool scenario-mark --task-path dryrun --id S1 --result pass --evidence "premature"`
- 출력: `{"ok": false, "command": "scenario-mark", "error": "scenario_not_locked"}` (exit code 9)
- 판정: lock 전 result 기록이 도구 레벨에서 차단됨을 확인(self-confirming 방지, H-2)

### 5. scenario-lock

- 시점: **2026-07-10 17:06:12 (KST)** (`locked_at`)
- 명령: `test-tool scenario-lock --task-path dryrun`
- 출력: `{"ok": true, "command": "scenario-lock", "locked": true, "locked_at": "2026-07-10T17:06:12+09:00"}`

### 6. 구현 — dryrun/src/hello.sh

- 시점: **2026-07-10 17:06:18 (KST)** (파일 mtime)
- 내용: 셔뱅(`#!/bin/bash`) + `echo "Hello, $1!"`, 실행권한 부여(`chmod +x`)
- CONTRACT.md §1/§2 준수(입력 `$1` name, 출력 `Hello, <name>!`, exit 0)

### 7. GREEN 확인 — PM 결정 1(cwd 동치) 검증

- 시점: 2026-07-10 17:06 (KST)
- `dryrun/` cwd 기준: `cd dryrun && bash src/hello.sh World` → 출력 `Hello, World!`, **exit 0**
- 프로젝트 루트 기준: `bash tasks/056-260710-opd-oppl-루프-오케스트레이터/dryrun/src/hello.sh World` → 출력 `Hello, World!`, **exit 0**
- 판정: 두 표현(backlog T01 acceptance `bash src/hello.sh World` @dryrun cwd ↔ CONTRACT §4 `bash dryrun/src/hello.sh World` @project root)이 **동일 스크립트·동일 결과를 가리키는 동치**임을 실행으로 확인 — backlog.json 손편집 없이 PM 결정 1 해소

### 8. scenario-mark pass + scenario-status

- 시점: **2026-07-10 17:06:34 (KST)** (`marked_at`)
- 명령: `test-tool scenario-mark --task-path dryrun --id S1 --result pass --evidence "stdout Hello, World! exit 0 (dryrun cwd + project root 양쪽 확인)"`
- 출력: `{"ok": true, "command": "scenario-mark", "scenario_id": "S1", "result": "pass"}`
- `scenario-status` → `{"ok": true, "locked": true, "total": 1, "red_confirmed": 1, "passed": 1, "failed": 0}`

### 9. L∞ 관찰 + L✓ 종료 판정

- 시점: 2026-07-10 17:06 (KST)
- `backlog-tool mark dryrun --id T01 --status done` → `{"ok": true, "status": "done"}`
- `backlog-tool done-check dryrun` → `{"ok": true, "all_done": true, "remaining": [], "done_count": 1, "total": 1}`

### 10. 무진전 가드 evidence (loop-control.md §4/§5 적용)

- 시점: 2026-07-10 17:06 (KST)
- `backlog-tool select-next dryrun` 재호출 → `{"ok": true, "next_task_id": null, "task": null}`
- **판정**: `next_task_id: null`이면 SKILL.md L0 절 규칙("next_task_id: null → done-check로 직행")에 따라 L0로 재진입하지 않고 **L✓ 종료 판정으로 직행**한다 — 무한 회전 없음을 확인. 이는 이미 §9에서 `done-check.all_done:true`로 종료 판정이 내려진 상태와 정합적이며, loop-control.md §4(무진전 감지: 백로그 정체 신호)가 관찰할 "잔여 pending 태스크 없이 select-next가 계속 태스크를 반환" 같은 이상 신호가 없음을 재확인한 것이다.

### 11. H-9 순서 evidence 요약표

검증 2원화(Evaluator 구현 전 → test-agent 구현 후) 순서가 뒤바뀌지 않았음을 시각으로 증명한다.

| 순서 | 이벤트 | 시각 (KST) | 비고 |
|------|--------|-----------|------|
| 1 | QA-SPEC.md 생성 (Evaluator spec-review, **구현 전**) | 2026-07-10 17:04:08 (내부 기록 17:03) | verdict: pass |
| 2 | RED 실관찰 (`src/hello.sh` 부재로 실패) | 2026-07-10 17:05 | exit 127 |
| 3 | scenario-init (RED-first 시드) | 2026-07-10 17:06:01 | red_confirmed:true |
| 4 | scenario-lock | 2026-07-10 17:06:12 | locked:true |
| 5 | `dryrun/src/hello.sh` 구현 생성 | 2026-07-10 17:06:18 | 파일 mtime |
| 6 | scenario-mark pass (test-agent, **구현 후**) | 2026-07-10 17:06:34 | marked_at |

**판정**: 1(QA-SPEC, 구현 전) < 5(구현) < 6(scenario-mark pass, 구현 후) — Evaluator 판정이 항상 구현보다 선행했고, test-agent 판정은 항상 구현보다 후행했다. 순서 역전 없음 (H-9 위반 없음).

### 12. H-7/H-4 evidence 요약

- **H-2 (self-confirming 차단)** — §4 음성 확인: lock 전 `scenario-mark`가 `scenario_not_locked`로 거부됨을 실제로 관찰. RED-first 시드(§3)도 RED를 먼저 실관찰한 뒤에만 이루어져, 시나리오 작성자가 스스로 통과를 보장하는 경로가 없음을 확인.
- **H-3 (backlog.json 동시쓰기 안전성 — 파일 락)** — 본 드라이런은 순차 단일 호출만 수행해 동시쓰기 충돌 재현 대상은 아니지만, 매 `mark`/`add-task` 호출이 `{"ok": true, ...}` 단일 트랜잭션 응답으로 완결되어 파일 락 기반 원자적 갱신과 모순되는 현상(부분 갱신·경합 오류)은 관찰되지 않았다.
- **무진전 감지(loop-control.md §4)** — §10에서 확인한 바와 같이 `select-next`가 `next_task_id: null`을 반환하며 즉시 L✓로 분기, 추가 회전이 발생하지 않았다(무한 루프 신호 없음).

### 13. Phase C 완료 시점

- 시점: 2026-07-10 17:06 (KST)
- 산출물 전체(Phase A~C 누적): `dryrun/PRD.md`, `dryrun/TRD.md`, `dryrun/CONTRACT.md`, `dryrun/backlog.json`, `dryrun/BACKLOG.md`, `dryrun/QA-SPEC.md`, `dryrun/test-scenario.json`, `dryrun/src/hello.sh`, `dryrun/DRYRUN-LOG.md`(본 파일)
- 결과: 전 시나리오 pass(1/1), 백로그 전건 done(all_done:true), 무진전 가드 확인 완료
- 다음 단계: TEST-SCENARIO.md S-090 기입 + §7 최종 판정

---
