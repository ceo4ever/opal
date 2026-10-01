---
template: sdlc-v2
---
# TASK: stockctl 다중 위치 재고·이동·감사·가져오기·충돌 감지

## Problem
현재 stockctl은 품목마다 위치 1개만 가진다(`docs/CLI.md`). 창고 여러 곳을 운영하면서 위치 간 이동, 변경 추적, 대량 등록, 동시 수정 사고 방지가 필요해졌지만 지금 도구로는 이를 할 수 없다. 위치별 수량을 따로 관리할 수 없고, 누가 언제 무엇을 바꿨는지 남지 않으며, 대량 등록은 명령을 하나씩 반복해야 하고, 두 사람이 같은 저장소를 동시에 고치면 한쪽 변경이 조용히 덮어써진다.

## Proposed outcome
- 품목은 위치별 수량(`items[sku] = {"name": ..., "locations": {LOC: qty}}`)을 가지며 저장소 최상위에 정수 `version`이 있다. 기존 단일 위치 형식 파일도 데이터 손실 없이 읽히고 다음 성공 저장 때 새 형식으로 기록된다. 모든 성공 저장은 `version`을 1 올리고 임시 파일 후 원자 교체로 저장된다.
- `add`·`remove`는 위치(기본 MAIN)를 지정해 수량을 증감하고, `list`는 품목·위치 조합별로 출력한다.
- `transfer`로 위치 간 수량을 옮긴다.
- 성공한 변경은 SKU별 감사 로그(`<저장소 경로>.audit.jsonl`)에 남고, `history`로 SKU 변경 이력을 최신순으로 볼 수 있다.
- `import-csv`로 CSV의 여러 행을 한 번의 저장으로 등록하고 거부 행은 사유와 함께 별도 파일로 받는다.
- 변경 명령은 `--expect-version`으로 동시 수정 충돌을 감지해 저장을 거부하고, `version` 명령으로 현재 version을 확인한다.

## Affected users and systems
- 사용자: stockctl로 창고 재고를 관리하는 운영자.
- 시스템: `stockctl` CLI 패키지(명령·저장소), 저장소 JSON 파일과 새 감사 로그 파일 `<저장소 경로>.audit.jsonl`, `import-csv`가 만드는 `FILE.rejected.csv`, `tests/`, `docs/CLI.md`.
- 포함: 요구서(REQUEST.md)의 데이터 절과 명령 계약 1~8 전체.
- 제외: 다중 프로세스 파일 잠금, 감사 로그 회전·압축, 명령 계약 1~8에 없는 신규 명령·옵션.

## Constraints
- C-1: 표준 라이브러리만 사용한다(외부 패키지 추가 금지 — `.opal/AGENT.md` 금지사항, `docs/CONVENTIONS.md`).
- C-2: 기존 테스트 `tests/test_basic.py`는 수정 없이 계속 통과해야 한다.
- C-3: `docs/CLI.md`를 새 명령 계약(명령·옵션·종료 코드·출력 형식·부수 파일)으로 갱신한다.
- C-4: 프로젝트 코드 컨벤션(`docs/CONVENTIONS.md` — @header, 임시 파일 후 `os.replace` 원자 저장, stderr 한 줄 오류, pytest + `python -m stockctl`)을 따른다.

## Acceptance criteria
- AC-1: 저장소는 `items[sku] = {"name": ..., "locations": {LOC: qty}}` 구조와 최상위 정수 `version`을 가진다. 기존 형식(품목 `{name, qty, location}`, `version` 없음) 파일은 `{location: qty}`, version 0으로 해석되어 모든 품목·이름·수량이 보존되고, 다음 성공 저장 때 새 형식으로 기록된다. 모든 성공 저장은 `version`을 정확히 1 올리고 임시 파일 후 원자 교체로 저장된다.
- AC-2: `add SKU --qty N [--name NAME] [--location LOC]`은 LOC(기본 MAIN)에 수량을 더하며 기존 출력·종료 코드를 유지한다. `remove SKU --qty N [--location LOC]`은 LOC(기본 MAIN)에서 차감하고, 미등록 SKU는 exit 1, 해당 위치 수량 부족은 exit 2이며 stderr가 `insufficient:`로 시작한다.
- AC-3: `list`는 품목·위치 조합마다 한 줄 `SKU\tNAME\tLOC\tQTY`를 SKU 다음 LOC 오름차순으로 출력하고, 수량 0인 위치는 출력하지 않는다.
- AC-4: `transfer SKU --from A --to B --qty N`은 A에서 B로 N을 옮기고 성공 시 stdout `SKU A->B N`, exit 0이다. 미등록 SKU exit 1, A의 수량 부족 exit 2(stderr `insufficient:`로 시작), qty ≤ 0 또는 A == B는 exit 5(stderr `invalid:`로 시작)이며, 실패 시 저장소 파일은 바이트 단위로 변하지 않는다.
- AC-5: 성공한 변경 명령(add, remove, transfer, import-csv로 반영된 행)은 SKU별로 `<저장소 경로>.audit.jsonl`에 `ts`(ISO 8601), `op`(add|remove|transfer|import), `sku`, `changes`({LOC: 부호 있는 증감}) 필드를 가진 JSON 한 줄을 추가하고, 실패한 명령은 감사 로그에 아무것도 남기지 않는다.
- AC-6: `history SKU`는 그 SKU의 감사 기록을 최신순으로 한 줄씩 `TS\tOP\tLOC:DELTA,...`(changes는 LOC 오름차순, DELTA는 부호 포함 예 `+5`, `-3`)로 출력하고, 기록이 없으면 출력 없이 exit 0이다.
- AC-7: `import-csv FILE`은 헤더 `sku,name,location,qty`의 CSV에서 qty가 양의 정수가 아니거나 필드가 빈 행을 거부하고, 유효 행을 한 번의 저장으로 모두 반영(add와 같은 의미)한 뒤 stdout `applied N, rejected M`을 출력한다. M > 0이면 `FILE.rejected.csv`에 원래 열 + `reason` 열로 거부 행을 쓰고 exit 3, M = 0이면 그 파일을 만들지 않고 exit 0이다.
- AC-8: 변경 명령(add, remove, transfer, import-csv)은 `--expect-version V`를 받아 현재 version이 V와 다르면 exit 4, stderr `conflict: expected V, found X`로 끝나고 저장하지 않는다. `version` 명령은 현재 version 정수 한 줄을 출력한다.
