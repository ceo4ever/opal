# TEST SCENARIO: @header 자산 스킬 신설 + 하네스 갱신·소비 절차 편입

> 작성일: 2026-09-04 | 상태: **실행 완료** (iteration 2 게이트 pass → TEST 실행 → S-20·S-25 Fail 보강 후 재검증)
> 작성자: PM(알투) 대행 — agentic 모드 | PLAN.md §리스크 가설 표 기반
> RED-first 트랙: **적용** (`harness/red-first.md` §1.5) — `state_tool.py` 게이트 판정 로직은 self-confirming 위험 영역(판정 결과가 곧 통과 근거)이므로 안전측 기본을 택한다. 대상 시나리오 S-9·S-10. `verify --red-check` ON.
> 문서·스킬 산출물 검사 시나리오는 「구현 후 시나리오 검증 허용」 트랙(설정·문서)이다.

## 1. 리스크 가설 표

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | F-002 / `opal-pm.md` §12 표 | "L2 = Gate 미적용" 원칙과 신설 검증 행의 문면 자기모순 | P1 | L1 | S-4 |
| H-2 | F-004 집행 지점 | PreToolUse `Task` hook 0건 + 플랫폼 분기 격리 — hook 경로면 Cursor/Gemini에서 규칙 소멸 | P1 | L1 | S-8 |
| H-3 | 전 F / 개정 8문서 | 변경이력 마커·컬럼 형태 이종 → 잘못된 형태 삽입 시 표 파손 | P2 | L1 | S-18 |
| H-4 | F-004 / `pipeline.json` ×3 | 행 수 변동 시 R-6 AC(a)와 정면 충돌 | P0 | L2 | S-13, S-16 |
| H-5 | F-001 / 레지스트리 | alias 영구 점유 — 중복 시 `skill-registry match` 라우팅 비결정 | P1 | L2 | S-2 |
| H-6 | F-004 / `cmd_advance`·`cmd_mark` 훅 | 발동 반경 — EXECUTE 보유 8 파이프라인에서 훅 무조건 발동 시 기존 태스크 진입 차단 | P0 | L2 | S-15 |
| H-7 | F-004 / `auto_pass` 거부 위치 | 거부를 graceful skip 앞에 두면 문서 전용 태스크에서 오탐 | P0 | L2 | S-11, S-12 |
| H-8 | F-004 / `state_tool.py` | 파일 상단 `@header` 미갱신 → 다음 CLOSE에서 `validate --changed` 자기 차단 | P1 | L2 | S-11 |
| H-9 | F-001 / `docs/CONVENTIONS.md` | 약어 표 결손 2건(`opgr`·`opeli5`) — `opcmb`만 더하면 총계가 또 틀린다 | P2 | L1 | S-2 |
| H-10 | F-004 / 인용 판정 로직 | 토큰 매칭이 실질 인용과 단순 언급을 구분 못해 미탐 또는 오탐 | P1 | L2 | S-9, S-10 |
| H-11 | F-004·F-005 / 배포 경계 | `~/.opal/` 미재배포 상태 실측은 구 배포본이 판정 — 통과·실패 모두 무의미 | P0 | L2 | S-17 |
| H-12 | 부속 / `docs/PROJECT.md`·`ARCHITECTURE.md` | 스킬 수 셀이 실측과 이미 2건 드리프트 — `+1`만 하면 오차 확대 | P2 | L1 | S-19 |

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터

> DB 없음(프레임워크 문서·CLI 도구 태스크). 사전 조건은 파일시스템 fixture다.

| 자원 | 식별자 | 상태 | 출처 |
|------|--------|------|------|
| 임시 태스크 폴더 (인용 0건) | `/tmp/opal-ts106/neg/` | `state.json`(EXECUTE 행 보유) + PLAN.md §4.2에 `.py` 대상·code-scan 인용 토큰 0건 | 수동 생성 (S-9 전용) |
| 임시 태스크 폴더 (인용 1건 이상) | `/tmp/opal-ts106/pos/` | 동일 구조 + PLAN.md §4.2에 `domain`/`layer`/`depends`/`exports` 중 1개 이상 인용 | 수동 생성 (S-10 전용) |
| 임시 프로젝트 트리 (manifest) | `/tmp/opal-ts106/proj/` | 코드 파일 3개 이상 + `.opal/` 없음(초기 상태) | 수동 생성 (S-20 전용) |
| 이 레포 (inline·맵 부재) | `/Volumes/Data/AIStudio/workspace/ai-framework` | `headerSource: inline`, `.opal/code-map/` 부재 | 실환경 그대로 |
| 태스크 106 폴더 (문서 전용) | `tasks/106-260904-opd-코드맵-스킬신설-하네스개정/` | PLAN.md §4.2 대상에 `.py` 1건 포함 | 실환경 그대로 |
| 기존 태스크 폴더 3건 | `tasks/103-…`, `tasks/104-…`, `tasks/105-…` | 완료 상태 `state.json` 보유 | 실환경 그대로 |
| 8 파이프라인 스펙 | `opal/skills/opal-pilot-{dev,dev-short,project,dev-wireframe,project-dev,project-loop,sdd,write-tech}/references/pipeline.json` | 개정 전 스냅샷(`git stash` 또는 `git show HEAD:`) | git |
| 개정 전 배포본 | `~/.opal/tools/state-tool/` | install 이전 상태 | 실환경 |

> `/tmp` 대신 세션 스크래치패드 경로를 사용해도 무방하다. **[MUST]** 임시 자원은 S-11·S-15 관측 종료 후 정리한다(PLAN Step 11 완료 기준 (c)).

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (CUD/호출) | Then (re-read) |
|---------|------------|----------------|---------------|
| S-1 | `opal/skills/` 트리 (`opal-code-map-builder/` 부재) | Step 1 실행 후 SKILL.md 파싱 | frontmatter 5필드 비공백 |
| S-2 | 레지스트리 alias 29종 · CONVENTIONS 표 27종 | Step 2·3 실행 후 `skill-registry get｜match` 호출 | alias 30종 · 중복 0 · 표↔레지스트리 1:1 |
| S-3 | Step 1 산출 SKILL.md | 모드 분기 3항 grep | 2택 제시·manifest 3단·inline 종료 분기 각각 존재 |
| S-4 | `opal-pm.md` §12 유지 4행 / 미적용 5행 | Step 8 실행 후 §12 재판독 | 유지 5행 + 각주 1줄 / 미적용 5행 원문 무변경 |
| S-5 | `header-rules.md` §갱신 시점 (3단) 3행 | Step 7 실행 후 표 재판독 | 제목 (4단) + (d) 행 존재 / (a)(b)(c) 원문 무변경 |
| S-6 | Step 7 산출 (d) 행 | 미수행 탐지 조건 문면 grep | "(b) CLOSE 게이트 `newly_uncovered` 누적" 명시 |
| S-7 | `opal-pm.md` §13 · `dispatch-process.md:126-135` | Step 9·10 실행 후 재판독 | 4열 2행 표 + 전환 조건 + 오버라이드 구분 + 비모순 1줄 / 포인터 1건·원문 복제 0건 |
| S-8 | PLAN.md §3.4 | 후보 비교표 판독 | 후보 3종 + 확정 1종 + 탈락 근거 존재 |
| S-9 | `/tmp/opal-ts106/neg/` (인용 0건) | `verify --code-scan-citation-check` → 이어서 EXECUTE 첫 행 `mark` | `ok:false`·`code_scan_citation_unmet`·exit 1 / `state.json` 무변경 |
| S-10 | `/tmp/opal-ts106/pos/` (인용 1건 이상) | 동일 2호출 | `code_scan_citation_check:"pass"`·exit 0 / `mark` 정상 진행 |
| S-11 | 이 레포 + 태스크 106 폴더 (`.md` 위주) | ① `verify --code-scan-citation-check` ② `.md`만으로 `validate --changed` ③ `validate --changed state_tool.py` | ① `skipped`(`doc_only_task`)·exit 0 ② exit 0 ③ exit 0·`newly_uncovered` 0 / 거부·경고 발화 0건 |
| S-12 | Step 4·6·7 산출물 3종 | 폴백 조건 문면 대조 | 3곳 전건 명시 + 게이트 순서가 판정보다 앞임이 확인 |
| S-13 | 개정 전 3 `pipeline.json` (git) | Step 5 실행 후 `len(task_steps)`·key 집합 대조 | 16/11/9 불변 + `key`·`id`·`stage`·`item` diff 0건 |
| S-14 | 기존 태스크 3폴더 `state.json` | `state-tool show <path>` × 3 | exit 0 · 오류 0건 |
| S-15 | 8 파이프라인 + 임시 태스크 폴더 8종 | 각각 EXECUTE 첫 행 `advance`/`mark` | skip 또는 pass만 · 예기치 않은 거부 0건 · stdout 키 집합 개정 전과 동일 |
| S-16 | 개정 후 3 `pipeline.json` | `state-tool spec-validate` × 3 | violations 0건 |
| S-17 | 개정 전 `~/.opal/` 배포본 | `./scripts/install-mac.sh` 실행 | 배포본에 SKILL.md·`opcmb` 반영 + 신설 플래그 인식 + install 스크립트 diff 0건 + 배포본 변경이력 strip 확인 |
| S-18 | 개정 8문서의 기존 변경이력 형태 | 전 Step 완료 후 마커·컬럼 순서 대조 | 문서별 기존 형태 유지 + 행 1건 추가(`(106)` 포함) |
| S-19 | `docs/PROJECT.md`·`ARCHITECTURE.md` 스킬 수 셀 (실측 44 vs 문서 42) | Step 13 실행 후 `find opal/skills -mindepth 1 -maxdepth 1 -type d｜wc -l` 대조 | 4개 셀 값이 실측 45와 일치 |
| S-20 | `/tmp/opal-ts106/proj/` (`.opal/` 부재) | SKILL.md 기술 시퀀스를 그대로 실행 — `init --header-source manifest --write` → `discover` → 리뷰 → `status: reviewed` → `scaffold` → `validate` | `.opal/code-map/index.json` + 패키지 매니페스트 생성 · `validate` exit 0 · 리뷰 게이트가 소유자 확인을 요구 |
| S-22 | 개정 전 `pm-review-gate.md` 항목 14 (자기판정 문면 보유) | Step 6 실행 후 항목 14 재판독 | 구형 문면 0건 + 신형 판정 수단·집행 지점·스킵 조건 3종 존재 |
| S-23 | `/tmp/opal-ts106/proj/` (manifest·code-map 존재) + @header 없는 신규 코드 파일 1개 | `validate --changed <신규파일>` → 매니페스트 기입 → 재실행 | `newly_uncovered` ≥1·exit 2 → 기입 후 0·exit 0 전이
| S-24 | `/tmp/opal-ts106/docauto/` (code-scan.json 유효 + PLAN.md 존재 + 대상 `.md`만) | EXECUTE 첫 행에 `--auto-pass` 실어 호출 | `skipped`·`doc_only_task`·exit 0 (거부 발생 0건)
| S-25 | 임시 폴더 3종(force / code-scan.json 부재 / PLAN.md 부재) + 플래그 2개 동시 지정 | 각각 훅 경유 호출 | `force` 통과 / `code_scan_unavailable` / `plan_md_absent` / 상호배타 exit 1

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 실 산출물 판독)

#### S-1: `opcmb` SKILL.md frontmatter 계약

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | F-001 / `opal/skills/opal-code-map-builder/SKILL.md` |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | Step 1 완료 후. YAML frontmatter 파싱 가능 |
| 기대 결과 | `name`·`description`·`alias`(=`opcmb`)·`triggers`·`version` 5필드 전건 존재·비공백 |
| 도구 | `python3` (yaml 파싱) |
| 실행 명령 | `python3 - <<'EOF'` (frontmatter 수동 파서 — PyYAML 미설치 환경) + `sed -n '1,14p' opal/skills/opal-code-map-builder/SKILL.md`. 관측 스코프: 프로젝트 소스 SKILL.md 1파일 |
| 결과 | **Pass** |
| 상세 | frontmatter 5필드 전건 비공백. `name='opal-code-map-builder'` · `description=블록 스칼라(비공백)` · `alias='opcmb'` · `triggers=['^opcmb$', '^opal-code-map-builder$', '(?i)(코드\\s*맵|code-?map|헤더\\s*자산)']`(3원소) · `version='1.0'`. 파서 출력 `ALL5 non-empty: True` · `alias==opcmb: True`. 부가 `domain: metadata` 1필드 확인(설계 초과 아님 — Step 1 게이트 기록과 일치). 파일 229행 |

#### S-3: 모드 분기 3항 문면 존재

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | F-001 / SKILL.md 모드 판별·시퀀스 절 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | Step 1 완료 후 |
| 기대 결과 | (i) `headerSource` 2택 제시 → `code-scan init --header-source <값> --write` 호출 절차 (ii) `manifest`의 `discover`→소유자 리뷰→`scaffold` 3단 (iii) `inline` 종료 분기 + `code-scan missing` 안내 반환 — 3항 각각 명시. `headerSource` 병합·자동 폴백·스코프별 재선언 경로 **0건** |
| 도구 | `grep` |
| 실행 명령 | `grep -n -- 'code-scan init --header-source' SKILL.md` · `grep -nE 'discover|scaffold|리뷰|reviewed' SKILL.md` · `grep -n 'code-scan missing\|inline' SKILL.md` · `grep -nE '병합|자동 폴백|스코프별 재선언' SKILL.md` + `sed -n '205,225p'` |
| 결과 | **Pass** |
| 상세 | (i) `:63` STEP 표 1행 = 「`headerSource` 2택을 소유자에게 제시 → 확정값 수령 / `code-scan init --header-source <값> --write`」 + `:103`·`:105` 코드펜스 2택 리터럴. (ii) `:65` discover → `:66` 소유자 리뷰 게이트 → `:67` `status: draft`→`reviewed` → `:68` scaffold — 3단(실측 4행) 명시, 본문 STEP 2·3·4·5로 전개. (iii) `:52`·`:64` `inline` 종료 분기 + `code-scan missing` 안내 반환, `:113` STEP 1-x 절. (iv) 병합·자동 폴백·스코프별 재선언 3종은 `:214-218` 「경계 — 신설하지 않는 것」 **금지 표 3행**으로만 등장 — 제공 경로 0건 |

#### S-4: L2 표 축 구분 각주 — 자기모순 소멸

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | F-002 / `opal/core/references/opal-pm.md` §12 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | Step 8 완료 후 |
| 기대 결과 | 「유지」 블록 5행(기존 4 + 신설 1) · 축 구분 각주 1줄이 "파이프라인 게이트 3종 한정"과 `header-rules.md` §갱신 시점 (4단) (d) 포인터를 포함 · 「미적용」 5행 원문 무변경 · §12 그 외 절 무변경 |
| 도구 | `grep` + `git diff` |
| 실행 명령 | `awk '/^## 12\./,/^## 13\./' opal/core/references/opal-pm.md` · `grep -n '유지\|미적용' opal-pm.md` · `git diff --numstat -- opal-pm.md` · `git diff -U0 -- opal-pm.md | grep '^@@'` |
| 결과 | **Pass** |
| 상세 | 「유지」 5행 실측(`:206`~`:210` — 기존 4 + 신설 `:208` 「@header 갱신 검증 (L2 완료 시점 — `code-scan validate --changed`)」). 「미적용」 5행(`:211`~`:215`) 원문 유지. 축 구분 각주 `:219` 1줄이 「파이프라인 게이트 3종(QA Gate / State Gate / PM Gate)에 한정」 + `harness/header-rules.md` §갱신 시점 (4단) (d) 포인터를 **둘 다** 포함. `git diff --numstat` = **+15/-0** · 삭제 라인 전수 **0건** → 「미적용」 5행·§12 그 외 절 원문 무변경 증명. diff 헌크 4개(+208 / +219,2 / +240,11 / +396) — §12 유지행·각주 · §13 신설 · 변경이력뿐 |

#### S-5: §갱신 시점 (4단) 전환 + 기존 3행 보존

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | F-002 / `opal/core/references/harness/header-rules.md` |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | Step 7 완료 후 |
| 기대 결과 | 표 제목 (4단) + (d) L2 완료 시점 행 존재 · (a)(b)(c) 3행 원문 무변경 · 폴백 3종이 "판정보다 앞에 평가한다" 순서 계약과 함께 기재 |
| 도구 | `grep` + `git diff` |
| 실행 명령 | `F=opal/core/references/harness/header-rules.md; grep -c '^### 갱신 시점 (4단)$' $F; grep -c '(d) . \*\*L2 경량 트랙 완료 시점\*\*' $F; grep -c '판정보다 앞에 평가한다' $F; git diff --numstat -- $F` (기대: 1 / 1 / 1 / 삭제 2건 = 표 제목·도입문뿐 → (a)(b)(c) 3행 무변경) |
| 결과 | **Pass** |
| 상세 | 실측 = 1 / 1 / 1 / `25 2`. `grep -c '^### 갱신 시점 (4단)$'` = 1 · `grep -c '(d) . \*\*L2 경량 트랙 완료 시점\*\*'` = 1 · `grep -c '판정보다 앞에 평가한다'` = 1. `git diff --numstat` = **+25/-2**이고 삭제 2줄 전수는 `### 갱신 시점 (3단)`(표 제목) + `@header는 "작업 완료 후 일괄 갱신"하지 않는다 — 아래 3개 시점에서만 갱신한다.`(도입문)뿐. `git diff | grep -cE '^-\| \((a|b|c)\)'` = **0** → (a)(b)(c) 3행 원문 무변경. 폴백 3종(`:47`~`:49` 자산 게이트 / 적용 범위 / `pre_existing` 비차단)이 `:45` **[MUST]** 「아래 3종은 `validate` 판정보다 앞에 평가한다 — 순서 자체가 계약이다」와 함께 기재 |

#### S-6: L2 미수행 탐지 조건 명시

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | F-002 / `header-rules.md` §갱신 시점 (d) 행 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | Step 7 완료 후 |
| 기대 결과 | (d) 행에 미수행 탐지 조건이 "(b) CLOSE 게이트 `validate --changed` exit≠0"으로 명시되고, **모드별 차단 사유 2종**이 함께 기재 — `inline` = `counts.newly_uncovered` ≥1 / `manifest` 관리 매니페스트 하위 = `violations[].sub == "no_entry"` |
| 도구 | `grep` |
| 실행 명령 | `F=opal/core/references/harness/header-rules.md; grep -c '(b) CLOSE 게이트의 .validate --changed. exit≠0' $F; grep -c 'counts.newly_uncovered. ≥1' $F; grep -c 'violations\[\].sub == "no_entry"' $F` (기대: 1 / 3 / 2) |
| 결과 | **Pass** |
| 상세 | 실측 = **1 / 3 / 2** (기대 1/3/2 정확 일치). `:53` (d) 미수행 탐지 조건 절이 「**(b) CLOSE 게이트의 `validate --changed` exit≠0**으로 누적 탐지된다」로 명시. 모드별 차단 사유 2종 표(`:57`~`:60`) — `inline` = `counts.newly_uncovered` ≥1 / `manifest`(관리 매니페스트 하위) = `violations[].sub == "no_entry"`. 추가로 `:62` **[MUST] `counts.newly_uncovered` 단독 인용은 금지** 1줄 확인 |

#### S-7: 2단 소비 규율 + 포인터 비복제

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | F-003 / `opal-pm.md` §13 · `pm/dispatch-process.md` |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | Step 9·10 완료 후 |
| 기대 결과 | §13에 4열(단/수단/목적/전환 조건) 2행 표 · 2차 전환 허용 조건 명시 · 소유자 오버라이드와의 구분 1줄 · "Glob/Grep 직행 금지"와의 비모순 1줄 · `:237` 오버라이드 문단 원문 무변경. `dispatch-process.md`는 포인터 불릿 1건이며 규정 원문 복제 0건 · `:130`·`:134` 원문 무변경 |
| 도구 | `grep` + `git diff` |
| 실행 명령 | `sed -n '236,256p' opal/core/references/opal-pm.md` · `git diff -- opal/core/references/pm/dispatch-process.md` · `git diff --numstat` 양 파일 |
| 결과 | **Pass** |
| 상세 | §13 「2단 소비 절차」 = 4열(단/수단/목적/전환 조건) **2행** 표 실측(`:240`~`:244`). 2차 전환 허용 조건이 분기명·기준값까지 인용 — 「1차로 후보가 확정된 뒤. 또는 `harness/header-rules.md` §빈 결과 폴백 ① 매칭 0건 · ② 저커버리지(`coverage.percent` 30% 미만)」. 「Glob/Grep 직행 금지」 비모순 1줄 존재(`:246`) · 소유자 오버라이드(소유자 권한 행사)와 2차 전환(PM 자율 절차) 구분 1줄 존재(`:248`) + `citation-rules.md` §9 (f) 인용. `opal-pm.md` 삭제 라인 **0건** → 오버라이드 문단 원문 무변경. `dispatch-process.md` = **+2/-0**(포인터 불릿 1 + 변경이력 1), 삭제 0건 → `:130` 무조건 호출·`:134` 직행 금지 원문 보존. 포인터 불릿은 「전환 규정의 원문은 `opal-pm.md` §13 「2단 소비 절차」가 소유한다」로 SSOT 위임만 하며 표·조건 **복제 0건** |

#### S-8: 집행 지점 후보 비교 근거 보존

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | F-004 / PLAN.md §3.4 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | PLAN 확정 후(이미 충족) |
| 기대 결과 | 후보 3종(`state-tool` / `code-scan` / `SubagentStop`) 비교표 + 확정 1종 + 탈락 근거가 각각 명시. 채택안이 플랫폼 독립 경로임이 근거로 기재 |
| 도구 | `grep` |
| 실행 명령 | `grep -n '^#\+ ' PLAN.md` (§3.4.2 위치 확정) · `sed -n '485,530p' tasks/106-.../PLAN.md` |
| 결과 | **Pass** |
| 상세 | 후보 3종 전건 비교표 확인 — DEC-1 표가 `state-tool` 확장 vs `code-scan` 자체 서브명령을 4축(파이프라인 게이트 통합 편의 / 도구 응집도 / `verify --evidence-check` 로직 재사용 비용 / 배포·플랫폼)으로 대조, DEC-5 표가 `SubagentStop` hook을 4축(사전 차단 가능성·판정 대상 특정·플랫폼 독립성·현 용도 결합)으로 대조. 확정 1종 = **`state-tool` 확장**(「3축 전건 `state-tool` 우위 → `state-tool` 확장 채택. `code-scan.js` 무변경」). 탈락 근거 각각 명시 — `code-scan`은 3축 「열위」 사유 개별 기재, `SubagentStop`은 「탈락 — DEC-1 채택안 대비 4축 전건 열위」. 플랫폼 독립 근거 기재 확인 — DEC-1 「배포·플랫폼 = 동등, 둘 다 `~/.opal/tools/` 배포, 플랫폼 독립」 + DEC-5 「플랫폼 독립성 = 위반 … Cursor·Gemini·Codex에서 규칙이 소멸한다」 |

#### S-12: 폴백 조건 3곳 명시 + 게이트 선행 순서

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | F-005 / `state_tool.py` · `pm-review-gate.md` · `header-rules.md` |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | Step 4·6·7 완료 후 |
| 기대 결과 | 폴백 조건이 3곳에 명시 — 훅 게이트 ③⑤ + `reason` 3값 / 항목 14 스킵 조건 3종 / (d) 미발동 조건 3종. 세 문면의 조건 집합이 서로 일치. 게이트 순서가 판정보다 앞임이 코드 주석 또는 문면으로 확인 |
| 도구 | `grep` |
| 실행 명령 | `sed -n '2600,2670p' opal/tools/state-tool/state_tool.py`(훅 게이트 주석·순서) · `sed -n '3210,3260p'`(verify 라우터 `reason` 3값) · `sed -n '112,128p' pm-review-gate.md` · `sed -n '32,80p' header-rules.md` |
| 결과 | **Pass** (조건 집합 일치 축 1건 이견 — PM 판단 요청, 하단 참조) |
| 상세 | 폴백 조건이 3곳 전건 명시 확인. ① `state_tool.py:2630`(③ 자산 게이트)·`:2647`(④ 산출물)·`:2652`(⑤ 적용 범위) + `cmd_verify:3226`·`:3228`·`:3233`의 `reason` 3값(`code_scan_unavailable`/`plan_md_absent`/`doc_only_task`). ② `pm-review-gate.md` 항목 14 스킵 조건 3종 — 동일 3값 리터럴. ③ `header-rules.md` (d) 미발동 조건 3종. **게이트 순서 선행 확인**: `state_tool.py:2600-2618` 독스트링이 「**게이트 순서 자체가 계약이다**」 + 7단 순서(①발동→②force→③자산→④산출물→⑤적용범위→⑥auto_pass 거부→⑦판정) + **[MUST] ⑥은 ③④⑤ 뒤** + 「형제 훅 `_run_clarification_hook`의 배치를 답습하지 않는다」를 명기하고, `cmd_verify:3211` 주석이 라우터도 동일 순서임을 못 박음. 문서 2곳도 「판정보다 앞에 평가한다」(header-rules `:45`) · 「3종은 판정보다 앞에 평가한다」(항목 14) 기재. **[이견]** 기대 문면의 「세 문면의 조건 집합이 서로 일치」는 3항 중 **2항만** 성립 — ①②는 3/3 동일하나 ③(`header-rules` (d))의 3번째 항목은 `pre_existing` 비차단이며 `doc_only_task`가 아니다. 이는 판정 대상 차이(헤더 커버리지 vs PLAN 인용)에 따른 도메인 분화로 보이며 `AGENTIC-LOG.md` §Step 6 게이트가 동일 판단을 기록했으나, 시나리오 기대 문면과는 불일치한다. 판정을 임의로 바꾸지 않고 PM 판단을 요청한다 |

#### S-18: 변경이력 형태별 준수

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | 전 F / 개정 8문서 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | 전 Step 완료 후 |
| 기대 결과 | 8문서 각각의 변경이력 마커(`## 변경이력` 헤딩형 vs `변경이력:` 인라인형)와 컬럼 순서가 개정 전 형태와 동일 · 각 문서에 행 1건 추가 · 각 행에 태스크 번호 `(106)` 포함 · 표 파손 0건 |
| 도구 | `grep` + `git diff` |
| 실행 명령 | 8문서 루프 — `grep -c '^## 변경이력' <f>` vs `git show HEAD:<f> | grep -c '^## 변경이력'` · 동일 대조 `^변경이력:` · `git diff -- <f> | grep -c '^+|.*(106)'` · `git diff -- <f> | grep -c '^-|'` |
| 결과 | **Pass** (README 변경이력 2행 — 관측값 병기) |
| 상세 | 8문서 마커 형태 전건 개정 전과 동일 — heading형 7문서(`docs/ARCHITECTURE.md` 1·`docs/CONVENTIONS.md` 2·`docs/PROJECT.md` 1·`pm-review-gate.md` 1·`opal-pm.md` 1·`dispatch-process.md` 1·`state-tool/README.md` 1) / inline형 1문서(`header-rules.md` `변경이력:` 1, `## 변경이력` **0건**) — HEAD 계수와 8/8 일치. 컬럼 순서도 문서별 기존 형태 유지(버전 컬럼 보유형 6문서는 `| vN | 시각 | 내용 |`, `ARCHITECTURE.md`·`PROJECT.md`는 버전 컬럼 없는 `| 날짜 | 내용 |` 그대로). `(106)` 태그 행 추가 확인 — 7문서 각 1행. 표 파손 0건(모든 신규 행이 기존 열 수와 동일). **관측 병기**: `state-tool/README.md`는 변경이력 행이 **2건**(v1.13 Step 15 종수 갱신 / v1.14 Step 16 절 신설)이다 — `AGENTIC-LOG.md`상 PLAN 결손 보강 2건이 별개 Step으로 수행됐기 때문이며 기대 「행 1건 추가」와 형식상 차이가 있으나 문서 형태·표 무결성은 준수. `ARCHITECTURE.md`·`PROJECT.md`의 `^-|` 삭제 각 1행은 변경이력이 아니라 S-19 스킬 수 셀 교체분이다 |

#### S-19: 스킬 수 셀 실측 정합

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-12 |
| 대상 | 부속 / `docs/PROJECT.md` · `docs/ARCHITECTURE.md` |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | Step 1·13 완료 후 |
| 기대 결과 | 4개 셀 값이 `find opal/skills -mindepth 1 -maxdepth 1 -type d \| wc -l` 실측값(개정 후 45)과 일치 · 스킬 수 셀 외 무변경 |
| 도구 | `find` + `grep` + `git diff` |
| 실행 명령 | `find opal/skills -mindepth 1 -maxdepth 1 -type d | wc -l` · `grep -n 'OPAL 스킬 45개\|OPAL 전용 (45종)\|opal/skills/\* (45개)\|OPAL 스킬 (45개)' docs/PROJECT.md docs/ARCHITECTURE.md` · `git diff -- docs/PROJECT.md docs/ARCHITECTURE.md` |
| 결과 | **Pass** |
| 상세 | 실측 = **45**. 4개 셀 전건 45 일치 — `docs/PROJECT.md:37`(OPAL 전용 (45종)) · `docs/ARCHITECTURE.md:77`(OPAL 스킬 45개) · `:217`(`opal/skills/* (45개)`) · `:425`(OPAL 스킬 (45개)). 스킬 수 문맥의 잔존 `42` grep **0건**(변경이력 서술 제외). `git diff` 실측 = 두 문서 모두 스킬 수 셀 교체 + 변경이력 1행뿐 — `ARCHITECTURE.md` 헌크 4개(`:77`·`:217`·`:425`·변경이력) · `PROJECT.md` 헌크 2개(`:37`·변경이력) → 셀 외 무변경 |

#### S-22: 교체형 채택/잔존 — 자기판정 문면 소멸 + 도구 판정 채택

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | F-004 / `opal/core/references/harness/pm-review-gate.md` §표준 검토 항목 14 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | Step 6 완료 후. 개정 전 항목 14는 "PM이 판정한다" 계열 자기판정 문면을 보유 |
| 기대 결과 | **(구형 잔존 0)** 항목 14에 "PM이 판정한다" 계열 문면 **0건** · **(신형 채택)** 판정 수단이 `state-tool verify --code-scan-citation-check` exit code로 명시 + 집행 지점 + 스킵 조건 3종이 존재 · 항목 1~13·자가 진단 절 무변경 |
| 도구 | `grep` + `git diff` |
| 실행 명령 | `sed -n '112,128p' opal/core/references/harness/pm-review-gate.md > /tmp/item14.txt` → `grep -cE 'PM이 판정한다|PM이 직접 판정|눈으로 읽어 스스로 판단한다|스스로 판정' /tmp/item14.txt` · `grep -c 'verify .*--code-scan-citation-check' /tmp/item14.txt` · `git diff -U0 | grep '^@@'` · `git diff | grep '^-[^-]'` |
| 결과 | **Pass** |
| 상세 | **(구형 잔존 0)** 항목 14 범위(`:112`~`:128`) 한정 자기판정 패턴 grep = **0건**. 삭제 3줄 전수가 구형 문면(`- **적용 범위**: … **N/A(스킵)**` / `- **판정**: 인용 부재 시 **Fail** → 재디스패치 1회` / 구형 `- **Pass 조건**`)임을 `git diff | grep '^-[^-]'`로 확인. **(신형 채택)** 판정 수단 = `~/.opal/tools/state-tool/run.sh verify tasks/{NNN}-.../ --code-scan-citation-check` 명시(grep 2건) + 3값 매핑(`pass`→Pass / `skipped`→N/A / `unmet` exit 1→Fail) + 집행 지점 2곳(verify 수동 호출 / EXECUTE 첫 행 `advance`·`mark` 자동 훅) + 스킵 조건 3종 전건 기재. 부정문 명문화 확인 — `:118` 「인용 여부를 눈으로 읽어 스스로 판단하지 않는다」 + PRINCIPLES §Core Stance 원문. `git diff -U0` 헌크 **2개뿐**(`@@ -116,3 +116,12` 항목 14 내부 + `@@ -180,0 +190` 변경이력) → 항목 1~13·자가 진단 절 무변경 구조 증명 |

### L2. 프로세스 통합 (자동, 실 도구 실행 → 상태 관측 → 재판독)

#### S-2: 레지스트리 라우팅 결정성 + 사본 정합

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5, H-9 |
| 대상 | F-001 / 레지스트리 + `docs/CONVENTIONS.md` 약어 표 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | Step 2·3 완료 후. 개정 전 alias 29종 / 표 27종 |
| 기대 결과 | `skill-registry.js get opcmb` 단일 항목 반환 · `match "opcmb"` 단일 해석(`ambiguous` 아님) · alias 총계 30종 · 중복 0건 · JSON 파싱 성공 · 기존 29종 항목 무변경 · CONVENTIONS 표 항목·총계가 레지스트리 30종과 1:1 일치 |
| 도구 | `node skill-registry.js` + `python3` |
| 실행 명령 | `node ~/.opal/tools/skill-registry/skill-registry.js get opcmb` · `… match "opcmb"` · `python3`(소스·배포본 레지스트리 alias 재귀 수집 + `docs/CONVENTIONS.md` §약어 (Alias) 표 파싱 양방향 차집합) · `git diff -- opal-skills-registry.json | grep '^-[^-]'` |
| 결과 | **Pass** |
| 상세 | 배포본 실행. `get opcmb` → 단일 항목 반환(exit 0, `name`/`alias`/`description`/`triggers` 3종/`paths`/`group: opal`). `match "opcmb"` → `{found:true, name:opal-code-map-builder, alias:opcmb, cleanInput:opcmb}` 단일 해석 · `ambiguous` 필드 부재 → 라우팅 결정성 확인(exit 0). alias 총계 — 소스 **30종**·중복 `[]`·`opcmb` 등재 True / 배포본 **30종**·중복 `[]`·`opcmb` True / **소스↔배포본 alias 집합 동일 True**. JSON 파싱 성공(양쪽) · `version 3.14.0` · `updated_at 2026-09-04`. 기존 29종 무변경 — 레지스트리 삭제 라인 전수 = `"version": "3.13.0"` + `"updated_at": "2026-09-02"` 2줄뿐. CONVENTIONS 표 = **30항목·중복 0** · 표↔레지스트리 **양방향 차집합 공집합**(1:1 일치 True) · 도입문 총계 `:45` 「현재 **30종**」 정합 |

#### S-9: 인용 미충족 → exit 1 차단 (RED-first 대상)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10 |
| 대상 | F-004 / `verify --code-scan-citation-check` + EXECUTE 첫 행 훅 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | `/tmp/opal-ts106/neg/` — `state.json`에 EXECUTE 행 보유 + PLAN.md §4.2에 `.py` 대상 파일 기재 + code-scan 인용 토큰 0건. `.opal/code-scan.json` 유효 |
| 기대 결과 | ① `verify --code-scan-citation-check` → `ok:false` · `error: code_scan_citation_unmet` · **exit 1** ② 동일 폴더 EXECUTE 첫 행 `mark` → 동일 에러코드로 거부 ③ `state.json` **무변경**(호출 전후 바이트 동일) |
| 도구 | `state-tool` CLI (블랙박스) |
| 실행 명령 | 픽스처 `SP/opal-ts106/neg/`(루트에 `.opal/MEMORY.json` + `.opal/code-scan.json{headerSource:inline, extensions:[.py,.js,.ts]}`, 태스크 폴더는 `state-tool init --skill opd --mode agentic --rows-from opal-pilot-dev/pipeline.json` 후 EXECUTE 앞 구간 done 처리, PLAN.md §4.2 `- **파일**: \`src/app.py\`` + 인용 토큰 0건). ① `~/.opal/tools/state-tool/run.sh verify <T> --code-scan-citation-check` ② `… mark <T> --task-step execute.implement --done --as-worker --worker-stage EXECUTE --worker-duration-minutes 1 --note "S-9 관측"` ②-b `… advance <T> --task-step execute.implement` ③ `md5 -q <T>/state.json` 호출 전후 |
| 결과 | **Pass** |
| 상세 | ① `{"ok": false, "command": "verify", "error": "code_scan_citation_unmet", "code_scan_citation_check": "unmet", "missing": ["citation_absent"], "target_files": ["src/app.py"], "matched_tokens": []}` · **exit 1** — 기대 3요소 전건 일치. ② `mark` → `{"ok": false, "error": "code_scan_citation_unmet", "missing": ["citation_absent"]}` · **exit 1** (동일 에러코드). ②-b `advance`도 동일 에러코드 · exit 1 → 두 집행 지점 모두 차단 확인. ③ `state.json` md5 **`b5bb12f3f337031e9e9f9aee9ec567fc` → 동일**(6123 바이트) → 영속 **무변경**. RED-first 대조 증거: `RED-EVIDENCE.md` §S-9 — 개정 전(`git show HEAD:` 복원본, HEAD `69f5ce1`)은 동일 픽스처에서 `mark` **ok:true·exit 0·state.json md5 변경(dd332df…→065e5a4…)** |

#### S-10: 인용 충족 → exit 0 통과 (RED-first 대상)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10 |
| 대상 | F-004 / 동일 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | `/tmp/opal-ts106/pos/` — S-9와 동일 구조에 `domain`/`layer`/`depends`/`exports` 중 1개 이상 인용 토큰 존재 |
| 기대 결과 | ① `code_scan_citation_check: "pass"` · exit 0 · `matched_tokens` 1건 이상 ② EXECUTE 첫 행 `mark` 정상 진행(행 상태 전이) |
| 도구 | `state-tool` CLI (블랙박스) |
| 실행 명령 | 픽스처 `SP/opal-ts106/pos/`(S-9와 동일 구조, PLAN.md §4.2 본문에 `domain`/`layer`/`depends`/`exports` 인용). ① `run.sh verify <T> --code-scan-citation-check` ② `run.sh mark <T> --task-step execute.implement --done --as-worker --worker-stage EXECUTE --worker-duration-minutes 1 --note "S-10 관측"` |
| 결과 | **Pass** |
| 상세 | ① `{"ok": true, "code_scan_citation_check": "pass", "reason": null, "target_files": ["src/app.py"], "matched_tokens": ["domain", "layer", "depends", "exports", "code-scan"]}` · **exit 0** · `matched_tokens` **5건**(≥1 충족). ② `mark` → `{ok: True, row_id: 12, stage: EXECUTE, status: done, owner: PM}` · exit 0 · `execute.implement` 행 상태 전이 **pending → done**(timestamp `2026-09-04 23:22:15` 기록) 확인. RED-first 대조 증거: `RED-EVIDENCE.md` §S-10 — 개정 전에는 `--code-scan-citation-check` 플래그 자체가 부재(argparse `unrecognized arguments`, exit 2)라 통과 판정을 낼 수단이 없었다 |

#### S-11: 미보급 프로젝트 오탐 0건

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7, H-8 |
| 대상 | F-005 / 이 레포(`headerSource: inline` + code-map 부재) |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | Step 4 완료 + Step 14 배포 완료 후(H-11). 이 레포 실환경 |
| 기대 결과 | ① 태스크 106 폴더 대상 `verify --code-scan-citation-check` → **`pass` · exit 0** (**PM 실측 기반 정정** — 이 태스크 PLAN.md §4.2 대상에 `.py`가 포함되어 게이트 ⑤가 발동하지 않고 ⑦ 판정으로 진행하며, 인용 토큰이 존재하므로 `pass`가 정답이다. 초안의 `skipped`·`doc_only_task` 기대는 이 태스크를 문서 전용으로 오판한 것이었다. `doc_only_task` 경로는 S-24·S-25가 전담 관측한다). 어느 값이든 **거부 0건**이 R-5 AC(a)의 판정 축이다 ② `.md`만 변경한 목록으로 `validate --changed` → exit 0 ③ `validate --changed opal/tools/state-tool/state_tool.py` → exit 0 · `newly_uncovered` 0 ④ 거부·경고 발화 **0건**(stdout·stderr 양축) |
| 도구 | `state-tool` + `code-scan` CLI |
| 실행 명령 | 배포본 경유. ① `~/.opal/tools/state-tool/run.sh verify tasks/106-260904-opd-코드맵-스킬신설-하네스개정 --code-scan-citation-check` ② `~/.opal/tools/code-scan/run.sh validate --changed "docs/PROJECT.md,docs/ARCHITECTURE.md,docs/CONVENTIONS.md" --json` ③ `~/.opal/tools/code-scan/run.sh validate --changed "opal/tools/state-tool/state_tool.py" --json` ④ stdout·stderr 분리 캡처(`>out 2>err` + `wc -c <err`) |
| 결과 | **Pass** |
| 상세 | ① `{"ok": true, "code_scan_citation_check": "pass", "reason": null}` · **exit 0** · `matched_tokens` **9종**(`domain`·`layer`·`depends`·`exports`·`write_to`·`reason`·`coverage`·`counts`·`code-scan`) · `target_files` **20건** — PM 정정 기대(`pass`·exit 0)와 일치. ② `.md` 3파일 → **exit 0** · `counts.newly_uncovered` **0** · `pre_existing` 3(비차단). ③ `state_tool.py` → **exit 0** · `counts.newly_uncovered` **0** · `pre_existing` 1(비차단). ④ stderr **0바이트**(① 실측) · ②③ stderr 공백 · 거부·경고 발화 **0건**. R-5 AC(a) 판정 축 「거부 0건」 충족. **부수 관측(이 태스크 회귀 아님)**: `state_tool.py`가 `uncovered:pre_existing`으로 나오는 것은 `code-scan.js:39 HEADER_READ_BYTES = 8192` < @header 블록 실측 11,9xx바이트라는 선존 한계 때문이며 HEAD 시점도 동일하다(§5 #4 참조) |

#### S-13: pipeline.json 행 수·key 불변

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | F-006 / 3 `pipeline.json` |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | Step 5 완료 후. 개정 전 스냅샷은 `git show HEAD:` |
| 기대 결과 | `len(task_steps)` = opd 16 / opds 11 / opp 9 불변 · key 집합 불변 · `git diff`에 `key`·`id`·`stage`·`item` 변경 0건 · `checklist` 길이만 4→5/4→5/3→4 · `gate` 필드 집합이 `artifacts`·`checklist` 2종 불변 |
| 도구 | `python3` + `git diff` |
| 실행 명령 | `python3`으로 3 `pipeline.json` 각각 현재본 vs `git show HEAD:<path>` 스냅샷 대조 — `len(task_steps)` · `key` 배열 · 행별 `(key,id,stage,item)` 4튜플 · `gate` 필드 집합 합집합 · `gate.checklist` 길이 맵. + `git diff -- opal/skills/*/references/pipeline.json | grep -E '^[+-] *"(key|id|stage|item)"'` |
| 결과 | **Pass** |
| 상세 | `len(task_steps)` — opd **16→16** / opds **11→11** / opp **9→9** (기대 16/11/9 불변 True). `key` 배열 3종 전건 **동일**(순서 포함) · 행별 `(key,id,stage,item)` 4튜플 **전건 동일 True**. `git diff`에서 `key`·`id`·`stage`·`item` 변경 라인 **0건**. `checklist` 길이 변경은 `plan.pm_gate` 1행뿐 — opd 4→5 · opds 4→5 · opp 3→4 (기대와 정확 일치). `gate` 필드 집합 = `['artifacts','checklist']` 개정 전후 **2종 불변**(3종 전건) |

#### S-14: 기존 태스크 폴더 조회 무결

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | F-006 / 기존 태스크 3폴더 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | Step 4·5 완료 + 배포 후. `tasks/103-…`·`tasks/104-…`·`tasks/105-…` |
| 기대 결과 | `state-tool show <path>` × 3 → exit 0 · 오류 0건 · 렌더 결과에 결손 필드 0건 |
| 도구 | `state-tool` CLI |
| 실행 명령 | 배포본 `~/.opal/tools/state-tool/run.sh show <path> --format json`(+ `--format md`) × 기존 태스크 폴더 4건(`tasks/103-…`·`tasks/104-…`·`tasks/105-…스킬-탐색설치-개선`·`tasks/105-…어댑터-확장필드-통로`) → exit code · JSON 파싱 · `data.rows[]` 필수 8필드(`row_id`·`stage`·`item`·`status`·`status_label`·`owner`·`timestamp`·`key`) 결손 검사 |
| 결과 | **Pass** |
| 상세 | 4폴더 전건 **exit 0** · `ok=True` · JSON 파싱 성공 · 오류 0건. rows 계수 — 103: **23행** / 104: **9행** / 105(스킬-탐색설치-개선): **12행** / 105(어댑터-확장필드-통로): **11행**. 필수 8필드 **결손 행 0건**(4폴더 전건 `[]`). `--format md` 렌더도 exit 0. 시나리오는 3폴더를 명시했으나 `tasks/105-*`가 실제 2폴더여서 **4폴더 전수**로 관측 스코프를 확대해 실행했다(축소 아님) |

#### S-15: 훅 발동 반경 — 8 파이프라인 회귀

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | F-006 / EXECUTE 단계 보유 8 파이프라인 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | Step 4·5 완료 + 배포 후. 8종 각각의 `pipeline.json`으로 임시 태스크 폴더를 `state-tool init`하고 EXECUTE 첫 행까지 진행 |
| 기대 결과 | 8종 전건에서 EXECUTE 첫 행 진입 시 훅이 **skip 또는 pass만** 관찰 · 예기치 않은 거부 0건 · 조건 미해당 호출의 stdout 키 집합이 개정 전과 동일. 관측 스코프(8종 목록)와 실행 명령을 결과에 병기 |
| 도구 | `state-tool` CLI |
| 실행 명령 | `bash SP/s15.sh skip` · `bash SP/s15.sh pass` — EXECUTE 보유 파이프라인 **8종**(opd·opds·opdw·opp·oppd·oppl·opsdd·opwt) × 개정 전(`git show HEAD:state_tool.py` 복원본) / 배포본 2버전 × 픽스처 2변이. 각 실행 = `python3 <tool> init <T> --skill <alias> --mode agentic --rows-from <pipeline.json>` → EXECUTE 앞 구간 done 처리 → `python3 <tool> advance <T> --task-step <해당 파이프라인 EXECUTE 첫 키>` |
| 결과 | **Pass** |
| 상세 | **관측 스코프 8종 + 각 파이프라인 EXECUTE 첫 키** — opd·opds·opdw·opp `execute.implement` / oppd `execute.actions` / oppl `execute.l0_select` / opsdd `execute.act_run` / opwt `execute.batches`. (`opdd`·`opgc`는 `python3` 실측상 EXECUTE 행 **0개**로 대상 아님 — 15행/7행.) **총 32 실행**(8종 × 2버전 × 2변이) 전건 **exit 0 · ok=True · error=None** — 예기치 않은 거부 **0건**. stdout 키 집합이 32 실행 전건 동일 = `auto_approved,command,item,ok,row_id,stage,status,timestamp,todo_mirror` → 개정 전후 **바이트 동형**. 변이 1 = `.opal/code-scan.json` 부재(조건 미해당 → 게이트 ③ skip) / 변이 2 = `code-scan.json` 유효 + 인용 보유 PLAN.md(⑦ 판정 → pass) — 두 변이 모두 「skip 또는 pass만」 충족 |

#### S-16: 스펙 검증 violations 0건

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | F-006 / 3 `pipeline.json` |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | Step 5 완료 후 |
| 기대 결과 | `state-tool spec-validate` × 3 → violations 0건 · exit 0 |
| 도구 | `state-tool` CLI |
| 실행 명령 | `~/.opal/tools/state-tool/run.sh spec-validate opal/skills/<pilot>/references/pipeline.json` × 3(opal-pilot-dev / -dev-short / -project), 배포본 실행 |
| 결과 | **Pass** |
| 상세 | 3종 전건 `{"ok": true, "command": "spec-validate", "violations": [], "violations_count": 0}` · **exit 0**. violations **0건** |

#### S-17: install 재배포 반영 + 스크립트 무변경

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-11 |
| 대상 | 부속 / `scripts/install-mac.sh` · `~/.opal/` 배포본 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | Step 1~10 완료 후 |
| 기대 결과 | ① `~/.opal/skills/opal-code-map-builder/SKILL.md` 존재 ② `~/.opal/references/opal-skills-registry.json`에 `opcmb` 반영 ③ 배포본 `~/.opal/tools/state-tool/run.sh verify --help`가 신설 플래그 인식 ④ `scripts/install-mac.sh`·`scripts/install/windows.ps1` git diff **0건** ⑤ 배포본 SKILL.md에서 변경이력 절 strip 확인 |
| 도구 | `bash` + `git diff` |
| 실행 명령 | ① `test -f ~/.opal/skills/opal-code-map-builder/SKILL.md` ② `grep -c '"opcmb"' ~/.opal/references/opal-skills-registry.json` ③ `~/.opal/tools/state-tool/run.sh verify --help | grep -A3 'code-scan-citation-check'` ④ `git diff --numstat -- scripts/install-mac.sh scripts/install/windows.ps1 | wc -l` ⑤ `grep -c '^## 변경이력' ~/.opal/skills/opal-code-map-builder/SKILL.md` + 배포본 `header-rules.md` (4단) · 배포본 3 `pipeline.json` rows/checklist |
| 결과 | **Pass** |
| 상세 | ① 배포본 SKILL.md **EXISTS**. ② 배포본 레지스트리 `opcmb` **1건** 등재(alias 30종·중복 0 — S-2 실측과 동일). ③ 배포본 `verify --help`가 `--code-scan-citation-check`를 usage와 옵션 설명 양쪽에 **인식**(설명 문면에 `code_scan_citation_unmet(exit 1)` + 「자산·산출물·적용 범위 3조건 미해당 시 skipped(exit 0)」). ④ `scripts/install-mac.sh`·`scripts/install/windows.ps1` git diff **0줄** → 스크립트 무변경. ⑤ 배포본 SKILL.md `## 변경이력` **0건** → install strip 정상. 추가 배포 반영 확인 — 배포본 `header-rules.md` `### 갱신 시점 (4단)` 1건 · 배포본 3 `pipeline.json` rows **16/11/9** · `plan.pm_gate.checklist` **5/5/4** |

#### S-20: 목표달성 — `opcmb` manifest 경로 완주 (자산 실제 생성)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 (목표달성 시나리오 — `harness/scenario-gate.md` §2 ①축) |
| 대상 | F-001 / 태스크 목표 "@header 자산의 **생성** 국면 완결" |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | `/tmp/opal-ts106/proj/` — 코드 파일 3개 이상, `.opal/` 부재. Step 1 완료 + 배포 후 |
| 기대 결과 | SKILL.md에 기술된 `manifest` 시퀀스를 그대로 실행했을 때 ① `code-scan init --header-source manifest --write` → `.opal/code-scan.json` 생성 ② `discover` → `.opal/code-map/index.json` 생성(`status: draft`·`origin: discover`) ③ `status`를 `reviewed`로 전환 ④ `scaffold` → 패키지 매니페스트 1개 이상 생성 ⑤ `validate` exit 0. **스킬 문면만으로 시퀀스가 성립하며 누락 명령·순서 오류 0건** |
| 도구 | `code-scan` CLI |
| 실행 명령 | 픽스처 `SP/opal-ts106/proj/`(`src/core/engine.py`·`src/core/util.py`·`src/api/handler.py` 3파일, `.opal/` 부재, `git init` + 커밋 1건). 배포본 `~/.opal/skills/opal-code-map-builder/SKILL.md` STEP 0~6 문면 그대로 — `run.sh init --header-source manifest --write` → `run.sh discover` → (STEP 3 리뷰 요약 제시) → `index.json` `status` `draft`→`reviewed` → `run.sh scaffold` → `run.sh validate` |
| 결과 | **Fail** (①~④ Pass / **⑤ validate exit 0 미달 — 실측 exit 2**) |
| 상세 | ① `init --header-source manifest --write` → `.opal/code-scan.json` **생성**, `headerSource=manifest`·scopes 1종(`src`)·extensions `[.py,.md]`, exit 0. ② `discover` → `.opal/code-map/index.json` **생성**, `"status": "draft"` · `"origin": "discover"` 확인, exit 0 (`Created .opal/code-map/index.json — scopes=1 layerRules=0 exclude=10`). ③ STEP 3 리뷰 항목 4종 실판독 가능(`scopes{root/anchors/stripPrefix/include/exclude}`·`layerRules`·`domains`·`exclude`) — 게이트 존재 확인, 소유자 승인은 S-21 [SUPERVISOR] 위임이라 대행하지 않음. ④ `status`를 `reviewed`로 전환 후 `scaffold` → `created=2 added=3`, 패키지 매니페스트 **2개**(`.opal/code-map/src/core.json`·`src/api.json`) 생성, exit 0. ⑤ **`validate` → `validate: 6 violation(s) — coverage 100% (3/3)` · exit 2**(기대 exit 0 미달). 위반 내역 = `{uncovered, sub:incomplete, detail:'layer,domain'}` × 3 + `{draft}` × 3. **원인 규명(보조 실측)**: (a) `scaffold` 골격이 `"draft": true` + 빈 `description`을 남기므로 `draft` 위반 3건이 필연이다 — SKILL.md STEP 5 자체가 「`description`·`exports`… 기입은 워커의 파일 변경 시점 몫」이라 밝히므로 시퀀스 안에서 해소되지 않는다. (b) `discover`가 이 트리에서 `layerRules=0`·`domains={}`를 냈고, SKILL.md STEP 3은 두 값을 「확인 대상」으로만 열거하며 **STEP 4는 `status` 전환만 지시**한다 — 「빈 `layerRules`/`domains`를 소유자가 채운다」는 지시가 문면에 없다. (c) 보조 실측으로 `layerRules`를 글롭형(`**/api/**`→api, `**/core/**`→service)으로 채우고 `domains` 지정 + `files{}`의 `description`/`exports` 기입 후 재실행하니 `validate: OK — coverage 100% (3/3)` **exit 0** 도달 → exit 0은 **도달 가능하나 SKILL.md 문면만으로는 도달하지 않는다**. 명령 누락·순서 오류는 0건(STEP 0→1→2→3→4→5→6이 실제 도구 계약과 정합). **PM 판단 요청**: 이 태스크의 목표달성 기준을 「`validate` exit 0」으로 유지할지, 아니면 SKILL.md STEP 3·4에 「빈 `layerRules`/`domains` 소유자 확정」과 STEP 6 exit 2 정상 경로(워커 기입 대기)를 명문화할지 |

#### S-23: 목표달성(갱신 국면) — 미갱신 탐지 실발동 → CLOSE 차단

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 (목표달성 시나리오 — 갱신 국면) |
| 대상 | F-002 / 태스크 목표 "@header 자산의 **갱신** 국면 완결" — `header-rules.md` §갱신 시점 (d)가 인용한 탐지 조건이 실제 발동하는가 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | **[MUST] 사전 조건 2갈래를 모두 만든다** — `code-scan.js` 실측상 차단 사유가 갈래별로 다르다. **갈래 A(manifest 관리 하위)**: `/tmp/opal-ts106/proj/` (S-20 완료 — `headerSource: manifest` + `scaffold` 완주). 관리 매니페스트가 덮는 디렉토리에 @header 없는 코드 파일 1개 신규 추가. **갈래 B(매니페스트 밖 + git)**: 관리 매니페스트가 없는 디렉토리에 동일 파일 추가. **git 저장소이며 커밋이 1개 이상** 존재해야 한다(`isGitUsable`이 work-tree AND `HEAD`를 요구 — `code-scan.js:1025-1035`. 커밋 없으면 `pre_existing`으로 분류되어 **비차단**이 되고 탐지가 발동하지 않는다) |
| 기대 결과 | **갈래 A**: `validate --changed <신규파일>` → `violations[]`에 `{code:"uncovered", sub:"no_entry"}` 1건 · **exit 2**. `counts.newly_uncovered`는 **0이 정상**(`:3427`이 `sub=="newly_uncovered"`만 계상, `no_entry` 전용 카운터 없음) — 차단은 `:3434-3436` 필터가 `no_entry`를 제외하지 않아 성립한다. **갈래 B**: → `counts.newly_uncovered` **≥ 1** · **exit 2**. **공통**: 두 갈래 모두 @header를 기입(A=매니페스트 `files{}` 엔트리 / B=인라인 또는 매니페스트)한 뒤 재실행 → 해당 위반 0 · **exit 0** 전이. ⇒ (b) CLOSE 게이트의 차단이 **모드별 2경로 모두에서 런타임으로 발동**함을 관측하며, 이 실측이 (d) 행 문면(모드별 차단 사유 2종)의 근거가 된다 |
| 도구 | `code-scan` CLI (블랙박스) |
| 실행 명령 | S-20 산출 트리(`SP/opal-ts106/proj/`, 보조 실측으로 baseline `validate` exit 0 확보 후) 2갈래. **갈래 A**: 관리 매니페스트 `src/core.json`이 덮는 `src/core/`에 `newmod.py`(@header 없음) 신규 → `~/.opal/tools/code-scan/run.sh validate --changed "src/core/newmod.py" [--json]` → `src/core.json` `files{}`에 엔트리 기입 후 재실행. **갈래 B**: 매니페스트 밖 `src/outside/loose.py` 신규(트리에 `git` work-tree + 커밋 1건 존재 확인 `git rev-parse --verify HEAD`) → 동일 `validate --changed` → `scopes.src.anchors`에 `outside` 추가 후 `scaffold` → 엔트리 기입 → 재실행 |
| 결과 | **Pass** |
| 상세 | **갈래 A**: `validate: 2 violation(s) — coverage 0% (0/1)` · **exit 2** · `violations[]`에 `{'code': 'uncovered', 'sub': 'no_entry', 'file': 'src/core/newmod.py'}` **1건** · `counts.newly_uncovered` = **0**(기대대로 0이 정상) → `no_entry`가 카운터 없이도 차단함을 런타임 실증. (부수 관측: 동반 위반 `{'code':'worker_scope_violation','sub':'files_key_removed'}` 1건.) **갈래 B**: 트리에 커밋 1건 존재(`git HEAD 존재: YES`) 확인 후 → `validate: 1 violation(s)` · **exit 2** · `{'code':'uncovered','sub':'newly_uncovered','file':'src/outside/loose.py'}` · `counts.newly_uncovered` = **1**(≥1 충족). **공통 전이**: A는 매니페스트 `files{}` 엔트리 기입만으로 `validate: OK — coverage 100% (1/1)` **exit 0** · `no_entry` 위반 **0건** · 전체 위반 `[]`. B는 `scaffold`가 `anchors` 밖 디렉토리를 만들지 않아(`created=0 updated=2 added=0`) `scopes.src.anchors`에 `outside` 추가 후 `scaffold`(`created=1 added=1`) → 엔트리 기입 → `validate: OK — coverage 100% (1/1)` **exit 0** · `newly_uncovered` **0**. ⇒ (b) CLOSE 게이트 차단이 **모드별 2경로 모두에서 런타임 발동**하고 기입으로 해소됨을 실증. **관측 병기**: 갈래 B의 해소에는 「@header 기입」 외에 `anchors`(소유자 관할 필드) 확장이 선행 필요했다 — 매니페스트 밖 신규 디렉토리는 `scaffold` 단독으로 편입되지 않는다 |

#### S-24: 경계 — 게이트 순서 계약 (`auto_pass` × 문서 전용 → 거부 아닌 skip)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 (P0 — `[MUST]` 순서 계약의 결정적 조합) |
| 대상 | F-005 / `state_tool.py` 훅 게이트 ⑥(`auto_pass` 거부)이 ③④⑤(graceful skip) **뒤**에 위치하는지 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | 임시 태스크 폴더 `/tmp/opal-ts106/docauto/` — `.opal/code-scan.json` **유효**(게이트 ③ 통과) + PLAN.md **존재**(게이트 ④ 통과) + PLAN.md §4.2 대상 파일이 **`.md`만**(게이트 ⑤ `doc_only_task` 해당). EXECUTE 첫 행에 `--auto-pass`를 실어 호출 |
| 기대 결과 | `auto_pass`가 실려 있어도 게이트 ⑤에서 먼저 스킵되어 **거부가 발생하지 않는다** — `skipped` · `reason: doc_only_task` · **exit 0**. **⑥을 ③④⑤ 앞에 두는 구현에서는 이 케이스가 거부로 실패하므로, 순서 계약 위반을 탐지하는 유일한 시나리오다** |
| 도구 | `state-tool` CLI (블랙박스) |
| 실행 명령 | 픽스처 `SP/opal-ts106/docauto/`(`.opal/code-scan.json` 유효 = 게이트 ③ 통과 · PLAN.md 존재 = ④ 통과 · §4.2 대상 `- **파일**: \`docs/GUIDE.md\`, \`README.md\`` = `.md`만 → ⑤ 해당). (a) `run.sh verify <T> --code-scan-citation-check` (b) `run.sh mark <T> --task-step execute.implement --done --auto-pass` (c) 판별력 대조군 `SP/opal-ts106/negauto/`(§4.2 대상 `.py` + 인용 0건)에 동일 `--auto-pass` 호출 |
| 결과 | **Pass** |
| 상세 | (a) `{"ok": true, "code_scan_citation_check": "skipped", "reason": "doc_only_task", "target_files": ["docs/GUIDE.md", "README.md"], "matched_tokens": []}` · **exit 0** — 기대 3요소(`skipped`·`doc_only_task`·exit 0) 전건 일치. (b) `--auto-pass`를 실은 EXECUTE 첫 행 `mark` → `{ok: True, row_id: 12, stage: EXECUTE, status: done, owner: auto}` · **exit 0** · **거부 0건** → 게이트 ⑤가 ⑥보다 먼저 평가됨을 실증. (c) **판별력 확인** — 동일 `--auto-pass`를 `.py` 대상 + 인용 0건 폴더에 실었을 때는 `{"ok": false, "error": "code_scan_citation_unmet", "missing": ["auto-pass cannot bypass code-scan citation gate"]}` · **exit 1**로 게이트 ⑥이 정상 발동한다 → (b)의 통과가 「게이트가 죽어서」가 아니라 「순서가 맞아서」임을 대조군으로 증명(공허한 통과 배제) |

#### S-25: 경계 — 잔여 스킵 분기 3종 + 플래그 상호배타

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | F-005 / 훅 게이트 ②(`force` 우회) · ③(`code_scan_unavailable`) · ④(`plan_md_absent`) + `cmd_verify` 플래그 상호배타 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | 임시 폴더 3종 — (i) S-9의 인용 0건 폴더에 `--force --note` 부여 (ii) `.opal/code-scan.json` **부재** 트리의 태스크 폴더 (iii) PLAN.md **부재** 태스크 폴더 |
| 기대 결과 | ① (i) `force` → 훅 미발동, EXECUTE 첫 행 `mark` **통과**(exit 0) + 의사결정 로그에 `--note` 기재 ② (ii) → `skipped` · `reason: code_scan_unavailable` · exit 0 ③ (iii) → `skipped` · `reason: plan_md_absent` · exit 0 ④ `verify --code-scan-citation-check`를 `--evidence-check`·`--clarification-check`와 동시 지정 → 상호배타 거부(exit 1). **`reason` 도메인 3값이 전건 실관측되어 닫힘이 증명된다** |
| 도구 | `state-tool` CLI (블랙박스) |
| 실행 명령 | (i) `run.sh mark <force픽스처T> --task-step execute.implement --done --force --note "…"` + `cat <T>/STATE.md` 의사결정 로그 판독 + `state.json` rows[].note 판독 / (i)-b `--force` 단독(`--note` 없이) / (ii) `.opal/code-scan.json` 부재 트리(`nocfg`) `verify` + `mark` / (iii) PLAN.md 부재 폴더(`noplan`) `verify` + `mark` / (iv) `run.sh verify <T> --code-scan-citation-check --evidence-check` · `… --clarification-check` · 3플래그 동시 (3조합) |
| 결과 | **Fail** (②③④ Pass / **① 「의사결정 로그에 `--note` 기재」 미충족**) |
| 상세 | **① 부분 미충족.** `--force --note` → 훅 미발동, `mark` **통과 exit 0**(`{ok: True, status: done, owner: PM}`) — 통과 축은 충족. 그러나 `<T>/STATE.md` 「## 의사결정 로그」 표가 **헤더만 남은 빈 표**이고 `--note`는 `state.json` rows[].note(`S-25 (i) 우회 관측 — 인용 0건이나 force 통과`)에만 남았다 → **기대 「의사결정 로그에 `--note` 기재」 불충족**. 소스 확인: `state_tool.py:1930-1941`의 `cmd_mark`는 `decision`을 `worker_scope_force`·`gate_artifact_force` 2경로에서만 설정하고 **code-scan 인용 게이트 `--force` 우회에는 `decision`을 설정하지 않는다**(`sync_state_md` 호출에 `decision=None` 전달). 반면 `pm-review-gate.md` 항목 14는 「우회 사실은 의사결정 로그에 남는다(§자가 진단 4번 `--force` 0건 확인 대상)」로 단언하므로 **문서↔집행 불일치**다. 091 선례(`gate_artifact_force` 강제 기록)와도 비대칭. (i)-b 부수 확인: `--force` 단독은 `note_required_for_force`(exit 1)로 거부되어 `--note` 필수 자체는 집행된다. **② Pass**: `code-scan.json` 부재 → `verify` `{skipped, reason: "code_scan_unavailable"}` exit 0 / `mark` exit 0·ok True. **③ Pass**: PLAN.md 부재 → `{skipped, reason: "plan_md_absent"}` exit 0 / `mark` exit 0·ok True. **④ Pass**: 3조합 전건 `{"ok": false, "error": "evidence_check_flag_conflict", "flags": [...]}` · **exit 1** — `flags` 배열에 실제 지정 플래그가 정확히 실린다. `reason` 도메인 3값(`code_scan_unavailable`/`plan_md_absent`/`doc_only_task`)은 ②③ + S-24 (a)로 **전건 실관측**되어 닫힘 증명. **관측 병기(경미)**: ④의 `message`는 기존 코드 재사용으로 「--evidence-check와 --clarification-check는 동시 사용 불가」 2종만 언급해 신규 플래그가 문면에서 빠져 있다 — `flags` 배열은 정확하므로 판정 영향 없음 |

### L3. 사용자 협업 (수동, [SUPERVISOR] 마커)

#### S-21: 소유자 리뷰 게이트 실제 작동 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | F-001 / `opcmb` 소유자 리뷰 게이트 (`status: draft` → `reviewed` 전환은 규정상 소유자 확정 사항) |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업)** — 자동화 불가. 리뷰 게이트의 목적이 "도구가 판정하지 않는 도메인 경계·`include`/`exclude` 정책을 소유자가 확정"하는 것이므로 사람 판단 자체가 검증 대상이다 |
| 조건 | S-20 완료 후 `/tmp/opal-ts106/proj/.opal/code-map/index.json`이 `status: draft` 상태로 존재 |
| 기대 결과 | `//opcmb`가 `scaffold`로 넘어가기 전에 초안의 `scopes`(root/anchors/stripPrefix/include/exclude)·`layerRules`·`domains`를 캡틴에게 제시하고 **승인 없이 진행하지 않는다**. 캡틴이 `status: reviewed` 전환을 확정한 뒤에만 `scaffold`가 실행된다 |
| 실행자 | [SUPERVISOR] — 캡틴 수동 확인 필요 |
| 결과 | **[SUPERVISOR 대기]** — opal-test-agent 미실행(L3 M3 위임). 캡틴 확인 후 Pass/Fail 기록 |
| 상세 | _{캡틴 확인 후 기록}_ — **opal-test-agent 사전 메모**: 게이트의 사전 조건 성립을 S-20 실행 중 확인했다. `discover`가 `index.json`을 `status: "draft"` · `origin: "discover"` · `note: "OWNER REVIEW REQUIRED — headerSource/anchors/stripPrefix/include 확인 후 status를 reviewed로 변경"` 상태로 생성하며, 배포본 SKILL.md STEP 3이 「초안 값을 요약해 제시하고 **사용자 확인**을 받는다. 승인 전에는 STEP 4·5로 진행하지 않는다」 · STEP 4가 「승인이 나오지 않은 상태에서 `status`를 임의로 `reviewed`로 바꾸지 않는다」를 명문화하고 있음을 실판독했다(문면 존재 = Pass 조건의 필요조건 충족). 다만 **실제 `//opcmb` 호출 시 에이전트가 멈추는지**는 사람 판단이 검증 대상이므로 캡틴 확인이 필요하다. 임시 프로젝트 트리는 회수 정책에 따라 삭제했으므로 확인 시 픽스처 재생성이 필요하다 — 재생성 절차는 S-20 「실행 명령」 칸 참조 |

**PM 요청 양식 (S-21)**

```
[SUPERVISOR 확인 요청] S-21 — opcmb 소유자 리뷰 게이트
1. 임시 프로젝트 경로: /tmp/opal-ts106/proj/
2. 확인 사항: //opcmb 실행 시 discover 직후 멈추고 index.json 초안(scopes·layerRules·domains)을 제시하는가
3. 판정: 승인 없이 scaffold로 넘어가면 Fail / 제시 후 대기하면 Pass
4. 회신: Pass / Fail + 관찰 내용 1줄
```

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| R-1 AC(a) | H-5 | L1 | S-1 | _{EXECUTE 워커가 채움}_:`[T106/L1-R1a]` | frontmatter 5필드 |
| R-1 AC(b) | H-5, H-9 | L2 | S-2 | (CLI 블랙박스 — 테스트 파일 없음):`[T106/L2-R1b]` | alias 30종·라우팅 결정성 |
| R-1 AC(c) | H-5 | L1 | S-3 | (CLI 블랙박스 — 테스트 파일 없음):`[T106/L1-R1c]` | manifest 3단 시퀀스 |
| R-1 AC(d) | H-5 | L1 | S-3 | (CLI 블랙박스 — 테스트 파일 없음):`[T106/L1-R1d]` | inline 종료 분기 |
| R-2 AC(a) | H-1 | L1 | S-4 | (CLI 블랙박스 — 테스트 파일 없음):`[T106/L1-R2a]` | §12 유지 행 + 각주 |
| R-2 AC(b) | H-1 | L1 | S-5 | (CLI 블랙박스 — 테스트 파일 없음):`[T106/L1-R2b]` | (4단) 전환 |
| R-2 AC(c) | H-1 | L1 | S-6 | (CLI 블랙박스 — 테스트 파일 없음):`[T106/L1-R2c]` | 미수행 탐지 조건 |
| R-3 AC(a) | H-2 | L1 | S-7 | (CLI 블랙박스 — 테스트 파일 없음):`[T106/L1-R3a]` | 2단 표 |
| R-3 AC(b) | H-2 | L1 | S-7 | (CLI 블랙박스 — 테스트 파일 없음):`[T106/L1-R3b]` | 전환 조건·오버라이드 구분 |
| R-3 AC(c) | H-2 | L1 | S-7 | (CLI 블랙박스 — 테스트 파일 없음):`[T106/L1-R3c]` | 직행 금지 비모순 |
| R-4 AC(a) | H-2 | L1 | S-8 | (CLI 블랙박스 — 테스트 파일 없음):`[T106/L1-R4a]` | 후보 3종 비교·확정 |
| R-4 AC(a) 교체형 잔존/채택 | H-2 | L1 | S-22 | (CLI 블랙박스 — 테스트 파일 없음):`[T106/L1-R4a2]` | **구형 잔존0 + 신형 채택** |
| R-4 AC(b) | H-10 | L2 | S-9 | (CLI 블랙박스 — 테스트 파일 없음):`[T106/L2-R4b]` | **RED-first 대상** — 미충족 exit 1 |
| R-4 AC(c) | H-10 | L2 | S-10 | (CLI 블랙박스 — 테스트 파일 없음):`[T106/L2-R4c]` | **RED-first 대상** — 충족 exit 0 |
| R-5 AC(a) | H-7, H-8 | L2 | S-11 | (CLI 블랙박스 — 테스트 파일 없음):`[T106/L2-R5a]` | 오탐 0건 |
| R-5 AC(b) | H-7 | L1 | S-12 | (CLI 블랙박스 — 테스트 파일 없음):`[T106/L1-R5b]` | 폴백 조건 3곳 |
| R-6 AC(a) | H-4 | L2 | S-13 | (CLI 블랙박스 — 테스트 파일 없음):`[T106/L2-R6a]` | 행 수·key 불변 |
| R-6 AC(b) | H-4 | L2 | S-14 | (CLI 블랙박스 — 테스트 파일 없음):`[T106/L2-R6b]` | 기존 폴더 조회 |
| R-6 AC(c) | H-6 | L2 | S-15 | (CLI 블랙박스 — 테스트 파일 없음):`[T106/L2-R6c]` | 8 파이프라인 graceful skip |
| R-6 AC(d) | H-4 | L2 | S-16 | (CLI 블랙박스 — 테스트 파일 없음):`[T106/L2-R6d]` | spec-validate 0건 |
| 완료기준(install) | H-11 | L2 | S-17 | (CLI 블랙박스 — 테스트 파일 없음):`[T106/L2-INST]` | 배포 반영·스크립트 무변경 |
| 제약 ⑤ (DEC-6) | H-3 | L1 | S-18 | (CLI 블랙박스 — 테스트 파일 없음):`[T106/L1-CHLOG]` | 문서별 변경이력 형태 |
| 부속(스킬 수 셀) | H-12 | L1 | S-19 | (CLI 블랙박스 — 테스트 파일 없음):`[T106/L1-DRIFT]` | 드리프트 보정 |
| R-2 (목표달성·갱신 국면) | H-1 | L2 | S-23 | (CLI 블랙박스 — 테스트 파일 없음):`[T106/L2-GOAL2]` | **탐지 실발동 → CLOSE 차단** |
| R-5 (경계·순서 계약) | H-7 | L2 | S-24 | (CLI 블랙박스 — 테스트 파일 없음):`[T106/L2-ORDER]` | **순서 위반 탐지 유일 시나리오** |
| R-5 (경계·스킵 분기) | H-7 | L2 | S-25 | (CLI 블랙박스 — 테스트 파일 없음):`[T106/L2-SKIP3]` | `reason` 3값 도메인 닫힘 |
| **목표달성** | H-5 | L2 | S-20 | (CLI 블랙박스 — 테스트 파일 없음):`[T106/L2-GOAL]` | 자산 실제 생성 — 생성 국면 완결 |
| **목표달성(사람 게이트)** | H-5 | L3 | S-21 | (수동) | 소유자 리뷰 게이트 작동 |

> 커버리지: R-1~R-6 AC 17건 + 부속 3건 + 목표달성 2건 = **26항 전건 매핑, 미매핑 시나리오 0건**.

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | `ruff check opal/tools/state-tool/state_tool.py --output-format concise` | **Pass** (신규 지적 0건) | 실측 5건 — `F401` `datetime.datetime` unused(`:28`) · `E741` ambiguous `l`(`:478`) · `F841` `status`(`:1136`) · `F841` `prev_status`(`:1994`) · `F541` f-string no placeholder(`:2045`). 동일 명령을 `git show HEAD:` 복원본에 실행하니 **동일 5종**(줄번호만 이동: `:26`·`:473`·`:1131`·`:1980`·`:2031`) → **선존 5건, 106 신규 0건**. 회귀 아님 |
| 2 | 타입 체크 | `mypy opal/tools/state-tool/state_tool.py` | **Skip** (도구 미설치) | `command not found: mypy` — 이 환경에 미설치. 프로젝트에 `mypy.ini`/`[tool.mypy]` 설정도 없다. 대체 게이트로 `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -q` → **379 passed, 3 skipped, 98 subtests passed, 0 failed**(72.45s) 실행 |
| 3 | 포맷터 | `black --check` (미설치) → `python3 -m py_compile opal/tools/state-tool/state_tool.py` | **Skip** (도구 미설치) / 문법 게이트 **Pass** | `black` 미설치로 포맷 검사 불가. 대체로 `py_compile` 실행 → **exit 0**(문법 오류 0건) |
| 4 | `@header` 커버리지 (`code-scan validate --changed`) | `~/.opal/tools/code-scan/run.sh validate --changed "<변경 16파일 csv>" [--json]` (목록 = `git diff --name-only HEAD` + untracked, `tasks/106-*` 제외) | **Fail** — exit 2 | `validate: 1 violation(s) — coverage 9.1% (1/11)` · **exit 2**. 차단 위반 1건 = `{'code': 'uncovered', 'sub': 'newly_uncovered', 'file': 'opal/tools/state-tool/tests/test_state_tool.py'}`. `counts` = `uncovered 10`(`newly_uncovered` **1** + `pre_existing` 9). `pre_existing` 9건(`docs/*.md` 3 · `harness/*.md` 2 · `opal-pm.md` · `dispatch-process.md` · `README.md` · `state_tool.py`)은 비차단. **원인 규명**: `test_state_tool.py`의 `@header` 마커는 오프셋 4에 있으나 블록 종료 `}`가 **11,762바이트**(HEAD 시점 10,741바이트) 지점이어서 `code-scan.js:39 HEADER_READ_BYTES = 8192` 슬라이스 안에서 닫히지 않는다 — 즉 **선존 도구 한계**(PM이 Step 4에서 `state_tool.py`에 대해 같은 계열 결함을 기록)이며, 106이 이 파일을 변경 목록에 올림으로써 표면화됐다. 다만 `state_tool.py`는 비차단 `pre_existing`으로 축퇴하는 반면 `test_state_tool.py`는 **차단 `newly_uncovered`**로 분류된다(`classifyUncovered`의 HEAD 슬라이스 파싱 결과 차이). **영향**: `header-rules.md` §갱신 시점 (b)에 따라 **CLOSE 진입이 차단된다** — PM 처치 필요 |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | **Pass** (0건) | 변경 16파일 전수에 `grep -nEi '(api[_-]?key|secret|passwd|password|token|private[_-]?key|access[_-]?key)\s*[:=]\s*["'\'']\w{16,}["'\'']|AKIA[0-9A-Z]{16}|sk-\w{20,}|ghp_\w{20,}|-----BEGIN .*PRIVATE KEY-----'` 실행 → **HIT 0건**. 추가로 `git diff -- state_tool.py` 추가 라인에 `/Users/`·`/home/`·`password`·`token` grep → 절대 홈경로·시크릿 리터럴 **0건**(`matched_tokens`·`_is_safe_artifact_token` 식별자 매칭뿐, 시크릿 아님) |
| 2 | .gitignore 확인 | **Pass** | `.gitignore` 존재. `git status --porcelain --ignored=no | grep -E '\.(env|pem|key|p12)$|credentials|secrets'` → **0건**. 변경 16파일 각각 `git check-ignore -q` → **ignore 대상 0건**(산출물이 실수로 무시되지 않음). 임시 픽스처는 전부 프로젝트 밖 세션 스크래치패드에 생성해 워킹트리 오염 0건 |
| 3 | 임시 자원(`/tmp/opal-ts106/`) 정리 확인 | **Pass** | 임시 자원 위치를 `/tmp` 대신 세션 스크래치패드(`/private/tmp/claude-501/.../scratchpad/`) 하위로 잡았다(§2.1 허용 문면). 회수 대상 — `opal-ts106/`(픽스처 10종: red-neg·neg·pos·docauto·docauto2·negauto·force·force2·nocfg·noplan·proj·proj-s20-snapshot) · `state-tool-HEAD/`(개정 전 베이스라인 사본) · `s15-skip/`·`s15-pass/`(8 파이프라인 A/B 트리 32개) · 헬퍼 스크립트 3종. TEST 종료 시 `rm -rf` 후 `find` 실측 **잔여 0건**. 프로젝트 워킹트리는 `git status --short`가 개정 대상 15파일 + 신규 2디렉토리만 보여 픽스처 유출 **0건** |

## 7. 판정

**Partial Fail** -- 시나리오 25건 중 **Pass 22 / Fail 2(S-20·S-25) / [SUPERVISOR 대기] 1(S-21)**. 핵심 기능(R-4 도구 판정 승격 · R-5 오탐 0건 · R-6 회귀 보존)은 전건 Pass이며 보안도 Pass이므로 Critical Fail이 아니다. Fail·차단 항목은 아래 3건이다.

1. **§5 #4 `@header` 커버리지 — exit 2 (차단)**: `code-scan validate --changed <변경 16파일>`이 `opal/tools/state-tool/tests/test_state_tool.py`에 대해 `{uncovered, sub: newly_uncovered}` 1건으로 **exit 2**를 반환한다. `header-rules.md` §갱신 시점 (b)에 따라 **CLOSE 진입이 차단되는 상태**다. 근인은 선존 도구 한계(`code-scan.js:39 HEADER_READ_BYTES = 8192` < 해당 파일 `@header` 블록 11,762바이트)이며 106이 그 파일을 변경 목록에 올려 표면화했다. 106 회귀가 아니라 **선존 결함의 표면화**이나, 게이트가 실제로 닫히므로 PM 처치가 필요하다.
2. **S-20 (목표달성·생성 국면) Fail**: `opcmb` SKILL.md의 `manifest` 시퀀스를 문면 그대로 완주했을 때 자산은 전건 생성되나(①~④ Pass) 최종 `validate`가 **exit 2**(위반 6건 = `uncovered:incomplete` ×3 + `draft` ×3)로 기대 exit 0에 미달한다. 원인은 STEP 3·4가 `discover`가 비운 `layerRules`/`domains`를 소유자가 채우도록 지시하지 않는 문면 결손 + `scaffold` 골격의 `draft: true`가 시퀀스 내에서 해소되지 않는 설계다. 보조 실측으로 두 값을 채우면 `validate` exit 0에 도달함을 확인했으므로 **도달 불가가 아니라 문면 결손**이다.
3. **S-25 ① 부분 Fail**: `--force --note` 우회는 통과(exit 0)하나 **`--note`가 STATE.md 의사결정 로그에 기재되지 않는다**(빈 표 실측, `state.json` rows[].note에만 기록). `pm-review-gate.md` 항목 14가 「우회 사실은 의사결정 로그에 남는다(§자가 진단 4번 `--force` 0건 확인 대상)」로 단언하므로 **문서↔집행 불일치**이며, 091 선례(`gate_artifact_force` 강제 기록, `state_tool.py:1933-1937`)와 비대칭이다. 자가 진단 4번의 감시 능력이 이 게이트에는 미치지 않는다.

**RED 증거**: S-9·S-10은 RED-first 트랙으로 개정 전 베이스라인(HEAD `69f5ce1`) 복원본에서 동일 픽스처 실패를 실관측한 뒤 GREEN을 기록했다 — 상세는 `RED-EVIDENCE.md`.

**PM 판단 요청 3건**: (a) §5 #4 차단 처치 방향(해당 파일 `@header` 축약 vs `HEADER_READ_BYTES` 상향 vs 명시적 예외) (b) S-20 목표달성 기준을 「`validate` exit 0」으로 유지할지 아니면 SKILL.md STEP 3·4 문면 보강으로 처리할지 (c) S-25 ①의 의사결정 로그 기재를 구현으로 맞출지(`state_tool.py` `decision` 설정 추가) 문서로 맞출지(항목 14 문면 정정). 부가로 S-12는 「세 문면의 조건 집합 일치」 축에서 `header-rules.md` (d) 3번째 항목만 갈리므로 판정 축 확정을 요청한다(§3 S-12 「상세」 참조). **§4 매핑 표 「테스트 파일:케이스」 열은 미기입 상태로 남겼다** — 본 검증은 테스트 파일이 아닌 실 CLI 블랙박스 실행이며, 그 칸의 기입 주체는 EXECUTE 워커로 지정되어 있다.

### PM Gate 체크 (7대 강제 룰)

- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 (실 도구 블랙박스 실행 + 실 산출물 판독만 사용)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐 (S-1~S-20, S-22~S-25)
- [x] 가설↔시나리오 매핑(§4) 완전 — 미매핑 시나리오 0건
- [x] L1/L2/L3 계층 명시 (전 시나리오)
- [x] L3 [SUPERVISOR] 마커 존재 + PM 요청 양식 첨부 (S-21)
- [x] 리스크 가설 표(§1) H-1~H-12 전건이 시나리오와 1:N 매핑
- [x] 모든 시나리오에 실행 방식(M1/M2/M3) 명시
- [x] **FE 변경 시 M2 시나리오 포함** — 해당 없음(변경 영역에 FE 화면·컴포넌트·인증/인가·외부 API 연동 0건. `dashboard/frontend/` 무변경)
- [x] **목표 커버** — R-1~R-6 전건이 §4에 커버 + 목표달성 시나리오 3건 존재 — S-20(생성 국면: 자산 실제 생성, L2)·S-21(생성 국면 사람 게이트, L3)·S-23(갱신 국면: 탐지 실발동 → CLOSE 차단, L2)

## 8. 재검증 (Step 17·18·19 보강 후 — PM 실측)

> TEST 1차에서 Fail 2건(S-20·S-25 ①)이 나와 PM이 Step 17·18을 추가 배정해 결함을 해소하고, Step 19로 회귀를 고정했다. 아래는 보강 후 재판정이다.

| 시나리오 | 1차 | 보강 | 재판정 근거 (PM 실측) |
|---------|-----|------|---------------------|
| **S-20** 목표달성·생성 국면 | ❌ Fail | Step 17 | **Pass** — SKILL.md 229→268행. STEP 3에 빈 `layerRules`·`domains` 소유자 확정 지시 + `code-scan-management.md` §2번 원문 인용, STEP 4에 `reviewed` 전환 전 반영 확인 3단, STEP 6에 **정상 종료 2종**(골격 완료 exit 2 = "기입 대기" 정상 / 기입 완료 exit 0) 구분. Step 17 워커 재완주 실측: 정상 경로 = 골격 완료·`draft` 3건·커버리지 100%, 기입 후 exit 0. **음성 경로(빈 값 강행)에서 1차 Fail 관측값이 그대로 재현**되어 원인이 문면 결손임이 확정됐다 |
| **S-25 ①** force 우회 로그 | ❌ Fail | Step 18 | **Pass** — `decision = code_scan_citation_force` 기재 확인(`STATE.md` 「## 의사결정 로그」 행 1건). `ERROR_CODES` **46 불변**(사유 키는 `decision` 문자열). 오탐 0건 대조군 2건(문서 전용·인용 존재 + force → 무기재) — 091 `gate_artifact_force` 동형 계약 |
| **S-25 ②③④** | ✅ Pass | — | 변동 없음 |
| **회귀 고정** (신설) | — | Step 19 | **Pass** — 인용 게이트 동작 4케이스 신설(`test_c1_`~`test_c4_`). `pytest` **383 passed, 3 skipped, 98 subtests passed, 0 failed**(1차 379 + 4, 감소 0건) · 테스트 메서드 382→386(+4, 소실 0건) · mock 0건 · `ERROR_CODES` 46 불변 · `schema/*.json` 무변경 |

### 재검증에서 드러난 사실 2건

- **`--auto-pass`는 그 자체로 의사결정 로그를 남긴다** — Step 19 워커가 PM 지시 전제("문서 전용 + force → 로그 전체 공백")를 직접 관측으로 반증했다. `--auto-pass` 경로는 093-era 계약이 `agentic auto-pass at row N` 행을 별도로 쓴다. 워커는 테스트를 기대에 맞추지 않고 판정 축을 `code_scan_citation` 포함 행으로 **좁혀 격리**했다(옳은 처치). 「로그 전체 공백」 단언은 force 경로에서만 성립한다
- **PLAN §3.4.2 게이트 ② 문면이 구판으로 남아 있었다** — 초판은 `force → return`(조기 반환)인데 Step 18 구현은 「거부만 무력화」다. Step 19 워커가 발견했고 **PM이 PLAN §3.4.2를 개정 근거와 함께 교정**했다(워커는 Guards상 PLAN 무접촉)

### §4 매핑 표 「테스트 파일:케이스」 열

본 검증은 테스트 파일이 아닌 **실 CLI 블랙박스 실행**(`run.sh` subprocess + 실 파일 상태)으로 수행했으므로 해당 열은 `(CLI 블랙박스 — 테스트 파일 없음)`으로 마감한다. 예외는 F-004 인용 게이트 동작 4케이스로, `opal/tools/state-tool/tests/test_state_tool.py`의 `test_c1_`~`test_c4_`가 회귀를 고정한다(Step 19).
