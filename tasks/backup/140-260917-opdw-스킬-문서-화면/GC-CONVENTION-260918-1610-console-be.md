# GC CONVENTION REPORT — 260918-1610-console-be

## 1. 헤더

- 실행 일시: 시작 2026-09-18 16:10 / 완료 2026-09-18 16:10 / 소요 -
- 범위: `Console BE` (dashboard/backend/) / 대상 파일 7개
- 에이전트: opal-convention-checker
- 기준 문서: `docs/CONVENTIONS.md` 존재 (프레임워크 전역 허브, Console BE 영역별 상세 문서 미분리)
- APPLY 수행 여부: N (수동 대기, read-only 진단)

---

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| 총 이슈 수 | 1 |
| 심각도 분포 | Critical 0 / High 1 / Medium 0 / Low 0 / Info 0 |
| 자동 수정 가능 | 0 |
| 수동 조치 필요 | 1 |
| 파일별 상위 Top 5 | main.py (1건) |
| 카테고리별 빈도 | 문서화 (1 파일) |
| Critical/High 수 | 1 |
| 문서 업데이트 제안 수 | 0 |

---

## 3. 수정 대상 (체크리스트)

### Critical (0건)

### High (1건)

- [ ] GC-C001 [dashboard/backend/main.py:6] @header가 실제 라우터 등록 상태와 어긋남(현재 사실 불일치)
  - 카테고리: 문서화
  - 위반 기준: 프로젝트(CONVENTIONS.md §@header 규칙, T0) — "코드 @header에는 현재 사실만 기재한다"
  - 설명: `@header.description`은 "7개 라우터 등록(5개 read-only + brain POST + config POST/GET)"이라 서술하지만, 실제 `include_router` 호출(136-143행)은 dashboard·projects·tasks·memory·doctor·brain·config·docs_skills 8개다. `@header.depends` 배열에도 신설된 `routers.docs_skills`가 빠져 있다.
  - 해결 방안: description의 라우터 수를 8개로 정정하고 docs_skills(GET 전용 공개 표면, T140 W-7)를 서술에 포함한다. `depends` 배열에 `"routers.docs_skills"`를 추가한다.
  - 자동 수정: N
  - 참조: `opal/core/references/header-standard.md` §2.1

### Medium (0건)

### Low (0건)

### Info (0건)

---

## 4. 문서 업데이트 제안 (§9·§10, 트리거 발동 시만)

트리거 미발동 — 해당 없음.

---

## 5. 문서 작성 유도 (해당 시)

`docs/CONVENTIONS.md`는 존재하나 OPAL 프레임워크 저장소 전역 허브 문서이며, Console BE(Python/FastAPI) 영역별 상세 문서(`BE-CONVENTIONS.md` 등)로 분리되어 있지 않다(허브+링크 모델 미적용). 또한 `dashboard/backend/`에는 formatter·linter 실행 설정(pyproject.toml/ruff.toml 등)이 없어 T1 tier 자동 검증 기준을 적용하지 못했다. Python 코드 스타일 세부 규칙(들여쓰기, import 그룹핑, docstring 형식 등)은 인접 코드에서 관측한 기존 패턴(T3)만으로 판단했으며, 이번 신규 파일 7건 모두 그 관측 패턴과 일관되어 별도 위반은 없었다.

- 제안: Console BE 영역 상세 컨벤션 문서 신설 또는 pyproject.toml + ruff/black 설정 도입 검토(소유자 승인 필요, 본 실행에서는 생성하지 않음).

---

## 부록 — 검토 근거 (evidence)

- `docs/CONVENTIONS.md` 전문 Read — Console BE 전용 세부 문서 없음, 허브 참고 문구만 존재(§파일 구조 하단)
- `.opal/code-scan.json` Read — `headerSource: inline`, `console-be: dashboard/backend/`, extensions에 `.py` 포함 → 이 스코프의 @header는 인라인 기록이 T0 강제
- `dashboard/backend/`에 pyproject.toml/ruff.toml/.flake8 부재 확인
- target_files 7개 전건 Read: `main.py`, `models.py`, `routers/docs_skills.py`, `adapters/skill_docs_adapter.py`, `parsers/skill_parser.py`, `tests/test_skill_docs.py`, `tests/test_skill_docs_layout.py`
- `main.py:6-10` @header 서술 대 `main.py:136-143` 실제 include_router 목록 대조 → 불일치 확인
- 나머지 6개 파일(models.py, routers/docs_skills.py, adapters/skill_docs_adapter.py, parsers/skill_parser.py, 테스트 2건)의 @header depends/exports는 실제 import·정의와 대조해 일치 확인 — 위반 없음
- 네이밍(snake_case 파일명), import 그룹핑(stdlib→서드파티→로컬), `from __future__ import annotations` 사용, 언어 규칙(한국어 설명+영문 식별자) 모두 인접 코드 관측 패턴과 일관 — 위반 없음
