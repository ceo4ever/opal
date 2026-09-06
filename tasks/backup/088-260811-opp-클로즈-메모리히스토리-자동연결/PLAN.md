# PLAN: CLOSE 완료 시 메모리 히스토리 자동 연결

> 작성일: 2026-08-11 | 적용 스킬: opp | 모드: agentic
> 입력: TASK.md
> 출력: PLAN.md

## 1. 현황 조사

### 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py` | mark 경로·CLOSE 마지막 행 판정·ok() stdout 페이로드 접합점 |
| D-2 | 소스 | todo_mirror_hook.py | `opal/tools/state-tool/todo_mirror_hook.py` | PostToolUse 릴레이 주입 구조(리마인더 확장 대상) |
| D-3 | 소스 | memory_tool.py | `opal/tools/memory-tool/memory_tool.py` | `append --kind history` / `show` / `update --kind history` CLI 계약·파일 락 |
| D-4 | 설계 | memory.schema.json | `opal/tools/memory-tool/schema/memory.schema.json` | historyRow 필수 필드·result 타입 제약·FIFO 상수 |
| D-5 | 설계 | state.schema.json | `opal/tools/state-tool/schema/state.schema.json` | `additionalProperties: false` — 비영속 설계 근거 |
| D-6 | 설계 | memory-learning.md | `opal/core/references/harness/memory-learning.md` | 히스토리 규약 SSOT(자동 연결 절 추가 대상) |
| D-7 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | @header·변경이력·배포 경계·도구 우선·플랫폼 분기 컨벤션 |
| D-8 | 설계 | red-first.md | `opal/core/references/harness/red-first.md` | RED→GREEN 순서·작성자≠구현자·공개 인터페이스 검증 |
| D-9 | 설계 | coding-principles.md | `opal/core/references/harness/coding-principles.md` | §2 PLAN 단계 Simplicity 체크·§3 희박 케이스 분류 |
| D-10 | 소스 | test_state_tool.py | `opal/tools/state-tool/tests/test_state_tool.py` | 기존 263개 테스트 픽스처·회귀 경계 |
| D-11 | 소스 | test_todo_mirror_hook.py | `opal/tools/state-tool/tests/test_todo_mirror_hook.py` | 훅 단위 테스트 계약(회귀 경계) |
| D-12 | 소스 | claude-hooks.json | `opal/core/hooks/claude-hooks.json` | PostToolUse 훅 등록 명령(변경 불요 확인) |
| D-13 | 소스 | install-mac.sh | `scripts/install-mac.sh` | `opal/tools/` 일괄 배포 경로(R-7 정합) |
| D-14 | 소스 | opp pipeline.json | `opal/skills/opal-pilot-project/references/pipeline.json` | opp CLOSE 행 구조(단일 행 `close.done_md`) |
| D-15 | 기획 | TASK.md | `tasks/088-260811-opp-클로즈-메모리히스토리-자동연결/TASK.md` | 확정 방향 D-1~D-6 / 요구사항 R-1~R-7 |

### [MUST] 컨벤션 제약 (재해석 금지)

- [MUST] `docs/CONVENTIONS.md` §구현 규칙/배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `agents/`, `community-skills/`, `scripts/`)에서 수행한다."
- [MUST] `docs/CONVENTIONS.md` §구현 규칙/@header 규칙: "코드 파일을 생성·수정할 때 파일 상단에 @header 블록을 작성한다 (해당 확장자에 한해)."
- [MUST] `docs/CONVENTIONS.md` §구현 규칙/변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 \"## 변경이력\" 표에 행을 추가한다."
- [MUST] `docs/CONVENTIONS.md` §구현 규칙/Guards: "커밋은 사용자가 명시적으로 요청할 때만 수행한다 — EXECUTE 완료·DONE.md 생성·테스트 통과 후에도 자동 커밋 금지."
- [MUST] `docs/CONVENTIONS.md` §구현 규칙/플랫폼 분기 격리: "스킬·에이전트 본문에 플랫폼 조건문을 추가하지 않는다 (행위는 플랫폼 독립적으로 기술하고, 도구명은 어댑터에 위임)."
- [MUST] `docs/CONVENTIONS.md` §언어 규칙: "코드/변수/필드명 | English" — 신규 함수·페이로드 필드명은 영문, 값(단계값 `완료`)만 한국어.
- [MUST] `~/.opal/PRINCIPLES.md` §2 Simplicity First: "Solve only the current requirement. No speculative abstraction or unrequested flexibility."

### 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/tools/state-tool/state_tool.py` | mark 경로 — CLOSE 마지막 행 판정 + ok() stdout 페이로드 | **예** | `state_tool.py:1369-1377` (is_close_last), `:1420-1422` (ok + todo_mirror) |
| `opal/tools/state-tool/todo_mirror_hook.py` | PostToolUse 릴레이 — stdout 페이로드 → additionalContext | **예** | `todo_mirror_hook.py:65-81` (extract), `:84-94` (context), `:97-121` (main) |
| `opal/tools/state-tool/tests/test_state_tool.py` | state-tool 단위 테스트 263건 | **예** (RED 신설) | `test_state_tool.py:145-174` (BaseTestCase), `:5182-5238` (TestTodoMirror 선례) |
| `opal/tools/state-tool/tests/test_todo_mirror_hook.py` | 훅 단위 테스트 12건 | **예** (RED 신설) | `test_todo_mirror_hook.py:51-171` |
| `opal/core/references/harness/memory-learning.md` | 히스토리 규약 SSOT | **예** | `memory-learning.md:16` (ambient 트리거), `:22-23` (FIFO·정정) |
| `opal/tools/memory-tool/memory_tool.py` | history append/show/update CLI | **아니오** (재사용) | `memory_tool.py:969-988` (history 분기), `:1273-1318` (show), `:1001-1059` (update 정정) |
| `opal/tools/memory-tool/schema/memory.schema.json` | historyRow 계약 | 아니오 | `memory.schema.json:69-97` |
| `opal/tools/state-tool/schema/state.schema.json` | state.json 계약 | **아니오** (비영속 설계로 회피) | `state.schema.json:8` `"additionalProperties": false` |
| `opal/core/hooks/claude-hooks.json` | PostToolUse 훅 등록 | **아니오** (동일 파일 재사용) | `claude-hooks.json:8` |
| `scripts/install-mac.sh` | 배포 | **아니오** (검증만) | `install-mac.sh:1111-1113` `install_dir "$opal_dir/tools"` |
| `opal/skills/opal-pilot-project/SKILL.md` 외 pilot 9종 | CLOSE 스펙 | **아니오** (D-5 확정) | TASK.md §확정 방향 D-5 |

### 현재 상태

**(1) CLOSE 마지막 행 판정 로직이 이미 존재한다.**
`cmd_mark`는 014 Phase 4에서 항목명 비의존 판정으로 바뀌어, "stage가 CLOSE이고 다음 행이 없거나 다음 행 stage가 CLOSE가 아님"으로 마지막 행을 계산한다 (`state_tool.py:1369-1373`). 이 값은 `current_status="done"` 전환에만 소비되고 있으며(`:1375-1377`), 재사용 가능한 지역 변수 `is_close_last`로 이미 산출되어 있다. 017의 다중 Step 가드 때문에 `row["status"] == "done"` 동반 조건이 함께 걸려 있어(`:1375`), `--step 1/2` 같은 중간 진행 mark에서는 오발동하지 않는다.

**(2) stdout 전용·비영속 페이로드 선례가 확립되어 있다.**
`build_todo_mirror()`는 state.json을 건드리지 않고 `ok()` stdout 페이로드에만 실린다 (`state_tool.py:452-487`, `:1420-1422`). 사유는 `state.schema.json:8`의 `"additionalProperties": false`이다. 076의 이 선례가 이번 R-4/R-5 페이로드 설계의 직접 근거다.

**(3) state-tool은 파일 락을 쓰지 않고, memory-tool만 락을 쓴다.**
`state_tool.py` 전문에 `flock`/`fcntl`/lock 획득 코드가 없다(`save_state_json`은 단순 write, `:205-210`). memory-tool은 `<MEMORY.json>.lock` O_CREAT|O_EXCL 배타 클레임을 쓰며 타임아웃 5초·stale 60초다 (`memory_tool.py:359-406`, `:152-153`). 즉 **state-tool → memory-tool 호출 시 중첩 락·데드락이 성립하지 않는다**(state-tool이 보유한 락이 없으므로).

**(4) state-tool은 이미 외부 프로세스를 호출하는 선례를 가진다.**
`get_kst_datetime()`이 `subprocess.run(["node", date_js, "datetime"], timeout=10)`으로 date 도구를 호출한다 (`state_tool.py:168-184`). `subprocess`·`pathlib`·`sys`는 이미 import되어 있다 (`:16-24`) — 신규 의존 없음.

**(5) memory-tool의 히스토리 계약.**
`append --kind history`는 `--title`(필수) / `--stage` / `--path` / `--summary`(→ `result`로 매핑)를 받아 `history[0]`에 insert하고 FIFO=5를 집행한다 (`memory_tool.py:969-988`, argparse `:1466-1478`). memory 분기의 80자 캡은 history에 적용되지 않는다(`:947-949`가 memory 분기 전용). `show --file <p>`는 read-only로 `history_rows`를 전량 반환한다 (`memory_tool.py:1273-1318`). `update --kind history --title <t> --result <r>`가 정정 경로다 (`:1001-1059`, argparse `:1480-1492`). **중복 검사 기능은 없다.**

**(6) historyRow 계약.**
필수 필드 5종 title·date·stage·path·result, `additionalProperties: false` (`memory.schema.json:69-97`). `result`는 `{"type": "string"}`만 걸려 있고 `minLength`가 없어 빈 문자열도 스키마 통과다. `date`는 memory-tool이 KST로 자동 충전한다(`memory_tool.py:931` → `get_kst_date()` `:184-201`).

**(7) 실제 히스토리 데이터의 현행 표기.**
`.opal/MEMORY.json` history 5행의 `title`은 모두 `"{3자리 번호} {제목구}"` 형태이고, `path`는 `"tasks/<폴더>/"`, `stage`는 `"완료·커밋"`이다. D-6에 따라 이번부터 `stage`는 `"완료"`로 바뀐다.

**(8) 프로젝트 루트 앵커.**
메모리 저장소는 `{프로젝트}/.opal/MEMORY.json`이며(`memory-learning.md:11`), 이 저장소는 태스크 폴더의 조상 디렉토리에 있다. state-tool에는 프로젝트 루트 개념이 없고 `<task-path>`만 받는다 (`state_tool.py:190-195`).

**(9) opp CLOSE 행은 단일 행이다.**
`pipeline.json` task_steps 9번 = `CLOSE / DONE.md 생성 / close.done_md`. 즉 opp에서 "CLOSE 마지막 행" = 유일한 CLOSE 행이다.

**(10) 훅은 `todo_mirror` 키만 추출한다.**
`extract_todo_mirror()`는 stdout 라인 중 마지막으로 파싱되는 JSON 객체의 `todo_mirror` 키만 본다 (`todo_mirror_hook.py:65-81`). `_MIRRORED_CMDS`에 `mark`가 이미 포함되어 있다 (`:22`) — 훅 등록·필터 변경 불요.

**(11) 배포는 디렉토리 통째 복사다.**
`install_dir "$opal_dir/tools" "$opal_home/tools"` (`install-mac.sh:1111-1113`). 기존 파일 수정은 install 스크립트 변경 없이 그대로 배포된다.

**(12) 헤더 기록 소스는 inline이다.**
`.opal/code-scan.json`의 전역 `headerSource`가 `"inline"` — @header는 파일 상단 주석에 직접 기재한다 (`docs/CONVENTIONS.md` §구현 규칙/@header 규칙).

### 영향 범위

| 영역 | 영향 | 판정 |
|------|------|------|
| state-tool `mark` (CLOSE 마지막 행, status=done) | 신규 부수효과 1건(히스토리 append) + stdout 필드 1개 추가 | 변경 |
| state-tool `mark` (그 외 전 경로) | 조건 미충족 → 무발동 | 무변경 |
| state-tool `init`/`advance`/`block`/기타 8종 | 접촉 없음 | 무변경 |
| state.json 스키마·영속 필드 | 비영속 설계로 회피 | 무변경 |
| memory-tool 코드·스키마 | 기존 CLI 재사용만 | 무변경 |
| pilot 10종 SKILL.md | D-5 확정 | 무변경 |
| PostToolUse 훅 등록(`claude-hooks.json`·`merge-hooks.py`) | 동일 훅 파일 내부 확장 | 무변경 |
| 기존 테스트 263건 + 훅 12건 | ok() 페이로드에 키 1개 추가(임시 폴더에서는 `skipped`) | 무변경 기대 |

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|
| — | 없음 | 신규 파일 없음 — 기존 2개 도구 파일·2개 테스트 파일·1개 SSOT 문서 확장으로 완결 | [MUST] `~/.opal/PRINCIPLES.md` §2 Simplicity First |

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| M-1 | `opal/tools/state-tool/state_tool.py` | 히스토리 연동 헬퍼 6종 + 상수 3종 신설, `cmd_mark`에 접합 1블록, `ok()`에 `history_link` 필드, @header 갱신 | TASK R-1~R-5, R-7 |
| M-2 | `opal/tools/state-tool/todo_mirror_hook.py` | `extract_history_link()` 신설 + `build_additional_context()` 3번째 인자 + `main()` 2-페이로드 분기, @header 갱신 | TASK R-5 |
| M-3 | `opal/tools/state-tool/tests/test_state_tool.py` | `TestCloseHistoryLink` 신설(TS-1~TS-7), @header description·exports 갱신 | TASK 완료기준, D-8 §1 |
| M-4 | `opal/tools/state-tool/tests/test_todo_mirror_hook.py` | 훅 확장 케이스 신설(TS-8~TS-10), @header description·exports 갱신 | TASK R-5, D-8 §1 |
| M-5 | `opal/core/references/harness/memory-learning.md` | "CLOSE 자동 연결" 절 신설 + 갱신 트리거 문구 정정 + 변경이력 v1.4(088) 행 | TASK R-6 |
| M-6 | `docs/ARCHITECTURE.md` | `tools/` 행 memory-tool 서술에 CLOSE 자동 연결 1구 보강 (**PM 판단 — TASK §범위 밖**) | `docs/ARCHITECTURE.md:82` |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| — | 없음 | — |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | RED 테스트 작성·실패 증거 확보 | M-3, M-4 | 중 |
| 2 | state-tool 히스토리 연동 헬퍼 신설 | M-1 | 중 |
| 3 | `cmd_mark` 접합 + stdout 페이로드 | M-1 | 하 |
| 4 | 훅 리마인더 릴레이 확장 | M-2 | 하 |
| 5 | SSOT 문서 반영 | M-5 | 하 |
| 6 | @header·변경이력 갱신 | M-1~M-5 | 하 |
| 7 | 전체 회귀 + E2E 실증 | 전 파일 | 중 |
| 8 | install 배포 정합 확인 | — | 하 |

> 의존 원칙: 헬퍼(하위) → 호출부(상위) → 릴레이(외곽) → 문서. RED는 전 구현에 선행한다 ([MUST] `opal/core/references/harness/red-first.md` §1: "RED 단계에서 실패 테스트 코드를 작성·실행하여 실패(exit code≠0)를 증거로 기록한 뒤 GREEN(구현) 진입. RED 증거 없이 GREEN 진입 금지.").

---

### 핵심 설계

#### §2.1 [쟁점 1] 트리거 판정 — 기존 `is_close_last` 재사용

**결정: `_derive_next_action`의 프론티어 소진 신호를 쓰지 않고, `cmd_mark`가 이미 계산하는 `is_close_last` 지역 변수를 그대로 재사용한다.**

근거:
- `is_close_last`는 014 Phase 4에서 "CLOSE 마지막 행 판정 항목명 비의존화"를 위해 도입된 판정식이며 이미 `cmd_mark` 안에 존재한다 (`state_tool.py:1369-1373`). 새 판정 로직을 만들면 SSOT가 둘이 된다 ([MUST] `~/.opal/PRINCIPLES.md` §2 Simplicity First).
- `_derive_next_action`은 "첫 미완료 행" 프론티어를 반환하며 `na` 행을 완료로 간주한다 (`state_tool.py:490-504`, `_COMPLETE_STATUSES` `:449`). agentic 모드에서 사용자 확인 행이 `na`로 초기화되는 경로(`:637-643`)가 있어, 프론티어 소진과 "CLOSE 마지막 행 mark 성공"이 항상 일치한다고 보장할 수 없다. 트리거를 프론티어에 걸면 **mark 대상 행이 아닌 다른 행의 상태 때문에** 발동/미발동이 갈릴 수 있다.
- 발동 조건은 `is_close_last and row["status"] == "done"` — `cmd_mark:1375`가 `current_status="done"` 전환에 쓰는 것과 **동일한 조건**이다. 017의 다중 Step 조기 done 가드(`:1326-1336`)와 자동 정합된다(`--step 1/2`는 `in_progress`로 남아 발동하지 않음).

```
# 접합 위치: sync_state_md() 직후, 최종 ok() 직전 (state_tool.py:1418~1420 사이)
history_link = None
if is_close_last and row["status"] == "done":
    history_link = link_memory_history(task_path, state)
```

접합 위치 근거: state.json·STATE.md 영속화(`:1386` `save_state_json`, `:1415-1418` `sync_state_md`)가 **완전히 끝난 뒤** 부수효과를 실행한다. 히스토리 연동 실패가 파이프라인 상태 기록을 되돌리는 일이 없어야 하기 때문이다(R-4). TEST stage verify 훅(`:1389-1398`)은 `row["stage"] == "TEST"` 전용이라 CLOSE 경로와 상호작용하지 않는다.

#### §2.2 [쟁점 2] 호출 방식 — 형제 `memory_tool.py`를 `sys.executable` subprocess로 호출

**결정: `subprocess.run([sys.executable, <sibling memory_tool.py>, ...], timeout=10)`. import 금지, `run.sh` 경유 금지.**

| 후보 | 채택 | 사유 |
|------|:----:|------|
| `import memory_tool` | ✗ | memory-tool의 `err()`는 `sys.exit(1)`을 호출한다 (`memory_tool.py:164-177`). in-process import는 state-tool 프로세스를 통째로 종료시켜 R-4(비차단)를 정면 위반한다. 모듈 전역 `SCHEMA` 로드(`:42-65`) 부작용도 동반된다 |
| `run.sh` 경유 | ✗ | `run.sh`는 `$HOME/.opal/.venv/bin/python`을 강제한다 (`opal/tools/memory-tool/run.sh`). 프로젝트 소스 트리 테스트·venv 미구성 환경에서 실패하며, `$HOME` 하드코딩은 [MUST] `docs/CONVENTIONS.md` §구현 규칙/플랫폼 분기 격리 취지에 어긋난다 |
| **`sys.executable` + 형제 경로** | ✓ | state-tool과 memory-tool은 항상 같은 `tools/` 부모를 공유한다(소스 트리 `opal/tools/`, 배포본 `~/.opal/tools/`). memory-tool은 표준 라이브러리 전용이므로(`memory_tool.py:27-36`) 동일 인터프리터로 실행 가능. `get_kst_datetime`의 subprocess 선례와 동형 (`state_tool.py:174-181`) |

```
_MEMORY_TOOL = pathlib.Path(__file__).resolve().parent.parent / "memory-tool" / "memory_tool.py"
```

**락 상호작용 검증**: state-tool은 어떤 파일 락도 획득하지 않는다(§1 현재 상태 (3)). memory-tool은 자식 프로세스 안에서 `<MEMORY.json>.lock`을 획득·해제한다 (`memory_tool.py:364-406`). 부모가 락을 보유하지 않으므로 중첩 락·데드락이 성립하지 않는다. 자식 락 대기 상한은 5초(`:152`)이고 부모 subprocess timeout은 10초이므로, 락 경합 시에도 부모가 먼저 죽지 않고 자식의 `lock_timeout` JSON을 정상 수신한다.

#### §2.3 [쟁점 3] MEMORY.json 경로 해석 — 조상 디렉토리 앵커 탐색

**결정: `<task-path>`에서 시작해 조상 디렉토리를 위로 훑어, `<dir>/.opal/MEMORY.json`이 파일로 존재하는 첫 디렉토리를 프로젝트 루트로 확정한다. 없으면 비차단 스킵.**

```
def find_project_root(task_path):
    """task_path의 조상 중 .opal/MEMORY.json을 가진 첫 디렉토리. 없으면 None."""
    p = pathlib.Path(task_path).resolve()
    for cand in (p, *p.parents):
        if (cand / ".opal" / "MEMORY.json").is_file():
            return cand
    return None
```

근거:
- 저장소 위치가 `{프로젝트}/.opal/MEMORY.json`으로 SSOT에 고정되어 있다 (`memory-learning.md:11`). `tasks/` 계층 깊이를 가정하지 않으므로 `tasks/<폴더>/`뿐 아니라 `tasks/backup/<폴더>/` 같은 변형에도 견딘다.
- 환경변수·설정 키를 새로 만들지 않는다 ([MUST] `~/.opal/PRINCIPLES.md` §2 Simplicity First — "No speculative abstraction or unrequested flexibility").
- **부재 시 동작**: `None` 반환 → `history_link = {"status": "skipped", "warning": "..."}`로 즉시 반환하고 subprocess를 아예 띄우지 않는다. 기존 263개 테스트는 `tempfile.mkdtemp()` 하위에서 돌므로(`test_state_tool.py:150-153`) 전부 이 조기 반환 경로를 타 성능·부작용 영향이 0이다.
- `path` 필드는 이 루트를 기준으로 산출한다: `task_path.resolve().relative_to(project_root).as_posix() + "/"` → `tasks/088-260811-opp-클로즈-메모리히스토리-자동연결/` (현행 데이터 표기와 일치, §1 (7)).

#### §2.4 [쟁점 4] 멱등성(R-3) — `path` 일치 사전 조회, memory-tool 무변경

**결정: 판정 키는 `path`. state-tool이 `memory_tool.py show --file <MEMORY.json>`로 사전 조회하여 동일 `path` 행이 있으면 append를 건너뛴다. memory-tool에는 신규 서브명령·플래그를 추가하지 않는다.**

근거:
- `path`는 태스크 폴더 1:1 대응이며 도구가 결정론적으로 산출하는 값이다. `title`은 PM이 `update --new-title`로 바꿀 수 있어(`memory_tool.py:1048-1053`) 멱등 키로 불안정하다. `date`는 재mark 일자가 다를 수 있다.
- `show`는 read-only이며 `history_rows`를 전량 반환한다 (`memory_tool.py:1273-1318`). MEMORY.json 파일 포맷 지식을 state-tool에 복제하지 않고 **공개 CLI 계약만 소비**한다 — 도구 경계 보존.
- memory-tool에 `--if-absent` 같은 신규 옵션을 추가하지 않는 이유: [MUST] `~/.opal/PRINCIPLES.md` §2 Simplicity First. TASK.md §범위 "제외: memory-tool CLI 신규 서브명령"과도 정합.
- FIFO·정정은 그대로 memory-tool 소유 (`memory_tool.py:982` `_enforce_history_fifo`) — state-tool은 재구현하지 않는다(TASK §제약).
- `show` 실패(rc≠0 / JSON 파싱 실패)는 **append를 시도하지 않고** `failed`로 종료한다 — 중복 위험(R-3)을 뚫느니 생성을 포기하는 쪽이 안전하다.

#### §2.5 [쟁점 5] 실패 비차단(R-4) — stdout 전용 `history_link` 필드

**결정: mark 응답은 항상 `ok: true`를 유지하고, 결과·경고를 `ok()` stdout 페이로드의 `history_link` 객체로 표면화한다. state.json에는 아무것도 쓰지 않는다.**

```
"history_link": {
  "status":  "created" | "duplicate_skipped" | "skipped" | "failed",
  "title":   "088 클로즈 메모리히스토리 자동연결",
  "path":    "tasks/088-260811-opp-클로즈-메모리히스토리-자동연결/",
  "stage":   "완료",
  "memory_file": "<abs>/.opal/MEMORY.json",
  "reminder": "…",            # status ∈ {created, duplicate_skipped}
  "warning":  "…"             # status ∈ {skipped, failed}
}
```

| status | 조건 | warning 내용 |
|--------|------|-------------|
| `created` | append 성공 | — |
| `duplicate_skipped` | 동일 `path` 행이 이미 존재 | — |
| `skipped` | 프로젝트 루트/`MEMORY.json` 미탐지, 또는 `memory_tool.py` 부재 | 미탐지 대상 경로 |
| `failed` | `show`/`append` rc≠0·타임아웃·JSON 파싱 실패·예외 | memory-tool `error`/`message` 또는 예외 요약 |

근거:
- [MUST] `opal/tools/state-tool/schema/state.schema.json` §root: `"additionalProperties": false` — 신규 영속 필드는 스키마 동반 갱신을 강제한다. 076 `todo_mirror`가 정확히 같은 이유로 stdout 전용·비영속을 택했다 (`state_tool.py:452-460` docstring: "비영속 — ok() stdout 페이로드에만 사용하며 save_state_json 미접촉 (H-3, state.schema.json §root additionalProperties:false 위반 회피)"). 동일 선례를 답습한다.
- **`err()`를 절대 호출하지 않는다** — `err()`는 `sys.exit`한다 (`state_tool.py:148-162`). 연동 함수는 최상위 `try/except Exception`으로 감싸 어떤 예외도 payload로 강등한다(brain-ingest no-op 비차단 패턴 답습, TASK R-4 §왜).
- `subprocess.run(..., timeout=10)`의 `TimeoutExpired`도 같은 except가 흡수한다.

#### §2.6 [쟁점 6] `result` 초기값 — 식별 가능한 플레이스홀더

**결정: `HISTORY_RESULT_PLACEHOLDER = "(PM 보강 대기)"`를 `--summary`로 전달한다. 빈 문자열을 쓰지 않는다.**

근거:
- 스키마상 `result`는 `{"type": "string"}`뿐이라 빈 문자열도 통과한다 (`memory.schema.json:92-95`). 그러나 같은 스키마가 `result`를 `"핵심결과 [MUST]. 무엇을 바꿨는지 + 결과"`로 규정하므로, 빈 값은 **미기재인지 의도된 공란인지 구분 불가**하다.
- 플레이스홀더가 있으면 PM·사람·후속 도구가 `MEMORY.json`만 보고 미보강 행을 즉시 식별한다(R-5 AC의 "PM이 보강해야 함을 식별할 수 있는 값").
- `append --kind history`의 `--summary`는 그대로 `result`에 매핑되고 80자 캡이 걸리지 않는다 (`memory_tool.py:970-980`; 캡은 memory 분기 `:947-949` 전용). 플레이스홀더 길이는 무제약.
- `title` 파생: `HISTORY_TITLE_PATTERN = re.compile(r"^(\d{3})-\d{6}-[a-z]+-(.+)$")`로 `state["task_id"]`를 분해해 `f"{번호} {나머지.replace('-', ' ')}"`를 만든다. 예: `088-260811-opp-클로즈-메모리히스토리-자동연결` → `088 클로즈 메모리히스토리 자동연결`. 현행 5개 행의 `"{번호} {제목구}"` 표기와 정합하며(§1 (7)), 패턴 불일치 시 `task_id` 원문으로 폴백한다. state.json에는 태스크 제목 필드가 없고 `task_id`가 유일한 제목 원천이다 (`state_tool.py:1017-1018`, `:1028-1038` — `task_title`은 STATE.md 렌더 전용이라 영속되지 않음). 표현이 마음에 들지 않으면 PM이 `update --kind history --new-title`로 정정한다 (`memory_tool.py:1048-1053`).
- `stage`: `HISTORY_STAGE_DONE = "완료"` (→ D-15 §확정 방향 D-6).

#### §2.7 [쟁점 7] 리마인더 페이로드(R-5) — 즉시 실행 가능한 명령 문자열 + 훅 병존 확장

**결정: `history_link.reminder`에 그대로 붙여넣어 실행 가능한 `update --kind history` 명령을 담는다. 훅은 기존 `todo_mirror` 주입을 유지한 채 리마인더를 덧붙이는 병존 구조로 확장한다(교체 아님).**

리마인더 문자열 형식:

```
[메모리 히스토리] 작업 히스토리 행이 자동 생성되었다(핵심결과 미기재). 지금 보강하라:
"$HOME/.opal/tools/memory-tool/run.sh" update --file <memory_file> --kind history --title "<title>" --result "<무엇을 바꿨는지 + 결과>"
```

- `title`을 도구가 파생하므로(§2.6) PM이 제목을 추측할 필요가 없도록 **실제 사용된 title을 문자열에 박아** 넣는다.
- PM 실행 경로는 사용자 대면 표준인 `run.sh`로 안내한다(내부 호출이 `sys.executable`인 것과 무관 — 안내 대상은 PM이다).

훅 확장 (`todo_mirror_hook.py`):

| 대상 | 변경 |
|------|------|
| `extract_todo_mirror(stdout)` | 내부를 `_extract_payload(stdout, "todo_mirror")`로 위임(동작·시그니처 불변 → D-11 기존 테스트 보존) |
| `extract_history_link(stdout)` | 신설 — `_extract_payload(stdout, "history_link")` |
| `build_additional_context(command_name, payload, history_link=None)` | 3번째 인자 **선택**으로 추가. `history_link["reminder"]`가 있으면 개행 후 덧붙인다. 기본값 `None`이라 기존 호출·테스트 무영향 |
| `main()` | 두 페이로드를 모두 추출 → **둘 다 없으면** 무출력 return(기존 fail-safe 유지), 하나라도 있으면 컨텍스트 출력 |

- `_MIRRORED_CMDS`에 `mark`가 이미 있어 필터 변경 불요 (`todo_mirror_hook.py:22`). `claude-hooks.json:8`·`merge-hooks.py` 무변경.
- 모듈명 `todo_mirror_hook`은 **바꾸지 않는다** — `claude-hooks.json:8`이 파일 경로를 직접 참조하고, 이미 배포된 사용자 `settings.json`에도 같은 경로가 박혀 있다. 개명은 [MUST] `docs/CONVENTIONS.md` §구현 규칙/배포 경계 하에서 불필요한 파급을 만든다. @header `description`에 역할 확장을 명시하는 것으로 대체한다.
- [MUST] `opal/tools/state-tool/todo_mirror_hook.py:126-130`: "DEC-9: 전 경로 fail-safe — 어떤 예외에서도 정상 도구 흐름을 차단하지 않는다." → 확장 코드도 이 계약을 깨지 않는다(예외 시 무출력 exit 0).
- **훅 미설정 환경 보증**: 리마인더 원문은 state-tool stdout(`history_link.reminder`)에 이미 존재하므로, 훅이 없어도 동일 문자열이 남는다(R-5 AC 후단).

#### §2.8 [쟁점 8] 회귀 범위 — 기존 테스트가 깨지지 않는 조건

| 조건 | 확인 |
|------|------|
| 기존 263개 state-tool 테스트가 CLOSE 마지막 행을 mark함 (`test_state_tool.py:434-447`, `:868-895`, `:1214-1260`) | 전부 `tempfile.mkdtemp()` 하위(`:150-153`)라 조상에 `.opal/MEMORY.json`이 없음 → `find_project_root()` `None` → subprocess 미실행·MEMORY.json 무접촉 |
| `ok()` 페이로드에 키 1개 추가 | 기존 테스트는 개별 키를 조회하지 `assertEqual(result, {...})` 전량 비교를 하지 않음(`_call_cmd` 반환 dict 부분 조회 패턴, `:158-174`) |
| state.json 스키마 검증 테스트 | `history_link` 미영속이므로 `additionalProperties:false` 무위반(076 TS-007 선례와 동형) |
| 훅 테스트 12건 (`test_todo_mirror_hook.py`) | `build_additional_context` 3번째 인자 기본값 `None`, `extract_todo_mirror` 시그니처·동작 불변, "페이로드 부재 → 무출력" 케이스는 두 키 모두 부재라 그대로 통과 |
| `subprocess` 신규 import | 불필요 — `state_tool.py:16-24`에 이미 존재 |

**금지 사항 (재해석 금지)**:
- [MUST] `opal/core/references/harness/red-first.md` §3 테스트 불변성: "GREEN/fix 루핑 중 RED 테스트 파일 수정 금지. 위반 시 블로커."
- [MUST] `opal/core/references/harness/coding-principles.md` §4 EXECUTE: "PLAN.md에 명시된 파일만 변경되었는가 / 인접 코드를 개선 명목으로 수정하지 않았는가"

#### §2.9 신설 심볼 목록 (M-1)

| 심볼 | 종류 | 역할 |
|------|------|------|
| `HISTORY_STAGE_DONE` | 상수 | `"완료"` (D-6) |
| `HISTORY_RESULT_PLACEHOLDER` | 상수 | `"(PM 보강 대기)"` (§2.6) |
| `HISTORY_TITLE_PATTERN` | 상수 | task_id 분해 정규식 (§2.6) |
| `find_project_root(task_path)` | 함수 | 조상 앵커 탐색 (§2.3) |
| `derive_history_title(task_id)` | 함수 | title 파생 + 폴백 (§2.6) |
| `build_history_reminder(title, memory_file)` | 함수 | 리마인더 문자열 (§2.7) |
| `_run_memory_tool(argv)` | 함수 | subprocess 실행 + 마지막 JSON 라인 파싱 → `(rc, dict\|None)` (§2.2) |
| `link_memory_history(task_path, state)` | 함수 | 오케스트레이션 — 항상 payload dict 반환, 예외 무전파 (§2.5) |

`link_memory_history`는 `@header` `exports`에 추가한다(공개 계약 — 테스트가 직접 호출 가능). 나머지 헬퍼는 내부 구현이다.

---

## 3. 실행 체크리스트

> 총 10개 Step (Phase A 1 / Phase B 3 / Phase C 2 / Phase D 4)
> Phase 내부는 전부 **순차** — Phase A·B·C가 동일 파일군을 연속 편집하므로 병렬 실행 대상이 없다.

### Step 1: RED 테스트 작성 및 실패 증거 확보

- [x] 완료 (PM 재검증: `test_state_tool` 269건 중 신규 7 FAIL / `test_todo_mirror_hook` 15건 중 신규 3 FAIL, 기존 274건 PASS)
- **agent**: `opal-test-agent` (mode: red)
- **파일**: `opal/tools/state-tool/tests/test_state_tool.py` (M-3), `opal/tools/state-tool/tests/test_todo_mirror_hook.py` (M-4)
- **작업 내용**:
  - `test_state_tool.py`에 `TestCloseHistoryLink(BaseTestCase)` 신설. 픽스처: `tmpdir/.opal/MEMORY.json`(유효 문서 `{"version":1,"last_task_number":0,"memories":[],"history":[]}`) + `tmpdir/tasks/088-260811-opp-테스트-태스크/`를 task_path로 사용. CLOSE 진입 게이트 충족을 위해 직전 `사용자 확인` 행을 `owner="user"`로 mark(`test_state_tool.py:434-447` 픽스처 패턴 재사용).
  - **TS-1 (R-1/R-2)**: CLOSE 마지막 행 mark → `MEMORY.json` `history[0]`에 1건 생성. `title == "088 테스트 태스크"`, `path == "tasks/088-260811-opp-테스트-태스크/"`, `stage == "완료"`, `date`가 `^\d{4}-\d{2}-\d{2}$`, `result == "(PM 보강 대기)"`. 응답 `history_link.status == "created"`.
  - **TS-2 (R-3)**: 동일 mark를 2회 연속 실행 → 해당 `path` 행이 정확히 1건. 2회차 `history_link.status == "duplicate_skipped"`.
  - **TS-3 (R-4a)**: `.opal/MEMORY.json` 부재 상태로 mark → `ok: true`, `history_link.status == "skipped"`, `warning` 비공백.
  - **TS-4 (R-4b)**: `MEMORY.json`을 손상된 JSON으로 덮어쓴 뒤 mark → `ok: true`, `history_link.status == "failed"`, `warning` 비공백 (블랙박스 결함 주입 — 내부 mock 없음).
  - **TS-5 (회귀)**: 비CLOSE 행 mark → `history_link` 미포함, `MEMORY.json` `history` 길이 불변.
  - **TS-6 (R-5)**: `history_link.reminder`에 `update`·`--kind history`·`--result`·실제 `title` 문자열이 모두 포함.
  - **TS-7 (영속 경계)**: mark 후 `state.json`에 `history_link` 키 없음 + `state.schema.json` 검증 통과 (076 TS-007 패턴).
  - `test_todo_mirror_hook.py`에 **TS-8** (stdout에 `todo_mirror`+`history_link` → `additionalContext`에 reminder 원문 포함), **TS-9** (`history_link` 부재 기존 payload → 기존 주입 동작 불변), **TS-10** (`history_link`만 있고 `todo_mirror` 부재 → exit 0 + reminder 주입) 추가.
  - 검증은 공개 인터페이스(`ST.cmd_mark` 호출 후 stdout 캡처 / 훅 스크립트 subprocess)로만 수행한다.
- **완료 기준**: 신규 10개 케이스가 **전부 FAIL**하고, 실패 출력(exit code ≠ 0 + 실패 케이스 목록)이 증거로 기록된다. 기존 263+12건은 이 시점에도 전건 PASS.
- **테스트**: `python3 -m unittest opal.tools.state-tool.tests... ` 상당 경로로 두 테스트 파일 실행 → 실패 로그 캡처
- **의존**: 없음
- **커버**: R-1, R-2, R-3, R-4, R-5

### Step 2: state-tool 히스토리 연동 헬퍼 신설

- [x] 완료
- **agent**: `opal-task-agent`
- **파일**: `opal/tools/state-tool/state_tool.py` (M-1)
- **작업 내용**: §2.9의 상수 3종 + 함수 5종을 신설한다. 배치는 `build_todo_mirror`/`_derive_next_action` 인접(`state_tool.py:452-505` 이후)에 새 구분선 블록으로 둔다. `link_memory_history()`는 ① `find_project_root` → `None`이면 `skipped` ② `_MEMORY_TOOL` 부재면 `skipped` ③ `show`로 `history_rows` 조회 → 실패 시 `failed` ④ 동일 `path` 존재 시 `duplicate_skipped` ⑤ `append --kind history --title/--stage/--path/--summary` → rc≠0이면 `failed` ⑥ 성공 시 `created`. 전체를 `try/except Exception`으로 감싸 `failed` payload로 강등한다. `err()` 호출 금지.
- **완료 기준**: 함수 단독 호출 시 어떤 입력(존재하지 않는 경로, 손상 JSON, 타임아웃)에도 예외를 전파하지 않고 반드시 dict를 반환한다. 표준 라이브러리 외 import 0건. `state_tool.py` 문법 검사 통과(`python3 -m py_compile`).
- **테스트**: Step 1의 TS-1~TS-4가 `history_link` 미접합 상태에서도 헬퍼 단위로는 통과 가능한지 확인(접합 전이므로 mark 경유 케이스는 여전히 FAIL)
- **의존**: Step 1
- **커버**: R-1, R-2, R-3, R-4

### Step 3: `cmd_mark` 접합 + stdout 페이로드 노출

- [x] 완료
- **agent**: `opal-task-agent`
- **파일**: `opal/tools/state-tool/state_tool.py` (M-1)
- **작업 내용**: `sync_state_md(...)` 호출 직후·최종 `ok(...)` 직전(`state_tool.py:1415-1422` 구간)에 §2.1 접합 블록을 삽입하고, `ok()` 호출에 `history_link`를 **값이 있을 때만** 추가한다(비CLOSE 경로에 키가 생기지 않도록 — TS-5). `state.json`에는 어떤 필드도 추가하지 않는다.
- **완료 기준**: TS-1~TS-7이 전부 GREEN. `git diff`상 `save_state_json`·`schema/state.schema.json` 무변경. 비CLOSE mark 응답에 `history_link` 키 부재.
- **테스트**: `test_state_tool.py` 전체 실행 → 263+7건 전건 PASS
- **의존**: Step 2
- **커버**: R-1, R-2, R-3, R-4, R-5

### Step 4: 훅 리마인더 릴레이 확장

- [x] 완료
- **agent**: `opal-task-agent`
- **파일**: `opal/tools/state-tool/todo_mirror_hook.py` (M-2)
- **작업 내용**: §2.7 표대로 `_extract_payload` 일반화, `extract_history_link` 신설, `build_additional_context`에 선택 인자 `history_link=None` 추가, `main()` 2-페이로드 분기. `_STATE_TOOL_SIG`·`_MIRRORED_CMDS`·모듈명·`claude-hooks.json`은 건드리지 않는다. 전 경로 무출력 exit 0 fail-safe 유지.
- **완료 기준**: TS-8~TS-10 GREEN + 기존 훅 테스트 12건 전건 PASS. 훅 스크립트를 깨진 stdin/stdout으로 실행해도 exit code 0.
- **테스트**: `test_todo_mirror_hook.py` 전체 실행
- **의존**: Step 3
- **커버**: R-5

### Step 5: SSOT 문서 반영 (memory-learning.md)

- [x] 완료
- **agent**: `opal-task-agent`
- **파일**: `opal/core/references/harness/memory-learning.md` (M-5)
- **작업 내용**: "## CLOSE 자동 연결" 절을 신설하여 ① 트리거(=CLOSE 마지막 행 `mark` 성공, `state-tool`이 집행) ② 역할 분담 — **생성=도구 / `result` 보강=PM** ③ 단계값 `완료` 규약(커밋은 CLOSE 밖) ④ 보강 명령 `update --kind history --title <t> --result <r>` ⑤ 실패는 비차단(mark는 성공)임을 명문화한다. 기존 `:16` 갱신 트리거 불릿의 "태스크 완료" 항목이 이제 도구 집행임을 가리키도록 문구를 정정한다. 변경이력 표에 `v1.4 | 2026-08-11 | 088 CLOSE 자동 연결 절 신설 …` 행을 추가한다.
- **완료 기준**: 문서에 CLOSE 자동 연결 절이 존재하고 위 ①~⑤가 모두 기재되며, 변경이력에 088 행이 추가된다. pilot 10종 SKILL.md는 무변경(`git status`로 확인).
- **테스트**: 문서 육안 검토 + `git diff --stat`로 변경 파일이 memory-learning.md 1건인지 확인
- **의존**: Step 4
- **커버**: R-6

### Step 6: @header·변경이력 갱신

- [x] 완료
- **agent**: `opal-task-agent`
- **파일**: `state_tool.py`, `todo_mirror_hook.py`, `test_state_tool.py`, `test_todo_mirror_hook.py`
- **작업 내용**: 4개 파일의 인라인 `@header` `description` 말미에 `088: …` 문장을 append한다(기록 소스 `inline` — `.opal/code-scan.json` `headerSource`). `state_tool.py` `exports`에 `link_memory_history`, `todo_mirror_hook.py` `exports`에 `extract_history_link`, 테스트 2종 `exports`에 신규 테스트 클래스명을 추가한다. 기존 서술은 삭제하지 않고 누적한다(076·074 선례).
- **완료 기준**: `code-scan`이 4개 파일의 헤더를 정상 파싱하고, `description`에 088 변경 내용이 포함된다 ([MUST] `docs/CONVENTIONS.md` §구현 규칙/@header 규칙).
- **테스트**: `~/.opal/tools/code-scan/run.sh scan` 또는 `validate`로 헤더 파싱 확인
- **의존**: Step 5
- **커버**: R-7

### Step 7: 전체 회귀 실행

- [x] 완료
- **agent**: `opal-task-agent`
- **파일**: (실행만)
- **작업 내용**: `test_state_tool.py`(263 + 신규 7) + `test_todo_mirror_hook.py`(12 + 신규 3)를 전건 실행한다. 실패 0건을 실행 출력으로 증거화한다.
- **완료 기준**: 두 스위트 exit code 0, 실패·에러 0건. 실행 출력이 산출물에 첨부된다 ([MUST] `opal/core/references/harness/coding-principles.md` §4: "완료 선언에 동작 증거(실행 출력/실응답)가 첨부되었는가").
- **테스트**: unittest 실행 출력 캡처
- **의존**: Step 6
- **커버**: TASK §완료기준 4번째 항목(기존 state-tool 테스트 전건 통과)

### Step 8: E2E 실증 (완료기준 3종)

- [x] 완료
- **agent**: `opal-task-agent`
- **파일**: (샌드박스 실행만 — 프로젝트 파일 무변경)
- **작업 내용**: 임시 디렉토리에 가짜 프로젝트 루트(`<tmp>/.opal/MEMORY.json` + `<tmp>/tasks/<태스크폴더>/`)를 구성하고, **`run.sh` 공개 CLI**로 `init` → 단계별 `mark` → CLOSE 마지막 행 `mark`를 실행한다. ① 히스토리 1건 자동 생성 ② 동일 mark 재실행 시 중복 0건 ③ `MEMORY.json` 손상 주입 시 mark `ok: true` 유지를 실제 stdout/파일 내용으로 실증한다. **실 프로젝트 `.opal/MEMORY.json`은 이 Step에서 건드리지 않는다.**
- **완료 기준**: 3종 실증 각각에 대해 실행 명령 + stdout JSON + `MEMORY.json` 내용 발췌가 증거로 남는다. 실 프로젝트 `.opal/MEMORY.json`의 `git diff`가 0.
- **테스트**: 위 실행 출력 자체가 증거
- **의존**: Step 7
- **커버**: R-1, R-2, R-3, R-4, R-5 (TASK §완료기준 1~3)

### Step 9: install 배포 정합 확인

- [x] 완료 (PM 직접 확인: `state_tool.py`·`todo_mirror_hook.py` 배포본 diff 0줄, `~/.opal/references/harness/memory-learning.md`에 CLOSE 자동 연결 절 반영)
- **agent**: `opal-task-agent`
- **파일**: (실행·검증만 — `scripts/install-mac.sh` 무변경)
- **작업 내용**: `./scripts/install-mac.sh`를 재실행한 뒤 `diff` 로 `~/.opal/tools/state-tool/state_tool.py`·`todo_mirror_hook.py`가 프로젝트 소스와 동일한지 확인한다(변경이력 strip 대상은 .md뿐이므로 .py는 완전 동일해야 한다). `~/.opal/references/harness/memory-learning.md`에 신규 절이 반영되었는지도 확인한다. install 스크립트 자체는 수정하지 않는다 — `install_dir "$opal_dir/tools"`가 이미 전체를 복사한다 (`install-mac.sh:1111-1113`).
- **완료 기준**: 두 .py 파일의 diff가 0줄이고, 배포된 memory-learning.md에 CLOSE 자동 연결 절이 존재한다. [MUST] `docs/CONVENTIONS.md` §구현 규칙/배포 경계 준수 — `~/.opal/` 직접 편집 0건.
- **테스트**: `diff <(cat opal/tools/state-tool/state_tool.py) ~/.opal/tools/state-tool/state_tool.py` 출력
- **의존**: Step 8
- **커버**: R-7

### Step 10: docs/ 갱신 (아키텍처 1행) — PM 판단

- [-] 해당 없음 — **PM 불채택**(2026-08-11). TASK.md §범위 밖이며, CLOSE 단계 표준 스텝 "관련 문서 업데이트"(`opal/skills/opal-pilot-project/SKILL.md:123-126`)가 동일 역할을 이미 소유하므로 EXECUTE 범위를 넓히지 않고 CLOSE에서 처리한다.
- **agent**: **PM 직접**
- **파일**: `docs/ARCHITECTURE.md` (M-6)
- **작업 내용**: `docs/ARCHITECTURE.md:82` `tools/` 행의 memory-tool 서술에 "CLOSE 마지막 행 mark 시 state-tool이 히스토리 행을 자동 생성(생성=도구/result 보강=PM)" 취지의 1구를 보강하고, 문서 하단 변경이력 표에 2026-08-11 / Task 088 행을 추가한다.
- **완료 기준**: 해당 행이 도구 간 호출 관계를 반영하고 변경이력 행이 추가된다.
- **테스트**: 문서 육안 검토
- **의존**: Step 9
- **비고**: **TASK.md §범위(포함 목록)에 없는 항목**이다. 코드 변경이 `docs/` 서술에 영향을 주므로 후보로 올리되, 범위 초과 여부는 PM이 판정한다 — 불채택 시 이 Step은 `-`(해당 없음) 처리한다.
- **커버**: (범위 외 보완)

### 요구사항 커버 매트릭스

| 요구사항 | 커버 Step | 검증 케이스 |
|---------|----------|-----------|
| R-1 히스토리 자동 생성 | 1, 2, 3, 8 | TS-1, E2E ① |
| R-2 필드 자동 충전 | 1, 2, 3, 8 | TS-1 |
| R-3 중복 방지(멱등) | 1, 2, 3, 8 | TS-2, E2E ② |
| R-4 실패 비차단 | 1, 2, 3, 8 | TS-3, TS-4, E2E ③ |
| R-5 result 보강 리마인더 | 1, 3, 4, 8 | TS-6, TS-8, TS-9, TS-10 |
| R-6 SSOT 문서 반영 | 5 | 문서 검토 |
| R-7 배포 정합 | 6, 9 | @header 파싱, install diff 0 |

---

## 4. QA 체크리스트

### 기능 테스트

- [ ] CLOSE 마지막 행 mark 1회 → `MEMORY.json` `history[0]`에 해당 태스크 행 1건 생성
- [ ] 생성 행의 `title`/`path`/`stage`/`result`가 §2.6 규약대로 채워짐 (`stage == "완료"`)
- [ ] `date`가 memory-tool이 채운 KST 당일(`^\d{4}-\d{2}-\d{2}$`)
- [ ] 동일 mark 2회 연속 → 해당 `path` 행 정확히 1건, 2회차 `duplicate_skipped`
- [ ] `MEMORY.json` 부재 → mark `ok: true` + `history_link.status == "skipped"` + warning
- [ ] `MEMORY.json` 손상 → mark `ok: true` + `history_link.status == "failed"` + warning
- [ ] 비CLOSE 행 mark → `history_link` 미출력, `MEMORY.json` 무변경
- [ ] `--step 1/2`로 CLOSE 행을 in_progress 유지 → 히스토리 미생성 (017 가드 정합)
- [ ] 훅 stdin에 `history_link` 포함 → `additionalContext`에 reminder 원문 포함
- [ ] 훅 미설정(스크립트 미실행) 상태에서도 mark stdout에 reminder 문자열 존재

### 일관성 테스트

- [ ] `state.json`에 신규 필드 0건 — `state.schema.json` `additionalProperties:false` 무위반
- [ ] `memory_tool.py`·`memory.schema.json` 무변경 (`git status`)
- [ ] pilot 10종 SKILL.md 무변경 (D-5)
- [ ] `claude-hooks.json`·`merge-hooks.py`·`install-mac.sh` 무변경
- [ ] FIFO·정정 로직이 state-tool에 복제되지 않음 (memory-tool 위임만)
- [ ] 신규 함수·필드명이 영문 ([MUST] `docs/CONVENTIONS.md` §언어 규칙), 값 `완료`만 한국어
- [ ] state-tool이 표준 라이브러리만 사용 (신규 의존 0)
- [ ] 기존 275건(263+12) 회귀 전건 PASS

### 문서 품질

- [ ] `memory-learning.md`에 CLOSE 자동 연결 절 존재 + "생성=도구 / result 보강=PM" 명시
- [ ] 단계값 `완료` 규약이 명문화되고 `완료·커밋` 표기가 폐기됨을 알 수 있음
- [ ] `memory-learning.md` 변경이력에 v1.4 (088) 행 추가
- [ ] 변경한 4개 코드 파일 @header `description`에 088 내용 반영 + `exports` 갱신
- [ ] 배포본과 소스가 동일(install diff 0), `~/.opal/` 직접 편집 0건

---

## 5. 리스크 및 대응

| # | 리스크 | 영향 | 대응 방안 |
|---|--------|------|----------|
| R-A | **두 도구 간 파일 락 상호작용** — state-tool이 memory-tool을 자식 프로세스로 호출 | 데드락 시 mark 영구 정지 | state-tool은 락을 전혀 획득하지 않음(§1 (3))이 확인됨 → 중첩 락 불성립. 자식 락 대기 상한 5초 < 부모 subprocess timeout 10초로 부모가 먼저 죽지 않음. 타임아웃 시에도 `failed` payload로 강등(§2.5) |
| R-B | **기존 태스크 폴더로 mark 재실행 시 부작용** — 완료된 과거 태스크의 CLOSE 행을 다시 mark | 중복 히스토리 행 / 오래된 태스크가 `history[0]`로 부상 | `path` 사전 조회로 중복 append 차단(§2.4). 단 **FIFO=5로 이미 밀려난 태스크**를 재mark하면 신규 행으로 재삽입될 수 있음 → 발생가능성 낮음·영향 낮음(정보 재게시일 뿐 데이터 손실 없음)이므로 대응 없음, Known Issue로 기록 ([MUST] `opal/core/references/harness/coding-principles.md` §3 희박 케이스 매트릭스 "낮음/낮음 → 시나리오 제외 또는 Known Issue 기록") |
| R-C | **show→append 사이의 TOCTOU** — 두 subprocess 사이에 타 프로세스가 같은 행을 추가 | 중복 1건 | mark는 PM 단일 세션의 순차 명령이며 동시 실행 시나리오가 없음. 발생가능성 낮음·영향 낮음 → 대응 없음(Known Issue) |
| R-D | **레거시 `MEMORY.md`만 있는 프로젝트** — `MEMORY.json` 부재로 앵커 미탐지 | 히스토리 자동 생성 무발동 | `skipped` + warning으로 표면화(비차단). 078 전환으로 현행 프로젝트는 모두 JSON이며, memory-tool의 lazy 마이그레이션은 `--file` 지정 호출에서만 동작함 |
| R-E | **title 파생값이 PM 취향과 다름** — task_id 슬러그 기반 | 히스토리 가독성 저하 | state.json에 태스크 제목 필드가 없어 task_id가 유일 원천(§2.6). PM이 `update --kind history --new-title`로 정정 가능하며, 이 경로는 이미 존재(`memory_tool.py:1048-1053`) |
| R-F | **PM이 result를 보강하지 않음** | `(PM 보강 대기)` 행이 잔존 | reminder를 stdout + 훅 additionalContext 양쪽으로 이중 전달(§2.7). 플레이스홀더 문자열이 미보강 행을 즉시 식별시킴 |
| R-G | **모듈명 `todo_mirror_hook`이 역할과 불일치** | 가독성 | 개명 시 `claude-hooks.json:8`과 배포된 사용자 `settings.json` 경로가 깨짐 → 개명 불가 판정, @header description으로 역할 확장 명시(§2.7) |
| R-H | **테스트가 실 `.opal/MEMORY.json`을 오염** | 프로젝트 메모리 손상 | 전 테스트가 `tempfile.mkdtemp()` 하위에서 실행되어 앵커 미탐지(§2.8). E2E(Step 8)도 임시 프로젝트 루트를 별도 구성하며, 완료 기준에 실 `MEMORY.json` `git diff` 0을 명시 |
| R-I | **범위 초과 — `docs/ARCHITECTURE.md`** | Simplicity 위반 소지 | Step 10을 PM 판단 조건부로 분리하고 TASK §범위 밖임을 명시 |

### 용어 일관성 검토 (citation-rules.md §7)

| 검출 대상 | 결과 |
|----------|------|
| state-tool `stage`(파이프라인 단계 enum: TASK/PLAN/CLOSE…) ↔ memory-tool `stage`(히스토리 단계 문자열 `"완료"`) | **동명이의 확인** — 같은 토큰이 두 도메인에서 다른 의미로 이미 사용 중이다. 이번 변경은 두 값을 혼용하지 않고 state-tool이 `HISTORY_STAGE_DONE = "완료"` 상수로 명시 변환하므로 결정성 이슈 아님. 개명은 memory.schema.json 파괴 변경이라 부적절 → `decision_required` 미발생 |
| `path`(historyRow) ↔ `task_path`(state-tool CLI 인자) | 전자는 프로젝트 루트 상대경로, 후자는 CLI 입력 경로. §2.3에서 변환 규칙을 명시하므로 모호성 없음 |

---

## 6. 리스크 가설 표 (변경 단위별)

> TEST-SCENARIO 단계가 없는 opp 파이프라인이므로, 아래 가설은 §3 Step 1의 RED 케이스와 §4 QA 체크리스트로 직접 소진된다.

| # | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 권고 검증 계층 | 대응 시나리오 |
|---|----------|-----------------|----------|--------------|--------------|
| H-1 | `cmd_mark` 접합 | mark의 "항상 ok 또는 명시적 error code" 계약 | CLOSE 진행 불가 → 태스크 마감 차단 | 단위(공개 CLI) | TS-3, TS-4 (부재·손상 주입 후 `ok: true`) |
| H-2 | `link_memory_history` | 예외 무전파 계약 | 미포착 예외가 mark를 크래시 | 단위 | TS-4 + 최상위 try/except 코드 리뷰 |
| H-3 | stdout 페이로드 확장 | `state.schema.json` `additionalProperties:false` | state.json 검증 실패 → validate 전면 실패 | 단위 + 스키마 검증 | TS-7 |
| H-4 | 사전 조회(`show`) | 멱등 계약 | 히스토리 중복 누적 → FIFO가 유효 이력 조기 폐기 | 단위 + E2E | TS-2, E2E ② |
| H-5 | 프로젝트 루트 앵커 탐색 | "임시 폴더에서는 무발동" 암묵 계약 | 테스트가 실 MEMORY.json 오염 | 단위 회귀 | TS-5 + 기존 263건 회귀, 실 `git diff` 0 확인 |
| H-6 | 훅 `build_additional_context` 시그니처 | 기존 2-인자 호출 계약 | 훅 크래시 → PostToolUse 노이즈 | 단위(훅 12건) | TS-9, TS-10 + 선택 인자 기본값 |
| H-7 | `memory-learning.md` 개정 | PM의 이중 기록 방지 계약 | PM이 수동 append를 병행해 중복 생성 | 문서 검토 | Step 5 완료 기준 ①~⑤ |
| H-8 | @header 갱신 | code-scan 파싱 계약 | 헤더 파싱 실패 → 코드 지도 붕괴 | 도구 검증 | Step 6 `code-scan` 확인 |

---

## 부록: 설계 쟁점 결정 요약

| 쟁점 | 결정 | 근거 절 |
|------|------|--------|
| 1. 트리거 판정 | `cmd_mark`의 기존 `is_close_last` + `status == "done"` 재사용 (프론티어 신호 미사용) | §2.1 |
| 2. 호출 방식 | 형제 `memory_tool.py`를 `sys.executable` subprocess로 (import·run.sh 배제), 데드락 불성립 | §2.2 |
| 3. 경로 해석 | 조상 디렉토리에서 `.opal/MEMORY.json` 앵커 탐색, 부재 시 비차단 스킵 | §2.3 |
| 4. 멱등성 | 키는 `path`. `show` 사전 조회로 판정, memory-tool 무변경 | §2.4 |
| 5. 실패 비차단 | `ok: true` 유지 + stdout 전용 `history_link.{status,warning}` (076 선례) | §2.5 |
| 6. result 초기값 | `"(PM 보강 대기)"` 플레이스홀더 (빈 문자열 배제) | §2.6 |
| 7. 리마인더 | 실행 가능한 `update --kind history` 명령 문자열, 훅은 기존 `todo_mirror`와 **병존 확장** | §2.7 |
| 8. 회귀 범위 | 임시 폴더 = 앵커 미탐지 → 무발동, 페이로드 키 추가·선택 인자 추가로 기존 275건 보존 | §2.8 |
