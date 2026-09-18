# oppb-runtime-tool

> OPPB(프로젝트 빌드 파일럿) 실행 런타임 CLI — 현재 서브 명령 `init`·`start`
> 소스: `opal/tools/oppb-runtime-tool/` | 배포: `~/.opal/tools/oppb-runtime-tool/`
> 의존성: `~/.opal/.venv/bin/python` (표준 라이브러리만 — `datetime`/`json`/`os`/`pathlib`/`subprocess`/`sys`/`tempfile`/`uuid`) + 로컬 **git 2.x**

## 개요

`init`이 허브(allocator) Git repository에 OPPB run의 미추적 작업 공간을 연다.

- **run root** `<allocator_root>/.opal-runs/<run_id>/` — 재시작 가능한 실행 운영 자료
- **cache root** `<allocator_root>/.opal-cache/oppb/` — run 간 재사용하는 content-addressed object

두 경로는 `.git/info/exclude`에 **멱등 등록**하고, 등록 문자열 존재가 아니라 `git check-ignore`의 **실제 판정**을 확인한다. 확인에 실패하면 run 시작을 거부한다(`start`도 같은 가드를 통과해야 한다). 계약 원문은 제안서 `docs/proposals/opal-oppb-project-build-pilot.md` §4.5가 소유한다.

공통 출력 계약(단일 라인 JSON·`error` 코드 안정성·exit code)은 `opal/core/references/harness/tool-output-contract.md`가 소유한다. 이 문서는 이 도구 고유 사항만 다룬다.

## 호출 형식

```bash
~/.opal/tools/oppb-runtime-tool/run.sh init  --allocator-root <절대경로> --project-root <절대경로>
~/.opal/tools/oppb-runtime-tool/run.sh start --run-root <절대경로>
```

stdout은 **항상 JSON**이다 — `--json` 플래그는 없다. run을 가리킬 때는 `--run-root`를 쓰며 `--run-id` 인자는 없다(`run_id`는 `init` 응답 필드로만 존재한다).

## 경로 인자 계약

- `--allocator-root`는 **명시 인자로만** 받는다. cwd·경로 세그먼트·`.opal-worktrees` 문자열로 추론하지 않는다 — `opal/core/references/harness/worktree.md` §task root와 allocator root 계약의 `[MUST]`.
- 미지정·상대경로·비존재 경로는 거부한다. `--project-root`도 같다.
- `--allocator-root`는 git 저장소의 **최상위**여야 한다. 하위 디렉토리면 `.git/info/exclude`의 상대 패턴이 run root·cache root를 가리키지 못해 등록과 판정 확인이 성립하지 않는다.
- 거부된 호출은 부작용을 남기지 않는다 — 인자 검증·저장소 확인·exclude 등록·ignore 판정 확인을 모두 통과한 뒤에만 디렉토리를 만든다.

## `init` 멱등 계약

재호출은 기존 run 상태를 **초기화하지 않는다.**

- `run_id`는 호출마다 새로 발급하므로 이전 run root를 덮어쓰는 경로 자체가 없다.
- `.git/info/exclude` 등록은 이미 있는 줄을 다시 쓰지 않는다 — 재호출로 중복 줄이 늘지 않는다.
- run root의 `run.json`은 부재일 때만 쓴다(대상 디렉토리 임시 파일 → `fsync` → `os.replace`).

`oppl-runtime-tool`의 `init`은 기존 ledger 존재를 확인하지 않고 덮어써 재실행 시 카운터가 0으로 돌아간다. OPPB는 재시작 가능성이 설계 전제이므로 그 동작을 복제하지 않는다.

## run identity — OPPL과 의도적으로 다르다

**`run_id`는 `oppb-runtime-tool init`이 자체 발급한다.** OPPL이 `state.json.run_id`를 SSOT로 삼는 것(D8)과 다르며, 이는 사고가 아니라 의도된 차이다 — OPPL의 run root는 태스크 폴더 안 `.oppl-run/`이라 태스크에 종속되지만, OPPB의 run root는 허브 `.opal-runs/<run_id>/`이고 제안서 §4.5가 "미추적 run root는 worktree 회수와 함께 삭제하지 않는다"고 정해 **태스크보다 오래 살아남는 것이 설계 요구**다.

## 설정 층

**별도 설정 파일 층을 두지 않는다.** `setting.json`에 `oppb.runtime` 블록을 추가하지 않으며, 예산·정책은 서브 명령의 `--spec`·`--policy` 파일 주입으로만 받는다.

## 소유 경계

- `oppl-runtime-tool`을 import하거나 호출하지 않는다. 원자 쓰기·파일 락 같은 공통 패턴은 형태만 복제한다.
- attempt 기동과 재부착·수확·고아 판정은 `opal-agent`가 소유한다. 이 도구가 다시 구현하지 않는다.
- 플랫폼 분기를 두지 않는다. `.git/info/exclude` 조작과 ignore 판정은 `git` CLI 공통 수단으로만 한다.

## 응답 필드

| 명령 | 성공 응답 키 |
|---|---|
| `init` | `run_id` · `run_root` · `cache_root` · `allocator_root` · `project_root` · `exclude_path` · `exclude_entries_added` |
| `start` | (Supervisor 본체 미구현 — 진입 가드만 존재한다) |

## 오류 코드

| 코드 | 의미 |
|---|---|
| `usage_error` | 명령 인자가 올바르지 않다 |
| `unknown_command` | 알 수 없는 서브 명령 |
| `allocator_root_missing` | `--allocator-root` 미지정 — cwd로 추론하지 않는다 |
| `allocator_root_not_absolute` | `--allocator-root`가 상대경로 |
| `allocator_root_not_found` | `--allocator-root` 경로 부재 |
| `allocator_root_not_a_git_repository` | git 저장소가 아님 |
| `allocator_root_not_repository_root` | git 저장소 최상위가 아님 |
| `project_root_missing` / `project_root_not_absolute` / `project_root_not_found` | `--project-root` 인자 계약 위반 |
| `run_root_missing` / `run_root_not_absolute` / `run_root_not_found` | `--run-root` 인자 계약 위반 |
| `run_root_invalid` | `<allocator_root>/.opal-runs/<run_id>` 형태가 아님 |
| `git_command_failed` | git 호출 실패 |
| `exclude_registration_failed` | `.git/info/exclude` 등록 실패 |
| `ignore_verification_failed` | 실제 ignore 판정 확인 실패 — run 시작 거부 |
| `run_root_create_failed` | run root·cache root 생성 실패 |
| `supervisor_not_implemented` | 진입 가드는 통과했으나 Supervisor 본체가 없음 |
| `internal_error` | 처리되지 않은 내부 오류 |

## 종료 코드

| 값 | 의미 |
|---|---|
| `0` | 성공 |
| `1` | 일반 실패 |
| `2` | 인자 사용 오류(`usage_error`·`unknown_command`) |

## 테스트

```bash
python3 -m pytest opal/tools/oppb-runtime-tool/tests/test_oppb_init.py -q
```

테스트는 `run.sh` 서브프로세스와 실제 git 저장소만 사용하고 내부 심볼을 import하지 않는다(mock 금지).
