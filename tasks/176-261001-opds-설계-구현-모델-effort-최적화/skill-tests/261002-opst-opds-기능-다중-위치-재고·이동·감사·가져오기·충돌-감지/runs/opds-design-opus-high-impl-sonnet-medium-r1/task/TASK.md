---
template: sdlc-v2
---
# TASK: stockctl 다중 위치 재고·이동·감사·가져오기·충돌 감지

## Problem
현재 stockctl은 품목마다 위치를 1개만 가진다(`docs/CLI.md` 표, `stockctl/store.py:6` "sku → {name, qty, location} 단일 위치 구조"). 창고 여러 곳을 운영하면서 위치 간 이동, 변경 추적, 대량 등록, 동시 수정 사고 방지가 필요해졌지만 현재 명령(add/remove/list)으로는 이를 할 수 없다(`stockctl/cli.py:50-66`). 요구 원문은 소유자 요구서 `REQUEST.md`이며 이 TASK의 요구사항으로 그대로 사용한다.

## Proposed outcome
- 품목이 위치별 수량(`locations: {LOC: qty}`)을 가지고 저장소에 정수 `version`이 있으며, 기존 단일 위치 파일도 데이터 손실 없이 계속 쓸 수 있다.
- add/remove가 위치를 지정해 동작하고, list가 품목·위치 조합별로 출력한다.
- transfer로 위치 간 이동, 감사 로그와 history로 변경 추적, import-csv로 대량 등록, `--expect-version`과 `version`으로 동시 수정 충돌 감지가 가능하다.
- `docs/CLI.md`가 새 계약을 기술한다.

## Affected users and systems
- 사용자: 여러 창고 위치의 재고를 CLI로 관리하는 운영자.
- 시스템: `stockctl/` 패키지(CLI·저장소), `tests/`, `docs/CLI.md`. 저장소 JSON 파일과 그 옆에 생기는 감사 로그 파일(`<저장소 경로>.audit.jsonl`), import-csv 거부 행 파일(`FILE.rejected.csv`).
- 제외: 표준 라이브러리 밖 의존성, 네트워크·DB 연동, 파일 잠금 기반 동시성 제어(충돌 감지는 version 비교로만 한다).

## Constraints
- C-1: 표준 라이브러리만 사용한다(`.opal/AGENT.md` §금지사항 "외부 패키지 추가 금지(표준 라이브러리만)", `docs/CONVENTIONS.md`).
- C-2: 기존 테스트 `tests/test_basic.py`는 수정 없이 계속 통과해야 한다.
- C-3: 저장은 임시 파일 기록 후 원자 교체를 유지한다(`docs/CONVENTIONS.md` "저장은 임시 파일 기록 후 `os.replace`로 원자 교체한다").
- C-4: `docs/CLI.md`를 새 계약으로 갱신한다.

## Acceptance criteria
- AC-1: 저장소 품목 구조가 `items[sku] = {"name": ..., "locations": {LOC: qty}}`이고 최상위에 정수 `version`이 있다. 기존 형식 파일(품목이 `{name, qty, location}`, `version` 없음)은 읽을 때 `{location: qty}`·version 0으로 해석되고, 다음 성공 저장 때 데이터 손실 없이 새 형식으로 기록된다.
- AC-2: 모든 성공 저장은 `version`을 정확히 1 올리고, `version` 명령은 현재 version 정수 한 줄을 출력한다.
- AC-3: `add SKU --qty N [--name NAME] [--location LOC]`은 LOC(기본 MAIN)에 수량을 추가하며 기존 출력·종료 코드를 유지한다. `remove SKU --qty N [--location LOC]`은 LOC(기본 MAIN)에서 차감하며, 미등록 SKU는 exit 1, 해당 위치 수량 부족은 exit 2이고 stderr가 `insufficient:`로 시작한다.
- AC-4: `list`는 품목·위치 조합마다 한 줄 `SKU\tNAME\tLOC\tQTY`를 SKU 다음 LOC 오름차순으로 출력하고, 수량 0인 위치는 출력하지 않는다.
- AC-5: `transfer SKU --from A --to B --qty N`은 A에서 B로 N을 이동하고 성공 시 stdout `SKU A->B N`, exit 0이다. 미등록 SKU exit 1, A 수량 부족 exit 2(stderr `insufficient:` 시작), qty ≤ 0 또는 A == B는 exit 5(stderr `invalid:` 시작)이며, 실패 시 저장소 파일은 바이트 단위로 변하지 않는다.
- AC-6: 성공한 변경 명령(add, remove, transfer, import-csv로 반영된 행)은 SKU별로 `<저장소 경로>.audit.jsonl`에 `ts`(ISO 8601)·`op`(add|remove|transfer|import)·`sku`·`changes`({LOC: 부호 있는 증감}) 필드의 JSON 한 줄을 추가하고, 실패한 명령은 아무것도 남기지 않는다.
- AC-7: `history SKU`는 그 SKU의 감사 기록을 최신순으로 한 줄씩 `TS\tOP\tLOC:DELTA,...`(changes는 LOC 오름차순, DELTA는 `+5`·`-3`처럼 부호 포함)로 출력하고, 기록이 없으면 출력 없이 exit 0이다.
- AC-8: `import-csv FILE`(헤더 `sku,name,location,qty`)은 qty가 양의 정수가 아니거나 필드가 빈 행을 거부하고, 유효 행을 한 번의 저장으로 add와 같은 의미로 모두 반영하며 stdout `applied N, rejected M`을 출력한다. M > 0이면 `FILE.rejected.csv`에 원래 열 + `reason` 열로 거부 행을 쓰고 exit 3, M = 0이면 그 파일을 만들지 않고 exit 0이다.
- AC-9: 변경 명령(add, remove, transfer, import-csv)은 `--expect-version V`를 받으며, 현재 version이 V와 다르면 exit 4, stderr `conflict: expected V, found X`이고 저장하지 않는다.
