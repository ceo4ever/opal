# SCENARIO GATE 1 — 목표-커버 루브릭 판단축 채점 (①⑤⑥)

> 실행 일시: 2026-08-04T11:50:30+0900 | phase: `scenario-rubric` | iteration: 1
> 채점자: opal-evaluator-agent (verdict-only · readonly)
> scenario_source: `tasks/083-260803-opds-샤드정책-확장/TEST-SCENARIO.md` (S-1~S-16, TS-ID 122 묶음)
> 기준 SSOT: `opal/core/references/harness/scenario-gate.md` §2(루브릭 6축)·§5-1(종료조건)
> 참조 입력: `TASK.md`(완료기준 ④), `PLAN.md`(F-001~F-012 / H-1~H-22 / §3 TS 정의), `.scenario-coverage-input.json`

## 0. 채점 범위

| 축 | 판정 주체 | 본 보고서 |
|----|----------|----------|
| ① 목표 달성 | opal-evaluator-agent | **채점 대상** |
| ② 요구 커버 / ③ 기능 커버 / ④ 리스크 커버 | test-tool(결정론) | 채점 제외 — `scenario-coverage-check` exit 0 / `all_covered: true` (requirements 11 · features 12 · hypotheses 22 · scenarios 16) |
| ⑤ 채택/잔존 | opal-evaluator-agent | **채점 대상** |
| ⑥ 경계/부정 | opal-evaluator-agent | **채점 대상** |

> 매핑 전량 커버(②③④)를 ①⑤⑥의 근거로 사용하지 않았다. 각 축은 시나리오 본문·PLAN TS 정의를 직접 읽어 독립 판정했다(070 사건 근거 — `scenario-gate.md` §1).

## 1. 판단축별 판정

| 축 | 점수 | 판정 근거 (인용) | gap |
|----|------|-----------------|-----|
| ① 목표 달성 | **2** | 목표("탐지에서 실제 분할까지 이어지는 경로를 도구 안에 완성")를 **전용 단일 시나리오 S-16**이 운영 계층(L2, 실 파일 read→write→re-read)에서 직접 검증한다 — "`--plan --out` → `--groups --dry-run` → `--groups` → `validate` 순으로 처리해 **`manifest_oversize`가 0건이 되고 엔트리 유실이 0건**임이 한 시나리오로 입증"(TEST-SCENARIO §3 S-16). PLAN `TS-054`가 같은 문언으로 고정돼 있고, 매핑 표 마지막 행이 "완료기준 ④ 왕복 입증 / S-16 / `[T083/L2-DONE4]` / **단일 시나리오**"로 귀속을 명시한다. 목표의 나머지 절반(2축 탐지 정확도)은 S-3(TS-020~025)이 4경계로 검증한다. **070식 결함(목표 검증 시나리오 자체의 부재) 없음** | — |
| ⑤ 채택/잔존 | **2** | **(a) 구 위치 `index.json manifestMaxBytes` 폐기 → 신 위치 `.opal/code-scan.json shardPolicy`**: 잔존0 = S-1 정적 검사 "`manifestMaxBytes(` 함수 정의 0개" + "`DEFAULT_SHARD_POLICY`가 상수 선언·`resolveShardPolicy` 본문 밖에 0회"(PLAN `TS-007`), 픽스처 측 잔존0 = §2.1 "082 승계 … **구 위치 키 제거** + `shardPolicy` 기재"(5+3 트리), 런타임 잔존0 = S-13 "구 위치 값 **무영향** + stderr 1줄 + `invalid_index`로 승격하지 않음". 채택 = S-1 3단 결정표 7행 전행 일치 · S-13 "구·신 동시 존재 시 **신 위치 승**" · S-15 install 시드로 신 위치 정책 키 생성 + 기존값 무손실. **(b) 단일 축 분류 → 단계 사다리 분류**: 채택 = S-5 "`trace[n].input === trace[n-1].remaining` · 앞 단계 배정 불변 · 미달 버킷이 즉시 `unassigned`로 확정되지 않음 · 5단계 각 1그룹 이상"(TS-100·101·107), 단일 축 초안의 실패 모드 차단 = S-4 "`unassigned` 존재 + **"기타" 라벨 0개**"(TS-035 — 불채택 사유였던 "잔여 임의 배분"의 역단언), 단일 축이 쓰지 않던 의미 SSOT 채택 = S-7 사전 2표 파싱(`영문`·`약어` 정확 추출). (b)의 구형은 PLAN §1.6에서 **불채택된 설계 초안**이고 배포된 적이 없어 코드 잔존 대상 자체가 없다 — 잔존축 N/A 처리 타당 | — |
| ⑥ 경계/부정 | **2** | **경계값 양방향**이 PLAN TS로 고정돼 있고 S-3 묶음(TS-020~TS-025)에 실려 있다 — 엔트리 `>=`: "`entries === minFiles`는 **대상**(하한은 이상), `entries === minFiles - 1`은 비대상"(TS-023) / 바이트 `>`: "`size === maxBytes`는 비대상, `size === maxBytes + 1`은 대상 (082 off-by-one 계약 보존)"(TS-024) / AND 조건 양쪽 실패(TS-020·TS-022). **부정 경로**: 설정 파손·부재·키부재·타입위반 4상태 비차단(S-2) · 설정 부재/파손 트리 `init`(S-8, P0 H-22) · 사전 파손·부재·경로 이탈·크기 상한 초과(S-7) · 4단계 쓰기 실패 주입 + 롤백(S-11, TS-046~049) · 라벨 경로 이탈 `../evil`·`_shards`·대문자(S-10, TS-053) · **inline 모드 `split` exit 1 + 사유 표면화**(S-10, H-14 조용한 성공 금지) · 사다리 밖 stage 값 exit 1(S-6, TS-111) · `--header-source` 누락 시 exit 1 + 파일 미생성(S-8) · `config_exists` 거부 + 원본 불변(S-9) | — |

**scores**: `{ goal: 2, adoption: 2, boundary: 2 }` · **average**: `2.0`

## 2. 구조적 특징에 대한 판단

- **기능축 묶음(TS 122 → S 16) 자체는 감점 사유 아님** — 각 S가 `TS 묶음` 열로 TS-ID 구간을 명시하고 PLAN §3의 해당 TS 표가 조건·기대결과를 문언으로 고정한다. 추적이 끊기는 지점을 찾지 못했다.
- **묶음으로 인한 목표 귀속 유실 없음** — 가장 위험한 후보였던 완료기준 ④가 다른 S에 흡수되지 않고 **S-16 단독 그룹**으로 분리돼 있다(TS-054 전용 귀속). 사다리·사전·`init`도 각각 S-5·S-7·S-8/S-9로 독립 귀속된다.
- **L3(사용자 협업) 0건 사유는 타당** — 산출물이 비대화형 CLI이고, "프롬프트 0건 · TTY 없이 동작"(S-8) 자체가 자동 시나리오로 검증된다. 사람이 개입하는 유일한 지점(의미 그룹 판단, TASK 배경 (5)(6))은 `--plan` 출력 ↔ `--groups` 입력 왕복이며, 이는 TS-050(무수정 파이프)·TS-113(`--trace --stop-after` 출력 파이프)·TS-042(부분 지정 시 미지정 엔트리 잔존)·TS-052(기존 샤드에 라벨 추가)로 자동 커버된다. [SUPERVISOR] 수동 확인이 필요한 잔여 항목을 찾지 못했다.

## 3. 권고 (advisory — 축 점수에 반영하지 않음, 재작성 강제 아님)

임계를 미달시키지 않으나 EXECUTE 단계에서 흡수하면 검증 강도가 올라가는 항목이다.

1. **S-16 사전 상태 단언 부재 (가장 실질적)** — S-16의 초과 상태는 Given("`split-target`을 초과 상태로 준비")과 PLAN Step 완료기준(§4.2 "매니페스트가 정책 기본값(10240)에서 2축 판정에 걸리도록 `shardPolicy`가 명시")에만 의존한다. 픽스처 정책이 잘못 잡히면 실행 전에도 `manifest_oversize === 0`이라 **"0건이 되고"가 공허하게 참**이 된다(false green). 기대 결과에 "실행 **전** `manifest_oversize === 1`"을 명시 단언으로 추가할 것.
2. **탐지→제안 시작 링크가 S-16 밖에 있음** — 목표 문언은 "**탐지에서** 실제 분할까지"인데 S-16은 `--plan`에서 시작한다. 탐지→유도 링크는 S-12("`next` 명령을 그대로 실행하면 exit 0 + `--plan` 출력")가 별도로 덮어 사슬은 S-12+S-16으로 완결되지만, S-16 앞에 `validate` 1회를 붙여 `next` 문구를 그대로 취해 `--plan`에 넣으면 전 궤가 한 시나리오에 들어간다.
3. **사다리 채택의 "효과" 단언은 최소 조건뿐** — 단일 축 불채택 사유가 "31%(90/288)가 `unassigned`로 남고 줄일 수단이 없음"(PLAN §1.6 대안 (c))인데, S-5의 단언은 "5단계 각 1그룹 이상"이라 S2~S5가 각 1그룹만 걷어도 통과한다. `split-target`에 대해 "S1 단독 결과 대비 `unassigned` 감소" 또는 "`unassigned` 비율 상한"을 1행 추가하면 채택 효과가 실측된다.
4. **손편집 groups 문서 집행 케이스** — 왕복은 무수정(TS-050·113)과 부분 지정(TS-042)으로 검증되나, 사람이 라벨명을 바꾸거나 파일을 그룹 간 옮긴 편집본을 집행하는 경로는 명시 TS가 없다(실사용 U-1 경로). TS-052 인접에 1행 추가를 권고.

## 4. 종합 verdict

| 항목 | 값 |
|------|-----|
| goal | 2 |
| adoption | 2 |
| boundary | 2 |
| average | 2.0 |
| 임계 (§5-1) | 각 축 ≥1 **AND** 평균 ≥1.5 |
| 0점 축 | 없음 |
| **verdict** | **pass** |

> 게이트 PASS 성립 조건(§6 tool-gated 집행)은 ① `scenario-coverage-check` exit 0 ② 본 보고서 verdict pass — **둘 다 충족**. 다만 최종 통과 선언은 PM(오케스트레이터)의 책임이며, 본 에이전트는 판정만 반환한다.

---

## 변경이력

| 일시 (KST) | 변경 내용 |
|---|---|
| 2026-08-04 11:50 | SCENARIO-GATE 1회차 채점 — ①2 ⑤2 ⑥2 / 평균 2.0 / verdict pass, gaps 0건 + advisory 4건 (Task 083) |
