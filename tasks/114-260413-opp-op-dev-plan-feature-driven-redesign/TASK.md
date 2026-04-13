# TASK: op-dev-plan 탑다운 기능 중심 구조 개편 + 후속 파이프라인 정합화

> 작성일: 2026-04-13 | 작업 유형: 개선 | 적용 스킬: opp | 모드: interactive
> 입력: 캡틴과의 대화 (PLAN 구조 검토 → 개편 방향 합의)
> 출력: TASK.md

## 작업 목표

`op-dev-plan` PLAN 단계를 **탑다운 기능 중심 구조**로 전면 개편하고, 중복 산출물인 `execution-plan.json`을 폐기하여 PLAN.md를 단일 SSOT로 통합한다. 개편된 PLAN 구조를 소비하는 후속 단계 스킬(`op-dev-execute`, `op-dev-qa`, `ui-designer`)을 동일 태스크 내에서 정합화한다.

## 배경

현재 `op-dev-plan`은 **파일/레이어 중심 구조**로 설계되어 다음 문제가 누적되고 있다:

1. 한 태스크에 여러 기능이 포함되어도 기능 단위 그룹핑이 없어 "이 기능이 완성되었는가"를 판정하기 어렵다
2. `execution-plan.json`이 PLAN.md의 파일 변경 계획·구현 순서·테스트 전략과 필드가 크게 겹쳐 중복 관리 비용이 높다
3. 환경변수·배치·마이그레이션이 1급 시민으로 존재하지 않아 누락 리스크가 있다
4. QA 체크리스트가 기능 ID와 매핑되지 않아 커버리지 추적이 불가하다
5. `execution-plan.json`이 FE는 screens(기능 단위)지만 BE는 layers(레이어 단위)로 비대칭이다

이 개편은 opsdd 파이프라인의 SPEC-PLAN.md가 이미 md 단일 SSOT로 기능 단위 설계를 성공적으로 수행하고 있는 선례를 op-dev-plan에 이식하는 작업이다. opsdd를 대체하지 않고, "요구사항이 이미 확정된 다기능 태스크"를 위한 중간 선택지를 확립한다.

## 배경 분석 (대화에서 도출)

### 현재 op-dev-plan 구조의 한계 (파일 중심 평면화)

| 섹션 | 실제 단위 | 기능 관점 |
|------|---------|---------|
| 1. 코드 분석 | 파일별 관련 파일 테이블 + 호출자/피호출자 | ❌ |
| 2. 구현 계획 > 파일 변경 계획 | 파일 단위 (신규/수정/영향) | ❌ |
| 2. 구현 계획 > 구현 순서 | 파일 단위 + 영역 태그([FE]/[BE]/[공통]) | ❌ |
| 2. 구현 계획 > 핵심 설계 | 클래스/함수 시그니처, 데이터 모델 | 🔸 FE 화면만 기능 단위 |
| 3. 실행 체크리스트 | 1파일 = 1작업 (`plan-guide.md` L185) | ❌ |
| `execution-plan.json` | `frontend.screens`: 기능 단위 / `backend.layers`: 레이어 단위 | 🔸 FE만 기능 단위 |

### opsdd와의 비교

- `op-sdd-plan`: `SPEC.md = 1 기능` 전제. SPEC-PLAN.md에 **아키텍처+데이터+API+보안+에러+ACT 분해**를 기능 단위로 통합. AC-FR-TS-ACT 추적 매트릭스 존재. **완전한 기능 단위 설계.**
- `op-dev-plan` (현재): 기능 추적 없음, 파일 중심.

### PLAN.md ↔ execution-plan.json 중복 실체

개편안을 그대로 적용할 경우 두 산출물이 거의 모든 주요 필드(기능 목록/AC/파일 변경/FE 화면/BE 레이어/환경/배치/마이그레이션/테스트 시나리오/실행 순서)를 중복 담게 된다. JSON의 역사적 이점(기계 판독)은 LLM이 md도 잘 읽는 현 구조에서 희석되었다.

## 확정된 설계 방향 (대화에서 합의)

### D1. 탑다운 기능 중심 PLAN.md 골격

```
1. 태스크 개요 + 기능 리스트업 (F-ID, AC, 우선순위, 의존 그래프)
2. 기능별 분석 (F-NNN 하위 섹션 반복)
   2.N.1 관련 파일 맵 (FE/BE/DB/환경/배치/공통)
   2.N.2 현재 구현
   2.N.3 영향 범위
3. 기능별 설계 (F-NNN 하위 섹션 반복)
   3.N.1 파일 변경 계획 (6영역 × 신규/수정)
   3.N.2 API·데이터 모델·화면 설계
   3.N.3 환경 변경
   3.N.4 배치/마이그레이션
   3.N.5 테스트 시나리오 (AC↔TS 매핑)
4. 통합 실행 계획 (기능 의존 기반 Phase 그룹핑, 기능-Step 매핑)
5. QA 체크리스트 (기능-QA 매트릭스 포함)
6. 복잡도 판별 + 실행 아키텍처 (기존 유지)
7. 기술 컨텍스트 (기존 유지)
8. 리스크 및 대응 (기능-리스크 연결)
```

### D2. A안 채택 — PLAN.md 단일 SSOT

- `execution-plan.json` **폐기** (생성 Step 제거 + deprecated 고지)
- PLAN.md의 구조화 섹션(features/parts 표준 포맷)을 후속 소비자가 직접 Read·파싱
- 기존에 생성된 json 파일은 하위호환 보존 (재생성 없음)

### D3. 자동 모드 축소 (Flat/Multi)

| 조건 | 모드 | 동작 |
|------|------|------|
| 기능 ≥ 2개 | **Multi-Feature** | F-NNN 하위 섹션 전개 |
| 기능 = 1개 | **Flat** | F 섹션 생략, 평면 구조 |
| ANALYSIS.md에 `features[]` 명시 | Multi 강제 | 상류 결과 존중 |

### D4. 후속 파이프라인 동시 정합화

- `op-dev-execute`: features 루프 기반으로 실행 로직 전환
- `ui-designer` (plan-driven): 입력을 `frontend.screens[]`(json) → PLAN.md 3.N.2 섹션 참조로 전환
- `op-dev-qa`: 기능-QA 매핑 매트릭스 검증 규칙 추가

### D5. 본 태스크 PLAN 시범 적용

본 태스크의 PLAN 단계에서 **새 탑다운 기능 중심 구조를 직접 시범 적용**한다. `op-task-plan` 스킬을 호출하되, 디스패치 프롬프트에 신규 구조 지침을 인라인 주입한다. 본 태스크의 EXECUTE 결과(새 SKILL.md)와 PLAN.md 구조가 **자기정합**이 되도록 PM Gate에서 교차 검증한다.

## 요구사항

- [x] **R1**. `op-dev-plan/SKILL.md`를 탑다운 기능 중심 구조로 재작성
  - **무엇을**: PLAN.md 출력 형식을 D1 골격으로 교체, 프로세스를 기능 식별 → 기능별 분석 → 기능별 설계 → 통합 실행 계획 순으로 재정렬
  - **어디에**: `opal/skills/op-dev-plan/SKILL.md`
  - **왜**: 파일 중심 구조의 기능 추적 부재 해소 (배경 1, 2)
  - **AC**: SKILL.md의 PLAN.md 출력 형식이 §1~§8(또는 동등) 구조이며 §2·§3가 기능(F-NNN) 하위 섹션 반복 구조임이 명시된다. "기능 리스트업", "기능별 분석", "기능별 설계", "기능-QA 매트릭스" 용어가 문서에 등장한다.

- [x] **R2**. `plan-guide.md`를 기능 중심 단계로 재설계
  - **무엇을**: "0단계: 기술 컨텍스트 로딩" 유지, "1단계: 기능 식별" 신설, 나머지 단계를 기능 루프 안으로 재배치
  - **어디에**: `opal/skills/op-dev-plan/references/plan-guide.md`
  - **왜**: R1의 프로세스가 가이드와 정합해야 한다
  - **AC**: 가이드에 "기능 식별" 단계가 신설되어 있고, 파일 변경 계획·구현 순서·핵심 설계·테스트 전략이 기능 루프 안에서 정의된다. 6영역(FE/BE/DB/환경/배치/공통) 분류 축이 명시된다.

- [x] **R3**. `execution-plan.json` 폐기 처리
  - **무엇을**: SKILL.md Step 7(execution-plan.json 생성) + plan-guide.md 6단계 + 스키마 섹션을 제거하거나 "Deprecated — PLAN.md §2·§3로 통합" 고지로 교체
  - **어디에**: `opal/skills/op-dev-plan/SKILL.md`, `opal/skills/op-dev-plan/references/plan-guide.md`
  - **왜**: 중복 산출물 제거 (배경 2, D2)
  - **AC**: 두 파일에 더 이상 "execution-plan.json을 생성하라"는 지시가 없고, 기존에 생성된 json은 하위호환 보존한다는 고지가 존재한다.

- [x] **R4**. PLAN.md 구조 파싱 규칙 명세
  - **무엇을**: 후속 소비자(execute/ui-designer/qa)가 PLAN.md에서 features/parts/test-scenarios를 추출할 때 사용할 섹션 앵커·테이블 컬럼·F-ID 포맷을 명세
  - **어디에**: `opal/skills/op-dev-plan/references/plan-guide.md`에 "PLAN.md 파싱 규칙" 섹션 신설
  - **왜**: JSON을 제거하면 md 구조가 계약이 된다 (D2)
  - **AC**: F-ID 포맷(`F-{NNN}`), 기능 섹션 앵커(`### F-NNN: {이름}`), 파일 맵 테이블 컬럼(영역/경로/역할/변경유형), 테스트 시나리오 테이블 컬럼(TS-ID/AC/유형/기대결과)이 규칙으로 정의된다.

- [x] **R5**. Flat/Multi 모드 자동 축소 규칙 추가
  - **무엇을**: 기능 개수에 따라 Flat/Multi를 자동 선택하는 규칙과 Flat 모드 PLAN.md 형식을 정의
  - **어디에**: `opal/skills/op-dev-plan/SKILL.md` + `plan-guide.md`
  - **왜**: 단일 기능 태스크의 overhead 방지 (D3)
  - **AC**: 판정 조건 테이블(D3)이 SKILL.md 또는 plan-guide.md에 존재하며, Flat 모드에서 F-NNN 섹션을 생략한 평면 구조가 예시로 제시된다.

- [x] **R6**. `op-dev-execute` features 루프 전환
  - **무엇을**: execute 스킬이 `execution-plan.json` 대신 PLAN.md의 §2·§3·§4를 입력으로 받아 기능 루프 기반으로 실행하도록 프로세스 재작성
  - **어디에**: `opal/skills/op-dev-execute/SKILL.md` (+ references가 있으면 references)
  - **왜**: PLAN.md SSOT 전환에 따른 소비자 정합화 (D4)
  - **AC**: SKILL.md에 "PLAN.md §2·§3 입력", "기능 루프 실행", "execution-plan.json 사용 안 함" 지시가 명시된다.

- [x] **R7**. `ui-designer` plan-driven 입력 전환
  - **무엇을**: plan-driven 모드의 입력을 `frontend.screens[]` JSON에서 PLAN.md §3.N.2(FE 화면 설계)로 변경
  - **어디에**: `opal/skills/ui-designer/SKILL.md` (+ references가 있으면 references)
  - **왜**: PLAN.md SSOT 전환에 따른 소비자 정합화 (D4)
  - **AC**: ui-designer가 PLAN.md의 FE 화면 섹션을 직접 Read하는 플로우가 명시되고, `execution-plan.json` 의존 서술이 제거된다.

- [x] **R8**. `op-dev-qa` 기능-QA 매핑 검증 규칙 추가
  - **무엇을**: PLAN PM Gate에서 F-NNN과 §5 QA 체크리스트 항목의 매핑 빈틈 여부를 검증하는 규칙을 추가
  - **어디에**: `opal/skills/op-dev-qa/SKILL.md` (+ references)
  - **왜**: 기능-QA 커버리지 추적 확립 (배경 4, D4)
  - **AC**: QA 스킬에 "모든 F-NNN이 §5 QA 체크리스트에서 최소 1개 항목 커버", "빈틈 발견 시 Fail" 규칙이 명시된다.

## 제약 조건

- **opsdd 파이프라인(op-sdd-*)은 이 태스크 범위 밖이다.** op-sdd-plan은 건드리지 않는다.
- **op-task-plan(opp 파이프라인)도 이 태스크 범위 밖**이다 — 추후 별도 태스크에서 검토.
- 기존에 생성된 `execution-plan.json`(과거 태스크 산출물)은 **수정·삭제하지 않는다**. 하위호환 보존.
- `opal-pilot-dev` / `opal-pilot-dev-short` 오케스트레이터 본체는 R6/R7/R8 인터페이스 맞춤에 필요한 **최소 수정만** 허용. 구조 변경은 금지.
- 하네스(`opal-harness*.md`), PM 프로세스(`opal-pm.md`)는 건드리지 않는다.
- 모든 변경 문서에 변경이력(버전, 일시 KST, 변경내용) 기록. 커밋은 캡틴 지시 시에만 수행.
- 한국어 본문 + 영어 코드·필드명 규칙(`docs/CONVENTIONS.md`) 준수.

## 기술 스택

- 프레임워크 문서(Markdown) 중심
- YAML frontmatter (스킬 정의)
- 대상 스킬: `op-dev-plan`, `op-dev-execute`, `op-dev-qa`, `ui-designer`

## 관련 문서

- `docs/PROJECT.md` — 프로젝트 원칙·문서 허브
- `docs/CONVENTIONS.md` — 네이밍·파일 구조·변경이력 규칙
- `opal/skills/op-dev-plan/SKILL.md` — 개편 대상
- `opal/skills/op-dev-plan/references/plan-guide.md` — 개편 대상
- `opal/skills/op-dev-execute/SKILL.md` — 소비자 정합화 대상
- `opal/skills/op-dev-qa/SKILL.md` — 소비자 정합화 대상
- `opal/skills/ui-designer/SKILL.md` — 소비자 정합화 대상
- `opal/skills/op-sdd-plan/SKILL.md` — 기능 중심 설계 선례(참고용, 수정 금지)
- `.opal/AGENT.md` — PM 검토 기준·금지사항(개발/배포 경계)

## 미확정 사항 (PLAN에서 결정)

- R4의 섹션 앵커 포맷 세부(예: H3 헤딩 안에 F-ID를 어디 배치할지)는 PLAN 단계에서 최종 결정
- R5 Flat 모드의 섹션 번호 부여 규칙(§2·§3 유지 vs 축약)은 PLAN 단계에서 최종 결정
- R6에서 execute 루프가 F-NNN 단위로 병렬 가능한지 여부는 PLAN의 복잡도 판별·병렬 그룹핑 결과에 따름
