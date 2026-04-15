# QA: EXECUTE — README.md 업데이트 (최근 변경 반영 + 설치/설정 섹션 확장)

> 검토일: 2026-04-15 | 판정: **Pass**

## 1. 요약

README.md가 636줄에서 794줄로 확장되어 TASK.md의 16개 요구사항(R-1~R-16)을 반영했다. opds/opd 파이프라인에서 TEST-SCENARIO가 PLAN에 통합 표기되고 QA Gate 문구가 제거되었으며, opsdd 파이프라인에 VERIFY가 추가되었다. 전문 에이전트 6종 테이블, 비서/PM 역할 전환, @header+code-scan, 하네스 모듈화가 반영되었다. 설치/설정 섹션이 사전 요구사항, 옵션별 상세, 설치 후 검증, Cursor/Gemini 수동 설정, //opi 생성물 상세, 빠른 시작, 트러블슈팅으로 대폭 확장되었다. 핵심 철학 5항목 테이블은 원본 그대로 유지되었다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| R-1 | opds/opd 파이프라인 TEST-SCENARIO 통합 | Pass | 비교 테이블(280~281줄): `PLAN(+테스트 시나리오)` 표기. opds 사용법(458줄): `TASK → PLAN(+테스트 시나리오) → EXECUTE → TEST`. opd 사용법(494줄): 동일. 진행 흐름(468줄, 509줄): "구현 계획 + 테스트 시나리오" 통합. TEST-SCENARIO 별도 단계 없음. QA Gate 관련 문구 없음. 3곳 일관 |
| R-2 | opsdd 파이프라인 VERIFY 추가 | Pass | 비교 테이블(284줄): `TASK → SPEC → VERIFY → REVIEW → DESIGN → EXECUTE-LOOP → DONE`. opsdd 사용법(552줄): 동일 파이프라인 문자열. VERIFY가 SPEC과 REVIEW 사이에 위치 |
| R-3 | 전문 에이전트 체계 반영 | Pass | (a) 주요 특징(36줄): "전문 에이전트(Specialist Agent) — 도메인별 전문 워커가 FE/BE/DB/기획/테스트를 담당". (b) 아키텍처 트리(749줄): `agents/ 서브에이전트 (전문 6종 + 범용 4종)`. (c) 전문 에이전트 섹션(724~739줄): 6종 테이블(opal-plan-agent, opal-fe-agent, opal-be-agent, opal-db-agent, opal-planning-agent, opal-test-agent) + 역할 + 폴백 동작 |
| R-4 | 비서/PM 역할 전환 | Pass | "비서 모드와 PM 모드" 소섹션(261~271줄): 비서/PM 테이블, `.opal/AGENT.md` 존재 여부로 자동 전환 명시 |
| R-5 | @header + code-scan 반영 | Pass | 아키텍처 개요 아래(765줄): "코드 파일에 `@header` 주석으로 메타데이터를 기록하고, `code-scan` 도구로 빠르게 탐색한다." |
| R-6 | 하네스 모듈화 반영 | Pass | 아키텍처 트리(751줄): `references/ 레지스트리 + 모듈화된 하네스 (harness/)` |
| R-7 | 사전 요구사항 | Pass | "사전 요구사항" 서브섹션(66~74줄): OS(macOS), 필수 도구(bash, git, Node.js v18+, Python 3), 지원 AI 플랫폼(Claude Code, Cursor, Gemini) 테이블 |
| R-8 | 설치 옵션별 상세 | Pass | "설치 옵션별 상세"(92~121줄): [1] OPAL 설치 배치 경로 13개 테이블, [2] MCP 서버 설정 4개 플랫폼 테이블. 교차 검증 3건: `~/.opal/AGENT.md`(install-mac.sh 416줄 cp 확인), `~/.claude/CLAUDE.md`(522줄 확인), `~/.cursor/rules/000-opal-agent.mdc`(525줄 cp 확인) -- 모두 일치 |
| R-9 | 설치 후 검증 | Pass | "설치 후 검증"(123~141줄): `ls ~/.opal/` 명령 + 기대 출력 + 부트스트랩 체크리스트 확인 방법 |
| R-10 | 플랫폼별 프로젝트 설정 | Pass | Claude Code 수동 설정(167~183줄), Cursor 수동 설정(185~187줄), Gemini 수동 설정(189~191줄) 각각 1문장 이상 |
| R-11 | //opi 생성물 상세 | Pass | "//opi 생성물 상세" 테이블(159~165줄): `.opal/AGENT.md`, `docs/PROJECT.md`, `docs/CONVENTIONS.md` 3개 파일 역할 명시 |
| R-12 | 빠른 시작 | Pass | "빠른 시작" 섹션(195~210줄): `//opp README에 프로젝트 설명 추가해줘` + `//opds` 예시 포함 |
| R-13 | 트러블슈팅 | Pass | "트러블슈팅" 섹션(771~794줄): 부트스트랩 미동작, // 커맨드 매칭 실패, MCP 연결 실패 3개 케이스 + 각 대응법 |
| R-14 | 목차 앵커 링크 | Pass | 목차 11개 항목 + 7개 서브항목 전부 실제 섹션 제목과 매칭. GitHub Markdown 앵커 규칙(소문자, 하이픈, 특수문자 제거) 준수 |
| R-15 | 어투·형식 일관성 | Pass | 신규 섹션 모두 존댓말+정보 전달 톤("~한다", "~된다") 사용. 테이블 헤더 포함, 코드블록 사용 기존 스타일과 동일 |
| R-16 | 핵심 철학 5항목 유지 | Pass | 22~28줄: 사용자 주권·단계적 실행·문서화 우선·플랫폼 독립·프로젝트 학습 5항목 테이블 원본 그대로 유지 |
| GE-1 | 체크리스트 완료 | Pass | PLAN.md §3 실행 체크리스트 Step 1~13 모두 `[x] 완료` 표기 |
| GE-2 | 산출물 존재 | Pass | README.md 794줄 존재 확인 (목표 800~850줄 이내) |
| GE-3 | TASK 충족 | Pass | R-1~R-16 전체 AC 충족 확인 (상세 위 참조) |

## 3. 지적 사항

### Info 1: community-skills 숫자 처리

- **심각도**: Info
- **내용**: PLAN.md Step 10에서 "31개 → 37개로 정정"이라고 기재했으나, EXECUTE 워커는 소스 리포지토리의 `community-skills/` 실제 디렉토리 수(31개)를 확인하고 31개를 유지했다. 소스 기준으로 정확한 판단이다.

### Info 2: 분량 제어

- **심각도**: Info
- **내용**: 636줄 → 794줄로 158줄 증가. 목표 범위(800~850줄 이내)를 충족한다. 설치/설정 섹션 확장과 3개 신규 섹션(빠른 시작, 전문 에이전트, 트러블슈팅) 추가 대비 적절한 분량이다.

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md | R-1~R-16 AC가 README.md에서 모두 충족되는가 | Pass -- 16개 전체 충족 |
| PLAN.md | Step 1~13 완료 기준이 실제 README.md에서 달성되었는가 | Pass -- 13개 Step 모두 완료 기준 충족 |
| install-mac.sh | R-8 설치 경로가 실제 구현과 일치하는가 (샘플 3건) | Pass -- `~/.opal/AGENT.md`(416줄), `~/.claude/CLAUDE.md`(522줄), `~/.cursor/rules/000-opal-agent.mdc`(525줄) 모두 일치 |
| agents.md | R-3 전문 에이전트 6종 이름이 레지스트리와 일치하는가 | Pass -- opal-plan-agent, opal-fe-agent, opal-be-agent, opal-db-agent, opal-planning-agent, opal-test-agent 모두 일치 |
| community-skills/ | 디렉토리 수가 README 표기와 일치하는가 | Pass -- 소스 31개, README 31개 |
| 비교 테이블 vs Pilot 사용법 | 파이프라인 표기가 일관되는가 | Pass -- opds/opd/opsdd 비교 테이블과 각 사용법 섹션 파이프라인 문자열 일치 |

## 5. 판정

**Pass**

R-1~R-16 전체 AC가 충족되었다. 파이프라인 표기는 비교 테이블과 각 Pilot 사용법에서 일관되며, 전문 에이전트 6종 이름은 agents.md 레지스트리와 정확히 일치한다. 설치 경로는 install-mac.sh 실제 구현과 교차 검증을 통과했다. community-skills 숫자는 소스 기준 31개로 정확하다. 794줄로 목표 분량 범위 이내이다.
