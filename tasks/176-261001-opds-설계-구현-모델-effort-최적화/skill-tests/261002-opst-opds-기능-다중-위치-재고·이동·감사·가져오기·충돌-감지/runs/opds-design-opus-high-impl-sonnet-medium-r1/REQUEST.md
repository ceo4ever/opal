# 요구서: stockctl 다중 위치 재고·이동·감사·가져오기·충돌 감지

현재 stockctl은 품목마다 위치 1개만 가진다(`docs/CLI.md`). 창고 여러 곳을 운영하면서 위치 간 이동, 변경 추적, 대량 등록, 동시 수정 사고 방지가 필요해졌다. 아래를 만족하도록 구현한다.

## 데이터
- 품목 구조를 `items[sku] = {"name": ..., "locations": {LOC: qty}}`로 바꾸고 저장소 최상위에 정수 `version`을 둔다.
- 기존 파일(품목이 `{name, qty, location}`인 형식, `version` 없음)은 읽을 때 `{location: qty}`, version 0으로 해석하고, 다음 성공 저장 때 새 형식으로 기록한다. 데이터가 사라지면 안 된다.
- 모든 성공 저장은 `version`을 1 올린다. 저장은 임시 파일 후 원자 교체를 유지한다.

## 명령 계약
1. `add SKU --qty N [--name NAME] [--location LOC]` — LOC(기본 MAIN)에 수량 추가. 기존 출력·종료 코드 유지.
2. `remove SKU --qty N [--location LOC]` — LOC(기본 MAIN)에서 차감. 미등록 SKU는 exit 1, 해당 위치 수량 부족은 exit 2이며 stderr가 `insufficient:`로 시작한다.
3. `list` — 품목·위치 조합마다 한 줄 `SKU\tNAME\tLOC\tQTY`, SKU 다음 LOC 오름차순, 수량 0인 위치는 출력하지 않는다.
4. `transfer SKU --from A --to B --qty N` — A에서 B로 이동. 성공 시 stdout `SKU A->B N`, exit 0. 미등록 SKU exit 1. A의 수량 부족 exit 2(stderr `insufficient:`로 시작). qty ≤ 0 또는 A == B는 exit 5(stderr `invalid:`로 시작). 실패 시 저장소 파일은 바이트 단위로 변하지 않는다.
5. 감사 로그 — 성공한 변경 명령(add, remove, transfer, import-csv로 반영된 행)은 SKU별로 `<저장소 경로>.audit.jsonl`에 JSON 한 줄을 추가한다. 필드: `ts`(ISO 8601), `op`(add|remove|transfer|import), `sku`, `changes`({LOC: 부호 있는 증감}). 실패한 명령은 아무것도 남기지 않는다.
6. `history SKU` — 그 SKU의 감사 기록을 최신순으로 한 줄씩 `TS\tOP\tLOC:DELTA,...`(changes는 LOC 오름차순, DELTA는 부호 포함 예 `+5`, `-3`) 출력. 기록이 없으면 출력 없이 exit 0.
7. `import-csv FILE` — 헤더 `sku,name,location,qty`. qty가 양의 정수가 아니거나 필드가 비면 그 행은 거부한다. 유효 행은 한 번의 저장으로 모두 반영(add와 같은 의미). stdout `applied N, rejected M`. M > 0이면 `FILE.rejected.csv`(원래 경로 뒤에 `.rejected.csv`)에 원래 열 + `reason` 열로 거부 행을 쓰고 exit 3, M = 0이면 파일을 만들지 않고 exit 0.
8. 충돌 감지 — 변경 명령(add, remove, transfer, import-csv)은 `--expect-version V`를 받는다. 현재 version이 V와 다르면 exit 4, stderr `conflict: expected V, found X`, 저장하지 않는다. `version` 명령은 현재 version 정수 한 줄을 출력한다.

## 제약
- 표준 라이브러리만 사용한다.
- 기존 테스트(`tests/test_basic.py`)는 계속 통과해야 한다.
- `docs/CLI.md`를 새 계약으로 갱신한다.
