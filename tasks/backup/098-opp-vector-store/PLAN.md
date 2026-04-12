# PLAN: OPAL Vector Store — sqlite-vec 기반 문서 벡터 검색 도구

> 작성일: 2026-04-07
> 입력: TASK.md + tasks/backup/059-opal-vector-store/PLAN.md (선행 설계 계승)
> 출력: PLAN.md

---

## 1. 현황 조사

### 1.1 기존 도구 구조

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `opal/tools/skill-registry/skill-registry.js` | 스킬 레지스트리 CLI (Node.js) | 없음 (패턴 참고) |
| `opal/tools/xlsx-tool/run.sh` | OPAL .venv python 호출 래퍼 | 없음 (run.sh 패턴 참고) |
| `opal/tools/check-env.js` | Node.js 환경 검증 | 없음 (참고만) |
| `opal/tools/requirements.txt` | Python 의존성 (글로벌 .venv) | **확인 필요** — vector-store 의존성 추가 여부 |
| `opal/core/hooks/claude-hooks.json` | Claude Code 훅 설정 | **수정** — PostToolUse(Write\|Edit) 추가 |
| `opal/core/references/opal-pm.md` | PM 행동 프로세스 | **수정** — §3 Step 2 벡터 검색 보강 |
| `opal/core/AGENT.md` | 에이전트 코어 정의 | **수정** — skill-registry 시맨틱 폴백 절차 추가 |
| `scripts/install-mac.sh` | 통합 배포 스크립트 | **수정** — vector-store 의존성 설치 + 초기 인덱싱 + 훅 머지 |
| `docs/ARCHITECTURE.md` | 시스템 아키텍처 | **수정** — tools/ 설명에 vector-store 추가 |

### 1.2 059 설계 계승/변경 비교

| 항목 | 059 (backup) | 098 (이번 태스크) |
|------|-------------|-----------------|
| 벡터 라이브러리 | sqlite-vector (Elastic License 2.0) | **sqlite-vec** (MIT) |
| 저장 방식 | BLOB 컬럼 + `vector_init` | **vec0 가상 테이블** |
| Python 패키지 | `sqliteai-vector` | **`sqlite-vec`** |
| Node.js 패키지 | `@sqliteai/sqlite-vector` | **`sqlite-vec` + `better-sqlite3`** |
| 진입점 파일명 | `vector-store.sh` | **`run.sh`** (xlsx-tool 패턴 일관) |
| tasks 인덱싱 | TASK.md + DONE.md | **TASK.md + STATE.md** (DONE.md 제외) |
| JSON 출력 | 미명시 | **`--json` 필수 플래그** |
| 스킬 통합 문서 수정 | 없음 | **opal-pm.md + AGENT.md 수정** |
| install-mac.sh 연동 | 의존성 설치만 | **초기 인덱싱 + 모델 프리로드 + 훅 머지** |
| 훅 설정 | 없음 | **PostToolUse(Write\|Edit) 자동 인덱싱** |

### 1.3 sqlite-vec API 요약

**Python**:
```python
import sqlite3, sqlite_vec
conn = sqlite3.connect("vector.db")
conn.enable_load_extension(True)
sqlite_vec.load(conn)
conn.enable_load_extension(False)
conn.execute("""
  CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(
    chunk_id INTEGER PRIMARY KEY,
    embedding float[384]
  )
""")
# 검색
conn.execute(
  "SELECT chunk_id, distance FROM vec_chunks WHERE embedding MATCH ? AND k=5 ORDER BY distance",
  [sqlite_vec.serialize_float32(query_vec)]
)
```

**Node.js**:
```javascript
const Database = require('better-sqlite3');
const sqliteVec = require('sqlite-vec');
const db = new Database('vector.db');
sqliteVec.load(db);
db.exec(`CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(
  chunk_id INTEGER PRIMARY KEY, embedding float[384]
)`);
```

### 1.4 영향 범위

- `opal/tools/vector-store/` 신규 디렉토리 추가 → `~/.opal/tools/vector-store/` 배포
- `~/.opal/vector.db` 글로벌 DB 파일 자동 생성 (런타임)
- 기존 `~/.opal/.venv/` 공유 또는 전용 venv 선택 필요 (§2.1 설계 결정 참조)
- 기존 도구(skill-registry, xlsx-tool)에는 영향 없음

---

## 2. 설계 결정

### 2.1 Python 환경 전략: 전용 venv vs 글로벌 .venv

**결정**: **전용 venv** (`opal/tools/vector-store/.venv`)

**근거**:
- `sentence-transformers`는 PyTorch를 포함하여 ~2GB 이상 — 글로벌 `.venv`에 추가하면 기존 사용자에게 큰 부하
- xlsx-tool은 이미 `~/.opal/.venv`를 공유하지만 경량 패키지(`openpyxl`, `pandas`)만 포함
- vector-store 전용 venv를 `opal/tools/vector-store/.venv`에 생성하면 독립성 보장
- install-mac.sh가 vector-store 디렉토리 복사 시 `.venv`는 복사 제외 후 배포 경로에서 생성

### 2.2 DB 스키마 설계 (sqlite-vec vec0 + chunks 메타 테이블 분리)

```sql
-- 메타데이터 테이블 (일반 SQLite)
CREATE TABLE IF NOT EXISTS chunks (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  namespace  TEXT    NOT NULL,
  file_path  TEXT    NOT NULL,
  chunk_index INTEGER NOT NULL,
  content    TEXT    NOT NULL,
  heading    TEXT,
  metadata   TEXT,                             -- JSON (추가 메타)
  created_at TEXT    DEFAULT (datetime('now')),
  updated_at TEXT    DEFAULT (datetime('now')),
  UNIQUE(namespace, file_path, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_chunks_namespace ON chunks(namespace);
CREATE INDEX IF NOT EXISTS idx_chunks_file      ON chunks(namespace, file_path);

-- 벡터 테이블 (sqlite-vec vec0 가상 테이블)
CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(
  chunk_id  INTEGER PRIMARY KEY,     -- chunks.id와 1:1
  embedding float[384]
);
```

**설계 이유**:
- `vec0` 가상 테이블은 `content`, `metadata` 등 일반 컬럼을 지원하지 않으므로 메타 테이블 분리 필수
- 검색 흐름: `vec_chunks` → `chunk_id` → `chunks` JOIN으로 content + file_path + heading 조회
- `namespace`로 opal/프로젝트별 분리, 동일 DB 파일 공유

### 2.3 run.sh 진입점 설계 (xlsx-tool 패턴 계승)

xlsx-tool의 `run.sh`는 글로벌 `.venv`를 사용하지만, vector-store는 전용 venv를 사용한다:

```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"

# 1) 전용 venv Python 우선
if [[ -x "$VENV_PYTHON" ]]; then
    exec "$VENV_PYTHON" "$SCRIPT_DIR/vector-store.py" "$@"
fi

# 2) 시스템 Python3 (의존성 없이 동작하지 않으므로 설치 안내)
if command -v python3 &>/dev/null; then
    echo '{"ok":false,"error":"vector-store venv not found. Run install-mac.sh first."}' >&2
    exit 1
fi

# 3) Node.js 폴백
if command -v node &>/dev/null && [[ -d "$SCRIPT_DIR/node_modules" ]]; then
    exec node "$SCRIPT_DIR/vector-store.js" "$@"
fi

echo '{"ok":false,"error":"Python3 venv 또는 Node.js node_modules가 없습니다. Run install-mac.sh first."}' >&2
exit 1
```

### 2.4 JSON 출력 형식 (필수 표준)

```json
// 성공
{"ok": true, "results": [{"score": 0.92, "file": "...", "chunk": 3, "content": "..."}]}

// 에러
{"ok": false, "error": "namespace 'opal' not found in vector.db"}
```

- `--json` 플래그가 없으면 사람이 읽기 쉬운 텍스트 형식 출력 (하위 호환)
- 에러는 항상 JSON (스킬/에이전트가 파싱 가능해야 함)

### 2.5 네임스페이스 설계

```
~/.opal/vector.db
├── namespace: opal
│   ├── ~/.opal/skills/*/SKILL.md
│   ├── ~/.opal/agents/*/AGENT.md
│   └── ~/.opal/references/*.md
└── namespace: {project-name}   (예: "opal", "myapp")
    ├── {project}/docs/          전체 .md 파일
    ├── {project}/tasks/*/TASK.md
    ├── {project}/tasks/*/STATE.md
    └── {project}/.opal/memory/*.md
```

- `opal` 네임스페이스: install-mac.sh 실행 시 자동 인덱싱
- 프로젝트 네임스페이스: `run.sh index --namespace <name> --dir <path>` 수동 또는 opi 연동

---

## 3. 구현 계획

### 3.1 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 |
|---|----------|------|
| 1 | `opal/tools/vector-store/run.sh` | 런타임 디스패처 (전용 venv → Node.js 폴백) |
| 2 | `opal/tools/vector-store/vector-store.py` | Python CLI 진입점 + 명령 라우팅 |
| 3 | `opal/tools/vector-store/lib/db.py` | DB 연결 + sqlite-vec 로드 + 스키마 초기화 |
| 4 | `opal/tools/vector-store/lib/embedder.py` | 임베딩 provider (sentence-transformers, all-MiniLM-L6-v2) |
| 5 | `opal/tools/vector-store/lib/chunker.py` | 마크다운 청킹 (헤딩 기반 1차 + 1000자 2차 분할) |
| 6 | `opal/tools/vector-store/lib/commands.py` | 6개 CLI 명령 구현 (index, search, add, update, delete, status) |
| 7 | `opal/tools/vector-store/requirements.txt` | Python 의존성 선언 (sqlite-vec, sentence-transformers) |
| 8 | `opal/tools/vector-store/vector-store.js` | Node.js CLI 진입점 (폴백) |
| 9 | `opal/tools/vector-store/lib/db.js` | Node.js DB 연결 + sqlite-vec 로드 |
| 10 | `opal/tools/vector-store/lib/embedder.js` | Node.js 임베딩 provider (@huggingface/transformers ONNX) |
| 11 | `opal/tools/vector-store/lib/chunker.js` | Node.js 청킹 (Python과 동일 알고리즘) |
| 12 | `opal/tools/vector-store/lib/commands.js` | Node.js 6개 명령 구현 |
| 13 | `opal/tools/vector-store/package.json` | npm 패키지 정의 (Node.js 폴백용) |

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 14 | `opal/core/hooks/claude-hooks.json` | PostToolUse(Write\|Edit) 훅 추가 — `docs/*.md`, `.opal/memory/*.md`, `tasks/*/TASK.md`, `tasks/*/STATE.md` 대상 자동 인덱싱 |
| 15 | `opal/core/references/opal-pm.md` | §3 Step 2에 vector-store 검색 보강 절차 추가 (조건부, 사용 가능 시) |
| 16 | `opal/core/AGENT.md` | 스킬 레지스트리 섹션에 시맨틱 폴백 절차 추가 |
| 17 | `scripts/install-mac.sh` | vector-store 전용 venv 생성 + pip install + opal 네임스페이스 초기 인덱싱 + 모델 프리로드 + PostToolUse 훅 머지 |
| 18 | `docs/ARCHITECTURE.md` | Global Layer tools/ 테이블에 `vector-store/` 설명 추가 |

#### 삭제

없음

### 3.2 핵심 의존성

**requirements.txt** (Python, 전용 venv):
```
sqlite-vec>=0.1.0
sentence-transformers>=3.0.0
```

**package.json** (Node.js 폴백):
```json
{
  "name": "opal-vector-store",
  "version": "1.0.0",
  "description": "OPAL 문서 벡터 스토어 (Node.js fallback)",
  "main": "vector-store.js",
  "dependencies": {
    "better-sqlite3": "^11.0.0",
    "sqlite-vec": "^0.1.0",
    "@huggingface/transformers": "^3.0.0"
  }
}
```

### 3.3 임베딩 provider

| 항목 | Python | Node.js |
|------|--------|---------|
| 패키지 | `sentence-transformers` | `@huggingface/transformers` |
| 모델 | `all-MiniLM-L6-v2` | `Xenova/all-MiniLM-L6-v2` |
| 차원 | 384 | 384 |
| 비고 | PyTorch 기반, 최고 품질 | ONNX 변환, 동등 품질 |

두 런타임 모두 동일 모델/차원 → Python 인덱싱 ↔ Node.js 검색 상호 호환.

### 3.4 훅 설정 (claude-hooks.json 수정 내용)

```json
{
  "PostToolUse": [
    {
      "matcher": "Write|Edit",
      "hooks": [
        {
          "type": "command",
          "command": "bash -c 'FILE=\"$CLAUDE_TOOL_INPUT_FILE_PATH\"; if [[ \"$FILE\" =~ (docs/[^/]+\\.md|.opal/memory/[^/]+\\.md|tasks/[^/]+/TASK\\.md|tasks/[^/]+/STATE\\.md)$ ]]; then NS=$(basename $(pwd)); ~/.opal/tools/vector-store/run.sh update --namespace \"$NS\" --file \"$FILE\" 2>/dev/null; fi'"
        }
      ]
    }
  ]
}
```

**참고**: install-mac.sh의 `merge_hooks_config` 함수로 `~/.claude/settings.json`에 머지.

### 3.5 opal-pm.md §3 Step 2 추가 내용

```markdown
#### 벡터 검색 보강 (vector-store 사용 가능 시)

`~/.opal/tools/vector-store/run.sh` 가 존재하면, 문서 테이블 선별 후 추가로 시맨틱 검색을 수행하여 누락된 관련 문서를 보완한다:

```bash
~/.opal/tools/vector-store/run.sh search \
  --namespace {project-name} \
  --query "{작업 설명}" \
  --top-k 5 \
  --json
```

- 검색 결과 중 문서 테이블에 없는 파일이 있으면 추가 선별 대상으로 고려한다
- 도구가 없거나 DB가 초기화되지 않은 경우 이 단계를 건너뛴다
```

### 3.6 AGENT.md 스킬 레지스트리 섹션 추가 내용

```markdown
#### 시맨틱 폴백 (vector-store 사용 가능 시)

`skill-registry.js match` 결과가 없을 때, `~/.opal/tools/vector-store/run.sh` 가 존재하면:

```bash
~/.opal/tools/vector-store/run.sh search \
  --namespace opal \
  --query "{입력 키워드}" \
  --top-k 3 \
  --json
```

결과에서 `SKILL.md` 경로를 추출하여 스킬명을 제안한다. 도구가 없으면 "스킬을 찾을 수 없습니다" 안내를 출력한다.
```

### 3.7 install-mac.sh 추가 구현

```bash
# ── vector-store 전용 venv + 의존성 ──────────────────────
install_vector_store() {
    local vs_dir="$opal_home/tools/vector-store"
    if [[ ! -d "$vs_dir" ]]; then
        warn "vector-store 디렉토리 없음 — 스킵"
        return
    fi

    if command -v python3 &>/dev/null; then
        info "vector-store Python venv 생성..."
        python3 -m venv "$vs_dir/.venv" 2>/dev/null
        "$vs_dir/.venv/bin/pip" install -q \
            -r "$vs_dir/requirements.txt" && \
            success "vector-store Python 의존성 설치 완료" || \
            warn "vector-store Python 의존성 설치 실패"

        # 임베딩 모델 프리로드
        info "임베딩 모델 프리로드 (all-MiniLM-L6-v2)..."
        "$vs_dir/.venv/bin/python" -c \
            "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')" && \
            success "임베딩 모델 프리로드 완료" || \
            warn "임베딩 모델 프리로드 실패 (첫 실행 시 다운로드 필요)"

        # opal 네임스페이스 초기 인덱싱
        info "opal 네임스페이스 초기 인덱싱..."
        "$vs_dir/run.sh" index --namespace opal --dir "$opal_home" \
            --pattern "skills/*/SKILL.md" \
            --pattern "agents/*/AGENT.md" \
            --pattern "references/*.md" && \
            success "opal 네임스페이스 인덱싱 완료" || \
            warn "opal 네임스페이스 인덱싱 실패"

    elif command -v node &>/dev/null && command -v npm &>/dev/null; then
        info "vector-store Node.js 의존성 설치..."
        (cd "$vs_dir" && npm install --production --silent) && \
            success "vector-store Node.js 의존성 설치 완료" || \
            warn "vector-store Node.js 의존성 설치 실패"
    else
        warn "Python3 또는 Node.js 없음 — vector-store를 사용하려면 설치 필요"
    fi

    chmod +x "$vs_dir/run.sh"

    # PostToolUse 훅 머지
    local claude_settings="$HOME/.claude/settings.json"
    local hooks_src="$FRAMEWORK_ROOT/opal/core/hooks/claude-hooks.json"
    if [[ -f "$hooks_src" ]]; then
        merge_hooks_config "$claude_settings" "$hooks_src"
        success "Claude Code 훅 설정 머지 완료"
    fi
}
```

---

## 4. 구현 순서 (Step별 실행 계획)

> 총 11개 Step

### Step 1: 의존성 파일 정의
- **파일**: `requirements.txt`, `package.json`
- **작업**: sqlite-vec + sentence-transformers (Python), sqlite-vec + better-sqlite3 + @huggingface/transformers (Node.js)
- **완료 기준**: 파일 생성, 버전 명시
- **의존**: 없음

### Step 2: Python DB 모듈 (`lib/db.py`)
- **파일**: `opal/tools/vector-store/lib/db.py`
- **작업**: sqlite-vec 로드, `chunks` 메타 테이블 + `vec_chunks` 가상 테이블 생성, `get_db(path?)` 함수 export
- **완료 기준**: `python3 -c "from lib.db import get_db; get_db(); print('ok')"` 성공
- **의존**: Step 1

### Step 3: Python 임베딩 모듈 (`lib/embedder.py`)
- **파일**: `opal/tools/vector-store/lib/embedder.py`
- **작업**: `SentenceTransformersProvider` 클래스, `create_provider()` 팩토리
- **완료 기준**: `provider.embed("hello world")` → 384차원 list[float]
- **의존**: Step 1

### Step 4: Python 청킹 모듈 (`lib/chunker.py`)
- **파일**: `opal/tools/vector-store/lib/chunker.py`
- **작업**: 헤딩 기반 1차 분할 → 1000자 초과 시 단락 단위 2차 분할, YAML frontmatter 제외, `chunk_file(path)` → `[{content, heading, chunk_index}]`
- **완료 기준**: 실제 마크다운 파일 입력 시 복수 청크 반환, 각 청크 1000자 이하
- **의존**: 없음

### Step 5: Python 명령 모듈 (`lib/commands.py`)
- **파일**: `opal/tools/vector-store/lib/commands.py`
- **작업**: `index`, `search`, `add`, `update`, `delete`, `status` 6개 명령. `--json` 플래그 지원
- **완료 기준**: `index` → `search --json` 파이프라인 성공, JSON 형식 준수
- **의존**: Step 2, 3, 4

### Step 6: Python CLI 진입점 (`vector-store.py`)
- **파일**: `opal/tools/vector-store/vector-store.py`
- **작업**: `argparse` 파싱, 명령 라우팅, `--help`, 에러 핸들링
- **완료 기준**: `python3 vector-store.py --help` 출력, `python3 vector-store.py index --namespace test --dir ./docs` 정상 실행
- **의존**: Step 5

### Step 7: `run.sh` 진입점
- **파일**: `opal/tools/vector-store/run.sh`
- **작업**: 전용 venv Python → Node.js 폴백 → 설치 안내 순서로 디스패치. xlsx-tool run.sh 패턴 계승
- **완료 기준**: `./run.sh --help` 실행 시 Python 또는 Node.js로 디스패치
- **의존**: Step 6

### Step 8: Node.js 폴백 구현
- **파일**: `vector-store.js`, `lib/db.js`, `lib/embedder.js`, `lib/chunker.js`, `lib/commands.js`
- **작업**: Python 구현과 동일한 기능. 동일 DB 스키마 + CLI 인터페이스 + 임베딩 모델/차원
- **완료 기준**: Node.js로 `search` 실행 시 Python으로 인덱싱한 데이터 검색 가능 (상호 호환)
- **의존**: Step 1

### Step 9: 훅 설정 수정 (`claude-hooks.json`)
- **파일**: `opal/core/hooks/claude-hooks.json`
- **작업**: `PostToolUse(Write|Edit)` 이벤트 + 경로 패턴 필터 추가
- **완료 기준**: JSON 유효성, 기존 SubagentStop/Stop 훅과 공존
- **의존**: Step 7

### Step 10: 스킬 통합 문서 수정
- **파일**: `opal/core/references/opal-pm.md`, `opal/core/AGENT.md`
- **작업**:
  - `opal-pm.md` §3 Step 2 — 벡터 검색 보강 절차 추가 (조건부)
  - `AGENT.md` 스킬 레지스트리 섹션 — 시맨틱 폴백 절차 추가
- **완료 기준**: 두 파일에 절차 명시, 조건부(`vector-store 사용 가능 시`) 분기 표현
- **의존**: Step 7

### Step 11: install-mac.sh + ARCHITECTURE.md 수정
- **파일**: `scripts/install-mac.sh`, `docs/ARCHITECTURE.md`
- **작업**:
  - install-mac.sh: `install_vector_store` 함수 추가, OPAL 설치 옵션(메뉴 1, 3)에서 호출
  - ARCHITECTURE.md: Global Layer tools/ 테이블에 `vector-store/` 행 추가
- **완료 기준**: install-mac.sh 실행 후 `run.sh status` 정상 동작, ARCHITECTURE.md에 설명 반영
- **의존**: Step 7, 8, 9, 10

---

## 5. 실행 체크리스트

### Step 1 — 의존성 파일 정의
- [ ] `opal/tools/vector-store/requirements.txt` 생성 (`sqlite-vec`, `sentence-transformers` 버전 명시)
- [ ] `opal/tools/vector-store/package.json` 생성 (`sqlite-vec`, `better-sqlite3`, `@huggingface/transformers` 버전 명시)
- **테스트**: 두 파일 존재 및 내용 확인

### Step 2 — Python DB 모듈
- [ ] `opal/tools/vector-store/lib/db.py` 생성
- [ ] sqlite-vec 로드 + chunks 테이블 + vec_chunks 가상 테이블 생성
- [ ] `get_db(path=None)` export (기본값: `~/.opal/vector.db`)
- **테스트**: `python3 -c "from lib.db import get_db; get_db(); print('ok')"` 성공

### Step 3 — Python 임베딩 모듈
- [ ] `opal/tools/vector-store/lib/embedder.py` 생성
- [ ] `SentenceTransformersProvider` 클래스 + `create_provider()` 팩토리
- **테스트**: 384차원 벡터 반환 확인

### Step 4 — Python 청킹 모듈
- [ ] `opal/tools/vector-store/lib/chunker.py` 생성
- [ ] 헤딩 기반 분할 + 1000자 초과 시 단락 분할
- [ ] YAML frontmatter 파싱 후 청크 제외
- **테스트**: `docs/ARCHITECTURE.md` 청킹 시 복수 청크 + 각 1000자 이하

### Step 5 — Python 명령 모듈
- [ ] `opal/tools/vector-store/lib/commands.py` 생성
- [ ] `index`, `search`, `add`, `update`, `delete`, `status` 구현
- [ ] `--json` 플래그: `{"ok": true/false, "results": [...]}` 형식 준수
- **테스트**: `docs/` 인덱싱 후 "아키텍처" 검색 → ARCHITECTURE.md 청크 상위 반환

### Step 6 — Python CLI 진입점
- [ ] `opal/tools/vector-store/vector-store.py` 생성
- [ ] argparse 파싱, 명령 라우팅, `--help` 출력
- **테스트**: `python3 vector-store.py --help` 정상 출력

### Step 7 — run.sh 진입점
- [ ] `opal/tools/vector-store/run.sh` 생성 (실행 권한 포함)
- [ ] 전용 venv Python → 설치 안내 → Node.js 폴백 순서
- **테스트**: `./run.sh --help` 실행 시 Python으로 디스패치

### Step 8 — Node.js 폴백
- [ ] `opal/tools/vector-store/vector-store.js` + `lib/db.js` + `lib/embedder.js` + `lib/chunker.js` + `lib/commands.js` 생성
- [ ] Python과 동일한 DB 스키마 + CLI 인터페이스
- [ ] `@huggingface/transformers` ONNX 임베딩 (Xenova/all-MiniLM-L6-v2)
- **테스트**: Python 인덱싱 → Node.js 검색 상호 호환

### Step 9 — 훅 설정 수정
- [ ] `opal/core/hooks/claude-hooks.json`에 `PostToolUse` 이벤트 추가
- [ ] 대상 경로: `docs/*.md`, `.opal/memory/*.md`, `tasks/*/TASK.md`, `tasks/*/STATE.md`
- **테스트**: JSON 유효성 검사, 기존 훅과 공존 확인

### Step 10 — 스킬 통합 문서 수정
- [ ] `opal-pm.md` §3 Step 2에 "벡터 검색 보강" 절 추가 (조건부)
- [ ] `AGENT.md` 스킬 레지스트리 섹션에 "시맨틱 폴백" 절 추가
- **테스트**: 두 파일에서 `vector-store` 키워드 존재 확인

### Step 11 — install-mac.sh + ARCHITECTURE.md
- [ ] `install-mac.sh`에 `install_vector_store` 함수 추가
- [ ] 메뉴 옵션 1, 3 실행 경로에 함수 호출 추가
- [ ] opal 네임스페이스 초기 인덱싱 + 모델 프리로드 포함
- [ ] `docs/ARCHITECTURE.md` Global Layer tools/ 테이블에 `vector-store/` 행 추가
- **테스트**: 시뮬레이션(실제 배포는 캡틴 수행)

---

## 6. QA 체크리스트

### 기능 테스트

- [ ] `run.sh index --namespace test --dir ./docs` — 인덱싱 성공
- [ ] `run.sh search --namespace test --query "아키텍처" --json` — 유효한 JSON, results 배열 포함
- [ ] `run.sh search --json` 결과: `{"ok": true, "results": [{"score": ..., "file": ..., "chunk": N, "content": ...}]}`
- [ ] `run.sh add --namespace test --file docs/ARCHITECTURE.md` — 단일 파일 추가 후 검색 가능
- [ ] `run.sh update --namespace test --file docs/ARCHITECTURE.md` — 재인덱싱 후 최신 내용 반영
- [ ] `run.sh delete --namespace test --file docs/ARCHITECTURE.md` — 삭제 후 검색 불가
- [ ] `run.sh delete --namespace test` — 네임스페이스 전체 삭제
- [ ] `run.sh status` — 네임스페이스별 청크 수 + DB 크기 출력
- [ ] 프로젝트별 네임스페이스 분리 — 다른 네임스페이스 검색 시 혼재 없음
- [ ] `~/.opal/vector.db` 글로벌 위치 생성 확인
- [ ] 외부 API 호출 없이 완전 로컬 동작
- [ ] 에러 케이스: DB 없음, 파일 없음, namespace 없음 → `{"ok": false, "error": "..."}` 반환

### 런타임 호환성

- [ ] Python 전용 venv 있을 때: Python으로 디스패치
- [ ] Python venv 없고 Node.js 있을 때: Node.js로 폴백
- [ ] 둘 다 없을 때: 설치 안내 + 에러 JSON 출력
- [ ] Python 인덱싱 → Node.js 검색: 상호 호환 (동일 결과)
- [ ] Node.js 인덱싱 → Python 검색: 상호 호환

### 통합 테스트

- [ ] `opal-pm.md` §3 Step 2에 vector-store 절차 존재 + 조건부 분기 명시
- [ ] `AGENT.md` 스킬 레지스트리 섹션에 시맨틱 폴백 절차 존재
- [ ] `claude-hooks.json` PostToolUse 훅 추가 + JSON 유효성
- [ ] `install-mac.sh`에 `install_vector_store` 함수 존재 + 기존 기능 파괴 없음

### 코드 품질

- [ ] 한국어 본문 + 영어 코드/필드명
- [ ] kebab-case 파일/폴더 네이밍
- [ ] 기존 `opal/tools/` 패턴과 일관 (run.sh 진입점, JSON 에러 형식)
- [ ] `requirements.txt`, `package.json` 필드 정확

---

## 7. 리스크

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| sqlite-vec macOS arm64 바이너리 호환 | 확장 로드 실패 → 도구 전체 불동작 | `sqlite_vec.load(conn)` 실패 시 명확한 에러 메시지 + GitHub releases 수동 설치 안내 |
| sentence-transformers PyTorch 의존성 크기 (~2GB) | install 시간/용량 증가 | 전용 venv 격리로 기존 .venv 영향 없음. Node.js 폴백 제공 |
| 임베딩 모델 첫 다운로드 (~22MB) | 오프라인 환경 첫 실행 실패 | install-mac.sh에서 프리로드. 실패 시 경고만 출력 (첫 search 시 재시도) |
| vec0 가상 테이블 SQLite 버전 의존성 | 구버전 SQLite에서 동작 불가 | `sqlite-vec` 패키지가 SQLite 번들 포함하므로 시스템 SQLite 버전 무관 |
| PostToolUse 훅 경로 패턴 오탐 | 불필요한 자동 인덱싱으로 성능 저하 | 경로 패턴을 최대한 좁게 설정. `2>/dev/null`으로 훅 실패가 편집 작업을 방해하지 않도록 |
| Python/Node.js 임베딩 벡터 불일치 | 상호 호환 실패 → 검색 오작동 | 동일 모델 (`all-MiniLM-L6-v2`, 384차원) + 동일 정규화 방식 강제. 호환성 테스트 항목 포함 |
| `merge_hooks_config` 기존 훅 덮어쓰기 | 기존 SubagentStop/Stop 훅 소실 | `merge_hooks_config`는 이벤트 키 단위로 머지 → 기존 이벤트는 유지. 단, 동일 이벤트 키가 있으면 덮어쓰기 → PostToolUse 훅은 신규이므로 기존 훅과 충돌 없음 |
