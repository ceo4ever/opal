---
type: concept
title: 목킹 전용 어댑터 검증은 응답 스키마 불일치를 통과시킨다
tags:
- 테스트
- 어댑터
- 외부CLI
- fixture
sources:
- tasks/145-260919-opds-워크트리-터미널-런처-orca-배선/DONE.md
- opal/tools/worktree-launcher/worktree_launcher/adapters/orca.py
- tasks/147-260919-opds-PM-보고-활동이벤트-정지판정-관측배선/DONE.md
- opal/tools/run-log-tool/adapters/agent_tool_adapter.py
related:
- worktree-tool
created: '2026-09-19'
updated: '2026-09-20'
status: active
---
## 개요

외부 CLI를 subprocess로 부르는 어댑터를 **목킹만으로 검증하면, 구현이 가정한 응답 스키마를 테스트가 그대로 되먹임해 불일치가 영구히 통과한다.** 테스트가 확인하는 것은 "어댑터가 외부 도구의 응답을 읽는가"가 아니라 "어댑터가 자기가 만든 fixture를 읽는가"가 되기 때문이다.

## 관측된 사례

### 태스크 145 — Orca CLI 응답 랩핑

태스크 145 이전, `worktree_launcher.adapters.orca`는 `orca terminal create --json` 응답을 `response["terminal"]`로 읽었다. 실제 응답은 `{"ok":true,"result":{"terminal":{...}}}`였다. 결과는 조용한 실패였다 — **터미널은 실제로 떴는데** `adapter_handle`·`reported_cwd`가 `null`이 되어 `launcher_core`가 `launch_receipt_missing`으로 판정하고 상태를 원자 복귀시켰다. 고아 터미널이 남았고, 로그상으로는 "기동 실패"로 보였다.

이 결함이 통과한 경로는 fixture였다. `fixtures/launcher/orca-json-response.json`이 `_fixture_note`에 "실제 stdout 스키마는 미실측"이라고 **스스로 적어 두고도** 그 가정 위에서 테스트가 초록으로 돌았다. 실측 응답에는 `cwd`도 `worktree_selector`도 없었고 cwd 원천은 `worktreeId`(`<repoId>::<path>`) 하나였다.
이 사례의 런처 소유권·회수 경계는 [[worktree-tool]]에서 관리한다.

### 태스크 147 — Claude Agent 훅 이름과 terminal 봉투

태스크 147의 첫 배선은 legacy `PostToolUse:Task`와 `<task-notification>` 종료 알림을 전제로 했다. 단위 테스트의 형식 복제 fixture는 이 전제를 그대로 재생하므로 통과했다.

실제 Claude Code 2.1.278을 호출하자 다음 두 차이가 연속으로 드러났다.

1. 완료 hook 이름은 `PostToolUse:Task`가 아니라 `PostToolUse:Agent`였다. 첫 실행에서는 어댑터 hook 자체가 호출되지 않았다.
2. matcher를 `Agent|Task`로 고친 뒤에는 시작·활동은 남았지만 terminal이 0건이였다. 현행 Agent 완료 원천은 legacy 알림이 아니라 구조화 `toolUseResult.status=completed`였다.

최종 어댑터는 현행 Agent와 legacy Task를 단일 정규화 경로로 보존하고, 구조화 결과의 canonical JSON 해시만 사건 원천으로 저장했다. 설치본으로 다시 실행한 실제 Agent에서 같은 worker run의 `worker.started`·`activity`·`worker.completed` 3경계가 모두 남아야 비로소 완료로 판정했다.

## 왜 단위 테스트로는 못 잡는가

목킹의 경계는 "우리 코드의 분기"까지다. 외부 도구의 **응답 형태와 훅 이름**은 우리 코드가 아니라 그 도구가 소유하므로, 목으로 넣은 순간 검증 대상에서 빠진다. 스키마 가정이 틀려도 목과 파서가 같은 가정을 공유하면 둘 다 일관되게 틀린 채 통과한다.

## 대응 — 실물 대조를 적합성의 일부로 강제한다

1. **fixture를 실측 캡처로 만든다.** 캡처 명령·일시·도구 버전을 fixture 자신에 기록한다. "미실측"이라고 적힌 fixture는 결함 신호다.
2. **live 대조 1건을 opt-in 테스트로 둔다.** 환경변수와 도구 존재를 둘 다 만족할 때만 돌고 그 외에는 skip이라 기본 스위트를 느리게 하지 않는다. teardown은 예외 경로를 포함해 자기 생성물만 회수한다.
3. **어댑터는 시작·중간·종료 경계를 따로 증명한다.** 시작 사건 1건만으로 채택을 주장하지 않고, 증분 활동과 terminal이 같은 실행 식별자로 연결되는지 본다.
4. **fixture의 역할을 문서에 못박는다.** fixture는 캡처 시점의 형태만 고정하고, 버전 드리프트는 live 테스트만이 잡는다. 적합성 스위트 docstring에 이 경계를 적어 다음 수정이 목킹으로 대체하지 못하게 한다.
5. **실측과 프롬프트·계획 문면이 다르면 실측이 이긴다.** 계획은 실측 형태를 반영해 고치고, legacy 경로는 현행 경로와 분리해 후방 호환으로만 남긴다.

## 적용 범위

외부 CLI·HTTP API·에이전트 하네스 훅을 감싸는 모든 어댑터에 해당한다. 사용자 세션·터미널·브라우저·서브에이전트처럼 **부수 효과가 큰 도구**일수록 목킹 유혹이 크고, 동시에 응답 형태 불일치의 비용도 크다.
