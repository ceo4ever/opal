---
template: sdlc-v2
---
# TASK: stockctl 다중 위치 재고·이동·감사·가져오기·충돌 감지

## Problem
stockctl은 품목마다 위치 1개만 가진다(`docs/CLI.md` §CLI 계약, `stockctl/store.py:5`). 창고 여러 곳을 운영하면서 위치 간 이동을 기록할 수 없고, 누가 언제 무엇을 바꿨는지 추적할 수 없으며, 대량 등록을 한 건씩 해야 하고, 두 사람이 동시에 같은 저장소를 고치면 한쪽 변경이 조용히 덮어써진다. 근거: 요구서 `../REQUEST.md` 서두.

## Proposed outcome
운영자는 한 품목을 여러 위치에 나눠 보관하고, 위치별로 추가·차감·조회·이동할 수 있다. 성공한 모든 변경은 SKU별 감사 기록으로 남고 `history`로 최신순 조회된다. CSV 한 파일로 여러 품목을 한 번에 등록하고 거부된 행은 사유와 함께 별도 파일로 돌려받는다. 저장소는 정수 `version`을 가지며, 변경 명령에 기대 version을 주면 그사이 다른 변경이 있었을 때 저장하지 않고 충돌로 거부한다. 기존 단일 위치 저장소 파일은 데이터 손실 없이 그대로 읽히고 다음 성공 저장 때 새 형식으로 바뀐다.

## Affected users and systems
- 사용자: stockctl CLI 운영자.
- 시스템: `stockctl/` 패키지(저장소·CLI), `tests/`, `docs/CLI.md`.
- 포함: 요구서 §데이터·§명령 계약 1~8 전부.
- 제외: 동시 실행 시 OS 수준 파일 잠금, 감사 로그 회전·삭제, 외부 패키지 도입.

## Constraints
- C-1: 표준 라이브러리만 사용한다(`.opal/AGENT.md` §금지사항, `docs/CONVENTIONS.md`).
- C-2: 기존 테스트 `tests/test_basic.py`는 수정 없이 계속 통과해야 한다.
- C-3: `docs/CLI.md`를 새 명령 계약(명령·옵션·출력 형식·종료 코드·파일 형식)으로 갱신한다.
- C-4: 저장소 저장은 임시 파일 기록 후 원자 교체를 유지하고, 그 밖의 프로젝트 컨벤션(`docs/CONVENTIONS.md`)을 따른다.

## Acceptance criteria
- AC-1: 저장소는 `items[sku] = {"name", "locations": {LOC: qty}}`와 최상위 정수 `version` 형식으로 기록된다. `version`이 없고 품목이 `{name, qty, location}`인 기존 파일은 `{location: qty}`·version 0으로 읽히며, 다음 성공 저장 때 모든 품목·수량·이름이 보존된 채 새 형식으로 기록된다.
- AC-2: 모든 성공 저장은 `version`을 정확히 1 올리고, 실패한 명령(미등록 SKU·수량 부족·무효 입력·version 충돌)은 저장소 파일을 바이트 단위로 바꾸지 않는다.
- AC-3: `add SKU --qty N [--name NAME] [--location LOC]`는 LOC(기본 MAIN)에 수량을 더하고 기존 출력 형식·종료 코드를 유지한다. `remove SKU --qty N [--location LOC]`는 LOC(기본 MAIN)에서 차감하며 미등록 SKU는 exit 1, 해당 위치 수량 부족은 exit 2와 `insufficient:`로 시작하는 stderr를 낸다.
- AC-4: `list`는 품목·위치 조합마다 `SKU\tNAME\tLOC\tQTY` 한 줄을 SKU 다음 LOC 오름차순으로 출력하고, 수량 0인 위치는 출력하지 않는다.
- AC-5: `transfer SKU --from A --to B --qty N`은 성공 시 A에서 B로 N을 옮기고 stdout `SKU A->B N`, exit 0을 낸다. 미등록 SKU는 exit 1, A 수량 부족은 exit 2(stderr `insufficient:` 시작), qty ≤ 0 또는 A == B는 exit 5(stderr `invalid:` 시작)이다.
- AC-6: 성공한 add·remove·transfer와 import-csv로 반영된 행마다 `<저장소 경로>.audit.jsonl`에 SKU별 JSON 한 줄(`ts` ISO 8601, `op` add|remove|transfer|import, `sku`, `changes` {LOC: 부호 있는 증감})이 추가되고, 실패한 명령은 아무 줄도 남기지 않는다.
- AC-7: `history SKU`는 그 SKU의 감사 기록을 최신순으로 `TS\tOP\tLOC:DELTA,...`(changes는 LOC 오름차순, DELTA는 `+5`·`-3`처럼 부호 포함) 한 줄씩 출력하고, 기록이 없으면 출력 없이 exit 0이다.
- AC-8: `import-csv FILE`은 헤더 `sku,name,location,qty`의 행 중 필드가 비지 않고 qty가 양의 정수인 행만 add와 같은 의미로 한 번의 저장에 모두 반영하고 stdout `applied N, rejected M`을 낸다. M > 0이면 `FILE.rejected.csv`에 원래 열과 `reason` 열로 거부 행을 쓰고 exit 3, M = 0이면 그 파일을 만들지 않고 exit 0이다.
- AC-9: add·remove·transfer·import-csv는 `--expect-version V`를 받아 현재 version이 V와 다르면 저장하지 않고 exit 4와 stderr `conflict: expected V, found X`를 낸다. `version` 명령은 현재 version 정수 한 줄을 출력한다.
