# E2E 프로젝트 설정

프로젝트별 E2E driver 매니페스트와 후보 순서 같은 추적 설정을 둔다.
실행 산출물은 이 디렉터리에 저장하지 않고 `.e2e/artifacts/`에 저장한다.

`environment.json`은 이 프로젝트의 E2E 실행 환경 선언이다. test-tool은 여기에 적힌 서비스(기동 명령·작업 폴더·환경 변수·health·의존 순서)를 띄우고, 표면(web·api·데스크톱·human)으로 테스트 대상을 고른다. 비밀값은 원문을 적지 않고 환경 변수 이름만 적는다. 필드 표와 검증 규칙의 원본은 `opal/tools/test-tool/lib/e2e/environment.py`다.
