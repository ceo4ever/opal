# ownership-tool fixtures (W-2)

이 트리는 태스크 138 W-2가 만든 디스크 fixture 코퍼스다. **테스트 모듈·구현 모듈은 이 트리에
포함되지 않는다**(W-1·W-3~W-6 소유). 여기서는 `.json`/`.md`만 소유한다.

## 플레이스홀더 규약

- `{HUB}` — 허브(allocator root) 절대경로. 실제 값은
  `/Volumes/Data/AIStudio/workspace/ai-framework`(이 환경 기준)였으나 테스트는 이 문자열을
  **하드코딩하지 않고** 임시 디렉터리로 복제한 뒤 그 복제본 경로로 치환해서 사용해야 한다.
- `{WT}` — 워크트리 루트 상위(`.opal-worktrees`) 절대경로. 마찬가지로 임시 디렉터리 복제 후 치환한다.
- 테스트는 fixture를 **직접 수정하지 않는다**. `tempfile.mkdtemp()` 등으로 이 트리를 복제하고,
  복제본 안에서 `{HUB}`/`{WT}` 문자열을 실제 임시 경로로 치환한 뒤 그 복제본에 대해 실행한다.
  (예: `shutil.copytree(FIXTURES_ROOT, tmp_dir)` → 파일 전체를 `text.replace("{HUB}", str(tmp_hub)).replace("{WT}", str(tmp_wt))`)

## 트리 구조와 대응표

| 경로 | 내용 | 대응 S-ID | 대응 AC/C/H | captured |
|---|---|---|---|---|
| `registry/active/WT-127/.meta/task_127.json` | 허브 실물 `.opal-worktrees/.meta/task_127.json` 사본(경로 플레이스홀더화). `task_ownership_version: 2`, `attribution_state` 키 부재(active) | S-3, S-23 | AC-9, AC-25 | 원본 실측(플레이스홀더 치환만) |
| `registry/active/WT-132/.meta/task_132.json` | 허브 실물 `task_132.json` 사본 | S-1, S-3, S-5, S-23 | AC-9, AC-10, AC-25 | 원본 실측 |
| `registry/active/WT-138/.meta/task_138.json` | 허브 실물 `task_138.json` 사본 | S-23 | AC-25 | 원본 실측 |
| `registry/closed/WT-132-CLOSED/.meta/task_132.json` | `attribution_state: "closed"` 대조군(AC-11) | S-2 | AC-11, C-7 | 파생(합성) |
| `registry/legacy/WT-LEGACY/.meta/task_legacy.json` | `task_ownership_version` 부재 legacy meta | S-14 | AC-3, C-12 | 합성 |
| `registry/invalid/invalid_registry.json` | 손상된 JSON(파싱 실패 재현) | S-3 | AC-9 | 합성 |
| `hub/HUB-0/tasks/` | 활성 허브 태스크 0건(빈 디렉터리, `.gitkeep`만) | S-5(대조), S-28 | AC-14 | 합성 |
| `hub/HUB-FOSSIL-AMBIGUOUS/tasks/132-.../state.json` | 허브 실물 `tasks/132-*/state.json` 사본 — `current_status: in_progress`, `transition_action: continue` 파생(state-tool show 실측) | S-1, S-29 | AC-10, AC-16, C-7, D-14 | 원본 실측 |
| `hub/HUB-MULTI/tasks/200-*/state.json`, `201-*/state.json` | 현재 세션 lease 2건에 대응하는 `continue` state 2건 | S-5 | AC-14, C-8, C-11 | 합성 |
| `hub/HUB-TWO-SESSIONS/tasks/210-*/state.json` | 세션 A·B 이원 lease 시나리오의 태스크 X | S-4 | AC-13, C-8 | 합성 |
| `hub/HUB-CLOSED-MERGED/tasks/132-.../state.json` | AC-11 대조군의 허브 merge 사본(허브 실물 기반) | S-2 | AC-11 | 원본 실측 기반 |
| `worktrees/WT-132/tasks/132-.../state.json` | canonical 132의 워크트리측 사본(허브와 바이트 동일, diff 확인함) | S-1, S-3 | AC-9, AC-10 | 원본 실측 |
| `worktrees/WT-132/tasks/{100,105,137}-*/state.json` | 화석 폴더 3건(허브 실물 워크트리 `tasks/` 실재 이름, 전건 `current_status: done`) | S-3 | AC-9, C-6 | 원본 실측 |
| `worktrees/SAME-WORKTREE-TWO-SESSIONS/tasks/220-*/state.json` | 동일 워크트리 이원 세션 시나리오 | S-13 | AC-18, C-11, C-13 | 합성 |
| `runtime/sessions/session-live.json` | D-5 세션 registry 스키마 — live | S-4, S-10~S-12 | C-9, D-5 | 스키마 파생 |
| `runtime/sessions/session-expired.json` | 세션 registry — expired | S-12 | C-9, D-5 | 스키마 파생 |
| `runtime/owner-current-session.json` | hub lease `owner.json` — 현재 세션 소유 | S-4, S-12 | C-8, C-9 | 스키마 파생 |
| `runtime/owner-foreign-session.json` | hub lease — 타 세션 소유(`foreign_owner`) | S-4, S-13 | C-8, AC-13 | 스키마 파생 |
| `runtime/owner-expired-lease.json` | hub lease — TTL 만료(`lease_expired`) | S-5, S-12 | C-8, AC-14 | 스키마 파생 |
| `runtime/stop-guard/stop-guard-sample.json` | stop receipt 스키마 샘플 | S-6 | C-10, D-4 | 스키마 파생 |
| `fingerprint/show-a-baseline.json` | `state-tool show --format json` 실측 원본(이 태스크 138) | S-6 | C-10, D-4, H-7 | 원본 실측 |
| `fingerprint/show-b-status-changed.json` | (a)에서 `execute.implement` 행 `status`만 `done`으로 의미 변경 | S-6 | C-10, D-4 | 원본 실측 기반 파생 |
| `fingerprint/show-c-note-runlog-only.json` | (a)에서 `updated_at`·row `note` 자유문·`run_log.pending_events`만 변경(D-4 제외 필드) — fingerprint는 (a)와 동일해야 함 | S-6 | C-10, D-4 | 원본 실측 기반 파생 |
| `launcher/fake_process-success.json` | launch+prompt receipt 둘 다 성공 | S-15, S-19 | AC-3, AC-7, AC-8, C-13 | 합성 |
| `launcher/fake_process-launch-failed.json` | launch 실패 경로 | S-15 | AC-7, AC-8, C-13 | 합성 |
| `launcher/fake_process-prompt-failed.json` | prompt 제출 실패 경로 | S-15 | AC-7, AC-8, C-13 | 합성 |
| `launcher/fake_process-cwd-mismatch.json` | `reported_cwd` 불일치 경로 | S-15 | AC-7, AC-8, C-13 | 합성 |
| `launcher/orca-json-response.json` | `orca terminal create --json` 응답 가정 샘플. **필드명은 실측 `--help` 플래그(`--worktree`/`--command`/`--title`/`--focus`/`--json`)만 근거로 한 가정**이며 실제 stdout JSON 스키마는 미실측 | S-16 | AC-5, C-2, H-6 | `--help` 플래그만 실측, stdout 스키마는 가정 |
| `hook-payloads/session-start.json` | SessionStart 합성 봉투 | S-10, S-29 | H-1, H-3, C-9 | **합성** (`captured:false`) |
| `hook-payloads/pretooluse.json` | PreToolUse 합성 봉투 | S-13 | AC-18, H-4 | **합성** |
| `hook-payloads/posttooluse.json` | PostToolUse 합성 봉투 | S-12 | C-9, H-1 | **합성** |
| `hook-payloads/stop.json` | Stop 합성 봉투(`stop_hook_active=false`) | S-1, S-2, S-5, S-6 | AC-15, AC-16, H-1 | **합성** |
| `hook-payloads/sessionend.json` | SessionEnd 합성 봉투 | S-12 | C-9, C-23 | **합성** |
| `hook-payloads/ENV-CAPTURE.md` | H-2 1차 실측 — 이 워커(서브에이전트) Bash의 `OPAL_SESSION_ID`/`CLAUDE_ENV_FILE`/`CLAUDE*` env 관측 원문 | S-29 | H-2 | **원본 실측**(이 세션) |

## captured 여부 요약

- **원본 실측**: 허브 실물 파일을 Read해 경로만 플레이스홀더로 치환한 것. registry meta 3종, `HUB-FOSSIL-AMBIGUOUS`/`WT-132` state.json 계열, `fingerprint/show-a-baseline.json`(및 그 파생 b/c), `ENV-CAPTURE.md`.
- **스키마 파생**: PLAN D-5가 정의한 필드 목록을 그대로 따라 만든 합성 레코드(runtime/*, launcher/*).
- **합성**: 이 세션에서 실제 캡처할 수 없는 대상(hook 봉투 5종, HUB-MULTI/TWO-SESSIONS/SAME-WORKTREE 등 다중 세션 시나리오)을 Claude Code hooks 문서 공통 필드 스키마로 조립한 것. hook 봉투는 각 파일에 `"_fixture": {"captured": false, ...}`로 명시했다. **S-29(W-6 배포 후 실제 세션 1회 캡처)에서 실캡처로 교체된다.**

## H-2 실측 결과 (요약)

`ENV-CAPTURE.md` 참조. 이 워커(opal-be-agent 서브에이전트) 세션에서 `OPAL_SESSION_ID`·`CLAUDE_ENV_FILE`
모두 unset이었다(관측 사실만, 해석은 W-7/W-8/W-9 EXECUTE 워커가 판단).

## 사용법

```python
import shutil, tempfile, pathlib

FIXTURES_ROOT = pathlib.Path(__file__).parent  # 이 README와 같은 디렉터리
tmp = pathlib.Path(tempfile.mkdtemp())
shutil.copytree(FIXTURES_ROOT, tmp, dirs_exist_ok=True)
hub_tmp = tmp / "hub_root"
wt_tmp = tmp / "wt_root"
for p in tmp.rglob("*.json"):
    text = p.read_text(encoding="utf-8")
    text = text.replace("{HUB}", str(hub_tmp)).replace("{WT}", str(wt_tmp))
    p.write_text(text, encoding="utf-8")
```

테스트는 이 복제본에 대해서만 읽고 쓰며, `opal/tools/ownership-tool/tests/fixtures/` 원본은 항상
읽기 전용으로 남는다.
