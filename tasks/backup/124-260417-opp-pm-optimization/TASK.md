# TASK: opal-pm.md 다운사이징 — pm/ 폴더 분리 최적화

> 작성일: 2026-04-17 | 작업 유형: 개선 | 적용 스킬: opp | 모드: agentic

## 작업 목표

`opal-pm.md`(560줄)의 Lazy 분리 가능 섹션을 `opal/core/references/pm/` 폴더의 개별 파일로 추출하여 Eager 로드 컨텍스트를 ~220줄로 줄인다.

## 배경

`opal-pm.md`는 부트스트랩 Eager 단계에서 전체 560줄이 무조건 로드된다.
분석 결과, 전체의 약 60%는 특정 트리거 시점에만 필요한 내용으로 Lazy 분리가 가능하다.
캡틴이 `opal/core/references/pm/` 폴더를 생성했고, 이 위치에 추출 파일을 배치한다.

## 배경 분석 (대화에서 도출)

**섹션별 분류:**

| § | 섹션명 | 현재 | 처리 |
|---|--------|------|------|
| §1 | PM 역할 개요 | ~20줄 | Eager 유지 |
| §2 | 컨텍스트 로드 절차 | ~20줄 | Eager 유지 |
| §3 | 디스패치 전 프로세스 (Step 0~7) | ~130줄 | Step 0, 6, 7 → Lazy 분리 |
| §4 | PM 검토 게이트 (11항목) | ~80줄 | Eager 유지 |
| §5 | 학습 루프 + 자기 개선 | ~110줄 | 핵심만 Eager, 세부 → Lazy |
| §6 | 에이전트 컨텍스트 주입 원칙 | ~70줄 | 3줄 요약만 Eager, 전체 → Lazy |
| §7 | 문서/코드 불일치 판단 | ~30줄 | Eager 유지 |
| §8 | 워커 행동 규칙 | ~15줄 | §7에 병합 (제거) |
| §9 | code-scan.json PM 관리 | ~40줄 | Lazy 분리 |
| §10 | 통합 조율 | ~30줄 | Lazy 분리 |
| §11 | 전문 에이전트 관리 | ~110줄 | Lazy 분리 (최대 절감) |
| 변경이력 | - | ~15줄 | 삭제 (각 파일별 관리) |

## 확정된 설계 방향 (대화에서 합의)

1. **추출 대상 파일** (`opal/core/references/pm/` 폴더에 배치):
   - `specialist-agent.md` — §11 전문 에이전트 관리 (110줄)
   - `orchestration.md` — §10 통합 조율 (30줄)
   - `code-scan-management.md` — §9 code-scan.json PM 관리 (40줄)
   - `self-improvement.md` — §5 자기 개선 세부 프로세스 (핵심 트리거 테이블 제외)
   - `context-injection.md` — §6 에이전트 컨텍스트 주입 원칙 전체 (감지 조건 테이블 포함)

2. **opal-pm.md 슬림화**:
   - §5: 트리거 테이블 + "→ `pm/self-improvement.md` 참조" stub으로 축소
   - §6: 3줄 원칙 + "→ `pm/context-injection.md` 참조" stub으로 축소
   - §8: §7 마지막에 1줄로 병합 후 §8 삭제
   - §9, §10, §11: 각각 stub 3줄로 대체
   - 변경이력: 삭제

3. **트리거 정의** (각 파일에 Lazy 로드 트리거 명시):
   - `specialist-agent.md`: 전문 에이전트 디스패치 직전
   - `orchestration.md`: 다중 에이전트 배치 구성 시
   - `code-scan-management.md`: code-scan.json 갱신 필요 시
   - `self-improvement.md`: 태스크 완료 또는 소유자 피드백 수신 시
   - `context-injection.md`: 디스패치 전 컨텍스트 주입 상세 판단 필요 시

## 요구사항

- [x] `pm/specialist-agent.md` 생성 — §11 전체 내용 이관, Lazy 트리거 명시
  - **AC**: 파일이 존재하고, §11 기존 내용(개념/구조/생성시점/갱신트리거/탐색경로/분배규칙)이 모두 포함됨
- [x] `pm/orchestration.md` 생성 — §10 전체 내용 이관, Lazy 트리거 명시
  - **AC**: 파일이 존재하고, §10 기존 내용(인터페이스 계약/Batch 핸드오프/충돌 해소) 포함됨
- [x] `pm/code-scan-management.md` 생성 — §9 전체 내용 이관, Lazy 트리거 명시
  - **AC**: 파일이 존재하고, §9 기존 내용(생성시점/갱신트리거/PM Gate 절차/최소 구조 JSON) 포함됨
- [x] `pm/self-improvement.md` 생성 — §5 자기 개선 세부 내용 이관
  - **AC**: 파일이 존재하고, §5.2의 개선 대상 테이블/프로세스 5단계/제한 규칙이 포함됨
- [x] `pm/context-injection.md` 생성 — §6 전체 내용 이관
  - **AC**: 파일이 존재하고, §6 기존 내용(최소 보장/트리거 선별/PM 판단/기술 스택 연동) 포함됨
- [x] `opal-pm.md` 슬림화 — 총 ~220줄 이하로 축소
  - **AC**: §5는 트리거 테이블 + stub으로 축소, §6은 3줄 원칙 + stub, §8 삭제(§7 마지막에 1줄 병합), §9~§11은 각 stub 3~5줄, 변경이력 삭제
- [x] `opal-pm.md` 내 stub이 올바른 탐색 경로를 명시함
  - **AC**: 각 stub이 `opal/core/references/pm/{파일명}` 경로와 Lazy 트리거 조건을 명시함

## 제약 조건

- 기존 내용 손실 없이 이관 (삭제가 아닌 추출)
- `opal-pm.md`의 §1~§4, §7은 건드리지 않음
- 각 추출 파일에 YAML frontmatter 없음 (참조 문서 형식)
- 추출 파일에 변경이력 불필요
- **배포 금지**: `~/.opal/references/` 직접 수정 금지. 소스(`opal/core/references/`) 수정만 허용

## 기술 스택

- Markdown 파일 편집

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | opal-pm.md | `opal/core/references/opal-pm.md` | 슬림화 대상 |
| D-2 | 소스 | pm/ 폴더 | `opal/core/references/pm/` | 추출 파일 배치 위치 |
