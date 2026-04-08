# PLAN: 에이전트 아이콘 Observability + 메모리 브리핑 간소화

> 작성일: 2026-04-08
> 입력: TASK.md
> 출력: PLAN.md

## 1. 현황 조사

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `opal/core/references/opal-harness.md` | 하네스 공통 — §5 Observability 행위 주체 표시 | O |
| `opal/core/AGENT.md` | 에이전트 정의 + 부트스트랩 — 메모리 브리핑 절차 | O |
| `agents/opal-task-agent/AGENT.md` | 범용 워커 — frontmatter에 `icon` 추가 | O |
| `agents/opal-task-qa-agent/AGENT.md` | QA 워커 — frontmatter에 `icon` 추가 | O |
| `agents/opal-task-action-agent/AGENT.md` | SDD 액션 에이전트 — frontmatter에 `icon` 추가 | O |
| `agents/op-dev-test-agent/AGENT.md` | 테스트 에이전트 — frontmatter에 `icon` 추가 | O |
| `agents/wtm-agent/AGENT.md` | 웹→마크다운 에이전트 — frontmatter에 `icon` 추가 | O |
| `docs/CONVENTIONS.md` | 에이전트 YAML frontmatter 스키마 정의 | O |

### 현재 상태

#### 하네스 §5 행위 주체 표시 (opal-harness.md 422-436행)

현재 테이블:

| 선언 형식 | 사용 시점 |
|----------|---------|
| `📋 알투[PM] 직접:` | PM이 직접 툴 호출 직전 |
| `⚙️ 워커 디스패치:` | Agent 도구로 워커 디스패치 직전 |
| `⚙️ 워커 완료:` | 워커 결과 수신 직후 |

문제점:
- "워커"로 한정되어 QA 에이전트(`opal-task-qa-agent`), 테스트 에이전트(`op-dev-test-agent`), 액션 에이전트(`opal-task-action-agent`) 등 비워커 에이전트 디스패치가 선언 대상에서 빠짐
- 아이콘 체계 없음 — 모든 Agent 디스패치가 동일한 `⚙️`로 표시

#### 에이전트 frontmatter 현황

| 에이전트 | frontmatter 필드 | icon 유무 |
|---------|-----------------|----------|
| opal-task-agent | name, description, model(standard) | X |
| opal-task-qa-agent | name, description, model(light) | X |
| opal-task-action-agent | name, description, model(advanced) | X |
| op-dev-test-agent | name, description, model(standard) | X |
| wtm-agent | name, description, model(light), color(green) | X |

#### 메모리 브리핑 절차 (AGENT.md 215-221행)

현재 5단계:
1. `{프로젝트}/.opal/MEMORY.md`를 Read
2. 없으면 브리핑 생략
3. 인덱스에서 최근 메모리 항목 파악
4. **관련성이 높은 메모리 파일을 선택적으로 Read** (삭제 대상)
5. 첫 응답에 브리핑 포함

문제점: MEMORY.md 인덱스만으로 브리핑에 충분한데, 4단계에서 하위 파일까지 Read하도록 되어 토큰 낭비

#### CONVENTIONS.md YAML Frontmatter 스키마 (68-82행)

에이전트 frontmatter 정의에 `model` 필드만 있고 `icon` 필드가 없음. 새 필드를 추가해야 스키마 일관성이 유지됨.

### 영향 범위

- **하네스 변경**: 모든 오케스트레이터(`opal-pilot-*`)가 하네스 §5를 참조하므로, 행위 주체 표시 형식 변경이 전체 파이프라인에 즉시 적용됨
- **에이전트 frontmatter 변경**: 기존 필드(name, description, model)에 `icon`을 추가하는 것이므로 하위 호환성 보장. 디폴트 `✨` 폴백이 있어 미정의 시에도 동작
- **메모리 브리핑 변경**: AGENT.md 단독 수정. 부트스트랩 시 이 절차를 따르므로 즉시 적용
- **CONVENTIONS.md 변경**: 스키마 문서이므로 실제 동작에 영향 없음. 문서 일관성 목적

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 |
|---|----------|------|
| (없음) | | |

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `opal/core/references/opal-harness.md` | §5 행위 주체 표시 테이블 — `{icon} 디스패치/완료` 형식으로 확장 + 아이콘 룩업 규칙 추가 |
| 2 | `docs/CONVENTIONS.md` | YAML Frontmatter 스키마에 `icon` 필드 추가 |
| 3 | `agents/opal-task-agent/AGENT.md` | frontmatter에 `icon: "✨"` 추가 |
| 4 | `agents/opal-task-qa-agent/AGENT.md` | frontmatter에 `icon: "🔍"` 추가 |
| 5 | `agents/opal-task-action-agent/AGENT.md` | frontmatter에 `icon: "⚡"` 추가 |
| 6 | `agents/op-dev-test-agent/AGENT.md` | frontmatter에 `icon: "🧪"` 추가 |
| 7 | `agents/wtm-agent/AGENT.md` | frontmatter에 `icon: "🌐"` 추가 |
| 8 | `opal/core/AGENT.md` | 메모리 브리핑 절차 4단계 삭제, 5단계 → 4단계 번호 조정 |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| (없음) | | |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | 하네스 §5 행위 주체 표시 확장 | `opal/core/references/opal-harness.md` | 중 |
| 2 | CONVENTIONS.md 스키마에 icon 필드 추가 | `docs/CONVENTIONS.md` | 하 |
| 3 | 에이전트 5개 frontmatter에 icon 추가 | `agents/*/AGENT.md` (5개) | 하 |
| 4 | 메모리 브리핑 절차 간소화 | `opal/core/AGENT.md` | 하 |

순서 근거: 하네스(1)가 아이콘 룩업 규칙을 정의하므로 먼저. CONVENTIONS(2)가 스키마를 정의하므로 에이전트(3) 전에. 메모리 브리핑(4)은 독립적이므로 마지막.

### 핵심 설계

#### 1. 하네스 §5 행위 주체 표시 확장 (`opal-harness.md`)

**변경 대상**: 422-436행 (행위 주체 표시 섹션)

**아이콘 룩업 규칙** 추가 (테이블 앞에 삽입):

```markdown
#### 아이콘 룩업

Agent 도구로 에이전트를 디스패치할 때, 해당 에이전트 AGENT.md의 frontmatter `icon` 필드를 읽어 사용한다.
`icon` 필드가 없으면 디폴트 아이콘 `✨`을 사용한다.
```

**테이블 변경**:

| 기존 | 변경 후 |
|------|--------|
| `⚙️ 워커 디스패치:` | `{icon} 디스패치: {단계명} — {설명}` |
| `⚙️ 워커 완료:` | `{icon} 완료: {단계명} — {결과 요약}` |
| `📋 알투[PM] 직접:` | 변경 없음 (현행 유지) |

**규칙 섹션 수정**:
- "워커"를 "에이전트"로 확장하여 모든 Agent 도구 디스패치(워커 + QA + 테스트 + 액션 등)에 적용됨을 명시

#### 2. CONVENTIONS.md YAML Frontmatter 스키마 (`docs/CONVENTIONS.md`)

**변경 대상**: 72-82행 (YAML Frontmatter 코드 블록)

```yaml
---
name: {컴포넌트 이름}
description: |
  {설명 — 트리거 키워드 포함}
triggers:             # 스킬만
  - "{트리거 문구}"
version: {X.Y.Z}     # 스킬만
model: {모델}         # 에이전트만
icon: {이모지}         # 에이전트만 (선택, 디폴트: ✨)
---
```

#### 3. 에이전트 frontmatter icon 필드 추가

각 에이전트 AGENT.md의 YAML frontmatter에 `icon` 필드를 `model` 필드 다음 줄에 추가.

| 에이전트 | icon | 선정 근거 |
|---------|------|----------|
| opal-task-agent | ✨ | 범용 워커 — 디폴트 아이콘 |
| opal-task-qa-agent | 🔍 | QA 검증 — 돋보기(검사/검증 의미) |
| opal-task-action-agent | ⚡ | SDD 액션 자율 실행 — 번개(빠른 자율 실행) |
| op-dev-test-agent | 🧪 | 테스트 실행 — 실험 플라스크 |
| wtm-agent | 🌐 | 웹→마크다운 변환 — 지구본(웹 리소스) |

wtm-agent의 기존 `color: green` 필드는 유지. `icon`은 `color` 다음 줄에 추가.

#### 4. 메모리 브리핑 절차 간소화 (`opal/core/AGENT.md`)

**변경 대상**: 215-221행 (절차 섹션)

기존:
```
1. `{프로젝트}/.opal/MEMORY.md`를 Read로 읽는다
2. MEMORY.md가 없으면 브리핑 생략 (인사만 하고 대기)
3. MEMORY.md가 있으면 인덱스에서 최근 메모리 항목을 파악한다
4. 관련성이 높은 메모리 파일을 선택적으로 Read한다 (전부 읽지 않음)  ← 삭제
5. 첫 응답에 브리핑을 포함한다
```

변경 후:
```
1. `{프로젝트}/.opal/MEMORY.md`를 Read로 읽는다
2. MEMORY.md가 없으면 브리핑 생략 (인사만 하고 대기)
3. MEMORY.md가 있으면 인덱스에서 최근 메모리 항목을 파악한다
4. 첫 응답에 브리핑을 포함한다
```

## 3. 실행 체크리스트

> 총 4개 Step | Phase 3개
>
> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | 1     | 1    | 순차 | 하네스 — 아이콘 룩업 규칙 정의 |
> | 2     | 2, 3 | 병렬 | CONVENTIONS + 에이전트 frontmatter (독립 파일) |
> | 3     | 4    | 순차 | 메모리 브리핑 간소화 (독립이나 별도 파일) |

### Step 1: 하네스 §5 행위 주체 표시 확장
- [ ] 완료
- **파일**: `opal/core/references/opal-harness.md`
- **작업 내용**:
  1. §5 행위 주체 표시 섹션(422행 부근)에 "아이콘 룩업" 서브섹션 추가 — frontmatter `icon` 필드 참조 규칙 + 디폴트 `✨` 명시
  2. 선언 형식 테이블에서 `⚙️ 워커 디스패치:` → `{icon} 디스패치: {단계명} — {설명}`, `⚙️ 워커 완료:` → `{icon} 완료: {단계명} — {결과 요약}`으로 변경
  3. `📋 알투[PM] 직접:` 행은 현행 유지
  4. 규칙 섹션에서 "워커"를 "에이전트"로 확장 — 모든 Agent 도구 디스패치 대상 명시
- **완료 기준**: 테이블에 아이콘 룩업 규칙이 명시되고, 모든 Agent 디스패치가 선언 대상에 포함됨
- **테스트**: opal-harness.md를 Read하여 (1) 아이콘 룩업 규칙 존재, (2) PM 직접 행위 현행 유지, (3) 워커 한정 표현 제거 확인
- **의존**: 없음

### Step 2: CONVENTIONS.md 스키마에 icon 필드 추가
- [ ] 완료
- **파일**: `docs/CONVENTIONS.md`
- **작업 내용**: YAML Frontmatter 코드 블록(72행 부근)에 `icon: {이모지}  # 에이전트만 (선택, 디폴트: ✨)` 행 추가 (`model` 다음 줄)
- **완료 기준**: YAML Frontmatter 스키마에 `icon` 필드가 에이전트 전용 선택 필드로 명시됨
- **테스트**: CONVENTIONS.md를 Read하여 icon 필드가 model 다음에 있고 주석이 올바른지 확인
- **의존**: Step 1 (하네스에서 아이콘 체계를 정의해야 스키마 추가가 의미 있음)

### Step 3: 에이전트 5개 frontmatter에 icon 추가
- [ ] 완료
- **파일**: `agents/opal-task-agent/AGENT.md`, `agents/opal-task-qa-agent/AGENT.md`, `agents/opal-task-action-agent/AGENT.md`, `agents/op-dev-test-agent/AGENT.md`, `agents/wtm-agent/AGENT.md`
- **작업 내용**:
  1. `opal-task-agent`: `model: standard` 다음 줄에 `icon: "✨"` 추가
  2. `opal-task-qa-agent`: `model: light` 다음 줄에 `icon: "🔍"` 추가
  3. `opal-task-action-agent`: `model: advanced` 다음 줄에 `icon: "⚡"` 추가
  4. `op-dev-test-agent`: `model: standard` 다음 줄에 `icon: "🧪"` 추가
  5. `wtm-agent`: `color: green` 다음 줄에 `icon: "🌐"` 추가
- **완료 기준**: 5개 에이전트 AGENT.md의 frontmatter에 유효한 이모지 값의 `icon` 필드가 존재
- **테스트**: 5개 파일을 Read하여 frontmatter `icon` 필드 값 확인
- **의존**: Step 1 (하네스에서 아이콘 룩업 규칙을 정의해야 frontmatter 필드가 의미 있음)

### Step 4: 메모리 브리핑 절차 간소화
- [ ] 완료
- **파일**: `opal/core/AGENT.md`
- **작업 내용**:
  1. 절차 섹션(215행 부근)에서 4단계("관련성이 높은 메모리 파일을 선택적으로 Read한다 (전부 읽지 않음)") 삭제
  2. 기존 5단계("첫 응답에 브리핑을 포함한다") → 4단계로 번호 조정
- **완료 기준**: 브리핑 절차가 4단계이며, MEMORY.md 인덱스만 읽도록 되어 있고 하위 파일 Read 단계가 없음
- **테스트**: AGENT.md를 Read하여 (1) 절차가 4단계인지, (2) 하위 파일 Read 언급이 없는지 확인
- **의존**: 없음

## 4. QA 체크리스트

### 기능 테스트
- [ ] R1: 하네스 §5에 아이콘 룩업 규칙이 명시되어 있는가 (frontmatter → 디폴트 ✨)
- [ ] R1: 행위 주체 표시 테이블이 `{icon} 디스패치/완료` 형식으로 변경되었는가
- [ ] R1: PM 직접 행위(`📋`) 표시가 현행 유지되는가
- [ ] R1: 모든 Agent 디스패치(워커 + QA + 테스트 + 액션)가 선언 대상에 포함되는가
- [ ] R2: 5개 에이전트 AGENT.md에 `icon` 필드가 존재하고 유효한 이모지 값인가
- [ ] R3: 메모리 브리핑 절차에 하위 파일 Read 단계가 없는가
- [ ] R3: 절차 번호가 1~4로 올바르게 조정되었는가

### 일관성 테스트
- [ ] CONVENTIONS.md의 YAML Frontmatter 스키마에 `icon` 필드가 추가되어 실제 에이전트 frontmatter와 일치하는가
- [ ] 하네스 §5의 아이콘 룩업 규칙과 에이전트 frontmatter 구조가 일관성 있는가
- [ ] 배포본(`~/.opal/`)은 수정되지 않았는가 (소스 파일만 수정)

### 문서 품질
- [ ] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가
- [ ] kebab-case 파일/폴더 네이밍을 따르는가
- [ ] YAML frontmatter가 올바른가 (에이전트 5개)

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| 기존 오케스트레이터 스킬이 `⚙️ 워커` 형식을 하드코딩 | 하네스 변경 후 불일치 발생 가능 | TASK.md 제약 조건에 따라 기존 오케스트레이터 SKILL.md 수정 불필요 (하네스 공통에서 해결). 다만 실행 시 오케스트레이터 스킬에 `⚙️ 워커` 직접 참조가 있는지 Grep으로 확인 권장 |
| wtm-agent에 기존 `color` 커스텀 필드와 `icon` 필드 충돌 | 필드 순서/위치 혼란 | `icon`을 `color` 다음에 추가하여 기존 필드 유지 |
| 배포본(`~/.opal/`) 미동기화 | 소스 수정 후 배포 전까지 동작 불일치 | install 스크립트로 배포하면 해결 — 구현 범위 외 |
