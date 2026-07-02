---
type: concept
title: 신규 스킬은 파일 배포만으로 부족하다 — 레지스트리 인덱스 등록이 발견의 전제조건
tags:
- skill-registry
- deployment-gap
- discovery
- lesson
sources:
- task:052
related:
- opal-workspace-sync
- skill-registry-validate-extension
created: '2026-07-02'
updated: '2026-07-02'
status: active
---
## 개념 요약

install 스크립트가 스킬 파일을 배포 위치로 복사하는 것과, 스킬 검색기(skill-registry)가 그 스킬을 실제로 "찾아낼 수 있는 것"은 서로 다른 두 단계이며, 하나가 되어도 다른 하나가 저절로 되지는 않는다.

## 배경·문제 (WHY)

태스크 052에서 [[opal-workspace-sync]] 스킬을 신설하고 install을 재실행했지만, 사용자가 `//opws`를 호출했을 때 스킬이 발견되지 않는 사건이 발생했다 (근거: task:052 AGENTIC-LOG #11). 원인은 install의 스킬 디렉토리 자동 순회 로직이 파일을 정상적으로 복사했음에도, skill-registry가 실제로 참조하는 것은 디스크 스캔이 아니라 `opal-skills-registry.json`이라는 별도 인덱스 파일이었기 때문이다. 이 인덱스에 새 스킬의 항목(alias·triggers·paths·domain)을 추가하는 절차가 PLAN·ANALYSIS 단계에서 누락되어 있었다.

## 결정 내용 (HOW)

신규 스킬을 만들 때는 아래 두 단계를 모두 완료해야 "생성 완료"로 간주한다.

1. **파일 배포**: 스킬 디렉토리를 소스 위치에 작성 → install이 자동 순회로 배포 위치에 복사한다.
2. **인덱스 등록**: `opal-skills-registry.json`에 해당 스킬 그룹 아래 alias·triggers·paths·domain 항목을 명시적으로 추가한다. 이 파일은 자동 순회 대상이 아니라 수동으로 채워야 하는 SSOT다.

배포 후에는 파일 존재 확인만으로 끝내지 말고, skill-registry의 매칭 조회로 런타임 발견 여부(found:true)까지 검증해야 한다. 파일 존재 검증만으로는 이 배포 갭을 잡아내지 못한다.

## 영향·관계

- 향후 모든 신규 스킬 생성 작업(PLAN·EXECUTE 단계)에 인덱스 등록 Step을 명시적으로 포함해야 한다.
- 테스트 시나리오에도 "레지스트리 discoverability" 항목(런타임 match 검증)을 표준으로 추가해야 한다 — 파일 존재 검사만으로는 불충분함이 이번 사건으로 실증되었다.
- 기존 [[skill-registry-validate-extension]](task:029)는 dangling(등록됐지만 파일 없음)·unregistered(파일 있지만 미등록) 드리프트를 validate로 감지하는 도구 강화였다. 이번 사건은 그 validate가 상시 실행되지 않는 워크플로우 지점(신규 스킬 생성 직후)에서 드리프트가 발생한 사례로, 도구 개선과는 별개로 "생성 프로세스 자체에 등록 Step을 넣어야 한다"는 프로세스 교훈이다.

## 근거 출처

task:052 (AGENTIC-LOG #11·#12, DONE.md §주요 의사결정·특이사항 4), [[opal-workspace-sync]]
