# DONE: code-scan PM 우선 무조건화 — 코드 작업 한정 + scan.json 자동 생성 + brain 역할 분담

> 완료일: 2026-06-11 22:56 | 적용 스킬: opp | 모드: semi-agentic
> 채번: 2026-05-26 (v1) → 2026-06-11 v2 재정의(016 이후 다이어트, 캡틴 결정 a) 후 당일 완료
> 산출물: TASK.md(v2) / PLAN.md / AGENTIC-LOG.md / DONE.md

## 완료 요약

코드 변경·코드 탐색 작업의 PM 디스패치 전 code-scan 호출을 조건부 옵션에서 **무조건 1순위 강제**로 격상했다. scan.json 부재 시 인터럽트 없는 즉석 자동 생성, 빈 결과 폴백 3분기, 사용자 오버라이드를 규약화했고, 016 opal-brain과의 역할 분담(brain=선별·stale·WHY / code-scan=전수·실시간·WHAT — 차이는 선별·신선도·깊이)을 명문화하여 트리거-인센티브-검증 루프를 폐쇄했다.

## 요구사항 달성 (F-1~F-6 전부 ✅)

| F | 결과 | 위치 |
|---|------|------|
| F-1 코드 작업 무조건화 | 조건부 진입·Glob/Grep 회피 경로 제거 + 코드/문서 판별 1줄 + 무조건 호출 + 자동생성/폴백 연결 | `dispatch-process.md` v1.4 |
| F-2 brain 역할 분담 | 4축 표(범위/신선도/깊이/원천) + 오버라이드 + analyze 의존 1줄 | `AGENT.md` v3.3 + `dispatch-process.md` |
| F-3 scan.json 자동 생성 | "첫 호출 시 부재면 즉석 추론 생성" + 추론 소스 3종(scopes/extensions+.md/exclude) + 보고 1줄 | `code-scan-management.md` v1.1 |
| F-4 빈 결과 폴백 | 3분기(0건→보강 / 커버리지30%↓→동시 / 정상→단독) + STATE 자유 텍스트 기록(행 편집 금지 3중 한정) | `header-rules.md` v1.1 |
| F-5 PM Gate 항목 | 14번 신설 — 코드 태스크 디스패치 컨텍스트 code-scan 인용 검증(문서 N/A) | `pm-review-gate.md` v1.5 |
| F-6 후속·폐기 기록 | 후속 2(Phase 2 워커 강제 / @header 커버리지 확충) + 폐기 1(.md 표준화→brain ingest 흡수) | `.opal/MEMORY.md` + `memory/follow-up-code-scan-phase2.md` |

+ `opal-pm.md` v1.2 §9 정합 (C-1 라우팅) / install 2회 재배포·배포본 grep 검증.

## v2 재정의 핵심 (TASK §v2 표 — 016 연동)

- 적용 범위: 모든 디스패치 → **코드 작업 한정** (문서 탐색은 brain search 담당)
- PM(대화) 전면 강제 제외, Phase 3 .md @header 표준화 폐기
- brain 종속 명문화: `analyze`는 code-scan @header 집계 의존 → code-scan 보급률이 brain 지식 품질의 상한

## 검증 증거

- AC 전건 grep 증거 (소스 + `~/.opal/` 배포본 — install 2회)
- 016 회귀 0: AGENT.md §opal-brain 활용 규칙(W4/W5) 무변경(워커 diff + PM grep 재검증), "brain → code-scan" 순서 보존(`dispatch-process.md:134-135`)
- state validate violations 0 / QA 체크리스트 15/15
- doc_code_mismatch 2건 코드 기준 처리: C-1(opal-pm.md §3 stub → §9 라우팅), C-2(code-scan.js 줄번호 :274-312 정정)

## PM Gate 발견·해소

- AGENT.md §code-scan 도입부 잔존 조건부 1건 — PLAN AC 미명시 누락분을 PM Gate spot-check로 발견, PM 직접 보정 + 재배포 (AGENTIC-LOG #3~4)

## 잔여·후속

1. **Phase 2 후속**: 워커 자체 탐색 강제(code-scan 우선) 격상 — 운영 데이터 축적 후 판단 (메모리 기록)
2. **후속**: OPAL 본 프로젝트 @header 커버리지 확충 — brain analyze 품질의 원료 (현 2파일 수준)
3. 미커밋 — 캡틴 지시 시 커밋 (브랜치 `feat/opal-brain-wiki`)
