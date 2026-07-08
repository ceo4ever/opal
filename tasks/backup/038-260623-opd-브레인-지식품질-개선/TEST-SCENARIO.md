# TEST SCENARIO: 브레인 entity 지식 품질 개선 — ingest @header 전사 탈피

> 작성일: 2026-06-23 | 상태: 작성 완료
> 작성자: 알투(PM) + 캡틴 페어 | PLAN.md 가설 표 기반

> **RED-first 판단** (`opal/core/references/harness/red-first.md` §1.5): 본 태스크는 **"설정·문서" 트랙**(스킬·템플릿·참조 콘텐츠 개선 + 행위 불변, 도구 코드 무변경)이므로 **구현-후-검증 허용** 트랙이다. 고전적 RED-first(실패 테스트 선작성)는 미적용하며 state-tool `verify --red-check`는 OFF. 검증은 ① 산출물 검사(L1) ② 도구 회귀(L1) ③ 시연(L3 캡틴 협업, 행동 변화 실측)으로 구성한다. 공통 불변(작성자≠구현자·TEST 단계 검증)은 유지: 본 시나리오는 PM 작성, EXECUTE는 opal-task-agent, 검증은 PM/캡틴.

---

## 1. 리스크 가설 표

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | M-1·M-3 SKILL 텍스트 강화 (entity 작성 행동) | "[MUST] 강화 → AI가 실제로 WHY를 합성한다"는 행동 계약 | P0 | L3 | S-7 |
| H-2 | M-2 재생성 런북 정확성 | "`init --force`로 재생성된다"는 운영 절차 계약 (실제 pages/ 미삭제) | P1 | L1 | S-4 |
| H-3 | M-1·M-3·M-4 5섹션 헤딩 괄호 레이블 | citation-rules §8.9 "5W1H 섹션 헤딩 강제 금지" 계약 | P1 | L1 | S-9 |
| H-4 | M-4 `## 코드 참조`→`## 소스 커버리지` 개명 | brain-tool add-page가 템플릿 내부 섹션명 검증 여부 | P1 | L1 | S-6 |
| H-5 | provenance 3종 집행 수단 | "[MUST] SKILL 텍스트만으로 집행"(도구 게이트 미채택) | P1 | L3 | S-7 |
| H-6 | M-1 입력 큐레이션 선행 절차 | 큐레이션 선행이 init 시드 소요를 과도하게 늘리는가 | P2 | L3 | S-7 |
| H-7 | drift 정합 (opal-brain SKILL ingest --all 표) | ingest --all 표가 코드 현실과 모순 (문서 신뢰 계약) | P2 | L1 | S-8 |
| H-8 | M-2 재생성 시 synthesis 유실 | synthesis는 query 파생물 — init로 복구 불가 | P0 | L1 | S-4 |

---

## 2. 테스트 데이터 설계

> DB 없음 — 본 태스크의 "데이터"는 **소스 파일(변경 전/후 상태)**과 **시연용 테스트 brain**이다.

### 2.1 사전 조건 데이터

| 테이블 | 식별자 | 상태 | 출처 |
|--------|--------|------|------|
| 소스 파일 | `opal/skills/opal-brain/SKILL.md` | 변경 전: init 시드 entity 4섹션 + ingest --all drift 행 존재 | git 현재 상태 |
| 소스 파일 | `opal/skills/op-brain-ingest/SKILL.md` | 변경 전: STEP 4 entity 예시 4섹션 | git 현재 상태 |
| 소스 파일 | `opal/tools/brain-tool/templates/page-entity.md` | 변경 전: 5섹션, 마지막 `## 코드 참조` | git 현재 상태 |
| 소스 파일 | `opal/core/references/harness/citation-rules.md` | 변경 전: §8.5 brain ingest 항목 generic | git 현재 상태 |
| 도구 테스트 | `opal/tools/brain-tool/tests/test_brain_tool.py` | 현재 전체 통과(베이스라인) | git 현재 상태 |
| 시연 brain | 임시 테스트 프로젝트 또는 본 프로젝트 `.opal/brain/` 사본 | entity 1건 재생성 대상 (캡틴 시연 환경) | 수동 (Step 6) |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (사전 상태) | When (변경/실행) | Then (검증) |
|---------|------------------|-----------------|------------|
| S-1 | 3파일 entity 구조 4/4/5섹션 혼재 | EXECUTE M-1·M-3·M-4 반영 | 3파일 entity가 동일 5섹션 + @header 전사 금지 [MUST] |
| S-2 | init 시드·ingest STEP 4에 큐레이션·provenance 규칙 없음 | EXECUTE M-1·M-3 반영 | 큐레이션 선행 + provenance 3종 [MUST] 명문화 |
| S-3 | `brain_tool.py` 현재 상태 | EXECUTE 전체 완료 | `git diff brain_tool.py` 빈 결과 (도구 무변경) |
| S-4 | `opal-brain/SKILL.md`에 재생성 런북 없음 | EXECUTE M-2 반영 | 런북 4단계 + `--force` 한계 + synthesis 유실 리스크 명시 |
| S-5 | §8.5 brain 항목 generic | EXECUTE M-5 반영 | §8.5가 §8.2·§8.8 명문화·init 경로 연결, 모순 없음 |
| S-6 | brain-tool pytest 베이스라인 통과 | M-4 섹션 개명 반영 | pytest 전체 통과, 회귀 0 |
| S-7 | 개선 SKILL 배포본 | 시연 brain에서 `//opbr init`로 entity 1건 재생성 | 재생성 entity가 5섹션 + WHY에 provenance 3종 중 하나 명시 + @header 전사 아님 |
| S-8 | ingest --all 표에 "코드 @header → entity" 행 존재 | EXECUTE M-1b 반영 | 해당 행이 코드 현실(ingest-scan 미스캔)에 맞게 정정 |
| S-9 | 5섹션 헤딩 확정 | EXECUTE M-1·M-3·M-4 반영 | 헤딩이 `## 누가/왜/어떻게` 형식 아님 (§8.9 비위반) |

---

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 산출물·회귀 검사)

#### S-1: entity 5섹션 표준 3파일 일관성

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1(구조 전제) |
| 대상 | `opal-brain/SKILL.md` 시드 entity · `op-brain-ingest/SKILL.md` STEP 4 entity · `page-entity.md` 템플릿 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구 — grep/파일 검사)** |
| 조건 | EXECUTE M-1·M-3·M-4 완료 후 |
| 기대 결과 | 세 파일의 entity 섹션 헤딩이 `## 개요` / `## 책임 (WHAT)` / `## 설계 배경 (WHY)` / `## 관계 (HOW)` / `## 소스 커버리지`로 **동일**하고, @header 전사 금지가 [MUST]로 기재됨 |
| 도구 | grep |
| 실행 명령 | `grep -n "## 개요\|## 책임 (WHAT)\|## 설계 배경 (WHY)\|## 관계 (HOW)\|## 소스 커버리지\|@header 전사 금지" opal/skills/opal-brain/SKILL.md opal/skills/op-brain-ingest/SKILL.md opal/tools/brain-tool/templates/page-entity.md` |
| 결과 | **Pass** |
| 상세 | 3파일 모두 5섹션 헤딩(개요/책임 WHAT/설계 배경 WHY/관계 HOW/소스 커버리지) 확인. @header 전사 금지 [MUST] 각 파일에 명시. opal-brain:134, op-brain-ingest:170, page-entity.md:19 (comment). opal-brain/SKILL.md에는 5섹션 표 포함(행 136~144). op-brain-ingest SKILL.md에는 entity 예시 섹션(행 191~209). page-entity.md에는 5섹션 헤딩(행 22,30,38,50,58). |

#### S-2: 입력 큐레이션 + provenance 명문화

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1, H-5, H-6 |
| 대상 | `opal-brain/SKILL.md` 시드 Step · `op-brain-ingest/SKILL.md` STEP 4 |
| 계층 | L1 |
| **실행 방식** | **M1 (grep)** |
| 조건 | EXECUTE M-1·M-3 완료 후 |
| 기대 결과 | 입력 큐레이션 선행 절차(PROJECT.md 문서·관련 task PLAN·관련 brain 페이지 확인)와 provenance 3종(`(근거:…)`/`(추론: 코드패턴)`/`(WHY 미확보)`)이 [MUST]로 명문화됨 |
| 도구 | grep |
| 실행 명령 | `grep -n "입력 큐레이션 선행\|provenance\|근거:.*doc\|추론: 코드패턴\|WHY 미확보" opal/skills/opal-brain/SKILL.md opal/skills/op-brain-ingest/SKILL.md` |
| 결과 | **Pass** |
| 상세 | opal-brain SKILL.md:128 — `[MUST] 입력 큐레이션 선행` 4단계(PROJECT.md·task PLAN·brain 페이지·WHY 합성) 명시. opal-brain SKILL.md:146 — `[MUST] provenance 3종` 표(근거/추론/미확보) 명시. op-brain-ingest SKILL.md:172-175 — provenance 3종 [MUST] 태그 명시. |

#### S-3: 도구 코드 무변경 (SKILL 절차 채택 확인)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | `opal/tools/brain-tool/brain_tool.py` |
| 계층 | L1 |
| **실행 방식** | **M1 (git diff)** |
| 조건 | EXECUTE 전체 완료 후 |
| 기대 결과 | `git diff opal/tools/brain-tool/brain_tool.py`가 **빈 결과** — 입력 큐레이션이 SKILL 절차로만 처리됨(도구 게이트 미채택, 캡틴 확정 #3) |
| 도구 | git |
| 실행 명령 | `git diff opal/tools/brain-tool/brain_tool.py` |
| 결과 | **Pass** |
| 상세 | `git diff opal/tools/brain-tool/brain_tool.py` → 빈 결과(exit code 0). brain_tool.py 무변경 확인. 캡틴 확정 #3(도구 게이트 미채택) 준수. |

#### S-4: 재생성 런북 + synthesis 유실 리스크

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2, H-8 |
| 대상 | `opal-brain/SKILL.md` `## STEP: init` 하단 재생성 런북 절 |
| 계층 | L1 |
| **실행 방식** | **M1 (파일 검사)** |
| 조건 | EXECUTE M-2 완료 후 |
| 기대 결과 | 런북이 4단계(① synthesis 백업 → ② `pages/entity/` 직접 삭제 또는 `.opal/brain/` 전체 → ③ init 재실행 → ④ 복원)로 기재되고, **`init --force`는 pages/ 미삭제** 한계와 **synthesis 유실 리스크 ⚠️**가 명시됨 |
| 도구 | grep/read |
| 실행 명령 | `grep -n "재생성 런북\|init --force\|synthesis 유실\|query 파생물\|①\|②\|③\|④" opal/skills/opal-brain/SKILL.md` |
| 결과 | **Pass** |
| 상세 | opal-brain SKILL.md:186 — "재생성 런북 (brain 전체 재시드)" 절 존재. 4단계(①백업:190, ②삭제:193, ③재생성:196, ④복원:198) 기재. opal-brain SKILL.md:191 — "⚠️ synthesis는 query 파생물 — ingest-scan 미대상이라 init로 복구 불가 → 유실 방지 필수" 명시. opal-brain SKILL.md:194 — "⚠️ `//opbr init --force` 만으로는 `pages/`가 보존되어 재생성되지 않는다 (`brain_tool.py:436-440` `exist_ok=True`)" 명시. |

#### S-5: citation-rules §8.5 정합

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3(연결) |
| 대상 | `opal/core/references/harness/citation-rules.md` §8.5 |
| 계층 | L1 |
| **실행 방식** | **M1 (파일 검사)** |
| 조건 | EXECUTE M-5 완료 후 |
| 기대 결과 | §8.5 brain ingest 워커 항목이 §8.2(코드 식별자 본문 주어 금지)·§8.8(부록 분리)을 명문화하고, opal-brain init entity 경로 연결 항목이 추가됨. 변경 내용과 모순 없음 |
| 도구 | read |
| 실행 명령 | `grep -n "brain ingest 워커\|brain init 시드\|§8.2.*§8.8\|소스 커버리지 부록" opal/core/references/harness/citation-rules.md` |
| 결과 | **Pass** |
| 상세 | citation-rules.md:365 — "brain ingest 워커: `opal/skills/op-brain-ingest/SKILL.md` STEP 4 entity 작성 규칙이 §8.2(코드 식별자 본문 주어 금지)·§8.8(부록 분리)을 명문화한다." 명시. citation-rules.md:366 — "brain init 시드: `opal/skills/opal-brain/SKILL.md` 핵심 엔티티 시드 entity 작성 규칙이 §8.2·§8.8을 명문화한다 (소스 커버리지 부록 분리)." 신규 항목 추가됨. v2.3 변경이력(citation-rules.md:424)에서도 038 태스크 반영 확인. |

#### S-6: brain-tool pytest 회귀 (섹션 개명 안전성)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | `opal/tools/brain-tool/tests/test_brain_tool.py` |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | M-4 `## 코드 참조`→`## 소스 커버리지` 개명 반영 후 |
| 기대 결과 | `pytest opal/tools/brain-tool/tests/` 전체 통과 — add-page는 파일명으로 템플릿 로드하고 내부 섹션명을 검증하지 않으므로 **회귀 0** |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/brain-tool/tests/ -v` |
| 결과 | **Pass** |
| 상세 | 109개 테스트 전체 통과(109 passed in 0.51s). Python 3.14.3, pytest-9.1.0. 섹션 개명(`## 소스 커버리지`) 후에도 brain-tool add-page가 파일명 기반 템플릿 로드로 내부 섹션명 미검증 — 회귀 0 확인. |

#### S-8: ingest --all drift 정정

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | `opal-brain/SKILL.md` ingest --all 배치 정책 표 |
| 계층 | L1 |
| **실행 방식** | **M1 (grep + brain_tool.py 대조)** |
| 조건 | EXECUTE M-1b 완료 후 |
| 기대 결과 | "코드 @header → entity" 행이 코드 현실(ingest-scan은 docs/skills/tasks→concept만, `brain_tool.py:1082-1135`)에 맞게 정정됨 — 죽은 행 제거 또는 정확한 설명으로 교체 |
| 도구 | grep |
| 실행 명령 | `grep -n "코드 @header\|ingest --all 미해당\|ingest-scan.*docs\|brain_tool.py:1082" opal/skills/opal-brain/SKILL.md` |
| 결과 | **Pass** |
| 상세 | opal-brain SKILL.md:258 — "코드 @header" 행이 `| 코드 @header | — | **ingest --all 미해당** — entity는 `//opbr init` 시드 경로에서만 생성됨. ingest-scan은 docs/skills/tasks→concept만 스캔하며 코드→entity 분기가 없다 (`brain_tool.py:1082-1135`) |`로 정정됨. 이전 버전의 잘못된 "entity / @header 필드 흡수" 행이 코드 현실(ingest-scan 미스캔) 반영으로 교체됨. git diff 확인: 이전 `| 코드 @header | entity | @header 필드 흡수 + ...` → 정정 완료. |

#### S-9: §8.9 충돌 없음 (5섹션 헤딩 형식)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | 5섹션 표준 헤딩 (3파일) |
| 계층 | L1 |
| **실행 방식** | **M1 (grep — 헤딩 형식 대조)** |
| 조건 | EXECUTE M-1·M-3·M-4 완료 후 |
| 기대 결과 | 헤딩이 `## 누가` / `## 왜` / `## 어떻게` 형식이 **아님** (도메인 의미 헤딩 + 괄호 보조 레이블). §8.9 비위반 근거가 SKILL 본문에 1줄 주석으로 부기됨 |
| 도구 | grep |
| 실행 명령 | `grep -rn "^## 누가\|^## 왜\|^## 어떻게\|8.9 비위반" opal/skills/opal-brain/SKILL.md opal/skills/op-brain-ingest/SKILL.md opal/tools/brain-tool/templates/page-entity.md` |
| 결과 | **Pass** |
| 상세 | 3파일 모두 `## 누가`, `## 왜`, `## 어떻게` 형식 헤딩 없음(부정 grep 결과 없음). §8.9 비위반 근거 주석 확인: opal-brain SKILL.md:136, op-brain-ingest SKILL.md:177, page-entity.md:34,46,54 (각 섹션별 주석). |

### L3. 사용자 협업 (수동, [SUPERVISOR] 마커)

#### S-7: 개선 SKILL로 entity 1건 재생성 시연 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1, H-5, H-6 |
| 대상 | 개선된 init 시드 규율의 **실제 행동 변화** (전사 → 합성) |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업)** — WHY 합성 품질·provenance 적정성은 의미 판정이라 캡틴 확인 필요 |
| 조건 | Step 6에서 `opal/` 소스를 install 재배포한 뒤, 시연용 brain에서 entity 1건을 `//opbr init`(또는 단건 ingest)로 재생성 |
| 기대 결과 | 재생성된 entity가 ① 5섹션 구조 준수 ② `## 설계 배경 (WHY)`에 provenance 3종 중 하나가 실제 명시 ③ 코드 식별자가 본문 주어가 아닌 `## 소스 커버리지` 부록에 배치 ④ @header 기계 전사가 아닌 합성된 서술 |
| 실행자 | [SUPERVISOR] — 캡틴 수동 확인 필요 |
| 결과 | **Pass** (캡틴 확인, 2026-06-23) |
| 상세 | 방법 A 경량 시연(배포 불요·실 brain 미변경) — 개선된 소스 SKILL 5섹션 규율로 state-tool entity 시연본 생성(`S7-시연-state-tool-entity.md`). 캡틴 4종 체크 PASS: ① 5섹션 ② WHY provenance 근거3·추론1·**미확보1**(task 134 폴더 삭제분 솔직 표기) ③ 코드 식별자 12심볼 소스 커버리지 부록 분리 ④ @header 전사 아닌 책임 단위 합성. 구버전(4섹션·provenance 없음·exports frontmatter only) 대비 행동 변화 실측 확인. |

**PM 표준 요청 양식 (S-7)**:
```
캡틴, [시나리오 S-7]은 사용자 협업 검증이 필요합니다.
요청 내용: 개선된 SKILL 배포 후, 시연용 brain에서 entity 1건을 재생성(//opbr init 또는 단건 ingest)
기대 결과: 재생성 entity가 (1) 5섹션 구조 (2) WHY에 provenance 3종 중 하나 명시 (3) 코드 식별자가 소스 커버리지 부록에 분리 (4) @header 전사 아닌 합성
확인 후 결과(PASS/FAIL + 상세)를 알려주세요.
```

---

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| R-1 AC | H-1, H-3 | L1 | S-1, S-9 | (grep 검사) | entity 5섹션 표준 + @header 전사 금지 |
| R-2 AC | H-1, H-5, H-6 | L1 | S-2 | (grep 검사) | 큐레이션 선행 + provenance 3종 [MUST] |
| R-3 AC | H-5 | L1 | S-3 | (git diff) | 도구 무변경 (SKILL 절차 채택) |
| R-4 AC | H-2, H-8 | L1 | S-4 | (파일 검사) | 재생성 런북 + 유실 리스크 |
| R-5 AC | H-3 | L1 | S-5 | (파일 검사) | §8.5 정합 |
| R-1·R-3 회귀 | H-4 | L1 | S-6 | `test_brain_tool.py`:전체 | 섹션 개명 회귀 0 |
| 완료기준 ④ 시연 | H-1, H-5, H-6 | L3 | S-7 | (시연·캡틴 확인) | 행동 변화 실측 |
| drift 정합 | H-7 | L1 | S-8 | (grep) | ingest --all 표 정정 |

---

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | markdownlint-cli2 (npx) | **허용** | 프로젝트 .markdownlint 설정 파일 없음(strict 기본값). MD013(line-length) · MD031(blanks-around-fences) · MD040(fenced-code-language) · MD060(table-column-style) 등이 기존 SKILL.md 파일들과 동일하게 보고됨 — 기존 파일(opal-pm.md 등) 대비 회귀 없음. OPAL Markdown 관행(긴 한국어 문장·코드펜스 스타일)과 markdownlint strict 기본값 불일치이며 프로젝트 공통 이슈로 신규 도입 없음. |
| 2 | 타입 체크 | N/A | **Pass** | 도구 코드 무변경(S-3 Pass) — brain_tool.py 수정 없어 Python 타입 체크 해당 없음 |
| 3 | 포맷터 | N/A | **Pass** | 변경 대상 파일은 Markdown 문서 4종. 포맷터(Prettier 등) 미설정 프로젝트 — 해당 없음 |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | **Pass** | 변경 4파일(opal-brain SKILL.md / op-brain-ingest SKILL.md / page-entity.md / citation-rules.md) — API key / password / token / secret 하드코딩 없음 확인(grep -rniE 검사). Markdown 문서만 변경 |
| 2 | .gitignore 확인 | **Pass** | 신규 파일 없음 — 기존 4파일 내용 변경만. .gitignore 검토 불필요 |
| 3 | brain-tool 단방향 보존 | **Pass** | `wiki→origin 역수정 금지` 문구 보존 확인: opal-brain SKILL.md:206 `[MUST] 단방향 동기화 — origin→wiki 읽기만. wiki→origin 역수정 금지.` · opal-brain SKILL.md:452 `brain → 코드 역방향 수정은 절대 금지` · op-brain-ingest SKILL.md:19 단방향 선언 — 모두 훼손 없음 |

## 7. 판정

**All Pass — L1 시나리오 8건 전원 Pass + S-7 [SUPERVISOR] L3 캡틴 확인 Pass (2026-06-23)**

L1 시나리오 전수 결과:

| 시나리오 | 결과 | 비고 |
|---------|------|------|
| S-1 | Pass | 3파일 5섹션 동일 + @header 전사 금지 [MUST] 기재 확인 |
| S-2 | Pass | 큐레이션 선행 4단계 + provenance 3종 [MUST] 명문화 확인 |
| S-3 | Pass | git diff brain_tool.py 빈 결과 — 도구 무변경 확인 |
| S-4 | Pass | 런북 4단계(①②③④) + --force 미삭제 한계 ⚠️ + synthesis 유실 ⚠️ 명시 확인 |
| S-5 | Pass | §8.5 brain ingest·init 워커 항목에 §8.2·§8.8 명문화 + init entity 경로 신규 추가 확인 |
| S-6 | Pass | pytest 109 passed / 0 failed — 섹션 개명 회귀 없음 |
| S-7 | **Pass** | L3 [SUPERVISOR] — 캡틴 확인(2026-06-23): 시연본 4종 체크 PASS, 행동 변화(전사→합성·provenance) 실측 |
| S-8 | Pass | "코드 @header → —(ingest --all 미해당)" 정정 확인 (`brain_tool.py:1082-1135` 주석 포함) |
| S-9 | Pass | 3파일 모두 `## 누가/왜/어떻게` 형식 없음 + §8.9 비위반 근거 주석 부기 확인 |

보안 §6 — Pass (시크릿 없음 · 단방향 문구 보존).
코드 품질 §5 — Markdown lint 기존 관행과 동일 수준 (신규 회귀 없음).

### PM Gate 체크 (7대 강제 룰)

- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 (grep/pytest/시연만 사용)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전 (H-1~H-8 모두 시나리오 매핑)
- [x] L1/L3 계층 명시 (모든 시나리오 — L2 해당 없음: DB·프로세스 통합 없음)
- [x] L3 [SUPERVISOR] 마커 존재(S-7) + PM 요청 양식 첨부
- [x] 리스크 가설 표(§1) H-N ID와 시나리오 S-N 매핑 완전
- [x] 모든 시나리오에 실행 방식(M1/M3) 명시
