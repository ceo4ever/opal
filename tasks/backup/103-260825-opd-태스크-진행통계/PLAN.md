# PLAN: OPAL Console 태스크 진행 통계

> 작성일: 2026-08-25 | 입력: TASK.md (15:38 최신본), ANALYSIS.md (390줄)
> 모드: Multi-Feature (F-001 ~ F-006) | 실행 모드: **복잡**
> 승계 원천 2원 (plan-guide §2단계): ANALYSIS.md §1.1 관련 파일 목록 · ANALYSIS.md §8 다음 단계 입력 확정값 24행 — **재조사 없이 승계, 재도출 금지**

---

## 결론

- **집계 정의는 `stats.py` 순수 모듈 1곳이 전부 소유하고, 표시 문자열(`7시간 5분`)까지 BE가 내려 FE를 완전 무계산으로 둔다** — P-7 확정.
- **응답 키는 원천 용어(`skill`·`timestamp`·`row_id`)로 통일하고 사표 필드(`row`·`updated_at`)는 값을 채운 deprecated 별칭으로 존치한다** — 캡틴 확정(집계 기준 15), R-A6·R-A7·R-A8 3건 해소.
- **정적 파생만 캐시하고 실시간 파생은 캐시 밖에서 `now` 주입으로 조립한다** — ANALYSIS §8 확정.
- **신규 발견 1건**: `cache.py`의 mtime 무효화가 monotonic 시계와 epoch mtime을 혼용해 `source_path`를 넘기는 즉시 캐시가 상시 무효화된다. R-12 AC(추가)의 선결 조건이므로 최소 수정으로 포함한다 (§추가 발견 P-8).
- **선행 의존 1건 고정**: 산출물 화이트리스트 폐기(BE, Step 6)가 상세 탭 배지 101=9(FE, Step 9)보다 반드시 앞선다.
- **회귀 경계를 선언한다** — `artifact_count`·`artifacts[]` 값 증가는 완료기준 (7)의 명시적 예외이며, 기존 테스트에 이 값을 assert하는 케이스는 0건임을 실측 확인했다 (P-4).
- **베이스라인 모수를 태스크 ID 목록으로 동결한다** — 102 완료 시 opd 모수가 7→8로 이동하므로 검증 시점 재측정 방식은 AC를 비결정론으로 만든다 (P-5).
- Step 14개 / 파일 신규 3 · 수정 7 / 신규 외부 의존 0건.

---

## 확정 입력 판정

> TASK.md `## 확정된 설계 방향`의 `[결정]` 9건 + 집계 기준 15항목은 ANALYSIS.md §확정 입력 판정에서 전건 판정 완료됐다. 본 PLAN은 그 판정을 승계하며 재판정하지 않는다(`analysis-core.md` §2 증분 소비). 아래는 **PLAN 단계에서 새로 판정이 필요한 항목**만 기재한다.

| 항목 | 판정 | 근거 |
|------|------|------|
| 집계 기준 15 「필드 명명 = 원천 용어 정렬」 (`TASK.md:111`) | 해당없음(결정) | 캡틴 확정 — ANALYSIS P-1·P-2 해소분. 재론 금지 |
| ANALYSIS §4(6) 표 「화이트리스트 교집합 91」 | **사실오류** | 워커 계수 오류. 정답 **92**(ANALYSIS.md §8 `[PM 정정]` 행, E1 — PM 재실측, 스코프 `tasks/*/` 폴더별 화이트리스트 교집합 열거). 본 PLAN·`STATS-BASELINE.md`는 92를 쓴다 |
| ANALYSIS §1.1 「`dashboard/backend/cache.py` — 수정 없음」 | **수정필요** | mtime 무효화 비교가 monotonic 값과 epoch mtime을 혼용한다 (`dashboard/backend/cache.py:47`·`:58`). `source_path` 전달만으로는 R-12 AC(추가)가 충족되지 않고 캐시가 상시 무효화된다. E1 — 실측 `time.monotonic()` 608022.53 vs `time.time()` 1787640046.06, 명령 `python3 -c "import time;print(time.monotonic(), time.time())"` (프로젝트 루트). §추가 발견 P-8 참조 |
| ANALYSIS §3.2 「`test_routers.py` 산출물 추론 케이스 4종이 `_get_artifact_files`를 간접 사용하는지 PLAN 확인 대상」 | **간접 사용 0건 — 회귀 없음** | 4종(`dashboard/backend/tests/test_routers.py:394`·`:405`·`:415`·`:425`)은 전부 `_infer_column_from_artifacts`를 직접 호출하며, 이 함수는 별도 목록 `_PROGRESS_ARTIFACTS`(`dashboard/backend/routers/tasks.py:99-102`)를 쓴다. `artifact_count`를 assert하는 케이스는 BE 테스트 전체에 0건. E1 — 스코프: `dashboard/backend/tests/` 11파일, 명령 `grep -rn "artifact_count" dashboard/backend/tests/` |

---

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

`tasks/*/state.json` 파이프라인 행을 원천으로, 태스크 상세 패널에 진행 통계 4블록(A-1~A-4)과 대시보드에 횡단 통계 4블록(B-1~B-4)을 추가한다. 총 리드타임을 **작업(`owner`=`PM`·`auto`)·대기(`owner`=`user`)** 2계열로 분해해 병목 단계와 캡틴 대기 구간을 동시에 드러낸다. 집계 정의는 신설 순수 모듈 `dashboard/backend/stats.py` 1곳에 격리하고, FE는 계산 없이 받은 값만 렌더한다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | 집계 코어 `stats.py` (소요·2계열·실시간·워크플로우별) | R-1, R-3(계산), R-4(계산), R-12(clamp·파싱·빈행) | P0 | 없음 |
| F-002 | 태스크 상세 API 확장 (행 확장·소요 파생·산출물 전수) | R-2, R-3(응답), R-4(응답), R-12(캐시·결측), 집계기준 9 | P0 | F-001 |
| F-003 | 대시보드 집계 API 확장 (워크플로우별) | R-10 | P0 | F-001 |
| F-004 | 태스크 상세 화면 2탭 + A-1~A-4 | R-5, R-6, R-7, R-8, R-9, R-12(축소 표시), R-13 | P0 | F-002 |
| F-005 | 대시보드 화면 B-1~B-4 + 워크플로우 필터 | R-11, R-12(축소 표시), R-13 | P0 | F-003 |
| F-006 | 기준일 스냅샷 · 베이스라인 대조 검증 | R-14, 완료기준 (1)(2)(3) | P0 | 없음(선행) |

R-1~R-14 전건 커버 확인: R-1→F-001 / R-2→F-002 / R-3→F-001·F-002 / R-4→F-001·F-002 / R-5~R-9→F-004 / R-10→F-003 / R-11→F-005 / R-12→F-001·F-002·F-004·F-005 / R-13→F-004·F-005 / R-14→F-006.

### 1.3 기능 의존 그래프 (ASCII)

```
F-006 (베이스라인 동결 — 최선행)
  │
F-001 (stats.py) ─┬─ F-002 (상세 API) ─── F-004 (상세 화면 A-1~A-4)
                  └─ F-003 (대시보드 API) ─ F-005 (대시보드 B-1~B-4)
                                                    │
                                          F-006 (대조 검증 — 최후행)
```

---

## PLAN 결정 — P-3 ~ P-7 (ANALYSIS 「PLAN 결정 필요」 소비)

> ANALYSIS §PLAN 결정 필요 7건 중 P-1·P-2는 캡틴이 집계 기준 15로 확정했다(재론 금지). 아래는 PLAN이 확정하는 5건이며, 각 항목은 **권고안 1개 + 근거**로 결론을 낸다.

### P-3 산출물 유형 분류 축 — **4유형 분류 + 전수 노출** (권고 확정)

**결정**: `.md` 전수를 노출하되, 파일명 기반 4유형으로 분류해 탭을 그룹 정렬한다. `STATE.md`·`AGENTIC-LOG.md`도 노출한다.

| 유형 값 | UI 라벨 | 판정 규칙 | 101 해당 |
|---------|---------|----------|---------|
| `pipeline` | 파이프라인 | 정확 일치: `TASK.md`·`ANALYSIS.md`·`PLAN.md`·`TEST-SCENARIO.md`·`TEST.md`·`DONE.md`·`WIREFRAME.md` | 5 |
| `verification` | 검증 | 접두 일치: `SCENARIO-GATE-`·`GC-`·`L3-JUDGMENT`·`RED-EVIDENCE`·`CONTRACT-CROSSCHECK` | 2 |
| `log` | 로그 | 정확 일치: `STATE.md`·`AGENTIC-LOG.md` | 2 |
| `other` | 기타 | 위 3유형 미해당 전부 | 0 |

**근거 3가지**.
1. **R-5 AC가 전수 노출을 요구한다** — 배지 값 9는 `.md` 전수 값이고, 화이트리스트 6종으로는 101이 5다 (ANALYSIS §8 「R-5 선행 조건」). 배지만 9로 하고 탭은 5만 여는 설계는 배지와 목록이 어긋나 사용자가 4개 문서에 도달할 수 없다.
2. **분류 규칙이 실측 파일명 분포에서 도출된다** — 유형별 접두/정확 일치 규칙이 현행 `tasks/**.md` 193개를 잔여 `other` 없이 덮는지 실측 확인했다. E1 — 스코프: `tasks/*/​*.md`(`tasks/backup/` 제외) 193개, 명령 `find tasks -maxdepth 2 -name "*.md" -not -path "tasks/backup/*" | xargs -n1 basename | sort | uniq -c`. 분포: `TASK.md` 24 · `STATE.md` 23 · `DONE.md` 22 · `PLAN.md` 21 · `AGENTIC-LOG.md` 20 · `TEST-SCENARIO.md` 17 · `SCENARIO-GATE-*` 28 · `ANALYSIS*` 12 · `GC-CONVENTION-*` 12 · `RED-EVIDENCE.md` 5 · `L3-JUDGMENT*` 3 · 그 외 8.
3. **`other` 버킷이 규칙 추가 없이 신종 산출물을 흡수한다** — 미래 산출물마다 분류 규칙을 고치는 유지보수 부채를 만들지 않는다(`coding-principles.md` §2 Simplicity First).

**응답 계약**: 기존 `TaskDetailResponse.artifacts: list[str]`(`dashboard/backend/models.py:160`)는 **전수 목록으로 값만 확장**하고 타입은 유지한다. 유형 정보는 `artifact_items: list[ArtifactItem]`으로 additive 추가한다 — 078 additive 선례(`dashboard/backend/models.py:172`)를 따라 FE 타입 동시 변경 없이 하위 호환을 유지한다.

**FE 반영**: 탭 정렬은 `pipeline → verification → log → other`, 그룹 내부는 위 표 나열 순 → 파일명 오름차순. 기본 활성 탭은 `artifacts[0]`(= `TASK.md`). `[MUST]` 탭 9개가 Sheet 폭(`w-[min(50vw,800px)]`, `dashboard/frontend/src/pages/tasks/TasksPage.tsx:366`)을 넘으므로 `TabsList`를 `overflow-x-auto` 컨테이너에 넣어 **가로 스크롤을 탭 바 내부에 격리**한다 (`TASK.md` §제약 조건 「가로 스크롤 격리」).

### P-4 회귀 경계 선언 — **명시적 예외 1건으로 선언** (권고 확정)

**결정**: 완료기준 (7) "기존 칸반·대시보드 화면의 기존 기능이 회귀하지 않는다"를 아래 4항으로 조작적 정의하고, `artifact_count`·`artifacts[]` **값** 변동을 예외로 명시한다.

| # | 회귀 판정 항목 | Pass 조건 |
|---|--------------|----------|
| 1 | 스키마 회귀 | 기존 응답 필드의 제거·타입 변경·의미 변경 0건 (additive만 허용) |
| 2 | 테스트 회귀 | 기존 pytest(`dashboard/backend/tests/` 11파일) 전건 green · 기존 vitest 7파일 전건 green |
| 3 | 화면 회귀 | 칸반 5컬럼 배치·정렬 불변, 읽기 전용 불변(dnd sensors 비활성·🔒 badge 상시), 대시보드 기존 4메트릭·활동추이·상태 파이 불변 |
| 4 | **예외** | `TaskCardResponse.artifact_count`·`TaskDetailResponse.artifacts[]`의 **값 증가**(101 기준 5→9, 전 카드 동반)는 집계기준 9의 의도된 결과이며 회귀가 아니다 |

**근거**: 화이트리스트 폐기는 `_get_artifact_files`의 소비자 3곳(`dashboard/backend/routers/tasks.py:283`·`:304`·`:361`·`:409`·`:430`)에 동반 변동을 일으키는 것이 설계상 불가피하다(ANALYSIS §3.2). 이를 선언하지 않으면 EXECUTE/TEST 단계에서 "카드 배지 숫자가 바뀌었다"가 회귀로 오판된다. 동시에 **기존 테스트가 이 값에 걸려 있지 않음을 실측 확인**했으므로(§확정 입력 판정 4행) 예외 선언의 비용은 문서 1줄이고, 테스트 수정은 발생하지 않는다.

### P-5 완료기준 (3) 검증 시점 — **태스크 ID 목록 동결(frozen cohort)** (권고 확정)

**결정**: `STATS-BASELINE.md`에 워크플로우별 **모수 구성 태스크 ID 목록**을 명시해 동결하고, 완료기준 (3) 검증은 그 목록으로 필터한 재계산과 대조한다. 검증 시점 재측정 방식은 채택하지 않는다.

동결 코호트 (기준일 2026-08-25, `current_status == "done"` 21건):

| skill | n | 태스크 ID (앞 3자리) |
|-------|---|---------------------|
| opd | 7 | 080 · 091 · 092 · 093 · 094 · 100 · 101 |
| opds | 10 | 081 · 082 · 083 · 085 · 090 · 095 · 096 · 097 · 098 · 099 |
| opp | 4 | 084 · 086 · 087 · 088 |

E1 — 스코프: `tasks/*/state.json` 23파일 전수, 명령 `python3` 인라인 집계(`current_status` 카운트 + `skill`별 `task_id` 열거). 진행 중 2건은 `102`·`103`.

**근거 3가지**.
1. **모수 이동이 확정 사실이다** — `102`(opd)가 본 태스크보다 먼저 완료되면 opd n=7→8이 되고 중앙값이 799분에서 이동한다 (ANALYSIS R-A4). 재측정 방식은 AC의 통과/불통과를 "누가 먼저 끝나느냐"에 맡긴다.
2. **AC는 결정론이어야 한다** — `TASK.md` §제약 조건이 이미 "실시간 값의 AC 금지 — 완료기준 수치 AC는 완료 태스크로만 잡는다"를 규정한다. 코호트 동결은 그 규정을 모수 축으로 확장한 것이다.
3. **베이스라인이 독립 측정이어야 자기확인이 아니다** — `STATS-BASELINE.md`는 `stats.py` **출력이 아니라** ANALYSIS §8 「재검증 완료 수치」(E1, PM 인라인 집계로 독립 재측정된 값)로 작성한다. 그래야 완료기준 (1)의 "베이스라인 ↔ 화면 표시값 일치"가 구현의 자기확인이 아닌 교차 검증이 된다.

**부수 결정**: Step 1(베이스라인 생성)을 **전 Step 중 최선행**에 둔다. 코드보다 먼저 코호트를 동결해야 `102` 완료로 인한 이동을 원천 차단한다.

### P-6 FE 컴포넌트 테스트 도입 — **도입한다 (신규 2파일, 범위 한정)** (권고 확정)

**결정**: `dashboard/frontend/src/pages/tasks/TasksPage.stats.test.tsx`·`dashboard/frontend/src/pages/dashboard/DashboardPage.stats.test.tsx` 2파일을 신설해 A/B 렌더 AC를 vitest 컴포넌트 테스트로 잡는다. L3 시각 확인(playwright)은 **병행하되 AC 판정 주체가 아니다**.

**범위 한정 (사변적 확대 금지)** — 아래 6항만 검증하고, 스냅샷 테스트·픽셀 비교·전체 트리 검증은 작성하지 않는다.

| # | 검증 대상 | 대응 AC |
|---|----------|--------|
| 1 | 상세 Sheet에 탭 2개 렌더 + 기본 활성 「태스크 대시보드」 + 산출물 배지 9 | R-5 |
| 2 | A-1 4타일 문자열 `7시간 5분` / `1시간 45분` / `5시간 20분 (75%)` / `TEST-SCENARIO` | R-6 |
| 3 | A-2 막대 7개 + TEST-SCENARIO 최장 강조 | R-7 |
| 4 | A-4 표 19행 + 게이트 표시 4건 | R-9 |
| 5 | `stats.available === false` 응답에서 "데이터 없음" 렌더 + 예외 0건 | R-12 |
| 6 | B-4 필터 선택 시 B-1~B-3 좁혀짐 + opp 선택 시 「표본 부족」 배지 | R-11 |

**근거 3가지**.
1. **AC 14건 중 7건이 FE 렌더 AC다** — R-5~R-9·R-11·R-13. L3 시각 확인만으로 잡으면 회귀 재발 방지 자산이 남지 않고, 매 검증마다 사람이 화면을 봐야 한다.
2. **인프라가 이미 있고 신규 의존이 0건이다** — `vitest ^4.1.9` + `happy-dom ^20.10.6` + Testing Library 구성이 완비돼 있고(`dashboard/frontend/vitest.config.ts`), `apiClient`를 `vi.mock`으로 대체해 페이지를 렌더하는 선례가 있다(`dashboard/frontend/src/pages/brain/brain-navigation-guard.test.tsx:31-39`). 새 개념 0으로 붙는다.
3. **BE 단위 테스트만으로는 "BE가 옳은 값을 냈다"까지만 증명된다** — FE가 그 값을 실제로 표시하는지는 별개 계약이며, 이번 태스크는 "데이터는 있는데 화면이 버리고 있다"를 고치는 태스크다(`TASK.md` §배경).

### P-7 표시 문자열 소유 — **BE가 소유한다 (`_minutes` + `_label` 쌍)** (권고 확정)

**결정**: 모든 시간량은 정수 분(`*_minutes`)과 표시 문자열(`*_label`)을 **쌍으로** 내린다. FE는 포맷 함수를 갖지 않는다.

포맷 규칙 (`stats.py` `format_duration` 단일 지점 소유):

| 입력(분) | 출력 |
|---------|------|
| `None` | `—` |
| `0` | `0분` |
| `1 ≤ m < 60` | `{m}분` |
| `m ≥ 60`, 나머지 0 | `{h}시간` |
| `m ≥ 60`, 나머지 > 0 | `{h}시간 {r}분` |

**근거 3가지**.
1. **`[MUST]` `TASK.md:119` `[결정]`: "FE는 계산하지 않고 받은 값만 렌더한다"** — 포맷은 반올림 규칙·0분 처리·`—` 처리를 포함하는 판정이며, 판정을 FE에 두면 그 결정이 화면 코드에 흩어진다.
2. **A와 B 두 화면이 같은 포맷을 쓴다** — FE 유틸로 두면 `TasksPage`·`DashboardPage` 양쪽에서 import하는 세 번째 소유자가 생기고, 이는 D-6이 없애려던 "정의가 2곳에 흩어져 앵커가 갈렸다"의 재발이다(`TASK.md:119`).
3. **정수 분을 함께 내리므로 표현력 손실이 없다** — 차트 축 스케일·막대 폭·정렬은 `*_minutes`를, 텍스트는 `*_label`을 쓴다. 023 DONE §3 "단계 파생은 BE 단일 소스 — FE는 표시만"의 연장이다 (→ D-17).

---

## 추가 발견 — P-8 `cache.py` 시계 혼용 (PLAN 신규, 승계 아님)

**사실**: `CacheStore.set`은 `expires_at = time.monotonic() + TTL_SECONDS`로 저장하고(`dashboard/backend/cache.py:58-60`), `CacheStore.get`은 `cached_since = expires_at - TTL_SECONDS`(= 저장 시점 monotonic 값)를 `os.path.getmtime()`(epoch 초)과 직접 비교한다(`dashboard/backend/cache.py:45-51`). 두 값은 기준점이 다른 서로 다른 시계다.

**E1 실측** — 스코프: 프로젝트 루트, 명령 `python3 -c "import time,os; print(time.monotonic(), time.time(), os.path.getmtime('dashboard/backend/cache.py'))"`
`time.monotonic()` = 608022.53 · `time.time()` = 1787640046.06 · `cache.py` mtime = 1781516662.61.
→ `current_mtime > cached_since`가 **항상 참**이므로, `source_path`를 넘긴 항목은 매 조회마다 즉시 폐기된다.

**영향**: R-12 AC(추가) "정적 파생 캐시 저장 시 `source_path`에 태스크 `state.json` 경로가 전달되어 `mtime` 무효화가 실제로 작동한다"를 `source_path` 전달만으로 충족시키면, 무효화가 "작동"하는 게 아니라 **캐시가 무력화**된다. 상세 응답 경로가 매 요청 전수 재계산이 되어 `TASK.md` §제약 조건 「기존 캐시 경로를 그대로 사용하고 무캐시 전수 스캔을 추가하지 않는다」와 정면 충돌한다.

**권고 (PLAN 확정)**: `cache.py`에 **최소 수정 1건**을 포함한다 — 저장 항목에 wall-clock 저장 시각을 함께 보관하고, mtime 비교를 그 값과 수행한다. TTL 축(`time.monotonic()`)은 그대로 둔다.

```python
# 변경 후 계약 (시그니처 불변)
def set(self, key: str, data: Any, source_path: str | None = None) -> None
def get(self, key: str) -> Any | None
```

- 공개 시그니처 무변경 → 호출부 4곳(`dashboard/backend/routers/tasks.py:377`·`:411`·`:433`, `dashboard/backend/routers/dashboard.py:220`) 파급 0.
- 내부 `_store` 튜플만 3-tuple → 4-tuple로 확장한다. `_store` 외부 참조 0건 (E2 — `dashboard/backend/cache.py` 내부 전용).
- **범위 고정**: TTL 값·키 전략·invalidate 동작은 건드리지 않는다. 이 수정 외 캐시 개선을 인접 개선 명목으로 추가하지 않는다 (`coding-principles.md` §4).

**리스크 가설 등록**: H-9 (§리스크 가설 표).

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 된다.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | `stats.py` 앵커 차분 (F-001) | 역행 타임스탬프에서 소요가 음수 → 스택 막대가 음수 폭으로 파손, opp(n=4) 집계 왜곡 | P0 | L1(단위, 고정 픽스처) 의무 | S-1 후보 — `086` `plan.user_confirm` −1분 실측 케이스를 0으로 clamp |
| H-2 | `stats.py` 앵커 진전 규칙 (F-001) | `in_progress`·`pending`·`na`·파싱 실패 행이 앵커를 진전시키면 뒤따르는 done 행의 소요가 통째로 소실 | P0 | L1(단위) 의무 | S-2 후보 — 101 총 425분 = 작업 105 + 대기 320 재현 |
| H-3 | `PipelineRow` 7필드 additive (F-002) | Pydantic 필수 필드로 추가 시 `state.json` 결측 행에서 ValidationError → 상세 패널 500 | P1 | L1(단위) + L2(실 `state.json` 통합) 의무 | S-3 후보 — 신규 필드 전건 기본값 보유, `092` 이전 `gate` 미보유 태스크 200 응답 |
| H-4 | `_get_artifact_files` 화이트리스트 폐기 (F-002) | 소비자 3곳 동반 변동 — 칸반 카드 배지·아카이브 카드 값 변화가 회귀로 오판 | P1 | L2(통합) + 문서(회귀 경계 선언) | S-4 후보 — 101 배지 9 확인 + 기존 pytest 전건 green |
| H-5 | `dashboard.py` ↔ `tasks.py` 헬퍼 공유 (F-003) | 순환 import — `stats.py`가 모델·라우터를 import하면 라우터↔모델↔stats 순환 | P1 | L1(단위, import 검사) 의무 | S-5 후보 — `stats.py` import 목록이 `datetime`·`statistics` 표준 라이브러리로 한정 |
| H-6 | 실시간 파생 캐시 (F-002) | 실시간 값을 캐시에 넣으면 최대 30초 정지 → 분 단위 표시에서 최대 1분 오차 | P2 | L1(단위, `now` 주입) + L3(시각) | S-6 후보 — 캐시 히트 응답에서도 `current_elapsed_minutes`가 재계산됨 |
| H-7 | 상세 Sheet 2탭 재구성 (F-004) | 읽기 전용 계약 위반 — 탭·표 추가 과정에서 dnd sensors 재활성·🔒 badge 소실 | P0 | L1(컴포넌트) + L3(시각) 의무 | S-7 후보 — 칸반 카드 드래그 불가·🔒 상시 표시 유지 |
| H-8 | recharts 스택 막대 색상 (F-004·F-005) | hex 리터럴 유입 → `[MUST]` 토큰 경유 규칙 위반 | P1 | L1(정적 grep) 의무 | S-8 후보 — 신규·수정 FE 파일에서 `#[0-9a-fA-F]{3,8}` 매칭 0건 |
| H-9 | `cache.py` 시계 혼용 수정 (P-8) | `source_path` 전달 시 캐시가 상시 무효화 → 매 요청 전수 재계산(성능 제약 위반) / 수정 오류 시 stale 응답 고착 | P1 | L1(단위, 임시 파일 touch) 의무 | S-9 후보 — 파일 미변경 시 캐시 히트, `state.json` touch 후 즉시 미스 |
| H-10 | 베이스라인 코호트 (F-006) | `102` 완료로 opd 모수 7→8 이동 → 완료기준 (3) 수치 AC가 시점 의존으로 비결정론화 | P1 | 문서(코호트 동결) + L2(대조) 의무 | S-10 후보 — `STATS-BASELINE.md` ID 목록으로 필터한 재계산이 799/276/75분과 일치 |
| H-11 | 목업 ↔ TASK.md 재작성본 충돌 (F-004·F-005) | EXECUTE 워커가 목업을 열고 폐기된 B 블록(혼합 중앙값·스킬/모드 분포)·A-1 4타일을 그대로 구현 | P1 | 문서(Step 본문에 계승/폐기 경계 명시) + L3(시각 대조) | S-11 후보 — B-1이 워크플로우별 3열로 렌더되고 혼합 「5시간 42분」이 화면에 0건 |
| H-12 | `artifacts` 전수 전환 (F-004) | 탭 9개가 Sheet 폭 초과 → 패널 본문이 가로로 밀림 | P2 | L1(컴포넌트) + L3(시각) | S-12 후보 — 탭 바가 자체 컨테이너에서만 가로 스크롤 |

---

## 2. 기능별 분석

> §2.N.1 관련 파일 맵은 ANALYSIS.md §1.1 「관련 파일 목록」 앞 4열을 재조사 없이 승계했다 (plan-guide §2단계 승계 원천 2원). §2.N.2·§2.N.3은 ANALYSIS §8 확정값을 승계해 간략 기술한다.

### F-001: 집계 코어 `stats.py`

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `dashboard/backend/stats.py` | 집계 정의 SSOT 순수 모듈 — 소요·2계열·워크플로우별 집계·실시간 파생 | 신규 |
| BE | `dashboard/backend/tests/test_routers.py` | `stats.py` 집계·`PipelineRow` 확장·결측 내성 RED-first 케이스 추가 | 수정 |

#### 2.1.2 현재 구현

집계 로직은 존재하지 않는다. 유사 파생은 `tasks.py`의 3헬퍼 `_derive_current_stage`(`dashboard/backend/routers/tasks.py:174`)·`_aggregate_status`(`:202`)·`_group_pipeline_stages`(`:228`)뿐이며, 전부 라우터 내부에 있고 시간 축 지표가 없다. 진행률은 `완료 rows / 전체 rows` 단일 수식이다(`dashboard/backend/routers/tasks.py:289-293`·`:415-419`).

원천 스키마 (E1 — 스코프: `tasks/101-260824-opd-핸드오프-스키마-계약정합/state.json`, `python3` json 로드): 최상위 키 9종(`task_id`·`skill`·`mode`·`schema_version`·`created_at`·`updated_at`·`current_status`·`rows`·`next_action`), 행 키 11종(`row_id`·`stage`·`item`·`key`·`status`·`status_label`·`timestamp`·`owner`·`note`·`gate`·`step`). `timestamp` 포맷은 `%Y-%m-%d %H:%M`.

#### 2.1.3 영향 범위

- 신규 모듈이므로 직접 영향은 0. 소비자는 F-002·F-003 두 라우터.
- `[MUST]` **순환 import 회피** — `stats.py`는 표준 라이브러리(`datetime`·`statistics`)만 의존하고 모델·라우터·캐시를 import하지 않는다 (ANALYSIS §8 확정값, R-A13). `dashboard.py`가 이미 `routers.tasks.COLUMN_MAP`을 함수 내 지연 import 중이므로(`dashboard/backend/routers/dashboard.py:151`) 결합을 늘리면 순환 위험이 실재한다.
- 파일 I/O 금지 — 산출물 `.md` 열거는 파일시스템 접근이므로 `stats.py`가 아닌 라우터가 소유한다.

---

### F-002: 태스크 상세 API 확장

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `dashboard/backend/models.py` | `PipelineRow` 확장 + `PipelineGate`·통계 응답 모델 신설 + `TaskDetailResponse` 확장 | 수정 |
| BE | `dashboard/backend/routers/tasks.py` | `get_task_detail`에 소요·실시간 파생 결합, `_group_pipeline_stages` 행 매핑 교정, `_get_artifact_files` 화이트리스트 폐기 | 수정 |
| BE | `dashboard/backend/cache.py` | 캐시 계약 — 호출부에서 `source_path` 전달로 활용 **+ 시계 혼용 최소 수정(P-8)** | 수정 |

> ANALYSIS §1.1은 `cache.py`를 `수정 없음`으로 승계했으나, P-8 실측 결과 `수정`으로 판정을 바꾼다 (§확정 입력 판정 3행).

#### 2.2.2 현재 구현

- `PipelineRow`는 4필드(`row`·`stage`·`status`·`updated_at`)뿐이다 (`dashboard/backend/models.py:136-140`).
- `_group_pipeline_stages`가 행을 `r.get("row", i)`·`r.get("updated_at", "")`에서 읽는다(`dashboard/backend/routers/tasks.py:259-267`). 원천에 두 키가 없으므로 `row`는 그룹 내부 0-based enumerate 인덱스로 폴백하고 `updated_at`은 전건 빈 문자열이다 (ANALYSIS §4(1)).
- `_get_artifact_files`는 6종 화이트리스트 고정이다 (`dashboard/backend/routers/tasks.py:89-96`).
- 캐시 저장 3곳 전부 `source_path` 미전달 (`dashboard/backend/routers/tasks.py:377`·`:411`·`:433`).
- `state.json` 부재 조기 반환 경로가 이미 있다 (`dashboard/backend/routers/tasks.py:403-412`).

#### 2.2.3 영향 범위

- **직접**: `GET /api/tasks/detail` 응답(additive), `GET /api/tasks` 응답의 `artifact_count` **값**(스키마 불변).
- **간접**: `_get_artifact_files` 소비자 3곳 동반 변동(`:283`·`:304`·`:361`·`:409`·`:430`) → P-4 회귀 경계로 흡수.
- **테스트 회귀 0건** (ANALYSIS §8 확정값) — 기존 계약 검증이 `PipelineStageGroup` 4속성만 `hasattr`로 확인하고 `PipelineRow` 필드를 직접 assert하지 않는다 (`dashboard/backend/tests/test_routers.py:653-660`). 산출물 카운트 assert도 0건(§확정 입력 판정 4행).

---

### F-003: 대시보드 집계 API 확장

#### 2.3.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `dashboard/backend/routers/dashboard.py` | `get_dashboard`에 워크플로우별 집계 결합 (`stats.py` 호출) | 수정 |
| BE | `dashboard/backend/models.py` | `DashboardSummaryResponse` 확장 | 수정 |

#### 2.3.2 현재 구현

`GET /api/dashboard`가 이미 존재하고(`dashboard/backend/routers/dashboard.py:109-110`), `_collect_all_tasks`가 프로젝트 전 태스크의 `state.json`을 수집하며 각 state에 `_task_id`·`_project`·`_task_dir`를 주입한다(`dashboard/backend/routers/dashboard.py:46-60`). 현행 산출은 4메트릭·상태분포·활동추이(7일)·알림·최근활동 5종이며 시간 축 지표가 없다. `_resolve_task_title`이 TASK.md H1에서 사람이 쓴 제목을 복원한다(`dashboard/backend/routers/dashboard.py:90`).

#### 2.3.3 영향 범위

- **직접**: `GET /api/dashboard` 응답(additive). 기존 5종 산출 무변경.
- **모수**: 완료 태스크만(집계기준 3) → 실시간 성분 0 → 현행 캐시 그대로 (ANALYSIS §8 확정값). 다중 파일 소스라 단일 `source_path` mtime 무효화는 적용 불가하며 TTL 30초로 충분하다.
- **`.md` 전수 카운트**는 파일시스템 접근이므로 `stats.py`가 아닌 `dashboard.py`가 `tasks.py`의 헬퍼를 지연 import해 수행한다 — `COLUMN_MAP` 지연 import 선례(`dashboard/backend/routers/dashboard.py:151`)를 그대로 따르며 새 모듈을 만들지 않는다.

---

### F-004: 태스크 상세 화면 2탭 + A-1~A-4

#### 2.4.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| FE | `dashboard/frontend/src/pages/tasks/TasksPage.tsx` | 상세 Sheet 2탭 재구성 + A-1~A-4 렌더 + 타입 동기 | 수정 |
| FE | `dashboard/frontend/src/index.css` | 시그니처 3색·상태색 5종 토큰 — 조회 전용, 신규 색 추가 불필요 | 수정 없음 |
| 환경 | `dashboard/frontend/package.json` | recharts 3.8.1 기보유 — 스택 막대에 추가 의존 불필요 | 수정 없음 |

#### 2.4.2 현재 구현

`TaskDrawer`(`dashboard/frontend/src/pages/tasks/TasksPage.tsx:340`)는 고정 헤더(`SheetHeader`, `:368-381`) + 본문 flex 컨테이너(`:384`) 구조이며, 본문은 파이프라인 스테퍼(고정, `:393-397`)와 산출물 `Tabs`(`:400-424`) 2단으로 되어 있다. `Tabs`·`TabsList`·`TabsTrigger`·`TabsContent`가 이미 import돼 있다(`:37`). FE 타입 `PipelineRow`·`PipelineStageGroup`·`TaskDetail`이 로컬 인터페이스로 선언돼 있다(`:64-90`).

#### 2.4.3 영향 범위

- **직접**: 상세 Sheet 본문 구조 전체. 칸반 보드 본체·카드는 무변경.
- `[MUST]` `dashboard/frontend/src/pages/tasks/TasksPage.tsx:1-9` `@header`: "[MUST] 읽기 전용: dnd-kit sensors 비활성·🔒 badge 상시·grab 커서 미사용" — 통계 블록도 조회 전용이며 쓰기 동작을 추가하지 않는다.
- **타입 동기 누락 시 빌드 실패** — `npm run build`가 `tsc -b && vite build`이므로 BE 응답 확장분을 FE 인터페이스에 반영하지 않으면 사용 시점에 컴파일 오류가 난다.

---

### F-005: 대시보드 화면 B-1~B-4

#### 2.5.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| FE | `dashboard/frontend/src/pages/dashboard/DashboardPage.tsx` | B-1~B-4 렌더 + 워크플로우 필터 + 타입 동기 | 수정 |

#### 2.5.2 현재 구현

`DashboardPage`(`dashboard/frontend/src/pages/dashboard/DashboardPage.tsx:436`)는 로컬 `useState<Period>`로 기간 필터를 관리하고 `ToggleGroup`으로 전환한다(`:184-195`). 차트 컴포넌트 4종 `MetricCard`(`:132`)·`ActivityChart`(`:168`)·`StatusPieChart`(`:253`)·`RecentTable`(`:375`)이 이미 있다. recharts는 `AreaChart`·`PieChart`만 import 중이다(`:15-27`). 색상은 CSS 변수 문자열 전달 패턴을 쓴다(`:202-232` — `stroke="var(--brand-primary)"`).

> **주의 (기존 코드 상태)**: `PIE_COLORS`(`dashboard/frontend/src/pages/dashboard/DashboardPage.tsx:246-251`)는 `oklch()` 리터럴을 직접 쓴다. hex는 아니므로 `[MUST]` 규칙 위반은 아니지만 토큰 경유는 아니다. **신규 차트는 이 패턴이 아니라 `var(--status-*)` CSS 변수 전달 패턴(`:202-232`)을 따른다.** 기존 `PIE_COLORS`는 인접 개선 명목으로 수정하지 않는다 (`coding-principles.md` §4).

#### 2.5.3 영향 범위

- **직접**: 대시보드 화면 하단에 통계 4블록 추가. 기존 4메트릭·활동추이·파이·알림·최근활동 무변경.
- **필터 상태**: `DashboardPage` 로컬 `useState` + 기존 `ToggleGroup` 패턴, ui-store 미사용, API 재호출 없음 (ANALYSIS §8 확정값).

---

### F-006: 기준일 스냅샷 · 베이스라인 대조 검증

#### 2.6.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `tasks/103-260825-opd-태스크-진행통계/STATS-BASELINE.md` | 기준일 2026-08-25 스냅샷 — 완료기준 대조 원천 | 신규 |

#### 2.6.2 현재 구현

없음. ANALYSIS §8 「재검증 완료 수치」가 독립 측정된 원천 값을 제공한다.

#### 2.6.3 영향 범위

- 런타임 경로 영향 0 — `[MUST]` `TASK.md:211` R-14 AC: "런타임 경로에는 스냅샷 파일을 두지 않는다".
- 완료기준 (1)(2)(3) 검증의 대조 원천이 된다.

---

## 3. 기능별 설계

### F-001: 집계 코어 `stats.py`

#### 3.1.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `dashboard/backend/stats.py` | BE | 집계 기준 15항목 전부를 소유하는 순수 모듈 | `TASK.md:119` `[결정]` · ANALYSIS §8 「`stats.py` 의존 범위」 |
| 2 | `dashboard/backend/tests/test_stats.py` | BE | `stats.py` 순수 함수 단위 테스트 (고정 픽스처, `now` 주입) | ANALYSIS §8 「`stats.py` 시간 주입」 |

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `dashboard/backend/tests/test_routers.py` | BE | 라우터 결합 계약 케이스 추가(`PipelineRow` 확장·결측 내성·산출물 전수) | `dashboard/backend/tests/test_routers.py:627-668` |

#### 3.1.2 API·데이터 모델·화면 설계

**공개 시그니처** (표준 라이브러리 `datetime`·`statistics`만 의존 — ANALYSIS §8 확정값)

```python
TS_FORMAT = "%Y-%m-%d %H:%M"

def parse_ts(value: str | None) -> datetime | None
def format_duration(minutes: int | None) -> str
def owner_series(row: dict, *, live: bool = False) -> str          # "work" | "wait" | ""
def row_durations(state: dict) -> list[dict]                        # 정적 — 행별 소요·계열·게이트
def task_static_stats(state: dict) -> dict                          # 정적 — 캐시 대상
def task_live_stats(state: dict, now: datetime | None = None) -> dict  # 실시간 — 캐시 밖
def workflow_stats(states: list[dict]) -> list[dict]                # 완료 태스크만, 워크플로우별
```

> ANALYSIS Q1은 `task_stats(state, now=None)` 단일 함수를 후보로 제시했다. 본 PLAN은 이를 `task_static_stats` / `task_live_stats` 2함수로 분할한다 — 근거: ANALYSIS §8 「캐시 전략」이 "정적 파생만 캐시, 실시간 파생은 캐시 밖 조립"을 확정했으므로, 캐시 경계와 함수 경계를 일치시키지 않으면 호출부가 반환 dict를 쪼개는 계산을 하게 된다. 확정값의 구현 형태 구체화이며 확정값 변경이 아니다.

**앵커·소요 알고리즘** (집계 기준 1·2·2-a)

1. `anchor = parse_ts(state["created_at"])`.
2. `rows` 원 순서로 순회. `status != "done"`인 행은 **소요 계산·앵커 진전 모두 건너뛴다** — `pending`·`na`·`in_progress`·`failed` 전부 제외 (ANALYSIS §8 「소요 합산 대상 행」, R-A11 열거 보정).
3. `ts = parse_ts(row["timestamp"])`가 `None`이면 소요 `None`, **앵커 미진전** (ANALYSIS §8 「파싱 실패 행 처리」).
4. `duration = max(0, int((ts - anchor).total_seconds() // 60))` — 음수는 0으로 clamp (ANALYSIS §8 「음수 소요 처리」, `086` `plan.user_confirm` 실측 −1분).
5. `anchor = max(anchor, ts)` — **단조 앵커**. 역행 행이 앵커를 되돌리면 다음 행 소요가 그만큼 부풀어 총합이 `마지막 done ts − created_at`과 어긋난다. 단조 앵커는 clamp 후에도 총합 항등을 보존한다.

**2계열 귀속** (집계 기준 6·14)

| 대상 | 판정 |
|------|------|
| `done` 행 | `owner == "user"` → `wait`, 그 외(`PM`·`auto`) → `work` |
| 현재 행(실시간) | `key`가 `.user_confirm`으로 끝나면 `wait`, 아니면 `work` — `owner` 미사용 |

> `[MUST]` `TASK.md:126` `[사실]`: "`pending` 행의 `owner`는 `init` 기본값이라 실시간 대기 귀속에 쓸 수 없다". 실측 `pending` 28행 전건 `owner=PM`, 예외 0건 (ANALYSIS §확정 입력 판정 F-4, E1).

**`task_static_stats` 반환 키** (정적 — 캐시 대상)

| 키 | 타입 | 의미 | 대응 AC |
|----|------|------|--------|
| `available` | bool | `rows`가 비었거나 `created_at` 파싱 실패면 `False` | R-12 |
| `total_minutes` / `total_label` | int / str | 완료 태스크의 총 리드타임 (마지막 done ts − `created_at`) | R-3, R-6 |
| `work_minutes` / `work_label` | int / str | 작업 계열 합 | R-3, R-6 |
| `wait_minutes` / `wait_label` | int / str | 대기 계열 합 | R-3, R-6 |
| `wait_ratio` | int | 대기 / 총 리드타임 백분율 (반올림) | R-6 |
| `peak_stage` / `peak_stage_label` | str / str | 최장 단계명과 그 소요 표시 문자열 | R-6, R-7 |
| `stages` | list[dict] | 단계별 `stage`·`work_minutes`·`wait_minutes`·`total_minutes`·`total_label`·`is_peak` | R-3, R-7 |
| `rows` | list[dict] | 행별 `row_id`·`duration_minutes`·`duration_label`·`series`·`is_max_gap` | R-8, R-9 |
| `gate_count` | int | `gate` 키 보유 행 수 | R-9 |
| `gate_recorded` | bool | 태스크 전체 행에 `gate`가 0건이면 `False` → FE 「미기록」 | R-12 |
| `blocker_count` | int | `status == "failed"` 행 수 | 집계기준 8 |

**`task_live_stats` 반환 키** (실시간 — 캐시 밖, `now` 주입)

| 키 | 타입 | 의미 | 대응 AC |
|----|------|------|--------|
| `is_running` | bool | `current_status != "done"` | R-6 |
| `total_minutes` / `total_label` | int / str | 진행 중이면 `created_at` → `now`, 완료면 정적 값 그대로 (집계기준 11) | R-4 |
| `current_row_id` / `current_stage` / `current_item` / `current_key` | int / str | `in_progress` 행 우선, 없으면 첫 `pending` 행 (집계기준 12) | R-4 |
| `current_series` | str | `key` 패턴 판정 (집계기준 14) | R-4 |
| `current_elapsed_minutes` / `current_elapsed_label` | int / str | 직전 done 행 → `now` (집계기준 13) | R-4 |

> `[MUST]` `TASK.md:223` §제약 조건: "실시간 파생값은 렌더 시각에 따라 변하므로 완료기준 수치 AC는 완료 태스크로만 잡는다." → `now` 주입이 BE 단위 테스트 층에서만 결정론적 assert를 가능하게 하는 장치다 (ANALYSIS §8 「`stats.py` 시간 주입」).

**`workflow_stats` 반환 형태** (집계 기준 3·4·5)

입력은 `current_status == "done"`인 state dict 리스트다. 라우터가 사전에 `_title`을 주입한다. 반환은 `skill`별 dict 리스트:

| 키 | 타입 | 의미 |
|----|------|------|
| `skill` | str | 원천 필드 값 그대로 (`opd`·`opds`·`opp`) — 집계기준 15 |
| `n` | int | 완료 태스크 수 |
| `sample_insufficient` | bool | `n < 5` → FE 「표본 부족」 배지 (집계기준 5) |
| `median_minutes` / `median_label` | int / str | 총 리드타임 중앙값 — **주 지표** |
| `mean_minutes` / `mean_label` | int / str | 평균 — 보조 지표 |
| `work_minutes` / `wait_minutes` / `wait_ratio` | int | 워크플로우 누적 2계열 |
| `gate_count` / `blocker_count` | int | 게이트·블로커 합계 |
| `stages` | list[dict] | 단계별 `stage`·`n`·`median_minutes`·`median_label`·`work_minutes`·`wait_minutes`·`is_peak` |
| `tasks` | list[dict] | 태스크별 `task_id`·`title`·`total_minutes`·`total_label`·`is_peak` |

> **`is_running`을 `tasks[]`에 두지 않는다** — 집계기준 3이 "B는 완료 태스크만"으로 확정했으므로 B-3에 진행 중 태스크가 등장하지 않는다. 목업 `mockup/dashboard.html` B-3의 `live` 막대 2개(`102`·`103`)는 이 확정에 의해 폐기된다.

**결측 내성 3경로 + 1** (R-12, ANALYSIS Q6 승계)

| 경로 | 차단 지점 | 처리 |
|------|----------|------|
| `state.json` 부재 | BE 라우터 (기존 조기 반환, `dashboard/backend/routers/tasks.py:403-412`) | `stats` 필드를 `available=False`로 채워 200 반환 |
| `rows` 비어있음 | BE `stats.py` | 빈 집계 반환. IndexError 금지 |
| `timestamp` 파싱 실패 | BE `stats.py` 단일 지점 | 소요 제외 + 앵커 미진전 |
| 역행 타임스탬프 | BE `stats.py` 단일 지점 | 0으로 clamp + 단조 앵커 |

FE는 `available === false` 수신 시 축소 표시만 담당하며 자체 방어 로직을 갖지 않는다 (ANALYSIS §8 「결측 내성 차단층」).

#### 3.1.3 환경 변경

해당 없음 — 표준 라이브러리만 사용. numpy/pandas 도입 없음.

#### 3.1.4 배치/마이그레이션

해당 없음. `stats.py`는 기존 `install_dashboard()` 패키지 복사 경로에 포함되어 배포 스크립트 수정이 불필요하다 (ANALYSIS §8 「배포 영향」).

#### 3.1.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-3 AC | 기능 테스트 | 101 픽스처에서 총 425분 = 작업 105 + 대기 320, `wait_ratio` 75 |
| TS-002 | R-3 AC | 기능 테스트 | 101 단계별 7행이 TASK 24(0/24)·ANALYSIS 22(17/5)·PLAN 13(11/2)·TEST-SCENARIO 295(10/285)·EXECUTE 18(18/0)·TEST 51(47/4)·CLOSE 2(2/0) |
| TS-003 | R-12 AC(추가) | 기능 테스트 | `086` 역행 행에서 소요 0, 음수 0건, 총합 = 마지막 done ts − `created_at` |
| TS-004 | R-12 AC | 기능 테스트 | `rows: []`·`created_at` 결측·`timestamp` 형식 오류 3케이스에서 예외 없이 `available=False` 또는 빈 집계 반환 |
| TS-005 | R-4 AC | 기능 테스트 | 고정 `now` 주입 시 진행 중 픽스처의 `current_key`가 `task.user_confirm`, `current_series` = `wait`, `total_minutes`가 `now` 기준 |
| TS-006 | R-4 AC | 기능 테스트 | 완료 픽스처(101)에서 `now`를 바꿔도 `total_minutes` 425 불변 |
| TS-007 | R-10 AC | 기능 테스트 | 동결 코호트 21건 입력 시 `skill`별 중앙값 opd 799 / opds 276 / opp 75, 대기 비중 21%/4%/54%, `opp.sample_insufficient === True` |
| TS-008 | R-1 AC, H-5 | 회귀 테스트 | `stats.py` import 목록이 `datetime`·`statistics`로 한정되고 `dashboard.backend` 하위 모듈 import 0건 |
| TS-009 | P-7 | 기능 테스트 | `format_duration`: `None`→`—`, `0`→`0분`, `45`→`45분`, `120`→`2시간`, `425`→`7시간 5분` |

---

### F-002: 태스크 상세 API 확장

#### 3.2.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `dashboard/backend/models.py` | BE | `PipelineGate`·`TaskStats`·`ArtifactItem` 신설, `PipelineRow` 7필드 + 파생 4필드 additive, `PipelineStageGroup` 5필드 additive, `TaskDetailResponse` 2필드 additive | `dashboard/backend/models.py:136-161` |
| 2 | `dashboard/backend/routers/tasks.py` | BE | `_group_pipeline_stages` 행 매핑을 원천 키로 교정 + 파생 결합, `get_task_detail`에 정적/실시간 파생 조립, `_get_artifact_files` 전수화 + `classify_artifact` 신설, 캐시 `source_path` 전달 | `dashboard/backend/routers/tasks.py:89-96`·`:259-267`·`:398-433` |
| 3 | `dashboard/backend/cache.py` | BE | mtime 비교 기준을 wall-clock으로 교정 (P-8, 최소 수정) | `dashboard/backend/cache.py:45-60` |

#### 3.2.2 API·데이터 모델·화면 설계

**`PipelineGate` (신설)** — 타입 모델 채택 (ANALYSIS §8 확정값, Q4)

| 필드 | 타입 | 기본값 |
|------|------|-------|
| `artifacts` | `list[str]` | `[]` |
| `checklist` | `list[str]` | `[]` |

> 근거: 원천 스키마가 `gate`를 `required: ["artifacts","checklist"]` + `additionalProperties: false`로 닫아 두었다 (`~/.opal/tools/state-tool/schema/state.schema.json` `rows.items.properties.gate`). 타입 모델을 쓰면 R-2 AC("`gate`가 `artifacts`·`checklist`를 가진 객체로 직렬화된다, 불리언 아님")가 스키마 층에서 자동 보증된다. `None`은 "게이트 행 아님"을 뜻하며 태스크 단위 「미기록」(`gate_recorded`)과는 별개 축이다.

**`PipelineRow` 확장** (`dashboard/backend/models.py:136-140`) — **전건 기본값 있는 additive** (078 선례 `dashboard/backend/models.py:172`)

| 필드 | 타입 | 기본값 | 성격 | 대응 AC |
|------|------|-------|------|--------|
| `row` | int | 0 | **deprecated 별칭** — `row_id` 값으로 채운다 | R-2 AC(추가) |
| `updated_at` | str | `""` | **deprecated 별칭** — `timestamp` 값으로 채운다 | R-2 AC(추가) |
| `stage` / `status` | str | — | 기존 | — |
| `row_id` | int | 0 | 신규 · 원천 정렬 키 | 집계기준 15 |
| `key` | str | `""` | 신규 · `*.user_confirm` 판정 원천 | R-2 |
| `item` | str | `""` | 신규 · A-4 「항목」 열 | R-9 |
| `timestamp` | str | `""` | 신규 · 원천 시각 | R-2 |
| `time_label` | str | `""` | 신규 · `HH:MM` 표시 문자열 | P-7, R-8 |
| `owner` | str | `""` | 신규 · 2계열 귀속 원천 | R-2 |
| `owner_label` | str | `""` | 신규 · `PM` / `캡틴` / `자동` | R-8, R-9 |
| `note` | `str \| None` | `None` | 신규 · A-4 비고 | R-2 |
| `gate` | `PipelineGate \| None` | `None` | 신규 · 게이트 행 표시 | R-2 |
| `duration_minutes` | int | 0 | 파생 · 행 소요 | R-3 |
| `duration_label` | str | `""` | 파생 · 표시 문자열 | P-7 |
| `series` | str | `""` | 파생 · `work` / `wait` / `""`(비done) | R-9 |
| `is_max_gap` | bool | `false` | 파생 · A-3 최대 공백 강조 | R-8 |

> **[MUST] 집계 기준 15 (캡틴 확정, `TASK.md:111`)**: "응답 키는 `state.json` 스키마 용어(`skill`·`timestamp`·`row_id`)를 쓴다. 사표 필드 `updated_at`·`row`는 deprecated 별칭으로 존치하되 값을 채운다. 「워크플로우」는 UI 표시 라벨로만 남는다." → 응답 키에 `workflow`를 만들지 않는다. 이 결정이 ANALYSIS R-A6·R-A7·R-A8 `terminology_mismatch` 3건을 해소한다.
>
> **R-2 AC 보정**: R-2 AC 본문은 신규 5키(`owner`·`gate`·`note`·`timestamp`·`key`)를 명시하나, R-2 AC(추가)가 요구하는 사표 필드 교정을 위해 `row_id`가, R-9가 요구하는 「항목」 열을 위해 `item`이 함께 필요하다. 신규 원천 필드는 **7종**이 된다 — AC 축소가 아닌 확장이며, 5키 검증은 그대로 통과한다.

**`PipelineStageGroup` 확장** (`dashboard/backend/models.py:143-148`)

| 필드 | 타입 | 기본값 | 대응 AC |
|------|------|-------|--------|
| `work_minutes` / `wait_minutes` / `total_minutes` | int | 0 | R-3, R-7 |
| `total_label` | str | `""` | P-7, R-7 |
| `is_peak` | bool | `false` | R-7 |

**`TaskStats` (신설)** — `task_static_stats` + `task_live_stats` 병합 결과를 담는 응답 모델. 필드는 §3.1.2의 두 반환 키 표와 1:1 대응하며, `stages`·`rows`는 `PipelineStageGroup`·`PipelineRow`가 이미 담으므로 `TaskStats`에는 중복 게재하지 않는다.

**`ArtifactItem` (신설)** — P-3

| 필드 | 타입 | 값 |
|------|------|---|
| `name` | str | 파일명 |
| `type` | str | `pipeline` / `verification` / `log` / `other` |
| `type_label` | str | 파이프라인 / 검증 / 로그 / 기타 |

**`TaskDetailResponse` 확장** (`dashboard/backend/models.py:151-161`)

| 필드 | 타입 | 기본값 | 비고 |
|------|------|-------|------|
| `stats` | `TaskStats \| None` | `None` | `None` 또는 `available=false` → FE "데이터 없음" |
| `artifact_items` | `list[ArtifactItem]` | `[]` | 기존 `artifacts: list[str]`는 타입 유지·값만 전수 확장 |

**`_group_pipeline_stages` 행 매핑 교정** (`dashboard/backend/routers/tasks.py:259-267`)

| 대상 | 현행 | 변경 후 |
|------|------|--------|
| 행 번호 | `r.get("row", i)` — 그룹 내부 0-based 폴백 | `r.get("row_id", i + 1)` → `row_id`·`row` 양쪽에 동일 값 |
| 시각 | `r.get("updated_at", "")` — 전건 빈 문자열 | `r.get("timestamp", "")` → `timestamp`·`updated_at` 양쪽에 동일 값 |

> A-3/A-4는 `pipeline[].rows[]` 평탄화로 충분하다 — `stage` 그룹이 전건 연속임을 실측 확인했으므로 원 행 순서가 보존된다. 별도 평탄 배열 필드를 신설하지 않는다 (ANALYSIS §8 「A-3/A-4 데이터 소스」).

**`_get_artifact_files` 전수화 + `classify_artifact` 신설** (`dashboard/backend/routers/tasks.py:89-96`)

```python
def _get_artifact_files(task_dir: str) -> list[str]     # 시그니처 불변, .md 전수 + 유형 순 정렬
def classify_artifact(name: str) -> tuple[str, str]     # (type, type_label) — P-3 4유형
```

시그니처를 유지하므로 소비자 3곳(`:283`·`:304`·`:361`·`:409`·`:430`)은 호출 코드 변경 없이 새 값을 받는다. 정렬은 `pipeline → verification → log → other`, 그룹 내부는 P-3 표 나열 순 → 파일명 오름차순.

**캐시 전략** (ANALYSIS §8 확정값, Q3)

- 캐시 키 현행 유지: `task_detail:{project}:{task_id}` (`dashboard/backend/routers/tasks.py:398`).
- `cache.set(cache_key, static_payload, source_path=os.path.join(task_dir, "state.json"))` — 파일 1개 `stat`이므로 전수 스캔이 아니며 성능 제약을 위반하지 않는다.
- 캐시에는 **정적 파생만** 담는다. 진행 중 태스크의 실시간 파생은 캐시 히트 이후 `task_live_stats(state, now=datetime.now())`로 계산해 응답에 합성한다.
- **캐시 히트 시에도 `state`가 필요하다** — `_read_state(task_dir)`는 캐시 조회보다 앞서 수행하고, 캐시는 정적 파생 payload만 담도록 구조를 조정한다.

**`cache.py` 최소 수정 (P-8)**

`_store` 항목을 `(data, expires_at, source_path)` → `(data, expires_at, source_path, set_wall)`로 확장하고, `set_wall = time.time()`을 저장한다. `get`의 mtime 비교를 `current_mtime > set_wall`로 바꾼다. `TTL_SECONDS`·`expires_at`(monotonic) 축은 그대로 둔다. 공개 시그니처 무변경.

#### 3.2.3 환경 변경

해당 없음.

#### 3.2.4 배치/마이그레이션

해당 없음.

#### 3.2.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-010 | R-2 AC | 통합 테스트 | 101 상세 응답 `pipeline[].rows[]` 각 원소가 `owner`·`gate`·`note`·`timestamp`·`key` 5키 보유, `gate` 보유 행 4건, `gate`가 `artifacts`·`checklist` 객체로 직렬화 |
| TS-011 | R-2 AC(추가) | 통합 테스트 | 101 `rows[]` 평탄화에서 `row`가 1~19 연속, `updated_at` 빈 문자열 0건 |
| TS-012 | R-3 AC | 통합 테스트 | 101 상세 응답 `stats.total_minutes` 425·`work_minutes` 105·`wait_minutes` 320·`wait_ratio` 75, `pipeline[]` 7그룹 소요가 TS-002와 동일 |
| TS-013 | R-4 AC | 통합 테스트 | 진행 중 태스크(103) 상세에서 `stats.current_key` 식별·`current_series`가 `key` 패턴 판정, 완료 태스크(101)는 `is_running=false`·425 고정 |
| TS-014 | 집계기준 9, R-5 선행 | 통합 테스트 | 101 상세 `artifacts` 길이 9, `artifact_items` 유형 분포 pipeline 5·verification 2·log 2·other 0 |
| TS-015 | R-12 AC | 통합 테스트 | `state.json` 없는 태스크 상세가 200 + `stats.available=false`, `092` 이전 태스크에서 `gate_recorded=false` |
| TS-016 | H-9, R-12 AC(추가) | 기능 테스트 | 임시 파일 기반 — 파일 미변경 시 캐시 히트, 파일 `touch` 후 즉시 미스 |
| TS-017 | P-4 회귀 경계 1·2 | 회귀 테스트 | 기존 pytest 전건 green, 기존 응답 필드 제거·타입 변경 0건 |

---

### F-003: 대시보드 집계 API 확장

#### 3.3.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `dashboard/backend/models.py` | BE | `WorkflowStat`·`StageStat`·`TaskLeadtime` 신설, `DashboardSummaryResponse` 5필드 additive | `dashboard/backend/models.py:84-92` |
| 2 | `dashboard/backend/routers/dashboard.py` | BE | `get_dashboard`에 워크플로우별 집계·산출물 규모 결합 | `dashboard/backend/routers/dashboard.py:136-138`·`:210-221` |

#### 3.3.2 API·데이터 모델·화면 설계

**`DashboardSummaryResponse` 확장** (`dashboard/backend/models.py:84-92`) — 기존 8필드 무변경

| 필드 | 타입 | 기본값 | 대응 AC |
|------|------|-------|--------|
| `completed_tasks` | int | 0 | R-10 (21) |
| `total_tasks` | int | 0 | R-10 (23) |
| `artifact_total` | int | 0 | R-10 (192) |
| `artifact_by_type` | `dict[str,int]` | `{}` | P-3 |
| `workflow_stats` | `list[WorkflowStat]` | `[]` | R-10, R-11 |

**`WorkflowStat` / `StageStat` / `TaskLeadtime`** — 필드는 §3.1.2 `workflow_stats` 반환 형태 표와 1:1 대응한다. `skill` 필드명을 쓰고 `workflow`를 만들지 않는다 (집계 기준 15).

**엔드포인트 계약**

```
GET /api/dashboard?project=<절대경로>
```

경로·파라미터 무변경. 응답만 additive 확장 (`dashboard/backend/routers/dashboard.py:109-110`).

**집계 결합 지점**

1. `all_tasks` 수집 직후(`dashboard/backend/routers/dashboard.py:136-138`), 각 state에 `_title = _resolve_task_title(t["_task_dir"], t["_task_id"])`를 주입한다 — `tasks.py`의 폴더명 폴백 결함(`dashboard/backend/routers/tasks.py:297`)을 우회한다. **선재 결함 수정이 아니라 이미 `dashboard.py`가 소유한 헬퍼의 재사용**이며, `tasks.py` 쪽 제목 폴백은 건드리지 않는다 (`TASK.md` §범위 「제목 폴백 결함 수정 — 별건」).
2. `completed = [t for t in all_tasks if t.get("current_status") == "done"]` → `workflow_stats(completed)`.
   - E1 검증 — 스코프: `tasks/*/state.json` 23파일 전수, 명령 `python3` 인라인 `current_status` 카운트. 결과 `done` 21 · `in_progress` 2, `skill`별 완료 opd 7 · opds 10 · opp 4. 집계기준 3의 "완료 21건 / 전체 23건"과 정합.
3. 산출물 규모: `from dashboard.backend.routers.tasks import _get_artifact_files, classify_artifact`를 **함수 내부 지연 import**로 조회한다 — `COLUMN_MAP` 지연 import 선례(`dashboard/backend/routers/dashboard.py:151`)를 그대로 따르며 새 모듈을 만들지 않는다.
4. 캐시는 현행 유지 — 모수가 완료 태스크만이라 실시간 성분이 없고, 다중 파일 소스라 단일 `source_path` mtime 무효화가 적용 불가하다 (ANALYSIS §8 「`/api/dashboard` 캐시」).

#### 3.3.3 환경 변경

해당 없음.

#### 3.3.4 배치/마이그레이션

해당 없음.

#### 3.3.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-020 | R-10 AC | 통합 테스트 | `GET /api/dashboard?project=<ai-framework 절대경로>` 응답에 `completed_tasks` 21 · `total_tasks` 23 |
| TS-021 | R-10 AC | 통합 테스트 | `workflow_stats`에 `skill` opd/opds/opp 3건, 중앙값 799/276/75분, `wait_ratio` 21/4/54 |
| TS-022 | R-10 AC, P-3 | 통합 테스트 | `artifact_total`이 `.md` 전수와 일치하고 `artifact_by_type` 4키 합계가 `artifact_total`과 동일 |
| TS-023 | 집계기준 15, H-5 | 회귀 테스트 | 응답 JSON에 `workflow` 키 0건, `skill` 키 사용. `stats.py`가 라우터·모델을 import하지 않음 |
| TS-024 | P-4 회귀 경계 1 | 회귀 테스트 | 기존 8필드(`total_projects`·`running_tasks`·`blockers`·`additional_work`·`status_distribution`·`activity_trend`·`alerts`·`recent_activities`) 값·타입 불변 |

---

### F-004: 태스크 상세 화면 2탭 + A-1~A-4

#### 3.4.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `dashboard/frontend/src/pages/tasks/TasksPage.stats.test.tsx` | FE | A-1~A-4·2탭 렌더 AC 컴포넌트 테스트 | P-6 |

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `dashboard/frontend/src/pages/tasks/TasksPage.tsx` | FE | 로컬 타입 동기 + `TaskDrawer` 2탭 재구성 + A-1~A-4 렌더 | `dashboard/frontend/src/pages/tasks/TasksPage.tsx:64-90`·`:340-437` |

#### 3.4.2 API·데이터 모델·화면 설계

##### 화면: 태스크 상세 Sheet (2탭)

- **ID**: FE-1
- **유형**: detail
- **action**: modify
- **경로**: `/tasks` (Sheet 오버레이 — 별도 라우트 없음)
- **파일**: `dashboard/frontend/src/pages/tasks/TasksPage.tsx`
- **shadcn 컴포넌트**: `Sheet`·`SheetHeader`·`SheetTitle`·`SheetDescription`(기존), `Tabs`·`TabsList`·`TabsTrigger`·`TabsContent`(기존, `:39`), `Badge`·`Card`·`Separator`·`ScrollArea`·`Skeleton`(기존), `Table`·`TableHeader`·`TableBody`·`TableRow`·`TableCell`(A-4용 — `dashboard/frontend/src/components/ui/table.tsx` 기보유, `DashboardPage.tsx:39-46`에서 사용 중)
- **UI 작업**: `TaskDrawer` 본문을 최상위 `Tabs` 2개(`stats` / `artifacts`)로 재구성. 태스크 식별 헤더(ID·제목·`skill`·`mode`·상태 배지·기간)는 `SheetHeader`에 고정 유지. 「태스크 대시보드」 탭에 기존 `PipelineStepper` + A-1~A-4 4블록, 「산출물」 탭에 기존 문서 뷰어 + 유형 그룹 정렬 탭. 기본 활성 탭 `stats`. 신규 하위 컴포넌트 4개(`StatsSummaryCards`·`StageStackBars`·`RowTimeline`·`RowDetailTable`)를 같은 파일 내부에 정의한다 — 기존 파일이 하위 컴포넌트를 파일 내부에 두는 패턴(`PipelineStepper`·`ArtifactContent`·`TaskDrawer`)을 따른다.
- **API 연동**: `GET /api/tasks/detail?project=&task_id=` — 기존 쿼리 그대로. 응답의 `stats`·`pipeline[].rows[]`·`artifact_items`를 읽는다. **신규 호출 0건, 재호출 0건.**

**블록별 렌더 계약** (전부 BE 값 직독 — FE 계산 0)

| 블록 | 데이터 소스 | 렌더 |
|------|-----------|------|
| A-1 | `stats.total_label` · `work_label` · `wait_label`+`wait_ratio` · `peak_stage` | 4타일. 진행 중이면 총 리드타임 타일에 「진행 중」 배지 (`stats.is_running`) |
| A-2 | `pipeline[].{stage, work_minutes, wait_minutes, total_label, is_peak}` | 가로 스택 막대 7개. 폭 = `total_minutes / max(total_minutes)`, 내부 2색 분할 = `work_minutes` : `wait_minutes`. `is_peak` 행 강조 |
| A-3 | `pipeline[].rows[]` 평탄화의 `{time_label, stage, item, owner_label, series, duration_label, is_max_gap}` | 시각 오름차순 타임라인. `series==="wait"` 항목 앞에 「공백 {duration_label} · 캡틴 확인 대기」 표시, `is_max_gap`에 「최대 공백」 접미 |
| A-4 | `pipeline[].rows[]` 평탄화 전량 | 표 7열(#·단계·항목·상태·담당·시각·소요[작업/대기 2열]). `gate !== null` 행에 `GATE` 배지 |

**결측 축소 표시**: `stats == null \|\| stats.available === false` → A-1~A-4 자리에 "데이터 없음" 1줄. `stats.gate_recorded === false` → 게이트 지표를 `0`이 아니라 「미기록」으로 표기 (R-12 AC).

**`[MUST]` 색상**: `dashboard/frontend/src/index.css` `:root`: "모든 컴포넌트는 이 토큰(또는 shadcn 표준 토큰)을 경유해야 한다. hex 하드코딩 금지 — oklch() 함수 값만 사용한다." → 2계열 색은 작업 = `var(--brand-primary)`, 대기 = `var(--brand-tertiary)`, 상태 점은 `var(--status-*)` 5종. **CSS 변수 문자열 전달 패턴**(`dashboard/frontend/src/pages/dashboard/DashboardPage.tsx:202-232`)을 따르고, `PIE_COLORS`(`:246-251`)의 `oklch()` 리터럴 직기입 패턴은 따르지 않는다.

**`[MUST]` 읽기 전용**: `dashboard/frontend/src/pages/tasks/TasksPage.tsx:1-9` `@header`: "[MUST] 읽기 전용: dnd-kit sensors 비활성·🔒 badge 상시·grab 커서 미사용" → 통계 블록에 클릭 편집·정렬 토글·드래그를 추가하지 않는다. 탭 전환은 조회 동작이므로 허용된다.

**`[MUST]` 가로 스크롤 격리**: A-4 표와 산출물 탭 바(9개)는 각각 자체 `overflow-x-auto` 컨테이너 안에서만 가로 스크롤한다. Sheet 본문이 가로로 밀리지 않아야 한다 (`TASK.md` §제약 조건).

**목업 계승 / 폐기 경계** (→ D-15, PM 보강 지시)

| 계승 (시각 형태) | 폐기 (TASK.md가 이긴다 — citation-rules §9(b)) |
|-----------------|---------------------------------------|
| 2탭 구조·탭 라벨·산출물 배지 위치 (`mockup/task-kanban.html` 탭 바) | 산출물 배지 값 **5** → **9** (`.md` 전수) |
| A-1 4타일 카드 레이아웃·타이포 위계 | A-1 타일 **구성** — 목업(총 리드타임/완료 단계/캡틴 확인 대기/게이트·블로커) → R-6 AC(총 리드타임/**작업**/대기·비중/**최장 단계**) |
| A-2 3열 그리드(라벨 104px · 막대 1fr · 값 92px), 최장 단계 강조, 하단 범례+요약 문장 | A-2 **단일색 채움** → **작업·대기 2색 스택**(R-7 AC) |
| A-3 타임라인 아이템·공백 배지·담당 범례(색+라벨 동반) | — (형태 전건 계승) |
| A-4 표 7열 구성·`GATE` 배지·`overflow-x-auto` 래퍼 | A-4 **소요 단일 열** → **작업·대기 2열 분리**(R-9 AC) |

##### 화면: 산출물 탭

- **ID**: FE-2
- **유형**: detail
- **action**: modify
- **경로**: `/tasks` (Sheet 내부 탭)
- **파일**: `dashboard/frontend/src/pages/tasks/TasksPage.tsx`
- **shadcn 컴포넌트**: `Tabs`·`TabsList`·`TabsTrigger`·`TabsContent`(기존)
- **UI 작업**: 기존 산출물 `Tabs`(`:400-424`)를 「산출물」 탭 내부로 이동. 탭 항목은 `artifact_items` 유형 순 정렬, 유형 라벨을 소형 구분자로 표시. `TabsList`를 `overflow-x-auto shrink-0` 래퍼에 넣는다.
- **API 연동**: `GET /api/tasks/artifact?project=&task_id=&name=` — 기존 그대로. 변경 없음.

#### 3.4.3 환경 변경

해당 없음 — recharts 3.8.1·radix tabs 기보유, 신규 외부 의존 0건 (ANALYSIS §8 확정값). A-2는 recharts 없이 CSS grid + `width:%` 스택으로 구현 가능하며(목업 형태 계승), 이 편이 Sheet 폭 대응과 hex 금지 준수에 유리하다.

#### 3.4.4 배치/마이그레이션

해당 없음.

#### 3.4.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-030 | R-5 AC | 기능 테스트 | 상세 Sheet에 탭 2개 렌더, 기본 활성 「태스크 대시보드」, 「산출물」 탭에 배지 9 |
| TS-031 | R-5 AC | 기능 테스트 | 탭 전환 시 각 탭 본문이 자체 영역에서만 세로 스크롤, `SheetHeader` 고정 유지 |
| TS-032 | R-6 AC | 기능 테스트 | 101 상세 A-1 4타일이 `7시간 5분` / `1시간 45분` / `5시간 20분 (75%)` / `TEST-SCENARIO` |
| TS-033 | R-7 AC | 기능 테스트 | 101 상세 A-2 막대 7개, TEST-SCENARIO 최장(`4시간 55분`) 강조, 그 막대가 대기 285분·작업 10분 2색 분할 |
| TS-034 | R-8 AC | 기능 테스트 | 101 상세 A-3 시각 오름차순, TEST-SCENARIO 사용자 확인 구간 공백 `4시간 45분`, 담당 구분이 색 단독이 아니라 라벨 동반 |
| TS-035 | R-9 AC | 기능 테스트 | 101 상세 A-4 19행, 게이트 표시 4건, 소요 작업·대기 2열 분리, 표가 자체 가로 스크롤 컨테이너 안에서만 스크롤 |
| TS-036 | R-12 AC | 기능 테스트 | `stats.available=false` 응답에서 통계 블록 자리 "데이터 없음", 콘솔 에러 0건 |
| TS-037 | R-13 AC, H-8 | 보안·품질 | 신규·수정 FE 파일에서 hex 색상 리터럴 0건 |
| TS-038 | H-7, P-4 회귀 경계 3 | 회귀 테스트 | 칸반 카드 드래그 불가·🔒 badge 상시 표시 유지, 5컬럼 배치·정렬 불변 |

---

### F-005: 대시보드 화면 B-1~B-4

#### 3.5.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `dashboard/frontend/src/pages/dashboard/DashboardPage.stats.test.tsx` | FE | B-1~B-4·필터 렌더 AC 컴포넌트 테스트 | P-6 |

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `dashboard/frontend/src/pages/dashboard/DashboardPage.tsx` | FE | 로컬 타입 동기 + B-1~B-4 블록 + 워크플로우 필터 | `dashboard/frontend/src/pages/dashboard/DashboardPage.tsx:55-91`·`:436-441` |

#### 3.5.2 API·데이터 모델·화면 설계

##### 화면: 대시보드 횡단 통계

- **ID**: FE-3
- **유형**: dashboard
- **action**: modify
- **경로**: `/dashboard`
- **파일**: `dashboard/frontend/src/pages/dashboard/DashboardPage.tsx`
- **shadcn 컴포넌트**: `Card`·`CardHeader`·`CardTitle`·`CardDescription`·`CardContent`(기존), `Badge`(기존), `ToggleGroup`·`ToggleGroupItem`(기존, `:48`), `Table` 계열(기존, `:40-47`), `Skeleton`(기존)
- **UI 작업**: 기존 5블록(4메트릭·활동추이·상태 파이·알림·최근활동) **아래**에 B-1~B-4를 추가한다. 기존 블록은 손대지 않는다. 신규 하위 컴포넌트 4개(`WorkflowFilter`·`WorkflowSummaryCards`·`WorkflowStageBars`·`TaskLeadtimeChart`)를 같은 파일 내부에 정의한다.
- **API 연동**: `GET /api/dashboard?project=` — 기존 쿼리 그대로. 응답의 `workflow_stats`·`completed_tasks`·`total_tasks`·`artifact_total`을 읽는다. **필터 변경 시 API 재호출 0건** — BE가 워크플로우별로 이미 분리한 집계를 내려주므로 필터는 응답 객체에서 키를 고르는 동작이다 (ANALYSIS §8 「워크플로우 필터 상태」).

**블록별 렌더 계약**

| 블록 | 위치 | 데이터 소스 | 렌더 |
|------|------|-----------|------|
| B-4 | 최상단(필터 진입점) | `workflow_stats[].{skill, n, median_label, wait_ratio, sample_insufficient}` | `ToggleGroup` 대조표. 선택 시 B-1~B-3이 그 `skill`로 좁혀진다. `sample_insufficient` 항목에 「표본 부족」 배지 |
| B-1 | 요약 | 선택된 `WorkflowStat` + 최상위 `completed_tasks`·`total_tasks`·`artifact_total` | 5타일 — 완료 태스크(전체 병기) / 중앙값(평균 보조) / 대기 비중(누적 병기) / 게이트·블로커 / 산출물 `.md` |
| B-2 | 단계별 | `WorkflowStat.stages[]` | 가로 스택 막대. 각 막대 라벨에 `n=` 표기 (R-11 AC). `is_peak` 강조 |
| B-3 | 태스크별 | `WorkflowStat.tasks[]` | 세로 스파크 컬럼. x축 = `task_id` 앞 3자리, 높이 = `total_minutes / max`. `is_peak` 강조. 하단에 최단·최장 표기 |

**필터 상태**: `const [skill, setSkill] = useState<string>(workflow_stats[0]?.skill ?? "")` — `DashboardPage` 로컬 `useState` + 기존 `ToggleGroup` 패턴(`:184-195`·`:437`). ui-store 미사용 (ANALYSIS §8 확정값, Q5).

**결측 축소 표시**: `workflow_stats.length === 0` → B-1~B-4 자리에 "데이터 없음" 1줄. `sample_insufficient` → 중앙값 옆 「표본 부족」 배지.

**`[MUST]` 색상**: 작업 = `var(--brand-primary)`, 대기 = `var(--brand-tertiary)`, 최장 강조 = `var(--brand-secondary)`. CSS 변수 문자열 전달 패턴(`:202-232`)을 따른다. hex 리터럴 0건.

**목업 계승 / 폐기 경계** (→ D-15, PM 보강 지시)

| 계승 (시각 형태) | 폐기 (TASK.md가 이긴다) |
|-----------------|----------------------|
| B-1 5타일 카드 그리드·수치 타이포·보조 캡션 1줄 (`mockup/dashboard.html` B-1) | B-1 **혼합 중앙값 「5시간 42분」** → 워크플로우별 분리 중앙값(799/276/75분) |
| B-2 3열 그리드(라벨 108px · 막대 1fr · 값 100px)·최장 강조·하단 요약 문장 | B-2 **혼합 단계별 평균** → 워크플로우별 작업·대기 스택 + 단계별 `n=` 표기 |
| B-3 스파크 컬럼 차트·x축 3자리 ID·하단 최단/최장 표기·범례 | B-3 **진행중(`live`) 막대 2개**(`102`·`103`) → 완료 태스크만(집계기준 3) |
| B-4 카드 위치(우측 1/3 컬럼)·범례 스와치 형태 | B-4 **「스킬·모드 분포」 분포 막대** → **워크플로우 필터 진입점**(`TASK.md:122` `[결정]`) |
| 4메트릭 「현행 — 변경 없음」 | — |

> `[MUST]` EXECUTE 워커 주의: `mockup/dashboard.html`을 열면 위 「폐기」 열의 형태가 그대로 보인다. **목업은 레이아웃·정보 밀도의 시각 형태 근거로만 계승하고, 수치 정의·블록 의미는 TASK.md 재작성본을 따른다** (ANALYSIS §4(5), citation-rules §9 (b) — TO-BE 근거 서열상 소유자 결정·요구사항 문서가 설계 산출물보다 상위).

#### 3.5.3 환경 변경

해당 없음 — recharts 3.8.1 기보유. B-2·B-3은 CSS grid + `width`/`height` `%` 방식으로 구현해 목업 형태를 그대로 계승한다. recharts `BarChart` 도입은 불필요하며, 도입하지 않는 편이 hex 금지·토큰 경유 준수에 유리하다.

#### 3.5.4 배치/마이그레이션

해당 없음.

#### 3.5.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-040 | R-11 AC | 기능 테스트 | B-4 필터 선택 시 B-1~B-3이 그 워크플로우로 좁혀지고 API 재호출 0건 |
| TS-041 | R-11 AC | 기능 테스트 | opp 선택 시 「표본 부족」 배지 표시(n=4) |
| TS-042 | R-11 AC | 기능 테스트 | B-2 막대에 단계별 `n=` 표기 존재 |
| TS-043 | R-10 AC | 기능 테스트 | B-1에 완료 21 / 전체 23, 산출물 `.md` 수, 선택 워크플로우 중앙값 표시 |
| TS-044 | R-12 AC | 기능 테스트 | `workflow_stats: []` 응답에서 B 블록 "데이터 없음", 콘솔 에러 0건 |
| TS-045 | R-13 AC, H-8 | 보안·품질 | 신규·수정 FE 파일에서 hex 색상 리터럴 0건 |
| TS-046 | P-4 회귀 경계 3 | 회귀 테스트 | 기존 4메트릭·활동추이·상태 파이·알림·최근활동 렌더 불변 |

---

### F-006: 기준일 스냅샷 · 베이스라인 대조 검증

#### 3.6.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `tasks/103-260825-opd-태스크-진행통계/STATS-BASELINE.md` | 공통 | 기준일 2026-08-25 스냅샷 — 수치 + 모수 태스크 ID 목록 + 측정 명령·스코프 | `TASK.md:208-211` (R-14), ANALYSIS §8 「`STATS-BASELINE.md` 필수 기재」 |

#### 3.6.2 API·데이터 모델·화면 설계

**`STATS-BASELINE.md` 필수 구조 6절** — 값만 적는 문서가 아니라 **재현 가능한 측정 기록**으로 구성한다.

| 절 | 내용 |
|----|------|
| §1 측정 조건 | 기준일 2026-08-25, 스코프(`tasks/*/state.json` 23파일 전수 + `tasks/*/` `.md` 파일 수), 측정 명령 원문, 근거 등급 E1 |
| §2 모수 구성 태스크 ID 목록 | P-5 동결 코호트 표 — `skill`별 완료 태스크 ID 전량 열거(opd 7 / opds 10 / opp 4). **완료기준 (3) 검증은 이 목록으로 필터한 재계산과 대조한다** |
| §3 워크플로우별 수치 | 중앙값 opd 799 / opds 276 / opp 75분, 작업·대기 분해, 대기 비중 21% / 4% / 54%, 단계 수, 표본 부족 판정 |
| §4 단계별 수치 | 단계별 모수(EXECUTE n=21 · TEST n=17 · TEST-SCENARIO n=7)와 중앙값·평균 |
| §5 태스크별 수치 | 101 총 425분 = 작업 105 + 대기 320(75%), 단계별 7행 분해(TASK 24(0/24)·ANALYSIS 22(17/5)·PLAN 13(11/2)·TEST-SCENARIO 295(10/285)·EXECUTE 18(18/0)·TEST 51(47/4)·CLOSE 2(2/0)), 행 19 · 게이트 4 |
| §6 이동값 경고 | 「이 문서 작성 이후 값이 변할 수 있는 항목」 — 행 상태 분포(done 263·in_progress 1·pending 28·na 11), `owner` 분포(PM 224·auto 43·user 36), `*.user_confirm` 중 `owner=auto` 41건, `.md` 전수(192, 본 태스크 산출물 추가로 증가), 진행 중 2건(`102`·`103`). **각 값에 측정 시각을 병기한다** |

**`[MUST]` 수치 원천**: §3~§5는 ANALYSIS.md §8 「재검증 완료 수치」(E1, PM 인라인 집계로 독립 재측정)에서 옮긴다. `stats.py` 출력을 받아 적지 않는다 — 그러면 완료기준 (1)이 구현의 자기확인이 된다 (P-5 근거 3).

**`[MUST]` 화이트리스트 교집합은 92**: ANALYSIS §4(6) 표의 「91」은 워커 계수 오류다. `[PM 정정]` 행(ANALYSIS.md §8)이 92를 확정했다.

**`[MUST]` 런타임 경로 금지**: `TASK.md:211` R-14 AC: "런타임 경로에는 스냅샷 파일을 두지 않는다" → 태스크 폴더에만 둔다. `dashboard/` 하위에 스냅샷을 생성하지 않는다.

#### 3.6.3 환경 변경

해당 없음.

#### 3.6.4 배치/마이그레이션

해당 없음.

#### 3.6.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-050 | R-14 AC | 산출물 검사 | `STATS-BASELINE.md`에 §1~§6 6절 전건 존재, §2에 태스크 ID 21건 전량 열거, §1에 측정 명령·스코프 기재 |
| TS-051 | 완료기준 (1) | 통합 테스트 | 베이스라인 §5 수치와 101 상세 화면 표시값이 전건 일치 |
| TS-052 | 완료기준 (3), H-10 | 통합 테스트 | 베이스라인 §2 ID 목록으로 필터한 재계산이 799/276/75분과 일치 |
| TS-053 | R-14 AC | 산출물 검사 | `dashboard/` 하위에 스냅샷 파일 0건 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 0 | F-006 | 1 | opal-task-agent | 순차 | 코호트 동결 — 코드보다 먼저 |
| 1 | F-001, F-002 | 2, 3 | opal-be-agent | 순차 | `cache.py` 결함 수정 → `stats.py` 신설 |
| 2 | F-001~F-003 | 4 | opal-be-agent | 순차 | 스키마 확장 — 3·5·6·7의 공통 선행 |
| 3 | F-002, F-003 | 5, 6, 7 | opal-be-agent | 5→6 순차, 7 병렬 | 5·6 동일 파일(`tasks.py`) 순차, 7은 독립 파일 |
| 4 | F-001~F-003 | 8 | opal-be-agent | 순차 | BE 테스트 — 5·6·7 완료 후 |
| 5 | F-004, F-005 | 9, 10, 11 | opal-fe-agent | 9→10 순차, 11 병렬 | 9·10 동일 파일(`TasksPage.tsx`) 순차, 11은 독립 파일 |
| 6 | F-004, F-005 | 12 | opal-fe-agent | 순차 | FE 컴포넌트 테스트 — 10·11 완료 후 |
| 7 | F-006 | 13 | opal-task-agent | 순차 | 베이스라인 대조 검증 |
| 8 | — | 14 | PM 직접 | 순차 | docs/ 갱신 |

### 4.2 실행 체크리스트

> 총 **14개 Step** | Phase 9개 | 실행 모드: **복잡**
> agent 배분: `opal-be-agent` 7 (Step 2~8) · `opal-fe-agent` 4 (Step 9~12) · `opal-task-agent` 2 (Step 1, 13) · PM 직접 1 (Step 14)

---

**[PM 정합 보정 — 2026-08-25 16:36]** TEST-SCENARIO 단계와 목표-커버 게이트가 발견한 배치 불일치 2건을 반영한다. 설계 변경이 아니라 **배치·지시 보정**이므로 PLAN 워커를 재디스패치하지 않고 PM Gate 권한으로 처리했다(선례: 태스크 099 AGENTIC-LOG #13).

**(1) RED 작성 배치 — Step 8 「구현 후 일괄」은 RED-first 강제와 양립하지 않는다.**
BE 3영역(`stats.py`·`models.py`/라우터·`cache.py`)은 PM이 RED-first 강제로 분기했다. `TEST-SCENARIO.md` §3.0의 RED 실행 배치를 따른다.

| RED 배치 | 파일 | 선행 위치 | 대상 시나리오 |
|---|---|---|---|
| R1 | `dashboard/backend/tests/test_cache.py` (신규) | **Step 2 직전** | TS-016 |
| R2 | `dashboard/backend/tests/test_stats.py` (신규) | **Step 3 직전** | TS-001~009 |
| R3 | `dashboard/backend/tests/test_routers.py` (확장) | **Step 5·7 직전** | TS-010~015·018·020~023 |

- 각 RED 배치는 실패 테스트를 작성·실행해 **exit code ≠ 0을 증거로 남긴 뒤** 해당 구현 Step에 진입한다.
- **Step 8은 「BE 테스트 확장」에서 「GREEN 전건 확인 + 잔여 케이스(TS-017·024 회귀 2건) 보강」으로 축소 재정의**한다. 신규 테스트 파일 작성은 R1~R3가 이미 수행한 상태다.
- `test_cache.py` 신설이 Step 8 파일 목록에 누락돼 있었다(현행 테스트에 cache 케이스 0건 실측) — R1이 소유한다.

**(2) 픽스처 동결 — 라이브 `state.json` 직독 금지.**
`FX-103`은 본 태스크 자신의 `state.json` 스냅샷이라 파이프라인 진행에 따라 **현재 행이 계속 이동한다**(16:03 row 9 → 16:29 row 10). 실시간 픽스처를 쓰는 모든 Step(**Step 8·12·13**)은 `TEST-SCENARIO.md` §0.5가 선언한 **동결 복사본**을 사용하고 `tasks/103-*/state.json`을 직접 읽지 않는다. `FX-102`도 동일하게 동결본을 쓴다.

---

#### Step 1: `STATS-BASELINE.md` 생성 — 코호트 동결

- [ ] 완료
- **소속 기능**: F-006
- **영역**: 공통
- **agent**: opal-task-agent
- **파일**: `tasks/103-260825-opd-태스크-진행통계/STATS-BASELINE.md` (신규)
- **작업 내용**: §3.6.2의 6절 구조로 작성한다. §2에 P-5 동결 코호트(opd 7 / opds 10 / opp 4, 태스크 ID 전량)를 열거하고, §3~§5 수치는 **ANALYSIS.md §8 「재검증 완료 수치」에서 옮긴다**(`stats.py` 출력 사용 금지). §1에 측정 명령 원문과 스코프를, §6에 이동값 경고와 각 값의 측정 시각을 기재한다. 화이트리스트 교집합은 **92**를 쓴다(ANALYSIS §8 `[PM 정정]`).
- **완료 기준**: §1~§6 6절 존재, §2에 태스크 ID 21건 전량 열거, §1에 측정 명령·스코프 기재, 「91」 표기 0건, `dashboard/` 하위 스냅샷 파일 0건
- **테스트**: TS-050, TS-053
- **실행 방법**: sub-agent
- **의존**: 없음 (**최선행 — `102` 완료로 인한 모수 이동을 차단한다**)

#### Step 2: `cache.py` mtime 비교 기준 교정 (P-8)

- [ ] 완료
- **소속 기능**: F-002
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `dashboard/backend/cache.py`
- **작업 내용**: `_store` 항목을 4-tuple로 확장해 `set_wall = time.time()`을 저장하고, `get`의 mtime 비교를 `current_mtime > set_wall`로 교정한다(§3.2.2). 공개 시그니처 `get`/`set`/`invalidate`/`clear`는 무변경. `@header` 인라인 주석의 `description`·`changelog`를 갱신한다. **`TTL_SECONDS` 값·키 전략·`invalidate` 동작은 건드리지 않는다** — 이 수정 외 캐시 개선을 인접 개선 명목으로 추가하지 않는다.
- **완료 기준**: `source_path` 지정 항목이 파일 미변경 시 TTL 내 캐시 히트, 파일 `touch` 후 즉시 미스. 기존 pytest 전건 green
- **테스트**: TS-016
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 3: `stats.py` 신설 — 집계 코어

- [ ] 완료
- **소속 기능**: F-001
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `dashboard/backend/stats.py` (신규)
- **작업 내용**: §3.1.2의 공개 시그니처 7종을 구현한다. 앵커·소요 알고리즘 5단계(단조 앵커 + 음수 clamp + 파싱 실패 시 앵커 미진전), 2계열 귀속(done 행은 `owner`, 현재 행은 `key`의 `*.user_confirm` 패턴), 대표값(중앙값 주·평균 보조·`n<5` 표본 부족), 게이트/블로커 집계, `format_duration` 5규칙을 담는다. `[MUST]` import는 `datetime`·`statistics` 표준 라이브러리로 한정하고 모델·라우터·캐시를 import하지 않는다(순환 회피, R-A13). 파일 I/O 0건. `@header` 인라인 주석을 작성한다.
- **완료 기준**: TS-001~TS-009 전건 통과. `stats.py` import 목록에 `dashboard.backend` 하위 모듈 0건
- **테스트**: TS-001, TS-002, TS-003, TS-004, TS-005, TS-006, TS-007, TS-008, TS-009
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 4: `models.py` 응답 스키마 확장

- [ ] 완료
- **소속 기능**: F-001, F-002, F-003
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `dashboard/backend/models.py`
- **작업 내용**: `PipelineGate`·`TaskStats`·`ArtifactItem`·`WorkflowStat`·`StageStat`·`TaskLeadtime` 6모델을 신설한다. `PipelineRow`에 §3.2.2 표의 신규 원천 7필드(`row_id`·`key`·`item`·`timestamp`·`time_label`·`owner`·`owner_label`·`note`·`gate`) + 파생 4필드(`duration_minutes`·`duration_label`·`series`·`is_max_gap`)를 **전건 기본값 있는 additive**로 추가한다. `PipelineStageGroup`에 5필드, `TaskDetailResponse`에 `stats`·`artifact_items` 2필드, `DashboardSummaryResponse`에 5필드를 additive 추가한다. `[MUST]` 집계 기준 15 — 응답 키는 `skill`·`timestamp`·`row_id`를 쓰고 `workflow` 키를 만들지 않으며, `row`·`updated_at`은 deprecated 별칭으로 존치한다. `@header` `exports`·`description`·`changelog`를 갱신한다.
- **완료 기준**: 기존 필드 제거·타입 변경 0건. 신규 필드 전건 기본값 보유. `python3 -m pytest dashboard/backend/tests/` 전건 green
- **테스트**: TS-017, TS-024
- **실행 방법**: sub-agent
- **의존**: Step 3

#### Step 5: `tasks.py` 상세 응답 결합 + 행 매핑 교정 + 캐시 `source_path`

- [ ] 완료
- **소속 기능**: F-002
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `dashboard/backend/routers/tasks.py`
- **작업 내용**: `_group_pipeline_stages`(`:231-269`)의 행 매핑을 `row_id`·`timestamp` 원천 키로 교정하고 `row`·`updated_at`에 동일 값을 채운다. `stats.py`의 `row_durations`·`task_static_stats` 결과를 행·그룹에 결합한다. `get_task_detail`(`:381-433`)에서 `_read_state`를 캐시 조회보다 앞으로 옮기고, **정적 파생만** `cache.set(..., source_path=<task_dir>/state.json)`으로 저장한 뒤, `task_live_stats(state, now=datetime.now())`를 캐시 밖에서 계산해 응답에 합성한다. `state.json` 부재 경로(`:403-412`)는 `stats.available=false`로 200 반환한다.
- **완료 기준**: TS-010~TS-013, TS-015 전건 통과. 101 `rows[]`에서 `row` 1~19 연속·`updated_at` 빈 문자열 0건
- **테스트**: TS-010, TS-011, TS-012, TS-013, TS-015
- **실행 방법**: sub-agent
- **의존**: Step 2, Step 4

#### Step 6: `tasks.py` 산출물 화이트리스트 폐기 + 유형 분류

- [ ] 완료
- **소속 기능**: F-002
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `dashboard/backend/routers/tasks.py`
- **작업 내용**: `_get_artifact_files`(`:89-96`)의 6종 화이트리스트를 폐기하고 `.md` 전수 열거로 바꾼다. **시그니처는 유지**해 소비자 3곳(`:283`·`:304`·`:361`·`:409`·`:430`)의 호출 코드를 변경하지 않는다. `classify_artifact(name) -> tuple[str, str]`을 신설해 P-3 4유형(`pipeline`/`verification`/`log`/`other`)을 판정하고, 정렬을 `pipeline → verification → log → other` → 그룹 내 나열 순 → 파일명 오름차순으로 둔다. `get_task_detail`에 `artifact_items`를 채운다. `@header` `exports`·`description`을 갱신한다.
- **완료 기준**: 101 상세 `artifacts` 길이 9, `artifact_items` 유형 분포 pipeline 5·verification 2·log 2·other 0. 기존 pytest 전건 green
- **테스트**: TS-014, TS-017
- **실행 방법**: sub-agent
- **의존**: Step 5 (**동일 파일 순차**)

#### Step 7: `dashboard.py` 워크플로우별 집계 결합

- [ ] 완료
- **소속 기능**: F-003
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `dashboard/backend/routers/dashboard.py`
- **작업 내용**: `all_tasks` 수집 직후(`:136-138`) 각 state에 `_title = _resolve_task_title(...)`를 주입한다. `current_status == "done"`인 state만 골라 `workflow_stats(completed)`를 호출하고, 결과와 `completed_tasks`·`total_tasks`를 응답에 담는다. 산출물 규모는 `tasks.py`의 `_get_artifact_files`·`classify_artifact`를 **함수 내부 지연 import**(`:151` 선례)로 호출해 `artifact_total`·`artifact_by_type`을 채운다. 캐시는 현행 유지(`source_path` 미전달 — 다중 파일 소스). 기존 5종 산출은 손대지 않는다. `@header` `description`을 갱신한다.
- **완료 기준**: TS-020~TS-024 전건 통과. 기존 8필드 값·타입 불변
- **테스트**: TS-020, TS-021, TS-022, TS-023, TS-024
- **실행 방법**: sub-agent
- **의존**: Step 4, Step 6 (`classify_artifact` 선행)

#### Step 8: BE 테스트 확장

- [ ] 완료
- **소속 기능**: F-001, F-002, F-003
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `dashboard/backend/tests/test_stats.py` (신규), `dashboard/backend/tests/test_routers.py`
- **작업 내용**: `test_stats.py`를 신설해 TS-001~TS-009를 고정 픽스처(101 실측 행 + `086` 역행 행 + 빈/결측 케이스)와 `now` 주입으로 구현한다. `test_routers.py`에 TS-010~TS-017·TS-020~TS-024를 추가한다. `[MUST]` RED-first 규약을 지킨다(`dashboard/backend/tests/test_routers.py:6` `@header`). 기존 케이스는 수정하지 않는다 — 산출물 카운트를 assert하는 기존 케이스가 0건임을 실측 확인했으므로 갱신 대상이 없다.
- **완료 기준**: `python3 -m pytest dashboard/backend/tests/` 전건 green. 신규 케이스 전건 실행
- **테스트**: TS-001~TS-024 (BE 전량)
- **실행 방법**: sub-agent
- **의존**: Step 5, Step 6, Step 7

#### Step 9: `TasksPage.tsx` 상세 Sheet 2탭 재구성 + 타입 동기

- [ ] 완료
- **소속 기능**: F-004
- **영역**: FE
- **agent**: opal-fe-agent
- **파일**: `dashboard/frontend/src/pages/tasks/TasksPage.tsx`
- **작업 내용**: 로컬 타입 `PipelineRow`·`PipelineStageGroup`·`TaskDetail`(`:64-90`)을 Step 4 스키마와 동기하고 `TaskStats`·`ArtifactItem` 인터페이스를 추가한다. `TaskDrawer` 본문(`:384-437`)을 최상위 `Tabs` 2개(`stats`/`artifacts`, 기본 활성 `stats`)로 재구성한다. 식별 헤더는 `SheetHeader`(`:368-381`)에 고정 유지하고 기간 배지를 추가한다. 기존 `PipelineStepper`는 `stats` 탭 상단으로, 기존 산출물 뷰어는 `artifacts` 탭으로 이동한다. 산출물 탭 배지에 `artifacts.length`(101=9)를 표시하고, `TabsList`를 `overflow-x-auto shrink-0` 래퍼에 넣는다. 각 탭 본문은 자체 영역에서만 세로 스크롤한다.
- **참조 문서**: `tasks/103-260825-opd-태스크-진행통계/mockup/task-kanban.html` — **계승**: 2탭 구조·탭 라벨·배지 위치. **폐기**: 배지 값 5 → **9**(`.md` 전수). 목업의 산출물 탭 5개 목록은 화이트리스트 시절 형태이므로 그대로 구현하지 않는다.
- **완료 기준**: TS-030, TS-031 통과. `npm run build`(`tsc -b && vite build`) 성공. 칸반 읽기 전용 불변
- **테스트**: TS-030, TS-031, TS-038
- **실행 방법**: sub-agent
- **의존**: Step 5, Step 6 (**배지 9는 BE 화이트리스트 폐기 선행 필수 — FE 단독으로는 5까지만 나온다**, ANALYSIS §8 「R-5 선행 조건」)

#### Step 10: `TasksPage.tsx` A-1~A-4 블록 렌더

- [ ] 완료
- **소속 기능**: F-004
- **영역**: FE
- **agent**: opal-fe-agent
- **파일**: `dashboard/frontend/src/pages/tasks/TasksPage.tsx`
- **작업 내용**: `stats` 탭에 A-1~A-4 4블록을 §3.4.2 「블록별 렌더 계약」대로 추가한다. 하위 컴포넌트 4개(`StatsSummaryCards`·`StageStackBars`·`RowTimeline`·`RowDetailTable`)를 파일 내부에 정의한다. **전부 BE 값 직독 — FE 계산 0건**(포맷 함수·분 단위 산술·비중 계산을 작성하지 않는다). `stats.available === false` → "데이터 없음" 축소 표시, `gate_recorded === false` → 「미기록」 표기. A-4 표는 자체 `overflow-x-auto` 컨테이너에 넣는다. `[MUST]` 색상은 `var(--brand-primary)`(작업)·`var(--brand-tertiary)`(대기)·`var(--status-*)` CSS 변수 문자열 전달 패턴을 쓰고 hex 리터럴을 0건으로 유지한다. `@header` `description`·`depends`를 갱신한다.
- **참조 문서**: `mockup/task-kanban.html` — **계승**: A-2 3열 그리드(104px/1fr/92px)·최장 강조·하단 범례+요약 문장, A-3 타임라인 아이템·공백 배지·담당 범례(색+라벨 동반), A-4 7열 표·`GATE` 배지·`overflow-x-auto` 래퍼. **폐기**: A-1 타일 구성(목업 「완료 단계」·「게이트·블로커」 → R-6 AC의 「작업」·「최장 단계」), A-2 단일색 채움 → **작업·대기 2색 스택**, A-4 소요 단일 열 → **작업·대기 2열 분리**.
- **완료 기준**: TS-032~TS-037 통과. `npm run build` 성공. hex 리터럴 0건
- **테스트**: TS-032, TS-033, TS-034, TS-035, TS-036, TS-037
- **실행 방법**: sub-agent
- **의존**: Step 9 (**동일 파일 순차**)

#### Step 11: `DashboardPage.tsx` B-1~B-4 + 워크플로우 필터

- [ ] 완료
- **소속 기능**: F-005
- **영역**: FE
- **agent**: opal-fe-agent
- **파일**: `dashboard/frontend/src/pages/dashboard/DashboardPage.tsx`
- **작업 내용**: 로컬 타입 `DashboardSummary`(`:83-91`)를 Step 4 스키마와 동기하고 `WorkflowStat`·`StageStat`·`TaskLeadtime` 인터페이스를 추가한다. 기존 5블록 **아래**에 B-4(필터)·B-1·B-2·B-3을 §3.5.2 「블록별 렌더 계약」대로 추가한다. 필터는 `useState` + 기존 `ToggleGroup` 패턴(`:184-195`)을 쓰고 ui-store를 쓰지 않으며 **API를 재호출하지 않는다**. 하위 컴포넌트 4개(`WorkflowFilter`·`WorkflowSummaryCards`·`WorkflowStageBars`·`TaskLeadtimeChart`)를 파일 내부에 정의한다. `[MUST]` 색상은 CSS 변수 문자열 전달 패턴(`:202-232`)을 쓴다 — 기존 `PIE_COLORS`(`:246-251`)의 `oklch()` 리터럴 직기입 패턴을 따르지 않으며, **기존 `PIE_COLORS`는 수정하지 않는다**(인접 개선 금지). `@header` `description`·`depends`를 갱신한다.
- **참조 문서**: `mockup/dashboard.html` — **계승**: B-1 5타일 그리드·수치 타이포, B-2 3열 그리드(108px/1fr/100px)·최장 강조·요약 문장, B-3 스파크 컬럼·x축 3자리 ID·최단/최장 표기·범례, B-4 카드 위치. **폐기**: B-1 혼합 중앙값 「5시간 42분」 → 워크플로우별 분리, B-2 혼합 단계별 평균 → 워크플로우별 2계열 스택 + `n=` 표기, B-3 진행중(`live`) 막대 2개 → 완료 태스크만, B-4 「스킬·모드 분포」 → **워크플로우 필터 진입점**.
- **완료 기준**: TS-040~TS-046 통과. `npm run build` 성공. hex 리터럴 0건. 기존 5블록 렌더 불변
- **테스트**: TS-040, TS-041, TS-042, TS-043, TS-044, TS-045, TS-046
- **실행 방법**: sub-agent
- **의존**: Step 7

#### Step 12: FE 컴포넌트 테스트 신설 (P-6)

- [ ] 완료
- **소속 기능**: F-004, F-005
- **영역**: FE
- **agent**: opal-fe-agent
- **파일**: `dashboard/frontend/src/pages/tasks/TasksPage.stats.test.tsx` (신규), `dashboard/frontend/src/pages/dashboard/DashboardPage.stats.test.tsx` (신규)
- **작업 내용**: P-6 「범위 한정」 6항만 검증한다. `apiClient`를 `vi.mock`으로 대체해 101 고정 응답을 주입하는 선례 패턴(`dashboard/frontend/src/pages/brain/brain-navigation-guard.test.tsx:31-39`)을 따르고, `QueryClientProvider`로 감싼다. **스냅샷 테스트·픽셀 비교·전체 트리 검증을 작성하지 않는다.** `@header` 인라인 주석에 `scenarios` 키로 TS-ID를 기재한다.
- **완료 기준**: `npm run test` 전건 green (기존 7파일 + 신규 2파일). TS-030·TS-032·TS-033·TS-035·TS-036·TS-040·TS-041 커버
- **테스트**: TS-030, TS-032, TS-033, TS-035, TS-036, TS-040, TS-041
- **실행 방법**: sub-agent
- **의존**: Step 10, Step 11

#### Step 13: 베이스라인 대조 검증

- [ ] 완료
- **소속 기능**: F-006
- **영역**: 공통
- **agent**: opal-task-agent
- **파일**: `tasks/103-260825-opd-태스크-진행통계/STATS-BASELINE.md` (대조 결과 §7 추가)
- **작업 내용**: 배포본 콘솔(127.0.0.1:7823)을 기동해 `GET /api/tasks/detail?task_id=101...`·`GET /api/dashboard?project=...` 실응답을 받고, `STATS-BASELINE.md` §2 동결 코호트로 필터한 값과 §3~§5 수치를 대조한다. 완료기준 (1)(2)(3)의 전건 일치를 확인하고 결과를 §7 대조 기록으로 추가한다. `102`가 그사이 완료됐더라도 **코호트 목록으로 필터해 비교**한다(P-5). L3 시각 확인은 playwright로 병행하되 AC 판정은 vitest·pytest 결과로 한다.
- **완료 기준**: TS-051, TS-052 통과. 완료기준 (1)(2)(3) 전건 일치 기록
- **테스트**: TS-051, TS-052
- **실행 방법**: sub-agent
- **의존**: Step 8, Step 10, Step 11, Step 12

#### Step 14: docs/ 갱신

- [ ] 완료
- **소속 기능**: —
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/ARCHITECTURE.md`
- **작업 내용**: §OPAL Console(`docs/ARCHITECTURE.md:254`)에 `stats.py` 집계 정의 SSOT 순수 모듈 신설과 "파생은 BE 단일 소스 — 집계 정의는 라우터가 아닌 순수 모듈이 소유" 규약을 반영한다. `dashboard/` 구조 트리(`docs/ARCHITECTURE.md:454`)에 `stats.py`를 추가하고 변경이력 표에 태스크 번호 `(103)`을 포함한 행을 추가한다. **`docs/CONVENTIONS.md`·`docs/PROJECT.md`는 갱신 대상이 아니다** — 새 컨벤션·새 스킬/에이전트가 도입되지 않았다.
- **완료 기준**: `docs/ARCHITECTURE.md` §OPAL Console·구조 트리·변경이력 3곳 갱신
- **테스트**: 산출물 검사 — 갱신 3곳 존재
- **실행 방법**: direct
- **의존**: Step 13

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 → 전 Step | 코호트 동결이 코드보다 선행해야 `102` 완료로 인한 모수 이동을 차단한다 (P-5) |
| Step 2 → Step 5 | `source_path` 전달이 캐시 무력화로 이어지지 않으려면 시계 교정이 선행이다 (P-8) |
| Step 3 → Step 4 | 스키마 필드가 `stats.py` 반환 키에서 도출된다 |
| Step 4 → Step 5·6·7 | 세 라우터 Step 모두 확장된 응답 모델을 참조한다 |
| Step 5 → Step 6 | 동일 파일(`tasks.py`) 순차 수정 — 파일 충돌 방지 |
| Step 6 → Step 7 | `dashboard.py`가 `classify_artifact`를 지연 import한다 |
| Step 5·6 → Step 9 | **산출물 배지 101=9는 BE 화이트리스트 폐기 선행 필수** — FE 단독 달성 불가 (ANALYSIS §8) |
| Step 9 → Step 10 | 동일 파일(`TasksPage.tsx`) 순차 수정 — 탭 골격이 있어야 블록을 붙인다 |
| Step 7 ∥ Step 5·6 | 독립 파일(`dashboard.py` vs `tasks.py`) — 단 Step 6의 `classify_artifact`에 의존하므로 실제로는 Step 6 후행 |
| Step 11 ∥ Step 9·10 | 독립 파일(`DashboardPage.tsx` vs `TasksPage.tsx`), 독립 기능(F-005 vs F-004) |
| Step 10·11 → Step 12 | 테스트 대상 컴포넌트가 존재해야 한다 |
| Step 8·12 → Step 13 | 대조 검증은 BE·FE 양쪽 완료 후에만 의미가 있다 |
| Step 13 → Step 14 | docs 갱신은 구현 확정 후 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | 앵커·소요·2계열 계산 정확성 | TS-001, TS-002 | 101 총 425 = 105 + 320(75%), 단계별 7행 전건 일치 |
| F-001 | 음수 clamp·단조 앵커 | TS-003 | `086` 소요 0, 음수 0건, 총합 항등 보존 |
| F-001 | 결측 내성 3경로 | TS-004 | 빈 rows·`created_at` 결측·형식 오류에서 예외 0건 |
| F-001 | 실시간 파생 결정론 | TS-005, TS-006 | 고정 `now` 주입 시 assert 가능, 완료 태스크는 `now` 무관 |
| F-001 | 워크플로우별 집계 | TS-007 | 중앙값 799/276/75, 대기 비중 21/4/54, opp 표본 부족 |
| F-001 | 순수 모듈 경계 | TS-008 | `dashboard.backend` 하위 import 0건 |
| F-001 | 표시 문자열 포맷 | TS-009 | `format_duration` 5규칙 전건 일치 |
| F-002 | `PipelineRow` 확장 계약 | TS-010 | 5키 보유, 게이트 4건, `gate` 객체 직렬화(불리언 아님) |
| F-002 | 사표 필드 교정 | TS-011 | 101 `row` 1~19 연속, `updated_at` 빈 문자열 0건 |
| F-002 | 상세 소요 파생 응답 | TS-012 | `stats` 값이 TS-001·TS-002와 동일 |
| F-002 | 실시간 파생 응답 | TS-013 | 103 현재 행 식별·`key` 패턴 귀속, 101 425 고정 |
| F-002 | 산출물 전수 + 유형 분류 | TS-014 | 101 `artifacts` 9, 유형 분포 5/2/2/0 |
| F-002 | 결측 태스크 200 응답 | TS-015 | `state.json` 부재 태스크에서 `available=false`, 「미기록」 표기 |
| F-002 | 캐시 mtime 무효화 | TS-016 | 미변경 히트, `touch` 후 미스 |
| F-003 | 대시보드 모수 | TS-020 | 완료 21 / 전체 23 |
| F-003 | 워크플로우별 응답 | TS-021 | 3건, 중앙값·대기 비중 일치 |
| F-003 | 산출물 규모 | TS-022 | `artifact_total` = 유형별 합계 |
| F-003 | 용어 일관성 | TS-023 | 응답 JSON에 `workflow` 키 0건 |
| F-004 | 2탭 분리 + 배지 | TS-030, TS-031 | 탭 2개·기본 활성 「태스크 대시보드」·배지 9·각 탭 자체 스크롤 |
| F-004 | A-1 4타일 | TS-032 | 4타일 문자열 전건 일치 |
| F-004 | A-2 스택 막대 | TS-033 | 7막대·최장 강조·2색 분할(285/10) |
| F-004 | A-3 타임라인 | TS-034 | 오름차순·공백 `4시간 45분`·라벨 동반 |
| F-004 | A-4 상세 표 | TS-035 | 19행·게이트 4·2열 분리·가로 스크롤 격리 |
| F-004 | 결측 축소 표시 | TS-036 | "데이터 없음" + 콘솔 에러 0건 |
| F-005 | B-4 필터 연동 | TS-040 | 필터 선택 시 B-1~B-3 좁혀짐·API 재호출 0건 |
| F-005 | 표본 부족 배지 | TS-041 | opp 선택 시 배지 표시 |
| F-005 | B-2 모수 표기 | TS-042 | 단계별 `n=` 표기 존재 |
| F-005 | B-1 요약 | TS-043 | 완료 21/전체 23·산출물 수·중앙값 표시 |
| F-005 | 결측 축소 표시 | TS-044 | 빈 `workflow_stats`에서 "데이터 없음" + 콘솔 에러 0건 |
| F-006 | 베이스라인 구조 | TS-050, TS-053 | 6절 존재·ID 21건 열거·런타임 경로 스냅샷 0건 |
| F-006 | 대조 검증 | TS-051, TS-052 | 완료기준 (1)(2)(3) 전건 일치 |

### 5.2 회귀 테스트

> 판정 기준은 P-4 「회귀 경계 선언」 4항을 따른다.

- [ ] 스키마 회귀 0 — 기존 응답 필드 제거·타입 변경·의미 변경 0건 (TS-017, TS-024)
- [ ] BE 테스트 회귀 0 — `python3 -m pytest dashboard/backend/tests/` 전건 green
- [ ] FE 테스트 회귀 0 — `npm run test` 기존 7파일 전건 green
- [ ] 빌드 회귀 0 — `npm run build`(`tsc -b && vite build`) 성공
- [ ] 칸반 화면 회귀 0 — 5컬럼 배치·정렬 불변, 읽기 전용 불변(드래그 불가·🔒 상시) (TS-038)
- [ ] 대시보드 화면 회귀 0 — 기존 4메트릭·활동추이·상태 파이·알림·최근활동 불변 (TS-046)
- [ ] **예외 확인** — `artifact_count`·`artifacts[]` 값 증가(101: 5→9)는 회귀가 아니다. 기존 테스트에 이 값을 assert하는 케이스 0건임을 재확인

### 5.3 코드/문서 품질

- [ ] `@header` — 신규·수정 코드 파일 전건에 인라인 주석 `@header` 블록 작성·갱신 (`[MUST]` `docs/CONVENTIONS.md` §@header 규칙, `.opal/code-scan.json` `headerSource: "inline"`)
- [ ] 네이밍 — Python 파일 snake_case(`stats.py`), 코드·변수·필드명 English (`docs/CONVENTIONS.md` §언어 규칙)
- [ ] 플랫폼 분기 격리 — 신규 코드에 플랫폼 조건문 0건 (`[MUST]` `docs/CONVENTIONS.md` §플랫폼 분기 격리)
- [ ] 배포 경계 — `~/.opal/` 직접 편집 0건, 변경은 프로젝트 소스에서만 (`[MUST]` `docs/CONVENTIONS.md` §배포 경계)
- [ ] State 관리 — `state.json` 직접 편집 0건, 본 태스크는 조회만 수행 (`[MUST]` `docs/CONVENTIONS.md` §State 관리)
- [ ] 사변적 추가 0건 — PLAN에 명시된 파일만 변경, 인접 코드 개선 명목 수정 0건 (`coding-principles.md` §4). 특히 `PIE_COLORS`·`tasks.py` 제목 폴백·TTL 값은 건드리지 않는다
- [ ] 불가능 시나리오 방어 분기 0건 (`coding-principles.md` §3)
- [ ] `docs/ARCHITECTURE.md` 변경이력 행 추가 (버전·KST 일시·태스크 번호 `(103)`)

### 5.4 보안

- [ ] 신규 코드에 하드코딩된 토큰·시크릿 0건
- [ ] 신규 쓰기 엔드포인트 0건 — GET 경로만 변경, 읽기 전용 원칙의 예외를 늘리지 않는다 (`docs/ARCHITECTURE.md` §OPAL Console)
- [ ] 경로 조작 — `artifacts` 전수화로 노출 파일이 늘어나므로 `GET /api/tasks/artifact`의 `name` 파라미터가 태스크 폴더 밖(`../`)을 읽지 않는지 확인
- [ ] `.env`·인증 파일이 `.gitignore`에 포함되어 있는지 확인
- [ ] 응답에 `note` 원문이 그대로 실리므로 마크다운 렌더 경로에서 XSS 방어가 기존 `MarkdownView` 수준으로 유지되는지 확인

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 14개 | 복잡 |
| 변경 파일 수 | 10개 (신규 5 · 수정 5) | 복잡 |
| 모듈 범위 | 다중 (BE 라우터·스키마·유틸 + FE 페이지 2 + 테스트 3 + 문서 2) | 복잡 |
| 작업 유형 | 대규모 개선 (신규 모듈 + 화면 8블록) | 복잡 |
| 외부 의존성 | 없음 (recharts 3.8.1·radix tabs 기보유) | 단순 |
| **실행 모드** | **복잡** | 하나라도 복잡 기준 해당 시 복잡 모드 |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

**그룹핑 원칙**: 동일 파일을 수정하는 Step은 반드시 같은 에이전트에 배치한다 (파일 충돌 방지).

| 에이전트 | Step | 소유 파일 |
|---------|------|----------|
| A (`opal-task-agent`) | 1 | `STATS-BASELINE.md` |
| B (`opal-be-agent`) | 2, 3, 4 | `cache.py`, `stats.py`, `models.py` |
| C (`opal-be-agent`) | 5, 6 | `routers/tasks.py` (동일 파일 — 단일 에이전트 필수) |
| D (`opal-be-agent`) | 7 | `routers/dashboard.py` |
| E (`opal-be-agent`) | 8 | `tests/test_stats.py`, `tests/test_routers.py` |
| F (`opal-fe-agent`) | 9, 10 | `TasksPage.tsx` (동일 파일 — 단일 에이전트 필수) |
| G (`opal-fe-agent`) | 11 | `DashboardPage.tsx` |
| H (`opal-fe-agent`) | 12 | `*.stats.test.tsx` 2파일 |
| I (`opal-task-agent`) | 13 | `STATS-BASELINE.md` §7 |
| J (PM 직접) | 14 | `docs/ARCHITECTURE.md` |

**DAG**

```
A ─→ B ─→ C ─→ D ─→ E ─┐
          │              ├─→ I ─→ J
          └─→ F ─┐       │
      D ─→ G ────┴─→ H ──┘
```

**배치 실행 순서**

| Batch | 에이전트 | 병렬 여부 |
|-------|---------|----------|
| 1 | A | 단독 |
| 2 | B | 단독 |
| 3 | C | 단독 |
| 4 | D | 단독 (C의 `classify_artifact` 의존) |
| 5 | E, F, G | **3병렬** (E=BE 테스트 · F=TasksPage · G=DashboardPage, 파일 교집합 0) |
| 6 | H | 단독 |
| 7 | I | 단독 |
| 8 | J | 단독 |

### C-2. 스킬 요구사항

| 요구 | 기존 스킬 매칭 | 갭 판별 |
|------|--------------|--------|
| BE 구현 (FastAPI·Pydantic·pytest) | `opal-be-agent` + `op-dev-execute` | 갭 없음 |
| FE 구현 (React·TS·Vitest·shadcn) | `opal-fe-agent` + `op-dev-execute` | 갭 없음 |
| 테스트 시나리오 | `op-dev-test-scenario` (PM이 STEP 3.5에서 작성) | 갭 없음 |
| 동적 검증 | `opal-test-agent` (BE/FE/E2E 3모드) | 갭 없음 |
| 산출물 문서 | `opal-task-agent` | 갭 없음 |

**신규 스킬 후보 0건** — 반복 패턴이 3개 Step 이상에서 발생하지 않는다. "BE 값 직독·FE 무계산" 규약은 인라인 지침(Step 10·11 작업 내용)으로 충분하다.

### C-3. 도구 요구사항

| 도구 | 용도 | 설치 필요 |
|------|------|----------|
| pytest | BE 단위·통합 테스트 | 기보유 |
| vitest + happy-dom + Testing Library | FE 컴포넌트 테스트 | 기보유 (`dashboard/frontend/vitest.config.ts`) |
| playwright MCP | L3 시각 확인 (배포본 7823 실데이터) | 기보유 — **AC 판정 주체 아님**(P-6) |
| shadcn MCP | `Tabs`·`Table`·`ToggleGroup` 사용례 확인 | 기보유 — 신규 컴포넌트 추가 시에만 |
| context7 / WebSearch | — | **불필요**, 신규 외부 의존 0건 (ANALYSIS §2.1) |

### C-4. 테스트 전략

**실행 명령**

```bash
python3 -m pytest dashboard/backend/tests/
cd /Volumes/Data/AIStudio/workspace/ai-framework/dashboard/frontend && npm run test && npm run build
```

| 계층 | 대상 | 모드 | 게이트 |
|------|------|------|-------|
| L1 단위 | `stats.py` 9케이스 (고정 픽스처 + `now` 주입) | BE | TS-001~TS-009 전건 green |
| L1 컴포넌트 | A/B 렌더 AC 6항 (`apiClient` mock) | FE | TS-030·032·033·035·036·040·041 green |
| L2 통합 | 실 `state.json` 23파일 기반 라우터 응답 | BE | TS-010~TS-024 전건 green |
| L2 회귀 | 기존 pytest 11파일 + 기존 vitest 7파일 | BE+FE | 전건 green |
| L3 시각 | 배포본 7823 실데이터 A/B 블록 (playwright) | E2E | 8블록 렌더 확인 — 보조 증거 |
| L3 대조 | `STATS-BASELINE.md` §2 코호트 필터 재계산 | 통합 | 완료기준 (1)(2)(3) 전건 일치 |

**RED-first 규약**: `dashboard/backend/tests/test_routers.py:6` `@header`가 RED-first를 명시하므로, Step 8·12의 신규 케이스는 구현 전 실패를 확인한 뒤 green으로 전환한다.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| BE 프레임워크 | FastAPI + uvicorn (127.0.0.1:7823) | `opal-be-agent` |
| BE 스키마 | Pydantic v2 `BaseModel` (`dashboard/backend/models.py:44`) | `opal-be-agent` |
| BE 테스트 | pytest + httpx TestClient | `opal-test-agent` (BE 모드) |
| BE 표준 라이브러리 | `datetime` · `statistics` (`stats.py` 전용 의존) | — |
| FE 프레임워크 | React ^19.2.6 | `opal-fe-agent` |
| FE 언어/빌드 | TypeScript ~6.0.2 / Vite ^8.0.12 (`npm run build` = `tsc -b && vite build`) | `opal-fe-agent` |
| FE 상태 | TanStack Query ^5.101.0 · Zustand ^5.0.14 | `opal-fe-agent` |
| FE UI | Tailwind ^4.3.1 · shadcn ^4.11.0 · Radix 12종 | `opal-fe-agent` |
| FE 차트 | recharts ^3.8.1 (기보유 — 본 태스크는 CSS grid 방식 채택) | `opal-fe-agent` |
| FE 테스트 | Vitest ^4.1.9 + happy-dom ^20.10.6 + Testing Library | `opal-test-agent` (FE 모드) |
| 원천 데이터 | `tasks/*/state.json` schema_version 1.0/1.1, `timestamp` 포맷 `%Y-%m-%d %H:%M` | — |

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| context7 | **미사용** — 신규 외부 의존 0건이라 최신 API 문서 조회가 불필요하다 (ANALYSIS §2.1) |
| shadcn | **미사용** — `Tabs`·`Table`·`ToggleGroup` 3종 모두 `dashboard/frontend/src/components/ui/`에 기설치돼 있고 프로젝트 내 사용례가 있다 |
| playwright | **EXECUTE/TEST 단계 예정** — L3 시각 확인용, AC 판정 주체 아님 |

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 기획 | TASK.md (103) | `tasks/103-260825-opd-태스크-진행통계/TASK.md` | 확정 입력·집계 기준 15항목·R-1~R-14 원천 |
| D-2 | 기획 | ANALYSIS.md (103) | `tasks/103-260825-opd-태스크-진행통계/ANALYSIS.md` | §1.1 파일 맵·§8 확정값 24행 승계 원천 |
| D-3 | 설계 | 시스템 아키텍처 | `docs/ARCHITECTURE.md` §OPAL Console | 읽기 전용 원칙·쓰기 예외 2건 경계 — Step 14 갱신 대상 |
| D-4 | 설계 | 코드 및 문서 컨벤션 | `docs/CONVENTIONS.md` §구현 규칙 | @header·Citation·State·배포 경계·플랫폼 분기 격리 |
| D-5 | 소스 | 태스크 라우터 | `dashboard/backend/routers/tasks.py` | 상세 응답 생성부 — Step 5·6 대상 |
| D-6 | 소스 | 응답 모델 | `dashboard/backend/models.py` | `PipelineRow`·`PipelineStageGroup`·`DashboardSummaryResponse` — Step 4 대상 |
| D-7 | 소스 | 대시보드 라우터 | `dashboard/backend/routers/dashboard.py` | 기존 집계 경로·지연 import 선례 — Step 7 대상 |
| D-8 | 소스 | TTL 캐시 | `dashboard/backend/cache.py` | 30초 TTL + mtime 무효화 계약 — P-8 근거·Step 2 대상 |
| D-9 | 소스 | 태스크 칸반 화면 | `dashboard/frontend/src/pages/tasks/TasksPage.tsx` | 상세 Sheet·읽기 전용 `@header` — Step 9·10 대상 |
| D-10 | 소스 | 대시보드 화면 | `dashboard/frontend/src/pages/dashboard/DashboardPage.tsx` | 기존 차트·`ToggleGroup` 필터·CSS 변수 전달 패턴 — Step 11 대상 |
| D-11 | 소스 | 전역 디자인 토큰 | `dashboard/frontend/src/index.css` | 시그니처 3색·상태색 5종·hex 금지 — R-13 근거 |
| D-12 | 소스 | 라우터 계약 테스트 | `dashboard/backend/tests/test_routers.py` | 회귀 판정 근거·RED-first 규약 |
| D-13 | 소스 | FE 컴포넌트 테스트 선례 | `dashboard/frontend/src/pages/brain/brain-navigation-guard.test.tsx` | `apiClient` mock + `QueryClientProvider` 패턴 — Step 12 근거 |
| D-14 | 설계 | state.json 스키마 | `~/.opal/tools/state-tool/schema/state.schema.json` | `gate`·`owner`·`status`·`timestamp` 도메인 — 직렬화 모델 근거 |
| D-15 | 기획 | 승인 목업 3화면 | `tasks/103-260825-opd-태스크-진행통계/mockup/` (`index.html`·`task-kanban.html`·`dashboard.html`) | A-1~A-4·B-1~B-4 **시각 형태** 근거 — 수치 정의·블록 의미는 폐기(§3.4.2·§3.5.2 경계표) |
| D-16 | 설계 | DONE.md (021) | `tasks/backup/021-260615-opd-opal-console/DONE.md` | Console 신설 결정·Sheet 통일 규격·배포 스크립트 경로 |
| D-17 | 설계 | DONE.md (023) | `tasks/backup/023-260616-opd-kanban-stage-pipeline-ux/DONE.md` §3 | "단계 파생은 BE 단일 소스 — FE는 표시만" 선례 — P-7 근거 |
| D-18 | 설계 | 인용 규칙 | `~/.opal/references/harness/citation-rules.md` §9 | 근거 등급 E1~E5·TO-BE 관할 2축 — 목업 폐기 판정 근거 |
| D-19 | 설계 | 코딩 원칙 | `~/.opal/references/harness/coding-principles.md` §2·§3·§4 | 사변적 추가·인접 개선·불가능 시나리오 방어 금지 |

**[MUST] 인용 (재해석 금지)**

- `[MUST]` `dashboard/frontend/src/pages/tasks/TasksPage.tsx:1-9` `@header`: "[MUST] 읽기 전용: dnd-kit sensors 비활성·🔒 badge 상시·grab 커서 미사용"
- `[MUST]` `dashboard/frontend/src/index.css` `:root`: "모든 컴포넌트는 이 토큰(또는 shadcn 표준 토큰)을 경유해야 한다. hex 하드코딩 금지 — oklch() 함수 값만 사용한다."
- `[MUST]` `docs/CONVENTIONS.md` §State 관리: "파이프라인 행 상태(⬜/🔄/✅) 변경은 `~/.opal/tools/state-tool/run.sh`로만 수행한다. `state.json` 직접 편집 금지 — 현황 조회는 `state-tool show <task-path>`로 한다."
- `[MUST]` `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `scripts/`)에서 수행한다."
- `[MUST]` `docs/CONVENTIONS.md` §플랫폼 분기 격리: "스킬·에이전트 본문에 플랫폼 조건문을 추가하지 않는다"
- `[MUST]` `docs/CONVENTIONS.md` §@header 규칙: "코드 파일을 생성·수정할 때 파일 상단에 @header 블록을 작성한다" — 본 프로젝트는 `.opal/code-scan.json` `headerSource: "inline"`이므로 **인라인 주석**에 기록한다
- `[MUST]` `docs/CONVENTIONS.md` §언어 규칙: "코드/변수/필드명 English" · "파일/폴더 이름 English, kebab-case (Python 파일은 snake_case)"
- `[MUST]` `docs/CONVENTIONS.md` §변경이력 작성 의무: "일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함"
- `[MUST]` `TASK.md:111` 집계 기준 15: "응답 키는 `state.json` 스키마 용어(`skill`·`timestamp`·`row_id`)를 쓴다. 사표 필드 `updated_at`·`row`는 deprecated 별칭으로 존치하되 값을 채운다."
- `[MUST]` `TASK.md:222` §제약 조건: "기존 캐시 경로(`dashboard/backend/cache.py`)를 그대로 사용하고 무캐시 전수 스캔을 추가하지 않는다."
- `[MUST]` `TASK.md:223` §제약 조건: "실시간 파생값은 렌더 시각에 따라 변하므로 완료기준 수치 AC는 완료 태스크로만 잡는다. 진행 중 태스크의 AC는 값이 아니라 동작으로 기술한다."
- `[MUST]` `TASK.md:211` R-14 AC: "런타임 경로에는 스냅샷 파일을 두지 않는다."

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| 1 | 음수 소요로 스택 막대 파손 (H-1, R-A1) | F-001 | High | 0 clamp + 단조 앵커 — `stats.py` 단일 지점. TS-003으로 고정 |
| 2 | 사표 필드가 A-3·A-4를 전건 공백으로 만듦 (H-2, R-A2) | F-002 | High | `_group_pipeline_stages` 행 매핑을 `row_id`·`timestamp`로 교정 + 별칭에 동일 값 주입. TS-011로 고정 |
| 3 | 산출물 카운트 동반 변동이 회귀로 오판 (H-4, R-A3) | F-002 | High | P-4 회귀 경계 4항 선언 + 기존 테스트 assert 0건 실측 확인 |
| 4 | 완료기준 (3) 모수 이동 (H-10, R-A4) | F-006 | High | P-5 코호트 동결 + Step 1 최선행 배치 |
| 5 | **`cache.py` 시계 혼용으로 캐시 무력화 (H-9, P-8 신규 발견)** | F-002 | High | Step 2에서 wall-clock 비교로 최소 교정. TS-016으로 고정. 범위를 그 한 줄로 고정 |
| 6 | 실시간 파생 캐시 정지 (H-6, R-A5) | F-002 | Medium | 정적/실시간 함수 분리 + 실시간은 캐시 밖 조립. `now` 주입으로 테스트 결정론 확보 |
| 7 | 목업↔요구사항 충돌로 폐기 블록 구현 (H-11, R-A9) | F-004, F-005 | Medium | **Step 9·10·11 본문에 계승/폐기 경계표를 명시**하고 `mockup/` 경로를 참조 문서로 기재. §3.4.2·§3.5.2에 경계표 2개 배치 |
| 8 | FE 렌더 AC를 잡을 테스트 기반 부재 (R-A10) | F-004, F-005 | Medium | P-6 채택 — 신규 2파일, 범위 6항 한정. 스냅샷 테스트 금지 |
| 9 | `in_progress` 행이 소요에 섞임 (R-A11) | F-001 | Medium | `status == "done"`만 합산 + 비done 행 앵커 미진전. ANALYSIS §8 열거 보정 승계 |
| 10 | hex 하드코딩 유입 (H-8, R-A14) | F-004, F-005 | Low | CSS 변수 문자열 전달 패턴 강제 + TS-037·TS-045 정적 검사. 기존 `PIE_COLORS`는 인접 개선 금지 |
| 11 | 순환 import (H-5, R-A13) | F-001 | Low | `stats.py` 표준 라이브러리 전용 + 지연 import 선례 유지. TS-008로 고정 |
| 12 | 게이트 지표 모수 편중 (R-A12) | F-002, F-004 | Low | `gate_recorded=false`를 태스크 단위로 내려 「미기록」 표기. 0과 구분 |
| 13 | 산출물 탭 9개가 Sheet 폭 초과 (H-12) | F-004 | Low | `TabsList`를 `overflow-x-auto` 래퍼에 격리. TS-035와 함께 확인 |
| 14 | 노출 파일 확대에 따른 경로 조작 표면 증가 | F-002 | Low | `GET /api/tasks/artifact`의 `name` 파라미터 경로 이탈 방어 확인 (§5.4) |

---

## 부록 — PLAN 품질 자체 검증

- **커버리지**: R-1~R-14 전건이 F-001~F-006에 매핑됐다(§1.2). 완료기준 (1)~(7) 전건이 TS 또는 §5.2 회귀 항목에 대응한다.
- **승계 규율**: ANALYSIS §1.1 파일 맵 11행·§8 확정값 24행을 재조사 없이 승계했다. 승계값을 뒤집은 항목은 `cache.py` 변경 유형 1건뿐이며 E1 실측 근거와 함께 §확정 입력 판정에 명시했다.
- **미결 소비**: ANALYSIS 「PLAN 결정 필요」 7건 중 P-1·P-2는 캡틴 확정 승계, P-3~P-7은 권고안 1개 + 근거로 확정했다. 신규 발견 P-8을 추가했다.
- **근거 표기**: 모든 설계 판단에 `경로:줄번호` 또는 `(→ D-N)` 인용을 부착했다. 새로 도입한 사실 주장 4건(P-3 파일명 분포 · P-4 테스트 assert 0건 · P-5 코호트 · P-8 시계 혼용)은 전부 E1이며 스코프와 실행 명령을 병기했다.
- **소스코드 원문 블록 0건** — 코드펜스 7개는 ASCII 그래프 2개(의존 그래프·에이전트 DAG)·함수 시그니처 3개·엔드포인트 계약 1개·실행 명령 1개로 한정된다 (citation-rules §2.2).
- **`decision_required`**: ANALYSIS가 에스컬레이션한 `terminology_mismatch` 3건(R-A6·R-A7·R-A8)은 캡틴의 집계 기준 15 확정으로 전건 해소됐다. 본 PLAN에서 신규 발생한 `terminology_mismatch` 0건.
