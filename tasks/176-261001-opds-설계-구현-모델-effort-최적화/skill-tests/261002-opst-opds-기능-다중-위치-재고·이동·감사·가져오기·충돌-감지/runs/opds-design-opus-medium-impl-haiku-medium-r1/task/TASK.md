---
template: sdlc-v2
---
# TASK: stockctl 다중 위치 재고·이동·감사·가져오기·충돌 감지

## Problem
현재 stockctl은 품목마다 위치를 1개만 가진다(`docs/CLI.md` §CLI 계약, `stockctl/store.py:3-8` 단일 위치 구조 `{name, qty, location}`). 창고를 여러 곳 운영하면서 같은 품목을 위치별로 보유·이동해야 하지만 표현할 수 없고, 누가 언제 무엇을 바꿨는지 추적할 수 없으며, 대량 등록 수단이 없고, 두 작업자가 같은 파일을 동시에 고칠 때 한쪽 변경이 조용히 덮어써지는 사고를 막을 장치가 없다. 요구 원문은 `../REQUEST.md`(허브 상위 `REQUEST.md`)이며 이 TASK는 그 요구를 그대로 수용 요구사항으로 쓴다.

## Proposed outcome
- 저장소가 품목별 위치→수량 구조와 최상위 정수 `version`을 갖고, 기존 단일 위치 파일도 데이터 손실 없이 읽히며 다음 성공 저장 때 새 형식으로 기록된다. 모든 성공 저장은 `version`을 1 올리고 원자 교체로 기록된다.
- `add`/`remove`/`list`가 위치 단위로 동작하고, `transfer`로 위치 간 이동을 할 수 있다.
- 성공한 변경은 SKU별 감사 기록으로 남고 `history`로 최신순 조회할 수 있다.
- `import-csv`로 여러 행을 한 번에 등록하고, 거부 행은 사유와 함께 별도 파일로 받는다.
- 변경 명령에 기대 version을 지정해 동시 수정 충돌을 감지·거부할 수 있고, `version`으로 현재 version을 조회할 수 있다.
- `docs/CLI.md`가 새 계약을 기술한다.

## Affected users and systems
- 사용자: stockctl CLI로 창고 재고를 관리하는 운영자.
- 시스템: `stockctl/` 패키지(저장소·CLI), `tests/`, `docs/CLI.md`, 저장소 JSON 파일과 그 옆에 생기는 감사 로그(`<저장소 경로>.audit.jsonl`)·거부 행 파일(`FILE.rejected.csv`).
- 제외: 외부 패키지 도입, 파일 잠금 기반 동시성 제어, 기존 명령의 출력 형식 변경(요구서가 바꾸는 `list`·`remove` 제외).

## Constraints
- C-1: Python 3 표준 라이브러리만 사용한다(`.opal/AGENT.md` §금지사항, `docs/CONVENTIONS.md`).
- C-2: 기존 테스트 `tests/test_basic.py`는 수정 없이 계속 통과해야 한다.
- C-3: 저장은 임시 파일 기록 후 원자 교체 방식을 유지한다(`docs/CONVENTIONS.md`, `stockctl/store.py:26-30`).
- C-4: 실패한 명령은 저장소 파일을 바이트 단위로 바꾸지 않고 감사 기록도 남기지 않는다.
- C-5: `docs/CONVENTIONS.md`의 프로젝트 규칙(@header, stderr 한 줄 오류, `python -m stockctl` 호출 테스트)을 따른다.

## Acceptance criteria
- AC-1: 저장소는 `items[sku] = {"name": ..., "locations": {LOC: qty}}`와 최상위 정수 `version`을 가진다. 기존 형식(`{name, qty, location}`, `version` 없음) 파일은 읽을 때 `{location: qty}`·version 0으로 해석되어 기존 품목·수량·위치가 하나도 사라지지 않고, 다음 성공 저장 때 새 형식으로 기록된다. 모든 성공 저장은 `version`을 정확히 1 올린다.
- AC-2: `add SKU --qty N [--name NAME] [--location LOC]`은 LOC(기본 MAIN)에 수량을 더하며 기존 출력 형식과 종료 코드를 유지한다. `remove SKU --qty N [--location LOC]`은 LOC(기본 MAIN)에서 차감하고, 미등록 SKU는 exit 1, 해당 위치 수량 부족은 exit 2와 `insufficient:`로 시작하는 stderr를 낸다.
- AC-3: `list`는 품목·위치 조합마다 `SKU\tNAME\tLOC\tQTY` 한 줄을 SKU 오름차순, 같은 SKU 안에서 LOC 오름차순으로 출력하고 수량 0인 위치는 출력하지 않는다.
- AC-4: `transfer SKU --from A --to B --qty N`은 성공 시 A에서 B로 N을 옮기고 stdout `SKU A->B N`, exit 0을 낸다. 미등록 SKU exit 1, A 수량 부족 exit 2(stderr `insufficient:` 시작), qty ≤ 0 또는 A == B는 exit 5(stderr `invalid:` 시작)이며, 실패 시 저장소 파일은 바이트 단위로 변하지 않는다.
- AC-5: 성공한 add·remove·transfer와 import-csv로 반영된 변경은 SKU별로 `<저장소 경로>.audit.jsonl`에 `ts`(ISO 8601)·`op`(add|remove|transfer|import)·`sku`·`changes`({LOC: 부호 있는 증감}) 필드를 가진 JSON 한 줄을 추가하고, 실패한 명령은 아무것도 남기지 않는다.
- AC-6: `history SKU`는 그 SKU의 감사 기록을 최신순으로 한 줄씩 `TS\tOP\tLOC:DELTA,...`(changes는 LOC 오름차순, DELTA는 `+5`·`-3`처럼 부호 포함) 형식으로 출력하고, 기록이 없으면 출력 없이 exit 0이다.
- AC-7: `import-csv FILE`은 헤더 `sku,name,location,qty` CSV에서 qty가 양의 정수가 아니거나 필드가 빈 행을 거부하고, 유효 행은 한 번의 저장으로 add와 같은 의미로 모두 반영한 뒤 stdout `applied N, rejected M`을 낸다. M > 0이면 `FILE.rejected.csv`에 원래 열 + `reason` 열로 거부 행을 쓰고 exit 3, M = 0이면 그 파일을 만들지 않고 exit 0이다.
- AC-8: 변경 명령(add, remove, transfer, import-csv)은 `--expect-version V`를 받고, 현재 version이 V와 다르면 exit 4와 stderr `conflict: expected V, found X`를 내며 저장하지 않는다. `version` 명령은 현재 version 정수 한 줄을 출력한다.
- AC-9: `docs/CLI.md`가 위 데이터 형식과 명령·출력·종료 코드 계약을 기술한다.
