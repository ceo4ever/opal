## 결정

`opal-cli console open`은 브라우저 실행 전에 전용 `/health`의 성공 HTTP 응답을 확인한다. 응답이 없으면 기존 `console start` 경로로 기동을 요청하고, 준비 확인을 재시도한다. 제한 횟수 안에 준비되지 않으면 브라우저를 열지 않고 로그 경로를 안내한다.

## 이유

브라우저 실행 성공은 Console 서버가 실제로 연결 가능한지를 의미하지 않는다. URL을 먼저 열면 사용자는 연결 실패 페이지를 보게 되고 기동 여부를 별도로 판별해야 한다. `/health`는 기존 Console의 준비 상태를 확인하는 전용 표면이므로, 이 응답을 open의 완료 조건으로 사용한다.

PID 레코드는 종료 권한을 판정할 때만 사용한다. `/health`가 응답하는 이미 실행 중인 비소유 Console은 종료하거나 레코드를 바꾸지 않고 열 수 있어야 한다.

## 근거

- `opal/tools/opal-cli/lib/console.sh` — start/status/open과 PID 소유권 구현
- `docs/ARCHITECTURE.md` — Console의 PID 소유권 경계
- `tasks/168-260930-oppm-콘솔-준비확인-후-오픈/evidence/verification.md` — 회귀·배포본 검증

## 관련 페이지

- [[opal-console]]
