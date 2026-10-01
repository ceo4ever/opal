---
template: sdlc-v2
---
# TASK: stockctl 다중 위치 재고·이동·감사·가져오기·충돌 감지

## Problem
stockctl은 품목마다 위치 1개만 가진다(`docs/CLI.md`, `stockctl/store.py:6` "sku → {name, qty, location} 단일 위치 구조"). 창고 여러 곳을 운영하면서 위치 간 이동, 변경 추적, 대량 등록, 동시 수정 사고 방지가 필요해졌지만 현재 CLI(`stockctl/cli.py:16-48`)는 add/remove/list만 제공하고 위치별 수량·이력·일괄 등록·버전 비교를 지원하지 않는다. 요구 원문: 사용자 요구서(프로젝트 외부 `opds-r1/REQUEST.md`) — 요구서의 요구를 TASK 요구사항으로 그대로 사용한다(사용자 지시).

## Proposed outcome
- 저장소는 품목별로 여러 위치의 수량을 담고 최상위에 정수 `version`을 가지며, 기존 단일 위치 파일도 데이터 손실 없이 읽혀 다음 성공 저장 때 새 형식으로 기록된다.
- 사용자는 위치를 지정해 add/remove 하고, 품목·위치 조합 단위로 list 하며, 위치 간 transfer 할 수 있다.
- 성공한 변경은 감사 로그에 SKU별로 남고 `history SKU`로 최신순 조회된다.
- CSV 파일로 여러 품목을 한 번에 등록하고 거부된 행은 사유와 함께 별도 파일로 받는다.
- 변경 명령은 기대 version을 받아 다른 사람이 먼저 바꾼 저장소를 덮어쓰지 않으며, 현재 version을 조회할 수 있다.

## Affected users and systems
- 사용자: 여러 창고 위치의 재고를 관리하는 stockctl CLI 사용자.
- 시스템: `stockctl/`(CLI·저장소), `tests/`, `docs/CLI.md`.
- 포함: 요구서의 데이터·명령 계약 1~8 전부.
- 제외: 외부 패키지, 동시 프로세스 잠금(파일 락), 감사 로그 회전·정리, 기존 감사 로그 형식 마이그레이션(신규 파일).

## Constraints
- C-1: 표준 라이브러리만 사용한다(`.opal/AGENT.md` §금지사항, `docs/CONVENTIONS.md`).
- C-2: 기존 테스트 `tests/test_basic.py`는 수정 없이 계속 통과해야 한다.
- C-3: 저장은 임시 파일 기록 후 원자 교체를 유지한다(`docs/CONVENTIONS.md`: "저장은 임시 파일 기록 후 `os.replace`로 원자 교체한다").
- C-4: `docs/CLI.md`를 새 명령 계약(명령·옵션·종료 코드·출력 형식)으로 갱신한다.

## Acceptance criteria
- AC-1: 저장소 형식 — 저장된 품목은 `items[sku] = {"name": ..., "locations": {LOC: qty}}` 구조이고 최상위에 정수 `version`이 있다. 품목이 `{name, qty, location}`이고 `version`이 없는 기존 파일은 `{location: qty}`, version 0으로 해석되며, 다음 성공 저장 때 새 형식으로 기록되고 기존 품목·수량·이름이 하나도 사라지지 않는다. 모든 성공 저장은 `version`을 정확히 1 올린다.
- AC-2: `add SKU --qty N [--name NAME] [--location LOC]`는 LOC(기본 MAIN)에 수량을 더하고 기존 stdout 형식·종료 코드를 유지한다. `remove SKU --qty N [--location LOC]`는 LOC(기본 MAIN)에서 차감하며, 미등록 SKU는 exit 1, 해당 위치 수량 부족은 exit 2이고 stderr가 `insufficient:`로 시작한다.
- AC-3: `list`는 품목·위치 조합마다 `SKU\tNAME\tLOC\tQTY` 한 줄을 SKU 다음 LOC 오름차순으로 출력하고 수량 0인 위치는 출력하지 않는다.
- AC-4: `transfer SKU --from A --to B --qty N`은 A에서 B로 수량을 옮기고 성공 시 stdout `SKU A->B N`, exit 0이다. 미등록 SKU exit 1, A의 수량 부족 exit 2(stderr `insufficient:` 시작), qty ≤ 0 또는 A == B는 exit 5(stderr `invalid:` 시작)이며, 실패 시 저장소 파일은 바이트 단위로 변하지 않는다.
- AC-5: 성공한 변경 명령(add, remove, transfer, import-csv로 반영된 행)은 SKU별로 `<저장소 경로>.audit.jsonl`에 JSON 한 줄(`ts` ISO 8601, `op` add|remove|transfer|import, `sku`, `changes` {LOC: 부호 있는 증감})을 추가하고, 실패한 명령은 감사 로그에 아무것도 남기지 않는다.
- AC-6: `history SKU`는 그 SKU의 감사 기록을 최신순으로 `TS\tOP\tLOC:DELTA,...`(changes는 LOC 오름차순, DELTA는 부호 포함 예 `+5`, `-3`) 한 줄씩 출력하고, 기록이 없으면 출력 없이 exit 0이다.
- AC-7: `import-csv FILE`은 헤더 `sku,name,location,qty`의 행 중 qty가 양의 정수가 아니거나 필드가 빈 행을 거부하고, 유효 행을 한 번의 저장으로 모두 반영(add와 같은 의미)한 뒤 stdout `applied N, rejected M`을 출력한다. M > 0이면 `FILE.rejected.csv`에 원래 열 + `reason` 열로 거부 행을 쓰고 exit 3, M = 0이면 그 파일을 만들지 않고 exit 0이다.
- AC-8: 변경 명령(add, remove, transfer, import-csv)은 `--expect-version V`를 받고, 현재 version이 V와 다르면 exit 4, stderr `conflict: expected V, found X`이며 저장하지 않는다. `version` 명령은 현재 version 정수 한 줄을 출력한다.
