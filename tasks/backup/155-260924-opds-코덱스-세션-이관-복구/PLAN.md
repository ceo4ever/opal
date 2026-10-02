---
template: sdlc-v2
---
# PLAN: 코덱스 세션 이관 복구

> 입력: [TASK.md](TASK.md). 실행 주체: PM. 기존 task_155와 feat/OP-TASK-155 재개.

## Approach

공개 ownership CLI와 lease 단일 writer를 유지하면서 플랫폼 신원 해석과 시작 경계를 보완한다. 허브와 다른 실제 Codex ID로 기존 pending lease claim 및 heartbeat를 관측했고, 공개 ownership-set으로 registry를 정합시켰다 (`run/resume-session-start.json`, `run/resume-heartbeat.json`). 이 임시 복구를 제품 수정 성공으로 계산하지 않는다.

코드맵 선조회: `code-scan search 'ownership|worktree.launcher' --project-root <source>`에서 ownership_core(util/opal-pipeline), launcher_core(util/opal-workspace), worktree_tool(interface)와 CLI 소비자를 확인했다. brain-tool search 'ownership Codex' 결과는 0건이다. 실제 계약은 `opal/tools/ownership-tool/ownership_tool/ownership_core.py:352`, `opal/tools/worktree-launcher/worktree_launcher/launcher_core.py:187`, `opal/tools/worktree-tool/worktree_tool.py:1911`을 읽어 확인했다.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| 플랫폼 신원 | OPAL 중립값 → 기존 Claude adapter → Codex adapter → payload. Codex adapter는 CODEX_SESSION_ID만 지원하고 thread ID를 대체값으로 쓰지 않는다. | C-1/C-2. 공식 `openai/codex`의 `core/src/exec_env.rs` inject_session_env는 공유 root-session을 주입하며 process_manager는 thread를 별도 주입한다. 공개 main과 설치본 0.154.0의 동일성은 주장하지 않는다. |
| 기동 신원 고정 | launcher preflight에서 명시 owner 또는 공통 해석기 신원을 한 번 확정하고 handoff와 모든 cancel에 같은 명시 ID를 전달한다. 미해석은 상태 변경 전에 거부하고 adapter·가용 source 이름만 진단한다. | AC-1/2/5, launcher_core.py:326. |
| 부모 상속 차단 | terminal에서 실행하는 명령을 중립 session-launch 진입점으로 감싸 OPAL 및 플랫폼 신원 변수를 adapter가 제거한 뒤 원래 명령을 실행한다. 사용자 설정 템플릿을 덮지 않는다. | C-3. 일반 CLI OPAL 우선순위와 새 세션의 신원 경계를 분리한다. |
| Codex 정식 시작 | Codex bootstrap이 공개 ownership-tool codex-start를 현재 절대 cwd에서 호출한다. adapter가 실제 native ID를 payload로 만들어 기존 session_start 및 heartbeat 경로를 사용한다. OPAL 상속 충돌은 명시 오류이며 임의 ID 생성·환경 파일 조작은 없다. | 기존 README §SessionStart, 공식 Hooks는 payload session_id를 지원하나 env export 인터페이스는 확인되지 않음. 추가 hook trust 설정 없이 기존 bootstrap/install 경로 사용. |
| registry 관측 | 공개 ownership-set에 lease owner 관측 옵션을 추가한다. registry lock 안에서 live lease owner를 읽어 반영하고 pending/unowned는 빈 owner로 둔다. launcher 최종 전이에 사용하여 허브 ID 잔존과 시작 순서 race를 방지한다. 늦은 시작은 기존 session_start의 빈 owner 등록 경로를 사용한다. | C-5, session_start_hook.py:115, worktree_tool.py:1825. registry는 writer 권한이 아니다. |
| 신원 소비 | worktree checkpoint도 공통 해석기를 사용한다. 훅 5종은 payload-only를 유지한다. | C-1/C-3, worktree_tool.py:2140. |

[MUST] `docs/CONVENTIONS.md` §배포 경계: `~/.opal/` 배포 파일을 직접 편집하지 않는다. source→정식 install→설치본 검증 순서만 사용한다.

[MUST] `TASK.md` C-6: 실제 Orca/Codex 실행 증거를 mock 성공으로 대체하지 않는다. merge/push는 하지 않는다.

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. 신원과 시작 경계 | PM | `opal/tools/ownership-tool/ownership_tool/codex_adapter.py`, `ownership_core.py`, `claude_adapter.py`, `cli.py` (동일 패키지), `opal/bootstrapper/codex-bootstrap.md`, `opal/tools/ownership-tool/tests/test_codex_identity.py`, `opal/tools/state-tool/state_tool.py`, `opal/tools/state-tool/tests/test_state_tool_ownership.py` | native resolver·source-name 진단·session-launch env 정리·codex-start 구현, payload-only 보존. state-tool 상태 전이·run-log actor의 신원 소비도 공통 resolver에 연결. RED 테스트 이후 구현. | 없음 | P1 | AC-1, AC-3, AC-6, C-1, C-2, C-3 |
| W-2. 이관 lifecycle | PM | `opal/tools/worktree-launcher/worktree_launcher/launcher_core.py`, `opal/tools/worktree-tool/worktree_tool.py`, `opal/tools/worktree-launcher/tests/test_codex_handoff.py`, 기존 관련 테스트 | 명시 ID 고정 전달, preflight·실패 cause 보존, 정리 및 원복 유지, 실제 lease owner registry 반영, checkpoint 공통 신원 사용. | W-1 | P2 | AC-2, AC-3, AC-4, AC-5, C-4, C-5 |
| W-3. 계약·설치 검증 | PM | `opal/tools/ownership-tool/README.md`, `opal/tools/worktree-launcher/README.md`, `opal/tools/worktree-tool/README.md`, `opal/core/references/harness/worktree.md`, `docs/ARCHITECTURE.md`, 관련 테스트, 태스크 `run/` 증거 | 코드 현재 사실·설치 경로 문서 동기화, 기존 installer가 패키지와 bootstrap을 배포함을 검증. 필요 시 installer의 누락 배포만 보완. | W-2 | P3 | AC-6, C-1, C-4, C-6 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. native ID 수명 | root session과 subagent thread를 혼동하거나 재개 시 다른 신원 선택 | 잘못된 owner | 공식 소스·설치본 메타·실제 두 세션 관측을 구분 기록, thread fallback 금지 |
| H-2. 시작 경쟁 | child claim이 launcher 최종 registry 전이 전 또는 후에 발생 | registry owner 누락/부모 잔존 | registry lock 안에서 lease 관측, 앞/뒤 순서 integration 테스트 |
| H-3. 설치·실행 권한 | source와 installed 차이 또는 실제 Orca terminal 실행 불가 | 실제 경로 미검증 | 정식 install과 실제 검증용 Codex 실행 증거 필수, 막히면 미완료 유지 |

## Release and recovery

- P1→P2→P3. ownership/launcher/worktree 기존 회귀 및 독립 RED/TEST/컨벤션 검증을 수행한다. 코드맵 헤더는 기존 inline 소스를 갱신하고 changed validate로 확인한다.
- 실제 Orca E2E는 기존 task_155 워크스페이스에 검증용 terminal만 사용한다. 별도 PM/태스크 채번/Git worktree는 생성하지 않는다. 실행 입력은 격리 fixture registry와 canonical task, 실제 부모·자식 ID를 사용한다. fixture는 실제 task_155 lease 및 opal-studio/task_008을 변경하지 않는다.
- 정식 install의 실제 영향 목록과 source/installed diff를 먼저 검토한다. 배포 권한이 추가로 필요하면 그 결과를 제시한 뒤 질문한다. 직접 ~/.opal 수정은 금지한다.
- 실패 시 검증 terminal handle만 정리하고 공개 cancel/ownership-set 원복을 확인한다. 설치 후 실패는 같은 공식 installer로 이전 검증 소스를 재설치하며 임의 파일 복사로 복구하지 않는다.
- 모든 필수 실제 검증 통과 전 CLOSE 완료를 주장하지 않는다. merge/push, 허브 MEMORY·미추적 스킬 변경은 범위 밖이다.

### 검증 중 계획 보완

설치 후 state-tool mark/advance가 native Codex 환경에서 ownership_session_id_missing을 실제 출력했다. `_current_session_id`의 OPAL 전용 소비가 원인이므로 W-1에 기존 state-tool 소비 경로와 회귀 테스트를 추가한다. 독립 RED 후 공통 resolver에 위임하며 새로운 플랫폼 env literal이나 영구 export를 만들지 않는다. AC-1/3/6과 기존 S-1/9 기준 내 수정이다.
