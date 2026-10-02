# DONE: stockctl 다중 위치 재고·이동·감사·가져오기·충돌 감지

## 결과

- 저장소가 `items[sku] = {"name", "locations": {LOC: qty}}`와 최상위 정수 `version` 형식이 되었다. 기존 단일 위치 파일(`{name, qty, location}`, version 없음)은 읽을 때 `{location: qty}`·version 0으로 해석하고 파일을 쓰지 않으며, 다음 성공 저장 때 손실 없이 새 형식으로 기록한다. 성공 저장마다 version +1, 저장은 `<경로>.tmp` + `os.replace` 원자 교체를 유지한다.
- `add`/`remove`가 `--location`(기본 MAIN)을 받고, `list`는 품목·위치 조합별 `SKU\tNAME\tLOC\tQTY`(SKU→LOC 오름차순, 0 수량 숨김)로 출력한다. 기존 `add` 출력 `SKU qty=Q`·종료 코드와 argparse 사용 오류 exit 2는 그대로다.
- 새 명령: `transfer`(exit 1/2/5, 실패 시 저장소 바이트 불변), `history`(감사 로그 최신순), `import-csv`(거부 행 `FILE.rejected.csv`, exit 3/0, 단일 저장), `version`. 변경 명령 4종은 `--expect-version V` 불일치 시 exit 4 `conflict: expected V, found X`로 아무것도 쓰지 않는다.
- 성공한 변경은 `<저장소>.audit.jsonl`에 SKU별 JSON 한 줄(`ts`·`op`·`sku`·`changes`)을 남기고, 실패는 아무것도 남기지 않는다.
- 요구서가 정하지 않은 경계는 PM 결정으로 고정했다(PLAN Decisions and contracts): 오류 판정 순서 5→4→1→2, `qty=Q`는 해당 위치 수량, import는 SKU별 합산 1줄, import 파일 읽기 실패·헤더 불일치는 exit 5 `invalid:`, 반영 0행이면 저장하지 않음.
- `docs/CLI.md`를 새 계약으로 갱신했다.

## 변경 파일

- `stockctl/store.py`
- `stockctl/cli.py`
- `docs/CLI.md`
- `tests/test_multiloc.py` (신규, RED-first 테스트 S-1~S-10)

## 검증

- RED: 구현 전 `python -m pytest tests/test_multiloc.py -q` → 10 failed(assertion/exit 불일치), `scenario-lock` locked=true.
- TEST(독립 opal-test-agent): `test-scenario.json` 14/14 pass(real-usage) — S-1~S-10 `python -m pytest tests/test_multiloc.py -v` 10 passed, S-11 `git diff --exit-code main -- tests/test_basic.py` 무수정 + 2 passed, S-12 표준 라이브러리 외 import 0, S-13 `os.replace` 원자 교체, S-14 `docs/CLI.md` 계약 대조.
- 전체 회귀(마지막 수정 기준): `python -m pytest tests -q` → 12 passed.
- 보안 검사: 위험 호출·시크릿 0건. 컨벤션 최종 검사 `GC-CONVENTION-2026-10-01T15-06-15-CLI.md` Critical 0 / High 0 / Medium 1(advisory, 오탐 판단 유지).

## 회고적 학습 후보

없음

## 참고

- 컨벤션 Medium GC-001(`docs/CLI.md` "### history 출력"을 이력 절로 감지)은 history 명령 기능 설명이라 유지했다.
- 기존 `tests/test_basic.py`·`stockctl/__main__.py`의 @header `"exports": []`는 같은 기계 검사에서 High로 잡힐 수 있으나 범위 밖(C-2)이라 손대지 않았다.
- `.gitignore`에 `stock.json`·`*.audit.jsonl`·`*.rejected.csv`가 없다(TEST 관찰, 요구 범위 밖).
- 로컬 개선 후보 "stockctl CLI 변경 PLAN에 argparse 사용 오류 기본 exit 2 유지를 명시"는 `improve-tool record --scope local`이 worktree에서 `memory-tool delegation failed: invalid_args`로 실패해 이 문서와 AGENTIC-LOG에만 기록했다(FW 개선 후보로 별도 접수).
