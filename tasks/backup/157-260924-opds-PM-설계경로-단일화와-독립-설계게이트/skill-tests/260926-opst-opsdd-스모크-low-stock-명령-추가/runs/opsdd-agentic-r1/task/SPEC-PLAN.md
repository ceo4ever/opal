# SPEC-PLAN: stockctl 재고 부족 품목 조회 (low-stock)

> 버전: 1.0 | 작성일: 2026-09-26 | SPEC.md v1.0 기준 (OQ-01/02 PM 확정본, NFR-03 삭제 반영)
> 입력: `tasks/001-low-stock/SPEC.md`, `tasks/001-low-stock/TEST-SCENARIOS.md`(TS-01~TS-17)
> REVIEW 메모: 구조 검증 S-1~S-6 Pass, 목표-커버 게이트 i1 pass. PM 확정 결정 OQ-01(`--below` 누락 = argparse exit 2), OQ-02(정수 판정 = Python `int()` 변환 성공 여부)를 설계 입력으로 사용한다.
> 참조 문서: `docs/PROJECT.md`, `docs/CONVENTIONS.md`, `docs/CLI.md`, `.opal/AGENT.md`. `docs/ARCHITECTURE.md`는 저장소에 없다. 아키텍처는 코드(`stockctl/cli.py`, `stockctl/store.py`, `stockctl/__main__.py`)를 직접 읽어 파악했다.

---

## 1. 아키텍처 설계

### 기존 구조 (실측)

- 진입점: `stockctl/__main__.py:12-14`이 `cli.main()`을 호출하고 반환값을 `sys.exit`에 넘긴다. 핸들러 반환값이 곧 종료 코드다.
- 명령 레이어: `stockctl/cli.py:50-66` `build_parser()`. 전역 `--store`(`:52`)와 `add_subparsers(dest="command", required=True)`(`:53`) 아래 `add`/`remove`/`list` 서브파서를 두고, 각 서브파서는 `set_defaults(func=cmd_*)`로 핸들러를 연결한다. `main()`(`:69-72`)은 파싱 후 `args.store = store.store_path(args.store)`로 경로를 확정하고 `args.func(args)`를 반환한다.
- 핸들러 패턴: `cmd_list`(`stockctl/cli.py:42-47`)는 `store.load` → `sorted(data["items"])` 순회 → `print(... "\t" ...)` → `return 0`. 오류는 `print(..., file=sys.stderr)` 한 줄 + 비0 반환(`cmd_remove`, `:27-39`).
- 데이터 레이어: `stockctl/store.py`. `store_path`(`:15-16`, `--store` > `STOCKCTL_STORE` > `stock.json`), `load`(`:19-23`, 파일이 없으면 `{"items": {}}`를 반환하고 파일을 만들지 않음), `save`(`:26-30`, `.tmp` 기록 후 `os.replace`). 쓰기는 `save`만 한다.
- 의존 방향: `__main__` → `cli` → `store` (단방향, 순환 없음).

### 컴포넌트 구성

| 컴포넌트 | 역할 | 신규/수정 | 레이어 |
|----------|------|----------|--------|
| `low-stock` 서브파서 (`build_parser()` 내부) | `low-stock` 명령과 필수 옵션 `--below`(문자열 그대로 수신)를 등록하고 `cmd_low_stock`에 연결 (FR-01) | 수정 (`stockctl/cli.py`) | api |
| `cmd_low_stock(args)` 핸들러 | N 검증 → 저장소 읽기 → qty < N 필터 → SKU 오름차순 `SKU\tQTY` 출력 → 종료 코드 반환 (FR-02~FR-06) | 신규 (`stockctl/cli.py` 내 함수) | api |
| `_parse_below(raw)` 검증 헬퍼 | `int(raw)` 변환 성공 + 1 이상이면 정수 반환, 아니면 `None` (FR-04, FR-05, A-3) | 신규 (`stockctl/cli.py` 내 모듈 비공개 함수) | api |
| `stockctl/cli.py` @header | description에 low-stock 반영 (C-4) | 수정 | api |
| `store.load` / `store.store_path` | 기존 읽기·경로 결정 재사용. 변경 없음 | 재사용 | data |
| `tests/test_low_stock.py` | TS-01~TS-06, TS-08~TS-17 자동 검증. @header 포함 | 신규 | test |
| `docs/CLI.md` 명령 표 | `low-stock` 행 추가 (FR-08) | 수정 | 문서 |

FR → 컴포넌트 매핑:

| FR | 컴포넌트 |
|----|---------|
| FR-01 | `low-stock` 서브파서, `main()`의 기존 `store_path` 경로 결정 재사용 |
| FR-02, FR-03 | `cmd_low_stock` (필터·정렬·출력) + `store.load` |
| FR-04, FR-05 | `_parse_below` + `cmd_low_stock` 오류 분기 |
| FR-06 | `cmd_low_stock`이 `store.load`만 호출하고 `store.save`를 호출하지 않음 |
| FR-07 | 기존 핸들러·서브파서 무수정, `tests/test_basic.py` 무수정 |
| FR-08 | `docs/CLI.md` |

### 의존관계

```
stockctl/__main__.py ──> cli.main()
                          ├─ build_parser() ── low-stock 서브파서 ──(set_defaults)──> cmd_low_stock
                          └─ store.store_path()          (기존, 무변경)
cmd_low_stock ──> _parse_below          (같은 모듈)
cmd_low_stock ──> store.load            (읽기 전용. store.save 호출 금지)
tests/test_low_stock.py ──(subprocess: python -m stockctl)──> stockctl
tests/test_low_stock.py ──(파일 읽기)──> docs/CLI.md   (TS-08)
```

새 의존은 기존 방향(`cli` → `store`) 안에서만 생긴다. `store` → `cli` 역의존이나 새 모듈은 없다.

### 변경 영향 범위

| 영향받는 컴포넌트 | 영향 내용 | 수준 (높음/중간/낮음) |
|------------------|----------|---------------------|
| `stockctl/cli.py` `build_parser()` | 서브파서 1개 추가. 기존 `add`/`remove`/`list` 서브파서 정의는 건드리지 않는다 | 중간 |
| `stockctl/cli.py` 핸들러 영역 | 함수 2개(`cmd_low_stock`, `_parse_below`) 추가. 기존 `cmd_add`/`cmd_remove`/`cmd_list`는 무변경 | 낮음 |
| `stockctl/cli.py` @header | description 문구 갱신 | 낮음 |
| `stockctl/store.py` | 변경 없음 (TASK "제외": 저장소 포맷 변경 금지, `TASK.md:16`) | 없음 |
| `tests/test_basic.py` | 변경 없음 (C-2) | 없음 |
| `tests/test_low_stock.py` | 신규 | 낮음 |
| `docs/CLI.md` | 표에 1행 추가. 기존 3행과 저장소 경로 문구는 유지 | 낮음 |

---

## 2. 데이터 모델

이 기능은 새 데이터를 만들지 않는다. 기존 저장소 스키마를 읽기만 한다.

### 엔티티

| 엔티티 | 속성 | 타입 | 제약 |
|--------|------|------|------|
| Store (JSON 루트) | `items` | object (sku → Item) | 파일이 없으면 `load`가 `{"items": {}}`를 반환 (`stockctl/store.py:19-23`) |
| Item | (키) `sku` | str | `items`의 키. 정렬은 파이썬 `sorted()` 코드 포인트 사전순 (EC-10) |
| Item | `name` | str | low-stock은 사용하지 않음 |
| Item | `qty` | int | 필터 대상. `qty < N` 엄격 비교 (FR-02, EC-01) |
| Item | `location` | str | low-stock은 사용하지 않음 |
| Threshold (런타임 값, 비저장) | `N` | int | `int(raw)` 변환 성공 + `N >= 1` (A-3, FR-05). 상한 없음 (EC-09, 파이썬 임의 정밀도 int) |

### 관계

| 관계 | 타입 | 설명 |
|------|------|------|
| Store → Item | 1:N | 기존 구조 그대로. low-stock은 전체 Item을 순회한다 |

### 스키마

기존과 같다 (`stockctl/store.py` @header: "sku → {name, qty, location} 단일 위치 구조"):

```json
{"items": {"<sku>": {"name": "<str>", "qty": <int>, "location": "<str>"}}}
```

### 인덱싱 전략

| 인덱스 | 대상 | 근거 |
|--------|------|------|
| 없음 | - | 저장소는 매 실행 시 JSON 전체를 메모리에 올린다(`store.load`). 조회는 전체 순회 O(n) + 정렬 O(n log n)이며 `cmd_list`와 같은 비용이다. 별도 인덱스 파일은 C-1(새 파일 금지)과 TASK "제외"(저장소 포맷 변경 금지)에 어긋난다. |

### 마이그레이션 (기존 데이터 시)

없음. 스키마·파일 포맷 변경이 없으므로 기존 저장소 파일을 그대로 사용한다.

---

## 3. API 설계

HTTP API가 없는 CLI이므로 "엔드포인트"는 CLI 명령으로 기술한다.

### 엔드포인트

| # | 메서드 | 경로 | 설명 | 인증 |
|---|--------|------|------|------|
| 1 | CLI | `stockctl [--store PATH] low-stock --below N` | qty < N 품목을 SKU 오름차순 `SKU\tQTY` 줄로 출력 | 없음 (로컬 파일 권한에 따름, 기존 명령과 동일) |

### 요청/응답 스키마

#### `low-stock`

- **요청**:
  - 전역 `--store PATH` (선택). 미지정 시 `STOCKCTL_STORE` → `stock.json` (기존 `store_path`, FR-01, AC-02).
  - `--below N` (필수, argparse `required=True`, **`type` 미지정 = 문자열 그대로 수신**). 공백 구분(`--below -3`)과 `=` 결합(`--below=-3`) 모두 값으로 받는다 (TD-2).
- **응답 (정상, exit 0)**:
  - stdout: `qty < N`인 품목마다 `f"{sku}\t{qty}\n"`. SKU는 `sorted(data["items"])` 순서. 헤더·장식·후행 공백 없음 (NFR-04). 인코딩은 기존 `print` 기본 동작 = `cmd_list`와 동일.
  - stderr: 빈 문자열.
  - 해당 품목이 없거나 저장소가 비었거나 파일이 없으면 stdout·stderr 모두 빈 문자열, exit 0 (FR-03, EC-04, EC-05).
- **에러**:

| 케이스 | 조건 | stdout | stderr | 종료 코드 | 근거 |
|--------|------|--------|--------|----------|------|
| 비정수 N | `int(raw)`가 `ValueError` (`abc`, `3.5`, `""`, `3.0`, `1e2`) | 빈 | `invalid: ...` 정확히 1줄 | 5 | FR-04, AC-04, EC-08 |
| 0 이하 N | `int(raw) <= 0` (`0`, `-3`) | 빈 | `invalid: ...` 정확히 1줄 | 5 | FR-05, AC-05, EC-07 |
| 잘못된 N + 저장소 부재/빈 상태 | 위 두 경우와 같음. 검증을 저장소 읽기보다 먼저 하므로 저장소 상태와 무관 | 빈 | `invalid: ...` 1줄 | 5 | EC-06, TD-4 |
| `--below` 누락 | argparse 필수 인자 오류 (핸들러 미진입) | 빈 | argparse usage + error (여러 줄) | 2 | EC-12, OQ-01 (기존 `--qty` 누락 관례) |

- **오류 메시지 형식 (고정)**: `invalid: --below must be a positive integer, got {raw!r}` — `print(..., file=sys.stderr)`로 1회 출력. `{raw!r}`(repr)는 개행·제어문자를 이스케이프하므로 입력값이 무엇이든 stderr가 정확히 1줄(`\n` 1개)로 보장된다 (NFR-02, TD-6). 테스트는 접두사 `invalid:`와 줄 수만 검사하므로 문구 뒷부분은 계약이 아니다.

### 내부 인터페이스

| 인터페이스 | 입력 | 출력 | 설명 |
|-----------|------|------|------|
| `_parse_below(raw: str) -> int \| None` | argparse가 받은 원문 문자열 | 1 이상 정수 또는 `None` | `try: n = int(raw) except ValueError: return None`; `return n if n >= 1 else None`. 부작용 없음 |
| `cmd_low_stock(args) -> int` | `args.below: str`, `args.store: Path` (`main()`에서 확정됨) | 종료 코드 0 또는 5 | ① `_parse_below(args.below)`가 `None`이면 stderr 1줄 후 `return 5` (저장소 미접근) ② `data = store.load(args.store)` ③ `for sku in sorted(data["items"])`: `qty = data["items"][sku]["qty"]`; `qty < n`이면 `print(f"{sku}\t{qty}")` ④ `return 0`. `store.save` 호출 금지 |
| `build_parser()` 추가분 | - | - | `ls = sub.add_parser("low-stock")`; `ls.add_argument("--below", required=True)`; `ls.set_defaults(func=cmd_low_stock)`. `add`/`remove`/`list` 등록 뒤에 추가한다 |
| `store.load(path)` / `store.store_path(explicit)` | 기존 | 기존 | 재사용만 한다. 시그니처·동작 변경 없음 |

---

## 4. 기술 결정

#### TD-1: `--below`를 문자열로 받고 핸들러에서 검증
- **결정**: `add_argument("--below", required=True)`로 `type`을 지정하지 않고, 정수 변환·범위 검증은 `cmd_low_stock`이 `_parse_below`로 수행한다.
- **근거**: argparse의 `type=int` 변환 실패는 `parser.error` → exit 2 + usage 여러 줄이 되어 FR-04(exit 5, `invalid:` 1줄)를 위반한다 (SPEC R-1, 기존 `--qty`가 이 경로, `stockctl/cli.py:56,62`). 핸들러에서 검증하면 exit 코드와 stderr 형식을 완전히 제어할 수 있고, 기존 명령의 파싱 경로는 전혀 건드리지 않는다.
- **대안**:
  - `type=` 사용자 함수 + `argparse.ArgumentTypeError` — 결국 `parser.error` 경로라 exit 2/usage. 포기.
  - `ArgumentParser.error` 오버라이드(서브클래스) — 전 명령의 파싱 오류 동작이 바뀌어 `add`/`remove`의 `--qty` 오류와 EC-12(`--below` 누락 exit 2)까지 영향. C-2 위반 위험. 포기.
  - `main()`에서 `SystemExit`를 잡아 코드 변환 — 누락(EC-12)과 값 오류를 구분할 수 없고 usage 출력은 이미 stderr에 쓰인 뒤라 NFR-02 위반. 포기.
- **영향**: `build_parser()` low-stock 서브파서, `cmd_low_stock`, `_parse_below`.

#### TD-2: 음수 값(`--below -3`)은 argparse 기본 동작으로 값으로 수신
- **결정**: 추가 처리 없이 argparse 기본 동작에 맡긴다. low-stock 서브파서에는 음수처럼 보이는 옵션(예: `-1`)을 정의하지 않는다는 설계 제약을 둔다.
- **근거**: argparse는 해당 파서에 음수처럼 보이는 옵션 문자열이 없으면 `-3`처럼 음수 형태인 인자를 옵션이 아닌 값으로 취급한다. 동일 구조 파서로 실측: `['low-stock','--below','-3']` → `below='-3'`, `['low-stock','--below=-3']` → `'-3'` (Python 3.14.3, 저장소 무수정 `python3 -c` 확인). 이후 `_parse_below`가 `-3 <= 0`으로 거부해 exit 5가 된다 (EC-07, TS-05).
- **대안**: argv 전처리로 `--below X`를 `--below=X`로 합치기 — `main()`에 명령 특화 로직이 들어가 기존 명령 파싱 경로에 끼어든다. `nargs=argparse.REMAINDER` — 뒤따르는 인자를 모두 흡수해 다른 동작을 바꾼다. 둘 다 불필요한 복잡도라 포기.
- **영향**: `build_parser()`. TS-05의 `["--below", "-3"]` 케이스가 이 결정의 회귀 방지 테스트다.
- **한계(범위 밖 기록)**: `--below -abc`처럼 음수 숫자 형태가 아닌 `-` 시작 값은 argparse가 옵션으로 보고 exit 2로 끝난다. SPEC(EC-07)은 음수 정수만 요구하고 TS에도 없는 입력이다. `--below=-abc`는 값으로 전달되어 exit 5다.

#### TD-3: 정수 판정 = `int(raw)` 변환 성공 (PM 확정 OQ-02 / A-3)
- **결정**: `_parse_below`는 `int(raw)`만 사용한다. 정규식이나 `str.isdigit` 같은 별도 규칙을 추가하지 않는다.
- **근거**: PM 확정 A-3. 실측(Python 3.14.3): `+3`→3, `03`→3, `' 3 '`→3, `1_000`→1000, `99999999999999999999`→그대로; `abc`/`3.5`/`''`/`3.0`/`1e2`/`' '`→`ValueError`. TS-04·TS-14·TS-16 기대값과 일치한다.
- **대안**: 정규식 `^[1-9][0-9]*$` — A-3/EC-11(`+3`, `03`, `1_000` 유효)을 위반한다. `float()` 후 정수 여부 확인 — `3.0`, `1e2`가 통과해 EC-08 위반. 포기.
- **영향**: `_parse_below`.
- **참고(결정의 귀결)**: `int()`는 유니코드 10진 숫자도 받는다(실측 `int('٣') == 3`). A-3에 따라 이런 입력도 유효로 처리하며, 이번 범위에서 추가 제한을 두지 않는다(SPEC에 없는 규칙을 만들지 않는다).

#### TD-4: N 검증을 저장소 읽기보다 먼저 수행
- **결정**: `cmd_low_stock`은 `_parse_below`를 가장 먼저 호출하고, 실패 시 `store.load`를 호출하지 않고 exit 5로 끝낸다.
- **근거**: EC-06(저장소 상태와 무관하게 exit 5)을 구조적으로 보장하고, 오류 경로에서 저장소 파일에 아예 접근하지 않으므로 FR-06도 자명해진다. 손상 JSON(A-2, 범위 밖)이 있어도 잘못된 N이 먼저 보고된다.
- **대안**: 읽은 뒤 검증 — 기능상 동작은 같을 수 있으나 저장소 상태가 오류 판정에 끼어들 여지가 생긴다. 포기.
- **영향**: `cmd_low_stock`.

#### TD-5: 읽기는 기존 `store.load`만 재사용, `store.py` 무변경
- **결정**: 새 저장소 함수를 만들지 않고 `store.load(args.store)`를 호출한다. `store.save`는 호출하지 않는다.
- **근거**: `store.load`는 파일이 없으면 `{"items": {}}`를 반환하고 파일을 만들지 않는다(`stockctl/store.py:19-23`). 파일 생성·`.tmp` 기록은 `store.save`(`:26-30`)에만 있으므로 `save`를 부르지 않으면 C-1/FR-06/NFR-01(바이트 불변, 새 파일 없음, mtime 불변)이 성립한다. `load`는 `read_text`만 하므로 동시 실행 중인 add/remove의 `os.replace`를 방해하지 않는다.
- **대안**: `store.py`에 `read_only_items()` 같은 헬퍼 추가 — 기능 차이가 없고 변경 범위만 늘린다. 포기.
- **영향**: `cmd_low_stock`, `stockctl/store.py`(무변경).

#### TD-6: 오류 출력은 `print(..., file=sys.stderr)` + `{raw!r}`
- **결정**: `print(f"invalid: --below must be a positive integer, got {raw!r}", file=sys.stderr)` 후 `return 5`.
- **근거**: 기존 오류 출력 패턴(`stockctl/cli.py:31,34`)과 같고, `docs/CONVENTIONS.md`의 "오류는 stderr에 한 줄로 쓰고 종료 코드로 구분한다"를 따른다. repr을 쓰면 원문에 개행이 있어도 한 줄이 보장된다.
- **대안**: 원문 그대로 `{raw}` — 개행 포함 입력 시 여러 줄이 되어 NFR-02를 깰 수 있다. `sys.exit(5)` 직접 호출 — 기존 핸들러는 반환값으로 종료 코드를 전달하므로(`__main__.py:14`) 패턴이 어긋난다. 포기.
- **영향**: `cmd_low_stock`.

#### TD-7: 출력 정렬·형식은 `cmd_list`와 같은 방식
- **결정**: `for sku in sorted(data["items"])` + `print(f"{sku}\t{qty}")`.
- **근거**: EC-10(파이썬 기본 문자열 순서, `list`와 동일)과 NFR-04(탭 1개, `\n` 종료, `list`와 같은 인코딩)를 `cmd_list`(`stockctl/cli.py:42-47`)와 같은 코드 형태로 만족한다.
- **대안**: 자연 정렬(`A2` < `A10`) — EC-10 위반. 포기.
- **영향**: `cmd_low_stock`.

#### TD-8: 테스트는 신규 파일 `tests/test_low_stock.py`에 작성
- **결정**: 새 테스트 파일에 `tests/test_basic.py:15-17`의 `run(tmp_path, *args)` 형태를 그대로 따른 로컬 헬퍼를 두고, 저장소 픽스처는 JSON을 직접 기록한다. TS-02는 `--store` 없이 `env`에 `STOCKCTL_STORE`를 주입하는 별도 호출을 쓴다. `test_basic.py`는 import하거나 수정하지 않는다.
- **근거**: C-2(기존 테스트 그대로 유지), `docs/CONVENTIONS.md`("테스트는 `tests/`에 pytest로 작성하고 CLI는 `python -m stockctl`로 호출한다"). 테스트 간 import 결합을 피한다.
- **대안**: `test_basic.py`에 추가 — 기존 파일을 수정하게 되어 C-2 판정이 흐려진다. 공용 `conftest.py` 신설 — 헬퍼 1개를 위해 파일을 늘리는 과잉 추상화. 포기.
- **영향**: `tests/test_low_stock.py`.

#### TD-9: ACT를 1개로 구성
- **결정**: `stockctl/cli.py`, `tests/test_low_stock.py`, `docs/CLI.md` 변경을 ACT-001 하나(담당 `opal-be-agent`)로 묶는다.
- **근거**: 변경은 서브파서 1개 + 함수 2개 + 테스트 파일 1개 + 문서 1행으로 한 워커가 한 세션에 끝낼 수 있다. 문서 행의 내용(출력 형식, 종료 코드 0/5)은 구현 계약과 같아야 하므로 같은 워커가 소유하는 편이 불일치 위험이 가장 작다. `docs/PROJECT.md` 프로젝트 구성에서 `stockctl/`, `tests/`의 전문 에이전트가 `opal-be-agent`이고, `docs/CLI.md`는 CLI 계약 문서라 같은 소유가 자연스럽다.
- **대안**: 코드 ACT와 문서 ACT 분리 — 문서 ACT가 너무 작고, TS-08 테스트 파일 소유가 둘로 갈리거나 테스트 파일을 하나 더 만들어야 한다. TS-07(전체 회귀)이 두 ACT가 모두 끝난 뒤에만 의미가 있어 병렬 이득도 없다. 포기.
- **영향**: 8. ACT 분해.

---

## 5. 보안 고려사항

### 인증/인가

| 리소스 | 접근 제어 | 방식 |
|--------|----------|------|
| 저장소 JSON 파일 | OS 파일 권한 | 기존 명령과 같다. low-stock은 읽기 권한만 필요하다(쓰기 권한 불필요) |
| `low-stock` 명령 | 없음 | 로컬 CLI. 인증 개념 없음 (기존 add/remove/list와 동일) |

### 데이터 보호

| 데이터 | 보호 수준 | 방식 |
|--------|----------|------|
| 저장소 파일 무결성 | 높음 (C-1) | `store.save` 미호출, 오류 경로에서 저장소 미접근(TD-4, TD-5). TS-06·TS-12·TS-13·TS-17로 바이트·디렉토리 목록 불변 검증 |
| 품목 데이터(SKU, qty) | 낮음 | 민감정보 아님. `name`/`location`은 출력하지 않는다(요구 형식 `SKU\tQTY`) |

### 입력 검증

| 입력 | 검증 규칙 | 위치 |
|------|----------|------|
| `--below` 원문 | 필수(argparse `required=True`, 누락 시 exit 2) → `int(raw)` 성공 → `>= 1`. 실패 시 exit 5 + `invalid:` 1줄 | `build_parser()`(존재), `_parse_below`(값) |
| `--below` 원문의 출력 반영 | 오류 메시지에 repr로만 삽입해 개행·제어문자 주입으로 출력 줄 수가 바뀌지 않게 한다 | `cmd_low_stock` (TD-6) |
| `--store` 경로 | 기존 `store_path` 규칙 그대로. 신규 검증 없음 | `main()` (기존) |
| 거대 정수 N | 파이썬 임의 정밀도 int라 오버플로 없음. 상한 제한 없음(EC-09) | `_parse_below` |

---

## 6. 에러 핸들링

### 에러 분류

HTTP 대신 프로세스 종료 코드로 구분한다 (`docs/CONVENTIONS.md`).

| 분류 | 예시 | 처리 방식 | 종료 코드 |
|------|------|----------|-----------|
| 비즈니스(입력값) | `--below abc`, `3.5`, `""`, `3.0`, `1e2` | stderr `invalid:` 1줄, stdout 빈, 저장소 미접근 | 5 |
| 비즈니스(입력값) | `--below 0`, `--below -3`, `--below=-3` | 같음 | 5 |
| CLI 사용 오류 | `--below` 누락 | argparse 기본 처리(usage + error). 핸들러 미진입 | 2 |
| 정상(빈 결과) | 해당 품목 없음, 빈 저장소, 저장소 파일 부재 | 무출력 | 0 |
| 시스템(범위 밖) | 손상된 JSON, 읽기 권한 없음 | 신규 처리 없음. 기존 명령과 같은 동작(파이썬 예외 전파) 유지 (SPEC A-2, Non-goals) | 기존 동작 |

종료 코드 5는 low-stock 잘못된 N 전용이며 기존 코드 0, 1, 2(`stockctl/cli.py:32,35`, `docs/CLI.md`)와 겹치지 않는다.

### 실패 시나리오

| # | 시나리오 | 원인 | 대응 | 검증 TS |
|---|---------|------|------|--------|
| F-1 | 비정수 N | `int(raw)` ValueError | `_parse_below` → `None` → stderr 1줄, exit 5 | TS-04 |
| F-2 | 0 이하 N | `int(raw) <= 0` | 같음 | TS-05 |
| F-3 | `--below -3`이 옵션으로 오인 | argparse 음수 처리 | TD-2: 값으로 수신되어 F-2 경로. 서브파서에 음수형 옵션 정의 금지 | TS-05 |
| F-4 | argparse `type=int` 경로로 exit 2/usage 발생 | `type=int` 사용 시 | TD-1: `type` 미지정 | TS-04 (`usage:`/`Traceback` 미포함 단언) |
| F-5 | 잘못된 N + 저장소 부재/빈 상태 | 저장소 상태가 판정에 개입 | TD-4: 검증 선행, 저장소 미접근 | TS-13 |
| F-6 | 저장소 파일 부재 시 파일 생성 | `save` 호출 또는 쓰기 모드 open | TD-5: `load`만 호출 | TS-12, TS-13 |
| F-7 | 조회로 저장소 바이트·mtime 변경 또는 `.tmp` 생성 | `save` 호출 | TD-5 | TS-06 |
| F-8 | `--below` 누락 | 필수 인자 없음 | argparse exit 2(OQ-01), 저장소 미접근 | TS-17 |
| F-9 | 오류 메시지가 여러 줄 | 원문 개행 포함 | TD-6: repr 삽입 | TS-04, TS-05 (줄 수 단언) |
| F-10 | 기존 명령 회귀 | 기존 서브파서·핸들러 수정 | 기존 코드 무수정, 추가만 | TS-07 |

### 복구 전략

재시도·폴백 대상이 없다. low-stock은 상태를 바꾸지 않는 멱등 조회이므로 실패 시 사용자가 올바른 N으로 다시 실행하면 된다. 부분 쓰기 가능성이 없어 롤백도 필요 없다. 로깅은 기존 CLI와 같이 별도 로그 없이 stderr 한 줄과 종료 코드로 원인을 구분한다.

---

## 7. 제약 반영

| # | 제약 조건 (SPEC.md) | 설계 반영 위치 | 반영 방식 |
|---|-------------------|--------------|----------|
| 1 | C-1: 저장소 읽기만, 바이트 동일·새 파일(`*.tmp`) 없음 | §3 내부 인터페이스, TD-4, TD-5, §5 데이터 보호 | `store.load`만 호출, `store.save` 금지, 오류 경로는 저장소 미접근. TS-06/12/13/17 검증 |
| 2 | C-2: 기존 add/remove/list·`tests/test_basic.py` 그대로 동작 | §1 변경 영향 범위, TD-1(대안 기각 사유), TD-8 | 기존 서브파서·핸들러·`store.py`·`test_basic.py` 무수정, 추가만. TS-07 전체 pytest |
| 3 | C-3: 외부 패키지 금지, 표준 라이브러리만 (`.opal/AGENT.md:18` "외부 패키지 추가 금지(표준 라이브러리만)") | §3, TD-1~TD-8 | `argparse`, `sys`, 내장 `int`/`sorted`만 사용. 테스트는 기존과 같은 pytest + `subprocess`/`json`/`os` 표준 모듈 |
| 4 | C-4: @header 유지·갱신 (`docs/CONVENTIONS.md` "모든 소스 파일 상단에 @header(module/layer/domain/description/exports)를 둔다.") | §1 컴포넌트 구성, ACT-001 완료 기준 | `stockctl/cli.py` description을 "add/remove/list/low-stock 서브커맨드…"로 갱신. exports는 기존 관례(핸들러 비공개, `main`만)대로 `["main"]` 유지. `tests/test_low_stock.py`에 `tests/test_basic.py:1-9` 형식 @header(module `test_low_stock`, layer `test`, domain `inventory`, exports `[]`) |
| 5 | C-4: 오류는 stderr 한 줄 + 종료 코드 (`docs/CONVENTIONS.md` "오류는 stderr에 한 줄로 쓰고 종료 코드로 구분한다.") | §3 에러 표, TD-6, §6 | `invalid: ... {raw!r}` 1줄 + exit 5 |
| 6 | C-4: 테스트는 `tests/` pytest, `python -m stockctl` 호출 (`docs/CONVENTIONS.md`) | TD-8 | `tests/test_low_stock.py`에서 `subprocess.run([sys.executable, "-m", "stockctl", ...])` |
| 7 | 종료 코드 5는 low-stock 잘못된 N 전용, 기존 0/1/2와 비중복 | §6 에러 분류 | 5는 `cmd_low_stock` 오류 분기에서만 반환 |
| 8 | 통합 포인트: argparse 서브커맨드 구조 합류, 전역 `--store`·`store_path` 공유 | §1 컴포넌트, §3 `build_parser()` 추가분 | `sub.add_parser("low-stock")` + `set_defaults(func=cmd_low_stock)`. 경로는 기존 `main()`에서 확정된 `args.store` 사용 |
| 9 | 통합 포인트: `store.load` 계약 준수, `store.save` 호출 금지 | TD-5 | 같음 |
| 10 | 통합 포인트: `docs/CLI.md` 표 형식(명령 \| 설명 \| 종료 코드) | ACT-001 범위 | 행 예: `` `stockctl low-stock --below N` `` \| qty < N 품목을 SKU 오름차순 `SKU\tQTY` 줄 출력(해당 없으면 무출력) \| 0 성공·빈 결과, 5 잘못된 N. 기존 3행과 "저장소 경로: …" 문구 유지 |
| 11 | R-1: N 검증을 argparse type 변환 실패 경로에 맡기지 않음, 음수 오인 방지 | TD-1, TD-2 | `type` 미지정 + 핸들러 검증. 음수는 argparse 기본 동작으로 값 수신(실측) |
| 12 | A-1: 저장소 파일 부재 = 빈 저장소, 무출력 exit 0, 파일 미생성 | TD-5 | `store.load` 기존 동작 그대로 |
| 13 | A-2: 손상 JSON은 신규 정의 없음, 기존 동작 유지 | §6 에러 분류(시스템) | 신규 처리 코드 없음 |
| 14 | A-3: `int()` 변환 성공 = 정수 | TD-3 | `_parse_below`가 `int(raw)`만 사용 |
| 15 | [MUST] PM 검토 기준 "기존 add/remove/list 동작 회귀 없음" (`.opal/AGENT.md:14`) | 제약 2와 같음 | TS-07 |

---

## 8. ACT 분해

기능이 작고 응집적이어서(서브파서 1개 + 함수 2개 + 신규 테스트 파일 + 문서 1행) ACT 1개로 구성한다(TD-9). 같은 파일을 여러 ACT로 나누지 않는다.

### 추적 매트릭스

| AC | FR | TS | 담당 ACT | 커버리지 |
|----|----|----|---------|----------|
| AC-01 | FR-01, FR-02 | TS-01 | ACT-001 | 완료 |
| AC-02 | FR-01 | TS-02 | ACT-001 | 완료 |
| AC-03 | FR-03 | TS-03 | ACT-001 | 완료 |
| AC-04 | FR-04 | TS-04 | ACT-001 | 완료 |
| AC-05 | FR-05 | TS-05 | ACT-001 | 완료 |
| AC-06 | FR-06 | TS-06 | ACT-001 | 완료 |
| AC-07 | FR-07 | TS-07 | ACT-001 | 완료 |
| AC-08 | FR-08 | TS-08 | ACT-001 | 완료 |
| EC-01 | FR-02 | TS-09 | ACT-001 | 완료 |
| EC-02, EC-03 | FR-02 | TS-10 | ACT-001 | 완료 |
| EC-04 | FR-03 | TS-11 | ACT-001 | 완료 |
| EC-05 | FR-03, FR-06 | TS-12 | ACT-001 | 완료 |
| EC-06 | FR-04, FR-05, FR-06 | TS-13 | ACT-001 | 완료 |
| EC-07 | FR-05 | TS-05 | ACT-001 | 완료 |
| EC-08 | FR-04 | TS-04 | ACT-001 | 완료 |
| EC-09 | FR-02 | TS-14 | ACT-001 | 완료 |
| EC-10 | FR-02 | TS-15 | ACT-001 | 완료 |
| EC-11 | FR-02 | TS-16 | ACT-001 | 완료 |
| EC-12 | FR-01, FR-06 | TS-17 | ACT-001 | 완료 |

### ACT ↔ TS 매핑 (TEST-SCENARIOS.md "담당 ACT" 할당)

TEST-SCENARIOS.md는 PM 소유라 수정하지 않는다. 각 TS의 "담당 ACT"는 아래 표를 기준으로 한다.

| TS | 담당 ACT | 테스트 위치 |
|----|---------|------------|
| TS-01 | ACT-001 | `tests/test_low_stock.py` |
| TS-02 | ACT-001 | `tests/test_low_stock.py` (env 주입) |
| TS-03 | ACT-001 | `tests/test_low_stock.py` |
| TS-04 | ACT-001 | `tests/test_low_stock.py` (parametrize 5건) |
| TS-05 | ACT-001 | `tests/test_low_stock.py` (parametrize 3건) |
| TS-06 | ACT-001 | `tests/test_low_stock.py` |
| TS-07 | ACT-001 | 저장소 루트 `python -m pytest -q tests/` 실행 로그 (신규 테스트 파일 없음) |
| TS-08 | ACT-001 | `tests/test_low_stock.py` (`docs/CLI.md` 내용 검사) |
| TS-09 | ACT-001 | `tests/test_low_stock.py` |
| TS-10 | ACT-001 | `tests/test_low_stock.py` |
| TS-11 | ACT-001 | `tests/test_low_stock.py` |
| TS-12 | ACT-001 | `tests/test_low_stock.py` |
| TS-13 | ACT-001 | `tests/test_low_stock.py` |
| TS-14 | ACT-001 | `tests/test_low_stock.py` |
| TS-15 | ACT-001 | `tests/test_low_stock.py` |
| TS-16 | ACT-001 | `tests/test_low_stock.py` |
| TS-17 | ACT-001 | `tests/test_low_stock.py` |

TS-01~TS-17 17건 모두 ACT-001에 매핑되며 미할당 TS는 없다.

### 의존관계 그래프

```
ACT-001   (고립 ACT, 선행·후행 없음)
```

순환 없음. 모든 ACT(1개)가 그래프에 포함된다.

### 실행 그룹

```
Group 1 (순차): ACT-001
```

### ACT 목록

#### ACT-001: low-stock 명령 구현 + 테스트 + CLI 계약 문서화
- **폴더**: tasks/001-low-stock/actions/ACT-001-low-stock-command/
- **담당 에이전트**: `opal-be-agent` (`docs/PROJECT.md` 프로젝트 구성: CLI `stockctl/`, `tests/` → opal-be-agent. `docs/CLI.md`는 CLI 계약 문서로 같은 ACT가 소유)
- **범위 (대상 파일)**:
  - `stockctl/cli.py` (수정): @header description 갱신; `_parse_below`, `cmd_low_stock` 추가; `build_parser()`에 `low-stock` 서브파서(`--below` 필수, `type` 미지정) 추가. 기존 `cmd_add`/`cmd_remove`/`cmd_list`와 기존 서브파서 정의는 수정하지 않는다.
  - `tests/test_low_stock.py` (신규): @header + TS-01~TS-06, TS-08~TS-17 테스트.
  - `docs/CLI.md` (수정): 명령 표에 `low-stock` 행 추가(§7 제약 10의 형식).
  - 변경 금지: `stockctl/store.py`, `stockctl/__main__.py`, `stockctl/__init__.py`, `tests/test_basic.py`.
- **AC 매핑**: AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-07, AC-08
- **FR 매핑**: FR-01, FR-02, FR-03, FR-04, FR-05, FR-06, FR-07, FR-08
- **EC 매핑**: EC-01~EC-12
- **TS 매핑**: TS-01, TS-02, TS-03, TS-04, TS-05, TS-06, TS-07, TS-08, TS-09, TS-10, TS-11, TS-12, TS-13, TS-14, TS-15, TS-16, TS-17
- **설계 근거**: §1 컴포넌트 구성, §3 내부 인터페이스, TD-1~TD-9
- **의존 (선행)**: 없음
- **완료 기준**:
  1. TS-01~TS-06, TS-08~TS-17이 `tests/test_low_stock.py`에서 Green.
  2. TS-07: 저장소 루트에서 `python -m pytest -q tests/` 전체 통과(실패 0, `tests/test_basic.py` 2건 포함), 실행 로그를 증거로 기록.
  3. `git diff` 기준 변경 파일이 `stockctl/cli.py`, `tests/test_low_stock.py`, `docs/CLI.md` 3개뿐이고, `stockctl/cli.py`의 기존 핸들러·서브파서 줄에 수정이 없다.
  4. `cmd_low_stock`에 `store.save` 호출이 없고, `--below`에 `type=`이 지정되지 않았다(TD-1, TD-5 준수, 코드 확인).
  5. `stockctl/cli.py` @header description 갱신, `tests/test_low_stock.py` @header 존재(C-4).
  6. 새 외부 패키지 import 없음(C-3).
