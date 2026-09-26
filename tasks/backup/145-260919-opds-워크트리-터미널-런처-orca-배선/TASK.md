---
template: sdlc-v2
---

# TASK: 워크트리 전용 터미널 런처 orca 경로 배선

## Problem

`--wt` 태스크는 워크트리와 canonical task path까지 만들고 끝난다. 워크트리 전용 터미널을 열어 LLM을 기동하고 태스크를 이어받게 하는 구간이 한 번도 동작한 적이 없다. 이 세션에서 실측한 결함은 다음과 같다.

- **호출부 0건** — `task-process.md` §오케스트레이터 공통 영역 스텝 4.5는 `worktree-tool create`에서 끝나고 launcher를 부르지 않는다. 소스 전체에 `worktree-launcher` 호출부가 없다.
- **CLI 표면 미구현** — `opal/tools/worktree-launcher/run.sh`가 `{"error":"not_implemented"}`로 exit 1한다. 라이브러리 직접 호출 외에 실행 경로가 없다.
- **응답 봉투 파싱 오류** — `orca terminal create --json`은 `{"ok":true,"result":{"terminal":{...}}}`를 반환하는데 `adapters/orca.py`의 `parse_response()`가 `response["terminal"]`을 읽는다. 그 결과 `adapter_handle`·`reported_cwd`가 `null`이 되고 `launcher_core`가 `launch_receipt_missing`으로 판정해 `hub_owned`로 원자 복귀한다. **터미널은 실제로 떠 있는데 실패로 기록된다.**
- **cwd 원천 불일치** — `_reported_cwd()`는 `terminal["cwd"]` 또는 `worktree_selector`를 기대하지만, orca 실제 응답에는 둘 다 없고 `worktreeId`(`<repoId>::<path>`)만 있다. 봉투를 고쳐도 cwd 가드에서 다시 막힌다.
- **실패 시 터미널 미정리** — 원자 복귀 경로가 이미 생성된 터미널을 닫지 않아 고아 터미널이 남는다. 이 세션 실측에서 3개가 남았다.
- **회수 seam 부재** — `launcher_core`의 공개 함수는 `run()` 하나뿐이고 어댑터에도 `launch()`만 있다. `worktree-tool remove`는 터미널의 존재를 모르므로 태스크 회수 후에도 터미널이 남는다.
- **시작 신호 부재** — 터미널에서 LLM이 떠도 "이 태스크를 이어서 수행하라"를 전달하는 경로가 없다. `prompt receipt`가 항상 비어 `sessionstart_claim_observation` 폴백으로 떨어진다.
- **에이전트·파라미터 선택 불가** — 어떤 LLM을 어떤 인자로 띄울지 설정할 곳이 없다. `generic` 어댑터는 `{cwd}`·`{command}` 템플릿을 받지만 그 템플릿을 선언할 설정 키가 어디에도 없어 항상 `template=None` 실패다.

이 결함들이 통과된 원인은 `test_adapter_orca.py`가 subprocess를 목킹하고 **구현이 가정한 응답 모양**을 스스로 넣어 파싱했기 때문이다. 실물 CLI 응답과 대조한 적이 없다.

## Proposed outcome

1. 허브 세션이 워크트리·브랜치·TASK.md·`state init`까지 만든 뒤, 워크트리 전용 터미널을 열고 그 터미널의 LLM이 태스크를 이어받는 흐름이 실제로 완주한다.
2. `worktree-launcher`가 어댑터 3동사 계약(`launch` / `read` / `close`)을 소유하고, 보고 dict가 기계 검증 가능한 스키마로 고정된다.
3. orca 어댑터가 실물 `orca terminal create --json` 응답을 정확히 파싱한다 — `result.terminal` 봉투와 `worktreeId` 기반 cwd 판정.
4. launch 실패로 원자 복귀할 때 이미 생성된 터미널을 닫는다. 고아 터미널을 남기지 않는다.
5. 태스크 회수(`worktree-tool remove`) 경로가 터미널 close를 선행 수행한다.
6. 시작 발화는 **기동 명령 인자**가 소유한다 — `--command 'claude "<태스크 경로> 이어서 수행"'` 형태로 argv에 실어 보내고, `terminal send`·키 입력 에뮬레이션·별도 캡슐 파일에 의존하지 않는다. 태스크 식별은 워크트리 1:1 + `state.json` + 부트스트랩 브리핑이 이미 결정론적으로 해결하므로 중복 수단을 만들지 않는다.
7. 기동할 에이전트와 인자를 설정으로 선택할 수 있다. 미설정이면 기본값으로 동작한다.
8. 새 어댑터 추가 비용이 "공통 적합성 테스트를 통과시키기"로 정의된다.
9. 워크트리 세션이 `completed_unmerged`로 끝난 사실을 허브 세션이 감지한다. 새 통지 채널을 만들지 않고 기존 registry(`attribution_state`)만 읽는다.

## Affected users and systems

| 대상 | 영향 |
|---|---|
| `opal/tools/worktree-launcher/` | 어댑터 계약 확장, orca 파서 수정, CLI 표면 신설, 적합성 테스트 |
| `opal/tools/worktree-tool/` | `remove` 전단 터미널 close 훅, `status`의 복귀 감지 필드 |
| `opal/core/references/harness/task-process.md` | 스텝 4.5에 launcher 호출 단계 추가 |
| `opal/core/references/harness/worktree.md` | 실행 흐름·회수 경계 등재 |
| `~/.opal/setting.json` 스키마 | `launcher` 블록 신설 (2-레이어 머지) |
| `--wt`를 쓰는 9개 Pilot | 스텝 4.5 경유이므로 공통 적용 |
| 비-orca 환경 | 이번 범위 밖 — 기존 동작 유지 |

## Constraints

- C-1. **orca 어댑터만 구현한다.** cmux·generic 어댑터는 이번 범위에서 제외하고, 계약만 확장 가능한 형태로 둔다.
- C-2. **상속 계층을 만들지 않는다.** 현행 덕타이핑 seam을 유지하고 동사와 보고 스키마만 표준화한다 — OPAL 도구는 모듈 함수 스타일이며 orca·cmux는 공유할 공통 구현이 없다.
- C-3. **워크트리는 허브를 추론하지 않는다**(`worktree.md` D-20). 허브가 발급값을 배달하고 워크트리는 그것만 읽는다.
- C-4. `worktree-tool`이 worktree·registry·canonical task path의 단일 소유자로 남는다. orca `worktree create`로 대체하지 않는다.
- C-5. 상태 쓰기는 전부 `ownership-set` 경유 — launcher는 사설 ownership writer를 두지 않는다.
- C-6. `--wt` 미사용 시 현행 동작 100% 유지. 플래그 없는 경로에 조건부 분기를 넣지 않는다.
- C-7. 적합성 테스트에 **실물 CLI 대조 1건**을 포함한다. 목킹 전용 검증은 이 결함을 다시 통과시킨다.
- C-8. **머지 경계는 불변이다.** 워크트리 세션은 `completed_unmerged`까지만 진행하고, `main` merge·push·worktree 제거는 사용자 승인 뒤 허브 세션이 수행한다(`guards.md` §커밋 규칙, `task-process.md` 5항). git이 허브에 체크아웃된 `main`을 워크트리에서 다시 체크아웃하지 못하므로 정책이자 기술 제약이다.
- C-9. `launcher` 설정의 "미설정 시 기본값" 규칙은 `models`의 "미설정 시 중단" 계약과 다르다. 그 비대칭의 근거를 설정 문서에 명시한다.
- C-10. 허브·기본 브랜치 commit과 merge·push는 사용자 승인 경계를 유지한다.

## Acceptance criteria

- AC-1. `worktree-launcher/run.sh`가 `not_implemented` 대신 실행 가능한 CLI를 제공하고, `--adapter orca`로 지정한 어댑터를 명시 주입한다(자동 폴백 없음).
- AC-2. 실물 `orca terminal create --json` 응답으로 `parse_response()`가 `adapter_handle`과 `reported_cwd`를 채운다. 목킹이 아닌 실제 호출 증거로 검증한다.
- AC-3. `launcher_core.run()`이 실물 orca 경로에서 `worktree_session_owned`까지 전이하고 `launch_receipt`·`prompt_receipt` 2종이 registry에 기록된다.
- AC-4. launch 실패를 주입하면 상태가 `hub_owned`로 복귀하고 **생성된 터미널이 0개 남는다**.
- AC-5. 하네스에 launcher 호출이 등재되고(스텝 5.5 — `state init` 이후여야 워크트리 첫 턴이 읽을 상태가 존재한다), `--wt` 태스크 1건을 돌렸을 때 워크트리 터미널에서 LLM이 기동해 **첫 턴이 스스로 시작**되며 해당 태스크의 다음 행을 이어받는다.
- AC-6. `worktree-tool remove` 후 해당 워크트리의 터미널이 0개 남는다.
- AC-7. `launcher.agents`에 `claude`·`codex` 2종을 선언하고 `default`를 바꾸면 기동되는 명령이 바뀐다. 블록 전체를 지우면 기본값으로 동작한다.
- AC-8. 공통 적합성 테스트 스위트가 존재하고 orca 어댑터가 전건 통과한다. 새 어댑터가 통과해야 할 계약이 그 스위트로 정의된다.
- AC-9. 허브 세션이 `worktree-tool status`만으로 해당 태스크가 `completed_unmerged`에 도달했는지 판정할 수 있고, 그 판정이 merge 안내의 입력이 된다.
- AC-10. `--wt` 미사용 경로의 기존 테스트가 전건 통과한다(회귀 없음).
