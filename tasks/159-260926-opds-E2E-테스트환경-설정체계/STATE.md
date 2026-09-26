# STATE: E2E 테스트 환경 설정 체계

> 최종 갱신: 2026-09-26 19:34:50
> 파이프라인 현황(rows/상태/다음 액션)의 SSOT는 `state.json`입니다.
> 조회: `~/.opal/tools/state-tool/run.sh show <task-path>`

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|
| 1 | 2026-09-26 19:19:38 | design-decision(detail): E2E 환경 설정 파일은 .opal/e2e/environment.json(JSON), 검증 스키마의 원본은 lib/e2e/environment.py 한 곳 | AC-1·C-4. .opal/e2e/README.md가 프로젝트 E2E 추적 설정 위치로 이미 정의. jsonschema는 설치 의존성으로 선언돼 있지 않아 기존 e2e_contract.py처럼 순수 Python 검증을 쓴다 |
| 2 | 2026-09-26 19:19:38 | design-decision(detail): run의 dashboard 고정 기동을 제거하고 설정 기반 서비스 기동으로 교체. 설정이 없으면 포트 임대 모양(backend·frontend)만 호환 유지하고 SUT 기동 시점에 blocked(e2e_env_config_missing)+안내 | AC-5·AC-6·C-5. 설정 없는 임시 트리 회귀 테스트(test_e2e_runtime.py:280-330)가 임대 2건과 urls 키를 단언한다. 다른 프로젝트는 원래도 dashboard 모듈이 없어 infra_error였으므로 원인을 명시하는 blocked가 개선이다 |
| 3 | 2026-09-26 19:19:39 | design-decision(detail): 태스크 127 backup 이동으로 깨진 test-tool 회귀 테스트 fixture(test-scenario.json·surfaces.json)를 tests/fixtures로 옮겨 참조를 고정 | AC-7. 변경 전 기준선 41 failed+3 errors의 원인이 전부 tasks/127 경로 부재(7e2184c)임을 임시 심볼릭 링크 재실행 156 passed로 확인 |
| 4 | 2026-09-26 19:34:45 | additional row inserted after row 7: stage=EXECUTE, item=W-2~W-6 구현 (W-1 완료 시점 워커 조기 done 보정), key=execute.w_1, new_row_id=8 | additional work entry |

## 블로커
없음
