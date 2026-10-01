# DONE: stockctl 다중 위치 재고·이동·감사·가져오기·충돌 감지

## 결과

- 품목 저장 구조를 `items[sku] = {"name", "locations": {LOC: qty}}`로 바꾸고 저장소 최상위에 정수 `version`을 두었다. 모든 성공 저장은 `version`을 1 올리며, 임시 파일 기록 후 `os.replace`로 원자 교체하는 방식은 그대로다.
- 구형 파일(`{name, qty, location}`, `version` 없음)은 읽을 때 `{location: qty}`·version 0으로 해석한다. 다음 성공 저장 때 품목·이름·수량(qty 0 포함)을 잃지 않고 새 형식으로 기록한다. 읽기만 하는 명령은 파일을 쓰지 않는다.
- `add`·`remove`는 `--location`(기본 MAIN) 단위로 동작하고, 출력 형식 `SKU qty=N`과 종료 코드는 기존과 같다. N은 바뀐 위치의 결과 수량이다. `list`는 품목·위치 조합마다 한 줄을 출력하며, 수량 0인 위치는 숨긴다.
- 새 명령 `transfer`·`history`·`import-csv`·`version`을 추가했고, 변경 명령 4종에 `--expect-version` 충돌 감지(exit 4)를 넣었다. 성공한 변경은 `<저장소>.audit.jsonl`에 감사 기록을 남긴다. 실패한 명령은 저장소·감사 파일·거부 파일을 바꾸지 않는다.
- 종료 코드: 0 성공, 1 미등록 SKU, 2 수량 부족, 3 import 거부 행 있음, 4 버전 충돌, 5 입력 무효. 실패 판정 순서는 입력 검증(5) → 충돌(4) → 미등록(1) → 부족(2)이다.
- 그대로 둔 것: 표준 라이브러리만 사용, 저장소 경로 규칙(`--store` > `STOCKCTL_STORE` > `stock.json`), `tests/test_basic.py`(수정 없이 통과).

## 변경 파일

- `stockctl/store.py`
- `stockctl/audit.py` (신규)
- `stockctl/cli.py`
- `tests/test_multiloc.py` (신규)
- `docs/CLI.md`

## 검증

- RED: 구현 전 `tests/test_multiloc.py` 14건 실패를 관찰(`test-tool scenario-red` 14/14) → `scenario-lock`.
- TEST(SHA a710ae0): `test-scenario.json` S-1~S-17 17/17 PASS.
- 전체 회귀: `python -m pytest tests/ -q` → 16 passed (test_multiloc 14 + test_basic 2).
- 보안 검사 Pass(시크릿·위험 호출 0건, `.gitignore` 확인). 최종 컨벤션 검사 Critical 0·High 0(권고 Medium 1·Low 2, `run/GC-CONVENTION-2026-10-02T00-00-00.md`).
- 설계 게이트 i1 pass(설계 4축 PASS, 시나리오 3축 2/2/2).

## 회고적 학습 후보

없음

## 참고

- PM이 정한 해석(사용자 재확인 권장): `add`/`remove` 출력 `qty=N`의 N은 총량이 아니라 바뀐 위치의 수량이다. 그 밖의 세부 결정(ts는 UTC 초 단위, history는 추가 순서의 역순, import에서 유효 행이 0건이면 저장하지 않음, import 헤더·파일 오류는 exit 5)은 `docs/CLI.md`에 적었다.
- 미처리 권고(요구 범위 밖): 손상된 저장소 JSON과 UTF-8이 아닌 CSV는 한 줄 오류 대신 traceback을 낸다(GC-001·GC-002). 다중 프로세스 동시 쓰기 잠금은 범위에서 제외했다.
- 머지 대기: 브랜치 `feat/OP-TASK-001`(워크트리 `.opal-worktrees/task_001`). main 머지는 사용자 승인 사항이다.
