# PLAN: 멀티 플랫폼 모델 매핑 참조 문서 + 스킬 적용

> 작성일: 2026-03-29 | 버전: v1.0

## 현황 조사 결과

### 관련 파일 및 현재 상태

#### model override 사용 파일 (오케스트레이터 스킬)

| 파일 | 현재 model 지정 방식 |
|------|---------------------|
| `skills/opal-pilot-dev/SKILL.md` | ANALYSIS: `haiku`, PLAN: `opus`, TEST-SCENARIO: `haiku`, EXECUTE: `sonnet` |
| `skills/opal-pilot-dev-short/SKILL.md` | PLAN: `opus`, TEST-SCENARIO: `haiku`, EXECUTE: `sonnet` |
| `skills/opal-pilot-dev-wireframe/SKILL.md` | WIREFRAME: `sonnet`, EXECUTE: `sonnet` |
| `skills/opal-project-pilot/SKILL.md` | PLAN: `opus`, EXECUTE: `sonnet` |
| `skills/opal-agent-creator/SKILL.md` | 설명에서 opus/sonnet/haiku 선택 가이드 제공 |

#### model 정의가 있는 에이전트

| 파일 | 현재 상태 |
|------|----------|
| `agents/opal-task-agent/AGENT.md` | frontmatter `model: sonnet` + 단계별 model 오버라이드 테이블 (haiku/opus/sonnet) |
| `agents/wtm-agent/AGENT.md` | frontmatter `model: haiku` |
| `agents/op-task-qa-agent/AGENT.md` | frontmatter `model: haiku` |
| `agents/op-dev-test-agent/AGENT.md` | frontmatter `model: sonnet` |

#### model 미사용 오케스트레이터

| 파일 | 비고 |
|------|------|
| `skills/opal-pilot-write/SKILL.md` | model 지정 없음 (오케스트레이터 직접 수행) |
| `skills/opal-pilot-write-tech/SKILL.md` | model 지정 없음 (PM이 워커 디스패치하지만 model 미명시) |

#### 참조 문서 인프라

| 파일 | 역할 |
|------|------|
| `opal/core/references/` | 소스 경로 (5개 .md 파일 존재) |
| `~/.opal/references/` | 배포 경로 |
| `scripts/install-mac.sh` | `cp -Rf opal/core/references/. ~/.opal/references/` 로 전체 복사 |
| `opal/core/references/opal-harness.md` | 오케스트레이터 공통 인프라 (model 관련 내용 없음) |

### 핵심 발견

1. **Claude 전용 하드코딩**: 모든 model 지정이 `haiku`, `opus`, `sonnet`으로 Claude 전용.
2. **분산 정의**: model 매핑이 각 오케스트레이터 SKILL.md와 에이전트 AGENT.md에 분산.
3. **추상화 부재**: 레벨 기반 추상화 없이 직접 모델명을 사용.
4. **배포 파이프라인 존재**: `opal/core/references/` -> `~/.opal/references/`로 자동 배포되므로 참조 문서 추가만 하면 배포됨.
5. **opal-harness.md가 적절한 중앙화 지점**: 이미 오케스트레이터 공통 인프라 역할을 하고 있으므로, model 매핑 참조를 이곳에서 연결하면 자연스럽다.

---

## 1. 파일 변경 계획

### 신규 생성

| # | 파일 경로 | 역할 |
|---|----------|------|
| 1 | `opal/core/references/opal-model-mapping.md` | 레벨 기반 모델 추상화 정의 + 플랫폼별 매핑 테이블 |

### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 2 | `opal/core/references/opal-harness.md` | model 매핑 참조 섹션 추가 (opal-model-mapping.md 링크) |
| 3 | `opal/core/AGENT.md` | 부트스트랩에 플랫폼 감지 → 모델 매핑 자동 적용 로직 추가 |
| 4 | `skills/opal-pilot-dev/SKILL.md` | `haiku`/`opus`/`sonnet` -> 레벨 참조 표기로 전환 |
| 5 | `skills/opal-pilot-dev-short/SKILL.md` | 동일 전환 |
| 6 | `skills/opal-pilot-dev-wireframe/SKILL.md` | 동일 전환 |
| 7 | `skills/opal-project-pilot/SKILL.md` | 동일 전환 |
| 8 | `skills/opal-agent-creator/SKILL.md` | model 선택 가이드를 레벨 참조로 전환 |
| 9 | `agents/opal-task-agent/AGENT.md` | model 오버라이드 테이블을 레벨 기반으로 전환 |

### 삭제

없음.

---

## 2. 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | 모델 매핑 참조 문서 신규 작성 | `opal/core/references/opal-model-mapping.md` | 중 |
| 2 | harness에 model 매핑 참조 섹션 추가 | `opal/core/references/opal-harness.md` | 하 |
| 3 | AGENT.md 부트스트랩에 플랫폼 감지 + 모델 매핑 로직 추가 | `opal/core/AGENT.md` | 중 |
| 4 | opal-pilot-dev model 전환 | `skills/opal-pilot-dev/SKILL.md` | 하 |
| 5 | opal-pilot-dev-short model 전환 | `skills/opal-pilot-dev-short/SKILL.md` | 하 |
| 6 | opal-pilot-dev-wireframe model 전환 | `skills/opal-pilot-dev-wireframe/SKILL.md` | 하 |
| 7 | opal-project-pilot model 전환 | `skills/opal-project-pilot/SKILL.md` | 하 |
| 8 | opal-agent-creator model 전환 | `skills/opal-agent-creator/SKILL.md` | 하 |
| 9 | opal-task-agent model 오버라이드 테이블 전환 | `agents/opal-task-agent/AGENT.md` | 하 |

---

## 3. 핵심 설계

### 3-1. opal-model-mapping.md 구조

#### 레벨 정의

3단계 레벨로 추상화한다. 레벨명은 직관적이고 플랫폼 중립적이어야 한다.

| 레벨 | 용도 | 특성 |
|------|------|------|
| `light` | 단순 작업: 분류, 포맷 변환, 검색 기반 분석 | 빠르고 저렴, 간단한 추론 |
| `standard` | 범용 작업: 코드 작성, 문서 작성, 일반 분석 | 균형 잡힌 성능 |
| `advanced` | 복잡 추론: 아키텍처 설계, 깊은 분석, 전략 수립 | 최고 추론 능력 |

#### 플랫폼별 매핑 테이블

| 레벨 | Claude | Gemini | OpenAI | 비고 |
|------|--------|--------|--------|------|
| `light` | haiku | gemini-2.5-flash-lite | gpt-4.1-mini | 빠르고 저렴, 단순 작업 |
| `standard` | sonnet | gemini-2.5-flash | gpt-4.1 | 균형 잡힌 범용 |
| `advanced` | opus | gemini-2.5-pro | o3 | 최고 추론 능력 |

> 매핑 테이블은 부트스트랩 시 플랫폼 감지 후 자동 적용된다.
> 플랫폼별 최신 모델이 출시되면 이 테이블을 갱신한다.
> 공식 모델 목록:
> - Claude: https://docs.anthropic.com/en/docs/about-claude/models
> - Gemini: https://ai.google.dev/gemini-api/docs/models
> - OpenAI: https://developers.openai.com/api/docs/models

#### 스킬에서의 참조 형식

스킬에서 model을 지정할 때 레벨명을 사용한다:

```markdown
**model**: standard  <!-- opal-model-mapping 참조 -->
```

#### 현재 매핑 관계 (기존 -> 레벨)

| 기존 (Claude) | 레벨 |
|---------------|------|
| haiku | light |
| sonnet | standard |
| opus | advanced |

### 3-2. AGENT.md 부트스트랩 — 플랫폼 감지 + 모델 매핑 자동 적용

부트스트랩 절차에 새 단계를 추가한다. 기존 4단계(참조 문서 Read) 직후에 삽입:

```
부트스트랩 기존 흐름:
1. identity.md 로드
2. 스킬 레지스트리 확인
3. 참조 문서 Read (agents.md, mcps.md, opal-harness.md)
4. ★ 신규: opal-model-mapping.md Read → 플랫폼 감지 → 모델 매핑 적용
5. 프로젝트 부트스트래퍼 확인
6. PM 컨텍스트 로드
7. 프로젝트 메모리 브리핑
```

**플랫폼 감지 로직**:

에이전트가 로드된 부트스트래퍼 파일로 현재 플랫폼을 판별한다:
- `CLAUDE.md`에서 로드됨 → Claude (Claude Code)
- `.cursorrules` / `.cursor/rules/`에서 로드됨 → Cursor
- `GEMINI.md`에서 로드됨 → Gemini (Gemini CLI / Antigravity)

> Cursor는 사용자가 설정한 모델 제공자(Claude/Gemini/OpenAI)에 따라 달라진다. Cursor 감지 시 모델 제공자를 추가 확인하거나, 사용자에게 질문한다.

**적용 방식**:

`opal-model-mapping.md`를 Read하여 현재 플랫폼에 해당하는 매핑 컬럼을 세션 컨텍스트에 로드한다. 이후 스킬에서 `**model**: standard` 등의 레벨명을 만나면, 매핑 테이블에서 현재 플랫폼의 실제 모델명으로 치환하여 적용한다.

### 3-3. opal-harness.md 변경

기존 섹션 번호 체계 유지. "5. Observability" 다음에 새 섹션 추가:

```markdown
## 6. Model Mapping (모델 매핑)

오케스트레이터가 워커를 디스패치할 때, model 필드는 레벨명을 사용한다.
레벨별 플랫폼 매핑: `~/.opal/references/opal-model-mapping.md` 참조.

| 레벨 | 용도 |
|------|------|
| light | 단순 작업 (분류, 포맷 변환, 검색 기반 분석) |
| standard | 범용 작업 (코드 작성, 문서 작성, 일반 분석) |
| advanced | 복잡 추론 (아키텍처 설계, 깊은 분석) |
```

### 3-3. 오케스트레이터 스킬 변경 패턴

모든 오케스트레이터에서 동일한 패턴으로 치환한다:

| 기존 | 변경 후 |
|------|--------|
| `**model**: haiku` | `**model**: light` |
| `**model**: sonnet` | `**model**: standard` |
| `**model**: opus` | `**model**: advanced` |

인라인 참조 표기도 동일:
- `op-dev-plan 워커 디스패치. **model**: opus.` -> `op-dev-plan 워커 디스패치. **model**: advanced.`

### 3-4. opal-agent-creator 변경

기존:
```
4. **model** -- 복잡도에 따라 선택 (opus: 복잡 추론, sonnet: 범용, haiku: 단순 작업)
```

변경:
```
4. **model** -- 레벨로 지정 (advanced: 복잡 추론, standard: 범용, light: 단순 작업). 레벨→모델 매핑: opal-model-mapping.md 참조
```

### 3-5. opal-task-agent 변경

model 오버라이드 테이블의 model 컬럼을 레벨명으로 전환:

| 단계 스킬 | model (기존) | model (변경) |
|----------|-------------|-------------|
| op-task-plan | opus | advanced |
| op-task-execute | sonnet | standard |
| op-dev-analysis | haiku | light |
| op-dev-plan | opus | advanced |
| op-dev-todo | haiku | light |
| op-dev-test-scenario | haiku | light |
| op-dev-execute | sonnet | standard |
| op-dev-wireframe | sonnet | standard |

frontmatter의 `model: sonnet` -> `model: standard`으로 변경.

---

## 3. 실행 체크리스트

### Step 1: 모델 매핑 참조 문서 작성
- [ ] 완료
- **파일**: `opal/core/references/opal-model-mapping.md`
- **작업 내용**: 레벨 정의 (light/standard/advanced), 플랫폼별 매핑 테이블 (Claude/Gemini/OpenAI), 스킬 참조 형식 가이드, 갱신 가이드라인 작성
- **완료 기준**: 3개 레벨 정의 + 3개 플랫폼 매핑 + 참조 형식 예시가 포함됨
- **테스트**: 문서가 단독으로 이해 가능한지 확인
- **의존**: 없음

### Step 2: opal-harness.md에 Model Mapping 섹션 추가
- [ ] 완료
- **파일**: `opal/core/references/opal-harness.md`
- **작업 내용**: 섹션 6 "Model Mapping" 추가 — 레벨 요약 테이블 + opal-model-mapping.md 참조 링크
- **완료 기준**: harness에서 model 레벨 요약과 참조 경로가 명시됨
- **테스트**: 기존 섹션 번호 체계가 유지되는지 확인
- **의존**: Step 1

### Step 3: AGENT.md 부트스트랩에 모델 매핑 자동 적용 로직 추가
- [ ] 완료
- **파일**: `opal/core/AGENT.md`
- **작업 내용**: 부트스트랩 절차에 플랫폼 감지 + opal-model-mapping.md Read + 매핑 적용 단계 추가
- **완료 기준**: 부트스트랩 절차에 플랫폼 감지 로직과 매핑 적용 방법이 명시됨
- **테스트**: 기존 부트스트랩 단계 번호 재조정이 정확한지 확인
- **의존**: Step 1

### Step 4: opal-pilot-dev model 전환
- [ ] 완료
- **파일**: `skills/opal-pilot-dev/SKILL.md`
- **작업 내용**: `haiku` -> `light`, `opus` -> `advanced`, `sonnet` -> `standard`로 전환 (4곳)
- **완료 기준**: 파일 내 haiku/opus/sonnet 문자열이 model 컨텍스트에서 없음
- **테스트**: Grep으로 잔여 확인
- **의존**: Step 1

### Step 5: opal-pilot-dev-short model 전환
- [ ] 완료
- **파일**: `skills/opal-pilot-dev-short/SKILL.md`
- **작업 내용**: `opus` -> `advanced`, `haiku` -> `light`, `sonnet` -> `standard`로 전환 (3곳)
- **완료 기준**: 파일 내 haiku/opus/sonnet 문자열이 model 컨텍스트에서 없음
- **테스트**: Grep으로 잔여 확인
- **의존**: Step 1

### Step 6: opal-pilot-dev-wireframe model 전환
- [ ] 완료
- **파일**: `skills/opal-pilot-dev-wireframe/SKILL.md`
- **작업 내용**: `sonnet` -> `standard`로 전환 (2곳)
- **완료 기준**: 파일 내 sonnet 문자열이 model 컨텍스트에서 없음
- **테스트**: Grep으로 잔여 확인
- **의존**: Step 1

### Step 7: opal-project-pilot model 전환
- [ ] 완료
- **파일**: `skills/opal-project-pilot/SKILL.md`
- **작업 내용**: `opus` -> `advanced`, `sonnet` -> `standard`로 전환 (2곳)
- **완료 기준**: 파일 내 opus/sonnet 문자열이 model 컨텍스트에서 없음
- **테스트**: Grep으로 잔여 확인
- **의존**: Step 1

### Step 8: opal-agent-creator model 가이드 전환
- [ ] 완료
- **파일**: `skills/opal-agent-creator/SKILL.md`
- **작업 내용**: model 선택 가이드 문구를 레벨 기반으로 변경
- **완료 기준**: 가이드에 light/standard/advanced 레벨과 opal-model-mapping.md 참조가 명시됨
- **테스트**: 기존 설명의 의미가 보존되는지 확인
- **의존**: Step 1

### Step 9: opal-task-agent model 오버라이드 테이블 전환
- [ ] 완료
- **파일**: `agents/opal-task-agent/AGENT.md`
- **작업 내용**: frontmatter `model: sonnet` -> `model: standard`, 오버라이드 테이블의 model 컬럼 전환
- **완료 기준**: 에이전트 파일 내 haiku/opus/sonnet이 model 컨텍스트에서 없음
- **테스트**: Grep으로 잔여 확인
- **의존**: Step 1

---

## 4. QA 체크리스트

### 기능 테스트
- [ ] opal-model-mapping.md에 3개 레벨(light/standard/advanced)이 정의되어 있는가
- [ ] opal-model-mapping.md에 3개 플랫폼(Claude/Gemini/OpenAI) 매핑이 있는가
- [ ] 모든 오케스트레이터(opd/opds/opdw/opp)의 model 필드가 레벨명으로 전환되었는가
- [ ] opal-agent-creator의 model 선택 가이드가 레벨 기반으로 변경되었는가
- [ ] opal-task-agent의 model 오버라이드 테이블이 레벨 기반으로 변경되었는가
- [ ] opal-harness.md에 Model Mapping 섹션이 추가되었는가

### 일관성 테스트
- [ ] 모든 변경된 파일에서 model 컨텍스트의 haiku/opus/sonnet이 레벨명으로 대체되었는가
- [ ] opal-model-mapping.md의 레벨 정의와 각 스킬의 model 지정이 일치하는가
- [ ] install-mac.sh 변경 없이 opal/core/references/에서 자동 배포되는가
- [ ] opal-pilot-write, opal-pilot-write-tech는 model 미사용이므로 변경 없이 유지되는가

### 문서 품질
- [ ] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가
- [ ] kebab-case 파일/폴더 네이밍을 따르는가 (opal-model-mapping.md)
- [ ] 각 변경 파일의 변경이력에 이번 변경이 기록되었는가
