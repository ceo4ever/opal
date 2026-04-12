# QA: PLAN — 에이전트 아이콘 Observability + 메모리 브리핑 간소화

> 검토일: 2026-04-08 | 판정: **Needs Revision**

## 1. 요약

PLAN은 TASK의 3개 요구사항(R1: 하네스 확장, R2: 에이전트 frontmatter 추가, R3: 메모리 브리핑 간소화)을 4개 Step으로 분해하고, 의존성을 고려한 순서(하네스 → CONVENTIONS → 에이전트 → 메모리)를 제시했다. 구현 계획과 QA 체크리스트는 포괄적이나, Step 1(하네스 §5 확장)과 Step 2(CONVENTIONS)의 변경 내용이 구체성이 부족하여 즉시 실행에 어려움이 있다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| GP-1 | 즉시 실행 가능성 | Warning | Step 1(하네스 §5)과 Step 2(CONVENTIONS)의 변경 내용이 구체적이지 않음. 특히 하네스의 "아이콘 룩업" 서브섹션 위치, 테이블 재구성 방식 등이 명확하지 않음 |
| GP-2 | 의존성 순서 | Pass | 의존성이 올바르게 분석되었고, 순서 근거가 명확함 (하네스 → CONVENTIONS → 에이전트 → 메모리) |
| GP-3 | TASK 반영 | Pass | TASK의 R1, R2, R3이 모두 PLAN의 Step 1~4에 매핑됨. AC(Acceptance Criteria)도 포함 |
| GP-4 | 파일 목록 완전성 | Pass | 8개 파일 모두 포함 (opal-harness.md, CONVENTIONS.md, 5개 에이전트, AGENT.md) |
| GP-5 | 설계 구체성 | Warning | R1의 테이블 변경 내용이 애매함. "기존 | 변경 후" 예시가 있지만 정확한 마크다운 문법이나 전체 문맥(기존 테이블 구조)이 없어 변경 범위가 불명확. CONVENTIONS 변경도 마찬가지 |
| GP-6 | 체크리스트 커버리지 | Pass | 4개 Step과 QA 체크리스트로 모든 요구사항이 분해됨. 기능 테스트, 일관성 테스트, 문서 품질 테스트 포함 |

## 3. 지적 사항

### Critical — 실행 불가 (수정 필수)

**C1: Step 1(하네스 §5) 변경 내용 불명확**

- PLAN에서는 "422-436행"의 "행위 주체 표시 섹션"을 수정한다고 했으나, 실제 하네스 파일을 보지 않고 이 범위가 정확한지 확인 불가
- "아이콘 룩업" 서브섹션을 "테이블 앞에 삽입"한다고 했지만, 기존 §5의 구조가 무엇인지(제목 → 서브섹션 → 테이블 구조인지)가 불명확하여 삽입 위치 판단 어려움
- 테이블 변경 예시:
  ```markdown
  | 기존 | 변경 후 |
  | `⚙️ 워커 디스패치:` | `{icon} 디스패치: {단계명} — {설명}` |
  ```
  하지만 기존 테이블의 다른 행(예: `📋 알투[PM] 직접:` 행)과의 조화, 행 순서, 마크다운 포맷팅이 불명확

**대응 필요 사항**:
1. 수정 전에 `opal/core/references/opal-harness.md`의 §5 섹션을 **Read하여** 정확한 라인 범위와 기존 구조 확인
2. PLAN의 Step 1 섹션을 "§5의 기존 내용 (XX~YY행)" 형식으로 재정의
3. 테이블 변경 시 **기존 전체 테이블 스냅샷** + **변경 후 전체 테이블 스냅샷** 제시

**C2: Step 2(CONVENTIONS.md) 변경 내용 불명확**

- PLAN의 제시 코드:
  ```yaml
  icon: {이모지}         # 에이전트만 (선택, 디폴트: ✨)
  ```
  하지만 기존 CONVENTIONS.md가 코드 블록으로 YAML 예시를 보여주는지, 설명 테이블로 정의하는지 불명확
- "72행 부근"이라는 표현으로 정확한 라인 범위 미정의
- 기존 구조(이전 필드들)와의 위치 관계가 불명확

**대응 필요 사항**:
1. 수정 전에 `docs/CONVENTIONS.md`의 YAML Frontmatter 섹션을 **Read하여** 정확한 라인 범위와 포맷(코드 블록인지 테이블인지) 확인
2. PLAN의 Step 2를 "기존 코드 블록 (XX~YY행)" 형식으로 재정의
3. **기존 CONVENTIONS.md 스냅샷** + **변경 후 스냅샷** 제시

### Warning — 실행 가능하나 개선 권장

**W1: Step 3(에이전트 frontmatter) 구체성**

- 5개 에이전트와 각각의 icon 값이 명시되어 있음 (✨, 🔍, ⚡, 🧪, 🌐)
- 하지만 wtm-agent의 경우 기존 `color: green` 필드 다음에 `icon`을 추가한다는 설명만 있고, 현재 wtm-agent의 실제 frontmatter 구조를 보여주지 않음
- PLAN §2.2.3에서 "wtm-agent의 기존 `color: green` 필드는 유지. `icon`은 `color` 다음 줄에 추가"라고 했으나, frontmatter에 `color` 필드가 정말 있는지, 다른 필드들과의 관계는 어떤지 불명확

**W2: Step 4(메모리 브리핑) 변경 내용 명확도**

- 삭제할 4단계와 남은 단계들을 텍스트로 비교하고 있으나, 줄 번호 범위(215-221행)가 정확한지 미확인
- PLAN의 "기존" 코드 블록과 "변경 후" 코드 블록은 명확하지만, 실제 AGENT.md 파일에서 이 섹션이 어느 부분인지(예: ## 절차 섹션인지) 확인 필요

**W3: 배포본 미동기화 리스크**

- PLAN §5에서 "배포본(`~/.opal/`) 미동기화" 리스크를 명시했으나, TASK의 제약 조건 "소스 파일만 수정 (`opal/core/`, `agents/`). `~/.opal/` 배포본 직접 수정 금지"와의 관계가 불명확
- 리스크 대응 "install 스크립트로 배포하면 해결"이라는 설명은 이 태스크의 범위 외이므로, PLAN에서 "이 태스크는 소스 파일만 수정하므로 배포 스크립트 실행은 별도 문제"라고 명시하는 게 나음

### Info — 참고 사항

**I1: CONVENTIONS.md 존재 확인**

- PLAN에서는 CONVENTIONS.md를 수정 대상으로 명시했으나, TASK에서는 언급되지 않음
- PLAN §1.3에서 "CONVENTIONS.md YAML Frontmatter 스키마 (68-82행)"라고 했는데, 이게 현재 프로젝트에 존재하는 파일인지 미확인
- 만약 파일이 없다면, PLAN의 파일 목록(§2)이 부정확함

**I2: Icon 선정 근거의 명확성**

- 각 에이전트의 icon 선정 근거가 설명되어 있으나, 이미지/이모지 렌더링 환경(예: 터미널, Markdown 뷰어)에서 의도대로 표시되는지 확인 필요
- 예: 🔍(돋보기)는 의도대로 보이는지, 🌐(지구본) vs 🔗(링크) 중 웹을 더 잘 표현하는 건 어느 것인지 등

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md | R1: AC의 "행위 주체 표시 테이블 확장" 요구사항이 PLAN Step 1에 반영되었으나, 구체성 부족 | Warning |
| TASK.md | R2: AC의 "5개 에이전트에 icon 필드 추가" 요구사항이 명확히 반영됨 | Pass |
| TASK.md | R3: AC의 "브리핑 절차에 하위 파일 Read 단계 없음" 요구사항이 명확히 반영됨 | Pass |
| TASK.md | 제약 조건: 소스 파일만 수정 — PLAN이 `opal/core/`, `agents/`, `docs/`만 수정 대상으로 지정 (배포본 미포함) | Pass |

## 5. 판정

**Needs Revision**

PLAN은 의존성 분석, 파일 목록, 전체 구조 측면에서는 우수하나, **Step 1(하네스 §5 변경)**과 **Step 2(CONVENTIONS 변경)**의 구체성이 부족하여 즉시 실행이 어렵다. 특히 기존 파일의 정확한 라인 범위와 구조를 파악하지 않은 상태에서 "422-436행", "72행 부근" 같은 모호한 표현만 제시되어 있다. 실행 전에 다음 3개 파일을 Read하여 PLAN의 Step 1, 2 섹션을 재정의하기를 권장한다:

1. `/Volumes/Data/AiStudio/workspace/opal/opal/core/references/opal-harness.md` — §5 섹션 정확한 라인 범위 + 기존 구조 파악
2. `/Volumes/Data/AiStudio/workspace/opal/docs/CONVENTIONS.md` — YAML Frontmatter 섹션 정확한 라인 범위 + 포맷 확인
3. `/Volumes/Data/AiStudio/workspace/opal/agents/wtm-agent/AGENT.md` — 기존 frontmatter 구조 확인 (color 필드 위치 등)

수정 후 다시 QA를 진행하면 Pass 판정 가능할 것으로 예상된다.
