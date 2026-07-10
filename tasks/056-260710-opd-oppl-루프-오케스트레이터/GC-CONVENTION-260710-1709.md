# GC CONVENTION REPORT — 260710-1709

<!--
  체크박스 5단계 상태 기호 (APPLY 단계가 기입):
  [ ]  open    — 미처리 (신규)
  [x]  done    — 적용 완료  ← 주석: 적용 시각 YYYY-MM-DD HH:mm + 수정 요약
  [~]  pending — 보류       ← 주석: 보류 사유
  [?]  review  — 확인 필요  ← 주석: 판단 근거 / 해결 방안
  [!]  failed  — 실패       ← 주석: 실패 사유 / 권장 대안
-->

## 1. 헤더

- 실행 일시: 2026-07-10 17:09 (KST)
- 범위: `all` (Framework — Markdown·Bash·Python) / 대상 파일 23개 (056 changed_files)
- 에이전트: opal-convention-checker
- 기준 문서: `docs/CONVENTIONS.md` 존재 — 단일 진입점 모델(허브+링크 미적용, 프레임워크 자체 규약 §참고 준용). scope=all이므로 허브 전체 적용.
- APPLY 수행 여부: N (수동 대기 — 진단 전담, 소스 미수정)

---

## 2. 요약 지표

> **[갱신 — 260710-1709 델타 재검 반영]** 최초 판정 시점 지표는 아래 표 하단 각주로 보존한다. 재검 상세는 §6 참조.

| 지표 | 값 (재검 후 현재) |
|------|-----|
| 총 이슈 수 | 7 (resolved 5 / open 2) |
| 심각도 분포 | Critical 0 / High 0 / Medium 0 / Low 1 / Info 1 |
| 자동 수정 가능 (잔여 open 기준) | 1 (GC-C006) |
| 수동 조치 필요 (잔여 open 기준) | 0 |
| 파일별 상위 Top 5 (잔여 open 기준) | opal/tools/state-tool/tests/test_state_tool.py (1건, GC-C006) |
| 카테고리별 빈도 (잔여 open 기준) | 미사용 import (1건, 1파일) |
| Critical/High 수 | 0 |
| 문서 업데이트 제안 수 | 0 |

> 최초 판정(2026-07-10 17:09, fix 이전): 총 이슈 7건 — Critical 0 / High 1 / Medium 3 / Low 2 / Info 1, 자동 수정 가능 4 / 수동 조치 필요 3.

---

## 3. 수정 대상 (체크리스트)

### Critical (0건)

### High (1건 — 0건 open / 1건 resolved)

- [x] GC-C001 [opal/core/references/opal-harness.md:239-248] `backlog-tool` 신규 도구가 §9 "현재 등록된 도구" 표에 미등록 (적용 2026-07-10 17:2x — resolved: §9 표에 backlog-tool 행 추가(:250) + test-tool 행 설명 8서브명령으로 동시 현행화 + 변경이력 v6.0(056) 추가. §6 재검 결과 참조)
  - 카테고리: 문서화
  - 위반 기준: 프로젝트(docs/CONVENTIONS.md §구현 규칙 "도구 우선 원칙" — "파일 처리·데이터 변환 작업이 필요할 때, 직접 코드를 작성하기 전에 OPAL 도구(`~/.opal/tools/`)를 우선 검토한다") + `opal-harness.md` §9 "현재 등록된 도구" 표(xlsx-tool/state-tool/brain-tool/test-tool/code-scan/cmux-tool)
  - 설명: 056에서 `opal/tools/backlog-tool/`(6서브명령 CLI, oppl Loop 2 백로그 SSOT 관리 도구)이 신설되었고 `opal-pilot-project-loop/SKILL.md`가 이를 핵심 도구로 다수 인용하지만, `opal-harness.md` §9 표에는 행이 추가되지 않았다. 이 표는 "도구 우선 원칙" 1단계("`~/.opal/references/tools.md`를 Read하여 사용 가능한 도구 목록을 확인")의 참조 대상이므로, 미등록 시 향후 워커/PM이 backlog-tool의 존재를 인지하지 못하고 직접 코드를 재구현할 위험이 있다.
  - 해결 방안: `opal-harness.md` §9 표에 `| backlog-tool | oppl 2-루프 오케스트레이터 백로그(backlog.json) SSOT 관리 — 6서브명령(init/add-task/select-next/mark/done-check/show) | oppl Loop 2 태스크 관리 시 |` 행 추가 + §변경이력 갱신(태스크 번호 056 포함).
  - 자동 수정: N (문서 반영은 PM 승인 후 처리 — CONVENTIONS.md §구현 규칙 Guards)
  - 참조: `opal/core/references/opal-harness.md:239-248`, `opal/tools/backlog-tool/README.md`

### Medium (3건 — 0건 open / 3건 resolved)

- [x] GC-C002 [opal/tools/state-tool/README.md:288-296] 변경이력 표에 이질적 행 혼입 (적용 — resolved: 이물 행 `xlsx-tool 패턴 | ...` 제거 확인. 변경이력 표가 `버전/일시/태스크/변경내용` 4열 스키마로만 구성됨. §6 참조)
  - 카테고리: 문서화
  - 위반 기준: 프로젝트(docs/CONVENTIONS.md §파일 구조 "변경이력" — 표 스키마는 `버전 | 일시 | 변경내용`)
  - 설명: `## 변경이력` 표(288~295행, 컬럼: 버전/일시(KST)/태스크/변경 내용) 마지막 줄(296행)에 `| xlsx-tool 패턴 | opal/tools/xlsx-tool/run.sh:1-12 | OPAL Tools 래퍼 패턴 |`라는, 컬럼 구조가 다른(3열, 변경이력 스키마 아님) 행이 섞여 있다. 내용상 "관련 문서" 표(280~286행, 컬럼: 문서/경로/참조 이유)에 들어가야 할 행이 변경이력 표 밑에 잘못 붙은 것으로 보인다.
  - 해결 방안: 해당 행을 "## 관련 문서" 표로 이동하거나(의도가 그것이라면), 불필요하면 삭제.
  - 자동 수정: Y (행 이동 — 단순 위치 교정)
  - 참조: `opal/tools/state-tool/README.md:280-296`

- [x] GC-C003 [opal/skills/opal-pilot-project-loop/SKILL.md:557-561] 변경이력 일시 형식 위반 (HH:mm 누락) (적용 — resolved: `v1.0 | 2026-07-10 16:44 | 초기 작성 (056)`으로 시각 보강 확인. §6 참조)
  - 카테고리: 문서화
  - 위반 기준: 프로젝트(docs/CONVENTIONS.md §파일 구조 "변경이력" — "일시 형식: `YYYY-MM-DD HH:mm` (KST 기준)")
  - 설명: SKILL.md 자체 변경이력 행이 `| v1.0 | 2026-07-10 | 초기 작성 (056) |`로 시각(HH:mm)이 누락되어 있다. 동일 태스크(056)에서 함께 작성된 하위 참조 문서 4종(`references/loop-control.md`, `contract.md`, `journey-flow.md`, `verification.md`)은 모두 `2026-07-10 16:33`으로 시각까지 정확히 기재되어 있어, SKILL.md 본문만 형식이 어긋나며 내부 일관성도 깨진다.
  - 해결 방안: `2026-07-10 16:33` (또는 실제 작성 시각)으로 갱신.
  - 자동 수정: Y (단순 치환)
  - 참조: `opal/skills/opal-pilot-project-loop/SKILL.md:561`, 비교 대상 `opal/skills/opal-pilot-project-loop/references/loop-control.md:153`

- [x] GC-C004 [docs/CONVENTIONS.md:38-49] §약어(Alias) 표에 신규 오케스트레이터 별칭 `oppl` 누락 (적용 — resolved: `| oppl | opal-pilot-project-loop |` 행이 `oppd` 다음·`opi` 이전에 추가됨 확인. §6 참조)
  - 카테고리: 네이밍
  - 위반 기준: 프로젝트(docs/CONVENTIONS.md §네이밍 규칙 "약어(Alias)" 표 자체의 완전성 — SSOT 정합)
  - 설명: 056에서 `opal-pilot-project-loop`(별칭 `oppl`)가 신규 오케스트레이터로 등록되었고(`opal-skills-registry.json`, `state-tool` `--skill` enum, `agents.md` 등에 모두 반영됨) `docs/CONVENTIONS.md` §약어 표(라인 40~49, opd/opds/opdw/opwt/opp/oppd/opi/opsdd 8종만 등재)에는 `oppl` 행이 추가되지 않았다. 이 표는 컨벤션 체커 자신이 유일 기준으로 삼는 문서이므로, 누락 시 향후 네이밍 체크가 `oppl`을 미등록 약어로 오판할 위험이 있다.
  - 해결 방안: `| oppl | opal-pilot-project-loop |` 행 추가.
  - 자동 수정: N (docs/CONVENTIONS.md 갱신은 CONVENTIONS.md §구현 규칙 Guards — 캡틴 승인 후 오케스트레이터가 반영)
  - 참조: `docs/CONVENTIONS.md:38-49`, `opal/core/references/opal-skills-registry.json:149-162`

### Low (2건 — 1건 open / 1건 resolved)

- [x] GC-C005 [opal/core/references/opal-harness.md:246] test-tool 등록 설명이 056 신규 서브명령(scenario-*) 반영 전 상태로 정체 (적용 — resolved: "8서브명령 resolve/check/unit/integration + scenario-init/lock/mark/status"로 현행화 확인, GC-C001과 동일 편집에서 함께 반영됨. §6 참조)
  - 카테고리: 문서화
  - 위반 기준: 프로젝트(docs/CONVENTIONS.md §변경이력 작성 의무 — 참조 문서 변경 시 최신 상태 유지 정신)
  - 설명: §9 표의 test-tool 행 설명이 "4서브명령 resolve/check/unit/integration"으로만 되어 있으나, 056에서 `scenario-init`/`scenario-lock`/`scenario-mark`/`scenario-status` 4개가 추가되어 실제로는 8서브명령 상태다(`opal/tools/test-tool/README.md` v1.1 참조). 기능 자체는 정상 동작하며 도구 존재는 이미 알려져 있어 GC-C001(신규 미등록)보다 영향도가 낮다.
  - 해결 방안: 설명을 "8서브명령(resolve/check/unit/integration + scenario-init/scenario-lock/scenario-mark/scenario-status)"으로 갱신.
  - 자동 수정: N
  - 참조: `opal/core/references/opal-harness.md:246`, `opal/tools/test-tool/README.md:271-276`

- [ ] GC-C006 [opal/tools/state-tool/tests/test_state_tool.py:33] 미사용 import (`patch`, `MagicMock`)
  - 카테고리: 미사용 import
  - 위반 기준: 프레임워크 base-convention-checklist §5(참고용, 프로젝트 CONVENTIONS.md에 import 규칙 명문은 없어 "추가 제안"으로 표시) + 파일 자체 헤더 정신("mock/patch/MagicMock 금지" — `red-first.md §4`)과의 모순
  - 설명: `from unittest.mock import patch, MagicMock`(33행)로 두 심볼을 가져오지만, 파일 전체에서 `patch(`/`MagicMock(` 형태의 실제 코드 호출은 없다 — 등장하는 모든 위치가 테스트 픽스처 문자열 리터럴(`"svc = MagicMock()\n"`) 또는 메서드명/주석/독스트링뿐이다. 이 파일은 자신의 테스트 원칙으로 "mock/patch/MagicMock 금지"를 명시하고 있어(3109행, 3500행 등) 정작 금지 대상 심볼을 계속 import하고 있는 점이 아이러니하다. 단, 이 import 라인 자체는 056 diff가 추가한 것이 아니라 기존 코드(사전 존재)이며, 056은 `subprocess` import 1건만 추가했다.
  - 해결 방안: 실제 코드에서 사용하지 않는다면 `patch, MagicMock` import 제거(회귀 스위트 재실행으로 안전성 확인 후).
  - 자동 수정: Y (미사용 import 제거 — 단, 광범위 파일이므로 제거 전 전체 회귀 1회 권장)
  - 참조: `opal/tools/state-tool/tests/test_state_tool.py:33`, https://docs.astral.sh/ruff/rules/unused-import/

### Info (1건)

- [ ] GC-C007 [전체 target_files] @header/변경이력/테스트 필드 컴플라이언스는 대부분 양호
  - 카테고리: 문서화 (참고 — 위반 아님, 정상 확인 기록)
  - 위반 기준: 없음 (정상 사례 기록)
  - 설명: 중점 점검 대상이었던 신규 `.py` 4파일(`backlog_tool.py`, `tests/test_backlog_tool.py`, `lib/scenario.py`, `tests/test_scenario.py`)의 `@header` 블록은 module/layer/domain/description/exports 필수 필드를 모두 갖췄고, 테스트 2파일은 `task`/`scenarios` 선택 필드도 정확히 기재했다(`header-standard.md` §2, `header-rules.md` §테스트 파일 전용 선택 필드 준수). `opal-evaluator-agent/AGENT.md`, `opal-pilot-project-loop/references/*.md` 4종의 변경이력도 (SKILL.md 본문 1건 제외) 모두 `YYYY-MM-DD HH:mm` 형식 + 태스크 번호(056)를 정확히 갖췄다. `opal-skills-registry.json`·`agents.md`의 신규 항목(oppl, opal-evaluator-agent) 등록과 변경이력도 상호 정합적이다.
  - 해결 방안: 조치 불요 — 참고 기록.
  - 자동 수정: N/A
  - 참조: TBD — 내부 확인 기록(공식 린트 규칙 없음)

---

## 4. 문서 업데이트 제안 (§9·§10, 트리거 발동 시만)

트리거 판정 결과: **빈도 트리거 미발동**(동일 fingerprint 3개 이상 파일에서 반복된 이슈 없음 — GC-C001/C005 두 건 모두 `opal-harness.md` 한 파일에 집중), **새 카테고리 트리거 미발동**(모든 이슈가 기존 CONVENTIONS.md 헤더 범주— 도구 우선 원칙/변경이력/약어— 내에서 설명 가능).

참고(비공식 트리거, 심각도 기반): High 1건(GC-C001)이 단일 파일에 집중되어 있으나 파급 범위(향후 워커의 도구 재발견 실패 위험)를 고려해 별도 우선 처리를 권장한다. GC-C001/C004는 `docs/CONVENTIONS.md`·`opal-harness.md` 자체의 SSOT 최신화 누락이므로, 오케스트레이터가 CLOSE 이전에 캡틴 승인을 받아 두 문서에 반영할 것을 제안한다(§5 조치 아님 — 정식 트리거 항목 아니므로 GC-DP 채번 생략).

---

## 5. 문서 작성 유도 (해당 시)

`docs/CONVENTIONS.md` 존재 — 작성 유도 생략.

---

## 6. 재검 결과 (델타 재검 — PM fix 워커 반영 확인)

> 실행: PM이 fix 워커로 GC-C001(High)·GC-C002~004(Medium)·GC-C005(Low, GC-C001과 동일 편집에 연계) 4건을 수정. 본 절은 해당 4개 파일만 재스캔한 델타 재검 결과다(전체 23개 target_files 재스캔 아님).

### 6.1 finding별 재확인

| ID | 심각도 | 대상 | 상태 | 확인 근거 |
|----|--------|------|------|----------|
| GC-C001 | High | `opal/core/references/opal-harness.md` §9 | **resolved** | `:250` `\| backlog-tool \| backlog.json SSOT 관리 — 6 서브명령 init/add-task/select-next/mark/done-check/show (oppl 백로그) \| oppl 루프(백로그 생성·태스크 선택·종료 판정) 시 \|` 행 확인. 변경이력에 `v6.0 \| 2026-07-10 \| §9 등록 도구 표에 backlog-tool 행 추가 ... test-tool 행 설명 현행화 ... (056)` 확인 |
| GC-C005 | Low | `opal/core/references/opal-harness.md:246` | **resolved** | `test-tool \| 테스트 단계별 도구 결정론적 집행 — 8서브명령 resolve/check/unit/integration + scenario-init/lock/mark/status \| ...` 로 현행화 확인 (GC-C001과 동일 편집·동일 v6.0 변경이력 행에서 함께 처리됨) |
| GC-C002 | Medium | `opal/tools/state-tool/README.md` 변경이력 표 | **resolved** | "## 관련 문서" 표(4행: PLAN.md/TASK.md/state.schema.json/xlsx-tool 패턴) + "## 변경이력" 표(4행: v1.0~v1.3, 버전/일시/태스크/변경내용 4열만) 로 완전 분리 확인. 변경이력 표에 이물 행 없음 |
| GC-C003 | Medium | `opal/skills/opal-pilot-project-loop/SKILL.md:561` | **resolved** | `\| v1.0 \| 2026-07-10 16:44 \| 초기 작성 (056) \|` — `HH:mm` 보강 확인. 하위 참조 문서 4종(loop-control/contract/journey-flow/verification, 모두 `16:33`)과 형식 정합(값 차이 6~44분은 실작성 시각 차로 정상, 형식 자체는 통일) |
| GC-C004 | Medium | `docs/CONVENTIONS.md:38-49` §약어(Alias) | **resolved** | `\| oppl \| opal-pilot-project-loop \|` 행이 `oppd` 다음·`opi` 이전에 추가됨 확인(현재 9종 등재: opd/opds/opdw/opwt/opp/oppd/oppl/opi/opsdd) |
| GC-C006 | Low | `opal/tools/state-tool/tests/test_state_tool.py:33` | **open (미수정 — 확인)** | `from unittest.mock import patch, MagicMock` 그대로 유지, 실제 코드 호출(`patch(`/`MagicMock(`) 없음 — 이전과 동일. PM이 "범위 외" 판정(056 diff 비대상, 별도 태스크 소관)한 것으로 확인. 상태 변경 없음 |
| GC-C007 | Info | 전체 target_files | **open (정보성, 조치 불요 유지)** | 정상 사례 기록 — 재검 대상 아님. `docs/CONVENTIONS.md`에 `## 변경이력` 섹션 자체가 없는 구조는 이번 재검에서도 확인(97행 이후 섹션 부재 유지) — PM이 "구조 불변 원칙(프레임워크 SSOT 문서 자체 변경이력 섹션 미보유가 기존 관례)"으로 신규 생성하지 않기로 승인. GC-C007 범위 내 참고 사항으로 흡수, 별도 신규 이슈 채번 안 함 |

### 6.2 신규 위반 스캔 (4개 수정 파일 한정)

- `opal/core/references/opal-harness.md`, `opal/tools/state-tool/README.md`, `opal/skills/opal-pilot-project-loop/SKILL.md`, `docs/CONVENTIONS.md` 4개 파일 대상 재스캔.
- 파일 말미 개행(EOF `\n`) 4개 파일 모두 정상.
- 줄 끝 trailing whitespace 4개 파일 모두 0건.
- `opal-harness.md` §9 표: 신규 2개 셀(`backlog-tool` 행, `test-tool` 행 설명)의 파이프(`|`) 컬럼 수가 기존 행과 동일(3열: 도구/용도/트리거 조건) — 표 구조 깨짐 없음.
- `opal-harness.md` 변경이력: `v6.0 | 2026-07-10 | ... (056)` 신규 행의 일시 형식은 `YYYY-MM-DD`만 기재되어 있어(예: v5.7·v5.9 등 기존 관례와 동일 — 이 문서 변경이력은 원래부터 시각 없이 날짜만 기재하는 관례가 혼재) 새 위반으로 볼 근거가 약하다(기존 문서 자체 관례 — GC-C003과 달리 이 문서는 애초에 CONVENTIONS.md §변경이력 "HH:mm" 규칙을 시각 포함/미포함 혼용해온 이력이 있음). 참고 사항으로만 기록 — 신규 GC-C 채번하지 않음.
- `state-tool/README.md` 변경이력 표: 4행 모두 4열 스키마 준수, 신규 이물 행 없음.
- `docs/CONVENTIONS.md` 약어 표: 9행 모두 2열(약어/풀네임) 스키마 준수, 신규 이물 행 없음.
- **결론: 4개 파일에서 fix로 인한 신규 위반 없음.**

### 6.3 최종 상태

- resolved 5건: GC-C001(High), GC-C002(Medium), GC-C003(Medium), GC-C004(Medium), GC-C005(Low)
- open 유지 2건: GC-C006(Low, PM 범위 외 판정), GC-C007(Info, 조치 불요 참고 기록)
- 잔여 심각도: Critical 0 / High 0 / Medium 0 / Low 1 / Info 1
- 신규 위반: 없음
