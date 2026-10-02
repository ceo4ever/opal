---
template: sdlc-v2
---
# PLAN: stockctl 다중 위치 재고·이동·감사·가져오기·충돌 감지

> 입력: [TASK.md](TASK.md) (ANALYSIS 없음 — PM 경로, 분석 결과는 아래 Findings)

## Approach

기존 2계층 구조(저장소 `stockctl/store.py` ↔ 명령 `stockctl/cli.py`)를 유지한 채 확장한다(code-scan 결과: `[data] store.py`, `[api] cli.py`, `[api] __main__.py`, `[util] __init__.py`, `[test] test_basic.py` 5파일).

- 저장소 계층이 형식 정규화(구형→신형), version 증가 저장, 감사 로그 추가·조회를 소유한다. 명령 계층은 이 API만 호출한다.
- 모든 변경 명령은 같은 순서로 처리한다: ① 인자·입력 검증(exit 5) → ② 저장소 load → ③ `--expect-version` 충돌 검사(exit 4) → ④ 도메인 검사(exit 1·2) → ⑤ 메모리 상 변경 → ⑥ `store.save`(원자 교체, version+1) → ⑦ 감사 로그 append → ⑧ stdout 출력. ①~④에서 실패하면 ⑥·⑦에 도달하지 않으므로 저장소·감사 로그는 변하지 않는다(C-4).
- 구현 전에 공개 CLI 동작을 고정하는 테스트를 구현자와 다른 주체가 먼저 작성해 RED를 관찰한다(`harness/red-first.md` §1 — 비즈니스 로직·CLI 계약 변경은 RED 적용 대상).

## Findings

### 직접 변경
- `stockctl/store.py`: 현재 `load`는 파일 부재 시 `{"items": {}}`만 반환하고 형식 변환이 없으며(`stockctl/store.py:19-23`), `save`는 `.tmp` 기록 후 `os.replace` 하지만 version을 다루지 않는다(`stockctl/store.py:26-30`). 구형 정규화·version 증가·감사 로그 helper를 추가한다. @header의 description·exports를 새 계약으로 갱신한다.
- `stockctl/cli.py`: 현재 품목은 `{"name","qty","location"}` 단일 위치로 생성되고(`stockctl/cli.py:18`), `remove`에는 `--location`이 없으며(`stockctl/cli.py:60-63`), `list`는 `item['location']`·`item['qty']`를 한 줄 출력한다(`stockctl/cli.py:42-47`). add/remove/list를 위치 기반으로 바꾸고 transfer·history·import-csv·version 서브커맨드와 `--expect-version`을 추가한다. @header를 갱신한다.
- `tests/test_multiloc.py`: 신규. AC-1~AC-8, C-4 공개 동작 테스트(RED 선작성).

### 회귀 확인
- `tests/test_basic.py`: `add A1 --qty 5 --name Apple` 후 `list`에 `A1\tApple\tMAIN\t5` 포함(`tests/test_basic.py:19-22`), `remove`가 부족 시 exit 2(`tests/test_basic.py:25-28`). 수정하지 않고 통과해야 한다(C-2).
- `stockctl/__main__.py`: `sys.exit(main())` 진입점(`stockctl/__main__.py:12-14`). 변경하지 않으며 `main()`의 정수 반환 계약을 유지한다.

### 문서 갱신
- `docs/CLI.md`: 현재 add/remove/list 3행과 저장소 경로 규칙만 있다(`docs/CLI.md` §CLI 계약). 새 명령 계약 전체로 갱신한다(C-3).

### 미확인 가정
없음.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| D-1 저장 형식 | 최상위 `{"version": int, "items": {SKU: {"name": str, "locations": {LOC: int}}}}`. 직렬화는 기존과 같이 `json.dumps(..., ensure_ascii=False, indent=2, sort_keys=True)` | TASK AC-1. 기존 직렬화 옵션 유지(`stockctl/store.py:29`) |
| D-2 구형 해석 | `store.load`는 품목에 `locations` 키가 없으면 `{"name": item.get("name", sku), "locations": {item.get("location") or "MAIN": item.get("qty", 0)}}`로 변환하고, 최상위 `version`이 없으면 0으로 둔다. 수량 0인 구형 품목도 `{LOC: 0}`로 보존한다. 파일 부재 시 `{"version": 0, "items": {}}`. load는 파일을 쓰지 않는다 | AC-1 "데이터가 사라지면 안 된다", C-4(실패 시 무변경). 구형 생성 코드가 `location` 기본값 MAIN을 썼다(`stockctl/cli.py:18`, `stockctl/cli.py:58`) |
| D-3 version 증가 | `store.save(path, data)`가 기록 직전 `data["version"] = data.get("version", 0) + 1`을 수행하고 임시 파일(`<경로>.tmp`) 기록 후 `os.replace`로 교체한다. 성공 저장만 증가 | AC-1, C-1 `docs/CONVENTIONS.md` "저장은 임시 파일 기록 후 `os.replace`로 원자 교체한다" |
| D-4 0 수량 위치 | 차감·이동으로 0이 된 위치 키는 저장소에 `0`으로 남긴다(삭제하지 않음). `list`만 0을 숨긴다. 모든 위치가 0인 품목도 등록 상태를 유지한다(remove 시 exit 1이 아니라 exit 2) | 저장 구조 단순화와 무손실. AC-3은 출력만 규정 |
| D-5 add | 위치 `LOC`(기본 `MAIN`)에 `--qty`를 더한다. 신규 SKU는 `name = --name or SKU`. 기존 SKU에 `--name`이 주어지면 이름을 갱신한다. stdout `SKU qty=N`(N = 그 위치의 변경 후 수량), exit 0. qty 값 검증은 기존처럼 하지 않는다 | AC-2 "기존 출력·종료 코드 유지"(`stockctl/cli.py:16-24`). 구형 단일 위치 사용에서는 위치 수량 = 품목 수량이라 기존 출력과 동일 |
| D-6 remove | 미등록 SKU → stderr `unknown sku: SKU`, exit 1. 그 위치 수량(없으면 0) < qty → stderr `insufficient: SKU has H at LOC`, exit 2. 성공 시 차감, stdout `SKU qty=N`(그 위치 남은 수량), exit 0. qty 값 검증은 기존처럼 하지 않는다 | AC-2, 기존 메시지 형식 유지(`stockctl/cli.py:30-38`) |
| D-7 list | `sorted(items)` 순회, 각 품목의 `sorted(locations)` 중 qty ≠ 0인 것만 `f"{sku}\t{name}\t{loc}\t{qty}"` 출력. 정렬은 Python 문자열 기본 정렬 | AC-3 |
| D-8 transfer | 인자: `SKU --from A --to B --qty N`(모두 필수, `--qty`는 int). 검사 순서: qty ≤ 0 → stderr `invalid: qty must be positive`, exit 5 / A == B → stderr `invalid: --from and --to must differ`, exit 5 → 충돌 검사 → 미등록 SKU → stderr `unknown sku: SKU`, exit 1 → A 수량 < N → stderr `insufficient: SKU has H at A`, exit 2. 성공 시 A −N, B +N(B가 없으면 생성), stdout `SKU A->B N`, exit 0 | AC-4, Approach의 공통 처리 순서 |
| D-9 감사 로그 경로·형식 | 경로 `Path(str(store_path) + ".audit.jsonl")`. 한 줄 = `json.dumps({"ts": ..., "op": ..., "sku": ..., "changes": {...}}, ensure_ascii=False, sort_keys=True)` + `\n`, append 모드(`"a"`, utf-8). `ts`는 `datetime.now(timezone.utc).isoformat()`(UTC, 오프셋 포함 ISO 8601). `changes` 값은 부호 있는 int(add `{LOC: +qty}`, remove `{LOC: -qty}`, transfer `{A: -N, B: +N}`) | AC-5 |
| D-10 감사 기록 시점 | `store.save` 성공 직후 같은 명령에서 append한다. 실패 명령·충돌·저장 없는 import(N=0)는 append하지 않는다 | AC-5 "실패한 명령은 아무것도 남기지 않는다", C-4 |
| D-11 import 감사 단위 | 반영된 유효 행을 SKU별로 묶어 SKU당 1줄(`op: "import"`), `changes`는 그 SKU의 위치별 증감 합계. 줄 순서는 SKU 오름차순, 모든 줄의 `ts`는 같은 값 | AC-5 "SKU별로 … JSON 한 줄" |
| D-12 history | 감사 로그 파일을 순서대로 읽어 `sku`가 일치하는 줄만 모아 **파일 역순**(나중에 추가된 줄이 먼저)으로 `f"{ts}\t{op}\t" + ",".join(f"{loc}:{delta:+d}" for loc in sorted(changes))` 출력, exit 0. 파일 부재·기록 없음 → 출력 없이 exit 0. 빈 줄은 건너뛴다 | AC-6. ts 동률 시에도 최신순이 결정되도록 파일 순서를 기준으로 함 |
| D-13 import-csv 입력 검증 | 파일을 `encoding="utf-8-sig", newline=""`로 `csv.reader`로 읽는다. 파일을 열 수 없으면 stderr `invalid: cannot read FILE`, exit 5. 첫 행(공백 제거 후)이 정확히 `["sku","name","location","qty"]`가 아니면 stderr `invalid: header must be sku,name,location,qty`, exit 5. 두 경우 모두 저장·감사·거부 파일 없음 | 요구서가 정하지 않은 입력 오류. 새 종료 코드를 만들지 않고 요구서의 입력 검증 실패 코드(5, `invalid:`)를 재사용 |
| D-14 import-csv 행 판정 | 헤더 뒤 각 행: 필드가 하나도 없는 빈 줄은 무시(집계 제외). 필드 수 ≠ 4 → reason `bad_columns`. 각 필드를 `strip()`한 값 중 빈 값이 있으면 → `empty_field`. qty(strip 후)가 ASCII 숫자만이 아니거나 `int(qty) <= 0` → `invalid_qty`. 판정 우선순위 `bad_columns` > `empty_field` > `invalid_qty`. 유효 행은 strip된 값을 add와 같은 의미로 반영(위치 수량 += qty, 이름은 그 행 name으로 설정, 같은 SKU가 여러 행이면 나중 행 이름이 남음) | AC-7 "qty가 양의 정수가 아니거나 필드가 비면 거부", "add와 같은 의미" |
| D-15 import-csv 처리·출력 | 순서: 입력 검증(D-13) → load → 충돌 검사(exit 4, 거부 파일도 쓰지 않음) → 행 판정 → N > 0이면 `store.save` 1회 + 감사(D-11), N = 0이면 저장·감사 없음 → M > 0이면 `Path(str(FILE) + ".rejected.csv")`에 `csv.writer`로 헤더 `sku,name,location,qty,reason`과 각 거부 행(원래 필드 그대로 + reason)을 덮어쓰기 → stdout `applied N, rejected M` → M > 0이면 exit 3, 아니면 exit 0. M = 0이면 거부 파일을 만들지 않는다(기존 파일이 있어도 건드리지 않음) | AC-7, AC-8 |
| D-16 충돌 감지 | add·remove·transfer·import-csv 서브파서에 `--expect-version V`(int, 선택)를 둔다. 주어졌고 load한 `version != V`이면 stderr `conflict: expected V, found X`, exit 4, 저장·감사·거부 파일 없음. 미지정이면 검사하지 않는다 | AC-8 |
| D-17 version 명령 | `version` 서브커맨드는 load한 version 정수를 한 줄 출력, exit 0(파일 부재·구형은 0). 저장소를 쓰지 않는다 | AC-8 |
| D-18 history·list·version 읽기 전용 | 읽기 명령은 저장소·감사 로그를 쓰지 않는다 | C-4, AC-1(구형 파일은 "다음 성공 저장" 때만 신형으로 기록) |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. 공개 동작 테스트 선작성(RED) | opal-test-agent | `tests/test_multiloc.py` | TEST-SCENARIO의 `구현 전 RED` 시나리오를 `tests/test_basic.py:14-16`과 같은 subprocess 방식(`python -m stockctl --store <tmp>/s.json ...`)으로 pytest 테스트로 작성한다. 파일 상단 @header 포함. 구형 형식 파일은 테스트에서 JSON을 직접 써서 준비한다. 현재 코드에서 실패(RED)를 관찰·기록한다 | 없음 | P1 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, C-4 |
| W-2. CLI 계약 문서 갱신 | opal-be-agent | `docs/CLI.md` | 명령 표를 add/remove/list/transfer/history/import-csv/version으로 갱신(각 인자·stdout·stderr 접두·종료 코드: D-5~D-17), 저장 형식(D-1·D-2·D-3), 감사 로그 경로·필드(D-9·D-11), import-csv 입력·거부 파일 형식(D-13~D-15), 공통 처리 순서와 실패 시 무변경 보장을 절로 추가. 저장소 경로 규칙 문장은 유지 | 없음 | P1 | C-3 |
| W-3. 저장소·CLI 구현(GREEN) | opal-be-agent | `stockctl/store.py`, `stockctl/cli.py` | `store.py`: D-1~D-3 `load`/`save`, `version_of(data)`, `audit_path(store_path)`, `append_audit(store_path, op, entries)`(entries = `[(sku, changes)]`, 한 ts 공유), `read_audit(store_path)` 추가. `cli.py`: D-5~D-18 서브커맨드·검사 순서·메시지 구현, 공통 충돌 검사 함수 1개로 4개 변경 명령에 적용. 두 파일 @header의 description·exports 갱신. W-1 테스트와 `tests/test_basic.py` 모두 통과 | W-1 | P2 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, C-1, C-2, C-4 |

## Risks

추가 검증이 필요한 위험 없음.

## Release and recovery

- 적용 순서: P1(W-1 RED 테스트, W-2 문서 — 서로 파일 비중첩·선행 없음 → 병렬) → RED 증거 기록·scenario-lock → P2(W-3 구현) → TEST 단계 전체 회귀.
- 검증 범위: `python -m pytest tests/` 전체(신규 + 기존 `tests/test_basic.py`) 결정론 실행과 CLI 실측. 외부 연동·설치·배포 없음 — 검증 종료 지점은 worktree에서의 전체 테스트 PASS다.
- 실패 시: worktree 브랜치(`feat/OP-TASK-001`)에서만 변경하므로 허브 `main`은 영향 없음. 실패 W는 담당 워커에게 fix 모드로 재지시한다.
