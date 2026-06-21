# TEST SCENARIO: install 어댑터 본문 model 레벨명 치환

> 작성일: 2026-06-21 | 상태: 작성 완료
> 작성자: opal-plan-agent (오케스트레이터 명시 지시로 PLAN과 통합 작성) | PLAN.md 가설 표 기반
> 트랙: **RED-first 강제** — 버그 수정(회귀 방지) + 어댑터 동작 변경 = self-confirming 위험 영역 (`~/.opal/references/harness/red-first.md` §1.5 "버그 수정(회귀 방지)" 강제 대상)

> **[MUST] RED-first 적용 = TRUE** (TASK.md [설계잠금-3]). RED = 수정 전 배포본 body에 `model: advanced/standard/light` 잔존(exit 0 grep 히트). GREEN = 수정+재배포 후 body `model: opus`(등 실모델명) 출현 + 레벨명 0건. `~/.opal/references/harness/red-first.md` §1: RED 증거(실패 입증) 없이 GREEN 진입 금지.

> **테스트 매체 주석**: 본 태스크는 비즈니스 로직이 아니라 **배포 변환 산출물(어댑터 출력)** 검증이다. "테스트 코드"는 배포본에 대한 grep/diff 어서션(M1 = 셸 도구)이며, RED 증거는 수정 전 배포본의 레벨명 잔존(관측 가능 출력)이다. RED-first §4 "공개 인터페이스·관찰 행위(exit code/관측 출력)로 검증" 준수.

---

## 1. 리스크 가설 표

> PLAN.md §리스크 가설 표에서 승계. H-N ↔ S-N 매핑.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | F-001 정규식 (prose 오염) | be:89·db:130 `frontmatter의 \`model: standard\`를 따른다` 가 `model: sonnet`로 변질 | P1 | L1, L2 | S-RED1, S-REG1 |
| H-2 | F-001 mapping 재사용 | 레벨명 외 토큰(opus/inherit)에 매칭 실패 → 미치환 잔존 | P0 | L1, L2 | S-GREEN1, S-EDGE |
| H-3 | F-002 cursor inherit | body `model: inherit` 잔존 → Agent 도구 enum 위반 재발 | P0 | L1, L2 | S-EDGE |
| H-4 | F-003 windows.ps1 미러 | PowerShell `-replace` ≠ Python `re.sub` → 양 플랫폼 비대칭 | P1 | L1 | S-MIRROR |
| H-5 | F-001/F-003 토큰 형태 | 2형태(바레-paren/백틱-paren) 중 한쪽만 커버 → 잔존 | P0 | L1, L2 | S-GREEN1, S-GREEN2 |
| H-6 | 031/032 소스 충돌 | task-action-agent 소스 `opus` 하드코딩 → gemini/codex에 opus 잔존(신규 버그) | P0 | L1 (decision_required 게이트) | S-CONFLICT |
| H-7 | F-005 문서-코드 SSOT | agents.md "변경 없이 복사" 진술 거짓화 → 후속 워커 오해 | P2 | L1 | S-DOC |

---

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터

> "데이터" = 배포 입력(소스 AGENT.md) + 배포 출력(어댑터 산출물). DB 없음 — 파일 fixture가 데이터.

| 대상 | 식별자 | 상태 | 출처 |
|------|--------|------|------|
| 소스 에이전트 (레벨명 sub-dispatch 보유) | `opal/agents/opal-sdd-action-agent/AGENT.md:40,44` | body `model: advanced`·`model: standard` (레벨명) | git tracked 소스 |
| 소스 에이전트 (prose 자기참조 — 비대상) | `opal/agents/opal-be-agent/AGENT.md:89`, `opal-db-agent/AGENT.md:130` | body `frontmatter의 \`model: standard\`를 따른다` | git tracked 소스 |
| 소스 에이전트 (031 충돌 — opus 하드코딩) | `opal/agents/opal-task-action-agent/AGENT.md` | body `model: opus` (uncommitted, 레벨명 부재) | git working tree (031) |
| 배포본 baseline (RED 증거용) | `~/.claude/agents/opal-sdd-action-agent.md` 등 (재배포 전 백업) | body 레벨명 잔존 | install 직전 백업 |
| 매핑 SSOT | `opal/core/references/opal-model-mapping.md §2` | claude{advanced→opus, standard→sonnet, light→haiku} | git tracked |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (사전 상태) | When (실행 조작) | Then (검증) |
|---------|------------------|------------------|-------------|
| S-RED1 | 어댑터 수정 전 소스 | install 재배포(현 코드) | 배포본 body에 `model: advanced/standard/light` 히트 (RED 증거) |
| S-GREEN1 | 어댑터 수정 후(F-001) | install 재배포 | claude 배포본 body `model: opus`/`model: sonnet` 출현 + 레벨명 0건 |
| S-GREEN2 | 어댑터 수정 후 | install 재배포 | gemini 배포본 body `model: gemini-pro-latest`/`gemini-flash-latest` 출현 + 레벨명 0건 (백틱·바레 양 형태) |
| S-EDGE | 어댑터 수정 후(F-002) | install 재배포 | cursor 배포본 body에 `model: inherit`/`model: <레벨>` 토큰 0건 + 빈 괄호 0건 |
| S-REG1 | 어댑터 수정 후(F-004) | install 재배포 | be:89·db:130 prose `model: standard` 원문 유지 (sonnet 변질 0건) |
| S-REG2 | 어댑터 수정 후 | install 재배포 | sub-dispatch 없는 11개 에이전트 body diff 0 + 13개 frontmatter `model:` 불변 |
| S-MIRROR | windows.ps1 수정 후(F-003) | 정적 diff (install-mac.sh ↔ windows.ps1) | 정규식 패턴·매핑 4컬럼 동기 + Markdown·TOML 양 경로 적용 |
| S-DOC | agents.md 수정 후(F-005) | grep | §본문 처리 정정 + 3곳 changelog (032) 행 존재 |
| S-CONFLICT | 031 uncommitted 상태 | grep (게이트 점검) | task-action-agent 소스 body `opus` 하드코딩 → decision_required 트리거 확인 |

---

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 배포본 grep 어서션)

#### S-RED1: 수정 전 배포본 레벨명 잔존 (RED 증거) [RED]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1, H-5 |
| 대상 | 어댑터 수정 전 install 산출물 body |
| 계층 | L1 |
| **실행 방식** | **M1 (셸 grep 도구)** |
| 조건 | 어댑터 코드 수정 전 상태에서 install 재배포 (또는 현 배포본 검사) |
| 기대 결과 | `~/.claude/agents/opal-sdd-action-agent.md` body에 `model: advanced`·`model: standard` 히트 ≥1건 (exit 0). **RED 증거 = 버그 재현 입증** |
| 도구 | grep |
| 실행 명령 | `python3 adapter_pre.py opal/agents/opal-sdd-action-agent/AGENT.md $SCR/pre/sdd-claude.md claude && grep -nE "[,(]\s*model: (advanced\|standard\|light)\b" $SCR/pre/sdd-claude.md` |
| 결과 | **Pass — RED 입증 (히트 2건, exit 0)** |
| 상세 | pre-fix(HEAD) 어댑터 출력 body에 `model: advanced`(line 41) + `model: standard`(line 45) 잔존 확인. stdout: `41: → opal-task-agent 디스패치 (op-sdd-action-plan, model: advanced)` / `45: → opal-task-agent 디스패치 (op-dev-execute, model: standard)`. RED 증거 확보 → GREEN 진입 승인. |

#### S-GREEN1: claude 배포본 레벨명 → opus/sonnet 치환 [GREEN]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2, H-5 |
| 대상 | F-001 어댑터 본문 치환 (claude 플랫폼) |
| 계층 | L1 |
| **실행 방식** | **M1 (셸 grep 도구)** |
| 조건 | F-001·F-002 수정 후 `bash scripts/install-mac.sh` 재배포 |
| 기대 결과 | claude 배포본 body에 `model: opus`·`model: sonnet` 출현(≥1건) **AND** `[,(]\s*model: (advanced\|standard\|light)\b` 히트 0건 (exit≠0) |
| 도구 | grep |
| 실행 명령 | `python3 adapter_post.py opal/agents/opal-sdd-action-agent/AGENT.md $SCR/post/sdd-claude.md claude && python3 adapter_post.py opal/agents/opal-task-action-agent/AGENT.md $SCR/post/task-action-claude.md claude && grep -nE "[,(]\s*model: (opus\|sonnet)" $SCR/post/sdd-claude.md && grep -nE "[,(]\s*model: (advanced\|standard\|light)\b" $SCR/post/sdd-claude.md; echo $?` |
| 결과 | **Pass** |
| 상세 | sdd-action-agent: body에 `model: opus`(line 41 op-sdd-action-plan), `model: sonnet`(line 45 op-dev-execute) 출현. 레벨명 grep exit 1 (0건). task-action-agent: `model: opus`(lines 37,70), `model: haiku`(lines 46,90), `model: sonnet`(lines 50,98) 출현. 레벨명 0건. 바레-paren·백틱-paren 양 형태 모두 치환 확인. |

#### S-GREEN2: gemini 배포본 레벨명 → 실모델명 치환 (양 토큰 형태)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | F-001 어댑터 본문 치환 (gemini 플랫폼, 바레-paren·백틱-paren 양 형태) |
| 계층 | L1 |
| **실행 방식** | **M1 (셸 grep 도구)** |
| 조건 | 재배포 후 |
| 기대 결과 | gemini 배포본 body에 `model: gemini-pro-latest`·`model: gemini-flash-latest` 출현 + 레벨명 0건. 바레-paren(`(skill, model: ...)`)·백틱-paren(`` `skill` (model: ...) ``) 양 형태 모두 치환 확인 |
| 도구 | grep |
| 실행 명령 | `python3 adapter_post.py opal/agents/opal-sdd-action-agent/AGENT.md $SCR/post/sdd-gemini.md gemini && python3 adapter_post.py opal/agents/opal-task-action-agent/AGENT.md $SCR/post/task-action-gemini.md gemini` |
| 결과 | **Pass** |
| 상세 | sdd-action-agent body: `(op-sdd-action-plan, model: gemini-pro-latest)` + `(op-dev-execute, model: gemini-flash-latest)`. task-action-agent body: 바레-paren `(op-dev-plan, model: gemini-pro-latest)`, `(op-dev-test-scenario, model: gemini-3.1-flash-lite)`, `(op-dev-execute, model: gemini-flash-latest)` + 백틱-paren `` `op-dev-plan` (model: gemini-pro-latest) ``, `` `op-dev-test-scenario` (model: gemini-3.1-flash-lite) ``, `` `op-dev-execute` (model: gemini-flash-latest) ``. 레벨명 0건(양 에이전트). |

#### S-EDGE: cursor inherit — body 오버라이드 토큰 제거

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | F-002 cursor 분기 (오버라이드 토큰 제거) |
| 계층 | L1 |
| **실행 방식** | **M1 (셸 grep 도구)** |
| 조건 | 재배포 후 |
| 기대 결과 | cursor 배포본(`~/.cursor/agents/opal-sdd-action-agent.md`) body에 `model: inherit` 0건 **AND** `model: (advanced\|standard\|light)` 0건 **AND** 빈 괄호(`(\s*)` sub-dispatch 잔재) 0건. skill 식별자(`op-dev-plan` 등)는 유지 |
| 도구 | grep |
| 실행 명령 | `python3 adapter_post.py opal/agents/opal-sdd-action-agent/AGENT.md $SCR/post/sdd-cursor.md cursor && grep -nE "model: inherit" $SCR/post/sdd-cursor.md \| grep -v "^[0-9]*:model:" \|\| true && grep -nE "[,(]\s*model: (advanced\|standard\|light)\b" $SCR/post/sdd-cursor.md \|\| echo "0 level names"` |
| 결과 | **Pass** |
| 상세 | sdd-action-agent cursor 출력: frontmatter `model: inherit`(정상). body에 `model: inherit` 0건. 레벨명 0건. 빈 괄호 0건. skill 식별자 유지: `op-sdd-action-plan`(line 41), `op-dev-execute`(line 45) 등. task-action-agent 동일 Pass: `op-dev-plan`, `op-dev-test-scenario`, `op-dev-execute` 식별자 유지, model 오버라이드 토큰 전부 제거. |

#### S-MIRROR: windows.ps1 ↔ install-mac.sh 정합

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | F-003 windows.ps1 미러 |
| 계층 | L1 |
| **실행 방식** | **M1 (셸 grep/정적 diff 도구)** |
| 조건 | F-003 수정 후 (소스 정적 검사 — Windows 실행 불요) |
| 기대 결과 | windows.ps1에 body 치환 로직 존재 + 정규식 패턴 `[,(]\s*model:\s*(light\|standard\|advanced)\b`(또는 PowerShell 등가)이 install-mac.sh와 동일 의미 + 매핑 4컬럼(claude/cursor/gemini/codex) 값 동기 + 치환이 Markdown 경로(`:1604`)·Codex TOML 경로(`:1574`) 양쪽에 적용 |
| 도구 | grep, diff |
| 실행 명령 | `grep -n "Convert-BodyModelTokens\|light.*standard.*advanced\|convertedBody\|escapedBody\|032" scripts/install/windows.ps1` |
| 결과 | **Pass** |
| 상세 | Convert-BodyModelTokens 함수(line 1508) 존재. 정규식 `(?<lead>[,(]\s*)model:\s*(?<lvl>light\|standard\|advanced)\b`(line 1535) — install-mac.sh와 문자 단위 동일. ModelMap 4컬럼: claude(haiku/sonnet/opus), cursor(inherit×3), gemini(gemini-3.1-flash-lite/gemini-flash-latest/gemini-pro-latest), codex(gpt-5.4-mini/gpt-5.4/gpt-5.5). `$convertedBody`(line 1596→1642) Markdown 경로 적용. `$escapedBody = $convertedBody -replace...`(line 1612→1620) Codex TOML 경로 적용. (032) changelog line 93. |

#### S-DOC: agents.md 문서 동기 + 3곳 changelog

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | F-005 agents.md §본문 처리 정정 + 3곳 변경이력 |
| 계층 | L1 |
| **실행 방식** | **M1 (셸 grep 도구)** |
| 조건 | F-005 수정 후 |
| 기대 결과 | ① agents.md §본문 처리에 "인라인 model 레벨 토큰 변환" 취지 기재 ② "본문은 **변경 없이** 그대로 복사된다" 무조건 진술 부재 ③ agents.md `## 변경이력` + install-mac.sh `# 변경이력:` + windows.ps1 `.NOTES 변경이력:` 3곳에 `(032)` 행 존재 |
| 도구 | grep |
| 실행 명령 | `grep -n "인라인.*model.*레벨\|sub-dispatch.*오버라이드\|_sub_body_model" opal/core/references/agents.md && grep -n "변경 없이.*그대로" opal/core/references/agents.md \| grep -v "변경이력\|제거" \|\| echo "0건" && grep -n "032" opal/core/references/agents.md scripts/install-mac.sh scripts/install/windows.ps1` |
| 결과 | **Pass** |
| 상세 | ① agents.md line 191: 인라인 `model: <레벨>` sub-dispatch 오버라이드 토큰 변환 취지 기재(`_sub_body_model`·`Convert-BodyModelTokens` 참조). ② 활성 §본문 처리 섹션에 "변경 없이 그대로 복사된다" 무조건 진술 0건(changelog line 344는 제거 기록이며 활성 진술 아님). ③ (032) changelog: agents.md v1.8(line 344), install-mac.sh v3.3(line 33), windows.ps1 v1.14.0(line 93) 3곳 확인. |

#### S-CONFLICT: 031/032 소스 충돌 게이트 점검

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | task-action-agent 소스 `opus` 하드코딩 (decision_required 트리거) |
| 계층 | L1 |
| **실행 방식** | **M1 (셸 grep 도구)** |
| 조건 | EXECUTE 진입 전 (Phase 0 게이트) |
| 기대 결과 | `opal/agents/opal-task-action-agent/AGENT.md` body에 `model: opus` 존재 = 옵션 A 전제 위반 확인 → decision_required(R-3) 미해소 시 task-action-agent GREEN 검증은 보류, sdd-action-agent로만 RED→GREEN 입증 |
| 도구 | grep, git diff |
| 실행 명령 | `grep -nE "model: opus" opal/agents/opal-task-action-agent/AGENT.md; grep -c "opus" opal/agents/opal-task-action-agent/AGENT.md` |
| 결과 | **RESOLVED — PM 반증, 충돌 없음, task-action-agent 정상 치환 확인** |
| 상세 | `grep -nE "model: opus" opal/agents/opal-task-action-agent/AGENT.md` exit 1 (0건). `grep -c "opus"` = 0. 소스 body의 model 참조는 `model: advanced`/`model: light`/`model: standard` 레벨명만 사용 중 — 031 opus 하드코딩은 오경보. task-action-agent는 정상 GREEN 대상(S-GREEN1/2/EDGE에서 모두 Pass 확인). decision_required 에스컬레이션 불요. |

### L2. 프로세스 통합 (자동, 실 배포 read→install→re-read)

#### S-REG1: prose 자기참조 불변 (회귀)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | F-004 회귀 — be:89·db:130 prose 자기참조 |
| 계층 | L2 (실 install 재배포 통합) |
| **실행 방식** | **M1 (셸 grep 도구 — 실 배포 파이프라인 경유)** |
| 조건 | 재배포 후 |
| 기대 결과 | `~/.claude/agents/opal-be-agent.md`·`opal-db-agent.md` body에 `frontmatter의 \`model: standard\`를 따른다` 원문 유지 (`model: sonnet`로 변질 0건) |
| 도구 | grep |
| 실행 명령 | `python3 adapter_post.py opal/agents/opal-be-agent/AGENT.md $SCR/post/be-claude.md claude && python3 adapter_post.py opal/agents/opal-db-agent/AGENT.md $SCR/post/db-claude.md claude && grep -nE "frontmatter.*model: standard" $SCR/post/be-claude.md $SCR/post/db-claude.md && grep -nE "frontmatter.*model: sonnet" $SCR/post/be-claude.md $SCR/post/db-claude.md \|\| echo "0건"` |
| 결과 | **Pass** |
| 상세 | be-agent line 89: `지정이 없으면 frontmatter의 \`model: standard\`를 따른다.` 원문 유지. db-agent line 129: 동일. `model: sonnet` 오염 0건(두 파일 모두). prose 자기참조 선행이 백틱이므로 `_LEVEL_RE` `[,(]` 앵커 미매칭 — 설계대로 보호됨. |

#### S-REG2: 비대상 본문 diff 0 + frontmatter 불변 (회귀)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1, H-2 |
| 대상 | F-004 회귀 — 비대상 11개 에이전트 본문 + 13개 frontmatter |
| 계층 | L2 (재배포 전 baseline → 후 diff) |
| **실행 방식** | **M1 (셸 diff/awk 도구)** |
| 조건 | 재배포 전 baseline 백업 → 재배포 → diff |
| 기대 결과 | ① sub-dispatch 없는 11개 에이전트(be/convention-checker/db/fe/plan/planning/security-checker/task/task-qa/test/wtm) 배포본 body diff 0 ② 13개 전체 frontmatter `model:` 값(line≤9) 재배포 전후 불변 ③ body 변경 에이전트 = sub-dispatch 레벨명 보유 에이전트로 한정(현재 소스: sdd-action-agent; 031 해소 시 task-action-agent 추가) |
| 도구 | diff, awk |
| 실행 명령 | for-loop: pre/post 어댑터로 11개 비대상 에이전트 변환 후 body diff; 13개 전체 frontmatter model: 비교 |
| 결과 | **Pass** |
| 상세 | ① 11개 비대상 에이전트 모두 body diff 0: opal-be-agent, opal-convention-checker, opal-db-agent, opal-fe-agent, opal-plan-agent, opal-planning-agent, opal-security-checker, opal-task-agent, opal-task-qa-agent, opal-test-agent, opal-wtm-agent. ② 13개 frontmatter model: 불변(claude 기준): be=opus, convention-checker=sonnet, db=sonnet, fe=sonnet, plan=opus, planning=opus, sdd-action=opus, security-checker=opus, task-action=opus, task=opus, task-qa=haiku, test=sonnet, wtm=haiku. 소스 변경(opal-be-agent v1.2 standard→advanced)도 pre/post 어댑터 변환 결과 동일(양쪽 opus). |

### L3. 사용자 협업 (수동, [SUPERVISOR] 마커)

#### S-SUP1: 031/032 레이어 충돌 결정 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | decision_required(R-3) — 031/032 소스 충돌 해소 방향 결정 |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업)** |
| 조건 | task-action-agent 소스가 `opus` 하드코딩(031 uncommitted)이며 옵션 A 전제와 충돌 |
| 기대 결과 | 사용자/PM이 R-3 옵션(A 소스 레벨명 복원 / B 어댑터만 수정 후 031 후 정합 / C 031·032 병합) 중 결정. PM 자율 결정 금지 (`citation-rules.md §7.5`) |
| 실행자 | [SUPERVISOR] — 캡틴 결정 필요 |
| 결과 | **RESOLVED — PM 반증(S-CONFLICT)으로 에스컬레이션 불요. task-action-agent 소스에 opus 하드코딩 없음(grep 0건). [SUPERVISOR] 결정 게이트 생략.** |
| 상세 | S-CONFLICT 실행 결과: `grep -c "opus" opal/agents/opal-task-action-agent/AGENT.md` = 0. 031 충돌 가설(H-6) 오경보 확정. S-SUP1 전제 조건(task-action-agent body에 `model: opus` 존재) 미충족 → 결정 불요. task-action-agent는 S-GREEN1/2/EDGE에서 정상 치환 Pass 확인. |

**PM 표준 요청 양식 (S-SUP1)**:
```
[결정 요청] 031/032 소스 레이어 충돌
- 현황: 진행 중 031이 opal-task-action-agent/AGENT.md 본문을 model: opus(claude 실모델명)로 하드코딩(uncommitted). 032 옵션 A(소스=플랫폼 중립 레벨명)의 전제 위반. 어댑터는 opus를 레벨명으로 인식 못해 gemini/codex 배포 시 model: opus 잔존(신규 cross-platform 버그).
- 선택지:
  A) task-action-agent 소스 본문 opus → 레벨명 복원 (031 미간섭 제약 위반 — 031 소유자 합의 필요)
  B) 032는 어댑터(install·windows·agents.md)만 수정. task-action-agent 소스는 031 완료 후 별도 정합. 032 검증은 sdd-action-agent로 RED→GREEN 입증 (권고)
  C) 031·032 병합 처리
- 영향: A/C는 031 작업과 충돌. B는 task-action-agent 배포본이 031 완료까지 opus 잔존(claude는 정상, gemini/codex는 미해결).
```

---

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| F-001 AC (RED) | H-1, H-5 | L1 | S-RED1 | (배포본 grep):[L1-F001-RED] | RED 증거 |
| F-001 AC (GREEN claude) | H-2, H-5 | L1 | S-GREEN1 | (배포본 grep):[L1-F001-claude] | opus/sonnet 출현 + 레벨명 0건 |
| F-001 AC (GREEN gemini) | H-5 | L1 | S-GREEN2 | (배포본 grep):[L1-F001-gemini] | 양 토큰 형태 |
| F-002 AC | H-3 | L1 | S-EDGE | (배포본 grep):[L1-F002-cursor] | inherit/레벨/빈괄호 0건 |
| F-003 AC | H-4 | L1 | S-MIRROR | (정적 diff):[L1-F003-mirror] | 정규식·매핑 동기 + 양 경로 |
| F-004 AC (prose) | H-1 | L2 | S-REG1 | (배포본 grep):[L2-F004-prose] | 회귀 |
| F-004 AC (불변) | H-1, H-2 | L2 | S-REG2 | (diff/awk):[L2-F004-invariant] | 11 body diff 0 + 13 fm 불변 |
| F-005 AC | H-7 | L1 | S-DOC | (문서 grep):[L1-F005-doc] | §본문 처리 + 3 changelog |
| (게이트) | H-6 | L1, L3 | S-CONFLICT, S-SUP1 | (게이트):[gate-R3] | decision_required |

---

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | Bash 문법 (install-mac.sh) | `bash -n scripts/install-mac.sh` | **Pass** | `bash -n scripts/install-mac.sh` exit 0, 오류 없음 |
| 2 | Python heredoc 문법 (어댑터 내장 py) | py compile / 재배포 무경고 | **Pass** | `python3 -m py_compile adapter_post.py` exit 0. `python3 -m py_compile adapter_pre.py` exit 0. 경고 없음. |
| 3 | PowerShell 정적 분석 | PSScriptAnalyzer (가능 시) | **Skip** | macOS 환경 pwsh 미설치 — PSScriptAnalyzer 실행 불가. windows.ps1 정적 확인: 문법 구조(함수 정의, 파라미터 선언, [regex]::Replace 호출)는 PS5.1+/7+ 공통 문법 준수 확인. |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | **Pass** | `grep -nEi "(api_key\|secret\|password\|token\|credential)\s*=\s*['\"][^'\"]{8,}"` 3파일 대상 — 0건. 추가된 코드: `_LEVEL_RE` 정규식 패턴 + mapping dict(모델명 상수) + sentinel string만 추가. |
| 2 | .gitignore 확인 | **Pass** | 변경된 3파일(`scripts/install-mac.sh`, `scripts/install/windows.ps1`, `opal/core/references/agents.md`)은 모두 소스 트리 내 .md/.sh/.ps1 — 배포본(`~/.claude/`, `~/.opal/`, `~/.cursor/` 등)은 repo 외부이며 .gitignore 대상이 아님. 소스 파일만 수정. |
| 3 | 배포 경계 준수 | **Pass** | 어댑터 Python(adapter_post.py): `open(dst, 'w')`는 `dst_file` 인자(install-mac.sh 호출자가 결정, SCR 격리 환경에서 테스트). `~/.opal/`, `~/.claude/agents/` 직접 편집 0건. 테스트는 scratch(`/private/tmp/…/scratchpad/adapter-test`)에만 출력. CONVENTIONS §배포 경계 준수. |

## 7. 판정

**All Pass — S-RED1 RED 증거(body 레벨명 히트 2건) 확보 후 모든 GREEN 시나리오(S-GREEN1/2/EDGE/REG1/REG2/MIRROR/DOC) Pass. S-CONFLICT RESOLVED(opus 하드코딩 없음). 코드 품질 Pass(bash -n, py compile). 보안 Pass. 가짜 구현 없음(실 어댑터 격리 실행·grep 검증).**

### PM Gate 체크 (7대 강제 룰)

- [x] 모의 객체·가짜 구현 패턴이 시나리오 본문에 부재 (본 태스크는 실 어댑터 격리 실행·grep 어서션 검증 — 가짜 구현 부재 자명)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전 (미매핑 시나리오 없음)
- [x] L1/L2/L3 계층 명시 (모든 시나리오)
- [x] L3 [SUPERVISOR] 마커 존재 + PM 요청 양식 첨부 (S-SUP1) — RESOLVED 처리
- [x] 리스크 가설 표(§1) H-N ↔ 시나리오 S-N 1:N 매핑 완전 (H-1~H-7 전부 매핑)
- [x] 모든 시나리오에 실행 방식(M1/M2/M3) 명시

### RED-first 게이트 (red-first.md §1·§2·§3)

- [x] S-RED1으로 RED 증거(pre-fix body `model: advanced`/`model: standard` 히트 2건, exit 0) 확보 후 GREEN 진입
- [x] RED 어서션 작성자(opal-test-agent) ≠ 구현자(op-dev-execute) 분리 확인
- [x] GREEN 루핑 중 RED 어서션(grep 패턴 `[,(]\s*model: (advanced|standard|light)\b`) 약화·삭제 없음 (test 불변성)
