# TASK 공통 프로세스

> 출처: opal/core/references/opal-harness.md §4
> 로드 시점: TASK 단계 진입 시 / 태스크 채번 시 / 저장 경로 판단 시
> 역할: 스킬 영역 프로세스 / 태스크 채번 규칙 / 공통 영역 후처리 / 저장 경로 규칙

---

오케스트레이터가 **직접 수행**한다 (워커 디스패치 없음).

#### 스킬 영역 (op-task 프로세스)

1. `op-task/SKILL.md`를 Read한다.
   - 탐색: `{프로젝트}/.opal/skills/op-task/SKILL.md` -> `~/.opal/skills/op-task/SKILL.md`
2. 스킬 프로세스를 따라 TASK.md를 작성한다.

#### 태스크 번호 채번 규칙

신규 태스크 생성 시:
1. `.opal/MEMORY.md` 헤더의 `last_task_number` 필드를 읽는다
2. `last_task_number + 1`을 계산한다
3. **즉시 `.opal/MEMORY.md`의 `last_task_number`를 갱신한다** — 폴더 생성 전에 수행하여 동시 실행 인스턴스 간 번호 중복을 방지한다
4. 태스크 폴더를 생성한다 (`tasks/{NNN}-{YYMMDD}-{스킬약어}-{태스크명}/`)
   - `{YYMMDD}`: `node ~/.opal/tools/date/date.js yymmdd` 실행하여 KST 기준 취득
5. TASK.md를 작성한다

#### 오케스트레이터 공통 영역 (스킬 완료 후 후처리)

3. **STEP 5(오케스트레이터 선택)에서 결정된 스킬약어**를 폴더명과 TASK.md 헤더 `적용 스킬` 필드에 반영한다.
4. **`--agentic` 플래그 여부를 TASK.md 헤더 `모드` 필드에 반드시 기록한다** (`interactive` 또는 `agentic`).
5. **[필수] STATE.md를 생성한다** (§3 템플릿 참조). 이 단계를 건너뛰면 세션 복원과 상태 추적이 불가능하다.
6. 사용자에게 보고하고 다음 단계 승인을 받는다.

#### 저장 경로 규칙

| 조건 | 저장 경로 |
|------|----------|
| `base_path` 지정 시 (오케스트레이터가 명시 주입) | `{base_path}/` (폴더 구조는 오케스트레이터 정의를 따름) |
| `base_path` 없음 (기본) | `tasks/{NNN}-{YYMMDD}-{스킬약어}-{태스크명}/` |

> **`base_path` 용도**: opsdd와 같이 단일 루트 폴더에 모든 산출물을 통합하는 오케스트레이터에서 활용한다. 기존 opp/opds/opd 등 `base_path`를 주입하지 않는 오케스트레이터는 기본 경로(`tasks/`)를 그대로 사용하므로 동작에 영향 없다.

```
📋 [TASK] 완료 보고
📎 산출물: tasks/{NNN}-{YYMMDD}-{스킬약어}-{태스크명}/TASK.md
적용 스킬: {약어}
다음 단계({다음 단계명})로 넘어갈까요?
```

> 도메인별 추가 확인 필드(문서 유형, 출력 모드 등)는 각 opal-pilot SKILL.md에서 정의.

---

## 변경이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-04-21 | 다운사이징 — opal-harness.md §4 분리 (128) |
