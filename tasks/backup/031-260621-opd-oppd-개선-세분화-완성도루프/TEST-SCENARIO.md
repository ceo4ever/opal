# TEST-SCENARIO: oppd 개선 — 프로세스 + WBS 세분화 + 액션 완성도 루프

> 작성일: 2026-06-21 | 작성자: 알투(PM) | 입력: PLAN.md §리스크 가설 표, §3 TS 매핑
> 트랙: **문서 정합성 검증** (코드 런타임 없음) — RED-first 미적용 (근거: PLAN.md §0, TASK.md §제약)
> 검증 계층 재해석: **L1**=grep/섹션·표 존재, **L2**=교차 파일 수치/용어/포인터 일치, **L3**=의미 무모순 검토(PM)
> 실행 방식: **M1** (PM 또는 opal-test-agent가 grep/Bash 명령 실행 + 결과 대조). 모든 경로는 프로젝트 소스 `opal/...`

---

## 1. 가설 ↔ 시나리오 매핑

| 가설(PLAN) | 시나리오 | 계층 |
|-----------|---------|------|
| H-1 SSOT 삼중 기재 | S-026 | L2 |
| H-2 D-3 소스/배포본 역전 | S-020b | L2 |
| H-3 용어 일관성 | S-용어 | L2 |
| H-4 F-027 무모순 | S-027 | L3 |
| H-5 sizing 동시 교체 | S-010 | L2 |
| H-6 scope 짝 | S-023 | L2 |
| H-7 병렬 재서술 동시 | S-014 | L2 |
| H-8 승격 vs 비승격 | S-002, S-003 | L2 |
| H-10 변경이력 7파일 | S-changelog | L1 |
| H-11 재PLAN 명명 | S-naming | L3 |

> H-9(roadmap-guide 고아)는 범위 외(P2) — 시나리오 없음. PLAN §9 후속 후보로만 기록.

---

## 2. 시나리오 목록

### #1 프로세스 (F-001~F-003)

| S-ID | F | 계층 | Given / When / Then | 실행 명령 | 기대 |
|------|---|------|--------------------|----------|------|
| S-001 | F-001 | L1 | 개선된 SKILL.md Phase 1 / docs/ 직접 작성 지시 grep / 0건 | `grep -nE "docs/(PRD\|TRD)\.md" opal/skills/opal-pilot-project-dev/SKILL.md` (Phase 1 범위) | 직접 작성 지시 0건, 태스크 폴더 경로로 기술 |
| S-002 | F-002 | L2 | §1-3 / 승격 단계 grep / greenfield·델타·승격 매칭 | `grep -nE "승격\|greenfield\|델타" opal/skills/opal-pilot-project-dev/SKILL.md` | 승격 단계 존재 + 분기 기준 + 대상(PRD/TRD본문+PROJECT.md등록+ARCHITECTURE) 열거 |
| S-003 | F-003 | L2 | 문서 등록 프로토콜 표 / WBS.md 행 grep / 0건 | `grep -n "docs/WBS.md" opal/skills/opal-pilot-project-dev/SKILL.md`; wbs-guide §후속조치 WBS 등록 항목 부재 | 등록 프로토콜에 WBS 행 부재, WBS 경로=태스크 폴더 |

### #2 세분화 (F-010~F-018)

| S-ID | F | 계층 | Given / When / Then | 실행 명령 | 기대 |
|------|---|------|--------------------|----------|------|
| S-010 | F-010 | L2 | wbs-guide + SKILL / "1~3일" grep / 양쪽 0건 | `grep -rn "1~3일" opal/skills/opal-pilot-project-dev/SKILL.md opal/skills/opal-pilot-project-dev/references/wbs-guide.md` | 0건 + "단일 책임"·"수용 시나리오" 표현 존재 (동시 교체 H-5) |
| S-011 | F-011 | L1 | wbs-guide §분할 원칙 / 너무 큼·작음 grep | `grep -nE "너무 큼\|너무 작음\|재분할\|흡수" .../wbs-guide.md` | 너무 큼(2+책임/2+수용기준/시나리오 불가)·작음(헬퍼 단독) 신호+조치 |
| S-012 | F-012 | L2 | wbs-guide 액션 컬럼 / 수용 시나리오·용어계층 grep | `grep -nE "수용 시나리오\|완료 기준" .../wbs-guide.md` | "수용 시나리오"(상위) 컬럼/소절 + generic 금지 + TEST-SCENARIO 연결 + 완료기준=하위 계층 |
| S-013 | F-013 | L1 | wbs-guide §액션 구조 / 통합 타입 grep | `grep -nE "통합" .../wbs-guide.md` | 통합 액션 타입 + 작성 규칙(언제+통합 수용 시나리오) + "통합 액션≠병렬 그룹" 구분 |
| S-014 | F-014 | L2 | wbs-guide + parallel-guide / 병렬 인과 grep / 양쪽 | `grep -nE "세분화.*병렬\|파생\|충돌" .../wbs-guide.md .../parallel-execution-guide.md` | 두 파일 모두 "병렬=세분화 파생" 인과 서술 (동시 H-7) |
| S-015 | F-015 | L1 | wbs-guide §PM 검수 + SKILL §2-3 / 4종 항목 grep | `grep -nE "단일 책임\|수용 시나리오\|통합 액션\|너무 큼" .../wbs-guide.md` | F-010~F-013 대조 4종 추가 (양쪽 정합) |
| S-016 | F-016 | L1 | wbs-guide / §BE 액션 분할 기준 grep | `grep -n "BE 액션 분할" .../wbs-guide.md` | BE 원자 5종(모델·엔드포인트·서비스·연동·인증) 표 + 수용 시나리오 예 |
| S-017 | F-017 | L2 | wbs-guide §FE + opal-fe-agent / T0/T1/T2 grep / 양쪽 | `grep -nE "T0\|T1\|T2\|3계층\|컴포넌트 API" .../wbs-guide.md opal/agents/opal-fe-agent/AGENT.md` | wbs-guide FE 3계층 표+추출기준(UI킷+2+)+소규모예외 / opal-fe-agent T0/T1/T2+컴포넌트 API 계약 역할 |
| S-018 | F-018 | L1 | wbs-guide / §BE/FE 분할 매트릭스 grep | `grep -n "BE/FE 분할 매트릭스\|레이어 경계" .../wbs-guide.md` | 매트릭스 표 + 계약(API/컴포넌트 API) 기반 병렬/순차 규칙 |

### B7 루프 (F-020~F-027)

| S-ID | F | 계층 | Given / When / Then | 실행 명령 | 기대 |
|------|---|------|--------------------|----------|------|
| S-020 | F-020 | L1 | opal-task-action-agent / PLAN 재진입·루프 grep | `grep -nE "재진입\|재설계 루프\|status.*failed" opal/agents/opal-task-action-agent/AGENT.md` | PLAN 재진입 경로 명시 + 선형 즉시종료가 루프+상한으로 대체 |
| S-020b | F-020 | L2 | (R-1) 소스에 배포본 역전 블록 병합 / grep | `grep -nE "model: opus\|디스패치 모델" opal/agents/opal-task-action-agent/AGENT.md` | 배포본에만 있던 model:opus 블록·인라인이 소스에 병합됨 (H-2) |
| S-021 | F-021 | L2 | AGENT.md + verification-loop-guide / triage 3분류 grep / 양쪽 | `grep -nE "triage\|구현 수준\|설계 수준\|회귀" .../AGENT.md .../verification-loop-guide.md` | 동일 triage 3분류 표(성격·신호·라우팅) 양쪽 일관 (H-3) |
| S-022 | F-022 | L1 | AGENT.md / 1차분류+자동승격 grep | `grep -nE "1차 분류\|자동 승격\|한도 초과" .../AGENT.md` | 1차분류 + fix 한도초과 설계 자동승격 + verification_log 근거 기록 |
| S-023 | F-023/025 | L2 | AGENT.md + SKILL Phase3 / scope·3계층 grep / 양쪽 | `grep -nE "scope.*(action\|wbs\|trd)\|3계층\|액션-로컬" .../AGENT.md opal/skills/opal-pilot-project-dev/SKILL.md` | D-3 scope 반환 필드 + D-1 Phase3 scope별 처리 분기 (짝 H-6) + 에이전트 WBS/TRD 직접수정 금지 가드 |
| S-024 | F-024 | L2 | SKILL Phase3 + STATE 템플릿 / 2단 기준·루프로그 grep | `grep -nE "2단\|scope.*불변\|재설계 루프 로그\|TRD.*사용자" .../SKILL.md` | WBS 2단 기준 + TRD/PRD 사용자 게이트 + STATE.md 재설계 루프 로그 행 |
| S-026 | F-026 | L2 | opal-harness 표 + D-4/D-3 포인터 / 수치 단일 grep | `grep -nE "PLAN 재진입\|재설계 루프.*2" opal/core/references/opal-harness.md`; D-4 §7·D-3은 "참조"만 | 하네스 표에 PLAN 재진입 N=2 행 1개(SSOT) + D-4/D-3은 수치 없이 포인터만 (삼중기재 금지 H-1) |
| S-027 | F-027 | L3 | verification-loop-guide §3-5 / scope 분기 무모순 (PM 판독) | `grep -nE "설계 수준\|scope별\|0회.*trd" .../verification-loop-guide.md` + PM 의미 검토 | §3-5가 scope별 분기(action→재PLAN/wbs→PM/trd→0회)로 재서술, B7 3계층과 무모순 (H-4) |

### 공통 품질

| S-ID | 계층 | Given / When / Then | 실행 명령 | 기대 |
|------|------|--------------------|----------|------|
| S-changelog | L1 | 수정 7파일 / 변경이력 (031) 행 grep | `grep -rln "(031)" <수정된 7개 파일의 변경이력>` | 7개 파일 모두 변경이력에 (031) 행 (H-10) |
| S-naming | L3 | AGENT.md / "PLAN 재지시"(QA)와 "재설계 루프/재진입"(B7) 구분 (PM 판독) | `grep -nE "PLAN 재지시\|재설계 루프" .../AGENT.md` | 두 개념이 구분 명명되어 혼용 없음 (H-11) |
| S-용어 | L2 | 신규 용어 전반 / 영역 쌍 토큰 일치 | triage/scope/T0~T2/통합 액션/수용 시나리오 토큰을 관련 파일 쌍에서 grep | 동일 개념=동일 토큰 (영역 간 불일치 0) |

---

## 3. 코드 품질 / 보안 항목

| 항목 | 적용 | 검증 |
|------|------|------|
| 린트/타입/포맷 | N/A (Markdown 문서) | — |
| 시크릿 스캔 | N/A (시크릿·자격증명 미포함 문서) | 변경 파일에 키/토큰 패턴 부재 grep |
| .gitignore | N/A | — |
| 회귀 | **적용** | 기존 회귀: oppd 파이프라인 단계/Gate 서술 보존, state-tool 행 구성 불변, 기존 정상 참조(wbs-guide↔SKILL Read 지시) 유지 |
| 변경이력 의무 | **적용** | S-changelog (7파일 (031) 행) |
| 플랫폼 독립성 | **적용** | 신규 서술에 플랫폼 조건문 부재 grep (Claude/Cursor/Gemini/Codex 분기 없음) |

---

## 4. 실행 방식 요약

- 전 시나리오 **M1**(grep/Bash + 결과 대조). 외부 브라우저·E2E 없음 → L3b 해당 없음.
- TEST 단계에서 opal-test-agent가 위 실행 명령을 일괄 실행하고 PASS/FAIL 기록.
- L3(S-027/S-naming/S-용어)는 grep 보조 + PM 의미 무모순 판독 병행.

---

## 5. 테스트 실행 결과

> 실행일: 2026-06-21 | 실행자: opal-test-agent | 모드: 문서 정합성 (M1 grep/Bash)

### 시나리오별 결과

| S-ID | 판정 | 근거 요약 |
|------|------|---------|
| S-001 | PASS | SKILL.md Phase 1에서 docs/(PRD\|TRD).md 직접 작성 지시 0건. 모든 PRD/TRD 경로 언급은 "작업본→docs/ 승격" 문맥만 존재 |
| S-002 | PASS | SKILL.md §1-3에 greenfield/델타 승격 분기 표 존재 (L246~L257). PRD/TRD 본문+PROJECT.md 등록+ARCHITECTURE.md delta 대상 열거 확인 |
| S-003 | PASS | `grep -n "docs/WBS.md"` 0건. SKILL.md §2-5, §문서 등록 프로토콜 모두 "태스크 폴더 전용" 명시, 등록 표에 WBS.md 행 부재 |
| S-010 | PASS | wbs-guide.md·SKILL.md 양쪽 "1~3일" 0건 (변경이력 내 F-010 언급 제외). "단일 책임"·"수용 시나리오" 표현 양쪽 다수 존재 |
| S-011 | PASS | wbs-guide.md에 "너무 큼 신호 → 재분할"(L26~L29), "너무 작음 신호 → 흡수"(L31~L32), BE원자 표 너무 큼/작음 컬럼 존재 |
| S-012 | PASS | wbs-guide.md §수용 시나리오 용어 계층(L39~L46): 수용 시나리오(상위)/완료 기준·검증 명령(하위) 계층 정의 + generic 금지 + TEST-SCENARIO 연결 명시 |
| S-013 | PASS | wbs-guide.md L62~L66: 통합 타입 표 존재. 언제 두는가 + 통합 수용 시나리오 필수 + "통합 액션은 별도 채번 대상이며, 병렬은 실행 방식이다" 구분 명시 |
| S-014 | PASS | wbs-guide.md L22·L215: "병렬은 세분화의 산출/파생 효과" + "세분화↑→충돌↓→병렬↑". parallel-guide.md L12: 동일 인과 서술. 양쪽 일치 |
| S-015 | PASS | wbs-guide.md PM 검수 체크리스트(L263~L266): 단일 책임/구체 수용 시나리오/통합 액션/너무 큼·작음 4종 체크 항목 존재 |
| S-016 | PASS | wbs-guide.md §BE 액션 분할 기준(L274~L287): 모델·엔드포인트·도메인 서비스·외부연동·인증 원자 5종 표 + 수용 시나리오 예 포함 |
| S-017 | PASS | wbs-guide.md §FE 액션 분할 기준(L293~L303): T0/T1/T2 3계층 표 + UI킷 우선 + 소규모 예외. opal-fe-agent AGENT.md L31~L47: T0/T1/T2 절 + 컴포넌트 API 계약 역할 양쪽 일치 |
| S-018 | PASS | wbs-guide.md §BE/FE 분할 매트릭스(L307~L318): 레이어 경계=액션 경계, API 계약(BE)/컴포넌트 API 계약(FE), 병렬/순차 조건, 통합 액션 필수 표 존재 |
| S-020 | PASS | action-agent AGENT.md: §실행 프로세스(L33): "재설계 루프 파이프라인" 명명. L53~L57: VERIFY 재설계 루프·3계층 라우팅. 선형 즉시종료→루프+상한 대체 확인 |
| S-020b | PASS | action-agent AGENT.md에서 "model: opus" 0건. 레벨명(advanced/standard/light)만 사용, 하네스 §6 모델 매핑 포인터 준수 |
| S-021 | PASS | action-agent AGENT.md L125~L133: triage 3분류 표(구현 수준/설계 수준/회귀). verification-loop-guide.md L85~L93: 동일 3분류 표(성격·신호·라우팅). 양쪽 일관 |
| S-022 | PASS | action-agent AGENT.md L125: "VERIFY 실패 triage (1차분류)" 명시. L135: "자동승격" 명시(fix 한도 초과→설계 수준 자동 승격). `verification_log`에 근거 기록 명시 |
| S-023 | PASS | action-agent L152~L154: scope action/wbs/trd 3계층 라우팅 표. SKILL.md §3-1 L435~L454: scope별 처리 분기 + WBS 2단 기준 + TRD/PRD 사용자 게이트. WBS/TRD 직접 수정 금지 가드(L262, L8) 양쪽 존재 |
| S-024 | PASS | SKILL.md L440~L444: WBS 2단 기준(scope·인터페이스 불변 조정=PM 자율/scope·기능 변경=사용자). L448: TRD/PRD 사용자 게이트 [MUST]. STATE.md 템플릿(L616): 재설계 루프 로그 섹션 존재 |
| S-026 | PASS | harness.md L56: "PLAN 재진입(재설계 루프) \| 2회 \| scope별 에스컬레이션" 행 1개(SSOT). action-agent·verification-loop-guide 양쪽 수치(2회) 미복제, "harness §1 참조"(포인터)만 존재. 삼중 기재 없음 |
| S-027 | PASS(L3) | verification-loop-guide §3-5 scope별 분기(L316~L322): action=재설계 루프[harness 상한], wbs=PM 에스컬레이션, trd=즉시 사용자 에스컬레이션(0회). L324 [MUST] "0회 즉시 에스컬레이션은 trd에만 적용" 명시. B7 3계층(harness §1 SSOT)과 의미 무모순 확인 |
| S-changelog | PASS | 7개 changed_files 전부 변경이력에 "(031)" 행 존재 확인 (grep -rln 결과 7/7) |
| S-naming | PASS(L3) | action-agent L65: "PLAN 재지시(QA 피드백 기반)"(2단계) vs "재설계 루프(PLAN 재진입)"(5단계) 구분 명명 박스 명시. "발동 조건이 다르므로 혼용하지 않는다" 명시. 혼용 0건 |
| S-용어 | PASS | triage(양쪽 존재), scope(3개 파일 일치), T0/T1/T2(wbs-guide·fe-agent 양쪽), 통합 액션(wbs-guide·SKILL 양쪽), 수용 시나리오(wbs-guide·SKILL 양쪽). 동일 개념=동일 토큰, 영역 간 불일치 0건 |

### 코드 품질 / 보안 결과

| 항목 | 결과 | 근거 |
|------|------|------|
| 시크릿 스캔 | PASS | 변경 7파일에 sk-/Bearer/password 패턴 0건 |
| 플랫폼 독립성 | PASS | Claude/Cursor/Gemini/Codex 분기 조건문 0건 |
| 회귀 | PASS | oppd Phase 1~3 파이프라인 서술 보존, state-tool 행 구성 불변, wbs-guide↔SKILL Read 지시 유지 |
| 변경이력 의무 | PASS | 7파일 모두 (031) 행 존재 (S-changelog 동일) |

### 최종 판정

**All Pass** — 전체 23개 시나리오 PASS (FAIL 0건, SKIP 0건)

---

## 변경이력

| 날짜 | 변경내용 |
|------|---------|
| 2026-06-21 | 초기 작성 — oppd 3축 개선 문서 정합성 검증 시나리오 (S-001~S-027 + 공통품질), H-1~H-11 매핑 (031) |
| 2026-06-21 | §5 테스트 실행 결과 기록 — S-001~S-027 + 공통품질 전체 PASS, All Pass 판정 (031) |
