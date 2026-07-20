# DONE: PM 학습 루프 tool-gated 재설계 + 로컬/FW 학습 분리 + fw-inbox 수집

> 완료일: 2026-07-20 | 적용 스킬: opd | 모드: agentic
> 태스크: 058-260713-opd-학습루프-도구화-개선수집

## 작업 목표 (달성)

정의만 있고 어디서도 호출되지 않던 PM 학습 루프/자기 개선을, `op-brain-ingest`와 같은 **tool-gated 집행 체계**(CLOSE 하드연결 + 도구 집행 + 산출물 증거)로 재설계했다. 학습을 **로컬 PM 개선**(프로젝트 `.opal/`)과 **FW 개선**(전역 `~/.opal/fw-inbox/`)으로 분리하고, 온디맨드 스킬 `opal-improve`(`//opim`)와 결정론 기록 도구 `improve-tool`을 신설했다.

## 요구사항 이행

| R | 내용 | 결과 |
|---|------|------|
| R1 | 회고 하드스텝 (pilot CLOSE) | ✅ 4 pilot(opd·opwt·opgc·oppd) CLOSE에 op-brain-ingest 직후 회고 스텝 대칭 삽입. no-op 비차단 문구 4파일 일치 |
| R2 | opal-improve 스킬 (`//opim`) | ✅ SKILL.md 5단계(관찰→분류→기록→보고→승인) + 로컬/FW 분류 2원화(결정론 게이트→루브릭, 동점 에스컬레이션). registry `opim` match 확인 |
| R3 | improve-tool 결정론 집행 | ✅ `opal/tools/improve-tool/`(run.sh+py) — `record --scope <local\|fw>`, `"ok"` JSON 계약. RED-first 14 테스트 GREEN. tools.md 등록 |
| R4 | fw-inbox 수집 + 로컬/FW 분류 | ✅ fw scope → `~/.opal/fw-inbox/{일시}-{host}-{slug}.md` 출처메타 4종(host·project·situation·created) 자기완결 적재. 실기록 증거: `20260717-103446-*-PLAN-단계에-전제한-도구-외부-계약-사전검증-스텝-추가.md` |
| R5 | 문서 SSOT 통합 + 잉여 제거 | ✅ `pm-learning-loop.md`→`pm-improvement-loop.md` rename SSOT 본문화(트리거 테이블·5단계·기록위치·hook 미채택 근거), `self-improvement.md` 삭제, `opal-pm.md §5` stub 신규 지칭, 라이브 dangling 0 |
| R6 | install 배포 반영 | ✅ install-mac.sh(improve-tool chmod + fw-inbox mkdir/README create-if-absent) / windows.ps1(New-Item -Force). clean_dirs·cleanDirs에 fw-inbox 미포함(런타임 데이터 보존 멱등) |

## 변경 파일

**신규**
- `opal/skills/opal-improve/SKILL.md` — `//opim` 온디맨드 개선 루프 스킬
- `opal/tools/improve-tool/` — run.sh·improve_tool.py·tests(14)·fw-inbox-README.md

**문서 SSOT**
- `opal/core/references/harness/pm-improvement-loop.md` — 구 pm-learning-loop.md rename + self-improvement 흡수 통합
- `opal/core/references/pm/self-improvement.md` — 삭제
- `opal/core/references/opal-pm.md` — §5 stub 신규 SSOT 지칭
- `opal/core/AGENT.md`, `opal/core/references/pm/specialist-agent.md`, `opal/skills/opal-project-init/references/agent-guide.md` — dangling 참조 정리

**파이프라인 훅**
- `opal/skills/opal-pilot-dev|write-tech|gc|project-dev/SKILL.md` — CLOSE 회고 하드스텝(4/4 대칭)

**도구·registry·배포**
- `opal/tools/memory-tool/memory_tool.py` — VALID_TYPES+=`improvement`, VALID_STATUSES+=`candidate` (additive, 캡틴 A안)
- `opal/core/references/opal-skills-registry.json` — `opim` 등록
- `opal/core/references/tools.md` — improve-tool 등록
- `scripts/install-mac.sh`, `scripts/install/windows.ps1` — 3자산(opal-improve·improve-tool·fw-inbox) 배포
- `docs/PROJECT.md` — 개선 루프 컴포넌트 섹션 + 변경이력

## 검증 결과 (All Pass)

- **TEST 단계**: S-1~14 전부 PASS. S-10/11(install)은 HOME 격리 sandbox 실증 — 실 `~/.opal` 무오염.
- **자동**: improve-tool pytest 14 passed(RED→GREEN, 테스트 불변) / memory-tool 88 passed(회귀 0) / ruff Pass(mypy 도구 부재 Skip — py_compile 대체, 허위 PASS 금지).
- **정합**: @header, 변경이력 6/6, registry `opim` match live, 라이브 dangling 0(잔여는 v1.0 changelog 이력 표기).
- **보안(§6)**: Pass.

## 설계 하이라이트

1. **op-brain-ingest 3요소 패턴 답습** — CLOSE 하드연결(회고 스텝) + 도구 집행(improve-tool) + 산출물 증거(fw-inbox/.opal 기록). no-op 비차단으로 CLOSE 안정성 유지.
2. **scope 분류 2원화** — 1차 결정론 게이트 → 2차 루브릭, 동점 시 에스컬레이션. 검증 2원화(evaluator+test) 사상을 분류에 적용(캡틴 검토 반영).
3. **hook 인프라 전면 폐기** — 플랫폼 훅 0개, 순수 스킬 온디맨드 + CLOSE 하드스텝만으로 플랫폼 독립 100%.
4. **memory-tool enum 확장 에스컬레이션** — PLAN이 전제한 enum이 실제 계약에 부재 → 캡틴 A안(additive 확장) 선택으로 해소. 이 학습 자체가 fw-inbox 1호 항목으로 기록됨(체계 self-application).

## 특이사항·후속

- **fw-inbox 소비 워크플로우 부재(후속 후보)**: 이번 범위는 수집(기록)까지. inbox 검토→ai-framework 소스 반영→install 배포를 잇는 tool-gated triage 워크플로우는 미구현 — prose 안내만 존재. 후속 태스크 후보.
- **이메일 발송(SMTP)·console cron 대행 발송**: 범위 제외 보류(후속 별도) — 여러 PC의 fw-inbox 중앙 수집 경로.
- **커밋**: 전 산출물 워킹 트리 미커밋 상태 — 캡틴 지시 시 수행.
