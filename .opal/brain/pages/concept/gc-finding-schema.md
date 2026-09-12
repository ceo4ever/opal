---
type: concept
title: GC finding schema — 검사 결과 계약 SSOT
tags:
- gc
- security
- convention
- schema
- ssot
- architecture
sources:
- task:120
related:
- skill-opal-pilot-gc
- opal-skill-classification-system
- opal-security-model
- opal-conventions
created: '2026-09-12'
updated: '2026-09-12'
status: draft
---
## 개념 요약

GC 진단이 산출하는 발견 항목의 필드 구성, 검사 결과 봉투, 최종 판정 4종, 기준 출처 등급, 이전 실행 대비 증감 비교를 한 문서가 단독 소유한다. 세 검사·보고 스킬과 두 checker 역할은 이 문서를 참조만 하고 필드·판정표를 자기 문서에 복제하지 않는다 (`opal/core/references/harness/gc-finding-schema.md`).

## 배경·문제 (WHY)

같은 검사 규칙이 Pilot 참조 문서, 두 checker 역할 문서, Pilot 스킬 본문 세 군데에 중복 기재돼 있었다. 재사용 계약이 어디에도 명시되지 않아 한쪽만 갱신되는 표류가 반복됐고, 보안 결과와 컨벤션 결과가 서로 다른 형식이라 통합 보고가 문자열 결합 수준에 머물렀다.

해소 방식은 두 축이다. 하나는 **스킬이 절차 SSOT, 에이전트는 thin role** — 검사 절차·기준은 단계 스킬이 소유하고 에이전트 문서에는 진입 게이트·입력·행동 규칙·반환 형식만 남긴다. 다른 하나는 **schema를 스킬 바깥 harness 문서로 한 번 더 올리는 것** — 스킬 3개에 같은 schema를 두면 원래의 중복이 그대로 재발하기 때문이다. 판정 축을 harness 문서에 위임하는 선례(`opal/skills/op-scenario-gate/SKILL.md:22-23`)와 같은 구조다.

## 결정 내용 (HOW)

### 결측과 통과를 같은 판정으로 묶지 않는다

기준 문서가 없으면 검사를 통째로 생략하던 동작(`check_enabled = false`)을 폐기했다. 생략은 결과적으로 "문제 없음"과 구분되지 않아, 기준이 없는 프로젝트가 조용히 무검사 통과를 얻었다. 대신 실행 설정·인접 코드에서 관측한 규칙으로 검사를 수행하되 결과 상태를 `partial`로 두고 기준 문서 결측을 결측 목록에 남긴다.

이 전환이 기존 호출자를 막지 않는 이유는 **집행 수준(disposition)을 심각도와 분리**했기 때문이다. 기준 부재 상태의 발견 항목은 전부 advisory로 고정되고, advisory는 차단 사유 계산에 포함되지 않는다. 따라서 이전의 스킵 동작을 전제하던 호출자(프로젝트 루프의 규칙 검사 단계, PM 리뷰 게이트)의 흐름은 그대로 유지된다.

### `INCOMPLETE` 판정 신설

검사기가 실행되지 못했거나 일부만 검사한 상태를 통과 계열과 구조적으로 분리하기 위해 판정을 4종(`PASS` / `PASS_WITH_ADVISORIES` / `FAIL` / `INCOMPLETE`)으로 확장했다. 어느 검사라도 상태가 `partial`·`error`이거나 결측 목록이 비어 있지 않으면 차단 항목의 유무와 무관하게 PASS 계열 산출을 금지한다 — 차단 항목 0건이라는 사실이 "검사가 충분히 돌았다"를 함의하지 못하게 하는 규칙이다.

### 기준 출처 등급으로 승격을 막는다

프로젝트 기준 문서, 실행 설정, 승인된 공식 표준, 검토된 커뮤니티 참조를 등급(T0~T3)으로 나누고 등급별 기본 집행 수준을 고정했다. 커뮤니티 출처의 발견 항목을 심각도만 근거로 차단으로 승격하는 것을 금지한다 — 외부 출처가 프로젝트 기준을 대체하지 못한다는 제약(TASK C-2)의 집행 지점이다.

### 이전 실행 대비 증감은 태스크 폴더 규약만으로 계산

신규·잔존·해결·억제 분류의 비교 키는 발견 항목의 fingerprint이며, 비교 대상은 같은 프로젝트의 직전 GC 태스크 폴더 산출물에서 찾는다. 새 런타임 상태 파일을 만들지 않고 기존 태스크 폴더 규약만으로 이전 실행을 특정하기 위한 선택이다. 대상이 없으면 전건을 신규로 표기한다.

### 새 CLI 도구를 만들지 않았다

판정과 증감 계산을 도구로 빼지 않고 harness 문서 + 보고 스킬이 소유하게 했다. 근거는 두 가지다. 발견 항목은 워커가 문맥에서 생성하는 값이라 결정론적 파서의 입력이 아직 아니고, GC 보고서를 소비하는 기존 도구가 0건이라 도구화 수요가 실재하지 않는다. 안정된 JSON 계약 이전에 CLI를 먼저 만드는 것은 `~/.opal/PRINCIPLES.md` §2(중복 패턴 선제거) 위반이다. 도구화는 schema가 실사용으로 안정된 뒤 별도 태스크로 남겼다.

## 영향·관계

- 보안 검사·컨벤션 검사·보고 통합 세 단계 스킬과 두 checker 역할 문서가 이 문서를 참조원으로 삼는다.
- Markdown 보고서 파일명은 유지하고 같은 실행이 machine-readable JSON을 추가 산출한다 — 기존 소비자(PM 리뷰 게이트, 프로젝트 루프) 파손을 피하면서 비교·판정 입력을 확보하기 위한 절충이다.
- 미적용 범위: 외부 reference registry 연동은 외부 공급망 축이라 별도 태스크로 분리했다.

## 관련 페이지

- [[skill-opal-pilot-gc]]
- [[opal-skill-classification-system]]
- [[opal-security-model]]
- [[opal-conventions]]

## 근거 출처

태스크 120 (`task:120`), `opal/core/references/harness/gc-finding-schema.md`
