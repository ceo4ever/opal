# TASK: AGENT.md §보고 형식 전면 제거

> 작성일: 2026-09-06 | 작업 유형: 개선 | 적용 스킬: opds | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

전 세션 상시 로드되는 `opal/core/AGENT.md` §보고 형식 177줄을 전면 제거하고, 이를 지목하는 파생 참조 2건을 동기화한 뒤 install로 재배포한다. 대체 규범은 이번 범위에 두지 않는다.

## 배경

§보고 형식은 Phase A(비서 tier) Eager 구간에 인라인되어 있어 비서·PM·`[ASSISTANT]` 캡 **모든 세션**에서 예외 없이 로드된다. 집행 도구가 없는 산문 규범인데도 절이 계속 증식해, 상시 로드 코어의 절반을 차지하는 상태에 도달했다. 캡틴은 절을 먼저 제거하고 실사용 케이스를 관찰하며 최소 가이드를 별도로 정하기로 결정했다.

## 배경 분석 (대화에서 도출)

**규모 실측**

| 항목 | 값 | 근거 |
|------|-----|------|
| §보고 형식 분량 | 177줄 / 14,912 bytes | `opal/core/AGENT.md:185-361` |
| 배포본 AGENT.md 총 분량 | 361줄 | install이 `## 변경이력` 이하를 절단(`scripts/install-mac.sh:226`) |
| 상시 로드 코어 내 비중 | 49% | 177 / 361 |
| 로드 조건 | Phase A Eager, 전 tier 무조건 | `opal/core/AGENT.md:17-19` |

**개정 나선 실측**

- 변경이력 표에서 §보고 형식을 명시 지목한 개정이 13건이며, 그중 11건이 2026-08-21~08-27 7일에 집중됐다 (`opal/core/AGENT.md:375-394`).
- 개정 사유가 연쇄한다 — v5.5 승인 교착 → v5.6 채널 2형태 → v5.7 애매 승인 → v5.8 자기모순 → v5.9 액션 위치 → v6.0 채널 이중화. 각 개정이 직전 개정이 만든 회피 경로를 막는 형태다.
- 최종 개정 v6.0(2026-08-27) 이후 10일간 추가 개정은 없다.

**집행 수단 부재**

- `opal/tools/` 20종과 `scripts/`를 스캔한 결과, 이 형식을 판정하는 lint·validate·QA 게이트가 0건이다.
- 헌법 Core Stance "Enforce, don't just advise: if a rule must always hold, a tool gates it — not prose"를 충족하지 못한 상태다 (`opal/core/PRINCIPLES.md`).

**이관 경로 기각 이력**

- 태스크 099가 전부 인라인 / 분리+포인터 / 절충 3안을 비교해, 전 tier 공통 규범은 분리해도 순이익이 0 또는 음수임을 실증했다 (`.opal/brain/pages/concept/lean-core-relocation-benefit-precondition.md`).
- 따라서 실질 선택지는 폐지 또는 축소뿐이며, 이번 태스크는 폐지를 택한다.

**보고 유형 10종의 소유자 대조**

§보고 형식을 제거해도 아래 7유형은 소유 문서가 그대로 살아 있다. 무규범이 되는 것은 3유형(질의 응답·제안/경보·정정)뿐이다.

| 유형 | 현재 소유 문서 | 제거 후 |
|------|--------------|--------|
| 세션 개시 브리핑 | `opal-pm.md` §15 | 존치 |
| 질의 응답·분석 | **AGENT.md §보고 형식** | 무규범 |
| 명확화 질문 | `PRINCIPLES.md` §1 + 명확화 게이트 | 존치 |
| 제안·경보 | **AGENT.md §주도성**(형태 규정 없음) | 무규범 |
| 진행 중 관측 | `harness/observability.md` | 존치 |
| 게이트 보고 | `opal-harness-semi-agentic.md` §10 | 존치 |
| 워커 결과 검토 | `harness/pm-review-gate.md` | 존치 |
| 실패·에스컬레이션 | `opal-harness.md` §1 + `opal-harness-agentic.md` §6 | 존치 |
| 완료 보고 | `opal-harness-semi-agentic.md` §10.3 + `opal-harness-agentic.md` §9 | 존치 |
| 정정 | **AGENT.md §보고 형식** 원칙 6·어휘 #8 | 무규범 |

**절 번호 파손 위험 (필수 제약)**

- `opal-pm.md`의 §9~§18은 프로젝트 소스 안에서 18회 축자 지목된다(§9×2 · §10×1 · §11×2 · §12×2 · §13×6 · §14×1 · §15×3 · §18×1).
- §8을 삭제하고 §9 이하를 당겨 재번호하면 이 18건이 **무성 파손**된다. 태스크 105에서 같은 유형의 절 번호 축자 지목 파손을 보존 조치로 막은 선례가 있다.

## 확정된 설계 방향 (대화에서 합의)

- `[결정]` `opal/core/AGENT.md` §보고 형식을 **전면 제거**한다. 축소·이관이 아니라 삭제다.
- `[결정]` 대체 규범(4조 최소안 등)은 **이번 범위에 두지 않는다**. 제거 후 실사용 케이스를 관찰하며 별건으로 검토한다.
- `[결정]` §보고 형식 하위의 **역할별 응답 표기 표**(`{name}:` / `{name}[PM]:` / `📋 {name}[PM]:`)와 **Observability 선언 스텁**도 함께 삭제한다 — 절 전체가 제거 대상이라는 문언을 그대로 적용한다.
- `[결정]` `opal-pm.md` §8은 **절 번호와 제목을 보존**하고 본문만 소유자 안내 1줄로 교체한다. 절 삭제·재번호는 금지한다.
- `[사실]` Observability 선언의 규범 본체는 `opal-harness.md` §5와 `harness/observability.md`가 소유하므로, AGENT.md의 스텁 삭제로 소실되지 않는다 (`opal/core/references/opal-harness.md` §5).
- `[사실]` 게이트 3종 보고 양식은 `opal-harness-semi-agentic.md` §10이 별도 소유하므로 제거 대상이 아니다 (`opal/core/references/opal-harness-semi-agentic.md:124-247`).
- `[결정]` 실행 트랙은 `//opds --agentic --wt`다.

## 명확화 결과

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | `opal/core/AGENT.md` §보고 형식 177줄을 삭제하고 파생 참조 2건을 동기화한 뒤 install로 재배포한다 | - | `opal/core/AGENT.md:185-361` |
| 범위 | **포함** — `opal/core/AGENT.md` §보고 형식 삭제 + 부트스트랩 절 Phase A 서술 2줄 동기화 / `opal-pm.md` §8 본문 1줄 교체(번호 보존) / `opal-harness-semi-agentic.md:126` 문구 교체 / `docs/ARCHITECTURE.md:59` 서술 동기화 / 4파일 변경이력 행 추가 / install 재배포. **제외** — 대체 규범 신설, `opal-harness-semi-agentic.md` §10 구판 표기 정정, `opal/skills/opal-brain/SKILL.md:384` 인라인 인용, brain 페이지 stale 정정(CLOSE ingest 소관) | - | `opal/core/references/opal-pm.md:100-107`, `opal/core/references/opal-harness-semi-agentic.md:126` |
| 제약 | (1) `~/.opal/` 직접 편집 금지 — 소스 수정 후 install 재배포만 허용 (2) `opal-pm.md` §9~§18 재번호 금지 (3) 스킬·에이전트·참조 문서 수정 시 변경이력 표 행 추가 의무 (4) 커밋은 캡틴 명시 요청 시에만 | - | `.opal/AGENT.md` §금지사항, 본 문서 §배경 분석 「절 번호 파손 위험」 |
| 완료기준 | 배포본 `~/.opal/AGENT.md`에 §보고 형식 잔존 0건이고, 프로젝트 소스에서 `AGENT.md §보고 형식`을 지목하는 댕글링 참조가 0건이며, `opal-pm.md` §9~§18 헤딩 번호가 변경 전과 동일하다 | - | 본 문서 §요구사항 AC |

## 요구사항

- [ ] **R-1. §보고 형식 절 삭제**
  - 무엇을: `### 보고 형식` 헤딩부터 `## 변경이력` 직전까지 전체 삭제(하위 역할별 응답 표기 표·Observability 선언 스텁 포함)
  - 어디에: `opal/core/AGENT.md:185-361`
  - 왜: 확정 방향 1 — 전면 제거
  - AC: 삭제 후 파일에서 `### 보고 형식` 헤딩이 0건이고, `🎯 결론`·`📌 추가 검토 사항`·`▶️ 승인 요청`·`마크다운 어휘`·`역할별 응답 표기` 문자열이 본문(변경이력 표 제외)에서 0건이다. 삭제 외 다른 절의 내용이 변경되지 않는다.

- [ ] **R-6. 부트스트랩 절 Phase A 능력 서술 동기화**
  - 무엇을: Phase A 보유 능력 열거에서 "보고 형식"을 제거(나머지 능력 — 도구·MCP 인지맵, `//` 커맨드/스킬 레지스트리 해석 — 은 보존)
  - 어디에: `opal/core/AGENT.md:7`(설계 원칙 박스) · `opal/core/AGENT.md:19`(Phase A 절 머리)
  - 왜: R-1 수행 후 두 줄이 존재하지 않는 능력을 서술하게 되어 문서가 거짓을 말한다
  - AC: 두 줄에서 `보고 형식` 문자열이 0건이고, `도구·MCP 인지맵`과 `` `//` 커맨드/스킬 레지스트리 해석 `` 문언은 보존된다.

- [ ] **R-7. `docs/ARCHITECTURE.md` Phase A 서술 동기화**
  - 무엇을: Phase A 로드 항목 열거에서 `보고형식`을 제거
  - 어디에: `docs/ARCHITECTURE.md:59`
  - 왜: 부트스트랩 2-tier 표가 Phase A 구성 요소로 보고형식을 명시하고 있어 R-1 후 사실과 어긋난다
  - AC: 해당 행에서 `보고형식` 문자열이 0건이고, `스킵게이트`·`identity`·`PRINCIPLES(헌법)`·`도구맵`·`` `//` 레지스트리 해석 `` 항목은 보존된다.

- [ ] **R-2. `opal-pm.md` §8 본문 교체 (번호 보존)**
  - 무엇을: §8 본문(설명 1줄 + 인용 블록 2개)을 "프레임워크는 게이트 3종과 세션 첫 응답 외의 보고 형식을 규정하지 않는다"는 취지의 안내 1줄로 교체
  - 어디에: `opal/core/references/opal-pm.md:100-107`
  - 왜: 확정 방향 4 — 절 삭제·재번호 시 외부 축자 지목 18건이 무성 파손된다
  - AC: `## 8. 보고 형식` 헤딩이 그대로 존재하고, §9~§18의 헤딩 번호·제목이 변경 전과 문자열 단위로 동일하다. §8 본문에 `AGENT.md §보고 형식` 문자열이 0건이다.

- [ ] **R-3. `opal-harness-semi-agentic.md` 댕글링 참조 제거**
  - 무엇을: "게이트 3종 외에는 `AGENT.md §보고 형식`의 형식 자율성이 유지된다"에서 존재하지 않게 될 절 지목을 제거하고, 게이트 3종 외 자유 형식이라는 의미만 남긴다
  - 어디에: `opal/core/references/opal-harness-semi-agentic.md:126`
  - 왜: 제거 후 죽은 포인터가 남는다
  - AC: 해당 줄에 `AGENT.md §보고 형식` 문자열이 0건이고, "게이트 3종만 본 양식을 따른다"는 규범 의미가 보존된다.

- [ ] **R-4. 변경이력 행 추가**
  - 무엇을: 변경 4파일 각각의 `## 변경이력` 표에 태스크 번호(108)와 KST 일시를 포함한 행 1건씩 추가
  - 어디에: `opal/core/AGENT.md` · `opal/core/references/opal-pm.md` · `opal/core/references/opal-harness-semi-agentic.md` · `docs/ARCHITECTURE.md`
  - 왜: 프로젝트 금지사항 「변경이력 누락 금지」
  - AC: 4파일 각각에 신규 행이 정확히 1건 추가되고 각 행에 `(108)` 및 `2026-09-06` 일시가 포함된다. **삽입 위치는 표 정렬축을 따른다** — `AGENT.md`·`opal-pm.md`·`opal-harness-semi-agentic.md` 3파일은 오름차순이므로 **말미**, `docs/ARCHITECTURE.md`는 **내림차순**이므로 구분선 직후 **첫 데이터 행**이다. (근거: PLAN.md §부록 #2 — 실측 결과 ARCHITECTURE 표 첫 데이터 행 `:497`이 2026-09-03로 최신이다)

- [ ] **R-5. install 재배포 및 배포본 검증**
  - 무엇을: `scripts/install-mac.sh`를 실행하여 `~/.opal/`에 반영하고 배포 결과를 검증
  - 어디에: `~/.opal/AGENT.md` · `~/.opal/references/opal-pm.md` · `~/.opal/references/opal-harness-semi-agentic.md`
  - 왜: `~/.opal/` 직접 편집 금지 — 배포가 유일한 반영 경로
  - AC: (a) 잔존 0 — `grep -c "### 보고 형식" ~/.opal/AGENT.md`가 0이다. (b) 채택 검증 — 배포본 `~/.opal/AGENT.md`의 총 줄 수가 변경 전(361줄) 대비 177줄 감소한 184줄이다. (c) 댕글링 0 — 배포본 3파일에서 `AGENT.md §보고 형식` 문자열이 0건이다. (d) 무손상 — 배포본 `~/.opal/references/opal-pm.md`의 §9~§18 헤딩이 변경 전과 동일하다. (e) 서술 정합 — 배포본 `~/.opal/AGENT.md` 부트스트랩 절에 `보고 형식` 0건이며, `docs/ARCHITECTURE.md:59`는 **소스 측 단독으로** `보고형식` 0건을 판정한다. (근거: PLAN.md §부록 #3 — `install-mac.sh` 전수 grep 결과 `docs/` 배포 지점 0건이므로 배포본 ARCHITECTURE는 존재하지 않는다)

## 제약 조건

- **배포 경계**: `~/.opal/` 배포 파일을 직접 수정하지 않는다. 프로젝트 소스(`opal/`)를 수정한 뒤 install로 재배포한다.
- **절 번호 불변**: `opal-pm.md` §9~§18을 재번호하지 않는다. 외부 축자 지목 18건이 무성 파손된다.
- **작업본 격리**: 코드 작업본은 `.opal-worktrees/task_108/`(브랜치 `feat/OP-TASK-108`)이며, 태스크 문서·`.opal/MEMORY.json`·`.opal/brain/`은 허브에 고정한다.
- **install 부수효과**: install은 worktree 브랜치 내용을 전역 `~/.opal/`에 배포한다 — 병합 전 상태가 전역에 반영되므로 CLOSE 시 브랜치 처리 방향을 캡틴에게 보고한다.
- **커밋 금지**: 커밋·머지는 캡틴이 명시 요청할 때만 수행한다.
- **Surgical**: 삭제 대상 외 인접 절을 개선하지 않는다 (`PRINCIPLES.md` §3).

## 기술 스택

- Markdown 문서 (프레임워크 SSOT)
- Bash — `scripts/install-mac.sh` (배포 어댑터)
- 검증: `grep` / `wc` 기반 문자열·줄 수 판정 (동적 테스트 대상 아님)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | AGENT.md | `opal/core/AGENT.md` | 제거 대상 절의 SSOT |
| D-2 | 소스 | opal-pm.md | `opal/core/references/opal-pm.md` | §8 파생 참조 |
| D-3 | 소스 | opal-harness-semi-agentic.md | `opal/core/references/opal-harness-semi-agentic.md` | :126 댕글링 참조 + §10 게이트 양식 소유자 |
| D-4 | 설계 | OPAL 헌법 | `opal/core/PRINCIPLES.md` | Enforce 원칙 · Surgical 원칙 근거 |
| D-5 | 설계 | lean core 이관 이익의 전제 조건 | `.opal/brain/pages/concept/lean-core-relocation-benefit-precondition.md` | 이관 경로 기각 이력(099) |
| D-6 | 설계 | 템플릿 우위 법칙 | `.opal/brain/pages/concept/template-precedence-over-prose-norms.md` | 제거 시 행동 회귀 예측 근거 |
| D-7 | 소스 | install 어댑터 | `scripts/install-mac.sh` | 변경이력 절단 동작(:226) · 배포 경로 |
