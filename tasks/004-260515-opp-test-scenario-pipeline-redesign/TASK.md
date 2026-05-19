# TASK: 테스트 시나리오 양식·작성 흐름·파이프라인 재설계

> 작성일: 2026-05-15 | 작업 유형: 개선 | 적용 스킬: opp | 모드: semi-agentic
> 입력: 사용자 요청 + 직전 PM(대화) 분석
> 출력: TASK.md

## 작업 목표

테스트 시나리오의 **양식(가설→데이터 설계→L1/L2/L3)**, **작성 시점·작성자(PLAN 직후, 알투+캡틴 페어)**, **EXECUTE input 전달 흐름(TDD red-green)**, **파이프라인 구조(4→5단계 직렬)**를 일괄 재설계하여, mams 사후 회귀 패턴이 사전 시나리오로 흡수되도록 OPAL 프레임워크 SSOT를 보강한다.

## 배경

mams 프로젝트(`/Volumes/Data/StoreLinkStudio/mams`)에서 OPAL을 사용해 개발한 결과, "단위 테스트 PASS인데 캡틴이 수동 테스트에서 결함 발견" 패턴이 반복 발생했다. mams `.opal/MEMORY.md`의 활성 feedback 12건 중 9건이 이 구조이며, 최근 6개 태스크(091/092/099/101/103/106)에 사후 핫픽스가 누적되었다.

원인 4갈래:
1. Repository.bulk_upsert mock이 SQLAlchemy NOT NULL/FK/UniqueConstraint 검증을 우회
2. PLAN의 "영향 범위"가 변경 파일 자체만 보고 호출자 횡단 grep 없이 좁게 정의
3. 병렬·DB connection pool·인증 토큰 등 운영 환경 의존 검증 카테고리 부재
4. FE 시각 확인이 권고 수준 — 강제 룰 없음

## 배경 분석 (대화에서 도출)

### 현 SSOT 빈틈 7건 (`op-dev-test-scenario/SKILL.md` + `references/test-scenario-guide.md`)

| 영역 | 현 SSOT | 빠진 룰 |
|------|--------|--------|
| 시나리오 깊이 | "기대 결과 구체적·검증 가능" 자가체크 | 정상/경계/NULL/병렬/FK/외부 API 분기 — 깊이 매트릭스 미강제 |
| 도구 매핑 | unit/e2e/lint/typecheck/security 5종 | "통합 테스트(실 DB fixture)" 카테고리 + mock 금지 룰 부재 |
| 회귀 테스트 섹션 | "기존 테스트 스위트" 빈 표 | 변경 파일 호출자 grep → 의존 스위트 식별 절차 없음 |
| FE 검증 | opal-test-agent `fe` mode 존재 | dev 서버 기동 + 사용자 시각 확인 강제 항목 부재 |
| AC ↔ 시나리오 매핑 | 매핑 표 의무 (TASK 001) | AC 자체에 "정상/경계/실패" 3종 명시 룰 없음 |
| 자기보고 객관화 | opal-test-agent가 PASS/FAIL 판정 | Critical 변경에 실 환경 1회 검증 로그 첨부 의무 없음 |
| 시나리오 도출 관점 | "AC 매핑" 강제 | "리스크 가설 매핑" 부재 → 당연한 시나리오 양산 |

### 현 파이프라인 self-confirming 구조

- `opal-pilot-dev/SKILL.md` STEP 3 PLAN: "op-dev-plan 워커가 PLAN.md와 TEST-SCENARIO.md를 통합 작성한다"
- → 같은 워커가 설계 가정을 세우고 검증 시나리오도 작성 → 가정의 빈틈을 가정 작성자가 못 봄
- `op-dev-execute/SKILL.md` grep 결과: TEST-SCENARIO 언급 0건
- → EXECUTE 워커는 시나리오를 input으로 받지 않으며, PLAN.md만 보고 진행
- → "시나리오 통과 = 구현 완료 기준" 흐름이 작동하지 않음

## 확정된 설계 방향 (대화에서 합의)

### 1. 시나리오 양식 — 7섹션 구조

```markdown
## 1. 리스크 가설 표 (PLAN.md에서 가져옴)
   | ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |

## 2. 테스트 데이터 설계 (신설·필수)
   2.1 사전 조건 데이터 (테이블·식별자·상태·출처)
   2.2 시나리오별 데이터 흐름 (Given(read) → When(CUD/호출) → Then(re-read))

## 3. 검증 시나리오
   L1. 기능 단위 (자동, 실 데이터 입력)
   L2. 프로세스 통합 (자동, 실 DB read→CUD→re-read)
   L3. 사용자 협업 (수동, [SUPERVISOR] 마커)

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

## 5. 코드 품질 / 6. 보안 / 7. 판정 (기존 유지)
```

### 2. 핵심 원칙 6종 (강제 룰)

| # | 원칙 | 위반 시 |
|---|------|--------|
| 1 | mock 0 | 시나리오 본문 `mock`/`patch`/`MagicMock` 등장 시 PM Gate FAIL |
| 2 | 실 데이터 사전 명시 | "사전 조건 데이터" 표 빈 칸 시 FAIL |
| 3 | read → CUD → re-read 사이클 | Given/When/Then 3필드 누락 시 FAIL |
| 4 | 가설 ↔ 시나리오 매핑 | 매핑 안 된 시나리오 = "당연한 시나리오"로 간주 FAIL |
| 5 | 시나리오 수 = 가설 수 | 정량 의무 폐기. 가설 N건 → 시나리오 N건 이상 |
| 6 | L3 [SUPERVISOR] 마커 → PM 표준 양식 요청 | 마커 발견 시 PM이 캡틴에 명시 요청 의무 |

### 3. 파이프라인 — `opal-pilot-dev` 4→5단계 직렬 재편

```
TASK → ANALYSIS → PLAN(가설 표 포함) → TEST-SCENARIO(신설)     → EXECUTE           → TEST        → CLOSE
                  opal-plan-agent     알투(PM)+캡틴 페어    워커(시나리오 input)  opal-test-agent
```

작성자 4분리: PLAN ≠ TEST-SCENARIO ≠ EXECUTE ≠ TEST → self-confirming 0.

### 4. EXECUTE 워커 디스패치 양식 변경

```
[WORKER]
op-dev-execute 스킬을 수행하라.
**checklist_source**: PLAN.md §4.2
**scenario_source**: TEST-SCENARIO.md (신설 input)
**완료 기준**: checklist 100% + 담당 Step 매핑 L1/L2 시나리오 PASS (L3는 TEST 단계 위임)
**자가 점검 절차**: 코드 작성 → 시나리오 "실행 명령" 추출 → Bash 실행 → PASS 확인 → 완료 보고
```

### 5. semi-agentic 모드 경계 이동

- 현행: PLAN 사용자 확인 행 통과 후 EXECUTE 작업 행부터 PM 자율
- 개정: **TEST-SCENARIO 사용자 확인 행** 통과 후 EXECUTE 작업 행부터 PM 자율
- 캡틴 검토 게이트 총 2회 (PLAN 1회 + TEST-SCENARIO 1회) + CLOSE 진입 1회

### 6. 적용 범위

- `opal-pilot-dev` (opd, Full Task) **우선 적용**
- opal-pilot-dev-short(opds), opal-pilot-project(opp)는 본 태스크에서 제외 (추후 별도 태스크에서 검토)
- mams 회귀 12건이 거의 전부 opd/opds 영역. opp(범용 작업)는 현재 TEST-SCENARIO 자체가 없어 신설 시 과도

## 요구사항

- [ ] **F-001** `op-dev-test-scenario/SKILL.md` 양식 7섹션 재편
  - **무엇을**: 시나리오 통일 형식을 §1 리스크 가설 표 + §2 테스트 데이터 설계 + §3 검증 시나리오(L1/L2/L3) + §4 4열 매핑 표 + §5 코드 품질 + §6 보안 + §7 판정 구조로 갱신
  - **어디에**: `opal/skills/op-dev-test-scenario/SKILL.md` "TEST-SCENARIO.md 통일 형식" 섹션
  - **왜**: 확정 방향 §1 — 가설 기반 도출 + 데이터 설계 의무 + L계층 명시화
  - **AC**: 새 양식이 7섹션 헤딩 모두 존재, §1 리스크 가설 표 컬럼 6종(ID/변경 단위/계약/영향/계층/시나리오), §2 사전 조건 데이터 표 컬럼 4종(테이블/식별자/상태/출처) + 데이터 흐름 표 컬럼 4종(시나리오/Given/When/Then), §3 L1/L2/L3 서브헤딩 존재함을 단순 grep으로 확인

- [ ] **F-002** `op-dev-test-scenario/references/test-scenario-guide.md` 재작성
  - **무엇을**: 작성 프로세스를 (1) PLAN 가설 표 Read → (2) 데이터 설계 → (3) 계층 결정 규칙 적용 → (4) Given/When/Then 시나리오 본문 작성 → (5) AC↔가설↔계층↔시나리오 4열 매핑으로 재구성. 시나리오 수 가이드 폐기. 계층 결정 규칙 표 신설.
  - **어디에**: `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md`
  - **왜**: 확정 방향 §1 + §2 — 가이드와 양식이 일치해야 작성자(알투)가 따를 수 있음
  - **AC**: 가이드에 5단계 작성 프로세스 명시, 계층 결정 규칙 표(변경 영역 7종 × 의무 계층) 존재, "시나리오 수 가이드" 섹션 폐기됨(grep으로 부재 확인), mock 금지 룰 명시

- [ ] **F-003** `opal-pilot-dev/SKILL.md` 5단계 재편 + STATE.md 행 구성 갱신
  - **무엇을**: STEP 3 PLAN과 STEP 4 EXECUTE 사이에 **STEP 3.5 TEST-SCENARIO** 단계 신설. PLAN STEP에서 TEST-SCENARIO.md 통합 작성 지시 제거. STATE.md 도메인 치환값의 행 구성에 TEST-SCENARIO 행(작업/생성/State Gate/사용자 확인) 추가. semi-agentic 모드 경계 이동 (PLAN → TEST-SCENARIO).
  - **어디에**: `opal/skills/opal-pilot-dev/SKILL.md` STEP 3 / 신설 STEP 3.5 / STATE.md 도메인 치환값 / Agentic 흐름도
  - **왜**: 확정 방향 §3 + §5 — 5단계 직렬 + 모드 경계 이동
  - **AC**: STEP 3.5 TEST-SCENARIO 단계가 SKILL.md에 명시되고 작성자가 "알투(PM)+캡틴 페어"로 기재됨, STATE.md 행 예시에 TEST-SCENARIO 4행이 추가되어 총 행 수가 기존 25행에서 약 29행으로 증가, "자율 게이트 흐름" 다이어그램에 TEST-SCENARIO 단계가 PLAN과 EXECUTE 사이에 포함됨

- [ ] **F-004** `op-dev-execute/SKILL.md` 디스패치 input + 자가 점검 절차 추가
  - **무엇을**: SKILL.md 입력 파라미터에 `scenario_source` 추가. 완료 기준에 "checklist 100% + 담당 Step 매핑 L1/L2 시나리오 PASS" 명시. 자가 점검 절차(코드 작성 → 시나리오 실행 명령 추출 → Bash 실행 → PASS 확인) 신설. L3 시나리오는 TEST 단계 위임 명시.
  - **어디에**: `opal/skills/op-dev-execute/SKILL.md`
  - **왜**: 확정 방향 §4 — TDD red-green 흐름 작동
  - **AC**: SKILL.md에 `scenario_source` 파라미터 정의, "자가 점검 절차" 섹션 존재, "L1/L2 시나리오 PASS = 완료 기준" 명시, L3 위임 룰 명시

- [ ] **F-005** `opal-pilot-dev/SKILL.md` STEP 4 EXECUTE 디스패치 프롬프트 갱신
  - **무엇을**: 디스패치 프롬프트 양식에 `**scenario_source**: TEST-SCENARIO.md`, `**완료 기준**: ...`, `**자가 점검 절차**: ...` 3 필드 추가. 기존 `**Scope 제한**`, `**Phase 순서**` 등은 유지.
  - **어디에**: `opal/skills/opal-pilot-dev/SKILL.md` STEP 4 §4-2 디스패치 프롬프트
  - **왜**: 확정 방향 §4 — 워커가 시나리오를 input으로 받아 자가 점검 가능
  - **AC**: 디스패치 프롬프트 예시에 3 필드 추가됨을 단순 grep(`scenario_source`)으로 확인

- [ ] **F-006** `opal-plan-agent/AGENT.md` 리스크 가설 표 작성 의무 추가
  - **무엇을**: PLAN.md 산출물 표준 구조에 "리스크 가설 표" 섹션 신설. 변경 단위별 H-1~N 가설 도출(깨질 수 있는 계약 + 운영 영향 + 검증 계층 권고 + 시나리오 후보) 의무화. mams 메모리 12건 패턴이 흡수되도록 가설 도출 예시 3종 명시.
  - **어디에**: `opal/agents/opal-plan-agent/AGENT.md` (또는 `op-dev-plan/SKILL.md` 양식)
  - **왜**: 확정 방향 §1 — 가설 표가 TEST-SCENARIO의 입력
  - **AC**: PLAN.md 표준 양식에 "리스크 가설 표" 섹션 명시, 컬럼 6종 정의(ID/변경 단위/계약/영향/계층/시나리오), 가설 도출 예시 3종(Repository 반환 계약 변경 / 병렬 동시성 / NOT NULL FK) 포함

- [ ] **F-007** PM Gate 검증 룰 보강 — TEST-SCENARIO 단계 신설 검증 항목
  - **무엇을**: `opal-pilot-dev/SKILL.md` PM Gate 점검 목록 표에 TEST-SCENARIO Phase 행 추가. 검증 6항목: ① mock 0 (grep으로 시나리오 본문 `mock`/`Mock`/`patch` 부재 확인) ② 사전 조건 데이터 표 채워짐 ③ Given/When/Then 3필드 모두 채워짐 ④ 가설↔시나리오 매핑 완전 ⑤ L1/L2/L3 계층 명시 ⑥ L3 시나리오에 [SUPERVISOR] 마커 + PM 요청 양식 포함
  - **어디에**: `opal/skills/opal-pilot-dev/SKILL.md` "PM Gate 점검 목록" 섹션
  - **왜**: 확정 방향 §2 — 6대 강제 룰의 자동 검증
  - **AC**: PM Gate 점검 목록에 TEST-SCENARIO 행 추가, 6 검증 항목 명시

- [ ] **F-008** `opal-harness-semi-agentic.md` 모드 경계 표 갱신
  - **무엇을**: §3 모드 경계 표의 `opd` 행에서 "PLAN 사용자 확인 행 → EXECUTE 작업 행"을 "TEST-SCENARIO 사용자 확인 행 → EXECUTE 작업 행"으로 갱신. §8 차이 표에 TEST-SCENARIO 단계 행 추가.
  - **어디에**: `opal/core/references/opal-harness-semi-agentic.md`
  - **왜**: 확정 방향 §5 — 모드 경계가 PLAN 끝 → TEST-SCENARIO 끝으로 이동
  - **AC**: §3 표 `opd` 행 갱신됨, §8 차이 표에 "TEST-SCENARIO 완료" 행 추가(interactive=사용자 승인 / semi-agentic=사용자 승인 / agentic=PM 자율)

- [ ] **F-009** L3 사용자 협업 게이트 신설 + PM 사용자 요청 표준 양식
  - **무엇을**: `opal-pilot-dev/SKILL.md` STEP 5 TEST 단계에 "L3 시나리오 협업 게이트" 추가. opal-test-agent가 L3 시나리오 만나면 즉시 PM에 반환, PM이 표준 양식으로 캡틴 요청, 응답 수신 후 결과 기록. 표준 요청 양식 신설.
  - **어디에**: `opal/skills/opal-pilot-dev/SKILL.md` STEP 5 + `opal/agents/opal-test-agent/AGENT.md` 행동 규칙
  - **왜**: 확정 방향 §1 핵심 원칙 6 — [SUPERVISOR] 마커 → PM 표준 양식 요청
  - **AC**: opal-pilot-dev SKILL.md STEP 5에 "L3 협업 게이트" 섹션 신설, opal-test-agent AGENT.md에 L3 시나리오 처리 절차(즉시 PM 반환) 명시, PM 사용자 요청 표준 양식 코드 블록 존재(`캡틴, [시나리오 S-N]은 ...` 4행 형식)

- [ ] **F-010** 변경이력 행 추가 — 모든 변경 파일에 v업/일시(KST)/태스크 번호
  - **무엇을**: F-001~F-009로 수정된 모든 파일(SKILL.md, AGENT.md, references/*.md)의 변경이력 표에 신규 행 추가. 일시는 `node ~/.opal/tools/date/date.js datetime` 결과 사용. 태스크 번호 `(004)` 명시.
  - **어디에**: 변경 파일별 "## 변경이력" 표
  - **왜**: `.opal/AGENT.md` §업무 수행 지침 — "스킬·에이전트·참조 문서 수정 시 변경이력 표에 행을 추가한다 (일시 KST + 태스크 번호 포함)"
  - **AC**: 변경 파일별 변경이력 표 마지막 행에 `(004)` 태스크 번호 + 2026-05-15 일시 + 변경 요약이 기재됨

## 제약 조건

- **적용 범위 제한**: `opal-pilot-dev`(opd) 전용. opds/opp/opdw/opsdd 등 다른 pilot은 본 태스크 범위 외 (추후 별도 태스크)
- **하위 호환**: 기존 mams 진행 중 태스크(107)는 본 변경 적용 후 신규 태스크부터 적용. 기존 태스크 retroactive 갱신 없음
- **배포 경계**: `.opal/AGENT.md` 금지사항 §1 준수 — `~/.opal/` 배포 파일 직접 수정 금지. 모든 변경은 프로젝트 소스(`opal/skills/`, `opal/agents/`, `opal/core/references/`)에서 수행. 배포는 캡틴이 install-mac.sh로 별도 결정
- **하네스 변경 SSOT**: `opal/core/references/opal-harness*.md`만 수정. 다른 곳에서 발췌·복제 금지
- **변경이력 추적성**: 스킬·에이전트·참조 문서 수정 시 변경이력 표 행 추가 의무 (F-010)
- **사용자 승인 없는 코드 생성·수정 금지**: 산출물 문서(.md) 작성·분석은 허용. 본 태스크는 .md 변경만 대상이므로 EXECUTE 단계에서 워커 디스패치로 수행

## 기술 스택

- Markdown (모든 산출물 .md 파일)
- Bash (state-tool, date.js 호출)
- 변경 대상 파일 유형: SKILL.md, AGENT.md, references/*.md (코드 변경 없음)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | op-dev-test-scenario SKILL.md (현행) | `opal/skills/op-dev-test-scenario/SKILL.md` | F-001 변경 대상 — 통일 형식 + 시나리오 작성 체크리스트 갱신 |
| D-2 | 설계 | test-scenario-guide.md (현행) | `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | F-002 변경 대상 — 작성 프로세스 + 도구 매핑 + 시나리오 수 가이드 |
| D-3 | 설계 | opal-pilot-dev SKILL.md (현행) | `opal/skills/opal-pilot-dev/SKILL.md` | F-003·F-005·F-007·F-009 변경 대상 — 4단계 → 5단계 + STATE.md 행 + PM Gate + STEP 5 L3 게이트 |
| D-4 | 설계 | op-dev-execute SKILL.md (현행) | `opal/skills/op-dev-execute/SKILL.md` | F-004 변경 대상 — scenario_source input + 자가 점검 절차 |
| D-5 | 설계 | opal-plan-agent AGENT.md | `opal/agents/opal-plan-agent/AGENT.md` | F-006 변경 대상 — PLAN.md 리스크 가설 표 작성 의무 |
| D-6 | 설계 | opal-test-agent AGENT.md | `opal/agents/opal-test-agent/AGENT.md` | F-009 변경 대상 — L3 시나리오 즉시 PM 반환 절차 |
| D-7 | 설계 | opal-harness-semi-agentic.md | `opal/core/references/opal-harness-semi-agentic.md` | F-008 변경 대상 — §3 모드 경계 + §8 차이 표 |
| D-8 | 설계 | opal-harness.md | `opal/core/references/opal-harness.md` | §1 Guards 참조 — 본 변경이 Guards 우회 없음 확인 |
| D-9 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | 산출물 작성 시 인용 규칙 준수 |
| D-10 | 설계 | reporting-template.md | `opal/core/references/harness/reporting-template.md` | 단계별 보고 양식 |
| D-11 | 외부 | mams .opal/MEMORY.md | `/Volumes/Data/StoreLinkStudio/mams/.opal/MEMORY.md` | 회귀 12건 패턴 실증 근거 (feedback 12행 + 작업 히스토리 091/092/099/101/103/106) |
| D-12 | 외부 | mams 태스크 107 TASK.md | `/Volumes/Data/StoreLinkStudio/mams/tasks/107-260515-opds-pmax-crtv-lookup-fix/TASK.md` | 시나리오 양식 예시 케이스 — 가설 도출 + 데이터 설계 패턴 검증 |
| D-13 | 설계 | docs/PROJECT.md | `docs/PROJECT.md` | 프로젝트 원칙 — 표준화·재사용성·하네스 준수 |
| D-14 | 설계 | docs/CONVENTIONS.md | `docs/CONVENTIONS.md` | 변경이력 형식·@header·인용 규칙 |
| D-15 | 설계 | .opal/AGENT.md | `.opal/AGENT.md` | 프로젝트 PM 금지사항 — 배포 경계·변경이력·하네스 우회 금지 |
