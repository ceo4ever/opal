# ANALYSIS: docs/PROJECT.md · docs/CONVENTIONS.md 실측 1:1 대조

> 작성일: 2026-08-11 13:09 KST | opi 최신화 Phase 2 Step C·D·E
> 읽기 전용 — 대상 문서 무수정 | `docs/ARCHITECTURE.md` 제외(별도 보고서)
> 산출 경로: 워커가 하네스 제약으로 파일을 쓰지 못해 **PM이 워커 반환 본문을 그대로 저장**했다.

## 0. 실측 베이스라인

| 항목 | 명령 | 결과 |
|---|---|---|
| 루트 | `ls -1` | `cursor-rules/ dashboard/ docs/ memory/ opal/ scripts/ skills/ tasks/` + `CLAUDE.md GEMINI.md LICENSE README.md VERSION` + `.opal/` |
| 루트 `agents/` | `ls -la agents/` | `No such file or directory` — **부재** |
| 루트 `community-skills/` | `find . -type d -name community-skills` | 0건 — **부재** |
| `opal/` 하위 | `ls -1 opal/` | `agents bootstrapper core skills templates tools` |
| OPAL 스킬 / 에이전트 / 도구 | `ls -1 opal/{skills,agents,tools}/` | **42 / 15 / 18** |
| 독립 스킬 | `ls -1 skills/` | **8종** |
| 태스크 폴더 | `ls -1 tasks/` | 31개, 전부 `{NNN}-{YYMMDD}-{스킬약어}-{한글태스크명}` |

**도구 서브명령 실측** (`run.sh --help` / `code-scan help`)

| 도구 | 개수 | 비고 |
|---|---|---|
| `backlog-tool` | **8** | init/add-task/select-next/mark/update-task/done-check/show/coverage-check |
| `brain-tool` | **10** | help 자체가 "10 서브 명령" — `analyze`·`ingest-scan` 포함 |
| `state-tool` | **11** | init/show/advance/mark/block/validate/add-row/status/gate-pass`[DEPRECATED]`/spec-validate/**verify**. 도구 help 본문은 "10종"이라 자기기술 불일치 |
| `memory-tool` | **9** | PM 기확인과 일치 |
| `test-tool` | **12** | 기본 4 + scenario-* **8** (multi-line `add_parser` 때문에 grep만으로는 8종만 잡힘 — `--help` 필수) |
| `improve-tool` | **3** | |
| `code-scan` | **15** | `code-scan v1.6.0` |

**PM 기확인 검증**: brain-tool 10 ✅ · memory-tool 9 ✅ · code-scan 15 ✅ · **state-tool은 10이 아니라 11**(`verify` 실재).
**`backlog-tool` 7 vs 8 확정**: 도구 실측 **8종** → `PROJECT.md:108`의 "8서브명령"이 **정확**. 하네스 측 7종 표기가 오기재다.

**alias 레지스트리 실측** (`opal-skills-registry.json`) — **27종**:
`opp opd opds opdw opwt opsdd opgc opdd oppd oppl wfb uid wtm erm mockup html-sa onb next help opi osc oac osm opbr opas opws opim`

## 1. 대조 요약

| 문서 | 일치 | 불일치 | 문서에 없음 | 실제에 없음 |
|---|---|---|---|---|
| `docs/PROJECT.md` | 7 | 5 | 6 | 1 |
| `docs/CONVENTIONS.md` | 6 | 8 | 4 | 4 |
| **합계** | **13** | **13** | **10** | **5** |

**심각도 상위 3건**

1. **루트 `agents/` 부재** — 두 문서 6개 지점(`PROJECT.md:37,50,158` · `CONVENTIONS.md:21,71,206`)이 없는 경로를 규범으로 기술. `프로젝트 구성` 표 Framework 경로에까지 들어가 opgc SCAN·PM 컨텍스트 주입에 실제 영향.
2. **태스크 폴더 네이밍 2문서 동시 오기재** — 31개 폴더 전부 날짜 포함인데 두 문서 모두 날짜 없는 구형 규칙 + 실존하지 않는 예시.
3. **PROJECT.md에 dev 파이프라인 섹션 자체 부재** — 주력 opd/opds/opdw/opwt/opp/oppd가 주요 컴포넌트 8섹션 어디에도 없음.

## 2. docs/PROJECT.md — 불일치·누락

### 2.1 불일치

| # | 위치 | 문서 표기 | 실측값 | 근거 | 갱신 제안 |
|---|---|---|---|---|---|
| P-1 | `:37` | `agents/` \| 에이전트 소스 | 루트 `agents/` 없음 | `ls -la agents/` | 행 삭제 → `opal/agents/`(15종) 행 신설 |
| P-2 | `:35` | `tasks/` = `{NNN}-{설명}/` | `{NNN}-{YYMMDD}-{스킬약어}-{태스크명}` | `ls -1 tasks/`; SSOT `harness/task-process.md:25` | 형식 교체 |
| P-3 | `:47` | `{NNN}-{스킬약어}-{설명}/` · 예시 `066-opp-orchestrator-skill-gate/`, `062-opp-opwt-external-refs/` | 실제 066 = `066-260717-opd-루프액션-opal-agent-채널`; 예시 2건 부재 | `ls -d tasks/052* tasks/055* tasks/066*` | 규칙+예시 동시 교체 |
| P-4 | `:50` | `agents/` "현재 비어있음" | 비어있는 게 아니라 디렉토리 부재 | 위와 동일 | 행 삭제 |
| P-5 | `:81` | `brain-tool` (**8 서브명령**) | **10** | `brain-tool/run.sh --help` | `8`→`10`, `analyze`/`ingest-scan` 명시 |

### 2.2 실제에 없음

| # | 위치 | 표기 | 실측 | 제안 |
|---|---|---|---|---|
| P-6 | `:158` §프로젝트 구성 | Framework 경로 = `opal/`, `skills/`, **`agents/`** | `agents/` 부재 | 경로에서 제거 |

*(경미) `:41` `.opal/` 설명 "에이전트/메모리 설정"은 실제 범위(`brain/`·`code-map/`·`code-scan.json`·`MEMORY.json`) 대비 축소 — 서술 확장 권장, 합계 미계상.*

### 2.3 문서에 없음 (실재하나 미기재)

| # | 대상 | 근거 | 제안 |
|---|---|---|---|
| P-8 | 구조맵 누락 폴더: `dashboard/` `cursor-rules/` `memory/` `opal/agents/` `opal/tools/` `opal/bootstrapper/` `opal/templates/` | `ls -1`, `ls -1 opal/` | 행 추가. `dashboard/`는 §프로젝트 구성·§Console엔 있고 구조맵에만 빠져 **문서 내부 모순** |
| P-9 | **dev 파이프라인 섹션 부재** — opd/opds/opdw/opwt/opp/oppd + `op-dev-*` 7종 | `grep "^## " docs/PROJECT.md` → 8섹션에 dev 없음 | **`## 주요 컴포넌트 (Dev 파이프라인)` 신설 — 최우선** |
| P-10 | 미등재 에이전트 10종: be/fe/plan/planning/sdd-action/task-action/task/task-qa/test/wtm-agent | `ls -1 opal/agents/` 15 중 등재 5 | Dev 섹션에 수용 |
| P-11 | 미등재 도구 12종 (+`opal-cli`는 `console`만 부분 등재) | `ls -1 opal/tools/` 18 중 등재 ~6 | §5 E-4 참조 |
| P-12 | 미등재 독립 스킬 8종 | `ls -1 skills/` | alias(wfb/uid/wtm/erm/mockup/html-sa)로 사용자 대면인데 목록 없음 |
| P-13 | 미등록 문서 (아래 2.4) | `find docs -type f` | 레지스트리 행 추가 |

### 2.4 §프로젝트 문서(`:162-172`) 3축 검증 + I-8 승계

| 검증 | 결과 |
|---|---|
| (a) 등록 6건 실재 | ✅ 전부 실재. **`ARCHITECTURE.md` 등록 확인 ✅**(`:168`) |
| (b) 미등록 실재 문서 | ⚠️ 아래 |
| (c) 컬럼 5종 | ✅ **`적용 범위` 컬럼 실재**(`:164`) → Step E 컬럼 추가 조건 **미해당** |

| 파일 | 등록 권장 | 사유 |
|---|---|---|
| `docs/architecture-diagram/opal_framework_architecture.html` | **권장 (I-8 확정)** | 태스크 086 산출물(커밋 `63c0e34`), 구조 시각 SSOT |
| `docs/SECURITY.md` | **권장** | `PROJECT.md:70`이 이미 checker 기준 문서로 참조 중인데 레지스트리 부재 — 내부 모순 |
| `docs/proposals/opal-brain-design.md` | 권장 | `PROJECT.md:83`이 "설계 SSOT"로 명시 참조 |
| `docs/proposals/opal-data-design.md` | 조건부 | 동일 성격 — 동반 등록이 일관 |
| `docs/backup/*.md` (3건) | **보류** | 2026-05-08 스냅샷, 현행 참조 문서 아님 |
| 루트 `CLAUDE.md`·`GEMINI.md` | 조건부 | `.opal/AGENT.md` 등록 대비 대칭성 |

### 2.5 §프로젝트 구성 섹션

**실재 확인**(`:152`), 스키마 `| 요소 | 경로 | 기술 스택 | 전문 에이전트 |`(`:156`) **일치 ✅** → Step E "섹션 신설" 조건 **미해당**. P-6만 교정.

### 2.6 일치 (변경 불요)

`프로젝트 구성` 섹션+스키마 · `프로젝트 문서` 5컬럼 · `ARCHITECTURE.md` 등록 · `backlog-tool` 8서브명령 · `test-tool scenario-*` 8종 · 최근 4종 등재(oppl·evaluator·loop-action·op-scenario-gate) · `code-scan 13→15`.

## 3. docs/CONVENTIONS.md — 불일치·누락

### 3.1 불일치

| # | 위치 | 문서 표기 | 실측값 | 근거 | 갱신 제안 |
|---|---|---|---|---|---|
| C-1 | `:23` | 태스크 폴더 `{NNN}-{스킬약어 또는 대상}-{동작/설명}` · 예시 `055-opi-task-record`, `052-orchestrator-cleanup` | `{NNN}-{YYMMDD}-{스킬약어}-{태스크명}`, 태스크명 **한글 기본** | `ls -1 tasks/`; `harness/task-process.md:25,60,64` | 규칙+예시 교체. "앞 3요소 ASCII 고정, 공백 금지" 명문 승계 |
| C-2 | `:21`, `:71` | `agents/{agent-name}/` — "현재 비어있음" / 구조 블록에 등재 | 디렉토리 **부재** | `ls -la agents/` | 항목·블록 삭제 |
| C-3 | `:206` 배포 경계 | 소스 경로 = `opal/`, `skills/`, **`agents/`**, **`community-skills/`**, `scripts/` | 둘 다 루트 부재 | `find . -type d -name community-skills` → 0건 | 두 경로 제거 |
| C-4 | `:35` 네이밍 체계 | `op-sdd-*` 예시에 **`op-sdd-tasks`** | 부재 — 실재는 spec/verify/plan/action-plan | `ls -d opal/skills/op-sdd-tasks` → 없음 | 예시 교체 |
| C-5 | `:119-123` 브랜치 전략 | `new-dtp-*` 기능 개발 브랜치 · 태스크 완료 후 main 머지 | 최근 25커밋 전부 **main 직접 커밋** | `git branch -a`, `git log --oneline -25` | 실관행 반영 + 예외 시 `feat/{NNN}-...` |
| C-6 | `:188` State 관리 | 서브명령 예에 **`gate-pass`** | 도구 help에 **`[DEPRECATED]`** 명시 | `state-tool/run.sh --help` | `gate-pass` 제거, `block`/`spec-validate` 대체 |
| C-7 | `:195` 도구 우선 원칙 | 등록 도구 예 4종 | 실재 **18종**. 핵심(`code-scan`·`memory-tool`·`brain-tool`·`test-tool`·`backlog-tool`) 전부 누락 | `ls -1 opal/tools/` | 예시 갱신 또는 `opal/tools/` 링크 위임 |
| C-8 | `:20` 에이전트 폴더 | 열거 7종 | 실재 **15종** | `ls -1 opal/agents/` | 열거 확장 또는 위임 |

### 3.2 실제에 없음

C-2(`agents/` 2지점), C-3(`agents/`·`community-skills/`), C-4(`op-sdd-tasks`) — 위 표에 통합, 합계 4건.

### 3.3 문서에 없음

| # | 대상 | 근거 | 제안 |
|---|---|---|---|
| C-9 | **alias 표 18종 누락** — `:40-50`은 9종만 | 레지스트리 alias 27종 | 표 확장 + 레지스트리 SSOT 링크 |
| C-10 | 태스크 산출물 구조에 `state.json`·`AGENTIC-LOG.md`·`GC-*.md` 미기재 | `ls tasks/088-.../`; `tasks/087-.../DONE.md:4` | 구조 블록 보강. `STATE.md`가 `state.json`의 렌더 뷰임을 명시 |
| C-11 | **문서 자체에 `## 변경이력` 절 부재** | `grep -n "변경이력"` → 의무 조항만 존재 | 문서 말미 변경이력 표 신설 (PROJECT.md와 대칭) |
| C-12 | CLOSE 시 메모리 히스토리 자동 생성(088)이 커밋 규칙에 미반영 | `tasks/088-.../DONE.md` §1·§3 | §4 참조 |

### 3.4 일치 (변경 불요) — 하네스 경로·§번호 실증

| 문서 위치 | 참조 | 실측 | 판정 |
|---|---|---|---|
| `:164` | `opal-harness.md` §1 Guards | `8:## 1. Guards (제약)` | ✅ |
| `:169` | §1 디스패치 의무 원칙 | `23:### 디스패치 의무 원칙` | ✅ |
| `:190` | §3 State | `133:## 3. State (상태 관리)` | ✅ |
| `:196` | §9 OPAL Tools | `221:## 9. OPAL Tools (도구)` | ✅ |
| `:177` | `header-rules.md`, `header-standard.md` §7 | `184:## 7. 2소스 표현` | ✅ |
| `:183` | `harness/citation-rules.md` | 실재 | ✅ |
| `:222` | `conventions-hub-model.md` | 실재 | ✅ |

**@header 규칙(`:171-177`) — 일치 ✅** : `headerSource` 단일 키·2택·미설정 시 전 명령 차단 서술이 `code-scan v1.6.0`과 정합.
**언어·네이밍(`:5-12`, `:18`) — 일치 ✅** / **변경이력 규칙(`:92-105`, `:198-202`) — 일치 ✅**

## 4. 최근 태스크 반영 필요성 판정

| 태스크 | 대상 문서·섹션 | 반영 필요 | 사유 |
|---|---|---|---|
| 083 | `PROJECT.md` 변경이력 | **불요** | 이미 기록. `code-scan` 15종 실측 일치 |
| 084 | 두 문서 | **불요(경계)** | 신설물은 `pm/asis-analysis.md` 하네스 참조뿐. 두 문서 모두 개별 하네스 참조를 열거하지 않는 구조 |
| 085 | `CONVENTIONS.md` §배포 경계 | **불요** | 릴리스 스크립트 내부 결함 수정. 규칙 자체 무변경 |
| 086 | `PROJECT.md` §프로젝트 문서 | **필요** | 다이어그램 HTML 레지스트리 미등록 (**I-8**) |
| 087 | 두 문서 | **불요** | `scripts/install*.sh` 내부 변경. 두 문서에 Python 버전 서술 없음 |
| 088 | `CONVENTIONS.md` §커밋 규칙 | **필요** | 아래 상세 |

**088 상세 판정**

- `:151` "하나의 태스크 = 하나의 커밋 (원칙)"은 **문구 자체가 유효하며, 088이 이를 집행 가능하게 만들었다.** 폐기 대상 아님.
- 088 이전 실관행은 태스크당 2커밋이었다. `git log` 실증: `3e44512 chore(087)`, `5d560dc chore(086)`, `d2ee797 chore(085)` — 3연속 히스토리 갱신 별도 커밋.
- 088 이후 `state-tool mark`(CLOSE 마지막 행)가 히스토리 행을 직접 생성하며, `result` 필드만 `"(PM 보강 대기)"` 플레이스홀더로 남는다.
- **갱신 제안**: §커밋 규칙에 1행 추가 — "CLOSE 시 메모리 히스토리 행은 `state-tool mark`가 자동 생성한다(088). PM은 `result` 필드를 보강한 뒤 커밋하며, 히스토리 갱신용 별도 커밋을 만들지 않는다."

## 5. Step E — 새 문서·새 섹션 후보

| # | 후보 | 근거 | 권장/보류 | 사유 |
|---|---|---|---|---|
| E-1 | `PROJECT.md` §프로젝트 구성 신설 | 조건표 | **해당 없음** | `:152` 실재 + 스키마 일치 |
| E-2 | `적용 범위` 컬럼 추가 | 조건표 | **해당 없음** | `:164` 실재 |
| E-3 | **`PROJECT.md` §주요 컴포넌트 (Dev 파이프라인) 신설** | P-9 | **강력 권장** | 주력 오케스트레이터 6종 + `op-dev-*` 7종 + 워커 10종이 SSOT에서 통째로 누락. 기존 8섹션과 동일 스키마 섹션 1개 추가가 최소 변경 |
| E-4 | 도구 인벤토리 섹션 신설 | P-11 | **보류** | 도구는 각 파이프라인 섹션에 분산 등재되는 현행 구조가 일관적. E-3 + C-7 링크 위임으로 해소 |
| E-5 | **`docs/BACKEND.md` 신설** | 조건표(BE 디렉토리 존재) | **비권장** | `dashboard/`는 부속 읽기 전용 대시보드. FastAPI 단일 데몬으로 표면이 좁고, 구조 설명은 `ARCHITECTURE.md §OPAL Console`이 보유, `프로젝트 구성` 표가 경로·스택·에이전트를 이미 매핑. 허브+링크 모델의 "다중 구성" 전제 미달 |
| E-6 | **`docs/FRONTEND.md` 신설** | 조건표(FE 디렉토리 존재) | **비권장** | E-5와 동일 논거. 7화면 단일 SPA, 시그니처 3색이 `:root` CSS 변수로 봉인돼 규칙 표면이 얇음 |
| E-7 | **§프로젝트 문서 레지스트리 4행 추가** | P-13 / I-8 | **권장** | 다이어그램 HTML · `SECURITY.md`(내부 모순 해소) · `proposals/` 2종 |
| E-8 | **`CONVENTIONS.md` 말미 §변경이력 신설** | C-11 | **권장** | PROJECT.md는 보유, CONVENTIONS는 부재 — 동급 SSOT인데 추적성 비대칭 |
| E-9 | `docs/backup/` 3건 등록 | — | **보류** | 2026-05-08 스냅샷. 레지스트리 노이즈 |

## 6. 섹션별 갱신 제안 요약

### docs/PROJECT.md

| 섹션 | 판정 |
|---|---|
| §프로젝트 개요 / §원칙 / §기준 | **변경 없음** |
| §프로젝트 구조 — 폴더 구조맵 `:30-41` | **갱신 필요**: `agents/` 삭제(P-1), `tasks/` 형식(P-2), 누락 7폴더(P-8), `.opal/` 설명 확장 |
| §네이밍 규칙 `:43-51` | **갱신 필요**: tasks 규칙+예시 교체(P-3), `agents/` 삭제(P-4) |
| §주요 컴포넌트 (SDD / GC / Data Design / Project Loop / Console / PM 개선 루프 / 목표-커버 게이트) | **변경 없음** |
| §주요 컴포넌트 (Project Brain) `:73-83` | **갱신 필요**: `brain-tool` 8→**10**(P-5) |
| **(신설) §주요 컴포넌트 (Dev 파이프라인)** | **신설 필요**: E-3 |
| §프로젝트 구성 `:152-160` | **갱신 필요(소폭)**: Framework 경로에서 `agents/` 제거(P-6) |
| §프로젝트 문서 `:162-172` | **갱신 필요**: 4행 추가(E-7 / I-8) |
| §변경이력 `:175-202` | **갱신 필요**: 태스크 089 행 추가 |

### docs/CONVENTIONS.md

| 섹션 | 판정 |
|---|---|
| §언어 규칙 | **변경 없음** |
| §네이밍 규칙 — 파일/폴더 `:16-24` | **갱신 필요**: `agents/` 삭제(C-2), 에이전트 7→15(C-8), 태스크 폴더 규칙+예시(C-1) |
| §컴포넌트 네이밍 체계 `:26-36` | **갱신 필요**: `op-sdd-tasks` 제거(C-4) |
| §약어(Alias) `:38-50` | **갱신 필요**: 9→27종, 레지스트리 SSOT 링크(C-9) |
| §파일 구조 `:54-73` | **갱신 필요**: `agents/{agent-name}/` 블록 삭제(C-2) |
| §YAML Frontmatter / §변경이력(규칙) | **변경 없음** |
| §태스크 산출물 구조 `:107-117` | **갱신 필요**: 폴더 형식 + `state.json`·`AGENTIC-LOG.md`·`GC-*.md`(C-10) |
| §브랜치 전략 `:119-123` | **갱신 필요**: main 직접 커밋 실관행(C-5) |
| §커밋 규칙 `:125-151` | **갱신 필요**: 088 자동 히스토리 1행(C-12) |
| §Guards / §디스패치 의무 / §@header / §Citation / §변경이력 의무 / §플랫폼 분기 / §허브+링크 | **변경 없음** |
| §State 관리 `:185-190` | **갱신 필요**: deprecated `gate-pass` 제거(C-6) |
| §도구 우선 원칙 `:192-196` | **갱신 필요**: 예시 갱신 또는 18종 위임(C-7) |
| §배포 경계 `:204-209` | **갱신 필요**: `agents/`·`community-skills/` 제거(C-3) |
| **(신설) §변경이력** | **신설 필요**: E-8 |

## 7. PM 확정 항목 처리

- **I-8 승계** — 다이어그램 HTML 레지스트리 등록 권장 확정
- **`backlog-tool` 상충 확정** — 도구 실측 **8종** → `PROJECT.md:108`이 정확, 하네스 측 7종이 오기재
- **부수 발견** — `state-tool`은 PM 기재 10종이 아닌 **11종**(`verify`). 도구 자체 help 문구도 "10종"으로 오기재
