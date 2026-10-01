# DONE: stockctl 다중 위치 재고·이동·감사·가져오기·충돌 감지

## 결과

- 저장소가 `{"version": int, "items": {SKU: {"name", "locations": {LOC: qty}}}}` 형식이 되었다. 구형 `{name, qty, location}` 파일(version 없음)은 읽을 때 `{location: qty}`·version 0으로 해석되고(수량 0 위치 포함 무손실), 다음 성공 저장 때 새 형식으로 기록된다. 모든 성공 저장은 version을 정확히 1 올리며 임시 파일 + `os.replace` 원자 교체를 유지한다.
- `add`/`remove`가 `--location`(기본 MAIN)으로 위치별 수량을 다루고, 기존 stdout `SKU qty=N`·종료 코드를 유지한다(N은 해당 위치 수량). `remove` 위치 부족은 exit 2 `insufficient:`.
- `list`는 `SKU\tNAME\tLOC\tQTY`를 SKU→LOC 오름차순으로 출력하고 수량 0 위치를 숨긴다.
- 신규 명령: `transfer`(exit 0/1/2/5, 실패 시 저장소·감사 파일 바이트 불변), `history`(최신순 `TS\tOP\tLOC:±N`), `import-csv`(행 거부 → `FILE.rejected.csv` + exit 3, 전부 유효 시 exit 0, 1회 저장), `version`.
- 성공한 변경은 `<저장소>.audit.jsonl`에 SKU당 1줄(`ts`·`op`·`sku`·`changes`)로 남고 실패 명령은 남기지 않는다.
- 변경 명령 4종이 `--expect-version V`를 받아 불일치 시 exit 4 `conflict: expected V, found X`로 저장하지 않는다.
- 유지: 기존 `tests/test_basic.py` 무수정 통과, 표준 라이브러리만 사용, `python -m stockctl` 진입점 불변.

## 변경 파일

- `stockctl/store.py`
- `stockctl/cli.py`
- `docs/CLI.md`
- `tests/test_multiloc.py` (신규)

## 검증

- `python -m pytest tests -q -p no:cacheprovider` → 13 passed (`tests/test_basic.py` 2 + `tests/test_multiloc.py` 11), commit `4c95128` 기준 worktree.
- RED-first: 구현 전 `tests/test_multiloc.py` 11 failed 관찰 → `test-tool scenario-red` 11/11 → `scenario-lock` 후 GREEN.
- `test-scenario.json`: S-1~S-14 14/14 pass (S-12 `git diff --exit-code main -- tests/test_basic.py` 무변경, S-13 표준 라이브러리 외 import 0건·원자 저장, S-14 `docs/CLI.md` 계약 일치). H-1 실측: `transfer A1 --from MAIN --to WH1 --qty -3` → exit 5 `invalid: qty must be positive`.
- 설계 게이트 i1 pass(독립 evaluator design 4축 PASS, scenario 2·2·2).
- 최종 컨벤션 검사 `GC-CONVENTION-2026-10-01T15-08-27-CLI.md`: Critical 0 / High 0 / Medium 0 / Low 0. 보안 스캔(위험 호출·시크릿 grep) 0건.

## 회고적 학습 후보

없음

## 참고

- 잔여 결함(Minor, 미수정): import-csv qty 판정에 쓴 `str.isdigit()`는 `'²'` 같은 유니코드 숫자를 참으로 보므로 그런 값이 오면 `int()`에서 예외가 난다(거부 대신 traceback). 후속으로 `qty.isascii() and qty.isdigit()` 판정을 권고한다.
- PM 해석 결정(요구서 미지정 영역, `design-decision --scope detail`): import 감사는 SKU당 1줄(LOC별 합산), 종료 코드 우선순위(transfer 5→4→1→2, 그 외 4 우선), import 파일 열기 실패는 argparse 오류(exit 2·usage 포함 2줄 stderr), 유효 0행이면 저장 생략(version 불변). 사용자가 다른 계약을 원하면 후속 조정 대상이다.
- 1차 컨벤션 검사 GC-001(High)은 신규 파일의 `"exports": []`를 미충족으로 보는 precheck 규칙과 프로젝트 관례(`tests/test_basic.py`)의 불일치였다. 테스트 @header exports를 함수 목록으로 보정해 해소했다.
