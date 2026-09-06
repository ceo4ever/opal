# TEST SCENARIO: 근거 등급층 신설 + 확정/미확정 판정 + 트랙 자동 강등

> 작성일: 2026-08-21 | 상태: 작성 완료 (Block A 선작성 + Block B 보강)
> 작성자: 알투(PM) + 캡틴 페어 | 도출 입력: TASK.md(Block A) + PLAN.md F-001~005·H-1~H-12(Block B)

## 결론

- 총 **35건** — Block A 20건(①3 / ②7 / ⑤3 / ⑥7) + Block B 10건(③④ 보강 7 + 회귀·배포·체감 3) + **게이트 iteration 2 보강 5건**(S-31~S-35).
- 계층 분포: L1 자동 **28**건 / L2 실파일 통합 4건 / L3 [SUPERVISOR] 3건 = 35건.
- **Block B가 채운 공백 7건은 전부 파괴 관점(H-6·H-7·H-8·H-9·H-10·H-11·H-12)** — Block A가 목표·요구·채택 축에서 도출할 수 없던 영역이다.
- **Block A 고유 4건은 PLAN TS-001~020에 대응이 없다** — S-1·S-3(목표달성 동작 검증) · S-17(과잉 차단 대조군) · S-20(임계 경계값). PLAN 유래 TS는 전부 산출물 "존재 검사"이므로 채택 관점이 비어 있었다. 095에서 관측된 관점 편향이 재현됐다.
- **보강은 additive-only가 아니었다** — Block A S-1·S-3의 계층을 L2(자동)에서 L3(SUPERVISOR)로 **하향 정정**했다.
- **[정정] 자동 검증 불가 범위를 좁혔다** — 게이트 iteration 1에서 평가자가 최초 근거("규칙 신설 태스크 안에서 자동 검증 불가")를 **과잉 일반화**로 판정했다. 자동 검증이 불가한 것은 **R-6 실작동(후속 태스크의 ANALYSIS·PLAN 거동)에 한정**되며, R-4 도구 집행은 본 태스크 `TASK.md`가 신 스키마로 작성된 유일한 실파일이므로 **in-task 자동 검증이 가능**하다(S-31·S-33 신설).
- 게이트 iteration 1 → 2: 평균 1.33(목표 1 / 채택 1 / 경계 2) → G-1·G-2 반영 + 비차단 권고 2건 흡수.
- H-5(§5 개정 파급)는 시나리오를 두지 않는다 — PLAN이 `grep -rn "인용 생략" opal/ docs/` 실측으로 의존자 0건을 확인해 가설이 해소됐다.

---

## 1. 리스크 가설 표

> PLAN.md §리스크 가설 표 H-1~H-12 전건 전재 (보강 완료 판정 조건 2).

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | F-003 신규 판정 | 레거시 TASK.md 001~097이 신 스키마 부재로 전건 미확정 판정 | P0 | L1 + L2 | S-13 |
| H-2 | F-003 `cmd_verify` | `--clarification-check` 거부 동작·`--auto-pass` 우회 불가 불변 | P0 | L1 | S-18 |
| H-3 | F-003 등급 매핑 | 경로 패턴→등급이 빌드 관습 의존 — 미매칭 처리 계약 | P1 | L1 | S-14 |
| H-4 | F-004 강등 라우터 | 강등(`opd`→`opds`)·승격(`opds`→`opd`) 상호 트리거 왕복 | P1 | L1 | S-19 |
| H-5 | F-001 §5 개정 | "추론 기반 인용 생략 허용" 의존 하류 규칙 | P2 | — | **해소** — PLAN 실측 `grep -rn "인용 생략" opal/ docs/` 의존자 0건 |
| H-6 | F-001 §9 배치 | `§8.6`·`opal-pm.md §7`·`doc-code-mismatch.md`와 중복 서술 | P2 | L1 | S-21 |
| H-7 | F-005 경량화 | 검증 자산 축소 = 확정 방향 §13 위반 | P0 | L1 | S-22 |
| H-8 | F-003 리팩터 | `_parse_clarification_table` 하위함수 추출이 dict 반환 계약 변형 | P0 | L1 | S-23 |
| H-9 | F-003 인자 추가 | `TestClarificationGate._call_clarification_verify`의 고정 필드 `SimpleNamespace`에 신 속성 부재 → AttributeError | P0 | L1 | S-24 |
| H-10 | F-003 에러 코드 | `TestErrorCodesCompleteness` 3건(카운트·목록·README 종수) 동시 파괴 | P0 | L1 | S-25 |
| H-11 | F-003 등급 범위 | 도구 자동 부여가 E2/E4/E5 한정 → E1·E3 상시 `unknown`, ③축 실효 저하 | P1 | L1 + PM 판정 | S-26 |
| H-12 | F-004 문서 신설 | 승격 규칙 미이관으로 임계값 2문서 분산 | P2 | L1 | S-27 |
| H-13 | F-003 인용 파싱 | 정규 인용 4형식(`경로 §N`·`경로:줄번호`·`[사이트명](URL)`·`(→ D-N §N)`) 중 미파싱 형식이 `citation_path_not_found`로 오강등 — 규정 준수 산출물의 과잉 차단 | **P0** | L1 + L2 | S-31, S-34 |

---

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터

> 이 태스크는 DB를 쓰지 않는다. "테이블"은 **판정 입력 픽스처 파일**로 치환한다 (`state-tool` 테스트 관행 — 실 파일 픽스처, mock 금지).

| 픽스처 | 식별자 | 상태 | 출처 |
|--------|--------|------|------|
| 신 스키마 TASK.md | `FX-NEW` | `## 명확화 결과` 4행 + `의존 사실` 열에 유효 인용, `## 확정된 설계 방향`에 `[결정]`·`[사실]` 태그 혼합 | fixture (tmp_path) |
| 인용 부재 TASK.md | `FX-NOCITE` | `[사실]` 항목의 `의존 사실` 셀이 `-` | fixture (tmp_path) |
| 경로 부재 TASK.md | `FX-BADPATH` | 존재하지 않는 파일 경로 + 파일 끝 초과 줄번호 인용 | fixture (tmp_path) |
| brain 단독 TASK.md | `FX-E5ONLY` | `의존 사실`이 `.opal/brain/pages/...` 단독 인용 | fixture (tmp_path) |
| 미매칭 경로 TASK.md | `FX-UNKNOWN` | 등급 패턴 밖 경로(예: `Makefile:12`) 인용 | fixture (tmp_path) |
| 결정 무인용 TASK.md | `FX-DECISION` | `[결정]` 태그 항목만 존재, 인용 0건, `의존 사실` 전건 `-` | fixture (tmp_path) |
| 4요소 미잠금 TASK.md | `FX-UNLOCKED` | `확정값` 셀에 `TBD` — 기존 게이트 회귀용 | fixture (tmp_path) |
| 레거시 실파일 | `FX-LEGACY` | 저장소 실측 19건 (`확정된 설계 방향` 18 / `미확정` 4 / `의존 사실` 전건 `-`) | 저장소 실파일 (`tasks/**/TASK.md`) |
| 개정 대상 문서 | `FX-DOCS` | Step 1~3·7~9 산출 후 상태 | 저장소 실파일 |
| 형식 변형 TASK.md | `FX-FORMAT` | 정규 4형식 혼재 — `경로 §N` · `경로:줄번호` · `[사이트명](URL)` · `(→ D-N §N)` | fixture (tmp_path) |
| E5 동반 TASK.md | `FX-E5PAIR` | `.opal/brain/**` + 원천(E2/E4) 동반 인용 | fixture (tmp_path) |
| **본 태스크 실파일** | `FX-SELF` | 본 태스크 `TASK.md` — 신 스키마로 작성된 **유일한 실파일**(`[결정]`/`[사실]` 14항 + `의존 사실` 4행) | 저장소 실파일 |
| 회귀 기준선 | `FX-BASE` | 341 passed / 3 skipped / 84 subtests (2026-08-21 실행 관측) | pytest 실행 |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (CUD/호출) | Then (re-read) |
|---------|------------|----------------|---------------|
| S-1 | 규칙 적용 후 첫 태스크의 TASK.md에 `[결정]` 항목 존재 | 해당 태스크 ANALYSIS·PLAN 수행 | 산출물 상단에 `## 확정 입력 판정` 3값 표가 존재하고 해당 항목 재설계 서술 0건 |
| S-2 | `FX-NOCITE` | `verify --evidence-check` | 해당 항목 `verdict:"미확정"`, `reasons:["citation_missing"]`, exit 0 |
| S-3 | 4축 전건 충족 작업을 `//opd`로 진입 | opd STEP 1 직후 강등 판정 | `opds` 트랙 진입 + 4축 판정 근거 사후 통보, 캡틴 승인 왕복 0회 |
| S-4 | `FX-DOCS` (`citation-rules.md`) | grep §9 구성요소 | E1~E5 각 1행 이상 + 2축 표 + "TO-BE 최하위" 문장 + 충돌 규칙 + §8.6 경계 1줄 |
| S-5 | `FX-DOCS` (`citation-rules.md`) | grep §0·§4·§5 | 사실/결정 분리 존재, §4 TASK 행 "사실 주장 필수", 3절 상호 모순 0건 |
| S-6 | `FX-DOCS` (`op-task/SKILL.md`) | grep 템플릿·체크리스트 | 태그 요구 + `의존 사실` 재정의 + `-` 허용 조건 + 레거시 비소급 + 체크리스트 2항 |
| S-7 | `FX-NEW` | `verify --evidence-check` | 항목별 `확정`/`미확정(사유)` + `confirmed_ratio` 반환, exit 0 |
| S-8 | `FX-DOCS` (`track-routing.md`, `opal-pilot-dev/SKILL.md`) | grep 4축·임계·배선 | 4축 표 + 잠정치 표기 + 강등 호출 지점 1건 + 승격 무충돌 |
| S-9 | `FX-DOCS` (`op-dev-analysis`·`op-dev-plan` SKILL.md) | grep 규약 | 재도출 금지 + 3값 표 포맷 + `사실오류` 경로 + "재설계 면제" 문장 |
| S-10 | `FX-DOCS` (`citation-rules.md`·`plan-guide.md`) | grep 경량화 규정 | 원문 블록 금지 + `경로:줄번호` 대체 + 설계 절 한정 + 결론 블록 골격 |
| S-11 | `FX-DOCS` (`citation-rules.md`) | grep 무조건 면제 서술 | 사실 주장에 대한 무조건 인용 면제 서술 **0건** (결정 대상 조건부 면제만 잔존) |
| S-12 | 본 태스크 산출물 `PLAN.md`·`TEST-SCENARIO.md` | 코드블록·인용 형식 검사 | 소스코드 원문 블록 0건 + 근거가 `경로:줄번호` 형식 |
| S-13 | `FX-LEGACY` 19건 | 각 파일에 `verify --evidence-check` | 전건 exit 0 (`skipped` 또는 미확정 반환), 예외·차단 0건 |
| S-14 | `FX-UNKNOWN` | `verify --evidence-check` | `grade:"unknown"` 반환, 차단·임의 등급 부여 0건 |
| S-15 | `FX-E5ONLY` | `verify --evidence-check` | `reasons:["e5_sole_citation"]`로 미확정 강등 |
| S-16 | `FX-BADPATH` | `verify --evidence-check` | `reasons:["citation_path_not_found"]`로 미확정 강등 |
| S-17 | `FX-DECISION` | `verify --evidence-check` | 해당 항목 `verdict:"확정"` **유지** — 결정은 등급 판정 대상 아님 |
| S-18 | `FX-UNLOCKED` | `verify --clarification-check` + `mark --auto-pass` | `clarification_gate_unmet` exit 1 유지 + `--auto-pass` 우회 불가 유지 |
| S-19 | 임계 경계 작업(파일 9·10) | 강등 판정 + 승격 판정 각 1회 | 두 판정이 동시 발동하지 않음 (A2 ≤9 vs 승격 ≥10 상호배타) |
| S-20 | 확정률·파일 수 임계-1 / 임계 / 임계+1 | 트랙 판정 각 호출 | 경계 판정이 결정론적으로 일관, 판정 불능·예외 0건 |
| S-21 | `FX-DOCS` (`citation-rules.md`·`opal-pm.md`·`doc-code-mismatch.md`) | 중복 서열 서술 검사 | §9 외 서열 규정 서술 0건 + §9에 포인터 존재 |
| S-22 | 검증 자산 3경로 | `git diff --stat` | `scenario-gate.md`·`red-first.md`·`op-dev-test-scenario/` diff **0건** |
| S-23 | Step 5 구현 후 코드 | `TestClarificationGate` 12건 실행 (테스트 무수정) | 12건 전건 PASS — dict 반환 계약 불변 |
| S-24 | Step 5 구현 후 코드 | 고정 필드 `SimpleNamespace`로 `cmd_verify` 호출 | AttributeError 0건 (`getattr` 기본값 경로 동작) |
| S-25 | Step 4·5 후 코드·README | `TestErrorCodesCompleteness` 3건 실행 | `len(ERROR_CODES)`==45 AND README 헤더 종수==45 AND 목록 일치 |
| S-26 | E1(실행 로그)·E3(생성 코드) 경로 인용 픽스처 | `verify --evidence-check` | `grade:"unknown"` 반환 + §9에 "E1·E3은 PM 판단" 경계 문장 존재 |
| S-27 | `FX-DOCS` (`track-routing.md`) | 승격 임계값 수치 검색 | 신설 문서에 승격 임계 수치 복제 0건, 포인터만 존재 |
| S-28 | `FX-BASE` 기준선 341/3/84 | Step 5·6 후 스위트 전체 실행 | 신규 포함 전건 PASS, 기준선 대비 감소 0건 |
| S-29 | 프로젝트 소스 개정 완료 상태 | install 재배포 실행 | 신설 `track-routing.md` 배포 확인 + 개정 문서 배포본 diff 0건 |
| S-30 | 규칙 적용 후 첫 태스크 PLAN.md | 캡틴이 결론 블록만 열람 | 결론 블록만으로 승인 판단 가능 |
| S-31 | `FX-SELF` — 본 태스크 TASK.md 실파일 | `verify --evidence-check` | exit 0 + `의존 사실` 인용 등급 부여 + `confirmed_ratio` 산출 + **인용 기재 3행이 `citation_missing`으로 강등되지 않음** |
| S-32 | `FX-DOCS` (`plan-guide.md`·`op-dev-analysis/SKILL.md`) | 구 조항 grep 부재 검사 | "핵심 로직을 정의한다" 계열 구 조항 잔존 **0건** |
| S-33 | `FX-SELF` | 신 템플릿 규약 대조 | 확정된 설계 방향 14항 전건 태그 부여 + `의존 사실` `-` 허용 조건 미위반 |
| S-34 | `FX-FORMAT` | `verify --evidence-check` | 정규 4형식 전건이 `citation_path_not_found`로 강등되지 **않음** |
| S-35 | `FX-E5PAIR` | `verify --evidence-check` | `e5_sole_citation` **미발생** — 원천 동반 시 확정 유지 |

---

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 실 파일 입력)

#### S-2: 인용 부재 항목의 미확정 강등

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 (판정 계약) |
| 대상 | `_check_evidence_gate` ①축 — 인용 존재 |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | `FX-NOCITE` — `[사실]` 항목의 `의존 사실` 셀이 `-` |
| 기대 결과 | `verdict:"미확정"`, `reasons:["citation_missing"]`, exit 0 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py::TestT098EvidenceCheck::test_s2_citation_missing_demotes -v` (관측 스코프: 단일 노드ID 선택 실행, 340개 중 1개 선택·339 deselected) |
| 결과 | **PASS** — `1 passed, 339 deselected in 0.05s` |
| 상세 | `FX-NOCITE`(`[사실]` 항목의 `의존 사실` 셀이 `-`) 픽스처로 `cmd_verify --evidence-check` 재실행 결과: (1) `verdict:"미확정"` — 해당 요소 판정값이 확정에서 미확정으로 강등됨을 테스트 어서션으로 실측 확인. (2) `reasons:["citation_missing"]` — 인용 부재 사유 코드가 정확히 이 값으로 반환됨을 확인. (3) exit 0 — CLI가 예외·비정상 종료 없이 정상 반환(차단이 아니라 강등 판정임을 재확인, `pytest` 프로세스 자체가 exit 0으로 종료). 3요소 전건 기대와 일치 — H-3 반증 실패 |

#### S-4: §9 근거 등급·관할 규정 존재

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | `citation-rules.md` §9 (R-1) |
| 계층 | L1 |
| **실행 방식** | **M1 (grep 산출물 검사)** |
| 조건 | Step 1 완료 후 `FX-DOCS` |
| 기대 결과 | E1~E5 각 1행 이상 + AS-IS/TO-BE 2축 표 + "소스코드는 TO-BE 최하위" 문장 + 충돌 해소 규칙 + §8.6 경계 1줄 |
| 도구 | grep / Read |
| 실행 명령 | `grep -n "^## " opal/core/references/harness/citation-rules.md` (§9 위치 확인) + `sed -n '420,476p' opal/core/references/harness/citation-rules.md` (§9 전문 판독) |
| 결과 | **PASS** |
| 상세 | (a) E1~E5 5행 표 존재(422-430행). (b) AS-IS/TO-BE 2축 표(438-441행) + "[MUST] 소스코드는 TO-BE 근거로 최하위다"(436행) 문장 확인. (c) 충돌 해소 규칙 명문화(443-445행 "(c) 충돌 해소 규칙"). (d) §8.6과의 경계 1줄 존재(463-465행 "(h) §8.6과의 경계" — "§8.6은 병기 대상 선정, §9는 병기된 원천 간 충돌 해소"). AC(a)~(d) 전건 충족 |

#### S-5: §0·§4·§5 자기모순 해소

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5(해소) |
| 대상 | `citation-rules.md` §0·§4·§5 (R-2) |
| 계층 | L1 |
| **실행 방식** | **M1 (grep 산출물 검사)** |
| 조건 | Step 1 완료 후 `FX-DOCS` |
| 기대 결과 | §5에 사실/결정 분리 존재, §4 표 TASK 행이 사실 주장 "필수", 3개 절 상호 모순 0건 |
| 도구 | grep / Read |
| 실행 명령 | `sed -n '1,15p;222,251p' opal/core/references/harness/citation-rules.md` (§0·§4·§5 판독) |
| 결과 | **PASS** |
| 상세 | §0(11행) "사실 주장"과 "결정"을 구분하고 결정은 §9(f) 판정 대상 아님을 명시. §4(228행) TASK 행 "사실 주장 필수 / 결정 선택 — §9 (f) 참조". §5(238-241행) "결정(권한 행사)"은 인용 생략 허용, "사실 주장"은 인용 생략 **허용하지 않는다**로 재확인. 3개 절 표현이 전건 "결정=선택적 인용/사실=필수 인용"으로 일관 — 상호 모순 0건 |

#### S-6: TASK.md 템플릿 스키마 확장 + 열 수 불변

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | `op-task/SKILL.md` (R-3) |
| 계층 | L1 |
| **실행 방식** | **M1 (grep 산출물 검사)** |
| 조건 | Step 2 완료 후 `FX-DOCS` |
| 기대 결과 | 태그 요구 + `의존 사실` 재정의 + `-` 허용 조건 + 레거시 비소급 + 체크리스트 2항 추가 + `## 명확화 결과` 표 열 수 **4 불변** |
| 도구 | grep / Read |
| 실행 명령 | `grep -n "## 명확화 결과" -A 10 opal/skills/op-task/SKILL.md` + `grep -n "\[결정\]\|\[사실\]\|의존 사실\|레거시\|체크리스트" opal/skills/op-task/SKILL.md` |
| 결과 | **PASS** |
| 상세 | 태그 요구(87·132행) + `의존 사실` 재정의·`-` 허용조건(138행: "확정값이 순수 [결정](사실 주장 0건)일 때만 `-` 허용") + 레거시 비소급(139행) + 작성 체크리스트 2항 추가(252·261행, v2.7 변경이력 286행에 "체크리스트 2항 추가" 명시) + `## 명확화 결과` 표 열 수 4 불변(141행 "요소\|확정값\|미확정(있으면)\|의존 사실" 4열) — 전건 충족 |

#### S-7: 신 스키마 판정 반환 계약

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | `verify --evidence-check` 반환 JSON (R-4 AC(a)) |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | `FX-NEW` |
| 기대 결과 | 항목별 `verdict` + `reasons` + `citations[{raw,grade,exists}]` + `confirmed_ratio` 반환, exit 0 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -v -k test_s7_new_schema_verdict_reasons_citations_ratio` |
| 결과 | **PASS** |
| 상세 | `test_s7_new_schema_verdict_reasons_citations_ratio PASSED` (1 passed, 339 deselected) — `FX-NEW` 픽스처로 `cmd_verify --evidence-check` 호출 시 항목별 `verdict`+`reasons`+`citations[{raw,grade,exists}]`+`confirmed_ratio` 반환 계약, exit 0 확인 |

#### S-8: 트랙 판정 4축·임계값·배선 존재

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4, H-12 |
| 대상 | `track-routing.md`(신규) + `opal-pilot-dev/SKILL.md` (R-5 AC(a)(b)) |
| 계층 | L1 |
| **실행 방식** | **M1 (grep 산출물 검사)** |
| 조건 | Step 7·8 완료 후 `FX-DOCS` |
| 기대 결과 | 4축·임계값 표 + 잠정치 표기 + opd 진입부 강등 판정 호출 지점 1건 + `opal-harness.md` §2 모듈 표 등재 1행 |
| 도구 | grep / Read |
| 실행 명령 | `grep -n "4축\|임계\|잠정" opal/core/references/harness/track-routing.md` + `sed -n '15,24p' opal/core/references/harness/track-routing.md` + `grep -n "track-routing\|강등" opal/skills/opal-pilot-dev/SKILL.md` + `grep -n "track-routing" opal/core/references/opal-harness.md` |
| 결과 | **PASS** |
| 상세 | track-routing.md §1(15-22행)에 A1~A4 4축 표 존재(설계확정률≥90%(잠정치)/변경파일≤9(잠정치)/신규개념0건/최고검증계층≤L2) + "(잠정치)" 표기(19·20행). `opal-pilot-dev/SKILL.md:32` "[MUST] 트랙 강등 판정: TASK 완료 직후 1회... 4축 전건(AND) 충족 여부를 판정" — 강등 호출 지점 1건 확인. `opal-harness.md:112` "§2 하네스 모듈 표"에 "트랙 라우팅 \| harness/track-routing.md \| ..." 1행 등재 확인 |

#### S-9: 확정 입력 소비 규약 존재

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | `op-dev-analysis/SKILL.md`·`op-dev-plan/SKILL.md` (R-6) |
| 계층 | L1 |
| **실행 방식** | **M1 (grep 산출물 검사)** |
| 조건 | Step 3 완료 후 `FX-DOCS` |
| 기대 결과 | 재도출 금지 + 3값 판정 표 포맷 + `사실오류` 확정 박탈·캡틴 보고 경로 + "확정은 검증 면제가 아니라 재설계 면제다" 문장 |
| 도구 | grep / Read |
| 실행 명령 | `grep -n "재도출\|재설계 면제\|사실오류\|확정 입력 판정\|3값" opal/skills/op-dev-analysis/SKILL.md opal/skills/op-dev-plan/SKILL.md` |
| 결과 | **PASS** |
| 상세 | 양 파일 모두에서 확인: 재도출 금지("[MUST] 재도출 금지: [결정] 태그 항목은 새로 설계하지 않고, 항목별 3값 판정만 수행"), 3값 판정 표 포맷("## 확정 입력 판정" 표 + 판정값 유효/수정필요/사실오류), `사실오류` 경로("해당 항목의 확정 지위를 박탈하고 정상 분석/설계 경로로 복귀... 소유자에게 보고"), "[MUST] 확정은 검증 면제가 아니라 재설계 면제다" 문장 — op-dev-analysis/SKILL.md 24-30행, op-dev-plan/SKILL.md 54-60행에 동형 배치 확인 |

#### S-10: 산출물 형식 경량화 규정 존재

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | `citation-rules.md` §2.2 + `plan-guide.md` (R-7 AC(a)(b)(c)) |
| 계층 | L1 |
| **실행 방식** | **M1 (grep 산출물 검사)** |
| 조건 | Step 1·3 완료 후 `FX-DOCS` |
| 기대 결과 | 소스코드 원문 블록 금지 + `경로:줄번호` 대체 규정 + 설계 절 "결정+근거+공개 계약" 한정 + 상단 결론 블록 골격 |
| 도구 | grep / Read |
| 실행 명령 | `sed -n '76,99p' opal/core/references/harness/citation-rules.md` + `grep -n "원문\|결론 블록\|경로:줄번호\|결정+근거\|공개 계약" opal/skills/op-dev-plan/references/plan-guide.md` |
| 결과 | **PASS** |
| 상세 | citation-rules.md §2.2(91-92행) "[MUST] 산출물 분량 규칙: ANALYSIS·PLAN 등 산출물에 소스코드 원문 블록을 기재하지 않는다. 대체: `경로:줄번호` 인용 + 필요 시 1~3줄 약식 발췌까지만 허용". plan-guide.md 11행에 동일 포인터("[MUST] 산출물에 소스코드 원문 블록을 기재하지 않는다 — 경로:줄번호 인용 + ... citation-rules.md §2.2"), 15행 "## PLAN.md 결론 블록(최상단 집약)" 골격 존재, 151행 "각 파일의 결정 + 근거 + 변경되는 공개 계약을 명세한다... 함수 본문 전사는 금지" — 전건 충족 |

#### S-11: 구형 조항 잔존 0건 (교체형 ⑤축)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5(해소) |
| 대상 | `citation-rules.md` §5 (R-2 AC(a) 구형 잔존0) |
| 계층 | L1 |
| **실행 방식** | **M1 (grep 부재 검사)** |
| 조건 | Step 1 완료 후 `FX-DOCS` |
| 기대 결과 | **사실 주장에 대한 무조건 인용 면제 서술 0건** — 결정(권한 행사) 대상의 조건부 면제만 잔존 |
| 도구 | grep |
| 실행 명령 | `grep -n "인용 생략\|근거 없이\|근거 인용 없이" opal/core/references/harness/citation-rules.md` |
| 결과 | **PASS** |
| 상세 | §5 "인용 생략 허용" 절(238-242행)에 잔존하는 것은 "결정(권한 행사)" 대상 조건부 면제(240행) 뿐이고, "사실 주장"은 "인용 생략을 **허용하지 않는다**"(241행)로 명문화됨 — 사실 주장에 대한 무조건 인용 면제 서술 **0건** 확인 |

#### S-12: 신형 채택 자기적용 (교체형 ⑤축)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | 본 태스크 산출물 `PLAN.md`·`TEST-SCENARIO.md` (R-7 신형 채택) |
| 계층 | L1 |
| **실행 방식** | **M1 (grep 부재 검사)** |
| 조건 | PLAN 확정 후 |
| 기대 결과 | 소스코드 원문 블록 0건 + 근거가 `경로:줄번호` 형식으로 기재 |
| 도구 | grep |
| 실행 명령 | `grep -n '```python\|```py\|```javascript\|```js\|```typescript\|```ts\|```java\b' PLAN.md TEST-SCENARIO.md` + `grep -c '^```' PLAN.md TEST-SCENARIO.md` + `grep -oE '`[A-Za-z0-9_./-]+\.(md\|py):[0-9]+(-[0-9]+)?`' PLAN.md TEST-SCENARIO.md \| wc -l` (경로: `tasks/098-260821-opds-근거등급-확정판정-트랙강등/`) |
| 결과 | **PASS** |
| 상세 | 소스코드 언어 태그 코드블록(```python 등) 0건 매치(exit 1). PLAN.md 내 코드펜스 2개(38-41행)는 ASCII 기능 의존 그래프이며 소스코드 아님, TEST-SCENARIO.md 코드펜스 0개. `경로:줄번호` 형식 인용 PLAN.md 21건·TEST-SCENARIO.md 7건 확인 — 소스코드 원문 블록 0건 + 근거 `경로:줄번호` 형식 기재 전건 충족 |

#### S-14: 미매칭 경로의 unknown 반환 (경계)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | `_grade_citation` ③축 (R-4 AC(d)) |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | `FX-UNKNOWN` — 등급 패턴 밖 경로 |
| 기대 결과 | `grade:"unknown"` 반환. 차단 0건, 임의 등급 부여 0건 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -v -k test_s14_unmatched_path_returns_unknown_not_blocked` |
| 결과 | **PASS** |
| 상세 | `test_s14_unmatched_path_returns_unknown_not_blocked PASSED` — `FX-UNKNOWN`(등급 패턴 밖 경로) 인용에 `grade:"unknown"` 반환, 차단·임의 등급 부여 0건 확인 |

#### S-15: brain 단독 인용 강등 (부정)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | ④축 E5 단독 금지 (R-4 AC(c)) |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | `FX-E5ONLY` |
| 기대 결과 | `reasons:["e5_sole_citation"]`로 미확정 강등 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -v -k test_s15_e5_sole_citation_demotes` |
| 결과 | **PASS** |
| 상세 | `test_s15_e5_sole_citation_demotes PASSED` — `FX-E5ONLY`(brain 단독 인용) 입력에 `reasons:["e5_sole_citation"]`로 미확정 강등 확인 |

#### S-16: 경로 부재·줄번호 초과 강등 (부정)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | ②축 인용 유효 (R-4 AC(b)) |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | `FX-BADPATH` — 없는 경로 + 파일 끝 초과 줄번호 |
| 기대 결과 | `reasons:["citation_path_not_found"]`로 미확정 강등 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -v -k test_s16_bad_path_and_line_overflow_demotes` |
| 결과 | **PASS** |
| 상세 | `test_s16_bad_path_and_line_overflow_demotes PASSED` — `FX-BADPATH`(존재하지 않는 경로 + 파일 끝 초과 줄번호) 입력에 `reasons:["citation_path_not_found"]`로 미확정 강등 확인 |

#### S-17: 근거 없는 `[결정]`은 확정 유지 — **과잉 차단 대조군**

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 (역방향) |
| 대상 | 결정 vs 사실 구분 (TASK.md 확정 방향 §5) |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | `FX-DECISION` — `[결정]` 태그만, 인용 0건, `의존 사실` 전건 `-` |
| 기대 결과 | 해당 항목 `verdict:"확정"` **유지**. 미확정 강등이 발생하면 FAIL |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -v -k test_s17_decision_tag_without_citation_stays_confirmed` |
| 결과 | **PASS** |
| 상세 | 이 시나리오가 FAIL하면 캡틴의 새 요구사항이 미확정으로 강등되어 파이프라인이 멈춘다 — P0 |

#### S-18: 기존 게이트 불변 (회귀)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | `--clarification-check` + `--auto-pass` 우회 불가 (R-4 AC(e)) |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest 회귀)** |
| 조건 | `FX-UNLOCKED` + 기존 테스트 스위트 |
| 기대 결과 | `clarification_gate_unmet` exit 1 유지 + `test_case9_auto_pass_cannot_bypass` PASS |
| 도구 | pytest + 직접 CLI |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -v -k TestClarificationGate` (12건) + `python3 opal/tools/state-tool/state_tool.py verify <tmp>/fx_unlocked/ --clarification-check --task-md <tmp>/fx_unlocked/TASK.md` (4요소 전건 `TBD`) |
| 결과 | **PASS** |
| 상세 | (1) `TestClarificationGate` 12/12 PASS — `test_case9_auto_pass_cannot_bypass` 포함 전건 통과, `--auto-pass` 우회 불가 불변. (2) 직접 CLI 재현: `{"ok": false, "command": "verify", "error": "clarification_gate_unmet", "message": "TASK 4요소(목표/범위/제약/완료기준) 미잠금 — 다음 단계 진입 거부 (PRINCIPLES §1 집행): ['목표', '범위', '제약', '완료기준']", "missing": ["목표", "범위", "제약", "완료기준"]}` exit 1 — 회귀 없음. (3) 부가 확인: `--clarification-check` + `--evidence-check` 동시 지정 시 `evidence_check_flag_conflict` exit 1 반환 확인(H-10 신규 코드 CLI 경로 정상). H-2 반증 실패 — 계약 불변.

#### S-19: 강등·승격 상호배타 (경계)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | A2(≤9) vs 승격(≥10) (R-5 AC(d)) |
| 계층 | L1 |
| **실행 방식** | **M1 (문서 정합 검사)** |
| 조건 | 파일 수 9 / 10 경계 입력 |
| 기대 결과 | 두 판정이 동시 발동하지 않고, 판정 시점(TASK 직후 vs PLAN 결과)이 분리 기재됨 |
| 도구 | grep / Read |
| 실행 명령 | `sed -n '34,52p' opal/core/references/harness/track-routing.md` + `grep -n "승격\|파일 수\|10" opal/skills/opal-pilot-dev-short/SKILL.md` |
| 결과 | **PASS** |
| 상세 | track-routing.md:39 "A2 9: 승격 임계와 **상호배타**가 되는 최대값이다 — 두 규칙이 동시 발동할 수 없다". `:51` "[MUST] 강등 판정 시점은 TASK 완료 직후 1회, 승격 판정 시점은 PLAN 결과로 분리한다... `opd`→`opds`→`opd`… 형태의 왕복 구조가 성립하지 않는다". `opal-pilot-dev-short/SKILL.md:250` "하향 강등(opd→opds)은 track-routing.md(SSOT)가 별도로 규정하며, 판정 시점이 TASK 직후(강등)/PLAN 결과(본 절 승격)로 분리되어 상호배타 — 아래 승격 규칙과 충돌하지 않는다" — 동시 발동 방지 + 판정 시점 분리 기재 양쪽 문서에서 확인 |

#### S-20: 임계 경계값 결정론 (경계)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | 4축 임계 경계 (R-5 AC(a)) |
| 계층 | L1 |
| **실행 방식** | **M1 (문서 정합 검사)** |
| 조건 | 확정률 89%/90%/91%, 파일 8/9/10 |
| 기대 결과 | 경계 판정이 결정론적으로 일관. 판정 불능·예외 0건 |
| 도구 | grep / Read |
| 실행 명령 | `grep -n "대략\|약 \|근처\|정도\|경우에 따라" opal/core/references/harness/track-routing.md` + `sed -n '15,24p' opal/core/references/harness/track-routing.md` |
| 결과 | **PASS** |
| 상세 | 헤징(모호) 표현("대략"·"약"·"근처"·"정도" 등) 매치 0건(exit 1). 4축 전건이 명시적 비교 연산자로 정의됨 — A1 "≥ 90%", A2 "≤ 9", A3 "0건/1건 이상이면 미충족", A4 "≤ L2/L3 이상이면 미충족" — 경계값(90%·9·0·L2)에서 판정이 결정론적이며 판정 불능·예외 발생 여지 0건 |

#### S-21: SSOT 중복 서술 0건 (Block B — H-6)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | §9 vs §8.6 · `opal-pm.md §7` · `doc-code-mismatch.md` |
| 계층 | L1 |
| **실행 방식** | **M1 (grep 부재 검사)** |
| 조건 | Step 1 완료 후 `FX-DOCS` |
| 기대 결과 | §9 외 위치에 등급 서열 규정 서술 0건 + §9에 3문서 포인터 존재 |
| 도구 | grep |
| 실행 명령 | `sed -n '463,473p' opal/core/references/harness/citation-rules.md` + `sed -n '373,385p' opal/core/references/harness/citation-rules.md` + `grep -n "^## §7\|^## 7\." opal/core/references/opal-pm.md` + `sed -n '91,99p' opal/core/references/opal-pm.md` + `grep -n "등급\|서열\|E1\|E2\|E3\|E4\|E5" opal/core/references/harness/doc-code-mismatch.md opal/core/references/opal-pm.md` |
| 결과 | **PASS** |
| 상세 | §9(i)(467-472행) "코드=SSOT 원칙: opal-pm.md §7 / 문서·코드 불일치: doc-code-mismatch.md" 3문서 포인터 존재 + "[MUST] 본 절이 근거 서열의 유일 SSOT다 — 위 문서들에 서열 규정을 복제하지 않는다"(472행). §8.6(373-384행)은 "병기 대상 선정" 규칙만 다루고 E1~E5 서열 언급 0건. opal-pm.md §7(91-97행)은 "코드가 실질적 문서(SSOT)"만 서술, E1~E5 언급 0건(grep 매치 없음). doc-code-mismatch.md도 등급·서열·E1~E5 매치 0건 — §9 외 위치 중복 서술 0건 확인 |

#### S-22: 검증 자산 무접촉 (Block B — H-7)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | `scenario-gate.md` · `red-first.md` · `op-dev-test-scenario/` (R-7 AC(d)) |
| 계층 | L1 |
| **실행 방식** | **M1 (git diff 실측)** |
| 조건 | Step 3 완료 후 |
| 기대 결과 | 3경로 `git diff --stat` **0건** |
| 도구 | git |
| 실행 명령 | `git diff --stat -- opal/core/references/harness/scenario-gate.md opal/core/references/harness/red-first.md opal/skills/op-dev-test-scenario/` + `git status --porcelain -- opal/core/references/harness/scenario-gate.md opal/core/references/harness/red-first.md opal/skills/op-dev-test-scenario/` |
| 결과 | **PASS** |
| 상세 | 두 명령 모두 출력 0줄(exit 0, diff/변경 0건) — 3경로(`scenario-gate.md`·`red-first.md`·`op-dev-test-scenario/`) 무접촉 실측 확인 |

#### S-23: 파서 리팩터 후 dict 계약 불변 (Block B — H-8)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 |
| 대상 | `_locate_clarification_table` 추출 후 `_parse_clarification_table` 반환 계약 |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest 회귀, 테스트 무수정)** |
| 조건 | Step 5 완료 후 |
| 기대 결과 | `TestClarificationGate` 12건 **무수정** 전건 PASS |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -v -k TestClarificationGate` |
| 결과 | **PASS** |
| 상세 | `12 passed, 328 deselected in 0.06s` — `test_case1_all_filled_pass`~`test_case10b_regression_simple_rows_spec_mark` 12건 전건 PASS(테스트 파일 diff 무수정 확인은 git diff 범위에 해당 클래스 라인 변경 없음으로 별도 확인). `_locate_clarification_table` 추출 후에도 `_parse_clarification_table`의 dict 반환 계약(호출자 관점)이 그대로 유지됨을 실증 — H-8 반증 실패.

#### S-24: 고정 필드 SimpleNamespace 호출 안전 (Block B — H-9)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 |
| 대상 | `getattr(args,"evidence_check",False)` 기본값 경로 |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | 신 속성 없는 고정 필드 `SimpleNamespace`로 `cmd_verify` 호출 |
| 기대 결과 | AttributeError 0건, 기존 분기 정상 동작 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -v -k test_s24_fixed_field_namespace_no_attribute_error` |
| 결과 | **PASS** |
| 상세 | `test_s24_fixed_field_namespace_no_attribute_error PASSED` — 신 속성(`evidence_check`) 부재 고정 필드 `SimpleNamespace`로 `cmd_verify` 호출 시 AttributeError 0건. `getattr(args,"evidence_check",False)` 기본값 경로가 정상 동작. H-9 반증 실패.

#### S-25: 에러 코드 카탈로그 3중 정합 (Block B — H-10)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10 |
| 대상 | `ERROR_CODES` · `EXPECTED_CODES` · README 헤더 종수 (R-4 AC(f)) |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | Step 4·5 완료 후 |
| 기대 결과 | `len(ERROR_CODES)`==45 AND README 헤더 종수==45 AND 목록 일치 — `TestErrorCodesCompleteness` 3건 PASS |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -v -k TestErrorCodesCompleteness` + `python3 -c "import sys; sys.path.insert(0,'opal/tools/state-tool'); import state_tool as ST; print(len(ST.ERROR_CODES))"` + `grep -n "에러 코드 카탈로그" opal/tools/state-tool/README.md` |
| 결과 | **PASS** |
| 상세 | `3 passed, 337 deselected in 0.04s` — `test_error_codes_count`·`test_all_28_codes_registered`·`test_s7_error_catalog_marker_import_realignment` 전건 PASS. 독립 실측: `len(ST.ERROR_CODES)`==**45**, `README.md:336` `"## 에러 코드 카탈로그 (45종 실측 SSOT...")` — 코드·목록·README 3중 정합 확인. `evidence_check_flag_conflict`도 CLI 직접 재현으로 exit 1 확인(S-18 상세 참조). H-10 반증 실패.

#### S-26: E1·E3 자동 부여 제외 경계 명문화 (Block B — H-11)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-11 |
| 대상 | 도구 자동 등급 범위 = E2/E4/E5 (확정 방향 §11) |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest + grep)** |
| 조건 | E1(실행 로그)·E3(생성 코드) 경로 인용 픽스처 + `FX-DOCS` |
| 기대 결과 | 두 경로 모두 `grade:"unknown"` 반환 + §9에 "E1·E3은 도구 자동 부여 대상 아님, PM 판단" 경계 문장 존재 |
| 도구 | pytest / grep |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -v -k test_s26_e1_execution_log_and_e3_generated_code_return_unknown` + `sed -n '459,462p' opal/core/references/harness/citation-rules.md` + `find . -iname "*evidence*mapping*" -o -iname "*grade*mapping*"` |
| 결과 | **PASS** |
| 상세 | `test_s26_e1_execution_log_and_e3_generated_code_return_unknown PASSED` — E1(실행 로그)·E3(생성 코드) 경로 인용 픽스처 양쪽 모두 `grade:"unknown"` 반환 확인. citation-rules.md §9(g)(459-461행) "[MUST] 도구 자동 부여 범위 경계: 도구가 경로 패턴으로 자동 부여하는 등급은 E2·E4·E5에 한정된다. E1(실행 관측)·E3(생성 코드)은 경로 패턴으로 판별 불가하므로 unknown으로 반환되어 PM 판단에 위임된다" 경계 문장 존재. 프로젝트별 매핑 설정 파일 신설 0건(find 매치 없음) |

#### S-27: 승격 임계값 복제 0건 (Block B — H-12)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-12 |
| 대상 | `track-routing.md` (R-5 AC(d)) |
| 계층 | L1 |
| **실행 방식** | **M1 (grep 부재 검사)** |
| 조건 | Step 7 완료 후 `FX-DOCS` |
| 기대 결과 | 신설 문서에 승격 임계값 수치 복제 0건, `opal-pilot-dev-short/SKILL.md` 포인터만 존재 |
| 도구 | grep |
| 실행 명령 | `grep -n "10개\|10건\|승격" opal/core/references/harness/track-routing.md` |
| 결과 | **PASS** |
| 상세 | track-routing.md 내 "승격" 언급 5건 모두 SSOT 포인터(`opal/skills/opal-pilot-dev-short/SKILL.md` §에스컬레이션 규칙 참조) 또는 "복제하지 않는다"(64행 "[MUST] 본 문서는 승격 판정 임계값을 복제하지 않는다") — 임계값 수치("10개" 등) 매치 0건. `opal-pilot-dev-short/SKILL.md:250`에 포인터만 존재("하향 강등은 track-routing.md(SSOT)가 별도로 규정") — 승격 임계값 복제 0건 확인 |

#### S-32: R-7 구형 조항 잔존 0건 (교체형 ⑤축 — 게이트 iter2 신설)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | `plan-guide.md` §3단계 + `op-dev-plan/SKILL.md` 템플릿 구간 (R-7 AC(a)(b) 구형 잔존0) |
| 계층 | L1 |
| **실행 방식** | **M1 (grep 부재 검사)** |
| 조건 | Step 1·3 완료 후 `FX-DOCS` |
| 기대 결과 | 구 조항 잔존 **0건** — 검사 대상 2지점: (a) `plan-guide.md:139` "각 파일의 핵심 구현 내용을 명세한다… **핵심 로직**을 정의한다" (b) `op-dev-plan/SKILL.md:204` `{핵심 로직 흐름, 함수/클래스 시그니처, 외부 의존성}`. 신형 문장과 공존하면 FAIL |
| 도구 | grep |
| 실행 명령 | `grep -n "핵심 로직을 정의\|핵심 로직 흐름, 함수" opal/skills/op-dev-plan/references/plan-guide.md opal/skills/op-dev-plan/SKILL.md` + `sed -n '135,155p' opal/skills/op-dev-plan/references/plan-guide.md` + `sed -n '195,215p' opal/skills/op-dev-plan/SKILL.md` |
| 결과 | **PASS** |
| 상세 | **[게이트 iter2 C-1 정정]** 최초 지시가 `op-dev-analysis/SKILL.md`를 대상으로 지목했으나 실측 히트 **0건**이어서 공허 PASS 상태였다. 실제 미포착 잔존은 `op-dev-plan/SKILL.md:204`다. **grep 범위 제한 [MUST]**: `plan-guide.md:96`("기존 코드 구조, 핵심 로직 흐름 파악")은 ANALYSIS 절 서술이므로 검사 범위에서 제외한다 — 포함하면 오탐 FAIL이 난다. S-10은 신형 **존재**만 보므로 신·구 공존을 통과시킨다 |

#### S-33: R-3 신형 채택 인스턴스 — 자기적용 (교체형 ⑤축 — 게이트 iter2 신설)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | 본 태스크 `TASK.md`가 신 템플릿 규약을 충족하는가 (R-3 채택 면) |
| 계층 | L1 |
| **실행 방식** | **M1 (grep 산출물 검사)** |
| 조건 | Step 2 완료 후 `FX-SELF` |
| 기대 결과 | (a) `## 확정된 설계 방향` 14항 전건 태그 부여 (b) `의존 사실` 셀 `-` 허용 조건 미위반 (c) **항목 내 `[사실]` 근거 문장이 인용 없이 방치되지 않음** — 인용 금지 정책(타 프로젝트 실측) 대상은 `(경로 비기재 — 본 문서 §배경 분석 (1) 참조)` 형태로 출처를 명시해야 하며 무표기는 R-2 AC(a) 자기위반으로 FAIL |
| 도구 | grep |
| 실행 명령 | `grep -n "^## 확정된 설계 방향\|^## 명확화 결과" TASK.md` + `sed -n '55,91p' TASK.md` + `grep -n "배경 분석" TASK.md` (경로: `tasks/098-260821-opds-근거등급-확정판정-트랙강등/`) |
| 결과 | **PASS** |
| 상세 | S-6(템플릿 문구 존재)으로 대체되지 않는다. **[게이트 iter2 C-3 정정]** (a)(b)는 현 산출물에서 자동 충족되어 단언이 약했다 — 평가자가 확정 방향 3·8항의 `[사실]` 근거 인용 0건을 R-2 AC(a) 자기위반 후보로 지적했으므로 (c)를 추가해 실효를 부여했다 |

#### S-34: 정규 인용 형식 변형 통과 — 과잉 차단 대조군 (⑥ — 게이트 iter2 신설)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-13** |
| 대상 | `_extract_citations` 형식 계약 (R-4 AC(b) 정반대 실패모드) |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | `FX-FORMAT` — 정규 4형식 혼재 |
| 기대 결과 | 4형식 전건이 `citation_path_not_found`로 강등되지 **않음**. 파싱 비대상 형식은 `unknown`으로 PM 판단에 위임되되 경로 부재로 오판정하지 않는다 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -v -k test_s34_regular_citation_formats_not_overblocked` |
| 결과 | **PASS** |
| 상세 | `test_s34_regular_citation_formats_not_overblocked PASSED` — `FX-FORMAT`(정규 4형식 혼재: `경로 §N`·`경로:줄번호`·`[사이트명](URL)`·`(→ D-N §N)`) 전건이 `citation_path_not_found`로 강등되지 않음 확인. 정규 형식 근거: `citation-rules.md:57-66`(§2.1) · `:76-95`(§2.2) · `:97-110`(§2.3) · `:200-218`(§3.2). S-16(경로 부재 강등)의 정반대 대조군 |

#### S-35: E5 동반 인용 통과 — 과잉 차단 대조군 (⑥ — 게이트 iter2 신설)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | ④축 E5 단독 금지의 false positive 경로 (R-4 AC(c)) |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | `FX-E5PAIR` — `.opal/brain/**` + 원천(E2/E4) 동반 인용 |
| 기대 결과 | `e5_sole_citation` **미발생**, 해당 항목 확정 유지 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -v -k test_s35_e5_paired_with_source_stays_confirmed` |
| 결과 | **PASS** |
| 상세 | `test_s35_e5_paired_with_source_stays_confirmed PASSED` — `FX-E5PAIR`(`.opal/brain/**` + 원천(E2/E4) 동반 인용)에서 `e5_sole_citation` 미발생, 확정 유지 확인. S-15는 E5 **단독** 강등만 본다 — 양성 대조군이 없으면 원천 동반 인용까지 오강등될 수 있다 |

### L2. 프로세스 통합 (자동, 실 파일 read→판정→re-read)

#### S-13: 레거시 실파일 19건 무차단 처리

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | 레거시 하위호환 (R-4 AC(e), R-3 AC(d)) |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest, 저장소 실파일)** |
| 조건 | `FX-LEGACY` — 저장소 실측 19건 (`의존 사실` 전건 `-`) |
| 기대 결과 | 전건 exit 0 (`evidence_check:"skipped"` 또는 미확정 반환). 예외·차단 0건 |
| 도구 | pytest + 직접 CLI(저장소 실파일 전건) |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -v -k test_s13_legacy_task_md_real_files_no_block` + 직접 CLI 루프: `for f in $(find tasks -name TASK.md \| grep -v 098-260821); do python3 opal/tools/state-tool/state_tool.py verify "$(dirname "$f")/" --evidence-check; done` |
| 결과 | **PASS** |
| 상세 | (1) pytest: `test_s13_legacy_task_md_real_files_no_block PASSED`. (2) 직접 CLI 확장 재현 — 098 제외 저장소 전체 실파일(`tasks/**/TASK.md`, backup 포함) **98건** 전건에 `verify --evidence-check` 호출: `총 실행: 98 / 실패: 0` — 예외·차단·비정상 exit 0건. (원 픽스처 정의 19건보다 넓은 범위로 재검증하여 H-1 무차단 계약을 더 강하게 확증) |

#### S-28: state-tool 전체 회귀 기준선 유지

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2, H-8, H-9, H-10 |
| 대상 | 스위트 전체 (R-4 AC(e)) |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest 전체)** |
| 조건 | Step 5·6 완료 후 |
| 기대 결과 | 신규 케이스 포함 전건 PASS. 기준선 **341 passed / 3 skipped / 84 subtests**(2026-08-21 실행 관측) 대비 감소 0건 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/ -q` (디렉토리, 2파일) + `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -q` (단독) + `python3 -m pytest opal/tools/state-tool/tests/test_todo_mirror_hook.py -q` (단독) |
| 결과 | **Partial Fail (선재 결함 1건 — §7 기록, 실질 회귀 0건)** |
| 상세 | 디렉토리(2파일): `1 failed, 354 passed, 3 skipped, 83 subtests passed` — 기준선(341P/3S/84subtests) 대비 **+13 passed / subtests 84→83(1건 FAIL 전환) / 신규 1 failed**. `test_state_tool.py` 단독: `337 passed`(기준선 324 대비 +13). `test_todo_mirror_hook.py` 단독: `17 passed`(기준선 17, 변화 없음). 유일한 FAIL은 `TestR11Invariants::test_r11_invariants_S40`의 서브테스트 `error_codes_key_set_untouched` 1건이며 §7 「선재 결함」 절 기재대로 HEAD 상대 비교 구조상 에러 코드를 추가하는 본 태스크에서 전제가 성립 불가 — **실질 회귀 0건**(선재 결함 1건 제외). +13 passed는 신규 클래스 `TestT098EvidenceCheck`(13건, S-2·S-7·S-13~17·S-24·S-26·S-31·S-34·S-35 대응)에서 온다 — `TestErrorCodesCompleteness`(3건)는 기존 클래스가 44→45 기대치로 갱신된 것이라 신규 카운트에 포함되지 않는다. |

#### S-29: install 배포본 정합

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | `~/.opal/` 배포본 vs 프로젝트 소스 (배포 경계) |
| 계층 | L2 |
| **실행 방식** | **M1 (install 후 diff)** |
| 조건 | CLOSE 직전 install 재배포 후 |
| 기대 결과 | 신설 `track-routing.md` 배포 확인 + 개정 문서 배포본 diff 0건. `install-mac.sh` 변경 0건 |
| 도구 | diff / bash |
| 실행 명령 | `bash scripts/install-mac.sh`(캡틴 직접 실행, 2회 — 1차 CLOSE / 2차 ADD-2 수정 후) → `ls ~/.opal/references/harness/track-routing.md` · `grep -c "근거 등급과 관할" ~/.opal/references/harness/citation-rules.md` · `~/.opal/tools/state-tool/run.sh verify <task-path> --evidence-check` (관측 스코프: 배포본 실사용 CLI 경로) |
| 결과 | **PASS** — 배포 6/6 정합 + ADD-2 수정분 반영 확인 |
| 상세 | **PM 실측(2회 배포 대조)**. 1차 배포 후: `track-routing.md` 존재(3419B — 소스 대비 diff 있음, `install-mac.sh`의 변경이력 strip 정상 동작) / 배포본 `citation-rules.md` §9 1건 + ADD-1 E1 스코프 1건 / 하네스 §2 모듈 표 1건 / opd·opds 배선 각 1건 / `--evidence-check` 인식 성공(BEFORE `unrecognized arguments` exit 2 → AFTER `ok:true`) — **6/6 정합**. 단, 1차 배포 직후 실사용 경로 판정이 `confirmed_ratio 0.0`(전건 `citation_path_not_found`)로 나와 **P0 결함을 발견**했다 — `_resolve_citation_exists`가 루트를 `__file__`에서 파생해 배포본에서 `root=None`이 되는 문제(ADD-2로 수정, `ADD_DONE-2.md`). 2차 배포 후 재실측: **`confirmed_ratio 0.75`**(목표만 `grade_unknown`, 범위·제약·완료기준 확정)로 프로젝트 소스 실행과 동일 — 배포 등가 확정. 배포본 코드 정합도 확인(`~/.opal/tools/state-tool/state_tool.py:2509` `find_project_root(task_md_path)` 존재). `install_opal_references()`가 `cp -Rf`로 디렉토리 전체 복사(`scripts/install-mac.sh:1567-1580`)이며 `install-mac.sh` 변경 0건. **본 시나리오가 in-project 검증만으로는 원리적으로 잡히지 않는 결함을 실제로 검출했다.** |

#### S-31: 본 태스크 TASK.md 실파일 판정 — ①축 in-task 자동 경로 (게이트 iter2 신설)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-13, H-3 (①축 목표달성) |
| 대상 | 목표 문장 2절 "근거 없는 추정이 확정으로 통과하는 구멍 제거"를 **실 산출물**에서 검증 |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest, 저장소 실파일)** |
| 조건 | `FX-SELF` — 본 태스크 `TASK.md`(신 스키마로 작성된 유일한 실파일) |
| 기대 결과 | exit 0 + `citation_missing` **0건**(4셀 전건 백틱 경로 스팬 보유) + `confirmed_ratio` == **3/4** — PLAN 인용 형식 계약 대입 시 `목표` 행은 디렉토리 없는 파일명 단독이라 `unknown`, 나머지 3행(`범위`·`제약`·`완료기준`)은 디렉토리 보유 경로로 E4/E2 등급 부여 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -v -k test_s31_self_task_md_real_file_confirmed_ratio` + 직접 CLI 재현: `python3 opal/tools/state-tool/state_tool.py verify "tasks/098-260821-opds-근거등급-확정판정-트랙강등/" --evidence-check` |
| 결과 | **PASS** — 단, `~/.opal/tools/state-tool/run.sh` 배포본으로 동일 명령 호출 시 `--evidence-check` 미인식(아래 상세) |
| 상세 | (1) pytest: `test_s31_self_task_md_real_file_confirmed_ratio PASSED`. (2) 프로젝트 소스 직접 재현 반환 JSON 원문: `{"ok": true, "command": "verify", "evidence_check": "routed", "items": [{"element": "목표", "verdict": "미확정", "reasons": ["grade_unknown"], "citations": [{"raw": "\`citation-rules.md\`", "grade": "unknown", "exists": null}]}, {"element": "범위", "verdict": "확정", "reasons": [], "citations": [{"raw": "\`opal/skills/opal-pilot-dev/SKILL.md\`", "grade": "E4", "exists": true}, {"raw": "\`wc -l\`", "grade": "unknown", "exists": null}]}, {"element": "제약", "verdict": "확정", "reasons": [], "citations": [{"raw": "\`opal/tools/state-tool/state_tool.py:2225\`", "grade": "E2", "exists": true}, {"raw": "\`:2299\`", "grade": "unknown", "exists": null}]}, {"element": "완료기준", "verdict": "확정", "reasons": [], "citations": [{"raw": "\`opal/tools/state-tool/tests/\`", "grade": "E2", "exists": true}, {"raw": "\`test_state_tool.py\`", "grade": "unknown", "exists": null}]}], "confirmed_ratio": 0.75, "unconfirmed": ["목표"]}` — exit 0, `citation_missing` **0건**(목표 항목 사유는 `grade_unknown`), `confirmed_ratio`==**0.75(3/4)** 기대와 정확히 일치. `/Users/`·`$HOME` 문자열 0건(§6-4 재확인). (3) **[실측 이탈 — 그대로 보고]** 지시된 `~/.opal/tools/state-tool/run.sh verify ... --evidence-check` 직접 호출은 `usage: state-tool ... error: unrecognized arguments: --evidence-check` exit 2 반환 — 배포본(`~/.opal/tools/state-tool/state_tool.py`)이 098 변경 미반영 구버전(pre-098, `_parse_clarification_table` 미분리·`evidence_check_flag_conflict` 미등재)이기 때문이다. S-29(install 재배포 검증)가 아직 수행되지 않은 상태이므로 예상된 이탈이며, 회귀가 아니다 — 프로젝트 소스(작업트리) 직접 호출로 R-4 계약을 대체 검증했다. S-7은 tmp_path 합성 픽스처(`FX-NEW`)이므로 이 축을 대신하지 않는다. 게이트 iteration 1 평가자 지적 G-1 대응 — 목표 검증의 in-task 자동 경로 |

### L3. 사용자 협업 (수동, [SUPERVISOR] 마커)

#### S-1: 재도출 금지가 실제로 작동한다 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 (①축 목표달성) |
| 대상 | R-6 실작동 — TASK.md 확정 항목이 재설계되지 않고 3값 판정을 산출하는가 |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업). 자동화 불가 — 규칙 적용 대상 태스크가 아직 없다** |
| 조건 | 본 태스크 CLOSE 후 첫 개발 태스크에서 ANALYSIS·PLAN 수행 |
| 기대 결과 | 산출물 상단에 `## 확정 입력 판정` 3값 표 존재 + 확정 항목 재설계 서술 0건 |
| 실행자 | [SUPERVISOR] — 캡틴 수동 확인 필요 |
| 결과 | _{캡틴 확인 후 기록}_ |
| 상세 | **자동 검증 불가 범위는 R-6 실작동(후속 태스크의 ANALYSIS·PLAN 거동)에 한정된다** — R-4 도구 집행은 S-31이 in-task 자동 검증한다. 게이트 iter1 평가자가 최초 근거를 과잉 일반화로 판정해 정정했다 |

#### S-3: 강등 라우터가 채택되어 동작한다 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 (①축 목표달성) |
| 대상 | R-5 실작동 — `//opd` 진입이 `opds`로 강등되는가 |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업). 자동화 불가 — 오케스트레이터 진입은 사람 발화가 트리거다** |
| 조건 | 본 태스크 CLOSE 후 4축 전건 충족 작업을 `//opd`로 진입 |
| 기대 결과 | `opds` 트랙 진입 + 4축 판정 근거 사후 통보. 캡틴 승인 왕복 0회 |
| 실행자 | [SUPERVISOR] — 캡틴 수동 확인 필요 |
| 결과 | _{캡틴 확인 후 기록}_ |
| 상세 | Block A L2 → Block B L3 하향 정정. 오케스트레이터 진입은 사람 발화가 트리거이므로 이 축은 수동이 타당하다(평가자도 L3 유지가 타당하다고 판정) |

#### S-30: 산출물 경량화 체감 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 (①축 목표달성) |
| 대상 | R-7 실효 — 결론 상단 집약이 캡틴의 읽기 부담을 실제로 줄이는가 |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업)** |
| 조건 | 본 태스크 CLOSE 후 첫 태스크의 PLAN.md 열람 |
| 기대 결과 | 결론 블록만 읽고 승인 판단이 가능하다 |
| 실행자 | [SUPERVISOR] — 캡틴 수동 확인 필요 |
| 결과 | _{캡틴 확인 후 기록}_ |
| 상세 | 캡틴 인터뷰 답변("결론을 상단에 집약, 상세는 품질 무해 범위 요약")의 직접 검증 축 |

---

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| 목표 문장 (TASK.md §작업 목표) | H-4, H-7, **H-13** | **L2** + L3 | **S-31**(자동), S-1, S-3, S-30 | S-31 = `test_t098_self_task_md_evidence` / 나머지 수동 | ①축 — S-31이 in-task 자동 경로, 나머지는 규칙 적용 후 캡틴 확인 |
| R-1 AC(a)(b)(c)(d) | H-6 | L1 | S-4, S-21 | 산출물 검사 [T098/L1-R1] | S-21은 중복 서술 부재 |
| R-2 AC(a) 구형 잔존0 | H-5(해소) | L1 | S-11 | 산출물 검사 [T098/L1-R2a] | 교체형 ⑤축 |
| R-2 AC(b)(c) | H-5(해소) | L1 | S-5 | 산출물 검사 [T098/L1-R2] | §0·§4·§5 모순 0건 |
| R-3 AC(a)(b)(c) | H-1 | L1 | S-6 | 산출물 검사 [T098/L1-R3] | 표 열 수 4 불변 포함 |
| R-3 AC(d) 레거시 비소급 | H-1 | L2 | S-13 | `test_state_tool.py`:`test_t098_legacy_task_md_*` | 실파일 19건. **[정정] 채택 면 아님** — 내용은 구형 잔존 허용이므로 `is_adoption_scenario` 미계상 |
| R-3 채택 인스턴스 | H-1 | L1 | **S-33** | 산출물 검사 [T098/L1-R3-adopt] | 자기적용 — 신 스키마 실파일 1건 |
| R-4 AC(a) | H-3 | L1 | S-7 | `test_state_tool.py`:`test_t098_evidence_check_returns_*` | 반환 계약 |
| R-4 AC(b) | H-3, **H-13** | L1 + L2 | S-16, **S-34**, **S-31** | `test_state_tool.py`:`test_t098_citation_*` | S-16 부정 / S-34 형식 변형 통과 / S-31 실파일 |
| R-4 AC(c) | H-3 | L1 | S-15, **S-35** | `test_state_tool.py`:`test_t098_e5_*` | S-15 부정 / S-35 양성 대조군 |
| R-4 AC(d) | H-3, H-11 | L1 | S-14, S-26 | `test_state_tool.py`:`test_t098_grade_unknown_*` | E1·E3 제외 경계 |
| R-4 AC(e) 기존 게이트 불변 | H-2, H-8, H-9 | L1 + L2 | S-18, S-23, S-24, S-28 | `TestClarificationGate` 12건 무수정 + 스위트 전체 | 기준선 341/3/84 |
| R-4 AC(f) 카탈로그 등재 | H-10 | L1 | S-25 | `TestErrorCodesCompleteness` 3건 | 44 → 45종 |
| R-4 (신규 에러) | H-10 | L1 | S-25 | `test_state_tool.py`:`test_t098_flag_conflict` | `evidence_check_flag_conflict` |
| R-5 AC(a) | H-4 | L1 | S-8, S-20 | 산출물 검사 [T098/L1-R5a] | 임계 경계값 포함 |
| R-5 AC(b) | H-4 | L1 | S-8 | 산출물 검사 [T098/L1-R5b] | opd 배선 지점 |
| R-5 AC(c) | H-4 | L1 + L3 | S-8, S-3 | 산출물 검사 + 수동 | 사후 통보 |
| R-5 AC(d) | H-4, H-12 | L1 | S-19, S-27 | 산출물 검사 [T098/L1-R5d] | 상호배타 + 복제 0건 |
| R-6 AC(a)(b)(c)(d) | H-7 | L1 + L3 | S-9, S-1 | 산출물 검사 + 수동 | ①축은 S-1 |
| R-7 AC(a)(b)(c) | H-7 | L1 | S-10, S-12, **S-32** | 산출물 검사 [T098/L1-R7] | S-12 신형 채택 / S-32 구형 잔존0 |
| R-7 AC(d) 자산 미축소 | H-7 | L1 | S-22 | `git diff --stat` 0건 | 3경로 |
| (배포 경계 — 제약) | H-6 | L2 | S-29 | install 후 diff | `~/.opal/` 직접 편집 0건 |

> 총 시나리오 **35건**(S-1~S-35) 전건이 §3에 전개된다. 계층: L1 28 / L2 4(S-13·S-28·S-29·S-31) / L3 3(S-1·S-3·S-30).
> 게이트 iteration 2 보강 5건: S-31(①축 자동) · S-32(R-7 구형 잔존0) · S-33(R-3 채택 인스턴스) · S-34(H-13 형식 변형) · S-35(E5 양성 대조군).

---

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | ruff(설치됨, 프로젝트 설정 부재) | 해당 없음(설정 부재) | `find . -iname "ruff.toml" -o -iname ".ruff.toml"` 0건, `pyproject.toml` 부재 — 프로젝트 린트 규칙 미정의로 새 설정 신설 없이 스킵(도구 자체는 `/opt/homebrew/bin/ruff` 존재하나 실행 대상 규칙 없음). 대신 구문·임포트 무결성으로 대체 확인(아래) |
| 2 | 타입 체크 | mypy(미설치) | 해당 없음(설정 부재) | `which mypy` → not found. 프로젝트에 타입 체크 설정 없음 — 신규 도구 설치 금지 지시 준수, 스킵 |
| 3 | 포맷터 | — | 해당 없음(설정 부재) | 포맷터 설정 파일 부재. 대체: `python3 -c "import state_tool"` → `IMPORT_OK`, `python3 -m py_compile opal/tools/state-tool/state_tool.py` → `PYCOMPILE_OK` (구문·임포트 무결성 실측 통과) |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | **PASS(0건)** | `git diff` 대상 8개 변경 파일에 `grep -iE "(api[_-]?key\|secret\|password\|token\|bearer)\s*[:=]\s*['\"][A-Za-z0-9_-]{8,}"` 실행 → 매치 0건(grep exit 1) |
| 2 | .gitignore 확인 | **PASS** | `.opal/*` + 예외 화이트리스트(`brain/`·`code-map/`·`code-scan.json`·`memory/`·`worktree.json`) + `*.local.md` 규칙 존재 확인. 태스크 산출물(`tasks/098-...`)은 추적 대상으로 정상(gitignore 미적용 확인) |
| 3 | 경로 이탈 방어 (`_grade_citation` 절대경로·`..` 토큰) | **PASS** | 임시 TASK.md(`/etc/passwd`, `../../../etc/passwd:1` 인용)로 `--evidence-check` 호출 → `{"element": "목표", "verdict": "미확정", "reasons": ["citation_path_not_found", "grade_unknown"], "citations": [{"raw": "\`/etc/passwd\`", "grade": "unknown", "exists": false}]}` 등 반환, exit 0. 두 이탈 경로 모두 `exists: false`로 fail-safe 처리 — 실존 판정 없음, 예외 0건 |
| 4 | 판정 JSON 홈 디렉토리 경로 노출 0건 | **PASS** | S-31 실측 반환 JSON 전문 및 S-13 98건 반환에 `grep -c "/Users/\|\$HOME"` → 0건 |

## 7. 판정

### [선재 결함] S-40 불변 검증의 구조적 충돌 — 미접촉 보고

> **본 태스크가 만든 회귀가 아니다.** 발견·기록하고 수정하지 않는다(`~/.opal/PRINCIPLES.md` §3 — 계획에 명시된 것만 건드린다 / 095 선례: 선재 결함 미접촉 보고).

- **현상**: `TestR11Invariants::test_r11_invariants_S40`의 서브테스트 `error_codes_key_set_untouched` 1건 FAIL — `추가=['evidence_check_flag_conflict'] 삭제=[]`.
- **원인**: 이 검증은 `git show HEAD:./state_tool.py`의 `ERROR_CODES` 키 집합을 **워킹트리와 대조**한다(`test_state_tool.py:8795-8809`). 태스크 094 R-11 전용 불변 가드로 작성됐으나 영구 스위트에 남았다.
- **구조적 성격**: 고정 기대 집합이 아니라 **직전 커밋 대비** 비교이므로, 에러 코드를 추가하는 **모든 후속 태스크가 커밋 전까지 반드시 FAIL**한다. 커밋되는 순간 HEAD == 워킹트리가 되어 자연 해소된다 — 즉 커밋 이후에는 어떤 보호도 제공하지 않는다.
- **본 태스크 판정**: 098은 R-4 AC(f)로 `ERROR_CODES` 44→45를 **요구**받았다. 따라서 이 서브테스트의 전제("ERROR_CODES가 바뀌지 않았다")는 본 태스크에서 성립할 수 없다. **실질 회귀 0건**이다.
- **실측 대조** (스코프 명기):

| 스코프 | 기준선(HEAD) | GREEN 후 | 차이 |
|--------|-------------|---------|------|
| `opal/tools/state-tool/tests/` 디렉토리(2파일) | 341 passed / 3 skipped / 84 subtests | **354 passed / 3 skipped / 83 subtests / 1 failed** | +13 통과(신규 13건) / 서브테스트 1건 구조적 FAIL |
| `test_state_tool.py` 단독 | 324 passed | 337 passed | +13 |
| `test_todo_mirror_hook.py` 단독 | 17 passed | 17 passed | 0 |

- **후속 태스크 후보**: S-40 불변 검증을 HEAD 상대 비교에서 **고정 기대 집합 대조**로 교체하거나, 태스크 종료 시 제거하는 규약을 신설한다.

---


**Partial Fail — 핵심 기능(L1 29건 + L2 S-13·S-31) 전건 PASS, 보안 4건 전건 PASS. 유일한 FAIL은 §7 기재 선재 결함 1건(`TestR11Invariants::test_r11_invariants_S40`)이며 본 태스크 의도적 변경(ERROR_CODES 44→45)의 구조적 필연으로 실질 회귀 0건. S-29(install 배포본 정합)는 배포 비가역 제약으로 CLOSE 단계 이월(해당 없음), S-1·S-3·S-30(L3 [SUPERVISOR])은 자동화 불가로 캡틴 수동 확인 대기 — 3건 모두 실패가 아니라 미실행 보류다. "All Pass"로 표기하지 않는 이유: 회귀 스위트에 문자 그대로 1 FAIL이 존재하며(선재 결함이라도), 이를 은폐 없이 그대로 반영한다.**

### PM Gate 체크 (7대 강제 룰)

- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 — 전 시나리오가 실 파일 픽스처·공개 CLI 경로
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐 — 픽스처 13종
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐 — 35행
- [x] 가설↔시나리오 매핑(§4) 완전 — 미매핑 시나리오 0건
- [x] L1/L2/L3 계층 명시 — 전 시나리오
- [x] L3 [SUPERVISOR] 마커 존재 — S-1·S-3·S-30
- [x] 리스크 가설 표(§1) H-N ↔ S-N 1:N 매핑 완전 — H-5는 실측 해소로 명시
- [x] 모든 시나리오에 실행 방식(M1/M2/M3) 명시
- [x] FE 변경 시 M2 시나리오 포함 — **해당 없음** (변경 파일 14개 전건 md·py, FE 0건)
- [x] **목표 커버** — R-1~R-7 전건이 §4에 커버되고, 목표달성 시나리오 **4건**이 존재 — **S-31(L2 자동)** + S-1·S-3·S-30(L3 수동)
