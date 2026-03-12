---
name: skill-manager
description: |
  OPAL 커뮤니티 스킬 검색, 설치, 관리.
  "스킬 검색", "스킬 찾아줘", "○○ 관련 스킬 있어?", "스킬 설치해줘",
  "설치된 스킬 목록", "설치된 스킬", "스킬 삭제해줘" 시 사용.
---

# Skill Manager

커뮤니티 스킬을 검색, 설치, 관리하는 OPAL 전용 스킬이다.
검색에는 `npx skills` CLI([vercel-labs/skills](https://github.com/vercel-labs/skills))를 활용한다.

## 프로세스

### 1. 스킬 검색

사용자가 특정 기능의 스킬을 찾을 때:

**1단계: 설치된 스킬 확인**

`~/.opal/references/skills.md`를 Read로 읽어 이미 설치된 스킬 중 매칭되는 것이 있는지 확인한다.

- 있으면: "이미 설치되어 있습니다" + 경로 안내 → 종료
- 없으면: 2단계로 진행

**2단계: 생태계 검색**

```bash
npx skills find [query]
```

실행 결과에서 관련 스킬을 찾아 사용자에게 표시한다:

```
| 스킬명 | 설명 | 설치 명령 |
|--------|------|----------|
| owner/repo@skill | 설명 | npx skills add owner/repo@skill |
```

**폴백 (npx 실행 실패 시):**

Node.js가 설치되어 있지 않으면 아래와 같이 안내한다:

```
npx 명령을 실행할 수 없습니다. 아래 방법으로 스킬을 검색해주세요:

- 웹 카탈로그: https://skills.sh/
- Node.js 설치 후: npx skills find [query]
```

### 2. 스킬 설치

검색 결과에서 사용자가 설치를 요청하면:

1. 검색 결과의 `owner/repo@skill` 정보에서 GitHub 저장소 URL을 구성한다
2. 임시 디렉토리에 `git clone --depth 1 https://github.com/{owner}/{repo}.git`으로 clone한다
3. 해당 스킬 디렉토리를 추출한다
4. OPAL 커뮤니티 스킬 디렉토리에 복사한다:

```
~/.opal/community-skills/{vendor}/{skill}/
```

5. 임시 디렉토리를 정리한다
6. `~/.opal/references/skills.md`의 커뮤니티 스킬 섹션에 새 항목을 추가한다

### 3. 설치된 스킬 목록

```bash
ls ~/.opal/community-skills/
```

벤더별로 그룹핑하여 표시한다. `references/skills.md`의 커뮤니티 스킬 섹션과 대조하여 보여준다.

### 4. 스킬 삭제

사용자가 삭제를 요청하면:

1. 삭제 대상 확인 (벤더/스킬명)
2. 해당 디렉토리를 `rm -rf`로 삭제
3. `~/.opal/references/skills.md`에서 해당 항목을 제거한다
4. 결과 보고

### 5. 스킬 업데이트 확인

```bash
npx skills check
```

설치된 스킬의 업데이트 가능 여부를 확인한다. (Node.js 필요)

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

- 스킬 검색 엔진: [skills.sh](https://skills.sh/) (vercel-labs/skills)
- 기본 번들 스킬(31개)은 `install-mac.sh`로 자동 설치된다
- 추가 스킬은 이 스킬을 통해 온디맨드로 검색/설치한다
