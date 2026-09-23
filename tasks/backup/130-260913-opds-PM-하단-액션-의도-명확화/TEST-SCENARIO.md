---
template: sdlc-v2
---
# TEST-SCENARIO: PM 하단 액션 의도 명확화

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: `/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_130`의 `feat/OP-TASK-130` 브랜치, POSIX shell, `rg`, `awk`, `git`, `shasum`, OPAL `state-tool` 사용 가능
- 공통 데이터: 변경 전 배포본 SHA-256은 `/Users/iskang/.opal/references/opal-pm.md`=`508ad0f3580e3e186d421fedb3a05cd85c51a5c5e48e1d9b40a8b048f609c477`, `/Users/iskang/.opal/references/opal-harness-semi-agentic.md`=`1ae8682d16cad0c5ed10bbba6773e9a706181500bbe64526b363d96eb520ba5b`
- 대역 사용과 한계: 사용하지 않음. 문서 계약 변경이므로 소스 본문·diff·독립 보고 판별을 실제 파일에서 검증한다.
- 실행 조건: 구현 완료 후 `opal-test-agent`가 구현 워커와 분리된 주체로 자동 정적 검사와 독립 리뷰를 수행한다. 문서·설정 변경이므로 RED-first 대상은 없다.

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1, AC-2, C-2, H-1 | 구현된 `opal/core/references/opal-pm.md` §8만 검증 입력으로 사용 | §8에서 하단 액션 두 형태와 사용자 결정 요청 구성 요소를 추출하고 줄 수를 센다 | 두 형태가 각각 `PM/입력 불필요`와 `사용자/입력 필요`로 유일하게 대응하고 상호 배타적이다. 결정 요청은 결정 한 가지, 선택지·답변 범위, PM 권고, 이유·주요 영향, 답변 후 다음 작업, 물음표로 끝나는 명시 질문 1개를 모두 요구하며 §8은 35줄 이하이다 | 정적 문서 검사(`awk`, `rg`)·worktree | 구현 후 |
| S-2 | AC-3, C-5, H-3 | 구현된 `opal/core/references/opal-harness-semi-agentic.md` §10을 입력으로 사용 | PLAN·EXECUTE·CLOSE 예시의 하단 블록을 각각 검사하고 `▶️ 다음 진행 사항입니다.` 잔존을 검색한다 | 세 예시 모두 `▶️ 사용자 결정 필요`로 사용자 입력 사실과 서로 다른 결정 대상을 직접 표시한다. §10 예시 구간에서 낡은 표지는 0건이고, 각 질문은 물음표로 끝난다 | 정적 문서 검사(`awk`, `rg`)·worktree | 구현 후 |
| S-3 | AC-4, C-1, H-2 | 두 변경 문서와 PLAN D-1이 존재한다 | 공통 계약의 정의 위치와 게이트 문서의 참조·예시를 대조하고, 게이트 §10에 별도 채널 의미 표나 상충하는 사용자 입력 정의가 있는지 독립 리뷰한다 | 하단 액션 의미와 행동 주체의 규범은 `opal-pm.md` §8 한 곳에만 있고 게이트 §10은 이를 명시적으로 참조한다. 게이트 문서에는 소비 예시 외 중복 정의가 없다 | 독립 문서 리뷰·worktree | 구현 후 |
| S-4 | AC-5, H-5 | TEST 워커는 구현 워커의 self-check 결과를 입력으로 사용하지 않고 변경된 두 문서만 읽는다 | 일반 보고 2건(PM이 계속할 사례 1건, 사용자 결정 사례 1건)과 PLAN·EXECUTE·CLOSE 게이트 예시 3건을 재현·판별하여 각 보고의 `actor`와 `input_required`를 기록한다 | 5건 모두 행동 주체가 정확히 하나로 판별되고 입력 필요 여부가 단일하다. 어느 보고도 두 하단 채널을 함께 쓰지 않으며, 사용자 결정 4건은 판단 정보와 명시 질문 없이 끝나지 않는다 | `opal-test-agent` 독립 보고 재현·manual semantic review·worktree | 구현 후 |
| S-5 | AC-6, C-3, H-4 | 구현 diff가 존재한다 | `git diff -- opal/core/AGENT.md`를 실행하고 보고 형식 제목과 두 하단 채널 문안을 각각 `rg`로 검색한다 | `opal/core/AGENT.md` diff가 없고 새 보고 형식·하단 채널 문안 검색 결과가 0건이다 | 정적 회귀 검사·worktree | 구현 후 |
| S-6 | AC-6, C-5 | 구현 전 HEAD의 게이트 §10 단계별 5요소 표, §3 모드 경계, §6 승인·상태 전이 계약을 기준선으로 사용한다 | `git diff -- opal/core/references/opal-harness-semi-agentic.md`를 검토하고 변경 범위를 §10 참조 문장과 세 하단 예시 블록에 대조한다 | 단계별 5요소 표와 §3·§6의 승인·상태 전이 규칙에는 의미 변경이 없고, 허용된 참조 문장·하단 예시 외 계약 변경이 없다 | diff 기반 독립 회귀 리뷰·worktree | 구현 후 |
| S-7 | C-4, H-1 | 구현된 `opal-pm.md` §8이 존재한다 | `## 8. 보고 형식`부터 다음 `---` 직전까지 `awk`로 줄 수를 계산하고 문장 추가 대신 기존 조·템플릿 하단이 교체되었는지 diff를 검토한다 | §8이 35줄 이하이며 기존 4개 조의 핵심 판단·비중복·확정/추정 분리 계약을 보존하고 하단 액션 계약은 기존 조·템플릿 교체로 반영된다 | 정적 검사와 diff 리뷰·worktree | 구현 후 |
| S-8 | C-6 | Setup의 두 배포본 SHA-256을 구현 전 기준선으로 사용한다 | 구현 후 같은 `/Users/iskang/.opal/references/` 두 파일에 `shasum -a 256`을 실행하고 기준선과 비교한다 | 두 SHA-256이 기준선과 정확히 같아 프로젝트 소스 밖 배포본을 수정하지 않았음이 확인된다 | 실제 배포 경계 검사·local filesystem | 구현 후 |
