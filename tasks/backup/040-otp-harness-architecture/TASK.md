# TASK: OPAL Harness Architecture — otp를 Agent Harness로 재설계

> 작성일: 2026-03-29 | 작업 유형: 아키텍처 설계
> 입력: 사용자 요청
> 출력: TASK.md → 설계 문서

## 작업 목표

OPAL 프레임워크의 otp 레이어를 **Agent Harness Engineering** 관점으로 재설계한다. 현재 도메인별로 복제된 오케스트레이터(otp-dev, otp-write, otp-wf)를 **범용 하네스(Harness) + 도메인 프로파일(Domain Profile)**로 분리하여, 어떤 종류의 작업이든 하나의 하네스 위에서 체계적으로 수행할 수 있게 한다.

## 배경

### Harness Engineering이란

> "에이전트가 아니라 하네스가 어려운 부분이다" — OpenAI Codex 팀

AI 에이전트를 감싸는 **운영 인프라 전체**를 설계하는 분야:
- **Context Engineering** — 에이전트에게 지속적으로 컨텍스트 제공
- **Constraints** — 가드레일, 금지 행동, 범위 제한
- **Feedback Loops** — QA, 검증, 자기 교정
- **State Management** — 상태 추적, 세션 복원
- **Observability** — 모니터링, 게이트 체크포인트

### OPAL은 이미 하네스를 구축하고 있었다

| Harness 구성 요소 | OPAL 현재 대응 | 문제점 |
|-------------------|---------------|--------|
| **Context** | AGENT.md, MEMORY.md, PROJECT.md | ✅ 잘 작동 |
| **Process** | otp-dev, otp-dev-short, otp-wf, otp-write | ❌ 도메인별 복제, 90% 중복 |
| **Constraints** | 구현 금지 원칙, 커밋 규칙, 가드레일 | ❌ 각 otp에 복붙 |
| **Feedback** | dtp-qa, dtp-test, PM 검토 게이트 | ✅ 공용 워커로 잘 분리 |
| **State** | STATE.md, 메모리 동기화 | ❌ 각 otp에 템플릿 복붙 |
| **Tools** | dtp-* 스킬, MCP, 커뮤니티 스킬 | ✅ 독립 컴포넌트로 잘 분리 |

**핵심 문제**: Process / Constraints / State가 도메인별 otp에 결합되어 복제되고 있다. 새 도메인이 추가될 때마다 하네스 전체를 복제해야 한다.

### 실제 발생한 문제 (036~039)

1. **038**: 캡틴이 스킬 개발에 `//otpd` 호출 — 프로세스가 필요했지 코드 개발이 아니었음
2. **otp 복제 패턴**: otp-write 생성 시 otp-dev-short에서 게이트/STATE/커밋 규칙을 복붙
3. **단계 중복**: 4개 otp의 TASK 단계가 95% 동일, PLAN도 70% 유사

## 설계 방향: Harness + Domain Profile

### 용어 정의

| 용어 | 정의 |
|------|------|
| **Harness** | 모든 작업에 공통 적용되는 프로세스 인프라 (Context, Process, Constraints, Feedback, State, Observability) |
| **Domain Profile** | 특정 작업 도메인의 전문성을 정의하는 설정 (조사 방식, 설계 패턴, 실행 워커, 도구/스킬) |
| **Pipeline** | Harness가 제공하는 단계별 프로세스 흐름 (TASK → ANALYSIS → PLAN → EXECUTE) |
| **Gate** | 단계 간 사용자 승인/피드백/중단 체크포인트 |
| **Guard** | 에이전트 행동 제약 (구현 금지 원칙, 커밋 규칙 등) |

### 목표 아키텍처

```
OPAL Framework
  ├── Context Layer (기존 유지)
  │   ├── identity.md — 에이전트 정체성
  │   ├── AGENT.md — PM 역할 + 프로젝트 컨텍스트
  │   ├── MEMORY.md — 프로젝트 메모리
  │   └── PROJECT.md — 프로젝트 정의 + 문서 레지스트리
  │
  ├── Harness Layer (신규 — otp 공통 인프라)
  │   ├── Pipeline — TASK → [ANALYSIS] → PLAN → EXECUTE
  │   ├── Gates — 단계 간 승인/피드백/중단
  │   ├── Guards — 구현 금지 원칙, 커밋 규칙
  │   ├── State — STATE.md 관리, 세션 복원
  │   ├── Observability — 보고 형식, 메모리 동기화
  │   └── Mode — Full / Short 프로세스 선택
  │
  ├── Domain Profiles (신규 — 도메인별 설정)
  │   ├── dev — 코드 개발 (dtp-execute, dtp-test)
  │   ├── write — 문서 작성 (직접 수행, opal-doc-standard)
  │   ├── wf — 와이어프레임 (wireframe-builder, ui-designer)
  │   ├── skill — 스킬/에이전트 개발 (skill-creator)
  │   └── ... (확장 가능)
  │
  └── Tool Layer (기존 유지)
      ├── dtp-* 단계 스킬
      ├── MCP 서버
      └── 커뮤니티 스킬
```

### 사용자 경험

```
//otp 로그인 기능 개발해줘      → Harness 기동 → 도메인 감지: dev
//otp PRD 작성해줘              → Harness 기동 → 도메인 감지: write
//otp 대시보드 화면 만들어줘     → Harness 기동 → 도메인 감지: wf
//otp 새 스킬 만들어줘           → Harness 기동 → 도메인 감지: skill

// 명시적 도메인 지정도 가능
//otp-dev, //otpw 등 기존 약어 유지 (하위 호환)
```

## 검토 항목

### 1. Harness 설계

- [ ] Pipeline 공통 프로세스 정의 (어떤 단계가 공통이고, 어디서 도메인 분기가 일어나는가)
- [ ] Full / Short 모드 전환 기준
- [ ] Gates 공통 패턴 (승인/피드백/중단 응답 처리)
- [ ] Guards 공통화 (구현 금지 원칙, 커밋 규칙을 하네스 레벨로)
- [ ] State 관리 통일 (STATE.md 템플릿, 세션 복원)
- [ ] Observability 통일 (보고 형식, 메모리 동기화)

### 2. Domain Profile 설계

- [ ] 프로파일 스키마 정의 (어떤 필드가 있어야 하는가)
- [ ] 도메인 자동 감지 로직 (사용자 요청에서 도메인 판별)
- [ ] 각 프로파일의 ANALYSIS/PLAN/EXECUTE 분기 정의
- [ ] 기존 otp-dev/otp-write/otp-wf에서 도메인 전문성만 추출하는 방법

### 3. 마이그레이션

- [ ] 기존 otp 스킬과의 공존 전략 (래핑? 점진적 흡수?)
- [ ] opal-skill-creator/opal-agent-creator와의 관계
- [ ] 단계별 전환 로드맵

## 039 완료 인사이트

039(otp-write-tech)가 완성되면서 Harness 설계에 중요한 패턴이 도출되었다:

| 인사이트 | 내용 |
|----------|------|
| **4 Phase Pipeline** | 병렬 분석 → PM 진단 → 병렬 작성 → 정합성 검증 — otp-dev의 4 STEP과 구조적으로 유사 |
| **PM + 워커 역할 분리** | PM이 판단(진단/배치/검수), 워커가 실행(분석/작성/검증) — 이것이 Harness의 핵심 패턴 |
| **diagnosis.json** | Phase 간 데이터를 구조화된 JSON으로 전달 — Pipeline State의 원형 |
| **배치 편성** | 의존성 DAG 기반 병렬/순차 결정 — PLAN의 복잡도 판별 + 실행 아키텍처와 동일 패턴 |
| **references/ 분리** | 도메인 전문 지식을 references/로 분리 — 이것이 Domain Profile의 원형 |
| **모드 분기** | 작성/수정/분석 3가지 모드 — Full/Short 모드의 확장 패턴 |

### otp-write-tech의 4 Phase → Harness Pipeline 매핑

```
otp-write-tech           Harness Pipeline         otp-dev (비교)
─────────────           ────────────────         ──────────────
Phase 1: 병렬 분석    →  ANALYSIS (조사)        →  STEP 2: ANALYSIS
Phase 2: PM 진단      →  PLAN (설계/판단)       →  STEP 3: PLAN
Phase 3: 병렬 작성    →  EXECUTE (산출)         →  STEP 4: EXECUTE
Phase 4: 정합성 검증  →  VERIFY (검증)          →  dtp-test + dtp-qa
```

## 제약 조건

- 이번 태스크는 **설계 문서 산출**이 목표. 스킬 구현은 후속 태스크
- 기존 otp 스킬은 당장 삭제하지 않음 (하위 호환 유지)
- 실제 사용 경험(036~039)에서 나온 인사이트를 근거로 설계

## 산출물

1. **OPAL Harness Architecture 설계 문서** — 하네스 구조, 도메인 프로파일 스키마, 파이프라인 흐름
2. **마이그레이션 로드맵** — 현재 → 목표 아키텍처 전환 단계

## 관련 문서

- [memory/architecture_otp_harness_vertical.md](.opal/memory/architecture_otp_harness_vertical.md) — 아키텍처 방향 메모리
- [skills/otp-dev/SKILL.md](skills/otp-dev/SKILL.md) — Full Task 오케스트레이터
- [skills/otp-dev-short/SKILL.md](skills/otp-dev-short/SKILL.md) — Short Task 오케스트레이터
- [skills/otp-write/SKILL.md](skills/otp-write/SKILL.md) — 문서 작성 오케스트레이터
- [skills/otp-wf/SKILL.md](skills/otp-wf/SKILL.md) — Wireframe UI 오케스트레이터
- [skills/otp-write-tech/SKILL.md](skills/otp-write-tech/SKILL.md) — 서비스 기획 산출물 오케스트레이터 (039 완료)

## 참조

- [Harness Engineering | OpenAI](https://openai.com/index/harness-engineering/)
- [Harness Engineering | Martin Fowler](https://martinfowler.com/articles/exploring-gen-ai/harness-engineering.html)
- [The importance of Agent Harness in 2026 | Phil Schmid](https://www.philschmid.de/agent-harness-2026)
- [Your Agent Needs a Harness, Not a Framework | Inngest](https://www.inngest.com/blog/your-agent-needs-a-harness-not-a-framework)
