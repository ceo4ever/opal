# PROBE-CHECKPOINT — checkpoint 권한 실증 (W-10 / P6)

> 완료 기준: AC-13 · C-10
> checklist_source: `PLAN.md` W-10 행 + Decisions and contracts D-L
> scenario_source: `TEST-SCENARIO.md` S-13 · S-13n (인용: S-14 · S-20)
> 실측 일시: 2026-09-19 20:30~20:33 KST
> 선행 사실: `PROBE-OWNERSHIP.md`(W-8)가 소유. 이 프로브는 재측정하지 않고 인용·대조만 한다.

## 0. 세션 식별자 3종 (H-5 — 착수 직후 선기록)

| 식별자 | 관측값 | 판정 |
|---|---|---|
| hook 봉투 `session_id` (W-10이 주입) | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` | 존재 |
| `OPAL_SESSION_ID` (쉘 변수, 착수 시점) | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` | 존재하나 **export 아님** — §1 함정 |
| 허브 registry `execution_ownership.owner_session_id` | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` | 3종 **전건 일치** |
| 태스크 lease `run/.runtime/owner.json.owner_session_id` | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` | 바이트 일치 |

→ **H-5 판정: PASS.** registry owner와 워커 세션이 같다. 잘못된 세션을 측정할 위험 없음.

## 1. 착수 전 해소한 함정 — `OPAL_SESSION_ID`가 export되지 않은 쉘 변수

`worktree_tool.py:2107`의 소유권 검사는 `os.environ.get("OPAL_SESSION_ID")`를 읽는다. 이 세션은 W-1 수정 **이전에** 부팅했으므로 값은 쉘 변수로만 존재하고 자식 프로세스에 상속되지 않았다.

| 관측 | 명령 | 결과 |
|---|---|---|
| 쉘 변수 속성 (before) | `typeset -p OPAL_SESSION_ID` | `typeset OPAL_SESSION_ID=4e1a2aa2-…` — **`-x` 없음** |
| 자식 프로세스 관측 (before) | `sh -c 'echo $OPAL_SESSION_ID'` | **빈 값** |

그대로 호출하면 `session_id=None` → `checkpoint_ownership_denied / foreign_owner`로 거부된다(H-5가 경고한 상황: 수정이 옳은데도 AC-13이 실패로 보임).

**해소 방법은 손타이핑 우회가 아니라 W-1이 수정한 계약 자체를 경유했다** — 배포본 SessionStart hook에 실제 봉투를 주입해 env 파일을 만들고 그 파일을 `source`했다.

```bash
CLAUDE_ENV_FILE=<scratchpad>/probe-env-w10.sh \
  ~/.opal/.venv/bin/python ~/.opal/tools/ownership-tool/ownership_tool/session_start_hook.py \
  < <scratchpad>/envelope-w10.json
# EXIT=0
```

봉투: `{"session_id":"4e1a2aa2-1800-43e6-af3c-60b86a27b237","cwd":"<worktree_root>","hook_event_name":"SessionStart","source":"startup"}`

- hook이 기록한 env 파일 전문: `export OPAL_SESSION_ID=4e1a2aa2-1800-43e6-af3c-60b86a27b237` — **`export ` 접두 확인**(W-1 계약, `session_start_hook.py:186`).
- `CLAUDE_ENV_FILE`은 **임시 파일**만 사용했고 플랫폼 소유 `~/.claude/session-env/` 아래는 건드리지 않았다.
- 이 hook 재현은 registry를 전이시키지 않았다 — `.meta/task_999.json` mtime이 `2026-09-19T20:22:09`로 **전후 동일**(W-6 멱등 게이트: 이미 자기 세션이 owner이므로 `ownership-set`을 호출조차 하지 않음, `PROBE-OWNERSHIP.md` §인용).

| 관측 | 명령 | 결과 |
|---|---|---|
| 쉘 변수 속성 (after `source`) | `typeset -p OPAL_SESSION_ID` | `export OPAL_SESSION_ID=4e1a2aa2-…` — **`-x` 속성 획득** |
| 자식 프로세스 관측 (after) | `sh -c 'echo $OPAL_SESSION_ID'` | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` |
| registry `owner_session_id`와 대조 | `cmp` (자식 stdout vs registry 값) | **BYTE-IDENTICAL** (exit 0) |

→ 호출 직전 자식 프로세스가 보는 `OPAL_SESSION_ID`가 registry owner와 바이트 일치함을 확증한 뒤에만 checkpoint를 호출했다.

## 2. 사전 확인

| 항목 | 명령 | 결과 | 판정 |
|---|---|---|---|
| 현재 브랜치 ≡ registry `branch` | `git branch --show-current` | `feat/OP-TASK-999` ≡ registry `branch`=`feat/OP-TASK-999` | 일치 |
| 빌드 부산물 부재 (H-4 / S-20) | `ls -d dashboard/frontend/dist` | `No such file or directory` (stage 직전 재확인) | **부재** — 삭제 조치 불요 |
| `dashboard/` working tree | `git status --porcelain dashboard/` | 출력 0줄 | 청정 |
| stage 대상 | `git status --porcelain` | 수정 4건 + 미추적 `tasks/999-…/` | 디스패치 명세와 일치 |

## 3. stage — 범위 밖 0건

`git add --` 로 4파일 + 태스크 폴더만 stage했다. 스테이징 결과 21개 경로(태스크 폴더가 미추적이라 하위 파일이 개별 전개됨):

| stage된 경로군 | 덮는 `--owned-scope` |
|---|---|
| `.opal/brain/pages/entity/ownership-tool.md` | `.opal/brain` |
| `opal/tools/ownership-tool/README.md` · `ownership_tool/session_start_hook.py` · `tests/test_session_start.py` | `opal/tools/ownership-tool` |
| `tasks/999-260919-opds-세션상속-스톱가드-목업검증/…` 17건 | `tasks/999-260919-opds-세션상속-스톱가드-목업검증` |

→ **scope가 stage 전건을 덮는다.** 범위를 넓히지 않았고 `checkpoint_scope_violation`은 발생하지 않았다.

## 4. checkpoint 호출 (1회)

```bash
~/.opal/tools/worktree-tool/run.sh checkpoint \
  --worktree-root /Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_999 \
  --mode agentic --stage execute \
  --owned-scope tasks/999-260919-opds-세션상속-스톱가드-목업검증 \
  --owned-scope opal/tools/ownership-tool \
  --owned-scope .opal/brain \
  --message "chore(999): 세션 상속·registry 부트 등록 실증 체크포인트"
# EXIT=0
```

응답 원문(경로 목록은 §3 표로 대체, 나머지는 전문):

```json
{"ok": true, "error": null, "command": "checkpoint", "task": "999",
 "project_root": "/Volumes/Data/AIStudio/workspace/ai-framework",
 "worktree_root": "/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_999",
 "branch": "feat/OP-TASK-999", "mode": "agentic", "stage": "execute",
 "commit": "a93a5ad8f0b55f9f5aef0cd39b209c4bcf2a7ac6",
 "checkpoint_shas": ["a93a5ad8f0b55f9f5aef0cd39b209c4bcf2a7ac6"],
 "staged": [ … 21개 경로 … ], "registered": true}
```

| 판정 항목 | 관측 | 판정 |
|---|---|---|
| `checkpoint_ownership_denied` | 응답·stderr 전문에 **0건** (`error: null`) | **없음** |
| `commit` | `a93a5ad8f0b55f9f5aef0cd39b209c4bcf2a7ac6` | 채워짐 |
| `checkpoint_shas` (응답) | `["a93a5ad8…"]` | 채워짐 |
| `mode` / `stage` | `agentic` / `execute` — 승인 프롬프트 없이 통과 | D-L 대로(`worktree_tool.py:2160-2166`은 승인을 `interactive`·`semi_agentic`에만 요구) |
| exit code | `0` | 성공 |

## 5. 허브 registry 대조 (S-13 · S-14)

`.opal-worktrees/.meta/task_999.json` → `execution_ownership`

| 필드 | 호출 前 | 호출 後 | 판정 |
|---|---|---|---|
| `checkpoint_shas` | `[]` | `["a93a5ad8f0b55f9f5aef0cd39b209c4bcf2a7ac6"]` | **append 확인** — 응답 `commit`과 동일 SHA |
| `state` | `worktree_session_owned` | `worktree_session_owned` | 불변 |
| `owner_session_id` | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` | 동일 | 불변 |
| `generation` | `3` | `3` | 불변 (역행 0 — PROBE-BASELINE §5.1의 `2`에서 단조 증가한 상태 유지) |
| `failure_reason` | `null` | `null` | 불변 (`hub_owned` 복귀 없음) |
| `launch_receipt` | `{orca, term_216541d9-…, 2026-09-19T08:39:27.966926+00:00, reported_cwd=worktree_root}` | 동일 | **보존** |
| `prompt_receipt` | `{prompt_id=451a5b33401bbc7a, submitted_at=2026-09-19T08:39:27.966926+00:00}` | 동일 | **보존** |
| `branch` (meta 최상위) | `feat/OP-TASK-999` | 동일 | 불변 |

→ **S-13 PASS.** `checkpoint_ownership_denied` 없이 1회 성공했고 성공 SHA가 registry `checkpoint_shas[]`에 append됐다. 불변 4필드(`state`·`owner_session_id`·`generation`·`failure_reason`)와 receipt 2종도 그대로다.

## 6. S-13n — `main` 무변경 증거 (C-10)

| 관측 | 명령 | 결과 |
|---|---|---|
| 현재 브랜치 | `git branch --show-current` | `feat/OP-TASK-999` |
| 최근 이력 | `git log --oneline -3` | `a93a5ad chore(999): 세션 상속·registry 부트 등록 실증 체크포인트` / `aa9c18f chore(145): CLOSE 귀속…` / `7949d57 feat(145): …` |
| 커밋 부모 | `git rev-parse a93a5ad^` | `aa9c18f191e088ca79245cfc1bda7844d9a8df4c` |
| `main` HEAD | `git log --oneline -1 main` | `aa9c18f chore(145): CLOSE 귀속 — MEMORY 히스토리·상태 확정` — **호출 전과 동일, 무변경** |
| 커밋 소재 브랜치 | `git branch --contains a93a5ad -a` | `* feat/OP-TASK-999` **단 1건** |
| main 대비 ahead/behind | `git rev-list --left-right --count main...HEAD` | `0	1` — main이 앞선 커밋 0, 워크트리 브랜치만 1 앞섬 |
| merge·rebase·reset·amend | `git reflog -5` | `commit:` 1건뿐. merge/rebase/amend 항목 **0건** (`HEAD@{1}` reset은 체크포인트 **이전**의 기존 이력) |
| push | `git rev-parse --abbrev-ref '@{u}'` | `fatal: no upstream configured for branch 'feat/OP-TASK-999'` — upstream 미설정, push **0건** |
| 잔여 working tree | `git status --porcelain` | 출력 0줄 (전량 커밋됨) |

→ **S-13n PASS.** 커밋은 `feat/OP-TASK-999`에만 존재하고 `main` commit·merge·push는 **0건**이다. C-10 준수.

## 7. 판정

| 완료 기준 | 판정 | 근거 |
|---|---|---|
| AC-13 | **충족** | §4 `checkpoint_ownership_denied` 0건 + `commit` 채워짐, §5 registry `checkpoint_shas[]` append. 수정 범위의 후속 분리 없음 — 추가 구현 없이 CLI 1회 호출로 실증됨(D-L 예측대로) |
| C-10 | **충족** | §6 — 워크트리 브랜치 한정, `main` commit·merge·push 0건 |
| S-13 | PASS | §4 · §5 |
| S-13n | PASS | §6 |
| S-20 (재확인분) | PASS | §2 — stage 직전 `dashboard/frontend/dist/` 부재 |
| S-14 (대조분) | 불변 확인 | §5 — 불변 4필드 + receipt 2종 |

**부수 관측(가치 있는 사실):** 이번 W-10이 드러낸 것은 단순한 권한 통과가 아니다. 이 세션은 W-1 수정 **이전에** 부팅했기 때문에 `OPAL_SESSION_ID`가 export되지 않은 상태였고(§1), 수정된 hook이 만든 env 파일을 경유해서야 checkpoint가 통과했다. 즉 **W-1의 `export` 계약이 checkpoint 소유권 검사의 실질적 전제**임이 경로로 실증됐다. 수정 전 부팅 세션은 재부팅 또는 env 파일 재적용 전까지 checkpoint를 통과할 수 없다는 사실은 후속 경계에서 운영 문서에 반영할 후보다(이번 범위 밖).
