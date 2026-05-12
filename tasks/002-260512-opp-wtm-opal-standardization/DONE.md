# DONE: 002 wtm-agent OPAL 표준화 + cmux 통합 + 사용자 surface 재사용

> 완료일: 2026-05-12 22:15 KST | 모드: semi-agentic | 스킬: //opp
> 시작: 2026-05-12 18:10 KST | 소요: 약 4시간 5분

## 1. 작업 결과 요약

`wtm-agent`를 OPAL 프레임워크 표준 워커 구조로 완전 통합하고, cmux browser를 Phase 2 폴백으로 추가하며, 사용자 cmux 브라우저 surface를 재사용해 마크다운으로 변환하는 인터페이스(3모드)를 도입했다. PLAN 12 Step / 5 Phase 모두 실행 완료.

## 2. 산출물

### 신규 (3건)

| 파일 | 크기 | 핵심 |
|------|------|------|
| `opal/tools/cmux-tool/run.sh` | 8611B (+x) | A/B/C 3모드 + 환경 감지 + JSON 8필드 + B/C cleanup 절대 금지 |
| `opal/tools/cmux-tool/README.md` | 5256B | 도구 사용법·출력 스키마·에러 코드·안전 가드 |
| `opal/agents/opal-wtm-agent/AGENT.md` | 5897B | 표준 7단계 디스패치 + 안전 가드 2차 담당 + v1.0 |

### 수정 (8건)

| 파일 | 변경 |
|------|------|
| `skills/web-to-markdown/SKILL.md` | Phase 1→2(cmux)→3(playwright) 재구성 + `--surface` 3모드 + `--wait <ms>` + v1.9 |
| `opal/core/references/agents.md` | §wtm-agent → §opal-wtm-agent 전면 갱신 + v1.4 |
| `scripts/install-mac.sh` | cmux-tool 어댑터 + 멱등 가드 + v2.2 |
| `opal/skills/opal-agent-creator/SKILL.md` | L66 예시 갱신 + v1.2 |
| `docs/PROJECT.md` | agents/ 구조 안내 갱신 |
| `docs/CONVENTIONS.md` | 범용 에이전트 폴더 설명 갱신 |
| `docs/ARCHITECTURE.md` | 다이어그램/표/트리뷰 갱신 + cmux-tool 추가 |
| `tasks/002-.../PLAN.md` | §3 Step + §4 QA 체크박스 [x] 갱신 + v1.1 보완 행 |

### 삭제 (2건)

| 경로 | 사유 |
|------|------|
| `agents/wtm-agent/AGENT.md` | 신규 위치 `opal/agents/opal-wtm-agent/`로 이행 완료 |
| `agents/wtm-agent/` | 빈 디렉토리 제거 |

## 3. QA 결과

| 단계 | 판정 | 비고 |
|------|------|------|
| QA-PLAN (1차) | Needs Revision | Critical 1 + Warning 3 (R-9 grep 검증 / JSON 필드 수 / 안전 가드 위치 / 변경이력 포맷) |
| QA-PLAN (재검증) | **Pass** | 4건 모두 해소, 회귀 없음 |
| QA-EXECUTE | **Pass** | 15/15 통과 (GE-1~GE-3, C-1~C-7, Q-1~Q-5, 정적 분석 F-6/F-7/F-9) |

## 4. 요구사항 충족 (R-1~R-13)

전체 13건 모두 `[x]` 충족.

| R | 결과 |
|---|------|
| R-1 opal-wtm-agent 신규 작성 | ✅ |
| R-2 wtm-agent 삭제 + 참조 갱신 | ✅ |
| R-3 cmux-tool 래퍼 신규 | ✅ |
| R-4 cmux 환경 감지 + 미설치 안내 | ✅ |
| R-5 Phase 폴백 체인 재정의 | ✅ |
| R-6 사용자 surface 3모드 지원 | ✅ |
| R-7 `--wait <ms>` 옵션 | ✅ |
| R-8 SKILL.md 갱신 | ✅ |
| R-9 Crawl4AI 부정합 3건 해소 | ✅ |
| R-10 agents.md 등록 갱신 | ✅ |
| R-11 install-mac.sh cmux-tool 등록 | ✅ |
| R-12 변경이력 추가 | ✅ |
| R-13 surface 추출 안전 가드 | ✅ |

## 5. 검증 종합

| 검증 항목 | 결과 |
|----------|------|
| bash syntax (`cmux-tool/run.sh`, `install-mac.sh`) | OK |
| JSON 8필드 SSOT 일관성 (5 파일) | 일관 |
| 변경이력 포맷 `YYYY-MM-DD HH:mm KST + (002)` | 단일 통일 |
| Crawl4AI 잔존 (web-to-markdown 관련) | 0건 |
| wtm-agent 잔존 (단어 경계, opal- 제외) | 0건 (변경이력 행 예외) |
| cmux 실환경 통합 테스트 (F-1~F-5, F-8, F-10) | 미실행 (정적 분석으로 대체, 캡틴 확인 발화) |

## 6. 잔여 / 후속 태스크 후보

| 우선순위 | 항목 | 비고 |
|----------|------|------|
| P1 | cmux 실환경 통합 테스트 7건 | F-1~F-5/F-8/F-10 — 실제 호출로 분기 검증 (캡틴 환경에서 1회 실측 권장) |
| P2 | install-mac.sh 재실행으로 `~/.opal/tools/cmux-tool/` + `~/.opal/agents/opal-wtm-agent/` 배포 | 별건 — 캡틴이 install 실행 시 자동 |
| P2 | Linux/Windows 어댑터 (cmux-tool 등록) | 본 태스크 범위 외 — install-mac.sh만 변경됨 |
| P3 | ANALYSIS 단계 model 승격 룰 (별건) | 2026-05-12 대화에서 보류 — 별도 태스크 |

## 7. 변경이력 SSOT 일람

| 파일 | 신규 행 |
|------|---------|
| `opal/agents/opal-wtm-agent/AGENT.md` | v1.0 (초기 작성) |
| `opal/tools/cmux-tool/README.md` | 신규 — 헤더만 |
| `skills/web-to-markdown/SKILL.md` | v1.9 |
| `opal/core/references/agents.md` | v1.4 |
| `opal/skills/opal-agent-creator/SKILL.md` | v1.2 |
| `scripts/install-mac.sh` | v2.2 |
| `tasks/002-.../PLAN.md` | v1.1 (QA 보완) |

## 8. 회고 (간략)

- **자동 루핑 1회 발효**: QA-PLAN Needs Revision → PLAN 워커 재소환 → 재QA Pass. §1 Guards 폴백 1/1 정상 작동.
- **실측 기반 PLAN의 신뢰도**: cmux 0.64.3 실측(naver.com 315KB 추출 + surface:3 cross-workspace 접근)으로 명령 시퀀스를 확정 후 PLAN 작성 → EXECUTE 워커가 추측 없이 구현 가능했음.
- **JSON 8필드 SSOT 단일 정의 효과**: §2 N-3에 한 곳 정의 후 4개 파일 참조 → QA에서 일관성 검증이 단순화.
- **안전 가드 3계층 분리**: cmux-tool 시그널 → opal-wtm-agent 가공·거부 → SKILL.md 노출. 책임 분리로 각 계층 독립 검증 가능.
