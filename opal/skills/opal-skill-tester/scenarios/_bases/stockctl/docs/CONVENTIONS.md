# 컨벤션

- Python 3 표준 라이브러리만 사용한다.
- 모든 소스 파일 상단에 @header(module/layer/domain/description/exports)를 둔다.
- 저장은 임시 파일 기록 후 `os.replace`로 원자 교체한다.
- 오류는 stderr에 한 줄로 쓰고 종료 코드로 구분한다.
- 테스트는 `tests/`에 pytest로 작성하고 CLI는 `python -m stockctl`로 호출한다.
- 커밋 메시지: `<type>(<task>): <요약>`
