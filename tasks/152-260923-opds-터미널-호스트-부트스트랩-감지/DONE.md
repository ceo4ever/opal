# DONE: 터미널 호스트 부트스트랩 감지와 worktree 기동 연계

## 결과

OPAL bootstrap이 현재 프로세스가 실행 중인 터미널 호스트를 결정론적으로 판별해 세션 컨텍스트로 소비한다. 신설 `terminal-context` 도구(Python 표준 라이브러리 + 얇은 `run.sh`)는 `host`·`multiplexers`·`confidence`·`evidence` 4키 JSON만 반환한다. 판별 우선순위는 명시 호스트 신호, 프로세스 조상, tmux client 조상, `TERM_PROGRAM`, `unknown` 순이다. 프로세스 조상은 실행 파일 basename 또는 `.app` 번들 이름이 정확히 일치할 때만 호스트로 인정하므로, 명령행 인자에 앱 이름이 들어 있어도 호스트가 바뀌지 않는다. 설치 여부나 다른 앱의 실행 상태도 판정에 쓰지 않으며, 비밀값·socket capability·원시 환경변수 값은 출력하지 않는다.

4종 bootstrapper(claude·codex·cursor·gemini)는 설정·marker 게이트 뒤 허용된 세션(`session.assistant`·`session.project`)에서만 판별기를 1회 호출한다. `bootstrap: off`와 `[WORKER]`의 무로드 계약은 그대로 유지했다.

`worktree-launcher`에 cmux adapter(launch·read·close 3동사)를 추가하고 적합성 suite 대상에 넣었다. `--wt` 기동은 감지한 host를 읽어 지원 adapter만 `--adapter`로 명시 주입한다. tmux는 선택을 바꾸지 않고, unknown·미지원 host는 다른 앱으로 추측 폴백하지 않은 채 비차단 실패로 허브 세션을 유지한다. cmux close는 명시 workspace handle 하나만 닫고 worktree 경로 기반 광역 close는 거부한다. worktree 생성·state 초기화·lease 이관·허브 복귀 순서는 바꾸지 않았다.

opt-in live 대조(`OPAL_LIVE_CMUX=1`)가 실물 cmux 응답이 `OK workspace:<n>` 한 줄임을 확인했다. 이에 맞춰 adapter 파싱과 fixture를 실측 형식으로 교정했으며, 접두 없는 `workspace:<n>`은 거부한다.

## 변경 파일

- `opal/tools/terminal-context/terminal_context.py` (신규)
- `opal/tools/terminal-context/run.sh` (신규)
- `opal/tools/terminal-context/README.md` (신규)
- `opal/tools/terminal-context/tests/test_terminal_context.py` (신규)
- `opal/tools/worktree-launcher/worktree_launcher/adapters/cmux.py` (신규)
- `opal/tools/worktree-launcher/worktree_launcher/cli.py`
- `opal/tools/worktree-launcher/README.md`
- `opal/tools/worktree-launcher/tests/test_adapter_cmux.py` (신규)
- `opal/tools/worktree-launcher/tests/test_adapter_conformance.py`
- `opal/tools/worktree-launcher/tests/test_cli.py`
- `opal/tools/ownership-tool/tests/fixtures/launcher/cmux-workspace-create-response.json` (신규)
- `opal/tools/ownership-tool/tests/fixtures/launcher/cmux-workspace-read-response.json` (신규)
- `opal/tools/ownership-tool/tests/fixtures/launcher/cmux-workspace-close-response.json` (신규)
- `opal/core/AGENT.md`
- `opal/core/references/harness/task-process.md`
- `opal/core/references/harness/worktree.md`
- `opal/core/references/tools.md`
- `opal/bootstrapper/claude-bootstrap.md`
- `opal/bootstrapper/codex-bootstrap.md`
- `opal/bootstrapper/cursor-bootstrap.mdc`
- `opal/bootstrapper/gemini-bootstrap.md`
- `scripts/install-mac.sh`
- `scripts/tests/task113_bootstrap_audit.py`
- `docs/ARCHITECTURE.md`
- `docs/PROJECT.md`

## 검증

- `~/.opal/.venv/bin/python -m pytest opal/tools/terminal-context/tests -q` — 11 passed
- `~/.opal/.venv/bin/python -m pytest opal/tools/worktree-launcher/tests/ -q` — 143 passed, 4 skipped (live 2건 opt-in skip, cmux 원문 계약 skip 2건)
- `~/.opal/.venv/bin/python -m pytest opal/tools/ownership-tool/tests/test_integration.py -q` — 16 passed
- `OPAL_LIVE_CMUX=1 ... pytest tests/test_adapter_cmux.py -k live` — 반복 실행 전건 pass, 전후 `cmux --id-format both workspace list` UUID 비교 잔존 0
- `python3 scripts/tests/task113_bootstrap_audit.py --mode source|installed|all` — 전부 exit 0, `ok:true`
- 소유자 installer 재배포 후 설치본 cmux adapter·cli·terminal-context 바이트 parity 일치, 설치본 `terminal-context/run.sh` 4키 JSON 반환
- `test-tool scenario-status` — S-1~S-5 5/5 pass (real-usage), RED 3/3 확인
- `state-tool validate` violations 0, `code-scan validate --changed` ok (newly_uncovered 0), `state-tool verify --code-scan-citation-check` pass, 컨벤션 진단 Critical/High 0

## 회고적 학습 후보

.opal/brain/pages/concept/terminal-host-detection-from-own-process-lineage.md
.opal/brain/pages/concept/live-cli-contrast-catches-fabricated-fixtures.md

## 참고

- ownership-tool 결함(별도 태스크 권고): 세션 안에서 실행한 `claude mcp get/list`가 SessionEnd 훅을 발화하고, `ownership_core.resolve_session_id`가 hook 봉투보다 상속 env `OPAL_SESSION_ID`를 우선해 부모 세션 lease를 해제하고 registry를 닫는다. 재현 실험으로 확인했다. 수정 배포 전까지 installer는 Claude 세션 밖 터미널에서 실행한다.
- test-tool 결함 2건: 비-pass verdict가 계약 검증 없이 저장돼 spec 전체가 `scenario_contract_invalid`로 교착될 수 있다. assertion은 `expected == actual` 문자열 일치만 판정하므로 기대값을 구체 값으로 적어야 한다.
- 이번 TEST 중 `test-scenario.json`의 S-5 `observed_executors` 1필드를 소유자 승인 하에 수동 복구했다(교착 해소 목적, 판정은 이후 test-tool로 재기록).
- 로컬 PM 개선 후보 1건(워크트리에서 improve-tool local 기록 불가로 여기 보존): lease 소유 세션 생존은 `.opal/run/.runtime/sessions` 레코드와 전체 claude 프로세스의 cwd(lsof)를 대조해 판정한다. `ps`를 `--session-id` 인자로만 거르면 같은 worktree의 다른 탭을 놓친다. 살아 있는 세션이면 해제 대신 그 탭의 `/exit`을 먼저 권한다.
- FW 개선 후보 3건은 `~/.opal/fw-inbox/`에 기록했다: ownership-tool 세션 ID 해석 우선순위, test-tool 비-pass verdict 무검증 저장, improve-tool 워크트리 local 기록 실패.
