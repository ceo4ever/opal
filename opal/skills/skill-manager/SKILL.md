---
name: skill-manager
description: |
  OPAL 커뮤니티 스킬 카탈로그 검색 및 설치 관리.
  "스킬 검색", "스킬 찾아줘", "○○ 관련 스킬 있어?", "스킬 설치해줘",
  "설치된 스킬 목록", "스킬 삭제해줘" 시 사용.
---

# Skill Manager

커뮤니티 스킬을 검색, 설치, 관리하는 OPAL 전용 스킬이다.

## 프로세스

### 1. 스킬 검색

사용자가 특정 기능의 스킬을 찾을 때:

1. `~/.opal/catalog/skills-catalog.md`를 Read로 읽는다
2. 사용자 요청 키워드와 매칭하여 관련 스킬을 찾는다
3. 결과를 테이블로 제시한다:

```
| 스킬명 | 설명 | 상태 |
|--------|------|------|
| anthropics/pdf | PDF 추출/생성/폼 처리 | ✅ 설치됨 |
| openai/playwright | 브라우저 자동화 | 미설치 |
```

### 2. 스킬 설치

카탈로그에서 찾은 미설치 스킬을 설치할 때:

1. 카탈로그에서 소스 URL을 확인한다
2. 임시 디렉토리에 `git clone --depth 1`으로 리포를 clone한다
3. 필요한 스킬 디렉토리를 추출한다
4. OPAL 커뮤니티 스킬 디렉토리에 복사한다:

```
~/.opal/community-skills/{vendor}/{skill}/
```

5. 임시 디렉토리를 정리한다
6. `~/.opal/references/skills.md`에 새 스킬 항목을 추가한다

### 3. 설치된 스킬 목록

```bash
ls ~/.opal/community-skills/
```

벤더별로 그룹핑하여 표시한다.

### 4. 스킬 삭제

사용자가 삭제를 요청하면:

1. 삭제 대상 확인 (벤더/스킬명)
2. 해당 디렉토리를 `rm -rf`로 삭제
3. 결과 보고

## 설치 경로 규칙

커뮤니티 스킬은 OPAL 내부(`~/.opal/community-skills/`)에만 설치한다.
OPAL 에이전트는 `~/.opal/references/skills.md`를 통해 이 스킬들을 인지하고 활용한다.
플랫폼 네이티브 skills/ 디렉토리에는 복사하지 않는다.

```
~/.opal/community-skills/
├── anthropics/
│   ├── docx/SKILL.md
│   └── pdf/SKILL.md
├── vercel-labs/
│   └── react-best-practices/SKILL.md
└── trailofbits/
    └── modern-python/SKILL.md
```

## 참고

- 카탈로그 소스: [ceo4ever/awesome-agent-skills](https://github.com/ceo4ever/awesome-agent-skills)
- 기본 번들 스킬(31개)은 `install-mac.sh`로 자동 설치된다
- 추가 스킬은 이 스킬을 통해 온디맨드로 설치한다
