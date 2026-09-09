---
name: op-task
description: |
  **사용자 요청을 sdlc-v2 TASK.md로 구조화하는 단계 스킬**. 문제·목표 결과·영향 범위·제약·완료 기준을 짧고 검증 가능하게 고정한다.
  반드시 이 스킬을 사용해야 하는 상황: 개발 오케스트레이터가 TASK 단계를 직접 수행할 때.
  필수 입력: 사용자 요청, task_path. 보장 출력: TASK.md.
---

# op-task — TASK.md 작성

## 실행 계약

- 호출자인 PM이 직접 수행한다. TASK 작성을 위해 워커나 다른 스킬을 호출하지 않는다.
- `pilot_key`, `mode`, 태스크 폴더 채번과 `state init`은 호출자/하네스가 소유한다. op-task는 재추천·재승인하거나 TASK.md에 복제하지 않는다.
- 프로젝트 문서와 런타임 capability 선별도 PM dispatch가 소유한다. op-task는 고정 기술 스택·스킬·MCP 카탈로그를 탐색하지 않는다.
- 상세 필드 규칙과 형식은 `references/task-guide.md`를 Read하여 따른다.

> 산출물의 사실·결정 근거는 호출자가 이미 로드한 `opal/core/references/harness/citation-rules.md`를 따른다.

## 프로세스

### 1. 필수 입력 확정

사용자 발화와 현재 프로젝트 맥락에서 다음 다섯 항목을 추출한다.

- `Problem`
- `Proposed outcome`
- `Affected users and systems`
- `Constraints`
- `Acceptance criteria`

목표·범위·제약·완료 기준을 바꿀 정보가 실제로 없을 때만 사용자에게 직접 질문한다. 구현 방식, 기술 스택, 대안 비교처럼 ANALYSIS/PLAN에서 결정할 내용은 질문하지 않는다. 답을 기다리지 않아도 확정 가능한 항목은 먼저 작성한다.

미확정 사항은 목표·범위·제약·완료 기준을 바꿀 때만 `Open questions`에 남긴다. 해결된 질문과 선택하지 않은 대안은 기록하지 않는다.

### 2. TASK.md 작성

`task_path/TASK.md`를 아래 계약으로 작성한다.

- 파일 첫 YAML frontmatter는 정확히 `template: sdlc-v2`다.
- 필수 다섯 절은 모두 비어 있지 않아야 한다.
- `Constraints`의 모든 항목은 고유 `C-N`, `Acceptance criteria`의 모든 항목은 고유 `AC-N`을 가진다.
- 추가 제약이 없어도 Constraints를 비우지 않고 기존 프로젝트 규칙 유지 조건을 한 항목으로 적는다.
- 교체·전환·마이그레이션 목표는 구형 잔존 0과 신형 채택을 관찰 가능한 Acceptance criteria에 포함한다.
- 단계·승인·gate·pilot·mode 상태는 적지 않는다. `state.json`이 소유한다.
- 기술 스택, 관련 문서 목록, 대안표, 구형 명확화 표를 별도 절로 만들지 않는다.

### 3. 계약 검사

```bash
~/.opal/tools/state-tool/run.sh verify <task-path> --clarification-check
```

`template=sdlc-v2`와 필수 절·AC/C 식별자 검사가 통과해야 완료다. 실패하면 누락된 필드만 고치고 다시 검사한다.

### 4. 반환

```text
TASK 완료: {task_path}/TASK.md
Open questions: {없음 | 질문 목록}
```

호출자는 반환 후 자신의 pipeline에 따라 TASK 행 mark, 사용자 확인, 다음 단계 전이를 수행한다.

## Legacy 호환

`template: sdlc-v2`가 없는 기존 TASK.md는 재개 입력으로만 읽는다. 신규 TASK에 legacy 절을 생성하지 않는다.

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | — | 초기 작성 |
| v1.1 | 2026-04-07 | "대화 내용 반영" 절에 "배경 분석 (대화에서 도출)" 섹션 추가. TASK.md 템플릿 갱신. 체크리스트 항목 분리 (094) |
| v1.2 | 2026-04-09 | 저장 경로 날짜 포함 형식으로 변경(`{NNN}-{YYMMDD}-{스킬약어}-{태스크명}`). `{NNN}` 채번 방식을 `last_task_number` 기반으로 변경. `{YYMMDD}` 항목 추가 (102) |
| v1.3 | 2026-04-17 | "관련 문서" 섹션을 유형+경로/URL 포함 테이블 포맷으로 전환 + citation-rules 참조 지시 추가 (123) |
| v1.4 | 2026-04-24 | citation-rules 트리거 1줄 주입 — SSOT + Trigger 패턴 (130) |
| v1.5 | 2026-05-09 11:22 | 모드 필드 3-way 갱신 + state init choices 갱신 + 기본값 안내 추가 (140) |
| v1.6 | 2026-05-12 11:16 | AC 작성 가이드에 카르파시 §4 원문 인용 + Bad/Good 예시 2번째 행 추가 (001) |
| v1.7 | 2026-05-12 15:03 | AC 작성 가이드의 외부 출처 인용 제거 — Bad/Good 예시(2행)는 유지. SSOT 자립성 회복 (001) |
| v1.8 | 2026-06-07 | QA→PM Gate 통합 정합화 — AC 정의·작성 가이드·작성 체크리스트의 "QA Gate에서 Pass/Fail 판정" → "PM Gate(문서검증)·TEST(동작 검증)에서 Pass/Fail 판정"(별도 QA Gate 단계 없음, 문서검증은 PM Gate가 흡수, 동작 검증은 TEST가 독립 수행) (014 Phase 4-2) |
| v1.9 | 2026-06-16 18:07 | STEP 4 템플릿에 "명확화 결과" 4요소 섹션 추가 — verify --clarification-check 검증 대상 표준화 (005) |
| v2.0 | 2026-06-17 10:24 | `{태스크명}` 규칙 완화 — 영문 kebab-case 외 한글·혼용 허용(공백 금지·하이픈 구분). 앞 3요소 ASCII 고정 명시 + macOS NFD 주의 추가 (026 L2: 한글 폴더명 허용) |
| v2.1 | 2026-06-17 15:50 | `{태스크명}` 기본값을 **한글**로 변경 — 영문·혼용은 소유자 명시 요청 시. 예시 한글 우선 재배치 (026 후속 L2: 한글 기본) |
| v2.2 | 2026-07-23 12:09 | `--next-action` 계약 보강 — advance/mark가 파이프라인 프론티어에서 자동 파생·갱신하며, 전이 시 1회성 오버라이드 가능함을 명시 (072) |
| v2.3 | 2026-07-23 13:18 | AC 작성 가이드에 "교체형 목표(구형→신형 전환·대체·마이그레이션) → 잔존0·채택 검증 기준 의무" 규칙 + Bad/Good 예시 1행 추가 — 루브릭 ①목표달성·⑤채택/잔존 축 채점 가능성 보장 (073) |
| v2.4 | 2026-07-28 | `{NNN}` 채번 서술을 `.opal/MEMORY.md` 헤더 직접 참조에서 `memory-tool task-number --bump` 포인터 참조로 전환 (절차 SSOT: `harness/task-process.md`) (078) |
| v2.5 | 2026-08-13 16:57 | state-tool 행 원천 지시 정정 — `--rows-from` 서술을 오케스트레이터 `references/pipeline.json` SSOT 기준으로 교체(구형 `.md` 파싱 지시 제거). 10/10 pilot 전환에 맞춘 pilot 밖 정합 (090) |
| v2.6 | 2026-08-16 13:30 | `--next-action` 서술의 표 전제 정정 — "`## 다음 액션` 초기값" → "`state.json` `next_action` 필드 초기값(조회: `state-tool show`)"로 치환. STATE.md가 파생 표를 렌더하지 않는 저널로 재정의됨에 따른 정합(094 R-6/R-7, Step 8) |
| v2.7 | 2026-08-21 17:21 | §확정된 설계 방향 항목 접두 태그(`[결정]`/`[사실]`) 의무화 + §명확화 결과 `의존 사실` 열 규약 재정의(열 수 4 불변) + `-` 허용 조건·인용 금지 예외 표기 + 레거시 비소급 + 작성 체크리스트 2항 추가 (098) |
| v2.8 | 2026-09-09 14:17 KST | 신규 TASK 작성 계약을 `template: sdlc-v2`와 5개 필수 절로 단순화하고, 인터뷰를 목표·범위·제약·완료 기준 변경 질문으로 제한하며, AC/C ID를 필수화하고 스킬·모드 상태는 state.json 소유로 정리 (task 111/W-2) |
| v2.9 | 2026-09-09 KST | 기술 스택·오케스트레이터 추천·state 초기화·고정 capability 산문을 제거하고 TASK 필드 확정·작성·계약 검사만 남김 (111) |
