# PLAN: OPAL 프로젝트 문서 벡터 스토어

> 작성일: 2026-03-31
> 입력: TASK.md
> 출력: PLAN.md

## 1. 현황 조사

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `opal/tools/check-env.js` | Node.js 환경 검증 | 없음 (참고만) |
| `opal/tools/skill-registry/skill-registry.js` | 스킬 레지스트리 CLI (Node.js) | 없음 (패턴 참고) |
| `scripts/install-mac.sh` | 통합 배포 스크립트 | 수정 — vector-store 의존성 설치 추가 |
| `docs/ARCHITECTURE.md` | 시스템 아키텍처 | 수정 — tools 설명 업데이트 |

### 현재 상태

**기존 도구 구조**:
- `opal/tools/` 소스 → `~/.opal/tools/` 배포 (install-mac.sh 경유)
- 기존 도구: `check-env.js` (단일 스크립트), `skill-registry/` (Node.js CLI)
- 모든 기존 도구가 Node.js로 구현됨
- install-mac.sh는 `opal/tools/` 전체를 `~/.opal/tools/`로 복사 후 Node.js 환경 체크

**install-mac.sh 배포 패턴**:
- `install_dir` 함수로 디렉토리 통째 복사 (`cp -Rf`)
- 클린 삭제: `tools` 포함 6개 프레임워크 디렉토리를 삭제 후 재배포
- Node.js 존재 시 `check-env.js` 실행, 없으면 경고만 출력
- Python 의존성 설치 패턴은 아직 없음 (MCP 머지용 python3은 시스템 기본 사용)

**sqlite-vector 조사 결과**:
- GitHub: https://github.com/sqliteai/sqlite-vector (SQLite Cloud, Inc.)
- 라이선스: OSI 오픈소스 프로젝트에서 무료 사용 가능, 상용은 Elastic License 2.0 / 별도 라이선스
- 지원 플랫폼: macOS arm64 포함 (prebuilt binary + pip + npm)
- API: `vector_init`, `vector_as_f32`, `vector_quantize_scan` 등
- 거리 메트릭: L2, Cosine, Dot Product, L1, Hamming 등 6종
- 데이터 타입: Float32, Float16, BFloat16, Int8, UInt8, 1bit
- 메모리: 기본 30MB
- 특징: 별도 인덱스 구조 없이 BLOB 컬럼에 벡터 저장, 즉시 쿼리 가능
- **Python 패키지**: `pip install sqliteai-vector` → `sqlite_vector.binaries` 경로에서 확장 로드
- **Node.js 패키지**: `@sqliteai/sqlite-vector` → `getExtensionPath()` + `better-sqlite3`로 로드
- **WASM**: `@sqliteai/sqlite-wasm` → 브라우저/Node.js, 자동 확장 로드

**참고: sqlite-vec vs sqlite-vector**:
- `sqlite-vec` (Alex Garcia): 순수 C, 가상 테이블 방식, MIT 라이선스, `sqlite-vec` npm
- `sqlite-vector` (SQLite Cloud): BLOB 기반, quantize_scan 방식, Elastic License 2.0
- TASK.md에서 sqlite-vector를 명시했으므로 이를 따름

### 임베딩 모델 비교

| 모델 | 런타임 | 차원 | 모델 크기 | 특징 |
|------|--------|------|----------|------|
| all-MiniLM-L6-v2 (transformers.js) | Node.js | 384 | ~22MB | ONNX 기반, 빠른 로드, 서버 불필요 |
| all-MiniLM-L6-v2 (sentence-transformers) | Python | 384 | ~22MB | PyTorch 의존, 성숙한 생태계 |
| nomic-embed-text (Ollama) | Ollama 서버 | 768/1024 | ~500MB | 높은 품질, Ollama 별도 실행 필요 |

### 런타임 전략: Python 우선 + Node.js 폴백

**우선순위**: Python3 → Node.js → 설치 안내

| 기준 | Python (우선) | Node.js (폴백) |
|------|--------------|----------------|
| sqlite-vector | `pip install sqliteai-vector` | `@sqliteai/sqlite-vector` + `better-sqlite3` |
| 임베딩 모델 | `sentence-transformers` (all-MiniLM-L6-v2) | `@huggingface/transformers` (ONNX) |
| 임베딩 품질 | 최고 (PyTorch 네이티브) | 동등 (ONNX 변환) |
| 의존성 | pip 패키지 (venv 관리) | npm 패키지 |
| ML 생태계 | 성숙, 모델 선택지 풍부 | 제한적이지만 충분 |

**이유**: 임베딩/ML 생태계는 Python이 압도적. Python이 있으면 Python으로, 없으면 Node.js로 폴백.

**임베딩 모델**: `all-MiniLM-L6-v2` (384차원, ~22MB)
- Python: `sentence-transformers` 직접 로드
- Node.js: `@huggingface/transformers` ONNX 버전
- 문서 임베딩에 충분한 품질 (STS-B ~84-85%)
- 384차원은 sqlite-vector의 Float32 기준 ~1.5KB/벡터로 가벼움

**런타임 디스패처** (`vector-store.sh`):
```bash
#!/bin/bash
# 1) Python3 확인 → python3 vector-store.py "$@"
# 2) Node.js 확인 → node vector-store.js "$@"
# 3) 둘 다 없음 → 설치 안내 메시지 출력
```

**공유 규약**:
- 동일한 DB 스키마 (`~/.opal/vector.db`)
- 동일한 CLI 인터페이스 (명령, 옵션, 출력 형식)
- 동일한 임베딩 모델/차원 (384차원, 코사인 유사도)
- Python/Node 어느 쪽으로 인덱싱해도 상호 검색 가능

### 영향 범위

- `opal/tools/vector-store/` 신규 디렉토리 추가 → `~/.opal/tools/vector-store/` 배포
- `scripts/install-mac.sh` 수정 → Python venv + npm 의존성 설치 단계 추가
- `~/.opal/vector.db` 글로벌 DB 파일 자동 생성 (런타임)
- 기존 도구/스킬에는 영향 없음 (완전 독립 모듈)

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 |
|---|----------|------|
| 1 | `opal/tools/vector-store/vector-store.sh` | 런타임 디스패처 (Python → Node.js → 설치 안내) |
| 2 | `opal/tools/vector-store/vector-store.py` | Python CLI 진입점 + CRUD 명령 |
| 3 | `opal/tools/vector-store/lib/db.py` | Python DB 연결 관리 (sqlite-vector 로드, 스키마 초기화) |
| 4 | `opal/tools/vector-store/lib/embedder.py` | Python 임베딩 provider (sentence-transformers) |
| 5 | `opal/tools/vector-store/lib/chunker.py` | Python 문서 청킹 로직 (마크다운 인식 분할) |
| 6 | `opal/tools/vector-store/lib/commands.py` | Python CLI 명령 구현 (index, search, add, update, delete, status) |
| 7 | `opal/tools/vector-store/requirements.txt` | Python 의존성 선언 |
| 8 | `opal/tools/vector-store/vector-store.js` | Node.js CLI 진입점 (폴백) |
| 9 | `opal/tools/vector-store/lib/db.js` | Node.js DB 연결 관리 (폴백) |
| 10 | `opal/tools/vector-store/lib/embedder.js` | Node.js 임베딩 provider (폴백) |
| 11 | `opal/tools/vector-store/lib/chunker.js` | Node.js 문서 청킹 (폴백) |
| 12 | `opal/tools/vector-store/lib/commands.js` | Node.js CLI 명령 구현 (폴백) |
| 13 | `opal/tools/vector-store/package.json` | npm 패키지 정의 (폴백용) |

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 14 | `scripts/install-mac.sh` | vector-store 의존성 설치 (Python venv + npm 폴백) |

#### 삭제

없음

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | Python 의존성 + 패키지 정의 | `requirements.txt`, `package.json` | 낮음 |
| 2 | Python DB 연결 + 스키마 | `lib/db.py` | 중간 |
| 3 | Python 임베딩 provider | `lib/embedder.py` | 중간 |
| 4 | Python 문서 청킹 | `lib/chunker.py` | 중간 |
| 5 | Python CRUD 명령 | `lib/commands.py` | 높음 |
| 6 | Python CLI 진입점 | `vector-store.py` | 낮음 |
| 7 | Node.js 폴백 구현 | `lib/db.js`, `lib/embedder.js`, `lib/chunker.js`, `lib/commands.js`, `vector-store.js` | 중간 |
| 8 | 런타임 디스패처 | `vector-store.sh` | 낮음 |
| 9 | install-mac.sh 수정 | `scripts/install-mac.sh` | 중간 |

### 핵심 설계

#### 1. 의존성 정의

**requirements.txt** (Python):
```
sqliteai-vector>=0.9.0
sentence-transformers>=3.0.0
```

**package.json** (Node.js 폴백):
```json
{
  "name": "opal-vector-store",
  "version": "1.0.0",
  "description": "OPAL 프로젝트 문서 벡터 스토어 (Node.js fallback)",
  "main": "vector-store.js",
  "type": "module",
  "dependencies": {
    "better-sqlite3": "^11.0.0",
    "@sqliteai/sqlite-vector": "^0.2.0",
    "@huggingface/transformers": "^3.0.0"
  }
}
```

#### 2. DB 스키마 (Python/Node.js 공유)

```sql
CREATE TABLE IF NOT EXISTS chunks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  namespace TEXT NOT NULL,
  file_path TEXT NOT NULL,
  chunk_index INTEGER NOT NULL,
  content TEXT NOT NULL,
  embedding BLOB,
  metadata TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now')),
  UNIQUE(namespace, file_path, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_chunks_namespace ON chunks(namespace);
CREATE INDEX IF NOT EXISTS idx_chunks_file ON chunks(namespace, file_path);
```

- DB 위치: `~/.opal/vector.db`
- `vector_init('chunks', 'embedding', 'type=FLOAT32,dimension=384,distance=COSINE')` 호출
- 네임스페이스로 프로젝트 분리 (동일 DB 파일 공유)
- Python과 Node.js가 동일 DB/스키마를 공유하므로 상호 호환

#### 3. 임베딩 provider

**Python** (`lib/embedder.py`):
```python
class EmbeddingProvider:
    def initialize(self): ...
    def embed(self, text) -> list[float]: ...
    @property
    def dimensions(self) -> int: ...

class SentenceTransformersProvider(EmbeddingProvider):
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
    def embed(self, text):
        return self.model.encode(text).tolist()
    @property
    def dimensions(self): return 384
```

**Node.js** (`lib/embedder.js`):
```javascript
class TransformersProvider {
  constructor(modelName = 'Xenova/all-MiniLM-L6-v2') { ... }
  async embed(text) { /* pipeline('feature-extraction') → Float32Array */ }
  get dimensions() { return 384; }
}
```

- 동일 모델(`all-MiniLM-L6-v2`), 동일 차원(384)으로 상호 호환
- 향후 확장: `OllamaProvider` 등 추가 가능

#### 4. 문서 청킹 (Python/Node.js 공유 알고리즘)

- `## 헤딩` 기준으로 1차 분할
- 각 섹션이 `MAX_CHUNK_SIZE`(기본 1000자)를 초과하면 단락 단위로 2차 분할
- 청크에 메타데이터 부착: `{ heading, file_path, chunk_index }`
- YAML frontmatter는 메타데이터로 추출하되 청크에서 제외
- 지원 파일: `.md`, `.txt` (향후 확장 가능)

#### 5. CLI 명령 (Python/Node.js 동일 인터페이스)

| 명령 | 설명 | 사용법 |
|------|------|--------|
| `index` | 프로젝트 문서 전체 인덱싱 | `vector-store.sh index --namespace <ns> --dir <path> [--pattern "**/*.md"]` |
| `search` | 시맨틱 검색 | `vector-store.sh search --namespace <ns> --query "<text>" [--top-k 5]` |
| `add` | 단일 파일/텍스트 추가 | `vector-store.sh add --namespace <ns> --file <path>` |
| `update` | 파일 재인덱싱 (변경 감지) | `vector-store.sh update --namespace <ns> --file <path>` |
| `delete` | 파일/네임스페이스 삭제 | `vector-store.sh delete --namespace <ns> [--file <path>]` |
| `status` | DB 상태 조회 | `vector-store.sh status [--namespace <ns>]` |

검색 출력 형식:
```
[0.92] docs/ARCHITECTURE.md (chunk 3)
  > OPAL은 2-레이어 아키텍처로 동작한다...

[0.87] docs/PROJECT.md (chunk 1)
  > AI 환경에서 IT 프로젝트를 체계적으로...
```

#### 6. 런타임 디스패처 (`vector-store.sh`)

```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 1) Python3 확인
if command -v python3 &>/dev/null; then
    VENV="$SCRIPT_DIR/.venv"
    if [[ -f "$VENV/bin/activate" ]]; then
        source "$VENV/bin/activate"
    fi
    exec python3 "$SCRIPT_DIR/vector-store.py" "$@"
fi

# 2) Node.js 확인
if command -v node &>/dev/null; then
    exec node "$SCRIPT_DIR/vector-store.js" "$@"
fi

# 3) 둘 다 없음
echo "Error: Python3 또는 Node.js가 필요합니다." >&2
echo "  - Python3 설치: brew install python3" >&2
echo "  - Node.js 설치: brew install node" >&2
exit 1
```

#### 7. install-mac.sh 수정

```bash
# ── vector-store 의존성 설치 ──
if [[ -d "$opal_home/tools/vector-store" ]]; then
    # Python 우선
    if command -v python3 &>/dev/null; then
        info "vector-store Python 의존성 설치..."
        python3 -m venv "$opal_home/tools/vector-store/.venv" 2>/dev/null
        "$opal_home/tools/vector-store/.venv/bin/pip" install -q \
            -r "$opal_home/tools/vector-store/requirements.txt" 2>/dev/null && \
            success "vector-store Python 의존성 설치 완료" || \
            warn "vector-store Python 의존성 설치 실패"
    # Node.js 폴백
    elif command -v node &>/dev/null && command -v npm &>/dev/null; then
        info "vector-store Node.js 폴백 의존성 설치..."
        (cd "$opal_home/tools/vector-store" && npm install --production --silent 2>/dev/null) && \
            success "vector-store Node.js 의존성 설치 완료" || \
            warn "vector-store Node.js 의존성 설치 실패"
    else
        warn "Python3 또는 Node.js가 없습니다 — vector-store를 사용하려면 설치하세요"
    fi
    # 디스패처 실행 권한
    chmod +x "$opal_home/tools/vector-store/vector-store.sh" 2>/dev/null
fi
```

## 3. 실행 체크리스트

> 총 9개 Step

### Step 1: 의존성 정의
- [ ] 완료
- **파일**: `opal/tools/vector-store/requirements.txt`, `opal/tools/vector-store/package.json`
- **작업 내용**: Python 의존성(`sqliteai-vector`, `sentence-transformers`) + Node.js 의존성(`better-sqlite3`, `@sqliteai/sqlite-vector`, `@huggingface/transformers`) 선언
- **완료 기준**: 파일 생성, 의존성 목록 정확
- **테스트**: 파일 존재 확인
- **의존**: 없음

### Step 2: Python DB 연결 + 스키마 (`lib/db.py`)
- [ ] 완료
- **파일**: `opal/tools/vector-store/lib/db.py`
- **작업 내용**: `~/.opal/vector.db` 경로로 sqlite3 연결, `sqlite_vector` 확장 로드, chunks 테이블 + 인덱스 생성, `vector_init` 호출. `get_db(db_path?)` export
- **완료 기준**: `python3 -c "from lib.db import get_db; db = get_db(); print('ok')"` 성공
- **테스트**: `~/.opal/vector.db` 파일 생성, chunks 테이블 존재 확인
- **의존**: Step 1

### Step 3: Python 임베딩 provider (`lib/embedder.py`)
- [ ] 완료
- **파일**: `opal/tools/vector-store/lib/embedder.py`
- **작업 내용**: `EmbeddingProvider` 베이스 클래스, `SentenceTransformersProvider` 구현 (`all-MiniLM-L6-v2`). `create_provider(type?)` 팩토리 함수. 첫 호출 시 모델 다운로드
- **완료 기준**: `provider.embed("hello world")` → 384차원 list[float] 반환
- **테스트**: 짧은 텍스트 임베딩 생성, 차원 수 검증
- **의존**: Step 1

### Step 4: Python 문서 청킹 (`lib/chunker.py`)
- [ ] 완료
- **파일**: `opal/tools/vector-store/lib/chunker.py`
- **작업 내용**: 마크다운 헤딩 기반 분할, 최대 1000자, YAML frontmatter 파싱/제외, 메타데이터 부착. `chunk_file(file_path)` → `[{content, metadata}]`
- **완료 기준**: ARCHITECTURE.md 입력 시 복수 청크 반환, 각 청크 1000자 이하
- **테스트**: 실제 프로젝트 문서로 청킹 결과 확인
- **의존**: 없음

### Step 5: Python CRUD 명령 (`lib/commands.py`)
- [ ] 완료
- **파일**: `opal/tools/vector-store/lib/commands.py`
- **작업 내용**: 6개 명령 — `index`, `search`, `add`, `update`, `delete`, `status`
- **완료 기준**: `index` → `search`로 관련 문서 검색 성공
- **테스트**: `docs/` 인덱싱 후 "아키텍처" 검색 시 ARCHITECTURE.md 상위 반환
- **의존**: Step 2, Step 3, Step 4

### Step 6: Python CLI 진입점 (`vector-store.py`)
- [ ] 완료
- **파일**: `opal/tools/vector-store/vector-store.py`
- **작업 내용**: `argparse`로 명령/옵션 파싱, commands 모듈 라우팅, `--help`, 에러 핸들링
- **완료 기준**: `python3 vector-store.py --help` 도움말 출력
- **테스트**: `python3 vector-store.py index --namespace test --dir ./docs` 정상 실행
- **의존**: Step 5

### Step 7: Node.js 폴백 구현
- [ ] 완료
- **파일**: `opal/tools/vector-store/vector-store.js`, `lib/db.js`, `lib/embedder.js`, `lib/chunker.js`, `lib/commands.js`
- **작업 내용**: Python 구현과 동일한 기능을 Node.js로 구현. 동일 DB 스키마, 동일 CLI 인터페이스, 동일 임베딩 모델/차원
- **완료 기준**: `node vector-store.js index --namespace test --dir ./docs` 정상 실행, Python으로 인덱싱한 데이터를 Node.js로 검색 가능 (상호 호환)
- **테스트**: Node.js로 `search` 실행 시 Python으로 인덱싱한 결과 검색 확인
- **의존**: Step 1

### Step 8: 런타임 디스패처 (`vector-store.sh`)
- [ ] 완료
- **파일**: `opal/tools/vector-store/vector-store.sh`
- **작업 내용**: Python3 → Node.js → 설치 안내 우선순위로 런타임 감지 및 디스패치
- **완료 기준**: `./vector-store.sh --help` 실행 시 적절한 런타임으로 디스패치
- **테스트**: Python3 있는 환경에서 Python 실행 확인, `PATH`에서 python3 제거 후 Node.js 폴백 확인
- **의존**: Step 6, Step 7

### Step 9: install-mac.sh 수정
- [ ] 완료
- **파일**: `scripts/install-mac.sh`
- **작업 내용**: Python venv 생성 + pip install (우선), Node.js npm install (폴백), 둘 다 없으면 경고. `vector-store.sh` 실행 권한 설정
- **완료 기준**: install-mac.sh 실행 후 Python venv 또는 node_modules 설치 확인
- **테스트**: `~/.opal/tools/vector-store/vector-store.sh status` 정상 실행
- **의존**: Step 8

## 4. QA 체크리스트

### 기능 테스트
- [ ] `index` 명령으로 프로젝트 문서 디렉토리 인덱싱 성공
- [ ] `search` 명령으로 자연어 쿼리 시 관련 문서 청크 반환
- [ ] `add` 명령으로 단일 파일 추가 후 검색 가능
- [ ] `update` 명령으로 파일 수정 후 재인덱싱 반영
- [ ] `delete` 명령으로 파일/네임스페이스 삭제 후 검색 불가
- [ ] `status` 명령으로 네임스페이스별 통계 출력
- [ ] 프로젝트별 네임스페이스 분리 확인 (다른 네임스페이스 검색 시 혼재 없음)
- [ ] `~/.opal/vector.db` 글로벌 위치에 DB 생성 확인
- [ ] 외부 API 호출 없이 완전 로컬 동작 확인
- [ ] Python → Node.js 폴백 전환 정상 동작
- [ ] Python/Node.js 상호 호환 (Python 인덱싱 → Node.js 검색, 역방향 포함)
- [ ] 둘 다 없을 때 설치 안내 메시지 출력

### 일관성 테스트
- [ ] 기존 `opal/tools/` 구조 패턴과 일관
- [ ] install-mac.sh 기존 흐름에 자연스럽게 통합 (기존 기능 파괴 없음)
- [ ] CLI 인터페이스 Python/Node.js 동일 (명령, 옵션, 출력 형식)

### 문서 품질
- [ ] 한국어 본문 + 영어 코드/필드명 규칙
- [ ] kebab-case 파일/폴더 네이밍
- [ ] requirements.txt, package.json 필드 정확

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| sqlite-vector 바이너리 호환 (Python pip / Node npm) | 확장 로드 실패 | GitHub releases에서 macOS arm64 바이너리 수동 다운로드 폴백. 또는 `sqlite-vec`(MIT) 대안 |
| 첫 임베딩 시 모델 다운로드 (~22MB) 필요 | 오프라인 환경에서 첫 실행 실패 | install-mac.sh에서 모델 프리로드 옵션 또는 사전 다운로드 안내 |
| Python/Node.js 둘 다 없는 환경 | 도구 사용 불가 | 디스패처에서 명확한 설치 안내 메시지 출력 |
| sentence-transformers PyTorch 의존성 크기 (~2GB) | 설치 시간/용량 | Python 환경이 이미 있으면 무시할 수준. Node.js 폴백 제공 |
| sqlite-vector Elastic License 2.0 | 상용 서비스 제공 시 이슈 | OPAL 오픈소스 사용은 무료. 상용 전환 시 재검토 |
| 대규모 문서 인덱싱 시 시간 소요 | UX 저하 | 진행률 표시, 배치 처리, incremental 모드 |
