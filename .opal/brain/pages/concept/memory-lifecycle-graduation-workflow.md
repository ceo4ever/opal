---
type: concept
title: 메모리 라이프사이클·졸업(promote) 워크플로우
tags:
  - memory
  - lifecycle
  - architecture
  - promote
sources:
  - task:045
related:
  - memory-tool
  - three-layer-memory-architecture
created: "2026-06-26"
updated: "2026-06-26"
status: active
---

## 개요

OPAL 메모리는 영구 지식 저장소가 아니라 **임시 인박스**다. 성숙한 지식은 영구 거처(docs=규범 / brain=설명)로 **졸업(promote)**하고, 진부화·완료된 지식은 상태 전이 후 정리한다. 갯수 상한 대신 졸업·자가검토·길이캡이 비대화를 방지한다. (근거: task:045 DONE 핵심 설계 결정 #1, #2)

## 결정 배경 (WHY)

기존 체계(task:016 — FIFO 10)는 갯수 상한과 수동 정리에 의존했다. 실데이터(이 프로젝트 `.opal/MEMORY.md`)는 단일 셀이 수천 자에 달하고, 상태값이 자유 텍스트(`대기/폐기 기록/예정/완료/~~완료~~/유지`)로 혼재했다 — 기계 판독 불가, 토큰 낭비. (근거: task:045 PLAN §2.1.2)

캡틴은 갯수 게이트를 제외하고 대신 세 기제의 조합으로 비대화를 억제하기로 결정했다(2026-06-26): 졸업(`promote`)으로 영구 거처 이전 후 삭제, 자가검토(`review` ambient 강제)로 정리 후보 표면화, 길이캡(요약 ≤80자)으로 인덱스 비대화 방지. (근거: task:045 DONE 핵심 설계 결정 #1)

히스토리는 소모성 로그이므로 FIFO=5 자동 정리를 허용하되, 메모리(지식)는 blind 삭제가 금지된다 — 지식 무손실이 원칙이다. (근거: task:045 DONE 핵심 설계 결정 #2)

## 결정 내용

### 라이프사이클 4상태

| 상태 | 의미 | 도구 집행 |
|------|------|---------|
| `active` | 살아있는 지식. 인덱스에 노출·로드 대상 | `append` 시 자동 부여 |
| `promoted` | 영구 거처로 졸업 완료 | `promote --to docs\|brain --ref <위치>` → 행+파일 삭제 + provenance 기록 |
| `superseded` | 더 새로운 결정이 대체 | `update --status superseded` → 행 보존(추적용), 로드 제외 |
| `dead` | 완료·진부화·철회 | `update --status dead` → 행 보존(추적용), 로드 제외 |

### 졸업(promote) 라우팅 표

| 메모리 성격 | 졸업지 | 유형 힌트 |
|------------|--------|---------|
| 행동 규칙·금지·확정 기준·선호 | `docs/AGENT.md` | feedback / preferences |
| 코드·문서 컨벤션 | `docs/CONVENTIONS.md` | — |
| 프로젝트 정의·범위 | `docs/PROJECT.md` | — |
| 설계 WHY·도메인 지식·비자명 해법 | `brain` (`//opbr ingest` 재사용) | architecture / issues |
| 완료·진부화·철회 | 삭제(`dead`/`superseded` → 정리) | task |

**docs=규범(행동을 지배)**, **brain=설명(왜·어떻게)**이 핵심 구분이다. 최종 졸업지·성숙 여부는 PM이 판단하고, 도구는 이전 확인·삭제·provenance만 집행한다(역할 경계). (근거: task:045 PLAN §3.5.2)

### 자가검토 ambient 강제

모든 변경 명령(`init/append/update/promote/prune/migrate`) 응답 JSON에 `review` 블록이 자동 첨부된다. 별도 CLOSE 훅이나 파일럿 변경 없이 "호출할 때마다 기존 메모리·히스토리를 검토"가 ambient하게 강제된다. 단독 `review` 명령으로도 health 점검이 가능하다. (근거: task:045 PLAN §3.10.2 / DONE 핵심 설계 결정 #4)

### 실증 (S-26)

이 프로젝트 `.opal/MEMORY.md` 실데이터에 라이브 적용: migrate → delete(promoted/dead/superseded/dangling) → 제목·요약 보정. **17,248 → 7,535 bytes (56% 감소)**, 인덱스 6→2행, review violations 0. (근거: task:045 DONE 라이브 적용)

## 영향 범위

- `opal/core/references/harness/memory-learning.md` — 라이프사이클 4상태·이관 워크플로우·자가검토 트리거·마커 규약을 SSOT로 기술 (v1.1)
- `opal/tools/memory-tool/` — 위 워크플로우를 결정론적으로 집행하는 CLI
- `opal/skills/opal-project-init/SKILL.md` — 신규 프로젝트 MEMORY.md 템플릿이 신포맷·마커 포함

## 관련 페이지

- [[memory-tool]] — 이 워크플로우를 집행하는 도구
- [[three-layer-memory-architecture]] — 메모리가 단기 인박스임을 명문화한 3계층 아키텍처
