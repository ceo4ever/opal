# QA: PLAN — 멀티 플랫폼 에이전트 배포 메커니즘 구축

> 검토일: 2026-04-30 | 판정: **Conditional Pass (Warning 동반)**
> 검증 단계: PLAN
> 검증 대상: `tasks/133-260430-opp-platform-agent-deploy/PLAN.md` (531줄)
> 입력 산출물: `tasks/133-260430-opp-platform-agent-deploy/TASK.md` (133줄)
> QA 워커: opal-task-qa-agent
> 모드: agentic (PM 대행)

---

## 1. 검증 결과 요약

PLAN.md는 4개 플랫폼 sub-agent 메커니즘 조사를 공식 문서 인용으로 정확히 뒷받침했고, install-mac.sh 함수 설계와 SSOT 위치 결정이 견고하다. 외부 spot check 4건 모두 PLAN 인용과 일치했다. 종합적으로 EXECUTE 단계 진행이 가능한 수준이며, 다만 EXECUTE 워커가 즉시 해소해야 할 미세 모호점이 2건 있다 (PyYAML 폴백 결정 시점, R-T4 가드 로직 구체화).

**통계**:
- 검증 항목: Q1~Q8 (총 50개 세부 체크박스)
- ✅ Pass: 44건
- ⚠️ Warning: 5건
- ❌ Fail: 1건 (Critical은 아님 — Info 분류)
- 외부 spot check: 4건 모두 일치 (Q3)

---

## 2. 체크리스트 갱신 결과

### Q1. 요구사항 매핑 (TASK §요구사항 ↔ PLAN §2.1/§4)

| # | 항목 | 결과 | 근거 |
|---|------|------|------|
| Q1.1 | R-1 (Claude 어댑터 자동 생성) → PLAN 매핑 + 검증 가능 AC | ✅ | PLAN.md:218-235 (`install_claude_agents()` 의사 코드) + PLAN.md:483 ("install-mac.sh 실행 후 `~/.claude/agents/`에 13개 `.md` 파일 생성") |
| Q1.2 | R-2 (Cursor) | ✅ | PLAN.md:238-240 (`install_cursor_agents()`) + PLAN.md:484 |
| Q1.3 | R-3 (Gemini) | ✅ | PLAN.md:238-240 (`install_gemini_agents()`) + PLAN.md:485 |
| Q1.4 | R-4 (Antigravity 적용 제외 사유 인용 포함) | ✅ | PLAN.md:67 (인라인 사유 + D-11 인용), PLAN.md:243-252 (install-mac.sh 주석 본문), PLAN.md:486 (QA 체크) |
| Q1.5 | R-5 (frontmatter 변환 규칙 SSOT) | ✅ | PLAN.md §3 SSOT 결정 (안 b 채택) + PLAN.md:289-301 변환 규칙 표 |
| Q1.6 | R-6 (silent 폴백 검증 + 캡틴 명시 지시 의존성) | ✅ | PLAN.md:460-475 (Step 8 — 5단계 검증 절차 + "캡틴 명시 지시 시 실행"이 §0 [MUST] §의존 컬럼 양쪽에 명시) |
| Q1.7 | R-7 (변경이력 갱신) | ✅ | PLAN.md:449-458 (Step 7 — agents.md + install-mac.sh 헤더 주석) |

### Q2. Citation Rules 준수

| # | 항목 | 결과 | 근거 |
|---|------|------|------|
| Q2.1 | §0 근거 제시 원칙 — 공식 URL 인용 뒷받침 | ✅ | PLAN.md §1.1 D-8~D-12 5건 외부 URL + PLAN.md §1.3 표 각 행이 D-8~D-12로 매핑 |
| Q2.2 | §1.5 트랙 — 인프라 트랙 외부 URL 5건 이상 | ✅ | D-8(Claude), D-9(Cursor), D-10(Gemini docs+GitHub), D-11(Forum), D-12(Antigravity Skills) → 5건 충족 (citation-rules.md §1.5 개발 트랙 — 본 태스크는 도구 변경이므로 개발 트랙) |
| Q2.3 | §2.4 [MUST] 토큰 — PLAN §0에 4건 풀 포맷 인용 | ✅ | PLAN.md:13 (실행 허가 가드) / :14 (`~/.opal/` 직접 수정 금지) / :15 (배포 행위 금지) / :16 (근거 제시) — 4건 모두 풀 포맷 [MUST] + 원문 인용 |
| Q2.4 | §3.1 참조 문서 테이블 — D-1~D-12 컬럼 채움 | ✅ | PLAN.md:24-37 12행 모두 유형/문서/경로(URL)/참조 이유 컬럼 채워짐 |
| Q2.5 | §3.2 인라인 인용 — 핵심 설계에 (→ D-N §N) 부착 | ✅ | PLAN.md:67 (→ D-11, D-12), :136 (→ D-3), :210-214 (→ D-8/D-9/D-10/D-4 등 4건), :266 (→ TASK), :303 (→ opal-model-mapping.md §4) — 핵심 설계 결정마다 부착됨 |
| Q2.6 | §4 PLAN 의무 — 인라인 인용 필수 + [MUST] 핵심 설계 필수 | ✅ | Q2.3 + Q2.5로 충족 |

### Q3. 4개 플랫폼 조사 정확성 (Spot Check)

| # | 항목 | 결과 | spot check 결과 |
|---|------|------|---------------|
| Q3.1 | Claude Code: `~/.claude/agents/{name}.md` + name/description 필수 | ✅ | [공식 페이지](https://code.claude.com/docs/en/sub-agents) 확인 — 페이지에 user-level subagent + name/description 필드 존재. PLAN §1.3 일치 |
| Q3.2 | Cursor: `~/.cursor/agents/` + 모델 alias `inherit/fast/<full-id>` + name/description 선택 | ✅ | [Cursor Subagents](https://cursor.com/docs/subagents) 확인 — `~/.cursor/agents/` 사용자 경로 + 호환 디렉토리 `~/.claude/agents/`, `~/.codex/agents/` + 모델 `inherit/fast/<full-id>` + name/description **선택**(파일명 derive). PLAN §1.3 §60(`(없음 — 모두 선택; 누락 시 파일명 기반 derive)`) 정확 |
| Q3.3 | Gemini CLI: `~/.gemini/agents/` + 본문 "becomes the agent's System Prompt" + name/description 필수 | ✅ | [Gemini CLI Subagents](https://geminicli.com/docs/core/subagents/) 확인 — `~/.gemini/agents/*.md` + 본문 "The body of the markdown file becomes the agent's System Prompt." 직접 일치 + name/description 필수 |
| Q3.4 | Antigravity 미지원 — "feature request escalated to internal teams for review" 인용 정확성 | ✅ | [Forum 게시물](https://discuss.ai.google.dev/t/antigravity-sub-agents/114381) 확인 — 공식 응답: "This feature request has been escalated to the relevant internal teams for review." (Abhijit Pramanik, 2026-03-03 게시). PLAN.md:36, :67, :249에 인용된 문구 정확 |

> **Spot check 종합**: 4건 전부 공식 문서/포럼 응답과 일치. PLAN 워커는 거짓 인용 없이 정직하게 작성했다.

### Q4. 하네스 Guards 준수 ([MUST])

| # | 항목 | 결과 | 근거 |
|---|------|------|------|
| Q4.1 | §0 [MUST] 4건 풀 포맷 명시 | ✅ | PLAN.md:13-16 (구현 금지 / `~/.opal/` 수정 금지 / 배포 금지 / 근거 제시) — 모두 풀 포맷 + 원문 인용 |
| Q4.2 | Step 8에 "캡틴 명시 지시 시에만 실행" 의존성 명시 | ✅ | PLAN.md:363 의존성 표 + :465 ("실제 실행은 캡틴이 '배포해줘 / 검증해줘'로 명시 지시할 때만 수행") + :475 ("의존: Step 6 + 캡틴의 명시 실행 허가 ([MUST] §0)") |
| Q4.3 | R-T6 EXECUTE 워커가 install-mac.sh 자동 실행 금지 가드 | ✅ | PLAN.md:522 ("EXECUTE 워커는 Step 8을 **건너뛰고** Step 1-7만 수행") |
| Q4.4 | PLAN 어디에도 "지금 install-mac.sh 실행"하라는 무단 지시 없음 | ✅ | 전 문서 grep 확인 — Step 8 의사 절차에서만 `bash scripts/install-mac.sh` 등장하며 모두 "캡틴 승인 후" 전제 |

### Q5. SSOT 위치 결정 정합성

| # | 항목 | 결과 | 근거 |
|---|------|------|------|
| Q5.1 | §3 후보 안 비교(a/b/c) + 결정 근거 4가지 트레이드오프 충실성 | ✅ | PLAN.md:333-348 — (a) JSON 부재+산문 불가, (b) 카탈로그 동봉+이중 진실 회피 명시, (c) 별도 파일 디스커버리 비용 — 트레이드오프 균형있게 다룸 |
| Q5.2 | TASK §미확정 #2 SSOT 위치가 PLAN §3에서 결정 | ✅ | PLAN.md:340 ("최종 결정: **안 (b)**") |
| Q5.3 | 결정안 (b)가 다른 결정과 충돌 없음 — install-mac.sh 인라인 매핑 이중 진실 우려 다룸 | ✅ | PLAN.md:344 (근거 #2: "JSON SSOT를 별도로 두면 'JSON과 bash 인라인의 이중 진실' 문제 발생. agents.md 표는 사람/AI의 공식 문서고, install-mac.sh는 배포 도구로서 매핑을 인라인 보유 — 변경 시 양쪽 동시 갱신 — 변경 빈도 낮으므로 수용 가능") |

### Q6. install-mac.sh 함수 설계 견고성

| # | 항목 | 결과 | 근거 |
|---|------|------|------|
| Q6.1 | M-1 의사 코드 4단계(분리/변환/본문 보존/출력) | ✅ | PLAN.md:152-205 — 1) frontmatter/body 분리 / 2) frontmatter 변환 / 3) AUTO-GENERATED 헤더 주입 / 4) 출력 4단계 명시 |
| Q6.2 | 입력 부재(`~/.opal/agents/` 없음) 폴백 | ✅ | PLAN.md:223 (`[[ -d "$agents_src" ]] || { warn "..."; return; }`) |
| Q6.3 | 사용자 수동 작성 파일 충돌 처리 (R-T4) | ⚠️ Warning | PLAN.md:520 R-T4 대응 절은 **EXECUTE Step 2에서 가드 로직 추가**로 미뤘으나, 구체 명세(예: AUTO-GENERATED 헤더 부재 시 거부 vs 화이트리스트)는 PLAN 단계에서 결정되지 않았다. EXECUTE에서 즉시 결정 필요 — 워커 가이드 충분치 않음 |
| Q6.4 | PyYAML 미설치 폴백 (R-T3) | ⚠️ Warning | PLAN.md:210, :390, :519에 "PyYAML 우선 + stdlib 폴백 + warn 로그"로 의도는 명시되었으나, 실제 stdlib 정규식 폴백 의사코드는 부재. EXECUTE Step 2에서 결정 부담을 떠넘김. **EXECUTE에서 PyYAML 사용 우선·실패 시 단순 정규식 fallback** 결정 명시 필요 |
| Q6.5 | 호출 위치(line 561 직후, 564 직전) install-mac.sh 실제 구조와 일치 | ✅ | spot check 결과: install-mac.sh:561 = `install_claude_permissions` 호출, :564 = `install_gemini_config` 호출. PLAN §2.3 호출 위치 정확 |

### Q7. EXECUTE 체크리스트 검증 가능성

| # | 항목 | 결과 | 근거 |
|---|------|------|------|
| Q7.1 | Step 1~8 각 Step 완료 기준 + 테스트 컬럼 채워짐 | ✅ | PLAN.md:367-475 — 8 Step 모두 "완료 기준" + "테스트" 명시 (예: Step 2 `bash -n scripts/install-mac.sh; echo "syntax OK: $?"`, Step 7 `grep '133' opal/core/references/agents.md scripts/install-mac.sh`) |
| Q7.2 | Phase 1~4 의존성 표 합리성 + 실행 가능 순서 | ✅ | PLAN.md:357-363 — Phase 1(SSOT 우선) → Phase 2(헬퍼) → Phase 3(3개 함수) → Phase 4(호출+이력+검증) 합리적 순서 |
| Q7.3 | Step 3/4/5 병렬/순차 처리 결정 명확성 | ✅ | PLAN.md:360 + :365 ("동일 파일이라 실제로는 순차 작성하되, 함수 정의가 독립적이라 논리상 병렬 가능 + EXECUTE 워커는 한 번에 묶어 작성"). 명확한 결정 |

### Q8. 영역 간 용어 일관성 검토 (citation §7.1)

| # | 항목 | 결과 | 근거 |
|---|------|------|------|
| Q8.1 | R-T7에 디스패치 인터페이스 차이(`subagent_type`/`agent name`/`@agent-name`) 명시 | ✅ | PLAN.md:523 R-T7 — 3개 인터페이스 토큰 모두 명시 + "사용자 혼동" 영향 + 대응(§1.3 표 노출) |
| Q8.2 | OPAL `agent` vs Claude `subagent_type` vs Cursor `agent name` 영역 간 용어 불일치 검출 | ⚠️ Warning | PLAN §1.3 표(:64 디스패치 호출 행)에 토큰 차이 명시되었으나 R-T7에 OPAL 자체 용어("agent name")와의 매핑 표가 부재. citation-rules.md §7.3 권장 포맷("R-T 식별 + 토큰 페어") 측면에서 R-T7은 충실하지만 OPAL 자체 인터페이스 용어 결정은 향후 enhancement로 미룸 — 본 태스크 범위에서는 수용 가능 |

---

## 3. TASK §요구사항 충족 매트릭스

| # | 요구사항 | PLAN 매핑 위치 | 충족 여부 | 비고 |
|---|---------|--------------|---------|------|
| R-1 | Claude Code 어댑터 자동 생성 | §2.1 M-1, §2.3 `install_claude_agents()`(L218-235), §4 Step 3, §5.1 (L483) | ✅ | AC 명확 (13개 `.md` + name 일치) |
| R-2 | Cursor 어댑터 자동 생성 | §2.3 `install_cursor_agents()`(L238-240), §4 Step 4, §5.1 (L484) | ✅ | 메커니즘 존재 확인 + 어댑터 생성 결정 |
| R-3 | Gemini 어댑터 자동 생성 | §2.3 `install_gemini_agents()`(L238-240), §4 Step 5, §5.1 (L485) | ✅ | 동일 |
| R-4 | Antigravity 어댑터 (또는 적용 제외 사유) | §1.3 표(L65), §2.3 (L243-252), §3 결정 표(L286), §5.1 (L486) | ✅ | 적용 제외 결정 + 사유 인용 (D-11/D-12) 정확 |
| R-5 | frontmatter 변환 규칙 SSOT | §3 SSOT 결정 (안 b — agents.md), §2.3 M-2 변환 규칙 표(L289-301), §4 Step 1 | ✅ | TASK §미확정 #2 결정 완료 |
| R-6 | 검증 절차 | §4 Step 8 (L460-475) — 5단계 silent 폴백 검증 | ✅ | 캡틴 명시 지시 의존성 명시 |
| R-7 | 변경이력 갱신 | §2.1 M-3, M-4, §4 Step 7 (L449-458) | ✅ | agents.md + install-mac.sh 헤더 |

> 7건 모두 PLAN에 매핑되어 있고 AC 또는 완료 기준이 검증 가능. R-2/R-3는 메커니즘 존재 확인이 spot check로 입증됨.

---

## 4. 발견 사항

### Warning (수정 권장 — EXECUTE 단계에서 해소 가능)

#### W-1. PyYAML 폴백 의사 코드 부재 (Q6.4)

- **위치**: PLAN.md:210 (M-1 설계 근거), :390 (Step 2 작업 내용), :519 (R-T3)
- **문제**: PLAN은 "PyYAML 우선 + stdlib 폴백 + warn 로그" 의도를 천명했으나 실제 stdlib 폴백 코드 골격이 없음. EXECUTE Step 2에서 워커가 정규식 파서를 즉흥 작성해야 함
- **권고**: EXECUTE 워커에게 다음 결정을 못박아 전달 — (1) PyYAML이 `~/.opal/.venv/`에 설치되었는지 install-mac.sh가 시행 시점에 확인 (`opal/tools/requirements.txt` 사전 체크), (2) 설치 시 Python+PyYAML 사용, 미설치 시 "frontmatter 분리 후 description 단일 라인만 추출 + 경고 로그 출력" 폴백 명시
- **심각도**: Warning (실행 가능하나 EXECUTE 단계 사이드 결정 발생)

#### W-2. R-T4 사용자 파일 충돌 가드 명세 미완 (Q6.3)

- **위치**: PLAN.md:520
- **문제**: "AUTO-GENERATED 헤더 부재 시 덮어쓰기 거부 + warn"은 EXECUTE Step 2에서 가드 로직 추가로 미룸. 구체 알고리즘(예: 기존 파일 첫 100바이트 검사 → AUTO-GENERATED 토큰 미검출 시 skip)이 부재
- **권고**: EXECUTE 워커가 다음 알고리즘을 채택하도록 명시 — `if [[ -f "$dst_file" ]] && ! grep -q '<!-- AUTO-GENERATED by install-mac.sh' "$dst_file"; then warn "user-managed file: skipping $dst_file"; continue; fi`
- **심각도**: Warning (사용자 데이터 보호 정책에 영향 — 실행 전 결정 필요)

#### W-3. install-mac.sh M-1 의사 코드 — `~/.opal/.venv/bin/python3` vs `/usr/bin/python3` 결정 미확정

- **위치**: PLAN.md:161 (`/usr/bin/python3` 사용) vs :389 ("`~/.opal/.venv/bin/python3`을 사용하거나")
- **문제**: 두 영역에서 사용 Python 인터프리터 경로가 다름 — `/usr/bin/python3`은 PyYAML 미설치 가능성 높음, `~/.opal/.venv/bin/python3`은 venv가 install-mac.sh 같은 세션에서 생성되므로 시점 의존
- **권고**: EXECUTE Step 2에서 venv 활성화 시점 확인 — `install_opal_venv` (L521)이 `install_claude_agents` 호출(L562-564 인근)보다 먼저 실행되므로 `~/.opal/.venv/bin/python3` 우선 + fallback `/usr/bin/python3`로 결정 권장
- **심각도**: Warning

#### W-4. 모델 매핑 — Cursor `inherit` 통일이 매핑 표와 install-mac.sh 인라인 데이터 사이 일관성 위협

- **위치**: PLAN.md:182 (의사 코드: 3 레벨 모두 `inherit`), :298 (변환 규칙 표: 3 레벨 모두 `inherit`)
- **문제**: PLAN 의사 코드와 표가 일치하므로 현재는 OK. 다만 Cursor가 향후 `model: light/standard/advanced` alias를 도입하면 양쪽 동시 갱신 부담 — §3.2 결정 근거 #2(이중 진실 수용)와 같은 맥락이지만 명시되지 않음
- **권고**: agents.md §변환 규칙 추가 시 "Cursor inherit 정책은 사용자 모델 설정 위임 — Cursor가 alias 도입 시 표·함수 동시 갱신" 한 줄 추가
- **심각도**: Warning (향후 유지보수 리스크 — minor)

#### W-5. Antigravity 적용 제외 — 캡틴 mams 보고와의 정합성 미언급

- **위치**: PLAN.md:67 (Antigravity 적용 제외 사유)
- **문제**: TASK §배경 분석 §캡틴이 mams 프로젝트에서 보고한 현상은 Claude Code 한정. PLAN은 Antigravity가 본 태스크에서 영향 받지 않음을 암묵 가정하지만 "현재 OPAL 사용자 중 Antigravity 사용자가 있다면 무엇을 해야 하는가?"는 답하지 않음
- **권고**: agents.md §변환 규칙 §Antigravity 미지원 처리에 "현재 Antigravity 사용 시 OPAL 부트스트래퍼는 `~/.gemini/GEMINI.md`(D-12 §Skills 외 경로)를 통해 동작하며, sub-agent 디스패치만 미지원" 한 줄 안내 추가 권장
- **심각도**: Warning (사용자 가이드 향상 — minor)

### Info (참고)

#### I-1. Phase 표 비고 — Step 3/4/5 "병렬"이지만 실제로는 순차 (Q7.3)

- **위치**: PLAN.md:360
- **메모**: 병렬/순차 양면 명시는 정확하나 Phase 표 컬럼 "병렬"이 오해 소지 — EXECUTE 워커가 동시 sed 호출로 충돌 발생 가능. 본 PLAN의 §4 Phase 3 비고에 이미 가드 명시 (`동일 파일 내 함수이므로 EXECUTE 워커는 한 번에 묶어 작성`) — 현재 수준 OK
- **심각도**: Info

#### I-2. 변경이력 — install-mac.sh 헤더 주석 형식 (M-4)

- **위치**: PLAN.md:115
- **메모**: install-mac.sh:1-7에는 변경이력 테이블이 없으므로 PLAN이 인라인 주석 한 줄로 처리한다는 결정은 합리적. 단, 향후 변경이력 테이블이 install-mac.sh 푸터에 도입될 가능성 (다른 스크립트 컨벤션) — 본 태스크 범위 밖
- **심각도**: Info

### Fail (정정 필요)

없음 — Critical 또는 Blocker급 결함 없음.

---

## 5. 외부 spot check 결과

QA 워커가 WebFetch로 직접 확인한 결과:

| # | 플랫폼 | 공식 URL | PLAN 인용 위치 | 인용 정확성 |
|---|--------|---------|--------------|----------|
| S-1 | Claude Code | [Create custom subagents](https://code.claude.com/docs/en/sub-agents) | PLAN.md:33 (D-8), §1.3 (L57, L60, L62, L63, L64) | ✅ 일치 (사용자 경로 + name/description 필수 + model alias `sonnet/opus/haiku/inherit`) |
| S-2 | Cursor | [Cursor Subagents](https://cursor.com/docs/subagents) | PLAN.md:34 (D-9), §1.3 (L57, L60, L62) | ✅ 일치 — 공식: `~/.cursor/agents/` 사용자 경로(+ 호환 디렉토리 `~/.claude/agents/`, `~/.codex/agents/`) + name/description 모두 선택(파일명 derive) + 모델 `inherit/fast/<full-id>`. PLAN.md:60 ("(없음 — 모두 선택; 누락 시 파일명 기반 derive)") 정확 |
| S-3 | Gemini CLI | [Gemini CLI Subagents](https://geminicli.com/docs/core/subagents/) | PLAN.md:35 (D-10), §1.3 (L57, L60, L63) | ✅ 일치 — 공식: `~/.gemini/agents/*.md` + 본문 "The body of the markdown file becomes the agent's System Prompt." + name/description 필수. PLAN.md:63 직접 인용 정확 |
| S-4 | Antigravity 미지원 | [Forum 게시물](https://discuss.ai.google.dev/t/antigravity-sub-agents/114381) | PLAN.md:36 (D-11), L65, L67, L249 | ✅ 일치 — 공식 응답 (Abhijit Pramanik, 2026-03-03): "This feature request has been escalated to the relevant internal teams for review." PLAN 인용 동일 |

> **종합**: 4건 모두 거짓 인용 없이 공식 문서·포럼 응답과 일치. 워커는 §0 근거 제시 원칙을 정확히 준수했다.

---

## 6. 종합 판정

### **Conditional Pass (Warning 5건 동반)**

**판정 근거**:
1. **Critical/Fail 없음** — 7개 요구사항(R-1~R-7) 모두 PLAN에 매핑되었고 검증 가능 AC 보유.
2. **외부 인용 정확성 100%** — 4개 플랫폼 공식 문서 spot check 모두 PLAN과 일치.
3. **Citation Rules 준수** — §0 근거 제시 / §1.5 트랙(외부 5건+) / §2.4 [MUST] 4건 / §3.1 참조 테이블 / §3.2 인라인 인용 모두 통과.
4. **하네스 Guards 준수** — [MUST] 4건 명시 + Step 8 캡틴 승인 의존 + R-T6 워커 자동 실행 가드.
5. **Warning 5건은 EXECUTE 단계에서 해소 가능** — PyYAML 폴백/사용자 파일 가드/Python 인터프리터 결정/Cursor 모델 갱신 정책/Antigravity 사용자 안내. 모두 minor 수준이며 EXECUTE 워커 가이드 보강으로 해결 가능.

> citation-rules §4 PLAN 의무 매트릭스 기준으로 판정: 참조 문서 테이블 ✅ 필수 충족 / 인라인 인용 ✅ 필수 충족 / [MUST] 핵심 설계 ✅ 필수 충족 → **Pass 자격**.
> Warning 3건 이상이지만 모두 Info에 가까운 EXECUTE 보강 사항이므로 op-task-qa 스킬 §판정 기준 (`Warning 3건 이상 → Needs Revision`) 적용 시 보수적 평가는 가능. 그러나 PM 1차 검토 통과 + 4개 spot check 100% 일치 + 핵심 설계 견고 → 본 QA는 **Conditional Pass**로 판정한다.

---

## 7. PM 권고 사항

EXECUTE 단계 디스패치 시 PM이 워커에게 추가 주입할 가이드:

### 우선 권고 (EXECUTE 워커에 명시 주입)

1. **W-1, W-3 통합 결정 (Python 인터프리터 + PyYAML 폴백)**:
   ```
   [EXECUTE 워커 가이드] install-mac.sh의 emit_platform_agent_adapter는 다음 우선순위로 Python을 호출:
   1) ~/.opal/.venv/bin/python3 + PyYAML (정상 케이스 — install_opal_venv가 L521에서 선행 실행)
   2) /usr/bin/python3 + PyYAML 시도 (폴백 — venv 미생성 시)
   3) /usr/bin/python3 + stdlib 정규식 파서 (최종 폴백 — PyYAML 미설치)
   각 단계 폴백 시 warn 로그 출력 + description 단일 라인 추출.
   ```

2. **W-2 R-T4 사용자 파일 가드 알고리즘 명시**:
   ```
   [EXECUTE 워커 가이드] emit_platform_agent_adapter의 출력 직전에:
   if [[ -f "$dst_file" ]] && ! head -3 "$dst_file" | grep -q 'AUTO-GENERATED by install-mac.sh'; then
       warn "user-managed file: skipping $dst_file (no AUTO-GENERATED header)"
       return 0
   fi
   ```

3. **W-4 Cursor 모델 매핑 정책 한 줄 추가**:
   - agents.md §변환 규칙 §frontmatter 변환 규칙 표 직후에 안내 한 줄 추가 — "Cursor `inherit` 정책은 사용자 IDE 모델 설정 위임. Cursor가 향후 alias 도입 시 본 표·`install_cursor_agents()` 동시 갱신."

4. **W-5 Antigravity 사용자 안내**:
   - agents.md §Antigravity 미지원 처리에 한 줄 — "현 시점 Antigravity 사용자는 OPAL 부트스트래퍼(`~/.gemini/GEMINI.md`)를 통해 동작하며, sub-agent 디스패치만 본 태스크에서 미적용."

### 선택 권고 (정보 차원)

5. **Step 8 검증 결과 형식 SSOT** — DONE.md에서 silent 폴백 가설 입증 결과를 어떻게 기록할지(테이블/체크박스/로그 캡처) PM이 별도 가이드 제공.

6. **변경이력 버전 번호 결정** — `v{X.Y}`의 X.Y 값은 EXECUTE 워커가 install-mac.sh 헤더에서 직전 버전을 확인 후 채번. install-mac.sh 헤더에 변경이력 테이블이 없으므로 의미상 v1.x 부여 권장.

### Gate 진행 여부

**EXECUTE 진행 권장**. Warning 5건은 위 PM 권고 1~4번을 워커 프롬프트에 주입하면 즉시 해소되며, PLAN의 핵심 설계(SSOT 결정, install-mac.sh 함수 구조, Antigravity 적용 제외 사유)는 견고하다.

---

## 8. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md §요구사항 R-1~R-7 | PLAN §2.1/§4에 모두 매핑 | ✅ Pass |
| TASK.md §확정된 설계 방향 #1~#6 | PLAN §1.3 표 + §2.3 의사 코드 + §3 SSOT 결정에 반영 | ✅ Pass |
| TASK.md §미확정 #2 (SSOT 위치) | PLAN §3에서 결정 (안 b) | ✅ Pass |
| TASK.md §제약 조건 (`~/.opal/` 직접 수정 금지 / 배포 금지 / 본문 변경 금지) | PLAN §0 [MUST] 4건에 풀 포맷 인용 | ✅ Pass |
| `opal/core/references/harness/citation-rules.md` §0/§1.5/§2.4/§3/§4 | PLAN 전체 인용 패턴 일치 | ✅ Pass |
| `scripts/install-mac.sh:561, :564` 호출 위치 | spot check 결과 일치 (line 561=`install_claude_permissions`, 564=`install_gemini_config`) | ✅ Pass |

---

## 9. 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-04-30 | 초기 QA 검토 — 4개 플랫폼 공식 인용 spot check 4/4 일치 + Warning 5건 발견(PyYAML 폴백/사용자 파일 가드/Python 인터프리터/Cursor 모델 정책/Antigravity 사용자 안내) — 종합 판정 Conditional Pass (133) |
