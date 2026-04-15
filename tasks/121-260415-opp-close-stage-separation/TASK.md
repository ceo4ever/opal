# TASK: 파이프라인 현황판 CLOSE 단계 분리 — DONE.md/State Gate/사용자 확인 귀속 재설계

> 작성일: 2026-04-15 | 작업 유형: 개선 | 적용 스킬: opp | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

파이프라인 현황판의 최종 단계(EXECUTE 또는 TEST)에 혼재되어 있던 `DONE.md 생성 / State Gate / 사용자 확인` 행을 **별도의 `CLOSE` 단계**로 분리한다. 모든 오케스트레이터가 공통 CLOSE 마감 블록을 공유하도록 표준화하여 단계 책임을 명확히 한다.

## 배경

현재 `harness/state-template.md`는 **"최종 단계(EXECUTE/TEST)"의 예외 규칙**으로 PM Gate 직후에 `DONE.md 생성 → State Gate → 사용자 확인`을 부착하도록 정의한다. 그 결과:

1. **단계 책임 혼재**: TEST 단계가 "테스트 통과"뿐 아니라 "태스크 전체 마감"까지 겸한다. EXECUTE 역시 동일.
2. **State Gate의 `단계` 필드 모호성**: "DONE.md 생성 중" 상태가 TEST 단계로 표기되어 의미 불일치 발생.
3. **템플릿 규칙 이원화**: "일반 단계 규칙"과 "최종 단계 예외 규칙"이 별도 존재하여 구조가 단순하지 않다.
4. **추가작업 진입의 모호성**: 완료 태스크에 다시 들어갈 때 "어느 단계로 되돌아가야 하는지"가 명확하지 않다.

모든 오케스트레이터의 마감 블록이 사실상 동일(`DONE.md 생성 → State Gate → 사용자 확인`)하므로, 이를 **공통 CLOSE 단계**로 승격하면 단계 책임이 깔끔하게 분리되고 템플릿 규칙이 단일화된다.

## 배경 분석 (대화에서 도출)

### 현황 파악

| 파일 | 현재 상태 | 문제 |
|------|----------|------|
| `opal/core/references/harness/state-template.md` L47 | "최종 단계(EXECUTE/TEST)" 예외 규칙으로 마감 블록 정의 | 공통 규칙과 예외 규칙이 공존 |
| `opal/core/references/opal-harness.md` §3 이벤트 테이블 | `사용자 확인 완료` / `태스크 완료` / `추가작업 진입` 이벤트가 단계와 분리되어 존재 | CLOSE 단계 도입 시 귀속 재정의 필요 |
| `opal/core/references/harness/additional-work.md` | `ADD_DONE.md 작성` → 절차 3단계 | CLOSE 재진입 개념으로 재표현 가능 |
| `opal/skills/opal-pilot-project/SKILL.md` STATE.md 도메인 치환값 | EXECUTE 단계에 `DONE.md 생성 / State Gate / 사용자 확인` 행 포함 | CLOSE 단계 행으로 이동 필요 |
| `opal/skills/opal-pilot-dev/SKILL.md` | TEST 단계에 마감 블록 혼재 | 동일 |
| `opal/skills/opal-pilot-dev-short/SKILL.md` | EXECUTE/TEST 단계에 마감 블록 혼재 | 동일 |
| `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | 동일 | 동일 |
| `opal/skills/opal-pilot-write-tech/SKILL.md` | 동일 | 동일 |
| `opal/skills/opal-pilot-sdd/SKILL.md` | 동일 | 동일 |

### 영향 범위

- **문서**: state-template.md, opal-harness.md §3, additional-work.md
- **스킬**: opp, opd, opds, opdw, opwt, opsdd의 "STATE.md 도메인 치환값" 섹션
- **기존 태스크 STATE.md**: 이미 생성된 STATE.md는 레거시 구조 유지. 신규 태스크부터 CLOSE 단계 반영.

## 확정된 설계 방향 (대화에서 합의)

1. **신규 단계명**: `CLOSE` (영문, 기존 단계명 TASK/PLAN/EXECUTE/TEST와 일관)
2. **CLOSE 단계 구성** (2행 고정, C안):
   - `DONE.md 생성`
   - `State Gate`
   - (사용자 확인 행 없음 — 직전 단계의 사용자 확인이 CLOSE 진입 게이트 역할)
3. **사용자 확인 위치 조정 (C안)**:
   - TASK/PLAN/ANALYSIS 등 **중간 단계의 `사용자 확인` 행은 유지** (단계별 승인 용도)
   - 직전 최종 단계(EXECUTE/TEST/QA/VERIFY) 끝에 `State Gate + 사용자 확인` 2행을 **신규 추가** — 태스크 마감 승인 = CLOSE 진입 게이트
   - 기존에 혼재되어 있던 `DONE.md 생성 / State Gate / 사용자 확인`은 제거하고, 그중 `DONE.md 생성 / State Gate`만 CLOSE 단계로 이동
   - 결과: 모든 단계가 일반 단계 패턴(`... PM Gate → State Gate → 사용자 확인`)을 100% 준수. "최종 단계 예외 규칙" 소멸
4. **CLOSE 진입 게이트 (신규 Guard)**: 사용자의 명시적 확인된 지시(`승인`, `확인`, `확인완료` 등)가 없으면 CLOSE 단계 진입 불가. agentic 모드에서도 이 규칙은 유지(다른 Gate는 PM 자율 통과 허용이지만 CLOSE 진입은 예외)
5. **추가작업 프로세스**: ADD_DONE.md 생성도 CLOSE 단계 재진입 개념으로 정리
6. **레거시 호환**: 기존 STATE.md 파일은 소급 변경 없음. 신규 태스크부터 적용

## 요구사항

- [x] **R-1**: `harness/state-template.md` — CLOSE 단계 공통 블록 규칙 추가 (C안)
  - **무엇을**: "최종 단계(EXECUTE/TEST)" 예외 규칙을 제거하고, "모든 파이프라인은 CLOSE 단계로 종료한다" 규칙 추가. CLOSE 단계 행 구성(`DONE.md 생성 / State Gate` — 2행)을 표준으로 명시. 직전 단계의 "사용자 확인"이 CLOSE 진입 게이트 역할을 한다는 원칙 포함.
  - **어디에**: `opal/core/references/harness/state-template.md` §"파이프라인 현황판 행 구성 규칙" + §"산출물 행 규칙"
  - **왜**: 예외 규칙을 공통 규칙으로 승격하여 템플릿 구조 단일화. 사용자 확인 위치를 일반 단계 패턴과 일치시켜 예외 소멸.
  - **AC**: state-template.md에 "CLOSE 단계" 항목이 추가되어 있고, "최종 단계(EXECUTE/TEST)" 예외 규칙 문구는 제거되어 있다. CLOSE 단계의 2행 구성(DONE.md 생성 / State Gate)이 명시되고, 직전 단계의 사용자 확인이 CLOSE 진입 게이트임이 서술되어 있다.

- [x] **R-2**: `opal-harness.md` §3 이벤트 테이블 갱신
  - **무엇을**: `사용자 확인 완료 / 태스크 완료 / 추가작업 진입 / 추가작업 완료` 이벤트를 CLOSE 단계 소속으로 재표기. "상태: 필드 전이 흐름" 설명에 CLOSE 단계 언급 추가
  - **어디에**: `opal/core/references/opal-harness.md` §3 STATE.md 기본 구조 이벤트 테이블
  - **왜**: 이벤트 테이블이 단계와 이벤트를 연결하는 SSOT이므로 CLOSE 단계 도입을 반영해야 함
  - **AC**: 이벤트 테이블의 `사용자 확인 완료 / 태스크 완료` 이벤트가 CLOSE 단계와 연관되도록 기술되어 있다. 상태 전이 흐름에 CLOSE 단계가 종료 단계로 명시되어 있다.

- [x] **R-3**: 6개 오케스트레이터 SKILL.md의 "STATE.md 도메인 치환값" 갱신 (C안)
  - **무엇을**: 각 SKILL.md의 "진행 현황 행 예시"에서 아래 변경을 적용. "단계 목록" 필드에 `CLOSE` 추가. 보고 형식에서 EXECUTE/TEST/QA/VERIFY 완료 시 "다음 단계(CLOSE)로 넘어갈까요?"로 사용자 승인을 받고, CLOSE는 자동 진행 후 마감 보고.
    - (a) EXECUTE/TEST 단계에 포함되어 있던 `DONE.md 생성 / State Gate / 사용자 확인` 3행 **제거**
    - (b) EXECUTE/TEST 단계 끝에 `State Gate / 사용자 확인` 2행 **신규 추가** (일반 단계 패턴 준수)
    - (c) `CLOSE` 단계 2행 **신규 추가**: `DONE.md 생성 / State Gate`
    - (d) opsdd의 경우 기존 Phase 6 `DONE`을 `CLOSE`로 리네이밍 + 기존 4행을 2행으로 통일 (첫 State Gate는 VERIFY 사용자 확인이 대체, 마지막 사용자 확인은 VERIFY 사용자 확인이 대체)
    - (e) opwt의 경우 QA 단계가 최종 단계이므로 QA 끝에 `State Gate / 사용자 확인` 추가 + CLOSE 2행
  - **어디에**:
    - `opal/skills/opal-pilot-project/SKILL.md`
    - `opal/skills/opal-pilot-dev/SKILL.md`
    - `opal/skills/opal-pilot-dev-short/SKILL.md`
    - `opal/skills/opal-pilot-dev-wireframe/SKILL.md`
    - `opal/skills/opal-pilot-write-tech/SKILL.md`
    - `opal/skills/opal-pilot-sdd/SKILL.md`
  - **왜**: 각 스킬이 자체 STATE.md 템플릿을 가지므로 스킬별 동기화 필요. C안 적용으로 모든 스킬이 일반 단계 패턴을 준수.
  - **AC**: 6개 SKILL.md 모두 `단계 목록`에 `CLOSE`가 포함되어 있고, 진행 현황 행 예시에서 (a) 기존 최종 단계에 포함되어 있던 마감 3행이 제거되고, (b) 최종 단계 끝에 `State Gate / 사용자 확인` 2행이 추가되고, (c) `CLOSE` 2행(`DONE.md 생성 / State Gate`)이 추가되어 있다.

- [x] **R-4**: `harness/additional-work.md` 업데이트 — ADD_DONE.md 생성을 CLOSE 재진입으로 명시
  - **무엇을**: "진입 절차"에서 "ADD_DONE.md 작성" 단계를 "CLOSE 단계 재진입 → ADD_DONE.md 생성 → State Gate → 사용자 확인"으로 재표현. 추가작업은 CLOSE 단계만 재실행한다는 원칙 추가.
  - **어디에**: `opal/core/references/harness/additional-work.md` §"추가작업 프로세스" §"진입 절차"
  - **왜**: CLOSE 단계를 도입하면 추가작업도 같은 마감 블록을 재사용하는 것이 자연스럽다
  - **AC**: additional-work.md에 "추가작업은 CLOSE 단계를 재진입한다"는 원칙이 명시되어 있고, ADD_DONE.md 생성이 CLOSE 단계 소속으로 기술되어 있다.

- [x] **R-5**: 레거시 호환 원칙 명시
  - **무엇을**: state-template.md 또는 opal-harness.md §3에 "기존 STATE.md는 소급 변경하지 않는다. 신규 태스크부터 CLOSE 단계를 반영한다" 단락 추가
  - **어디에**: `opal/core/references/harness/state-template.md` 또는 `opal/core/references/opal-harness.md` §3 레거시 호환 노트
  - **왜**: 진행중인 태스크 및 과거 완료 태스크의 STATE.md 파일을 일괄 수정하지 않도록 원칙 고정
  - **AC**: 레거시 호환 원칙 단락이 state-template.md 또는 opal-harness.md §3에 존재한다.

- [x] **R-6**: 변경이력 갱신
  - **무엇을**: 각 변경 문서(opal-harness.md, state-template.md, additional-work.md, opal-harness-agentic.md, 6개 SKILL.md)의 "변경이력" 테이블에 v{N} 항목 추가 (태스크 번호 121 참조)
  - **어디에**: 각 변경 문서 하단 변경이력 섹션
  - **왜**: OPAL 컨벤션 (변경이력은 문서 SSOT 유지의 핵심)
  - **AC**: 변경된 모든 문서의 변경이력 테이블에 121 태스크가 참조된 새 버전 행이 추가되어 있다.

- [x] **R-7**: CLOSE 진입 게이트 — 사용자 명시 승인 필수 규칙 명문화 (신규)
  - **무엇을**: "사용자의 확인된 지시(`승인`/`확인`/`확인완료` 등 명시적 표현)가 없으면 CLOSE 단계 진입 불가"라는 불가침 규칙을 하네스에 추가. agentic 모드에서도 이 규칙은 유지(다른 Gate는 PM 자율 통과 허용하나 CLOSE 진입은 예외).
  - **어디에**:
    - `opal/core/references/opal-harness.md` §1 Guards — "CLOSE 진입 게이트" 서브섹션 신설
    - `opal/core/references/harness/state-template.md` — CLOSE 단계 규칙 서술 내부에 반영
    - `opal/core/references/opal-harness-agentic.md` §7 "유지되는 규칙" 테이블 — "CLOSE 진입 게이트" 행 추가
  - **왜**: CLOSE는 태스크 마감 단계. 자동 진입은 사용자가 의도하지 않은 마감을 유발할 수 있다. 특히 agentic 모드에서 PM 자율 진행이 허용되는 반면, 태스크 전체 마감만은 사용자 의사결정 영역임을 명문화.
  - **AC**: (1) `opal-harness.md` §1 Guards에 "CLOSE 진입 게이트 — 사용자의 확인된 지시(승인/확인/확인완료 등)가 없으면 CLOSE 단계 진입 불가" 규칙이 존재한다. (2) `state-template.md` CLOSE 단계 규칙에 같은 원칙이 서술되어 있다. (3) `opal-harness-agentic.md` §7 유지되는 규칙 테이블에 "CLOSE 진입 게이트" 행이 추가되어 "agentic 모드에서도 CLOSE 진입은 사용자 승인 필수"임이 명시되어 있다.

## 제약 조건

- `~/.opal/` 경로 직접 수정 금지 (확정 기준 #2) — 반드시 프로젝트 소스(`opal/core/`, `opal/skills/`)에서 수정
- 기존 STATE.md 파일(진행 중 포함) 소급 변경 금지 — 120번 등 진행 중인 태스크의 파일 건드리지 말 것
- 레거시 호환 원칙 준수 — 기존 파이프라인 현황판 구조를 유지하는 세션 복원이 가능해야 함
- `STATE.md 도메인 치환값` 테이블의 "모드" 필드는 변경하지 않음 (단계 목록만 갱신)
- 120번 태스크 폴더(`tasks/120-260415-opp-pm-constraint-citation-rule/`)는 다른 알투가 작업 중이므로 절대 건드리지 않음

## 기술 스택

- Markdown 문서 편집
- OPAL 프레임워크 컨벤션 (`harness/header-rules.md` — .md @header 규칙 적용 대상 아님: 표준 하네스 문서는 예외)

## 관련 문서

- `opal/core/references/opal-harness.md` — §1 Guards(R-7) + §3 이벤트 테이블 + 레거시 호환 원칙
- `opal/core/references/opal-harness-agentic.md` — §7 유지되는 규칙 (R-7 CLOSE 진입 게이트 행 추가)
- `opal/core/references/harness/state-template.md` — 파이프라인 현황판 행 구성 규칙 (핵심 변경)
- `opal/core/references/harness/additional-work.md` — 추가작업 프로세스
- `opal/skills/opal-pilot-project/SKILL.md` — opp 치환값
- `opal/skills/opal-pilot-dev/SKILL.md` — opd 치환값
- `opal/skills/opal-pilot-dev-short/SKILL.md` — opds 치환값
- `opal/skills/opal-pilot-dev-wireframe/SKILL.md` — opdw 치환값
- `opal/skills/opal-pilot-write-tech/SKILL.md` — opwt 치환값
- `opal/skills/opal-pilot-sdd/SKILL.md` — opsdd 치환값
- `docs/CONVENTIONS.md` — 변경이력 작성 컨벤션
