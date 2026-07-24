# DONE: 부트스트랩 진입 모델 사용자레벨 상시 → 프로젝트레벨 opt-in (2-tier)

> 완료일: 2026-06-30 17:00 KST | 스킬: opds | 모드: agentic | 태스크: 049

## 결과 요약

OPAL 부트스트랩을 **2-tier**로 전환했다. 전역 마커는 항상 **비서(Lite) tier**를 로드하고, **PM(Full) tier**는 `.opal/AGENT.md`가 존재하는(=`opi`로 초기화된) 프로젝트에서만 승격된다. 이로써 "프레임워크는 사용자레벨 설치 + PM 부트스트랩은 프로젝트레벨 opt-in"이 달성되었고, 전역 알투 비서는 유지된다.

## 핵심 설계 결정

| # | 결정 | 근거 |
|---|------|------|
| 1 | 비서/PM 모순(전역 비서 유지 + 비-opi PM 미로드)을 **2-tier**로 해소 | 비서=Phase A(항상), PM=Phase B(승격) 분리 |
| 2 | PM 승격 게이트 = **`.opal/AGENT.md` 존재** | 현 역할전환 표·완료보고 PM모드 칼럼이 이미 쓰는 신호와 동일 → 정합 리스크 최소 |
| 3 | 2-tier 로직은 **AGENT.md 한 파일에 집중**, bootstrapper는 진입점만 | 헌법 "플랫폼 분기는 어댑터에만, 로직은 AGENT.md" 준수 |
| 4 | 전역 마커는 제거가 아니라 **경량 비서 마커로 유지** | "전역 비서 유지" 충족 — Claude Code엔 전역 자동로드가 CLAUDE.md뿐 |
| 5 | install 스크립트는 **변경 대상 아님(검증만)** | `install_opal_section` 마커 단위 치환이 이미 구버전 능동 교체+사용자 내용 보존 제공 |
| 6 | `//opi` 불변식 — 비서 tier가 `//` 레지스트리 해석 보유 | `//` Lazy 트리거 전제조건 부재 → 비-opi 폴더 OPAL화 진입점 보존 |

## 변경 파일 (10건)

| 파일 | 변경 |
|------|------|
| `opal/core/AGENT.md` | Eager 2-phase 재구성(Phase A 비서/Phase B PM 승격) + 부트스트래퍼 자동 관리 절 2-tier 반전 + 완료보고 비서세션 `⬜` 규칙 + 변경이력 |
| `opal/bootstrapper/claude-bootstrap.md` | 비서 진입 의미 정합 + 변경이력 049 |
| `opal/bootstrapper/gemini-bootstrap.md` | 〃 |
| `opal/bootstrapper/codex-bootstrap.md` | 〃 |
| `opal/bootstrapper/cursor-bootstrap.mdc` | 본문 의미 정합(frontmatter 무손상, 변경이력 표 미신설) |
| `opal/skills/opal-project-init/templates/common/platform/AGENTS.md` | **신규** — Codex 프로젝트 마커 템플릿 |
| `opal/skills/opal-project-init/scripts/apply.js` | `PLATFORM_FILES`에 AGENTS.md 1행(mergeOther 재사용) |
| `opal/skills/opal-project-init/SKILL.md` | Phase 4-1 표·기존파일처리·완료보고에 AGENTS.md + 변경이력 |
| `docs/ARCHITECTURE.md` | 부트스트랩 2-tier 진입 모델 절 + 변경이력 |
| `docs/PROJECT.md` | 변경이력 049 행 |

## 검증 결과

- **자동화 17/17 PASS, FAIL 0** (L1 정적 14 + L2 동작계약 3).
- **RED-first**: TS-013/015(apply.js) RED FAIL→GREEN 전환 확인(작성자≠구현자). TS-009(install 마커교체) 회귀 가드 GREEN.
- **회귀 0**: setting.json 스키마·`bootstrap:off` 게이트·models 우선순위 불변, opi 기존 3종 비파괴.
- **L3 8건 pending(캡틴 직접)**: 부트스트랩 LLM 거동 + 실배포 필요 — install 재배포 후 실세션 확인.

## 후속 (캡틴)

1. **install 재배포** — 소스 변경분을 `~/.opal/`·전역 마커에 반영(배포 경계: 캡틴 수행).
2. **L3 실세션 검증** (재배포 후): ①비-opi 비서 활성 ②비-opi PM 미로드 ③비-opi `//opi` 발동 ④opi 후 PM 승격 ⑤`bootstrap:off` 킬스위치.
3. **커밋** — 캡틴 지시 시 수행(현재 미커밋).

## 산출물

- `TASK.md` / `PLAN.md` / `TEST-SCENARIO.md` / `AGENTIC-LOG.md` / `tests/`(ts-009·013·015)
