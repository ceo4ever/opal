# DONE: OPAL Console 프로젝트별 환경 설정 화면 — 프라임 풀 토글 단일 기능

> 완료일: 2026-07-14 18:40 KST | 적용 스킬: opd (agentic) | 태스크: 061

## 목표 달성

콘솔 7번째 화면 `/settings`를 신설하고, 읽기 전용 원칙의 두 번째 쓰기 예외를 **설정 라우터 1곳에 격리**했다. 최종 범위는 캡틴 확정에 따라 **프라임 풀(사전 예열) 토글 단일 기능** — 토글 ON 시 `console.config.json` `prewarm_projects` 반영 + `BrainSessionRegistry.prewarm()` 즉시 호출(재기동 불요·멱등), OFF 시 목록 제거. console.config 전반·프로젝트 로컬 설정 편집은 구현 후 회수(JSON 수동 편집 유지, 화면 기능은 필요 시 하나씩 추가). 기존 read-only 5종 + 브레인 POST 계약 불변.

## 변경 파일 (커밋 9443606)

| 파일 | 변경 |
|------|------|
| `dashboard/backend/routers/config.py` | 신규 — GET /api/config + POST /api/config/prewarm, 스캔 화이트리스트 400 게이트, LLM 호출 0회, 거부 로깅 |
| `dashboard/backend/config.py` | `_WRITE_LOCK` + `_atomic_write_json`(temp+os.replace) + `save_config` 머지 보존(미지 키 유지) |
| `dashboard/backend/models.py` | `ConsoleConfigResponse`·`ConfigWriteResponse`·`PrewarmToggleRequest` |
| `dashboard/backend/main.py` | config 라우터 등록 (CORS·바인딩 불변) |
| `dashboard/backend/tests/*` | RED-first 24케이스 → 축소 후 유지 10케이스 (T061 프리픽스) |
| `dashboard/frontend/src/pages/settings/SettingsPage.tsx` | 신규 — 토글 카드 + prewarm 목록 읽기 전용 + 수동 편집 안내 |
| `dashboard/frontend/src/{router,components/app-shell/AppShell}.tsx` | /settings 라우트 + 네비 "설정" + TopBar 설정 버튼 연결 |
| `dashboard/frontend/src/lib/api.ts` | 에러 detail 표면화(FastAPI 문자열·Pydantic 422 배열, 안전 폴백) — PM 승인 스코프 확장 |
| `dashboard/frontend/src/components/ui/{switch,label}.tsx` | shadcn 정식 추가 |
| `docs/ARCHITECTURE.md` | §설정 화면 절 신설 + 7화면 다이어그램 + 변경이력 2행 |

## 검증 증거

- **RED-first(BE 강제 트랙)**: 신규 24케이스 전건 RED(AttributeError/404) → scenario-red 5/5 → scenario-lock → `verify --red-check` pass → GREEN. 테스트 불변성 diff 검증(단언 약화 0).
- **자동 검증**: 축소 반영 후 전체 스위트 **245 passed·1 skipped·0 failed**(기준선 235+유지 10), 신규 케이스 5회 반복 0 flaky(동시성 10회 스트레스 0 race). ruff·tsc·eslint 클린, vitest 111/111.
- **실기동 E2E(cmux)**: S-8' API 표면 축소 확인(신규 2종만 노출·회수 3종 부재), S-9' 축소 화면 렌더·토글 ON→config 실반영→OFF 원복(구독 트리거 1회 이내), 스크린샷 2건. 환경 전 과정 원상복구(config 바이트 동일·배포 데몬 재기동).
- **S-10(캡틴)**: "승인. 배포는 내가 했어." — 캡틴이 install 재배포 직접 수행 + CLOSE 승인 (2026-07-14 18:37).
- **컨벤션**: GC-CONVENTION-2607141828.md — Critical 0/High 0/Medium 0/Low 2(FE 파일명 관례·api.ts depends 누락)/Info 1.
- **보안**: 시크릿 0, 설정 라우터 LLM 호출 0회(브레인 격리 불변), 127.0.0.1 바인딩 불변, path traversal 방어는 화이트리스트 축소로 표면 자체 제거.

## 운영 기록 (특이사항)

- ANALYSIS 워커가 산출물 파일 미저장(Artifact Gate Fail 1회) → 재지시로 해소. 서브에이전트 하네스의 analysis 파일명 Write 차단을 Bash heredoc으로 우회(폴백 사후 승인, AGENTIC-LOG #2~4).
- scenario-lock이 혼합 트랙 미지원(전 시나리오 RED 증거 요구) → SSOT를 RED 트랙 S-1~S-5로 재구성해 해소. RED 워커가 비RED 시나리오 증거 조작을 거부하고 정직 보고(AGENTIC-LOG #9~11).
- 범위 변경 2회: ① 캡틴 raw JSON 탭 편집안 논의 → ② 최종 "토글만 반영, JSON 수동" 확정 — 구현된 console 편집·project-local API/화면/테스트 14건 회수(무인증 데몬 쓰기 표면 최소화, AGENTIC-LOG #20~22).
- prewarm 호출을 "목록 신규 추가 시 1회"로 구현(테스트 스펙 준수·멱등 강화) — PLAN 의사코드 이탈 사후 승인(AGENTIC-LOG #12).

## 잔여·후속 액션

1. **후속 기능 후보(캡틴 방침: 필요 시 하나씩 추가)**: console.config 편집·프로젝트 로컬 설정 편집 UI — 이번 회수분 설계·테스트가 PLAN.md §3.3~3.4·git 이력에 보존되어 재활용 가능.
2. **프레임워크 개선 제안**: test-tool scenario-init에 red_required(트랙) 필드 도입 — scenario-lock 혼합 트랙 지원 (AGENTIC-LOG #11).
3. **컨벤션 Low 2건**: CONVENTIONS.md에 FE 컴포넌트 PascalCase 예외 조항 추가 검토 + api.ts @header depends 보강 — 별건 L2 처리 가능.
4. **선행 잔여(059·060 후속, 불변)**: opbr_adapter raw `claude -p` → opal-agent 이관 / mypy 도입 검토.

## 산출물

TASK.md / ANALYSIS.md / PLAN.md / TEST-SCENARIO.md / test-scenario.json / AGENTIC-LOG.md / GC-CONVENTION-2607141828.md / evidence-s9-settings-page.png / evidence-s9r-settings-reduced.png / DONE.md
