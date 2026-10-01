---
template: sdlc-v2
---
# PLAN: 터미널 호스트 부트스트랩 감지와 worktree 기동 연계

> 입력: [TASK.md](TASK.md), [AGENTIC-LOG.md](AGENTIC-LOG.md)

## 참조 문서

| # | 유형 | 경계 | 참조 이유 |
|---|---|---|---|
| D-1 | 설계 | `opal/core/AGENT.md` | setting·marker 스킵 게이트와 session bootstrap 순서 |
| D-2 | 설계 | `opal/core/references/harness/task-process.md` | `--wt` 생성→state init→launcher 순서와 비차단 복귀 |
| D-3 | 설계 | `opal/core/references/harness/worktree.md` | canonical worktree 경로와 launcher adapter 소유권 |
| D-4 | 규칙 | `docs/CONVENTIONS.md` | source-first 배포, `@header`, 플랫폼 분기 격리 |
| D-5 | 소스 | `opal/tools/worktree-launcher/worktree_launcher/cli.py` | 폐쇄 adapter 목록과 명시 주입 경계 |
| D-6 | 소스 | `opal/tools/worktree-launcher/worktree_launcher/adapters/orca.py` | 3동사 보고 스키마와 subprocess seam |
| D-7 | 소스 | `scripts/tests/task113_bootstrap_audit.py` | 4종 bootstrapper 동일성·스킵 순서·설치본 parity |
| D-8 | 실측 | `cmux --help` (2026-09-23) | `new-workspace --cwd --command`, `read-screen`, `close-workspace`, 자동 환경변수 계약 |

## Approach

판별과 기동을 두 계층으로 나눈다. 신설 `terminal-context` 도구는 현재 프로세스에 결부된 환경과 조상 계보만 사용해 `host`, `multiplexers`, `confidence`, `evidence` JSON을 만든다. bootstrapper는 disabled/worker 게이트 통과 후 이 JSON을 세션 컨텍스트로 유지한다. `--wt` 스텝 5.5는 실제 기동 직전에 동일 도구를 다시 읽어 stale 판정을 피하고, `host` 값과 정확히 같은 지원 adapter만 `--adapter` 인자로 명시 주입한다.

code-scan `target` 결과는 신설 `terminal_context.py`·`adapters/cmux.py`와 기존 `task113_bootstrap_audit.py`·`install-mac.sh`·`opal/core/AGENT.md` 모두 `write_to=inline`, `reason=header_source_inline`이다. 따라서 생성·수정하는 code-scan 대상에 inline `@header` 설명을 함께 갱신한다.

## Decisions and contracts

| 결정 | 변경 후 계약 | 근거 |
|---|---|---|
| D-A. 출력은 4필드 폐쇄 스키마다 | `host: str`, `multiplexers: list[str]`, `confidence: high|medium|low`, `evidence: list[str]` 외의 키를 방출하지 않는다. evidence는 `env:CMUX_SURFACE_ID`, `ancestor:Orca`, `tmux:client_ancestor`, `env:TERM_PROGRAM` 같은 신호명만 담고 값은 담지 않는다 | 보안 가능 값을 노출하지 않으면서 사후 판정 근거는 남긴다 |
| D-B. 호스트 우선순위는 명시 신호 → 직접 조상 → tmux client 조상 → `TERM_PROGRAM` → `unknown` | `OPAL_TERMINAL_HOST` 허용값(`cmux`, `orca`), cmux 자동 변수, 실행 조상 이름·경로, tmux client PID 조상, 정규화된 `TERM_PROGRAM` 순서다. 설치 경로·전역 프로세스·프로젝트 등록은 조회하지 않는다 | cmux가 Ghostty를 내장하여 `TERM_PROGRAM` 단독 판정이 잘못될 수 있고, tmux server 계보는 호스트를 잃으므로 client 계보가 필요하다 |
| D-C. multiplexer는 adapter 선택에 쓰지 않는다 | `TMUX` 존재 또는 계보의 tmux는 `multiplexers:["tmux"]`로만 보고하고, `host` 결정은 그 밖 호스트 신호로 한다 | tmux는 터미널 앱이 아니라 중간 계층이다 |
| D-D. `--wt` 소비자는 adapter 명을 추측하지 않는다 | 실행 직전 감지 결과의 `host` ≡ `SUPPORTED_ADAPTERS` 키일 때만 launcher를 호출한다. `unknown`·일반 터미널·미지원 host는 `fallback_attempted:false`로 허브 세션이 계속한다 | 다른 앱이 설치·실행 중이라는 이유로 현재 host를 바꾸면 안 된다 |
| D-E. cmux adapter는 cmux CLI 3동사를 감싼다 | launch=`cmux new-workspace --name <task> --cwd <wt> --command <command> --focus true`, read=`cmux read-screen --workspace <handle> --lines <limit>`, close=`cmux close-workspace --workspace <handle>`. stdout workspace ref가 handle이며 launcher가 생성한 해당 workspace만 닫는다 | 현재 cmux CLI의 공개 인자와 신원 경계를 그대로 쓴다 |
| D-F. bootstrap 스킵 게이트를 보존한다 | terminal context 호출은 `bootstrap: off` 및 `[WORKER]` 반환 후, assistant/project event load와 함께 읽히는 공통 bootstrap 영역에만 둔다. 호출 실패는 OPAL 필수 bootstrap 누락으로 보고한다 | disabled/worker가 아무 전역 문서·도구도 읽지 않는 기존 계약을 유지한다 |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. terminal-context 감지기 | PM | `opal/tools/terminal-context/{terminal_context.py,run.sh,README.md,tests/test_terminal_context.py}` | Python 표준 라이브러리로 D-A~D-C 우선순위·스키마를 구현하고 process/env/tmux seam을 fixture로 검증한다. `run.sh`는 venv Python이 있으면 우선하고 system `python3`로 폴백하는 얇은 wrapper다 | 없음 | P1 | AC-1, AC-2, AC-5, C-1, C-2, C-4 |
| W-2. bootstrap 소비와 배포 감사 | PM | `opal/core/AGENT.md`, `opal/bootstrapper/{claude-bootstrap.md,codex-bootstrap.md,cursor-bootstrap.mdc,gemini-bootstrap.md}`, `scripts/install-mac.sh`, `scripts/tests/task113_bootstrap_audit.py` | 4종 body에 D-F 호출·세션 컨텍스트 보유를 동일하게 추가하고, 스킵 앞 미호출·설치본 parity·신설 run.sh 실행 권한을 검증한다 | W-1 | P2 | AC-3, AC-6, C-3, C-6 |
| W-3. cmux adapter 및 폐쇄 목록 확장 | PM | `opal/tools/worktree-launcher/worktree_launcher/adapters/cmux.py`, `.../cli.py`, `.../tests/test_adapter_cmux.py`, `.../tests/test_adapter_conformance.py`, `.../tests/test_cli.py` | D-E 3동사, 단일 workspace handle, 명령 argv prompt receipt, 실패 dict, `fallback_attempted:false`를 구현하고 `cmux` 명시 주입을 적합성 suite에 추가한다 | W-1 | P2 | AC-4, AC-5 |
| W-4. `--wt` host 소비 계약 | PM | `opal/core/references/harness/{task-process.md,worktree.md}`, `opal/tools/worktree-launcher/README.md` | 스텝 5.5가 terminal context를 재감지·읽고 지원 host만 `--adapter` 명시 인자로 전달하는 명령·실패 계약을 적는다. multiplexer·unknown·오탐 금지를 명시한다 | W-1, W-3 | P3 | AC-4, AC-5, C-5 |
| W-5. 문서·아키텍처 정합화 | PM | `docs/ARCHITECTURE.md`, `opal/core/references/tools.md`, `opal/tools/worktree-launcher/README.md`, 신설 tool README | host·multiplexer 모델, 판별 근거, adapter 선택 경계, 비지원 폴백 없음, source→installed 배포를 사용자 계약으로 고정한다 | W-2~W-4 | P4 | AC-6, C-4, C-6 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. tmux 안의 shell 조상이 tmux server에서 끝나 실제 host를 잃을 수 있다 | tmux client 저편의 host 판별 | `host=unknown`이 되어 `--wt` launcher가 기동되지 않는다 | `tmux display-message -p '#{client_pid}'` 결과의 조상을 별도로 걷고, 실패하면 추측 없이 다음 근거로 내려간다 |
| H-2. cmux stdout 형식 또는 CLI 버전이 변하면 workspace handle 파싱이 깨진다 | cmux workspace launch/read/close 신원 연결 | 생성된 workspace를 읽거나 닫지 못한다 | 첫 non-empty line의 단일 ref만 허용하고 그 밖은 `response_unparsable`; subprocess fixture와 opt-in live 검증을 분리한다 |
| H-3. bootstrap 호출을 marker 판정 전에 두면 disabled/worker 무로드 계약을 깨뜨린다 | setting·marker skip gate | 세션 스킵이 회귀하고 작은 프로세스 호출도 발생한다 | 4종 bootstrap body 순서와 off/worker 모의 실행을 audit로 고정한다 |
| H-4. bootstrap 시점 결과를 오래 재사용하면 tmux attach·host 전환 후 stale할 수 있다 | `--wt` adapter 선택의 현재성 | 잘못된 adapter를 기동한다 | bootstrap은 컨텍스트 제공, `--wt` 기동 직전에는 동일 판별기를 재실행해 최종 host를 소비한다 |

## Release and recovery

- P1 감지기→P2 bootstrap·adapter→P3 harness 소비→P4 문서 순으로 적용한다.
- source 단위·계약 테스트와 bootstrap audit를 먼저 통과한 뒤 `scripts/install-mac.sh`로 설치본을 동기화하고 parity를 검증한다. `~/.opal` 파일은 직접 편집하지 않는다.
- 실패 시 신설 bootstrap 호출과 cmux adapter 등록을 함께 돌려 source·installed drift를 남기지 않는다. 생성된 사용자 workspace는 handle이 확인된 경우에만 정밀 회수한다.
