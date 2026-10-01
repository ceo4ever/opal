---
template: sdlc-v2
---
# PLAN: stockctl 다중 위치 재고·이동·감사·가져오기·충돌 감지

> 입력: [TASK.md](TASK.md) (PM 경로 — ANALYSIS.md 없음, 분석 결과는 `## Findings`)

## 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | cli.py | `stockctl/cli.py` | 현재 add/remove/list 동작·출력·종료 코드·argparse 구성 |
| D-2 | 소스 | store.py | `stockctl/store.py` | 현재 저장 형식·경로 해석·원자 저장 |
| D-3 | 소스 | test_basic.py | `tests/test_basic.py` | 보존해야 할 기존 회귀 테스트 |
| D-4 | 설계 | CLI.md | `docs/CLI.md` | 갱신 대상 CLI 계약 |
| D-5 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 코드 컨벤션 |
| D-6 | 기획 | 요구서 | `../REQUEST.md`(허브 상위, 사용자 제공) | TASK 원천 — 데이터 절·명령 계약 1~8·제약 |

## Approach

저장소 계층(`stockctl/store.py`)이 새 형식(`{"version": int, "items": {sku: {"name", "locations": {LOC: qty}}}}`)의 읽기·레거시 정규화·버전 증가 원자 저장·감사 로그 추가/조회를 소유하고, 명령 계층(`stockctl/cli.py`)이 add/remove/list를 다중 위치로 바꾸고 transfer/history/import-csv/version과 `--expect-version` 충돌 검사를 추가한다. 실패 경로는 저장·감사 쓰기 호출 전에 반환하는 구조로 "실패 시 저장소 바이트 불변·감사 무기록"을 보장한다. 검증은 RED-first로 `opal-test-agent`가 `tests/test_multiloc.py`를 먼저 작성해 실패를 관찰한 뒤 구현한다. 마지막으로 `docs/CLI.md`를 새 계약으로 갱신한다.

현재 사실(E2):
- 저장 형식은 품목 `{name, qty, location}` 단일 위치이며 `version`이 없다 (→ D-2:19-23, D-1:16-24).
- 저장은 `<path>.tmp` 기록 후 `os.replace` (→ D-2:26-30). 이 방식을 유지한다.
- `remove`는 미등록 exit 1(`unknown sku:`), 부족 exit 2(`insufficient:`) (→ D-1:27-39).
- 저장소 경로는 `--store` > `STOCKCTL_STORE` > `stock.json` (→ D-2:15-16, D-4).
- 기존 테스트는 `add`/`list`의 `A1\tApple\tMAIN\t5` 출력과 `remove` 부족 exit 2만 검증한다 (→ D-3).

## Findings

### 직접 변경
- `stockctl/store.py` — 새 저장 형식, 레거시 정규화, `version` 증가 저장, 감사 로그 경로·추가·조회.
- `stockctl/cli.py` — add/remove/list 다중 위치화, transfer/history/import-csv/version 신설, `--expect-version`.
- `tests/test_multiloc.py` — 신규 RED 테스트(TEST-SCENARIO S-1~S-12 대응).

### 회귀 확인
- `tests/test_basic.py` — 수정 없이 통과해야 한다(C-2).
- `stockctl/__main__.py` — `main()` 반환값을 종료 코드로 쓰는 진입점(변경 없음, 새 종료 코드 3/4/5가 그대로 전달되는지 확인).

### 문서 갱신
- `docs/CLI.md` — 명령 표·저장 형식·감사 로그·부수 파일·종료 코드 갱신(C-3).

### 미확인 가정
없음.

## Decisions and contracts

### 저장소

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| 저장 형식 | 최상위 `{"version": <int>, "items": {SKU: {"name": <str>, "locations": {LOC: <int>}}}}`. 직렬화는 기존과 같이 `json.dumps(..., ensure_ascii=False, indent=2, sort_keys=True)` | AC-1, D-2:28 |
| 파일 부재 | `load`는 `{"version": 0, "items": {}}`를 반환 | 기존 부재 처리 유지(D-2:21-22) + version 0 |
| 레거시 정규화 | `load` 시 `locations` 키가 없는 품목은 `{"name": item.get("name", sku), "locations": {item["location"]: item["qty"]}}`로 바꾸고 `qty`·`location` 키는 버린다. 최상위 `version`이 없으면 0. 품목 단위로 판정하므로 혼합 파일도 처리. 정규화는 메모리에서만 일어나며 파일은 다음 성공 저장 때만 새 형식으로 기록 | AC-1 |
| 읽기 전용 명령 | `list`·`history`·`version`은 저장소 파일을 쓰지 않는다(레거시 파일도 그대로 둔다) | AC-1 "다음 성공 저장 때" |
| 버전 증가 | `store.save(path, data)`가 `data["version"]`을 1 올린 뒤 기록한다. 명령 계층은 version을 직접 바꾸지 않는다. 한 명령은 성공 시 `save`를 정확히 1회 호출 | AC-1 "모든 성공 저장은 version 1 증가", AC-7 "한 번의 저장" |
| 원자 저장 | 기존 `<path>.tmp` 기록 후 `os.replace` 유지 | AC-1, C-4, D-5:5 |
| 0 수량 위치 | remove/transfer로 0이 된 위치 키는 삭제하지 않고 0으로 남긴다. 품목도 삭제하지 않는다(재차 remove는 exit 2) | 단순성. list가 0을 숨기므로 외부 출력 영향 없음(AC-3) |

### 명령 공통

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| 검사 순서(변경 명령) | ① 인자·입력 파일 검증(exit 5) → ② `load` → ③ `--expect-version` 검사(exit 4) → ④ 도메인 검사(미등록 exit 1, 부족 exit 2) → ⑤ `save` 1회 → ⑥ 감사 로그 추가 → ⑦ stdout 출력. ①~④ 실패는 저장·감사·부수 파일 쓰기 전에 반환 | AC-4·AC-5·AC-8 "실패 시 저장/기록 없음" |
| `--expect-version` | add·remove·transfer·import-csv 각 서브파서의 옵션 `--expect-version V`(`type=int`, 기본 None). 지정 시 현재 version ≠ V면 stderr `conflict: expected V, found X` 한 줄, exit 4 | AC-8 |
| `version` | `stockctl [--store PATH] version` → 현재 version 정수 한 줄(`print(data["version"])`), exit 0. 파일 부재·레거시는 0 | AC-8 |
| 오류 출력 | 모든 오류는 stderr 한 줄 + 종료 코드 | C-4, D-5:6 |
| 종료 코드 표 | 0 성공 / 1 미등록 SKU / 2 수량 부족 / 3 import-csv 거부 행 존재 / 4 version 충돌 / 5 invalid 입력. argparse 사용법 오류(기존 exit 2)는 변경하지 않는다 | REQUEST 명령 계약 2·4·7·8 |

### 명령별

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| add | `add SKU --qty N [--name NAME] [--location LOC] [--expect-version V]`, LOC 기본 `MAIN`. 신규 SKU는 name=`NAME or SKU`, 기존 SKU는 `--name`이 있으면 이름 갱신. `locations[LOC] += N`(없으면 0에서 시작). stdout `SKU qty=<LOC의 변경 후 수량>`, exit 0. qty 값 검증은 기존처럼 하지 않는다 | AC-2 "기존 출력·종료 코드 유지"(D-1:16-24의 `SKU qty=N` 형식). 단일 위치 시절 qty는 그 위치 수량이었으므로 명령이 다룬 위치의 수량을 출력 |
| remove | `remove SKU --qty N [--location LOC] [--expect-version V]`, LOC 기본 `MAIN`. 미등록 SKU → stderr `unknown sku: SKU`, exit 1. `locations.get(LOC, 0) < N` → stderr `insufficient: SKU has <현재> at LOC`, exit 2. 성공 시 `locations[LOC] -= N`, stdout `SKU qty=<LOC의 변경 후 수량>`, exit 0 | AC-2, D-1:31·34 기존 문구 접두 유지 |
| list | `for sku in sorted(items)`, `for loc in sorted(locations)`, `qty == 0`이면 건너뛰고 `SKU\tNAME\tLOC\tQTY` 출력, exit 0 | AC-3 |
| transfer | `transfer SKU --from A --to B --qty N [--expect-version V]` (`--from`은 `dest="src"`, `--to`는 `dest="dst"`, 셋 다 required). ① `N <= 0` → stderr `invalid: qty must be positive`, exit 5; `A == B` → stderr `invalid: --from and --to must differ`, exit 5 (qty 검사가 먼저). ④ 미등록 → `unknown sku: SKU` exit 1; `locations.get(A, 0) < N` → `insufficient: SKU has <현재> at A` exit 2. 성공 시 `A -= N`, `B += N`(없으면 생성), stdout `SKU A->B N`, exit 0 | AC-4 |
| history | `history SKU` — 감사 로그 파일이 없거나 해당 SKU 기록이 없으면 출력 없이 exit 0. 기록은 파일 줄 순서의 역순(마지막에 추가된 줄이 먼저)으로 `TS\tOP\tLOC:DELTA,...` 출력. changes는 LOC 오름차순, DELTA는 `f"{d:+d}"`(예 `+5`, `-3`, `+0`), 항목 구분은 `,`. 빈 줄은 무시. 저장소는 읽지 않는다 | AC-6. ts 동률에도 결정론적인 "최신순"을 위해 추가 순서를 기준으로 함 |
| import-csv 읽기 | `import-csv FILE [--expect-version V]`. `open(FILE, newline="", encoding="utf-8-sig")` + `csv.DictReader`. ① 파일을 열 수 없으면 stderr `invalid: cannot read FILE` exit 5; 헤더에 `sku,name,location,qty` 네 열 중 하나라도 없으면 stderr `invalid: header must include sku,name,location,qty` exit 5 (추가 열·열 순서는 허용). ①은 load·version 검사보다 먼저 | AC-7 헤더 계약. 입력 검증 실패를 invalid 계열(exit 5)로 통일 |
| import-csv 행 판정 | 네 필드 값을 `strip()`한 뒤 헤더 순서(sku,name,location,qty)로 첫 빈 필드(누락 `None` 포함)가 있으면 거부, reason `empty field: <열이름>`. 그다음 qty가 정규식 `[0-9]+` 전체 일치가 아니거나 `int(qty) <= 0`이면 거부, reason `invalid qty`. 나머지는 유효 행 | AC-7 "qty가 양의 정수가 아니거나 필드가 비면 거부" |
| import-csv 반영 | 유효 행을 CSV 순서대로 add와 같은 의미로 메모리에 적용(신규 SKU name=행 name, 기존 SKU도 행 name으로 갱신 — add `--name` 지정과 동일, `locations[location] += qty`). 유효 행 N ≥ 1이면 `save` 1회, N = 0이면 저장하지 않음(version 불변) | AC-7 "한 번의 저장으로 모두 반영(add와 같은 의미)" |
| import-csv 출력·부수 파일 | stdout `applied N, rejected M`. M > 0이면 `FILE + ".rejected.csv"`(인자 문자열 뒤에 접미)를 덮어써서 헤더 = 원래 헤더 열 전체 + `reason`, 각 거부 행 = 원래(strip 전) 값 + reason을 `csv.writer`(`newline=""`, utf-8)로 쓰고 exit 3. M = 0이면 그 파일을 만들지도 지우지도 않고 exit 0 | AC-7 |

### 감사 로그

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| 경로 | `Path(str(store_path) + ".audit.jsonl")` | AC-5 `<저장소 경로>.audit.jsonl` |
| 레코드 | `{"ts": <ISO 8601>, "op": "add"|"remove"|"transfer"|"import", "sku": SKU, "changes": {LOC: <부호 있는 int>}}`를 `json.dumps(rec, ensure_ascii=False, sort_keys=True)` 한 줄로. ts는 `datetime.now(timezone.utc).isoformat(timespec="microseconds")` (예 `2026-10-01T14:48:00.123456+00:00`), 한 명령 안의 레코드는 같은 ts | AC-5 |
| 명령별 changes | add `{LOC: +N}`, remove `{LOC: -N}`, transfer `{A: -N, B: +N}`, import는 SKU별 1줄로 그 SKU 유효 행들의 `{location: qty 합계}`, 줄 순서는 CSV에서 SKU가 처음 나온 순서 | AC-5 "SKU별로 JSON 한 줄" |
| 쓰기 시점·방식 | `save` 성공 직후 `open(audit, "a", encoding="utf-8")`로 그 명령의 모든 줄을 한 번의 `write`로 추가. 실패 명령(①~④에서 반환)은 감사 파일을 열지 않는다 | AC-5 "실패한 명령은 아무것도 남기지 않는다" |

### 모듈 구조

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| store.py 공개 함수 | `store_path(explicit=None)`(유지), `load(path) -> dict`(정규화 포함), `save(path, data) -> None`(version +1 후 원자 기록), `audit_path(path) -> Path`, `append_audit(path, records: list[dict]) -> None`(ts가 없으면 채우지 않음 — 호출자가 ts 포함 레코드 전달), `read_audit(path) -> list[dict]`(파일 순서, 부재 시 `[]`). @header의 description·exports 갱신 | C-4 @header, D-5:4 |
| cli.py | 서브커맨드 `add`·`remove`·`list`·`transfer`·`history`·`import-csv`·`version`. 헬퍼 `_check_version(data, expected) -> int|None`(충돌 시 stderr 출력 후 4 반환)·`_now()`(ts). `main()`은 `args.func(args)` 반환값을 그대로 반환. @header description·exports 갱신 | 구현자 선택 제거 |
| 외부 의존 | 표준 라이브러리(`argparse`, `csv`, `json`, `os`, `re`, `sys`, `datetime`, `pathlib`)만 사용 | C-1 |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. RED 테스트 작성 | opal-test-agent (red mode) | `tests/test_multiloc.py` | TEST-SCENARIO S-1~S-12를 `python -m stockctl` subprocess 호출 pytest로 작성(함수명 `test_s<N>_...`, `tmp_path` 저장소 사용). 구현 전 실행해 실패를 관찰·기록 | 없음 | P1 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8 |
| W-2. 저장소·명령 구현 | opal-be-agent | `stockctl/store.py`, `stockctl/cli.py` | Decisions and contracts의 저장소·명령 공통·명령별·감사 로그·모듈 구조 표를 그대로 구현. `tests/test_multiloc.py`·`tests/test_basic.py`는 수정하지 않는다 | W-1 | P2 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, C-1, C-2, C-4 |
| W-3. CLI 계약 문서 갱신 | opal-be-agent | `docs/CLI.md` | 명령 표를 add/remove/list/transfer/history/import-csv/version(+`--expect-version`)으로 갱신하고, 저장 형식(`version`·`locations`, 레거시 자동 변환), 감사 로그 경로·레코드 필드, `FILE.rejected.csv`, 종료 코드 0~5 표, stderr 접두(`unknown sku:`/`insufficient:`/`conflict:`/`invalid:`)를 기재. 경로 우선순위 문장은 유지 | 없음 | P2 | C-3 |

W-2와 W-3은 같은 P2에서 선행 관계·파일 중첩이 없으므로 한 `opal-be-agent` 디스패치에 묶어 맡긴다.

## Risks

추가 검증이 필요한 위험 없음.

## Release and recovery

- 적용 순서: P1(W-1 RED 작성·실패 관찰 → `test-tool scenario-lock`) → P2(W-2·W-3) → TEST(전체 `python -m pytest tests -q`).
- 검증 범위: 결정론 CLI 통합 테스트(subprocess)와 Check(표준 라이브러리 전용·@header·`docs/CLI.md` 내용)로 끝난다. 설치·배포 단계는 없다.
- 실패 시: 변경은 워크트리 브랜치 `feat/OP-TASK-001`에만 있고 허브 `main`은 사용자 merge 전까지 불변이므로, 실패 Work item 파일만 되돌려 재작업한다. 운영 데이터 측면에서 새 형식으로 한 번 저장된 저장소는 구버전 stockctl이 읽지 못하므로, 코드 롤백 시 사용자는 사전 백업본을 쓰거나 `locations`의 단일 위치 항목을 `{qty, location}`으로 되돌려야 한다(이 태스크 범위의 자동 역변환 없음).
