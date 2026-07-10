# TRD: hello-cli (드라이런)

## 기술 선택
- 언어: Bash (외부 의존성 없음, 표준 내장 명령만 사용)
- 위치: `dryrun/src/hello.sh`

## 구현 방식
- `$1`을 name으로 받아 `echo "Hello, $1!"` 출력
- 인자 누락 시 동작은 범위 밖(드라이런이므로 미정의)

## 수용 기준
- `bash dryrun/src/hello.sh World` → stdout `Hello, World!`, exit code 0
