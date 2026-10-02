---
template: sdlc-v2
---
# PLAN: stockctl 다중 위치 재고·이동·감사·가져오기·충돌 감지

> 입력: [TASK.md](TASK.md) | 작성자: PM(coordinator, PM 경로 — ANALYSIS.md 없음, 분석은 아래 Findings)

## 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | CLI 계약 | `docs/CLI.md` | 현행 명령·종료 코드·저장소 경로 규칙 |
| D-2 | 설계 | 컨벤션 | `docs/CONVENTIONS.md` | 표준 라이브러리·@header·원자 저장·stderr 한 줄·pytest |
| D-3 | 소스 | cli.py | `stockctl/cli.py` | 현행 add/remove/list·argparse 구조 |
| D-4 | 소스 | store.py | `stockctl/store.py` | 현행 load/save/store_path |
| D-5 | 소스 | test_basic.py | `tests/test_basic.py` | 회귀 기준 테스트 |
| D-6 | 설계 | PM 프로필 | `.opal/AGENT.md` | 금지사항(외부 패키지 금지) |

## Approach

저장 계층(`stockctl/store.py`)이 신·구 형식을 하나의 정규 형식 `{"version": int, "items": {sku: {"name", "locations"}}}`으로 읽고, 저장할 때마다 `version`을 올린다. 감사 로그는 새 모듈 `stockctl/audit.py`가 소유한다. 명령 계층(`stockctl/cli.py`)은 기존 argparse 구조(→ D-3:50-66)를 유지한 채 add/remove/list를 위치 단위로 바꾸고 transfer·history·import-csv·version과 공통 `--expect-version` 검사를 추가한다. 모든 실패 경로는 `store.save`와 감사 추가를 호출하기 전에 반환하므로 저장소·감사 파일이 변하지 않는다. 테스트는 RED-first로 구현 전에 `tests/test_multiloc.py`에 고정한다. 다중 프로세스 잠금, 감사 로그 순환은 범위 밖이다(TASK §Affected users and systems).

## Findings

### 직접 변경
- `stockctl/store.py` — 현재 품목을 `{name, qty, location}` 단일 위치로 다루고(→ D-4:6) 빈 저장소를 `{"items": {}}`로 돌려준다(→ D-4:21-22). `version`이 없다. 정규화·version 증가를 넣는다.
- `stockctl/cli.py` — add가 `item["qty"]`·`item["location"]`을 직접 쓰고(→ D-3:18-21), remove에 `--location`이 없으며(→ D-3:60-63), list가 품목당 한 줄이다(→ D-3:42-47). 위치 단위로 바꾸고 새 명령을 추가한다.
- `stockctl/audit.py` — 신규. 감사 로그 추가·조회.
- `tests/test_multiloc.py` — 신규. AC-1~AC-8 공개 동작 테스트(RED-first).

### 회귀 확인
- `tests/test_basic.py` — 수정하지 않는다(C-2). `add A1 --qty 5 --name Apple` 후 `list`에 `A1\tApple\tMAIN\t5`, 수량 부족 remove exit 2를 그대로 통과해야 한다(→ D-5:19-28).
- `stockctl/__main__.py` — `main()` 반환값을 종료 코드로 쓰는 진입점(`stockctl/__main__.py:12-14`). 변경 없음, `main` 시그니처 유지로 회귀 없음을 확인한다.

### 문서 갱신
- `docs/CLI.md` — 명령 표(→ D-1)를 새 계약(add/remove/list/transfer/history/import-csv/version, `--expect-version`, 종료 코드 0~5, 저장 형식·감사 파일)으로 교체한다(C-4).

### 미확인 가정
- H-1 참조.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| 정규 저장 형식 | 파일 최상위 `{"items": {SKU: {"name": str, "locations": {LOC: int}}}, "version": int}`. 직렬화는 기존과 같이 `json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)` | AC-1, 기존 직렬화 유지(→ D-4:29) |
| 구형 이관 | `store.load`: 파일 없음 → `{"version": 0, "items": {}}`. 파일 있음 → `version = raw.get("version", 0)`. 품목에 `"locations"` 키가 있으면 `{"name": item["name"], "locations": {loc: int(q) ...}}`, 없으면(구형) `{"name": item["name"], "locations": {item["location"]: item["qty"]}}`. qty 0 품목도 그대로 이관. 정규화된 dict만 반환하고 load는 파일을 쓰지 않는다 | AC-1 무손실·version 0 해석. 구형은 cli가 항상 세 키를 기록(→ D-3:18) — H-1 |
| version 증가 위치 | `store.save(path, data)`가 `data["version"] += 1` 후 기존 방식(같은 디렉토리 `<파일>.tmp` 기록 → `os.replace`)으로 저장하고 새 version을 반환한다. cli는 version을 직접 올리지 않는다 | "모든 성공 저장 +1"(AC-1)을 한 곳에서 보장, 원자 저장 유지(C-3, → D-2) |
| 감사 모듈 | `stockctl/audit.py`: `audit_path(store_path) -> Path` = `Path(str(store_path) + ".audit.jsonl")`; `record(op, sku, changes) -> dict` = `{"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "op": op, "sku": sku, "changes": changes}`; `append(store_path, records)` = 파일을 `"a"`·utf-8로 열어 각 record를 `json.dumps(r, ensure_ascii=False)` + `"\n"`으로 기록(records가 비면 파일을 열지 않음); `read(store_path, sku) -> list[dict]` = 파일이 없으면 `[]`, 있으면 빈 줄 제외 각 줄을 파싱해 `sku`가 같은 것만 파일 순서대로 반환 | AC-5·AC-6. 결정 기록: ts UTC 초 단위 |
| 저장·감사 순서 | 변경 명령은 성공 시 `store.save` 다음에 `audit.append`를 호출한다. 실패 경로는 둘 다 호출하지 않는다 | 실패 명령 무기록(AC-5), 실패 시 저장소 바이트 불변(AC-4) |
| 실패 판정 순서 | 입력 검증(exit 5, stderr `invalid: ...`) → `store.load` → 버전 충돌(exit 4) → 미등록 SKU(exit 1) → 수량 부족(exit 2). 오류는 stderr 한 줄 | 결정 기록(detail). 컨벤션 stderr 한 줄(→ D-2) |
| `--expect-version` | add·remove·transfer·import-csv 서브파서에 `--expect-version`(`type=int`, `dest="expect_version"`, 기본 None). 값이 있고 `data["version"] != V`면 stderr `conflict: expected V, found X` (X=현재 version), exit 4, 저장·감사·거부 파일 없음 | AC-8 |
| add | `add SKU --qty N [--name NAME] [--location LOC=MAIN] [--expect-version V]`. 품목 없으면 `{"name": NAME or SKU, "locations": {}}` 생성, NAME이 주어지면 이름 갱신(→ D-3:18-20과 동일 의미). `locations[LOC] = locations.get(LOC, 0) + N`. 저장·감사(op `add`, changes `{LOC: N}`). stdout `SKU qty=<LOC의 변경 후 수량>`, exit 0. `--qty` 값 검증은 기존처럼 하지 않는다 | AC-2. 결정 기록: N=LOC 수량 |
| remove | `remove SKU --qty N [--location LOC=MAIN] [--expect-version V]`. 미등록 SKU → stderr `unknown sku: SKU`, exit 1(기존 문구 → D-3:31). `have = locations.get(LOC, 0)`, `have < N` → stderr `insufficient: SKU has HAVE at LOC`, exit 2. 성공 시 `locations[LOC] = have - N`(0이어도 키 유지), 저장·감사(op `remove`, changes `{LOC: -N}`), stdout `SKU qty=<LOC의 변경 후 수량>`, exit 0 | AC-2. 결정 기록: 0 키 유지 |
| list | 품목 SKU 오름차순, 각 품목 안에서 LOC 오름차순으로 `qty != 0`인 위치마다 `SKU\tNAME\tLOC\tQTY` 출력, exit 0. 헤더 없음 | AC-3 |
| transfer | `transfer SKU --from A --to B --qty N [--expect-version V]`(argparse: `--from`(`dest="src"`)·`--to`(`dest="dst"`)·`--qty`(`type=int`) 모두 `required=True`). 입력 검증: `N <= 0` → `invalid: qty must be positive`, `A == B` → `invalid: source and destination must differ`, 둘 다 exit 5(qty 검사 먼저). 이후 충돌(4) → 미등록(1, `unknown sku: SKU`) → `have = locations.get(A, 0) < N` → `insufficient: SKU has HAVE at A`, exit 2. 성공: `locations[A] = have - N`, `locations[B] = locations.get(B, 0) + N`, 저장·감사(op `transfer`, changes `{A: -N, B: N}`), stdout `SKU A->B N`, exit 0 | AC-4 |
| history | `history SKU`: 저장소를 읽지 않는다. `audit.read(store, SKU)`를 역순으로 순회하며 `TS\tOP\tCHANGES` 출력. CHANGES = changes 키 오름차순 `f"{loc}:{delta:+d}"`를 `,`로 연결(`+5`, `-3`, `+0`). 기록·파일 없음 → 출력 없이 exit 0 | AC-6. 결정 기록: 최신순 = 추가 순서 역순 |
| import-csv 입력 | `import-csv FILE [--expect-version V]`. FILE을 `encoding="utf-8-sig"`, `newline=""`로 열어 `csv.reader`로 읽는다. 열기 실패(`OSError`) → `invalid: cannot read FILE`, exit 5. 첫 행(헤더)의 각 셀 `strip()` 결과가 정확히 `["sku","name","location","qty"]`가 아니면(빈 파일 포함) `invalid: header must be sku,name,location,qty`, exit 5. 이 두 검사는 `store.load` 전에 한다 | AC-7. 결정 기록 |
| import-csv 행 판정 | 헤더 뒤 각 행: 길이 0(빈 줄)은 건너뜀(집계 제외). 길이 ≠ 4 → reason `expected 4 fields, got K`. 셀을 `strip()`한 값 중 헤더 순서로 첫 빈 값 → reason `empty field: <열이름>`. qty가 ASCII 숫자만(`s.isascii() and s.isdigit()`)이 아니거나 `int(s) <= 0` → reason `qty must be a positive integer`. 나머지는 유효 행 | AC-7 "양의 정수가 아니거나 필드가 비면 거부" |
| import-csv 반영·출력 | 충돌 검사(4)는 행 판정 전에 한다. 유효 행을 파일 순서대로 add와 같은 의미(품목 없으면 생성, name 갱신, `locations[loc] += qty`)로 메모리에 반영하고, 유효 행 수 N ≥ 1이면 `store.save` 1회 후 행마다 감사 record(op `import`, changes `{loc: qty}`)를 한 번의 `audit.append`로 추가. N = 0이면 저장·감사 없음. 거부 행 수 M ≥ 1이면 `Path(str(FILE) + ".rejected.csv")`를 `"w"`·utf-8·`newline=""`로 열어 `csv.writer`로 원래 헤더 행 + `"reason"`, 이어서 각 거부 행의 원래 셀(공백 제거 전) + reason을 쓴다. stdout `applied N, rejected M`. M ≥ 1 → exit 3, M = 0 → exit 0이며 거부 파일을 만들지도 지우지도 않는다 | AC-7, AC-5. 결정 기록 |
| 서브파서 | 기존 `add`(`--qty` int required, `--name`, `--location` 기본 `MAIN`)·`list` 유지, `remove`에 `--location`(기본 `MAIN`) 추가, 신규 `transfer`, `history`(위치 인자 `sku`), `import-csv`(위치 인자 `file`), `version`(인자 없음). 각 서브파서는 `set_defaults(func=...)`로 연결(→ D-3:54-65 패턴) | AC-2~AC-8 |
| version | `version`: `store.load` 후 `print(data["version"])`, exit 0. 파일 없음·구형 파일 → `0` | AC-8 |
| 종료 코드 표 | 0 성공 / 1 미등록 SKU / 2 수량 부족 / 3 import 거부 행 있음 / 4 버전 충돌 / 5 입력 무효(transfer 인자, import 파일·헤더). argparse 자체 사용법 오류는 기존대로 argparse 기본(exit 2) | AC-2·4·7·8, D-1 갱신 대상 |
| 저장소 경로 | `--store` > `STOCKCTL_STORE` > `stock.json`(→ D-1, D-4:15-16) 변경 없음. `--store`는 기존처럼 서브커맨드 앞 전역 옵션 | 회귀 방지(C-2) |
| @header | `stockctl/audit.py`, `tests/test_multiloc.py`에 @header(module/layer/domain/description/exports)를 두고, `stockctl/store.py`·`stockctl/cli.py`의 @header description·exports를 새 구조로 갱신 | C-3, [MUST] `docs/CONVENTIONS.md`: "모든 소스 파일 상단에 @header(module/layer/domain/description/exports)를 둔다." |

[MUST] `docs/CONVENTIONS.md`: "Python 3 표준 라이브러리만 사용한다." — `json`, `csv`, `os`, `sys`, `argparse`, `pathlib`, `datetime`만 사용한다.
[MUST] `docs/CONVENTIONS.md`: "저장은 임시 파일 기록 후 `os.replace`로 원자 교체한다."
[MUST] `docs/CONVENTIONS.md`: "테스트는 `tests/`에 pytest로 작성하고 CLI는 `python -m stockctl`로 호출한다."

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. RED 테스트 작성 | opal-test-agent | `tests/test_multiloc.py` | TEST-SCENARIO의 `구현 전 RED` 시나리오를 `tests/test_basic.py`와 같은 `subprocess.run([sys.executable, "-m", "stockctl", "--store", ...])` 방식(→ D-5:14-16)과 pytest `tmp_path`로 공개 동작(stdout·stderr·exit·파일 내용)만 검증하는 테스트로 작성하고 실행해 실패 증거를 기록한다. 구현 코드는 만들지 않는다 | 없음 | P1 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, C-3 |
| W-2. CLI 계약 문서 갱신 | opal-task-agent | `docs/CLI.md` | 명령 표를 이 PLAN `Decisions and contracts`의 명령·옵션·stdout/stderr 형식·종료 코드 0~5로 교체하고, 저장 형식(`items[sku] = {"name", "locations"}`, 최상위 `version`, 구형 이관 규칙), 감사 파일(`<저장소 경로>.audit.jsonl` 필드), import 거부 파일 규칙, 저장소 경로 규칙(기존 문장 유지)을 절로 추가한다 | 없음 | P1 | C-4 |
| W-3. 저장·감사·명령 구현 | opal-be-agent | `stockctl/store.py`, `stockctl/audit.py`, `stockctl/cli.py` | `Decisions and contracts`의 정규 저장 형식·구형 이관·version 증가·감사 모듈·저장·감사 순서·실패 판정 순서·`--expect-version`·add·remove·list·transfer·history·import-csv·version·@header를 그대로 구현한다. `tests/test_multiloc.py`·`tests/test_basic.py`는 수정하지 않는다 | W-1 | P2 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, C-1, C-2, C-3 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. 구형 파일의 모든 품목은 `name`·`qty`·`location` 키를 가진다(현행 add가 세 키를 항상 기록, → D-3:18) | 구형 이관(AC-1) — 여러 품목·qty 0 품목·MAIN 외 위치가 섞인 실제 구형 파일에서 품목이나 수량이 사라지거나 읽기가 실패할 수 있음 | 기존 사용자 재고 데이터 손실 | W-3 구형 이관 규칙(qty 0·비 MAIN 위치 그대로 이관), 여러 품목이 섞인 구형 파일을 읽고 변경 후 전 품목 보존을 확인하는 시나리오 |

## Release and recovery
- 적용 순서: P1(W-1 RED 테스트, W-2 문서 — 파일이 겹치지 않아 병렬) → `test-tool scenario-lock` → P2(W-3 구현).
- 검증 범위: `python -m pytest tests/` 전체(신규 `tests/test_multiloc.py` + 기존 `tests/test_basic.py`)로 결정론 검증한다. 외부 연동·설치·배포는 없다.
- 실측 경계: 해당 없음(시간·품질 목표 없음).
- 실패 시: 배포가 없으므로 워크트리 브랜치 `feat/OP-TASK-001`에서 수정·재검증한다. 구형 파일은 load가 쓰지 않으므로 실패한 명령이 사용자 파일을 바꾸지 않는다.
