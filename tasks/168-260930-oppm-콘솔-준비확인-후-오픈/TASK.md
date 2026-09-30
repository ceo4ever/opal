# TASK — Console 준비 확인 후 열기

## 요청과 목표

- 요청: `opal-cli console open`이 서버의 실행 준비를 확인한 뒤에만 브라우저를 열도록 수정한다.
- 완료 기준: 서버가 꺼진 상태에서 `open`이 기동을 시도하고 `/health`가 응답할 때만 브라우저 실행을 요청한다. 제한 시간 내 준비되지 않으면 브라우저를 열지 않고 오류와 로그 경로를 알린다.

## 승인된 작업 계약

1. 목표/완료 조건: Console의 `open` 경로가 `/health` 확인을 통과한 뒤에만 URL을 연다.
2. 포함/제외 범위: `console.sh`의 준비 확인과 `open` 제어 흐름, CLI 도움말·아키텍처 설명, 회귀 테스트를 포함한다. Console API·프런트엔드·PID 소유권 모델은 제외한다.
3. 변경 대상: `opal/tools/opal-cli/lib/console.sh`, `opal/tools/opal-cli/run.sh`, `docs/ARCHITECTURE.md`, `scripts/tests/test_console_open.sh`.
4. 결정/가정: 준비 상태의 판단 원천은 `GET /health`의 성공 응답이며, 이미 응답 중인 비소유 Console은 종료하거나 소유권 레코드를 변경하지 않는다. 준비 대기는 설치 스크립트와 같은 최대 10초를 사용한다.
5. 검증 방법: Bash 구문 검사, 준비 대기 헬퍼의 재시도 동작, `open` 분기의 기동·대기·브라우저 실행 순서 검사, 기존 Console 소유권 회귀 테스트를 실행한다. E2E는 CLI 제어 흐름 변경으로 사용자 여정/API 계약에 영향이 없어 미실행 검토한다.
6. 예상 영향: Console CLI 동작과 아키텍처 문서 설명은 갱신한다. 기획·보안·brain·memory·code-scan 영향은 완료 시 근거와 함께 판정한다.

## 승인 근거

캡틴이 2026-09-30에 “알투가 직접 수정해줘”라고 요청하여 위 범위의 구현을 승인했다.

## 영향 후보 집합

| 대상 | 선별 근거 | 예상 영향 | 상태 |
|---|---|---|---|
| `opal/tools/opal-cli/lib/console.sh` | `console open` 구현과 `/health` URL을 소유 | 준비 확인·기동·오픈 순서 변경 | pending |
| `opal/tools/opal-cli/run.sh` | 사용자용 CLI 도움말에 `open` 설명을 복제 | 준비 보장 문구 갱신 | pending |
| `docs/ARCHITECTURE.md` | Console 기동 명령의 아키텍처 설명 | `open`의 준비 보장 기록 | pending |
| `scripts/tests/test_console_open.sh` | 기존 Console 셸 테스트(`test_console_ownership.sh`)에는 open 준비 경로가 없음 | 준비 대기·순서 회귀 검증 추가 | pending |
| `.opal/brain/` | Console 규범 변경의 결정 이유 저장소 | 검색 결과 없음; 완료 시 갱신 필요성 재판정 | pending |
| `.opal/MEMORY.json` | 다음 세션 주의사항 저장소 | 동작 변경 후 후속 주의 여부 판정 | pending |

## 참조와 제약

- `opal/tools/opal-cli/lib/console.sh:394`는 현재 브라우저 실행만 하므로 준비 확인이 없다.
- `scripts/install-mac.sh:2060`은 `/health`를 최대 10초 기다리는 기존 패턴이다.
- `docs/ARCHITECTURE.md:279`의 PID 소유권 규칙을 유지한다.
- `docs/CONVENTIONS.md`의 Bash 3.2 호환성과 플랫폼 분기 격리 규칙을 따른다.

## 실행 기록

- Run ID: `run_3cad17cf-60c1-4275-b6bc-b79349b78886`
- self-pm: `.opal/self-pm/run_3cad17cf-60c1-4275-b6bc-b79349b78886.json`
- run-log: `run/run-log-run_3cad17cf-60c1-4275-b6bc-b79349b78886-0001.jsonl`
