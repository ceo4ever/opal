---
template: sdlc-v2
---
# PLAN: stockctl 다중 위치 재고·이동·감사·가져오기·충돌 감지

> 입력: [TASK.md](TASK.md) | 작성자: PM (actor=coordinator, PM 경로)

## 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | CLI 계약 | `docs/CLI.md` | 현행 명령·종료 코드·저장소 경로 우선순위 |
| D-2 | 설계 | 컨벤션 | `docs/CONVENTIONS.md` | 표준 라이브러리, @header, 원자 교체, stderr 한 줄, pytest·`python -m stockctl` |
| D-3 | 소스 | store.py | `stockctl/store.py` | 현행 저장 구조·load/save |
| D-4 | 소스 | cli.py | `stockctl/cli.py` | 현행 add/remove/list 동작·출력 |
| D-5 | 소스 | test_basic.py | `tests/test_basic.py` | 보존해야 할 회귀 계약 |
| D-6 | 기획 | PM 프로필 | `.opal/AGENT.md` | 금지사항(외부 패키지 금지) |

## Approach

저장 계층(`stockctl/store.py`)이 새 형식(`items[sku] = {name, locations}` + 최상위 `version`)과 레거시 해석, version 증가 저장, 감사 로그 읽기·쓰기를 소유하고, 명령 계층(`stockctl/cli.py`)이 7개 서브커맨드(add·remove·list·transfer·history·import-csv·version)의 인자·판정 순서·출력을 소유한다. 현행 구조는 품목당 단일 위치이며(→ D-3:6, D-3:19-30) 명령은 add/remove/list 셋뿐이다(→ D-4:50-66). 계약 문서 `docs/CLI.md`는 코드와 병렬로 같은 계약을 기술한다. 비즈니스 로직·CLI 계약 변경이므로 RED-first를 적용한다 — `opal-test-agent`가 구현 전에 새 공개 동작 테스트를 작성해 실패를 관찰한 뒤 구현 워커가 GREEN을 만든다.

## Findings

### 직접 변경
- `stockctl/store.py`: 단일 위치 구조 docstring·load/save(→ D-3:6, D-3:19-30)를 다중 위치·version·레거시 정규화·감사 로그 helper로 교체한다.
- `stockctl/cli.py`: add/remove/list(→ D-4:16-47)와 parser(→ D-4:50-66)를 새 계약으로 바꾸고 transfer·history·import-csv·version 서브커맨드와 `--expect-version`을 추가한다.

### 회귀 확인
- `tests/test_basic.py`: `A1\tApple\tMAIN\t5` list 출력(→ D-5:19-22)과 remove 수량 부족 exit 2(→ D-5:25-28)가 변경 없이 통과해야 한다(C-2).
- `stockctl/__main__.py`: `main()` 반환값을 `sys.exit`에 넘기는 진입점이 그대로 동작해야 한다.

### 문서 갱신
- `docs/CLI.md`: 명령 표(→ D-1:3-7)를 새 7개 명령·옵션·종료 코드·출력 형식과 저장소/감사 로그/거부 행 파일 형식으로 갱신한다(C-4).

### 미확인 가정
없음.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| 저장 형식 | 파일 = `{"items": {SKU: {"name": str, "locations": {LOC: int}}}, "version": int}`. 직렬화는 현행대로 `json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)` | AC-1 원문. 직렬화 옵션은 현행 유지(→ D-3:29) |
| 레거시 해석 | `store.load`가 품목별로 `locations` 키가 없으면 `{"name": item.get("name") or sku, "locations": {item.get("location") or "MAIN": item.get("qty", 0)}}`로 변환하고, 최상위 `version`이 없으면 0으로 둔다. `load`는 파일을 쓰지 않는다(실패 명령에서 레거시 파일이 바뀌지 않음). 파일 부재 = `{"items": {}, "version": 0}` | AC-1 "읽을 때 해석, 다음 성공 저장 때 새 형식", AC-5 실패 시 바이트 불변 |
| 저장 | `store.save(path, data)`가 `data["version"]`을 1 올린 뒤 `<path>.tmp`에 쓰고 `os.replace`로 교체하며 새 version을 반환한다. 실패하는 명령은 `save`를 호출하지 않는다 | AC-2, C-3(→ D-2 "임시 파일 기록 후 `os.replace`로 원자 교체") |
| 명령 판정 순서 | 모든 변경 명령: ① 인자 검증(exit 5) → ② `store.load` → ③ `--expect-version` 비교(exit 4) → ④ 도메인 검사(미등록 SKU exit 1 → 수량 부족 exit 2) → ⑤ 변경·`save`·감사 기록·stdout. ①~④ 실패 시 저장소·감사 로그·거부 행 파일 어느 것도 쓰지 않는다. 오류는 stderr 한 줄 | 요구서가 정하지 않은 복수 오류 동시 발생 시 우선순위를 고정. 입력 오류는 저장소 상태와 무관하므로 먼저, 충돌은 저장소 내용 판정보다 먼저(→ D-2 "오류는 stderr에 한 줄") |
| `--expect-version` | add·remove·transfer·import-csv 서브커맨드 옵션 `--expect-version V`(int, 기본 없음). 현재 version ≠ V면 stderr `conflict: expected V, found X`, exit 4 | AC-9 원문 |
| add | `add SKU --qty N [--name NAME] [--location LOC=MAIN] [--expect-version V]`. 신규 SKU는 name = NAME 또는 SKU, NAME이 주어지면 기존 품목 name 갱신. `locations[LOC] += N`. stdout `SKU qty=Q`(Q = 변경 후 해당 LOC 수량), exit 0. qty 값 검증은 추가하지 않는다 | AC-3 "기존 출력·종료 코드 유지"(→ D-4:16-24). 단일 위치였던 기존 파일·MAIN 단독 사용에서 Q는 기존 값과 같다 |
| remove | `remove SKU --qty N [--location LOC=MAIN] [--expect-version V]`. 미등록 SKU: stderr `unknown sku: SKU` exit 1. `locations.get(LOC, 0) < N`: stderr `insufficient: SKU has H at LOC` exit 2. 성공: `locations[LOC] -= N`(0이 되어도 키 보존), stdout `SKU qty=Q`(해당 LOC 잔량), exit 0 | AC-3 원문, 기존 메시지 형식 유지(→ D-4:27-39) |
| list | 품목 SKU 오름차순, 각 품목 내 LOC 오름차순으로 수량 ≠ 0인 위치마다 `SKU\tNAME\tLOC\tQTY` 한 줄, exit 0 | AC-4 원문 |
| transfer | `transfer SKU --from A --to B --qty N [--expect-version V]`(`--from`은 dest `from_loc`). ① N ≤ 0: stderr `invalid: qty must be positive`, A == B: stderr `invalid: from and to must be different`, exit 5 → 이후 판정 순서대로 exit 4/1/2(`insufficient: SKU has H at A`). 성공: A −N, B +N(B 없으면 생성), stdout `SKU A->B N`, exit 0 | AC-5 원문 |
| 감사 로그 | 경로 `str(store_path) + ".audit.jsonl"`. 성공 저장 직후 append 모드로 레코드당 한 줄 `json.dumps({"ts","op","sku","changes"}, ensure_ascii=False, sort_keys=True)`. `ts = datetime.now(timezone.utc).isoformat(timespec="seconds")`. 한 명령이 바꾼 SKU마다 한 줄: add `{LOC: +N}`, remove `{LOC: -N}`, transfer `{A: -N, B: +N}`, import-csv는 반영된 행을 SKU별로 합산(같은 LOC는 합계)해 SKU 오름차순으로 SKU당 한 줄, op `import` | AC-6 "SKU별로 … JSON 한 줄". import의 '반영된 행'은 거부 행을 제외한다는 뜻으로 해석 |
| history | `history SKU`: 감사 로그 파일을 줄 순서로 읽어(빈 줄 무시) sku가 일치하는 레코드를 역순(나중에 추가된 것이 최신)으로 출력. 형식 `TS\tOP\tLOC:DELTA,...`, changes는 LOC 오름차순, DELTA는 `format(delta, "+d")`. 파일 없음·기록 없음은 출력 없이 exit 0 | AC-7 원문. 같은 초의 기록도 순서가 유지되도록 ts가 아닌 파일 순서로 최신순을 판정 |
| import-csv 입력 | `import-csv FILE [--expect-version V]`. `open(FILE, encoding="utf-8-sig", newline="")` + `csv.reader`. 파일을 읽을 수 없으면 stderr `invalid: cannot read FILE` exit 5. 첫 행(각 셀 strip)이 정확히 `sku,name,location,qty`가 아니면(빈 파일 포함) stderr `invalid: header must be sku,name,location,qty` exit 5 | 요구서가 정하지 않은 파일 수준 오류를 transfer의 입력 오류 코드(5·`invalid:`)로 통일 |
| import-csv 행 판정 | 셀이 하나도 없는 빈 줄은 건너뛰고 집계하지 않는다. 각 셀은 앞뒤 공백 제거 후 판정. 거부 사유 판정 순서: 셀 수 ≠ 4 → `column_count`, 빈 필드 → `empty_field`, qty가 `[0-9]+` 전체 일치가 아니거나 0 → `invalid_qty`. 유효 행은 파일 순서대로 add와 같은 의미로 반영(name은 행의 name으로 설정, `locations[location] += qty`) | AC-8 "양의 정수가 아니거나 필드가 비면 거부", "add와 같은 의미" |
| import-csv 결과 | 판정 순서 ③ 뒤 반영 행 N > 0이면 `save` 1회 + 감사 기록, N = 0이면 저장·감사 기록 없음. M > 0이면 `FILE + ".rejected.csv"`를 덮어써 헤더 `sku,name,location,qty,reason` + 거부 행(원래 셀을 4칸으로 맞춤: 부족분 빈 문자열, 초과분 절단 — 공백 제거 전 원래 값) + reason을 `csv.writer`로 쓰고 exit 3. M = 0이면 그 파일을 만들거나 건드리지 않고 exit 0. stdout은 exit 0·3 모두 `applied N, rejected M` | AC-8 원문 "한 번의 저장으로 모두 반영" |
| version | `version`: 현재 version 정수 한 줄, exit 0, 저장하지 않음(파일 부재 0, 레거시 0) | AC-2 원문 |
| 모듈 경계 | `store.py` exports: `load`, `save`, `store_path`, `audit_path`, `append_audit`, `read_audit`. `cli.py` exports `main`. 두 파일의 @header description·exports를 새 계약으로 갱신 | → D-2 "모든 소스 파일 상단에 @header" |
| RED 테스트 소유 | `opal-test-agent`(red mode)가 새 공개 동작 테스트를 `tests/test_multiloc.py`에 `python -m stockctl` subprocess 방식으로 작성한다. 구현 워커는 테스트 파일을 수정하지 않는다. `tests/test_basic.py`는 수정하지 않는다 | `red-first.md` §1.5 "구현자와 다른 주체가 … 실패 테스트를 작성", C-2, → D-2 "CLI는 `python -m stockctl`로 호출" |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. 다중 위치 저장소·명령 구현 | opal-be-agent | `stockctl/store.py`, `stockctl/cli.py` | Decisions and contracts의 저장 형식·레거시 해석·저장·감사 로그를 `store.py`에, 판정 순서·`--expect-version`·add·remove·list·transfer·history·import-csv·version 계약을 `cli.py`에 구현하고 두 파일 @header를 갱신한다. 표준 라이브러리(`argparse`, `json`, `csv`, `os`, `re`, `datetime`, `pathlib`, `sys`)만 사용 | 없음 | P1 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, AC-9, C-1, C-2, C-3 |
| W-2. CLI 계약 문서 갱신 | opal-task-agent | `docs/CLI.md` | 명령 표를 7개 명령(옵션·stdout·stderr 접두사·종료 코드)으로 교체하고, 판정 순서, 저장소 JSON 형식·레거시 해석·version 규칙, 감사 로그 경로·레코드 필드, history 출력 형식, import-csv 헤더·거부 사유·`.rejected.csv` 형식을 Decisions and contracts와 같은 내용으로 기술한다. 저장소 경로 우선순위 문장은 유지 | 없음 | P1 | C-4 |

## Risks

추가 검증이 필요한 위험 없음.

## Release and recovery

- 적용 순서: RED 테스트 작성·실패 관찰(`opal-test-agent`) → P1의 W-1·W-2 병렬 → TEST 단계 전체 회귀(`python -m pytest tests`).
- 검증 범위: 결정론 CLI subprocess 테스트(새 계약 + `tests/test_basic.py` 회귀), 레거시 파일 무손실 전환, 실패 시 저장소 바이트 불변. 외부 연동 없음.
- 실측 경계: 해당 없음(시간·성능 목표 없음).
- 실패 시: 설치·배포 대상이 없는 로컬 CLI 변경이며 worktree 브랜치(`feat/OP-TASK-001`)에서만 변경하므로, 실패하면 해당 커밋을 되돌리거나 브랜치를 merge하지 않는다.
