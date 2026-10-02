# 교본 원문 출처

> 수집: 2026-10-02 (알투) · 근거: `docs/proposals/261002_단위_테스트_경량_경로.md` §5.6, `docs/proposals/261002_테스트_및_시나리오_품질_강화.md` §6.4
> 원문 내용은 수정하지 않는다. 단, 각 교본의 `SKILL.md`는 OPAL 스킬 스캐너(`skill-registry` 검증, `brain-tool` 스킬 수집)가 스킬로 오인하지 않도록 파일 이름만 `GUIDE.md`로 바꿨다. sha256(12)은 이름 변경 후의 폴더 파일(경로순) 내용 기준.
> 판정·사용 범위·읽지 않을 절은 언어별 색인(`INDEX.md`, 후속 태스크)에서 관리한다.
> 판정: `사용` = 현재 프로젝트(pug·stl·OPAL) 요소에 연결, `보관` = 해당 스택 요소가 생기면 연결할 수 있도록 원문만 보관.
> ECC 커밋: `c70874fae9eb0e5ad0365beb7e2955899fd1d30f` (affaan-m/ECC, 2026-09-29). 설치본 사본은 `~/.opal/community-skills/`에서 복사.

| 폴더 | 교본 | 출처 저장소 | 원문 경로 | 커밋·버전 | 라이선스 | 판정 | 파일 | 크기 | sha256(12) |
|---|---|---|---|---|---|---|---|---|---|
| kotlin | `kotlin-patterns` | affaan-m/ECC | `skills/kotlin-patterns` | `c70874fa` | MIT | 사용 | 1 | 19KB | `e519234772a3` |
| kotlin | `kotlin-testing` | affaan-m/ECC | `skills/kotlin-testing` | `c70874fa` | MIT | 사용 | 1 | 20KB | `13e39ad65e86` |
| kotlin | `hexagonal-architecture` | affaan-m/ECC | `skills/hexagonal-architecture` | `c70874fa` | MIT | 사용 | 1 | 11KB | `1579f70e4cd5` |
| kotlin | `kotlin-coroutines-flows` | affaan-m/ECC | `skills/kotlin-coroutines-flows` | `c70874fa` | MIT | 보관(Android·KMP 요소용) | 1 | 8KB | `ed7d895ecd6c` |
| kotlin | `rules-kotlin` | affaan-m/ECC | `rules/kotlin` | `c70874fa` | MIT | 보관(프레임워크 상이) | 5 | 13KB | `6a3a38148c7d` |
| java | `springboot-patterns` | affaan-m/ECC | `skills/springboot-patterns` | `c70874fa` | MIT | 보관(Spring MVC·JPA 요소용) | 1 | 10KB | `ff1884a8492d` |
| java | `springboot-tdd` | affaan-m/ECC | `skills/springboot-tdd` | `c70874fa` | MIT | 보관(JUnit·Mockito 요소용) | 1 | 4KB | `e4bd145484d9` |
| java | `springboot-verification` | affaan-m/ECC | `skills/springboot-verification` | `c70874fa` | MIT | 보관(Maven·정적 분석 요소용) | 1 | 6KB | `c9449f169a3b` |
| typescript | `react-best-practices` | vercel-labs/agent-skills | `skills/react-best-practices` | `설치본 ~/.o` | MIT | 사용 | 64 | 177KB | `4544ac7f0faa` |
| typescript | `composition-patterns` | vercel-labs/agent-skills | `skills/composition-patterns` | `설치본 ~/.o` | MIT | 사용 | 14 | 49KB | `1f0b1e98e276` |
| typescript | `next-best-practices` | vercel-labs/next-skills(현재 원본에 없음) | `skills/next-best-practices` | `설치본 ~/.o` | 미확인 | 사용(라이선스 확인 전 외부 배포 금지) | 20 | 79KB | `24732948e63c` |
| typescript | `react-testing` | affaan-m/ECC | `skills/react-testing` | `c70874fa` | MIT | 사용 | 1 | 13KB | `51c18b4e2828` |
| typescript | `vite-patterns` | affaan-m/ECC | `skills/vite-patterns` | `c70874fa` | MIT | 사용(Vite 요소) | 1 | 17KB | `2238d353196b` |
| typescript | `react-patterns` | affaan-m/ECC | `skills/react-patterns` | `c70874fa` | MIT | 보관(vercel-labs와 중복) | 1 | 11KB | `f3208d44a5d5` |
| typescript | `nextjs-turbopack` | affaan-m/ECC | `skills/nextjs-turbopack` | `c70874fa` | MIT | 보관(vercel-labs와 중복) | 1 | 3KB | `336034322d20` |
| typescript | `frontend-patterns` | affaan-m/ECC | `skills/frontend-patterns` | `c70874fa` | MIT | 보관(vercel-labs와 중복) | 1 | 15KB | `a5b971eb9e74` |
| typescript | `backend-patterns` | affaan-m/ECC | `skills/backend-patterns` | `c70874fa` | MIT | 보관(Node·Express 요소용) | 1 | 13KB | `9b983d0297a9` |
| python | `python-patterns` | affaan-m/ECC | `skills/python-patterns` | `c70874fa` | MIT | 사용 | 1 | 17KB | `103e0130dac3` |
| python | `python-testing` | affaan-m/ECC | `skills/python-testing` | `c70874fa` | MIT | 사용 | 1 | 19KB | `b9f7a158dae3` |
| python | `fastapi-patterns` | affaan-m/ECC | `skills/fastapi-patterns` | `c70874fa` | MIT | 사용(FastAPI 요소) | 1 | 15KB | `f54c2bf5a61e` |
| python | `modern-python` | trailofbits/skills | `plugins/modern-python` | `설치본 ~/.o` | CC-BY-SA-4.0 | 사용(도구 설정) | 12 | 55KB | `d127e1a6071f` |
| sql | `database-migrations` | affaan-m/ECC | `skills/database-migrations` | `c70874fa` | MIT | 사용(PostgreSQL 절) | 1 | 12KB | `dad2f1964295` |
| sql | `postgres-patterns` | affaan-m/ECC | `skills/postgres-patterns` | `c70874fa` | MIT | 사용 | 1 | 4KB | `9c8c391ae9e9` |
| common | `api-design` | affaan-m/ECC | `skills/api-design` | `c70874fa` | MIT | 사용 | 1 | 13KB | `250e464413a1` |
| common | `tdd-workflow` | affaan-m/ECC | `skills/tdd-workflow` | `c70874fa` | MIT | 사용(Common Testing Mistakes 절) | 1 | 21KB | `8887afa786ef` |
| common | `coding-standards` | affaan-m/ECC | `skills/coding-standards` | `c70874fa` | MIT | 보관(OPAL 규칙과 중복) | 1 | 13KB | `e80544c3d1ea` |

라이선스 고지: `licenses/`. `next-best-practices`는 원 저장소에서 현재 찾을 수 없어 라이선스 미확인 — 확인 전 OPAL 외부 배포 금지.
