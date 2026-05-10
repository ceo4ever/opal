# DONE: 알투 보고 형식 표준 — 3블록 구조 정식 등재

> 완료일: 2026-05-10 19:55 (KST) | 적용 스킬: opp | 모드: semi-agentic | 태스크 번호: 143

## 1. 작업 결과 요약

알투(에이전트)의 모든 응답을 **3블록 구조(결론·근거·다음)** 로 통일하는 보고 형식 표준을 OPAL 정식 규칙으로 등재했다. 신규 SSOT 1개 + 기존 참조 문서 3개 갱신.

캡틴 추가 요구사항(C-b) 반영으로 **§7 단계 전환 보고 양식**(PLAN 완료 / EXECUTE 후 사용자 확인 / CLOSE 진입 3종) 표준이 함께 신설되었다. 본 DONE.md는 §7.3 CLOSE 진입 보고 양식의 최종 산출물 적용 사례다.

## 2. 산출물

| # | 파일 | 작업 | 버전 |
|---|------|------|------|
| 1 | `opal/core/references/harness/reporting-template.md` | 신규 | v1.0 |
| 2 | `opal/core/AGENT.md` | 수정 (Eager 6.6 + 보고 형식 섹션 대체 + 부트스트랩 보고 reporting 칼럼) | v2.4 |
| 3 | `opal/core/references/opal-harness.md` | 수정 (§2 모듈 테이블 행 추가) | v4.8 |
| 4 | `opal/core/references/opal-pm.md` | 수정 (§8 신설) | v1.1 |

## 3. 의사결정 결과

| # | 결정 | 결과 |
|---|------|------|
| M-1 | 트리거 로딩 방식 | Eager 명시 (Step 6.6 신규) |
| M-2 | 보고/비보고 판별 | 알투 자율 판단 (명시 기준 없음) |
| M-3 | 기존 보고 형식 섹션 처리 | 통합 대체 (간단/상세 2종 → 3블록 참조, 역할 표기·Observability 유지) |
| M-4 (v1.1 재정의) | 단계별 결론 카드 표준화 | 캡틴 게이트 3종(PLAN 완료 / EXECUTE 후 / CLOSE 진입) 한정 표준 |

## 4. 검증 결과

| 단계 | 산출물 | 판정 |
|------|--------|------|
| QA-PLAN (v1.0) | QA-PLAN.md §1~§6 | Pass |
| QA-PLAN (v1.1 재검) | QA-PLAN.md §7 | Pass |
| QA-EXECUTE | QA-EXECUTE.md | Pass — Critical 0 / Warning 0 |
| 컨벤션 자동 진단 (Framework) | GC-CONVENTION-Framework-260510-1945.md | Pass — Critical 0 / High 0 / Medium 3 / Low 3 (이번 범위 밖) |
| PM Gate (PLAN) | 필수 4건 + 도메인 6건 | Pass |
| PM Gate (EXECUTE) | QA + 컨벤션 + 보존 항목 + 자기참조 + 142 가드 | Pass |

## 5. 자기참조 검증

reporting-template.md 본문 자체가 자기 정의한 원칙을 위배하지 않음:

- 3블록 구조 — 본문 흐름이 결론→근거→다음 패턴과 정합 ✅
- 일목요연(D-3) — 결론 1~2줄, 핵심 3개 이내, 표·리스트 우선, ASCII 박스 없음 ✅
- 시각 구분(D-4) — `---` 구분선, 굵은 헤딩, 빈 줄 분리 ✅
- 재사용성 — 프로젝트명·고유 경로 하드코딩 없음 ✅
- 플랫폼 독립 — Claude/Cursor/Gemini 분기 조건문 없음 ✅

## 6. 잔여 미해결 / 후속 태스크 후보

| # | 항목 | 비고 |
|---|------|------|
| 1 | install 재배포 | 신규 reporting-template.md를 `~/.opal/references/harness/`로 배포 — 캡틴이 명시적으로 지시 시 진행 |
| 2 | **GC-DP-C001 후속 태스크** — CONVENTIONS.md §변경이력 컬럼명 표준 명시화 | 컨벤션 진단 Medium/Low 6건 (`일시` vs `날짜` vs `일시(KST)` 불일치) — 별도 태스크 권고 |
| 3 | 142 태스크 병행 결과 동기화 | 142 마감 후 양 태스크 변경 파일 확인 (충돌 없음 검증됨, 단 통합 검증 권고) |

## 7. 142 태스크 충돌 가드 통과

- `scripts/install-mac.sh` 미수정 ✅
- `opal/core/references/community-skills-registry.json` 미수정 ✅
- 변경 영역 — 142(community-skills 영역) ↔ 143(보고 형식 영역) 완전 분리

## 8. 영향

- **알투 모든 응답 형식 통일** — PM(태스크) / PM(대화) / 비서 모드 모두 3블록 구조 적용
- **캡틴 게이트 가시성 향상** — semi-agentic 모드 PLAN/EXECUTE/CLOSE 3 게이트 보고 양식 표준화로 의사결정 일관성 확보
- **재사용성** — 다른 OPAL 프로젝트에도 그대로 적용 가능 (프로젝트 의존 없음)
- **install 배포 자동화** — `cp -Rf opal/core/references/. ~/.opal/references/`로 신규 파일 자동 배포

## 9. 변경이력 갱신 확인

| 파일 | 버전 | 일시 | 태스크 번호 |
|------|------|------|-------------|
| `reporting-template.md` | v1.0 | 2026-05-10 19:36 | (143) |
| `AGENT.md` | v2.4 | 2026-05-10 19:36 | (143) |
| `opal-harness.md` | v4.8 | 2026-05-10 19:36 | (143) |
| `opal-pm.md` | v1.1 | 2026-05-10 19:36 | (143) |

## 10. 적용 시점

- 다음 알투 세션부터 즉시 적용 (Eager 단계에서 자동 로드)
- 단, install 재배포 시점부터 모든 알투 인스턴스에 반영 — 미배포 시 본 프로젝트의 알투에서만 작동
