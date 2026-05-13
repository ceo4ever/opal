# DONE: 보고 형식 양식 보강 — 결론/근거 번호화 + 이모티 prefix + 다음 블록 2갈래

> 완료일: 2026-05-13 17:48 KST | 적용 스킬: opp | 모드: semi-agentic

## 1. 작업 결과 요약

보고 형식 SSOT(`reporting-template.md`)에 캡틴이 제안한 양식 보강 규칙 3가지(결론·근거 항목 번호화 / 4종 이모티 prefix / 다음 블록 2갈래 분기)를 정식 등재했다. 부트스트랩 진입점(`opal/core/AGENT.md`)의 핵심 구조 라인 1줄을 새 이모티 표기로 정합화하고, install-mac.sh 재실행으로 배포본까지 반영했다.

본 태스크 진행 중(TASK·PLAN·EXECUTE 보고 전체) 알투가 새 양식을 즉시 적용하여 자가 점검(Step 6)을 통과했다.

## 2. 산출물

| # | 파일 | 변경 |
|---|------|------|
| 1 | `opal/core/references/harness/reporting-template.md` | §1·§2·§3·§4·§8.1~§8.3·§9 전면 갱신 + §변경이력 v1.1 행 추가 |
| 2 | `opal/core/AGENT.md` | line 194 핵심 구조 라인을 이모티 표기로 갱신 + §변경이력 v2.6 행 추가 |
| 3 | `tasks/003-260513-opp-reporting-format-enhancement/TASK.md` | 요구사항 7건 [x] 갱신 (QA-PLAN 단계) |
| 4 | `tasks/003-260513-opp-reporting-format-enhancement/PLAN.md` | §3 실행 체크리스트 6/6 [x] + §4 QA 체크리스트 17/17 [x] |
| 5 | `tasks/003-260513-opp-reporting-format-enhancement/QA-PLAN.md` | PLAN QA 보고 (Pass) |
| 6 | `tasks/003-260513-opp-reporting-format-enhancement/QA-EXECUTE.md` | EXECUTE QA 보고 (Pass) |
| 7 | `tasks/003-260513-opp-reporting-format-enhancement/AGENTIC-LOG.md` | semi-agentic 자율 통과 게이트 기록 |
| 8 | `tasks/003-260513-opp-reporting-format-enhancement/STATE.md` | 파이프라인 현황판 (state-tool 관리) |

배포 결과:
- `~/.opal/references/harness/reporting-template.md` — 새 양식 반영 (이모티 4종 + 항목 번호화 + 다음 블록 2갈래)
- `~/.opal/AGENT.md` — 핵심 구조 라인 이모티 표기 반영
- 양 배포본 `## 변경이력` 섹션 strip 확인 (install-mac.sh `strip_deploy_md` 정상 동작)

## 3. 핵심 변경 — reporting-template.md

### §1 — 이모티 헤딩 4종 매핑 표 신설

| 블록 | 이모티 | 헤딩 형식 |
|------|--------|----------|
| 결론 | 🎯 | `🎯 결론` |
| 근거 | 🔍 | `🔍 근거` |
| 다음 (의사결정) | ❓ | `❓ 의사 결정해 주세요?` |
| 다음 (진행) | ▶️ | `▶️ 다음 진행 사항입니다.` |

### §2 — 결론 카드 → 다음 블록 분기 재정의

- §2.1 의사결정 필요 시 (`❓` 블록): 결론 첫 줄에 "캡틴 결정이 필요합니다 — N개 옵션 중 알투 권고는 X번" + 옵션은 근거 블록 흡수
- §2.2 단순 진행 시 (`▶️` 블록): 번호 + 들여쓰기 리스트, 옵션 1개일 때도 `▶️` 분기 사용 (R-5 대응)

### §3 — 항목 번호화 규칙 신설

- 결론 항목 수: 1~3개 권고 (기존 "결론 길이 1~2줄" 재정의)
- 근거 항목 수: 3개 이내 유지
- 항목 번호화: `1)`, `2)`, `3)` 형식

### §4 — 시각 구분 보강

- 블록 헤딩을 이모티 표기로 갱신
- "항목 사이 빈 줄" 행 명확화 (말이 길어질수록 필수)

### §8.1~§8.3 게이트 3종 양식 갱신

- 5요소 표준(의사결정 요약 / 변경 범위 / 체크포인트 / 실행 구성 / 다음 액션) 유지
- 양식 예시 3건을 새 양식(이모티 + 번호화 + ▶️/❓ 분기)으로 전면 갱신

### §9 예시 카드 3건 갱신

- PLAN 완료 / EXECUTE 완료 / PM(대화) 검토 응답 모두 새 양식 적용

### §변경이력 v1.1 행 추가

`| v1.1 | 2026-05-13 17:35 | 태스크 003 — 보고 형식 양식 보강 (이모티 prefix + 항목 번호화 + 다음 블록 2갈래) (003) |`

## 4. AGENT.md 변경

- line 194 핵심 구조 라인: `**결론** (필수) → **근거** (필수) → **다음** (옵션)` → `🎯 결론 (필수) → 🔍 근거 (필수) → ❓/▶️ 다음 (옵션) — 다음 블록은 의사결정/진행 2갈래`
- 역할별 응답 표기 표 / Observability / 필수 로드 안내 — 유지 (SSOT 단일성)
- §변경이력 v2.6 행 추가

## 5. 미확정 사항 결정 결과

| # | 결정 | 근거 |
|---|------|------|
| M-1 | (a) 기존 §1~§9 구조 유지 보강 | D-1~D-5가 §1·§2·§3·§4·§8·§9에 깔끔히 매핑됨 |
| M-2 | (b) AGENT.md 핵심 구조 라인 1줄만 갱신 | SSOT 단일성 — 양식 예시는 reporting-template.md 단일 정의 |
| M-3 | (c) §변경이력 표 이미 존재, 행만 추가 | EXECUTE 워커가 reporting-template.md:238-242 §변경이력 표 확인. TASK 가정 정정 |

## 6. 정합성 검증 결과 (Step 3)

- `opal/core/references/opal-pm.md` §8 (lines 100-109) — 헤딩 표기 미언급, 충돌 없음, 수정 없음
- `opal/core/references/opal-harness.md` §2 모듈 테이블 (line 98) — 표기 무관, 충돌 없음, 수정 없음
- `docs/` 영향 없음 — CONVENTIONS.md/ARCHITECTURE.md grep 매칭은 모두 일반 "근거"/"결정 근거" 표현으로 보고 형식과 무관

## 7. QA 결과

| 단계 | 판정 | 산출물 |
|------|------|--------|
| PLAN | Pass | `QA-PLAN.md` (7개 요구사항 매핑, [MUST] 4건, 인용 규칙 완전 준수) |
| EXECUTE | Pass | `QA-EXECUTE.md` (GE-1·GE-2·GE-3 충족, 가드레일 위반 0건) |

decision_required: 0건

## 8. 게이트 통과 기록

| 단계 | 사용자 확인 | 시각 | 발화 |
|------|------------|------|------|
| TASK | ✅ | 2026-05-13 17:23 | "승인, semi-agentic" |
| PLAN | ✅ | 2026-05-13 17:34 | "승인" |
| EXECUTE | ✅ | 2026-05-13 17:48 | "승인" (CLOSE 진입) |

semi-agentic 자율 통과 게이트:
- EXECUTE 작업 행 (12), QA Gate (13), QA-EXECUTE.md 생성 (14), State Gate (15), PM Gate (16), State Gate (17) — 모두 `--auto-pass` 통과 (AGENTIC-LOG.md 기록)

## 9. 후속 태스크 후보

- 없음 (본 태스크로 완결)

다만 향후 참고용:
- 새 양식이 다른 OPAL pilot(opd/opds/opdw/opwt/oppd/opsdd)의 SKILL.md 단계 보고 양식과도 정합한지 운용 중 모니터링 권장 (현재 reporting-template.md SSOT만 갱신, 각 pilot SKILL.md 내부 보고 양식 표기는 변경 안 함 — pilot SKILL.md는 산출물 명세이지 응답 양식 명세가 아니므로 영향 없을 것으로 예상)

## 10. 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-05-13 17:48 | DONE.md 작성 — 태스크 003 완료 |
