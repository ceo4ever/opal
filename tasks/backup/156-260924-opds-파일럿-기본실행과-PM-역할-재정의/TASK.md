---
template: sdlc-v2
---
# TASK: 파일럿 기본 실행 정책과 PM 역할 재정의

## Problem
사용자는 신규 개발 태스크마다 `--agentic --wt`(opd/opds는 `--pm`까지)를 반복 입력하고 있다. 현재 설치본은 신규 태스크 기본 mode를 `semi-agentic`, workspace를 허브, actor를 `worker`로 두며(`opal/core/references/harness/modes.md` §라우팅 계약 3, `opal/core/references/harness/worktree.md` §`--wt` 미사용 시), `--pm`은 "PM이 단계 skill을 직접 수행"하는 의미다(`opal/core/references/harness/actor.md` §`--pm` 실행 계약). 사용자가 원하는 PM 역할은 요구사항·분석·계획·테스트 시나리오 작성과 조율이며 구현은 전문 워커가 맡는 구조다.

또한 현행 문서에 모순이 있다. `actor.md` §독립 검증 경계는 `actor=pm`의 CLOSE 첫 행에 `--owner user`를 요구하지만 `opal-pilot-dev/SKILL.md` §CLOSE 전이는 actor 무관 자동 CLOSE를 말한다. EXECUTE 분기·TEST FAIL 수정 경로·TEST-SCENARIO 작성자 설명도 actor별로 일관되지 않다. `harness/task-process.md` 스텝 4.5는 worktree 생성 실패 시 허브 `tasks/`로 폴백해 허브에서 코드 수정을 시작할 수 있다.

## Proposed outcome
신규 opd/opds/oppd/oppl/oppb 태스크는 플래그 없이도 agentic과 worktree로 시작한다(oppb는 기존 프로젝트 worktree 1개·Supervisor 구조 유지). opd/opds 신규 태스크는 기본으로 재정의된 PM 조율 actor로 실행되어, PM이 TASK·분석·PLAN·TEST-SCENARIO와 분배·소유권·검토·재작업·마감을 맡고 FE/BE/DB 등 전문 워커가 구현·자가 점검·FAIL 수정을 맡는다. 기존 태스크 재개는 저장된 mode·workspace·actor를 바꾸지 않는다. 명시 해제·충돌 플래그는 도구가 결정론적으로 해석하고, worktree 생성이 실패하면 허브에서 코드를 수정하지 않고 멈춘다.

## Affected users and systems
- 포함: OPAL FW 소스의 harness 문서(`actor`·`worktree`·`modes`·`task-process`·`guards` 등 관련 owner 문서), `opal-pilot-dev`(opd/opds)와 `opal-pilot-project-dev`(oppd)·`opal-pilot-project-loop`(oppl)·`opal-pilot-project-build`(oppb) Pilot 문서·pipeline fixture, `state-tool`(resolve-mode·init)·`worktree-tool`·`worktree-launcher` 중 기본값·실패 정책 해석 경로, 스킬 커맨드 문법 노출 문서, 회귀 테스트, 관련 docs·brain.
- 사용자: OPAL을 설치해 실제 구현 프로젝트에서 Pilot을 쓰는 사용자와 그 PM 에이전트.
- 제외: opp·opdw·opwt·opsdd·opdd·opgc 등 다른 Pilot의 기본값, `oppm`(opal-self-pm) 계약, 자동 push/merge 권한.

## Constraints
- C-1: 기본값 변경 대상은 opd·opds·oppd·oppl·oppb 5개 Pilot의 신규 태스크뿐이다. 다른 Pilot의 mode·workspace·actor 기본값은 바뀌지 않는다.
- C-2: 기본 PM 조율 actor는 opd/opds에만 적용하며 oppd·oppl·oppb로 확대하지 않는다.
- C-3: 기존 태스크 재개는 저장된 mode·workspace(worktree 여부·작업본)·actor를 상속하고 신규 기본값으로 바꾸지 않는다.
- C-4: 기본 PM 조율 해제 옵션 이름과 의미는 기존 `actor=worker` 저장값·기존 `--pm` 의미와 혼동되지 않아야 한다. oppb의 worktree 필수 구조에 맞지 않는 workspace 해제는 조용히 무시하거나 허브로 폴백하지 않고 명시 거부한다.
- C-5: 독립 evaluator(`op-scenario-gate`)·opal-test-agent·조건부 보안/컨벤션 검사·실제 실행 증거·기존 state gate는 어느 actor·mode에서도 생략되지 않는다.
- C-6: agentic 기본값은 기존 지원 기능의 기본값 변경이다. 실제 미해결 결정·권한 경계·독립 검증·재시도/예산 제한·oppb P5 사용자 전용 merge 게이트·push/merge/deploy 승인 경계를 약화하지 않는다.
- C-7: 규칙은 다른 실제 구현 프로젝트에서 재사용 가능해야 하며 플랫폼 분기는 adapter 계층에만 둔다. `~/.opal/` 배포본을 직접 수정하지 않고 소스 수정 후 install로 반영한다.
- C-8: 이 태스크 자체는 착수 시점 설치본의 현행 `--pm` 계약(PM 직접 수행, 독립 검증 워커 유지)으로 실행한다. 목표 계약은 merge·install 이후 생성되는 신규 태스크부터 적용되며 그 시점을 DONE.md에 기록한다.
- C-9: 허브 working tree의 기존 미커밋 변경(`.opal/MEMORY.json` 등)을 보존하고 이 태스크 커밋에 포함하지 않는다. 테스트 명령·환경·결과·실패와 재실행 근거를 태스크 폴더와 run-log에 남긴다.

## Acceptance criteria
- AC-1: 플래그 없는 신규 opd·opds·oppd·oppl·oppb 태스크에서 도구의 mode 판정이 `agentic`이고 worktree 사용이 기본 선택된다. opp 등 대상 밖 Pilot의 신규 태스크는 기존 `semi-agentic`·허브 기본값을 유지한다(자동 테스트로 확인).
- AC-2: 무플래그 신규 opd/opds 태스크의 저장 actor가 새 PM 조율 값이고, oppd·oppl·oppb 신규 태스크는 PM 조율 actor를 받지 않는다(자동 테스트로 확인).
- AC-3: 저장 mode·worktree·actor가 있는 기존 태스크를 무플래그로 재개하면 세 값이 모두 그대로 유지된다. legacy `actor=pm`·actor 키 부재 태스크도 기존 의미로 해석된다(자동 테스트로 확인).
- AC-4: `--wt`/`--no-wt` 동시 지정, 모드 플래그 2개 이상, PM 조율 해제와 `--pm` 동시 지정 같은 충돌은 도구가 고유 오류 코드로 거부하고, oppb의 `--no-wt`는 명시 오류로 거부한다(자동 테스트로 확인).
- AC-5: 재정의된 opd/opds PM 조율 계약에서 구현·자가 점검·TEST FAIL 수정 주체가 전문 워커이고, 병렬은 의존성 없음·변경 파일 비중첩일 때만 허용되며, PM이 분배·파일 소유권·결과 검토·재작업·마감을 맡는다는 규칙이 SSOT 한 곳에 있고 Pilot 문서가 이를 참조한다. EXECUTE 분기·TEST FAIL 수정 경로·TEST-SCENARIO 작성자·CLOSE 전이 설명 간 모순이 0건이다.
- AC-6: worktree 생성 실패 시 신규 기본 경로와 명시 `--wt` 모두 허브 `tasks/`로 폴백해 코드 수정을 시작하지 않고 실패 사유와 함께 차단된다. 사용자가 명시 `--no-wt`를 선택한 경우만 허브 경로를 쓴다. 상위/하위 작업본 중복, lease 이관, launcher 실패, 재개·복구 경로를 점검한 결과가 문서와 테스트에 반영된다.
- AC-7: 변경된 도구의 기존 회귀 테스트와 신규 테스트가 모두 통과하고 install 후 설치본에서 새 기본값이 관측된다. opal-e2e 스킬 적용 여부를 검토해 실행/미실행/차단 근거를 남긴다.
- AC-8: PROJECT.md 레지스트리 기반으로 식별한 관련 docs(PROJECT.md·README·스킬 커맨드 문서 등)와 brain이 새 계약으로 갱신되고, 구형 `--pm` 의미(PM 직접 구현)를 현행 기본 계약으로 서술하는 문장이 대상 문서에 남지 않는다.
