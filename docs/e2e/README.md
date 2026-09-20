# E2E 여정 라이브러리

검증을 통과해 프로젝트 자산으로 승격된 E2E 여정과 재사용 조각을 추적한다. 각 문서는
Markdown 안 fenced YAML 한 벌을 계약 원본으로 가지며 test-tool이 그 원본을 직접 읽는다.

- `journeys/`: 사용자 관점의 완결된 여정
- `fragments/`: 여러 여정이 공유하는 재사용 조각

조각은 `id`·`params`·`steps`와 하나 이상의 `postconditions`를 가져야 한다. `fill`·`type`
입력은 원문 `value`가 아니라 환경 변수 이름을 받는 `value_ref`로 선언한다. 여정은
`steps[]`에 `{fragment: <id>, with: {...}}`를 두어 조각을 참조한다. 참조는 여정에서
조각으로만 향하며 조각끼리 중첩하지 않는다.

전개된 각 step은 `fragment:<id>:<회차>:<원래-step-id>` 식별자를 받아 여정 본문 step과
구분된다. 두 범위에 같은 연산이 있어도 정상적인 별도 실행으로 유지되며, 각 연산이
`actions.jsonl` 한 행으로 남는다.

실행 산출물과 로컬 상태는 이 디렉터리가 아니라, Git에서 전량 제외되는
`<project>/.e2e/` 아래에 둔다.

## 승격 게이트

태스크의 `e2e/` 초안은 같은 journey id의 실행이 완전한 `pass` 증적을 남긴 뒤에만 이
디렉터리로 승격할 자격이 있다. 자격은 다음 명령의 `eligible=true`만 인정한다.

```bash
~/.opal/tools/test-tool/run.sh e2e promote-check \
  --journey <journey-id> --run-id <run-id> [--artifact-root <path>]
```

도구는 `run.json`의 status·exit·실행 여부·증적 완전성과 journey 일치를 읽기 전용으로
검사한다. 사람의 산문 판단이나 실패·불완전 run은 승격 근거가 아니다.
