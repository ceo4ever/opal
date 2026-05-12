# TASK: wtm-agent OPAL 표준화 + cmux 통합 + 사용자 surface 재사용

> 작성일: 2026-05-12 | 작업 유형: 개선 | 적용 스킬: opp | 모드: semi-agentic
> 입력: 캡틴 발화 + 대화 누적 결정 10건
> 출력: TASK.md

## 작업 목표

`wtm-agent`를 OPAL 프레임워크 표준 워커 구조로 완전 통합하고, cmux browser를 Phase 2 폴백으로 추가하며, 사용자가 열어둔 cmux 브라우저 surface를 재사용해 마크다운으로 변환할 수 있는 인터페이스(3모드)를 도입한다.

## 배경

- `wtm-agent`가 `agents/` 루트 직속에 있어 OPAL 표준 위치(`opal/agents/opal-*-agent/`)와 불일치하며, 이름 컨벤션(`opal-{name}-agent`)에서도 벗어남.
- `skills/web-to-markdown/SKILL.md` v1.7에서 Phase 2 백엔드를 Crawl4AI → playwright-tool CLI로 교체했으나 `agents/wtm-agent/AGENT.md` 본문/frontmatter 및 `opal/core/references/agents.md` 등록 정보가 여전히 Crawl4AI로 명시되어 3곳 부정합 발생 — 디스패치 시 워커가 잘못된 백엔드 안내를 따를 위험.
- 캡틴이 cmux 터미널 환경에서 자주 작업하지만 web-to-markdown은 cmux 통합 부재 — 사용자 세션을 활용한 인증/SPA 페이지 변환이 어려움.
- 캡틴이 이미 열어둔 cmux 브라우저 페이지(예: 광고 관리 페이지)를 알투가 함께 분석하는 협업 시나리오 미지원.

## 배경 분석 (대화에서 도출)

### wtm-agent OPAL 표준 적합도 (12항목)

| 항목 | 현 상태 | 평가 |
|------|---------|------|
| 위치 | `agents/wtm-agent/` (루트 직속) | ❌ |
| 네이밍 | `wtm-agent` (prefix 없음) | ❌ |
| Phase 2 백엔드 | Crawl4AI (구버전) | ❌ SKILL.md v1.7 부정합 |
| wireframe 모드 인지 | 없음 (full/clean만) | ❌ SKILL.md v1.3 미반영 |
| browser 모드 인지 | 없음 | ❌ SKILL.md v1.4-1.5 미반영 |
| OPAL Tools 호출 절차 | Crawl4AI Python 직접 호출 안내 | ❌ `~/.opal/tools/{tool}/run.sh` 표준 위배 |
| 실행 프로세스 구조 | 자체 정의 Phase 1/2 | △ 표준 7단계 구조 미준수 |
| 결과 반환 형식 | 자유 형식 | △ JSON 표준 비준수 |
| SKILL.md 자체 Read 절차 | 없음 (프로세스 하드코딩) | △ 동기화 부담 누적 |
| 변경이력 | 없음 | △ |
| model 매핑 | `light` | ✅ |
| color/icon | `green` / 🌐 | ✅ |

### cmux 0.64.3 실측 결과

| 항목 | 결과 |
|------|------|
| 바이너리 | `/Applications/cmux.app/Contents/Resources/bin/cmux` |
| 환경 감지 신호 | `$CMUX_SURFACE_ID` (UUID) — 가장 안정적 단일 조건 |
| 핸들 반환 | `cmux browser open <url>` stdout: `OK surface=surface:N pane=pane:M placement=split` |
| 본문 추출 | `eval --script "document.documentElement.outerHTML"` (selector 무관) 또는 `get html --selector <css>` |
| 메타 추출 | `get title`, `get url` (selector 불필요) |
| 로드 대기 | `wait --load-state complete --timeout-ms <ms>` |
| cleanup | `<surface> tab close` (workspace 정보 불필요) |
| naver.com 테스트 | 315,209 bytes HTML 정상 추출 |
| 사용자 surface 재사용 | short ref(`surface:3`) / UUID 둘 다 cross-workspace 접근 정상 |
| 미해소 1건 | `cmux browser` 서브에 `--workspace` 옵션 부재 — `cmux browser open` 시 `--workspace $CMUX_WORKSPACE_ID` 명시 권고 |

### 발견된 부정합 3건

| # | 위치 | 현 상태 | 정합 대상 |
|---|------|---------|----------|
| 1 | `agents/wtm-agent/AGENT.md` frontmatter description | "Phase 2(Crawl4AI)" | playwright-tool CLI |
| 2 | `agents/wtm-agent/AGENT.md` 본문 Phase 2 섹션 | Crawl4AI Python 호출 전체 절차 | playwright-tool CLI 호출 |
| 3 | `opal/core/references/agents.md` L218 | "Phase 2(Crawl4AI) 폴백" | "Phase 2(cmux, 조건부) → Phase 3(playwright-tool CLI)" |

## 확정된 설계 방향 (대화에서 합의)

1. **개선 범위: 옵션 A 완전 표준화** — 위치 이동 + 이름 변경 + 디스패치 프로세스 표준화 + JSON 결과 반환
2. **Phase 폴백 체인 재정의**: Phase 1 WebFetch → Phase 2 cmux(조건부) → Phase 3 playwright-tool CLI
3. **cmux 환경 감지**: `[[ -n "$CMUX_SURFACE_ID" ]] && command -v cmux >/dev/null 2>&1`
4. **cmux 미설치 시**: 설치 안내(공식 사이트 + GitHub 링크) 출력 후 Phase 3로 폴백
5. **cmux-tool 신규 도구**: `~/.opal/tools/cmux-tool/run.sh` 래퍼 (URL 모드 + surface 모드 통합)
6. **사용자 surface 재사용 3모드**:
   | 모드 | 호출 | navigate | cleanup |
   |------|------|----------|---------|
   | A. 신규 (기본) | `<url>` | 새 surface 생성 + open | ✅ 알투가 close |
   | B. 현재 페이지 | `--surface <handle>` | 안 함 | ❌ 사용자 surface 유지 |
   | C. surface 재사용 + navigate | `--surface <handle> <url>` | 해당 surface goto | ❌ 사용자 surface 유지 |
7. **`--wait <ms>` 옵션**: 사용자 제어, 기본값 2000ms, 0 명시 시 wait 생략
8. **사용자 surface cleanup 절대 금지** — B/C 모드 안전 가드
9. **SKILL.md 호출 인터페이스 확장**: `//wtm --surface <handle>`, `//wtm --surface <handle> {url}`, `--wait <ms>`
10. **Crawl4AI 부정합 3건 동시 해소**

## 요구사항

- [x] **R-1. opal-wtm-agent 신규 작성**
  - 무엇을: 표준 디스패치 프로세스(opal-task-agent 7단계 구조) + JSON 결과 형식의 AGENT.md 작성
  - 어디에: `opal/agents/opal-wtm-agent/AGENT.md`
  - 왜: 확정 방향 §1 (옵션 A 완전 표준화), [MUST] `.opal/AGENT.md` §PM 검토 기준: "컴포넌트 구조가 표준화 체계(스킬·에이전트·하네스)와 정합한가"
  - AC: 파일이 `opal/agents/opal-wtm-agent/AGENT.md`에 존재 / frontmatter `name: opal-wtm-agent` + `model: light` / 실행 프로세스가 opal-task-agent와 동일 7단계 구조 / 결과 반환 JSON 5필드(`artifact_path`, `summary`, `status`, `blockers`, `changed_files`) 명시

- [x] **R-2. 기존 wtm-agent 삭제**
  - 무엇을: `agents/wtm-agent/` 폴더 제거 + 모든 참조 새 경로로 갱신
  - 어디에: 프로젝트 루트 + 참조 문서(`docs/PROJECT.md`, `docs/CONVENTIONS.md`, `docs/ARCHITECTURE.md`, `opal/skills/opal-agent-creator/SKILL.md`)
  - 왜: 확정 방향 §1, 중복 제거 + SSOT 일관성
  - AC: `agents/wtm-agent/` 폴더 미존재 / `grep -rln "wtm-agent" --include="*.md"` 결과에 잔존 참조 0건(변경이력/history 예외) 또는 모두 `opal-wtm-agent`로 갱신

- [x] **R-3. cmux-tool 래퍼 신규**
  - 무엇을: cmux browser 호출을 캡슐화한 bash 래퍼 스크립트
  - 어디에: `opal/tools/cmux-tool/run.sh`
  - 왜: 확정 방향 §5, [MUST] `opal-harness.md` §9 OPAL Tools: "OPAL 도구는 모두 `~/.opal/tools/{tool-name}/run.sh` 래퍼를 통해 호출한다"
  - AC: 실행 가능(`chmod +x`) / 입력 인터페이스 `run.sh <url> [--mode <full|clean|wireframe>] [--wait <ms>]` + `run.sh --surface <handle> [<url>] [--mode] [--wait]` 모두 지원 / JSON 출력 `{"ok": true|false, "content": "...", "title": "...", "final_url": "...", "method": "cmux"}` / 신규 모드(A)에서만 cleanup 수행, B/C 모드에서는 close 명령 호출 안 함(스크립트 grep으로 검증)

- [x] **R-4. cmux 환경 감지 + 미설치 안내**
  - 무엇을: cmux 환경 진입 조건과 미설치 시 설치 안내 메시지 표준화
  - 어디에: `opal/tools/cmux-tool/run.sh` + `skills/web-to-markdown/SKILL.md` Phase 2 섹션
  - 왜: 확정 방향 §3·§4
  - AC: `$CMUX_SURFACE_ID` 미존재 시 cmux Phase 자동 건너뛰기 + Phase 3로 폴백 / `$CMUX_SURFACE_ID` 존재 + `cmux` 미설치 시 설치 안내(다운로드 URL `https://cmux.com/` + GitHub `https://github.com/manaflow-ai/cmux`) 출력 후 Phase 3로 폴백 / 정상 cmux 환경에서는 Phase 2 진입

- [x] **R-5. Phase 폴백 체인 재정의**
  - 무엇을: 실행 흐름을 1→2(cmux 조건부)→3 구조로 갱신
  - 어디에: `skills/web-to-markdown/SKILL.md` "실행 흐름" + "Phase 1" + "Phase 2"(신규 cmux) + "Phase 3"(playwright-tool CLI로 리네임) 섹션
  - 왜: 확정 방향 §2
  - AC: 흐름도에 3단계 명시 / 각 Phase별 성공/실패 판정 기준 명시 / `--browser` 모드 분기도 cmux/playwright 우선순위 일치

- [x] **R-6. 사용자 surface 재사용 3모드 지원**
  - 무엇을: A/B/C 3가지 입력 모드 + cleanup 가드 + read-only 안전 규칙
  - 어디에: `opal/tools/cmux-tool/run.sh` + `opal/agents/opal-wtm-agent/AGENT.md` + `skills/web-to-markdown/SKILL.md` 호출 인터페이스 섹션
  - 왜: 확정 방향 §6·§8, 캡틴-알투 협업 브라우저 시나리오
  - AC: `run.sh --surface <handle>` 시 navigate 안 함 + cleanup 없음 / `run.sh --surface <handle> <url>` 시 navigate 후 cleanup 없음 / `run.sh <url>` 시 새 surface + cleanup / 사용자 surface는 어떤 경우에도 `tab close` 호출 안 함 (스크립트 정적 검증)

- [x] **R-7. --wait 옵션**
  - 무엇을: wait 시간을 ms 단위로 지정할 수 있는 옵션, 기본 2000ms
  - 어디에: `opal/tools/cmux-tool/run.sh` + `skills/web-to-markdown/SKILL.md` 호출 인터페이스
  - 왜: 확정 방향 §7
  - AC: `--wait 5000` 명시 시 5초 대기 / 미명시 시 2000ms 기본 / `--wait 0` 명시 시 wait 생략

- [x] **R-8. SKILL.md Phase 절차 + 호출 인터페이스 갱신**
  - 무엇을: 실행 흐름 + 호출 인터페이스 섹션 + Phase 1/2/3 사양 + 추출 모드 + 의존성 + 변경이력 갱신
  - 어디에: `skills/web-to-markdown/SKILL.md`
  - 왜: 확정 방향 §2·§9, SSOT 정합
  - AC: 호출 인터페이스에 `//wtm --surface <handle>`, `//wtm --surface <handle> {url}`, `--wait <ms>` 예시 포함 / Phase 2 cmux + Phase 3 playwright-tool CLI로 명시 / Phase 2 cmux 사양 섹션 신규(명령 시퀀스 5단계 포함) / 변경이력에 v1.9 행 추가(2026-05-12, 태스크 002)

- [x] **R-9. Crawl4AI 부정합 3건 해소**
  - 무엇을: AGENT.md frontmatter description + 본문 Phase 2 섹션 + agents.md 등록 정보를 모두 playwright-tool CLI 기반으로 갱신
  - 어디에: `opal/agents/opal-wtm-agent/AGENT.md` (신규 작성 시) + `opal/core/references/agents.md` §wtm-agent
  - 왜: SSOT 정합, 확정 방향 §10
  - AC: 전체 코드베이스에서 `grep -rln "Crawl4AI"` 검색 시 web-to-markdown 관련 잔존 0건(변경이력 행 예외 허용)

- [x] **R-10. opal/core/references/agents.md 등록 갱신**
  - 무엇을: wtm-agent 섹션을 opal-wtm-agent로 갱신 (이름, 위치, Phase 폴백 체인, 입출력 명세)
  - 어디에: `opal/core/references/agents.md` §wtm-agent
  - 왜: 레지스트리 SSOT (확정 방향 §1·§2)
  - AC: 섹션명 `opal-wtm-agent` / 호출 시점에 Phase 1→2→3 명시 / 입력에 `url|--surface`, `mode`, `--wait` 옵션 명시 / 출력 JSON 형식 명시

- [x] **R-11. install-mac.sh cmux-tool 등록**
  - 무엇을: cmux-tool을 install 어댑터에 추가
  - 어디에: `scripts/install-mac.sh`
  - 왜: 배포 어댑터 의무, [MUST] `.opal/AGENT.md` §PM 검토 기준: "부트스트래퍼·MCP 등 배포 영향 항목이 install 스크립트에 반영되었는가"
  - AC: install-mac.sh가 `opal/tools/cmux-tool/` → `~/.opal/tools/cmux-tool/` 복사 / 실행 권한 부여(`chmod +x`) / 정상 설치 시 cmux 의존성 안내 메시지 출력 / 재실행 시 멱등(idempotent)

- [x] **R-12. 변경이력 추가**
  - 무엇을: 변경된 파일에 변경이력 행 추가 (KST 타임스탬프 + 태스크 002)
  - 어디에: `skills/web-to-markdown/SKILL.md` 변경이력 표 + `opal/agents/opal-wtm-agent/AGENT.md` 신규 변경이력 표 + `opal/core/references/agents.md`(있을 경우)
  - 왜: 추적성, [MUST] `.opal/AGENT.md` §업무 수행 지침: "문서 변경이력: 스킬·에이전트·참조 문서 수정 시 변경이력 표에 행을 추가한다 (일시 KST + 태스크 번호 포함)"
  - AC: web-to-markdown SKILL.md에 v1.9 행 (2026-05-12 + 002) / opal-wtm-agent AGENT.md에 v1.0 행 (2026-05-12 + 002)

- [x] **R-13. 사용자 surface 추출 안전 가드**
  - 무엇을: B/C 모드 결과 보고에 저장 경로 + 민감 정보 경고 표시
  - 어디에: `opal/agents/opal-wtm-agent/AGENT.md` 안전 규칙 섹션 + `skills/web-to-markdown/SKILL.md` Phase 2 사용자 surface 모드 사양
  - 왜: 확정 방향 surface 재사용 안전 가드, 인증 세션 기반 추출 결과는 민감 정보 포함 가능
  - AC: B/C 모드 실행 결과 보고에 저장 경로 명시 / "사용자 세션 기반 추출 — 민감 정보 포함 가능, 외부 공유 시 검토 필요" 안내 포함 / 사용자 surface 핸들이 명시되지 않은 경우 B/C 모드 진입 거부

## 제약 조건

- [MUST] `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다." → 모든 변경은 프로젝트 소스(`opal/`, `skills/`, `agents/`, `scripts/`)에 작성, 배포는 install-mac.sh로
- [MUST] `opal-harness.md` §1 Guards: "사용자가 명시적으로 '승인', '진행해', '구현해' 등의 실행 허가를 내릴 때까지 코드를 작성하거나 파일을 생성/수정하지 않는다."
- [MUST] 사용자 surface cleanup 절대 금지: B/C 모드에서 `tab close` 호출 안 함 — 스크립트 정적 검증으로 보장
- 기존 web-to-markdown 호출 패턴 하위 호환 유지: 단일 URL 호출, full/clean/wireframe 모드, `--browser` 플래그 모두 정상 동작
- cmux 의존성은 외부 도구 — install 어댑터에서 등록 가능 여부만 점검, cmux 자체 설치는 사용자 책임
- 플랫폼 분기 어댑터 경계: install-mac.sh만 수정 (Linux/Windows 어댑터는 본 태스크 범위 외)
- `cmux browser` 서브에는 `--workspace` 옵션 부재 — `cmux browser open` 호출 시 `--workspace $CMUX_WORKSPACE_ID` 명시

## 기술 스택

- Markdown, YAML (문서 + frontmatter)
- Bash (cmux-tool 래퍼 + install-mac.sh)
- Node.js (date 도구 활용, install-mac.sh 검증)
- cmux 0.64.3+ (외부 의존성, 선택)
- playwright-tool CLI (기존 의존성)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | opal-harness.md | `opal/core/references/opal-harness.md` | §1 Guards / §6 모델 매핑 / §9 OPAL Tools 표준 |
| D-2 | 설계 | agents.md | `opal/core/references/agents.md` | wtm-agent 레지스트리 등록 정보 (L216-221) |
| D-3 | 설계 | web-to-markdown SKILL.md | `skills/web-to-markdown/SKILL.md` | v1.8 현행 Phase 구조 + 호출 인터페이스 |
| D-4 | 설계 | wtm-agent AGENT.md (현행) | `agents/wtm-agent/AGENT.md` | 삭제 대상 — 마이그레이션 원본 |
| D-5 | 설계 | opal-pm.md | `opal/core/references/opal-pm.md` | §11 프로젝트 전문 에이전트 관리 |
| D-6 | 설계 | header-rules.md | `opal/core/references/harness/header-rules.md` | @header 규칙 (코드 파일 변경 시) |
| D-7 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | 산출물 인용 규칙 |
| D-8 | 외부 | cmux Browser Automation 문서 | [cmux docs](https://cmux.com/ko/docs/browser-automation) | cmux 브라우저 자동화 명령 사양 |
| D-9 | 외부 | cmux GitHub | [manaflow-ai/cmux](https://github.com/manaflow-ai/cmux) | 설치 안내 링크 |
| D-10 | 소스 | install-mac.sh | `scripts/install-mac.sh` | OPAL Tools 배포 어댑터 |
| D-11 | 소스 | opal-task-agent AGENT.md | `opal/agents/opal-task-agent/AGENT.md` | 표준 워커 구조 참조 모델 |
| D-12 | 소스 | opal-be-agent AGENT.md | `opal/agents/opal-be-agent/AGENT.md` | 표준 워커 구조 참조 모델 (도메인별) |
| D-13 | 설계 | .opal/AGENT.md | `.opal/AGENT.md` | PM 검토 기준 + 금지사항 + 업무 수행 지침 |
| D-14 | 설계 | docs/PROJECT.md | `docs/PROJECT.md` | wtm-agent 참조 경로 갱신 대상 |
| D-15 | 설계 | docs/CONVENTIONS.md | `docs/CONVENTIONS.md` | wtm-agent 참조 경로 갱신 대상 |
| D-16 | 설계 | docs/ARCHITECTURE.md | `docs/ARCHITECTURE.md` | wtm-agent 참조 경로 갱신 대상 |
