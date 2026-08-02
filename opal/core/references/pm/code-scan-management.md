# code-scan.json PM 관리 의무

> 출처: opal-pm.md §9
> Lazy 트리거: code-scan.json 갱신 필요 시
> 탐색 경로: `opal/core/references/pm/code-scan-management.md`

`{프로젝트}/.opal/code-scan.json`은 code-scan 도구의 프로젝트별 설정 파일이다.
PM이 이 파일의 생성과 갱신을 담당한다.

## 생성 시점

**PM이 code-scan을 첫 호출하는 시점에 `.opal/code-scan.json`이 부재하면, 즉석 추론으로 생성한 뒤 호출을 진행한다.** 단 `headerSource`만은 추론 대상이 아니다 — 이 한 값은 소유자에게 2택을 확인하고(§headerSource 필드 관리 — 최초 설정 절차), 나머지 필드는 종전대로 인터럽트 없이 추론한다.

### 추론 소스 규약

| 필드 | 추론 소스 | 규칙 |
|------|----------|------|
| `scopes` | `docs/PROJECT.md §프로젝트 구성` 표의 요소·경로 컬럼 | 부재 시 프로젝트 루트 1-depth 디렉토리 스캔으로 대체 |
| `extensions` | 프로젝트에 실재하는 코드 확장자 자동 감지 | `.md` **기본 포함** — brain·문서 @header 자산화 목적 |
| `exclude` | 기본값(`node_modules`, `__pycache__`, `.git`, `dist`, `build`, `.venv`) | `backup`, `.pytest_cache`, `.next`, `.nuxt`, `tests` 등 보강 |
| `headerSource` | **추론 금지** | PM이 소유자에게 2택을 확인해 확정한다 (§headerSource 필드 관리 참조). 확인 전에는 파일을 생성하지 않는다 |

최소 구조 예시:

```json
{
  "headerSource": "inline",
  "scopes": { "be": "backend/src/", "fe": "frontend/src/" },
  "extensions": [".py", ".js", ".ts", ".vue", ".jsx", ".tsx", ".svelte", ".kt", ".kts", ".java", ".swift", ".md"],
  "exclude": ["node_modules", "__pycache__", ".git", "dist", "build", ".venv", "backup", ".pytest_cache", ".next", ".nuxt"],
  "excludePatterns": []
}
```

`scopes` 항목은 문자열 축약형(`"be": "backend/src/"`) 또는 객체형(`"be": { "path": "backend/src/", "include": [], "exclude": [] }`) 두 형식을 쓴다. 객체형의 `include`/`exclude`는 **파일 집합 필터**이며 모드 선언이 아니다 — 스코프 항목에 `headerSource`를 넣어도 무시되고 stderr 안내 1줄만 나온다.

`scopes`는 프로젝트의 요소/경로 표에서 추론한다.
예: `{ "be": "backend/src/", "fe": "frontend/src/" }`

### 생성 보고

즉석 자동 생성 직후 STATE 자유 텍스트 또는 응답에 다음 형식으로 1줄 보고한다:

```
📂 code-scan.json 자동 생성: headerSource={값} · scopes={N}종 · extensions=[...] · exclude=[...]
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

`.opal/code-scan.json` 최상위의 `headerSource` 필드가 @header를 인라인 주석과 code-map 매니페스트 중 **어느 쪽에 쓰고 어느 쪽에서 읽을지**를 결정한다. 조회·작성·검증 전 경로가 이 한 값을 따른다.

| 값 | 의미 |
|----|------|
| `inline` | 소스 파일 인라인 @header만 사용한다. 매니페스트는 읽지도 쓰지도 않는다 |
| `manifest` | code-map 매니페스트(파일 엔트리 → 패키지 → layerRules → domains 4단)만 사용한다. 인라인은 읽지 않는다 |

- **2택뿐이며 기본값이 없다.** 값이 없거나 두 값 밖이면 도구가 **전 명령을 exit 1로 거부**하고 stdout JSON에 사유(`header_source_unset` \| `header_source_invalid` \| `code_scan_config_invalid`)를, stderr에 사람용 안내를 낸다. 폴백은 없다 — 조용히 다른 모드로 동작하지 않는다.
- **프로젝트당 전역 1회 설정이며 스코프별 재선언은 없다.** `scopes` 항목이나 `.opal/code-map/index.json`의 스코프에 이 키를 넣으면 무시되고 stderr 안내 1줄만 나온다.
- 우선순위는 CLI `--header-source` > 최상위 `headerSource`의 **2층**이다. CLI 플래그는 그 실행 1회에만 적용되므로 설정 파일 기재를 대신하지 않는다.
- 구형 값은 제거되었다 — 설정되어 있으면 무효값으로 거부되며 자동 변환하지 않는다. 프로젝트 전체를 위 2택 중 하나로 통일해 다시 지정한다.

### 최초 설정 절차 (PM)

1. PM이 code-scan을 첫 호출할 때 `.opal/code-scan.json`이 없거나 `headerSource`가 없으면, 소유자에게 다음 2택을 제시하고 확인을 받는다.
   - `inline` — 소스 파일에 직접 @header 주석을 기록한다 (기본 권장 — 소스 편집이 자유로운 저장소)
   - `manifest` — `.opal/code-map/` 외부 매니페스트에만 기록한다 (소스 편집이 제한되는 저장소)
2. 확인된 값을 `.opal/code-scan.json`의 **최상위 `headerSource`**에 기재한 뒤 호출을 진행한다 — 프로젝트당 **전역 1회** 설정이며, 스코프별로 다시 묻거나 재선언하지 않는다.
3. 도구는 이 질문을 하지 않는다 — 비대화형을 유지한다. 도구의 역할은 거부와 안내까지이고, 값의 확정은 소유자, 중개는 PM의 몫이다.
4. 이미 기록된 값을 바꾸는 것은 저장소 전체의 헤더 자산 위치를 바꾸는 결정이므로, PM이 임의로 전환하지 않고 소유자 확인을 다시 받는다.

PM은 유효성 검증을 사전에 대신할 필요가 없다 — 도구가 실행 시작 시 스스로 판정해 거부한다.

## .opal/code-map/index.json PM·소유자 관리 의무

`code-scan discover [--out <path>] [--dry-run]`는 프로젝트 구조를 스캔해 `.opal/code-map/index.json` **초안**을 생성한다(`status: "draft"`, `origin: "discover"`). 이 초안은 자동 추론 결과이므로 그대로 확정 채택하지 않고 다음 흐름을 따른다.

1. **discover 초안 생성**: PM 또는 워커가 `code-scan discover`를 실행해 초안을 생성한다. 이미 `index.json`이 존재하면 도구가 `index_exists` 오류로 거부하므로 `--dry-run`으로 먼저 미리보기하거나 `--out`으로 별도 경로에 생성한다.
2. **소유자 리뷰**: 초안의 `scopes`(root/anchors/stripPrefix/`include`/`exclude`)·`layerRules`·`exclude`·`domains` 값을 소유자가 검토·수정한다. **도구는 도메인 경계·`include`/`exclude` 파일 집합 필터 정책을 판정하지 않는다** — 이 값들은 소유자가 확정한다. 기록 소스(모드)는 index.json 소관이 아니다 — 전역 `headerSource`가 결정한다. PM은 판정을 대신하지 않고 리뷰를 중개·독촉하는 역할에 한정한다.
3. **`status: reviewed` 전환**: 소유자 확인이 끝나면 `status` 필드를 `"draft"`에서 `"reviewed"`로 PM 또는 소유자가 직접 갱신한다. 도구는 이 전환을 자동화하지 않는다 — discover 산출물의 `note` 필드에 `OWNER REVIEW REQUIRED — headerSource/anchors/stripPrefix/include 확인 후 status를 reviewed로 변경` 안내가 포함되어 있다.

PM Gate 검토 절차 8번(`pm-review-gate.md`)에서 `status`가 `"draft"`인 채로 방치된 code-map을 발견하면, PM 임의 확정 없이 소유자에게 리뷰 필요 사실을 보고한다.

> 상세 도구 사용법: `~/.opal/references/tools.md` code-scan 섹션 참조

## 변경이력

| 일시 (KST) | 버전 | 변경 내용 |
|-----------|------|----------|
| 2026-06-11 22:36 | v1.1 | §생성 시점 재작성 — 즉석 추론 자동 생성 문구, 추론 소스 3종 규약(scopes/extensions/exclude), 생성 보고 1줄 형식, brain 품질 회복 근거 추가 (010) |
| 2026-07-28 15:10 | v1.2 | §headerSource 필드 관리(auto/inline/manifest, 기본값 auto, 잘못된 값 stderr 경고 + auto 폴백) 신설. §`.opal/code-map/index.json` PM·소유자 관리 의무 신설 — discover 초안 → 소유자 리뷰 → `status: reviewed` 전환 흐름, 도메인 경계·readonly 정책은 소유자가 확정함을 명시 (077) |
| 2026-08-02 14:47 | v1.4 | §headerSource 필드 관리 재작성 — `inline`/`manifest` 2택·기본값 없음·미설정/무효값 전 명령 거부(`header_source_unset`/`header_source_invalid`/`code_scan_config_invalid`)·CLI > 전역 2층 우선순위·전역 1회 설정(스코프별 재선언 없음) + **최초 설정 절차(PM 중개·소유자 확정) 신설**. §추론 소스 규약에 `headerSource` 추론 금지 행 추가 + 최소 구조 예시·생성 보고에 `headerSource` 포함. §index.json 관리 의무의 `readonly` 정책 서술을 `include`/`exclude` 파일 집합 필터로 교체 + `note` 문자열 인용 갱신. 행 번호 인용(`code-scan.js:187-190`)을 동작 서술로 대체 (080) |
| 2026-07-29 | v1.3 | §갱신 트리거에 `exclude`/`excludePatterns` 변경 후 `scaffold` 재실행 안내 1줄 추가 — 변경 전 등재 파일이 `orphan`으로 남는 문제 예방 (077 결함 D) |
