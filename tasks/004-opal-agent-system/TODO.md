# OPAL AI 에이전트 시스템 — 실행 체크리스트

> 작성일: 2026-03-09 | 작성자: R2 | 버전: v1.0

## Part A: 복잡도 판별

- **파일 수**: 신규 9 + 수정 2 + 삭제 3 = 총 14개
- **작업 유형**: 문서 작성 + 스크립트 수정
- **판정**: 단순 (메인 에이전트 직접 실행)

## Part B: 실행 체크리스트

### Step 1: 소스 구조 생성

- [x] `templates/opal/bootstrapper/` 디렉토리 생성
- [x] `templates/opal/core/` 디렉토리 생성
- [x] `templates/opal/skills/onboarding/` 디렉토리 생성
- [x] `templates/opal/skills/project-init/` 디렉토리 생성
- [x] `templates/opal/skills/orchestrator/` 디렉토리 생성
- [x] `templates/opal/templates/` 디렉토리 생성

### Step 2: 에이전트 코어 작성

- [x] `templates/opal/core/AGENT.md` 작성
  - 부트스트랩 절차 (identity.md 로드, 온보딩 트리거)
  - 정체성 적용 규칙 (identity.md 필드 매핑)
  - 핵심 역할 (AI 개인 비서, 프로젝트 오케스트레이터)
  - 행동 규칙 (주도성, 보고 형식)
  - 스킬 참조 (플랫폼 스킬 + OPAL 전용 스킬)
- [x] `templates/opal/core/identity-template.md` 작성
  - YAML frontmatter 필드 정의
  - Markdown body 템플릿

### Step 3: 부트스트래퍼 작성

- [x] `templates/opal/bootstrapper/claude-bootstrap.md` 작성
  - 스니핏 형식 (```markdown 펜스 포함)
  - CLAUDE.md 마커 삽입용
- [x] `templates/opal/bootstrapper/cursor-bootstrap.mdc` 작성
  - YAML frontmatter (alwaysApply: true)
  - OPAL AGENT.md Read 지시
- [x] `templates/opal/bootstrapper/gemini-bootstrap.md` 작성
  - 스니핏 형식 (```markdown 펜스 포함)
  - GEMINI.md 마커 삽입용

### Step 4: OPAL 전용 스킬 작성

- [x] `templates/opal/skills/onboarding/SKILL.md` 작성
  - YAML frontmatter (name, description)
  - 인터뷰 프로세스 (Round 1 필수 + Round 2 선택)
  - identity-template.md 기반 identity.md 생성 절차
  - 확인 및 완료 보고
- [x] `templates/opal/skills/project-init/SKILL.md` 작성
  - 프로젝트 구조 분석 절차
  - project-agent.md 템플릿 기반 생성
  - {프로젝트}/.opal/AGENT.md 저장
- [x] `templates/opal/skills/orchestrator/SKILL.md` 작성
  - 프로젝트 에이전트 AGENT.md Read
  - 서브에이전트(Task 도구) 호출 절차
  - Antigravity 대안 (동일 컨텍스트 실행)
  - 결과 검토 및 보고

### Step 5: 프로젝트 에이전트 템플릿

- [x] `templates/opal/templates/project-agent.md` 작성
  - 프로젝트 개요 섹션 (이름, 스택, 구조)
  - 프로젝트 규칙 섹션 (컨벤션, 브랜치, 테스트)
  - 작업 수행 규칙

### Step 6: install-mac.sh 수정

- [x] OPAL 마커 상수 추가 (`OPAL_START`, `OPAL_END`)
- [x] `install_opal_section` 함수 작성 (R2 + OPAL 마커 하위 호환)
- [x] `install_opal` 함수 작성
  - 부트스트래퍼 3개 설치 (Claude 마커, Cursor 파일복사, Antigravity 마커)
  - `~/.opal/` 디렉토리에 core + skills + templates 설치
- [x] 기존 `install_r2` → `install_opal`로 교체
- [x] 메뉴 [4] 라벨 변경: "R2 알투" → "OPAL (AI 에이전트)"
- [x] `print_summary` 업데이트 (`~/.opal/` 경로 추가)

### Step 7: CLAUDE.md 업데이트

- [x] 프로젝트 루트 `CLAUDE.md`의 R2 관련 설명을 OPAL로 업데이트
  - 소스 구조 설명에서 `templates/r2/` → `templates/opal/`
  - 배포 구조에 `~/.opal/` 추가
  - 컴포넌트 설명에 OPAL 에이전트 추가

### Step 8: 기존 R2 파일 삭제

- [x] `templates/r2/000-r2-persona.mdc` 삭제
- [x] `templates/r2/claude-snippet.md` 삭제
- [x] `templates/r2/gemini-snippet.md` 삭제
- [x] `templates/r2/` 디렉토리 삭제 (비어있으면)

### 완료 검증

- [x] `templates/opal/` 구조 확인 (9개 파일)
- [x] `templates/r2/` 삭제 확인
- [x] `scripts/install-mac.sh` 문법 오류 없음 (bash -n)
- [x] CLAUDE.md 일관성 확인

| 버전 | 날짜 | 작성자 | 변경내용 |
|------|------|--------|---------|
| v1.0 | 2026-03-09 | R2 | 최초 작성 — 8단계 실행 체크리스트 |
