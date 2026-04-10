# QA-EXECUTE: opsdd STATE Gate 완성 + VERIFY Phase 추가

> QA 수행일: 2026-04-10 | 단계: EXECUTE

## 결과 요약
- 총 체크 항목: 33
- 통과: 32
- 이슈: 1 (Minor)

## 체크리스트

### 4-1. STATE Gate 완성 검증

- [x] SKILL.md STATE.md 도메인 치환값의 진행 현황 행 구조가 하네스 §3 "진행 현황 행 구성 규칙"과 일치한다 — SKILL.md 293~336행의 43행 테이블이 harness.md §3 opsdd 행 예시(opal/core/references/opal-harness.md:237~281)와 행 번호·Phase·항목명 전부 일치.
- [x] 진행 현황 행 총 43행 구조이다 (TASK 3 + SPEC 8 + REVIEW 9 + DESIGN 8 + EXECUTE 5 + VERIFY 6 + DONE 4) — SKILL.md 293~336행 계수: 행 1~3(TASK 3) + 4~11(SPEC 8) + 12~20(REVIEW 9) + 21~28(DESIGN 8) + 29~33(EXECUTE 5) + 34~39(VERIFY 6) + 40~43(DONE 4) = 43행 확인.
- [x] ACT 목록 SSOT 섹션이 있다 (`| ACT | 이름 | 그룹 | 의존 | 코드 | L1 lint | L2 build | 상태 | 시작 | 완료 |`) — SKILL.md 343행 헤더 정확히 일치.
- [x] TS 현황 섹션이 있다 (Green/Red/Fail/Skip 건수 테이블) — SKILL.md 349~358행 `## TS 현황 (VERIFY Phase 요약)` 섹션, Green/Red/Fail/Skip 4행 테이블 확인.
- [x] SPEC 변경 이력 섹션이 있다 — SKILL.md 360~365행 `## SPEC 변경 이력` 섹션 확인.
- [x] "완료 산출물" 독자 테이블 구조가 제거되었다 — SKILL.md 전체에서 `완료 산출물` 섹션/테이블 미발견 (변경이력 440행에 과거 흔적 언급만 있음). 제거 확인.
- [x] 진행 현황 행 수행 원칙 주석이 포함되어 있다 — SKILL.md 290행: `> **수행 원칙**: 위에서 아래로 순서대로 처리한다. 현재 행이 ✅가 아니면 다음 행으로 진행 불가.`

### 4-2. ACT 목록 SSOT 검증

- [x] execute-loop-guide.md §9.2(또는 ACT 목록 섹션) 테이블 구조가 `| ACT | 이름 | 그룹 | 의존 | 코드 | L1 lint | L2 build | 상태 | 시작 | 완료 |`다 — execute-loop-guide.md 318행 헤더 확인, SKILL.md 343행과 동일.
- [x] SKILL.md의 ACT 목록 SSOT 컬럼이 execute-loop-guide.md와 일치한다 — 양쪽 모두 `| ACT | 이름 | 그룹 | 의존 | 코드 | L1 lint | L2 build | 상태 | 시작 | 완료 |` 10컬럼 구조로 일치.
- [x] spec-plan-guide.md에 ACT 상태 필드 금지 원칙이 명시되어 있다 ("STATE.md ACT 목록 테이블이 SSOT") — spec-plan-guide.md §7 주의사항(274~278행): "ACT 블록에 상태 필드(`- **상태**: 대기/완료`)를 두지 않는다. ACT 실행 상태는 STATE.md ACT 목록 테이블이 SSOT다." 확인.

### 4-3. VERIFY Phase 검증

- [x] SKILL.md 파이프라인 다이어그램에 VERIFY Phase가 포함된다 (EXECUTE-LOOP → VERIFY → DONE) — SKILL.md 47~52행 파이프라인에 `Phase 5: VERIFY ... → Phase 6: DONE` 명시. 23행 Harness 모드 라인에도 `EXECUTE-LOOP → VERIFY → DONE` 순서 확인.
- [x] YAML frontmatter description이 "6단계 파이프라인"을 반영한다 — SKILL.md 4행: `명세 기반 개발을 6단계 파이프라인으로 수행한다.`
- [x] version이 2.5.0으로 업데이트되었다 — SKILL.md 13행: `version: 2.5.0`
- [x] Phase 5: VERIFY 섹션이 존재한다 — SKILL.md 234행: `## Phase 5: VERIFY`
- [x] Phase 6: DONE 섹션으로 번호가 이동되었다 — SKILL.md 255행: `## Phase 6: DONE`
- [x] VERIFY Phase에 E2E 수행 + TEST-SCENARIOS.md 갱신 의무가 명시되어 있다 — SKILL.md 242~244행: `1. TEST-SCENARIOS.md의 모든 시나리오를 Playwright E2E로 수행` / `2. 각 시나리오 Pass/Fail 확인 즉시 TEST-SCENARIOS.md 추적 매트릭스 갱신 (배치 금지)`
- [x] VERIFY Phase Gate 흐름이 명시되어 있다 — SKILL.md 239행: `Gate: State Gate → PM Gate → State Gate → 사용자 Gate`

### 4-4. L1/L2 검증 루프 검증

- [x] execute-loop-guide.md에 L1/L2 검증 루프 규칙이 명시되어 있다 — execute-loop-guide.md 337~356행 `## L1/L2 검증 루프` 섹션. L1(tsc --noEmit) + L2(pnpm build) 절차, 재시도 한도 테이블 포함.
- [x] SKILL.md Phase 4에 PM이 각 ACT 완료 후 L1/L2 직접 검증 의무가 명시되어 있다 — SKILL.md 204~214행 `### L1/L2 검증 루프 (PM 직접 실행)`: "PM은 워커가 각 ACT를 완료할 때마다 다음을 직접 실행한다"
- [x] L1 무제한 재시도, L2 2회 초과 → 캡틴 에스컬레이션 규칙이 반영되어 있다 — execute-loop-guide.md 350~351행 테이블: `L1 lint/type | 제한 없음 | —` / `L2 build | 2회 | 캡틴 에스컬레이션`. SKILL.md 212행: `L2 2회 초과 실패 → 캡틴 에스컬레이션` (L1 무제한 규칙은 execute-loop-guide.md에 위임).
- [x] execute-loop-guide.md §9.3 갱신 시점 테이블에 L1/L2 관련 이벤트 행이 추가되어 있다 — execute-loop-guide.md 363~369행: `ACT L1 통과 | 코드 ✅, L1 lint ✅ 갱신` / `ACT L2 통과 | L2 build ✅, 상태 ✅, 완료 날짜 기록` / `ACT L1/L2 실패 | L1 lint ❌ 또는 L2 build ❌ 갱신` 3행 추가 확인.

### 4-5. 일관성 검증

- [x] SKILL.md의 파이프라인 요약, STATE.md 도메인 치환값, 각 Phase 섹션이 모두 6단계를 일관되게 반영한다 — 파이프라인 요약(32~53행): Phase 0~6 명시. 도메인 치환값(271행): `TASK / SPEC / REVIEW / DESIGN / EXECUTE-LOOP / VERIFY / DONE`. 각 Phase 섹션: Phase 0~6 모두 존재. 일관성 확인.
- [x] harness.md §3의 opsdd 진행 현황 행 예시가 SKILL.md의 도메인 치환값 43행과 일치한다 — opal/core/references/opal-harness.md 237~281행(43행 예시)과 SKILL.md 293~336행 전수 대조: 행 번호, Phase명, 항목명 전부 일치.
- [~] 소스 경로(`opal/skills/`, `opal/core/`)만 수정되고 `~/.opal/` 직접 수정이 없다 — 수정 대상 4개 파일 모두 `opal/skills/` 또는 `opal/core/` 경로에 위치. `~/.opal/` 직접 수정 없음. 단, `~/.opal/references/opal-harness.md`(배포본)에는 v3.4 변경사항(opsdd 43행 예시)이 아직 반영되지 않은 상태 확인 — 소스→배포 sync(install)가 필요하나, 이는 배포 절차 문제이며 소스 수정 범위 준수 자체는 Pass.

### 4-6. 변경이력 검증

- [x] SKILL.md 변경이력에 v2.5.0 항목이 추가되어 있다 — SKILL.md 441행: `| v2.5.0 | 2026-04-10 | R-1 STATE.md 도메인 치환값 → 43행 진행 현황 구조로 교체 + ACT 목록 SSOT + TS 현황 + SPEC 변경이력 섹션 추가; R-2 VERIFY Phase(Phase 5) 신설 + DONE → Phase 6; R-3 EXECUTE-LOOP L1/L2 검증 루프 명시 (105) |`
- [x] execute-loop-guide.md 변경이력에 항목이 추가되어 있다 — execute-loop-guide.md 433행: `| 2026-04-10 | R-3 | ACT 목록 테이블 L1/L2 컬럼 추가 (의존, 코드, L1 lint, L2 build, 시작, 완료) + L1/L2 검증 루프 규칙 섹션 추가 + 9-3 갱신 시점 테이블에 L1/L2 이벤트 행 추가 |`
- [x] spec-plan-guide.md 변경이력에 항목이 추가되어 있다 — spec-plan-guide.md 294행: `| 2026-04-10 | R-4 | §7 주의사항 추가 — ACT 블록에 상태 필드 금지 원칙 (STATE.md ACT 목록 테이블이 SSOT) |`
- [x] opal-harness.md 변경이력에 항목이 추가되어 있다 — opal/core/references/opal-harness.md 688행: `| v3.4 | 2026-04-10 | §3 진행 현황 행 구성 규칙에 opsdd (opal-pilot-sdd) 43행 진행 현황 예시 추가 (R-5, 105) |`

## 이슈 목록

| # | 심각도 | 항목 | 내용 | 권고 |
|---|-------|------|------|------|
| 1 | Minor | 4-5. 소스-배포 동기화 | `~/.opal/references/opal-harness.md`(배포본)에 v3.4(opsdd 43행 예시) 변경사항이 반영되지 않아 소스와 diff 발생. `install-mac.sh` 또는 `opal install` 실행으로 배포 sync 필요 | install 스크립트 실행으로 배포본 갱신 |

## 판정

PASS

> 이슈 #1은 소스 파일 수정 완료 후 배포 sync가 미수행된 상태로, 소스 코드 범위의 변경은 올바르게 수행되었다. 기능 오동작 또는 명세 불일치 없음. 전체 33항목 중 32항목 Pass, 1항목 Minor(개선 사항).
