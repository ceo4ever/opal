# PRD: hello-cli (드라이런)

## 목표
`hello <name>` 형태로 호출하면 인사말을 출력하는 초소형 CLI를 만든다.

## 배경
oppl Loop 1 D2~D5 산출물 구조를 최소 규모로 재현·검증하기 위한 드라이런 대상.

## 범위
- 단일 bash 스크립트 `dryrun/src/hello.sh` 하나만 구현 (Phase C에서 작성)
- 인자 1개(name)를 받아 인사말 출력

## 수용 기준
- `bash dryrun/src/hello.sh World` 실행 시 stdout에 정확히 `Hello, World!` 출력 + exit code 0

## 비범위
- 다국어 지원, 인자 검증 고급화, 패키징/배포 없음
