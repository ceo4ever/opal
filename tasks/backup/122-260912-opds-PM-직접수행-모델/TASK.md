---
template: sdlc-v2
---
# TASK: PM 직접 수행 모델 — actor 축 신설과 L2 대체

## Problem

현행 `L2 경량 트랙`은 "PM이 직접 수행한다"는 실행 주체 결정을 "작업이 작다"는 규모 조건(파일 1~2개·단순 수정·동작검증 불요)에 묶어 놓았다. 이 때문에 세 가지 비용이 발생한다.

1. Pilot의 단계·상태·Gate를 유지한 채 PM이 직접 구현할 공식 경로가 없다. 규모가 조금만 커지면 워커 위임 외 선택지가 없다.
2. 대화 도중 요구를 발견하고 다시 조사하는 적응형 작업은 고정 단계 Pilot과 무상태 L2 중 하나로만 강제 선택된다.
3. 직접 수행을 마칠 때 기획·설계·문서·brain·memory 영향 확인이 하나의 완료 계약으로 묶여 있지 않아 낡은 원천이 남는다.

또한 사용자 대면 용어가 `L2 경량 트랙`·`direct-workflow`·`direct-adaptive`로 흩어져 있어 어떤 진입점이 무엇을 보장하는지 문서만으로 판별할 수 없다.

## Proposed outcome

사용자는 목적이 다른 두 개의 PM 직접 수행 진입점을 명확히 구분해서 쓴다.

- `//opd --pm <작업>` / `//opds --pm <작업>` — Dev Pilot의 단계·산출물·`state.json`·event receipt·PM Gate·CLOSE 승인을 **그대로 유지한 채** 구현 주체만 PM으로 바꾼다.
- `//oppm <작업>` — 질문 한 개와 PM 권고 답안을 반복하는 대화형 PM 작업 루프(`opal-self-pm`)를 발동한다. 쓰기 전 계약 승인, 완료 전 지식 영향 전수 판정, 사용자 최종 확인 전 종료 금지를 보장한다.

`--pm`은 workflow도 mode도 아닌 **actor 축**으로 파싱되어 `--interactive`/`--agentic`/`--wt`와 자유롭게 조합된다. 규모를 근거로 직접 수행 여부를 제한하던 `L2 경량 트랙`과 `direct-workflow`·`direct-adaptive` 용어는 owner 문서에서 사라진다.

## Affected users and systems

- **사용자**: OPAL PM을 쓰는 프로젝트 소유자 — 진입점 3종(`//opd`, `//opd --pm`, `//oppm`)의 선택 기준이 바뀐다.
- **하네스 owner 문서**: `opal/core/references/opal-pm.md`(§12 L2), `harness/guards.md`(actor 분기·승인 경계), `harness/capability.md`(PM capability 선택), `pm/dispatch-process.md`(Steps 1~3 preflight 분리).
- **Pilot·단계 스킬**: `opal-pilot-dev`(`opd`/`opds`) — actor 인지 실행 계약과 `--pm` 파싱.
- **신규 컴포넌트**: `opal-self-pm` 스킬 + `//oppm` alias + 경량 실행 기록.
- **배포·문서**: `README.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, 스킬 커맨드 레지스트리, `scripts/install-mac.sh` 어댑터.
- **범위 제외**: `opwt`·`opsdd`·`oppd`·`oppl`로의 `--pm` 확산(제안서 §12-4)과 전 Pilot 회귀 시나리오(§12-6). 본 태스크는 제안서 §12가 권고한 "한 Pilot 수직 검증"까지만 수행한다.
- **범위 제외**: GC 검사 본체 분리(제안서 §8) — 태스크 120에서 `op-gc-security`·`op-gc-convention`·`op-gc-report`로 이미 완료됨. 본 태스크는 그 실명 3종을 직접 수행 경로에서 **호출**하는 연동만 다룬다.

## Constraints

- C-1: 배포 경계를 지킨다 — `~/.opal/` 배포본을 직접 편집하지 않고 프로젝트 소스(`opal/`, `skills/`, `scripts/`)만 수정한 뒤 install로 재배포한다.
- C-2: `--pm` 태스크에서도 기존 Pilot의 단계 순서·산출물·`state.json`·event receipt·observability·PM Gate·CLOSE 사용자 승인을 하나도 약화하지 않는다.
- C-3: `--pm` 미지정 기본 경로(`//opd`, `//opds`)의 동작·산출물·상태 스키마는 바이트 수준으로 현행을 유지한다.
- C-4: 직접 수행 선택은 작업 방식 승인일 뿐이며 외부 skill·package 설치, 프로젝트 밖 쓰기, 비가역 변경, commit·push·배포는 기존 별도 승인 경계를 유지한다.
- C-5: 서브에이전트는 독립 검토·평가·테스트에만 사용한다. 구현·파일 수정을 서브에이전트가 수행하면 그 실행 단위는 직접 수행으로 기록하지 않는다.
- C-6: 규칙 원문은 owner 문서 한 곳에만 둔다 — `opal-harness.md`는 호환 인덱스이므로 원문을 복제하지 않고, 스킬·에이전트 문서는 owner를 참조만 한다.
- C-7: 플랫폼 분기를 로직에 넣지 않는다 — 명령·옵션 노출 차이는 `scripts/install-mac.sh`의 어댑터 계층에서만 처리한다.
- C-8: 제안서 §8이 쓴 가칭 `op-security-check`·`op-convention-check` 대신 실제 배포 명칭 `op-gc-security`·`op-gc-convention`·`op-gc-report`를 사용한다.

## Acceptance criteria

- AC-1: `//opd --pm`, `//opds --pm`, `//opd --pm --agentic --wt`가 각각 actor=pm과 해당 mode·워크스페이스 축으로 파싱되며, `--pm`이 `mode_flag_conflict` 판정의 모드 플래그 개수에 포함되지 않는다.
- AC-2: `--pm`으로 실행한 Dev Pilot 태스크 1건이 `state.json` 행 구성·event receipt 검증·PM Gate·CLOSE 사용자 승인 게이트를 `--pm` 없는 실행과 동일하게 통과한다.
- AC-3: `--pm` 실행에서 PLAN `Work items`의 `담당`이 `PM`으로 기록되고, `worker.dispatch` load·verify는 독립 검증자(test-agent·evaluator·checker)를 호출하는 시점에만 발생한다.
- AC-4: `--pm` 없이 실행한 `//opds` 태스크의 `state.json` 스키마와 STATE 렌더 결과에 actor 관련 키가 **추가되지 않는다**(기본 경로 무변경 확인).
- AC-5: `//oppm`이 `opal-self-pm`을 발동하고, 스킬이 질문 1개 + 선택지 + PM 권고 답안 + 권고 이유 + 다음 조회를 한 묶음으로 제시하는 루프로 동작한다.
- AC-6: `opal-self-pm`이 파일·설정·데이터 쓰기 전에 목표·완료조건·포함/제외 범위·변경 대상·확정 결정·검증 방법·지식 영향 6항목 계약을 제시하고 사용자 승인을 받은 뒤에만 쓰기를 시작한다.
- AC-7: 승인된 계약 범위 밖 변경·별도 권한 경계·새 사용자 결정이 발생하면 `opal-self-pm`이 작업을 멈추고 질문 루프로 복귀한다.
- AC-8: `opal-self-pm` 완료 직전에 기획·설계·프로젝트 문서·CONVENTIONS·SECURITY·brain·memory·code-scan 8개 영역이 각각 `update` 또는 `no-op + 근거`로 판정되어 사용자에게 제시되며, 무근거 생략이 남아 있지 않다.
- AC-9: `opal-self-pm`이 사용자 최종 확인 발화 이전에 완료를 선언하지 않는다.
- AC-10: `opal-self-pm`의 경량 실행 기록이 `objective`·`status`·`decisions`·`open_questions`·`approved_scope`·`changed_files`·`validation`·`knowledge_impact` 8필드를 갖는 machine-readable 파일로 남고, `state.json`·`test-scenario.json`·`backlog.json` 3-SSOT와 경로·소유권이 충돌하지 않는다.
- AC-11: `opal-self-pm`과 `--pm` Pilot이 `op-gc-security`·`op-gc-convention`·`op-gc-report`를 같은 입력·결과 계약으로 호출한다.
- AC-12: owner 문서 전체에서 `L2 경량 트랙`·`direct-workflow`·`direct-adaptive` 잔존이 0건이며(`grep` 실측), 같은 자리에 actor 축과 `opal-self-pm` 설명이 들어가 있다.
- AC-13: `README.md`·`docs/PROJECT.md`·`docs/ARCHITECTURE.md`·스킬 커맨드 레지스트리·`scripts/install-mac.sh`에 `--pm` 옵션과 `oppm`/`opal-self-pm`이 등재되고, install 실행 후 배포본(`~/.opal/`)에서 동일하게 노출된다.
- AC-14: `--pm`을 지원하지 않는 Pilot(`opwt`·`opsdd`·`oppd`·`oppl`)에 `--pm`을 전달하면 조용히 무시하지 않고 미지원임을 사용자에게 알린다.
