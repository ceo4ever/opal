# PLAN: 프로젝트별 포트 매니저 CLI 도구 (r2-port)

> 작성일: 2026-03-09 | 참조: TASK.md, RESEARCH.md

## 1. 구현 범위

### 신규 생성 파일

| # | 파일 경로 | 역할 |
|---|----------|------|
| 1 | `scripts/r2-port.sh` | 포트 매니저 CLI 스크립트 |
| 2 | `claude/skills/port-mgr/SKILL.md` | AI 스킬 — 프로젝트 셋업 시 포트 등록 가이드 |
| 3 | `cursor/skills/port-mgr/SKILL.md` | (2번과 동일 내용, Cursor용) |
| 4 | `antigravity/skills/port-mgr/SKILL.md` | (2번과 동일 내용, Antigravity용) |

### 수정 파일

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `scripts/install-mac.sh` | r2-port 설치 메뉴 [6] 추가, `install_r2port()` 함수 |

## 2. 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | r2-port.sh CLI 전체 구현 | `scripts/r2-port.sh` | 중 |
| 2 | /etc/hosts 마커 기반 관리 통합 | `scripts/r2-port.sh` | 중 |
| 3 | install-mac.sh 연동 | `scripts/install-mac.sh` | 하 |
| 4 | port-mgr AI 스킬 작성 | `*/skills/port-mgr/SKILL.md` | 하 |

## 3. 핵심 설계

### 3.1 도메인 네이밍 컨벤션

```
{프로젝트명}.front.local    ← 프론트엔드 서버
{프로젝트명}.api.local      ← API 서버
{프로젝트명}.{type}.local   ← 기타
```

프로젝트명은 입력 형태와 무관하게 **kebab-case로 정규화**한다:

| 변환 규칙 | 입력 → 출력 |
|----------|------------|
| PascalCase | `MyShop` → `my-shop` |
| camelCase | `myShopApp` → `my-shop-app` |
| snake_case | `my_shop` → `my-shop` |
| 대문자 | `MY-SHOP` → `my-shop` |
| 공백 | `My Shop` → `my-shop` |
| 연속 하이픈 | `my--shop` → `my-shop` |

예시:
- `r2-port register MyShop --type front` → `my-shop.front.local` → 포트 3001
- `r2-port register myShop --type api` → `my-shop.api.local` → 포트 8001

### 3.2 r2-port CLI (`scripts/r2-port.sh`)

**명령어 인터페이스:**

```
r2-port register <project-name> --type front|api|other [--project <path>]
r2-port list
r2-port info <project-name>.<type>.local
r2-port env <project-name>.<type>.local
r2-port release <project-name>.<type>.local
```

- `register`는 프로젝트명 + type으로 도메인을 자동 생성: `{project}.{type}.local`
- `info`, `env`, `release`는 전체 도메인으로 지정

**레지스트리 (`~/ports.json`):**

```json
{
  "my-shop.front.local": {
    "port": 3001,
    "type": "front",
    "project": "/path/to/my-shop",
    "created": "2026-03-09"
  },
  "my-shop.api.local": {
    "port": 8001,
    "type": "api",
    "project": "/path/to/my-shop",
    "created": "2026-03-09"
  }
}
```

**포트 할당 로직:**

1. `~/ports.json`에 도메인이 있으면 기존 포트 반환
2. 없으면 type별 범위에서 빈 포트 탐색:
   - front: 3000~3999
   - api: 8000~8999
   - other: 9000~9999
3. `lsof -i :PORT -sTCP:LISTEN -t`로 사용 중 확인 + 레지스트리 내 중복 확인
4. 빈 포트 발견 시 레지스트리에 저장

**JSON 처리:** Python 인라인 스크립트 (python3/python fallback, 크로스 플랫폼)

### 3.3 /etc/hosts 마커 관리

R2 설치 방식과 동일한 마커 패턴:

```
# === R2-PORT START ===
127.0.0.1	my-shop.front.local
127.0.0.1	my-shop.api.local
# === R2-PORT END ===
```

- **register**: 마커 영역에 도메인 추가 (없으면 마커 블록 신규 생성)
- **release**: 마커 영역에서 도메인 삭제 (마커는 유지)
- sudo 실패 시 warn 출력 후 계속 진행 (포트 할당은 정상 동작)
- 변경 후 `dscacheutil -flushcache && killall -HUP mDNSResponder`

### 3.4 port-mgr AI 스킬

AI가 프로젝트 셋업/서버 구성 시 참조하는 가이드:

**트리거**: 새 프로젝트 생성, 서버 설정, dev script 작성 시

**스킬 내용:**
1. `r2-port register`로 도메인+포트 등록
2. 프레임워크별 실행 스크립트에 내장하는 패턴:

```jsonc
// Next.js — package.json
{
  "scripts": {
    "dev": "r2-port register my-shop --type front --project $(pwd) && next dev --port $(r2-port env my-shop.front.local --port-only)"
  }
}
```

```bash
# FastAPI — run.sh
PORT=$(r2-port register my-shop --type api --project $(pwd) --port-only)
uvicorn main:app --host 0.0.0.0 --port $PORT
```

3. 수동 등록/해제 CLI 안내

### 3.5 install-mac.sh 연동

- `show_menu()`에 `[6] r2-port (포트 매니저)` 추가
- `install_r2port()` 함수: `scripts/r2-port.sh` → `~/.r2/bin/r2-port` 복사 + 실행 권한
- PATH 안내: `~/.r2/bin`이 PATH에 없으면 셸 프로파일 추가 여부 확인

## 4. 의존성 및 환경 변경

| 항목 | 내용 |
|------|------|
| python3 | macOS 기본 포함 — 추가 설치 불필요 |
| PATH | `~/.r2/bin` 추가 필요 (설치 시 자동 처리 또는 안내) |

## 5. 테스트 전략

| 테스트 | 방법 |
|--------|------|
| register → list 확인 | 도메인 등록 후 list에 표시되는지 |
| 도메인 자동 생성 | `register my-shop --type api` → `my-shop.api.local` |
| 중복 register | 같은 도메인 재등록 시 기존 포트 반환 |
| release → list 확인 | 해제 후 목록에서 사라지는지 |
| env 출력 | PORT, BASE_URL 형식이 올바른지 |
| 포트 충돌 회피 | 이미 사용 중인 포트를 건너뛰는지 |

## 6. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| sudo 거부 | /etc/hosts 등록 실패 | 포트 할당은 정상 동작, hosts만 수동 안내 |
| python3 미설치 | JSON 처리 불가 | 시작 시 확인, 없으면 안내 후 종료 |
| ports.json 수동 편집 오류 | 파싱 실패 | 에러 핸들링 + 백업 안내 |
