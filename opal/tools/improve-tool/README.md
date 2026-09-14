# improve-tool

> PM 개선 루프 결정론 집행 CLI — 개선 후보를 로컬(프로젝트 `.opal/`)과 FW(`~/.opal/fw-inbox/`) 2원으로 분기 기록한다
> 소스: `opal/tools/improve-tool/` | 배포: `~/.opal/tools/improve-tool/`
> 의존성: `~/.opal/.venv/bin/python` (표준 라이브러리만 — `argparse`/`json`/`os`/`pathlib`/`re`/`socket`/`subprocess`/`sys`/`datetime`) + 형제 도구 `memory-tool`(local scope 위임)

## 개요

`improve-tool`은 3서브명령(`record`/`list`/`show`)으로 개선 후보를 기록·조회한다.

- **분류는 호출자의 몫이다.** 로컬 개선인지 프레임워크 개선인지 판단하는 것은 `opal-improve` 스킬(`//opim`)과 CLOSE 회고 하드스텝이며, 이 도구는 **확정된 `--scope`를 결정론적으로 집행만** 한다.
- **모든 경로가 `ok` 키를 보장한다.** `record`/`list`/`show` 3서브명령 모두 `--scope`에 `choices=`를, 필수 인자에 `required=`를 **의도적으로 쓰지 않고** 수동 검증한다. argparse 오류도 `_GracefulArgumentParser`가 가로채 JSON으로 바꾸므로 traceback이 새지 않는다.
- `memory-tool` 위임 경로는 배포 경로를 하드코딩하지 않고 **자기 위치 기준 형제 디렉토리**(`{TOOL_DIR}/../memory-tool/run.sh`)를 가리킨다 — 소스 트리와 배포 트리 양쪽에서 같은 방식으로 해석된다.

## scope 2분기

| scope | 대상 | 동작 |
|-------|------|------|
| `local` | `<project-root>/.opal/MEMORY.json` | `memory-tool append --type improvement --status candidate`로 위임 |
| `fw` | `~/.opal/fw-inbox/{YYYYMMDD-HHmmss}-{host}-{slug}.md` | 자기완결 마크다운 항목을 직접 write |

**local 대상 해석 (`_resolve_memory_target`)** — 3서브명령이 공유하는 단일 판정 지점이다.

1. `.opal/MEMORY.json` 존재 → 그 경로로 위임
2. `.opal/MEMORY.md`만 존재 → **`.json` 경로로 위임**해 `memory-tool`의 lazy 변환을 유도(과도기)
3. 둘 다 부재 → 위임하지 않고 graceful no-op (`{"ok": true, "scope": "local", "skipped": true, "reason": "no MEMORY.json"}`, write 0건)

**`--project-root` 생략 시 기준은 `Path.cwd()`다.** 워커나 훅에서 호출할 때 cwd가 기대와 다르면 조용히 no-op으로 떨어지므로, 자동 경로에서는 `--project-root`를 명시하는 편이 안전하다.

**환경변수 `IMPROVE_FW_INBOX`**: 설정 시 fw scope의 기본 목적지(`~/.opal/fw-inbox/`) 대신 그 경로를 최우선 사용한다 — `record`뿐 아니라 `list`/`show`의 조회 기준에도 동일하게 적용된다(테스트 격리 훅).

## 호출 형식

```bash
~/.opal/tools/improve-tool/run.sh <command> --scope {local|fw} [options]
```

## 3개 서브 명령

### 1. `record` — 개선 후보 기록

```bash
~/.opal/tools/improve-tool/run.sh record --scope {local|fw} --title <제목> \
  [--body <제안 본문>] [--situation <맥락>] \
  [--source-task <NNN|task-path>] [--project-root <경로>]
```

- `--title`은 **비공백 필수**다. 빈 문자열이면 `--title is required (non-empty)`.
- `--situation`은 자유 문자열이다 — 소스에 값 도메인 제한이 없다. 비우면 fw 항목에 `unspecified`로 기록된다.
- `--source-task`는 fw 항목 frontmatter에만 실린다(local 위임에는 전달되지 않는다).

**scope `fw` 산출물** — `~/.opal/fw-inbox/{YYYYMMDD-HHmmss}-{host}-{slug}.md`

파일명의 시점은 **KST**(`UTC+9` 고정)이고, `host`는 `socket.gethostname()`, `slug`는 제목에서 영숫자·한글 외 문자를 `-`로 바꿔 40자로 자른 값(비면 `improvement`)이다. 내용은 frontmatter(`type`/`title`/`created`/`host`/`project`/`project_root`/`source_task`/`situation`/`status: inbox`) + `## 제안 요약` / `## 상황 (Context)` / `## 제안 내용` 3절이다. `--body`가 없으면 본문은 `(본문 미기재)`가 된다.

**scope `local`** — `--body`(없으면 `--title`)를 80자로 잘라 `--summary`로 넘긴다(81자 이상이면 79자 + `…`).

```json
// fw 성공
{"ok": true, "scope": "fw", "path": "/Users/.../fw-inbox/20260717-095231-host-slug.md", "id": "20260717-095231-host-slug.md"}

// local 성공 (memory-tool 위임)
{"ok": true, "scope": "local", "delegated": "memory-tool", "file": "/path/.opal/MEMORY.json", "title": "..."}

// local no-op (메모리 인덱스 부재)
{"ok": true, "scope": "local", "skipped": true, "reason": "no MEMORY.json"}
```

---

### 2. `list` — 개선 후보 목록 (읽기 전용)

```bash
~/.opal/tools/improve-tool/run.sh list --scope {local|fw} [--project-root <경로>]
```

- `fw`: fw-inbox 디렉토리의 `*.md`를 이름순으로 모아 `[{id, path}]`로 돌려준다. **디렉토리가 없으면 오류가 아니라 빈 목록**이다.
- `local`: `memory-tool show`의 `index_rows` 중 `type == "improvement"`인 행만 걸러 돌려준다. 메모리 인덱스가 없으면 `{"ok": true, "scope": "local", "items": [], "skipped": true, "reason": "no MEMORY.json"}`.

---

### 3. `show` — 단일 개선 후보 조회 (읽기 전용)

```bash
~/.opal/tools/improve-tool/run.sh show --scope {local|fw} [--id <id>] [--path <경로>] [--project-root <경로>]
```

- `fw`: `--path`를 우선 쓰고, 없으면 `--id`를 fw-inbox 디렉토리 아래 파일명으로 해석한다. 둘 다 없으면 `--id or --path is required for show --scope fw`. 파일 전문을 `item.content`로 돌려준다.
- `local`: **`--id`는 파일명이 아니라 메모리 인덱스 행의 `title`이다.** 일치 행이 없으면 `item not found: <id>`. 메모리 인덱스 자체가 없으면 `--id` 검사보다 먼저 no-op으로 빠진다.

## 사용 예시

```bash
# 프레임워크 개선 후보 기록
~/.opal/tools/improve-tool/run.sh record --scope fw \
  --title "게이트 재진입 시 근거 인용 검증" \
  --body "PM Gate에서 인용 경로 실재 여부를 결정론적으로 확인할 창구가 없다." \
  --situation retrospective --source-task 131

# 프로젝트 로컬 개선 후보 기록 (memory-tool 위임)
~/.opal/tools/improve-tool/run.sh record --scope local \
  --project-root /path/to/project \
  --title "워커 디스패치 프롬프트에 코드 루트 절대경로 고정"

# 목록 조회
~/.opal/tools/improve-tool/run.sh list --scope fw
~/.opal/tools/improve-tool/run.sh list --scope local --project-root /path/to/project

# 단일 조회
~/.opal/tools/improve-tool/run.sh show --scope fw --id 20260717-095231-host-slug.md
~/.opal/tools/improve-tool/run.sh show --scope local --project-root /path/to/project \
  --id "워커 디스패치 프롬프트에 코드 루트 절대경로 고정"
```

## 오류 코드

**선언 목록 없음.** `error` 값은 안정 식별자가 아니라 **사람이 읽는 자유 문자열**이다(`ERROR_CODES` 카탈로그가 없다). 호출자는 `error` 문자열로 분기하지 말고 `ok`만 판정에 쓴다.

실제로 방출되는 실패 계열(문면은 고정 계약이 아니다):

| 상황 | 메시지 계열 | 발생 명령 |
|------|-----------|----------|
| scope 값 위반 | `--scope must be one of ('local', 'fw'), got '<값>'` | 전 명령 |
| 제목 누락 | `--title is required (non-empty)` | record |
| fw-inbox 준비/쓰기 실패 | `failed to prepare fw-inbox directory: ...` / `failed to write fw-inbox entry: ...` | record(fw) |
| memory-tool 위임 실패 | `memory-tool delegation failed: ...` | record(local) |
| memory-tool 조회 실패 | `memory-tool show failed: ...` | list/show(local) |
| 식별자 누락 | `--id or --path is required for show --scope fw` / `--id (title) is required for show --scope local` | show |
| 대상 부재 | `fw-inbox entry not found: <경로>` / `item not found: <id>` | show |
| argparse 오류 | `argument error: <원문>` | 전 명령 |
| 그 외 예외 | `unexpected error: <원문>` | 전 명령 |

## 종료 코드

| 코드 | 의미 |
|------|------|
| `0` | 성공 — **no-op(`skipped: true`)도 성공이다** |
| `1` | 위 실패 전건(인자 오류·write 실패·`memory-tool` 위임 실패 포함), 그리고 `run.sh`의 venv 부재 선검사 |

argparse 오류까지 `_GracefulArgumentParser`가 흡수해 exit 1 + JSON으로 바꾸므로, **이 도구에는 exit 2 경로가 없다.** `run.sh`의 venv 부재 메시지만 stdout이 아닌 stderr로 나간다.

## 제약

- `list --scope local`은 `memory-tool show`의 `index_rows`에 의존한다 — 인덱스에 없는 개선 후보는 조회되지 않는다.
- `show --scope local`은 `index_rows`의 행 자체를 돌려준다. fw처럼 본문 전문을 주지 않는다.
- `record --scope local`은 기존 항목과 제목이 겹쳐도 중복 검사를 하지 않는다(위임받은 `memory-tool`의 append 계약을 그대로 따른다).
- `memory-tool` 호출에는 30초 타임아웃이 걸려 있다. 초과하면 `record`는 `memory-tool delegation failed:`로, `list`/`show`는 `memory-tool show failed:`로 접힌다.
- 기록만 하고 처리하지 않는다 — fw-inbox 항목의 `status: inbox`를 바꾸거나 항목을 삭제·이관하는 서브명령은 없다.
