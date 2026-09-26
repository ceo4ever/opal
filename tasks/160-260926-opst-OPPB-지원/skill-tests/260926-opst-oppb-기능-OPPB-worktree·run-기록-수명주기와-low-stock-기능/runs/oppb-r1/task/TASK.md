---
template: sdlc-v2
---
# TASK: stockctl 재고 부족 품목 조회

## Problem
창고 담당자가 곧 떨어질 품목을 한 번에 확인할 방법이 없다. 현재는 `list` 전체 출력을 눈으로 훑어야 한다.

## Proposed outcome
`stockctl low-stock --below N`으로 수량이 N 미만인 품목만 SKU 오름차순 `SKU\tQTY` 형식으로 한 번에 확인할 수 있고, 잘못된 N은 일관된 오류로 거절된다.

## Affected users and systems
- 사용자: 창고 담당자(CLI 사용자)
- 시스템: `stockctl/cli.py`(새 서브커맨드), `tests/`(신규 테스트), `docs/CLI.md`(명령 계약)
- 제외: 저장 형식(`stockctl/store.py`의 JSON 구조), 기존 `add`·`remove`·`list` 출력 계약

## Constraints
- C-1: 저장 형식과 기존 `add`·`remove`·`list` 출력 계약을 바꾸지 않는다.
- C-2: 외부 패키지를 추가하지 않는다(Python 3 표준 라이브러리만).
- C-3: `low-stock`은 저장소 파일을 읽기만 하며 바이트 단위로 변경하지 않는다(파일이 없으면 만들지 않는다).
- C-4: 외부 서비스·운영 데이터·원격 저장소를 변경하지 않는다.
- C-5: `docs/CONVENTIONS.md`(@header, stderr 한 줄 오류, pytest + `python -m stockctl`)를 따른다.

## Acceptance criteria
- AC-1: `stockctl low-stock --below N`은 수량이 N 미만인 품목을 SKU 오름차순으로 `SKU\tQTY` 한 줄씩 출력하고 exit 0으로 끝난다.
- AC-2: 해당 품목이 없으면 stdout에 아무것도 출력하지 않고 exit 0으로 끝난다.
- AC-3: N이 정수가 아니거나 0 이하이면 stderr에 `invalid:`로 시작하는 한 줄을 쓰고 exit 5로 끝난다.
- AC-4: `low-stock` 실행 전후 저장소 파일의 바이트가 동일하다.
- AC-5: 기존 명령과 `tests/test_basic.py`가 계속 통과한다.
- AC-6: `docs/CLI.md`에 `low-stock` 명령·출력 형식·종료 코드가 문서화된다.
