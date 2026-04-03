# PLAN: OPAL xlsx-tool

> 작성일: 2026-04-03 | 태스크: 076-opp-xlsx-tool

## 산출물 목록

| # | 산출물 | 경로 | 설명 |
|---|--------|------|------|
| 1 | `requirements.txt` | `opal/tools/requirements.txt` | OPAL 통합 Python 의존성 |
| 2 | `xlsx-tool.py` | `opal/tools/xlsx-tool/xlsx-tool.py` | CLI 메인 스크립트 |
| 3 | `run.sh` | `opal/tools/xlsx-tool/run.sh` | venv python 래퍼 |
| 4 | `install-mac.sh` 수정 | `scripts/install-mac.sh` | venv 생성 + pip install 섹션 추가 |

---

## Step 1 — requirements.txt 생성

`opal/tools/requirements.txt` 신규 생성.

```
# Office XML (docx / pptx / xlsx 공통)
openpyxl>=3.1.0
pandas>=2.0.0
lxml>=5.0.0
defusedxml>=0.7.0

# PDF
pypdf>=4.0.0
pdf2image>=1.17.0
pdfplumber>=0.11.0

# Image / GIF
Pillow>=10.0.0
imageio>=2.31.0
imageio-ffmpeg>=0.4.9
numpy>=1.24.0

# AI / MCP
anthropic>=0.39.0
mcp>=1.1.0
PyYAML>=6.0.0

# Web Testing
playwright>=1.40.0
```

---

## Step 2 — xlsx-tool.py 구현

`opal/tools/xlsx-tool/xlsx-tool.py` 신규 생성.

### 커맨드 구조

```
python xlsx-tool.py <command> [options]

Commands:
  info     <file>              시트 목록, 행/열 수, 헤더 메타데이터 출력
  read     <file> [options]    시트 데이터를 JSON으로 출력
  search   <file> [options]    키워드 또는 셀 범위로 검색
  write    <file> [options]    JSON/CSV 데이터를 xlsx로 저장 (신규 또는 수정)
```

### 옵션 상세

```
read:
  --sheet <name|index>    특정 시트 선택 (기본: 전체)
  --range <A1:Z100>       셀 범위 제한
  --header-row <n>        헤더 행 번호 (기본: 1)

search:
  --sheet <name|index>
  --keyword <text>        키워드 검색
  --range <A1:Z100>       범위 내 검색

write:
  --sheet <name>          대상 시트명 (기본: Sheet1)
  --mode <new|update>     신규 생성 또는 기존 파일 수정
  --data <json_string>    인라인 JSON 데이터
  --data-file <path>      JSON 파일 경로
  --format                헤더 볼드, 열 너비 자동, 테두리 기본 서식 적용
```

### 출력 형식

모든 커맨드는 JSON으로 출력한다.

```json
// 성공
{ "ok": true, "command": "read", "data": [...] }

// 실패
{ "ok": false, "command": "read", "error": "Sheet 'foo' not found" }
```

### 구현 전략

- `info`, `read`, `search` — openpyxl (서식 보존, 셀 단위 접근)
- `write` 신규 — pandas (대량 데이터) + openpyxl (서식 적용)
- `write` 수정 — openpyxl (기존 파일 서식 유지)

---

## Step 3 — run.sh 생성

`opal/tools/xlsx-tool/run.sh` 신규 생성.

```bash
#!/bin/bash
# xlsx-tool 래퍼 — OPAL venv python 호출
VENV_PYTHON="$HOME/.opal/.venv/bin/python"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -x "$VENV_PYTHON" ]]; then
  echo '{"ok":false,"error":"OPAL venv not found. Run install-mac.sh first."}' >&2
  exit 1
fi

exec "$VENV_PYTHON" "$SCRIPT_DIR/xlsx-tool.py" "$@"
```

---

## Step 4 — install-mac.sh 수정

`install_opal()` 함수 내 도구 설치 블록 다음에 venv 섹션 추가.

### 추가 위치

기존 `install_dir "$opal_dir/tools" ...` 블록 바로 다음.

### 추가 내용

```bash
# ── Python venv ──
install_opal_venv
```

### 신규 함수 `install_opal_venv()`

```bash
install_opal_venv() {
    local venv_dir="$USER_HOME/.opal/.venv"
    local req_src="$FRAMEWORK_ROOT/opal/tools/requirements.txt"

    if [[ ! -f "$req_src" ]]; then
        warn "opal/tools/requirements.txt 없음 — Python venv 스킵"
        return
    fi

    info "Python 가상환경 설정..."

    # venv 생성 (없으면)
    if [[ ! -d "$venv_dir" ]]; then
        python3 -m venv "$venv_dir"
        success "venv 생성: $venv_dir"
    else
        success "venv 기존 사용: $venv_dir"
    fi

    # 패키지 설치
    "$venv_dir/bin/pip" install --quiet --upgrade pip
    "$venv_dir/bin/pip" install --quiet -r "$req_src"
    success "Python 패키지 설치 완료 (requirements.txt)"

    # playwright 브라우저 초기화
    "$venv_dir/bin/playwright" install --quiet 2>/dev/null || \
        warn "playwright install 실패 — 수동 실행: ~/.opal/.venv/bin/playwright install"
}
```

---

## QA 체크리스트

- [ ] `run.sh info sample.xlsx` → JSON 메타데이터 출력
- [ ] `run.sh read sample.xlsx --sheet Sheet1` → 데이터 JSON 출력
- [ ] `run.sh search sample.xlsx --keyword 키워드` → 매칭 셀 위치 반환
- [ ] `run.sh write output.xlsx --data '[{"A":1}]' --format` → 파일 생성 + 헤더 볼드
- [ ] `run.sh write existing.xlsx --mode update --sheet Sheet1 --data '[...]'` → 기존 파일 수정
- [ ] venv 없는 환경에서 `run.sh` → 구조화된 JSON 에러 반환
- [ ] install-mac.sh 실행 후 `~/.opal/.venv/` 생성 확인
- [ ] install-mac.sh 실행 후 `pip list`로 패키지 설치 확인
- [ ] `~/.opal/tools/xlsx-tool/run.sh` 배포 확인
