# OPAL Skills Catalog

> [ceo4ever/awesome-agent-skills](https://github.com/ceo4ever/awesome-agent-skills) 기반 | 549+ skills

## 사용법

AI가 이 파일을 Read하여 사용자 요청에 맞는 스킬을 검색한다.

1. 사용자가 "○○ 관련 스킬 있어?" 요청
2. 이 파일에서 키워드 매칭으로 관련 스킬 검색
3. 결과를 사용자에게 제시
4. 설치 요청 시 `skill-manager` 스킬의 설치 프로세스 수행

**기본설치** 컬럼: ✅ = `install-mac.sh`로 자동 설치되는 기본 번들 스킬 (31개)

---

## Official Claude Skills

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| anthropics/docx | Word 문서 생성/편집/분석 | [GitHub](https://github.com/anthropics/skills/tree/main/skills/docx) | ✅ |
| anthropics/doc-coauthoring | 협업 문서 편집 | [GitHub](https://github.com/anthropics/skills/tree/main/skills/doc-coauthoring) | ✅ |
| anthropics/pptx | PowerPoint 프레젠테이션 | [GitHub](https://github.com/anthropics/skills/tree/main/skills/pptx) | ✅ |
| anthropics/xlsx | Excel 스프레드시트 | [GitHub](https://github.com/anthropics/skills/tree/main/skills/xlsx) | ✅ |
| anthropics/pdf | PDF 추출/생성/폼 처리 | [GitHub](https://github.com/anthropics/skills/tree/main/skills/pdf) | ✅ |
| anthropics/algorithmic-art | p5.js 제너러티브 아트 | [GitHub](https://github.com/anthropics/skills/tree/main/skills/algorithmic-art) | ✅ |
| anthropics/canvas-design | PNG/PDF 비주얼 디자인 | [GitHub](https://github.com/anthropics/skills/tree/main/skills/canvas-design) | ✅ |
| anthropics/frontend-design | 프론트엔드 UI/UX 개발 | [GitHub](https://github.com/anthropics/skills/tree/main/skills/frontend-design) | ✅ |
| anthropics/slack-gif-creator | Slack용 애니메이션 GIF | [GitHub](https://github.com/anthropics/skills/tree/main/skills/slack-gif-creator) | ✅ |
| anthropics/theme-factory | 프로페셔널 테마 생성 | [GitHub](https://github.com/anthropics/skills/tree/main/skills/theme-factory) | ✅ |
| anthropics/web-artifacts-builder | React+Tailwind HTML 아티팩트 | [GitHub](https://github.com/anthropics/skills/tree/main/skills/web-artifacts-builder) | ✅ |
| anthropics/mcp-builder | MCP 서버 생성 가이드 | [GitHub](https://github.com/anthropics/skills/tree/main/skills/mcp-builder) | ✅ |
| anthropics/webapp-testing | Playwright 웹앱 테스트 | [GitHub](https://github.com/anthropics/skills/tree/main/skills/webapp-testing) | ✅ |
| anthropics/brand-guidelines | 브랜드 컬러/타이포 적용 | [GitHub](https://github.com/anthropics/skills/tree/main/skills/brand-guidelines) | ✅ |
| anthropics/internal-comms | 상태 보고서/뉴스레터 | [GitHub](https://github.com/anthropics/skills/tree/main/skills/internal-comms) | ✅ |
| anthropics/skill-creator | 스킬 작성 가이드 | [GitHub](https://github.com/anthropics/skills/tree/main/skills/skill-creator) | ✅ |
| anthropics/claude-api | Claude API 연동 | [GitHub](https://github.com/anthropics/skills/tree/main/skills/claude-api) | ✅ |
| anthropics/template | 스킬 기본 템플릿 | [GitHub](https://github.com/anthropics/skills/tree/main/template) | ✅ |

## Google Labs (Stitch)

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| google-labs-code/design-md | DESIGN.md 관리 | [GitHub](https://github.com/google-labs-code/stitch-skills/tree/main/skills/design-md) | ✅ |
| google-labs-code/enhance-prompt | 프롬프트 개선 | [GitHub](https://github.com/google-labs-code/stitch-skills/tree/main/skills/enhance-prompt) | ✅ |
| google-labs-code/react-components | Stitch→React 변환 | [GitHub](https://github.com/google-labs-code/stitch-skills/tree/main/skills/react-components) | ✅ |
| google-labs-code/remotion | 워크스루 영상 생성 | [GitHub](https://github.com/google-labs-code/stitch-skills/tree/main/skills/remotion) | ✅ |
| google-labs-code/shadcn-ui | shadcn/ui 컴포넌트 빌드 | [GitHub](https://github.com/google-labs-code/stitch-skills/tree/main/skills/shadcn-ui) | ✅ |
| google-labs-code/stitch-loop | 디자인→코드 반복 루프 | [GitHub](https://github.com/google-labs-code/stitch-skills/tree/main/skills/stitch-loop) | ✅ |

## Vercel Engineering

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| vercel-labs/react-best-practices | React 베스트 프랙티스 | [GitHub](https://github.com/vercel-labs/agent-skills/tree/main/skills/react-best-practices) | ✅ |
| vercel-labs/web-design-guidelines | 웹 디자인 가이드라인 | [GitHub](https://github.com/vercel-labs/agent-skills/tree/main/skills/web-design-guidelines) | ✅ |
| vercel-labs/composition-patterns | React 컴포넌트 컴포지션 패턴 | [GitHub](https://github.com/vercel-labs/agent-skills/tree/main/skills/composition-patterns) | ✅ |
| vercel-labs/next-best-practices | Next.js 베스트 프랙티스 | [GitHub](https://github.com/vercel-labs/next-skills/tree/main/skills/next-best-practices) | ✅ |
| vercel-labs/vercel-deploy-claimable | Vercel 배포 | [GitHub](https://github.com/vercel-labs/agent-skills/tree/main/skills/claude.ai/vercel-deploy-claimable) | - |
| vercel-labs/next-cache-components | Next.js 캐싱 전략 | [GitHub](https://github.com/vercel-labs/next-skills/tree/main/skills/next-cache-components) | - |
| vercel-labs/next-upgrade | Next.js 업그레이드 | [GitHub](https://github.com/vercel-labs/next-skills/tree/main/skills/next-upgrade) | - |
| vercel-labs/react-native-skills | React Native 베스트 프랙티스 | [GitHub](https://github.com/vercel-labs/agent-skills/tree/main/skills/react-native-skills) | - |

## 코드 품질 & 보안

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| trailofbits/modern-python | uv, ruff, ty, pytest 모던 Python | [GitHub](https://github.com/trailofbits/skills/tree/main/plugins/modern-python) | ✅ |
| getsentry/code-review | 코드 리뷰 수행 | [GitHub](https://github.com/getsentry/skills/tree/main/plugins/sentry-skills/skills/code-review) | ✅ |
| openai/security-best-practices | 언어별 보안 취약점 리뷰 | [GitHub](https://github.com/openai/skills/tree/main/skills/.curated/security-best-practices) | ✅ |

## VoltAgent

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| voltagent/create-voltagent | VoltAgent 프로젝트 셋업 | [GitHub](https://github.com/VoltAgent/skills/tree/main/skills/create-voltagent) | - |
| voltagent/voltagent-best-practices | VoltAgent 아키텍처 패턴 | [GitHub](https://github.com/VoltAgent/skills/tree/main/skills/voltagent-best-practices) | - |
| voltagent/voltagent-core-reference | VoltAgent 클래스 레퍼런스 | [GitHub](https://github.com/VoltAgent/skills/tree/main/skills/voltagent-core-reference) | - |
| voltagent/voltagent-docs-bundle | VoltAgent 문서 번들 | [GitHub](https://github.com/VoltAgent/skills/tree/main/skills/voltagent-docs-bundle) | - |

## Composio

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| ComposioHQ/skills | 1000+ 외부 앱 AI 에이전트 연결 | [GitHub](https://github.com/ComposioHQ/skills) | - |

## Supabase

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| supabase/postgres-best-practices | PostgreSQL 베스트 프랙티스 | [GitHub](https://github.com/supabase/agent-skills/tree/main/skills/supabase-postgres-best-practices) | - |

## Google Gemini

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| google-gemini/gemini-skills | Gemini API/SDK 스킬 라이브러리 | [GitHub](https://github.com/google-gemini/gemini-skills) | - |

## Stripe

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| stripe/stripe-best-practices | Stripe 연동 베스트 프랙티스 | [GitHub](https://github.com/stripe/ai/tree/main/skills/stripe-best-practices) | - |
| stripe/upgrade-stripe | Stripe SDK/API 버전 업그레이드 | [GitHub](https://github.com/stripe/ai/tree/main/skills/upgrade-stripe) | - |

## CallStack

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| callstackincubator/react-native-best-practices | React Native 성능 최적화 | [GitHub](https://github.com/callstackincubator/agent-skills/blob/main/skills/react-native-best-practices/SKILL.md) | - |
| callstackincubator/github | GitHub PR/코드리뷰 워크플로우 | [GitHub](https://github.com/callstackincubator/agent-skills/tree/main/skills/github) | - |
| callstackincubator/upgrading-react-native | React Native 업그레이드 | [GitHub](https://github.com/callstackincubator/agent-skills/tree/main/skills/upgrading-react-native) | - |

## Expo

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| expo/expo-app-design | Expo 앱 디자인 | [GitHub](https://github.com/expo/skills/tree/main/plugins/expo-app-design) | - |
| expo/expo-deployment | Expo 앱 배포 | [GitHub](https://github.com/expo/skills/tree/main/plugins/expo-deployment) | - |
| expo/upgrading-expo | Expo SDK 업그레이드 | [GitHub](https://github.com/expo/skills/tree/main/plugins/upgrading-expo) | - |

## Better Auth

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| better-auth/best-practices | Better Auth 베스트 프랙티스 | [GitHub](https://github.com/better-auth/skills/tree/main/better-auth/best-practices) | - |
| better-auth/commands | Better Auth CLI 명령어 | [GitHub](https://github.com/better-auth/skills/tree/main/better-auth/commands) | - |
| better-auth/create-auth | Better Auth 인증 셋업 | [GitHub](https://github.com/better-auth/skills/tree/main/better-auth/create-auth) | - |

## Tinybird

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| tinybirdco/tinybird-best-practices | Tinybird 프로젝트 가이드라인 | [GitHub](https://github.com/tinybirdco/tinybird-agent-skills/tree/main/skills/tinybird-best-practices) | - |

## HashiCorp (Terraform)

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| hashicorp/terraform-code-generation | Terraform HCL 코드 생성 | [GitHub](https://github.com/hashicorp/agent-skills/tree/main/terraform/code-generation) | - |
| hashicorp/terraform-module-generation | Terraform 모듈 생성/리팩토링 | [GitHub](https://github.com/hashicorp/agent-skills/tree/main/terraform/module-generation) | - |
| hashicorp/terraform-provider-development | Terraform 프로바이더 개발 | [GitHub](https://github.com/hashicorp/agent-skills/tree/main/terraform/provider-development) | - |

## Sanity

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| sanity-io/sanity-best-practices | Sanity Studio/GROQ 베스트 프랙티스 | [GitHub](https://github.com/sanity-io/agent-toolkit/tree/main/skills/sanity-best-practices) | - |
| sanity-io/content-modeling-best-practices | Sanity 콘텐츠 모델링 | [GitHub](https://github.com/sanity-io/agent-toolkit/tree/main/skills/content-modeling-best-practices) | - |
| sanity-io/seo-aeo-best-practices | SEO/AEO 패턴 | [GitHub](https://github.com/sanity-io/agent-toolkit/tree/main/skills/seo-aeo-best-practices) | - |
| sanity-io/content-experimentation-best-practices | 콘텐츠 A/B 테스트 | [GitHub](https://github.com/sanity-io/agent-toolkit/tree/main/skills/content-experimentation-best-practices) | - |

## Firecrawl

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| firecrawl/firecrawl-cli | 웹 스크래핑/크롤링/검색 CLI | [GitHub](https://github.com/firecrawl/cli/tree/main/skills/firecrawl-cli) | - |
| firecrawl/firecrawl-claude-plugin | Claude Code 웹 스크래핑 플러그인 | [GitHub](https://github.com/firecrawl/firecrawl-claude-plugin) | - |

## Neon

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| neondatabase/using-neon | Neon Serverless Postgres | [GitHub](https://github.com/neondatabase/agent-skills/tree/main/skills/neon-postgres) | - |

## Cloudflare

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| dmmulroy/cloudflare-skill | Cloudflare Workers/Pages/AI 레퍼런스 | [GitHub](https://github.com/dmmulroy/cloudflare-skill/tree/main/skills/cloudflare) | - |
| cloudflare/agents-sdk | 스케줄링/RPC/MCP 서버 스테이트풀 AI 에이전트 | [GitHub](https://github.com/cloudflare/skills/tree/main/skills/agents-sdk) | - |
| cloudflare/building-ai-agent-on-cloudflare | Cloudflare AI 에이전트 빌드 | [GitHub](https://github.com/cloudflare/skills/tree/main/skills/building-ai-agent-on-cloudflare) | - |
| cloudflare/building-mcp-server-on-cloudflare | MCP 서버 빌드 (OAuth 포함) | [GitHub](https://github.com/cloudflare/skills/tree/main/skills/building-mcp-server-on-cloudflare) | - |
| cloudflare/durable-objects | Durable Objects (RPC/SQLite/WebSocket) | [GitHub](https://github.com/cloudflare/skills/tree/main/skills/durable-objects) | - |
| cloudflare/web-perf | Core Web Vitals 감사 | [GitHub](https://github.com/cloudflare/skills/tree/main/skills/web-perf) | - |
| cloudflare/wrangler | Workers/KV/R2/D1 배포 관리 | [GitHub](https://github.com/cloudflare/skills/tree/main/skills/wrangler) | - |

## ClickHouse

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| ClickHouse/agent-skills | ClickHouse 베스트 프랙티스 | [GitHub](https://github.com/ClickHouse/agent-skills) | - |

## Remotion

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| remotion-dev/remotion | React 프로그래밍 비디오 | [GitHub](https://github.com/remotion-dev/skills/tree/main/skills/remotion) | - |

## Replicate

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| replicate/replicate | AI 모델 탐색/비교/실행 | [GitHub](https://github.com/replicate/skills/tree/main/skills/replicate) | - |

## Typefully

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| typefully/typefully | SNS 콘텐츠 생성/예약/게시 | [GitHub](https://github.com/typefully/agent-skills/tree/main/skills/typefully) | - |

## Netlify

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| netlify/netlify-functions | 서버리스 API 엔드포인트 | [GitHub](https://github.com/netlify/context-and-tools/tree/main/skills/netlify-functions) | - |
| netlify/netlify-edge-functions | 엣지 미들웨어 | [GitHub](https://github.com/netlify/context-and-tools/tree/main/skills/netlify-edge-functions) | - |
| netlify/netlify-blobs | Key-value 오브젝트 스토리지 | [GitHub](https://github.com/netlify/context-and-tools/tree/main/skills/netlify-blobs) | - |
| netlify/netlify-db | 매니지드 Postgres | [GitHub](https://github.com/netlify/context-and-tools/tree/main/skills/netlify-db) | - |
| netlify/netlify-image-cdn | 이미지 최적화/변환 CDN | [GitHub](https://github.com/netlify/context-and-tools/tree/main/skills/netlify-image-cdn) | - |
| netlify/netlify-forms | HTML 폼 핸들링 | [GitHub](https://github.com/netlify/context-and-tools/tree/main/skills/netlify-forms) | - |
| netlify/netlify-frameworks | SSR 프레임워크 배포 | [GitHub](https://github.com/netlify/context-and-tools/tree/main/skills/netlify-frameworks) | - |
| netlify/netlify-caching | CDN 캐싱 설정 | [GitHub](https://github.com/netlify/context-and-tools/tree/main/skills/netlify-caching) | - |
| netlify/netlify-config | netlify.toml 설정 레퍼런스 | [GitHub](https://github.com/netlify/context-and-tools/tree/main/skills/netlify-config) | - |
| netlify/netlify-cli-and-deploy | CLI 로컬 개발/배포 | [GitHub](https://github.com/netlify/context-and-tools/tree/main/skills/netlify-cli-and-deploy) | - |
| netlify/netlify-deploy | 자동 배포 워크플로우 | [GitHub](https://github.com/netlify/context-and-tools/tree/main/skills/netlify-deploy) | - |
| netlify/netlify-ai-gateway | AI 모델 통합 게이트웨이 | [GitHub](https://github.com/netlify/context-and-tools/tree/main/skills/netlify-ai-gateway) | - |

## Google Workspace CLI

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| googleworkspace/gws-shared | 공유 인증/출력 포맷 | [GitHub](https://github.com/googleworkspace/cli/tree/main/skills/gws-shared) | - |
| googleworkspace/gws-drive | Google Drive 관리 | [GitHub](https://github.com/googleworkspace/cli/tree/main/skills/gws-drive) | - |
| googleworkspace/gws-sheets | Google Sheets 읽기/쓰기 | [GitHub](https://github.com/googleworkspace/cli/tree/main/skills/gws-sheets) | - |
| googleworkspace/gws-gmail | Gmail 관리 | [GitHub](https://github.com/googleworkspace/cli/tree/main/skills/gws-gmail) | - |
| googleworkspace/gws-calendar | Google Calendar 관리 | [GitHub](https://github.com/googleworkspace/cli/tree/main/skills/gws-calendar) | - |
| googleworkspace/gws-admin | Workspace 사용자/그룹 관리 | [GitHub](https://github.com/googleworkspace/cli/tree/main/skills/gws-admin) | - |
| googleworkspace/gws-docs | Google Docs 읽기/쓰기 | [GitHub](https://github.com/googleworkspace/cli/tree/main/skills/gws-docs) | - |
| googleworkspace/gws-slides | Google Slides 읽기/쓰기 | [GitHub](https://github.com/googleworkspace/cli/tree/main/skills/gws-slides) | - |
| googleworkspace/gws-tasks | Google Tasks 관리 | [GitHub](https://github.com/googleworkspace/cli/tree/main/skills/gws-tasks) | - |
| googleworkspace/gws-workflow | 크로스서비스 워크플로우 | [GitHub](https://github.com/googleworkspace/cli/tree/main/skills/gws-workflow) | - |

## Hugging Face

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| huggingface/hugging-face-cli | HF Hub CLI 모델/데이터 관리 | [GitHub](https://github.com/huggingface/skills/tree/main/skills/hugging-face-cli) | - |
| huggingface/hugging-face-datasets | 데이터셋 관리 | [GitHub](https://github.com/huggingface/skills/tree/main/skills/hugging-face-datasets) | - |
| huggingface/hugging-face-evaluation | 모델 평가 | [GitHub](https://github.com/huggingface/skills/tree/main/skills/hugging-face-evaluation) | - |
| huggingface/hugging-face-jobs | HF 인프라 컴퓨트 잡 | [GitHub](https://github.com/huggingface/skills/tree/main/skills/hugging-face-jobs) | - |
| huggingface/hugging-face-model-trainer | SFT/DPO/GRPO 모델 트레이닝 | [GitHub](https://github.com/huggingface/skills/tree/main/skills/hugging-face-model-trainer) | - |
| huggingface/hugging-face-paper-publisher | HF Hub 논문 게시 | [GitHub](https://github.com/huggingface/skills/tree/main/skills/hugging-face-paper-publisher) | - |
| huggingface/hugging-face-tool-builder | HF API 스크립트 빌더 | [GitHub](https://github.com/huggingface/skills/tree/main/skills/hugging-face-tool-builder) | - |
| huggingface/hugging-face-trackio | ML 실험 트래킹 | [GitHub](https://github.com/huggingface/skills/tree/main/skills/hugging-face-trackio) | - |

## Trail of Bits (Security)

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| trailofbits/ask-questions-if-underspecified | 모호한 요구사항 질의 | [GitHub](https://github.com/trailofbits/skills/tree/main/plugins/ask-questions-if-underspecified) | - |
| trailofbits/audit-context-building | 코드 아키텍처 딥 분석 | [GitHub](https://github.com/trailofbits/skills/tree/main/plugins/audit-context-building) | - |
| trailofbits/building-secure-contracts | 스마트 컨트랙트 보안 (6 블록체인) | [GitHub](https://github.com/trailofbits/skills/tree/main/plugins/building-secure-contracts) | - |
| trailofbits/differential-review | 보안 중심 diff 리뷰 | [GitHub](https://github.com/trailofbits/skills/tree/main/plugins/differential-review) | - |
| trailofbits/insecure-defaults | 비보안 기본 설정 탐지 | [GitHub](https://github.com/trailofbits/skills/tree/main/plugins/insecure-defaults) | - |
| trailofbits/property-based-testing | 속성 기반 테스트 | [GitHub](https://github.com/trailofbits/skills/tree/main/plugins/property-based-testing) | - |
| trailofbits/semgrep-rule-creator | Semgrep 규칙 생성 | [GitHub](https://github.com/trailofbits/skills/tree/main/plugins/semgrep-rule-creator) | - |
| trailofbits/sharp-edges | 위험 API/설정 식별 | [GitHub](https://github.com/trailofbits/skills/tree/main/plugins/sharp-edges) | - |
| trailofbits/static-analysis | 정적 분석 (CodeQL/Semgrep/SARIF) | [GitHub](https://github.com/trailofbits/skills/tree/main/plugins/static-analysis) | - |
| trailofbits/variant-analysis | 패턴 기반 취약점 검색 | [GitHub](https://github.com/trailofbits/skills/tree/main/plugins/variant-analysis) | - |

## Sentry

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| getsentry/agents-md | AGENTS.md 생성/관리 | [GitHub](https://github.com/getsentry/skills/tree/main/plugins/sentry-skills/skills/agents-md) | - |
| getsentry/claude-settings-audit | Claude 설정 감사 | [GitHub](https://github.com/getsentry/skills/tree/main/plugins/sentry-skills/skills/claude-settings-audit) | - |
| getsentry/commit | 커밋 베스트 프랙티스 | [GitHub](https://github.com/getsentry/skills/tree/main/plugins/sentry-skills/skills/commit) | - |
| getsentry/create-pr | PR 생성 | [GitHub](https://github.com/getsentry/skills/tree/main/plugins/sentry-skills/skills/create-pr) | - |
| getsentry/find-bugs | 코드 버그 찾기 | [GitHub](https://github.com/getsentry/skills/tree/main/plugins/sentry-skills/skills/find-bugs) | - |
| getsentry/iterate-pr | PR 피드백 반영 | [GitHub](https://github.com/getsentry/skills/tree/main/plugins/sentry-skills/skills/iterate-pr) | - |

## OpenAI

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| openai/cloudflare-deploy | Cloudflare 배포 | [GitHub](https://github.com/openai/skills/tree/main/skills/.curated/cloudflare-deploy) | - |
| openai/develop-web-game | Playwright 웹 게임 개발 | [GitHub](https://github.com/openai/skills/tree/main/skills/.curated/develop-web-game) | - |
| openai/doc | .docx 문서 처리 | [GitHub](https://github.com/openai/skills/tree/main/skills/.curated/doc) | - |
| openai/figma-implement-design | Figma→코드 구현 | [GitHub](https://github.com/openai/skills/tree/main/skills/.curated/figma-implement-design) | - |
| openai/figma | Figma 디자인 컨텍스트 | [GitHub](https://github.com/openai/skills/tree/main/skills/.curated/figma) | - |
| openai/gh-address-comments | GitHub PR 코멘트 대응 | [GitHub](https://github.com/openai/skills/tree/main/skills/.curated/gh-address-comments) | - |
| openai/gh-fix-ci | GitHub Actions CI 디버깅 | [GitHub](https://github.com/openai/skills/tree/main/skills/.curated/gh-fix-ci) | - |
| openai/imagegen | OpenAI 이미지 생성/편집 | [GitHub](https://github.com/openai/skills/tree/main/skills/.curated/imagegen) | - |
| openai/jupyter-notebook | Jupyter 노트북 생성 | [GitHub](https://github.com/openai/skills/tree/main/skills/.curated/jupyter-notebook) | - |
| openai/linear | Linear 이슈/프로젝트 관리 | [GitHub](https://github.com/openai/skills/tree/main/skills/.curated/linear) | - |
| openai/netlify-deploy | Netlify 자동 배포 | [GitHub](https://github.com/openai/skills/tree/main/skills/.curated/netlify-deploy) | - |
| openai/notion-knowledge-capture | 대화→Notion 위키 변환 | [GitHub](https://github.com/openai/skills/tree/main/skills/.curated/notion-knowledge-capture) | - |
| openai/notion-meeting-intelligence | Notion 기반 회의 준비 | [GitHub](https://github.com/openai/skills/tree/main/skills/.curated/notion-meeting-intelligence) | - |
| openai/notion-research-documentation | Notion 콘텐츠 리서치 | [GitHub](https://github.com/openai/skills/tree/main/skills/.curated/notion-research-documentation) | - |
| openai/notion-spec-to-implementation | Notion 스펙→구현 계획 | [GitHub](https://github.com/openai/skills/tree/main/skills/.curated/notion-spec-to-implementation) | - |
| openai/openai-docs | OpenAI 개발자 문서 가이드 | [GitHub](https://github.com/openai/skills/tree/main/skills/.curated/openai-docs) | - |
| openai/pdf | PDF 읽기/생성/리뷰 | [GitHub](https://github.com/openai/skills/tree/main/skills/.curated/pdf) | - |
| openai/playwright | 브라우저 자동화 | [GitHub](https://github.com/openai/skills/tree/main/skills/.curated/playwright) | - |
| openai/render-deploy | Render 클라우드 배포 | [GitHub](https://github.com/openai/skills/tree/main/skills/.curated/render-deploy) | - |
| openai/screenshot | 데스크톱/앱 스크린샷 캡처 | [GitHub](https://github.com/openai/skills/tree/main/skills/.curated/screenshot) | - |
| openai/sentry | Sentry 이슈 분석 | [GitHub](https://github.com/openai/skills/tree/main/skills/.curated/sentry) | - |
| openai/sora | Sora 비디오 생성 | [GitHub](https://github.com/openai/skills/tree/main/skills/.curated/sora) | - |
| openai/speech | TTS 오디오 생성 | [GitHub](https://github.com/openai/skills/tree/main/skills/.curated/speech) | - |
| openai/spreadsheet | 스프레드시트 생성/분석 | [GitHub](https://github.com/openai/skills/tree/main/skills/.curated/spreadsheet) | - |
| openai/transcribe | 오디오→텍스트 변환 | [GitHub](https://github.com/openai/skills/tree/main/skills/.curated/transcribe) | - |
| openai/vercel-deploy | Vercel 배포 | [GitHub](https://github.com/openai/skills/tree/main/skills/.curated/vercel-deploy) | - |
| openai/yeet | git push + PR 생성 | [GitHub](https://github.com/openai/skills/tree/main/skills/.curated/yeet) | - |

## Microsoft

> .NET, Java, Python, Rust, TypeScript, General — 100+ Azure 스킬. 전체 목록은 [GitHub](https://github.com/microsoft/skills) 참조.

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| microsoft/mcp-builder | MCP 서버 생성 가이드 | [GitHub](https://github.com/microsoft/skills/tree/main/.github/skills/mcp-builder) | - |
| microsoft/skill-creator | Azure AI 스킬 생성 가이드 | [GitHub](https://github.com/microsoft/skills/tree/main/.github/skills/skill-creator) | - |
| microsoft/frontend-ui-dark-ts | React/Tailwind 다크 테마 UI | [GitHub](https://github.com/microsoft/skills/tree/main/.github/skills/frontend-ui-dark-ts) | - |
| microsoft/zustand-store-ts | Zustand 스토어 패턴 | [GitHub](https://github.com/microsoft/skills/tree/main/.github/skills/zustand-store-ts) | - |
| microsoft/react-flow-node-ts | React Flow 노드 컴포넌트 | [GitHub](https://github.com/microsoft/skills/tree/main/.github/skills/react-flow-node-ts) | - |
| microsoft/pydantic-models-py | Pydantic 모델 API 스키마 | [GitHub](https://github.com/microsoft/skills/tree/main/.github/skills/pydantic-models-py) | - |
| microsoft/fastapi-router-py | FastAPI 라우터 CRUD/인증 | [GitHub](https://github.com/microsoft/skills/tree/main/.github/skills/fastapi-router-py) | - |

## fal.ai

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| fal-ai-community/fal-audio | TTS/STT fal.ai 오디오 | [GitHub](https://github.com/fal-ai-community/skills/blob/main/skills/claude.ai/fal-audio/SKILL.md) | - |
| fal-ai-community/fal-generate | 이미지/비디오 AI 생성 | [GitHub](https://github.com/fal-ai-community/skills/blob/main/skills/claude.ai/fal-generate/SKILL.md) | - |
| fal-ai-community/fal-image-edit | AI 이미지 편집 | [GitHub](https://github.com/fal-ai-community/skills/blob/main/skills/claude.ai/fal-image-edit/SKILL.md) | - |
| fal-ai-community/fal-platform | fal.ai 플랫폼 API | [GitHub](https://github.com/fal-ai-community/skills/blob/main/skills/claude.ai/fal-platform/SKILL.md) | - |
| fal-ai-community/fal-upscale | 이미지/비디오 AI 업스케일 | [GitHub](https://github.com/fal-ai-community/skills/blob/main/skills/claude.ai/fal-upscale/SKILL.md) | - |
| fal-ai-community/fal-workflow | AI 모델 체이닝 워크플로우 | [GitHub](https://github.com/fal-ai-community/skills/blob/main/skills/claude.ai/fal-workflow/SKILL.md) | - |

## WordPress

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| WordPress/wordpress-router | WordPress 리포 분류/라우팅 | [GitHub](https://github.com/WordPress/agent-skills/tree/trunk/skills/wordpress-router) | - |
| WordPress/wp-block-development | Gutenberg 블록 개발 | [GitHub](https://github.com/WordPress/agent-skills/tree/trunk/skills/wp-block-development) | - |
| WordPress/wp-plugin-development | 플러그인 아키텍처 | [GitHub](https://github.com/WordPress/agent-skills/tree/trunk/skills/wp-plugin-development) | - |
| WordPress/wp-rest-api | REST API 라우트/스키마 | [GitHub](https://github.com/WordPress/agent-skills/tree/trunk/skills/wp-rest-api) | - |

## Transloadit

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| transloadit/transloadit | 미디어 프로세싱 라우터 | [GitHub](https://github.com/transloadit/skills/tree/main/skills/transloadit) | - |
| transloadit/docs-transloadit-robots | 86+ 프로세싱 Robot 레퍼런스 | [GitHub](https://github.com/transloadit/skills/tree/main/skills/docs-transloadit-robots) | - |

## Binance

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| binance/crypto-market-rank | 크립토 마켓 랭킹 | [GitHub](https://github.com/binance/binance-skills-hub/tree/main/skills/binance-web3/crypto-market-rank) | - |
| binance/spot | 스팟 트레이딩 오더 관리 | [GitHub](https://github.com/binance/binance-skills-hub/tree/main/skills/binance/spot) | - |

## Community — Marketing

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| coreyhaines31/copywriting | 마케팅 카피 작성 | [GitHub](https://github.com/coreyhaines31/marketingskills/tree/main/skills/copywriting) | - |
| coreyhaines31/seo-audit | SEO 감사/진단 | [GitHub](https://github.com/coreyhaines31/marketingskills/tree/main/skills/seo-audit) | - |
| coreyhaines31/content-strategy | 콘텐츠 전략 계획 | [GitHub](https://github.com/coreyhaines31/marketingskills/tree/main/skills/content-strategy) | - |
| BrianRWagner/ai-marketing-skills | 17 마케팅 프레임워크 | [GitHub](https://github.com/BrianRWagner/ai-marketing-skills) | - |

## Community — Product Management

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| deanpeters/discovery-process | 프로덕트 디스커버리 사이클 | [GitHub](https://github.com/deanpeters/Product-Manager-Skills/tree/main/skills/discovery-process) | - |
| deanpeters/user-story | 유저 스토리 작성 | [GitHub](https://github.com/deanpeters/Product-Manager-Skills/tree/main/skills/user-story) | - |
| deanpeters/prd-development | PRD 작성 프로세스 | [GitHub](https://github.com/deanpeters/Product-Manager-Skills/tree/main/skills/prd-development) | - |
| phuryn/create-prd | PRD 생성 (8섹션 템플릿) | [GitHub](https://github.com/phuryn/pm-skills/tree/main/pm-execution/skills/create-prd) | - |
| phuryn/product-strategy | 프로덕트 전략 캔버스 | [GitHub](https://github.com/phuryn/pm-skills/tree/main/pm-product-strategy/skills/product-strategy) | - |
| phuryn/competitor-analysis | 경쟁사 분석 | [GitHub](https://github.com/phuryn/pm-skills/tree/main/pm-market-research/skills/competitor-analysis) | - |

## Community — Development & Testing

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| obra/test-driven-development | TDD 프랙티스 | [GitHub](https://github.com/obra/superpowers/blob/main/skills/test-driven-development/SKILL.md) | - |
| obra/systematic-debugging | 체계적 디버깅 | [GitHub](https://github.com/obra/superpowers/blob/main/skills/systematic-debugging/SKILL.md) | - |
| obra/subagent-driven-development | 서브에이전트 기반 개발 | [GitHub](https://github.com/obra/superpowers/blob/main/skills/subagent-driven-development/SKILL.md) | - |
| NeoLabHQ/code-review | 멀티에이전트 코드 리뷰 | [GitHub](https://github.com/NeoLabHQ/context-engineering-kit/tree/master/plugins/code-review) | - |
| NeoLabHQ/sdd | 스펙 기반 개발 워크플로우 | [GitHub](https://github.com/NeoLabHQ/context-engineering-kit/tree/master/plugins/sdd) | - |
| testdino-hq/playwright-skill | Playwright 70+ 테스트 패턴 | [GitHub](https://github.com/testdino-hq/playwright-skill) | - |
| ibelick/ui-skills | UI 에이전트 가이드 | [GitHub](https://github.com/ibelick/ui-skills) | - |
| zxkane/aws-skills | AWS 인프라/클라우드 패턴 | [GitHub](https://github.com/zxkane/aws-skills) | - |
| antonbabenko/terraform-skill | Terraform IaC 베스트 프랙티스 | [GitHub](https://github.com/antonbabenko/terraform-skill) | - |

## Community — Context Engineering

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| muratcankoylan/context-fundamentals | 컨텍스트 엔지니어링 기초 | [GitHub](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering/tree/main/skills/context-fundamentals) | - |
| muratcankoylan/multi-agent-patterns | 멀티에이전트 아키텍처 패턴 | [GitHub](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering/tree/main/skills/multi-agent-patterns) | - |
| muratcankoylan/memory-systems | 메모리 시스템 설계 | [GitHub](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering/tree/main/skills/memory-systems) | - |
| k-kolomeitsev/data-structure-protocol | 그래프 기반 장기 메모리 | [GitHub](https://github.com/k-kolomeitsev/data-structure-protocol) | - |

## Community — Productivity

| 스킬명 | 설명 | 소스 | 기본설치 |
|--------|------|------|----------|
| hanfang/claude-memory-skill | 계층적 메모리 시스템 | [GitHub](https://github.com/hanfang/claude-memory-skill) | - |
| kreuzberg-dev/kreuzberg | 62+ 포맷 텍스트/테이블 추출 | [GitHub](https://github.com/kreuzberg-dev/kreuzberg/tree/main/skills/kreuzberg) | - |
| op7418/NanoBanana-PPT-Skills | AI PPT 생성 | [GitHub](https://github.com/op7418/NanoBanana-PPT-Skills) | - |
| wrsmith108/linear-claude-skill | Linear 이슈/프로젝트 관리 | [GitHub](https://github.com/wrsmith108/linear-claude-skill) | - |

---

> 이 카탈로그는 주요 스킬을 선별하여 수록했습니다.
> 전체 549+ 스킬 목록은 [awesome-agent-skills](https://github.com/ceo4ever/awesome-agent-skills) 참조.
