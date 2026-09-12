# PM 디스패치 전 프로세스

> Lazy 트리거: 워커 디스패치 직전

PM은 워커마다 아래 순서를 다시 수행한다. 과거 디스패치의 문서·capability 목록을 재사용하지 않는다.

## Step 0. worker.dispatch 이벤트 게이트

**[MUST]** 매 워커 디스패치 직전에 다음을 새로 수행한다.

1. manifest가 선언한 predecessor `pilot.start`의 receipt를 `state-tool event-verify`로 재검증한다.
   현재 receipt가 없으면 `pilot.start` load·전문 적용·검증을 먼저 수행한다.
2. `~/.opal/tools/event-loader/run.sh load --event worker.dispatch > <worker-receipt-path>`를 호출한다.
3. 응답의 `documents[].content` 전문을 적용한다. 이 문서도 같은 응답에 포함되므로 직접 다시
   Read하거나 `worker.dispatch`를 재귀 load하지 않는다.
4. `~/.opal/tools/event-loader/run.sh verify --event worker.dispatch --receipt <worker-receipt-path>`를
   호출한다.
5. predecessor 미충족, load 실패, 필수 문서 누락, stale receipt, wrong-event receipt면 아래 Steps 1~7과 Agent
   호출을 시작하지 않고 blocker로 반환한다.

manifest의 `worker.dispatch` 문서 집합이 유일한 SSOT다. 이 문서에는 구성 파일 목록을 복제하지 않는다.

## Step 1. 실행 단위 확정

- sdlc-v2: 현재 PLAN Work item의 담당, 변경 대상, 선행 작업, 실행 그룹, 완료 기준 연결
- legacy: 현재 PLAN 실행 Step과 관련 기능·가설
- 단계 산출물 작업: 호출 스킬의 입력·출력 계약

같은 실행 그룹이어도 변경 대상이 겹치거나 선행 관계가 있으면 순차 실행한다. 같은 파일을 여러
워커에게 나누지 않는다. 실행 단위가 커서 분할해야 하면 변경 대상이 겹치지 않는 묶음으로 나누고,
같은 파일의 연속 수정은 한 워커가 맡는다.

## Step 2. 프로젝트 지식과 코드맵 선조회

프로젝트에 존재하는 자산만 다음 순서로 조회한다.

1. `.opal/brain/`이 있으면 작업 키워드로 검색하고 관련 페이지만 선별한다.
2. 기존 코드맵이 있으면 변경 후보의 구조·의존·소비자를 조회한다.

둘 다 없으면 건너뛴다. 디스패치를 위해 새 brain이나 코드맵을 만들지 않는다. 조회 결과는 파일
전문이 아니라 이번 실행 단위에 필요한 사실·근거 경로만 주입한다. brain은 과거 결정의 이유,
코드맵은 현재 구조의 근거로 사용하며 어느 한쪽으로 다른 쪽을 대체하지 않는다.

## Step 3. PROJECT 레지스트리와 관련 문서

`docs/PROJECT.md`가 있으면 읽고 문서 레지스트리와 프로젝트 구성에서 이번 실행 단위에 필요한
기획·설계·개발·운영 문서를 선별한다.

선별 우선순위:

1. TASK, ANALYSIS, PLAN, 사용자 지시가 직접 가리킨 문서
2. 레지스트리의 용도·참조 시점이 현재 단계와 맞는 문서
3. 변경 경로가 프로젝트 구성의 경로와 맞는 도메인 문서
4. 레지스트리가 폴더나 패턴을 제시하면 키워드가 직접 맞는 문서
5. 선별 문서가 필수로 참조하는 종속 문서

폴더 전체와 backup 문서를 전량 읽지 않는다. PROJECT가 없을 때만 TASK가 지목한 문서,
`.opal/AGENT.md`, 존재하는 공통 컨벤션·아키텍처 문서를 최소 폴백으로 사용한다.

강제 규칙은 `[MUST] <문서경로> §N: <원문>`으로 주입하고, 나머지는 작업에 미치는 영향만 요약한다.
문서와 코드가 충돌하면 어느 쪽이 낡았는지 임의로 정하지 말고 충돌 근거를 PM에게 반환하게 한다.

## Step 4. 에이전트와 모델 선택

PROJECT 프로젝트 구성과 `.opal/AGENT.md`의 전문 에이전트 매핑을 우선하고, 없으면
`agents.md`를 사용한다. 매핑이 없으면 `opal-task-agent`를 사용한다.

모델은 effective setting의 해당 플랫폼·레벨 값을 사용한다. PLAN에는 실제 실행 가능한 담당 역할을
기입하며, 존재하지 않는 에이전트 이름을 만들지 않는다.

## Step 5. 컨텍스트 슬라이싱

`pm/context-injection.md`의 단계별 계약에 따라 다음만 추린다.

- 현재 실행 단위
- Step 2의 관련 지식·코드맵 근거
- Step 3의 관련 문서와 강제 제약
- 현재 단위와 연결된 이전 산출물 구간
- 선행 배치 결과 중 현재 단위가 소비하는 계약

전체 TASK/PLAN/문서 전문을 관성적으로 복제하지 않는다.

## Step 6. 실행 capability 주입

현재 런타임에서 실제 호출 가능하고 이번 실행 단위에 필요한 항목만 확인해 주입한다.

```markdown
## 실행 capability
- {이름} — {이번 실행 단위에서의 용도}
```

추가 capability가 필요 없으면 `기본 제공 도구만 사용`이라고 적는다. 저장소 문서의 고정 목록,
과거 세션의 목록, 모델이 알고 있을 것이라는 추정은 사용하지 않는다. 구조적 workflow 호출은
그 호출을 소유한 스킬·하네스가 지시하며 capability 추천 목록으로 복제하지 않는다.

## Step 7. 디스패치

Step 0에서 현재 디스패치용 `worker.dispatch` receipt가 성공 검증된 경우에만 Agent 도구를
호출한다. 다른 워커 또는 이전 시점의 receipt는 재사용하지 않는다.

워커 프롬프트는 아래 계약만 가진다.

### 워커 컨텍스트 주입 템플릿

```markdown
[WORKER]

## 이벤트 검증
- event: `worker.dispatch`
- receipt: {현재 디스패치용 receipt 절대경로}
- verification: {`event-loader verify --event worker.dispatch`의 `ok: true` 결과}
- loaded_documents: {현재 load 응답의 `documents[].content` 전문}

## 작업
- 단계·실행 단위: {W/Step/산출물}
- 태스크 폴더: {절대경로}
- 변경 범위: {소유 파일·인터페이스}
- 완료 기준: {연결 AC/C/S 또는 산출물 계약}

## 선조회 근거
- 프로젝트 지식: {없음 | 사실·경로}
- 코드맵: {없음 | 구조·의존 근거}

## 참조 문서와 제약
- {선별 문서 경로와 필요한 구간}
- {강제 규칙 원문 또는 영향 요약}

## 실행 capability
- {현재 사용 가능한 관련 capability | 기본 제공 도구만 사용}

## 반환
- status, changed_files, validation, blockers
```

worktree 태스크는 문서 루트와 코드 루트를 각각 절대경로로 추가한다. 이때 문서 루트는
`worktree-tool`이 발급한 canonical `task_path`(워크트리 안)를 그대로 주입하며, PM은 cwd나
`.opal-worktrees` 문자열로 추측해 구성하지 않는다 — 해석 규칙 원문은
`opal/core/references/harness/worktree.md` §canonical path 발급 계약이 소유한다.
워커는 배정 범위 밖 파일과 git history를 변경하지 않는다. 디스패치 직전 사용자에게 다음 한 줄을 알린다.

```text
⚙️ 워커 디스패치: {단계} — {역할}
```
