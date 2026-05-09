# TASK: opi 프로젝트 초기화

- 모드: 초기화 (기존)
- 시작일시: 2026-05-08 17:43
- 완료일시: 2026-05-08 21:43
- 상태: 완료

## 배경

OPAL 프레임워크 자체 개발 저장소. tasks/ 운영 + 다른 태스크들이 PM 모드 가정으로 진행 중이지만 `.opal/AGENT.md`가 부재하여 PM 모드가 비활성 상태였음. 후속 태스크 139(P1: 배포 채널 정비 + Get Started UX 통합) 진입 전 PM 환경부터 갖추기 위해 opi 진행.

> 채번 이력: 최초 17:44 시점 137번으로 채번했으나, 별도 세션이 16:50에 137을 선점한 사실이 확인되어 138로 시프트.

## 사전 분석 (Phase 1 Step A/B)

### 레이아웃 탐색
- 코드 디렉토리: `opal/tools/` (Python + Node 혼재)
- 문서 디렉토리: `docs/`
- 태스크 디렉토리: `tasks/`
- 자산 디렉토리: `agents/`, `cursor-rules/`, `scripts/`, `skills/`, `community-skills/`, `opal/{agents,bootstrapper,core,skills,templates}` (모두 Markdown 자산)

### 기술 스택
- `opal/tools/requirements.txt` → Python (Playwright, MCP 의존성)
- `opal/tools/check-env.js` → Node.js 환경 점검 (단일 스크립트, package.json 없음)
- 본체: Markdown + YAML + Bash + Node + Python 혼재

### 프로젝트 카테고리
- **일반 프로젝트** (코드 디렉토리는 도구 1개뿐, 본체는 Markdown 자산)
- 기존 `docs/PROJECT.md`의 "프로젝트 구성" 단일 요소 "Framework" 분류 그대로 유효

## 인터뷰 결과 (초기화 기존, 2문)

| Q | 답변 |
|---|------|
| Q1/2. 이 프로젝트는 어떤 목적으로 사용되나요? | "AI 환경에서 IT 프로젝트를 체계적으로 수행하기 위한 범용 AI 개발 프레임워크" — 기존 `docs/PROJECT.md` 첫 줄 그대로 |
| Q2/2. 분석 결과 외에 추가로 담을 내용이 있나요? | (b) 팀 컨벤션/규칙 + (c) 외부 연동/의존 서비스 — 알투가 분석해서 직접 정리 |

## 산출물

| 파일 | 작업 | 핵심 변경 |
|------|------|------|
| `.opal/AGENT.md` | **신규** | PM 프로필 — AI 프레임워크 설계 전문가 + 도메인 검토 6항목 + 금지사항 6종(`~/.opal/` 직접 편집 금지 등) |
| `docs/CONVENTIONS.md` | 갱신 | "구현 규칙" 섹션 신설 — Guards / 디스패치 의무 / @header / Citation Rules / State / 도구 우선 / 변경이력 / 배포 경계 / 플랫폼 분기 격리 (8개 절) |
| `docs/ARCHITECTURE.md` | 갱신 | "외부 의존 서비스" 섹션 신설 — MCP 서버 5종 + Anthropic Claude API + Python venv + Node.js + 배포 채널(예정) |
| `docs/PROJECT.md` | 미세 갱신 | 프로젝트 문서 테이블에 `.opal/MEMORY.md` 등록 + `CONVENTIONS.md` 용도 라인 보강 |
| `.opal/MEMORY.md` | 갱신 | 138 (opi 완료) 행 추가 + `last_task_number=138` |

## 백업

```
docs/backup/PROJECT_202605081743.md
docs/backup/ARCHITECTURE_202605081743.md
docs/backup/CONVENTIONS_202605081743.md
```

## 부트스트래퍼 점검

| 파일 | OPAL 마커 |
|------|----------|
| `CLAUDE.md` | ✅ 정상 |
| `GEMINI.md` | ✅ 정상 |
| `.cursorrules` | ✅ 정상 |

## 후속 태스크

- **139 (P1)**: 배포 채널 정비 + Get Started UX 통합 — `opal` CLI 단일 진입점 (`install`/`update`/`doctor`/`uninstall`/`mcp`) + `install.sh`/`install.ps1` + 부트스트랩 a/b 분기 + `//start` 슬래시 스킬 + README 정제 + GitHub Release Workflow (mac+linux+win+release 통합)

## 결함 회고

- TASK 진입 직전 `.opal/MEMORY.md` 작업 히스토리 재조회 누락 — 별도 세션의 137 선점을 인지하지 못해 중복 채번 발생. 후속 PM Gate 검증 항목으로 "TASK 채번 직전 MEMORY 재조회"를 추가 권장.
