# PLAN: 전문 개발 에이전트 시스템 설계

> 작성일: 2026-04-15
> 입력: TASK.md
> 출력: PLAN.md

## 1. 현황 조사

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `agents/opal-task-agent/AGENT.md` | 범용 워커 에이전트 (폴백 대상) | 이동 (→ `opal/agents/`) |
| `agents/opal-task-qa-agent/AGENT.md` | 범용 QA 워커 (기존 유지) | 이동 (→ `opal/agents/`) |
| `agents/op-dev-test-agent/AGENT.md` | 테스트 워커 (강화 대상) | 이동 + 리네이밍 (→ `opal/agents/opal-test-agent/`) |
| `agents/opal-task-action-agent/AGENT.md` | 액션 에이전트 (변경 영향) | 이동 (→ `opal/agents/`) |
| `agents/wtm-agent/AGENT.md` | 웹→마크다운 (OPAL 무관) | 변경 없음 (agents/ 유지) |
| `opal/agents/opal-sdd-action-agent/AGENT.md` | SDD 액션 에이전트 | 변경 없음 (이미 opal/agents/) |
| `opal/core/references/agents.md` | 에이전트 레지스트리 | 수정 (전문 에이전트 + 매핑 테이블) |
| `opal/core/references/opal-pm.md` | PM 행동 프로세스 | 수정 (§3, §4, §6, §10 신설) |
| `opal/skills/op-dev-plan/SKILL.md` | PLAN 스킬 | 수정 (agent 필드 + docs/ 갱신 규칙) |
| `opal/skills/op-dev-plan/references/plan-guide.md` | PLAN 가이드 | 수정 (Step 형식에 agent 필드) |
| `opal/skills/op-dev-execute/SKILL.md` | EXECUTE 스킬 | 수정 (실행 주체 갱신) |
| `opal/skills/op-dev-execute/personas/frontend-engineer.md` | FE 페르소나 (흡수 대상) | 변경 없음 (유지, 폴백용) |
| `opal/skills/op-dev-execute/personas/backend-engineer.md` | BE 페르소나 (흡수 대상) | 변경 없음 (유지, 폴백용) |
| `opal/skills/op-dev-analysis/SKILL.md` | ANALYSIS 스킬 | 수정 (실행 주체 갱신) |
| `opal/skills/op-dev-test-scenario/SKILL.md` | TEST-SCENARIO 스킬 | 수정 (실행 주체 갱신) |
| `opal/skills/op-task-execute/SKILL.md` | 범용 EXECUTE 스킬 | 수정 (실행 주체 갱신) |
| `scripts/install-mac.sh` | 설치 스크립트 | 수정 (에이전트 소스 경로 변경) |
| `docs/CONVENTIONS.md` | 코드 컨벤션 | 수정 (에이전트 경로 규칙 갱신) |
| `docs/ARCHITECTURE.md` | 시스템 아키텍처 | 수정 (서브에이전트 다이어그램 갱신) |

### 현재 상태

**에이전트 구성**: 현재 5개 에이전트(opal-task-agent, opal-task-qa-agent, op-dev-test-agent, opal-task-action-agent, wtm-agent)가 `agents/`에 있고, opal-sdd-action-agent만 `opal/agents/`에 있다. OPAL 전용 에이전트와 범용 에이전트가 같은 디렉토리에 혼재.

**PM 디스패치**: `opal-pm.md` §3은 5단계(문서 테이블 확인 → 문서 선별 → Read+핵심 제약 추출 → 종속 관계 확인 → 영구 기준 판단)로 구성되며, 에이전트 선택/슬라이싱 로직이 없다. 현재는 opal-task-agent에 전체 문서를 주입하는 방식.

**op-dev-plan SKILL.md**: v2.0 기능 중심 구조. §4.2 실행 체크리스트의 Step 형식에 `소속 기능`, `파일`, `작업 내용`, `완료 기준`, `테스트`, `실행 방법`, `의존` 필드가 있다. `영역` 필드와 `agent` 필드는 없다. plan-guide.md의 Step 형식도 동일.

**op-dev-execute SKILL.md**: 실행 주체가 `opal-task-agent 또는 dtp-wireframe-ui-agent`로 고정 기재. FE/BE 페르소나 전환을 스킬 내부에서 수행.

**설치 스크립트**: `scripts/install-mac.sh`는 `$FRAMEWORK_ROOT/agents/` 디렉토리에서만 에이전트를 읽어 `~/.opal/agents/`로 설치. `opal/agents/`는 설치 대상에 포함되지 않음. opal-sdd-action-agent가 `opal/agents/`에 있지만 install 스크립트에서 누락되어 있는 상태.

**agents.md**: "opal-pilot 에이전트" 섹션에 4개 에이전트 등록. "전문 에이전트" 개념 없음. 매핑 테이블 없음. 에이전트 추가 가이드는 형식 예시만 있음.

**CONVENTIONS.md 에이전트 경로**: 에이전트 폴더 네이밍만 정의(`{대상 워크플로우}-{역할}`). 소스 경로 규칙(`opal/agents/`)은 미정의.

### 영향 범위

1. **오케스트레이터**: opal-pilot-dev, opal-pilot-dev-short, opal-pilot-project — 직접 변경은 없으나, PM 디스패치 로직 변경(opal-pm.md)을 통해 새 에이전트로 라우팅됨
2. **opal-task-action-agent**: 내부에서 opal-task-agent, opal-task-qa-agent, op-dev-test-agent를 디스패치 — 리네이밍(op-dev-test-agent → opal-test-agent) 영향. 단, 이번 태스크에서는 AGENT.md 내 참조만 갱신 (oppd Phase 3에서 사용하는 에이전트명)
3. **기존 persona 파일**: 삭제하지 않고 유지 — opal-task-agent 폴백 시 기존대로 동작
4. **pilot SKILL.md**: 파이프라인 구조(단계 정의, Gate 순서) 변경하지 않음. 에이전트 선택은 PM이 수행
5. **설치 배포**: install-mac.sh의 에이전트 소스 경로가 `agents/` → `opal/agents/`로 변경되면, 기존 `agents/`에 남은 wtm-agent만 별도 처리 필요

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 |
|---|----------|------|
| N1 | `opal/agents/opal-fe-agent/AGENT.md` | 프론트엔드 전문 워커 에이전트 |
| N2 | `opal/agents/opal-be-agent/AGENT.md` | 백엔드 전문 워커 에이전트 |
| N3 | `opal/agents/opal-plan-agent/AGENT.md` | PLAN 단계 전문 워커 에이전트 |
| N4 | `opal/agents/opal-test-agent/AGENT.md` | 테스트 전문 워커 에이전트 (op-dev-test-agent 리네이밍+강화) |
| N5 | `opal/agents/opal-planning-agent/AGENT.md` | 서비스 기획 전문 워커 에이전트 (opwt 파이프라인) |
| N6 | `opal/agents/opal-db-agent/AGENT.md` | DB 모델 설계+구현 전문 워커 에이전트 |

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| M1 | `opal/core/references/agents.md` | 전문 에이전트 섹션 + 매핑 테이블 + 에이전트 추가 가이드 + 폴백 규칙 + 탐색 경로 갱신 |
| M2 | `opal/core/references/opal-pm.md` | §3에 Step 0/6/7 추가, §4에 영역 침범+인터페이스+docs/ 무효화 체크, §6 에이전트별 문서 매핑, §10 통합 조율 신설 |
| M3 | `opal/skills/op-dev-plan/SKILL.md` | Step 형식에 `영역`+`agent` 필드 추가, docs/ 갱신 Step 자동 생성 규칙 추가 |
| M4 | `opal/skills/op-dev-plan/references/plan-guide.md` | Step 형식에 `영역`+`agent` 필드 추가, docs/ 갱신 Step 규칙 추가 |
| M5 | `opal/skills/op-dev-execute/SKILL.md` | 실행 주체에 "전문 에이전트 또는 opal-task-agent (폴백)" 표기 |
| M6 | `opal/skills/op-dev-analysis/SKILL.md` | 실행 주체에 "전문 에이전트 또는 opal-task-agent (폴백)" 표기 |
| M7 | `opal/skills/op-dev-test-scenario/SKILL.md` | 실행 주체에 opal-task-agent 참조 유지 (115에서 PLAN에 통합됨) |
| M8 | `opal/skills/op-task-execute/SKILL.md` | 실행 주체에 "전문 에이전트 또는 opal-task-agent (폴백)" 표기 |
| M9 | `agents/opal-task-agent/AGENT.md` | → `opal/agents/opal-task-agent/AGENT.md`로 이동 |
| M10 | `agents/opal-task-qa-agent/AGENT.md` | → `opal/agents/opal-task-qa-agent/AGENT.md`로 이동 |
| M11 | `agents/op-dev-test-agent/AGENT.md` | → `opal/agents/opal-test-agent/AGENT.md`로 이동+리네이밍 (기존 내용을 opal-test-agent가 흡수) |
| M12 | `agents/opal-task-action-agent/AGENT.md` | → `opal/agents/opal-task-action-agent/AGENT.md`로 이동 + 내부 op-dev-test-agent 참조를 opal-test-agent로 갱신 |
| M13 | `scripts/install-mac.sh` | 에이전트 소스 경로를 `opal/agents/`로 변경 + `agents/` 범용(wtm-agent) 별도 처리 |
| M14 | `docs/CONVENTIONS.md` | 에이전트 소스 경로 규칙 (`opal/agents/`) 추가, 전문 에이전트 네이밍 체계 추가 |
| M15 | `docs/ARCHITECTURE.md` | 서브에이전트 다이어그램에 전문 에이전트 4종 추가, 구성도 갱신 |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| D1 | `agents/opal-task-agent/AGENT.md` | `opal/agents/`로 이동 후 원본 삭제 |
| D2 | `agents/opal-task-qa-agent/AGENT.md` | `opal/agents/`로 이동 후 원본 삭제 |
| D3 | `agents/op-dev-test-agent/AGENT.md` | `opal/agents/opal-test-agent/`로 이동+리네이밍 후 원본 삭제 |
| D4 | `agents/opal-task-action-agent/AGENT.md` | `opal/agents/`로 이동 후 원본 삭제 |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | 전문 에이전트 AGENT.md 생성 (R-1~R-4) | N1~N4 | 중 |
| 2 | agents.md 레지스트리 갱신 (R-13) | M1 | 중 |
| 3 | op-dev-plan SKILL.md + plan-guide.md 갱신 (R-5, R-6) | M3, M4 | 중 |
| 4 | opal-pm.md 갱신 (R-7~R-11) | M2 | 높음 |
| 5 | 관련 스킬 실행 주체 갱신 (R-12) | M5~M8 | 낮음 |
| 6 | 에이전트 디렉토리 이동 (R-14) | M9~M12, D1~D4, M13, M14, M15 | 중 |

### 핵심 설계

#### N1. opal-fe-agent AGENT.md

**규격**: YAML frontmatter (`name`, `description`, `model: standard`, `icon`) + 본문

**핵심 내용**:
- FE 전문 지식 내장: 기존 `personas/frontend-engineer.md`의 5원칙 + 3행동규칙을 흡수·확장
  - React 컴포넌트 설계 (단일 책임, 재렌더링 방지, Suspense/lazy)
  - shadcn/ui Critical Rules (FieldGroup/Field 폼 구조, gap 레이아웃, 컴포넌트 조회 후 구현)
  - 접근성(a11y) 기본 준수
  - Tailwind CSS 활용 규칙
  - 반응형 레이아웃 기본 적용
- 자체 로드 문서: `FRONTEND.md`, `CONVENTIONS.md` (FE 섹션만)
- 금지 규칙: BE 파일(`backend/`, `server/`, `api/` 등) 수정 금지
- MCP/스킬 활용: shadcn MCP, context7, ui-designer 스킬, vercel-labs 커뮤니티 스킬
- 실행 프로세스: opal-task-agent와 동일 골격 (스킬 Read → 컨텍스트 로드 → 프로세스 수행 → 결과 반환) + FE 도메인 문서만 로드
- 결과 반환 형식: opal-task-agent와 동일 JSON

#### N2. opal-be-agent AGENT.md

**규격**: 동일 (model: standard)

**핵심 내용**:
- BE 전문 지식 내장: 기존 `personas/backend-engineer.md`의 5원칙 + 3행동규칙을 흡수·확장
  - RESTful API 설계 원칙
  - 입력 검증 + OWASP Top 10 방어
  - 모델 → DTO → 서비스 → 라우터 레이어 구조
  - 쿼리 N+1 방지, ORM 패턴 준수
  - 환경변수 시크릿 관리
  - 에러 핸들링 레이어별 분리
- 자체 로드 문서: `BACKEND.md`, `BE-FRAMEWORK.md`, `CONVENTIONS.md` (BE 섹션만)
- 금지 규칙: FE 파일(`frontend/`, `src/pages/`, `src/components/` 등) 수정 금지
- MCP/스킬 활용: context7, trailofbits/modern-python 커뮤니티 스킬
- 실행 프로세스 + 결과 반환: opal-task-agent와 동일 골격

#### N3. opal-plan-agent AGENT.md

**규격**: YAML frontmatter (`model: advanced` 고정)

**핵심 내용**:
- PLAN 단계 전문: 코드 분석 + 기능 중심 설계 + 테스트 시나리오 통합
- 전체 docs/ 읽기 권한 (도메인 제한 없음)
- 에이전트 라우팅: "PM이 전달한 전문 에이전트 매핑 테이블을 참조하여 §4.2 실행 체크리스트의 각 Step에 agent 필드를 배정한다"
- 매핑 테이블 없으면 agent 필드 생략 (폴백: PM이 직접 판단)
- docs/ 갱신 Step: 코드 변경이 docs/ 내용에 영향을 미치는 경우 자동 추가
- 실행 프로세스: 스킬(op-dev-plan) Read → 전체 프로젝트 컨텍스트 로드 → 기능 중심 PLAN + TEST-SCENARIO 작성 → 결과 반환
- 기존 op-dev-plan SKILL.md 프로세스를 그대로 따름 (에이전트가 스킬을 대체하는 것이 아님)

#### N4. opal-test-agent AGENT.md

**규격**: YAML frontmatter (`model: standard`, `name: opal-test-agent`)

**핵심 내용**:
- 기존 op-dev-test-agent의 전체 기능 유지 (TEST-SCENARIO.md 기반 동적 검증)
- 3가지 테스트 모드:
  - **BE mode**: BACKEND.md + BE-FRAMEWORK.md 로드, API/서비스/DB 테스트 집중
  - **FE mode**: FRONTEND.md 로드, 컴포넌트 렌더링/접근성/E2E 테스트 집중
  - **E2E mode**: 전체 docs/ 로드, 통합 시나리오 검증
- 모드 결정: PM이 디스패치 시 mode 파라미터로 지정 (기본값: E2E)
- 기존 코드: getsentry/code-review 커뮤니티 스킬 활용 유지
- 결과 반환 형식: 기존 op-dev-test-agent와 동일

#### N5. opal-planning-agent AGENT.md

**규격**: YAML frontmatter (`model: advanced`)

**핵심 내용**:
- 서비스 기획 전문: PRD, TRD, 서비스 정책서, IA, WBS, 외부 API 명세서, 기능도, 순서도, 운영 정책서
- 문서 형식: MD 기본 + 엑셀 가능 (xlsx-tool 활용)
- opwt 파이프라인의 EXECUTE 단계 워커로 투입
- opal-doc-standard 참조하여 문서 작성
- 자체 로드 문서: 기존 기획 산출물, 와이어프레임 등 외부 참조 산출물
- 실행 프로세스: network-guide.md의 워커 프롬프트를 따르되, 기획 전문 지식 내장
- 결과 반환 형식: opal-task-agent와 동일 JSON

#### N6. opal-db-agent AGENT.md

**규격**: YAML frontmatter (`model: standard`)

**핵심 내용**:
- DB 모델 설계+구현 전문: 개념 모델링 → 논리 모델링 → 물리 모델링 → 마이그레이션
- 출력 형식: MD(설계 문서) + DBML(스키마 정의) + SQL(마이그레이션)
- 표준사전 참조: 엑셀 파일(xlsx-tool)로 표준사전을 읽어 네이밍/타입 규칙 준수
- 자체 로드 문서: DB 설계 문서, 표준사전(엑셀), 기획서(참조)
- PLAN 단계: 기획서 기반 개념/논리/물리 모델 설계
- EXECUTE 단계: 설계 기반 마이그레이션 코드 생성 (Alembic, Django migration 등)
- 금지 규칙: FE 파일 수정 금지
- 실행 프로세스 + 결과 반환: opal-task-agent와 동일 골격

#### M1. agents.md 갱신

**추가 섹션**: "전문 에이전트 (Specialist)" — 기존 "opal-pilot 에이전트" 섹션 아래에 추가

**매핑 테이블**:
```markdown
## 전문 에이전트 매핑 테이블

| 에이전트 | 단계 | 영역 | model | 자체 로드 문서 |
|----------|------|------|-------|--------------|
| opal-plan-agent | PLAN | 공통 | advanced | 전체 docs/ |
| opal-fe-agent | EXECUTE | FE | standard | FRONTEND.md, CONVENTIONS.md (FE) |
| opal-be-agent | EXECUTE | BE | standard | BACKEND.md, BE-FRAMEWORK.md, CONVENTIONS.md (BE) |
| opal-db-agent | PLAN, EXECUTE | DB | standard | DB 설계 문서, 표준사전(엑셀) |
| opal-planning-agent | EXECUTE | 기획 | advanced | 기획 산출물, 와이어프레임 등 |
| opal-test-agent | TEST | 공통 | standard | ARCHITECTURE.md (테스트 섹션) |
```

**에이전트 추가 가이드**: 프레임워크 레벨(opal/agents/ → agents.md 등록 → install) + 프로젝트 레벨({프로젝트}/.opal/agents/)

**폴백 규칙 3단계**:
1. agents.md에 전문 에이전트 섹션 없음 → 기존 방식 (opal-task-agent)
2. 매핑 테이블에 해당 단계/영역 없음 → 해당 단계는 기존 방식
3. 매핑 있음 → 전문 에이전트 사용

**프로젝트별 에이전트 오버라이드**: 탐색 경로를 기존 2단계 유지 (`{프로젝트}/.opal/agents/` → `~/.opal/agents/`)

**기존 "opal-pilot 에이전트" 섹션 갱신**: op-dev-test-agent 항목을 opal-test-agent로 리네이밍, 에이전트 경로를 `opal/agents/`로 표기

#### M2. opal-pm.md 갱신

**§3 디스패치 전 프로세스** — 기존 5단계 유지 + 3단계 추가:

- **Step 0. 에이전트 선택** (기존 Step 1~5 앞에 삽입):
  1. agents.md의 전문 에이전트 매핑 테이블 Read
  2. 현재 단계 + 영역 → 에이전트 선택
  3. 전문 에이전트 없으면 opal-task-agent 폴백
  4. PLAN 디스패치 시: 매핑 테이블을 함께 주입 (agent 배정 위임)

- **Step 6. 실행 라우팅** (기존 Step 5 뒤에 추가):
  1. PLAN.md §4 실행 체크리스트의 agent 필드 참조
  2. 의존 그래프 기반 Batch 구성
  3. Batch 내 독립 → 병렬 / 의존 → 순차

- **Step 7. 컨텍스트 슬라이싱** (Step 6 뒤에 추가):
  - PLAN.md §3 해당 F-NNN 섹션만 추출
  - 도메인 문서 (FE용 / BE용 분리)
  - TEST-SCENARIO 해당 TS-ID만
  - 선행 Batch changed_files (통합 Step용)

**§4 PM 검토 게이트** — 기존 8항목 유지 + 추가:
- 영역 침범 체크: FE↔BE 상호 파일 수정 여부
- 인터페이스 정합성: Batch 간 BE API ↔ FE 호출 일치
- docs/ 무효화 체크: changed_files가 docs/ 내용을 무효화하지 않는가
- Fail 시: 해당 전문 에이전트에 재지시 (기존은 opal-task-agent에)

**§6 참조 문서 전달 의무** — 에이전트별 문서 매핑 테이블 추가:
| 에이전트 | 필수 문서 | 선택 문서 |
|----------|----------|----------|
| opal-plan-agent | PROJECT, ARCHITECTURE, CONVENTIONS | FRONTEND, BACKEND, 도메인 전체 |
| opal-fe-agent | CONVENTIONS (FE), FRONTEND | PROJECT (요약만) |
| opal-be-agent | CONVENTIONS (BE), BACKEND, BE-FRAMEWORK | PROJECT (요약만) |
| opal-test-agent | ARCHITECTURE (테스트 섹션) | 해당 도메인 문서 |
| opal-task-agent (폴백) | 기존 전체 문서 전달 방식 유지 | — |

**§10 통합 조율** (신규 섹션):
1. 인터페이스 계약 관리 — BE API 스펙 → FE 전달, 공통 타입 동기화
2. Batch 간 핸드오프 — changed_files 수집 → 후속 Batch 주입, 실패 시 중단 판단
3. 충돌 해소 — 동일 파일 양쪽 수정 시 순차 전환, 공통 영역 선행 결과 반영

#### M3. op-dev-plan SKILL.md 갱신

**§4.2 실행 체크리스트 Step 형식에 `영역` + `agent` 필드 추가**:

```markdown
#### Step N: {작업 제목}
- [ ] 완료
- **소속 기능**: F-NNN
- **영역**: {FE / BE / DB / 환경 / 배치 / 공통 / 문서}  ← 신규
- **agent**: {에이전트명}                                  ← 신규
- **파일**: {대상 파일 경로}
- **작업 내용**: {구체적 구현 내용}
- **완료 기준**: {검증 가능한 완료 조건}
- **테스트**: {TS-ID 또는 검증 방법}
- **실행 방법**: {direct / sub-agent}
- **의존**: {선행 Step 번호 또는 "없음"}
```

**영역 → agent 매핑 규칙** (PLAN.md 출력 형식 섹션에 추가):

| 영역 | 기본 agent | 비고 |
|------|-----------|------|
| FE | opal-fe-agent | 프론트엔드 전문 |
| BE | opal-be-agent | 백엔드 전문 |
| DB | opal-be-agent | BE에 포함 (향후 opal-db-agent 분리 가능) |
| 환경 | opal-task-agent | 범용 |
| 배치 | opal-task-agent | 범용 |
| 공통 | opal-task-agent | 범용 (PM이 영향 범위에 따라 오버라이드 가능) |
| 문서 | PM 직접 | docs/ 갱신 Step |

**agent 필드 배정 규칙**:
- PM이 디스패치 시 전문 에이전트 매핑 테이블을 주입하면, 이를 참조하여 배정
- 매핑 테이블이 없으면 agent 필드 생략 (폴백: PM이 직접 판단)

**docs/ 갱신 Step 자동 생성 규칙** (Step 10 전에 새 규칙 섹션 추가):
- 코드 변경이 docs/ 문서 내용에 영향을 미치는 경우, 실행 체크리스트에 docs/ 갱신 Step을 자동 추가
- 영역: `문서`, agent: `PM 직접`
- 의존: 해당 코드 변경 Step 완료 후
- 갱신 대상 판단 기준:
  - 새 API 엔드포인트 → BACKEND.md
  - 새 컴포넌트/페이지 → FRONTEND.md
  - 구조 변경 → ARCHITECTURE.md
  - 새 패턴/규칙 → CONVENTIONS.md

#### M4. plan-guide.md 갱신

SKILL.md와 동일한 변경을 plan-guide.md의 "4.2 실행 체크리스트" Step 형식에 적용:
- `영역` 필드 추가 (6영역 + 문서)
- `agent` 필드 추가
- 영역 → agent 매핑 테이블 추가
- docs/ 갱신 Step 규칙 추가

Phase 그룹핑(4.1)에 agent 정보 반영:
```markdown
| Phase | 기능 | Step | agent | 실행 | 비고 |
```

#### M5~M8. 관련 스킬 실행 주체 갱신

각 SKILL.md의 "실행 컨텍스트" 섹션에서 실행 주체를 갱신:

**변경 전**:
```
- **실행 주체**: 워커 에이전트 (opal-task-agent)
```

**변경 후**:
```
- **실행 주체**: 워커 에이전트 — PM이 agents.md 매핑 테이블 또는 PLAN.md agent 필드에 따라 적합한 에이전트를 선택한다 (폴백: opal-task-agent)
```

대상 스킬: op-dev-execute (M5), op-dev-analysis (M6), op-dev-test-scenario (M7), op-task-execute (M8)

op-dev-test-scenario (M7)는 115에서 PLAN에 통합됐으므로, opal-task-agent 참조는 유지하되 비고로 "opal-plan-agent가 PLAN 통합 작성 시 함께 수행"을 추가

#### M9~M12, D1~D4. 에이전트 디렉토리 이동

**이동 매핑**:

| 원본 | 이동 후 | 비고 |
|------|---------|------|
| `agents/opal-task-agent/` | `opal/agents/opal-task-agent/` | 내용 변경 없음 |
| `agents/opal-task-qa-agent/` | `opal/agents/opal-task-qa-agent/` | 내용 변경 없음 |
| `agents/op-dev-test-agent/` | `opal/agents/opal-test-agent/` | 리네이밍 + 강화 (N4가 대체) |
| `agents/opal-task-action-agent/` | `opal/agents/opal-task-action-agent/` | 내부 op-dev-test-agent → opal-test-agent 참조 갱신 |
| `agents/wtm-agent/` | (유지) | OPAL 무관, 이동 안 함 |

**M12 opal-task-action-agent 내부 참조 갱신**: `op-dev-test-agent` → `opal-test-agent` (6단계 TEST의 디스패치 대상명)

#### M13. install-mac.sh 갱신

에이전트 소스 경로 변경:
```bash
# 현재
"$FRAMEWORK_ROOT/agents"

# 변경 후
"$FRAMEWORK_ROOT/opal/agents"
```

wtm-agent는 `agents/`에 남으므로, 별도 처리:
```bash
# OPAL 에이전트 (opal/agents/ → ~/.opal/agents/)
for agent_dir in "$FRAMEWORK_ROOT/opal/agents"/*/; do ...

# 범용 에이전트 (agents/ → ~/.opal/agents/) — OPAL 무관 에이전트
for agent_dir in "$FRAMEWORK_ROOT/agents"/*/; do ...
```

#### M14. CONVENTIONS.md 갱신

에이전트 소스 경로 규칙 추가:
- OPAL 전용 에이전트: `opal/agents/{agent-name}/AGENT.md`
- 범용 에이전트 (OPAL 무관): `agents/{agent-name}/AGENT.md`
- 전문 에이전트 네이밍: `opal-{domain}-agent` (예: opal-fe-agent, opal-be-agent)

#### M15. ARCHITECTURE.md 갱신

서브에이전트 다이어그램에 전문 에이전트 추가:
```
│  ├─ opal-task-agent: 범용 워커 (폴백)
│  ├─ opal-plan-agent: PLAN 단계 전문 (advanced)     ← 신규
│  ├─ opal-fe-agent: FE EXECUTE 전문                  ← 신규
│  ├─ opal-be-agent: BE EXECUTE 전문                  ← 신규
│  ├─ opal-test-agent: 테스트 전문 (도메인별 모드)     ← 강화
│  ├─ opal-task-qa-agent: QA 스킬 동적 실행
│  ├─ opal-task-action-agent: oppd Phase 3 액션 자율 실행
│  └─ wtm-agent: 웹→마크다운 변환
```

---

## 3. 실행 체크리스트

> 총 18개 Step | Phase 5개
>
> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | 1 | 1, 2, 3, 4, 5, 6 | 병렬 | 독립 에이전트 AGENT.md 6종 생성 |
> | 2 | 7, 8 | 병렬 | agents.md 레지스트리 + op-dev-plan SKILL.md (독립 파일) |
> | 3 | 9, 10 | 병렬 | plan-guide.md + opal-pm.md (독립 파일) |
> | 4 | 11, 12, 13, 14 | 병렬 | 관련 스킬 실행 주체 갱신 (각각 독립 파일) |
> | 5 | 15, 16, 17, 18 | 순차 | 에이전트 이동 → install.sh → CONVENTIONS → ARCHITECTURE (의존 체인) |

### Step 1: opal-fe-agent AGENT.md 생성
- [ ] 완료
- **파일**: `opal/agents/opal-fe-agent/AGENT.md`
- **작업 내용**: 프론트엔드 전문 워커 에이전트 AGENT.md 신규 작성. YAML frontmatter(name, description, model: standard, icon) + 본문(FE 전문 지식 내장, 자체 로드 문서 목록, BE 파일 수정 금지 규칙, MCP/스킬 활용 지침, 실행 프로세스, 결과 반환 형식). 기존 `personas/frontend-engineer.md`의 5원칙 + 3행동규칙을 흡수·확장.
- **완료 기준**: AGENT.md가 OPAL 에이전트 규격을 따르고, AC 4항목(규격 준수, 자체 로드 문서 명시, BE 수정 금지, MCP/스킬 지침) 모두 충족
- **테스트**: AGENT.md YAML frontmatter 파싱 가능 + 본문에 필수 섹션 존재 확인
- **의존**: 없음

### Step 2: opal-be-agent AGENT.md 생성
- [ ] 완료
- **파일**: `opal/agents/opal-be-agent/AGENT.md`
- **작업 내용**: 백엔드 전문 워커 에이전트 AGENT.md 신규 작성. YAML frontmatter(name, description, model: standard, icon) + 본문(BE 전문 지식 내장, 자체 로드 문서 목록, FE 파일 수정 금지 규칙, MCP/스킬 활용 지침, 실행 프로세스, 결과 반환 형식). 기존 `personas/backend-engineer.md`의 5원칙 + 3행동규칙을 흡수·확장.
- **완료 기준**: AGENT.md가 OPAL 에이전트 규격을 따르고, AC 4항목 모두 충족
- **테스트**: AGENT.md YAML frontmatter 파싱 가능 + 본문에 필수 섹션 존재 확인
- **의존**: 없음

### Step 3: opal-plan-agent AGENT.md 생성
- [ ] 완료
- **파일**: `opal/agents/opal-plan-agent/AGENT.md`
- **작업 내용**: PLAN 단계 전문 워커 에이전트 AGENT.md 신규 작성. YAML frontmatter(name, description, model: advanced, icon) + 본문(전체 docs/ 접근, 에이전트 라우팅 — PM이 전달한 매핑 테이블 참조하여 agent 배정, 매핑 없으면 생략, docs/ 갱신 Step 자동 추가, 실행 프로세스, 결과 반환 형식).
- **완료 기준**: AGENT.md가 OPAL 에이전트 규격을 따르고, model: advanced 명시, agent 필드 배정 규칙 명시, 매핑 테이블 없을 때 폴백 규칙 명시
- **테스트**: AGENT.md YAML frontmatter에 `model: advanced` 존재 + 본문에 agent 배정 + 매핑 테이블 참조 규칙 존재 확인
- **의존**: 없음

### Step 4: opal-test-agent AGENT.md 생성
- [ ] 완료
- **파일**: `opal/agents/opal-test-agent/AGENT.md`
- **작업 내용**: 테스트 전문 워커 에이전트 AGENT.md 신규 작성. 기존 op-dev-test-agent 전체 기능 유지 + 3가지 테스트 모드(BE mode, FE mode, E2E mode) 추가. 모드별 로딩 문서 구분. YAML frontmatter(name: opal-test-agent, description, model: standard, icon).
- **완료 기준**: 3가지 모드 정의 + 모드별 로딩 문서 구분 + 기존 TEST-SCENARIO.md 기반 동적 검증 기능 유지
- **테스트**: AGENT.md에 BE mode/FE mode/E2E mode 3섹션 존재 + 기존 실행 프로세스 유지 확인
- **의존**: 없음

### Step 5: opal-planning-agent AGENT.md 생성
- [ ] 완료
- **파일**: `opal/agents/opal-planning-agent/AGENT.md`
- **작업 내용**: 서비스 기획 전문 워커 에이전트 AGENT.md 신규 작성. YAML frontmatter(name, description, model: advanced, icon) + 본문(기획 산출물 유형 나열, 자체 로드 문서, MD 기본+엑셀 가능, opal-doc-standard 참조, 실행 프로세스, 결과 반환 형식). opwt 파이프라인의 EXECUTE 워커로 투입.
- **완료 기준**: AGENT.md가 OPAL 에이전트 규격을 따르고, 기획 산출물 유형(PRD, TRD, 정책서, IA, WBS 등)이 나열, MD+엑셀 가능 명시
- **테스트**: AGENT.md에 기획 산출물 유형 목록 존재 + model: advanced 확인
- **의존**: 없음

### Step 6: opal-db-agent AGENT.md 생성
- [ ] 완료
- **파일**: `opal/agents/opal-db-agent/AGENT.md`
- **작업 내용**: DB 모델 설계+구현 전문 워커 에이전트 AGENT.md 신규 작성. YAML frontmatter(name, description, model: standard, icon) + 본문(3단계 모델링: 개념/논리/물리, DBML 출력 지원, 표준사전 엑셀 참조, 자체 로드 문서, 마이그레이션 구현 지원, PLAN+EXECUTE 양 단계 투입 가능, 실행 프로세스, 결과 반환 형식).
- **완료 기준**: AGENT.md가 OPAL 에이전트 규격을 따르고, 3단계 모델링 명시, DBML+표준사전 참조, PLAN+EXECUTE 양 단계 투입 명시
- **테스트**: AGENT.md에 개념/논리/물리 모델링 3단계 + DBML + 표준사전 참조 존재 확인
- **의존**: 없음

### Step 7: agents.md 레지스트리 갱신
- [ ] 완료
- **파일**: `opal/core/references/agents.md`
- **작업 내용**: (1) "전문 에이전트 (Specialist)" 섹션 추가 — 6종 에이전트 상세 정보. (2) 전문 에이전트 매핑 테이블 추가 (6행). (3) 에이전트 추가 가이드 (프레임워크/프로젝트 레벨). (4) 폴백 규칙 3단계. (5) 기존 "opal-pilot 에이전트" 섹션에서 op-dev-test-agent → opal-test-agent 리네이밍. (6) 탐색 경로 유지.
- **완료 기준**: 전문 에이전트 섹션 + 매핑 테이블 + 추가 가이드 + 폴백 규칙이 존재. 기존 에이전트 정보가 보존됨
- **테스트**: agents.md에 매핑 테이블이 6행(opal-plan-agent, opal-fe-agent, opal-be-agent, opal-db-agent, opal-planning-agent, opal-test-agent) 존재 확인
- **의존**: Step 1~6 (전문 에이전트 AGENT.md 6종 생성 후 등록)

### Step 8: op-dev-plan SKILL.md 갱신
- [ ] 완료
- **파일**: `opal/skills/op-dev-plan/SKILL.md`
- **작업 내용**: (1) §4.2 실행 체크리스트 Step 형식에 `영역` + `agent` 필드 추가. (2) 영역 → agent 매핑 규칙 테이블 추가. (3) agent 필드 배정 규칙 (PM 매핑 테이블 참조, 없으면 생략). (4) docs/ 갱신 Step 자동 생성 규칙 추가. (5) 영역 태그에 `문서` 추가.
- **완료 기준**: Step 템플릿에 영역+agent 필드 포함, 매핑 테이블 존재, docs/ 갱신 규칙 존재
- **테스트**: SKILL.md Step 형식에 `**영역**`과 `**agent**` 필드 존재 확인
- **의존**: 없음

### Step 9: plan-guide.md 갱신
- [ ] 완료
- **파일**: `opal/skills/op-dev-plan/references/plan-guide.md`
- **작업 내용**: (1) 4.2 실행 체크리스트 Step 형식에 `영역` + `agent` 필드 추가. (2) 영역 → agent 매핑 테이블 추가. (3) docs/ 갱신 Step 규칙 추가. (4) 4.1 Phase 그룹핑 테이블에 agent 컬럼 추가.
- **완료 기준**: plan-guide.md의 Step 형식이 SKILL.md와 일치, Phase 테이블에 agent 컬럼 존재
- **테스트**: plan-guide.md Step 형식에 `**영역**`과 `**agent**` 필드 존재 확인
- **의존**: Step 8 (SKILL.md와 일관성 유지)

### Step 10: opal-pm.md 갱신
- [ ] 완료
- **파일**: `opal/core/references/opal-pm.md`
- **작업 내용**: (1) §3에 Step 0(에이전트 선택), Step 6(실행 라우팅), Step 7(컨텍스트 슬라이싱) 추가. (2) §4에 영역 침범 체크 + 인터페이스 정합성 + docs/ 무효화 체크 항목 추가 + Fail 시 전문 에이전트 재지시 규칙. (3) §6에 에이전트별 문서 매핑 테이블 추가. (4) §10 통합 조율 신규 섹션 추가.
- **완료 기준**: §3에 8단계(Step 0~7) 구조, §4에 신규 체크 항목 4개, §6에 매핑 테이블, §10에 3가지 역할 정의
- **테스트**: opal-pm.md에 §10 섹션 존재 + §3에 "에이전트 선택" 단계 존재 + §4에 "영역 침범" 항목 존재 확인
- **의존**: Step 7 (agents.md에 매핑 테이블이 먼저 정의되어야 §3에서 참조 가능)

### Step 11: op-dev-execute SKILL.md 실행 주체 갱신
- [ ] 완료
- **파일**: `opal/skills/op-dev-execute/SKILL.md`
- **작업 내용**: "실행 주체" 라인을 "워커 에이전트 — PM이 agents.md 매핑 테이블 또는 PLAN.md agent 필드에 따라 적합한 에이전트를 선택한다 (폴백: opal-task-agent)"로 갱신
- **완료 기준**: 실행 주체에 전문 에이전트 + 폴백 표기 존재
- **테스트**: SKILL.md에 "agents.md 매핑 테이블" 또는 "폴백: opal-task-agent" 문구 존재 확인
- **의존**: 없음

### Step 12: op-dev-analysis SKILL.md 실행 주체 갱신
- [ ] 완료
- **파일**: `opal/skills/op-dev-analysis/SKILL.md`
- **작업 내용**: Step 9와 동일한 패턴으로 실행 주체 갱신
- **완료 기준**: 실행 주체에 전문 에이전트 + 폴백 표기 존재
- **테스트**: SKILL.md에 "폴백: opal-task-agent" 문구 존재 확인
- **의존**: 없음

### Step 13: op-dev-test-scenario SKILL.md 실행 주체 갱신
- [ ] 완료
- **파일**: `opal/skills/op-dev-test-scenario/SKILL.md`
- **작업 내용**: 실행 주체 갱신 + 비고로 "opal-plan-agent가 PLAN 통합 작성 시 함께 수행 (115에서 통합)" 추가. 기존 opal-task-agent 참조는 유지.
- **완료 기준**: 실행 주체에 전문 에이전트 참조 + PLAN 통합 비고 존재
- **테스트**: SKILL.md에 "opal-plan-agent" 또는 "PLAN 통합" 문구 존재 확인
- **의존**: 없음

### Step 14: op-task-execute SKILL.md 실행 주체 갱신
- [ ] 완료
- **파일**: `opal/skills/op-task-execute/SKILL.md`
- **작업 내용**: Step 9와 동일한 패턴으로 실행 주체 갱신
- **완료 기준**: 실행 주체에 전문 에이전트 + 폴백 표기 존재
- **테스트**: SKILL.md에 "폴백: opal-task-agent" 문구 존재 확인
- **의존**: 없음

### Step 15: 에이전트 디렉토리 이동
- [ ] 완료
- **파일**: `agents/` → `opal/agents/` (4개 에이전트 이동)
- **작업 내용**: (1) `agents/opal-task-agent/` → `opal/agents/opal-task-agent/`. (2) `agents/opal-task-qa-agent/` → `opal/agents/opal-task-qa-agent/`. (3) `agents/op-dev-test-agent/` → 삭제 (opal-test-agent가 대체). (4) `agents/opal-task-action-agent/` → `opal/agents/opal-task-action-agent/` + 내부 op-dev-test-agent → opal-test-agent 참조 갱신. (5) `agents/wtm-agent/` 유지.
- **완료 기준**: 4개 에이전트가 `opal/agents/`에 존재, `agents/`에는 `wtm-agent/`만 남음, opal-task-action-agent 내부 참조가 opal-test-agent로 갱신
- **테스트**: `ls opal/agents/`에 7개 디렉토리(기존 opal-sdd-action-agent + 신규 4 + 이동 3), `ls agents/`에 wtm-agent만 존재 확인
- **의존**: Step 4 (opal-test-agent AGENT.md가 먼저 생성되어야 op-dev-test-agent 삭제 가능)
- **비고**: N5(opal-planning-agent), N6(opal-db-agent)도 이동 대상에 해당하지 않음 (신규 생성이므로 이미 opal/agents/에 존재)

### Step 16: install-mac.sh 갱신
- [ ] 완료
- **파일**: `scripts/install-mac.sh`
- **작업 내용**: 에이전트 소스 경로를 `$FRAMEWORK_ROOT/agents`에서 `$FRAMEWORK_ROOT/opal/agents`로 변경. `agents/` 디렉토리의 범용 에이전트(wtm-agent)도 함께 설치되도록 별도 루프 추가. 카운트 로직 갱신.
- **완료 기준**: OPAL 에이전트는 `opal/agents/`에서, 범용 에이전트는 `agents/`에서 설치. 두 소스 모두 `~/.opal/agents/`에 배포
- **테스트**: install-mac.sh에 `opal/agents` 경로 참조 존재 + `agents/` 폴백 루프 존재 확인
- **의존**: Step 15 (디렉토리 이동 완료 후)

### Step 17: CONVENTIONS.md 갱신
- [ ] 완료
- **파일**: `docs/CONVENTIONS.md`
- **작업 내용**: 에이전트 경로 규칙 섹션에 OPAL 전용 에이전트(`opal/agents/`) vs 범용 에이전트(`agents/`) 구분 추가. 전문 에이전트 네이밍 체계(`opal-{domain}-agent`) 추가. 에이전트 폴더 네이밍 예시 갱신.
- **완료 기준**: CONVENTIONS.md에 에이전트 소스 경로 이원 구조 명시 + 전문 에이전트 네이밍 규칙 존재
- **테스트**: CONVENTIONS.md에 `opal/agents/` 경로 규칙 존재 확인
- **의존**: Step 15 (디렉토리 구조 확정 후)

### Step 18: ARCHITECTURE.md 갱신
- [ ] 완료
- **파일**: `docs/ARCHITECTURE.md`
- **작업 내용**: 서브에이전트 다이어그램에 전문 에이전트 4종(opal-plan-agent, opal-fe-agent, opal-be-agent, opal-test-agent) 추가. "서브에이전트 5개"를 "서브에이전트 8개"로 갱신. 전문 에이전트 체계 구성도 추가.
- **완료 기준**: 다이어그램에 8개 에이전트 표기 + 전문 에이전트 4종 포함
- **테스트**: ARCHITECTURE.md에 opal-plan-agent, opal-fe-agent, opal-be-agent, opal-test-agent 4종 존재 확인
- **의존**: Step 15 (디렉토리 구조 확정 후)

---

## 4. QA 체크리스트

### 기능 테스트
- [ ] R-1: opal-fe-agent AGENT.md가 OPAL 에이전트 규격을 따르고, 자체 로드 문서(FRONTEND.md, CONVENTIONS.md FE), BE 수정 금지, MCP/스킬 지침이 포함되어 있는가
- [ ] R-2: opal-be-agent AGENT.md가 OPAL 에이전트 규격을 따르고, 자체 로드 문서(BACKEND.md, BE-FRAMEWORK.md, CONVENTIONS.md BE), FE 수정 금지, MCP/스킬 지침이 포함되어 있는가
- [ ] R-3: opal-plan-agent AGENT.md에 model: advanced, agent 배정 규칙, 매핑 테이블 참조가 명시되어 있는가
- [ ] R-4: opal-test-agent AGENT.md에 BE/FE/E2E 3가지 모드가 정의되고 모드별 로딩 문서가 구분되어 있는가
- [ ] R-5: opal-planning-agent AGENT.md에 기획 산출물 유형(PRD, TRD, 정책서, IA, WBS 등)이 나열되고, MD+엑셀 가능이 명시되어 있는가
- [ ] R-6: opal-db-agent AGENT.md에 3단계 모델링(개념/논리/물리), DBML 출력, 표준사전 참조, PLAN+EXECUTE 양 단계 투입이 명시되어 있는가
- [ ] R-7: op-dev-plan SKILL.md Step 형식에 영역+agent 필드가 포함되고, 영역→agent 매핑 테이블이 존재하는가
- [ ] R-8: op-dev-plan SKILL.md에 docs/ 갱신 Step 자동 생성 규칙이 정의되어 있는가
- [ ] R-9: opal-pm.md §3에 Step 0(에이전트 선택), Step 6(실행 라우팅), Step 7(슬라이싱)이 정의되고, 폴백 규칙 3단계가 존재하는가
- [ ] R-10: opal-pm.md §4에 영역 침범 + 인터페이스 정합성 항목이 추가되었는가
- [ ] R-11: opal-pm.md §6에 에이전트별 문서 매핑 테이블이 포함되고, 기존 범용 방식이 유지되는가
- [ ] R-12: opal-pm.md §10에 인터페이스 계약 관리, Batch 간 핸드오프, 충돌 해소 3가지 역할이 정의되어 있는가
- [ ] R-13: opal-pm.md §4에 docs/ 무효화 체크 항목이 추가되어 있는가
- [ ] R-14: 관련 스킬 4개의 실행 주체에 "전문 에이전트 또는 opal-task-agent (폴백)" 표기가 있는가
- [ ] R-15: agents.md에 전문 에이전트 섹션 + 매핑 테이블(6행) + 추가 가이드 + 폴백 규칙이 존재하는가
- [ ] R-16: 4개 에이전트가 opal/agents/로 이동, agents/에 wtm-agent만 남아있는가

### 일관성 테스트
- [ ] agents.md의 매핑 테이블과 opal-pm.md §6의 문서 매핑 테이블이 일치하는가
- [ ] op-dev-plan SKILL.md의 Step 형식과 plan-guide.md의 Step 형식이 일치하는가
- [ ] 전문 에이전트 AGENT.md의 결과 반환 형식이 opal-task-agent와 동일한가
- [ ] install-mac.sh의 에이전트 소스 경로가 실제 디렉토리 구조와 일치하는가
- [ ] opal-task-action-agent 내부의 에이전트 참조(opal-test-agent)가 실제 디렉토리와 일치하는가
- [ ] CONVENTIONS.md의 에이전트 경로 규칙이 실제 디렉토리 구조와 일치하는가
- [ ] ARCHITECTURE.md의 에이전트 개수(10개)가 실제와 일치하는가

### 문서 품질
- [ ] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가
- [ ] kebab-case 파일/폴더 네이밍을 따르는가
- [ ] YAML frontmatter 키가 영어이고 파싱 가능한가
- [ ] 기존 에이전트(opal-task-agent 등)가 삭제되지 않고 폴백으로 유지되는가
- [ ] pilot SKILL.md의 파이프라인 구조(단계 정의, Gate 순서)가 변경되지 않았는가
- [ ] `~/.opal/` 직접 수정이 없고 `opal/` 소스 경로에서만 수정했는가

---

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| opal-task-action-agent 내부 에이전트 참조 누락 | oppd Phase 3 액션 실행 시 op-dev-test-agent를 찾지 못함 | Step 13에서 opal-task-action-agent 내부 모든 에이전트명 참조를 grep으로 확인 후 갱신 |
| install-mac.sh 에이전트 소스 이원화 복잡도 | 설치 시 누락 가능 | opal/agents + agents 두 디렉토리 모두 순회하는 루프를 명확히 분리 |
| 기존 태스크의 PLAN.md에 agent 필드 없음 | 과거 PLAN.md로 EXECUTE 시 agent 필드 부재 | opal-pm.md 폴백 규칙: agent 필드 없으면 기존 방식(opal-task-agent) 사용. PLAN.md 하위호환 보장 |
| 전문 에이전트와 opal-task-agent 결과 형식 차이 | 오케스트레이터가 결과 파싱 실패 | 전문 에이전트 결과 반환 형식을 opal-task-agent와 완전 동일하게 유지 |
| opal-sdd-action-agent가 install에서 누락 상태 | SDD 파이프라인 배포 안 됨 | 이번 install-mac.sh 갱신 시 opal/agents/ 전체를 소스로 잡아 자동 해소 |
| op-dev-test-scenario SKILL.md의 opal-task-agent 하드참조 다수 | 115에서 PLAN 통합됐으나 기존 참조 잔존 | 실행 주체만 갱신하고, 본문의 "opal-task-agent 담당 필드" 등 역할 설명은 유지 (워커명이 아니라 역할 설명이므로) |
