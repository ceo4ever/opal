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
   ~/.opal/tools/memory-tool/run.sh task-number --file .opal/MEMORY.json --bump
   ```
2. 응답 JSON의 `last_task_number` 값이 이번 태스크 번호다 (계산하지 않는다).
3. 태스크 폴더를 생성한다 (`tasks/{NNN}-{YYMMDD}-{스킬약어}-{태스크명}/`)
   - `{YYMMDD}`: `node ~/.opal/tools/date/date.js yymmdd` 실행하여 KST 기준 취득
4. TASK.md를 작성한다

> `.opal/MEMORY.json`이 없고 `.opal/MEMORY.md`만 있으면 도구가 자동 변환 후 처리한다.
> 둘 다 없으면 `memory_json_not_found` — `memory-tool init`을 먼저 실행한다.
> 동시 실행 인스턴스 간 번호 중복 방지는 (LLM이 아닌) `task-number --bump`의 원자적 증가(파일 락 + 임시파일 rename)가 책임진다.

#### 오케스트레이터 공통 영역 (스킬 완료 후 후처리)

3. **STEP 5(오케스트레이터 선택)에서 결정된 스킬약어**를 폴더명과 `state init --skill`에 반영한다. 신규 `template: sdlc-v2` TASK.md에는 스킬 헤더를 쓰지 않는다. legacy TASK를 재개할 때만 기존 헤더를 해석 호환으로 읽는다.
4. **모드 플래그(`--interactive` / `--semi-agentic` / `--agentic`)는 `state init --mode`에만 기록한다** (`interactive` / `semi-agentic` (기본) / `agentic`). 신규 `template: sdlc-v2` TASK.md에는 모드 헤더를 쓰지 않는다.

4.5. **`--worktree`/`--wt` 플래그가 있을 때만 수행한다** (플래그가 없으면 이 스텝 전체를 건너뛰고 4 → 5로 직행한다 — 현행 동작 100% 유지).

   ```bash
   ~/.opal/tools/worktree-tool/run.sh create \
     --project-root <프로젝트 절대경로> \
     --task <NNN> \
     [--slug <태스크명>] \
     [--skill <약어>]
   ```

   - `ok: true` → 응답의 `worktree_root` 값을 아래 5번 `state init`의 `--worktree <path>`에 전달한다. `warnings[]`가 있으면 그대로 사용자에게 전달한다(**차단하지 않는다**).
   - `ok: false` → **태스크 폴더·TASK.md를 롤백하지 않는다.** `--wt` 없이 5번으로 진행하고(=`--worktree`를 전달하지 않으므로 `state.json`이 현행 스키마와 동일해진다), 실패 사유(`error` 코드)를 사용자에게 보고한다. agentic 모드에서는 사용자 확인을 요구하지 않고 자동 계속하되 AGENTIC-LOG.md에 실패 사유를 기록한다.
     - 오류가 `CONFIG_NOT_FOUND`이면 `~/.opal/tools/worktree-tool/run.sh init --project-root <프로젝트> [--dry-run]`을 안내한다. `init`은 독립 `.git` 발견 시 multi-repo, 없으면 monorepo 초안을 만들 뿐 자동 확정하지 않으므로 사용자가 검토·수정한다. 수동 작성은 `~/.opal/templates/worktree-multi-repo.json` 또는 `worktree-monorepo.json`을 복사해 시작한다.
   - 도구는 부분 실패 시 자기가 만든 worktree·브랜치만 스스로 되돌린다(all-or-nothing) — 파이프라인이 정리할 잔여물은 없다.
   - 축 정의 SSOT: `opal/core/references/harness/worktree.md`.
   - 워크트리에서 허브 고정 데이터(`tasks/`·`.opal/`)를 참조하는 경로 판정 규칙은 `opal/core/references/harness/worktree.md` §허브 루트 해석 규칙이 SSOT다.

5. **[필수] `state init`을 호출하여 STATE.md를 생성한다**. 이 단계를 건너뛰면 세션 복원과 상태 추적이 불가능하다. LLM이 직접 작성하는 것은 금지된다 (`harness/state-template.md` §[MUST] 블록).

   ```bash
   ~/.opal/tools/state-tool/run.sh init <task-path> \
     --skill <약어> \
     --mode <interactive|semi-agentic|agentic> \
     [--task-title <태스크 제목>] \
     [--next-action <첫 액션 텍스트>] \
     [--worktree <worktree_root 절대경로>]      ← 4.5가 ok:true를 반환한 경우에만 전달
   ```

   - `--task-title`: STATE.md 1행 제목 (생략 시 task-path 마지막 디렉토리명)
   - `--next-action`: `state.json` `next_action` 필드 초기값 (조회: `state-tool show`) (생략 시 `"PLAN 단계 진입"`) — 이후 `advance`/`mark`에서도 파이프라인 프론티어 기준으로 자동 갱신되며, 전이 시 동일 플래그로 1회성 오버라이드 가능하다(072)
   - 행 구성의 SSOT는 오케스트레이터 `references/pipeline.json`이며 `--rows-from`으로 지정한다(`--rows-spec`은 인라인 JSON 직접 지정용). SKILL.md 행 표는 사람 열람용 미러이며 `.md` 파싱은 deprecated(090)

   근거: `tasks/134-260501-opp-pipeline-state-tool/TASK.md` F-9 / `PLAN.md` §2.11 G-8 / §2.19.1 / §1.5 M-3

6. 사용자에게 보고하고 다음 단계 승인을 받는다.

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
다음 단계({다음 단계명})로 넘어갈까요?
```

> 도메인별 추가 확인 필드(문서 유형, 출력 모드 등)는 각 opal-pilot SKILL.md에서 정의.

---
