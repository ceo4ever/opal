# PLAN: 제미나이 플랫폼 전용 OPAL 규율 강화 (Hardening)

> 최종 갱신: 2026-04-02 | 기존 PLAN 대비 설계 방향 전면 전환 + 제미나이 알투 제언 3건 반영

---

## 1. 설계 방향 (기존 대비 변경 사항)

### 변경 전 (초기 PLAN)
- `gemini-bootstrap-hardened.md` 별도 파일 생성
- `~/.opal/identity.md` 직접 수정 → **배포 금지 원칙 위반**
- "자아 교정(Process-First Identity)" 중심 접근

### 변경 후 (확정)
- 별도 파일 없이 **GEMINI.md에 HARDENING 섹션 추가** (단일 파일 원칙)
- identity 준수는 GEMINI.md 내 **GUARD-3**으로 대체 (배포 금지 원칙 준수)
- "자아 교정" → **Guard + 명시적 실패 보고(FAIL 코드)** 구조로 전환
- Phase Gate는 opal-harness.md에 추가하지 않고 **GEMINI.md 전용**으로 적용

### 변경 근거
| 항목 | 이유 |
|------|------|
| 자아 교정 접근 폐기 | 정체성 문구 강화는 긴 세션에서 희석됨. 근본 원인(구조적 강제 장치 부재)과 불일치 |
| identity.md 직접 수정 폐기 | 배포 금지 원칙: `~/.opal/` 파일은 이 프로젝트에서 직접 수정하지 않음 |
| opal-harness.md Phase Gate 보류 | 제미나이에서만 확인된 문제 — 공통 하네스 수정은 과잉 적용 가능성. 제미나이 전용으로 먼저 적용 |
| SSOT 보류 | interactive/agentic 모드, 스킬별 커뮤니케이션 패턴 차이로 별도 검토 필요 |

---

## 2. 확인된 문제 및 처방

| # | 증상 | 원인 | 처방 | Guard |
|---|------|------|------|-------|
| 1 | Lazy 항목을 전부 즉시 로드 | Lazy 금지 조건 없음 | `opal/core/AGENT.md` 금지 원칙 추가 | GUARD-2 |
| 2 | 읽었다 하고 내용 안 지킴 | 읽기 검증 게이트 없음 | Read-Proof (동적 문서 한정) | GUARD-5 |
| 3 | PLAN 보자마자 실행, QA 생략 | 단계 전환 선행 조건 없음 | Phase Gate (하네스/스킬 위임) | GUARD-4 |

---

## 3. 수정 대상 파일

| 파일 | 성격 | 변경 내용 |
|------|------|---------|
| `opal/core/AGENT.md` | 공통 (전 플랫폼) | Lazy 금지 원칙 + 트리거 테이블 `트리거 전 로드` 열 추가 |
| `GEMINI.md` (루트) | 제미나이 전용 | `GEMINI HARDENING` 섹션 추가 |
| `opal/skills/opal-project-init/templates/common/platform/GEMINI.md` | 제미나이 전용 (신규 프로젝트 템플릿) | 동일 내용 추가 |

---

## 4. GEMINI HARDENING 섹션 구조

GEMINI.md에 추가할 `=== GEMINI HARDENING START/END ===` 섹션.

### GUARD 구조 (5개)

| Guard | 이름 | 해결 문제 | 실패 코드 |
|-------|------|---------|---------|
| GUARD-1 | 부트스트랩 강제 | Eager 미완료 → 첫 응답 차단 | `BOOTSTRAP_INCOMPLETE` |
| GUARD-2 | Lazy 로딩 금지 | 트리거 없는 선행 로드 차단 | `LAZY_PRELOAD` |
| GUARD-3 | 정체성 준수 | identity.md 미적용 차단 | `IDENTITY_NOT_APPLIED` |
| GUARD-4 | Phase Gate | 하네스/스킬 Gate 우회 차단 | `PHASE_GATE_VIOLATION` |
| GUARD-5 | Read-Proof | 동적 문서 미인용 차단 | `READ_UNVERIFIED` |

### 실패 보고 공통 형식

```
⛔ [GEMINI FAIL] {실패 코드}
위반: {무엇을 어겼는가}
현재 상태: {어디까지 진행됐는가}
조치: {무엇을 해야 하는가}
```

### GUARD-4 설계 원칙

Phase Gate 조건 테이블을 GEMINI.md에 하드코딩하지 않는다.

- **Gate 규칙 정의**: 로드된 서브 하네스(`opal-harness-interactive.md` 또는 `opal-harness-agentic.md`) 및 스킬 SKILL.md를 따름
- **GEMINI.md의 역할**: "하네스/스킬이 정의한 Gate를 반드시 거쳐야 한다. 어기면 FAIL이다"를 강제

모드/스킬에 무관하게 공통 적용되는 실패 조건:
- 하네스에 정의된 Gate 우회
- 캡틴 명시 승인 없이 단계 전환 (interactive 모드)
- QA 단계를 하네스 정의 또는 캡틴 지시 없이 생략
- 완료 보고 전 체크리스트 미갱신

**승인 키워드 목록** (캡틴 메시지에 아래 중 하나가 있어야 단계 전환 가능):

> "승인", "진행해", "진행해줘", "OK", "ok", "좋아", "맞아", "그래", "해줘", "네"

위 키워드 없이 단계 전환 시도 → `PHASE_GATE_VIOLATION`
캡틴이 키워드를 추가/수정할 수 있음 (이 목록은 기본값).

### GUARD-5 적용 범위 및 보고 형식

| 문서 유형 | 적용 여부 | 근거 |
|---------|---------|------|
| PLAN.md, TASK.md, STATE.md (동적) | ✅ 적용 | 태스크마다 내용이 달라 메모리 위조 어려움 |
| identity.md, opal-harness.md (정적) | ❌ 제외 | 메모리에서 그럴듯한 인용 생성 가능 — 실효성 낮음 |

**보고 형식** (제미나이 알투 제언 반영 — Step 추적 + 제약 인용 병합):

```
[Read 완료] {파일명}
현재 Step: Step {N} — {Step 제목}
적용 제약: "{PLAN/TASK에서 현재 작업에 적용되는 제약 직접 인용}"
```

`현재 Step` 필드가 PLAN → EXECUTE 점프를 물리적으로 차단하는 역할을 한다.
"마지막 체크리스트 항목"이 아닌 **현재 진행 중인 Step**을 명시 (미래 항목 복창 방지).

---

## 5. 구현 단계

### Step 1: `opal/core/AGENT.md` — Lazy 금지 원칙 + 트리거 테이블 확장

Lazy 트리거 테이블 위에 금지 원칙 문구 추가:
```markdown
> **[LAZY 금지 원칙]** Lazy 항목은 트리거 조건이 발생하기 전까지 절대 로드하지 않는다.
> "미리 읽어두면 도움이 될 것 같다"는 판단으로 선행 로드하는 것은 금지다.
> 트리거 없이 Lazy 항목을 로드한 세션은 부트스트랩 비정상으로 간주한다.
```

트리거 테이블 컬럼 2개 추가 (제미나이 알투 제언 반영):

| 트리거 조건 | 로드 대상 | 전제 조건 | 트리거 전 로드 | 위반 시 조치 |
|------------|----------|----------|--------------|------------|
| `//` 커맨드 | skill-registry → skills.md | - | **금지** | 로드 중단, 트리거 발생 시 재로드 |
| 워커 디스패치 직전 | agents.md + model-mapping.md | 하네스 완료 | **금지** | 로드 중단, 트리거 발생 시 재로드 |
| MCP 사용 요청 | mcps.md | - | **금지** | 로드 중단, 트리거 발생 시 재로드 |
| 프로젝트 작업 요청 또는 `//opp` | `.opal/AGENT.md` (PM) + `docs/PROJECT.md` | 하네스 완료 | **금지** | 로드 중단, 트리거 발생 시 재로드 |
| PM 컨텍스트 로드 후 또는 소유자 요청 | `.opal/MEMORY.md` | PM 컨텍스트 완료 | **금지** | 로드 중단, 트리거 발생 시 재로드 |

`위반 시 조치` 컬럼이 GEMINI.md GUARD-2의 `LAZY_PRELOAD` FAIL 코드와 연결됨.
이 컬럼은 플랫폼 중립 — 클로드 포함 전 플랫폼에 절차적 엄격함이 전파된다.

### Step 2: `GEMINI.md` (루트) — HARDENING 섹션 추가

기존 `=== OPAL END ===` 아래에 `=== GEMINI HARDENING START/END ===` 섹션 추가.
GUARD-1 ~ GUARD-5 전체 포함.

### Step 3: 템플릿 동기화

`opal/skills/opal-project-init/templates/common/platform/GEMINI.md`에 Step 2와 동일한 내용 추가.

---

## 6. QA 체크리스트

### GUARD 설계 검증
- [x] GUARD-1: Eager 3개 미완료 시 첫 응답이 실제로 차단되는 구조인가?
- [x] GUARD-2: Lazy 금지 조건이 AGENT.md와 GEMINI.md에서 일관되게 정의되어 있는가?
- [x] GUARD-2: AGENT.md 트리거 테이블에 `트리거 전 로드` + `위반 시 조치` 컬럼이 모두 추가되었는가?
- [x] GUARD-3: identity 미적용 시 FAIL 코드가 명확히 출력되는가?
- [x] GUARD-4: Phase Gate가 하네스/스킬을 위임하면서도 우회 불가 원칙을 유지하는가?
- [x] GUARD-4: 승인 키워드 목록이 명시되어 있고 캡틴이 수정 가능하다는 안내가 있는가?
- [x] GUARD-5: 동적 문서만 적용되고 정적 문서는 제외되어 있는가?
- [x] GUARD-5: 보고 형식에 `현재 Step` + `적용 제약` 두 필드가 모두 포함되어 있는가?

### 설계 원칙 검증
- [x] 배포 금지 원칙 준수: `~/.opal/` 직접 수정 없음
- [x] 공통 하네스(opal-harness.md) 미수정 (Phase Gate는 GEMINI.md 전용)
- [x] 템플릿과 루트 GEMINI.md가 동일한 내용인가?
- [x] **[Self-Check]** 완료 보고 전 이 체크리스트를 모두 갱신했는가?

### 보류 항목 확인
- [x] SSOT Enforcement는 이 태스크에 포함되지 않음 (별도 검토 필요 — 보류 사유: interactive/agentic 모드, 스킬별 차이)
