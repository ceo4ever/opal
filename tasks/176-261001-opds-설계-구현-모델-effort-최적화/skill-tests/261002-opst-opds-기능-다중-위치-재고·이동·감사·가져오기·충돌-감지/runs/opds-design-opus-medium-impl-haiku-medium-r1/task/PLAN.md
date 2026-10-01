---
template: sdlc-v2
---
# PLAN: stockctl 다중 위치 재고·이동·감사·가져오기·충돌 감지

> 입력: [TASK.md](TASK.md)

## 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | CLI 계약 | `docs/CLI.md` | 현행 명령·출력·종료 코드, 갱신 대상 |
| D-2 | 설계 | 컨벤션 | `docs/CONVENTIONS.md` | 표준 라이브러리·@header·원자 저장·stderr 한 줄·pytest 규칙 |
| D-3 | 소스 | 저장소 | `stockctl/store.py` | 현행 load/save와 원자 교체 |
| D-4 | 소스 | CLI | `stockctl/cli.py` | 현행 add/remove/list와 parser |
| D-5 | 소스 | 회귀 테스트 | `tests/test_basic.py` | 무수정 통과 대상 |
| D-6 | 기획 | 요구서 | `../REQUEST.md`(허브 상위) | 요구 원문 |

## Approach
저장소 계층(`stockctl/store.py`)에 새 데이터 형식·기존 형식 정규화·version 증가·감사 로그 읽기/쓰기를 두고, CLI 계층(`stockctl/cli.py`)이 그 위에서 명령 7종(add, remove, list, transfer, history, import-csv, version)과 `--expect-version` 충돌 감지를 구현한다. 공개 동작은 RED-first로 먼저 테스트(`tests/test_multiloc.py`)에 고정하고, `docs/CLI.md`를 새 계약으로 교체한다. 동시성 제어는 요구서 범위대로 version 비교(낙관적 검사)만 하고 파일 잠금은 두지 않는다(TASK §Affected users and systems 제외 범위).

## Findings

### 직접 변경
- `stockctl/store.py`: 현행은 품목을 `{name, qty, location}` 단일 위치로 보고(`stockctl/store.py:3-8`), 파일이 없으면 `{"items": {}}`를 반환하며(`stockctl/store.py:19-23`), version 없이 임시 파일+`os.replace`로 저장한다(`stockctl/store.py:26-30`). 새 형식 정규화·version 증가·감사 로그 함수가 여기에 들어간다.
- `stockctl/cli.py`: add는 품목 최상위 `qty`/`location`을 직접 갱신하고(`stockctl/cli.py:15-23`), remove는 `--location`이 없고 품목 전체 수량으로 부족을 판정하며(`stockctl/cli.py:26-38`), list는 품목당 1줄을 출력한다(`stockctl/cli.py:41-46`). parser에는 add/remove/list만 있다(`stockctl/cli.py:53-68`). 세 명령 모두 위치 단위로 바뀌고 transfer·history·import-csv·version과 `--expect-version`이 추가된다.
- `tests/test_multiloc.py`: 신규 공개 동작 테스트 파일(RED-first 대상).

### 회귀 확인
- `tests/test_basic.py`: add 후 list에 `A1\tApple\tMAIN\t5`가 있어야 하고(`tests/test_basic.py:19-22`), 수량 부족 remove가 exit 2여야 한다(`tests/test_basic.py:25-28`). 파일을 수정하지 않고 통과를 확인한다(C-2).
- `stockctl/__main__.py`: `python -m stockctl` 진입점(`stockctl/__main__.py:10-14`)은 변경하지 않으며 모든 테스트의 호출 경로로 동작만 확인한다.

### 문서 갱신
- `docs/CLI.md`: 현행 3개 명령 표(`docs/CLI.md` §CLI 계약)를 새 데이터 형식, 명령 7종, `--expect-version`, 출력 형식, 종료 코드(0~5), 감사 로그·거부 파일 경로 계약으로 교체한다.

### 미확인 가정
없음.

## Decisions and contracts

모든 결정은 요구서(D-6)·TASK AC를 구현자가 선택 없이 따를 수 있게 구체화한 것이다.

### 데이터·저장 (AC-1, C-3)

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| 저장 형식 | `{"version": <int>, "items": {SKU: {"name": <str>, "locations": {LOC: <int>}}}}`. 파일이 없으면 `load`는 `{"version": 0, "items": {}}`를 반환한다. | 요구서 §데이터 (→ D-6) |
| 기존 형식 정규화 | `load`는 품목에 `locations` 키가 없으면 `{"name": item["name"], "locations": {item.get("location", "MAIN"): item["qty"]}}`로 바꾸고, 최상위 `version`이 없으면 0으로 둔다. 품목 단위로 판정하므로 섞인 파일도 처리한다. 정규화는 메모리에서만 하고 파일은 다음 성공 저장 때 새 형식으로 기록된다. | 요구서 §데이터, 현행 품목 구조 (→ D-3:3-8, D-4:17) |
| version 증가 | `save(path, data)`가 기록 직전에 `data["version"] = data.get("version", 0) + 1`을 수행한다. 성공 저장 1회당 정확히 +1. | 요구서 §데이터 |
| 원자 저장 유지 | 현행대로 `<path>.tmp`에 `json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)`를 쓰고 `os.replace`로 교체한다. | [MUST] `docs/CONVENTIONS.md`: "저장은 임시 파일 기록 후 `os.replace`로 원자 교체한다." (→ D-2, D-3:26-30) |
| 수량 0 위치 | remove·transfer로 0이 된 위치는 저장소에 `{LOC: 0}`으로 남긴다(삭제하지 않음). 출력에서만 숨긴다. | 데이터 무손실 우선, list 계약은 출력만 규정 (→ D-6 §명령 계약 3) |
| 실패 시 무변경 | 실패 경로(종료 코드 ≠ 0이고 3이 아닌 경우)는 `save`·감사 기록·거부 파일 쓰기를 호출하지 않는다. 따라서 저장소·감사 로그 바이트가 그대로다. | C-4, AC-4 |

### 명령 공통 처리 순서 (AC-2, AC-4, AC-7, AC-8)

변경 명령(add, remove, transfer, import-csv)은 다음 순서로 판정하고, 앞 단계에서 실패하면 뒤 단계를 실행하지 않는다.

1. argparse 인자 검증(현행 argparse 동작 그대로).
2. 명령별 입력 검증 → 실패 시 exit 5, stderr `invalid: ...` (transfer의 qty ≤ 0·`--from == --to`, import-csv의 파일 부재·헤더 불일치).
3. 저장소 `load`.
4. `--expect-version V`가 주어졌고 현재 `version != V`이면 exit 4, stderr `conflict: expected V, found X`(X = 현재 version).
5. 도메인 검증 → 미등록 SKU exit 1(stderr `unknown sku: SKU`), 위치 수량 부족 exit 2(stderr `insufficient: SKU has Q at LOC`, Q = 해당 위치 현재 수량, 위치가 없으면 0).
6. 변경 적용 → `save` 1회 → 감사 기록 추가 → stdout 출력 → 종료 코드 반환.

stderr는 모두 한 줄이다([MUST] `docs/CONVENTIONS.md`: "오류는 stderr에 한 줄로 쓰고 종료 코드로 구분한다." → D-2).

### 명령별 계약

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| add | `add SKU --qty N [--name NAME] [--location LOC] [--expect-version V]`. LOC 기본 `MAIN`. 신규 SKU는 name = NAME 또는 SKU. 기존 SKU에 `--name`이 있으면 name 갱신. `locations[LOC] = locations.get(LOC, 0) + N`. stdout `SKU qty=Q`(Q = 갱신 후 해당 LOC 수량), exit 0. qty 값 범위 검증은 추가하지 않는다(현행 유지). | 요구서 §명령 계약 1 "기존 출력·종료 코드 유지", 현행 출력 형식 (→ D-4:15-23). Q를 위치 수량으로 정한 이유: 명령이 LOC 단위로 동작하며 단일 위치 파일에서는 현행 값과 같다. |
| remove | `remove SKU --qty N [--location LOC] [--expect-version V]`. LOC 기본 `MAIN`. 미등록 exit 1, `locations.get(LOC, 0) < N`이면 exit 2(`insufficient:`). 성공 시 차감, stdout `SKU qty=Q`(Q = 차감 후 해당 LOC 수량), exit 0. | 요구서 §명령 계약 2, 현행 메시지 (→ D-4:29-34) |
| list | SKU 오름차순, 각 SKU 안에서 LOC 오름차순으로 `SKU\tNAME\tLOC\tQTY` 한 줄씩. 수량이 0인 위치는 출력하지 않는다. 헤더 없음. exit 0. | 요구서 §명령 계약 3 |
| transfer | `transfer SKU --from A --to B --qty N [--expect-version V]`. N ≤ 0이면 stderr `invalid: qty must be positive`, A == B이면 stderr `invalid: --from and --to must differ`, 둘 다 exit 5(qty 검사 먼저). 미등록 exit 1, `locations.get(A, 0) < N`이면 exit 2(`insufficient: SKU has Q at A`). 성공 시 A -= N, B += N(B 없으면 생성), stdout `SKU A->B N`, exit 0. | 요구서 §명령 계약 4 |
| 감사 로그 | 경로 `Path(str(store_path) + ".audit.jsonl")`. 성공 저장 직후 레코드마다 `json.dumps({"ts", "op", "sku", "changes"}, ensure_ascii=False, sort_keys=True) + "\n"`을 append 모드(UTF-8)로 쓴다. `ts` = `datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")`. `changes` 값은 부호 있는 int: add `{LOC: +N}`, remove `{LOC: -N}`, transfer `{A: -N, B: +N}`. | 요구서 §명령 계약 5 |
| import 감사 단위 | import-csv는 반영된 SKU마다 레코드 1줄(`op: "import"`)을 SKU 오름차순으로 쓰고, `changes`는 그 SKU의 유효 행 qty를 LOC별로 합산한 값이다. 한 실행의 레코드는 같은 `ts`를 쓴다. | 요구서 §명령 계약 5 "SKU별로 JSON 한 줄" |
| history | `history SKU`. 저장소를 읽지 않고 감사 로그만 읽는다. 로그 파일이 없거나 해당 SKU 레코드가 없으면 출력 없이 exit 0. 레코드를 파일 줄 순서의 역순(최신 추가가 먼저)으로 `TS\tOP\tLOC:DELTA,...` 출력. changes는 LOC 오름차순, DELTA는 `f"{delta:+d}"`(예 `+5`, `-3`), 쉼표로 구분. | 요구서 §명령 계약 6. 최신순을 ts 비교 대신 줄 순서로 정한 이유: 초 단위 ts는 같은 초 안에서 동률이 생기지만 append 순서는 항상 시간순이다. |
| import-csv 입력 검증 | `import-csv FILE [--expect-version V]`. FILE이 없으면 stderr `invalid: cannot read FILE`, `csv.DictReader`(UTF-8, `newline=""`)의 fieldnames가 정확히 `["sku", "name", "location", "qty"]`가 아니면 stderr `invalid: header must be sku,name,location,qty`, 둘 다 exit 5이며 아무 파일도 쓰지 않는다. | 요구서 §명령 계약 7 헤더 규정, 공통 처리 순서 2단계 |
| import-csv 행 판정 | 행마다 헤더 순서로 4개 필드를 보고, 값이 없거나(`None`) 공백 제거 후 빈 문자열이면 reason `empty field: <필드명>`(첫 번째 빈 필드). 그다음 qty를 공백 제거 후 10진 숫자만으로 이뤄지고 int 값이 > 0인지 보고 아니면 reason `invalid qty`. 통과한 행은 공백 제거한 sku·name·location·qty로 add와 같은 의미(name 갱신, 해당 위치 수량 증가)로 파일 순서대로 메모리에 반영한다. | 요구서 §명령 계약 7 "qty가 양의 정수가 아니거나 필드가 비면 거부", "add와 같은 의미" |
| import-csv 저장·출력 | 유효 행이 1개 이상이면 `save` 1회 후 감사 기록, 0개면 저장하지 않는다(version 불변). stdout `applied N, rejected M`. M > 0이면 `Path(str(FILE) + ".rejected.csv")`에 `csv.writer`로 헤더 `sku,name,location,qty,reason`과 거부 행의 원래 값 4개 + reason을 덮어쓰고 exit 3. M = 0이면 거부 파일을 만들지도 지우지도 않고 exit 0. 충돌(exit 4)·입력 오류(exit 5)에서는 거부 파일도 쓰지 않는다. | 요구서 §명령 계약 7 |
| expect-version | add·remove·transfer·import-csv 서브파서에 `--expect-version`(type=int, 선택)을 둔다. 공통 처리 순서 4단계로 판정한다. | 요구서 §명령 계약 8 |
| version | `version`은 저장소를 load(정규화 포함)해 version 정수만 한 줄 출력, exit 0. 파일이 없으면 `0`, 기존 형식 파일은 `0`. | 요구서 §명령 계약 8, §데이터 |
| 저장소 경로 | 현행 그대로 `--store` > `STOCKCTL_STORE` > `stock.json`, 전역 옵션 `--store`는 서브커맨드 앞. | 현행 (→ D-3:15-16, D-4:54) |

### 모듈 인터페이스 (W-3 내부 계약)

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| store 공개 함수 | `store_path(explicit=None)`(현행), `load(path) -> dict`(정규화 포함), `save(path, data)`(version +1, 원자 교체), `audit_path(path) -> Path`, `append_audit(path, records: list[dict])`(records가 비면 아무것도 안 함), `read_audit(path) -> list[dict]`(파일 없으면 `[]`, 빈 줄 무시). | 저장 형식·감사 로그 책임을 한 모듈에 모아 CLI가 파일 형식을 몰라도 되게 한다 |
| @header 갱신 | `stockctl/store.py`·`stockctl/cli.py`의 @header `description`·`exports`를 새 구조와 함수 목록으로 갱신한다. 신규 테스트 파일에도 @header를 둔다. | [MUST] `docs/CONVENTIONS.md`: "모든 소스 파일 상단에 @header(module/layer/domain/description/exports)를 둔다." (→ D-2) |
| 의존성 | `json`, `os`, `csv`, `datetime`, `pathlib`, `argparse`, `sys`만 사용한다. | [MUST] `.opal/AGENT.md` §금지사항: "외부 패키지 추가 금지(표준 라이브러리만)" (C-1) |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. 공개 동작 RED 테스트 작성 | opal-test-agent (red mode) | `tests/test_multiloc.py` | TEST-SCENARIO.md의 `구현 전 RED` 시나리오를 pytest로 작성한다. 각 테스트는 `subprocess`로 `python -m stockctl --store <tmp>/s.json ...`을 호출하고 stdout·stderr·exit code·저장소/감사/거부 파일 내용과 바이트를 검증한다. 테스트 함수 이름에 S-ID를 포함한다(예 `test_s1_...`). 현재 구현에서 실패를 관찰한다. | 없음 | P1 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, C-4, C-5 |
| W-2. CLI 계약 문서 갱신 | opal-be-agent | `docs/CLI.md` | 위 §Decisions and contracts의 저장 형식, 명령 7종 문법·출력·종료 코드(0 성공, 1 미등록 SKU, 2 수량 부족, 3 import 거부 행 있음, 4 version 충돌, 5 입력 오류), `--expect-version`, 감사 로그·거부 파일 경로, 저장소 경로 우선순위를 표와 짧은 설명으로 기술한다. | 없음 | P1 | AC-9 |
| W-3. 저장소·CLI 구현 | opal-be-agent | `stockctl/store.py`, `stockctl/cli.py` | `store.py`: §데이터·저장과 §모듈 인터페이스대로 `load` 정규화, `save` version 증가, `audit_path`·`append_audit`·`read_audit` 추가. `cli.py`: §명령 공통 처리 순서와 §명령별 계약대로 add/remove/list 변경, transfer/history/import-csv/version 서브커맨드와 `--expect-version` 추가. 두 파일 @header 갱신. W-1 테스트와 `tests/test_basic.py`를 모두 GREEN으로 만든다(테스트 파일 수정 금지). | W-1 | P2 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, C-1, C-2, C-3, C-4, C-5 |

## Risks
추가 검증이 필요한 위험 없음.

## Release and recovery
- 적용 순서: P1(W-1 RED 테스트, W-2 문서 — 파일이 겹치지 않아 병렬) → RED 증거 기록·scenario-lock → P2(W-3 구현).
- 검증 범위: `python -m pytest -q tests/` 전체(신규 + `tests/test_basic.py` 회귀)와 TEST-SCENARIO의 결정론 검사(문서 내용·표준 라이브러리 import 검사). 외부 연동·설치·배포 없음.
- 실측 경계: 해당 없음(시간·품질 수치 목표 없음).
- 실패 시: 배포가 없으므로 worktree 브랜치 `feat/OP-TASK-001`에서 수정 커밋을 추가하거나 브랜치를 merge하지 않으면 허브 `main`은 영향이 없다. 기존 형식 저장소는 첫 성공 저장 때 새 형식으로 바뀌므로, 사용자 데이터 파일은 이 브랜치를 merge한 뒤에만 영향받는다.
