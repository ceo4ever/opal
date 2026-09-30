# 구현 검증 기록

검증 대상: 로컬 opal-pilot-dev2 스킬 패키지. 전역 설치본은 수정하지 않았다.

## 실행 결과

- `python3 -m unittest discover -s opal-pilot-dev2/tests -v`: 31 tests, OK.
- 기존 OPAL Python 환경으로 skill-creator quick_validate 실행: Skill is valid.
- 임시 Git 저장소에서 실제 기존 worktree-tool create/status 및 opd2 init 성공.
- 실제 Python 덧셈 버그의 실패 재현 → 코드 수정 → Builder/Verifier 명령 실행 → 리뷰 기록 →
  ready_for_merge 전체 경로 성공. 이 테스트의 역할 판정은 fixture이며 실제 독립 에이전트 평가와 구분한다.

## 차단 검증

모드/작업본 충돌, 재개 작업본 변경, 지원 밖 저장 모드, 손상 상태, 승인 없는 semi-agentic
전이, 고위험 무승인/위험 하향, source 해시 불일치, 범위 밖 untracked 파일, 증거 누락,
검증 후 소스 변경, 로그 변조, 보호 테스트 수정, 최신 리뷰 fail, 테스트 실패,
실행 중 소스 변경, 재시도 상한, wt receipt 누락을 테스트했다.

## 별도 평가 상태

독립 에이전트가 별도 임시 저장소에서 INTENT → DESIGN → PLAN → BUILD 진입을 실행했다.
이후 하위 Builder 실행이 완료되기 전에 서비스 크레딧 부족으로 평가 에이전트가 실패했다.
잔여 하위 실행은 중단했다. 독립 에이전트 전체 개발·검증·리뷰 평가를 PASS로 기록하지 않는다.

## 미실행 영역

- 실제 UI 터미널의 전용 Codex 세션 기동과 세션 소유권 이관.
- 실제 운영 배포·관측·rollback. release 테스트는 로컬 명령을 사용하는 전이 계약 검증이다.
- 사용자 프로젝트의 multi-repo 전체 검증과 전역 //opd2 명령 등록.

로컬 CLI는 기록된 승인·역할·증거를 검사하지만 인증/OS 격리를 대체하지 않는다.
이 경계는 governance.md와 execution.md에 명시했다.
