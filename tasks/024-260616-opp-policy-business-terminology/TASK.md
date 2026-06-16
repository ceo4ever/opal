# TASK 024 — 기획 산출물 비즈니스 용어 우선 원칙 내재화

> 태스크 번호: 024
> 생성일시: 2026-06-16 17:09 KST
> 스킬: //opp --agentic
> 모드: agentic
> 상태: 진행 중

---

## 1. 배경

opwt(opal-pilot-write-tech)로 소스 코드를 읽어 정책서 등 기획 산출물을 역설계할 때, 워커가 코드 변수·enum·식별자(`autoSelCancelYn`, `AUTO_SELECT_CANCELABLE` 등)를 본문에 그대로 나열하는 문제가 관찰되었다. 정책서·brain 등 기획/지식 산출물은 비즈니스 용어·자연어로 서술되어야 하며, 코드 식별자는 근거(`경로:줄번호`)로만 병기되어야 한다.

핵심 명제(캡틴 지시): **"코드는 SSOT 근거이지 본문 서술의 주어가 아니다."**

## 2. 목표

기획 산출물(정책서·PRD·TRD·IA·외부API명세 등)과 brain 페이지가 비즈니스 용어/자연어로 서술되도록, 근거/용어 SSOT(`citation-rules.md`)에 원칙을 신설하고 작성·검증·brain 적용 지점에 참조 주입한다.

## 3. 요구사항

| # | 요구사항 | 완료 기준 |
|---|---------|----------|
| R-1 | `citation-rules.md`에 "비즈니스 용어 우선 원칙(기획 산출물)" SSOT 신설 | 새 § 추가 — 코드 식별자 나열 금지 / 자연어 변환 예시 / 조건·상태군 풀어쓰기 / "조건(용어)+코드 근거" 표 분리 권장 / 변경이력 갱신 |
| R-2 | opwt Phase 3 워커 프롬프트(보강·재작성·신규·외부API)에 공통 작성 원칙 주입 | `network-guide.md` §7에 R-1 참조 블록 추가 |
| R-3 | opwt QA 검증에 비즈니스 용어 체크 추가 | `consistency-rules.md`에 "본문이 코드 식별자를 주어로 썼는가" 검증 항목 추가 |
| R-4 | brain 페이지 작성 규칙에 동일 원칙 적용 | `op-brain-ingest/SKILL.md` STEP 4 페이지 작성 규칙에 1줄 추가 |
| R-5 | 공통 문서 표준 포인터 | `opal-doc-standard.md` 정책서 행에 R-1 포인터 추가 |
| R-6 | 확정 기준 영구 기록 | `.opal/AGENT.md` 확정 기준 표에 #7 행 추가 (캡틴 제공 문안) |
| R-7 | 배포 + 변경이력 | `install-mac.sh` 재배포 / 수정 문서 변경이력 행 추가 |

## 4. 관련 문서 (참조 테이블)

| # | 유형 | 문서 | 경로 | 참조 이유 |
|---|------|------|------|----------|
| D-1 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | 근거/용어 SSOT — 원칙 신설 위치 (R-1) |
| D-2 | 설계 | network-guide.md | `opal/skills/opal-pilot-write-tech/references/network-guide.md` | opwt Phase 3 워커 프롬프트 (R-2) |
| D-3 | 설계 | consistency-rules.md | `opal/skills/opal-pilot-write-tech/references/consistency-rules.md` | opwt QA 검증 (R-3) |
| D-4 | 설계 | op-brain-ingest SKILL.md | `opal/skills/op-brain-ingest/SKILL.md` | brain 페이지 작성 규칙 (R-4) |
| D-5 | 설계 | opal-doc-standard.md | `opal/core/references/opal-doc-standard.md` | 공통 문서 표준 (R-5) |
| D-6 | 설계 | 프로젝트 AGENT.md | `.opal/AGENT.md` | 확정 기준 표 (R-6) |
| D-7 | 설계 | install-mac.sh | `scripts/install-mac.sh` (또는 동등 배포 스크립트) | 배포 (R-7) |

## 5. 제약

- 배포 경계: `~/.opal/` 직접 편집 금지. 프로젝트 소스(`opal/`)만 수정 후 install로 배포.
- SSOT 단일화: 원칙 본문은 `citation-rules.md` 1곳에만 두고 나머지는 참조만 (헌법 거버넌스 — 하위 문서는 재서술 금지).
- 변경이력 누락 금지: 수정한 참조/스킬 문서 각각에 변경이력 행 추가.
- 동작검증(TEST) 불요: 문서/프롬프트 변경. 코드 로직 변경 없음.

## 6. 캡틴 제공 확정 기준 문안 (R-6 원문)

> 정책서·brain 등 기획 산출물은 코드 변수·enum·식별자 나열 금지 — 반드시 비즈니스 용어/자연어로 설명하고, 코드 식별자(`autoSelCancelYn`·`AUTO_SELECT_CANCELABLE` 등)는 괄호+근거 인용(`경로:줄번호`)으로만 병기한다. 조건·상태군은 의미를 풀어 쓴다(예: `autoSelCancelYn≠N` → "자동취소가 켜져 있고", `basicPugCpMsnBscId≠null` → "기본 미션이 지정되어 있으며"). 코드는 SSOT 근거이지 본문 서술의 주어가 아니다. 표는 "조건(용어)"+"코드 근거" 분리 권장.
