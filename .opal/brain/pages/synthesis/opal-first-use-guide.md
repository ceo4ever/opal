---
type: synthesis
title: OPAL 첫 사용 가이드 — 설치부터 파이프라인까지
tags:
- guide
- onboarding
- first-use
sources:
- synthesis:query-2026-06-11
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 질문·동기

캡틴 질의 "opal framework를 처음 사용하려면 어떻게 해야지? 사용순서와 예시를 제안해줘"에서 파생. 온보딩·시작·초기화 3개 스킬 페이지를 합성하여 첫 사용 경로를 단일 가이드로 도출.

## 분석·비교

첫 사용은 5단계 순차 경로다. ③까지가 준비, ④부터가 실전.

| 단계 | 명령 | 내용 |
|------|------|------|
| 0. 설치 | `bash scripts/install-mac.sh` | `~/.opal/`에 스킬·도구·에이전트 글로벌 배포 |
| 1. 온보딩 | (자동) | `identity.md` 부재 시 자동 인터뷰 — 에이전트 이름·성격·호칭 설정 |
| 2. 진단 | `//start` | 5항목 환경 진단 → 다음 액션 하나 권유. 재진입 시에도 사용 |
| 3. 프로젝트 초기화 | `//opi` | 코드 분석+인터뷰로 `docs/`·`.opal/` 직접 작성. 모든 파이프라인의 전제 |
| 4. 실전 | `//opp`·`//opds`·`//opd` 등 | 범용 작업 / 버그 수정 / 기능 개발. `--agentic`으로 자율 모드 |

## 결론

진입 장벽은 "어디서 시작하나"이며, 답은 항상 `//start`다. 프로젝트 작업이 안 되는 가장 흔한 원인은 ③ `//opi` 생략(파이프라인 스킬은 `docs/PROJECT.md`·`.opal/AGENT.md`를 전제). 지식 위키는 `//opbr init` 후 `//opbr ask`로 질의.

## 인용 페이지

- [[skill-opal-onboarding]] — 1단계 정체성 설정
- [[skill-opal-start]] — 2단계 환경 진단·재진입 가이드
- [[skill-opal-project-init]] — 3단계 프로젝트 초기화 (파이프라인 전제 조건)

## 근거 출처

- task:016 (query 모드 dogfooding 중 합성)
- `opal/skills/opal-onboarding/SKILL.md` / `opal/skills/opal-start/SKILL.md` / `opal/skills/opal-project-init/SKILL.md`
