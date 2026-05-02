# 추가작업 프로세스

> 출처: opal-harness.md §3
> 로드 시점: 태스크 완료 후 추가 수정 필요 시
> 역할: 추가작업 프로세스 + ADD_DONE.md 템플릿

---

### ADD_DONE.md 템플릿

추가작업 완료 시 작성한다. DONE.md와는 별도 문서이며, DONE.md는 원본 완료 기록으로 보존하고 수정하지 않는다.

파일명 규칙: `ADD_DONE-{N}.md` (순번, 예: `ADD_DONE-1.md`)

| 필드 | 설명 |
|------|------|
| 추가작업 번호 | `ADD-{N}` (순번, 예: `ADD-1`) |
| 일시 | 작업 시작/완료 일시 (KST) |
| 사유 | 추가작업이 필요한 이유 |
| 변경 내용 | 수행한 변경 사항 |
| 변경 파일 | 수정/생성/삭제된 파일 목록 |
| 검증 결과 | QA 검증 통과 여부 |

---

### 추가작업 프로세스

> **CLOSE 재진입 원칙**: 추가작업은 CLOSE 단계를 재진입하여 수행한다. ADD_DONE.md 생성 → State Gate는 CLOSE 단계의 마감 블록과 동일한 패턴을 따른다.

태스크가 `완료` 상태인 후에 추가 수정이 필요할 때 진입하는 프로세스다.

#### 감지 조건

PM이 다음 조건을 자동 인식하면 추가작업 프로세스 진입을 제안한다:

1. 완료된 태스크의 산출물 파일을 수정해야 할 때
2. 완료된 태스크와 같은 도메인의 코드/문서를 수정해야 할 때
3. 소유자이 완료된 태스크를 언급하며 수정을 요청할 때

위 조건 외에도 소유자이 "추가작업" 등으로 명시 요청하면 즉시 진입한다.

#### 진입 절차

1. STATE.md 상태를 `완료` → `추가작업중`으로 갱신
   - `add-row` 실행 시 current_status가 `done`이면 자동으로 `additional_work`로 전환 (PLAN §2.11 G-7)
   - 명시 호출 옵션: `~/.opal/tools/state-tool/run.sh status tasks/{NNN}-.../ --set additional_work`
2. 추가작업 행 삽입:
   ```
   ~/.opal/tools/state-tool/run.sh add-row tasks/{NNN}-.../ --after <마지막행N> --stage CLOSE --item "추가작업 항목명"
   ```
   - 응답: `{"ok": true, "command": "add-row", "row_id": N+1, "current_status": "additional_work"}`
   - 근거: TASK F-11 / PLAN §2.11 G-7
3. CLOSE 단계 재진입: ADD_DONE.md 작성 (DONE.md는 원본 완료 기록으로 보존, 수정 금지)
4. 스킬별 검증 수행 (아래 테이블 참조)
5. State Gate (추가작업 행 ✅ 처리):
   ```
   ~/.opal/tools/state-tool/run.sh mark tasks/{NNN}-.../ --row <N+1> --done
   ```
6. 사용자 확인
7. STATE.md 상태를 `추가작업중` → `추가작업완료`로 갱신:
   ```
   ~/.opal/tools/state-tool/run.sh status tasks/{NNN}-.../ --set additional_work_done
   ```
   - 근거: PLAN §2.11 G-7 (`additional_work → additional_work_done` 전환은 명시 호출만)

#### 스킬별 검증 오버라이드

각 오케스트레이터 SKILL.md에서 추가 오버라이드 가능하며, 명시 없으면 이 테이블을 따른다.

| 스킬 | 추가작업 검증 | 비고 |
|------|-------------|------|
| opp | QA Gate (QA 에이전트) | 문서 변경 검증 |
| opds | lint + build + 관련 테스트 | 간략 검증 |
| opd | 전체 테스트 스위트 + QA Gate | 풀 검증 |
| opwt | QA Gate (QA 에이전트) | 기획 문서 검증 |
| opsdd | QA Gate (QA 에이전트) | 설계 문서 검증 |

> **각 오케스트레이터 SKILL.md 참조 가이드**: 태스크 완료 후 추가작업이 필요하면 이 섹션(§3 추가작업 프로세스)을 따른다.

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-04-05 | 최초 작성 — opal-harness.md §3에서 분리 (087) |
| v1.1 | 2026-04-15 | CLOSE 재진입 원칙 추가 + 진입 절차 State Gate/사용자 확인 포함 (121) |
| v1.2 | 2026-05-01 | 진입 절차 1~7번에 state-tool 호출 명세 추가 — `add-row` / `mark` / `status --set additional_work_done` (§2.11 G-7) + 자동 전환 명시 (134) |
