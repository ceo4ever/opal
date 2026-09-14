# xlsx-tool

> xlsx 파일의 메타데이터 조회·읽기·검색·쓰기를 담당하는 4서브명령 CLI
> 소스: `opal/tools/xlsx-tool/` | 배포: `~/.opal/tools/xlsx-tool/`
> 의존성: `~/.opal/.venv/bin/python` + **openpyxl** (소스가 실제로 import하는 유일한 외부 패키지)

## 개요

OPAL 스킬이 엑셀 파일을 다룰 때 쓰는 공용 창구다. 4개 서브명령(`info`/`read`/`search`/`write`)으로 구성되며 모든 응답은 단일 라인 JSON이다.

지원 확장자는 `.xlsx` `.xlsm` `.xltx` `.xltm` 4종이다(대소문자 무시). 그 외 확장자는 파일이 실재해도 거부한다.

## 호출 형식

```bash
~/.opal/tools/xlsx-tool/run.sh <command> <file> [options]
```

개발 중에는 소스 경로로 직접 호출한다.

```bash
bash opal/tools/xlsx-tool/run.sh <command> <file> [options]
```

## 출력 형식

```json
// 성공
{"ok": true, "command": "read", "file": "data.xlsx", "sheet": "2026", "data": [...]}

// 실패
{"ok": false, "command": "read", "error": "시트를 찾을 수 없습니다: 'foo' (전체: ['Sheet1'])"}
```

## 4개 서브 명령

### 1. `info` — 시트 목록과 구조

```bash
~/.opal/tools/xlsx-tool/run.sh info <file>
```

시트별로 `name`/`rows`(`max_row`)/`columns`(`max_column`)/`headers`를 돌려준다. `headers`는 **1행의 값 있는 셀만** 모은 목록이며(`--header-row` 같은 옵션이 없다), 1행이 비어 있으면 빈 배열이다.

**성공 응답**:
```json
{"ok": true, "command": "info", "file": "project.xlsx", "sheets": [{"name": "Sheet1", "rows": 42, "columns": 5, "headers": ["이름", "부서"]}]}
```

---

### 2. `read` — 데이터 읽기

```bash
~/.opal/tools/xlsx-tool/run.sh read <file> [--sheet <name|index>] [--range <A1:Z100>] [--header-row <n>]
```

| 옵션 | 기본값 | 설명 |
|------|-------|------|
| `--sheet` | 없음 | 시트 이름 또는 **0-기준 인덱스 문자열**. 생략하면 전 시트를 읽는다 |
| `--range` | 없음 | `A1:Z100` 형식. 지정 시 아래 "행 배열" 모드 |
| `--header-row` | `"1"` | 헤더로 쓸 행 번호(1-기준) |

출력 모양이 두 갈래다.

- `--range` **미지정**: `--header-row` 행을 키로 삼아 각 데이터 행을 dict로 만든다. 헤더 셀이 비어 있으면 `col_<인덱스>`로 대체된다.
- `--range` **지정**: 헤더 해석 없이 셀 값 2차원 배열(행 배열)을 그대로 돌려준다.

`--sheet`를 주면 `data`가 그 시트의 데이터이고, 생략하면 `data`가 `{시트명: 데이터}` 맵이다. 수식은 계산된 값으로 읽는다(`data_only=True`).

---

### 3. `search` — 키워드 검색

```bash
~/.opal/tools/xlsx-tool/run.sh search <file> --keyword <text> [--sheet <name|index>] [--range <A1:Z100>]
```

`--keyword`는 **필수**(argparse `required=True`)다. 셀 값을 문자열화해 **대소문자 무시 부분 일치**로 찾는다(정규식이 아니다). `--sheet` 생략 시 전 시트를 훑는다.

**성공 응답**:
```json
{"ok": true, "command": "search", "file": "wbs.xlsx", "keyword": "백엔드", "count": 2,
 "matches": [{"sheet": "Sheet1", "cell": "B7", "value": "백엔드 API"}]}
```

---

### 4. `write` — 신규 생성 또는 시트 갱신

```bash
~/.opal/tools/xlsx-tool/run.sh write <file> --data '<json>'       [--sheet <name>] [--mode new|update] [--format]
~/.opal/tools/xlsx-tool/run.sh write <file> --data-file <path.json> [--sheet <name>] [--mode new|update] [--format]
```

| 옵션 | 기본값 | 설명 |
|------|-------|------|
| `--data` / `--data-file` | — | 둘 중 하나가 필요하다. **둘 다 주면 `--data-file`이 우선한다** |
| `--sheet` | `Sheet1` | 대상 시트명 |
| `--mode {new,update}` | `new` | 아래 참조 |
| `--format` | off | 헤더 행 볼드 + 배경색(`D9E1F2`) + 가운데 정렬, 전 셀 얇은 테두리, 열 너비 자동(최대 60) |

**모드 동작**

- `update`이고 **파일이 실재할 때만** 기존 워크북을 연다. 대상 시트가 없으면 새로 만든다.
- `new`이거나 파일이 없으면 새 워크북을 만들어 `<file>`에 저장한다 — **기존 파일은 통째로 덮어써진다.**

**데이터 형식**

- `list[dict]`: 첫 항목의 키 순서를 헤더로 쓴다. 헤더 행은 `mode != "update"`이거나 `ws.max_row == 1`일 때 기록한다.
- `list[list]`: 행 그대로 append.
- 그 외(빈 배열, dict, 스칼라 등)는 거부한다.

**성공 응답**:
```json
{"ok": true, "command": "write", "file": "output.xlsx", "sheet": "Sheet1", "mode": "new", "rows_written": 1}
```

## 사용 예시

```bash
# 파일 구조 파악
~/.opal/tools/xlsx-tool/run.sh info project.xlsx

# 특정 시트 읽기 (헤더 기준 dict 목록)
~/.opal/tools/xlsx-tool/run.sh read data.xlsx --sheet "2026"

# 3행을 헤더로 삼아 읽기
~/.opal/tools/xlsx-tool/run.sh read data.xlsx --sheet 0 --header-row 3

# 범위 읽기 (헤더 해석 없이 2차원 배열)
~/.opal/tools/xlsx-tool/run.sh read data.xlsx --sheet "요약" --range A1:D20

# 키워드로 셀 찾기
~/.opal/tools/xlsx-tool/run.sh search wbs.xlsx --keyword "백엔드"

# JSON 데이터로 새 파일 생성 (서식 포함)
~/.opal/tools/xlsx-tool/run.sh write output.xlsx \
  --data '[{"이름":"홍길동","부서":"개발"}]' --format

# 큰 데이터는 파일로 전달
~/.opal/tools/xlsx-tool/run.sh write report.xlsx --data-file ./rows.json --format

# 기존 파일의 특정 시트에 이어쓰기
~/.opal/tools/xlsx-tool/run.sh write report.xlsx \
  --mode update --sheet "요약" \
  --data '[{"항목":"완료","수":"12"}]'
```

## 오류 코드

**선언 목록 없음.** 이 도구는 오류 코드 카탈로그를 정의하지 않는다. `error` 값은 안정 식별자가 아니라 **사람이 읽는 한국어 문장**(대부분)이거나 예외 원문 문자열이다. 호출자는 `error` 문자열로 분기하지 말고 `ok`만 판정에 쓴다.

실제로 방출되는 실패 계열은 다음과 같다(문면은 고정 계약이 아니다).

| 상황 | 메시지 계열 | 발생 명령 |
|------|-----------|----------|
| 파일 부재 | `파일을 찾을 수 없습니다: <경로>` | 전 명령 |
| 확장자 미지원 | `지원하지 않는 파일 형식입니다: <suffix>` | 전 명령 |
| 워크북 로드 실패 | openpyxl 예외 원문 | 전 명령 |
| 시트 인덱스 초과 | `시트 인덱스 범위 초과: <n> (전체 <N>개)` | read/search/write(update) |
| 시트 이름 부재 | `시트를 찾을 수 없습니다: '<name>' (전체: [...])` | read/search |
| 범위 형식 오류 | `범위 형식 오류: <값> (예: A1:Z100)` | read/search |
| 데이터 인자 누락 | `--data 또는 --data-file 중 하나가 필요합니다` | write |
| JSON 파싱 실패 | `--data JSON 파싱 실패: ...` / `data-file 로드 실패: ...` | write |
| 데이터 형식 위반 | `데이터가 비어 있습니다` / `data는 list(dict) 또는 list(list) 형식이어야 합니다` | write |
| 저장 실패 | `파일 저장 실패: <원문>` | write |
| 그 외 예외 | 예외 원문(`main`의 포괄 핸들러가 JSON으로 감싼다) | 전 명령 |

## 종료 코드

| 코드 | 의미 |
|------|------|
| `0` | 성공 |
| `1` | 위 실패 전건, 서브명령 미지정(이때 usage를 출력하고 1), `run.sh`의 venv 부재 선검사 |
| `2` | argparse 인자 오류(알 수 없는 서브명령, `search --keyword` 누락, 위치 인자 `file` 누락 등) |

exit 2 경로와 서브명령 미지정 경로는 JSON이 아닌 usage 텍스트를 출력한다.

## 제약

- `write`의 `--mode new`는 **경고 없이 기존 파일을 덮어쓴다.** 기존 내용을 지키려면 `--mode update`를 명시한다.
- `--sheet`의 숫자 해석은 `str.isdigit()` 기준이므로, **이름이 숫자로만 된 시트(예: `"2026"`)는 인덱스로 오해석된다.** 그런 시트는 인덱스로 지정하거나 이름을 바꿔야 한다.
- `read`의 `--range` 모드는 `--header-row`를 무시한다(두 옵션은 배타적으로 동작한다).
- `search`는 정규식을 지원하지 않는다 — 부분 문자열 일치뿐이다.
- `write`는 셀 서식·수식·차트를 보존하지 않는다. `--mode update`라도 대상 시트에 행을 append할 뿐이며, `--format`을 주면 시트 전체 셀에 테두리와 열 너비를 다시 적용한다.
- 배포 환경의 `~/.opal/.venv`에는 `pandas`도 설치되지만(`opal/tools/requirements.txt`), **이 도구의 소스는 pandas를 import하지 않는다.**
