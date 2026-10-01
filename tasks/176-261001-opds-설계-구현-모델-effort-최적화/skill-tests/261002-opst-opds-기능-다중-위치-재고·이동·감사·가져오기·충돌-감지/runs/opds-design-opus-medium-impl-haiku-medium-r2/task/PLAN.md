---
template: sdlc-v2
---
# PLAN: stockctl 다중 위치 재고·이동·감사·가져오기·충돌 감지

> 입력: [TASK.md](TASK.md)

## Approach

저장소 계층(`stockctl/store.py`)을 다중 위치 + `version` 구조로 바꾸고 읽기 시 기존 단일 위치 형식을 정규화한다. 감사 로그 읽기·쓰기는 새 모듈 `stockctl/audit.py`가 소유한다. CLI(`stockctl/cli.py`)는 add/remove/list를 위치 단위로 바꾸고 transfer·history·import-csv·version 명령과 변경 명령 공통 `--expect-version` 옵션을 추가한다. RED-first를 적용해 `opal-test-agent`가 공개 CLI 동작을 검증하는 실패 테스트(`tests/test_multiloc.py`)를 먼저 쓰고, 구현 워커가 GREEN을 만든다. `docs/CLI.md`를 새 계약으로 갱신한다.

참조 문서:

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 기획 | 요구서 | `../REQUEST.md` | 데이터·명령 계약 1~8·제약 원문 |
| D-2 | 설계 | CLI 계약 | `docs/CLI.md` | 현행 명령·종료 코드·저장소 경로 규칙 |
| D-3 | 설계 | 컨벤션 | `docs/CONVENTIONS.md` | 표준 라이브러리·@header·원자 저장·stderr 한 줄·pytest |
| D-4 | 소스 | store.py | `stockctl/store.py` | 현행 load/save/store_path |
| D-5 | 소스 | cli.py | `stockctl/cli.py` | 현행 서브커맨드·출력·종료 코드 |
| D-6 | 소스 | test_basic.py | `tests/test_basic.py` | 회귀 기준 테스트 |

## Findings

### 직접 변경
- `stockctl/store.py`: 품목이 `{name, qty, location}` 단일 위치 구조이고(`stockctl/store.py:6`) 파일 부재 시 `{"items": {}}`만 반환하며 version 개념이 없다(`stockctl/store.py:19-23`). 저장은 `.tmp` 기록 후 `os.replace`(`stockctl/store.py:26-30`). → 정규화 로드·version 증가 저장으로 변경.
- `stockctl/cli.py`: add가 기존 품목의 위치를 무시하고 `qty`만 누적(`stockctl/cli.py:16-24`), remove에 `--location` 없음(`stockctl/cli.py:60-63`), list가 품목당 한 줄(`stockctl/cli.py:42-47`). → 위치 단위 동작과 신규 명령 추가.
- `stockctl/audit.py`: 신규 감사 로그 모듈.
- `tests/test_multiloc.py`: 신규 RED 테스트(작성자 `opal-test-agent`).

### 회귀 확인
- `tests/test_basic.py`: `add A1 --qty 5 --name Apple` 후 list에 `A1\tApple\tMAIN\t5`(`tests/test_basic.py:19-22`), MAIN 2개에서 3개 remove 시 exit 2(`tests/test_basic.py:25-28`). 수정 없이 통과해야 한다(C-3).
- `stockctl/__main__.py`: `sys.exit(main())` 진입점(`stockctl/__main__.py:12-14`)은 변경하지 않는다.

### 문서 갱신
- `docs/CLI.md`: 명령 표 전체를 새 계약(위치 옵션·transfer·history·import-csv·version·`--expect-version`·종료 코드 0~5·저장소/감사/거부 파일 형식)으로 갱신. 저장소 경로 결정 규칙 문장은 유지.

### 미확인 가정
없음.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| 저장 구조 | 파일 최상위 `{"items": {SKU: {"name": str, "locations": {LOC: int}}}, "version": int}`. JSON은 기존과 같이 `ensure_ascii=False, indent=2, sort_keys=True` | AC-1, 기존 직렬화 유지(→ D-4:29) |
| 로드 정규화 | `store.load(path)`: 파일 없으면 `{"items": {}, "version": 0}`. `version` 키 없으면 0. 품목에 `locations`가 없으면 `{"name": item.get("name", sku), "locations": {item.get("location") or "MAIN": item.get("qty", 0)}}`로 변환(수량 0도 키 유지). 로드만으로는 파일을 쓰지 않는다 | AC-1, C-2 "데이터가 사라지면 안 된다"(→ D-1 §데이터) |
| 저장 | `store.save(path, data)`: `data["version"] = data["version"] + 1` 후 `<path>.tmp`에 기록하고 `os.replace`로 교체. 성공 경로에서만 호출하며 명령당 최대 1회 | AC-1, C-2, [MUST] `docs/CONVENTIONS.md`: "저장은 임시 파일 기록 후 `os.replace`로 원자 교체한다." |
| 0 수량 위치 | 차감·이동으로 0이 된 위치 키는 삭제하지 않고 0으로 유지. 표시는 list가 걸러낸다 | design-decision(detail) 기록, AC-3, C-2 |
| 오류 판정 순서·출력 | 순서: 입력 자체 검증(exit 5) → 저장소 로드 → `--expect-version` 불일치(exit 4) → 미등록 SKU(exit 1) → 수량 부족(exit 2). 오류는 stderr 한 줄. 문구: `unknown sku: {SKU}`(기존 유지), `insufficient: {SKU} has {보유} at {LOC}`, `invalid: qty must be positive`, `invalid: --from and --to must differ`, `conflict: expected {V}, found {X}`. 실패 시 저장·감사·거부 파일을 쓰지 않는다 | design-decision(detail) 기록, AC-2·4·8, C-4, [MUST] `docs/CONVENTIONS.md`: "오류는 stderr에 한 줄로 쓰고 종료 코드로 구분한다." |
| 종료 코드 | 0 성공, 1 미등록 SKU, 2 수량 부족(argparse 사용법 오류도 기존대로 2), 3 import 거부 행 존재, 4 version 충돌, 5 invalid 입력 | AC-2·4·7·8(→ D-1 §명령 계약) |
| `--expect-version V` | add·remove·transfer·import-csv 서브커맨드 옵션(`type=int`, 기본 None). None이면 검사하지 않음. 비교 대상은 정규화 로드 후 version(기존 형식은 0) | AC-8 |
| add | `add SKU --qty N [--name NAME] [--location LOC=MAIN] [--expect-version V]`. 신규 SKU는 name 기본값 SKU. `--name`이 있으면 name 갱신. `locations[LOC] += N`(없으면 0에서 시작). stdout `SKU qty={LOC의 변경 후 수량}`, exit 0. 감사 `op=add`, `changes={LOC: +N}` | AC-2·5, design-decision(detail): N은 대상 LOC 수량 — 단일 위치 사용 시 기존 출력(→ D-5:23)과 동일 |
| remove | `remove SKU --qty N [--location LOC=MAIN] [--expect-version V]`. 미등록 exit 1, `locations.get(LOC, 0) < N`이면 exit 2. 성공 시 stdout `SKU qty={LOC 잔량}`, 감사 `op=remove`, `changes={LOC: -N}` | AC-2·5 |
| list | 모든 SKU 오름차순, 각 SKU 안에서 LOC 오름차순으로 수량이 0이 아닌 위치만 `SKU\tNAME\tLOC\tQTY` 출력 | AC-3 |
| transfer | `transfer SKU --from A --to B --qty N [--expect-version V]`(`--from`은 `dest="src"`). N ≤ 0이면 `invalid: qty must be positive`, A == B면 `invalid: --from and --to must differ`(둘 다 exit 5, qty 검사 먼저). 이후 순서대로 exit 4/1/2. 성공 시 A -= N, B += N, stdout `SKU A->B N`, 감사 `op=transfer`, `changes={A: -N, B: +N}` | AC-4·5 |
| 감사 로그 | `stockctl/audit.py`: `audit_path(store_path) = Path(str(store_path) + ".audit.jsonl")`. `append(store_path, entries)`는 각 entry를 `json.dumps(entry, ensure_ascii=False, sort_keys=True)` + `\n`으로 append. entry 필드 `ts`(`datetime.now(timezone.utc).isoformat(timespec="seconds")`), `op`, `sku`, `changes`({LOC: int}). 저장소 저장 성공 직후에만 호출 | AC-5, C-4 |
| history | `history SKU`: 감사 파일이 없거나 해당 SKU 기록이 없으면 출력 없이 exit 0. 파일 줄 순서를 역순으로(최신순) 해당 SKU만 `TS\tOP\tLOC:DELTA,...` 출력. changes는 LOC 오름차순, DELTA는 `f"{d:+d}"`(예 `+5`, `-3`). JSON 파싱 실패 줄은 건너뜀. 저장소 파일은 읽지 않는다 | AC-6 |
| import-csv 입력 | `import-csv FILE [--expect-version V]`. `utf-8-sig`·`newline=""`로 `csv.reader` 읽기. 파일을 읽을 수 없으면 `invalid: cannot read {FILE}` exit 5. 첫 행 각 셀 strip 결과가 정확히 `["sku","name","location","qty"]`가 아니면(빈 파일 포함) `invalid: header must be sku,name,location,qty` exit 5. 이후 빈 리스트 행(빈 줄)은 무시 | AC-7, 판정 순서 결정 |
| import-csv 행 판정 | 셀 수가 4가 아니면 거부 사유 `column count`. 그 외 각 셀 strip 후 열 순서(sku,name,location,qty)대로 첫 빈 셀이면 `empty field: {열이름}`. qty가 ASCII 숫자만(`re.fullmatch(r"[0-9]+", ...)`)이 아니거나 0이면 `invalid qty`. 유효 행 값은 strip한 값을 사용 | AC-7 |
| import-csv 반영 | 전체 행 판정 후 저장소 로드 → 충돌 검사(exit 4면 아무것도 쓰지 않음). 유효 행 N ≥ 1이면 각 행을 add와 같은 의미로 반영(신규 SKU 생성, name은 행 값으로 설정, `locations[loc] += qty`)하고 한 번 저장. N = 0이면 저장하지 않는다. 감사는 SKU마다 1줄 `op=import`, changes는 그 SKU 유효 행의 LOC별 합산, 같은 ts. stdout `applied N, rejected M` | AC-5·7, design-decision(detail) 2건 |
| import-csv 거부 파일 | M > 0이면 `FILE + ".rejected.csv"`에 헤더 `sku,name,location,qty,reason`과 거부 행(원본 셀을 strip 없이 4칸으로 맞춤 — 부족분 빈 문자열, 초과분 버림 — + 사유)을 `csv.writer`(utf-8, `newline=""`)로 덮어쓰고 exit 3. M = 0이면 그 파일을 만들거나 건드리지 않고 exit 0 | AC-7 |
| version | `version`: 정규화 로드 후 version 정수 한 줄 출력, exit 0(파일 없으면 0) | AC-8 |
| 헤더 주석 | 신규·변경 소스 파일 상단 @header의 description/exports를 새 책임에 맞게 갱신 | [MUST] `docs/CONVENTIONS.md`: "모든 소스 파일 상단에 @header(module/layer/domain/description/exports)를 둔다." |
| 의존성 | 표준 라이브러리(`argparse`, `csv`, `json`, `os`, `re`, `datetime`, `pathlib`, `sys`)만 사용 | C-1, [MUST] `.opal/AGENT.md` §금지사항: "외부 패키지 추가 금지(표준 라이브러리만)" |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. RED 테스트 작성 | opal-test-agent (red mode) | `tests/test_multiloc.py` | TEST-SCENARIO의 `구현 전 RED` 시나리오를 `subprocess`로 `python -m stockctl --store <tmp>/s.json ...`을 호출하는 pytest로 작성하고 현 코드에서 실패를 관찰·기록. `tests/test_basic.py`는 수정하지 않음 | 없음 | P1 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, C-2, C-4 |
| W-2. CLI 계약 문서 갱신 | opal-be-agent | `docs/CLI.md` | Decisions and contracts의 데이터 구조·명령 7종(add/remove/list/transfer/history/import-csv/version)·`--expect-version`·출력·stderr 접두어·종료 코드 0~5·감사/거부 파일 경로와 형식을 표와 짧은 절로 기술. 저장소 경로 규칙 문장 유지 | 없음 | P1 | AC-9 |
| W-3. 저장소·감사·CLI 구현 | opal-be-agent | `stockctl/store.py`, `stockctl/audit.py`, `stockctl/cli.py` | Decisions and contracts 표의 저장 구조·로드 정규화·저장·감사 로그·명령 계약·판정 순서·출력을 그대로 구현. `store.load/save/store_path` 이름 유지, `audit.audit_path/append/read_entries` 신설, cli 서브커맨드 transfer/history/import-csv/version 추가. W-1 테스트와 `tests/test_basic.py`를 GREEN으로 만든다(테스트 수정 금지) | W-1 | P2 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, C-1, C-2, C-3, C-4 |

## Risks
추가 검증이 필요한 위험 없음.

## Release and recovery
- 적용 순서: P1(W-1 RED 테스트 → `test-tool scenario-red`/`scenario-lock`, W-2 문서 병렬) → P2(W-3 구현) → TEST 단계 전체 회귀(`python -m pytest -q tests`).
- 검증 범위: CLI 공개 동작(stdout·stderr·exit code·저장소/감사/거부 파일 내용)을 subprocess로 결정론 검증. 외부 연동·설치·배포 없음.
- 실측 경계: 해당 없음.
- 실패 시: 설치·배포가 없으므로 worktree 브랜치 `feat/OP-TASK-001`의 변경을 되돌리면 복구된다. 사용자 저장소 파일은 기존 형식도 읽기 호환되므로 별도 마이그레이션 롤백 절차가 없다.
