# Test Scenarios: stockctl 재고 부족 품목 조회 (low-stock)

> 버전: 1.0 | 작성일: 2026-09-26 | SPEC.md v1.0 기준 (OQ-01/02 PM 확정본)
> 상태: Green — VERIFY 2026-09-26 10:30 (`python3 -m pytest -q tests/` 30 passed + PM 블랙박스 CLI E2E, 담당 ACT: 전부 ACT-001)
> 공통 실행 방식: `subprocess.run([sys.executable, "-m", "stockctl", "--store", <tmp>/s.json, ...])` (`docs/CONVENTIONS.md`: "CLI는 `python -m stockctl`로 호출한다", 기존 `tests/test_basic.py:15-17` 패턴). 저장소 픽스처는 테스트가 JSON(`{"items": {sku: {"name", "qty", "location"}}}`, `stockctl/store.py:5-6`)을 직접 기록해 만든다.

## 추적 매트릭스

| AC/EC | FR | 시나리오 ID | 유형 | 설명 | 상태 |
|----|----|-----------|------|------|------|
| AC-01 | FR-01, FR-02 | TS-01 | e2e | qty < N 품목만 SKU 오름차순 `SKU\tQTY`, stderr 빈, exit 0 | Green |
| AC-02 | FR-01 | TS-02 | integration | `--store` 없이 `STOCKCTL_STORE` 경로 사용 | Green |
| AC-03 | FR-03 | TS-03 | e2e | 해당 품목 없음 → stdout·stderr 빈, exit 0 | Green |
| AC-04, EC-08 | FR-04 | TS-04 | e2e | 비정수 N(`abc`,`3.5`,`""`,`3.0`,`1e2`) → `invalid:` 1줄, exit 5 | Green |
| AC-05, EC-07 | FR-05 | TS-05 | e2e | 0 이하 N(`0`,`--below=-3`,`--below -3`) → `invalid:` 1줄, exit 5 | Green |
| AC-06 | FR-06 | TS-06 | integration | 정상/빈/오류 실행 후 저장소 바이트 동일·새 파일 없음 | Green |
| AC-07 | FR-07 | TS-07 | integration | 전체 pytest(기존 `tests/test_basic.py` 포함) 통과 | Green |
| AC-08 | FR-08 | TS-08 | unit | `docs/CLI.md`에 low-stock 행·출력 형식·종료 코드 0/5, 기존 행 유지 | Green |
| EC-01 | FR-02 | TS-09 | e2e | qty == N 품목은 출력 제외 | Green |
| EC-02, EC-03 | FR-02 | TS-10 | e2e | `--below 1` → qty 0 품목만 `SKU\t0` 출력 | Green |
| EC-04 | FR-03 | TS-11 | e2e | 빈 저장소 `{"items": {}}` → 무출력 exit 0 | Green |
| EC-05 | FR-03, FR-06 | TS-12 | integration | 저장소 파일 부재 → 무출력 exit 0, 파일 미생성 | Green |
| EC-06 | FR-04, FR-05, FR-06 | TS-13 | e2e | 저장소 부재/빈 상태 + 잘못된 N → exit 5, 파일 미생성 | Green |
| EC-09 | FR-02 | TS-14 | e2e | 매우 큰 N(`99999999999999999999`) → 전 품목 출력 exit 0 | Green |
| EC-10 | FR-02 | TS-15 | e2e | SKU 정렬은 문자열 사전순(`A10` < `A2`), `list`와 동일 순서 | Green |
| EC-11 | FR-02 | TS-16 | e2e | `+3`,`03`,`" 3 "` → `--below 3`과 동일 stdout, `1_000` → 1000 | Green |
| EC-12 | FR-01, FR-06 | TS-17 | e2e | `--below` 누락 → argparse exit 2, 저장소 무변경 | Green |

## 시나리오 상세

### TS-01: 임계값 미만 품목만 SKU 오름차순 출력
- **출처**: AC-01 (FR-01, FR-02)
- **유형**: e2e
- **GIVEN**: 저장소에 `B`(qty 2), `A`(qty 1), `C`(qty 5), `D`(qty 3)
- **WHEN**: `low-stock --below 3`
- **THEN**: stdout == `"A\t1\nB\t2\n"`, stderr == `""`, returncode == 0
- **테스트 케이스**: 정상: 위 입력 / 경계값: qty 3(`D`)=N 제외 (TS-09와 교차)
- **검증 방법**: 자동, pytest + subprocess
- **담당 ACT**: ACT-001
- **상태**: Green

### TS-02: 환경변수 저장소 경로 사용
- **출처**: AC-02 (FR-01)
- **유형**: integration
- **GIVEN**: `STOCKCTL_STORE`=qty 1 품목 `X`를 가진 저장소 경로, `--store` 미지정
- **WHEN**: `python -m stockctl low-stock --below 2` (env 주입)
- **THEN**: stdout == `"X\t1\n"`, returncode == 0
- **검증 방법**: 자동, pytest + subprocess(env)
- **담당 ACT**: ACT-001
- **상태**: Green

### TS-03: 해당 품목 없음
- **출처**: AC-03 (FR-03)
- **유형**: e2e
- **GIVEN**: 모든 품목 qty ≥ 5 (예: `A` 5, `B` 9)
- **WHEN**: `low-stock --below 5`
- **THEN**: stdout == `""`, stderr == `""`, returncode == 0
- **검증 방법**: 자동
- **담당 ACT**: ACT-001
- **상태**: Green

### TS-04: 정수가 아닌 N 거부
- **출처**: AC-04, EC-08 (FR-04)
- **유형**: e2e
- **GIVEN**: 품목이 있는 저장소
- **WHEN**: `--below` 값이 각각 `abc`, `3.5`, `""`, `3.0`, `1e2` (parametrize)
- **THEN**: 각 경우 stdout == `""`, stderr가 `invalid:`로 시작하고 개행으로 끝나는 정확히 1줄(`stderr.count("\n") == 1`), returncode == 5, `usage:`/`Traceback` 미포함
- **검증 방법**: 자동
- **담당 ACT**: ACT-001
- **상태**: Green

### TS-05: 0 이하 N 거부
- **출처**: AC-05, EC-07 (FR-05)
- **유형**: e2e
- **GIVEN**: 품목이 있는 저장소
- **WHEN**: 인자 형태 각각 `["--below", "0"]`, `["--below=-3"]`, `["--below", "-3"]` (parametrize)
- **THEN**: 각 경우 stdout == `""`, stderr `invalid:` 시작 정확히 1줄, returncode == 5 (특히 `--below -3`이 argparse exit 2로 끝나지 않음)
- **검증 방법**: 자동
- **담당 ACT**: ACT-001
- **상태**: Green

### TS-06: 저장소 무변경 (정상·빈 결과·오류)
- **출처**: AC-06 (FR-06, NFR-01)
- **유형**: integration
- **GIVEN**: 저장소 파일 바이트와 저장소 디렉토리 파일 목록을 실행 전 기록
- **WHEN**: 정상(`--below 3`), 빈 결과(`--below 1`, qty 0 품목 없음), 오류(`--below abc`, `--below 0`) 각각 실행
- **THEN**: 매 실행 후 파일 바이트 동일, 디렉토리 파일 목록 동일(`*.tmp` 등 신규 없음), mtime 불변
- **검증 방법**: 자동
- **담당 ACT**: ACT-001
- **상태**: Green

### TS-07: 기존 명령 회귀 없음
- **출처**: AC-07 (FR-07, C-2)
- **유형**: integration
- **GIVEN**: low-stock이 추가된 코드베이스
- **WHEN**: 저장소 루트에서 `python -m pytest -q` (디렉토리 스코프 `tests/`)
- **THEN**: `tests/test_basic.py` 2건 포함 전체 통과, 실패 0
- **검증 방법**: 자동 (pytest 실행 로그를 증거로 기록)
- **담당 ACT**: ACT-001
- **상태**: Green

### TS-08: CLI 계약 문서화
- **출처**: AC-08 (FR-08)
- **유형**: unit
- **GIVEN**: 변경 후 `docs/CLI.md`
- **WHEN**: 명령 표를 읽음 (pytest에서 파일 내용 검사)
- **THEN**: `low-stock --below N` 포함 행 존재, 그 행에 `SKU\tQTY`와 종료 코드 `0`·`5` 표기, 기존 add/remove/list 행과 저장소 경로 문구(`--store` > `STOCKCTL_STORE` > `stock.json`) 유지
- **검증 방법**: 자동(파일 검사) + PM 육안 확인
- **담당 ACT**: ACT-001
- **상태**: Green

### TS-09: qty == N 제외
- **출처**: EC-01 (FR-02)
- **유형**: e2e
- **GIVEN**: `A` qty 3, `B` qty 2
- **WHEN**: `low-stock --below 3`
- **THEN**: stdout == `"B\t2\n"`, exit 0
- **담당 ACT**: ACT-001 · **상태**: Green

### TS-10: `--below 1`은 qty 0 품목만
- **출처**: EC-02, EC-03 (FR-02)
- **유형**: e2e
- **GIVEN**: `Z` qty 0, `A` qty 1
- **WHEN**: `low-stock --below 1`
- **THEN**: stdout == `"Z\t0\n"`, exit 0
- **담당 ACT**: ACT-001 · **상태**: Green

### TS-11: 빈 저장소
- **출처**: EC-04 (FR-03)
- **유형**: e2e
- **GIVEN**: 저장소 내용 `{"items": {}}`
- **WHEN**: `low-stock --below 10`
- **THEN**: stdout·stderr 빈, exit 0
- **담당 ACT**: ACT-001 · **상태**: Green

### TS-12: 저장소 파일 부재
- **출처**: EC-05 (FR-03, FR-06)
- **유형**: integration
- **GIVEN**: `--store`가 존재하지 않는 경로를 가리킴, 디렉토리 비어 있음
- **WHEN**: `low-stock --below 10`
- **THEN**: stdout·stderr 빈, exit 0, 실행 후 해당 경로·디렉토리에 파일 미생성
- **담당 ACT**: ACT-001 · **상태**: Green

### TS-13: 잘못된 N × 저장소 부재/빈 상태
- **출처**: EC-06 (FR-04, FR-05, FR-06)
- **유형**: e2e
- **GIVEN**: (a) 저장소 파일 부재, (b) `{"items": {}}`
- **WHEN**: 각각 `--below abc`, `--below 0`
- **THEN**: 모두 stdout 빈, stderr `invalid:` 1줄, exit 5; (a)에서 파일 미생성
- **담당 ACT**: ACT-001 · **상태**: Green

### TS-14: 매우 큰 N
- **출처**: EC-09 (FR-02)
- **유형**: e2e
- **GIVEN**: `A` qty 1, `B` qty 1000000
- **WHEN**: `low-stock --below 99999999999999999999`
- **THEN**: stdout == `"A\t1\nB\t1000000\n"`, exit 0
- **담당 ACT**: ACT-001 · **상태**: Green

### TS-15: SKU 사전순 정렬
- **출처**: EC-10 (FR-02)
- **유형**: e2e
- **GIVEN**: `A2` qty 1, `A10` qty 1, `a1` qty 1
- **WHEN**: `low-stock --below 5`
- **THEN**: stdout == `"A10\t1\nA2\t1\na1\t1\n"` (파이썬 `sorted()` 순서, `list` SKU 순서와 동일), exit 0
- **담당 ACT**: ACT-001 · **상태**: Green

### TS-16: 부호·공백·선행 0·밑줄 표기 수용
- **출처**: EC-11 (FR-02, SPEC A-3)
- **유형**: e2e
- **GIVEN**: TS-01과 같은 저장소
- **WHEN**: `--below` 값 `+3`, `03`, `" 3 "` 각각; 추가로 `1_000`
- **THEN**: 앞 3건 stdout == `--below 3` 결과(`"A\t1\nB\t2\n"`), exit 0; `1_000`은 전 품목(qty < 1000) 출력, exit 0
- **담당 ACT**: ACT-001 · **상태**: Green

### TS-17: `--below` 누락
- **출처**: EC-12 (FR-01, FR-06)
- **유형**: e2e
- **GIVEN**: 품목이 있는 저장소(바이트 기록)
- **WHEN**: `low-stock` (옵션 없음)
- **THEN**: returncode == 2 (argparse 필수 인자 오류), stdout 빈, 저장소 바이트 동일
- **담당 ACT**: ACT-001 · **상태**: Green
