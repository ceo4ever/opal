# GC CONVENTION REPORT — 2026-07-20T15-59

<!--
  체크박스 5단계 상태 기호 (APPLY 단계가 기입):
  [ ]  open    — 미처리 (신규)
  [x]  done    — 적용 완료  ← 주석: 적용 시각 YYYY-MM-DD HH:mm + 수정 요약
  [~]  pending — 보류       ← 주석: 보류 사유
  [?]  review  — 확인 필요  ← 주석: 판단 근거 / 해결 방안
  [!]  failed  — 실패       ← 주석: 실패 사유 / 권장 대안
-->

## 1. 헤더

- 실행 일시: 시작 2026-07-20 15:55 / 완료 2026-07-20 15:59 / 소요 4분
- 범위: 태스크 070 changed_files 지정본 / 대상 파일 12개
  (state_tool.py, state.schema.json, pipeline-spec.schema.json(신규), README.md,
  opal-pilot-project/dev/dev-short/dev-wireframe SKILL.md 4종 + references/pipeline.json 4종(신규),
  test_state_tool.py, docs/CONVENTIONS.md)
- 에이전트: opal-convention-checker
- 기준 문서: `docs/CONVENTIONS.md` 존재 — 단일 허브 문서 모델(허브+링크 미적용, scope 무관 허브 전체 체크)
- APPLY 수행 여부: N (수동 대기 — 본 에이전트는 진단 전담, 소스 미수정)

---

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| 총 이슈 수 | 5 |
| 심각도 분포 | Critical 0 / High 0 / Medium 1 / Low 2 / Info 2 |
| 자동 수정 가능 | 1 |
| 수동 조치 필요 | 4 |
| 파일별 상위 Top 5 | state_tool.py (3건) / test_state_tool.py (1건) / docs/CONVENTIONS.md (1건) |
| 카테고리별 빈도 | 죽은 코드 (1 파일) / 코드 품질 (1 파일) / 미사용 import (1 파일) / 문서화 (2 파일) |
| Critical/High 수 | 0 |
| 문서 업데이트 제안 수 | 0 (빈도 트리거 0건 + 새 카테고리 트리거 0건) |

**중점 점검 결과 요약**:
- 변경이력 작성 의무: SKILL.md 4종 + README.md 모두 태스크 070 행 존재 확인 (§3 참조, 위반 없음).
- @header/헤더 관례: `.py` 2개 파일(state_tool.py, test_state_tool.py)만 대상 — 둘 다 070 반영해 `description`/`exports` 갱신 확인. `.json`/`.md`는 header-rules.md §적용 대상 확장자 제외 대상이라 @header 불필요(정상).
- 배포 경계: `git status` 확인 결과 `~/.opal/` 관련 변경 없음 — 프로젝트 소스(`opal/`, `docs/`, `tasks/`)만 변경됨 (위반 없음).
- 문서 표준: 언어 규칙(한국어 본문 + 영어 식별자), YAML frontmatter, 태스크 폴더 네이밍 모두 준수 확인.

---

## 3. 수정 대상 (체크리스트)

### Critical (0건)

### High (0건)

### Medium (1건)

- [ ] GC-C001 [opal/tools/state-tool/state_tool.py:392-418, 1416-1423] `resolve_row_index()`의 `addr_label` 매개변수가 정의만 되고 함수 본문에서 전혀 사용되지 않음
  - 카테고리: 죽은 코드 (사용되지 않는 인자)
  - 위반 기준: 프레임워크 base-convention-checklist §카테고리4 (참조용 — docs/CONVENTIONS.md에 인자 사용 규칙 명시 없음)
  - 설명: `resolve_row_index(state, command, key_val=None, id_val=None, row_val=None, addr_label="task-step")` 시그니처에 `addr_label`이 선언되어 있고, `cmd_add_row`가 `addr_label="after"`로 호출하지만(line 1420-1423) 함수 본문(line 405-418)에서 `addr_label`을 참조하는 코드가 없다. 그 결과 `ERROR_CODES`의 `task_step_addr_required`/`task_step_addr_conflict`/`task_step_not_found` 메시지는 add-row의 실제 플래그명(`--after-task-step`/`--after-task-step-id`/`--after`)이 아니라 항상 `--task-step`/`--task-step-id`/`--row` 문구로 고정 출력된다 — add-row 컨텍스트에서 에러 메시지가 실제 플래그명과 불일치할 수 있다.
  - 해결 방안: (a) `addr_label`을 실제로 사용해 `ERROR_CODES` 템플릿에 플래그명을 파라미터화하거나, (b) 현재 설계상 공용 에러 코드로 충분하다고 판단되면 미사용 매개변수 `addr_label`을 제거한다.
  - 자동 수정: N
  - 참조: TBD — pylint W0613 (unused-argument) 규칙 참조 https://pylint.pycqa.org/en/latest/user_guide/messages/warning/unused-argument.html

### Low (2건)

- [ ] GC-C002 [opal/tools/state-tool/state_tool.py:115-125] 신규 `ERROR_CODES` 항목(`spec_file_not_found` ~ `task_step_key_duplicate`)의 콜론 정렬이 기존 항목들의 열 정렬 패턴과 어긋남
  - 카테고리: 들여쓰기/포맷
  - 위반 기준: 프레임워크 base-convention-checklist §카테고리2 (참조용 — docs/CONVENTIONS.md에 dict 정렬 규칙 명시 없음)
  - 설명: 기존 `ERROR_CODES` 딕셔너리는 `"key":` 뒤 공백을 값 시작 열에 맞춰 정렬해 왔으나(예: `"worker_scope_violation":         "..."`), 070에서 추가된 일부 항목(`"spec_validation_failed": "..."` 등)은 정렬 없이 단일 공백만 사용해 가독성 일관성이 깨짐.
  - 해결 방안: 070 신규 8개 항목의 콜론 뒤 공백을 기존 항목과 동일한 열에 맞춰 재정렬.
  - 자동 수정: Y (포맷터 재정렬)
  - 참조: TBD — black/prettier 미도입 시 팀 컨벤션 별도 정의 필요

- [ ] GC-C003 [opal/tools/state-tool/state_tool.py:24] `from datetime import datetime` — 파일 전체에서 실제 사용처 없음(미사용 import, 070 diff 도입분 아닌 기존 코드)
  - 카테고리: 미사용 import
  - 위반 기준: 프레임워크 base-convention-checklist §카테고리5 (참조용 — docs/CONVENTIONS.md에 import 규칙 명시 없음)
  - 설명: `grep -n "datetime("` / `datetime\.` 검색 결과 `get_kst_datetime()` 함수명·주석·문자열에만 "datetime" 문자열이 등장하고, import된 `datetime` 클래스를 실제로 호출하는 코드는 없다. `git diff`로 확인한 결과 이 import 라인은 070에서 추가된 것이 아니라 기존 코드에 이미 존재하던 것 — 070 신규 결함 아님, 기존 잔존 이슈.
  - 해결 방안: 미사용이 최종 확인되면 `from datetime import datetime` 라인 제거.
  - 자동 수정: Y (미사용 import 제거)
  - 참조: TBD — pyflakes F401 (unused import) https://www.flake8rules.com/rules/F401.html

### Info (2건)

- [ ] GC-C004 [docs/CONVENTIONS.md 전체] 허브 문서 자체에는 "## 변경이력" 섹션이 없음 — 이번 070 편집(§State 관리 1행 추가)도 변경이력 미기재
  - 카테고리: 문서화
  - 위반 기준: docs/CONVENTIONS.md §변경이력 작성 의무("스킬·에이전트·참조 문서를 변경하면 '## 변경이력' 표에 행을 추가한다") — 문언상 CONVENTIONS.md 자신도 대상으로 해석될 여지가 있으나, `git log`로 확인한 과거 이력(064/056/140 등 다수 커밋)에서도 CONVENTIONS.md 자체에 변경이력 표가 추가된 적이 없어 프레임워크 전반의 기존 관행으로 판단됨 — 070에 국한된 신규 위반 아님.
  - 설명: 프로젝트 전반에 걸쳐 반복되는 패턴이므로 이번 태스크의 결함으로 보기는 어려우나, PM 판단에 따라 "허브 문서(CONVENTIONS.md)는 변경이력 대상 제외"를 §변경이력 작성 의무 절에 명시적 예외로 추가하면 향후 동일 질문 재발을 막을 수 있음.
  - 해결 방안: (선택) CONVENTIONS.md §변경이력 작성 의무에 "단, 본 허브 문서(docs/CONVENTIONS.md) 자체는 제외" 문구 추가 검토.
  - 자동 수정: N
  - 참조: TBD — 프로젝트 정책 결정 사항, 외부 린트 규칙 해당 없음

- [ ] GC-C005 [opal/tools/state-tool/tests/test_state_tool.py:1-16] `layer: test` @header에 header-rules.md가 정의한 선택 필드 `task`/`scenarios` 미기재
  - 카테고리: 문서화
  - 위반 기준: `opal/core/references/harness/header-rules.md` §테스트 파일 전용 선택 필드 (선택 필드 — 강제 아님)
  - 설명: header-rules.md는 `layer: test` 파일에 `task`(최초 작성 태스크 번호)와 `scenarios`(TEST-SCENARIO.md S-ID 목록) 필드를 "선택"으로 안내한다. 현재 `description` 문자열 안에 태스크 번호(005/054/056/070)가 산문으로 나열되어 있어 실질적 정보는 있으나, 구조화된 `task`/`scenarios` 필드는 없음 — 선택 필드이므로 위반은 아니며 참고 제안 수준.
  - 해결 방안: (선택) `"task": "070"`, `"scenarios": ["S-1", "...", "S-14"]` 필드를 @header JSON에 추가해 기계 파싱 편의성 향상.
  - 자동 수정: N
  - 참조: `opal/core/references/harness/header-rules.md` §테스트 파일 전용 선택 필드

---

## 4. 문서 업데이트 제안 (§9·§10, 트리거 발동 시만)

트리거 미발동 — 해당 없음.

- 빈도 트리거: 동일 fingerprint가 3개 이상 파일에서 발견된 이슈 없음(모든 이슈가 단일 파일 국소 이슈).
- 새 카테고리 트리거: 발견된 모든 카테고리(죽은 코드/들여쓰기/미사용 import/문서화)가 이미 base-convention-checklist 카테고리 내에 존재하며, docs/CONVENTIONS.md에 신규 헤더 신설이 필요한 미커버 영역 없음.

---

## 5. 문서 작성 유도 (해당 시)

`docs/CONVENTIONS.md` 존재 — 작성 유도 생략.
