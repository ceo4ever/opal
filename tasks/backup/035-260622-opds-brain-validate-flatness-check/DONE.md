# DONE: brain validate 평탄성 검사 추가

> 완료일: 2026-06-22 07:36 KST | 스킬: opds | 모드: agentic
> 태스크: 035 | 입력: TASK.md / PLAN.md / TEST-SCENARIO.md

## 1. 작업 요약

`brain_tool.py`의 `validate_frontmatter`에 **선택 필드(`tags`/`sources`/`related`)의 평탄성 검사**를 추가했다. 034 후속으로 brain related 7건을 정비하던 중 드러난 **validate 사각지대**(평탄성 미검사로 중첩 리스트 `[['a','b']]`가 통과 → 검색·링크 누락 유발)를 도구가 구조적으로 차단하도록 집행한다(헌법 Core Stance "Enforce, don't just advise").

- 각 선택 필드가 존재하면 `isinstance(v, list) and all(isinstance(x, str) for x in v)` 검사. 위반 시 `f"{key} must be a flat list of strings"` violation
- None(필드 부재)·빈 리스트 `[]`는 통과(선택 필드). bool 요소도 검출(`isinstance(True, str)==False`)

## 2. 변경 파일

| 파일 | 변경 내용 |
|------|----------|
| `opal/tools/brain-tool/brain_tool.py` | `validate_frontmatter` status 검사 다음에 평탄성 검사 9줄 + @header `[035]` 변경이력. 기존 상수 `OPTIONAL_FRONTMATTER`(`:51`) 재사용 |
| `opal/tools/brain-tool/tests/test_brain_tool.py` | RED-first 신규 케이스 9개 (TestValidateFrontmatter 8 + TestValidateFlatness035 1) |

> Surgical: brain_tool.py +9줄. `parse_frontmatter`·`_score_page`·`cmd_lint`·`cmd_search`·`cmd_index`·`cmd_validate` 본문 불변.

## 3. 검증 결과

| 항목 | 결과 |
|------|------|
| RED 증거 (작성자≠구현자) | RED 워커(opal-test-agent) 작성 → 수정 전 **6 FAIL** 확보 후 GREEN 진입 |
| pytest 전체 | **109 passed, 0 failed** (기존 103 + 신규 6 관련) |
| TEST 동적검증 | L1/L2 **All Pass** (TS-001~008·010) |
| PM 직접 spot-check | 중첩 related/비문자열 sources/bool tags → 검출 ✅ / 정상·빈리스트·부재 → 통과 ✅ |
| L3 배포 (S-9) | **캡틴 직접 수행 예정** — `./scripts/install-mac.sh` 재배포 후 배포본 발효 검증 |

## 4. 설계 결정 (요약)

- **평탄성 판정**: `v is None` → continue(통과), 빈 리스트는 `all()` 빈 시퀀스 True로 자동 통과(별도 분기 불필요). 위반 = list 아님 또는 요소 중 비문자열.
- **작성자≠구현자(red-first §2)**: 검증 도구 자체를 검증하는 self-confirming 고위험 작업이므로, RED 테스트(opal-test-agent)와 GREEN 구현(opal-task-agent)을 분리 디스패치.
- **Surgical**: 기존 검증(필수5·type·status) 로직 불변, 신규 상수 0.

## 5. 후속 / 미해결

- **배포 (캡틴 직접)**: `./scripts/install-mac.sh` 재배포 시 035 평탄성 검사가 배포본 `~/.opal`에 발효된다. 재배포 후 `grep "must be a flat list of strings" ~/.opal/tools/brain-tool/brain_tool.py` ≥ 1 확인 권장.
- 이상 사항 없음.

## 6. 산출물

- `TASK.md` / `PLAN.md` / `TEST-SCENARIO.md` / `STATE.md` / `AGENTIC-LOG.md` / `DONE.md`
