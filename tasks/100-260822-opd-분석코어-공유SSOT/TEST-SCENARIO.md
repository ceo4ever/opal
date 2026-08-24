# TEST SCENARIO: ANALYSIS 분석 코어 공유 SSOT 신설

> 작성일: 2026-08-23 | 상태: 작성 완료
> 작성자: 알투(PM) + 캡틴 페어 | PLAN.md 가설 표 기반 (작성자 ≠ PLAN 워커 — self-confirming 방지)

## 0. 트랙 판정 (RED-first)

| 변경 영역 | 트랙 | 근거 |
|-----------|------|------|
| F-007 `opal/tools/state-tool/state_tool.py` — evidence-check 반환 계약 확장 | **RED-first 강제** | `opal/core/references/harness/red-first.md:29` — "API 계약"은 self-confirming 위험군. S-20~S-26이 RED 대상이며 Tier4a에서 선작성한다 |
| F-001~F-006, F-008 — 규범 문서 개정 | 구현 후 검증 | 동 문서 `:35` — "설정·문서"는 구현 후 시나리오 검증 허용 |

> 공통 불변 3항 유지: ① 테스트 코드 산출물 ② 작성자≠구현자 ③ TEST 단계 검증.
> **도출 입력 2계열**: Block A(채택 관점 — TASK.md 목표·R-1~R-12·교체형 잔존/채택 기준)를 먼저 도출하고, Block B(파괴 관점 — PLAN.md H-1~H-14·F-001~F-008)로 보강했다.

---

## 1. 리스크 가설 표

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | F-007 / `state_tool.py` | 표 전용 파서를 불릿 섹션에 재사용 → 파싱 실패 | P1 | L1 | S-20 |
| H-2 | F-007 / `confirmed_ratio` | 분모 확대로 기존 "4요소" 전제 소비자 파괴 | P1 | L1 | S-21 |
| H-3 | 범위 / opp·oppd 경로 | 배제가 결정으로 기록되지 않아 누락으로 오인 | P2 | L3 | S-31 |
| H-4 | F-005 / 거울 사본 | `qa-dev-guide.md`와 `op-dev-qa/SKILL.md` 분리 갱신 → 즉시 drift | P1 | L1 | S-15 |
| H-5 | F-001 / 하네스 모듈 표 | 「해당 §」 열 미대응 → 표 계약 위반 | P2 | L1 | S-2 |
| H-6 | F-007 / 배포 경계 | 소스 GREEN을 런타임 반영으로 오인 | P1 | L3 | S-32 |
| H-7 | F-004 / Q표 배치 | 산문 배치 시 준수율 0% — 형식만 통과 | P1 | L1+L3 | S-8, S-30 |
| H-8 | F-008 / 재생성 대조 | 재생성본 서술을 그대로 신뢰 → 환각 승계 | P2 | L3 | S-30 |
| H-9 | F-007 / `README.md` | 신규 키 추가 후 계약 문서 stale | P1 | L2 | S-27 |
| H-10 | F-002 / 이관 절차 | 원본 삭제 누락 → 중복이 오히려 +1 | P0 | L1 | S-4 |
| H-11 | F-001 / `opal-harness.md` | 최상위 절 재배치 → 타 문서 `§N` 인용 전건 파손 | P0 | L1 | S-3 |
| H-12 | 문서 / `docs/ARCHITECTURE.md` | 동일 수치 2곳 중 한쪽만 갱신 | P2 | L2 | S-28 |
| H-13 | F-002 / R-2 판정식 | 판정 스코프가 신설 SSOT를 제외 → 위양성 Pass | P0 | L1 | S-5 |
| H-14 | Phase 2 병렬 | 워커별 앵커명 추측 → 포인터 불일치 | P0 | L1 | S-1 |

---

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터

| 테이블 | 식별자 | 상태 | 출처 |
|--------|--------|------|------|
| 규범 문서 집합 | `opal/core/references/harness/**` · `opal/skills/op-dev-{analysis,plan,qa}/**` · `opal/skills/opal-pilot-dev/**` | EXECUTE 개정 전 상태를 git working tree 기준으로 확보 | 리포지토리 현행 파일(fixture 불요) |
| 파서 픽스처 A | `## 확정된 설계 방향` 불릿 6행 + `## 명확화 결과` 표 4행을 가진 TASK.md | 신규 생성 | pytest tmp_path 실 파일(mock 금지) |
| 파서 픽스처 B | `## 확정된 설계 방향` 섹션이 **없는** 레거시 TASK.md | 신규 생성 | pytest tmp_path 실 파일 |
| 파서 픽스처 C | `## 확정된 설계 방향` 항목 **0건**(헤딩만) TASK.md | 신규 생성 | pytest tmp_path 실 파일 |
| 실 태스크 폴더 | `tasks/100-260822-opd-분석코어-공유SSOT/` | 현행 | 본 태스크 산출물 |
| baseline 산출물 | `tasks/100-260822-opd-분석코어-공유SSOT/ANALYSIS.baseline.md` | 2026-08-23 고정(331줄) | PM 스냅샷 |
| 재생성 산출물 | `tasks/100-260822-opd-분석코어-공유SSOT/ANALYSIS-REGEN.md` | TEST 단계에서 생성 | 표준 opd STEP 2 디스패치 |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (CUD/호출) | Then (re-read) |
|---------|------------|----------------|---------------|
| S-1 | 개정 후 `analysis-core.md` | 앵커 목록 추출 | Tier2 산출물의 `§N` 인용이 앵커 목록에 100% 포함 |
| S-2 | 개정 후 `opal-harness.md` | §2 모듈 표 파싱 | 신규 행 1개 + 4열 전부 비어있지 않음 |
| S-3 | 개정 전/후 `opal-harness.md` | 최상위 `## §N` 헤딩 목록 비교 | 기존 §1~§10 번호·제목 불변 |
| S-4 | 개정 후 `analysis-guide.md` | 체크리스트 섹션 grep | 원본 항목 부재 + `analysis-core.md` 포인터 존재 |
| S-5 | 개정 후 4파일 + `analysis-core.md` | 정규화 중복 계수(스코프 5파일) | 2회 이상 출현 문장 0건 |
| S-6 | 개정 후 `tech-context-guide.md` | 미등록 MCP명 정규식 매치 | 0건 |
| S-7 | 개정 후 `tech-context-guide.md` | 등록본 조회 규칙 문장 grep | 1건 이상 |
| S-8 | 개정 후 `op-dev-analysis/SKILL.md` | §6 템플릿 필드 파싱 | SSOT 경로 + 델타 2필드 구조 |
| S-9 | 개정 후 `op-dev-analysis/SKILL.md` | Q표 섹션 헤딩 grep | 템플릿 실물 섹션 존재 + "권장" 표기 |
| S-10 | 개정 후 `opal-pilot-dev/SKILL.md` | STEP 2 프롬프트 슬롯 grep | 질문 주입 슬롯 1개 |
| S-11 | 개정 후 `op-dev-analysis/SKILL.md` | 핸드오프 표 골격 파싱 | `항목\|확정값\|근거` 3열 |
| S-12 | 개정 후 `analysis-core.md` | 원문 덤프 금지 문장 grep | 포인터 형태로 존재(원문 복제 아님) |
| S-13 | 개정 후 `qa-dev-guide.md` | R축 행 계수 | 코드펜스 검증 행 1개 추가 |
| S-14 | 개정 후 `qa-dev-guide.md` | R축 행 계수 | 확정 입력·근거 등급 검증 행 추가 |
| S-15 | 개정 후 `qa-dev-guide.md` + `op-dev-qa/SKILL.md` | R/P 번호 범위 대조 | 두 파일의 번호 범위 일치 |
| S-16 | 개정 후 `pipeline.json` | `spec-validate` 실행 | exit 0 + checklist 4항목 |
| S-17 | 개정 후 `plan-guide.md` | `analysis-core.md` Read 지시 grep | 1건 이상 |
| S-18 | 개정 전/후 `plan-guide.md` | 2단계 절차 문단 수 계수 | 감소 + 감소분마다 포인터 대응 |
| S-19 | 개정 후 `plan-guide.md` | 2.N.1·2.N.3 승계 지시 grep | `[MUST] 재도출 금지` 문장 존재 |
| S-20 | 픽스처 A | `verify --evidence-check` | `items[]`에 `source=direction` 항목 존재 |
| S-21 | 픽스처 A | 동일 호출 | `confirmed_ratio` 분모가 명확화 결과 4요소로 불변 |
| S-22 | 픽스처 A | 동일 호출 | `direction_confirmed_ratio` 키 존재 |
| S-23 | 픽스처 A·B·C | 동일 호출 | 전 경로 exit 0 |
| S-24 | 픽스처 B | 동일 호출 | graceful skip — 기존 반환 형태 유지 |
| S-25 | 픽스처 A | `--evidence-check --clarification-check` | `evidence_check_flag_conflict` exit 1 |
| S-26 | 픽스처 C | `verify --evidence-check` | 분모 0 나눗셈 없음, 예외 미발생 |
| S-27 | 개정 후 `state_tool.py` + `README.md` | 신규 키 문자열 대조 | 코드 키와 문서 키 일치 |
| S-28 | 개정 후 `docs/ARCHITECTURE.md` | 동일 수치 2곳 grep | 두 값 일치 |
| S-29 | 실 태스크 폴더 | `verify --evidence-check` 실행 | 두 source 항목 혼재 반환, exit 0 |
| S-30 | baseline + 재생성본 | AC-G1~G4 판정 명령 실행 | 대조 결과 기록 + PM 직접 Read 교차검증 |
| S-31 | 개정 후 TASK.md | 배제 결정 문장 확인 | opp·oppd 배제가 명시적 결정으로 기록 |
| S-32 | 개정 후 `state_tool.py` + 배포본 | 소스/배포본 차이 확인 | 미반영이 정상임을 캡틴이 확인 |
| S-33 | 개정 후 `plan-guide.md` + ANALYSIS 핸드오프 표 8행 | 표만으로 PLAN 2.N.1·2.N.3 입력 채우기 시도 | 추가 문서 열람 없이 채워지면 Pass |

---

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 실 데이터 입력)

#### S-1: analysis-core.md 앵커 계약 준수

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-14 |
| 대상 | F-001 / Tier2 산출물의 `analysis-core.md §N` 인용 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구 — 스크립트)** |
| 조건 | Tier1(Step 1) 완료 후 Tier2 5개 Step 산출물 존재 |
| 기대 결과 | Tier2 산출물이 인용한 앵커명이 `analysis-core.md` 실제 헤딩 목록에 100% 포함 |
| 도구 | bash grep + 비교 스크립트 |
| 실행 명령 | `grep -n "^## [0-9]" opal/core/references/harness/analysis-core.md` (앵커 목록) + `grep -rnoE "analysis-core\.md[^\`]*§[0-9]+(\.[0-9]+)?" opal/ docs/` (인용 전수, 관측 스코프: opal/ + docs/ 전체) |
| 결과 | Pass |
| 상세 | 앵커 목록(analysis-core.md 실제 헤딩) = §1~§7(7개). 인용 전수 검색 결과 `opal-harness.md`(§2), `op-dev-analysis/SKILL.md`(§7 ×2), `op-dev-plan/plan-guide.md`(§5·§1·§3·§6, 변경이력 1건 포함), `analysis-guide.md`(§1·§6·§4·§6·§7)에서 총 11건 인용 — 전부 §1/§2/§4/§5/§6/§7 범위 내로 100% 포함. §3 인용도 plan-guide.md:98·459에 존재해 앵커 밖 인용 0건. |

#### S-2: 하네스 모듈 표 신규 행 4열 완비

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | F-001 / `opal/core/references/opal-harness.md` §2 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | Step 2 완료 |
| 기대 결과 | `analysis-core.md` 행 1개 추가 + `모듈\|파일\|로드 시점\|해당 §` 4열 전부 비어있지 않음 |
| 도구 | bash grep |
| 실행 명령 | `grep -n "분석 코어" opal/core/references/opal-harness.md` (§2 하네스 모듈 표, opal-harness.md:113 대상) |
| 결과 | Pass |
| 상세 | 113행: `\| 분석 코어 \| harness/analysis-core.md \| ANALYSIS 단계 진입 시 / PLAN 2단계(기능별 분석) 진입 시 \| §2 \|` — 4열(모듈·파일·로드 시점·해당 §) 전부 값 존재, 신규 행 1개. |

#### S-3: 하네스 최상위 절 번호 불변 (회귀)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-11 |
| 대상 | F-001 / `opal-harness.md` 절 번호 체계 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | Step 2 전후 스냅샷 확보 |
| 기대 결과 | 개정 전후 `## N.` 헤딩 목록이 완전 동일 — 1건이라도 다르면 Fail |
| 도구 | bash diff |
| 실행 명령 | `diff <(git show HEAD:opal/core/references/opal-harness.md \| grep -n "^## [0-9]") <(grep -n "^## [0-9]" opal/core/references/opal-harness.md)` (개정 전 HEAD 스냅샷 vs 현재, 파일 전체 375줄 스코프) |
| 결과 | Pass |
| 상세 | 개정 전/후 모두 `## 1.`~`## 10.` 10개 헤딩(번호·제목) 완전 동일 — diff 출력 0줄. `git diff --stat`도 §2 내부 +9줄만 확인(최상위 헤딩 미변경). |

#### S-4: 이관 원본 삭제 확인

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10 |
| 대상 | F-002 / `analysis-guide.md` 체크리스트 섹션 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | Step 4 완료 |
| 기대 결과 | 이관된 체크리스트 원본 항목이 `analysis-guide.md`에 부재 + `analysis-core.md` 포인터 1건 이상 존재 (둘 다 충족해야 Pass) |
| 도구 | bash grep |
| 실행 명령 | `grep -n "\\- \\[ \\]" opal/skills/op-dev-analysis/references/analysis-guide.md` (원본 체크리스트 잔존) + `grep -c "analysis-core.md" opal/skills/op-dev-analysis/references/analysis-guide.md` (포인터, 파일 전체 109줄 스코프) |
| 결과 | Pass |
| 상세 | 체크리스트 항목(`- [ ]`) 매치 0건(grep exit 1) — 원본 본문 잔존 0건. `analysis-core.md` 포인터 참조 6건(§1·§4·§6 ×2·§7 ×2) — 1건 이상 조건 충족. |

#### S-5: 중복 0건 — 신설 SSOT 포함 스코프

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-13 |
| 대상 | F-002 / R-2 AC (a) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | Phase 2 완료 |
| 기대 결과 | 스코프를 **5파일**(기존 4 + `analysis-core.md`)로 두고 정규화 후 2회 이상 출현 문장 0건. 스코프에서 `analysis-core.md`를 빼면 위양성 Pass가 되므로 스코프 자체를 검증 항목에 포함한다 |
| 도구 | python 정규화 계수 스크립트 |
| 실행 명령 | python3 정규화 dedup 스크립트(리스트/인용/헤딩/볼드/백틱 제거+공백압축, 20자 이상, 2개 이상 파일 완전일치) — **관측 스코프 5파일**: `opal/skills/op-dev-analysis/SKILL.md` · `opal/skills/op-dev-analysis/references/analysis-guide.md` · `opal/skills/op-dev-analysis/references/tech-context-guide.md` · `opal/skills/op-dev-plan/references/plan-guide.md` · `opal/core/references/harness/analysis-core.md` |
| 결과 | Pass |
| 상세 | 5파일 스코프에서 원시 중복 매치 1건 검출: `SKILL.md:20` ↔ `plan-guide.md:11` "[MUST] 산출물에 소스코드 원문 블록을 기재하지 않는다... 규칙 SSOT: citation-rules.md §2.2" — 이는 `analysis-core.md` §7 dedup 비대상 예외 2종("citation-rules.md 트리거 문구 등 SSOT+Trigger 관용구")에 해당(ANALYSIS.md:209에서도 동일 판정). 예외 적용 후 순중복 **0건**. `analysis-core.md`를 스코프에서 제외했다면 이 판정 자체가 성립하지 않았을 것 — 5파일 스코프 유지가 위양성 방지에 필수임을 확인. |

#### S-6: 미등록 MCP 잔존 0건

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-13(동일 계열 위양성 방지) |
| 대상 | F-003 / R-3 AC (a) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | Step 5 완료 |
| 기대 결과 | `tech-context-guide.md`에서 `supabase|github|figma|sentry` 정규식 매치 0건 |
| 도구 | bash grep -E |
| 실행 명령 | `grep -inE "supabase|github|figma|sentry" opal/skills/op-dev-analysis/references/tech-context-guide.md` (파일 전체 154줄 스코프) |
| 결과 | Pass |
| 상세 | 매치 0건(grep exit 1). §4 MCP 매핑 절이 하드코딩 예시를 전부 삭제하고 등록본(`mcps.md`) 조회 규칙으로 교체됨을 확인. |

#### S-7: 등록본 조회 규칙 문장 존재

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-13 |
| 대상 | F-003 / R-3 AC (b) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | Step 5 완료 |
| 기대 결과 | "등록본 조회 + 미등록 기재 금지" 취지 문장 1건 이상 |
| 도구 | bash grep |
| 실행 명령 | `grep -n "등록본\|미등록.*기재 금지\|등록된 것 중" opal/skills/op-dev-analysis/references/tech-context-guide.md` (파일 전체 154줄 스코프) |
| 결과 | Pass |
| 상세 | 3건 매치: :98 "등록된 것 중 이번 태스크에 필요한 것만 매핑", :100 "매핑 기준·MCP 종류는 항상 mcps.md를 조회", :102 "미등록 MCP는 기재 금지." — 1건 이상 충족. |

#### S-8: §6 템플릿 2필드 구조 전환

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7(형식만 통과 방지 계열) |
| 대상 | F-003 / R-4 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | Step 3·5 완료 |
| 기대 결과 | §6 템플릿이 "프로젝트 SSOT 경로 + 이번 태스크 델타" 2필드이고, 전체 스택 재기재 금지 문장이 존재 |
| 도구 | bash grep |
| 실행 명령 | `grep -n "SSOT 경로 + 델타\|프로젝트 SSOT\|재기재하지 마라\|재기재하지 않" opal/skills/op-dev-analysis/references/tech-context-guide.md` (파일 전체 154줄 스코프) |
| 결과 | Pass |
| 상세 | :115 "ANALYSIS.md의 '6. 기술 컨텍스트' 섹션은 **SSOT 경로 + 델타** 2필드 구조로 기록한다. [MUST] 프로젝트 전체 기술 스택을 태스크마다 재기재하지 마라" — 2필드 구조 명시 + 재기재 금지 [MUST] 문장 확인. :120~121 "6.1 프로젝트 SSOT"/:123 "6.2 이번 태스크 델타" 서브섹션도 실물로 존재. |

#### S-9: Q표가 템플릿 실물 섹션으로 배치됨

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | F-004 / R-5 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | Step 3 완료 |
| 기대 결과 | ANALYSIS.md 통일 형식 **코드펜스 안**에 Q표 섹션이 존재하고 "권장" 표기가 병기됨. 산문 서술만 있고 템플릿에 없으면 Fail |
| 도구 | bash grep(코드펜스 범위 한정) |
| 실행 명령 | `awk '/^```markdown$/{print NR} /^```$/{print NR}' opal/skills/op-dev-analysis/SKILL.md` (코드펜스 경계) + `grep -n "지정 분석 질문\|권장(강제 아님)" opal/skills/op-dev-analysis/SKILL.md` (파일 전체 204줄 스코프) |
| 결과 | Pass |
| 상세 | ANALYSIS.md 통일 형식 코드펜스는 74행(```markdown 시작)~172행(``` 종료). "## 7. 지정 분석 질문 Q1~QN 답변"(157행)·"> 권장(강제 아님)..."(159행) 모두 이 구간 내부 — 산문 배치가 아니라 템플릿 실물 섹션으로 확인. |

#### S-10: 디스패치 프롬프트 질문 슬롯 추가

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | F-004 / R-5 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | Step 8 완료 |
| 기대 결과 | `opal-pilot-dev/SKILL.md` STEP 2 프롬프트에 질문 주입 슬롯 1개 |
| 도구 | bash grep |
| 실행 명령 | `awk '/^## STEP 2/,/^## STEP 3/' opal/skills/opal-pilot-dev/SKILL.md \| grep -n "분석 질문"` (STEP 2 디스패치 프롬프트 블록 스코프) |
| 결과 | Pass |
| 상세 | STEP 2 프롬프트에 `**분석 질문**: {Q1~QN — PM이 이번 분석에서 답을 받아야 할 질문. 없으면 "없음"}` 슬롯 1개 확인. |

#### S-11: 핸드오프 표 3열 골격

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | F-004 / R-6 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | Step 3 완료 |
| 기대 결과 | 템플릿에 「다음 단계 입력」 섹션 + `항목\|확정값\|근거` 3열 표 골격 존재 |
| 도구 | bash grep |
| 실행 명령 | `grep -n "다음 단계 입력\|항목 \| 확정값 \| 근거" opal/skills/op-dev-analysis/SKILL.md` (ANALYSIS.md 통일 형식 코드펜스 74~172행 스코프) |
| 결과 | Pass |
| 상세 | :163 "## 8. 다음 단계 입력 — PLAN이 재조사 없이 쓸 수 있는 확정값" 헤딩 + :165 `\| 항목 \| 확정값 \| 근거 \|` 3열 표 헤더 확인. |

#### S-12: 원문 덤프 금지가 포인터로 배선됨

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10(복제 금지 계열) |
| 대상 | F-004 / R-7 (a) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | Step 1 완료 |
| 기대 결과 | `analysis-core.md`에 금지 조항이 `citation-rules.md §2.2` **포인터 형태**로 존재. 원문 문장을 복제했으면 Fail(수치·문언 복제 금지) |
| 도구 | bash grep |
| 실행 명령 | `grep -n "citation-rules.md.*§2.2\|원문 블록" opal/core/references/harness/analysis-core.md` + `sed -n '97p' opal/core/references/harness/citation-rules.md`(원문 대조, 두 파일 전체 스코프) |
| 결과 | Pass |
| 상세 | analysis-core.md:167 "소스코드 원문 블록이 0건인가 — 코드펜스는 실행 명령·시그니처로 한정한다(citation-rules.md §2.2 소스코드 원문 블록 금지)" — citation-rules.md:97 원문("[MUST] 산출물 분량 규칙: ...")과 문언이 다른 체크리스트 표현으로, §2.2 포인터만 인용. 원문 복제 아님. |

#### S-13: QA 코드펜스 검증 행 추가

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | F-005 / R-7 (b) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | Step 7 완료 |
| 기대 결과 | `qa-dev-guide.md` ANALYSIS 표에 코드펜스 관련 검증 행 1개 추가 |
| 도구 | bash grep |
| 실행 명령 | `grep -n "^\| R-7 \|" opal/skills/op-dev-qa/references/qa-dev-guide.md` (ANALYSIS 검증 기준 표, :67-78 스코프) |
| 결과 | Pass |
| 상세 | :77 `\| R-7 \| 원문 덤프 차단 \| 소스코드 원문 블록이 0건인가? 코드펜스가 실행 명령·시그니처로 한정되는가? \|` — 코드펜스 검증 행 1개 신규 추가 확인. |

#### S-14: QA 확정 입력·근거 등급 검증 행 추가

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | F-005 / R-8 (a) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | Step 7 완료 |
| 기대 결과 | 확정 입력 판정·근거 등급 검증 행이 각각 존재 |
| 도구 | bash grep |
| 실행 명령 | `grep -n "^\| R-8 \|" opal/skills/op-dev-qa/references/qa-dev-guide.md` (ANALYSIS 검증 기준 표, :67-78 스코프) |
| 결과 | Pass (단서 병기) |
| 상세 | :78 `\| R-8 \| 098 규약 준수 \| 확정 입력 판정표가 전건 판정되고, 근거 등급·관측 스코프·실행 명령이 병기되었는가? \|` — PLAN.md TS-017 설계상 R-8 **1개 행**이 "확정 입력 판정"과 "근거 등급" 두 검증 취지를 함께 서술하는 형태로 의도됨(별도 2행 아님). 두 취지 모두 R-8 행 텍스트 안에 문자열로 실존해 "각각 존재" 조건을 텍스트 레벨에서 충족. |

#### S-15: 거울 사본 동시 갱신 정합

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | F-005 / `qa-dev-guide.md` ↔ `opal/skills/op-dev-qa/SKILL.md` |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | Step 7 완료 |
| 기대 결과 | 두 파일의 R축·P축 번호 범위가 일치. 한쪽만 늘어났으면 Fail |
| 도구 | bash grep + 비교 |
| 실행 명령 | `grep -n "R-1 ~ R-8\|R-1~R-8\|P-1 ~ P-8\|P-1~P-8" opal/skills/op-dev-qa/references/qa-dev-guide.md opal/skills/op-dev-qa/SKILL.md` (두 파일 전체 스코프) |
| 결과 | Pass |
| 상세 | qa-dev-guide.md: ANALYSIS 표 R-1~R-8(8행), PLAN(Full) 표 P-1~P-8(8행) 실물 정의. op-dev-qa/SKILL.md:118 "ANALYSIS: R-1 ~ R-8", :121 "PLAN (Full): P-1 ~ P-8" 거울 사본 — 두 파일 번호 범위 완전 일치. |

#### S-16: pipeline.json checklist 4항목 + 스펙 검증

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | F-005 / R-8 (b) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | Step 9 완료 |
| 기대 결과 | `analysis.pm_gate.checklist`가 4항목 문자열 배열이고 `state-tool spec-validate` exit 0 |
| 도구 | state-tool spec-validate |
| 실행 명령 | `opal/tools/state-tool/run.sh spec-validate opal/skills/opal-pilot-dev/references/pipeline.json` |
| 결과 | Pass |
| 상세 | `python3 -c "import json; print(len(json.load(open('opal/skills/opal-pilot-dev/references/pipeline.json'))['task_steps'][3]['gate']['checklist']))"` → 4 (문자열 배열 4항목: §0 참조 문서 / §확정 입력 판정 / §다음 단계 입력 3열 표 / 소스코드 원문 블록 0건). `spec-validate` 실행 결과: `{"ok": true, "command": "spec-validate", "violations": [], "violations_count": 0}`, exit 0. |

#### S-17: plan-guide의 analysis-core Read 지시

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10 |
| 대상 | F-006 / R-9 (a) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | Step 6 완료 |
| 기대 결과 | `plan-guide.md`에 `analysis-core.md` Read 지시 1건 이상 |
| 도구 | bash grep |
| 실행 명령 | `grep -n "analysis-core.md.*Read\|\[MUST\].*analysis-core" opal/skills/op-dev-plan/references/plan-guide.md` (파일 전체 459줄 스코프) |
| 결과 | Pass |
| 상세 | :27 "[MUST] `opal/core/references/harness/analysis-core.md`를 Read한다 — PLAN 2단계(기능별 분석)는 이 문서가 정의하는 절차...를 따른다." — 1건 이상 충족. |

#### S-18: 절차 문단의 포인터 대체 (R-9 신 판정식)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10 |
| 대상 | F-006 / R-9 (b) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | Step 6 완료 + 개정 전 스냅샷 |
| 기대 결과 | `plan-guide.md` 2단계 자체 절차 서술 문단 수가 개정 전 대비 **감소**하고, 감소분마다 `analysis-core.md` 포인터가 대응. before/after 수치를 병기 |
| 도구 | python 문단 계수 스크립트 |
| 실행 명령 | `git diff HEAD -- opal/skills/op-dev-plan/references/plan-guide.md` (2단계 2.N.1~2.N.3 구간, :87-104) |
| 결과 | Pass |
| 상세 | before=7문단 / after=4문단(변경이력 v2.6 자체 명시 "문단 7→4"과 diff 실측 일치, 감소 3). 2.N.1: 서술문+표+노트 2개(3블록) → [MUST] 승계 문장 1개 + `analysis-core.md` §5 포인터(1블록). 2.N.2: 분기 서술+"없음" 6항목 불릿(2블록) → "있음"[MUST] 승격 문장+"없음" §1·§3 포인터 문장(2블록, 순변화 없음). 2.N.3: 4항목 불릿(1블록) → [MUST] 승계 문장+§6 포인터(1블록, 순변화 없음이나 서술→포인터 대체). 순감소 3(2.N.1에서 발생)이 §5 포인터에 대응하고, 2.N.2·2.N.3도 각각 §1·§3, §6 포인터로 서술을 대체 — 감소분 전건 포인터 대응 확인. |

#### S-19: PLAN 승계 [MUST] 배선

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10 |
| 대상 | F-006 / R-11 (a)(b) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | Step 6 완료 |
| 기대 결과 | 2.N.1·2.N.3에 승계 지시 존재 + `[MUST] 재도출 금지` 문장 존재 |
| 도구 | bash grep |
| 실행 명령 | `grep -n "재도출 금지" opal/skills/op-dev-plan/references/plan-guide.md` (2.N.1 :92, 2.N.3 :102 스코프) |
| 결과 | Pass |
| 상세 | :92(2.N.1) "[MUST] ANALYSIS.md 「다음 단계 입력」 표의 확정값은 재조사 없이 승계한다([MUST] 재도출 금지 — ...)" / :102(2.N.3) "[MUST] ANALYSIS.md 「다음 단계 입력」 표의 확정값은 재조사 없이 승계한다([MUST] 재도출 금지 — ...)" — 2.N.1·2.N.3 둘 다 승계 지시 + `[MUST] 재도출 금지` 문장 확인(2.N.2 :96도 동일 문구 추가 보유). |

#### S-20: [RED] 확정된 설계 방향 항목이 items[]에 반환된다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | F-007 / `verify --evidence-check` |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest, 실 파일 픽스처 — mock 금지)** |
| 조건 | 픽스처 A. **Tier4a에서 선작성해 실패(exit≠0)를 증거로 기록한 뒤 GREEN 진입** |
| 기대 결과 | 반환 `items[]`에 `source`가 확정된 설계 방향인 항목이 불릿 수만큼 존재 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py::TestT100DirectionEvidence::test_t100_direction_items_merged_into_items_with_source_field -v` |
| 결과 | Pass (GREEN) |
| 상세 | 1 passed. 픽스처 A 최상위 불릿 6건(결정 3 + 사실 3) 전부 `source="confirmed_direction"`으로 items[]에 편입, 명확화 결과 4건은 `source="clarification"` — 총 10건. 중첩 불릿 1행은 비수집 확인. Tier4a RED 단계에서 실패(exit≠0) 기록 후 Step 11 GREEN 구현 완료 상태. |

#### S-21: [RED] 기존 confirmed_ratio 분모 불변 (회귀)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | F-007 / PD-1 분리형 계약 |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | 픽스처 A |
| 기대 결과 | `confirmed_ratio` 분모가 명확화 결과 4요소로 유지 — 확정된 설계 방향 항목이 분모에 섞이면 Fail |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py::TestT100DirectionEvidence::test_t100_existing_confirmed_ratio_denominator_unchanged -v` |
| 결과 | Pass (GREEN) |
| 상세 | 1 passed. 픽스처 A에서 `confirmed_ratio`=0.5(2/4) 불변, clarification source 항목 4건 고정, unconfirmed={제약,완료기준} — 방향 항목 6건이 분모에 섞이지 않음을 확인(PD-1 분리형 계약 유지). |

#### S-22: [RED] direction_confirmed_ratio 신규 키 반환

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | F-007 / R-10 (a) |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | 픽스처 A |
| 기대 결과 | 반환 JSON에 `direction_confirmed_ratio` 키 존재 + 값이 0~1 범위 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py::TestT100DirectionEvidence::test_t100_direction_confirmed_ratio_new_key_returned -v` |
| 결과 | Pass (GREEN) |
| 상세 | 1 passed. `direction_confirmed_ratio`=1.0(확정3+승계3/6, 0~1 범위 내) 반환 확인, `confirmed_ratio`(0.5)와 값이 달라 PD-1 분리형(별개 분모) 성립. |

#### S-23: [RED] exit 0 라우터 계약 유지

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | F-007 / R-10 (b) |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | 픽스처 A·B·C 3종 |
| 기대 결과 | 3개 픽스처 전부 exit 0 — 미확정이 있어도 차단하지 않는다 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py::TestT100DirectionEvidence::test_t100_exit_code_zero_on_all_return_paths -v` |
| 결과 | Pass (GREEN) |
| 상세 | 1 passed. TASK.md 부재 skip / 명확화 섹션 부재 skip / 픽스처 A·B·C 정상 판정 3종 — 전 5경로 exit 0 확인, 정상 경로 JSON에 `direction_confirmed_ratio` 포함. |

#### S-24: [RED] 섹션 부재 시 graceful skip (하위호환)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | F-007 / 레거시 TASK.md |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | 픽스처 B(섹션 없음) |
| 기대 결과 | 신규 파서가 독자적으로 부재를 처리하고 기존 반환 형태가 유지됨 — 예외·크래시 없음 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py::TestT100DirectionEvidence::test_t100_legacy_task_md_without_direction_section_graceful_skip -v` |
| 결과 | Pass (GREEN) |
| 상세 | 1 passed. 픽스처 B(섹션 없음) — exit 0, items 4건(명확화만), confirmed_ratio 0.5 불변, unconfirmed 2건 불변, `direction_confirmed_ratio`=None. 예외·크래시 없이 기존 반환 형태 유지 확인. |

#### S-25: [RED][대조군] 플래그 상호 배타 계약 불변

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | F-007 / `evidence_check_flag_conflict` |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | 픽스처 A + 두 플래그 동시 지정 |
| 기대 결과 | 기존과 동일하게 `evidence_check_flag_conflict` exit 1 — 신규 파서 추가가 이 경로를 흔들지 않는다 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py::TestT098EvidenceCheck::test_evidence_check_flag_conflict_exit1 -v` |
| 결과 | Pass (대조군, 무변경 확인) |
| 상세 | 1 passed. `--evidence-check`+`--clarification-check` 동시 지정 → exit 1, `error="evidence_check_flag_conflict"` — 기존(TestT098EvidenceCheck, 무수정 클래스) 계약 그대로 유지, 신규 파서(`_locate_confirmed_direction_items`) 추가가 이 경로에 영향 없음 확인. |

#### S-26: [RED][경계값] 확정 항목 0건일 때 분모 0 처리

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | F-007 / 경계 조건 |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | 픽스처 C(헤딩만, 항목 0건) |
| 기대 결과 | ZeroDivisionError 미발생 + `direction_confirmed_ratio`가 정의된 값(예: null 또는 0)으로 반환 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py::TestT100DirectionEvidence::test_t100_direction_section_with_zero_items_no_zero_division -v` |
| 결과 | Pass (GREEN) |
| 상세 | 1 passed. 픽스처 C(헤딩만, 항목 0건) — exit 0, ZeroDivisionError 미발생, `direction_confirmed_ratio` ∈ {None, 0.0}, `confirmed_ratio` 0.5 불변, items 4건(명확화만). |

### L2. 프로세스 통합 (자동, 실 파일 read→변경→re-read)

#### S-27: README 계약 문서 정합

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 |
| 대상 | F-007 / `opal/tools/state-tool/README.md` |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | Step 11 완료 |
| 기대 결과 | 코드가 반환하는 신규 키 문자열이 README 반환 계약 절에 동일 문자열로 존재 |
| 도구 | bash grep 대조 |
| 실행 명령 | `grep -n '"direction_confirmed_ratio"\|"source"\|confirmed_direction' opal/tools/state-tool/state_tool.py` vs `grep -n "direction_confirmed_ratio\|confirmed_direction\|source" opal/tools/state-tool/README.md` (두 파일 전체 스코프) |
| 결과 | Pass |
| 상세 | 코드: `direction_confirmed_ratio`(2668/2749행), `source`(2326/2633/2658행), `"confirmed_direction"`(2326행) 키 존재. README: :278-341(반환 계약 절)에 `direction_confirmed_ratio`, `source`(`"clarification"`\|`"confirmed_direction"`) 동일 문자열로 명시 + 예시 JSON(:318-326)·필드표(:338) 일치. v1.9 변경이력(:460)에도 동일 키 반영. |

#### S-28: docs 동일 수치 2곳 동시 갱신

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-12 |
| 대상 | `docs/ARCHITECTURE.md` |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | Step 12 완료 |
| 기대 결과 | 동일 수치가 등장하는 2곳의 값이 서로 일치 |
| 도구 | bash grep |
| 실행 명령 | `grep -n "harness/[^)]*파일\|harness/ [0-9]*파일" docs/ARCHITECTURE.md`(정규식 전종 매치, 파일 전체 502줄 스코프, 변경이력 행 `:478``:481`은 과거 값 인용이므로 판정 대상에서 제외) + `ls opal/core/references/harness/ \| wc -l`(실측 대조) |
| 결과 | 1차 Fail → PM 정정 → **재검 Pass** |
| 상세 | **1차 검증(Fail)**: `:80` §핵심 디렉토리 표 "harness/`(하네스 세부 규약 **17파일**...)" vs `:382` 디렉토리 트리 "harness/ **19파일**" — 두 곳 불일치(17 vs 19), 실측(`ls \| wc -l`=19, `analysis-core.md` 포함)은 `:382`와만 일치. H-12 가설("동일 수치 2곳 중 한쪽만 갱신") 재현으로 판정. **PM 정정 경위**: PM 1차 조치가 `:80` 한 줄 안에 등장하는 "최상위 17파일"(references/ 최상위 파일 수, 실측 17로 무관·무변경 대상)과 "harness/(하네스 세부 규약 17파일)"(harness/ 파일 수, 정정 대상) 두 수치를 혼동해 앞의 1건만 확인하고 뒤의 harness 언급 정정을 누락했음을 확인 — TEST S-28 검출이 잔존 결함을 잡아 PM이 `:80` 뒷부분을 19파일로 정정(`:478` 변경이력에 정정 경위 기록됨). **재검증(현재)**: 정규식 전종 매치 결과 현재-상태 언급 2곳 — `:80`(하네스 세부 규약 **19파일**), `:382`(harness/ **19파일**) — 두 값 일치, 실측(19)과도 일치. `:478``:481` 변경이력 행의 "17파일" 언급은 과거 값을 기록한 이력 문구이므로 stale 판정에서 제외(지시사항 반영). **판정: Pass.** |

#### S-29: 실 태스크 폴더 CLI 통합 실행

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1, H-2 |
| 대상 | F-007 / CLI 경로 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | Step 11 GREEN + 본 태스크 폴더 |
| 기대 결과 | 실 TASK.md(확정된 설계 방향 16건 + 명확화 결과 4행)로 실행 시 두 source 항목이 혼재 반환되고 exit 0 |
| 도구 | state-tool run.sh |
| 실행 명령 | `opal/tools/state-tool/run.sh verify "tasks/100-260822-opd-분석코어-공유SSOT" --evidence-check` |
| 결과 | Pass |
| 상세 | exit 0, `ok:true`. `items[]`에 `source="clarification"` 4건(목표·범위·제약·완료기준) + `source="confirmed_direction"` 21건([결정] 16 + [사실] 5) 혼재 반환 확인. `confirmed_ratio`=0.75(명확화 4요소 기준 불변), `direction_confirmed_ratio`=1.0, `unconfirmed`=["목표"]. |

### L3. 사용자 협업 (수동, [SUPERVISOR] 마커)

#### S-30: 목표 달성 — 재생성 대조 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7, H-8 |
| 대상 | F-008 / R-12 · AC-G1~G4 |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업)** — AC-G2·G3 계수는 M1 자동 병행 |
| 조건 | Step 13. baseline(`ANALYSIS.baseline.md`) 고정 + 표준 opd 프롬프트로 `ANALYSIS-REGEN.md` 생성. AC-G1은 Step 11 GREEN 이후에만 측정, AC-G4는 측정 불가로 확정 |
| 기대 결과 | AC-G1 `승계` 판정 존재 / AC-G2 선조회 인용 1건 이상 / AC-G3 코드펜스 비율 baseline 대비 감소(동률 허용) / AC-G4 측정 불가 명시 |
| **Fail 조건(명시)** | 아래 중 **하나라도** 해당하면 S-30은 **Fail**이다 — ⓐ 재생성본에 TASK 확정 항목의 재확인 서술이 1건 이상 존재 ⓑ 재생성본에 선조회(`code-scan`·`brain`) 인용이 0건 ⓒ 코드펜스 비율이 baseline보다 **증가** ⓓ 재생성본이 표준 프롬프트가 아닌 PM 수동 주입으로 만들어짐. '천장 효과'는 ⓐ~ⓓ 어디에도 해당하지 않을 때만 '동등 재현'으로 판정하는 근거이며, **Fail 조건을 면제하지 않는다** |
| 실행자 | [SUPERVISOR] — 캡틴이 PM의 대조 결과를 직접 Read해 교차검증(ANALYSIS 서술 신뢰 금지) |
| 결과 | **조건부 Pass** |
| 상세 | 캡틴 확인 2026-08-24 14:41. 3축 실측 충족 — ① 선조회 인용 존재(D-17 brain 0건·D-18 code-scan 0건·D-19 과거 산출물, **PM 지시 없이 워커가 자발 수행**) ② 코드펜스 비율 6.3%→**0.0%** 감소 ③ 신규 템플릿 섹션 3종(Q표·핸드오프·PLAN 결정 필요)이 지시 없이 전건 등장. Fail 조건 ⓑⓒⓓ 미저촉. ⓐ(재확인 서술)는 형식상 저촉하나 그 재확인이 TASK.md `[사실]` 2건의 실제 stale을 검출해 값을 만들었고, 근본 원인은 AC-G1이 상류가 없는 ANALYSIS 단계를 겨눈 **판정 기준 결함**이므로 조건부 Pass로 확정(소유자 승인). AC-G1은 PLAN 단계로 재배치, `해당없음(결정)` 판정값 템플릿 승격 — 후속 2건 이월. |

> **PM 요청 양식**: "baseline `ANALYSIS.baseline.md`(331줄)과 재생성본 `ANALYSIS-REGEN.md`를 나란히 열어, ① TASK 확정 항목이 재확인되지 않고 승계로만 나타나는지 ② 선조회 인용이 있는지 ③ 코드펜스 비율이 줄었는지 세 가지를 확인해주세요. 천장 효과로 개선 폭이 작을 수 있으나, 위 Fail 조건 ⓐ~ⓓ에 걸리면 '동등 재현'이 아니라 Fail입니다."

#### S-31: opp·oppd 배제가 결정으로 기록됨 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | 범위 결정 |
| 계층 | L3 |
| **실행 방식** | **M3** |
| 조건 | TASK.md 최종본 |
| 기대 결과 | `op-task-plan/references/plan-guide.md` 배제가 "누락"이 아니라 "명시적 결정"으로 읽히는지 캡틴이 확인 |
| 실행자 | [SUPERVISOR] |
| 결과 | Pass |
| 상세 | 캡틴 확인 2026-08-24 14:41. `TASK.md` 범위 셀 「제외(명시적 결정)」에 `op-task-plan/references/plan-guide.md`(opp·oppd 경로) 배제가 기록돼 있고, 별도 파일임이 ANALYSIS §7 Q8로 확인됨 — 누락이 아니라 의도된 결정으로 읽힌다. |

> **PM 요청 양식**: "TASK.md 범위 셀의 제외 항목에 opp·oppd 경로 배제가 적혀 있습니다. 이것이 의도한 결정이 맞는지 확인해주세요 — 아니라면 범위를 넓혀야 합니다."

#### S-32: 배포 미반영을 완료로 오인하지 않음 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | F-007 / 배포 경계 |
| 계층 | L3 |
| **실행 방식** | **M3** |
| 조건 | Step 11 GREEN 완료 후 |
| 기대 결과 | 소스는 GREEN이나 배포본(`~/.opal/tools/state-tool/`)은 구버전임을 캡틴이 확인하고, DONE.md에 미수행으로 기재될 것을 승인 |
| 실행자 | [SUPERVISOR] |
| 결과 | Pass |
| 상세 | 캡틴 확인 2026-08-24 14:41. 소스는 GREEN(단일 파일 347 / 디렉토리 364 passed)이나 배포본 `~/.opal/tools/state-tool/`은 구버전 유지. H-6대로 정상 상태이며 DONE.md에 미수행으로 명시하는 조건으로 승인 — EXECUTE를 완료로 오인하지 않았음을 확인. |

> **PM 요청 양식**: "`state_tool.py` 소스는 GREEN이지만 재배포는 범위 밖이라 실행하지 않았습니다. 배포본이 구버전인 상태로 태스크를 닫는 것이 맞는지 확인해주세요."

#### S-33: 핸드오프 표만으로 PLAN 입력이 채워지는가 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10, H-8 |
| 대상 | F-006 / R-11 — PLAN 승계 행동(AC-G4 측정 불가에 대한 축소 대체 검증) |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업)** |
| 조건 | Step 6 완료 후. 개정된 `plan-guide.md`와 본 태스크 `ANALYSIS.md`의 「다음 단계 입력」 표만 제시한다 — PLAN.md 본문·§1.1 12행 표는 제시하지 않는다 |
| 기대 결과 | 핸드오프 표 8행만으로 `plan-guide.md` 2.N.1(관련 파일 맵)·2.N.3(영향 범위)의 입력이 **재조사 없이** 채워지는지 캡틴이 판단 |
| **Fail 조건(명시)** | 채우기 위해 ANALYSIS 본문·코드·상류 문서를 다시 열어야 하면 **Fail** — 승계 계약이 성립하지 않은 것이다 |
| 실행자 | [SUPERVISOR] — 캡틴 수동 확인 |
| 결과 | **Fail** |
| 상세 | 캡틴 확인 2026-08-24 14:41. 재생성본 「다음 단계 입력」 확정값 4행(구현 상태·측정 선행조건·pytest 수치·opds 커버 경로)만으로는 `plan-guide.md` 2.N.1 관련 파일 맵의 필수 필드(파일·6영역 라벨·변경 유형·순서)를 채울 수 없다. 채우려면 ANALYSIS 본문 §1.1을 다시 열어야 하므로 Fail 조건 저촉. **행 수 문제가 아니라 표 스키마 문제** — baseline 8행도 동일 필드가 없다. 개정된 `plan-guide.md:92`가 승계를 [MUST]로 요구하는데 표 스키마가 그 요구를 담지 못하는 계약 불일치. 처방 후보 2안: ⓐ 핸드오프 표에 파일 맵 하위 표 규정 ⓑ 2.N.1을 승계 대상에서 제외하고 ANALYSIS §1.1 직접 인용으로 배선. R-11 잔여 과제로 DONE.md 이월. |

> **PM 요청 양식**: "ANALYSIS의 「다음 단계 입력」 표 8행만 보고, PLAN 2단계의 관련 파일 맵과 영향 범위를 채울 수 있는지 봐주세요. 다른 문서를 열어야 한다면 승계가 실패한 것입니다."
>
> **왜 이 시나리오가 필요한가**: AC-G4(PLAN 재생성 대조)가 baseline PLAN.md 부재로 측정 불가로 확정됐고, 그 결과 목표의 'PLAN 절반'을 행동 계층에서 재는 항목이 0건이 됐다. PLAN 전체 재생성은 범위 확대라 채택하지 않고, 승계 계약만 좁게 확인하는 축소 대체 검증으로 갈음한다(SCENARIO-GATE-1 gaps 2).

---

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| R-1 (a)(b) | H-5, H-11, H-14 | L1 | S-1, S-2, S-3 | 스크립트:앵커·표·회귀 | F-001 |
| R-2 (a)(b) | H-10, H-13 | L1 | S-4, S-5 | 스크립트:중복계수 | F-002 |
| R-3 (a)(b) | H-13 | L1 | S-6, S-7 | 스크립트:MCP grep | F-003 |
| R-4 | H-7 | L1 | S-8 | 스크립트:템플릿 구조 | F-003 |
| R-5 | H-7 | L1 | S-9, S-10 | 스크립트:섹션·슬롯 | F-004 |
| R-6 | H-7 | L1 | S-11 | 스크립트:표 골격 | F-004 |
| R-7 (a) | H-10 | L1 | S-12 | 스크립트:포인터 형태 | F-004 |
| R-7 (b) | H-4 | L1 | S-13 | 스크립트:QA 행 | F-005 |
| R-8 (a)(b) | H-4 | L1 | S-14, S-15, S-16 | state-tool spec-validate | F-005 |
| R-9 (a)(b) | H-10 | L1 | S-17, S-18 | 스크립트:문단 계수 | F-006 |
| R-10 (a)~(d) | H-1, H-2 | L1+L2 | S-20~S-26, S-29 | `opal/tools/state-tool/tests/test_state_tool.py`:TestT100DirectionEvidence [T100/L1-R10] | F-007, RED-first |
| R-11 (a)(b) | H-10 | L1 | S-19 | 스크립트:MUST grep | F-006 |
| R-11 (c) | H-4 | L1 | S-15 | 스크립트:P축 대조 | F-005 |
| R-12 / AC-G1~G4 | H-7, H-8 | L3 | S-30 | 수동 대조 + 계수 스크립트 | F-008, 목표달성 시나리오 |
| 범위 결정 | H-3 | L3 | S-31 | 수동 확인 | 배제 명시 |
| 배포 경계 | H-6, H-9, H-12 | L2+L3 | S-27, S-28, S-32 | 수동 + grep | 계약·문서 정합 |
| R-11 (승계 행동) | H-10, H-8 | L3 | S-33 | 수동 확인 | F-006, AC-G4 축소 대체 검증(목표달성 계열) |

> **커버 확인**: R-1~R-12 전건이 최소 1개 시나리오에 매핑됐다(12/12). H-1~H-14 전건이 최소 1개 시나리오를 갖는다(14/14). 목표달성 시나리오는 S-30(ANALYSIS 트랙)과 S-33(PLAN 트랙 축소 대체)이다.

---

## 5. 코드 품질

> 위상: lint/type/format은 EXECUTE 단계 귀속 단위 테스트이며, TEST 단계는 회귀 가드 용도로만 재실행한다(중복 독립 실행 아님, opal-test-agent 페르소나 §코드 품질 검사 기준).

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | `ruff check` (Python 변경분: `state_tool.py` + `test_state_tool.py`) | Pass (회귀 가드) | `ruff check opal/tools/state-tool/state_tool.py opal/tools/state-tool/tests/test_state_tool.py` → 18개 위반 검출(:26,415,1073,1696,1747 / :46,51,792,1056,1142,1170,1588,1590,3165,3785,4664,8387,8542). `git diff HEAD` 대조 결과 이번 태스크 diff 범위(state_tool.py :3, :2268-2760 / test_state_tool.py :8979-9400)와 전건 비중첩 — 18건 전부 본 태스크 이전부터 존재하던 baseline 위반이며 신규 도입 0건. `python3 -m py_compile` 양쪽 파일 clean. |
| 2 | 타입 체크 | 해당 없음 | 해당 없음 | 프로젝트에 mypy/pyright 설정 파일 부재 — state-tool은 동적 타입 CLI 스크립트로 타입 체커 미도입. |
| 3 | 포맷터 | 해당 없음 | 해당 없음 | black/isort 등 포맷터 미설치·설정 파일 부재(프로젝트 전역) — 포맷 검사 대상 없음. |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | Pass | changed_files 15건 전체 대상 `grep -nEi "(api[_-]?key|secret|password|passwd|token|bearer)\s*[:=]\s*['\"][A-Za-z0-9_\-\.]{8,}['\"]"` + AWS/PEM 키 패턴(`AKIA[0-9A-Z]{16}`, `-----BEGIN ... PRIVATE KEY-----`) 스캔 — 매치 0건. |
| 2 | .gitignore 확인 | Pass | `.gitignore:32`에 `.env` 패턴 등록 확인. changed_files 15건 중 민감 파일(.env/credentials/키 파일) 유형 0건 — 해당 없음이 정상. |

## 7. 판정

**Partial Fail — S-1~S-32 Pass(32건, S-30은 조건부 Pass) / S-33 Fail(1건).** L1/L2 29건은 전건 Pass이며(S-28은 1차 Fail → PM 정정 → 재검 Pass로 이력 보존), RED-first 7건이 GREEN 전환, 회귀 pytest 347/364 감소 0건, 코드 품질·보안 전항목 Pass다. 유일한 Fail은 S-33(핸드오프 표 스키마가 PLAN 파일 맵 필드를 담지 못하는 계약 불일치)이며 P2급 설계 잔여로 소유자가 Fail 확정 후 R-11 잔여 과제로 이월했다 — 기능·보안·회귀에 Critical Fail 요건은 없다.**

### PM Gate 체크 (7대 강제 룰)

- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 — 픽스처는 실 파일(tmp_path)로 명시
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐 (S-1~S-33)
- [x] 가설↔시나리오 매핑(§4) 완전 — 미매핑 시나리오 없음
- [x] L1/L2/L3 계층 명시 (모든 시나리오)
- [x] L3 [SUPERVISOR] 마커 존재 + PM 요청 양식 첨부 (S-30·S-31·S-32·S-33)
- [x] 리스크 가설 표(§1) H-1~H-14와 시나리오 1:N 매핑 완전
- [x] 모든 시나리오에 실행 방식(M1/M2/M3) 명시
- [x] FE 변경 시 M2 시나리오 포함 — **비해당**(FE 화면·인증/인가·외부 API 연동 없음, 변경 대상은 규범 문서 + CLI 파서)
- [x] 목표 커버 — R-1~R-12 전건 §4 매핑 + 목표달성 시나리오 S-30 존재
