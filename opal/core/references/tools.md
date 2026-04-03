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

## 변경이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-04-03 | xlsx-tool 등록 (076) |
