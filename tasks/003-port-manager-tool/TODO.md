# TODO: 프로젝트별 포트 매니저 CLI 도구 (r2-port)

> 작성일: 2026-03-09 | 참조: TASK.md, RESEARCH.md, PLAN.md

## Part A: 실행 체크리스트

> 총 5개 Step | 실행 모드: 단순

### Step 1: r2-port.sh CLI 전체 구현

- **파일**: `scripts/r2-port.sh`
- **작업 내용**:
  - 셸 스크립트 기본 구조 (set -euo pipefail, 컬러 출력, usage)
  - python3 존재 확인
  - 도메인 컨벤션: `{project}.{type}.local` 자동 생성
  - 프로젝트명 정규화: PascalCase/camelCase/snake_case/대문자/공백 → kebab-case 변환
  - `register <project-name> --type front|api|other [--project <path>]`
    - `~/ports.json` 조회 → 기존이면 기존 포트 반환, 없으면 빈 포트 탐색
    - 포트 범위: front 3000~3999, api 8000~8999, other 9000~9999
    - `lsof`로 사용 중 확인 + 레지스트리 내 중복 확인
    - `--port-only` 옵션: 포트 번호만 stdout 출력 (스크립트 연동용)
  - `list` — 전체 등록 도메인/포트 테이블 출력
  - `info <domain>` — 특정 도메인의 포트, 타입, URL 출력
  - `env <domain> [--port-only]` — PORT/BASE_URL 출력 또는 포트만 출력
  - `release <domain>` — 레지스트리에서 삭제
  - JSON 읽기/쓰기 (python3 인라인)
- **완료 기준**: 5개 명령어 모두 정상 동작, register → list → info → env → release 전체 흐름 확인
- **테스트**: 스크립트 직접 실행하여 전체 명령어 동작 확인
- **실행 방법**: direct
- **의존**: 없음
- **상태**: ⬜ 미실행 (보류)

### Step 2: /etc/hosts 마커 기반 관리 통합

- **파일**: `scripts/r2-port.sh`
- **작업 내용**:
  - `# === R2-PORT START ===` / `# === R2-PORT END ===` 마커 관리
  - register 시: 마커 영역에 `127.0.0.1\t<domain>` 추가 (마커 블록 없으면 생성)
  - release 시: 마커 영역에서 해당 도메인 라인 삭제
  - sudo 필요 — 실패 시 warn 출력 후 계속 진행
  - 변경 후 DNS 캐시 플러시 (`dscacheutil -flushcache && killall -HUP mDNSResponder`)
- **완료 기준**: register/release 시 /etc/hosts 마커 영역이 올바르게 업데이트됨
- **테스트**: register 후 `/etc/hosts` 확인, release 후 삭제 확인
- **실행 방법**: direct
- **의존**: Step 1
- **상태**: ⬜ 미실행 (보류)

### Step 3: install-mac.sh 연동

- **파일**: `scripts/install-mac.sh`
- **작업 내용**:
  - `show_menu()`에 `[6] r2-port (포트 매니저)` 추가
  - `install_r2port()` 함수: `scripts/r2-port.sh` → `~/.r2/bin/r2-port` 복사, chmod +x
  - PATH 처리: `~/.r2/bin`이 PATH에 없으면 `.zshrc`에 추가 여부 확인
  - `[5] 전체 설치`에 `install_r2port` 추가
  - 메뉴 범위 업데이트 (0-5 → 0-6)
- **완료 기준**: 메뉴 [6] 선택 시 r2-port 설치 완료
- **테스트**: install-mac.sh 실행 → [6] 선택 → `r2-port` 명령어 확인
- **실행 방법**: direct
- **의존**: Step 1
- **상태**: ⬜ 미실행 (보류)

### Step 4: port-mgr AI 스킬 작성

- **파일**: `claude/skills/port-mgr/SKILL.md`, `cursor/skills/port-mgr/SKILL.md`, `antigravity/skills/port-mgr/SKILL.md`
- **작업 내용**:
  - 스킬 트리거: 프로젝트 생성, 서버 설정, dev script 구성 시
  - r2-port register 호출 가이드
  - 프레임워크별 실행 스크립트 내장 패턴:
    - Next.js: package.json dev script에 r2-port 연동
    - FastAPI: run.sh에 r2-port 연동
    - 기타 프레임워크 범용 패턴
  - 수동 CLI 사용법 안내
  - 3개 플랫폼 동일 내용으로 작성
- **완료 기준**: AI가 프로젝트 셋업 시 이 스킬을 참조하여 r2-port를 자동 호출할 수 있음
- **테스트**: 스킬 YAML frontmatter 유효성, 내용 검토
- **실행 방법**: direct
- **의존**: Step 1
- **상태**: ⬜ 미실행 (보류)

### Step 5: 통합 테스트

- **파일**: 없음 (동작 검증)
- **작업 내용**:
  - 전체 시나리오 테스트: register → list → info → env → release
  - /etc/hosts 마커 영역 정상 동작 확인
  - 중복 register 시 기존 포트 반환 확인
  - 포트 충돌 회피 확인 (이미 사용 중인 포트 스킵)
- **완료 기준**: 전체 시나리오 통과
- **테스트**: 직접 실행
- **실행 방법**: direct
- **의존**: Step 1, 2, 3
- **상태**: ⬜ 미실행 (보류)

---

## Part B: QA 체크리스트

### B-1. 기능 테스트
- [ ] `r2-port register my-shop --type front` → `my-shop.front.local` 도메인 자동 생성
- [ ] `r2-port register MyShop --type api` → `my-shop.api.local` (kebab-case 정규화)
- [ ] camelCase/PascalCase/snake_case/대문자/공백 입력 모두 동일한 kebab-case로 변환
- [ ] 이미 등록된 도메인 재등록 시 기존 포트 반환
- [ ] `r2-port list`로 전체 목록 확인
- [ ] `r2-port info`로 개별 도메인 정보 확인
- [ ] `r2-port env`로 PORT/BASE_URL 출력
- [ ] `r2-port env --port-only`로 포트 번호만 출력
- [ ] `r2-port release`로 도메인 해제
- [ ] /etc/hosts에 R2-PORT 마커 영역 정상 관리
- [ ] 포트 범위(front 3000~3999, api 8000~8999) 준수
- [ ] AI 스킬이 프레임워크별 내장 패턴을 포함

### B-2. 회귀 테스트
- [ ] install-mac.sh 기존 메뉴(1~5) 정상 동작
- [ ] /etc/hosts 마커 영역 외 기존 내용 보존

### B-3. 코드 품질
- [ ] install-mac.sh의 기존 코딩 패턴(컬러 출력, 함수 네이밍) 준수
- [ ] r2-port.sh shellcheck 경고 없음
- [ ] 스킬 YAML frontmatter 형식 준수

### B-4. 보안
- [ ] sudo 처리 시 비밀번호가 로그에 노출되지 않음
- [ ] ports.json에 민감 정보 없음

---

## 보류 사유

> 🔒 2026-03-09 보류 결정
> 다중 머신 환경(개인 맥북, 회사 맥북, 개발 서버 등)에서 머신별 독립 관리가 필요하여
> 중앙 포트 레지스트리의 실효성이 낮다고 판단. 추후 필요 시 재개.
