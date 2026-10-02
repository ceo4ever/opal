---
template: sdlc-v2
---
# PLAN: stockctl 다중 위치 재고·이동·감사·가져오기·충돌 감지

> 입력: [TASK.md](TASK.md)

## 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | CLI 계약 | `docs/CLI.md` | 현재 명령·종료 코드·출력 형식(갱신 대상) |
| D-2 | 설계 | 컨벤션 | `docs/CONVENTIONS.md` | @header, 원자 저장, stderr 한 줄, pytest·`python -m stockctl` 규칙 |
| D-3 | 소스 | cli.py | `stockctl/cli.py` | add/remove/list 현행 구현과 parser |
| D-4 | 소스 | store.py | `stockctl/store.py` | load/save/store_path 현행 저장 구조 |
| D-5 | 소스 | test_basic.py | `tests/test_basic.py` | 회귀 기준(수정 금지) |
| D-6 | 외부 | Python argparse | [argparse — Parser for command-line options](https://docs.python.org/3/library/argparse.html) | 음수 인자 값 해석 규칙 |

## Approach

저장 계층(`stockctl/store.py`)이 신·구 형식 정규화, version 증가를 포함한 원자 저장, 감사 로그 append/read를 소유하고, CLI 계층(`stockctl/cli.py`)이 명령별 검증 순서·출력·종료 코드를 소유한다. 모든 변경 명령은 "load → 검증(실패 시 저장·감사 0건) → 메모리 변경 → save 1회 → 감사 append → stdout" 순서를 따른다. 실패 경로는 save와 감사 append 이전에 반환하므로 저장소·감사 파일은 바이트 단위로 불변이다(→ D-4:26-30 기존 원자 저장 재사용). RED-first를 적용해(비즈니스 로직·CLI 계약) 구현자와 다른 주체(`opal-test-agent` red mode)가 공개 CLI 동작을 검증하는 실패 테스트를 먼저 작성한다.

## Findings

### 직접 변경
- `stockctl/store.py`: `load`가 `{"items": {}}`만 반환하고 구형 `{name, qty, location}`을 그대로 돌려준다(D-4:19-23). 정규화·version·감사 함수를 추가한다.
- `stockctl/cli.py`: `cmd_add`/`cmd_remove`/`cmd_list`가 `item["qty"]`·`item["location"]` 단일 위치 필드를 직접 쓴다(D-3:16-47). parser에 `--location`(remove), `--expect-version`, transfer/history/import-csv/version 서브커맨드가 없다(D-3:50-66).
- `tests/test_multiloc.py`: 신규 계약을 검증하는 테스트 파일(현재 없음).

### 회귀 확인
- `tests/test_basic.py`: add+list(`A1\tApple\tMAIN\t5`)·remove 수량 부족 exit 2를 검증한다(D-5:21-30). 수정 없이 통과해야 한다(C-2).
- `stockctl/__main__.py`: `sys.exit(main())` 진입점. 변경하지 않으며 `python -m stockctl` 호출이 유지되는지만 확인한다.

### 문서 갱신
- `docs/CLI.md`: 명령 표가 add/remove/list 3종·단일 위치 출력 `SKU\tNAME\tLOCATION\tQTY`만 기술한다(D-1). 새 계약 전체로 갱신한다(C-4).

### 미확인 가정
- H-1 (argparse가 `--qty -3` 같은 음수 값을 옵션이 아닌 값으로 받아 exit 5 경로에 도달하는지).

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| 저장 형식 | `{"version": <int>, "items": {SKU: {"name": str, "locations": {LOC: int}}}}`. `save`는 기존처럼 `json.dumps(..., ensure_ascii=False, indent=2, sort_keys=True)`를 `<path>.tmp`에 쓰고 `os.replace`로 교체한다 | AC-1, C-3, D-4:26-30 |
| 구형 해석 | `store.load`: 파일 없음 → `{"version": 0, "items": {}}`. 파일 있음 → `version = data.get("version", 0)`; 각 품목이 `"locations"` 키를 가지면 그대로, 없으면 `{"name": item["name"], "locations": {item.get("location", "MAIN"): item["qty"]}}`로 변환(qty 0 위치도 보존). 변환은 메모리에서만 하며 파일은 다음 성공 save 때 새 형식으로 기록된다 | AC-1 "데이터가 사라지면 안 된다" |
| version 증가 위치 | `store.save(path, data)`가 쓰기 직전 `data["version"] = data.get("version", 0) + 1`을 수행하고 새 version을 반환한다. 성공 저장마다 정확히 +1 | AC-1, AC-8 |
| 명령당 저장 횟수 | 성공한 변경 명령은 save를 정확히 1회 호출한다. import-csv도 유효 행 전체를 반영한 뒤 1회. 유효 행 0건이면 save·감사를 하지 않는다(version 불변) | AC-7 "한 번의 저장", 변경 없는 저장으로 version이 오르는 것을 방지 |
| 감사 로그 | 경로 `Path(str(store_path) + ".audit.jsonl")`. 레코드 `{"ts": datetime.now(timezone.utc).isoformat(), "op": ..., "sku": ..., "changes": {LOC: int}}`를 `json.dumps(record, ensure_ascii=False, sort_keys=True)` + `"\n"`로 append(UTF-8). save 성공 직후에만 append. 한 명령에서 SKU당 1줄: add/remove는 `{LOC: +N}`/`{LOC: -N}`, transfer는 `{A: -N, B: +N}`, import는 같은 SKU의 반영 행을 LOC별 합산한 1줄 | AC-5 "SKU별로 … JSON 한 줄" |
| history 정렬 | 감사 파일 줄 순서(append 순)를 역순으로 출력해 최신순을 만든다(ts 문자열 비교 안 함 — 같은 시각 기록의 순서 보존). 출력 `f"{ts}\t{op}\t" + ",".join(f"{loc}:{delta:+d}" for loc in sorted(changes))`. 감사 파일이 없거나 해당 SKU 기록이 없으면 출력 없이 exit 0 | AC-6 |
| 변경 명령 공통 옵션 | add/remove/transfer/import-csv 서브파서에 `--expect-version`(type=int, default None). 값이 주어지고 load 후 현재 version과 다르면 stderr `conflict: expected {V}, found {X}`, exit 4, 저장·감사·rejected 파일 쓰기 없음 | AC-8 |
| 검증 순서(종료 코드 우선순위) | add: 충돌(4). remove: 충돌(4) → 미등록(1) → 수량 부족(2). transfer: 인자 무효(5, load 전) → 충돌(4) → 미등록(1) → 수량 부족(2). import-csv: 충돌(4) → 행 검증 | 인자 무효는 저장소 상태와 무관하므로 먼저 판정. 충돌은 저장소 상태 판정 중 가장 먼저 — 다른 사람이 바꾼 저장소에 대한 판정을 내리지 않음 |
| add | `--location` 기본 MAIN. 품목 없으면 `{"name": args.name or args.sku, "locations": {}}` 생성, `--name`이 있으면 이름 갱신, `locations[LOC] = locations.get(LOC, 0) + qty`. stdout `f"{sku} qty={locations[LOC]}"`(해당 위치 수량), exit 0 | AC-2 기존 형식 `SKU qty=N` 유지(D-3:23). 단일 위치(MAIN) 사용 시 기존과 동일 값 |
| remove | `--location` 기본 MAIN. 미등록 → stderr `unknown sku: {sku}` exit 1. `locations.get(LOC, 0) < qty` → stderr `insufficient: {sku} has {have} at {LOC}` exit 2. 성공 시 차감(0이 되어도 키 유지), stdout `f"{sku} qty={locations[LOC]}"` exit 0 | AC-2, D-3:30-38 |
| list | `for sku in sorted(items): for loc in sorted(locations): if qty != 0: print(f"{sku}\t{name}\t{loc}\t{qty}")` | AC-3 |
| transfer | `transfer SKU --from A --to B --qty N`(argparse dest `from_loc`, `to_loc`). `qty <= 0` → stderr `invalid: qty must be positive` exit 5; `A == B` → stderr `invalid: from and to must differ` exit 5. 미등록 exit 1(`unknown sku: {sku}`), `locations.get(A,0) < N` → `insufficient: {sku} has {have} at {A}` exit 2. 성공: A -= N(0이어도 키 유지), B += N, save, 감사 op `transfer`, stdout `f"{sku} {A}->{B} {N}"` exit 0 | AC-4 |
| import-csv 파싱 | `import-csv FILE`. 파일을 `open(FILE, newline="", encoding="utf-8")` + `csv.DictReader`로 읽는다. 열린 파일을 못 읽으면(존재하지 않음 등) 기존 CLI 인자 오류와 같은 처리로 `parser.error(...)`(stderr usage, exit 2)를 낸다. 행마다 `sku,name,location,qty` 4개 필드를 `(value or "").strip()`으로 읽어 하나라도 빈 값이면 reason `empty field: {field}`(헤더 순서상 첫 빈 필드), qty가 `str.isdigit()`이 아니거나 `int(qty) <= 0`이면 reason `invalid qty: {raw}`로 거부. 헤더가 다르면 해당 필드가 빈 값으로 읽혀 모든 행이 행 규칙으로 거부된다 | AC-7 행 거부 규칙. 파일 수준 오류는 새 종료 코드를 만들지 않고 기존 argparse 오류 경로 재사용 |
| import-csv 반영·출력 | 유효 행을 파일 순서대로 add 의미로 반영(이름 갱신 포함) → N>0이면 save 1회 + SKU별 감사(op `import`) → M>0이면 `FILE + ".rejected.csv"`에 `csv.DictWriter(fieldnames=reader.fieldnames + ["reason"], extrasaction="ignore")`로 헤더+거부 행(원래 값 그대로 + reason) 기록(덮어쓰기). stdout `applied {N}, rejected {M}`. 종료 코드 M>0 → 3, M=0 → 0이며 M=0이면 rejected 파일을 만들지 않는다 | AC-7 |
| version 명령 | `version` 서브커맨드: load 후 `print(data["version"])`, exit 0(파일 없음·구형 파일은 0) | AC-8 |
| 문서 | `docs/CLI.md`를 명령 표(명령·옵션·종료 코드·출력), 저장 형식·구형 호환, 감사 로그 형식, import-csv 규칙, 충돌 감지, 검증 순서로 갱신 | C-4 |
| @header | `store.py`·`cli.py`의 description·exports를 새 구조로 갱신, 신규 테스트 파일에 @header 추가 | D-2 "모든 소스 파일 상단에 @header" |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. RED 계약 테스트 작성 | opal-test-agent (red mode) | `tests/test_multiloc.py` | TEST-SCENARIO의 `구현 전 RED` 시나리오를 `tests/test_basic.py`와 같은 subprocess 방식(`python -m stockctl --store <tmp>`)의 pytest로 작성. @header 포함. 구현 전 실행해 실패 관찰 | 없음 | P1 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8 |
| W-2. 저장 계층·CLI 구현 | opal-be-agent | `stockctl/store.py`, `stockctl/cli.py` | 위 Decisions and contracts의 저장 형식·구형 해석·version·감사 함수(`audit_path`, `append_audit`, `read_audit`)와 명령 계약(add/remove/list/transfer/history/import-csv/version, `--expect-version`, 검증 순서)을 구현. 표준 라이브러리(`argparse`, `csv`, `datetime`, `json`, `os`, `pathlib`, `sys`)만 사용. @header 갱신 | W-1 | P2 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, C-1, C-2, C-3 |
| W-3. CLI 계약 문서 갱신 | opal-be-agent | `docs/CLI.md` | Decisions and contracts의 외부 계약(명령·옵션·종료 코드·출력·저장 형식·감사 로그·import-csv·충돌 감지·검증 순서)으로 문서 전체 갱신 | W-1 | P2 | C-4 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. argparse가 `--qty -3`의 `-3`을 옵션이 아닌 값으로 받는다(파서에 음수처럼 보이는 옵션이 없으면 값으로 해석 — D-6) | AC-4 qty ≤ 0 → exit 5 `invalid:` | 가정이 틀리면 argparse 오류(exit 2)로 끝나 AC-4 불충족 | W-2는 음수처럼 보이는 옵션 문자열을 추가하지 않는다. 음수·0 qty transfer 시나리오로 실제 exit 5를 검증 |

## Release and recovery
- 적용 순서: P1(W-1 RED 테스트, 실패 관찰·잠금) → P2(W-2 구현, W-3 문서 — 같은 워커 1배치) → TEST 단계 전체 pytest.
- 검증 범위: `python -m pytest tests/ -q` 전체(기존 `tests/test_basic.py` 회귀 포함)와 시나리오별 CLI 실측. 설치·배포 없음 — 검증은 worktree에서 pytest 통과로 종료한다.
- 실패 시: worktree 브랜치 `feat/OP-TASK-001`의 체크포인트 이전 상태로 되돌리는 보정 커밋을 추가한다(main 미반영 상태라 사용자 데이터 영향 없음). 구형 저장소 파일은 실패 명령에서 재기록되지 않으므로 복구 대상이 없다.
