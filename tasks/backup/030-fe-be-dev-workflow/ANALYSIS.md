# ANALYSIS: 프론트엔드/백엔드 개발 워크플로우 체계화

> 작성일: 2026-03-22 | 참조: TASK.md
> 갱신: 2026-03-22 — 대화 중 도출된 인사이트 최종 반영

---

## 1. 핵심 발견 사항

### 1-1. 단계별 역할 재정의

| 단계 | 역할 | 커뮤니티 스킬 필요? |
|------|------|------------------|
| **ANALYSIS** | 프로젝트 이해 + 기술 조사 + tech-context.json 생성 | context7 (최신 문서), docs/ 참조 |
| **PLAN** | 구현 설계 — 모든 기술/보안 결정이 여기서 완결. execution-plan.json 생성 | ✅ 커뮤니티 스킬 참조 + 보안 설계 |
| **EXECUTE** | PLAN대로 코드 작성 — 새로운 판단 안 함 | ❌ 불필요 (PLAN에 이미 반영됨) |
| **TEST** | 코드 검증 (기능 + 보안) | 스모크 테스트, code-review, security-best-practices |

### 1-2. execute-guide.md = 워커의 행동 규범

execute-guide.md가 정의하는 것:

| 항목 | 내용 |
|------|------|
| **입력 파악** | 무슨 파일을 읽어서 작업 내용을 파악할 것인가 |
| **실행 절차** | 어떤 순서로 코드를 작성할 것인가 |
| **진행 추적** | Step 완료 시 체크리스트/STATE.md 갱신 |
| **금지 행동** | PLAN에 없는 것 임의 추가/변경 금지, 다른 영역 침범 금지 |
| **가드레일** | 놓친 것 발견 시 판단 기준 (멈추고 보고 vs 진행 후 보고) |
| **보안 가드레일** | 실행 중 보안 위반 감지 시 즉시 중단 |
| **완료 보고** | 보고 형식, 포함 내용 |

들어가면 안 되는 것: FE/BE 디스패치 로직(→ modes/), 기술 스택별 구현 방법(→ PLAN), 커뮤니티 스킬 참조(→ PLAN)

현재 상태 vs 필요 조치:

| 항목 | 현재 | 필요 |
|------|------|------|
| 입력 파악 | ✅ 있음 | execution-plan.json 기반으로 갱신 |
| 실행 절차 | ✅ 있음 | 유지 |
| 진행 추적 | ✅ 있음 | JSON 기반으로 갱신 |
| 금지 행동 | ❌ 없음 | **추가 필요** |
| 가드레일 | ⚠️ 블로커 처리만 | **보강 필요** (판단 기준 추가) |
| 보안 가드레일 | ❌ 없음 | **추가 필요** |
| 완료 보고 | ✅ 있음 | 유지 |

금지 행동 (신규):
- PLAN에 명시되지 않은 파일을 변경하지 않는다
- PLAN의 설계를 임의로 변경하지 않는다 (더 나은 방법이 있어도 멈추고 보고)
- 다른 영역(FE가 BE, BE가 FE)의 코드를 변경하지 않는다
- 테스트/린트 통과를 위해 기존 코드를 수정하지 않는다 (보고)

가드레일 판단 기준 (신규):
- **즉시 멈추고 보고**: PLAN과 실제 코드 불일치, 예상 못한 의존성, 보안 이슈
- **진행 후 보고**: 사소한 네이밍 차이, PLAN보다 단순한 구현 가능, deprecated 경고

보안 가드레일 (신규):
- 하드코딩된 시크릿/인증 정보 발견 시 즉시 중단
- .env 파일에 들어가야 할 값이 소스에 있으면 즉시 중단
- SQL 직접 조합 (injection 위험) 발견 시 즉시 중단

### 1-3. FE/BE 병렬 서브에이전트 필수화

현재: 단순 모드(순차) / 복잡 모드(Part C 기반 선택적)
변경: 단일 영역(순차) / 복수 영역(FE/BE 필수 병렬) / 영역 내 병렬(독립 Step)

FE/BE 병렬 디스패치 로직은 **modes/dev-full.md, modes/dev-short.md** (오케스트레이터 파이프라인)에 추가. execute-guide.md에는 넣지 않음 (워커 가이드이므로).

### 1-4. ui-designer를 FE UI 구현의 단일 진입점으로

| 작업 | 현재 | 목표 |
|------|------|------|
| wireframe.md → 새 프로젝트 | ✅ ui-designer (scaffold) | ✅ 동일 |
| 기존 프로젝트에 화면 추가/수정 | ❌ dtp-dev-agent 직접 | ✅ ui-designer (plan-driven 모드) |

add/modify를 따로 나누지 않음. **plan-driven 모드** 하나로 통일:
- 입력: execution-plan.json의 해당 화면 screen 객체
- 신규든 수정이든 PLAN이 결정한 대로 실행
- ui-designer가 자기 패턴(화면 유형별) + 규칙(shadcn Critical Rules) 적용

### 1-5. PLAN이 만드는 execution-plan.json

PLAN 단계에서 마크다운 체크리스트 대신 **구조화된 JSON**을 생성:

```json
{
  "frontend": {
    "screens": [
      {
        "id": "SCR-001",
        "screen": "사용자 프로필 페이지",
        "path": "app/profile/page.tsx",
        "action": "new",
        "type": "detail",
        "ui_work": { "layout": "...", "components": [...], "interactions": [...] },
        "api_work": { "endpoints": [...], "data_binding": {...} }
      }
    ]
  },
  "backend": {
    "layers": [
      { "layer": "model", "changes": [...] },
      { "layer": "dto", "changes": [...] },
      { "layer": "service", "changes": [...] },
      { "layer": "router", "changes": [...] }
    ]
  },
  "common": [...]
}
```

EXECUTE 흐름: 공통 먼저 → [FE 서브에이전트 + BE 서브에이전트 병렬] → 테스트

### 1-6. 2단계 보안 검토

| 시점 | 검토 내용 | 스킬 |
|------|----------|------|
| **PLAN** (설계 보안) | 인증/인가 방식 결정, 입력 검증 위치, 시크릿 관리 전략, OWASP top 10 설계 수준 방지 | openai/security-best-practices |
| **TEST** (코드 보안) | SQL injection, XSS, 하드코딩 시크릿, access control 패턴 매칭, .gitignore 검증 | openai/security-best-practices + getsentry/code-review |

PLAN에서 **설계 수준 보안** 잡고, TEST에서 **코드 수준 보안** 검증. EXECUTE 워커는 보안 판단 불필요 (PLAN대로 + 가드레일만).

### 1-7. 커뮤니티 스킬/MCP 연결 경로 부재 (근본 문제)

현재 워커가 외부 지식을 참조하는 경로가 **0개**. 이번 태스크에서 해결:
- ANALYSIS: dev-tools-registry.md 참조 → tech-context.json 생성
- PLAN: tech-context.json의 스킬 참조 → 설계 결정 반영 + 보안 검토
- EXECUTE: PLAN대로 실행 (FE는 ui-designer 호출)
- TEST: 스모크 테스트 + code-review + security-best-practices

---

## 2. 방향 결정

하이브리드: 가이드 직접 수정 + tech-context.json + dev-tools-registry + execution-plan.json

| 구성요소 | 역할 |
|---------|------|
| **dev-tools-registry.md** | 기술 스택 → 스킬/MCP 매핑 (ANALYSIS 워커가 참조) |
| **tech-context.json** | ANALYSIS에서 생성 → PLAN에서 소비 (프로젝트 기술 컨텍스트) |
| **execution-plan.json** | PLAN에서 생성 → EXECUTE에서 소비 (구조화된 실행 계획) |
| **analysis-guide.md** | 0단계(docs/+opi) + context7 의무 + tech-context.json 생성 |
| **plan-guide.md** | 스킬 참조 설계 + 보안 설계 + execution-plan.json 생성 |
| **execute-guide.md** | 행동 규범 (금지 행동, 가드레일, 보안 가드레일) |
| **modes/*.md** | FE/BE 병렬 디스패치 (오케스트레이터 로직) |
| **ui-designer SKILL.md** | plan-driven 모드 추가 (FE UI 구현 단일 진입점) |

---

## 3. 구현 범위 (확정)

| # | 파일 | 유형 | 내용 | ROI |
|---|------|------|------|-----|
| 1 | `references/dev-tools-registry.md` | 신규 | 기술 스택 → 스킬/MCP 매핑 | 높음 |
| 2 | `references/analysis-guide.md` | 수정 | 0단계(docs/+opi) + context7 의무 + 실데이터 샘플링 + tech-context.json 생성 | 높음 |
| 3 | `references/plan-guide.md` | 수정 | tech-context.json 소비 + 보안 설계 + execution-plan.json 생성 규칙 | 높음 |
| 4 | `references/execute-guide.md` | 수정 | 금지 행동 + 가드레일 + 보안 가드레일 추가 (기술/디스패치 내용 없음) | 높음 |
| 5 | `skills/ui-designer/SKILL.md` | 수정 | plan-driven 모드 추가 (execution-plan.json screen 입력) | 높음 |
| 6 | `agents/dtp-dev-test-agent/AGENT.md` | 수정 | 스모크 테스트 + code-review + security-best-practices 연계 | 높음 |
| 7 | `SKILL.md` (dev-task-pilot) | 수정 | 산출물에 tech-context.json, execution-plan.json 추가 | 중간 |
| 8 | `modes/dev-full.md` | 수정 | FE/BE 병렬 디스패치 + execution-plan.json 기반 워커 프롬프트 | 중간 |
| 9 | `modes/dev-short.md` | 수정 | Short에서도 execution-plan.json 생성/참조 + 병렬 디스패치 | 중간 |

---

## 4. 제약/리스크

| 리스크 | 심각도 | 대응 |
|--------|--------|------|
| ui-designer plan-driven 모드 설계 복잡도 | 중간 | scaffold의 Phase 4 패턴 재활용 |
| tech-context.json 기술 스택 자동 판별 실패 | 낮음 | TASK.md "적용 도구" 섹션으로 사용자 확인 |
| ui-designer scaffold P0 (5화면 통합, 프로덕션 Next.js) | 중간 | 이번에 plan-driven 모드 우선, scaffold P0은 별도 태스크 |
| FE/BE 병렬 실행 시 공유 파일 충돌 | 낮음 | execution-plan.json의 common을 먼저 실행 |
| execution-plan.json ↔ 기존 마크다운 PLAN.md 공존 | 낮음 | JSON이 실행 계획, PLAN.md가 설계 설명 — 역할 분리 |
| 보안 스킬(security-best-practices) 호출 시 토큰 증가 | 낮음 | PLAN에서는 핵심 체크리스트만, TEST에서 전수 검사 |
