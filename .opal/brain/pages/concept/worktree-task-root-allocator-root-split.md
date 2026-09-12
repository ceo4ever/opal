---
type: concept
title: 워크트리 태스크 루트 분리 — 해석용 task root와 발급용 allocator root
tags:
- worktree
- architecture
- workspace
- ownership
- root-resolution
sources:
- task:118
- task:119
related:
- worktree-workspace-isolation-axis
- worktree-tasks-fixture-structural-limit
- worktree-slot-existence-to-occupancy-judgment
- worktree-tool
- three-layer-memory-architecture
- state-aware-path-resolution-unblocks-merge
- switch-first-plumbing-later-verification
created: '2026-09-12'
updated: '2026-09-12'
status: draft
---
## 개요

워크트리 태스크의 작업 루트를 용도별로 둘로 분리했다. 태스크 문서·`.opal` 설정·코드 스캔·인용 판정을 해석하는 루트(`task_root`)와, 번호 채번과 완료 이력 귀속을 쓰는 허브 루트(`allocator_root`)다. 두 루트는 서로를 대체하지 않으며, 허브 쓰기용 루트는 현재 위치·조상 경로·디렉터리 이름 문자열로 추론하지 않고 워크트리 생성 도구가 발급한 메타데이터로만 전달된다(계약 원문: `opal/core/references/harness/worktree.md` §task root와 allocator root 계약).

## 결정 배경 (WHY)

- 이전 계약은 "태스크 문서·메모리·브레인은 허브에 고정하고 코드만 분기한다"였고, 네 런타임이 각자 "경로에 워크트리 디렉터리 세그먼트가 보이면 무조건 허브로 되돌린다"는 보정 함수를 중복 구현해 그 고정을 흉내 냈다(`code-scan.js`의 `hubRootFromPath`, `event_loader.py`의 `_hub_root`, `brain_tool.py`의 `hub_root`/`_hub_cwd`, `dashboard/backend/paths.py`의 `hub_root`). (근거: task:118 ANALYSIS Q1 5개 행)
- 실측 결과 이 "4런타임 동일 위험"이라는 전제 자체가 성립하지 않았다. 코드 스캔 도구의 루트 탐색은 워크트리에 설정 디렉터리가 실체화되기만 하면 이미 워크트리 자신에 착지했고, 세그먼트 보정값은 진단용 알림 한 곳에서만 소비됐다(`opal/tools/code-scan/code-scan.js:338-346`, `:3687-3694`). 콘솔 쪽 보정 함수는 프로덕션 호출자가 0건인 죽은 코드였다(`dashboard/backend/routers/doctor.py:85-90`). (근거: task:118 ANALYSIS Q1 code-scan·Console 행)
- 반대로 상태 도구의 루트 탐색은 "가장 가까운 메모리 파일 보유 조상"을 찾기 때문에, 설정 디렉터리를 워크트리에 실체화하는 순간 지금까지 우연히 허브로 가던 동작이 **워크트리 사본**으로 뒤바뀌었다(`opal/tools/state-tool/state_tool.py:704-711` 실측). 그 상태로 완료 처리가 이력을 쓰면 워크트리 회수 시 이력이 소실된다. (근거: task:118 ANALYSIS Q1 state-tool 행)
- 즉 실제 분기축은 "허브냐 워크트리냐"가 아니라 **"해석이냐 발급값이냐"**였다. 해석용 탐색은 하나로 두고, 쓰기용 루트에서는 탐색 자체를 없애 명시 인자로 받는 편이 이 축과 일치한다. (근거: task:118 PLAN D-4)

## 결정 내용

- 해석용 탐색 함수는 시그니처째 개명해 목적을 이름에 못 박고, 동작은 바꾸지 않았다. 쓰기용 호출 1곳은 탐색 호출을 제거하고 허브 절대 경로를 인자로 받도록 바꿨다(`opal/tools/state-tool/state_tool.py:730`, PLAN D-4).
- 허브 쓰기용 루트는 상대 경로나 미지정이면 추론하지 않고 즉시 거부한다. 브레인 도구의 회고적 학습 쓰기 경로도 같은 규율을 따라, 명시 인자 없는 쓰기를 전용 오류로 막는다(`opal/tools/brain-tool/brain_tool.py:304-318`, PLAN D-4·W-7).
- 완료 처리는 이력을 즉시 쓰지 않고 "머지 대기" 상태만 확정하며, 허브 메모리 이력 append는 허브 절대 경로를 명시로 받는 별도 귀속 명령이 전담한다(PLAN D-4b, AC-4).
- 워크트리 생성 도구가 정규 경로 6종 필드를 발급하고, 소비자는 이 발급값을 전달받아 쓴다. 등록된 워크트리 태스크와 같은 이름의 태스크 폴더가 허브에도 있으면 자동 선택하지 않고 모호성 오류로 차단한다(계약: `harness/worktree.md` §canonical path 발급 계약).
- 소유권 버전 필드가 없는 기존 태스크는 legacy로 판정해 실행 중 위치를 자동 이동하지 않는다. 이 태스크 진행 시점의 활성 슬롯 3건이 전부 legacy로 판정돼, 실제 허브에서 콘솔의 허용 루트 목록이 빈 배열을 반환하며 현행 동작이 유지됨을 실측했다(PLAN D-9, AGENTIC-LOG 엔트리 62).

## 영향 범위

- 이 결정은 [[worktree-workspace-isolation-axis]]의 "문서는 허브 고정, 코드만 분기"라는 위치 기준 격리축을 **대체한다**. 위치는 더 이상 디렉터리 경로 문자열로 정해지지 않고 루트 소유권으로 정해진다.
- [[worktree-tasks-fixture-structural-limit]]이 기록한 구조적 한계(태스크 문서 디렉터리가 워크트리에 없어 픽스처 의존 테스트가 통과 불가)는 태스크 문서·설정 디렉터리를 cone에 실체화할 수 있게 되면서 해소 경로를 얻었다. 같은 조건의 픽스처에서 관련 16건이 전부 통과했다(근거: task:118 ANALYSIS Q1 AC-2 재기준선 행).
- 재진입 가드는 [[worktree-slot-existence-to-occupancy-judgment]]의 "존재가 아니라 점유로 판정" 전환과 동형으로 설계됐다 — 워크트리 전체의 미커밋 여부가 아니라, 미커밋 대상 경로 집합이 완료 문서가 선언한 학습 후보 집합의 부분집합인지로 판정한다(PLAN D-3b).
- 네 런타임의 보정 함수와 세 런타임이 공유하던 골든표가 제거되고 각 런타임의 착지 계약 테스트로 교체됐다.

- 이 결정이 만든 장치는 태스크 118 시점에는 실행되지 않았다. 캡슐 실체화 범위를 선언하는 설정 키가 비어 있어 해석용 루트가 워크트리가 아니라 허브로 탈출했고, 값이 들어간 태스크 119에서야 계약이 실제로 성립했다 — 경위는 [[switch-first-plumbing-later-verification]].
- 태스크 119는 이 결정의 단일 복사본 차단 위에 귀속 진행 상태를 판정에 더해, 병합 이후 정상 상황까지 막던 연쇄를 풀었다. 차단은 진행 중 상태에만 적용되도록 좁혀졌을 뿐 사라지지 않았다 — [[state-aware-path-resolution-unblocks-merge]].

## 관련 페이지

- [[worktree-workspace-isolation-axis]]
- [[worktree-tasks-fixture-structural-limit]]
- [[worktree-slot-existence-to-occupancy-judgment]]
- [[worktree-tool]]
- [[three-layer-memory-architecture]]
- [[state-aware-path-resolution-unblocks-merge]]
- [[switch-first-plumbing-later-verification]]
