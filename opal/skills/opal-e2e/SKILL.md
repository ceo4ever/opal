---
name: opal-e2e
description: |
  프로젝트 E2E 여정과 조각을 설정·작성·실행·조회하는 operator. 반드시 이 스킬을 사용하는 상황: "opal-e2e", "e2e 여정", "//e2e". 모드: setup | author | run | status.
alias: e2e
triggers:
  - "^e2e$"
  - "^opal-e2e$"
  - "(?i)(e2e\\s*여정|여정\\s*(작성|실행|조회))"
version: "1.1"
domain: quality
pipeline: "MODE: setup | author | run | status"
---

# opal-e2e

프로젝트 E2E 여정·조각의 operator다. 단계 파이프라인과 워커 디스패치는 만들지 않는다.
실행·판정·승격 자격은 `test-tool`이 소유하며 이 스킬은 명령을 호출하고 구조화 결과를
해석만 한다.

## 모드 라우팅

| 호출 | 동작 |
|---|---|
| `//e2e setup` | 프로젝트 E2E 환경 설정(`.opal/e2e/environment.json`)을 검토·확정한다 |
| `//e2e author [journey|fragment]` | 여정 또는 조각 초안을 대화로 작성한다 |
| `//e2e run <journey-id>` | `test-tool e2e run`을 호출한다 |
| `//e2e status [run-id]` | 최근 run과 신선도 원장을 읽기 전용으로 조회한다 |
| 모드 미지정 | 네 모드 중 하나를 사용자에게 확인한다 |

`import` 모드는 제공하지 않는다. 작성 계약과 예시는
[`references/authoring.md`](references/authoring.md)를 따른다. 환경 설정 인터뷰 항목과
확인 체크리스트는 [`references/setup.md`](references/setup.md)를 따른다.

## setup

준비되지 않은 환경에서 `author`·`run`을 시작하면 먼저 이 모드를 안내한다.

1. `~/.opal/tools/test-tool/run.sh e2e env-inspect --project-root <project-root>`로 표면
   후보·driver 설치·비밀 이름을 읽기 전용으로 검토한다.
2. ①-1 폴백: env-inspect 후보가 없거나 부족한 표면에 한해, `docs/PROJECT.md`가 있으면
   그 "프로젝트 구성" 절과 관련 설계 문서에서 기동 방법·표면을 추정하고 결과에 "추정"과
   근거 위치(파일·절)를 표시한다. `docs/PROJECT.md`가 없으면 이 폴백을 건너뛴다. 이 추정은
   `env-inspect`가 아니라 스킬 층의 해석이며, `env-inspect` 자체는 파일 구조만 보는 결정론
   도구로 그대로 둔다.
3. 탐지·추정으로 확정하지 못한 항목과 ①-1의 모든 추정값을 사용자 인터뷰로 확정한다(대상
   표면, 로컬 기동 또는 기존 URL, 계정·비밀 환경 변수 이름, 데이터 준비·복원, 외부 연동
   정책). 확인 전 추정값은 설정 파일에 쓰지 않는다.
4. 확정한 내용으로 초안을 태스크 작업이면 `<task-path>/e2e/`, 일회성이면
   `<project>/.e2e/scratch/`에 두고 `~/.opal/tools/test-tool/run.sh e2e env-validate --file <초안 경로> --project-root <project-root>`로 검증한 뒤 사용자 확인 게이트를 연다.
5. 사용자 확인 뒤에만 초안을 `.opal/e2e/environment.json`에 기록한다.
6. `~/.opal/tools/test-tool/run.sh e2e env-check --project-root <project-root>`를 실행하고
   `ready`/`not_ready`와 `cause`·`remediation`을 그대로 보고한다. 결과값을 스킬이 임의로
   바꾸거나 실패를 성공으로 바꾸지 않는다.

## author

`author`는 준비된 환경을 전제로 한다. 준비되지 않았으면 먼저 `setup`을 안내한다.

1. 태스크 작업이면 `<task-path>/e2e/`, 일회성이면 `<project>/.e2e/scratch/`에 초안을 둔다.
   `docs/e2e/`에 바로 작성하지 않는다.
2. 여정의 목표·표면·step·단언 또는 조각의 params·step·postconditions를 사용자와 확정한다.
   `fill`·`type` 값은 원문이 아니라 `value_ref`로만 받는다.
3. 끝에 사용자 확인 게이트를 열어 작성된 단언과 사후 조건을 확인받는다.
4. 승격하려면 먼저 `run`으로 같은 journey id를 실행한 뒤 아래 게이트를 호출한다.

```bash
~/.opal/tools/test-tool/run.sh e2e promote-check \
  --journey <journey-id> --run-id <run-id> [--artifact-root <path>]
```

`eligible=true`일 때만 초안을 `docs/e2e/journeys/` 또는 `docs/e2e/fragments/`로 옮길
자격이 있다. `eligible=false`, 명령 실패, 사람의 산문 합격 선언은 승격 근거가 아니다.
도구는 자격만 판정하고 복사하지 않으므로 실제 이동 전 대상과 조각화 여부를 사용자에게
확인한다.

## run

```bash
~/.opal/tools/test-tool/run.sh e2e run \
  --scenario <journey-id> --task-path <task-path> \
  --target <source-main|source-worktree|installed> [추가 옵션]
```

stdout JSON과 실제 process exit을 그대로 보고한다. 스킬이 `pass`를 재계산하거나
exit을 덮어쓰지 않는다. 결과의 `run_id`와 `run_json_path`를 다음 승격 게이트 입력으로 쓴다.

## status

지정 run은 다음 명령으로 조회한다.

```bash
~/.opal/tools/test-tool/run.sh e2e status --run-id <run-id> [--artifact-root <path>]
```

run id가 없으면 `<project>/.e2e/freshness.json`과 `.e2e/artifacts/`의 최근 항목을 읽기
전용으로 요약한다. 원장의 `evidence_reuse`는 새 pass가 아니라 이전 pass 증적 재인용으로
표시한다. 파일·state·판정은 변경하지 않는다.

## 판정 소유 경계

- E2E 최종 status와 exit은 `test-tool` 계약만 소유한다.
- 환경 준비 판정(`ready`/`not_ready`, `cause`, `remediation`)은 `e2e env-check`만 소유한다. `setup` 절은 이 결과를 그대로 보고하며 자체 판정을 만들지 않는다.
- `docs/e2e/` 승격 자격은 `e2e promote-check`의 `eligible`만 소유한다.
- 스킬은 실패를 성공으로 바꾸거나 불완전 증적을 보완했다고 간주하지 않는다.
- 외부 서비스 쓰기나 실제 배포가 필요하면 수행하지 않고 사용자에게 에스컬레이션한다.
