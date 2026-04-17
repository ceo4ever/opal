# code-scan.json PM 관리 의무

> 출처: opal-pm.md §9
> Lazy 트리거: code-scan.json 갱신 필요 시
> 탐색 경로: `opal/core/references/pm/code-scan-management.md`

`{프로젝트}/.opal/code-scan.json`은 code-scan 도구의 프로젝트별 설정 파일이다.
PM이 이 파일의 생성과 갱신을 담당한다.

## 생성 시점

code-scan 도구를 처음 사용하려 할 때 `.opal/code-scan.json`이 없으면 PM이 직접 생성한다.

최소 구조:

```json
{
  "scopes": {},
  "extensions": [".py", ".js", ".ts", ".vue", ".jsx", ".tsx", ".svelte", ".kt", ".kts", ".java", ".swift"],
  "exclude": ["node_modules", "__pycache__", ".git", "dist", "build", ".venv"],
  "excludePatterns": []
}
```

`scopes`는 프로젝트의 BE/FE 디렉터리 구조에 맞게 정의한다.
예: `{ "be": "backend/src/", "fe": "frontend/src/" }`

## 갱신 트리거

다음 상황에서 PM이 code-scan.json을 검토하고 필요 시 갱신한다:

1. **신규 도메인/폴더 추가**: EXECUTE 결과로 새 도메인 또는 주요 폴더가 추가된 경우
2. **대규모 리팩토링**: 폴더 구조가 변경된 경우
3. **신규 기술 스택 추가**: 기존 extensions에 없는 확장자를 가진 언어가 도입된 경우

## PM Gate 확인 절차

`opal-pm.md` §4 검토 절차 8번에서 code-scan.json 갱신이 필요하다고 판단되면:
1. `.opal/code-scan.json`을 Read하여 현재 상태 확인
2. 갱신 필요 시 직접 수정한다 (이 경우는 PM이 직접 갱신 허용)
3. 갱신 내용을 소유자에게 보고한다

> 상세 도구 사용법: `~/.opal/references/tools.md` code-scan 섹션 참조
