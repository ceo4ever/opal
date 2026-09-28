# DONE: AC 핵심 요구사항 작성 기준 명확화

## 변경 결과

- `task-guide.md`에서 AC를 별도 Requirements 절이 없는 sdlc-v2의 검증 가능한 핵심 요구사항으로 정의했다.
- 하나의 AC를 하나의 독립적인 수용 결정으로 규정하고 출처성·필수성·관찰성·해법 독립성·비중복성의 다섯 채택 조건을 추가했다.
- 관찰 지점 수가 아니라 수용 결정으로 원자성을 판정하며, 불가분한 성공·거부 경계는 같은 AC에 둘 수 있게 했다.
- 같은 요구를 테스트 환경·배포 단계별로 나누는 사례와 구현 방법을 AC로 올리는 사례를 중복으로 판정했다.
- AC가 아닌 구현·검증·수행 절차·프로젝트 공통 규칙·영향 목록의 기록 위치를 명시했다.
- `SKILL.md`와 README가 owner 가이드의 실행 요약을 동일하게 소비하도록 정합화했다.

## 변경 파일

- `opal/skills/op-task/references/task-guide.md`
- `opal/skills/op-task/SKILL.md`
- `opal/skills/op-task/README.md`
- `.opal/brain/pages/concept/ac-core-acceptance-requirement.md`
- `.opal/brain/index.md`
- `.opal/brain/log.md`
- `tasks/165-260928-oppm-AC-핵심-요구사항-작성-기준/TASK.md`
- `tasks/165-260928-oppm-AC-핵심-요구사항-작성-기준/evidence/validation.md`

## 검증

- 관련 `clarification` 계약 테스트: 13 passed
- 전체 관련 파일 테스트: 169 passed, 2 unrelated environment-dependent failures
- `git diff --check`: PASS
- 필수 기준·라우팅 문구 정적 검사: PASS
- `code-scan validate --changed`: exit 0 (`newly_uncovered: 0`, 기존 `pre_existing` 3건)
- brain: concept를 active 상태로 연결·색인했으며 검색 노출과 대상 페이지 lint 0건을 확인했다.
- E2E: 문서 규범 변경으로 미적용. 근거와 대체 검증은 `evidence/validation.md`에 기록했다.

## 지식 동기화

| 영역 | 판정 | 근거 |
|---|---|---|
| 기획 | no-op | 제품 정책·사용자 흐름 변경이 아니라 TASK 작성 규범 변경이다. |
| 설계 | no-op | 런타임 구조·인터페이스·데이터 모델 변경이 없다. |
| 프로젝트 문서 | no-op | 기존 `op-task` 컴포넌트와 경로 안의 owner 문서 갱신이며 PROJECT 레지스트리 변경이 필요 없다. |
| CONVENTIONS | no-op | 새 전역 컨벤션이 아니라 `op-task` 전용 작성 계약이며 기존 owner 단일화 규칙을 지켰다. |
| SECURITY | no-op | 권한·인증·비밀·입력 처리 변경이 없다. |
| brain | update | 실행 규범 원문은 owner 가이드에 유지하고, 개수 제한 대신 비중복 수용 결정을 채택한 WHY를 `pages/concept/ac-core-acceptance-requirement.md`에 동기화했다. |
| memory | no-op | 재사용할 규범은 소스 문서에 반영했고 별도 세션 주의사항이 없다. |
| code-scan | no-op | 변경 파일은 기존 헤더 미보유 `pre_existing`이며 validate exit 0이다. |

## 미해결·후속

- 이번 변경은 기존 TASK에 소급 적용하지 않았다.
- 실제 다음 TASK 작성에서 의미 중복 판정이 안정적으로 적용되는지는 사용 과정에서 관찰한다.
- 배포본 `~/.opal/`에는 직접 쓰지 않았으며 install은 수행하지 않았다.

## 사용자 확인

- 캡틴의 지식 반영 피드백을 적용했으며, “태스크 마무리 후” 지시에 따라 최종 확인으로 간주하고 종료 기록을 진행한다.
