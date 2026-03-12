# Awesome Agent Skills 카탈로그 통합 — 리서치

> 작성일: 2026-03-09 | 작성자: OPAL | 버전: v1.0

## 1. 기본 번들 스킬 확정

### Official Claude Skills (17개)

| # | 스킬 | 소스 경로 | 설명 |
|---|------|----------|------|
| 1 | anthropics/docx | anthropics/skills/tree/main/skills/docx | Word 문서 생성/편집/분석 |
| 2 | anthropics/doc-coauthoring | anthropics/skills/tree/main/skills/doc-coauthoring | 협업 문서 편집 |
| 3 | anthropics/pptx | anthropics/skills/tree/main/skills/pptx | PowerPoint 프레젠테이션 |
| 4 | anthropics/xlsx | anthropics/skills/tree/main/skills/xlsx | Excel 스프레드시트 |
| 5 | anthropics/pdf | anthropics/skills/tree/main/skills/pdf | PDF 추출/생성/폼 처리 |
| 6 | anthropics/algorithmic-art | anthropics/skills/tree/main/skills/algorithmic-art | p5.js 제너러티브 아트 |
| 7 | anthropics/canvas-design | anthropics/skills/tree/main/skills/canvas-design | PNG/PDF 비주얼 디자인 |
| 8 | anthropics/frontend-design | anthropics/skills/tree/main/skills/frontend-design | 프론트엔드 UI/UX 개발 |
| 9 | anthropics/slack-gif-creator | anthropics/skills/tree/main/skills/slack-gif-creator | Slack용 애니메이션 GIF |
| 10 | anthropics/theme-factory | anthropics/skills/tree/main/skills/theme-factory | 프로페셔널 테마 생성 |
| 11 | anthropics/web-artifacts-builder | anthropics/skills/tree/main/skills/web-artifacts-builder | React+Tailwind HTML 아티팩트 |
| 12 | anthropics/mcp-builder | anthropics/skills/tree/main/skills/mcp-builder | MCP 서버 생성 가이드 |
| 13 | anthropics/webapp-testing | anthropics/skills/tree/main/skills/webapp-testing | Playwright 웹앱 테스트 |
| 14 | anthropics/brand-guidelines | anthropics/skills/tree/main/skills/brand-guidelines | 브랜드 컬러/타이포 적용 |
| 15 | anthropics/internal-comms | anthropics/skills/tree/main/skills/internal-comms | 상태 보고서/뉴스레터 |
| 16 | anthropics/skill-creator | anthropics/skills/tree/main/skills/skill-creator | 스킬 작성 가이드 |
| 17 | anthropics/template | anthropics/skills/tree/main/template | 스킬 기본 템플릿 |

### Skills by Google Labs — Stitch (6개)

| # | 스킬 | 소스 경로 | 설명 |
|---|------|----------|------|
| 18 | google-labs-code/design-md | google-labs-code/stitch-skills/tree/main/skills/design-md | DESIGN.md 관리 |
| 19 | google-labs-code/enhance-prompt | google-labs-code/stitch-skills/tree/main/skills/enhance-prompt | 프롬프트 개선 |
| 20 | google-labs-code/react-components | google-labs-code/stitch-skills/tree/main/skills/react-components | Stitch→React 변환 |
| 21 | google-labs-code/remotion | google-labs-code/stitch-skills/tree/main/skills/remotion | 워크스루 영상 생성 |
| 22 | google-labs-code/shadcn-ui | google-labs-code/stitch-skills/tree/main/skills/shadcn-ui | shadcn/ui 컴포넌트 빌드 |
| 23 | google-labs-code/stitch-loop | google-labs-code/stitch-skills/tree/main/skills/stitch-loop | 디자인→코드 반복 루프 |

**합계: 23개 스킬**

## 2. 설치 구조 설계

### 기본 번들 설치 위치

```
~/.opal/community-skills/
├── anthropics/
│   ├── docx/SKILL.md
│   ├── doc-coauthoring/SKILL.md
│   ├── pptx/SKILL.md
│   └── ... (17개)
└── google-labs-code/
    ├── design-md/SKILL.md
    ├── enhance-prompt/SKILL.md
    └── ... (6개)
```

`~/.opal/community-skills/`에 중앙 저장하고, AGENT.md에서 이 경로를 스킬 탐색 경로로 추가한다.

### 설치 방법

install-mac.sh에서 OPAL 설치 시:
1. `git clone --depth 1 https://github.com/anthropics/skills.git` (임시 디렉토리)
2. `skills/` 하위의 23개 디렉토리를 `~/.opal/community-skills/anthropics/`로 복사
3. `git clone --depth 1 https://github.com/google-labs-code/stitch-skills.git` (임시 디렉토리)
4. `skills/` 하위의 6개 디렉토리를 `~/.opal/community-skills/google-labs-code/`로 복사
5. 임시 디렉토리 정리

## 3. 카탈로그 설계 (방법 A)

### 카탈로그 파일: `~/.opal/catalog/skills-catalog.md`

```markdown
# OPAL Skills Catalog

## 검색 방법
AI가 이 파일을 Read하여 사용자 요청에 맞는 스킬을 검색한다.

## 카탈로그

| 카테고리 | 스킬명 | 설명 | 소스 URL | 설치 여부 |
|----------|--------|------|----------|----------|
| Official Claude | anthropics/docx | Word 문서 생성/편집 | https://github.com/... | ✅ 설치됨 |
| Community | stripe/stripe-best-practices | Stripe 베스트 프랙티스 | https://github.com/... | - |
...
```

### 카탈로그 생성 방법

`templates/opal/catalog/skills-catalog.md`에 549개+ 스킬을 정리하여 소스에 포함.
install-mac.sh에서 `~/.opal/catalog/`에 복사.

## 4. skill-manager 스킬 설계

### 역할

- 카탈로그에서 스킬 검색
- 외부 스킬 설치 (git clone → community-skills/ 배치)
- 설치된 스킬 목록 조회
- 스킬 삭제

### 트리거

- "스킬 검색", "○○ 관련 스킬 있어?", "스킬 설치해줘", "설치된 스킬 목록"

| 버전 | 날짜 | 작성자 | 변경내용 |
|------|------|--------|---------|
| v1.0 | 2026-03-09 | OPAL | 최초 작성 |
