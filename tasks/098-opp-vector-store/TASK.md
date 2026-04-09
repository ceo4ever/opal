# TASK: OPAL Vector Store — sqlite-vec 기반 문서 벡터 검색 도구

> 작성일: 2026-04-08 | 작업 유형: 신규 | 적용 스킬: opp | 모드: interactive
> 입력: 사용자 요청 + 059 태스크 산출물 + 사전 분석 대화
> 출력: TASK.md

## 작업 목표

`sqlite-vec` 기반 로컬 벡터 스토어 도구(`opal/tools/vector-store/`)를 구현하고, OPAL 프레임워크 워크플로우(PM 디스패치 전 문서 선별, skill-registry 매칭, 메모리 검색)에 통합한다. Claude Code PostToolUse 훅으로 주요 파일 변경 시 자동 인덱싱도 지원한다.

## 배경

현재 OPAL PM은 작업 시작 시 `docs/PROJECT.md` 문서 테이블 전체를 수동으로 읽고 관련 문서를 선별한다. 프로젝트가 성장할수록 이 비용이 증가하고, 메모리 파일이 쌓일수록 관련 항목을 놓치는 리스크가 생긴다. 벡터 시맨틱 검색을 도입하면 자연어 쿼리로 관련 문서·메모리·스킬을 즉시 검색할 수 있다.

059 태스크(backup)에서 TASK + PLAN + QA-PLAN(Pass)까지 완료되었으나 EXECUTE가 보류된 상태다. 이번 태스크는 059 설계를 계승하되, 라이선스·통합·훅 설계를 보강하여 새로운 태스크로 진행한다.

## 배경 분석 (대화에서 도출)

### sqlite-vec vs sqlite-vector 비교 결론

| 항목 | sqlite-vec ✅ | sqlite-vector ❌ |
|------|-------------|----------------|
| 라이선스 | MIT / Apache-2.0 | Elastic License 2.0 (상용 SaaS 금지) |
| 인덱스 | HNSW (ANN, 대용량 유리) | 없음 (full scan) |
| 커뮤니티 | 활발 (SQLite 공식 추천) | 활발 |
| npm | `sqlite-vec` | `@sqliteai/sqlite-vector` |

→ **sqlite-vec 선택** (MIT 라이선스, OPAL 오픈소스·개인 사용 무제한)

### 벡터 DB 저장 방식

- **제목이 아닌 전체 내용을 청크 단위로 저장**
- 마크다운 헤딩 기준 1차 분할 → 1000자 초과 시 단락 단위 2차 분할
- 각 청크: `content`(실제 텍스트) + `embedding`(384차원 벡터) + `metadata`(파일경로, 청크번호, 헤딩)

### 네임스페이스 설계

```
~/.opal/vector.db
├── namespace: opal                ← OPAL 프레임워크 공통 (install 시 인덱싱)
│   ├── skills/*/SKILL.md
│   ├── agents/*/AGENT.md
│   ├── references/*.md            ← harness, pm, skills.md 등
│   └── tools/*/README.md (있으면)
│
└── namespace: {project-name}      ← 프로젝트별 (opi 초기화 또는 수동)
    ├── docs/                       ← PROJECT.md, ARCHITECTURE.md 등
    ├── tasks/*/TASK.md + STATE.md  ← 완료/진행중 모두 (DONE.md 제외)
    ├── .opal/memory/*.md
    └── .opal/AGENT.md
```

### 스킬 통합 포인트 (확정)

| 통합 대상 | 활용 방식 |
|----------|----------|
| `opal-pm.md §3 Step 2` | 작업 설명으로 관련 문서 자동 검색 → 수동 테이블 선별 보강 |
| `skill-registry` | `//` 키워드 매칭 실패 시 시맨틱 폴백 |
| MEMORY 브리핑 | 관련 메모리 자동 선택 (현재 수동 판단) |
| `op-task` TASK 작성 | 유사 이전 태스크 검색 → TASK.md 작성 참고 |

### 훅 연동 방향 (확정)

- Claude Code `PostToolUse(Write|Edit)` 훅으로 특정 경로 파일 변경 시 자동 인덱싱
- 대상 경로: `docs/*.md`, `.opal/memory/*.md`, `tasks/*/DONE.md`
- 전체 파일 변경에 걸면 부하 → 경로 패턴으로 대상 좁힘
- 읽기(디스패치 전 검색)는 훅보다 opal-pm.md 프로세스 내에서 명시적 호출 (투명성 우선)

## 확정된 설계 방향 (대화에서 합의)

1. **라이브러리**: `sqlite-vec` (MIT) — sqlite-vector 대체
2. **저장 단위**: 전체 문서 내용을 청크 분할하여 저장 (제목만 저장 X)
3. **네임스페이스**: `opal`(프레임워크 공통) + `{project-name}`(프로젝트별) 2계층
4. **tasks 인덱싱 범위**: TASK.md + STATE.md, 완료/진행중 모두 (DONE.md 제외 — 찾은 후 직접 읽으면 충분)
5. **Tool API**: CLI 명령 + `--json` 출력 플래그 (스킬·PM이 Bash로 파싱 가능)
6. **스킬 통합**: opal-pm.md §3 Step 2 보강 + skill-registry 폴백 추가
7. **훅 연동**: PostToolUse(Write|Edit) — 특정 경로 대상 자동 인덱싱
8. **install-mac.sh**: 의존성 설치 + `opal` 네임스페이스 초기 인덱싱 + 모델 프리로드
9. **런타임**: Python 우선 / Node.js 폴백 (059 설계 계승)
10. **임베딩**: `all-MiniLM-L6-v2` (384차원, ~22MB ONNX, 완전 로컬)

## 요구사항

### R1. vector-store 도구 구현

- [ ] `opal/tools/vector-store/` 디렉토리 신규 생성
  - **무엇을**: sqlite-vec 기반 벡터 스토어 CLI 도구 구현
  - **어디에**: `opal/tools/vector-store/` (소스) → `~/.opal/tools/vector-store/` (배포)
  - **왜**: OPAL 문서·메모리·스킬에 대한 시맨틱 검색 기반 제공
  - **AC**: `~/.opal/tools/vector-store/run.sh index --namespace test --dir ./docs` 실행 성공, `run.sh search --namespace test --query "아키텍처" --json` 출력이 유효한 JSON이며 results 배열 포함

- [ ] Python 구현 (우선): `vector-store.py`, `lib/db.py`, `lib/embedder.py`, `lib/chunker.py`, `lib/commands.py`, `requirements.txt`
  - **AC**: Python3 환경에서 index → search 전 과정 동작

- [ ] Node.js 폴백: `vector-store.js`, `lib/db.js`, `lib/embedder.js`, `lib/chunker.js`, `lib/commands.js`, `package.json`
  - **AC**: Python 없는 환경에서 Node.js로 동일 CLI 동작, Python 인덱싱 데이터와 상호 호환

- [ ] 런타임 디스패처: `run.sh` (Python3 → Node.js → 설치 안내)
  - **AC**: `run.sh` 실행 시 Python3 있으면 Python 호출, 없으면 Node.js 호출

### R2. CLI 명령 + JSON 출력

- [ ] 6개 명령 구현: `index`, `search`, `add`, `update`, `delete`, `status`
  - **AC**: 각 명령이 `--help`로 사용법 출력, `--json` 플래그 시 JSON 형식 출력

- [ ] `search --json` 출력 형식 준수
  - **AC**: `{"ok": true, "results": [{"score": 0.xx, "file": "...", "chunk": N, "content": "..."}]}`

- [ ] 에러 시 `{"ok": false, "error": "..."}`  출력
  - **AC**: DB 없음, 파일 없음 등 에러 상황에서 위 형식 반환

### R3. 네임스페이스 설계 구현

- [ ] `opal` 네임스페이스: skills/*/SKILL.md, agents/*/AGENT.md, references/*.md 인덱싱
  - **AC**: `index --namespace opal --dir ~/.opal` 실행 후 `search --namespace opal --query "워커 디스패치"` 시 opal-harness.md 또는 opal-pm.md 청크 반환

- [ ] `{project}` 네임스페이스: docs/, tasks/(TASK.md + STATE.md, 완료/진행중 모두), .opal/memory/ 인덱싱
  - **AC**: `index --namespace opal-project --dir ./docs` 후 검색 결과가 다른 네임스페이스와 혼재 없음

### R4. install-mac.sh 통합

- [ ] vector-store 의존성 설치 (Python venv 또는 npm)
  - **AC**: install-mac.sh 실행 후 `run.sh status` 정상 동작

- [ ] `opal` 네임스페이스 초기 인덱싱
  - **AC**: install-mac.sh 완료 후 `search --namespace opal --query "하네스"` 결과 반환

- [ ] 임베딩 모델 프리로드 (첫 실행 지연 방지)
  - **AC**: install-mac.sh 완료 후 첫 search 시 모델 다운로드 없이 즉시 응답

- [ ] PostToolUse 훅 설정 머지 (`claude-hooks.json` 또는 install-mac.sh 직접)
  - **AC**: `~/.claude/settings.json`에 PostToolUse 훅 항목 추가됨

### R5. opal-pm.md §3 통합

- [ ] Step 2 "관련 문서 선별" 에 벡터 검색 보강 절차 추가
  - **무엇을**: vector-store search 결과를 문서 선별에 활용하는 절차 명시
  - **어디에**: `opal/core/references/opal-pm.md` §3 Step 2
  - **왜**: 문서 테이블 수동 선별 보완, 문서 누락 방지
  - **AC**: §3 Step 2에 "vector-store 사용 가능 시" 조건부 검색 절차가 존재함

### R6. skill-registry 시맨틱 폴백

- [ ] skill-registry.js에 `--semantic` 폴백 모드 추가 또는 AGENT.md에 절차 명시
  - **무엇을**: `//` 커맨드 키워드 매칭 실패 시 vector-store search로 폴백하는 절차
  - **어디에**: `~/.opal/tools/skill-registry/skill-registry.js` 또는 `~/.opal/AGENT.md` 스킬 레지스트리 섹션
  - **왜**: 정확한 스킬명 모를 때도 자연어로 관련 스킬 탐색 가능
  - **AC**: AGENT.md 또는 skill-registry에 시맨틱 폴백 절차가 명시됨

## 제약 조건

- OPAL 프레임워크 소스 구조 준수: `opal/tools/` 소스 → `~/.opal/tools/` 배포
- 배포 행위 금지: install-mac.sh 실행은 캡틴이 수행 (소스만 수정)
- `~/.opal/` 경로 직접 편집 금지 (확정 기준 #2)
- 완전 로컬 동작: 외부 API 의존 없음
- macOS arm64 지원 필수 (캡틴 환경)
- 기존 `opal/tools/skill-registry/` 패턴 일관성 유지

## 기술 스택

- **벡터 DB**: sqlite-vec (MIT, SQLite 확장)
- **임베딩**: all-MiniLM-L6-v2 (384차원, ~22MB ONNX)
- **런타임**: Python 3 (sentence-transformers) 우선 / Node.js (@huggingface/transformers) 폴백
- **배포**: install-mac.sh

## 관련 문서

- `tasks/backup/059-opal-vector-store/` — 선행 태스크 (TASK + PLAN + QA-PLAN Pass)
- `opal/tools/skill-registry/skill-registry.js` — 기존 도구 패턴 참조
- `opal/core/references/opal-pm.md` — §3 통합 대상
- `opal/core/AGENT.md` — skill-registry 섹션 (폴백 절차 추가 대상)
- `scripts/install-mac.sh` — 배포 스크립트 수정 대상
- `docs/ARCHITECTURE.md` — 도구 구조 반영 대상
