# DONE: stockctl 재고 부족 품목 조회 (low-stock)

> 완료: 2026-09-26 10:30 | 모드: agentic | 스킬: //opsdd | 작성: PM(알투)

## 결과 요약
`stockctl low-stock --below N` 명령을 추가했다. 수량 N 미만 품목을 SKU 오름차순 `SKU\tQTY`로 출력(exit 0), 해당 없으면 무출력(exit 0), 정수 아님·0 이하 N은 stderr `invalid:` 한 줄 + exit 5. 저장소는 읽기만 한다. `docs/CLI.md`에 명령을 추가했다.

## TASK Acceptance criteria 판정 (E1 — 저장소 루트 `python3 -m pytest -q tests/` 30 passed + PM 블랙박스 CLI 실행)
| AC | 판정 | 근거 |
|---|---|---|
| AC-1 SKU 오름차순 `SKU\tQTY`, exit 0 | Pass | TS-01/09/10/14/15/16, E2E `--below 3` → `A\t1 B\t2 Z\t0` exit 0 |
| AC-2 해당 없음 무출력 exit 0 | Pass | TS-03/11/12, E2E 파일 부재 store → 무출력 exit 0 |
| AC-3 비정수 → `invalid:` 1줄 exit 5 | Pass | TS-04(abc/3.5/""/3.0/1e2), E2E `abc`·`3.5` |
| AC-4 0 이하 → `invalid:` 1줄 exit 5 | Pass | TS-05(0/`=-3`/`-3`), E2E `0`·`-3` |
| AC-5 저장소 바이트 불변 | Pass | TS-06/12/13/17, E2E 후 sha·mtime·디렉토리 목록 불변 |
| AC-6 기존 테스트 포함 전체 pytest 통과 | Pass | 30 passed (test_basic 2건 포함), E2E `list` 출력 정상 |
| AC-7 `docs/CLI.md` 명령 추가 | Pass | TS-08, `docs/CLI.md` low-stock 행(출력 형식·종료 코드 0/5) |

Constraints: C-1(저장소 무변경) Pass · C-2(기존 동작 유지) Pass · C-3(표준 라이브러리만) Pass — 신규 import 없음(json/os/subprocess/sys/pathlib/pytest는 테스트 한정) · C-4(컨벤션) Pass — @header validate ok, opal-convention-checker Critical/High/Medium 0.

## 변경 파일
- `stockctl/cli.py` — `_parse_below`, `cmd_low_stock`, `low-stock` 서브파서, @header description 갱신
- `tests/test_low_stock.py` — 신규 (28 테스트, TS-01~17)
- `docs/CLI.md` — low-stock 행 추가
- (태스크 메타) `.opal/MEMORY.json` last_task_number 0→1 (채번 도구), `tasks/001-low-stock/**`

## 산출물
TASK.md · SPEC.md · TEST-SCENARIOS.md(17/17 Green) · SPEC-PLAN.md · actions/ACT-001-low-stock-command/{PLAN,TEST,DONE}.md · GC-CONVENTION-2026-09-26T10-27-00.md · AGENTIC-LOG.md · STATE.md

## PM 결정 / 잔여 사항
- `--below` 누락 → argparse exit 2(기존 `--qty`와 동일, 요구서 미규정 영역).
- 정수 판정 = Python `int()` 규칙: `+3`, `03`, ` 3 `, `1_000`, 유니코드 10진 숫자도 유효.
- 한계: `--below -abc`처럼 음수 숫자 형태가 아닌 `-` 시작 값은 argparse가 옵션으로 해석해 exit 2(`--below=-abc`는 exit 5). 요구서 문구를 엄격히 적용하려면 후속 조정 필요.
- `test-tool unit --scope be`는 전역 mypy 미설치로 중단(환경 한계, 프로젝트 요구 아님).

## 회고 / 개선 후보
- PM 실수: SPEC 워커 행 소요 기록을 mark 시 누락했다가 사후 기록(3분). 워커 행은 `--as-worker --worker-stage --worker-duration-minutes`로 처음부터 기록할 것.
- 커밋·merge는 수행하지 않았다(사용자 승인 경계). 허브 작업본에 변경이 미커밋 상태로 남아 있다.
