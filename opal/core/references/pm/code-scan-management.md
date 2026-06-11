# code-scan.json PM 관리 의무

> 출처: opal-pm.md §9
> Lazy 트리거: code-scan.json 갱신 필요 시
> 탐색 경로: `opal/core/references/pm/code-scan-management.md`

`{프로젝트}/.opal/code-scan.json`은 code-scan 도구의 프로젝트별 설정 파일이다.
PM이 이 파일의 생성과 갱신을 담당한다.

## 생성 시점

**PM이 code-scan을 첫 호출하는 시점에 `.opal/code-scan.json`이 부재하면, 사용자 인터럽트 없이 즉석 추론으로 생성한 뒤 호출을 진행한다.**

### 추론 소스 3종 규약

| 필드 | 추론 소스 | 규칙 |
|------|----------|------|
| `scopes` | `docs/PROJECT.md §프로젝트 구성` 표의 요소·경로 컬럼 | 부재 시 프로젝트 루트 1-depth 디렉토리 스캔으로 대체 |
| `extensions` | 프로젝트에 실재하는 코드 확장자 자동 감지 | `.md` **기본 포함** — brain·문서 @header 자산화 목적 |
| `exclude` | 기본값(`node_modules`, `__pycache__`, `.git`, `dist`, `build`, `.venv`) | `backup`, `.pytest_cache`, `.next`, `.nuxt`, `tests` 등 보강 |

최소 구조 예시:

```json
{
  "scopes": { "be": "backend/src/", "fe": "frontend/src/" },
  "extensions": [".py", ".js", ".ts", ".vue", ".jsx", ".tsx", ".svelte", ".kt", ".kts", ".java", ".swift", ".md"],
  "exclude": ["node_modules", "__pycache__", ".git", "dist", "build", ".venv", "backup", ".pytest_cache", ".next", ".nuxt"],
  "excludePatterns": []
}
```

`scopes`는 프로젝트의 요소/경로 표에서 추론한다.
예: `{ "be": "backend/src/", "fe": "frontend/src/" }`

### 생성 보고

즉석 자동 생성 직후 STATE 자유 텍스트 또는 응답에 다음 형식으로 1줄 보고한다:

```
📂 code-scan.json 자동 생성: scopes={N}종 · extensions=[...] · exclude=[...]
```

> **brain 품질 회복 근거**: brain `sync-header` / `analyze`가 `.opal/code-scan.json` 부재 시 `code_scan_json_missing`으로 실패한다(`brain_tool.py:632-643`). 자동 생성은 brain 지식 품질 회복에 직접 기여한다.

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

## 변경이력

| 일시 (KST) | 버전 | 변경 내용 |
|-----------|------|----------|
| 2026-06-11 22:36 | v1.1 | §생성 시점 재작성 — 즉석 추론 자동 생성 문구, 추론 소스 3종 규약(scopes/extensions/exclude), 생성 보고 1줄 형식, brain 품질 회복 근거 추가 (010) |
