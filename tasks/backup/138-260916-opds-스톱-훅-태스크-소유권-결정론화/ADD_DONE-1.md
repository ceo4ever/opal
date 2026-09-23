# ADD_DONE-1 — CLAUDE_CONFIG_DIR 배포 대상 확장

| 필드 | 값 |
|------|-----|
| 추가작업 번호 | ADD-1 |
| 일시 | 2026-09-18 20:55 ~ 21:15 KST |

## 사유

태스크 138 배포 후 S-25 수동 E2E 중, `opal_agent_fallback`으로 띄운 첫 세션이 session registry·stop-guard receipt를 하나도 남기지 않았다. 원인은 자식 프로세스가 부모의 `CLAUDE_CONFIG_DIR`을 상속했고 그 디렉터리의 `settings.json`에 hooks가 0건이었던 것이다. install은 `$USER_HOME/.claude`에만 산출물을 배치한다.

`CLAUDE_CONFIG_DIR`을 쓰는 세션은 `~/.claude`를 읽지 않는다. 따라서 훅뿐 아니라 부트스트래퍼(`CLAUDE.md`)·서브에이전트 어댑터(`agents/`)·`~/.opal` 읽기 권한까지 전부 빠진 채로 돈다. 증상이 오류가 아니라 **조용한 무동작**이라, 배포는 성공으로 보이면서 OPAL만 통째로 빠진다. 훅만 고치면 나머지 3지점이 남으므로 4지점을 한 경계로 묶었다.

## 변경 내용

- `scripts/install-mac.sh`에 `claude_config_dirs()` seam 신설 — 배치 대상 config 디렉터리를 1행 1건으로 출력한다. 기본은 `$USER_HOME/.claude` 하나이고, `CLAUDE_CONFIG_DIR`이 비어 있지 않고 HOME과 다를 때만 1건을 더한다(후행 `/` 정규화·중복 제거).
- `hook_settings_targets()`는 그 위에 얹어 `<dir>/settings.json`을 낸다.
- 배치 4지점을 전부 대상 순회로 교체: 훅 병합, `install_claude_permissions`, `install_claude_agents`, 부트스트래퍼 `CLAUDE.md` 삽입. 각 함수는 단건 처리부(`_install_claude_*_one`)로 분리해 순회부와 배치부를 나눴다.
- `scripts/install/windows.ps1`에 같은 경계의 `Get-ClaudeConfigDirs`를 신설하고 훅·부트스트래퍼를 순회로 교체 — mac만 고치면 플랫폼 비대칭이 남는다.
- `scripts/tests/test_hook_parity.py`에 RED 11건 추가(대상 기본값·확장·중복 제거·빈 문자열·4지점 순회·windows parity). 기존 `test_installer_targets_home_settings_only`는 대상이 더 이상 단건이 아니므로 이름과 단언을 갱신했다.

## 변경 파일

- `scripts/install-mac.sh` (수정)
- `scripts/install/windows.ps1` (수정)
- `scripts/tests/test_hook_parity.py` (수정 — RED 11건 추가)
- `tasks/138-260916-opds-스톱-훅-태스크-소유권-결정론화/ADD_DONE-1.md` (생성)

## 검증 결과

- **RED 확인** — 구현 전 신규 단언 11건이 전부 실패(`hook_settings_targets: command not found` 등), 구현 후 전건 GREEN.
- **스위트** — `scripts/tests/` **31 passed**, 0 failed. `bash -n scripts/install-mac.sh` 통과. (`pwsh` 미설치로 PowerShell 파서 검사는 생략 — 정적 단언으로만 커버.)
- **실배포 실측** — `CLAUDE_CONFIG_DIR=~/.claude_platform_mkt` 상태에서 재설치하니 4지점이 두 대상 모두에 배치됐다.

  | 대상 | ownership 훅 | `~/.opal` 권한 | 부트스트래퍼 | 에이전트 |
  |------|---|---|---|---|
  | `~/.claude` | 5건 | 2건 | 있음 | 17개 |
  | `~/.claude_platform_mkt` | 5건 | 2건 | 있음 | 16개 |

- **멱등** — 연속 3회 재설치에서 `~/.claude_platform_mkt/settings.json` md5 `0166436931421beb012d7bfeae9ad181` 바이트 동일. `~/.claude/settings.json`·`CLAUDE.md`도 동일.
- **기본 경로 무변경** — `CLAUDE_CONFIG_DIR` 미설정·빈 문자열일 때 대상이 `$USER_HOME/.claude/settings.json` 단건임을 테스트가 집행한다(`test_targets_default_is_home_settings_only`, `test_targets_ignore_empty_claude_config_dir`).
