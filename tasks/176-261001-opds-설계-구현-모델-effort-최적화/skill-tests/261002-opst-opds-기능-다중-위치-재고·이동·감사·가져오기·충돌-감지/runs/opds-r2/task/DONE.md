# DONE: stockctl 다중 위치 재고·이동·감사·가져오기·충돌 감지

## 결과

stockctl 저장소가 품목별 다중 위치(`items[sku] = {name, locations{LOC: qty}}`)와 최상위 정수 `version` 형식으로 바뀌었다. 기존 단일 위치 파일(`{name, qty, location}`, `version` 없음)은 읽을 때 `{location: qty}`·version 0으로 해석되고, 다음 성공 저장 때 데이터 손실 없이 새 형식으로 기록된다. 성공 저장마다 version이 1 오르며, 임시 파일 기록 후 `os.replace`로 원자 교체하는 방식은 그대로다.

- `add`·`remove`는 `--location`(기본 MAIN)을 받는다. 출력 `SKU qty=Q`와 종료 코드는 그대로이며, Q는 변경 후 해당 위치의 수량이다. `remove`는 미등록이면 exit 1, 그 위치 수량이 부족하면 exit 2(`insufficient:`)다.
- `list`는 품목·위치 조합마다 `SKU\tNAME\tLOC\tQTY` 한 줄을 SKU, LOC 순으로 정렬해 출력하고, 수량 0인 위치는 뺀다.
- 새 명령은 `transfer`(exit 0/1/2/5), `history SKU`(최신순), `import-csv FILE`(`applied N, rejected M`, 거부 행이 있으면 `FILE.rejected.csv` 생성 후 exit 3), `version`이다.
- 성공한 변경은 `<저장소>.audit.jsonl`에 SKU당 JSON 한 줄로 남는다.
- 변경 명령 4종은 `--expect-version V`를 받는다. 현재 version이 V와 다르면 exit 4와 `conflict: expected V, found X`를 내고 아무것도 쓰지 않는다.
- 실패한 명령은 저장소·감사·거부 파일을 바이트 단위로 바꾸지 않는다. 실패 조건이 겹치면 5→4→1→2 순서로 첫 조건 하나만 보고한다.

유지한 것: 저장소 경로 우선순위(`--store` > `STOCKCTL_STORE` > `stock.json`), add의 qty 값 무검증, 기존 `tests/test_basic.py`(수정 없음, 통과). 표준 라이브러리만 사용한다.

## 변경 파일

- `stockctl/store.py`
- `stockctl/audit.py` (신규)
- `stockctl/cli.py`
- `tests/test_multiloc.py` (신규)
- `docs/CLI.md`

## 검증

- `python3 -m pytest tests/ -q` → 12 passed (test_basic 2 + test_multiloc 10), 대상 SHA `305c693`
- RED-first: 구현 전 `tests/test_multiloc.py` 10개 실패를 관찰해 `test-tool scenario-red` 10건 기록, `scenario-lock` 이후 GREEN
- TEST(독립 opal-test-agent): `test-tool scenario-status` 13/13 pass, fail·blocked·awaiting_human 0
- `git diff main -- tests/test_basic.py` → 빈 출력
- 보안 검사: eval·exec·`shell=True`·pickle·하드코딩 시크릿 0건
- 컨벤션 최종 검사 `run/GC-CONVENTION-20261002-0005.md`: Critical·High 0, Low 1(유지 — 참고 참조)
- 설계 게이트 i1 pass (design 4축 PASS, scenario 2·2·2)

## 회고적 학습 후보

없음

## 참고

- 컨벤션 GC-001(Low): `.rejected.csv`는 임시 파일 없이 직접 기록한다. 원자 교체 규칙의 대상은 재고 저장소로 보고 PLAN D-14대로 두었다.
- `--expect-version`에 정수가 아닌 값을 주면 argparse 기본 오류(exit 2)가 난다. 기존 `--qty`와 같은 동작이며 요구서 범위 밖이다.
- 요구서가 정하지 않은 해석 결정(D-4·D-5/D-6·D-10·D-12~D-14)은 `state.json` design decision과 AGENTIC-LOG #4에 기록했다.
- PLAN 체크포인트 `10c8ccb`에 lease 런타임 파일 `run/.runtime/owner.json`이 함께 추적되기 시작했다. 런타임 소유 파일이라 이번 태스크에서는 손대지 않았다.
- merge(`main`)는 사용자 승인 사항이며 수행하지 않았다.
