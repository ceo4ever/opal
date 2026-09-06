# TASK: memory-tool 참조 무결성 검사 + 본문 부재 행 고착 해소

> 작성일: 2026-08-20 | 작업 유형: 개선 | 적용 스킬: opds | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

`memory-tool`이 인덱스 행과 본문 파일의 불일치를 **검출하지 못하고**, 불일치가 발생한 행은 어떤 정리 명령으로도 **제거할 수 없는** 고착 상태에 빠지는 문제를 해소한다. 아울러 규범 문서의 라이프사이클 표를 스키마와 정합시킨다.

## 배경

`.opal/MEMORY.json` 정리 작업 중 인덱스 행 10건 중 7건이 본문 `.md` 파일 없이 존재하는 상태가 발견됐다. 인덱스는 커밋 대상이나 본문은 대부분 미커밋이어서, 다른 머신에서 클론하면 **인덱스만 있고 지식은 없는** 상태가 된다.

문제는 검출·정리 두 층 모두에서 막힌다는 점이다. `review`는 참조 무결성을 검사하지 않아 불일치를 끝까지 표면화하지 못했고, 발견 후 정리하려 하자 `promote`와 `delete`의 가드가 조합되어 해당 행에 도달할 수 있는 명령이 하나도 없었다.

## 배경 분석 (대화에서 도출)

### (1) 검출 공백 — `review`에 참조 무결성 검사 없음

`build_review_block()`(`opal/tools/memory-tool/memory_tool.py:828-870`)이 수행하는 행 단위 검사는 4종이다.

| 검사 | 조건 | 근거 |
|------|------|------|
| `invalid_status` | `status not in VALID_STATUSES` | `memory_tool.py:846` |
| `invalid_type` | `rtype not in VALID_TYPES` | `memory_tool.py:848` |
| `summary_too_long` | `len(summary) > SUMMARY_MAX_LENGTH` | `memory_tool.py:850` |
| `title_too_long` | `len(title) > TITLE_MAX_LENGTH` | `memory_tool.py:852` |

`row["file"]`이 가리키는 경로의 **실재 여부를 검사하는 분기가 없다**. 실측에서 본문 부재 5건이 있는 상태로 `review`를 호출했으나 반환된 violations는 `title_too_long` 3건뿐이었다.

### (2) 정리 공백 — 두 가드의 조합이 사각지대를 만든다

| 명령 | 가드 | 본문 부재 행에 대한 결과 |
|------|------|------------------------|
| `promote` | 본문 `.md` 존재 필수 (`memory_tool.py:1166-1168`) | `memory_file_not_found` **거부** |
| `delete` | `status`가 `dead`/`superseded`인 행만 허용 (`memory_tool.py:1331`) | `active`/`promoted`/`candidate` **거부** |

두 가드 각각은 무손실 원칙상 옳다. 그러나 조합하면 **본문이 없고 상태가 `dead`/`superseded`가 아닌 행은 어떤 명령으로도 정리할 수 없다**. 실측에서 `promote` 3건을 시도해 3건 전부 `memory_file_not_found`로 거부됐다.

우회는 상태를 임의 조작(`update --status superseded`)하는 것뿐이며, 이는 감사 추적을 오염시킨다. 실제로 이번 정리는 지식 귀착처를 개별 실증한 뒤에야 이 우회를 캡틴 승인 하에 사용했다.

### (3) 문서 공백 — 라이프사이클 표에 `candidate` 누락

스키마의 `status` enum은 5종이다(`opal/tools/memory-tool/schema/memory.schema.json:54` — `["active", "promoted", "superseded", "dead", "candidate"]`). 그러나 규범 문서의 라이프사이클 표(`opal/core/references/harness/memory-learning.md:31-36`)는 `active`/`promoted`/`superseded`/`dead` **4종만** 기재한다.

`candidate`는 코드 상 유효 상태이고 실제 데이터에도 존재하는데, PM이 그 상태를 만났을 때 의미·진입 트리거·도구 동작을 판단할 규범 근거가 없다.

## 확정된 설계 방향 (대화에서 합의)

- **D-1**: 세 결함을 하나의 태스크로 묶는다. (1)(2)는 같은 사각지대의 검출층·정리층이고, (3)은 그 사각지대에 남는 상태값의 규범 근거이므로 분리하면 반쪽 처방이 된다.
- **D-2**: 상태를 임의 조작해 삭제를 강행하는 방식은 정식 경로로 채택하지 않는다. 감사 추적 오염 대비 이득이 없다.
- **D-3**: 배포는 TEST 전건 통과 이후에 수행한다. 검증 미완 규칙이 전역 홈으로 퍼지는 창을 만들지 않는다(095 확정 사항 계승 — `opal/core/references/harness/red-first.md` §1.6).

## 명확화 결과

> TASK 4요소를 잠근다. 각 요소는 확정값 또는 명시적 "N/A: <사유>"로 채운다 (공란·TBD 금지).

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | `memory-tool`이 인덱스↔본문 불일치를 검출하고, 불일치 행을 정식 경로로 정리할 수 있게 한다. 라이프사이클 규범 문서를 스키마와 정합시킨다. | - | `memory_tool.py:828-870` / `:1166-1168` / `:1331` |
| 범위 | **포함** — `memory_tool.py`(review 검사 추가 + 고착 해소 경로), `tests/test_memory_tool.py`(신규 시나리오), `memory-learning.md`(라이프사이클 표 + 필요 시 절차 서술), 변경이력. **제외** — 누락된 본문 `.md` 5건의 복원(작성 머신 접근 필요, 별건), 다른 도구(`state-tool`·`brain-tool`)의 동종 검사, `MEMORY.json` 스키마 변경. | R-2 구현 방식 3안 중 택일 → PLAN | `.opal/MEMORY.json` 실측 (참조 3 / 실재 1 / 누락 2) |
| 제약 | (1) `~/.opal/` 직접 편집 금지 — 프로젝트 소스 수정 후 install. (2) 무손실 원칙 유지 — 살아있는 지식의 blind 삭제 경로를 새로 만들지 않는다. (3) 기존 테스트 3100줄 회귀 0. (4) `MEMORY.json` 스키마 무변경. (5) 변경 문서 변경이력에 096 행 추가. (6) install은 TEST 전건 통과 후. | - | `.opal/AGENT.md` §금지사항 / `memory-learning.md:24` |
| 완료기준 | (1) 본문 부재 행이 `review` violations에 검출된다. (2) 본문 부재 행이 상태 임의 조작 없이 정식 명령으로 정리된다. (3) 라이프사이클 표가 스키마 enum 5종과 일치한다. (4) `pytest opal/tools/memory-tool` 전건 GREEN. (5) 실환경 `.opal/MEMORY.json` 잔존 2건에 새 경로가 실동작한다. (6) install 후 배포본과 소스 diff 0. | - | R-1~R-3 AC |

## 요구사항

- [ ] **R-1** `review` 참조 무결성 검사 추가
  - 무엇을: `build_review_block()`에 인덱스 행의 `file` 경로 실재 여부 검사를 추가
  - 어디에: `opal/tools/memory-tool/memory_tool.py` `build_review_block()`
  - 왜: 본문 부재 5건이 있는 상태에서 `review`가 이를 표면화하지 못했다 (배경 분석 (1))
  - AC: 본문 `.md`가 없는 인덱스 행이 1건 이상이면 `review` 응답에 해당 행을 식별하는 항목이 반환되고, 본문이 전건 실재하면 해당 항목이 0건이다. 기존 violations 4종의 반환 형태는 불변이다.

- [ ] **R-2** 본문 부재 행 고착 해소
  - 무엇을: 본문 `.md`가 없는 인덱스 행을 상태 임의 조작 없이 정리할 수 있는 정식 경로를 제공
  - 어디에: `opal/tools/memory-tool/memory_tool.py` (구현 방식은 PLAN에서 결정 — 미확정 ①)
  - 왜: `promote` 본문 존재 요구와 `delete` 상태 가드가 조합되어 도달 불가 행이 발생한다 (배경 분석 (2))
  - AC: `status`가 `candidate` 또는 `promoted`이고 본문이 없는 행에 대해, `update --status`를 거치지 않고 단일 명령으로 인덱스 행이 제거되며, 응답에 제거 사유와 지식 귀착처가 기록된다. 본문이 **존재하는** 행에 같은 명령을 적용하면 거부되어 기존 무손실 가드가 우회되지 않는다.

- [ ] **R-3** 라이프사이클 규범 문서 정합
  - 무엇을: 라이프사이클 표에 `candidate` 행을 추가하고, R-2가 신설한 경로를 절차에 반영
  - 어디에: `opal/core/references/harness/memory-learning.md` §메모리 라이프사이클
  - 왜: 스키마 enum은 5종인데 규범 표는 4종이라 `candidate` 상태의 판단 근거가 없다 (배경 분석 (3))
  - AC: 표에 `candidate` 행이 존재하고 의미·진입 트리거·도구 동작 3열이 채워진다. 표의 상태 값 집합이 `memory.schema.json:54` enum과 문자 단위로 일치한다. 기존 4행의 서술은 R-2 반영분 외 diff 0이다.

- [ ] **R-4** 검증·배포
  - 무엇을: 신규 시나리오 테스트 추가 + 전건 회귀 확인 + install 재배포
  - 어디에: `opal/tools/memory-tool/tests/test_memory_tool.py`, `scripts/install-mac.sh` 실행
  - 왜: 도구 코드 변경은 self-confirming 위험 영역이므로 RED 증거 없이 완료 판정할 수 없다 (`opal/core/references/harness/red-first.md`)
  - AC: R-1·R-2 각각에 대해 변경 전 FAIL / 변경 후 PASS를 보이는 시나리오가 존재한다. `pytest opal/tools/memory-tool` 전건 GREEN. install 후 `~/.opal/tools/memory-tool/memory_tool.py`와 프로젝트 소스의 diff가 0이다.

## 미확정 사항 (PLAN에서 결정)

| # | 항목 | 후보 | 판단 기준 |
|---|------|------|----------|
| ① | R-2 구현 방식 | (a) `promote`에 본문 부재 허용 플래그 추가 (b) `delete` 상태 가드를 "본문 부재 시 예외" 조건으로 완화 (c) 신규 서브명령 신설 | 무손실 가드를 약화시키지 않으면서 명령 수를 늘리지 않는 쪽. `PRINCIPLES.md` §2 Simplicity |
| ② | R-1 검출 결과의 심각도 | (a) `violations`(결함) (b) `cleanup_candidates`(권고) (c) 신규 배열 | 본문 부재가 "데이터 결함"인지 "정리 대기"인지의 성격 판정. 기존 두 배열의 의미 경계를 침범하지 않을 것 |

## 제약 조건

- **배포 경계**: `~/.opal/` 직접 편집 금지. 프로젝트 소스(`opal/`) 수정 후 `scripts/install-mac.sh`로 재배포 — [MUST] `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다."
- **무손실 원칙 유지**: [MUST] `opal/core/references/harness/memory-learning.md:24`: "메모리(지식)는 **blind 삭제 금지** — 갯수 상한을 두지 않는 대신, 성숙한 지식은 `promote`로 영구 거처(docs/brain)로 졸업한 뒤 삭제하고, 진부화는 `dead`/`superseded` 전이 후 자가검토(`review`)로 정리한다(데이터 무손실)."
- **회귀 0**: 기존 `tests/test_memory_tool.py` 3100줄 전건 GREEN 유지.
- **스키마 무변경**: `memory.schema.json`의 `status` enum·필드 구성을 바꾸지 않는다. 이번 결함은 스키마가 아니라 코드·문서의 정합 문제다.
- **변경이력 의무**: 수정한 규범 문서 변경이력 표에 KST 일시 + `(096)` 행 추가 — [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무.
- **install 순서**: TEST 전건 통과 이후에만 실행한다.

## 기술 스택

- Python 3.14 (`~/.opal/.venv`) — `memory_tool.py` 단일 파일 CLI
- pytest 9.1.0 — `opal/tools/memory-tool/tests/test_memory_tool.py` (3100줄)
- JSON Schema — `opal/tools/memory-tool/schema/memory.schema.json`

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | memory-tool 본체 | `opal/tools/memory-tool/memory_tool.py` | R-1·R-2 변경 대상. `:828-870` review / `:1166-1168` promote 가드 / `:1331` delete 가드 |
| D-2 | 소스 | memory-tool 테스트 | `opal/tools/memory-tool/tests/test_memory_tool.py` | R-4 신규 시나리오 추가 + 회귀 기준선 |
| D-3 | 설계 | 메모리 스키마 | `opal/tools/memory-tool/schema/memory.schema.json` | `:54` status enum 5종 — R-3 정합 기준 |
| D-4 | 설계 | 기억과 학습 규범 | `opal/core/references/harness/memory-learning.md` | R-3 변경 대상. `:24` 무손실 원칙 / `:29-38` 라이프사이클 |
| D-5 | 설계 | RED-first 규칙 | `opal/core/references/harness/red-first.md` | R-4 RED 증거 의무 + §1.6 배포 순서 |
| D-6 | 설계 | PM 프로필 | `.opal/AGENT.md` | 배포 경계·변경이력 금지사항 |
| D-7 | 설계 | 컨벤션 | `docs/CONVENTIONS.md` | 변경이력 작성 의무 |
