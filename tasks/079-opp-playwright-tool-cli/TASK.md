# TASK: playwright-tool CLI 구현 + wtm 스킬 연동

> 작성일: 2026-04-03 | 작업 유형: 신규+개선 | 적용 스킬: opp | 모드: interactive
> 입력: 사용자 요청
> 출력: playwright-tool CLI, wtm SKILL.md 수정, 비교 검토 문서

## 작업 목표

Playwright를 MCP가 아닌 독립 CLI 툴로 래핑하여 OPAL 툴로 등록하고, wtm 스킬의 `--browser` 모드가 MCP 대신 CLI 툴을 호출하도록 변경한다. 이를 통해 복수 URL 처리 시 에이전트별 독립 브라우저 인스턴스로 진정한 병렬 처리를 가능하게 한다.

## 배경

### 현재 문제
- Playwright MCP: 단일 서버 프로세스 = 단일 브라우저 → 에이전트 여러 개가 동일 브라우저 공유
- 복수 URL + browser 모드 시 에이전트 병렬 디스패치 불가 (탭 충돌, 탭 전환 경쟁)
- wtm 스킬이 browser 모드에서 MCP에 의존하여 순차 수집만 가능

### 해결 방향
- Playwright가 이미 `~/.opal/.venv`에 설치되어 있음
- CLI 툴로 래핑하면 각 Bash 호출이 독립 프로세스 → 독립 브라우저 → 진짜 병렬 처리
- xlsx-tool 패턴과 동일한 구조로 OPAL 툴 등록

### 멀티탭 방식 검토
- 동일 브라우저 내 탭 분리 방식도 후보로 검토
- PLAN 단계에서 멀티브라우저 vs 멀티탭 비교 분석 포함

## 요구사항

### playwright-tool CLI
- [ ] `opal/tools/playwright-tool/main.py` — Python CLI 구현
  - 인자: `URL`, `--mode {full|clean}`, `--output {파일경로}`
  - 동작: navigate → 콘텐츠 추출 → MD 정제 → stdout 또는 파일 저장
  - headless 실행, 타임아웃 30초
- [ ] `opal/tools/playwright-tool/run.sh` — 래퍼 스크립트 (xlsx-tool 패턴)
  - `~/.opal/.venv/bin/python` 경로 사용
  - JSON 출력: `{"ok": true, "path": "...", "content": "..."}` 또는 `{"ok": false, "error": "..."}`
- [ ] playwright 직접 설치 여부 체크 로직 포함 (venv 경로 확인)

### wtm SKILL.md 수정
- [ ] `--browser` 모드: Playwright MCP 대신 `playwright-tool` CLI 호출로 변경
- [ ] 단일 URL + browser 모드: CLI 직접 호출 (브라우저 1개)
- [ ] 복수 URL + browser 모드: 에이전트 병렬 디스패치 허용 (각자 CLI 호출 → 독립 브라우저)
  - 기존 "PM 직접 순차 수집" 조건에서 browser 모드 제외
- [ ] playwright 설치 체크: MCP 체크 → CLI 체크로 교체 (venv 설치 확인)
- [ ] Phase 1 실패 시 Phase 2 폴백: MCP → CLI 호출로 변경

### 비교 검토
- [x] PLAN.md에 멀티브라우저 vs 멀티탭 비교 분석 포함
  - 속도, 리소스, 구현 복잡도, 격리 수준, 실용성 관점

### 배포 동기화
- [ ] `scripts/install-mac.sh`에 playwright-tool 배포 경로 추가
  - `opal/tools/playwright-tool/` → `~/.opal/tools/playwright-tool/`

## 제약 조건

- Python 실행 환경: `~/.opal/.venv/bin/python` (고정)
- playwright 패키지: 이미 venv에 설치됨 (`playwright installed` 확인)
- run.sh 출력 형식: JSON (`{"ok": bool, ...}`) — xlsx-tool 패턴 일치
- 배포 파일 직접 수정 금지 (`~/.opal/` 경로 직접 편집 불가)
- install-mac.sh 동기화 필수 (배포 구조 = 소스 구조)
- wtm SKILL.md는 `skills/web-to-markdown/SKILL.md` (프로젝트 소스)

## 기술 스택

- Python (playwright-sync API 또는 playwright-async)
- Playwright (`~/.opal/.venv` 설치됨)
- Bash (run.sh 래퍼)
- Markdown (wtm 산출물)

## 관련 문서

- `skills/web-to-markdown/SKILL.md` — 수정 대상
- `opal/tools/xlsx-tool/` — 패턴 참조
- `scripts/install-mac.sh` — 배포 경로 추가 대상
- `opal/core/references/opal-harness.md` — 도구 우선 원칙 §8
