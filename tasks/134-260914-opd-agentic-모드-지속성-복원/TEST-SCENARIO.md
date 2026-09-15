---
template: sdlc-v2
---
# TEST-SCENARIO: agentic 모드 지속성 복원

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: task_134 워크트리의 Python 표준 라이브러리 unittest 환경과 실제 `state-tool`·`event-loader` 공개 CLI
- 공통 데이터: 임시 태스크 폴더에 신규·agentic·interactive·semi-agentic·mode 누락·unknown mode·malformed JSON 상태를 각각 생성하며, 저장 전후 파일 바이트와 행·생성 시각을 비교
- 대역 사용과 한계: 외부 서비스 대역은 사용하지 않음. 실제 4개 플랫폼 대화 세션은 자동 실행하지 않으며 플랫폼 중립 소스의 정적 계약과 격리 install 결과로 대리 검증
- 실행 조건: 구현 전 RED 시나리오는 테스트 작성자와 구현자를 분리하고 `test-tool`에 실패 증거를 잠근 뒤 구현 시작. 구현 후에는 전체 관련 회귀를 독립 테스트 워커가 실행

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-2, AC-4, C-1, C-2, C-4, H-2 | 신규 state 부재와 유효 mode를 가진 기존 state를 각각 준비 | `resolve-mode` 공개 CLI를 신규 무플래그, 신규 명시, 기존 무플래그, 기존 동일·상이 명시 조합으로 실행하고 저장 전후 JSON을 비교 | 신규 무플래그는 semi-agentic, 명시는 최우선, 기존 무플래그는 저장값이며 override는 mode와 감사 정보만 원자 갱신함. rows·created_at·기타 필드는 동일하고 동일값 재지정은 무변경 | subprocess 기반 unit/integration, 임시 실제 파일 | 구현 전 RED |
| S-2 | AC-1, AC-2, C-1, C-2 | agentic state에서 사용자 확인 행을 진행 중으로 두고 첫 CLI 프로세스를 종료 | 별도 새 프로세스에서 무플래그 mode 해석 후 다음 단계 `advance`를 실행 | effective mode가 agentic/state로 복원되고 직전 비-CLOSE 사용자 확인 행이 `owner=auto`, done으로 전이되며 `auto_approved`에 포함됨 | subprocess integration, 실제 state-tool CLI | 구현 전 RED |
| S-3 | AC-1, AC-7, C-3, H-4 | agentic·interactive·semi-agentic 상태에 각 모드 경계와 CLOSE 직전 확인 행을 구성 | 사용자 검토 왕복을 모사해 다음 단계 진입과 CLOSE 진입을 각각 시도 | agentic 비-CLOSE만 자동 승인, interactive 전 구간과 semi-agentic pre-execute는 사용자 확인 요구, agentic·semi-agentic CLOSE는 `owner=user` 전까지 거부됨 | 기존 T093 회귀 + 신규 공개 CLI 관통 테스트 | 구현 전 RED |
| S-4 | AC-5, AC-7, C-1, C-3, C-4, H-1 | 기존 state의 mode가 누락·null·비문자·빈 문자열·enum 밖 문자열인 케이스 | 무플래그 resolve, validate, 다음 단계 advance를 실행하고 파일 바이트를 비교 | 모두 interactive/fail_closed로 정규화되어 자동 승인하지 않고 구조화 경고·위반을 반환함. state를 조용히 수정하지 않으며 명시 mode로만 복구 가능 | subprocess unit/integration, 임시 실제 파일 | 구현 전 RED |
| S-5 | AC-5, C-1, C-4, H-1 | JSON 문법 오류와 top-level 비객체 state를 준비 | 무플래그 및 명시 mode resolve를 각각 실행 | 모두 `state_json_malformed`로 차단되고 state·STATE.md는 바이트 불변이며 신규 task 기본값으로 오인되지 않음 | subprocess unit, 실제 파일 I/O | 구현 전 RED |
| S-6 | AC-6, C-1, C-4, C-6, H-3 | 정상 agentic·invalid legacy·긴 문자열·부분 조회 실패 프로젝트 fixture를 준비 | boot-summary와 project-brief 공개 CLI를 실행 | 최신 미완료 1건에 mode/mode_source가 additive로 노출되고 invalid는 interactive/fail_closed로 표시됨. `이어보기` 기존 블록과 UTF-8 1,024바이트 상한이 유지되고 부분 실패는 해당 블록만 생략됨 | event-loader/state-tool subprocess integration | 구현 전 RED |
| S-7 | AC-3, AC-7, C-2, C-3, C-6, H-4 | Pilot·track owner 문서와 정적 계약 스크립트를 준비 | 기존 task 재호출, `oppd→opwt`, `opd→opds`, `opds→opd` 경로의 호출 템플릿과 게이트 문구를 검사 | 모든 경로가 effective mode를 명시 상속하며 트랙 수락·PRD/TRD 소유권·CLOSE 사용자 확인 문구는 남아 있고 플랫폼별 조건문은 0건 | 정적 계약 unittest/script | 구현 전 RED |
| S-8 | AC-7, C-3, C-4 | 기존 모드×단계 자동 승인 테스트 전체 | state-tool의 T093 자동 승인·경계·단일 판정·R11 경계 테스트를 실행 | 기존 interactive·semi-agentic·agentic·CLOSE·worker/force 경계가 전부 통과하고 unknown mode 허용 회귀가 없음 | Python unittest | 구현 후 |
| S-9 | AC-8, C-5, C-6 | W-2~W-4 소스·문서 변경 완료, 허브의 기존 사용자 변경은 보존 | 정적 계약 검사와 격리된 install 검증을 실행하고 배포 대상 파일을 소스와 비교 | 하네스·Pilot·README·프로젝트 문서가 구현 계약과 일치하고 지원 플랫폼 공통 배포가 가능함. `~/.opal/` 수기 편집과 플랫폼 로직 분기가 없음 | 프로젝트 install/static-check 스크립트, 격리 대상 | 설치 후 |
| S-10 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, C-1, C-2, C-3, C-4, C-5, C-6, H-1, H-2, H-3, H-4 | 모든 RED가 GREEN이고 문서 정합화 완료 | 신규 mode resolver·state-tool 전체·event-loader 전체·정적 Pilot 계약 테스트를 한 묶음으로 재실행 | 실패 0건, RED 기대 완화·삭제 0건, 테스트 외 소스와 태스크 산출물만 계획 범위에서 변경됨 | 독립 TEST 워커, 실제 명령 로그 | 구현 후 |
