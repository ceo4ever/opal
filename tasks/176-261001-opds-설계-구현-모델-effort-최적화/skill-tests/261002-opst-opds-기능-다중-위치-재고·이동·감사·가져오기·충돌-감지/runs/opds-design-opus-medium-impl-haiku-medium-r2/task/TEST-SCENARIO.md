---
template: sdlc-v2
---
# TEST-SCENARIO: stockctl 다중 위치 재고·이동·감사·가져오기·충돌 감지

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: worktree 루트에서 Python 3 + pytest. CLI는 `subprocess.run([sys.executable, "-m", "stockctl", "--store", str(tmp_path / "s.json"), ...], capture_output=True, text=True)`로 호출한다(`tests/test_basic.py:14-16`과 같은 방식). 행동 시나리오는 `tests/test_multiloc.py`에 시나리오 ID를 함수명에 포함해 작성한다(예: `test_s1_legacy_migration`).
- 공통 데이터: 각 시나리오는 pytest `tmp_path`의 빈 디렉터리에서 시작한다. 감사 로그는 `<tmp>/s.json.audit.jsonl`, import 입력은 `<tmp>/in.csv`, 거부 파일은 `<tmp>/in.csv.rejected.csv`.
- 바이트 불변 확인: 실패 명령 직전·직후에 저장소 파일을 `read_bytes()`로 읽어 동일한지, 감사 로그 줄 수가 같은지 비교한다.
- 대역 사용과 한계: 사용하지 않음(실제 CLI 프로세스·실제 파일).
- 실행 조건: 자동 실행. 사람 협업 없음.
- 병렬 그룹: 선언 없음(순차).

## Scenarios

| ID | 유형 | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|---|
| S-1 | integration | AC-1, C-2 | `s.json`에 version 키 없는 기존 형식 `{"items": {"A1": {"name": "Apple", "qty": 5, "location": "WH1"}, "B2": {"name": "Bolt", "qty": 0, "location": "MAIN"}}}`를 기록 | ① `version` ② `list` ③ `add B2 --qty 1` ④ 파일을 JSON으로 읽음 ⑤ `add A1 --qty 1 --location WH1` 후 다시 읽음 | ① stdout `0` ② stdout 정확히 `A1\tApple\tWH1\t5` 한 줄(B2는 0이라 미출력) ③ exit 0 ④ `version == 1`, `items.A1 == {"name": "Apple", "locations": {"WH1": 5}}`, `items.B2 == {"name": "Bolt", "locations": {"MAIN": 1}}`, 어떤 품목에도 `qty`·`location` 키 없음, `s.json.tmp` 파일 없음 ⑤ `version == 2`, `A1.locations.WH1 == 6` | pytest subprocess | 구현 전 RED |
| S-2 | integration | AC-2 | 빈 저장소 | ① `add A1 --qty 5 --name Apple` ② `add A1 --qty 3 --location WH1` ③ `remove A1 --qty 2 --location WH1` ④ `remove A1 --qty 4` ⑤ `remove A1 --qty 5 --location WH1` ⑥ `remove A1 --qty 1 --location NOPE` ⑦ `remove ZZ --qty 1` | ① exit 0, stdout `A1 qty=5` ② exit 0, stdout `A1 qty=3` ③ exit 0, stdout `A1 qty=1` ④ exit 0, stdout `A1 qty=1`(MAIN 기본) ⑤⑥ exit 2, stderr가 `insufficient:`로 시작 ⑦ exit 1 | pytest subprocess | 구현 전 RED |
| S-3 | integration | AC-3 | 빈 저장소 | `add B --qty 1 --location Z`, `add B --qty 1 --location A`, `add A --qty 2 --location M`, `remove B --qty 1 --location Z` 후 `list` | stdout 줄이 정확히 `A\tA\tM\t2`, `B\tB\tA\t1` 순서 두 줄(SKU 다음 LOC 오름차순, 수량 0인 B@Z 미출력) | pytest subprocess | 구현 전 RED |
| S-4 | integration | AC-4, C-4 | `add A1 --qty 5 --location WH1` 완료 상태 | ① `transfer A1 --from WH1 --to WH2 --qty 2` ② `list` ③ 각각 직전 바이트 저장 후 실패 명령: `transfer ZZ --from WH1 --to WH2 --qty 1`, `transfer A1 --from WH1 --to WH2 --qty 9`, `transfer A1 --from WH1 --to WH2 --qty 0`, `transfer A1 --from WH1 --to WH2 --qty -1`, `transfer A1 --from WH1 --to WH1 --qty 1` | ① exit 0, stdout `A1 WH1->WH2 2` ② `A1\tA1\tWH1\t3`, `A1\tA1\tWH2\t2` ③ exit 순서대로 1, 2(stderr `insufficient:` 시작), 5, 5, 5(셋 다 stderr `invalid:` 시작). 각 실패 뒤 저장소 바이트 동일, 감사 로그 줄 수 불변 | pytest subprocess | 구현 전 RED |
| S-5 | integration | AC-5, C-4 | 빈 저장소 | `add A1 --qty 5`, `remove A1 --qty 2`, `transfer A1 --from MAIN --to WH1 --qty 1`, 실패 명령 `remove A1 --qty 99` 실행 후 `s.json.audit.jsonl`을 줄 단위 JSON으로 읽음 | 정확히 3줄. 각 줄 키 집합이 `{"ts","op","sku","changes"}`, `datetime.fromisoformat(ts)` 성공. 순서대로 `op/changes`가 `add/{"MAIN": 5}`, `remove/{"MAIN": -2}`, `transfer/{"MAIN": -1, "WH1": 1}`, `sku`는 모두 `A1`. 실패 명령은 줄을 추가하지 않음 | pytest subprocess | 구현 전 RED |
| S-6 | integration | AC-6 | 빈 저장소 | ① 감사 로그 없는 상태에서 `history A1` ② `add A1 --qty 5 --location WH2`, `add A1 --qty 1 --location WH1`, `transfer A1 --from WH2 --to WH1 --qty 3`, `add B1 --qty 1` 후 `history A1` ③ `history NOPE` | ① exit 0, stdout 빈 문자열 ② exit 0, 3줄이 최신순: 1줄째 필드 2·3이 `transfer`·`WH1:+3,WH2:-3`, 2줄째 `add`·`WH1:+1`, 3줄째 `add`·`WH2:+5`. 각 줄은 탭 3필드이고 1필드는 `fromisoformat` 성공. B1 기록 미포함 ③ exit 0, stdout 빈 문자열 | pytest subprocess | 구현 전 RED |
| S-7 | integration | AC-7, AC-5 | `add OLD --qty 1` 완료(version 1). `in.csv`: 헤더 `sku,name,location,qty`, 행 `A1,Apple,WH1,5` / `B1,Bolt,MAIN,2` / `A1,Apple,WH2,3` / `C1,Cog,MAIN,abc` / `D1,Disk,MAIN,0` / `E1,,MAIN,1` / `F1,Fan,MAIN,-2` | `import-csv <tmp>/in.csv` 후 `version`, `list`, 거부 파일, 감사 로그 확인 | exit 3, stdout `applied 3, rejected 4`. `version` 출력 `2`(저장 1회). list에 `A1\tApple\tWH1\t5`, `A1\tApple\tWH2\t3`, `B1\tBolt\tMAIN\t2` 포함, C1·D1·E1·F1 없음. `in.csv.rejected.csv`를 `csv.DictReader`로 읽으면 헤더 `sku,name,location,qty,reason`, sku 순서 `C1,D1,E1,F1`, 모든 reason 비어 있지 않음. 감사 로그에 `op == "import"`인 줄이 A1(`{"WH1": 5, "WH2": 3}`)·B1(`{"MAIN": 2}`) 각 1줄 | pytest subprocess | 구현 전 RED |
| S-8 | integration | AC-7 | 빈 저장소, `in.csv`에 헤더 + 유효 행 `A1,Apple,MAIN,4` | `import-csv <tmp>/in.csv` | exit 0, stdout `applied 1, rejected 0`, `in.csv.rejected.csv` 파일 없음, `list`에 `A1\tApple\tMAIN\t4` | pytest subprocess | 구현 전 RED |
| S-9 | integration | AC-8, C-4 | `add A1 --qty 5` 완료(version 1), `in.csv`에 유효 행 1개 | ① `version` ② `add A1 --qty 1 --expect-version 1` ③ 바이트 저장 후 `add A1 --qty 1 --expect-version 9`, `remove A1 --qty 1 --expect-version 0`, `transfer A1 --from MAIN --to WH1 --qty 1 --expect-version 7`, `import-csv <tmp>/in.csv --expect-version 5` ④ `version` | ① stdout `1` ② exit 0 ③ 모두 exit 4, stderr가 각각 `conflict: expected 9, found 2`, `conflict: expected 0, found 2`, `conflict: expected 7, found 2`, `conflict: expected 5, found 2`로 시작. 저장소 바이트·감사 줄 수 불변, `in.csv.rejected.csv` 없음 ④ stdout `2` | pytest subprocess | 구현 전 RED |
| S-10 | regression | C-3 | 구현 완료 worktree, `tests/test_basic.py`가 main 대비 변경 없음 | `git diff --exit-code main -- tests/test_basic.py` 후 `python -m pytest -q tests/test_basic.py` | diff exit 0, pytest 2 passed | worktree shell | 구현 후 |
| S-11 | check | C-1 | 구현 완료 worktree | `stockctl/*.py`의 `import`/`from` 문 모듈 목록을 수집해 `sys.stdlib_module_names` 또는 패키지 내부 상대 import인지 확인 | 비표준 외부 모듈 0건 | python 스크립트 | 구현 후 |
| S-12 | check | AC-9 | W-2 완료 | `docs/CLI.md` Read | `transfer`, `history`, `import-csv`, `version`, `--expect-version`, `--location`, `insufficient:`, `invalid:`, `conflict:`, `.audit.jsonl`, `.rejected.csv`, 종료 코드 3·4·5가 모두 기술되고 PLAN Decisions and contracts와 모순 없음 | 문서 검토 | 구현 후 |
