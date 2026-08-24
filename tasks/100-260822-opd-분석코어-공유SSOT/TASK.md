# TASK: ANALYSIS 분석 코어 공유 SSOT 신설 — 지식 선조회·확정 승계·중복 제거

> 작성일: 2026-08-22 | 작업 유형: 개선 | 적용 스킬: opd | 모드: semi-agentic
> 개정: 2026-08-22 20:58 — 자체 검토 반영(목표 달성 AC 신설·AC 판정식 명문화·범위 2건 추가·E1 실행 명령 정정·개수 하드코딩 제거)
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

ANALYSIS·PLAN 두 단계가 공유하는 분석 절차 SSOT(`analysis-core.md`)를 신설하고, 지식 자산 선조회·확정 입력 승계·중복 제거를 통해 이미 확정된 사실의 재도출을 제거한다.

## 배경

분석 단계가 프로젝트 지식 자산(brain·code-scan·docs·과거 산출물)과 연결되지 않은 채 매번 백지에서 탐색하고, TASK 단계에서 이미 확정된 사실을 다시 확인하며, 같은 절차 규범이 ANALYSIS·PLAN 두 스킬에 복제되어 한쪽만 개정되는 상태다.

## 배경 분석 (대화에서 도출)

### (1) 프레임워크 측 결손

| # | 결손 | 근거 |
|---|------|------|
| 1 | 098이 `op-dev-analysis/SKILL.md`·`plan-guide.md`는 개정했으나 `analysis-guide.md`는 누락 — 내용 변경 이력이 051 이동 커밋 이후 0건 | E1 — `git log --oneline -- opal/skills/op-dev-analysis/references/analysis-guide.md` (스코프: 단일 파일, 결과 1행) |
| 2 | 워커 가이드가 Glob/Grep 직행을 지시해 PM 규범과 충돌 | `opal/skills/op-dev-analysis/references/analysis-guide.md:11-24` vs `opal/core/references/pm/dispatch-process.md:124` `:128` |
| 3 | 분석 체인 3개 파일에 `code-scan`·`brain-tool`·`tool-scan` 언급 0건 | E1 — `grep -rn "code-scan\|brain-tool\|tool-scan" opal/skills/op-dev-analysis/ \| wc -l` → `0` (스코프: 해당 스킬 디렉토리 3파일) |
| 4 | 품질 체크리스트 복제 — **체크리스트 섹션 2파일 기준 정확 일치 5건**(ANALYSIS §7 Q2 재측정). 4파일 교차·20자 이상 기준으로는 6건(체크리스트 5 + MUST 트리거 1)이며, 두 수치는 계수 기준이 다르다 | `opal/skills/op-dev-analysis/SKILL.md:166` / `opal/skills/op-dev-analysis/references/analysis-guide.md:146` |
| 5 | 기술 컨텍스트 가이드가 미등록 MCP 4종을 매핑 기준으로 제시 | `opal/skills/op-dev-analysis/references/tech-context-guide.md:92-107` vs `opal/core/references/mcps.md:14-65` |
| 6 | 098 신설 규약을 검증하는 축이 QA·게이트 양쪽에 부재 | `opal/skills/op-dev-qa/references/qa-dev-guide.md:67-77` / `opal/skills/opal-pilot-dev/references/pipeline.json:9` |

### (2) 현장 실측 — OPAL 적용 프로젝트 3곳

> 경로 비기재 — 소유자 지시(타 프로젝트 경로·출처 기재 금지)에 따라 프로젝트를 A/B/C로 익명 표기한다.
> 관측 스코프: 3개 프로젝트 `tasks/**/ANALYSIS.md` 전수 = 82건 / 총 20,113줄 (2026-08-22 20:40 KST 측정).

**재현 명령** (`$P` = 각 프로젝트 루트, 경로 비기재 정책에 따라 변수로 표기):

```bash
# 총 건수 / 총 줄수
find $P/tasks -name ANALYSIS.md | wc -l
find $P/tasks -name ANALYSIS.md -exec cat {} \; | wc -l
# 도구 언급률 (파일 단위 루프 — 디렉토리 대상 grep 직행 금지)
for f in $(find $P/tasks -name ANALYSIS.md); do grep -qi "code-scan" "$f" && echo "$f"; done | wc -l
# 코드펜스 내부 줄 비율 (전체 합산)
for f in $(find $P/tasks -name ANALYSIS.md); do awk 'BEGIN{inf=0;c=0;t=0}{t++; if($0~/^```/){inf=!inf;c++;next} if(inf)c++} END{print t","c}' "$f"; done | awk -F, '{t+=$1;c+=$2} END{printf "%d/%d = %.1f%%\n", c, t, c*100/t}'
# 템플릿 준수 (3대 섹션 AND)
for f in $(find $P/tasks -name ANALYSIS.md); do grep -q "^## 1\. 기존 코드 분석" "$f" && grep -q "^## 3\. 영향 범위" "$f" && grep -q "^## 6\. 기술 컨텍스트" "$f" && echo "$f"; done | wc -l
# brain ingest 커버리지
grep -rho "task:[0-9]\{3\}" $P/.opal/brain/pages | sort -u | wc -l
# 조회 비용
cd $P && time ~/.opal/tools/code-scan/run.sh summary
```

| # | 관측 | 수치 |
|---|------|------|
| 1 | 지식 자산 미사용 | `code-scan` 언급 5건(6%), `brain` 언급 14건(17%) |
| 2 | 자산은 이미 존재 | A 5,100파일/9도메인·brain 210p, B 623파일/48도메인·brain 150p, C 1,476파일/21도메인·brain 66p |
| 3 | 조회 비용은 무시 가능 | A 프로젝트 `code-scan summary` 4.6초, `brain-tool search` 0.69초 |
| 4 | 불변 정보 재도출 + 결과 불일치 | 동일 레포 §6.1 기술 스택이 태스크별로 "Kotlin 2.2.21 / Boot 3.3.7" → "Kotlin 2.x / Boot 3.3.x"로 흔들림 |
| 5 | 템플릿 준수 56% | 표준 3대 섹션(§1·§3·§6) 전부 보유 46/82 |
| 6 | 현장 발명 3종 | 「분석 질문 Q1~QN」 7건(3개 프로젝트, 260503~260820) / 「다음 단계 입력」 표 / 「프로세스 이슈」 표 |
| 7 | 원문 덤프 | 코드펜스 보유 62건(75%), 펜스 내부 2,964줄(전체의 14.7%), 극단 1건은 421줄 중 261줄(62%) |
| 8 | brain은 과거 산출물을 전량 대체하지 못함 | C 프로젝트 DONE.md 12건 중 brain이 인용한 태스크 7건(58%) |

## 확정된 설계 방향 (대화에서 합의)

- `[결정]` A — 분석 시작 시 지식 선조회 3단(brain → code-scan → docs 레지스트리 → 과거 태스크 산출물)을 수행하고, 조회 결과와의 델타만 분석한다.
- `[결정]` C — 품질 체크리스트·산출물 템플릿의 복제본을 제거하고 SSOT를 각 1곳으로 수렴한다.
- `[결정]` D — MCP 목록 복제를 제거하고 등록본(`mcps.md`) 조회 또는 `tool-scan which` 라우팅으로 대체한다. 미등록 MCP는 기재 금지.
- `[결정]` F — 기술 컨텍스트는 프로젝트 SSOT 1곳에 확정하고 ANALYSIS는 포인터 + 델타만 기재한다.
- `[결정]` G — 「분석 질문 Q표」를 표준 섹션으로 도입하되 강제가 아닌 권장으로 시작한다.
- `[결정]` H — 「다음 단계 입력」 핸드오프 표를 ANALYSIS.md 고정 섹션으로 승격한다.
- `[결정]` I — 소스코드 원문 덤프 금지를 워커 가이드에 배선하고 QA 축을 추가한다.
- `[결정]` E — ANALYSIS PM Gate 체크리스트를 채우고 QA에 098 규약 검증 축을 추가한다.
- `[결정]` J — 동일 개정을 `plan-guide.md`에 적용해 opds(Short) 경로를 커버한다.
- `[결정]` K — TASK 확정 항목의 재확인을 면제하고, 판정은 도구가 결정론적으로 수행한다.
- `[결정]` L — PLAN이 ANALYSIS 확정 사항을 승계하고 재도출을 금지한다.
- `[결정]` 배치 — 공유 SSOT는 `opal/core/references/harness/analysis-core.md`에 둔다. 대안(`opal/skills/_shared/`)은 신규 탐색 경로 규칙이 필요해 기각.
- `[결정]` 역할 분리 — 절차는 `analysis-core.md`, 산출물 형식은 각 스킬이 소유한다.
- `[결정]` B 흡수 — 증분 분석은 독립 축이 아니라 A의 하위 규칙으로 둔다.
- `[결정]` 목표 달성 측정 — EXECUTE 완료 후 **동일 TASK.md 입력으로 ANALYSIS를 1회 재생성**해, 구 규범으로 작성된 본 태스크의 ANALYSIS.md를 baseline으로 대조 측정한다. 신규 검증 도구는 만들지 않고 기존 도구 + 계수 명령으로 판정한다.
- `[결정]` 임계 기준 — 분량계 지표(코드펜스 비율 등)는 절대 임계값이 아니라 **baseline 대비 감소**로 판정한다.
- `[사실]` `verify --evidence-check`는 항목별 `verdict`·`confirmed_ratio`·`unconfirmed[]`를 반환하는 라우터이며 exit 0을 유지한다 (`opal/tools/state-tool/README.md:267-299`).
- `[사실]` 현재 evidence-check의 파싱 대상은 TASK.md `## 명확화 결과` 표의 `의존 사실` 열뿐이며 `## 확정된 설계 방향` 섹션은 대상 밖이다 (`opal/tools/state-tool/README.md:270-272`).
- `[사실]` 현재 ANALYSIS는 `[결정]`만 재도출을 면제하고 `[사실]`은 E1~E4 재확인 대상이다 (`opal/skills/op-dev-analysis/SKILL.md:30`).
- `[사실]` PLAN의 ANALYSIS 재사용 지시는 `2.N.2 현재 구현`에만 있고 `2.N.1`·`2.N.3`에는 없으며, 강도도 "간략 작성"으로 `[MUST]`가 아니다 (`opal/skills/op-dev-plan/references/plan-guide.md:88` `:104` `:115`).
- `[사실]` brain은 선별·stale 가능한 파생 스냅샷이므로 과거 산출물 직접 조회를 대체하지 못한다 (`opal/core/references/opal-pm.md:243-244`).
- `[사실]` E5(brain·code-map) 단독 인용은 금지되어 E1~E4 동반이 필요하다 (`opal/core/references/harness/citation-rules.md:451`).

## 명확화 결과

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | ANALYSIS·PLAN 공유 분석 절차 SSOT를 신설하고, 지식 선조회·확정 승계·중복 제거로 재도출을 제거한다 | - | - |
| 범위 | 포함(15파일): ① `harness/analysis-core.md`(신규) ② `opal-harness.md` 모듈 표 ③ `op-dev-analysis/SKILL.md` ④ `analysis-guide.md` ⑤ `tech-context-guide.md` ⑥ `plan-guide.md` ⑦ `qa-dev-guide.md` ⑧ `op-dev-qa/SKILL.md`(R/P 번호 거울 사본 — ANALYSIS Q6에서 정합 필수로 편입) ⑨ `opal-pilot-dev/SKILL.md` ⑩ `opal-pilot-dev/references/pipeline.json` ⑪ `state_tool.py` ⑫ `tests/test_state_tool.py` ⑬ `opal/tools/state-tool/README.md`(PD-1 반환 계약 변경에 따른 계약 문서 정합 — PLAN Step 11 편입, 2026-08-23 소유자 승인) ⑭ `docs/ARCHITECTURE.md` ⑮ `docs/PROJECT.md`(docs 갱신 규칙에 따른 자동 추가 — PLAN Step 12, 동일 승인) / 제외(명시적 결정): brain ingest 커버리지 개선, 프로세스 이슈 섹션 표준화, install 재배포, **`op-task-plan/references/plan-guide.md`(opp·oppd 경로 — 별도 파일이며 이번 개정 미적용, ANALYSIS H-3)** | - | `opal/core/references/harness/citation-rules.md:451` |
| 제약 | 배포본(`~/.opal/`) 직접 편집 금지 · 규범 복제 금지(포인터 사용) · 기존 산출물 비소급 · evidence-check exit 0 계약 유지 | - | `opal/tools/state-tool/README.md:267-272` |
| 완료기준 | R-1~R-12 AC 전건 Pass + 목표 달성 AC-G1~G4 충족 + 회귀 스위트 감소 0건(**관측 스코프·실행 명령 병기 필수** — 단일 파일 실행과 디렉토리 실행을 구분해 기재) | - | `opal/skills/op-dev-analysis/SKILL.md:166` / `opal/skills/op-dev-analysis/references/analysis-guide.md:146` |

## 요구사항

- [ ] **R-1 (A) 분석 코어 SSOT 신설** — 무엇을: 지식 선조회 3단·증분 소비·델타 탐색 규율·분석 깊이 기준·관련 파일 맵 6영역 축·의존성/영향 범위 도출·품질 체크리스트를 단독 소유하는 문서 신설 / 어디에: `opal/core/references/harness/analysis-core.md`(신규) + `opal-harness.md` §2 하네스 모듈 표 1행 / 왜: 확정 방향 A·역할 분리 / **AC**: (a) 파일이 지정 경로에 존재하고 **위 「무엇을」이 열거한 소유 범위 각각에 대응하는 섹션 헤딩**이 모두 존재한다(개수는 「무엇을」 필드가 소유하며 AC에 복제하지 않는다) (b) 하네스 모듈 표에 로드 시점·탐색 경로가 기재된 행이 1개 추가된다.
- [ ] **R-2 (C) 중복 제거** — 무엇을: 체크리스트·§6 템플릿 복제본 제거 후 포인터로 대체 / 어디에: `op-dev-analysis/SKILL.md`, `analysis-guide.md`, `tech-context-guide.md` / 왜: 배경 분석 (1)-4 / **AC**: (a) **판정식** — 대상 3파일에서 체크리스트 항목 문장을 정규화(선행 `- [ ] ` 제거·공백 압축)한 뒤 중복 계수했을 때 2회 이상 출현 문장이 0건이다(스코프: `opal/skills/op-dev-analysis/**`, 정확 문자열이 아닌 정규화 후 비교) (b) 3파일 각각이 `analysis-core.md` 포인터를 1개 이상 보유한다.
- [ ] **R-3 (D) MCP 목록 복제 제거** — 무엇을: 하드코딩 MCP 목록 삭제 후 등록본 조회 규칙으로 교체 / 어디에: `tech-context-guide.md:92-107` / 왜: 배경 분석 (1)-5 / **AC**: (a) 대상 파일에서 `supabase|github|figma|sentry` 정규식 매치 0건 (b) "등록본 조회 후 필요한 것만 기재, 미등록 기재 금지" 취지의 규칙 문장이 존재한다.
- [ ] **R-4 (F) 기술 컨텍스트 SSOT 승격** — 무엇을: 태스크별 재도출 폐지, 프로젝트 SSOT 포인터 + 델타 기재로 전환 / 어디에: `analysis-core.md` + ANALYSIS.md §6 템플릿 / 왜: 배경 분석 (2)-4 / **AC**: §6 템플릿이 "프로젝트 SSOT 경로 + 이번 태스크 델타" 2필드 구조로 바뀌고, 전체 스택 재기재를 금지하는 문장이 존재한다.
- [ ] **R-5 (G) 분석 질문 Q표** — 무엇을: PM이 디스패치 시 Q1~QN을 명시하고 워커가 그 질문에 답하는 섹션을 권장 표준으로 도입 / 어디에: ANALYSIS.md 템플릿 + `opal-pilot-dev/SKILL.md` STEP 2 디스패치 프롬프트 / 왜: 배경 분석 (2)-6 / **AC**: 템플릿에 Q표 섹션이 존재하고 "권장(강제 아님)" 표기가 있으며, 디스패치 프롬프트에 질문 주입 슬롯이 1개 추가된다.
- [ ] **R-6 (H) 핸드오프 표 신설** — 무엇을: 「다음 단계 입력 — PLAN이 재조사 없이 쓸 수 있는 확정값」 표를 ANALYSIS.md 고정 섹션으로 추가 / 어디에: `op-dev-analysis/SKILL.md` 통일 형식 / 왜: 배경 분석 (2)-6 / **AC**: 템플릿에 해당 섹션이 존재하고 `항목 | 확정값 | 근거` 3열 표 골격을 갖는다.
- [ ] **R-7 (I) 원문 덤프 차단** — 무엇을: `citation-rules.md:97` 금지 조항을 워커 가이드에 배선 + QA 검증 축 추가 / 어디에: `analysis-core.md`, `qa-dev-guide.md` / 왜: 배경 분석 (2)-7 / **AC**: (a) 가이드에 원문 블록 금지 문장이 존재한다(원문 복제가 아닌 `citation-rules.md §2.2` 포인터 형태) (b) QA 표에 코드펜스 관련 검증 행이 1개 추가된다.
- [ ] **R-8 (E) 검증 축·게이트 보강** — 무엇을: QA ANALYSIS 기준에 098 규약 검증 축 추가 + `analysis.pm_gate` 체크리스트 채움 / 어디에: `qa-dev-guide.md:67-77`, `pipeline.json:9-10` / 왜: 배경 분석 (1)-6 / **AC**: (a) QA 표에 확정 입력 판정·근거 등급 검증 행이 추가된다 (b) `analysis.pm_gate`의 `checklist`가 `["-"]`가 아닌 실제 항목 배열이 되고 JSON 파싱이 성공한다.
- [ ] **R-9 (J) Short 트랙 동반 적용** — 무엇을: `plan-guide.md`가 `analysis-core.md`를 Read하도록 배선하고 자체 절차 서술을 포인터로 교체 / 어디에: `plan-guide.md:25-39` `:88-123` / 왜: 확정 방향 J / **AC**: (a) plan-guide에 `analysis-core.md` Read 지시가 존재한다 (b) **판정식 교체(ANALYSIS §7 Q2 근거)** — 텍스트 정확 일치는 개정 전에도 0건이므로 판정 대상이 아니다. 대신 `plan-guide.md`의 절차 서술 문단이 포인터로 **대체**되었는지로 판정한다: `plan-guide.md` 2단계(현행 `:88-123`)의 자체 절차 서술 문단 수가 감소하고, 감소분마다 `analysis-core.md` 포인터가 대응한다(문단 수 before/after 실측 병기).
- [ ] **R-10 (K) 확정 사실 승계** — 무엇을: `verify --evidence-check` 파싱 범위를 `## 확정된 설계 방향`까지 확장하고, 4축 통과 `[사실]`에 대한 확인 면제 조건과 판정값 `승계`를 신설 / 어디에: `state_tool.py` + `tests/test_state_tool.py`, `op-dev-analysis/SKILL.md` 확정 입력 소비 규약 / 왜: 확정 방향 K / **AC**: (a) `## 확정된 설계 방향` 항목이 `items[]`에 포함되어 반환된다 (b) exit 0 계약이 유지된다 (c) 판정표 템플릿에 `승계` 값이 추가된다 (d) 신규 테스트가 통과하고 기존 통과 수 감소가 0건이다(**스코프·명령 병기**: 단일 파일 `pytest opal/tools/state-tool/tests/test_state_tool.py` / 디렉토리 `pytest opal/tools/state-tool/` 각각 기재).
- [ ] **R-11 (L) PLAN 승계 [MUST]화** — 무엇을: 핸드오프 표를 PLAN 2단계 진입 입력으로 규정하고 승계 항목 재도출을 `[MUST]` 금지로 명시 / 어디에: `plan-guide.md:88` `:100` `:115`, `qa-dev-guide.md` P축 / 왜: 배경 분석 (1)-2·확정 방향 L / **AC**: (a) 2.N.1·2.N.3에 승계 지시가 존재한다 (b) `[MUST] 재도출 금지` 문장이 존재한다 (c) QA P축에 승계 준수 검증 행이 1개 추가된다.
- [ ] **R-12 목표 달성 실측** — 무엇을: EXECUTE 완료 후 동일 TASK.md 입력으로 ANALYSIS를 1회 재생성해 baseline(본 태스크 ANALYSIS.md)과 대조 측정 / 어디에: TEST 단계 산출물(대조표) / 왜: 수단 AC만으로는 "문서는 고쳤는데 행동은 그대로"를 검출하지 못함 / **AC**: 아래 AC-G1~G4를 충족한다. **선행조건 배선(ANALYSIS §7 Q9 근거)** — ① baseline은 ANALYSIS PM Gate 통과 시점의 `ANALYSIS.baseline.md` 사본으로 고정한다 ② AC-G1은 `승계` verdict가 R-10 GREEN 이후에만 존재하므로 EXECUTE 체크리스트에 'R-10 GREEN 완료 후 측정' 선행조건으로 배선한다 ③ AC-G4는 baseline PLAN.md가 없어 이번 회차 **측정 불가**이며, DONE.md에 '측정 불가(선행조건 미충족)'로 명시하는 것으로 갈음한다 ④ baseline은 PM 수동 주입으로 만들어져 천장 효과가 있으므로, 대조의 성격은 '개선 증명'이 아니라 '규범만으로 동등 수준이 재현되는가'임을 DONE.md에 명시한다.

### 목표 달성 AC (AC-G)

| # | AC | 판정 방법 |
|---|-----|----------|
| AC-G1 | 재생성 ANALYSIS.md에 TASK.md 확정 항목의 재확인 서술이 0건이고, 확정 입력 판정표에 `승계` 행으로 나타난다 | 판정표 행 검사 + `verify --evidence-check` 반환값 대조 |
| AC-G2 | 재생성 ANALYSIS.md에 `code-scan`·`brain` 조회 결과 인용이 1건 이상 존재한다 | §0 참조 문서 표 검사 |
| AC-G3 | 코드펜스 내부 줄 비율이 **baseline 대비 감소**한다 | 두 산출물에 동일 awk 계수 적용, 비율 비교 |
| AC-G4 | PLAN.md가 핸드오프 표 항목을 재도출 없이 인용하고, ANALYSIS와 정규화 후 20자 이상 일치 문단이 baseline 대비 감소한다 | 두 산출물 대조 계수 |

> 표본 한계: 재생성 1회이므로 통계가 아니라 존재 증명이다. 이 한계를 DONE.md에 명시한다.

## 제약 조건

- 배포본(`~/.opal/`) 직접 편집 금지 — 프로젝트 소스만 수정하고 재배포는 소유자가 수행한다.
- 규범 복제 금지 — 기존 SSOT(`citation-rules.md`·`mcps.md` 등)의 문장을 옮겨 적지 않고 포인터로 참조한다.
- 개수·임계값 복제 금지 — 목록 개수는 목록 소유 문서에만 두고 AC·설명문에 복제하지 않는다.
- 기존 산출물 비소급 — 이미 작성된 ANALYSIS.md/PLAN.md는 소급 개정하지 않는다 (`citation-rules.md` §5).
- `verify --evidence-check`의 exit 0 라우터 계약과 `--clarification-check` 상호 배타 계약을 유지한다.
- 타 프로젝트 경로·출처를 산출물에 기재하지 않는다 — 익명 표기 + 비기재 사유 명시.
- 모든 실측 수치는 관측 스코프와 실행 명령을 병기한다 (`citation-rules.md` §9 E1).

## 기술 스택

- 문서: Markdown (OPAL 프레임워크 규범 문서)
- 코드: Python 3 (`opal/tools/state-tool/state_tool.py`), 테스트 `pytest`
- 도구: state-tool, code-scan, brain-tool, memory-tool

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | 인용 규칙·근거 등급 | `opal/core/references/harness/citation-rules.md` | 원문 블록 금지(§2.2)·근거 등급(§9)·비소급(§5) 기준 |
| D-2 | 설계 | 분석 스킬 | `opal/skills/op-dev-analysis/SKILL.md` | ANALYSIS.md 형식·확정 입력 소비 규약 개정 대상 |
| D-3 | 설계 | 분석 가이드 | `opal/skills/op-dev-analysis/references/analysis-guide.md` | 절차 이관 원본 |
| D-4 | 설계 | 기술 컨텍스트 가이드 | `opal/skills/op-dev-analysis/references/tech-context-guide.md` | MCP 목록 복제 제거 대상 |
| D-5 | 설계 | PLAN 가이드 | `opal/skills/op-dev-plan/references/plan-guide.md` | 승계 규약·중복 절차 포인터화 대상 |
| D-6 | 설계 | Dev QA 가이드 | `opal/skills/op-dev-qa/references/qa-dev-guide.md` | 검증 축 추가 대상 |
| D-7 | 소스 | state-tool README | `opal/tools/state-tool/README.md` | evidence-check 라우터 계약 |
| D-8 | 설계 | PM 디스패치 프로세스 | `opal/core/references/pm/dispatch-process.md` | code-scan·brain 선조회 PM 규범 |
| D-9 | 설계 | 하네스 | `opal/core/references/opal-harness.md` | 모듈 표 등록 대상 |
| D-10 | 설계 | opd 오케스트레이터 | `opal/skills/opal-pilot-dev/SKILL.md` | STEP 2 디스패치 프롬프트 질문 슬롯 추가 대상 |
