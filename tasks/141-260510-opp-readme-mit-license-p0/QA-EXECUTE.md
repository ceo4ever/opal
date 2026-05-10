# QA: EXECUTE — README 오픈소스 공개 P0 정비 (MIT LICENSE + 표시·실측 정정)

> 검토일: 2026-05-10 | 판정: Pass

## 1. 요약

LICENSE 신규 생성(SPDX MIT 표준 텍스트), README 배지 2종·License 섹션 신설, OPAL_VERSION 예시 generic 화, 부트스트랩 첫 줄 7칼럼 정정, agents 카운트 13개, community-skills 30개/6개 조직, MCP 트러블슈팅 라인 대체, ARCHITECTURE.md 에이전트 표·배포 모델 동기화 — TASK.md R-1~R-8 전 항목 구현 완료. 실측 검증(find, grep) 통과. 분류 레이블 표현의 미세 불일치(Warning 1건)가 있으나 합계 13개는 일치하며 진행에 지장 없음.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| R-1 | LICENSE 파일 존재 + SPDX MIT 표준 텍스트 + 저작권 1행 + 추가 텍스트 없음 | Pass | `/Volumes/Data/AiStudio/workspace/opal/LICENSE` 존재, 22행, `MIT License` / `Copyright (c) 2026 OPAL contributors` / `Permission is hereby granted...` 순 정합 |
| R-2 | README 상단 배지 2종 (License-MIT yellow.svg + github/v/release/ceo4ever/opal) | Pass | L5: `[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) [![Latest Release](https://img.shields.io/github/v/release/ceo4ever/opal)](https://github.com/ceo4ever/opal/releases)` |
| R-3 | README 하단 `## License` 헤딩 + MIT 명시 + `[LICENSE](LICENSE)` 링크 + 저작권 표기 | Pass | L778 `## License` / L780 MIT + LICENSE 링크 / L782 `Copyright (c) 2026 OPAL contributors` |
| R-4 | `<원하는-태그>` placeholder 2건 + GitHub Releases 링크 한 줄 안에 포함 + specific 버전 표기 0건 | Pass | L98: `OPAL_VERSION=<원하는-태그>` (mac/linux) + `$env:OPAL_VERSION = '<원하는-태그>'` (Windows) + Releases 링크 동일 라인. `grep OPAL_VERSION=v` → 0건 |
| R-5 | 부트스트랩 첫 줄 7칼럼 (`PM모드` 포함) + AGENT.md L53 SSOT 일치 | Pass | L105: `[부트스트랩] ✅ identity ✅ harness ✅ PM ✅ PM모드 ⏳ registry ⏳ references ⏳ model-mapping` — `~/.opal/AGENT.md:53`과 완전 일치 |
| R-6 | README L729 agents 13개 분류 + ARCHITECTURE.md L188 `(12개)` + L189 `(범용 1개)` 합계 13 + 에이전트 표 13행 | Warning | 합계 13 일치. 단, 분류 레이블 표현 미세 불일치 (§3 참조) |
| R-7 | README L730 `30개 / 6개 조직` + 실측 30개 / 6개 조직 일치 | Pass | `find community-skills -maxdepth 3 -name SKILL.md \| wc -l` = 30, `ls -1d community-skills/*/` = 6개 |
| R-8 | "설치 메뉴에서 [2] 또는 [3]" 표현 0건 + 검증 명령 안내 존재 | Pass | `grep 설치 메뉴` → 0건. L774: `claude mcp list` / `opal-cli doctor` 안내 포함 |
| GE-1 | PLAN.md §3 실행 체크리스트 10개 Step 전부 `[x]` 완료 | Pass | Step 1~10 모두 `[x] 완료` 표시 |
| GE-2 | 산출물 3개 존재 확인 (LICENSE / README.md / ARCHITECTURE.md) | Pass | 파일 존재 확인 완료 |
| GE-3 | TASK.md R-1~R-8 전 요구사항 충족 | Pass | R-6 분류 레이블 불일치 제외 실질적 모든 AC 충족 |
| CON-1 | LICENSE 저작권 ↔ README §License 저작권 텍스트 정합 | Pass | 양측 `Copyright (c) 2026 OPAL contributors` 동일 |
| CON-2 | README ASCII 박스(L727-734) 폭 정합 | Pass | 내부 콘텐츠 라인 (L728-733) display_width 모두 60 일치 |
| CON-3 | 변경이력 행 추가 안 함 (LICENSE / README / ARCHITECTURE) | Pass | 3개 파일 모두 `변경이력` 헤딩 없음 |

## 3. 지적 사항

### Warning — R-6: 분류 레이블 표현 불일치

- **심각도**: Warning
- **위치**: README L729 ↔ ARCHITECTURE.md §에이전트 표
- **내용**:
  - README L729: `서브에이전트 (전문 6 + 범용 5 + GC 2)` — GC 체커를 별도 카테고리로 표기
  - ARCHITECTURE.md 에이전트 섹션: `**범용 에이전트 (기존)**` 하나의 테이블에 opal-security-checker / opal-convention-checker를 포함하여 7행 (GC 체커가 범용 테이블에 내포)
  - **합계**: 양측 모두 13개 일치
- **영향**: 기능·카운트 정합에는 영향 없음. 사용자가 두 문서를 나란히 읽을 경우 "GC가 범용에 포함인가, 별도 카테고리인가"에 혼동 가능성 존재
- **근거**: PLAN M-4 설계에서 `(전문 6 + 범용 5 + GC 2)` 레이블을 명시했고 M-9에서 "범용 에이전트 표 하단에 2행 추가"를 결정 — 두 설계가 레이블 일관성보다 각각의 수정 목표를 우선한 결과
- **권고**: 향후 P1 태스크에서 ARCHITECTURE.md §에이전트 분류를 GC 체커 전용 서브섹션으로 분리하거나, README 표기를 `범용 7 + 전문 6`으로 통일 (현재는 진행 무방)

### Info — ARCHITECTURE.md agent count 라인 번호 이동

- **심각도**: Info
- **내용**: PLAN §4 QA 체크리스트에서 "ARCHITECTURE.md L186 = 12개, L187 = 1개"라고 참조했으나 실제 파일에서 해당 내용은 L188, L189에 위치함 (다른 편집으로 2행 이동). 내용 자체는 정확히 반영되어 있음.
- **영향**: QA 리포트 라인 번호 참조 오차 — 기능 무관

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md R-1 AC | SPDX 표준 텍스트 + `Copyright (c) 2026 OPAL contributors` + 추가 텍스트 없음 | Pass |
| TASK.md R-2 AC | 두 배지 SVG URL 정합 + License 배지 → LICENSE 상대 링크 | Pass |
| TASK.md R-3 AC | `## License` + MIT 명시 + `[LICENSE](LICENSE)` + 저작권 표기 | Pass |
| TASK.md R-4 AC | specific 버전 0건 + placeholder + Releases 링크 한 줄 | Pass |
| TASK.md R-5 AC | AGENT.md:53 칼럼 수(7)·항목명·구분자 일치 | Pass |
| TASK.md R-6 AC | 카운트 13개 일치 + ARCHITECTURE.md 분류 정합 (레이블 불일치 Warning) | Warning |
| TASK.md R-7 AC | 30개 + 6개 조직 실측 일치 | Pass |
| TASK.md R-8 AC | "설치 메뉴" 표현 제거 + 검증 명령 안내 | Pass |
| PLAN.md §3 체크리스트 | Step 1~10 `[x]` 완료 | Pass |
| PLAN.md §4 QA 체크리스트 | R-1~R-8 + 일관성 + 문서 품질 항목 `[x]` 완료 | Pass |
| PLAN.md §제약 조건 | 변경이력 행 추가 안 함 (3개 파일) | Pass |

## 5. 판정

**Pass**

R-1~R-8 전 요구사항이 구현되었고 실측 검증(find/grep)이 통과한다. ARCHITECTURE.md와 README 간 GC 체커 분류 레이블 표현 불일치(Warning 1건)가 있으나 합계 13개 카운트는 정합하며 기능·법적 효력에 영향이 없다. Critical 항목 없음. 다음 단계(CLOSE) 진행 가능.
