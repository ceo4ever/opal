---
type: concept
title: Environment Probe 준비 baseline 격리
tags:
- environment-probe
- git
- isolation
- bootstrap
- oppb
sources:
- task:146
related:
- fixture-vs-real-blind-spot-lesson
- fix-validity-requires-failure-mode-reproduction
created: '2026-09-19'
updated: '2026-09-19'
status: draft
---
## 개요

환경 관측은 원본 작업공간을 건드리지 않으면서도 실제 실행 입력을 빠짐없이 재현해야 한다. 태스크 146은 accepted HEAD의 전체 tracked tree와 순차 bootstrap 결과를 준비 baseline으로 만들고, 각 관측 명령을 그 baseline의 독립 복사본에서 실행하는 격리 모델을 확정했다.

## 결정 배경 (WHY)

아카이브 기반 snapshot은 배포 산출물을 만드는 데는 적합하지만 `.gitattributes export-ignore`를 적용하므로, 저장소 안에서 추적되는 테스트 fixture와 작업 문서가 관측 입력에서 사라질 수 있다. 환경 관측의 목적은 배포 archive 재현이 아니라 accepted HEAD 실행 조건 재현이므로 두 표면을 같은 것으로 취급하면 안 된다. (근거: task:146 PLAN D-1, DONE 결과)

또한 명령마다 pristine snapshot을 새로 만들면 설치·생성된 의존성을 후속 관측 명령이 소비할 수 없다. 반대로 모든 명령을 한 디렉터리에서 연속 실행하면 앞선 build의 출력이 뒤 명령에 새어 command별 귀속과 병렬 안전성 판단이 흐려진다. 준비 단계와 관측 sibling은 서로 다른 공유 규칙이 필요하다. (근거: task:146 PLAN D-3·D-4)

## 결정 내용

- snapshot은 임시 index로 accepted HEAD의 전체 tracked tree를 물질화한다. 원본 branch, HEAD, 공유 index, tracked/untracked/ignored 파일은 변경하지 않는다 (`opal/tools/oppb-runtime-tool/probe.py:310`).
- bootstrap은 선언 순서대로 같은 snapshot에서 실행하고 각 delta를 해당 command id로 한 번 관측한 뒤 현재 상태를 준비 baseline으로 승격한다 (`opal/tools/oppb-runtime-tool/probe.py:483`).
- 비-bootstrap 명령은 준비 baseline의 committed HEAD를 각자 독립 repo에 다시 물질화해 실행한다. bootstrap 산출물은 보이지만 sibling 산출물은 보이지 않는다 (`opal/tools/oppb-runtime-tool/probe.py:483`).
- 명령 timeout은 실행 조건의 일부이므로 정규화된 값이 command identity와 freshness hash에 포함된다. 생략과 explicit 기본값은 동일하게 취급한다 (`opal/tools/oppb-runtime-tool/probe.py:618`, `opal/tools/oppb-runtime-tool/probe.py:687`).
- 수용 판정 명령은 관측 명령에 섞지 않는다. 환경 probe는 실행 조건을 관측하고, 최종 판정은 별도 Supervisor 경로가 소유한다 (`opal/skills/op-oppb-project-slice/SKILL.md:199`).

## 검증 경계

작은 합성 fixture만으로는 준비 baseline 복사 시 실제 Git object layout에서 발생하는 결함을 놓칠 수 있다. 태스크 146에서는 설치본 절대경로 CLI와 실제 태스크 외부 clone으로 동일 실패 모드를 재검증했고, 8개 관측 명령의 성공·profile seal·원본 상태 불변을 함께 확인했다. 이는 [[fixture-vs-real-blind-spot-lesson]]의 실데이터 검증 원칙을 환경 격리 경계에 적용한 사례다.

## 영향 범위

Environment Probe의 snapshot, bootstrap, command timeout 계약과 이를 소비하는 프로젝트 slice P2 환경 봉인 단계에 적용된다. 세부 실행 계약의 SSOT는 코드와 OPPB 계약 문서이며, 이 페이지는 선택 이유와 경계만 설명한다.

## 관련 페이지

- [[fixture-vs-real-blind-spot-lesson]]
- [[fix-validity-requires-failure-mode-reproduction]]
