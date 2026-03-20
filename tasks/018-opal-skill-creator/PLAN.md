# PLAN: opal-skill-creator 스킬 생성

> 작성일: 2026-03-20 | 모드: Short Task | 참조: TASK.md

## 1. 코드 분석

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `~/.opal/community-skills/skill-creator/SKILL.md` | anthropics/skill-creator 커뮤니티 스킬 (래핑 대상) | X (수정 금지) |
| `skills/doc-writer/SKILL.md` | 문서 작성 표준 규칙 (의존 대상) | X |
| `skills/version-mgr/SKILL.md` | 버전 관리 규칙 (의존 대상) | X |
| `~/.opal/references/skills.md` | 스킬 레지스트리 (등록 대상) | O |
| `skills/opal-skill-creator/SKILL.md` | **신규 생성** | O |

### 현재 구현

**skill-creator (커뮤니티 스킬) 핵심 프로세스:**

1. **Capture Intent** -- 스킬의 목적, 트리거, 출력 형식을 파악
2. **Interview and Research** -- 에지 케이스, 입출력 형식, 의존성 확인
3. **Write the SKILL.md** -- YAML frontmatter(name, description) + 마크다운 본문 작성
4. **Test Cases** -- 2-3개 테스트 프롬프트 작성, evals/evals.json 저장
5. **Running and evaluating** -- 서브에이전트로 with-skill/baseline 병렬 실행, 그레이딩, 벤치마크
6. **Improving the skill** -- 피드백 기반 반복 개선
7. **Description Optimization** -- 트리거 정확도 최적화 (run_loop.py)
8. **Package and Present** -- .skill 파일 패키징

skill-creator는 범용 스킬 생성 도구이므로 OPAL 프레임워크 고유의 규격(디렉토리 구조, 레지스트리 등록, 버전 태깅, 3플랫폼 배포 규칙 등)을 알지 못한다. 이 간극을 opal-skill-creator가 메워야 한다.

**기존 프레임워크 스킬 공통 구조:**

- `skills/{skill-name}/SKILL.md` 단일 파일 구조 (대부분)
- YAML frontmatter: `name`, `description` (description에 트리거 키워드 포함, "반드시 이 스킬을 사용해야 하는 상황" 패턴)
- 필요 시 `references/` 하위 디렉토리에 상세 가이드 추가
- doc-writer 규칙 준수: 한국어 본문, 영어 코드/필드명
- version-mgr 규칙 준수: v1.0 초기 버전, 변경이력 테이블

**레지스트리 형식 (`~/.opal/references/skills.md`):**

- 프레임워크 스킬 테이블: `| 스킬 | 트리거 | 설명 |`
- 탐색 경로 6단계 우선순위 정의

### 영향 범위

- **상위 의존 (이 스킬을 호출하는 곳)**: OPAL 에이전트가 "스킬 만들어줘", "새 스킬 생성" 등의 트리거로 호출
- **하위 의존 (이 스킬이 호출하는 것)**:
  - skill-creator 커뮤니티 스킬 (1단계 콘텐츠 생성 위임)
  - version-mgr (초기 버전 v1.0 태깅)
  - doc-writer (문서 표준 규칙 참조)
- **레지스트리**: `~/.opal/references/skills.md`에 새 항목 추가 필요
- **배포**: `install-mac.sh`가 `skills/`를 3개 플랫폼에 복사하므로 추가 배포 스크립트 변경 불필요

## 2. 구현 계획

### 변경 파일

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `skills/opal-skill-creator/SKILL.md` | 신규 생성 -- 2단계 파이프라인 스킬 본문 |
| 2 | `~/.opal/references/skills.md` | 프레임워크 스킬 테이블에 opal-skill-creator 항목 추가 |

### 핵심 설계

#### SKILL.md 전체 구조

```yaml
---
name: opal-skill-creator
description: |
  **OPAL 프레임워크 스킬 생성 파이프라인**. skill-creator로 SKILL.md를 생성한 뒤, OPAL 규격 후처리(디렉토리 구조, frontmatter 보정, 레지스트리 등록, 버전 태깅)를 자동 수행합니다.
  반드시 이 스킬을 사용해야 하는 상황: "새 스킬 만들어줘", "스킬 생성", "프레임워크 스킬 추가", "스킬 작성해줘", "스킬 개선해줘", 기존 프레임워크 스킬 수정/개선 요청 시.
  커뮤니티 skill-creator를 래핑하여 OPAL 프레임워크 규격을 자동 적용합니다.
---
```

#### Phase 1: 콘텐츠 생성 (skill-creator 위임)

- skill-creator SKILL.md를 Read로 읽어 그 프로세스를 따른다
- 단, 스킬 유형(프레임워크 / OPAL 전용)에 따라 저장 경로를 미리 결정하고 skill-creator에 전달
- 신규 생성 vs 기존 개선(improve) 분기:
  - **신규**: Capture Intent부터 시작
  - **개선**: 기존 SKILL.md를 로드하여 skill-creator의 improve 플로우로 진입

#### Phase 2: OPAL 규격 후처리

skill-creator가 SKILL.md 초안을 완성하면, 아래 후처리를 순차 수행:

1. **디렉토리 구조 확정**
   - 프레임워크 스킬: `skills/{name}/SKILL.md` (+ 필요 시 `references/`)
   - OPAL 전용 스킬: `~/.opal/skills/{name}/SKILL.md`
   - 에이전트 필요 시: `agents/{platform}/` 3플랫폼 템플릿

2. **YAML frontmatter 보정**
   - `name`: kebab-case 확인
   - `description`: OPAL 트리거 패턴 적용 ("반드시 이 스킬을 사용해야 하는 상황: ..." 포함)
   - doc-writer 규칙: 한국어 본문, 영어 코드/필드명

3. **레지스트리 등록**
   - `~/.opal/references/skills.md`의 해당 섹션 테이블에 항목 추가
   - 트리거 키워드, 설명, 경로 기입

4. **버전 태깅**
   - version-mgr 규칙에 따라 v1.0 초기 버전 설정
   - 문서 하단에 변경이력 테이블 추가

5. **에이전트 생성 (선택)**
   - 스킬이 독립 컨텍스트 실행을 필요로 하면, CLAUDE.md의 "Agent 추가 시" 가이드에 따라 3플랫폼 에이전트 파일 생성
   - `agents/claude/{name}/AGENT.md`, `agents/cursor/{name}.md`, `agents/antigravity/{name}/SKILL.md`

#### 분기 로직

```
사용자 요청 수신
  ├── "새 스킬 만들어줘" → 신규 생성 모드
  │     ├── 스킬 유형 확인 (프레임워크 / OPAL 전용)
  │     ├── Phase 1: skill-creator (Capture Intent → ... → Optimize)
  │     └── Phase 2: OPAL 후처리
  │
  └── "스킬 개선해줘" / 기존 스킬명 지정 → 개선 모드
        ├── 기존 SKILL.md 로드
        ├── Phase 1: skill-creator improve 플로우
        └── Phase 2: OPAL 후처리 (레지스트리 갱신, 버전 Minor/Major 증가)
```

#### 레지스트리 등록 항목 (skills.md 추가분)

```markdown
| opal-skill-creator | "스킬 만들어줘", "새 스킬 생성", "스킬 작성", "프레임워크 스킬 추가", "스킬 개선" | OPAL 프레임워크 스킬 생성 파이프라인 (skill-creator 래핑 + 규격 후처리) |
```

## 3. 실행 체크리스트

- [x] Step 1: `skills/opal-skill-creator/SKILL.md` 작성 -- YAML frontmatter + Phase 1(skill-creator 위임) + Phase 2(OPAL 후처리) 파이프라인 본문
- [x] Step 2: `~/.opal/references/skills.md` 프레임워크 스킬 테이블에 opal-skill-creator 항목 추가
- [x] Step 3: 스킬 내부 검증 -- SKILL.md를 읽고 프로세스 흐름이 완결적인지 확인 (신규 생성, 개선 모드 모두)

## 4. QA 체크리스트

### 기능 테스트

- [ ] SKILL.md의 Phase 1이 skill-creator의 핵심 프로세스(Capture Intent ~ Optimize)를 정확히 참조하는가
- [ ] Phase 2의 5개 후처리 항목(디렉토리, frontmatter, 레지스트리, 버전, 에이전트)이 모두 정의되어 있는가
- [ ] 신규 생성 모드와 개선 모드가 명확히 분기되는가
- [ ] 프레임워크 스킬 / OPAL 전용 스킬 유형별 경로가 올바른가

### 회귀 테스트

- [ ] skill-creator 커뮤니티 스킬 자체를 수정하지 않았는가
- [ ] 기존 스킬(doc-writer, version-mgr)과의 의존 관계가 올바르게 명시되어 있는가
- [ ] 레지스트리 테이블 형식이 기존 항목과 일관적인가

### 코드 품질

- [ ] 한국어 본문 / 영어 코드 규칙을 준수하는가
- [ ] YAML frontmatter 형식이 기존 스킬과 동일한 패턴인가
- [ ] SKILL.md가 500줄 이하로 유지되는가 (skill-creator 권장)
- [ ] 프로세스 설명이 명령형(imperative)으로 작성되어 있는가
