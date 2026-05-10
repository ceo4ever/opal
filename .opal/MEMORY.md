# opal Memory Index

> 최종 갱신: 2026-05-10 20:30 (144 진행 중)
> last_task_number: 144

## 메모리 카테고리

| 카테고리 | 설명 | 완료 시 |
|----------|------|---------|
| task | 일회성 작업 계획/예정 | 삭제 |
| project | 프로젝트 비전, 방향성 등 지속 지식 | 유지 (폐기 시 삭제) |
| architecture | 아키텍처 설계 결정과 근거 | 유지 (변경 시 갱신) |
| feedback | 캡틴의 작업 방식 피드백 | 유지 (철회 시 삭제) |
| preferences | 이 프로젝트에서 캡틴이 선호하는 방식 | 유지 |
| issues | 반복되는 이슈와 해결법 | 유지 |

> 메모리 파일은 `memory/` 디렉토리에 저장한다.
> 새 메모리가 생기면 이 인덱스에 파일 경로와 설명을 추가한다.
> **task 타입은 완료 시 메모리 파일 + 인덱스 항목을 삭제한다.**

## 메모리

| 등록일시 | 카테고리 | 상태 | 파일 | 설명 |
|----------|----------|------|------|------|
| 2026-05-09 | preferences | 유지 | [memory/preferences_default_semi_agentic.md](memory/preferences_default_semi_agentic.md) | 캡틴 기본 작업 패턴: PLAN 검토 + EXECUTE 자율 (semi-agentic 모드 기본 채택) |
| 2026-03-22 | project | 진행 중 | [memory/project_security_task.md](memory/project_security_task.md) | 보안 전용 컴포넌트 — TEST(코드 보안) 122에서 완료, PLAN(설계 보안)은 후속 분리 유지 |
| 2026-04-09 | task | 예정 | [memory/task_098_vector_store.md](memory/task_098_vector_store.md) | OPAL Vector Store — sqlite-vec 기반 문서 벡터 검색 도구 (PLAN ✅, EXECUTE 보류) |


## 작업 히스토리 (최대 10개, FIFO)

| 등록일자 | 작업 | 단계 | 경로 | 시작일시 | 완료일시 |
|----------|------|------|------|---------|---------|
| 2026-05-10 | 알투 보고 형식 표준 — 3블록 구조 정식 등재. 신규 `reporting-template.md` SSOT(§1~§9 + §7 단계 전환 보고 양식 PLAN 완료/EXECUTE 후/CLOSE 진입 3종 5요소 표준) + `AGENT.md`(Eager Step 6.6 추가 + §보고 형식 섹션 통합 대체(간단/상세 2종 → 3블록 참조, 역할 표기·Observability 유지) + 부트스트랩 보고 8칼럼 reporting 추가) + `opal-harness.md`(§2 모듈 테이블 행 추가) + `opal-pm.md`(§8 신설). 의사결정 4건 — M-1 Eager 명시(이전 Lazy 결정 정직성 측면 번복) / M-2 알투 자율 판단 / M-3 통합 대체 / M-4 v1.1 재정의(캡틴 게이트 3종 한정 표준 — 11종 분류 폐기 정신 보존). QA-PLAN/QA-EXECUTE 모두 Pass + 컨벤션 자동 진단 Critical/High 0(Medium/Low 6은 기존 파일 변경이력 컬럼명 불일치 — GC-DP-C001 후속 태스크 제안). 142(community-skills fetch) 병행 충돌 가드 통과(install-mac.sh / community-skills-registry.json 미수정). 자기참조 검증(reporting-template.md 본문 자체가 3블록·일목요연·시각구분·재사용성·플랫폼 독립 5항목 모두 통과) (143) | 완료 | tasks/143-260510-opp-agent-reporting-3block-standard/ | 2026-05-10 17:30 | 2026-05-10 19:55 |
| 2026-05-10 | community-skills 번들 → fetch 방식 전환 (skills.sh / npx skills) — community-skills/ 폴더 통째 git rm (553 파일) + registry v2(`source_repo`/`license`, paths 폐기) + skill-registry.js v2 인식 + match 응답 4 신설 필드(installed/source_repo/license/install_command) + opal-skill-manager v1.1 + install-mac.sh v2.0(community-skills 함수/clean 제거) + windows.ps1 v1.6.0(동일) + README/ARCHITECTURE/PROJECT 갱신. D-1~D-4 SSOT(자동 fetch/메타데이터 카탈로그/미설치 감지/기존 보존). source_repo 검증: anthropics 18+openai 1+vercel-labs 5=24 형식 명시 / getsentry+google-labs-code+trailofbits=7 null. 알려진 후속: //skill-manager 매칭 결함(별도 태스크) + Windows 회귀 검증(push 후) (142) | 완료 | tasks/142-260510-opp-community-skills-fetch-migration/ | 2026-05-10 17:02 | 2026-05-10 18:36 |
| 2026-05-10 | README 오픈소스 공개 P0 정비 — MIT LICENSE 신규 + README 배지·라이선스 섹션·OPAL_VERSION generic·부트스트랩 7칼럼·agents 13개·community-skills 30/6조직·MCP 트러블슈팅 + 추가작업 R-9(3-way 모드 체계 설명: 주요특징+ToC+섹션본문) + R-10(Windows winget Python 자동 설치 한 줄). ARCHITECTURE.md M-9(GC 체커 2행 §에이전트 표 보강) 동기화. QA pass_with_minor (Warning C-1: 분류 레이블 — 합계 13 정합, P1 후속). 별도 태스크 142로 community-skills fetch 전환 분리 결정 (141) | 완료 | tasks/141-260510-opp-readme-mit-license-p0/ | 2026-05-10 14:38 | 2026-05-10 16:56 |
| 2026-05-09 | semi-agentic 모드 도입 + 전체 pilot 기본 모드 변경 — 3-way 모드 체계(interactive/semi-agentic 기본/agentic) 신설. 신규 N-1(opal-harness-semi-agentic.md) + N-2(preferences 메모리) + 수정 19종(하네스 3 / 부트스트랩 4 / op-task / pilot 7 / state-tool 2 / .opal 2) + Step 9 보정 docs/CONVENTIONS.md L161 = 총 22 변경 + GC-C001/C002 헤더 보정 3종. D-DEC-1(oppd Phase 2 WBS) / D-DEC-2(opsdd Phase 3 DESIGN) / D-DEC-5(MODE_BOUNDARY_STAGES) / D-DEC-7(AGENTIC-LOG EXECUTE 진입 시점). install + 6단계 동작 검증 모두 PASS (140) | 완료 | tasks/140-260508-opp-default-semi-agentic-mode/ | 2026-05-08 23:51 | 2026-05-09 12:18 |
| 2026-05-09 | 배포 채널 정비 + Get Started UX 통합 (P1) — `scripts/install.sh`/`install.ps1`/`install/{macos,windows}` one-liner + `opal/tools/opal-cli/` 5 서브커맨드 + `opal/tools/doctor/` 4섹션 + `opal/core/AGENT.md` Eager Step 6.5 cwd 분기 + `opal/skills/opal-start/` 신규 + `opal-onboarding` triggers 보강 + `opal-skills-registry.json` v3.4.0 + `.github/workflows/release.yml` (attest-build-provenance v2) + README §설치 4 Step 정제 + ARCHITECTURE.md §배포 채널 현행 전환. 캡틴 결정: D1=`opal-cli` 명칭(opalrb 충돌 회피), D2=`https://github.com/ceo4ever/opal`. v0.1 태그 push로 첫 release 발동 (139) | 완료 | tasks/139-260508-opp-distribute-and-getstarted/ | 2026-05-08 21:43 | 2026-05-09 09:07 |
| 2026-05-08 | opi 프로젝트 초기화 — `.opal/AGENT.md` 신규 + `docs/CONVENTIONS.md` 구현 규칙 섹션 신설 + `docs/ARCHITECTURE.md` 외부 의존 서비스 섹션 신설 + `docs/PROJECT.md` 문서 테이블 보강. 후속 태스크 139(P1)로 배포 채널 정비 + Get Started UX 통합 진행 (138) | 완료 | tasks/138-260508-opi-opal/ | 2026-05-08 17:43 | 2026-05-08 21:43 |
| 2026-05-08 | PLAN 워커 컨벤션 [MUST] 인용 강제 — 사전 주입 강화 (제안 A). 잠재 적용 지점 4종 정밀 분석 후 #1·#3 채택 + #2 부분 채택 + #4 비채택 결정. 5개 파일 변경(dispatch-process v1.1 / op-task-plan SKILL v1.4 / plan-guide v1.2 / op-dev-plan SKILL v2.5 / opal-plan-agent v1.1). 136(B)와 검사 시점·대상·메커니즘 분리 → 사전·사후 이중 안전망 완성 (137) | 완료 | tasks/137-260508-opp-plan-convention-injection/ | 2026-05-08 16:50 | 2026-05-08 22:56 |
| 2026-05-08 | PM Gate 컨벤션 자동 진단 — opal-convention-checker를 changed_files 영역별로 병렬 디스패치하여 GC-CONVENTION-{area}-{ts}.md 보고서 생성, Critical/High 시 PM Gate Fail. opp/opdw=EXECUTE PM Gate, opd/opds=TEST PM Gate에 §13 발동(R-T4 (b) 옵션 채택). 변경 파일 6개(pm-review-gate v1.2 / opal-convention-checker AGENT.md v1.2 / opp v2.8 / opd v3.5 / opds v3.4 / opdw v2.5) (136) | 완료 | tasks/136-260508-opp-pm-gate-convention-auto-check/ | 2026-05-08 13:11 | 2026-05-08 22:08 |
| 2026-05-07 | 시스템 아키텍처 HTML 스킬 OPAL 통합 + 트윈 빌드 비교 — standalone 일반 도구 스킬로 정착, `//html-sa` 호출 가능화, 원본 vs OPAL 호환 수정본 두 HTML 산출, ADD-1로 §2 컨텍스트 흡수 보강(code-scan + 의존성 매니페스트 + 디렉토리 트리) (135) | 추가작업완료 | tasks/135-260507-opp-system-arch-html-skill-port/ | 2026-05-07 11:11 | 2026-05-08 13:57 |
| 2026-04-30 | 멀티 플랫폼 에이전트 배포 메커니즘 — Claude/Cursor/Gemini sub-agent 어댑터 자동 생성 (133) | 완료 | tasks/133-260430-opp-platform-agent-deploy/ | 2026-04-30 14:48 | 2026-04-30 16:55 |
| 2026-04-30 | html-mockup 일반 스킬 신규 개발 (132) | 완료 | tasks/132-260430-opp-html-mockup-skill/ | 2026-04-30 11:27 | 2026-04-30 13:14 |
| 2026-04-24 | Citation Rules 하네스 보편화 — 근거 제시 원칙 강화 (130) | 완료 | tasks/130-260424-opp-plan-citation-hardening/ | 2026-04-24 08:30 | 2026-04-24 11:42 |
| 2026-04-22 | op-dev-execute 구획화 + EXECUTE 디스패치 라우팅 전파 (129) | 완료 | tasks/129-260422-opp-op-dev-execute-agent-guide-split/ | 2026-04-22 23:17 | 2026-04-23 12:31 |
