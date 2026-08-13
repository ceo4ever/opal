# SCENARIO GATE 1 — 목표-커버 루브릭 판정 (판단축 ①⑤⑥)

> 실행 일시: 2026-08-13T16:11:00+09:00 | phase: `scenario-rubric` | iteration: 1
> scenario_source: `tasks/090-260813-opds-파이프라인-스펙-마이그레이션/TEST-SCENARIO.md`
> normalized_payload: `tasks/090-260813-opds-파이프라인-스펙-마이그레이션/.scenario-coverage-input.json`
> 판정 주체: opal-evaluator-agent (verdict-only · readonly)
> 규칙 SSOT: `opal/core/references/harness/scenario-gate.md` §2(6축 · 판정주체 분리) · §5-1(종료조건 임계)

> **판정 범위**: 판단축 ①⑤⑥만 채점한다. ②③④(요구·기능·리스크 매핑 커버)는 test-tool `scenario-coverage-check`가 결정론으로 이미 판정했으며(exit 0 / `all_covered: true`) 본 보고서는 그 축을 재판정하지 않는다 (scenario-gate.md §2 [MUST]).

---

## 1. 판단축별 판정

| 축 | 정의 | 점수 | 통과선 | 판정 |
|----|------|------|--------|------|
| ① 목표 달성 | 사용자/운영 계층에서 태스크 목표를 검증하는 시나리오 존재 | **2** | ≥1 | PASS |
| ⑤ 채택/잔존 | 교체형 목표 = 구형 잔존0 · 신형 채택 검증 시나리오 존재 | **1** | ≥1 | PASS (gap 1건) |
| ⑥ 경계/부정 | 경계값·부정 경로 시나리오 존재 | **2** | ≥1 | PASS |

**scores**: `{"goal": 2, "adoption": 1, "boundary": 2}` · **average**: `1.67`

---

### ① 목표 달성 — 2점

**근거**

- **사용자 계층이 실재한다.** S-17(§3 L3, `[SUPERVISOR]`)은 install 재배포된 **배포본** `~/.opal/skills/*/references/pipeline.json`을 대상으로 캡틴이 **새 세션**에서 실제 pilot을 호출해 ① 태스크 폴더·STATE.md 생성 ② deprecation 경고 미출력 ③ 행 수(oppl 19 / oppd 13) 일치를 확인한다. 목표의 최종 관측점("pilot을 실제로 쓸 수 있는가")을 산출물 정적 검사가 아니라 **실사용**으로 잡는다.
- **자동화 불가 사유가 타당하다.** S-17 실행 방식 칸의 "새 세션이 필요해 자동화 불가. M2 대체 불가"는 성립한다 — 새 에이전트 세션에서 스킬 트리거로 pilot을 기동하는 경로는 CLI 호출로 재현되지 않는다. 또한 S-13은 레포 경로, S-17은 배포본 경로로 대상이 달라 **배포 반영까지가 검증 범위**에 들어온다. 회피성 수동 전가가 아니다.
- **L1/L2가 정적 검사에 치우치지 않았다.** 운영 계층 실행형이 별도로 3건 있다 — S-13(10 pilot × 실 `init`, 모드 조합 포함 20회, exit 0 · `ok:true` · `schema_version:"1.1"` · **deprecation 경고 0회** · `rows_count` 기대치 일치), S-14(oppl·oppd 하드 실패 **전/후** 대조 — 전 `skill_md_parse_error` 기록, 후 `rows_count` 19/13 성공), S-16(런타임 stage-transition 실증).
- **070 재발 아님.** §4 매핑 표에 `목표 (9→10/10 전환, 실사용 가능) | H-1, H-5 | L2 + L3 | S-13, **S-17** | [T090/L3-GOAL] | **목표달성 시나리오**` 행이 요구(R-N) 행과 **별도로** 존재한다. 070은 이 행 자체가 도출되지 않은 사건이었다(scenario-gate.md §1 각주). 정규화 페이로드에서도 `is_goal_scenario: true`가 S-17에 부여되어 있다.
- **부수 목표(하드 실패 해소)도 목표 계층에서 잡힌다.** S-14가 전/후 증거를 모두 요구하므로 "원래 됐던 것 아니냐"는 반박이 차단된다.

**관찰(감점 아님)**

- S-17의 실사용 대상이 "최소 2종(권장 oppl·oppd)"으로 한정되나, 나머지 8종은 S-13이 10/10 자동 커버하므로 공백이 아니다.
- 목표 문장 중 "registry `pipeline` 드리프트 정합"은 S-9(L1 정적)만 커버한다. 다만 registry `pipeline` 필드는 소비 코드가 없는 표기 필드이므로(TASK.md 배경 분석 (3) · R-4) 운영 계층 관측점이 존재하지 않는다 — 검증 불가 대상이라 감점 사유로 삼지 않는다.

---

### ⑤ 채택/잔존 — 1점 (gap 1건)

교체형 목표(구형 `.md` 파싱 → 신형 `.json` 파싱)이므로 **잔존 0**과 **채택** 양쪽을 본다.

**충족된 부분**

- **채택은 3중으로 검증된다.** ① 문서 채택 — S-10 후반("`rows-from.*references/pipeline.json` 매칭이 10개 파일에 각 1건 이상") ② 런타임 채택 — S-13(10 pilot 실 `init` 성공 + deprecation 경고 0회) ③ 실사용 채택 — S-17. 채택축은 2점 수준이다.
- **잔존 검증이 존재한다.** S-10 전반이 대상 6종 SKILL.md에서 `## 변경이력` **이전 구간**의 `rows-from.*SKILL.md` 매칭 0건을 요구한다(D-9). `awk` 구간 분리로 과거 이력 개변을 유발하지 않는 설계도 타당하다. S-13의 "deprecation 경고 0회"는 런타임 잔존 신호를 겸한다.

**감점 사유 — 잔존 grep 범위가 pilot SKILL.md 10개로 한정되어, 레포 내 살아있는 구형 지시를 놓친다 (실측 확인)**

S-10 "대상" 칸이 `10 pilot SKILL.md`다. 그러나 레포에는 pilot SKILL.md **밖에서** deprecated `.md` 경로를 지시하는 살아있는 문서가 실재한다:

- `opal/core/references/tools.md:152` — `--rows-from ~/.opal/skills/opal-pilot-project/SKILL.md`. **이미 전환 완료된 opp**를 `.md` 경로로 호출하는 실행 예시다. 코어 레퍼런스 문서의 예시이므로 에이전트가 그대로 복사하면 실제 `build_rows_from_skill_md` 호출이 발생한다.
- `opal/core/references/tools.md:84` — CLI 시놉시스가 `[--rows-from <path-to-skill.md>]`로 `.md` 형태만 표기한다.
- `opal/core/references/harness/task-process.md:49` · `opal/skills/op-task/SKILL.md:223` — "행 구성(`--rows-spec`/`--rows-from`)은 오케스트레이터 SKILL.md 'STATE.md 도메인 치환값' 참조". 행 구성 원천을 **SKILL.md 표**로 가리키는 포인터로, 이번 이관 후 SSOT(`pipeline.json`)와 어긋난다.

즉 S-10이 PASS해도 태스크 목표 문장의 "deprecated `build_rows_from_skill_md` 경로의 **호출자가 0건**"은 증명되지 않는다 — 증명되는 명제는 "6 pilot SKILL.md 안에서 0건"까지다. TASK.md 완료기준 (8)이 "지시하는 **pilot** 0건"으로 좁게 적힌 것이 이 구멍의 원인이며, 시나리오는 그 좁은 문장을 그대로 따라갔다.

> 판별 기준: `opal/tools/state-tool/README.md`와 `.opal/brain/pages/entity/state-tool.md`의 `.md` 언급은 **도구 자신의 분기 동작 설명**이므로 잔존이 아니다. 위 4개 지점은 **사용을 지시·예시**하므로 성격이 다르다.

**gap (Producer 재작성 지시)**

> S-10의 잔존 grep 대상을 `10 pilot SKILL.md` → **레포 전역**(제외: `tasks/**`, `## 변경이력` 이후 구간, `opal/tools/state-tool/**` 도구 자체 문서, `.opal/brain/**` 서술 문서)으로 확장하고, 기대 결과에 `opal/core/references/tools.md:84,152` · `opal/core/references/harness/task-process.md:49` · `opal/skills/op-task/SKILL.md:223` 4개 지점의 처리 결과를 **명시적으로** 포함하라. 이 4곳을 이번 태스크 범위 밖으로 둔다면(R-2는 6 pilot SKILL.md만 규정), S-10 기대 결과에 "범위 밖 알려진 잔존 4건 — 후속 태스크 이월"을 명시하고 TASK.md 목표 문장의 "호출자 0건"을 "**pilot** 호출자 0건"으로 좁혀 표현을 일치시켜라. 둘 중 어느 쪽이든 **잔존 주장과 검증 범위가 일치**해야 한다.

---

### ⑥ 경계/부정 — 2점

**부정 경로 근거 (5건, 실질적)**

| 시나리오 | 부정 경로 성격 | 검증 방식이 실질적인 근거 |
|---------|--------------|----------------------|
| S-3 | 범위 밖 변경 차단 (H-3) | 계수(`EXECUTE-LOOP` 17회 전후 동일) + 외부 6파일 SHA-256 + `execute-loop-guide.md` diff 0 — **"안 했다"를 해시로 증명**하는 구조라 통과 조건이 느슨하지 않다 |
| S-11 | 배포 경계 위반 (H-15) | `git status --porcelain` 변경 파일이 전부 `opal/`·`docs/`·`tasks/` 하위, `~/.opal/` 0건 |
| S-12 | 범위 밖 개명 유혹 (H-16) | oppl `SKILL.md:121`·`:137` 두 줄이 `git diff`에 **미등장** — 줄 단위 지정이라 회피 불가 |
| S-15 | 레포 오염 (H-14) | 검증 시작 스냅샷 ↔ `rm -rf $WORK` 후 스냅샷 동일 + `tasks/080~089` state.json 무변경(제약 (d)) |
| S-16 | `--wbs` 미완 행 (H-17) | id 10~12 `mark --na` 후 id 13 CLOSE 진입 — D-7b 표준화 판단 ③의 런타임 성립 여부 |

**경계값 근거**

- S-5 — 백틱 · 전각 대시(`—`) · 체크마크(`✓`) · 플레이스홀더(`{NN}`) · 소수점 ID(`D1.5`)의 **문자 단위** 보존. 이관 작업에서 가장 깨지기 쉬운 지점을 정확히 겨눈다.
- S-4 — `spec_id_sequence_invalid` · `spec_key_duplicate` · `spec_key_format_invalid` · `spec_stage_invalid` · `spec_key_stage_mismatch` 전건 0. opdd `ddl_migration.*` slug라는 까다로운 케이스를 명시.
- S-8 — **부재 조건**을 명시적으로 요구한다(opwt `meta.stages`에 `ANALYSIS` 부재, opsdd에 `EXECUTE-LOOP` 부재). 긍정 일치만 보는 검사와 다르다.
- S-1 — 특수문자 4종(`{ts}` · `[-{element}]` · `작업 (Batch 동적 삽입)` · `구조 검증 (S-1~S-6)`) 보존.

**관찰(감점 아님 — 개선 권고)**

- **negative control 부재.** S-4는 "10건 전부 `ok:true`"만 본다. 경로 오타 등으로 검사 대상이 0건이어도 통과할 수 있다. 고의 위반 스펙 1건으로 `spec-validate`가 실제 FAIL을 내는지 확인하면 검사 자체의 생존을 담보할 수 있다.
- **S-16이 단방향이다.** "`--na` 후 CLOSE 진입 허용"만 확인하므로, stage-transition guard가 아예 무력화돼도 PASS한다. 반대 케이스(id 10~12를 `--na` 없이 미완으로 둔 채 CLOSE 진입 시 `stage_transition_violation`으로 **차단**됨)를 함께 넣으면 표준화 판단 ③의 실증이 완결된다.
- 두 항목 모두 부정 경로의 **부재**가 아니라 기존 부정 경로의 강화 여지이므로 통과선(≥1) 및 2점 앵커("경계·부정 경로 시나리오 존재")에는 영향이 없다.

---

## 2. 종합 verdict

```json
{"scores": {"goal": 2, "adoption": 1, "boundary": 2}, "average": 1.67, "verdict": "pass"}
```

**verdict: `pass`**

판정 근거 — scenario-gate.md §5-1 임계 2조건을 모두 충족한다.

1. **0점 축 없음** — ①2 · ⑤1 · ⑥2 전부 ≥1.
2. **평균 ≥1.5** — (2+1+2)/3 = **1.67**.

결정론 파트(②③④)는 test-tool `scenario-coverage-check` exit 0 · `all_covered: true`로 이미 충족되었으므로, §6 tool-gated 집행의 두 증거가 모두 성립한다.

**gaps**

| # | 축 | gap |
|---|----|-----|
| 1 | ⑤ 채택/잔존 | S-10 잔존 grep 범위가 pilot SKILL.md 10개로 한정되어, `opal/core/references/tools.md:84,152` · `opal/core/references/harness/task-process.md:49` · `opal/skills/op-task/SKILL.md:223`의 살아있는 구형 지시(특히 tools.md:152는 이미 전환된 opp를 `.md` 경로로 호출하는 실행 예시)를 검출하지 못한다. 범위를 레포 전역으로 확장하거나, 범위 밖으로 둘 경우 "알려진 잔존 4건 — 후속 이월"을 S-10 기대 결과에 명시하고 목표 문장의 "호출자 0건"을 "pilot 호출자 0건"으로 좁혀 표현을 일치시켜라. |

> `verdict: pass`이므로 루프는 수렴이며 재작성은 필수가 아니다. 다만 위 gap은 **목표 문장과 검증 범위의 불일치**이므로, EXECUTE 진입 전 S-10 기대 결과 1줄 보강 또는 TASK.md 목표 표현 정정 중 하나를 반영할 것을 권고한다. 반영 여부 판단과 실행은 PM(오케스트레이터) 책임이며, 본 에이전트는 판정과 제안만 반환한다.

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-08-13 | iteration 1 판정 — ①2·⑤1·⑥2, average 1.67, verdict pass, gap 1건 (잔존 검증 범위) |
