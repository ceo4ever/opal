# PROBE-REGRESSION — W-11 (P7) 회귀 스위트 실행

- 실행 시각: 2026-09-19
- 코드 루트: `/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_999`
- HEAD: `a93a5ad8f0b55f9f5aef0cd39b209c4bcf2a7ac6`
- 러너: `~/.opal/.venv/bin/python -m pytest`
- 판정: **PASS (All Pass)** — 4개 스위트 전부 exit 0, 실패 0건

## 1. 세션 식별자 3종 (S-21 / H-5)

| 항목 | 값 | 일치 |
|---|---|---|
| `CLAUDE_CODE_SESSION_ID` (env) | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` | 기준 |
| `OPAL_SESSION_ID` (export 여부) | export 됨 — 동일 값 | 일치 |
| registry `execution_ownership.owner_session_id` (`.opal-worktrees/.meta/task_999.json`) | `4e1a2aa2-1800-43e6-af3c-60b86a27b237` | 일치 |

부가: `state=worktree_session_owned`, `generation=3`, `checkpoint_shas=["a93a5ad8f0b55f9f5aef0cd39b209c4bcf2a7ac6"]`.
3종 전부 일치 — 세션 상속 경로에 불일치 없음.

## 2. 사전 확인 (H-4)

`dashboard/frontend/dist/` — 실행 **전** 부재, 실행 **후** 부재. 삭제 조치 없음(애초에 없음).

## 3. 스위트별 결과

각 수치는 스위트 디렉터리 전체 실행 결과다(단일 파일 실행 수치 아님).

| 스코프(디렉터리) | 통과 | 실패 | 기타 | 소요 | exit |
|---|---|---|---|---|---|
| `opal/tools/ownership-tool/tests` | 62 | 0 | — | 1.24s (wall 1s) | 0 |
| `opal/tools/state-tool/tests` | 535 (+339 subtests) | 0 | skipped 3 | 352.10s (wall 353s) | 0 |
| `opal/tools/worktree-tool/tests` | 146 | 0 | — | 115.99s (wall 116s) | 0 |
| `opal/tools/worktree-launcher/tests` | 110 | 0 | skipped 1 | 2.70s (wall 3s) | 0 |

합계: 853 passed (+339 subtests), 0 failed, 4 skipped.

## 4. AC-7 4축 대응 (개별 확인)

| 축 | 담당 테스트 | 결과 |
|---|---|---|
| hook main 경유 E2E | `opal/tools/ownership-tool/tests/test_integration.py` | 7 passed in 0.32s — PASS |
| subprocess 상속 (W-1 신규 단언) | `opal/tools/ownership-tool/tests/test_session_start.py` | 10 passed in 2.81s — PASS |
| state-tool lease/run-log | `opal/tools/state-tool/tests/test_state_tool_ownership.py` | 3 passed in 1.22s — PASS |
| Stop evaluator | `opal/tools/ownership-tool/tests/test_stop_evaluator.py` | 10 passed in 0.24s — PASS |

W-1 신규 단언 실재 확인 (`test_session_start.py`):
- `:123-124` — env 파일 줄이 `export OPAL_SESSION_ID=`로 시작함을 단언(느슨한 `"OPAL_SESSION_ID=" in env_text` 대체).
- `:129-135` — 파일을 `source`한 **자식 프로세스**가 읽은 값이 세션 ID와 바이트 동일함을 `subprocess`로 관측(실제 셸 상속 경계).
- `:165-174` — 셸 메타문자를 포함한 hostile session id도 source 후 자식이 원값 그대로 수신.

## 5. 복귀 경로 단언 3건 (D-K) — [MUST] 확인

`opal/tools/worktree-launcher/tests/test_launcher_core.py`의 `assert eo["owner_session_id"] is None` 3건, 해당 테스트 개별 실행 결과:

| 라인 | 테스트 | 결과 |
|---|---|---|
| :81 | `test_launch_failed_path_reverts_atomically` | PASSED |
| :110 | `test_prompt_failed_path_reverts_atomically` | PASSED |
| :143 | `test_cwd_mismatch_path_reverts_atomically` | PASSED |

`3 passed in 0.46s`. W-6의 registry 부트 등록이 복귀 경로 불변식(실패 시 owner 비움)을 깨지 않음을 확인.

## 6. S-17 (C-3) — hook 자기 환경 미수정

대상: `opal/tools/ownership-tool/ownership_tool/session_start_hook.py` (repo 내 유일 파일)

grep 패턴 `os\.environ\[...\] *=|os\.environ\.update|os\.environ\.setdefault|os\.putenv|setenv|environ\.pop|del os\.environ` → **0 matches**.

파일 내 `os.environ` 전체 참조는 2건뿐이며 둘 다 비수정:
- `:180` 독스트링 — "이 모듈은 자신의 `os.environ`을 수정하지 않는다"
- `:200` `env = os.environ if env is None else env` — 읽기 전용 바인딩

세션 ID 전파는 `_append_session_id()`가 **부모 쉘 프리앰블 파일에 `export ...` 1줄 append**하는 경로에만 존재한다(`handle()`에서 `env_file_path`는 `claude_adapter.ENV_FILE_ENV`로부터 획득). 즉 변경은 파일 내용에만 있고 hook 프로세스 자신의 환경에는 없다. → **PASS**

## 7. S-18 (C-5 · C-8) — 타 슬롯 자산 불가침 (읽기 전용)

| 파일 | sha256 (실행 전 = 실행 후 동일) | mtime |
|---|---|---|
| `.opal-worktrees/.meta/task_128.json` | `49a4bba824202d5147cabc47d9d11b66a8816e4978a16b705739555a312195cb` | 2026-09-13 00:46 |
| `.opal-worktrees/.meta/task_142.json` | `0d5bb4111452fd99605928a171c1f85fa4029c39a9718d58dd2fad62432e9515` | 2026-09-18 17:25 |

4개 스위트 실행 전후 sha256 동일. mtime은 태스크 999 착수(09-19) 이전 시점 그대로.
`git status --porcelain` 변경 목록은 전부 `tasks/999-260919-.../` 하위(AGENTIC-LOG.md, PROBE-BASELINE.md, STATE.md, run-log jsonl, state.json, test-scenario.json, PROBE-CHECKPOINT.md). 태스크 999 외 자산 수정 **0건**. → **PASS**

## 8. S-19 (C-7) — 플랫폼 고유 변수명 격리

- `opal/tools/state-tool/state_tool.py:642-647` `_current_session_id()`는 `os.environ.get("OPAL_SESSION_ID")` **하나만** 읽는다. 다른 변수 폴백 없음.
- `state-tool` 전체에서 `CLAUDE_CODE_SESSION_ID|CLAUDE_ENV_FILE|CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` grep:
  - 프로덕션 코드(`--include=*.py`, `/tests/` 제외): **0건**
  - 단 1건이 `opal/tools/state-tool/tests/test_state_tool_ownership.py:6` 모듈 독스트링(`"OPAL_SESSION_ID(또는 CLAUDE_CODE_SESSION_ID 매핑) 존재 시 ..."`)에 **문자열 설명으로만** 존재 — 코드 참조·환경 조회 아님.
- 세 변수명의 **프로덕션 코드 유일 소유자**: `opal/tools/ownership-tool/ownership_tool/claude_adapter.py` (3종 모두). 그 외 프로덕션 모듈 0건, 나머지 매치는 ownership-tool 테스트/fixture 문서.

판정: **PASS** (테스트 독스트링 1건은 실행 경로 밖의 서술 — 계약 위반 아님, 기록 목적으로 명시)

## 9. 종합

- 실패 0건 → blocked 조건 미해당.
- 소스·테스트 파일 수정 없음, 커밋 없음, Stop hook 미실행, 타 슬롯 미변경.
