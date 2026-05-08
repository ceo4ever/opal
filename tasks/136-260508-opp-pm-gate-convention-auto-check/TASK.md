# TASK: PM Gate 컨벤션 자동 진단 — opal-convention-checker 영역별 병렬 디스패치

> 작성일: 2026-05-08 | 작업 유형: 개선 | 적용 스킬: opp | 모드: interactive
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

PM Gate에 "컨벤션 자동 진단" 항목을 신설하여, EXECUTE 완료 후 `changed_files`를 영역별로 분할해 `opal-convention-checker`에 병렬 디스패치하고 영역별 보고서로 컨벤션 준수를 객관 검증하는 절차를 하네스에 정착시킨다.

## 배경

현재 하네스(D-1)의 PM Gate 검토 11항목 중 **컨벤션 준수**를 명시적으로 진단하는 항목이 없다. 5번 "참조 문서 내용 반영" / 6번 "프로젝트 원칙 부합"으로 간접 검증되지만 PM 자연어 평가에 의존하여 미세 위반(네이밍, 들여쓰기, import 순서 등)이 누락된다. `opal-convention-checker`(D-2) 진단 도구가 이미 존재하지만 `opal-pilot-gc`(opgc)의 CHECK 단계에서만 호출되어 **별도 슬래시 명령(`//opgc`)을 수동 발동**해야 한다. 그 결과 EXECUTE가 컨벤션을 위반해도 PM Gate에서 자동으로 잡히지 않는다.

## 배경 분석 (대화에서 도출)

| 단계 | 현재 상태 | 갭 |
|------|----------|-----|
| PLAN 에이전트 자체 로드 | ✅ `docs/CONVENTIONS.md` Read 명시(D-6 §자체 로드 문서) | PLAN.md에 `[MUST]` 원문 인용으로 박는 강제 절차 미정의 |
| PM → EXECUTE 워커 디스패치 | ⚠️ 인용 의무 룰 존재(D-5 §Step 3) | 인용 카탈로그에 "컨벤션 [MUST] 항목" 명시 부재 — PM 재량 누락 가능 |
| EXECUTE 워커(BE/FE 등) 자체 로드 | ❓ 도메인 한정일 가능성 | PLAN 에이전트만 "도메인 제한 없이 docs/ 전체"라고 명시 |
| PM Gate 검토 11항목 | ❌ 컨벤션 항목 부재 | 자연어 평가에 의존, 미세 위반 누락 |
| 자동 사후 진단 | ❌ 없음 | opgc는 수동 발동 |

본 태스크는 **사후 검증 자동화(제안 B)**에 한정한다. 사전 주입 강화(제안 A)는 별도 후속 태스크로 분리한다.

## 확정된 설계 방향 (대화에서 합의)

1. **호출 시점**: 매 EXECUTE Step이 아닌, **태스크 단위 EXECUTE PM Gate 1회**에서 호출. 비용 합리화.
2. **호출 입력**: EXECUTE가 반환한 `changed_files`만 (소스 파일에 한정 — docs/만 변경된 경우 스킵).
3. **영역별 병렬 디스패치 (옵션 a)**:
   - `changed_files`를 `docs/PROJECT.md` "## 프로젝트 구성" 섹션 경로 prefix 매칭(D-3)으로 영역별 분할
   - 영역별로 `opal-convention-checker`를 따로 호출 (scope=영역명)
   - 영역별 보고서 산출: `tasks/{NNN}-.../GC-CONVENTION-{area}-{ts}.md`
4. **단일 문서 프로젝트(허브+링크 미적용)**: scope 무관 허브 전체 적용. 보고서 1개 — `GC-CONVENTION-{ts}.md` (D-4 §허브+링크 모델은 선택).
5. **판정**:
   - Critical/High 이슈 ≥1건 → PM Gate **Fail** → 워커 재지시 1회 → 미해결 시 캡틴 에스컬레이션
   - Medium 이하만 → PM Gate **Pass** + 캡틴에 요약 보고
6. **스킵 조건**:
   - `changed_files` = 0건
   - `changed_files`가 컨벤션 적용 대상 외만 포함 (docs/, .opal/, *.md 등)
   - `docs/CONVENTIONS.md` 부재 → 체커가 자체적으로 "초안 생성 유도" 보고서만 작성하고 PM Gate Pass
7. **하위 호환**: `.opal/AGENT.md` 미존재 프로젝트는 PM Gate 자체가 스킵되므로(D-1 §3) 컨벤션 자동 진단도 동시 스킵.

## 요구사항

- [x] **R-1: PM Gate 검토 항목 신설** — `opal/core/references/harness/pm-review-gate.md` §검토 절차에 "13. 컨벤션 자동 진단" 항목 추가
  - 어디에: D-1 §검토 절차 (12번 "STATE.md 정합성 자동 검증" 다음)
  - 왜: 확정 방향 §1 — 객관 진단 자동화
  - AC: §검토 절차에 13번 항목이 존재하고, 트리거 조건/호출 절차/판정 기준/스킵 조건이 모두 명시되어 있다 (소절 4개 이상)

- [x] **R-2: 영역 자동 판정 규약 명시** — D-1 §13에 영역 분할 의사코드 또는 D-3 §라우팅 참조 링크 포함
  - 어디에: D-1 §13 신설 항목 내부
  - 왜: 확정 방향 §3 — `docs/PROJECT.md` prefix 매칭 규약 재사용
  - AC: D-3 §라우팅의 의사코드를 그대로 따른다는 명시(또는 링크 인용)가 존재하고, 매칭 실패 시 "허브 전체 적용 폴백"이 정의되어 있다

- [x] **R-3: opal-convention-checker 입력 명세 확장** — `opal/agents/opal-convention-checker/AGENT.md` §입력 명세에 "PM Gate 호출 시나리오" 항목 추가
  - 어디에: D-2 §입력 명세 (현재 7개 파라미터 테이블 하단)
  - 왜: 확정 방향 §3·§4 — `target_files=changed_files`, `scope=영역명 또는 all`, `task_folder=현재 태스크` 호출 규약 명시
  - AC: §입력 명세에 PM Gate 호출 시 파라미터 매핑 표가 존재하고, 영역별 병렬 디스패치 시 각 호출이 독립 시간 ts를 공유하는지 또는 분리되는지 규약이 명시되어 있다

- [x] **R-4: 보고서 파일명 규약 정의** — D-2 §실행 프로세스 Phase 5에 영역별 다중 보고서 파일명 규약 추가
  - 어디에: D-2 §Phase 5 (현재 `GC-CONVENTION-{timestamp}.md` 단일)
  - 왜: 확정 방향 §3·§4 — 영역별 보고서 분리
  - AC: 영역별 호출 시 `GC-CONVENTION-{area}-{ts}.md` 포맷, 단일 호출 시 기존 `GC-CONVENTION-{ts}.md` 포맷이 모두 정의되어 있다

- [x] **R-5: 판정 기준 명문화** — D-1 §13에 Critical/High = Fail / Medium 이하 = Pass 판정 기준 명시
  - 어디에: D-1 §13 신설 항목 내부
  - 왜: 확정 방향 §5 — 자동 판정의 일관성
  - AC: 심각도별 판정 표가 존재하고, Fail 시 1회 재지시 → 캡틴 에스컬레이션 흐름이 D-1 §4 Gate Fail 공통 처리와 정합적으로 연결된다

- [x] **R-6: 스킵 조건 명문화** — D-1 §13에 호출 스킵 조건 3종 명시
  - 어디에: D-1 §13 신설 항목 내부
  - 왜: 확정 방향 §6 — 불필요 호출 비용 차단
  - AC: changed_files=0 / 컨벤션 적용 외 / CONVENTIONS.md 부재 3종이 명시되어 있고, 각각의 처리(스킵 + Pass / 체커 자체 처리) 방식이 구분되어 있다

- [x] **R-7: 하위 호환성 명문화** — D-1 §13에 `.opal/AGENT.md` 미존재 시 자동 스킵 동작 명시
  - 어디에: D-1 §13 신설 항목 내부
  - 왜: 확정 방향 §7 — 기존 프로젝트 깨지지 않게 보장
  - AC: AGENT.md 미존재 시 PM Gate 자체 스킵으로 컨벤션 자동 진단도 동시 스킵된다는 문장이 존재한다

- [x] **R-8: opp/opd/opds/oppd SKILL.md PM Gate 점검 목록 갱신 검토** — 각 오케스트레이터의 "PM Gate 점검 목록" 표에 컨벤션 진단 산출물(`GC-CONVENTION-*.md`) 추가가 필요한지 판단
  - 어디에: `opal/skills/opal-pilot-project/SKILL.md` 외 dev/short/wireframe 오케스트레이터
  - 왜: PM Gate 점검 목록은 산출물·체크리스트 위치 SSOT (D-1 §PM Gate 자가 진단 절차 §2)
  - AC: 각 SKILL.md의 점검 목록에 EXECUTE Phase의 산출물 컬럼에 `GC-CONVENTION-*.md`가 추가되어 있거나, 추가하지 않는 명확한 사유가 PLAN.md에 기재되어 있다

## 제약 조건

- **OPAL 자체는 단일 `docs/CONVENTIONS.md`** 사용 — 허브+링크 모델 미적용. 본 변경은 OPAL 자체에서 동작하되, 영역 분할 동작은 허브+링크 프로젝트에서만 효과를 발휘한다.
- **하위 호환 보장** — 기존 PM Gate 통과 태스크의 동작이 깨지면 안 된다. AGENT.md 미존재 / CONVENTIONS.md 부재 시 자동 스킵.
- **비용 제어** — EXECUTE 매 Step 호출이 아닌 EXECUTE PM Gate 단위 1회 호출 (영역별 분할 시 N회).
- **자동 루핑 제약 준수** — Fail 시 워커 재지시 최대 1회 (D-1 §검토 절차 §판정 부합).
- **본 태스크는 사후 검증 자동화(제안 B)만 다룸** — 사전 주입 강화(제안 A: dispatch-process.md 인용 카탈로그 확장)는 별도 후속 태스크로 분리한다.

## 기술 스택

- Markdown, YAML (OPAL 프레임워크 문서/에이전트 정의)
- 호출 측: `opal-convention-checker`(서브에이전트), state-tool (게이트 갱신)
- 코드 변경 없음 (문서·에이전트 정의 변경 한정)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | pm-review-gate.md | `opal/core/references/harness/pm-review-gate.md` | PM Gate 검토 절차 SSOT — §13 신설 대상 |
| D-2 | 설계 | opal-convention-checker AGENT.md | `opal/agents/opal-convention-checker/AGENT.md` | 입력 명세 확장 + Phase 5 보고서 파일명 규약 갱신 대상 |
| D-3 | 설계 | context-injection.md | `opal/core/references/pm/context-injection.md` | "## 프로젝트 구성" prefix 매칭 라우팅 규약 — §라우팅 의사코드 재사용 |
| D-4 | 설계 | conventions-hub-model.md | `opal/core/references/conventions-hub-model.md` | 허브+링크 모델 규약 — 단일 문서 프로젝트 분기 근거 |
| D-5 | 설계 | dispatch-process.md | `opal/core/references/pm/dispatch-process.md` | 인용 의무 규칙 — 본 태스크는 참고만, 변경은 별도 태스크 |
| D-6 | 설계 | opal-plan-agent AGENT.md | `opal/agents/opal-plan-agent/AGENT.md` | PLAN 에이전트 자체 로드 명세 — 현재 갭 근거 |
| D-7 | 설계 | opp SKILL.md | `opal/skills/opal-pilot-project/SKILL.md` | EXECUTE PM Gate 호출 시점 + PM Gate 점검 목록 갱신 검토 대상 |
| D-8 | 설계 | docs/PROJECT.md | `docs/PROJECT.md` | OPAL 자체 "## 프로젝트 구성" 단일 요소 — 영역 분할 폴백 검증 |
| D-9 | 설계 | docs/CONVENTIONS.md | `docs/CONVENTIONS.md` | OPAL 컨벤션 SSOT — 단일 문서 모델 동작 검증 |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §2 참조.
