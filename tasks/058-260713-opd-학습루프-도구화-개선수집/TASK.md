# TASK: PM 학습 루프 tool-gated 재설계 + 로컬/FW 학습 분리 + fw-inbox 수집

> 작성일: 2026-07-13 | 작업 유형: 개선 | 적용 스킬: opd | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

정의만 있고 파이프라인·도구 어디서도 호출되지 않아 죽어있는 PM 학습 루프/자기 개선을, `op-brain-ingest`와 같은 tool-gated 집행 체계로 재설계한다. 학습을 **로컬 PM 개선**과 **FW(프레임워크) 개선**으로 분리하고, FW 개선 제안은 프로젝트에 묻히지 않도록 전역 `~/.opal/fw-inbox/`로 수집한다.

## 배경

PM 학습 루프/자기 개선(`opal-pm.md §5` stub / `pm-learning-loop.md` / `self-improvement.md`)은 정의만 존재하고 실제로 작동하지 않는다. PRINCIPLES "Enforce, don't just advise: if a rule must always hold, a tool gates it — not prose." 를 정면으로 위반하는 순수 prose 프로토콜이기 때문이다. 반면 바로 옆의 자매 훅 `op-brain-ingest`는 CLOSE 하드연결 + 도구 집행 + 산출물 증거의 3요소로 살아있어, 이 성공 패턴을 답습할 수 있다.

## 배경 분석 (대화에서 도출)

전수 조사 2회(Explore)로 확정한 현황:

- **호출 지점 0건**: `학습 루프`·`self-improvement` 문자열은 정의 3문서와 부트스트랩 로드 언급, `specialist-agent.md:69`, `agent-guide.md` placeholder, `opal-pilot-project-dev/SKILL.md:561-566`(prose)에만 존재 — 파이프라인·도구 어디서도 호출·집행되지 않음.
- **CLOSE 4스텝에 회고 없음**: 모든 pilot CLOSE(`opal-pilot-dev/SKILL.md:230`, `write-tech:377`, `gc:324`, `project-dev:765`)는 ①DONE.md+state mark ②관련문서 업데이트 ③op-brain-ingest ④완료보고뿐. 지식 누적 훅은 op-brain-ingest 하나.
- **도구 집행/관측 부재**: `state_tool.py`에 `학습/learning/self-improve` 0건. memory-tool은 학습 루프를 인지하지 못하는 일반 CRUD. 학습 신호가 어디에도 적재되지 않아 회고할 재료 자체가 없음.
- **SSOT 파편·지칭 오류**: 정의가 3문서에 분산. `self-improvement.md`는 "트리거 테이블은 opal-pm.md §5에 유지"라 하나 실제 테이블은 `pm-learning-loop.md §5.2`에 있어 SSOT 지칭이 어긋남.
- **console 아키텍처(발송 대행 검토용)**: opal console은 각 PC 로컬 상주 데몬(FastAPI 127.0.0.1:7823, `ARCHITECTURE.md:241`)이며 중앙 수집 서버가 아니다. 서버측 cron/스케줄러 없음, 이메일 outbound 없음 — 얹으려면 신규. `~/.opal/console.config.json`을 읽어 로컬 `~/.opal/` 접근은 가능.
- **hook 계약(검토 후 폐기)**: Claude Code UserPromptSubmit(매 발화)·Stop(매 턴)·PostToolUse·git post/pre-commit 계약을 확인했으나, 빈번함·플랫폼종속·bash 의미판단 불가로 전면 미채택 결정.

## 확정된 설계 방향 (대화에서 합의)

1. **2트랙 구조** — ① **태스크 경로(회고)**: CLOSE 단계에 회고 하드스텝 삽입 → 자동 enforce(tool-gated). ② **비태스크 경로(PM 직접/L2/대화)**: `//opim`(opal-improve) 명시 스킬 온디맨드 + PM 피드백 감지 시 제안 nudge(soft).
2. **학습 2분류** — **로컬 PM 개선** → 그 프로젝트 `.opal/`(AGENT.md 확정기준·검토기준·전문에이전트·memory). **FW 개선** → 전역 `~/.opal/fw-inbox/`.
3. **회고 입력 = 태스크/세션 궤적 신호**(워커 재시도·폴백, 소유자 재지시·피드백, PM Gate 반복이슈, PLAN 재진입) — 산출물 재독이 아님(그건 PM Gate/QA 담당). 산출 = 프로세스·규칙 개선점.
4. **스킬명 `opal-improve`, 약어 `//opim`** — 등록 25개 alias와 충돌 없음·`op+2글자` 컨벤션 부합 확인 완료.
5. **hook 인프라 전면 폐기** — 순수 스킬 온디맨드 + 태스크 CLOSE 하드스텝만. 세션 백스톱도 생략(hook 0개, 플랫폼독립 100%).
6. **문서 SSOT 통합** — 정의 3문서를 SSOT 1개로 통합 + `self-improvement.md` 트리거 테이블 지칭 오류 수정 + 두 얼굴(회고/피드백) 명확 분리.
7. **결정론 집행** — 학습 산출 기록·검증은 도구(신규 `improve-tool` 또는 서브명령)로 tool-gate. fw-inbox 항목은 출처 메타(PC·프로젝트·상황·일시) 포함 자기완결.
8. **프레임워크-우선 원칙** — 에이전트 행동 개선(보고형식·프로세스 등)은 개인 memory가 아니라 프레임워크 소스 SSOT 수정 → install 배포 대상. 배포경계(`~/.opal` 직접수정 금지) 준수.

## 명확화 결과

> TASK 4요소를 잠근다.

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | 학습 루프를 tool-gated 2트랙으로 재설계 + 로컬/FW 분리 + `~/.opal/fw-inbox` 수집 + `opal-improve`(`//opim`) 신설 + 정의 3문서 SSOT 통합 | 각 컴포넌트의 세부 인터페이스(improve-tool 서브명령 시그니처, fw-inbox 항목 스키마, 회고 스텝 삽입 위치)는 PLAN에서 확정 | op-brain-ingest 패턴, Explore 조사 결과 |
| 범위 | **포함**: ①CLOSE 회고 하드스텝 ②opal-improve 스킬(//opim)+registry 등록 ③improve-tool(또는 서브명령) 결정론 집행 ④fw-inbox 수집(기록까지)+로컬/FW 분류 ⑤정의 3문서 SSOT 통합·지칭오류 수정 ⑥install 배포 반영. **제외**: 이메일 발송(SMTP)·console cron 대행 발송 = **보류(후속 별도)** | - | 대화 보류 지시 |
| 제약 | 플랫폼 독립(Claude Code hook 사용 금지) / 배포경계(소스 수정 후 install, `~/.opal` 직접수정 금지) / op-brain-ingest 패턴 답습 / STATE·state-tool 마커 직접편집 금지 / 변경이력 행 추가 의무 | - | PRINCIPLES, AGENT.md 금지사항 |
| 완료기준 | 아래 요구사항 R1~R6의 AC 전부 충족 + 재설계된 학습 루프가 실제로 호출·집행됨을 증거(dry-run/실행 출력)로 확인 | - | 헌법 §4(evidence) |

## 요구사항

- [ ] **R1 회고 하드스텝** — 무엇을: pilot CLOSE 단계에 학습 루프(회고) 하드스텝 삽입 / 어디에: 대상 pilot SKILL.md CLOSE(PLAN에서 대상 확정) / 왜: 확정방향 §1 / AC: 지정 pilot CLOSE 프로세스에 회고 스텝이 op-brain-ingest와 나란히 존재하고, 회고 산출(개선후보 N건 또는 "없음")이 도구로 기록되도록 명시돼 있다.
- [ ] **R2 opal-improve 스킬** — 무엇을: `opal-improve` 스킬 신설(`//opim`) / 어디에: `opal/skills/opal-improve/` + `opal-skills-registry.json` / 왜: 확정방향 §1·§4 / AC: SKILL.md가 존재하고 5단계 프로세스(관찰→분류→기록→보고→승인) + 로컬/FW 분류 분기를 정의하며, registry match로 `//opim`이 해석된다.
- [ ] **R3 improve-tool 결정론 집행** — 무엇을: 학습 산출 기록·검증 도구(신규 `improve-tool` 또는 기존 도구 서브명령) / 어디에: `opal/tools/` + `tools.md` 등록 / 왜: 확정방향 §7, PRINCIPLES enforce / AC: 도구가 학습 산출을 결정론적으로 기록하고(로컬 목적지 또는 fw-inbox), `"ok"` JSON 계약을 반환한다.
- [ ] **R4 fw-inbox 수집 + 로컬/FW 분류** — 무엇을: FW 개선을 `~/.opal/fw-inbox/`에 출처메타 포함 자기완결 항목으로 적재, 로컬 PM 개선과 분류 분기 / 어디에: `~/.opal/fw-inbox/`(런타임 데이터) + 분류 로직(opal-improve/improve-tool) / 왜: 확정방향 §2 / AC: FW로 분류된 학습이 `~/.opal/fw-inbox/{메타}.md`로 기록되고, 로컬로 분류된 학습은 프로젝트 `.opal/` 목적지로 가는 것이 실행으로 확인된다.
- [ ] **R5 문서 SSOT 통합 + 잉여 제거** — 무엇을: 정의 3문서를 SSOT 1개로 통합. 구 `pm-learning-loop.md`를 `pm-improvement-loop.md`로 **rename**하여 SSOT 본문화(self-improvement 내용 흡수) + `self-improvement.md` **삭제** + 이를 참조하던 링크 dangling 정리 + `opal-pm.md §5` stub이 신규 SSOT를 가리키게 정리 + 두 얼굴(회고/피드백) 분리 서술 + hook 미채택 근거 기록 / 어디에: `opal-pm.md §5`, `pm-improvement-loop.md`(신규 SSOT), `self-improvement.md`(삭제) / 왜: 확정방향 §5·§6 / AC: ①`pm-improvement-loop.md` 단일 SSOT에 트리거 테이블·5단계·기록위치가 모두 존재 ②`self-improvement.md` 파일이 제거됨 ③`self-improvement.md`·구 `pm-learning-loop.md`를 가리키는 dangling 참조 0건 ④트리거 테이블 지칭 오류 소멸.
- [ ] **R6 install 배포 반영** — 무엇을: 신규 스킬·도구·문서를 install 스크립트에 반영 / 어디에: `scripts/install-mac.sh`(및 win) / 왜: 확정방향 §8, 배포경계 / AC: install 실행 시 opal-improve·improve-tool·fw-inbox 초기화가 `~/.opal/`로 배포된다.

## 제약 조건

- 플랫폼 독립 — Claude Code hook(UserPromptSubmit/Stop/PostToolUse 등)에 의존하지 않는다.
- 배포경계 — 프로젝트 소스(`opal/`·`skills/`·`agents/`·`scripts/`)를 수정하고 install로 배포한다. `~/.opal/` 직접 수정 금지(단 `~/.opal/fw-inbox/`는 런타임 데이터 디렉토리로 install이 초기화).
- op-brain-ingest 성공 패턴 답습(CLOSE 하드연결 + 도구 집행 + 증거 산출).
- 변경이력 행 추가 의무(스킬·에이전트·참조 문서 수정 시).
- 이메일 발송·console cron 대행은 이번 범위 제외(후속 태스크).

## 기술 스택

- Markdown, YAML (스킬·참조 문서)
- Python (improve-tool, `run.sh` 래퍼 — 기존 OPAL 도구 컨벤션)
- Bash (install 스크립트)
- Node.js (skill-registry 연동)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | PM 학습 루프 정의 | `opal/core/references/harness/pm-learning-loop.md` | 재설계 대상 SSOT 후보 |
| D-2 | 설계 | 자기 개선 세부 프로세스 | `opal/core/references/pm/self-improvement.md` | 5단계 프로세스·기록 위치·지칭 오류 |
| D-3 | 설계 | opal-pm.md §5 | `opal/core/references/opal-pm.md` | 학습 루프 stub |
| D-4 | 설계 | op-brain-ingest / CLOSE 훅 | `opal/skills/op-brain-ingest/`, `opal/skills/opal-pilot-dev/SKILL.md:230` | 답습할 자매 훅 패턴 |
| D-5 | 설계 | 아키텍처 (console·배포) | `docs/ARCHITECTURE.md` | console 구조·배포 모델 |
| D-6 | 설계 | 컨벤션 (Guards/도구/배포경계) | `docs/CONVENTIONS.md` | 구현 규칙 준수 |
