---
template: sdlc-v2
---
# TEST-SCENARIO: TEST 단계 소요시간 단축

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: 이 worktree의 OPAL CLI와 임시 디렉터리의 실제 git 저장소. 변경 전후 고정 입력으로 CLI·문서 계약을 검증한다.
- 공통 데이터: 사람 협업 2건과 자동 시나리오 2건이 있는 TEST-SCENARIO fixture, fix·요구 변경 행이 있는 임시 태스크, main과 기능 브랜치.
- 대역 사용과 한계: 파일·git fixture는 격리된 실 파일·실 git으로 구성한다. 외부 설치본 검증을 대체하지 않는다.
- 실행 조건: 자동 테스트는 별도 사용자 조치 없이 수행한다. 실제 `~/.opal` 설치는 외부 쓰기 승인 후 수행한다.

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1, C-2 | L3 로그인·DDL 두 건과 자동 검사 두 건 | TEST 시작 절차·agent 고정 사례 실행 | 사람 조치 두 건이 한 요청으로 자동 완료 전에 제시되고, 대기 중 자동 검사가 실행되며 사람 제출은 verifier만 PASS 판정 | 절차 계약 검사와 CLI 실행 기록 | 구현 후 |
| S-2 | AC-2, C-5, C-6 | TEST의 fix 두 행과 요구 변경 세 행, legacy 행 | state-tool 추가 행 명령으로 종류별 계수 후 네 번째 요구 변경 시도 | 별도 계수·상한 초과 거부와 분리 결정 요청, legacy 재개 유지 | state-tool 공개 CLI 통합 | 구현 전 RED, 구현 후 |
| S-3 | AC-3, C-3, C-4, H-1 | 실패 S-ID, 변경 파일 영향 S-ID, 관계 불명 S-ID | fix 반복과 최종 Gate 계약·실행 로그 확인 | 반복은 실패+영향만, 불명은 확대, Gate는 필수 전건 PASS·전체 회귀 1회. 구형 전 PASS 재실행 문구 0건 | 계약 검사·실행 fixture | 구현 후 |
| S-4 | AC-4, C-2, C-3 | 동일 SHA·환경·PASS 증거와 SHA/환경 변경 사례 | TEST 증거 재사용 판정 | 같은 서명은 경로를 보고에 기록하고 재실행 생략, 다르면 실행 | agent 계약·실행 fixture | 구현 후 |
| S-5 | AC-5, C-2 | TEST 재작업 2회 후 최종 수정 | GC 호출 순서 확인 | 중간 컨벤션 검사 필수 호출 0회, 최종 Gate에서 checker 1회·Critical/High 0건 판정 | pilot·PM Gate 계약 검사 | 구현 후 |
| S-6 | AC-6, C-1, C-7 | 실제 git fixture의 main 동등/선행 두 경우 | worktree-tool 분기 조회와 TEST 진입 계약 확인 | 동등 0/0, 선행 behind 양수; 선행 시 merge 승인 전 TEST 시작 차단, 도구는 쓰기 없음 | 실 git CLI 통합 | 구현 전 RED, 구현 후 |
| S-7 | AC-7, C-5, C-6, H-2 | 태스크 162와 legacy 태스크 한 건 | TEST 실행·대기 시작/종료를 기록하고 요약 조회 | 실제 사건 시각에서 자동/대기 시간 산출, fix/요구 변경 수 분리, legacy 결측은 unknown | state-tool 공개 CLI·기존 태스크 조회 | 구현 전 RED, 구현 후 |
| S-8 | AC-8, C-5 | 변경된 events manifest | `event-loader load --event stage.test` 후 verify | 새 실행 규칙 문서가 필수 집합에 포함되고 receipt 검증 PASS | event-loader 실제 CLI | 구현 전 RED, 구현 후 |
| S-9 | AC-9, C-2 | 동일 manifest와 변경된 프로젝트 주입 문서 | receipt 재사용 미채택 결정·기존 검증 경계 확인 | PLAN에 근거가 남고 새 stale receipt 우회 경로가 없음 | 문서·회귀 검사 | 구현 후 |
| S-10 | AC-10, C-1, C-4, C-7 | 변경 소스와 임시 설치 대상 | 관련 회귀·임시 install 후 진입점 비교 | 관련 테스트 PASS, 설치 대상 스킬·하네스·CLI 반영, 161·163 파일/상태 무변경 | pytest·설치 스크립트의 임시 대상 | 설치 후 |
