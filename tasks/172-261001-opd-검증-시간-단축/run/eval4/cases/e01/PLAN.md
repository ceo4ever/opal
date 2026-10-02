---
template: sdlc-v2
---
# PLAN: Codex 워크트리 부팅 소유권 복구

> 입력: [TASK.md](TASK.md), [REQUEST.md](REQUEST.md). 실행 주체: PM 조율(coordinator), 구현: Work item 담당 워커.

## Approach

허브 registry의 최종 전이는 허브 launcher가 확인한 자식 lease owner를 worktree-tool의 잠금 안에서 비교한 뒤 수행한다. 자식의 codex-start는 lease 획득에 성공했으나 허브 registry 쓰기만 권한 거부된 경우 정상 부팅과 이관 진단을 반환한다. 실패 경로에서는 터미널과 lease를 확인한 증거에 따라 hub 소유 복귀 또는 복구 필요 상태를 결정한다. 구현 범위와 검증 조건은 `REQUEST.md` §변경 내용·§테스트를 따른다.

## Findings

### 직접 변경

`opal/tools/worktree-tool/worktree_tool.py`, `opal/tools/worktree-launcher/worktree_launcher/launcher_core.py`, `opal/tools/worktree-launcher/worktree_launcher/cli.py`, `opal/tools/worktree-launcher/worktree_launcher/adapters/orca.py`, `opal/tools/ownership-tool/ownership_tool/session_start_hook.py`, `opal/tools/ownership-tool/ownership_tool/codex_adapter.py`, `opal/tools/ownership-tool/ownership_tool/ownership_core.py`, `opal/tools/worktree-launcher/worktree_launcher/settings.py`, `opal/core/setting.default.json`, `scripts/install-mac.sh`, `scripts/install/windows.ps1`와 해당 모듈 테스트를 변경한다. 현재 owner 없는 성공과 실패 시 무조건 복귀 흐름의 위치는 `worktree_tool.py:1957-1964`, `launcher_core.py:287-333`, `launcher_core.py:414-481`이다.

### 회귀 확인

`opal/tools/worktree-launcher/tests/test_adapter_cmux.py`, `opal/tools/worktree-launcher/tests/test_adapter_generic.py`, `opal/tools/ownership-tool/tests/test_lease.py`의 기존 행위를 재실행한다. 변경하지 않는 인접 소비자는 canonical task path 해석, status·remove 가드, 허브 브리핑·Console의 상태 표현이다. 새 상태가 이 소비자의 허용 집합에 닿는지 W-1에서 조사한다. 이 소비자들은 이번 변경 대상이 아니므로 영향이 확인돼도 소비자 코드는 바꾸지 않고, W-1의 영향 판정 기록에 닿는 위치와 후속 조치 필요 여부를 남겨 PM에 보고한다.

### 문서 갱신

`opal/core/references/harness/worktree.md`, `docs/ARCHITECTURE.md`, `opal/tools/worktree-tool/README.md`, `opal/tools/worktree-launcher/README.md`, `opal/tools/ownership-tool/README.md`, `opal/tools/worktree-tool/schema/worktree.schema.json`, `opal/bootstrapper/codex-bootstrap.md`의 실제 계약이 바뀌는 절을 갱신한다.

### 미확인 가정

H-1, H-2, H-3.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| owner 원자 확정 | `--owner-from-lease`는 live owner·`--expected-owner`·`--exclude-owner`를 registry lock 안에서 검사하며, 불일치 시 registry 바이트 불변 | `REQUEST.md` §변경 내용 1·3; `opal/core/references/harness/worktree.md` §Codex identity 연결 |
| 실패 안전 분류 | polling timeout 뒤 close 전에 마지막 lease를 한 번 읽고, 그때 확인된 자식 claim만 최종 전이로 합류한다. `not_created`는 close 생략, `created`는 close 성공과 handle absent 확인 필수, `unknown`은 worktree 부재를 입증할 때까지 복귀 금지. 그 뒤 시작된 handoff만 cancel하고 lease를 재조회한다. 하나라도 불명·실패·외부 live owner이면 `recovery_required`, 새 launch 금지. `recover`는 보존 handle 또는 worktree root의 absent·cancel·lease 확인 후에만 hub_owned로 복귀한다 | `REQUEST.md` §변경 내용 2·2-1·2-2; `opal/tools/worktree-launcher/worktree_launcher/launcher_core.py:287-333` |
| 부팅 권한 경계 | lease 획득 후 registry 권한 거부만 `registry_owner_deferred_to_hub` 진단과 함께 정상 처리. 다른 실패는 유지 | `REQUEST.md` §변경 내용 4·5·6; `opal/tools/ownership-tool/ownership_tool/session_start_hook.py:115-171` |
| 설정 이관 | 구 Codex 기본 argv와 정확히 일치할 때만 `--no-daemon` 기본값으로 이관. 수정값 보존 | `REQUEST.md` §변경 내용 8; `opal/tools/worktree-launcher/worktree_launcher/settings.py:38` |
| checkpoint 쓰기 경계 | `REQUEST.md`가 허용한 경로 (b)를 채택한다. Codex 부트 문구에 허브 meta 쓰기의 `registry_write_denied` 시 권한 상승 요청 후 동일 checkpoint 명령 재실행을 명시한다. 호출자는 자식 세션이며 승인 없는 승격은 없다. 승격 불가·재실패는 checkpoint 실패 그대로 보고한다 | `REQUEST.md` §변경 내용 7; `opal/core/references/harness/worktree.md` §실행 소유권 |
| cmux 확인 경계 | 현재 실행 환경에 cmux 실행 파일이 없어 반환 형식과 worktree 단위 부재를 확인할 수 없다. 이번 변경은 Orca만 `status`·`status_worktree`를 구현하며 cmux·generic·fallback은 `unknown(status_unsupported)`로 닫아 실패 시 `recovery_required`를 유지한다 | `REQUEST.md` §변경 내용 2-2; `opal/tools/worktree-launcher/worktree_launcher/adapters/cmux.py` |
| Codex 버전 정책 | 고정 최소 버전을 추정하지 않는다. 설치 안내는 `codex --help`에 `--no-daemon`이 있는 버전을 요구한다. 지원하지 않는 바이너리의 즉시 종료는 lease 미획득 timeout→종료 확인→hub_owned 경로로 처리하며, 종료가 불명이면 `recovery_required`다. 이 PC의 0.157.1 help에는 옵션이 있다 | `REQUEST.md` §변경 내용 8; [OpenAI Codex CLI 소스](https://github.com/openai/codex/blob/rust-v0.157.0/codex-rs/cli/src/main.rs) |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. registry 전이와 잠금 | opal-task-agent | `opal/tools/worktree-tool/worktree_tool.py`, `opal/tools/worktree-tool/tests/test_worktree_tool.py`, `opal/tools/worktree-tool/schema/worktree.schema.json` | 권한 거부 즉시 분류. `--owner-from-lease`는 lock 안에서 live lease·expected 일치·excluded 불일치를 검사하고 쓰기 전 거부. `session_launching→recovery_required→hub_owned`만 허용, owner null과 terminal_creation·adapter·handle·receipts·observed_lease_owner 보존, hub_owned 복귀 시 소거. registry 상태 소비자 목록과 영향 판정 기록 | 없음 | P1 | AC-1, AC-2, AC-3, AC-4, C-1, C-2 |
| W-2. lease 부팅 | opal-task-agent | `opal/tools/ownership-tool/ownership_tool/session_start_hook.py`, `opal/tools/ownership-tool/ownership_tool/codex_adapter.py`, `opal/tools/ownership-tool/ownership_tool/ownership_core.py`, `opal/tools/ownership-tool/tests/test_session_start.py`, `opal/tools/ownership-tool/tests/test_codex_identity.py` | lease 성공 후 registry 권한 거부만 비치명화, lock 권한 거부 즉시 분류, 다른 실패 보존 | 없음 | P1 | AC-1, AC-4, C-1 |
| W-4. Codex 기본값과 설치 이관 | opal-task-agent | `opal/tools/worktree-launcher/worktree_launcher/settings.py`, `opal/core/setting.default.json`, `scripts/install-mac.sh`, `scripts/install/windows.ps1`, `opal/tools/worktree-launcher/tests/test_settings.py`, `scripts/tests/test_agent_adapter_fields.sh` | `--no-daemon` 기본값·구 기본값 정확 일치 이관·사용자 수정값 보존. 버전 숫자 추측 대신 `codex --help` 옵션 확인을 설치 안내에 넣고, 미지원 즉시 종료의 timeout 복귀를 W-3에서 검증 | 없음 | P1 | AC-5, C-3 |
| W-3. 터미널 상태와 안전한 launcher | opal-task-agent | `opal/tools/worktree-launcher/worktree_launcher/launcher_core.py`, `opal/tools/worktree-launcher/worktree_launcher/cli.py`, `opal/tools/worktree-launcher/worktree_launcher/adapters/orca.py`, `opal/tools/worktree-launcher/tests/test_launcher_core.py`, `opal/tools/worktree-launcher/tests/test_adapter_orca.py`, `opal/tools/worktree-launcher/tests/test_adapter_conformance.py`, `opal/tools/worktree-launcher/tests/test_cli.py` | `code-scan scan opal/tools/worktree-launcher/worktree_launcher`에서 launcher_core가 lifecycle, Orca가 terminal 동사를 소유함을 확인. bounded lease polling 뒤 close 전 최종 claim만 성공. 원자 비교 실패 시 owner 재추격 금지. 실패 시 not_created/created/unknown 분류→close·absent 확인→실제 handoff만 cancel→lease 재조회→hub_owned 또는 recovery_required. recover는 registry 보존값으로 같은 확인 재수행. Orca는 show stale+list 부재만 absent, 다른 adapter는 unknown. 구 Codex 버전의 즉시 종료도 timeout 경로로 검증 | W-1 | P2 | AC-1, AC-2, AC-3, C-1, C-2 |
| W-5. 문서와 공개 계약 | opal-task-agent | `opal/core/references/harness/worktree.md`, `docs/ARCHITECTURE.md`, `opal/tools/worktree-tool/README.md`, `opal/tools/worktree-launcher/README.md`, `opal/tools/ownership-tool/README.md`, `opal/bootstrapper/codex-bootstrap.md` | 실제 성공·실패·복구, checkpoint 권한 상승 요청, cmux status 미지원, `codex --help` 지원 옵션 요건을 구현 결과에 맞춰 갱신 | W-1, W-2, W-3, W-4 | P3 | AC-1, AC-3, AC-4, AC-5, C-1, C-2, C-3 |
| W-6. 통합과 실측 준비 | opal-task-agent | `opal/tools/worktree-launcher/tests/test_integration.py`, `opal/tools/worktree-launcher/tests/test_codex_handoff.py` | 단위 경계를 넘는 성공·실패 전이 및 설치본 검증 명령 준비. source 테스트와 실제 터미널 관측을 분리해 기록 | W-1, W-2, W-3, W-4 | P3 | AC-1, AC-2, AC-3, AC-6, C-4 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. Orca 조회 응답의 terminal 신원·list 형식이 환경마다 다름 | stale handle과 실제 부재의 이중 확인 | 잘못된 허브 복귀 | W-3에서 실제 CLI 응답과 fixture를 비교하고 알 수 없으면 unknown 처리 |
| H-2. Codex `--no-daemon` 최소 지원 버전 미확인 | 기본 명령 기동 | 설치 사용자 세션 기동 실패 | W-4에서 지원 근거 조사, 미지원 동작은 timeout 복구 시나리오로 고정 |
| H-3. checkpoint가 허브 meta에 쓸 수 없음 | 첫 체크포인트 기록 | 162의 후속 작업 차단 | source/installed 실측에서 확인한다. `registry_write_denied`이면 자식 세션이 권한 상승을 요청한 뒤 동일 checkpoint 명령을 재실행하고, 승인 불가·재실패이면 checkpoint 실패로 보고한다 |

## Release and recovery

- 적용 순서: P1의 배타적 파일 작업, P2 launcher 통합, P3 문서·통합 검증 순서. 161·162 파일과 개인 launcher 설정은 변경하지 않는다.
- 검증 범위: source pytest·installer bash 테스트, 공개 CLI의 실패·성공 응답, 실제 Orca 터미널·lease·registry 값, 설치본 진입점과 태스크 162 첫 checkpoint를 구별해 기록한다.
- 실측 경계: lease polling과 terminal 확인은 설정 상한 안에서 종료해야 한다. 미확인 상태는 자동 재기동하지 않는다.
- 실패 시: 설치 전에는 source 수정으로만 재시험한다. install 배포와 162 재기동은 별도 권한 경계에 닿으므로 실행 전 중단·보고한다. 162 기존 세션 복구는 `REQUEST.md` §162 복구 순서의 모든 확인을 통과해야 한다.
