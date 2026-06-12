# DONE: README 최신화 — 신규 베이스라인(001~017 + brain) 반영

> 완료일: 2026-06-12 12:28 | 적용 스킬: opp | 모드: agentic
> 입력: TASK.md, PLAN.md | 결과: README.md 갱신 완료

## 완료 요약

README.md를 v0.5.0 베이스라인의 신규 기능·플랫폼·트랙으로 최신화하고, SSOT(레지스트리·하네스·각 SKILL.md·PROJECT.md)와 불일치하던 오정보를 정정했다. 단일 파일(`README.md`) 변경, +108 / −7 라인.

## 변경 내역 (README.md)

### 신규 반영 (6 + 독립 스킬 2)
| 항목 | 위치 | SSOT 근거 |
|------|------|-----------|
| A-1 opal-brain (`//opbr`) 사용법 섹션 + 특징·목차 | Pilot 사용법 / 주요 특징 / 목차 | `~/.opal/skills/opal-brain/SKILL.md`, `docs/PROJECT.md` §Project Brain |
| A-2 opal-pilot-gc (`//opgc`) 사용법 + 비교표 행 | Pilot 사용법 / 비교표 / 선택 가이드 | `~/.opal/skills/opal-pilot-gc/SKILL.md` |
| A-3 Codex 플랫폼 | 설치 Step 1 표 + Step 3 안내 | `docs/PROJECT.md:17` |
| A-4 OPAL 헌법 (검증된 완료·강제 우선 + SSOT 한 줄) | 핵심 철학 표 | `~/.opal/PRINCIPLES.md:12-40` |
| A-5 L2 경량 트랙 | 비서/PM 모드 섹션 뒤 신규 | `~/.opal/AGENT.md:141-173` |
| A-6 TDD RED-first 트랙 | opds 흐름 하위 신규 | `~/.opal/references/harness/red-first.md` |
| A-7 독립 스킬 html-mockup·system-architecture-html | 독립 스킬 사용법 | 레지스트리 standalone |

### 오정보 정정 (4)
| 항목 | 정정 내용 | SSOT |
|------|----------|------|
| B-1 부트스트랩 체크리스트 | `✅ principles` 선두 추가 | `~/.opal/AGENT.md:55` |
| B-2 opsdd 파이프라인 | `TASK → SPEC → REVIEW → DESIGN → EXECUTE-LOOP → VERIFY → CLOSE` (비교표·사용법 2곳 통일) | `~/.opal/skills/opal-pilot-sdd/SKILL.md:23` |
| B-3 지원 플랫폼 표 | Codex 추가 | `docs/PROJECT.md:17` |
| B-4 에이전트 수 | "전문 7 + 범용 4 + GC 2 = 13" | `opal/agents/` 13개 |

## 미확정 결정 (PLAN→CLOSE 확정)
- **U-1 ppt-builder**: README 등재 **보류** (캡틴 확정). 미커밋 작업 중 산출물(`skills/ppt-builder/ ??`, 레지스트리 `M`). 정식 커밋 시 1줄 추가로 등재 가능.
- **U-2 opsdd 정본**: SKILL.md SSOT 채택. 레지스트리·PROJECT.md 상이 표기는 README 범위 밖.
- **U-3 개편 범위**: 부분 보강(구조 보존, 헌법 §3 Surgical Changes).

## QA 결과 (PM 강화 검토 — git diff 직접 Read)
- ✅ opsdd 정본 2곳 문자 단위 동일, 구표기 잔존 0
- ✅ ppt-builder 미등재(0건), 부트스트랩 principles 선두, Codex ≥2, 전문 7 정정
- ✅ opgc 7 / opbr 6 / L2 / RED-first 신규 섹션 존재, 목차 앵커 무결성
- ✅ Surgical — 정정 외 기존 문장 변경 없음

## 게이트 이력 (agentic)
3개 게이트(PLAN / PLAN-PM / EXECUTE-PM) 전부 Pass, Fail 0, 에스컬레이션 0. 상세: `AGENTIC-LOG.md`.

## 후속 태스크 후보
- **SSOT 정합 태스크**: opsdd 파이프라인 표기가 레지스트리(`SPEC→VERIFY→PLAN→TASKS→VERIFY→LOOP→DONE`)·PROJECT.md(`…→EXECUTE`)·SKILL.md(정본) 3곳에서 상이 → 레지스트리·PROJECT.md를 SKILL.md 정본으로 정합 권고.
- ppt-builder 정식 커밋 시 README 독립 스킬 등재.
