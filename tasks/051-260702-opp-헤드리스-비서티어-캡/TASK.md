# TASK: `[ASSISTANT]` 마커로 headless(claude -p) 호출을 비서 tier로 캡

> 작성일: 2026-07-02 | 작업 유형: 개선 | 적용 스킬: opp | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

049에서 도입한 2-tier 부트스트랩(비서=Phase A / PM=Phase B, `.opal/AGENT.md` opt-in 승격)의 이득을 `claude -p` 헤드리스 호출에도 적용한다. 프롬프트 첫 줄 `[ASSISTANT]` 마커를 신설하여, cwd에 `.opal/AGENT.md`가 있어도 PM tier(Phase B)로 승격하지 않고 비서 tier(Phase A)까지만 로드하도록 부트스트랩 게이트를 확장한다.

## 배경

- 현재 `claude -p`는 인터랙티브와 동일하게 `~/.claude/CLAUDE.md`(OPAL 마커)를 상속하고, cwd에 `.opal/AGENT.md`가 있으면 **무조건 PM tier까지 승격**된다 (승격 신호가 `.opal/AGENT.md` 존재 하나뿐 — `opal/core/AGENT.md:28`).
- 기존 스킵 경로는 둘 다 all-or-nothing이다: `bootstrap:off`(세션/프로젝트 토글) · `[WORKER]`(Phase A·B·공통 전부 스킵 — `opal/core/AGENT.md:9`). "비서 tier만 켜고 PM은 끈다"는 중간 단이 없다.
- 대표 피해 경로: 대시보드 브레인 질의 어댑터가 `cwd=project_path`로 `claude -p '//opbr query --read-only ...'`를 구동하는데(`dashboard/backend/adapters/opbr_adapter.py:129,159`), 읽기전용 브레인 워커가 PM tier(구현금지 가드·디스패치 의무·CLOSE 게이트)를 불필요하게 로드한다 → tier 오염(서브프로세스가 자신을 PM으로 오인) 위험.

## 배경 분석 (대화에서 도출)

대화에서 알투가 직접 실측·조사한 결과:

1. **claude -p 부트스트랩 실측** (프로젝트 cwd): `setting.json → identity.md → PRINCIPLES.md → 프로젝트 .opal/AGENT.md → opal-harness.md → opal-pm.md` **6개 파일 Read 후 PM 모드 진입**. 즉 Phase A + Phase B 풀 로드 확인.
2. **지연 병목 정정** (037 후속 PoC `follow-up-brain-query-lite.md`): 부트스트랩 파일 로딩은 콜드 지연의 병목이 **아니다**(자명 작업 ~5초). 콜드 69초의 진짜 원인은 인-에이전트 멀티턴 루프. → 본 태스크의 tier 캡은 **지연 단축이 목적이 아니라 "올바른 tier 격리(정합성)"가 본질**. 지연 레버는 별건(`opbr --lite`).
3. **`//` 커맨드는 비서 tier 능력**: `//`(opi 포함) 커맨드·스킬 레지스트리 해석은 비서 tier가 보유하고 `//` Lazy 트리거는 전제조건이 없다(`opal/core/AGENT.md:15`). → `[ASSISTANT]` 캡(비서 tier only) 상태에서도 `//opbr` 정상 완주 가능.
4. **대안 비교**: `--append-system-prompt` 주입안은 AGENT.md 무변경 스톱갭이나, 게이트에 앵커되지 않는 애드혹 NL이라 drift·비결정·비재사용 → 헌법 "Enforce, don't just advise" 위배. `[ASSISTANT]` 마커안 채택(캡틴 확정).

## 확정된 설계 방향 (대화에서 합의)

**3단 마커 사다리** — 첫 줄 마커로 부트스트랩 로드 범위를 결정:

| 첫 줄 마커 | 로드 범위 | 용도 |
|-----------|----------|------|
| `[WORKER]` | 아무것도 로드 안 함 (Phase A·B·공통 전부 스킵) | PM이 컨텍스트를 직접 주입하는 워커 |
| `[ASSISTANT]` (신설) | **비서 tier만 (Phase A)** — `.opal/AGENT.md`가 있어도 Phase B 스킵 | headless 비서·읽기전용 워커 (예: 브레인 질의) |
| (마커 없음) | 비서 + PM (Phase A + B, 프로젝트면 승격) | 일반 인터랙티브 세션 |

- 집행 지점: `opal/core/AGENT.md`(SSOT) Phase B 승격 게이트에 억제 절 추가. `[WORKER]` 규칙과 직교하는 별도 스킵 경로로 명문화.
- 마커는 첫 줄 프리픽스이며 이후 라인(`//opbr ...` 등)은 실제 요청으로 정상 처리된다.
- 브레인 어댑터가 첫 소비자: `opbr_adapter.py`의 `-p` 프롬프트 첫 줄에 `[ASSISTANT]` 프리픽스.

## 명확화 결과

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | `[ASSISTANT]` 첫 줄 마커 신설 → headless 호출을 비서 tier(Phase A)로 캡, PM tier(Phase B) 승격 억제 | - | `opal/core/AGENT.md:9,15,28` |
| 범위 | 포함: `opal/core/AGENT.md`(게이트+완료보고+변경이력), `opbr_adapter.py`(프롬프트 프리픽스+주석). 제외: 헌법/harness/opal-pm 문서, 지연 경량화(`--lite`), install 재배포(캡틴 수행), 인터랙티브 동작 | - | 배경 분석 4 |
| 제약 | ~/.opal 직접 편집 금지(소스만 수정 후 install) / 변경이력 행 추가 의무 / 플랫폼 분기 어댑터 격리 / 인터랙티브 세션 동작 무변경(회귀 0) | - | `.opal/AGENT.md` §금지사항 |
| 완료기준 | 아래 요구사항 AC 전부 충족 + `[ASSISTANT]` 프리픽스 시 Phase B 미로드 실측 확인(dev-artifact 배포로 검증, 캡틴 install은 후속) | - | 헌법 §4 |

## 요구사항

- [ ] **R1 — Phase B 억제 게이트**: `opal/core/AGENT.md` Phase B 승격 게이트(현 `:28`)에 "프롬프트 첫 줄이 `[ASSISTANT]`이면 `.opal/AGENT.md`가 있어도 Phase B 전체를 스킵한다"는 절을 추가한다.
  - 어디에: `opal/core/AGENT.md` §부트스트랩 > Phase B 승격 게이트 + `[WORKER 규칙]` 인접(설계원칙 박스)
  - 왜: 승격 신호가 `.opal/AGENT.md` 존재 하나뿐이라 headless 캡 불가 (`opal/core/AGENT.md:28`)
  - AC: (a) Phase B 게이트 문장에 `[ASSISTANT]` 억제 조건이 존재한다. (b) `[WORKER]`(전부 스킵) / `[ASSISTANT]`(Phase A만) / 무마커(A+B) 3단 구분이 문서에 명시된다. (c) 마커 이후 라인이 실제 요청으로 처리되며 `//` 커맨드 인식이 유지됨이 명시된다.
- [ ] **R2 — 완료 보고 tier 표기**: `[ASSISTANT]` 캡 세션의 부트스트랩 완료 보고에서 `harness`·`PM`·`PM모드`를 `⬜`로 표기하는 규칙을 추가한다.
  - 어디에: `opal/core/AGENT.md` §부트스트랩 완료 보고 (현 비서 세션 표기 규칙 `:79` 인접)
  - 왜: 비서 세션(.opal/AGENT.md 부재)과 동일하게 Phase B 미로드 상태를 관측 가능해야 함
  - AC: 완료 보고 규칙에 `[ASSISTANT]` 캡 세션의 `⬜ harness ⬜ PM ⬜ PM모드` 표기 예시가 존재한다.
- [ ] **R3 — 변경이력**: `opal/core/AGENT.md` 변경이력 표에 051 행을 추가한다 (일시 KST + 태스크 번호).
  - AC: 변경이력 표 마지막에 `v4.2`(또는 다음 버전) / `2026-07-02 HH:mm` / 051 설명 행이 존재한다.
- [ ] **R4 — 브레인 어댑터 첫 소비자 적용**: `opbr_adapter.py`의 `-p` 프롬프트 첫 줄에 `[ASSISTANT]` 프리픽스를 추가하고, docstring/주석에 근거를 반영한다.
  - 어디에: `dashboard/backend/adapters/opbr_adapter.py:123`(prompt 구성) + 상단 docstring
  - 왜: 읽기전용 브레인 워커가 PM tier를 로드하지 않도록 캡 (tier 격리)
  - AC: (a) prompt 첫 줄이 `[ASSISTANT]`이고 이어서 `//opbr query --read-only "..."`가 온다. (b) docstring에 비서 tier 캡 의도가 1줄 이상 기재된다. (c) 기존 read-only 가드·shell=False·allowedTools 계약이 유지된다.
- [ ] **R5 — 동작 검증**: `[ASSISTANT]` 프리픽스가 있는 `claude -p` 호출이 프로젝트 cwd에서 Phase B(harness/opal-pm/프로젝트 AGENT.md)를 로드하지 않음을 실측한다.
  - 왜: 헌법 §4 — done은 검증된 동작. 문서 프로즈 변경이 실제 런타임 게이트 판단에 반영되는지 확인 (self-confirming 방지)
  - AC: 캡 마커 프로브의 완료 보고가 `⬜ harness ⬜ PM ⬜ PM모드`이고, Read한 파일 목록에 opal-harness.md·opal-pm.md·프로젝트 .opal/AGENT.md가 없다. (dev-artifact로 ~/.opal/AGENT.md 배포 후 검증 — 캡틴 canonical install은 후속)

## 제약 조건

- **배포 경계**: `~/.opal/` 직접 편집 금지. 소스(`opal/core/AGENT.md`)를 수정하고 install로 재배포한다. 검증용 dev-artifact 배포는 예외이며 캡틴의 canonical install이 최종 (`.opal/AGENT.md` §금지사항 / 044 메모리).
- **회귀 0**: 마커 없는 인터랙티브 세션의 부트스트랩 동작은 변하지 않아야 한다.
- **변경이력 누락 금지**: 문서 수정 시 변경이력 표 행 추가.
- **플랫폼 분기 금지**: 마커 규약은 어댑터/문서 논리에만, 플랫폼 하드코딩 없음.

## 기술 스택

- OPAL 프레임워크 문서(Markdown) — `opal/core/AGENT.md`
- Python 3 (dashboard 백엔드 어댑터) — `dashboard/backend/adapters/opbr_adapter.py`

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | AGENT.md (부트스트랩 SSOT) | `opal/core/AGENT.md` | Phase A/B 게이트·WORKER 규칙·완료보고 — 수정 대상 |
| D-2 | 소스 | opbr_adapter.py | `dashboard/backend/adapters/opbr_adapter.py` | claude -p 호출 첫 소비자 — 프롬프트 프리픽스 대상 |
| D-3 | 설계 | opal-pm.md | `~/.opal/references/opal-pm.md` | Phase B가 로드하는 PM 행동 프로세스 (억제 대상 확인) |
| D-4 | 설계 | 브레인질의 콜드 경량화 메모리 | `.opal/memory/follow-up-brain-query-lite.md` | 지연 병목 정정 근거 — 본 태스크는 정합성 목적 |
