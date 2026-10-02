# DONE: stockctl 다중 위치 재고·이동·감사·가져오기·충돌 감지

## 결과

- 저장소가 `items[sku] = {"name", "locations": {LOC: qty}}`와 최상위 정수 `version` 구조가 되었다. 성공 저장마다 version이 1씩 오르고, 저장은 기존처럼 임시 파일에 쓴 뒤 `os.replace`로 교체한다. 기존 형식(`{name, qty, location}`, version 없음)은 `{location: qty}`·version 0으로 읽히고, 다음 성공 저장 때 새 형식으로 기록된다. 수량 0인 위치도 보존된다.
- `add`·`remove`가 `--location`(기본 MAIN) 단위로 동작한다. `list`는 품목·위치 조합마다 한 줄씩, SKU 다음 LOC 오름차순으로 출력하고 수량 0인 위치는 숨긴다.
- 신규 명령은 4개다: `transfer`(exit 1/2/5), `history`(최신순, `LOC:+N` 형식), `import-csv`(한 번의 저장, `FILE.rejected.csv`, exit 3), `version`.
- 변경 명령 4종에 `--expect-version`을 추가했다. version이 다르면 exit 4와 `conflict: expected V, found X`를 내고 저장하지 않는다.
- 성공한 변경은 `<저장소>.audit.jsonl`에 기록된다(ts/op/sku/changes, import는 SKU별 1줄로 합산). 실패한 명령은 저장소·감사 로그·거부 파일을 바꾸지 않는다.
- 유지한 것: 저장소 경로 규칙(`--store` > `STOCKCTL_STORE` > `stock.json`), add/remove 출력 형식 `SKU qty=N`과 기존 종료 코드, `unknown sku:` 문구, 표준 라이브러리만 사용.
- `docs/CLI.md`를 새 계약으로 갱신했다.

## 변경 파일

- `stockctl/store.py`
- `stockctl/audit.py` (신규)
- `stockctl/cli.py`
- `tests/test_multiloc.py` (신규, RED-first)
- `docs/CLI.md`

## 검증

- `python -m pytest -q tests` → 11 passed (test_multiloc 9 + test_basic 2). `tests/test_basic.py`는 main 대비 무변경이다(`git diff --exit-code main -- tests/test_basic.py` exit 0).
- RED-first: 구현 전 S-1~S-9 9 failed를 관찰했고 `scenario-red` 9건 기록 후 `scenario-lock`. 구현 후 GREEN.
- `test-scenario.json`: 12/12 PASS(S-1~S-12, opal-test-agent 독립 판정, 수정 후 S-1~S-11 재실행).
- 컨벤션 최종 검사 `run/GC-CONVENTION-2026-10-02T00-09.md`: Critical/High/Medium 0, Low 1(advisory). 보안 grep 0건.
- 설계 게이트 i1 pass(evaluator 설계 4축 PASS, 시나리오 2/2/2).

## 회고적 학습 후보

없음

## 참고

- 컨벤션 advisory GC-005: 감사 로그는 append 전용이라 "임시 파일 + `os.replace`" 규약을 적용하지 않았다. 이 예외를 `docs/CONVENTIONS.md`에 명시할지는 소유자가 결정할 사항이다.
- PM이 요구서를 해석해 확정한 세부 4건이 있다(`design-decision` detail 기록).
  1. add/remove 출력 N은 대상 LOC의 수량이다.
  2. import 감사 기록은 SKU별 1줄로 합산한다.
  3. 오류 판정 순서는 5→4→1→2다.
  4. 수량 0인 위치 키는 저장소에 유지하고, 유효 행이 0건인 import는 저장하지 않는다.
- EXECUTE 중 `docs/CLI.md`가 미커밋 상태에서 원본으로 되돌아간 일이 1회 있었다. 원인 주체는 확인하지 못했고 W-2 워커가 복원했다. 이후 소실을 막기 위해 검증 단위마다 체크포인트 커밋을 남겼다.
