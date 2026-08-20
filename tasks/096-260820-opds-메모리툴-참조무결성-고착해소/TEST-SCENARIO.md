# TEST SCENARIO: memory-tool 참조 무결성 검사 + 본문 부재 행 고착 해소

> 작성일: 2026-08-20 | 상태: 작성 완료 (Block A 선작성 → Block B 보강 완료)
> 작성자: 알투(PM) + 캡틴 페어 | 도출 트랙: 목표계열 선작성 (`opal/core/references/harness/red-first.md` §1.6)

## 0. 도출 트랙 기록

**착수 판단** (§1.6 (f) 기준 적용):

| 조건 | 096 판정 | 근거 |
|------|---------|------|
| PLAN 워커 예상 소요 > 선작성 소요 | ✓ 선작성 유리 | 실측 — PLAN 워커 998초(약 16분 39초), tool_uses 35회. 선작성 소요는 그 구간에 은닉 |
| 목표가 파괴 관점으로 환원되지 않는다 | ✓ 선작성 유리 | R-2 핵심 AC가 **음성 통제**, R-3이 목표 달성 판정 |
| 단일 결함 수정이다 | ✗ 해당 없음 | 결함 3건 + 검증·배포 |
| 교체형 목표다 | ✗ 해당 없음 | 신설·보강. 루브릭 ⑤는 **N/A** — "기존 무손실 가드의 잔존"을 준용 검증 |

**Block A 도출 입력** (TASK.md 유래 3종만 — PLAN.md 미열람 상태에서 도출): 목표 문장 / 요구사항 R-1~R-4 / (교체형 아님)

**Block B 도출 입력** (PLAN.md 유래): §1.2 기능 목록 F-001~F-004 / §리스크 가설 표 H-1~H-11

### 보강 이력

| # | 조치 | 대상 | 사유 |
|---|------|------|------|
| 1 | **삭제(흡수)** | 선작성 S-1~S-6, S-14, S-16 | PLAN TS-001~003·006~009·018·020~023이 동일 검증을 **더 정밀한 Pass 조건**으로 규정. 중복 제거 |
| 2 | **수정** | 선작성 S-15 (표==enum) — L3 `[SUPERVISOR]` → **L1 / M1** | PLAN H-7이 "문서-스키마 파리티 테스트로 **기계 집행** 전환"을 제안. 선작성은 "문서 판정이니 사람이 본다"고 가정했으나 자동화가 가능하며, 수동 판정은 H-7이 지적한 "다음 enum 변경 때 재발"을 막지 못한다 → TS-015 |
| 3 | **수정** | 선작성 S-1 (실환경) — "사본에서 수행" → **"사본 수행 + 원본 해시 전후 동일"** | PLAN TS-023이 원본 보전을 해시 대조로 강화. 선작성 기준 상향 → TS-023 |
| 4 | **해소** | 선작성 S-8 (`active` + 본문 부재 미규정 경계) | PLAN §3.2.2가 "`--orphan` 경로는 `status`를 읽지 않는다 … `active`까지 자연 포함한다 — **부분 처방 금지**"로 명시 규정. 선작성이 걸어둔 FAIL 압박이 해소됨 → TS-032로 확인 시나리오 존치 |
| 5 | **추가** | TS-004·005·010·012·013·016·017·022 | Block B(H-1·H-3·H-4·H-5·H-9) 유래 — 선작성만으로는 도출 불가 |
| 6 | **존치** | TS-024~031, TS-033 | 선작성 고유. PLAN QA 집합에 대응 없음 (§4 커버 현황 참조) |

**게이트 iteration 1 지적 반영 (2라운드)**

| # | gap | 조치 |
|---|-----|------|
| 7 | G-1 (①) | TS-021·TS-023 도구를 배포본 `run.sh` → **프로젝트 소스 직접 실행**으로 정정. 실행 시점(PLAN Step 5)이 install(Step 6)보다 앞서 구버전을 측정할 뻔했다 |
| 8 | G-2 (①) | §4 ①행에 **TS-015 추가** — 목표 3절 중 R-3(규범↔스키마 정합)이 목표달성 축에 미연결이었다 |
| 9 | **G-3 (⑤, P0)** | **TS-034·TS-035·TS-036·TS-037 신설** + TS-005 검출 어휘 정정. PLAN 재설계 1/2회차로 `memory_file_unresolvable` 신설·조기 반환 가드 확정 후 반영 |
| 10 | G-4 (⑤) | 채택 측 표지 부여 — TS-006·TS-007에 `is_adoption_scenario`. 준용 축을 잔존 한쪽으로만 표지하면 "새 경로가 실제로 동작하는가"가 축에서 빠진다 |
| 11 | 관측 1 | 초안↔최종 ID 대응 표 18행 신설, 비율 61% → **50%** 정정, 부적격 신호 발화 인정 |
| 12 | 관측 3 | PLAN ID가 `QA-NNN`으로 개명(136건)되어 번호 공간 충돌 해소 |

**게이트 iteration 2 필수 정정 반영 (3라운드 — 게이트는 pass, 채점 외 지적)**

| # | 지적 | 조치 |
|---|------|------|
| 13 | `fx-traversal` `status` 미지정 | §2.1에 `candidate` 명시 + `fx-traversal-dead`(dead) 신설. 미지정 시 TS-037 기대치가 status에 따라 갈려 워커 구성에 따라 FAIL한다 |
| 14 | **TS-037이 PLAN R-13의 과장을 인코딩** | 기대치를 **status별 분기**로 정정. 무플래그 `else` 경로는 `mem_file`을 **조회하지 않으므로** dead/superseded × 해석 불가는 **허용**이 정상이다(코드 실측 확인). 과장된 기대치를 두면 GREEN을 좇는 워커가 무플래그 경로에 가드를 추가해 PLAN이 `[MUST]`로 보존 명령한 `else` 3줄과 TS-011을 위반한다 — iteration 1 G-1과 동일한 실패 형태 |
| 15 | 위 위험의 음성 통제 부재 | **TS-038 신설** — `else` 3줄 불변을 직접 실증 |
| 16 | TS-036 fixture 미등재 | §2.1에 `fx-mixed-vocab` 등재 |
| 17 | `promote` 어휘 단절 | PLAN이 **(가) 범위 내 정정** 채택 — `cmd_promote()` `:1165-1166`의 `None` 분기를 `memory_file_unresolvable`로 교체(회귀 영향 실측 0건). TS-037 ③ 기대 코드 확정 + **TS-039 신설**(3명령 어휘 일관성, PLAN QA-026 대응) |

### 초안 ↔ 최종 ID 대응 (전 18건)

> 게이트 iteration 1 지적 반영 — 최초 기재한 "11/18(61%)"는 **오산이었다**. S-1이 흡수·수정에 이중 계상됐고, 수정·삭제 11 + 존치 9 = 20건이 분모 18을 초과했다. 아래로 정정한다.

| 초안 | 판정 | 최종 ID | 비고 |
|------|------|---------|------|
| S-1 | **수정** | TS-021 + TS-023 | 원본 해시 보전 요건 추가로 분화 (기준 상향) |
| S-2 | 흡수 | TS-001 | |
| S-3 | 흡수 | TS-002 | |
| S-4 | 흡수 | TS-003 | |
| S-5 | 흡수 | TS-006, TS-007, TS-014 | 1→3 분해 |
| S-6 | 흡수 | TS-008, TS-009 | |
| S-7 | 존치 | TS-024 | 선작성 고유 |
| S-8 | 존치(해소) | TS-032 | PLAN이 경계를 규정 → 확인 시나리오로 전환 |
| S-9 | 존치 | TS-025 | 선작성 고유 |
| S-10 | 존치 | TS-011, TS-030 | |
| S-11 | 존치 | TS-031 | 선작성 고유 |
| S-12 | 존치 | TS-019(흡수분) + TS-026(고유분) | "케이스 수 미감소"가 고유 |
| S-13 | 존치 | TS-027 | 선작성 고유 |
| S-14 | 흡수 | TS-020 | |
| S-15 | **수정** | TS-015 | L3 `[SUPERVISOR]` → L1/M1 (방향 역전) |
| S-16 | 흡수 | TS-018 | |
| S-17 | 존치 | TS-029 | |
| S-18 | 존치 | TS-028 | 선작성 고유 |

**신규 추가**(Block B 유래, 초안 대응 없음): TS-004, TS-005, TS-010, TS-012, TS-013, TS-016, TS-017, TS-022 — 8건. 최종 33건.

**정정된 비율**: 흡수 7 + 수정 2 = **9/18 (50%)**. 존치 9건.

§1.6 (f) 후단은 "선작성한 시나리오가 PLAN 확정 후 보강에서 **절반 이상 수정·삭제되면 그 태스크는 선작성 부적격이었다는 신호**"로 규정한다. 50%는 이 문언에 해당하므로 — **신호는 발화했다.** 앞선 "정상적 계열 병합이므로 부적격 신호 아님"이라는 자기판정은 규칙 문언이 사유를 구분하지 않는다는 점에서 **철회한다**.

다만 신호 발화와 별개로 실질 이득도 관측됐다: 존치 9건 중 선작성 고유 6건(TS-024·025·026·027·028·031)이 ⑥경계·부정 축의 백본과 유일한 RED 증거 시나리오를 구성하며, PLAN 유래 도출에 대응이 없다. 두 사실을 함께 다음 태스크 착수 판단의 관측 데이터로 남긴다 — **"부적격 신호"와 "품질 이득"이 동시 발생하는 사례가 존재한다는 것 자체가 §1.6 (f) 판정 기준의 정밀화 대상**임을 시사한다(후속 제안 대상, 본 태스크 범위 밖).

> **[주의] 번호 공간 분리**: 본 문서의 `TS-NNN`과 `PLAN.md` §5.1 QA 매트릭스의 `TS-NNN`은 **서로 다른 번호 공간**이다(예: PLAN TS-009 = `dead`+본문 존재 / 본 문서 TS-009 = `active`+바이트 불변). EXECUTE 교차 참조 시 오식별하지 않도록, PLAN 쪽 ID에 접두를 부여하는 정정을 PLAN 워커에 요청했다.

---

## 1. 리스크 가설 표

> PLAN.md §리스크 가설 표 H-1~H-11 전건 전재 (Block B 보강 완료).

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | `build_review_block()` 시그니처 (`doc` → `doc, json_path=None`) | 호출부 9곳 중 하나라도 누락 시 **침묵 실패**(기본값 `None`이 검사를 건너뜀 — TypeError 아님) | P1 | L1 | TS-004 |
| H-2 | `delete --orphan` | 무손실 가드 — blind 삭제 경로 신설. **벡터 2종**: ① 본문 실재 확인 누락 ② `_resolve_memory_file()` `None` 반환 시 가드 통과 (**G-3 — 개정 전 설계의 실제 결함**) | **P0** | L1 (본문 존재 × 4 status 전수 + `None` 반환 3경로 전수) | TS-008, TS-009, **TS-034, TS-035, TS-037** |
| H-3 | `delete --orphan` 운영 의미 | "본문 부재"가 소실이 아니라 **타 머신 미동기화**일 수 있음 → 조기 제거 시 영구 유실 | **P0** | L1 + 운영 규범 | TS-012, TS-021, TS-033 |
| H-4 | 검출 술어 ↔ 처분 술어 | 두 곳이 경로를 다르게 해석하면 2차 고착(검출은 되는데 정리는 거부) | P1 | L1 | TS-006 |
| H-5 | `review`/`delete` 응답 키 추가 | 하위 소비자 파싱 — `state-tool` CLOSE subprocess 호출, `improve-tool` `show` 의존 | P1 | L2 | TS-013, TS-022 |
| H-6 | 실환경 `.opal/MEMORY.json` 적용 | 프로젝트 SSOT 파일 손상 | **P0** | L2 | TS-021, TS-023 |
| H-7 | 라이프사이클 표 ↔ 스키마 enum | 수동 동기화 계약 — 다음 enum 변경 때 재발 (R-3 자체가 재발 사례) | P2 | L1 (기계 집행 전환) | TS-015 |
| H-8 | install 실행 시점 | 배포 순서 계약 — TEST 전 install 시 미검증 규칙이 전역 홈으로 확산 | P1 | L2 | TS-019, TS-020 |
| H-9 | 신규 ERROR_CODES **3종** (총 23→26) | 문서 파리티 — README·tools.md 표 누락 시 SSOT 3중 불일치 재발 (094 교훈) | P2 | L1 | TS-017 |
| H-10 | `review` 호출당 파일 stat 증가 | 성능·락 점유 — 매 변경 명령이 review를 자동 첨부 | P2 | L1 | TS-019 |
| H-11 | 역방향 고아 (인덱스에 없는 `memory/*.md` 2건 실재) | 본 태스크는 인덱스→파일 방향만 처리 | P2 | **범위 밖** | 없음 (PLAN §9 R-5 후속 보고) |

---

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터

| 대상 | 식별자 | 상태 | 출처 |
|------|--------|------|------|
| 실환경 인덱스 | `테스트 fixture 실환경 미재현 시 결함 통과` | `candidate`, 본문 **부재** | 실환경 `.opal/MEMORY.json` (커밋 `891b4be` 이후) |
| 실환경 인덱스 | `PM이 도구 계수를 grep으로 대체해 오판했다` | `candidate`, 본문 **부재** | 실환경 (동일) |
| 실환경 인덱스 | `변경이력 제거 검토 결정 — A안 확정` | `active`, 본문 **실재** | 실환경 (동일) — 음성 통제용 |
| pytest fixture A | `fx-missing` | 인덱스 3행 / 그중 2행 본문 부재 | tmp_path 생성 (실 파일, mock 금지) |
| pytest fixture B | `fx-intact` | 인덱스 3행 / 본문 전건 실재 | tmp_path 생성 |
| pytest fixture C | `fx-empty` | `memories: []` | tmp_path 생성 |
| pytest fixture D | `fx-matrix` | 4 status(`active`/`promoted`/`superseded`/`dead`) × 2(본문 유/무) = 8행 | tmp_path 생성 — 전이표 전수용 |
| pytest fixture E | `fx-traversal` | `file`이 `memory/` 밖을 가리키는 1행 (`memory/../outside.md` — 스키마 패턴 `^memory/[^/].*\.md$` **통과**). **`status: candidate`** — 게이트 iter2 지적 반영, 미지정 시 TS-037 기대치가 status에 따라 갈린다 | tmp_path 생성 — 경로 탈출 방어용 |
| pytest fixture E' | `fx-traversal-dead` | `fx-traversal`과 동일하되 **`status: dead`** | tmp_path 생성 — 무플래그 경로 음성 통제용 |
| pytest fixture H | `fx-mixed-vocab` | 본문 부재 행 1 + 경로 탈출 행 1 **공존** | tmp_path 생성 — TS-036 검출 어휘 2분용 (iter2 지적 반영) |
| pytest fixture F | `fx-traversal-live` | `fx-traversal` + **`memory/` 밖에 본문 파일이 실재** | tmp_path 생성 — G-3 P0 벡터② 재현용 |
| pytest fixture G | `fx-unresolvable-3` | `None` 반환 3경로(경로 탈출 / 빈 `file` in-test 주입 / resolve 예외) 각 1행 | tmp_path 생성 — 전수 검증용 |
| 회귀 기준선 | pytest 수집 결과 | **163 passed / 25 subtests / 18.03s** | PLAN 실측 (`PLAN.md` §5.2) |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (CUD/호출) | Then (re-read) |
|---------|------------|----------------|---------------|
| TS-001 | `fx-missing` | `review` | `violations`에 `memory_file_missing` 2건 |
| TS-002 | `fx-intact` | `review` | `memory_file_missing` 0건 |
| TS-003 | 4종 위반 유발 fixture | `review` | 기존 4종 엔트리 키·값·상대 순서 불변 |
| TS-004 | `fx-missing` | 변경 명령 6종 각각 | 6개 응답 전부에 검출 + `grep -c "build_review_block(doc)"` == 0 |
| TS-005 | `fx-traversal` | `review` | **`memory_file_unresolvable`**(≠ `memory_file_missing`)로 검출 + `memory/` 밖 stat 0회 |
| TS-006 | `fx-missing` | `review` → `delete --orphan --ref X` → `review` | 검출→정리 왕복 성립, 잔여 1건 |
| TS-007 | `fx-matrix` (본문 부재 4행) | 각 행에 `delete --orphan --ref X` | 4행 전부 `ok:true` + 행 제거 |
| TS-008 | `fx-matrix` (본문 실재 4행) | 각 행에 `delete --orphan --ref X` | 4행 전부 `memory_file_exists` + 인덱스·본문 불변 |
| TS-009 | `fx-intact` | `delete --orphan --ref X` (active 행) | `memory_file_exists` + `MEMORY.json` 바이트 불변 |
| TS-010 | `fx-missing` | `delete --orphan` (`--ref` 생략) | `orphan_ref_missing` + 행 불변 |
| TS-011 | `fx-missing` (candidate) | `delete` (무플래그) | `delete_requires_dead_or_superseded` + 행 불변 |
| TS-012 | `fx-missing` | `delete --orphan --ref X` | `.memory_provenance.log`에 `delete-orphan` + `ref=` + `summary=` |
| TS-013 | `fx-missing` | `delete --orphan --ref X` | `.tmp`/`.lock` 잔여 0건, 후속 `show` `ok:true` |
| TS-014 | `fx-missing` | `delete --orphan --ref X` **1회** | `update --status` 미경유로 행 제거 (호출 이력 1건) |
| TS-015 | `memory-learning.md` 표 + `memory.schema.json:54` | 파리티 검사 실행 | 상태 값 집합 문자 단위 동일(5종) |
| TS-016 | `memory-learning.md` `candidate` 행 | 3열 비공백 검사 | 의미·진입 트리거·도구 동작 전부 채워짐 |
| TS-017 | `ERROR_CODES`(26종) + README·tools.md 표 | 파리티 검사 | 신규 **3종**이 양 문서 표에 등재, 기존 23종 불변 |
| TS-018 | 변경 전 `memory-learning.md` | `git diff` | 기존 4행 3열 텍스트 불변 |
| TS-019 | 변경 후 전체 | `pytest opal/tools/memory-tool -q` | 163+신규 전건 pass, 소요 ≈ 18s 대 |
| TS-020 | TEST 전건 통과 상태 | `install-mac.sh` → `diff` | `memory_tool.py` diff 0줄 |
| TS-021 | 실환경 `.opal/MEMORY.json` (**읽기 전용**) | `review` | `memory_file_missing` 2건 |
| TS-022 | 변경 후 전체 | `pytest opal/tools/state-tool -q` | 전건 pass |
| TS-023 | 실환경 사본 + 원본 해시 | 사본에서 2건 `delete --orphan` | 사본 제거 성공 + **원본 해시 전후 동일** |
| TS-024 | `fx-missing` | 미존재 `--title`로 `delete --orphan --ref X` | `row_not_found` + `MEMORY.json` 바이트 불변 |
| TS-025 | `fx-empty` | `review` | `ok:true` + `memory_file_missing` 0건, 예외 없음 |
| TS-026 | 변경 전/후 pytest collected 수 | 양쪽 수집 | 케이스 수가 **감소하지 않음** (163 이상) |
| TS-027 | 신규 추가 테스트 블록 | `grep -E "mock\|patch\|MagicMock"` | 0건 |
| TS-028 | `memory.schema.json` | `git diff` | 0줄 |
| TS-029 | 변경한 문서 5종 | `## 변경이력` 표 grep | 각 1건, KST 일시 + semver + `(096)` |
| TS-030 | `fx-intact` | `promote --to docs --ref X` / `--ref` 생략 | 정상 졸업 / `promote_ref_missing` — 변경 전과 동일 |
| TS-031 | 구현 **전** 코드 | TS-001·TS-007 대표 케이스 실행 | FAIL. 사유가 "기능 부재"(fixture·import 오류 아님) |
| TS-032 | `fx-matrix` (`active` + 본문 부재 1행) | `delete --orphan --ref X` | `ok:true` + 행 제거 (PLAN §3.2.2 "부분 처방 금지" 규정과 일치) |
| TS-033 | 실환경 잔존 2건 | 캡틴 판정 | 실제 제거 여부 결정 — 본 태스크는 결정을 강제하지 않음 |
| TS-034 | `fx-traversal-live` | `delete --orphan --ref X` | `memory_file_unresolvable` + 인덱스 행 불변 + `memory/` 밖 본문 파일 불변 |
| TS-035 | `fx-unresolvable-3` | 3행 각각 `delete --orphan --ref X` | 3건 전부 `memory_file_unresolvable` + 행 불변 |
| TS-036 | `fx-mixed-vocab` | `review` | 두 행이 서로 다른 `type`으로 반환 |
| TS-037 | `fx-traversal`(candidate) + `fx-traversal-dead`(dead) | `delete` / `delete --orphan` / `promote` 각각 | `--orphan`·`promote`는 status 무관 거부 / 무플래그는 candidate 거부·**dead 허용** |
| TS-038 | `fx-traversal-dead` | 무플래그 `delete` | **허용** + 행 제거. `else` 3줄 불변 실증 |
| TS-039 | `fx-traversal` | `review` / `promote` / `delete --orphan` | 세 명령 전부 `memory_file_unresolvable` 어휘 |

---

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 실 데이터 입력)

> 공통 — **실행 방식 M1 (테스트 도구)**, 도구 `pytest` (`~/.opal/.venv/bin/python -m pytest`). mock/patch/MagicMock 금지, 실 fixture·실 프로세스(subprocess)만.

| ID | 시나리오 | 가설 | 조건 | 기대 결과 | 결과 | 상세 |
|----|---------|------|------|----------|------|------|
| TS-001 | 본문 부재 행이 `violations`에 검출 | H-4 | `fx-missing`, `review` | `memory_file_missing` 엔트리 수 == 본문 부재 행 수(2) | Pass | `pytest -k test_qa001_missing_body_detected_in_violations` → `1 passed` exit 0. |
| TS-002 | 위양성 0 (음성 통제) | H-4 | `fx-intact`, `review` | `memory_file_missing` 0건 | Pass | `pytest -k test_qa002_no_false_positive_when_bodies_intact` → `1 passed` exit 0. |
| TS-003 | 기존 violations 4종 형태 불변 | H-5 | 4종 위반 유발 fixture | 키 집합·값·상대 순서 변경 전과 동일 | Pass | `pytest -k test_qa003_existing_four_violation_types_unchanged` → `1 passed` exit 0. |
| TS-004 | **호출부 9곳 누락 0 (침묵 실패 방어)** | H-1 | 변경 명령 6종 각각 실행 | 6개 응답 전부 검출 + `grep -c "build_review_block(doc)"` == 0 | Pass | `pytest -k test_qa004_call_sites_pass_json_path_and_six_commands_detect` → `1 passed` exit 0. |
| TS-005 | 경로 탈출 행은 **`memory_file_unresolvable`로** 검출 | H-4 | `fx-traversal` | `memory_file_missing`이 **아니라** `memory_file_unresolvable`로 검출. `memory/` 밖 stat 0회 | Pass | `pytest -k test_qa005_traversal_row_reported_as_unresolvable_not_missing` → `1 passed` exit 0. |
| TS-034 | **경로 탈출 + 본문 실재 행의 `--orphan` 거부** `[P0]` | **H-2 벡터②** | `memory/` 밖에 본문이 **실재**하는 경로 탈출 행에 `delete --orphan --ref X` | `memory_file_unresolvable` 거부. 인덱스 행 불변 + **`memory/` 밖 본문 파일 불변**(삭제·수정 0) | Pass | `pytest -k test_qa024_traversal_with_live_body_outside_memory_rejected` → `1 passed` exit 0. |
| TS-035 | **`None` 반환 3경로 전수** `[P0]` | **H-2 벡터②** | ① 경로 탈출 ② 빈 `file`(스키마 우회 in-test 직접 주입) ③ resolve 예외 | 3경로 전부 `memory_file_unresolvable` 거부 + 행 불변. **어느 경로도 삭제로 이어지지 않음** | Pass | `pytest -k test_qa025_none_return_three_paths_all_rejected` → `1 passed` exit 0. |
| TS-036 | 검출 어휘 2분 (부재 ≠ 해석 불가) | H-4 | 본문 부재 행 + 경로 탈출 행이 공존하는 fixture, `review` | 두 행이 **서로 다른 `type`**으로 반환됨. 운영자가 `review` 출력만으로 "정리 가능" vs "포인터 수리 필요"를 구별 가능 | Pass | `pytest -k test_ts036_mixed_vocab_review_distinguishes_missing_from_unresolvable` → `1 passed` exit 0. |
| TS-037 | 해석 불가 행의 잔존 고착 — **status별 분기 확인** | H-2 | `fx-traversal`(**candidate**)과 `fx-traversal-dead`(**dead**)에 `delete`(무플래그) / `delete --orphan` / `promote` 각각 | **① `--orphan`**: status 무관 `memory_file_unresolvable` 거부 · **② 무플래그 `delete`**: candidate → `delete_requires_dead_or_superseded` 거부 / **dead → 허용(음성 통제)** — `else` 분기는 `mem_file`을 조회하지 않으므로 기존 동작이 불변임을 실증한다 · **③ `promote`**: **`memory_file_unresolvable`** 거부 (096에서 `memory_file_not_found` → 변경. 해석 성공 + 본문 부재인 경우는 `memory_file_not_found` 불변) | Pass | ①③: `pytest -k test_ts037_orphan_and_promote_reject_regardless_of_status` → `1 passed, 2 subtests passed`(candidate/dead 2/2) exit 0. ②-candidate: `test_qa011_no_flag_delete_still_requires_dead_or_superseded` → Pass(위 TS-011 근거 재사용). ②-dead: `test_ts038_no_flag_delete_allows_dead_unresolvable_row` → Pass(아래 TS-038 근거 재사용). 3파트 전부 실측 확인. |
| TS-038 | 무플래그 `delete`가 `mem_file`을 조회하지 않음 (음성 통제) `[핵심]` | **H-2** | `fx-traversal-dead`에 무플래그 `delete` | **허용**되어 행이 제거된다. PLAN이 `[MUST]`로 보존 명령한 `else` 3줄(`memory_tool.py:1355-1357`)이 문자 그대로 불변임을 실증 — GREEN을 좇아 무플래그 경로에 가드를 추가하면 이 시나리오가 FAIL한다 | Pass | `pytest -k test_ts038_no_flag_delete_allows_dead_unresolvable_row` → `1 passed` exit 0. |
| TS-039 | **3명령 어휘 일관성** (`review` · `promote` · `delete --orphan`) | H-4 | `fx-traversal` 동일 행에 세 명령 각각 | 세 명령이 **같은 행을 같은 어휘(`memory_file_unresolvable`)로** 지칭한다. 한 행을 두고 review는 "해석 불가", promote는 "부재"라고 말하는 표면이 없다 | Pass | `pytest -k test_qa026_ts039_vocabulary_consistency_across_three_commands` → `1 passed` exit 0. |
| TS-006 | 검출→정리 왕복 성립 (2차 고착 부재) | H-4 | `review` → `delete --orphan --ref X` → `review` | 검출된 행이 그대로 정리되고 잔여가 재검출됨 | Pass | `pytest -k test_qa006_candidate_orphan_row_cleaned_real_layout_roundtrip` → `1 passed` exit 0. `_install_json()` 실환경 레이아웃(`.opal/MEMORY.json`↔`.opal/memory/*.md` 형제 구조) 재현으로 왕복 확인. |
| TS-007 | 본문 부재 4 status 전부 정리 가능 | H-2 | `fx-matrix` 본문 부재 4행 | 4행 전부 `ok:true` + 행 제거 | Pass | candidate: `pytest -k test_qa006_candidate_orphan_row_cleaned_real_layout_roundtrip` → `1 passed`. promoted: `pytest -k test_qa007_promoted_orphan_row_cleaned` → `1 passed`. active: TS-032 직접 CLI 실증(스크래치패드) `{"ok":true,"row_removed":true,"orphan":true,...}` + 행 제거 확인. dead·superseded: 직접 CLI 실증(스크래치패드, fixture_doc_populated.json 기반 `task_done.md`/`arch_old.md` skip) 각각 `{"ok":true,"row_removed":true,"orphan":true,"reason":"memory_file_missing",...}` + 최종 인덱스에서 4행 모두 제거 확인(`['메인 직접 커밋 선호','콘솔 브레인 구독 인증','졸업한 선호 규칙','개선 후보 기록']`만 잔존). 4 status 전건 실측 완료. |
| TS-008 | **본문 실재 행 status 무관 거부** `[핵심]` | **H-2** | `fx-matrix` 본문 실재 4행 | 4행 전부 `memory_file_exists`, 인덱스·본문 불변 | Pass | `pytest -k test_qa008_orphan_rejected_when_body_exists_all_statuses` → `1 passed, 4 subtests passed`(active/dead/superseded/promoted 4/4) exit 0. subtest 단위 결과: 4개 전부 SUBFAILED 0건. |
| TS-009 | **`active` + 본문 실재 바이트 불변** `[핵심]` | **H-2** | `fx-intact` active 행 | `memory_file_exists` + `MEMORY.json` 바이트 단위 불변 | Pass | `pytest -k test_qa009_active_body_exists_orphan_rejected_bytes_unchanged` → `1 passed` exit 0. |
| TS-010 | 귀착처 미기재 정리 거부 | H-3 | `--ref` 생략 | `orphan_ref_missing` + 행 불변 | Pass | `pytest -k test_qa010_orphan_without_ref_rejected` → `1 passed` exit 0. |
| TS-011 | 무플래그 `delete` 동작 완전 불변 | H-2 | 본문 부재 `candidate`에 무플래그 | `delete_requires_dead_or_superseded` | Pass | `pytest -k test_qa011_no_flag_delete_still_requires_dead_or_superseded` → `1 passed` exit 0. |
| TS-012 | 사유·귀착처·**요약** 감사 로그 보존 | **H-3** | `delete --orphan --ref X` | `.memory_provenance.log`에 `delete-orphan` 행 + `ref=` + `summary=` | Pass | `pytest -k test_qa012_provenance_log_records_reason_ref_and_summary` → `1 passed` exit 0. |
| TS-013 | 원자성·잔여 0 | H-5 | `delete --orphan --ref X` | `.tmp`/`.lock` 0건, 후속 `show` `ok:true` | Pass | `pytest -k test_qa013_orphan_delete_leaves_no_residue_and_show_ok` → `1 passed` exit 0. |
| TS-014 | `update --status` 미경유 단일 호출 | H-2 | `delete --orphan --ref X` 1회 | 1회 호출로 행 제거. 상태 전이 호출 0건 | Pass | `pytest -k test_qa014_single_call_no_status_transition_required` → `1 passed` exit 0. |
| TS-015 | **라이프사이클 표 == 스키마 enum (기계 집행)** | **H-7** | 파리티 검사 | 상태 값 집합이 문자 단위 동일(5종). 검사가 테스트로 상시 실행됨 | Pass | `pytest -k test_qa015_lifecycle_table_matches_schema_enum` → `1 passed` exit 0. |
| TS-016 | `candidate` 행 3열 채움 | H-7 | 표 파싱 | 의미·진입 트리거·도구 동작 전부 비공백 | Pass | `pytest -k test_qa016_candidate_row_columns_filled` → `1 passed` exit 0. |
| TS-017 | 신규 에러 코드 문서 파리티 | H-9 | `ERROR_CODES`(총 23→**26종**) vs README·tools.md 표 | 신규 **3종**(`memory_file_exists`·`orphan_ref_missing`·`memory_file_unresolvable`)이 양 문서 표에 등재. 기존 23종 불변 | Pass | `pytest -k test_qa017_new_error_codes_documented_in_readme_and_toolsmd` → `1 passed` exit 0. |
| TS-018 | 기존 4행 diff 0 (음성 통제) | H-7 | `git diff` | 4개 상태 행 3열 텍스트 불변 | Pass | `pytest -k test_qa018_existing_four_rows_text_unchanged` → `1 passed` exit 0. |
| TS-019 | 전건 GREEN + 성능 비퇴행 | H-10 | `pytest opal/tools/memory-tool -q` | 163+신규 전건 pass, 소요 ≈ 18s 대 | Pass | `~/.opal/.venv/bin/python -m pytest opal/tools/memory-tool -q` → `187 passed, 31 subtests passed in 21.51s`, exit code 0. FAILED/SUBFAILED 라인 0건(요약 라인·exit code로 판정, subtests 왜곡 배제). 기준선 18.03s(163p/25sub) 대비 21.51s(187p/31sub) — 신규 24케이스+6서브테스트 추가분 대비 자연스러운 증가이며 H-10이 우려한 이상 퇴행(`Path.exists()` 락 밖 추가) 징후 없음 |
| TS-024 | 미존재 title 부정 경로 | H-2 | 미존재 `--title` | `row_not_found` + 바이트 불변 | Pass | `pytest -k test_delete_row_not_found` → `1 passed`(`ok:false`+`row_not_found` 확인). 바이트 불변은 스크래치패드 직접 CLI 실증으로 보강: `delete --title "존재하지않는항목-096검증"` 실행 전후 SHA-256 `da7ff88b…c0` == `da7ff88b…c0`(완전 동일). |
| TS-025 | 인덱스 0건 경계 | H-1 | `fx-empty`, `review` | `ok:true` + 0건, 예외·traceback 없음 | Pass | 전용 pytest 케이스 부재 확인 후 직접 CLI 실증(스크래치패드): `{"memories":[],"history":[]}` 문서에 `review` 실행 → `{"ok":true,...,"violations":[],"promote_candidates":[],"cleanup_candidates":[]}`, exit 0, stderr 없음(예외·traceback 부재). |
| TS-026 | **케이스 수 미감소** | H-10 | 변경 전/후 collected 수 대조 | 163 이상. 테스트 삭제로 GREEN을 만들지 않았음 | Pass | `~/.opal/.venv/bin/python -m pytest opal/tools/memory-tool --collect-only -q` → `187 tests collected in 0.03s`. 변경 전 기준선 163 대비 24건 순증(감소 0) — RED-EVIDENCE.md §4 신규 24건과 일치, 테스트 삭제로 GREEN을 만들지 않았음을 수량으로 확인 |
| TS-027 | 신규 테스트 mock 부재 | — | `grep` on 신규 블록 | 0건 | Pass | `sed -n '3241,3849p' test_memory_tool.py \| grep -inE "mock\|patch\|MagicMock"` → 1건이나 원문은 "직접 호출 — **mock 아님**, 실제 함수를 실행한다" — 금지 서술 자체를 인용한 부정문(메타-순환 오탐)이며 실제 `unittest.mock`/`@patch`/`MagicMock(`/`Mock(` 사용은 전체 파일 grep 0건(exit 1). §6 보안표의 3건 확인과 동일 결론. |
| TS-028 | 스키마 무변경 (부정) | H-7 | `git diff memory.schema.json` | 0줄. 문서를 스키마에 맞추는 방향이지 역이 아님 | Pass | `git diff opal/tools/memory-tool/schema/memory.schema.json \| wc -l` → `0`. `git diff --stat` 무출력. |
| TS-029 | 변경이력 096 행 | H-9 | 변경 문서 5종 grep | 각 1건, KST 일시 + semver + `(096)` | Pass | 5종 각 1건 확인: `memory_tool.py:25` "v2.2 2026-08-20 … (096)"(@header 라인) / `README.md:326` "\| v2.2 \| 096 \| 2026-08-20 12:23 …(096) \|" / `tools.md:1169` "\| v2.17 \| 2026-08-20 12:23 \| …(096) \|" / `memory-learning.md:109` "\| v1.5 \| 2026-08-20 12:23 \| 096 …(096) \|" / `test_memory_tool.py:32` "v1.3 2026-08-20 096 RED-first 블록 추가…(096)"(@header). 전건 KST 일시(`2026-08-20 12:23` 또는 동일 일자) + semver(v2.2/v2.17/v1.5/v1.3) + `(096)` 태그 포함. |
| TS-030 | 기존 `promote` 정상 경로 회귀 (⑤ 준용) | H-2 | 정상 졸업 / `--ref` 생략 | 변경 전과 동일 동작·에러 코드 | Pass | 정상 졸업: `pytest -k test_promote_to_docs_removes_row_and_file` → `1 passed`(행·본문 파일 모두 제거). `--ref` 생략: `pytest -k "test_promote_without_ref_rejected or test_promote_without_ref_preserves_row_and_file"` → `2 passed`(`promote_ref_missing` + 행·파일 불변). 096 변경(F-002)은 `cmd_promote()`의 `mem_file is None` 분기 어휘만 정정했고 본문 실재/정상 졸업 경로는 무변경 — 회귀 0건. |
| TS-031 | **RED 증거 — 구현 전 FAIL** | — | TS-001·TS-007 대표 케이스를 구현 전 실행 | FAIL. 사유가 "기능 부재"(fixture·import 오류 아님) | Pass | 구현 전 재실행은 GREEN 완료 후 시점상 불가(RED 시점 데이터는 `RED-EVIDENCE.md`가 SSOT). 동 문서 §2 stdout 원문: `test_qa001_missing_body_detected_in_violations` FAILED(TS-001 대표) + `test_qa006_candidate_orphan_row_cleaned_real_layout_roundtrip` FAILED(TS-007 계열 대표, `argparse: error: unrecognized arguments: --orphan --ref`) — exit code 1. §6.1 표가 두 건 모두 "기능 부재"(검출 로직 부재 / CLI 플래그 미신설)로 귀속함을 명시, fixture·import 오류 0건. RED 작성자(opal-test-agent mode:red)≠구현자(opal-be-agent) 분리 준수(red-first.md §2). |
| TS-032 | `active` + 본문 부재 정리 허용 | H-2 | `fx-matrix` 해당 1행 | `ok:true` + 행 제거. PLAN §3.2.2 "부분 처방 금지" 규정과 일치 | Pass | 전용 pytest 케이스 부재 확인 후 직접 CLI 실증(스크래치패드): `fixture_doc_populated.json`의 "메인 직접 커밋 선호"(status:`active`) 행만 본문 미생성 → 사전 `review`에서 `memory_file_missing` 1건 검출 → `delete --orphan --ref X` → `{"ok":true,"row_removed":true,"orphan":true,"reason":"memory_file_missing",...}` + 인덱스에서 해당 행 제거 확인. PLAN §3.2.2 "`--orphan` 경로는 status를 읽지 않는다" 규정과 실측 일치. |

### L2. 프로세스 통합 (자동, 실 프로세스 read→CUD→re-read)

#### TS-021: 실환경 인덱스에서 검출이 성립한다 `[목표달성]`

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3, H-6 |
| 대상 | 태스크 목표 전단 — "검출 불가" → "검출 가능" 전환 |
| 계층 | L2 |
| **실행 방식** | **M1 (실 CLI 프로세스, subprocess)** |
| 조건 | 실환경 `.opal/MEMORY.json`을 **읽기 전용**으로 `review` 호출 |
| 기대 결과 | `memory_file_missing` 2건 검출(잔존 candidate 2건). 본문 실재 1건은 미검출 |
| 도구 | **`~/.opal/.venv/bin/python opal/tools/memory-tool/memory_tool.py` (프로젝트 소스 직접 실행)** — G-1 정정. 이 시나리오의 실행 시점은 PLAN Step 5이고 install은 Step 6이므로, 배포본을 쓰면 신규 경로가 없는 구버전을 측정해 FAIL하거나 install 선행을 유도해 D-3·H-8(배포 순서)을 위반한다. 배포본 실동작 확인은 TS-020이 담당 |
| 실행 명령 | `HASH_BEFORE=$(shasum -a 256 .opal/MEMORY.json \| awk '{print $1}'); ~/.opal/.venv/bin/python opal/tools/memory-tool/memory_tool.py review --file .opal/MEMORY.json; HASH_AFTER=$(shasum -a 256 .opal/MEMORY.json \| awk '{print $1}')` |
| 결과 | Pass |
| 상세 | exit 0. `violations`에 `memory_file_missing` **정확히 2건** 검출: `{"type":"memory_file_missing","title":"fixture 실환경 미재현 시 결함 통과","file":"memory/테스트_fixture가_실환경_구조를_재현하지_않으면_결함이_통과한다.md"}` / `{"type":"memory_file_missing","title":"PM이 도구 계수를 grep으로 대체해 오판했다","file":"memory/PM이_도구_계수를_grep으로_대체해_오판했다.md"}`. `memory_file_unresolvable` 0건. 본문 실재 1건(`active`, "변경이력 제거 검토 결정 — A안 확정")은 인덱스 3행 직접 확인 결과 `violations`에 미검출(음성 통제 성립). 해시: BEFORE=`d5ae7b4c3d…7d15c` == AFTER=`d5ae7b4c3d…7d15c` (전 40+자 SHA-256 완전 동일) — read-only 확인 |

#### TS-023: 실환경 정리 리허설 + 원본 보전 `[목표달성]`

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3, H-6 |
| 대상 | 태스크 목표 후단 — "정리 불가" → "정리 가능" 전환 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | 실환경 `.opal/MEMORY.json`을 스크래치패드로 **복사**. 사본에서 2건 `delete --orphan --ref X`. 원본은 실행 전후 해시 취득 |
| 기대 결과 | 사본에서 2건 제거 성공 + 재`review` 0건. **원본 해시 전후 동일** |
| 도구 | **`~/.opal/.venv/bin/python opal/tools/memory-tool/memory_tool.py` (프로젝트 소스 직접 실행)** — G-1 정정, TS-021과 동일 사유. `shasum` |
| 실행 명령 | `mkdir -p <scratch>/rehearsal/.opal && cp .opal/MEMORY.json <scratch>/rehearsal/.opal/MEMORY.json && cp -r .opal/memory <scratch>/rehearsal/.opal/memory` → `delete --file <copy> --title "fixture 실환경 미재현 시 결함 통과" --orphan --ref "미복원: 096 QA-023 리허설, 실작성 머신 로컬"` → `delete --file <copy> --title "PM이 도구 계수를 grep으로 대체해 오판했다" --orphan --ref "미복원: 096 QA-023 리허설, 실작성 머신 로컬"` → `review --file <copy>` → (음성 통제) `delete --file <copy> --title "변경이력 제거 검토 결정 — A안 확정" --orphan --ref "테스트: 거부되어야 함"` → 원본 `.opal/MEMORY.json` 해시 실행 전후 대조 |
| 결과 | Pass |
| 상세 | 사본 레이아웃을 `<scratch>/rehearsal/.opal/{MEMORY.json,memory/}` 형제 구조로 재현(경로 화이트리스트 요건 충족). 2건 `delete --orphan --ref` 각각 `{"ok":true,"row_removed":true,"orphan":true,"reason":"memory_file_missing","provenance_logged":true}` 성공 반환(exit 0), 재`review` 결과 `violations: []`(0건) 확인. `.memory_provenance.log`에 두 행 모두 `delete-orphan \| ref=… \| summary=…` 기록 확인(TS-012 요건과 교차 충족). **음성 통제**: 본문 실재 `active` 행에 동일하게 `--orphan` 시도 → `{"ok":false,"error":"memory_file_exists","message":"--orphan은 본문 .md가 부재한 행 전용 — 본문이 실재함: …"}` exit 1로 거부, 사본 인덱스에 해당 행 그대로 잔존 + 본문 파일 불변 확인. **원본 보전**: 원본 `.opal/MEMORY.json` SHA-256 실행 전 `d5ae7b4c3d…7d15c` == 리허설 전 과정(2건 삭제 성공 + 1건 거부) 완료 후 재측정 `d5ae7b4c3d…7d15c` — 완전 동일. 원본은 이 시나리오 전 구간에서 read 1회(TS-021)만 접근했으며 write 0회 |

> **[MUST] 원본 불변**: 실제 `.opal/MEMORY.json`의 잔존 2건 제거 여부는 **캡틴 판단 사항**이며 본 태스크의 검증 범위가 아니다 (TS-033). 리허설은 사본에서만 수행한다 (H-6).

#### TS-020: install 후 배포본 정합

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 |
| 대상 | R-4 AC 후단 + 배포 경계 제약 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | TEST 전건 통과 **이후** `scripts/install-mac.sh` 실행 → `~/.opal/tools/memory-tool/memory_tool.py` vs 프로젝트 소스 |
| 기대 결과 | diff **0줄**. 실행 시점이 TEST 전건 통과 이후임이 로그로 확인됨 |
| 도구 | `diff` |
| 실행 명령 | `diff ~/.opal/tools/memory-tool/memory_tool.py opal/tools/memory-tool/memory_tool.py` (install은 캡틴이 Step 6에서 TEST 전건 통과 이후 실행 완료 — 본 시나리오는 install 재실행 없이 배포본 정합만 확인) |
| 결과 | Pass |
| 상세 | `diff` 무출력, `wc -l` == `0` — 배포본과 프로젝트 소스 `memory_tool.py` 완전 동일. 배포본 직접 로드 확인: `len(ERROR_CODES) == 26` + `memory_file_exists`/`orphan_ref_missing`/`memory_file_unresolvable` 3종 전부 `True`. `bash ~/.opal/tools/memory-tool/run.sh delete --help`에 `--orphan`/`--ref` 옵션 노출 확인. **배포본 실동작**(신규 경로) 확인: 스크래치패드에 본문 부재 1행(`prefs_commit.md` 미생성) 구성 후 `bash run.sh review` → `memory_file_missing` 1건 검출, `bash run.sh delete --title "메인 직접 커밋 선호" --orphan --ref "TS-020 배포본 실동작 확인"` → `{"ok":true,"row_removed":true,"orphan":true,...}` 성공 — 배포본에서 신규 F-001·F-002 경로가 실제로 동작함을 실증(단순 diff 0 확인을 넘어선 실행 검증). |

> **[주의]** `install-mac.sh:220-232`가 배포 시 `.md`의 변경이력을 strip하므로 **diff 0 검증 대상은 `memory_tool.py`로 한정**한다 (PLAN §9 R-9). `.md` 파일에 diff 0을 요구하면 반드시 실패한다.

#### TS-022: 하위 소비자 무영향

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | `state-tool`이 CLOSE 시 memory-tool을 subprocess 호출(`link_memory_history()`), `improve-tool`이 `show` 응답에 의존 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | `pytest opal/tools/state-tool -q` + `pytest opal/tools/improve-tool -q` |
| 기대 결과 | 전건 pass. `review` 응답에 키가 추가돼도 하위 소비자 파싱이 깨지지 않음 |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/state-tool -q` / `~/.opal/.venv/bin/python -m pytest opal/tools/improve-tool -q` |
| 결과 | Pass |
| 상세 | state-tool: `341 passed, 3 skipped, 84 subtests passed in 53.40s`, exit 0. improve-tool: `17 passed in 2.16s`, exit 0. 두 스위트 모두 FAILED/ERROR 0건 — `link_memory_history()`(CLOSE subprocess 호출)·`show` 응답 의존 경로 모두 096의 `review`/`delete` 응답 키 추가에 영향받지 않음(H-5 대응). 참고: 지시에 따라 `opal/tools/test-tool`은 실행하지 않음(선재 실패 1건 존재, 096 무관) |

### L3. 사용자 협업 (수동, [SUPERVISOR] 마커)

#### TS-033: 실환경 잔존 2건의 실제 제거 여부 판정 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | 실환경 `.opal/MEMORY.json`의 본문 부재 `candidate` 2건 |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업)** — 자동화 부적격. H-3이 규정하듯 "본문 부재"가 소실이 아니라 **타 머신 미동기화**일 수 있어, 제거는 지식 영구 유실 가능성을 수반한다 |
| 조건 | 도구가 2건을 검출·정리 가능한 상태가 된 후, 각 행의 `summary`와 지식 귀착처 유무를 캡틴에게 제시 |
| 기대 결과 | 캡틴이 (a) 작성 머신에서 본문 회수 (b) `--ref`를 붙여 제거 (c) 보류 중 택일. **본 태스크는 결정을 강제하지 않으며, 미결정도 정상 종료 조건이다** |
| 실행자 | [SUPERVISOR] — 캡틴 수동 확인 필요 |
| PM 요청 양식 | "실환경 메모리 2건이 본문 없이 인덱스에만 남아 있습니다. 각각의 요약은 다음과 같습니다: (1) `테스트 fixture가 실환경 구조를 재현하지 않으면 결함이 통과한다` (2) `PM이 도구 계수를 grep으로 대체해 오판했다`. 두 건 모두 brain·docs에 대응 페이지가 없습니다(실측). (a) 작성 머신에서 본문 회수 / (b) 귀착처를 지정해 제거 / (c) 보류 중 무엇으로 할까요?" |
| 결과 | 대기 — 캡틴 판정 필요 |
| 상세 | opal-test-agent는 본 항목을 판정하지 않는다(디스패치 지시 준수). 실환경 `.opal/MEMORY.json`의 잔존 2건에 대한 조작은 수행하지 않았으며, TS-021 read-only 검출·TS-023 사본 리허설(원본 해시 전후 동일 확인)로 도구가 이 2건을 검출·정리할 수 있는 상태임만 실증했다. 실제 제거 여부는 캡틴의 별도 결정 사항으로 남긴다. 미결정은 §3 표 자체가 명시한 정상 종료 조건이다.

---

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| R-1 AC 전단 (검출) | H-4 | L1 | TS-001 | `opal/tools/memory-tool/tests/test_memory_tool.py::TestReviewReferenceIntegrity::test_qa001_missing_body_detected_in_violations` | F-001 |
| R-1 AC 후단 (오탐 0) | H-4 | L1 | TS-002 | `opal/tools/memory-tool/tests/test_memory_tool.py::TestReviewReferenceIntegrity::test_qa002_no_false_positive_when_bodies_intact` | 음성 통제 |
| R-1 AC 후단 (형태 불변) | H-5 | L1 | TS-003 | `opal/tools/memory-tool/tests/test_memory_tool.py::TestReviewReferenceIntegrity::test_qa003_existing_four_violation_types_unchanged` | 회귀 |
| R-1 (호출부 완전성) | H-1 | L1 | TS-004 | `opal/tools/memory-tool/tests/test_memory_tool.py::TestReviewReferenceIntegrity::test_qa004_call_sites_pass_json_path_and_six_commands_detect` | 침묵 실패 방어 |
| R-1 (경로 안전) | H-4 | L1 | TS-005 | `opal/tools/memory-tool/tests/test_memory_tool.py::TestReviewReferenceIntegrity::test_qa005_traversal_row_reported_as_unresolvable_not_missing` | 보안 |
| R-1 (경계) | H-1 | L1 | TS-025 | 직접 CLI 실행 (pytest 케이스 없음) — §3 실행 명령 참조 | 인덱스 0건 |
| R-2 AC 전단 (정리 가능) | H-2, H-4 | L1 | TS-006, TS-007, TS-014, TS-032 | TS-006: `opal/tools/memory-tool/tests/test_memory_tool.py::TestDeleteOrphan::test_qa006_candidate_orphan_row_cleaned_real_layout_roundtrip` / TS-007: `opal/tools/memory-tool/tests/test_memory_tool.py::TestDeleteOrphan::test_qa007_promoted_orphan_row_cleaned`(promoted 대표) + 직접 CLI 실행 (pytest 케이스 없음) — §3 실행 명령 참조(active/dead/superseded 3종 CLI 실증) / TS-014: `opal/tools/memory-tool/tests/test_memory_tool.py::TestDeleteOrphan::test_qa014_single_call_no_status_transition_required` / TS-032: 직접 CLI 실행 (pytest 케이스 없음) — §3 실행 명령 참조 | F-002 |
| R-2 AC 후단 (가드 유지 — 벡터①) | **H-2** | L1 | **TS-008, TS-009** | TS-008: `opal/tools/memory-tool/tests/test_memory_tool.py::TestDeleteOrphan::test_qa008_orphan_rejected_when_body_exists_all_statuses` / TS-009: `opal/tools/memory-tool/tests/test_memory_tool.py::TestDeleteOrphan::test_qa009_active_body_exists_orphan_rejected_bytes_unchanged` | **핵심 음성 통제** |
| R-2 AC 후단 (가드 유지 — **벡터②**) | **H-2** | L1 | **TS-034, TS-035** | TS-034: `opal/tools/memory-tool/tests/test_memory_tool.py::TestDeleteOrphan::test_qa024_traversal_with_live_body_outside_memory_rejected` / TS-035: `opal/tools/memory-tool/tests/test_memory_tool.py::TestDeleteOrphan::test_qa025_none_return_three_paths_all_rejected` | **G-3 P0 대응.** 확인 불가 ≠ 부재 |
| R-2 (잔존 고착 — status별 분기) | H-2 | L1 | TS-037 | `opal/tools/memory-tool/tests/test_memory_tool.py::TestDeleteOrphan::test_ts037_orphan_and_promote_reject_regardless_of_status`(①③) + `opal/tools/memory-tool/tests/test_memory_tool.py::TestDeleteOrphan::test_qa011_no_flag_delete_still_requires_dead_or_superseded`(②-candidate) + `opal/tools/memory-tool/tests/test_memory_tool.py::TestDeleteOrphan::test_ts038_no_flag_delete_allows_dead_unresolvable_row`(②-dead) | PLAN §9 R-13 이월 근거. **선재 고착이며 096이 신설한 것이 아니다** (iter2 판정) |
| R-2 (무플래그 경로 불변) | **H-2** | L1 | **TS-038** | `opal/tools/memory-tool/tests/test_memory_tool.py::TestDeleteOrphan::test_ts038_no_flag_delete_allows_dead_unresolvable_row` | **음성 통제** — `else` 3줄 문자 불변 실증 |
| R-1·R-2 (어휘 일관성) | H-4 | L1 | TS-039 | `opal/tools/memory-tool/tests/test_memory_tool.py::TestDeleteOrphan::test_qa026_ts039_vocabulary_consistency_across_three_commands` | PLAN QA-026 대응. citation-rules §7.1 |
| R-1 (검출 어휘 2분) | H-4 | L1 | TS-036 | `opal/tools/memory-tool/tests/test_memory_tool.py::TestReviewReferenceIntegrity::test_ts036_mixed_vocab_review_distinguishes_missing_from_unresolvable` | 처분이 갈리므로 어휘도 갈린다 |
| R-2 (귀착처 의무) | H-3 | L1 | TS-010, TS-012 | TS-010: `opal/tools/memory-tool/tests/test_memory_tool.py::TestDeleteOrphan::test_qa010_orphan_without_ref_rejected` / TS-012: `opal/tools/memory-tool/tests/test_memory_tool.py::TestDeleteOrphan::test_qa012_provenance_log_records_reason_ref_and_summary` | 감사 추적 |
| R-2 (무플래그 불변) | H-2 | L1 | TS-011 | `opal/tools/memory-tool/tests/test_memory_tool.py::TestDeleteOrphan::test_qa011_no_flag_delete_still_requires_dead_or_superseded` | 회귀 |
| R-2 (원자성) | H-5 | L1 | TS-013 | `opal/tools/memory-tool/tests/test_memory_tool.py::TestDeleteOrphan::test_qa013_orphan_delete_leaves_no_residue_and_show_ok` | |
| R-2 (부정) | H-2 | L1 | TS-024 | `opal/tools/memory-tool/tests/test_memory_tool.py::TestDelete::test_delete_row_not_found`(row_not_found 확인) + 직접 CLI 실행 (pytest 케이스 없음) — §3 실행 명령 참조(바이트 불변 보강 실증) | 미존재 title |
| R-2 (잔존 준용) | H-2 | L1 | TS-030 | `opal/tools/memory-tool/tests/test_memory_tool.py::TestPromoteToDocs::test_promote_to_docs_removes_row_and_file`(정상 졸업) + `opal/tools/memory-tool/tests/test_memory_tool.py::TestPromoteLossless::test_promote_without_ref_rejected` + `opal/tools/memory-tool/tests/test_memory_tool.py::TestPromoteLossless::test_promote_without_ref_preserves_row_and_file`(--ref 생략) | promote 회귀 |
| R-3 AC 전단·중단 | **H-7** | L1 | TS-015, TS-016 | TS-015: `opal/tools/memory-tool/tests/test_memory_tool.py::TestLifecycleDocParity::test_qa015_lifecycle_table_matches_schema_enum` / TS-016: `opal/tools/memory-tool/tests/test_memory_tool.py::TestLifecycleDocParity::test_qa016_candidate_row_columns_filled` | F-003 — 기계 집행 |
| R-3 AC 후단 | H-7 | L1 | TS-018 | `opal/tools/memory-tool/tests/test_memory_tool.py::TestLifecycleDocParity::test_qa018_existing_four_rows_text_unchanged` | 음성 통제 |
| R-3 (문서 파리티) | H-9 | L1 | TS-017 | `opal/tools/memory-tool/tests/test_memory_tool.py::TestLifecycleDocParity::test_qa017_new_error_codes_documented_in_readme_and_toolsmd` | ERROR_CODES |
| R-4 AC 전단 (RED) | — | L1 | TS-031 | `RED-EVIDENCE.md` §2·§3·§6.1(RED 시점 stdout 인용, 재실행 불가) — 대표 케이스 노드: `opal/tools/memory-tool/tests/test_memory_tool.py::TestReviewReferenceIntegrity::test_qa001_missing_body_detected_in_violations`(TS-001) / `opal/tools/memory-tool/tests/test_memory_tool.py::TestDeleteOrphan::test_qa006_candidate_orphan_row_cleaned_real_layout_roundtrip`(TS-007) | F-004 |
| R-4 AC 중단 (회귀) | H-10 | L1 | TS-019, TS-026 | TS-019: 전체 스위트 실행(`pytest opal/tools/memory-tool -q`) — 개별 케이스 아님, §3 실행 명령 참조 / TS-026: `pytest opal/tools/memory-tool --collect-only -q` — 개별 케이스 아님, §3 실행 명령 참조 | 케이스 수 미감소 포함 |
| R-4 AC 후단 (install) | H-8 | L2 | TS-020 | 직접 CLI 실행 (pytest 케이스 없음) — §3 실행 명령 참조 | `.py` 한정 |
| R-4 (하위 소비자) | H-5 | L2 | TS-022 | 직접 프로세스 실행(`pytest opal/tools/state-tool -q` / `pytest opal/tools/improve-tool -q`, 전체 스위트) — 개별 케이스 아님, §3 실행 명령 참조 | |
| **목표 (전체) — 검출·정리 전환** | H-3, H-6 | L2 | **TS-021, TS-023** | TS-021: 직접 CLI 실행 (pytest 케이스 없음) — §3 실행 명령 참조 / TS-023: 직접 CLI 실행 (pytest 케이스 없음) — §3 실행 명령 참조 | **목표달성 시나리오** |
| **목표 3절 — 규범↔스키마 정합** | H-7 | L1 | **TS-015** | `opal/tools/memory-tool/tests/test_memory_tool.py::TestLifecycleDocParity::test_qa015_lifecycle_table_matches_schema_enum` | **목표달성 시나리오** — G-2 정정. 목표 문장은 3절("검출" · "정리" · "라이프사이클 규범 문서를 스키마 enum과 정합")이며 3절은 문서 상태 자체가 목표다. 기계 집행 파리티(TS-015)가 그 목표의 직접 증거이므로 ①축에 연결한다 |
| 제약 (4) 스키마 무변경 | H-7 | L1 | TS-028 | 직접 CLI 실행 (pytest 케이스 없음) — §3 실행 명령 참조 | 부정 |
| 제약 (5) 변경이력 | H-9 | L1 | TS-029 | 직접 CLI 실행 (pytest 케이스 없음) — §3 실행 명령 참조 | |
| PRINCIPLES §4 mock 금지 | — | L1 | TS-027 | 직접 CLI 실행 (pytest 케이스 없음) — §3 실행 명령 참조 | |
| 운영 판단 (H-3 잔여 리스크) | H-3 | L3 | TS-033 | 해당 없음 (수동) | 캡틴 판정 |

### 루브릭 축 커버 현황

| 축 | 상태 | 시나리오 |
|----|------|---------|
| ① 목표 달성 | ✓ | TS-021, TS-023 (검출·정리 전환) + TS-015 (규범↔스키마 정합) — G-2 정정 |
| ② 요구 커버 | ✓ R-1~R-4 전건 | 전 TS |
| ③ 기능 커버 | ✓ F-001~F-004 전건 | F-001: TS-001~005, 025 / F-002: TS-006~014, 024, 030, 032 / F-003: TS-015~018, 028, 029 / F-004: TS-019~023, 026, 027, 031 |
| ④ 리스크 커버 | ✓ H-1~H-10 전건 (H-11은 PLAN이 범위 밖 판정) | 위 §1 표 "시나리오" 열 |
| ⑤ 채택·잔존 | N/A (교체형 아님) — 준용 검증 **양면** | **잔존 측**(기존 가드 생존): TS-008, TS-009, TS-011, TS-030 / **채택 측**(신규 경로 발동): TS-006, TS-007 — G-4 정정. 준용 축을 잔존 한쪽으로만 표지하면 "새 경로가 실제로 동작하는가"가 축에서 빠진다 |
| ⑥ 경계·부정 | ✓ | TS-005, TS-009, TS-010, TS-011, TS-024, TS-025, TS-028, TS-032 |

---

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | `ruff` (프로젝트 미지정 — 시스템 설치본으로 정보성 실행) | Pass(정보성) | `ruff check opal/tools/memory-tool/memory_tool.py opal/tools/memory-tool/tests/test_memory_tool.py` → `E741` 경고 1건, 위치는 096 변경 범위 밖(`git diff` 대조 결과 해당 라인 미포함 — 079 트랙 선재 코드). 096 변경분(diff 832 lines)에 신규 lint 위반 0건 |
| 2 | 타입 체크 | N/A | 프로젝트에 타입 체커(mypy 등) 미설치·`docs/CONVENTIONS.md`에 지정 없음(확인 완료) — 대신 `python -m py_compile` 구문 검증 수행, 정상 컴파일 확인 |
| 3 | 포맷터 | N/A | 프로젝트에 포맷터(black 등) 미설치·CONVENTIONS.md에 지정 없음(확인 완료) |
| 4 | `code-scan validate` (@header 커버리지) | N/A | `.opal/code-scan.json` 존재하나 `code-scan` CLI 미설치(미탐지) — @header 존재 여부는 `memory_tool.py:6` description·변경이력 라인 갱신을 육안 확인(PLAN §4.4 #4 대조 완료) |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | Pass | `git diff opal/tools/memory-tool/memory_tool.py opal/tools/memory-tool/tests/test_memory_tool.py \| grep -iE "api[_-]?key\|secret\|password\|token\s*=\|Bearer "` → 0건 |
| 2 | .gitignore 확인 | Pass | `.memory_provenance.log`는 기존 경로(`promote`가 이미 사용) — 신규 산출 파일 없음. `.gitignore`에 `.opal/memory/**` 예외 규칙 확인, 096 변경으로 인한 영향 없음 |
| 3 | 경로 탈출 방어 유지 (TS-005) | Pass | RED-EVIDENCE.md §10.3 `TestReviewReferenceIntegrity` 6/6 GREEN(TS-005/qa005 포함)로 이미 실증. 본 Step에서 QA-023 리허설 중 벡터② 음성 통제(본문 실재 행 `--orphan` 거부, `memory/` 밖 미접근)로 교차 재확인 |
| 4 | `--ref` 값이 경로로 해석되지 않음 | Pass | 코드 검사(`memory_tool.py:1417-1421`) — `ref` 변수는 `.memory_provenance.log` append 문자열 포매팅(`ref={ref}`)에만 사용되고 어떤 경로 함수(`_resolve_memory_file`/`Path`/`open` 대상)에도 전달되지 않음. QA-023 리허설 provenance 로그 실측(`ref=미복원: 096 QA-023 리허설, 실작성 머신 로컬`)이 문자열 그대로 기록됨을 확인 |

## 7. 판정

**All Pass**

- 전 시나리오(TS-001~TS-039, 총 39건) 실행 완료. **Pass 38건 / Fail 0건 / 대기 1건(TS-033)**.
- TS-033은 §3 L3 정의 자체가 "본 태스크는 결정을 강제하지 않으며, 미결정도 정상 종료 조건"으로 규정한 수동 통지형 항목이며, [MUST] 지시("네가 판정하지 마라")에 따라 opal-test-agent가 판정하지 않고 `대기 — 캡틴 판정 필요`로 기록했다. 이는 §7 판정 기준의 "All Pass" 예외 조건("TS-033의 `대기`는 Pass 판정을 막지 않는다")에 해당하므로 전체 판정에 영향을 주지 않는다.
- 전건 회귀(`pytest opal/tools/memory-tool -q`): **187 passed, 31 subtests passed, exit 0** (실행 완료 시각 기준 재확인 — 기존 Step 5 실측치와 일치).
- 실환경 `.opal/MEMORY.json` SHA-256 해시: 본 TEST 단계 시작 전/종료 시점 모두 `d5ae7b4c3daeafdaa330bdf35deb2542f632322673f3e86f29d5f4f2a0a7d15c` — **완전 동일**(원본 무변경 확인, 본 단계에서 원본에 대해 수행한 조작은 read 0회 추가 — TS-021이 이미 read-only 검증 완료했으므로 재실행하지 않았고, TS-033 판단 근거 제시도 §3 표에 기재된 정적 요약을 인용했을 뿐 파일 접근 없음).
- RED 테스트 파일(`test_memory_tool.py`)·구현 파일(`memory_tool.py`) 어느 쪽도 본 TEST 단계에서 수정하지 않았다(전 구간 Read/Bash 실행만 수행, Edit 대상은 `TEST-SCENARIO.md` 1개 파일).
- FAIL 없음 — 판정 근거에 명시할 실패 ID 없음.

### PM Gate 체크 (7대 강제 룰)

- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 (grep 확인) — `grep -n "mock\|patch\|MagicMock" test_memory_tool.py` 3건 전건 재확인: `:6` @header "mock/patch/MagicMock 금지" 정책 서술, `:152` "mock이 아니라 실 파일 작성이다"(부정 서술), `:3671` "mock 아님, 실제 함수를 실행한다"(부정 서술) — 3건 전부 **금지 서술 자체**(메타-순환 오탐)이며 실제 `unittest.mock`/`@patch`/`MagicMock(`/`Mock(` 사용은 0건(TS-027 근거와 동일).
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐 — 육안 확인, 공란 없음.
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐 — TS-001~TS-039 전건 §2.2 표에 3필드 기재 확인.
- [x] 가설↔시나리오 매핑(§4) 완전 (미매핑 시나리오 없음) — §4 매핑 표 전 30행(TS-033 제외 29행 + TS-033 1행)에 "테스트 파일:케이스" 열 기재 완료. 전용 pytest 케이스가 있는 행은 `파일::클래스::메서드` 노드 ID로, 없는 행(TS-020·021·023·024 바이트 보강분·025·027·028·029·032·TS-019/026 전체 스위트분·TS-022 하위 소비자 스위트)은 "직접 CLI 실행/프로세스 실행 (pytest 케이스 없음) — §3 실행 명령 참조"로 실행 방식을 명시. TS-031은 재실행 불가한 RED 시점 증거이므로 `RED-EVIDENCE.md` §2·§3·§6.1 인용 + 대표 노드 병기. TS-033은 수동 항목이므로 "해당 없음 (수동)" 유지. AC↔가설↔시나리오 1:1 대응 미매핑 시나리오 없음.
- [x] L1/L2/L3 계층 명시 (모든 시나리오) — §3 L1(TS-001~TS-018, TS-024~TS-032, TS-034~TS-039)·L2(TS-020~TS-023)·L3(TS-033) 구획 확인.
- [x] L3 [SUPERVISOR] 마커 존재 + PM 요청 양식 첨부 (TS-033) — §3 TS-033 확인, `[SUPERVISOR]` 마커 + PM 요청 양식 원문 그대로 보존.
- [x] 리스크 가설 표(§1) H-N ID와 시나리오 TS-N 1:N 매핑 완전 — H-1~H-11 전건이 §1 표 "시나리오" 열에 대응 TS-ID를 가짐(H-11만 범위 밖으로 명시).
- [x] 모든 시나리오에 실행 방식(M1/M2/M3) 명시 — L1/L2 전건 M1(테스트 도구/실 프로세스), L3 TS-033 M3(사용자 협업) 명시 확인.
- [x] FE 변경 시 M2 시나리오 포함 — **해당 없음** (FE 변경 0, Python CLI 단일).
- [x] 목표 커버 — TASK.md R 전체가 §4에 커버 + 목표달성 시나리오 최소 1건 (TS-021, TS-023) — 둘 다 본 TEST 실행에서 Pass 확인(Step 5 기록치와 본 단계 재확인 일치), TS-015(3절 규범↔스키마 정합)도 Pass.
