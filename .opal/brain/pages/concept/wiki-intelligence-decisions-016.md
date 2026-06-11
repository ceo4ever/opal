---
type: concept
title: opal-wiki-pilot 지능화 결정 — M-4/M-5 (016)
tags:
- architecture
- naming
- git
- brain
- policy
sources:
- task:016
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: active
---
## 개념 요약

016 태스크에서 확정된 이름 정책(M-4: opal-brain 구현 식별자 유지)과 brain git 추적 정책(M-5: brain만 예외 추적). opal-wiki-pilot은 비전 용어로만 병기한다.

## 배경·문제 (WHY)

015 자산(스킬명·alias `opbr`·brain-tool·레지스트리·30+ 페이지 링크·6 PM 문서)이 모두 `brain` 기준이어서 "opal-wiki"로 리네임 시 016 범위 폭증·회귀 위험이 컸다. brain git 추적 미결 상태에서 멀티PC 협업이 불가능했다(설계 §R2 전제 조건).

## 결정 내용 (HOW)

**M-4 (이름)**
- 구현 식별자: `opal-brain` / `opbr` / `brain-tool` / `.opal/brain/` 유지.
- "opal-wiki-pilot"은 비전·컨셉 명칭으로 `docs/proposals/opal-brain-design.md §13`에만 병기.

**M-5 (git 추적)**
- `.gitignore` 패턴: `.opal/` 무시 유지 + `!.opal/brain/` + `!.opal/brain/**` 예외.
- brain 페이지는 사람이 읽는 .md SSOT(User sovereignty) — 팀·멀티PC 공유·git 리뷰 가능.
- `code-scan.json`은 파생 캐시이므로 계속 무시.
- 후속: brain-tool 원자적 index 재생성 + git merge 전략은 설계 §R2 후속.

## 영향·관계

- `.gitignore` — 016 M-5 brain 예외 추가
- `docs/proposals/opal-brain-design.md` — §13 이름 정책·§R2 git 추적 명문화

## 근거 출처

`task:016` PLAN §0 M-4/M-5 — `.gitignore:2`(brain 예외 패턴), `docs/proposals/opal-brain-design.md §13`(이름 매핑).

## 관련

- [[page-type-dynamic-schema]] — M-1·W1 결정의 상세 페이지
- [[three-layer-memory-architecture]] — W3 결정의 상세 페이지
- [[brain-search-on-demand]] — W5 결정의 상세 페이지
- [[opal-brain-design-proposal]] — 016 확정이 반영된 설계 SSOT
