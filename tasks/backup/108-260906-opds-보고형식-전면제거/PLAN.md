# PLAN: AGENT.md §보고 형식 전면 제거

> 작성일: 2026-09-06 | 입력: TASK.md (ANALYSIS.md 없음 — 코드/문서 분석을 PLAN에서 직접 수행)
> 모드: Multi-Feature | 실행 모드: 복잡
> 문서 루트: `/Volumes/Data/AIStudio/workspace/ai-framework/tasks/108-260906-opds-보고형식-전면제거/`
> 코드 루트: `/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_108/` (브랜치 `feat/OP-TASK-108`)

## 결론

- **설계**: 4파일 4 Step(파일 1개 = Step 1개)으로 삭제·동기화를 끝내고, 전역 배포(install)는 EXECUTE에서 분리해 TEST 단계에 PM 직접 실행으로 둔다.
- **결정 M-1**: `install-mac.sh`는 워커(비-tty)에서 실행하면 메뉴 선택 없이 `install_opal` + `install_mcp`가 강제 실행되므로(`scripts/install-mac.sh:2192-2197`), **캡틴 터미널에서 PM이 메뉴 [1]로 실행**한다.
- **결정 M-4**: TASK.md AC의 수치 2건이 실측과 다르다 — 배포본 AGENT.md는 360줄이 아니라 **361줄**이므로 목표치는 183줄이 아니라 **184줄**이며, `docs/ARCHITECTURE.md` 변경이력 표는 **내림차순**이라 신규 행이 마지막이 아니라 **첫 행**에 들어간다. 두 건 모두 `사실오류`로 판정하고 정정 적용한다.
- **결정 M-3**: 「잔존 0」 판정은 install의 strip 식(`scripts/install-mac.sh:226`)과 **동일한 awk 표현식**으로 본문을 잘라낸 뒤 grep한다 — 소스 본문 판정과 배포본 판정의 경계가 정확히 일치한다.
- **리스크 H-4(P1)**: 「템플릿 우위 법칙」상 골격 템플릿이 세션에서 사라지면 보고 품질 회귀가 예측된다. 이는 캡틴이 의도한 관찰 대상이며 이번 범위에서 대체 규범을 두지 않는다 — 회귀 관찰 항목으로만 남긴다.
- **리스크 H-5(P0)**: install은 병합 전 브랜치 내용을 전역 `~/.opal/`에 배포하고, `~/.opal/{skills,agents,references,templates,tools,dashboard-server}`를 `rm -rf` 후 재생성한다(`scripts/install-mac.sh:1205-1214`). CLOSE 시 브랜치 처리 방향을 캡틴에게 반드시 보고한다.

---

## 확정 입력 판정

| 항목 | 판정 | 근거 |
|------|------|------|
| `opal/core/AGENT.md` §보고 형식을 **전면 제거**한다 (축소·이관 아님) | 유효 | - |
| 대체 규범(4조 최소안 등)은 이번 범위에 두지 않는다 | 유효 | - |
| 역할별 응답 표기 표 + Observability 선언 스텁도 함께 삭제한다 | 유효 | 두 블록 모두 §보고 형식 하위 구간 안에 있음을 실측 확인 — `opal/core/AGENT.md:351-357`(표기 표) · `opal/core/AGENT.md:359-360`(Observability 스텁), 절 경계는 `:185-361` |
| `opal-pm.md` §8은 절 번호·제목을 보존하고 본문만 교체한다 | 유효 | §9~§18 헤딩 실재 확인 — `opal/core/references/opal-pm.md:111,122,131,140,223,266,301,337,353,367` |
| Observability 규범 본체는 `opal-harness.md` §5 / `harness/observability.md`가 소유한다 `[사실]` | 유효 | AGENT.md 스텁 자체가 "선언 형식과 적용 시점은 하네스 §5 Observability 참조"로 위임 중 — `opal/core/AGENT.md:360` |
| 게이트 3종 보고 양식은 `opal-harness-semi-agentic.md` §10이 소유한다 `[사실]` | 유효 | `opal/core/references/opal-harness-semi-agentic.md:124-247` (§10 헤딩 `:124`, §10.1 `:130` / §10.2 `:166` / §10.3 `:208`, 변경이력 `:248`) |
| 실행 트랙은 `//opds --agentic --wt` | 유효 | worktree 실재 확인 — `.opal-worktrees/task_108` (브랜치 `feat/OP-TASK-108`, working tree clean) |
| R-5 AC(b) — 배포본 총 줄 수 360줄 → 183줄 | **사실오류** | 실측 `wc -l ~/.opal/AGENT.md` = **361**. strip은 `## 변경이력`(소스 `opal/core/AGENT.md:362`) **직전까지** keep하므로 1~361행이 배포된다 (`scripts/install-mac.sh:226`). 정정 목표치 = 361 − 177 = **184줄** |
| R-4 AC — "4파일 각각 변경이력 표 **마지막 행**이 신규 추가분" | **사실오류** | `docs/ARCHITECTURE.md` 변경이력 표는 **최신 우선 내림차순**이다 — 첫 데이터 행 `docs/ARCHITECTURE.md:497`이 2026-09-03, 파일 말미가 2026-06-18. ARCHITECTURE.md만 **첫 데이터 행(:497 위치)** 삽입으로 정정하고, 나머지 3파일은 원문대로 말미 추가 |
| R-5 AC(e) — "배포본 ... `docs/ARCHITECTURE.md:59`" | **수정필요** | install은 `docs/`를 배포하지 않는다 — `scripts/install-mac.sh` 전수 grep 결과 `docs/` 배포 지점 0건(유일 히트는 `:1702` playwright URL 주석). ARCHITECTURE.md 검증은 **소스 측 단독**으로 성립한다 |

> `사실오류` 3건은 확정 지위를 박탈하고 정상 설계 경로로 복귀했다 — 수치·삽입 위치·검증 대상 범위를 위 근거대로 정정하여 아래 설계에 반영했다. **소유자 보고 필요 항목이며 완료 보고에도 재기재한다.**

---

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

전 세션 상시 로드되는 `opal/core/AGENT.md` §보고 형식(실측 177줄, `:185-361`)을 절 전체 삭제하고, 그 절을 지목하던 파생 참조 3줄(2파일)과 Phase A 능력 서술 3줄(2파일)을 동기화한다. 4파일에 변경이력 행을 추가한 뒤 `scripts/install-mac.sh`로 재배포하여 배포본 `~/.opal/`에 잔존 0을 확인한다. 대체 규범은 두지 않는다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | §보고 형식 절 삭제 + Phase A 능력 서술 동기화 (AGENT.md 단일 파일) | R-1, R-6 | P0 | 없음 |
| F-002 | 파생 참조 동기화 (opal-pm.md §8 본문 교체 / semi-agentic:126 / ARCHITECTURE.md:59) | R-2, R-3, R-7 | P0 | 없음 (F-001과 파일 비중첩) |
| F-003 | 변경이력 행 추가 (4파일) | R-4 | P1 | F-001, F-002 (동일 파일 후행 편집) |
| F-004 | install 재배포 및 배포본 검증 | R-5 | P0 | F-001, F-002, F-003 |

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 ─┐
       ├─ F-003 ─ F-004
F-002 ─┘
(F-001 ∥ F-002 : 대상 파일 비중첩)
(F-003은 F-001·F-002가 건드린 같은 4파일의 변경이력 절을 편집하므로 같은 Step에 인라인 합류)
```

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-001 / `opal/core/AGENT.md:185-361` 삭제 | **절 경계 오삭제** — 범위 미달 시 §보고 형식 잔재가 남고, 범위 초과 시 직전 절 `### 기억과 학습`(`:180-183`) 또는 직후 `## 변경이력`(`:362`)이 파손된다. 삭제 후 파일은 정확히 217줄(394−177)이어야 한다 | P0 | L1(산출물 검사) | TS-001, TS-003 |
| H-2 | F-002 / `opal-pm.md` §8 | **절 번호 무성 파손** — §8을 삭제하고 §9 이하를 당기면 프로젝트 소스 안 18회 축자 지목(§9×2·§10×1·§11×2·§12×2·§13×6·§14×1·§15×3·§18×1)이 조용히 깨진다. §8 헤딩 문자열과 §9~§18 헤딩 10개가 변경 전과 바이트 단위로 동일해야 한다 | P0 | L1(헤딩 목록 diff vs `git show HEAD:`) | TS-006, TS-007, TS-015 |
| H-3 | F-001·F-003 / `opal/core/AGENT.md` | **잔존 0 오판(양방향)** — ⑴ 변경이력 표에 과거 기록으로 남은 `§보고 형식`·`🎯` 문자열을 삭제 대상으로 오인해 과삭제, ⑵ 반대로 본문 잔존을 변경이력으로 착각해 미검출. 판정식이 install strip과 다른 경계를 쓰면 소스·배포본 판정이 갈린다 | P1 | L1(awk 본문 절단 후 grep — install `:226`과 동일 식) | TS-002, TS-011 |
| H-4 | F-001 전체 (제거의 부작용) | **행동 회귀** — 「템플릿 우위 법칙」상 산문 규칙보다 템플릿이 유도력을 갖는다(대조 실험 템플릿 3/3 vs 산문 0/3, `.opal/brain/pages/concept/template-precedence-over-prose-norms.md`). 골격 템플릿(`🎯`/`📌`/`▶️`) 실물이 상시 로드에서 사라지면 무규범 3유형(질의 응답·제안/경보·정정)의 보고 품질이 회귀한다. **의도된 결과이므로 차단하지 않고 관찰한다** | P1 | L3(운영 관찰 — 이번 태스크 검증 대상 아님) | 후속 관찰 이월 |
| H-5 | F-004 / `scripts/install-mac.sh` 실행 | **전역 비가역 부수효과** — ⑴ 병합 전 브랜치 내용이 전역 `~/.opal/`로 나간다, ⑵ `install_opal()`이 `~/.opal/{skills,agents,references,templates,tools,dashboard-server}`를 `rm -rf` 후 재생성한다(`:1205-1214`), ⑶ 비-tty 실행 시 `install_mcp`까지 자동 동반된다(`:2192-2197`) — MCP 서버 재설정은 태스크 범위 밖 | P0 | L2(PM 직접 실행 + 실행 로그 확인) | TS-012~TS-016 |
| H-6 | F-004 / 배포본 줄 수 판정 | **기대치 오류로 인한 오판** — TASK.md AC(b)의 360/183 기준으로 검증하면 정상 결과(184줄)를 실패로 오판한다 | P2 | L1(수치 정정 반영) | TS-013 |
| H-7 | F-003 / `docs/ARCHITECTURE.md` | **정렬축 역전** — 표가 내림차순인데 말미에 추가하면 최신 행이 최하단에 놓여 표 규약이 깨진다 | P2 | L1(첫 데이터 행 위치 확인) | TS-011 |
| H-8 | F-002 / `opal-harness-semi-agentic.md` | **과삭제** — `:153`("기존 보고 형식 2종을 완전 대체")과 `:186`("`AGENT.md` 수정 — §보고 형식 인라인 + Eager Step 6.6 제거")은 §10.1/§10.2 **양식 예시 본문** 안의 과거 보고 예시이며 삭제 대상이 아니다(TASK.md §범위 「제외 — §10 구판 표기 정정」). 편집 대상은 `:126` 단 1줄 | P1 | L1(153·186행 문자열 불변 확인) | TS-010 |
| H-9 | F-001 / `opal/core/AGENT.md:7`·`:19` | **보존 토큰 동반 삭제** — "보고 형식·"만 제거해야 하는데 열거 어절 전체를 지우면 `도구·MCP 인지맵`·`` `//` 커맨드/스킬 레지스트리 해석 ``이 함께 사라져 비서 tier 능력 서술이 소실된다 | P1 | L1(보존 토큰 2종 × 2줄 존재 확인) | TS-004 |

---

## 2. 기능별 분석

### F-001: §보고 형식 절 삭제 + Phase A 능력 서술 동기화

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 에이전트 | `opal/core/AGENT.md` | 제거 대상 절의 SSOT + Phase A 능력 서술 소유 | 수정 |

#### 2.1.2 현재 구현

- 파일 실측: **394줄 / 53,610 bytes**. `## 변경이력`은 `:362`.
- §보고 형식 절 경계: **`:185`(`### 보고 형식`) ~ `:361`(공백행)** = **177줄**. `:184`는 공백, `:362`가 `## 변경이력`이므로 `185-361` 삭제 시 `:184` 공백 + `## 변경이력`이 자연 연결된다 (여분 공백행 생성 없음).
- 절 내부 구조 (`opal/core/AGENT.md:185-361`): 적용 범위 인용 2줄(`:187-188`) → **골격**(`:190`) 4층 표 → `[MUST]` 5개(`:202`,`:204`,`:206`,`:208`,`:218`) → 도구 호출 규율(`:220`) → 2단 결정 트리(`:222`) → `📌` 3어(`:232`) → 골격 템플릿 코드펜스 3쌍(`:240/270`, `:273/283`, `:288/291`) → **원칙**(`:293`) → **마크다운 어휘**(`:305`) → **작동하는가**(`:338`) → **역할별 응답 표기** 표(`:351-357`) → **Observability 선언** 스텁(`:359-360`).
- 코드펜스 안에 `## 🎯 결론`(`:244`) · `## 📌 추가 검토 사항`(`:259`) · `## ▶️ 승인 요청`(`:266`, `:275`)이 있다 — Markdown 헤딩처럼 보이지만 템플릿 예시 문자열이다. 절 삭제로 함께 사라진다.
- Phase A 능력 서술 2곳:
  - `opal/core/AGENT.md:7` (설계 원칙 박스) — "…**보고 형식**·도구·MCP 인지맵·`//` 커맨드/스킬 레지스트리 해석 능력은 본 AGENT.md 본문이 보유하며…"
  - `opal/core/AGENT.md:19` (Phase A 절 머리 인용) — "> 비서 tier는 **보고 형식**·도구·MCP 인지맵·`//` 커맨드/스킬 레지스트리 해석 능력을 보유하며…"
- 배포 경로: `strip_deploy_md "$opal_dir/core/AGENT.md" "$opal_home/AGENT.md"` (`scripts/install-mac.sh:1218`), strip 식은 `awk 'BEGIN{keep=1} /^## 변경이력$/{keep=0} keep==1{print}'` (`:226`) → 배포본 = 소스 1~361행 = **361줄**(실측 `wc -l ~/.opal/AGENT.md`).

#### 2.1.3 영향 범위

- **직접 소비자**: 모든 세션(비서·PM·`[ASSISTANT]` 캡). Phase A Eager 인라인이므로 조건 없이 로드된다 (`opal/core/AGENT.md:17-19`).
- **역참조**: `opal-pm.md:104,107`(F-002) · `opal-harness-semi-agentic.md:126`(F-002) · `docs/ARCHITECTURE.md:59`(F-002).
- **범위 밖 언급(삭제 금지)**: `.opal/AGENT.md:40`(프레임워크-우선 개선 원칙의 예시 어구) · `opal/skills/opal-brain/SKILL.md:384,488` · `opal/skills/opal-pilot-*` 등 21개 파일의 일반 명사 "보고 형식" — TASK.md §범위 「제외」에 해당하며 `AGENT.md §보고 형식` 축자 지목이 아니다.
- **관련 테스트**: 없음 — 이 형식을 판정하는 lint·validate·QA 게이트가 `opal/tools/`·`scripts/`에 0건이다(TASK.md §집행 수단 부재). 검증은 전부 산출물 검사(grep/wc)다.

---

### F-002: 파생 참조 동기화

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | `opal/core/references/opal-pm.md` | §8 보고 형식 — AGENT.md 절을 지목하는 포인터 | 수정 |
| 가이드 | `opal/core/references/opal-harness-semi-agentic.md` | §10 머리글의 형식 자율성 단서 | 수정 |
| 문서 | `docs/ARCHITECTURE.md` | 부트스트랩 2-tier 표 Phase A 로드 항목 | 수정 |

#### 2.2.2 현재 구현

- `opal/core/references/opal-pm.md` — 396줄, `## 변경이력` `:377`. §8 경계는 **`:100`(`## 8. 보고 형식`) ~ `:107`**, 그 뒤 `:108` 공백 / `:109` `---` / `:111` `## 9. code-scan.json PM 관리 의무`.
  - `:102` 설명 1줄, `:104-107` 인용 블록(4줄, `:105`는 `>` 단독). `:104`가 "보고 형식 본문: AGENT.md §보고 형식 (Eager 인라인 — 별도 Read 불요)", `:107`이 골격 4층 전문을 재서술한 장문 포인터.
  - **§9~§18 헤딩 실측**: `:111` §9 / `:122` §10 / `:131` §11 / `:140` §12 / `:223` §13 / `:266` §14 / `:301` §15 / `:337` §16 / `:353` §17 / `:367` §18. **[MUST] 이 10개 헤딩 문자열이 변경 전후 동일해야 한다.**
- `opal/core/references/opal-harness-semi-agentic.md` — 260줄, `## 변경이력` `:248`. 편집 대상은 **`:126` 1줄**: "이 3 게이트 보고만 본 양식을 따른다 (§3 모드 경계 / §6 CLOSE 게이트 참조). 게이트 3종 외에는 `` `AGENT.md §보고 형식` ``의 형식 자율성이 유지된다."
  - 같은 파일 `:153`·`:186`은 §10.1/§10.2 **양식 예시 코드 본문**으로 삭제 대상이 아니다(H-8).
- `docs/ARCHITECTURE.md` — 525줄, `## 변경이력` `:493`. `:59`는 2-tier 표의 Phase A 행: "…| 스킵게이트(setting.json 머지) + identity + PRINCIPLES(헌법) + **보고형식**·도구맵·`` `//` `` 레지스트리 해석 | 자비스 비서 |" — 여기만 띄어쓰기 없는 `보고형식` 표기다.
  - **install은 `docs/`를 배포하지 않는다** — `scripts/install-mac.sh` 전수 grep에서 `docs/` 배포 지점 0건.

#### 2.2.3 영향 범위

- `opal-pm.md` §8은 Phase B(PM tier) Eager 로드 대상이므로(`opal/core/AGENT.md:35`) PM 세션 전체에 영향.
- `opal-harness-semi-agentic.md`는 semi-agentic 모드 Lazy 로드. `:126` 수정은 §10 게이트 3종 규범 자체를 건드리지 않는다.
- `docs/ARCHITECTURE.md`는 프로젝트 문서 — 런타임 로드 대상이 아니며 사람·PM 참조용.
- **본문(변경이력 제외) 기준 `AGENT.md §보고 형식` 축자 지목 실측 = 3줄 / 2파일** (`opal-pm.md:104,107` · `semi-agentic.md:126`). 이 3줄이 F-002가 0으로 만들어야 할 전건이다.

---

### F-003: 변경이력 행 추가 (4파일)

#### 2.3.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 에이전트 | `opal/core/AGENT.md` | 변경이력 표 (`:362~`) | 수정 |
| 가이드 | `opal/core/references/opal-pm.md` | 변경이력 표 (`:377~`) | 수정 |
| 가이드 | `opal/core/references/opal-harness-semi-agentic.md` | 변경이력 표 (`:248~`) | 수정 |
| 문서 | `docs/ARCHITECTURE.md` | 변경이력 표 (`:493~`) | 수정 |

#### 2.3.2 현재 구현

| 파일 | 표 컬럼 | 정렬 | 현재 최신 | 삽입 위치 |
|------|--------|------|----------|----------|
| `opal/core/AGENT.md` | `버전 \| 일시 \| 변경내용` | 오름차순 | `v6.0 \| 2026-08-27 14:18` | 파일 말미 |
| `opal/core/references/opal-pm.md` | `버전 \| 날짜 \| 내용` | 오름차순 | `v2.5 \| 2026-09-04 22:43` | 파일 말미 |
| `opal/core/references/opal-harness-semi-agentic.md` | `버전 \| 날짜 \| 내용` | 오름차순 | `v1.6 \| 2026-09-02 17:22` | 파일 말미 |
| `docs/ARCHITECTURE.md` | `날짜 \| 변경 내용` (버전 컬럼 없음) | **내림차순** | `2026-09-03 13:15` (`:497`) | **구분선 `:496` 직후 = 새 첫 데이터 행** |

#### 2.3.3 영향 범위

배포본에는 반영되지 않는다 — install이 `## 변경이력` 이하를 strip 한다 (`scripts/install-mac.sh:226`, `:235`). 소스 추적성 전용.

---

### F-004: install 재배포 및 배포본 검증

#### 2.4.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 배치 | `scripts/install-mac.sh` | 배포 어댑터 (실행만, 수정 없음) | 참조 |
| 배치 | `~/.opal/AGENT.md` | 배포 산출물 | 생성(배포) |
| 배치 | `~/.opal/references/opal-pm.md` | 배포 산출물 | 생성(배포) |
| 배치 | `~/.opal/references/opal-harness-semi-agentic.md` | 배포 산출물 | 생성(배포) |

#### 2.4.2 현재 구현

- `detect_framework_root()`는 `FRAMEWORK_ROOT`를 **스크립트 파일의 부모 디렉토리**로 결정한다 (`scripts/install-mac.sh:103-106`). → **[MUST] worktree 안의 스크립트를 실행해야 브랜치 내용이 배포된다.** 허브의 스크립트를 실행하면 main 내용이 배포되어 이번 변경이 반영되지 않는다.
- `detect_framework_root()`는 `$FRAMEWORK_ROOT/skills`와 `$FRAMEWORK_ROOT/opal/agents` 존재를 요구한다(`:108-112`) — worktree에 둘 다 실재 확인 완료.
- 배포 지점: AGENT.md `:1218` / PRINCIPLES.md `:1222` / references 디렉토리 통째 복사 후 재귀 strip `:1748-1750`.
- **비대화형 게이트**: `if [[ "${OPAL_AUTO_INSTALL:-0}" == "1" ]] || [[ ! -t 0 ]]` (`:2192`) → 워커 Bash처럼 stdin이 tty가 아니면 메뉴를 건너뛰고 `install_opal` + **`install_mcp`**를 실행하고 `exit 0` 한다(`:2195-2197`). 메뉴 [1](OPAL 자산 배포만)을 선택하려면 tty가 필요하다(`:2221-2229`).
- 파괴적 선행 동작: `clean_dirs=("skills" "agents" "references" "templates" "tools" "dashboard-server")`를 `rm -rf` 후 재배포한다 (`:1205-1214`). 보존 대상은 `identity.md` / `AGENT.md` / `projects/` / `community-skills/`.

#### 2.4.3 영향 범위

전역 `~/.opal/` 전체 — 이 태스크가 손대지 않은 스킬·도구·에이전트까지 재배포 대상이다. 병합 전 브랜치 상태가 전역에 나간다(H-5).

---

## 3. 기능별 설계

### F-001: §보고 형식 절 삭제 + Phase A 능력 서술 동기화

#### 3.1.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| - | 없음 | - | - | - |

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/AGENT.md` | 에이전트 | `:185-361` 177줄 삭제(§보고 형식 전체 — 골격·[MUST]·템플릿 3블록·원칙·어휘표·작동하는가·역할별 응답 표기 표·Observability 스텁) | (→ D-1 §보고 형식) `opal/core/AGENT.md:185-361` |
| 2 | `opal/core/AGENT.md` | 에이전트 | `:7` 설계 원칙 박스에서 `보고 형식·` 어절만 제거 | `opal/core/AGENT.md:7` |
| 3 | `opal/core/AGENT.md` | 에이전트 | `:19` Phase A 절 머리 인용에서 `보고 형식·` 어절만 제거 | `opal/core/AGENT.md:19` |

#### 3.1.2 설계 (편집 계약)

**절 삭제 — 경계 계약**

- 삭제 시작: `### 보고 형식`이 시작하는 행(현재 `:185`).
- 삭제 끝: `## 변경이력` 행(현재 `:362`) **직전 행**(현재 `:361`, 공백행).
- 삭제 후 인접 문맥은 `…§기억과 학습 인용 2줄(:182-183)` + 공백행(`:184`) + `## 변경이력` 순이어야 한다.
- **[MUST] `opal/core/PRINCIPLES.md` §3: "Touch only what the plan names. Don't improve adjacent code."** — `### 기억과 학습`(`:180-183`)과 `## 변경이력` 표 본문은 한 글자도 건드리지 않는다.
- 삭제 후 총 줄 수: **217줄** (394 − 177).

**`:7` 치환 계약** — 대상 어절만 제거, 문장 나머지 불변.

- Before: `` … 보고 형식·도구·MCP 인지맵·`//` 커맨드/스킬 레지스트리 해석 능력은 본 AGENT.md 본문이 보유하며 … ``
- After: `` … 도구·MCP 인지맵·`//` 커맨드/스킬 레지스트리 해석 능력은 본 AGENT.md 본문이 보유하며 … ``
- 보존 토큰: `도구·MCP 인지맵` / `` `//` 커맨드/스킬 레지스트리 해석 `` (H-9)

**`:19` 치환 계약**

- Before: `` > 비서 tier는 보고 형식·도구·MCP 인지맵·`//` 커맨드/스킬 레지스트리 해석 능력을 보유하며 … ``
- After: `` > 비서 tier는 도구·MCP 인지맵·`//` 커맨드/스킬 레지스트리 해석 능력을 보유하며 … ``

> **[MUST] `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `scripts/`)에서 수행한다."** — 모든 편집은 코드 루트(`.opal-worktrees/task_108/`) 안에서만 수행한다.

> **[MUST] 입력 축소** — 파일 전체 통독 금지. `grep -n`으로 위치를 특정한 뒤 해당 구간만 Read하고 Edit로 부분 편집한다. 177줄 삭제는 `sed -i` 범위 삭제가 아니라 **경계 문자열 앵커 기반**으로 수행한다(줄번호는 선행 편집으로 이동할 수 있다 — `:7`/`:19` 편집은 줄 수를 바꾸지 않으므로 순서 무관하나, 앵커 방식이 안전하다).

#### 3.1.3 환경 변경

해당 없음.

#### 3.1.4 배치/마이그레이션

해당 없음 (배포는 F-004).

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 AC (헤딩 0건) | 산출물 검사 | `opal/core/AGENT.md` 본문(변경이력 절 제외)에 `### 보고 형식` 0건 |
| TS-002 | R-1 AC (문자열 0건) | 산출물 검사 | 본문에 `🎯 결론` / `📌 추가 검토 사항` / `▶️ 승인 요청` / `마크다운 어휘` / `역할별 응답 표기` 전건 0 |
| TS-003 | R-1 AC (무손상) | 회귀 테스트 | 총 217줄, `### 기억과 학습`·`## 변경이력` 헤딩 존치, 변경이력 표 행 수 불변, 헤딩 목록이 baseline에서 `:185-361` 구간 헤딩만 제거된 것과 일치 |
| TS-004 | R-6 AC | 산출물 검사 | `:7`·`:19` 두 줄에 `보고 형식` 0건 / `도구·MCP 인지맵` 2건 / `` `//` 커맨드/스킬 레지스트리 해석 `` 2건 |

---

### F-002: 파생 참조 동기화

#### 3.2.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| - | 없음 | - | - | - |

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/opal-pm.md` | 가이드 | §8 본문(`:102` 설명 1줄 + `:104-107` 인용 블록)을 안내 1줄로 교체. **헤딩 `:100` `## 8. 보고 형식`은 문자열 그대로 보존** | (→ D-2 §8) `opal/core/references/opal-pm.md:100-107` |
| 2 | `opal/core/references/opal-harness-semi-agentic.md` | 가이드 | `:126` 둘째 문장에서 `` `AGENT.md §보고 형식` `` 지목을 제거하고 "게이트 3종 외에는 형식이 자율" 의미만 유지 | `opal/core/references/opal-harness-semi-agentic.md:126` |
| 3 | `docs/ARCHITECTURE.md` | 문서 | `:59` Phase A 행 로드 항목 열거에서 `보고형식·` 제거 | `docs/ARCHITECTURE.md:59` |

#### 3.2.2 설계 (편집 계약)

**(1) `opal-pm.md` §8 — 번호 보존 본문 교체**

> **[MUST] 절 번호 재번호 금지** — `## 8. 보고 형식` 헤딩과 `## 9.`~`## 18.` 헤딩 10개는 문자열 단위로 불변이다. 프로젝트 소스에서 §9~§18이 18회 축자 지목되므로 재번호는 무성 파손을 일으킨다 (TASK.md §배경 분석 「절 번호 파손 위험」, 실측 헤딩 위치 `opal/core/references/opal-pm.md:111,122,131,140,223,266,301,337,353,367`).

- 교체 범위: `:102`부터 `:107`까지 (헤딩 `:100`, 공백 `:101`, 그리고 절 종료 공백 `:108`·구분선 `:109`는 보존).
- 교체 후 §8 본문 = 안내 1줄. 문안 계약 — 아래 3요소를 담고 `AGENT.md §보고 형식` 문자열을 포함하지 않는다:
  1. 프레임워크는 게이트 3종과 세션 첫 응답 외의 보고 형식을 규정하지 않는다는 사실
  2. 게이트 3종 양식의 소유자 포인터 — `opal-harness-semi-agentic.md` §10
  3. 세션 첫 응답의 소유자 포인터 — 본 문서 §15
- 권장 문안(EXECUTE 워커가 그대로 사용 가능):
  `프레임워크는 게이트 3종과 세션 첫 응답 외의 보고 형식을 규정하지 않는다 — 게이트 3종 양식은 `opal-harness-semi-agentic.md` §10이, 세션 첫 응답(부트스트랩 완료 보고 + 메모리 브리핑)은 본 문서 §15가 소유한다. 그 밖의 응답 형식은 자율이다.`
- 결과 절 길이: 헤딩 1 + 공백 1 + 본문 1 = 3줄 (기존 8줄 → 3줄, 5줄 감소).

**(2) `opal-harness-semi-agentic.md:126` — 죽은 포인터 제거**

- Before: `이 3 게이트 보고만 본 양식을 따른다 (§3 모드 경계 / §6 CLOSE 게이트 참조). 게이트 3종 외에는 `` `AGENT.md §보고 형식` ``의 형식 자율성이 유지된다.`
- After 계약: 첫 문장은 불변. 둘째 문장에서 `` `AGENT.md §보고 형식` `` 지목만 제거하고 "게이트 3종 외에는 형식이 자율"이라는 규범 의미를 보존한다.
- 권장 문안: `이 3 게이트 보고만 본 양식을 따른다 (§3 모드 경계 / §6 CLOSE 게이트 참조). 게이트 3종 외의 응답은 형식 자율이다.`
- **[MUST] `:153`·`:186`은 §10.1/§10.2 양식 예시 본문이므로 손대지 않는다** (H-8, TASK.md §범위 「제외 — §10 구판 표기 정정」).

**(3) `docs/ARCHITECTURE.md:59` — Phase A 로드 항목 동기화**

- Before(3번째 컬럼): `` 스킵게이트(setting.json 머지) + identity + PRINCIPLES(헌법) + 보고형식·도구맵·`//` 레지스트리 해석 ``
- After: `` 스킵게이트(setting.json 머지) + identity + PRINCIPLES(헌법) + 도구맵·`//` 레지스트리 해석 ``
- 보존 토큰: `스킵게이트` / `identity` / `PRINCIPLES(헌법)` / `도구맵` / `` `//` 레지스트리 해석 ``. 표의 나머지 3개 컬럼과 `:60` Phase B 행은 불변.

#### 3.2.3 환경 변경

해당 없음.

#### 3.2.4 배치/마이그레이션

해당 없음.

#### 3.2.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-005 | R-7 AC | 산출물 검사 | `docs/ARCHITECTURE.md:59`에 `보고형식` 0건, 보존 토큰 5종 전건 존치 |
| TS-006 | R-2 AC (헤딩 보존) | 산출물 검사 | `grep -c '^## 8\. 보고 형식$' opal-pm.md` = 1 |
| TS-007 | R-2 AC (번호 불변) | 회귀 테스트 | `grep -n '^## 9\.\|^## 1[0-8]\.' `의 §9~§18 헤딩 **제목 문자열 10개**가 `git show HEAD:` baseline과 동일 (줄번호는 §8 축소로 −5 이동해도 무방) |
| TS-008 | R-2 AC (본문 0건) | 산출물 검사 | §8 구간 본문에 `AGENT.md §보고 형식` 0건 |
| TS-009 | R-3 AC | 산출물 검사 | semi-agentic `:126` 해당 줄에 `AGENT.md §보고 형식` 0건, `게이트 3종` 문자열 존치 |
| TS-010 | R-3 과삭제 방지 (H-8) | 회귀 테스트 | `:153`·`:186` 두 줄이 baseline과 문자열 동일 |

---

### F-003: 변경이력 행 추가

#### 3.3.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/AGENT.md` | 에이전트 | 변경이력 표 말미에 `v6.1` 행 추가 | (→ D-3 §변경이력 작성 의무) |
| 2 | `opal/core/references/opal-pm.md` | 가이드 | 변경이력 표 말미에 `v2.6` 행 추가 | (→ D-3 §변경이력 작성 의무) |
| 3 | `opal/core/references/opal-harness-semi-agentic.md` | 가이드 | 변경이력 표 말미에 `v1.7` 행 추가 | (→ D-3 §변경이력 작성 의무) |
| 4 | `docs/ARCHITECTURE.md` | 문서 | 변경이력 표 **첫 데이터 행**(구분선 직후)에 `2026-09-06 HH:mm` 행 삽입 | `docs/ARCHITECTURE.md:496-497` (내림차순 실측) |

#### 3.3.2 설계 (행 포맷 계약)

> **[MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 "## 변경이력" 표에 행을 추가한다." / "일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함 — 예: `(138)`."**

> **[MUST] 일시는 `node ~/.opal/tools/date/date.js datetime`으로 취득한다 (KST, 추측 금지).** — `docs/CONVENTIONS.md:26` 동일 원칙. PLAN 작성 시각 실측값은 `2026-09-06 12:56`이며, EXECUTE 시점에 재취득한다.

| 파일 | 신규 행 |
|------|--------|
| `opal/core/AGENT.md` | `\| v6.1 \| 2026-09-06 HH:mm \| **§보고 형식 절 전면 제거**(177줄, 구 `:185-361`) — 골격 4층·[MUST] 5종·골격 템플릿 3블록·원칙·마크다운 어휘표·「작동하는가」·역할별 응답 표기 표·Observability 선언 스텁 전부 삭제. 대체 규범은 두지 않는다(제거 후 실사용 관찰 → 별건 검토). 부트스트랩 Phase A 능력 서술 2줄(설계 원칙 박스·Phase A 절 머리)에서 「보고 형식」 어절 동기 제거. 파생 참조 동기화: `opal-pm.md` §8 본문 · `opal-harness-semi-agentic.md` §10 머리글 · `docs/ARCHITECTURE.md` 2-tier 표 (108) \|` |
| `opal/core/references/opal-pm.md` | `\| v2.6 \| 2026-09-06 HH:mm \| §8 본문을 소유자 안내 1줄로 교체 — AGENT.md §보고 형식 전면 제거(108)에 따라 죽은 포인터 제거. 게이트 3종은 `opal-harness-semi-agentic.md` §10, 세션 첫 응답은 §15가 소유하며 그 밖은 형식 자율임을 명시. **절 번호·제목 보존**(§9~§18 축자 지목 18건 무성 파손 방지 — 재번호 금지) (108) \|` |
| `opal/core/references/opal-harness-semi-agentic.md` | `\| v1.7 \| 2026-09-06 HH:mm \| §10 머리글의 죽은 포인터 제거 — `AGENT.md §보고 형식` 지목을 삭제하고 「게이트 3종 외의 응답은 형식 자율」 의미만 유지. AGENT.md 절 전면 제거(108) 반영. §10 양식 3종 본문·예시는 불변 (108) \|` |
| `docs/ARCHITECTURE.md` | `\| 2026-09-06 HH:mm \| **부트스트랩 2-tier 표 Phase A 로드 항목에서 「보고형식」 제거** — `opal/core/AGENT.md` §보고 형식 절 전면 제거(177줄)에 따른 서술 동기화. 스킵게이트·identity·PRINCIPLES·도구맵·`//` 레지스트리 해석 항목은 존치 (Task 108) \|` (※ **표 첫 데이터 행에 삽입** — 이 표는 내림차순) |

#### 3.3.3 환경 변경

해당 없음.

#### 3.3.4 배치/마이그레이션

해당 없음.

#### 3.3.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-011 | R-4 AC (정정 적용) | 산출물 검사 | 3파일(AGENT.md·opal-pm.md·semi-agentic.md)의 변경이력 표 **마지막 행**과 ARCHITECTURE.md의 **첫 데이터 행**에 `(108)`/`(Task 108)`과 `2026-09-06`이 포함된다 |

---

### F-004: install 재배포 및 배포본 검증

#### 3.4.1 파일 변경 계획

**신규 생성 / 수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| - | `scripts/install-mac.sh` | 배치 | **수정 없음** — 실행만 한다 | `scripts/install-mac.sh:1218`, `:1748-1750` |

#### 3.4.2 설계 (실행 계약)

**M-1. 실행 주체·배치 판정 — TEST 단계 / PM 직접 / 대화형 터미널**

| 축 | 판정 | 근거 |
|----|------|------|
| 단계 | **TEST** (EXECUTE 아님) | install은 코드 루트(worktree)를 변경하지 않는다. 산출물은 전역 `~/.opal/`이며, 이는 EXECUTE의 `changed_files` 계약 밖이다. R-5 AC 5건(a~e)이 전부 배포본 검증이므로 성격상 검증 단계에 속한다 |
| 주체 | **PM 직접** (워커 디스패치 아님) | ⑴ 워커 Bash는 stdin이 tty가 아니므로 `[[ ! -t 0 ]]`가 참이 되어 메뉴를 건너뛰고 `install_opal` + **`install_mcp`**를 실행한다(`scripts/install-mac.sh:2192-2197`) — MCP 서버 재설정은 태스크 범위 밖 부수효과다. ⑵ `install_opal()`이 `~/.opal/` 6개 디렉토리를 `rm -rf` 후 재생성한다(`:1205-1214`) — 비가역 전역 행동. ⑶ `.opal/AGENT.md` §금지사항 「사용자 승인 없는 코드 생성·수정 금지」의 취지상 전역 배포는 소유자 가시 행동이어야 한다 |
| 방법 | **대화형 터미널에서 메뉴 [1]** | 메뉴 [1]은 `install_opal`만 실행한다(`:2225-2229`). tty가 있어야 메뉴 분기에 도달한다(`:2221`) |
| 실행 경로 | **`{코드 루트}/scripts/install-mac.sh`** | `FRAMEWORK_ROOT = dirname(스크립트 디렉토리)` (`:103-106`) — 허브 스크립트를 실행하면 main 내용이 배포되어 이번 변경이 반영되지 않는다. **[MUST] worktree 안의 스크립트를 실행한다** |

실행 명령:

```bash
# 캡틴/PM 대화형 터미널에서:
/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_108/scripts/install-mac.sh
# → 배너의 "프레임워크 루트: .../.opal-worktrees/task_108" 확인 후 메뉴 [1] 선택
```

**배포 기대 산출**

| 배포본 | 기대값 | 산식 |
|--------|--------|------|
| `~/.opal/AGENT.md` | **184줄** | 현재 361줄 − 177줄. (TASK.md의 360→183은 사실오류 — M-4) |
| `~/.opal/references/opal-pm.md` | 본문에 `AGENT.md §보고 형식` 0건 + §8 헤딩 존치 + §9~§18 헤딩 불변 | strip은 변경이력만 절단 |
| `~/.opal/references/opal-harness-semi-agentic.md` | 본문에 `AGENT.md §보고 형식` 0건 | 〃 |
| `docs/ARCHITECTURE.md` | **배포 대상 아님** — 소스 측에서만 검증 | install에 `docs/` 배포 지점 0건 (M-4 (c)) |

**M-3. 잔존 0 판정 — 변경이력 절 제외 방법**

소스 판정 시 아래 헬퍼로 `## 변경이력` 이후를 잘라낸 뒤 grep한다. **install의 strip 식(`scripts/install-mac.sh:226`)과 동일한 awk 표현식**이므로 소스 본문 판정과 배포본 판정이 정확히 같은 경계를 쓴다.

```bash
body() { /usr/bin/awk 'BEGIN{k=1} /^## 변경이력$/{k=0} k==1{print}' "$1"; }
```

배포본은 이미 strip 되어 있으므로 헬퍼 없이 파일 전체를 grep한다.

#### 3.4.3 환경 변경

해당 없음 (install이 `~/.opal/` 전역을 재배포하나 신규 패키지·설정 추가는 없다).

#### 3.4.4 배치/마이그레이션

`scripts/install-mac.sh` 1회 실행. 롤백 경로 — main 체크아웃 상태의 허브 스크립트를 재실행하면 배포본이 원복된다.

#### 3.4.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-012 | R-5 AC (a) | 산출물 검사 | `grep -c '### 보고 형식' ~/.opal/AGENT.md` = 0 |
| TS-013 | R-5 AC (b) — 정정 | 산출물 검사 | `wc -l < ~/.opal/AGENT.md` = **184** (TASK.md 183은 사실오류) |
| TS-014 | R-5 AC (c) | 산출물 검사 | 배포본 3파일에서 `AGENT.md §보고 형식` 0건 |
| TS-015 | R-5 AC (d) | 회귀 테스트 | 배포본 `~/.opal/references/opal-pm.md`의 §9~§18 헤딩 10개가 소스 본문·baseline과 동일 |
| TS-016 | R-5 AC (e) — 정정 | 산출물 검사 | 배포본 `~/.opal/AGENT.md` 부트스트랩 구간(1~50행)에 `보고 형식` 0건 **+ 소스** `docs/ARCHITECTURE.md:59`에 `보고형식` 0건 (ARCHITECTURE.md는 배포 대상 아님) |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001, F-003 | 1 | `opal-task-agent` | 디스패치 A (단독) | `opal/core/AGENT.md` 1파일 — R-1·R-6·R-4가 같은 파일을 건드리므로 **분할 금지**, 순차 편집 |
| 1 | F-002, F-003 | 2, 3, 4 | `opal-task-agent` | 디스패치 B (Step 2·3·4 순차, 디스패치 A와 병렬) | 산출 3파일 — `pm/dispatch-process.md` Step 6 산출량 상한(3개) 준수 |
| 2 | F-004 | 5 | **PM 직접** | 순차 (Phase 1 전건 완료 후) | 대화형 터미널 메뉴 [1] — 워커 디스패치 금지(M-1) |

> **디스패치 분할 근거**: 단일 디스패치 산출 파일 3개 초과 시 비중첩 분할, 동일 파일을 2개 이상 Step이 변경하면 같은 디스패치에 묶어 순차 편집(후행 저장이 선행 편집을 덮는 충돌 방지). 디스패치 A는 1파일, 디스패치 B는 3파일로 둘 다 상한 내이며 파일 집합이 비중첩이라 병렬 가능하다.

### 4.2 실행 체크리스트

> 총 5개 Step | Phase 2개 | 실행 모드: 복잡

#### Step 0 (선행): baseline 스냅샷

Step 1 착수 전 PM 또는 워커가 1회 실행한다. 회귀 판정(TS-003·TS-007·TS-010)의 비교 기준이다.

```bash
WT=/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_108
mkdir -p /tmp/task108-baseline
git -C "$WT" show HEAD:opal/core/AGENT.md                              > /tmp/task108-baseline/AGENT.md
git -C "$WT" show HEAD:opal/core/references/opal-pm.md                 > /tmp/task108-baseline/opal-pm.md
git -C "$WT" show HEAD:opal/core/references/opal-harness-semi-agentic.md > /tmp/task108-baseline/semi-agentic.md
grep -n '^## ' /tmp/task108-baseline/opal-pm.md > /tmp/task108-baseline/pm-headings.txt
```

#### Step 1: `opal/core/AGENT.md` — §보고 형식 절 삭제 + Phase A 서술 2줄 동기화 + 변경이력

- [ ] 완료
- **소속 기능**: F-001, F-003
- **영역**: 에이전트
- **agent**: `opal-task-agent`
- **파일**: `/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_108/opal/core/AGENT.md`
- **작업 내용**:
  1. `grep -n '^### 보고 형식$\|^## 변경이력$' `로 절 경계를 재확인한다 (기대: 185, 362).
  2. `### 보고 형식`(`:185`)부터 `## 변경이력`(`:362`) 직전 행까지 **177줄을 삭제**한다. 하위 역할별 응답 표기 표(`:351-357`)·Observability 선언 스텁(`:359-360`) 포함. 코드펜스 3쌍(`:240/270`, `:273/283`, `:288/291`)이 절 안에 있으므로 펜스 짝이 끊기지 않는지 확인한다.
  3. `:7`(설계 원칙 박스)에서 `보고 형식·` 어절만 제거. 보존: `도구·MCP 인지맵`, `` `//` 커맨드/스킬 레지스트리 해석 ``.
  4. `:19`(Phase A 절 머리 인용)에서 동일 처리.
  5. `node ~/.opal/tools/date/date.js datetime`으로 KST 일시를 취득하고, 변경이력 표 **말미**에 `v6.1` 행을 추가한다 (문안: §3.3.2 표).
- **완료 기준**: 총 217줄. 본문(변경이력 절 제외)에 `### 보고 형식`·`🎯 결론`·`📌 추가 검토 사항`·`▶️ 승인 요청`·`마크다운 어휘`·`역할별 응답 표기` 0건. `### 기억과 학습`·`## 변경이력` 헤딩 존치. `:7`·`:19`에 `보고 형식` 0건 + 보존 토큰 2종 각 2건. 변경이력 마지막 행에 `(108)`·`2026-09-06` 포함.
- **테스트**: TS-001, TS-002, TS-003, TS-004, TS-011
- **실행 방법**: sub-agent
- **의존**: 없음 (Step 0 baseline 선행 권장)

#### Step 2: `opal/core/references/opal-pm.md` — §8 본문 교체(번호 보존) + 변경이력

- [ ] 완료
- **소속 기능**: F-002, F-003
- **영역**: 가이드
- **agent**: `opal-task-agent`
- **파일**: `/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_108/opal/core/references/opal-pm.md`
- **작업 내용**:
  1. `grep -n '^## ' `로 §8~§18 헤딩 위치를 기록한다 (변경 전 baseline).
  2. §8 본문 `:102`(설명 1줄)과 `:104-107`(인용 블록 4줄)을 §3.2.2 (1)의 안내 1줄로 교체한다. **헤딩 `## 8. 보고 형식`(`:100`), 공백 `:101`, 절 종료 공백·구분선(`:108-109`)은 보존.**
  3. **[MUST] §9~§18 헤딩을 재번호하지 않는다** — 절 삭제 금지, 번호·제목 문자열 불변.
  4. 변경이력 표 **말미**에 `v2.6` 행 추가 (문안: §3.3.2 표).
- **완료 기준**: `grep -c '^## 8\. 보고 형식$'` = 1. §9~§18 헤딩 제목 10개가 baseline과 동일. §8 본문에 `AGENT.md §보고 형식` 0건. 변경이력 마지막 행에 `(108)`·`2026-09-06`.
- **테스트**: TS-006, TS-007, TS-008, TS-011
- **실행 방법**: sub-agent
- **의존**: 없음 (Step 1과 병렬 — 파일 비중첩)

#### Step 3: `opal/core/references/opal-harness-semi-agentic.md` — `:126` 죽은 포인터 제거 + 변경이력

- [ ] 완료
- **소속 기능**: F-002, F-003
- **영역**: 가이드
- **agent**: `opal-task-agent`
- **파일**: `/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_108/opal/core/references/opal-harness-semi-agentic.md`
- **작업 내용**:
  1. `:126` 한 줄만 §3.2.2 (2)의 문안으로 교체한다. 첫 문장(`이 3 게이트 보고만 본 양식을 따른다 (§3 모드 경계 / §6 CLOSE 게이트 참조).`)은 불변.
  2. **[MUST] `:153`·`:186`은 §10.1/§10.2 양식 예시 본문이므로 건드리지 않는다** (H-8). §10 본문·표·예시 전체 불변.
  3. 변경이력 표 **말미**에 `v1.7` 행 추가 (문안: §3.3.2 표).
- **완료 기준**: `:126`에 `AGENT.md §보고 형식` 0건 + `게이트 3종` 문자열 존치. `:153`·`:186` baseline 대비 문자열 동일. 변경이력 마지막 행에 `(108)`·`2026-09-06`.
- **테스트**: TS-009, TS-010, TS-011
- **실행 방법**: sub-agent
- **의존**: 없음 (Step 2와 같은 디스패치 내 순차)

#### Step 4: `docs/ARCHITECTURE.md` — 2-tier 표 Phase A 서술 동기화 + 변경이력(내림차순 첫 행)

- [ ] 완료
- **소속 기능**: F-002, F-003
- **영역**: 문서
- **agent**: `opal-task-agent`
- **파일**: `/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_108/docs/ARCHITECTURE.md`
- **작업 내용**:
  1. `:59` Phase A 행의 3번째 컬럼에서 `보고형식·`만 제거한다. 보존: `스킵게이트(setting.json 머지)`, `identity`, `PRINCIPLES(헌법)`, `도구맵`, `` `//` 레지스트리 해석 ``.
  2. `:60` Phase B 행과 `:62-65` 불릿 4개는 불변.
  3. 변경이력 표가 **내림차순**임을 확인하고(구분선 `:496` 직후 `:497`이 최신 2026-09-03), 신규 행을 **구분선 직후 = 새 첫 데이터 행**으로 삽입한다 (문안: §3.3.2 표).
- **완료 기준**: `:59`에 `보고형식` 0건 + 보존 토큰 5종 전건 존치. 변경이력 표 첫 데이터 행에 `2026-09-06`·`(Task 108)` 포함하고, 그 다음 행이 기존 `2026-09-03 13:15` 행이다.
- **테스트**: TS-005, TS-011
- **실행 방법**: sub-agent
- **의존**: 없음 (Step 2·3과 같은 디스패치 내 순차)

> **docs/ 갱신 Step 판정**: 본 Step 4가 `docs/ARCHITECTURE.md` 갱신 Step에 해당한다(시스템 구조 서술 변경 → ARCHITECTURE.md). 다만 R-7이 요구사항으로 명시되어 있어 워커 작업 범위이며, 별도 PM 직접 Step을 신설하지 않는다. `docs/CONVENTIONS.md`·`docs/PROJECT.md`는 이번 변경으로 갱신 대상이 되지 않는다 — 새 패턴·규칙 도입이 없고 문서 레지스트리 구성도 불변이다.

#### Step 5: install 재배포 및 배포본 검증 (R-5)

- [ ] 완료
- **소속 기능**: F-004
- **영역**: 배치
- **agent**: **PM 직접** (워커 디스패치 금지 — M-1)
- **파일**: `/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_108/scripts/install-mac.sh` (실행 전용, 수정 없음) → 산출: `~/.opal/AGENT.md`, `~/.opal/references/opal-pm.md`, `~/.opal/references/opal-harness-semi-agentic.md`
- **작업 내용**:
  1. Step 1~4 완료 및 §5 소스 QA 전건 통과를 확인한다.
  2. **캡틴에게 전역 배포 승인을 받는다** — install은 병합 전 브랜치 내용을 전역 `~/.opal/`에 배포하고 6개 디렉토리를 `rm -rf` 후 재생성한다(H-5).
  3. 대화형 터미널에서 `{코드 루트}/scripts/install-mac.sh`를 실행하고, 배너의 `프레임워크 루트:`가 `.opal-worktrees/task_108`인지 확인한 뒤 **메뉴 [1]**을 선택한다.
  4. §5.2 배포본 검증 명령 5종을 실행한다.
- **완료 기준**: TS-012~TS-016 전건 Pass. 특히 `wc -l < ~/.opal/AGENT.md` = **184** (183 아님).
- **테스트**: TS-012, TS-013, TS-014, TS-015, TS-016
- **실행 방법**: direct (PM, 대화형 tty)
- **의존**: Step 1, 2, 3, 4

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 ∥ (Step 2·3·4) | 대상 파일 집합이 비중첩 — Step 1은 `opal/core/AGENT.md` 단독, Step 2~4는 나머지 3파일. 서로의 편집 결과를 입력으로 쓰지 않는다 |
| Step 1 내부 순차 (삭제 → `:7`/`:19` → 변경이력) | 동일 파일 3회 편집. R-1·R-6·R-4가 같은 파일을 건드리므로 분할하면 후행 저장이 선행 편집을 덮는다 |
| Step 2 → Step 3 → Step 4 (같은 디스패치 내 순차) | 파일은 독립이나 단일 디스패치 산출량 상한(3개)에 맞춰 한 워커가 순차 처리 |
| (Step 1~4) → Step 5 | install은 소스 최종본을 배포한다 — 전건 완료 전 실행하면 부분 반영본이 전역으로 나간다 |
| Step 5는 워커와 병렬 불가 | 전역 `~/.opal/` 재생성 중 워커가 `~/.opal/` 자산(스킬·도구)을 읽으면 경합한다 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | §보고 형식 절 완전 제거 | TS-001, TS-002 | 본문 잔존 문자열 6종 전건 0 |
| F-001 | 무손상 — 인접 절·총 줄 수 | TS-003 | 217줄, 인접 헤딩 2종 존치, 헤딩 목록이 baseline 마이너스 삭제 구간과 일치 |
| F-001 | Phase A 능력 서술 동기화 | TS-004 | 2줄에 `보고 형식` 0건, 보존 토큰 2종 각 2건 |
| F-002 | ARCHITECTURE 2-tier 표 동기화 | TS-005 | `:59` `보고형식` 0건, 보존 토큰 5종 존치 |
| F-002 | opal-pm §8 번호·제목 보존 | TS-006, TS-007 | §8 헤딩 1건, §9~§18 제목 10개 baseline 동일 |
| F-002 | opal-pm §8 본문 포인터 제거 | TS-008 | §8 본문 `AGENT.md §보고 형식` 0건 |
| F-002 | semi-agentic 죽은 포인터 제거 | TS-009 | `:126` 지목 0건, 규범 의미 존치 |
| F-002 | semi-agentic 과삭제 방지 | TS-010 | `:153`·`:186` 문자열 불변 |
| F-003 | 변경이력 4파일 기록 | TS-011 | 3파일 말미 + ARCHITECTURE 첫 데이터 행, 각 `(108)`·`2026-09-06` |
| F-004 | 배포본 잔존 0 | TS-012, TS-014 | 배포본 3파일 지목·헤딩 0건 |
| F-004 | 배포본 채택·무손상 | TS-013, TS-015 | 184줄, §9~§18 헤딩 동일 |
| F-004 | 배포본 서술 정합 | TS-016 | 배포본 부트스트랩 구간 + 소스 ARCHITECTURE `:59` 0건 |

### 5.2 검증 명령 (실행 가능 형태)

**공통 프롤로그**

```bash
WT=/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_108
BL=/tmp/task108-baseline
body() { /usr/bin/awk 'BEGIN{k=1} /^## 변경이력$/{k=0} k==1{print}' "$1"; }   # install:226과 동일 식
```

**소스 검증 (Step 1~4 완료 후 / EXECUTE 게이트)**

```bash
# TS-001 — §보고 형식 헤딩 0건 (본문)
body "$WT/opal/core/AGENT.md" | grep -c '^### 보고 형식$'                      # 기대 0

# TS-002 — 삭제 대상 문자열 0건 (본문, 변경이력 절 제외)
body "$WT/opal/core/AGENT.md" \
  | grep -cE '🎯 결론|📌 추가 검토 사항|▶️ 승인 요청|마크다운 어휘|역할별 응답 표기'   # 기대 0

# TS-003 — 무손상: 총 줄 수 + 인접 헤딩 + 헤딩 목록 회귀
wc -l < "$WT/opal/core/AGENT.md"                                              # 기대 217
grep -c '^### 기억과 학습$' "$WT/opal/core/AGENT.md"                           # 기대 1
grep -c '^## 변경이력$'     "$WT/opal/core/AGENT.md"                           # 기대 1
diff <(grep -o '^#\{1,4\} .*' "$BL/AGENT.md" \
        | grep -vE '^### 보고 형식$|^## 🎯 결론$|^## 📌 추가 검토 사항$|^## ▶️ 승인 요청$') \
     <(grep -o '^#\{1,4\} .*' "$WT/opal/core/AGENT.md")
# 기대: 차이 없음. baseline 헤딩 25개 − 삭제 구간 5개(`### 보고 형식` 1 + 템플릿 예시 헤딩 4) = 20개

# TS-004 — Phase A 능력 서술 2줄
awk 'NR==7||NR==19' "$WT/opal/core/AGENT.md" | grep -c '보고 형식'             # 기대 0
awk 'NR==7||NR==19' "$WT/opal/core/AGENT.md" | grep -c '도구·MCP 인지맵'        # 기대 2
awk 'NR==7||NR==19' "$WT/opal/core/AGENT.md" | grep -cF '`//` 커맨드/스킬 레지스트리 해석'  # 기대 2

# TS-005 — ARCHITECTURE 2-tier 표
grep -n 'Phase A — 비서(Lite)' "$WT/docs/ARCHITECTURE.md" | grep -c '보고형식'  # 기대 0
grep 'Phase A — 비서(Lite)' "$WT/docs/ARCHITECTURE.md" \
  | grep -cE '스킵게이트.*identity.*PRINCIPLES\(헌법\).*도구맵'                  # 기대 1

# TS-006 / TS-007 — §8 헤딩 보존 + §9~§18 번호 불변
grep -c '^## 8\. 보고 형식$' "$WT/opal/core/references/opal-pm.md"             # 기대 1
diff <(grep -o '^## .*' "$BL/opal-pm.md") \
     <(grep -o '^## .*' "$WT/opal/core/references/opal-pm.md")                 # 기대: 차이 없음

# TS-008 — §8 본문 포인터 제거
awk '/^## 8\. 보고 형식$/{f=1} /^## 9\./{f=0} f' "$WT/opal/core/references/opal-pm.md" \
  | grep -c 'AGENT.md §보고 형식'                                              # 기대 0

# TS-009 — semi-agentic 죽은 포인터 제거
body "$WT/opal/core/references/opal-harness-semi-agentic.md" | grep -c 'AGENT.md §보고 형식'  # 기대 0
sed -n '126p' "$WT/opal/core/references/opal-harness-semi-agentic.md" | grep -c '게이트 3종'   # 기대 1

# TS-010 — 과삭제 방지 (§10 양식 예시 2줄 불변)
SA="$WT/opal/core/references/opal-harness-semi-agentic.md"
diff <(sed -n '153p;186p' "$BL/semi-agentic.md") \
     <(grep -F -e '기존 보고 형식 2종을 완전 대체' \
              -e '§보고 형식 인라인 + Eager Step 6.6 제거' "$SA")               # 기대: 차이 없음 (2줄 존치)

# TS-011 — 변경이력 4파일
tail -1 "$WT/opal/core/AGENT.md"                                    | grep -c '(108)'      # 기대 1
tail -1 "$WT/opal/core/references/opal-pm.md"                       | grep -c '(108)'      # 기대 1
tail -1 "$WT/opal/core/references/opal-harness-semi-agentic.md"     | grep -c '(108)'      # 기대 1
awk '/^## 변경이력$/{f=1} f&&/^\| 2026/{print; exit}' "$WT/docs/ARCHITECTURE.md" \
  | grep -c '2026-09-06'                                                                    # 기대 1 (내림차순 첫 행)
```

**배포본 검증 (Step 5 / TEST 게이트)**

```bash
# TS-012 — 잔존 0
grep -c '### 보고 형식' ~/.opal/AGENT.md                                        # 기대 0

# TS-013 — 채택 검증 (정정: 183 아님)
wc -l < ~/.opal/AGENT.md                                                        # 기대 184

# TS-014 — 댕글링 0
grep -c 'AGENT.md §보고 형식' ~/.opal/AGENT.md \
  ~/.opal/references/opal-pm.md ~/.opal/references/opal-harness-semi-agentic.md # 기대 전부 0

# TS-015 — 무손상 (§9~§18 헤딩)
diff <(grep -o '^## .*' "$WT/opal/core/references/opal-pm.md" | grep -v '^## 변경이력') \
     <(grep -o '^## .*' ~/.opal/references/opal-pm.md)                          # 기대: 차이 없음

# TS-016 — 서술 정합
sed -n '1,50p' ~/.opal/AGENT.md | grep -c '보고 형식'                            # 기대 0
grep 'Phase A — 비서(Lite)' "$WT/docs/ARCHITECTURE.md" | grep -c '보고형식'       # 기대 0 (소스 — docs는 배포 대상 아님)
```

### 5.3 회귀 테스트

- [ ] `opal/core/AGENT.md` 코드펜스 짝이 맞는가 — 삭제 구간에 3쌍(6줄)이 있었으므로 펜스 줄 수가 **baseline 8 → 2**여야 한다 (`grep -c '^\`\`\`' `).
- [ ] `opal/core/AGENT.md`의 Lazy 트리거 테이블(`:48~`)·스킬 레지스트리 절(`:68~`)·부트스트랩 완료 보고(`:73~`)·정체성 적용(`:89~`)·핵심 역할(`:101~`)·행동 규칙(`:122~`) 헤딩이 모두 존치하는가.
- [ ] `opal-pm.md` §9~§18 본문(헤딩 아닌 내용)이 §8 편집으로 밀려나거나 잘리지 않았는가 — 파일 총 줄 수가 396 − 5 = **391**인가.
- [ ] `opal-harness-semi-agentic.md` §10 양식 3종(§10.1 `:130` / §10.2 `:166` / §10.3 `:208`) 헤딩이 모두 존치하는가.
- [ ] `docs/ARCHITECTURE.md` 2-tier 표의 Phase B 행(`:60`)과 하위 불릿 4개(`:62-65`)가 불변인가.
- [ ] 배포 후 `~/.opal/skills/`·`~/.opal/tools/`·`~/.opal/agents/`가 정상 재생성되었는가 (install의 `rm -rf` 후 재배포 — H-5). `~/.opal/community-skills/`와 `~/.opal/identity.md`가 보존되었는가.
- [ ] 배포 후 새 세션에서 부트스트랩이 정상 완주하는가 (Phase A 로드 실패 없음).

### 5.4 코드/문서 품질

- [ ] 4파일 모두 변경이력 행이 추가되었는가 (`docs/CONVENTIONS.md` §변경이력 작성 의무).
- [ ] 일시가 `YYYY-MM-DD HH:mm` KST 형식이고 `node ~/.opal/tools/date/date.js datetime`으로 취득했는가 (추측 금지).
- [ ] 버전이 semver 증분인가 (AGENT.md v6.0→v6.1 / opal-pm v2.5→v2.6 / semi-agentic v1.6→v1.7). ARCHITECTURE.md는 버전 컬럼이 없으므로 날짜만.
- [ ] `~/.opal/` 직접 편집이 0건인가 — 모든 편집이 코드 루트 안에서 수행되었는가 (`.opal/AGENT.md` §금지사항 / `docs/CONVENTIONS.md` §배포 경계).
- [ ] Surgical — 삭제 대상 외 인접 절을 "개선"하지 않았는가 (`opal/core/PRINCIPLES.md` §3).
- [ ] `git diff --stat`의 변경 파일이 정확히 4개인가 (그 외 파일 변경 0).

### 5.5 보안

- [ ] 변경 4파일에 하드코딩된 토큰·시크릿·개인 식별자가 유입되지 않았는가 (변경이력 문안 포함).
- [ ] `.env`·인증 파일이 스테이징에 포함되지 않았는가 (`git status --short` 확인).
- [ ] install 실행 시 `OPAL_HOME_OVERRIDE`를 사용하지 않았는가 — 비표준 `OPAL_HOME` 경로 배포 방지 (`scripts/install-mac.sh:1195-1203`).
- [ ] **[MUST] git 이력 변경 금지** — `git commit`·`git push`·`git reset`·`git rebase` 미실행. 변경은 워킹트리에 남긴다 (`opal/core/references/opal-harness.md` §1 커밋 규칙).

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 5개 (+ baseline 선행 1) | 단순 |
| 변경 파일 수 | **4개** | **복잡** |
| 모듈 범위 | **다중** — `opal/core/`(에이전트) / `opal/core/references/`(가이드 2) / `docs/`(문서) / 전역 배포 | **복잡** |
| 작업 유형 | 제거형 개선 (신규 개발 아님) | 단순 |
| 외부 의존성 | 없음 (새 패키지·API·도구 없음). 단 **전역 배포 부수효과** 존재 | 단순 |
| **실행 모드** | **복잡** | 「하나라도 복잡 기준 해당 시 복잡 모드」 |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

```
Batch 0 (PM 직접, 즉시)
  └─ baseline 스냅샷 (git show HEAD → /tmp/task108-baseline/)

Batch 1 (병렬 2 디스패치)
  ├─ 디스패치 A : opal-task-agent  ── Step 1 (opal/core/AGENT.md)               [산출 1파일]
  └─ 디스패치 B : opal-task-agent  ── Step 2 → Step 3 → Step 4 (순차)            [산출 3파일]
       Step 2: opal/core/references/opal-pm.md
       Step 3: opal/core/references/opal-harness-semi-agentic.md
       Step 4: docs/ARCHITECTURE.md

Batch 2 (PM 게이트)
  └─ 소스 QA §5.2 「소스 검증」 11블록 실행 → 전건 Pass 시 진행

Batch 3 (PM 직접, tty 필요 — 워커 금지)
  └─ Step 5 : install-mac.sh 메뉴 [1] 실행 → §5.2 「배포본 검증」 5블록
```

**그룹핑 근거**
1. **파일 충돌 방지** — `opal/core/AGENT.md`를 R-1·R-6·R-4가 함께 수정하므로 반드시 단일 에이전트(디스패치 A)에 배치한다. 3요구사항을 별도 디스패치로 쪼개면 후행 저장이 선행 편집을 덮는다.
2. **산출량 상한** — 디스패치 B의 산출 3파일은 상한(3개) 경계값이다. 4파일을 한 디스패치에 넣으면 상한 위반이므로 A/B 분할이 강제된다.
3. **병렬 극대화** — A와 B의 파일 집합이 비중첩이라 동시 실행 가능하다.

### C-2. 스킬 요구사항

| 대상 | 스킬 | 판정 |
|------|------|------|
| Step 1~4 | `op-dev-execute` (기존) | 기존 스킬로 충분 — 순수 md 편집이며 신규 패턴 없음 |
| Step 5 | 없음 (PM 직접 절차) | 스킬 신설 불필요. install 실행은 1회성이며 `docs/CONVENTIONS.md` §배포 경계가 이미 절차를 규정한다 |

**갭 판별**: 동일 패턴(「절 삭제 + 파생 참조 동기화 + 변경이력 + 재배포」)이 4개 Step에 걸치나, 이는 파일별 반복일 뿐 새 절차가 아니다 — 인라인 지침(§3 편집 계약)으로 충분하며 스킬 후보 아님.

### C-3. 도구 요구사항

| 도구 | 용도 | 신규 설치 |
|------|------|----------|
| `grep` / `awk` / `sed` / `wc` / `diff` (BSD, macOS 기본) | 위치 특정 · 본문 절단 · 검증 판정 | 불필요 |
| `git show` | baseline 스냅샷 | 불필요 |
| `node ~/.opal/tools/date/date.js datetime` | KST 일시 취득 (추측 금지) | 불필요 |
| `scripts/install-mac.sh` | 전역 배포 (**tty 필요** — 메뉴 [1]) | 불필요 |

**주의**: `body()` 헬퍼는 `/usr/bin/awk`를 명시한다 — install의 strip과 동일 바이너리·동일 식을 써야 경계 판정이 일치한다 (`scripts/install-mac.sh:226`).

### C-4. 테스트 전략

동적 테스트 대상이 아니다 — 전 검증이 **산출물 검사(grep/wc/diff)**다. 이 형식을 판정하는 lint·validate 게이트가 프로젝트에 0건이므로 자동 테스트 스위트가 없다.

| 계층 | 실행 시점 | 내용 | 실행 주체 |
|------|----------|------|----------|
| L1 소스 검증 | Step 1~4 완료 직후 | §5.2 「소스 검증」 TS-001~TS-011 | PM (EXECUTE 게이트) |
| L1 회귀 | 동상 | §5.3 회귀 항목 1~5 | PM |
| L2 배포 검증 | Step 5 직후 | §5.2 「배포본 검증」 TS-012~TS-016 | PM (tty) |
| L2 배포 무손상 | Step 5 직후 | §5.3 회귀 항목 6~7 (전역 자산 재생성·새 세션 부트스트랩) | PM |
| L3 행동 관찰 | CLOSE 이후 | H-4 회귀 관찰 — 이번 태스크 검증 범위 밖, 후속 이월 | 캡틴 |

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 프레임워크 SSOT | Markdown (에이전트·참조 문서·프로젝트 문서) | `op-dev-execute` |
| 배포 어댑터 | Bash (`scripts/install-mac.sh`) | 없음 (PM 직접 실행) |
| 검증 | `grep` / `awk` / `wc` / `diff` (BSD coreutils) | 없음 (동적 테스트 대상 아님) |

> React·Python·shadcn 등 op-dev-plan Step 2의 추천 스킬 테이블 항목은 이번 스택에 해당 없음 — Read 대상 없음.

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| 없음 | 외부 라이브러리·컴포넌트 조회가 필요 없는 순수 프레임워크 문서 태스크 |

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | AGENT.md (OPAL 코어) | `opal/core/AGENT.md` | 제거 대상 절의 SSOT — 절 경계 `:185-361`, Phase A 서술 `:7`·`:19`, 변경이력 `:362` |
| D-2 | 소스 | opal-pm.md | `opal/core/references/opal-pm.md` | §8 파생 참조 `:100-107` + §9~§18 헤딩 보존 대상 `:111~:367` |
| D-3 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | §변경이력 작성 의무(`:245-249`) · §배포 경계(`:251-256`) · 변경이력 표 포맷(`:129-142`) |
| D-4 | 소스 | opal-harness-semi-agentic.md | `opal/core/references/opal-harness-semi-agentic.md` | `:126` 댕글링 참조 + §10 게이트 양식 소유자(`:124-247`) + 과삭제 금지 구간 `:153`·`:186` |
| D-5 | 설계 | ARCHITECTURE.md | `docs/ARCHITECTURE.md` | 부트스트랩 2-tier 표 Phase A 행 `:59` + 변경이력 내림차순 실측 `:493-497` |
| D-6 | 설계 | OPAL 헌법 (PRINCIPLES.md) | `opal/core/PRINCIPLES.md` | §3 Surgical Changes(`:31-35`) · Core Stance "Enforce, don't just advise"(`:15`) |
| D-7 | 소스 | install 어댑터 | `scripts/install-mac.sh` | strip 식 `:226`·`:235` / AGENT.md 배포 `:1218` / references 재귀 strip `:1748-1750` / `rm -rf` 선행 `:1205-1214` / FRAMEWORK_ROOT 결정 `:103-106` / 비대화형 게이트 `:2192-2197` / 메뉴 [1] `:2225-2229` |
| D-8 | 설계 | 프로젝트 AGENT.md (PM 검토 기준) | `.opal/AGENT.md` | §금지사항 `:59-66` — `~/.opal/` 직접 편집 금지 · 변경이력 누락 금지 |
| D-9 | 설계 | lean core 이관 이익의 전제 조건 | `.opal/brain/pages/concept/lean-core-relocation-benefit-precondition.md` | 099 이관 경로 기각 이력 — 전 tier 공통 규범 분리는 순이익 0/음수. 이번 태스크가 이관이 아니라 폐지를 택한 근거 |
| D-10 | 설계 | 템플릿 우위 법칙 | `.opal/brain/pages/concept/template-precedence-over-prose-norms.md` | 템플릿 3/3 vs 산문 0/3 대조 실험 — 제거 후 행동 회귀 예측 근거 (H-4) |
| D-11 | 설계 | 인용 규칙 | `opal/core/references/harness/citation-rules.md` | §2 인용 포맷 · §2.4 [MUST] 포맷 · §9 (f) 결정은 등급 판정 대상 아님 |
| D-12 | 기획 | TASK.md | `tasks/108-260906-opds-보고형식-전면제거/TASK.md` | 요구사항 R-1~R-7 · 확정된 설계 방향 · 제약 조건 |

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | 절 경계 오삭제로 인접 절·변경이력 파손 (H-1) | F-001 | P0 | 경계 앵커(`^### 보고 형식$` / `^## 변경이력$`) 기반 삭제 + 총 줄 수 217 판정 + 인접 헤딩 존치 확인 (TS-003) |
| R-2 | `opal-pm.md` §9~§18 재번호로 축자 지목 18건 무성 파손 (H-2) | F-002 | P0 | 헤딩 보존 편집 계약 + baseline 대비 `diff` 판정 (TS-007, TS-015). 재번호는 **[MUST] 금지** |
| R-3 | 변경이력 표의 과거 기록을 삭제 대상으로 오인한 과삭제 (H-3) | F-001, F-003 | P1 | 잔존 0 판정을 install strip과 동일 awk 식으로 본문에 한정 (M-3). 변경이력 표 행 수 불변 확인 |
| R-4 | 규범 제거 후 보고 품질 행동 회귀 (H-4) | F-001 | P1 | **차단하지 않는다** — 캡틴 결정에 따른 의도된 관찰. 무규범 3유형(질의 응답·제안/경보·정정)을 후속 관찰 항목으로 CLOSE에 이월 (D-10) |
| R-5 | install 전역 부수효과 — 병합 전 브랜치 배포 + 6개 디렉토리 `rm -rf` + 비-tty 시 MCP 동반 (H-5) | F-004 | P0 | Step 5를 PM 직접·tty·메뉴 [1]로 한정 (M-1). 실행 전 캡틴 승인. CLOSE 시 브랜치 처리 방향 보고. 롤백 = main 스크립트 재실행 |
| R-6 | TASK.md AC 수치 오류로 정상 결과를 실패 오판 (H-6) | F-004 | P2 | 확정 입력 판정에서 `사실오류` 3건 명시 + AC 정정치(184줄 / ARCHITECTURE 첫 행 / docs 미배포)를 TS에 반영 |
| R-7 | ARCHITECTURE 변경이력 정렬축 역전 (H-7) | F-003 | P2 | 구분선 직후 삽입 계약 + 다음 행이 `2026-09-03 13:15`인지 확인 (TS-011) |
| R-8 | semi-agentic §10 양식 예시 과삭제 (H-8) | F-002 | P1 | 편집 대상을 `:126` 1줄로 명시 + `:153`·`:186` 불변 판정 (TS-010) |
| R-9 | Phase A 보존 토큰 동반 삭제 (H-9) | F-001 | P1 | 어절 단위 치환 계약 + 보존 토큰 2종 각 2건 카운트 (TS-004) |
| R-10 | 워커가 허브(`ai-framework/`)를 편집하여 worktree 격리 위반 | F-001~F-003 | P1 | 전 Step의 **파일** 필드를 코드 루트 절대경로로 기재. 완료 후 허브 `git status`에 프레임워크 파일 변경 0건 확인 |

---

## 부록. 문서/코드 불일치 보고 (PM 조치 필요)

`docs/` 및 TASK.md 기재값과 실제 파일 내용이 다른 항목이다. **실제 파일 기준으로 설계했다.**

| # | 문서 기재 | 실측 | 조치 |
|---|----------|------|------|
| 1 | TASK.md §배경 분석: 배포본 AGENT.md 360줄 / R-5 AC(b) 183줄 | 배포본 **361줄** → 목표 **184줄** | PLAN에서 정정 반영 (TS-013). TASK.md 소급 수정은 하지 않음 |
| 2 | TASK.md R-4 AC: "4파일 각각 변경이력 표 **마지막 행**" | `docs/ARCHITECTURE.md`는 **내림차순** — 신규 행은 **첫 데이터 행** | PLAN에서 파일별 삽입 위치 분기 (Step 4, TS-011) |
| 3 | TASK.md R-5 AC(e): "배포본 ... `docs/ARCHITECTURE.md:59`" | install은 `docs/`를 배포하지 않음 (배포 지점 0건) | ARCHITECTURE 검증을 소스 측 단독으로 재배치 (TS-016) |
| 4 | TASK.md §범위: "`opal-pm.md:100-107`" | 정확 — 헤딩 `:100`, 본문 `:102`·`:104-107` | 확인 완료, 조치 불요 |
| 5 | TASK.md §범위: "`semi-agentic.md:126`" | 정확 | 확인 완료, 조치 불요 |
| 6 | TASK.md §요구사항 R-1: "`AGENT.md:185-361`" | 정확 (177줄) | 확인 완료, 조치 불요 |
| 7 | TASK.md §요구사항 R-7: "`ARCHITECTURE.md:59`" | 정확 | 확인 완료, 조치 불요 |
