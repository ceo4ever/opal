---
type: concept
title: 측정 중 FW 지문 변경은 비교를 오염
tags:
- opst
- measurement
- framework
sources:
- task:176
related: [opst-variant-design-impl-settings, measurement-tool-more-fallible-than-artifact-lesson]
created: '2026-10-02'
updated: '2026-10-02'
status: draft
---
## 개요

설정 변형을 비교하는 측정 중에 배포된 프레임워크가 바뀌면 변형 간 차이가 설정 효과인지 프레임워크 차이인지 구분할 수 없어 비교가 오염된다.

## 결정 배경 (WHY)

- (근거: task:176 DONE.md C-4) stockctl 8개 세션은 지문 `main+19da06`, todo-crud 8개는 `v0.7.3-72-gbb257506+9c962d`로 측정 중 배포 FW가 바뀌었다. 이 세션은 측정 중 install을 하지 않았고 외부 재설치로 추정한다.
- 시나리오 묶음 안에서는 지문이 일치해 시나리오별 비교는 유효했으나, 두 시나리오를 합친 결론은 낼 수 없었다.

## 결정 내용

- 도구 규칙: 한 비교 묶음의 `framework` 지문(설치 VERSION + state-tool·파일럿 SKILL sha)이 하나가 아니면 보고서가 `비교 무효 — FW 버전 상이`를 표시하고 품질 하한 판정을 내지 않는다.
- 운영 규칙: 측정 시작부터 끝까지 재설치를 하지 않는다. 같은 머신의 다른 세션 install이 배포본을 덮을 수 있으므로 실행 중 지문 변경을 감지해 중단하는 장치는 아직 없다 (근거: task:176 DONE.md).

## 관련 페이지

- [[opst-variant-design-impl-settings]]
- [[measurement-tool-more-fallible-than-artifact-lesson]]
