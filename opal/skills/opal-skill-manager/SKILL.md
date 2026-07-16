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

스킬 레지스트리 도구로 이미 설치된 스킬 중 매칭되는 것이 있는지 확인한다:

```bash
node ~/.opal/tools/skill-registry/skill-registry.js match "{검색어}"
```

- 있으면: 설치된 스킬 정보를 안내하고, "추가로 다른 스킬도 검색할까요?"를 물어본다
  - 사용자가 원하면: 2단계로 진행
  - 사용자가 불필요하면: 종료
- 없으면: 바로 2단계로 진행

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
6. `~/.opal/references/community-skills-registry.json`에 새 스킬 항목을 추가한다

### 3. 설치된 스킬 목록

```bash
ls ~/.opal/community-skills/
```

벤더별로 그룹핑하여 표시한다. `community-skills-registry.json`과 대조하여 보여준다:

```bash
node ~/.opal/tools/skill-registry/skill-registry.js list --group=community
```

### 4. 스킬 삭제

사용자가 삭제를 요청하면:

1. 삭제 대상 확인 (벤더/스킬명)
2. 해당 디렉토리를 `rm -rf`로 삭제
3. `~/.opal/references/community-skills-registry.json`에서 해당 항목을 제거한다
4. 결과 보고

### 5. 스킬 업데이트 확인

```bash
npx skills check
```

설치된 스킬의 업데이트 가능 여부를 확인한다. (Node.js 필요)

## 설치 경로 규칙

커뮤니티 스킬은 OPAL 내부(`~/.opal/community-skills/`)에만 설치한다.
OPAL 에이전트는 `~/.opal/references/community-skills-registry.json`을 통해 이 스킬들을 인지하고 활용한다.
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
- 커뮤니티 스킬 SSOT: `npx skills` CLI — OPAL은 번들로 배포하지 않음. 사용자가 `//skill-manager` 또는 `// 커맨드` 첫 호출 시 동의 prompt를 거쳐 fetch.
- 설치 위치: `~/.opal/community-skills/{owner}/{skill}/SKILL.md`
- 레지스트리: `~/.opal/references/community-skills-registry.json` (v2 메타데이터 카탈로그 — 트리거 + source_repo + license)

### 6. `// 커맨드` 미설치 매칭 시 자동 설치·실행

알투가 `//pdf` 같은 community 트리거를 매칭했는데 skill-registry가 `installed: false`로 응답하면,
**라이선스가 확인된 스킬은 동의 대기 없이 자동 설치·실행**한다. 문제 있는 라이선스(미확인, Unknown)만 게이트한다.

> 근거: 소유자(캡틴) 확정 — "문제 있는 라이선스만 아니면 무조건 설치·실행" (064).

**분기 판정** (skill-registry `match` 응답의 `license`·`source_repo` 기준):

1. `license ≠ "Unknown"` (라이선스 확인됨) + `source_repo` 있음 → **자동 설치·실행** (동의 prompt 없음):
   - 비차단 통지 1줄만 표시:
     ```
     [자동 설치] {source_repo} · {license} · commit {commit_sha || "미고정(HEAD)"}
     ```
   - `npx skills add {source_repo}` 호출
   - 설치 완료 후 `~/.opal/community-skills/{owner}/{skill}/SKILL.md`를 Read하여 즉시 절차 실행
2. `license == "Unknown"` (라이선스 미확인) → **설치 전 확인 게이트 유지** (자동 우회 금지):
   ```
   이 스킬은 라이선스가 확인되지 않았습니다 (Unknown License) — proceed at your own risk.
   - 출처: {source_repo}
   - commit SHA: {commit_sha || "미고정 (HEAD 가변)"}

   정말로 설치하시겠습니까? (y/N)
   ```
   - 디폴트는 `N` (입력 없이 Enter 시 거부)
   - 수락(`y`): `npx skills add {source_repo}` 호출 → SKILL.md Read → 즉시 절차 실행
   - 거부(`N`): "수동 설치는 `//skill-manager`로 — `npx skills find {keyword}`로 검색 후 설치하세요" 안내 후 종료
   - §1 스킬 검색 결과에서도 Unknown 라이선스 항목에는 "⚠️ 라이선스 미확인" 경고를 표시한다.
3. `source_repo`가 `null` (registry에 미등재):
   - "이 스킬은 vercel-labs/skills 카탈로그에 미등재. 수동 설치는 `//skill-manager`로" 안내

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.1 | 2026-05-10 17:00 KST | "기본 번들 31개" 표현 제거 + fetch 흐름 SSOT 강조 + `// 커맨드` 미설치 매칭 시 자동 fetch 흐름 추가 (142) |
| v1.2 | 2026-05-10 21:00 KST | Unknown 라이선스 두 번째 확인 + commit_sha 노출 + 빨간 경고 메시지 추가 (144) |
| v1.3 | 2026-07-16 14:59 KST | §6 미설치 매칭 → 자동 설치·실행 (라이선스 확인 스킬 동의 게이트 제거, Unknown만 게이트 유지) (064) |
