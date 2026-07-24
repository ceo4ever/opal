# CONTRACT: hello-cli (드라이런)

> oppl Loop 1 D4 산출물 구조 재현 — `references/contract.md` §2(스키마·시그니처·경계 + 기계검증절 + 루브릭절) 준수.

## 1. 스키마 (Schema)

- 입력: CLI 위치 인자 1개 `name` (string, 필수, `$1`)
- 출력: stdout 문자열 `Hello, <name>!` (단일 라인)
- exit code: 0 (성공). 그 외 값은 정의하지 않음(범위 밖)

## 2. 시그니처 (Signature)

- 호출 형태: `bash dryrun/src/hello.sh <name>`
- 반환값: 없음 — stdout 출력과 프로세스 exit code로만 결과를 전달

## 3. 경계 (Boundary)

- `hello.sh`는 stdout 출력과 exit code 산출까지만 책임진다.
- 인자 검증(빈 문자열·특수문자 등)과 호출 실패 처리는 계약 범위 밖 — 호출자가 올바른 인자를 전달할 책임을 진다.

## 4. 기계검증절 (Machine-Verifiable Section)

- 검증 명령: `bash dryrun/src/hello.sh World`
- 기대 결과: stdout == `Hello, World!` (trailing newline 허용) AND exit code == 0
- 검증 주체: opal-test-agent (T4a, Phase C에서 실제 실행)

## 5. 루브릭절 (Rubric Section)

Evaluator가 D6/G 게이트에서 판정하는 기준 (Likert 1–5, 통과선 ≥4):

| 항목 | 설명 |
|------|------|
| 계약 완전성 | 스키마·시그니처·경계가 hello.sh 구현에 필요한 정보를 빠짐없이 담는가 |
| 계약 일관성 | PRD/TRD의 수용 기준과 본 문서 §4 기계검증절이 동일한 명령·기대값을 가리키는가 |
| 설계 정합 | 경계 정의가 드라이런 목적(최소 규모 재현)에 맞게 과설계 없이 단순한가 |
