# DONE: @header 자산 스킬 신설 + 하네스 갱신·소비 절차 편입

> 완료일: 2026-09-05 00:15 (KST) | 스킬: `//opd --agentic` | 태스크: 106
> 워커 소요 합계: **147분** (ANALYSIS 6 / PLAN 19 / EXECUTE 69 / TEST 53)
> 판정: **완료** — 19 Step 전건, `pytest 383 passed / 0 failed`, 회귀 0건

## 1. 무엇을 했는가

`@header` 자산의 **생성–갱신–소비 3국면**을 완결했다.

| 국면 | 산출 | 집행 형태 |
|------|------|----------|
| **생성** | `opal-code-map-builder`(`opcmb`) 스킬 신설 — `init`\|`update` 2모드, 자산 존재 감지 판별 | 스킬(하네스 밖) |
| **갱신** | `header-rules.md` §갱신 시점 **(3단)→(4단)** — (d) L2 경량 트랙 완료 시점 신설 | 하네스 규정 + 기존 `validate --changed` 재사용 |
| **소비** | `opal-pm.md` §13 2단 소비 절차(1차 code-scan → 2차 grep) + **PM 자기판정 → 도구 판정 승격** | `state-tool verify --code-scan-citation-check` + EXECUTE 첫 행 자동 훅 |

## 2. 변경 산출물

**신규 1**: `opal/skills/opal-code-map-builder/SKILL.md` (268행)
**수정 15** (`+645/-61`):

| 파일 | 변경 |
|------|------|
| `opal/core/references/opal-skills-registry.json` | `opcmb` 등재 · `version` 3.14.0 · alias 30종 |
| `docs/CONVENTIONS.md` | 약어 표 `opcmb` + **결손 2건 보정**(`opgr`·`opeli5`) · 총계 27→30종 |
| `opal/core/references/harness/header-rules.md` | §갱신 시점 (4단) + (d) 행 + 폴백 3종 + **모드별 차단 사유 2종** |
| `opal/core/references/opal-pm.md` | §12 「유지」 5행 + 축 구분 각주 / §13 2단 소비 표 |
| `opal/core/references/pm/dispatch-process.md` | 2차 전환 포인터 1건(원문 복제 0건) |
| `opal/core/references/harness/pm-review-gate.md` | 항목 14 집행 승격 — 자기판정 문면 **0건** |
| `opal/tools/state-tool/state_tool.py` | 인용 검증 라우터 + EXECUTE 첫 행 훅(게이트 ①~⑦) + `force` 의사결정 로그 |
| `opal/skills/opal-pilot-{dev,dev-short,project}/references/pipeline.json` | `plan.pm_gate.gate.checklist` 확장(행 수 불변) |
| `opal/tools/state-tool/tests/test_state_tool.py` | 종수 단언 6건 정합 + 동작 4케이스 신설(382→386) |
| `opal/tools/state-tool/README.md` | 카탈로그 46종 + `verify --code-scan-citation-check` 절 신설 |
| `docs/PROJECT.md` · `docs/ARCHITECTURE.md` | 스킬 수 셀 42→45(드리프트 2건 포함 정합) |

## 3. 요구사항 충족

| R | 판정 | 근거 |
|---|------|------|
| R-1 스킬 신설 | ✅ | SKILL.md 268행 · alias **30종·중복 0** · 표↔레지스트리 양방향 차집합 공집합 |
| R-2 갱신 트리거 편입 | ✅ | §갱신 시점 (4단) (d) 행 · §12 「유지」 5행 + 축 구분 각주 |
| R-3 소비 2단 규율 | ✅ | §13 4열 2행 표 · 포인터 원문 복제 0건 |
| R-4 집행 승격 | ✅ | 게이트 ①~⑦(⑥이 ③④⑤ 뒤) · `reason` 3값 도메인 닫힘 · 항목 14 자기판정 0건 |
| R-5 미보급 폴백 | ✅ | 오탐 0건(`newly_uncovered` 0, `pre_existing`만 비차단) · 폴백 조건 3곳 명시 |
| R-6 회귀 보존 | ✅ | `task_steps` **16/11/9 불변** + key 집합 동일 · `spec-validate` violations 0건 · **8 파이프라인 A/B 대조 전건 동일** |

## 4. 최대 산출 — 기능이 아니라 게이트 순서 계약

이 태스크의 최대 발견은 **게이트 배치 순서 자체가 계약**이라는 점이다.

- `_run_clarification_hook`는 `auto_pass` 거부를 graceful skip **앞**에 둔다. 그 배치를 답습하면 문서 전용 태스크에서 거부가 발생해 「오탐 0건」이 원리적으로 깨진다(H-7, P0).
- 근거는 이미 코드에 있었다 — `code-map-hook.js:121-124` "이 게이트는 ⑥ code-map 로딩보다 **반드시 위**에 있어야 한다 … **순서 자체가 계약이며**".
- 이 순서 계약을 **코드(게이트 ⑥ 주석)·`header-rules.md` (d) 폴백 3종·`pm-review-gate.md` 항목 14 스킵 조건** 3곳에 일관 기재했고, **S-24**가 순서 위반을 탐지하는 유일한 판별 조합으로 회귀를 고정한다.
- 시나리오 집합만으로는 이 결함을 못 잡았다 — 목표-커버 게이트 iteration 1이 그것을 지적했다(아래 §5).

## 5. 검증 2원화가 세 번 작동했다

| # | 지점 | 잡아낸 것 |
|---|------|----------|
| 1 | 목표-커버 게이트 iteration 1 (Evaluator) | S-11이 게이트 ⑥에 닿지 않아 **순서 계약이 깨진 구현도 전건 Pass 가능**했다. goal 시나리오 2건이 모두 `R-1`에만 매핑(생성 국면 편중) |
| 2 | TEST 단계 (test-agent) | S-20 문면 결손 · S-25 문서↔집행 불일치 — 둘 다 PM·구현 워커가 못 본 것 |
| 3 | Step 19 (test-agent ≠ Step 18 구현자) | PM 지시 전제 반증(`--auto-pass`는 093-era 계약으로 자체 로그를 쓴다) + PLAN §3.4.2 문면 drift 발견 |

- 워커가 테스트를 기대에 맞추지 않고 **관측을 보고**한 것이 세 번 모두 결정적이었다.

## 6. PM 오판 2건 (기록)

- **CLOSE 차단 원인 오진** — "Step 15의 `@header` 증가분이 8192 창문을 넘겼다"고 판단했으나, `git checkout --`로 변경을 배제한 **HEAD 원본에서도 재현**된다. 실제 원인은 `code-scan.js`의 문자/바이트 비대칭이다(§8 이월 1번).
- **S-11 ① 기대 오판** — 이 태스크를 문서 전용으로 보고 `skipped`·`doc_only_task`를 기대했으나, §4.2에 `.py`가 포함되어 `pass`가 정답이다. 판정 축인 「거부 0건」은 충족.

## 7. PLAN 결손 2건 (Step 15·16)

원 PLAN 14 Step이 두 가지를 빠뜨렸고, **둘 다 워커 격리가 정상 작동한 결과** 드러났다.

- **Step 15** — `ERROR_CODES` 45→46이 종수 단언 6건을 깨뜨리는데 대응 Step 없음. 098이 H-10 「테스트 선갱신」으로 흡수한 선례가 있다.
- **Step 16** — 신규 플래그를 설명하는 README 절 미배정. 098 v1.8이 카탈로그 정정과 함께 신규 절을 추가한 선례가 있다.
- 교훈: **선례가 있는 동반 작업은 PLAN 분해 시 선례를 먼저 조회해야 한다.** 두 결손 모두 098 한 태스크에 답이 있었다.

## 8. 이월 사항

| # | 항목 | 심각도 |
|---|------|--------|
| 1 | **`code-scan` 문자/바이트 비대칭** — 라이브 읽기 `Buffer.alloc(8192)`(바이트) vs HEAD 비교 `slice(0,8192)`(문자). 한글 `@header`가 그 구간에 있으면 변경 시마다 **거짓 회귀 `newly_uncovered`로 CLOSE를 차단**한다. 실측: `test_state_tool.py` json_end 10887바이트 / 8134문자 | **높음** |
| 2 | `HEADER_READ_BYTES = 8192` 초과 파일 — `state_tool.py`·`test_state_tool.py`의 `description` 누적 성장이 원인. 이력을 파괴하지 않는 압축·분리 전략 필요 | 중 |
| 3 | 기존 45개 SKILL.md `@header` 미보유 — 신설 `opcmb`만 보유한 비대칭. 소급 부여는 `discover`/`scaffold`의 몫 | 중 |
| 4 | 변경이력 제거 A안(2026-08-14 확정, 미실행)과 현행 규약 충돌 | 중 |
| 5 | `opcmb` `backfill` 팬아웃 · `split` 샤딩 모드 — 이번 범위 제외 | 중 |
| 6 | `opi`에 code-map Phase 편입 — 이번 범위 제외 | 낮음 |
| 7 | `tasks/` 아래 `105` 번호 중복 2건 · `memory_file_missing` 위반 2건 | 낮음 |

## 9. CLOSE 게이트 우회 기록

`header-rules.md` §갱신 시점 (b) CLOSE 진입 전 게이트가 `validate --changed` exit≠0(`newly_uncovered` 1건 — `test_state_tool.py`)으로 차단했다.

- **판정**: 이 태스크가 만든 미갱신이 **아니다**. `git checkout --`로 변경을 배제한 HEAD 원본에서도 동일하게 재현되며, 원인은 §8 이월 1번의 도구 결함이다.
- **처치**: 캡틴 승인 아래 진입하고 결함을 이월 등록했다. 근거·실측은 `AGENTIC-LOG.md` §[정정] CLOSE 게이트 차단 원인에 기록됐다.

## 10. 미수행

- **커밋** — 하네스 커밋 규칙(사용자 명시 요청 시에만)에 따라 수행하지 않았다.
- **재배포** — Step 17(SKILL.md 268행)·18(`state_tool.py`)·19(테스트)가 배포 이후 변경되어 `~/.opal/` 배포본이 뒤처져 있다.
- **S-21 (L3 `[SUPERVISOR]`)** — `//opcmb`가 `discover` 직후 멈추고 `index.json` 초안을 제시하는지 캡틴 수동 확인 대기.
