# GC CONVENTION REPORT — 2607141612

<!--
  체크박스 5단계 상태 기호 (APPLY 단계가 기입):
  [ ]  open    — 미처리 (신규)
  [x]  done    — 적용 완료  ← 주석: 적용 시각 YYYY-MM-DD HH:mm + 수정 요약
  [~]  pending — 보류       ← 주석: 보류 사유
  [?]  review  — 확인 필요  ← 주석: 판단 근거 / 해결 방안
  [!]  failed  — 실패       ← 주석: 실패 사유 / 권장 대안
-->

## 1. 헤더

- 실행 일시: 2026-07-14 16:12:33 (단회 실행, read-only 진단)
- 범위: `changed_files` (태스크 060) / 대상 파일 6개
- 에이전트: opal-convention-checker
- 기준 문서: `docs/CONVENTIONS.md` (존재 — 유일 기준, 허브+링크 미적용 단일 문서)
- APPLY 수행 여부: N (read-only, 소스 미수정 — 보고서만 생성)

---

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| 총 이슈 수 | 3 |
| 심각도 분포 | Critical 0 / High 0 / Medium 1 / Low 2 / Info 0 |
| 자동 수정 가능 | 1 |
| 수동 조치 필요 | 2 |
| 파일별 상위 Top 5 | test_brain.py (1건) / config.py (1건) / ARCHITECTURE.md (1건) |
| 카테고리별 빈도 | 문서화 (2 파일) / 미사용 import (1 파일) |
| Critical/High 수 | 0 |
| 문서 업데이트 제안 수 | 0 (빈도 임계 N=3 미달 — 트리거 없음) |

---

## 3. 수정 대상 (체크리스트)

### Critical (0건)

### High (0건)

### Medium (1건)

- [ ] GC-C001 [dashboard/backend/tests/test_brain.py:7-27] @header `exports` 목록이 실제 클래스 정의와 불일치
  - 카테고리: 문서화 (헤더 정합성)
  - 위반 기준: 프로젝트(`docs/CONVENTIONS.md` §@header 규칙: "변경이력은... 헤더 내 변경이력 라인으로 갱신한다" — exports도 동일 헤더 필드로서 정확성 요구) + `opal/core/references/harness/header-rules.md` §파일 수정 시 "함수/엔드포인트 추가 → exports 갱신"
  - 설명: 이번 태스크(060)가 `exports` 배열에 신규 클래스 4개(`TestBrainPrimePool`, `TestBrainWarmInjection`, `TestBrainLifespanPrewarm`, `TestBrainPoolFixtureRegression`)를 정확히 추가했으나, 같은 배열 내 기존 드리프트를 함께 고치지 않았다. (1) 실존하는 `TestOpbrAdapterAllowedTools` 클래스(`test_brain.py:1240`)가 목록에서 누락됨. (2) 실존하지 않는 `TestConversationBrainSessionWarm` 항목이 남아 있음(실제로는 `TestConversationBrainSessionCold` 클래스 내 `test_warm_ask_uses_resume` 메서드로 흡수되어 있음). 두 드리프트 모두 태스크 060 이전부터 존재했으나(`git show HEAD` 확인), 이번 변경이 같은 필드를 수정하면서 정합화 기회를 놓쳤다. `code-scan exports` 조회 시 잘못된 결과를 유발한다(`opal/core/references/harness/header-rules.md` §code-scan 활용 가이드).
  - 해결 방안: `exports` 배열에서 `TestConversationBrainSessionWarm` 제거, `TestOpbrAdapterAllowedTools` 추가.
  - 자동 수정: N (배열 항목 판단 필요 — 단순 치환 아님)
  - 참조: `opal/core/references/harness/header-rules.md` §파일 수정 시

### Low (2건)

- [ ] GC-C002 [dashboard/backend/config.py:18] 미사용 import `os`
  - 카테고리: 미사용 import
  - 위반 기준: 프레임워크 base-convention-checklist 카테고리5 (참조용 — CONVENTIONS.md에 import 관련 명시 규칙 없음, 일반 코드 품질 기준 적용)
  - 설명: `import os` 이후 파일 전체에서 `os.` 참조가 한 곳도 없다(`Path`만 사용). 태스크 060 diff 대상은 아니나(기존부터 존재) changed_files 범위 내 발견.
  - 해결 방안: `import os` 라인 삭제.
  - 자동 수정: Y (제거)
  - 참조: [Ruff F401 — unused-import](https://docs.astral.sh/ruff/rules/unused-import/)

- [ ] GC-C003 [docs/ARCHITECTURE.md:394] `## 변경이력` 표 형식이 CONVENTIONS.md §변경이력 규칙과 다름
  - 카테고리: 문서화
  - 위반 기준: 프로젝트(`docs/CONVENTIONS.md` §변경이력: "일시 형식: YYYY-MM-DD HH:mm (KST 기준)" + "버전: semver (vX.Y.Z)")
  - 설명: 태스크 060이 추가한 신규 행("2026-07-14 | OPAL Console 브레인 질의 표에...")은 `날짜 | 변경 내용` 2열 포맷으로, CONVENTIONS.md가 요구하는 `버전 | 일시(HH:mm) | 변경내용` 3열 포맷과 다르다. 다만 ARCHITECTURE.md 전체 변경이력 표가 태스크 029부터 057까지 동일한 2열·시각 없는 포맷을 일관되게 사용해 온 기존 문서 관행이며, 이번 신규 행은 그 관행을 그대로 따른 것이다(태스크 060 단독 신규 위반 아님).
  - 해결 방안: 문서 전체 변경이력 표를 `버전/일시/변경내용` 3열로 마이그레이션하거나, ARCHITECTURE.md류 프로젝트 문서에 한해 2열 포맷을 허용 예외로 CONVENTIONS.md에 명문화. 즉시 조치보다는 문서 정책 결정 필요.
  - 자동 수정: N (문서 구조 변경 — 캡틴 결정 필요)
  - 참조: `docs/CONVENTIONS.md` §변경이력

### Info (0건)

---

## 4. 문서 업데이트 제안 (§9·§10, 트리거 발동 시만)

트리거 미발동 — 이번 실행 내 동일 fingerprint가 3개 파일 이상에서 발견되지 않았고, CONVENTIONS.md에 없는 새 카테고리도 등장하지 않았다.

참고: GC-C003과 관련해 "코드 파일 @header `changelog` 라인의 시각(HH:mm) 표기 여부"가 `config.py`/`brain_session.py`/`main.py` 3개 파일에서 일관되지 않게 관찰되었으나(3개는 날짜만, `test_brain.py`의 동일 세션 추가 항목 1건은 `13:31 KST` 시각 포함), CONVENTIONS.md §변경이력이 "스킬·에이전트·참조 문서"의 `## 변경이력` 표 포맷에 한정되어 있어 코드 `@header` 내 changelog 배열에는 명시적 시각 규칙이 없다. 규칙 모호성으로 판단해 이번 회차에서는 위반으로 분류하지 않았으나, CONVENTIONS.md에 `@header changelog` 라인 포맷(시각 포함 여부)을 명문화하는 것을 캡틴 검토용으로 제안한다.

---

## 5. 문서 작성 유도 (해당 시)

- `docs/CONVENTIONS.md` 존재 — 작성 유도 생략.
