# opal Memory Index

> 최종 갱신: 2026-06-26 (044 도구·MCP·스킬 통합 검색·사용법·활용 체계 — TASK)
> last_task_number: 53
> ⚠️ 채번 충돌: 015·016이 양 PC에서 중복 사용됨 (main: 015 보고형식·016 TDD·017 가드 / brain 라인: 015 brain 코어·016 wiki 지능화). 다음 채번은 018부터.


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





> v0.5.0 베이스라인 시작 — 이전 작업 히스토리는 git log + tasks/ 폴더(삭제됨)에서 추적
> 새 태스크는 001부터 채번

## 메모리
<!-- memory:index:start -->
| 제목 | 등록일 | 유형 | 상태 | 파일 | 요약 |
|------|--------|------|------|------|------|
| Console 브레인 구독 인증 | 2026-06-22 | project | active | `memory/console-brain-subscription-auth.md` | Console 브레인 질의는 종량제 API 아닌 사용자 Claude 구독(로컬 claude -p). API키·SDK 금지 |
| 브레인 질의 콜드 경량화(037후속) | 2026-06-23 | task | active | `memory/follow-up-brain-query-lite.md` | 브레인 질의 콜드 latency 경량화 — 검색을 LLM 밖 brain-tool로. opbr --lite 권고 |
<!-- memory:index:end -->

## 작업 히스토리 (최대 5개, FIFO)
<!-- memory:history:start -->
| 제목 | 등록일 | 단계 | 경로 | 핵심결과 |
|------|--------|------|------|----------|
| 053 brain related 링크필드 정비 + validate 집행 강화 | 2026-07-10 | 완료 | tasks/053-260708-opp-related-링크필드-정비/ | validate 링크필드(related) 검사 신설+--related 플래그. 11페이지 34항목 정비. 118 GREEN. 후속=install 재배포·커밋 |
| 052 워크스페이스 git 일괄 동기화 | 2026-07-02 | 완료 | tasks/052-260702-opd-워크스페이스-git-동기화/ | git-sync-tool(도구)+opal-workspace-sync(스킬 opws) 신설. ff-only pull·5종 skip·무손실. 교훈: 신규 스킬은 skills-registry.json 등록 필수. 13/13 GREEN. opd/agentic |
| 051 headless(claude -p) 비서티어 캡 | 2026-07-02 | 완료 | tasks/051-260702-opp-헤드리스-비서티어-캡/ | [ASSISTANT] 첫 줄 마커 신설 → 3단 스킵 사다리([WORKER]전부/[ASSISTANT]Phase A만/무마커 A+B). Phase B 승격 게이트에 억제 절 AND 추가(cwd에 .opal/AGENT.md 있어도 첫 줄 [ASSISTANT]면 PM tier 스킵). 첫 소비자=opbr_adapter.py -p 프롬프트 프리픽스(보안 계약 불변). 본질=tier 격리(정합성), 지연 아님. **실측 검증**: [ASSISTANT] 프로브 ⬜harness⬜PM + Phase B 미로드, 무마커 대조군 6파일=회귀0. ARCHITECTURE.md 반영, brain concept 1건. **후속=캡틴 canonical install(현재 ~/.opal는 dev-artifact)**·커밋·headless 소비자 인벤토리 스캔. opp/agentic |
| 050 AGENT.md 다이제스트 (비서 코어 경량화) | 2026-06-30 | 완료 | tasks/050-260630-opds-에이전트-다이제스트/ | AGENT.md 493→236줄(런타임 ~51%↓). PM섹션→opal-pm.md 이동+dedup, 부트스트래퍼→신규 ref. TEST 17/17. 후속=install재배포·L3·커밋·051(PRINCIPLES 역할배치) |
| 049 부트스트랩 프로젝트레벨 전환 (2-tier) | 2026-06-30 | 완료 | tasks/049-260630-opds-부트스트랩-프로젝트레벨-전환/ | 비서(전역)/PM(opi한정) 2-tier 분리. TEST 17/17 PASS. 후속=install재배포·L3·커밋 |
<!-- memory:history:end -->
