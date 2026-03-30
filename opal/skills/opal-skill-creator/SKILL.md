---
name: opal-skill-creator
description: |
  **OPAL 프레임워크 스킬 생성 파이프라인**. skill-creator로 SKILL.md를 생성한 뒤, OPAL 규격 후처리(디렉토리 구조, frontmatter 보정, 레지스트리 등록, 버전 태깅)를 자동 수행합니다.
  반드시 이 스킬을 사용해야 하는 상황: "새 스킬 만들어줘", "스킬 생성", "프레임워크 스킬 추가", "스킬 작성해줘", "스킬 개선해줘", 기존 프레임워크 스킬 수정/개선 요청 시, "스킬 만들고 등록해줘", "OPAL 스킬 추가".
  커뮤니티 skill-creator를 래핑하여 OPAL 프레임워크 규격을 자동 적용합니다. 단순히 스킬 콘텐츠만 만드는 것이 아니라, 디렉토리 배치, 레지스트리 등록, 버전 태깅까지 한 번에 완료합니다.
---

# OPAL 프레임워크 스킬 생성 파이프라인

skill-creator 커뮤니티 스킬로 SKILL.md 콘텐츠를 생성한 뒤, OPAL 프레임워크 규격에 맞는 후처리를 자동 수행하는 2단계 파이프라인이다.

## 의존 스킬

| 스킬 | 역할 | 필수 |
|------|------|------|
| skill-creator | Phase 1 콘텐츠 생성 위임 | O |
| opal-doc-standard | 문서 표준 + 버전 관리 규칙 참조 (Read: ~/.opal/references/opal-doc-standard.md) | O |

## 진입 분기

사용자 요청을 분석하여 모드를 결정한다.

```
사용자 요청 수신
  |
  +-- 새 스킬 요청 ("만들어줘", "생성", "추가") --> 신규 생성 모드
  |     +-- 스킬 유형 확인 (프레임워크 / OPAL 전용)
  |     +-- Phase 1: skill-creator (Capture Intent ~ 완료)
  |     +-- Phase 2: OPAL 후처리
  |
  +-- 기존 스킬 개선 ("개선해줘", "수정해줘", 스킬명 지정) --> 개선 모드
        +-- 기존 SKILL.md 로드
        +-- Phase 1: skill-creator improve 플로우
        +-- Phase 2: OPAL 후처리 (레지스트리 갱신, 버전 증가)
```

### 스킬 유형 판단 기준

| 유형 | 저장 경로 | 기준 |
|------|----------|------|
| 프레임워크 스킬 | `skills/{name}/SKILL.md` | 3개 플랫폼 공용, install-mac.sh로 배포 |
| OPAL 전용 스킬 | `~/.opal/skills/{name}/SKILL.md` | OPAL 에이전트에서만 사용 |

사용자에게 유형을 확인한다. 명시하지 않으면 프레임워크 스킬로 기본 설정한다.

---

## Phase 1: 콘텐츠 생성 (skill-creator 위임)

skill-creator 커뮤니티 스킬의 프로세스를 따라 SKILL.md 콘텐츠를 생성한다. skill-creator 자체를 수정하지 않는다.

### 실행 방법

1. skill-creator SKILL.md를 Read로 읽는다.
   - 탐색 경로: `~/.opal/community-skills/skill-creator/SKILL.md`
   - 대체 경로: `~/.opal/community-skills/anthropics/skill-creator/SKILL.md`

2. skill-creator의 프로세스를 순서대로 따른다.

#### 신규 생성 모드

skill-creator의 전체 프로세스를 실행한다:

1. **Capture Intent** -- 스킬 목적, 트리거, 출력 형식 파악
2. **Interview and Research** -- 에지 케이스, 입출력 형식, 의존성 확인
3. **Write the SKILL.md** -- 초안 작성
4. **Test Cases** -- 테스트 프롬프트 작성 (선택)
5. **Running and evaluating** -- 테스트 실행 및 평가 (선택)
6. **Improving the skill** -- 피드백 기반 반복 개선 (선택)

단, SKILL.md 작성 시 아래 OPAL 규칙을 skill-creator에 컨텍스트로 전달한다:

- 한국어 본문, 영어 코드/필드명 (opal-doc-standard 규칙)
- 명령형(imperative) 문체
- SKILL.md 500줄 이하 유지
- 필요 시 `references/` 하위에 상세 가이드 분리

#### 개선 모드

1. 기존 SKILL.md를 Read로 로드한다.
2. skill-creator의 improve 플로우로 진입한다.
3. 사용자 피드백에 따라 반복 개선한다.

### Phase 1 완료 조건

- SKILL.md 초안이 작성되었거나 기존 SKILL.md가 개선되었다.
- 사용자가 콘텐츠에 만족했다 (또는 사용자가 테스트/평가 단계를 스킵했다).

---

## Phase 2: OPAL 규격 후처리

Phase 1에서 완성된 SKILL.md에 OPAL 프레임워크 규격을 적용한다. 아래 5개 항목을 순차 수행한다.

### 2-1. 디렉토리 구조 확정

스킬 유형에 따라 파일을 배치한다.

**프레임워크 스킬:**
```
skills/{name}/
├── SKILL.md
└── references/        (필요 시)
    └── {guide}.md
```

**OPAL 전용 스킬:**
```
~/.opal/skills/{name}/
├── SKILL.md
└── references/        (필요 시)
    └── {guide}.md
```

디렉토리가 없으면 생성한다. SKILL.md를 해당 경로에 저장한다.

### 2-2. YAML frontmatter 보정

Phase 1에서 작성된 frontmatter를 OPAL 규격에 맞게 보정한다.

검증 항목:

| 필드 | 규칙 | 예시 |
|------|------|------|
| `name` | kebab-case, 디렉토리명과 일치 | `api-analyzer` |
| `description` | OPAL 트리거 패턴 포함 | 아래 참조 |

**description 필수 구조:**
```yaml
description: |
  **{스킬 한줄 요약}**. {스킬이 하는 일 설명}.
  반드시 이 스킬을 사용해야 하는 상황: {트리거 키워드 나열}.
  {부가 설명}.
```

- 첫 문장은 볼드(**) 처리된 한줄 요약이다.
- "반드시 이 스킬을 사용해야 하는 상황:" 패턴을 반드시 포함한다.
- 트리거 키워드는 쌍따옴표로 감싼 자연어 구문을 쉼표로 나열한다.

### 2-3. 레지스트리 등록

`~/.opal/references/skills.md`에 스킬 항목을 추가한다.

**신규 생성 모드:**
- 해당 섹션(프레임워크 스킬 / OPAL 전용 스킬) 테이블에 새 행을 추가한다.
- 형식: `| {name} | {트리거 키워드} | {한줄 설명} |`

**개선 모드:**
- 기존 항목의 트리거나 설명이 변경되었으면 갱신한다.
- 변경이 없으면 그대로 둔다.

### 2-4. 버전 태깅

opal-doc-standard 규칙을 따른다 (Read: `~/.opal/references/opal-doc-standard.md`).

**신규 생성 모드:**
- SKILL.md 상단에 메타정보를 추가한다:
  ```
  > 작성일: {오늘 일시 YYYY-MM-DD HH:mm KST} | 버전: v1.0
  ```
- 문서 하단에 변경이력 테이블을 추가한다:
  ```markdown
  ## 변경이력

  | 버전 | 일시 | 변경내용 |
  |------|------|---------|
  | v1.0 | {오늘 일시 YYYY-MM-DD HH:mm} | 초기 작성 |
  ```

**개선 모드:**
- 변경 범위를 파악하여 Major/Minor를 결정한다.
  - 구조적 변경 (섹션 추가/삭제): Major 증가 (v1.x -> v2.0)
  - 내용 수정 (기존 섹션 수정): Minor 증가 (v1.0 -> v1.1)
- 변경이력 테이블에 새 버전 항목을 추가한다.
- 기존 파일을 보존하고, 새 버전은 새 파일로 생성한다.

### 2-5. 에이전트 생성 (선택)

스킬이 독립 컨텍스트에서 실행되는 에이전트를 필요로 하는 경우에만 수행한다.

사용자에게 에이전트 필요 여부를 확인한다. 필요하면 3개 플랫폼 에이전트 파일을 생성한다:

| 플랫폼 | 경로 | 형식 |
|--------|------|------|
| Claude Code | `agents/claude/{name}/AGENT.md` | 디렉토리 기반 |
| Cursor | `agents/cursor/{name}.md` | 플랫 파일 |
| Antigravity | `agents/antigravity/{name}/SKILL.md` | 스킬 통합 |

에이전트 파일에는 입력/출력 명세, 실행 프로세스, 검증 기준을 명시한다. 네이밍은 `{워크플로우}-{역할}` 패턴을 따른다.

---

## 완료 체크리스트

Phase 2 완료 후 아래 항목을 검증한다:

- [ ] SKILL.md가 올바른 경로에 저장되었는가
- [ ] YAML frontmatter의 name이 kebab-case이고 디렉토리명과 일치하는가
- [ ] description에 "반드시 이 스킬을 사용해야 하는 상황:" 패턴이 포함되어 있는가
- [ ] `~/.opal/references/skills.md`에 항목이 등록되었는가
- [ ] 버전 태깅이 적용되었는가 (메타정보 + 변경이력 테이블)
- [ ] SKILL.md가 500줄 이하인가
- [ ] 한국어 본문 / 영어 코드 규칙을 준수하는가

모든 항목이 통과하면 사용자에게 결과를 보고한다:

```
[opal-skill-creator 완료]
- 스킬: {name}
- 경로: {SKILL.md 경로}
- 유형: {프레임워크 / OPAL 전용}
- 버전: v{버전}
- 레지스트리: 등록 완료
- 에이전트: {생성됨 / 해당 없음}
```

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-03-20 | 초기 작성 |
