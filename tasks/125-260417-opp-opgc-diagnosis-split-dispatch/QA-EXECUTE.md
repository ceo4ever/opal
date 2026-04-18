# QA: EXECUTE — opgc 진단 전담화 + 프로젝트 구성 표준 정립

> 검토일: 2026-04-17 | 판정: Pass

## 1. 요약

opgc(opal-pilot-gc)를 진단 전담 4단계 Pilot(SCAN → CHECK → REPORT → CLOSE)로 재정의하고, APPLY 단계를 완전 제거하여 수정은 opds 수동 체인으로 이관했다. PROJECT.md에 `## 프로젝트 구성` 표준 섹션(4컬럼: 요소/경로/기술 스택/전문 에이전트)을 신설하고 "프로젝트 문서" 테이블에 `적용 범위` 컬럼을 추가(지시 B 오버라이드에 따라 기존 `용도` 유지 + `적용 범위` 신규 = 총 5컬럼)했다. 체커 AGENT 2종에서 APPLY·Edit/Write·apply_mode를 제거하고 허브+링크 체이닝용 `scope` 입력을 추가했으며, 신규 참조 문서 `conventions-hub-model.md`를 신설했다. opi/opal-pm/context-injection/agents 주변 문서 정합화도 모두 반영되었다.

changed_files 11개 전수 검증 결과 F-1~F-11 AC 전부 충족, CR-EX-1~8 정합성 추가 검증 전부 Pass, PLAN §3 11개 Step + §4 QA 체크리스트 전 항목 `[x]` 상태.

## 2. 검증 결과

### 2.1 기본 검증 ID (SKILL.md §범용 단계별 검증 ID)

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| GE-1 | 체크리스트 완료 — PLAN §3 Step 1~11 모두 `[x]` | Pass | `PLAN.md:601/619/634/657/673/707/728/743/752/768/777` 모두 `- [x] 완료`. unchecked 0개(grep 결과). |
| GE-2 | 산출물 존재 — changed_files 11개 실제 존재 및 의도 변경 | Pass | 11개 파일 모두 존재. PROJECT.md(L74-80 프로젝트 구성, L84 적용 범위 컬럼), conventions-hub-model.md 신규(L1-102), 두 AGENT.md(tools 축소, APPLY 제거), opgc SKILL.md(4단계), opi SKILL.md(L285-316 인터뷰, L641-642 최신화 분기), context-injection.md(L60 라우팅 섹션), opal-pm.md(L148 한 줄 추가), agents.md(L56/68 scope 추가), PLAN.md(§3/§4 체크박스 `[x]`) 모두 확인. |
| GE-3 | TASK 충족 — F-1~F-11 AC 전부 파일에 반영 | Pass | 아래 §2.2 AC 상세 검증 전 항목 Pass. |

### 2.2 AC 상세 검증 (F-1 ~ F-11)

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| F-1 | opgc CLI 축약·조합 전환 | Pass | `opal/skills/opal-pilot-gc/SKILL.md:28-35` Arguments 파싱 블록에 `--apply` 없음(파싱 블록 기준). Arguments 테이블(L38-44)에 `--security`/`--convention` 2행 존재, `--only` 시작 행 0개. 조합 예시 8종 수록 — 요구 3종(`--scope all --convention` L33, `--agentic --convention` L34, `--scope all --convention --agentic` L35) 포함. |
| F-2 | APPLY 단계 제거 | Pass | `--apply` 등장은 ① L21 Guards 맥락("APPLY 단계 제거됨"), ② L53-56 마이그레이션 안내(허용 문맥), ③ L478 변경이력뿐. STEP 4 = CLOSE(L318). 파이프라인 현황판(L396-405) 헤더+구분+8행 = SCAN/CHECK/REPORT/CLOSE만 포함(8행 이하). |
| F-3 | opgc → opds 수동 체인 가이드 | Pass | CLOSE 섹션 L336-368에 `//opds` 호출 예시(L341), opds TASK.md 골격 블록 — `## 요구사항`(L359-361, auto_fixable), `## 참조 문서`(L354-357, GC-*.md), `## 제약`(L363-367, `[?] review 제외`·회귀 금지) 모두 포함. |
| F-4 | PROJECT.md 기반 SCAN 동적 분할 병렬 | Pass | STEP 1.5(L113-150)에 파싱 의사코드(L117-138), 요소별 target_files 분할 표(L142-146), fallback 분기(L134-138). STEP 2.2(L179-201)에 요소×체커 매트릭스 4케이스(Case A/B/C/D) — 요구 3케이스 이상 충족. 섹션 부재 시 fallback 명시(L148, L198). |
| F-5 | 체커 두 AGENT.md APPLY 제거 | Pass | 두 AGENT.md 모두: ①Phase 6/7 APPLY 소제목 부재(변경이력 맥락만 잔존), ②`tools: [Read, Grep, Glob, Bash]` 정확 일치(convention L9, security L9), ③입력 명세 `apply_mode` 행 없음, ④반환 `changed_files`에 `GC-CONVENTION-{ts}.md`/`GC-SECURITY-{ts}.md` 보고서만 포함(convention L166, security L167). |
| F-6 | 체커 허브+링크 참조 체이닝 | Pass | 두 AGENT.md 모두: ①입력 명세에 `scope` 행 존재(convention L31, security L28), ②Phase 1(컨벤션)/Phase 2(보안)에 "허브 Read → 링크 파싱 → scope 매칭 상세 Read" 흐름(convention L37-66, security L39-69) 명시, ③`check_enabled` 판정과 공존(convention L61/63, security L64/68). |
| F-7 | PROJECT.md 프로젝트 구성 + 적용 범위 컬럼 | Pass | `docs/PROJECT.md:74` `## 프로젝트 구성` H2 존재, L78-80 스키마 4컬럼(`요소/경로/기술 스택/전문 에이전트`) 모두 채워짐(Framework 행). "프로젝트 문서" 테이블(L84) 컬럼 `문서/설명/용도/적용 범위/참조 시점` **5컬럼**(지시 B 옵션2 오버라이드) — 모든 행의 `적용 범위` 셀 "Framework" 기재, 빈 셀 0개. QA 관점에서 지시 B 오버라이드(TASK.md AC "4컬럼"을 "5컬럼"으로 재정의) 인지 후 Pass 처리. |
| F-8 | opi 반영 | Pass | `opal/skills/opal-project-init/SKILL.md:285` "프로젝트 구성 인터뷰" 블록, L287-316 Q8~Q10 인터뷰, L350-353 Phase 2 작성 프로세스 "표준 섹션" 명시, L641-642 최신화 Step E "섹션/컬럼 부재 시 추가 제안" 분기 2행 신설. 변경이력 v3.4(L869, 2026-04-17, 125). |
| F-9 | opal-pm.md / context-injection.md 라우팅 | Pass | `context-injection.md:60` `## PROJECT.md 프로젝트 구성 기반 라우팅` 절 존재. 파싱 의사코드(L66-86), 예시(L90-109) 3건 이상. opal-pm.md §6(L148)에도 요약 한 줄 + context-injection.md 참조(L150). |
| F-10 | 주변 문서 정합화 | Pass | `agents.md`에 `--apply`/`--only` 문자열 0건(grep 결과 매치 없음). opgc SKILL.md 변경이력 v1.1(L478, 2026-04-17, 125). README.md에 opgc/opal-pilot-gc 문자열 없음(grep 결과) → "해당 없음" 기록 유지. |
| F-11 | 허브+링크 가이드 문서 | Pass | `opal/core/references/conventions-hub-model.md` 신설 확인(L1-102). ①허브 역할 §2(L14-21), ②링크 규약 §3(L23-37) — `[FE-CONVENTIONS.md](./FE-CONVENTIONS.md) — Frontend` 예시 포함, ③체커 체이닝 흐름 §4(L39-48) 4단계, ④예시 블록 §5(L50-94) 2종(풀스택/단일 문서) — 요구 1개 이상 충족. |

### 2.3 정합성 추가 검증 (CR 계열)

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| CR-EX-1 | 지시 A — PROJECT.md opgc 설명 4단계로 교체 | Pass | `docs/PROJECT.md:70` "GC 4단계 Pilot: SCAN → CHECK → REPORT → CLOSE"로 정확히 반영. |
| CR-EX-2 | 지시 B — 프로젝트 문서 테이블 `용도` 유지 + `적용 범위` 추가 = 5컬럼 | Pass | L84 `\| 문서 \| 설명 \| 용도 \| 적용 범위 \| 참조 시점 \|` — 정확히 5컬럼. 모든 행에 `적용 범위=Framework` 기재. |
| CR-EX-3 | 지시 C — opi 변경이력 v3.3 이후 합리적 번호 | Pass | `opal-project-init/SKILL.md:869` v3.4 — v3.3의 다음 마이너 버전으로 합리적. |
| CR-EX-4 | 지시 D — DONE.md 미생성, EFFECT-ANALYSIS.md 미변경 | Pass | `tasks/125-.../` 폴더 내용: EFFECT-ANALYSIS.md(수정 없음, ls 기준 4/18 13:34 기존 타임스탬프), PLAN.md, QA-PLAN.md, STATE.md, TASK.md — DONE.md 부재. git status에서 EFFECT-ANALYSIS.md의 M 플래그 없음 확인. |
| CR-EX-5 | 하위호환 — 프로젝트 구성 섹션 부재 시 fallback 명시 | Pass | opgc SKILL.md STEP 1.5(L135-138, L148) + STEP 2.2 Case D(L198-200)에서 "섹션 부재 시 1+1 단일 디스패치 유지" 명시. |
| CR-EX-6 | `~/.opal/` 수정 0건, 커뮤니티 스킬 원본 수정 0건, git commit 0건 | Pass | git log 최신 커밋 `8f0ed8a feat(124)` — 125번 커밋 없음. git status에 `~/.opal/` 하위 수정 없음(모두 `opal/`, `docs/`, `tasks/`, `.opal/MEMORY.md`). community-skills 변경 없음. |
| CR-EX-7 | PLAN §3/§4 체크박스 전체 `[x]` | Pass | grep `^- \[ \]` 결과 0건. 35개 체크박스 전체 `[x]` 상태. |
| CR-EX-8 | 변경이력 버전 표기 — 두 체커 + opgc v1.1 (날짜/125 포함) | Pass | opal-convention-checker/AGENT.md:232, opal-security-checker/AGENT.md:216, opal-pilot-gc/SKILL.md:478 — 각각 `v1.1 \| 2026-04-17 \| ... (125)` 포맷 확인. conventions-hub-model.md v1.0(L102), opi SKILL.md v3.4(L869)도 동반 확인. |

## 3. 지적 사항

지적 사항 없음.

### 심각도 분류

- Critical: 없음
- Warning: 없음
- Info: 없음

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md ↔ EXECUTE 산출물 | TASK.md F-1~F-11 AC 전부 실제 파일에 반영되었는가 | Pass — §2.2 AC 상세 검증 전 항목 충족 |
| TASK.md §제약 조건 ↔ EXECUTE 산출물 | `~/.opal/` 수정 금지, 커뮤니티 스킬 원본 수정 금지, 단일 태스크 완료, 커밋 금지, 하위호환 | Pass — git status/log·fallback 명시·폴더 미분할 확인 |
| PLAN.md §2 구현 계획 ↔ EXECUTE 산출물 | 신규 1개(N-1) + 수정 9개(M-1~M-9) 전부 수행됐는가 | Pass — N-1 conventions-hub-model.md 신설, M-1~M-9 전부 의도대로 변경됨. (단, M-5 CONVENTIONS.md는 허브+링크 참고 문단 추가로 수행됨.) |
| PLAN.md §3 Step 1~11 ↔ EXECUTE 산출물 | 각 Step의 완료 기준이 실제로 충족되었는가 | Pass — 각 Step 완료 기준을 §2.2 AC 근거로 교차 확인 |
| PLAN.md §4 QA 체크리스트 ↔ EXECUTE 산출물 | 기능/일관성/문서 품질 체크리스트가 실제 상태와 일치하는가 | Pass — 21개 항목 모두 `[x]`, 각 항목 근거 §2.2에서 확인 |
| opgc SKILL ↔ 체커 AGENT | 디스패치 템플릿의 `scope` 파라미터 ↔ AGENT 입력 명세 `scope` | Pass — opgc SKILL.md L227 `scope: {element.요소명 또는 "all"}` ↔ convention AGENT L31, security AGENT L28 정합 |
| opgc SKILL ↔ STATE.md 도메인 치환값 | 단계 목록 정합 | Pass — L391 `SCAN / CHECK / REPORT / CLOSE` 정확 일치 |
| agents.md 매핑 테이블 ↔ AGENT Phase 흐름 | 허브+링크 체이닝 표기 정합 | Pass — agents.md L149-150 "(허브+링크 체이닝 — conventions-hub-model.md 참조)" ↔ AGENT Phase 1/2 흐름 일치 |
| context-injection.md 라우팅 ↔ PROJECT.md 프로젝트 구성 스키마 | 요소/경로/기술 스택/전문 에이전트 4필드 정합 | Pass — context-injection.md L66 파싱 스키마 ↔ PROJECT.md L78 테이블 헤더 일치 |
| 변경이력 날짜/태스크 번호 일치 | 2026-04-17 / 125 표기 | Pass — 5개 문서(opgc SKILL v1.1, convention AGENT v1.1, security AGENT v1.1, opi v3.4, conventions-hub-model v1.0) 전부 일치 |

## 5. 판정

**Pass**

TASK.md F-1~F-11 AC, 지시 A~D 오버라이드 반영, PLAN §3/§4 체크리스트 완료, CR 정합성 검증(CR-EX-1~8) 전원 충족. `~/.opal/` 미수정·커뮤니티 스킬 미수정·git commit 0건 등 하네스 Guards 제약도 준수됐다. 다음 단계(CLOSE — DONE.md 생성)로 진행 가능.
