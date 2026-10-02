---
template: sdlc-v2
---
# TEST-SCENARIO: stockctl 다중 위치 재고·이동·감사·가져오기·충돌 감지

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: worktree `feat/OP-TASK-001` 루트에서 `python3 -m pytest`. CLI는 `python3 -m stockctl --store <tmp>/s.json ...` subprocess로 호출한다(`docs/CONVENTIONS.md`). 각 시나리오는 pytest `tmp_path`의 독립 저장소를 쓴다.
- 공통 데이터: 레거시 저장소 fixture는 테스트가 JSON을 직접 기록한다 — `{"items": {"A1": {"name": "Apple", "qty": 5, "location": "W1"}, "B1": {"name": "Banana", "qty": 0, "location": "MAIN"}}}`(`version` 키 없음).
- "바이트 불변" 판정: 명령 전후 저장소 파일과 `<저장소>.audit.jsonl`의 `read_bytes()`(없으면 부재 상태)를 비교한다.
- 대역 사용과 한계: 사용하지 않음. 모든 검증은 실제 CLI 프로세스와 실제 파일로 수행한다.
- 실행 조건: 자동 실행.
- 병렬 그룹: 선언 없음(순차).

## Scenarios

| ID | 유형 | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|---|
| S-1 | integration | AC-1, C-4 | 레거시 fixture 저장소 | ① `list` ② `version` ③ `add A1 --qty 1 --location W2` ④ 저장소 JSON 로드 | ① `A1\tApple\tW1\t5` 한 줄만 출력(B1은 수량 0이라 미출력), exit 0 ② stdout `0` ③ exit 0 ④ 최상위 `version == 1`, `items.A1 == {"name": "Apple", "locations": {"W1": 5, "W2": 1}}`, `items.B1 == {"name": "Banana", "locations": {"MAIN": 0}}`, 어느 품목에도 `qty`·`location` 키 없음, 저장소 디렉토리에 `.tmp` 파일 없음 | pytest subprocess + JSON 파일 검사 | 구현 전 RED |
| S-2 | integration | AC-2 | 빈 `tmp_path` | `version` → `add A1 --qty 5` → `version` → `remove A1 --qty 1` → `transfer A1 --from MAIN --to W2 --qty 1` → `version` → 이어서 실패 명령 6종: `remove ZZ --qty 1`, `remove A1 --qty 99`, `transfer A1 --from MAIN --to MAIN --qty 1`, `transfer A1 --from MAIN --to W2 --qty 0`, `transfer ZZ --from MAIN --to W2 --qty 1`, `add A1 --qty 1 --expect-version 0` 각각 전후 비교 | version 출력이 `0`, `1`, `3` 순서. 실패 명령 6종 각각 exit ≠ 0이고 저장소·감사 파일 바이트 불변, 이후 `version`은 계속 `3` | pytest subprocess + 바이트 비교 | 구현 전 RED |
| S-3 | integration | AC-3 | 빈 `tmp_path` | ① `add A1 --qty 5 --name Apple` ② `add A1 --qty 3 --location W2` ③ `remove A1 --qty 1 --location W2` ④ `remove A1 --qty 2` ⑤ `remove ZZ --qty 1` ⑥ `remove A1 --qty 5 --location W2` ⑦ `remove A1 --qty 1 --location NOPE` ⑧ `list` | ① stdout `A1 qty=5` exit 0 ② `A1 qty=3` exit 0 ③ `A1 qty=2` exit 0 ④ `A1 qty=3` exit 0 ⑤ exit 1 ⑥·⑦ exit 2, stderr가 `insufficient:`로 시작 ⑧ `A1\tApple\tMAIN\t3`과 `A1\tApple\tW2\t2` 두 줄 | pytest subprocess | 구현 전 RED |
| S-4 | check | C-2 | 구현 완료 worktree | `python3 -m pytest tests/test_basic.py -q` 및 `git diff main -- tests/test_basic.py` | pytest 전건 pass, `tests/test_basic.py` diff 없음 | pytest + git diff | 구현 후 |
| S-5 | integration | AC-4 | 빈 `tmp_path` | `add A1 --qty 2 --location W9`, `add A1 --qty 3`, `add A1 --qty 1 --location B0`, `add B1 --qty 1 --location W2`, `add C1 --qty 1 --location X`, `remove C1 --qty 1 --location X` 후 `list` | stdout 줄 목록이 정확히 `A1\tA1\tB0\t1`, `A1\tA1\tMAIN\t3`, `A1\tA1\tW9\t2`, `B1\tB1\tW2\t1`(C1 미출력), exit 0 | pytest subprocess | 구현 전 RED |
| S-6 | integration | AC-5 | `add A1 --qty 5` 완료 저장소 | ① `transfer A1 --from MAIN --to W2 --qty 2` ② `list` ③ `transfer ZZ --from MAIN --to W2 --qty 1` ④ `transfer A1 --from MAIN --to W2 --qty 4` ⑤ `transfer A1 --from MAIN --to W2 --qty 0` ⑥ `transfer A1 --from MAIN --to W2 --qty -1` ⑦ `transfer A1 --from W2 --to W2 --qty 1` | ① stdout `A1 MAIN->W2 2`, exit 0 ② `A1\tA1\tMAIN\t3`, `A1\tA1\tW2\t2` ③ exit 1 ④ exit 2, stderr `insufficient:` 시작 ⑤·⑥·⑦ exit 5, stderr `invalid:` 시작. ③~⑦ 각각 저장소 파일 바이트 불변 | pytest subprocess + 바이트 비교 | 구현 전 RED |
| S-7 | integration | AC-6 | 빈 `tmp_path` | `add A1 --qty 5`, `remove A1 --qty 2`, `transfer A1 --from MAIN --to W2 --qty 1`, 실패 `remove A1 --qty 99`, 실패 `transfer A1 --from MAIN --to MAIN --qty 1` 후 `<저장소>.audit.jsonl` 파싱 | 파일이 정확히 3줄, 각 줄이 JSON 객체로 키 집합 `{ts, op, sku, changes}`, `datetime.fromisoformat(ts)` 성공, (op, sku, changes) 순서가 (`add`, `A1`, `{"MAIN": 5}`), (`remove`, `A1`, `{"MAIN": -2}`), (`transfer`, `A1`, `{"MAIN": -1, "W2": 1}`) | pytest subprocess + JSON 파싱 | 구현 전 RED |
| S-8 | integration | AC-7 | 빈 `tmp_path` | ① 감사 파일 없는 상태에서 `history A1` ② S-7의 성공 명령 3개 + `add B1 --qty 1` 후 `history A1` ③ `history ZZ` | ① 출력 없음, exit 0 ② 정확히 3줄, 각 줄 `\t` 3필드, 첫 필드는 ISO 8601로 파싱됨, (OP, CHANGES)가 위에서부터 (`transfer`, `MAIN:-1,W2:+1`), (`remove`, `MAIN:-2`), (`add`, `MAIN:+5`), B1 기록 없음 ③ 출력 없음, exit 0 | pytest subprocess | 구현 전 RED |
| S-9 | integration | AC-8, AC-6 | `add Z9 --qty 1` 완료 저장소(version 1), CSV `in.csv`: 헤더 `sku,name,location,qty` + 행 `A1,Apple,W1,5` / `A1,Apple,W2,3` / `B1,Banana,MAIN,2` / `C1,,W1,1` / `D1,Dragon,W1,0` / `E1,Egg,W1,abc` / `F1,Fig,W1,-2` | `import-csv <tmp>/in.csv` 후 `version`, `list`, `in.csv.rejected.csv`·감사 파일 검사 | stdout `applied 3, rejected 4`, exit 3. `version` = `2`(1회 저장). list에 `A1\tApple\tW1\t5`, `A1\tApple\tW2\t3`, `B1\tBanana\tMAIN\t2` 포함, C1·D1·E1·F1 없음. `in.csv.rejected.csv` 헤더가 `sku,name,location,qty,reason`이고 데이터 4행이 원래 4개 값 + 비어 있지 않은 reason. 감사 파일에 추가된 줄이 `op=import`로 A1(`{"W1": 5, "W2": 3}`)·B1(`{"MAIN": 2}`) SKU당 1줄씩 정확히 2줄 | pytest subprocess + csv/JSON 파싱 | 구현 전 RED |
| S-10 | integration | AC-8 | 빈 `tmp_path`, CSV: 헤더 + `A1,Apple,W1,5` / `B1,Banana,W2,1` | `import-csv <tmp>/ok.csv` | stdout `applied 2, rejected 0`, exit 0, `ok.csv.rejected.csv` 파일 없음, `version` = `1` | pytest subprocess | 구현 전 RED |
| S-11 | integration | AC-9 | `add A1 --qty 5` 완료 저장소(version 1), 헤더+`B1,Banana,W1,1` CSV | ① `add A1 --qty 1 --expect-version 0` ② `remove A1 --qty 1 --expect-version 5` ③ `transfer A1 --from MAIN --to W2 --qty 1 --expect-version 0` ④ `import-csv <csv> --expect-version 0` ⑤ `add A1 --qty 1 --expect-version 1` ⑥ `version` | ①~④ 각각 exit 4, stderr가 정확히 `conflict: expected V, found 1`(V는 각 기대값), 저장소·감사 파일 바이트 불변, ④ 뒤 `<csv>.rejected.csv` 없음 ⑤ exit 0 ⑥ stdout `2` | pytest subprocess + 바이트 비교 | 구현 전 RED |
| S-12 | check | C-3 | 구현 완료 worktree | `docs/CLI.md` 검사 | add·remove·list·transfer·history·import-csv·version 7개 명령, `--expect-version`, 종료 코드 3·4·5, `.audit.jsonl`·`.rejected.csv` 형식이 모두 기술되고 각 출력 형식이 PLAN D-5~D-16과 일치 | 문서 Read + grep | 구현 후 |
| S-13 | check | C-1, C-4 | 구현 완료 worktree | `stockctl/*.py`의 import 문 추출 후 `sys.stdlib_module_names`·패키지 내부 모듈과 대조, 각 소스·테스트 파일 상단 @header 존재 확인, `stockctl/store.py`의 저장 경로가 임시 파일 기록 후 `os.replace` 사용 | 외부 패키지 import 0건, @header(module/layer/domain/description/exports) 누락 0건, 원자 교체 사용 확인 | 정적 검사(grep·python) | 구현 후 |
