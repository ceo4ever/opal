---
template: sdlc-v2
---
# TASK: stockctl 다중 위치 재고·이동·감사·가져오기·충돌 감지

## Problem
현재 stockctl은 품목마다 위치 1개만 가진다(`docs/CLI.md` §CLI 계약, `stockctl/store.py:6`). 창고 여러 곳을 운영하면서 같은 품목을 여러 위치에 나눠 보관할 수 없고, 위치 간 이동·변경 이력 추적·CSV 대량 등록·동시 수정 사고(다른 사람이 먼저 바꾼 저장소를 덮어씀) 방지 수단이 없다. 요구 원문은 요구서 `../REQUEST.md`(허브 상위 `REQUEST.md`)이며 이 TASK는 그 요구를 그대로 수용 기준으로 사용한다.

## Proposed outcome
- 품목이 위치별 수량(`items[sku] = {"name": ..., "locations": {LOC: qty}}`)을 가지며 저장소 최상위에 정수 `version`이 있다. 기존 단일 위치 파일도 데이터 손실 없이 그대로 읽히고 다음 성공 저장 때 새 형식으로 바뀐다.
- `add`·`remove`가 위치 단위로 동작하고, `list`가 품목·위치 조합별로 출력한다.
- `transfer`로 위치 간 이동, `history`로 SKU별 변경 이력 조회, `import-csv`로 대량 등록, `--expect-version`·`version`으로 충돌 감지가 가능하다.
- 성공한 변경은 SKU별 감사 기록(`<저장소 경로>.audit.jsonl`)으로 남고 실패한 명령은 아무것도 남기지 않는다.
- `docs/CLI.md`가 새 명령 계약을 기술한다.

## Affected users and systems
- 사용자: stockctl CLI로 창고 재고를 관리하는 운영자.
- 시스템: `stockctl/` 패키지(CLI·저장소), `tests/`, `docs/CLI.md`, 사용자의 기존 재고 JSON 파일과 새 감사 로그 파일(`<저장소 경로>.audit.jsonl`), import 거부 파일(`FILE.rejected.csv`).
- 제외: 표준 라이브러리 외 패키지, 다중 프로세스 파일 잠금, 감사 로그 순환·정리, 원격 저장소.

## Constraints
- C-1: 표준 라이브러리만 사용한다(`.opal/AGENT.md` §금지사항, `docs/CONVENTIONS.md`).
- C-2: 기존 테스트 `tests/test_basic.py`가 수정 없이 계속 통과한다.
- C-3: 저장은 임시 파일 기록 후 원자 교체를 유지하고, 프로젝트 컨벤션(`docs/CONVENTIONS.md` — @header, stderr 한 줄 오류, pytest + `python -m stockctl`)을 따른다.
- C-4: `docs/CLI.md`를 새 명령 계약으로 갱신한다.

## Acceptance criteria
- AC-1: 저장 형식 — 성공 저장 결과 파일의 품목은 `{"name": ..., "locations": {LOC: qty}}`, 최상위에 정수 `version`을 가진다. 기존 형식 파일(품목 `{name, qty, location}`, `version` 없음)은 읽을 때 `{location: qty}`·version 0으로 해석되어 모든 명령이 동작하고, 다음 성공 저장 때 품목·이름·수량 손실 없이 새 형식으로 기록된다. 모든 성공 저장은 `version`을 정확히 1 올린다.
- AC-2: `add SKU --qty N [--name NAME] [--location LOC]`는 LOC(기본 MAIN)에 수량을 더하고 기존 출력 형식·종료 코드(0)를 유지한다. `remove SKU --qty N [--location LOC]`는 LOC(기본 MAIN)에서 차감하며, 미등록 SKU는 exit 1, 해당 위치 수량 부족은 exit 2이고 stderr가 `insufficient:`로 시작한다.
- AC-3: `list`는 품목·위치 조합마다 `SKU\tNAME\tLOC\tQTY` 한 줄을 SKU 오름차순, 같은 SKU 안에서 LOC 오름차순으로 출력하고, 수량 0인 위치는 출력하지 않는다.
- AC-4: `transfer SKU --from A --to B --qty N`은 A에서 B로 수량을 옮기고 성공 시 stdout `SKU A->B N`, exit 0이다. 미등록 SKU exit 1, A 수량 부족 exit 2(stderr `insufficient:` 시작), qty ≤ 0 또는 A == B는 exit 5(stderr `invalid:` 시작)이며, 실패 시 저장소 파일은 바이트 단위로 변하지 않는다.
- AC-5: 성공한 변경(add, remove, transfer, import-csv로 반영된 각 행)은 SKU별로 `<저장소 경로>.audit.jsonl`에 JSON 한 줄(`ts` ISO 8601, `op` ∈ add|remove|transfer|import, `sku`, `changes` {LOC: 부호 있는 증감})을 추가하고, 실패한 명령은 감사 로그에 아무것도 남기지 않는다.
- AC-6: `history SKU`는 그 SKU의 감사 기록을 최신순으로 한 줄씩 `TS\tOP\tLOC:DELTA,...`(changes는 LOC 오름차순, DELTA는 `+5`·`-3`처럼 부호 포함)로 출력하고, 기록이 없으면 출력 없이 exit 0이다.
- AC-7: `import-csv FILE`(헤더 `sku,name,location,qty`)은 qty가 양의 정수가 아니거나 필드가 빈 행을 거부하고, 유효 행을 add와 같은 의미로 한 번의 저장에 모두 반영하며 stdout `applied N, rejected M`을 출력한다. M > 0이면 `FILE.rejected.csv`에 원래 열 + `reason` 열로 거부 행을 쓰고 exit 3, M = 0이면 그 파일을 만들지 않고 exit 0이다.
- AC-8: 변경 명령(add, remove, transfer, import-csv)은 `--expect-version V`를 받아 현재 version이 V와 다르면 exit 4, stderr `conflict: expected V, found X`로 끝내고 저장하지 않는다. `version` 명령은 현재 version 정수 한 줄을 출력한다.
