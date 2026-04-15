# OPAL Tools

> OPAL 에이전트가 파일 처리, 데이터 변환 등 특정 작업 시 호출하는 CLI 도구 레지스트리.
> 새 도구 추가 시 이 파일에 등록하고 install-mac.sh의 `install_opal_venv()`를 통해 배포한다.

---

## xlsx-tool

**용도**: xlsx 파일 읽기, 쓰기, 검색, 메타데이터 조회  
**실행 경로**: `~/.opal/tools/xlsx-tool/run.sh`  
**소스 경로**: `opal/tools/xlsx-tool/`  
**의존성**: `~/.opal/.venv` (openpyxl, pandas)

### 커맨드

```bash
# 시트 목록, 행/열 수, 헤더 메타데이터 조회
~/.opal/tools/xlsx-tool/run.sh info <file>

# 데이터 읽기 (JSON 출력)
~/.opal/tools/xlsx-tool/run.sh read <file> [--sheet <name|index>] [--range <A1:Z100>] [--header-row <n>]

# 키워드 검색
~/.opal/tools/xlsx-tool/run.sh search <file> --keyword <text> [--sheet <name>] [--range <A1:Z100>]

# 데이터 쓰기 (신규 또는 수정)
~/.opal/tools/xlsx-tool/run.sh write <file> --data '<json>' [--sheet <name>] [--mode new|update] [--format]
~/.opal/tools/xlsx-tool/run.sh write <file> --data-file <path.json> [--sheet <name>] [--mode new|update] [--format]
```

### 출력 형식

모든 커맨드는 JSON으로 출력한다.

```json
// 성공
{ "ok": true, "command": "read", "data": [...] }

// 실패
{ "ok": false, "command": "read", "error": "Sheet 'foo' not found" }
```

### 사용 예시

```bash
# 파일 구조 파악
~/.opal/tools/xlsx-tool/run.sh info project.xlsx

# 특정 시트 읽기
~/.opal/tools/xlsx-tool/run.sh read data.xlsx --sheet "2026"

# 키워드로 셀 찾기
~/.opal/tools/xlsx-tool/run.sh search wbs.xlsx --keyword "백엔드"

# JSON 데이터로 새 파일 생성 (서식 포함)
~/.opal/tools/xlsx-tool/run.sh write output.xlsx \
  --data '[{"이름":"홍길동","부서":"개발"}]' \
  --format

# 기존 파일의 특정 시트 업데이트
~/.opal/tools/xlsx-tool/run.sh write report.xlsx \
  --mode update --sheet "요약" \
  --data '[{"항목":"완료","수":"12"}]'
```

---

## code-scan

**용도**: 코드 파일의 `@header` 메타블록 스캔 — 도메인/레이어/의존 관계 조회  
**실행 경로**: `node ~/.opal/tools/code-scan/code-scan.js <command>`  
**소스 경로**: `opal/tools/code-scan/`  
**의존성**: Node.js (외부 패키지 없음)

### 커맨드

```bash
# 전체 스캔 (scope 미지정 시 프로젝트 전체)
node ~/.opal/tools/code-scan/code-scan.js scan [path] [--scope <name>]

# 도메인별 조회 (인자 없으면 목록)
node ~/.opal/tools/code-scan/code-scan.js domain [name]

# 레이어별 조회 (인자 없으면 목록)
node ~/.opal/tools/code-scan/code-scan.js layer [name]

# 헤더 내 패턴 검색 (정규식 지원, 대소문자 무시)
node ~/.opal/tools/code-scan/code-scan.js search <pattern>
# 예: search "auth.*service", search "^user", search "login|logout"

# 도메인/레이어 요약
node ~/.opal/tools/code-scan/code-scan.js summary

# 의존 관계 추적
node ~/.opal/tools/code-scan/code-scan.js depends <module>

# @header 없는 파일 목록
node ~/.opal/tools/code-scan/code-scan.js missing
```

### 주요 옵션

| 옵션 | 설명 |
|------|------|
| `--scope <name>` | 스코프 필터 (`.opal/code-scan.json`의 `scopes` 키) |
| `--domain <name>` | 도메인 필터 |
| `--layer <name>` | 레이어 필터 |
| `--exclude <patterns>` | 제외 패턴 (쉼표 구분, 와일드카드 지원) |
| `--brief` | 한 줄 요약 출력 (기본값) |
| `--full` | 전체 헤더 JSON 출력 |
| `--json` | 파이프용 raw JSON 출력 |

### 프로젝트 설정

프로젝트 루트의 `.opal/code-scan.json`으로 스코프와 필터를 정의한다.

```json
{
  "scopes": { "be": "workspace/backend/", "fe": "workspace/frontend/src/" },
  "extensions": [".py", ".js", ".ts", ".vue"],
  "exclude": ["node_modules", "__pycache__"],
  "excludePatterns": ["__init__.py", "test_*", "*.spec.ts"]
}
```

### PM 관리 방안

`{프로젝트}/.opal/code-scan.json`은 PM이 생성하고 관리한다.

- **생성 시점**: code-scan 도구를 처음 사용하려 할 때 파일이 없으면 PM이 생성
- **갱신 트리거**: 신규 도메인/폴더 추가, 대규모 리팩토링, 신규 언어 도입
- **PM Gate 확인**: EXECUTE 완료 후 PM Gate에서 신규 scope/domain 반영 여부 확인

상세 관리 절차: `~/.opal/references/opal-pm.md` §9 참조

### 사용 예시

```bash
# BE 스코프 도메인 요약
node ~/.opal/tools/code-scan/code-scan.js summary --scope be

# auth 모듈 의존 관계 추적
node ~/.opal/tools/code-scan/code-scan.js depends auth

# @header 누락 파일 확인
node ~/.opal/tools/code-scan/code-scan.js missing --scope fe

# exports 필드 전용 검색 (정규식 지원, 대소문자 무시)
node ~/.opal/tools/code-scan/code-scan.js exports "issueToken"
# 예: exports "^get[A-Z]", exports "Token$", exports "create|update"

# @header 검증 (PM Gate용)
node ~/.opal/tools/code-scan/code-scan.js scan src/auth/auth.service.ts --json
```

---

## 변경이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-04-03 | xlsx-tool 등록 (076) |
| v1.1 | 2026-04-11 | code-scan 등록 |
| v1.2 | 2026-04-12 | code-scan 섹션에 PM 관리 방안 서브섹션 추가 + exports 커맨드 사용 예시 추가 (109) |
