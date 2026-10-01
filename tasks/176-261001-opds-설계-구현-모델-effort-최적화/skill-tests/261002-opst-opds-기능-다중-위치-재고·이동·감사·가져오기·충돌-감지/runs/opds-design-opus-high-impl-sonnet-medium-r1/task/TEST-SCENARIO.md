---
template: sdlc-v2
---
# TEST-SCENARIO: stockctl 다중 위치 재고·이동·감사·가져오기·충돌 감지

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: worktree `feat/OP-TASK-001` 루트에서 Python 3 + pytest. CLI는 `python -m stockctl --store <tmp>/s.json ...` subprocess로 호출한다(`docs/CONVENTIONS.md`).
- 공통 데이터: 시나리오마다 pytest `tmp_path`에 새 저장소를 만든다. 레거시 파일은 `{"items": {"A1": {"name": "Apple", "qty": 7, "location": "WH1"}}}`를 직접 써서 준비한다. 감사 로그는 `<tmp>/s.json.audit.jsonl`이다.
- 자동화 위치: S-1~S-10은 `opal-test-agent`가 red mode로 `tests/test_multiloc.py`에 작성한다. 바이트 불변 판정은 명령 전후 `Path.read_bytes()` 비교로 한다.
- 대역 사용과 한계: 사용하지 않음(실제 CLI 프로세스·실제 파일 시스템).
- 실행 조건: 자동 실행.
- 병렬 그룹: S-1, S-2, S-3, S-4, S-5, S-6, S-7, S-8, S-9, S-10

## Scenarios

| ID | 유형 | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|---|
| S-1 | integration | AC-1, AC-2 | 빈 저장소 | `add A1 --qty 5 --name Apple` → `add A1 --qty 3 --location WH2` → `version` | 저장소 JSON이 `items.A1 == {"name": "Apple", "locations": {"MAIN": 5, "WH2": 3}}`, 최상위 `version == 2`(int), 품목에 `qty`·`location` 키 없음; `version` stdout `2\n`, exit 0; 저장 뒤 `s.json.tmp` 잔존 없음 | pytest subprocess | 구현 전 RED |
| S-2 | integration | AC-1, AC-2 | 레거시 파일(A1 Apple qty 7 WH1, version 없음) | `list`·`version` 실행 후 파일 바이트 비교 → `add A1 --qty 1` | `list` stdout `A1\tApple\tWH1\t7`, `version` stdout `0`, 두 명령 뒤 파일 바이트 불변; add 뒤 JSON이 `items.A1 == {"name": "Apple", "locations": {"WH1": 7, "MAIN": 1}}`, `version == 1` | pytest subprocess | 구현 전 RED |
| S-3 | integration | AC-3 | 빈 저장소 | `add A1 --qty 5` → `add A1 --qty 4 --location WH2` → `remove A1 --qty 2` → `remove A1 --qty 1 --location WH2` → `remove ZZ --qty 1` → `remove A1 --qty 4` | stdout 순서대로 `A1 qty=5`, `A1 qty=4`, `A1 qty=3`, `A1 qty=3`(모두 exit 0); 미등록 `ZZ` exit 1; MAIN 3 < 4는 합계 6이어도 exit 2이고 stderr가 `insufficient:`로 시작 | pytest subprocess | 구현 전 RED |
| S-4 | integration | AC-4 | 빈 저장소 | `add B1 --qty 2 --name Banana` → `add A1 --qty 1 --name Apple --location WH2` → `add A1 --qty 3` → `add A1 --qty 2 --location AAA` → `remove A1 --qty 2 --location AAA` → `list` | stdout 줄이 정확히 `A1\tApple\tMAIN\t3`, `A1\tApple\tWH2\t1`, `B1\tBanana\tMAIN\t2` 순서이며 수량 0인 `AAA` 줄 없음, exit 0 | pytest subprocess | 구현 전 RED |
| S-5 | integration | AC-5, AC-2 | A1 MAIN 5, version 1 | `transfer A1 --from MAIN --to WH2 --qty 2` → `version` | stdout `A1 MAIN->WH2 2`, exit 0; JSON `locations == {"MAIN": 3, "WH2": 2}`; `version` stdout `2` | pytest subprocess | 구현 전 RED |
| S-6 | integration | AC-5, AC-6 | A1 MAIN 5 저장소와 감사 로그 바이트 기록 | `transfer ZZ --from MAIN --to WH2 --qty 1`, `transfer A1 --from MAIN --to WH2 --qty 6`, `transfer A1 --from WH9 --to MAIN --qty 1`, `transfer A1 --from MAIN --to WH2 --qty 0`, `--qty -1`, `transfer A1 --from MAIN --to MAIN --qty 1` | 종료 코드 순서대로 1, 2, 2, 5, 5, 5; exit 2 stderr는 `insufficient:`, exit 5 stderr는 `invalid:`로 시작; 매 명령 뒤 저장소 파일 바이트와 감사 로그 바이트 불변 | pytest subprocess | 구현 전 RED |
| S-7 | integration | AC-6, AC-7 | 빈 저장소 | `add A1 --qty 5` → `remove A1 --qty 1` → `transfer A1 --from MAIN --to WH2 --qty 2` → 실패 명령 `remove A1 --qty 99` → 감사 로그 읽기 → `history A1` → `history ZZ` | 감사 로그 정확히 3줄, 각 줄 JSON 키 집합 `{ts, op, sku, changes}`, `ts`는 `datetime.fromisoformat` 파싱 가능, op 순서 `add`·`remove`·`transfer`, changes 순서대로 `{"MAIN": 5}`, `{"MAIN": -1}`, `{"MAIN": -2, "WH2": 2}`; `history A1` stdout 3줄이 최신순 `TS\ttransfer\tMAIN:-2,WH2:+2`, `TS\tremove\tMAIN:-1`, `TS\tadd\tMAIN:+5`(TS는 감사 로그 ts와 동일); `history ZZ` stdout 빈 문자열, exit 0 | pytest subprocess | 구현 전 RED |
| S-8 | integration | AC-8, AC-6, AC-2 | 저장소 version 0(빈 저장소), CSV 헤더 `sku,name,location,qty` + 행 `A1,Apple,MAIN,5` / `A1,Apple,WH2,2` / `B1,Banana,MAIN,0` / `C1,Cherry,MAIN,abc` / `D1,,MAIN,1` / `E1,Egg,MAIN,-3` | `import-csv <tmp>/in.csv` → `version` → `history A1` | stdout `applied 2, rejected 4`, exit 3; `version` stdout `1`(저장 1회); A1 locations `{"MAIN": 5, "WH2": 2}`, B1~E1 미등록; `<tmp>/in.csv.rejected.csv` 헤더 `sku,name,location,qty,reason`과 거부 4행이 원래 값과 비어 있지 않은 reason을 가짐; 감사 로그 op `import`, sku `A1` 1줄 changes `{"MAIN": 5, "WH2": 2}`; `history A1` 1줄 `TS\timport\tMAIN:+5,WH2:+2` | pytest subprocess | 구현 전 RED |
| S-9 | integration | AC-8 | 저장소에 A1 Apple MAIN 1, CSV에 유효 행 `A1,Apricot,WH2,3` / `B1,Banana,MAIN,4`만 | `import-csv <tmp>/ok.csv` → `list` | stdout `applied 2, rejected 0`, exit 0; `<tmp>/ok.csv.rejected.csv` 파일 없음; list가 `A1\tApricot\tMAIN\t1`, `A1\tApricot\tWH2\t3`, `B1\tBanana\tMAIN\t4` | pytest subprocess | 구현 전 RED |
| S-10 | integration | AC-9 | A1 MAIN 5, version 1 | 성공: `add A1 --qty 1 --expect-version 1`; 실패: `add`·`remove A1 --qty 1`·`transfer A1 --from MAIN --to WH2 --qty 1`·`import-csv <유효 CSV>` 각각에 `--expect-version 1`(현재 2) | 성공 명령 exit 0 후 version 2; 실패 4건 모두 exit 4, stderr 첫 줄이 정확히 `conflict: expected 1, found 2`; 실패 뒤 저장소·감사 로그 바이트 불변, `.rejected.csv` 생성 없음 | pytest subprocess | 구현 전 RED |
| S-11 | regression | C-2 | 구현 완료 worktree | `git diff --exit-code main -- tests/test_basic.py` 후 `python -m pytest tests/test_basic.py -q` | diff exit 0(파일 무수정), pytest 2 passed | pytest + git | 구현 후 |
| S-12 | check | C-1 | 구현 완료 | `stockctl/*.py`의 모든 최상위 import 모듈명을 `sys.stdlib_module_names` 또는 패키지 내부 상대 import와 대조 | 표준 라이브러리 밖 import 0건 | Python 스크립트 정적 검사 | 구현 후 |
| S-13 | check | C-3 | 구현 완료 | `stockctl/store.py`에서 저장 경로 확인: 임시 파일 기록 후 `os.replace` 호출 | `save`가 임시 파일에 쓰고 `os.replace`로 교체하며 저장소 파일을 직접 `write_text`/`open(..., "w")`로 쓰는 경로 없음 | 소스 검사 | 구현 후 |
| S-14 | check | C-4 | 구현 완료 | `docs/CLI.md` 내용 확인 | add·remove·list·transfer·history·import-csv·version 7개 명령, `--expect-version`, 종료 코드 1·2·3·4·5, `conflict:`·`insufficient:`·`invalid:` 접두사, `.audit.jsonl`·`.rejected.csv` 형식, 저장소 `locations`·`version` 형식이 PLAN Decisions and contracts와 일치 | 문서 검사 | 구현 후 |
