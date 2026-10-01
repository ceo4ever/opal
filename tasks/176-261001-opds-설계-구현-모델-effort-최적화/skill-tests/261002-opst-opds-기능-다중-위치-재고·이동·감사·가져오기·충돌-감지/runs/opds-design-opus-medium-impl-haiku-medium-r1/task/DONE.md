# DONE: stockctl 다중 위치 재고·이동·감사·가져오기·충돌 감지

## 결과

- 저장소가 `{"version": int, "items": {SKU: {"name", "locations": {LOC: qty}}}}` 형식이 되었다. 기존 단일 위치 파일(`{name, qty, location}`, version 없음)은 읽을 때 `{location: qty}`·version 0으로 해석되고 다음 성공 저장 때 새 형식으로 기록된다. 모든 성공 저장은 version을 1 올리며 임시 파일 + `os.replace` 원자 교체를 유지한다.
- `add`/`remove`가 `--location`(기본 MAIN) 단위로 동작하고 기존 출력 `SKU qty=Q`·종료 코드를 유지한다(Q = 해당 위치 수량). `list`는 품목·위치 조합마다 한 줄을 SKU→LOC 오름차순으로 내고 수량 0 위치는 숨긴다.
- 신규 명령: `transfer`(위치 간 이동, 실패 시 저장소 바이트 불변), `history`(감사 기록 최신순), `import-csv`(유효 행 일괄 반영·거부 행 `FILE.rejected.csv`), `version`.
- 성공한 변경은 `<저장소>.audit.jsonl`에 SKU별 JSON 한 줄(`ts`·`op`·`sku`·`changes`)로 남고, 실패한 명령은 아무것도 남기지 않는다.
- 변경 명령 4종이 `--expect-version V`를 받아 불일치 시 exit 4·`conflict: expected V, found X`로 거부한다.
- 유지·경계: 표준 라이브러리만 사용, 기존 `tests/test_basic.py` 무수정 통과, 전역 `--store` 우선순위 유지. 동시성은 요구서 범위대로 version 비교만 하고 파일 잠금은 두지 않았다. add의 qty 범위 검증은 추가하지 않았다(현행 유지).

## 변경 파일

- `stockctl/store.py`
- `stockctl/cli.py`
- `tests/test_multiloc.py` (신규)
- `docs/CLI.md`

## 검증

- `python -m pytest -q tests/` → 13 passed (신규 11 + 기존 2), SHA a50af41 — opal-test-agent 독립 실행, 증거 `run/test-evidence/S-12-pytest.out`
- `test-tool scenario-status` → 14/14 pass, fail·blocked 0, RED 11/11 확인 후 잠금(구현 전 실패 관찰 기록)
- `git diff --exit-code main -- tests/test_basic.py` → 변경 없음
- 보안 검사(시크릿·위험 호출 grep, `.gitignore`) → 이상 없음
- 컨벤션 checker 최종 1회 → High 1·Medium 1 모두 오탐으로 판정(기존 `tests/test_basic.py:7`·`stockctl/__main__.py:7`과 같은 `"exports": []` 형식, `### history`는 명령 절) — `GC-CONVENTION-2026-10-02T00-10-00.md`
- PM 추가 재현: 헤더만 있는 CSV → `applied 0, rejected 0`·exit 0·파일 미생성, import 충돌 → exit 4·거부 파일 없음, 전부 거부 → exit 3·version 불변, 파일 없음 → exit 5

## 회고적 학습 후보

없음

## 참고

- 잔여 Minor(retain): import-csv qty 판정의 `str.isdigit()`는 위첨자 등 비ASCII 숫자를 통과시켜 `int()` 예외가 날 수 있다. 요구서 범위 밖 입력이라 이번에는 고치지 않았다.
- TEST-SCENARIO Setup의 개별 실행 표기 `-k s<N>`은 실제 테스트 이름(`test_s01_`~`test_s11_`)에 맞춰 두 자리로 실행해야 한다.
- merge는 사용자 승인 사항이다. 워크트리 `.opal-worktrees/task_001`(브랜치 `feat/OP-TASK-001`)는 머지 대기 상태다.
