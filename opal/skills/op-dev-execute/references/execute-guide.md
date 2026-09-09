# EXECUTE 단계 상세 가이드

> 실행 컨텍스트: 이 가이드는 EXECUTE 워커가 읽고 따른다. 서브 에이전트 사용이 불가능하거나 사용자가 직접 수행을 원하면 오케스트레이터가 같은 절차를 직접 따른다.

## 절대 금지

| # | 금지 행동 | 이유 |
|---|---|---|
| 1 | PLAN.md에 없는 파일 생성·수정 | 계획 밖 변경은 추적과 복구가 어렵다. |
| 2 | PLAN 설계를 임의 변경 | PM Gate를 통과한 설계 계약이 무효화된다. |
| 3 | 다른 영역 침범 금지 / 다른 W의 파일 소유권 침범 | 병렬 실행 충돌이 난다. |
| 4 | PLAN에 없는 패키지 설치 | 의존성 변경은 사전 설계와 승인 대상이다. |
| 5 | 시크릿 하드코딩 | 보안 위반이다. |
| 6 | RED 테스트 파일 수정 | reward hacking 방지. 테스트 수정 필요 시 블로커로 보고한다. |
| 7 | `git commit`, `git push`, `git reset`, `git rebase` | 커밋·머지는 소유자 권한이다. |

## 입력 우선순위

1. sdlc-v2 `PLAN.md`의 `## Work items`
2. legacy `PLAN.md §4.2` 실행 체크리스트
3. legacy `PLAN.md §3` 실행 체크리스트
4. legacy `execution-plan.json`

## sdlc-v2 실행 절차

### 1. 진입 계약 검사

실행 전 아래 검사를 호출한다.

```bash
~/.opal/tools/state-tool/run.sh verify <task-folder> --plan-contract-check
~/.opal/tools/state-tool/run.sh verify <task-folder> --code-scan-citation-check
```

`--plan-contract-check` 실패는 블로커다. `--code-scan-citation-check`는 code-scan 적용 코드 파일이 없으면 skip 가능하다.

### 2. Work items 읽기

각 W는 아래 필드를 실행 계약으로 사용한다.

| 필드 | 사용 방식 |
|---|---|
| 작업 | W-ID와 제목 |
| 담당 | 디스패치 대상 확인 |
| 변경 대상 | 수정 허용 파일 |
| 구체적 변경 | 구현 지시 |
| 선행 작업 | 순서 제약 |
| 실행 그룹 | 병렬 가능 배치 |
| 완료 기준 연결 | 담당 AC/C와 시나리오 연결 |

오케스트레이터가 특정 W만 지정했으면 그 W만 처리한다. 지정되지 않았으면 실행 그룹 오름차순으로 처리한다.

### 3. 구현

- `변경 대상`에 있는 파일만 수정한다.
- 실제 코드 구조가 PLAN과 다르면 임의 해석하지 말고 블로커로 보고한다.
- 문서 W가 배정되면 코드 W와 같은 절차로 수행한다. 구현으로 내용이 달라지는 기획·설계·운영 문서만 수정하고, 참조만 한 문서는 수정하지 않는다.
- code-scan 대상 확장자 파일을 수정하면 `~/.opal/references/header-standard.md`에 맞춰 @header를 갱신한다.

### 4. 자가 점검

각 W 완료 직후 변경 범위에 맞는 검증을 실행한다.

- `test-tool resolve`
- BE 변경: `test-tool unit --scope be`
- FE 변경: `test-tool unit --scope fe`
- sdlc-v2 scenario coverage: `test-tool scenario-coverage-build --task-folder <task-folder> --template sdlc-v2` 후 `test-tool scenario-coverage-check --coverage-input <task-folder>/.scenario-coverage-input.json`
- 담당 AC/C/H에 연결된 L1/L2 시나리오가 있으면 공개 인터페이스로 직접 실행한다.

실패하면 최대 3회 수정·재실행한다. 환경, 외부 서비스, 권한 문제로 검증할 수 없으면 통과 처리하지 않고 블로커로 보고한다.

### 5. 상태 기록

sdlc-v2는 PLAN.md에 체크박스를 갱신하지 않는다. 진행 상태는 state.json이 소유한다.

```bash
~/.opal/tools/state-tool/run.sh mark <task-folder> --task-step execute.implement --done --as-worker --worker-stage EXECUTE --action-step <N/M>
```

시나리오 결과와 증거는 TEST 단계 또는 `test-scenario.json`이 소유한다. TEST-SCENARIO.md 본문에 PASS/FAIL을 복제하지 않는다.

## 블로커 처리

블로커가 발생하면 즉시 중단하고 아래 정보를 오케스트레이터에 반환한다.

- 작업 ID: sdlc-v2는 `W-N`, legacy는 Step 번호
- 상황: 실제 오류, 누락 입력, 외부 서비스·권한 문제
- 원인: 확인된 사실만 적고 추정은 구분한다.
- 필요한 결정: PLAN 수정, 파일 소유권 재배정, 환경 조치, 사용자 결정 중 무엇인지 명시한다.

블로커 상태에서 PLAN 범위 밖 파일을 수정하거나 TEST-SCENARIO.md에 PASS/FAIL을 임의 기록하지 않는다.

## Legacy 폴백

legacy PLAN은 기존 `§4.2`/`§3` Step과 `execution-plan.json`을 읽어 기존 절차대로 처리한다. legacy 체크박스가 있으면 완료 시 갱신할 수 있다. 신규 sdlc-v2 PLAN에는 체크박스와 QA 결과를 만들지 않는다.

CLOSE 단계의 최종 보고·히스토리·정리 계약은 그대로 유지한다. EXECUTE의 문서 W는 구현으로 즉시 내용이 달라지는 문서 최신화만 수행한다.

## 보안 가드레일

아래 패턴을 감지하면 즉시 중단하고 블로커로 보고한다.

| 패턴 | 감지 방법 | 조치 |
|---|---|---|
| 하드코딩 시크릿 | `password=`, `secret=`, `api_key=`, `token=` 리터럴 값 | 환경변수 또는 설정 주입으로 교체 제안 |
| SQL Injection | 문자열 결합 SQL | 파라미터 바인딩 사용 |
| 민감 파일 생성 | `.env`, `credentials.*`, `*.pem` | `.gitignore` 포함 여부 확인 |
| 무제한 입력 | 사용자 입력을 검증 없이 DB/파일시스템에 전달 | 입력 검증 추가 |

## 결과 반환

```json
{
  "artifact_path": "tasks/{NNN}-{태스크명}/",
  "summary": "실행 요약",
  "status": "complete | blocked",
  "blockers": [],
  "changed_files": ["파일1", "파일2"],
  "work_items": ["W-1"],
  "verification": ["실행한 명령과 결과"]
}
```

## 변경이력

| 버전 | 일시 | 변경내용 |
|---|---|---|
| v1.0 | - | 초기 작성 |
| v1.2 | 2026-04-23 11:39 | specialist/generalist 가이드 분리 (129) |
| v3.0 | 2026-09-09 14:18 KST | sdlc-v2 Work items 우선 실행, plan-contract/code-scan 진입 검사, state.json/test-scenario.json 상태·증거 소유권, legacy 폴백 규칙을 정리 (task 111/W-4) |
| v3.1 | 2026-09-09 14:18 KST | execute-specialist-guide.md와 execute-generalist-guide.md의 기존 참조가 유효하도록 `절대 금지`, `블로커 처리`, `다른 영역 침범 금지` 앵커를 복원하고 반환 형식에 work_items를 추가 (task 111/W-4) |
| v3.2 | 2026-09-09 14:18 KST | 문서 W도 EXECUTE 범위에서 수행하고 구현으로 내용이 달라지는 문서만 수정하며 참조 전용 문서는 제외하도록 docs 계약 추가. legacy와 CLOSE 최신화 계약 유지 명시 (task 111/W-4) |
