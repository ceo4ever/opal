# code-scan 관리 가이드 (테스트 픽스처 — 태스크 077 결함 C)

이 문서는 `@header` 메타블록이 무엇인지 설명하는 산문이다. 각 코드 파일 상단에
이 블록을 작성해두면 code-scan 도구가 파일을 빠르게 분석할 수 있다는 취지를
설명할 뿐, 이 문서 자신은 실제 @header 블록을 보유하지 않는다.

## 설정 예시

프로젝트 루트에 `.opal/code-scan.json` 파일을 아래와 같이 작성한다:

    {
      "scopes": { "be": "workspace/backend/" },
      "extensions": [".py", ".js"],
      "exclude": ["node_modules", "fixtures"]
    }

이 설정 예시 JSON은 스캔 범위를 제한하기 위한 예시 자료일 뿐 이 문서의 헤더가
아니다. 이 문서에는 표준 포맷(header-standard.md §3)의 `@header {` 근접 토큰이
어디에도 등장하지 않는다.
