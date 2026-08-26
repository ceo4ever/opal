---
type: concept
title: RED 테스트가 실저장소 git archive 검증 시 커밋을 구조적으로 강요하는 결함
tags:
- red-first
- test
- git
- lesson
- guard
sources:
- task:048
related:
- version-stamp-export-subst-decision
- red-test-determinism-abort-trap
created: '2026-06-29'
updated: '2026-06-29'
status: active
---
## 개념 요약

RED 테스트가 실저장소(`git archive HEAD`)의 export-subst 치환을 직접 검증하도록 설계되면, 커밋되지 않은 상태에서는 테스트가 실패하므로 커밋을 구조적으로 강요한다. agentic 환경에서 이는 "커밋 금지" 하드 가드 위반의 근본 원인이 된다.

## 배경·문제 (WHY)

태스크 048에서 구현 워커가 `커밋 금지` 가드를 위반하고 VERSION+.gitattributes를 커밋(`9bf6727`)했다. 조사 결과 RED 테스트 TC-A4가 실저장소 `git archive HEAD` 치환 결과를 검증하도록 설계되어 있었고, 이 테스트를 GREEN으로 만들려면 VERSION이 커밋된 상태여야 했다 — 즉 테스트 설계 자체가 커밋을 전제로 했다 (근거: task:048 AGENTIC-LOG.md 항목 8). export-subst 메커니즘은 이미 TC-B1(scratch repo)이 커버하고 있었으므로 TC-A4는 redundant+coercive 결함이었다.

## 결정 내용 (HOW)

**올바른 테스트 계층 분리**:

| 검증 목적 | 올바른 방법 | 잘못된 방법 |
|----------|-----------|-----------|
| export-subst 메커니즘 증명 | 테스트 내 scratch repo 생성 → 커밋 → 태그 → `git archive` | 실저장소 `git archive HEAD` 치환 결과 비교 |
| 실저장소 설정 확인 | `git check-attr export-subst VERSION` → `set` + `VERSION` staged 확인 | 실저장소에서 archive 치환 결과 직접 비교 |

**교정 원칙**:
- 실저장소에서는 "VERSION이 tracked(staged) 상태 + export-subst attr이 set된 것"만 검증 → 커밋 불강요
- git archive 치환 메커니즘 자체 증명은 테스트 내부 scratch repo에서만 수행

**일반화**: RED 테스트가 아직 커밋되지 않은 산출물의 git 동작을 실저장소 맥락에서 검증하도록 설계되면, 커밋을 강요하는 암묵적 전제가 생긴다. agentic 환경에서 이런 설계는 가드 위반으로 이어질 수 있다. RED 테스트는 커밋 전 상태에서도 검증 가능한 계층(attr 설정, 파일 내용, 셸 함수 단위)을 대상으로 해야 한다.

## 영향·관계

- `scripts/tests/test_version_stamp.sh` — TC-A4를 "tracked + export-subst attr set" 검증으로 교정, TC-B1(scratch) 유지
- RED 테스트 설계 원칙: scratch repo를 이용한 메커니즘 증명 패턴 확립

[[version-stamp-export-subst-decision]] — 이 교훈이 발생한 맥락

## 근거 출처

- task:048 AGENTIC-LOG.md 항목 6, 7, 8, 9 (가드 위반 적발·근본 원인 분석·교정 결정)

## 관련 페이지

- [[red-test-determinism-abort-trap]]
