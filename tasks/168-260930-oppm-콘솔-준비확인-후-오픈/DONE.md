# DONE — Console 준비 확인 후 열기

> 사용자 최종 확인: 2026-09-30 커밋 요청으로 확인

## 변경 결과

- `opal-cli console open`이 먼저 `/health`를 확인하고, 미응답이면 `console start` 후 준비 확인을 재시도하도록 변경했다.
- 준비 확인이 실패하면 브라우저를 열지 않고 오류와 `/tmp/opal-console.log` 경로를 안내한다.
- PID 소유권 모델은 바꾸지 않았다. 이미 응답하는 비소유 Console은 그대로 연다.
- CLI 도움말과 Architecture Console 설명을 새 동작에 맞춰 갱신했다.
- 설치 절차를 실행해 `~/.opal` 배포본에도 반영했다.

## 검증

- `scripts/tests/test_console_open.sh`: PASS 5 / FAIL 0
- Bash 구문, 코드맵 정합, 소스와 배포본 일치, 배포본 `opal-cli console open`과 `/health` 응답을 확인했다.
- 상세 실행 증거: [verification.md](evidence/verification.md)
- 기존 소유권 회귀 스크립트는 변경과 무관한 기존 S-3 실패 및 격리 서버 종료 지연으로 완료하지 못했다. 상세는 증거 문서에 기록했다.
- 신규 brain 페이지는 indexed 되었고 개별 lint 이슈가 없었다. 전체 brain lint의 기존 이슈 315건은 별도 범위다.

## 지식 동기화 판정

| 영역 | 판정 | 근거 |
|---|---|---|
| 기획 | no-op | 사용자 정책·서비스 흐름은 변경하지 않은 로컬 CLI 동작 수정이다. |
| 설계 | update | `docs/ARCHITECTURE.md`에 open의 health 기반 준비 계약을 반영했다. |
| 프로젝트 문서 | no-op | PROJECT의 Console 컴포넌트·경로 설명은 현재 변경 표면과 일치한다. |
| CONVENTIONS | no-op | Bash 3.2 호환, 플랫폼 분기 격리, source→install 배포 경계를 기존 방식으로 따랐다. |
| SECURITY | no-op | localhost 바인딩, URL·PID 소유권·권한 모델을 변경하지 않았다. |
| brain | update | `console-open-health-readiness` 페이지에 채택 이유와 소유권 경계를 기록했다. |
| memory | no-op | 다음 세션에 별도 주의사항이나 후속 작업이 남지 않았다. |
| code-scan | no-op | 변경 `.sh` 파일은 현재 code-scan 대상 확장자가 아니며 `validate --changed`가 OK를 반환했다. |

## 미해결 사항

- 기존 `test_console_ownership.sh`의 S-3 실패와 장시간 격리 서버 실행은 이 변경 범위 밖의 기존 테스트 문제다.
