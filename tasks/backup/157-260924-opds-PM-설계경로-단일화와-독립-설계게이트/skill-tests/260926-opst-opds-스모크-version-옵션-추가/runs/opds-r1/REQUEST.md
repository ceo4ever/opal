# 요구서: stockctl 버전 확인 옵션

운영자가 설치된 stockctl 버전을 확인할 방법이 없다. 아래를 구현한다.

- `stockctl --version`은 표준 출력에 `stockctl 0.1.0` 한 줄을 출력하고 exit 0으로 끝난다. 버전 문자열은 `stockctl/__init__.py`의 `__version__` 값을 사용한다.
- `--version`은 서브커맨드 없이 단독으로 쓸 수 있다. 저장소 파일을 만들거나 읽지 않는다.
- 기존 명령(add/remove/list)과 기존 테스트는 그대로 동작해야 한다.
- `docs/CLI.md`에 옵션을 추가한다.
