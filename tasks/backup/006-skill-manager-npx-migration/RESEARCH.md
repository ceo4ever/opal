# RESEARCH: skill-manager npx skills 전환

> 작성일: 2026-03-12 | 작업 유형: 기능 개선

## 1. npx skills CLI 분석

### 핵심 명령어

| 명령어 | 설명 |
|--------|------|
| `npx skills find [query]` | 대화형 스킬 검색 (키워드 기반) |
| `npx skills add <owner/repo@skill>` | 스킬 설치 |
| `npx skills add <pkg> -g -y` | 글로벌 설치 (확인 생략) |
| `npx skills check` | 업데이트 확인 |
| `npx skills update` | 전체 업데이트 |

### 설치 경로

- **프로젝트 스코프** (기본): `./<agent>/skills/`
- **글로벌 스코프** (`-g`): `~/<agent>/skills/`
- **커스텀 경로**: `~/.skills-cli/config.json`으로 설정 가능 (개발 중, Issue #209)

### OPAL 경로와의 호환성

`npx skills add`의 기본 경로(`~/<agent>/skills/`)는 OPAL의 경로(`~/.opal/community-skills/`)와 다르다.
커스텀 경로 설정 기능이 아직 개발 중이므로, **검색에만 npx skills를 사용하고 설치는 기존 방식(git clone)을 유지**하는 것이 현실적이다.

## 2. 전환 전략

### 검색: npx skills find (대체)

```
사용자: "PDF 관련 스킬 있어?"

1단계: references/skills.md에서 설치된 스킬 중 매칭 확인
  → 있으면 바로 안내

2단계: 없으면 npx skills find pdf 실행
  → 실시간 생태계 검색 결과 표시
  → 사용자에게 설치 여부 확인
```

### 설치: git clone 유지

`npx skills add`가 OPAL 경로를 지원하지 않으므로:
1. `npx skills find` 결과에서 `owner/repo@skill` 정보 추출
2. `git clone --depth 1 https://github.com/{owner}/{repo}.git` 실행
3. 해당 스킬 디렉토리를 `~/.opal/community-skills/{vendor}/{skill}/`로 복사
4. `~/.opal/references/skills.md`에 항목 추가

### 폴백: Node.js 미설치 시

`npx` 명령이 실패하면:
- "Node.js가 설치되어 있지 않습니다. skills.sh에서 직접 검색해주세요." 안내
- [skills.sh](https://skills.sh/) URL 제공

## 3. 영향 범위

### 삭제 대상

| 파일 | 이유 |
|------|------|
| `opal/catalog/skills-catalog.md` | npx skills find로 대체 |
| `opal/catalog/` 디렉토리 | 카탈로그 파일 삭제 후 빈 디렉토리 |

### 수정 대상

| 파일 | 변경 내용 |
|------|----------|
| `opal/skills/skill-manager/SKILL.md` | 검색→npx skills find, 카탈로그 참조 제거 |
| `opal/core/references/skills.md` | skill-manager 트리거 설명 업데이트 |
| `opal/core/AGENT.md` | catalog/ 참조가 있으면 제거 |
| `scripts/install-mac.sh` | 카탈로그 복사 로직 제거 (290-297행) |
| `CLAUDE.md` | catalog/ 디렉토리 참조 제거 |
| `README.md` | catalog/ 관련 설명 업데이트 |

### 변경 없음

| 파일 | 이유 |
|------|------|
| 기본 번들 31개 | install-mac.sh로 복사, 변경 없음 |
| `~/.opal/community-skills/` | 경로 유지 |
| `references/skills.md` | 형식 유지, 내용만 약간 수정 |

## 4. 결론

- **검색**: `skills-catalog.md` → `npx skills find` (실시간, 전체 생태계)
- **설치**: git clone 방식 유지 (OPAL 경로 호환성)
- **업데이트 확인**: `npx skills check` 추가 가능 (향후)
- **카탈로그 파일**: 삭제 (역할 완전 대체)
- **Node.js 의존성**: 검색 기능에만 필요, 없으면 skills.sh URL 폴백
