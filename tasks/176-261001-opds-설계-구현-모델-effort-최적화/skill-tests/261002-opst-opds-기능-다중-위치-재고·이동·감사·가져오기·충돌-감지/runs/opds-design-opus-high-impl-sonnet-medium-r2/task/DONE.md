# DONE: stockctl 다중 위치 재고·이동·감사·가져오기·충돌 감지

## 결과

- 저장소 형식을 `{"version": int, "items": {SKU: {"name", "locations": {LOC: qty}}}}`로 바꿨다. 기존 단일 위치 파일(`{name, qty, location}`, `version` 없음)은 읽을 때 `{location: qty}`·version 0으로 정규화되고 다음 성공 저장 때 새 형식으로 기록된다. 읽기 명령(`list`·`history`·`version`)은 파일을 쓰지 않는다. 모든 성공 저장은 `version`을 1 올리며 기존 `<path>.tmp` + `os.replace` 원자 저장을 유지한다.
- `add`·`remove`에 `--location`(기본 MAIN)을 적용했다. 출력 `SKU qty=<그 위치 수량>`과 종료 코드 0/1/2(`unknown sku:`/`insufficient:`)는 그대로다. `list`는 SKU·LOC 오름차순으로 출력하고 수량 0인 위치는 숨긴다.
- 신규 명령: `transfer`(exit 0/1/2/5), `history`(감사 기록 최신순), `import-csv`(`applied N, rejected M`, 거부 행은 `FILE.rejected.csv`에 쓰고 exit 3), `version`.
- 변경 명령 4종에 `--expect-version V`를 추가했다. 불일치 시 exit 4, stderr `conflict: expected V, found X`, 저장하지 않는다.
- 성공한 변경은 SKU별로 `<저장소>.audit.jsonl`에 `{ts, op, sku, changes}` 한 줄씩 남는다. 실패한 명령은 저장소 바이트와 감사 로그를 건드리지 않는다.
- 요구서에 없던 세부는 PLAN에 detail 결정으로 고정했다. import 입력 파일 오류는 exit 5 `invalid:`, history 순서는 추가 순서의 역순, import 감사는 SKU별 1줄, 유효 행이 0건이면 저장하지 않는다, 수량 0인 위치 키는 유지한다.

## 변경 파일

- `stockctl/store.py`
- `stockctl/cli.py`
- `docs/CLI.md`
- `tests/test_multiloc.py` (신규)

## 검증

- RED: S-1~S-12는 구현 전에 12건 모두 실패했다(`scenario-red` 기록 후 `scenario-lock`).
- `python -m pytest tests -q`: 14 passed (test_multiloc 12, test_basic 2).
- `test-scenario.json`: S-1~S-15 15/15 PASS (real-usage).
  - S-13: `git diff --exit-code main -- tests/test_basic.py` 결과 diff가 없고 기존 테스트도 통과한다.
  - S-14: 표준 라이브러리만 쓰고, @header 5키와 `os.replace`가 있다.
  - S-15: `docs/CLI.md`에 새 계약이 반영됐다.
- 보안 검사 PASS(시크릿 0건, `shell=True`·`eval`·`exec` 없음). 컨벤션 검사 Critical/High 0건(`run/GC-CONVENTION-2026-10-02T00-03.md`).

## 회고적 학습 후보

없음

## 참고

- 컨벤션 advisory GC-001(medium)은 미적용했다. `FILE.rejected.csv`를 원자 교체 없이 직접 덮어쓴다. 이 파일은 저장소가 아닌 보조 산출물이며 PLAN 결정과 일치한다. 개선 후보로 기록했다.
- 숫자가 아닌 `--qty` 같은 argparse 사용법 오류는 기존대로 exit 2다(`docs/CLI.md` 명시).
- 새 형식으로 한 번 저장한 저장소는 구버전 stockctl이 읽지 못한다. 자동 역변환은 없다.
- 로컬 개선 후보(improve-tool local은 워크트리에서 위임 실패 → 여기 기록): ① 문서 갱신 W 디스패치 시 요구서 출력 형식 토큰을 [MUST] 원문 인용(W-3 `LOCATION`→`LOC` 재작업 1회 원인) ② `FILE.rejected.csv` 원자 교체 적용 여부 검토(GC-001).
- 커밋은 워크트리 브랜치 `feat/OP-TASK-001`에만 있다. `main` merge는 사용자 승인 사항이다.
