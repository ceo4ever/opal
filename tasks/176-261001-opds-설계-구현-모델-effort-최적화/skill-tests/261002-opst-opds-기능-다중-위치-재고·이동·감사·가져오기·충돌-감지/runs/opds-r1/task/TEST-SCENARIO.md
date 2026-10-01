---
template: sdlc-v2
---
# TEST-SCENARIO: stockctl 다중 위치 재고·이동·감사·가져오기·충돌 감지

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: worktree 루트에서 Python 3 + pytest. CLI는 `python -m stockctl --store <tmp>/s.json ...`를 subprocess로 호출한다(`tests/test_basic.py`와 같은 방식). 감사 로그 경로는 `<tmp>/s.json.audit.jsonl`.
- 공통 데이터: 시나리오마다 pytest `tmp_path`에 새 저장소를 만든다. 구형 저장소 fixture는 `{"items": {"A1": {"name": "Apple", "qty": 5, "location": "WH1"}, "B2": {"name": "Bolt", "qty": 0, "location": "MAIN"}}}`(version 키 없음).
- "바이트 불변" 판정: 명령 전후 저장소 파일(및 존재 시 감사 파일)의 bytes를 비교하고, 저장소 디렉터리에 `.tmp` 잔여 파일이 없음을 확인한다.
- 대역 사용과 한계: 사용하지 않음(실제 CLI 프로세스와 실제 파일 시스템 사용).
- 실행 조건: 자동 실행. 사람 협업 없음.
- 병렬 그룹: S-1, S-2, S-3, S-4, S-5, S-6, S-7, S-8, S-9, S-10, S-11

## Scenarios

| ID | 유형 | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|---|
| S-1 | integration | AC-1, AC-8, C-3 | 구형 fixture 저장소(version 없음) | ① `version` ② `list` ③ `add C3 --qty 1` ④ 저장소 JSON 로드 | ① stdout `0` ② stdout 정확히 `A1\tApple\tWH1\t5\n`(B2는 0이라 미출력) ③ exit 0 ④ 최상위 `version == 1`, `items.A1 == {"name": "Apple", "locations": {"WH1": 5}}`, `items.B2 == {"name": "Bolt", "locations": {"MAIN": 0}}`, `items.C3 == {"name": "C3", "locations": {"MAIN": 1}}`, 품목에 `qty`·`location` 키 없음, `.tmp` 잔여 없음 | pytest subprocess + JSON 파일 검사 | 구현 전 RED |
| S-2 | integration | AC-1, AC-8 | 빈 저장소 경로(파일 없음) | `version` → `add A1 --qty 5` → `remove A1 --qty 2` → `transfer A1 --from MAIN --to WH1 --qty 1` → (sku,name,location,qty 유효 2행 CSV) `import-csv` → 각 명령 뒤 `version` | 최초 `0`, 이후 성공 명령마다 정확히 `1`,`2`,`3`,`4`(import-csv는 2행이어도 +1), 저장소 JSON `version`과 `version` 출력이 일치 | pytest subprocess | 구현 전 RED |
| S-3 | integration | AC-2 | 빈 저장소 | ① `add A1 --qty 5 --name Apple` ② `add A1 --qty 3 --location WH1` ③ `remove A1 --qty 2 --location WH1` ④ `remove A1 --qty 4 --location WH1` ⑤ `remove ZZ --qty 1` ⑥ `remove A1 --qty 1` | ① exit 0, stdout `A1 qty=5` ② exit 0, stdout `A1 qty=3` ③ exit 0, stdout `A1 qty=1` ④ exit 2, stderr가 `insufficient:`로 시작(MAIN에 5가 있어도 WH1 기준 판정), 저장소 bytes 불변 ⑤ exit 1, 저장소 bytes 불변 ⑥ 기본 위치 MAIN에서 차감, exit 0, stdout `A1 qty=4` | pytest subprocess | 구현 전 RED |
| S-4 | integration | AC-3 | `add B1 --qty 2 --location WH2 --name Bolt`, `add A1 --qty 1 --location WH1 --name Apple`, `add A1 --qty 4`, `add A1 --qty 3 --location AUX`, `remove A1 --qty 3 --location AUX` | `list` | stdout 정확히 `A1\tApple\tMAIN\t4\nA1\tApple\tWH1\t1\nB1\tBolt\tWH2\t2\n`(SKU→LOC 오름차순, 수량 0인 AUX 미출력), exit 0 | pytest subprocess | 구현 전 RED |
| S-5 | integration | AC-4 | `add A1 --qty 5 --name Apple` | `transfer A1 --from MAIN --to WH1 --qty 3` 후 `list` | transfer exit 0, stdout 정확히 `A1 MAIN->WH1 3\n`; list에 `A1\tApple\tMAIN\t2`, `A1\tApple\tWH1\t3` | pytest subprocess | 구현 전 RED |
| S-6 | integration | AC-4, H-1 | `add A1 --qty 2`(감사 파일 1줄 존재) | ① `transfer ZZ --from MAIN --to WH1 --qty 1` ② `transfer A1 --from MAIN --to WH1 --qty 3` ③ `transfer A1 --from MAIN --to WH1 --qty 0` ④ `transfer A1 --from MAIN --to WH1 --qty -3` ⑤ `transfer A1 --from MAIN --to MAIN --qty 1` | ① exit 1 ② exit 2, stderr `insufficient:` 시작 ③④⑤ exit 5, stderr `invalid:` 시작(④는 argparse 오류 exit 2가 아님). 모든 경우 저장소·감사 파일 bytes 불변, `.tmp` 잔여 없음 | pytest subprocess | 구현 전 RED |
| S-7 | integration | AC-5 | 빈 저장소 | `add A1 --qty 5` → `remove A1 --qty 2` → `transfer A1 --from MAIN --to WH1 --qty 1` → `remove A1 --qty 99`(실패) → `add A1 --qty 1 --expect-version 99`(실패) → 감사 파일 줄 단위 `json.loads` | 정확히 3줄. 각 줄 키 집합 `{ts, op, sku, changes}`, `datetime.fromisoformat(ts)` 성공. 순서대로 `op/changes` = `add/{"MAIN": 5}`, `remove/{"MAIN": -2}`, `transfer/{"MAIN": -1, "WH1": 1}`, 모두 `sku == "A1"`. 실패 2건은 줄을 추가하지 않음 | pytest subprocess + JSONL 파싱 | 구현 전 RED |
| S-8 | integration | AC-6 | S-7과 같은 성공 3건 + `add B1 --qty 1` | ① `history A1` ② `history B9` ③ 감사 파일 없는 새 저장소에서 `history A1` | ① exit 0, 3줄이 최신순 `TS\ttransfer\tMAIN:-1,WH1:+1`, `TS\tremove\tMAIN:-2`, `TS\tadd\tMAIN:+5`(TS는 각 감사 줄의 `ts` 값 그대로), B1 기록 미포함 ② exit 0, stdout 빈 문자열 ③ exit 0, stdout 빈 문자열 | pytest subprocess | 구현 전 RED |
| S-9 | integration | AC-5, AC-7 | 저장소에 `add A1 --qty 1 --name Apple`(version 1). CSV `in.csv`: 헤더 `sku,name,location,qty`, 행 `A1,Apple,WH1,4` / `A1,Apple,WH1,2` / `B2,Bolt,MAIN,3` / `C3,Cog,MAIN,0` / `D4,,MAIN,2` / `E5,Elf,MAIN,x` / `F6,Fan,MAIN,-1` | `import-csv <tmp>/in.csv` | exit 3, stdout `applied 3, rejected 4`. 저장소 `version == 2`(한 번 저장), `A1.locations == {"MAIN": 1, "WH1": 6}`, `B2 == {"name": "Bolt", "locations": {"MAIN": 3}}`, C3·D4·E5·F6 미등록. `<tmp>/in.csv.rejected.csv`를 `csv.DictReader`로 읽으면 헤더 `sku,name,location,qty,reason`, 4행이 원래 값(C3/D4/E5/F6) 그대로이고 `reason`이 모두 비어 있지 않음. 감사 파일에 추가된 import 줄은 SKU당 1줄: A1 `{"WH1": 6}`, B2 `{"MAIN": 3}`, `op == "import"` | pytest subprocess + CSV/JSONL 파싱 | 구현 전 RED |
| S-10 | integration | AC-7 | 빈 저장소, 유효 2행 CSV `ok.csv`, 그리고 헤더만 다른 CSV `bad.csv`(헤더 `sku,title,location,qty`, 1행) | ① `import-csv ok.csv` ② `import-csv bad.csv` | ① exit 0, stdout `applied 2, rejected 0`, `ok.csv.rejected.csv` 파일이 존재하지 않음 ② exit 3, stdout `applied 0, rejected 1`, `bad.csv.rejected.csv` 1행에 reason 존재, 저장소 version 변화 없음(① 후 값 유지) | pytest subprocess | 구현 전 RED |
| S-11 | integration | AC-8 | `add A1 --qty 5`(version 1), CSV 유효 1행 | ① `add A1 --qty 1 --expect-version 0` ② `remove A1 --qty 1 --expect-version 7` ③ `transfer A1 --from MAIN --to WH1 --qty 1 --expect-version 2` ④ `import-csv in.csv --expect-version 3` ⑤ `add A1 --qty 1 --expect-version 1` | ①~④ 각각 exit 4, stderr 정확히 `conflict: expected {V}, found 1`(V=0,7,2,3), 저장소·감사 파일 bytes 불변, ④는 rejected 파일 미생성 ⑤ exit 0, `version` 출력 `2` | pytest subprocess | 구현 전 RED |
| S-12 | check | C-2 | 구현 완료 worktree | `git diff --exit-code main -- tests/test_basic.py` 후 `python -m pytest tests/test_basic.py -q` | diff 없음(exit 0), 기존 2개 테스트 PASS | git + pytest | 구현 후 |
| S-13 | check | C-1, C-3 | 구현 완료 worktree | `stockctl/*.py`의 모든 `import`/`from ... import` 최상위 모듈을 `sys.stdlib_module_names`와 패키지 자체(`stockctl`, 상대 import)에 대조하고, `stockctl/store.py`에서 `.tmp` 기록 후 `os.replace` 호출 확인 | 표준 라이브러리 외 모듈 0건, 저장 경로가 임시 파일 + `os.replace`를 사용 | 정적 검사(python 스크립트·grep) | 구현 후 |
| S-14 | check | C-4 | 구현 완료 worktree | `docs/CLI.md` Read | add/remove/list/transfer/history/import-csv/version 명령, `--location`·`--expect-version` 옵션, 종료 코드 0~5, 출력 형식(`SKU\tNAME\tLOC\tQTY`, `SKU A->B N`, `applied N, rejected M`, history 줄 형식, `conflict:` 메시지), 저장 형식·구형 호환, 감사 로그 경로·필드가 PLAN Decisions and contracts와 일치 | 문서 검토 | 구현 후 |
