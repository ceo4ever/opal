---
name: opal-pilot-dev2
description: >-
  AI-native SDLC 파일럿 opd2. 아이디어·변경·인시던트를 intent, spec, plan,
  구현, 독립 검증, 리뷰, 승인된 배포와 관측으로 연결한다.
  opd2 또는 opal-pilot-dev2 요청에 적용하며 semi-agentic, agentic, wt를 지원한다.
  기존 opd 호출이나 설명만 요청한 작업에는 적용하지 않는다.
---
# OPAL Pilot Dev 2

자체 AI-native 생명주기를 실행한다. 기존 opd에서는 진행 모드의 의미와 워크트리
생성·기동·소유권·체크포인트·마감 절차를 가져온다. 기존 opd Full profile로 전체
작업을 넘기거나 intent/spec을 TASK/PLAN으로 대체하지 않는다.

## 진입

1. 프로젝트 지침, 사용자 목표, 신규/재개 여부를 읽는다. 별도 배포 요청이 없으면
   delivery=build(리뷰 완료·머지 대기)로 한다.
2. [실행 연결](references/execution.md)로 mode/workspace를 확정한다. 신규 기본은
   agentic + wt. semi-agentic/agentic과 wt/no-wt는 독립 축이다.
3. wt면 OPAL이 발급한 canonical task path와 작업본을 사용한다. 생성 실패는 중단한다.
4. [생명주기](references/lifecycle.md), [아티팩트](references/artifacts.md)를 읽고
   scripts/lifecycle.py로 초기화한다. 재개는 status 결과로 이어간다.

호출은 python3 <skill-dir>/scripts/lifecycle.py <command> <task>다.

- init: --repo <git-root> --change-id <id> --mode agentic --workspace worktree --worktree-receipt <json>
- status: 저장 상태와 현재 단계를 조회한다.
- transition: --actor coordinator. 도구가 전이를 허용할 때만 다음 단계로 이동한다.

## 필요한 시점에 읽기

| 시점 | 문서 | 역할 |
|---|---|---|
| 시작·재개 | agents/coordinator.md, references/lifecycle.md | Coordinator |
| intent/spec/plan | references/artifacts.md, references/risk-model.md | Coordinator + 사용자 |
| 구현 | agents/builder.md, references/testing.md | Builder |
| 독립 검증 | agents/verifier.md, references/testing.md | Verifier |
| 리뷰 | agents/reviewer.md, references/governance.md | Reviewer |
| 배포·관측 | references/rollout.md, references/metrics.md | 승인된 실행자·운영 담당자 |

에이전트 문서는 디스패치 계약이다. 해당 단계에서 실제 독립 에이전트를 호출하고 role
문서·아티팩트·소유 파일·검증 명령을 전달한다. Builder는 Verifier/Reviewer를 겸하지 않는다.
역할 문자열이 다르다는 것만으로 독립 실행 증거가 되지는 않는다.

## 진행 계약

- semi-agentic: intent, spec, plan/시나리오까지 사용자 검토, 이후 정상 개발·검증·리뷰·마감 자율.
- agentic: 정상 단계 자율 진행. 미결정 요구·외부 계약·고위험 승인·권한 부족·재시도 상한은 대기.
- 상태 변경은 lifecycle 도구만 수행한다. journal이 기준이고 state.json은 읽기 projection이다.
- 테스트 명령은 실제 실행한다. 실패·환경 부재·타임아웃은 통과가 아니다.
- 증거 뒤 코드/아티팩트가 바뀌면 재검증한다. merge/push/배포는 자율 모드만으로 승인되지 않는다.
- 구조·해시·증거 연결은 도구가, 요구 의미와 품질은 독립 에이전트가 검사한다.

## 완료

build는 REVIEW 통과 후 DONE.md와 함께 CLOSED/ready_for_merge로 끝난다.
release는 RELEASE·OBSERVE 실행 증거와 승인 후 CLOSED/observed로 끝난다.
배포하지 않은 결과를 배포 완료라고 보고하지 않는다.

패키지 검사: python3 -m unittest discover -s <skill-dir>/tests -v.
행동 평가는 [evals.md](references/evals.md)를 사용한다.
현재 검증 범위와 미실행 영역은 [validation.md](references/validation.md)에 기록한다.
전역 //opd2 별칭 등록은 별도 통합이며 현재 폴더는 직접 사용할 스킬 원본이다.
