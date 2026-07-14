# TASK: OPAL Console 브레인 프라임 연결 풀 — 지정 프로젝트 선프라임 + 새 대화 웜 핸들 배정

> 작성일: 2026-07-13 | 작업 유형: 신규 | 적용 스킬: opd | 모드: agentic
> 입력: 사용자 요청 (2026-07-13 대화 — 프라임 연결 풀 구상 + 설계 방향 합의)
> 출력: TASK.md

## 작업 목표

OPAL Console 백엔드에 브레인 프라임 연결 풀을 신설한다 — 지정 프로젝트를 서버 기동 시 선프라임하여 풀에 등록하고, 새 대화 시작 시 웜 핸들을 즉시 배정하여 첫 질의의 콜드 대기(실측 약 56초)를 웜 수준(수초대)으로 단축한다.

## 배경

현재 대시보드 브레인 질의는 대화(conversation)별 콜드 프라임을 사용자가 대화를 시작한 시점에 수행한다. 콜드 프라임은 claude CLI 부트스트랩 로드를 포함해 실측 약 56초가 소요되어(`dashboard/backend/adapters/opbr_adapter.py` @header "콜드 ~56s"), 새 대화의 첫 질의 체감 대기가 길다. prime-on-intent(브레인 UI 진입 시 백그라운드 프라임)가 있으나, 사용자가 대화를 여는 즉시 질의하는 흐름에서는 여전히 콜드 대기가 발생한다.

## 배경 분석 (대화에서 도출)

- 059 태스크에서 `conversation_id`(FE 대화 키)와 `_claude_session_id`(BE 발급 claude 핸들)가 분리됨 — `dashboard/backend/adapters/brain_session.py:87-89`. 풀에서 미리 프라임한 웜 핸들을 새 대화 세션에 주입하는 것이 구조적으로 성립한다.
- 웜 핸들이 주입되면 첫 질의는 기존 `ask()`의 웜 분기(`--resume`)를 그대로 탄다 — `brain_session.py:260-273`. ask 분기 로직 변경 불요.
- 프라임 1회 = 사용자 Claude 구독 실호출 1회 — API 키 금지, 로컬 `claude -p` 구독 인증 (메모리 `console-brain-subscription-auth`, `opbr_adapter.py` @header "[MUST] --safe-mode·--bare·anthropic SDK·API 키 절대 금지").
- 세션은 `cwd=project_path`로 프로젝트별 격리됨 — `opbr_adapter.py:175`. 풀은 프로젝트 단위로 격리되어야 한다.
- `console.config.json`은 `opal-cli console scan`이 생성·머지하며, 백엔드는 읽기 전용 소비 — `dashboard/backend/config.py:34-38`. scan 머지 스크립트는 미지정 키를 보존하므로(`opal/tools/opal-cli/lib/console.sh:196-232` — data 로드 후 scan_roots만 갱신) 새 키 추가가 안전하다.
- `main.py`에 기동 훅(lifespan/startup) 부재 — `dashboard/backend/main.py` 전체에 startup 훅 없음. 신설 필요.
- 브레인 검색은 질의 시점에 `brain-tool search`로 수행되므로 오래 대기한 웜 핸들의 지식 신선도(stale) 위험은 낮다 — 별도 TTL 재프라임 불요 판단.

## 확정된 설계 방향 (대화에서 합의)

1. **지정 프로젝트만 선프라임** — `console.config.json`에 지정한 프로젝트에 한해 서버 기동 시 선프라임한다 (구독 사용량 통제, 캡틴 1안).
2. **풀 크기 기본 1** — 프로젝트당 웜 핸들 1개를 유지한다.
3. **체크아웃 + 백그라운드 리필** — 새 대화가 풀 핸들을 가져가면(체크아웃) 백그라운드로 새 프라임을 수행해 풀을 다시 채운다 (캡틴 3안).
4. **동시 프라임 상한 1~2** — 기동 시 다중 프로젝트 프라임·연속 리필이 몰려도 동시 실행을 제한한다.
5. **lock 하 체크아웃** — 새 대화 2개가 동시에 같은 풀 항목을 집지 않도록 lock으로 pop한다.
6. **TTL 재프라임 불요** — stale 위험이 낮으므로 풀 항목의 주기적 재프라임은 하지 않는다 (비용 대비 불요).
7. **FE 변경 불요** — 기존 prime/status/query API 계약을 유지하고, BE 내부에서 풀 체크아웃을 우선 적용한다.

## 명확화 결과

> TASK 4요소를 잠근다. 각 요소는 확정값 또는 명시적 "N/A: <사유>"로 채운다 (공란·TBD 금지).

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | 지정 프로젝트 선프라임 풀 신설로 새 대화 첫 질의를 콜드(~56s)에서 웜(수초대)으로 단축 | - | `opbr_adapter.py` @header 콜드 실측 |
| 범위 | 포함: BE 4파일(`config.py`·`brain_session.py`·`main.py`·`routers/brain.py`) + config 스키마 키 신설 + 테스트. 제외: FE 변경, opal-cli scan 변경, TTL 재프라임, install 배포 스크립트 변경(배포는 기존 update 경로 재사용) | - | 확정 설계 방향 §7 |
| 제약 | API 키·SDK 금지(구독 `claude -p`만), 프로젝트별 cwd 격리 유지, 기존 API 계약 불변, backend 무상태 원칙(Q&A 영속 금지 — 세션 핸들만 인메모리), 동시 프라임 상한, `~/.opal/` 직접 수정 금지(프로젝트 소스만) | - | `opbr_adapter.py`·`brain_session.py` @header [MUST] |
| 완료기준 | 아래 요구사항 AC 전체 Pass + 단위테스트 GREEN + 실기동 검증(지정 프로젝트 선프라임 로그 + 새 대화 웜 배정 확인) | - | TEST-SCENARIO 단계 |

## 요구사항

- [ ] **F-1 config 확장** — 무엇을: `console.config.json`에 `prewarm_projects`(프로젝트 절대경로 배열, 기본 `[]`) 키를 파싱하는 필드 추가 / 어디에: `dashboard/backend/config.py` `ConsoleConfig`·`load_config` / 왜: 지정 프로젝트만 선프라임(확정 방향 §1) / AC: 키 부재·빈 배열·잘못된 타입 시 기본 `[]`로 동작하고, 지정 시 리스트가 로드된다 (단위테스트로 판정).
- [ ] **F-2 프라임 풀 신설** — 무엇을: 프로젝트별 웜 핸들 풀(선프라임·lock 하 체크아웃·백그라운드 리필·동시 프라임 상한) 구현 / 어디에: `dashboard/backend/adapters/brain_session.py` (신규 클래스 또는 레지스트리 확장) / 왜: 확정 방향 §2·§3·§4·§5 / AC: (a) 체크아웃 시 풀에서 핸들이 제거되고 리필이 트리거된다, (b) 동시 체크아웃 2건에서 같은 핸들이 중복 배정되지 않는다, (c) 동시 프라임 수가 상한을 넘지 않는다 — 각각 단위테스트로 판정.
- [ ] **F-3 기동 선프라임** — 무엇을: 서버 기동 시 `prewarm_projects` 각 프로젝트를 백그라운드 선프라임하여 풀 등록 / 어디에: `dashboard/backend/main.py` (lifespan/startup 훅 신설) / 왜: 확정 방향 §1 / AC: 기동 시 지정 프로젝트 수만큼 프라임이 트리거되고(로그 확인), 미지정(빈 배열) 시 프라임 0회·기동 지연 없음.
- [ ] **F-4 새 대화 웜 배정** — 무엇을: 새 대화(미등록 session_id)의 prime/query 진입 시 해당 프로젝트 풀에 웜 핸들이 있으면 체크아웃하여 세션에 주입(즉시 ready), 없으면 기존 콜드 경로 폴백 / 어디에: `dashboard/backend/adapters/brain_session.py`(주입 로직) + `dashboard/backend/routers/brain.py`(진입점 연결) / 왜: 확정 방향 §3·§7 / AC: (a) 풀에 핸들이 있을 때 새 session_id의 상태가 콜드 프라임 없이 ready가 되고 첫 질의가 `--resume` 웜 경로를 탄다(단위테스트 — subprocess 모킹), (b) 풀이 비어 있으면 기존 콜드 동작과 동일(회귀 없음), (c) 기존 API 요청/응답 스키마 불변.
- [ ] **F-5 실기동 검증** — 무엇을: 실제 서버 기동으로 선프라임→새 대화 웜 배정 흐름 확인 / 어디에: 로컬 콘솔 데몬 (이 프로젝트를 prewarm 지정) / 왜: 완료기준(실검증 의무 — 헌법 §4) / AC: 기동 로그에 선프라임 완료 기록 + 새 대화 첫 질의 elapsed가 웜 수준(콜드 대비 유의미 단축)으로 관측된다.

## 제약 조건

- [MUST] `dashboard/backend/adapters/opbr_adapter.py` @header: "--safe-mode·--bare·anthropic SDK·API 키 절대 금지" — 구독 `claude -p` 경로 유지.
- [MUST] `dashboard/backend/adapters/brain_session.py` @header: "backend 무상태 원칙 — Q&A 내용 저장 안 함. 세션 핸들만(휘발성 프로세스 상태) 보유, DB·파일 영속 금지" — 풀도 인메모리 한정.
- 기존 브레인 API 5종(auth/status/prime/query/job)의 요청·응답 계약 불변 (FE 무변경 — 확정 방향 §7).
- 프로젝트별 cwd 격리 유지 — 풀 키는 project_path (`opbr_adapter.py:175` cwd 격리).
- 배포 경계: `~/.opal/` 직접 수정 금지, 프로젝트 소스(`dashboard/`)만 수정 (.opal/AGENT.md §금지사항).
- 코드 파일 변경 시 @header 갱신 + 변경이력 기록 (.opal/AGENT.md §업무 수행 지침).

## 기술 스택

- Python 3.11+ / FastAPI + uvicorn (dashboard/backend)
- threading 기반 동시성 (기존 brain_session.py 패턴 유지)
- pytest (dashboard/backend/tests)
- claude CLI 서브프로세스 (`claude -p --session-id/--resume`)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | brain_session (세션 상태기계) | `dashboard/backend/adapters/brain_session.py` | 풀 신설 대상 — ID 분리·lock 패턴·리셋 트리거 준수 |
| D-2 | 소스 | opbr_adapter (claude 호출) | `dashboard/backend/adapters/opbr_adapter.py` | prime_and_ask 계약·cwd 격리·[MUST] 제약 |
| D-3 | 소스 | brain 라우터 (API 진입점) | `dashboard/backend/routers/brain.py` | prime/query 진입점에 풀 체크아웃 연결 |
| D-4 | 소스 | config (console.config.json 로더) | `dashboard/backend/config.py` | prewarm_projects 키 추가 지점 |
| D-5 | 소스 | main (FastAPI 앱) | `dashboard/backend/main.py` | 기동 훅(lifespan) 신설 지점 |
| D-6 | 소스 | console scan 머지 | `opal/tools/opal-cli/lib/console.sh:196-232` | config 신규 키 보존 확인 근거 (수정 대상 아님) |
| D-7 | 설계 | 059 태스크 (ID 분리·[ASSISTANT] 캡) | `tasks/059-260713-opds-에이전트마커-3단-세션주입/` | conversation_id↔claude 핸들 분리 설계 배경 |
