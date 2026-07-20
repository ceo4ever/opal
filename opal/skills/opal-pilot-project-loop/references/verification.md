# 검증 가이드 (3-tier + 2원화 + 기록 규칙)

> opal-pilot-project-loop(oppl)의 검증 체계 — 결정론/루브릭/사람 3-tier 위계와 Evaluator/test-agent 2원화, 산출물 기록 규칙.
> SKILL.md `## 검증 2원화` 절에서 인라인 참조한다.
> 근거: `tasks/056-260710-opd-oppl-루프-오케스트레이터/SPEC.html` §04 "검증 3-tier + 기준 항목", §03 note "산출물·기록 규칙".

---

## 1. 개요

oppl의 검증은 두 개의 서로 직교하는 축으로 구성된다.

1. **검증 3-tier** — 무엇을 기준으로 판정하는가 (§2)
2. **검증 2원화** — 언제·누가 판정하는가 (§3)

두 축은 함께 작동한다 — 태스크 파이프라인의 G 게이트는 "누가"(Evaluator, 구현 전) × "무엇으로"(② 루브릭 tier)의 교차점이고, T4a는 "누가"(test-agent, 구현 후) × "무엇으로"(① 결정론 tier)의 교차점이다.

---

## 1.5 증거 충실도 사다리 (Evidence Fidelity Ladder)

> 검증 3-tier(§2)·2원화(§3)가 "무엇을·언제·누가" 판정하는지를 규정한다면, 본 절은 "어떤 실행 환경에서 관찰된 결과라야 인정하는가"를 규정한다 — 목(mock) 상대 GREEN과 실 서버·실 브라우저 GREEN을 동일한 "verified"로 집계하는 갭을 봉쇄한다(069).

### 1.5.1 충실도 3단계 정의

| 단계 | 정의 |
|------|------|
| `mock` | 목(mock) 상대 테스트 코드 — 단위(unit) 수준. 실 네트워크·실 서버·실 브라우저 미개입. |
| `real-http` | 실 서버 기동 + 계약 spec(예: OpenAPI/스웨거) 기반 실 HTTP 전수 conformance. auth 표면은 실 로그인 토큰 체인(로그인 → 토큰 → Authorization 헤더)을 포함해야 한다. |
| `real-usage` | 실 브라우저(cmux browser 우선 / playwright 폴백) E2E — 실 진입점(entry point)·실 데이터 흐름을 통해 사용자와 동일한 경로로 관찰한다. |

사다리 순서는 `mock(0) < real-http(1) < real-usage(2)`이며, 상위 단계가 하위 단계를 포함(subsume)한다.

### 1.5.2 BE/FE 매핑

| 영역 | 단위 | 통합 |
|------|------|------|
| BE | 테스트 코드(`mock`) | spec 기반 실 HTTP(`real-http`) |
| FE | 목 허용 컴포넌트 테스트(`mock`) | 실 브라우저 × 실 BE(`real-usage`) |

### 1.5.3 [MUST] done 규범

완료(done)의 최종 증거는 사용자가 실제 접촉하는 방식과 같은 충실도에서 관찰된 것만 인정한다. 사용자 접촉 표면·여정은 real-usage PASS ≥1 없이 done을 인정하지 않는다.

### 1.5.4 [MUST] 실행 주체

oppl 프레임워크 도구는 규범·게이트만 정의하며, 실 HTTP 호출·브라우저 E2E 실행의 주체는 대상 프로젝트의 test-agent다.

## 1.6 워킹 스켈레톤 게이트 메커니즘

워킹 스켈레톤(실행 스켈레톤, `SKILL.md` D5 의무 — 069) 태스크의 존재·구성 판정은 backlog-tool 전용 게이트를 두지 않는다 — 어느 태스크가 스켈레톤인지 구조적으로 탐지하기 취약하기 때문이다. 대신 **D6 Evaluator 판정 항목**(스켈레톤 존재·구성 4항, binary — `opal-evaluator-agent/AGENT.md` Base 루브릭)으로 집행하며, 커버리지 게이트(`backlog-tool coverage-check`)가 스켈레톤 표면의 커버 여부를 간접 보강한다.

---

## 2. 검증 3-tier 위계

**결정론 → 루브릭 → 사람** 순서로, **하위 tier를 통과해야 상위 tier로 진행**한다 (Anthropic 등급 체계와 정합 — SPEC §09 근거).

| tier | 성격 | 담당 | 판정 형태 |
|------|------|------|----------|
| ① 결정론 (code-based) | 객관·재현·무료 | test-tool(L1~L3)·convention/security-checker | binary/threshold pass·fail |
| ② 루브릭 (LLM-judge) | 주관·판단 | opal-evaluator-agent | 앵커된 척도(Likert 1–5, 통과선 ≥4) + drift binary |
| ③ 사람 (human) | 최종·비가역 게이트 | User | 승인/거부 |

### 2.1 ① 결정론 기준 항목

| 기준 항목 | 판정 형태 | 도구 |
|----------|----------|------|
| Lint/Format | binary — 오류 0 | L1 · test-tool |
| Build/Type | binary — pass | L2 |
| Unit/Integration | binary — 100% green | L3a · test-tool |
| E2E(L3b) | binary — pass, 실행 환경=실 브라우저(cmux-tool 우선/playwright 폴백) | L3b |
| 계약 conformance | binary — 표면 인벤토리 전수(분모=surfaces.json) 실 서버·실 HTTP 대조, `surface_unverified` exit 시 fail (상세 §2.1.1) | test-agent + `test-tool scenario-conformance` (`contract.md` §2.2 기계검증절) |
| 커버리지 | threshold — ≥ N% | test-tool |
| 보안·정적분석 | threshold — critical 0 | security-checker |

#### 2.1.1 [MUST] 계약 conformance 실행 규범 (원문)

분모=표면 인벤토리(surfaces.json) 전수. 실행 방식=실 서버 기동+실 HTTP로 응답 형태를 계약과 대조하며, `auth:required` 표면은 실 로그인 토큰 체인(로그인→토큰→Authorization 헤더)으로 호출해야 결과 인정(목·핸들러 단위 테스트 대체 불인정). origin 선언 시 표면 전수에 Origin 헤더 요청 + preflight(OPTIONS)를 보내 `Access-Control-Allow-*`를 계약과 대조(CORS 결정론 검사).

### 2.2 ② 루브릭 기준 항목

| 차원 | 척도 | 통과선 | 판정자 |
|------|------|--------|--------|
| 계약 완전성 | Likert 1–5 | ≥4 | Evaluator |
| 계약 일관성 | Likert 1–5 | ≥4 | Evaluator |
| 설계 정합 (구현↔CONTRACT/TRD) | Likert 1–5 | ≥4 | Evaluator |
| drift 필요성 | binary yes/no | — | Evaluator (`contract.md` §4 절차로 연결) |
| 컨벤션 정신 (가독성·네이밍) | Likert 1–5 | ≥4 | Evaluator |
| 아키텍처 적합 (레이어·의존) | Likert 1–5 | ≥4 | Evaluator |

**루브릭 원칙**: 평가자 ≠ 생성자(강한 모델로 평가) · SMART 기준(❌"안전한 출력" → ✅"harmful 0.1% 미만" 식 구체화) · 자동화 우선(기계 채점 가능한 건 전부 ①로 이전) · 엣지 케이스 포함(비정상·초장문·부적절·모호 입력 시나리오화).

### 2.3 ③ 사람

D7(Loop 1 종료 게이트)·비가역 행동 승인이 대상이다. 상세는 `loop-control.md` §9 "사람 게이트"를 따른다.

### 2.4 실패 시 되돌림

| tier | 실패 시 |
|------|--------|
| ① 결정론 실패 | Executor 재작업 (fix loop — `loop-control.md` §2·§7, 하네스 §1 재시도 한도) |
| ② 루브릭 미달 | Evaluator 피드백 (optimizer loop — 통과선 + 반복상한, `loop-control.md` §2) |

---

## 3. 검증 2원화 — Evaluator(구현 전) / test-agent(구현 후)

태스크 내부 파이프라인은 검증 책임을 시점으로 명확히 분리한다 — **이 순서가 뒤바뀌면 명세 리뷰 게이트가 무력화된다(H-9)**.

```
T1 명세·설계 → T2 테스트시나리오(RED-first)
   ↓
G 명세 리뷰 게이트 ── Evaluator ── 구현 전 ── 명세 정합·완전성 루브릭 + RED 확인
   ↓ (verdict: pass)
T3 구현
   ↓
T4a 테스트 ── test-agent ── 구현 후 ── 테스트·계약 conformance·회귀
   ↓ (pass)
T4b 규칙검사 ── conv/sec-checker ── 통과 후 변경 파일 컨벤션·보안
   ↓
T5 마무리
```

**T2 테스트시나리오(RED-first) 세부 순서**: `scenario-init`(spec존 생성, `red_confirmed`는 항상 false로 생성 — 시드 입력 무시) → 실패 테스트 작성·실행(RED 실관찰) → `scenario-red --evidence`(RED 증거와 함께 `red_confirmed`를 tool-gated로 갱신, `locked` 후에는 거부) → `scenario-lock`(전 시나리오 `red_confirmed==true`일 때만 동결). RED를 증거 없이 선언하는 우회 경로를 tool 레벨에서 봉쇄한다(enforce-don't-advise 보강 — 056/ADD-1, `.opal/brain/pages/concept/oppl-scenario-red-confirmed-gap.md`).

**순서 불변 규칙**:

1. **G(Evaluator, 구현 전)가 항상 T3(구현) 이전에 완료된다.** G verdict가 fail이면 T3에 진입하지 않는다.
2. **T4a(test-agent, 구현 후)는 T3 완료 후에만 실행된다.** 구현이 없는 상태에서 test-agent를 호출하지 않는다.
3. **T4b(conv/sec-checker)는 T4a 통과 후에만 실행된다** — "테스트 통과 후 변경 파일" 검사이므로, 아직 테스트를 통과하지 못한 변경분을 컨벤션/보안 검사에 넣지 않는다.
4. **drift 시만 예외적으로 Evaluator를 재콜백한다** — 구현/테스트 중(T3 또는 T4a) CONTRACT.md와의 불일치(drift)가 발견된 경우에만, T4a 이후에도 Evaluator를 다시 호출한다 (`contract.md` §4 절차). 이것이 2원화 순서의 유일한 예외이며, drift가 아닌 일반 재작업에서는 Evaluator를 재콜백하지 않는다.

**순서 증거(evidence) 확인 방법**: 각 verdict/결과에 시점(timestamp)을 남긴다(§5 결과 계약). QA-SPEC.md(G 게이트, 구현 전)의 시점이 test-scenario.json result존(T4a, 구현 후)의 시점보다 항상 앞서야 한다 — 드라이런 검증(TEST-SCENARIO.md S-090)이 이 순서를 evidence로 확인한다.

---

## 4. 산출물 자동 생성

**모든 단계·검사는 완료의 일부로 산출물을 자동 생성한다** — 검증했다는 사실 자체가 산출물로 남지 않으면 검증되지 않은 것으로 취급한다(done = verified 헌법).

| 이벤트 | 자동 산출물 |
|--------|-----------|
| T2 테스트시나리오 작성 | test-scenario.json (spec존) |
| G 명세 리뷰 | QA-SPEC.md |
| T3 구현 | 코드 변경 + verification_log |
| T4a 테스트 | test-scenario.json (result존) + verification_log |
| T4b 규칙검사 | `GC-CONVENTION-{ts}.md` · `GC-SECURITY-{ts}.md` |
| T5 마무리 | DONE.md |

---

## 5. 기록 규칙

### 5.1 기존 리포트 준용

새 리포트 포맷을 만들지 않는다 — **기존 OPAL 리포트를 준용**한다:

| 검사 성격 | 리포트 |
|----------|--------|
| 테스트 결과 | `test-scenario.json`(result존) + verification_log |
| 보안 | `GC-SECURITY-{ts}.md` |
| 컨벤션 | `GC-CONVENTION-{ts}.md` |
| 명세 리뷰 (Evaluator) | `QA-*.md` (기본: `QA-SPEC.md`) |
| 마무리 | `DONE.md` |

### 5.2 폴백 — VERIFICATION.md

위 5종 리포트 중 해당 검사에 대응하는 리포트 포맷이 없는 경우(예: 드라이런 E2E처럼 여러 검사가 복합된 경우)에는 태스크 폴더 `VERIFICATION.md`에 기록한다. `VERIFICATION.md`는 GC-*/QA-* 리포트가 커버하지 못하는 검사만을 위한 잔여(residual) 기록소이며, GC-*/QA-* 리포트를 대체하지 않는다.

### 5.3 결과 계약 (모든 기록 공통 스키마)

모든 검증 산출물은 자기완결적으로 아래 4필드를 포함한다.

```json
{
  "대상": "검증한 항목 (파일/시나리오/게이트 ID)",
  "결과": "PASS | FAIL",
  "사유": "판정 근거 (FAIL 시 상세 필수)",
  "시점": "타임스탬프 (KST)"
}
```

- FAIL인 경우 사유는 재작업에 필요한 구체 정보(오류 위치·기대값·실제값)를 포함한다.
- 시점은 §3 "순서 evidence" 확인에 쓰이므로 모든 기록에 반드시 포함한다.
- `{item, result, reason, suggestion}`(Evaluator 결과 계약 — `opal/agents/opal-evaluator-agent/AGENT.md`)은 이 공통 스키마를 Evaluator 문맥에 특화한 것이다: `item`=대상, `result`=결과, `reason`=사유, `suggestion`=추가 제안(공통 스키마 대비 확장 필드).

---

## 관련 문서

- `opal/skills/opal-pilot-project-loop/SKILL.md` — 본 가이드를 인라인 참조하는 오케스트레이터 본문 (`## 검증 2원화` 절)
- `contract.md` §2.2, §4 — 기계검증절·drift 재콜백 절차 (§2.1, §3-4 규칙의 근거)
- `loop-control.md` §2, §7, §9 — tier 실패 시 재시도 한도·에러 처리·사람 게이트
- `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` — Layered Verification·에스컬레이션 프로토콜 선례
- `opal/agents/opal-evaluator-agent/AGENT.md` — ② 루브릭 tier 판정 실행 주체
- `opal/agents/opal-convention-checker/AGENT.md`, `opal/agents/opal-security-checker/AGENT.md` — GC-*.md 리포트 산출 선례

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-07-10 16:33 | 초기 작성 — 검증 3-tier(결정론/루브릭/사람) 기준 항목 표, 검증 2원화 순서 불변 규칙 + drift 재콜백 예외, 산출물 자동 생성·GC-*/QA-* 기록 규칙·VERIFICATION.md 폴백, 결과 계약 스키마 정의 (056) |
| v1.1 | 2026-07-10 | §3 검증 2원화 절에 "T2 테스트시나리오(RED-first) 세부 순서" 추가 — scenario-init(시드 무력화) → RED 실관찰 → scenario-red(증거 tool-gated 갱신) → scenario-lock 순서 명시 (056/ADD-1) |
| v1.2 | 2026-07-18 22:33 | §1.5 신설 "증거 충실도 사다리" — mock/real-http/real-usage 3단계 정의·BE/FE 매핑·real-usage done 규범([MUST])·oppl 도구 vs 대상 프로젝트 test-agent 실행 주체 분리([MUST]) 명문화. 기존 §2~§5 절 번호 불변 (069) |
| v1.3 | 2026-07-18 22:45 | §2.1 "계약 conformance" 행 갱신([MUST] 분모=surfaces.json 전수·실 서버+실 HTTP·auth 토큰 체인·CORS preflight 결정론 검사, 원문은 §2.1.1로 분리) + `test-tool scenario-conformance` 도구 반영, "E2E(L3b)" 행에 실행 환경(실 브라우저, cmux-tool 우선/playwright 폴백) 명시. §1.6 신설 "워킹 스켈레톤 게이트 메커니즘"(D6 Evaluator 판정 항목 집행 + 커버리지 게이트 간접 보강) (069) |
