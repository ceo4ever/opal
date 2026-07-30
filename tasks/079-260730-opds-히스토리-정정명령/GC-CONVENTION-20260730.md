# GC CONVENTION REPORT — 2026-07-30T12-29

## 1. 헤더

- 실행 일시: 2026-07-30 12:29 KST (opal-convention-checker 단독 체크, 소요 측정 없음)
- 범위: 태스크 079 `changed_files` 지정 4개 파일(디스패치 프롬프트가 명시한 5개 산출물 — `opal/tools/memory-tool/memory_tool.py`, `opal/tools/memory-tool/tests/test_memory_tool.py`, `opal/tools/memory-tool/README.md`, `opal/core/references/tools.md`(memory-tool 절+v2.8 행만), `opal/core/references/harness/memory-learning.md`)
- 에이전트: opal-convention-checker
- 기준 문서: `docs/CONVENTIONS.md` 존재 — 해당 문서만을 기준으로 점검(프레임워크 내장 기본값 미적용)
- APPLY 수행 여부: N (본 에이전트는 진단 전담, 읽기 전용)

---

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| 총 이슈 수 | 2 |
| 심각도 분포 | Critical 0 / High 0 / Medium 1 / Low 1 / Info 0 |
| 자동 수정 가능 | 1 |
| 수동 조치 필요 | 1 |
| 파일별 상위 Top 5 | `opal/tools/memory-tool/README.md` (1건) / `opal/core/references/tools.md` (1건) |
| 카테고리별 빈도 | 문서화(변경이력 표 형식) (2 파일) |
| Critical/High 수 | 0 |
| 문서 업데이트 제안 수 | 0 (빈도 임계값 N=3 미도달, 새 카테고리 없음) |

---

## 3. 수정 대상 (체크리스트)

### Critical (0건)

### High (0건)

### Medium (1건)

- [ ] GC-C001 [`opal/tools/memory-tool/README.md`:309] 변경이력 표 "태스크" 열에 날짜·시간·태스크번호가 혼재 삽입됨
  - 카테고리: 문서화
  - 위반 기준: 프로젝트(CONVENTIONS.md §변경이력 — "일시는 `YYYY-MM-DD HH:mm`(KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함")
  - 설명: README.md의 `## 변경이력` 표는 열 구성이 `버전 | 태스크 | 내용`이며, v1.0(045)~v2.0(078) 행 전부 "태스크" 열에 순수 태스크 번호만 기입해 왔다(예: `045`, `058`, `078`). 그런데 이번 079 행(`| v2.1 | 2026-07-30 11:49 KST (079) | ... |`)만 유일하게 "태스크" 열에 `날짜 시간 KST (태스크번호)`를 통째로 밀어넣어, 같은 열 안에서 형식이 8행 대 1행으로 불일치한다. CONVENTIONS.md는 일시를 별도 표기하되 변경내용에 태스크 번호를 괄호로 포함하라고 규정하며, 열 자체에 날짜를 섞으라는 지시는 없다.
  - 해결 방안: 079 행의 "태스크" 열을 기존 행과 동일하게 `079`만 남기고, 일시(`2026-07-30 11:49 KST`) 정보는 필요 시 "내용" 열 문두에 붙이거나 생략한다. 예: `| v2.1 | 079 | update에 --kind {memory,history} 신설 — ... (2026-07-30 11:49 KST) |`
  - 자동 수정: N (문서 내용 재작성 필요 — 단순 치환 아님)
  - 참조: TBD — 프로젝트 `docs/CONVENTIONS.md` §변경이력 규칙 링크(사내 문서, 외부 URL 없음)

### Low (1건)

- [ ] GC-C002 [`opal/core/references/tools.md`:885] memory-tool v2.8 행에 일시 `HH:mm` 시각 누락(날짜만 표기)
  - 카테고리: 문서화
  - 위반 기준: 프로젝트(CONVENTIONS.md §변경이력 — "일시 형식: `YYYY-MM-DD HH:mm` (KST 기준)")
  - 설명: tools.md 079 행은 `| v2.8 | 2026-07-30 | memory-tool ... |`로 시각(HH:mm)이 빠져 있다. 다만 이는 079가 새로 만든 결함이 아니라 tools.md 전체 변경이력(v1.0/v1.2/v1.3/v1.6/v1.7/v1.8/v2.0/v2.4/v2.6 등 9개 이상 행)에 이미 만연한 패턴이며, 079 행은 그 기존 관행을 그대로 답습한 것에 가깝다. 079 단독 책임으로 보기는 어려워 Low로 낮춤 — 빈도 트리거(N=3) 조건도 이미 사전에 tools.md 자체에서 충족되어 있어 이번 진단에서는 신규 트리거로 별도 표면화하지 않는다(§4 참조).
  - 해결 방안: 후속 tools.md 전체 정비 시 모든 행에 `HH:mm`을 일괄 보정 권고(079 단독 수정은 실익 낮음, 별도 문서 정비 태스크로 이관 권장).
  - 자동 수정: N (파일 전체 이력 재작성 필요, 079 스코프 밖)
  - 참조: TBD — 프로젝트 `docs/CONVENTIONS.md` §변경이력 규칙 링크(사내 문서, 외부 URL 없음)

### Info (0건)

---

## 4. 문서 업데이트 제안 (§9·§10, 트리거 발동 시만)

트리거 미발동 — 이번 실행 범위(4~5개 파일) 내에서 동일 fingerprint가 3개 이상 파일에 걸쳐 나타나는 이슈가 없고, CONVENTIONS.md에 없는 새 카테고리도 발견되지 않았다. (GC-C002가 지적하는 tools.md 자체의 반복 패턴은 이번 실행 대상 파일 집합이 아니라 tools.md 한 파일 "내부"의 반복이므로, 본 체커의 "파일 수 기준" 빈도 트리거 정의(§4)에는 해당하지 않는다.)

---

## 5. 문서 작성 유도 (해당 시)

- 존재 — 작성 유도 생략 (`docs/CONVENTIONS.md` 정상 로드, 위 §1~§4 전 항목을 그 규칙만으로 판정)

---

## 부록 — 점검 세부 확인 내역 (근거 인용)

- **@header description/exports 일치**: `memory_tool.py:2-25` @header — `exports`에 `cmd_init/cmd_append/cmd_update/cmd_promote/cmd_prune/cmd_show/cmd_review/cmd_delete/cmd_task_number/build_review_block/load_document/atomic_write_json/memory_lock/validate_document/_migrate_md_to_json` 14개가 모두 실제 정의(`memory_tool.py:888,917,1062,1126,1212,1273,1384,1328,1402,828,415,337,363,321,680`)와 일치. 079가 신설한 `_check_update_kind_args`(`memory_tool.py:1006`), `_apply_history_correction`(`memory_tool.py:1037`)은 exports 목록에 없음 — 그러나 선례(`_migrate_md_to_json`, 언더스코어 프리픽스이면서도 exports 등재)와 비교하면 등재 여부에 일관된 규칙이 없어 보여 위반으로 단정하지 않고 §5(getsentry 보조 참조 없음, 자체 판단)로 처리: **위반 아님, 관찰 사항** — CONVENTIONS.md에 exports 필드 등재 기준을 정의하는 규칙이 없어 판정 보류. `test_memory_tool.py:7-21` @header exports는 신규 4클래스(`TestUpdateBackCompat/TestUpdateKindHistory/TestUpdateKindArgGuard/TestUpdateHistoryLossless`) 전부 등재 — 이상 없음.
- **변경이력 작성 의무**: 5개 산출물 전부 079 태그 행 확인 — `memory_tool.py:22`(v2.1), `test_memory_tool.py:27`(v1.2), `README.md:309`(v2.1), `tools.md:885`(v2.8), `memory-learning.md:83`(v1.3). 버전 순번 전부 각 파일의 직전 버전 다음 순번과 일치(077이 tools.md v2.7을 선점했으므로 079는 v2.8 — 정상).
- **표준 라이브러리 전용**: `memory_tool.py:28-36` import 전량 표준 라이브러리(`argparse/contextlib/json/os/pathlib/re/sys/time/datetime`) — 외부 패키지 0건.
- **네이밍·언어**: 신규 식별자(`_check_update_kind_args`, `_apply_history_correction`, `_HISTORY_CORRECTABLE_FIELDS`, `--stage/--result/--path`) 전부 영문 snake_case/kebab — 위반 없음. 문서 본문(README.md/tools.md/memory-learning.md) 한국어 — 위반 없음.
- **배포 경계**: 5개 파일 전부 프로젝트 소스 경로(`opal/tools/`, `opal/core/references/`) 하위 — `~/.opal/` 직접 편집 흔적 없음.
- **테스트 컨벤션**: `test_memory_tool.py` 전체(079 신규 4클래스 포함) `unittest.mock`/`@patch`/`MagicMock` 사용 0건(grep 확인) — 실 `subprocess.run`/`subprocess.Popen` + `tempfile.TemporaryDirectory` 기반 실프로세스·실파일 검증만 사용. `ERROR_CODES` 23종 불변(TS-028 전제와 실측 일치, `memory_tool.py` 딕셔너리 리터럴 파싱 확인) — 신규 에러 코드 유입 없음.
