# TASK 공통 프로세스

> owner: 이 문서 (`harness/task-process.md`)
> 로드 시점: TASK 단계 진입 시 / 태스크 채번 시 / 저장 경로 판단 시
> 역할: 스킬 영역 프로세스 / 태스크 채번 규칙 / 공통 영역 후처리 / 저장 경로 규칙

---

오케스트레이터가 **직접 수행**한다 (워커 디스패치 없음).

#### 스킬 영역 (op-task 프로세스)

1. `op-task/SKILL.md`를 Read한다.
   - 탐색: `{프로젝트}/.opal/skills/op-task/SKILL.md` -> `~/.opal/skills/op-task/SKILL.md`
2. 스킬 프로세스를 따라 TASK.md를 작성한다.

#### 태스크 번호 채번 규칙

신규 태스크 생성 시:
1. 아래를 호출한다 — 도구가 원자적으로 증가·저장한다. **LLM 직접 편집 금지.**
   ```bash
   ~/.opal/tools/memory-tool/run.sh task-number --file <허브 절대경로>/.opal/MEMORY.json --bump
   ```
   - **[MUST] allocator는 항상 허브 절대경로다. cwd에서 추론하거나 상대경로로 전달하지 않는다.** 상대경로는 cwd가 워크트리일 때 cone 사본을 가리켜 `WORKTREE_WRITE_REJECTED`로 이 스텝에서 즉시 실패한다.
2. 응답 JSON의 `last_task_number` 값이 이번 태스크 번호다 (계산하지 않는다).
3. 폴더명 `{NNN}-{YYMMDD}-{스킬약어}-{태스크명}`을 확정한다 (아직 만들지 않는다)
   - `{YYMMDD}`: `node ~/.opal/tools/date/date.js yymmdd` 실행하여 KST 기준 취득
4. 폴더 생성과 TASK.md 작성 순서는 **`--worktree`/`--wt` 유무로만** 갈린다.
   - **`--wt` 없음(기본)**: 허브 `tasks/{폴더명}/`을 생성하고 TASK.md를 작성한 뒤 5번으로 간다. **현행 순서(폴더 → TASK.md → `state init`) 100% 유지 — 어떤 조건부 분기도 실행되지 않는다.**
   - **`--wt` 있음**: 폴더를 만들지 않고 4.5로 간다. worktree를 먼저 만들고, `create` 응답의 `task_path`를 생성한 뒤 그 경로에 TASK.md를 작성한다.

> `.opal/MEMORY.json`이 없고 `.opal/MEMORY.md`만 있으면 도구가 자동 변환 후 처리한다.
> 둘 다 없으면 `memory_json_not_found` — `memory-tool init`을 먼저 실행한다.
> 동시 실행 인스턴스 간 번호 중복 방지는 (LLM이 아닌) `task-number --bump`의 원자적 증가(파일 락 + 임시파일 rename)가 책임진다.

#### 오케스트레이터 공통 영역 (스킬 완료 후 후처리)

3. **STEP 5(오케스트레이터 선택)에서 결정된 스킬약어**를 폴더명과 `state init --skill`에 반영한다. 신규 `template: sdlc-v2` TASK.md에는 스킬 헤더를 쓰지 않는다. legacy TASK를 재개할 때만 기존 헤더를 해석 호환으로 읽는다.
4. **모드 플래그(`--interactive` / `--semi-agentic` / `--agentic`)는 `state init --mode`에만 기록한다** (`interactive` / `semi-agentic` (기본) / `agentic`). 신규 `template: sdlc-v2` TASK.md에는 모드 헤더를 쓰지 않는다.

4.5. **`--worktree`/`--wt` 플래그가 있을 때만 수행한다** (플래그가 없으면 이 스텝 전체를 건너뛰고 4 → 5로 직행한다 — 현행 동작 100% 유지).

   ```bash
   ~/.opal/tools/worktree-tool/run.sh create \
     --project-root <허브 절대경로> \
     --task <NNN> \
     --task-folder {NNN}-{YYMMDD}-{스킬약어}-{태스크명} \
     [--slug <태스크명>] \
     [--skill <약어>]
   ```

   - **[MUST] `create`는 `task_path` 디렉토리를 만들지 않는다 — 경로 계약만 확정한다.** 폴더 생성은 아래 `ok: true` 1의 별도 스텝이며, 건너뛰면 TASK.md 쓰기가 실패한다.
   - `ok: true` → 순서대로 수행한다.
     1. 응답의 `task_path`를 `mkdir -p <task_path>`로 생성한다.
     2. 그 `task_path`에 TASK.md를 작성한다(채번 규칙 4항).
     3. 응답의 `worktree_root` 값을 아래 5번 `state init`의 `--worktree <path>`에 전달한다.

     `warnings[]`가 있으면 그대로 사용자에게 전달한다(**차단하지 않는다**).
   - `ok: false` → **허브 `tasks/{폴더명}/`에 폴더를 생성하고 TASK.md를 작성한 뒤 `--worktree` 없이 5번으로 진행한다**(=`--worktree`를 전달하지 않으므로 `state.json`이 현행 스키마와 동일해진다). 이 시점에는 어느 위치에도 폴더가 없으므로 롤백할 대상이 없고 폴더는 한 위치에만 생긴다. 실패 사유(`error` 코드)를 사용자에게 보고한다. agentic 모드에서는 사용자 확인을 요구하지 않고 자동 계속하되 AGENTIC-LOG.md에 실패 사유를 기록한다.
     - 오류가 `CONFIG_NOT_FOUND`이면 `~/.opal/tools/worktree-tool/run.sh init --project-root <프로젝트> [--dry-run]`을 안내한다. `init`은 독립 `.git` 발견 시 multi-repo, 없으면 monorepo 초안을 만들 뿐 자동 확정하지 않으므로 사용자가 검토·수정한다. 수동 작성은 `~/.opal/templates/worktree-multi-repo.json` 또는 `worktree-monorepo.json`을 복사해 시작한다.
   - 도구는 부분 실패 시 자기가 만든 worktree·브랜치만 스스로 되돌린다(all-or-nothing) — 파이프라인이 정리할 잔여물은 없다.
   - 축 정의 SSOT: `opal/core/references/harness/worktree.md`.
   - 태스크 문서·설정을 해석하는 `task_root`와 채번·귀속 쓰기에만 쓰는 `allocator_root`의 판정 규칙은 `opal/core/references/harness/worktree.md` §task root와 allocator root 계약이 SSOT다. canonical task path의 기계 계약은 worktree-tool metadata/schema가 소유한다.

5. **[필수] `state init`을 호출하여 STATE.md를 생성한다**. 이 단계를 건너뛰면 세션 복원과 상태 추적이 불가능하다. LLM이 직접 작성하는 것은 금지된다 (`harness/state-template.md` §[MUST] 블록).

   ```bash
   ~/.opal/tools/state-tool/run.sh init <task-path> \
     --skill <약어> \
     --mode <interactive|semi-agentic|agentic> \
     [--task-title <태스크 제목>] \
     [--next-action <첫 액션 텍스트>] \
     [--worktree <worktree_root 절대경로>]      ← 4.5가 ok:true를 반환한 경우에만 전달
   ```

   - `<task-path>`: `--wt` 태스크는 4.5가 발급한 **워크트리 안 canonical `task_path`**(허브 `tasks/` 아래가 아니다), 그 외에는 허브 `tasks/{폴더명}` 경로다. cwd나 `.opal-worktrees` 문자열로 추측하지 않는다.
   - `--task-title`: STATE.md 1행 제목 (생략 시 task-path 마지막 디렉토리명)
   - `--next-action`: `state.json` `next_action` 필드 초기값 (조회: `state-tool show`) (생략 시 `"PLAN 단계 진입"`) — 이후 `advance`/`mark`에서도 파이프라인 프론티어 기준으로 자동 갱신되며, 전이 시 동일 플래그로 1회성 오버라이드 가능하다(072)
   - 행 구성의 SSOT는 오케스트레이터 `references/pipeline.json`이며 `--rows-from`으로 지정한다(`--rows-spec`은 인라인 JSON 직접 지정용). SKILL.md 행 표는 사람 열람용 미러이며 `.md` 파싱은 deprecated(090)

   근거: `tasks/134-260501-opp-pipeline-state-tool/TASK.md` F-9 / `PLAN.md` §2.11 G-8 / §2.19.1 / §1.5 M-3

6. `state init` 응답의 `transition_action` / `report_type` / `next_action`을 소비해 보고한다.
   - `report_type=progress_report`이면 비차단 완료 보고만 남기고, `transition_action=continue`에 따라 다음 단계로 즉시 이어간다.
   - `report_type=decision_request`이면 사용자 결정이 필요한 질문으로 보고하고 대기한다.
   - `transition_action=blocked`이면 실행 불가 사유와 필요한 조치를 보고한다.

#### `--wt` 체크포인트 커밋과 merge 경계

`--wt` 태스크의 전용 세션은 `harness/guards.md` §커밋 규칙의 폐쇄된 예외만 소비한다. worktree 여부, canonical task, 현재 branch와 세션 소유권을 registry로 확인하지 못하면 일반 사용자 승인 규칙으로 돌아간다.

1. 단계 작업과 필수 Gate·검증을 먼저 완료한다. 검증 중 발견한 이슈가 권한 범위 안에서 보정되고 재검증을 통과하면 해결된 이슈로 기록만 남기고 파이프라인을 중단하지 않는다.
2. `agentic`은 사용자 판단이 필요한 미해결 사항이 없는 안정 경계에서 PM이 소유 worktree 브랜치에 체크포인트 커밋하고 즉시 다음 단계로 진입한다.
3. `interactive`는 기존 각 단계 사용자 승인 뒤 그 단계 산출물을 체크포인트 커밋하고 다음 단계로 진입한다. `semi-agentic`은 PLAN-equivalent 승인 뒤 명세 체크포인트를 만들고, EXECUTE·TEST 변경은 커밋하지 않고 누적하며, 기존 CLOSE 진입 승인 뒤 누적 구현·테스트 체크포인트를 만든다. 같은 CLOSE 승인은 승인된 CLOSE/finalize 범위의 최종 체크포인트까지 허용하되 merge·push 승인으로 확장되지 않는다. 새 사용자 Gate를 추가하지 않는다.
4. 체크포인트 직전 staged 경로가 canonical task와 해당 worktree의 소유 변경으로 폐쇄되는지 검사한다. staged 변경이 0건이면 체크포인트를 만들지 않고 다음 단계로 진행한다. 성공 SHA는 lifecycle record에 기록하며 자동 amend·rebase·reset은 하지 않는다.
5. `main`·기본 브랜치 commit, worktree branch의 merge·push, 배포와 worktree 제거는 체크포인트 예외 밖이다. 특히 `main`·기본 브랜치 merge는 모드와 무관하게 사용자 승인 뒤 허브에서만 수행한다.

체크포인트 후보 경계는 명세 Gate 완료, 검증된 독립 구현 단위, 전체 회귀 통과와 CLOSE/finalize 직전이며 실제 커밋 여부는 위 모드 규칙이 결정한다. 모든 state 행이나 단순 로그 갱신마다 커밋하지 않는다.

#### 저장 경로 규칙

| 조건 | 저장 경로 |
|------|----------|
| `base_path` 지정 시 (오케스트레이터가 명시 주입) | `{base_path}/` (폴더 구조는 오케스트레이터 정의를 따름) |
| `base_path` 없음 (기본) | `tasks/{NNN}-{YYMMDD}-{스킬약어}-{태스크명}/` |

> **`base_path` 용도**: opsdd와 같이 단일 루트 폴더에 모든 산출물을 통합하는 오케스트레이터에서 활용한다. 기존 opp/opds/opd 등 `base_path`를 주입하지 않는 오케스트레이터는 기본 경로(`tasks/`)를 그대로 사용하므로 동작에 영향 없다.

> **`{태스크명}` 문자 규칙**: **[기본] 한글로 작성한다.** 영문 kebab-case·한글+영문 혼용은 소유자가 명시 요청할 때만 사용한다(상세: `op-task/SKILL.md` §저장 경로). 단 **공백 금지**(셸 안정성), 단어 구분은 하이픈(`-`), 앞 3요소(`{NNN}-{YYMMDD}-{스킬약어}`)는 **ASCII 고정**(파싱 안정성).

```
📋 [TASK] 완료 보고
📎 산출물: tasks/{NNN}-{YYMMDD}-{스킬약어}-{태스크명}/TASK.md
적용 스킬: {약어}
전이: {transition_action} / 보고: {report_type}
다음 액션: {next_action}
```

> 도메인별 추가 확인 필드(문서 유형, 출력 모드 등)는 각 opal-pilot SKILL.md에서 정의.

---
