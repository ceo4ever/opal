# TEST-SCENARIO: AGENT.md 다이제스트 — 비서 tier 코어 경량화

> 태스크: 050-260630-opds-에이전트-다이제스트 | 작성일: 2026-06-30
> 입력: PLAN.md 리스크 가설 표(H-1~H-7) + §3.x.5 테스트 시나리오 + §5 QA 매트릭스 + §7 C-4
> 검증 계층: L1(산출물 grep/구조·`bash -n`) → L3(049 회귀 실세션 — 캡틴 직접)
> SSOT: `opal/core/references/harness/red-first.md`

---

## RED-first 판단

> red-first.md §1.5 하이브리드 자동분기 적용. 판단 주체 = PM(작성 시점). 모호하면 RED-first 기본(안전측).

| 변경 영역 | 트랙 | 근거 (red-first.md §1.5) |
|----------|------|------------------------|
| F-001 AGENT.md 이관 섹션 제거 (TS-001~003) | 구현-후-검증 | **"설정·문서" + "행위 불변 리팩터"** — 행동 규칙 의미 불변 이동. 정적 grep 단언 |
| F-002 opal-pm.md 수신·dedup (TS-004~006) | 구현-후-검증 | 문서 이동·dedup. 정적 grep |
| F-003 신규 reference 이관 (TS-007~009) | 구현-후-검증 | 문서 이동. install 불변은 `bash -n` 회귀 단언 |
| F-004 변경이력 trim (TS-010~011) | 구현-후-검증 | 문서 |
| F-005 교차참조 갱신 (TS-012~013) | 구현-후-검증 | 문서 (포인터 정합 — 정적 grep) |
| F-001 동작 불변 회귀 (TS-014) | 구현-후-검증 | 행위 불변 리팩터 — 정적 grep(049 재실행) + L3 실세션(캡틴) |

**트랙 결론**: 본 태스크는 **전 항목 구현-후-검증 트랙**이다. red-first.md §1.5 "RED-first 강제" 5종(비즈니스 로직/DB 스키마/API 계약/인증·인가/버그 수정)에 해당하는 변경이 **0건** — 순수 문서 이동·dedup·trim(행위 불변 리팩터 + 설정·문서). 따라서 RED 셸/node 테스트 선작성 적격 항목 없음. state-tool `--red-check` OFF.

**공통 불변(red-first.md §1.5)**: ① 테스트 산출물 = 정적 grep 단언 스크립트(또는 opal-test-agent 일괄 grep) ② 작성자≠구현자(opal-test-agent가 검증, 구현 워커와 분리) ③ TEST 단계 검증 유지.

**graceful skip(§5)**: 부트스트랩은 LLM 거동이라 049 회귀의 L3(실세션)는 결정론적 자동화 불가 → 캡틴 수동 확인(pending). 정적 단언(L1)이 결정론적 핵심 게이트.

---

## 1. 시나리오 목록

### L1 — 산출물 검사 (정적·결정론적)

| TS-ID | 항목 | 대상 파일 | 검증 방법 | PASS 조건 | 결과 |
|-------|------|---------|----------|----------|------|
| TS-001 | AGENT.md 이관 섹션 제거 (R-1, H-3) | `opal/core/AGENT.md` | grep 부재 단언: `#### 하네스 모드 체계`·`#### 자동 전환 트리거`·`#### 소유자 오버라이드`·`### code-scan 활용 규칙`·`### opal-brain 활용 규칙`·`## 프로젝트 메모리 브리핑`·`## 모델 매핑 자동 적용`·`## 프로젝트 부트스트래퍼 자동 관리`·`## 프로젝트 컨텍스트` 헤딩 0건 | 9개 이관 헤딩 grep 0건 | ✅PASS — grep 결과 0건 확인 |
| TS-002 | 부트스트랩 보존 (R-1, R-6, H-5) | `opal/core/AGENT.md` | grep 잔존: `## 부트스트랩` + `Phase A` + `Phase B` + `.opal/AGENT.md` 게이트 + `[스킵 게이트` + `부트스트랩 완료 보고` | 부트스트랩 절(Eager 2-phase·step0·완료보고) 전부 잔존 | ✅PASS — L5 `## 부트스트랩`, L13 Phase A, L26 Phase B, L28 게이트, L17 스킵 게이트, L68 완료보고 전부 확인 |
| TS-003 | 비서 코어 완결성 7항목 (R-6, H-3) | `opal/core/AGENT.md` | grep 잔존: `## 정체성 적용`·`### 보고 형식`·`### 도구·MCP 적극 활용 규칙`·`//`불변식(Phase A `opi 발동`)·`### 주도성`·`## 핵심 역할`·`#### 상태 정의` | 필수 7섹션 전부 잔존 | ✅PASS — L83 정체성 적용, L177 보고 형식, L127 도구·MCP 규칙, L15 opi 발동 불변식, L159 주도성, L93 핵심 역할, L120 상태 정의 전부 확인 |
| TS-004 | opal-pm.md 이관 섹션 수신 (R-2) | `opal/core/references/opal-pm.md` | grep 잔존: 역할전환 상세(`하네스 적용 기준`·`자동 전환`·`L2`)·`code-scan 활용`·`opal-brain 활용`·`메모리 브리핑`·모델매핑 적용·`프로젝트 컨텍스트` | 이관 7섹션 opal-pm.md에 존재 | ✅PASS — §12 하네스 적용 기준/자동 전환/L2, §13 code-scan 활용, §14 opal-brain 활용, §15 메모리 브리핑, §16 모델매핑 적용, §17 프로젝트 컨텍스트 전부 확인 |
| TS-005 | dedup — 중복 표 신설 부재 (R-2, H-2) | `opal/core/references/opal-pm.md` | grep: ① `semi-agentic`+`interactive`+`agentic` 3행 모드 표 신설 **부재** ② 모델매핑 우선순위 표(`setting.local.json`→`setting.json`→표) 신설 **부재** ③ 대신 `opal-harness.md §2`·`opal-harness.md §6`·`opal-model-mapping.md §5` 포인터 **존재** | 3-way·모델매핑 표 미복사 + 포인터 단일화 존재 | ✅PASS — semi-agentic/interactive/agentic 언급은 포인터·맥락설명뿐(표 신설 없음). 모델매핑 우선순위 표 미신설. L151 `opal-harness.md §2`, L314 `opal-harness.md §6 + opal-model-mapping.md §5` 포인터 존재 확인 |
| TS-006 | 포인터 정합 (R-2, H-1) | `opal/core/references/opal-pm.md` | opal-pm.md의 `→ opal-harness.md §2`·`§6`·`opal-model-mapping.md §5` 포인터가 실제 존재 헤딩 지시(대상 grep 확인) | 포인터 대상 실존(dangling 0) | ✅PASS — opal-harness.md L67 `## 2. 모듈 구조`, L178 `## 6. Model Mapping` 실존. opal-model-mapping.md L76 `## 5. 사용자·프로젝트 오버라이드` 실존 |
| TS-007 | bootstrapper-management.md 신규 (R-3) | `opal/core/references/bootstrapper-management.md` | 파일 존재 + grep: 4 플랫폼 소절(`Claude`·`Cursor`·`Codex`·`Antigravity`/`Gemini`) + 수동 삽입 마커 블록(`# === OPAL START ===`+`# === OPAL END ===`) + 2-tier 서술(`전역 마커`+`비서 tier`) | reference 존재 + 4플랫폼 + 마커 블록 + 2-tier 보존 | ✅PASS — 파일 실존. L9 Claude Code, L31 Cursor, L35 Codex, L44 Antigravity(Gemini) 4소절. L21 `# === OPAL START ===`, L28 `# === OPAL END ===`. L5/L7 2-tier 서술 확인 |
| TS-008 | AGENT.md 포인터만 잔류 (R-3, H-4) | `opal/core/AGENT.md` | grep: `## 프로젝트 부트스트래퍼 자동 관리` 절 **부재** + step6 또는 본문에 `bootstrapper-management.md` 참조 1줄 **존재** | 절 제거 + 포인터 1줄 존재 | ✅PASS — 헤딩 0건(부재). L37 step 6에 `(상세: references/bootstrapper-management.md)` 포인터 존재 확인 |
| TS-009 | install 불변 (R-3, R-6) | `scripts/install-mac.sh` | `bash -n scripts/install-mac.sh` exit 0 + grep `extract_bootstrap_content`·`install_opal_section`·`strip_deploy_md` 호출부 불변 | bash -n exit 0 + install 로직 미변경 | ✅PASS — `bash -n` exit 0. extract_bootstrap_content L241, install_opal_section L251/L257/L333, strip_deploy_md L224/L1042/L1046 호출부 전부 불변 확인 |
| TS-010 | 변경이력 trim (R-4) | `opal/core/AGENT.md` | `## 변경이력` 표 데이터 행 ≤6 + "전체 이력"+`git log` 안내 1줄 grep 존재 | 표 ≤6행 + git 링크 안내 | ✅PASS — 데이터 행 6개(≤6). L226 `> 전체 이력: \`git log --follow opal/core/AGENT.md\`` 안내 확인 |
| TS-011 | 변경이력 049·050 보존 (R-4, H-6) | `opal/core/AGENT.md` | 변경이력 grep: `(049)` 행 + `(050)` 행 모두 존재 | 049·050 행 잔존 | ✅PASS — L234 (049) v4.0 행, L235 (050) v4.1 행 모두 잔존 확인 |
| TS-012 | dangling 0 — 전수 grep (R-5) | `opal/` `docs/` | `grep -rn "AGENT.md §\|프로젝트 부트스트래퍼 자동 관리" opal/ docs/` 결과에서 **이동 섹션을 가리키는** 참조 0(잔류=보고형식/스킬레지스트리/기억학습 + 비-core=확정기준/금지규칙/페르소나 제외) | 이동 섹션 dangling 0 | ✅PASS — 참조 결과 전수 확인: state-tool 테스트(§확정 기준 — 비-core), opal-pm.md(출처 주석+§보고 형식 — 잔류 섹션), opal-harness-semi-agentic.md(§보고 형식 — 잔류), skill-commands/memory-learning(출처 주석), execute-specialist-guide(§페르소나/§금지 규칙 — 비-core). 이동 섹션 가리키는 dangling 0 |
| TS-013 | 교차참조 포인터 유효 (R-5, H-1, H-4) | `opal/core/AGENT.md` | X-2(`opal-pm.md §code-scan 활용 규칙`)·X-3(`opal-pm.md §opal-brain 활용 규칙`)·X-1(`bootstrapper-management.md`) 갱신 포인터의 대상 실존 확인 | 갱신 포인터 3건 대상 실존 | ✅PASS — X-1 bootstrapper-management.md 파일 실존. X-2 opal-pm.md L207 `## 13. code-scan 활용 규칙` 실존. X-3 opal-pm.md L239 `## 14. opal-brain 활용 규칙` 실존 |
| TS-015 | WORKER 규칙 보존 (직교 스킵 경로 — 재구성 회귀) | `opal/core/AGENT.md` | grep: `[WORKER 규칙]` 잔존 + 스킵 범위 `부트스트랩 전체`/`Phase A·Phase B·공통 전부` + setting.json과 `별개의 독립 스킵 경로`(또는 `직교 스킵 경로`) 표기 + 비서/PM tier와 무관 명시 | WORKER 규칙 잔존 + 전체 스킵 의미 + 2-phase 명시 + 직교 경로 표기 | ✅PASS — L9 `[WORKER 규칙]` + `Phase A·Phase B·공통 전부 건너뜀` + `직교 스킵 경로` + `비서/PM tier 분기와 무관` 전부 1개 문단에 확인. L20 `별개의 독립 스킵 경로` 추가 확인 |

### L3 — 실세션 동작 회귀 (수동, 부트스트랩 LLM 거동 — 캡틴 직접)

> 049 TS-001~004 회귀 직결. 정적 단언(위 TS-002·TS-003)이 1차 게이트. L3는 실세션 동작 확인.

| TS-ID | 항목 (049 회귀) | 검증 방법 | PASS 조건 | 결과 |
|-------|------|----------|----------|------|
| TS-014a | 049 TS-001 회귀 — Eager 2-phase | 다이제스트 후 AGENT.md에 049 TS-001 grep 재실행 (Phase A/B 구분 + Phase B 게이트 + Phase A identity/PRINCIPLES) | 049 TS-001 PASS 동일 (정적) | ✅PASS — L13 Phase A 비서 tier, L26 Phase B PM tier, L28 게이트 명문화, L22 identity, L24 PRINCIPLES 전부 다이제스트 후 보존 |
| TS-014b | 049 TS-002 회귀 — PM tier 게이팅 | 049 TS-002 grep 재실행 (`.opal/AGENT.md` 부재 시 Phase B 스킵) | 049 TS-002 PASS 동일 (정적) | ✅PASS — L28 "cwd에 `.opal/AGENT.md`가 없으면 Phase B 전체를 스킵한다(harness·opal-pm·PM 컨텍스트 미로드)" 다이제스트 후 보존 |
| TS-014c | 049 TS-003 회귀 — `//` 불변식 | 049 TS-003 grep 재실행 (Phase A `//`(opi) 발동 + Lazy 트리거 전제조건 부재) | 049 TS-003 PASS 동일 (정적) | ✅PASS — L15 Phase A `//opi 발동 가능` 불변식 + L52 Lazy 트리거 `//` 전제조건 `-`(없음) 다이제스트 후 보존 |
| TS-014d | 049 TS-004 회귀 — step0 스킵게이트 | 049 TS-004 grep 재실행 (setting.json+bootstrap:off+fail-safe+models) | 049 TS-004 PASS 동일 (정적) | ✅PASS — L17~19 step 0 스킵게이트+effective setting+bootstrap:off 판정+fail-safe+models 로드 다이제스트 후 전부 보존 |
| TS-014e | 비서 세션 실세션 동작 | 비-opi 폴더 새 세션 — 비서 활성(identity·보고형식·도구판단·`//` 진입·주도성) + 완료보고 `⬜ harness ⬜ PM` | 비서 코어 행동 완결(정보 손실 0) | ⏸ pending (캡틴) |
| TS-014f | PM 세션 실세션 동작 | opi 프로젝트 새 세션 — opal-pm.md 로드 후 역할전환/code-scan/brain/메모리브리핑/모델매핑 적용이 PM 행동으로 정상 발동 | 이관 섹션이 opal-pm.md 경유로 PM 세션에서 정상 동작 | ⏸ pending (캡틴) |

---

## 2. 코드 품질

> L1 정적 검사 기반 — 마크다운 grep, install `bash -n`.

| 항목 | 기준 | 결과 |
|------|------|------|
| 변경이력 기록 | AGENT.md(050) + opal-pm.md(050) + bootstrapper-management.md(v1.0/050)에 050 행(KST 일시) | ✅PASS — AGENT.md L235 v4.1(050), opal-pm.md L348 v1.4(050), bootstrapper-management.md L58 v1.0(050) 전부 확인 |
| install 구문 무결 | `bash -n scripts/install-mac.sh` exit 0 (로직 불변 — 검증만) | ✅PASS (TS-009) — bash -n exit 0 확인 |
| 과서술/과설계 금지 | 신규 reference 1개만(PRINCIPLES.md §2) + 유지 섹션 문구 불변(PRINCIPLES.md §3 Surgical) | ✅PASS — bootstrapper-management.md 1개만 신규 생성. 기존 섹션 문구 불변 |
| dedup | 3-way·모델매핑 우선순위 표 목적지 중복 신설 부재(포인터 단일화) | ✅PASS (TS-005) — 표 신설 없음, 포인터만 존재 |
| Lazy 테이블 과확장 금지 | bootstrapper-management.md를 런타임 Lazy 트리거로 신규 등록 안 함(설치시점 가이드) | ✅PASS — Lazy 트리거 테이블에 bootstrapper-management.md 행 없음. step 6 인라인 포인터(상세: 참조 링크)만 존재 |

---

## 3. 보안

| 항목 | 기준 | 결과 |
|------|------|------|
| 시크릿 없음 | 이동/신규 문서 변경분에 토큰/시크릿(api_key/secret/token/Bearer) 없음 | ✅PASS — grep 결과 3개 변경 파일 모두 해당 패턴 없음 |
| 권한 최소 — 신 표면 0 | reference 문서는 Read 대상, 신규 MCP/권한 등록 0 | ✅PASS — reference 신규 파일 1개(bootstrapper-management.md)는 Read 대상. 신규 MCP/권한 등록 없음 |
| 민감정보 비저장 | bootstrapper 마커는 부트스트랩 진입 지시만(인증/네트워크/시크릿 없음) | ✅PASS — 마커 블록(OPAL START/END)은 AGENT.md/identity.md 로드 지시만 포함. 인증·네트워크·시크릿 없음 |

---

## 4. 회귀 테스트

| 항목 | 기준 | 결과 |
|------|------|------|
| 049 TS-001~004 불변 | 다이제스트 후 AGENT.md 정적 grep 재실행 PASS | ✅PASS (TS-014a~d) — 4건 전부 다이제스트 후 보존 확인 |
| 부트스트랩 완료 보고 형식 | 비서 세션 `⬜ harness ⬜ PM ⬜ PM모드` 표기 규칙 보존 | ✅PASS (TS-002) — L79 비서 세션 ⬜ 표기 규칙 보존 확인 |
| opal-pm.md §8 참조 불변 | `AGENT.md §보고 형식` 참조(보고형식 잔류) 불변 | ✅PASS — opal-pm.md L104 `AGENT.md §보고 형식 (Eager 인라인)` 참조 불변. AGENT.md §보고 형식 잔류 확인 |
| install 배포 파이프라인 불변 | strip_deploy_md(변경이력)·extract_bootstrap_content(마커) 무영향 | ✅PASS (TS-009) — bash -n exit 0. 호출부 불변 확인 |
| Antigravity 자동 삽입 동작 불변 | step6 Gemini 자동삽입 로직 불변(포인터만 이관처로 변경) | ✅PASS (TS-008) — L37 step 6 Antigravity 자동삽입 로직 불변. 포인터가 references/bootstrapper-management.md로 이관처 지시 |

---

## 5. 시나리오 ↔ AC/리스크 매핑

| TS-ID | F-ID | AC/완료기준 | 리스크(H) | 트랙 |
|-------|------|-----------|----------|------|
| TS-001, TS-003 | F-001 | R-1·R-6 / 완료기준 ①④⑤ | H-3, H-5 | 정적 |
| TS-002 | F-001 | R-1·R-6 / 완료기준 ④ | H-5 | 정적 |
| TS-004, TS-005, TS-006 | F-002 | R-2 / 완료기준 ② | H-1, H-2, H-7 | 정적 |
| TS-007, TS-008, TS-009 | F-003 | R-3 / install 불변 | H-4 | 정적 + bash -n |
| TS-010, TS-011 | F-004 | R-4 | H-6 | 정적 |
| TS-012, TS-013 | F-005 | R-5 / 완료기준 ③ | H-1, H-4 | 정적 |
| TS-014a~d | F-001 | R-6 / 완료기준 ④ | H-5 | 정적(049 재실행) |
| TS-014e~f | F-001·F-002 | R-6 / 비서 코어 완결·PM 동작 | H-3, H-5 | L3 실세션 |
| TS-015 | F-001 | R-6 / WORKER 직교 스킵 보존 | H-5 | 정적(재구성 회귀) |

---

## 6. 실행 노트

- **RED-first 산출물 없음**: 본 태스크는 red-first.md §1.5 "RED-first 강제" 5종에 해당하는 변경이 0건(순수 문서 이동·dedup·trim = 설정·문서 + 행위 불변 리팩터). RED 셸/node 테스트 선작성 불요. state-tool `--red-check` OFF.
- **정적 단언 자동화**: TS-001~013·TS-014a~d는 grep/`bash -n`으로 결정론적 PASS/FAIL. opal-test-agent가 일괄 수행(작성자≠구현자 — 구현 워커와 분리).
- **L3 실세션(graceful skip)**: TS-014e/f는 부트스트랩·PM 행동 LLM 거동이라 캡틴 직접 확인(pending). install 재배포는 캡틴 책임(배포 경계).
- **dangling 전수 grep 주의(TS-012)**: 잔류 참조(보고형식·스킬레지스트리·기억학습 출처 주석)와 비-core AGENT.md 참조(확정기준·금지규칙·페르소나·결과반환 — 프로젝트/에이전트 레벨)는 dangling이 아니다. 이동 섹션(역할전환 상세·code-scan/brain 활용·메모리브리핑·모델매핑·부트스트래퍼·프로젝트 컨텍스트)을 가리키는 참조만 0이어야 한다.

---

## 7. 최종 판정

> 실행일: 2026-06-30 | 실행자: opal-test-agent

| 분류 | 수 |
|------|-----|
| ✅ PASS (L1 정적+bash -n) | 17 (TS-001~013, TS-014a~d, TS-015) |
| ⏸ pending (L3 실세션) | 2 (TS-014e, TS-014f) |
| ❌ FAIL | 0 |

**종합 판정: TEST PASS (L3 pending=캡틴)**

- L1 정적 단언 13건 전체 PASS (TS-001~013, TS-015)
- L1 회귀 4건 전체 PASS (TS-014a~d) — 049 grep 단언 다이제스트 후 보존 확인
- 코드 품질 5항목 PASS, 보안 3항목 PASS, 회귀 5항목 PASS
- L3 실세션 2건(TS-014e, TS-014f)은 부트스트랩·PM 행동 LLM 거동 — 결정론적 자동화 불가, 캡틴 직접 확인 대기 (graceful skip)
