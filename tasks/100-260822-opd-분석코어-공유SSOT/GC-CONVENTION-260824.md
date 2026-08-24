# GC-CONVENTION 보고서 — 태스크 100 (분석코어-공유SSOT)

## 1. 헤더

- **실행 일시**: 2026-08-24 14:46 (KST)
- **범위(scope)**: 전체(단일 문서 프로젝트, 허브+링크 모델 미적용 — `docs/CONVENTIONS.md` 단일 진입점)
- **기준 문서**: `docs/CONVENTIONS.md` (282줄, `check_enabled = true`) — 프레임워크 내장 기본값 없음, 본 문서 규칙만 적용
- **호출 목적**: TEST PM Gate 「컨벤션 자동 진단 PASS」(`opal/skills/opal-pilot-dev/references/pipeline.json` id 13 checklist) 근거 산출
- **관측 스코프**: 아래 15개 대상 파일 (`git status --short` + `git diff --stat` 실측). 이 보고서의 모든 계수는 이 15개 파일에 대한 것이며, 동일 커밋 diff에 포함된 그 외 파일(`.opal/MEMORY.json`, `opal/core/PRINCIPLES.md`, `opal/core/references/opal-doc-standard.md`, `opal/core/references/opal-skills-registry.json`, `opal/skills/opal-grill/` 등)은 **본 진단 범위 밖**이다(디스패치 지시서가 지정한 15건에 한정).

```
opal/core/references/harness/analysis-core.md   (신규, untracked)
opal/core/references/opal-harness.md
opal/skills/op-dev-analysis/SKILL.md
opal/skills/op-dev-analysis/references/analysis-guide.md
opal/skills/op-dev-analysis/references/tech-context-guide.md
opal/skills/op-dev-plan/references/plan-guide.md
opal/skills/op-dev-qa/SKILL.md
opal/skills/op-dev-qa/references/qa-dev-guide.md
opal/skills/opal-pilot-dev/SKILL.md
opal/skills/opal-pilot-dev/references/pipeline.json
opal/tools/state-tool/state_tool.py
opal/tools/state-tool/tests/test_state_tool.py
opal/tools/state-tool/README.md
docs/ARCHITECTURE.md
docs/PROJECT.md
```

---

## 2. 요약 지표

| 심각도 | 건수 |
|--------|------|
| Critical | 0 |
| High | 0 |
| Medium | 1 |
| Low | 0 |
| Info | 0 |

**PM Gate 판정 근거**: Critical/High **0건** — 「컨벤션 자동 진단 PASS」 조건(Critical/High 0건) 충족.

---

## 3. 수정 대상

### GC-C001 (Medium)

- **파일:줄**: `opal/tools/state-tool/tests/test_state_tool.py:6` (description 필드), `:7-22` (exports 배열, 마지막 항목 `TestT098Add2RootDerivation`)
- **카테고리**: 문서화 (@header 갱신 누락)
- **위반 기준**: `docs/CONVENTIONS.md` §@header 규칙(210~216행) — "코드 파일을 생성·수정할 때 파일 상단에 @header 블록을 작성한다" + "변경이력은 별도 표 또는 헤더 내 변경이력 라인으로 갱신한다". 기록 소스는 `.opal/code-scan.json`의 전역 `headerSource: "inline"`(실측 확인)이므로 인라인 @header가 유일한 기록 위치다.
- **설명**: 이번 커밋에서 `TestT100DirectionEvidence` 클래스(415줄, `test_state_tool.py:8987`)가 신규 추가되었으나(`git diff --stat` 기준 `+415` 라인), 파일 최상단 @header 블록의 `description`(:6)과 `exports`(:7-22) 모두 `098 ADD-2`(`TestT098Add2RootDerivation`)에서 멈춰 있고 `TestT100DirectionEvidence`에 대한 서술·exports 등재가 없다. 같은 태스크의 `state_tool.py` 헤더(:6)는 "100: `verify --evidence-check` 파싱 대상 확장(F-007, PLAN §3.7.2) — ..."로 정상 갱신되어 있어, 자매 파일 간 갱신 불일치가 관측된다.
- **해결 방안**: `test_state_tool.py` @header `description`에 "100: `TestT100DirectionEvidence` 신설 — ..." 요약 문장을 추가하고, `exports` 배열에 `"TestT100DirectionEvidence"`를 추가한다.
- **자동 수정**: N (서술 문장 내용은 사람 판단 필요 — 파일 구조 변경 아님, 단 문구 신설이라 자동 치환 부적합)
- **참조 URL**: `opal/core/references/header-standard.md` §7 (2소스 표현), `opal/core/references/harness/header-rules.md`

---

## 4. 문서 업데이트 제안

- **빈도 트리거**: 발동 없음 — 동일 fingerprint 이슈가 3개 파일 이상에서 재현되지 않음(이슈 총 1건).
- **새 카테고리 트리거**: 발동 없음 — GC-C001은 `docs/CONVENTIONS.md`의 기존 "@header 규칙" 절에 이미 포섭되는 카테고리이며, 헤더에 새 규범 조항이 필요한 사안이 아니다(집행 누락 사례일 뿐).
- **심각도 트리거**: 해당 없음 — Critical/High 0건.

---

## 5. 문서 작성 유도

해당 없음 — `docs/CONVENTIONS.md` 존재 확인, 초안 생성 절차 불필요.

---

## 6. 특히 확인할 항목 6종 — 판정 결과 (자기완결 근거 포함)

### (1) 변경이력 의무

**판정: 통과 (12/12 md 문서 + 2/2 py 헤더 중 1건 staleness → 위 GC-C001로 반영)**

관측 스코프: 대상 15건 중 "스킬·에이전트·참조 문서"(`docs/CONVENTIONS.md` §변경이력 작성 의무 적용 대상)에 해당하는 md 문서 12건 전수 + 코드 파일 2건(`state_tool.py`, `test_state_tool.py`, @header 내 변경이력 라인 방식) + `pipeline.json`(JSON, md 변경이력·헤더 규정 비적용 대상 — 위반 아님).

실행 명령 및 결과(각 파일 마지막 `## 변경이력` 표/헤더에서 태스크 100 행 존재 여부, `grep -n "100" <file>` + 표 tail 확인):

| # | 파일 | 100행 존재 | 근거 |
|---|------|-----------|------|
| 1 | `opal/core/references/harness/analysis-core.md` | ✓ | `:183-184` v1.0/v1.1 (100) |
| 2 | `opal/core/references/opal-harness.md` | ✓ | `:322` v7.4 (100) |
| 3 | `opal/skills/op-dev-analysis/SKILL.md` | ✓ | `:200`(tail) v1.6 (100) |
| 4 | `opal/skills/op-dev-analysis/references/analysis-guide.md` | ✓ | v1.1 (100), 파일 말미 |
| 5 | `opal/skills/op-dev-analysis/references/tech-context-guide.md` | ✓ | 2026-08-23 12:42, 태스크 100, 파일 말미 |
| 6 | `opal/skills/op-dev-plan/references/plan-guide.md` | ✓ | `:461`(tail) v2.6 (100) |
| 7 | `opal/skills/op-dev-qa/SKILL.md` | ✓ | `:198`(tail) v1.4 (100) |
| 8 | `opal/skills/op-dev-qa/references/qa-dev-guide.md` | ✓ | `:164`(tail) v1.4 (100) |
| 9 | `opal/skills/opal-pilot-dev/SKILL.md` | ✓ | `:427`(tail) v5.6 (100) |
| 10 | `opal/tools/state-tool/README.md` | ✓ | v1.9 (100), 파일 말미 |
| 11 | `docs/ARCHITECTURE.md` | ✓ | `:478` 2026-08-23 13:09, "태스크 100" 명시(표 상단 삽입 — tail 확인만으론 누락되어 재확인 요망 사례) |
| 12 | `docs/PROJECT.md` | ✓ | `:240` 2026-08-23, "태스크 100" 명시(표 상단 삽입) |
| 13 | `opal/tools/state-tool/state_tool.py` | ✓ | @header description 말미 "100: `verify --evidence-check` 파싱 대상 확장..." |
| 14 | `opal/tools/state-tool/tests/test_state_tool.py` | ✗ | @header description(:6)·exports(:7-22) 모두 098 ADD-2에서 정지, `TestT100DirectionEvidence`(:8987, +415줄) 미반영 → **GC-C001** |
| 15 | `opal/skills/opal-pilot-dev/references/pipeline.json` | 해당없음 | JSON 설정 파일 — §변경이력 작성 의무 적용 대상(스킬/에이전트/참조 문서) 아님, 위반 아님 |

주의: `docs/ARCHITECTURE.md`·`docs/PROJECT.md`는 변경이력 표가 **날짜 역순**이라 `tail`만으로는 최신 행이 보이지 않는다 — `grep -n "100"`으로 표 상단 삽입 행을 직접 확인해 오탐(false negative)을 피했다(1차 tail 확인 시 누락으로 오판할 뻔한 사례, 재확인 절차로 정정).

### (2) 배포 경계

**판정: 통과 (0건)**

관측 스코프: 대상 15건 전부의 파일 경로.

실행 명령: `git status --short` (세션 시작 시점) — 변경된 15개 파일 전부가 프로젝트 소스 경로(`opal/`, `docs/`) 하위이며 `~/.opal/`(배포본) 경로는 diff에 등장하지 않는다. 15개 파일의 절대경로 프리픽스를 확인한 결과 `~/.opal` 또는 사용자 홈 배포 디렉토리를 가리키는 항목 0건.

### (3) 플랫폼 분기 격리

**판정: 통과 (0건)**

관측 스코프: md/json 대상 12개 문서(코드 2개·JSON 1개 제외 — 플랫폼 조건문은 본문 서술에 한정된 규칙이라 소스코드 인자/테스트 데이터 문자열은 스코프에서 제외).

실행 명령:
```bash
for f in <12개 파일>; do
  git diff -- "$f" | grep -E '^\+' | grep -viE '^\+\+\+' | grep -E 'Claude|Cursor|Gemini|Antigravity|claude|cursor|gemini'
done
```
결과: 매치 0건 (신규 추가된 라인 중 플랫폼명 언급 없음). `analysis-core.md` §1 말미에 "[MUST] 플랫폼 조건문 금지" 문구 자체가 포함되어 있으나 이는 규칙 서술이지 조건문 추가가 아니다.

### (4) State 관리 (PM Gate 정의 SSOT)

**판정: 통과 (0건 중복)**

관측 스코프: `opal/skills/opal-pilot-dev/references/pipeline.json`(gate.checklist 신규 채움, id 4 `analysis.pm_gate`) ↔ `opal/skills/opal-pilot-dev/SKILL.md`(동일 diff에서 STEP 2 디스패치 프롬프트에 `**분석 질문**:` 슬롯 1줄만 추가).

실행 명령:
```bash
grep -n "참조 문서 — code-scan\|확정 입력 판정\|다음 단계 입력\|소스코드 원문 블록 0건" opal/skills/opal-pilot-dev/SKILL.md
```
결과: 매치 0건 — `pipeline.json`에 신규 채워진 4개 checklist 문구가 `SKILL.md`에 복제되지 않았다. `SKILL.md` v5.6 변경이력 행 자체가 "PM Gate checklist 문구 복제 없음(SSOT는 pipeline.json 유지) (100)"이라고 명시하여 의도적 준수를 확인.

### (5) 수치·목록 복제 금지 (analysis-core.md 신설에 따른 검증)

**판정: 통과 — 오히려 기존 중복 4건을 능동 제거**

관측 스코프: `analysis-core.md`(신규) 본문 전체(184줄) + `analysis-guide.md`/`tech-context-guide.md`/`plan-guide.md` diff.

근거:
- `analysis-core.md:26` "결과가 불충분한 경우의 분기 판정은 `header-rules.md` §빈 결과 폴백이 소유한다(**본 문서는 분기 조건·수치를 복제하지 않는다**)" — 명시적 비복제 선언.
- `analysis-core.md:25` E1~E5 근거 등급은 라벨만 사용하고 `citation-rules.md` §9로 원문 소유권을 넘김(등급표 재정의 없음).
- MCP 목록: `tech-context-guide.md` diff에서 하드코딩 매핑 5행(context7/supabase/github/figma/sentry)을 **삭제**하고 "[MUST] 등록 MCP의 이름·개수를 이 문서에 복제하지 마라"로 교체(`mcps.md` 조회로 일원화) — 기존 위반을 이번 태스크가 시정.
- `analysis-guide.md`/`plan-guide.md`: 분석 깊이 기준표·6영역 축·영향 범위 체크리스트 본문을 삭제하고 `analysis-core.md §N` 포인터로 전환(각 diff에서 확인).
- 루프 상한(재시도 횟수 등)·근거 등급 수치표·MCP 전체 목록의 원문 재기재는 15건 전체에서 0건.

실행 명령: `git diff -- opal/skills/op-dev-analysis/references/analysis-guide.md opal/skills/op-dev-analysis/references/tech-context-guide.md opal/skills/op-dev-plan/references/plan-guide.md` (본문 상단 §3에서 발췌한 3개 diff 전량 육안 대조).

### (6) 인용 형식 (경로:줄번호가 저장소 루트 기준인지)

**판정: 통과 (0건 축약 위반)**

관측 스코프: md 문서 12건. 정규식 전종 매치 명령:
```bash
grep -noE '[A-Za-z0-9_./-]+\.(md|py|json|js|ts|yaml|yml|sh):[0-9]+' <12개 파일>
```
매치 4건, 전부 `opal/tools/state-tool/README.md` 내부(§verify --evidence-check 예시 JSON 블록):
```
opal/tools/state-tool/README.md:317: opal/tools/state-tool/state_tool.py:100
opal/tools/state-tool/README.md:321: opal/tools/state-tool/README.md:267
opal/tools/state-tool/README.md:323: opal/tools/state-tool/README.md:267
opal/tools/state-tool/README.md:445: opal/tools/xlsx-tool/run.sh:1
```
4건 전부 저장소 루트 기준 전체 경로(디렉토리 포함, 파일명 축약 없음). 파일명 없이 줄번호만 단독 표기된 인용(예: 단순 `:123`)이 md 문서 본문에 있는지 별도 확인:
```bash
grep -noE '(^|[^A-Za-z0-9_./-])[A-Za-z0-9_-]+\.(md|py|json|js|ts|yaml|yml|sh):[0-9]+' <12개 파일> | grep -v '/[A-Za-z0-9_-]*\.\(md\|py\|json\|js\|ts\|yaml\|yml\|sh\):[0-9]'
```
결과: 0건(경로 슬래시 없는 축약형 없음).

**참고(위반 아님, 스코프 외 관찰)**: `opal/tools/state-tool/tests/test_state_tool.py`의 Python 주석·docstring 내부에 `:4225`, `:2400`, `:4237-4238` 형태의 파일-내부 자기참조(같은 파일의 다른 줄을 가리키는 코드 코멘트 관용구)가 존재하나, `docs/CONVENTIONS.md` §Citation Rules는 "TASK.md/PLAN.md/ANALYSIS.md/QA 산출물" 작성 시의 인용 규칙이며 소스코드 주석에는 적용되지 않는다. 또한 동일 파일 내 자기참조는 "축약"이 아니라 관용적 자기지시 표기이므로 이 항목의 판정 대상이 아니다.

---

## 관측 스코프 종합 (재인용)

- 대상 파일 수: 15개 (지시서 지정)
- 실행 명령 전체 목록: `git status --short`, `git diff --stat -- <15개 파일>`, `git diff -- <파일>`(개별), `git log --oneline -5 -- opal/core/references/harness/analysis-core.md`, `grep -n "## 변경이력"/"100"` (파일별), `grep -noE` 정규식 스캔(플랫폼 분기·인용 형식 2종), `cat .opal/code-scan.json`(headerSource 확인)
- 계수 방식: 문자열 완전일치가 아닌 정규식 전종 매치(`grep -oE`)로 산정, 라인 단위 diff(`git diff` `+` 라인)만을 "신규 추가"로 간주해 플랫폼 분기 검사에 적용

---

## 완료 보고 요약

- Critical 0 / High 0 / Medium 1 / Low 0
- Critical·High 없음(전건 열거 대상 없음)
- 6개 확인 항목: (1) 변경이력 통과(1건 staleness는 Medium 이슈로 별도 계상) / (2) 배포경계 통과(0건) / (3) 플랫폼분기 통과(0건) / (4) State관리 통과(0건 복제) / (5) 수치복제금지 통과(기존 위반 4건 능동 제거) / (6) 인용형식 통과(0건 축약)
- 블로커: 없음
