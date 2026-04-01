# DONE: OPAL JSON 레지스트리 + 파싱 도구 개발

> 완료일: 2026-03-29

## 변경 요약

### 신규 생성
- **opal/core/references/opal-skills-registry.json** — 프레임워크 25개 스킬 (otp 5 + dtp 8 + standalone 5 + opal 7)
- **opal/core/references/community-skills-registry.json** — 커뮤니티 31개 스킬 (anthropics 18 + vercel-labs 5 + google-labs-code 5 + trailofbits 1 + getsentry 1 + openai 1)
- **opal/tools/skill-registry/skill-registry.js** — Node.js CLI 파싱 도구 (match/get/list/validate)
- **opal/tools/check-env.js** — Node.js 환경 체크

### 수정
- **opal/core/AGENT.md** — 부트스트랩 3단계: CLI 도구 확인 (컨텍스트 0줄), 7단계(스킬 가이드 브리핑) 삭제, 단계 번호 재조정
- **opal/core/references/skills.md** — 스킬 테이블 전부 제거, 도구 사용법 + 기술 스택별 추천만 유지
- **opal/skills/opal-skill-manager/SKILL.md** — skills.md 참조 5곳 → JSON 도구로 대체
- **scripts/install-mac.sh** — tools 배포 + Node.js 체크 추가

### 삭제
- **opal/core/references/skill-guide.md** — JSON 도구가 대체

## 아키텍처

```
opal/core/references/                    ← 데이터 (SSOT)
  ├── opal-skills-registry.json          프레임워크 25개 (그룹: otp/dtp/standalone/opal)
  ├── community-skills-registry.json     커뮤니티 31개 (그룹: 벤더별)
  └── skills.md                          기술 스택별 추천만 (폴백용)

opal/tools/                              ← 도구 (코드)
  ├── check-env.js                       Node.js 환경 체크
  └── skill-registry/
      └── skill-registry.js              CLI (match/get/list/validate)
```

## 테스트 결과

| 테스트 | 결과 |
|--------|------|
| validate (56개 스킬) | ✅ valid: true |
| match: `//otpds` (약어, 앞/뒤/중간) | ✅ otp-dev-short |
| match: `//opi`, `//opdp` (OPAL 약어) | ✅ opal-project-init, opal-project-dev-pilot |
| match: "스킬 검색해줘" (OPAL 자연어) | ✅ opal-skill-manager |
| match: "API 분석해줘" (standalone 자연어) | ✅ api-analyzer |
| match: "문서 작성해줘" (otp 자연어) | ✅ otp-write |
| match: "코드 리뷰해줘" (커뮤니티 자연어) | ✅ getsentry/code-review |
| match: "Excel 파일 만들어줘" (커뮤니티) | ✅ anthropics/xlsx |
| match: "PDF 변환해줘" (커뮤니티) | ✅ anthropics/pdf |
| match: "보안 리뷰해줘" (커뮤니티) | ✅ openai/security-best-practices |
| match: "shadcn 컴포넌트" (커뮤니티) | ✅ vercel-labs/shadcn |
| list --group=otp | ✅ 5개 |
| list --group=opal | ✅ 7개 |
| list --group=anthropics | ✅ 18개 |
| check-env | ✅ node: true, v22.14.0 |
