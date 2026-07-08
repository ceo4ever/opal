# TASK: code-scan PM 우선 무조건화 — 코드 작업 한정 강제 + scan.json 자동 생성 + brain 역할 분담

> 작성일: 2026-05-26 | **v2 재정의: 2026-06-11 (016 opal-brain 이후 다이어트 — 캡틴 결정 a)** | 작업 유형: 개선 | 적용 스킬: opp | 모드: semi-agentic
> 입력: 캡틴 발화 + 대화 누적 결정 6건 (v1) + 016 이후 재평가 대화 (v2)
> 출력: TASK.md

## 작업 목표

**코드 변경·코드 탐색이 필요한 작업**의 PM 디스패치 전 단계에서 code-scan 호출을 조건부 옵션에서 **무조건 1순위 강제**로 격상한다. `.opal/code-scan.json` 자동 생성 규약 + 빈 결과 폴백 기준 + 사용자 오버라이드를 명문화하고, **016에서 신설된 opal-brain과의 역할 분담(brain=WHY/HOW 요약 지식, code-scan=실시간 WHAT 구조)을 규약에 명시**하여 트리거-인센티브-검증 루프를 폐쇄한다.

## v2 재정의 — 016 이후 범위 변경 (SSOT)

| 구분 | v1 원안 | v2 확정 | 사유 |
|------|---------|---------|------|
| 디스패치 전 무조건화 | 모든 디스패치 | **코드 변경·코드 탐색 작업 한정** | 순수 문서 작업은 code-scan 불요. brain search가 문서 탐색 담당 (016 W5) |
| PM(대화) 모드 전면 강제 | 포함 | **제외** — 코드 구조 질문 시 우선 사용 원칙만 유지 | 일반 질의 1차 채널은 brain search로 이동 (016) |
| brain 역할 분담 명문화 | (없음 — 016 이전) | **신규 F-2** | analyze가 code-scan @header 의존 + brain→code-scan 순서 (016 dispatch-process v1.3) |
| Phase 3 .md @header 표준화 | 후속 예고 | **폐기** | 문서 요약·검색은 brain ingest가 흡수 (016 W2) |
| Phase 2 워커 강제 / OPAL @header 커버리지 확충 | 후속 예고 | 후속 유지 | 워커 강제는 운영 데이터 후 판단. @header 커버리지는 brain analyze 품질의 원료 |

## 배경 (v1 진단 — 여전히 유효)

OPAL 전반에서 `code-scan`(v1.2.0) 활용률이 낮다. 트리거가 "조건부 옵션"으로 박혀 있어 사용 안 함이 디폴트가 된다:

1. **트리거가 조건부**: 핵심 문서들이 "`.opal/code-scan.json`이 존재하는 프로젝트에서" 활용으로 한정하고 "없으면 Glob/Grep 폴백"이라는 매끄러운 회피 경로 제공. 016에서도 이 조건부 문구는 미수정.
2. **PM 생성 의무 발동 시점 모호**: `pm/code-scan-management.md`의 "처음 사용하려 할 때"가 언제인지 게이트 부재.
3. **사전 활용 게이트 부재**: `pm-review-gate.md`는 EXECUTE 사후 @header 검증만 다룸. 디스패치 전 code-scan 활용 게이트 없음.
4. **@header 생산-소비 비대칭**: 작성은 강제(EXECUTE Step 3-H), 소비는 옵션 → 자산이 쌓여도 안 쓰임.
5. **(v2 신규) brain 종속 관계**: 016 `brain-tool analyze`(init 동적 제안의 입력)가 code-scan @header 집계에 의존 → code-scan 보급률이 brain 품질의 상한이 됨. 실증: OPAL 본 프로젝트 @header 커버리지 2파일 수준이라 analyze 결과 빈약 (016 세션 확인).

실증 사례: MAMS 프로젝트는 scopes/extensions(.md 포함)/exclude를 갖춘 scan.json을 운영하며 frontmatter @header가 `code-scan.js:278-301`로 파싱됨을 확인 (v1).

## 요구사항

- [ ] **F-1. 코드 작업 디스패치 전 code-scan 무조건화** (`pm/dispatch-process.md` + `opal-pm.md §3`)
  - **무엇을**: "code-scan 사전 범위 파악" 절의 조건부 표현("`.opal/code-scan.json`이 존재하는 프로젝트에서") 제거 → "**코드 변경·코드 탐색이 필요한 작업이면 무조건 호출**" + 결과 3분기(F-4) 연결. 순수 문서 작업은 명시적 스킵 허용.
  - **어디에**: `opal/core/references/pm/dispatch-process.md` §code-scan 사전 범위 파악 (016 v1.3 기준 — 줄번호 재확인 필요) + `opal-pm.md §3` 요약 정합.
  - **왜**: 진단 §1·§3. **AC**: ① "코드 작업이면 무조건 호출" 문구 존재 ② 조건부 문구 제거 ③ 코드/문서 작업 판별 기준 1줄 명시 ④ 결과 3분기 명시.

- [ ] **F-2. brain ↔ code-scan 역할 분담 명문화** (`opal/core/AGENT.md` + `pm/dispatch-process.md`)
  - **무엇을**: ① AGENT.md "code-scan 활용 규칙"에 역할 분담 표(brain=**선별 핵심 모듈**의 @header 스냅샷+설계 배경 WHY — 원천은 code-scan @header, ingest/sync 시점 기준이라 stale 가능 / code-scan=**전수·실시간** WHAT 구조·exports·depends. 코드 정보의 차이는 포함 여부가 아닌 선별·신선도·깊이) + "scan.json 없으면 사용 생략" 행을 F-3 자동 생성으로 교체 ② 사용자 오버라이드("grep으로 해" 등 발화 시 자체 도구 즉시 전환) 명문화 ③ dispatch-process의 brain(Step 1.5)→code-scan 순서에 "analyze는 code-scan @header 의존" 1줄.
  - **어디에**: `opal/core/AGENT.md` §code-scan 활용 규칙·§opal-brain 활용 규칙 (016 v3.2 기준), `pm/dispatch-process.md`.
  - **왜**: v2 재정의 — 두 도구의 경계 모호가 미사용의 새 원인이 되는 것 방지. **AC**: ① 역할 분담 표 존재 ② 오버라이드 문구 존재 ③ analyze 의존 관계 1줄 존재.

- [ ] **F-3. scan.json 자동 생성 규약 신설** (`pm/code-scan-management.md`)
  - **무엇을**: "처음 사용하려 할 때" → "**PM 첫 호출 시 부재면 인터럽트 없이 즉석 추론 생성**". 추론 소스 3종: `scopes`(docs/PROJECT.md 프로젝트 구성) / `extensions`(프로젝트 확장자 자동 + .md 기본 포함) / `exclude`(기본값 + backup 등 보강). 생성 직후 1줄 보고 형식.
  - **어디에**: `opal/core/references/pm/code-scan-management.md` §생성 시점.
  - **왜**: 진단 §2. **AC**: ① 즉석 생성 문구 ② 추론 소스 3종 규약 ③ 생성 보고 1줄 형식.

- [ ] **F-4. 빈 결과 폴백 기준 명문화** (`harness/header-rules.md` §code-scan 활용 가이드에 흡수 — 신설 파일 없음)
  - **무엇을**: 3분기 — ① 검색(`search`/`exports`) 매칭 0건 → Glob/Grep 보강 ② `scan/domain/layer` @header 커버리지 30% 미만 → code-scan+Glob/Grep 동시 활용 ③ 그 외 → code-scan 결과만. 폴백 발동 시 STATE.md **자유 텍스트 영역**(블로커/다음 액션 — 현황판 행 아님, state-tool 비경유 영역)에 "code-scan 폴백: {사유}" 1줄 기록.
  - **어디에**: `opal/core/references/harness/header-rules.md` §code-scan 활용 가이드.
  - **왜**: 진단 §1 "결과 부족" 모호성 제거. **AC**: ① 3분기 표 존재 ② STATE 자유 텍스트 기록 규약(행 편집 아님 명시) ③ PM이 디스패치 전 Read 가능한 경로.

- [ ] **F-5. PM Gate 검증 항목 추가** (`harness/pm-review-gate.md`)
  - **무엇을**: "**코드 변경 태스크**의 디스패치 컨텍스트에 code-scan 결과(domain/layer/depends/exports)가 인용되었는가" 항목 신설 (문서 작업은 N/A).
  - **어디에**: `opal/core/references/harness/pm-review-gate.md` 표준 검토 항목 (현행 13항목 뒤 — 번호 충돌 없게).
  - **왜**: 진단 §3. **AC**: ① 항목 추가 ② 코드/문서 트리거 조건 명시 ③ 기존 번호 정합.

- [ ] **F-6. 후속 태스크 후보 기록 + Phase 3 폐기 명시** (`.opal/MEMORY.md`)
  - **무엇을**: Phase 2(워커 자체 탐색 강제 — 운영 데이터 후) + OPAL 본 @header 커버리지 확충(brain analyze 품질 원료)을 후속 후보로 기록. .md @header 표준화는 **폐기(brain ingest 흡수)** 사유와 함께 기록.
  - **왜**: v2 재정의 추적성. **AC**: 메모리에 후속 2건 + 폐기 1건이 사유와 함께 기재.

## 제약 조건

- **변경 범위 한정**: PM 행동 규약 + 생성 규약 + 폴백 기준 + PM Gate 항목만. 워커 AGENT.md 6종 **미수정**. 코드(`code-scan.js`) 무변경.
- **016 산출물 회귀 금지**: AGENT.md v3.2·dispatch-process v1.3의 brain 규칙(W4·W5)을 훼손하지 않는다. brain→code-scan 순서 유지.
- **state-tool 정합**: STATE.md 폴백 기록은 자유 텍스트 영역만 사용 — 현황판 행 직접 편집 금지.
- **하위 호환**: 기존 태스크/문서 소급 변경 없음 (citation-rules §5).
- **변경이력 의무**: 수정 .md 전부 변경이력 행 추가 (KST + 010).
- **배포 경계**: 소스(`opal/core/`) 수정 후 install 재배포.

## 기술 스택

- OPAL 프레임워크 (Markdown SSOT) / `code-scan v1.2.0` (`opal/tools/code-scan/code-scan.js`) / `state-tool` / `brain-tool`(016 — 정합 확인용)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | opal-pm.md | `opal/core/references/opal-pm.md` | §3 디스패치 전 프로세스 — F-1 |
| D-2 | 설계 | dispatch-process.md | `opal/core/references/pm/dispatch-process.md` | §code-scan 사전 범위 파악 + §Step 1.5 (016 v1.3) — F-1·F-2 |
| D-3 | 설계 | core/AGENT.md | `opal/core/AGENT.md` | §code-scan 활용 규칙 + §opal-brain 활용 규칙 (016 v3.2) — F-2 |
| D-4 | 설계 | code-scan-management.md | `opal/core/references/pm/code-scan-management.md` | 생성 규약 — F-3 |
| D-5 | 설계 | header-rules.md | `opal/core/references/harness/header-rules.md` | §code-scan 활용 가이드 — F-4 |
| D-6 | 설계 | pm-review-gate.md | `opal/core/references/harness/pm-review-gate.md` | 표준 검토 항목 (현행 13항목) — F-5 |
| D-7 | 소스 | code-scan.js | `opal/tools/code-scan/code-scan.js` | 도구 능력 (.md frontmatter @header 파싱 `:278-301`) |
| D-8 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | 산출물 인용 포맷 |
| D-9 | 설계 | opal-harness.md | `opal/core/references/opal-harness.md` | §1 오버라이드 메커니즘 + §9 도구 우선 원칙 |
| D-10 | 외부 | MAMS scan.json 실증 | `/Volumes/Data/StoreLinkStudio/mams/.opal/code-scan.json` | scopes/extensions 패턴 실증 |
| D-11 | 설계 | 016 결정 (brain 역할) | `tasks/016-260611-opp-wiki-intelligence/DONE.md` + `.opal/brain/pages/concept/wiki-intelligence-decisions-016.md` | brain/code-scan 역할 분담·analyze 의존 근거 |
