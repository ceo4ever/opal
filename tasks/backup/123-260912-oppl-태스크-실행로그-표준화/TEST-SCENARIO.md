---
template: sdlc-v2
---
# TEST-SCENARIO: 태스크 실행 로그 — 기록 기반 완성

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: 워크트리 `/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_123`, Python 표준 실행 환경, pytest. 검증 스위트 3종 — `opal/tools/run-log-tool/tests/`, `opal/tools/state-tool/tests/`, `dashboard/backend/tests/`.
- 공통 데이터
  - secret fixture: 환경변수형 비밀값·`Bearer` 토큰·API key·private key 블록 4종. 같은 fixture를 표준 append·상태 보관함·legacy 가져오기 3경로에 동일하게 투입한다.
  - 보존 대상 fixture: `event_id`(UUIDv4)·`sha256` 다이제스트·`worker_log_token_id` — 비밀값과 형태가 비슷한 16진 문자열이며 마스킹되면 안 된다.
  - 시간대 fixture: 날짜 경계(로컬 자정 직전·직후)를 걸치는 사건 시각 쌍, `timeZone`만 다른 설정 2벌.
  - 동결 fixture: `dashboard/backend/tests/fixtures/t103_states/`와 `STATS-BASELINE.md`. **수정하지 않는다.**
- 대역 사용과 한계: **사용하지 않는다.** 전 시나리오가 `run.sh` subprocess 실호출과 디스크 파일 검사로 판정한다. mock·patch·MagicMock·가짜 파일시스템을 쓰지 않는다(기존 `test_run_log_tool.py`·`test_state_tool_run_log.py` 관례). 예외는 `test_routers.py`가 이미 쓰는 `brain_session_registry.prewarm` 대체 1건이며 이번 범위에서 늘리지 않는다.
- 실행 조건: 전 시나리오 자동 실행. S-4의 경계 동시성은 `multiprocessing` barrier로 유발하며, barrier 대기는 배타 락 상한 30,000 ms보다 충분히 짧게 잡는다 — 그러지 않으면 판정이 `task_lock_timeout`과 뒤섞인다.
- 판정 원천: 평문 잔존·git 추적·파일 권한은 **디스크 실측**으로만 판정한다. 코드 문구 검사나 로그 문자열 일치는 통과 근거가 아니다.

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-13 | secret fixture 4종, 신규 run | 표준 append·상태 보관함 커밋·legacy 가져오기 3경로에 각각 투입하고 조각 파일·`state.json`·원본 사본을 읽는다 | 3경로 산출물 어디에도 평문 비밀값이 0건. 마스킹 호출 지점이 `redact()` 한 곳뿐임을 호출 계보로 확인 | integration — `run-log-tool`·`state-tool` run.sh 실호출 + 디스크 파일 grep | 구현 전 RED |
| S-2 | AC-13, C-5, H-1 | 마스킹 대상을 포함한 사건 payload | `redact()`를 1회·2회 통과시키고 각각 `validate_event()`와 16 KiB 상한 판정에 넣는다 | 1회와 2회 결과가 동일(멱등). 키 집합·타입·중첩 깊이 불변. 상한이 `redact()` 통과 후 최종 줄에서 측정되는 순서 불변 | unit — `run-log-tool` 스위트 | 구현 전 RED |
| S-3 | AC-13, H-5 | 보존 대상 fixture(`event_id`·`sha256`·`worker_log_token_id`)를 포함한 사건 | 마스킹을 통과시킨 뒤 순번 발급·요청 식별자 멱등 판정·출처 대조를 실행한다 | 세 필드 값이 통과 전후 동일. 멱등 판정·순번 발급·출처 대조 결과가 마스킹 미적용 기준선과 일치 | unit — `run-log-tool` 스위트 | 구현 전 RED |
| S-4 | AC-8, H-2 | 조각 크기가 4 MiB 상한 직전인 run | `multiprocessing` barrier로 다중 프로세스 append를 동시 해제한다 | 새 조각이 정확히 1개 생성. run 전역 순번 중복 0·누락 0. 정상 호출 중 다른 호출의 pending 오탐 0. `task_lock_timeout` 미발생 | integration — 다중 프로세스 실호출 + 조각 파일 실측 | 구현 전 RED |
| S-5 | AC-8, C-8 | 새 조각 경로에 심볼릭 링크·경계 이탈 경로를 심어 둔 상태 | 조각 전환을 유발한다 | 링크 추종·경계 이탈이 거부되고 예외 봉투로 환원. 생성된 조각 0600·`run/` 0700 유지. 기존 방어 함수를 재사용했음을 호출 계보로 확인 | integration — 실파일 권한·링크 검사 | 구현 전 RED |
| S-6 | AC-8, H-2 | 조각 2개 이상으로 전환이 끝난 run | 닫힌 조각의 mtime·바이트를 기록한 뒤 append를 이어가고 `scan_run()`으로 순번·멱등을 재판정한다 | 닫힌 조각의 mtime·바이트 불변. 순번이 조각을 넘어 단조 증가. 요청 식별자 멱등 판정 범위가 run 전역 유지 | integration — 조각 파일 실측 | 구현 전 RED |
| S-7 | AC-12, C-4 | `data.duration_spans[]`를 가진 terminal 사건 | 합 일치·합 불일치·같은 `source_id` 중복 3종을 append하고, 코어의 파생 조회 함수를 호출한다 | 합 일치는 수용. 불일치와 `source_id` 중복은 거부. 조회가 `duration_ms`와 `floor(duration_ms / 60000)`을 반환. 코어 실행 중 `state.json` 읽기 0건(정적 import 0건 + 동적 접근 0건) | integration — `run-log-tool reconcile-duration` 실호출 + 파일 접근 관측 | 구현 전 RED |
| S-8 | AC-12, C-3, H-6 | 스키마 1.2 태스크, 다중 process span을 가진 동일 `worker_run_id` | `mark`를 ① 인자 없이 ② 파생값과 같은 `--worker-duration-minutes`로 ③ 다른 값으로 3회 실행한다 | ①은 파생 분값을 자동 기록하고 span이 중복 없이 합산. ②는 수용 + deprecated 경고. ③은 `worker_duration_conflict`로 거부하고 `state.json`을 변경하지 않음 | integration — `state-tool mark` 실호출 + `state.json` 실측 | 구현 전 RED |
| S-9 | C-3, H-6 | `run_log` 블록이 없는 스키마 1.0·1.1 태스크 | 변경 전후 동일 인자로 `mark`·`advance`를 실행하고 산출물과 응답을 바이트 비교한다 | `state.json` 산출물과 응답 키 집합이 변경 전과 바이트 동일. 파생 조회가 호출되지 않음 | integration — 변경 전(git HEAD) 출력과 diff | 구현 후 |
| S-10 | AC-20 | 전역·프로젝트 로컬 설정 2벌, 날짜 경계 fixture | 전역만·로컬만·양쪽·양쪽 부재·무효 IANA 이름 5변형으로 `load_quiet_hours()`를 호출하고, legacy 로컬 시각과 사건 UTC를 함께 해석한다 | 하위 키 단위로 로컬이 전역을 덮고, 부재는 `Asia/Seoul` 기본. 무효 IANA는 `Asia/Seoul` 폴백하고 예외를 던지지 않으며 설정 파일을 다시 쓰지 않음. 날짜 경계 fixture에서 세 시간계 해석이 일치 | unit — `dashboard/backend` 스위트 | 구현 전 RED |
| S-11 | AC-20 | `timeZone`만 다른 설정 2벌 | 각각으로 `quiet_hours_token()`을 만들고 라우터 캐시 키를 생성한다 | 두 토큰이 서로 다르고 캐시 키가 갈린다. 보정 꺼짐은 `off`로 유지 | unit — `dashboard/backend` 스위트 | 구현 전 RED |
| S-12 | AC-20, C-1 | 시드 원본과 install 스크립트 | `opal/core/setting.default.json`의 `quietHours`와 `scripts/install-mac.sh`의 `SEED_KEYS` 배선을 정적으로 대조한다 | 시드에 `timeZone` 키와 `_help` 설명이 존재. `SEED_KEYS`가 `quietHours`를 객체 단위로 실어 하위 키가 전파됨을 확인. **install을 실행하지 않고 `~/.opal/` 파일이 변경되지 않음** | unit — 설정 파일 파싱 + `~/.opal/` mtime 대조 | 구현 후 |
| S-13 | C-2, H-3 | 동결 fixture와 `STATS-BASELINE.md` | `stats.py` 공개 함수 6종의 시그니처를 대조하고 `dashboard/backend` 스위트를 실행한다 | `quiet_hours` 인자가 2튜플(미적용 `None`)로 유지. `stats.py`가 모델·라우터·캐시를 import하지 않고 파일 I/O 0건. 동결 fixture 수정 0건으로 전건 통과 | integration — 스위트 실행 + `git diff` fixture 무변경 확인 | 구현 후 |
| S-14 | AC-14, C-8, H-4 | S-1·S-2·S-3 통과 후, 실제 태스크 1건 실행 | `.gitignore`의 한시 제외 블록을 제거하고 태스크를 실행한 뒤 `git status`·`git check-ignore`로 추적 목록을 확인한다 | `tasks/**/run/raw/`·`tasks/**/run/.runtime/`·`.opal-task.lock`이 제외되고 **마스킹된 조각은 추적된다.** 추적 대상 조각에 평문 비밀값 0건. 한시 제외 주석 블록이 남아 있지 않음 | integration — 실제 실행 + git 실호출 | 구현 후 |
| S-15 | AC-21, C-2 | W-1이 확정한 재측정 기준선 | 3개 스위트를 전건 실행하고 기준선과 대비한다 | 세 스위트 전건 통과. 기준선 대비 실패 증가 0. **기존 테스트 파일 수정 0건**(`git diff` 실측) | integration — 스위트 실행 + `git diff --stat` | 구현 후 |
| S-16 | C-5, C-9 | `CONTRACT.md` §2.2·§2.2.1, `surfaces.json` `err` 집합, 구현된 오류 코드 테이블 | 세 자산의 오류 코드 집합을 양방향 대조한다(MV-30) | 계약에만 있고 구현에 없는 코드 0건, 구현에만 있고 계약에 없는 코드 0건. `CONTRACT.md`·`TRD.md`·`surfaces.json` 변경 0건(`git diff` 실측) | unit — 자산 파싱 대조 + `git diff` | 구현 후 |
| S-17 | C-1, C-6 | 태스크 전체 변경분 | `git status`로 변경 파일 목록을 확정하고 `~/.opal/` 트리와 3-SSOT 파일을 확인한다 | `~/.opal/` 하위 변경 0건, install 실행 흔적 0건. `state.json`·`backlog.json`·`test-scenario.json` 직접 편집 0건(전부 전용 도구 경유) | integration — git 실호출 + 도구 호출 이력 대조 | 구현 후 |
| S-18 | C-7 | 변경된 도구 코드 | `run_log_core.py`·`state_tool.py`·`config.py`의 플랫폼 조건 분기를 확인한다 | 도구 로직에 플랫폼별 분기 0건. 플랫폼 차이는 변환·어댑터 계층에만 존재 | unit — 정적 검사 | 구현 후 |
| S-19 | AC-21 | 기 충족 AC-1·2·3·6·7·10·15·19의 기존 시나리오 | 해당 시나리오를 변경 후 코드로 재실행한다 | 멱등·4축 조합 거부·상태 보관함 복구·`run_log_missing` 진단·legacy 가져오기 단방향·I/O 방어가 전부 유지. 판정은 실제 실행 출력으로만 하고 기존 테스트 파일을 고쳐 통과시키지 않음 | integration — 스위트 실행 출력 | 구현 후 |
