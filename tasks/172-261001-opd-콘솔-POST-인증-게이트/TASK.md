---
template: sdlc-v2
---
# TASK: OPAL Console 상태 변경 API 인증 게이트와 구형 Brain 실행 차단 (Gateway 제안 Phase 0)

## Problem

OPAL Console backend는 127.0.0.1:7823에 바인딩되지만, LLM 실행과 설정 쓰기를 일으키는 POST 3종(`/api/brain/prime`, `/api/brain/query`, `/api/config/prewarm`)이 인증·Origin/Host·CSRF 검사 없이 열려 있다(`dashboard/backend/routers/brain.py:155`, `dashboard/backend/routers/brain.py:207`, `dashboard/backend/routers/config.py:84`). CORS middleware만 등록되어 있으며(`dashboard/backend/main.py:126-134`), CORS는 브라우저의 응답 읽기만 제한할 뿐 다른 사이트의 요청 전송이나 DNS rebinding을 막지 못한다. 따라서 사용자가 연 임의 웹 페이지가 로컬 `claude -p` 실행이나 설정 파일 쓰기를 일으킬 수 있다.

구형 Brain 경로는 Bash 전체를 허용한 `claude -p`로 `//opbr query --read-only`를 실행한다(`dashboard/backend/adapters/opbr_adapter.py:100-175`). 서버 기동 시 `prewarm_projects`가 설정되어 있으면 사용자 조작 없이도 이 프로세스가 선프라임된다(`dashboard/backend/main.py:57-70`). 이 실행을 사용자가 위험을 이해하고 켜는 장치가 없다.

`opal-cli console open`은 health 확인 뒤 고정 URL을 브라우저로 연다(`opal/tools/opal-cli/lib/console.sh:425-429`). 인증이 도입되면 사용자가 Console에 들어갈 정상 진입 경로가 필요하다.

설계 근거는 허브의 미추적 제안서 `/Volumes/Data/AIStudio/workspace/ai-framework/docs/proposals/opal-agent-gateway-execution-policy.md` §6.2·§7.1·§8·§9 Phase 0이다. 이 제안서는 Phase 0 통과를 이후 모든 Phase의 진입 조건으로 정한다(같은 문서 §9 Phase 0 완료 기준).

## Proposed outcome

- Console의 상태 변경 요청과 LLM 실행 요청은 정상 진입으로 발급받은 브라우저 세션에서, 허용된 Origin/Host와 CSRF 검증을 통과해야만 처리된다. 다른 사이트, DNS rebinding, 무세션 요청은 실제 작업 전에 거절된다.
- 사용자는 `opal-cli console open`으로 Console을 열면 별도 입력 없이 인증된 상태가 된다. 세션이 없는 북마크로 접속하면 민감 데이터가 없는 잠금 화면과 재진입 안내만 본다.
- 구형 `claude -p` Brain은 기본적으로 꺼져 있다. 인증된 사용자가 위험(파일 읽기 범위 비제한, 임의 Bash, 네트워크 유출)을 화면에서 확인하고 명시적으로 켰을 때만 동작한다. 꺼져 있으면 HTTP 요청, 서버 기동 선프라임, 내부 Registry 직접 호출 어느 경로로도 새 `claude -p` 프로세스가 생기지 않는다.
- Brain 첫 진입 화면과 업그레이드 안내는 새 Brain이 나오기 전까지 Brain을 기본적으로 쓸 수 없다는 사실과, 구형 경로를 위험을 수락하고 켜는 선택지를 설명한다.

## Affected users and systems

- 사용자: 로컬에서 OPAL Console을 쓰는 개발자. 기존 북마크 사용 방식과 Brain 기본 가용성이 바뀐다.
- 시스템: Console backend(`dashboard/backend/` — FastAPI 앱·Brain/설정 라우터·Brain 세션 Registry·opbr adapter·설정 저장), Console frontend(`dashboard/frontend/` — API 호출, 잠금 화면, Brain 진입 안내, 구형 Brain 토글), `opal-cli console`(`opal/tools/opal-cli/lib/console.sh`)과 그 회귀 테스트, test-tool E2E의 Console SUT 진입 경로.
- 포함: 제안서 §9 Phase 0의 1~5항.
- 제외: Agent Gateway 서비스, Account·Profile·Binding, `opal-agent` ACP·resolver, 새 Brain transport, 워커 전환(Phase 1 이후). 인증 없는 `/health` 외의 기존 GET 응답 형식 변경은 Phase 0 3항의 점검 결과로만 다룬다.

## Constraints

- C-1: Console의 127.0.0.1 바인딩과 외부 비노출 원칙을 유지하며, 인증 도입이 공개 포트나 원격 접근을 새로 열지 않는다.
- C-2: 세션·진입 token·CSRF 값은 URL query·서버 로그·Referrer·테스트 로그·artifact에 남지 않는다.
- C-3: 구형 Brain 실행 허용 여부는 서버 측에 저장된 값이 결정한다. 업그레이드나 기존 설정(`prewarm_projects` 포함)이 이를 자동으로 켜지 않으며, 화면 경고 표시만으로 서버 차단을 대체하지 않는다.
- C-4: 프로젝트 공통 계약(`.opal/AGENT.md` §금지사항 — `~/.opal/` 직접 편집 금지, 하드코딩 플랫폼 분기 금지)과 `docs/CONVENTIONS.md`를 따른다.

## Acceptance criteria

- AC-1: Console의 모든 상태 변경 API(현재 POST 3종과 이번에 추가되는 API)와 WebSocket handshake는 유효한 브라우저 세션, 허용된 Origin/Host, CSRF 검증을 모두 통과할 때만 실제 작업을 수행한다. 다른 사이트의 단순 요청·JSON 요청, 허용 목록 밖 Host(DNS rebinding), 무세션·위조 요청은 작업 전에 거절되고 LLM 실행이나 설정 쓰기가 0회다.
- AC-2: `opal-cli console open`은 짧은 수명의 1회성 진입 token으로 인증 세션을 만든 뒤 Console을 열며, token은 URL fragment로만 전달되고 교환 즉시 주소창에서 제거된다. 만료되었거나 이미 사용된 token은 세션을 만들지 못한다. 유효한 세션 cookie가 있으면 기본 URL 북마크가 바로 열리고, 세션이 없으면 민감 데이터 없는 잠금 화면과 재진입 안내만 표시된다.
- AC-3: 구형 Brain 허용 값이 꺼져 있으면 Brain prime·query HTTP 요청, 서버 기동 시 선프라임, Registry의 prime·prewarm·submit·ask·풀 리필 직접 호출, adapter 최종 실행 지점 어느 경로에서도 새 `claude -p` 프로세스가 0회 생성된다. 인증된 사용자가 위험을 확인하고 켠 경우에만 구형 Brain이 `legacy`로 표시되어 동작한다. 끄는 요청이 완료된 뒤에는 새 프로세스가 생기지 않으며, 이미 시작된 turn은 끝까지 진행되고 그 사실이 화면에 표시된다.
- AC-4: Brain 첫 진입 화면은 새 Brain 출시 전까지 Brain이 기본적으로 사용 불가하다는 사실과, 구형 경로의 위험을 수락하고 켜는 선택지를 함께 보여 준다.
- AC-5: 인증 없는 `/health`는 데몬 상태만 응답하고 프로젝트·설정·계정 정보를 포함하지 않는다. 민감한 프로젝트 데이터를 반환하는 기존 GET 경로는 같은 세션 검사를 거치며, 무세션 접근은 데이터 없이 거절된다.
- AC-6: Console E2E SUT는 사용자 Console의 7823 포트를 쓰지 않고 자체 포트·HOME의 테스트 서버에서 같은 진입 token 교환으로 인증된 상태가 되어 기존 시나리오를 수행한다. 고정 URL을 전제로 한 기존 `console open` 회귀 테스트는 새 진입 계약을 검증하도록 바뀌어 통과한다.
</content>
</invoke>
