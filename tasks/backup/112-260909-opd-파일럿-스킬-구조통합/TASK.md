---
template: sdlc-v2
---
# TASK: 파일럿 전용 스킬 내부화와 Dev Pilot 통합

## Problem

SDD 파일럿만 사용하는 단계 스킬 네 개가 독립 최상위 스킬처럼 배포·등록되어 있어 실제 소유 경계와 디렉토리 구조가 어긋난다. 또한 Full 개발과 Short 개발이 별도 Pilot 폴더에 구현되어 공통 흐름 변경 시 두 구현의 계약과 문서가 함께 드리프트할 위험이 있다. 현재 프로젝트 문서도 네 SDD 단계를 독립 단계 스킬로 열거하고 Short 개발 Pilot을 별도 오케스트레이터로 설명한다 (`docs/PROJECT.md:70`, `docs/PROJECT.md:113`, `docs/PROJECT.md:116`, `docs/CONVENTIONS.md:39`).

## Proposed outcome

SDD 전용 단계 기능은 `opal-pilot-sdd` 내부에서만 소유·배포되고, 개발 Pilot은 하나의 정본에서 Full과 Short 프로필을 실행한다. 사용자는 기존 `//opd`와 `//opds` 호출을 계속 사용할 수 있으며, 기존 상태 식별자와 두 트랙의 단계 의미도 유지된다.

## Affected users and systems

- 사용자: `//opd`, `//opds`, `//opsdd`를 호출하는 OPAL 사용자와 관련 개발·검증 에이전트.
- 시스템: 세 Pilot의 스킬·참조·파이프라인, SDD 액션 에이전트, 스킬 레지스트리·설치 경로, state-tool 계약, 프로젝트 설명 문서와 관련 테스트.
- 포함: 네 SDD 단계 스킬의 소유 경계 정리, 오래된 `op-sdd-verify` 계약의 유효 규칙 보존 여부 판단, `opal-pilot-dev-short` 구현의 `opal-pilot-dev` 통합, 호출·상태·라우팅 호환, 활성 문서·검사 정합.
- 제외: 과거 task·brain·대시보드 fixture의 일괄 변환, Full/Short 단계 의미의 재설계, 관련 없는 Pilot과 도구의 구조 개편.

## Constraints

- C-1: `//opd`와 `//opds` 호출 호환성을 유지하고 각 호출이 Full과 Short 프로필을 명확히 선택해야 한다.
- C-2: 기존 `state.json`의 `skill=opd|opds` 식별자와 Full 16행·Short 11행 파이프라인 의미를 보존해야 한다.
- C-3: `opd`의 TASK 직후 강등과 `opds`의 PLAN 이후 승격은 판정 시점 분리와 왕복 재귀 차단을 유지해야 한다 (`opal/core/references/harness/track-routing.md:45`, `opal/core/references/harness/track-routing.md:58`).
- C-4: `op-sdd-verify`의 현재 호출 여부와 S-1~S-6 소비 관계를 근거로 처리하고, 유효 검증 규칙이나 활성 포인터를 유실하지 않아야 한다 (`opal/skills/opal-pilot-sdd/references/verify-guide.md:185`).
- C-5: 변경은 이 태스크 전용 worktree의 프로젝트 소스에 적용하고 설치본 `~/.opal/`은 직접 편집하지 않는다.
- C-6: 상위 문서 표준에 따라 이번 태스크에서 수정하는 문서·스킬·에이전트·참조 문서의 내장 `변경이력` 절을 제거하고, 프로젝트 컨벤션과 PM 프로필의 낡은 변경이력 작성 의무를 상위 SSOT 포인터로 교체해야 한다. 과거 태스크·brain 기록은 보존한다 (`opal/core/references/opal-doc-standard.md` §4~§5).
- C-7: 과거 완료 태스크와 brain 기록은 역사 자료로 보존하며 활성 호출 계약과 혼동하지 않는다.

## Acceptance criteria

- AC-1: `opal/skills/` 최상위에서 네 `op-sdd-*` 디렉토리가 사라지고, `opal-pilot-sdd` 및 SDD 액션 에이전트의 활성 호출이 Pilot 내부 경로만 사용한다.
- AC-2: `op-sdd-verify`의 유효 검증 규칙은 현재 REVIEW 흐름에서 직접 소비되며, 제거되거나 이동된 옛 경로를 가리키는 활성 참조가 0건이다.
- AC-3: `opal-pilot-dev-short`의 중복 구현 디렉토리가 제거되고, `//opd`와 `//opds`가 하나의 canonical `opal-pilot-dev` 구현에서 각각 Full과 Short 프로필로 해석된다.
- AC-4: Full 프로필은 기존 16행, Short 프로필은 기존 11행 상태 계약을 생성하며 기존 `opd|opds` 식별자 조회·재개가 통과한다.
- AC-5: Full→Short 강등과 Short→Full 승격의 기존 임계·시점·재귀 차단 계약이 자동 검사 또는 대표 시나리오로 검증된다.
- AC-6: 스킬 레지스트리 검증, 설치/배포 관련 검사, state-tool과 Pilot 관련 회귀 테스트가 통과한다.
- AC-7: README·PROJECT·ARCHITECTURE·CONVENTIONS와 활성 에이전트/하네스 문서가 새 소유 구조를 설명하고, 최상위 스킬 수·경로·alias가 실제 파일 구조와 일치한다.
- AC-8: 설치 절차 후 전역 설치본에서 두 개발 명령과 SDD 내부 단계 경로가 해석되며 제거된 최상위 SDD·Short Pilot 구현이 재생성되지 않는다.
