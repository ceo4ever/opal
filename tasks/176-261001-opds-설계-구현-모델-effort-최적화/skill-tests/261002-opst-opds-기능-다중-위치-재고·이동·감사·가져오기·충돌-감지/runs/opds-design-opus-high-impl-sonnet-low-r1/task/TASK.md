---
template: sdlc-v2
---
# TASK: stockctl 다중 위치 재고·이동·감사·가져오기·충돌 감지

## Problem
stockctl은 품목마다 위치 1개만 가진다(`docs/CLI.md` 계약, `stockctl/store.py:6` "sku → {name, qty, location} 단일 위치 구조"). 창고 여러 곳을 운영하면서 위치 간 이동, 변경 추적, 대량 등록, 동시 수정 사고 방지가 필요해졌지만 현재 도구로는 어느 것도 할 수 없다. 요구 원문: `/private/tmp/claude-501/-Volumes-Data-AiStudio-workspace-opal--opal-worktrees-task-176/39b1b7a5-a283-4de9-b1e6-120a0bdcb558/scratchpad/measure-function-stockctl-multiloc/opds-design-opus-high-impl-sonnet-low-r1/REQUEST.md`(요구서 — 사용자가 TASK 요구사항으로 그대로 사용하도록 지시).

## Proposed outcome
- 한 품목이 여러 위치에 수량을 가지며, 기존 단일 위치 형식 파일도 데이터 손실 없이 계속 쓸 수 있다.
- 위치를 지정해 추가·차감·조회하고, 위치 간 재고를 이동할 수 있다.
- 성공한 모든 변경이 SKU별 감사 기록으로 남고, SKU별 변경 이력을 최신순으로 조회할 수 있다.
- CSV 파일로 여러 품목을 한 번에 등록하고, 거부된 행과 사유를 별도 파일로 받는다.
- 저장소 version으로 동시 수정을 감지해, 예상과 다른 version이면 변경이 거부된다.

## Affected users and systems
- 사용자: stockctl CLI로 창고 재고를 관리하는 운영자.
- 시스템: `stockctl` 패키지(CLI·저장소), JSON 저장소 파일과 그 옆 감사 로그 파일(`<저장소 경로>.audit.jsonl`), CSV 가져오기 입력·거부 출력 파일, `docs/CLI.md`, `tests/`.
- 제외: 파일 잠금 기반 동시성 제어, 감사 로그 회전·정리, 외부 패키지 도입.

## Constraints
- C-1: 프로젝트 금지사항과 컨벤션을 따른다 — 표준 라이브러리만 사용, 임시 파일 기록 후 원자 교체 저장, 오류는 stderr 한 줄 + 종료 코드 구분(`.opal/AGENT.md` §금지사항, `docs/CONVENTIONS.md`).
- C-2: 기존 테스트(`tests/test_basic.py`)는 수정 없이 계속 통과해야 한다.
- C-3: `docs/CLI.md`를 새 명령 계약(명령·옵션·출력 형식·종료 코드·파일 형식)으로 갱신한다.
- C-4: 실패한 명령(검증 실패·충돌 포함)은 저장소 파일을 바꾸지 않고 감사 기록도 남기지 않는다.

## Acceptance criteria
- AC-1: 저장소는 품목별 `{"name": ..., "locations": {LOC: qty}}` 구조와 최상위 정수 `version`을 가진다. 기존 형식(품목이 `{name, qty, location}`이고 `version` 없음) 파일은 `{location: qty}`·version 0으로 읽히고, 다음 성공 저장 때 새 형식으로 기록되며 어떤 품목·수량도 사라지지 않는다. 모든 성공 저장은 `version`을 정확히 1 올린다.
- AC-2: `add SKU --qty N [--name NAME] [--location LOC]`는 LOC(기본 MAIN)에 수량을 더하고 기존 출력·종료 코드를 유지한다. `remove SKU --qty N [--location LOC]`는 LOC(기본 MAIN)에서 차감하며, 미등록 SKU는 exit 1, 그 위치 수량 부족은 exit 2와 `insufficient:`로 시작하는 stderr로 거부된다.
- AC-3: `list`는 품목·위치 조합마다 `SKU\tNAME\tLOC\tQTY` 한 줄을 SKU 오름차순, 같은 SKU 안에서는 LOC 오름차순으로 출력하고, 수량 0인 위치는 출력하지 않는다.
- AC-4: `transfer SKU --from A --to B --qty N`은 A에서 B로 N을 옮기고 stdout `SKU A->B N`, exit 0을 낸다. 미등록 SKU는 exit 1, A 수량 부족은 exit 2(stderr `insufficient:` 시작), qty ≤ 0 또는 A == B는 exit 5(stderr `invalid:` 시작)이며, 실패 시 저장소 파일은 바이트 단위로 변하지 않는다.
- AC-5: 성공한 add·remove·transfer와 import-csv로 반영된 변경은 SKU별로 `<저장소 경로>.audit.jsonl`에 `ts`(ISO 8601)·`op`(add|remove|transfer|import)·`sku`·`changes`({LOC: 부호 있는 증감}) 필드를 가진 JSON 한 줄을 추가한다. 실패한 명령은 아무 줄도 남기지 않는다.
- AC-6: `history SKU`는 그 SKU의 감사 기록을 최신순으로 `TS\tOP\tLOC:DELTA,...`(changes는 LOC 오름차순, DELTA는 `+5`·`-3`처럼 부호 포함) 한 줄씩 출력하고, 기록이 없으면 출력 없이 exit 0이다.
- AC-7: `import-csv FILE`은 헤더 `sku,name,location,qty`의 CSV에서 qty가 양의 정수가 아니거나 필드가 빈 행을 거부하고, 유효 행 전부를 add와 같은 의미로 한 번의 저장에 반영한 뒤 stdout `applied N, rejected M`을 낸다. M > 0이면 `FILE.rejected.csv`에 원래 열 + `reason` 열로 거부 행을 쓰고 exit 3, M = 0이면 그 파일을 만들지 않고 exit 0이다.
- AC-8: 변경 명령(add, remove, transfer, import-csv)은 `--expect-version V`를 받으며, 현재 version이 V와 다르면 exit 4, stderr `conflict: expected V, found X`로 거부되고 저장하지 않는다. `version` 명령은 현재 version 정수 한 줄을 출력한다.
