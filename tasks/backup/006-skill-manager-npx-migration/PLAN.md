# PLAN: skill-manager npx skills 전환

> 작성일: 2026-03-12 | 작업 유형: 기능 개선

## 구현 순서

1. skill-manager SKILL.md 전면 재작성
2. install-mac.sh에서 카탈로그 복사 로직 제거
3. opal/catalog/ 디렉토리 삭제
4. AGENT.md에서 catalog 참조 제거
5. references/skills.md에서 skill-manager 설명 업데이트
6. CLAUDE.md, README.md 반영

## 파일별 상세 설계

### 1. opal/skills/skill-manager/SKILL.md (전면 재작성)

**검색 프로세스 변경:**

```
기존: skills-catalog.md Read → 키워드 매칭
변경: references/skills.md에서 설치됨 확인 → 없으면 npx skills find [query]
```

**설치 프로세스 변경:**

```
기존: 카탈로그에서 URL 확인 → git clone → 복사
변경: npx skills find 결과에서 owner/repo 확인 → git clone --depth 1 → 복사
      → references/skills.md에 항목 추가
```

**Node.js 폴백 추가:**
- `npx` 실행 실패 시 skills.sh URL 안내

**유지 항목:**
- 설치 경로: `~/.opal/community-skills/{vendor}/{skill}/`
- 설치된 스킬 목록: `ls ~/.opal/community-skills/`
- 스킬 삭제: `rm -rf` + references/skills.md에서 항목 제거

### 2. scripts/install-mac.sh

`install_opal()` 함수에서 카탈로그 복사 블록 제거:

```bash
# 삭제 대상 (290-297행)
local catalog_src="$FRAMEWORK_ROOT/opal/catalog"
local catalog_dst="$opal_home/catalog"
if [[ -d "$catalog_src" ]]; then
    mkdir -p "$catalog_dst"
    cp -Rf "$catalog_src"/. "$catalog_dst"/
    success "스킬 카탈로그 → $catalog_dst/"
fi
```

### 3. opal/catalog/ 삭제

`opal/catalog/skills-catalog.md` 파일 및 `opal/catalog/` 디렉토리 삭제.

### 4. opal/core/AGENT.md

catalog/ 참조가 있으면 제거. 현재 AGENT.md에는 직접적인 catalog 참조가 없으므로 확인만.

### 5. opal/core/references/skills.md

skill-manager 트리거 설명을 업데이트:

```
기존: "스킬 검색", "스킬 설치해줘", "설치된 스킬 목록"
변경: "스킬 검색", "스킬 찾아줘", "스킬 설치해줘", "설치된 스킬", "스킬 삭제"
```

### 6. CLAUDE.md

소스 구조에서 `catalog/` 항목 제거:

```
기존: ├── catalog/                     스킬 카탈로그 (skills-catalog.md)
변경: (삭제)
```

### 7. README.md

- 소스 구조에서 `catalog/` 항목 제거
- OPAL 스킬 설명에서 카탈로그 참조를 npx skills로 변경

## 테스트 전략

- `bash -n install-mac.sh` — 문법 검증
- 카탈로그 파일 삭제 후 다른 파일에서 참조가 남아있지 않은지 확인
- skill-manager SKILL.md의 프로세스 흐름이 논리적으로 완결되는지 검토
