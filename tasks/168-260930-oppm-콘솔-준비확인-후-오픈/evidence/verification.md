# 검증 증거

## 재현 조건

- 실행일: 2026-09-30 KST
- 작업본: `/Volumes/Data/AIStudio/workspace/ai-framework`
- 배포본: `~/.opal/tools/opal-cli/lib/console.sh`가 소스 파일과 `cmp` 일치
- Console health: `http://127.0.0.1:7823/health`

## 실행 결과

| 검증 | 명령 또는 방법 | 결과 |
|---|---|---|
| 준비 대기 회귀 | `bash scripts/tests/test_console_open.sh` | PASS 5, FAIL 0 |
| Bash 구문 | `bash -n opal/tools/opal-cli/lib/console.sh` 및 `bash -n opal/tools/opal-cli/run.sh` | PASS |
| 코드맵 정합 | `code-scan validate --changed ... --full` | `validate: OK — coverage 0% (0/1)` |
| 설치 배포 | `OPAL_AUTO_INSTALL=1 bash scripts/install-mac.sh`의 OPAL 설치 | PASS, Console `/health` 응답 확인 |
| 배포본 실제 명령 | `opal-cli console open; curl -fsS http://127.0.0.1:7823/health` | 브라우저 열기 성공, `{"status":"ok","version":"0.1.0"}` |
| brain 페이지 | `brain-tool add-page`와 `brain-tool lint` | 신규 페이지 indexed 성공, 전체 brain lint는 기존 이슈 315건을 보고 |

## E2E 적용 검토

`opal-e2e`를 검토했다. 변경은 로컬 CLI의 기동·준비 확인 제어 흐름이며 Console 화면, API 계약, 여러 서비스에 걸친 사용자 여정은 바꾸지 않는다. 셸 단위 회귀와 실제 배포본 명령으로 검증했으므로 E2E 여정은 미실행했다.

## Brain lint

`console-open-health-readiness` 신규 페이지는 lint 결과에 개별 이슈로 나오지 않았다. 전체 brain lint의 315건은 기존 페이지의 frontmatter·링크 문제이며 이번 페이지 추가와 무관하다.

## 기존 소유권 회귀 스크립트

`bash scripts/tests/test_console_ownership.sh`를 실행했으나, 기존 S-3이 `types_ok=0`으로 실패했고 격리 uvicorn 프로세스를 계속 기동하여 실행 환경 제한 시간 안에 종료하지 못했다. 이 변경과 무관한 기존 실패로 분리했으며, 이 실행에서 시작한 부모 테스트 프로세스와 그 자식 서버만 종료했다. 사용자 Console `127.0.0.1:7823/health`는 종료 전후 모두 정상 응답했다.
