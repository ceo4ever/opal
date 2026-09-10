---
module: pm-activation
role: project-aware assistant에서 PM으로 승격하는 이벤트 경계의 단일 SSOT
load: pm.activate
---

# PM Activation

프로젝트 감지만으로 PM을 활성화하지 않는다. 일반 대화는 project-aware assistant 상태를
유지하고, 프로젝트 작업 요청 또는 `//` 커맨드가 들어온 시점에 `pm.activate` 이벤트를
발생시킨다.

## 활성화 계약

1. 현재 프로젝트 루트를 `harness/worktree.md`의 허브 루트 규칙으로 확정한다.
2. 실행 위치에 맞는 event-loader로 `load --event pm.activate --project-root <hub>`를 호출한다.
3. 성공 응답의 문서 전문을 모두 소비한다. 필수 문서 집합은 `events.json`만이 소유하며 이 문서에 복제하지 않는다.
4. 응답 event가 `pm.activate`이고 receipt가 현재 manifest·문서 해시와 일치함을 확인한 뒤 PM 행동을 시작한다.
5. load 실패, 필수 문서 누락, stale receipt, wrong-event receipt 중 하나라도 발생하면 PM 활성화를 중단하고 구조화 오류를 blocker로 반환한다.

`session.disabled`는 OPAL 문서를 0건 로드하는 순수 모드이므로 이 경계에 도달하지 않는다.
`session.worker`는 전역 부트스트랩을 건너뛴 뒤 디스패치된 worker 이벤트 계약을 따르는
별도 경로이며 PM 활성화의 대체 경로가 아니다.
