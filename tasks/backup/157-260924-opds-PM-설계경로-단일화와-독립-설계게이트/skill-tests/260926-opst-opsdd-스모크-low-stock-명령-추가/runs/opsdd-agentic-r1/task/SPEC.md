# SPEC: stockctl 재고 부족 품목 조회 (low-stock)

> 버전: 1.0 | 작성일: 2026-09-26 | 상태: Draft
> TASK: tasks/001-low-stock/TASK.md
> 요구 원천: `../REQUEST.md` (사용자 지시: 요구서의 요구를 TASK 요구사항으로 그대로 사용)

## 1. Background (배경)

stockctl은 창고 재고를 JSON 파일(sku → {name, qty, location})로 관리하는 CLI이며, 현재 add/remove/list 세 명령을 제공한다(`docs/CLI.md`).

- AS-IS: 곧 떨어질 품목을 확인하려면 창고 담당자가 `stockctl list`로 전 품목(`SKU\tNAME\tLOCATION\tQTY`)을 출력한 뒤 수량을 직접 걸러야 한다. 이 작업은 품목 수에 비례해 느려지고 실수가 잦다.
- TO-BE: `stockctl low-stock --below N` 한 번으로 수량이 N 미만인 품목만 SKU 오름차순 `SKU\tQTY` 줄로 확인한다. 잘못된 N은 식별 가능한 오류(`invalid:`)와 전용 종료 코드 5로 거부된다. 조회는 저장소를 바꾸지 않으며, 명령 계약은 `docs/CLI.md`에 문서화된다.

## 2. Goals (목표)

- `stockctl low-stock --below N` 명령을 제공한다. 수량이 N 미만인 품목만 SKU 오름차순 `SKU\tQTY` 줄로 출력하고 exit 0으로 끝난다. (TASK AC-1)
- N 미만 품목이 없으면 아무것도 출력하지 않고 exit 0으로 끝난다. (TASK AC-2)
- 정수가 아니거나 0 이하인 N은 stderr `invalid:` 한 줄과 exit 5로 거부한다. (TASK AC-3, AC-4)
- low-stock은 저장소 파일을 읽기만 한다. 실행 결과(정상·빈 결과·오류)와 관계없이 저장소 바이트가 바뀌지 않고 새 파일도 생기지 않는다. (TASK AC-5, C-1)
- 기존 add/remove/list 명령과 기존 테스트가 그대로 동작한다. (TASK AC-6, C-2)
- `docs/CLI.md` 명령 표에 low-stock 명령, 출력 형식, 종료 코드(0/5)를 추가한다. (TASK AC-7)

## 3. Non-goals (비목표)

- `--below` 외 필터(위치·이름·SKU 패턴 등)나 "N 이하" 같은 다른 비교 연산 -- 요구서에 없다.
- 출력 포맷 옵션(JSON/CSV, 헤더 행, NAME·LOCATION 열 추가, 정렬 기준 변경) -- 요구서가 `SKU\tQTY`와 SKU 오름차순을 고정한다.
- 기본 임계값(`--below` 생략 시 기본 N) 도입 -- 요구서에 없다(누락 시 동작은 EC-12).
- 저장소 포맷(`stockctl/store.py` 데이터 구조) 변경 -- TASK "제외" 항목이다.
- 기존 add/remove/list 동작·종료 코드·오류 메시지 변경 -- TASK "제외" 항목이자 C-2 위반이다.
- 손상된(파싱 불가) 저장소 JSON에 대한 신규 오류 계약 -- 기존 명령에도 정의되어 있지 않은 범위다. 이번 태스크에서는 기존 명령과 같은 동작을 유지한다(A-2).
- 재고 보충·알림 같은 후속 조치 -- 조회 전용 명령이다.

## 4. User Stories (사용자 스토리)

- As a 창고 담당자, I want `stockctl low-stock --below N`으로 수량이 N 미만인 품목만 보고 싶다, so that 전 품목 목록을 직접 거르지 않고 보충 대상을 바로 파악할 수 있다.
- As a 창고 담당자, I want 잘못된 N을 넣었을 때 `invalid:` 오류와 전용 종료 코드를 받고 싶다, so that 결과가 비어서 없는 것인지 입력이 잘못된 것인지 구분할 수 있다.
- As a 스크립트로 stockctl을 호출하는 운영자, I want 조회 결과가 기계가 파싱하기 쉬운 `SKU\tQTY` 줄로 나오고 조회가 저장소를 바꾸지 않기를 원한다, so that 파이프라인에서 안전하게 반복 실행할 수 있다.

## 5. Functional Requirements (기능 요구사항)

- [FR-01] stockctl은 `low-stock` 서브커맨드를 제공하고, 필수 옵션 `--below N`으로 임계값 N을 받는다. 전역 옵션 `--store PATH`와 기존 저장소 경로 우선순위(`--store` > `STOCKCTL_STORE` > `stock.json`)를 그대로 따른다. (TASK AC-1)
- [FR-02] N이 1 이상의 정수이면 저장소에서 qty가 N보다 **엄격히 작은**(qty < N) 품목만 골라, SKU 오름차순으로 한 품목당 `SKU\tQTY` 한 줄(개행 종료)씩 stdout에 출력하고, stderr에는 아무것도 쓰지 않으며 exit 0으로 끝난다. (TASK AC-1)
- [FR-03] 조건에 맞는 품목이 하나도 없으면 stdout·stderr에 아무것도 출력하지 않고 exit 0으로 끝난다. (TASK AC-2)
- [FR-04] N이 정수로 해석되지 않으면 stdout에는 아무것도 쓰지 않고, stderr에 `invalid:`로 시작하는 정확히 한 줄을 쓰고 exit 5로 끝난다. (TASK AC-3)
- [FR-05] N이 정수이지만 0 이하이면 stdout에는 아무것도 쓰지 않고, stderr에 `invalid:`로 시작하는 정확히 한 줄을 쓰고 exit 5로 끝난다. (TASK AC-4)
- [FR-06] low-stock은 결과(정상·빈 결과·오류)와 관계없이 저장소 파일의 바이트를 바꾸지 않고, 저장소 경로와 같은 디렉토리에 어떤 파일(`*.tmp` 포함)도 새로 만들지 않는다. (TASK AC-5, C-1)
- [FR-07] 기존 add/remove/list 명령의 인자·출력·종료 코드·저장 동작이 변경 전과 같고, 기존 테스트(`tests/test_basic.py`)를 포함한 전체 pytest가 통과한다. (TASK AC-6, C-2)
- [FR-08] `docs/CLI.md` 명령 표에 `low-stock` 행을 추가해 명령 형식(`stockctl low-stock --below N`), 출력 형식(`SKU\tQTY` 줄, SKU 오름차순, qty < N), 종료 코드(0 성공·빈 결과, 5 잘못된 N)를 명시한다. (TASK AC-7)

## 6. Acceptance Criteria (수용 기준)

### AC-01: 임계값 미만 품목만 SKU 오름차순으로 출력
> 대응 FR: FR-01, FR-02

- **GIVEN**: `--store`로 지정한 저장소에 품목 `B`(qty 2), `A`(qty 1), `C`(qty 5), `D`(qty 3)가 있을 때
- **WHEN**: `python -m stockctl --store <path> low-stock --below 3`을 실행하면
- **THEN**: stdout이 정확히 `A\t1\nB\t2\n`이고, stderr는 비어 있으며, exit code는 0이다 (qty 3인 `D`와 qty 5인 `C`는 출력되지 않는다)

### AC-02: 저장소 경로 우선순위 준수
> 대응 FR: FR-01

- **GIVEN**: `--store` 없이 환경변수 `STOCKCTL_STORE`가 qty 1인 품목 `X`를 가진 저장소를 가리킬 때
- **WHEN**: `python -m stockctl low-stock --below 2`를 실행하면
- **THEN**: stdout이 `X\t1\n`이고 exit code는 0이다

### AC-03: 해당 품목이 없으면 무출력 exit 0
> 대응 FR: FR-03

- **GIVEN**: 저장소의 모든 품목 qty가 5 이상일 때
- **WHEN**: `python -m stockctl --store <path> low-stock --below 5`를 실행하면
- **THEN**: stdout과 stderr가 모두 비어 있고 exit code는 0이다

### AC-04: 정수가 아닌 N 거부
> 대응 FR: FR-04

- **GIVEN**: 품목이 있는 저장소가 있을 때
- **WHEN**: `--below` 값으로 `abc`, `3.5`, `""`(빈 문자열) 중 하나를 주어 low-stock을 실행하면
- **THEN**: 각 경우 stdout은 비어 있고, stderr는 `invalid:`로 시작하는 정확히 한 줄이며, exit code는 5다

### AC-05: 0 이하 N 거부
> 대응 FR: FR-05

- **GIVEN**: 품목이 있는 저장소가 있을 때
- **WHEN**: `--below 0` 또는 `--below=-3`으로 low-stock을 실행하면
- **THEN**: 각 경우 stdout은 비어 있고, stderr는 `invalid:`로 시작하는 정확히 한 줄이며, exit code는 5다

### AC-06: 저장소 무변경 (정상·빈 결과·오류)
> 대응 FR: FR-06

- **GIVEN**: 저장소 파일의 실행 전 바이트와 저장소 디렉토리의 파일 목록을 기록해 두었을 때
- **WHEN**: low-stock을 정상 결과(AC-01), 빈 결과(AC-03), 오류(AC-04·AC-05 입력) 조건으로 각각 실행하면
- **THEN**: 매번 실행 후 저장소 파일 바이트가 실행 전과 같고, 디렉토리에 새 파일(`*.tmp` 포함)이 생기지 않는다

### AC-07: 기존 명령 회귀 없음
> 대응 FR: FR-07

- **GIVEN**: low-stock이 추가된 코드베이스일 때
- **WHEN**: 저장소 루트에서 전체 pytest를 실행하면
- **THEN**: `tests/test_basic.py`를 포함한 모든 테스트가 통과하고, add/remove/list의 기존 출력·종료 코드(remove 1·2 포함)가 변경 전과 같다

### AC-08: CLI 계약 문서화
> 대응 FR: FR-08

- **GIVEN**: 변경 후 `docs/CLI.md`가 있을 때
- **WHEN**: 명령 표를 확인하면
- **THEN**: `low-stock --below N` 행이 있고, 그 행에 출력 형식 `SKU\tQTY`(SKU 오름차순, qty < N)와 종료 코드 0(성공·빈 결과)·5(잘못된 N)가 적혀 있으며, 기존 add/remove/list 행과 저장소 경로 문구는 유지된다

## 7. Edge Cases (엣지 케이스)

- [EC-01] qty가 N과 같은 품목 -- 출력하지 않는다("미만"은 엄격 비교).
- [EC-02] qty가 0인 품목 -- N ≥ 1이면 항상 출력한다(`SKU\t0`).
- [EC-03] `--below 1` -- qty가 0인 품목만 출력한다(최소 유효 N).
- [EC-04] 저장소가 비어 있음(`{"items": {}}`) -- 무출력, exit 0 (FR-03).
- [EC-05] 저장소 파일이 존재하지 않음 -- 빈 저장소로 간주해 무출력 exit 0이며, 파일을 만들지 않는다 (A-1, FR-06).
- [EC-06] 잘못된 N과 저장소 상태의 조합(저장소 부재·비어 있음 포함) -- 저장소 상태와 관계없이 exit 5와 `invalid:` 한 줄이다.
- [EC-07] 음수 N을 공백 구분으로 전달(`--below -3`) -- 옵션이 아닌 값으로 받아들여 0 이하 규칙에 따라 exit 5와 `invalid:` 한 줄이다. 값이 argparse 옵션으로 잘못 해석되어 exit 2/usage로 끝나면 안 된다.
- [EC-08] 소수·지수 표기(`3.0`, `1e2`) -- 정수가 아니므로 exit 5와 `invalid:` 한 줄이다.
- [EC-09] 매우 큰 정수 N(예: `99999999999999999999`) -- 정수이자 1 이상이므로 유효하며, 이 경우 모든 품목이 출력된다.
- [EC-10] SKU 정렬 -- 파이썬 문자열 기본 순서(코드 포인트 사전순) 오름차순이며 기존 `list`의 정렬과 같다. 예: `A10`이 `A2`보다 먼저 나온다.
- [EC-11] `+3`, ` 3 `, `03` 같은 부호·공백·선행 0 표기 -- 정수 판정 규칙(A-3)에 따라 유효한 정수로 받는다. 값이 1 이상이면 정상 조회한다. 예: `--below +3`, `--below 03`, `--below " 3 "`은 모두 `--below 3`과 같은 stdout을 내고 exit 0이다. 같은 규칙에 따라 `1_000`도 1000으로 받는다.
- [EC-12] `--below` 누락(`stockctl low-stock`) -- 기존 `--qty` 누락과 같이 argparse 필수 인자 오류(exit 2, usage 출력)로 끝난다. 이 경우는 N "값"의 유효성 문제가 아니라 CLI 사용 오류이므로 low-stock의 exit 5/`invalid:` 계약(FR-04, FR-05, NFR-02) 대상이 아니다. 이때도 저장소는 바뀌지 않는다(FR-06).

## 8. Non-functional Requirements (비기능 요구사항)

- [NFR-01] 읽기 전용 안전성: low-stock은 저장소에 대한 쓰기(임시 파일 포함)를 전혀 하지 않는다. 동시에 실행 중인 add/remove의 원자 교체(`os.replace`)를 방해하지 않는다. AC-06으로 검증한다.
- [NFR-02] 오류 출력 규약: 잘못된 N 값으로 인한 low-stock 오류(FR-04, FR-05)는 stderr 정확히 한 줄(개행 1개)이다. 파이썬 traceback이나 argparse usage 여러 줄을 출력하지 않는다(`docs/CONVENTIONS.md`). AC-04·AC-05로 검증한다. `--below` 누락(EC-12)은 기존 CLI 사용 오류 관례를 따르므로 이 규약 대상이 아니다.
- [NFR-03] (삭제: 요구서 범위 외)
- [NFR-04] 기계 가독성: 출력 줄에 헤더·장식·후행 공백이 없다. 필드 구분은 탭 1개, 줄 끝은 `\n`이며 인코딩은 기존 `list` 출력과 같다.
- [NFR-05] 이식성: Python 3 표준 라이브러리만으로 동작한다. 새 런타임 의존성이나 설치 절차를 추가하지 않는다.

## 9. Constraints (제약)

### 기술·정책 제약
- C-1 (TASK): 저장소 파일은 읽기만 한다. 실행 전후 바이트가 같고 새 파일(`*.tmp` 포함)이 없어야 한다. → FR-06, NFR-01
- C-2 (TASK): 기존 명령(add/remove/list)과 기존 테스트(`tests/test_basic.py`)는 그대로 동작해야 한다. → FR-07
- C-3 (TASK, `.opal/AGENT.md` 금지사항, `docs/CONVENTIONS.md`): 외부 패키지 추가 금지, Python 3 표준 라이브러리만 사용한다. → NFR-05
- C-4 (TASK, `docs/CONVENTIONS.md`): 소스 @header(module/layer/domain/description/exports)를 유지·갱신한다. 오류는 stderr 한 줄 + 종료 코드로 구분한다. 테스트는 `tests/`에 pytest로 작성하고 CLI는 `python -m stockctl`로 호출한다. → FR-04, FR-05, NFR-02
- 종료 코드 5는 low-stock의 잘못된 N 전용이다. 기존 코드(0, remove의 1·2)와 겹치지 않는다.

### 통합 포인트 (기존 시스템)
- `stockctl/cli.py`의 argparse 서브커맨드 구조(`build_parser()`/`main()`)에 새 서브커맨드로 합류한다. 전역 `--store`와 `store.store_path()` 경로 결정을 공유한다.
- 저장소 읽기는 기존 `store.load` 계약을 따른다. 파일이 없으면 `{"items": {}}`를 반환하고 파일을 만들지 않는다(`stockctl/store.py:19-23`). 쓰기는 `store.save`만 하며(`stockctl/store.py:26-30`, `.tmp` 생성 후 `os.replace`), low-stock은 이 경로를 호출하면 안 된다.
- `docs/CLI.md` 명령 표 형식(명령 | 설명 | 종료 코드)에 맞춰 행을 추가한다.

### 리스크 (DESIGN 입력)
- R-1: 기존 `--qty`는 argparse `type=int`로 파싱되고, argparse 파싱 오류는 exit 2와 usage 여러 줄을 낸다(`stockctl/cli.py:56,62,69-70`). `--below`의 비정수 값을 같은 방식으로 받으면 FR-04(exit 5, `invalid:` 한 줄)를 위반한다. 음수 값의 옵션 오인(EC-07)도 같은 위험이다. 따라서 N 검증은 argparse type 변환 실패 경로에 맡기지 않는 형태여야 한다. 구체적인 방식은 DESIGN에서 정한다.

### 가정 (Assumptions -- REVIEW에서 PM 확인)
- A-1: 저장소 파일이 없으면 기존 `store.load` 동작대로 빈 저장소로 간주해 무출력 exit 0으로 끝내고, 파일을 만들지 않는다. 근거: 요구서의 "해당 품목이 없으면 아무것도 출력하지 않고 exit 0", C-1, 기존 `list` 동작과의 일관성.
- A-2: 저장소 JSON이 손상된 경우의 동작은 이번 범위에서 새로 정의하지 않는다. 기존 명령과 같은 동작을 유지한다(Non-goals).
- A-3 (확정): Python `int()`가 10진으로 변환에 성공하는 문자열은 정수다. 따라서 `+3`, ` 3 `, `03`은 유효하다(EC-11). 변환에 실패하는 문자열(`abc`, `3.5`, `3.0`, `1e2`, 빈 문자열 등)은 정수가 아니며 exit 5다(FR-04, EC-08).

## 10. Open Questions (미결 사항)

- 없음 (OQ-01/02 PM 확정 2026-09-26 -- EC-11, EC-12, A-3에 반영)
