---
template: sdlc-v2
feature: low-stock
---
# TASK: stockctl 재고 부족 품목 조회 (low-stock)

## Problem
창고 담당자가 곧 떨어질 품목을 한 번에 확인할 방법이 없다. 현재 `list`는 전 품목을 출력하므로 수량 임계값 이하 품목을 사람이 직접 걸러야 한다. (출처: `../REQUEST.md` 요구서)

## Proposed outcome
`stockctl low-stock --below N` 한 번으로 수량이 N 미만인 품목만 SKU 오름차순 `SKU\tQTY` 줄로 확인할 수 있고, 잘못된 N은 식별 가능한 오류와 전용 종료 코드로 거부된다. 명령 계약은 `docs/CLI.md`에 문서화된다.

## Affected users and systems
- 사용자: 창고 담당자(stockctl CLI 사용자)
- 시스템: `stockctl/cli.py`(서브커맨드 추가), `tests/`(신규 테스트), `docs/CLI.md`(명령 계약)
- 제외: 저장소 포맷(`stockctl/store.py`의 데이터 구조) 변경, 기존 add/remove/list 동작 변경

## Constraints
- C-1: 저장소 파일은 읽기만 하고 바꾸지 않는다 — low-stock 실행 전후 저장소 파일 바이트가 동일하고 새 파일(`*.tmp` 포함)을 만들지 않는다.
- C-2: 기존 명령(add/remove/list)과 기존 테스트(`tests/test_basic.py`)는 그대로 동작해야 한다.
- C-3: 외부 패키지 추가 금지 — Python 3 표준 라이브러리만 사용한다 (`.opal/AGENT.md` 금지사항, `docs/CONVENTIONS.md`).
- C-4: `docs/CONVENTIONS.md`를 준수한다 — 소스 @header 유지, 오류는 stderr 한 줄 + 종료 코드, 테스트는 `tests/`의 pytest로 `python -m stockctl` 호출.

## Acceptance criteria
- AC-1: `stockctl low-stock --below N`은 수량이 N 미만인 품목만 SKU 오름차순으로 `SKU\tQTY` 형식 한 줄씩 stdout에 출력하고 exit 0으로 끝난다.
- AC-2: N 미만 품목이 없으면 stdout·stderr에 아무것도 출력하지 않고 exit 0으로 끝난다.
- AC-3: N이 정수가 아니면 stderr에 `invalid:`로 시작하는 한 줄을 쓰고 exit 5로 끝난다.
- AC-4: N이 0 이하이면 stderr에 `invalid:`로 시작하는 한 줄을 쓰고 exit 5로 끝난다.
- AC-5: low-stock 실행(정상·빈 결과·오류 모두) 후 저장소 파일 내용이 실행 전과 바이트 단위로 동일하다.
- AC-6: 기존 테스트를 포함한 전체 pytest가 통과한다(기존 add/remove/list 회귀 없음).
- AC-7: `docs/CLI.md` 명령 표에 `low-stock` 명령·출력 형식·종료 코드(0/5)가 추가되어 있다.
