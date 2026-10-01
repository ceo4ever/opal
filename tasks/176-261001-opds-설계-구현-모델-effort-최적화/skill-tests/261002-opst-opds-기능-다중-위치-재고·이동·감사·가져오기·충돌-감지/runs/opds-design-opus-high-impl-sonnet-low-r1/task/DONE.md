# DONE: stockctl 다중 위치 재고·이동·감사·가져오기·충돌 감지

## 결과

- 저장소가 품목별 `{"name", "locations": {LOC: qty}}` 구조와 최상위 정수 `version`을 갖는다. 구형 `{name, qty, location}` 파일(version 없음)은 읽을 때 `{location: qty}`·version 0으로 해석되고 다음 성공 저장 때 신형으로 기록된다(수량 0 품목도 보존). 성공 저장마다 version +1, 저장은 임시 파일 + `os.replace` 원자 교체를 유지한다.
- `add`/`remove`가 `--location`(기본 MAIN)을 받고, `list`는 품목·위치 조합별 한 줄(SKU→LOC 오름차순, 수량 0 숨김)을 출력한다. 기존 출력 형식 `SKU qty=N`과 종료 코드(remove 1·2)는 유지된다.
- 신규 명령: `transfer`(exit 1/2/5, 실패 시 바이트 무변경), `history`(감사 기록 최신순), `import-csv`(유효 행 1회 저장, `FILE.rejected.csv` + exit 3), `version`.
- 성공한 변경은 `<저장소>.audit.jsonl`에 SKU별 JSON 한 줄(`ts`·`op`·`sku`·`changes`)로 남고, 실패·충돌 명령은 아무것도 남기지 않는다.
- 변경 명령 4종이 `--expect-version V`를 받아 불일치 시 exit 4, `conflict: expected V, found X`로 거부한다.
- 경계: 요구서 미규정 세부(검사 순서 5→4→1→2, import 입력 오류 exit 5, reason 토큰 `bad_columns`/`empty_field`/`invalid_qty`, add/remove 출력 N=위치 수량, 0 수량 위치 보존)는 PLAN D-4~D-15로 확정했다. 표준 라이브러리만 사용했다.

## 변경 파일

- `stockctl/store.py`
- `stockctl/cli.py`
- `tests/test_multiloc.py`
- `docs/CLI.md`

## 검증

- RED: 구현 전 `python3 -m pytest tests/test_multiloc.py -q` → 11 failed(구현 부재 원인), `test-tool scenario-red` 11건 기록 후 `scenario-lock`.
- TEST(opal-test-agent, SHA 3b015ce): S-1~S-15 15/15 PASS(`test-scenario.json`, 증거 `run/test/S-*.out`). 전체 회귀 `python3 -m pytest tests/ -q` → 13 passed. `git diff main -- tests/test_basic.py` 빈 출력(기존 테스트 무수정).
- 보안 검사 Pass(시크릿·민감 파일·위험 호출 없음). lint/type은 프로젝트 설정 부재로 미실행.
- 컨벤션(opal-convention-checker, base main): High 1건 GC-001(`tests/test_multiloc.py` @header `exports` 누락)은 오탐으로 판정 — finding의 검증 기준인 `code-scan scan tests/test_multiloc.py --json`이 `"exports": []`를 반환하고 기존 `tests/test_basic.py`와 같은 관례다. 실질 Critical/High 0건.
- 설계 게이트 i1 pass(design 4축 PASS, scenario 2/2/2).

## 회고적 학습 후보

없음

## 참고

- worktree `feat/OP-TASK-001`은 머지 대기 상태다. `main` merge는 사용자 승인 사항이다.
- convention-precheck가 빈 `exports: []`를 필드 누락으로 판정하는 문제는 FW 개선 후보로 기록했다.
