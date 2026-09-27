# DONE: 검증 도구 실행 정확성 복구

## 결과

`test-tool unit`의 설치 확인(`check`)과 실제 검사(`run`)를 분리했다. `run` 누락·설치 확인 실패·검사 실패·미실행을 구별하고, 실행 명령·설정 출처·작업 디렉터리·실제 검사 범위를 CLI 결과에 기록한다. 변경 파일 검사는 도구가 지원할 때만 적용한다. 전역 템플릿, 추론 설정, 스키마와 직접 소비하는 문서도 같은 계약으로 맞췄다.

## 변경 파일

- `opal/tools/test-tool/lib/runner.py`, `opal/tools/test-tool/lib/resolver.py`, `opal/tools/test-tool/test_tool.py`, `opal/tools/test-tool/README.md`
- `opal/tools/test-tool/tests/test_test_tool.py`, `opal/tools/test-tool/tests/test_red_s161_unit_contract.py`, `opal/tools/test-tool/tests/fixtures/unit-real/`
- `opal/templates/test-tools.yaml`, `opal/core/references/test-tools-schema.yaml`
- `opal/skills/op-dev-execute/references/execute-guide.md`, `opal/agents/opal-test-agent/AGENT.md`
- `tasks/161-260927-opd-검증도구-실행정확성-복구/`의 계획·시나리오·상태·검증 증거·컨벤션 보고서

## 검증

- `test-tool scenario-status`: S-1~S-13 모두 PASS, FAIL/BLOCKED 0건. 결과와 실행 증거는 `test-scenario.json` 및 `evidence/`에 보존했다.
- Python의 실제 ruff·mypy·pytest와 TypeScript의 eslint·tsc·vitest로 정상·위반·변경 파일 사례를 검증했다.
- `python -m pytest opal/tools/test-tool/tests -q -p no:cacheprovider -rf`: 소켓 허용 환경에서 569 passed, 345 subtests passed, 0 failed. 수정 후 대상 테스트는 31 passed, 13 subtests passed.
- 변경 코드 Ruff E741 0건, `code-scan validate --changed` 신규 미적용 0건, `state-tool validate` 위반 0건, 컨벤션 보고서 Critical/High 0건.
- 배포본의 실행기·전역 템플릿·스키마 원문 해시 5개 일치. README는 설치기의 `## 변경이력` 제거 후 본문 일치. 새 로그인 셸에서 전역 템플릿 경로와 배포본 `resolve`·`unit` 실제 실행을 확인했다(`evidence/deploy/final-s13-assessment.json`).

## 회고적 학습 후보

.opal/brain/pages/entity/test-tool.md

## 참고

작업본 귀속 finalize를 완료했다(관측 변경 0건, 귀속 커밋 없음). 태스크 브랜치의 merge·push와 worktree 회수는 사용자 권한 경계에 남겨 둔다.
