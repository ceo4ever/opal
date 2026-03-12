# Awesome Agent Skills 카탈로그 통합 — 구현 계획

> 작성일: 2026-03-09 | 작성자: OPAL | 버전: v1.0

## 파일 변경 목록

### 신규 생성

| # | 파일 | 설명 |
|---|------|------|
| 1 | `templates/opal/catalog/skills-catalog.md` | 549개+ 스킬 카탈로그 (검색용) |
| 2 | `templates/opal/skills/skill-manager/SKILL.md` | 스킬 검색/설치/관리 스킬 |

### 수정

| # | 파일 | 변경 내용 |
|---|------|----------|
| 3 | `scripts/install-mac.sh` | `install_opal()`에 기본 번들 설치 + 카탈로그 복사 추가 |
| 4 | `templates/opal/core/AGENT.md` | 스킬 참조에 community-skills 경로 + skill-manager 추가 |

**합계: 신규 2 + 수정 2 = 4개 파일**

## 세부 설계

### 1. skills-catalog.md

549개+ 스킬을 카테고리별로 정리한 Markdown 테이블.

구조:
```
# OPAL Skills Catalog
> ceo4ever/awesome-agent-skills 기반

## 사용법
(AI가 이 파일을 Read하여 검색하는 절차)

## Official Claude Skills
| 스킬명 | 설명 | 소스 | 기본설치 |
...

## Google Labs (Stitch)
...

## Community — Development
...
(전체 카테고리 반복)
```

### 2. skill-manager SKILL.md

```yaml
---
name: skill-manager
description: |
  OPAL 스킬 카탈로그 검색 및 설치 관리.
  "스킬 검색", "○○ 관련 스킬", "스킬 설치", "설치된 스킬 목록" 시 사용.
---
```

프로세스:
1. 검색: `~/.opal/catalog/skills-catalog.md` Read → 키워드 매칭
2. 설치: git clone → `~/.opal/community-skills/{vendor}/{skill}/` 배치
3. 목록: `~/.opal/community-skills/` 탐색
4. 삭제: 디렉토리 제거

### 3. install-mac.sh 수정

`install_opal()` 함수에 추가:

```bash
install_basic_skills() {
    local tmp=$(mktemp -d)
    local cs_dir="$opal_home/community-skills"
    
    # Anthropic Official Skills (17개)
    git clone --depth 1 https://github.com/anthropics/skills.git "$tmp/anthropics"
    mkdir -p "$cs_dir/anthropics"
    for skill in docx doc-coauthoring pptx xlsx pdf ...; do
        cp -r "$tmp/anthropics/skills/$skill" "$cs_dir/anthropics/"
    done
    
    # Google Labs Stitch (6개)
    git clone --depth 1 https://github.com/google-labs-code/stitch-skills.git "$tmp/google-labs"
    mkdir -p "$cs_dir/google-labs-code"
    for skill in design-md enhance-prompt ...; do
        cp -r "$tmp/google-labs/skills/$skill" "$cs_dir/google-labs-code/"
    done
    
    rm -rf "$tmp"
}
```

### 4. AGENT.md 수정

스킬 참조 섹션에 추가:
```
### 커뮤니티 스킬 (~/.opal/community-skills/)
- 기본 설치: Anthropic 공식 17개 + Google Labs Stitch 6개
- 추가 설치: skill-manager 스킬로 검색/설치
- 카탈로그: ~/.opal/catalog/skills-catalog.md
```

OPAL 전용 스킬에 `skill-manager` 추가.

| 버전 | 날짜 | 작성자 | 변경내용 |
|------|------|--------|---------|
| v1.0 | 2026-03-09 | OPAL | 최초 작성 |
