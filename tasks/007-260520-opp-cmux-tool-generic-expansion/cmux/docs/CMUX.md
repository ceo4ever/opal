---
@header {
  "module": "cmux-guide",
  "layer": "reference",
  "domain": "dev-tool",
  "description": "cmux(AI 코딩 에이전트용 macOS 터미널) MAMS 통합 환경 가이드 — 워크플로우·설정·단축키·예시·로그 분석",
  "exports": ["설치-및-초기-설정", "workspace-surface-split-표준-구성", "필수-단축키", "서버-자동-기동", "내장-브라우저", "알림-연동", "예시-워크플로우", "로그-분석", "트러블슈팅"],
  "depends": ["batch-guide", "project"]
}
---

# cmux MAMS 통합 가이드

> **이 문서의 섹션 태그**  
> `[MAMS 전용]` — MAMS 특화 설정·포트·명령 (프레임워크 승격 시 프로젝트별 파일로 분리)  
> `[일반]` — cmux 범용 사용법 (승격 시 `~/.opal/cmux/docs/`로 이동 가능)  
> `[MAMS+일반]` — 혼합 (MAMS 예시 + 일반 개념 병행)

CLI 레퍼런스·Socket API·hooks 레시피 상세 → [CMUX-TOOLS.md](./CMUX-TOOLS.md)

---

## 1. 설치 및 초기 설정 [일반]

### 1-1. cmux 설치

```bash
# Homebrew (권장)
brew install manaflow-ai/tap/cmux

# 또는 GitHub Releases에서 DMG 다운로드
# https://github.com/manaflow-ai/cmux/releases
```

<!-- 실제 사용 시 'cmux --version' 으로 설치 확인 권장 -->

### 1-2. Ghostty 설정 예시 적용 [MAMS 전용]

MAMS용 Ghostty 설정 샘플을 수동으로 복사·적용한다.

```bash
# 기존 설정 백업 후 적용 (전역 파일은 워커/스크립트가 수정하지 않음)
cp ~/.config/ghostty/config ~/.config/ghostty/config.bak
cp .opal/cmux/config/ghostty.config.sample ~/.config/ghostty/config
```

샘플에 포함된 주요 설정:
- `font-family = D2Coding Nerd Font` — 한글 지원 Nerd Font
- `theme = GruvboxDark`
- `cursor-style = block`
- MAMS 친화 키바인딩 (`⌘⇧↵` 전체화면 등)

### 1-3. cmux.json 팔레트 로드 [MAMS 전용]

루트 `cmux.json`은 `.opal/cmux/config/cmux.json`의 심볼릭 링크다.
cmux는 프로젝트 루트의 `cmux.json`을 자동 인식한다.

```bash
# 심볼릭 링크 확인
ls -l cmux.json
# → cmux.json -> .opal/cmux/config/cmux.json

# 팔레트 명령 팔레트: ⌘P (또는 cmux 설정의 command-palette 단축키)
```

팔레트에 `MAMS:` 접두어 명령 15개가 표시된다.  
→ 자세히: [CMUX-TOOLS.md §1](./CMUX-TOOLS.md#1-cli-명령-레퍼런스)

---

## 2. Workspace/Surface/Split 표준 구성 [MAMS 전용]

### 2-1. 단위 개념

| 단위 | 설명 | 예시 |
|------|------|------|
| **Workspace** | 프로젝트/브랜치 단위 | `mams-main`, `mams-feature-xxx` |
| **Surface/Tab** | 역할 단위 | `be`, `fe`, `batch` |
| **Split Pane** | 프로세스 단위 | 서버 프로세스 + 브라우저 분할 |

### 2-2. MAMS Surface 표준 세트

| ⌘ 키 | Surface 이름 | 역할 | 포트/경로 |
|------|-------------|------|----------|
| ⌘1 | `pm-claude` | Claude Code 대화 창 | — |
| ⌘2 | `be` | FastAPI 백엔드 서버 | `8000` |
| ⌘3 | `fe` | Next.js 프론트엔드(본) | `3000` |
| ⌘4 | `fe-wire` | Next.js 와이어프레임(참조용) | `3001` |
| ⌘5 | `fe-test` | Next.js 테스트 빌드 | `3002` |
| ⌘6 | `batch` | Airflow Docker 배치 | `8080` |
| ⌘7 | `db` | DB 콘솔 / 마이그레이션 | — |
| ⌘8 | `ops` | 기타 운영 명령 | — |

<!-- ⌘1~8 숫자 키 Surface 이동은 cmux 버전에 따라 다를 수 있음 — 'cmux --help'로 검증 권장 -->

### 2-3. 기동 방법 요약

```bash
# 전체 기동 (BE + FE + Batch)
bash .opal/cmux/scripts/start-all.sh

# 와이어프레임도 함께 기동
bash .opal/cmux/scripts/start-all.sh --with-wire

# 개별 기동
bash .opal/cmux/scripts/open-dev.sh be
bash .opal/cmux/scripts/open-dev.sh fe
```

---

## 3. 필수 단축키 가이드 [일반]

<!-- 아래 단축키는 cmux 기본값 기준이며, 버전에 따라 달라질 수 있음. 'cmux --help'로 검증 권장 -->
<!-- → 자세히: CMUX-TOOLS.md §2 단축키 전체 목록 -->

| 단축키 | 동작 |
|--------|------|
| `⌘P` | 커맨드 팔레트 열기 (MAMS 명령 검색) |
| `⌘T` | 새 Surface/탭 생성 |
| `⌘W` | 현재 Surface 닫기 |
| `⌘⇧L` | 브라우저 좌우 분할 오픈 |
| `⌘1`~`⌘8` | Surface 이동 |
| `⌘⇧←→` | Split Pane 간 이동 |
| `⌘⇧↵` | 전체화면 전환 (Ghostty 설정 필요) |
| `⌘K` | 현재 pane 클리어 |
| `⌘C` | 복사 |
| `⌘V` | 붙여넣기 |

→ 자세히: [CMUX-TOOLS.md §2](./CMUX-TOOLS.md#2-단축키-레퍼런스)

---

## 4. 서버 자동 기동 — 스크립트·팔레트·레시피 [MAMS 전용]

### 4-1. BE (FastAPI)

| 방식 | 명령 |
|------|------|
| **스크립트** | `bash .opal/cmux/scripts/open-dev.sh be` |
| **팔레트** | `MAMS: Start BE dev` |
| **수동** | `cd workspace/backend && uv run uvicorn app.mams.main:mams_app --reload --port 8000` |

로그: `.opal/cmux/logs/be-YYYYMMDD-HHMM.log`

### 4-2. FE (Next.js 본)

| 방식 | 명령 |
|------|------|
| **스크립트** | `bash .opal/cmux/scripts/open-dev.sh fe` |
| **팔레트** | `MAMS: Start FE dev` |
| **수동** | `cd workspace/frontend && pnpm dev` |

로그: `.opal/cmux/logs/fe-YYYYMMDD-HHMM.log`

### 4-3. FE 와이어프레임

| 방식 | 명령 |
|------|------|
| **스크립트** | `bash .opal/cmux/scripts/open-dev.sh fe-wire` |
| **팔레트** | `MAMS: Start FE wireframe` |
| **수동** | `cd workspace/frontend_wireframe && pnpm dev --port 3001` |

### 4-4. FE 테스트

| 방식 | 명령 |
|------|------|
| **스크립트** | `bash .opal/cmux/scripts/open-dev.sh fe-test` |
| **팔레트** | `MAMS: Start FE test` |
| **수동** | `cd workspace/frontend_test && pnpm dev --port 3002` |

### 4-5. Batch (Airflow Docker)

| 방식 | 명령 |
|------|------|
| **스크립트** | `bash .opal/cmux/scripts/open-dev.sh batch` |
| **팔레트** | `MAMS: Start Batch (Airflow)` |
| **기동** | `cd workspace/backend && docker compose -f docker-compose.airflow.yml up -d` |
| **중지** | `cd workspace/backend && docker compose -f docker-compose.airflow.yml down` |
| **로그 follow** | `docker compose -f docker-compose.airflow.yml logs -f airflow-apiserver` |

**Airflow 비밀번호 확인 절차**:
```bash
# 팔레트로 실행
MAMS: Show Airflow password

# 또는 직접 실행
cd workspace/backend && docker compose -f docker-compose.airflow.yml exec airflow-apiserver \
  cat /opt/airflow/simple_auth_manager_passwords.json.generated
```

> UI: `http://localhost:8080` (admin/admin 기본값 또는 위 파일 참조)

### 4-6. 전체 일괄 기동·종료

```bash
# 일괄 기동
bash .opal/cmux/scripts/start-all.sh
# 또는 팔레트: MAMS: Start All

# 일괄 종료
bash .opal/cmux/scripts/stop-all.sh
# 또는 팔레트: MAMS: Stop All
```

---

## 5. 내장 브라우저 활용 패턴 [MAMS+일반]

<!-- cmux browser 서브커맨드는 버전에 따라 달라질 수 있음 — 'cmux browser --help'로 검증 권장 -->
<!-- → 자세히: CMUX-TOOLS.md §3 브라우저 CLI 전체 목록 -->

### 5-1. Swagger (BE API 문서)

```bash
# 팔레트
MAMS: Open Swagger

# 직접 명령 (cmux browser open-split --help로 플래그 검증 권장)
cmux browser open-split http://localhost:8000/docs
```

### 5-2. Next.js FE 개발 서버

```bash
# 팔레트
MAMS: Open Next dev

# 직접 명령
cmux browser open-split http://localhost:3000
```

### 5-3. Airflow UI

```bash
# 팔레트
MAMS: Open Airflow UI

# 직접 명령
cmux browser open-split http://localhost:8080
```

### 5-4. Wireframe 좌우 비교 [MAMS 전용]

```bash
# 팔레트 (워크스페이스 레이아웃 자동 설정)
MAMS: Open wireframe compare

# 수동: FE 본(3000) + 와이어프레임(3001) 동시 오픈
cmux browser open-split http://localhost:3000
# 우측 분할은 cmux browser open-split 또는 ⌘⇧L 단축키 활용
```

### 5-5. 브라우저 A/B/C 분기 자동 탐지 [MAMS 전용]

```bash
# test-browser.sh로 기존 브라우저 상태 자동 탐지 후 분기
bash .opal/cmux/scripts/test-browser.sh http://localhost:3000/register

# 비대화 환경: 분기 강제 지정
CMUX_BROWSER_DECISION=B bash .opal/cmux/scripts/test-browser.sh http://localhost:3000/register
```

---

## 6. 알림 연동 [일반]

→ 자세히: [CMUX-TOOLS.md §4](./CMUX-TOOLS.md#4-claude-code-hooks-레시피)

### 6-1. cmux notify 기본 사용

```bash
# 기본 알림 (--title/--subtitle/--body 공식 플래그)
cmux notify --title "Claude Code" --subtitle "MAMS" --body "Response ready"

# cmux notify --help 로 플래그 검증 권장
```

### 6-2. Claude Code hooks 적용

`.claude/settings.local.json`에 hooks가 이미 등록되어 있다.
샘플 파일을 비교·재적용할 경우:

```bash
# 샘플 확인
cat .opal/cmux/config/claude-hooks.sample.json

# 직접 settings.local.json 편집 (기존 hooks 보존 필수)
# → 반드시 jq 또는 수동으로 병합할 것. 덮어쓰기 금지.
```

등록된 hooks 이벤트:
- `Stop` — Claude 응답 완료 시 알림
- `Notification` — 권한 요청 대기 시 알림  
- `PreCompact` — 컨텍스트 압축 임박 시 알림

---

## 7. 예시 워크플로우 [MAMS 전용]

### 7-A. 사용자 등록 E2E 브라우저 테스트

**시나리오**: 신규 사용자 등록 폼 제출 흐름을 브라우저 자동화로 테스트한다.

**Step 1 — 기존 브라우저 감지**

```bash
# pane 목록 조회
cmux list-panes

# 현재 브라우저 URL 조회
cmux browser url
# → 출력 예: http://localhost:3000/dashboard
```

**Step 2 — A/B/C 분기 결정**

| 상황 | 판단 | 동작 |
|------|------|------|
| 브라우저 없음 | B안 | `cmux browser open-split http://localhost:3000/register` |
| 동일 도메인 + 대기 중 | A안 | `cmux browser navigate http://localhost:3000/register` |
| 동일 도메인 + 작업 중 | C안 | 별도 test Surface 생성 |

자동 처리:
```bash
bash .opal/cmux/scripts/test-browser.sh http://localhost:3000/register
```

**Step 3 — 브라우저 자동화 (Socket API / CLI 사용)**

```bash
# 페이지 스냅샷 (Accessibility tree)
cmux browser snapshot

# 폼 입력 (cmux browser fill --help로 selector 형식 검증 권장)
cmux browser fill "#email" "test@example.com"
cmux browser fill "#password" "Test1234!"

# 제출 버튼 클릭
cmux browser click "#submit-btn"

# 결과 대기
cmux browser wait "#success-message"

# 최종 스냅샷
cmux browser snapshot
```

**Socket JSON-RPC 예시** (직접 소켓 통신):
```bash
# browser.fill 예시 (Socket API — 런타임 검증 권장)
echo '{"jsonrpc":"2.0","method":"browser.fill","params":{"selector":"#email","value":"test@example.com"},"id":1}' \
  | nc -U /tmp/cmux.sock
```

<!-- Socket API browser.* 네임스페이스 존재 여부는 런타임 'echo ...|nc -U /tmp/cmux.sock' 검증 권장 -->

---

### 7-B. FE 화면 개발 (wireframe 좌우 비교)

**시나리오**: 와이어프레임을 참조하며 본 FE 화면을 개발한다.

```bash
# 1. FE(본) + FE-wire Surface 동시 기동
bash .opal/cmux/scripts/open-dev.sh fe
bash .opal/cmux/scripts/open-dev.sh fe-wire

# 2. 좌우 브라우저 비교 (팔레트 사용)
# 팔레트: MAMS: Open wireframe compare
# → FE 본 (localhost:3000) + 와이어프레임 (localhost:3001) 동시 오픈

# 3. 또는 직접 명령
cmux browser open-split http://localhost:3000
# 두 번째 창 (⌘⇧L 또는 별도 surface)
cmux browser open-split http://localhost:3001
```

개발 중 실시간 확인:
- BE 서버가 실행 중이어야 API 응답이 정상 렌더링됨
- FE HMR(Hot Module Replacement)이 작동하므로 저장 즉시 브라우저 갱신
- `cmux browser snapshot`으로 현재 화면 상태를 알투가 분석 가능

---

### 7-C. 매체 API 테스트 (Swagger)

**시나리오**: 새 매체 API Endpoint를 Swagger UI로 검증한다.

```bash
# 1. BE Surface 기동
bash .opal/cmux/scripts/open-dev.sh be

# 2. Swagger 브라우저 분할 오픈
cmux browser open-split http://localhost:8000/docs
# 또는 팔레트: MAMS: Open Swagger

# 3. 특정 API 스크롤 (Socket API 사용)
cmux browser navigate "http://localhost:8000/docs#/매체명/endpoint_path"

# 4. 스냅샷으로 현재 상태 파악
cmux browser snapshot

# 5. 로그 확인
bash .opal/cmux/scripts/analyze-log.sh be --minutes 5
```

---

## 8. 로그 분석 워크플로우 [MAMS 전용]

### 8-1. 로그 파일 구조

```
.opal/cmux/logs/
├── be-20260418-1230.log       # FastAPI uvicorn 출력
├── fe-20260418-1230.log       # Next.js pnpm dev 출력
├── fe-wire-20260418-1230.log  # 와이어프레임 출력
├── fe-test-20260418-1230.log  # 테스트 빌드 출력
├── batch-20260418-1230.log    # Airflow 로그
└── .gitkeep
```

파일 형식: `{surface}-YYYYMMDD-HHMM.log` (서버 기동 시 tee로 자동 생성)

### 8-2. analyze-log.sh 사용법

```bash
# 기본 사용 (BE 최신 로그, 최근 500라인 분석)
bash .opal/cmux/scripts/analyze-log.sh be

# 팔레트
MAMS: Analyze BE log (last 5 min)

# FE 로그 분석
bash .opal/cmux/scripts/analyze-log.sh fe --minutes 10

# Batch 로그 분석
bash .opal/cmux/scripts/analyze-log.sh batch
```

출력 섹션:
1. `== Recent ERRORs ==` — ERROR/CRITICAL 레벨 라인
2. `== Tracebacks ==` — Traceback/Exception 포함 라인
3. `== Structlog events ==` — FastAPI structlog JSON의 `event` 필드

### 8-3. E2E 실패 시 상관 분석 예시

E2E 테스트 실패 시 BE + FE 로그를 동시에 분석한다:

```bash
# BE 로그 분석
bash .opal/cmux/scripts/analyze-log.sh be

# 같은 시각대 FE 로그 분석
bash .opal/cmux/scripts/analyze-log.sh fe

# Airflow 배치 관련이면 batch 로그도 확인
bash .opal/cmux/scripts/analyze-log.sh batch
```

상관 분석 포인트:
- BE의 `ERROR`/`Traceback` 시각 ↔ FE의 API 호출 실패 시각 매칭
- structlog `event` 필드에서 요청 경로·메서드·status_code 확인
- 네트워크 오류(ConnectionRefusedError)는 서버 기동 여부 재확인

---

## 9. 트러블슈팅 [MAMS+일반]

### 9-1. Airflow 비밀번호를 모를 때

```bash
# 팔레트로 확인
MAMS: Show Airflow password

# 또는 직접
cd workspace/backend && docker compose -f docker-compose.airflow.yml exec airflow-apiserver \
  cat /opt/airflow/simple_auth_manager_passwords.json.generated

# admin/admin 기본값 시도 (초기 설치 직후 동작 가능)
```

### 9-2. 포트 충돌

| 포트 | 서비스 | 충돌 해결 |
|------|--------|----------|
| `8000` | FastAPI BE | `lsof -i :8000` → PID kill |
| `3000` | Next.js FE 본 | `lsof -i :3000` → PID kill |
| `3001` | FE 와이어프레임 | `lsof -i :3001` → PID kill |
| `3002` | FE 테스트 | `lsof -i :3002` → PID kill |
| `8080` | Airflow | `docker compose down` 또는 `lsof -i :8080` |

### 9-3. cmux 소켓 연결 안 될 때

```bash
# 소켓 파일 존재 확인
ls -la /tmp/cmux.sock

# nightly 버전은 경로가 다름
ls -la /tmp/cmux-nightly.sock

# CMUX_SOCKET_PATH 환경변수로 경로 지정
export CMUX_SOCKET_PATH=/tmp/cmux-nightly.sock
```

### 9-4. 심볼릭 링크 확인

```bash
ls -l cmux.json
# → cmux.json -> .opal/cmux/config/cmux.json

readlink cmux.json
# → .opal/cmux/config/cmux.json

# 링크 재생성 (깨진 경우)
rm cmux.json && ln -s .opal/cmux/config/cmux.json cmux.json
```

### 9-5. 세션 복원 한계

cmux 세션 복원 시 레이아웃·디렉토리·스크롤백은 복원되지만  
**라이브 프로세스(서버·Docker·Claude)는 복원되지 않는다.**

재기동 방법:
```bash
bash .opal/cmux/scripts/start-all.sh
# 또는 팔레트: MAMS: Start All
```

### 9-6. 로그 디스크 팽창 방지 (선제 대응)

```bash
# 7일 이상 된 로그 삭제 (수동)
find .opal/cmux/logs -name "*.log" -mtime +7 -delete

# 향후 개선: logrotate 또는 cron으로 자동화 권장 (별도 태스크)
```
