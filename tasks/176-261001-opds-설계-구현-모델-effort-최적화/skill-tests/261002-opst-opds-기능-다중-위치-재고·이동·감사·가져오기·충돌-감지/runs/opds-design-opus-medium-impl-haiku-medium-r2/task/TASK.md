---
template: sdlc-v2
---
# TASK: stockctl 다중 위치 재고·이동·감사·가져오기·충돌 감지

## Problem
stockctl은 품목마다 위치 1개만 가진다(`docs/CLI.md` §CLI 계약, `stockctl/store.py:6`). 창고 여러 곳을 운영하면서 같은 품목을 여러 위치에 나눠 보관할 수 없고, 위치 간 이동·변경 이력 추적·대량 등록 수단이 없으며, 두 사람이 같은 저장소를 동시에 고칠 때 한쪽 변경이 조용히 덮어써지는 사고를 막을 방법이 없다(요구서 `../REQUEST.md` 서두).

## Proposed outcome
- 한 품목이 여러 위치에 수량을 가지며, 저장소는 정수 version을 갖고 성공 저장마다 1씩 증가한다. 기존 단일 위치 형식 파일도 데이터 손실 없이 그대로 읽히고 다음 성공 저장 때 새 형식으로 바뀐다.
- add·remove·list가 위치 단위로 동작하고, transfer로 위치 간 이동을 한다.
- 성공한 변경은 SKU별 감사 기록으로 남고 history로 최신순 조회된다.
- import-csv로 CSV 대량 등록을 하며 거부 행은 사유와 함께 별도 파일로 돌려받는다.
- 변경 명령에 기대 version을 주면 다른 변경이 끼어든 경우 저장하지 않고 충돌로 알리며, version 명령으로 현재 version을 확인한다.
- `docs/CLI.md`가 새 명령 계약을 설명한다.

## Affected users and systems
- 사용자: stockctl CLI로 창고 재고를 관리하는 운영자.
- 시스템: `stockctl/` 패키지(저장소·CLI), 저장소 JSON 파일, 저장소 옆 감사 로그 파일(`<저장소 경로>.audit.jsonl`), import 거부 파일(`FILE.rejected.csv`), `tests/`, `docs/CLI.md`.
- 제외: 저장소 경로 결정 규칙(`--store` > `STOCKCTL_STORE` > `stock.json`, `docs/CLI.md`)은 바꾸지 않는다. 감사 로그의 회전·삭제는 범위 밖이다.

## Constraints
- C-1: 표준 라이브러리만 사용한다(`.opal/AGENT.md` §금지사항, `docs/CONVENTIONS.md`).
- C-2: 저장은 임시 파일 기록 후 원자 교체를 유지하며, 기존 형식 파일의 품목 데이터(SKU·이름·위치·수량)가 사라지면 안 된다(요구서 §데이터).
- C-3: 기존 테스트 `tests/test_basic.py`가 수정 없이 계속 통과해야 한다(요구서 §제약).
- C-4: 실패한 변경 명령은 저장소 파일을 바이트 단위로 바꾸지 않고 감사 로그에도 아무것도 남기지 않는다(요구서 §명령 계약 4·5·8).

## Acceptance criteria
- AC-1: 저장소가 `items[sku] = {"name", "locations": {LOC: qty}}`와 최상위 정수 `version` 구조를 가지며 모든 성공 저장이 version을 1 올린다. `{name, qty, location}` 품목·version 없는 기존 파일은 `{location: qty}`·version 0으로 해석되어 다음 성공 저장 때 새 형식(version 1)으로 기록되고 품목 데이터가 보존된다.
- AC-2: `add SKU --qty N [--name NAME] [--location LOC]`는 LOC(기본 MAIN)에 수량을 더하고 기존 출력·종료 코드를 유지한다. `remove SKU --qty N [--location LOC]`는 LOC(기본 MAIN)에서 차감하며 미등록 SKU는 exit 1, 해당 위치 수량 부족은 exit 2와 `insufficient:`로 시작하는 stderr를 낸다.
- AC-3: `list`는 품목·위치 조합마다 `SKU\tNAME\tLOC\tQTY` 한 줄을 SKU 다음 LOC 오름차순으로 출력하고 수량 0인 위치는 출력하지 않는다.
- AC-4: `transfer SKU --from A --to B --qty N`은 성공 시 A에서 B로 N을 옮기고 stdout `SKU A->B N`, exit 0을 낸다. 미등록 SKU exit 1, A 수량 부족 exit 2(stderr `insufficient:` 시작), qty ≤ 0 또는 A == B는 exit 5(stderr `invalid:` 시작)이며 실패 시 저장소 파일은 바이트 단위로 변하지 않는다.
- AC-5: 성공한 add·remove·transfer와 import-csv로 반영된 각 행은 SKU별로 `<저장소 경로>.audit.jsonl`에 `ts`(ISO 8601)·`op`(add|remove|transfer|import)·`sku`·`changes`({LOC: 부호 있는 증감}) 필드의 JSON 한 줄을 추가하고, 실패한 명령은 아무것도 남기지 않는다.
- AC-6: `history SKU`는 그 SKU의 감사 기록을 최신순으로 `TS\tOP\tLOC:DELTA,...`(changes는 LOC 오름차순, DELTA는 `+5`·`-3`처럼 부호 포함) 한 줄씩 출력하고, 기록이 없으면 출력 없이 exit 0이다.
- AC-7: `import-csv FILE`은 헤더 `sku,name,location,qty`의 유효 행을 한 번의 저장으로 add와 같은 의미로 반영하고 stdout `applied N, rejected M`을 낸다. qty가 양의 정수가 아니거나 필드가 빈 행은 거부되며, M > 0이면 `FILE.rejected.csv`에 원래 열 + `reason` 열로 거부 행을 쓰고 exit 3, M = 0이면 그 파일을 만들지 않고 exit 0이다.
- AC-8: add·remove·transfer·import-csv는 `--expect-version V`를 받아 현재 version이 V와 다르면 저장하지 않고 exit 4와 stderr `conflict: expected V, found X`를 낸다. `version` 명령은 현재 version 정수 한 줄을 출력한다.
- AC-9: `docs/CLI.md`가 위 데이터 구조·명령·옵션·출력·종료 코드 계약을 반영한다.
