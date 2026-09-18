# opal-pilot-dev-short

> **[DEPRECATED]** 이 스킬 폴더는 하위호환을 위해 남아 있습니다. `opds`의 실제 실행은 `opal-pilot-dev`가 소유하며, 사용법은 [opal-pilot-dev](../opal-pilot-dev/README.md)를 참조하세요.

`opds` 요청을 처리하기 위한 스킬 폴더이지만, 실제 `opds` 실행은 `opal-pilot-dev`가 소유한다.

## 개요

- `opds`의 Short profile(TASK → PLAN → EXECUTE → TEST → CLOSE)은 canonical하게 `opal-pilot-dev` 스킬 안에서 수행된다.
- 이 스킬(`opal-pilot-dev-short`)은 별도의 물리적 오케스트레이터가 아니며, `opds` 요청이 들어오면 `opal-pilot-dev`로 라우팅하도록 정의돼 있다.
- PLAN 결과에서 작업 규모가 크다고 판단되면 Full Task(`opal-pilot-dev`)로의 에스컬레이션을 제안하는 규칙도 함께 정의돼 있다.

## 언제 쓰나

이 스킬을 직접 선택할 필요는 없다. `opds`로 코드 개발 작업을 요청하면 자동으로 `opal-pilot-dev`가 Short profile로 수행한다.

| 상황 | 사용할 스킬 |
|---|---|
| 코드 개발 작업(범위가 명확함) | `opal-pilot-dev`(`opds`로 호출) |
| 코드 개발 작업(결정 사항이 남음) | `opal-pilot-dev`(`opd`로 호출) |
| 코드를 읽기만 하는 설명, API 명세서, 기획 문서, PR 리뷰, git 작업, 단순 설정 변경 | 해당 없음 (다른 스킬 사용) |

## 사용법

```
//opds {작업 요청}
```

호출하면 `opal-pilot-dev`의 Short profile 절차(TASK → PLAN → EXECUTE → TEST → CLOSE)를 그대로 따른다. 모드 플래그(`--interactive`/`--semi-agentic`/`--agentic`)와 CLOSE 진입 시 사용자 승인 필수 규칙도 `opal-pilot-dev`와 동일하다.

## 파이프라인

```
TASK → PLAN → EXECUTE → TEST → CLOSE
```

세부 단계 설명, 산출물, 내부 디스패치 워커는 `opal-pilot-dev`의 README를 참조한다. `opal-pilot-dev-short` SKILL.md는 PLAN 결과 기반 Full Task 에스컬레이션 조건(예상 변경 파일 10개 이상, 다단계 기술 의사결정, 다중 모듈 연쇄 영향)을 별도로 정의하지만, 실제 파이프라인 진행은 `opal-pilot-dev`가 담당한다.

## 산출물

`opal-pilot-dev`의 Short profile과 동일: `TASK.md`, `PLAN.md`, `TEST-SCENARIO.md`, `test-scenario.json`, `DONE.md` 등.

## 관련 스킬

- `opal-pilot-dev` — `opds`/`opd`를 실제로 수행하는 canonical 스킬

## FAQ

### `opal-pilot-dev-short`와 `opal-pilot-dev`의 `opds` 중 무엇을 선택해야 하나요?
`opds`로 요청하면 어느 쪽이든 결과적으로 `opal-pilot-dev`가 처리한다. 화면에서 스킬을 선택할 때는 `opal-pilot-dev`를 기준으로 봐도 무방하다.
