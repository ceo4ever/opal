---
template: sdlc-v2
---
# PLAN: stockctl 다중 위치 재고·이동·감사·가져오기·충돌 감지

> 입력: [TASK.md](TASK.md)

## Approach
저장소 계층(`stockctl/store.py`)을 다중 위치 + 최상위 `version` 형식으로 바꾸고, 읽을 때 레거시 품목을 정규화해 다음 성공 저장에서 새 형식으로 기록되게 한다. 감사 로그는 새 모듈 `stockctl/audit.py`가 append/조회를 소유한다. CLI(`stockctl/cli.py`)는 기존 add/remove/list를 위치 인식으로 바꾸고 transfer·history·import-csv·version 명령과 변경 명령 공통 `--expect-version`을 추가한다. 모든 실패 경로는 쓰기 전에 판정해 저장소·감사 로그를 건드리지 않는다. 공개 동작은 구현 전에 테스트 에이전트가 `tests/test_multiloc.py`로 RED 고정하고, 구현 워커가 GREEN으로 만든다. `docs/CLI.md`는 아래 계약으로 갱신한다.

근거: 현행 단일 위치 구조 `stockctl/store.py:1-9`·`stockctl/cli.py:16-45`, 원자 저장 `stockctl/store.py:24-28`, 기존 회귀 `tests/test_basic.py:19-29`, 컨벤션 `docs/CONVENTIONS.md`.

## Findings

### 직접 변경
- `stockctl/store.py`: 단일 위치 `{name, qty, location}` 구조(`stockctl/store.py:5`, `stockctl/cli.py:18`)를 `{name, locations}` + `version`으로 교체하고 레거시 정규화·version 증가를 추가한다. 원자 저장(`stockctl/store.py:24-28`)은 유지한다.
- `stockctl/audit.py`: 신규. 감사 로그 append·SKU별 조회.
- `stockctl/cli.py`: add/remove/list 위치 인식화(`stockctl/cli.py:16-45`), transfer·history·import-csv·version 추가, `--expect-version` 공통 처리.
- `tests/test_multiloc.py`: 신규. 요구서 계약 전체의 공개 CLI 동작 테스트(RED 선작성).

### 회귀 확인
- `tests/test_basic.py`: 수정 없이 통과해야 한다. add 기본 위치 MAIN·list 4열 형식(`tests/test_basic.py:19-22`), remove 부족 exit 2(`tests/test_basic.py:25-29`)가 새 계약과 일치한다.
- `stockctl/__main__.py`: `main()` 반환값을 종료 코드로 쓰는 진입점(`stockctl/__main__.py:13`) 변경 없음 — 새 종료 코드 3·4·5도 같은 경로로 전달된다.

### 문서 갱신
- `docs/CLI.md`: 명령 표·종료 코드·출력 형식·저장소/감사/거부 파일 형식을 새 계약으로 교체한다.

### 미확인 가정
없음.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| D-1 저장 형식 | 파일 최상위 `{"version": int, "items": {SKU: {"name": str, "locations": {LOC: int}}}}`. `json.dumps(..., ensure_ascii=False, indent=2, sort_keys=True)`로 기록(현행 직렬화 옵션 유지). 저장소 파일이 없으면 `{"version": 0, "items": {}}`로 읽는다 | 요구서 §데이터, 현행 `stockctl/store.py:24-28` |
| D-2 레거시 정규화 | 읽을 때 품목에 `locations` 키가 없으면 `{"name": item.get("name", SKU), "locations": {item.get("location", "MAIN"): item.get("qty", 0)}}`로 바꾼다. `version` 키가 없으면 0. 파일 자체는 읽기에서 고치지 않고 다음 성공 저장에서만 새 형식이 기록된다 | 요구서 §데이터 2항 |
| D-3 version 증가와 원자 저장 | 저장 함수는 메모리의 `version`을 정확히 1 올린 뒤 `<path>.tmp`에 기록하고 `os.replace`로 교체한다. 실패 판정은 모두 저장 호출 전에 끝내므로 실패 명령은 저장소 파일과 감사 로그를 바이트 단위로 바꾸지 않는다 | 요구서 §데이터 3항, C-4 |
| D-4 실패 판정 순서 | 한 명령에 여러 실패 조건이 겹치면 ① 입력 무효(exit 5) → ② version 충돌(exit 4) → ③ 미등록 SKU(exit 1) → ④ 수량 부족(exit 2) 순으로 첫 조건 하나만 보고한다. 입력 무효는 저장소 없이 판정 가능한 인자·파일 형식 오류다 | 요구서가 조합 우선순위를 정하지 않음. 저장소 독립 검사 → 상태 의존 검사 순으로 결정론화(구현 세부, 외부 계약 추가 없음) |
| D-5 add | `add SKU --qty N [--name NAME] [--location LOC] [--expect-version V]`. LOC 기본 `MAIN`. 신규 SKU 이름은 NAME 또는 SKU. NAME이 주어지면 기존 이름을 덮어쓴다. `locations[LOC] += N`. stdout `SKU qty=Q`(Q = 변경 후 LOC의 수량), exit 0. qty 값 검증은 현행처럼 추가하지 않는다. 감사 `op=add`, `changes={LOC: +N}` | 요구서 명령 1 "기존 출력·종료 코드 유지", 현행 `stockctl/cli.py:16-24`. 기존 단일 위치에서 품목 수량 = 그 위치 수량이므로 Q를 위치 수량으로 두면 기존 의미가 보존된다 |
| D-6 remove | `remove SKU --qty N [--location LOC] [--expect-version V]`. 미등록 SKU: stderr `unknown sku: SKU`, exit 1. LOC 수량(없으면 0) < N: stderr `insufficient: SKU has Q at LOC`, exit 2. 성공: `locations[LOC] -= N`(0이 되어도 키 유지), stdout `SKU qty=Q`(변경 후 LOC 수량), exit 0. 감사 `op=remove`, `changes={LOC: -N}` | 요구서 명령 2, 현행 `stockctl/cli.py:27-39` 메시지 형식 유지 |
| D-7 list | SKU 오름차순, 각 SKU 안에서 LOC 오름차순, 수량이 0인 위치는 제외하고 `SKU\tNAME\tLOC\tQTY` 한 줄씩 출력, exit 0 | 요구서 명령 3 |
| D-8 transfer | `transfer SKU --from A --to B --qty N [--expect-version V]`. N ≤ 0: stderr `invalid: qty must be positive`, A == B: stderr `invalid: from and to must be different`, 둘 다 exit 5. 미등록 SKU exit 1(`unknown sku: SKU`). A 수량 < N: stderr `insufficient: SKU has Q at A`, exit 2. 성공: A -= N, B += N(B 없으면 생성), 한 번 저장, stdout `SKU A->B N`, exit 0. 감사 `op=transfer`, `changes={A: -N, B: +N}` | 요구서 명령 4 |
| D-9 감사 로그 | 경로 `str(저장소 경로) + ".audit.jsonl"`. 성공 저장 직후 SKU당 한 줄 `{"changes": {...}, "op": ..., "sku": ..., "ts": ...}`를 `json.dumps(ensure_ascii=False, sort_keys=True)`로 append(UTF-8). `ts`는 `datetime.now(timezone.utc).isoformat(timespec="seconds")`. 실패 명령은 append하지 않는다 | 요구서 명령 5 |
| D-10 import 감사 단위 | import-csv는 반영된 행을 SKU별로 합산해 SKU당 한 줄을 남긴다(`op=import`, 같은 SKU·LOC 행은 증감 합산). SKU 순서는 CSV 첫 등장 순 | 요구서 명령 5 "SKU별로 … JSON 한 줄" |
| D-11 history | `history SKU`: 감사 파일에서 `sku`가 일치하는 줄을 파일 역순(최신순 = append 역순)으로 `TS\tOP\tLOC:DELTA,...` 출력. changes는 LOC 오름차순, DELTA는 `f"{d:+d}"`. 파일이 없거나 기록이 없으면 출력 없이 exit 0 | 요구서 명령 6. 같은 초의 ts 동률을 append 순서로 해소 |
| D-12 import-csv 입력 무효 | FILE을 열 수 없거나(UTF-8, `newline=""`) 첫 행이 정확히 `sku,name,location,qty`가 아니면 stderr `invalid: ...` 한 줄, exit 5, 어떤 파일도 쓰지 않는다 | 요구서가 헤더를 고정함. 기존 무효 종료 코드 5를 재사용하고 새 코드를 만들지 않음 |
| D-13 import-csv 행 판정 | 데이터 행은 `csv.reader`로 읽는다. 셀이 하나도 없는 빈 줄은 건너뛴다(집계 제외). 셀 수 ≠ 4면 사유 `column count`. 각 셀을 strip한 값 중 빈 값이 있으면 사유 `empty field: <열이름>`(첫 빈 열). qty가 `[0-9]+`가 아니거나 0이면 사유 `invalid qty`. 유효 행은 strip한 값으로 add와 같은 의미(이름 덮어쓰기, `locations[loc] += qty`)로 메모리에 반영 | 요구서 명령 7 |
| D-14 import-csv 반영·출력 | 유효 행 N ≥ 1이면 한 번 저장(version +1) 후 감사 append. N = 0이면 저장·감사 없음(version 불변). 거부 M ≥ 1이면 `str(FILE) + ".rejected.csv"`에 헤더 `sku,name,location,qty,reason`과 거부 행(원래 셀 4개 — 부족하면 빈 값, 초과분 버림 — + 사유)을 `csv.writer`로 쓰고 exit 3. M = 0이면 그 파일을 만들지 않고 exit 0. 두 경우 모두 stdout `applied N, rejected M` | 요구서 명령 7 "한 번의 저장" — 반영할 행이 없으면 저장할 변경이 없음 |
| D-15 충돌 감지 | add·remove·transfer·import-csv는 `--expect-version V`(int)를 받는다. 지정되었고 현재 version ≠ V면 stderr `conflict: expected V, found X`, exit 4, 저장·감사·거부 파일 없음. 미지정이면 검사하지 않는다 | 요구서 명령 8 |
| D-16 version 명령 | `version`은 현재 version 정수 한 줄을 stdout에 출력, exit 0(파일 없으면 0, 레거시 파일이면 0) | 요구서 명령 8 |
| D-17 모듈 경계 | `store.py` exports `store_path`, `load`, `save`(+ 정규화는 `load` 내부). `audit.py` exports `audit_path`, `append`, `read`. 명령 로직·CSV 처리는 `cli.py`. 각 파일 상단 @header를 새 역할로 갱신 | `docs/CONVENTIONS.md` @header 규칙. 단일 사용처 추상화를 만들지 않음 |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. 공개 동작 RED 테스트 | opal-test-agent | `tests/test_multiloc.py` | TEST-SCENARIO의 `구현 전 RED` 시나리오를 pytest로 작성한다. `python -m stockctl --store <tmp>/s.json ...` subprocess로만 검증하고(내부 함수 import 금지), 레거시 fixture는 JSON 파일을 직접 써서 만든다. @header 포함. 구현 전 실행 실패를 관찰해 RED 증거로 기록 | 없음 | P1 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, AC-9 |
| W-2. CLI 계약 문서 갱신 | opal-be-agent | `docs/CLI.md` | D-1~D-16 계약으로 명령 표(7개 명령·옵션·출력·종료 코드 0/1/2/3/4/5), 실패 판정 순서, 저장소·감사(jsonl)·거부(csv) 파일 형식, 저장소 경로 우선순위(기존 문장 유지)를 기술 | 없음 | P1 | C-3 |
| W-3. 저장소·감사·CLI 구현 | opal-be-agent | `stockctl/store.py`, `stockctl/audit.py`, `stockctl/cli.py` | D-1~D-17을 그대로 구현한다. 표준 라이브러리만 사용(json, os, csv, re, datetime, pathlib, argparse, sys). 모든 실패 판정을 저장 전에 수행. W-1 테스트와 `tests/test_basic.py`를 수정하지 않고 통과시킨다 | W-1 | P2 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, AC-9, C-1, C-2, C-4 |

## Risks
추가 검증이 필요한 위험 없음.

## Release and recovery
- 적용 순서: P1(W-1 RED 작성·잠금, W-2 문서) → P2(W-3 구현) → TEST 전체 실행.
- 검증 범위: `python -m pytest tests/` 전체(기존 `tests/test_basic.py` 포함)와 TEST-SCENARIO 시나리오. 설치·배포 없음 — worktree 브랜치에서 테스트 통과가 검증 종료 지점이다.
- 실패 시: worktree 브랜치 `feat/OP-TASK-001`에만 변경이 있으므로 허브 `main`은 영향 없음. 사용자 데이터 파일은 레거시 형식을 읽기만 하다가 성공 저장 때만 교체되며, 교체는 원자적이다.
