---
template: sdlc-v2
---
# TASK: TEST 단계 소요시간 단축

## Problem

opd/opds TEST 단계가 벽시계 기준으로 수 시간~수 일 걸린다. 테스트 실행 자체는 초~분 단위다(vitest 206건 5.5s, mams 실데이터 실행 19~397s). 시간은 세 곳에서 소모된다. 첫째, 사람 전용 시나리오(L3·로그인·DDL·관찰)가 자동 테스트 PASS 뒤에야 하나씩 요청되어 대기가 누적된다(mams TEST 워커 실작업 138분 vs 벽시계 약 90시간, opal-studio 004 6일). 둘째, TEST 중 요구·UX 변경이 fix 상한 밖에서 무제한 흡수된다(opal-studio 009 UX 15회, 010 fix 상한 초과 6차). 셋째, 수정마다 전 시나리오·품질·보안·전체 회귀를 다시 돌리고(`guards.md:101`, `opal-pilot-dev/SKILL.md:318`), EXECUTE·PM·TEST에서 같은 검사를 반복하며, GC 컨벤션 검사도 재작업마다 재실행되고(010에서 4회), main 분기 차이를 CLOSE 직전에야 발견한다(010 병합 56분). 행 시점이 사후 일괄 기입돼 단계별 소요를 측정할 수도 없다. 근거 전문은 같은 폴더 REQUEST.md에 있다.

## Proposed outcome

TEST 진입 시 사람 조치가 필요한 항목이 한 묶음으로 먼저 요청되고, 자동 검증은 그 대기와 병행한다. 현재 목표·수용 기준을 충족하기 위한 피드백은 정상적인 수정으로 처리하고, 목표·수용 기준 자체의 변경만 별도 기록한다. 횟수만으로 피드백을 거부하지 않는다. 수정 반복에서는 실패·영향 시나리오만 재검증하고 전체 회귀·GC 컨벤션 검사는 게이트 경계에서 1회 수행한다. main과의 분기 차이는 TEST 진입 시점에 확인된다. 태스크마다 TEST의 자동 실행 시간·사람 대기 시간·수정 반복 수를 도구로 조회할 수 있다.

## Affected users and systems

- 대상 사용자: opd/opds를 쓰는 소유자와 PM(프레임워크를 설치한 모든 프로젝트).
- 대상 시스템: `opal-pilot-dev` 스킬과 pipeline fixture, `opal-test-agent`, `op-dev-execute` fix 모드 지시, `op-dev-test-scenario`(사람 조치 항목 표기), 하네스 `guards.md`·`events.json`의 `stage.test` 문서 집합(필요 시 TEST 전용 하네스 문서 신설), `state-tool`(요구 변경 행 구분·소요 조회), `worktree-tool` 또는 TEST 진입 분기 확인 절차, 관련 docs와 install 배포.
- 제외: test-tool 실행기·resolver·스키마·템플릿과 `--changed-files` 실행 연결(태스크 161 소유), GC 스킬·체커 내부 로직과 증분 재검사(제안 B·D 소유), oppl/oppd/oppb 파이프라인, 모드 체계(agentic/semi-agentic/interactive) 자체 변경.

## Constraints

- C-1: docs/CONVENTIONS.md의 배포 경계를 지킨다. `~/.opal/`을 직접 수정하지 않고 프로젝트 소스 수정 후 정식 install로 배포하고 배포본을 검증한다.
- C-2: 독립 검증 경계를 유지한다. TEST 실행·판정은 계속 `opal-test-agent`가, 컨벤션 검사는 `opal-convention-checker`가 수행하며 PM 직접 판정으로 대체하지 않는다.
- C-3: 게이트 경계에서의 전체 회귀 1회와 모든 필수 시나리오 PASS 요건을 약화하지 않는다. 재검증 축소는 반복 구간에만 적용한다.
- C-4: 태스크 161이 소유한 test-tool 실행기·resolver·스키마·템플릿 파일과 GC 스킬·체커 내부 파일을 수정하지 않는다. 인접 계약이 필요하면 소비 측 규칙만 정의하고 의존을 문서화한다.
- C-5: 규칙은 SSOT 한 곳에 두고 하위 문서는 참조한다(PRINCIPLES §Governance). 반드시 지켜야 하는 규칙은 가능한 한 도구로 집행한다.
- C-6: 기존 태스크 재개 호환을 깨지 않는다. 저장 행·legacy 태스크는 기존 방식으로 재개된다.
- C-7: 허브의 미커밋 변경·타 태스크(161·128) 파일을 수정하거나 포함하지 않는다.

## Acceptance criteria

- AC-1: TEST 진입 시 사람 조치가 필요한 시나리오와 선행 조치(로그인·DDL·권한·관찰)가 한 번의 묶음 요청으로 제시되고, 그 대기 중에도 자동 시나리오 실행이 진행되는 절차가 pilot·test-agent에 정의되어 있다. 고정 사례에서 사람 조치 요청이 자동 테스트 완료 전에 발생함을 확인한다.
- AC-2: 현재 목표·수용 기준을 충족하기 위한 사용자 피드백과 TEST 지적은 fix로 기록한다. 합의된 목표·수용 기준 자체의 변경은 별도 유형으로 기록해 소요를 분석하되, 횟수만으로 수용을 거부하지 않는다. 고정 사례에서 네 번째 변경 행도 수용·계수되는지 확인한다. 범위 밖 요청의 새 태스크·PLAN 재진입 여부는 내용에 따라 사용자와 결정한다.
- AC-3: fix 반복의 재검증 범위가 실패 시나리오 + 변경 파일에 영향받는 시나리오로 정의되고, 전체 회귀·lint/type·보안 검사는 PM Gate 경계에서 1회 수행하도록 규칙(`guards.md` 회귀 방지 조항, pilot fix 지시, test-agent 절차)이 일관되게 바뀌어 있다. 구형 "매 수정마다 이전 PASS 전건 재실행" 문구가 소스에 남지 않는다.
- AC-4: EXECUTE에서 같은 커밋 기준으로 통과한 lint/type/unit 결과가 있으면 TEST가 이를 재사용하고 재실행하지 않는 조건이 정의되어 있으며, 재사용 시 증거 경로가 test-scenario.json 또는 TEST 보고에 남는다.
- AC-5: GC 컨벤션 검사 호출이 TEST 게이트당 최종 1회(최종 수정 후)로 정의되고, 재작업 중간 호출이 필수가 아님이 pm-review-gate·pilot 규칙에 일관되게 반영되어 있다.
- AC-6: TEST 진입 시 기본 브랜치와의 분기(선행 merge된 변경) 확인 단계가 있고, 분기가 있으면 통합 후 TEST를 시작하는 절차가 정의되어 있다. 실제 worktree에서 분기 있음/없음 두 사례를 실행 확인한다.
- AC-7: 태스크의 TEST 자동 실행 시간·사람 대기 시간·fix/요구 변경 반복 수를 조회하는 도구 명령이 있고, 사후 일괄 mark로 시점이 왜곡되지 않도록 실제 이벤트 시각에 기반한다. 이 태스크 자체와 기존 태스크 1건 이상에서 실제 출력으로 확인한다.
- AC-8: `stage.test` 이벤트가 TEST 실행 규칙 문서를 로드하도록 `events.json`이 갱신되고, event-loader load/verify가 통과한다.
- AC-9: 수정 1회당 디스패치 고정비를 줄이는 경량 경로(예: 같은 단계·같은 manifest hash 내 receipt 재사용 조건)가 검토되어, 채택 시 도구 검증과 함께 반영되고 미채택 시 근거가 PLAN에 기록된다.
- AC-10: 관련 기존 회귀 테스트(state-tool·event-loader·worktree-tool 등 변경 도구)가 통과하고, 정식 install 후 배포본에서 변경된 스킬·하네스·도구 진입점을 검증한 결과가 남는다.
