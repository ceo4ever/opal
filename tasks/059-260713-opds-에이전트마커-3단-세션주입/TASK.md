# TASK: opal-agent 부트스트랩 마커 3-way 확장 + caller-supplied session id 지원

> 작성일: 2026-07-13 | 작업 유형: 개선 | 적용 스킬: opds | 모드: semi-agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

opal-agent의 `--opal-bootstrap` 옵션을 2-way(on|off)에서 3-way(on|assistant|off)로 확장하여 [ASSISTANT] 중간 tier(비서 tier 캡) 서브에이전트 호출을 지원하고, 브레인 이관의 나머지 갭인 caller-supplied session id 주입을 함께 지원한다.

## 배경

브레인 질의(opbr)를 opal-agent로 호출하려면 [ASSISTANT] tier가 필요하다. 현재 opal-agent는 `on`(마커 없음 → 프로젝트 cwd에서 PM tier 승격)과 `off`([WORKER] → 어떤 tier도 미로드)만 지원하여, "Phase A(`//` 커맨드 해석 능력)는 유지 + Phase B(PM tier) 승격만 억제"라는 브레인 워커의 요구를 충족하는 옵션이 없다.

## 배경 분석 (대화에서 도출)

- 현재 마커 옵션은 2-way: `AgentConfig.opal_bootstrap: "on"|"off"`, off면 `_mark()`가 프롬프트 첫 줄에 `[WORKER]` 주입 (→ D-1:91, D-1:146-149, D-1:611).
- `_mark()`는 "최종 프롬프트의 최외곽 첫 줄" 규칙을 이미 보장 — cursor/antigravity의 system_prompt 접붙임 이후에 적용 (→ D-1:382, D-1:431).
- 게이트 인프라는 완비: 부트스트래퍼 4종(claude/gemini/codex/cursor) 모두 첫 줄 `[WORKER]`/`[ASSISTANT]` 마커 게이트 보유 (→ D-5, 각 파일 v1.1/v1.3 변경이력).
- [ASSISTANT] 마커의 의미 SSOT는 core AGENT.md의 [ASSISTANT 규칙] — Phase A만 로드, Phase B 억제, `//` 커맨드 정상 발동 (→ D-3).
- 브레인 소비자 opbr_adapter.py는 `[ASSISTANT]\n//opbr query --read-only ...` 프롬프트 + cold=`--session-id <FE제공 id>` / warm=`--resume <id>` 계약을 사용 (→ D-4:127-130).
- opal-agent ClaudeAdapter는 `--resume`만 지원하고 신규 세션에 caller-supplied session id를 지정하는 수단이 없다 (→ D-1:173-174). 마커 3-way만으로는 브레인 이관에 불충분.

## 확정된 설계 방향 (대화에서 합의)

1. **기존 플래그 값 확장** — 새 플래그를 만들지 않고 `--opal-bootstrap on|assistant|off`로 확장한다. on/off의 기존 의미는 불변(하위호환).
2. **마커 3-way와 마커 사다리 1:1 대응** — `on`=마커 없음(풀 부트스트랩) / `assistant`=`[ASSISTANT]`(Phase A만) / `off`=`[WORKER]`(전부 스킵).
3. **caller-supplied session id 지원 포함** — 브레인 이관 선행 조건을 이 태스크에서 한 번에 닫는다 (캡틴 범위 확정: "3-way + session-id 갭 포함").

## 명확화 결과

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | `--opal-bootstrap` 3-way 확장([ASSISTANT] 지원) + caller-supplied session id 주입 지원 | - | 부트스트래퍼 게이트 4종은 이미 [ASSISTANT] 처리 완비 (→ D-5) |
| 범위 | 포함: `opal/tools/opal-agent/opal_agent.py`·`README.md`(+ 필요 시 install 매니페스트 확인). 제외: opbr_adapter.py 실제 이관(후속 태스크), 부트스트래퍼 수정 없음 | - | 배포 경계 — `~/.opal/` 직접 수정 금지, 프로젝트 소스만 (→ D-6) |
| 제약 | on/off 기존 의미·기본값(on) 불변. 무의존성(Python 3.10+ stdlib) 유지. 플랫폼 분기는 어댑터 계층 내부에만 | session id 파라미터 표면(파라미터명·provider별 capability 처리)은 PLAN에서 결정 | claude CLI cold=`--session-id`/warm=`--resume` 계약 (→ D-4) |
| 완료기준 | ① assistant 지정 시 조립 프롬프트 첫 줄이 정확히 `[ASSISTANT]` ② cold session id 지정 시 claude 조립 커맨드에 `--session-id <id>` 포함 ③ 기존 on/off·resume 동작 회귀 0 ④ claude 실측 프로브에서 [ASSISTANT] 캡 확인(부트스트랩 보고 `⬜ harness ⬜ PM`) | - | 051 실측 검증 방법 재사용 (→ D-3) |

## 요구사항

- [ ] **R-1 마커 3-way 확장**: `AgentConfig.opal_bootstrap`·CLI `--opal-bootstrap` choices에 `assistant` 추가, `_mark()`가 assistant일 때 첫 줄 `[ASSISTANT]` 주입 — `opal/tools/opal-agent/opal_agent.py`에 반영. 근거: 브레인 워커는 Phase A 유지+Phase B 억제 필요 (→ D-3).
  - AC: `--opal-bootstrap assistant`로 조립된 최종 프롬프트의 첫 줄이 정확히 `[ASSISTANT]`이고, 전 provider에서 system_prompt 접붙임보다 바깥(최외곽)에 위치한다.
- [ ] **R-2 하위호환 보존**: on/off의 기존 동작·기본값(on) 불변 — 동일 파일. 근거: 확정 방향 §1.
  - AC: on=마커 없음, off=`[WORKER]` 첫 줄, 기본값 on — 기존 호출 시그니처 전부 무변경 통과.
- [ ] **R-3 caller-supplied session id**: claude provider에서 신규(cold) 세션에 호출자가 session id를 지정할 수 있다 — 동일 파일. 근거: opbr cold 계약 (→ D-4:127-130).
  - AC: cold 지정 시 조립 커맨드에 `--session-id <id>`가 포함되고, 기존 resume(warm) 지정 시 `--resume <id>`가 유지되며, 두 경로가 상호 배타적으로 동작한다. 미지원 provider에 지정 시 stderr 경고(효력 없음 명시).
- [ ] **R-4 문서 갱신**: README 플래그 표·사용 예·변경이력(v2.5)에 3-way와 session id를 반영 — `opal/tools/opal-agent/README.md` + `opal_agent.py` 헤더 변경이력.
  - AC: README에 `assistant` 값 행과 session id 사용 예가 존재하고, 변경이력에 v2.5 행(일시 KST + 059)이 추가되어 있다.
- [ ] **R-5 동작검증(실측)**: claude 프로브로 [ASSISTANT] 캡을 확인한다.
  - AC: `--opal-bootstrap assistant` 실측 호출의 응답에서 비서 tier 캡 증거(부트스트랩 보고 라인 `⬜ harness ⬜ PM` 또는 PM tier 미로드 확인)가 확보된다.

## 제약 조건

- [MUST] `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다."
- [MUST] `.opal/AGENT.md` §금지사항: "변경이력 누락 금지 — 스킬·에이전트·참조 문서 수정 시 변경이력 표 행 추가 의무."
- 무의존성 유지 — Python 3.10+ 표준 라이브러리만 (→ D-1:7).
- 플랫폼(provider) 분기는 어댑터 계층 내부에만 — 공통 API 표면에 provider 하드코딩 금지.
- 부트스트래퍼 4종·core AGENT.md는 수정 대상 아님(게이트는 이미 완비) — 범위 밖 파일 수정 금지.

## 기술 스택

- Python 3.10+ (표준 라이브러리만, 무의존) — opal_agent.py
- Bash — run.sh 래퍼 (수정 불요 예상)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | opal_agent.py | `opal/tools/opal-agent/opal_agent.py` | 현행 2-way 마커 구현(`:91,146-149,611`)·resume 전용 session 처리(`:173-174`) |
| D-2 | 소스 | opal-agent README | `opal/tools/opal-agent/README.md` | 플래그 문서·변경이력 갱신 대상 |
| D-3 | 설계 | core AGENT.md | `opal/core/AGENT.md` | [ASSISTANT 규칙]·3단 스킵 사다리 의미 SSOT + 051 실측 검증 방법 |
| D-4 | 소스 | opbr_adapter.py | `dashboard/backend/adapters/opbr_adapter.py` | 브레인 소비자 계약 레퍼런스 — `[ASSISTANT]` 프롬프트(`:127-130`)·cold/warm 세션 핸들 |
| D-5 | 소스 | 부트스트래퍼 4종 | `opal/bootstrapper/` | 첫 줄 마커 게이트 완비 근거(claude/gemini/codex v1.1·v1.3, cursor `.mdc:8`) |
| D-6 | 설계 | PM 프로필 | `.opal/AGENT.md` | 배포 경계·변경이력 의무 등 금지사항 |
