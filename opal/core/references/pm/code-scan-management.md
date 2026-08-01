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

`exclude`/`excludePatterns` 설정을 변경한 뒤에는 `scaffold`를 재실행해 매니페스트를 정리한다(변경 전 등재 파일이 `orphan`으로 남는다).

## PM Gate 확인 절차

`opal-pm.md` §4 검토 절차 8번에서 code-scan.json 갱신이 필요하다고 판단되면:
1. `.opal/code-scan.json`을 Read하여 현재 상태 확인
2. 갱신 필요 시 직접 수정한다 (이 경우는 PM이 직접 갱신 허용)
3. 갱신 내용을 소유자에게 보고한다

## headerSource 필드 관리

`.opal/code-scan.json`의 `headerSource` 필드은 @header 조회 시 인라인/code-map 매니페스트 중 어느 쪽을 우선·전용으로 볼지 결정한다.

| 값 | 의미 |
|----|------|
| `auto` (기본값) | 인라인 @header 우선, 없으면 code-map 매니페스트(파일 엔트리 → 패키지 → layerRules → domains 순) 조회 |
| `inline` | 인라인 @header만 사용, code-map 매니페스트는 조회하지 않음 |
| `manifest` | 인라인 추출을 건너뛰고 code-map 매니페스트만 조회 |

`auto`/`inline`/`manifest` 3종 외의 값이 설정되면 도구가 stderr에 `Warning: invalid headerSource "..." falling back to "auto"`를 출력하고 `auto`로 자동 폴백한다(`code-scan.js:187-190`). PM은 이 필드를 프로젝트 특성(단일 저장소 vs readonly 벤더 서브트리 혼재 등)에 맞춰 설정하되, 유효성 검증 자체는 도구가 자체 수행하므로 PM이 별도로 사전 검증할 필요는 없다.

## .opal/code-map/index.json PM·소유자 관리 의무

`code-scan discover [--out <path>] [--dry-run]`는 프로젝트 구조를 스캔해 `.opal/code-map/index.json` **초안**을 생성한다(`status: "draft"`, `origin: "discover"`). 이 초안은 자동 추론 결과이므로 그대로 확정 채택하지 않고 다음 흐름을 따른다.

1. **discover 초안 생성**: PM 또는 워커가 `code-scan discover`를 실행해 초안을 생성한다. 이미 `index.json`이 존재하면 도구가 `index_exists` 오류로 거부하므로 `--dry-run`으로 먼저 미리보기하거나 `--out`으로 별도 경로에 생성한다.
2. **소유자 리뷰**: 초안의 `scopes`(root/anchors/stripPrefix/`readonly`)·`layerRules`·`exclude`·`domains` 값을 소유자가 검토·수정한다. **도구는 도메인 경계·`readonly` 정책을 판정하지 않는다** — 이 값들은 소유자가 확정한다. PM은 판정을 대신하지 않고 리뷰를 중개·독촉하는 역할에 한정한다.
3. **`status: reviewed` 전환**: 소유자 확인이 끝나면 `status` 필드를 `"draft"`에서 `"reviewed"`로 PM 또는 소유자가 직접 갱신한다. 도구는 이 전환을 자동화하지 않는다 — discover 산출물의 `note` 필드에 "OWNER REVIEW REQUIRED — readonly/anchors/stripPrefix 확인 후 status를 reviewed로 변경" 안내가 포함되어 있다.

PM Gate 검토 절차 8번(`pm-review-gate.md`)에서 `status`가 `"draft"`인 채로 방치된 code-map을 발견하면, PM 임의 확정 없이 소유자에게 리뷰 필요 사실을 보고한다.

> 상세 도구 사용법: `~/.opal/references/tools.md` code-scan 섹션 참조

## 변경이력

| 일시 (KST) | 버전 | 변경 내용 |
|-----------|------|----------|
| 2026-06-11 22:36 | v1.1 | §생성 시점 재작성 — 즉석 추론 자동 생성 문구, 추론 소스 3종 규약(scopes/extensions/exclude), 생성 보고 1줄 형식, brain 품질 회복 근거 추가 (010) |
| 2026-07-28 15:10 | v1.2 | §headerSource 필드 관리(auto/inline/manifest, 기본값 auto, 잘못된 값 stderr 경고 + auto 폴백) 신설. §`.opal/code-map/index.json` PM·소유자 관리 의무 신설 — discover 초안 → 소유자 리뷰 → `status: reviewed` 전환 흐름, 도메인 경계·readonly 정책은 소유자가 확정함을 명시 (077) |
| 2026-07-29 | v1.3 | §갱신 트리거에 `exclude`/`excludePatterns` 변경 후 `scaffold` 재실행 안내 1줄 추가 — 변경 전 등재 파일이 `orphan`으로 남는 문제 예방 (077 결함 D) |
