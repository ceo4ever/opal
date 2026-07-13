# GC CONVENTION REPORT — 260713-1532

<!--
  체크박스 5단계 상태 기호 (APPLY 단계가 기입):
  [ ]  open    — 미처리 (신규)
  [x]  done    — 적용 완료  ← 주석: 적용 시각 YYYY-MM-DD HH:mm + 수정 요약
  [~]  pending — 보류       ← 주석: 보류 사유
  [?]  review  — 확인 필요  ← 주석: 판단 근거 / 해결 방안
  [!]  failed  — 실패       ← 주석: 실패 사유 / 권장 대안
-->

## 1. 헤더

- 실행 일시: 시작 2026-07-13 15:30:00 / 완료 2026-07-13 15:32:00 / 소요 약 2분
- 범위: `staged 아님 — 지정 파일 3개` / 대상 파일 3개
  - `opal/tools/opal-agent/opal_agent.py` (수정)
  - `opal/tools/opal-agent/README.md` (수정)
  - `opal/tools/opal-agent/tests/test_opal_agent.py` (신규)
- 에이전트: opal-convention-checker
- 기준 문서: `docs/CONVENTIONS.md` 존재 — 단일 문서(허브) 모델 (허브+링크 모델 예시 B: OPAL 자체는 상세 링크 없음, scope="all"로 허브 전체 적용)
- APPLY 수행 여부: N (진단 전담 — 소스 파일 수정 금지, 보고서만 산출)

---

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| 총 이슈 수 | 2 |
| 심각도 분포 | Critical 0 / High 0 / Medium 1 / Low 1 / Info 0 |
| 자동 수정 가능 | 0 |
| 수동 조치 필요 | 2 |
| 파일별 상위 Top 5 | opal_agent.py (2건) / README.md (1건, GC-C002와 중복 집계) / test_opal_agent.py (0건) |
| 카테고리별 빈도 | 문서화 (2 파일: opal_agent.py, README.md) |
| Critical/High 수 | 0 |
| 문서 업데이트 제안 수 | 0 (빈도 0건 + 새 카테고리 0건 — 빈도 임계값 N=3 미달, scope 3파일 한정) |

---

## 3. 수정 대상 (체크리스트)

### Critical (0건)

### High (0건)

### Medium (1건)

- [ ] GC-C001 [opal/tools/opal-agent/opal_agent.py:1-53] 모듈 상단에 `@header` JSON 블록 부재
  - 카테고리: 문서화
  - 위반 기준: 프로젝트(CONVENTIONS.md §구현 규칙 > @header 규칙) + `opal/core/references/harness/header-rules.md` §8 + `~/.opal/references/header-standard.md` §2·§3
  - 설명: `.py`는 code-scan 지원 확장자로 @header 필수 대상이나, 현재 모듈 docstring(1~53행)은 설계·caveat·변경이력을 담은 자유서술 프로즈이며 `@header { "module": ..., "layer": ..., "domain": ..., "description": ..., "exports": [...] }` 형식의 JSON 블록을 포함하지 않는다. header-rules.md §파일 수정 시: "기존 파일에 @header가 없으면, 파일 생성 규칙과 동일하게 신규 작성한다" — 이번 태스크(059)에서 해당 파일이 실질 수정(v2.5, 필드·어댑터 추가)되어 트리거 조건에 해당한다. 참고로 `opal/tools/` 형제 도구 8개 중 6개(state-tool, memory-tool, brain-tool, git-sync-tool, tool-scan, backlog-tool, test-tool)는 이미 `@header` 블록을 준수하고 있어(`xlsx-tool`, `playwright-tool/main.py`만 동일 누락), opal_agent.py의 누락은 프로젝트 관행에서도 예외적이다.
  - 해결 방안: 기존 모듈 docstring의 설계·caveat·변경이력 프로즈는 유지하되, 최상단(shebang 다음 줄)에 `@header {"module": "opal_agent", "layer": "util", "domain": "opal-agent", "description": "...", "exports": ["call_agent", "AgentConfig", "AgentResult", "PROVIDERS", ...]}` JSON 블록을 신설 삽입한다. 캡틴 판단에 따라 "기존 docstring이 헤더 역할을 대체한다"는 예외를 CONVENTIONS.md에 명문화하는 대안도 가능(그 경우 §@header 규칙에 tool 파일 예외 조항 추가 필요).
  - 자동 수정: N (exports 목록·description 문구는 판단 필요, 구조 삽입 위치도 확인 필요)
  - 참조: `opal/core/references/harness/header-rules.md` / `~/.opal/references/header-standard.md`

### Low (1건)

- [ ] GC-C002 [opal/tools/opal-agent/opal_agent.py:43-52, opal/tools/opal-agent/README.md:177-185] 변경이력 형식이 CONVENTIONS.md §변경이력의 표(table) 포맷과 불일치(불릿 리스트 사용)
  - 카테고리: 문서화
  - 위반 기준: 프로젝트(CONVENTIONS.md §파일 구조 > 변경이력) — "`| 버전 | 일시 | 변경내용 |` 표 형식, 일시는 KST `YYYY-MM-DD HH:mm`" 예시 제시. 단, 해당 규칙 문언은 "스킬·에이전트·참조 문서"를 명시 대상으로 하며 `opal/tools/` 도구 파일은 명시적 포함/제외가 불분명함(적용 범위 모호).
  - 설명: opal_agent.py 모듈 docstring과 README.md 모두 "- v2.5 (2026-07-13 15:25 KST, 059) ..." 형태의 불릿 리스트로 변경이력을 관리한다. 날짜(KST)·태스크 번호 괄호 표기 관행은 준수하고 있으나, CONVENTIONS.md가 예시로 제시하는 표 포맷과는 다르다. 이번 태스크(059)가 신규로 도입한 편차는 아니며 v1.0(태스크 057 이전)부터 이어진 기존 관례를 그대로 따른 것이다.
  - 해결 방안: (a) 표 포맷으로 통일하거나 (b) CONVENTIONS.md §변경이력 규칙에 "코드 파일(도구) 내 변경이력은 불릿 리스트 허용" 예외를 명문화한다. 이번 태스크 범위(3파일)만으로는 강제 수정보다 문서 정합 논의 대상으로 판단, Low로 표기.
  - 자동 수정: N (형식 변경 시 과거 이력 전체 재포맷 필요 — 범위가 이번 태스크를 넘어섬)
  - 참조: TBD — docs/CONVENTIONS.md §파일 구조 > 변경이력 재정의 논의 필요 (별도 공식 린트 규칙 없음)

### Info (0건)

---

## 4. 문서 업데이트 제안 (§9·§10, 트리거 발동 시만)

트리거 미발동 — 이슈 2건 모두 서로 다른 성격(하나는 순수 누락, 하나는 형식 모호성)이며, 빈도 트리거 임계값(N=3 파일) 미달(문서화 카테고리 2파일). 새 카테고리 트리거도 없음(CONVENTIONS.md에 "문서화" 카테고리 자체는 이미 존재 — §@header 규칙, §변경이력).

---

## 5. 문서 작성 유도 (해당 시)

- `docs/CONVENTIONS.md` 존재 — 작성 유도 생략.

---

## 부가 확인 사항 (참고, 위반 아님)

- 네이밍: `opal_agent.py`(snake_case), `test_opal_agent.py`(snake_case) — CONVENTIONS.md §네이밍 규칙 "Python 파일은 snake_case" 준수.
- 들여쓰기/포맷: 3개 파일 모두 탭 혼용·trailing whitespace·EOF 개행 누락 없음(확인 완료).
- @header — `tests/test_opal_agent.py`: `layer: test` 선택 필드(`task: "059"`, `scenarios: [...]`) 포함해 header-rules.md §테스트 파일 전용 선택 필드를 정확히 준수 — 모범 사례.
- 플랫폼 분기 격리(§구현 규칙): `ProviderAdapter` 서브클래스별 분기는 정확히 어댑터 계층 내부에 위치하며, 스킬/에이전트 본문에 조건문이 노출되지 않음 — 준수.
- 코드 품질(getsentry/code-review, 추가 제안 성격): N+1/O(n²)/불필요 메모리 할당 패턴 미발견.
