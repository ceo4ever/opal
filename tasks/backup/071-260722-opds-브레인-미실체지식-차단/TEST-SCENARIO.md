# TEST SCENARIO: 브레인 미실체 지식 등록 차단 게이트

> 작성일: 2026-07-22 | 상태: PLAN 통합 산출(§5/§6/판정은 TEST 단계에서 채움)
> 작성자: opal-plan-agent | PLAN.md §리스크 가설 표(H-1~H-10) 기반
> **RED-first 판정: RED-first 트랙 ON (`verify --red-check` ON)**. 근거 — 이번 변경은 **도구 동작 변경**(add-page 미실체 거부·lint 신규 kind 검출)으로 `opal/core/references/harness/red-first.md` §1.5 "self-confirming 위험 높음(버그 수정/회귀 방지·API 계약)" 카테고리에 해당. 실패 테스트를 **먼저** 작성·실행(exit≠0 증거)한 뒤 GREEN 구현으로 진입한다. **작성자≠구현자**(§2): RED = opal-test-agent(mode: red), GREEN = op-dev-execute(opal-be-agent). GREEN/fix 중 RED 테스트 수정 금지(§3). 검증은 **공개 인터페이스**(CLI JSON `ok`/`error`/`issues`/`markers`)로만(§4). **mock 금지** — 실 `brain_tool.py` import + tmpdir 격리.

## 1. 리스크 가설 표

> PLAN.md §리스크 가설 표(H-1~H-10) 승계.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | `detect_speculative_markers` (F-002) | 오검출(FP) — 정착 헤딩이 마커 토큰 부분 포함 → 정당 지식 거부 | P1 | L1 | S-4, S-7 |
| H-2 | add-page `--body-file` 접합 (F-001↔F-002) | 스킬이 템플릿 본문으로 add-page → 본문 미스캔 → 게이트 무력화 | P1 | L2 | S-6, S-11 |
| H-3 | `--force` 우회 정책 (F-002) | `--force`만(note 없이) 통과 → 백도어 | P1 | L1 | S-2, S-3 |
| H-4 | lint `speculative` kind (F-002) | 정상 active concept 과검출 / 미실체 미검출 | P1 | L1 | S-6, S-7 |
| H-5 | add-page 거부의 CLOSE 영향 (F-002↔ingest) | `speculative_content` 거부가 hard-fail → CLOSE 중단 | **P0** | L2 | S-10 |
| H-6 | 하위호환 (F-002) | `--body-file` 없는 기존 호출 회귀 | P1 | L1 | S-5, S-12 |
| H-7 | frontmatter 신규 키 (F-002) | `speculative_override`/`override_note`가 validate/index 파손 | P2 | L1 | S-3, S-12 |
| H-8 | draft-term 불변 (M-3) | `_score_page` term 한정 draft 필터 손상 → query 진입점③ 회귀 | P1 | L1 | S-9 |
| H-9 | 배포 경계 (F-004) | `~/.opal/` 직접 수정 / install 누락 → drift | P1 | L3 | S-13 |
| H-10 | 추적성 (F-001/002) | @header `[071]`·변경이력 누락 | P2 | L1 | S-11, S-12 |

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터

> DB 없음(도구·문서 태스크). tmpdir 격리 fixture + 실증 등가 콘텐츠로 구성. **mock 금지·실측 기반**(실 `brain_tool.py` 호출).

| 대상 | 식별자 | 상태 | 출처 |
|------|--------|------|------|
| 미실체 본문 fixture (concept) | `## 개요` + `## 구현 영향 범위 (HOW) — 아직 미착수, 설계 기록 단계` + `## 미확정 이슈` (type:concept status:active) | 테스트 내 직접 write | pointail `direct-delivery-mission-design.md` 등가 (TASK §실증 케이스) |
| 정상 본문 fixture (concept) | `## 개요` + `## 결정 내용 (HOW)` + `## 영향·관계` (마커 0, sources 有) | 테스트 내 직접 write | page-concept 템플릿 정착 구조 (→ D-10) |
| 미실체 body-file (스크래치) | tmpdir `spec-body.md` (미실체 헤딩 포함) | 테스트 내 작성 | add-page `--body-file` 입력 |
| 정상 body-file (스크래치) | tmpdir `clean-body.md` (마커 0) | 테스트 내 작성 | add-page `--body-file` 입력 |
| draft term fixture | `pages/term/*.md` status:draft (`_write_term_page`) | 테스트 내 직접 write | M-3 불변 회귀 |
| 신규 코드 | `opal/tools/brain-tool/brain_tool.py` (`detect_speculative_markers`·게이트) | EXECUTE Step2 산출 | EXECUTE |
| SSOT 스킬 | `opal/skills/{op-brain-ingest,opal-brain}/SKILL.md` | EXECUTE Step3 산출 | EXECUTE |
| 배포본 | `~/.opal/tools/brain-tool/brain_tool.py` | Step6(배포) 산출 | install |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (준비) | When (실행) | Then (관찰) |
|---------|------------|----------------|---------------|
| S-1 | init된 tmpdir brain + 미실체 body-file | `cmd_add_page(--body-file 미실체, force=False)` | ok:false + error=`speculative_content` + markers 비어있지 않음 |
| S-2 | 동상 | `cmd_add_page(--body-file 미실체, force=True, note=None)` | ok:false — note 필수 거부 |
| S-3 | 동상 | `cmd_add_page(--body-file 미실체, force=True, note="캡틴 승인")` | ok:true + warning + 생성 페이지 frontmatter `speculative_override:true`/`override_note` |
| S-4 | init + 정상 body-file | `cmd_add_page(--body-file 정상)` | ok:true(거부 없음), 페이지 생성 |
| S-5 | init | `cmd_add_page(body_file=None)` (기존 호출) | ok:true + 템플릿 본문 생성(하위호환) |
| S-6 | 미실체 concept 직접 write(active) | `cmd_lint` | issues에 kind=`speculative` (page=fixture) |
| S-7 | 정상 active concept 직접 write | `cmd_lint` | issues에 `speculative` 미출현 |
| S-8 | `speculative_override:true` 페이지 write | `cmd_lint` → 재Read | 여전히 리포트 + 페이지 파일 내용 불변(삭제·수정 0) |
| S-9 | draft term fixture(`_write_term_page` status:draft) | `cmd_search(query, include_draft=False)` | draft term 미노출(M-3 불변) |
| S-10 | op-brain-ingest SKILL | 에러 대응 표 grep | `speculative_content` skip-and-continue 행 존재(CLOSE 비차단 명문) |
| S-11 | 두 SKILL + README | grep(미실체 행/SSOT 참조/`--body-file`/lint speculative 행/변경이력 071) | 전부 존재 + opal-brain 재정의 부재 |
| S-12 | 전체 테스트 스위트 | `pytest test_brain_tool.py -v` | 신규+기존 All Pass, 회귀 0 |
| S-13 | 배포본 경로 | install 후 grep/Read | `speculative`/`body-file` 반영 + 소스 일치 |

## 3. 검증 시나리오

### L1. 기능 단위 (자동, RED→GREEN / 실 도구·실 파일)

#### S-1: add-page 미실체 본문 거부 (TS-201)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1(정탐측), F-002 AC (R-3) |
| 대상 | `cmd_add_page` + `detect_speculative_markers` |
| 계층 | L1 |
| 실행 방식 | **M1 (pytest — 실 brain_tool 호출)** |
| RED 조건 | 함수/인자 부재 → import/AttributeError 또는 미거부로 실패 |
| 기대 결과 | 미실체 헤딩 body-file로 add-page → `ok:false`, `error=="speculative_content"`, `markers` 비어있지 않음, 페이지 파일 미생성 |
| 도구 | pytest, tmpdir |
| 실행 명령 | `pytest opal/tools/brain-tool/tests/test_brain_tool.py -k SpeculativeGate071 -v` |
| 결과 | **Pass** — `test_add_page_rejects_speculative_body_file` PASSED. 실측: `exit_code≠0`, `result["ok"]==False`, `result["error"]=="speculative_content"`, `result["markers"]` 비어있지 않음, `pages/concept/spec-reject-page.md` 미생성 확인(전 assertion 통과) |

#### S-2: `--force` note 없으면 거부 (TS-202)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3, F-002 AC (R-3) |
| 대상 | `cmd_add_page` force 분기 |
| 계층 | L1 |
| 실행 방식 | **M1 (pytest)** |
| 기대 결과 | `force=True, note=None` → 여전히 `ok:false`(백도어 차단), note 필수 메시지 |
| 실행 명령 | 상동 `-k SpeculativeGate071` |
| 결과 | **Pass** — `test_add_page_force_without_note_still_rejected` PASSED. 실측: `force=True, note=None` 조합에서도 `exit_code≠0`, `result["ok"]==False`, `pages/concept/spec-force-only-page.md` 미생성 — note 없는 `--force` 단독 백도어 우회 없음 확인 |

#### S-3: `--force --note` 우회 + 경고 기재 (TS-203)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3, H-7, F-002 AC (R-3) |
| 대상 | `cmd_add_page` override 경로 + frontmatter |
| 계층 | L1 |
| 실행 방식 | **M1 (pytest)** |
| 기대 결과 | `force=True, note="<사유>"` → `ok:true` + 응답 `warning`/`speculative_markers`/`override_note` + 생성 페이지 frontmatter에 `speculative_override:true`·`override_note` 기록 |
| 실행 명령 | 상동 |
| 결과 | **Pass** — `test_add_page_force_with_note_overrides_and_records` PASSED. 실측: `exit_code==0`, `result["ok"]==True`, 응답에 `warning`/`speculative_markers`/`override_note`(값 일치) 포함, 생성된 `pages/concept/spec-override-page.md` frontmatter에 `speculative_override:true`·`override_note` 기재 확인(파싱 검증) |

#### S-4: 정상 concept 본문 통과 — 오검출 없음 (TS-204)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1(오탐측), F-002 회귀 |
| 대상 | `detect_speculative_markers` FP 경계 |
| 계층 | L1 |
| 실행 방식 | **M1 (pytest)** |
| 기대 결과 | 정상 정착 헤딩(마커 0) body-file → `ok:true`, 거부 없음. 산문에 "향후" 단순 언급 포함해도 미거부(구조적 신호 우선) |
| 실행 명령 | 상동 |
| 결과 | **Pass** — `test_add_page_normal_body_file_passes` PASSED. 실측: `exit_code==0`, `result["ok"]==True`, `pages/concept/normal-body-page.md` 생성 확인 — 정상 정착 본문(산문 "향후" 단순 언급 포함)에서 오검출 없음(H-1 방어 확인) |

#### S-5: `--body-file` 미지정 하위호환 (TS-205)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6, F-002 하위호환 |
| 대상 | `cmd_add_page` 기존 경로 |
| 계층 | L1 |
| 실행 방식 | **M1 (pytest)** |
| 기대 결과 | `body_file=None`(기존 호출) → 템플릿 본문으로 정상 생성 `ok:true`, 마커 스캔이 템플릿에 미발동(거부 0) |
| 실행 명령 | 상동 |
| 결과 | **Pass** — `test_add_page_without_body_file_backward_compat` PASSED. 실측: `body_file` 미지정 기존 호출에서 `exit_code==0`, `result["ok"]==True`, `pages/concept/legacy-page.md` 생성 — 하위호환 회귀 없음(H-6 확인) |

#### S-6: lint 미실체 소급 검출 (TS-206)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4(정탐), H-2(backstop), F-002 AC (R-4) |
| 대상 | `cmd_lint` `speculative` kind |
| 계층 | L1 |
| 실행 방식 | **M1 (pytest — pointail 등가 fixture 직접 write)** |
| 기대 결과 | concept/active + 미실체 헤딩("아직 미착수, 설계 기록 단계"/"미확정 이슈") 페이지 → lint `issues`에 `{"kind":"speculative","page":...,"markers":[...]}` 포함 |
| 실행 명령 | 상동 |
| 결과 | **Pass** — `test_lint_detects_speculative_concept_page` PASSED. 실측: pointail 등가 fixture(`pointail-equiv`, concept/active) 직접 write 후 lint 실행 → `issues`에 `kind=="speculative", page=="pointail-equiv"` 항목 존재, `markers` 비어있지 않음(소급 검출 확인, backstop 정탐) |

#### S-7: lint 정상 active 오탐 없음 (TS-207)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4(오탐측), H-1 |
| 대상 | `cmd_lint` FP 경계 |
| 계층 | L1 |
| 실행 방식 | **M1 (pytest)** |
| 기대 결과 | 정상 active concept(마커 0) → lint issues에 `speculative` 미출현(기존 kind는 정상 동작) |
| 실행 명령 | 상동 |
| 결과 | **Pass** — `test_lint_no_false_positive_on_normal_concept` PASSED. 실측: `normal-active-concept` fixture(마커 0) lint 실행 → 해당 페이지 issues에 `speculative` kind 미출현 확인(H-4 오탐측 회귀 없음) |

#### S-8: lint 비파괴 — override 리포트 + 페이지 불변 (TS-208)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7, F-002(하위호환 제약: lint 검출까지만) |
| 대상 | `cmd_lint` + 파일 불변성 |
| 계층 | L1 |
| 실행 방식 | **M1 (pytest — 실행 전후 파일 바이트 비교)** |
| 기대 결과 | `speculative_override:true` 페이지 → lint가 여전히 리포트(+override 부기), 페이지 파일 내용은 lint 실행 전후 **동일**(자동 삭제·수정 0) |
| 실행 명령 | 상동 |
| 결과 | **Pass** — `test_lint_override_page_still_reported_and_unchanged` PASSED. 실측: `speculative_override:true` 기재 페이지에서도 lint issues에 `kind=="speculative"` 여전히 리포트됨 + lint 실행 전후 페이지 파일 바이트 비교(`before_bytes == after_bytes`) 동일 — 비파괴 확인 |

#### S-9: draft-term 불변 (M-3) (TS-209)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8, M-3 |
| 대상 | `_score_page` term 한정 draft 필터(`brain_tool.py:619-629`) |
| 계층 | L1 |
| 실행 방식 | **M1 (pytest 회귀)** |
| 기대 결과 | status:draft term 페이지가 기본 search(`include_draft=False`)에서 제외 유지. 미실체 게이트 도입이 이 경로를 변경하지 않음 |
| 실행 명령 | 상동 + 기존 `TestTermDraft027` 회귀 |
| 결과 | **Pass** — `test_search_draft_term_excluded_default_m3_regression` PASSED + 기존 `TestTermDraft027`(6건) 전부 PASSED(전체 실행 로그 참조). 실측: `m3-draft-term`(status:draft) 페이지가 `include_draft=False` 기본 search 결과(`matches`)에서 제외됨 확인 — `_score_page` term 한정 draft 필터([R-6] 2026-06-17) 무변경 회귀 |

#### S-10: op-brain-ingest CLOSE 비차단 명문 (TS-103 일부)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-5 (P0)**, F-001 AC (R-1) |
| 대상 | `opal/skills/op-brain-ingest/SKILL.md` 에러 대응 표 |
| 계층 | L2 |
| 실행 방식 | **M1 (grep)** |
| 기대 결과 | 에러 대응 표에 `speculative_content` → "skip-and-continue / CLOSE 비차단" 행 존재. `duplicate_page`/"그 외 ok:false" 정책과 정합. "어떤 에러도 CLOSE를 중단시키지 않는다" 문구 유지 |
| 실행 명령 | `grep -nE "speculative_content\|skip\|CLOSE" opal/skills/op-brain-ingest/SKILL.md` |
| 결과 | **Pass** — grep 실행 결과 line 298: `` `speculative_content` \| 미실체 마커 감지 거부. 해당 페이지를 건너뛰고 나머지 계속 진행(skip-and-continue). **CLOSE 비차단** `` 행 존재. line 301: "어떤 에러도 CLOSE를 중단시키지 않는다." 문구 유지. line 36 "CLOSE를 막지 않는다"·line 285 "CLOSE 단계를 막아서는 안 된다"와 정합 확인 |

#### S-11: SSOT 스킬 명문화 + 접합 grep (TS-101/102/103)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2, H-10, F-001 AC (R-1·R-2) |
| 대상 | 두 SKILL.md + README |
| 계층 | L1 |
| 실행 방식 | **M1 (grep)** |
| 기대 결과 | ① op-brain-ingest §STEP3 제외 기준에 미실체 행 + 예시(개선·오류·향후·미확정 설계) ② opal-brain ingest 절이 "op-brain-ingest §STEP3 SSOT 참조"(재정의 부재) + lint 표 `speculative` 행 ③ 두 SKILL add-page 예시에 `--body-file` ④ 변경이력 `(071)` ⑤ README에 `--force`/`--note`/`--body-file`/`speculative` |
| 실행 명령 | `grep -nE "미실체\|speculative\|body-file\|071" opal/skills/op-brain-ingest/SKILL.md opal/skills/opal-brain/SKILL.md opal/tools/brain-tool/README.md` |
| 결과 | **Pass** — 3파일 실측 grep 결과: ① op-brain-ingest §STEP3 제외 기준 표(line 76)에 "미실체 지식" 행 + 예시(개선사항·오류·향후 계획·미확정 설계) + 판별 신호(line 78, 구조적 헤딩 우선) 존재. ② opal-brain(line 210) "미실체 제외 — op-brain-ingest §STEP3 제외 기준을 SSOT로 재사용한다(별도 정의하지 않음)" — 재정의 부재 확인 + lint kind 표(line 500)에 `speculative` 행 존재. ③ 두 SKILL add-page 예시(op-brain-ingest line 226/234, opal-brain line 229/234/294/299)에 `--body-file` 반영. ④ 변경이력 `(071)`: op-brain-ingest line 315(v1.6), opal-brain line 578(v1.9). ⑤ README(line 51/56-61/112-115/139)에 `--force`/`--note`/`--body-file`/`speculative_content`/`speculative` kind 전부 반영 |

### L2. 프로세스 통합 (자동 — 실 도구·실 파일)

#### S-12: 전체 pytest 회귀 0 (TS-301)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6, H-7, H-10, F-003 AC (R-5) |
| 대상 | `test_brain_tool.py` 전체 |
| 계층 | L2 |
| 실행 방식 | **M2 (pytest 전량 실행)** |
| 기대 결과 | 신규 `TestSpeculativeGate071`(TS-201~209) All Pass + 기존 전 클래스(TestAddPage/TestLint/TestSearch/TestValidate/TestTermDraft027/TestTermLint027 등) 무회귀. exit 0 |
| 도구 | pytest |
| 실행 명령 | `pytest opal/tools/brain-tool/tests/test_brain_tool.py -v` |
| 결과 | **Pass** — 실행 출력: `127 passed in 0.57s`, exit 0. 신규 `TestSpeculativeGate071` 9건(TS-201~209) 전부 PASSED + 기존 전 클래스(TestInit/TestAddPage/TestIndex/TestLog/TestSearch/TestSyncHeader/TestLint/TestValidate/TestErrorCodes/TestDynamicPageTypes/TestAnalyze/TestIngestScan/TestValidateFrontmatter/TestValidateFlatness035/TestTermDraft027/TestTermLint027) 118건 전부 PASSED — 회귀 0 확인 |

### L3. 사용자 협업 (수동, [SUPERVISOR] 마커)

#### S-13: install 재배포 + 배포본 검증 (TS-401) [SUPERVISOR]
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9, F-004 AC (R-6) |
| 대상 | `./scripts/install-mac.sh` 실행 (배포 = 사람 게이트) |
| 계층 | L3 |
| 실행 방식 | **M3 (사용자 협업 — 캡틴 승인 후 PM 대행 가능)** |
| 조건 | S-1~S-12 통과 후, 캡틴 배포 승인 |
| 기대 결과 | 배포 후 `~/.opal/tools/brain-tool/brain_tool.py` grep `speculative`·`body-file` 매칭 + 소스와 일치(변경이력 strip 제외). 배포 SKILL 2종 소스 일치 |
| 실행자 | [SUPERVISOR] — 캡틴 승인 필요 (`docs/CONVENTIONS.md` §배포 경계) |
| 실행 명령 | `./scripts/install-mac.sh` → `grep -c "speculative" ~/.opal/tools/brain-tool/brain_tool.py` |
| 결과 | **미실행 — 캡틴 배포 승인 대기(SUPERVISOR 게이트)**. S-1~S-12 전부 Pass 확인됨. `docs/CONVENTIONS.md` §배포 경계에 따라 `~/.opal/` 배포는 캡틴 승인 후 PM이 직접 실행하는 사람 게이트로, 본 TEST 단계(opal-test-agent)는 실행하지 않음. `git status` 확인 결과 `~/.opal/` 하위 직접 수정 0건(소스 `opal/` 경로만 변경) |

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스(계획) | 비고 |
|-------|---------|---------|---------|-----------------------|------|
| R-3 (미실체 거부) | H-1 | L1 | S-1 | test_brain_tool.py:TestSpeculativeGate071 | TS-201, RED |
| R-3 (force note 필수) | H-3 | L1 | S-2 | 〃 | TS-202, RED |
| R-3 (force+note 우회) | H-3,H-7 | L1 | S-3 | 〃 | TS-203, RED |
| R-3 (정상 통과) | H-1 | L1 | S-4 | 〃 | TS-204, 회귀 |
| R-3 (하위호환) | H-6 | L1 | S-5 | 〃 | TS-205, 회귀 |
| R-4 (lint 검출) | H-4,H-2 | L1 | S-6 | 〃 | TS-206, RED |
| R-4 (오탐 없음) | H-4,H-1 | L1 | S-7 | 〃 | TS-207, 회귀 |
| R-4 (비파괴) | H-7 | L1 | S-8 | 〃 | TS-208, RED |
| M-3 (draft 불변) | H-8 | L1 | S-9 | 〃 + TestTermDraft027 | TS-209, 회귀 |
| R-1 (CLOSE 비차단) | H-5 | L2 | S-10 | op-brain-ingest SKILL(grep) | TS-103 |
| R-1·R-2 (SSOT 명문화) | H-2,H-10 | L1 | S-11 | 2 SKILL + README(grep) | TS-101/102/103 |
| R-5 (회귀 0) | H-6,H-10 | L2 | S-12 | pytest 전량 | TS-301 |
| R-6 (배포) | H-9 | L3 | S-13 | install 실행 | TS-401, 사람 게이트 |

## 5. 코드 품질

> **회귀 가드 용도** — lint/type/포맷은 단위(EXECUTE) 위상이며 이미 EXECUTE에서 통과 전제. 아래는 TEST 단계의 중복 아닌 회귀 확인이다.

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트/구문 | `python3 -m pyflakes brain_tool.py` (가능 시) + `python3 -c "import ast; ast.parse(...)"` | **Pass** | pyflakes 미설치(venv에 모듈 부재, `No module named pyflakes`)로 ast 구문 파싱으로 대체: `ast.parse(open('opal/tools/brain-tool/brain_tool.py').read())` → 예외 없이 통과("OK - syntax valid") |
| 2 | 타입 체크 | 해당 없음(타입힌트 부분적, mypy 미도입) | N/A | - |
| 3 | 포맷터 | 기존 스타일 준수(4-space, 기존 헬퍼 패턴) | **Pass** | pytest 전체 127건 통과가 스타일 회귀 없음을 간접 확인. 코드 리뷰상 4-space 인덴트·기존 `_norm`/`ok`/`err` 헬퍼 패턴 재사용 확인(PLAN §3.2.2 설계와 일치) |
| 4 | @header/변경이력 | grep `[071]`·`(071)` | **Pass** | brain_tool.py @header description에 `[071] add-page 미실체 거부 게이트(...)...` 태그 존재, exports 배열에 `detect_speculative_markers` 등재 확인. 코드 내 `(071)` 주석 6곳(line 56,517,542,643,926,1276). 2 SKILL 변경이력 `(071)`: op-brain-ingest v1.6(line 315), opal-brain v1.9(line 578). README 변경이력 v1.2(line 139)에도 `(071)` 존재 |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | **Pass** | `grep -inE "api[_-]?key\|secret\|token.*=" opal/tools/brain-tool/brain_tool.py` → 매칭 0건(grep exit 1). `SPECULATIVE_MARKERS`(line 59-62: "미착수"·"미확정"·"향후계획" 등)는 업무 마커 문자열 확인 — 시크릿 아님 |
| 2 | 경로 처리 안전성 | **Pass** | `--body-file` 처리(brain_tool.py:519-522)는 `pathlib.Path(body_file).read_text()` — 읽기 전용, 사용자 제공 경로를 그대로 열람만 함. 쓰기는 `path`/`type` 인자로 파생된 대상 페이지 경로(`pages/{type}/{name}.md`)에 한정 — 임의 경로 write 부작용 없음 |
| 3 | 배포 경계 | **Pass** | `git status` 확인 결과 이번 태스크 변경 파일 전부 `opal/` 소스 경로(`opal/tools/brain-tool/brain_tool.py`, `tests/test_brain_tool.py`, `opal/skills/{op-brain-ingest,opal-brain}/SKILL.md`, `opal/tools/brain-tool/README.md`) — `~/.opal/` 배포본 직접 수정 0건 |

## 7. 판정

> All Pass 기준: L1(S-1~S-9,S-11) + L2(S-10,S-12) 전부 Pass + L3(S-13) 배포 확인 + §5/§6 Pass + 회귀 0.

**판정: All Pass** (단, S-13은 L3 SUPERVISOR 배포 게이트로 유보 — 캡틴 승인 대기, 코드/테스트/문서 산출물 자체는 전부 검증 완료)

- L1(S-1~S-9, S-11): 전부 Pass — `TestSpeculativeGate071` 9건 전부 PASSED(실행 출력 증거 §3 각 결과란 참조) + SSOT 문서 grep 3파일 전부 매칭.
- L2(S-10, S-12): 전부 Pass — op-brain-ingest 에러 대응 표 `speculative_content` skip-and-continue 행 확인(CLOSE 비차단) + 전체 pytest `127 passed, 0 failed`(exit 0), 회귀 0.
- L3(S-13): **미실행** — 배포는 사람 게이트(SUPERVISOR). 코드/테스트/문서 산출물 검증(S-1~S-12)이 전부 Pass이므로 배포 승인 조건은 충족되었으나, 실제 `./scripts/install-mac.sh` 실행은 캡틴 승인 후 PM이 별도 수행해야 함.
- §5 코드 품질: Pass (구문 유효·스타일 회귀 없음·@header/변경이력 추적성 확인).
- §6 보안: Pass (하드코딩 시크릿 0건·경로 처리 안전·배포 경계 준수).
- 목업 미잔존: 확인 — `TestSpeculativeGate071` 전 케이스가 실 `brain_tool.py` 함수(`cmd_add_page`/`cmd_lint`/`cmd_search`)를 tmpdir 격리 상에서 직접 호출(테스트 코드 본문 열람 확인, mock/patch/MagicMock 부재, `_mock_kst()`만 예외적 허용 — 기존 정책과 동형).

### PM Gate 체크 (7대 강제 룰)
- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 (실 `brain_tool` import + tmpdir·실 파일만; KST만 격리 목적 `_mock_kst()` 허용 — 기존 테스트 정책 `test_brain_tool.py:22-23`) — `TestSpeculativeGate071` 소스 열람으로 확인
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전 (H-1~H-10 전부 매핑)
- [x] L1/L2/L3 계층 명시 (S-1~9,11=L1 / S-10,12=L2 / S-13=L3)
- [x] L3 [SUPERVISOR] 마커 + 캡틴 협업 명시 (S-13)
- [x] 실행 방식(M1/M2/M3) 전 시나리오 명시
- [x] **RED-first 전용**: RED 증거(exit≠0) 선확보 + 작성자(opal-test-agent)≠구현자(op-dev-execute) + RED 테스트 불변성 — Step1(opal-test-agent) RED 작성 → Step2(opal-be-agent) GREEN 구현 분리는 PLAN.md §4.2 실행 이력으로 확인. 본 TEST 단계는 RED 테스트 파일 무수정(검증만 수행, brain_tool.py·test_brain_tool.py 미변경 확인)
