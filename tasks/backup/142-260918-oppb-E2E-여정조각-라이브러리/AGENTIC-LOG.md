# AGENTIC-LOG: E2E 여정·조각 라이브러리

> 모드: semi-agentic | 시작: 2026-09-20 00:38 | 스킬: //oppb

## 실행 기록

- P2 사용자 게이트 승인: S-27 핵심 단언을 유지하고 조각 전개분과 본문을 구분 집계하도록 측정 범위 정정.
- P2 Environment Probe 재봉인: 8개 명령 성공, `fresh=true`, `parallel_dispatch_allowed=true`, 거부 경로 0건.
- P3 Supervisor 기동: PID 57822, 복구 대상 0건.
- P3 차단: `run_command=null`인 T01·T02에서 Runner를 생략하고 verifier를 즉시 실행하여, 구현 전 테스트가 `NO TESTS RAN`(exit 5)으로 각각 3회 실패했다. `supervisor.py`의 capability-agent 기본 실행 계약과 `_admit_task` 구현이 불일치하며 태스크 142 lease 밖 프레임워크 보정이 필요하다.
- P3 추가작업 승인: 캡틴 지시로 PM이 Supervisor 결함을 태스크 142 추가작업으로 직접 수정했다.
- Supervisor 보정 1: `run_command=null`을 자동 완료·검증 전환하지 않고 `opal-agent` Runner로 기동하도록 조기 반환을 제거했다. 신규 RED→GREEN 및 전체 Supervisor 회귀를 통과했다.
- Supervisor 보정 2: 선언된 Executor 수가 `max_active_executors`보다 많아도 같은 runner 세대 안에서 빈 pool slot만큼 배치 실행하도록 admission·세대별 outcome 추적을 보정했다.
- 검증·배포: 소스 OPPB 런타임 `132 passed, 13 subtests passed`; 설치본 Supervisor `7 passed`; 소스/설치본 `supervisor.py`·`test_supervisor.py` SHA-256 일치. 공식 `install-mac.sh` 배포와 Console health 복구 완료.
- P3 재개: 기존 PID 57822를 종료하고 새 run `20260920T015608Z-93a90651`을 생성했다. Runner 2·Executor 2·전체 4 상한에서 실제 attempt 기동을 확인했다.
- P3 1차 재차단(정정): `opal-agent` attempt의 `api_error_status: 429`는 캡틴의 Codex 한도가 아니었다. Supervisor가 `--provider`를 누락해 `opal-agent` 기본값인 별도 Claude를 호출한 결과였다. 캡틴 제보 후 Codex 단발 호출 성공, `models.platform=auto`, attempt의 `provider=claude`를 대조해 오진을 정정했다.
- Provider 라우팅 추가 보정: effective `models.platform`의 명시값을 우선하고 `auto`이면 현재 세션 환경 표식으로 Codex를 선택해 `--provider codex`를 명시하도록 수정했다. RED→GREEN, Supervisor `7 passed`, OPPB 전체 `132 passed, 13 subtests passed`, 공식 설치와 설치본 회귀를 통과했다.
- P3 실호출 확인: 새 run `20260920T040809Z-1ecce38b`에서 Runner 2·Executor 2가 모두 `provider=codex`로 실제 기동했다. 이로써 92%가 남은 Codex 경로가 정상임을 확인했다.
- P3 2차 재차단: 실제 dispatch prompt가 execution packet 절대경로와 worker 역할 없이 `capability …`만 전달되고, packet도 `opal-capability-agent` 진입 게이트가 요구하는 budget·contract를 제공하지 않는 별도 계약 결함을 확인했다. 일반 PM 세션 오진입·동일 lease 병렬 쓰기 위험이 있어 새 run의 Supervisor와 4개 process group을 회수했다. 작업 소스 변경은 발생하지 않았다.
- 종료 점검: 새 run Supervisor·Runner·Executor 잔존 프로세스 0을 확인했다. 회귀 테스트가 142 워크트리에 남긴 uvicorn 52개를 해당 CWD 범위로 한정해 종료했으며, 설치 Console `http://127.0.0.1:7823/health`는 `status=ok`, `version=0.1.0`을 유지했다.
- P3 완주: 새 run `20260920T053616Z-375ae84f`에서 T01~T07이 모두 `accepted`로 종료되었고 active runner·executor·lease는 0건이다. T04 declarative driver의 전역 registry·프로젝트 discovery 경계를 PM 추가작업으로 보정했다.
- P4 검증: OPPB 런타임 `132 passed, 13 subtests passed`, test-tool `472 tests OK`, 통합·보안·컨벤션 evidence 21건, INTENT 완료조건 8/8 PASS. 보안 검토에서 여정 ID path traversal을 발견해 single-filename 검증과 회귀 테스트를 추가했다.
- 배포 검토: `scripts/install-mac.sh` 성공, 핵심 설치 파일 9개의 source/install SHA-256 일치, 설치본 Supervisor 7 tests·skill registry validate 통과. 설치 레이아웃 차이를 반영해 E2E 프래그먼트 fixture 테스트 루트 탐색을 보강했다.
- CLOSE 문서 수명주기: 활성 제안서 참조 0건을 확인하고 `e2e-journey-fragment-library.md`를 `적용완료`로 `docs/proposals/archives/`에 보관했다.
